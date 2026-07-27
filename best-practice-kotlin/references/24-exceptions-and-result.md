<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 24. Exceptions & `Result`

Kotlin has no checked exceptions. The
[exceptions reference](https://kotlinlang.org/docs/exceptions.html) states it
directly: "Kotlin treats all exceptions as unchecked by default." Nothing in a
signature tells a caller what can be thrown, no compiler warning appears when
a throwing call goes unhandled, and no `throws` clause forces a decision. That
removes Java's most-complained-about ceremony and, in exchange, moves the
entire burden of documenting and containing failure onto you.

This chapter covers what to throw, what never to catch, and where the boundary
between an exception and a modelled outcome sits. Its most consequential rule
is §24.17, the **cancellation rule**: in `suspend` code, `catch (e: Exception)`
also catches `CancellationException`, so a routine defensive catch silently
disables structured concurrency and turns a cancelled coroutine into one that
keeps running. `runCatching` has the identical defect for the identical reason
(§24.18). The coroutine mechanics behind both are
[Chapter 35, Cancellation & Timeouts](35-cancellation-and-timeouts.md).

Two neighbouring topics are deferred. Modelling a closed set of *expected*
outcomes — the thing `kotlin.Result` is repeatedly and wrongly used for — is
[Chapter 13, Sealed Types](13-sealed-types.md); §24.19 states the boundary.
Using an exception in place of a loop exit or a "not found" signal is ruled out
in [Chapter 22, §22.21](22-control-flow-and-when.md), and §24.3 gives the
reasoning. Null handling, `!!`, and the alternatives to it are
[Chapter 6, Null Safety](06-null-safety.md).

**Tool alignment:** detekt's `UseRequire`, `UseCheckOrError`,
`UseRequireNotNull`, `UseCheckNotNull`, `TooGenericExceptionThrown`,
`TooGenericExceptionCaught`, `SwallowedException`, `RethrowCaughtException`,
`ThrowingExceptionsWithoutMessageOrCause`, `ThrowingExceptionFromFinally`,
`ReturnFromFinally`, `PrintStackTrace`, `InstanceOfCheckForException`,
`ErrorUsageWithThrowable`, `ObjectExtendsThrowable`, `NotImplementedDeclaration`,
`MissingUseCall`, `SuspendFunSwallowedCancellation`, and
`SuspendFunInFinallySection` all fire on rules below. Four of those —
`NotImplementedDeclaration`, `MissingUseCall`,
`SuspendFunSwallowedCancellation`, and `SuspendFunInFinallySection` — ship
**inactive by default** and have to be switched on in `detekt.yml` before they
report anything. Rules a named check actually enforces are marked
**Violation**; the rest are **Suggestion**.

## 24.1 Document every exception a public function can throw in KDoc, with `@throws`.

> Why? Kotlin's signature carries no failure information at all, so KDoc is the
> *only* contract a caller has. Without it, the caller either wraps every call
> in a defensive `catch (e: Exception)` — which §24.13 and §24.17 rule out —
> or discovers the failure mode in production. Document the exception type and,
> more importantly, the condition: "throws `IllegalArgumentException` if
> `amount` is negative" is useful; "throws `IllegalArgumentException` on bad
> input" is not. See [Chapter 4, KDoc](04-kdoc.md) for tag formatting.
> **Suggestion** — no tool can tell that documentation is missing.

```kotlin
// bad — the caller cannot know this parses, let alone that it throws
fun parseAmount(raw: String, currency: Currency): Money =
    Money(raw.toLong(), currency)

// good
/**
 * Parses [raw] as a whole number of minor units of [currency].
 *
 * @throws NumberFormatException if [raw] is not a valid decimal integer.
 * @throws IllegalArgumentException if the parsed value is negative.
 */
fun parseAmount(raw: String, currency: Currency): Money {
    val minorUnits = raw.toLong()
    require(minorUnits >= 0) { "amount must be non-negative, was $minorUnits" }
    return Money(minorUnits, currency)
}
```

## 24.2 Annotate a Kotlin function with `@Throws` when Java callers must be able to handle its exception.

> Why? Because Kotlin emits no `throws` clause, Java code calling a Kotlin
> function cannot `catch` a checked exception from it — javac rejects the catch
> block as unreachable. The exceptions reference gives `@Throws` as the fix:
> the annotation "alerts callers about possible exceptions" by writing the
> `throws` clause into the bytecode. Apply it only at the Java-facing boundary;
> on a function only Kotlin calls it is noise. See
> [Chapter 28, Java Interop](28-java-interop.md). **Suggestion.**

```kotlin
// bad — Java callers get "exception IOException is never thrown in the
// corresponding try block" and cannot compile a catch
fun writeReport(path: Path, report: Report) {
    Files.newBufferedWriter(path).use { it.write(report.render()) }
}

// good
@Throws(IOException::class)
fun writeReport(path: Path, report: Report) {
    Files.newBufferedWriter(path).use { it.write(report.render()) }
}
```

## 24.3 Throw only for conditions that are genuinely exceptional; never for an expected outcome.

> Why? An exception is an undeclared non-local jump that captures a stack trace
> on the way out. Used for an outcome the caller expects — "no such user",
> "password wrong", "cart empty" — it costs a stack walk on the common path,
> makes the control flow invisible at the call site, and forces callers into
> `try`/`catch` blocks that suppress unrelated failures. Model absence with a
> nullable return, and a closed set of outcomes with a sealed type
> ([Chapter 13](13-sealed-types.md)). Reserve throwing for programming errors
> and for genuine infrastructure failure. **Suggestion.**

```kotlin
// bad — "not found" is an expected outcome, not an exceptional condition
fun findUser(email: String): User =
    repository.byEmail(email) ?: throw NoSuchElementException("no user: $email")

// bad — the caller now has to catch to implement ordinary logic
val user = try {
    findUser(email)
} catch (e: NoSuchElementException) {
    return SignInResult.UnknownAccount
}

// good — absence is a value
fun findUser(email: String): User? = repository.byEmail(email)

val user = findUser(email) ?: return SignInResult.UnknownAccount
```

## 24.4 Validate arguments with `require`, which throws `IllegalArgumentException`.

> Why? `require` states the precondition as a positive assertion and produces
> the exception type the JDK and every Kotlin reader associate with a bad
> argument. Hand-rolling `if (!cond) throw IllegalArgumentException(...)`
> inverts the condition — the single most common place to get a validation
> backwards — and costs three lines where one does. The message lambda is
> `() -> Any`, so it is evaluated only on failure and interpolation is free on
> the happy path. **Violation — enforced by `detekt/UseRequire`.**

```kotlin
// bad — the condition is inverted, and the string is built on every call
fun withdraw(amount: Money, balance: Money) {
    if (amount <= Money.ZERO) {
        throw IllegalArgumentException("amount must be positive, was $amount")
    }
}

// good
fun withdraw(amount: Money, balance: Money) {
    require(amount > Money.ZERO) { "amount must be positive, was $amount" }
    require(amount <= balance) { "amount $amount exceeds balance $balance" }
}
```

## 24.5 Assert object state with `check`, which throws `IllegalStateException`.

> Why? The distinction between `require` and `check` is who is at fault, and it
> is worth keeping: `IllegalArgumentException` says "the caller passed something
> invalid," `IllegalStateException` says "this object is not in a state where
> that call makes sense." A caller reading a stack trace can act on the first
> and must escalate the second. Collapsing both into one type destroys that
> signal. **Violation — enforced by `detekt/UseCheckOrError`.**

```kotlin
// bad — wrong exception type; reads as though the caller passed bad input
class Connection {
    private var open = false

    fun send(frame: Frame) {
        if (!open) {
            throw IllegalArgumentException("connection is closed")
        }
    }
}

// good
class Connection {
    private var open = false

    fun send(frame: Frame) {
        check(open) { "connection is closed; call open() first" }
    }
}
```

## 24.6 Use `error(...)` for a state the code believes is unreachable — it returns `Nothing`, so it works inside an expression.

> Why? `error` throws `IllegalStateException` and is declared
> `fun error(message: Any): Nothing`. Because `Nothing` is a subtype of every
> type, `error(...)` type-checks as the value of any branch, which makes it the
> right way to close an otherwise-exhaustive `when` over an open subject
> (§22.4) without introducing a fake default. Two traps: `error(e)` where `e`
> is a `Throwable` produces an exception whose *message* is the throwable's
> `toString` and whose `cause` is `null`, discarding the original stack trace;
> and `TODO()` throws `NotImplementedError`, which is a placeholder, not an
> error path. **Suggestion — `detekt/ErrorUsageWithThrowable` covers this, but it is absent from detekt 1.23.8's default config (the docs site is ahead of the latest stable release). Enable it once your detekt version ships it; see chapter 47.**
> for the `error(throwable)` form (active by default) and
> `detekt/NotImplementedDeclaration`, which "reports all exceptions of the type
> `NotImplementedError` that are thrown" and "also reports all `TODO(..)`
> functions" but is **not active by default**.

```kotlin
// bad — a fake default value hides the impossible case until much later
fun rateFor(tier: String): BigDecimal = when (tier) {
    "gold" -> BigDecimal("0.10")
    "silver" -> BigDecimal("0.05")
    else -> BigDecimal.ZERO // silently prices unknown tiers at zero
}

// bad — the cause is dropped; the original stack trace is gone
catch (e: IOException) {
    error(e)
}

// good — the unreachable branch says so, and still type-checks as BigDecimal
fun rateFor(tier: String): BigDecimal = when (tier) {
    "gold" -> BigDecimal("0.10")
    "silver" -> BigDecimal("0.05")
    else -> error("unknown tier: $tier")
}

// good — keep the cause (see 24.15)
catch (e: IOException) {
    throw PricingUnavailableException("rate lookup failed for $tier", e)
}
```

## 24.7 Replace every `!!` with `requireNotNull` or `checkNotNull`, and give it a message that names the value.

> Why? `!!` throws a `NullPointerException` with no message, so the stack trace
> tells you the line and nothing else — on a line with three nullable
> expressions you cannot tell which one was null.
> `requireNotNull(x) { "..." }` throws `IllegalArgumentException` with your
> text, `checkNotNull` throws `IllegalStateException`, and both smart-cast the
> result to the non-null type so the rest of the function is unchanged. Pick
> between them by the same "whose fault" rule as §24.4 versus §24.5.
> **Violation — enforced by `detekt/UnsafeCallOnNullableType`** for the `!!`
> itself, and by `detekt/UseRequireNotNull` / `detekt/UseCheckNotNull` for the
> hand-rolled `require(x != null)` form.

```kotlin
// bad — which of the three was null?
fun ship(order: Order) {
    val label = carrier!!.rateCard!!.labelFor(order.destination!!)
}

// bad — the hand-rolled form loses the smart cast
fun ship(order: Order) {
    require(order.destination != null) { "destination is required" }
    val destination: Address = order.destination!!
}

// good — each failure names itself, and each value is smart-cast afterwards
fun ship(order: Order) {
    val carrier = checkNotNull(carrier) { "no carrier configured for ${order.id}" }
    val rateCard = checkNotNull(carrier.rateCard) { "carrier has no rate card" }
    val destination =
        requireNotNull(order.destination) { "order ${order.id} has no destination" }
    val label = rateCard.labelFor(destination)
}
```

## 24.8 Never rely on `assert` for anything that must hold in production.

> Why? The stdlib documents that `assert` "throws an `AssertionError` if the
> value is false **and runtime assertions have been enabled on the JVM using
> the `-ea` JVM option**." Production JVMs almost never run with `-ea`, so an
> `assert` in shipped code is a comment with a lambda attached. Use it only for
> genuinely optional self-checks that you are content to see disabled; use
> `require`/`check` for everything that must hold. **Suggestion.**

```kotlin
// bad — silently disabled in production; the invariant is not enforced at all
fun settle(payment: Payment) {
    assert(payment.amount > Money.ZERO) { "amount must be positive" }
    ledger.post(payment)
}

// good — the invariant is enforced wherever the code runs
fun settle(payment: Payment) {
    require(payment.amount > Money.ZERO) { "amount must be positive, was ${payment.amount}" }
    ledger.post(payment)
}
```

## 24.9 Never throw an exception without a message, and never construct one without the cause when you have one.

> Why? A bare `throw IllegalStateException()` gives an operator a stack trace
> and no statement of what went wrong, which is the difference between a
> five-minute incident and an hour of code archaeology. Put the offending
> values in the message — the ids, the state, the bound that was violated —
> because the log line is all anyone will have. **Violation — enforced by
> `detekt/ThrowingExceptionsWithoutMessageOrCause`.**

```kotlin
// bad — the stack trace points at the line; nothing says what was wrong with it
if (batch.size > limit) {
    throw IllegalStateException()
}

// good
if (batch.size > limit) {
    throw IllegalStateException("batch ${batch.id} has ${batch.size} items, limit is $limit")
}
```

## 24.10 Never throw `Exception`, `RuntimeException`, `Error`, or `Throwable`.

> Why? A generic throw forces every caller who wants to handle it into an
> equally generic catch, which then swallows everything else on that path — the
> two anti-patterns feed each other. It also erases the only machine-readable
> signal a failure carries: its type. Throw the most specific type that
> describes the failure, from the stdlib where one fits and from your own
> hierarchy where none does (§24.11). **Violation — enforced by
> `detekt/TooGenericExceptionThrown`** (default `exceptionNames` is
> `['Error', 'Exception', 'RuntimeException', 'Throwable']`).

```kotlin
// bad — the caller must catch Exception to handle it, and then catches everything
fun load(id: OrderId): Order {
    throw Exception("order $id not found")
}

// good
fun load(id: OrderId): Order {
    throw OrderNotFoundException(id)
}
```

## 24.11 Define a custom exception type only when a caller will branch on it or needs data from it.

> Why? A custom type earns its keep by carrying structure — the id that was not
> found, the field that failed validation — so a caller can act on it
> programmatically instead of parsing a message string. A type that adds only a
> name over `IllegalStateException` adds a file, an import, and a decision for
> every future reader, and nobody ever catches it. Extend `RuntimeException`
> (Kotlin has no checked exceptions to opt into), give it a `cause` parameter,
> and put the structured data in `val` properties. **Suggestion** — but note
> `detekt/ObjectExtendsThrowable` catches the specific mistake of declaring an
> exception as an `object`, which shares one stack trace across every throw
> site.

```kotlin
// bad — a bare rename with no data; the caller still has to parse the message
class OrderException(message: String) : RuntimeException(message)

// bad — a single shared instance, so the stack trace is from the first throw
object OrderNotFound : RuntimeException("order not found")

// good — carries the data a caller needs, and preserves the cause
class OrderNotFoundException(
    val orderId: OrderId,
    cause: Throwable? = null,
) : RuntimeException("order $orderId not found", cause)

// the caller can now act on the structure, not on the text
catch (e: OrderNotFoundException) {
    metrics.increment("order.missing", "tenant" to e.orderId.tenant)
}
```

## 24.12 Never catch `Throwable`, and never catch `Exception` unless you both handle it and rethrow what you cannot.

> Why? `Throwable` includes `Error` — `OutOfMemoryError`, `StackOverflowError`,
> `LinkageError` — which are JVM-level failures that no application code can
> meaningfully recover from and that leave the process in an undefined state.
> Catching `Exception` is narrower but still catches every programming error
> (`NullPointerException`, `ClassCastException`) alongside the one I/O failure
> you meant to handle, so a genuine bug is converted into a log line and the
> program limps on with wrong data. In `suspend` code it is worse still — see
> §24.17. **Violation — enforced by `detekt/TooGenericExceptionCaught`**
> (default `exceptionNames` includes `Exception`, `RuntimeException`,
> `Throwable`, `Error`, and `NullPointerException`).

```kotlin
// bad — catches OutOfMemoryError and every NullPointerException in the block
fun refresh(): Snapshot? = try {
    client.fetchSnapshot()
} catch (e: Throwable) {
    logger.warn(e) { "refresh failed" }
    null
}

// good — catch exactly the failure you can handle; everything else propagates
fun refresh(): Snapshot? = try {
    client.fetchSnapshot()
} catch (e: IOException) {
    logger.warn(e) { "snapshot refresh failed, serving stale data" }
    null
}
```

## 24.13 Catch by type; never `is`-check or cast inside a `catch` block.

> Why? A `catch (e: Exception) { if (e is IOException) ... }` re-implements the
> JVM's own dispatch, badly: the `else` branch of that `if` is the swallow of
> §24.14, and the compiler can no longer tell you that a catch clause is
> unreachable or that a type was forgotten. Multiple `catch` clauses express
> the same intent declaratively, in order, with the narrowest type first.
> **Violation — enforced by `detekt/InstanceOfCheckForException`;** the
> unreachable-clause case is `detekt/UnreachableCatchBlock`.

```kotlin
// bad — hand-rolled dispatch, and the implicit else swallows everything
try {
    client.fetchSnapshot()
} catch (e: Exception) {
    if (e is IOException) {
        logger.warn(e) { "network failure" }
    } else if (e is SerializationException) {
        logger.error(e) { "malformed payload" }
    }
}

// good
try {
    client.fetchSnapshot()
} catch (e: SerializationException) {
    logger.error(e) { "malformed payload" }
} catch (e: IOException) {
    logger.warn(e) { "network failure" }
}
```

## 24.14 Never swallow a caught exception.

> Why? An empty `catch`, or one that logs only `e.message`, destroys the stack
> trace — the only artefact that says *where* the failure came from. The
> symptom is a production incident whose log reads `null` or
> `Connection reset` with no indication of which of forty call sites produced
> it. Either handle the failure (with the throwable passed to the logger, not
> its message), rethrow it, or wrap it with the original as `cause`.
> `printStackTrace()` is not handling either: it writes to stderr, bypassing
> every log appender, correlation id, and alerting rule. **Violation —
> enforced by `detekt/SwallowedException` and `detekt/PrintStackTrace`.**

```kotlin
// bad — the stack trace is gone three different ways
try {
    parse(payload)
} catch (e: SerializationException) {
    // ignored
}

try {
    parse(payload)
} catch (e: SerializationException) {
    logger.warn { "parse failed: ${e.message}" }
}

try {
    parse(payload)
} catch (e: SerializationException) {
    e.printStackTrace()
}

// good — the throwable reaches the logger, with context
try {
    parse(payload)
} catch (e: SerializationException) {
    logger.warn(e) { "failed to parse payload for tenant ${payload.tenantId}" }
}
```

## 24.15 Pass the original exception as `cause` whenever you translate one across a layer boundary.

> Why? The `cause` chain is what makes a stack trace in a five-layer
> application readable — `Caused by:` lines reconstruct the path from the HTTP
> handler down to the socket that actually failed. Constructing the new
> exception with only a message discards everything below the translation
> point, so the trace begins at the layer that noticed the problem rather than
> the layer that had it. Every JDK exception has a `(message, cause)`
> constructor; give yours one too (§24.11). **Suggestion** — the omission is
> partly covered by `detekt/ThrowingExceptionsWithoutMessageOrCause`.

```kotlin
// bad — the SQL exception, its vendor code, and its stack frames are gone
catch (e: SQLException) {
    throw RepositoryException("could not load order $id")
}

// good — Caused by: java.sql.SQLException ... survives to the log
catch (e: SQLException) {
    throw RepositoryException("could not load order $id", e)
}
```

## 24.16 Never log and rethrow the same failure.

> Why? Every layer that logs before rethrowing multiplies one incident into N
> stack traces in the log, at N different severities, so an operator cannot
> tell whether one thing failed or five did, and alert thresholds tuned on
> volume fire wrongly. Log once, at the boundary that actually decides what to
> do about the failure — the request handler, the job runner, the top-level
> supervisor — and let every layer below it either propagate or translate
> (§24.15). **Suggestion** — note that `detekt/RethrowCaughtException`
> deliberately permits a `catch` that does work before `throw e`, so it will
> not flag this.

```kotlin
// bad — the same failure is logged at three layers; the log shows three incidents
catch (e: SQLException) {
    logger.error(e) { "query failed" }
    throw RepositoryException("could not load order $id", e)
}

// good — the lower layer only adds context; the boundary decides and logs
catch (e: SQLException) {
    throw RepositoryException("could not load order $id", e)
}

// good — one log line, at the layer that turns the failure into a response
@ExceptionHandler(RepositoryException::class)
fun handle(e: RepositoryException): ResponseEntity<ErrorBody> {
    logger.error(e) { "request failed" }
    return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(ErrorBody.INTERNAL)
}
```

## 24.17 In `suspend` code, never catch `Exception` without rethrowing `CancellationException`.

> Why? **This is the cancellation rule, and it is the highest-consequence rule
> in the chapter.** Coroutine cancellation is delivered by *throwing*
> `CancellationException` from the next suspension point. `CancellationException`
> extends `IllegalStateException`, so it extends `Exception` — which means a
> routine `catch (e: Exception)` intercepts it, treats a cancellation as an
> application failure, and returns normally. The coroutine then keeps running
> inside a scope that believes it is cancelled: `withTimeout` does not stop the
> work, a cancelled request keeps consuming a connection, and a
> `SupervisorJob` shutdown never completes. Nothing fails loudly; the process
> just leaks. Either catch narrowly enough to exclude it, or rethrow it in a
> dedicated first clause. See
> [Chapter 35, Cancellation & Timeouts](35-cancellation-and-timeouts.md).
> **Violation — enforced by `detekt/TooGenericExceptionCaught`;** the
> `suspend`-specific forms are `detekt/SuspendFunSwallowedCancellation` (§24.18)
> and `detekt/SuspendFunInFinallySection` (§24.20).

```kotlin
// bad — swallows cancellation; withTimeout below never actually stops the work
suspend fun fetchProfile(id: UserId): Profile? = try {
    client.get(id)
} catch (e: Exception) {
    logger.warn(e) { "profile fetch failed for $id" }
    null
}

withTimeout(2.seconds) { fetchProfile(id) } // times out, work continues

// good — rethrow cancellation first, then handle real failures
suspend fun fetchProfile(id: UserId): Profile? = try {
    client.get(id)
} catch (e: CancellationException) {
    throw e
} catch (e: IOException) {
    logger.warn(e) { "profile fetch failed for $id" }
    null
}

// good — a narrow catch never sees CancellationException in the first place
suspend fun fetchProfile(id: UserId): Profile? = try {
    client.get(id)
} catch (e: IOException) {
    logger.warn(e) { "profile fetch failed for $id" }
    null
}
```

## 24.18 Never wrap a suspending call in bare `runCatching`.

> Why? `runCatching` catches `Throwable`, so it has §24.17's defect and
> §24.12's simultaneously: it swallows `CancellationException`, and it swallows
> `OutOfMemoryError`. detekt's rule states the consequence directly —
> "`CancellationException` must be immediately rethrown to maintain proper
> coroutine cancellation semantics and avoid memory leaks or crashes." In
> non-suspending code `runCatching` is fine and often the clearest thing to
> write. In `suspend` code, use `try`/`catch` with an explicit
> `CancellationException` clause, or write the cancellation-aware wrapper once
> and use it everywhere. **Violation — enforced by
> `detekt/SuspendFunSwallowedCancellation`** (coroutines rule set; **not active
> by default**, so enable it explicitly — this is the single most valuable
> detekt rule to turn on in a coroutine codebase).

```kotlin
// bad — cancellation is captured as a Result.failure and the coroutine continues
suspend fun load(id: UserId): Result<Profile> = runCatching { client.get(id) }

// good — detekt's own compliant shape
suspend fun load(id: UserId): Profile? = try {
    client.get(id)
} catch (e: CancellationException) {
    throw e
} catch (e: IOException) {
    null
}

// good — write it once if you need Result at a boundary
suspend inline fun <T> runCatchingCancellable(block: () -> T): Result<T> =
    try {
        Result.success(block())
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        Result.failure(e)
    }
```

## 24.19 Use `kotlin.Result` only to ferry a generic failure across a boundary; model domain outcomes with a sealed type.

> Why? The
> [KEEP that introduced `Result`](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)
> is explicit: "The `Result` class is not designed to represent domain-specific
> error conditions," and "if some API requires its callers to handle failures
> locally... then it should use nullable types... or domain-specific data
> types." `Result` carries a bare `Throwable`, so a caller who wants to branch
> on the failure has to `is`-check it — §24.13's anti-pattern wearing a
> different hat — and exhaustiveness is impossible. Returning `Result<T>` has
> been legal since Kotlin 1.5, which removed the earlier compiler restriction;
> legality is not a recommendation. Use it where the failure is genuinely
> opaque and just needs transporting (a callback bridge, a coroutine
> continuation, a retry helper); use a sealed hierarchy
> ([Chapter 13](13-sealed-types.md)) where the caller must handle each outcome.
> **Suggestion.**

```kotlin
// bad — the caller must type-check a Throwable to implement business logic
suspend fun placeOrder(cart: Cart): Result<OrderId>

when (val e = result.exceptionOrNull()) {
    is OutOfStockException -> showBackorder(e.sku)
    is PaymentDeclinedException -> showPaymentRetry()
    else -> showGenericError()
}

// good — a closed set of outcomes, exhaustively handled with no else (22.3)
sealed interface PlaceOrderResult {
    data class Placed(val orderId: OrderId) : PlaceOrderResult
    data class OutOfStock(val sku: Sku) : PlaceOrderResult
    data object PaymentDeclined : PlaceOrderResult
}

suspend fun placeOrder(cart: Cart): PlaceOrderResult

when (val result = placeOrder(cart)) {
    is PlaceOrderResult.Placed -> showConfirmation(result.orderId)
    is PlaceOrderResult.OutOfStock -> showBackorder(result.sku)
    PlaceOrderResult.PaymentDeclined -> showPaymentRetry()
}
```

## 24.20 Never `return` from a `finally` block, and never throw from one.

> Why? `finally` runs while an exception is propagating. A `return` inside it
> completes the function normally, which *discards the in-flight exception
> entirely* — the failure vanishes with no log line anywhere. A `throw` from
> `finally` replaces the original exception with the new one, losing the real
> cause the same way. Keep `finally` to cleanup that cannot fail, and prefer
> `use` (§24.21), which handles the interaction correctly by adding a failing
> `close` to the original exception's suppressed list. In coroutines a
> suspending call in `finally` will not run at all once the job is cancelled
> unless it is wrapped in `withContext(NonCancellable)`. **Violation —
> enforced by `detekt/ReturnFromFinally` and
> `detekt/ThrowingExceptionFromFinally`** (both active by default) **and
> `detekt/SuspendFunInFinallySection`** (coroutines rule set, not active by
> default).

```kotlin
// bad — the IOException from parse() is discarded and nobody ever learns of it
fun read(path: Path): Config {
    val stream = Files.newInputStream(path)
    try {
        return parse(stream)
    } finally {
        stream.close()
        return Config.DEFAULT
    }
}

// bad — cleanup never runs once the coroutine is cancelled
launch {
    try {
        suspendingWork()
    } finally {
        suspendingCleanup()
    }
}

// good — cleanup only, no control flow
fun read(path: Path): Config = Files.newInputStream(path).use { parse(it) }

// good — cleanup that must survive cancellation says so
launch {
    try {
        suspendingWork()
    } finally {
        withContext(NonCancellable) { suspendingCleanup() }
    }
}
```

## 24.21 Close every `AutoCloseable` with `use`, never with a hand-written `try`/`finally`.

> Why? `use` is declared
> `inline fun <T : AutoCloseable?, R> T.use(block: (T) -> R): R` and, per its
> documentation, "in case if the resource is being closed due to an exception
> occurred in [block], and the closing also fails with an exception, the latter
> is added to the suppressed exceptions of the former." A hand-written
> `try`/`finally` gets that backwards: a failure in `close()` replaces the real
> exception, which is §24.20's bug in its most common disguise. `use` also
> makes it impossible to forget the `close` on an early return. Nest or chain
> `use` calls for multiple resources. **Suggestion — `detekt/MissingUseCall` covers this, but it is absent from
> detekt 1.23.8's default config (the docs site is ahead of the latest stable
> release), so it cannot be enabled on that version. Re-check on upgrade; see
> chapter 47.**

