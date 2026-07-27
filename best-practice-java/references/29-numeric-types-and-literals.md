<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 29. Numeric Types & Literals

Java's numeric types are a set of trade-offs the language made in 1995 and
has never been able to revisit. `int` wraps silently on overflow. `double`
cannot represent 0.1. Boxed primitives have identity, so `==` on them means
something different from `==` on their unboxed forms, and unboxing a `null`
throws a `NullPointerException` from a line with no visible dereference.
None of this is a defect in the language so much as a set of sharp edges
that every Java programmer is expected to have memorised — and this chapter
is that list.

The through-line is that the *type* has to match the arithmetic you
actually want. Money is exact decimal arithmetic and therefore is not a
`double`. A running total that might exceed two billion is not an `int`. A
value that participates in equality is not a boxed primitive compared with
`==`. Get the type right at declaration and most of the remaining rules
never come up.

This chapter is built on **Effective Java, 3rd ed.**, Items 60 ("Avoid
`float` and `double` if exact answers are required") and 61 ("Prefer
primitive types to boxed primitives"), together with the JDK 21 API
contracts for
[`BigDecimal`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html),
[`Math`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Math.html),
and
[`RandomGenerator`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/random/RandomGenerator.html),
and the
[Google Java Style Guide §4.8.8 Numeric Literals](https://google.github.io/styleguide/javaguide.html#s4.8.8-numeric-literals).
Nullability of boxed types in general is
[Chapter 25](25-nullability.md); `equals`/`hashCode` contracts are
[Chapter 10](10-equals-hashcode-tostring.md).

**Tool alignment:** Error Prone's `BigDecimalLiteralDouble`,
`BigDecimalEquals`, `BoxedPrimitiveEquality`, `ReferenceEquality`,
`IntLongMath`, `NarrowingCompoundAssignment`,
`FloatingPointLiteralPrecision`, and `BadShiftAmount` cover a large share of
this chapter mechanically, and Checkstyle's `UpperEll`, `HexLiteralCase`,
and `MagicNumber` cover the literal rules. Rules those checks catch are
marked **Violation**; the rest are **Suggestions**.

## 29.1 Never use `float` or `double` where an exact answer is required.

> Why? Effective Java, 3rd ed., Item 60: `float` and `double` "are designed
> primarily for scientific and engineering calculations" and "do not
> provide exact results" — they are binary floating-point, so no
> finite-length representation of 0.1 exists at all. `1.03 - 0.42` prints
> `0.6100000000000001`, and Bloch's worked example of buying candies priced
> in tenths of a dollar out of a `double funds = 1.00` reports three items
> bought and `$0.3999999999999999` in change, where the correct answer is
> four items and no change. This is not a rounding-display problem you can
> paper over at the edge; the error compounds through every subsequent
> operation. **Suggestion.**

```java
// bad — reports 3 items and $0.3999999999999999 change
double funds = 1.00;
int itemsBought = 0;
for (double price = 0.10; funds >= price; price += 0.10) {
  funds -= price;
  itemsBought++;
}

// good — exact decimal arithmetic; reports 4 items and no change
BigDecimal funds = new BigDecimal("1.00");
int itemsBought = 0;
for (BigDecimal price = new BigDecimal("0.10");
    funds.compareTo(price) >= 0;
    price = price.add(new BigDecimal("0.10"))) {
  funds = funds.subtract(price);
  itemsBought++;
}
```

## 29.2 For money, use `int` or `long` counted in the smallest unit when the range allows it, and `BigDecimal` otherwise.

> Why? Effective Java, 3rd ed., Item 60 gives both alternatives and is
> explicit that `BigDecimal` has costs: it is "a lot less convenient than
> using a primitive arithmetic type and it's slower." Counting in cents (or
> the currency's minor unit) keeps the arithmetic exact *and* primitive. An
> `int` holds roughly ±21 million dollars in cents and a `long` holds more
> money than exists, so the range is rarely the limit. Reach for
> `BigDecimal` when you need fractional minor units (interest, FX, unit
> pricing) or when the scale is part of the contract. **Suggestion.**

```java
// bad — a double that will drift, and an ambiguous "amount"
public record LineItem(String sku, double price) {}

// good — exact and primitive; the unit is in the type name
public record LineItem(String sku, long priceInCents) {}

// good — exact with a scale, where fractional minor units are real
public record ExchangeRate(Currency from, Currency to, BigDecimal rate) {}
```

## 29.3 Construct a `BigDecimal` from a `String` or `BigDecimal.valueOf`, never from a `double` literal.

> Why? `new BigDecimal(0.1)` does not mean "one tenth". The constructor is
> documented as producing the *exact* binary value of the `double`, so it
> yields
> `0.1000000000000000055511151231257827021181583404541015625` — the
> imprecision is captured permanently instead of being avoided. The
> `String` constructor gives exactly the digits you wrote, and
> `BigDecimal.valueOf(double)` routes through `Double.toString`, which
> gives the shortest representation that round-trips. Use the `String` form
> for literals in source; use `valueOf` when a `double` arrives from
> outside and you have no better source.
> **Violation — enforced by Error Prone `BigDecimalLiteralDouble`.**

```java
// bad — captures the binary imprecision exactly
BigDecimal tenth = new BigDecimal(0.1);
BigDecimal price = new BigDecimal(19.99);

// good
BigDecimal tenth = new BigDecimal("0.1");
BigDecimal price = new BigDecimal("19.99");

// good — when the double came from outside and there is no string form
BigDecimal fromLegacy = BigDecimal.valueOf(legacyReading);
```

## 29.4 Always pass a scale and a `RoundingMode` to `BigDecimal.divide`.

> Why? The single-argument `divide` throws `ArithmeticException` when the
> exact quotient has a non-terminating decimal expansion — `1 / 3` is the
> first case anyone hits, and it fails in production rather than in the
> test that only divided by 2. Supplying a scale and a `RoundingMode` makes
> the result total. Choose the mode deliberately: `HALF_EVEN` (banker's
> rounding) is the IEEE 754 default and is unbiased over many operations,
> which is why financial systems prefer it; `HALF_UP` matches what most
> humans and most regulations call "round half away from zero". Never
> accept the deprecated `int`-valued rounding constants.
> **Suggestion.**

```java
// bad — throws ArithmeticException: Non-terminating decimal expansion
BigDecimal share = total.divide(new BigDecimal("3"));

// good — scale and rounding are part of the contract
BigDecimal share = total.divide(new BigDecimal("3"), 2, RoundingMode.HALF_EVEN);

// also good — a MathContext when precision, not scale, is what is fixed
BigDecimal share = total.divide(new BigDecimal("3"), MathContext.DECIMAL128);
```

## 29.5 Compare `BigDecimal` values with `compareTo`, never with `equals`.

> Why? `BigDecimal.equals` compares scale as well as value, so
> `new BigDecimal("2.0").equals(new BigDecimal("2.00"))` is `false` — the
> two objects represent the same number with different scales. This makes
> `BigDecimal` treacherous in any equality-based structure: a `HashSet` can
> hold both `2.0` and `2.00`, and a `Map` lookup with a differently scaled
> key silently misses. `compareTo` compares numeric value only and returns
> `0` for both. If you need `BigDecimal` in a hash-based collection,
> normalise the scale on the way in with `setScale` or
> `stripTrailingZeros`. **Violation — enforced by Error Prone
> `BigDecimalEquals`.**

```java
// bad — false, and a Set can end up holding both
boolean same = new BigDecimal("2.0").equals(new BigDecimal("2.00"));

// good
boolean same = new BigDecimal("2.0").compareTo(new BigDecimal("2.00")) == 0;

// good — AssertJ has the comparison built in
assertThat(actual).isEqualByComparingTo(new BigDecimal("2.00"));
```

## 29.6 Pin the scale explicitly before persisting, displaying, or comparing a `BigDecimal`.

> Why? Scale survives arithmetic in ways that surprise: `add` takes the
> maximum scale of its operands, `multiply` takes the *sum* of them, so a
> chain of multiplications produces a value with a scale nobody chose. A
> monetary column defined as `NUMERIC(19,2)` will then round on insert
> according to the database's rules rather than yours, and the value read
> back is not `equals` to the one written. Call `setScale(n, mode)` at the
> boundary so the rounding decision lives in your code, once, visibly.
> **Suggestion.**

```java
// bad — scale is whatever the arithmetic produced; the database rounds
BigDecimal total = unitPrice.multiply(quantity).multiply(taxRate);
repository.save(new Invoice(id, total));

// good
BigDecimal total =
    unitPrice.multiply(quantity).multiply(taxRate).setScale(2, RoundingMode.HALF_EVEN);
repository.save(new Invoice(id, total));
```

## 29.7 Prefer primitive types to boxed primitives.

> Why? Effective Java, 3rd ed., Item 61 lists three differences that all
> bite: boxed primitives have identity distinct from their value, they have
> one non-functional value (`null`) that primitives do not, and they are
> slower and more space-consuming. Use a boxed type only where the language
> forces it — as a type parameter (`List<Integer>`, `Map<K, Long>`), in
> reflective contexts, or where `null` is a genuine, documented part of the
> domain. Everywhere else, declare the primitive.
> **Suggestion.**

```java
// bad — three boxed fields that can each be null and each allocate
public final class Reading {
  private Double value;
  private Integer sequence;
  private Boolean valid;
}

// good
public record Reading(double value, int sequence, boolean valid) {}
```

## 29.8 Never apply `==` or `!=` to boxed primitives.

> Why? On boxed operands, `==` compares references, so the answer depends
> on whether the JVM's autobox cache happened to hand back the same object.
> JLS §5.1.7 requires caching only for `int` values in `-128..127`, so
> `Integer.valueOf(100) == Integer.valueOf(100)` is `true` and
> `Integer.valueOf(1000) == Integer.valueOf(1000)` is `false`. Code that
> passes every test with small inputs fails in production with large ones.
> Effective Java, Item 61 uses exactly this to break a comparator. Compare
> with `equals`, or unbox one side explicitly, or use
> `Integer.compare`/`Long.compare`.
> **Violation — enforced by Error Prone `BoxedPrimitiveEquality` and
> `ReferenceEquality`.**

```java
// bad — returns 1 for two equal Integers outside the cache range
Comparator<Integer> naturalOrder = (i, j) -> (i < j) ? -1 : (i == j ? 0 : 1);

// good — the library comparator, or an explicit unboxing
Comparator<Integer> naturalOrder = Integer::compare;

Comparator<Integer> alsoFine =
    (i, j) -> {
      int first = i;
      int second = j;
      return (first < second) ? -1 : ((first == second) ? 0 : 1);
    };
```

## 29.9 Never let a boxed primitive be auto-unboxed where it can be `null`.

> Why? Unboxing compiles to an `intValue()` or `booleanValue()` call, so a `null` produces a
> `NullPointerException` on a line that contains no visible dereference —
> `if (flags.get(key))` throws when the key is absent, and the stack trace
> points at an `if`. Mixed-type operations are the worst case: in
> `boxedInt == primitiveInt` the boxed operand is unboxed to make the
> comparison numeric, so a rule you followed in §29.8 turns into an NPE
> here. Guard the `null` before the arithmetic, or use the primitive-valued
> accessors that take a default.
> **Suggestion.**

```java
// bad — NPE if "beta" is absent, from a line that dereferences nothing
Map<String, Boolean> flags = loadFlags();
if (flags.get("beta")) {
  enableBeta();
}

// bad — the boxed operand is unboxed to compare; NPE when count is null
Integer count = counts.get(key);
if (count == 0) {}

// good
if (Boolean.TRUE.equals(flags.get("beta"))) {
  enableBeta();
}

// good — the default is explicit
int count = counts.getOrDefault(key, 0);
if (count == 0) {}
```

## 29.10 Never accumulate into a boxed local variable.

> Why? Effective Java, 3rd ed., Item 61 shows a loop declared as
> `Long sum = 0L` that runs correctly and is dramatically slower than the
> same loop with a `long`, because every `sum += i` unboxes, adds, and
> boxes a fresh `Long` — roughly 2^31 needless allocations in Bloch's
> example. Nothing about the code looks wrong, which is the point: a single
> misplaced capital letter turns a register operation into an allocation.
> Check every accumulator, counter, and index declaration.
> **Suggestion.**

```java
// bad — one capital letter; 2^31 boxed allocations
Long sum = 0L;
for (long i = 0; i < Integer.MAX_VALUE; i++) {
  sum += i;
}

// good
long sum = 0L;
for (long i = 0; i < Integer.MAX_VALUE; i++) {
  sum += i;
}
```

## 29.11 Detect integer overflow with the `Math.*Exact` methods instead of letting it wrap.

> Why? Java's integer arithmetic wraps silently on overflow, so
> `Integer.MAX_VALUE + 1` is `Integer.MIN_VALUE` and no exception is
> raised. A quantity, a byte count, or a running total that overflows
> becomes negative and flows onward as a plausible-looking value, which
> means the failure surfaces somewhere far from its cause. `Math.addExact`,
> `subtractExact`, `multiplyExact`, `negateExact`, `incrementExact`, and
> `toIntExact` throw `ArithmeticException` at the point of overflow.
> Related: `Math.abs(Integer.MIN_VALUE)` returns `Integer.MIN_VALUE` — a
> negative absolute value — where `Math.absExact` throws.
> **Suggestion.**

```java
// bad — silently wraps to a negative total
int total = 0;
for (int size : sizes) {
  total += size;
}

// bad — returns Integer.MIN_VALUE, which is negative
int magnitude = Math.abs(offset);

// good — fails loudly at the point of overflow
int total = 0;
for (int size : sizes) {
  total = Math.addExact(total, size);
}

int magnitude = Math.absExact(offset);
```

## 29.12 Widen before you multiply when the result is a `long`.

> Why? The expression is evaluated in the type of its operands, not in the
> type of the variable it is assigned to. `long millis = seconds * 1000;`
> with an `int seconds` computes in `int`, so it wraps once `seconds` passes
> about 2.1 million (roughly 25 days), *then* widens the already-wrong value
> to `long`.
> The declared `long` gives a false sense that the range was considered.
> Cast one operand, or write the literal as a `long`.
> **Violation — enforced by Error Prone `IntLongMath`.**

```java
// bad — overflows in int before the widening conversion
int seconds = readSeconds();
long millis = seconds * 1000;

// good — a long literal forces the multiplication into long
long millis = seconds * 1000L;

// good — or be explicit and overflow-checked
long millis = Math.multiplyExact((long) seconds, 1000L);
```

## 29.13 Use `Math.floorDiv` and `Math.floorMod` when an operand can be negative.

> Why? Java's `/` truncates toward zero and `%` takes the sign of the
> dividend, so `-7 / 2` is `-3` (not `-4`) and `-7 % 3` is `-1` (not `2`).
> That breaks every use of `%` as a bucket or wrap-around index: a hash
> that happens to be negative produces a negative array index and an
> `ArrayIndexOutOfBoundsException` for a fraction of inputs.
> `Math.floorDiv` rounds toward negative infinity and `Math.floorMod`
> returns a result with the sign of the *divisor*, which is the behaviour
> the modular-arithmetic reading assumes. **Suggestion.**

```java
// bad — negative hash yields a negative index
int bucket = key.hashCode() % buckets.length;

// bad — -7 / 2 is -3, so the "page" is off by one for negative offsets
int page = offset / pageSize;

// good
int bucket = Math.floorMod(key.hashCode(), buckets.length);
int page = Math.floorDiv(offset, pageSize);
```

## 29.14 Never narrow with a compound assignment operator.

> Why? Compound assignment operators contain an invisible cast. `int x;
> x *= 1.5;` compiles, computes in `double`, and silently truncates back to
> `int` — the same code written out as `x = x * 1.5;` is a compile error.
> The same applies to `byte b; b += 300;` and `int i; i += someLong;`. The
> shorthand hides exactly the narrowing conversion the language would
> otherwise force you to acknowledge with an explicit cast.
> **Violation — enforced by Error Prone `NarrowingCompoundAssignment`.**

```java
// bad — compiles, truncates; the expanded form would not compile
int total = 7;
total *= 1.5; // 10, not 10.5 — the fraction is gone without a word

// good — make the type of the arithmetic match the type of the result
double total = 7;
total *= 1.5; // 10.5

// good — or acknowledge the narrowing where it belongs
int total = 7;
total = (int) Math.round(total * 1.5); // 11
```

## 29.15 Write `long` literals with an uppercase `L`.

> Why?
> [Google Java Style Guide §4.8.8](https://google.github.io/styleguide/javaguide.html#s4.8.8-numeric-literals)
> is unambiguous: "`long`-valued integer literals use an uppercase `L`
> suffix, never lowercase (to avoid confusion with the digit `1`). For
> example, `3000000000L` rather than `3000000000l`." In most fonts a
> lowercase `l` next to a digit is indistinguishable from a `1`, so
> `10l` reads as `101`. **Violation — enforced by Checkstyle `UpperEll`.**

```java
// bad — reads as 101 in most fonts
long timeoutNanos = 10l;

// good
long timeoutNanos = 10L;
```

## 29.16 Use underscores to group digits in long numeric literals.

> Why? A ten-digit constant is unreadable and unverifiable at a glance —
> nobody counts the zeros in `1000000000`, they assume. Underscores
> (Java 7+) are erased by the compiler and let the literal carry its own
> grouping, so a wrong magnitude becomes visible. Group decimal values in
> threes, hex in bytes or words, and binary in nibbles or bytes so the
> grouping matches the domain's natural unit.
> **Suggestion.**

```java
// bad — is that a billion or a hundred million?
long nanosPerSecond = 1000000000;
int mask = 0xFF00FF00;
long cardNumber = 1234567890123456L;

// good
long nanosPerSecond = 1_000_000_000;
int mask = 0xFF00_FF00;
long cardNumber = 1234_5678_9012_3456L;
```

## 29.17 Use binary or hex literals when the domain is bitwise, and write the hex digits in uppercase.

> Why? A bit mask written in decimal hides its structure: `240` says
> nothing, `0b1111_0000` says exactly what it is. Hex is the right choice
> for byte-aligned values and colour or protocol constants. Write the `A-F`
> digits in uppercase: Checkstyle's `HexLiteralCase` requires it (following
> the OpenJDK style guide), and a mix of `0xFF` and `0xff` in the same
> constant block makes diffs and greps noisy. The check looks only at the
> digits, not at the `0x` and `0b` prefixes, which are conventionally
> lowercase.
> **Suggestion for the choice of base; Violation for the digit case,
> enforced by Checkstyle `HexLiteralCase`.**

```java
// bad — the structure of the value is invisible, and the case is mixed
int highNibble = 240;
int colour = 0xFFaa00;

// good
int highNibble = 0b1111_0000;
int colour = 0xFFAA00;
```

## 29.18 Never shift by a distance outside the width of the operand type.

> Why? Java masks the shift distance rather than saturating it: for an
> `int`, only the low five bits of the right operand are used, so
> `1 << 32` is `1`, not `0`, and `1 << 33` is `2`. For a `long` the low six
> bits are used. Code that computes the shift distance — a bit-packing
> routine, a bloom filter, a flags enum — silently wraps and corrupts the
> encoding rather than producing zero. If the operand is an `int` but you
> need up to 64 positions, widen it first with a `1L` literal.
> **Violation — enforced by Error Prone `BadShiftAmount`.**

```java
// bad — 1, not 0; the int shift distance is masked to 5 bits
int all = 1 << 32;
int flag = 1 << index; // silently wrong when index >= 32

// good
long all = 1L << 32;
long flag = 1L << index; // correct for index in 0..63
```

## 29.19 Never compare floating-point values with `==`, and never assume `equals` and `==` agree.

> Why? Accumulated representation error means two values that are
> mathematically equal are usually not bitwise equal, so `==` on computed
> `double`s is a coin flip. Worse, the two comparison mechanisms disagree
> in opposite directions on the special values: `0.0 == -0.0` is `true` but
> `Double.compare(0.0, -0.0)` is positive, and `Double.NaN == Double.NaN`
> is `false` but `Double.valueOf(Double.NaN).equals(Double.valueOf(Double.NaN))`
> is `true`. Compare with an explicit tolerance for computed values, and use
> `Double.compare` for ordering. **Suggestion.**

```java
// bad — almost never true, and NaN makes it unpredictable
if (measured == expected) {}

// bad — no total order: NaN compares 0 against everything, so the sort
// result depends on the input order
Double[] values = readValues();
Arrays.sort(values, (a, b) -> (a < b) ? -1 : (a > b) ? 1 : 0);

// good — an explicit, domain-chosen tolerance
if (Math.abs(measured - expected) < TOLERANCE) {}

// good — total ordering, NaN and signed zero handled
Arrays.sort(values, Double::compare);
```

## 29.20 Handle `NaN` and infinity explicitly wherever a `double` can come from division or parsing.

> Why? `NaN` is contagious and silently poisons every downstream
> calculation: it is not equal to itself, every comparison against it is
> `false`, and `Math.max(NaN, x)` is `NaN`. Because floating-point division
> by zero produces `Infinity` or `NaN` rather than throwing, a bad input
> propagates all the way to a report or a database column instead of
> failing at the boundary. Validate with `Double.isFinite` where the value
> enters your domain, not where it is finally rendered.
> **Suggestion.**

```java
// bad — a zero denominator yields Infinity, and it is persisted as such
double rate = successes / (double) attempts;
repository.save(new Metric(name, rate));

// bad — every comparison against NaN is false, so this branch never runs
if (rate == Double.NaN) {}

// good — reject non-finite values at the boundary
double rate = successes / (double) attempts;
if (!Double.isFinite(rate)) {
  throw new IllegalArgumentException("rate is not finite for attempts=" + attempts);
}
repository.save(new Metric(name, rate));
```

## 29.21 Beware of literals that lose precision the moment they are written.

> Why? A `double` literal with more significant digits than the type can
> hold is silently rounded at compile time, so the constant in the source
> is not the constant in the class file — `double d = 0.1234567890123456789;`
> is not the number you typed, and a reader comparing the source against a
> specification will believe it is. Either write a literal the type can
> represent, or use `BigDecimal` and stop pretending `double` has the
> range. The same applies to an `int` literal assigned to a `float`, where
> large values lose low-order bits.
> **Violation — enforced by Error Prone `FloatingPointLiteralPrecision`.**

```java
// bad — the compiler rounds this; the class file holds a different number
double planckConstant = 6.62607015000000000001e-34;

// good — the literal is representable, or the type is exact
double planckConstant = 6.62607015e-34;
BigDecimal exactRate = new BigDecimal("0.1234567890123456789");
```

## 29.22 Choose the random source by purpose: `SecureRandom` for secrets, `ThreadLocalRandom` under contention, `RandomGenerator` otherwise.

> Why? These are three different guarantees and substituting one for
> another is a real defect. `java.util.Random` is a 48-bit linear
> congruential generator whose output is trivially predictable from a
> couple of samples, so using it for a token, a password reset code, or a
> session id is a security hole; use `SecureRandom`. `Random` is
> thread-safe but its single seed is a contention point, so a shared
> instance under load serialises callers; use `ThreadLocalRandom.current()`
> in that case — and never share a `ThreadLocalRandom` reference between
> threads, which defeats its entire design. For ordinary simulation and
> sampling, `RandomGenerator.getDefault()` (Java 17+) gives a modern
> algorithm behind a stable interface. **Suggestion.**

```java
// bad — predictable generator producing a security-sensitive value
private static final Random RANDOM = new Random();

public String newResetToken() {
  byte[] bytes = new byte[32];
  RANDOM.nextBytes(bytes);
  return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
}

// good — unpredictable source for anything security-sensitive
private static final SecureRandom SECURE_RANDOM = new SecureRandom();

public String newResetToken() {
  byte[] bytes = new byte[32];
  SECURE_RANDOM.nextBytes(bytes);
  return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
}

// good — non-security sampling on a hot path
int jitterMillis = ThreadLocalRandom.current().nextInt(0, 250);

// good — general-purpose, modern algorithm, injectable for tests
private final RandomGenerator random;

public Sampler(RandomGenerator random) {
  this.random = random;
}
```

## 29.23 Parse external numbers with the wrapper's `parse*` method and handle `NumberFormatException` at the boundary.

> Why? `Integer.parseInt` returns a primitive and `Integer.valueOf` returns
> a boxed object, so using `valueOf` where a primitive is wanted adds an
> allocation and an unboxing for nothing. More importantly, both throw
> `NumberFormatException` — an unchecked exception — on malformed input, so
> a value arriving from a request parameter, a config file, or a CSV column
> will crash with a stack trace that says nothing about *which* field was
> bad. Catch it where the field's identity is still known and convert it
> into a domain error ([Chapter 24](24-exceptions.md)).
> **Suggestion.**

```java
// bad — allocates for nothing, and the NFE escapes with no field context
int limit = Integer.valueOf(request.getParameter("limit"));

// good
private static int parseLimit(String raw) {
  try {
    return Integer.parseInt(raw);
  } catch (NumberFormatException e) {
    throw new InvalidRequestException("limit must be an integer but was: " + raw, e);
  }
}
```

## 29.24 Name every numeric constant instead of writing a magic number.

> Why? A bare `86_400` in an expression forces the reader to reverse
> engineer the unit and the intent, and the same value repeated in three
> places drifts when one of them is updated. A `private static final` with
> a name states the unit, gives the value one home, and makes the compiler
> the enforcer of consistency. The exceptions everyone accepts are `-1`,
> `0`, `1`, and `2` in obvious positions, and the dimensions of a small
> literal array. **Violation — enforced by Checkstyle `MagicNumber`.**

```java
// bad — what is 86400, and is 3 retries or seconds?
if (Duration.between(issuedAt, now).toSeconds() > 86400) {}
retry(operation, 3);

// good
private static final Duration TOKEN_TTL = Duration.ofDays(1);
private static final int MAX_RETRIES = 3;

if (Duration.between(issuedAt, now).compareTo(TOKEN_TTL) > 0) {}
retry(operation, MAX_RETRIES);
```
