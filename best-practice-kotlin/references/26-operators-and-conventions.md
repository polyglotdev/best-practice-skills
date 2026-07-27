<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 26. Operators & Conventions

Kotlin's operators are resolved by *name*, not by symbol. Writing `a + b`
compiles to a call to a function called `plus` marked with the `operator`
modifier; `a in b` compiles to `b.contains(a)`; `a[i] = v` compiles to
`a.set(i, v)`. The set of recognised names is fixed and closed — you cannot
invent a new symbol, and you cannot repurpose an existing one to mean something
the reader will not expect. The whole feature is therefore an exercise in
restraint: the compiler will happily let you define `Money.div(Customer)`, and
nothing but review will stop you.

The normative source is the Kotlin language documentation on
[operator overloading](https://kotlinlang.org/docs/operator-overloading.html),
which lists every recognised name and the expression each one translates to.
The Kotlin coding conventions supply the surrounding style rules:
[indexing suffix](https://kotlinlang.org/docs/coding-conventions.html#indexing-suffix),
[infix functions](https://kotlinlang.org/docs/coding-conventions.html#infix-functions),
[destructuring declarations](https://kotlinlang.org/docs/coding-conventions.html#destructuring-declarations),
and
[modifiers order](https://kotlinlang.org/docs/coding-conventions.html#modifiers-order),
which places `operator` and `infix` at a fixed position in the modifier list.

Four topics are deferred. The **semantics** of `equals`, `hashCode`, and
`compareTo` — the contracts you must satisfy, not merely the syntax that binds
them to `==` and `<` — are [Chapter 23](23-equality-and-ordering.md).
The **delegation conventions** `getValue`, `setValue`, and `provideDelegate`
are [Chapter 16](16-delegation.md). **Function design in general**, including
when an extension is the right shape and how `infix` interacts with named
arguments, is [Chapter 8](08-functions.md). **Data class design**, including
what `componentN` is generated from, is [Chapter 11](11-data-classes.md);
§26.17 covers only the destructuring hazard.

**Tool alignment:** detekt's `ExplicitCollectionElementAccessMethod` reports
call sites that use `map.get(k)` / `map.put(k, v)` where the indexed-access
operator would read better. That is the only rule here a checker can decide.
Nothing mechanically verifies that an overloaded operator *means* what its
symbol means, so every other rule in this chapter is a **Suggestion**.

## 26.1 Declare an operator with the `operator` modifier and one of the names Kotlin recognises — you cannot invent a symbol.

> Why? The
> [operator overloading reference](https://kotlinlang.org/docs/operator-overloading.html)
> defines a closed mapping: `plus`, `minus`, `times`, `div`, `rem`,
> `unaryPlus`, `unaryMinus`, `not`, `inc`, `dec`, `rangeTo`, `rangeUntil`,
> `contains`, `get`, `set`, `invoke`, `plusAssign`, `minusAssign`,
> `timesAssign`, `divAssign`, `remAssign`, `equals`, `compareTo`, `iterator`,
> `componentN`, plus the delegation trio. A function with one of those names but *without*
> `operator` is an ordinary function and `a + b` will not compile against it;
> a function with `operator` and any name outside the list is a compile error.
> Knowing the list is also what stops you hoping that `pow` gives you `**` —
> Kotlin has no exponentiation operator, and an `infix fun pow` (§26.18) is the
> closest legal approximation. **Suggestion.**

```kotlin
// bad — `operator` on a name Kotlin does not recognise; the compiler rejects
// the modifier outright ("illegal function name")
data class Vector2(val x: Double, val y: Double) {
    operator fun dot(other: Vector2): Double = x * other.x + y * other.y
}

// bad — right name, missing modifier: `a + b` does not compile
data class Vector2(val x: Double, val y: Double) {
    fun plus(other: Vector2) = Vector2(x + other.x, y + other.y)
}

// good — recognised name plus the modifier for the operator, an ordinary
// (infix) function for the operation that has no symbol
data class Vector2(val x: Double, val y: Double) {
    operator fun plus(other: Vector2) = Vector2(x + other.x, y + other.y)

    infix fun dot(other: Vector2): Double = x * other.x + y * other.y
}
```

## 26.2 Overload an operator only when the symbol already means, to any reader, exactly what your implementation does.

> Why? An operator is the least searchable construct in the language. A reader
> who meets `a.merge(b)` can jump to the declaration; a reader who meets
> `a + b` assumes they already know what it does and moves on. That assumption
> is the entire value of operator overloading, and it is also the entire risk:
> the moment `+` means "append to the audit log" or "combine and persist", every
> call site in the codebase lies. The test is not "is there an analogy?" but
> "would a reviewer who has never seen this type guess right?" If the answer is
> no, use a named function. **Suggestion.**

```kotlin
// bad — `+` here means "send"; nothing at the call site suggests I/O
class Mailbox(private val transport: Transport) {
    operator fun plus(message: Message) {
        transport.send(message)
    }
}

mailbox + Message("hello") // reads as a pure combination; performs network I/O

// good — the name carries the meaning, and `+` is reserved for combination
class Mailbox(private val transport: Transport) {
    fun send(message: Message) {
        transport.send(message)
    }
}

mailbox.send(Message("hello"))
```

## 26.3 `plus`, `minus`, `times`, `div`, and `rem` must return a new value and must never mutate the receiver.

> Why? `a + b` is an expression, and every reader treats it as one: they expect
> to be able to write `val c = a + b` and still have `a` unchanged, to hoist it
> out of a loop, and to evaluate it twice with the same result. An arithmetic
> operator that mutates breaks all three, and it breaks them silently — the
> expression still compiles and still returns something. If your operation
> mutates, it is an augmented assignment (`plusAssign`, §26.13) or a named
> method, never `plus`. **Suggestion.**

```kotlin
// bad — `plus` mutates and returns the same instance; `a + b` changes `a`
class Basket(private val items: MutableList<Item> = mutableListOf()) {
    operator fun plus(item: Item): Basket {
        items += item
        return this
    }
}

val original = Basket()
val combined = original + Item("book") // `original` changed too, and they alias

// good — a fresh value; `original` is untouched
class Basket(val items: List<Item> = emptyList()) {
    operator fun plus(item: Item): Basket = Basket(items + item)
}
```

## 26.4 Do not define an arithmetic operator for an operation that is not closed over the type or has no single obvious meaning.

> Why? `Money + Money` is unambiguous. `Money * Money` is not: money squared is
> not a quantity anyone models, and the only sensible multiplications are
> `Money * scalar` and `Money / Money -> ratio`. Defining the meaningless
> overload does not just add a useless function — it makes a genuine unit bug
> compile. The rule generalises: if the operator's result type is not the same
> type (or a deliberately chosen other type you can name), and if a reader would
> have to ask "in what units?", write a named function instead. Also note the
> `rem` naming: Kotlin's `%` is remainder, not modulo, and it takes the sign of
> the dividend. **Suggestion.**

```kotlin
// bad — `Money * Money` has no meaning, but `price * quantityAsMoney` compiles
@JvmInline
value class Money(val minorUnits: Long) {
    operator fun times(other: Money) = Money(minorUnits * other.minorUnits)
}

// good — multiplication only by a scalar; division of like by like yields a
// dimensionless ratio, which is named rather than implied
@JvmInline
value class Money(val minorUnits: Long) {
    operator fun plus(other: Money) = Money(Math.addExact(minorUnits, other.minorUnits))

    operator fun times(factor: Int) = Money(Math.multiplyExact(minorUnits, factor.toLong()))

    fun ratioTo(other: Money): Double = minorUnits.toDouble() / other.minorUnits
}
```

## 26.5 Define `get` and `set` only for genuine indexed access, and use the `[]` form at call sites.

> Why? `a[i]` translates to `a.get(i)` and `a[i] = v` to `a.set(i, v)`, with
> any number of indices — `a[x, y]` is `a.get(x, y)`. The operator is right
> when the receiver *is* a container addressed by a key or coordinate, and
> wrong when it is a lookup with side effects, a fallible query, or a service
> call, because `[]` promises cheap, total access. On the call-site half,
> `map[key]` reads better than `map.get(key)` and `map[key] = value` better
> than `map.put(key, value)` — note that `put` returns the previous value while
> the operator form returns `Unit`, so the two are not interchangeable when the
> return value is used. Multi-argument indexing has its own wrapping rule in
> [Kotlin coding conventions: Indexing suffix](https://kotlinlang.org/docs/coding-conventions.html#indexing-suffix).
> **Violation — enforced by `detekt/ExplicitCollectionElementAccessMethod`
> for the call-site half.**

```kotlin
// bad — a database round-trip behind `[]`, and explicit accessor calls where
// the operator form exists
class UserTable(private val db: Database) {
    operator fun get(id: UserId): User = db.query("select ... where id = ?", id)
}

val name = attributes.get("name")
attributes.put("name", "ada")

// good — `[]` for real indexed access into an owned buffer
class Grid(private val width: Int, private val cells: IntArray) {
    operator fun get(x: Int, y: Int): Int = cells[y * width + x]

    operator fun set(x: Int, y: Int, value: Int) {
        cells[y * width + x] = value
    }
}

val name = attributes["name"]
attributes["name"] = "ada"
```

## 26.6 Define `contains` so that `x in y` reads as membership, and keep it a pure, cheap predicate.

> Why? `a in b` compiles to `b.contains(a)` and `a !in b` to `!b.contains(a)`,
> so the receiver is the *container* and the argument is the *element* — the
> reversal trips people up when they write the function by hand. `in` reads as
> a question, so `contains` must answer it without side effects and without
> surprising cost; a `contains` that issues a query turns `if (x in y)` into a
> hidden network call. It is one of the best operators to define, because
> `instant in window` genuinely reads better than `window.covers(instant)`.
> **Suggestion.**

```kotlin
// bad — roles reversed (the *element* is the receiver, so the expression that
// compiles is `blockList in userId`), and the predicate performs a network
// round-trip behind `in`
class BlockList(private val client: HttpClient) {
    fun isBlocked(id: UserId): Boolean = client.get("/blocked/${id.value}").isSuccess
}

operator fun UserId.contains(list: BlockList): Boolean = list.isBlocked(this)

if (blockList in userId) { // reads backwards, and hits the network
    return Response.forbidden()
}

// good — receiver is the container, argument is the element, and it is pure
data class TimeWindow(val start: Instant, val endExclusive: Instant) {
    operator fun contains(instant: Instant): Boolean =
        instant >= start && instant < endExclusive
}

if (now in maintenanceWindow) {
    return Response.serviceUnavailable()
}
```

## 26.7 Define `rangeTo` / `rangeUntil` only for a type with a natural total order, and define `compareTo` alongside them.

> Why? `a..b` calls `rangeTo` and `a..<b` calls `rangeUntil`. A range whose
> endpoints cannot be compared is not a range — it is a pair with misleading
> syntax, and code that later asks "is `x` in this range?" or iterates it has
> nothing to work with. The stdlib's own ranges are built on `Comparable`, so
> making your type `Comparable<T>` gets you `ClosedRange<T>` and the `in`
> operator for free, and is very often all you needed. Reach for a custom
> `rangeTo` only when the range type itself carries behaviour the generic one
> does not. **Suggestion.**

```kotlin
// bad — a "range" over an unordered type; `in` and iteration are meaningless
data class Sku(val code: String)

operator fun Sku.rangeTo(other: Sku): Pair<Sku, Sku> = this to other

// good — implementing Comparable gives `..`, `in`, and sorting at once, via
// the stdlib's `rangeTo` for Comparable types
@JvmInline
value class Version(private val encoded: Long) : Comparable<Version> {
    override fun compareTo(other: Version): Int = encoded.compareTo(other.encoded)
}

val supported: ClosedRange<Version> = Version(2_004_000L)..Version(2_999_999L)
if (current in supported) {
    proceed()
}
```

## 26.8 Get `compareTo` by implementing `Comparable<T>`, not by declaring a bare `operator fun compareTo`.

> Why? `<`, `>`, `<=`, and `>=` all translate to `compareTo`, which must return
> `Int`. Declaring it standalone gets you the four operators and nothing else:
> `sorted()`, `maxOrNull()`, `coerceIn`, `ClosedRange`, `TreeMap`, and every
> Java API that takes a `Comparable` all remain unavailable. Implementing the
> interface costs the same line and unlocks all of it. Note that when you
> `override` `Comparable.compareTo`, the `operator` modifier is inherited from
> the interface declaration, so repeating it on the override is redundant. The
> ordering *contract* —
> antisymmetry, transitivity, and consistency with `equals` — is
> [Chapter 23](23-equality-and-ordering.md), and violating it corrupts sorted
> collections rather than throwing. **Suggestion.**

```kotlin
// bad — `<` works, `sorted()` and `in` do not
class Priority(val level: Int) {
    operator fun compareTo(other: Priority): Int = level.compareTo(other.level)
}

listOf(Priority(2), Priority(1)).sorted() // does not compile

// good
class Priority(val level: Int) : Comparable<Priority> {
    override fun compareTo(other: Priority): Int = level.compareTo(other.level)
}

listOf(Priority(2), Priority(1)).sorted()
```

## 26.9 Never declare `operator fun equals` yourself — override `Any.equals`, and override `hashCode` with it.

> Why? `==` translates to `a?.equals(b) ?: (b === null)`, so it is already
> wired to the `equals` every class inherits from `Any`; declaring a *new*
> `operator fun equals(other: SomeType)` creates an overload that shadows the
> real one only for statically-known types, so `a == b` and
> `listOf(a).contains(b)` can disagree. Override the inherited
> `equals(other: Any?)` instead, or let `data class` generate it. The identity
> operators `===` and `!==` are not overloadable at all. The contract that ties
> `equals` to `hashCode` is [Chapter 23](23-equality-and-ordering.md).
> **Suggestion.**

```kotlin
// bad — an overload, not an override; collections still use Any.equals
class Isbn(private val digits: String) {
    operator fun equals(other: Isbn): Boolean = digits == other.digits
}

// good — override the inherited member, and hashCode with it
class Isbn(private val digits: String) {
    override fun equals(other: Any?): Boolean =
        this === other || (other is Isbn && digits == other.digits)

    override fun hashCode(): Int = digits.hashCode()
}

// best, when the type really is a value carrier
@JvmInline
value class Isbn(val digits: String)
```

## 26.10 Prefer implementing `Iterable<T>` to declaring a bare `operator fun iterator()`.

> Why? A `for (x in y)` loop only needs `y.iterator()` with the `operator`
> modifier, so the bare form works — but it works *only* for the `for` loop.
> `Iterable<T>` declares that same function as an operator and additionally
> unlocks the entire stdlib extension surface (`map`, `filter`, `first`,
> `sumOf`, `joinToString`, `associateBy`) plus every Java API that takes an
> `Iterable`. The bare operator is worth using in exactly one situation: as an
> extension that adapts a third-party type you cannot make `Iterable`, kept
> `internal` per §26.16. Note that an `iterator()` returning a fresh iterator
> each call is required — returning the same one makes the second loop over the
> object silently empty. **Suggestion.**

```kotlin
// bad — `for` works, nothing else does, and the iterator is shared
class Playlist(private val tracks: List<Track>) {
    private val shared = tracks.iterator()

    operator fun iterator(): Iterator<Track> = shared
}

for (track in playlist) { /* ... */ }
playlist.map { it.title }   // does not compile
for (track in playlist) { /* never runs — iterator exhausted */ }

// good
class Playlist(private val tracks: List<Track>) : Iterable<Track> {
    override fun iterator(): Iterator<Track> = tracks.iterator()
}

playlist.map { it.title }
```

## 26.11 Define `invoke` only when the receiver genuinely behaves like a function.

> Why? `a()` translates to `a.invoke()`, so defining `invoke` makes an object
> callable. That is right when the type *is* a function with state — a
> configured validator, a policy, a strategy, a parser — and the single
> behaviour it exposes is "apply me to an input". It is wrong when the type has
> several behaviours and you picked one to privilege, because the call site
> then gives the reader no name at all: `handler(event)` says nothing about
> whether that dispatches, enqueues, or validates. When in doubt, prefer a
> named method or a plain function type (`(Event) -> Result`), which needs no
> `invoke` at all. **Suggestion.**

```kotlin
// bad — the type has four behaviours; `cache(key)` privileges one of them
// and reads as a constructor call
class Cache<K, V> {
    operator fun invoke(key: K): V? = get(key)

    fun get(key: K): V? = TODO()
    fun put(key: K, value: V) = TODO()
    fun evict(key: K) = TODO()
}

// good — a single-behaviour type whose whole purpose is to be applied
class MaxLengthRule(private val max: Int) {
    operator fun invoke(value: String): ValidationResult =
        if (value.length <= max) {
            ValidationResult.Valid
        } else {
            ValidationResult.TooLong(value.length, max)
        }
}

val titleRule = MaxLengthRule(max = 120)
val result = titleRule(submission.title)
```

## 26.12 Do not use a companion `invoke` to fake a constructor; give the factory a name.

> Why? `companion object { operator fun invoke(...) }` makes `Thing(x)` compile
> even though `Thing`'s constructor is private, so the call site looks like
> construction while arbitrary code runs — caching, validation, subtype
> selection, I/O. That is precisely the information a reader needs and precisely
> what the syntax hides.
> [Kotlin coding conventions: Factory functions](https://kotlinlang.org/docs/coding-conventions.html#factory-functions)
> pushes the other way: "avoid giving it the same name as the class itself.
> Prefer using a distinct name, making it clear why the behavior of the factory
> function is special." The narrow exception the conventions do allow is a
> top-level function named after an *abstract return type*
> (`fun Foo(): Foo = FooImpl()`), which is a different construct. See
> [Chapter 14](14-objects-and-companions.md). **Suggestion.**

```kotlin
// bad — looks like `new Connection(...)`, actually consults a pool and blocks
class Connection private constructor(private val socket: Socket) {
    companion object {
        operator fun invoke(url: String): Connection = pool.borrow(url)
    }
}

val connection = Connection("db://primary")

// good — the name says what is special
class Connection private constructor(private val socket: Socket) {
    companion object {
        fun borrowFromPool(url: String): Connection = pool.borrow(url)

        fun openDirect(url: String): Connection = Connection(Socket(url))
    }
}

val connection = Connection.borrowFromPool("db://primary")
```

## 26.13 Define `plus` or `plusAssign`, not both — declaring both on a mutable receiver is an ambiguity error.

> Why? The
> [operator overloading reference](https://kotlinlang.org/docs/operator-overloading.html)
> states the resolution rule exactly: for `a += b`, if both `plusAssign` and
> `plus` are applicable, `a` is mutable, and `plus` returns a subtype of `a`'s
> type, the compiler reports an ambiguity; otherwise it falls back to
> `a = a + b`. So the pair is not merely redundant — it is a compile error at
> every `+=` site on a `var`, and the fix is to decide what the type is. An
> immutable type defines `plus` only (and `+=` on a `var` rebinds). A mutable
> collection-like type defines `plusAssign` only (and `+=` mutates in place).
> The same applies to `minus`/`minusAssign`, `times`/`timesAssign`,
> `div`/`divAssign`, and `rem`/`remAssign`. **Suggestion.**

```kotlin
// bad — both defined; `bag += "apple"` fails with an assignment-operator
// ambiguity because `plus` returns a subtype of Bag
class Bag(private val items: MutableList<String> = mutableListOf()) {
    operator fun plus(item: String): Bag = Bag((items + item).toMutableList())

    operator fun plusAssign(item: String) {
        items += item
    }
}

var bag = Bag()
bag += "apple"

// good — pick one. Immutable value type: `plus` only.
data class Bag(val items: List<String> = emptyList()) {
    operator fun plus(item: String): Bag = Bag(items + item)
}

// good — or a mutable container: `plusAssign` only, declared `val`.
class MutableBag {
    private val items = mutableListOf<String>()

    operator fun plusAssign(item: String) {
        items += item
    }
}
```

## 26.14 Know that `+=` on a `var` of a read-only collection type reallocates the whole collection — never do it in a loop.

> Why? This is the most expensive one-character mistake in Kotlin. The stdlib
> defines both `Collection<T>.plus(element)`, returning a brand-new `List<T>`,
> and `MutableCollection<in T>.plusAssign(element)`, which appends in place.
> Which one `+=` picks depends entirely on the declared type of the receiver
> and whether it is `var` or `val` — and the two are one keyword apart. A `var
> List` accumulator in a loop copies every element on every iteration: O(n²)
> time and O(n²) garbage, with no warning from the compiler and no visual
> difference at the call site. Accumulate into a `MutableList` (or `buildList`,
> see [Chapter 25, §25.8](25-immutability.md)) and freeze once at the end.
> **Suggestion.**

```kotlin
// bad — `+=` here resolves to Collection.plus: a full copy per iteration
fun parseAll(lines: List<String>): List<Record> {
    var records: List<Record> = emptyList()
    for (line in lines) {
        records += parse(line) // allocates a new list of size 1, 2, 3, ... n
    }
    return records
}

// good — `+=` resolves to MutableCollection.plusAssign: amortised O(1) append
fun parseAll(lines: List<String>): List<Record> {
    val records = mutableListOf<Record>()
    for (line in lines) {
        records += parse(line)
    }
    return records.toList()
}

// good — or let buildList own the mutable phase entirely
fun parseAll(lines: List<String>): List<Record> = buildList {
    lines.forEach { add(parse(it)) }
}
```

## 26.15 `inc` and `dec` must return a fresh value of type `T` and must not mutate the receiver.

> Why? The
> [operator overloading reference](https://kotlinlang.org/docs/operator-overloading.html)
> is explicit: "The `inc()` and `dec()` functions must return a value, which
> will be assigned to the variable on which the `++` or `--` operation was
> used. They shouldn't mutate the object on which the `inc` or `dec` was
> invoked." Resolution separately "checks that the return type of the function
> is a subtype of `T`". The compiler relies on that: for `a++` it stores the
> initial value of `a` in temporary storage, assigns the result of `inc()` to
> `a`, and returns the stored value; for `++a` it assigns first and yields the
> new value. If `inc()` mutates the receiver *and* returns
> it, the "old value" the compiler saved is the same object, now changed, and
> `val old = counter++` silently gives you the new count. `a++` also requires
> `a` to be assignable, so `inc` on a `val` is dead code. **Suggestion.**

```kotlin
// bad — mutates and returns `this`; postfix `++` yields the already-updated
// value, so `before` and `counter` are the same object
class Counter(var value: Int) {
    operator fun inc(): Counter {
        value++
        return this
    }
}

var counter = Counter(0)
val before = counter++
println(before.value) // 1, not 0

// good — a fresh value each time
@JvmInline
value class Counter(val value: Int) {
    operator fun inc(): Counter = Counter(value + 1)

    operator fun dec(): Counter = Counter(value - 1)
}
```

## 26.16 Do not define operators as extensions on types you do not own, beyond a narrow `internal` or `private` scope.

> Why? An operator extension on a foreign type is invisible at the call site
> and unsearchable from it: a reader who sees `duration / 2` on a
> `java.time.Duration` has no reason to suspect that the meaning comes from
> your file. Worse, extensions do not participate in overload resolution the
> way members do, so if the owning library later adds the same operator as a
> member, the member wins and your semantics change under you with no
> compilation error. Where the convenience is genuinely worth it, keep the
> extension `internal` or `private` so its blast radius is one module, and
> never publish one from a library. The general extension guidance is
> [Kotlin coding conventions: Extension functions](https://kotlinlang.org/docs/coding-conventions.html#extension-functions)
> — "restrict the visibility of extension functions as much as it makes sense."
> **Suggestion.**

```kotlin
// bad — public operator on a JDK type; every consumer of this module now has
// `String / String` in scope with a meaning only this file knows
operator fun String.div(other: String): Path = Path.of(this, other)

// good — the same convenience, contained
internal operator fun Path.div(child: String): Path = resolve(child)

// good — or just use the named API and lose nothing
val config = basePath.resolve("config").resolve("app.yaml")
```

## 26.17 Treat positional destructuring as a versioning hazard: reordering or inserting a `data class` component silently rewrites every destructuring site.

> Why? `val (a, b) = thing` compiles to `component1()` and `component2()`, which
> a `data class` generates from its primary constructor *in declaration order*.
> Insert a component at position 1, or swap two same-typed components, and every
> destructuring call site keeps compiling while binding different values —
> including across module boundaries, where you cannot see the call sites at
> all. Named access and `copy(name = ...)` do not have this property.
> Destructuring stays appropriate where the positions *are* the contract:
> `Pair`, `Triple`, `Map.Entry`, `withIndex()`, and small locals whose
> declaration is on screen. Use `_` for components you do not need, as shown in
> [Kotlin coding conventions: Destructuring declarations](https://kotlinlang.org/docs/coding-conventions.html#destructuring-declarations).
> **Suggestion.**

```kotlin
// bad — adding `middleName` later keeps every call site compiling and every
// one of them now binds the wrong string
data class Name(val first: String, val last: String)

val (first, last) = name

// good — named access survives component changes
val first = name.first
val last = name.last

// good — destructuring where position is genuinely the contract
for ((index, track) in playlist.withIndex()) {
    println("$index: ${track.title}")
}

for ((sku, quantity) in basket.lines) {
    reserve(sku, quantity)
}
```

## 26.18 Declare a function `infix` only when it takes two objects playing a similar role, and never when it mutates the receiver.

> Why?
> [Kotlin coding conventions: Infix functions](https://kotlinlang.org/docs/coding-conventions.html#infix-functions)
> gives both halves: "Declare a function as `infix` only when it works on two
> objects which play a similar role. Good examples: `and`, `to`, `zip`. Bad
> example: `add`," and "Do not declare a method as `infix` if it mutates the
> receiver object." The reason is symmetry: infix notation drops the dot, which
> visually levels receiver and argument, so it lies about any function where
> one side is the container and the other is the contents. Infix also forbids
> named arguments at the call site and requires exactly one parameter, so it
> costs readability wherever the parameter's meaning is not obvious from the
> function name. See [Chapter 8](08-functions.md) for the general form.
> **Suggestion.**

```kotlin
// bad — asymmetric (a list and an element), and it mutates the receiver
infix fun <T> MutableList<T>.add(element: T) {
    this += element
}

results add record

// good — two operands of equal standing, no mutation
infix fun Permission.and(other: Permission): PermissionSet = PermissionSet(this, other)

infix fun Version.isCompatibleWith(other: Version): Boolean = major == other.major

val required = Permission.READ and Permission.WRITE
if (installed isCompatibleWith required.minimumVersion) {
    proceed()
}
```

## 26.19 Do not add `operator fun of` for collection literals in production code — collection literals are Experimental in Kotlin 2.4.

> Why? Kotlin 2.4 introduces collection literals — `val fruit = ["apple",
> "banana"]` — and lets a custom type opt in by declaring `operator fun of` on
> its companion. The feature is **Experimental in Kotlin 2.4** and requires
> `-Xcollection-literals`; it cannot construct Java-defined collections, and a
> literal whose target type cannot be inferred defaults to `List`. Adding
> `operator fun of` to a type today therefore ships an operator that does
> nothing unless every consuming module also sets the flag, and whose behaviour
> may change before it stabilises. Ship a plain `fun of(vararg ...)` factory
> instead — the call site is three characters longer and stable.
> **Suggestion.**

```kotlin
// bad — depends on an Experimental 2.4 feature; the literal only compiles in
// modules built with -Xcollection-literals
class Matrix private constructor(private val rows: List<Row>) {
    companion object {
        operator fun of(vararg rows: Row) = Matrix(rows.toList())
    }
}

val m: Matrix = [Row(1, 2), Row(3, 4)]

// good — an ordinary named factory, stable on every 2.x compiler
class Matrix private constructor(private val rows: List<Row>) {
    companion object {
        fun of(vararg rows: Row) = Matrix(rows.toList())
    }
}

val m = Matrix.of(Row(1, 2), Row(3, 4))
```
