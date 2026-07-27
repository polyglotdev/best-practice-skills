<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 30. Logging

Logs are the only diagnostic that survives the incident. Nobody attaches a
debugger to production, and by the time a report arrives the process has
been restarted; what is left is whatever the code wrote down. That makes a
log statement a piece of API design — its audience is an operator at 03:00
who has never read the method it came from, and its contract is that the
line contains enough identifiers to find the next thing to look at.

Two failure modes dominate. The first is under-logging: a `catch` that
swallows the cause, or a failure path that returns an error code and writes
nothing, leaving an incident with no evidence at all. The second is
over-logging: the same failure written at four layers, a `DEBUG` line inside
a hot loop, or a request body dumped whole — which fills the retention
window, buries the useful line, and occasionally exfiltrates a password
into a log aggregator that a hundred people can read.

This chapter covers the facade choice, the mechanics of parameterized
logging, level discipline, exception logging, the handle-errors-once rule
as it applies to logs, contextual logging with the MDC, and what must never
be written down. It draws on the
[SLF4J user manual](https://www.slf4j.org/manual.html), the
[`LoggingEventBuilder`](https://www.slf4j.org/apidocs/org/slf4j/spi/LoggingEventBuilder.html)
fluent API added in SLF4J 2.0, and Google Java Style
[§6.2 Caught exceptions](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions).
Exception *design* is [Chapter 24](24-exceptions.md); this chapter covers
only what happens at the moment one is written down. Message formatting
generally is [Chapter 21](21-strings-and-text-blocks.md) — SLF4J
placeholders are not `String.format` and the two must never be mixed.

**Tool alignment:** Error Prone's `SystemOut` and `CatchAndPrintStackTrace`
catch the two most common violations mechanically, `SystemExitOutsideMain`
catches the worst version of "log and die", and Checkstyle's
`RegexpSinglelineJava` and `IllegalImport` can ban a concrete logging API
or `printStackTrace` project-wide. Everything about *what* to write is a
judgement call and is labeled **Suggestion**.

## 30.1 Depend on the SLF4J API, and let the deployable choose the implementation.

> Why? A library that compiles against Logback, Log4j 2, or
> `java.util.logging` forces that choice on every application that consumes
> it, and two libraries with different choices produce two log files with
> two formats and no shared correlation. SLF4J is a facade: your code
> depends on `org.slf4j:slf4j-api` only, and the application at the top of
> the dependency tree puts exactly one binding on the runtime classpath. Do
> not ship a binding from a library — a `logback-classic` dependency in a
> library's `implementation`/`compile` scope is a bug that surfaces as a
> duplicate-binding warning in somebody else's build. **Suggestion.**

```java
// bad — a library hard-wires the implementation for all of its consumers
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.LoggerContext;

// good — the facade only; the application picks the binding
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
```

## 30.2 Never write to `System.out` or `System.err` from library or service code.

> Why? Standard streams bypass everything the logging configuration
> provides: no level, no timestamp, no logger name, no correlation id, no
> appender routing, and no way to turn the output off without a redeploy.
> They are also synchronised and unbuffered per line, so a chatty
> `System.out.println` on a hot path serialises every thread that reaches
> it. The only legitimate uses are a `main` method in a CLI whose *output*
> is the product, and a build-time tool.
> **Violation — enforced by Error Prone `SystemOut`.**

```java
// bad — invisible to the log pipeline and impossible to switch off
public void process(Order order) {
  System.out.println("processing " + order.id());
  try {
    handler.handle(order);
  } catch (HandlerException e) {
    e.printStackTrace();
  }
}

// good
public void process(Order order) {
  log.debug("processing order id={}", order.id());
  try {
    handler.handle(order);
  } catch (HandlerException e) {
    log.error("order processing failed id={}", order.id(), e);
  }
}
```

## 30.3 Declare the logger as a `private static final` field named for its enclosing class.

> Why? The logger name is what the operator filters on, so it must be the
> fully qualified class name — passing the class literal gets that right
> automatically and survives renames and copy-paste, where a hard-coded
> string does not. `static` means one instance per class rather than one
> per object, which matters for any type allocated in a loop. `private`
> keeps it out of the subclass's namespace, where an inherited logger would
> report the *parent's* name for every line the child writes.
> **Suggestion.**

```java
// bad — a hard-coded name that survives a copy-paste into the wrong class,
// and a per-instance field
public class OrderService {
  private final Logger log = LoggerFactory.getLogger("OrderService");
}

// bad — protected, so every subclass logs under the parent's name
public abstract class BaseHandler {
  protected static final Logger log = LoggerFactory.getLogger(BaseHandler.class);
}

// good
public class OrderService {
  private static final Logger log = LoggerFactory.getLogger(OrderService.class);
}
```

## 30.4 Use `{}` placeholders — never string concatenation, and never `String.format`.

> Why? The placeholder form defers *message assembly* until after the level
> check, so a disabled `DEBUG` line costs a boolean test instead of
> building a `String` that is immediately discarded. Concatenation builds
> that string unconditionally, at every call, on every hot path.
> `String.format` is worse than concatenation: it parses the format string
> at runtime *and* boxes every argument into an `Object[]`, and mixing
> `%s` with a logging method that expects `{}` produces a message with the
> literal `%s` left in it. Be precise about the benefit — the *arguments*
> are still evaluated eagerly (see §30.10); it is the formatting that is
> deferred. **Suggestion.**

```java
// bad — builds the string even when DEBUG is off
log.debug("resolved user " + user.getId() + " in tenant " + tenant.getName());

// bad — %s is not an SLF4J placeholder; the message prints "%s" verbatim
log.info(String.format("resolved user %s", user.getId()));
log.info("resolved user %s", user.getId());

// good
log.debug("resolved user id={} tenant={}", user.getId(), tenant.getName());
```

## 30.5 Pass the exception as the final argument, not `e.getMessage()`.

> Why? SLF4J treats a trailing `Throwable` with no matching placeholder as
> the exception to render, which gives the full stack trace *and* the
> `caused by` chain. `e.getMessage()` gives one line, usually the least
> informative one — a `NullPointerException` has a message of `null` in
> older code, and a wrapped `SQLException` puts the actionable detail in the
> cause, not the outermost message. An operator cannot find the failing
> line from a message alone. Note the trailing throwable must genuinely have
> no `{}` of its own; adding one turns it back into a formatted argument.
> **Suggestion.**

```java
// bad — one line of text, no stack, no cause chain
} catch (SQLException e) {
  log.error("query failed: {}", e.getMessage());
}

// bad — the throwable is consumed by the placeholder, so no stack is printed
} catch (SQLException e) {
  log.error("query failed for tenant={} cause={}", tenantId, e);
}

// good — placeholders for context, the throwable last and unmatched
} catch (SQLException e) {
  log.error("query failed tenant={} statement={}", tenantId, statementId, e);
}
```

## 30.6 Never call `printStackTrace`.

> Why? It writes to `System.err` (see §30.2), so the trace escapes the
> logging pipeline entirely — no level, no correlation id, and no
> aggregation. In a containerised deployment it interleaves with the real
> log stream at line granularity, so a multi-line trace from one thread
> gets shredded across another thread's output and becomes unreadable. It
> is also the standard shape of a swallowed exception: `printStackTrace`
> followed by falling through to the next statement discards the failure
> while looking like it handled it.
> **Violation — enforced by Error Prone `CatchAndPrintStackTrace`.**

```java
// bad
} catch (IOException e) {
  e.printStackTrace();
}

// good — logged through the pipeline, and the method still fails
} catch (IOException e) {
  throw new ConfigLoadException("unable to read config from " + path, e);
}
```

## 30.7 Choose the level by who has to act on the line, not by how the author felt about it.

> Why? Levels are a routing decision, and the routing only works if the
> whole codebase agrees on the meaning. If `ERROR` is used for anything
> unexpected, the on-call alert fires on things nobody can act on and gets
> muted, which is how a real outage goes unnoticed. The operational
> definitions are: **ERROR** — an operator must do something, now.
> **WARN** — an anomaly the system recovered from, worth a dashboard but
> not a page. **INFO** — a lifecycle or business event a reader would want
> in a normal-day log. **DEBUG** — developer diagnostics, off in
> production by default. **TRACE** — firehose detail, enabled on one class
> for one investigation. In particular, a failure the caller is expected to
> handle is not an `ERROR` in the callee. **Suggestion.**

```java
// bad — a validation failure is the caller's normal path, not an incident
if (!request.isValid()) {
  log.error("invalid request: {}", request);
  return Result.rejected();
}

// bad — a lifecycle event buried at DEBUG, invisible when it matters
log.debug("started listener on port={}", port);

// good
if (!request.isValid()) {
  log.debug("rejecting invalid request id={} reason={}", request.id(), request.reason());
  return Result.rejected();
}

log.info("started listener port={}", port);
log.warn("retrying upstream call attempt={} of={}", attempt, maxAttempts);
log.error("failed to acquire database connection after={} attempts", maxAttempts, e);
```

## 30.8 Log a failure once, at the layer that decides what to do about it.

> Why? Logging and rethrowing at every layer produces N copies of one
> incident, each with a different stack depth, so the operator cannot tell
> whether they are looking at one failure or N and the retention window
> fills with duplicates. The rule is the same one
> [Chapter 24](24-exceptions.md) states for exception handling: an error is
> *handled* exactly once, and logging is a form of handling. A layer that
> rethrows adds context to the exception ([§24](24-exceptions.md)) and
> writes nothing; the layer that finally swallows or converts it writes the
> line. **Suggestion.**

```java
// bad — the same failure logged three times on the way up
} catch (SQLException e) {
  log.error("query failed", e);
  throw new RepositoryException(e);
}
// ... in the service
} catch (RepositoryException e) {
  log.error("could not load order", e);
  throw new OrderLookupException(e);
}

// good — lower layers add context and rethrow; only the handler logs
} catch (SQLException e) {
  throw new RepositoryException("loading order id=" + id, e);
}
// ... at the boundary that decides the outcome
} catch (RepositoryException e) {
  log.error("order lookup failed id={}", id, e);
  return Response.serverError();
}
```

## 30.9 Never log credentials, tokens, keys, personal data, or whole request and response bodies.

> Why? A log line is copied to an aggregator, indexed, retained for months,
> and readable by everyone with dashboard access — a far wider audience
> than the process that held the secret. A logged bearer token is a live
> credential sitting in a search index; logged personal data turns the log
> store into a system of record subject to deletion requests it cannot
> honour. Whole-body logging is the usual route in, because the body
> contains the password field nobody remembered was there. Log identifiers,
> sizes, and outcomes; never contents. If a value must be traceable, log a
> stable hash or the last four characters, deliberately.
> **Suggestion.**

```java
// bad — a live credential and a full personal record, retained for months
log.info("authenticating with token={}", bearerToken);
log.debug("received payload={}", objectMapper.writeValueAsString(request));

// good — identity and shape, not contents
log.info("authenticating subject={} tokenId={}", subject, claims.getId());
log.debug("received payload type={} bytes={}", request.getClass().getSimpleName(), size);
```

## 30.10 Guard genuinely expensive arguments — the placeholder form defers formatting, not evaluation.

> Why? This is the point most style guides get wrong.
> `log.debug("state={}", buildStateSnapshot())` calls `buildStateSnapshot()`
> before the logging method is entered, because Java evaluates arguments
> eagerly; the placeholder only saves the concatenation. For a cheap getter
> that does not matter and a guard would be noise. For anything that
> serialises, queries, or allocates, wrap the call site in
> `isDebugEnabled()` — or use SLF4J 2.0's fluent builder, whose
> `addArgument(Supplier<?>)` genuinely defers the computation.
> **Suggestion.**

```java
// bad — serialises the whole object on every call, even with DEBUG off
log.debug("state={}", objectMapper.writeValueAsString(snapshot));

// good — the level check happens before the expensive call
if (log.isDebugEnabled()) {
  log.debug("state={}", objectMapper.writeValueAsString(snapshot));
}

// good — SLF4J 2.0 fluent API, deferred via a Supplier
log.atDebug().addArgument(() -> objectMapper.writeValueAsString(snapshot)).log("state={}");
```

## 30.11 Write log messages for operators, and put the identifiers in them.

> Why? The reader is not the author and does not have the source open. A
> message like `"failed"` or `"something went wrong"` tells them nothing;
> neither does a message that names a local variable they cannot see. What
> makes a line useful is the *joinable* data: the entity id, the tenant,
> the correlation id, the attempt number, the upstream host. Keep the
> literal prefix stable so it can be grepped and alerted on, and put the
> varying data in placeholders rather than in the prose. Never localise a
> log message — it is not user-facing text, and a translated message
> destroys every runbook and alert rule that matched it.
> **Suggestion.**

```java
// bad — unsearchable, unjoinable, and the interesting values are missing
log.error("Something went wrong!");
log.warn("Retrying...");
log.info(messages.getString("shutdown.complete")); // localised

// good — stable prefix, joinable identifiers
log.error("order settlement failed orderId={} tenantId={} gateway={}", id, tenant, gateway, e);
log.warn("upstream retry scheduled host={} attempt={} backoffMs={}", host, attempt, backoff);
log.info("shutdown complete durationMs={}", elapsed.toMillis());
```

## 30.12 Put correlation context in the MDC, and always remove it in a `finally`.

> Why? Repeating `requestId` in every placeholder is noise and gets
> forgotten on exactly the line that matters. The MDC attaches the value to
> the thread once, and the appender adds it to every line. The hazard is
> that the MDC is thread-local and pooled threads are reused: a key left
> behind after a request completes attaches to the *next* request on that
> thread, so one user's trace id ends up on another user's log lines.
> Clearing it is not optional and must survive an exception — use
> `MDC.putCloseable` in try-with-resources, or an explicit `finally`. Note
> that MDC does not propagate to threads you spawn, virtual or platform
> ([Chapter 27](27-virtual-threads.md)); copy it explicitly.
> **Suggestion.**

```java
// bad — an exception skips the remove, and the id leaks onto the next
// request handled by this pooled thread
MDC.put("requestId", requestId);
handle(request);
MDC.remove("requestId");

// good — try-with-resources removes the key on every path
try (MDC.MDCCloseable ignored = MDC.putCloseable("requestId", requestId)) {
  handle(request);
}

// good — explicit finally where several keys are set
MDC.put("requestId", requestId);
MDC.put("tenantId", tenantId);
try {
  handle(request);
} finally {
  MDC.remove("requestId");
  MDC.remove("tenantId");
}
```

## 30.13 Log key-value pairs rather than burying data in prose.

> Why? Logs are parsed far more often than they are read. A message like
> `"Order 4821 for tenant acme failed after 3 attempts"` requires a regex
> per field and breaks the moment the wording changes, while
> `orderId=4821 tenantId=acme attempts=3` is trivially splittable and, with
> SLF4J 2.0's `addKeyValue`, becomes real structured fields in a JSON
> appender rather than substrings of a message. Keep the key names
> consistent across the codebase — `orderId` in one class and `order_id` in
> another means two dashboard queries where there should be one.
> **Suggestion.**

```java
// bad — every field needs a regex, and the regex breaks on rewording
log.warn("Order " + orderId + " for tenant " + tenant + " failed after 3 attempts");

// good — splittable pairs
log.warn("order attempt exhausted orderId={} tenantId={} attempts={}", orderId, tenant, 3);

// good — genuinely structured, when the appender supports it
log.atWarn()
    .addKeyValue("orderId", orderId)
    .addKeyValue("tenantId", tenant)
    .addKeyValue("attempts", 3)
    .log("order attempt exhausted");
```

## 30.14 Never log unconditionally inside a hot loop — aggregate or sample.

> Why? A `DEBUG` line inside a loop over a million rows is a million I/O
> operations and a million allocations, and even with the level disabled it
> is a million level checks plus a million evaluations of whatever is in the
> argument list (§30.10). Worse,
> when someone enables that level to investigate an unrelated problem, the
> appender becomes the bottleneck and the system's behaviour changes under
> observation. Log the summary after the loop, or emit every Nth iteration,
> or use a metric instead — a counter is the right tool for "how many", and
> a log line is the wrong one. **Suggestion.**

```java
// bad — one line per row when DEBUG is on; when it is off, the level check
// and the argument evaluation still run once per row
for (Row row : rows) {
  log.debug("processing row={}", row);
  process(row);
}

// good — a summary at the end, and a metric for the count
long failures = 0;
for (Row row : rows) {
  if (!process(row)) {
    failures++;
  }
}
log.info("batch complete rows={} failures={} durationMs={}", rows.size(), failures, elapsed);
```

## 30.15 Do not log method entry and exit as a substitute for tracing.

> Why? Entry/exit logging doubles the volume of every log file to
> reconstruct a call graph that a tracer already produces, with spans,
> timings, and cross-service links that logs cannot express. It also
> encodes the call structure into the log, so an ordinary refactor changes
> the output and breaks whatever was grepping it. If you need to see the
> path a request took, instrument it; if you need to see that a specific
> boundary was crossed, log the boundary and the outcome, not the entry.
> **Suggestion.**

```java
// bad — noise proportional to the call graph, obsolete after any refactor
public Order load(OrderId id) {
  log.debug("entering load({})", id);
  Order order = repository.find(id);
  log.debug("exiting load, returning {}", order);
  return order;
}

// good — the outcome at the boundary that matters
public Order load(OrderId id) {
  Order order = repository.find(id);
  if (order == null) {
    log.info("order lookup miss orderId={}", id);
  }
  return order;
}
```

## 30.16 A logging call must never change behaviour or throw.

> Why? Logging is diagnostics and must be inert. The two ways it stops
> being inert are a `toString()` with a side effect or an exception — a
> lazy collection that triggers a database query when rendered, or a
> `toString` that dereferences a nullable field and throws an NPE *inside*
> the `catch` block that was trying to report the original failure, losing
> it entirely. The second is arithmetic in the argument list. If a value is
> expensive or fragile to render, render it defensively at the call site.
> **Suggestion.**

```java
// bad — order.toString() renders a lazily loaded collection, so enabling
// DEBUG issues a query per line and can throw inside the catch
} catch (PaymentException e) {
  log.error("payment failed for {}", order, e);
}

// good — log identifiers, which cannot trigger loading or throw
} catch (PaymentException e) {
  log.error("payment failed orderId={} amountMinor={}", order.id(), order.amountMinor(), e);
}
```

## 30.17 When a `catch` block takes no action, say why in a comment — and prefer logging to silence.

> Why?
> [Google Java Style §6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions):
> "It is very rarely correct to do nothing in response to a caught
> exception. (Typical responses are to log it, or if it is considered
> 'impossible', rethrow it as an `AssertionError`.) When it truly is
> appropriate to take no action whatsoever in a catch block, the reason
> this is justified is explained in a comment." An empty `catch` is
> indistinguishable from an oversight, so the comment is what tells the
> next reader it was deliberate. A `DEBUG` line costs nothing and turns a
> silent branch into a traceable one.
> **Violation — enforced by Checkstyle `EmptyCatchBlock`.**

```java
// bad — an empty catch with no comment: indistinguishable from a mistake
try {
  registry.deregister(id);
} catch (RegistryException e) {
}

// good — the intent is stated, and the branch is traceable
try {
  return Optional.of(parser.parse(raw));
} catch (ParseException e) {
  // Unparseable input is an expected caller error, reported via the empty
  // Optional; DEBUG keeps the cause available when investigating.
  log.debug("discarding unparseable input length={}", raw.length(), e);
  return Optional.empty();
}
```

## 30.18 Configure logging declaratively, and never reconfigure the framework from application code.

> Why? Programmatic configuration ties the log format, the levels, and the
> appenders to a redeploy, which is precisely what you cannot do during an
> incident. It also requires importing the implementation, breaking §30.1.
> A declarative `logback-spring.xml`, `log4j2.xml`, or Spring Boot
> `logging.level.*` property can be overridden by environment variable at
> start-up and, with most implementations, changed at runtime. Application
> code should not know which implementation is present, let alone mutate
> it. **Suggestion.**

```java
// bad — imports the implementation and hard-codes an operational decision
LoggerContext context = (LoggerContext) LoggerFactory.getILoggerFactory();
context.getLogger("com.example").setLevel(Level.DEBUG);

// good — application code knows only the facade; the level is configuration
private static final Logger log = LoggerFactory.getLogger(OrderService.class);

// application.yaml, overridable per environment without a rebuild:
//   logging:
//     level:
//       com.example: ${APP_LOG_LEVEL:INFO}
```

## 30.19 Never let a log line be the only handling an error gets.

> Why? "Log and continue" leaves the system in the state that caused the
> failure while telling the operator it was noticed, which is worse than
> crashing — the process keeps serving requests from a corrupt cache, or
> commits half a transaction, and the log line scrolls past. A caught
> exception must result in a recovery, a translated failure returned to the
> caller, or a rethrow ([Chapter 24](24-exceptions.md)). Logging is how the
> decision is *recorded*, not what the decision is. The pathological
> version, calling `System.exit` from inside application code so the log
> line is the last thing anyone sees, also makes the class untestable.
> **Violation for the exit case — enforced by Error Prone
> `SystemExitOutsideMain`.**

```java
// bad — the cache is now inconsistent and the method reports success
} catch (CacheException e) {
  log.error("cache update failed key={}", key, e);
}
return true;

// bad — untestable, and skips every shutdown hook
} catch (CacheException e) {
  log.error("cache update failed key={}", key, e);
  System.exit(1);
}

// good — logged once, and the failure is actually propagated
} catch (CacheException e) {
  log.warn("cache update failed, falling back to source key={}", key, e);
  return loadFromSource(key);
}
```
