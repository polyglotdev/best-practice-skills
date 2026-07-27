<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 17. Properties & Backing Fields

A Kotlin property is not a Java field. It is a getter, optionally a setter,
and *optionally* a field — and which of the three you get depends entirely on
what you wrote. Getting this wrong produces the two most common property bugs
in Kotlin: an accessor that recurses into itself forever, and a "read-only"
`List` that a caller can still mutate through the reference you handed them.

This chapter covers the property/function boundary, custom accessors and the
`field` identifier, the backing-property pattern and the explicit backing
fields that replace it (Stable since Kotlin 2.4), initialization order,
`const val`, extension properties, and
what a mutable property in a public API costs you. It draws from
[Properties](https://kotlinlang.org/docs/properties.html) in the language
reference, the Kotlin coding conventions on
[functions vs properties](https://kotlinlang.org/docs/coding-conventions.html#functions-vs-properties),
[names for backing properties](https://kotlinlang.org/docs/coding-conventions.html#names-for-backing-properties),
and
[coding conventions for libraries](https://kotlinlang.org/docs/coding-conventions.html#coding-conventions-for-libraries),
and from the Android Kotlin style guide on
[backing properties](https://developer.android.com/kotlin/style-guide#backing_properties)
and
[implicit return/property types](https://developer.android.com/kotlin/style-guide#implicit_returnproperty_types).

Four neighbouring topics are deferred. **Property naming** — camelCase,
`SCREAMING_SNAKE_CASE` for constants, the `is`/`has` prefix for Booleans — is
[Chapter 3, Naming](03-naming.md). **Delegated properties**, including
`by lazy` and the `lazy` / `lateinit` / nullable decision table, are
[Chapter 16, Delegation](16-delegation.md). **Read-only collection interfaces
at API boundaries** are [Chapter 25, Immutability](25-immutability.md);
§17.6 covers only the aliasing hazard specific to backing properties.
**`@JvmField`, `@get:JvmName`, and how Kotlin properties appear to Java
callers** are [Chapter 28, Java Interop](28-java-interop.md).

**Tool alignment:** `ktlint/standard:property-naming` and
`ktlint/standard:backing-property-naming` enforce the naming half of §17.5 —
the latter exists specifically so a private backing property may start with
`_` without tripping the general rule. detekt's naming ruleset adds
`detekt/TopLevelPropertyNaming`, `detekt/ObjectPropertyNaming`,
`detekt/BooleanPropertyNaming`, and `detekt/NonBooleanPropertyPrefixedWithIs`.
`detekt/LateinitUsage` (style ruleset, off by default) surfaces every
`lateinit` for §17.14. Rules those checks cover are marked **Violation**;
everything else is a **Suggestion**, because no linter can tell whether a
getter is cheap or whether a `var` should have been a `val`.

## 17.1 Use a property when the computation is cheap, cannot throw, and returns the same result while the object is unchanged; otherwise use a function.

> Why? The Kotlin coding conventions give the test directly: prefer a
> property when the algorithm "does not throw", "is cheap to calculate (or
> cached on the first run)", and "returns the same result over invocations if
> the object state hasn't changed"
> ([Functions vs
> properties](https://kotlinlang.org/docs/coding-conventions.html#functions-vs-properties)).
> A property reads as a field at the call site, so callers put it in string
> templates, in log lines, and inside loops without thinking. A property that
> opens a socket or throws on the third read violates every expectation that
> syntax creates. **Suggestion.**

```kotlin
// bad — reads as a field, performs a network call, and throws
val Account.balance: Money
    get() = ledgerClient.fetchBalance(id)

logger.info("balance is ${account.balance}")   // I/O inside a log statement

// good — the parenthesis warns the reader that something happens
fun Account.fetchBalance(): Money = ledgerClient.fetchBalance(id)

// good — cheap, total, stable: a property is right
val Account.isOverdrawn: Boolean
    get() = cachedBalance < Money.ZERO
```

## 17.2 Inside a custom accessor, refer to the storage with `field`, never with the property's own name.

> Why? `field` is the only identifier that reaches the backing field
> ([Backing fields](https://kotlinlang.org/docs/properties.html#backing-fields)).
> Writing the property name inside its own accessor calls the accessor
> again — the getter recurses until the stack overflows, and the setter
> recurses until it does. There is no compiler error for this; it is a
> `StackOverflowError` at runtime, on the first access. **Suggestion.**

```kotlin
// bad — infinite recursion in both directions. Note there is no initializer:
// neither accessor mentions `field`, so no backing field exists and `= 0`
// would itself be an error ("Initializer is not allowed here because this
// property has no backing field").
class Scoreboard {
    var score: Int
        get() = score                       // calls itself
        set(value) {
            score = value.coerceAtLeast(0)  // calls itself
        }
}

// good
class Scoreboard {
    var score: Int = 0
        set(value) {
            field = value.coerceAtLeast(0)
            logger.debug("score updated to {}", field)
        }
}
```

## 17.3 Do not write an accessor whose whole body is `field`.

> Why? An accessor that only reads or only assigns the backing field is
> exactly the accessor the compiler generates for you. Writing it out adds
> three lines that a reviewer must read and compare against the default
> before concluding that nothing unusual is happening. Delete it; if you
> later need real behaviour, add it then. **Suggestion.**

```kotlin
// bad — six lines that mean "var score: Int = 0"
class Scoreboard {
    var score: Int = 0
        get() = field
        set(value) {
            field = value
        }
}

// good
class Scoreboard {
    var score: Int = 0
}
```

## 17.4 Know which of your properties actually allocate storage: a backing field exists only when an accessor uses `field` or the default accessor is kept.

> Why? "Backing fields aren't created by default for all properties because
> they might not need them"
> ([Backing fields](https://kotlinlang.org/docs/properties.html#backing-fields)).
> A `val` with a custom getter and no `field` reference is pure computation:
> zero bytes per instance, recomputed on every read. A `val` with an
> initializer is storage: one slot per instance, computed once. Choosing the
> wrong one gives you either a hot loop recomputing a regex match, or a
> cached value that goes stale when the inputs change. **Suggestion.**

```kotlin
// bad — no backing field, so the regex is re-run on every single read
class Request(val path: String) {
    val segments: List<String>
        get() = path.split("/").filter { it.isNotEmpty() }
}

for (i in 0 until 1_000) {
    process(request.segments)   // 1000 splits of the same immutable string
}

// good — the input is immutable, so compute once into a field
class Request(val path: String) {
    val segments: List<String> = path.split("/").filter { it.isNotEmpty() }
}

// good — no field, because the value genuinely tracks mutable state
class Basket {
    private val lines = mutableListOf<Line>()

    val isEmpty: Boolean
        get() = lines.isEmpty()
}
```

## 17.5 Back a public read-only collection with a private mutable one named with a leading underscore.

> Why? The Kotlin coding conventions state the pattern and the naming rule
> together: "if a class has two properties which are conceptually the same
> but one is part of a public API and another is an implementation detail,
> use an underscore as the prefix for the name of the private property"
> ([Names for backing
> properties](https://kotlinlang.org/docs/coding-conventions.html#names-for-backing-properties)).
> The Android style guide adds that the name "should exactly match that of
> the real property except prefixed with an underscore"
> ([Backing properties](https://developer.android.com/kotlin/style-guide#backing_properties)).
> Exposing the `MutableList` directly lets any caller add to your internals
> without going through the method that maintains your invariants. Where the
> limitations allow it, §17.7's explicit backing field expresses the same
> thing with one name instead of two.
> **Violation — enforced by `ktlint/standard:backing-property-naming`** for
> the naming half; the pattern itself is a **Suggestion**.

```kotlin
// bad — every caller can mutate the list, bypassing addLine()'s validation
class Invoice {
    val lines = mutableListOf<Line>()

    fun addLine(line: Line) {
        require(line.quantity > 0) { "quantity must be positive" }
        lines += line
    }
}

invoice.lines += Line(quantity = -5)   // compiles; invariant broken

// good
class Invoice {
    private val _lines = mutableListOf<Line>()

    val lines: List<Line>
        get() = _lines.toList()

    fun addLine(line: Line) {
        require(line.quantity > 0) { "quantity must be positive" }
        _lines += line
    }
}
```

## 17.6 Remember that `get() = _items` hands out a live view, not a snapshot — copy when the caller must not observe later mutations.

> Why? `List` is a read-only *interface*, not an immutable *type*. Returning
> the `MutableList` under a `List` declaration means the caller's reference
> keeps changing under them while they iterate, which is a
> `ConcurrentModificationException` waiting for the right interleaving — and
> a caller who suspects what you did can recover the mutability with
> `(list as MutableList).add(...)`. `toList()` costs an allocation and closes
> both holes. Return the live view only when you have deliberately chosen
> cheap reads over isolation, and say so. **Suggestion.** See
> [Chapter 25, Immutability](25-immutability.md).

```kotlin
// bad — the returned "read-only" list is the internal list
class Basket {
    private val _items = mutableListOf<Item>()

    val items: List<Item>
        get() = _items

    fun add(item: Item) {
        _items += item
    }
}

val snapshot = basket.items
basket.add(Item("late arrival"))
snapshot.size                             // changed underneath the caller
(snapshot as MutableList<Item>).clear()   // succeeds — internals wiped

// good — a snapshot the caller owns
class Basket {
    private val _items = mutableListOf<Item>()

    val items: List<Item>
        get() = _items.toList()

    fun add(item: Item) {
        _items += item
    }
}
```

## 17.7 Prefer an explicit backing field over the two-property pattern — it is Stable as of Kotlin 2.4, and needs no opt-in flag.

> Why? A `field` declaration inside a property body lets one declaration carry
> a public read-only type and a private mutable implementation type
> ([Explicit backing
> fields](https://kotlinlang.org/docs/properties.html#explicit-backing-fields)),
> collapsing §17.5's `_city` / `city` pair into a single member with no second
> name to keep in sync. Inside the class, smart casting gives you the field's
> type, so `city.value = ...` works without a second property. Kotlin 2.4
> "promotes context parameters, explicit backing fields, and annotation
> use-site targets features to Stable"
> ([What's new in Kotlin 2.4.0](https://kotlinlang.org/docs/whatsnew24.html)),
> so no compiler flag is required — it was Experimental behind
> `-Xexplicit-backing-fields` only in Kotlin 2.3. The documented limitations
> are narrow: the property must have no custom getter, must be read-only
> (`val`), must not be `open`, must not be a delegated property, and must not
> be a compile-time constant; the field's type must be a subtype of the
> property's type and have `private` visibility. When any of those bites, fall
> back to §17.5. **Suggestion.**

```kotlin
// bad (when no §17.7 limitation applies) — two names for one piece of state,
// and _city is reachable from every member of the class even where only the
// read-only view was intended
class LocationViewModel {
    private val _city = MutableStateFlow("")
    val city: StateFlow<String> get() = _city

    fun updateCity(newCity: String) {
        _city.value = newCity
    }
}

// good — one declaration; Stable in Kotlin 2.4, no flag
class LocationViewModel {
    val city: StateFlow<String>
        field = MutableStateFlow("")

    fun updateCity(newCity: String) {
        city.value = newCity   // smart cast to MutableStateFlow inside the class
    }
}

// good — the field type may be spelled out when inference is not obvious
class Cart {
    val items: List<String>
        field: MutableList<String> = mutableListOf()
}

// good — still the right answer when a limitation applies: `open` properties
// and properties with a custom getter cannot have an explicit backing field
open class Registry {
    private val _entries = mutableListOf<Entry>()
    open val entries: List<Entry> get() = _entries.toList()
}
```

If your build must also compile under Kotlin 2.3, the syntax is available
there behind an opt-in. On 2.4 and later this flag is unnecessary:

```kotlin
// build.gradle.kts — required on Kotlin 2.3 only
kotlin {
    compilerOptions {
        freeCompilerArgs.add("-Xexplicit-backing-fields")
    }
}
```

## 17.8 Never read a property from an initializer that runs before it — and never call an `open` member during construction.

> Why? Property initializers and `init` blocks execute top to bottom in
> declaration order
> ([Constructors](https://kotlinlang.org/docs/classes.html#constructors)),
> so a forward reference reads a slot that has not been written yet. Within a
> single class the compiler usually catches it; across an inheritance
> boundary it does not. The base class's initializers run first, so an `open`
> property read from a base `init` block invokes the *derived* getter against
> a backing field still holding its default. The Kotlin documentation's
> advice is unambiguous: "avoid using open members in the constructors,
> property initializers, and `init` blocks"
> ([Derived class initialization
> order](https://kotlinlang.org/docs/inheritance.html#derived-class-initialization-order)).
> **Suggestion.**

```kotlin
// bad — Base's init runs before Derived's initializers, so size is still 0
open class Base {
    open val size: Int = 0

    init {
        require(size > 0) { "size must be positive" }   // always fails
    }
}

class Derived : Base() {
    override val size: Int = 10
}

// good — take the value through the constructor, so it exists before any
// initializer can read it
open class Base(val size: Int) {
    init {
        require(size > 0) { "size must be positive" }
    }
}

class Derived : Base(size = 10)
```

## 17.9 Use `const val` only for a value that is genuinely frozen; use a plain `val` for anything a consumer might see change.

> Why? "Compile-time constants are inlined at compile time, so each reference
> is replaced with its actual value"
> ([Compile-time
> constants](https://kotlinlang.org/docs/properties.html#compile-time-constants)).
> That is the whole point when the constant is an annotation argument or a
> `when` branch label — and the whole problem across a module boundary,
> because every consumer bakes in the literal and keeps using the old value
> until it is *recompiled*, not merely re-linked. `const` also only accepts a
> `String` or a primitive, at top level or in an `object`/companion, with no
> custom getter. **Suggestion.**

```kotlin
// bad — const across a published module boundary; bumping it silently leaves
// already-compiled consumers on 30
const val DEFAULT_TIMEOUT_SECONDS = 30

// good — a normal val is read through a getter, so consumers pick up changes
val DEFAULT_TIMEOUT: Duration = Duration.ofSeconds(30)

// good — const is required here: an annotation argument must be a constant
const val REPLACEMENT_NOTE = "Use OrderServiceV2 instead"

@Deprecated(REPLACEMENT_NOTE)
fun oldApi() { /* ... */ }
```

## 17.10 Declare the type explicitly on every public property; omit it only where the initializer makes the type obvious and the property is not API.

> Why? The Android style guide permits omitting an inferable type but adds a
> carve-out: "When writing a library, retain the explicit type declaration
> when it is part of the public API"
> ([Implicit return/property
> types](https://developer.android.com/kotlin/style-guide#implicit_returnproperty_types)).
> The Kotlin coding conventions say the same for libraries: "always
> explicitly specify function return types and property types (to avoid
> accidentally changing the return type when the implementation changes)"
> ([Coding conventions for
> libraries](https://kotlinlang.org/docs/coding-conventions.html#coding-conventions-for-libraries)).
> Without the annotation, swapping `mutableListOf()` for `listOf()` in the
> initializer silently changes the published type. **Suggestion.**

```kotlin
// bad — the public type is whatever the initializer happens to return today,
// and today it is MutableList<Rule>
class RuleSet {
    val rules = mutableListOf<Rule>()
}

// good — the declared type is the contract; the initializer is an
// implementation detail that can change freely
class RuleSet {
    val rules: List<Rule> = mutableListOf()
}

// fine — private, and the type is obvious from the right-hand side
private val logger = LoggerFactory.getLogger(RuleSet::class.java)
```

## 17.11 Never try to store state in an extension property — it has no backing field.

> Why? An extension does not add anything to the class it extends, so there
> is nowhere to put a value: "Since extensions don't actually add members to
> classes, there's no efficient way for an extension property to have a
> backing field. That's why initializers are not allowed for extension
> properties"
> ([Extension properties](https://kotlinlang.org/docs/extensions.html#extension-properties)).
> The workaround people reach
> for — a top-level `WeakHashMap` keyed by the receiver — is a memory leak
> and a thread-safety hazard dressed up as a property. If the state belongs
> to the object, put it on the object; if you do not own the object, wrap it.
> **Suggestion.**

```kotlin
// bad — does not compile: "Initializers are not allowed for extension properties"
var Request.traceId: String = ""

// bad — compiles, and leaks every Request that ever had a trace id
private val traceIds = mutableMapOf<Request, String>()

var Request.traceId: String
    get() = traceIds[this].orEmpty()
    set(value) {
        traceIds[this] = value
    }

// good — a computed extension property, which needs no storage
val Request.isPreflight: Boolean
    get() = method == "OPTIONS" && "Access-Control-Request-Method" in headers

// good — state the type does not own goes in a wrapper the caller holds
data class TracedRequest(val request: Request, val traceId: String)
```

## 17.12 Override a `val` with a `var` only when the mutability is genuinely part of the subtype's contract.

> Why? Kotlin allows it in one direction only — "you can also override a
> `val` property with a `var` property, but not vice versa"
> ([Overriding
> properties](https://kotlinlang.org/docs/inheritance.html#overriding-properties)) —
> because a `val` declares a getter and a `var` adds a setter. Widening this
> way means every caller holding the *base* type sees a read-only property
> whose value changes underneath them, with no member on the base type that
> explains why. That is Liskov substitution violated by a property
> declaration. **Suggestion.**

```kotlin
// bad — callers typed to Shape see an immutable-looking `size` that mutates
abstract class Shape {
    abstract val size: Int
}

class ResizableShape(override var size: Int) : Shape()

fun render(shape: Shape) {
    val cells = IntArray(shape.size)
    // ... another thread calls resizable.size = 0 ...
    for (i in 0 until shape.size) { /* index out of bounds */ }
}

// good — mutability is declared where callers can see it
abstract class Shape {
    abstract val size: Int
}

interface Resizable {
    fun resize(newSize: Int)
}

class ResizableShape(size: Int) : Shape(), Resizable {
    override var size: Int = size
        private set

    override fun resize(newSize: Int) {
        require(newSize >= 0) { "size must be >= 0, was $newSize" }
        size = newSize
    }
}
```

## 17.13 Treat a public `var` in a domain type as a design smell: name the transition instead.

> Why? The Kotlin coding conventions open the immutability section with
> "prefer using immutable data to mutable"
> ([Immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability)).
> A public `var` publishes every possible state transition at once, with no
> place to validate one and no name for any of them. `order.status =
> SHIPPED` on a cancelled order compiles. A `private set` plus a named method
> puts the legal transitions in the API and the illegal ones behind a
> `check`. **Suggestion.**

```kotlin
// bad — any code anywhere can move an order to any state
class Order(val id: OrderId) {
    var status: OrderStatus = OrderStatus.DRAFT
    var trackingId: TrackingId? = null
}

order.status = OrderStatus.SHIPPED   // from CANCELLED, with no tracking id

// good — the transitions are the API
class Order(val id: OrderId) {
    var status: OrderStatus = OrderStatus.DRAFT
        private set

    var trackingId: TrackingId? = null
        private set

    fun ship(trackingId: TrackingId) {
        check(status == OrderStatus.PAID) { "cannot ship an order in status $status" }
        this.trackingId = trackingId
        status = OrderStatus.SHIPPED
    }
}
```

## 17.14 Use `lateinit` only for a non-null value a framework assigns before first read, and check it with `::prop.isInitialized`.

> Why? `lateinit` trades the compiler's null check for a runtime
> `UninitializedPropertyAccessException`, which is worth it exactly when the
> value is genuinely always assigned first — Spring field injection, a JUnit
> `@BeforeEach`. It is not a way to avoid writing `?.`; if absence is a state
> the program can be in, the property is nullable (§16.10 and
> [Chapter 6](06-null-safety.md)). When you must probe it, Kotlin gives you
> `this::prop.isInitialized`
> ([Late-initialized properties and
> variables](https://kotlinlang.org/docs/properties.html#late-initialized-properties-and-variables));
> catching the exception instead turns a control-flow question into
> exception-driven flow. Note `lateinit` is not allowed on primitives, on
> `val`, in a primary constructor, or with a custom accessor.
> **Suggestion** — `detekt/LateinitUsage` (style ruleset, off by default)
> flags every occurrence so each one has to be argued for.

```kotlin
// bad — "not loaded yet" is a real, ongoing state, and the caller is forced
// into a try/catch to discover it
class ProfileCache {
    lateinit var profile: Profile

    fun displayName(): String =
        try {
            profile.name
        } catch (e: UninitializedPropertyAccessException) {
            "loading..."
        }
}

// good — the domain has an absent state, so the type has one
class ProfileCache {
    var profile: Profile? = null

    fun displayName(): String = profile?.name ?: "loading..."
}

// good — genuinely assigned by the framework before any test body runs
class OrderServiceTest {
    private lateinit var service: OrderService

    @BeforeEach
    fun setUp() {
        service = OrderService(FakeRepository())
    }
}

// good — when a probe is unavoidable, ask the property, do not catch
class Connection {
    private lateinit var channel: Channel

    fun closeQuietly() {
        if (this::channel.isInitialized) {
            channel.close()
        }
    }
}
```

## 17.15 Derive a value with a getter instead of keeping a second `var` you have to remember to update.

> Why? Two properties that must agree are two properties that will
> eventually disagree — the bug is always in the one code path that updated
> the first and forgot the second. A `val` with a getter has no second copy
> to fall out of sync, and the compiler makes it impossible to forget.
> Reach for a cached field only after measuring, and only when the inputs are
> immutable (§17.4). **Suggestion.**

```kotlin
// bad — remove() forgot to adjust the total; nothing catches it
class Cart {
    private val _lines = mutableListOf<Line>()

    var total: Money = Money.ZERO
        private set

    fun add(line: Line) {
        _lines += line
        total += line.amount
    }

    fun remove(line: Line) {
        _lines -= line
    }
}

// good — one source of truth; the total cannot drift
class Cart {
    private val _lines = mutableListOf<Line>()

    val lines: List<Line>
        get() = _lines.toList()

    val total: Money
        get() = _lines.fold(Money.ZERO) { running, line -> running + line.amount }

    fun add(line: Line) {
        _lines += line
    }

    fun remove(line: Line) {
        _lines -= line
    }
}
```
