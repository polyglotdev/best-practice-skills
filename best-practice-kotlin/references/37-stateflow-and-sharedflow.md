<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 37. `StateFlow` & `SharedFlow`

[Chapter 36](36-flow.md) is entirely about **cold** flows: a recipe that runs
once per collector, owned by whoever collects it, finished when the collector
finishes. This chapter is about the two **hot** flows in kotlinx.coroutines, and
almost everything that matters about them follows from inverting that sentence.
A hot flow runs whether or not anyone is collecting, is shared by every
collector, and is owned by a `CoroutineScope` rather than by a consumer. That
makes lifetime and resource ownership the central design questions — a leaked
scope is a leaked upstream subscription, and a hot flow that never completes
turns `toList()` into a hang.

The chapter covers `StateFlow` (always has a value, conflated, never completes),
`SharedFlow` (configurable replay and buffering, no initial value), how to
choose between them, and how to promote a cold flow to hot with `shareIn` and
`stateIn`. It draws on the
[`StateFlow`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)
and
[`SharedFlow`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)
API references and the
[`SharingStarted`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/)
strategies.

Three things are deferred. **Operators** — `map`, `catch`, `buffer`, the
flattening family — are [Chapter 36](36-flow.md) and apply unchanged to hot
flows, with the one caveat in §37.14. The **backing-property pattern** used to
expose a read-only view is [Chapter 17, §17.5](17-properties-and-backing-fields.md);
§37.3 applies it rather than re-deriving it. **`Channel`**, the other hot
primitive, is [Chapter 38](38-channels-and-select.md) — read §38.1 before
choosing a `Channel` over a `SharedFlow` for events. Testing hot flows is
[Chapter 39](39-coroutine-testing.md).

**Tool alignment:** no detekt rule understands hot-flow lifetime, so almost
every rule here is a **Suggestion**. The one exception is scope creation:
`detekt/GlobalCoroutineUsage` fires on `GlobalScope`, which is the single most
common way to leak a hot flow's upstream. Treat the absence of enforcement as a
reason to review these by hand, not as a reason to relax.

## 37.1 Decide "hot or cold" first, because it decides who owns the resource.

> Why? A cold flow's upstream starts when a collector arrives and stops when
> that collector leaves — the consumer owns the lifetime, and correctness is
> local. A hot flow's upstream starts and stops with its **scope**, which usually
> belongs to some longer-lived object, so the upstream can outlive every
> collector, keep a socket open, keep polling an API, and keep billing you.
> Making a flow hot is a resource-ownership decision, not a performance tweak,
> and the question to ask is "who cancels the scope?" If you cannot name that
> object, the flow should stay cold. **Suggestion.**

```kotlin
// bad — made hot "so it is faster", in a scope nobody ever cancels; the poll
// loop runs for the lifetime of the process
class RateService(private val client: RateClient) {
    val rates: SharedFlow<Rate> =
        pollRates().shareIn(GlobalScope, SharingStarted.Eagerly, replay = 1)
}

// good — cold by default; each caller owns its own collection
class RateService(private val client: RateClient) {
    fun rates(): Flow<Rate> = pollRates()
}

// good — hot where sharing is genuinely required, in a scope with an owner
class RateService(
    private val client: RateClient,
    private val scope: CoroutineScope, // cancelled by the component that built it
) {
    val rates: SharedFlow<Rate> =
        pollRates().shareIn(scope, SharingStarted.WhileSubscribed(5_000), replay = 1)
}
```

## 37.2 Use `StateFlow` for state and `SharedFlow` for events.

> Why? `StateFlow` is defined by the invariant that it always has exactly one
> current `value`, conflates updates, and never completes. That is the shape of
> *state*: "the connection is `Degraded`", "there are 4 items in the cart". A
> `SharedFlow` has no current value and delivers each emission to whoever is
> subscribed at the time. That is the shape of an *event*: "the save failed",
> "the user tapped retry". Using the wrong one is not a style preference — it is
> a data-loss or data-duplication bug, spelled out in §37.8. **Suggestion.**

