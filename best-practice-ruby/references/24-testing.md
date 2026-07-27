<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 24. Testing

A Ruby test suite usually picks **RSpec** or **Minitest** and sticks with it.
This chapter covers the rules that hold for both: determinism, one behaviour
per example, clear names. It then covers the RSpec-shaped conventions that
RuboCop's RSpec department enforces in this skill's `.rubocop.yml`.
Rails-specific fixtures, system tests, and parallel test runners live in
[Chapter 35, Rails Testing](35-rails-testing.md).

**Minitest-only apps:** every `RSpec/*` **Violation** / `Enforced by:`
callout below is **N/A**. Keep writing clear example names and one
behaviour per test; do not disable core, Rails, Lint, Security, or
Performance departments to quiet RSpec. See
[Chapter 37.15](37-rubocop-configuration.md).

Depth model: match the procedural tone of sibling skills' testing chapters
(for example Kotlin's testing chapter): not a framework tutorial, but a set
of reject/rewrite rules with examples.

Sources: [RSpec](https://rspec.info/), [Minitest](https://docs.seattlerb.org/minitest/),
and the enabled `RSpec/*` cops in
`docs/reference-data/rubocop-effective-enabled.txt`. Rules those cops catch
are **Violation** in RSpec suites; shared design rules are **Suggestion**.

## 24.1 Pick one framework (RSpec or Minitest) per application and keep the suite consistent.

> Why? Mixing `assert_equal` and `expect(...).to eq` in one app doubles
> cognitive load and splits shared helpers. Either choice is fine on Ruby
> 4.0; consistency is not. Gems may use Minitest while the app uses RSpec —
> that is normal. **Suggestion.**

```ruby
# bad — both styles in app/test and spec/
assert_equal 1, cart.size
expect(cart.size).to eq(1)

# good — RSpec throughout the app
expect(cart.size).to eq(1)

# good — Minitest throughout the gem
assert_equal 1, cart.size
```

## 24.2 Prefer clear `describe` / `context` / `it` wording that states behaviour and condition.

> Why? Example names are the failure report. Vague strings like `'works'`
> waste CI output. `RSpec/ExampleWording`, `RSpec/ContextWording`, and
> `RSpec/DescribeMethod` push consistent phrasing (`'when …'`, `'with …'`,
> `#method`). **Violation.**

> Enforced by: RSpec/ExampleWording.

```ruby
# bad
describe Cart do
  it 'works' do
    # ...
  end
end

# good
describe Cart do
  describe '#total' do
    context 'when the cart is empty' do
      it 'returns zero' do
        expect(Cart.new.total).to eq(Money.zero)
      end
    end
  end
end
```

## 24.3 Prefer `context` strings that start with `when`, `with`, or `without` (project style).

> Why? `RSpec/ContextWording` enforces a prefix list so context blocks read
> as conditions, not as restated class names. **Violation.**

> Enforced by: RSpec/ContextWording.

```ruby
# bad
context 'empty cart' do
end

# good
context 'when the cart is empty' do
end
```

## 24.4 Prefer `described_class` over repeating the class constant under test.

> Why? Renames and anonymous class tricks stay DRY.
> `RSpec/DescribedClass` enforces it. **Violation.**

> Enforced by: RSpec/DescribedClass.

```ruby
# bad
describe Billing::Invoice do
  it 'creates an invoice' do
    expect(Billing::Invoice.new).to be_a(Billing::Invoice)
  end
end

# good
describe Billing::Invoice do
  it 'creates an invoice' do
    expect(described_class.new).to be_a(described_class)
  end
end
```

## 24.5 Prefer verified doubles over `double('Something')` string names.

> Why? Verifying doubles fail when the API drifts; pure named doubles lie
> quietly. Prefer `instance_double`, `class_double`, or `object_double`.
> `RSpec/VerifiedDoubles` and `RSpec/VerifiedDoubleReference` enforce this.
> **Violation.**

> Enforced by: RSpec/VerifiedDoubles.

```ruby
# bad
mailer = double('Mailer')
allow(mailer).to receive(:deliver)

# good
mailer = instance_double(NotificationMailer, deliver: true)
```

## 24.6 Prefer spies that you have configured; avoid stubbing without verifying intent.

> Why? `RSpec/StubbedMock` and message-expectation cops catch "stubbed but
> never asserted" and "expected but never stubbed" confusion. Prefer
> `have_received` after a spy, or an expectation set before the act.
> **Violation** when the enabled cops fire.

> Enforced by: RSpec/StubbedMock.

```ruby
# bad — mock configured as a stub with no verification path
allow(service).to receive(:call).and_return(true)
service.call

# good
allow(service).to receive(:call).and_return(true)
service.call
expect(service).to have_received(:call)
```

## 24.7 Prefer `expect` over older `should` syntax.

> Why? Modern RSpec is expect-based; implicit should is disabled in current
> defaults. Keep the suite on one syntax. **Suggestion** (config-level),
> reinforced by cops like `RSpec/ImplicitExpect` when they fire.

> Enforced by: RSpec/ImplicitExpect.

```ruby
# bad
cart.total.should == 0

# good
expect(cart.total).to eq(0)
```

## 24.8 Prefer `eq` / `be` / `be_nil` matchers that match the assertion you mean.

> Why? `RSpec/Eq`, `RSpec/BeEq`, `RSpec/BeEql`, `RSpec/BeNil`, and
> `RSpec/IdenticalEqualityAssertion` keep equality checks precise — value
> vs identity vs nil. **Violation.**

> Enforced by: RSpec/BeNil.

```ruby
# bad
expect(user.nickname).to eq(nil)
expect(left).to be == right

# good
expect(user.nickname).to be_nil
expect(left).to eq(right)
expect(left).to be(right) # identity when you truly mean it
```

## 24.9 Prefer one behaviour per example; keep examples short enough to read.

> Why? A 60-line example with five asserts hides failures and names poorly.
> `RSpec/ExampleLength` and `RSpec/MultipleExpectations` encode the
> pressure — split by behaviour when the example grows. **Violation** at
> configured thresholds; treat the spirit as **Suggestion** if you
> consciously raise limits for feature specs.

> Enforced by: RSpec/ExampleLength.

```ruby
# bad
it 'manages the cart' do
  cart = Cart.new
  expect(cart).to be_empty
  cart.add(item)
  expect(cart.size).to eq(1)
  cart.remove(item)
  expect(cart).to be_empty
end

# good
it 'is empty when no items have been added' do
  expect(Cart.new).to be_empty
end

it 'increments size when an item is added' do
  cart = Cart.new
  cart.add(item)
  expect(cart.size).to eq(1)
end
```

## 24.10 Prefer `let` / `subject` discipline: define before use, avoid let side effects.

> Why? `RSpec/LetBeforeExamples`, `RSpec/ScatteredLet`, `RSpec/LetSetup`,
> and `RSpec/LeadingSubject` keep memoized helpers readable. Do not put
> side effects in `let` — use `before` for setup that mutates the world.
> **Violation.**

> Enforced by: RSpec/LetSetup.

```ruby
# bad — let used only for side effect
let!(:user) { create(:user) }
let(:login) { sign_in(user) } # side effect buried in let

# good
let(:user) { create(:user) }

before { sign_in(user) }
```

## 24.11 Prefer `before` / `after` hooks with explicit scope; avoid `before(:all)` for mutable DB state.

> Why? `before(:all)` shares state across examples and flakes under
> reordering. `RSpec/BeforeAfterAll` flags risky uses. Prefer
> `before(:each)` (the default). **Violation.**

> Enforced by: RSpec/BeforeAfterAll.

```ruby
# bad
before(:all) do
  @user = create(:user)
end

# good
let(:user) { create(:user) }
```

## 24.12 Prefer focused examples never committed; keep `fit` / `fdescribe` / `:focus` out of main.

> Why? `RSpec/Focus` fails CI when focus metadata ships. Use focus locally;
> unfocus before push. **Violation.**

> Enforced by: RSpec/Focus.

```ruby
# bad
fit 'returns zero' do
  # ...
end

# good
it 'returns zero' do
  # ...
end
```

## 24.13 Prefer explicit exception expectations with the error class.

> Why? `RSpec/UnspecifiedException` rejects bare `raise_error` without a
> class. Assert the type (and message when meaningful). In Minitest, use
> `assert_raises(ErrorClass)`. **Violation** in RSpec.

> Enforced by: RSpec/UnspecifiedException.

```ruby
# bad
expect { service.call }.to raise_error

# good
expect { service.call }.to raise_error(Billing::DeclinedError)

# good — Minitest
assert_raises(Billing::DeclinedError) { service.call }
```

## 24.14 Prefer predicate matchers over `eq(true)` / `eq(false)` for predicate methods.

> Why? `expect(user).to be_active` reads as the domain question.
> `RSpec/PredicateMatcher` encodes this. **Violation.**

> Enforced by: RSpec/PredicateMatcher.

```ruby
# bad
expect(user.active?).to eq(true)

# good
expect(user).to be_active
```

## 24.15 Prefer deterministic tests: freeze time, stub network, inject clocks.

> Why? Flakes destroy trust. Use `travel_to` / `freeze_time` (Rails —
> chapter 20), WebMock/VCR (or similar) for HTTP, and pure functions where
> possible. Never `sleep` to wait for work (see chapter 22). **Suggestion.**

```ruby
# bad
it 'expires the session' do
  session = Session.start
  sleep 2
  expect(session).to be_expired
end

# good
it 'expires the session after ttl' do
  freeze_time do
    session = Session.start(ttl: 30)
    travel 31.seconds
    expect(session).to be_expired
  end
end
```

## 24.16 Prefer real objects or verified doubles over `any_instance_of`.

> Why? `RSpec/AnyInstance` is a global monkey patch of behaviour and makes
> failures mysterious. Inject dependencies; stub the collaborator you own.
> **Violation.**

> Enforced by: RSpec/AnyInstance.

```ruby
# bad
allow_any_instance_of(Mailer).to receive(:deliver)

# good
mailer = instance_double(Mailer, deliver: true)
service = Service.new(mailer: mailer)
```

## 24.17 Prefer Minitest naming that reads like a specification when you are not on RSpec.

> Why? Minitest has no `context`, but `test_*` methods or
> `describe`/`it` (with minitest/spec) should still state behaviour. Keep
> one assert-theme per test. **Suggestion.**

```ruby
# bad
def test_cart
  cart = Cart.new
  assert_predicate cart, :empty?
  cart.add(Item.new)
  assert_equal 1, cart.size
end

# good
def test_new_cart_is_empty
  assert_predicate Cart.new, :empty?
end

def test_add_increments_size
  cart = Cart.new
  cart.add(Item.new)
  assert_equal 1, cart.size
end
```

## 24.18 Prefer example groups that map to a class or method; avoid grab-bag specs.

> Why? `RSpec/MultipleDescribes`, `RSpec/DescribeClass`, and file-path cops
> (`RSpec/SpecFilePathFormat`, `RSpec/SpecFilePathSuffix`) keep the tree
> navigable: one primary constant per file under `spec/…`. **Violation.**

> Enforced by: RSpec/SpecFilePathSuffix.

```ruby
# bad — spec/models/stuff_spec.rb describing three unrelated classes

# good — spec/models/cart_spec.rb
RSpec.describe Cart do
  # ...
end
```

## 24.19 Prefer pending examples with a reason, or delete them.

> Why? `RSpec/PendingWithoutReason` rejects bare `pending` / `skip` without
> explanation. Track the reason or remove the example. **Violation.**

> Enforced by: RSpec/PendingWithoutReason.

```ruby
# bad
it 'calculates tax' do
  pending
end

# good
it 'calculates tax' do
  pending 'waiting on tax provider sandbox credentials'
end
```

## 24.20 Prefer no expectation-less examples.

> Why? `RSpec/NoExpectationExample` catches examples that never assert.
> If you need a smoke "does not raise" check, assert that explicitly.
> **Violation.**

> Enforced by: RSpec/NoExpectationExample.

```ruby
# bad
it 'runs' do
  service.call
end

# good
it 'runs without raising' do
  expect { service.call }.not_to raise_error
end

# better — assert an observable result
it 'marks the order paid' do
  service.call
  expect(order.reload).to be_paid
end
```
