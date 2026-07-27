<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 9. Modules, Mixins & Refinements

Modules are Ruby's dual-purpose tool: namespaces for constants and methods,
and mixins that compose behaviour into classes via `include`, `extend`, and
`prepend`. This chapter covers when a module beats a class, how to group and
order mixin declarations, `module_function` versus `extend self`, empty-line
discipline around inclusions, and when refinements are the right scoped
alternative to open classes. Class layout and inheritance belong in
[Chapter 5](05-classes-and-modules.md); metaprogramming that defines methods
on modules belongs in [Chapter 10](10-metaprogramming-discipline.md).

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[modules vs classes](https://rubystyle.guide/#modules-vs-classes),
[mixin grouping](https://rubystyle.guide/#mixin-grouping),
[module_function](https://rubystyle.guide/#module-function),
[empty lines after module inclusion](https://rubystyle.guide/#empty-lines-after-module-inclusion),
[no monkey-patching](https://rubystyle.guide/#no-monkey-patching), and
[duck typing](https://rubystyle.guide/#duck-typing), together with the
[Ruby 4.0 Refinement docs](https://docs.ruby-lang.org/en/4.0/syntax/refinements_rdoc.html)
for lexical patching. There is no harvested rubystyle.guide anchor named
`refinements`; refinement rules cite the language docs only.

**Tool alignment:** `Style/MixinGrouping`, `Style/MixinUsage`,
`Style/ModuleFunction`, `Style/ClassAndModuleChildren`, and
`Lint/SendWithMixinArgument` are effectively enabled. Rules those cops catch
are **Violation**; the rest are **Suggestion**.

## 9.1 Prefer a module over a class when the type has no instances and exists only to hold methods or constants.

> Why? The guide's
> [modules vs classes](https://rubystyle.guide/#modules-vs-classes)
> rule is direct: use a module for a namespace or a bag of methods that
> never needs `new`. Instantiating a "utility class" is noise; inheriting
> from one to steal helpers is worse. A module documents "this is not an
> object identity." **Suggestion.**

```ruby
# bad — never instantiated, yet readers look for .new
class StringUtils
  def self.blank?(value)
    value.nil? || value.strip.empty?
  end
end

# good
module StringUtils
  module_function

  def blank?(value)
    value.nil? || value.strip.empty?
  end
end
```

## 9.2 Use a class when you need identity, state, or polymorphic instances; do not fake that with a module plus `extend`.

> Why? Modules compose behaviour; classes create instances. If callers need
> `PaymentGateway.new(credentials)` and multiple concurrent instances with
> different state, a class is the right shape. Stuffing instance variables
> onto a singleton module obscures lifecycle and testing seams.
> **Suggestion.**

```ruby
# bad — module pretending to be a stateful service
module PaymentGateway
  class << self
    attr_accessor :api_key

    def charge(amount)
      Client.post('/charges', amount: amount, key: api_key)
    end
  end
end

# good — instance holds credentials; easy to stub in tests
class PaymentGateway
  def initialize(api_key:)
    @api_key = api_key
  end

  def charge(amount)
    Client.post('/charges', amount: amount, key: @api_key)
  end
end
```

## 9.3 Group consecutive `include`, `extend`, and `prepend` calls of the same kind together; do not interleave unrelated declarations.

> Why? The guide's
> [mixin grouping](https://rubystyle.guide/#mixin-grouping)
> rule and RuboCop's `Style/MixinGrouping` keep the ancestor-chain edits in
> one visual block so a reader can see the full composition at a glance.
> Scattering mixins between `attr_*`, constants, and methods hides the
> lookup order. **Violation.**
>
> Enforced by: Style/MixinGrouping.

```ruby
# bad — includes split by attributes and constants
class Order
  include Auditable
  attr_reader :id
  include Billable
  STATUS = :open
  extend ClassMethods
end

# good — same-kind mixins grouped; then attributes and constants
class Order
  include Auditable
  include Billable

  extend ClassMethods

  STATUS = :open

  attr_reader :id
end
```

## 9.4 Prefer `include` for instance behaviour, `extend` for class/singleton behaviour, and `prepend` only when you must wrap an existing method.

> Why? `include` inserts the module above `Object` in the instance
> ancestor chain; `extend` adds methods to the singleton class;
> `prepend` inserts *before* the class so `super` reaches the original
> method. Casual `prepend` for ordinary helpers makes `super` mandatory and
> surprises readers who expect `include` override semantics. Reserve
> `prepend` for cross-cutting wrappers (instrumentation, soft deprecation)
> with a comment naming why wrap-before is required. **Suggestion.**

```ruby
# bad — prepend used when include would do
module Timestamped
  def touch
    @touched_at = Time.now
  end
end

class Document
  prepend Timestamped
end

# good — include for additive instance API; prepend only to wrap
module Timestamped
  def touch
    @touched_at = Time.now
  end
end

class Document
  include Timestamped
end

module SoftDelete
  def destroy
    update!(deleted_at: Time.now)
  end
end

class Record
  # Must run before ActiveRecord#destroy
  prepend SoftDelete
end
```

## 9.5 Do not call `include`, `extend`, or `prepend` via `send` / `__send__` with a dynamic module list unless the call site is a documented DSL.

> Why? `Lint/SendWithMixinArgument` flags `send(:include, Mod)` because it
> bypasses the normal mixin syntax and hides which modules enter the
> ancestor chain. Dynamic mixins also defeat static review. Prefer a plain
> `include` list; if a plugin registry must compose at boot, do it in one
> boot-time method with an explicit allow-list, not scattered `send`.
> **Violation.**
>
> Enforced by: Lint/SendWithMixinArgument.

```ruby
# bad
mod = Auditable
Order.send(:include, mod)

# good
class Order
  include Auditable
end
```

## 9.6 Leave a blank line after a block of mixin declarations before the next non-mixin body element.

> Why? The guide's
> [empty lines after module inclusion](https://rubystyle.guide/#empty-lines-after-module-inclusion)
> rule separates composition from the class's own surface. RuboCop's
> layout cops around bodies reinforce the same visual break. Without it,
> the first method looks like part of the mixin list. **Suggestion.**

```ruby
# bad
class Invoice
  include Billable
  include Auditable
  def total
    line_items.sum(&:amount)
  end
end

# good
class Invoice
  include Billable
  include Auditable

  def total
    line_items.sum(&:amount)
  end
end
```

## 9.7 Prefer `module_function` (or a consistent `extend self`) for modules that expose both callable functions and mixin instance methods; pick one style per module.

> Why? The guide's
> [module_function](https://rubystyle.guide/#module-function)
> section and `Style/ModuleFunction` require a single, idiomatic way to
> dual-purpose a module. Mixing `extend self`, manual `module_function :x`,
> and `class << self` in one file makes privacy and override behaviour
> unpredictable — `module_function` makes copies that become private
> instance methods. **Violation.**
>
> Enforced by: Style/ModuleFunction.

```ruby
# bad — three mechanisms for the same idea
module Text
  extend self

  def normalize(value)
    value.to_s.strip
  end

  module_function :normalize

  class << self
    def blank?(value)
      normalize(value).empty?
    end
  end
end

# good — one mechanism
module Text
  module_function

  def normalize(value)
    value.to_s.strip
  end

  def blank?(value)
    normalize(value).empty?
  end
end
```

## 9.8 Do not use `include` / `extend` / `prepend` at the top level outside a class or module body.

> Why? `Style/MixinUsage` rejects top-level mixin calls because they alter
> `Object` or `main`'s singleton in ways that leak across the process.
> Application code should compose inside an explicit namespace. Scripts that
> truly need a top-level helper should define a method on `main` or a
> dedicated module instead. **Violation.**
>
> Enforced by: Style/MixinUsage.

```ruby
# bad — pollutes Object / main
include Enumerable

# good — scoped to the type that needs it
class Playlist
  include Enumerable

  def each(&block)
    @tracks.each(&block)
  end
end
```

## 9.9 Prefer compact (`Foo::Bar`) or nested (`module Foo; class Bar`) namespace style consistently within a project; do not redefine an outer module with `class` syntax.

> Why? `Style/ClassAndModuleChildren` and the guide's namespace guidance keep
> one nesting style so autoloading (Zeitwerk) and grep stay predictable.
> Writing `class Foo::Bar` when `Foo` is a module is fine; writing
> `class Foo` when `Foo` was already a module (or the reverse) corrupts
> the constant table. Prefer nested definitions for files that own the
> outer namespace, and compact style for one-off namespaced classes in
> their own file when the outer module already exists. **Violation.**
>
> Enforced by: Style/ClassAndModuleChildren.

```ruby
# bad — inconsistent children style in the same tree without project rule
module Billing
  class Invoice
  end
end

class Billing::Receipt
end

# good — one file owns the outer module with nested children
module Billing
  class Invoice
  end

  class Receipt
  end
end
```

## 9.10 Prefer duck typing over `is_a?` / `kind_of?` checks that gate mixin behaviour.

> Why? The guide's
> [duck typing](https://rubystyle.guide/#duck-typing)
> rule prefers responding to the needed protocol over walking the ancestor
> chain. Mixins especially should not require `is_a?(SomeModule)` —
> callers that implement the same methods should work. Use `respond_to?`
> only at true boundaries (deserialization, plugin loaders); inside domain
> code, just call the method. **Suggestion.**

```ruby
# bad
def serialize(obj)
  raise TypeError unless obj.is_a?(Serializable)

  obj.to_h
end

# good
def serialize(obj)
  obj.to_h
end
```

## 9.11 Prefer refinements over open-class monkey patches when you must add behaviour to a core or third-party type.

> Why? The guide's
> [no monkey-patching](https://rubystyle.guide/#no-monkey-patching)
> rule forbids reopening `String`, `Array`, and gem classes in global
> scope. [Refinements](https://docs.ruby-lang.org/en/4.0/syntax/refinements_rdoc.html)
> activate only in files (or modules) that `using` them, so patches stay
> lexical. Use a wrapper object or plain helper module when a refinement
> is heavier than the call sites justify. **Suggestion.**

```ruby
# bad — global monkey patch
class String
  def blank?
    strip.empty?
  end
end

# good — lexical refinement
module StringBlank
  refine String do
    def blank?
      strip.empty?
    end
  end
end

module Reports
  using StringBlank

  def self.empty_title?(title)
    title.blank?
  end
end
```

## 9.12 Activate refinements with `using` at the file or module scope that needs them; do not expect refinements to apply through method calls from unrefined scopes.

> Why? Refinement activation is lexical. A method defined in a scope that
> did not `using` the refinement will not see refined methods, even if the
> *caller* activated them. Put `using` next to the code that calls the
> refined API, document the refinement module at the top of the file, and
> avoid refining widely used core methods that make stack traces hard to
> follow. **Suggestion.**

```ruby
# bad — refinement active in caller, but helper was defined elsewhere
module StringBlank
  refine String do
    def blank?
      strip.empty?
    end
  end
end

def empty_title?(title)
  title.blank? # NoMethodError — this scope never used the refinement
end

using StringBlank
empty_title?('  ')

# good — using wraps the definitions that call refined methods
module StringBlank
  refine String do
    def blank?
      strip.empty?
    end
  end
end

module Titles
  using StringBlank

  module_function

  def empty_title?(title)
    title.blank?
  end
end
```

## 9.13 Keep mixin modules focused on one protocol; extract a second module when a file grows unrelated helper piles.

> Why? Fat mixins recreate multiple inheritance's worst failure mode:
> unrelated methods sharing one ancestor slot and colliding on common
> names (`#call`, `#process`, `#run`). Split by capability
> (`Billable`, `Auditable`, `Publishable`) and compose at the class.
> If a mixin needs many collaborators, it is often a collaborator object
> instead. **Suggestion.**

```ruby
# bad — kitchen-sink mixin
module ModelExtras
  def bill!
  end

  def audit!
  end

  def to_csv
  end

  def geocode!
  end
end

# good — one protocol per module
module Billable
  def bill!
  end
end

module Auditable
  def audit!
  end
end

class Account
  include Billable
  include Auditable
end
```

## 9.14 Prefer explicit collaborator injection over mixins when the behaviour needs configuration or replaceable dependencies.

> Why? Mixins bake a single implementation into the ancestor chain.
> Services that talk to HTTP, clocks, or feature flags are easier to test
> as injected objects. Use a mixin only when the behaviour is intrinsic
> to many types (enumeration, comparison) and needs no per-instance
> wiring. **Suggestion.**

```ruby
# bad — mixin hides the HTTP client
module Chargeable
  def charge!(amount)
    HttpClient.post('/charge', amount: amount)
  end
end

class Order
  include Chargeable
end

# good — dependency is visible and swappable
class Order
  def initialize(gateway:)
    @gateway = gateway
  end

  def charge!(amount)
    @gateway.charge(amount)
  end
end
```

## 9.15 Document the required host methods a mixin expects, and fail fast in `included` / `prepended` only when the contract is non-obvious.

> Why? Duck typing still needs a contract. A short comment listing required
> methods (`#id`, `#save!`) beats runtime `respond_to?` noise in hot paths.
> Use an `included` hook to raise a clear `TypeError` only for mixins that
> are unsafe to include into the wrong host — not for every helper module.
> **Suggestion.**

```ruby
# bad — silent failure when host lacks #save!
module Publishable
  def publish!
    update!(published_at: Time.now)
  end
end

# good — contract documented; optional included check for safety-critical mixins
# Host must implement #update! (ActiveRecord-style).
module Publishable
  def self.included(base)
    return if base.method_defined?(:update!)

    raise TypeError, "#{base} must implement #update! to include Publishable"
  end

  def publish!
    update!(published_at: Time.now)
  end
end
```