```kotlin
// bad — connection state modelled as an event stream, so a screen that starts
// collecting late has no idea whether the connection is up
private val _connection = MutableSharedFlow<ConnectionState>()
val connection: SharedFlow<ConnectionState> = _connection.asSharedFlow()

// good — state is a StateFlow; a late collector immediately sees the current value
private val _connection = MutableStateFlow<ConnectionState>(ConnectionState.Idle)
val connection: StateFlow<ConnectionState> = _connection.asStateFlow()

// good — events are a SharedFlow
private val _errors = MutableSharedFlow<SaveError>(extraBufferCapacity = 16)
val errors: SharedFlow<SaveError> = _errors.asSharedFlow()
```

## 37.3 Keep the `Mutable*` flow private and expose the read-only view with `asStateFlow()` / `asSharedFlow()`.

> Why? This is the backing-property pattern from
> [Chapter 17, §17.5](17-properties-and-backing-fields.md), applied to flows: a
> public `MutableStateFlow` lets any caller assign `value`, which destroys the
> single-writer invariant that makes state reasoning tractable. Declaring the
> public property as `StateFlow` is *not* sufficient on its own: the object
> handed out is still a `MutableStateFlow`, so an `as` cast reaches the setter.
> `asStateFlow()`
> returns a genuine read-only wrapper, and its documented purpose is exactly
> this: it "represents a mutable state flow as a read-only state flow."
> **Suggestion.**

```kotlin
// bad — any caller can write; there is no single writer
class CartViewModel {
    val itemCount = MutableStateFlow(0)
}

// bad — the declared type is read-only, but the object is not; a cast reaches
// the setter
class CartViewModel {
    private val _itemCount = MutableStateFlow(0)
    val itemCount: StateFlow<Int> = _itemCount
}

// good — asStateFlow() wraps, so the cast escape hatch is closed
class CartViewModel {
    private val _itemCount = MutableStateFlow(0)
    val itemCount: StateFlow<Int> = _itemCount.asStateFlow()

    fun add(item: Item) {
        _itemCount.update { it + 1 }
    }
}
```

## 37.4 Make the state type value-equal and immutable, because `StateFlow` conflates with `equals`.

> Why? The `StateFlow` reference calls this "strong equality-based conflation":
> "values in state flow are conflated using `Any.equals` comparison in a similar
> way to `distinctUntilChanged` operator," and "state flow behavior with classes
> that violate the contract for `Any.equals` is unspecified." Two failure modes
> follow. A class with default identity equality never conflates, so every
> assignment re-emits even when nothing changed. A **mutable** class mutated in
> place is worse: the new value is `equals` to the old one because it *is* the
> old one, so the update is conflated away and collectors never see the change.
> Use a `data class` or a `value class` of immutable components.
> **Suggestion.**

```kotlin
// bad — mutable state object mutated in place; equals compares the same
// instance to itself, so the assignment is conflated away and nobody updates
class Filters(var query: String, var onlyActive: Boolean)

private val _filters = MutableStateFlow(Filters("", false))

fun setQuery(q: String) {
    _filters.value.query = q
    _filters.value = _filters.value // no-op: same instance, conflated
}

// good — immutable data class; copy() produces a value that is not equals to
// the previous one, so the emission survives conflation
data class Filters(val query: String, val onlyActive: Boolean)

private val _filters = MutableStateFlow(Filters("", onlyActive = false))

fun setQuery(q: String) {
    _filters.update { it.copy(query = q) }
}
```

## 37.5 Use `update` for any read-modify-write on a `MutableStateFlow`.

> Why? `value = value + 1` is two operations with a window between them; two
> coroutines running it concurrently lose an increment. `update` is documented as
> updating "the `MutableStateFlow.value` atomically using the specified function
> of its value" via compare-and-set. The price is stated in the same doc: "the
> function may be evaluated multiple times if the value is being concurrently
> updated," so the lambda must be a pure function of its input — no logging, no
> I/O, no counters incremented inside it. **Suggestion.**

```kotlin
// bad — lost update under concurrency
fun increment() {
    _count.value = _count.value + 1
}

// bad — update with a side effect; the audit line is written once per CAS retry
fun increment() {
    _count.update {
        auditLog.record("incremented")
        it + 1
    }
}

// good — pure transform, atomic under contention
fun increment() {
    _count.update { it + 1 }
}
```

