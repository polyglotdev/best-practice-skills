<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 38. Channels & `select`

A `Channel<E>` is the low-level communication primitive coroutines were built
on: a hot, concurrency-safe queue with suspending `send` and `receive`. Unlike a
`Flow`, which is a *recipe* re-executed per collector
([Chapter 36](36-flow.md)), and unlike a `SharedFlow`, which broadcasts each
value to every subscriber ([Chapter 37](37-stateflow-and-sharedflow.md)), a
channel delivers each element to **exactly one** receiver, once. That single
property makes it the right tool for work distribution and the wrong tool for
almost everything people reach for it for.

The guidance in the
[channels documentation](https://kotlinlang.org/docs/channels.html) is
unambiguous about the ordering: `Flow` is the default, and a `Channel` is the
exception you justify. This chapter covers capacities and overflow policies,
`send`/`receive` semantics and their non-suspending siblings, who closes a
channel and how, iteration, the `produce` builder, fan-out and fan-in, the
[`select`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.selects/select.html)
expression, conversion to and from `Flow`, and the leak patterns that make
channels the hardest coroutine primitive to review.

Two things are deferred. **Hot-flow lifetime and scope ownership** are
[Chapter 37, §37.1 and §37.18](37-stateflow-and-sharedflow.md) — everything said
there about a leaked scope applies verbatim to a channel-producing coroutine.
**Cancellation semantics** are
[Chapter 35, Cancellation & Timeouts](35-cancellation-and-timeouts.md); this
chapter only covers what cancellation does to a channel's two ends.

**Tool alignment:** no detekt rule reasons about channel lifetime, so nearly
every rule here is a **Suggestion**. Two adjacent checks do fire on code that
often appears alongside channel misuse: `detekt/GlobalCoroutineUsage` on the
scope that owns a leaked producer, and `detekt/SuspendFunInFinallySection` on
the *suspending* cleanup hazard noted in §38.12 (the non-suspending
`cancel()` in that section's sample does not trip it). The library's own opt-in
markers matter more here
than in most chapters — `produce` and `actor` are both annotated, and this
chapter names the annotation each time.

## 38.1 Default to `Flow`; justify a `Channel`.

> Why? The [channels documentation](https://kotlinlang.org/docs/channels.html)
> positions channels as the primitive underneath the higher-level API, and
> almost every producer/consumer problem is better served by a cold `Flow`
> (per-collector lifetime, operators, structured cancellation) or a `SharedFlow`
> (broadcast, replay, subscription accounting). A `Channel` gives up all of
> that in exchange for one thing: each element goes to exactly one receiver. If
> you cannot name that requirement, you want a flow. **Suggestion.**

```kotlin
// bad — a channel used as a plain stream: no operators, manual closing, and a
// second consumer would silently steal half the elements
fun events(): ReceiveChannel<Event> {
    val channel = Channel<Event>(Channel.BUFFERED)
    scope.launch {
        source.forEach { channel.send(it) }
        channel.close()
    }
    return channel
}

// good — a cold flow: no lifetime to manage, operators available, every
// collector gets every element
fun events(): Flow<Event> = flow {
    source.forEach { emit(it) }
}

// good — a channel where "exactly one worker takes each job" is the point
private val jobs = Channel<RenderJob>(capacity = 64)
```

## 38.2 Choose the capacity deliberately; `RENDEZVOUS` is the default and it means "no buffer".

> Why? `Channel()` with no argument is `Channel.RENDEZVOUS`, documented as "the
> zero buffer capacity" — `send` suspends until a receiver arrives, and vice
> versa. That is a synchronisation point, not a queue, and it is the correct
> default because it back-pressures the producer. The alternatives each encode a
> different contract: `BUFFERED` uses the default buffer size (64 on the JVM
> under the default `SUSPEND` overflow strategy, overridable with the
> `kotlinx.coroutines.channels.defaultBuffer` system property, and 1 if a
> different `BufferOverflow` is supplied), `UNLIMITED` never suspends the sender
> and therefore never
> back-pressures — an unbounded memory risk — and `CONFLATED` keeps only the most
> recent element. Writing `Channel(Channel.UNLIMITED)` to make a hang go away
> converts a visible deadlock into an invisible leak. **Suggestion.**

```kotlin
// bad — UNLIMITED chosen to stop send() from suspending; a fast producer now
// grows the heap without bound and the back-pressure signal is gone
private val ingest = Channel<Record>(Channel.UNLIMITED)

// good — a bounded buffer states how much slack the pipeline tolerates
private val ingest = Channel<Record>(capacity = 256)

// good — CONFLATED where only the freshest value matters
private val latestPosition = Channel<Position>(Channel.CONFLATED)
```

## 38.3 Pair a non-`SUSPEND` `onBufferOverflow` with a capacity, and say what you are dropping.

> Why? `Channel(capacity, onBufferOverflow, onUndeliveredElement)` takes a
> `BufferOverflow` of `SUSPEND` (the default), `DROP_OLDEST`, or `DROP_LATEST`.
> The two dropping policies silently discard data, which is fine for a telemetry
> sample and a defect for a payment instruction. Because the loss is invisible at
> the call site — `send` simply returns — the choice belongs in a named constant
> or a comment stating what is acceptable to lose. Note also that `CONFLATED` is
> documented as "a single-element buffer with conflating behavior" — the same
> effect as `capacity = 1` with `DROP_OLDEST` — so pick one spelling rather than
> writing both. **Suggestion.**

```kotlin
// bad — data silently dropped, with nothing at the declaration to say so
private val samples = Channel<Sample>(16, BufferOverflow.DROP_OLDEST)

// good — the policy is named and the loss is documented
/** Newest-wins: gauge samples older than the last [SAMPLE_BUFFER] are not worth keeping. */
private val samples = Channel<Sample>(
    capacity = SAMPLE_BUFFER,
    onBufferOverflow = BufferOverflow.DROP_OLDEST,
)

// good — the default when nothing may be lost
private val payments = Channel<PaymentInstruction>(capacity = 64) // SUSPEND
```

## 38.4 Use `send`/`receive` when back-pressure is wanted, and never discard the `ChannelResult` from `trySend`/`tryReceive`.

> Why? `send` and `receive` suspend, which is how a channel communicates
> back-pressure and closure. `trySend` returns a
> `ChannelResult<Unit>` — "successful result when the element was added" or a
> "failed result if the channel is closed" or full — and `tryReceive` returns a
> `ChannelResult<E>`. Ignoring that result turns a full or closed channel into a
> silent no-op, which is the single most common channel bug. If you are calling
> `trySend` because you are not in a coroutine, handle the failure; if you are in
> a coroutine, call `send`. **Suggestion.**

```kotlin
// bad — the result is discarded, so a full or closed channel drops the command
// with no trace
fun enqueue(command: Command) {
    commands.trySend(command)
}

// good — the failure is a first-class outcome
fun enqueue(command: Command): Boolean =
    commands.trySend(command)
        .onFailure { cause -> logger.warn(cause) { "command queue rejected $command" } }
        .isSuccess

// good — inside a coroutine, suspend instead of polling
suspend fun enqueueBlocking(command: Command) {
    commands.send(command)
}
```

## 38.5 The sender closes the channel, and closes it exactly once.

> Why? `close()` is on `SendChannel`, not `ReceiveChannel`, and that is the
> design: only the producer knows there is no more data. A receiver that closes
> is asserting something it cannot know. Closing signals normal completion —
> pending elements are still delivered, and the receiving side sees the end only
> after draining. Sending to an already-closed channel throws
> `ClosedSendChannelException` (a subclass of `IllegalStateException`, precisely
> because it indicates a programmer error), so two producers racing to close is a
> crash, not a benign duplicate. **Suggestion.**

```kotlin
// bad — the consumer closes, so a still-running producer crashes with
// ClosedSendChannelException
launch {
    for (record in records) {
        process(record)
        if (record.isTerminal) {
            records.close() // not the receiver's call to make
        }
    }
}

// good — the producer owns the close, in a finally so it happens on failure too
launch {
    try {
        source.forEach { records.send(it) }
    } finally {
        records.close()
    }
}
```

## 38.6 Close with a cause when the producer fails, so the failure reaches the consumer.

> Why? `close(cause: Throwable?)` propagates the cause to the receiving side: a
> `receive()` on a channel closed with a cause throws that cause rather than
> `ClosedReceiveChannelException`. A plain `close()` after a producer failure
> looks to the consumer exactly like normal completion, so a truncated result set
> is processed as if it were the whole set — a silent correctness bug rather than
> a loud failure. **Suggestion.**

```kotlin
// bad — the consumer sees an ordinary end-of-stream and commits a partial batch
launch {
    try {
        source.forEach { records.send(it) }
    } catch (e: IOException) {
        logger.error(e) { "source failed" }
    } finally {
        records.close()
    }
}

// good — the consumer's receive() rethrows the cause and the batch is aborted
launch {
    var failure: Throwable? = null
    try {
        source.forEach { records.send(it) }
    } catch (e: IOException) {
        failure = e
    } finally {
        records.close(failure)
    }
}
```

## 38.7 Iterate with `for (x in channel)` when the channel outlives the loop, and `consumeEach` when it does not.

> Why? These are not synonyms. A `for` loop over a `ReceiveChannel` reads until
> the channel is closed and leaves it open. `consumeEach` is documented as
> performing "the given action for each received element and cancels the channel
> afterward" — including when the action throws or returns early, in which case
> "that exception will be used for cancelling the channel and rethrown." That
> cancellation is what you want for a single-consumer channel you are finished
> with, and precisely what you must not do in a fan-out worker, where cancelling
> the shared channel starves every sibling. The `consumeEach` docs say so
> directly: "when the channel does not need to be closed after iterating over its
> elements, a regular `for` loop should be used instead." **Suggestion.**

```kotlin
// bad — worker 1 finishing (or failing) cancels the shared channel, so workers
// 2..N stop receiving
repeat(workerCount) {
    launch { jobs.consumeEach { render(it) } }
}

// good — a for loop leaves the shared channel alone
repeat(workerCount) {
    launch {
        for (job in jobs) {
            render(job)
        }
    }
}

// good — consumeEach for a single-consumer channel that should die with the loop
launch { results.consumeEach { report(it) } }
```

## 38.8 Prefer `produce` to a hand-rolled `Channel` plus `launch` — and note it is `@ExperimentalCoroutinesApi`.

> Why? `produce` binds a `ReceiveChannel` to the coroutine that fills it: the
> channel is closed automatically when the block completes, and cancelling the
> returned channel cancels the producer. The hand-rolled equivalent has to close
> in a `finally` (§38.5), has to remember to cancel the producing `Job`, and
> leaks both if either is forgotten. The cost is the annotation: `produce` is
> `@ExperimentalCoroutinesApi`, with the documented caveat that "behaviour of
> producers that work as children in a parent scope with respect to cancellation
> and error handling may change in the future." Opt in explicitly.
> **Suggestion.**

```kotlin
// bad — three separate things to get right: the close, the Job, and the failure
// path; forgetting any one leaks the producer
fun CoroutineScope.numbers(): ReceiveChannel<Int> {
    val channel = Channel<Int>()
    launch {
        for (i in 1..100) channel.send(i)
        channel.close()
    }
    return channel
}

// good — the builder owns closing and cancellation
@OptIn(ExperimentalCoroutinesApi::class)
fun CoroutineScope.numbers(): ReceiveChannel<Int> = produce {
    for (i in 1..100) {
        send(i)
    }
}
```

## 38.9 Fan out by giving many receivers one channel, and fan in by giving many senders one channel — but close only once.

> Why? Fan-out falls out of the delivery guarantee: N workers reading one channel
> each take a disjoint subset of the elements, which is a work queue with no
> partitioning logic to write. Fan-in is the mirror image and has one hazard: `N`
> producers means `N` candidates to call `close()`, and the second call is a
> no-op while a `send` racing it throws. Close from the coordinator after all
> producers have joined, not from inside a producer. **Suggestion.**

```kotlin
// bad — each producer closes when it finishes, so the first one to finish ends
// the channel and the rest crash on send
shards.forEach { shard ->
    launch {
        shard.records().collect { merged.send(it) }
        merged.close()
    }
}

// good — the coordinator closes once, after every producer has completed
launch {
    coroutineScope {
        shards.forEach { shard ->
            launch { shard.records().collect { merged.send(it) } }
        }
    } // returns only when all children have finished
    merged.close()
}
```

## 38.10 Chain channels into a pipeline only when each stage needs its own concurrency.

> Why? A pipeline of `produce` stages is the classic channel idiom, and it is
> genuinely useful when stages run at different rates on different dispatchers.
> But `Flow` expresses the same pipeline declaratively, with `buffer` (§36.13)
> supplying exactly the stage-to-stage decoupling the channels were providing —
> and without the closing, cancellation, and leak obligations. Reach for a
> channel pipeline when a stage must fan out to several workers or must be fed by
> several producers; otherwise use a flow. **Suggestion.**

```kotlin
// bad — a two-stage channel pipeline that a flow expresses in three lines,
// with two channels and two Jobs to keep alive
@OptIn(ExperimentalCoroutinesApi::class)
fun CoroutineScope.report(ids: List<DocId>): ReceiveChannel<Report> {
    val fetched = produce { ids.forEach { send(store.fetch(it)) } }
    return produce { for (doc in fetched) send(analyse(doc)) }
}

// good — a flow, with buffer decoupling the two stages
fun report(ids: List<DocId>): Flow<Report> =
    ids.asFlow()
        .map { store.fetch(it) }
        .buffer(capacity = 32)
        .map { analyse(it) }

// good — a channel pipeline when a stage genuinely fans out to workers
@OptIn(ExperimentalCoroutinesApi::class)
fun CoroutineScope.analyseInParallel(docs: ReceiveChannel<Doc>): ReceiveChannel<Report> {
    val out = Channel<Report>(capacity = 32)
    repeat(WORKER_COUNT) {
        launch {
            for (doc in docs) {
                out.send(analyse(doc))
            }
        }
    }
    return out
}
```

## 38.11 Convert with `consumeAsFlow` for a single collector and `receiveAsFlow` for several.

> Why? The two differ in exactly one documented respect, and it is a runtime
> failure if you pick wrong. `consumeAsFlow` produces a flow that "can be
> collected just once and throws `IllegalStateException` when trying to collect
> it more than once", and it cancels the channel when collection ends.
> `receiveAsFlow` "supports multiple collectors of the resulting flow" — with the
> channel's own semantics preserved, so those collectors *split* the elements
> rather than each receiving all of them. Neither one turns a channel into a
> broadcast: for that you want a `SharedFlow`
> ([Chapter 37](37-stateflow-and-sharedflow.md)). **Suggestion.**

```kotlin
// bad — consumeAsFlow collected twice; the second collect throws
// IllegalStateException at runtime
val results = channel.consumeAsFlow()
launch { results.collect { audit(it) } }
launch { results.collect { render(it) } } // IllegalStateException

// good — receiveAsFlow when several coroutines share the work
val results = channel.receiveAsFlow()
launch { results.collect { worker(1).handle(it) } }
launch { results.collect { worker(2).handle(it) } }

// good — consumeAsFlow for the single-consumer case it was designed for
channel.consumeAsFlow().collect { report(it) }
```

## 38.12 Never leave a channel unconsumed — a suspended sender holds its coroutine forever.

> Why? With any bounded capacity, `send` suspends when the buffer is full. If the
> only receiver goes away — the consumer returned early, its scope was cancelled
> and the channel was not, an exception unwound past the loop — the producer stays
> suspended inside `send` for the lifetime of its scope. It holds every reference
> in its frame, and nothing in the runtime reports it. Cancel the channel on the
> consumer's exit path (`cancel()`, not `close()`, since the receiver is
> abandoning undelivered elements), or use `produce`, whose cancellation is wired
> for you (§38.8). Note that cleanup in a `finally` must not itself suspend
> without `withContext(NonCancellable)` — see
> [Chapter 35](35-cancellation-and-timeouts.md).
> **Suggestion** for the leak; the `finally` hazard is a **Violation — enforced
> by `detekt/SuspendFunInFinallySection`.**

```kotlin
// bad — the consumer returns on the first bad record and abandons the channel;
// the producer stays suspended in send() until the whole scope dies
suspend fun ingest(records: ReceiveChannel<Record>) {
    for (record in records) {
        if (!record.isValid) {
            return // producer is now stuck
        }
        store(record)
    }
}

// good — cancel the channel on every exit path
suspend fun ingest(records: ReceiveChannel<Record>) {
    try {
        for (record in records) {
            if (!record.isValid) {
                return
            }
            store(record)
        }
    } finally {
        records.cancel()
    }
}
```

## 38.13 Supply `onUndeliveredElement` when an element owns a resource.

> Why? An element that is sent but never received — because the channel was
> cancelled, or closed with elements still buffered — simply vanishes. If that
> element is a file handle, a pooled connection, or a reference-counted buffer,
> the resource leaks. `Channel(capacity, onBufferOverflow, onUndeliveredElement)`
> takes a callback invoked for exactly those elements, which is the only hook
> that fires on the abandonment paths. For plain data it is unnecessary; for
> anything closeable it is mandatory. **Suggestion.**

```kotlin
// bad — cancelling the channel abandons every buffered connection without
// returning it to the pool
private val leased = Channel<PooledConnection>(capacity = 32)

// good — abandoned elements are released
private val leased = Channel<PooledConnection>(
    capacity = 32,
    onUndeliveredElement = { connection -> connection.release() },
)
```

## 38.14 Use `select` only to race genuinely independent suspending sources, and treat it as a last resort for readability.

> Why? `select` waits on several clauses at once and resumes with the first that
> becomes available — `onReceive` / `onReceiveCatching` on a `ReceiveChannel`,
> `onSend` on a `SendChannel`, `onAwait` on a `Deferred`, `onJoin` on a `Job`.
> It is the only construct that expresses "whichever of these happens first", and
> it is also the least readable thing in the coroutines API: the clauses are
> registered, not called, so ordinary control-flow intuition does not apply. When
> a `merge` of flows, a `withTimeout`, or an `awaitAll` says the same thing, say
> it that way instead. **Suggestion.**

```kotlin
// bad — select used where a plain timeout is what is meant
@OptIn(ExperimentalCoroutinesApi::class)
suspend fun fetchOrGiveUp(): Response? = coroutineScope {
    val request = async { client.fetch() }
    select {
        request.onAwait { it }
        onTimeout(2_000) { null }
    }
}

// good — withTimeoutOrNull states the intent directly
suspend fun fetchOrGiveUp(): Response? =
    withTimeoutOrNull(2.seconds) { client.fetch() }

// good — select where the race is the point: two channels, first one wins
suspend fun nextCommand(local: ReceiveChannel<Command>, remote: ReceiveChannel<Command>): Command =
    select {
        local.onReceive { it }
        remote.onReceive { it }
    }
```

## 38.15 Remember that `select` is biased to the first clause, and reach for `selectUnbiased` when fairness matters.

> Why? The `select` documentation states that it "is biased to the first clause"
> — when several clauses are ready simultaneously, the first one in source order
> is chosen. That is deterministic and often desirable (a shutdown signal should
> outrank a work item), but it also means a permanently-ready first clause
> starves everything below it. `selectUnbiased` randomises the order for exactly
> this case. Deciding which you want is part of writing the `select`, not an
> optimisation to revisit. **Suggestion.**

```kotlin
// bad — `fast` is never empty, so being first it wins every race and
// `slow.onReceive` is never selected
select {
    fast.onReceive { handle(it) } // always ready
    slow.onReceive { handle(it) } // starved
}

// good — deliberate bias: shutdown outranks work
select {
    shutdown.onReceive { throw CancellationException("shutting down") }
    work.onReceive { handle(it) }
}

// good — randomised when neither source should starve the other
selectUnbiased {
    fast.onReceive { handle(it) }
    slow.onReceive { handle(it) }
}
```

## 38.16 `onTimeout` is `@ExperimentalCoroutinesApi` — prefer wrapping the whole `select` in `withTimeoutOrNull`.

> Why? `SelectBuilder.onTimeout` carries `@ExperimentalCoroutinesApi` and its own
> documentation notes it "may be replaced [with] light-weight timer/timeout
> channels in the future". Wrapping the `select` in `withTimeoutOrNull` uses only
> stable API, composes with the surrounding cancellation machinery, and reads as
> the timeout it is. Reserve `onTimeout` for the case where the timeout must
> compete with the other clauses on equal terms rather than bound the whole
> expression. **Suggestion.**

```kotlin
// bad — unflagged experimental API inside a hot loop
suspend fun nextOrIdle(work: ReceiveChannel<Task>): Task? = select {
    work.onReceive { it }
    onTimeout(500) { null }
}

// good — stable API, same behaviour, and the timeout bounds the whole select
suspend fun nextOrIdle(work: ReceiveChannel<Task>): Task? =
    withTimeoutOrNull(500.milliseconds) {
        select { work.onReceive { it } }
    }
```

## 38.17 Use a channel for actor-like state ownership rather than sharing mutable state behind a lock.

> Why? Confining mutable state to a single coroutine and feeding it commands
> through a channel removes an entire class of concurrency bug: there is one
> writer, in one coroutine, processing one message at a time, so no lock is
> needed and no interleaving is possible. This is the strongest remaining case
> for a `Channel` over a `Flow`, because it depends on exactly-one-consumer
> delivery. Note that the dedicated `actor` builder is annotated
> `@ObsoleteCoroutinesApi` — its documentation says "this API will become
> obsolete in future updates with introduction of complex actors" — so build the
> pattern from a plain `Channel` plus a `launch` rather than from `actor`.
> **Suggestion.**

```kotlin
// bad — shared mutable state guarded by a lock the caller must remember
class Counters {
    private val lock = ReentrantLock()
    private val values = mutableMapOf<String, Long>()

    fun increment(name: String) = lock.withLock { values[name] = (values[name] ?: 0L) + 1L }
    fun snapshot(): Map<String, Long> = lock.withLock { values.toMap() }
}

// good — one owning coroutine, commands over a channel, no lock
sealed interface CounterCommand {
    data class Increment(val name: String) : CounterCommand
    data class Snapshot(val reply: CompletableDeferred<Map<String, Long>>) : CounterCommand
}

fun CoroutineScope.counters(): SendChannel<CounterCommand> {
    val commands = Channel<CounterCommand>(capacity = 64)
    launch {
        val values = mutableMapOf<String, Long>()
        for (command in commands) {
            when (command) {
                is CounterCommand.Increment ->
                    values[command.name] = (values[command.name] ?: 0L) + 1L
                is CounterCommand.Snapshot -> command.reply.complete(values.toMap())
            }
        }
    }
    return commands
}
```

## 38.18 Do not model state with a channel — that is what `StateFlow` is for.

> Why? A channel has no current value: a consumer that arrives late gets whatever
> is sent *next*, not what is true *now*. Simulating a current value with
> `Channel.CONFLATED` gets you the last element, once, to one receiver — and then
> the value is gone, so a second reader sees nothing. `StateFlow` exists exactly
> to hold "the current value, readable by anyone, at any time"
> ([Chapter 37, §37.2](37-stateflow-and-sharedflow.md)). **Suggestion.**

```kotlin
// bad — a CONFLATED channel used as state; the first reader consumes the value
// and every later reader blocks until the next update
private val connectionState = Channel<ConnectionState>(Channel.CONFLATED)

suspend fun current(): ConnectionState = connectionState.receive()

// good — state is a StateFlow; every reader sees the current value immediately
private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Idle)
val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

fun current(): ConnectionState = _connectionState.value
```
