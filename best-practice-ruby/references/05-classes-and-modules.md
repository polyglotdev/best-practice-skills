<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 5. Classes & Modules

Classes and modules are Ruby's primary packaging for behaviour and namespace.
This chapter covers class vs module choice, nested definition style,
constructors, attribute macros, visibility sections, class methods, and when
to reach for `Data.define` instead of an open class. Mixins and refinements
deepen in [Chapter 9](09-modules-mixins-and-refinements.md);
metaprogramming discipline is [Chapter 10](10-metaprogramming-discipline.md);
Struct/Data detail is [Chapter 17](17-struct-data-and-value-objects.md).

Normative anchors live in
[Classes and Modules](https://rubystyle.guide/#classes-modules),
[modules vs classes](https://rubystyle.guide/#modules-vs-classes),
[class and self](https://rubystyle.guide/#class-and-self),
[visibility](https://rubystyle.guide/#visibility),
[attr family](https://rubystyle.guide/#attr_family), and
[namespace definition](https://rubystyle.guide/#namespace-definition).

**Tool alignment:** `Style/ClassAndModuleChildren`, `Style/ClassMethods`,
`Style/AccessModifierDeclarations`, `Style/TrivialAccessors`, `Style/Attr`,
`Style/ModuleFunction`, `Style/DataInheritance`, `Lint/MissingSuper`,
`Lint/ConstantDefinitionInBlock`, and length metrics cover the mechanical
half.

## 5.1 Prefer a module for namespacing and mixins; prefer a class when you need instances or inheritance of state.

> Why? The guide's
> [modules vs classes](https://rubystyle.guide/#modules-vs-classes) rule keeps
> `new` / inheritance for classes and uses modules for roles and namespaces.
> A module that only exists to be instantiated is a class in denial; a class
> used only as a bag of class methods is often a module (or a singleton class)
> in denial.
> **Suggestion.**

```ruby
# bad — class used only as a namespace
class Payment
  class Gateway
  end
end

# good — module namespaces, class instances
module Payment
  class Gateway
    def charge(amount); end
  end
end
```

## 5.2 Define nested classes and modules with compact style (`class Foo::Bar`) outside Rails autoload roots that need nested style.

> Why? The shipped config sets `Style/ClassAndModuleChildren` to `compact`,
> matching the guide's
> [namespace definition](https://rubystyle.guide/#namespace-definition)
> preference for `class Foo::Bar`. Compact form fails when the parent is not
> yet defined — Zeitwerk usually defines parents via path, but classic nested
> form (`module Foo; class Bar`) is required in some Rails paths. The shipped
> config therefore excludes `app/controllers`, `app/helpers`, `app/mailers`,
> `app/jobs`, `config`, `spec`, `test`, and `db` from the compact rule. Follow
> compact in `lib/` and plain Ruby gems; follow nested where the exclude
> applies.
> **Violation.**
>
> Enforced by: Style/ClassAndModuleChildren.

```ruby
# bad — nested form in lib/ (compact preferred)
module Payment
  class Gateway
  end
end

# good — compact in lib/
class Payment::Gateway
end

# good — nested form still appropriate under app/models with Zeitwerk
# (excluded from the compact cop in the shipped config)
module Billing
  class Invoice
  end
end
```

## 5.3 Prefer `class << self` or `def self.` consistently for class methods; do not mix styles in one class body.

> Why? The guide's
> [def self class methods](https://rubystyle.guide/#def-self-class-methods)
> and [class and self](https://rubystyle.guide/#class-and-self) sections allow
> both `def self.foo` and `class << self`, but mixing them in one file is
> noise. `Style/ClassMethods` prefers `def self.` for singleton methods
> defined on the class. Use `class << self` when you need private class
> methods via the singleton class's visibility modifiers in a block.
> **Violation.**
>
> Enforced by: Style/ClassMethods.

```ruby
# bad — mixed styles
class Order
  def self.find_paid
  end

  class << self
    def find_void
    end
  end
end

# good — def self. for simple class methods
class Order
  def self.find_paid
  end

  def self.find_void
  end
end

# good — class << self when privacy needs a block
class Order
  class << self
    def find_paid
      search(:paid)
    end

    private

    def search(status)
      # ...
    end
  end
end
```

## 5.4 Declare visibility with `private` / `protected` / `public` as section headers, indented with the method defs.

> Why? The guide's
> [visibility](https://rubystyle.guide/#visibility),
> [indent public/private/protected](https://rubystyle.guide/#indent-public-private-protected),
> and
> [empty lines around access modifier](https://rubystyle.guide/#empty-lines-around-access-modifier)
> rules treat modifiers as section dividers, not per-method suffixes
> (`private :foo`). `Style/AccessModifierDeclarations` enforces the section
> style. Put a blank line above the modifier (Layout/EmptyLinesAroundAccessModifier).
> **Violation.**
>
> Enforced by: Style/AccessModifierDeclarations.

```ruby
# bad
class Order
  def publish
  end
  private :publish

  def normalize; end
  private :normalize
end

# good
class Order
  def publish
    normalize
  end

  private

  def normalize
  end
end
```

Also enforced by: Layout/EmptyLinesAroundAccessModifier.

## 5.5 Prefer `attr_reader`, `attr_writer`, and `attr_accessor` over hand-rolled trivial accessors.

> Why? The guide's [attr family](https://rubystyle.guide/#attr_family) and
> [attr](https://rubystyle.guide/#attr) rules, plus `Style/TrivialAccessors` and
> `Style/Attr`, reject `def foo; @foo; end` boilerplate. Use the macro; write a
> manual method only when you add logic (lazy default, coercion, freezing).
> **Violation.**
>
> Enforced by: Style/TrivialAccessors.

```ruby
# bad
class User
  def name
    @name
  end

  def name=(value)
    @name = value
  end
end

# good
class User
  attr_accessor :name
end

# good — manual writer earns its keep
class User
  attr_reader :name

  def name=(value)
    @name = value.strip
  end
end
```

Also enforced by: Style/Attr.

## 5.6 Do not use class variables (`@@`); prefer class instance variables or constants.

> Why? The guide's
> [no class vars](https://rubystyle.guide/#no-class-vars) rule exists because
> `@@` is shared across the inheritance tree in surprising ways — a subclass
> assignment can clobber the parent. `Style/ClassVars` flags them. Use
> `@cache = {}` on the singleton class, `class_attribute` in Rails, or a
> constant for immutable config.
> **Violation.**
>
> Enforced by: Style/ClassVars.

```ruby
# bad
class Catalog
  @@items = []

  def self.items
    @@items
  end
end

# good — class instance variable
class Catalog
  @items = []

  class << self
    attr_accessor :items
  end
end

# good — immutable config as a constant
class Catalog
  DEFAULT_LIMIT = 50
end
```

## 5.7 Call `super` from an overridden method that participates in a cooperative hierarchy; do not swallow the parent silently.

> Why? `Lint/MissingSuper` flags constructors and lifecycle hooks
> (`initialize`, certain ActiveSupport callbacks depending on config) that
> override a parent without `super`. Skipping `super` in `initialize` drops
> parent setup and produces half-built objects. When you intentionally replace
> rather than extend behaviour, leave a comment — and prefer composition over
> deep inheritance ([Liskov](https://rubystyle.guide/#liskov),
> [SOLID](https://rubystyle.guide/#solid-design)).
> **Violation.**
>
> Enforced by: Lint/MissingSuper.

```ruby
# bad
class AdminUser < User
  def initialize(name)
    @admin = true
    @name = name
  end
end

# good
class AdminUser < User
  def initialize(name)
    super
    @admin = true
  end
end
```

## 5.8 Do not define constants inside a block (including `Class.new` blocks) unless you understand the scoping trap.

> Why? The guide's
> [no constant definition in block](https://rubystyle.guide/#no-constant-definition-in-block)
> and `Lint/ConstantDefinitionInBlock` catch constants that leak to the
> enclosing namespace or get redefined on every call. Define named classes at
> the top level / module body; use `Class.new` without assigning a constant
> when you truly need an anonymous class.
> **Violation.**
>
> Enforced by: Lint/ConstantDefinitionInBlock.

```ruby
# bad — redefines ::Error on every call in some scopes
def build_gateway
  Class.new do
    Error = Class.new(StandardError)
  end
end

# good
class Gateway
  Error = Class.new(StandardError)
end
```

## 5.9 Prefer `Data.define` for new immutable value objects; use `Struct` only when you need its mutability or legacy API.

> Why? The authoring brief and Ruby 4.0 docs prefer `Data.define` for
> immutable values. The guide still documents
> [`Struct.new`](https://rubystyle.guide/#struct-new); both are valid, but new
> code should default to `Data`. Do not subclass `Data.define` products —
> `Style/DataInheritance` forbids inheriting from `Data.define` return values.
> Full comparison is [Chapter 17](17-struct-data-and-value-objects.md).
> **Violation.**
>
> Enforced by: Style/DataInheritance.

```ruby
# bad — inheriting from Data.define
class Point < Data.define(:x, :y)
  def magnitude
    Math.hypot(x, y)
  end
end

# good — Data.define with a block for behaviour
Point = Data.define(:x, :y) do
  def magnitude
    Math.hypot(x, y)
  end
end

# good — Struct when a mutable legacy shape is required
Slot = Struct.new(:name, :value, keyword_init: true)
```

## 5.10 Keep classes and modules under the Metrics length ceilings; extract collaborators when the file tells multiple stories.

> Why? The shipped config sets `Metrics/ClassLength` and `Metrics/ModuleLength`
> Max to 150 (counting array/hash/heredoc as one). A class past that is usually
> several domains glued together — extract a PORO, a query object, or a module
> under [Chapter 9](09-modules-mixins-and-refinements.md). Treat the metric as
> a prompt to redesign, not as a `# rubocop:disable` tax.
> **Violation.**
>
> Enforced by: Metrics/ClassLength.

```ruby
# bad — god class that mails, charges, and renders
class Order
  def charge!; end
  def email_receipt; end
  def to_pdf; end
  # ... 200 more lines
end

# good — split by responsibility
class Order
  def charge!
    OrderCharger.new(self).call
  end
end

class OrderCharger
  def initialize(order); @order = order; end
  def call; end
end
```

Also enforced by: Metrics/ModuleLength.

## 5.11 Prefer composition over deep inheritance; do not build five-layer class trees for reuse.

> Why? The guide's [Liskov](https://rubystyle.guide/#liskov) and
> [SOLID](https://rubystyle.guide/#solid-design) notes warn that inheritance of
> convenience couples types forever. A decorator, a collaborator injected in
> `initialize`, or a module mixin for a narrow role usually ages better. When
> you inherit, every subclass must be a true subtype — no
> `raise NotImplementedError` for half the parent API.
> **Suggestion.**

```ruby
# bad — inheritance for reuse of a helper
class Refund < Order
  def process; end
end

# good — composition
class Refund
  def initialize(order, gateway:)
    @order = order
    @gateway = gateway
  end

  def process
    @gateway.credit(@order.total)
  end
end
```

## 5.12 Prefer factory class methods (`Person.guest`) over inventing parallel constructors when construction varies.

> Why? The guide's
> [factory methods](https://rubystyle.guide/#factory-methods) rule keeps
> `Person.new` for the canonical construction path and adds named factories for
> variants. Multiple incompatible `initialize` option sets are a smell —
> keyword args with clear names scale further than positional optional flags.
> **Suggestion.**

```ruby
# bad — boolean blinders in initialize
class User
  def initialize(name, admin = false, guest = false)
  end
end

# good
class User
  def initialize(name:, role: :member)
    @name = name
    @role = role
  end

  def self.guest
    new(name: 'Guest', role: :guest)
  end

  def self.admin(name)
    new(name: name, role: :admin)
  end
end
```

## 5.13 Do not leave a single-line class or module body jammed on one line.

> Why? The guide's
> [single-line classes](https://rubystyle.guide/#single-line-classes) rule
> rejects `class Foo; def bar; end; end` as unreadable. `Style/SingleLineMethods`
> and related cops push method bodies to multiline form; empty classes used as
> namespace tags should still use the multiline `class Foo; end` form across
> lines, or better a module.
> **Violation.**
>
> Enforced by: Style/SingleLineMethods.

```ruby
# bad
class Order; def total; @total; end; end

# good
class Order
  def total
    @total
  end
end
```

## 5.14 Group `include`, `extend`, and `prepend` at the top of the class body, with a blank line after the group.

> Why? The guide's
> [mixin grouping](https://rubystyle.guide/#mixin-grouping) and
> [empty lines after module inclusion](https://rubystyle.guide/#empty-lines-after-module-inclusion)
> rules put ancestry declarations where readers look first. `Style/MixinGrouping`
> can enforce grouped form. Details of mixin design are
> [Chapter 9](09-modules-mixins-and-refinements.md).
> **Suggestion.**

```ruby
# bad — includes scattered
class Order
  def total; end

  include Auditable
  attr_reader :id
  extend Forwardable
end

# good
class Order
  include Auditable
  extend Forwardable

  attr_reader :id

  def total; end
end
```

## 5.15 Prefer `module_function` or a dedicated singleton for modules that expose procedural APIs.

> Why? The guide's
> [module function](https://rubystyle.guide/#module-function) rule and
> `Style/ModuleFunction` cover modules that are both mixin and procedural
> facade. For a pure utility surface, prefer a module with
> `module_function` or plain `def self.` methods — and reconsider whether those
> methods should be instance methods on a real type instead.
> **Suggestion.**

```ruby
# bad — ambiguous module used only for procedural calls
module StringUtils
  def self.truncate(str, len)
    str[0, len]
  end
end

# good — clearer home, or module_function when mixin+procedural is intentional
module Truncation
  module_function

  def truncate(str, len)
    str[0, len]
  end
end
```
