<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 35. Rails Testing

Rails tests prove adapters and integrations: controllers, jobs, mailers,
and the database. Language-level RSpec/Minitest habits live in
[Chapter 24](24-testing.md). This chapter covers the Rails-shaped surface
from the
[Rails Style Guide](https://github.com/rubocop/rails-style-guide)
([testing](https://rails.rubystyle.guide/#testing),
[integration testing](https://rails.rubystyle.guide/#integration-testing),
[freeze-time](https://rails.rubystyle.guide/#freeze-time),
[delivery-method-test](https://rails.rubystyle.guide/#delivery-method-test))
plus the enabled `RSpec/*` and `Rails/*` cops that keep the suite honest.

Prefer **single quotes** in examples and factory data.

**Minitest-only apps:** treat every `RSpec/*` callout in this chapter and
in chapter 24 as **N/A**. Keep core, Rails, Performance, Lint, and
Security departments enabled. Do not disable `Rails/HttpStatus` (or other
Rails cops) because the suite is Minitest; map the same intent to
`assert_response` / `assert_enqueued_with` instead. See chapter 37.15.

**Tool alignment:** `RSpec/VerifiedDoubles`, `RSpec/ContextWording`,
`RSpec/ExampleWording`, `RSpec/Focus`, `RSpec/LetSetup`,
`Rails/HttpStatus`, `Rails/TimeZone`, `Rails/ResponseParsedBody`,
`Rails/RedundantTravelBack` — only when listed in
`docs/reference-data/rubocop-effective-enabled.txt`.

## 35.1 Prefer integration/request specs for HTTP behaviour over isolated controller unit tests.

> Why? [integration-testing](https://rails.rubystyle.guide/#integration-testing)
> exercises routing, middleware, and strong params together. A controller
> unit test that stubs the world proves little about the request path.
> **Suggestion.**

```ruby
# bad — heavy stubbing of the controller instance
allow(controller).to receive(:current_user).and_return(user)
get :show, params: { id: 1 }

# good — request spec / integration test
get account_path, headers: auth_headers_for(user)
expect(response).to have_http_status(:ok)
```

## 35.2 Use symbolic HTTP status codes in expectations.

> Why? [http-status-code-symbols](https://rails.rubystyle.guide/#http-status-code-symbols)
> keeps assertions readable (`:not_found` vs `404`).
> **Violation.**
>
> Enforced by: Rails/HttpStatus.

```ruby
# bad
expect(response).to have_http_status(404)

# good
expect(response).to have_http_status(:not_found)
```

## 35.3 Freeze or travel time deliberately; never depend on wall-clock `Time.now` in examples.

> Why? [freeze-time](https://rails.rubystyle.guide/#freeze-time) and the
> Active Support time helpers make expiry, billing periods, and "due at"
> assertions deterministic.
> **Suggestion.**

```ruby
# bad
it 'marks the trial expired' do
  expect(account).to be_trial_expired # flakes near midnight
end

# good
it 'marks the trial expired after 14 days' do
  travel_to Time.zone.parse('2026-01-01 12:00:00') do
    account = create(:account, trial_ends_on: Date.new(2025, 12, 31))
    expect(account).to be_trial_expired
  end
end
```

## 35.4 Use zone-aware times in tests the same way production does.

> Why? Mixing `Time.parse` (system zone) with `Time.zone.parse` hides
> off-by-one bugs that only appear in CI. Align with
> [tz-config](https://rails.rubystyle.guide/#tz-config) /
> [time](https://rails.rubystyle.guide/#time).
> **Violation.**
>
> Enforced by: Rails/TimeZone.

```ruby
# bad
travel_to Time.parse('2026-01-01 12:00:00')

# good
travel_to Time.zone.parse('2026-01-01 12:00:00')
```

## 35.5 Prefer verified doubles over `double('Anything')` for app collaborators.

> Why? Unverified doubles silently accept misspelled methods.
> `RSpec/VerifiedDoubles` catches that class of green-but-wrong suite.
> **Violation.**
>
> Enforced by: RSpec/VerifiedDoubles.

```ruby
# bad
gateway = double('Gateway', charge!: true)

# good
gateway = instance_double(PaymentGateway, charge!: true)
```

## 35.6 Keep mailers on the test delivery method in the test environment.

> Why? [delivery-method-test](https://rails.rubystyle.guide/#delivery-method-test)
> accumulates messages in `ActionMailer::Base.deliveries` instead of
> talking to SMTP.
> **Suggestion.**

```ruby
# good — config/environments/test.rb
config.action_mailer.delivery_method = :test
```

## 35.7 Assert on enqueued jobs, not on side effects inside `perform_now` unless that is the unit under test.

> Why? Request specs that run jobs inline couple HTTP latency to gateway
> stubs. Prefer `have_enqueued_job` / `assert_enqueued_with`, and unit-test
> the job/service separately.
> **Suggestion.**

```ruby
# bad — every request spec pays for Checkout.call
perform_enqueued_jobs { post checkouts_path }

# good
expect {
  post checkouts_path, params: checkout_params
}.to have_enqueued_job(CheckoutJob)
```

## 35.8 Use factories (or fixtures) consistently; do not invent ad-hoc `User.create!` soup in every example.

> Why? Scattered setup drifts validation requirements and burns suite time
> on irrelevant attributes. FactoryBot (or fixtures) keeps the minimum
> valid record in one place.
> **Suggestion.**

```ruby
# bad
user = User.create!(email: 'a@example.com', name: 'Ada', plan: 'pro', ...)

# good
user = create(:user, :pro)
```

## 35.9 Phrase `context` / `describe` blocks around Rails behaviour and role.

> Why? Failure output should say which role and which request shape failed.
> **Violation.**
>
> Enforced by: RSpec/ContextWording.

```ruby
# bad
context 'test' do
end

# good
context 'when the user is signed in' do
end
```

## 35.10 Never commit focused examples (`fit`, `fdescribe`, `:focus`).

> Why? A focused file turns CI into a lie — green while the rest of the
> suite is skipped.
> **Violation.**
>
> Enforced by: RSpec/Focus.

```ruby
# bad
fit 'charges the card' do
end

# good
it 'charges the card' do
end
```

## 35.11 Avoid `let!` that exists only for side effects without being referenced.

> Why? `RSpec/LetSetup` flags memoized helpers created solely to trigger
> persistence. Prefer explicit `before` setup or use the value.
> **Violation.**
>
> Enforced by: RSpec/LetSetup.

```ruby
# bad
let!(:user) { create(:user) }

it 'renders the dashboard' do
  get dashboard_path
end

# good
let(:user) { create(:user) }

before { sign_in(user) }

it 'renders the dashboard' do
  get dashboard_path
  expect(response).to have_http_status(:ok)
end
```

## 35.12 System/feature specs are for critical user journeys only.

> Why? Browser-driven tests are slow and flaky under parallel CI. Reserve
> them for signup, checkout, and other journeys that routing specs cannot
> prove. Cover the rest with request and model/service specs.
> **Suggestion.**

```ruby
# bad — system spec for every CRUD index filter
# good — request spec for filters; one system spec for checkout happy path
```

## 35.13 Parallelize safely: no shared filesystem or leaked `ENV` mutations.

> Why? Rails parallel testing forks workers. Global `ENV['FEATURE'] =`
> without restoration and writable tmp paths without unique names cross-talk
> between workers.
> **Suggestion.**

```ruby
# bad
before { ENV['BILLING'] = 'off' }

# good
around do |example|
  ClimateControl.modify(BILLING: 'off') { example.run }
end
```

## 35.14 Prefer single quotes in factory traits, emails, and assertion messages.

> Why? Matches [consistent-string-literals](https://rubystyle.guide/#consistent-string-literals)
> and `Style/StringLiterals` across `spec/` and `test/`.
> **Violation.**
>
> Enforced by: Style/StringLiterals.

```ruby
# bad
create(:user, email: "ada@example.com")

# good
create(:user, email: 'ada@example.com')
```

## 35.15 Prefer `response.parsed_body` over ad-hoc `JSON.parse(response.body)`.

> Why? `Rails/ResponseParsedBody` keeps JSON/HTML parsing on the
> Response API so content-type handling stays consistent across request
> specs.
> **Violation.**
>
> Enforced by: Rails/ResponseParsedBody.

```ruby
# bad
payload = JSON.parse(response.body)

# good
payload = response.parsed_body
```

## 35.16 Do not wrap examples in redundant `travel_back` when using block-form time helpers.

> Why? `travel_to` / `freeze_time` blocks already restore the clock.
> Extra `travel_back` is noise and can hide nested time bugs.
> **Violation.**
>
> Enforced by: Rails/RedundantTravelBack.

```ruby
# bad
travel_to(Time.zone.parse('2026-01-01 12:00:00')) do
  expect(account).to be_trial_expired
end
travel_back

# good
travel_to(Time.zone.parse('2026-01-01 12:00:00')) do
  expect(account).to be_trial_expired
end
```

## 35.17 In Minitest suites, assert with Rails helpers; ignore RSpec-only Violation labels.

> Why? The shipped `.rubocop.yml` loads `rubocop-rspec` for RSpec apps.
> A Minitest app should not turn off `Rails/*` to silence RSpec noise —
> either omit the RSpec plugin, exclude `spec/**/*`, or treat `RSpec/*`
> findings as **N/A** while keeping Rails/Security cops on. Map the same
> intent: symbolic statuses, zone-aware times, enqueued jobs.
> **Suggestion.**

```ruby
# good — Minitest request test
class AccountsControllerTest < ActionDispatch::IntegrationTest
  test 'shows the account when signed in' do
    sign_in(users(:ada))
    get account_url
    assert_response :ok
  end
end
```

## 35.18 Assert mailer delivery through `ActionMailer::Base.deliveries` or enqueued jobs, not SMTP.

> Why? Paired with
> [delivery-method-test](https://rails.rubystyle.guide/#delivery-method-test)
> and chapter 33: request specs should prove a message was queued or
> recorded, not that a provider accepted it.
> **Suggestion.**

```ruby
# bad — hits a real adapter in CI
perform_enqueued_jobs { post invites_path }

# good — assert the mailer job / delivery array
expect {
  post invites_path, params: { email: 'ada@example.com' }
}.to have_enqueued_mail(InviteMailer, :welcome)
```

## 35.19 Keep database cleaner / transactional tests consistent with parallel workers.

> Why? Mixing truncation strategies with transactional fixtures under
> `parallelize` leaks rows across workers. Prefer Rails' default
> transactional tests for unit/request specs; use truncation only for
> system specs that need a committed database visible to the browser.
> **Suggestion.**

```ruby
# bad — truncation for every request spec
# good — transactional tests by default; truncation only in system tests
```

## 35.20 Prefer `assert_enqueued_with` / `have_enqueued_job` argument matchers over inspecting job YAML.

> Why? Serialized ActiveJob arguments drift with GlobalID. Match on job
> class and keyword args; let the framework own serialization.
> **Suggestion.**

```ruby
# bad
job = enqueued_jobs.last
expect(YAML.load(job[:args].first)).to include('user_id' => user.id)

# good
expect {
  post checkouts_path
}.to have_enqueued_job(CheckoutJob).with(user)
```
