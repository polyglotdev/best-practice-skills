<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 11. Data Classes

`data class` is the most over-applied keyword in Kotlin. It is a code
generator with a very specific output — `equals`, `hashCode`, `toString`,
`componentN`, and `copy` — and every one of those five commits you to a
semantic. Applied to a genuine value carrier, it removes forty lines of
boilerplate that nobody would have got right by hand. Applied to a JPA
entity, a service, a mutable cache key, or anything with identity, it
generates exactly the wrong behaviour and generates it silently.

This chapter is about that fit. The generation rules come from the
[language documentation on data classes](https://kotlinlang.org/docs/data-classes.html),
which states the requirements plainly — "the primary constructor must have at
least one parameter", "all primary constructor parameters must be marked as
`val` or `var`", and "data classes can't be abstract, open, sealed, or inner"
— and which is the source for the two behaviours that cause most of the
trouble: that "the compiler only uses the properties defined inside the
primary constructor for the automatically generated functions", and that
"the `copy()` function creates a shallow copy of the instance."

Three neighbouring topics are deferred. **Single-component wrappers** belong
in [Chapter 12](12-value-classes.md), which §11.18 routes to. **Closed
hierarchies with data-class leaves** are
[Chapter 13](13-sealed-types.md). **The `equals`/`hashCode` contract itself**,
including why an `Array` component breaks it, is
[Chapter 23](23-equality-and-ordering.md); §11.6 states only the data-class
consequence. Spring's use of data classes for `@ConfigurationProperties`
binding is [Chapter 43](43-spring-configuration-properties.md), and the
compiler plugins that make them work with JPA and Jackson are
[Chapter 41](41-spring-kotlin-setup.md).

**Tool alignment:** detekt ships four directly relevant rules —
`DataClassShouldBeImmutable`, `DataClassContainsFunctions`, `UseDataClass`,
and `LongParameterList` — but the first three are **not** active in the
default configuration and must be enabled explicitly, and
`LongParameterList` sets `ignoreDataClasses` to `true` by default, so an
eleven-component data class passes a stock detekt run without comment. Assume
none of this is on unless you turned it on (see
[Chapter 47](47-ktlint-and-detekt.md)).

## 11.1 Use `data` only when the type is a transparent value carrier — a type whose identity *is* its contents.

> Why? Every member `data` generates presupposes that two instances with equal
> components are interchangeable: `equals` says so, `hashCode` puts them in
> the same bucket, `copy` mints a replacement, and `toString` prints the
> components on the assumption they are the whole story. If that
> interchangeability is not true of your type, you have not saved boilerplate
> — you have shipped four wrong behaviours. The converse is also worth acting
> on: a class that holds nothing but data and has hand-written `equals` and
> `hashCode` should become a `data class`.
> **Violation — enforced by `detekt/UseDataClass`** for the converse
> direction ("Classes that simply hold data should be refactored into a `data
> class`"), which is *not* active by default.

```kotlin
// bad — a service is not a value; `==` on two clients is meaningless, and
// `copy()` invites callers to mint a client with a swapped-out HTTP stack
data class PaymentClient(
    val httpClient: HttpClient,
    val baseUrl: String,
    val apiKey: String,
)

// good — the service is a plain class; the value it carries is the data class
class PaymentClient(
    private val httpClient: HttpClient,
    private val config: PaymentConfig,
)

data class PaymentConfig(val baseUrl: String, val apiKey: String)
```

## 11.2 Never use `data` for a type with identity semantics.

> Why? An entity is defined by *which one it is*, not by what its fields
> currently say — two `Customer` rows with the same email are still two
> customers, and one `Customer` whose email changed is still the same
> customer. A generated `equals` inverts both of those. The damage is not
> theoretical: put such an object in a `Set`, mutate a field, and it becomes
> unfindable (§11.4); load two snapshots of the same row and they compare
> unequal.

```kotlin
// bad — two loads of row 42 taken a second apart compare unequal
data class Customer(val id: Long, val email: String, val lastSeenAt: Instant)

// good — identity is the id, and only the id
class Customer(val id: Long, val email: String, val lastSeenAt: Instant) {
    override fun equals(other: Any?): Boolean =
        this === other || (other is Customer && id == other.id)

    override fun hashCode(): Int = id.hashCode()

    override fun toString(): String = "Customer(id=$id, email=$email)"
}
```

## 11.3 Keep behaviour out of a data class; if it is growing methods, it is not a data class.

> Why? Methods are how a type acquires invariants and collaborators, and both
> of those contradict "transparent value carrier". Once a data class has a
> `charge()`, a `refund()`, and a `settle()`, its `copy()` is a hole in every
> invariant those methods maintain, and its `equals` is comparing the state of
> a machine rather than the contents of a record. Derived read-only
> properties and conversion functions are the accepted exceptions.
> **Violation — enforced by `detekt/DataClassContainsFunctions`** ("Data
> classes should mainly be used to store data"), which is *not* active by
> default and which exempts functions whose names start with one of the
> prefixes in its `conversionFunctionPrefix` option (default `['to']`).

```kotlin
// bad — a state machine wearing a record's clothes
data class Subscription(
    val id: String,
    var status: String,
    var renewsAt: Instant,
) {
    fun cancel() {
        status = "cancelled"
    }

    fun renew(period: Period) {
        status = "active"
        renewsAt = renewsAt.plus(period)
    }
}

// good — the record is a record; the behaviour lives with the invariants
data class Subscription(
    val id: String,
    val status: SubscriptionStatus,
    val renewsAt: Instant,
) {
    val isActive: Boolean get() = status == SubscriptionStatus.ACTIVE

    fun toSummary(): SubscriptionSummary = SubscriptionSummary(id, status)
}

class SubscriptionService(private val repository: SubscriptionRepository) {
    fun cancel(id: String): Subscription {
        val current = repository.load(id)
        return repository.save(current.copy(status = SubscriptionStatus.CANCELLED))
    }
}
```

## 11.4 Declare every component `val`. A `var` component in a `Set` or as a `Map` key breaks the hash invariant.

> Why? A hash-based collection files an element under the `hashCode` it had at
> insertion time and never re-files it. Mutating a component afterwards changes
> the `hashCode` without moving the entry, so the element is still in the set
> but can no longer be found in it — `contains` returns `false`, `remove` does
> nothing, and iteration still yields it. This is the single most damaging
> consequence of `data class` with `var`, and it fails silently.
> **Violation — enforced by `detekt/DataClassShouldBeImmutable`** ("This rule
> reports mutable properties inside data classes. Data classes should mainly be
> used to store immutable data."), which is *not* active by default.

```kotlin
// bad — the element is in the set and simultaneously not findable in it
data class CacheKey(var tenant: String, var path: String)

val keys = hashSetOf(CacheKey("acme", "/users"))
val key = keys.first()
key.tenant = "globex"
println(key in keys)        // false
println(keys.remove(key))   // false — the entry is now unreachable
println(keys.size)          // 1

// good — every component is a val; a change means a new key
data class CacheKey(val tenant: String, val path: String)

val keys = hashSetOf(CacheKey("acme", "/users"))
val moved = keys.first().copy(tenant = "globex")
```

## 11.5 Put every semantically significant property in the primary constructor.

> Why? "The compiler only uses the properties defined inside the primary
> constructor for the automatically generated functions." A property declared
> in the body is therefore invisible to `equals`, `hashCode`, `toString`,
> `componentN`, and `copy` — so two instances that differ in it compare equal,
> a `copy()` silently drops it, and it never shows up in a log line. If the
> property genuinely is incidental (a lazily computed cache, a derived view),
> that exclusion is correct and worth a comment; if it is part of the value,
> the body is the wrong place for it.

```kotlin
// bad — `discountMinor` is part of the line item's meaning but not of its
// identity, its string form, or its copy
data class LineItem(val sku: String, val quantity: Int) {
    var discountMinor: Long = 0
}

val a = LineItem("SKU-1", 2).apply { discountMinor = 500 }
val b = LineItem("SKU-1", 2)
println(a == b)            // true
println(a)                 // LineItem(sku=SKU-1, quantity=2)
println(a.copy().discountMinor) // 0 — silently dropped

// good — every component of the value is a component of the constructor
data class LineItem(val sku: String, val quantity: Int, val discountMinor: Long = 0)
```

## 11.6 Never give a data class an `Array` component.

> Why? The generated `equals` compares each component with `==`, which for
> `Array` is reference equality — so two data class instances holding
> byte-for-byte identical arrays compare unequal, and `hashCode` disagrees
> with any notion of content the caller had in mind. Arrays are also mutable,
> which reintroduces §11.4's hash problem through the back door. Carry a
> `List` (or a `ByteString`-like wrapper) instead; if the raw array is
> genuinely unavoidable at a serialization boundary, drop `data` and write
> `equals`/`hashCode` with `contentEquals`/`contentHashCode` by hand. The
> underlying contract is [Chapter 23](23-equality-and-ordering.md).

```kotlin
// bad — reference equality on the array component
data class Payload(val id: String, val bytes: ByteArray)

println(Payload("a", byteArrayOf(1, 2)) == Payload("a", byteArrayOf(1, 2))) // false

// good — an immutable component, so the generated members are correct
data class Payload(val id: String, val bytes: List<Byte>)

// good — the array is unavoidable, so `data` goes and the members are explicit
class Payload(val id: String, val bytes: ByteArray) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is Payload) return false
        return id == other.id && bytes.contentEquals(other.bytes)
    }

    override fun hashCode(): Int = 31 * id.hashCode() + bytes.contentHashCode()

    override fun toString(): String = "Payload(id=$id, bytes=${bytes.size} B)"
}
```

## 11.7 Put invariants in an `init` block, because `copy()` runs the primary constructor and nothing else.

> Why? `copy()` calls the primary constructor, so an `init` block runs on
> every copy — which is exactly what you want. Validation placed anywhere
> *other* than the primary constructor path does not: a check inside a
> companion factory guards the first instance and no derivative of it, so
> `Email.of("ada@example.com").copy(value = "nonsense")` produces an invalid
> instance of a type whose whole purpose was to be valid. Put the invariant
> where the constructor runs it. **Suggestion.**

```kotlin
// bad — the factory validates; copy() does not
data class Email(val value: String) {
    companion object {
        fun of(raw: String): Email {
            require("@" in raw) { "not an email address: $raw" }
            return Email(raw.lowercase())
        }
    }
}

