<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 36. `Flow`

A `Flow<T>` is a **cold asynchronous stream**. Building one allocates an object
and nothing else — no coroutine starts, no work runs, no resource is acquired
until a terminal operator calls `collect`. Every collector gets its own
independent execution of the whole pipeline. That single property explains
almost every rule in this chapter: because a `Flow` is a recipe rather than a
running process, the questions "who owns it?", "when does it stop?", and "what
thread is it on?" all have answers that differ sharply from a `Thread`, a
`Channel`, or an RxJava `Observable`.

This chapter covers building flows, the operator vocabulary, the two invariants
the runtime enforces (**context preservation** and **exception transparency**),
backpressure, and cancellation. It draws on the
[`Flow` API reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/),
the [asynchronous flow guide](https://kotlinlang.org/docs/flow.html), and the
[flow API reference index](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/).

Three neighbouring topics are deferred. **Hot flows** — `StateFlow`,
`SharedFlow`, `shareIn`, and `stateIn` — are
[Chapter 37, `StateFlow` & `SharedFlow`](37-stateflow-and-sharedflow.md); this
chapter is entirely about cold flows. **`Channel` and `select`** are
[Chapter 38, Channels & `select`](38-channels-and-select.md), which also covers
converting between the two abstractions. **Testing a flow** — `runTest`,
`Turbine`, virtual time — is
[Chapter 39, Coroutine Testing](39-coroutine-testing.md). Dispatcher selection
itself belongs to
[Chapter 34, Dispatchers & Coroutine Context](34-dispatchers-and-context.md);
§36.4 and §36.5 only cover how a dispatcher is *attached* to a flow.

**Tool alignment:** detekt's `coroutines` ruleset mechanically enforces exactly
one rule in this chapter, `SuspendFunWithFlowReturnType` (§36.16). A second
check, `SuspendFunSwallowedCancellation`, fires on an adjacent sin discussed in
§36.6 but does not enforce the rule itself. Rules a named check actually
enforces are marked **Violation**; the rest are **Suggestion**, even where an
adjacent check exists.
The kotlinx.coroutines library also carries its own opt-in markers —
`@FlowPreview` and `@ExperimentalCoroutinesApi` — and this chapter names them
per operator, because an unflagged use of a preview operator is exactly the
kind of finding this skill exists to catch.

## 36.1 Treat every `Flow` as cold — building one does nothing, collecting one does everything.

> Why? The [flow documentation](https://kotlinlang.org/docs/flow.html) states
> that flows are "cold streams... the code inside a `flow` builder does not run
> until the flow is collected." A function that returns a `Flow` has therefore
> performed no I/O, opened no connection, and consumed no quota at the moment it
> returns. Two consequences follow that trip people up constantly: collecting
> the same `Flow` twice runs the pipeline twice, and forgetting to collect it
> runs the pipeline zero times — silently, with no error. **Suggestion.**

```kotlin
// bad — the author expects the audit write to happen; it never does, because
// nothing collects the returned flow
fun recordAndStream(orderId: OrderId): Flow<Event> = flow {
    auditLog.write("stream opened for $orderId")
    emitAll(eventRepository.stream(orderId))
}

fun handle(orderId: OrderId) {
    recordAndStream(orderId) // built, never collected — no audit row is written
}

// good — the side effect is performed by the caller, eagerly, and the flow
// carries only the stream
suspend fun handle(orderId: OrderId) {
    auditLog.write("stream opened for $orderId")
    eventRepository.stream(orderId).collect { event -> process(event) }
}
```

## 36.2 Use `flowOf` or `asFlow` for values you already hold, and `flow { }` only when production itself suspends.

> Why? `flowOf(a, b, c)` and `list.asFlow()` say "these values exist" in one
> line and cannot get the emission context wrong. A `flow { }` builder is for
> the case where producing each value requires a suspending call — a paginated
> HTTP fetch, a cursor walk, a polling loop. Wrapping an already-materialised
> list in `flow { list.forEach { emit(it) } }` adds a suspension machine around
> a plain iteration and hides the fact that the data was never asynchronous.
> **Suggestion.**

```kotlin
// bad — a synchronous list dressed up as an asynchronous stream
fun activeRegions(): Flow<Region> = flow {
    for (region in Region.entries) {
        if (region.active) {
            emit(region)
        }
    }
}

// good — the values already exist; say so
fun activeRegions(): Flow<Region> =
    Region.entries.asFlow().filter { it.active }

// good — flow { } earns its keep when each element requires suspension
fun allOrders(): Flow<Order> = flow {
    var cursor: Cursor? = null
    do {
        val page = orderClient.fetchPage(cursor) // suspends
        page.orders.forEach { emit(it) }
        cursor = page.next
    } while (cursor != null)
}
```

## 36.3 Reserve `channelFlow` for concurrent producers and `callbackFlow` for callback bridges — and always end a `callbackFlow` with `awaitClose`.

> Why? `flow { }` forbids emitting from another coroutine (§36.4). When a source
> genuinely produces from several coroutines at once, or from a listener the
> library invokes on its own thread, `channelFlow` and `callbackFlow` are the
> sanctioned escapes: they back the emission with a `Channel`, so `send` is safe
> across contexts. `callbackFlow` additionally requires the block to suspend
> until the channel closes — the
> [`callbackFlow` reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html)
> says using `awaitClose` "is mandatory in order to prevent memory leaks when
> the flow collection is cancelled" and that the builder "throws
> `IllegalStateException` if block returns, but the channel is not closed yet."
> Without it you leak a registered listener for the lifetime of the process.
> **Suggestion.**

```kotlin
// bad — the callback is registered and never removed; the builder throws
// IllegalStateException at collection time because the block returns early
fun priceTicks(symbol: Symbol): Flow<Tick> = callbackFlow {
    marketData.subscribe(symbol) { tick -> trySend(tick) }
}

// good — awaitClose suspends until the collector cancels, then unregisters
fun priceTicks(symbol: Symbol): Flow<Tick> = callbackFlow {
    val subscription = marketData.subscribe(symbol) { tick ->
        trySend(tick).onFailure { logger.debug { "dropped tick for $symbol" } }
    }
    awaitClose { subscription.cancel() }
}

// good — channelFlow when several coroutines produce into one stream
fun fanIn(shards: List<Shard>): Flow<Record> = channelFlow {
    shards.forEach { shard ->
        launch { shard.records().collect { send(it) } }
    }
}
```

## 36.4 Never change the emission context inside `flow { }` — the only legal way to move upstream work is `flowOn`.

> Why? The
> [`Flow` reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/)
> states the context-preservation invariant plainly: "All flow implementations
> should only emit from the same coroutine context," and "changing the context
> of emission is prohibited, no matter whether it is `withContext(ctx)` or a
> builder argument (e.g. `launch(ctx)`)." The runtime enforces it — a violation
> is not a subtle race, it is an `IllegalStateException` raised at collection
> time reporting that the flow invariant was violated. The rule exists so that a
> collector can reason about which context its lambda runs in without reading
> the producer. **Suggestion** — the failure is a runtime exception, not a
> lint finding.

```kotlin
// bad — withContext inside flow { } violates context preservation and throws
// IllegalStateException when collected
fun reports(): Flow<Report> = flow {
    withContext(Dispatchers.IO) {
        reportDao.findAll().forEach { emit(it) }
    }
}

// good — flowOn moves the upstream, and emit stays on one context
fun reports(): Flow<Report> = flow {
    reportDao.findAll().forEach { emit(it) }
}.flowOn(Dispatchers.IO)
```

## 36.5 Place `flowOn` immediately after the operators it is meant to govern — it changes the upstream only.

> Why? `flowOn` is not a global setting on the pipeline; it rewrites the context
> of everything *declared above it* and leaves everything below untouched. A
> `flowOn(Dispatchers.IO)` written at the end of a chain therefore silently
> moves the CPU-bound `map` in the middle onto the I/O pool as well, and a
> `flowOn` written before an expensive `map` leaves that `map` on the
> collector's dispatcher. Read the chain bottom-up when auditing: each `flowOn`
> claims everything above it up to the next `flowOn`. **Suggestion.**

```kotlin
// bad — one flowOn at the end drags the CPU-bound decode onto the I/O pool,
// and a reader cannot tell that was unintentional
fun thumbnails(ids: List<ImageId>): Flow<Thumbnail> =
    ids.asFlow()
        .map { blobStore.read(it) }     // blocking I/O
        .map { decodeAndScale(it) }     // CPU bound
        .flowOn(Dispatchers.IO)

// good — each stage names its own dispatcher, and the boundary is explicit
fun thumbnails(ids: List<ImageId>): Flow<Thumbnail> =
    ids.asFlow()
        .map { blobStore.read(it) }
        .flowOn(Dispatchers.IO)
        .map { decodeAndScale(it) }
        .flowOn(Dispatchers.Default)
```

## 36.6 Never wrap `emit` in a `try`/`catch`.

> Why? This is the **exception transparency** invariant. Downstream failures
> propagate back through `emit`, so a `try`/`catch` around `emit` catches the
> *collector's* exception and treats it as a producer problem — swallowing an
> error that belongs to code the producer has never seen. The `Flow` reference
> is explicit: "when `emit` or `emitAll` throws, the Flow implementations must
> immediately stop emitting new values and complete with an exception," and the
> machinery "throws `IllegalStateException` on any attempt to emit a value, if
> an exception has been thrown on previous attempt." Catch around the *source*
> call, never around the emission. **Suggestion** — but note that
> `detekt/SuspendFunSwallowedCancellation` fires on the closely related sin of
> wrapping a suspending call in `runCatching`, which swallows
> `CancellationException` the same way.

```kotlin
// bad — catches the collector's exception, then emits again into a broken
// collector; the second emit throws IllegalStateException
fun quotes(ids: List<QuoteId>): Flow<Quote> = flow {
    for (id in ids) {
        try {
            emit(quoteClient.fetch(id))
        } catch (e: IOException) {
            emit(Quote.unavailable(id))
        }
    }
}

// good — the try guards only the fallible source call
fun quotes(ids: List<QuoteId>): Flow<Quote> = flow {
    for (id in ids) {
        val quote = try {
            quoteClient.fetch(id)
        } catch (e: IOException) {
            Quote.unavailable(id)
        }
        emit(quote)
    }
}
```

## 36.7 Recover with the `catch` operator, and remember it sees upstream exceptions only.

> Why? `catch` is the transparency-preserving replacement for a `try` around
> `collect`: it intercepts anything thrown *above* it in the chain and may emit
> a fallback, while deliberately ignoring anything thrown by the collector or by
> operators below it. That asymmetry is the point — a bug in your `collect`
> lambda must not be absorbed by the producer's error handling. Position `catch`
> immediately below the stage whose failures you intend to handle.
> **Suggestion.**

```kotlin
// bad — try/catch around collect also swallows failures from the collector's
// own body, so a NullPointerException in render() looks like a network outage
try {
    priceFeed.collect { render(it) }
} catch (e: Exception) {
    showOfflineBanner()
}

// good — catch handles upstream failure and leaves collector bugs to propagate
priceFeed
    .catch { cause ->
        logger.warn(cause) { "price feed failed, showing last known values" }
        emitAll(cachedPrices())
    }
    .collect { render(it) }
```

## 36.8 Use `onStart` to seed, `onEach` to observe, and `onCompletion` to clean up — none of them substitutes for `catch`.

> Why? These four operators occupy distinct slots and are routinely misused for
> one another. `onStart` runs before the first upstream emission and may itself
> emit (a loading placeholder). `onEach` is a pass-through side effect. The
> lambda passed to `onCompletion` receives the terminal cause — `null` on normal
> completion, the exception otherwise — and runs on cancellation too, which
> makes it the right home for resource release. But `onCompletion` **observes**
> a failure without consuming it: the exception still propagates. Only `catch`
> stops it. **Suggestion.**

```kotlin
// bad — onCompletion is used as if it swallowed the error; the exception still
// reaches the collector, and the "success" branch is never distinguished
searchResults(query)
    .onCompletion { showSpinner(false) }
    .collect { render(it) }

// good — each operator does its own job, in the right order
searchResults(query)
    .onStart { showSpinner(true) }
    .onEach { metrics.increment("search.result") }
    .catch { cause -> showError(cause.message) }
    .onCompletion { cause ->
        showSpinner(false)
        if (cause == null) {
            markDone()
        }
    }
    .collect { render(it) }
```

## 36.9 Retry with `retry` or `retryWhen` rather than a hand-rolled loop, and never retry a `CancellationException`.

> Why? A hand-rolled retry inside `flow { }` re-runs the producer *including its
> emissions*, so a failure on element 900 replays elements 1 to 899 into the
> collector. `retry`/`retryWhen` restart the upstream from scratch under
> controlled conditions, and the operator documentation states that it "is
> transparent to exceptions that occur in downstream flow and does not retry on
> exceptions that are thrown to cancel the flow", so the predicate never has to
> screen for cancellation itself. The `retryWhen` predicate has signature
> `suspend FlowCollector<T>.(cause: Throwable, attempt: Long) -> Boolean`, so it
> can back off with `delay` and can emit a placeholder before deciding. What the
> operator will not do for you is bound the attempts or tell a transient failure
> from a permanent one, so a predicate that returns `true` unconditionally
> hammers a malformed request or a 403 forever. **Suggestion.**

```kotlin
// bad — an unbounded, undiscriminating predicate: a 403 or a parse failure is
// retried forever, with no attempt limit and no backoff between attempts
inventoryFeed()
    .retryWhen { cause, _ -> cause is Exception }
    .collect { apply(it) }

// good — retry only what is genuinely transient, with a bounded backoff
inventoryFeed()
    .retryWhen { cause, attempt ->
        val retryable = cause is IOException && attempt < MAX_RETRIES
        if (retryable) {
            delay(BASE_BACKOFF * (1L shl attempt.toInt()))
        }
        retryable
    }
    .collect { apply(it) }
```

## 36.10 Use `transform` when an operator changes the number of elements in the stream.

> Why? `map` is one-in-one-out and `filter` is one-in-zero-or-one-out. When a
> stage must emit two elements for one input, or none for some and three for
> others, `transform` expresses it directly with an explicit `emit` per output.
> The common workarounds — `map` to a `List` followed by `flatMapConcat`, or
> `map` to a nullable followed by `filterNotNull` — cost an allocation per
> element and force the reader to reconstruct the cardinality from two operators
> instead of one. **Suggestion.**

```kotlin
// bad — a list-per-element allocation, and the cardinality change is split
// across two operators
transactions
    .map { txn -> if (txn.isSplit) txn.legs() else listOf(txn) }
    .flatMapConcat { it.asFlow() }

// good — one operator, explicit emissions, no intermediate list
transactions.transform { txn ->
    if (txn.isSplit) {
        txn.legs().forEach { emit(it) }
    } else {
        emit(txn)
    }
}
```

## 36.11 Choose the flattening operator by semantics — and note all three are `@ExperimentalCoroutinesApi`.

> Why? `flatMapConcat` collects each inner flow to completion before starting
> the next, preserving order at the cost of throughput. `flatMapMerge` runs up
> to `concurrency` inner flows at once and interleaves their output. Guarded by
> `@ExperimentalCoroutinesApi`, `flatMapLatest` cancels the previous inner flow
> the moment a new outer value arrives, which is exactly right for
> search-as-you-type and exactly wrong for anything with a side effect you must
> not abandon halfway. All three — along with `mapLatest` and `transformLatest`
> — carry `@ExperimentalCoroutinesApi` as of kotlinx.coroutines 1.11, so their
> behaviour may change; opt in explicitly at the declaration rather than letting
> the warning ride. **Suggestion.**

```kotlin
// bad — flatMapMerge for a stream whose order is part of the contract; the
// ledger entries interleave and the running balance is wrong
@OptIn(ExperimentalCoroutinesApi::class)
fun ledger(accounts: Flow<AccountId>): Flow<Entry> =
    accounts.flatMapMerge { entriesFor(it) }

// good — order-preserving concatenation where order matters
@OptIn(ExperimentalCoroutinesApi::class)
fun ledger(accounts: Flow<AccountId>): Flow<Entry> =
    accounts.flatMapConcat { entriesFor(it) }

// good — flatMapLatest where a superseded query should be abandoned
@OptIn(ExperimentalCoroutinesApi::class)
fun suggestions(queries: Flow<String>): Flow<List<Suggestion>> =
    queries.flatMapLatest { search(it) }
```

## 36.12 Use `combine` when every source contributes its latest value, and `zip` when the sources must be paired element by element.

> Why? These two look interchangeable and are not. `combine` fires on *any*
> source emitting and pairs it with the most recent value of the others, so a
> chatty source produces many outputs against one stale value from a quiet one.
> `zip` waits until *both* sources have produced the next element and pairs them
> strictly positionally, completing as soon as the shorter one does. Picking
> `combine` for a positional pairing produces duplicated left-hand values;
> picking `zip` for a "latest state" join stalls the whole pipeline behind the
> slowest source. **Suggestion.**

```kotlin
// bad — zip for a latest-state join: the panel stops updating as soon as the
// (rarely changing) settings flow stops emitting
val panel: Flow<Panel> = liveMetrics.zip(userSettings) { m, s -> Panel(m, s) }

// good — combine re-renders whenever either side changes
val panel: Flow<Panel> = liveMetrics.combine(userSettings) { m, s -> Panel(m, s) }

// good — zip is right when the pairing is genuinely positional
val labelled: Flow<Labelled> = values.zip(labels) { v, l -> Labelled(v, l) }
```

## 36.13 Insert `buffer` to overlap a slow producer with a slow collector, and `conflate` when only the newest value matters.

> Why? By default a flow is fully sequential — the producer suspends inside
> `emit` until the collector's lambda returns, so total time is the sum of both.
> `buffer` runs the producer in its own coroutine with a queue between them, so
> total time approaches the max. `conflate` is documented as a shortcut for
> `buffer(Channel.CONFLATED)`: a slow collector
> skips intermediate values instead of back-pressuring the producer. Reach for
> `conflate` only where dropping is semantically safe — a UI gauge, yes; a
> payment event, no. **Suggestion.**

```kotlin
// bad — producer and collector strictly alternate; a 100 ms fetch and a 100 ms
// write take 200 ms per element
pageFetcher.pages()
    .collect { page -> warehouse.write(page) }

// good — buffer decouples them; throughput is bounded by the slower stage alone
pageFetcher.pages()
    .buffer(capacity = 16)
    .collect { page -> warehouse.write(page) }

// good — conflate where only the freshest sample is meaningful
sensorReadings()
    .conflate()
    .collect { reading -> gauge.render(reading) }
```

## 36.14 Suppress repeats with `distinctUntilChanged`, and use `distinctUntilChangedBy` when identity lives in one field.

> Why? `distinctUntilChanged` compares consecutive elements with `equals`, so it
> is only meaningful on a type whose `equals` is value-based — a `data class`, a
> `value class`, an enum. Calling it on a type with reference equality drops
> nothing and misleads the reader into thinking deduplication is happening. When
> only part of the element identifies it (a version-stamped record, say), name
> that part with `distinctUntilChangedBy` rather than writing an `equals` that
> lies. **Suggestion.**

```kotlin
// bad — Session has identity equality, so nothing is ever suppressed
class Session(val userId: UserId, val lastSeen: Instant)

sessions.distinctUntilChanged().collect { refresh(it) }

// good — deduplicate on the field that actually carries identity
sessions.distinctUntilChangedBy { it.userId }.collect { refresh(it) }

// good — value-based equality makes the plain operator meaningful
data class Session(val userId: UserId, val lastSeen: Instant)

sessions.distinctUntilChanged().collect { refresh(it) }
```

## 36.15 `debounce` and `sample` are `@FlowPreview` — opt in at the declaration and record why.

> Why? Both time-based rate limiters carry `@FlowPreview` in kotlinx.coroutines
> 1.11, which is a stronger warning than `@ExperimentalCoroutinesApi`: the API
> shape itself may change. They are also easy to confuse. `debounce` emits an
> element only after the source has been quiet for the given window — right for
> "wait until the user stops typing". `sample` emits the latest element on a
> fixed cadence regardless of quiet periods — right for "at most one update per
> second". Using `debounce` for a steady stream that never goes quiet emits
> nothing at all. **Suggestion.**

```kotlin
// bad — an unflagged preview operator, and debounce on a continuously busy
// source emits nothing because the quiet window never elapses
fun throttled(ticks: Flow<Tick>): Flow<Tick> =
    ticks.debounce(200.milliseconds)

// good — the opt-in is explicit, and sample matches "at most one per window"
@OptIn(FlowPreview::class)
fun throttled(ticks: Flow<Tick>): Flow<Tick> =
    ticks.sample(200.milliseconds)

// good — debounce where the source genuinely goes quiet
@OptIn(FlowPreview::class)
fun settledQuery(keystrokes: Flow<String>): Flow<String> =
    keystrokes.debounce(300.milliseconds)
```

## 36.16 Never mark a function that returns a `Flow` as `suspend`.

> Why? The `suspend` modifier promises the caller that the function does work
> before it returns a value. A cold flow does no work when built (§36.1), so the
> modifier is at best a lie and at worst forces every caller into a coroutine to
> obtain an object that would have been free. detekt's rule documentation for
> this case states the intent directly: it prevents `suspend` modifiers on
> functions returning `Flow`, maintaining cold observable stream semantics.
> If the function truly must suspend before it can build the flow, that argument
> should be a parameter instead.
> **Violation — enforced by `detekt/SuspendFunWithFlowReturnType`.**

```kotlin
// bad — the caller must be in a coroutine just to construct a cold flow
suspend fun auditTrail(tenant: TenantId): Flow<AuditEntry> =
    flow { emitAll(auditDao.stream(tenant)) }

// good — building is free; suspension happens at collection
fun auditTrail(tenant: TenantId): Flow<AuditEntry> =
    flow { emitAll(auditDao.stream(tenant)) }

// good — when a suspending lookup is genuinely required, hoist it to the caller
fun auditTrail(scope: TenantScope): Flow<AuditEntry> =
    flow { emitAll(auditDao.stream(scope.tenantId)) }
```

## 36.17 End with the narrowest terminal operator the caller actually needs.

> Why? `collect`, `toList`, `first`, `firstOrNull`, `single`, `reduce`, and
> `fold` differ in how much of the stream they consume and what they assert.
> `first()` cancels the upstream after one element; `toList().first()` drains
> the entire stream, materialises every element, and then throws away all but
> one — a correctness problem, not just a performance one, when the flow is
> infinite. `single()` additionally asserts that exactly one element exists and
> throws otherwise, which is a useful invariant to encode rather than to comment.
> **Suggestion.**

```kotlin
// bad — drains an unbounded stream to answer a question about its head
val latest: Reading = sensorReadings().toList().first()

// bad — silently accepts a second match that indicates a data bug
val account: Account = accountsMatching(iban).first()

// good — cancels upstream after one element
val latest: Reading = sensorReadings().first()

// good — encodes "exactly one" as an assertion the runtime checks
val account: Account = accountsMatching(iban).single()

// good — fold when the answer is an aggregate, not an element
val total: Money = lineItems().fold(Money.ZERO) { acc, item -> acc + item.amount }
```

## 36.18 Do not assume a `flow { }` body is cancellable when it never suspends — check with `ensureActive()`.

> Why? Coroutine cancellation is cooperative: it takes effect at suspension
> points. The `flow` builder and every `SharedFlow` are documented as already
> cancellable — `emit` itself checks — but a producer that computes for a long
> time *between* emissions has no suspension point and will run to completion
> after cancellation. The `cancellable()` operator is documented as a shortcut
> for `.onEach { currentCoroutineContext().ensureActive() }`, which tells you
> both the fix and its cost: it is a per-element check, and it does nothing for a
> long-running body between elements. For that, call `ensureActive()` inside the
> loop. **Suggestion.**

```kotlin
// bad — cancelling the collector does not stop this; the loop runs to the end
fun primes(limit: Int): Flow<Int> = flow {
    for (n in 2..limit) {
        if (isPrimeByTrialDivision(n)) { // seconds of CPU for large n
            emit(n)
        }
    }
}

// good — an explicit cooperation point inside the expensive loop
fun primes(limit: Int): Flow<Int> = flow {
    for (n in 2..limit) {
        currentCoroutineContext().ensureActive()
        if (isPrimeByTrialDivision(n)) {
            emit(n)
        }
    }
}

// good — cancellable() where the flow comes from a non-cancellable source you
// do not control, such as a plain iterable
fun records(rows: Iterable<Row>): Flow<Row> = rows.asFlow().cancellable()
```

## 36.19 Prefer `onEach { }.launchIn(scope)` to `scope.launch { flow.collect { } }` when collection is the whole coroutine body.

> Why? `launchIn(scope)` is exactly `scope.launch { collect() }`, but written as
> the last link of the chain it keeps the pipeline reading top-to-bottom instead
> of forcing the reader to jump inside a `launch` block to find the terminal
> operator. It also makes the returned `Job` the obvious handle for cancellation.
> The rule is stylistic, with one substantive edge: `launchIn` takes no lambda,
> so anything you would have written after `collect` inside the `launch` block
> must move into `onCompletion`. **Suggestion.**

```kotlin
// bad — the pipeline is buried one nesting level down, and the Job is anonymous
viewScope.launch {
    notifications()
        .filter { it.severity >= Severity.WARN }
        .collect { banner.show(it) }
}

// good — linear chain, named Job, explicit scope ownership
private val bannerJob: Job =
    notifications()
        .filter { it.severity >= Severity.WARN }
        .onEach { banner.show(it) }
        .launchIn(viewScope)
```

## 36.20 Never nest `collect` inside `collect` when you meant to flatten.

> Why? An inner `collect` inside an outer collector's lambda runs sequentially
> inside the outer emission, so the outer producer is back-pressured for the
> entire lifetime of every inner flow. If any inner flow is infinite, the outer
> flow advances exactly once and then hangs forever — with no error, no log, and
> no obvious culprit. The flattening operators in §36.11 exist precisely to make
> the intended concurrency explicit. **Suggestion.**

```kotlin
// bad — if watch(project) never completes, the outer flow never sees a second
// project, and the bug presents as "only the first project updates"
projects().collect { project ->
    watch(project).collect { change -> apply(change) }
}

// good — the intent (watch all projects concurrently) is stated by the operator
@OptIn(ExperimentalCoroutinesApi::class)
suspend fun applyAllChanges() {
    projects()
        .flatMapMerge { project -> watch(project) }
        .collect { change -> apply(change) }
}
```
