<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 29. Context Parameters

Context parameters let a function declare a dependency that the *caller's
scope* supplies rather than the call site passing explicitly. They exist to
remove the plumbing parameter — the logger, the transaction, the request
scope, the JSON encoder — that threads through twelve signatures so that the
thirteenth can use it.

**Read the status section below before you use anything in this chapter.**
This feature has moved twice in three releases, and a great deal of material
on the internet teaches a syntax that no longer compiles.

**Status, as of Kotlin 2.4 — verified against the release notes.**

| Piece | Introduced | Status | Opt-in |
|---|---|---|---|
| Context parameters (core) | 2.2 | Listed as **Stable** in the 2.4 release notes | none on 2.4; `-Xcontext-parameters` on 2.2/2.3 |
| Context *arguments* (explicit) | 2.4 | **Experimental** | `-Xexplicit-context-arguments` |
| Callable references to context declarations | — | **Not stabilised in 2.4** | — |
| Context *receivers* (the prototype they replaced) | 1.6.20 | **Removed** | — |

[Kotlin 2.2](https://kotlinlang.org/docs/whatsnew22.html) introduced context
parameters as Experimental behind `-Xcontext-parameters`, and stated plainly
that "context parameters replace an older experimental feature called context
receivers". The [Kotlin 2.4 release notes](https://kotlinlang.org/docs/whatsnew24.html)
list, under language features "now Stable in this release": "Context
parameters, except for context arguments and callable references."

There is a live inconsistency in the upstream documentation worth knowing
about: the dedicated
[context parameters page](https://kotlinlang.org/docs/context-parameters.html)
still opens with "This feature is Experimental. To opt in, add the following
compiler option to your build file." The two pages disagree. The safe reading
— and the one this chapter takes — is that the *core* declaration form has
stabilised in 2.4 while the surrounding pieces have not, and that you should
confirm against the exact compiler version your build pins before committing
to either. That verification takes thirty seconds and is the difference
between a working build and a mystery flag.

Two neighbouring topics are deferred. **Ordinary parameter and function
design**, including when an extension receiver is the right shape, is
[Chapter 8, Functions](08-functions.md). **Dependency injection in a Spring
application** — the mechanism context parameters are most often mistaken for
— is [Chapter 42, Spring: Beans & Injection in Kotlin](42-spring-beans-and-injection.md).
The coroutine `CoroutineContext`, which is a *runtime* map and shares nothing
but a word with this feature, is
[Chapter 34, Dispatchers & Coroutine Context](34-dispatchers-and-context.md).

**Tool alignment:** neither ktlint nor detekt ships a rule for context
parameters at the time of writing. Every rule in this chapter is therefore a
**Suggestion**, and none of them will be caught by CI — which is itself an
argument for §29.14.

## 29.1 Confirm the feature's status against your pinned compiler version before writing a single `context(...)`.

> Why? The status table above changed in 2.2, in 2.3.20, and again in 2.4. A
> team on 2.2 needs `-Xcontext-parameters` and will get "unresolved
> reference" without it; a team on 2.4 does not; a team that adopted the
> 2.2 flag and upgraded may now be passing a flag the compiler warns about.
> Worse, [Kotlin 2.4](https://kotlinlang.org/docs/whatsnew24.html) notes that
> "Kotlin 2.3.20 changed the overload resolution for context parameters. As a
> result, calls to overloads that differ only by context parameters can become
> ambiguous" — meaning code that compiled on 2.3.0 may not compile on 2.3.20
> without the change in §29.10. This is not a feature you can adopt from
> memory. **Suggestion.**

```kotlin
// bad — copied from a 2.2-era blog post into a 2.4 build; the flag is at best
// redundant and at worst a warning the team learns to ignore
kotlin {
    compilerOptions {
        freeCompilerArgs.add("-Xcontext-parameters")
    }
}

// good — on 2.2/2.3, the flag is required and the comment says why
kotlin {
    compilerOptions {
        // Context parameters are Experimental on Kotlin 2.2/2.3; remove this when
        // the toolchain moves to 2.4, where the core feature is Stable.
        freeCompilerArgs.add("-Xcontext-parameters")
    }
}
```

## 29.2 Never write the context-receiver syntax `context(Type)`; the parameter must be named.

> Why? Context receivers were removed, not renamed. Kotlin 2.2 states that
> "the main difference is that context parameters are not introduced as
> receivers in the body of a function. As a result, you need to use the name
> of the context parameters to access their members, unlike with context
> receivers, where the context is implicitly available." Every tutorial,
> conference talk, and Stack Overflow answer written between 2022 and 2025
> teaches the receiver form — `context(LoggingScope)` with `log(...)` called
> bare inside the body — and none of it compiles. If you find that shape in
> your codebase, it predates 2.2 and needs migrating, not extending.
> **Suggestion.**

```kotlin
// bad — context receiver syntax: the type has no name and members are called
// implicitly. Removed from the language.
context(UserService)
fun outputMessage(message: String) {
    log("Log: $message")
}

// good — context parameter: named, and members are reached through the name
context(users: UserService)
fun outputMessage(message: String) {
    users.log("Log: $message")
}
```

## 29.3 Use `_` as the name when the context value is only there to be re-propagated, never read.

> Why? [The reference](https://kotlinlang.org/docs/context-parameters.html)
> documents `_` as a name that makes "the value available for resolution
> without accessing it by name". The alternative is inventing a name you
> never use, which draws the reader's eye to a binding that does nothing, and
> which some warning configurations flag as unused. `_` says exactly the
> right thing: *this function needs the context to exist so that the
> functions it calls can resolve it, and it does not touch it itself.*
> **Suggestion.**

```kotlin
// bad — `users` is bound but never read; the reader hunts for its use
context(users: UserService)
fun logWelcome() {
    outputMessage("Welcome!")
}

// good — the underscore states that this frame only forwards the context
context(_: UserService)
fun logWelcome() {
    outputMessage("Welcome!")
}
```

## 29.4 Reach for a context parameter only for a genuinely ambient dependency — never for a value the caller is thinking about.

> Why? The whole benefit is removing a parameter from *every* signature in a
> call chain. That only pays when the value is the same for the entire chain
> and the caller does not choose it per call: a request-scoped correlation
> id, an open transaction, a permission subject, a serialization format. If
> the caller picks the value — an order id, a page size, a target currency —
> it belongs in the parameter list where the reader can see it. Making a
> caller-chosen value ambient is how you get a function whose behaviour
> depends on something invisible at the call site, which is the exact
> complaint people have about `ThreadLocal`. **Suggestion.**

```kotlin
// bad — `currency` is a decision the caller makes per call, hidden in context
context(currency: Currency)
fun formatTotal(order: Order): String =
    currency.format(order.total)

// good — the decision stays visible at the call site
fun formatTotal(order: Order, currency: Currency): String =
    currency.format(order.total)

// good — a transaction genuinely is ambient for the whole call chain
context(tx: Transaction)
fun archiveOrder(id: OrderId) {
    tx.execute("update orders set archived = true where id = ?", id.value)
}
```

## 29.5 Do not use context parameters as a substitute for constructor injection.

> Why? Constructor injection gives you a dependency that is resolved once, is
> `val`, is visible in the type's own signature, and that a test can replace
> by constructing the object differently. A context parameter gives you a
> dependency resolved at every call site by type, invisible in the class
> declaration, and replaceable only by changing every caller's scope. The
> first is a design; the second is an implicit global with better manners.
> In Spring in particular, the container *is* the injection mechanism — see
> [Chapter 42, §42.1](42-spring-beans-and-injection.md) for the constructor
> `val` rule. **Suggestion.**

```kotlin
// bad — the service's dependencies are invisible in its declaration, and a
// test must construct a context rather than a service
class OrderService {
    context(repo: OrderRepository, clock: Clock)
    fun place(request: PlaceOrder): OrderId { ... }
}

// good — dependencies are in the constructor, where a reader and a test both
// find them
class OrderService(
    private val repo: OrderRepository,
    private val clock: Clock,
) {
    fun place(request: PlaceOrder): OrderId { ... }
}
```

## 29.6 Do not use context parameters to model something that is actually per-coroutine runtime state.

> Why? Context parameters are resolved by the **compiler**, statically, from
> lexical scope. They do not travel across a `launch`, they are not part of
> `CoroutineContext`, and they cannot be read by a framework at runtime. If
> what you need is "this value follows the work wherever it is dispatched" —
> an MDC correlation id, a tracing span, a security principal in a reactive
> chain — the correct mechanism is a `CoroutineContext.Element`, covered in
> [Chapter 34](34-dispatchers-and-context.md), or the SLF4J `MDCContext`
> element in [Chapter 31, §31.13](31-logging.md). Confusing the two produces
> a design that compiles and then loses the value the first time work crosses
> a dispatcher. **Suggestion.**

```kotlin
// bad — the context parameter does not survive the launch; the coroutine body
// cannot see `trace` and this does not compile, which is the lucky case
context(trace: TraceId)
suspend fun handle(request: Request) = coroutineScope {
    launch { emitSpan() }  // emitSpan() requires context(TraceId): unresolved
}

// good — runtime propagation needs a runtime context element
suspend fun handle(request: Request) = coroutineScope {
    withContext(TraceContext(request.traceId)) {
        launch { emitSpan() }
    }
}
```

## 29.7 Do not design an API that needs a context parameter on a constructor; constructors cannot have one.

> Why? [The reference](https://kotlinlang.org/docs/context-parameters.html)
> lists this restriction outright: constructors cannot declare context
> parameters. Discovering it halfway through a refactor is expensive, because
> the usual workaround — a factory function in the companion object that
> carries the context and calls a private constructor — changes the type's
> public shape. Decide up front: if construction needs the dependency, it is
> a constructor parameter (§29.5), and the context parameter, if any, belongs
> on the *operations*. **Suggestion.**

```kotlin
// bad — does not compile: a constructor cannot declare a context parameter
class AuditLog(private val name: String) {
    context(clock: Clock)
    constructor(prefix: String, name: String) : this("$prefix-$name")
}

// good — the dependency is an ordinary constructor parameter
class AuditLog(
    private val name: String,
    private val clock: Clock,
)

// good — if you genuinely want context-driven construction, it is a factory
class AuditLog private constructor(
    private val name: String,
    private val clock: Clock,
) {
    companion object {
        context(clock: Clock)
        fun named(name: String): AuditLog = AuditLog(name, clock)
    }
}
```

## 29.8 A property with a context parameter has no backing field, no initializer, and no delegate — declare it as a computed getter or not at all.

> Why? The reference states the restriction directly: properties with context
> parameters cannot have backing fields or initializers, and cannot be
> delegated. This follows from the semantics — the property's value depends
> on which context is in scope at the *use* site, so there is no single value
> to store. Writing `context(fmt: Formatter) val label: String = ...` fails
> to compile with a message about the initializer that does not immediately
> point at the context parameter as the cause. See
> [Chapter 17, Properties & Backing Fields](17-properties-and-backing-fields.md)
> and [Chapter 16, Delegation](16-delegation.md). **Suggestion.**

```kotlin
// bad — initializer on a context property: does not compile
context(fmt: MoneyFormatter)
val Order.label: String = fmt.format(total)

// bad — delegation on a context property: does not compile
context(fmt: MoneyFormatter)
val Order.label: String by lazy { fmt.format(total) }

// good — a computed getter, evaluated against whatever context is in scope
context(fmt: MoneyFormatter)
val Order.label: String
    get() = fmt.format(total)
```

## 29.9 Never put two context parameters of the same type in scope; give each one a distinct type.

> Why? Context resolution is by **type**, not by name: the reference notes
> that if multiple compatible values exist at the same scope level, the
> compiler reports an ambiguity error. Two `String` context parameters, or
> two `Clock`s, or a `UserService` shadowed by another `UserService` from an
> enclosing scope, produce a resolution failure at every call site rather
> than at the declaration — so the error lands on innocent code far from the
> cause. The fix is the same one that fixes every "two values of the same
> primitive type" problem: a
> [value class](12-value-classes.md) per role. **Suggestion.**

```kotlin
// bad — two String contexts; every call inside this scope is ambiguous
context(tenantId: String, correlationId: String)
fun audit(event: String) { ... }

// good — distinct types make resolution unambiguous and the call site readable
@JvmInline value class TenantId(val value: String)

@JvmInline value class CorrelationId(val value: String)

context(tenant: TenantId, correlation: CorrelationId)
fun audit(event: String) { ... }
```

## 29.10 Disambiguate overloads that differ only by context parameter with an explicit context argument — Experimental in 2.4, requires `-Xexplicit-context-arguments`.

> Why? [Kotlin 2.4](https://kotlinlang.org/docs/whatsnew24.html) added this
> for a concrete regression: "Kotlin 2.3.20 changed the overload resolution
> for context parameters. As a result, calls to overloads that differ only by
> context parameters can become ambiguous. You can now resolve this ambiguity
> by passing an explicit context argument at the call site." The release
> notes label it plainly: "This feature is Experimental. To opt in, add the
> following compiler option to your build file: `-Xexplicit-context-arguments`."
> That means an unflagged use does not compile and a flagged use is exposed
> to churn across compiler versions — treat it as a targeted escape hatch for
> a specific ambiguity, not as a general call-site style. **Suggestion.**

```kotlin
// bad — with both senders in scope, `sendNotification()` is ambiguous
context(defaultEmailSender: EmailSender, defaultSmsSender: SmsSender)
fun notifyUser() {
    sendNotification()   // ambiguity: which overload?
    sendNotification()
}

// good — Experimental in Kotlin 2.4; requires -Xexplicit-context-arguments
context(defaultEmailSender: EmailSender, defaultSmsSender: SmsSender)
fun notifyUser() {
    sendNotification(emailSender = defaultEmailSender)
    sendNotification(smsSender = defaultSmsSender)
}

// good — no flag needed: avoid the ambiguity instead of resolving it
context(defaultEmailSender: EmailSender, defaultSmsSender: SmsSender)
fun notifyUser() {
    sendEmailNotification(defaultEmailSender)
    sendSmsNotification(defaultSmsSender)
}
```

## 29.11 Do not build an API on callable references to context-parameter declarations; they are excluded from the 2.4 stabilisation.

> Why? The 2.4 stable list reads "Context parameters, except for context
> arguments **and callable references**." Anything that stabilises "except
> for X" is telling you that X is still moving. A `::` reference to a
> function with a context parameter is precisely the kind of construct that
> a higher-order API bakes into its public signature, so getting it wrong
> costs a source-incompatible change later. Wrap the call in a lambda
> instead, which is stable, equally readable, and imposes no constraint on
> how the reference form eventually settles. **Suggestion.**

```kotlin
// bad — a callable reference to a context-parameter function, in a public API
context(_: AuditLog)
fun record(event: Event) { ... }

fun install(handler: (Event) -> Unit) { ... }

context(_: AuditLog)
fun wireUp() {
    install(::record)   // callable references here are not stable in 2.4
}

// good — an explicit lambda; the reference form is never exposed
context(_: AuditLog)
fun wireUp() {
    install { event -> record(event) }
}
```

## 29.12 Keep context parameters out of the public API of a published library or shared module.

> Why? A context parameter is part of the caller's compile-time obligation:
> every consumer must arrange for a value of that type to be in lexical scope
> before they can call your function. For a library that is a hard adoption
> cost, and for a feature whose surrounding pieces are still Experimental
> (see the status table) it is a cost you may have to renegotiate on the next
> compiler bump. Use them, if at all, *inside* a module — behind a normal
> public function that takes the dependency explicitly. See
> [Chapter 5, Declarations & Visibility](05-declarations-and-visibility.md).
> **Suggestion.**

```kotlin
// bad — every consumer of this library must now construct a RenderScope in
// lexical scope before they can call the entry point
context(scope: RenderScope)
fun renderInvoice(invoice: Invoice): String { ... }

// good — ordinary public entry point; the context stays an internal detail
fun renderInvoice(invoice: Invoice, theme: Theme): String {
    val scope = RenderScope(theme)
    return with(scope) { renderBody(invoice) }
}

context(scope: RenderScope)
private fun renderBody(invoice: Invoice): String { ... }
```

## 29.13 Do not add a context parameter for something an extension receiver already expresses.

> Why? Kotlin already has a mechanism for "this function operates in the
> presence of an X": the extension receiver. `fun Transaction.archive(id:
> OrderId)` reads at the call site as `tx.archive(id)`, needs no compiler
> flag, no status table, and no scope arrangement. A context parameter earns
> its keep only when you need *more than one* such value, or when the natural
> receiver is already taken by the thing the function is about. Using it to
> restate a single receiver adds an unfamiliar construct and removes the call
> site's clue about what the function operates on. See
> [Chapter 8, Functions](08-functions.md) and the coding conventions on
> [extension functions](https://kotlinlang.org/docs/coding-conventions.html#extension-functions).
> **Suggestion.**

```kotlin
// bad — one ambient value, expressed with the newer, heavier construct
context(tx: Transaction)
fun archiveOrder(id: OrderId) {
    tx.execute("update orders set archived = true where id = ?", id.value)
}

// good — an extension receiver, which the call site shows: tx.archiveOrder(id)
fun Transaction.archiveOrder(id: OrderId) {
    execute("update orders set archived = true where id = ?", id.value)
}

// good — two ambient values is where a context parameter starts to pay
context(tx: Transaction, audit: AuditLog)
fun OrderId.archive() {
    tx.execute("update orders set archived = true where id = ?", value)
    audit.record("order.archived", value)
}
```

## 29.14 On a 2.4 production codebase, default to explicit parameters and constructor injection; adopt context parameters only where you can absorb compiler churn.

> Why? This is the honest recommendation and it is worth stating plainly.
> The core feature is listed as Stable in 2.4, but two of its parts are not,
> the dedicated documentation page still says Experimental, the overload
> resolution changed in a patch release inside the 2.3 line, and no linter
> in the Kotlin ecosystem understands the construct yet — so nothing in CI
> will tell you when a usage drifts. Set against that, the benefit is
> removing a parameter from some signatures. Explicit parameters and
> constructor injection have none of that risk and cost you a few characters
> per call. The trade is worth taking in an **internal DSL**, in a module
> whose compiler version is pinned and upgraded deliberately, or in code
> whose whole reason to exist is the scoped-context pattern. It is not worth
> taking in ordinary service code. **Suggestion.**

```kotlin
// bad — context parameters threaded through ordinary service code on 2.4,
// for the sake of removing one argument from three call sites
context(clock: Clock)
fun expireSession(session: Session): Session =
    session.copy(expiredAt = clock.instant())

// good — an explicit parameter; nothing to re-verify on the next upgrade
fun expireSession(session: Session, clock: Clock): Session =
    session.copy(expiredAt = clock.instant())

// good — a DSL is where the pattern genuinely earns its cost
context(builder: HtmlBuilder)
fun p(text: String) {
    builder.append("<p>").append(text).append("</p>")
}
```

## 29.15 If you do adopt them, confine them to one module, pin the Kotlin version, and record the decision.

> Why? Every Experimental-adjacent feature needs an exit plan, and the exit
> is cheap only while the usage is contained. A module boundary gives you a
> single place to check on a compiler upgrade, a single build file carrying
> the opt-in flag (on 2.2/2.3) or the version assumption (on 2.4), and a
> single blast radius if the resolution rules shift again as they did in
> 2.3.20. Recording *why* matters as much as recording *what*: the next
> person to see `context(` will otherwise assume it is ordinary idiom and
> spread it. This mirrors the skill-wide rule that no experimental feature
> appears without its opt-in and a justification. **Suggestion.**

```kotlin
// bad — the flag is in the root build file, so every module in the repo may
// silently start using the feature
allprojects {
    tasks.withType<KotlinCompile>().configureEach {
        compilerOptions.freeCompilerArgs.add("-Xexplicit-context-arguments")
    }
}

// good — scoped to the one module that needs it, with the reason recorded
// :render-dsl/build.gradle.kts
kotlin {
    compilerOptions {
        // Explicit context arguments are Experimental in Kotlin 2.4. Used only
        // by the HTML DSL in this module to disambiguate the EmailSender /
        // SmsSender overloads. Re-verify on every Kotlin upgrade.
        freeCompilerArgs.add("-Xexplicit-context-arguments")
    }
}
```