val valid = Email.of("Ada@example.com")
val invalid = valid.copy(value = "nonsense") // no check runs

// good — the constructor is the only path, so it is the only place to check
data class Email(val value: String) {
    init {
        require("@" in value) { "not an email address: $value" }
    }

    companion object {
        fun of(raw: String): Email = Email(raw.lowercase())
    }
}
```

## 11.8 Remember that `copy()` is shallow; it does not isolate a mutable component.

> Why? The docs say it directly: "The `copy()` function creates a shallow
> copy of the instance. In other words, it doesn't copy components recursively.
> As a result, references to other objects are shared." Code that calls
> `copy()` to get a safe snapshot before handing an object to another thread,
> another module, or a caller gets no such thing if any component is mutable
> — both objects point at the same `MutableList`. The fix is to make the
> component immutable in the first place ([Chapter 25](25-immutability.md)),
> not to deep-copy at each call site.

```kotlin
// bad — `snapshot` and `order` share one list; mutating either is visible in both
data class Order(val id: String, val lines: MutableList<Line>)

val snapshot = order.copy()
order.lines.add(Line("SKU-9", 1))
println(snapshot.lines.size) // includes the new line

// good — an immutable component makes the shallow copy a real snapshot
data class Order(val id: String, val lines: List<Line>)

