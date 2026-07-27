<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 12. Value Classes

A `@JvmInline value class` is the only construct in Kotlin that gives you a
genuinely new type without paying for an object. `UserId`, `OrderId`, and
`Sku` all erase to `String` at runtime, yet the compiler refuses to let you
pass one where another is expected — and it will refuse in every existing
call site the moment you introduce the type, which is what makes the
refactor worth doing.

This chapter is about that trade. The rules come from the
[language documentation on inline value classes](https://kotlinlang.org/docs/inline-classes.html),
which is the normative source for every restriction quoted below: "an inline
class must have a single property initialized in the primary constructor",
"inline class properties cannot have backing fields... (no `lateinit`
/delegated properties)", "it is forbidden for inline classes to participate
in a class hierarchy... [they] are always `final`", "inline classes are
allowed to inherit from interfaces", and the representation rule that
governs when the wrapper reappears: "as a rule of thumb, inline classes are
boxed whenever they are used as another type."

Value classes sit between two neighbours. **Data classes** — the right shape
once a value has two or more components — are
[Chapter 11](11-data-classes.md), whose §11.18 hands off to this chapter.
**Type aliases**, which look similar and are not, are
[Chapter 7](07-types-and-type-aliases.md); §12.3 states the one distinction
that decides between them. The JVM-signature consequences in §12.10 and
§12.11 are a preview of [Chapter 28](28-java-interop.md), and the Spring web
binding in §12.16 belongs to
[Chapter 44](44-spring-web-and-coroutines.md).

**Tool alignment:** neither ktlint nor detekt ships a rule that recognises
value classes as such, so almost every rule in this chapter is a
**Suggestion**. `detekt/MagicNumber` and `detekt/LongParameterList` fire on
the surrounding code in the usual way, but nothing will tell you that a bare
`String` parameter should have been a `UserId`. Treat §12.2 as a review
question, not a lint finding.

## 12.1 Declare a value class with both the `value` modifier and `@JvmInline`.

> Why? The docs are prescriptive about the JVM spelling: "To declare an
> inline class for the JVM backend, use the `value` modifier along with the
> `@JvmInline` annotation before the class declaration." `value class` alone
> is not a JVM declaration you can compile — the annotation is what selects
> the inline representation. Write it once, at the top of the declaration,
> and never on a nested member.

```kotlin
// bad — does not compile on the JVM backend
value class UserId(val value: String)

// good
@JvmInline
value class UserId(val value: String)
```

## 12.2 Wrap a domain-meaningful primitive in a value class so a mix-up cannot compile.

> Why? This is the whole point of the construct. When `userId`, `orderId`,
> and `sku` are all `String`, a transposed argument pair is a runtime bug
> that gets caught in staging at best and in a support ticket at worst — and
> it is invisible in a diff, because both sides of the swap are the same
> type. Give each one a value class and the swap becomes a compile error at
> every call site simultaneously, with no allocation and no runtime cost in
> the common case (§12.7). The mechanical part of the refactor is finding the
> call sites, and the compiler does that for you. **Suggestion** — no linter
> can tell a meaningful `String` from an incidental one.

```kotlin
// bad — the two arguments are transposed; this compiles and ships
fun cancel(orderId: String, userId: String) { /* ... */ }

cancel(userId, orderId)

// good — the same call is now a compile error at every site at once
@JvmInline
value class OrderId(val value: String)

@JvmInline
value class UserId(val value: String)

fun cancel(orderId: OrderId, userId: UserId) { /* ... */ }

cancel(userId, orderId) // error: type mismatch
```

## 12.3 Use a value class, not a type alias, whenever a mix-up would be a bug.