## 37.6 Size a `MutableSharedFlow` deliberately: `replay`, `extraBufferCapacity`, `onBufferOverflow`.

> Why? The defaults are `replay = 0`, `extraBufferCapacity = 0`,
> `onBufferOverflow = BufferOverflow.SUSPEND` — a completely unbuffered flow on
> which `emit` suspends until every current subscriber has taken the value. The
> `tryEmit` documentation is precise about the corner people get wrong: it "can
> return `false` only when the `BufferOverflow` strategy is `SUSPEND` and there
> are subscribers collecting this flow", and when there are no subscribers "the
> buffer is not used", the value is dropped (no replay cache is configured), and
> `tryEmit` reports `true`. So an unbuffered flow loses the value either way and
> the return code does not reliably tell you. That is a reasonable default for
> back-pressured events and a terrible one for fire-and-forget notifications
> emitted from a non-suspending context. Note the documented constraint: values
> of `onBufferOverflow` other than `SUSPEND` "are supported only when
> `replay > 0` or `extraBufferCapacity > 0`". **Suggestion.**

```kotlin
// bad — zero buffer plus tryEmit: the toast is dropped whether or not anyone is
// subscribed, and the return code does not consistently report the loss
private val _toasts = MutableSharedFlow<Toast>()

fun show(toast: Toast) {
    _toasts.tryEmit(toast) // false while anyone collects, true (and dropped) otherwise
}

// good — buffer sized for the burst, newest-wins on overflow, and the result
// of tryEmit is not thrown away
private val _toasts = MutableSharedFlow<Toast>(
    extraBufferCapacity = 32,
    onBufferOverflow = BufferOverflow.DROP_OLDEST,
)

fun show(toast: Toast) {
    check(_toasts.tryEmit(toast)) { "toast buffer must never reject with DROP_OLDEST" }
}
```

## 37.7 Set `replay` to the number of past events a *late* subscriber legitimately needs — usually zero.

> Why? `replay` is not a buffer for throughput; it is a promise to re-deliver old
> values to subscribers that were not there when they happened. For genuine
> one-shot events that promise is wrong: a screen that resubscribes after a
> configuration change re-receives "payment failed" and shows the dialog twice.
> Use `replay = 1` only where the last value is genuinely current state — at
> which point ask whether you wanted a `StateFlow` (§37.2). If you need the
> replay buffer for buffering rather than for replay, that is what
> `extraBufferCapacity` is for. **Suggestion.**

```kotlin
// bad — replay resurrects a consumed one-shot event on every resubscribe
private val _navigation = MutableSharedFlow<NavCommand>(replay = 1)

// good — no replay for one-shot events; buffer without replaying
private val _navigation = MutableSharedFlow<NavCommand>(extraBufferCapacity = 8)
```

## 37.8 Never use a `StateFlow` for one-shot events.

> Why? Both of `StateFlow`'s defining behaviours are wrong for events.
> Conflation means two identical events in a row (two failures with the same
> message) collapse into one, so the second is **lost**. Replay-of-one means a
> new collector immediately receives the last event, so it is **duplicated**. The
> usual patch — emitting a sentinel `null` after each event to "consume" it —
> encodes an event queue in a state variable and races the moment there are two
> collectors. Use a `SharedFlow` with `replay = 0`, or a `Channel`
> ([Chapter 38](38-channels-and-select.md)) when exactly-one-consumer delivery is
> required. **Suggestion.**

```kotlin
// bad — conflation loses the second identical error, and every new collector
// re-receives the last one
private val _error = MutableStateFlow<String?>(null)
val error: StateFlow<String?> = _error.asStateFlow()

fun fail(message: String) {
    _error.value = message
    _error.value = null // "consume" — races every other collector
}

// good — events are events
private val _errors = MutableSharedFlow<String>(extraBufferCapacity = 16)
val errors: SharedFlow<String> = _errors.asSharedFlow()

suspend fun fail(message: String) {
    _errors.emit(message)
}
```

