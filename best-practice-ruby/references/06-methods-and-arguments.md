<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 6. Methods & Arguments

Methods are the unit of reuse in Ruby. This chapter covers definition shape,
parentheses, argument lists, optional positional args, return style, bang
pairs, nested methods, and length/complexity ceilings. Keyword arguments and
`...` forwarding are [Chapter 7](07-keyword-arguments-and-forwarding.md).
Blocks as parameters are [Chapter 8](08-blocks-procs-and-lambdas.md).

Normative anchors live in
[Methods](https://rubystyle.guide/#methods),
[method parentheses](https://rubystyle.guide/#method-parens),
[short methods](https://rubystyle.guide/#short-methods),
[too many params](https://rubystyle.guide/#too-many-params),
[optional arguments](https://rubystyle.guide/#optional-arguments),
[no nested methods](https://rubystyle.guide/#no-nested-methods),
[no explicit return](https://rubystyle.guide/#no-explicit-return), and
[three is the number](https://rubystyle.guide/#three-is-the-number-thou-shalt-count).

**Tool alignment:** `Style/MethodDefParentheses`, `Style/DefWithParentheses`,
`Style/RedundantReturn`, `Style/SingleLineMethods`, `Style/EmptyMethod`,
`Style/OptionalArguments`, `Lint/UnusedMethodArgument`,
`Lint/NestedMethodDefinition`, `Metrics/MethodLength`, `Metrics/AbcSize`,
`Metrics/ParameterLists`, and related cops.

## 6.1 Always use parentheses in a method definition that takes parameters.

> Why? The guide's
> [method parentheses](https://rubystyle.guide/#method-parens) rule and the
> shipped `Style/MethodDefParentheses` (`require_parentheses`) require
> `def foo(bar)` not `def foo bar`. Definitions without args may omit empty
> parens (`def foo`) — do not write `def foo()` unless you need to emphasize
> arity zero for a DSL.
> **Violation.**
>
> Enforced by: Style/MethodDefParentheses.

```ruby
# bad
def charge amount, currency
end

# good
def charge(amount, currency)
end

# good — no args, no empty parens
def total
  @total
end
```

Also related: Style/DefWithParentheses.

## 6.2 Keep methods short; treat twenty lines as a soft ceiling, not a badge.

> Why? The guide's [short methods](https://rubystyle.guide/#short-methods)
> rule and shipped `Metrics/MethodLength` Max of 20 (with array/hash/heredoc
> counting as one) push extraction. A long method is usually several steps that
> deserve names. Disable only when the method is an irreducible worksheet
> (see [Chapter 4, §4.12](04-comments-and-yard.md)).
> **Violation.**
>
> Enforced by: Metrics/MethodLength.

```ruby
# bad — multi-responsibility method
def process(order)
  validate(order)
  tax = compute_tax(order)
  # ... fifteen more steps inline
end

# good
def process(order)
  validate!(order)
  receipt = charge!(order)
  notify!(order, receipt)
  receipt
end
```

## 6.3 Limit positional parameters; prefer keyword arguments once the list grows past three.

> Why? The guide's
> [too many params](https://rubystyle.guide/#too-many-params) and
> [three is the number](https://rubystyle.guide/#three-is-the-number-thou-shalt-count)
> rules flag long positional lists. The shipped `Metrics/ParameterLists` Max is
> 5 with `CountKeywordArgs: false`, so keywords do not inflate the metric —
> use them. At call sites, keywords document intent; positionals do not.
> Chapter 7 owns the keyword rules in depth.
> **Violation.**
>
> Enforced by: Metrics/ParameterLists.

```ruby
# bad
def book(hotel, room, nights, discount, loyalty, notify)
end

# good
def book(hotel:, room:, nights:, discount: 0, loyalty: nil, notify: true)
end
```

## 6.4 Put optional positional arguments after required ones; prefer keywords for new optional API.

> Why? The guide's
> [optional arguments](https://rubystyle.guide/#optional-arguments) rule and
> `Style/OptionalArguments` require required params first. Optional positionals
> also interact badly with added parameters later — prefer
> [keyword arguments vs optional arguments](https://rubystyle.guide/#keyword-arguments-vs-optional-arguments)
> for new surfaces (Chapter 7).
> **Violation.**
>
> Enforced by: Style/OptionalArguments.

```ruby
# bad — optional before required
def connect(timeout = 5, host)
end

# good — required first (legacy positional)
def connect(host, timeout = 5)
end

# good — keywords for new code
def connect(host:, timeout: 5)
end
```

## 6.5 Never use a mutable object as a default argument value.

> Why? The guide's
> [no mutable defaults](https://rubystyle.guide/#no-mutable-defaults) rule
> exists because default expressions are evaluated once at method definition
> time. An `[]` or `{}` default is shared across calls, producing
> cross-request leaks that look like heisenbugs. Use `nil` and assign inside
> the method body.
> **Suggestion.**

```ruby
# bad — shared array across calls
def tags(list = [])
  list << 'default'
end

# good
def tags(list = nil)
  list = [] if list.nil?
  list << 'default'
end

# good — keywords, same pattern
def tags(list: nil)
  list = [] if list.nil?
  list << 'default'
end
```

## 6.6 Omit explicit `return` when the last expression is the return value.

> Why? The guide's
> [no explicit return](https://rubystyle.guide/#no-explicit-return) rule and
> `Style/RedundantReturn` treat a trailing `return value` as noise. Keep
> `return` for early exits. In a method that intentionally returns `nil`, an
> ending `nil` or empty method body is clearer than `return`.
> **Violation.**
>
> Enforced by: Style/RedundantReturn.

```ruby
# bad
def total
  return @items.sum(&:price)
end

# good
def total
  @items.sum(&:price)
end

# good — early return stays
def total
  return 0 if @items.empty?

  @items.sum(&:price)
end
```

## 6.7 Do not define methods inside methods.

> Why? The guide's
> [no nested methods](https://rubystyle.guide/#no-nested-methods) rule and
> `Lint/NestedMethodDefinition` flag `def` inside `def`. Nested defs redefine
> the outer method on the receiver/class on every call and are almost never
> what the author meant — use a block, a lambda, or a private method on the
> class.
> **Violation.**
>
> Enforced by: Lint/NestedMethodDefinition.

```ruby
# bad
def process
  def helper
    1
  end
  helper
end

# good
def process
  helper
end

private

def helper
  1
end
```

## 6.8 Do not write a single-line method with a trailing `; end` body.

> Why? The guide's
> [no single-line methods](https://rubystyle.guide/#no-single-line-methods)
> rule and `Style/SingleLineMethods` reject `def foo; bar; end`. Endless
> methods (`def foo = bar`) are available and sometimes fine for trivial
> one-liners — see [endless methods](https://rubystyle.guide/#endless-methods)
> — but prefer a normal multiline body for anything with control flow.
> **Violation.**
>
> Enforced by: Style/SingleLineMethods.

```ruby
# bad
def total; @items.sum(&:price); end

# good
def total
  @items.sum(&:price)
end

# good — endless method for a trivial reader (optional)
def total = @items.sum(&:price)
```

## 6.9 Use empty method form `def foo; end` only for intentional stubs; prefer `def foo = nil` or raise in abstract hooks.

> Why? `Style/EmptyMethod` distinguishes compact empty methods from multiline
> empty bodies. An empty hook that should be overridden is clearer as
> `raise NotImplementedError` in libraries, or omitted entirely when the
> superclass should not advertise it. Do not leave empty methods as permanent
> TODOs.
> **Suggestion.**

```ruby
# bad — silent no-op that looks unfinished
def on_success
end

# good — explicit no-op when the API requires the method
def on_success; end

# good — abstract template
def on_success
  raise NotImplementedError, "#{self.class}#on_success"
end
```

## 6.10 Prefix unused parameters with `_` rather than leaving them unexplained.

> Why? Covered also in [Chapter 3, §3.15](03-naming.md). At the method layer,
> `Lint/UnusedMethodArgument` fails CI when an arg is unused without the
> underscore convention. Do not delete an argument that is part of an overridden
> signature — rename to `_event` instead.
> **Violation.**
>
> Enforced by: Lint/UnusedMethodArgument.

```ruby
# bad
def handle(event, context)
  publish(event)
end

# good
def handle(event, _context)
  publish(event)
end
```

## 6.11 Keep ABC size and cyclomatic complexity under the shipped ceilings; extract predicates and helpers when branches multiply.

> Why? `Metrics/AbcSize` Max 20 and `Metrics/CyclomaticComplexity` /
> `Metrics/PerceivedComplexity` Max 10 are soft design prompts. Nested
> conditionals are also discouraged by the guide's
> [no nested conditionals](https://rubystyle.guide/#no-nested-conditionals)
> advice — prefer guard clauses (`Style/GuardClause` helps). Complexity in
> Rails controllers usually means a missing service object
> ([Chapter 34](34-service-objects.md)).
> **Violation.**
>
> Enforced by: Metrics/AbcSize.

```ruby
# bad — nested branching
def fee(order)
  if order.domestic?
    if order.express?
      10
    else
      5
    end
  else
    order.express? ? 25 : 15
  end
end

# good — table or guards
def fee(order)
  return 10 if order.domestic? && order.express?
  return 5 if order.domestic?
  return 25 if order.express?

  15
end
```

Also enforced by: Metrics/CyclomaticComplexity.

## 6.12 Prefer guard clauses at the top of a method over deep `if` wrapping.

> Why? Flattened methods read top-to-bottom as preconditions then happy path.
> `Style/GuardClause` suggests this rewrite. Combine with §6.6 so each guard
> is an early `return` / `raise` without a redundant trailing return.
> **Suggestion.**

```ruby
# bad
def publish(order)
  if order.paid?
    if order.email.present?
      Mailer.receipt(order).deliver_later
    end
  end
end

# good
def publish(order)
  return unless order.paid?
  return if order.email.blank?

  Mailer.receipt(order).deliver_later
end
```

## 6.13 Use parentheses at call sites when the method takes arguments; omit them for zero-arg calls that read as attributes.

> Why? The guide's
> [method call parentheses](https://rubystyle.guide/#method-call-parentheses)
> family distinguishes declarative DSLs from ordinary calls. For ordinary
> application code, `charge(order)` is clearer than `charge order`, and
> `Style/MethodCallWithoutArgsParentheses` prefers `total` over `total()` for
> zero-arg calls. Keyword-only call rules deepen in Chapter 7.
> **Suggestion.**

```ruby
# bad — bareword args in ordinary code
charge order, currency

# good
charge(order, currency)

# good — zero-arg reads as a property
order.total
```

## 6.14 Do not mutate arguments unless the method name and docs make that the contract.

> Why? The guide's
> [no param mutations](https://rubystyle.guide/#no-param-mutations) rule
> prevents surprising side effects on caller-owned objects. If you must mutate,
> use a bang name and document it. Prefer returning a new object.
> **Suggestion.**

```ruby
# bad — silently mutates caller's hash
def normalize(options)
  options[:timeout] ||= 5
  options
end

# good
def normalize(options)
  options = options.dup
  options[:timeout] ||= 5
  options
end

# good — explicit bang contract
def normalize!(options)
  options[:timeout] ||= 5
  options
end
```

## 6.15 Prefer a single main path; use `alias_method` (not `alias`) when you need a synonym.

> Why? The guide's
> [alias method](https://rubystyle.guide/#alias-method) and
> [alias method lexically](https://rubystyle.guide/#alias-method-lexically)
> rules prefer `alias_method :new, :old` because it is a method call and
> respects scope. `Style/Alias` can enforce this. Do not pile synonyms to
> paper over a bad primary name — rename instead.
> **Suggestion.**

```ruby
# bad
alias total amount

# good
alias_method :total, :amount
```

## 6.16 Do not use parallel assignment for unrelated values just to save lines.

> Why? The guide's
> [parallel assignment](https://rubystyle.guide/#parallel-assignment) section
> allows swapping and multi-return unpacking, but unrelated initials
> (`a, b = 1, 2`) are harder to breakpoint and diff. Prefer separate lines
> unless the values are a natural tuple.
> **Suggestion.**

```ruby
# bad
name, timeout, retries = 'Ada', 5, 3

# good
name = 'Ada'
timeout = 5
retries = 3

# good — natural tuple / swap
left, right = right, left
name, email = parse_identity(payload)
```

## 6.17 Avoid `and` / `or` for control flow; use `&&` / `||` and separate statements.

> Why? The guide's
> [no and or or](https://rubystyle.guide/#no-and-or-or) rule and `Style/AndOr`
> exist because `and`/`or` have different precedence than `&&`/`||` and cause
> subtle bugs in assignment. Reserve `and`/`or` for the rare intentional
> control-flow idiom only if the team forbids them entirely in `.rubocop.yml`
> (this skill's defaults flag them via Style/AndOr when enabled).
> **Violation.**
>
> Enforced by: Style/AndOr.

```ruby
# bad
ok = save and notify

# good
ok = save && notify

# good — clearer as statements
saved = save
notify if saved
```
