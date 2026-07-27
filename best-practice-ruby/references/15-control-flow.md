<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 15. Control Flow

Ruby offers `if` / `unless`, modifiers, ternaries, `case` / `when`, safe
navigation, and loop forms that can either clarify intent or bury it.
This chapter covers preferring modifiers for simple guards, `unless` for
negatives, `case` over long `if/elsif` chains, avoiding nested ternaries
and double negation, and keeping conditions free of assignment surprises.
Pattern matching (`case ... in`) is [Chapter 16](16-pattern-matching.md);
exceptions as flow are banned in [Chapter 11](11-exceptions-and-errors.md).

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[flow of control](https://rubystyle.guide/#flow-of-control),
[case vs if else](https://rubystyle.guide/#case-vs-if-else),
[unless for negatives](https://rubystyle.guide/#unless-for-negatives),
[until for negatives](https://rubystyle.guide/#until-for-negatives),
[ternary operator](https://rubystyle.guide/#ternary-operator),
[and or flow](https://rubystyle.guide/#and-or-flow),
[no and or or](https://rubystyle.guide/#no-and-or-or),
[safe navigation](https://rubystyle.guide/#safe-navigation),
[no nested conditionals](https://rubystyle.guide/#no-nested-conditionals),
[use if case returns](https://rubystyle.guide/#use-if-case-returns),
[no bang bang](https://rubystyle.guide/#no-bang-bang),
[no then](https://rubystyle.guide/#no-then),
[no else with unless](https://rubystyle.guide/#no-else-with-unless),
[if as a modifier](https://rubystyle.guide/#if-as-a-modifier),
[while as a modifier](https://rubystyle.guide/#while-as-a-modifier),
[infinite loop](https://rubystyle.guide/#infinite-loop),
[no flip flops](https://rubystyle.guide/#no-flip-flops),
[no nested ternary](https://rubystyle.guide/#no-nested-ternary),
[no non nil checks](https://rubystyle.guide/#no-non-nil-checks),
[safe assignment in condition](https://rubystyle.guide/#safe-assignment-in-condition),
and [no parens around condition](https://rubystyle.guide/#no-parens-around-condition).

**Tool alignment:** `Style/AndOr`, `Style/NegatedIf`, `Style/NegatedUnless`,
`Style/IfUnlessModifier`, `Style/GuardClause`, `Style/TernaryParentheses`,
`Style/NestedTernaryOperator`, `Style/MultilineTernaryOperator`,
`Style/SafeNavigation`, `Style/DoubleNegation`, `Style/NonNilCheck`,
`Style/ParenthesesAroundCondition`, `Style/For`, `Style/InfiniteLoop`,
`Style/YodaCondition`, `Style/SoleNestedConditional`, `Style/IfInsideElse`,
`Style/EmptyElse`, `Style/CaseLikeIf`, `Lint/AssignmentInCondition`,
`Lint/FlipFlop`, and related cops are effectively enabled. Rules those
cops catch are **Violation**; the rest are **Suggestion**.

## 15.1 Prefer `&&` / `||` over `and` / `or` for boolean expressions; reserve `and` / `or` only for control-flow sugar if the project allows it at all.

> Why? The guide's
> [no and or or](https://rubystyle.guide/#no-and-or-or)
> /
> [and or flow](https://rubystyle.guide/#and-or-flow)
> rules and `Style/AndOr` reject `and`/`or` in boolean expressions because
> their precedence is lower than assignment and surprises readers.
> Prefer `&&` / `||` everywhere in application code. **Violation.**
>
> Enforced by: Style/AndOr.

```ruby
# bad
ready = signed_in and admin?

# good
ready = signed_in && admin?
active = signed_in || guest?
```

## 15.2 Prefer `unless` for simple negative conditions; prefer `if !` / `if not` when the condition contains `&&` / `||` or is hard to parse.

> Why? The guide's
> [unless for negatives](https://rubystyle.guide/#unless-for-negatives)
> rule reads well for single predicates (`unless valid?`). Compound
> `unless a || b` is a cognitive trap — rewrite as `if`.
> `Style/NegatedIf` / `Style/NegatedUnless` keep negation style consistent.
> **Suggestion** for the compound case; negated-if form is a **Violation**
> when cops apply.
>
> Enforced by: Style/NegatedIf.

```ruby
# bad — unless with compound logic
unless user.active? || user.guest?
  reject!
end

# good
if !user.active? && !user.guest?
  reject!
end

# good — simple unless
unless user.active?
  reject!
end
```

## 15.3 Prefer modifier `if` / `unless` for simple one-line guards; expand to a block body when the expression is multiline or heavy.

> Why? The guide's
> [if as a modifier](https://rubystyle.guide/#if-as-a-modifier)
> rule and `Style/IfUnlessModifier` keep short guards dense without
> nesting. `Style/MultilineIfModifier` rejects multiline modifier forms.
> **Violation.**
>
> Enforced by: Style/IfUnlessModifier.

```ruby
# bad
if valid?
  save!
end

# good
save! if valid?

# good — too heavy for a modifier
if valid? && quota_available?(user) && !dry_run?
  save!
  notify!
end
```

## 15.4 Prefer guard clauses / early returns over deeply nested `if` bodies.

> Why? The guide's
> [no nested conditionals](https://rubystyle.guide/#no-nested-conditionals)
> spirit and `Style/GuardClause` flatten methods that start with
> precondition checks. Happy path stays left-aligned. **Violation.**
>
> Enforced by: Style/GuardClause.

```ruby
# bad
def publish
  if valid?
    if admin?
      persist!
    end
  end
end

# good
def publish
  return unless valid?
  return unless admin?

  persist!
end
```

## 15.5 Prefer `case` / `when` over long `if` / `elsif` / `else` chains comparing one value.

> Why? The guide's
> [case vs if else](https://rubystyle.guide/#case-vs-if-else)
> rule and `Style/CaseLikeIf` make multi-branch equality clearer as
> `case`. Keep `if` for unrelated predicates. Pattern-matching `in`
> branches are chapter 16. **Violation.**
>
> Enforced by: Style/CaseLikeIf.

```ruby
# bad
if status == :open
  open!
elsif status == :closed
  close!
elsif status == :archived
  archive!
end

# good
case status
when :open then open!
when :closed then close!
when :archived then archive!
end
```

## 15.6 Prefer returning values from `if` / `case` expressions over assigning inside each branch.

> Why? The guide's
> [use if case returns](https://rubystyle.guide/#use-if-case-returns)
> rule and `Style/ConditionalAssignment` keep a single assignment.
> **Suggestion** when the cop's style matches; treat as house style even
> when autocorrect is quiet.

```ruby
# bad
if admin?
  role = :admin
else
  role = :user
end

# good
role = if admin?
         :admin
       else
         :user
       end

role = admin? ? :admin : :user
```

## 15.7 Prefer a ternary only for simple, single-expression branches; never nest ternaries or span them across lines.

> Why? The guide's
> [ternary operator](https://rubystyle.guide/#ternary-operator),
> [no nested ternary](https://rubystyle.guide/#no-nested-ternary),
> and related rules, with `Style/NestedTernaryOperator` and
> `Style/MultilineTernaryOperator`, keep `? :` readable. Expand to `if`
> when either branch needs a statement. **Violation.**
>
> Enforced by: Style/NestedTernaryOperator.

```ruby
# bad
label = admin? ? (active? ? 'A' : 'B') : 'C'

# good
label = if admin?
          active? ? 'A' : 'B'
        else
          'C'
        end
```

## 15.8 Prefer `&.` safe navigation over `obj && obj.method` chains for nil-tolerant calls.

> Why? The guide's
> [safe navigation](https://rubystyle.guide/#safe-navigation)
> rule and `Style/SafeNavigation` shorten nil checks. Do not use `&.`
> to hide bugs when `obj` must be present — fail loudly instead.
> **Violation.**
>
> Enforced by: Style/SafeNavigation.

```ruby
# bad
name = user && user.profile && user.profile.name

# good
name = user&.profile&.name
```

## 15.9 Prefer explicit predicates over `!!` double negation when you need a boolean.

> Why? The guide's
> [no bang bang](https://rubystyle.guide/#no-bang-bang)
> rule and `Style/DoubleNegation` reject `!!value` as cryptic. Use
> `!value.nil?`, a predicate method, or `ActiveModel` / custom
> `#present?` style APIs. **Violation.**
>
> Enforced by: Style/DoubleNegation.

```ruby
# bad
ready = !!config[:flag]

# good
ready = config[:flag] == true
ready = !config[:flag].nil?
```

## 15.10 Prefer `obj.nil?` over `obj == nil`; prefer positive predicates over `!obj.nil?` when a domain predicate exists.

> Why? The guide's
> [no non nil checks](https://rubystyle.guide/#no-non-nil-checks)
> rule and `Style/NonNilCheck` / `Style/NilComparison` keep nil tests
> idiomatic. Prefer `if obj` only when every falsy value (`nil` and
> `false`) should share a branch. **Violation.**
>
> Enforced by: Style/NonNilCheck.

```ruby
# bad
process if !user.nil?

# good
process unless user.nil?
process if user
```

## 15.11 Do not use `unless` with `else`; rewrite as `if`.

> Why? The guide's
> [no else with unless](https://rubystyle.guide/#no-else-with-unless)
> rule and `Style/UnlessElse` remove the double negative of reading
> `unless` / `else`. **Violation.**
>
> Enforced by: Style/UnlessElse.

```ruby
# bad
unless valid?
  reject
else
  accept
end

# good
if valid?
  accept
else
  reject
end
```

## 15.12 Do not use `then` on multiline `if` / `unless` / `case` branches.

> Why? The guide's
> [no then](https://rubystyle.guide/#no-then)
> rule and `Style/MultilineIfThen` / `Style/WhenThen` keep `then` for
> compact one-line `when` / `if` forms only. **Violation.**
>
> Enforced by: Style/MultilineIfThen.

```ruby
# bad
if valid? then
  save!
end

# good
if valid?
  save!
end

# good — one-line when
case status
when :open then open!
when :closed then close!
end
```

## 15.13 Prefer `loop do` for intentional infinite loops; prefer `while` / `until` when the condition is natural.

> Why? The guide's
> [infinite loop](https://rubystyle.guide/#infinite-loop)
> rule and `Style/InfiniteLoop` prefer `loop do` over `while true`.
> Use `until` for negative loop conditions
> ([until for negatives](https://rubystyle.guide/#until-for-negatives)).
> **Violation.**
>
> Enforced by: Style/InfiniteLoop.

```ruby
# bad
while true
  break if done?
  work
end

# good
loop do
  break if done?

  work
end

sleep(0.1) until ready?
```

## 15.14 Do not use flip-flop (`..` / `...` as a conditional).

> Why? The guide's
> [no flip flops](https://rubystyle.guide/#no-flip-flops)
> rule and `Lint/FlipFlop` ban a rarely understood feature that hides
> state inside the condition. Use an explicit boolean flag. **Violation.**
>
> Enforced by: Lint/FlipFlop.

```ruby
# bad
lines.each do |line|
  puts line if (line =~ /BEGIN/)..(line =~ /END/)
end

# good
printing = false
lines.each do |line|
  printing = true if line.match?(/BEGIN/)
  puts line if printing
  printing = false if line.match?(/END/)
end
```

## 15.15 Wrap assignments used as conditions in parentheses (or avoid assignment-in-condition entirely).

> Why? The guide's
> [safe assignment in condition](https://rubystyle.guide/#safe-assignment-in-condition)
> rule and `Lint/AssignmentInCondition` require parentheses so readers
> see intent rather than a typo'd `==`. Prefer assigning on the previous
> line. **Violation.**
>
> Enforced by: Lint/AssignmentInCondition.

```ruby
# bad
if user = find_user(id)
  notify(user)
end

# good
if (user = find_user(id))
  notify(user)
end

# better
user = find_user(id)
notify(user) if user
```

## 15.16 Prefer no parentheses around simple conditions; use them when nesting operators needs grouping.

> Why? The guide's
> [no parens around condition](https://rubystyle.guide/#no-parens-around-condition)
> rule and `Style/ParenthesesAroundCondition` remove `if (ready?)` noise.
> Keep parens for `(a || b) && c` grouping. **Violation.**
>
> Enforced by: Style/ParenthesesAroundCondition.

```ruby
# bad
if (ready?)
  run!
end

# good
if ready?
  run!
end

if (retryable || force) && online?
  run!
end
```

## 15.17 Prefer normal-order conditions (`value == 0`) over Yoda conditions (`0 == value`).

> Why? `Style/YodaCondition` rejects constant-first comparisons carried
> over from languages where `=` typos assign inside conditions. Ruby's
> `Lint/AssignmentInCondition` already covers that hazard. **Violation.**
>
> Enforced by: Style/YodaCondition.

```ruby
# bad
if 0 == count
  warn('empty')
end

# good
if count == 0
  warn('empty')
end

if count.zero?
  warn('empty')
end
```
