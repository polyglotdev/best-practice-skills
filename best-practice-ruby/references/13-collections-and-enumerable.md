<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 13. Collections & Enumerable

Arrays, enumerables, and sets are where Ruby code earns its brevity — or
hides O(n) surprises. This chapter covers literal construction, preferring
Enumerable helpers over hand-rolled loops, `map` / `select` / `find` /
`reduce` discipline, size versus count, sets for membership, and not
mutating a collection while you iterate it. Hash-specific rules live in
[Chapter 14](14-hashes-and-keywords.md); `for` versus `each` control-flow
overlap is reinforced in [Chapter 15](15-control-flow.md).

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[collections](https://rubystyle.guide/#collections),
[map find select reduce](https://rubystyle.guide/#map-find-select-reduce-include-size),
[flat map](https://rubystyle.guide/#flat-map),
[count vs size](https://rubystyle.guide/#count-vs-size),
[set vs array](https://rubystyle.guide/#set-vs-array),
[array coercion](https://rubystyle.guide/#array-coercion),
[array join](https://rubystyle.guide/#array-join),
[literal array hash](https://rubystyle.guide/#literal-array-hash),
[percent w](https://rubystyle.guide/#percent-w),
[percent i](https://rubystyle.guide/#percent-i),
[no for loops](https://rubystyle.guide/#no-for-loops),
[reverse each](https://rubystyle.guide/#reverse-each),
[first and last](https://rubystyle.guide/#first-and-last),
[slicing with ranges](https://rubystyle.guide/#slicing-with-ranges),
[accessing elements directly](https://rubystyle.guide/#accessing-elements-directly),
[no modifying collections](https://rubystyle.guide/#no-modifying-collections), and
[no gappy arrays](https://rubystyle.guide/#no-gappy-arrays).

**Tool alignment:** `Style/For`, `Style/WordArray`, `Style/SymbolArray`,
`Style/ArrayJoin`, `Style/EmptyLiteral`, `Style/SlicingWithRange`,
`Style/Sample`, `Style/ZeroLengthPredicate`, `Performance/Count`,
`Performance/Detect`, `Performance/FlatMap`, `Performance/MapCompact`,
`Performance/Size`, `Performance/ReverseEach`, `Performance/Sum`, and
related cops are effectively enabled. Rules those cops catch are
**Violation**; the rest are **Suggestion**.

## 13.1 Prefer array and hash literals over `Array.new` / `Hash.new` / `Array()` / `Hash[]` for ordinary construction.

> Why? The guide's
> [literal array hash](https://rubystyle.guide/#literal-array-hash)
> rule and `Style/EmptyLiteral` prefer `[]` and `{}`. Constructor forms
> are for sized arrays with a default (`Array.new(3, 0)`) or default-proc
> hashes. **Violation.**
>
> Enforced by: Style/EmptyLiteral.

```ruby
# bad
names = Array.new
counts = Hash.new
list = Array()
map = Hash[]

# good
names = []
counts = {}
sized = Array.new(3, 0)
with_default = Hash.new(0)
```

## 13.2 Prefer `each` (and other Enumerable methods) over `for` / `for...in`.

> Why? The guide's
> [no for loops](https://rubystyle.guide/#no-for-loops)
> rule and `Style/For` reject `for` because it does not create a new
> scope — loop variables leak. `each` takes a block with proper scoping.
> **Violation.**
>
> Enforced by: Style/For.

```ruby
# bad
for user in users
  notify(user)
end

# good
users.each do |user|
  notify(user)
end
```

## 13.3 Prefer Enumerable helpers (`map`, `select`/`filter`, `reject`, `find`/`detect`, `any?`, `all?`, `none?`) over hand-built accumulator loops when the helper expresses the intent.

> Why? The guide's
> [map find select reduce](https://rubystyle.guide/#map-find-select-reduce-include-size)
> section is the idiomatic core. Accumulators are fine for multi-step
> reductions that would need several passes or obscure `reduce` blocks;
> they are not fine for a plain projection. **Suggestion.**

```ruby
# bad
names = []
users.each { |user| names << user.name }

# good
names = users.map(&:name)
```

## 13.4 Prefer `find` / `detect` over `select.first` when you want the first match.

> Why? `select.first` builds a temporary array of every match.
> `Performance/Detect` flags that pattern. Use `find` for the first hit
> and `select` when you need all matches. **Violation.**
>
> Enforced by: Performance/Detect.

```ruby
# bad
admin = users.select(&:admin?).first

# good
admin = users.find(&:admin?)
```

## 13.5 Prefer `flat_map` over `map { ... }.flatten` (especially `flatten(1)`).

> Why? The guide's
> [flat map](https://rubystyle.guide/#flat-map)
> rule and `Performance/FlatMap` avoid the intermediate array and make
> one-level flattening explicit. Use `flatten` only when depth is not 1
> or the map step already exists for another reason. **Violation.**
>
> Enforced by: Performance/FlatMap.

```ruby
# bad
ids = users.map(&:order_ids).flatten

# good
ids = users.flat_map(&:order_ids)
```

## 13.6 Prefer `map { ... }.compact` alternatives that avoid the intermediate array when filtering nils — use `filter_map` (or `filter_map`-equivalent style) for map-plus-compact.

> Why? `Performance/MapCompact` and `Style/MapCompactWithConditionalBlock`
> push toward a single pass. Ruby's `filter_map` is the clear expression
> of "map and drop nils." **Violation.**
>
> Enforced by: Performance/MapCompact.

```ruby
# bad
titles = books.map(&:subtitle).compact

# good
titles = books.filter_map(&:subtitle)
```

## 13.7 Prefer `size` / `length` over `count` when you do not pass a block or argument and the collection answers size in O(1).

> Why? The guide's
> [count vs size](https://rubystyle.guide/#count-vs-size)
> rule and `Performance/Count` / `Performance/Size` note that `count`
> may iterate. Use `count` with a block (`count { ... }`) or when the
> object is a lazy enumerator / database relation that defines `count`
> meaningfully. **Violation.**
>
> Enforced by: Performance/Count.

```ruby
# bad
n = users.count

# good
n = users.size
matching = users.count(&:active?)
```

## 13.8 Prefer predicate methods over comparing `size` / `length` to zero.

> Why? `Style/ZeroLengthPredicate` prefers `empty?` / `any?` over
> `size == 0` / `length > 0`. Predicates read as questions and avoid
> magic zeros. **Violation.**
>
> Enforced by: Style/ZeroLengthPredicate.

```ruby
# bad
return if users.length == 0
process if items.size > 0

# good
return if users.empty?
process if items.any?
```

## 13.9 Prefer a `Set` for frequent membership checks over `Array#include?` on large lists.

> Why? The guide's
> [set vs array](https://rubystyle.guide/#set-vs-array)
> rule is algorithmic: `Set#include?` is amortized O(1);
> `Array#include?` is O(n). Build the set once at the boundary. Keep
> arrays when order and duplicates matter. **Suggestion.**

```ruby
# bad
allowed = %w[admin editor viewer]
users.select { |user| allowed.include?(user.role) }

# good
allowed = %w[admin editor viewer].to_set
users.select { |user| allowed.include?(user.role) }
```

## 13.10 Prefer `%w[]` / `%i[]` for word and symbol arrays without interpolation.

> Why? The guide's
> [percent w](https://rubystyle.guide/#percent-w)
> and
> [percent i](https://rubystyle.guide/#percent-i)
> rules, with `Style/WordArray` and `Style/SymbolArray`, shorten
> homogeneous literal lists. Use ordinary `['a b']` when an element
> contains spaces, and `%W` / `%I` when interpolation is required.
> **Violation.**
>
> Enforced by: Style/WordArray.

```ruby
# bad
roles = ['admin', 'editor', 'viewer']
keys = [:id, :name, :email]

# good
roles = %w[admin editor viewer]
keys = %i[id name email]
```

## 13.11 Prefer `Array#join` over `Array#*` when joining into a string with a separator.

> Why? The guide's
> [array join](https://rubystyle.guide/#array-join)
> rule and `Style/ArrayJoin` prefer `join` because `*` looks like
> repetition. **Violation.**
>
> Enforced by: Style/ArrayJoin.

```ruby
# bad
line = parts * ','

# good
line = parts.join(',')
```

## 13.12 Prefer range slicing (`ary[1..]`, `ary[..-2]`) over explicit length arithmetic and `ary[1..-1]` style when ranges express the intent.

> Why? The guide's
> [slicing with ranges](https://rubystyle.guide/#slicing-with-ranges)
> rule and `Style/SlicingWithRange` prefer endless / beginless ranges for
> "rest of collection" slices. **Violation.**
>
> Enforced by: Style/SlicingWithRange.

```ruby
# bad
rest = items[1..-1]

# good
rest = items[1..]
all_but_last = items[..-2]
```

## 13.13 Prefer `first` / `last` / `dig` over manual index access when they express the intent; use indices when the position is domain-meaningful.

> Why? The guide's
> [first and last](https://rubystyle.guide/#first-and-last)
> and
> [accessing elements directly](https://rubystyle.guide/#accessing-elements-directly)
> rules prefer named accessors for ends of collections. Keep `items[0]`
> when the zero offset is part of a protocol (byte buffers, packed
> fields). **Suggestion.**

```ruby
# bad
head = users[0]
tail = users[-1]

# good
head = users.first
tail = users.last
```

## 13.14 Prefer `reverse_each` over `reverse.each`.

> Why? The guide's
> [reverse each](https://rubystyle.guide/#reverse-each)
> rule and `Performance/ReverseEach` avoid allocating a reversed copy.
> **Violation.**
>
> Enforced by: Performance/ReverseEach.

```ruby
# bad
items.reverse.each { |item| process(item) }

# good
items.reverse_each { |item| process(item) }
```

## 13.15 Do not mutate a collection while iterating it; build a new collection or iterate a shallow copy.

> Why? The guide's
> [no modifying collections](https://rubystyle.guide/#no-modifying-collections)
> rule avoids skipped elements and `RuntimeError` from many Ruby
> collections. Prefer `reject`, `filter`, or `delete_if` (which are
> designed for in-place filtering) over `each` + `delete`. **Suggestion.**

```ruby
# bad
users.each do |user|
  users.delete(user) if user.inactive?
end

# good
users.reject!(&:inactive?)
active = users.reject(&:inactive?)
```

## 13.16 Prefer `sum` over `reduce(0, :+)` / `inject(0, :+)` for numeric totals.

> Why? `Performance/Sum` prefers `sum`, which is clearer and optimized
> for numerics. Use `reduce` when the operation is not addition or the
> accumulator is a non-numeric structure. **Violation.**
>
> Enforced by: Performance/Sum.

```ruby
# bad
total = amounts.reduce(0, :+)

# good
total = amounts.sum
```

## 13.17 Prefer `sample` over `shuffle.first` when picking a random element.

> Why? `Style/Sample` avoids shuffling the whole collection to pick one
> element. Pass `n` to `sample` when you need several unique picks.
> **Violation.**
>
> Enforced by: Style/Sample.

```ruby
# bad
winner = users.shuffle.first

# good
winner = users.sample
trio = users.sample(3)
```

## 13.18 Prefer `Array()` coercion carefully — use it for nil-or-one-or-many boundaries, not as a substitute for normalizing your API.

> Why? The guide's
> [array coercion](https://rubystyle.guide/#array-coercion)
> discussion allows `Array(value)` to turn `nil` into `[]` and wrap
> scalars. It is the wrong default inside domain code that should already
> receive arrays. Document the boundary; do not sprinkle `Array()`
> defensively everywhere. **Suggestion.**

```ruby
# bad — hides whether callers pass bad types
def notify(users)
  Array(users).each { |user| mail(user) }
end

# good — explicit boundary
def notify(users)
  users = Array(users)
  users.each { |user| mail(user) }
end

# better — require an array at the API boundary
def notify(users)
  raise ArgumentError, 'users must be an Array' unless users.is_a?(Array)

  users.each { |user| mail(user) }
end
```