val snapshot = order
val updated = order.copy(lines = order.lines + Line("SKU-9", 1))
```

## 11.9 A `private` primary constructor does not close a data class, because the generated `copy()` is public.

> Why? This is the best-known hole in `data class`, tracked as
> [KT-11914, "Confusing data class copy with private constructor"](https://youtrack.jetbrains.com/issue/KT-11914).
> The generated
> `copy()` has historically been public regardless of the primary
> constructor's visibility, so a private constructor plus a validating or
> interning factory is not a gate — any caller holding one instance can mint
> arbitrary others. Kotlin has been migrating this since 2.0.20, and the
> remedy is the
> [`@ConsistentCopyVisibility`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-consistent-copy-visibility/)
> annotation, which makes `copy()` take the constructor's visibility, or the
> module-wide `-Xconsistent-data-class-copy-visibility` compiler flag.
> `@ExposedCopyVisibility` is the opposite escape hatch — it keeps the old
> public `copy()` for binary compatibility and is explicitly discouraged for
> new code. Verify the exact diagnostic your compiler version emits rather
> than assuming; the migration runs across several releases. **Suggestion.**

```kotlin
// bad — `of` interns instances, and `copy()` walks straight past it
data class Currency private constructor(val code: String) {
    companion object {
        private val cache = mutableMapOf<String, Currency>()

        fun of(code: String): Currency = cache.getOrPut(code) { Currency(code) }
    }
}