> Why? The docs draw the line unambiguously: "the crucial difference is that
> type aliases are assignment-compatible with their underlying type (and with
> other type aliases with the same underlying type), while inline classes are
> not. In other words, inline classes introduce a truly new type, contrary to
> type aliases which only introduce an alternative name (alias) for an
> existing type." A `typealias UserId = String` is documentation the compiler
> ignores; it buys readability at the declaration and enforces nothing at the
> call site. Reserve `typealias` for shortening long generic and function
> types — see
> [the conventions' type aliases guidance](https://kotlinlang.org/docs/coding-conventions.html#type-aliases)
> and [Chapter 7](07-types-and-type-aliases.md).

```kotlin
// bad — the alias documents an intent the compiler will not enforce
typealias UserId = String
typealias OrderId = String

fun archive(userId: UserId) { /* ... */ }

val orderId: OrderId = "ord-7"
archive(orderId)      // compiles: both are String
archive("literally anything")

// good
@JvmInline
value class UserId(val value: String)

fun archive(userId: UserId) { /* ... */ }

archive(orderId)      // error: type mismatch
archive("anything")   // error: type mismatch
```

## 12.4 Put the type's invariant in an `init` block — this is the main reason to prefer a value class over a type alias.

> Why? "Inline classes support some functionality of regular classes. In
> particular, they are allowed to declare properties and functions, have an
> `init` block and secondary constructors." That `init` block turns the
> wrapper from a naming device into a parse-don't-validate boundary: once a
> `Percentage` exists, it is in range, and no function downstream needs to
> re-check. A type alias can express none of this. Use `require` for anything
> a caller can get wrong, exactly as in
> [§10.4](10-classes-and-interfaces.md).

```kotlin
// bad — the type says "percentage" and guarantees nothing; every consumer
// re-checks, and one of them will forget
@JvmInline
value class Percentage(val value: Int)

fun applyDiscount(price: Long, discount: Percentage): Long {
    require(discount.value in 0..100) { "out of range" } // again, and again
    return price * (100 - discount.value) / 100
}

// good — invalid values cannot be represented
@JvmInline
value class Percentage(val value: Int) {
    init {
        require(value in 0..100) { "percentage must be 0..100, was $value" }
    }
}

fun applyDiscount(price: Long, discount: Percentage): Long =
    price * (100 - discount.value) / 100
```

## 12.5 Keep exactly one `val` in the primary constructor and add no other state.

> Why? These are hard compiler restrictions, not preferences: "an inline
> class must have a single property initialized in the primary constructor",
> and "inline class properties cannot have backing fields. They can only have
> simple computable properties (no `lateinit` /delegated properties)." The
> reason is representational — the class *is* its single value at runtime, so
> there is nowhere for a second field to live. Computed properties and
> functions are fine, because they need no storage. If you find yourself
> wanting a second field, you wanted a `data class` (§12.17).

```kotlin
// bad — every one of these is a compile error
@JvmInline
value class Range(val from: Int, val to: Int) // two constructor properties

@JvmInline
value class CachedKey(val key: String) {
    var hits: Int = 0                          // backing field
    lateinit var loadedAt: Instant             // lateinit
    val parts: List<String> by lazy { key.split(":") } // delegated property
}

// good — computed properties and functions need no storage
@JvmInline
value class CacheKey(val value: String) {
    val tenant: String get() = value.substringBefore(':')

    val path: String get() = value.substringAfter(':')

    fun scopedTo(prefix: String): CacheKey = CacheKey("$prefix:$value")
}
```

## 12.6 Share behaviour through an interface; a value class is always final.

> Why? "It is forbidden for inline classes to participate in a class
> hierarchy. This means that inline classes cannot extend other classes and
> are always `final`." What they *can* do is "inherit from interfaces", so an
> interface is the only mechanism available for common behaviour across
> several value classes. Note that using the value through its interface type
> boxes it (§12.7) — which is the correct trade when the alternative is
> duplicating the same three members across nine identifier types.

```kotlin
// bad — a value class cannot extend a class
open class Identifier(val raw: String)

@JvmInline
value class UserId(val value: String) : Identifier(value) // does not compile

// good
interface Identifier {
    val raw: String
}

@JvmInline
value class UserId(val value: String) : Identifier {
    override val raw: String get() = value
}

@JvmInline
value class OrderId(val value: String) : Identifier {
    override val raw: String get() = value
}
```

## 12.7 Know the four places the wrapper reappears, and do not design around them.

> Why? "As a rule of thumb, inline classes are boxed whenever they are used
> as another type" — as a nullable, as a generic type argument, as an
> interface type, or as `Any`. The docs' own example enumerates exactly
> these. Two conclusions follow, and both matter. First: the zero-allocation
> claim is real for the direct case, which is most parameters and most return
> values. Second: it does not hold inside a `List<UserId>` or a `UserId?` —
> and that is fine. A boxed value class costs precisely what the equivalent
> `data class` would have cost, so the fallback is never *worse* than the
> alternative you would otherwise have written. Choosing a raw `String` to
> dodge boxing trades a compile-time guarantee for an allocation you were
> going to make anyway.

```kotlin
interface Identifier {
    val raw: String
}

@JvmInline
value class UserId(val value: String) : Identifier {
    override val raw: String get() = value
}

fun direct(id: UserId) { /* ... */ }

fun <T> generic(value: T) { /* ... */ }

fun asInterface(id: Identifier) { /* ... */ }

fun any(value: Any) { /* ... */ }

val id = UserId("u-1")

direct(id)                            // unboxed — the JVM parameter is a String
generic(id)                           // boxed — used as T
asInterface(id)                       // boxed — used as Identifier
any(id)                               // boxed — used as Any
val maybe: UserId? = id               // boxed — UserId? is a different type
val all: List<UserId> = listOf(id)    // boxed — List<T> is generic

// bad — reverting to the raw type to avoid a boxing cost you would pay anyway
fun loadAll(ids: List<String>): List<User> { /* ... */ }

// good
fun loadAll(ids: List<UserId>): List<User> { /* ... */ }
```

## 12.8 Do not wrap a value whose wrapper name adds nothing.

> Why? A value class earns its keep by making one of two things impossible: a
> mix-up between two same-typed concepts (§12.2), or an invalid value
> (§12.4). A wrapper that does neither is pure ceremony — it adds a type to
> read, an `.value` to every use site, a mangled JVM signature (§12.10), and
> a conversion at every boundary, in exchange for nothing. `Name(val value:
> String)` on a type that is only ever displayed is the canonical example.
> **Suggestion.**

```kotlin
// bad — nothing can be confused with a display name, and any string is valid
@JvmInline
value class DisplayName(val value: String)

@JvmInline
value class Note(val value: String)

data class Profile(val name: DisplayName, val note: Note?)

println(profile.name.value) // .value at every single use site

// good — wrap the identifier, leave the prose alone
@JvmInline
value class UserId(val value: String)

data class Profile(val id: UserId, val name: String, val note: String?)
```

## 12.9 Decide between value class, data class, type alias, and plain class by what the type must guarantee.

> Why? All four spellings produce "a type with a name", so the choice is
> easy to make by habit rather than by requirement. The distinguishing
> questions are: how many components does the value have, must the compiler
> reject a mix-up, and does identity matter more than contents? Answering
> those three in order picks the construct every time. **Suggestion.**

| The type… | Use | Because |
|---|---|---|
| has one component; a mix-up or an invalid value must not compile | `@JvmInline value class` | distinct type, `init` validation, no allocation in the direct case |
| has two or more components and its identity is its contents | `data class` ([Ch. 11](11-data-classes.md)) | generated `equals`/`hashCode`/`copy` are correct for a value carrier |
| is just a shorter name for a long generic or function type | `typealias` ([Ch. 7](07-types-and-type-aliases.md)) | no new type is wanted, and none is created |
| has identity, invariants, or behaviour maintained by methods | plain `class` ([Ch. 10](10-classes-and-interfaces.md)) | `copy()` and structural equality would both be wrong |

```kotlin
// good — one of each, chosen by the table
@JvmInline
value class Sku(val value: String)                         // one component, must not mix up

data class Money(val amountMinor: Long, val currency: String) // two components, is its contents

typealias PriceLookup = (Sku) -> Money                     // a function type, shortened

class PricingService(private val rates: RateTable)         // behaviour and collaborators
```

## 12.10 Annotate `@JvmName` on any function taking a value class parameter that Java must call.

> Why? The compiler mangles the JVM name of a function that takes a value
> class parameter: "functions using inline classes are mangled by adding some
> stable hashcode to the function name. Therefore, `fun compute(x: UInt)` will
> be represented as `public final void compute-<hashcode>(int x)`, which solves
> the clash problem." The hyphen makes the name unusable from Java
> entirely. The documented workaround is to "add the `@JvmName` annotation
> before the function declaration". Kotlin callers are unaffected either way,
> so this is only a rule at a Java-facing boundary — but at that boundary it
> is the difference between a callable API and one that does not resolve. See
> [Chapter 28](28-java-interop.md).

```kotlin
@JvmInline
value class Cents(val value: Long)

// bad — the JVM method is `charge-<hashcode>(long)`; Java cannot name it
fun charge(amount: Cents) { /* ... */ }

// good — a stable JVM name for Java callers
@JvmName("chargeCents")
fun charge(amount: Cents) { /* ... */ }
```

## 12.11 Never treat a value class as a validation barrier against Java or reflection-driven callers.

> Why? Because the class erases to its underlying type, the JVM signature a
> Java caller sees takes a `long`, a `String`, or an `int` — not your
> wrapper. Nothing stops that caller from passing a value your `init` block
> would have rejected, and nothing runs the `init` block, because no wrapper
> is ever constructed. The same applies to any framework that populates
> values reflectively. Inside Kotlin, the invariant is real; across the
> boundary, it is a convention. Validate again at the boundary, or expose the
> underlying type there deliberately. **Suggestion.**

```kotlin
@JvmInline
value class Percentage(val value: Int) {
    init {
        require(value in 0..100) { "percentage must be 0..100, was $value" }
    }
}

@JvmName("applyPercentage")
fun apply(price: Long, discount: Percentage): Long =
    price * (100 - discount.value) / 100

// From Java: applyPercentage(1000L, 250) compiles and runs. The init block
// never executes, because no Percentage object is ever created.

// good — the Kotlin-facing API keeps the type; the Java-facing entry point
// re-validates by constructing the wrapper explicitly
@JvmName("applyPercentageChecked")
fun applyChecked(price: Long, discountPercent: Int): Long =
    apply(price, Percentage(discountPercent))
```

## 12.12 Use a value class as a map key freely; equality and hashing come from the wrapped value.

> Why? The compiler generates `equals`, `hashCode`, and `toString` for a
> value class the same way it does for a data class, all derived from the
> single wrapped property — so a `Map<Sku, Int>` behaves exactly as the
> `Map<String, Int>` it erases to, while refusing an `OrderId` key at compile
> time. The key is boxed, because a generic type argument always boxes
> (§12.7), which is the same allocation the raw `String` key would have made.
> Note that referential equality is not available: "because inline classes may
> be represented both as the underlying value and as a wrapper, referential
> equality is pointless for them and is therefore prohibited" — a restriction,
> not a limitation, since two wrappers over equal values are indistinguishable
> by design.

```kotlin
// bad — the map accepts any string, including an order id or a typo
val stock: MutableMap<String, Int> = mutableMapOf()
stock[orderId] = 4 // compiles; wrong key space

// good — same runtime behaviour, wrong keys rejected at compile time
@JvmInline
value class Sku(val value: String)

val stock: MutableMap<Sku, Int> = mutableMapOf()
stock[Sku("A-1")] = 4
stock[orderId] = 4          // error: type mismatch
println(Sku("A-1") in stock) // true — hashing follows the wrapped String
```

## 12.13 Override `toString()` on a value class that wraps a secret.

> Why? The generated `toString` renders the wrapped value, and it is invoked
> implicitly by string templates, by SLF4J's `{}` placeholder, and by
> exception and assertion messages. Wrapping a bearer token or an API key in
> a value class is a good instinct — it stops the raw string being passed
> where a user id belongs — but it does nothing for logging unless you also
> take the `toString` away. This is [§11.14](11-data-classes.md) applied to a
> single-component type; the logging discipline is
> [Chapter 31](31-logging.md). **Suggestion.**

```kotlin
// bad — the token reaches the log aggregator from a line containing no secret
@JvmInline
value class ApiToken(val value: String)

logger.info("calling billing with {}", token) // ApiToken(value=sk_live_9f3c…)

// good
@JvmInline
value class ApiToken(val value: String) {
    override fun toString(): String = "ApiToken(***)"
}
```

## 12.14 Give the value class the operators its domain actually has, and no others.

> Why? Without them, every arithmetic or comparison expression has to unwrap
> — and once `.value` appears on both sides of a `+`, the raw type is loose
> again in the surrounding code and the type safety you bought in §12.2 stops
> at the first calculation. Declaring `plus`, `times`, and `compareTo` on the
> wrapper keeps the raw value inside the type. The discipline is to add only
> the operations the domain has: adding two `Cents` is meaningful, adding two
> `UserId`s is not, and an operator that means nothing is worse than the
> unwrapping it replaced. Operator conventions in general are
> [Chapter 26](26-operators-and-conventions.md). **Suggestion.**

```kotlin
// bad — the raw Long escapes at every calculation
@JvmInline
value class Cents(val value: Long)

val total = Cents(lineA.value + lineB.value + shipping.value * 2)

// good — the meaningful operations live on the type
@JvmInline
value class Cents(val value: Long) : Comparable<Cents> {
    operator fun plus(other: Cents): Cents = Cents(value + other.value)

    operator fun times(quantity: Int): Cents = Cents(value * quantity)

    override fun compareTo(other: Cents): Int = value.compareTo(other.value)
}

val total = lineA + lineB + shipping * 2

// good — no operators, because none of them would mean anything
@JvmInline
value class UserId(val value: String)
```

## 12.15 Add a failable factory rather than making every parser call site catch.

> Why? An `init` block that calls `require` throws on invalid input, which is
> the right behaviour for a programming error and the wrong one for untrusted
> input — a malformed IBAN in a request body is an expected outcome, not a
> bug, and turning it into a 500 by way of an uncaught
> `IllegalArgumentException` is a design failure. Keep the `init` block as
> the invariant and add a companion factory that returns `null` or a
> `Result` for the parsing path, so the two audiences get the shape each one
> needs. See [Chapter 24](24-exceptions-and-result.md) for the
> exception-versus-`Result` decision. **Suggestion.**

```kotlin
// bad — every boundary that handles user input wraps this in try/catch
@JvmInline
value class Iban(val value: String) {
    init {
        require(value.matches(Regex("[A-Z]{2}\\d{2}[A-Z0-9]{11,30}"))) {
            "invalid IBAN: $value"
        }
    }
}

// good — the invariant stays, and untrusted input gets a total function
@JvmInline
value class Iban(val value: String) {
    init {
        require(value.matches(PATTERN)) { "invalid IBAN: $value" }
    }

    companion object {
        private val PATTERN = Regex("[A-Z]{2}\\d{2}[A-Z0-9]{11,30}")

        fun parseOrNull(raw: String): Iban? =
            if (raw.matches(PATTERN)) Iban(raw) else null
    }
}
```

## 12.16 Register an explicit converter before a value class crosses a Spring web binding boundary.

> Why? Spring binds `@PathVariable`, `@RequestParam`, `@RequestHeader`, and
> friends through its `ConversionService`, and a value class is not a type it
> knows. Worse, the binding path is exactly where the erasure in §12.11
> bites: Java reflection reports the handler parameter as the *underlying*
> type while Kotlin reflection reports the *wrapper*, and Spring has
> historically thrown `IllegalArgumentException: object is not an instance of
> declaring class` on that mismatch
> ([spring-framework#31698](https://github.com/spring-projects/spring-framework/issues/31698),
> [#27345](https://github.com/spring-projects/spring-framework/issues/27345)).
> Support has improved across recent versions, so the rule is not "never do
> it" — it is "register the converter, and cover the endpoint with a test
> before you rely on it". Details in
> [Chapter 44](44-spring-web-and-coroutines.md). **Suggestion.**

```kotlin
// bad — assuming the binding works because the underlying type is a String
@GetMapping("/users/{id}")
fun get(@PathVariable id: UserId): UserResponse = service.load(id)

// good — the conversion is declared, and a WebMvcTest covers the route
@Component
class UserIdConverter : Converter<String, UserId> {
    override fun convert(source: String): UserId = UserId(source)
}

@GetMapping("/users/{id}")
fun get(@PathVariable id: UserId): UserResponse = service.load(id)
```

## 12.17 Do not choose a value class for a concept that is about to grow a second field.

> Why? Adding a second component to a value class is not an edit — it is a
> change of construct, because "an inline class must have a single property
> initialized in the primary constructor". Every `.value` access, every
> `@JvmName`, and every place the erased type was relied upon has to move at
> once. Money without a currency, a timestamp without a zone, and a quantity
> without a unit are the three that reliably grow a second field within a
> year. If the concept plausibly has a second dimension, start with a `data
> class` — it costs one allocation and saves the migration. **Suggestion.**

```kotlin
// bad — correct until the first non-GBP customer, then a whole-codebase edit
@JvmInline
value class Money(val minorUnits: Long)

// good — the second dimension is present from the start
data class Money(val minorUnits: Long, val currency: Currency) {
    init {
        require(minorUnits >= 0) { "minorUnits must be >= 0, was $minorUnits" }
    }
}

// good — a value class is still right where the concept is genuinely
// one-dimensional
@JvmInline
value class Sku(val value: String)
```