## 37.9 Promote a cold flow with `shareIn` or `stateIn` — never by hand-launching a collector into a mutable flow.

> Why? The hand-rolled version — `scope.launch { cold.collect { _state.value = it } }`
> — reimplements `stateIn` with none of its guarantees: no subscription
> accounting, no upstream restart, no stop timeout, and a `Job` you have to
> remember to cancel. `shareIn` and `stateIn` encapsulate all of that behind one
> call whose parameters (`scope`, `started`, `initialValue`) are exactly the
> three decisions the situation actually requires. **Suggestion.**

```kotlin
// bad — a hand-rolled sharing coroutine; the Job leaks, and the upstream keeps
// running with zero subscribers
class PresenceService(private val scope: CoroutineScope) {
    private val _online = MutableStateFlow(emptySet<UserId>())
    val online: StateFlow<Set<UserId>> = _online.asStateFlow()

    init {
        scope.launch { presenceStream().collect { _online.value = it } }
    }
}

// good — stateIn owns the sharing coroutine and the subscription accounting
class PresenceService(private val scope: CoroutineScope) {
    val online: StateFlow<Set<UserId>> = presenceStream()
        .stateIn(
            scope = scope,
            started = SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000),
            initialValue = emptySet(),
        )
}
```

## 37.10 Choose `SharingStarted` deliberately — `Eagerly`, `Lazily`, and `WhileSubscribed` are three different resource contracts.

> Why? `Eagerly` starts the upstream when the flow is created and never stops it:
> correct only when the upstream is cheap and the data must be fresh from
> process start. `Lazily` starts on the first subscriber and, once started,
> also never stops. `WhileSubscribed` starts on the first subscriber and stops
> `stopTimeoutMillis` after the last one leaves — the only option that releases
> the upstream. The `stopTimeoutMillis` parameter defaults to `0`, which tears
> down and rebuilds the upstream across even a momentary subscriber gap; a few
> seconds is the usual value when subscribers churn. A second parameter,
> `replayExpirationMillis`, defaults to `Long.MAX_VALUE`, so the replay cache
> survives the stop unless you say otherwise. **Suggestion.**

```kotlin
// bad — Eagerly on an expensive upstream: the websocket is open from process
// start, whether or not any screen is showing
val prices: StateFlow<Prices> = priceSocket()
    .stateIn(scope, SharingStarted.Eagerly, Prices.EMPTY)

// bad — WhileSubscribed() with the default zero timeout: rotating the screen
// closes and reopens the socket
val prices: StateFlow<Prices> = priceSocket()
    .stateIn(scope, SharingStarted.WhileSubscribed(), Prices.EMPTY)

// good — released when unobserved, tolerant of a brief resubscribe gap
val prices: StateFlow<Prices> = priceSocket()
    .stateIn(
        scope = scope,
        started = SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000),
        initialValue = Prices.EMPTY,
    )
```

## 37.11 Call `shareIn`/`stateIn` once, at a property, never inside a function that callers invoke repeatedly.

> Why? Each call creates a **new** hot flow with its own sharing coroutine in
> the given scope. Putting one inside a function body means every call leaks
> another upstream subscription into the scope, and callers who compare the
> returned flows for identity get different objects each time — so nothing is
> actually shared. The whole point of a hot flow is that there is exactly one.
> Assign it to a `val` (or a lazily-initialised property) and hand out that.
> **Suggestion.**

```kotlin
// bad — one new sharing coroutine per call; nothing is shared, and the scope
// accumulates upstreams
class FeedService(private val scope: CoroutineScope) {
    fun feed(): SharedFlow<Post> =
        rawFeed().shareIn(scope, SharingStarted.WhileSubscribed(5_000), replay = 0)
}

// good — one hot flow, created once
class FeedService(private val scope: CoroutineScope) {
    val feed: SharedFlow<Post> =
        rawFeed().shareIn(scope, SharingStarted.WhileSubscribed(5_000), replay = 0)
}

// good — per-key sharing when the stream genuinely varies, cached by key
class FeedService(private val scope: CoroutineScope) {
    private val byTopic = ConcurrentHashMap<TopicId, SharedFlow<Post>>()

    fun feed(topic: TopicId): SharedFlow<Post> = byTopic.computeIfAbsent(topic) {
        rawFeed(it).shareIn(scope, SharingStarted.WhileSubscribed(5_000), replay = 0)
    }
}
```

