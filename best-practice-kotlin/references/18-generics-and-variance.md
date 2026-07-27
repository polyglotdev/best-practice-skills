<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 18. Generics & Variance

Kotlin's generics are Java's generics plus one large improvement:
**declaration-site variance**. Instead of every caller writing
`List<? extends Animal>` at every use site, the author of `List` writes
`out E` once and every caller gets covariance for free. The Kotlin
documentation summarises the whole model in one line — "Consumer in,
Producer out!"
([Declaration-site variance](https://kotlinlang.org/docs/generics.html#declaration-site-variance)) —
and that line is most of what you need.

Everything else in this chapter is either the fallout of that model
(use-site projections, star projections, function-type variance,
`@JvmSuppressWildcards` at the Java boundary) or the fallout of the one thing
Kotlin inherited unchanged from the JVM: **erasure**. A type argument does
not exist at runtime, so you cannot `is`-check it, cannot instantiate an
array of it, and cannot recover it from a cast. Rules §18.10 through §18.11
are all consequences of that single fact.

The rules draw from
[Generics: in, out, where](https://kotlinlang.org/docs/generics.html) in the
language reference, from
[Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
for the wildcard-generation rules, and from the Android Kotlin style guide on
[type variable names](https://developer.android.com/kotlin/style-guide#type_variable_names).
Neither style guide has anything to say about variance, so the variance rules
below cite the language reference directly rather than attaching a
style-guide anchor to a rule that guide does not make.

Two topics are deferred. **`inline` and `reified` in general** — when to
inline at all, the cost of inlining, non-local returns — are
[Chapter 9, Lambdas & Higher-Order Functions](09-lambdas-and-higher-order-functions.md);
§18.9 covers only what reification buys you for generics. **Platform types,
nullability annotations, and the rest of the Java boundary** are
[Chapter 28, Java Interop](28-java-interop.md); §18.14 and §18.15 cover only
the generic-specific corners.

**Tool alignment:** almost nothing here is linted. The compiler's own
`UNCHECKED_CAST` warning is the one mechanical check that matters (§18.10),
and it becomes a build failure under
`kotlin { compilerOptions { allWarningsAsErrors.set(true) } }` — see
[Chapter 47](47-ktlint-and-detekt.md). `detekt/UnsafeCast` catches casts
that can never succeed, which is a different and narrower problem. detekt's
naming ruleset has no type-parameter rule at all, so §18.16 is a
**Suggestion**, not a **Violation**, despite being a normative style rule.

## 18.1 Declare a type parameter `out` when the type only ever produces it.

> Why? "When a type parameter `T` of a class `C` is declared `out`, it may
> occur only in the out-position in the members of `C`, but in return
> `C<Base>` can safely be a supertype of `C<Derived>`"
> ([Declaration-site variance](https://kotlinlang.org/docs/generics.html#declaration-site-variance)).
> Declaring it once, on the interface, spares every one of your callers from
> writing a projection at every use site — which is precisely the Java
> wildcard tax Kotlin was designed to remove. **Suggestion.**

```kotlin
// bad — invariant, so a Producer<Cat> is not a Producer<Animal> even though
// every value it can ever yield is an Animal
interface Producer<T> {
    fun produce(): T
}

val cats: Producer<Cat> = CatFactory()
val animals: Producer<Animal> = cats   // Type mismatch

// good — declared once, at the declaration site
interface Producer<out T> {
    fun produce(): T
}

val animals: Producer<Animal> = cats   // OK
```

## 18.2 Declare a type parameter `in` when the type only ever consumes it.

> Why? Contravariance is the mirror image, and the standard library uses it
> everywhere you already rely on: `Comparable<in T>`, `Comparator<in T>`,
> and the parameter positions of every function type. A `Sink<Any>` can
> obviously accept a `String`, so it should be usable wherever a
> `Sink<String>` is required — but only `in` makes the compiler agree
> ([Declaration-site variance](https://kotlinlang.org/docs/generics.html#declaration-site-variance)).
> **Suggestion.**

```kotlin
// bad — invariant, so a general-purpose sink cannot be reused for a narrower
// element type and every call site needs its own instance
fun interface Sink<T> {
    fun accept(value: T)
}

val anySink: Sink<Any> = Sink { println(it) }
val stringSink: Sink<String> = anySink   // Type mismatch

// good
fun interface Sink<in T> {
    fun accept(value: T)
}

val stringSink: Sink<String> = anySink   // OK
```

## 18.3 When `out` conflicts with a mutating member, split the type instead of reaching for `@UnsafeVariance`.

> Why? `out T` may occur only in out-positions, so adding `fun put(value: T)`
> to a covariant interface is a compile error: *Type parameter T is declared
> as 'out' but occurs in 'in' position*. That error is not an inconvenience,
> it is the soundness check — without it a `Box<Cat>` upcast to `Box<Animal>`
> would accept a `Dog`. The standard library's answer is the shape to copy: a
> covariant read-only `List<out E>` and an invariant `MutableList<E>` that
> extends it. `@UnsafeVariance` exists as an escape hatch (`Collection<out E>`
> uses it on `contains`), but the name is the documentation: it disables the
> check rather than satisfying it. **Suggestion.**

```kotlin
// bad — does not compile: T is 'out' but occurs in 'in' position
interface Box<out T> {
    fun get(): T
    fun put(value: T)
}

// bad — compiles, and reintroduces exactly the hole the check prevents
interface Box<out T> {
    fun get(): T
    fun put(value: @UnsafeVariance T)
}

// good — the read half is covariant; the write half is invariant
interface Box<out T> {
    fun get(): T
}

interface MutableBox<T> : Box<T> {
    fun put(value: T)
}
```

## 18.4 Use a use-site projection when the class must stay invariant but one function only reads, or only writes.

> Why? `Array<T>` is invariant because it can be both read and written, so a
> `copy(from: Array<Any>, ...)` signature rejects `Array<Int>`. A projection
> narrows what that one parameter permits: "you can only call methods that
> return the type parameter `T`, which in this case means that you can only
> call `get()`"
> ([Type projections](https://kotlinlang.org/docs/generics.html#type-projections)).
> `Array<out Any>` is Java's `Array<? extends Object>` and `Array<in String>`
> is `Array<? super String>` — the same tool, applied where the caller needs
> it rather than baked into the class. **Suggestion.**

```kotlin
// bad — invariance rejects every source array whose type is not exactly Any
fun copy(from: Array<Any>, to: Array<Any>) {
    for (i in from.indices) to[i] = from[i]
}

val ints: Array<Int> = arrayOf(1, 2, 3)
val objects: Array<Any> = Array(3) { "" }
copy(ints, objects)   // Type mismatch: Array<Int> is not Array<Any>

// good — the source is projected: only producing members are callable on it
fun copy(from: Array<out Any>, to: Array<Any>) {
    for (i in from.indices) to[i] = from[i]
}

// good — the mirror image, when the parameter is written to
fun fill(dest: Array<in String>, value: String) {
    for (i in dest.indices) dest[i] = value
}
```

## 18.5 Do not project a collection type that the standard library has already declared variant.

> Why? `List<out E>`, `Set<out E>`, `Collection<out E>`, `Iterable<out T>`,
> `Sequence<out T>`, and `Map<K, out V>` are all covariant already. Writing
> `List<out Animal>` adds nothing; writing `MutableList<out Animal>` is
> worse, because it advertises a mutable type and then forbids mutation, so
> the reader has to work out that you meant `List`. Accept the read-only
> interface and the variance arrives with it. **Suggestion.** See
> [Chapter 20, Collections & Sequences](20-collections-and-sequences.md) and
> [Chapter 25, Immutability](25-immutability.md).

```kotlin
// bad — MutableList is invariant, so this rejects a List<Cat> outright
fun totalWeight(animals: MutableList<Animal>): Double =
    animals.sumOf { it.weightKg }

// bad — a mutable type projected read-only: two wrongs
fun totalWeight(animals: MutableList<out Animal>): Double =
    animals.sumOf { it.weightKg }

// bad — redundant projection; List<E> is already List<out E>
fun totalWeight(animals: List<out Animal>): Double =
    animals.sumOf { it.weightKg }

// good
fun totalWeight(animals: List<Animal>): Double =
    animals.sumOf { it.weightKg }
```

## 18.6 Use a star projection only when the type argument genuinely does not matter, and know it reads as `out TUpper` and writes as `in Nothing`.

> Why? `Foo<*>` is not "any `Foo`" in the loose sense — it has precise
> semantics. For an invariant `Foo<T : TUpper>`, the documentation says
> `Foo<*>` "is equivalent to `Foo<out TUpper>` for reading values and to
> `Foo<in Nothing>` for writing values"
> ([Star-projections](https://kotlinlang.org/docs/generics.html#star-projections)).
> So you can read `Any?` out of a `MutableList<*>` and you can put nothing
> into it — which is exactly right for a `size` or `isEmpty` query, and
> exactly wrong as a way of silencing a type error. **Suggestion.**

```kotlin
// bad — a type parameter that the body never uses, forcing inference work on
// every call site for no benefit
fun <T> describe(items: List<T>): String = "${items.size} items"

// good — the argument truly does not matter here
fun describe(items: List<*>): String = "${items.size} items"

// what a star projection actually permits
val unknown: MutableList<*> = mutableListOf(1, 2, 3)
val first: Any? = unknown[0]   // reads as Any?  (out Any?)
unknown.add(4)                 // does not compile (in Nothing)

// bad — a star projection reached for to dodge a real type error; the cast
// below is unchecked and fails in the caller, not here
fun sum(values: List<*>): Int {
    @Suppress("UNCHECKED_CAST")
    return (values as List<Int>).sum()
}

// good — say what you actually accept
fun sum(values: List<Int>): Int = values.sum()
```

## 18.7 Constrain a type parameter with an upper bound instead of casting inside the body.

> Why? An unbounded `T` is `Any?`, so any body that needs a capability has to
> cast to get it — and that cast is unchecked, so the failure moves from the
> author's compile to the caller's runtime. An upper bound
> ([Upper bounds](https://kotlinlang.org/docs/generics.html#upper-bounds))
> pushes the requirement into the signature, where the compiler rejects the
> bad call site instead. **Suggestion.**

```kotlin
// bad — unbounded T, so the body casts; largest(listOf(Point(1, 2))) compiles
// and throws ClassCastException at runtime
fun <T> largest(items: List<T>): T? =
    items.maxWithOrNull { a, b -> (a as Comparable<T>).compareTo(b) }

// good — the requirement is in the signature, so the bad call does not compile
fun <T : Comparable<T>> largest(items: List<T>): T? = items.maxOrNull()
```

## 18.8 Use a `where` clause when a type parameter needs more than one bound.

> Why? "Only one upper bound can be specified inside the angle brackets. If
> the same type parameter needs more than one upper bound, you need a
> separate `where`-clause"
> ([Upper bounds](https://kotlinlang.org/docs/generics.html#upper-bounds)).
> The alternative — declaring one bound and casting for the other — is §18.7
> all over again, with the cast hidden one level deeper. **Suggestion.**

```kotlin
// bad — only CharSequence is declared, so comparing requires an unchecked cast
fun <T : CharSequence> copyWhenGreater(list: List<T>, threshold: T): List<String> =
    list.filter { (it as Comparable<T>) > threshold }.map { it.toString() }

// good — both requirements are stated, and both are checked at the call site
fun <T> copyWhenGreater(list: List<T>, threshold: T): List<String>
    where T : CharSequence,
          T : Comparable<T> {
    return list.filter { it > threshold }.map { it.toString() }
}
```

## 18.9 Add `reified` (with `inline`) when the function genuinely needs the type argument at runtime.

> Why? Erasure removes the type argument from the compiled body, so `as? T`
> becomes a no-op and `T::class` does not compile at all. `inline` +
> `reified` substitutes the real type into each call site, which makes `is T`,
> `as T`, and `T::class.java` work. The cost is that the function body is
> copied into every caller, so reify the smallest possible function — see
> [Chapter 9](09-lambdas-and-higher-order-functions.md). **Suggestion.**

```kotlin
// bad — T is erased, so `as? T` compiles to nothing: the function hands back
// whatever it was given, and a ClassCastException surfaces later, wherever
// the caller first touches the value at the concrete type
fun <T> Any?.asOrNull(): T? = this as? T   // warning: unchecked cast

// good — reification makes the check real, so the miss is a null, right here
inline fun <reified T> Any?.asOrNull(): T? = this as? T

val n: Int? = "not a number".asOrNull()    // null, as intended

// good — a class literal is only reachable through a reified parameter
inline fun <reified T : Any> loggerFor(): Logger =
    LoggerFactory.getLogger(T::class.java)
```

## 18.10 Never `is`-check a parameterized type, and treat every `UNCHECKED_CAST` suppression as a deferred crash.

> Why? "Cannot check for instance of erased type" is a compile error for
> `value is List<String>`, and the corresponding `as List<String>` compiles
> with only a warning
> ([Type erasure](https://kotlinlang.org/docs/generics.html#type-erasure)).
> Suppressing that warning does not make the cast safe; it moves the
> `ClassCastException` from the cast site to whichever caller first touches
> an element, which is the worst possible place for it to appear. Star
> projections are what erasure can actually support. **Suggestion** — the
> compiler's `UNCHECKED_CAST` warning is the mechanical half, and it fails
> the build under `allWarningsAsErrors`.

```kotlin
// bad — does not compile: cannot check for instance of erased type
fun isStringList(value: Any): Boolean = value is List<String>

// bad — compiles, then explodes somewhere else entirely
@Suppress("UNCHECKED_CAST")
fun asStringList(value: Any): List<String> = value as List<String>

asStringList(listOf(1, 2, 3))       // no failure here...
    .first().length                  // ...ClassCastException here

// good — a star projection is all the runtime can verify
fun isList(value: Any): Boolean = value is List<*>

// good — verify the elements when the element type actually matters
fun asStringListOrNull(value: Any): List<String>? {
    val list = value as? List<*> ?: return null
    return if (list.all { it is String }) list.filterIsInstance<String>() else null
}
```

## 18.11 Do not build an array of a type parameter; use a list, or reify at the boundary.

> Why? Creating `Array<T>` requires the element type at runtime, so
> `arrayOfNulls<T>(n)` inside a non-inline generic declaration is a compile
> error: *Cannot use 'T' as reified type parameter*. The usual workaround —
> allocate `Array<Any?>` and cast — compiles but produces an `Object[]` at
> runtime, so `toTypedArray()`, `System.arraycopy` into a typed target, and
> every Java caller see the wrong array type. A `List` has no such problem,
> and needs no cast. **Suggestion.**

```kotlin
// bad — does not compile
class RingBuffer<T>(capacity: Int) {
    private val slots: Array<T?> = arrayOfNulls(capacity)
}

// bad — compiles, but the runtime array is Object[], not T[]
class RingBuffer<T>(capacity: Int) {
    @Suppress("UNCHECKED_CAST")
    private val slots: Array<T?> = arrayOfNulls<Any?>(capacity) as Array<T?>
}

// good — no reification needed, no cast, no lie about the runtime type
class RingBuffer<T>(private val capacity: Int) {
    private val slots = ArrayList<T?>(capacity)
}

// good — when an array is genuinely required, reify at the boundary
inline fun <reified T> nullArrayOf(size: Int): Array<T?> = arrayOfNulls(size)
```

## 18.12 Put the type parameter on the function when only one member needs it, not on the whole class.

> Why? A class-level parameter is part of the type, so every caller must name
> it even to reach members that ignore it, and one instance can serve exactly
> one element type. A
> [generic function](https://kotlinlang.org/docs/generics.html#generic-functions)
> scopes the parameter to the one member that uses it, so a single instance
> serves every caller and inference usually removes the type argument
> entirely. **Suggestion.**

```kotlin
// bad — the class is generic for one method's benefit; callers need a separate
// Serializer instance per payload type
class Serializer<T>(private val mapper: ObjectMapper) {
    fun encode(value: T): String = mapper.writeValueAsString(value)
    fun contentType(): String = "application/json"
}

val orders = Serializer<Order>(mapper)
val invoices = Serializer<Invoice>(mapper)

// good — one instance, parameter scoped to the member that uses it
class Serializer(private val mapper: ObjectMapper) {
    fun <T> encode(value: T): String = mapper.writeValueAsString(value)
    fun contentType(): String = "application/json"
}

val serializer = Serializer(mapper)
serializer.encode(order)
serializer.encode(invoice)
```

## 18.13 Declare a callback parameter at the exact type you invoke it with — function types are contravariant in parameters and covariant in return.

> Why? `(P) -> R` is `Function1<in P, out R>`, so `(Any) -> String` is a
> subtype of `(String) -> Any`: a function that accepts more and returns less
> is substitutable. Declaring the parameter as `(Any) -> Unit` "to be
> flexible" does the opposite — it forces every caller to widen their
> handler. Declare it narrowly and the broad handlers still fit.
> **Suggestion.**

```kotlin
// a function that accepts more and promises less is a subtype
val describeAnything: (Any) -> String = { it.toString() }
val describeString: (String) -> Any = describeAnything   // OK

val narrow: (String) -> String = { it.uppercase() }
val widened: (Any) -> Any = narrow                        // Type mismatch

// bad — "flexible" parameter type; a specific handler no longer fits
fun onOrderPlaced(handler: (Any) -> Unit) { /* ... */ }

onOrderPlaced { event: OrderPlaced -> ship(event.orderId) }   // Type mismatch

// good — declare the type you actually pass; broader handlers still work
fun onOrderPlaced(handler: (OrderPlaced) -> Unit) { /* ... */ }

onOrderPlaced { event -> ship(event.orderId) }   // specific handler: OK
onOrderPlaced(::logAnything)                     // (Any) -> Unit: also OK
```

## 18.14 Use a definitely non-null type (`T & Any`) when a generic value must be non-null even though `T` itself may be nullable.

> Why? An unbounded `T` has upper bound `Any?`, so `T` can be instantiated as
> `String?` and every `T`-typed value in the signature becomes nullable with
> it. `T & Any` pins that one position to non-null; the documentation notes
> that "a definitely non-nullable type must have a nullable upper bound"
> ([Definitely non-nullable
> types](https://kotlinlang.org/docs/generics.html#definitely-non-nullable-types)),
> so it applies exactly where you need it. Its main job is overriding a
> generic Java method whose parameters and return are annotated `@NotNull` —
> see [Chapter 28](28-java-interop.md). **Suggestion.**

```kotlin
// bad — T can be inferred as String?, so both the fallback and the result are
// nullable and the function guarantees nothing
fun <T> orDefault(value: T?, fallback: T): T = value ?: fallback

val name: String? = orDefault(null, null as String?)   // compiles; returns null

// good — the fallback and the result are definitely non-null
fun <T> orDefault(value: T?, fallback: T & Any): T & Any = value ?: fallback

val name: String = orDefault(null, "unknown")
orDefault(null, null as String?)   // does not compile

// good — the Java-interop case this feature exists for:
// interface Store<T> { @NotNull T load(@NotNull T key); }
class InMemoryStore<T> : Store<T> {
    override fun load(key: T & Any): T & Any = cache.getValue(key)
}
```

## 18.15 Control the Java wildcards Kotlin generates with `@JvmSuppressWildcards` and `@JvmWildcard` when Java has to see the exact type.

> Why? Kotlin translates declaration-site variance into Java wildcards on
> *parameters* — a `List<Item>` parameter becomes `List<? extends Item>`,
> because `List<out E>` is covariant — and generates no wildcards on return
> types, "because otherwise Java clients will have to deal with them"
> ([Variant generics](https://kotlinlang.org/docs/java-to-kotlin-interop.html)).
> One carve-out matters when you read a signature: "when the argument type is
> final, there's usually no point in generating the wildcard", and Kotlin
> classes are final unless declared `open`, so the wildcard below appears only
> because `Item` is an interface. That is usually invisible, and occasionally
> fatal: a Java class
> implementing a Kotlin interface must reproduce the wildcard exactly or its
> method silently fails to override. `@JvmSuppressWildcards` removes the
> wildcard where Java needs the exact type; `@JvmWildcard` adds one where the
> default omits it. **Suggestion.** See [Chapter 28](28-java-interop.md).

```kotlin
interface Item        // not final, so the wildcard is generated

// bad — a Java implementor has to reproduce `List<? extends Item>` exactly;
// writing the obvious `List<Item>` produces an overload, not an override
interface Importer {
    fun importAll(items: List<Item>)
}
// Java sees: void importAll(java.util.List<? extends Item> items)

// good — Java sees the exact type, so the obvious override is the right one
interface Importer {
    fun importAll(items: List<@JvmSuppressWildcards Item>)
}
// Java sees: void importAll(java.util.List<Item> items)

// good — the reverse: return types get no wildcard by default, so ask for one
class Box<out T>(val value: T)

fun boxDerived(value: Derived): Box<@JvmWildcard Derived> = Box(value)
// Java sees: Box<? extends Derived> boxDerived(Derived value)
```

## 18.16 Name a type parameter with a single capital letter, or a class-style name suffixed with `T`.

> Why? The Android Kotlin style guide permits exactly two forms: "a single
> capital letter, optionally followed by a single numeral (such as `E`, `T`,
> `X`, `T2`)" or "a name in the form used for classes, followed by the
> capital letter `T` (such as `RequestT`, `FooBarT`)"
> ([Type variable names](https://developer.android.com/kotlin/style-guide#type_variable_names)).
> The point is that a reader can tell a type parameter from a real type on
> sight. `EntityType` reads like a class; `EntityT` does not.
> **Suggestion** — detekt's naming ruleset has no type-parameter rule, so
> nothing catches this for you.

```kotlin
// bad — lowercase names, and names that read as concrete types
fun <input, output> transform(value: input, f: (input) -> output): output = f(value)

interface Repository<EntityType, IdentifierType> {
    fun findById(id: IdentifierType): EntityType?
}

// good — single capitals for the conventional roles
fun <T, R> transform(value: T, transform: (T) -> R): R = transform(value)

// good — class-style name plus T where a bare letter would be too terse
interface Repository<EntityT, IdT> {
    fun findById(id: IdT): EntityT?
}
```

## 18.17 Do not introduce a type parameter that appears exactly once in the signature.

> Why? A type parameter exists to *relate* two positions — an argument to a
> return, one argument to another. If `T` appears in one place and nowhere
> else, it relates nothing: it is `Any?` with extra ceremony, it makes
> inference work at every call site, and it invites a reader to look for a
> constraint that does not exist. The one genuine exception is a `reified`
> parameter used for its runtime type rather than its position (§18.9).
> **Suggestion.**

```kotlin
// bad — T constrains nothing; this is Any? spelled with angle brackets
fun <T> logValue(value: T) {
    logger.info("value={}", value)
}

// good
fun logValue(value: Any?) {
    logger.info("value={}", value)
}

// good — the exception: T appears once, but reification is the whole point
inline fun <reified T : Any> ObjectMapper.decode(json: String): T =
    readValue(json, T::class.java)
```

## 18.18 Reach for a sealed hierarchy when a generic signature has grown a phantom parameter or a third constraint.

> Why? Generics express "the same behaviour for many types". When a signature
> needs three `where` clauses, or carries a parameter that only some members
> use, it is usually trying to express "one of several *different* cases" —
> which is what a `sealed` type is for. The sealed version gives you an
> exhaustive `when` with no `else` branch, so adding a case becomes a compile
> error rather than a silently unhandled path. **Suggestion.** See
> [Chapter 13, Sealed Types](13-sealed-types.md) and
> [Chapter 22, Control Flow & `when`](22-control-flow-and-when.md).

```kotlin
// bad — three constraints and three nullable fields to model two outcomes;
// nothing stops a caller constructing one with all three null
class ImportResult<T, E, S>(
    val value: T? = null,
    val error: E? = null,
    val stats: S? = null,
) where T : Any,
        E : Throwable,
        S : ImportStats

// good — the cases are named, the invalid combinations are unrepresentable,
// and `when` is exhaustive without an else
sealed interface ImportResult {
    data class Imported(val rows: Int, val stats: ImportStats) : ImportResult
    data class Rejected(val cause: Throwable) : ImportResult
}

fun report(result: ImportResult): String =
    when (result) {
        is ImportResult.Imported -> "imported ${result.rows} rows"
        is ImportResult.Rejected -> "rejected: ${result.cause.message}"
    }
```
