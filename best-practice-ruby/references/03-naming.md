<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 3. Naming

A name is the only part of a declaration every reader sees. This chapter covers
what to call classes, modules, methods, variables, constants, predicates, and
files' primary constants — and the small set of Ruby suffixes (`?`, `!`, `=`)
that carry meaning beyond spelling.

The normative source is the Ruby Style Guide's
[Naming Conventions](https://rubystyle.guide/#naming-conventions) section,
especially
[snake_case for methods and vars](https://rubystyle.guide/#snake-case-symbols-methods-vars),
[CamelCase for classes](https://rubystyle.guide/#camelcase-classes),
[SCREAMING_SNAKE_CASE](https://rubystyle.guide/#screaming-snake-case), and
[predicate methods](https://rubystyle.guide/#predicate-methods).

**What to call a `.rb` file**, and how it maps to the constant inside it, is
[Chapter 2, §2.4](02-source-files-and-structure.md). **Bang / non-bang pairs**
and mutator naming deepen in
[Chapter 6](06-methods-and-arguments.md). **Keyword argument names** are
[Chapter 7](07-keyword-arguments-and-forwarding.md).

**Tool alignment:** `Naming/MethodName`, `Naming/VariableName`,
`Naming/ConstantName`, `Naming/ClassAndModuleCamelCase`,
`Naming/PredicateMethod`, `Naming/AsciiIdentifiers`,
`Naming/MemoizedInstanceVariableName`, and
`Naming/RescuedExceptionsVariableName` cover the shapes. Whether a noun is the
*right* noun is **Suggestion** — no regex can answer that.

## 3.1 Build identifiers from ASCII letters, digits, and underscores only.

> Why? The guide's
> [English identifiers](https://rubystyle.guide/#english-identifiers) preference
> and RuboCop's `Naming/AsciiIdentifiers` reject non-ASCII letters in names.
> A non-ASCII identifier survives the parser but breaks grep, breaks some CI
> log encodings, and is painful to type on another keyboard. Digits are fine
> after the first character; leading digits are a syntax error anyway.
> **Violation.**
>
> Enforced by: Naming/AsciiIdentifiers.

```ruby
# bad — non-ASCII identifiers
précision = 0.001
class Résumé
  def naïve_score
    0
  end
end

# good
precision = 0.001
class Resume
  def naive_score
    0
  end
end
```

## 3.2 Write class and module names in CamelCase (PascalCase), as nouns or noun phrases.

> Why? The guide's
> [CamelCase classes](https://rubystyle.guide/#camelcase-classes) rule is
> absolute for type names. A class named with a verb (`ProcessOrder`) is nearly
> always a method wearing a class costume — prefer `OrderProcessor` plus
> `#process`. Modules that namespace follow the same casing
> (`Payment::Gateway`). Compact nested style (`module Foo::Bar`) vs. nested
> style is a Layout/Style concern covered in
> [Chapter 5](05-classes-and-modules.md); the *name* is still CamelCase.
> **Violation.**
>
> Enforced by: Naming/ClassAndModuleCamelCase.

```ruby
# bad — snake_case type, and a verb as a class
class order_processor
end

class ProcessOrder
  def run
  end
end

# good
class OrderProcessor
  def process
  end
end

module Payment
  class Gateway
  end
end
```

## 3.3 Write method names, variable names, and symbols in snake_case.

> Why? The guide's
> [snake_case symbols, methods, vars](https://rubystyle.guide/#snake-case-symbols-methods-vars)
> rule is the default Ruby look. camelCase methods are a JavaScript import and
> fight every core API (`each`, `map`, `find_by`). Numbers inside names follow
> [snake_case with numbers](https://rubystyle.guide/#snake-case-symbols-methods-vars-with-numbers)
> — `http1_client` or `left2_right`, not `HTTP1Client` as a method.
> **Violation.**
>
> Enforced by: Naming/MethodName.

```ruby
# bad
def sendMessage(userId)
  userName = userId.to_s
  :QueuedJob
end

# good
def send_message(user_id)
  user_name = user_id.to_s
  :queued_job
end
```

Also enforced by: Naming/VariableName.

## 3.4 Write constants in SCREAMING_SNAKE_CASE.

> Why? The guide's
> [SCREAMING_SNAKE_CASE](https://rubystyle.guide/#screaming-snake-case) rule
> marks a constant as a stable, shared binding. camelCase constants look like
> classes; lowercase constants look like methods. Freeze deep values when the
> constant holds a collection — see `Style/MutableConstant` and
> [Chapter 12](12-strings-and-symbols.md) / [Chapter 13](13-collections-and-enumerable.md).
> **Violation.**
>
> Enforced by: Naming/ConstantName.

```ruby
# bad
MaxRetries = 3
default_timeout = 30

# good
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

Also related: Style/MutableConstant.

## 3.5 End a predicate method with `?` and make it return a boolean-ish value.

> Why? The guide's
> [bool methods qmark](https://rubystyle.guide/#bool-methods-qmark) and
> [predicate methods](https://rubystyle.guide/#predicate-methods) rules make
> `?` the signal that a method is safe to use in a conditional. Returning
> `nil`/`Object` from a `?` method trains callers to write `if foo.bar?` and
> accidentally rely on truthiness of a non-boolean. Prefer actual `true` /
> `false` (or a documented boolean-ish protocol).
> **Violation.**
>
> Enforced by: Naming/PredicateMethod.

```ruby
# bad — predicate without ?, and ? method returning a user
def active
  status == :active
end

def admin?
  user if role == :admin
end

# good
def active?
  status == :active
end

def admin?
  role == :admin
end
```

## 3.6 Do not prefix a predicate with `is_`, `has_`, or `can_` when `?` already carries that meaning.

> Why? The guide's
> [bool methods prefix](https://rubystyle.guide/#bool-methods-prefix) rule
> treats `is_active?` as redundant noise — `active?` is enough. English-speaking
> APIs in ActiveSupport (`blank?`, `present?`, `empty?`) never use the prefix.
> Keep `has_` only when the root would be ungrammatical or ambiguous without it
> (`has_key?` is inherited from Hash; for new APIs prefer `key?`).
> **Suggestion.**

```ruby
# bad
def is_active?
  status == :active
end

def has_items?
  items.any?
end

# good
def active?
  status == :active
end

def items?
  items.any?
end
```

## 3.7 End a dangerous or mutating method with `!` only when a safer non-bang twin exists.

> Why? The guide's
> [dangerous method bang](https://rubystyle.guide/#dangerous-method-bang) rule
> reserves `!` for the "more dangerous" half of a pair — `save` / `save!`,
> `exit` / `exit!`, or mutate-in-place vs return-copy. A lone `def update!`
> with no `update` is not communicating a choice; it is shouting. Rails bang
> methods (`save!`, `update!`, `find_or_create_by!`) follow this pair pattern
> and raise on failure — see [Chapter 26](26-activerecord-models.md).
> **Suggestion.**

```ruby
# bad — bang with no non-bang twin
def publish!
  # mutates and also sends email
end

# good — pair: safe returns boolean / copy; bang raises or mutates
def save
  # returns false on validation failure
end

def save!
  save || raise(ActiveRecord::RecordInvalid, self)
end
```

## 3.8 Name a non-predicate, non-bang method as a verb or verb phrase; name a pure query as a noun only when it is cheap and idempotent.

> Why? A bare noun method (`order.total`) reads as an attribute and invites
> callers to assume it is cheap. If the method hits the network or fills a
> cache, prefer `fetch_total` / `calculate_total`. Attribute readers via
> `attr_reader` keep the noun form because they *are* cheap. Accessor naming
> detail is in the guide's
> [accessor mutator method names](https://rubystyle.guide/#accessor_mutator_method_names).
> **Suggestion.**

```ruby
# bad — noun that hides a query
def exchange_rates
  HTTP.get('/rates').parse
end

# good
def fetch_exchange_rates
  HTTP.get('/rates').parse
end

# good — cheap attribute
attr_reader :currency
```

## 3.9 Name memoized instance variables after the method, with a leading `@` and optional matching underscore policy from RuboCop.

> Why? `Naming/MemoizedInstanceVariableName` requires the memoized ivar to
> match the method name (commonly `@foo` for `def foo`). A mismatch
> (`def users; @accounts ||= ...`) is a rename hazard and confuses readers who
> grep for one name. Prefer `||=` memoization only for values that cannot be
> `false` or `nil` meaningfully — otherwise use `defined?(@foo)` or
> `ActiveSupport::Memoizable` patterns carefully (see later chapters).
> **Violation.**
>
> Enforced by: Naming/MemoizedInstanceVariableName.

```ruby
# bad — ivar name disagrees with the method
def users
  @accounts ||= User.active.to_a
end

# good
def users
  @users ||= User.active.to_a
end
```

## 3.10 Name a rescued exception variable `error` (not `e`, `ex`, or `exception`).

> Why? The shipped config sets `Naming/RescuedExceptionsVariableName` with
> `PreferredName: error`. Single-letter `e` is ungrepable and collides with
> every other `e` in the method. Consistency matters more than the specific
> word — and this repo already chose `error`.
> **Violation.**
>
> Enforced by: Naming/RescuedExceptionsVariableName.

```ruby
# bad
begin
  charge!(order)
rescue PaymentError => e
  log.warn(e.message)
end

# good
begin
  charge!(order)
rescue PaymentError => error
  log.warn(error.message)
end
```

## 3.11 Prefer English words; avoid cryptic Perl-isms and stamped abbreviations.

> Why? The guide's
> [English syntax](https://rubystyle.guide/#english-syntax) and
> [no cryptic Perlisms](https://rubystyle.guide/#no-cryptic-perlisms) rules
> reject `$:` / `$?`-style globals in application code and discourage
> private abbreviations (`usr`, `msg`, `mgr`) that only the author expands
> correctly. Prefer `$!` alternatives (`error` in rescue) and stdlib names
> (`$LOAD_PATH` over `$:`).
> **Suggestion.**

```ruby
# bad
$:.unshift(lib)
msg = usr.nm

# good
$LOAD_PATH.unshift(lib)
message = user.name
```

## 3.12 Do not encode a variable's type, scope, or storage in its name.

> Why? Hungarian prefixes (`str_name`, `arr_users`, `@@class_cache` as a
> *name* concern) restate what the declaration already says and go stale the
> first time the type changes. Ruby's `@` / `@@` / `$` prefixes already mark
> scope; repeating `m_` or `s_` is Java muscle memory. **Suggestion.**

```ruby
# bad
str_tenant_id = tenant.id
arr_pending = []
hash_options = {}

# good
tenant_id = tenant.id
pending = []
options = {}
```

## 3.13 Do not build a type name out of a meaningless word: `Manager`, `Handler`, `Processor`, `Util`, `Helper`, `Info`, `Data`.

> Why? These words postpone deciding what the class does, which is why such
> classes grow without limit. `UserDataManager` has no boundary that would tell
> you a method does not belong in it. A `Util` module is usually a set of
> methods that should be instance methods, refinements, or well-named POROs.
> Prefer a noun that states the responsibility (`UserRepository`,
> `WelcomeMailer`).
> **Suggestion.**

```ruby
# bad
class UserDataManager
  def load(id); end
  def send_welcome_email(user); end
  def export_csv(users); end
end

# good
class UserRepository
  def load(id); end
end

class WelcomeMailer
  def send(user); end
end
```

## 3.14 Never prefix an interface-like module with `I`, and avoid an `Impl` suffix on the only implementation.

> Why? `IPaymentGateway` is a C#/Java import. In Ruby the file says `module` or
> `class`, and duck typing means the "interface" is usually an implicit
> protocol. Name the module after the role (`PaymentGateway`), and name each
> implementation after what distinguishes it (`StripePaymentGateway`,
> `FakePaymentGateway`). `FooImpl` only names a category, not a distinction.
> **Suggestion.**

```ruby
# bad
module IPaymentGateway
end

class PaymentGatewayImpl
end

# good
module PaymentGateway
end

class StripePaymentGateway
  include PaymentGateway
end

class FakePaymentGateway
  include PaymentGateway
end
```

## 3.15 Prefix unused block and method arguments with `_` or name them `_`.

> Why? The guide's
> [underscore unused vars](https://rubystyle.guide/#underscore-unused-vars) and
> [trailing underscore variables](https://rubystyle.guide/#trailing-underscore-variables)
> conventions mark intentional non-use so `Lint/UnusedMethodArgument` /
> `Lint/UnusedBlockArgument` stay quiet for the right reason. Prefer a
> descriptive `_order` over a bare `_` when the position's meaning helps the
> reader.
> **Violation.**
>
> Enforced by: Lint/UnusedMethodArgument.

```ruby
# bad — unused arg looks accidental
def charge(order, _notify)
  gateway.charge(order)
end

items.map { |item, index| item.price }

# good
def charge(order, _notify)
  gateway.charge(order)
end

items.map { |item, _index| item.price }
# or
items.map(&:price)
```

Also enforced by: Lint/UnusedBlockArgument.

## 3.16 Do not shadow an outer local with an inner one.

> Why? The guide's [no shadowing](https://rubystyle.guide/#no-shadowing) rule
> and `Lint/ShadowingOuterLocalVariable` catch the silent failure mode where a
> block parameter displaces a method argument of the same name. The code
> compiles, refers to the wrong binding, and produces a plausible wrong answer.
> **Violation.**
>
> Enforced by: Lint/ShadowingOuterLocalVariable.

```ruby
# bad — block param shadows method arg
def reconcile(order, candidates)
  candidates.each do |order|
    report(compare(order, order))
  end
end

# good
def reconcile(order, candidates)
  candidates.each do |candidate|
    report(compare(order, candidate))
  end
end
```

## 3.17 Name enum-like constants and status values clearly; prefer symbols or a dedicated type over magic strings.

> Why? Scattered `'paid'` / `'Paid'` / `'PAID'` strings drift. A SCREAMING
> constant or a well-known symbol (`:paid`) gives a single grep target. When
> the set is closed and behaviour varies by case, prefer a small class or
> `Data.define` over a bare string — see
> [Chapter 17](17-struct-data-and-value-objects.md). Rails enums are
> [Chapter 26](26-activerecord-models.md).
> **Suggestion.**

```ruby
# bad
order.status == 'Paid'

# good
PAID = 'paid'
order.status == PAID

# good — symbol protocol
order.status == :paid
```

## 3.18 Prefer clear block parameter names over single letters, except in idiomatic one-line enumerations.

> Why? `Naming/BlockParameterName` allows short names but a three-line block
> with `|x, y|` is hostile. Use `|item|`, `|row|`, `|account|` once the block
> grows past a single expression. Single letters remain fine for `|_|` unused,
> numeric reduces (`|sum, n|`), and truly idiomatic `matrix[i][j]` math.
> **Suggestion.**

```ruby
# bad — opaque once the block grows
users.each do |u|
  send_mail(u.email)
  audit(u.id)
  refresh(u)
end

# good
users.each do |user|
  send_mail(user.email)
  audit(user.id)
  refresh(user)
end

# good — idiomatic one-liner
prices.map { |p| p * tax_rate }
```