val usd = Currency.of("USD")
val bogus = usd.copy(code = "XXXX") // never validated, never interned

// good — the generated copy() now matches the constructor's visibility
@ConsistentCopyVisibility
data class Currency private constructor(val code: String) {
    companion object {
        private val cache = mutableMapOf<String, Currency>()

        fun of(code: String): Currency = cache.getOrPut(code) { Currency(code) }
    }
}

// good — interning implies identity semantics anyway, so drop `data` (see 11.2)
class Currency private constructor(val code: String) {
    override fun toString(): String = "Currency($code)"

    companion object {
        private val cache = mutableMapOf<String, Currency>()

        fun of(code: String): Currency = cache.getOrPut(code) { Currency(code) }
    }
}
```

## 11.10 Do not destructure positionally beyond two or three components, and never across a module boundary.

> Why? `componentN` is generated "corresponding to properties in their order
> of declaration", so destructuring binds by position and nothing else.
> Reorder two same-typed components in the declaration — a refactor nobody
> would flag in review — and every destructuring site still compiles, now with
> the values swapped. The larger the component list and the further the
> destructuring site is from the declaration, the less likely anyone notices.
> Named property access costs one extra token and cannot silently rebind. The
> conventions' own
> [destructuring declarations](https://kotlinlang.org/docs/coding-conventions.html#destructuring-declarations)
> section is purely about formatting and takes no position on this; the risk
> argument is the one that matters. **Suggestion.**

```kotlin
// bad — swapping `city` and `postcode` in the declaration silently rebinds this
data class Address(val street: String, val city: String, val postcode: String)

val (street, city, postcode) = address

// good — binding by name cannot be broken by a reordering
val street = address.street
val city = address.city
val postcode = address.postcode

// good — positional destructuring is fine where the shape is obviously fixed
for ((code, count) in countsByCode) { /* ... */ }
```

## 11.11 Keep the component list short; nest a data class rather than growing a flat one.

> Why? A data class with fourteen components has fourteen positional
> `componentN` functions, a `copy()` with fourteen parameters, a `toString`
> nobody reads, and a constructor call that only survives review because it
> uses named arguments. It is also the shape that most often signals a missing
> intermediate concept — an address, a money amount, a date range — that other
> parts of the system also want. Note that stock detekt will not tell you:
> `LongParameterList` defaults `ignoreDataClasses` to `true`.
> **Violation — enforced by `detekt/LongParameterList`** only once you set
> `ignoreDataClasses: false`; `allowedConstructorParameters` defaults to 6.

```kotlin
// bad — flat, and the address concept is duplicated inline
data class ShippingRequest(
    val orderId: String,
    val recipientName: String,
    val line1: String,
    val line2: String?,
    val city: String,
    val postcode: String,
    val countryCode: String,
    val weightGrams: Int,
    val insuredValueMinor: Long,
    val currencyCode: String,
)

// good — the concepts are named and reusable
data class Address(
    val line1: String,
    val line2: String?,
    val city: String,
    val postcode: String,
    val countryCode: String,
)

data class Money(val amountMinor: Long, val currencyCode: String)

data class ShippingRequest(
    val orderId: String,
    val recipientName: String,
    val address: Address,
    val weightGrams: Int,
    val insuredValue: Money,
)
```

## 11.12 Use default parameter values for optional components; do not hand-write a builder.

> Why? A builder exists in Java because the language has no named or default
> arguments. Kotlin has both, so a data class with defaults gives you the
> builder's whole value proposition — set the three fields you care about out
> of eleven, in any order, readably — with none of its cost: no mutable
> intermediate object, no `build()` that can be forgotten, no second place for
> the field list to drift out of sync. Validation still has one home, the
> `init` block (§11.7). **Suggestion.**

```kotlin
// bad — a Java builder transliterated into Kotlin
data class HttpConfig(val baseUrl: String, val connectTimeout: Duration, val retries: Int) {
    class Builder(private val baseUrl: String) {
        private var connectTimeout: Duration = Duration.ofSeconds(10)
        private var retries: Int = 3

