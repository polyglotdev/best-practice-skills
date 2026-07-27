<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 31. Logging

Logs are the only observability signal that survives a process dying, and
they are the one thing every incident review reads first. They are also the
easiest thing in a Kotlin codebase to get subtly wrong, because Kotlin's most
attractive feature at a log call site — the string template — is exactly the
wrong tool for the job, and it looks perfect.

This chapter covers the API to log through, the three Kotlin logger idioms
and when each is right, the eager-evaluation trap that Kotlin templates
create, level discipline, what must never reach a log line, and the
coroutine-specific failure of `MDC`.

Sources are the [SLF4J manual](https://www.slf4j.org/manual.html) and the
[`LoggingEventBuilder` API](https://www.slf4j.org/apidocs/org/slf4j/spi/LoggingEventBuilder.html)
for the fluent form, [kotlin-logging](https://github.com/oshai/kotlin-logging)
for the Kotlin facade, and the
[`kotlinx-coroutines-slf4j` `MDCContext` reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-slf4j/kotlinx.coroutines.slf4j/-m-d-c-context/)
for §31.14. Neither style guide legislates on logging, so no rule here
carries a style-guide citation.

Two neighbouring topics are deferred. **What to do with a failure** —
propagate, translate, or handle — is
[Chapter 24, Exceptions & `Result`](24-exceptions-and-result.md); §31.9 states
only the logging half of the handle-once rule. **Coroutine context
propagation in general**, including why a `ThreadLocal` does not follow a
coroutine, is [Chapter 34, Dispatchers & Coroutine Context](34-dispatchers-and-context.md).

**Tool alignment:** `detekt/PrintStackTrace` fires on `printStackTrace()` and
`Thread.dumpStack()`. `detekt/SwallowedException` and
`detekt/TooGenericExceptionCaught` cover the catch blocks where bad logging
usually lives. `detekt/ForbiddenMethodCall`, configured with
`kotlin.io.println`, turns §31.1 into a build failure. Rules a named check
enforces are marked **Violation**; the rest are **Suggestion**.

## 31.1 Log through SLF4J; `println` has no place in library or service code.

> Why? `println` writes to `System.out` with no level, no timestamp, no
> logger name, no MDC, and no way to turn it off in production. It bypasses
> every appender, so it never reaches the log aggregator, never gets
> structured, and never rotates — it just fills a container's stdout buffer.
> SLF4J is a facade, so choosing it does not commit you to an implementation:
> Logback, Log4j 2, or `java.util.logging` all bind behind it. The only
> legitimate `println` is in a CLI's own output stream, which is a user
> interface, not a log.
> **Violation — enforced by `detekt/ForbiddenMethodCall`** when configured
> with `kotlin.io.println` (the rule requires type resolution).

```kotlin
// bad — invisible to the log pipeline, unfilterable, undisableable
fun process(order: Order) {
    println("processing order ${order.id}")
    ...
}

// good
private val logger = LoggerFactory.getLogger(OrderProcessor::class.java)

fun process(order: Order) {
    logger.info("processing order {}", order.id)
    ...
}
```

```yaml
# config/detekt/detekt.yml — makes the rule above a build failure
style:
  ForbiddenMethodCall:
    active: true
    methods:
      - reason: 'use SLF4J, not stdout'
        value: 'kotlin.io.println'
```

## 31.2 Declare one private logger per class, and name it after the class — not after the companion object.

> Why? The logger's name is what appears in every line and what per-package
> level configuration matches against, so getting it wrong makes a whole
> class unfilterable. Kotlin sets a specific trap here: inside a
> `companion object`, `javaClass` resolves to the *companion's* class, so
> `LoggerFactory.getLogger(javaClass)` yields the logger
> `com.example.OrderService$Companion`, which no sane logback config
> matches. Use the explicit `OrderService::class.java`, or use a top-level
> `private val`, which has no companion to trip over and is the more
> idiomatic Kotlin shape. **Suggestion.**

```kotlin
// bad — the logger is named com.example.OrderService$Companion
class OrderService {
    companion object {
        private val logger = LoggerFactory.getLogger(javaClass)
    }
}

// bad — a public logger is API surface nobody asked for
class OrderService {
    val logger = LoggerFactory.getLogger(OrderService::class.java)
}

// good — explicit class reference inside a companion
class OrderService {
    companion object {
        private val logger: Logger = LoggerFactory.getLogger(OrderService::class.java)
    }
}

// good — top-level private val; file-scoped, no companion, no ceremony, and
// the name follows the class through a rename
private val logger: Logger = LoggerFactory.getLogger(OrderService::class.java)

class OrderService { ... }
```

## 31.3 With plain SLF4J, use `{}` placeholders — never a Kotlin string template.

> Why? This is the Kotlin-specific trap and it is worth its own rule because
> the wrong version looks *better*. A Kotlin string template is evaluated
> where it is written, before the call, so `logger.debug("state: $state")`
> builds the entire string — every `toString`, every concatenation, every
> allocation — and then hands it to a logger that throws it away because
> `DEBUG` is disabled. SLF4J's parameterized form defers formatting until
> after the level check: with `{}` placeholders the arguments are passed by
> reference and only rendered if the event is actually logged. In a hot path
> the difference is measurable; in a debug statement inside a loop it is
> dramatic. **Suggestion.**

```kotlin
// bad — the template is built on every call, even when DEBUG is off
logger.debug("resolved ${candidates.size} candidates for ${request.describe()}")

// good — nothing is formatted unless DEBUG is enabled
logger.debug("resolved {} candidates for {}", candidates.size, request)

// good — templates are fine where the level is always on and the args are
// already strings, but the parameterized form costs nothing, so prefer it
logger.info("started on port {}", port)
```

## 31.4 Use a lazy logging API instead of an `isDebugEnabled` guard.

> Why? The guard exists only because the plain SLF4J call evaluates its
> arguments eagerly (§31.3). It works, but it doubles the line count, it is
> easy to write for `debug` and forget for `trace`, and reviewers stop
> noticing when it is missing. Both lazy APIs remove the need: kotlin-logging
> takes a `() -> Any?` message lambda, and SLF4J 2.0's fluent builder accepts
> a `Supplier<String>` which Kotlin fills by SAM conversion. Either way the
> lambda body does not run unless the level is enabled. **Suggestion.**

```kotlin
// bad — correct, but noisy, and the trace() below it was forgotten
if (logger.isDebugEnabled) {
    logger.debug("plan: {}", plan.explain())
}
logger.trace("full plan: ${plan.dump()}")   // dump() runs unconditionally

// good — kotlin-logging: the lambda runs only if the level is enabled
logger.debug { "plan: ${plan.explain()}" }
logger.trace { "full plan: ${plan.dump()}" }

// good — plain SLF4J 2.0 fluent API, no extra dependency
logger.atDebug().log { "plan: ${plan.explain()}" }
```

## 31.5 In a Kotlin codebase, prefer kotlin-logging's `KotlinLogging.logger {}`; keep the import paths straight.

> Why? [kotlin-logging](https://github.com/oshai/kotlin-logging) is a thin
> facade over SLF4J that gives you the lambda form of §31.4 on every level,
> and `KotlinLogging.logger {}` derives the logger name from the enclosing
> class automatically, which removes the §31.2 companion trap entirely. The
> one thing to get right is the coordinates: version 5 moved the group id
> from `io.github.microutils` to `io.github.oshai` and the root package from
> `mu` to `io.github.oshai.kotlinlogging`. Code and tutorials predating that
> move will not resolve, and the failure reads like a missing dependency
> rather than a rename. It still requires an SLF4J binding at runtime.
> **Suggestion.**

```kotlin
// bad — the pre-5.x package; unresolved against a current dependency
import mu.KotlinLogging

private val logger = KotlinLogging.logger {}

// good — current coordinates and package
// build.gradle.kts: implementation("io.github.oshai:kotlin-logging-jvm:7.0.3")
import io.github.oshai.kotlinlogging.KotlinLogging

private val logger = KotlinLogging.logger {}

class OrderService {
    fun process(order: Order) {
        logger.debug { "processing ${order.id}" }
    }
}
```

## 31.6 Assign levels by who acts on the line, not by how important it feels.

> Why? A level is a routing decision, and the only useful question is "who
> reads this, and what do they do about it?" The scale is:
>
> | Level | Means | Consequence |
> |---|---|---|
> | `ERROR` | an operator must act, now | pages someone |
> | `WARN` | an anomaly the system recovered from | shows up in a review |
> | `INFO` | a lifecycle event: started, bound, shut down | always on in production |
> | `DEBUG` | diagnostics for a developer chasing a specific problem | off by default |
> | `TRACE` | firehose: per-item, per-frame detail | off, enabled surgically |
>
> Inflating levels is not cautious, it is destructive: an `ERROR` for a
> user's mistyped password trains the on-call to ignore `ERROR`, and the
> real outage arrives in a stream of noise. **Suggestion.**

```kotlin
// bad — a validation failure is not an operator's problem, and "loaded a
// config value" is not a lifecycle event
logger.error("invalid email address: {}", input)
logger.info("config key {} = {}", key, value)

// good
logger.debug("rejected registration: invalid email {}", input)
logger.info("started on port {} (profile {})", port, profile)
logger.warn("payment gateway timed out, retrying ({}/{})", attempt, maxAttempts)
logger.error("payment gateway unreachable after {} attempts", maxAttempts, e)
```

## 31.7 Pass the exception object itself as the last argument; never log only `e.message`.

> Why? SLF4J treats a trailing `Throwable` specially — it renders the full
> stack trace, and every structured appender extracts the exception type,
> message, and cause chain into their own fields. `e.message` throws all of
> that away and leaves a line like `error: null`, because plenty of
> exceptions carry no message at all: `NullPointerException`,
> `IndexOutOfBoundsException`, and every exception constructed from another
> without one. Without the stack trace, the log tells you something failed
> and nothing about where. **Suggestion.**

```kotlin
// bad — renders "sync failed: null" and loses the entire cause chain
catch (e: SQLException) {
    logger.error("sync failed: ${e.message}")
}

// bad — the exception is consumed as a {} argument, so no stack trace
catch (e: SQLException) {
    logger.error("sync failed: {}", e.toString())
}

// good — trailing Throwable: full stack trace and cause chain
catch (e: SQLException) {
    logger.error("sync failed for tenant {}", tenantId, e)
}
```

## 31.8 Never call `printStackTrace()`.

> Why? It writes to `System.err`, bypassing the logging pipeline exactly like
> `println` in §31.1, with the added problem that it carries no context at
> all — no logger name, no correlation id, no message saying what was being
> attempted. In a container it lands interleaved with unrelated stderr output
> and in a structured-logging setup it appears as dozens of unparseable
> lines. It is almost always the residue of an IDE-generated `catch` block
> that nobody replaced.
> **Violation — enforced by `detekt/PrintStackTrace`.**

```kotlin
// bad — IDE-generated catch block, shipped
try {
    reindex()
} catch (e: IOException) {
    e.printStackTrace()
}

// good
try {
    reindex()
} catch (e: IOException) {
    logger.error("reindex failed for shard {}", shardId, e)
}
```

## 31.9 Log a failure exactly once, where it is handled — never log and rethrow.

> Why? Logging and rethrowing produces the same failure at every level of the
> stack, so one incident yields five stack traces with five different
> messages and no indication which is the real one. Worse, it hides the
> decision: the frame that logged clearly did not handle the problem, or it
> would not have rethrown. Either handle it — log, and recover — or
> propagate it and let the frame that actually decides do the logging, with
> the context that makes it useful. See
> [Chapter 24, Exceptions & `Result`](24-exceptions-and-result.md) for the
> full rule. **Suggestion** — the adjacent `detekt/SwallowedException` and
> `detekt/RethrowCaughtException` fire on related shapes.

```kotlin
// bad — the same failure logged three times on its way out
fun loadProfile(id: UserId): Profile =
    try {
        repository.find(id)
    } catch (e: SQLException) {
        logger.error("failed to load profile {}", id, e)
        throw e
    }

// good — add context by wrapping; let the boundary log
fun loadProfile(id: UserId): Profile =
    try {
        repository.find(id)
    } catch (e: SQLException) {
        throw ProfileUnavailableException("cannot load profile $id", e)
    }

// good — the boundary that decides, logs
@ExceptionHandler(ProfileUnavailableException::class)
fun handle(e: ProfileUnavailableException): ResponseEntity<ErrorBody> {
    logger.error("profile request failed", e)
    return ResponseEntity.status(503).body(ErrorBody("temporarily unavailable"))
}
```

## 31.10 Never log a credential, token, key, or piece of personal data.

> Why? A log line is the least-protected copy of any datum you hold: it is
> replicated to an aggregator, retained for months, readable by everyone with
> a dashboard, and frequently shipped to a third-party SaaS. A password, an
> API key, a bearer token, or a full card number in a log is a disclosure
> incident and, for personal data, a regulatory one — and redacting it after
> the fact means purging every downstream index. Log identifiers, not
> contents: a user id instead of an email, a token *hash* or last four
> characters instead of the token. **Suggestion.**

```kotlin
// bad — three separate incidents on one line
logger.info("auth ok: email={} token={} card={}", email, bearerToken, pan)

// good — identifiers and prefixes only
logger.info("auth ok: userId={} tokenPrefix={}", userId, bearerToken.take(6))
```

## 31.11 Redact in the type's `toString`, not at every call site — and remember `data class` generates one that prints everything.

> Why? §31.10 is unenforceable if it depends on every developer remembering
> at every call site. Put the guarantee in the type: a
> [value class](12-value-classes.md) or a class with an overridden
> `toString` cannot leak, no matter who logs it. The specific Kotlin hazard
> is that a `data class` **generates** a `toString` containing every
> component, so `logger.info("registering {}", request)` prints the password
> that a `RegistrationRequest` happens to carry — with no code anywhere that
> mentions the password. See
> [Chapter 11, Data Classes](11-data-classes.md). **Suggestion.**

```kotlin
// bad — the generated toString prints the password; nothing at the call site
// reveals that
data class RegistrationRequest(
    val email: String,
    val password: String,
)

logger.info("registering {}", request)

// good — the secret is a type that cannot render itself
@JvmInline
value class Secret(private val value: String) {
    fun reveal(): String = value

    override fun toString(): String = "Secret(***)"
}

data class RegistrationRequest(
    val email: String,
    val password: Secret,
)

// good — or override toString on the carrier itself
data class RegistrationRequest(
    val email: String,
    val password: String,
) {
    override fun toString(): String = "RegistrationRequest(email=$email, password=***)"
}
```

## 31.12 Do not log per item inside a loop; log the aggregate.

> Why? A log line per element turns an operation over ten thousand rows into
> ten thousand lines, which costs I/O in the hot path, drowns the surrounding
> context, and — with most aggregators charging by volume — costs actual
> money. The information a reader wants is almost never "row 4,712 was
> processed"; it is "processed 10,000 rows, 3 failed, here are the three". If
> you genuinely need per-item detail, it is `TRACE` (§31.6), off by default.
> **Suggestion.**

```kotlin
// bad — one line per row, at INFO
orders.forEach { order ->
    logger.info("processing order {}", order.id)
    process(order)
}

// good — one line, with the outcome and the failures named
val failures = orders.mapNotNull { order ->
    runCatching { process(order) }.exceptionOrNull()?.let { order.id to it }
}
logger.info("processed {} orders, {} failed", orders.size, failures.size)
failures.forEach { (id, e) -> logger.warn("order {} failed", id, e) }
```

## 31.13 Set MDC values in a filter and always clear them, using `try`/`finally` or `MDC.putCloseable`.

> Why? MDC is backed by a `ThreadLocal`, and application servers reuse
> threads. A correlation id left in the MDC after a request finishes is
> attached to the *next* request that lands on that thread, which produces
> log lines correctly formatted, plausibly timed, and attributed to the wrong
> user — the worst class of observability bug, because it actively misleads
> an investigation. Every `MDC.put` needs a matching removal on every path,
> which means `finally`, or the `MDC.putCloseable` handle used with Kotlin's
> `use`. **Suggestion.**

```kotlin
// bad — an exception (or an early return) leaks the id onto the next request
// that reuses this thread
fun doFilter(request: HttpServletRequest, chain: FilterChain) {
    MDC.put("correlationId", request.correlationId())
    chain.doFilter(request, response)
    MDC.remove("correlationId")
}

// good — cleared on every path
fun doFilter(request: HttpServletRequest, chain: FilterChain) {
    MDC.putCloseable("correlationId", request.correlationId()).use {
        chain.doFilter(request, response)
    }
}
```

## 31.14 MDC does not follow a coroutine across a dispatcher — use `MDCContext` from `kotlinx-coroutines-slf4j`.

> Why? MDC is thread-local; a coroutine is not bound to a thread. The moment
> work suspends and resumes on another thread — a `withContext(Dispatchers.IO)`,
> a `launch`, a dispatcher hop inside a library — the MDC is whatever that
> thread last had, which is usually empty and occasionally another request's.
> The fix is `MDCContext`, a `ThreadContextElement` that captures the current
> MDC map and reinstalls it on every resumption. Two details from
> [its documentation](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-slf4j/kotlinx.coroutines.slf4j/-m-d-c-context/)
> matter: it captures at *construction*, so construct it where the MDC is
> populated; and updates made with `MDC.put` *inside* a coroutine are lost at
> the next suspension unless you capture them with a fresh
> `withContext(MDCContext())`. See
> [Chapter 34](34-dispatchers-and-context.md). **Suggestion.**

```kotlin
// bad — the correlation id set by the servlet filter is gone the moment this
// dispatches to the IO pool
suspend fun handle(request: Request): Response = withContext(Dispatchers.IO) {
    logger.info("handling {}", request.id)   // no correlationId in the MDC
    repository.load(request.id)
}

// good — capture the caller's MDC and carry it across every resumption
// build.gradle.kts:
//   implementation("org.jetbrains.kotlinx:kotlinx-coroutines-slf4j:1.10.2")
suspend fun handle(request: Request): Response =
    withContext(Dispatchers.IO + MDCContext()) {
        logger.info("handling {}", request.id)   // correlationId present
        repository.load(request.id)
    }
```

## 31.15 Attach machine-readable fields as key-value pairs, not by concatenating them into the message.

> Why? A message like `"order 4711 for tenant acme failed after 3 attempts"`
> is readable by a human and opaque to everything else: filtering on tenant
> requires a regex, and the regex breaks the first time someone reorders the
> sentence. SLF4J 2.0's `addKeyValue` puts each datum in its own field, so
> the aggregator can index and filter on it, while the human-readable message
> stays short and stable. Keep the message a constant and the variables in
> fields — that also makes log lines group correctly when the aggregator
> clusters by message template. **Suggestion.**

```kotlin
// bad — every value is trapped inside prose
logger.warn("order $orderId for tenant $tenantId failed after $attempts attempts")

// good — indexable fields, stable message
logger.atWarn()
    .addKeyValue("orderId", orderId)
    .addKeyValue("tenantId", tenantId)
    .addKeyValue("attempts", attempts)
    .log("order processing failed")
```

## 31.16 Do not inject a logger as a constructor parameter or declare it as a bean.

> Why? A logger is not a dependency — it is a static, per-class fact with no
> lifecycle, no configuration a caller should choose, and no meaningful test
> double. Putting it in the constructor pollutes every construction site,
> every test, and every DI declaration, and it invites a caller to pass the
> *wrong* logger, which silently misattributes lines. Declare it as a
> `private val` next to the class (§31.2) and leave the constructor for
> things that vary. **Suggestion.**

```kotlin
// bad — every test and every wiring site now has to supply a logger
@Service
class OrderService(
    private val repository: OrderRepository,
    private val logger: Logger,
)

// good
private val logger = KotlinLogging.logger {}

@Service
class OrderService(
    private val repository: OrderRepository,
)
```

## 31.17 A logging call must never change behaviour: no side effects, no possibility of throwing.

> Why? Logging is meant to observe the system, not participate in it. An
> argument expression that mutates state, opens a connection, or calls a
> method that can throw makes the program behave differently depending on the
> configured log level — the hardest class of bug to reproduce, because
> turning on `DEBUG` to investigate changes the thing you are investigating.
> Under a lazy API (§31.4) it is worse: the expression runs only *sometimes*.
> The specific Kotlin hazard is calling `toString()` on a lazily-initialised
> or nullable-chained value inside the lambda, where an exception is thrown
> from inside the logging framework and may be swallowed by its own error
> handling. **Suggestion.**

```kotlin
// bad — the counter only increments when DEBUG is on, and next() consumes an
// element that the loop below then never sees
logger.debug { "next item: ${iterator.next()} (seen ${counter.incrementAndGet()})" }

// bad — throws from inside the logging call if the chain is absent
logger.info("shipping to {}", order.customer.address.postcode)

// good — pure, total expressions only
logger.debug { "next item: ${peeked.orEmpty()} (seen ${counter.get()})" }
logger.info("shipping to {}", order.customer?.address?.postcode ?: "unknown")
```
