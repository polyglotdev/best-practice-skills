<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 14. Hashes & Keywords

Hashes are Ruby's primary structural type for named data; keyword
arguments are the method-parameter form of the same idea. This chapter
covers hash literal style, `fetch` versus `[]`, transform helpers,
`each_key` / `each_value`, key types, merging kwargs, and preferring
real keyword parameters over options hashes. Method signature design for
kwargs and argument forwarding is covered in depth in
[Chapter 7](07-keyword-arguments-and-forwarding.md); this chapter focuses
on hash values in ordinary code.

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[hash literals](https://rubystyle.guide/#hash-literals),
[hash fetch](https://rubystyle.guide/#hash-fetch),
[hash fetch defaults](https://rubystyle.guide/#hash-fetch-defaults),
[hash each](https://rubystyle.guide/#hash-each),
[hash transform methods](https://rubystyle.guide/#hash-transform-methods),
[hash key](https://rubystyle.guide/#hash-key),
[ordered hashes](https://rubystyle.guide/#ordered-hashes),
[no mixed hash syntaxes](https://rubystyle.guide/#no-mixed-hash-syntaxes),
[no mutable keys](https://rubystyle.guide/#no-mutable-keys),
[symbols as keys](https://rubystyle.guide/#symbols-as-keys),
[keyword arguments vs option hashes](https://rubystyle.guide/#keyword-arguments-vs-option-hashes),
[no optional hash params](https://rubystyle.guide/#no-optional-hash-params),
[no braces opts hash](https://rubystyle.guide/#no-braces-opts-hash),
[hash literal as last array item](https://rubystyle.guide/#hash-literal-as-last-array-item),
[merging keyword arguments](https://rubystyle.guide/#merging-keyword-arguments),
[use hash blocks](https://rubystyle.guide/#use-hash-blocks), and
[hash values at](https://rubystyle.guide/#hash-values-at-and-hash-fetch-values).

**Tool alignment:** `Style/HashSyntax`, `Style/HashEachMethods`,
`Style/HashTransformKeys`, `Style/HashTransformValues`,
`Style/PreferredHashMethods`, `Style/HashAsLastArrayItem`,
`Lint/DuplicateHashKey`, and related cops are effectively enabled. Rules
those cops catch are **Violation**; the rest are **Suggestion**.

## 14.1 Prefer the Ruby 1.9+ symbol-key syntax (`key: value`) over the rocket (`:key => value`) for symbol keys.

> Why? The guide's
> [hash literals](https://rubystyle.guide/#hash-literals)
> rule and `Style/HashSyntax` standardize on the shorter form. Keep the
> rocket for non-symbol keys (`'Content-Type' => '...'`). **Violation.**
>
> Enforced by: Style/HashSyntax.

```ruby
# bad
user = { :name => 'Ada', :id => 1 }

# good
user = { name: 'Ada', id: 1 }
headers = { 'Content-Type' => 'application/json' }
```

## 14.2 Do not mix rocket and label syntaxes in the same hash literal.

> Why? The guide's
> [no mixed hash syntaxes](https://rubystyle.guide/#no-mixed-hash-syntaxes)
> rule keeps one literal readable. Split into two hashes and merge if
> key classes differ and force different spellings. **Suggestion.**

```ruby
# bad
config = { host: 'localhost', :port => 443 }

# good
config = { host: 'localhost', port: 443 }
```

## 14.3 Prefer `fetch` over `[]` when a missing key is an error (or when you need a default that is not `nil`).

> Why? The guide's
> [hash fetch](https://rubystyle.guide/#hash-fetch)
> and
> [hash fetch defaults](https://rubystyle.guide/#hash-fetch-defaults)
> rules make absence loud. `hash[:k]` returns `nil` for both missing keys
> and present-`nil` values; `fetch` distinguishes them. Prefer
> `fetch(key) { expensive }` over `fetch(key, expensive)` when the
> default should be lazy. **Suggestion.**

```ruby
# bad
host = config[:host] # nil means missing or null?

# good
host = config.fetch(:host)
timeout = config.fetch(:timeout, 30)
token = config.fetch(:token) { ENV.fetch('TOKEN') }
```

## 14.4 Prefer `key?` / `value?` over `has_key?` / `has_value?`.

> Why? The guide's
> [hash key](https://rubystyle.guide/#hash-key)
> preference and `Style/PreferredHashMethods` standardize on the shorter
> predicates. **Violation.**
>
> Enforced by: Style/PreferredHashMethods.

```ruby
# bad
if payload.has_key?(:id)
  process(payload)
end

# good
if payload.key?(:id)
  process(payload)
end
```

## 14.5 Prefer `each_key` / `each_value` over `keys.each` / `values.each`.

> Why? The guide's
> [hash each](https://rubystyle.guide/#hash-each)
> rule and `Style/HashEachMethods` avoid allocating the intermediate
> array of keys or values. **Violation.**
>
> Enforced by: Style/HashEachMethods.

```ruby
# bad
config.keys.each { |key| warn key }
config.values.each { |value| validate(value) }

# good
config.each_key { |key| warn key }
config.each_value { |value| validate(value) }
```

## 14.6 Prefer `transform_keys` / `transform_values` over `each_with_object` or `map` + `to_h` for key/value mapping.

> Why? The guide's
> [hash transform methods](https://rubystyle.guide/#hash-transform-methods)
> rule and `Style/HashTransformKeys` /
> `Style/HashTransformValues` name the intent and allocate once.
> **Violation.**
>
> Enforced by: Style/HashTransformKeys.

```ruby
# bad
normalized = {}
headers.each { |key, value| normalized[key.downcase] = value }

# good
normalized = headers.transform_keys(&:downcase)
amounts = prices.transform_values { |cents| cents / 100.0 }
```

## 14.7 Prefer `values_at` / `fetch_values` when reading several keys at once.

> Why? The guide's
> [hash values at](https://rubystyle.guide/#hash-values-at-and-hash-fetch-values)
> rule unpacks parallel assignment cleanly and fails fast with
> `fetch_values` when any key is missing. **Suggestion.**

```ruby
# bad
name = row[:name]
email = row[:email]
id = row[:id]

# good
name, email, id = row.values_at(:name, :email, :id)
name, email, id = row.fetch_values(:name, :email, :id)
```

## 14.8 Prefer keyword arguments over an options hash for methods you control.

> Why? The guide's
> [keyword arguments vs option hashes](https://rubystyle.guide/#keyword-arguments-vs-option-hashes)
> and
> [no optional hash params](https://rubystyle.guide/#no-optional-hash-params)
> rules give callers named parameters, required-key checking, and
> forwarding with `**`. Options hashes are for truly open-ended
> dictionaries (HTTP headers, JSON merge patches). **Suggestion.**

```ruby
# bad
def connect(opts = {})
  host = opts[:host] || 'localhost'
  port = opts[:port] || 443
  Client.new(host, port)
end

# good
def connect(host: 'localhost', port: 443)
  Client.new(host, port)
end
```

## 14.9 Prefer bare keyword lists at call sites; do not wrap the trailing options hash in braces when it is kwargs-shaped.

> Why? The guide's
> [no braces opts hash](https://rubystyle.guide/#no-braces-opts-hash)
> rule prefers `draw(color: 'red')` over `draw({ color: 'red' })` for
> the last argument. Braces remain correct when the hash is not last or
> when you pass a positional Hash object intentionally. **Suggestion.**

```ruby
# bad
draw({ color: 'red', width: 2 })

# good
draw(color: 'red', width: 2)
```

## 14.10 Prefer braces around a trailing hash that is an array element when omitting them would bind to the method call instead.

> Why? The guide's
> [hash literal as last array item](https://rubystyle.guide/#hash-literal-as-last-array-item)
> rule and `Style/HashAsLastArrayItem` keep `[1, 2, { a: 1 }]`
> unambiguous. **Violation.**
>
> Enforced by: Style/HashAsLastArrayItem.

```ruby
# bad — depending on Ruby parsing / style, trailing bare hash is unclear
pairs = [1, 2, a: 1]

# good
pairs = [1, 2, { a: 1 }]
```

## 14.11 Prefer immutable keys (symbols, frozen strings, numbers); do not use mutable objects as hash keys.

> Why? The guide's
> [no mutable keys](https://rubystyle.guide/#no-mutable-keys)
> rule avoids lost entries when a key's `#hash` changes after insertion.
> Freeze strings used as keys, or prefer symbols. **Suggestion.**

```ruby
# bad
key = 'user'
data = { key => 1 }
key.upcase! # data can no longer find the entry reliably

# good
data = { user: 1 }
data = { 'user'.freeze => 1 }
```

## 14.12 Rely on insertion order only when the language guarantee matters; do not treat hashes as unordered bags in comments or APIs.

> Why? The guide's
> [ordered hashes](https://rubystyle.guide/#ordered-hashes)
> note reflects that Ruby hashes enumerate in insertion order. Document
> order-sensitive APIs explicitly; do not invent a parallel `Array` of
> pairs unless you need duplicate keys. **Suggestion.**

```ruby
# bad — comment lies on modern Ruby
# Hash order is undefined, sort before display
config.each { |key, value| puts "#{key}=#{value}" }

# good — insertion order is the display order we want
STEPS = { validate: 1, charge: 2, fulfill: 3 }.freeze
STEPS.each_key { |step| run(step) }
```

## 14.13 Prefer `**` merging / double-splat expansion over `merge` when assembling keyword argument hashes for a call.

> Why? The guide's
> [merging keyword arguments](https://rubystyle.guide/#merging-keyword-arguments)
> guidance keeps kwargs as kwargs: `save(**defaults, **overrides)`.
> Use `merge` when you are building a Hash data structure, not when you
> are about to splat into keywords. **Suggestion.**

```ruby
# bad
create(user.merge(role: 'admin'))

# good
create(**user, role: 'admin')
create(**defaults, **overrides)
```

## 14.14 Prefer a default block on `Hash.new` when the default value is mutable; do not reuse one mutable default instance.

> Why? The guide's
> [use hash blocks](https://rubystyle.guide/#use-hash-blocks)
> advice (and the classic `Hash.new([])` bug) requires
> `Hash.new { |h, k| h[k] = [] }` so each missing key gets a fresh
> array. A shared `[]` default mutates across keys. **Suggestion.**

```ruby
# bad — every key shares one array
groups = Hash.new([])
groups[:a] << 1
groups[:b] << 2 # also appears under :a

# good
groups = Hash.new { |hash, key| hash[key] = [] }
groups[:a] << 1
groups[:b] << 2
```

## 14.15 Do not duplicate keys in a literal hash.

> Why? `Lint/DuplicateHashKey` catches the silent overwrite. Earlier keys
> vanish without error. **Violation.**
>
> Enforced by: Lint/DuplicateHashKey.

```ruby
# bad
config = { host: 'a.example', host: 'b.example' }

# good
config = { host: 'b.example' }
```

## 14.16 Prefer `except` / `slice` (stdlib or ActiveSupport) over hand-deleting keys when projecting a hash.

> Why? Projection methods state the keep/drop set without mutating the
> source. Hand `delete` loops mutate and hide the retained key list.
> In plain Ruby 4.0, `Hash#except` and `Hash#slice` are available.
> **Suggestion.**

```ruby
# bad
filtered = attrs.dup
filtered.delete(:password)
filtered.delete(:token)

# good
filtered = attrs.except(:password, :token)
public_attrs = attrs.slice(:id, :name, :email)
```

## 14.17 Prefer `transform_values` with `Style/HashTransformValues` over building a new hash in an `each` loop for value-only maps.

> Why? Value-only rewrites are the twin of 14.6. RuboCop's
> `Style/HashTransformValues` catches the loop form. Keep
> `each_with_object` only when the conversion needs the key and value
> together in a non-transform shape. **Violation.**
>
> Enforced by: Style/HashTransformValues.

```ruby
# bad
cents = {}
prices.each { |sku, dollars| cents[sku] = (dollars * 100).to_i }

# good
cents = prices.transform_values { |dollars| (dollars * 100).to_i }
```

## 14.18 Prefer not treating `HashWithIndifferentAccess` (or string/symbol dual access) as the default hash type outside Rails params boundaries.

> Why? Indifferent access hides key-type bugs and allocates wrapper
> objects. At the controller boundary, strong params already give you a
> constrained object; convert to a plain symbol-keyed hash (or a
> `Data` / keyword struct) before passing into domain code. See also
> [symbols as keys](https://rubystyle.guide/#symbols-as-keys).
> **Suggestion.**

```ruby
# bad — indifferent hash leaked into the domain
def charge(attrs)
  Money.charge(attrs[:amount] || attrs['amount'])
end

# good — normalize once at the edge
def charge(amount:)
  Money.charge(amount)
end

def charge_from_params(params)
  charge(amount: params.require(:amount))
end
```
