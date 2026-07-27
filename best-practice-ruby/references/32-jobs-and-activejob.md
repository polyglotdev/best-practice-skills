<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 32. Jobs & ActiveJob

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

Jobs are asynchronous entry points into the same domain as controllers.
They must be idempotent where retries exist, take simple arguments
(GlobalID or primitives), and inherit application defaults for queues
and error handling. Prefer `ApplicationJob` over bare
`ActiveJob::Base`.

The Rails Style Guide covers process and background email concerns in
[background-email](https://rails.rubystyle.guide/#background-email),
[managing-processes](https://rails.rubystyle.guide/#managing-processes),
and [foreman](https://rails.rubystyle.guide/#foreman). ActiveJob API
detail follows the
[Rails Guides: Active Job](https://guides.rubyonrails.org/active_job_basics.html)
where the style guide is silent.

**Tool alignment:** `Rails/ApplicationJob`, `Rails/SaveBang`,
`Rails/SkipsModelValidations`, `Rails/TimeZone`, `Rails/Output`,
`Rails/Exit`, and `Rails/EagerEvaluationLogMessage` are enabled.

## 32.1 Inherit every job from `ApplicationJob`.

> Why? Retry policy, discarded-error reporting, and default queues belong
> in one base class.
> **Violation.**
>
> Enforced by: Rails/ApplicationJob.

```ruby
# bad
class RebuildSearchIndexJob < ActiveJob::Base
  def perform(account_id)
    # ...
  end
end

# good
class RebuildSearchIndexJob < ApplicationJob
  def perform(account_id)
    # ...
  end
end
```

## 32.2 Keep `perform` small — load records, call a domain object, exit.

> Why? Jobs that embed full workflows are untestable without the queue
> adapter. Push logic to a service; the job is the async adapter.
> **Suggestion.**

```ruby
# bad
class FulfillOrderJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)
    Payments.charge!(order)
    Inventory.reserve!(order)
    order.update!(state: :fulfilled)
    OrderMailer.receipt(order).deliver_later
  end
end

# good
class FulfillOrderJob < ApplicationJob
  def perform(order_id)
    Orders::Fulfill.new.call(Order.find(order_id))
  end
end
```

## 32.3 Pass GlobalID-compatible records or primitive IDs — not structs of AR objects built by hand.

> Why? ActiveJob serializes GlobalID for AR objects. Passing a hash of
> attributes silently freezes stale state and skips locking.
> **Suggestion.**

```ruby
# bad
FulfillOrderJob.perform_later(order.attributes)

# good
FulfillOrderJob.perform_later(order)
# or
FulfillOrderJob.perform_later(order.id)
```

## 32.4 Make jobs idempotent under `retry_on` / at-least-once delivery.

> Why? Adapters retry. A job that charges a card twice on retry is an
> incident. Use idempotency keys, state guards, or DB uniqueness.
> **Suggestion.**

```ruby
# bad
def perform(order_id)
  order = Order.find(order_id)
  Payments.charge!(order)
  order.update!(state: :paid)
end

# good
def perform(order_id)
  order = Order.find(order_id)
  return if order.paid?

  Orders::Charge.new.call(order)
end
```

## 32.5 Configure `retry_on` / `discard_on` on `ApplicationJob` or the specific job — never swallow errors.

> Why? Bare `rescue StandardError` inside `perform` marks the job
> successful and drops the failure. Let ActiveJob's retry machinery see
> the exception.
> **Suggestion.**

```ruby
# bad
def perform(id)
  sync!(id)
rescue StandardError => error
  Rails.logger.error(error)
end

# good
class SyncJob < ApplicationJob
  retry_on Net::OpenTimeout, wait: :polynomially_longer, attempts: 5
  discard_on ActiveRecord::RecordNotFound

  def perform(id)
    sync!(id)
  end
end
```

## 32.6 Prefer `deliver_later` for mail from jobs and requests; do not nest job-enqueues unbounded.

> Why? [background-email](https://rails.rubystyle.guide/#background-email)
> — sending inline in a web request couples latency to SMTP. From a job,
> `deliver_later` is still fine (another queue hop) unless you need the
> same transaction; avoid fan-out loops that enqueue N jobs per row
> without a throttle.
> **Suggestion.**

```ruby
# bad — in a controller
UserMailer.welcome(user).deliver_now

# good
UserMailer.welcome(user).deliver_later
```

## 32.7 Use bang persistence when a failed write should fail the job.

> Why? A soft `save` returning `false` looks like success to the queue.
> **Violation** when returns are ignored.
>
> Enforced by: Rails/SaveBang.

```ruby
# bad
def perform(id)
  user = User.find(id)
  user.update(synced_at: Time.current)
end

# good
def perform(id)
  user = User.find(id)
  user.update!(synced_at: Time.current)
end
```

## 32.8 Do not skip validations inside jobs to "make it work".

> Why? Jobs are still writers. `update_column` in a job is how corrupt
> state spreads asynchronously.
> **Violation.**
>
> Enforced by: Rails/SkipsModelValidations.

```ruby
# bad
user.update_columns(synced_at: Time.current)

# good
user.update!(synced_at: Time.current)
```

## 32.9 Use zone-aware time APIs (`Time.zone`, `Time.current`), not `Time.now`.

> Why? Jobs often run in UTC processes while business rules are local.
> **Violation.**
>
> Enforced by: Rails/TimeZone.

```ruby
# bad
user.update!(synced_at: Time.now)

# good
user.update!(synced_at: Time.current)
```

## 32.10 Log with lazy blocks / programs that avoid eager interpolation.

> Why? `Rails/EagerEvaluationLogMessage` flags string building that
> always allocates even when the log level would discard the message.
> **Violation.**
>
> Enforced by: Rails/EagerEvaluationLogMessage.

```ruby
# bad
Rails.logger.debug("order=#{order.inspect} lines=#{order.lines.to_a}")

# good
Rails.logger.debug { "order=#{order.id} line_count=#{order.lines.size}" }
```

## 32.11 Never `exit` / `puts` from a job.

> Why? Same as application code — kill the worker process or bypass the
> logger.
> **Violation.**
>
> Enforced by: Rails/Exit, Rails/Output.

```ruby
# bad
def perform
  puts 'done'
  exit(0)
end

# good
def perform
  Rails.logger.info('done')
end
```

## 32.12 Set queues intentionally (`queue_as`) and keep names stable.

> Why? Latency-sensitive jobs (`mailers`, `realtime`) must not share a
> queue with bulk reindexes. Name queues by SLO, not by class nickname
> of the week.
> **Suggestion.**

```ruby
# bad — everything default
class RebuildSearchIndexJob < ApplicationJob
end

# good
class RebuildSearchIndexJob < ApplicationJob
  queue_as :low
end

class NotifyUserJob < ApplicationJob
  queue_as :within_five_seconds
end
```

## 32.13 Constrain concurrency when a job must be singular per resource.

> Why? Two overlapping `ReconcileAccountJob`s for the same account race.
> Use adapter locks (`sidekiq-unique-jobs`, Solid Queue concurrency
> controls, `for_update`) — pick one and document it.
> **Suggestion.**

```ruby
# bad — enqueue freely on every webhook
ReconcileAccountJob.perform_later(account.id)

# good — guard at enqueue or inside perform with a lock
def perform(account_id)
  Account.transaction do
    account = Account.lock.find(account_id)
    Accounts::Reconcile.new.call(account)
  end
end
```

## 32.14 Run job workers under a process manager in each environment.

> Why? [managing-processes](https://rails.rubystyle.guide/#managing-processes)
> and [foreman](https://rails.rubystyle.guide/#foreman) — a web-only
> boot means `deliver_later` piles up forever in development and
> silently drops work if production forgets the worker dyno.
> **Suggestion.**

```bash
# bad — only `rails server` in Procfile

# good — Procfile
web: bundle exec puma -C config/puma.rb
worker: bundle exec rake solid_queue:start
```

## 32.15 Test jobs by executing the domain path — `perform_now` / `perform_enqueued_jobs` — not by asserting JSON payloads of the adapter.

> Why? Adapter payload shapes change. Assert on side effects and on
> `have_been_enqueued` for the job class + args.
> **Suggestion** (see [Chapter 35](35-rails-testing.md)).

```ruby
# bad
expect(serialized_job_payload).to include('FulfillOrderJob')

# good
expect {
  FulfillOrderJob.perform_now(order.id)
}.to change { order.reload.state }.to('fulfilled')

expect {
  OrdersController.action(:create).call(env)
}.to have_enqueued_job(FulfillOrderJob).with(order)
```