## 37.12 Remember that a hot flow never completes, so terminal operators that wait for completion will hang.

> Why? `StateFlow` and `SharedFlow` have no completion event. `toList()`,
> `count()`, `last()`, `reduce()`, and `fold()` all wait for one, so on a hot
> flow they never return — a hang with no exception and no log line. Only
> operators that terminate on their own terms are safe: `first()`,
> `firstOrNull()`, `take(n)`, or `collect` inside a coroutine you cancel. For a
> `StateFlow` specifically, reading `.value` is the direct way to get the
> current state without collecting at all. **Suggestion.**

```kotlin
// bad — never returns; a StateFlow has no completion
suspend fun snapshotAll(): List<Prices> = prices.toList()

// good — .value for the current state of a StateFlow
fun snapshot(): Prices = prices.value

// good — take(n) bounds the collection explicitly
suspend fun firstThree(): List<Prices> = prices.take(3).toList()
```

## 37.13 Never collect a hot flow in a scope that outlives the consumer.

> Why? `collect` on a hot flow returns only when its coroutine is cancelled, so
> the collecting coroutine lives exactly as long as its scope. Collect a
> long-lived service's `StateFlow` in a scope tied to the process and the
> consumer object can never be garbage-collected, its `collect` lambda keeps
> firing after the screen or request it belonged to is gone, and each new
> consumer adds another live collector. The scope must be the *consumer's*, and
> something must cancel it. `GlobalScope` is never that something. **Violation
> — enforced by `detekt/GlobalCoroutineUsage`** for the `GlobalScope` form
> specifically; the general lifetime mismatch is a **Suggestion**.

```kotlin
// bad — GlobalScope collection: the handler is retained forever, and closing
// the screen does not stop the work
class DetailScreen(private val service: PresenceService) {
    init {
        GlobalScope.launch { service.online.collect { render(it) } }
    }
}

// good — collected in a scope the screen owns and cancels
class DetailScreen(private val service: PresenceService) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    init {
        service.online.onEach { render(it) }.launchIn(scope)
    }

    fun close() {
        scope.cancel()
    }
}
```

## 37.14 Understand that a slow subscriber back-pressures a `SharedFlow` with `BufferOverflow.SUSPEND`.

> Why? With the default `SUSPEND` policy, `emit` does not return until there is
> buffer room for every current subscriber — so one collector doing slow I/O in
> its `collect` lambda stalls the producer and, with it, every other collector.
> This is the correct default (nothing is dropped) and a common production
> surprise. The fix is either to give the slow collector its own buffer, or to
> change the overflow policy and accept the loss explicitly. `StateFlow` never
> has this problem because it is conflated by construction: a slow collector
> simply skips intermediate values. **Suggestion.**

```kotlin
// bad — the archive writer's 200 ms round trip throttles the live UI collector
// on the same SharedFlow
scope.launch { events.collect { archive.write(it) } } // slow subscriber
scope.launch { events.collect { ui.render(it) } }     // runs at the archiver's pace

// good — the slow subscriber buffers on its own side
scope.launch { events.buffer(capacity = 256).collect { archive.write(it) } }
scope.launch { events.collect { ui.render(it) } }

// good — or the producer declares that dropping is acceptable
private val _events = MutableSharedFlow<Event>(
    extraBufferCapacity = 256,
    onBufferOverflow = BufferOverflow.DROP_OLDEST,
)
```

## 37.15 Drive optional upstream work from `subscriptionCount` rather than counting subscribers by hand.

> Why? `SharedFlow.subscriptionCount` is itself a `StateFlow<Int>`, so "start the
> expensive thing when someone is listening and stop it when nobody is" is an
> ordinary flow expression rather than a hand-maintained counter with its own
> races. Reach for it only when `SharingStarted.WhileSubscribed` (§37.10) does
> not already express what you need — it usually does, and the explicit counter
> is the more error-prone of the two. **Suggestion.**

