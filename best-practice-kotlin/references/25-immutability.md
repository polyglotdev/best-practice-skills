<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 25. Immutability

Kotlin makes immutability cheap enough to be the default, and then hands you
two ways to believe you have it when you do not. The first is `val`, which
freezes a *reference* and says nothing at all about the object on the other
end of it. The second is the read-only collection interfaces — `List`, `Set`,
`Map` — which are read-only *views*, not immutable *collections*. A `List<T>`
you hand a caller can be the very `MutableList<T>` you are still appending to.
This chapter is mostly about closing that gap.

The normative source is
[Kotlin coding conventions: Immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability),
which is unusually blunt for a style guide: "Prefer using immutable data to
mutable. Always declare local variables and properties as `val` rather than
`var` if they are not modified after initialization," and "Always use immutable
collection interfaces (`Collection`, `List`, `Set`, `Map`) to declare
collections which are not mutated." The surrounding
[idiomatic-use section](https://kotlinlang.org/docs/coding-conventions.html#idiomatic-use-of-language-features),
the
[property naming rules](https://kotlinlang.org/docs/coding-conventions.html#property-names),
the
[backing-property naming rule](https://kotlinlang.org/docs/coding-conventions.html#names-for-backing-properties),
and the Android style guide's
[backing properties](https://developer.android.com/kotlin/style-guide#backing_properties)
section supply the rest.

Four neighbouring topics are deferred. **Data class design** — when a `data
class` is the right shape at all, and what `copy()`, `equals`, and
`componentN` generate — is [Chapter 11](11-data-classes.md). **Property
accessor mechanics**, including custom getters and explicit backing fields, is
[Chapter 17](17-properties-and-backing-fields.md). **The collection API
surface** — `map`/`filter`/`fold`, sequences, and which factory returns what —
is [Chapter 20](20-collections-and-sequences.md). **The `equals`/`hashCode`
contract** that mutable components violate is
[Chapter 23](23-equality-and-ordering.md). And **shared mutable state under
concurrency** is [Chapter 33](33-coroutine-fundamentals.md) and
[Chapter 40](40-coroutine-anti-patterns.md); §25.14 and §25.15 state the
language-level principle those chapters build on.

**Tool alignment:** detekt's `VarCouldBeVal` (type-resolution required) reports
local `var`s and private properties that are never reassigned, `MayBeConstant`
reports `val`s that could be `const val`, and `UseDataClass` reports classes
that only carry data. Rules those checks actually enforce are marked
**Violation**; the rest are **Suggestion**, because no analyser can tell that a
collection you handed out was supposed to be a snapshot.

## 25.1 Declare every local variable and every property `val` unless something actually reassigns it.

> Why?
> [Kotlin coding conventions: Immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability)
> makes this unconditional: "Always declare local variables and properties as
> `val` rather than `var` if they are not modified after initialization." A
> `var` is a standing instruction to the reader — *watch this, it changes* —
> and a `var` that never changes spends that attention for nothing. It also
> costs you smart casts: the compiler will not smart-cast a mutable property,
> so a `var` forces null-handling ceremony a `val` would not.
> **Violation — enforced by `detekt/VarCouldBeVal`, which reports local
> variables and private class properties only; a public `var` that is never
> reassigned is on you.**

```kotlin
// bad — nothing ever reassigns any of these
fun render(config: Config): String {
    var formatter = DateTimeFormatter.ISO_INSTANT
    var region = config.region
    return "$region@${formatter.format(config.createdAt)}"
}

class RetryPolicy(var maxAttempts: Int, var backoff: Duration)

// good
fun render(config: Config): String {
    val formatter = DateTimeFormatter.ISO_INSTANT
    val region = config.region
    return "$region@${formatter.format(config.createdAt)}"
}

class RetryPolicy(val maxAttempts: Int, val backoff: Duration)
```

## 25.2 Remember that `val` freezes the reference, not the object it points at.

> Why? `val` is Java's `final`, not C++'s `const`. It guarantees exactly one
> thing: the binding will never be rebound. If the referent is mutable, every
> holder of that reference can change it, and the `val` will not have stopped a
> single mutation. This is the single most common false sense of immutability
> in Kotlin code, because the declaration *reads* as a guarantee. Immutability
> is a property of the type you chose, not of the keyword you declared it with.
> **Suggestion.**

```kotlin
// bad — `val` is doing no work: the referent is fully mutable and shared
class Article(val tags: MutableList<String>)

val tags = mutableListOf("kotlin")
val article = Article(tags)
article.tags += "oops"    // compiles — `val` never stopped this
tags.clear()              // and so does this, from outside the object

// good — the reference and the referent are both fixed
class Article(tags: List<String>) {
    val tags: List<String> = tags.toList()
}
```

## 25.3 Declare collection parameters, properties, and return types with the read-only interfaces — never `Mutable*`, and never a concrete implementation type.

> Why?
> [Kotlin coding conventions: Immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability)
> gives both halves of this rule and the exact examples: a parameter typed
> `HashSet<String>` for a value that is never mutated is "use of a mutable
> collection type for value which will not be mutated", and `arrayListOf()` is
> wrong because it "returns `ArrayList<T>`, which is a mutable collection
> type." Naming `MutableList` in a signature is a public promise that mutation
> is part of the contract; naming `ArrayList` additionally welds your callers
> to an implementation you may want to change. `listOf`, `setOf`, and `mapOf`
> return the read-only interfaces and are the correct default factories.
> **Suggestion.**

```kotlin
// bad — the signature advertises mutability the function never uses, and the
// local pins a concrete implementation type
fun validateValue(actualValue: String, allowedValues: HashSet<String>) { /* ... */ }

fun defaults(): ArrayList<String> = arrayListOf("a", "b", "c")

class Report(val rows: MutableList<Row>)

// good
fun validateValue(actualValue: String, allowedValues: Set<String>) { /* ... */ }

fun defaults(): List<String> = listOf("a", "b", "c")

class Report(val rows: List<Row>)
```

## 25.4 Treat a read-only `List` as a view, not a guarantee — snapshot with `toList()` before you hand one out.

> Why? `List` and `MutableList` are two interfaces over the same runtime
> object. On the JVM `mutableListOf()` produces a `java.util.ArrayList`; typing the result
> `List<T>` hides the mutating methods from Kotlin call sites, but it does not
> make the object immutable, does not stop the code that still holds the
> `MutableList` reference from appending, and does not stop a Java caller (or
> an unchecked cast) from mutating it directly. A method that returns the live
> backing collection is not returning a snapshot — it is returning a window
> that keeps moving after the caller has looked away. `toList()`, `toSet()`,
> and `toMap()` each allocate an independent copy. **Suggestion.**

```kotlin
// bad — the returned `List` is the same object as the private MutableList
class Cart {
    private val items = mutableListOf<Item>()

    fun add(item: Item) {
        items += item
    }

    fun snapshot(): List<Item> = items
}

val cart = Cart()
val view = cart.snapshot()
cart.add(Item("book"))
println(view.size) // 1 — the "snapshot" moved under the caller

// good — copy at the boundary
class Cart {
    private val items = mutableListOf<Item>()

    fun add(item: Item) {
        items += item
    }

    fun snapshot(): List<Item> = items.toList()
}
```

## 25.5 Copy every mutable collection argument on the way in, and validate the copy — not the original.

> Why? Storing the caller's collection directly leaves them holding a live
> handle to your internals, and they can mutate it past every invariant your
> `init` block checked. The copy must be taken *before* validation, not after:
> otherwise a concurrent (or merely careless) caller can change the value in
> the window between the check and the assignment, and your object goes live
> with state it never approved. Note the shape of the fix — take the
> constructor parameter *without* `val`, and declare the property separately so
> the property holds the copy. **Suggestion.**

```kotlin
// bad — the caller keeps a live handle on the list the Order validated
class Order(val lines: List<Line>) {
    init {
        require(lines.isNotEmpty()) { "order must have at least one line" }
    }
}

val lines = mutableListOf(Line("book", 1))
val order = Order(lines)
lines.clear()
println(order.lines.size) // 0 — past its own require()

// good — copy first, then validate the copy
class Order(lines: List<Line>) {
    val lines: List<Line> = lines.toList()

    init {
        require(this.lines.isNotEmpty()) { "order must have at least one line" }
    }
}
```

## 25.6 Never expose an `Array` as part of an API — Kotlin has no read-only array type.

> Why? Every one of `List`/`MutableList`, `Set`/`MutableSet`, and
> `Map`/`MutableMap` has a read-only half. `Array` has none: `Array<T>` is
> always mutable, `arr[0] = x` always compiles, and there is no interface you
> can name to take that away. An `Array`-typed property is therefore a
> permanently public mutation point no amount of `val` will close. The same
> applies to `vararg` parameters, which arrive as an array — copy before you
> store. Arrays belong in performance-critical internals (§25.17), not in
> signatures. **Suggestion.**

```kotlin
// bad — Array is always mutable; the caller can rewrite the palette in place
class Palette(val colors: Array<Color>)

val palette = Palette(arrayOf(Color.RED, Color.BLUE))
palette.colors[0] = Color.GREEN // compiles

// good — accept the array, expose a copied List
class Palette(colors: Array<out Color>) {
    val colors: List<Color> = colors.toList()

    companion object {
        fun of(vararg colors: Color) = Palette(colors)
    }
}
```

## 25.7 When a class genuinely mutates a collection internally, use the backing-property pattern: a private `_`-prefixed mutable half and a public read-only half.

> Why?
> [Kotlin coding conventions: Names for backing properties](https://kotlinlang.org/docs/coding-conventions.html#names-for-backing-properties)
> specifies the shape and the name exactly — "use an underscore as the prefix
> for the name of the private property" — and shows `_elementList` /
> `elementList`. The Android style guide's
> [backing properties](https://developer.android.com/kotlin/style-guide#backing_properties)
> section carries the same rule. The point is that the mutable type appears in
> exactly one place, `private`, and the public surface names only the read-only
> interface, so no caller can widen it back. Note that the public property must
> still hand out a snapshot if callers can retain it (§25.4). Kotlin 2.4 also
> offers explicit backing fields (`val x: T` followed by `field = ...`), which
> collapse this pair into one declaration; that feature was Experimental in
> Kotlin 2.3 behind `-Xexplicit-backing-fields` and
> [graduated to Stable in Kotlin 2.4](https://kotlinlang.org/docs/whatsnew24.html),
> so on a 2.4 floor it needs no flag. It is covered in
> [Chapter 17](17-properties-and-backing-fields.md). **Suggestion.**

```kotlin
// bad — the mutable type leaks into the public API, and the name gives no
// signal that a second, private view exists
class Basket {
    val elements = mutableListOf<Element>()
}

Basket().elements.clear() // any caller, any time

// good
class Basket {
    private val _elements = mutableListOf<Element>()
    val elements: List<Element> get() = _elements.toList()

    fun add(element: Element) {
        _elements += element
    }
}
```

## 25.8 Build a collection with `buildList` / `buildSet` / `buildMap` so the mutable phase is confined to the builder lambda.

> Why? The alternative is a `val acc = mutableListOf<T>()` that stays mutable
> for the rest of the enclosing scope, and a `return acc` that hands out a live
> `ArrayList` typed as `List`. `buildList` gives you a `MutableList` receiver
> inside the lambda and a `List` outside it, and the builder is not valid after
> the lambda returns — the mutable phase has a hard boundary rather than a
> convention. These functions have been stable since Kotlin 1.6.
>
> Kotlin 2.4 additionally offers collection literals (`val xs: List<String> =
> ["a", "b"]`), but they are **Experimental in Kotlin 2.4** and require
> `-Xcollection-literals`; they cannot construct Java-defined collections, and
> they default to `List` when the target type cannot be inferred. Do not use
> them in production code without the flag and a comment justifying it.
> **Suggestion.**

```kotlin
// bad — `headers` stays mutable for the whole function and escapes as a live
// ArrayList typed as Map
fun headersFor(request: Request): Map<String, String> {
    val headers = mutableMapOf<String, String>()
    headers["accept"] = "application/json"
    if (request.token != null) {
        headers["authorization"] = "Bearer ${request.token}"
    }
    return headers
}

// good — mutability ends where the lambda ends
fun headersFor(request: Request): Map<String, String> = buildMap {
    put("accept", "application/json")
    request.token?.let { put("authorization", "Bearer $it") }
}
```

## 25.9 Reach for `kotlinx.collections.immutable` only when you need the guarantee in the type system or cheap structural sharing — and know it is Alpha.

> Why? Defensive copying (§25.4, §25.5) solves the aliasing problem but pays a
> full copy each time, and it still leaves `List` as the declared type, so
> nothing at the type level distinguishes "immutable" from "read-only view".
> `org.jetbrains.kotlinx:kotlinx-collections-immutable` supplies
> `ImmutableList`/`ImmutableSet`/`ImmutableMap` (a type-level promise that the
> collection never changes) and `PersistentList`/`PersistentSet`/`PersistentMap`
> (the same promise plus `add`/`remove`/`put` returning a new instance that
> shares structure with the old one, so repeated derivation is not repeated
> copying). The cost is real: as of 0.5.1 the library's own README states the
> API is subject to change, and the badges read Alpha. Take the dependency when
> a hot path derives collections repeatedly, or when an API contract genuinely
> needs to say "immutable"; otherwise `toList()` is enough. **Suggestion.**

```kotlin
// bad — every event copies the whole history; O(n) per append, O(n^2) overall,
// and the declared type still promises nothing
class Ledger(val entries: List<Entry>) {
    fun record(entry: Entry) = Ledger(entries + entry)
}

// good — structural sharing, and the type states the guarantee
class Ledger(val entries: PersistentList<Entry> = persistentListOf()) {
    fun record(entry: Entry) = Ledger(entries.add(entry))
}
```

## 25.10 Make a value object immutable all the way down: every component `val`, and every component type itself immutable.

> Why? A `data class` whose components are all `val` is still mutable if one of
> those components is a `MutableList`, an `Array`, a `java.util.Date`, or any
> other type with in-place mutators. The object then has all the *appearance*
> of a value — `copy()`, structural `equals`, destructuring — while two
> "equal" instances can drift apart because they share the same mutable part.
> That interacts badly with hashing: see
> [Chapter 23](23-equality-and-ordering.md) for why a value whose `hashCode`
> can change is unusable as a `Map` key or `Set` element. Immutability is
> transitive or it is nothing. **Suggestion.**

```kotlin
// bad — all-val components, but the object is still mutable, and both
// instances share the same list
data class Invoice(
    val id: InvoiceId,
    val lines: MutableList<Line>,
    val issuedAt: java.util.Date,
)

// good — every component is itself immutable
data class Invoice(
    val id: InvoiceId,
    val lines: List<Line>,
    val issuedAt: Instant,
) {
    init {
        require(lines.isNotEmpty()) { "invoice must have at least one line" }
    }
}
```

## 25.11 Derive new values with `copy()` rather than mutating — and remember `copy()` is shallow.

> Why? `copy()` is the idiomatic way to express "the same value, with one thing
> different", and it keeps the original valid for anyone still holding it. But
> the generated `copy()` copies *references*: if a component is mutable, the
> copy and the original share it, and mutating through either one is visible
> through both. That is the failure §25.10 exists to prevent, and it is
> invisible at the `copy()` call site. If a component must be a collection,
> make sure it was frozen on the way in (§25.5), so the shallow copy is safe by
> construction. Note that a `data class` cannot use the §25.5 shape — `copy()`
> requires the component to *be* the primary-constructor `val`, so there is no
> parameter left to copy from — and a secondary constructor taking `Collection`
> does not help either, because a `List` argument is more specific and binds to
> the primary constructor instead. Freeze in a factory, and keep the primary
> constructor an internal detail. **Suggestion.**

```kotlin
// bad — mutating in place invalidates every reference already handed out
class Session(var lastSeenAt: Instant, val visitedPages: MutableList<String>)

fun touch(session: Session, page: String) {
    session.lastSeenAt = Instant.now()
    session.visitedPages += page
}

// good — derive; the factory freezes the collection so copy() is safe
data class Session(val lastSeenAt: Instant, val visitedPages: List<String>) {
    companion object {
        fun of(lastSeenAt: Instant, pages: Collection<String>): Session =
            Session(lastSeenAt, pages.toList())
    }
}

fun touch(session: Session, page: String): Session =
    session.copy(lastSeenAt = Instant.now(), visitedPages = session.visitedPages + page)
```

## 25.12 Freeze configuration at construction; a configuration object must expose no way to change itself.

> Why? Configuration is read from many places, often on many threads, usually
> without any synchronisation, and almost always after startup. A settable
> field on a config object turns every one of those reads into a race and makes
> the effective configuration depend on when you looked. Bind once, validate
> once in `init`, and hand out an immutable object; when configuration must
> genuinely change at runtime, model that explicitly as a new immutable
> snapshot published through a `StateFlow` (§25.15), not as a mutable field.
> For the Spring binding form of this rule, see
> [Chapter 43](43-spring-configuration-properties.md). **Suggestion.**

```kotlin
// bad — anyone can retune the client mid-flight, and nothing revalidates
class HttpClientConfig {
    var baseUrl: String = ""
    var connectTimeout: Duration = Duration.ofSeconds(10)
    var maxRetries: Int = 3
}

// good — validated once, frozen thereafter
data class HttpClientConfig(
    val baseUrl: String,
    val connectTimeout: Duration = Duration.ofSeconds(10),
    val maxRetries: Int = 3,
) {
    init {
        require(baseUrl.isNotBlank()) { "baseUrl must not be blank" }
        require(maxRetries >= 0) { "maxRetries must be >= 0, was $maxRetries" }
    }
}
```

## 25.13 Never hold mutable state in an `object` or a `companion object`.

> Why? An `object` is a process-wide singleton, so a `var` or a mutable
> collection inside one is global mutable state with all the usual
> consequences: no test can reset it, two tests in the same JVM interfere,
> nothing can substitute it, and every access is an unsynchronised race unless
> you remember otherwise. Kotlin makes this especially easy to write by
> accident, because `companion object` looks like a scoping device rather than
> a singleton. Constants (§25.18) and pure functions are fine in an `object`;
> state is not. Inject the holder instead — see
> [Chapter 14](14-objects-and-companions.md). **Suggestion.**

```kotlin
// bad — global mutable state; unsynchronised, unresettable, untestable
object MetricsRegistry {
    var lastFlushedAt: Instant? = null
    val counters = mutableMapOf<String, Long>()

    fun increment(name: String) {
        counters[name] = (counters[name] ?: 0L) + 1L
    }
}

// good — an ordinary class the caller owns and a test can construct fresh
class MetricsRegistry {
    private val counters = ConcurrentHashMap<String, Long>()

    fun increment(name: String) {
        counters.merge(name, 1L) { current, delta -> current + delta }
    }

    fun snapshot(): Map<String, Long> = counters.toMap()
}
```

## 25.14 Make immutability your first thread-safety strategy, and reach for a lock only when it fails.

> Why? An immutable object needs no synchronisation at all: there is no write
> for a read to race with, so it can be shared across any number of threads or
> coroutines without a lock, a `@Volatile`, or a happens-before argument.
> Kotlin gives you safe publication for free, because a `val` property compiles
> to a `final` field and the JVM memory model guarantees that a correctly
> constructed object's `final` fields are visible to every thread that sees the
> reference — provided `this` did not escape the constructor. Every lock you do
> not need is a deadlock you cannot have. See
> [Chapter 33](33-coroutine-fundamentals.md) for how this plays out under
> structured concurrency. **Suggestion.**

```kotlin
// bad — mutable shared state plus a lock the next caller will forget to take
class PriceBook {
    private val lock = Any()
    private val prices = mutableMapOf<Sku, Money>()

    fun update(sku: Sku, price: Money) {
        synchronized(lock) { prices[sku] = price }
    }

    fun priceOf(sku: Sku): Money? = prices[sku] // forgot the lock
}

// good — an immutable snapshot needs no lock at all
class PriceBook(private val prices: Map<Sku, Money>) {
    fun priceOf(sku: Sku): Money? = prices[sku]

    fun withPrice(sku: Sku, price: Money): PriceBook = PriceBook(prices + (sku to price))
}
```

## 25.15 When shared state must change, hold an immutable snapshot in a `MutableStateFlow` and replace it with `update {}`.

> Why? Some state genuinely changes and genuinely is shared. The Kotlin answer
> is not "mutable collection plus lock" — it is "immutable value in an atomic
> reference". `MutableStateFlow<T>` is that reference: readers see a complete,
> consistent `T` and never a half-applied edit, and
> [`update { old -> new }`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html)
> "updates the `value` atomically using the specified function", so a lost
> update is impossible. The price is stated in the same doc: the function "may
> be evaluated multiple times, if `value` is being concurrently updated," so the
> lambda must be a pure transform — never log, emit, or mutate inside it.
> Assigning `state.value = state.value + x` is *not* equivalent — it is a
> read-modify-write with a window in the middle, which is exactly the race
> `update` exists to close. `StateFlow` and `SharedFlow` in depth are
> [Chapter 37](37-stateflow-and-sharedflow.md). **Suggestion.**

```kotlin
// bad — read-modify-write on .value races; concurrent callers lose updates
class ConnectionRegistry {
    private val _connections = MutableStateFlow<Set<ConnectionId>>(emptySet())
    val connections: StateFlow<Set<ConnectionId>> = _connections

    fun register(id: ConnectionId) {
        _connections.value = _connections.value + id
    }
}

// good — atomic compare-and-set over an immutable snapshot
class ConnectionRegistry {
    private val _connections = MutableStateFlow<Set<ConnectionId>>(emptySet())
    val connections: StateFlow<Set<ConnectionId>> = _connections.asStateFlow()

    fun register(id: ConnectionId) {
        _connections.update { it + id }
    }
}
```

## 25.16 A builder is mutable; its product must not be — and `build()` must not leak the builder's own buffer.

> Why? A builder exists to stage optional values before an object is legal, so
> it has to be mutable. The bug is letting that mutability survive `build()`:
> if `build()` passes the builder's `MutableList` straight into the product,
> then calling `add(...)` again afterwards silently edits an object the caller
> already considers finished — and if `build()` is called twice, both products
> share one list. Copy in `build()`, validate the whole combination there, and
> keep the product's constructor private so the builder is the only path in.
> **Suggestion.**

```kotlin
// bad — the product shares the builder's list; building twice aliases them
class Pipeline private constructor(val stages: List<Stage>) {
    class Builder {
        private val stages = mutableListOf<Stage>()

        fun stage(stage: Stage) = apply { stages += stage }

        fun build() = Pipeline(stages)
    }
}

val builder = Pipeline.Builder().stage(Parse)
val pipeline = builder.build()
builder.stage(Emit)          // mutates pipeline.stages too
println(pipeline.stages.size) // 2

// good — build() snapshots and validates
class Pipeline private constructor(val stages: List<Stage>) {
    class Builder {
        private val stages = mutableListOf<Stage>()

        fun stage(stage: Stage) = apply { stages += stage }

        fun build(): Pipeline {
            require(stages.isNotEmpty()) { "pipeline must have at least one stage" }
            return Pipeline(stages.toList())
        }
    }
}
```

## 25.17 Contain deliberate local mutability: a `var` or a `MutableList` that never escapes its function is correct, and does not need apologising for.

> Why? "Prefer immutable" is not "never mutate". A single-threaded accumulation
> loop, a hand-rolled parser, and a tight numeric inner loop are all cases
> where local mutation is the clearest and fastest expression of the algorithm,
> and rewriting them as a `fold` over an immutable accumulator can be both
> slower and harder to read. The rule that matters is *containment*: the
> mutable object is created inside the function, is never stored in a field, is
> never passed to code that could retain it, and is converted to a read-only
> type before it is returned (§25.4). Mutability whose lifetime you can see in
> one screen is not shared mutable state. **Suggestion.**

```kotlin
// bad — mutability that escapes: the buffer becomes a field, so its lifetime
// and its aliases are now unbounded
class Tokenizer(private val source: String) {
    private val buffer = mutableListOf<Token>()

    fun tokens(): List<Token> {
        buffer.clear()
        // ... appends to buffer ...
        return buffer
    }
}

// good — the same mutability, contained and frozen on the way out
class Tokenizer(private val source: String) {
    fun tokens(): List<Token> {
        val buffer = mutableListOf<Token>()
        var index = 0
        while (index < source.length) {
            val (token, next) = readToken(source, index)
            buffer += token
            index = next
        }
        return buffer.toList()
    }
}
```

## 25.18 Use `const val` for compile-time constants, and reserve SCREAMING_SNAKE_CASE for values that are deeply immutable.

> Why? `const val` is the only Kotlin declaration that is immutable at compile
> time: the value is inlined at every use site, so it cannot be reassigned,
> cannot be reflected over, and does not cost a getter call. A plain `val` in
> an `object` is a runtime read through an accessor, and the compiler cannot
> prove anything about it.
> [Kotlin coding conventions: Property names](https://kotlinlang.org/docs/coding-conventions.html#property-names)
> ties the naming to the guarantee: screaming snake case is for "properties
> marked with `const`, or top-level or object `val` properties with no custom
> `get` function that hold deeply immutable data", while "top-level or object
> properties which hold objects with behavior or mutable data should use camel
> case names." A `MutableSet` named `ALLOWED_VALUES` misreports itself.
> **Suggestion — `detekt/MayBeConstant` covers this, but it is absent from detekt 1.23.8's default config (the docs site is ahead of the latest stable release). Enable it once your detekt version ships it; see chapter 47.**

```kotlin
// bad — a getter call at every use site for a value the Kotlin compiler could
// have inlined, and a SCREAMING_SNAKE name on a value that is anything but
// constant
object Limits {
    val MAX_RETRIES = 3
    val ALLOWED_SCOPES: MutableSet<String> = mutableSetOf("read", "write")
    val REQUEST_COUNTER: AtomicLong = AtomicLong()
}

// good — const where the compiler can inline, SCREAMING_SNAKE only for
// deeply immutable values, and no mutable state in the object at all (§25.13)
object Limits {
    const val MAX_RETRIES = 3
    val DEFAULT_TIMEOUT: Duration = Duration.ofSeconds(30) // not a compile-time constant
    val ALLOWED_SCOPES: Set<String> = setOf("read", "write")
}
```
