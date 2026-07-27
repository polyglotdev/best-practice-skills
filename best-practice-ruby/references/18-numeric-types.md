<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 18. Numeric Types

Ruby collapses Fixnum/Bignum into `Integer`, keeps `Float` for binary
floating point, and offers `Rational`, `Complex`, and `BigDecimal` when
exactness matters. Style guidance lives under
[numbers](https://rubystyle.guide/#numbers),
[underscores-in-numerics](https://rubystyle.guide/#underscores-in-numerics),
[numeric-literal-prefixes](https://rubystyle.guide/#numeric-literal-prefixes),
[float-division](https://rubystyle.guide/#float-division),
[float-comparison](https://rubystyle.guide/#float-comparison),
[integer-type-checking](https://rubystyle.guide/#integer-type-checking),
[exponential-notation](https://rubystyle.guide/#exponential-notation), and
[random-numbers](https://rubystyle.guide/#random-numbers).

**Tool alignment:** enabled cops in this area include
`Style/NumericLiterals`, `Style/NumericLiteralPrefix`,
`Style/NumericPredicate`, `Style/FloatDivision`, `Style/ExponentialNotation`,
`Style/EvenOdd`, `Lint/FloatComparison`, `Lint/FloatOutOfRange`,
`Lint/BigDecimalNew`, `Lint/UnifiedInteger`, `Lint/NumberConversion`,
`Lint/RandOne`, `Style/RandomWithOffset`, and `Style/Sample`. Mark those
**Violation**; domain choices (money as Integer cents, Prefer Rational)
are **Suggestion**.

## 18.1 Use underscores to break up large numeric literals.

> Why? `1000000` is easy to miscount; `1_000_000` is not. The style guide's
> [underscores-in-numerics](https://rubystyle.guide/#underscores-in-numerics)
> rule is mechanical and RuboCop enforces a digit-group threshold.
> **Violation.**

> Enforced by: Style/NumericLiterals.

```ruby
# bad
threshold = 1000000
timeout_ms = 15000

# good
threshold = 1_000_000
timeout_ms = 15_000
```

## 18.2 Use `0o`, `0b`, and `0x` prefixes for octal, binary, and hex literals.

> Why? A leading `0` octal (`0123`) is a classic footgun.
> [numeric-literal-prefixes](https://rubystyle.guide/#numeric-literal-prefixes)
> requires explicit `0o` / `0b` / `0x`. **Violation.**

> Enforced by: Style/NumericLiteralPrefix.

```ruby
# bad
mode = 0755

# good
mode = 0o755
mask = 0b1111_0000
color = 0xff_00_aa
```

## 18.3 Prefer predicate forms (`odd?`, `even?`, `zero?`, `positive?`, `negative?`) over arithmetic comparisons.

> Why? `n.even?` reads as the question being asked;
> [numbers](https://rubystyle.guide/#numbers) and RuboCop's
> `Style/NumericPredicate` keep comparisons idiomatic. **Violation.**

> Enforced by: Style/NumericPredicate.

```ruby
# bad
do_something if x % 2 == 0
exit if count == 0

# good
do_something if x.even?
exit if count.zero?
```

## 18.4 Prefer `#even?` / `#odd?` over bit tricks for parity.

> Why? `x & 1 == 0` is clever and wrong-shaped for humans. `Style/EvenOdd`
> steers you to the predicate. **Violation.**

> Enforced by: Style/EvenOdd.

```ruby
# bad
flag = (n & 1).zero?

# good
flag = n.even?
```

## 18.5 Divide intentionally: use `.fdiv`, `fdiv`, or Rational when you need a non-integer result.

> Why? `1 / 2` is `0` in Ruby. The guide's
> [float-division](https://rubystyle.guide/#float-division) prefers making
> float (or rational) division explicit rather than hoping a literal is a
> float. **Violation** when RuboCop's configured style matches.

> Enforced by: Style/FloatDivision.

```ruby
# bad — integer division by accident
ratio = completed / total

# good — explicit float division
ratio = completed.fdiv(total)

# good — exact rational when you must not lose precision early
ratio = Rational(completed, total)
```

## 18.6 Never compare Floats with `==` for application logic.

> Why? Binary floating point is approximate.
> [float-comparison](https://rubystyle.guide/#float-comparison) and
> `Lint/FloatComparison` forbid direct equality. Compare with a tolerance,
> use integers (cents), `BigDecimal`, or `Rational` instead. **Violation.**

> Enforced by: Lint/FloatComparison.

```ruby
# bad
expect(score).to eq(0.1 + 0.2)

# good
expect(score).to be_within(0.000_1).of(0.3)

# good — money as integer cents
expect(total_cents).to eq(30)
```

## 18.7 Prefer `Integer` (and `Integer()`) over legacy `Fixnum` checks.

> Why? `Fixnum` and `Bignum` are gone as separate classes.
> [integer-type-checking](https://rubystyle.guide/#integer-type-checking)
> and `Lint/UnifiedInteger` reject the old names. **Violation.**

> Enforced by: Lint/UnifiedInteger.

```ruby
# bad
value.is_a?(Fixnum)

# good
value.is_a?(Integer)
Integer(value, exception: false)
```

## 18.8 Construct `BigDecimal` with `BigDecimal(...)`, not `BigDecimal.new`.

> Why? `BigDecimal.new` is deprecated; `Lint/BigDecimalNew` catches it.
> Prefer string or integer inputs over floats when building decimals.
> **Violation.**

> Enforced by: Lint/BigDecimalNew.

```ruby
# bad
require 'bigdecimal'
amount = BigDecimal.new('10.5')
amount = BigDecimal(0.1) # float contamination

# good
amount = BigDecimal('10.5')
amount = BigDecimal(10.5, 2) # only when the float source is unavoidable
```

## 18.9 Prefer scientific notation style that RuboCop's `Style/ExponentialNotation` expects.

> Why? Mixing `1.2E3` and `1.2e3` in one file is noise.
> [exponential-notation](https://rubystyle.guide/#exponential-notation)
> documents the community preference; keep the project consistent via
> RuboCop autocorrect. **Violation.**

> Enforced by: Style/ExponentialNotation.

```ruby
# bad — inconsistent exponent casing in one module
a = 1.2E3
b = 3.4e2

# good — one style project-wide (after rubocop -A)
a = 1.2e3
b = 3.4e2
```

## 18.10 Prefer `Integer` / `Float` conversion methods that match intent; avoid noisy `to_i` chains on unsure input.

> Why? `Lint/NumberConversion` flags some `to_i` / `to_f` / `to_d` patterns
> in favour of `Integer()`, `Float()`, or `BigDecimal()`. Use the conversion
> that documents failure behaviour (`exception: false` vs raise).
> **Violation** where the cop fires; choose the safer constructor.

> Enforced by: Lint/NumberConversion.

```ruby
# bad — silent zero on garbage
user_id = params[:id].to_i

# good — explicit conversion with failure policy
user_id = Integer(params[:id], exception: false)
raise ArgumentError, 'id required' unless user_id
```

## 18.11 Store money and other exact quantities as integer minor units or `BigDecimal`, not `Float`.

> Why? Float cannot represent most decimal fractions. Billing, tax, and FX
> code should use integer cents (or a money gem) or `BigDecimal` with a
> documented rounding mode. **Suggestion.**

```ruby
# bad
price = 19.99
total = price * quantity

# good
price_cents = 1_999
total_cents = price_cents * quantity

# good
require 'bigdecimal'
price = BigDecimal('19.99')
total = (price * quantity).round(2, BigDecimal::ROUND_HALF_EVEN)
```

## 18.12 Prefer `Random` / `SecureRandom` APIs over `rand` edge cases; do not call `rand(1)`.

> Why? `rand(1)` always returns `0`, which is almost never intended —
> `Lint/RandOne` catches it. Prefer ranges (`rand(1..6)`) and use
> `SecureRandom` for tokens. **Violation.**

> Enforced by: Lint/RandOne.

```ruby
# bad
n = rand(1)

# good
n = rand(1..6)
token = SecureRandom.hex(16)
```

## 18.13 Prefer `Random.rand` offset helpers that stay readable; use `Style/RandomWithOffset` guidance.

> Why? `rand(n) + m` is easy to get wrong on inclusive bounds. Prefer a
> range literal. **Violation.**

> Enforced by: Style/RandomWithOffset.

```ruby
# bad
roll = rand(6) + 1

# good
roll = rand(1..6)
```

## 18.14 Prefer `Enumerable#sample` over shuffle-and-take for random selection.

> Why? `[1, 2, 3].shuffle.first` allocates a full shuffle.
> [random-numbers](https://rubystyle.guide/#random-numbers) and
> `Style/Sample` prefer `#sample`. **Violation.**

> Enforced by: Style/Sample.

```ruby
# bad
winner = users.shuffle.first

# good
winner = users.sample
pair = users.sample(2)
```

## 18.15 Reject out-of-range float literals that become Infinity.

> Why? Extremely large float literals silently become `Infinity`.
> `Lint/FloatOutOfRange` catches them. Use `BigDecimal` or integers for
> huge magnitudes. **Violation.**

> Enforced by: Lint/FloatOutOfRange.

```ruby
# bad — may become Infinity depending on magnitude
x = 1.0e400

# good
require 'bigdecimal'
x = BigDecimal('1e400')
```

## 18.16 Prefer `Rational` for exact ratios; convert to Float only at display edges.

> Why? Aspect ratios, probabilities under combination, and fractional math
> stay exact as `Rational` until you format for humans. **Suggestion.**

```ruby
# bad
half = 1 / 2.0 # float already

# good
half = Rational(1, 2)
display = format('%.4f', half.to_f)
```