```kotlin
// bad — if both parse() and close() throw, only the close failure survives
fun read(path: Path): Config {
    val stream = Files.newInputStream(path)
    try {
        return parse(stream)
    } finally {
        stream.close()
    }
}

// good — one expression, and a failing close is recorded as suppressed
fun read(path: Path): Config = Files.newInputStream(path).use { parse(it) }

// good — multiple resources nest
fun copy(source: Path, target: Path): Long =
    Files.newInputStream(source).use { input ->
        Files.newOutputStream(target).use { output ->
            input.transferTo(output)
        }
    }
```

## 24.22 Use `try` as an expression when both the happy path and the recovery produce a value.

> Why? The coding conventions'
> [conditional statements](https://kotlinlang.org/docs/coding-conventions.html#conditional-statements)
> section lists `try` alongside `if` and `when`: "Prefer using the expression
> form of `try`, `if`, and `when`." The statement form needs a `var` declared
> before the `try` and assigned in two places, which means the compiler cannot
> prove it is assigned exactly once and a reader must check both branches to
> learn the type. The expression form makes the recovery value part of the same
> expression as the value it replaces. **Suggestion.**

```kotlin
// bad — a var, two assignments, and no compile-time guarantee of either
fun port(raw: String): Int {
    var value: Int
    try {
        value = raw.toInt()
    } catch (e: NumberFormatException) {
        value = DEFAULT_PORT
    }
    return value
}

// good
fun port(raw: String): Int = try {
    raw.toInt()
} catch (e: NumberFormatException) {
    DEFAULT_PORT
}

// good — when there is no exception to recover from, do not use try at all
fun port(raw: String): Int = raw.toIntOrNull() ?: DEFAULT_PORT
```
