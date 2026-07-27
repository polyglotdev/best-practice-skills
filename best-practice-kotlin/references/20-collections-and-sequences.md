<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 20. Collections & Sequences

Kotlin splits every collection type in two: a read-only interface (`List`,
`Set`, `Map`, `Collection`, `Iterable`) that only reads, and a `Mutable*`
interface that extends it with writes. Almost every collection decision in a
Kotlin codebase follows from taking that split seriously at API boundaries, and
from understanding precisely what it does *not* guarantee — a `List` reference
can be a live view over a `MutableList` that someone else still holds.

This chapter draws on the Kotlin coding conventions'
[Immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability)
and [Loops](https://kotlinlang.org/docs/coding-conventions.html#loops) sections,
the language documentation's
[Collections overview](https://kotlinlang.org/docs/collections-overview.html)
and [Sequences](https://kotlinlang.org/docs/sequences.html) pages, and the
[standard library API reference](https://kotlinlang.org/api/core/) for the
operator vocabulary.

Two topics are deferred. Defensive copying, structural sharing, and what
"immutable" is actually worth in a concurrent program are
[Chapter 25, Immutability](25-immutability.md); §20.2 states the trap and hands
off. Variance — why `List<out E>` is covariant and `MutableList<E>` is not, and
what that means for your own generic types — is
[Chapter 18, Generics & Variance](18-generics-and-variance.md).

**Tool alignment:** a large share of this chapter is mechanically checked.
detekt's `potential-bugs/DontDowncastCollectionTypes`,
`potential-bugs/DoubleMutabilityForCollection`,
`potential-bugs/MapGetWithNotNullAssertionOperator`,
`style/ExplicitCollectionElementAccessMethod`, `style/UseEmptyCounterpart`,
`style/UseOrEmpty`, `style/UnnecessaryFilter`, `style/UseAnyOrNoneInsteadOfFind`,
`style/UseSumOfInsteadOfFlatMapSize`, `style/RedundantHigherOrderMapUsage`,
`style/UselessCallOnNotNull`, `performance/CouldBeSequence`,
`performance/ArrayPrimitive`, `performance/SpreadOperator`, and
`performance/ForEachOnRange` all fire on rules stated below. Rules a named check
enforces are marked **Violation**; the rest are **Suggestion**.

## 20.1 Declare every parameter, return type, and property with the read-only collection interface.

> Why? The coding conventions are explicit: "Always use immutable collection
> interfaces (`Collection`, `List`, `Set`, `Map`) to declare collections which
> are not mutated," and they name the two failure modes in the same breath —
> a `Mutable*` parameter type invites the caller to hand over a live object and
> tells them nothing about whether you will write to it, and a concrete type
> (`ArrayList`, `HashSet`) welds an implementation choice into your API forever.
> The convention text calls `arrayListOf()` bad "because [it] returns
> `ArrayList<T>`, which is a mutable collection type."
> **Suggestion.**

```kotlin
// bad — the signature says "I may mutate this" and pins the implementation
fun validate(actual: String, allowed: HashSet<String>): Boolean = actual in allowed

class Basket {
    val lines: MutableList<Line> = mutableListOf()
}

// bad — arrayListOf returns ArrayList, a mutable concrete type
val allowedValues = arrayListOf("a", "b", "c")

// good — read-only interfaces in, read-only interfaces out
fun validate(actual: String, allowed: Set<String>): Boolean = actual in allowed

class Basket {
    private val _lines = mutableListOf<Line>()
    val lines: List<Line> get() = _lines
}

val allowedValues: List<String> = listOf("a", "b", "c")
```

## 20.2 Remember that read-only is not immutable — copy when the caller must not observe later mutation.

> Why? `List` is an interface, not a guarantee. A `List<Line>` returned from a
> getter that yields the same `MutableList` the class keeps writing to is a live
> view: the caller's "snapshot" changes under them, and any hash-based cache
> keyed on it silently corrupts. The
> [Collections overview](https://kotlinlang.org/docs/collections-overview.html)
> makes the parallel point about `val`: "a mutable collection doesn't have to be
> assigned to a `var`. Write operations with a mutable collection are still
> possible even if it is assigned to a `val`." Read-only means *this reference*
> cannot write. See [Chapter 25, Immutability](25-immutability.md).
> **Suggestion.**

```kotlin
// bad — `lines` is a live window onto the mutable backing list
class Basket {
    private val backing = mutableListOf<Line>()
    val lines: List<Line> get() = backing

    fun add(line: Line) {
        backing += line
    }
}

val snapshot = basket.lines // List<Line>, size 0
basket.add(line)            // snapshot.size is now 1

// good — hand out a copy when the caller must not see later writes
class Basket {
    private val backing = mutableListOf<Line>()
    val lines: List<Line> get() = backing.toList()

    fun add(line: Line) {
        backing += line
    }
}
```

## 20.3 Never cast a read-only collection to its mutable interface.

> Why? The cast usually succeeds, because the read-only reference genuinely does
> point at an `ArrayList`. That is the problem: it silently defeats the one
> guarantee the API surface was making, and it will start throwing
> `UnsupportedOperationException` the day the producer switches to
> `listOf(...)`, `List.of(...)`, or a `buildList` result. detekt's rationale is
> that "the result of the downcast is platform specific and can lead to unexpected
> crashes."
> **Violation — enforced by `detekt/DontDowncastCollectionTypes`.**

```kotlin
// bad — reaches through the read-only interface into the object behind it
fun appendAll(target: List<Line>, extra: List<Line>) {
    (target as MutableList<Line>).addAll(extra)
}

// good — ask for what you need in the signature
fun appendAll(target: MutableList<Line>, extra: List<Line>) {
    target += extra
}

// better — return a new list and leave the caller's data alone
fun withAll(target: List<Line>, extra: List<Line>): List<Line> = target + extra
```

## 20.4 Never declare a `var` whose type is a mutable collection.

> Why? That is two independent axes of mutability on one declaration: the
> reference can be reassigned *and* the object can be written to. Every reader
> then has to establish which one a given line is using, and every concurrency
> argument has to cover both. Pick one — `val` plus a mutable collection when
> you accumulate in place, `var` plus a read-only type when you replace
> wholesale.
> **Violation — enforced by `detekt/DoubleMutabilityForCollection`.**

```kotlin
// bad — reassignable reference to a writable object
var seen: MutableSet<UserId> = mutableSetOf()

// good — mutate the contents, never the reference
val seen: MutableSet<UserId> = mutableSetOf()

// good — replace the whole value, never mutate it
var seen: Set<UserId> = emptySet()
```

## 20.5 Construct conditional collections with `buildList` / `buildSet` / `buildMap`.

> Why? The alternative is a `mutableListOf()` local that accumulates and then
> escapes as the return value — at which point its static type has been
> `MutableList` through the whole function, and whether it stays mutable after
> the `return` depends on the declared return type rather than on anything
> visible at the accumulation site. `buildList` scopes the mutability to the
> builder block and hands back a read-only `List`. It has been Stable since
> Kotlin 1.6. **Suggestion.**

```kotlin
// bad — a mutable local escapes; nothing at the `+=` sites says it will be frozen
fun headers(request: Request): List<String> {
    val result = mutableListOf<String>()
    result += "Accept: application/json"
    if (request.hasBody) {
        result += "Content-Type: application/json"
    }
    return result
}

// good — the mutability lives and dies inside the builder block
fun headers(request: Request): List<String> = buildList {
    add("Accept: application/json")
    if (request.hasBody) {
        add("Content-Type: application/json")
    }
}

// good — the same shape for maps and sets
fun tags(env: String, region: String?): Map<String, String> = buildMap {
    put("env", env)
    region?.let { put("region", it) }
}
```

## 20.6 Use `emptyList()` / `emptySet()` / `emptyMap()` rather than a no-argument factory call.

> Why? `listOf()` allocates nothing a reader can see and states nothing a reader
> can use; `emptyList()` names the intent and returns a shared singleton. detekt
> puts it as "instantiation of an object's 'empty' state should use the object's
> 'empty' initializer for clarity purposes." The same applies on the way out of
> a nullable: `x ?: emptyList()` is spelled `x.orEmpty()`.
> **Violation — enforced by `detekt/UseEmptyCounterpart` and
> `detekt/UseOrEmpty`.**

```kotlin
// bad
fun defaults(): List<Rule> = listOf()
val ids: Set<UserId> = setOf()
val lines = order?.lines ?: emptyList()

// good
fun defaults(): List<Rule> = emptyList()
val ids: Set<UserId> = emptySet()
val lines = order?.lines.orEmpty()
```

## 20.7 Use `listOfNotNull` instead of building a list and filtering nulls out of it.

> Why? `listOf(a, b, c).filterNotNull()` allocates the intermediate list, then
> allocates a second one, and makes the reader infer from the second call what
> the first one was really trying to express. `listOfNotNull` says it once and
> returns `List<T>` rather than `List<T?>`, so the null never enters the type
> system. The mirror-image mistake — calling a null-tolerant helper on a value
> that cannot be null — is flagged by detekt.
> **Suggestion**; `listOf(1).orEmpty()` and friends are a
> **Violation — enforced by `detekt/UselessCallOnNotNull`.**

```kotlin
// bad — two allocations and an inferred intent
val tags: List<String> = listOf(env, region, tenant).filterNotNull()

// bad — a null-tolerant call on a value the compiler knows is non-null
val safe = listOf("a", "b").orEmpty()

// good
val tags: List<String> = listOfNotNull(env, region, tenant)
val safe = listOf("a", "b")
```

## 20.8 Do not use collection literals — `[...]` is Experimental in Kotlin 2.4.

> Why? Bracket syntax for collections landed in
> [Kotlin 2.4](https://kotlinlang.org/docs/whatsnew24.html) as an **Experimental**
> feature. It does not compile without
> `freeCompilerArgs.add("-Xcollection-literals")`, and it carries three sharp
> edges even once enabled: when the expected type cannot be inferred the literal
> defaults to `kotlin.List` (not `Array`, not `Set`), it cannot construct
> collections defined in Java, and a custom type only participates if it declares
> `operator fun of` with a trailing `vararg` in its companion object. Treat an
> unflagged use in production code as a finding, exactly as this skill treats any
> other experimental feature. **Suggestion.**

```kotlin
// bad — Experimental in 2.4; will not compile without -Xcollection-literals
val shapes: MutableList<String> = ["triangle", "square", "circle"]

// bad — no expected type, so this is List<Int>, not Array<Int> and not Set<Int>
val anything = [1, 2, 3]

// bad — collection literals cannot construct a Java-defined collection at all
val javaList: java.util.LinkedList<String> = ["a"]

// good — the stable factory functions say the same thing and pin the type
val shapes: MutableList<String> = mutableListOf("triangle", "square", "circle")
val numbers: List<Int> = listOf(1, 2, 3)
val unique: Set<Int> = setOf(1, 2, 3)
```

## 20.9 Convert to a `Sequence` only when the chain is long, the input is large, or the terminal operation short-circuits.

> Why? The [Sequences](https://kotlinlang.org/docs/sequences.html) page states
> both halves of the trade: a `Sequence` lets "you avoid building results of
> intermediate steps, therefore improving the performance of the whole
> collection processing chain," but "the lazy nature of sequences adds some
> overhead which may be significant when processing smaller collections or doing
> simpler computations." An `Iterable` chain materialises one list per operator;
> a `Sequence` chain materialises none, but allocates a wrapper per operator and
> makes an indirect call per element per stage. The win is real for long chains
> over large inputs, and for anything ending in `first`, `find`, `any`, or
> `take`, where laziness stops the work early. It is negative for a two-operator
> chain over ten elements. **Suggestion** — `detekt/CouldBeSequence` flags long
> chains by count and cannot know your input size, so treat it as a prompt to
> measure rather than a verdict.

```kotlin
// bad — three intermediate Lists built over 500_000 rows to find one element
val firstFailure = rows
    .map(::parse)
    .filter { it.status == Status.FAILED }
    .firstOrNull()

// good — parse and test one row at a time, and stop at the first match
val firstFailure = rows
    .asSequence()
    .map(::parse)
    .filter { it.status == Status.FAILED }
    .firstOrNull()

// bad — a sequence over three elements pays the wrapper cost for nothing
val names = listOf(a, b, c).asSequence().map { it.name }.toList()

// good
val names = listOf(a, b, c).map { it.name }
```

## 20.10 Terminate every sequence chain — an intermediate operation on its own does nothing.

> Why? "If a sequence operation returns another sequence, which is produced
> lazily, it's called intermediate. Otherwise, the operation is terminal ...
> Sequence elements can be retrieved only with terminal operations." A chain
> that ends in `map` or `filter` is a description of work, not the work. On an
> `Iterable` the same line would have executed eagerly, which is exactly why
> this bug survives the conversion to `asSequence()` and gets discovered in
> production. **Suggestion.**

```kotlin
// bad — nothing runs: `map` is intermediate and the resulting Sequence is dropped
files.asSequence().map { it.delete() }

// good — a terminal operation drives the chain
val deleted: List<Boolean> = files.asSequence().map { it.delete() }.toList()

// better — a side effect is not a `map`; use a loop and say so
for (file in files) {
    file.delete()
}
```

## 20.11 Index once with `associateBy` or `groupBy` instead of scanning inside a loop.

> Why? `first { }`, `find { }`, `any { }`, and `contains` on a `List` are O(n).
> Calling one inside a loop over another collection is O(n·m), and it looks
> exactly like the O(n) version at a glance — there is no syntactic signal.
> Building the index costs one pass and turns every subsequent lookup into O(1).
> The coding conventions' [Loops](https://kotlinlang.org/docs/coding-conventions.html#loops)
> section makes the general point: "understand the cost of the operations being
> performed in each case and keep performance considerations in mind."
> **Suggestion.**

```kotlin
// bad — scans the whole customer list once per order
fun enrich(orders: List<Order>, customers: List<Customer>): List<EnrichedOrder> =
    orders.map { order ->
        EnrichedOrder(order, customers.first { it.id == order.customerId })
    }

// good — one pass to index, then O(1) per order
fun enrich(orders: List<Order>, customers: List<Customer>): List<EnrichedOrder> {
    val byId = customers.associateBy(Customer::id)
    return orders.map { order ->
        EnrichedOrder(order, byId.getValue(order.customerId))
    }
}
```

## 20.12 Use the operator that names the intent instead of `fold` or a manual accumulator.

> Why? The coding conventions ask you to "prefer using higher-order functions
> (`filter`, `map` etc.) to loops," but the point is not that `fold` is a
> higher-order function — it is that the reader should not have to run the
> accumulator in their head to discover you were grouping. `groupBy`,
> `partition`, `sumOf`, and `groupingBy().eachCount()` each state a specific
> operation, return the right type without a cast, and cannot be got subtly
> wrong. **Suggestion.**

```kotlin
// bad — fold doing four jobs the stdlib already names
val byStatus = orders.fold(mutableMapOf<Status, MutableList<Order>>()) { acc, order ->
    acc.getOrPut(order.status) { mutableListOf() }.add(order)
    acc
}
val totalMinor = orders.map { it.totalMinor }.sum()
val paid = orders.filter { it.isPaid }
val unpaid = orders.filter { !it.isPaid }
val perStatus = orders.groupBy(Order::status).mapValues { it.value.size }

// good
val byStatus: Map<Status, List<Order>> = orders.groupBy(Order::status)
val totalMinor: Long = orders.sumOf(Order::totalMinor)
val (paid, unpaid) = orders.partition(Order::isPaid)
val perStatus: Map<Status, Int> = orders.groupingBy(Order::status).eachCount()
```

## 20.13 Pick the right member of the `associate` family: `associateBy` derives the key, `associateWith` derives the value, `associate` derives both.

> Why? All three produce a `Map`, so all three typecheck, and `associate { it.id
> to it }` is the form people reach for because it mirrors what a loop would do.
> Naming the variant tells the reader in one word which side of the pair came
> from the element — and `associateBy(Customer::id)` admits a method reference,
> which the `to`-pair form cannot. **Suggestion.**

```kotlin
// bad — `associate` used where one side of the pair is just the element
val byId = customers.associate { it.id to it }
val nameLengths = names.associate { it to it.length }

// good — the name says which side is derived
val byId: Map<CustomerId, Customer> = customers.associateBy(Customer::id)
val nameLengths: Map<String, Int> = names.associateWith(String::length)

// good — `associate` when both sides really are derived
val loyalty: Map<String, Int> = customers.associate { it.email to it.loyaltyPoints }
```

## 20.14 Choose between `first`, `single`, and their `OrNull` variants deliberately — they fail differently.

> Why? These four are not interchangeable and their failure modes are not
> obvious from the names. `first()` and `first { }` throw
> `NoSuchElementException` when nothing matches. `single()` throws
> `NoSuchElementException` when the collection is empty but
> `IllegalArgumentException` when it has more than one element — it is the only
> one that enforces uniqueness. `firstOrNull` returns `null` for "nothing
> matched", while `singleOrNull` returns `null` for *both* "nothing matched" and
> "more than one matched", which silently converts a duplicate-data bug into a
> missing-data one. **Suggestion.**

```kotlin
// bad — `first` on a collection that is legitimately allowed to be empty
val admin = users.first { it.role == Role.ADMIN }

// bad — `firstOrNull` where "exactly one" is the invariant; a duplicated
// config row is silently accepted and the second one ignored
val config = configs.firstOrNull { it.env == env }

// bad — `singleOrNull` conflates "none" with "too many"
val config = configs.singleOrNull { it.env == env } ?: Config.DEFAULT

// good — zero is a legal case, so handle it explicitly
val admin = users.firstOrNull { it.role == Role.ADMIN }
    ?: error("no admin configured for tenant $tenantId")

// good — "exactly one" is the invariant, so let `single` enforce it
val config = configs.single { it.env == env }
```

## 20.15 Never structurally modify a collection while iterating it.

> Why? `for (x in list) { list.remove(x) }` throws
> `ConcurrentModificationException` from the underlying `ArrayList` iterator —
> usually not on the first removal, which is why this survives a quick manual
> test and fails on the input with two expired sessions. The stdlib has
> predicate-driven mutators (`removeAll`, `retainAll`) that do the whole pass
> without an iterator to invalidate; when the body needs to do more than remove,
> iterate a snapshot. **Suggestion.**

```kotlin
// bad — ConcurrentModificationException, and not reliably on the first removal
val sessions = mutableListOf(a, b, c)
for (session in sessions) {
    if (session.isExpired) {
        sessions.remove(session)
    }
}

// good — one predicate-driven pass, no live iterator
sessions.removeAll { it.isExpired }

// good — when the body must do more, iterate a snapshot
for (session in sessions.toList()) {
    if (session.isExpired) {
        session.close()
        sessions.remove(session)
    }
}
```

## 20.16 Prefer a `for` loop to `forEach`, except on a nullable receiver or at the end of a chain.

> Why? The coding conventions carve out this exact exception: "Prefer using
> higher-order functions (`filter`, `map` etc.) to loops. Exception: `forEach`
> (prefer using a regular `for` loop instead, unless the receiver of `forEach` is
> nullable or `forEach` is used as part of a longer call chain)." A `for` loop
> gives the element a name, allows `break` and `continue`, and makes `return`
> mean what it looks like. On a range, `forEach` is also measurably slower
> because the range is iterated through `Iterable` rather than compiled to a
> counting loop.
> **Violation — enforced by `detekt/ForEachOnRange`** for the range case; the
> general case is a **Suggestion**.

```kotlin
// bad — a plain loop written as a lambda; the element has no name
orders.forEach {
    audit.record(it.id)
}

// bad — forEach on a range, iterated through Iterable
(0..<pageCount).forEach { page -> fetch(page) }

// good
for (order in orders) {
    audit.record(order.id)
}

for (page in 0..<pageCount) {
    fetch(page)
}

// good — the two exceptions the conventions name
maybeOrders?.forEach { audit.record(it.id) }
orders.asSequence().filter(Order::isPaid).forEach { audit.record(it.id) }
```

## 20.17 Use `List` rather than `Array`; reserve the primitive arrays for measured hot paths and Java boundaries.

> Why? `Array<T>` is the wrong default in Kotlin on three counts. Its `equals`
> and `hashCode` are referential, so two arrays with identical contents are
> never equal and an array is useless as a map key. `Array<Int>` boxes every
> element — detekt's rationale is that "using `Array<Primitive>` leads to
> implicit boxing and performance hit," and `IntArray` is the fix when you
> genuinely need one. And passing a list to a `vararg` parameter needs
> `*list.toTypedArray()`, where "using a spread operator causes a full copy of
> the array to be created before calling a method."
> **Violation — enforced by `detekt/ArrayPrimitive` and
> `detekt/SpreadOperator`.**

```kotlin
// bad — boxes every element, and Array equality is referential
val scores: Array<Int> = arrayOf(1, 2, 3)
fun applyRules(rules: Array<Rule>) { /* ... */ }
applyRules(*ruleList.toTypedArray()) // full copy on every call

// good — List everywhere the API is yours
val scores: List<Int> = listOf(1, 2, 3)
fun applyRules(rules: List<Rule>) { /* ... */ }
applyRules(ruleList)

// good — a primitive array where the profiler says the boxing matters
val scores: IntArray = intArrayOf(1, 2, 3)
```

## 20.18 Access a map with `[ ]`, and never paper over the nullable result with `!!`.

> Why? `map[key]` is the idiomatic accessor — detekt notes that "in Kotlin
> functions `get` or `set` can be replaced with the shorter operator `[]`" — and
> it returns `V?` precisely because a missing key is a real outcome. `!!` on
> that result converts a modelled absence into a `NullPointerException` with no
> message and no key name in the stack trace. Decide instead: `?:` for a
> default, `getValue` when a missing key is a programming error and you want a
> `NoSuchElementException` that names the key, `getOrElse` when the fallback is
> computed.
> **Violation — enforced by `detekt/ExplicitCollectionElementAccessMethod` and
> `detekt/MapGetWithNotNullAssertionOperator`.**

```kotlin
// bad — verbose accessor plus a bang that discards the key name
val region = config.get("region")!!

// good — indexing, plus an explicit decision about absence
val region = config["region"] ?: DEFAULT_REGION

// good — a missing key is a bug here; getValue throws NoSuchElementException
val region = config.getValue("region")

// good — computed fallback without inserting it
val region = config.getOrElse("region") { resolveRegionFromMetadata() }
```

## 20.19 Use the single-pass operator instead of chaining two that produce an intermediate list.

> Why? `filter { }.count()` builds a whole list to ask a question about its length;
> `find { } != null` builds a result to throw it away; `flatMap { }.size`
> flattens millions of elements to count them. Each has a single-pass equivalent
> that allocates nothing, and each is a named detekt rule because the shorter
> form is also the clearer one — `count { }` says "how many", `any { }` says
> "is there one".
> **Violation — enforced by `detekt/UnnecessaryFilter`,
> `detekt/UseAnyOrNoneInsteadOfFind`, `detekt/UseSumOfInsteadOfFlatMapSize`, and
> `detekt/RedundantHigherOrderMapUsage`.**

```kotlin
// bad — an intermediate collection per link, and a name that hides the question
val failures = results.filter { it.isFailure }.count()
val hasAdmin = users.find { it.role == Role.ADMIN } != null
val lineCount = orders.flatMap { it.lines }.size
val names = users.map { it }.map { it.name }

// good
val failures = results.count { it.isFailure }
val hasAdmin = users.any { it.role == Role.ADMIN }
val lineCount = orders.sumOf { it.lines.size }
val names = users.map { it.name }
```
