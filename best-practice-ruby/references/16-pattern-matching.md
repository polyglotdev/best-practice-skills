<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 16. Pattern Matching

Pattern matching is a stable Ruby feature (no experimental warning on
Ruby 4.0). Prefer `case ... in` when you are destructuring arrays, hashes,
or objects that implement `deconstruct` / `deconstruct_keys`, and keep
ordinary `case ... when` for triple-equals style matching on classes and
ranges. This chapter sticks to idioms documented for Ruby 4.0 — no invented
APIs, gems, or speculative syntax.

The rules draw on the
[Ruby 4.0 pattern matching docs](https://docs.ruby-lang.org/en/4.0/syntax/pattern_matching_rdoc.html)
and the [Ruby Style Guide](https://rubystyle.guide/) anchors that touch
case/pattern punctuation:
[no in-pattern semicolons](https://rubystyle.guide/#no-in-pattern-semicolons),
[one-line cases](https://rubystyle.guide/#one-line-cases), and
[no when semicolons](https://rubystyle.guide/#no-when-semicolons).
Ordinary `case` / `when` control-flow choice remains
[Chapter 15](15-control-flow.md).

**Tool alignment:** few cops are pattern-matching-specific. `Style/WhenThen`,
`Style/MultilineWhenThen`, `Style/HashLikeCase`, and `Lint/DuplicateCaseCondition`
still apply to `case` forms. Prefer **Suggestion** unless a listed cop
clearly fires.

## 16.1 Prefer `case ... in` when the branch needs to destructure structure; prefer `case ... when` when matching with `===`.

> Why? `when` uses `===` (classes, ranges, regexps, values). `in` matches
> shapes and binds variables from arrays, hashes, and custom
> deconstructors. Using `in` for a plain class check is noisier than
> `when String`; using `when` for nested hash shapes forces manual digs.
> See the
> [pattern matching docs](https://docs.ruby-lang.org/en/4.0/syntax/pattern_matching_rdoc.html).
> **Suggestion.**

```ruby
# bad — when with hand-rolled destructuring
case payload
when Hash
  name = payload[:name]
  age = payload[:age]
  greet(name, age)
end

# good — in destructures
case payload
in { name:, age: }
  greet(name, age)
end

# good — when still right for === matching
case value
when String then format_string(value)
when Integer then format_int(value)
when 0..9 then format_digit(value)
end
```

## 16.2 Prefer `case expr` / `in pattern` over a bare `in` assignment when you need multiple branches or an else.

> Why? One-line `expr => pattern` and `expr in pattern` are for single
> patterns. Multi-branch matching belongs in `case`. Mixing styles in one
> method makes skimming harder. **Suggestion.**

```ruby
# bad — nested one-line matches pretending to be a switch
if payload in { type: 'user', name: }
  handle_user(name)
elsif payload in { type: 'bot', name: }
  handle_bot(name)
end

# good
case payload
in { type: 'user', name: }
  handle_user(name)
in { type: 'bot', name: }
  handle_bot(name)
else
  raise ArgumentError, "unknown payload: #{payload.inspect}"
end
```

## 16.3 Prefer hash patterns with required keys named explicitly; use `**nil` when extra keys must be rejected.

> Why? `{ name:, age: }` matches hashes that have at least those keys
> and ignores extras by default. The documented closed form is
> `{ name:, age:, **nil }`, which fails when unexpected keys appear.
> Bind only the keys you use; do not invent other closed-hash syntax.
> **Suggestion.**

```ruby
# bad — digs after a weak match
case row
in Hash
  name = row.fetch(:name)
  mail(name)
end

# good — open shape (extras allowed)
case row
in { name: }
  mail(name)
end

# good — closed shape (extras rejected)
case row
in { name:, age:, **nil }
  greet(name, age)
end
```
## 16.4 Prefer array patterns with `*` rest for variable-length lists; pin lengths when the arity is part of the contract.

> Why? `[first, *rest]`, `[*leading, last]`, and find patterns like
> `[*pre, :separator, *post]` are the documented ways to express sequence
> shapes. Matching a fixed arity with `[a, b, c]` fails when a fourth
> element appears — use that when arity is the contract. **Suggestion.**

```ruby
# bad
case items
in Array
  first = items[0]
  rest = items[1..]
  process(first, rest)
end

# good
case items
in [first, *rest]
  process(first, rest)
in []
  process_empty
end
```
## 16.5 Prefer alternative patterns (`|`) over duplicated branches that differ only by a constant or class.

> Why? `Integer | Float` (and similar) is the documented alternative
> pattern form. Duplicated bodies drift apart. Keep alternatives short;
> extract a method when the shared body grows. **Suggestion.**

```ruby
# bad
case value
in Integer
  format_number(value)
in Float
  format_number(value)
end

# good
case value
in Integer | Float
  format_number(value)
in String
  format_string(value)
end
```

## 16.6 Prefer `=>` as-patterns when you need both a substructure match and the whole value (or a typed binding).

> Why? `Integer => n` and `Array => items` are documented as-patterns.
> They replace a separate assignment after the match and keep the type
> check next to the name. **Suggestion.**

```ruby
# bad
case response
in { body: }
  body = response[:body]
  parse(body)
end

# good
case response
in { body: String => body }
  parse(body)
end
```

## 16.7 Prefer pattern guards (`if` / `unless`) on `in` branches for predicates that are not structural.

> Why? Guards are part of the
> [documented pattern matching syntax](https://docs.ruby-lang.org/en/4.0/syntax/pattern_matching_rdoc.html).
> Keep structure in the pattern and boolean checks in the guard so the
> shape stays readable. **Suggestion.**

```ruby
# bad — buries the age check in the branch with a manual reject
case user
in { age: Integer => age }
  next unless age >= 18

  admit(user)
end

# good
case user
in { age: Integer => age } if age >= 18
  admit(user)
in { age: Integer }
  reject_underage(user)
end
```

## 16.8 Prefer variable pinning (`^local`) when the pattern must equal an existing value; do not rebind over a name you meant to compare.

> Why? An unadorned identifier in a pattern binds a new variable. Pinning
> with `^` compares against an already-bound local (or expression in
> `^(...)`). Forgetting to pin is a common silent logic bug. **Suggestion.**

```ruby
# bad — rebinds expected instead of comparing
expected = :admin
case role
in expected
  grant!
end

# good — pin compares to the existing local
expected = :admin
case role
in ^expected
  grant!
end
```

## 16.9 Implement `deconstruct` / `deconstruct_keys` on your types when they are natural pattern subjects; keep the returned shapes stable.

> Why? Custom matching uses those two methods as documented — there is no
> separate "pattern match protocol" API beyond them. Return arrays from
> `deconstruct` and hashes (or `nil` for unknown keys) from
> `deconstruct_keys`. Changing shapes is a breaking change for every
> `in` site. **Suggestion.**

```ruby
# bad — force callers to convert to hashes by hand
class Point
  attr_reader :x, :y

  def initialize(x, y)
    @x = x
    @y = y
  end
end

case point
in Point
  x = point.x
  y = point.y
  draw(x, y)
end

# good
class Point
  attr_reader :x, :y

  def initialize(x, y)
    @x = x
    @y = y
  end

  def deconstruct
    [x, y]
  end

  def deconstruct_keys(_keys)
    { x: x, y: y }
  end
end

case point
in Point[x, y]
  draw(x, y)
in Point[x:, y:]
  draw(x, y)
end
```

## 16.10 Prefer `expr => pattern` for single-pattern destructuring assignments; prefer `expr in pattern` when you need a boolean match without binding-heavy branches.

> Why? Both one-line forms are documented. `=>` raises `NoMatchingPatternError`
> on failure (good for "this must be the shape"). `in` returns
> `true` / `false` (good for conditionals). Do not rescue
> `NoMatchingPatternError` for ordinary control flow — use `in` or an
> `else` branch instead. **Suggestion.**

```ruby
# bad — rescue as control flow
begin
  { name: name } => payload
rescue NoMatchingPatternError
  return
end

# good — boolean form
return unless payload in { name: }

# good — assignment form when failure is exceptional
config => { host:, port: }
connect(host, port)
```

## 16.11 Do not put semicolons between pattern branches or after `in` / `when` patterns to compress multiple statements onto one line.

> Why? The guide's
> [no in-pattern semicolons](https://rubystyle.guide/#no-in-pattern-semicolons)
> and
> [no when semicolons](https://rubystyle.guide/#no-when-semicolons)
> rules keep branches scannable. Use `then` for a single expression, or a
> full indented body for multiple statements. **Suggestion.**

```ruby
# bad
case payload
in { name: }; greet(name); log(name)
end

# good
case payload
in { name: }
  greet(name)
  log(name)
end

# good — one expression with then
case status
when :open then open!
when :closed then close!
end
```

## 16.12 Prefer `then` only for one-expression `when` / `in` branches; use a multiline body when the branch has multiple statements.

> Why? The guide's
> [one-line cases](https://rubystyle.guide/#one-line-cases)
> rule and `Style/WhenThen` / `Style/MultilineWhenThen` keep compact
> branches compact and reject `then` on multiline bodies. **Violation.**
>
> Enforced by: Style/MultilineWhenThen.

```ruby
# bad
case status
when :open then
  open!
  notify!
end

# good
case status
when :open
  open!
  notify!
when :closed then close!
end
```

## 16.13 Prefer an explicit `else` (or exhaustive patterns) over letting `NoMatchingPatternError` escape from application boundaries.

> Why? Unmatched `case ... in` raises. At process edges (jobs, request
> handlers), convert that into a domain error with context. Inside
> trusted internal code, exhaustive patterns without `else` are fine when
> the type system of inputs is closed. **Suggestion.**

```ruby
# bad — bare raise with no context at the boundary
case params
in { action: 'start' }
  start!
in { action: 'stop' }
  stop!
end

# good
case params
in { action: 'start' }
  start!
in { action: 'stop' }
  stop!
else
  raise ArgumentError, "unsupported params: #{params.inspect}"
end
```

## 16.14 Prefer pattern matching over manual `is_a?(Hash)` plus `fetch` chains for structural JSON-like data.

> Why? Once you are branching on shape, `in { type:, ** }` states the
> contract in the header instead of repeating digs in every branch.
> Keep `when` for `===` matches; keep `in` for structure. **Suggestion.**

```ruby
# bad
case payload
when Hash
  if payload[:type] == 'user'
    handle_user
  elsif payload[:type] == 'bot'
    handle_bot
  end
end

# good
case payload
in { type: 'user' }
  handle_user
in { type: 'bot' }
  handle_bot
end
```
## 16.15 Prefer keeping patterns shallow; extract nested matching into methods when nesting passes two levels.

> Why? Deeply nested array/hash patterns are powerful and unreadable.
> Match one layer, call a method that matches the next. This also keeps
> `NoMatchingPatternError` messages closer to the failing shape.
> **Suggestion.**

```ruby
# bad
case response
in { data: { user: { address: { city: } } } }
  mail_to_city(city)
end

# good
case response
in { data: { user: user } }
  handle_user(user)
end

def handle_user(user)
  case user
  in { address: { city: } }
    mail_to_city(city)
  end
end
```

## 16.16 Prefer ordinary conditionals when there is only one pattern and no bindings worth destructuring.

> Why? Pattern matching is not a prestige feature. `return unless user`
> remains clearer than `case user in User`. Use patterns when they
> remove digs, `is_a?` chains, or parallel assignments — not when they
> replace a nil check. **Suggestion.**

```ruby
# bad
case user
in Object
  save(user)
end

# good
save(user) if user

# good — pattern earns its keep
case user
in { id:, name: }
  index(id, name)
end
```
