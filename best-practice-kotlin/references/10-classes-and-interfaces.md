<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 10. Classes & Interfaces

Kotlin's class declaration is compressed to the point where a whole Java
class — fields, constructor, accessors — collapses into one header line. That
compression is the language's biggest ergonomic win and also where most of
its subtle traps live: what runs when, what the primary constructor is
allowed to see, and which of the three things called "a constructor" you
actually wanted. This chapter covers construction and initialization,
finality, the interface-versus-abstract-class decision, class layout, and the
nested/`inner` distinction.

The rules draw on the
[Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
— specifically
[class layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout),
[class headers](https://kotlinlang.org/docs/coding-conventions.html#class-headers),
[interface implementation layout](https://kotlinlang.org/docs/coding-conventions.html#interface-implementation-layout),
[factory functions](https://kotlinlang.org/docs/coding-conventions.html#factory-functions),
and
[default parameter values](https://kotlinlang.org/docs/coding-conventions.html#default-parameter-values)
— together with the
[Android Kotlin style guide's class member ordering](https://developer.android.com/kotlin/style-guide#class_member_ordering)
rule and the language documentation on
[classes](https://kotlinlang.org/docs/classes.html),
[inheritance](https://kotlinlang.org/docs/inheritance.html), and
[nested and inner classes](https://kotlinlang.org/docs/nested-classes.html).

Four neighbouring topics are deliberately deferred. **Data classes** —
what `data` generates and when it is the wrong shape — are
[Chapter 11](11-data-classes.md). **Value classes** are
[Chapter 12](12-value-classes.md). **Sealed hierarchies** are
[Chapter 13](13-sealed-types.md), and **`object` declarations, companion
objects, and factory placement** are
[Chapter 14](14-objects-and-companions.md). Kotlin's `by` delegation, which
§10.14 leans on, gets its full treatment in
[Chapter 16](16-delegation.md); property accessors and backing fields are
[Chapter 17](17-properties-and-backing-fields.md).

**Tool alignment:** several rules below are mechanically enforced. detekt's
`AbstractClassCanBeConcreteClass`, `UtilityClassWithPublicConstructor`,
`NestedClassesVisibility`, `UseRequire`, and `UseCheckOrError` are active in
detekt's default configuration; `ClassOrdering`, `UnnecessaryInnerClass`, and
`ComplexInterface` exist but are **not** active by default and must be
switched on explicitly.
Rules a named check actually enforces are marked **Violation**; the rest are
**Suggestion**.

## 10.1 Declare a class's properties in its primary constructor, not in the body assigned from a constructor parameter.

> Why? The
> [language docs on classes](https://kotlinlang.org/docs/classes.html)
> treat `class Person(val name: String)` as the normal shape, and are explicit
> that "these constructor parameter properties are stored as part of the
> instance and are accessible from outside the class." Re-declaring the property in the body doubles the surface area a
> reader has to check for agreement — the parameter name, the property name,
> the type, and the assignment — and creates a window where the property is
> still unassigned (see §10.5). **Suggestion.**

```kotlin
// bad — four lines to say what the header already said, and `region` is
// unassigned for the duration of the init block above it
class ShippingZone(name: String, region: String) {
    val name: String
    val region: String

    init {
        this.name = name
        this.region = region
    }
}

// good
class ShippingZone(val name: String, val region: String)
```

## 10.2 Prefer one primary constructor with default parameter values to a chain of secondary constructors.

> Why? The
> [coding conventions on default parameter values](https://kotlinlang.org/docs/coding-conventions.html#default-parameter-values)
> say it directly: "Prefer declaring functions with default parameter values
> to declaring overloaded functions." The same applies to constructors. A
> telescoping chain forces every reader to trace the delegation to find where
> initialization actually happens, and a caller reading
> `RetryPolicy(3, 1_000)` cannot tell which number is which. Defaults plus
> named arguments at the call site fix both. If Java callers need the
> overloads as distinct JVM signatures, add `@JvmOverloads` — see
> [Chapter 28](28-java-interop.md). **Suggestion.**

```kotlin
// bad — the reader has to walk three hops to find the real initialization
class RetryPolicy {
    val maxAttempts: Int
    val backoffMillis: Long
    val jitter: Boolean

    constructor() : this(3)

    constructor(maxAttempts: Int) : this(maxAttempts, 1_000L)

    constructor(maxAttempts: Int, backoffMillis: Long) : this(maxAttempts, backoffMillis, false)

    constructor(maxAttempts: Int, backoffMillis: Long, jitter: Boolean) {
        this.maxAttempts = maxAttempts
        this.backoffMillis = backoffMillis
        this.jitter = jitter
    }
}

val policy = RetryPolicy(5, 250L, true) // which flag is which?

// good — one constructor, and the call site names what it sets
class RetryPolicy(
    val maxAttempts: Int = 3,
    val backoffMillis: Long = 1_000L,
    val jitter: Boolean = false,
)

val policy = RetryPolicy(maxAttempts = 5, backoffMillis = 250L, jitter = true)
```

## 10.3 Use a named factory function — not a secondary constructor — when construction carries a name, can fail, or returns something other than a fresh instance.

> Why? The
> [coding conventions on factory functions](https://kotlinlang.org/docs/coding-conventions.html#factory-functions)
> recommend replacing overloaded constructors with factory functions when
> they "can't be reduced to a single constructor including parameters with
> default values", and warn to "avoid giving it the same name as the class
> itself. Prefer using a distinct name, making it clear why the behavior of
> the factory function is special." A constructor's name is fixed, so two
> constructions that differ in *meaning* rather than in signature cannot be
> told apart; a constructor also cannot return `null`, a cached instance, or
> a subtype. Placement of the factory (companion object versus top-level
> function) is [Chapter 14](14-objects-and-companions.md). **Suggestion.**

```kotlin
// bad — two constructions with the same shape; only one can exist, and neither
// says what its argument means
class Temperature(val kelvin: Double) {
    constructor(celsius: Double) : this(celsius + 273.15) // does not compile: same signature
}

// good — each factory names its input, and one of them may fail
class Temperature private constructor(val kelvin: Double) {
    companion object {
        fun ofKelvin(kelvin: Double): Temperature = Temperature(kelvin)

        fun ofCelsius(celsius: Double): Temperature = Temperature(celsius + 273.15)

        fun parseOrNull(text: String): Temperature? =
            text.removeSuffix("K").toDoubleOrNull()?.let(::Temperature)
    }
}
```

## 10.4 Validate constructor arguments in an `init` block with `require`, `requireNotNull`, or `check` — never a hand-written `throw`.

> Why? `require` throws `IllegalArgumentException` and `check` throws
> `IllegalStateException`, which is the same distinction you would make by
> hand, but the stdlib forms take a lazily-evaluated message lambda and read
> as a precondition rather than as control flow. Use `require` for anything
> the *caller* got wrong and `check` for anything the *object's own state*
> got wrong. Validating at construction means the object is either valid or
> does not exist, so no downstream method has to re-check.
> **Violation — enforced by `detekt/UseRequire` and `detekt/UseCheckOrError`.**

```kotlin
// bad — hand-rolled throws; detekt flags both
class Discount(val percentage: Int, val code: String) {
    init {
        if (percentage !in 0..100) {
            throw IllegalArgumentException("percentage out of range")
        }
        if (code.isBlank()) {
            throw IllegalStateException("code must not be blank")
        }
    }
}

// good — preconditions read as preconditions, and name the rejected value
class Discount(val percentage: Int, val code: String) {
    init {
        require(percentage in 0..100) { "percentage must be 0..100, was $percentage" }
        require(code.isNotBlank()) { "code must not be blank" }
    }
}
```

## 10.5 Declare every property above the `init` block that reads it.

> Why? Property initializers and `init` blocks are one interleaved sequence:
> the language docs state that "they run in the order in which they appear in
> the class body, along with property initializers." An `init` block placed
> above a property therefore runs before that property is assigned. The
> compiler catches a *direct* read, but it cannot see a read that goes
> through a member function, so the failure surfaces as a `null` in a
> non-nullable `String` or a zero in a non-zero `Int` at runtime. Keeping the
> declaration order honest is the only reliable defence.
> **Suggestion** — no check verifies indirect reads.

```kotlin
// bad — `describe()` reads `fullName` before its initializer has run;
// this prints "Greeting(null)"
class Greeting(first: String, last: String) {
    init {
        println(describe())
    }

    val fullName: String = "$first $last"

    fun describe(): String = "Greeting($fullName)"
}

// good — the init block sits below everything it depends on
class Greeting(first: String, last: String) {
    val fullName: String = "$first $last"

    init {
        println(describe())
    }

    fun describe(): String = "Greeting($fullName)"
}
```

## 10.6 Never call an `open` member from a constructor, a property initializer, or an `init` block.

> Why? The
> [language docs on derived class initialization order](https://kotlinlang.org/docs/inheritance.html#derived-class-initialization-order)
> carry an explicit warning: "When the base class constructor is executed,
> the properties declared or overridden in the derived class have not yet
> been initialized. Using any of those properties in the base class
> initialization logic (either directly or indirectly through another
> overridden `open` member implementation) may lead to incorrect behavior or
> a runtime failure. When designing a base class, you should therefore avoid
> using `open` members in the constructors, property initializers, or `init`
> blocks." Pass what the base needs as a constructor argument instead.
> **Suggestion.**

```kotlin
// bad — the virtual call lands in Derived.size before Derived's initializer runs,
// so this prints "Base init: size = 0", not 2
open class Base(val label: String) {
    open val size: Int = 0

    init {
        println("Base init: size = $size")
    }
}

class Derived(label: String, items: List<String>) : Base(label) {
    override val size: Int = items.size
}

// good — the base takes what it needs, so nothing is virtual during construction
open class Base(val label: String, val size: Int) {
    init {
        println("Base init: size = $size")
    }
}

class Derived(label: String, items: List<String>) : Base(label, items.size)
```

## 10.7 Leave classes final; add `open` only where extension is a designed, documented extension point.

> Why? "By default, Kotlin classes are final – they can't be inherited." That
> default is not an inconvenience to work around — it is the language taking
> the position that an inheritable class is an API surface with a contract,
> and that most classes were never designed to have one. Marking a class
> `open` without documenting what an override may assume creates a fragile
> base class: any future change to a non-`open` method's *call pattern*
> silently changes the behaviour of every subclass. If you find yourself
> adding `open` to enable a test double, extract an interface instead — that
> is [Chapter 32](32-testing.md)'s answer, not `open`. Spring and JPA need
> `open` classes, but you get them from the `kotlin-spring` and `kotlin-jpa`
> compiler plugins, never by hand — see
> [Chapter 41](41-spring-kotlin-setup.md). **Suggestion.**

```kotlin
// bad — opened so a test could subclass it; now every method is a contract
open class PricingService(private val rates: RateTable) {
    open fun priceFor(sku: String): Long = rates.lookup(sku)

    open fun priceAll(skus: List<String>): Map<String, Long> =
        skus.associateWith { priceFor(it) } // subclasses now depend on this calling priceFor
}

// good — the seam is an interface; the implementation stays final
interface PricingService {
    fun priceFor(sku: String): Long

    fun priceAll(skus: List<String>): Map<String, Long>
}

class RateTablePricingService(private val rates: RateTable) : PricingService {
    override fun priceFor(sku: String): Long = rates.lookup(sku)

    override fun priceAll(skus: List<String>): Map<String, Long> =
        skus.associateWith { priceFor(it) }
}
```

## 10.8 Prefer an interface with default implementations to an abstract class; reach for an abstract class only when you need state or a non-public constructor.

> Why? An interface can carry default method bodies and abstract properties,
> which covers almost everything an abstract base class was doing. What an
> interface *cannot* do is hold a backing field or restrict who may construct
> an implementor — so those two needs, and only those two, justify the
> abstract class. Choosing the interface keeps the door open for a class that
> already has a superclass, and keeps the test double trivial. **Suggestion.**

```kotlin
// bad — abstract class used purely to share a default implementation, which
// permanently spends the implementor's one superclass slot
abstract class Validator<T> {
    abstract fun errors(value: T): List<String>

    fun isValid(value: T): Boolean = errors(value).isEmpty()
}

// good — same sharing, no inheritance slot consumed
interface Validator<T> {
    fun errors(value: T): List<String>

    fun isValid(value: T): Boolean = errors(value).isEmpty()
}

// good — abstract class earns its keep: it holds state and closes construction
abstract class BufferedSink protected constructor(private val buffer: ByteArray) {
    protected var position: Int = 0
        private set

    abstract fun flush(bytes: ByteArray)
}
```

## 10.9 Never declare an abstract class that has no abstract members.

> Why? A class with no abstract members is a concrete class that has been
> forbidden from being instantiated for no stated reason. Either it is a
> complete implementation, in which case drop `abstract`, or it is a namespace
> for shared helpers, in which case it should be an `object` or a set of
> top-level functions ([Chapter 14](14-objects-and-companions.md)).
> **Suggestion — `detekt/AbstractClassCanBeConcreteClass` covers this, but it is absent from detekt 1.23.8's default config (the docs site is ahead of the latest stable release). Enable it once your detekt version ships it; see chapter 47.**, whose
> own wording is "Abstract classes which do not define any `abstract` members
> should instead be refactored into concrete classes." The neighbouring
> `detekt/UtilityClassWithPublicConstructor` catches the namespace variant.

```kotlin
// bad — nothing is abstract; this is a concrete class wearing a costume
abstract class HttpDefaults {
    val connectTimeoutMillis: Long = 5_000L
    val readTimeoutMillis: Long = 30_000L
}

// good — it is a set of constants, so make it an object
object HttpDefaults {
    const val CONNECT_TIMEOUT_MILLIS: Long = 5_000L
    const val READ_TIMEOUT_MILLIS: Long = 30_000L
}
```

## 10.10 Expose an interface's read-only data as an abstract property, not a `getX()` function.

> Why? The
> [coding conventions on functions versus properties](https://kotlinlang.org/docs/coding-conventions.html#functions-vs-properties)
> give the test: prefer a property when the underlying algorithm "does not
> throw", "is cheap to calculate (or cached on the first run)", and "returns
> the same result over invocations if the object state hasn't changed." A
> `getName()` function on an interface fails no part of that test — it is a
> property written in Java's spelling, and it costs every implementor the
> chance to satisfy it with `override val name: String` in the constructor
> header. **Suggestion.**

```kotlin
// bad — Java spelling; every implementor must write a function body
interface Tenant {
    fun getId(): String

    fun getDisplayName(): String
}

class DbTenant(private val id: String, private val displayName: String) : Tenant {
    override fun getId(): String = id

    override fun getDisplayName(): String = displayName
}

// good — the implementor satisfies the contract in its constructor header
interface Tenant {
    val id: String

    val displayName: String
}

class DbTenant(override val id: String, override val displayName: String) : Tenant
```

## 10.11 Never fake per-instance state behind an interface property; an interface property has no backing field.

> Why? An interface property can only ever have a computed accessor — there
> is no field to store into. Code that wants state anyway reaches for a
> file-level or companion-level map keyed by `this`, which is a memory leak
> (nothing is ever removed), a thread-safety hazard (the map is unsynchronized),
> and a correctness bug the moment an implementor overrides `equals`, because
> two equal instances then collide on one entry. Declare the property abstract
> and let each implementor own the storage. Backing fields in general are
> [Chapter 17](17-properties-and-backing-fields.md). **Suggestion.**

```kotlin
// bad — a file-level map standing in for the backing field the interface cannot have
private val auditIds = mutableMapOf<Auditable, String>()

interface Auditable {
    val auditId: String
        get() = auditIds.getOrPut(this) { "audit-${auditIds.size}" }
}

// good — the interface states the contract; the implementor supplies the storage
interface Auditable {
    val auditId: String
}

class Invoice(override val auditId: String, val amountMinor: Long) : Auditable
```

## 10.12 Order a class's contents: property declarations and initializer blocks, then secondary constructors, then methods, then the companion object.

> Why? The
> [coding conventions on class layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout)
> fix exactly this order, and add two refinements worth quoting: "Do not sort
> the method declarations alphabetically or by visibility, and do not separate
> regular methods from extension methods. Instead, put related stuff together",
> and "Put nested classes next to the code that uses those classes. If the
> classes are intended to be used externally and aren't referenced inside the
> class, put them in the end, after the companion object." When implementing
> an interface, the
> [interface implementation layout](https://kotlinlang.org/docs/coding-conventions.html#interface-implementation-layout)
> rule adds that you should "keep the implementing members in the same order as
> members of the interface", and the
> [overload layout](https://kotlinlang.org/docs/coding-conventions.html#overload-layout)
> rule that you should "always put overloads next to each other in a class."
> **Violation — enforced by `detekt/ClassOrdering`**, which is *not* active in
> detekt's default configuration; enable it explicitly (see
> [Chapter 47](47-ktlint-and-detekt.md)).

```kotlin
// bad — companion first, init stranded below the methods, overloads split apart
class Ledger(private val currency: String) {
    companion object {
        fun empty(currency: String): Ledger = Ledger(currency)
    }

    fun post(amountMinor: Long) { /* ... */ }

    private val entries = mutableListOf<Long>()

    fun post(amountMinor: Long, note: String) { /* ... */ }

    init {
        require(currency.length == 3) { "currency must be an ISO 4217 code" }
    }
}

// good
class Ledger(private val currency: String) {
    private val entries = mutableListOf<Long>()

    init {
        require(currency.length == 3) { "currency must be an ISO 4217 code" }
    }

    fun post(amountMinor: Long) { /* ... */ }

    fun post(amountMinor: Long, note: String) { /* ... */ }

    companion object {
        fun empty(currency: String): Ledger = Ledger(currency)
    }
}
```

## 10.13 Keep a nested class plain; add `inner` only when it genuinely needs the enclosing instance.

> Why? The
> [nested classes docs](https://kotlinlang.org/docs/nested-classes.html) are
> blunt about the cost: "Inner classes carry a reference to an object of an
> outer class." That hidden field keeps the whole outer object alive for as
> long as any inner instance survives — which is how a short-lived request
> object ends up pinned in a long-lived cache, and how a nested class becomes
> silently unserializable. A plain nested class has no such reference, so make
> `inner` a deliberate choice rather than a reflex imported from Java, where
> the default is the other way round.
> **Violation — enforced by `detekt/UnnecessaryInnerClass`** ("Nested classes
> that do not access members from the outer class do not require the `inner`
> qualifier"), which is *not* active by default. `detekt/NestedClassesVisibility`
> is active by default and covers the adjacent case of a misleading explicit
> `public` on a nested class inside an `internal` one.

```kotlin
// bad — `inner` is unnecessary, and every Page pins the whole ReportBuilder,
// including its buffer, for as long as the page is referenced
class ReportBuilder(private val buffer: StringBuilder) {
    inner class Page(val number: Int, val lines: List<String>)

    fun page(number: Int, lines: List<String>): Page = Page(number, lines)
}

// good — no hidden outer reference; Page can outlive the builder harmlessly
class ReportBuilder(private val buffer: StringBuilder) {
    class Page(val number: Int, val lines: List<String>)

    fun page(number: Int, lines: List<String>): Page = Page(number, lines)
}
```

## 10.14 Compose, and let `by` forward what you did not override, instead of inheriting to reuse an implementation.

> Why? Inheriting from a concrete class binds you to the *sequence of internal
> calls* the superclass happens to make today, not just to its published
> behaviour — the classic demonstration being a counting list whose `addAll`
> double-counts because the superclass's `addAll` loops through `add`. It also
> drags the entire supertype's API into yours, so every method you never
> thought about is now part of your contract. Kotlin makes the alternative
> cheap: `by` generates the forwarding methods you would otherwise write by
> hand, and members you do override are *not* called from the delegate. See
> [Chapter 16](16-delegation.md) for the full semantics, including the
> deliberate limitation that the delegate never sees your overrides.
> **Suggestion.**

```kotlin
// bad — ArrayList.addAll calls add internally, so addCount is doubled
class InstrumentedList<E> : ArrayList<E>() {
    var addCount: Int = 0
        private set

    override fun add(element: E): Boolean {
        addCount++
        return super.add(element)
    }

    override fun addAll(elements: Collection<E>): Boolean {
        addCount += elements.size
        return super.addAll(elements)
    }
}

// good — the delegate's internals are none of our business
class InstrumentedList<E>(
    private val delegate: MutableList<E> = mutableListOf(),
) : MutableList<E> by delegate {

    var addCount: Int = 0
        private set

    override fun add(element: E): Boolean {
        addCount++
        return delegate.add(element)
    }

    override fun addAll(elements: Collection<E>): Boolean {
        addCount += elements.size
        return delegate.addAll(elements)
    }
}
```

## 10.15 Close the primary constructor with `private constructor` when every instance must come through a factory.

> Why? A factory that documents itself as "the way to build one of these" is
> advisory until the constructor is closed; a public constructor next to it is
> a second, unvalidated entry point that will eventually be used. Kotlin's
> spelling puts the modifier on the header — `class Foo private constructor(...)`
> — and the language docs note the empty-header form for the case where the
> class takes no arguments at all: "declare an empty primary constructor with
> non-default visibility." Note that this rule does **not** transfer to `data`
> classes, where the generated `copy()` reopens the hole — see
> [§11.9](11-data-classes.md). **Suggestion.**

```kotlin
// bad — the factory validates, and the constructor next to it does not
class SessionToken(val value: String, val expiresAtEpochSeconds: Long) {
    companion object {
        fun issue(value: String, ttlSeconds: Long): SessionToken {
            require(value.length >= 32) { "token too short" }
            return SessionToken(value, System.currentTimeMillis() / 1000 + ttlSeconds)
        }
    }
}

val forged = SessionToken("x", Long.MAX_VALUE) // compiles; skips every check

// good — one door
class SessionToken private constructor(
    val value: String,
    val expiresAtEpochSeconds: Long,
) {
    companion object {
        fun issue(value: String, ttlSeconds: Long): SessionToken {
            require(value.length >= 32) { "token too short" }
            return SessionToken(value, System.currentTimeMillis() / 1000 + ttlSeconds)
        }
    }
}
```

## 10.16 Keep an interface narrow enough that every implementor needs every member.

> Why? Each member you add to an interface is a member every implementor must
> supply and every test double must stub — including the implementors for
> which it is meaningless and which therefore return `null`, throw
> `UnsupportedOperationException`, or quietly do nothing. Those degenerate
> implementations are a reliable source of production surprises. Split the
> interface along the lines its implementors actually fall on; a class can
> implement several.
> **Violation — enforced by `detekt/ComplexInterface`**, which flags interfaces
> whose member count exceeds `allowedDefinitions` (default 10) and which is
> *not* active in detekt's default configuration; enable it explicitly (see
> [Chapter 47](47-ktlint-and-detekt.md)).

```kotlin
// bad — a read-only report store must still implement four write methods
interface DocumentStore {
    fun read(id: String): ByteArray?

    fun list(prefix: String): List<String>

    fun write(id: String, bytes: ByteArray)

    fun delete(id: String)

    fun setRetention(id: String, days: Int)

    fun purgeExpired(): Int
}

// good — split along the line implementors actually fall on
interface DocumentReader {
    fun read(id: String): ByteArray?

    fun list(prefix: String): List<String>
}

interface DocumentWriter {
    fun write(id: String, bytes: ByteArray)

    fun delete(id: String)
}

interface RetentionPolicyStore {
    fun setRetention(id: String, days: Int)

    fun purgeExpired(): Int
}
```

## 10.17 Never let `this` escape from a constructor or an `init` block.

> Why? Until the last property initializer has run, `this` refers to a
> half-built object. Registering it with a listener registry, handing it to an
> executor, or assigning it to a shared field from inside `init` publishes that
> half-built state to whoever picks it up — and on the JVM, another thread may
> observe non-nullable properties as `null` because the `final` field writes
> have not been made visible. Construct fully, then publish, which is exactly
> what a factory function is for (§10.3, §10.15). **Suggestion** — nothing
> detects this mechanically.

```kotlin
// bad — the bus may deliver a tick before `threshold` is assigned
class PriceWatcher(bus: EventBus, threshold: Long) : TickListener {
    init {
        bus.register(this)
    }

    private val threshold: Long = threshold

    override fun onTick(priceMinor: Long) {
        if (priceMinor > threshold) { /* ... */ }
    }
}

// good — fully constructed before anyone can see it
class PriceWatcher private constructor(private val threshold: Long) : TickListener {
    override fun onTick(priceMinor: Long) {
        if (priceMinor > threshold) { /* ... */ }
    }

    companion object {
        fun attach(bus: EventBus, threshold: Long): PriceWatcher =
            PriceWatcher(threshold).also(bus::register)
    }
}
```
