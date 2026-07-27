<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 7. Keyword Arguments & Forwarding

Keyword arguments are the default for new Ruby APIs: they document call
sites, avoid boolean blinders, and compose cleanly with forwarding. This
chapter covers required vs optional keywords, ordering, boolean keywords,
the migration off options hashes, and `...` / `*` / `**` / `&` forwarding on
Ruby 4.0.

Normative anchors live in
[keyword arguments vs option hashes](https://rubystyle.guide/#keyword-arguments-vs-option-hashes),
[keyword arguments vs optional arguments](https://rubystyle.guide/#keyword-arguments-vs-optional-arguments),
[keyword arguments order](https://rubystyle.guide/#keyword-arguments-order),
[boolean keyword arguments](https://rubystyle.guide/#boolean-keyword-arguments),
[merging keyword arguments](https://rubystyle.guide/#merging-keyword-arguments),
[arguments forwarding](https://rubystyle.guide/#arguments-forwarding),
[block forwarding](https://rubystyle.guide/#block-forwarding),
[no optional hash params](https://rubystyle.guide/#no-optional-hash-params), and
[no braces opts hash](https://rubystyle.guide/#no-braces-opts-hash).

**Tool alignment:** `Style/ArgumentsForwarding`, `Style/KeywordParametersOrder`,
`Style/OptionalBooleanParameter`, and hash-related Style cops. Where the
shipped config is silent, rules are **Suggestion**.

## 7.1 Prefer keyword arguments over an options hash for new methods.

> Why? The guide's
> [keyword arguments vs option hashes](https://rubystyle.guide/#keyword-arguments-vs-option-hashes)
> and
> [no optional hash params](https://rubystyle.guide/#no-optional-hash-params)
> rules reject `def foo(options = {})` for ordinary APIs. Keywords give
> required-key checking, typo errors (`unknown keyword`), and self-documenting
> calls. Keep a trailing options hash only when you must accept an open set of
> pass-through keys from a third party.
> **Suggestion.**

```ruby
# bad
def charge(order, options = {})
  currency = options[:currency] || 'USD'
  notify = options.fetch(:notify, true)
end

# good
def charge(order, currency: 'USD', notify: true)
end
```

## 7.2 Prefer keyword arguments over optional positionals when adding flexibility.

> Why? The guide's
> [keyword arguments vs optional arguments](https://rubystyle.guide/#keyword-arguments-vs-optional-arguments)
> rule exists because optional positionals become ambiguous the moment you add
> a second one (`connect(host, 5)` — is `5` timeout or port?). Keywords stay
> clear at every arity.
> **Suggestion.**

```ruby
# bad
def connect(host, timeout = 5, retries = 3)
end

# good
def connect(host:, timeout: 5, retries: 3)
end
```

## 7.3 Put required keyword parameters before optional ones.

> Why? The guide's
> [keyword arguments order](https://rubystyle.guide/#keyword-arguments-order)
> rule and `Style/KeywordParametersOrder` require required kwargs first, then
> optional kwargs with defaults. Mixing them forces readers to scan for which
> keys are mandatory.
> **Violation.**
>
> Enforced by: Style/KeywordParametersOrder.

```ruby
# bad
def book(nights: 1, hotel:, room:)
end

# good
def book(hotel:, room:, nights: 1)
end
```

## 7.4 Pass boolean intent as a keyword, never as a bare positional true/false.

> Why? The guide's
> [boolean keyword arguments](https://rubystyle.guide/#boolean-keyword-arguments)
> rule rejects `send_mail(user, true)` — readers cannot see what `true` means.
> `Style/OptionalBooleanParameter` flags boolean positionals. Name the keyword
> after the behaviour (`notify:`, `strict:`, `overwrite:`).
> **Violation.**
>
> Enforced by: Style/OptionalBooleanParameter.

```ruby
# bad
def deliver(user, true)
end

deliver(user, true)

# good
def deliver(user, notify: true)
end

deliver(user, notify: true)
```

## 7.5 Do not wrap a trailing options hash in braces at the call site when it is the last argument.

> Why? The guide's
> [no braces opts hash](https://rubystyle.guide/#no-braces-opts-hash) rule
> treats `foo(1, { bar: 2 })` as outdated when `foo(1, bar: 2)` works. Braces
> remain correct when the hash is not last, or when you need to pass a single
> Hash positional that is not keyword-mapped.
> **Suggestion.**

```ruby
# bad
charge(order, { currency: 'EUR', notify: false })

# good
charge(order, currency: 'EUR', notify: false)

# good — braces required: hash is a positional value
merge_defaults({ currency: 'EUR' }, fallback)
```

## 7.6 Use `**` when merging or capturing keyword arguments; do not hand-roll hash merges for kwargs.

> Why? The guide's
> [merging keyword arguments](https://rubystyle.guide/#merging-keyword-arguments)
> section prefers keyword splat semantics over stringly hashes. Capturing with
> `**options` keeps keyword nature (symbol keys, `ArgumentError` on unknowns
> when forwarded carefully). Convert with `**hash` only when the hash keys are
> symbols.
> **Suggestion.**

```ruby
# bad
def proxy(user, options = {})
  target.call(user, options.merge(role: :guest))
end

# good
def proxy(user, **options)
  target.call(user, **options, role: :guest)
end
```

## 7.7 Prefer `...` argument forwarding when you pass all arguments through unchanged.

> Why? The guide's
> [arguments forwarding](https://rubystyle.guide/#arguments-forwarding) rule
> and `Style/ArgumentsForwarding` prefer `def proxy(...) = target.call(...)`
> (or a multiline body) over manually naming `*args, **kwargs, &block` when
> nothing inspects the arguments. Forwarding is shorter, allocates less, and
> stays correct when new keyword parameters appear upstream.
> **Violation.**
>
> Enforced by: Style/ArgumentsForwarding.

```ruby
# bad — manual forwarding when nothing is inspected
def proxy(*args, **kwargs, &block)
  target.call(*args, **kwargs, &block)
end

# good
def proxy(...)
  target.call(...)
end
```

## 7.8 Use anonymous block forwarding (`&`) when you only forward the block.

> Why? The guide's
> [block forwarding](https://rubystyle.guide/#block-forwarding) rule allows
> `def each(&) = items.each(&)` / `def each(&block)` depending on style.
> The shipped `.rubocop.yml` sets `Naming/BlockForwarding` to `anonymous`;
> prefer `&` when the block is not referenced by name in the method body.
> If you need to `block.call`, keep a named `&block`.
> **Suggestion** — cite only cops from the effective enabled list; treat the
> anonymous style as house convention even when the Naming cop is not in that
> list.

```ruby
# bad — named block that is only forwarded
def each(&block)
  items.each(&block)
end

# good — anonymous block forwarding
def each(&)
  items.each(&)
end

# good — named because it is invoked
def around(&block)
  setup
  block.call
ensure
  teardown
end
```

## 7.9 Do not mix required positionals, optional positionals, and a large keyword surface without an intentional design.

> Why? Hybrid signatures (`def foo(a, b = 1, c:, d: 2)`) are legal but hard to
> extend. Prefer all-keywords once anything is optional, or a small positional
> head (`def charge(order, currency: 'USD')`) where the primary object is
> obvious. Document the construction story in YARD when the method is public
> gem API ([Chapter 4](04-comments-and-yard.md)).
> **Suggestion.**

```ruby
# bad — hard to extend later
def charge(order, notify = true, currency:, receipt: false)
end

# good — positional head + keywords
def charge(order, currency:, notify: true, receipt: false)
end

# good — all keywords
def charge(order:, currency:, notify: true, receipt: false)
end
```

## 7.10 Raise early on invalid keyword combinations rather than silently ignoring conflicts.

> Why? Keyword args catch unknown keys, but mutually exclusive keys
> (`format: :csv` and `as_json: true`) need an explicit check. Fail with
> `ArgumentError` and a message that names both keys. Pattern matching can
> express closed sets of options — see
> [Chapter 16](16-pattern-matching.md).
> **Suggestion.**

```ruby
# bad — last writer wins silently
def export(format: :csv, as_json: false)
  return JSON.dump(rows) if as_json

  CSV.generate { |csv| rows.each { |r| csv << r } }
end

# good
def export(format: :csv, as_json: false)
  if as_json && format != :json
    raise ArgumentError, 'as_json: true conflicts with format: other than :json'
  end

  # ...
end
```

## 7.11 Prefer double splat at the call site when forwarding a Hash of options that are keywords.

> Why? Passing a Hash without `**` into a keyword method can raise
> `ArgumentError` (wrong number of arguments / unexpected argument) depending
> on separation rules. On modern Ruby, be explicit: `charge(**options)` when
> `options` holds keywords, and keep string-keyed hashes away from keyword
> surfaces.
> **Suggestion.**

```ruby
# bad — ambiguous Hash vs keywords
options = { currency: 'EUR' }
charge(order, options)

# good
charge(order, **options)
```

## 7.12 Do not use `Hash#merge` to simulate keyword defaults when kwargs already provide them.

> Why? Rebuilding defaults with merge reintroduces options-hash bugs (string
> vs symbol keys, shared mutability). Declare defaults on the parameter list;
> override with `**` at the call or with explicit keyword overrides.
> **Suggestion.**

```ruby
# bad
def connect(options = {})
  options = { timeout: 5, retries: 3 }.merge(options)
  # ...
end

# good
def connect(timeout: 5, retries: 3)
  # ...
end
```

## 7.13 When wrapping a method, forward keywords you do not understand with `**` rather than enumerating every key.

> Why? Wrappers that list every keyword of a delegate break whenever the
> delegate grows a parameter. Capture extras with `**rest` and forward
> `**rest`, or use `...` when you forward everything (§7.7). Log or assert on
> `rest` only in debug layers, not in hot paths.
> **Suggestion.**

```ruby
# bad — wrapper falls behind the delegate
def charge(order, currency: 'USD', notify: true)
  Gateway.charge(order, currency: currency, notify: notify)
end

# good — stays compatible when Gateway adds keywords
def charge(order, **options)
  Gateway.charge(order, **options)
end

# good — full forwarding
def charge(...)
  Gateway.charge(...)
end
```

## 7.14 Prefer keyword arguments for DSLs that configure objects; keep block bodies for behaviour.

> Why? `User.create(name: 'Ada', role: :admin)` is clearer than a block that
> assigns attributes unless you need deferred logic. When both appear
> (FactoryBot-style), keywords set data and the block runs after. Do not force
> callers into a block for what a keyword can express.
> **Suggestion.**

```ruby
# bad — block required for static data
def create_user(&block)
  user = User.new
  block.call(user)
  user.save!
end

create_user do |user|
  user.name = 'Ada'
  user.role = :admin
end

# good
def create_user(**attributes)
  User.create!(**attributes)
end

create_user(name: 'Ada', role: :admin)
```