        fun connectTimeout(value: Duration) = apply { connectTimeout = value }

        fun retries(value: Int) = apply { retries = value }

        fun build() = HttpConfig(baseUrl, connectTimeout, retries)
    }
}

// good
data class HttpConfig(
    val baseUrl: String,
    val connectTimeout: Duration = Duration.ofSeconds(10),
    val retries: Int = 3,
) {
    init {
        require(retries >= 0) { "retries must be >= 0, was $retries" }
    }
}

val config = HttpConfig(baseUrl = "https://api.example.com", retries = 5)
```

## 11.13 When you want a subtype, model the hierarchy as a sealed interface with data class leaves.

> Why? "Data classes can't be abstract, open, sealed, or inner", so the
> instinct to add a subtype has nowhere to go inside the data class itself.
> The right shape is a `sealed interface` whose implementations are data
> classes: each leaf keeps its generated members, the hierarchy stays closed,
> and a `when` over it is exhaustive without an `else`, so adding a case
> becomes a compile error rather than a runtime surprise. Full treatment in
> [Chapter 13](13-sealed-types.md); the exhaustiveness half is
> [Chapter 22](22-control-flow-and-when.md).

```kotlin
// bad — `open data class` does not compile, and the workaround is worse:
// one flat class with a discriminator and a pile of nullable fields
data class PaymentEvent(
    val type: String,
    val authorizationCode: String? = null,
    val refundReason: String? = null,
    val declineCode: String? = null,
)

// good
sealed interface PaymentEvent {
    val paymentId: String

    data class Authorized(override val paymentId: String, val code: String) : PaymentEvent

    data class Refunded(override val paymentId: String, val reason: String) : PaymentEvent

    data class Declined(override val paymentId: String, val declineCode: String) : PaymentEvent
}
```

## 11.14 Override `toString()` on any data class that carries a secret.

> Why? The generated `toString` prints every primary-constructor component,
> and it is invoked implicitly by string templates, by SLF4J's `{}`
> placeholder, and by most exception and assertion messages. A
> `clientSecret`, a bearer token, or a card PAN therefore reaches your log
> aggregator the first time anyone logs the enclosing object — a leak that no
> code review catches, because the offending line contains no secret. Overriding
> `toString` is permitted on a data class and suppresses the generated one.
> Logging discipline generally is [Chapter 31](31-logging.md). **Suggestion.**

```kotlin
// bad — the secret is in every log line that mentions the request
data class TokenRequest(val clientId: String, val clientSecret: String)

logger.debug("exchanging {}", request)
// TokenRequest(clientId=svc-billing, clientSecret=sk_live_9f3c...)

// good
data class TokenRequest(val clientId: String, val clientSecret: String) {
    override fun toString(): String = "TokenRequest(clientId=$clientId, clientSecret=***)"
}
```

## 11.15 A JPA entity is not a data class.

> Why? Three of the five generated members are wrong for an entity at once.
> `equals`/`hashCode` cover a generated `@Id` that is `null` until the first
> flush, so an entity's hash changes after persistence and any `Set` it was
> added to beforehand loses it. `toString` touches every field, which forces
> every lazy association to load — usually outside the session, producing
> `LazyInitializationException` from inside a log statement. And `copy()`
> hands callers a detached twin sharing the same identifier. Entities also
> need `open` classes and a no-arg constructor, which come from the
> `kotlin-jpa` and `no-arg` compiler plugins, never from a hand-written
> secondary constructor — see
> [Chapter 41](41-spring-kotlin-setup.md) and
> [Chapter 45](45-spring-data-and-transactions.md). **Suggestion.**

```kotlin
// bad — hashCode changes on flush; toString drags in every lazy association
@Entity
data class Customer(
    @Id @GeneratedValue val id: Long? = null,
    var email: String,
    @OneToMany(mappedBy = "customer") val orders: List<Order> = emptyList(),
)

