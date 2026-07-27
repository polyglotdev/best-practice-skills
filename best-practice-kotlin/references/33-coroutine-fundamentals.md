<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 33. Coroutine Fundamentals

A coroutine is not a thread, a task queue entry, or a lightweight `Runnable`. It
is a computation that the compiler has rewritten so it can stop in the middle
and start again later, plus a small runtime that decides *where* and *when* the
restart happens. Almost every coroutine bug in production traces back to
forgetting the first half of that sentence — treating `suspend` as a synonym for
"runs in the background" — or forgetting the second — starting work that no
longer has an owner willing to stop it.

This chapter covers the model: what `suspend` compiles to, what structured
concurrency guarantees, how scopes and jobs form a tree, how failure travels
through that tree, and the four builders (`launch`, `async`, `withContext`,
`runBlocking`) you actually need. It draws on the
[Coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html),
[Composing suspending functions](https://kotlinlang.org/docs/composing-suspending-functions.html),
[Coroutine exceptions handling](https://kotlinlang.org/docs/exception-handling.html),
and the
[kotlinx.coroutines API reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/).

Four neighbouring topics are deferred. Which dispatcher to pick, how
`CoroutineContext` composes, and how to inject a dispatcher are
[Chapter 34, Dispatchers & Coroutine Context](34-dispatchers-and-context.md).
Cancellation, `CancellationException`, and timeouts are
[Chapter 35, Cancellation & Timeouts](35-cancellation-and-timeouts.md) — this
chapter mentions cancellation only where structured concurrency depends on it.
Streams of values are [Chapter 36, `Flow`](36-flow.md). The consolidated
catalogue of things not to do — with the shortest possible reproduction for each
— is [Chapter 40, Coroutine Anti-patterns](40-coroutine-anti-patterns.md); the
rules here are the reasoning behind that catalogue.

**Tool alignment:** detekt ships a `coroutines` rule set that covers part of this
chapter. `RedundantSuspendModifier` and `SuspendFunWithFlowReturnType` are active
in detekt's default configuration; `GlobalCoroutineUsage`,
`SuspendFunWithCoroutineScopeReceiver`, `SuspendFunInFinallySection`, and
`SuspendFunSwallowedCancellation` exist but are **inactive by default** and must
be switched on in `detekt.yml` before they catch anything. Rules a named check
actually enforces are marked **Violation**; the rest are **Suggestion**.

## 33.1 Treat `suspend` as "this function can pause and resume", never as "this function runs in the background".

> Why? The compiler rewrites a `suspend` function into a state machine and adds a
> hidden `Continuation` parameter — the continuation-passing-style (CPS)
> transformation. Each suspension point becomes a state the function can be
> re-entered at. What the transformation does **not** add is a second thread of
> control: calling a `suspend` function is still an ordinary sequential call that
> returns when the callee is done. Two `suspend` calls in a row take the sum of
> their latencies, exactly like two blocking calls. Concurrency comes from
> `launch` and `async`, never from the `suspend` keyword. **Suggestion.**

```kotlin
// bad — reads as "both fetches happen at once"; they do not. The two round trips
// are strictly sequential and the total latency is their sum.
suspend fun loadDashboard(userId: UserId): Dashboard {
    val profile = profileClient.fetch(userId)
    val orders = orderClient.recent(userId)
    return Dashboard(profile, orders)
}

// good — concurrency is written down, not assumed
suspend fun loadDashboard(userId: UserId): Dashboard = coroutineScope {
    val profile = async { profileClient.fetch(userId) }
    val orders = async { orderClient.recent(userId) }
    Dashboard(profile.await(), orders.await())
}
```

## 33.2 Never start a coroutine in `GlobalScope`.

> Why? `GlobalScope` is annotated `@DelicateCoroutinesApi` for a reason the docs
> state plainly: it is "easy to use to create new coroutines, avoiding all
> bureaucracy of structured concurrency, but it also means losing all its
> benefits."
> [The API reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-global-scope/)
> lists three concrete failures: work continues after the thing it was serving is
> gone, a coroutine that never resumes leaks whatever it holds ("the socket will
> not be closed, leading to a resource leak"), and an uncaught exception falls
> through to platform last-resort handling. A `GlobalScope` coroutine has no
> parent, so nothing can cancel it and nothing waits for it.
> **Violation — enforced by `detekt/GlobalCoroutineUsage`** once enabled; it is
> inactive in detekt's default configuration.

```kotlin
// bad — outlives the request that started it, cannot be cancelled, and its
// failure reaches Thread.uncaughtExceptionHandler rather than your error handling
fun onDocumentSaved(documentId: DocumentId) {
    GlobalScope.launch {
        searchIndex.reindex(documentId)
    }
}

// good — the scope is a dependency with an owner and a lifetime
class DocumentIndexer(
    private val scope: CoroutineScope,
    private val searchIndex: SearchIndex,
) {
    fun onDocumentSaved(documentId: DocumentId): Job = scope.launch {
        searchIndex.reindex(documentId)
    }
}
```

## 33.3 Never construct a `CoroutineScope` inside a function and drop the reference.

> Why? `CoroutineScope(...)` is a factory, not a block — it returns a live scope
> whose `Job` you are now responsible for cancelling. If the reference goes out of
> scope at the end of the function, nothing can ever cancel the children, and you
> have rebuilt `GlobalScope` with extra steps. A scope must be a *field* of
> something with a lifecycle, or it must be a lexical `coroutineScope { }` block
> that ends when the block ends. **Suggestion.**

```kotlin
// bad — a fresh, unreachable scope per call; the launch is unstoppable and the
// function returns before the work has started, let alone finished
fun archive(orderId: OrderId) {
    CoroutineScope(Dispatchers.IO).launch {
        archiveStore.write(orderId)
    }
}

// good — lexical scope; the function does not return until the child completes,
// and cancelling the caller cancels the child
suspend fun archive(orderId: OrderId) = coroutineScope {
    launch { archiveStore.write(orderId) }
}
```

## 33.4 Inside a `suspend` function, get a scope from `coroutineScope { }` — never from a constructor.

> Why? `coroutineScope` builds a child scope of the *caller's* scope, suspends
> until every child launched inside it completes, and rethrows the first child
> failure after cancelling its siblings. That is the whole structured-concurrency
> contract in one builder: the function cannot return while work it started is
> still running, and the caller's cancellation reaches everything the function
> spawned. A hand-built `CoroutineScope` has none of those properties.
> **Suggestion.**

```kotlin
// bad — compiles and usually works, but the children belong to an orphan scope:
// cancelling the caller does not cancel the fetches, and if `pricing` fails the
// `customer` request is left running until it completes on its own
suspend fun enrich(order: Order): Enriched {
    val scope = CoroutineScope(Dispatchers.Default)
    val customer = scope.async { customerClient.fetch(order.customerId) }
    val pricing = scope.async { pricingClient.quote(order) }
    return Enriched(order, customer.await(), pricing.await())
}

// good — coroutineScope waits, propagates cancellation, and rethrows failures
suspend fun enrich(order: Order): Enriched = coroutineScope {
    val customer = async { customerClient.fetch(order.customerId) }
    val pricing = async { pricingClient.quote(order) }
    Enriched(order, customer.await(), pricing.await())
}
```

## 33.5 Reach for `supervisorScope { }` only when a child's failure genuinely must not cancel its siblings.

> Why? `coroutineScope` is the correct default because it treats every child as
> load-bearing: one failure cancels the rest and surfaces immediately, so you
> never build a result out of partial data. `supervisorScope` disables that —
> [the docs](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/supervisor-scope.html)
> put it this way: "if a child coroutine launched in the new scope fails, it will
> not affect the other children of the scope." Use it when each child is an
> independent unit of work whose failure is a data point, not an abort signal.
> Note the asymmetry, which the same page spells out — "if the block finishes with
> an exception, it will cancel the scope and all its children": failure of the
> **block itself** still takes everything down.
> **Suggestion.**

```kotlin
// bad — one bad webhook endpoint cancels every other delivery in the batch
suspend fun deliverAll(events: List<WebhookEvent>) = coroutineScope {
    events.forEach { event -> launch { webhookClient.deliver(event) } }
}

// good — deliveries are independent; a failure is recorded, not fatal
suspend fun deliverAll(events: List<WebhookEvent>): List<DeliveryResult> =
    supervisorScope {
        events
            .map { event ->
                async {
                    try {
                        DeliveryResult.Delivered(event.id, webhookClient.deliver(event))
                    } catch (e: IOException) {
                        DeliveryResult.Failed(event.id, e)
                    }
                }
            }
            .awaitAll()
    }
```

Note the narrow `catch (e: IOException)`. A `catch (e: Exception)` here would
swallow `CancellationException` and break the very structure this rule relies on
— see [Chapter 35, §35.2](35-cancellation-and-timeouts.md).

## 33.6 Use `launch` when you want the effect and `async` when you want the value — and never call `async` without a matching `await`.

> Why? `launch` returns a `Job`, which carries completion but no result, and its
> failure propagates up the job tree. `async` returns a `Deferred`, which *holds*
> the failure until someone calls `await()`; the API reference is explicit that
> "the caller of `async` is responsible for handling the exceptions in the returned
> `Deferred` value." Where that bites is a **root** `async` — one that is not a
> child of another coroutine, which is what you get in a `supervisorScope` or on a
> `SupervisorJob`-based scope. The exception-handling guide draws exactly that
> line: used as root coroutines, `launch` and friends "treat exceptions as uncaught
> exceptions", while `async` and `produce` are "relying on the user to consume the
> final exception, for example via `await`". A root `async` nobody awaits therefore
> swallows its own exception silently — the work fails, nothing logs, and the
> caller carries on as though it succeeded. Inside a plain `coroutineScope` the
> failure is not lost, because a failing child still cancels the scope and
> `coroutineScope` rethrows; it just arrives as a scope-wide cancellation instead
> of at the call site. Either way: want the effect and not the value, use `launch`.
> **Suggestion** — no linter can see a missing `await`.

```kotlin
// bad — the scope is supervised, so this `async` is a root coroutine: the failure
// is parked in a Deferred nobody reads and nothing ever logs it
private val scope = CoroutineScope(SupervisorJob() + defaultDispatcher)

fun record(entry: AuditEntry) {
    scope.async { auditStore.append(entry) }
}

// good — no result wanted, so `launch`; the failure has nowhere else to go and
// reaches the scope's CoroutineExceptionHandler (§33.12) instead of vanishing
fun record(entry: AuditEntry): Job = scope.launch { auditStore.append(entry) }
```

## 33.7 Never wrap a single call in `async { }` and immediately `await()` it.

> Why? `async { block }.await()` runs `block` and waits for it, which is what
> calling `block` directly already does. The wrapper buys a `Deferred`
> allocation, a dispatch, and a reader who has to check whether anything
> concurrent is going on. `async` earns its keep only when at least two of them
> are in flight before the first `await`. **Suggestion.**

```kotlin
// bad — a Deferred created and consumed on the next line; no concurrency at all
suspend fun currentRate(pair: CurrencyPair): Rate = coroutineScope {
    val deferred = async { rateClient.fetch(pair) }
    deferred.await()
}

// good
suspend fun currentRate(pair: CurrencyPair): Rate = rateClient.fetch(pair)
```

## 33.8 Await a collection of `Deferred` values with `awaitAll`, not a loop of `await()`.

> Why? `awaitAll` fails fast, and the API reference contrasts the two forms
> directly: it "is not equivalent to `deferreds.map { it.await() }` which fails
> only when it sequentially gets to wait for the failing deferred, while this
> `awaitAll` fails immediately as soon as any of the deferreds fail." A
> `map { it.await() }` loop waits on element 0 before it ever observes that
> element 7 already failed, so the caller sees the failure later and holds every
> in-flight resource until then. **Suggestion.**

```kotlin
// bad — blocks on the slowest early element before noticing a later failure
suspend fun quoteAll(items: List<Item>): List<Quote> = coroutineScope {
    val deferred = items.map { async { pricingClient.quote(it) } }
    deferred.map { it.await() }
}

// good — fails as soon as any quote fails
suspend fun quoteAll(items: List<Item>): List<Quote> = coroutineScope {
    items.map { async { pricingClient.quote(it) } }.awaitAll()
}
```

## 33.9 Use `withContext` to change the context, never to introduce concurrency.

> Why? `withContext` is a `suspend` function that runs its block, waits for it,
> and returns its value — the API reference says it "does not introduce
> concurrency" and is "similar to `coroutineScope`" in creating a lexically
> scoped child. Two `withContext` calls in a row are as sequential as two plain
> calls. Reaching for it to "parallelise" is the single most common
> misunderstanding of the API after §33.1. **Suggestion.**

```kotlin
// bad — the author believed these overlap; they run one after the other
suspend fun snapshot(userId: UserId): Snapshot {
    val prefs = withContext(ioDispatcher) { prefsDao.load(userId) }
    val quota = withContext(ioDispatcher) { quotaDao.load(userId) }
    return Snapshot(prefs, quota)
}

// good — withContext for the dispatcher, async for the concurrency
suspend fun snapshot(userId: UserId): Snapshot = coroutineScope {
    val prefs = async(ioDispatcher) { prefsDao.load(userId) }
    val quota = async(ioDispatcher) { quotaDao.load(userId) }
    Snapshot(prefs.await(), quota.await())
}
```

## 33.10 When a component genuinely owns background work, build the scope as `CoroutineScope(SupervisorJob() + dispatcher)` and cancel it in a lifecycle hook.

> Why? A component that starts work from a non-suspending entry point needs a
> scope that outlives the call but not the component. `SupervisorJob()` keeps one
> failed unit of work from tearing down every other one the component owns
> (§33.11), the explicit dispatcher stops the scope defaulting to
> `Dispatchers.Default` by accident, and the cancel in the shutdown hook is what
> makes the scope's lifetime *defined* rather than "until the JVM exits". Without
> the cancel, the scope is `GlobalScope` wearing a field name. **Suggestion.**

```kotlin
// bad — no SupervisorJob, so one failed reindex cancels the scope permanently,
// and nothing ever cancels it on shutdown
@Service
class Reindexer(private val searchIndex: SearchIndex) {
    private val scope = CoroutineScope(Dispatchers.Default)

    fun submit(documentId: DocumentId) {
        scope.launch { searchIndex.reindex(documentId) }
    }
}

// good — supervised, explicitly dispatched, and cancelled with the bean
@Service
class Reindexer(private val searchIndex: SearchIndex) : DisposableBean {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    fun submit(documentId: DocumentId): Job = scope.launch {
        searchIndex.reindex(documentId)
    }

    override fun destroy() {
        scope.cancel()
    }
}
```

## 33.11 Know that an uncaught failure in a child cancels its parent and every sibling — unless the parent's job is a `SupervisorJob`.

> Why? This is the rule that makes structured concurrency safe and also the one
> that surprises people. Failure travels *up* to the parent job, which cancels
> itself and therefore every other child. A `SupervisorJob` overrides only the
> upward half: children still die when the parent is cancelled, but a child's
> failure stops at the supervisor. Passing `SupervisorJob()` into a *child*
> builder does nothing useful — the supervision has to sit at the level that owns
> the siblings you want to protect. **Suggestion.**

```kotlin
// bad — SupervisorJob passed to the child; the child now has no parent at all,
// so the scope neither waits for it nor learns that it failed
scope.launch(SupervisorJob()) {
    riskyWork()
}

// good — supervision at the level that owns the siblings
val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
scope.launch { riskyWork() }   // a failure here does not cancel the sibling
scope.launch { otherWork() }
```

## 33.12 Install a `CoroutineExceptionHandler` at the root of a `launch` hierarchy only — it is never consulted for `async`.

> Why? The handler is documented as "a last-resort mechanism" for exceptions
> "without a clear propagation path". `async` always has a propagation path — the
> returned `Deferred` — so the handler is dead code there; the API reference shows
> exactly this case with the comment "This line will not be printed!". It is also
> ignored on a non-root coroutine, because a child's exception is delegated to its
> parent rather than handled locally. Attach it to the scope (or the outermost
> `launch`) and nowhere else. **Suggestion.**

```kotlin
// bad — a handler on an `async`: the failure goes into the Deferred instead, and
// the API reference marks this exact case "This line will not be printed!"
scope.async(CoroutineExceptionHandler { _, e -> logger.error("lost", e) }) {
    settle(paymentId)
}

// good — handler in the scope's context, where a root `launch` will reach it
private val handler = CoroutineExceptionHandler { _, cause ->
    logger.error("unhandled failure in settlement scope", cause)
}
private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default + handler)

fun settleAsync(paymentId: PaymentId): Job = scope.launch { settle(paymentId) }
```

## 33.13 Make every `suspend` function main-safe: the callee chooses the dispatcher, never the caller.

> Why? A `suspend` function whose contract is "call me on `Dispatchers.IO`" has
> pushed a correctness requirement into a KDoc line, where the compiler cannot
> check it and reviewers will not notice it. Main-safety means a function is safe
> to call from any dispatcher because it switches internally to whatever it
> needs. That makes the function composable — callers stop reasoning about
> threads entirely — and it puts the `withContext` next to the blocking call it
> exists to protect. See
> [Chapter 34](34-dispatchers-and-context.md) for which dispatcher to choose.
> **Suggestion.**

```kotlin
// bad — the requirement lives in a comment, and every call site must repeat it
/** Must be called from `Dispatchers.IO`. */
suspend fun loadInvoice(id: InvoiceId): Invoice = invoiceDao.findBlocking(id)

// good — safe from any dispatcher; the switch is the callee's business
suspend fun loadInvoice(id: InvoiceId): Invoice = withContext(ioDispatcher) {
    invoiceDao.findBlocking(id)
}
```

## 33.14 Call `runBlocking` only from `main`, from a test, or from a non-suspending callback boundary.

> Why? `runBlocking` blocks the calling thread until its coroutine finishes. The
> API reference says it exists "to bridge regular blocking code to libraries that
> are written in suspending style, to be used in `main` functions, in tests, and
> in non-`suspend` callbacks", and warns that calling it from a `suspend`
> function "will block, potentially leading to thread starvation issues" — you
> have given up the one property that made the code suspending. Inside a coroutine
> it is always redundant: you can just call the function.
> **Suggestion.** For the test-specific replacement, `runTest`, see
> [Chapter 39, Coroutine Testing](39-coroutine-testing.md).

```kotlin
// bad — blocks a dispatcher thread from inside a coroutine, for nothing
suspend fun loadConfiguration(): Config {
    val data = runBlocking { fetchConfigurationData() }
    return Config.from(data)
}

// good
suspend fun loadConfiguration(): Config = Config.from(fetchConfigurationData())

// good — a genuine boundary: a non-suspending framework callback
override fun onMessage(message: Message) {
    runBlocking { handler.handle(message.toCommand()) }
}
```

## 33.15 Do not mark a function `suspend` unless it actually suspends.

> Why? `suspend` is a viral restriction: it can only be called from another
> `suspend` function or a coroutine builder, so a spurious one forces every caller
> up the chain to become suspending or to open a coroutine. detekt describes the
> cost as unnecessarily restricting the function's usage. If the body never calls
> another `suspend` function, drop the modifier.
> **Violation — enforced by `detekt/RedundantSuspendModifier`.**

```kotlin
// bad — nothing in the body suspends; every caller is now forced into a coroutine
suspend fun normalise(email: String): Email = Email(email.trim().lowercase())

// good
fun normalise(email: String): Email = Email(email.trim().lowercase())
```

## 33.16 Do not declare a `suspend` function with a `CoroutineScope` receiver.

> Why? A `suspend fun CoroutineScope.doWork()` invites callers to `launch` inside
> a scope that is not the function's own, so the children outlive the call and
> escape the caller's structured-concurrency guarantees — the function returns
> while its work is still running. detekt adds a second reason: a `suspend`
> function "also has its own `coroutineContext`, which is now ambiguous and mixed
> with the receiver's", so it is no longer obvious which scope a `launch` in the
> body belongs to. If a function needs to start children, it should open
> `coroutineScope { }` itself (§33.4) and own them.
> **Violation — enforced by `detekt/SuspendFunWithCoroutineScopeReceiver`** once
> enabled; it is inactive in detekt's default configuration.

```kotlin
// bad — returns before either child finishes; the caller's scope is left holding
// work it never asked for
suspend fun CoroutineScope.warmCaches(tenantId: TenantId) {
    launch { priceCache.warm(tenantId) }
    launch { catalogCache.warm(tenantId) }
}

// good — the function owns its children and does not return until they are done
suspend fun warmCaches(tenantId: TenantId) = coroutineScope {
    launch { priceCache.warm(tenantId) }
    launch { catalogCache.warm(tenantId) }
}
```
