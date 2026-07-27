<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 14. Objects, Companions & Factories

Kotlin has no `static` keyword. That single omission is what this chapter is
about: everything Java expresses with `static` — singletons, utility methods,
constants, factories — Kotlin splits across three constructs with different
semantics, and picking the wrong one is the most common way a Java-shaped mind
writes non-idiomatic Kotlin. An `object` declaration is a lazily initialized
singleton. An object *expression* is an anonymous instance created where it
appears. A `companion object` is a real object that happens to be tied to a
class. None of them is a namespace for statics, and Kotlin's actual answer to
"where do the static helpers go" is usually "at the top level, in a file."

The upstream sources are the
[Kotlin object declarations and expressions documentation](https://kotlinlang.org/docs/object-declarations.html)
— particularly
[companion objects](https://kotlinlang.org/docs/object-declarations.html#companion-objects)
and the
[behaviour difference between object declarations and expressions](https://kotlinlang.org/docs/object-declarations.html#behavior-difference-between-object-declarations-and-expressions) —
the
[Kotlin coding conventions on factory functions](https://kotlinlang.org/docs/coding-conventions.html#factory-functions)
and
[names for class-like functions](https://kotlinlang.org/docs/coding-conventions.html#names-for-class-like-functions),
the
[Android Kotlin style guide on constant names](https://developer.android.com/kotlin/style-guide#constant_names),
and the
[Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
reference for
[static methods](https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-methods),
[static fields](https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-fields),
and
[package-level functions](https://kotlinlang.org/docs/java-to-kotlin-interop.html#package-level-functions).

Three neighbours are deferred. **`data object` in a sealed hierarchy** is
[Chapter 13, §13.4](13-sealed-types.md) — this chapter covers the plain
`object`. **Mutable global state**, and why an `object` is the worst place to
put it, is [Chapter 25](25-immutability.md); §14.16 states only the shape of
the rule. **The full `@JvmStatic` / `@JvmField` / `@JvmName` interop story** is
[Chapter 28](28-java-interop.md); §14.5 and §14.14 cover the part you need to
get a companion object right in the first place.

**Tool alignment:** three rules below are mechanically enforced. detekt's
`ObjectLiteralToLambda`, `UtilityClassWithPublicConstructor`, and
`MayBeConstant` (all `style`, all active by default) and
`ObjectPropertyNaming` / `TopLevelPropertyNaming` (`naming`, active by
default) each fire on a specific failure named below — though only
`TopLevelPropertyNaming` actually demands `UPPER_SNAKE_CASE` at default
configuration, as §14.13 explains. detekt's `ClassOrdering` covers §14.7 but
is **off** by default, so that rule stays a Suggestion unless you enable it.

## 14.1 Use an `object` declaration for a genuinely stateless singleton instead of hand-rolling one.

> Why? The
> [object declarations documentation](https://kotlinlang.org/docs/object-declarations.html#object-declarations)
> gives you both guarantees for free: "Object declarations are initialized
> lazily, when accessed for the first time" and "The initialization of an
> object declaration is thread-safe and done on first access." A transplanted
> Java singleton — private constructor plus a `getInstance()` on the companion
> — reimplements exactly that, badly, and adds a class, a constructor, and an
> accessor the reader has to check. **Suggestion.**

```kotlin
// bad — a Java singleton transplanted; the private constructor, the companion,
// and getInstance() together do what `object` does in one keyword
class JsonCodec private constructor() {
    fun encode(value: Any): String = /* ... */ ""

    companion object {
        private val instance = JsonCodec()

        fun getInstance(): JsonCodec = instance
    }
}

// good
object JsonCodec {
    fun encode(value: Any): String = /* ... */ ""
}
```

## 14.2 Implement a stateless interface with `object : Interface` rather than a class you allocate on every call.

> Why? A stateless implementation has nothing to distinguish two instances, so
> allocating a fresh one per call is pure waste and defeats reference equality
> for callers that cache it. The Kotlin coding conventions even give this shape
> its own naming rule under
> [property names](https://kotlinlang.org/docs/coding-conventions.html#property-names):
> "Names of properties holding references to singleton objects can use the same
> naming style as `object` declarations." **Suggestion.**

```kotlin
// bad — a new comparator per call; two calls produce unequal instances
class LastNameComparator : Comparator<Person> {
    override fun compare(a: Person, b: Person): Int = a.lastName.compareTo(b.lastName)
}

fun byLastName(): Comparator<Person> = LastNameComparator()

// good — one instance, named like the object it is
object LastNameComparator : Comparator<Person> {
    override fun compare(a: Person, b: Person): Int = a.lastName.compareTo(b.lastName)
}
```

## 14.3 Use an object expression for a one-off anonymous instance — but let a lambda take over when the target is a functional interface.

> Why? An object expression is the right tool when you must override several
> members or extend a class. When the target has exactly one abstract method,
> the object expression is four lines of ceremony around one line of behaviour,
> and Kotlin's SAM conversion already gives you the lambda form. Object
> expressions are also, per the
> [behaviour difference](https://kotlinlang.org/docs/object-declarations.html#behavior-difference-between-object-declarations-and-expressions)
> section, "executed (and initialized) immediately, where they are used" —
> unlike an `object` declaration, they are not singletons and not lazy.
> **Violation — enforced by `detekt/ObjectLiteralToLambda`.**

```kotlin
// bad — an anonymous object implementing a single method
executor.execute(
    object : Runnable {
        override fun run() {
            reindex()
        }
    },
)

// good — SAM conversion
executor.execute { reindex() }

// good — object expression is still right when you override more than one member
val listener = object : MouseAdapter() {
    override fun mousePressed(event: MouseEvent) = beginDrag(event)

    override fun mouseReleased(event: MouseEvent) = endDrag(event)
}
```

## 14.4 Know the three initialization timings, and never hide expensive work or a side effect behind one.

> Why? The three constructs initialize at three different moments, and the
> [documentation](https://kotlinlang.org/docs/object-declarations.html#behavior-difference-between-object-declarations-and-expressions)
> names all three: an object expression is initialized "immediately, where
> [it is] used"; an object declaration "lazily, when accessed for the first
> time"; and "A companion object is initialized when the corresponding class is
> loaded (resolved) that matches the semantics of a Java static initializer."
> So a heavy `object` initializer runs on whichever unlucky request touches it
> first — a latency spike with no obvious cause — and a companion `init` block
> runs at a moment determined by classloading, which may be never. Put
> start-up work in start-up code. **Suggestion.**

```kotlin
// bad — the disk read happens on the first request that touches SchemaCache,
// and the metrics registration happens whenever FeatureFlags is first loaded
object SchemaCache {
    val schemas: Map<String, Schema> = loadFromDisk()
}

class FeatureFlags {
    companion object {
        init {
            MetricsRegistry.register("feature-flags")
        }
    }
}

// good — construction is explicit, ordered, and testable
class SchemaCache(private val schemas: Map<String, Schema>) {
    companion object {
        fun load(path: Path): SchemaCache = SchemaCache(readSchemas(path))
    }
}

fun startUp(path: Path): Application {
    MetricsRegistry.register("feature-flags")
    return Application(schemaCache = SchemaCache.load(path))
}
```

## 14.5 Treat a companion object as a real object, not a `static` namespace — Java callers need `@JvmStatic`.

> Why? A companion object compiles to a nested class plus a static `Companion`
> field on the enclosing class; its members are *instance* methods on that
> object. Kotlin hides this (`Foo.create(...)` just works), Java does not:
> without the annotation a Java caller must write `Foo.Companion.create(...)`.
> [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-methods)
> spells out what the annotation buys: "the compiler generates both a static
> method in the enclosing class of the object and an instance method in the
> object itself." If Java code calls it, annotate it.
> **Suggestion** — no default detekt or ktlint rule checks for missing
> `@JvmStatic`.

```kotlin
// bad — Java must write Duration d = RetryPolicy.Companion.defaultBackoff();
class RetryPolicy(val maxAttempts: Int) {
    companion object {
        fun defaultBackoff(): Duration = Duration.ofMillis(250)
    }
}

// good — Java writes RetryPolicy.defaultBackoff(); Kotlin is unchanged
class RetryPolicy(val maxAttempts: Int) {
    companion object {
        @JvmStatic
        fun defaultBackoff(): Duration = Duration.ofMillis(250)
    }
}
```

## 14.6 Leave the companion object unnamed unless the name genuinely adds meaning.

> Why? The
> [companion objects documentation](https://kotlinlang.org/docs/object-declarations.html#companion-objects)
> notes that the name "can be omitted (defaults to `Companion`)". Kotlin call
> sites never mention it either way, so a name like `Factory` or `Helper` is
> pure noise that changes nothing except the qualifier Java callers have to
> spell. Name the companion only when it is referenced as a value in its own
> right — for example when it implements an interface a caller passes around.
> **Suggestion.**

```kotlin
// bad — the name does nothing; Kotlin never uses it and it says nothing new
class User(val name: String) {
    companion object Factory {
        fun create(name: String): User = User(name)
    }
}

// good — unnamed
class User(val name: String) {
    companion object {
        fun create(name: String): User = User(name)
    }
}

// good — named, because the companion is itself passed around as a value
class User(val name: String) {
    companion object ByName : Comparator<User> {
        override fun compare(a: User, b: User): Int = a.name.compareTo(b.name)
    }
}

fun sorted(users: List<User>): List<User> = users.sortedWith(User.ByName)
```

## 14.7 Put the companion object last in the class body.

> Why? The Kotlin coding conventions'
> [class layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout)
> rule fixes the order: "1. Property declarations and initializer blocks
> 2. Secondary constructors 3. Method declarations 4. Companion object." A
> companion at the top pushes the class's actual instance API below a block of
> factories and constants, so a reader scanning for "what does an instance of
> this do" has to scroll past the part that is not about instances at all.
> **Suggestion** — detekt's `ClassOrdering` enforces exactly this order, but it
> is off by default.

```kotlin
// bad — factories and constants before the instance API
class Invoice(val lines: List<Line>) {
    companion object {
        const val MAX_LINES = 500

        fun empty(): Invoice = Invoice(emptyList())
    }

    val total: Money get() = lines.sumOf { it.amount }

    fun withLine(line: Line): Invoice = Invoice(lines + line)
}

// good
class Invoice(val lines: List<Line>) {
    val total: Money get() = lines.sumOf { it.amount }

    fun withLine(line: Line): Invoice = Invoice(lines + line)

    companion object {
        const val MAX_LINES = 500

        fun empty(): Invoice = Invoice(emptyList())
    }
}
```

## 14.8 Prefer a top-level function to a companion object member that does not touch the class's private state.

> Why? Kotlin compiles
> [package-level functions](https://kotlinlang.org/docs/java-to-kotlin-interop.html#package-level-functions)
> to plain static methods on a file facade class — no companion class, no
> static `Companion` field, no indirection, and no need for `@JvmStatic`. A
> companion object earns its keep only when its members need the class's
> private constructor or private members. If the function would compile
> unchanged outside the class, it belongs outside the class. **Suggestion.**

```kotlin
// bad — the companion exists only to give these functions a home, and neither
// touches anything private
class Slug(val value: String) {
    companion object {
        fun normalize(raw: String): String = raw.trim().lowercase().replace(' ', '-')

        fun isValid(raw: String): Boolean = raw.matches(SLUG_PATTERN)
    }
}

// good — top-level functions; the class keeps only what is about a Slug
fun normalizeSlug(raw: String): String = raw.trim().lowercase().replace(' ', '-')

fun isValidSlug(raw: String): Boolean = raw.matches(SLUG_PATTERN)

class Slug(val value: String)
```

## 14.9 Never write a Kotlin utility class.

> Why? A `class Utils` whose entire body is a companion object is a Java idiom
> with no purpose in Kotlin: the class exists solely because Java has nowhere
> else to put a static method, and Kotlin has a file. Worse, the class is still
> instantiable — `StringUtils()` compiles — because Kotlin supplies a public
> no-arg constructor. Use top-level functions, or extension functions when the
> operation reads as behaviour on the receiver.
> **Violation — enforced by `detekt/UtilityClassWithPublicConstructor`.**

```kotlin
// bad — instantiable, and the companion is a namespace pretending to be a class
class StringUtils {
    companion object {
        fun truncate(value: String, maxLength: Int): String =
            if (value.length <= maxLength) value else value.take(maxLength - 1) + "…"
    }
}

val truncated = StringUtils.truncate(title, 40)
val pointless = StringUtils() // compiles

// good — an extension function at the top level
fun String.truncate(maxLength: Int): String =
    if (length <= maxLength) this else take(maxLength - 1) + "…"

val shortened = title.truncate(40)
```

## 14.10 Put a factory on the companion object when it needs the private constructor, and name it with the conventional vocabulary.

> Why? This is the one thing a companion object does that nothing else can: it
> can see the class's `private constructor`, so it can make construction go
> through a validating or caching entry point that callers cannot bypass. Name
> the factory from the vocabulary every Kotlin and Java reader already knows —
> `of` and `valueOf` for cheap conversion, `from` for a type conversion,
> `parse` for input that may be malformed, `create` for a fresh instance —
> because each of those names is a promise about cost and failure.
> **Suggestion.**

```kotlin
// bad — a public constructor, so the validation is optional; and the factory
// name says nothing about the fact that it can fail
class Ean13(val digits: String) {
    companion object {
        fun make(raw: String): Ean13 {
            require(raw.length == 13) { "EAN-13 must be 13 digits, was ${raw.length}" }
            return Ean13(raw)
        }
    }
}

val bypassed = Ean13("nope") // no validation ran

// good — construction is impossible without going through a named factory
class Ean13 private constructor(val digits: String) {
    companion object {
        fun parse(raw: String): Ean13 {
            require(raw.length == 13 && raw.all(Char::isDigit)) {
                "EAN-13 must be 13 digits, was '$raw'"
            }
            return Ean13(raw)
        }

        fun from(upc: Upc): Ean13 = Ean13("0" + upc.digits)
    }
}
```

## 14.11 Do not give a factory function the same name as the class it constructs.

> Why? The Kotlin coding conventions'
> [factory functions](https://kotlinlang.org/docs/coding-conventions.html#factory-functions)
> rule is direct: "If you declare a factory function for a class, avoid giving
> it the same name as the class itself. Prefer using a distinct name, making it
> clear why the behavior of the factory function is special. Only if there is
> really no special semantics, you can use the same name as the class." The one
> sanctioned exception is in
> [names for class-like functions](https://kotlinlang.org/docs/coding-conventions.html#names-for-class-like-functions):
> "Factory functions that create class instances can have the same name as the
> abstract return type" — a top-level `fun Foo(): Foo` that hides a private
> `FooImpl`. **Suggestion.**

```kotlin
data class Polar(val angle: Double, val radius: Double)

// bad — Point(...) tells the reader nothing about why this is not a constructor
class Point(val x: Double, val y: Double) {
    companion object {
        fun Point(polar: Polar): Point =
            Point(polar.radius * cos(polar.angle), polar.radius * sin(polar.angle))
    }
}

// good — the name says what makes it special
class Point(val x: Double, val y: Double) {
    companion object {
        fun fromPolar(angle: Double, radius: Double): Point =
            Point(radius * cos(angle), radius * sin(angle))
    }
}

// good — the sanctioned exception: a class-like function named after the
// abstract type it returns, hiding the implementation
interface Cache<K, V> {
    fun put(key: K, value: V)
}

private class LruCache<K, V>(private val maxSize: Int) : Cache<K, V> {
    private val entries = LinkedHashMap<K, V>()

    override fun put(key: K, value: V) {
        entries[key] = value
        if (entries.size > maxSize) entries.remove(entries.keys.first())
    }
}

fun <K, V> Cache(maxSize: Int): Cache<K, V> = LruCache(maxSize)
```

## 14.12 Use `operator fun invoke` on a companion only as a genuine pseudo-constructor.

> Why? The
> [invoke operator](https://kotlinlang.org/docs/operator-overloading.html#invoke-operator)
> makes `Foo(x)` a call to `Foo.Companion.invoke(x)`, which reads at the call
> site exactly like construction. That is a feature when the thing really is
> construction — a private constructor plus validation, or a factory returning
> a hidden subtype — and a trap otherwise, because a reader who sees `Foo(x)`
> will assume it allocates, cannot fail, and does no I/O. If the operation is
> anything more than "build one of these", give it a name. **Suggestion.**

```kotlin
// bad — reads as construction, performs a blocking network round trip
class UserClient(private val http: HttpClient) {
    companion object {
        operator fun invoke(id: UserId): User = defaultHttp.get("/users/$id")
    }
}

val user = UserClient(id) // looks like a constructor call

// good — a name that says what happens
class UserClient(private val http: HttpClient) {
    fun fetch(id: UserId): User = http.get("/users/$id")
}

// good — a real pseudo-constructor: the private constructor makes validation
// unavoidable, and invoke takes a different representation so it can never be
// confused with the constructor it delegates to
class Percentage private constructor(val basisPoints: Int) {
    companion object {
        operator fun invoke(ratio: Double): Percentage {
            require(ratio in 0.0..1.0) { "ratio must be in 0.0..1.0, was $ratio" }
            return Percentage((ratio * 10_000).roundToInt())
        }
    }
}

val threeQuarters = Percentage(0.75)
```

## 14.13 Declare scalar constants `const`, name them `UPPER_SNAKE_CASE`, and put them at the top level or in an `object`.

> Why? The
> [Android Kotlin style guide on constant names](https://developer.android.com/kotlin/style-guide#constant_names)
> sets all three parts: "Constant names use UPPER_SNAKE_CASE"; "Constant values
> can only be defined inside of an `object` or as a top-level declaration.
> Values otherwise meeting the requirement of a constant but defined inside of
> a `class` must use a non-constant name"; and "Constants which are scalar
> values must use the `const` modifier." A companion object *is* an object, so
> constants belong there or at the top level, never as an instance property of
> the class. Without `const`, a scalar is a property with a getter rather than
> a compile-time constant, so it cannot be used in an annotation argument and
> cannot be inlined.
> **Suggestion — `detekt/MayBeConstant` covers this, but it is absent from detekt 1.23.8's default config (the docs site is ahead of the latest stable release). Enable it once your detekt version ships it; see chapter 47.** for the missing `const`,
> **and `detekt/TopLevelPropertyNaming`** for a top-level constant that is not
> `UPPER_SNAKE_CASE` (its default `constantPattern` is `[A-Z][_A-Z0-9]*`).
> `detekt/ObjectPropertyNaming` covers constants inside an `object` or
> companion, but its default `constantPattern` is `[A-Za-z][_A-Za-z0-9]*`,
> which accepts camelCase — tighten it to `[A-Z][_A-Z0-9]*` if you want the
> naming half enforced there too.

```kotlin
// bad — an instance property, camelCase, and not const
class HttpClient {
    val defaultTimeoutMillis = 5_000
}

// bad — in an object, but still not const, so it is a getter call
object HttpDefaults {
    val TIMEOUT_MILLIS = 5_000
}

// good — top level, const, UPPER_SNAKE_CASE
const val DEFAULT_TIMEOUT_MILLIS = 5_000

// good — in the companion, which is an object
class HttpClient {
    companion object {
        const val DEFAULT_TIMEOUT_MILLIS = 5_000
    }
}
```

## 14.14 Know which constants become JVM static fields, and annotate the ones Java must read directly.

> Why?
> [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-fields)
> draws the line precisely: "Properties declared as `const` (in classes as well
> as at the top level) are turned into static fields in Java", while a
> non-`const` companion property is a private static field plus an accessor on
> the `Companion` object — Java has to call `Foo.Companion.getX()`. Adding
> `@JvmField` "makes it a static field with the same visibility as the property
> itself", but the same page's requirements exclude anything `const`, `private`,
> `open`, `override`, or delegated. Reference types cannot be `const`, so a
> `Duration` or a `List` constant that Java reads needs `@JvmField`.
> **Suggestion.**

```kotlin
// bad — Java must write TokenService.Companion.getDEFAULT_TTL(), which nobody
// expects from something named like a constant
class TokenService {
    companion object {
        val DEFAULT_TTL: Duration = Duration.ofMinutes(15)
    }
}

// good — const for scalars, @JvmField for the reference types Java reads
class TokenService {
    companion object {
        const val HEADER_NAME = "Authorization" // Java: TokenService.HEADER_NAME

        @JvmField
        val DEFAULT_TTL: Duration = Duration.ofMinutes(15) // Java: TokenService.DEFAULT_TTL
    }
}
```

## 14.15 Prefer a file-private top-level `const val` to a companion object that exists only to hold constants.

> Why? A companion object costs a nested class and a static field, and it puts
> the constant in the class's public API surface whether you wanted that or
> not. A top-level `private const val` in the same file is visible to
> everything in that file, invisible to everything outside it, and compiles to
> a private static field on the file facade — no extra class at all. Reserve
> the companion for constants that are genuinely part of the type's published
> contract. **Suggestion.**

```kotlin
// bad — a companion whose only job is holding two implementation details,
// both of which are now public API
class RetryingUploader(private val client: StorageClient) {
    fun upload(blob: Blob) = retry(MAX_ATTEMPTS, BACKOFF_MILLIS) { client.put(blob) }

    companion object {
        const val MAX_ATTEMPTS = 3
        const val BACKOFF_MILLIS = 250L
    }
}

// good — file-private constants, no companion, nothing added to the API
private const val MAX_ATTEMPTS = 3
private const val BACKOFF_MILLIS = 250L

class RetryingUploader(private val client: StorageClient) {
    fun upload(blob: Blob) = retry(MAX_ATTEMPTS, BACKOFF_MILLIS) { client.put(blob) }
}
```

## 14.16 Never put mutable state in an `object` or a companion object.

> Why? An `object` is a process-wide singleton, so a `var` or a mutable
> collection inside one is global mutable state with every problem that
> implies: no test can reset it, two tests in the same JVM interfere, and every
> access is a data race unless you made it thread-safe by hand. The Kotlin
> coding conventions'
> [immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability)
> rule — "Prefer using immutable data to mutable" — bites hardest here, because
> the singleton removes the usual escape hatch of constructing a fresh
> instance. Make it an injected class with a normal lifetime; see
> [Chapter 25](25-immutability.md). **Suggestion.**

```kotlin
// bad — global mutable state; unresettable in tests, racy in production
object SessionRegistry {
    private val sessions = mutableMapOf<UserId, Session>()

    fun put(session: Session) {
        sessions[session.userId] = session
    }

    fun get(id: UserId): Session? = sessions[id]
}

// good — an ordinary class the caller owns and a test can construct fresh
class SessionRegistry {
    private val sessions = ConcurrentHashMap<UserId, Session>()

    fun put(session: Session) {
        sessions[session.userId] = session
    }

    fun get(id: UserId): Session? = sessions[id]
}
```

## 14.17 Do not declare a companion object you barely use.

> Why? Every companion object is an extra class file, an extra static field on
> the enclosing class, and an extra hop for the reader — who now has to check
> whether the class has type-level behaviour before concluding it does not. A
> companion holding one private constant, or an empty one left behind by a
> refactor, buys nothing. Delete it and move the member to the top level
> (§14.8) or into the file (§14.15). **Suggestion.**

```kotlin
// bad — an empty companion left over from a refactor
class TsvWriter(private val sink: Appendable) {
    companion object

    fun write(row: List<String>) = sink.append(row.joinToString("\t")).append('\n')
}

// bad — a companion holding one private constant, which is exactly what a
// file-private top-level const val is for
class CsvWriter(private val sink: Appendable) {
    fun write(row: List<String>) = sink.append(row.joinToString(DELIMITER)).append('\n')

    private companion object {
        const val DELIMITER = ","
    }
}

// good
private const val DELIMITER = ","

class CsvWriter(private val sink: Appendable) {
    fun write(row: List<String>) = sink.append(row.joinToString(DELIMITER)).append('\n')
}
```
