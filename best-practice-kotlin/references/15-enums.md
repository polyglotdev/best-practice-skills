<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 15. Enums

An enum class is a closed set of named singletons that all have the same shape.
That last clause is the whole design constraint: every constant carries the
same properties and answers the same methods, differing only in the values it
was constructed with. When that is true, an enum is the cheapest, clearest,
most tool-friendly type in the language. When it stops being true — when one
constant needs a field the others have no meaning for — you have outgrown the
enum and want a sealed hierarchy instead.

The upstream sources are the
[Kotlin enum classes documentation](https://kotlinlang.org/docs/enum-classes.html),
particularly
[working with enum constants](https://kotlinlang.org/docs/enum-classes.html#working-with-enum-constants),
[anonymous classes](https://kotlinlang.org/docs/enum-classes.html#anonymous-classes),
and
[implementing interfaces in enum classes](https://kotlinlang.org/docs/enum-classes.html#implementing-interfaces-in-enum-classes);
the
[Android Kotlin style guide on enum classes](https://developer.android.com/kotlin/style-guide#enum_classes)
and
[constant names](https://developer.android.com/kotlin/style-guide#constant_names);
and the Kotlin coding conventions'
[enumerations](https://kotlinlang.org/docs/coding-conventions.html#enumerations)
naming rule.

Three topics are deferred. **The enum-versus-sealed decision** is stated from
the sealed side in [Chapter 13, §13.5](13-sealed-types.md); §15.10 here states
it from the enum side, and the two rules are meant to be read together.
**`when` exhaustiveness in general** — subjects, guard conditions, formatting —
is [Chapter 22](22-control-flow-and-when.md). **Spring configuration binding
and request binding** are Chapters [43](43-spring-configuration-properties.md)
and [44](44-spring-web-and-coroutines.md); §15.17 covers only the enum-specific
part.

**Tool alignment:** several rules below are mechanically enforced. ktlint's
`standard:enum-entry-name-case` and detekt's `EnumNaming` (`naming`, active by
default) constrain constant names — note that both accept `UPPER_SNAKE_CASE`
*and* `UpperCamelCase`, so §15.14 is about picking one, not about the linter
choosing for you. detekt's `ElseCaseInsteadOfExhaustiveWhen` (`potential-bugs`)
catches §15.8 — but it is **off by default** and requires type resolution, so
you have to enable it — and `SwallowedException` (`exceptions`, active by
default) catches the `valueOf`-in-a-`try` anti-pattern in §15.6. Rules no tool
can check are labeled **Suggestion**.

## 15.1 Give each constant its data as constructor properties, not as a `when` in a function somewhere else.

> Why? A `when` that maps constants to values lives apart from the constants
> themselves, so adding a constant means editing two places — and the compiler
> only reminds you about the second one if the `when` happens to be an
> exhaustive expression. Constructor properties put the data on the constant,
> where a reader looking at `MERCURY` can see everything `MERCURY` is. The
> [enum classes documentation](https://kotlinlang.org/docs/enum-classes.html)
> shows exactly this shape. **Suggestion.**

```kotlin
// bad — the data lives in a function far from the constants
enum class Planet { MERCURY, VENUS, EARTH }

fun massKg(planet: Planet): Double = when (planet) {
    Planet.MERCURY -> 3.303e23
    Planet.VENUS -> 4.869e24
    Planet.EARTH -> 5.976e24
}

fun radiusM(planet: Planet): Double = when (planet) {
    Planet.MERCURY -> 2.4397e6
    Planet.VENUS -> 6.0518e6
    Planet.EARTH -> 6.37814e6
}

// good — one place to look, one place to edit
enum class Planet(val massKg: Double, val radiusM: Double) {
    MERCURY(3.303e23, 2.4397e6),
    VENUS(4.869e24, 6.0518e6),
    EARTH(5.976e24, 6.37814e6),
    ;

    val surfaceGravity: Double get() = GRAVITATIONAL_CONSTANT * massKg / (radiusM * radiusM)
}
```

## 15.2 When behaviour genuinely varies per constant and is intrinsic to it, declare an abstract member and override it on each constant.

> Why? The
> [anonymous classes](https://kotlinlang.org/docs/enum-classes.html#anonymous-classes)
> section of the enum documentation exists for this: "Enum constants can
> declare their own anonymous classes with their corresponding methods, as well
> as with overriding base methods." The payoff is that adding a constant
> without supplying the behaviour is a compile error at the constant, rather
> than a missing branch in a `when` you have to remember exists. Reserve this
> for behaviour that belongs to the constant — the same layering rule as
> [Chapter 13, §13.16](13-sealed-types.md) applies, so an enum in the domain
> module should not grow a method that needs the web framework. **Suggestion.**

```kotlin
// bad — the behaviour is intrinsic but lives outside; adding MODULO compiles
// everywhere until this one when is found
enum class Operation { PLUS, MINUS, TIMES }

fun apply(operation: Operation, x: Double, y: Double): Double = when (operation) {
    Operation.PLUS -> x + y
    Operation.MINUS -> x - y
    Operation.TIMES -> x * y
}

// good — adding MODULO without an apply() body does not compile
enum class Operation(val symbol: String) {
    PLUS("+") {
        override fun apply(x: Double, y: Double): Double = x + y
    },
    MINUS("-") {
        override fun apply(x: Double, y: Double): Double = x - y
    },
    TIMES("*") {
        override fun apply(x: Double, y: Double): Double = x * y
    },
    ;

    abstract fun apply(x: Double, y: Double): Double
}
```

## 15.3 Format the enum to the style guide: one line when it has no member declarations, and a semicolon separating constants from members.

> Why? The
> [Android Kotlin style guide on enum classes](https://developer.android.com/kotlin/style-guide#enum_classes)
> is specific: "An enum with no functions and no documentation on its constants
> may optionally be formatted as a single line," and "When the constants in an
> enum are placed on separate lines, a blank line is not required between them
> except in the case where they define a body." The enum documentation adds the
> separator rule: when the enum declares members, "separate the constant
> definitions from the member definitions with a semicolon." A trailing comma
> before that semicolon keeps future diffs to one line.
> **Suggestion** — ktlint owns the mechanical formatting; this rule is about
> the shape you write in the first place.

```kotlin
// bad — four lines for a bare enum, and no semicolon separating the members
enum class Answer {
    YES,
    NO,
    MAYBE
}

enum class Suit(val color: CardColor) {
    HEARTS(CardColor.RED),
    SPADES(CardColor.BLACK)
    val isRed: Boolean get() = color == CardColor.RED
}

// good
enum class Answer { YES, NO, MAYBE }

enum class Suit(val color: CardColor) {
    HEARTS(CardColor.RED),
    SPADES(CardColor.BLACK),
    ;

    val isRed: Boolean get() = color == CardColor.RED
}
```

## 15.4 Use `entries`; do not call `values()`.

> Why? `values()` is a synthetic function that returns a **fresh array copy on
> every call**, so iterating it in a hot path allocates once per iteration and
> hands the caller a mutable array it could modify. `entries`, added in Kotlin
> 1.9.0, returns a cached, unmodifiable `List` — the KEEP's generated bytecode
> shows `values()` as literally `return $VALUES.clone()`. The
> [enum entries KEEP](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0283-enum-entries.md)
> is explicit that `values()` is being retired without a formal deprecation
> cycle: it "will be softly decommissioned with the help of IDE assistance",
> because a hard deprecation of something that has existed since Kotlin 1.0
> would churn the whole ecosystem. Being soft-deprecated means no compiler
> error will ever tell you — you have to apply this rule yourself.
> **Suggestion.**

```kotlin
// bad — a new array on every call, and a mutable one at that
fun allNames(): List<String> = Status.values().map { it.name }

fun isTerminal(status: Status): Boolean = Status.values().last() == status

// good — cached, unmodifiable List<Status>
fun allNames(): List<String> = Status.entries.map { it.name }

fun isTerminal(status: Status): Boolean = Status.entries.last() == status
```

## 15.5 In a reified generic, use `enumEntries<T>()` rather than `enumValues<T>()`.

> Why? Same reason, one level up. The
> [enum classes documentation](https://kotlinlang.org/docs/enum-classes.html#working-with-enum-constants)
> states the difference directly: `enumEntries<T>()` "returns the same list
> each time", while "the `enumValues<T>()` function is still supported, but we
> recommend that you use the `enumEntries<T>()` function instead because it has
> less performance impact. Every time you call `enumValues<T>()` a new array is
> created." `enumEntries` has been stable since Kotlin 2.0. **Suggestion.**

```kotlin
// bad — a fresh array per call, inside a function designed to be called often
inline fun <reified T : Enum<T>> parseOrNull(name: String): T? =
    enumValues<T>().firstOrNull { it.name == name }

// good
inline fun <reified T : Enum<T>> parseOrNull(name: String): T? =
    enumEntries<T>().firstOrNull { it.name == name }
```

## 15.6 Never let `valueOf` see untrusted input, and never catch `IllegalArgumentException` to control flow.

> Why? `valueOf` "throws an `IllegalArgumentException` if the specified name
> does not match any of the enum constants defined in the class", per the
> [enum classes documentation](https://kotlinlang.org/docs/enum-classes.html#working-with-enum-constants).
> Wrapping it in a `try`/`catch` to get a null back turns an expected outcome —
> a client sent a value you do not recognise — into an exception construction
> with a stack trace capture, on a path that may be hot, and it swallows an
> exception without inspecting it. Provide a total function that returns null
> and let the caller decide. **Violation — enforced by
> `detekt/SwallowedException`** for the discarded `IllegalArgumentException`;
> the `valueOf` call itself is a **Suggestion**.

```kotlin
// bad — exception-driven control flow, and the exception is thrown away
fun parseStatus(raw: String): Status? = try {
    Status.valueOf(raw)
} catch (e: IllegalArgumentException) {
    null
}

// good — a total function; nothing is thrown on the expected path
fun parseStatus(raw: String): Status? = Status.entries.firstOrNull { it.name == raw }
```

## 15.7 Build the name-to-constant lookup once, in the companion object.

> Why? §15.6's `firstOrNull` scan is fine for five constants on a cold path and
> wrong for fifty on a hot one — it is a linear scan plus a string comparison
> per entry, every call. Building an immutable map once in the companion object
> makes the lookup a single hash. Doing it in the companion also keeps the
> lookup beside the constants it indexes, so a new constant joins the map for
> free. **Suggestion.**

```kotlin
// bad — a linear scan on every inbound request, and the wire vocabulary is
// silently assumed to equal the constant names
enum class Status { ACTIVE, SUSPENDED, CLOSED }

fun parseStatus(raw: String): Status? =
    Status.entries.firstOrNull { it.name.equals(raw, ignoreCase = true) }

// good — one hash lookup, and the wire vocabulary is explicit
enum class Status(val wireValue: String) {
    ACTIVE("active"),
    SUSPENDED("suspended"),
    CLOSED("closed"),
    ;

    companion object {
        private val BY_WIRE_VALUE: Map<String, Status> =
            Status.entries.associateBy(Status::wireValue)

        fun fromWireValue(value: String): Status? = BY_WIRE_VALUE[value.lowercase()]
    }
}
```

## 15.8 Write `when` over an enum exhaustively, with no `else`.

> Why? Identical reasoning to
> [Chapter 13, §13.6](13-sealed-types.md), and the
> [`when` documentation](https://kotlinlang.org/docs/control-flow.html#when-expressions-and-statements)
> grants enums the same privilege as sealed types: "If your subject is a
> `Boolean`, `enum` class, `sealed` class, or one of their nullable
> counterparts, you can cover all cases without an `else` branch." An `else`
> converts "the compiler will show me every place a new constant must be
> handled" into "the new constant silently behaves like the default", which is
> the exact failure enums exist to prevent. Qualify every branch
> (`Status.ACTIVE`, not bare `ACTIVE`): dropping the type name in a `when` over
> an enum is *context-sensitive resolution*, which is still **Experimental in
> Kotlin 2.4** and needs `-Xcontext-sensitive-resolution`.
> **Violation — enforced by `detekt/ElseCaseInsteadOfExhaustiveWhen`**, which
> is off by default and requires type resolution, so enable it explicitly.

```kotlin
// bad — adding Status.PENDING routes silently to else
fun badgeColour(status: Status): Colour = when (status) {
    Status.ACTIVE -> Colour.GREEN
    Status.SUSPENDED -> Colour.AMBER
    else -> Colour.GREY
}

// good — adding Status.PENDING is a compile error here
fun badgeColour(status: Status): Colour = when (status) {
    Status.ACTIVE -> Colour.GREEN
    Status.SUSPENDED -> Colour.AMBER
    Status.CLOSED -> Colour.GREY
}
```

## 15.9 Have the enum implement the interface its constants plug into.

> Why? Enums can implement interfaces — the
> [implementing interfaces in enum classes](https://kotlinlang.org/docs/enum-classes.html#implementing-interfaces-in-enum-classes)
> section covers both the "implement it once for the whole enum" and "implement
> it per constant" forms. When you already have an abstraction like
> `Comparator`, `Predicate`, or your own `RetryPolicy`, letting the constants
> *be* instances of it means callers accept the interface and never learn the
> enum exists, which keeps the enum out of every signature that only needs the
> behaviour. **Suggestion.**

```kotlin
// bad — callers must take the enum and translate it themselves
enum class Backoff { NONE, LINEAR, EXPONENTIAL }

fun delayFor(backoff: Backoff, attempt: Int): Duration = when (backoff) {
    Backoff.NONE -> Duration.ZERO
    Backoff.LINEAR -> Duration.ofMillis(100L * attempt)
    Backoff.EXPONENTIAL -> Duration.ofMillis(100L shl attempt)
}

fun upload(blob: Blob, backoff: Backoff) { /* calls delayFor */ }

// good — the constants are the abstraction; upload never mentions the enum
fun interface BackoffStrategy {
    fun delayFor(attempt: Int): Duration
}

enum class Backoff : BackoffStrategy {
    NONE {
        override fun delayFor(attempt: Int): Duration = Duration.ZERO
    },
    LINEAR {
        override fun delayFor(attempt: Int): Duration = Duration.ofMillis(100L * attempt)
    },
    EXPONENTIAL {
        override fun delayFor(attempt: Int): Duration = Duration.ofMillis(100L shl attempt)
    },
}

fun upload(blob: Blob, backoff: BackoffStrategy) { /* ... */ }
```

## 15.10 Decide enum versus sealed type explicitly, on whether every variant has the same shape.

> Why? The two are not interchangeable and the choice is not a matter of
> taste. An enum is right when the constants are a fixed vocabulary that all
> answer the same questions — `Weekday`, `LogLevel`, `HttpMethod` — because you
> get a compile-time-known instance per name, free `entries`, free `EnumSet`
> and `EnumMap`, free `Comparable`, and a name that serializes trivially. A
> sealed hierarchy is right when the variants carry different payloads; see
> [Chapter 13, §13.5](13-sealed-types.md) for the same rule stated from that
> side. The failure mode is an enum growing nullable properties that only some
> constants use. **Suggestion.**

```kotlin
// bad — an enum stretched past its shape; three of the four properties are
// null for most constants, and nothing stops you reading the wrong one
enum class Notification(
    val emailSubject: String?,
    val smsBody: String?,
    val webhookUrl: String?,
) {
    EMAIL_WELCOME("Welcome", null, null),
    SMS_OTP(null, "Your code is %s", null),
    WEBHOOK_ORDER_SHIPPED(null, null, "https://example.test/hooks/shipped"),
}

// good — a sealed hierarchy for variants with different payloads
sealed interface Notification {
    data class Email(val subject: String, val body: String) : Notification
    data class Sms(val body: String) : Notification
    data class Webhook(val url: String) : Notification
}

// good — an enum for a uniform vocabulary
enum class Channel { EMAIL, SMS, WEBHOOK }
```

## 15.11 Never persist or transmit `ordinal`.

> Why? `ordinal` is the constant's position in the source file. It is not part
> of the type's meaning, nobody reviewing a reordering diff thinks about it,
> and once it is in a database column or a wire payload, an alphabetical sort
> of the constant list silently rewrites the meaning of every row already
> stored. Persist the `name`, or better, an explicit code property you control
> independently of declaration order (§15.7). On JPA entities that means
> `@Enumerated(EnumType.STRING)`, never the `ORDINAL` default — and spell the
> use-site target explicitly, per
> [Chapter 27](27-annotations-and-use-site-targets.md), so there is no doubt
> the annotation landed on the field. **Suggestion.**

```kotlin
// bad — the column holds 0/1/2, and EnumType.ORDINAL is the JPA default, so
// omitting the annotation entirely is the same bug
@Entity
class Subscription(
    @field:Enumerated(EnumType.ORDINAL)
    val status: Status,
)

fun toWire(status: Status): Int = status.ordinal

// good — an explicit, stable code that reordering cannot touch
enum class Status(val code: String) {
    ACTIVE("A"),
    SUSPENDED("S"),
    CLOSED("C"),
}

@Entity
class Subscription(
    @field:Enumerated(EnumType.STRING)
    val status: Status,
)

fun toWire(status: Status): String = status.code
```

## 15.12 Treat the constant list of a persisted enum as a schema: append, never reorder, never delete.

> Why? Once a constant's `name` or code is in a database or a message that
> outlives the deploy, the enum is a published data contract. Deleting a
> constant means old rows deserialize to nothing — `valueOf` throws and
> `fromWireValue` returns null on data you wrote yourself. Reordering is
> harmless *only* if §15.11 was followed; if anything ever persisted `ordinal`,
> reordering is silent data corruption. Renaming is deletion plus addition.
> Every one of these is a migration, not a refactor. **Suggestion.**

```kotlin
// bad — a "cleanup" commit that alphabetises the constants and drops one that
// "nothing uses any more"; every persisted TRIALING row is now unreadable
enum class Status(val code: String) {
    ACTIVE("A"),
    CLOSED("C"),
    SUSPENDED("S"),
}

// good — append only, and retire a constant by marking it rather than removing
// it until the backfill has run
enum class Status(val code: String, val isAcceptedForNewRecords: Boolean = true) {
    ACTIVE("A"),
    SUSPENDED("S"),
    CLOSED("C"),
    TRIALING("T", isAcceptedForNewRecords = false), // retired 2026-05; backfill pending
    PAUSED("P"),
}
```

## 15.13 Use `java.util.EnumSet` and `java.util.EnumMap` for enum-keyed sets and maps.

> Why? `EnumSet` is a bit vector and `EnumMap` is an array indexed by
> `ordinal`, so both are dramatically smaller and faster than the hash-based
> defaults, and both iterate in declaration order rather than hash order.
> Kotlin's standard library ships no equivalent and no `enumSetOf` helper — on
> the JVM you use the `java.util` types directly. Note that both are *mutable*
> implementations, so declare the property with the read-only `Set`/`Map` type
> and never hand the `EnumSet` itself to a caller; see
> [Chapter 25](25-immutability.md). **Suggestion.**

```kotlin
// bad — a hash set of enums: boxing into buckets, hash-order iteration
val weekend: Set<Weekday> = hashSetOf(Weekday.SATURDAY, Weekday.SUNDAY)
val hoursWorked: MutableMap<Weekday, Int> = HashMap()

// good — bit vector and ordinal-indexed array, both in declaration order
val weekend: Set<Weekday> = EnumSet.of(Weekday.SATURDAY, Weekday.SUNDAY)
val hoursWorked: MutableMap<Weekday, Int> = EnumMap(Weekday::class.java)

// good — when the set is a compile-time constant and never mutated, the plain
// stdlib factory is still fine and is genuinely immutable
val weekendDays: Set<Weekday> = setOf(Weekday.SATURDAY, Weekday.SUNDAY)
```

## 15.14 Pick one enum-constant naming style for the codebase and hold it.

> Why? The two upstream guides differ, deliberately. The Kotlin coding
> conventions'
> [enumerations](https://kotlinlang.org/docs/coding-conventions.html#enumerations)
> rule says "it's OK to use either all uppercase, underscore-separated
> (screaming snake case) names ... or upper camel case names, depending on the
> usage." The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#constant_names)
> is stricter: "Constant names use UPPER_SNAKE_CASE." Both ktlint's
> `standard:enum-entry-name-case` and detekt's `EnumNaming` accept either form,
> so no tool will make the decision for you. Mixing the two inside one codebase
> means every reader has to check which convention this particular enum picked.
> Default to `UPPER_SNAKE_CASE` — it is the stricter of the two guides and it
> matches the constant-naming rule the rest of the codebase already follows.
> **Suggestion** — the linters constrain the *form*, not the consistency.

```kotlin
// bad — three conventions in one file
enum class LogLevel { Debug, INFO, warn, ERROR_FATAL }

// good — one convention, applied everywhere
enum class LogLevel { DEBUG, INFO, WARN, ERROR_FATAL }
```

## 15.15 Do not give an enum mutable state.

> Why? Every enum constant is a process-wide singleton, so a `var` on the enum
> is global mutable state with the extra indignity that it looks like a
> constant. One request mutating `Status.ACTIVE.lastSeenAt` changes what every
> other request observes, no test can reset it, and the field is racy unless
> you synchronised it by hand. This is the same rule as
> [Chapter 14, §14.16](14-objects-and-companions.md); enums just make it
> easier to violate by accident because `enum class` reads as a constant
> declaration. **Suggestion.**

```kotlin
// bad — a global counter disguised as an enum property
enum class Endpoint(val path: String) {
    HEALTH("/health"),
    METRICS("/metrics"),
    ;

    var hitCount: Long = 0

    fun record() {
        hitCount++
    }
}

// good — the enum stays a value; the mutable count lives in an owned collaborator
enum class Endpoint(val path: String) {
    HEALTH("/health"),
    METRICS("/metrics"),
}

class EndpointCounters {
    private val hits: MutableMap<Endpoint, LongAdder> =
        EnumMap<Endpoint, LongAdder>(Endpoint::class.java)
            .apply { Endpoint.entries.forEach { put(it, LongAdder()) } }

    fun record(endpoint: Endpoint) {
        hits.getValue(endpoint).increment()
    }
}
```

## 15.16 Do not add a catch-all `UNKNOWN` constant unless the wire format genuinely has one.

> Why? An `UNKNOWN` added "for safety" is a case that never legitimately
> occurs, and every exhaustive `when` in the codebase now has a branch for it
> that the author had to invent behaviour for. Worse, it turns a
> deserialization failure into a valid-looking value that flows deep into the
> system before anything notices. If the source is closed — your own database,
> your own enum — reject unknown input at the boundary and let it be an error.
> If the source is genuinely open — a third-party API that adds values without
> telling you — the honest model is a sealed hierarchy with an `Unknown(raw)`
> variant that keeps the original string, not an enum constant that discards
> it. **Suggestion.**

```kotlin
// bad — UNKNOWN is unreachable from any correct input, discards the raw value,
// and forces a meaningless branch into every when
enum class Currency { USD, EUR, GBP, UNKNOWN }

fun parseCurrency(raw: String): Currency =
    Currency.entries.firstOrNull { it.name == raw } ?: Currency.UNKNOWN

// good — closed vocabulary: unknown input is an error at the boundary
enum class Currency { USD, EUR, GBP }

fun parseCurrency(raw: String): Currency =
    requireNotNull(Currency.entries.firstOrNull { it.name == raw }) {
        "unsupported currency '$raw'"
    }

// good — genuinely open vocabulary: keep the raw value, do not invent a constant
sealed interface ProviderEvent {
    data object Captured : ProviderEvent
    data object Refunded : ProviderEvent
    data class Unrecognised(val raw: String) : ProviderEvent
}
```

## 15.17 Bind Spring configuration and request parameters to enums deliberately, and keep the wire vocabulary separate from the constant names.

> Why? Spring Boot's relaxed binding matches configuration values to enum
> constants by name, case-insensitively and ignoring separators, which is
> convenient but means **your constant names are part of your configuration
> contract** — renaming one breaks every deployment's `application.yaml`
> silently until start-up. For inbound HTTP, binding a request parameter
> straight to an enum leaves the framework to produce the error when a client
> sends an unknown value, so you get its message and its status code rather
> than yours. Bind the raw `String` and map it through the lookup from §15.7
> when the wire vocabulary is not identical to the constant names. See
> [Chapter 43](43-spring-configuration-properties.md) for configuration binding
> and [Chapter 44](44-spring-web-and-coroutines.md) for the web layer.
> **Suggestion.**

```kotlin
// bad — the client-facing vocabulary is welded to the constant names, and an
// unknown value produces whatever the framework decides to say
@RestController
class SubscriptionController(private val service: SubscriptionService) {
    @GetMapping("/subscriptions")
    fun list(@RequestParam status: Status): List<SubscriptionResponse> =
        service.byStatus(status)
}

// good — the wire vocabulary is explicit and the error message is yours
@RestController
class SubscriptionController(private val service: SubscriptionService) {
    @GetMapping("/subscriptions")
    fun list(@RequestParam status: String): List<SubscriptionResponse> {
        val accepted = Status.entries.map(Status::wireValue)
        val parsed = Status.fromWireValue(status)
            ?: throw ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                "unknown status '$status'; expected one of $accepted",
            )
        return service.byStatus(parsed)
    }
}

// good — configuration binding is fine as long as you treat the constant names
// as published contract and never rename them casually
@ConfigurationProperties("billing")
data class BillingProperties(val defaultCurrency: Currency, val retryBackoff: Backoff)
```