```kotlin
// bad — a hand-maintained counter with a check-then-act race between the
// decrement and the shutdown
private var listeners = 0

fun subscribe() {
    if (listeners++ == 0) locationHardware.start()
}

fun unsubscribe() {
    if (--listeners == 0) locationHardware.stop()
}

// good — derived from the flow's own accounting
init {
    _locations.subscriptionCount
        .map { it > 0 }
        .distinctUntilChanged()
        .onEach { active -> if (active) locationHardware.start() else locationHardware.stop() }
        .launchIn(scope)
}
```

## 37.16 Treat `resetReplayCache` as an experimental escape hatch, not a design tool.

> Why? `MutableSharedFlow.resetReplayCache` carries `@ExperimentalCoroutinesApi`,
> and reaching for it is nearly always a sign that `replay` was set for the wrong
> reason (§37.7). Clearing the replay cache does nothing for subscribers that
> already received the value, so it does not make a replayed event
> "un-delivered"; it only changes what the *next* subscriber sees. If you find
> yourself resetting the cache to stop an event being re-delivered, the fix is
> `replay = 0`. **Suggestion.**

```kotlin
// bad — replay = 1 plus a reset, to simulate a one-shot event
@OptIn(ExperimentalCoroutinesApi::class)
fun consumeNavigation() {
    _navigation.resetReplayCache()
}

// good — the flow simply does not replay
private val _navigation = MutableSharedFlow<NavCommand>(extraBufferCapacity = 8)
val navigation: SharedFlow<NavCommand> = _navigation.asSharedFlow()
```

## 37.17 Do not apply operators to a `StateFlow` and expect the result to still be a `StateFlow`.

> Why? Every standard operator returns a plain cold `Flow`. `state.map { ... }`
> is *cold*: it has no `.value`, it re-runs the mapping per collector, and it
> loses the conflation and the always-has-a-value guarantee that the caller was
> relying on. If a derived value must remain state, convert it back with
> `stateIn` — supplying an `initialValue`, since the mapping is not applied to
> the source's current value for free. The same holds for `combine` over two
> `StateFlow`s. **Suggestion.**

```kotlin
// bad — the declared type is a lie only until someone needs .value; this is a
// cold Flow with none of StateFlow's guarantees
val userName: Flow<String> = user.map { it.displayName }

// good — converted back to state, with the initial value stated
val userName: StateFlow<String> = user
    .map { it.displayName }
    .stateIn(
        scope = scope,
        started = SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000),
        initialValue = user.value.displayName,
    )
```

## 37.18 Give a hot flow's scope a `SupervisorJob` and an explicit cancellation point.

> Why? A hot flow's sharing coroutine lives in the scope you hand it. With a
> plain `Job`, one failing upstream cancels the scope and takes every other hot
> flow sharing it down with it — silently, because there is no collector to
> observe the failure. A `SupervisorJob` isolates siblings. Just as important,
> the object that constructs the scope must be the object that cancels it: a
> scope created in a constructor and never cancelled is the leak this whole
> chapter is about. See
> [Chapter 33, Coroutine Fundamentals](33-coroutine-fundamentals.md) for the
> structured-concurrency rules this specialises. **Suggestion.**

```kotlin
// bad — plain Job, and nothing ever cancels the scope
class Dashboard {
    private val scope = CoroutineScope(Dispatchers.Default)

    val alerts: SharedFlow<Alert> =
        alertStream().shareIn(scope, SharingStarted.Eagerly, replay = 0)
    val metrics: StateFlow<Metrics> =
        metricStream().stateIn(scope, SharingStarted.Eagerly, Metrics.EMPTY)
}

// good — supervised siblings, and a close() the owner is required to call
class Dashboard : AutoCloseable {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    val alerts: SharedFlow<Alert> = alertStream()
        .shareIn(scope, SharingStarted.WhileSubscribed(5_000), replay = 0)
    val metrics: StateFlow<Metrics> = metricStream()
        .stateIn(scope, SharingStarted.WhileSubscribed(5_000), Metrics.EMPTY)

    override fun close() {
        scope.cancel()
    }
}
```
