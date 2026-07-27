<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 3. Naming

A name is the only part of a declaration every reader sees. This chapter covers
what to call packages, types, functions, properties, constants, type parameters,
and test members, and the small set of places where Kotlin deliberately breaks
its own camelCase rule.

The normative sources are the
[Android Kotlin style guide, Naming](https://developer.android.com/kotlin/style-guide#naming_2)
and the
[Kotlin coding conventions, Naming rules](https://kotlinlang.org/docs/coding-conventions.html#naming-rules).
They agree on nearly everything. Where they disagree — two-letter acronyms
(§3.6) and backticked test names (§3.8) — this chapter says so explicitly and
tells you how to pick, rather than quietly siding with one.

Three neighbouring topics are deferred. **What to call a `.kt` file**, and how a
file's name relates to the declarations inside it, is
[Chapter 2, Source Files & Structure](02-source-files-and-structure.md).
**The explicit backing field syntax** — as opposed to the underscore *name*
convention in §3.13 — is
[Chapter 17, Properties & Backing Fields](17-properties-and-backing-fields.md).
**How a Kotlin name is projected into Java**, including `@JvmName` and the
getter-naming rule that makes §3.15 matter, is
[Chapter 28, Java Interop](28-java-interop.md).

**Tool alignment:** most of this chapter is mechanically enforced. ktlint's
`standard:package-name`, `standard:class-naming`, `standard:function-naming`,
`standard:property-naming`, and `standard:backing-property-naming` cover the
shapes; detekt's `naming` ruleset adds `PackageNaming`, `ClassNaming`,
`FunctionNaming`, `VariableNaming`, `TopLevelPropertyNaming`,
`ObjectPropertyNaming`, `ConstructorParameterNaming`, `FunctionParameterNaming`,
`LambdaParameterNaming`, `EnumNaming`, `BooleanPropertyNaming`,
`NonBooleanPropertyPrefixedWithIs`, `NoNameShadowing`,
`MemberNameEqualsClassName`, and `ForbiddenClassName`. Rules a named check
actually catches are marked **Violation**; the judgement calls — is this noun
the *right* noun, is `Manager` meaningless here — are **Suggestion**, because no
regex can answer them. Configuration for both tools is
[Chapter 47](47-ktlint-and-detekt.md).

## 3.1 Build identifiers from ASCII letters and digits only, and use the underscore only where the guide explicitly permits it.

> Why? The
> [Android Kotlin style guide, Naming](https://developer.android.com/kotlin/style-guide#naming_2)
> opens with exactly this constraint: "Identifiers use only ASCII letters and
> digits, and, in a small number of cases noted below, underscores." The
> permitted underscore sites are a closed list — separating words in a constant
> name (§3.10), prefixing a backing property (§3.13), and separating logical
> components of a test function name (§3.8). Everywhere else an underscore is a
> smell, and a non-ASCII identifier is a portability hazard: it survives the
> Kotlin compiler but breaks grep, breaks some CI log encodings, and produces
> JVM member names that are painful to reference from Java.

```kotlin
// bad — non-ASCII identifiers, and underscores outside the permitted sites
val précision = 0.001
class Résumé(val naïveScore: Int)

fun send_order(order_id: String) { /* ... */ }

// good
val precision = 0.001
class Resume(val naiveScore: Int)

fun sendOrder(orderId: String) { /* ... */ }
```

## 3.2 Write package names in all lowercase, with consecutive words concatenated and no underscores.

> Why? The
> [Android Kotlin style guide, Package Names](https://developer.android.com/kotlin/style-guide#package_names)
> requires "all lowercase, with consecutive words simply concatenated together
> (no underscores)", and lists `com.example.deepSpace` and
> `com.example.deep_space` as WRONG against `com.example.deepspace`. The
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#naming-rules)
> agree on the underscore — "Names of packages are always lowercase and do not
> use underscores" — but are *looser* on multi-word segments: they say
> multi-word names are "generally discouraged", and that if you need one you may
> "either just concatenate them together or use camel case
> (`org.example.myProject`)." Follow Android here, because the concatenated form
> is also a correctness rule on case-insensitive filesystems: a package that
> differs from another only by case maps to the same directory on macOS and
> Windows, so `com.example.deepSpace` and `com.example.deepspace` collide in a
> way that fails only on someone else's machine. **Violation for the underscore
> only — `ktlint/standard:package-name` rejects any `_` in a package name, and
> `detekt/PackageNaming`'s default `packagePattern` of
> `'[a-z]+(\.[a-z][A-Za-z0-9]*)*'` does too.** Neither flags
> `com.example.deepSpace`: ktlint's regex is
> `[a-z][a-zA-Z\d]*(\.[a-z][a-zA-Z\d]*)*`, which permits an uppercase letter
> after the first character of a segment, and detekt's default permits the same.
> The camelCase half of this rule is a **Suggestion** unless you tighten
> `packagePattern` yourself.

```kotlin
// bad
package com.example.deepSpace

// bad
package com.example.deep_space

// good
package com.example.deepspace
```

## 3.3 Name types in PascalCase, with a class named as a noun or noun phrase.

> Why? The
> [Android Kotlin style guide, Type names](https://developer.android.com/kotlin/style-guide#type_names)
> states that "class names are written in PascalCase and are typically nouns or
> noun phrases", and the
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#choose-good-names)
> put it as "the name of a class is usually a noun or a noun phrase explaining
> what the class is: `List`, `PersonReader`." An interface names a thing too,
> but may instead be an adjective when it describes a capability rather than an
> entity — `Readable`, `Comparable`, `AutoCloseable`. A type named with a verb
> (`ProcessOrder`) is nearly always a function wearing a class costume.
> **Violation — enforced by `ktlint/standard:class-naming` and
> `detekt/ClassNaming`** for the casing; the noun-versus-verb judgement is a
> **Suggestion**.

```kotlin
// bad — a verb phrase as a type, and lower camel case on a class
class calculateShipping(val order: Order) {
    fun run(): Money = TODO()
}

// good — the class is the thing, the function is the action
class ShippingCalculator(private val rates: RateTable) {
    fun quote(order: Order): Money = TODO()
}

// good — an interface may be an adjective when it names a capability
interface Retryable {
    val maxAttempts: Int
}
```

## 3.4 Name a test class after the class under test, suffixed with `Test`.

> Why? The
> [Android Kotlin style guide, Type names](https://developer.android.com/kotlin/style-guide#type_names)
> is specific: "Test classes are named starting with the name of the class they
> are testing, and ending with `Test`. For example, `HashTest` or
> `HashIntegrationTest`." The suffix is not decoration on Maven: Surefire's
> default includes are name patterns (`**/Test*`, `**/*Test`, `**/*Tests`,
> `**/*TestCase`), so a class named `OrderServiceSpec` compiles, reports no
> error, and silently never runs. Gradle's `Test` task does not have that
> failure mode by default — it detects test classes from bytecode — but any
> build that narrows it with an explicit `include("**/*Test.class")` reintroduces
> exactly the Surefire behaviour. Naming to the pattern costs nothing and
> survives a move between build tools. The full testing chapter is
> [Chapter 32](32-testing.md). **Suggestion.**

```kotlin
// bad — will not match the default `*Test` include pattern
class TestShippingCalculator { /* ... */ }
class ShippingCalculatorSpec { /* ... */ }

// good
class ShippingCalculatorTest { /* ... */ }
class ShippingCalculatorIntegrationTest { /* ... */ }
```

## 3.5 Name functions in camelCase, as verbs or verb phrases.

> Why? The
> [Android Kotlin style guide, Function names](https://developer.android.com/kotlin/style-guide#function_names)
> requires camelCase and notes functions "are typically verbs or verb phrases.
> For example, `sendMessage` or `stop`." The
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#choose-good-names)
> add the reason: the name "should also suggest if the method is mutating the
> object or returning a new one" — see §3.20. A function named as a bare noun
> (`orderTotal()`) reads as a property and invites a reader to assume it is
> cheap and idempotent, which a function is under no obligation to be.
> **Violation — enforced by `ktlint/standard:function-naming` and
> `detekt/FunctionNaming`** for the casing (detekt's default `functionPattern`
> is `'[a-z][a-zA-Z0-9]*'`); the verb-phrase choice is a **Suggestion**.

```kotlin
// bad — PascalCase on an ordinary function, and a noun that hides a network call
fun SendMessage(text: String) { /* ... */ }

fun exchangeRates(): Map<Currency, BigDecimal> = httpClient.get("/rates")

// good
fun sendMessage(text: String) { /* ... */ }

fun fetchExchangeRates(): Map<Currency, BigDecimal> = httpClient.get("/rates")
```

## 3.6 Lowercase an acronym before applying camel or Pascal case, so only its first letter is capitalized.

> Why? The
> [Android Kotlin style guide, Camel case](https://developer.android.com/kotlin/style-guide#camel_case)
> gives a four-step algorithm whose third step is "now lowercase everything
> (including acronyms)", producing `XmlHttpRequest`, `newCustomerId`, and
> `supportsIpv6OnIos`. The point is that a shouted acronym destroys word
> boundaries: in `XMLHTTPRequest` there is no way to see where one word ends and
> the next begins, and the ambiguity compounds with every acronym you add.
>
> **The two guides conflict on two-letter acronyms.** The
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#choose-good-names)
> carve out an exception — "for two-letter acronyms, use uppercase for both
> letters. For example, `IOStream`" — while Android's algorithm has no such
> case and yields `IoStream`. Pick one per codebase and apply it everywhere;
> mixing them is worse than either choice. **Suggestion** in both directions:
> no linter arbitrates this.

```kotlin
// bad — acronyms shouted, so the word boundaries vanish
class HTTPURLConnectionFactory { /* ... */ }

fun parseJSONResponse(body: String): Response = TODO()

fun supportsIPv6OnIOS(): Boolean = TODO()

// good — lowercase the acronym first, then apply camel or Pascal case
class HttpUrlConnectionFactory { /* ... */ }

fun parseJsonResponse(body: String): Response = TODO()

fun supportsIpv6OnIos(): Boolean = TODO()
```

## 3.7 Reserve PascalCase function names for the two class-like exceptions: a factory function named for its abstract return type, and a `@Composable` returning `Unit`.

> Why? The
> [Kotlin coding conventions, Names for class-like functions](https://kotlinlang.org/docs/coding-conventions.html#names-for-class-like-functions)
> name exactly two exceptions. Factory functions "that create class instances
> can have the same name as the abstract return type", which lets a library
> swap a constructor for a factory without breaking a single call site. And
> "`@Composable` functions that return `Unit`" are PascalCased — the
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#function_names)
> explains why: they are "named as nouns, as if they were types." Anything
> outside these two cases that is PascalCased will read as a constructor call
> and mislead. **Violation — enforced by `ktlint/standard:function-naming` and
> `detekt/FunctionNaming`**, which flag both exceptions too. Configure the
> escape hatch rather than suppressing per call site: ktlint reads
> `ktlint_function_naming_ignore_when_annotated_with=Composable` from
> `.editorconfig`.

```kotlin
// bad — PascalCase on a function that is neither a factory nor a Composable
fun ValidateOrder(order: Order): Boolean = TODO()

// good — factory function named for the abstract type it returns
interface Clock {
    fun now(): Instant
}

private class SystemClock : Clock {
    override fun now(): Instant = Instant.now()
}

fun Clock(): Clock = SystemClock()

// good — @Composable returning Unit is named as a noun
@Composable
fun NameTag(name: String) { /* ... */ }
```

## 3.8 Separate the logical components of a test function name with underscores; use backticked names with spaces only where every target runtime supports them.

> Why? The
> [Android Kotlin style guide, Function names](https://developer.android.com/kotlin/style-guide#function_names)
> permits underscores "to appear in test function names to separate logical
> components of the name", giving `pop_emptyStack()`. It then forbids spaces
> outright: "Function names should not contain spaces because this is not
> supported on every platform (notably, this is not fully supported in
> Android)." The
> [Kotlin coding conventions, Names for test methods](https://kotlinlang.org/docs/coding-conventions.html#names-for-test-methods)
> permit backticked names "in tests (and only in tests)", with the caveat that
> "such method names are only supported by Android runtime from API level 30."
>
> So this is a platform question, not a taste question. On a server-side JVM
> target, backticked names are legal and read far better in a failure report.
> On Android below API 30 they crash at runtime. Decide once, per module, from
> the target — not from preference. **Suggestion.** Note that
> `ktlint/standard:function-naming` already treats a file importing anything
> under `io.kotest`, `junit.framework`, `kotlin.test`, `org.junit`, or
> `org.testng` as a test file and allows backticked names there, so the linter
> will not stop you from shipping a name that an old Android runtime rejects.

```kotlin
// bad — spaces in a production function name, on any platform
fun `charge the card`(token: PaymentToken) { /* ... */ }

// good — underscores separate logical components, portable everywhere
class StackTest {
    @Test
    fun pop_emptyStack_throws() { /* ... */ }
}

// good — backticks, but only on a JVM-only or API 30+ target
class StackTest {
    @Test
    fun `pop on an empty stack throws NoSuchElementException`() { /* ... */ }
}
```

## 3.9 Name every non-constant in camelCase: instance properties, local properties, and parameters.

> Why? The
> [Android Kotlin style guide, Non-constant names](https://developer.android.com/kotlin/style-guide#non-constant_names)
> makes camelCase the default for everything that is not a constant under the
> strict test in §3.10, and "these names are typically nouns or noun phrases."
> The default matters more than it looks: because SCREAMING_SNAKE_CASE carries a
> real guarantee (§3.10), using it loosely destroys the signal for the names
> that have earned it. **Violation — enforced by
> `ktlint/standard:property-naming`, `detekt/VariableNaming`,
> `detekt/ConstructorParameterNaming`, `detekt/FunctionParameterNaming`, and
> `detekt/LambdaParameterNaming`.**

```kotlin
// bad
class OrderService(
    private val Repository: OrderRepository,
    private val TENANT_ID: String,
) {
    fun place(Order_Request: OrderRequest) {
        val Result = Repository.save(Order_Request)
    }
}

// good
class OrderService(
    private val repository: OrderRepository,
    private val tenantId: String,
) {
    fun place(orderRequest: OrderRequest) {
        val result = repository.save(orderRequest)
    }
}
```

## 3.10 Use SCREAMING_SNAKE_CASE only for a genuine constant: a `val` with no custom getter, holding a deeply immutable value.

> Why? The
> [Android Kotlin style guide, Constant names](https://developer.android.com/kotlin/style-guide#constant_names)
> defines a constant by four conditions at once — it is a `val`, it has no
> custom `get` function, its contents are deeply immutable, and its functions
> have no detectable side effects. The `val` keyword alone proves none of that:
> `val` freezes the *reference*, not the object behind it. The guide also
> requires the `const` modifier on scalars, which is what promotes the value to
> a compile-time constant that can be inlined and used in an annotation
> argument. **Violation at top level — enforced by
> `detekt/TopLevelPropertyNaming`**, whose default `constantPattern` is
> `'[A-Z][_A-Z0-9]*'`, and by `ktlint/standard:property-naming` for a `const val`
> anywhere (its `ktlint_property_naming_constant_naming` defaults to
> `screaming_snake_case`). Inside an `object`, `detekt/ObjectPropertyNaming`
> owns the check but its default `constantPattern` of `'[A-Za-z][_A-Za-z0-9]*'`
> accepts `maxRetryCount` just as readily as `MAX_RETRY_COUNT`, so tighten it if
> you want the rule enforced there.

```kotlin
// bad — camelCase on a genuine constant, and no `const` on scalars
val maxRetryCount = 3
val defaultCharsetName = "UTF-8"

// good — scalars and strings take `const`
const val MAX_RETRY_COUNT = 3
const val DEFAULT_CHARSET_NAME = "UTF-8"

// good — `const` is not legal here, but these are still deeply immutable,
// so they are still constants and still take a constant name
val SUPPORTED_LOCALES: List<String> = listOf("en", "fr", "de")
val RETRY_DELAYS_MILLIS: Map<Int, Long> = mapOf(1 to 100L, 2 to 400L, 3 to 1_600L)
```

## 3.11 Do not give a constant name to anything whose contents can change — a mutable collection, a non-empty array, or an immutable collection of mutable elements.

> Why? This is the trap in §3.10 and it catches almost everyone. The
> [Android Kotlin style guide, Non-constant names](https://developer.android.com/kotlin/style-guide#non-constant_names)
> lists the failures explicitly: `val mutableCollection: MutableSet<String>`,
> `val mutableElements = listOf(mutableInstance)`, `val nonEmptyArray =
> arrayOf("these", "can", "change")`, and `val logger = Logger.getLogger(...)`
> are all **non**-constants, and all take camelCase. Arrays are the sharpest
> edge: `arrayOf("a", "b")` is a `val`, looks frozen, and lets any caller
> reassign `[0]`. A SCREAMING_SNAKE_CASE name on it tells every future reader
> the value is safe to share, which is exactly wrong. The immutability rules
> themselves are [Chapter 25](25-immutability.md). **Suggestion** — detekt's
> patterns check the *shape* of the name, and cannot tell whether the value
> behind it is deeply immutable.

```kotlin
// bad — every one of these can change, but the name promises otherwise
val MUTABLE_CACHE: MutableSet<String> = HashSet()
val DEFAULT_HEADERS = arrayOf("Accept", "Content-Type")
val ACTIVE_SESSIONS = listOf(sessionA, sessionB) // Session has `var` members
val LOGGER = LoggerFactory.getLogger(OrderService::class.java)

// good — camelCase, because none of these is deeply immutable
val mutableCache: MutableSet<String> = HashSet()
val defaultHeaders = arrayOf("Accept", "Content-Type")
val activeSessions = listOf(sessionA, sessionB)
val logger = LoggerFactory.getLogger(OrderService::class.java)

// good — an empty array has nothing to mutate, so it *is* a constant
val EMPTY_HEADERS = emptyArray<String>()
```

## 3.12 Define constants at top level or inside an `object`; a value inside a `class` takes a non-constant name even when it is otherwise constant.

> Why? The
> [Android Kotlin style guide, Constant names](https://developer.android.com/kotlin/style-guide#constant_names)
> states this as a hard placement rule: "Constant values can only be defined
> inside of an `object` or as a top-level declaration. Values otherwise meeting
> the requirement of a constant but defined inside of a `class` must use a
> non-constant name." The rationale is per-instance allocation — a `val` in a
> class body is initialized once *per object*, so it is not a constant in any
> useful sense however immutable its value is. A `companion object` counts as an
> object, which is where the value usually belongs. See
> [Chapter 14](14-objects-and-companions.md) for whether a companion is the
> right home at all. **Violation — enforced by `detekt/VariableNaming`**, whose
> default `variablePattern` of `'[a-z][A-Za-z0-9]*'` rejects a
> SCREAMING_SNAKE_CASE property inside a class body.

```kotlin
// bad — constant name on a per-instance property
class RetryPolicy(private val clock: Clock) {
    val MAX_ATTEMPTS = 5
}

// good — camelCase, because it is allocated per instance
class RetryPolicy(private val clock: Clock) {
    val maxAttempts = 5
}

// good — hoisted into the companion, where a constant name is correct
class RetryPolicy(private val clock: Clock) {
    companion object {
        const val MAX_ATTEMPTS = 5
    }
}
```

## 3.13 Name a backing property exactly like its public counterpart, prefixed with a single underscore, and use that prefix nowhere else.

> Why? The
> [Android Kotlin style guide, Backing properties](https://developer.android.com/kotlin/style-guide#backing_properties)
> and the
> [Kotlin coding conventions, Names for backing properties](https://kotlinlang.org/docs/coding-conventions.html#names-for-backing-properties)
> agree on the shape. Kotlin's wording is "use an underscore as the prefix for
> the name of the private property"; Android's is that the backing property's
> "name should exactly match that of the real property except prefixed with an
> underscore." The value of the convention is that it is *exclusive* — an
> underscore in a name means "this is the private half of a public property
> pair", and nothing else. The moment you use `_` for an unrelated private
> field, a reader has to go looking for a public `lock` that does not exist.
> The syntax and lifecycle of backing fields, including the explicit backing
> field form — which is Stable as of Kotlin 2.4 and needs no compiler flag — are
> [Chapter 17](17-properties-and-backing-fields.md); this rule is only about
> the name. **Violation — enforced by
> `ktlint/standard:backing-property-naming`.**

```kotlin
// bad — the underscore borrowed for a private field that backs nothing,
// while the actual backing property is named something else entirely
class OrderBook {
    private val _lock = Any()
    private val entries = mutableListOf<Order>()

    val allOrders: List<Order> get() = entries
}

// good — the underscore marks one property pair, and only that
class OrderBook {
    private val lock = Any()
    private val _orders = mutableListOf<Order>()

    val orders: List<Order> get() = _orders
}
```

## 3.14 Name type parameters with a single capital letter, optionally followed by a numeral, or with a class-style name suffixed by a capital `T`.

> Why? The
> [Android Kotlin style guide, Type variable names](https://developer.android.com/kotlin/style-guide#type_variable_names)
> permits exactly two styles: "a single capital letter, optionally followed by a
> single numeral (such as `E`, `T`, `X`, `T2`)" or "a name in the form used for
> classes, followed by the capital letter `T` (such as `RequestT`, `FooBarT`)."
> The single-letter form is universally understood in an obvious position — `T`
> in a one-parameter function, `K`/`V` on a map. Reach for the `...T` form the
> moment a signature carries three or more parameters and the letters stop
> being self-explanatory. What you must not do is name a type parameter like an
> ordinary class, because `fun <Request> handle(r: Request)` is indistinguishable
> at a glance from a real `Request` type and will silently shadow one if it
> exists. Variance and bounds are [Chapter 18](18-generics-and-variance.md).
> **Suggestion.**

```kotlin
// bad — reads as a concrete type, and shadows the real `Request` class if
// one is in scope
fun <Request, Response> dispatch(request: Request): Response = TODO()

// good — single letters where the role is obvious
fun <T> firstOrNull(items: List<T>): T? = items.firstOrNull()

class Cache<K, V>(private val entries: MutableMap<K, V>)

// good — the `...T` form when there are several and letters stop helping
interface Handler<RequestT, ResponseT, ErrorT> {
    fun handle(request: RequestT): ResponseT

    fun onFailure(request: RequestT, error: ErrorT)
}
```

## 3.15 Prefix a Boolean with `is`, `has`, `are`, `should`, or `can` — and never prefix a non-Boolean with `is`.

> Why? A bare adjective or noun reads as a value at the call site:
> `if (account.active)` invites the reader to wonder whether `active` is a
> Boolean, a status enum, or a nullable timestamp. The prefix makes the
> predicate reading unambiguous. The `is` prefix specifically has a second,
> load-bearing consequence on the JVM: the
> [Kotlin/Java interop guide](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
> states that "if the name of the property starts with `is`, a different name
> mapping rule is used: the name of the getter is the same as the property name,
> and the name of the setter is obtained by replacing `is` with `set`" — and
> that this "applies to properties of any type, not just `Boolean`." So a
> non-Boolean named `isOwner` silently ships a JavaBeans getter named
> `isOwner()`, which Jackson, Spring, and every reflection-based mapper will
> read as a Boolean property and mis-bind. See
> [Chapter 28](28-java-interop.md). **Violation — enforced by
> `detekt/BooleanPropertyNaming`** (default `allowedPattern` `'^(is|has|are)'`;
> widen it if you want `should`/`can`) **and `detekt/NonBooleanPropertyPrefixedWithIs`.**

```kotlin
// bad — bare adjectives, and an `is` prefix on a non-Boolean that will
// serialize as a JavaBeans boolean property
class Account(
    val active: Boolean,
    val adminRights: Boolean,
    val isOwner: User,
)

// good
class Account(
    val isActive: Boolean,
    val hasAdminRights: Boolean,
    val owner: User,
)
```

## 3.16 Name enum entries in SCREAMING_SNAKE_CASE.

> Why? An enum entry is a singleton constant, so it takes a constant name under
> §3.10. The
> [Kotlin coding conventions, Property names](https://kotlinlang.org/docs/coding-conventions.html#property-names)
> allow either form — "for enum constants, it's OK to use either all uppercase,
> underscore-separated (screaming snake case) names (`enum class Color { RED,
> GREEN }`) or upper camel case names, depending on the usage" — but
> SCREAMING_SNAKE_CASE is what makes an entry
> visually distinct from the enum type itself at a `when` branch, and it is what
> `name` serializes to without a custom converter. Pick it and hold it. Enum
> design generally — when an enum beats a sealed hierarchy, entry bodies,
> exhaustiveness — is [Chapter 15](15-enums.md). **Suggestion in practice:**
> `detekt/EnumNaming`'s default `enumEntryPattern` of `'[A-Z][_a-zA-Z0-9]*'`
> only requires a leading capital, so it accepts `Shipped` as readily as
> `SHIPPED`; tighten the pattern if you want the rule enforced.

```kotlin
// bad — three casings in one declaration
enum class OrderStatus { pending, awaitingPayment, Shipped }

// good
enum class OrderStatus { PENDING, AWAITING_PAYMENT, SHIPPED }
```

## 3.17 Do not encode a variable's type, scope, or mutability in its name.

> Why? Hungarian notation and its Android-era descendants (`mField` for member,
> `sField` for static) exist to compensate for a language that cannot show you a
> declaration's type at the use site. Kotlin can: the IDE shows it, the compiler
> checks it, and `val`/`var` already state mutability in the declaration.
> Encoding it again gives you two sources of truth that drift the first time the
> type changes — `strUserId` that is now a `UserId`, `listOrders` that is now a
> `Set`. The prefix survives the refactor and lies. **Suggestion.**

```kotlin
// bad — prefixes restate what the declaration already says, and go stale
class OrderService(
    private val mRepository: OrderRepository,
    private val strTenantId: String,
    private val listPendingOrders: MutableList<Order>,
) {
    fun place(objRequest: OrderRequest) {
        val boolAccepted = validate(objRequest)
    }
}

// good
class OrderService(
    private val repository: OrderRepository,
    private val tenantId: String,
    private val pendingOrders: MutableList<Order>,
) {
    fun place(request: OrderRequest) {
        val isAccepted = validate(request)
    }
}
```

## 3.18 Do not build a type name out of a meaningless word: `Manager`, `Wrapper`, `Util`, `Helper`, `Data`, `Info`, `Processor`.

> Why? The
> [Kotlin coding conventions, Choose good names](https://kotlinlang.org/docs/coding-conventions.html#choose-good-names)
> put it directly: "the names should make it clear what the purpose of the
> entity is, so it's best to avoid using meaningless words (`Manager`,
> `Wrapper`) in names." These words are load-bearing in exactly one way — they
> let you postpone deciding what the class does, which is why such classes grow
> without limit. `UserDataManager` has no boundary that would tell you a method
> does not belong in it. A `Util` object is usually a set of extension functions
> that never needed a holder at all. **Violation, partly — `detekt/ForbiddenClassName`
> fails the build on any substring you list in its `forbiddenName` config**
> (nothing is forbidden by default, so you must populate it). Whether a
> replacement name is *better* is a **Suggestion**.

```kotlin
// bad — no boundary; every new user-shaped method lands here
class UserDataManager(private val db: Database) {
    fun load(id: UserId): User = TODO()
    fun sendWelcomeEmail(user: User) = TODO()
    fun exportCsv(users: List<User>): String = TODO()
}

object StringUtil {
    fun truncate(value: String, maxLength: Int): String = TODO()
}

// good — each name states a responsibility, so misfits are obvious
class UserRepository(private val db: Database) {
    fun load(id: UserId): User = TODO()
}

class WelcomeMailer(private val mail: MailSender) {
    fun send(user: User) = TODO()
}

// good — an extension function needs no holder at all
fun String.truncate(maxLength: Int): String = TODO()
```

## 3.19 Never prefix an interface with `I`, and reach for the `Impl` suffix only where the implementation genuinely has no distinguishing name.

> Why? The `IFoo` convention is imported from C# and pre-generics Java, where
> the type system could not tell you what kind of thing `Foo` was. In Kotlin the
> declaration says `interface`, so the prefix carries zero information and
> breaks the naming symmetry the rest of the ecosystem uses — nothing in the
> stdlib is `IList` or `ICollection`. `FooImpl` is the mirror failure: it names
> the *category* ("the implementation") rather than the *distinction* (which
> implementation), which stops working the moment there are two.
>
> There is one genuinely defensible use, and the
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#names-for-class-like-functions)
> point at it: their factory-function example pairs `class FooImpl : Foo` with
> `fun Foo(): Foo`. Make that class `private` — the conventions do not, but it
> is the whole point — and `Impl` never appears in the public API, so the bad
> name is invisible to callers and the interface keeps the domain word. When the
> class *is* public, prefer `Default...` — it says "the one you get unless you
> ask otherwise", which is real information. **Suggestion.**

```kotlin
// bad — the `I` carries nothing, and `Impl` names a category, not a difference
interface IPaymentGateway {
    fun charge(amount: Money): Receipt
}

class PaymentGatewayImpl(private val http: HttpClient) : IPaymentGateway {
    override fun charge(amount: Money): Receipt = TODO()
}

// good — the interface owns the domain word; each class says how it works
interface PaymentGateway {
    fun charge(amount: Money): Receipt
}

class StripePaymentGateway(private val http: HttpClient) : PaymentGateway {
    override fun charge(amount: Money): Receipt = TODO()
}

class InMemoryPaymentGateway : PaymentGateway {
    override fun charge(amount: Money): Receipt = TODO()
}

// good — `Impl` is fine when it is private and never reaches a caller
interface Clock {
    fun now(): Instant
}

private class ClockImpl : Clock {
    override fun now(): Instant = Instant.now()
}

fun Clock(): Clock = ClockImpl()
```

## 3.20 Distinguish a mutating operation from a copying one by verb form: `sort` mutates, `sorted` returns a copy.

> Why? The
> [Kotlin coding conventions, Choose good names](https://kotlinlang.org/docs/coding-conventions.html#choose-good-names)
> make this a naming obligation: the name "should also suggest if the method is
> mutating the object or returning a new one. For instance `sort` is sorting a
> collection in place, while `sorted` is returning a sorted copy of the
> collection." The stdlib holds the convention without exception — `reverse` and
> `reversed`, `shuffle` and `shuffled`, `sortBy` and `sortedBy`. Breaking it
> produces the worst class of bug: a caller who assumes the wrong half writes
> code that compiles, runs, and silently discards the result or silently
> mutates a shared list. **Suggestion.**

```kotlin
// bad — the imperative name promises mutation, but the result is a copy that
// the caller here throws away
fun sortOrders(orders: MutableList<Order>): List<Order> =
    orders.sortedBy { it.placedAt }

// good — imperative verb, in-place effect, no return value
fun sortOrders(orders: MutableList<Order>) {
    orders.sortBy { it.placedAt }
}

// good — participle, pure, returns the new collection
fun sortedOrders(orders: List<Order>): List<Order> =
    orders.sortedBy { it.placedAt }
```

## 3.21 Do not shadow an outer name with an inner one.

> Why? A shadowed name makes a reader resolve scope by hand for every use below
> the shadow, and the failure mode is silent: the code compiles, refers to the
> wrong binding, and produces a plausible wrong answer. It is worst in lambdas,
> where an explicit parameter name can quietly displace an enclosing function
> parameter of the same type, so the compiler has no complaint to make.
> **Violation — enforced by `detekt/NoNameShadowing`.**

```kotlin
// bad — the lambda parameter shadows the function parameter, and two lines
// down nobody can tell which `order` is in play
fun reconcile(order: Order, candidates: List<Order>) {
    candidates.forEach { order ->
        report(compare(order, order))
    }
}

// good — distinct names, so every reference resolves on sight
fun reconcile(order: Order, candidates: List<Order>) {
    candidates.forEach { candidate ->
        report(compare(order, candidate))
    }
}
```
