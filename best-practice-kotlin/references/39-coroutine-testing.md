<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 39. Coroutine Testing

A coroutine test has one property no other test has: the code under test can
finish *after* the assertions run. Every failure mode in this chapter is a
variation on that single fact. A test that launches work, asserts, and passes
has proved nothing unless something made the launched work actually execute
first, and the default `TestDispatcher` deliberately does not.

The `kotlinx-coroutines-test` module exists to make that deterministic. It
replaces real time with a virtual clock, gives you explicit control over when
queued work runs, and fails the test if a coroutine is left dangling. This
chapter is about using it correctly, drawing on the
[kotlinx-coroutines-test API reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/)
and the
[module README](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-test/README.md).

Three neighbouring topics are deferred. **Dispatcher injection** — why a
`CoroutineDispatcher` belongs in a constructor rather than baked into a
`withContext` call — is [Chapter 34, Dispatchers & Coroutine
Context](34-dispatchers-and-context.md); §39.12 is the testing consequence of
that rule, not a restatement of it. **What cancellation actually does** to a
running coroutine is [Chapter 35, Cancellation &
Timeouts](35-cancellation-and-timeouts.md); §39.17 only covers how to assert
it. **General test structure** — JUnit 5 lifecycle, MockK basics, fixture
design, and the backtick naming convention from [Kotlin coding conventions:
names for test
methods](https://kotlinlang.org/docs/coding-conventions.html#names-for-test-methods)
— is [Chapter 32, Testing](32-testing.md). The full catalogue of coroutine
failures that are *not* test-specific is [Chapter 40, Coroutine
Anti-patterns](40-coroutine-anti-patterns.md).

**Tool alignment:** detekt's `CoroutineLaunchedInTestWithoutRunTest`,
`InjectDispatcher`, `SleepInsteadOfDelay`, and `SuspendFunSwallowedCancellation`
back rules below, and all four are enabled in this repo's
`config/detekt/detekt.yml`. Rules a named check actually enforces are marked
**Violation**; the rest are **Suggestion**.

## 39.1 Use `runTest` as the body of every test that touches `suspend` code.

> Why? `runTest` installs a `TestScope`, a virtual clock, and a
> single-threaded `TestDispatcher`, and it waits for every child coroutine of
> the test scope before returning. Launching a coroutine from a plain `@Test`
> function instead gives you a race between the coroutine and the assertions,
> which the assertions usually win. The
> [`runTest` reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html)
> describes it as running "on a single thread, unless other
> `CoroutineDispatcher` are used for child coroutines", and states that
> "child coroutines are not executed in parallel to the test body".
> **Violation — enforced by `detekt/CoroutineLaunchedInTestWithoutRunTest`.**

```kotlin
// bad — the launched coroutine races the assertion, on a scope nothing owns
@Test
fun `records the payment`() {
    val scope = CoroutineScope(Dispatchers.Default)
    scope.launch { ledger.record(payment) }
    assertEquals(1, ledger.entries().size) // flaky: usually fails, sometimes not
}

// good
@Test
fun `records the payment`() = runTest {
    ledger.record(payment)
    assertEquals(1, ledger.entries().size)
}
```

## 39.2 Never use `runBlocking` for a test that exercises code containing `delay` or a timeout.

> Why? `runBlocking` runs on real time. A retry policy that backs off for one,
> two, and four seconds costs seven real seconds per test run, and a
> `withTimeout(30.seconds)` costs thirty. `runTest` skips those delays against
> a virtual clock — the
> [README](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-test/README.md)
> states that "the calls to `delay` are automatically skipped, preserving the
> relative execution order of the tasks" — so the same test finishes in
> milliseconds *and* lets you assert on elapsed virtual time (§39.10).
> **Suggestion.**

```kotlin
// bad — seven real seconds of wall clock, every CI run, forever
@Test
fun `retries three times with backoff`() = runBlocking {
    val response = client.fetchWithRetry(url) // delays 1s, then 2s, then 4s
    assertEquals(Response.Ok, response)
}

// good — delays are skipped, and the backoff schedule becomes assertable
@Test
fun `retries three times with backoff`() = runTest {
    val response = client.fetchWithRetry(url)
    assertEquals(Response.Ok, response)
    assertEquals(7_000L, currentTime)
}
```

## 39.3 Make `runTest` the whole test body, with an expression-bodied test function.

> Why? `runTest` returns a `TestResult`. Wrapping it in a block body discards
> that value and, worse, creates a region *after* the closing brace where
> statements run outside the test coroutine — outside the virtual clock,
> outside the leak check, and outside the timeout. A reader scanning the file
> cannot tell which of those statements are inside the coroutine and which are
> not. The expression body makes it unambiguous. **Suggestion.**

```kotlin
// bad — the assertion runs after runTest has already completed and torn down
@Test
fun `settles the invoice`() {
    runTest {
        billing.settle(invoice)
    }
    assertEquals(InvoiceStatus.SETTLED, invoice.status) // outside the test scope
}

// good
@Test
fun `settles the invoice`() = runTest {
    billing.settle(invoice)
    assertEquals(InvoiceStatus.SETTLED, invoice.status)
}
```

## 39.4 Drain the scheduler before asserting on the effect of a `launch`.

> Why? This is the single most common false pass in coroutine testing. The
> default `StandardTestDispatcher` queues rather than executes: its
> [reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-standard-test-dispatcher.html)
> says `launch` and `async` blocks "will not be entered immediately". A test
> that asserts immediately after `launch` observes the world exactly as it was
> before the coroutine started, so any assertion that happens to describe the
> *initial* state goes green and stays green even when the production code is
> deleted. **Suggestion** — no tool can distinguish a vacuous assertion from a
> real one.

```kotlin
// bad — the launched coroutine is queued, never run; both assertions describe
// the pre-checkout world and would still pass with an empty `submit`
@Test
fun `submitting an order charges the card`() = runTest {
    launch { checkout.submit(order) }
    assertEquals(0, gateway.chargeCount)
    assertNull(orders.byId(order.id))
}

// good — run everything pending, then assert the effect you actually want
@Test
fun `submitting an order charges the card`() = runTest {
    launch { checkout.submit(order) }
    advanceUntilIdle()
    assertEquals(1, gateway.chargeCount)
    assertEquals(OrderStatus.PAID, orders.byId(order.id)?.status)
}
```

## 39.5 Default to `StandardTestDispatcher`; do not reach for `UnconfinedTestDispatcher` to avoid thinking about advancement.

> Why? `StandardTestDispatcher` is what `runTest` installs when you pass no
> context, and its queueing behaviour is a feature: it forces the test to state
> when queued work runs, which is exactly the ordering question a concurrency
> bug hides in. `UnconfinedTestDispatcher` makes that question disappear, and
> its own
> [reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-unconfined-test-dispatcher.html)
> warns that "like `Dispatchers.Unconfined`, this is a specific dispatcher with
> execution order guarantees that are unusual and not shared by most other
> dispatchers, so it can only be used reliably for testing functionality, not
> the specific order of actions". A test that passes only under `Unconfined`
> is a test whose subject has an ordering bug. **Suggestion.**

```kotlin
// bad — Unconfined chosen so the author never has to call advanceUntilIdle;
// the test now exercises an execution order production will never produce
@Test
fun `applies discounts before tax`() = runTest(UnconfinedTestDispatcher()) {
    launch { pricing.recalculate(cart) }
    assertEquals(Money.of("90.00"), cart.total)
}

// good — the default dispatcher, with the advancement stated
@Test
fun `applies discounts before tax`() = runTest {
    launch { pricing.recalculate(cart) }
    advanceUntilIdle()
    assertEquals(Money.of("90.00"), cart.total)
}
```

## 39.6 Use `UnconfinedTestDispatcher` only where eager entry is the thing under test — typically to subscribe a collector before an emission.

> Why? There is one case `StandardTestDispatcher` cannot express cleanly: a hot
> flow with no replay drops anything emitted before a subscriber exists, and a
> queued collector is not yet a subscriber. `UnconfinedTestDispatcher` "ensures
> `launch` and `async` blocks at the top level of `runTest` are entered
> eagerly", which is precisely the guarantee you need. Reach for it here and
> nowhere else, and pass the test's own scheduler so the clock stays shared
> (§39.14). **Suggestion.**

```kotlin
// bad — the collector is queued, not subscribed, so `emit` drops the value
// and the assertion fails for a reason that has nothing to do with the code
@Test
fun `delivers to an active subscriber`() = runTest {
    val events = MutableSharedFlow<String>()
    val seen = mutableListOf<String>()
    backgroundScope.launch { events.collect { seen += it } }
    events.emit("created")
    assertEquals(listOf("created"), seen)
}

// good — eager entry makes the collector a subscriber before the emission
@Test
fun `delivers to an active subscriber`() = runTest {
    val events = MutableSharedFlow<String>()
    val seen = mutableListOf<String>()
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        events.collect { seen += it }
    }
    events.emit("created")
    assertEquals(listOf("created"), seen)
}
```

## 39.7 Launch anything that never completes into `backgroundScope`, not the test scope.

> Why? `runTest` waits for every child of the test scope. A collector on a
> `StateFlow`, a polling loop, or a channel consumer never completes, so the
> test hangs until the sixty-second default timeout fires and reports an
> `AssertionError` that names nothing useful. `TestScope.backgroundScope`
> exists for exactly this: its
> [reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-scope/background-scope.html)
> describes "a scope for background work" that "is automatically cancelled
> when the test finishes", and notes that `advanceUntilIdle` "will stop
> advancing the virtual time once only the coroutines in this scope are left
> unprocessed".
> **Suggestion.**

```kotlin
// bad — the assertion passes, and then the collector, a child of the test
// scope, never completes: runTest blocks for 60 seconds and fails with a
// timeout rather than reporting the green assertion
@Test
fun `exposes the running total`() = runTest {
    val seen = mutableListOf<Int>()
    launch(UnconfinedTestDispatcher(testScheduler)) {
        basket.total.collect { seen += it }
    }
    basket.add(item)
    advanceUntilIdle()
    assertEquals(listOf(0, 1), seen)
}

// good — backgroundScope coroutines are cancelled when the test body ends
@Test
fun `exposes the running total`() = runTest {
    val seen = mutableListOf<Int>()
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        basket.total.collect { seen += it }
    }
    basket.add(item)
    advanceUntilIdle()
    assertEquals(listOf(0, 1), seen)
}
```

## 39.8 Advance the clock with `advanceUntilIdle`, `advanceTimeBy`, or `runCurrent` — never with `delay` in the test body.

> Why? Each of the three says something different and says it precisely:
> `runCurrent()` runs what is due *now* without moving the clock,
> `advanceTimeBy(d)` moves the clock by a stated amount, and
> `advanceUntilIdle()` runs everything pending. A bare `delay(100)` in the test
> body says none of those — it is a guess that happens to be large enough
> today, it silently moves `currentTime` and so invalidates any later time
> assertion, and it re-breaks the moment someone adds an internal delay longer
> than the guess. **Suggestion.**

```kotlin
// bad — 100 is a magic number chosen by trial; it also advances the clock,
// so a later `assertEquals(5_000L, currentTime)` now reads 5_100
@Test
fun `refreshes the cache`() = runTest {
    launch { cache.refresh() }
    delay(100)
    assertTrue(cache.isFresh)
}

// good — states the intent: run everything that is pending
@Test
fun `refreshes the cache`() = runTest {
    launch { cache.refresh() }
    advanceUntilIdle()
    assertTrue(cache.isFresh)
}
```

## 39.9 Remember that `advanceTimeBy` is half-open: it does not run the task scheduled at exactly the target time.

> Why? The
> [`advanceTimeBy` reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-coroutine-scheduler/advance-time-by.html)
> is explicit that it runs "the tasks scheduled for
> `currentTime()..<currentTime() + delayTimeMillis`" — the upper bound is
> exclusive. A `delay(1_000)` resumes at exactly 1000, so `advanceTimeBy(1_000)`
> moves the clock to 1000 and leaves that continuation unrun. This produces the
> most confusing failure in the whole module: the clock reads the value you
> expected and the effect still has not happened. Follow with `runCurrent()`,
> or advance past the boundary. **Suggestion.**

```kotlin
// bad — the continuation scheduled at exactly 1000 is not in [0, 1000)
@Test
fun `fires the heartbeat after one second`() = runTest {
    var fired = false
    launch {
        delay(1_000)
        fired = true
    }
    advanceTimeBy(1_000)
    assertTrue(fired) // fails, even though currentTime is 1000
}

// good — runCurrent drains the tasks due at the new current time
@Test
fun `fires the heartbeat after one second`() = runTest {
    var fired = false
    launch {
        delay(1_000)
        fired = true
    }
    advanceTimeBy(1_000)
    runCurrent()
    assertTrue(fired)
}
```

## 39.10 Assert elapsed time against `currentTime`, never against a wall-clock measurement.

> Why? `runTest` skips delays, so no real time passes — that is the entire
> point. A test that measures with `measureTimeMillis` or `System.nanoTime` is
> measuring how long the assertions took, which is a few microseconds and
> tells you nothing about the schedule the code under test actually followed.
> `currentTime` reads the virtual clock, so an exponential backoff or a
> debounce window becomes a single exact-equality assertion rather than a
> tolerance band. **Suggestion.**

```kotlin
// bad — measures real elapsed time, which runTest deliberately does not spend
@Test
fun `backs off exponentially`() = runTest {
    val elapsed = measureTimeMillis { client.fetchWithRetry(url) }
    assertTrue(elapsed >= 7_000) // fails: elapsed is ~1 ms
}

// good — the virtual clock records the schedule the code actually requested
@Test
fun `backs off exponentially`() = runTest {
    client.fetchWithRetry(url)
    assertEquals(7_000L, currentTime) // 1s + 2s + 4s
}
```

## 39.11 Test a timeout with `delay` under virtual time, never with `Thread.sleep`.

> Why? `Thread.sleep` is not a suspension point, so `withTimeout` has nowhere
> to deliver the cancellation — the block runs to completion and the timeout
> silently does not fire. The test then asserts the wrong outcome *and* costs
> real seconds. `delay` is cancellable and virtual, so the timeout fires
> deterministically and instantly.
> **Violation — enforced by `detekt/SleepInsteadOfDelay`.**

```kotlin
// bad — Thread.sleep cannot be cancelled, so withTimeoutOrNull returns
// "response" rather than null, and the suite is three seconds slower
@Test
fun `times out a slow upstream`() = runTest {
    val result = withTimeoutOrNull(2_000) {
        Thread.sleep(3_000)
        "response"
    }
    assertNull(result)
}

// good
@Test
fun `times out a slow upstream`() = runTest {
    val result = withTimeoutOrNull(2_000) {
        delay(3_000)
        "response"
    }
    assertNull(result)
    assertEquals(2_000L, currentTime)
}
```

## 39.12 Inject the dispatcher into the class under test rather than replacing `Dispatchers.Main` globally.

> Why? `Dispatchers.setMain` mutates process-wide state, which makes tests
> order-dependent and forces a teardown that can be forgotten (§39.13). An
> injected `CoroutineDispatcher` with a production default needs neither: the
> test hands in a `TestDispatcher` backed by its own scheduler and nothing
> global changes. detekt's rule states the principle directly — "always use
> dependency injection to inject dispatchers for easier testing" — and its
> compliant example is a default parameter value, so the production call site
> stays unchanged. See [Chapter 34](34-dispatchers-and-context.md) for the
> design rule this test rule depends on.
> **Violation — enforced by `detekt/InjectDispatcher`.**

```kotlin
// bad — the dispatcher is welded in; the only lever a test has is global state
class ReportService(private val repo: ReportRepository) {
    suspend fun build(id: ReportId): Report = withContext(Dispatchers.IO) {
        repo.load(id).render()
    }
}

// good — a constructor parameter with a production default
class ReportService(
    private val repo: ReportRepository,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {
    suspend fun build(id: ReportId): Report = withContext(ioDispatcher) {
        repo.load(id).render()
    }
}

// good — the test supplies a dispatcher on the test's own scheduler
@Test
fun `builds the report`() = runTest {
    val service = ReportService(repo, StandardTestDispatcher(testScheduler))
    assertEquals(expectedReport, service.build(reportId))
}
```

## 39.13 If you must call `Dispatchers.setMain`, pair it with `resetMain` in a lifecycle hook, never inline in the test.

> Why? `setMain` is legitimate for framework code that hardcodes
> `Dispatchers.Main` and offers no seam. But an inline `setMain` with a matching
> inline `resetMain` at the end of the body is skipped whenever the body throws
> — which is exactly what a failing test does — leaving a dead `TestDispatcher`
> installed for every subsequent test in the same JVM. Those tests then fail
> with an unrelated message, and the failure order changes when someone renames
> a test. A JUnit 5 extension makes the reset unconditional. **Suggestion.**

```kotlin
// bad — a failed assertion skips resetMain and poisons the rest of the JVM
@Test
fun `loads the dashboard`() = runTest {
    Dispatchers.setMain(StandardTestDispatcher(testScheduler))
    assertEquals(Dashboard.Loaded, presenter.load())
    Dispatchers.resetMain()
}

// good — the extension resets even when the test throws
class MainDispatcherExtension(
    private val dispatcher: TestDispatcher = UnconfinedTestDispatcher(),
) : BeforeEachCallback, AfterEachCallback {
    override fun beforeEach(context: ExtensionContext) {
        Dispatchers.setMain(dispatcher)
    }

    override fun afterEach(context: ExtensionContext) {
        Dispatchers.resetMain()
    }
}

class DashboardPresenterTest {
    @JvmField
    @RegisterExtension
    val mainDispatcher = MainDispatcherExtension()

    @Test
    fun `loads the dashboard`() = runTest {
        assertEquals(Dashboard.Loaded, presenter.load())
    }
}
```

## 39.14 Give every `TestDispatcher` you construct the test's own `testScheduler`.

> Why? `StandardTestDispatcher()` with no argument creates a *new*
> `TestCoroutineScheduler` unless `Dispatchers.Main` has been replaced. Two
> schedulers mean two independent virtual clocks: `advanceUntilIdle()` on the
> test's clock never runs anything the subject queued on its own, so the test
> fails with a green production path and no explanation. Passing
> `testScheduler` keeps one clock for the whole test. **Suggestion.**

```kotlin
// bad — the service runs on its own clock; the test's advancement is a no-op
@Test
fun `debounces rapid input`() = runTest {
    val search = SearchService(StandardTestDispatcher())
    search.query("kot")
    search.query("kotlin")
    advanceTimeBy(301)
    runCurrent()
    assertEquals(listOf("kotlin"), search.executed) // fails: executed is empty
}

// good — one scheduler, one clock
@Test
fun `debounces rapid input`() = runTest {
    val search = SearchService(StandardTestDispatcher(testScheduler))
    search.query("kot")
    search.query("kotlin")
    advanceTimeBy(301)
    runCurrent()
    assertEquals(listOf("kotlin"), search.executed)
}
```

## 39.15 Use `toList()` only on a `Flow` that completes; bound the collection otherwise.

> Why? `toList()` is a terminal operator that suspends until the upstream
> completes. A `StateFlow`, a `SharedFlow`, or any `callbackFlow` backed by a
> live source never completes, so `toList()` suspends forever and the test dies
> at the `runTest` timeout — sixty seconds later, with an `AssertionError` that
> points at the test method rather than the offending call. Bound it with
> `take(n)`, collect in `backgroundScope` (§39.7), or use Turbine (§39.16).
> **Suggestion.**

```kotlin
// bad — a StateFlow never completes; this suspends until the test times out
@Test
fun `emits each loading state`() = runTest {
    val states = viewModel.state.toList()
    assertEquals(3, states.size)
}

// good — bound the collection, and start it before triggering the work
@Test
fun `emits each loading state`() = runTest {
    val states = async { viewModel.state.take(3).toList() }
    runCurrent()
    viewModel.load()
    advanceUntilIdle()
    assertEquals(listOf(Idle, Loading, Loaded), states.await())
}
```

## 39.16 Use Turbine for a hot or long-lived `Flow` instead of hand-rolling a collector and a mutable list.

> Why? The `async`/`take`/`await` dance in §39.15 is fragile — it hardcodes the
> emission count, it needs the collector started at the right moment, and it
> cannot express "and nothing else was emitted".
> [Turbine](https://github.com/cashapp/turbine) subscribes eagerly inside
> `test { }`, gives you `awaitItem()`, `awaitComplete()`, and `awaitError()` as
> assertions, has `expectNoEvents()` for the negative case, and fails the test
> if an event is left unconsumed when the block ends. Use `turbineScope { }`
> with `testIn` when you need two flows at once. **Suggestion.**

```kotlin
// bad — a mutable list, manual advancement, a hardcoded size assertion, and
// no way to assert that nothing further was emitted
@Test
fun `emits loading then loaded`() = runTest {
    val seen = mutableListOf<SearchEvent>()
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        service.events.collect { seen += it }
    }
    service.query("kotlin")
    advanceUntilIdle()
    assertEquals(2, seen.size)
}

// good — Turbine on a hot flow; test { } cancels the collection at the end
@Test
fun `emits loading then loaded`() = runTest {
    service.events.test {
        service.query("kotlin")
        assertEquals(SearchEvent.Loading, awaitItem())
        assertEquals(SearchEvent.Loaded(listOf("coroutines")), awaitItem())
        expectNoEvents()
    }
}

// good — a finite flow: assert the terminal event too
@Test
fun `completes after the last page`() = runTest {
    repo.pages(query).test {
        assertEquals(Page(1), awaitItem())
        assertEquals(Page(2), awaitItem())
        awaitComplete()
    }
}

// good — a failing flow: assert the error rather than wrapping in try/catch
@Test
fun `propagates an upstream failure`() = runTest {
    repo.pages(query).test {
        assertIs<IOException>(awaitError())
    }
}
```

## 39.17 Test cancellation as its own case, and assert both that the job cancelled and that cleanup ran.

> Why? A test that only exercises the happy path cannot tell you whether the
> subject is cancellable at all. A tight CPU loop with no suspension point, a
> `finally` block that never runs because the work was blocking, and a
> connection left open on cancel all pass every happy-path test in the suite.
> `cancelAndJoin()` waits for the coroutine to actually finish unwinding, so
> the assertions that follow observe the post-cleanup state rather than racing
> it. See [Chapter 35](35-cancellation-and-timeouts.md) for what cancellation
> does. **Suggestion.**

```kotlin
// bad — cancel() returns immediately and nothing is asserted; this test passes
// against an implementation that ignores cancellation entirely
@Test
fun `streams until cancelled`() = runTest {
    val job = launch { streamer.run() }
    advanceUntilIdle()
    job.cancel()
}

// good — join the unwind, then assert the observable consequences
@Test
fun `releases the connection when cancelled`() = runTest {
    val job = launch { streamer.run() }
    advanceUntilIdle()
    job.cancelAndJoin()
    assertTrue(job.isCancelled)
    assertFalse(connection.isOpen)
    assertEquals(1, connection.closeCount)
}
```

## 39.18 Stub and verify `suspend` collaborators with MockK's `coEvery` and `coVerify`.

> Why? `every { }` and `verify { }` take a non-suspending lambda, so a
> `suspend` call inside one is a compile error — "suspension functions can be
> called only within coroutine body" — not a runtime surprise. The `co`
> variants take a suspending lambda and are the only form that works. The
> failure worth naming is the *half* migration: `coEvery` for the stub and a
> plain `verify` for the assertion, which compiles only if the verified member
> happens not to be `suspend`, and then silently verifies the wrong overload.
> See [Chapter 32](32-testing.md) for MockK setup. **Suggestion.**

```kotlin
// bad — does not compile: `charge` is a suspend function and the `every`
// lambda is not a coroutine body
@Test
fun `settles the invoice`() = runTest {
    every { gateway.charge(any()) } returns ChargeResult.Approved
    billing.settle(invoice)
    verify(exactly = 1) { gateway.charge(invoice.amount) }
}

// good
@Test
fun `settles the invoice`() = runTest {
    coEvery { gateway.charge(any()) } returns ChargeResult.Approved
    billing.settle(invoice)
    coVerify(exactly = 1) { gateway.charge(invoice.amount) }
}
```

## 39.19 Assert an expected failure with `assertFailsWith`, never by inspecting a `runCatching` result.

> Why? `runCatching` catches `Throwable`, which includes
> `CancellationException`. Inside a test that means a cancelled test coroutine
> is reported as a business failure and the assertion goes green for entirely
> the wrong reason; outside a test it breaks structured concurrency outright
> (see [Chapter 24, §24.18](24-exceptions-and-result.md) and
> [Chapter 35](35-cancellation-and-timeouts.md)). `kotlin.test.assertFailsWith`
> is `inline`, so its lambda inherits the enclosing coroutine context and
> `suspend` calls work directly — note that JUnit's `assertThrows` is a Java
> method taking a SAM, so it does *not* accept a `suspend` call.
> **Violation — enforced by `detekt/SuspendFunSwallowedCancellation`.**

```kotlin
// bad — swallows CancellationException, and asserts only "something failed"
@Test
fun `rejects a negative amount`() = runTest {
    val result = runCatching { billing.charge(Money.of("-1.00")) }
    assertTrue(result.isFailure)
}

// good — names the exception type, and the message is available to assert on
@Test
fun `rejects a negative amount`() = runTest {
    val failure = assertFailsWith<IllegalArgumentException> {
        billing.charge(Money.of("-1.00"))
    }
    assertEquals("amount must be positive", failure.message)
}
```
