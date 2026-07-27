<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 6. Null Safety

Null safety is the single feature that most distinguishes Kotlin from the
Java it interoperates with, and it is the one most often thrown away by a
two-character operator. This chapter is the centrepiece of the skill: it
bans `!!` outright, gives the ordered list of things to do instead, maps
exactly where smart casting stops working, and sets the rule that no platform
type from Java is allowed to travel into Kotlin code without being given a
type at the boundary.

It draws on the [Kotlin null safety
reference](https://kotlinlang.org/docs/null-safety.html), the [smart cast
prerequisites](https://kotlinlang.org/docs/typecasts.html#smart-cast-prerequisites),
[Java interop: null-safety and platform
types](https://kotlinlang.org/docs/java-interop.html#null-safety-and-platform-types),
and the coding conventions on
[platform types](https://kotlinlang.org/docs/coding-conventions.html#platform-types)
and
[nullable Boolean values in conditions](https://kotlinlang.org/docs/coding-conventions.html#nullable-boolean-values-in-conditions).

Two neighbouring topics are deferred. The mechanics of the Java side —
`@JvmStatic`, SAM conversion, mapped types, and how Kotlin's own nullability
appears to a Java caller — are
[Chapter 28, Java Interop](28-java-interop.md); §6.10 and §6.11 cover only
the nullability half. `as`, `as?`, and the rest of the cast operators are
[Chapter 7, Types & Type Aliases](07-types-and-type-aliases.md); §6.1 and
§7.9 meet at the same failure. Where a deeply nullable chain is really a
missing sum type, see [Chapter 13, Sealed Types](13-sealed-types.md).

**Tool alignment:** most of this chapter is mechanically enforceable.
`detekt/UnsafeCallOnNullableType` fires on every `!!`;
`detekt/MapGetWithNotNullAssertionOperator`, `detekt/HasPlatformType`,
`detekt/NullCheckOnMutableProperty`, `detekt/NullableBooleanCheck`,
`detekt/NullableToStringCall`, `detekt/UnnecessarySafeCall`,
`detekt/UnnecessaryNotNullOperator`, `detekt/UnnecessaryNotNullCheck`,
`detekt/CanBeNonNullable`, and `detekt/UnnecessaryLet` cover most of the
rest. Rules a named check enforces are marked **Violation**; the rest are
**Suggestion**.

## 6.1 Never write `!!`.

> Why? The [reference](https://kotlinlang.org/docs/null-safety.html#not-null-assertion-operator)
> describes exactly what it does: "if the value is `null`, the `!!` operator
> forces it to be treated as non-nullable, which results in an NPE." That
> NPE carries no message, no field name, and no indication of which of the
> three `!!` on the line fired — it is strictly worse than the Java NPE it
> replaces, because a Java NPE at least has helpful-NPE messages on modern
> JVMs. Every `!!` is a claim the compiler could not verify, written in a
> syntax that makes it invisible in review. If the claim is true, one of
> §6.2 to §6.8 expresses it in a way the compiler *can* verify. If it is
> false, you have shipped a crash.
> **Violation — enforced by `detekt/UnsafeCallOnNullableType`.**

```kotlin
// bad — three assertions on one line; the NPE names none of them
fun shippingLabel(order: Order): String =
    order.customer!!.address!!.postcode!!

// good — the absent case is named and handled
fun shippingLabel(order: Order): String? =
    order.customer?.address?.postcode

// good — the absent case is a bug, so say so, with a message
fun shippingLabel(order: Order): String =
    requireNotNull(order.customer?.address?.postcode) {
        "order ${order.id} has no shipping postcode"
    }
```

## 6.2 Before reaching for any null-handling operator, restructure so the value cannot be null.

> Why? Every `?.`, `?:`, and null check is a small tax paid at every use
> site, forever. Most nullable properties are nullable because a constructor
> was allowed to leave them unset, or because a `null` was used as an
> "unknown" sentinel that some later step always fills in. Push the
> requirement into the type: a required constructor parameter, a non-null
> field with a default, a
> [sealed type](13-sealed-types.md) that models "not yet loaded" as its own
> case. A type that cannot be null needs no null handling anywhere.
> **Violation — enforced by `detekt/CanBeNonNullable`,** which reports
> nullable properties and parameters that are never actually null.

```kotlin
// bad — nullable because construction is two-phase; now every consumer of
// every field pays for it
class Session {
    var userId: UserId? = null
    var startedAt: Instant? = null
    var locale: Locale? = null

    fun describe(): String = "${userId} since ${startedAt} (${locale})"
}

// good — the type makes the invariant unnecessary to check
class Session(
    val userId: UserId,
    val startedAt: Instant,
    val locale: Locale = Locale.UK,
) {
    fun describe(): String = "$userId since $startedAt ($locale)"
}
```

## 6.3 Use `?.` to reach through a value that may be absent, and let the whole chain evaluate to `null`.

> Why? "Instead of throwing an NPE, if the object is `null`, the `?.`
> operator simply returns `null`." A chain of safe calls short-circuits at
> the first absent link, which is almost always the semantics you want and is
> a single character per link. The alternative — nested `if (x != null)` —
> costs a level of indentation per link and puts the interesting expression
> at the bottom of a staircase.
> **Suggestion.**

```kotlin
// bad — four levels of nesting to express one expression
fun managerEmail(employee: Employee): String? {
    val department = employee.department
    if (department != null) {
        val head = department.head
        if (head != null) {
            return head.email
        }
    }
    return null
}

// good
fun managerEmail(employee: Employee): String? =
    employee.department?.head?.email
```

## 6.4 Use `?:` to supply the fallback at the point of use, not a `null` default at the declaration.

> Why? "If the expression to the left of `?:` is not `null`, the Elvis
> operator returns it. Otherwise, the Elvis operator returns the expression
> to the right. The expression on the right-hand side is evaluated only if
> the left-hand side is `null`." That laziness matters: the fallback can be
> an expensive lookup or a `throw` without costing anything on the happy
> path. Writing the fallback at the use site also lets two different callers
> disagree about what "absent" means, which a single hardcoded default in the
> producer cannot express.
> **Suggestion.**

```kotlin
// bad — the producer guesses one default for everybody, and the caller can
// no longer tell "absent" from "genuinely UK"
fun countryOf(order: Order): String = order.address?.country ?: "GB"

// good — the producer reports absence; each caller decides
fun countryOf(order: Order): String? = order.address?.country

val forInvoice = countryOf(order) ?: billingCountry(order)
val forDisplay = countryOf(order) ?: "Unknown"
```

## 6.5 Use `?:` with `return` or `throw` to exit early, so the rest of the function works with a non-null value.

> Why? "Since `throw` and `return` are expressions in Kotlin, you can also
> use them on the right-hand side of the Elvis operator." The right-hand side
> then has type `Nothing`, which is a subtype of every type (see
> [§7.3](07-types-and-type-aliases.md)), so the compiler narrows the
> left-hand expression to its non-null type for everything below. One line
> converts a nullable into a non-null local and removes the need for any
> further null handling in the function body — this is the single most
> valuable null idiom in the language.
> **Suggestion.**

```kotlin
// bad — the nullability leaks all the way down the function
fun renderInvoice(orderId: OrderId): String {
    val order = repository.find(orderId)
    val customer = order?.customer
    return "${customer?.name ?: "?"}: ${order?.total ?: Money.ZERO}"
}

// good — two guards, then plain non-null code
fun renderInvoice(orderId: OrderId): String {
    val order = repository.find(orderId) ?: return "unknown order $orderId"
    val customer = order.customer
        ?: throw IllegalStateException("order $orderId has no customer")
    return "${customer.name}: ${order.total}"
}
```

## 6.6 When a `null` means a programming error rather than a legitimate state, use `requireNotNull` or `checkNotNull` with an informative message.

> Why? `requireNotNull(value) { "..." }` returns the non-null value and
> throws `IllegalArgumentException` with your message when it is `null`;
> `checkNotNull` is the same shape but throws `IllegalStateException`. That
> is the whole difference between them and `!!`: a named exception type that
> classifies the failure (bad argument versus broken invariant) and a message
> that tells whoever reads the log *which* value was missing and in what
> context. Use `requireNotNull` for arguments crossing into your code and
> `checkNotNull` for your own state.
> **Suggestion** — but the `!!` these replace is a
> **Violation — enforced by `detekt/UnsafeCallOnNullableType`.**

```kotlin
// bad — "java.lang.NullPointerException" and nothing else
fun activate(config: Map<String, String>) {
    val region = config["region"]!!
    val key = config["apiKey"]!!
    connect(region, key)
}

// good — the exception names the missing key and the operation
fun activate(config: Map<String, String>) {
    val region = requireNotNull(config["region"]) { "config is missing 'region'" }
    val key = requireNotNull(config["apiKey"]) { "config is missing 'apiKey'" }
    connect(region, key)
}

// good — a broken internal invariant is an IllegalStateException
fun flush() {
    val open = checkNotNull(connection) { "flush() called before connect()" }
    open.write(buffer)
}
```

## 6.7 Prefer a plain null check that enables smart casting to `?.let` when the block is more than a single expression.

> Why? After `if (x == null) return`, the compiler smart-casts `x` to its
> non-null type for the rest of the scope, so the body reads as ordinary
> non-null code with no extra nesting and no `it`. `?.let { }` introduces a
> lambda, an implicit `it`, and a return value nobody wants when the block is
> a sequence of statements — and it silently makes the whole expression
> `null` when the receiver is `null`, which is easy to miss when the result is
> discarded. Save `?.let` for the case it was designed for: transforming a
> nullable into another value (see §6.17 and
> [Chapter 19, Scope Functions](19-scope-functions.md)).
> **Violation — enforced by `detekt/UnnecessaryLet`** for the degenerate
> single-call cases; **Suggestion** for the rest.

```kotlin
// bad — a statement block wearing a lambda, and an unused Unit? result
fun handle(event: Event?) {
    event?.let {
        audit.record(it)
        metrics.increment(it.type)
        dispatcher.publish(it)
    }
}

// good — guard, then flat non-null code
fun handle(event: Event?) {
    if (event == null) return
    audit.record(event)
    metrics.increment(event.type)
    dispatcher.publish(event)
}
```

## 6.8 Know exactly when smart casting fails, and copy the value into a local `val` when it does.

> Why? Smart casting is not "the compiler noticed a null check"; it is a
> guarantee that the value cannot change between the check and the use. The
> [reference](https://kotlinlang.org/docs/typecasts.html#smart-cast-prerequisites)
> spells out where that guarantee does not hold:
> `val` local variables always smart-cast "except local delegated
> properties"; `val` *properties* only "if the property is `private`,
> `internal`, or if the check is performed in the same module where the
> property is declared", and never for `open` properties or properties with
> custom getters; `var` local variables only "if the variable is not modified
> between the check and its usage, is not captured in a lambda that modifies
> it, and is not a local delegated property"; and `var` properties **never**,
> "because the variable can be modified at any time by other code." The fix
> is never `!!` — it is one line that copies the value into a local `val`,
> after which the check and the use are talking about the same value by
> construction.
> **Violation — enforced by `detekt/NullCheckOnMutableProperty`,** which
> reports a null check on a mutable property precisely because it does not
> smart-cast.

```kotlin
// bad — `listener` is a var property, so it never smart-casts, and the usual
// "fix" is an assertion
class Uploader {
    var listener: ProgressListener? = null

    fun report(percent: Int) {
        if (listener != null) {
            listener!!.onProgress(percent) // no smart cast; !! papers over it
        }
    }
}

// good — one local val; the check and the call see the same value
class Uploader {
    var listener: ProgressListener? = null

    fun report(percent: Int) {
        val current = listener ?: return
        current.onProgress(percent)
    }
}

// bad — a custom getter can return a different value on each call, so this
// does not smart-cast either
class Registry(private val source: Source) {
    val active: Node? get() = source.lookup()

    fun refresh() {
        if (active != null) {
            active!!.reload()
        }
    }
}

// good
class Registry(private val source: Source) {
    val active: Node? get() = source.lookup()

    fun refresh() {
        val node = active ?: return
        node.reload()
    }
}
```

## 6.9 Never `!!` the result of a `Map` lookup; say which behaviour you meant with `getValue`, `getOrElse`, or an explicit check.

> Why? `map[key]!!` is the most common `!!` in real Kotlin, and it is the
> one with the best replacements. `map.getValue(key)` throws
> `NoSuchElementException` naming the missing key — a far better failure than
> a bare NPE. `map.getOrElse(key) { default }` supplies a fallback lazily.
> On the JVM only, `map.getOrDefault(key, default)` supplies an eager one —
> it is a `java.util.Map` default method surfaced through `kotlin.collections`
> and is not available in common Multiplatform code. Each states an intent
> that `!!` erases.
> **Violation — enforced by `detekt/MapGetWithNotNullAssertionOperator`.**

```kotlin
// bad — NPE with no indication of which key was missing
val handler = handlers[event.type]!!
handler.handle(event)

// good — throws NoSuchElementException naming the key
val handler = handlers.getValue(event.type)
handler.handle(event)

// good — fall back deliberately
val handler = handlers.getOrElse(event.type) { NoopHandler }
handler.handle(event)

// good — treat "no handler" as a real branch
val handler = handlers[event.type] ?: return HandleResult.Unsupported(event.type)
handler.handle(event)
```

## 6.10 Give every value crossing from Java an explicit Kotlin type at the boundary.

> Why? A Java value has a *platform type*, written `T!` in diagnostics, which
> "means `T` or `T?`" — the compiler suspends null checking for it entirely.
> Platform types "can't be mentioned explicitly in the program", so a platform
> type that is allowed to propagate through inference silently disables null
> safety for every declaration downstream, and the eventual NPE surfaces
> nowhere near the Java call that produced the `null`. Assigning to a declared
> non-null type makes the compiler "emit an assertion upon assignment," so
> the failure lands at the boundary with the boundary's stack frame. The
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#platform-types)
> make this a hard rule for anything visible: "A public function/method
> returning an expression of a platform type must declare its Kotlin type
> explicitly," and "any property (package-level or class-level) initialized
> with an expression of a platform type must declare its Kotlin type
> explicitly." Only a local may leave it inferred.
> **Violation — enforced by `detekt/HasPlatformType`.**

```kotlin
// bad — the inferred type is String!, so `name` is neither checked nor
// checkable, and the NPE surfaces at some caller far from here
class Person {
    val name = MyJavaApi.getProperty("name")
}

fun apiCall() = MyJavaApi.getProperty("name")

// good — the boundary decides, and the assertion fires here
class Person {
    val name: String = MyJavaApi.getProperty("name")
}

fun apiCall(): String = MyJavaApi.getProperty("name")

// good — when the Java side really can return null, say so
fun optionalHeader(): String? = MyJavaApi.getHeader("X-Trace-Id")
```

## 6.11 Configure the compiler to honour the Java side's nullability annotations instead of guessing.

> Why? A platform type is what you get when the Java declaration says
> nothing. When it *does* say something, Kotlin can use it: "Java types that
> have nullability annotations are represented not as platform types, but as
> actual nullable or non-nullable Kotlin types." Kotlin understands JetBrains
> `org.jetbrains.annotations`, JSpecify `org.jspecify.annotations`, JSR-305
> `javax.annotation`, Android, Eclipse, Lombok, and others. Two settings
> matter. JSR-305 defaults to warnings — "the default behavior is the same to
> `-Xjsr305=warn`" — so a mismatch compiles; set `-Xjsr305=strict` to make it
> an error. JSpecify is the exception: it is "the only supported flavor that
> uses `strict` report level by default", so a `@NullMarked` Java package or
> type gives you real Kotlin types with no configuration at all. On a Java
> codebase you control, adding JSpecify `@NullMarked` and `@Nullable` is the
> highest-leverage change you can make for its Kotlin callers — every
> platform type on the other side of the boundary becomes a checked one.
> **Suggestion.**

```kotlin
// bad — build.gradle.kts leaves JSR-305 at its default, so a @Nonnull
// violation is a warning nobody reads
kotlin {
    compilerOptions {
        // nothing configured
    }
}

// good
kotlin {
    compilerOptions {
        freeCompilerArgs.addAll(
            "-Xjsr305=strict",
            "-Xjspecify-annotations=strict",
        )
    }
}

// good — with the Java side annotated `@NullMarked`, these are real Kotlin
// types and neither one is a platform type
val account: String = ledgerApi.requiredAccount()
val memo: String? = ledgerApi.optionalMemo()
```

## 6.12 Use `lateinit` only for a non-null value a framework assigns before first read, and check it with `isInitialized` rather than a null check.

> Why? `lateinit` is a targeted escape hatch for dependency injection, test
> fixtures, and framework callbacks — cases where a value is genuinely
> non-null from the first read onward but cannot be supplied to the
> constructor. Used anywhere else it is strictly worse than a nullable type:
> you lose the compiler's help, and an early read throws
> `UninitializedPropertyAccessException` instead of giving you a `null` you
> could have handled. It also cannot express "absent" as a state, so any
> code that legitimately needs to ask "is it there yet?" has to use
> `this::prop.isInitialized`. If you find yourself wanting that check in
> business logic, the property should have been nullable (or the object
> should not have existed yet). See [§5.16](05-declarations-and-visibility.md)
> for the three-way choice against `by lazy`.
> **Suggestion** — `detekt/LateinitUsage` can flag every occurrence if
> configured to, but cannot distinguish a legitimate injection point.

```kotlin
// bad — lateinit standing in for a value that is legitimately absent, so
// every read is a potential UninitializedPropertyAccessException
class Draft {
    lateinit var submittedAt: Instant

    fun isSubmitted(): Boolean = this::submittedAt.isInitialized
}

// good — absence is a real state, so it is a nullable type
class Draft {
    var submittedAt: Instant? = null
        private set

    fun isSubmitted(): Boolean = submittedAt != null
}

// good — lateinit where a framework guarantees assignment before first read
class LedgerServiceTest {
    private lateinit var service: LedgerService

    @BeforeEach
    fun setUp() {
        service = LedgerService(InMemoryRepository())
    }
}
```

## 6.13 Compare a nullable `Boolean` with `== true` or `!= false`, never with `?: true`/`?: false`.

> Why? The [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#nullable-boolean-values-in-conditions)
> give exactly one instruction: "If you need to use a nullable `Boolean` in a
> conditional statement, use `if (value == true)` or `if (value == false)`
> checks." The Elvis forms say the same thing in more characters and read
> ambiguously — `flag ?: false` makes the reader stop and work out which of
> the three states maps where, whereas `flag == true` is unambiguous by
> construction: only `true` passes. The distinction matters because
> `!(flag == true)` and `flag == false` are different tests when `flag` is
> `null`.
> **Violation — enforced by `detekt/NullableBooleanCheck`.**

```kotlin
// bad
if (user.isVerified ?: false) {
    grantAccess(user)
}
if (!(feature.enabled ?: true)) {
    skip(feature)
}

// good — `null` fails the first test and fails the second one too
if (user.isVerified == true) {
    grantAccess(user)
}
if (feature.enabled == false) {
    skip(feature)
}
```

## 6.14 Distinguish `List<T>?` from `List<T?>` from an empty list, and prefer the empty list to both.

> Why? These are three different contracts and callers cannot guess which
> one you meant. `List<T>?` says "there may be no list at all", which forces
> a null check before every iteration for a distinction that, for a
> collection, is almost never meaningful — an empty list already means
> "nothing here". `List<T?>` says "the list exists and some entries are
> missing", which is a real and occasionally correct shape. `List<T>` says
> "there is a list; it may be empty", which is what you want in the
> overwhelming majority of cases and needs no null handling at all.
> **Suggestion.**

```kotlin
// bad — every caller must handle two flavours of "nothing"
fun tagsFor(post: Post): List<String>? =
    if (post.tags.isEmpty()) null else post.tags

// bad — nullable elements the caller did not ask for
fun tagsFor(post: Post): List<String?> = post.rawTags

// good — one shape; emptiness is expressed by the list itself
fun tagsFor(post: Post): List<String> = post.tags

// good — nullable elements only where "missing entry" is genuinely modelled
fun readingsFor(sensor: Sensor): List<Reading?> = sensor.hourlyReadings
```

## 6.15 Never return `null` from a function whose result is a collection.

> Why? This is §6.14 stated as a hard rule, because it is the case that
> actually shows up. A `null` list forces `?: emptyList()` at every call
> site; forget it once and you have an NPE or, worse, a silently skipped
> loop. Returning `emptyList()`, `emptySet()`, or `emptyMap()` costs nothing
> — the stdlib's empty instances are shared singletons — and makes the
> for-loop, the `map`, and the `isEmpty()` at every call site correct without
> a guard.
> **Suggestion.**

```kotlin
// bad — the caller must remember a fallback at every use site
fun findOverdue(customer: CustomerId): List<Invoice>? {
    val rows = repository.overdue(customer)
    return if (rows.isEmpty()) null else rows
}

for (invoice in findOverdue(id)!!) { /* NPE waiting to happen */ }

// good
fun findOverdue(customer: CustomerId): List<Invoice> =
    repository.overdue(customer)

for (invoice in findOverdue(id)) { /* correct when there are none */ }
```

## 6.16 Strip nulls with `filterNotNull`, `mapNotNull`, and `listOfNotNull` rather than filtering and then asserting.

> Why? `list.filter { it != null }` still has type `List<T?>` — the compiler
> cannot see that the predicate removed the nulls — so the pattern almost
> always ends in a `!!` or an unchecked cast on the next line. The stdlib has
> purpose-built functions whose *return types* encode the narrowing:
> `filterNotNull()` turns `List<Int?>` into `List<Int>`, `mapNotNull { }`
> maps and drops nulls in one pass, and `listOfNotNull(a, b, c)` builds a
> `List<T>` from nullable arguments. The reference shows the first directly:
> "If you have a collection of nullable elements and want to keep only the
> non-null ones, use the `filterNotNull()` function."
> **Suggestion.**

```kotlin
// bad — the filter does not change the type, so the map needs an assertion
val ids: List<String> = rows
    .map { it.externalId }
    .filter { it != null }
    .map { it!! }

// good
val ids: List<String> = rows.mapNotNull { it.externalId }

// good — the same idea for a fixed set of optional values
val headers: List<Header> = listOfNotNull(
    traceHeader,
    tenantHeader,
    idempotencyHeader,
)
```

## 6.17 Use `?.let` to *transform* a nullable into a value, not to run a block of statements or to nest.

> Why? `?.let { }` is an expression: it evaluates to the block's result, or
> to `null`. That makes it the right tool for "if this exists, turn it into
> that" — and the wrong tool for everything else. As a statement it discards
> a `T?` nobody reads (§6.7). Nested, it produces two shadowed `it`s that no
> reader can keep straight, at which point the guard-clause form of §6.5 is
> both shorter and clearer. And a `?.let` wrapping a single call is just a
> safe call with extra syntax.
> **Violation — enforced by `detekt/UnnecessaryLet`** for the single-call and
> non-null-receiver forms; **Suggestion** for the nesting.

```kotlin
// bad — a safe call written the long way
val length = name?.let { it.length }

// bad — two nested `it`s, one shadowing the other
fun route(order: Order?): Route? =
    order?.let { o ->
        o.address?.let { it ->
            router.resolve(it)
        }
    }

// good
val length = name?.length

// good — transformation, one level
fun route(order: Order?): Route? =
    order?.address?.let(router::resolve)

// good — or as guard clauses when there is real work to do
fun route(order: Order?): Route? {
    val address = order?.address ?: return null
    audit.record(address)
    return router.resolve(address)
}
```

## 6.18 Never let a nullable value reach a string template or `toString()` by accident.

> Why? `"$user"` on a nullable `user` compiles happily and prints the literal
> text `null`, which then ends up in a log line, an error message, a
> generated filename, or — worst — a user-facing string. The
> [reference](https://kotlinlang.org/docs/null-safety.html#nullable-receiver)
> notes that `.toString()` can be called on a nullable receiver and that
> "when invoked on a `null` value, it safely returns the string `"null"`
> without throwing an exception" — which is exactly the problem when the
> result is user-visible. Make the choice explicit:
> `?: "unknown"` for a display default, `?.toString()` when a nullable
> `String?` is genuinely what you want downstream.
> **Violation — enforced by `detekt/NullableToStringCall`.**

```kotlin
// bad — logs "rejected order null for customer null"
logger.warn("rejected order $orderId for customer $customerId")

// good — the fallback is chosen, not stumbled into
logger.warn(
    "rejected order ${orderId ?: "<none>"} for customer ${customerId ?: "<none>"}",
)

// good — propagate the nullability instead of flattening it
val label: String? = orderId?.toString()
```

## 6.19 Delete the safe calls, assertions, and null checks the compiler tells you are redundant.

> Why? A `?.` on a value that is already non-null is not harmless: it tells
> every future reader that this value can be `null`, so they will keep
> writing null handling around it, and the real nullability boundary drifts
> further from where it belongs. The same goes for a `!!` on a non-null value
> and a `requireNotNull` on one — each is a small lie about the type. (A bare
> `if (x != null)` on a non-null type is caught by the compiler itself, which
> reports the condition as always true.) These are the easiest findings in the
> whole chapter to fix, and clearing them is what makes the remaining null
> handling meaningful.
> **Violation — enforced by `detekt/UnnecessarySafeCall` (`?.` on a non-null
> receiver), `detekt/UnnecessaryNotNullOperator` (`!!` on a non-null value),
> and `detekt/UnnecessaryNotNullCheck`, which "reports unnecessary not-null
> checks with `requireNotNull` or `checkNotNull` that can be removed by the
> user".**

```kotlin
// bad — `id` and `total` are both non-null, so all three of these are noise
// that implies otherwise
fun describe(id: OrderId, total: Money): String {
    val checked = requireNotNull(id) // UnnecessaryNotNullCheck
    return "${checked.value}: ${total!!}, ${total?.currency}"
}

// good
fun describe(id: OrderId, total: Money): String =
    "${id.value}: $total, ${total.currency}"
```