// good — identity-based equality, a toString that touches no association
@Entity
class Customer(
    @Id @GeneratedValue var id: Long? = null,
    var email: String,
) {
    @OneToMany(mappedBy = "customer")
    var orders: MutableList<Order> = mutableListOf()

    override fun equals(other: Any?): Boolean =
        this === other || (other is Customer && id != null && id == other.id)

    override fun hashCode(): Int = javaClass.hashCode()

    override fun toString(): String = "Customer(id=$id, email=$email)"
}
```

## 11.16 Never add a hand-written no-arg secondary constructor to satisfy a framework.

> Why? Jackson, JPA, and Spring's constructor binding all need something a
> Kotlin data class does not have by default, and every one of them has a
> supported answer: `jackson-module-kotlin` for Jackson, the `no-arg` /
> `kotlin-jpa` compiler plugins for JPA, and Spring Boot's own constructor
> binding for `@ConfigurationProperties`
> ([Chapter 43](43-spring-configuration-properties.md)). A hand-written
> `constructor() : this("", 0)` "fixes" the reflection failure by making every
> invariant optional — the empty string and the zero are now legal values of
> your type, reachable from any caller, and `init` validation either rejects
> them (breaking the framework you were appeasing) or is absent (leaving the
> junk values live). **Suggestion.**

```kotlin
// bad — junk defaults become legal domain values, reachable by anyone
data class ShipmentRequest(val orderId: String, val weightGrams: Int) {
    constructor() : this("", 0)
}

// good — the type keeps its invariants; the plugin supplies what the framework
// needs (see Chapter 41 for the Gradle configuration)
data class ShipmentRequest(val orderId: String, val weightGrams: Int) {
    init {
        require(orderId.isNotBlank()) { "orderId must not be blank" }
        require(weightGrams > 0) { "weightGrams must be positive, was $weightGrams" }
    }
}
```

## 11.17 Nest request and response data classes inside the type that owns the endpoint.

> Why? Wire shapes proliferate — `CreateOrderRequest`, `CreateOrderResponse`,
> `UpdateOrderRequest` — and as top-level declarations they fill the package's
> namespace with types that have exactly one caller each. Nesting them under
> the controller or client that owns them makes the ownership visible in the
> qualified name (`OrderApi.CreateRequest`), keeps the diff for an endpoint
> change in one file, and matches the conventions' guidance to "put nested
> classes next to the code that uses those classes". Nest them plainly, never
> as `inner` — see [§10.13](10-classes-and-interfaces.md). **Suggestion.**

```kotlin
// bad — four top-level types with one caller each, names disambiguated by prefix
data class CreateOrderRequest(val sku: String, val quantity: Int)
data class CreateOrderResponse(val orderId: String)
data class CancelOrderRequest(val orderId: String, val reason: String)
data class CancelOrderResponse(val cancelled: Boolean)

// good — ownership is visible at the use site
interface OrderApi {
    fun create(request: CreateRequest): CreateResponse

    fun cancel(request: CancelRequest): CancelResponse

    data class CreateRequest(val sku: String, val quantity: Int)

    data class CreateResponse(val orderId: String)

    data class CancelRequest(val orderId: String, val reason: String)

    data class CancelResponse(val cancelled: Boolean)
}
```

## 11.18 With exactly one component, prefer a value class; with behaviour and identity, prefer a plain class.

> Why? A `data class` with one component pays for four generated members you
> did not need and allocates a wrapper object on every construction. A
> `@JvmInline value class` gives you the same distinct type, the same
> structural equality, an `init` block for validation, and — in the common
> cases — no allocation at all, because the compiler represents it as the
> underlying value. Going the other way: if the type has invariants that
> methods maintain, `copy()` is a hole in them and identity matters more than
> contents, so a plain class with hand-written members is correct. The full
> value-class rules, including where boxing reappears, are
> [Chapter 12](12-value-classes.md). **Suggestion.**

```kotlin
// bad — a one-component data class; allocates, and copy() is meaningless
data class UserId(val value: String)

// good — a distinct type with no wrapper allocation in the common case
@JvmInline
value class UserId(val value: String) {
    init {
        require(value.isNotBlank()) { "userId must not be blank" }
    }
}
```
