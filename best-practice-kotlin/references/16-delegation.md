<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 16. Delegation

Kotlin spells two unrelated features with the same keyword. **Class
delegation** — `class Derived(b: Base) : Base by b` — makes the compiler
generate forwarding implementations of every member of an interface, which
turns "composition over inheritance" from a paragraph of boilerplate into a
one-liner. **Property delegation** — `val x: T by someDelegate` — routes a
property's `get`/`set` through an object that implements `getValue` and
`setValue`. This chapter covers both, in that order, and then the delegates
the standard library ships: `lazy`, `Delegates.observable`,
`Delegates.vetoable`, `Delegates.notNull`, and map-backed properties.

The rules draw from
[Delegation](https://kotlinlang.org/docs/delegation.html) and
[Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
in the Kotlin language documentation, and from the Kotlin coding conventions
on [immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability).
Neither style guide legislates delegation, so most rules here are grounded in
the language reference rather than in a normative style rule.

Two neighbouring topics are deferred. The **backing-property pattern** —
`private val _items: MutableList<T>` behind a public `List<T>` — and
**explicit backing fields** are [Chapter 17, Properties & Backing
Fields](17-properties-and-backing-fields.md); §16.5 only covers the case
where `by lazy` replaces that pattern outright. **`lateinit` and nullability
generally** are [Chapter 6, Null Safety](06-null-safety.md); §16.10 gives the
decision table for choosing between `lazy`, `lateinit`, and a nullable
`var`, and nothing more.

**Tool alignment:** almost nothing in this chapter is mechanically checkable.
`detekt/LateinitUsage` (style ruleset, disabled by default) is the one rule
that touches §16.10, by flagging every `lateinit` so a reviewer has to
justify it. Every other rule below is a **Suggestion** — a fabricated
`> Enforced by:` callout would be worse than none.

## 16.1 Implement an interface by forwarding to a member with `by` rather than by subclassing an implementation you only wanted to reuse.

> Why? [Delegation](https://kotlinlang.org/docs/delegation.html) states that
> "the compiler will generate all the methods of `Base` that forward to `b`."
> Subclassing to reuse one method drags in every other member of the base
> class, including the ones added in its next release, and welds your type to
> a single implementation forever. Delegation gives you the same reuse with
> an interface-shaped seam: the collaborator arrives as a constructor
> argument, so a test can hand in a fake. **Suggestion.**

```kotlin
interface EventSink {
    fun emit(event: Event)
    fun flush()
}

// bad — subclassing purely to reuse emit(); CountingSink now inherits every
// present and future member of BufferedSink, and can never wrap anything else
open class BufferedSink : EventSink {
    override fun emit(event: Event) { /* ... */ }
    override fun flush() { /* ... */ }
}

class CountingSink : BufferedSink() {
    var count = 0
        private set

    override fun emit(event: Event) {
        count++
        super.emit(event)
    }
}

// good — forward everything you have no opinion about, override only emit()
class CountingSink(private val delegate: EventSink) : EventSink by delegate {
    var count = 0
        private set

    override fun emit(event: Event) {
        count++
        delegate.emit(event)
    }
}
```

## 16.2 Treat the delegate as captured at construction: never delegate to a `var` and expect a later reassignment to be seen.

> Why? The `by` clause stores the *value* of the expression in a synthetic
> field when the object is built —
> [Delegation](https://kotlinlang.org/docs/delegation.html) says "`b` will be
> stored internally in objects of `Derived`". If you write
> `class Scheduler(var clock: Clock) : Clock by clock`, you end up with two
> separate stores of the same reference: the property, and the hidden field
> the generated forwarders actually read. Reassigning `clock` updates the
> property and changes nothing any caller of a forwarded member can observe.
> **Suggestion.**

```kotlin
interface Clock {
    fun now(): Instant
}

// bad — two copies of the reference; `by clock` captured the constructor
// argument, so scheduler.clock = TestClock() has no effect on now()
class Scheduler(var clock: Clock) : Clock by clock

val scheduler = Scheduler(SystemClock)
scheduler.clock = TestClock(Instant.EPOCH)
scheduler.now() // still the system clock

// good — one source of truth; forward by hand when the target can change
class Scheduler(private var clock: Clock) : Clock {
    override fun now(): Instant = clock.now()

    fun retarget(newClock: Clock) {
        clock = newClock
    }
}
```

## 16.3 Do not override a member that the delegate's own implementation depends on.

> Why? The Kotlin documentation is explicit: "members overridden in this way
> do not get called from the members of the delegate object, which can only
> access its own implementations of the interface members"
> ([Overriding a member of an interface implemented by
> delegation](https://kotlinlang.org/docs/delegation.html#overriding-a-member-of-an-interface-implemented-by-delegation)).
> Your override wins for direct calls from outside and loses for every call
> the delegate makes internally, so the object has two answers to the same
> question depending on who asks. Parameterise the implementation instead.
> **Suggestion.**

```kotlin
interface Formatter {
    val prefix: String
    fun format(message: String): String
}

class DefaultFormatter : Formatter {
    override val prefix: String = "default"
    override fun format(message: String): String = "[$prefix] $message"
}

// bad — prefix is overridden, but format() runs inside the delegate and reads
// the delegate's own prefix
class AuditFormatter(delegate: Formatter) : Formatter by delegate {
    override val prefix: String = "audit"
}

AuditFormatter(DefaultFormatter()).prefix           // "audit"
AuditFormatter(DefaultFormatter()).format("hi")     // "[default] hi"

// good — the varying part is an argument to the implementation, so there is
// exactly one source of truth
class PrefixedFormatter(override val prefix: String) : Formatter {
    override fun format(message: String): String = "[$prefix] $message"
}

val audit: Formatter = PrefixedFormatter("audit")
audit.format("hi")                                   // "[audit] hi"
```

## 16.4 Remember that `by` forwards only the interface's own members — `equals`, `hashCode`, and `toString` are not among them.

> Why? Class delegation generates forwarders for the members declared on the
> delegated interface. `equals`, `hashCode`, and `toString` are declared on
> `Any`, not on your interface, so the wrapper inherits the identity-based
> versions. Two wrappers around equal delegates compare unequal, a `Set` of
> wrappers silently accepts duplicates, and log lines print
> `Wrapped@6d06d69c`. **Suggestion.** See [Chapter 23, Equality &
> Ordering](23-equality-and-ordering.md) for the general contract.

```kotlin
interface Money {
    val minorUnits: Long
}

class Cash(override val minorUnits: Long) : Money {
    override fun equals(other: Any?): Boolean = other is Cash && other.minorUnits == minorUnits
    override fun hashCode(): Int = minorUnits.hashCode()
    override fun toString(): String = "Cash($minorUnits)"
}

// bad — identity equality leaks through the wrapper
class Audited(private val delegate: Money) : Money by delegate

Audited(Cash(500)) == Audited(Cash(500))   // false
setOf(Audited(Cash(500)), Audited(Cash(500))).size  // 2
println(Audited(Cash(500)))                // Audited@6d06d69c

// good — forward the Any members deliberately, or do not wrap a value type
class Audited(private val delegate: Money) : Money by delegate {
    override fun equals(other: Any?): Boolean = other is Audited && other.delegate == delegate
    override fun hashCode(): Int = delegate.hashCode()
    override fun toString(): String = "Audited($delegate)"
}
```

## 16.5 Use `by lazy` for a value that is expensive and computed once, instead of a nullable field plus a null check.

> Why?
> [Lazy properties](https://kotlinlang.org/docs/delegated-properties.html#lazy-properties)
> gives you memoisation, thread safety, and a non-nullable type in one
> declaration. The hand-rolled equivalent needs a nullable backing field, a
> custom getter, an unreachable error branch to satisfy the type checker, and
> a comment explaining the invariant — and it is not thread-safe unless you
> write the locking yourself. Note that the Android style guide's
> [backing properties](https://developer.android.com/kotlin/style-guide#backing_properties)
> section shows exactly this hand-rolled shape, but it is illustrating the
> *naming* convention, not recommending the mechanism. **Suggestion.**

```kotlin
// bad — three members, no thread safety, and an "unreachable" branch that only
// exists to convince the compiler
class Registry {
    private var _table: Map<String, Handler>? = null

    val table: Map<String, Handler>
        get() {
            if (_table == null) {
                _table = loadTable()
            }
            return _table ?: error("unreachable")
        }
}

// good — one declaration; the type is non-null and the value is computed once
class Registry {
    val table: Map<String, Handler> by lazy { loadTable() }
}
```

## 16.6 Choose the `LazyThreadSafetyMode` deliberately; do not drop to `NONE` unless single-threaded first access is guaranteed.

> Why? `lazy { ... }` defaults to `LazyThreadSafetyMode.SYNCHRONIZED`, which
> locks so the initializer runs exactly once and every thread sees the same
> value. `PUBLICATION` allows the initializer to run concurrently but
> publishes only the first result — correct only if the initializer is
> side-effect-free and producing a throwaway instance is acceptable. `NONE`
> uses no locks at all: the standard library says "If the instance is accessed
> from multiple threads, its behavior is *unspecified*"
> ([`LazyThreadSafetyMode`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/)).
> Unspecified is stronger than "may compute twice" — with no synchronization
> there is no happens-before edge, so another thread can observe a partially
> constructed object. **Suggestion.**

| Mode | Initializer runs | Safe across threads | Use when |
|---|---|---|---|
| `SYNCHRONIZED` (default) | exactly once | yes | anything shared; the default is correct |
| `PUBLICATION` | possibly more than once | yes, one value wins | initializer is pure and cheap to repeat |
| `NONE` | once, unsynchronised | **no** | provably confined to one thread |

```kotlin
// bad — NONE chosen for "performance" on a property read from the request
// thread pool; two threads can race and one can see a half-built parser
class SchemaCache {
    val parser: SchemaParser by lazy(LazyThreadSafetyMode.NONE) { SchemaParser(load()) }
}

// good — shared state keeps the synchronised default
class SchemaCache {
    val parser: SchemaParser by lazy { SchemaParser(load()) }
}

// good — NONE is fine here because the object is confined to one coroutine
class RequestScopedView(private val raw: ByteArray) {
    val decoded: String by lazy(LazyThreadSafetyMode.NONE) { raw.decodeToString() }
}
```

## 16.7 Use `Delegates.observable` when a change must trigger a side effect, and keep the handler trivial.

> Why?
> [Observable properties](https://kotlinlang.org/docs/delegated-properties.html#observable-properties)
> fires the handler *after* every assignment, including assignments of the
> same value. That is the right tool for "notify a listener" and the wrong
> tool for anything that can fail, block, or reenter — a handler that itself
> writes the property recurses, and a handler that throws leaves the property
> already updated. **Suggestion.**

```kotlin
// bad — the handler does real work on the setter's thread, and reassigning
// inside it recurses
var status: Status by Delegates.observable(Status.IDLE) { _, old, new ->
    auditLog.write(old, new)                 // blocking I/O in a setter
    if (new == Status.FAILED) status = Status.IDLE  // infinite recursion
}

// good — the handler only publishes; policy lives in the collector
var status: Status by Delegates.observable(Status.IDLE) { _, old, new ->
    if (old != new) listeners.forEach { it.onStatusChanged(new) }
}
```

## 16.8 Do not use `Delegates.vetoable` to reject invalid input — a veto is silent.

> Why? `vetoable`'s handler runs *before* the assignment and returns `false`
> to discard it. Discarding is not rejecting: the caller's `obj.retries = -1`
> completes normally, the property keeps its old value, and nothing tells
> anyone the write was ignored. Use `require` in a custom setter (or in the
> constructor) so an invalid value is a loud `IllegalArgumentException` at
> the call site. Reserve `vetoable` for genuine "clamp to the last valid
> state" semantics where dropping the write is the specified behaviour.
> **Suggestion.**

```kotlin
// bad — the caller has no way to learn the write was thrown away
var retries: Int by Delegates.vetoable(3) { _, _, new -> new >= 0 }

config.retries = -1
println(config.retries)  // 3 — looks like the assignment never happened

// good — fail where the mistake was made
var retries: Int = 3
    set(value) {
        require(value >= 0) { "retries must be >= 0, was $value" }
        field = value
    }
```

## 16.9 Do not use `Delegates.notNull()` where a constructor parameter or `lateinit` would do.

> Why? `Delegates.notNull<T>()` gives you a non-null `var` that throws
> `IllegalStateException` if read before it is written. It exists for the
> narrow case that `lateinit` cannot cover: a primitive type, which
> `lateinit` forbids. For everything else it costs an extra heap object per
> property, hides the initialization requirement behind a delegate, and gives
> a worse error message than `lateinit`'s
> `UninitializedPropertyAccessException`. If the value is known at
> construction, it belongs in the constructor. **Suggestion.**

```kotlin
// bad — the value is available at construction; the delegate adds an object
// and a failure mode for nothing
class Session {
    var userId: String by Delegates.notNull()
}

val session = Session().apply { userId = id }

// good
class Session(val userId: String)

// good — notNull() earns its place only for a primitive assigned later by a
// framework, where lateinit is not allowed
class Benchmark {
    var iterations: Int by Delegates.notNull()   // lateinit var Int does not compile
}
```

## 16.10 Choose between `lazy`, `lateinit`, and a nullable `var` from the table, not from habit.

> Why? All three express "not available yet", and they are not
> interchangeable. `by lazy` is for a value *this object* can compute on
> demand; it is `val`, thread-safe by default, and can never be observed
> uninitialized. `lateinit var` is for a value *someone else* injects before
> first read; it is mutable, non-null, and throws
> `UninitializedPropertyAccessException` if that contract is broken. A
> nullable `var` is for a value whose absence is a legitimate, ongoing state
> the caller must handle. Picking `lateinit` because you did not want to
> write `?.` is the failure mode this table exists to prevent — see
> [Chapter 6](06-null-safety.md). **Suggestion.** `detekt/LateinitUsage`
> (style ruleset, off by default) surfaces every `lateinit` for review.

| | `by lazy` | `lateinit var` | nullable `var` |
|---|---|---|---|
| Mutability | `val` | `var` | `var` |
| Who supplies the value | this object | an external caller/framework | an external caller |
| Absence is a valid state | no | no | **yes** |
| Read before init | impossible | `UninitializedPropertyAccessException` | returns `null` |
| Primitives allowed | yes | **no** | yes (boxed) |
| Thread-safe by default | yes | no | no |
| Typical use | expensive derived value, cached config | Spring/JUnit field injection, `@BeforeEach` setup | optional field, "not loaded yet" cache |

```kotlin
// bad — lateinit used to dodge nullability; "no avatar" is a real state and the
// property throws instead of returning null
class Profile {
    lateinit var avatarUrl: String
}

// good — absence is part of the domain
class Profile {
    var avatarUrl: String? = null
}

// good — this object can compute it
class Profile(private val userId: UserId) {
    val displayName: String by lazy { directory.lookup(userId).fullName }
}

// good — the framework assigns it before any test body runs
class OrderServiceTest {
    private lateinit var service: OrderService

    @BeforeEach
    fun setUp() {
        service = OrderService(FakeRepository())
    }
}
```

## 16.11 Delegate properties to a `Map` only for genuinely dynamic data, never as a shortcut for declaring a class.

> Why?
> [Storing properties in a map](https://kotlinlang.org/docs/delegated-properties.html#storing-properties-in-a-map)
> reads each property out of a map keyed by the property's own name. That is
> useful when the shape really is dynamic (a parsed JSON envelope, a
> config bag). It is a trap when the shape is known: a missing key throws
> `NoSuchElementException` on *read* rather than on construction, and a
> wrong value type throws `ClassCastException` at the access site because the
> cast is unchecked. Both failures land far from the data that caused them.
> **Suggestion.**

```kotlin
// bad — a known-shape DTO built out of a map; typos and type errors survive
// until something reads the property
class User(private val map: Map<String, Any?>) {
    val name: String by map
    val age: Int by map
}

val user = User(mapOf("name" to "Ada", "years" to 36))
user.age    // NoSuchElementException: Key age is missing in the map

// good — the shape is known, so declare it and let construction fail fast
data class User(val name: String, val age: Int)

// good — map delegation for data that is genuinely dynamic at runtime
class FeatureFlags(private val raw: Map<String, Any?>) {
    val darkMode: Boolean by raw
    val betaRollout: Double by raw
}
```

## 16.12 Write a custom delegate by implementing `ReadOnlyProperty` or `ReadWriteProperty`, not by hand-rolling the operator functions.

> Why? A delegate only needs `operator fun getValue` (and `setValue` for a
> `var`) with the signatures in
> [Property delegate
> requirements](https://kotlinlang.org/docs/delegated-properties.html#property-delegate-requirements),
> so an ad-hoc class works. But the interfaces state the intent in the type,
> make the read-only/read-write distinction visible at the declaration site,
> and give you the exact parameter list the compiler expects rather than one
> you have to remember. `ReadOnlyProperty` is a `fun interface`, so the
> read-only case is a lambda. **Suggestion.**

```kotlin
import kotlin.properties.ReadOnlyProperty
import kotlin.properties.ReadWriteProperty
import kotlin.reflect.KProperty

// bad — correct, but nothing in the type says what this is, and a typo in the
// signature fails with a confusing "missing getValue" error at the use site
class Trimmed {
    private var current: String = ""

    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = current

    operator fun setValue(thisRef: Any?, property: KProperty<*>, newValue: String) {
        current = newValue.trim()
    }
}

// good
class Trimmed : ReadWriteProperty<Any?, String> {
    private var current: String = ""

    override fun getValue(thisRef: Any?, property: KProperty<*>): String = current

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        current = value.trim()
    }
}

// good — read-only delegates are a SAM conversion away
fun envVar(name: String): ReadOnlyProperty<Any?, String?> =
    ReadOnlyProperty { _, _ -> System.getenv(name) }
```

## 16.13 Implement `provideDelegate` when the delegate needs the property's name or owner at creation time.

> Why?
> [Providing a delegate](https://kotlinlang.org/docs/delegated-properties.html#providing-a-delegate)
> exists so validation can happen when the object is built rather than the
> first time the property is read. Without it, a delegate that derives a
> configuration key from `property.name` cannot discover a missing key until
> someone reads that property — possibly in production, possibly never in
> tests. `provideDelegate` runs in the constructor, so a missing key is a
> construction failure. **Suggestion.**

```kotlin
// bad — the key is only checked on first read, so a typo can ship
class ConfigKey<T>(private val parse: (String) -> T) : ReadOnlyProperty<Config, T> {
    override fun getValue(thisRef: Config, property: KProperty<*>): T =
        parse(thisRef.require(property.name))
}

// good — every key is validated when the Config object is constructed
class ConfigKey<T>(private val parse: (String) -> T) {
    operator fun provideDelegate(
        thisRef: Config,
        property: KProperty<*>,
    ): ReadOnlyProperty<Config, T> {
        val key = property.name
        require(thisRef.contains(key)) { "missing configuration key: $key" }
        return ReadOnlyProperty { config, _ -> parse(config.raw(key)) }
    }
}

class Config(private val values: Map<String, String>) {
    fun contains(key: String): Boolean = key in values
    fun raw(key: String): String = values.getValue(key)

    val port: Int by ConfigKey(String::toInt)
    val host: String by ConfigKey { it }
}
```

## 16.14 Do not put a delegate on a hot property without accounting for its cost.

> Why? The
> [translation rules](https://kotlinlang.org/docs/delegated-properties.html#translation-rules-for-delegated-properties)
> spell out what a delegated property compiles to: a hidden
> `prop$delegate` field holding the delegate instance, and accessors that
> call `prop$delegate.getValue(this, this::prop)` — passing a `KProperty`
> reference on every access. That is one extra object per delegated property
> per instance, plus a virtual call and a reflection object where a plain
> field read would have been a `getfield`. For a `val` in a request-scoped
> object it is invisible; for a property read a million times a second in a
> value type it is not. **Suggestion.** See [Chapter 12, Value
> Classes](12-value-classes.md) for the allocation-sensitive case.

```kotlin
// bad — four Lazy objects allocated per Point, for four trivial computations
class Point(val x: Double, val y: Double) {
    val magnitude: Double by lazy { hypot(x, y) }
    val angle: Double by lazy { atan2(y, x) }
    val unitX: Double by lazy { x / magnitude }
    val unitY: Double by lazy { y / magnitude }
}

// good — computed properties with no delegate, no field, no allocation
class Point(val x: Double, val y: Double) {
    val magnitude: Double get() = hypot(x, y)
    val angle: Double get() = atan2(y, x)
    val unitX: Double get() = x / magnitude
    val unitY: Double get() = y / magnitude
}
```

## 16.15 Use a local delegated property to defer work that a branch may never need.

> Why?
> [Local delegated
> properties](https://kotlinlang.org/docs/delegated-properties.html#local-delegated-properties)
> let `by lazy` apply to a local variable, so an expensive value inside a
> function is computed on first read and not at all if no branch reaches it.
> The alternative — hoisting the call above the `if` — pays for it
> unconditionally; the other alternative — a nullable local plus a null check
> in each branch — reintroduces exactly the boilerplate §16.5 removes.
> **Suggestion.**

```kotlin
// bad — the snapshot is loaded even when the fast path returns immediately
fun render(request: Request): Response {
    val snapshot = loadSnapshot(request.id)   // expensive, often unused
    if (request.isCached) {
        return cachedResponse(request)
    }
    return renderFrom(snapshot)
}

// good — loadSnapshot runs only when the slow path is actually taken
fun render(request: Request): Response {
    val snapshot by lazy { loadSnapshot(request.id) }
    if (request.isCached) {
        return cachedResponse(request)
    }
    return renderFrom(snapshot)
}
```

## 16.16 Do not write a delegate where a function, a computed property, or a constructor parameter says it more plainly.

> Why? A delegate adds a type, an allocation, and a level of indirection that
> a reader has to follow before they can answer "what does this property
> return?". That price buys something real for `lazy` or for a delegate
> reused across a dozen properties. It buys nothing for a one-off
> transformation that a custom getter expresses in one line, and it actively
> obscures a value that should simply have been passed in. **Suggestion.**

```kotlin
// bad — a bespoke delegate used exactly once, to uppercase a string
class Uppercased(private val source: () -> String) : ReadOnlyProperty<Any?, String> {
    override fun getValue(thisRef: Any?, property: KProperty<*>): String = source().uppercase()
}

class Account(private val rawCode: String) {
    val code: String by Uppercased { rawCode }
}

// good
class Account(private val rawCode: String) {
    val code: String get() = rawCode.uppercase()
}

// better still — normalise once, at the boundary, and store the result
class Account(rawCode: String) {
    val code: String = rawCode.uppercase()
}
```
