<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 8. Blocks, Procs & Lambdas

Blocks are Ruby's primary iteration and lifetime hook. This chapter covers
brace vs `do`/`end`, single-line vs multiline, `Proc` vs lambda semantics,
stabby lambda syntax, symbol-to-proc, block arguments, and when not to force a
block into a temporary Proc. Normative anchors live in
[Blocks, Procs & Lambdas](https://rubystyle.guide/#blocks-procs-lambdas),
[single-line blocks](https://rubystyle.guide/#single-line-blocks),
[single-action blocks](https://rubystyle.guide/#single-action-blocks),
[block argument](https://rubystyle.guide/#block-argument),
[stabby lambda](https://rubystyle.guide/#stabby-lambda-with-args),
[proc](https://rubystyle.guide/#proc), and
[lambda multi-line](https://rubystyle.guide/#lambda-multi-line).

**Tool alignment:** `Style/BlockDelimiters`, `Style/Lambda`, `Style/Proc`,
`Style/SymbolProc`, `Style/ExplicitBlockArgument`,
`Performance/BlockGivenWithExplicitBlock`, `Lint/UnusedBlockArgument`,
`Naming/BlockParameterName`, and `Metrics/BlockLength`.

## 8.1 Use `{ }` for single-line blocks and `do`/`end` for multiline blocks.

> Why? The guide's
> [single-line blocks](https://rubystyle.guide/#single-line-blocks) rule and
> the shipped `Style/BlockDelimiters` (`line_count_based`) enforce this split.
> Braces bind tighter than `do`/`end`, which also matters when a block is
> passed beside other arguments — but the line-count rule alone removes most
> debates.
> **Violation.**
>
> Enforced by: Style/BlockDelimiters.

```ruby
# bad — multiline with braces, single-line with do/end
names.map { |name|
  name.upcase
}

names.map do |name| name.upcase end

# good
names.map { |name| name.upcase }

names.map do |name|
  name.upcase
end
```

## 8.2 Prefer symbol-to-proc when the block only sends one method with no arguments.

> Why? The guide's
> [single-action blocks](https://rubystyle.guide/#single-action-blocks) rule
> and `Style/SymbolProc` rewrite `map { |x| x.foo }` to `map(&:foo)`. The
> shorthand fails when you need arguments (`map { |x| x.foo(1) }`) or multiple
> statements — keep a block then.
> **Violation.**
>
> Enforced by: Style/SymbolProc.

```ruby
# bad
names.map { |name| name.upcase }
items.each { |item| item.persist! }

# good
names.map(&:upcase)
items.each(&:persist!)

# good — needs an argument, keep the block
names.map { |name| name.slice(0, 3) }
```

## 8.3 Prefer stabby lambda (`->`) over `lambda`; use `proc` / `Proc.new` only when Proc semantics are required.

> Why? The shipped `Style/Lambda` EnforcedStyle is `literal` (stabby). The
> guide's
> [stabby lambda with args](https://rubystyle.guide/#stabby-lambda-with-args),
> [stabby lambda no args](https://rubystyle.guide/#stabby-lambda-no-args), and
> [proc](https://rubystyle.guide/#proc) sections distinguish the forms.
> Lambdas check arity and use local `return`; procs do not check arity and
> `return` from the enclosing method — pick deliberately.
> **Violation.**
>
> Enforced by: Style/Lambda.

```ruby
# bad
greeter = lambda { |name| "hi #{name}" }
greeter = lambda { 'hi' }

# good
greeter = ->(name) { "hi #{name}" }
greeter = -> { 'hi' }

# good — Proc semantics intentional (arity soft, return escapes)
callback = proc { |event| handle(event) }
```

Also related: Style/Proc.

## 8.4 Use `do`/`end` for multiline stabby lambdas; keep the parameters on the `->` line.

> Why? The guide's
> [lambda multi-line](https://rubystyle.guide/#lambda-multi-line) rule rejects
> stuffing a multiline body into `{ }` for lambdas the same way §8.1 does for
> blocks. Put args in `->(a, b)` and open `do` on the same line.
> **Suggestion.**

```ruby
# bad
handler = ->(event) {
  audit(event)
  publish(event)
}

# good
handler = ->(event) do
  audit(event)
  publish(event)
end
```

## 8.5 Prefer yielding or an implicit block to creating a Proc when you only need to call the block once.

> Why? The guide's
> [block argument](https://rubystyle.guide/#block-argument) discussion and
> `Style/ExplicitBlockArgument` / `Performance/BlockGivenWithExplicitBlock`
> push you away from `&block` + `block.call` when `yield` suffices. Capturing
> `&block` allocates a Proc; `yield` does not.
> **Violation.**
>
> Enforced by: Style/ExplicitBlockArgument.

```ruby
# bad — unnecessary Proc allocation
def around(&block)
  setup
  block.call
  teardown
end

# good
def around
  setup
  yield
  teardown
end

# good — capture only when storing or passing on
def around(&block)
  hooks << block
end
```

Also enforced by: Performance/BlockGivenWithExplicitBlock.

## 8.6 Check `block_given?` before yielding when the block is optional.

> Why? Calling `yield` without a block raises `LocalJumpError`. If the block
> is optional, guard with `block_given?` or provide a default behaviour.
> Do not combine `block_given?` with an unused `&block` capture — that is what
> `Performance/BlockGivenWithExplicitBlock` flags.
> **Suggestion.**

```ruby
# bad
def each_item
  items.each { |item| yield item }
end

# good — required block documented by API
def each_item
  raise ArgumentError, 'block required' unless block_given?

  items.each { |item| yield item }
end

# good — optional block
def each_item
  return items.each unless block_given?

  items.each { |item| yield item }
end
```

## 8.7 Do not use `Object#tap` merely to get a local variable; prefer a named local or `then`/`yield_self` for transformation.

> Why? The guide's [avoid tap](https://rubystyle.guide/#avoid-tap) rule flags
> `tap` as a smell when it only introduces a name. `tap` is fine for
> side-effect debugging or configuring an object you then return. For
> pipelines that transform, prefer `then` (guide:
> [object yield self vs object then](https://rubystyle.guide/#object-yield-self-vs-object-then)).
> **Suggestion.**

```ruby
# bad — tap used only to name the value
user = User.create!(name: 'Ada').tap { |u| notify(u) }

# good — explicit steps
user = User.create!(name: 'Ada')
notify(user)

# good — transformation pipeline
json = payload
  .then { |data| JSON.parse(data) }
  .then { |hash| Order.new(hash) }
```

## 8.8 Prefer `map` / `select` / `reject` / `find` over `each` with manual accumulation.

> Why? Enumerable methods communicate intent and avoid off-by-one mutation
> bugs. `each` with `<<` into an outer array is almost always `map` or
> `filter_map`. Performance cops like `Performance/MapCompact` and
> `Style/MapCompactWithConditionalBlock` catch some of the common inefficient
> forms — see [Chapter 13](13-collections-and-enumerable.md).
> **Suggestion.**

```ruby
# bad
result = []
users.each do |user|
  result << user.name if user.active?
end

# good
result = users.select(&:active?).map(&:name)

# good — filter_map when available intent matches
result = users.filter_map { |user| user.name if user.active? }
```

## 8.9 Keep block length under the Metrics ceiling; extract methods when a block grows past ~30 lines.

> Why? Shipped `Metrics/BlockLength` Max is 30 (excluding specs/config). A long
> block is a method that has not been named yet. Especially avoid multiline
> blocks nested three deep — extract helpers or an object.
> **Violation.**
>
> Enforced by: Metrics/BlockLength.

```ruby
# bad — page-long block inside a controller action
users.each do |user|
  # 40 lines of billing logic
end

# good
users.each { |user| Billing::Reconcile.new(user).call }
```

## 8.10 Do not shadow outer locals with block parameters.

> Why? Restates [Chapter 3, §3.16](03-naming.md) at the block layer because
> this is where shadowing actually appears. `Lint/ShadowingOuterLocalVariable`
> fails the build; rename the block parameter.
> **Violation.**
>
> Enforced by: Lint/ShadowingOuterLocalVariable.

```ruby
# bad
def totals(order)
  order.lines.map { |order| order.amount }
end

# good
def totals(order)
  order.lines.map { |line| line.amount }
end
```

## 8.11 Prefix unused block arguments with `_`.

> Why? `Lint/UnusedBlockArgument` flags unused block args. Common in
> `Hash#each` when you only need keys or values — prefer `each_key` /
> `each_value` when that is the intent, or `_value` when the API forces both.
> **Violation.**
>
> Enforced by: Lint/UnusedBlockArgument.

```ruby
# bad
users.each_with_index { |user, index| store(user) }

# good
users.each_with_index { |user, _index| store(user) }

# good — better API choice
users.each { |user| store(user) }
```

## 8.12 Prefer `{ }` when a single-line block is chained or used as a value; beware `do`/`end` precedence.

> Why? `do`/`end` binds more loosely than braces. `foo bar do ... end` passes
> the block to `foo`, not `bar`. When chaining, braces (or parentheses around
> the call) prevent mis-association. RuboCop's `Lint/AmbiguousBlockAssociation`
> catches many of these.
> **Violation.**
>
> Enforced by: Lint/AmbiguousBlockAssociation.

```ruby
# bad — block may bind to the wrong method
expect(order.total).to eq 10 do
  # ...
end

# good — parentheses / braces make association clear
expect(order.total).to(eq(10))
result = items.map { |i| i.price }.sum
```

## 8.13 Call procs with `call` / `.()`; do not use `proc[...]` as the primary invocation style in application code.

> Why? The guide's [proc call](https://rubystyle.guide/#proc-call) section
> documents the options. `call` is the most readable; `.()` is acceptable in
> dense functional code. `[]` looks like Hash access and confuses readers.
> `Style/LambdaCall` can enforce a consistent call style when configured.
> **Suggestion.**

```ruby
# bad — looks like hash access
callback[event]

# good
callback.call(event)
callback.(event)
```

## 8.14 Do not convert a block to a Proc just to pass it to a method that accepts a block.

> Why? `method(&:to_proc)` chains and `Proc.new { }` wrappers around an
> existing block are usually needless. Pass the block implicitly, or use
> `&callable` when you already have a callable object (`method(:foo)`, a
> lambda, an object implementing `to_proc`).
> **Suggestion.**

```ruby
# bad
def process(items, &block)
  items.each { |item| block.call(item) }
end

process(items, &proc { |i| i.touch! })

# good
def process(items)
  items.each { |item| yield item }
end

process(items, &:touch!)
```

## 8.15 Prefer `map` + compact forms RuboCop knows about over inventing your own.

> Why? Shipped cops such as `Style/MapCompactWithConditionalBlock`,
> `Performance/MapCompact`, and `Style/MapToHash` encode idioms that are both
> clearer and faster. Use them instead of `map { ... }.compact` or
> `map { |x| [x.key, x.value] }.to_h` when the rewrite matches.
> **Violation.**
>
> Enforced by: Style/MapCompactWithConditionalBlock.

```ruby
# bad
names = users.map { |user| user.name if user.active? }.compact

# good
names = users.filter_map { |user| user.name if user.active? }
```

Also related: Performance/MapCompact and Style/MapToHash.

## 8.16 Avoid nesting blocks so deep that readers lose the subject; extract named methods or POROs.

> Why? Nested `map` / `each` / `do` pyramids are the block form of high
> cyclomatic complexity. Three levels is usually the practical maximum before
> a private method or a small object improves the file. Metrics on the outer
> method often fire first (§6.11); treat that as the cue.
> **Suggestion.**

```ruby
# bad
orders.each do |order|
  order.lines.each do |line|
    line.taxes.each do |tax|
      audit(order, line, tax)
    end
  end
end

# good
orders.each { |order| audit_order(order) }

def audit_order(order)
  order.lines.each { |line| audit_line(order, line) }
end
```

## 8.17 Use numbered block parameters sparingly; prefer named parameters once the block has more than one expression.

> Why? Numbered parameters (`_1`, `_2`) are concise for one-liners and hostile
> in multiline bodies where `_1` loses meaning. RuboCop naming cops may not
> force this; treat named params as the default for anything that needs a
> comment or a second line.
> **Suggestion.**

```ruby
# bad — numbered params across multiple lines
users.each do
  send_mail(_1.email)
  audit(_1.id)
end

# good — numbered ok for a tiny one-liner
users.each { put_s(_1.name) }

# good — named for multiline
users.each do |user|
  send_mail(user.email)
  audit(user.id)
end
```
