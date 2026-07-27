<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 17. Struct, Data & Value Objects

Ruby has three common shapes for small value carriers: a plain class with
`attr_reader`, `Struct`, and (since 3.2) `Data`. On Ruby 4.0 the default for
**new immutable value objects** is
[`Data.define`](https://docs.ruby-lang.org/en/4.0/Data.html). `Struct` remains
valid when you need mutability, optional keyword construction quirks, or an
existing API that already speaks Struct. Prefer a real class when behaviour
grows beyond accessors and a couple of derived methods.

Upstream style lives under
[Structs](https://rubystyle.guide/#struct-new),
[no extending Struct.new](https://rubystyle.guide/#no-extend-struct-new), and
[no extending Data.define](https://rubystyle.guide/#no-extend-data-define).
Equality and presentation helpers that often ride on value objects are covered
by [eql](https://rubystyle.guide/#eql) and
[define-to-s](https://rubystyle.guide/#define-to-s).

**Tool alignment:** `Style/DataInheritance` and `Style/StructInheritance`
catch subclassing the factory return value.
`Lint/StructNewOverride` flags `Struct.new` member names that collide with
`Struct` instance methods. Rules a named enabled cop enforces are marked
**Violation**; the rest are **Suggestion**.

## 17.1 Prefer `Data.define` for new immutable value objects.

> Why? `Data` is purpose-built for immutable, keyword-friendly value objects:
> members are read-only, `#==` / `#eql?` / `#hash` compare by value, and
> `#with` returns a copy with selected members replaced. Reaching for
> `Struct.new` (mutable by default) or an ad-hoc class with hand-rolled
> equality is usually more code for a weaker contract. Use `Data` when the
> type is a bag of fields plus light behaviour. **Suggestion.**

```ruby
# bad — mutable Struct for a value that should never change after construction
Point = Struct.new(:x, :y, keyword_init: true)

origin = Point.new(x: 0, y: 0)
origin.x = 1 # silently mutates a "value"

# bad — class boilerplate that only reimplements Data
class Money
  attr_reader :cents, :currency

  def initialize(cents:, currency:)
    @cents = cents
    @currency = currency
  end

  def ==(other)
    other.is_a?(Money) && cents == other.cents && currency == other.currency
  end
  alias eql? ==

  def hash
    [self.class, cents, currency].hash
  end
end

# good
Money = Data.define(:cents, :currency) do
  def format
    format('%.2f %s', cents / 100.0, currency)
  end
end

price = Money.new(cents: 1999, currency: 'USD')
discounted = price.with(cents: 1499)
```

## 17.2 Keep `Struct` when mutability or an existing Struct API is the point.

> Why? `Data` is the wrong tool when callers must assign members after
> construction, when you are extending a library that already returns Struct
> instances, or when you need `Struct`'s historical constructor shapes
> (`Struct.new(:a, :b)` positional args without keywords). Prefer
> `keyword_init: true` for new Structs so call sites stay named. Document
> mutability at the constant. **Suggestion.**

```ruby
# bad — Data forced into a mutable workflow via rebuild noise
Session = Data.define(:token, :expires_at)
session = Session.new(token: 'abc', expires_at: Time.now)
session = session.with(expires_at: Time.now + 3600) # fine, but awkward if
# the domain truly needs in-place updates across many collaborators

# good — Struct when mutation is intentional
Session = Struct.new(:token, :expires_at, keyword_init: true)

session = Session.new(token: 'abc', expires_at: Time.now)
session.expires_at = Time.now + 3600
```

## 17.3 Do not subclass the return value of `Data.define`.

> Why? `Data.define` returns an anonymous class; subclassing that class is
> fragile and is the pattern the style guide rejects under
> [no-extend-data-define](https://rubystyle.guide/#no-extend-data-define). Put
> behaviour in the block passed to `Data.define`, or write a normal class.
> **Violation.**

> Enforced by: Style/DataInheritance.

```ruby
# bad
class Point < Data.define(:x, :y)
  def magnitude
    Math.hypot(x, y)
  end
end

# good
Point = Data.define(:x, :y) do
  def magnitude
    Math.hypot(x, y)
  end
end
```

## 17.4 Do not subclass the return value of `Struct.new`.

> Why? Same inheritance trap as Data: `class Foo < Struct.new(...)` creates
> an anonymous parent and surprises `ancestors`, YAML, and constant lookup.
> The guide's
> [no-extend-struct-new](https://rubystyle.guide/#no-extend-struct-new) rule
> and RuboCop's `Style/StructInheritance` both require assigning the Struct
> to a constant (optionally with a block for methods). **Violation.**

> Enforced by: Style/StructInheritance.

```ruby
# bad
class Customer < Struct.new(:name, :email)
  def domain
    email.split('@').last
  end
end

# good
Customer = Struct.new(:name, :email, keyword_init: true) do
  def domain
    email.split('@').last
  end
end
```

## 17.5 Prefer `Struct.new` / `Data.define` assigned to a constant over inline anonymous types.

> Why? Anonymous Structs and Datas make stack traces, `inspect`, and
> serialization worse (`#<data x=1>` without a name is hard to grep). Naming
> the type is free documentation and matches
> [struct-new](https://rubystyle.guide/#struct-new). **Suggestion.**

```ruby
# bad — anonymous type leaked from a method
def parse_pair(line)
  Struct.new(:left, :right).new(*line.split(':'))
end

# good
Pair = Data.define(:left, :right)

def parse_pair(line)
  left, right = line.split(':', 2)
  Pair.new(left: left, right: right)
end
```

## 17.6 Avoid member names that override `Struct` instance methods.

> Why? Passing `:hash`, `:to_s`, `:members`, or similar to `Struct.new`
> silently overrides core methods and breaks hashing, printing, or
> introspection in ways that only show up later. RuboCop flags the common
> collisions. Rename the member (`digest`, `label`, …). **Violation.**

> Enforced by: Lint/StructNewOverride.

```ruby
# bad — :hash overrides Struct#hash
Fingerprint = Struct.new(:hash, :algo, keyword_init: true)

# good
Fingerprint = Struct.new(:digest, :algo, keyword_init: true)

# good — Data member names are also worth keeping boring and non-colliding
Fingerprint = Data.define(:digest, :algo)
```

## 17.7 Prefer keyword construction for Struct and Data at call sites.

> Why? Positional `Point.new(1, 2)` is a swap bug waiting to happen.
> `Data.define` constructs with keywords by default; for Struct, pass
> `keyword_init: true` (or use the Ruby 3.2+ form that accepts keywords when
> defined that way). Named fields document intent at every call site.
> **Suggestion.**

```ruby
# bad
Point = Struct.new(:x, :y)
Point.new(10, 20)

# good
Point = Struct.new(:x, :y, keyword_init: true)
Point.new(x: 10, y: 20)

# good — Data is keyword-first
Point = Data.define(:x, :y)
Point.new(x: 10, y: 20)
```

## 17.8 Put light behaviour in the `Data.define` / `Struct.new` block; extract a class when behaviour dominates.

> Why? A short `format`, predicate, or conversion method belongs next to the
> members. Once you accumulate validation, collaboration with services, or
> multiple collaborators, a named class (or PORO under `app/models` /
> `app/values` in Rails) is clearer than a 80-line block on a factory.
> **Suggestion.**

```ruby
# bad — Struct block becoming a service object
OrderTotal = Data.define(:line_items, :tax_rate, :coupon) do
  def initialize(...)
    super
    validate!
    apply_coupon!
    persist_audit!
  end
  # ... dozens of methods ...
end

# good — Data stays a value; behaviour lives elsewhere
OrderTotal = Data.define(:cents, :currency)

class OrderTotalCalculator
  def self.call(line_items:, tax_rate:, coupon: nil)
    cents = line_items.sum(&:cents)
    cents = coupon.apply(cents) if coupon
    cents = (cents * (1 + tax_rate)).round
    OrderTotal.new(cents: cents, currency: 'USD')
  end
end
```

## 17.9 Treat `Data` instances as values: copy with `#with`, never mutate internals.

> Why? Freezing the object is not enough if members hold mutable hashes or
> arrays. Prefer immutable members (or freeze them in a custom
> `self.new` / factory). Replacement goes through `#with`. **Suggestion.**

```ruby
# bad — shared mutable member
Config = Data.define(:flags)
config = Config.new(flags: { debug: false })
config.flags[:debug] = true # mutates every alias of this hash

# good — freeze members at the boundary
Config = Data.define(:flags) do
  def self.build(flags)
    new(flags: flags.transform_keys(&:to_sym).freeze)
  end
end

config = Config.build(debug: false)
updated = config.with(flags: config.flags.merge(debug: true).freeze)
```

## 17.10 Prefer value equality; do not compare value objects with `equal?` / `equal`.

> Why? Value objects are equal when their members are equal.
> [eql](https://rubystyle.guide/#eql) and
> [identity-comparison](https://rubystyle.guide/#identity-comparison) remind
> you that `equal?` is object identity. `Data` and well-built Structs already
> implement value `#==` / `#eql?`. Assert on `==` in tests. **Suggestion.**

```ruby
# bad
expect(left.equal?(right)).to be(true)

# good
expect(left).to eq(right)
expect(left).to eql(right)
```

## 17.11 Implement `#to_s` / `#inspect` only when the default is unhelpful; keep them side-effect free.

> Why? [define-to-s](https://rubystyle.guide/#define-to-s) encourages a useful
> string form for domain types. `Data` already provides a solid `#inspect`.
> Override `#to_s` for user-facing formatting, not for logging side effects.
> **Suggestion.**

```ruby
# bad — to_s performs I/O
Money = Data.define(:cents, :currency) do
  def to_s
    Audit.log(self)
    format('%.2f %s', cents / 100.0, currency)
  end
end

# good
Money = Data.define(:cents, :currency) do
  def to_s
    format('%.2f %s', cents / 100.0, currency)
  end
end
```

## 17.12 Avoid `OpenStruct` for application value objects.

> Why? `OpenStruct` is open to typo keys, slower than Struct/Data, and weak
> on intentional API surface. Reserve it for exploratory scripts or genuine
> open bags of properties from untrusted shapes you deliberately accept.
> Prefer `Data.define`, `Struct`, or a class. **Suggestion** — `Style/OpenStructUse`
> exists in RuboCop but is not enabled in this skill's effective config, so
> do not treat this as a Violation here.

```ruby
# bad
require 'ostruct'
user = OpenStruct.new(name: 'Ada', email: 'ada@example.com')
user.nmae # => nil, silent typo

# good
User = Data.define(:name, :email)
user = User.new(name: 'Ada', email: 'ada@example.com')
```

## 17.13 Freeze Struct instances at the boundary when you need Struct but immutability.

> Why? Sometimes an API or serializer expects a Struct, but your domain wants
> immutability. Construct, then `#freeze` (and freeze mutable members). Prefer
> migrating that type to `Data` when you control the definition. **Suggestion.**

```ruby
# acceptable transitional pattern
Point = Struct.new(:x, :y, keyword_init: true)

def origin
  Point.new(x: 0, y: 0).freeze
end

# better when you own the type
Point = Data.define(:x, :y)
```

## 17.14 Pattern-match Data and Struct by deconstructing members, not by digging with `[]` only.

> Why? Ruby 4 pattern matching works cleanly with `Data` / Struct
> deconstruction. Prefer `in Point[x:, y:]` (or array deconstruction) over
> stringly `point[:x]` when the type is known — see chapter 16. **Suggestion.**

```ruby
# bad — loses type information at the call site
def quadrant(point)
  x = point[:x]
  y = point[:y]
  # ...
end

# good
Point = Data.define(:x, :y)

def quadrant(point)
  case point
  in Point[x: 0.., y: 0..] then :i
  in Point[x: ..0, y: 0..] then :ii
  in Point[x: ..0, y: ..0] then :iii
  in Point[x: 0.., y: ..0] then :iv
  end
end
```

## 17.15 Do not use Struct/Data as a substitute for a Hash when the shape is truly open.

> Why? If keys arrive from JSON with unknown fields, a Hash (or a validated
> schema object) is honest. Stuffing arbitrary keys into OpenStruct or
> rebuilding Data members dynamically hides the openness. Use Hash until the
> shape stabilizes, then promote to `Data`. **Suggestion.**

```ruby
# bad — inventing members at runtime
def to_value(hash)
  Data.define(*hash.keys.map(&:to_sym)).new(**hash.transform_keys(&:to_sym))
end

# good — keep open data as a Hash; promote known shapes
User = Data.define(:id, :email)

def to_user(hash)
  User.new(id: hash.fetch('id'), email: hash.fetch('email'))
end
```
