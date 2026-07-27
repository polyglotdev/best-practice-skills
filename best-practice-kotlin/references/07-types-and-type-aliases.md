<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 7. Types & Type Aliases

Kotlin's type system is richer than the JVM it compiles to, and most of that
richness is a style tool: `Nothing` lets the compiler prove a branch is
unreachable, `Unit` lets a function say it produces nothing without saying
`void`, `as?` turns a crash into a value, `reified` recovers a type argument
erasure would have thrown away, and a type alias renames a signature without
inventing a type. This chapter is about using each of those for what it is,
and — just as often — about not reaching for one when a different construct
carries more meaning.

It draws on the language reference for
[type checks and casts](https://kotlinlang.org/docs/typecasts.html),
[generics](https://kotlinlang.org/docs/generics.html) (including
[star-projections](https://kotlinlang.org/docs/generics.html#star-projections),
[type erasure](https://kotlinlang.org/docs/generics.html#type-erasure), and
[definitely non-nullable types](https://kotlinlang.org/docs/generics.html#definitely-non-nullable-types)),
[numbers](https://kotlinlang.org/docs/numbers.html), and
[type aliases](https://kotlinlang.org/docs/type-aliases.html), plus the
coding conventions on
[type aliases](https://kotlinlang.org/docs/coding-conventions.html#type-aliases),
[the `Unit` return type](https://kotlinlang.org/docs/coding-conventions.html#unit-return-type),
and [type arguments](https://kotlinlang.org/docs/coding-conventions.html#type-arguments).

Three neighbouring topics are deferred. Declaration-site and use-site
**variance**, type-parameter bounds, and generic API design are
[Chapter 18, Generics & Variance](18-generics-and-variance.md); §7.12 covers
only the star projection you reach for when you have no type argument at all.
Giving a primitive a distinct domain type is
[Chapter 12, Value Classes](12-value-classes.md), which §7.14 defers to
directly. The nullability half of casts and platform types is
[Chapter 6, Null Safety](06-null-safety.md).

**Tool alignment:** `detekt/SafeCast`,
`detekt/CastNullableToNonNullableType`, `detekt/CastToNullableType`,
`detekt/DontDowncastCollectionTypes`, and `detekt/ImplicitUnitReturnType`
enforce §7.2 and §7.8 to §7.10 mechanically. `detekt/UnsafeCast` covers only
the sliver of §7.7 it can prove impossible. Rules a named check enforces are
marked **Violation**; the rest are **Suggestion**.

## 7.1 Use `Any` only when you genuinely mean "any object"; reach for a type parameter or a sealed type instead.

> Why? `Any` is the root of Kotlin's non-null hierarchy (`Any?` is the true
> top type), so a parameter or return of type `Any` tells the caller nothing
> and forces a cast at the first use — reintroducing exactly the runtime
> failure Kotlin's type system exists to prevent. Nearly every `Any` in
> application code is one of three things wearing a disguise: a generic
> function that has not been made generic, a closed set of alternatives that
> wants a [sealed interface](13-sealed-types.md), or an open extension point
> that wants an interface. The legitimate uses are narrow: a logging or
> serialization sink, `equals(other: Any?)`, and a heterogeneous payload you
> immediately hand to a library.
> **Suggestion.**

```kotlin
// bad — the caller loses the type, and every consumer casts it back
fun firstOrDefault(values: List<Any>, fallback: Any): Any =
    values.firstOrNull() ?: fallback

val name = firstOrDefault(names, "unknown") as String

// good — generic; the type survives the call
fun <T> firstOrDefault(values: List<T>, fallback: T): T =
    values.firstOrNull() ?: fallback

val name = firstOrDefault(names, "unknown")

// bad — `Any` standing in for a closed set of outcomes
fun parse(raw: String): Any = if (raw.isBlank()) ParseError.Empty else Token(raw)

// good — a sealed hierarchy the compiler can check exhaustively
sealed interface ParseResult {
    data class Success(val token: Token) : ParseResult
    data object Empty : ParseResult
}

fun parse(raw: String): ParseResult =
    if (raw.isBlank()) ParseResult.Empty else ParseResult.Success(Token(raw))
```

## 7.2 Omit `: Unit` from a block-bodied function, and never give a function an expression body whose value is `Unit`.

> Why? Two halves of the same idea. The
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#unit-return-type)
> say a `Unit`-returning function should simply omit the return type — writing
> `: Unit` is the Kotlin equivalent of writing `: void`, adding a word that
> carries no information. The second half is the trap: `fun log(m: String) =
> logger.info(m)` is an *expression* body whose inferred type happens to be
> `Unit`. It compiles, but the signature now says "this returns whatever
> `logger.info` returns", so the day `info` starts returning a value, this
> function's public type changes silently. Use a block body for anything
> performed for its effect.
> **Violation — enforced by `detekt/ImplicitUnitReturnType`** for the
> expression-body half; **Suggestion** for the explicit `: Unit`.

```kotlin
// bad — redundant `: Unit`, and an expression body used for a side effect
fun record(event: Event): Unit {
    audit.write(event)
}

fun log(message: String) = logger.info(message)

// good
fun record(event: Event) {
    audit.write(event)
}

fun log(message: String) {
    logger.info(message)
}
```

## 7.3 Give a function that never returns normally the return type `Nothing`.

> Why? `Nothing` is "a built-in type that is a subtype of all other types,
> also known as the bottom type", used "to represent functions or expressions
> that never complete successfully, either because they always throw an
> exception or enter an endless execution path like an infinite loop." That
> subtyping is what makes it useful in *style* rather than theory: because
> `Nothing` fits everywhere, a `Nothing`-returning helper can sit on the right
> of an Elvis operator, in a `when` branch, or as the initializer of a `val`
> and the compiler will still consider the surrounding value definitely
> assigned and the code below unreachable. Declare the helper `: Nothing` and
> you get that for free; declare it `: Unit` and every call site needs an
> extra `return` or `throw` to convince the compiler.
> **Suggestion.**

```kotlin
// bad — `fail` returns Unit, so the Elvis expression's type is the common
// supertype of String and Unit (Any) and will not fit a String declaration
fun fail(message: String) {
    throw IllegalArgumentException(message)
}

fun greet(person: Person) {
    val name: String = person.name ?: fail("name required") // does not compile
    println(name)
}

// good — `Nothing` is a subtype of String, so the Elvis branch type-checks
// and `name` is definitely assigned below
fun fail(message: String): Nothing {
    throw IllegalArgumentException(message)
}

fun greet(person: Person) {
    val name: String = person.name ?: fail("name required")
    println(name)
}
```

## 7.4 Let `Nothing` type your genuinely empty and impossible values instead of a cast or a nullable.

> Why? Because `Nothing` has no instances and is a subtype of everything,
> `List<Nothing>` is assignable to `List<T>` for any `T`, and `Nothing?` has
> exactly one value: `null`. That is what lets `emptyList()` be shared across
> every element type without a cast, and it is the clean way to give a sealed
> hierarchy's "no value" case a type argument that fits every instantiation.
> Reaching for an unchecked cast or a nullable field to achieve the same
> thing throws away a guarantee the type system was offering for free. The
> stdlib's own `TODO()` is declared `: Nothing` for the same reason.
> **Suggestion.**

```kotlin
// bad — an unchecked cast to make the empty case fit every element type
sealed class Loaded<T> {
    class Ready<T>(val value: T) : Loaded<T>()
    class Missing<T> : Loaded<T>()
}

@Suppress("UNCHECKED_CAST")
fun <T> missing(): Loaded<T> = Loaded.Missing<Any?>() as Loaded<T>

// good — a single `Missing` object, typed with Nothing, fits every T
sealed interface Loaded<out T> {
    data class Ready<T>(val value: T) : Loaded<T>
    data object Missing : Loaded<Nothing>
}

fun <T> missing(): Loaded<T> = Loaded.Missing
```

## 7.5 There is no implicit numeric widening in Kotlin — convert explicitly, and pick the right type at the declaration instead.

> Why? "Numeric types are not subtypes of one another. Kotlin requires
> explicit conversions to avoid silent data loss and unexpected behavior."
> An `Int` is not accepted where a `Double` is expected, even though every
> `Int` fits. Kotlin *does* widen inside an arithmetic expression
> (`intValue + longValue` is a `Long`), but not on assignment or argument
> passing. The upshot for style: a trail of `.toLong()` / `.toDouble()` calls
> is almost always the symptom of a declaration typed wrongly upstream, not
> something to fix at each call. Fix the declaration.
> **Suggestion.**

```kotlin
// bad — the declaration is Int, so every downstream use converts
val timeoutMillis = 30_000

fun schedule(delayMillis: Long, ratio: Double) { /* ... */ }

schedule(timeoutMillis.toLong(), retries.toDouble() / attempts.toDouble())

// good — declare the type you actually need
val timeoutMillis: Long = 30_000

schedule(timeoutMillis, ratio = retries.toDouble() / attempts)
```

## 7.6 Write a numeric literal in its target type rather than converting after the fact.

> Why? `1L`, `1.0`, `1.0f`, `1u`, `0xFF`, and `0b0001` all produce the type
> directly, and underscores (`1_000_000`) make magnitude readable at a
> glance. `1.toLong()` produces the same value with an extra call and an
> extra thing for the reader to check. The literal form also makes an
> accidental integer division impossible to miss: `1 / 2` is `0`, `1.0 / 2`
> is `0.5`, and the difference is one character you can see.
> **Suggestion.**

```kotlin
// bad — conversions where a literal suffix would do, and a silent integer
// division
val backoff = 2.toLong()
val budget = 5000000.toLong()
val ratio = completed / total // Int / Int == Int

// good
val backoff = 2L
val budget = 5_000_000L
val ratio = completed.toDouble() / total
```

## 7.7 Prefer an `is` check and the smart cast it produces to an explicit `as`.

> Why? `is` and `as` express the same intent, but only one of them lets the
> compiler carry the knowledge forward. After `if (value is Invoice)`, `value`
> *is* an `Invoice` for the rest of the branch with no further syntax; `as`
> produces a new binding whose correctness nobody checked. `as` also throws
> `ClassCastException` on failure — "throws `ClassCastException` at runtime if
> the cast fails" — with no context beyond the two class names. Reserve `as`
> for the case where failure genuinely cannot happen and you have no
> `is`-shaped place to put the check. See
> [§6.8](06-null-safety.md) for the cases where smart casting is unavailable.
> **Suggestion** — `detekt/UnsafeCast` "reports casts that will never
> succeed", so it catches only the subset the compiler can prove impossible
> (`s as Int` where `s: String`), not the far more common downcast that
> merely *might* fail.

```kotlin
// bad — an unchecked cast, and a ClassCastException if the assumption is
// wrong
fun total(document: Document): Money {
    val invoice = document as Invoice
    return invoice.total
}

// good — `is` checks and smart-casts in one step
fun total(document: Document): Money? =
    if (document is Invoice) document.total else null

// good — as a `when`, which smart-casts in each branch
fun total(document: Document): Money = when (document) {
    is Invoice -> document.total
    is CreditNote -> -document.amount
    else -> Money.ZERO
}
```

## 7.8 When a cast can fail, use `as?` with an Elvis fallback — never `as` inside a `try`.

> Why? `as?` "returns `null` if the cast fails instead of throwing an
> exception", which turns a control-flow decision into a value you can hand
> straight to `?:`. Wrapping `as` in `try { } catch (e: ClassCastException)`
> achieves the same thing in six lines, costs an exception construction on
> the failing path, and will happily swallow a `ClassCastException` thrown by
> something *else* inside the block. It also catches the cast in the wrong
> place: a broad `catch` around a cast is one of the classic ways a
> `CancellationException` gets swallowed in coroutine code (see
> [Chapter 35](35-cancellation-and-timeouts.md)).
> **Violation — enforced by `detekt/SafeCast`,** which reports the
> `if (x is T) x else null` form the same rule covers.

```kotlin
// bad — exception-driven control flow around a cast
fun asInvoice(document: Document): Invoice? =
    try {
        document as Invoice
    } catch (e: ClassCastException) {
        null
    }

// bad — the long form of `as?`
fun asInvoice(document: Document): Invoice? =
    if (document is Invoice) document else null

// good
fun asInvoice(document: Document): Invoice? = document as? Invoice

// good — with the fallback at the point of use
val total = (document as? Invoice)?.total ?: Money.ZERO
```

## 7.9 Never launder nullability through a cast: `as` on a nullable value is an NPE wearing a cast's clothes.

> Why? `value as String` where `value` is `String?` compiles, and throws
> `NullPointerException` — not `ClassCastException` — when the value is
> `null`. It is `!!` in disguise, with the same absent message and none of
> `!!`'s visual warning (see [§6.1](06-null-safety.md)). The mirror-image
> mistake, `value as? String?`, is also wrong for a different reason: the
> nullable target type makes the safe cast unable to fail, so it silently
> returns `null` for *both* "wrong type" and "was null", collapsing two
> distinct outcomes into one.
> **Violation — enforced by `detekt/CastNullableToNonNullableType` and
> `detekt/CastToNullableType`.**

```kotlin
// bad — NullPointerException when `raw` is null, from an expression that
// looks like a type check
val id: String = raw as String

// bad — `as? String?` can never fail, so the two failure modes merge
val id: String? = raw as? String?

// good — the cast and the absence are handled separately
val id: String = raw as? String ?: error("expected a String id, got $raw")

// good — when absence is a legitimate outcome
val id: String? = raw as? String
```

## 7.10 Never downcast a read-only collection interface to its mutable counterpart.

> Why? `List<T>` and `MutableList<T>` are distinct Kotlin types that erase to
> the same `java.util.List`, so `list as MutableList<T>` compiles with only
> an unchecked-cast warning and then either mutates a collection its owner
> believed was frozen or throws `UnsupportedOperationException` at runtime if
> the underlying instance is genuinely immutable. Both outcomes are worse
> than the alternative, which is one line: `toMutableList()` makes a copy you
> own. If the copy is too expensive, the API should have returned a mutable
> type in the first place.
> **Violation — enforced by `detekt/DontDowncastCollectionTypes`.**

```kotlin
// bad — mutates through a read-only view, or throws, depending on what the
// caller actually passed
fun appendAudit(entries: List<Entry>, entry: Entry) {
    (entries as MutableList<Entry>).add(entry)
}

// good — copy, mutate, return; the caller's list is untouched
fun appendAudit(entries: List<Entry>, entry: Entry): List<Entry> =
    entries + entry

// good — when a mutable working set really is needed
fun appendAudit(entries: List<Entry>, entry: Entry): List<Entry> {
    val working = entries.toMutableList()
    working.add(entry)
    return working
}
```

## 7.11 Type arguments are erased at runtime; use `reified` on an `inline` function when you need the type, and never test for one you do not have.

> Why? "At runtime, the instances of generic types do not hold any
> information about their actual type arguments. The type information is said
> to be erased. For example, the instances of `Foo<Bar>` and `Foo<Baz?>` are
> erased to just `Foo<*>`." So `value is List<String>` cannot compile,
> `value as List<String>` compiles with an unchecked-cast warning and defers
> the failure to the first element access, and passing `Class<T>` around is a
> Java workaround Kotlin no longer needs. The exclusion is "inline functions
> with reified type parameters, which have their actual type arguments
> inlined at each call site. This enables type checks and casts for the type
> parameters."
> **Suggestion** — the compiler's unchecked-cast warning is the closest
> mechanical signal.

```kotlin
// bad — the cast is unchecked; the ClassCastException surfaces at the first
// element access, far from here
fun <T> decodeList(json: String, type: Class<T>): List<T> =
    mapper.readValue(json, List::class.java) as List<T>

// good — reified recovers the type argument at each call site
inline fun <reified T> decodeList(json: String): List<T> =
    mapper.readValue(json, object : TypeReference<List<T>>() {})

val orders: List<Order> = decodeList(payload)

// good — reified makes a runtime type check possible at all
inline fun <reified T> Iterable<*>.firstOfType(): T? =
    firstOrNull { it is T } as T?
```

## 7.12 Use a star projection when you genuinely know nothing about a type argument — and know what it costs you.

> Why? `Foo<*>` is Kotlin's safe answer to Java's raw type. It is not "any
> `Foo`" in the loose sense: for a covariant `Foo<out T : TUpper>`, `Foo<*>`
> "is equivalent to `Foo<out TUpper>`", so reads give you `TUpper`; for a
> contravariant `Foo<in T>`, `Foo<*>` "is equivalent to `Foo<in Nothing>`",
> so "there is nothing you can write to `Foo<*>` in a safe way"; and for an
> invariant parameter you get the read behaviour of the first and the write
> behaviour of the second. That is the whole trade: a star projection buys
> you the ability to hold the value without knowing its argument, and it
> costs you writing. If you need to write, you need a real type parameter.
> **Suggestion.**

```kotlin
// bad — `Any?` throws away even the upper bound, so the read needs a cast
fun sizeOf(container: Any?): Int = (container as Collection<*>).size

// bad — `Handler<Any>` is not "a handler of anything": MutableList is
// invariant, so a MutableList<Handler<ClickEvent>> does not fit, and every
// handler in the list has been flattened to the useless Any payload
fun register(handlers: MutableList<Handler<Any>>) { /* ... */ }

// good — star projection: safe to read, impossible to corrupt
fun describe(handlers: List<Handler<*>>): String =
    handlers.joinToString { it.name }

// good — a real type parameter where the argument is needed
fun <T : Event> register(handlers: MutableList<Handler<T>>, handler: Handler<T>) {
    handlers.add(handler)
}
```

## 7.13 Use a type alias to name a long generic signature or a repeated function type — and remember it creates no new type.

> Why? The
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#type-aliases)
> put it plainly: "If you have a functional type or a type with type
> parameters which is used multiple times in a codebase, prefer defining a
> type alias for it." A `typealias` is pure abbreviation — the compiler
> substitutes it everywhere, so `MouseClickHandler` and
> `(Any, MouseEvent) -> Unit` are the *same* type, interchangeable in both
> directions. That is exactly what you want for readability and exactly what
> you must not rely on for safety: an alias adds no checking, and two aliases
> for the same underlying type are freely swappable at every call site.
> **Suggestion.**

```kotlin
// bad — the same eleven-token type spelled out four times
fun subscribe(handler: (Any, MouseEvent) -> Unit) { /* ... */ }
fun unsubscribe(handler: (Any, MouseEvent) -> Unit) { /* ... */ }

fun index(people: Map<String, List<Pair<Person, Instant>>>) { /* ... */ }
fun merge(
    a: Map<String, List<Pair<Person, Instant>>>,
    b: Map<String, List<Pair<Person, Instant>>>,
): Map<String, List<Pair<Person, Instant>>> = a + b

// good
typealias MouseClickHandler = (Any, MouseEvent) -> Unit
typealias PersonIndex = Map<String, List<Pair<Person, Instant>>>

fun subscribe(handler: MouseClickHandler) { /* ... */ }
fun unsubscribe(handler: MouseClickHandler) { /* ... */ }

fun index(people: PersonIndex) { /* ... */ }
fun merge(a: PersonIndex, b: PersonIndex): PersonIndex = a + b
```

## 7.14 Never use a type alias to model a domain concept — use a `value class`.

> Why? This is the failure mode §7.13's last sentence sets up.
> `typealias UserId = String` looks like a domain type and behaves like
> nothing at all: `UserId` and `String` are the same type, so
> `findUser(orderId)` compiles when `orderId` is also a `String` alias, and
> the bug reaches production. A `@JvmInline value class UserId(val value:
> String)` is a genuinely distinct type — the compiler rejects the mix-up —
> and on the JVM it is erased to the underlying `String` in most positions,
> so the safety is close to free. See
> [Chapter 12, Value Classes](12-value-classes.md) for the boxing rules and
> the cases where a value class is the wrong shape.
> **Suggestion.**

```kotlin
// bad — three aliases for String; every one of these calls compiles
typealias UserId = String
typealias OrderId = String
typealias Email = String

fun findUser(id: UserId): User? = repository.byId(id)

findUser(orderId)   // compiles
findUser(email)     // compiles
findUser("nonsense") // compiles

// good — distinct types the compiler enforces
@JvmInline
value class UserId(val value: String)

@JvmInline
value class OrderId(val value: String)

fun findUser(id: UserId): User? = repository.byId(id)

findUser(orderId)    // does not compile
findUser("nonsense") // does not compile
```

## 7.15 Nest a type alias inside the declaration it belongs to rather than parking it at the top level.

> Why? A top-level `typealias` is visible to the whole file and, if public,
> to the whole module — so an alias that only makes sense in the context of
> one class pollutes a namespace it has no business in, and its name has to
> carry the class's name to compensate (`CacheEntryPredicate` rather than
> `Predicate`). Nested type aliases fix that: they live in the class, they
> can be `private`, and they read as part of the type's own vocabulary.
> Nested type aliases arrived in Kotlin 2.2 in Beta behind
> [`-Xnested-type-aliases`](https://kotlinlang.org/docs/whatsnew22.html#support-for-nested-type-aliases)
> and became [Stable in Kotlin 2.3](https://kotlinlang.org/docs/whatsnew23.html),
> so on the 2.4 floor they need no opt-in flag. Note that a nested type alias
> cannot capture the enclosing class's type parameters.
> **Suggestion.**

```kotlin
// bad — an alias that only means anything inside Cache, exported to the whole
// file (and, being public, to the whole module)
typealias CacheEntryPredicate = (key: String, writtenAt: Instant) -> Boolean

class Cache {
    private val evictionRules = mutableListOf<CacheEntryPredicate>()

    private fun isStale(key: String, writtenAt: Instant): Boolean =
        evictionRules.any { rule -> rule(key, writtenAt) }
}

// good — nested, private, and named for its context
class Cache {
    private typealias EntryPredicate = (key: String, writtenAt: Instant) -> Boolean

    private val evictionRules = mutableListOf<EntryPredicate>()

    private fun isStale(key: String, writtenAt: Instant): Boolean =
        evictionRules.any { rule -> rule(key, writtenAt) }
}
```

## 7.16 Use `import ... as` (or a `private` type alias) to disambiguate two same-named types, rather than fully qualifying one of them.

> Why? Two `Instant`s, two `Order`s, or a domain type and its JPA entity in
> the same file leave you with three options: fully qualify one everywhere,
> alias it once, or rename the type. Fully qualifying puts a package path
> into every signature and buries the interesting part of the line; the
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#type-aliases)
> point at the alternative directly: "If you use a private or internal type
> alias for avoiding name collision, prefer the `import ... as` mentioned in
> Packages and Imports." Reach for `import ... as` first — it is scoped to
> the file and needs no declaration — and a `private typealias` only when the
> renamed type also needs to appear in the file's own declarations.
> **Suggestion.**

```kotlin
// bad — a package path in every signature
fun toEntity(
    order: com.example.domain.Order,
): com.example.persistence.Order = com.example.persistence.Order(order.id.value)

// good — aliased at the import, so the signatures read cleanly
import com.example.domain.Order
import com.example.persistence.Order as OrderEntity

fun toEntity(order: Order): OrderEntity = OrderEntity(order.id.value)
```

## 7.17 Name the parameters in a function type when their meaning is not obvious from their types.

> Why? A function type is a signature the reader has to interpret positionally,
> and `(String, String, Boolean) -> Unit` gives them nothing to go on. Kotlin
> lets you name the parameters inside the type — `(name: String, email:
> String, verified: Boolean) -> Unit` — and those names show up in IDE
> completion and in the rendered signature, exactly like a normal parameter
> list. They cost nothing at the call site and are the cheapest documentation
> in the language. Two same-typed adjacent parameters is the threshold: if
> swapping them would still compile, name them.
> **Suggestion.**

```kotlin
// bad — swapping the first two arguments compiles and ships
typealias Notifier = (String, String, Boolean) -> Unit

fun register(notify: Notifier) { /* ... */ }

// good — the names travel with the type
typealias Notifier = (recipient: String, subject: String, urgent: Boolean) -> Unit

fun register(notify: Notifier) { /* ... */ }
```

## 7.18 Use a definitely non-nullable type (`T & Any`) when overriding a Java member whose type is annotated non-null.

> Why? "To make interoperability with generic Java classes and interfaces
> easier, Kotlin supports declaring a generic type parameter as definitely
> non-nullable" by writing `T & Any`, and "a definitely non-nullable type must
> have a nullable upper bound." The case it exists for is precise: "the most
> common use case for declaring definitely non-nullable types is when you want
> to override a Java method that contains `@NotNull` as an argument." Without
> it, a type parameter with an implicit `Any?` bound makes the override's
> parameter nullable, which either fails to compile against the Java
> `@NotNull` or, worse, quietly accepts a `null` the Java side promised would
> never arrive. Outside interop you almost never need it: "when working only
> with Kotlin, it's unlikely that you will need to declare definitely
> non-nullable types explicitly because Kotlin's type inference takes care of
> this for you."
> **Suggestion.**

```kotlin
// The Java side: interface Game<T> { T save(T x); @NotNull T load(@NotNull T x); }

// bad — T1 has an implicit Any? bound, so the override's parameter is
// nullable and does not match the annotated Java signature
interface ArcadeGame<T1> : Game<T1> {
    override fun save(x: T1): T1
    override fun load(x: T1): T1
}

// good — `& Any` states that this position is definitely non-nullable
interface ArcadeGame<T1> : Game<T1> {
    override fun save(x: T1): T1
    override fun load(x: T1 & Any): T1 & Any
}
```
