<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 34. Service Objects

When a use case does not belong on an Active Record model, a controller, or
a job, give it a plain Ruby object with one public entry point. The
[Rails Style Guide](https://github.com/rubocop/rails-style-guide) does not
mandate a gem named "service object"; it does require
[skinny controllers](https://rails.rubystyle.guide/#skinny-controllers),
[one method per action](https://rails.rubystyle.guide/#one-method),
[non-ActiveRecord models](https://rails.rubystyle.guide/#non-activerecord-models)
when you need Active Model behaviour without a table, and
[model business logic](https://rails.rubystyle.guide/#model-business-logic)
that stays about the domain rather than view formatting.

This chapter is the boundary layer those rules imply: extract a PORO (or an
`ActiveModel::Model` form object) when orchestration, multi-model writes, or
external I/O would otherwise fatten a controller or model. Prefer **single
quotes** in every sample.

**Tool alignment:** most of these rules are design Suggestions. Where a rule
collides with an enabled cop (`Rails/SaveBang`, `Rails/SkipsModelValidations`,
`Metrics/MethodLength`, `Style/ArgumentsForwarding`), it is labeled
**Violation**.

## 34.1 Extract a service when a controller action orchestrates more than one model or side effect.

> Why? [skinny-controllers](https://rails.rubystyle.guide/#skinny-controllers)
> and [one-method](https://rails.rubystyle.guide/#one-method) keep HTTP
> adapters thin. Multi-step checkout, invite flows, and "create X then notify
> Y" belong in a named object the action can call in one line.
> **Suggestion.**

```ruby
# bad — controller owns the use case
class CheckoutsController < ApplicationController
  def create
    order = current_user.orders.create!(checkout_params)
    PaymentGateway.charge!(order)
    OrderMailer.receipt(order).deliver_later
    redirect_to order
  end
end

# good — one call; HTTP stays HTTP
class CheckoutsController < ApplicationController
  def create
    order = Checkout.call(user: current_user, params: checkout_params)
    redirect_to order
  end
end
```

## 34.2 Give the object one public entry point (`call`, `call!`, or a verb).

> Why? A kitchen-sink class with five public methods is a hidden module.
> One entry point makes the use case obvious in stack traces and in
> `Checkout.call(...)` call sites. **Suggestion.**

```ruby
# bad
class Checkout
  def prepare(...); end
  def charge(...); end
  def notify(...); end
end

# good
class Checkout
  def self.call(user:, params:)
    new(user:, params:).call
  end

  def call
    # ...
  end
end
```

## 34.3 Prefer keyword arguments at the service boundary.

> Why? Positional bags of three or more values hide meaning at the call
> site. Keywords document the contract and pair with
> [arguments forwarding](https://rubystyle.guide/#arguments-forwarding) when
> wrapping.
> **Suggestion.**

```ruby
# bad
Checkout.call(user, params, true)

# good
Checkout.call(user: user, params: params, notify: true)
```

## 34.4 Keep persistence failures loud with bang methods inside the service.

> Why? A service that swallows `save` false returns forces every caller to
> inspect return codes. [save-bang](https://rails.rubystyle.guide/#save-bang)
> is the Rails guide's rule for "failure must raise."
> **Violation.**
>
> Enforced by: Rails/SaveBang.

```ruby
# bad
order.save
PaymentGateway.charge(order)

# good
order.save!
PaymentGateway.charge!(order)
```

## 34.5 Never skip validations to "just make it work" inside a service.

> Why? [beware-skip-model-validations](https://rails.rubystyle.guide/#beware-skip-model-validations)
> exists because `update_attribute`, `update_column`, and friends bypass
> callbacks and validations. A service is not a license to corrupt data.
> **Violation.**
>
> Enforced by: Rails/SkipsModelValidations.

```ruby
# bad
user.update_column(:status, 'active')

# good
user.update!(status: 'active')
```

## 34.6 Wrap multi-model writes in an Active Record transaction.

> Why? Partial success (order created, payment failed, mail sent) is worse
> than a raised error. Transactions make the service's write set atomic.
> **Suggestion.**

```ruby
# bad
order = user.orders.create!(attrs)
payment = order.payments.create!(charge_attrs)
# payment failed? order still persists

# good
Order.transaction do
  order = user.orders.create!(attrs)
  order.payments.create!(charge_attrs)
  order
end
```

## 34.7 Put form/validation-only objects on `ActiveModel::Model`, not fake AR tables.

> Why? [non-activerecord-models](https://rails.rubystyle.guide/#non-activerecord-models)
> is explicit: validations without persistence use Active Model. Do not
> invent a `contact_messages` table just to get `validates`.
> **Suggestion.**

```ruby
# bad — table that is never queried outside the form post
class ContactMessage < ApplicationRecord
end

# good
class ContactMessage
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :email, :string
  attribute :body, :string

  validates :email, :body, presence: true
end
```

## 34.8 Keep view formatting out of services and models.

> Why? [model-business-logic](https://rails.rubystyle.guide/#model-business-logic)
> sends HTML/formatting helpers to the view layer. A service that returns
> markup couples domain work to presentation.
> **Suggestion.**

```ruby
# bad
def call
  "<strong>#{user.name}</strong> checked out"
end

# good — return domain data; format in the view/mailer
def call
  Receipt.new(user:, order:)
end
```

## 34.9 Name the class after the use case, not after a pattern suffix soup.

> Why? `Checkout`, `InviteMember`, and `RotateApiKey` read better in
> call sites than `CheckoutServiceService`. If the team standardizes on a
> `Services::` namespace, keep the *class* name a verb phrase.
> **Suggestion.**

```ruby
# bad
class CheckoutServiceManager
end

# good
class Checkout
end

# also good — namespaced
module Billing
  class Checkout
  end
end
```

## 34.10 Inject collaborators; do not reach for globals inside `call`.

> Why? Hard-coded `PaymentGateway` constants and `ENV.fetch` deep in the
> method make tests patch constants. Pass gateways and clocks as keywords
> with defaults.
> **Suggestion.**

```ruby
# bad
def call
  PaymentGateway.charge!(order)
end

# good
def initialize(user:, params:, gateway: PaymentGateway)
  @gateway = gateway
end

def call
  @gateway.charge!(order)
end
```

## 34.11 Return a meaningful result; do not use exceptions for ordinary control flow.

> Why? Raising `CheckoutFailed` for "card declined" forces every caller into
> `rescue`. Prefer a result object or bang/non-bang pair (`call` / `call!`)
> where failure is expected. Reserve exceptions for bugs and violated
> invariants. **Suggestion.**

```ruby
# bad — expected business failure as exception
def call
  raise CardDeclined unless gateway.charge(order)
  order
end

# good — result the controller can branch on
CheckoutResult = Data.define(:ok, :order, :error)

def call
  return CheckoutResult.new(ok: false, order: nil, error: 'declined') unless gateway.charge(order)

  CheckoutResult.new(ok: true, order: order, error: nil)
end
```

## 34.12 Keep jobs thin: enqueue a service, do not reimplement it in `perform`.

> Why? HTTP and Active Job are two adapters over the same use case. Duplicating
> orchestration in `ApplicationJob#perform` drifts. Call the same object the
> controller calls.
> **Suggestion.**

```ruby
# bad
class CheckoutJob < ApplicationJob
  def perform(user_id, params)
    user = User.find(user_id)
    order = user.orders.create!(params)
    PaymentGateway.charge!(order)
  end
end

# good
class CheckoutJob < ApplicationJob
  def perform(user_id, params)
    Checkout.call(user: User.find(user_id), params: params)
  end
end
```

## 34.13 Do not autoload business logic from `lib/` without an explicit Zeitwerk path.

> Why? Classic Rails apps dump POROs in `lib/` and forget to add it to
> `config.autoload_paths` / `config.autoload_lib`. Prefer `app/services/`
> (or `app/models/` for Active Model form objects) so Zeitwerk picks them up
> in Rails 8 defaults.
> **Suggestion.**

```ruby
# bad — file in lib/checkout.rb, missing from autoload
# good — app/services/checkout.rb defining Checkout
```

## 34.14 Prefer single quotes in service code and stringly status values.

> Why? [consistent-string-literals](https://rubystyle.guide/#consistent-string-literals)
> and the shipped `Style/StringLiterals` cop both prefer single quotes.
> Services that mint status tokens (`'pending'`, `'paid'`) should match.
> **Violation.**
>
> Enforced by: Style/StringLiterals.

```ruby
# bad
order.update!(status: "paid")

# good
order.update!(status: 'paid')
```
