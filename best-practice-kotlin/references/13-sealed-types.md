<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 13. Sealed Types

A sealed type is Kotlin's way of telling the compiler "this is the complete
list of possibilities, and nobody outside this module gets to add to it." That
one guarantee is what turns a `when` from a runtime dispatch into a
compile-time proof: the compiler knows every variant, so it can reject a
`when` that forgets one. Everything else in this chapter — the choice between
`sealed interface` and `sealed class`, the `data object` variants, the
prohibition on `else` — exists to protect that guarantee.

The upstream rules come from the
[Kotlin language documentation on sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html),
specifically
[inheritance](https://kotlinlang.org/docs/sealed-classes.html#inheritance) and
[use sealed classes with when expression](https://kotlinlang.org/docs/sealed-classes.html#use-sealed-classes-with-when-expression),
plus
[data objects in sealed hierarchies](https://kotlinlang.org/docs/object-declarations.html#use-data-objects-with-sealed-hierarchies)
and the
[`when` exhaustiveness rules](https://kotlinlang.org/docs/control-flow.html#when-expressions-and-statements).
Neither the
[Android Kotlin style guide](https://developer.android.com/kotlin/style-guide)
nor the
[Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
legislates sealed hierarchies directly, so where this chapter cites a style
guide it is for an adjacent rule — [class
layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout) or
[immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability) —
and never for a claim the guide does not make.

Three neighbouring topics are deferred. **The formatting and general idiom of
`when`** — subjects, guard conditions, `when` versus `if` — is
[Chapter 22](22-control-flow-and-when.md); this chapter covers only what
sealedness adds to it. **Enums** get their own treatment in
[Chapter 15](15-enums.md); §13.5 and §13.6 state the decision rule and
Chapter 15 fills in the detail. **Error handling strategy** — when to throw,
when to return `Result`, when to model failure as a domain type — is
[Chapter 24](24-exceptions-and-result.md); §13.11 states only the part that
concerns sealed hierarchies. Data class semantics themselves are
[Chapter 11](11-data-classes.md).

**Tool alignment:** one rule below is mechanically enforced. detekt's
`ElseCaseInsteadOfExhaustiveWhen` (`potential-bugs`) reports a `when` that
carries an `else` even though its branches already cover every case, which is
exactly the §13.6 failure — note that it is **off by default** and requires
type resolution, so you must both enable it and run detekt with a classpath.
Everything else here is design judgement no linter can make, and is labeled
**Suggestion**.

## 13.1 Default to `sealed interface`; reach for `sealed class` only when the variants share state or a constructor.

> Why? A `sealed class` is
> [always abstract](https://kotlinlang.org/docs/sealed-classes.html) and
> therefore occupies a variant's single superclass slot, which stops that
> variant from extending any other class — including a second sealed class. A
> `sealed interface` costs nothing: it carries no constructor, no state, and a
> variant may implement several of them. Start with the interface and upgrade
> only when you find a property every single variant genuinely shares.
> **Suggestion.**

```kotlin
// bad — the sealed class contributes nothing but a superclass slot, so no
// variant can ever extend another class, and the variants get identity
// equality instead of structural equality
sealed class ApiFailure

class NotFound(val resource: String) : ApiFailure()
class RateLimited(val retryAfter: Duration) : ApiFailure()

// good
sealed interface ApiFailure

sealed interface Retryable

data class NotFound(val resource: String) : ApiFailure
data class RateLimited(val retryAfter: Duration) : ApiFailure, Retryable
```

## 13.2 Declare every direct subtype in the same package and the same module as the sealed declaration.

> Why? This is not a style preference, it is the language rule that makes
> sealing work.
> [Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html#inheritance):
> "Direct subclasses of sealed classes and interfaces must be declared in the
> same package. They may be top-level or nested inside any number of other
> named classes, named interfaces, or named objects." They must also live in
> the same compilation module. Splitting variants across packages does not
> weaken the guarantee — it fails to compile. **Suggestion** (the compiler
> already rejects it; the rule is here so you place files deliberately rather
> than discovering the constraint by build failure).

```kotlin
// bad — com/example/api/ApiFailure.kt declares the sealed interface,
// com/example/api/errors/NotFound.kt declares a variant in another package;
// this does not compile
package com.example.api

sealed interface ApiFailure

// ---- com/example/api/errors/NotFound.kt ----
package com.example.api.errors

import com.example.api.ApiFailure

data class NotFound(val resource: String) : ApiFailure // compile error

// good — one package; splitting across files inside it is fine
package com.example.api

sealed interface ApiFailure

// ---- com/example/api/NotFound.kt ----
package com.example.api

data class NotFound(val resource: String) : ApiFailure
```

## 13.3 Model a closed choice as an algebraic data type: a sealed interface whose variants are `data class`es.

> Why? The whole point of a sealed hierarchy is that each variant may carry a
> *different* payload. `data class` gives each variant structural `equals`,
> `hashCode`, `toString`, and destructuring for free, so the variant behaves
> like the value it is rather than like an identity. The Kotlin coding
> conventions'
> [immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability)
> rule applies to the components: "Always declare local variables and
> properties as `val` rather than `var` if they are not modified after
> initialization." A variant with a mutable component silently breaks its own
> `hashCode` — see [Chapter 11](11-data-classes.md). **Suggestion.**

```kotlin
// bad — one class with three nullable fields; nothing stops a caller from
// constructing a "Success" that also carries an error code
class PaymentResult(
    val transactionId: String? = null,
    val declineCode: String? = null,
    val retryAfter: Duration? = null,
)

// good — each variant carries exactly the data that variant has
sealed interface PaymentResult {
    data class Captured(val transactionId: String) : PaymentResult

    data class Declined(val declineCode: String, val reason: String) : PaymentResult

    data class Deferred(val retryAfter: Duration) : PaymentResult
}
```

## 13.4 Use `data object` for a variant that carries no data — never a `class` with no properties, and never an `object` in a hierarchy you print or compare.

> Why? Two instances of a payload-free `class Pending : Status` are not equal
> to each other, so the variant behaves like an identity when it is
> conceptually a value. A plain `object` fixes equality (there is only one
> instance) but its `toString` prints the type name plus an identity hash. The
> [data objects in sealed hierarchies](https://kotlinlang.org/docs/object-declarations.html#use-data-objects-with-sealed-hierarchies)
> documentation exists for precisely this case: `data object` gives the
> singleton a readable `toString` and a structural `equals`/`hashCode`, so it
> mixes cleanly with the `data class` variants beside it. **Suggestion.**

```kotlin
// bad — a fresh instance every time; Pending() != Pending(), and logging one
// prints com.example.Pending@6d06d69c
sealed interface Status {
    class Pending : Status
    data class Failed(val cause: String) : Status
}

// bad — a plain object fixes equality but still prints an identity hash
sealed interface Status {
    object Pending : Status
    data class Failed(val cause: String) : Status
}

// good
sealed interface Status {
    data object Pending : Status
    data class Failed(val cause: String) : Status
}

// Status.Pending == Status.Pending, and Status.Pending.toString() is "Pending"
```

## 13.5 Choose a sealed type over an enum the moment two variants need to carry different data.

> Why? An enum constant is a singleton of one class, so every constant has the
> same shape: the same properties, populated with different values. The moment
> one case needs a `retryAfter: Duration` that no other case has, an enum can
> only express it as a nullable property that is meaningless for every other
> constant — and nothing stops a caller reading it on the wrong one. A sealed
> hierarchy puts the field on the one variant that has it, and the compiler
> refuses to let you read it anywhere else.
> [Chapter 15](15-enums.md) covers the enum side of this decision.
> **Suggestion.**

```kotlin
// bad — retryAfter is null for two of the three constants, and the compiler
// happily lets you read Outcome.CAPTURED.retryAfter
enum class Outcome(val retryAfter: Duration?, val declineCode: String?) {
    CAPTURED(null, null),
    DECLINED(null, "51"),
    DEFERRED(Duration.ofSeconds(30), null),
}

// good — each field lives on the variant that actually has it
sealed interface Outcome {
    data object Captured : Outcome

    data class Declined(val declineCode: String) : Outcome

    data class Deferred(val retryAfter: Duration) : Outcome
}
```

## 13.6 Never write an `else` branch in a `when` over a sealed type.

> Why? This is the single rule that the whole chapter is for. With every
> variant listed and no `else`, adding a new variant turns every `when` in the
> codebase into a compile error that points you at the code you must update.
> Add an `else` and the compiler goes quiet: the new variant silently falls
> into the catch-all, and you find out in production. The
> [`when` documentation](https://kotlinlang.org/docs/control-flow.html#when-expressions-and-statements)
> is explicit that no `else` is needed here: "If your subject is a `Boolean`,
> `enum` class, `sealed` class, or one of their nullable counterparts, you can
> cover all cases without an `else` branch."
> **Violation — enforced by `detekt/ElseCaseInsteadOfExhaustiveWhen`**, which
> is off by default and requires type resolution, so enable it explicitly.

```kotlin
// bad — adding Outcome.Refunded compiles cleanly and silently routes to else
fun describe(outcome: Outcome): String = when (outcome) {
    is Outcome.Captured -> "captured"
    is Outcome.Declined -> "declined: ${outcome.declineCode}"
    else -> "unknown"
}

// good — adding Outcome.Refunded is a compile error here, which is the point
fun describe(outcome: Outcome): String = when (outcome) {
    is Outcome.Captured -> "captured"
    is Outcome.Declined -> "declined: ${outcome.declineCode}"
    is Outcome.Deferred -> "retry in ${outcome.retryAfter}"
}
```

## 13.7 Make the `when` an expression, so exhaustiveness is actually checked.

> Why? Exhaustiveness is only required of a `when` *expression*. The
> [`when` documentation](https://kotlinlang.org/docs/control-flow.html#when-expressions-and-statements)
> states both halves: "If you use `when` as a statement, you don't need to
> cover all possible cases" but "If you use `when` as an expression, you must
> cover all possible cases." A `when` used purely for side effects therefore
> gets no protection from §13.6 at all — a new variant just does nothing.
> The cleanest fix is to have the `when` produce a value the caller uses; the
> explicit `: Unit` expression body is the fallback when there is genuinely
> nothing to return. Note that detekt's `OptionalUnit` would flag the explicit
> `: Unit` form, but it is off by default — if you turn it on, prefer the
> value-producing shape. **Suggestion.**

```kotlin
// bad — a statement; adding Outcome.Deferred compiles and silently does nothing
fun record(outcome: Outcome) {
    when (outcome) {
        is Outcome.Captured -> metrics.increment("captured")
        is Outcome.Declined -> metrics.increment("declined")
    }
}

// good — the when produces a value, so the compiler demands every branch
private fun metricName(outcome: Outcome): String = when (outcome) {
    is Outcome.Captured -> "captured"
    is Outcome.Declined -> "declined"
    is Outcome.Deferred -> "deferred"
}

fun record(outcome: Outcome) {
    metrics.increment(metricName(outcome))
}

// good — when there is nothing to return, an explicit Unit expression body
// still makes the when an expression
fun audit(outcome: Outcome): Unit = when (outcome) {
    is Outcome.Captured -> auditLog.captured()
    is Outcome.Declined -> auditLog.declined(outcome.declineCode)
    is Outcome.Deferred -> auditLog.deferred(outcome.retryAfter)
}
```

## 13.8 Nest the variants inside the sealed declaration when they have no meaning outside it; keep them top-level when they do.

> Why? The
> [Kotlin coding conventions on class layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout)
> give the general form of this rule: "Put nested classes next to the code that
> uses those classes. If the classes are intended to be used externally and
> aren't referenced inside the class, put them in the end." Nesting buys you a
> qualified name (`PaymentResult.Declined`) that reads as what it is at every
> call site, and it keeps the package namespace free of a dozen bare names like
> `Declined` and `Deferred` that mean nothing on their own. Keep a variant
> top-level only when it is a first-class domain concept that callers name
> independently. **Suggestion.**

```kotlin
// bad — Declined and Deferred are meaningless names in the package namespace,
// and a second hierarchy cannot reuse either word
sealed interface PaymentResult

data class Declined(val declineCode: String) : PaymentResult
data class Deferred(val retryAfter: Duration) : PaymentResult

// good — nested; call sites read PaymentResult.Declined
sealed interface PaymentResult {
    data class Declined(val declineCode: String) : PaymentResult
    data class Deferred(val retryAfter: Duration) : PaymentResult
}
```

## 13.9 Group related variants into a nested sealed hierarchy rather than flattening twenty siblings into one list.

> Why? A flat sealed interface with twenty variants forces every `when` to
> enumerate all twenty even when the caller only cares about three groups.
> Nesting the groups as themselves-sealed subtypes lets a caller match at
> whichever level it needs — `is Failure.Transport` handles four variants at
> once — while the innermost `when` still gets full exhaustiveness. Sealing is
> transitive in exactly the way you want: an intermediate sealed subtype keeps
> its own leaves closed. **Suggestion.**

```kotlin
// bad — every caller must enumerate all seven leaves even to distinguish
// "retry" from "give up"
sealed interface SyncFailure {
    data object ConnectionRefused : SyncFailure
    data object DnsFailure : SyncFailure
    data class Timeout(val elapsed: Duration) : SyncFailure
    data class Http5xx(val status: Int) : SyncFailure
    data class Unauthorized(val realm: String) : SyncFailure
    data class Forbidden(val scope: String) : SyncFailure
    data class Malformed(val pointer: String) : SyncFailure
}

// good — callers match at the level they care about
sealed interface SyncFailure {
    sealed interface Transport : SyncFailure {
        data object ConnectionRefused : Transport
        data object DnsFailure : Transport
        data class Timeout(val elapsed: Duration) : Transport
        data class Http5xx(val status: Int) : Transport
    }

    sealed interface Authorization : SyncFailure {
        data class Unauthorized(val realm: String) : Authorization
        data class Forbidden(val scope: String) : Authorization
    }

    data class Malformed(val pointer: String) : SyncFailure
}

fun shouldRetry(failure: SyncFailure): Boolean = when (failure) {
    is SyncFailure.Transport -> true
    is SyncFailure.Authorization -> false
    is SyncFailure.Malformed -> false
}
```

## 13.10 Declare the type parameter of a generic sealed type `out`, and give payload-free variants `Nothing`.

> Why? Without `out`, `Loaded<Cat>` is not a `Loaded<Animal>` and every call
> site needs a cast. Worse, a payload-free variant like `Pending` would need
> its own type argument, so you would be forced to write `Pending<User>` and
> `Pending<Order>` as separate values that are not equal to each other.
> Declaring the parameter
> [covariant](https://kotlinlang.org/docs/generics.html#declaration-site-variance)
> and typing the empty variants as `Nothing` — the type that is a subtype of
> everything — lets one `data object Pending : Loadable<Nothing>` serve every
> `Loadable<T>`. **Suggestion.**

```kotlin
// bad — invariant, so Pending must be parameterised and there is a distinct
// Pending instance per T
sealed interface Loadable<T> {
    class Pending<T> : Loadable<T>
    data class Loaded<T>(val value: T) : Loadable<T>
}

val a: Loadable<User> = Loadable.Pending()
val b: Loadable<User> = Loadable.Pending()
// a != b

// good — covariant, one shared Pending
sealed interface Loadable<out T> {
    data object Pending : Loadable<Nothing>
    data class Loaded<out T>(val value: T) : Loadable<T>
    data class Failed(val cause: Throwable) : Loadable<Nothing>
}

val a: Loadable<User> = Loadable.Pending
val b: Loadable<Order> = Loadable.Pending
// a === b, and Loadable<Cat> is a Loadable<Animal>
```

## 13.11 Return a sealed domain result when the failure is an expected outcome the caller must handle; throw for programming errors.

> Why? A sealed result makes the failure part of the type, so the caller cannot
> compile without addressing it — which is right for "card declined" or "user
> not found", outcomes the business has an answer for. It is wrong for "this
> argument was null", which is a bug: wrapping a bug in a result type forces
> every caller to handle a case that should have crashed at the boundary.
> `kotlin.Result` sits between the two — it carries a `Throwable`, not a domain
> variant, so it tells the caller *that* something failed but not *which of the
> failures you promised* — and it is documented as a
> [value class encapsulating a successful or failed outcome](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-result/).
> [Chapter 24](24-exceptions-and-result.md) covers the full decision.
> **Suggestion.**

```kotlin
// bad — a bug (blank id) and a domain outcome (no such customer) are both
// squeezed into the same nullable return, so the caller cannot tell them apart
fun findCustomer(id: String): Customer? {
    if (id.isBlank()) return null
    return repository.load(id)
}

// good — the bug throws at the boundary; the domain outcome is a variant
sealed interface CustomerLookup {
    data class Found(val customer: Customer) : CustomerLookup
    data object NotFound : CustomerLookup
    data class Suspended(val until: Instant) : CustomerLookup
}

fun findCustomer(id: String): CustomerLookup {
    require(id.isNotBlank()) { "id must not be blank" }
    val customer = repository.load(id) ?: return CustomerLookup.NotFound
    return customer.suspendedUntil
        ?.let { CustomerLookup.Suspended(it) }
        ?: CustomerLookup.Found(customer)
}
```

## 13.12 Do not seal a type that consumers are genuinely meant to extend.

> Why? Sealing is a promise that *you* own the complete list. If the type is an
> extension point — a payment gateway, a validation rule, a serializer — then
> the list is by definition open, and sealing it converts every third-party
> implementation from "supported" into "impossible". The tell is a `when` in
> your own code that ends in a branch doing something generic: if you can write
> a sensible default for an unknown variant, you did not need exhaustiveness,
> and an ordinary `interface` with polymorphic dispatch is the correct tool.
> **Suggestion.**

```kotlin
// bad — sealed, so no consumer of this library can add a gateway, and the
// generic branch shows exhaustiveness was never actually needed
sealed interface PaymentGateway {
    data object Stripe : PaymentGateway
    data object Adyen : PaymentGateway
}

fun charge(gateway: PaymentGateway, amount: Money): Receipt = when (gateway) {
    is PaymentGateway.Stripe -> stripeClient.charge(amount)
    is PaymentGateway.Adyen -> adyenClient.charge(amount)
}

// good — open interface, polymorphic dispatch, consumers can implement it
interface PaymentGateway {
    suspend fun charge(amount: Money): Receipt
}

class StripeGateway(private val client: StripeClient) : PaymentGateway {
    override suspend fun charge(amount: Money): Receipt = client.charge(amount)
}
```

## 13.13 Do not build a sealed hierarchy where one type with an optional field says the same thing.

> Why? A sealed hierarchy costs a file of declarations and a `when` at every
> use site. It earns that cost when the variants carry genuinely different data
> or drive genuinely different behaviour. Two variants that differ only by the
> presence of one field, and whose `when` branches do the same thing either
> way, are a nullable property wearing a costume. **Suggestion.**

```kotlin
// bad — the hierarchy adds a when at every call site to reconstruct a nullable
sealed interface Address {
    data class WithUnit(val street: String, val unit: String, val city: String) : Address
    data class WithoutUnit(val street: String, val city: String) : Address
}

fun format(address: Address): String = when (address) {
    is Address.WithUnit -> "${address.street} ${address.unit}, ${address.city}"
    is Address.WithoutUnit -> "${address.street}, ${address.city}"
}

// good
data class Address(val street: String, val unit: String?, val city: String)

fun format(address: Address): String =
    listOfNotNull(address.street, address.unit).joinToString(" ") + ", ${address.city}"
```

## 13.14 Rely on the smart cast inside a `when` branch; never re-cast the subject with `as`.

> Why? Inside an `is` branch, the compiler has already narrowed the subject —
> the [smart cast](https://kotlinlang.org/docs/typecasts.html#smart-casts) is
> free and cannot fail. Writing `outcome as Outcome.Declined` after the `is`
> check re-introduces the runtime failure the `when` just eliminated, and the
> unsafe cast operator throws `ClassCastException` if the branches are ever
> reordered incorrectly. Note that a smart cast requires a stable subject: a
> `var` property or one from another module will not narrow, which is one more
> reason variant components are `val` (§13.3).
> **Suggestion** — no linter covers this. detekt's `UnsafeCast` sounds
> relevant but only "reports casts that will never succeed", so it stays
> silent on a redundant cast inside an `is` branch, which always succeeds.

```kotlin
// bad — redundant, and reintroduces a ClassCastException path
fun describe(outcome: Outcome): String = when (outcome) {
    is Outcome.Captured -> "captured"
    is Outcome.Declined -> "declined: ${(outcome as Outcome.Declined).declineCode}"
    is Outcome.Deferred -> "retry in ${(outcome as Outcome.Deferred).retryAfter}"
}

// good — outcome is already narrowed inside each branch
fun describe(outcome: Outcome): String = when (outcome) {
    is Outcome.Captured -> "captured"
    is Outcome.Declined -> "declined: ${outcome.declineCode}"
    is Outcome.Deferred -> "retry in ${outcome.retryAfter}"
}
```

## 13.15 Treat a published sealed type as a binary-compatibility promise: adding a variant is a breaking change.

> Why? Sealing constrains subtypes to one module, but it does not constrain
> *consumers* of that module — every downstream `when` over your sealed type is
> exhaustive against the variant list you shipped. Add a variant in a patch
> release and every consumer's `when` stops compiling. Worse, a consumer
> compiled against the old list and run against the new jar hits
> `kotlin.NoWhenBranchMatchedException` at runtime, because that is what the
> compiler emits for a `when` expression with no matching branch and no `else`.
> Either commit to the variant list as public API, or keep the hierarchy
> `internal` and expose a stable façade. **Suggestion.**

```kotlin
// bad — public sealed API in a library; every added variant is a major-version
// break, and old consumers fail at runtime with NoWhenBranchMatchedException
sealed interface HttpFailure {
    data class Timeout(val elapsed: Duration) : HttpFailure
    data class Status(val code: Int) : HttpFailure
}

// good — the closed hierarchy stays internal; the published surface is stable
internal sealed interface HttpFailureInternal {
    data class Timeout(val elapsed: Duration) : HttpFailureInternal
    data class Status(val code: Int) : HttpFailureInternal
    data class Cancelled(val reason: String) : HttpFailureInternal
}

class HttpFailure internal constructor(
    val kind: Kind,
    val detail: String,
) {
    enum class Kind { TIMEOUT, STATUS, OTHER }
}
```

## 13.16 Put behaviour on the variant only when it belongs to the same layer; otherwise dispatch with a `when` where the behaviour lives.

> Why? An abstract member on the sealed interface forces every variant to know
> about that behaviour. That is right for something intrinsic — "is this
> failure retryable?" is a property of the failure. It is wrong for something
> that belongs to a different layer: giving a domain `PaymentResult` an
> abstract `toHttpResponse()` drags the web framework into the domain module
> and makes the domain untestable without it. Keep the variant dumb and put the
> `when` in the layer that owns the concern — you still get exhaustiveness, and
> the dependency points the right way. **Suggestion.**

```kotlin
// bad — the domain model now depends on the web framework, and every new
// variant must be edited to know about HTTP
sealed interface PaymentResult {
    fun toHttpResponse(): ResponseEntity<*>

    data class Captured(val transactionId: String) : PaymentResult {
        override fun toHttpResponse() = ResponseEntity.ok(transactionId)
    }

    data class Declined(val declineCode: String) : PaymentResult {
        override fun toHttpResponse() = ResponseEntity.status(402).body(declineCode)
    }
}

// good — intrinsic behaviour on the variant, layer-specific behaviour outside
sealed interface PaymentResult {
    val isRetryable: Boolean

    data class Captured(val transactionId: String) : PaymentResult {
        override val isRetryable: Boolean get() = false
    }

    data class Declined(val declineCode: String) : PaymentResult {
        override val isRetryable: Boolean get() = declineCode == "91"
    }
}

// in the web module, where the framework already is
fun PaymentResult.toHttpResponse(): ResponseEntity<*> = when (this) {
    is PaymentResult.Captured -> ResponseEntity.ok(transactionId)
    is PaymentResult.Declined -> ResponseEntity.status(402).body(declineCode)
}
```
