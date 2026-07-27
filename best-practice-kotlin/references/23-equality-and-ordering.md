<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 23. Equality & Ordering

Kotlin splits equality into two operators that Java spells the same way. `==`
is **structural** equality and compiles to a null-safe `equals` call; `===` is
**referential** equality and compares object identity. Java's `==` is the
second of these, so every Java developer arriving in Kotlin brings a reflex
that is now wrong in the common case, and the compiler will not warn them —
`"a" === "a"` is a perfectly well-typed `Boolean` expression whose value
depends on the JVM's string pool. That reversal is §23.1 and it is the single
biggest thing to get right in this chapter.

The rest of the chapter is contract work: the `equals`/`hashCode` pact,
what `data class` does and does not derive, why a mutable property inside
`equals` corrupts a `HashSet`, and the `Comparable`/`Comparator` rules that
make sorting predictable. Float and array equality each get their own rule
because both behave differently from every other type.

Sources: the language reference on
[equality](https://kotlinlang.org/docs/equality.html) and
[numbers](https://kotlinlang.org/docs/numbers.html); the standard library
contracts for
[`Any.equals`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-any/equals.html),
[`Any.hashCode`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-any/hash-code.html),
and
[`Comparable.compareTo`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-comparable/compare-to.html);
and the
[kotlin.comparisons](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.comparisons/)
package for comparator construction. Data-class semantics are covered in
[Chapter 11, Data Classes](11-data-classes.md); value-class equality in
[Chapter 12, Value Classes](12-value-classes.md); string comparison beyond
equality in [Chapter 21, Strings](21-strings.md); and the immutability
argument behind §23.9 in [Chapter 25, Immutability](25-immutability.md).

**Tool alignment:** detekt's `AvoidReferentialEquality`,
`EqualsWithHashCodeExist`, `WrongEqualsTypeParameter`,
`EqualsAlwaysReturnsTrueOrFalse`, `EqualsNullCall`,
`DataClassShouldBeImmutable`, and `ImplicitDefaultLocale` all fire on rules
below. Rules a named check actually enforces are marked **Violation**; the
rest are **Suggestion**.

## 23.1 Use `==` for structural equality and `===` only when object identity is genuinely the question.

> Why? The
> [equality reference](https://kotlinlang.org/docs/equality.html) states that
> `a == b` is translated to `a?.equals(b) ?: (b === null)` — it is a null-safe
> `equals` call, not a pointer comparison. `===` is the pointer comparison, and
> it is almost never what a domain question needs: "is this the same order" is
> `==`, while "is this literally the object I handed you earlier" is `===`. The
> failure is silent and intermittent, because identity for interned strings and
> cached boxed integers depends on values the JVM chose, not on your code.
> **Suggestion.**

```kotlin
// bad — identity comparison where value comparison was meant
fun isConfirmed(status: String): Boolean = status === "CONFIRMED"

// good
fun isConfirmed(status: String): Boolean = status == "CONFIRMED"

// good — identity is the actual question: has the caller handed back our object?
fun isSameSession(candidate: Session): Boolean = candidate === activeSession
```

## 23.2 Never apply `===` to a `String`, a boxed number, or a collection.

> Why? These are exactly the types where identity is an implementation detail
> of the runtime. Two `String` values built from the same characters may or may
> not be the same object depending on whether one was a literal; `Integer`
> caching makes `===` true for small values and false above the cache
> threshold, so a test with `1` passes and production with `1000` fails.
> detekt's `AvoidReferentialEquality` puts it plainly: "checking for referential
> equality for some types (such as `String` or `List`) is likely not intentional
> and may cause unexpected results." **Violation — enforced by
> `detekt/AvoidReferentialEquality`** (default `forbiddenTypePatterns` is
> `['kotlin.String']`; add your own collection and boxed-number patterns).

```kotlin
// bad — true for a literal, false for a computed string; passes in tests
val a: String = "CONFIRMED"
val b: String = buildStatus()
println(a === b) // false, even when a == b

// bad — depends on the Integer cache; true for 127, false for 128
val x: Int? = 127
val y: Int? = 127
println(x === y) // true — and false if both were 128

// good
println(a == b)
println(x == y)
```

## 23.3 Compare against `null` with `== null`, never with `equals(null)`.

> Why? `a == null` is compiled directly to `a === null` — no method call, no
> chance of a `NullPointerException` on the receiver, and no dependence on
> whether the receiver's `equals` handles `null` correctly. `a.equals(null)`
> requires `a` to be non-null already, so it either fails to compile on a
> nullable receiver or invites a `?.` that makes the whole expression a
> nullable `Boolean` and drags in the §22.20 problem. **Violation — enforced by
> `detekt/EqualsNullCall`.**

```kotlin
// bad — a method call where an identity check will do, and the result is Boolean?
if (customer?.equals(null) == true) {
    return Outcome.Missing
}

// good
if (customer == null) {
    return Outcome.Missing
}
```

## 23.4 Override `equals` and `hashCode` together, or override neither.

> Why? The documented contract for
> [`Any.hashCode`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-any/hash-code.html)
> requires that "if two objects are equal according to the `equals()` method,
> then calling the `hashCode` method on each of the two objects must produce the
> same integer result." Override `equals` alone and two equal objects land in
> different buckets, so a `HashSet` holds visible duplicates and
> `map[key]` returns `null` for a key that is `==` to one already stored. The
> failure is data-dependent and will not reproduce on a one-element fixture.
> **Violation — enforced by `detekt/EqualsWithHashCodeExist`.**

```kotlin
// bad — hashCode is still identity-based, so the set holds two "equal" entries
class Sku(val code: String) {
    override fun equals(other: Any?): Boolean = other is Sku && code == other.code
}

val skus = setOf(Sku("A-1"), Sku("A-1")) // size == 2

// good
class Sku(val code: String) {
    override fun equals(other: Any?): Boolean = other is Sku && code == other.code

    override fun hashCode(): Int = code.hashCode()
}
```

## 23.5 Declare `equals` with the parameter type `Any?`; a typed parameter is an unrelated overload.

> Why? `Any.equals` is declared as `equals(other: Any?): Boolean`. Writing
> `equals(other: Sku)` does not override it — it adds a second function with a
> different signature, so the compiler will not even let you write `override`,
> and every caller that goes through `==`, a `HashMap`, or a `List.contains`
> still reaches the inherited identity implementation. The code looks correct
> and behaves as though nothing was written. **Violation — enforced by
> `detekt/WrongEqualsTypeParameter`.**

```kotlin
// bad — this is an overload, not an override; == still compares identity
class Sku(val code: String) {
    fun equals(other: Sku): Boolean = code == other.code
    override fun hashCode(): Int = code.hashCode()
}

// good
class Sku(val code: String) {
    override fun equals(other: Any?): Boolean = other is Sku && code == other.code

    override fun hashCode(): Int = code.hashCode()
}
```

## 23.6 Write `equals` in the standard shape: identity fast path, `is` check, then field comparison.

> Why? The
> [`Any.equals` contract](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-any/equals.html)
> demands reflexivity, symmetry, transitivity, consistency, and
> `x.equals(null) == false`. The canonical shape satisfies all five by
> construction: `this === other` gives reflexivity for free and short-circuits
> the common self-comparison, `other is T` gives both the null rejection and the
> smart cast, and comparing the identifying fields gives symmetry and
> transitivity. Deviating from it — a bare `return true`, a `!=` on the wrong
> field — produces an `equals` that compiles and quietly breaks every
> hash-based collection. **Violation — enforced by
> `detekt/EqualsAlwaysReturnsTrueOrFalse`** for the degenerate cases; the
> unchecked `as` in the bad example below is `detekt/UnsafeCast` territory only
> when the cast can never succeed, so nothing catches the general shape.

```kotlin
// bad — no null handling, no type check, and an unchecked cast
class Money(val minorUnits: Long, val currency: Currency) {
    override fun equals(other: Any?): Boolean {
        val that = other as Money
        return minorUnits == that.minorUnits
    }

    override fun hashCode(): Int = minorUnits.hashCode()
}

// good
class Money(val minorUnits: Long, val currency: Currency) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is Money) return false
        return minorUnits == other.minorUnits && currency == other.currency
    }

    override fun hashCode(): Int = 31 * minorUnits.hashCode() + currency.hashCode()
}
```

## 23.7 Use an exact-class check instead of `is` when the type is `open` and a subclass may add state.

> Why? `other is Money` accepts a subclass, which breaks symmetry the moment
> the subclass adds a field to its own `equals`: `base.equals(derived)` is
> `true` while `derived.equals(base)` is `false`, so whether a `HashSet`
> contains an element depends on which object it happened to compare first.
> Comparing `javaClass` instead makes the relation symmetric for every pair.
> The cleanest answer is usually to close the type — a `final` class (Kotlin's
> default) or a `data class` never has this problem, which is why §23.7 only
> applies to hierarchies that were deliberately opened. **Suggestion.**

```kotlin
// bad — open class with an `is` check; symmetry breaks against any subclass
open class Money(val minorUnits: Long) {
    override fun equals(other: Any?): Boolean =
        other is Money && minorUnits == other.minorUnits

    override fun hashCode(): Int = minorUnits.hashCode()
}

class TaxedMoney(minorUnits: Long, val taxMinorUnits: Long) : Money(minorUnits)

// good — exact class comparison keeps the relation symmetric
open class Money(val minorUnits: Long) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other == null || javaClass != other.javaClass) return false
        return minorUnits == (other as Money).minorUnits
    }

    override fun hashCode(): Int = minorUnits.hashCode()
}
```

## 23.8 Know that a `data class` derives `equals`, `hashCode`, and `toString` from its primary-constructor properties only.

> Why? Properties declared in the class body are invisible to the generated
> members. Two instances that differ only in a body property are `==`, hash
> identically, and print identically — so a cache keyed on the object silently
> returns the wrong one, and a failing test prints two objects that look the
> same. This is a deliberate design choice, not a bug, and the fix is to move
> the identifying property into the primary constructor (or to stop using a
> `data class`; see [Chapter 11](11-data-classes.md)). **Suggestion.**

```kotlin
// bad — `region` is not part of equals/hashCode/toString
data class Warehouse(val id: String) {
    var region: String = "unknown"
}

val a = Warehouse("W1").apply { region = "eu-west" }
val b = Warehouse("W1").apply { region = "us-east" }
println(a == b)   // true
println(a)        // Warehouse(id=W1) — region is invisible

// good — everything that identifies the value is in the primary constructor
data class Warehouse(val id: String, val region: String)
```

## 23.9 Never let a `var` property participate in `equals`/`hashCode` if instances are used as `Set` elements or `Map` keys.

> Why? The `hashCode` contract only promises consistency "provided no
> information used in `equals` comparisons on the object is modified." Mutate a
> participating property after insertion and the object's hash changes while it
> sits in the bucket chosen by its old hash: the collection now contains an
> element it cannot find. `contains` returns `false`, `remove` is a no-op, and
> the entry leaks for the lifetime of the map. Making the components `val` is
> the fix, and it is why data classes are supposed to be immutable.
> **Violation — enforced by `detekt/DataClassShouldBeImmutable`,** which
> reports "mutable properties inside data classes" but is **not active in
> detekt's default configuration**; it also does nothing for a non-data class
> that overrides `equals` over a `var`, which this rule still forbids.

```kotlin
// bad — mutating `code` after insertion strands the element in the set
data class Sku(var code: String)

val sku = Sku("A-1")
val stock = mutableSetOf(sku)
sku.code = "A-2"
println(stock.contains(sku))  // false — the object is in the set and unreachable
println(stock.remove(sku))    // false — cannot be removed either

// good — the identity of a value cannot change under the collection
data class Sku(val code: String)

val sku = Sku("A-1")
val stock = mutableSetOf(sku)
val renamed = sku.copy(code = "A-2")
```

## 23.10 Make `toString` describe the value, and keep credentials and personal data out of it.

> Why? `toString` is what a log line, an assertion failure, and a debugger
> tooltip show, so its job is to let a reader distinguish this instance from a
> similar one — the default `Warehouse@6d06d69c` fails at that completely. The
> mirror-image failure is worse: a `data class` generates a `toString`
> containing *every* primary-constructor property, so a password, token, or
> national identifier put there will be written to the log the first time
> anything prints the object. Wrap secrets in a type whose `toString` redacts
> them (see [Chapter 12, Value Classes](12-value-classes.md)) or override
> `toString` by hand. **Suggestion.**

```kotlin
// bad — the generated toString leaks the token into every log line
data class ApiCredential(val clientId: String, val secret: String)

logger.info { "authenticating with $credential" }
// ApiCredential(clientId=svc-billing, secret=sk_live_9f3a...)

// good — the secret is present in the value and absent from its rendering
data class ApiCredential(val clientId: String, val secret: Secret) {
    override fun toString(): String = "ApiCredential(clientId=$clientId, secret=***)"
}

class Secret(private val value: String) {
    fun reveal(): String = value

    override fun toString(): String = "***"
}
```

## 23.11 Implement `Comparable` only when the type has exactly one obvious natural order; otherwise expose a `Comparator`.

> Why? `Comparable` is a claim that the type has *the* order, and it is the
> order every `sorted()`, `TreeSet`, and `maxOrNull()` will silently use
> forever. A `Person` has no natural order — surname then forename is a
> presentation choice, and hire date is another — so baking one in means every
> other ordering has to fight it. Money, versions, and timestamps do have a
> natural order and should implement `Comparable`. **Suggestion.**

```kotlin
// bad — an arbitrary presentation order frozen into the type
data class Employee(val surname: String, val forename: String, val hiredOn: LocalDate) :
    Comparable<Employee> {
    override fun compareTo(other: Employee): Int = surname.compareTo(other.surname)
}

// good — the type has no natural order, so orderings are named and chosen
data class Employee(val surname: String, val forename: String, val hiredOn: LocalDate) {
    companion object {
        val BY_NAME: Comparator<Employee> = compareBy({ it.surname }, { it.forename })
        val BY_SENIORITY: Comparator<Employee> = compareBy { it.hiredOn }
    }
}

// good — a type that genuinely has one order
@JvmInline
value class Money(val minorUnits: Long) : Comparable<Money> {
    override fun compareTo(other: Money): Int = minorUnits.compareTo(other.minorUnits)
}
```

## 23.12 Never implement `compareTo` by subtraction.

> Why? `a - b` overflows. `Int.MIN_VALUE - 1` wraps to `Int.MAX_VALUE`, so a
> comparator built on subtraction reports that a very negative number is
> *greater* than a positive one. The resulting order violates transitivity,
> which means `sortedWith` may throw
> `IllegalArgumentException: Comparison method violates its general contract!`,
> and a `TreeMap` built with it can lose entries. `compareTo` on the field, or
> `compareValuesBy`, is exact for the whole range and reads no worse.
> **Suggestion** — no linter models the overflow.

```kotlin
// bad — overflows for large-magnitude operands and breaks transitivity
class Reading(val micros: Int) : Comparable<Reading> {
    override fun compareTo(other: Reading): Int = micros - other.micros
}

println(Reading(Int.MIN_VALUE) < Reading(1)) // false — wrong

// good
class Reading(val micros: Int) : Comparable<Reading> {
    override fun compareTo(other: Reading): Int = micros.compareTo(other.micros)
}

// good — multiple keys, still exact
class Reading(val micros: Int, val sensorId: String) : Comparable<Reading> {
    override fun compareTo(other: Reading): Int =
        compareValuesBy(this, other, { it.micros }, { it.sensorId })
}
```

## 23.13 Keep `compareTo` consistent with `equals`, or document loudly that it is not.

> Why? The sorted collections do not use `equals` at all — `TreeSet` and
> `TreeMap` decide that two elements are duplicates when `compareTo` returns
> zero. If `compareTo` compares fewer fields than `equals`, adding a
> genuinely distinct element to a `TreeSet` silently drops it; if it compares
> more, a `TreeMap` lookup misses a key that is `==` to one it holds. The same
> object then behaves one way in a `HashSet` and another in a `TreeSet`, which
> is the hardest class of bug to reproduce. **Suggestion.**

```kotlin
// bad — equals uses (id, issuedAt); compareTo uses issuedAt only
data class Ticket(val id: String, val issuedAt: Instant) : Comparable<Ticket> {
    override fun compareTo(other: Ticket): Int = issuedAt.compareTo(other.issuedAt)
}

val now = Instant.now()
val sorted = sortedSetOf(Ticket("T1", now), Ticket("T2", now))
println(sorted.size) // 1 — T2 was silently discarded

// good — compareTo tie-breaks on every field equals considers
data class Ticket(val id: String, val issuedAt: Instant) : Comparable<Ticket> {
    override fun compareTo(other: Ticket): Int =
        compareValuesBy(this, other, { it.issuedAt }, { it.id })
}
```

## 23.14 Build comparators with `compareBy` and `thenBy`, not a hand-written chain of comparisons.

> Why? The hand-written form re-derives the same three-way-comparison logic on
> every key, and the bug it invites is silent: forgetting to return early after
> a non-zero primary comparison discards the primary key entirely. `compareBy`
> and `thenBy` from
> [kotlin.comparisons](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.comparisons/)
> encode "compare by this, then by that" as composition, so the ordering reads
> in the order it is applied and no early return can be forgotten. Use
> `compareByDescending` and `thenByDescending` rather than negating a result.
> **Suggestion.**

```kotlin
// bad — the primary key is computed and then thrown away
val byNameThenDate = Comparator<Employee> { a, b ->
    a.surname.compareTo(b.surname)
    a.hiredOn.compareTo(b.hiredOn)
}

// bad — negating a comparison to reverse it; correct here, but breaks the
// moment the result is Int.MIN_VALUE
val newestFirst = Comparator<Employee> { a, b -> -a.hiredOn.compareTo(b.hiredOn) }

// good
val byNameThenDate: Comparator<Employee> = compareBy<Employee> { it.surname }
    .thenBy { it.forename }
    .thenByDescending { it.hiredOn }

val newestFirst: Comparator<Employee> = compareByDescending { it.hiredOn }
```

## 23.15 State null ordering explicitly with `nullsFirst` or `nullsLast`.

> Why? A comparator that dereferences a nullable key throws
> `NullPointerException` the first time a null arrives — usually in production,
> on the one row that has no value. `nullsFirst` and `nullsLast` wrap an
> existing comparator and place nulls at a chosen end, turning an implicit
> crash into a stated policy. `compareBy` on a nullable selector already routes
> through `compareValues`, which puts null first; if you want the other end,
> say so. **Suggestion.**

```kotlin
// bad — throws as soon as one employee has no termination date
val byTermination = Comparator<Employee> { a, b ->
    a.terminatedOn!!.compareTo(b.terminatedOn!!)
}

// good — active employees (null termination date) sort last, deliberately
val byTermination: Comparator<Employee> =
    compareBy(nullsLast<LocalDate>()) { it.terminatedOn }
```

## 23.16 Rely on sort stability instead of inventing a tiebreaker that has no meaning.

> Why? `sortedWith` documents that "the sort is *stable*. It means that equal
> elements preserve their order relative to each other after sorting." So
> sorting by department and then by name is two stable sorts in reverse order,
> or one composed comparator — either way you never need to append an
> arbitrary key like `id` merely to make the result deterministic. Appending a
> meaningless tiebreaker hides the fact that the primary keys tie, and it makes
> the order change when ids are reassigned. Add a tiebreaker only when the tie
> has a defined resolution (as in §23.13, where consistency with `equals`
> demands one). **Suggestion.**

```kotlin
// bad — `id` is appended only to make the output deterministic, and now the
// display order changes whenever ids are reassigned
val display = employees.sortedWith(
    compareBy<Employee> { it.department }.thenBy { it.id },
)

// good — one composed comparator over keys that mean something; ties keep
// their input order because the sort is stable
val display = employees.sortedWith(
    compareBy<Employee> { it.department }.thenBy { it.surname },
)
```

## 23.17 Never compare computed `Double` or `Float` values with `==`, and know that the semantics change when the static type is not floating point.

> Why? Two facts, both surprising. First, IEEE 754 arithmetic makes
> `0.1 + 0.2 == 0.3` false, so equality on computed floating-point values is a
> question about representation, not about magnitude — compare against a
> tolerance, or use `BigDecimal` for money. Second, the
> [numbers reference](https://kotlinlang.org/docs/numbers.html) documents that
> IEEE semantics apply only "when operands are statically known to be `Float` or
> `Double`"; through a non-floating-point static type such as `Any`,
> `Comparable<*>`, or a generic `T`, Kotlin falls back to `equals`/`compareTo`,
> under which "`NaN` is considered equal to itself" and "`-0.0` is considered
> less than `0.0`." The same two values therefore compare differently depending
> on where they are standing, which is why a `Double` must never be a `Map` key
> or a `Set` element. **Suggestion.**

```kotlin
// bad — false, and the reason is invisible at the call site
println(0.1 + 0.2 == 0.3) // false

// bad — the same pair, two answers, depending on static type
fun generalizedEquals(a: Any, b: Any): Boolean = a == b

println(Double.NaN == Double.NaN)                  // false  (IEEE 754)
println(generalizedEquals(Double.NaN, Double.NaN)) // true   (equals)
println(0.0 == -0.0)                               // true   (IEEE 754)
println(generalizedEquals(0.0, -0.0))              // false  (equals)

// good — compare with an explicit tolerance
private const val EPSILON = 1e-9

fun approximatelyEquals(a: Double, b: Double): Boolean = abs(a - b) < EPSILON

// good — exact decimal arithmetic where exactness is the requirement
val total: BigDecimal = BigDecimal("0.1") + BigDecimal("0.2")
println(total == BigDecimal("0.3")) // true
```

## 23.18 Compare arrays with `contentEquals` or `contentDeepEquals`, never with `==`.

> Why? `Array` does not override `equals`, so `==` on two arrays is identity —
> the one place in Kotlin where `==` and `===` mean the same thing for a
> reference type, and the one place a reader will not expect it. `contentEquals`
> compares element by element, `contentDeepEquals` recurses into nested arrays,
> and `contentHashCode`/`contentDeepHashCode` are their `hashCode` partners. The
> consequence for class design is §23.8's twin: an `Array` property inside a
> `data class` makes the generated `equals` compare identities, so two instances
> holding identical contents are unequal. Use a `List` in any type that needs
> value semantics. **Suggestion.**

```kotlin
// bad — compares references; false for two arrays with identical contents
val a = intArrayOf(1, 2, 3)
val b = intArrayOf(1, 2, 3)
println(a == b) // false

// bad — the generated equals compares the array reference
data class Payload(val bytes: ByteArray)

println(Payload(byteArrayOf(1)) == Payload(byteArrayOf(1))) // false

// good
println(a.contentEquals(b))                              // true
println(arrayOf(a).contentDeepEquals(arrayOf(b)))        // true

// good — a List gives the data class real value semantics
data class Payload(val bytes: List<Byte>)
```

## 23.19 Compare collections with `==`, but remember a `List` is never equal to a `Set`.

> Why? Collections do implement structural `equals`, and it is defined across
> implementations: an `ArrayList` equals a `LinkedList` with the same elements
> in the same order, and a `HashSet` equals a `LinkedHashSet` with the same
> members. What does not hold is equality *across* collection kinds — a `List`
> requires the other side to be a `List`, so `listOf(1, 2) == setOf(1, 2)` is
> `false` no matter how it reads. This bites when a repository changes a return
> type from `List` to `Set` and a test comparing against a literal list starts
> failing for a reason unrelated to the data. **Suggestion.**

```kotlin
// bad — the repository now returns a Set, so this is false for every input
val ids: Collection<Int> = repository.activeIds()
check(ids == listOf(1, 2, 3)) { "unexpected ids: $ids" }

// good — compare like with like when membership is the question
check(ids.toSet() == setOf(1, 2, 3)) { "unexpected ids: $ids" }

// good — compare as lists when order is the question
check(ids.sorted() == listOf(1, 2, 3)) { "unexpected ids: $ids" }
```

## 23.20 Compare strings case-insensitively with `equals(other, ignoreCase = true)`, and pass an explicit `Locale` to any case conversion you keep.

> Why? `a.lowercase() == b.lowercase()` allocates two strings to answer a
> question the standard library answers directly, and — worse — the no-argument
> `lowercase()` uses the platform default locale. In a Turkish locale `"I"`
> lowercases to a dotless `"ı"`, so `"ID".lowercase() == "id"` is `false` on a
> machine configured differently from your laptop. The same applies to
> `compareTo(other, ignoreCase = true)` for ordering. Reserve
> `lowercase(Locale.ROOT)` for values you are storing or transmitting, and use
> the locale-aware overload only for text shown to a user. See
> [Chapter 21, Strings](21-strings.md) for the rest of the string rules.
> **Violation — enforced by `detekt/ImplicitDefaultLocale`.**

```kotlin
// bad — two allocations, and wrong under a Turkish default locale
fun matches(header: String, expected: String): Boolean =
    header.lowercase() == expected.lowercase()

// good — one call, locale-independent by construction
fun matches(header: String, expected: String): Boolean =
    header.equals(expected, ignoreCase = true)

// good — case folding for storage is explicitly locale-independent
val normalizedKey = header.lowercase(Locale.ROOT)

// good — case-insensitive ordering
val headers = raw.sortedWith { a, b -> a.compareTo(b, ignoreCase = true) }
```
