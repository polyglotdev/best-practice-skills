<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 44. Spring: Web Layer & Coroutines

This is a **delta chapter**. Everything Spring's web layer requires of a Java
service it also requires of a Kotlin one, and none of it is repeated here.
Thin controllers, dedicated request and response DTOs, `@Valid` on every
`@RequestBody`, one `@RestControllerAdvice`, RFC 9457 `ProblemDetail` bodies,
correct status codes, idempotency keys, pagination envelopes, declarative
`@HttpExchange` clients, and central CORS configuration are all in
**`best-practice-java` Chapter 34, "Spring: Web Layer"** — read it first and
apply it unchanged. What follows is only what Kotlin and coroutines change.

The Kotlin-specific surface is small but sharp: `suspend` handler functions
and what Spring actually does with them, `Flow` as a streaming return type,
the `kotlinx-coroutines-reactor` bridge that makes any of it work, the
`await*` extensions on `WebClient` and the functional API, the `coRouter`
DSL, and the three places Kotlin's type system collides with Spring's
reflective binding: `data class` DTOs and Jackson, annotation use-site
targets and Jakarta validation, and `value class` parameters.

Rules here draw on
[Spring Framework: Coroutines](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html),
[Spring Boot: Kotlin Support](https://docs.spring.io/spring-boot/reference/features/kotlin.html),
and the
[kotlinx.coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html).
Cancellation semantics are [Chapter 35](35-cancellation-and-timeouts.md),
dispatcher choice is [Chapter 34](34-dispatchers-and-context.md), and the
general coroutine anti-patterns this chapter specialises are
[Chapter 40](40-coroutine-anti-patterns.md).

**Tool alignment:** detekt's coroutines ruleset covers two of these
mechanically and both are active by default — `RedundantSuspendModifier`
(§44.3) and `SuspendFunWithFlowReturnType` (§44.6). `GlobalCoroutineUsage`
covers part of §44.8 but ships inactive. Nothing in ktlint or detekt
understands Spring MVC, so every other rule below is a **Suggestion**.

## 44.1 Put `kotlinx-coroutines-reactor` on the classpath before you write your first `suspend` handler.

> Why? Spring adapts a suspending handler by turning it into a `Mono`, and it
> can only do that through the Reactor bridge. The
> [reference](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html)
> states the condition exactly: "Coroutines support is enabled when
> `kotlinx-coroutines-core` and `kotlinx-coroutines-reactor` dependencies are
> in the classpath." Neither arrives with `spring-boot-starter-web`, so a
> Kotlin MVC service that adds only `kotlinx-coroutines-core` compiles fine
> and fails at request time rather than at build time. **Suggestion.**

```kotlin
// bad — build.gradle.kts: the handler compiles, the request does not dispatch
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core")
}

// good
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor")
}
```

## 44.2 Mark a handler `suspend` only when the work it awaits is genuinely non-blocking.

> Why? On WebFlux, `suspend` is the whole point: the handler releases the
> event-loop thread at every suspension point. On Spring MVC it buys much
> less than it looks like it does. Spring MVC adapts the suspending handler
> to a `Mono` and completes the request through the Servlet async path, so
> the container thread is released — but only for as long as the body is
> genuinely suspended. A handler whose body is one `withContext(Dispatchers.IO)`
> around a JDBC call has not stopped blocking; it has moved the block from a
> Tomcat thread to an IO-dispatcher thread and added a context switch and an
> async dispatch on each side. That is a net loss unless the container's
> thread pool is the actual bottleneck. Reach for `suspend` on MVC when the
> handler awaits several independent remote calls concurrently, not because
> the codebase has decided every function is `suspend`. **Suggestion.**

```kotlin
// bad — cargo cult: one blocking JDBC read, wrapped, on a blocking stack.
// Two extra thread hops and a Servlet async dispatch buy nothing.
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse =
    withContext(Dispatchers.IO) { orderQueries.findById(id) }

// good — plain blocking handler on a blocking stack
@GetMapping("/orders/{id}")
fun get(@PathVariable id: UUID): OrderResponse = orderQueries.findById(id)

// good — suspend earns its keep: three remote calls overlap instead of queue
@GetMapping("/orders/{id}/dashboard")
suspend fun dashboard(@PathVariable id: UUID): DashboardResponse = coroutineScope {
    val order = async { orderClient.fetch(id) }
    val shipping = async { shippingClient.fetch(id) }
    val invoices = async { billingClient.fetchInvoices(id) }
    DashboardResponse(order.await(), shipping.await(), invoices.await())
}
```

## 44.3 Never mark a handler `suspend` when nothing in its body suspends.

> Why? A `suspend` modifier on a function that never suspends still costs the
> full adaptation: Spring wraps it in a `Mono`, the Servlet container starts
> and completes an async dispatch, and every test of that endpoint now has to
> deal with async dispatching (see [Chapter 46, §46.10](46-spring-testing-kotlin.md)).
> It also lies to the reader about the function's cost model. The modifier is
> a claim about behaviour, not a decoration.
> **Violation — enforced by `detekt/RedundantSuspendModifier`.**

```kotlin
// bad — nothing here suspends; detekt flags the modifier
@GetMapping("/health/version")
suspend fun version(): VersionResponse = VersionResponse(buildInfo.version)

// good
@GetMapping("/health/version")
fun version(): VersionResponse = VersionResponse(buildInfo.version)
```

## 44.4 Never block inside a WebFlux handler, and do not mistake `withContext(Dispatchers.IO)` for making it reactive.

> Why? A WebFlux server runs on a small fixed event-loop pool, usually one
> thread per core. A blocking call on one of those threads stalls every
> in-flight request on that thread, including requests that touch none of the
> blocking code — the failure is a dead process, not a slow endpoint. This is
> `best-practice-java` §34.20 restated in coroutine terms, and the Kotlin
> trap is specific: `withContext(Dispatchers.IO)` *does* keep the event loop
> free, so the code is correct, but it does not make the call non-blocking.
> You have bought a bounded thread pool, and `Dispatchers.IO` has a default
> parallelism of 64 — beyond that, requests queue. If a handler's real
> dependency is JDBC, WebFlux is the wrong stack for it; see
> [Chapter 34](34-dispatchers-and-context.md). **Suggestion.**

```kotlin
// bad — JDBC on the event loop; a handful of concurrent requests kill the server
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse =
    OrderResponse.from(jdbcOrderRepository.findById(id))

// bad — .block() on the event loop is the same failure with extra steps
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse =
    inventoryWebClient.get().uri("/stock/{id}", id).retrieve().bodyToMono<OrderResponse>().block()!!

// good — the block is isolated, and the ceiling is explicit
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse =
    withContext(Dispatchers.IO) { OrderResponse.from(jdbcOrderRepository.findById(id)) }
```

## 44.5 Return `Flow<T>` from a handler only when you also declare a streaming media type.

> Why? The
> [reference](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html)
> maps `fun handler(): Flux<T>` to `fun handler(): Flow<T>`, and Spring
> supports `Flow` return values in both MVC and WebFlux annotated
> controllers. But under the default `application/json` — a non-streaming
> media type — the encoder has to produce one well-formed JSON array, so the
> elements are aggregated and the response is a single array with no
> per-element framing. You have paid for a streaming pipeline and delivered a
> batch response. Declare `application/x-ndjson` (`MediaType.APPLICATION_NDJSON_VALUE`) for
> machine consumers or `text/event-stream`
> (`MediaType.TEXT_EVENT_STREAM_VALUE`) for browsers, so each element is
> framed and flushed on its own. **Suggestion.**

```kotlin
// bad — a streaming source rendered as one JSON array; nothing streams
@GetMapping("/orders/events")
fun events(): Flow<OrderEvent> = orderEvents.stream()

// good — newline-delimited JSON: one framed element per emission
@GetMapping("/orders/events", produces = [MediaType.APPLICATION_NDJSON_VALUE])
fun events(): Flow<OrderEvent> = orderEvents.stream()

// good — server-sent events for a browser consumer
@GetMapping("/orders/events", produces = [MediaType.TEXT_EVENT_STREAM_VALUE])
fun events(): Flow<ServerSentEvent<OrderEvent>> =
    orderEvents.stream().map { event ->
        ServerSentEvent.builder(event).id(event.id.toString()).event("order").build()
    }
```

## 44.6 Never declare a `suspend` function that returns a `Flow`.

> Why? A `Flow` is already cold and already asynchronous — subscribing to it
> is what does the work, so there is nothing for the `suspend` modifier to
> buy. What it costs is real: the caller must be in a coroutine merely to
> *obtain* the flow, before collecting anything, which forces a suspension
> point into code that only wanted to wire a pipeline. Spring's own
> repository conventions follow this rule, returning `Flow<T>` from plain
> functions and reserving `suspend` for single values (see
> [Chapter 45, §45.13](45-spring-data-and-transactions.md)).
> **Violation — enforced by `detekt/SuspendFunWithFlowReturnType`.**

```kotlin
// bad — the caller must suspend just to build the pipeline
@GetMapping("/orders/events", produces = [MediaType.APPLICATION_NDJSON_VALUE])
suspend fun events(): Flow<OrderEvent> = orderEvents.stream()

// good
@GetMapping("/orders/events", produces = [MediaType.APPLICATION_NDJSON_VALUE])
fun events(): Flow<OrderEvent> = orderEvents.stream()
```

## 44.7 Never catch `Exception` or `Throwable` inside a `suspend` handler.

> Why? Cancellation in coroutines is delivered as a `CancellationException`
> thrown from a suspension point. When a client disconnects mid-request,
> WebFlux cancels the reactive chain and the handler's coroutine is
> cancelled — so a broad `catch (e: Exception)` intercepts the cancellation
> signal, swallows it, and converts a client that hung up into a logged 500
> and a stack trace your on-call engineer will chase. Worse, swallowing it
> breaks the structured-concurrency contract: children that should have
> stopped keep running. Catch the specific exception you can actually handle,
> and let everything else reach the `@RestControllerAdvice`. See
> [Chapter 35](35-cancellation-and-timeouts.md) for the general rule.
> **Violation — enforced by `detekt/TooGenericExceptionCaught`.**
> `detekt/SwallowedException` covers the adjacent case where the caught
> exception is neither used nor rethrown, which is not quite this one.

```kotlin
// bad — a client disconnect becomes a 500 with a fabricated error body
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse =
    try {
        orderClient.fetch(id)
    } catch (e: Exception) {
        logger.error("order lookup failed", e)
        OrderResponse.unavailable(id)
    }

// good — handle what you can name; rethrow cancellation untouched
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse =
    try {
        orderClient.fetch(id)
    } catch (e: OrderServiceTimeoutException) {
        logger.warn("order lookup timed out id={}", id, e)
        throw OrderTemporarilyUnavailableException(id, e)
    }
```

## 44.8 Never launch fire-and-forget work from a handler with `GlobalScope` or a freshly constructed `CoroutineScope`.

> Why? `GlobalScope` has no lifetime, no parent, and no cancellation: work
> launched into it survives the request, survives shutdown attempts, and
> reports its failures nowhere. A `CoroutineScope(Dispatchers.IO)` created
> inline is the same defect wearing a different name — nothing ever cancels
> it, so every request leaks a scope. Both also silently drop exceptions,
> since no supervisor is watching. If the work must outlive the request, give
> it an application-scoped bean that owns a scope with a real lifecycle
> (cancelled in `@PreDestroy`), or hand it to Spring's own async
> infrastructure. See [Chapter 33](33-coroutine-fundamentals.md).
> **Suggestion.** `detekt/GlobalCoroutineUsage` catches the `GlobalScope`
> half of this rule, but it is not active by default and it flags only
> `GlobalScope.launch`/`GlobalScope.async` — an inline
> `CoroutineScope(Dispatchers.IO)` passes it, so the second half is review-only.

```kotlin
// bad — unowned, uncancellable, and its failures vanish
@PostMapping("/orders")
suspend fun create(@Valid @RequestBody request: CreateOrderRequest): OrderResponse {
    val order = checkout.placeOrder(request.toCommand())
    GlobalScope.launch { analytics.recordOrder(order.id) }
    return OrderResponse.from(order)
}

// good — a bean owns the scope, and shutdown cancels it
@Component
class BackgroundWork(ioDispatcher: CoroutineDispatcher) : DisposableBean {

    private val scope = CoroutineScope(SupervisorJob() + ioDispatcher)

    fun launch(block: suspend CoroutineScope.() -> Unit) {
        scope.launch(block = block)
    }

    override fun destroy() {
        scope.cancel()
    }
}
```

## 44.9 Consume `WebClient` with the `await*` extensions, never with `.block()`.

> Why? `.block()` on a coroutine-based handler is the exact failure §44.4
> describes, and on a WebFlux event-loop thread Reactor will refuse it
> outright rather than deadlock quietly. Spring ships coroutine extensions
> for the whole `WebClient` surface — `awaitBody<T>()`, `awaitBodyOrNull<T>()`,
> `awaitBodilessEntity()`, and `awaitExchange { }` — which suspend instead of
> parking a thread and give you a nullable Kotlin type where the `Mono` may
> be empty. Note the mapping the
> [reference](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html)
> gives: "`fun handler(): Mono<T>` becomes `suspend fun handler(): T` or
> `suspend fun handler(): T?` depending on if the `Mono` can be empty or
> not (with the advantage of being more statically typed)." **Suggestion.**

```kotlin
// bad — blocks a thread, and `!!` papers over an empty Mono
suspend fun stockLevel(sku: String): StockLevel =
    webClient.get().uri("/inventory/{sku}", sku).retrieve().bodyToMono<StockLevel>().block()!!

// good — suspends, and the empty case is in the type
suspend fun stockLevel(sku: String): StockLevel? =
    webClient.get().uri("/inventory/{sku}", sku).retrieve().awaitBodyOrNull<StockLevel>()

// good — a body that must be present, with the status branch handled
suspend fun reserve(request: ReservationRequest): Reservation =
    webClient
        .post()
        .uri("/reservations")
        .bodyValue(request)
        .retrieve()
        .onStatus(HttpStatusCode::is5xxServerError) { response ->
            Mono.error(InventoryUnavailableException(response.statusCode()))
        }
        .awaitBody<Reservation>()
```

## 44.10 Bridge a third-party `Publisher` with `awaitSingle`, `awaitFirstOrNull`, or `asFlow` rather than blocking on it.

> Why? Plenty of libraries you do not control still hand back a `Mono`,
> `Flux`, or a bare `Publisher` — a reactive driver, a messaging client, a
> Spring API that has no coroutine overload yet. `kotlinx-coroutines-reactive`
> converts each of those without leaving the coroutine: `awaitSingle()` for
> exactly one element, `awaitSingleOrNull()` and `awaitFirstOrNull()` for a
> source that may be empty, and `asFlow()` for a stream. All of them respect
> cancellation, which `.block()` and `.toIterable()` do not. Choose the one
> whose cardinality matches the source: `awaitSingle()` on an empty publisher
> throws `NoSuchElementException`, which is a bug you want at the boundary
> rather than three frames later. **Suggestion.**

```kotlin
// bad — parks a thread and ignores cancellation entirely
suspend fun latestQuote(symbol: String): Quote = Mono.from(quotePublisher(symbol)).block()!!

// good — cardinality is explicit and cancellation propagates
suspend fun latestQuote(symbol: String): Quote? = quotePublisher(symbol).awaitFirstOrNull()

suspend fun exactlyOneConfig(key: String): ConfigEntry = configMono(key).awaitSingle()

fun quoteStream(symbol: String): Flow<Quote> = quotePublisher(symbol).asFlow()
```

## 44.11 Use `RestClient` for blocking MVC code and `WebClient` for coroutine code; do not mix the two.

> Why? `RestClient` (Spring Framework 6.1+) is the modern synchronous client
> and is the right choice in a plain MVC handler — it shares `WebClient`'s
> fluent shape without dragging Reactor into a stack that has no use for it.
> But it is blocking, and Spring ships it **no suspending `await*`
> extensions** — its Kotlin extensions are reified `body<T>()` conveniences,
> and the coroutine reference documents `await*` for the WebFlux client only.
> Calling `RestClient` from
> a `suspend` function therefore parks whichever thread that coroutine is on, which is
> fatal on WebFlux and merely wasteful elsewhere. `WebClient` plus the
> `await*` extensions of §44.9 is the coroutine-side answer. Picking per call
> site is how a service ends up with a `RestClient` invoked from an event
> loop. **Suggestion.**

```kotlin
// bad — a blocking client called from a suspend function
suspend fun stockLevel(sku: String): StockLevel =
    restClient.get().uri("/inventory/{sku}", sku).retrieve().body(StockLevel::class.java)!!

// good — blocking client, blocking handler; the empty body is in the type
@GetMapping("/inventory/{sku}")
fun stock(@PathVariable sku: String): StockLevel? =
    restClient.get().uri("/inventory/{sku}", sku).retrieve().body(StockLevel::class.java)

// good — suspending handler, suspending client
@GetMapping("/inventory/{sku}")
suspend fun stock(@PathVariable sku: String): StockLevel =
    webClient.get().uri("/inventory/{sku}", sku).retrieve().awaitBody<StockLevel>()
```

## 44.12 Prefer annotated `@RestController` handlers; reach for `coRouter` only when the routing itself is what varies.

> Why? `coRouter { }` is a genuinely Kotlin-only capability — WebFlux.fn with
> suspending handlers, no annotations, routes as ordinary values you can
> compose, filter, and build in a loop. That is exactly right when routes are
> assembled from configuration or a plugin registry. It is exactly wrong as
> the default: you give up `@Valid` argument resolution, `@ExceptionHandler`
> advice, the entire `springdoc` annotation surface, and the ability of any
> new reader to find an endpoint by grepping for its path. Pick one style per
> module and state why. **Suggestion.**

```kotlin
// bad — the functional DSL used for an ordinary fixed CRUD surface, so every
// convenience the annotation model provides has to be rebuilt by hand
@Bean
fun orderRoutes(handler: OrderHandler) = coRouter {
    GET("/orders/{id}", handler::get)
    POST("/orders", handler::create)
}

// good — annotations for a fixed surface
@RestController
@RequestMapping("/orders")
class OrderController(private val checkout: CheckoutService) {

    @PostMapping(consumes = [MediaType.APPLICATION_JSON_VALUE])
    suspend fun create(@Valid @RequestBody request: CreateOrderRequest): OrderResponse =
        OrderResponse.from(checkout.placeOrder(request.toCommand()))
}

// good — coRouter where the routes genuinely come from data
@Bean
fun pluginRoutes(plugins: List<RoutePlugin>) = coRouter {
    plugins.forEach { plugin -> GET(plugin.path, plugin::handle) }
}

// the handler side of the functional model
@Component
class OrderHandler(private val checkout: CheckoutService) {

    suspend fun create(request: ServerRequest): ServerResponse {
        val command = request.awaitBody<CreateOrderRequest>().toCommand()
        val response = OrderResponse.from(checkout.placeOrder(command))
        return ServerResponse.ok().bodyValueAndAwait(response)
    }
}
```

## 44.13 Model request and response bodies as `data class`es with `val` properties, and keep `jackson-module-kotlin` on the classpath.

> Why? A `data class` is the Kotlin answer to `best-practice-java` §34.5's
> record DTO: immutable, correct `equals` for test assertions, useful
> `toString`. But Jackson cannot bind one without help — there is no no-arg
> constructor, and the parameter names Jackson needs live in Kotlin metadata,
> not in the class file. Spring Boot's
> [Kotlin support](https://docs.spring.io/spring-boot/reference/features/kotlin.html)
> is direct about it: the Jackson Kotlin module "is required for serializing /
> deserializing JSON data in Kotlin. It is automatically registered when found
> on the classpath." Without it, deserialization fails at runtime; worse, with
> a *nullable-unaware* mapper a missing JSON field can be bound as `null` into
> a non-null Kotlin property, producing a value the type system says cannot
> exist. `spring-boot-starter-web` pulls the module in for a Kotlin project,
> but a hand-assembled `ObjectMapper` will not. Cross-reference
> [Chapter 41](41-spring-kotlin-setup.md) for the full plugin and dependency
> set. **Suggestion.**

```kotlin
// bad — a mutable JavaBean DTO written to satisfy Jackson
class CreateOrderRequest {
    var customerId: UUID? = null
    var lines: MutableList<LineItemRequest> = mutableListOf()
}

// good — immutable, and jackson-module-kotlin binds it natively
data class CreateOrderRequest(
    val customerId: UUID,
    val lines: List<LineItemRequest>,
    val note: String? = null,
)

data class OrderResponse(
    val id: UUID,
    val status: OrderStatus,
    val total: BigDecimal,
    val placedAt: Instant,
) {
    companion object {
        fun from(order: Order) =
            OrderResponse(order.id, order.status, order.total, order.placedAt)
    }
}
```

## 44.14 Write the use-site target explicitly on every validation constraint applied to a constructor property.

> Why? A Jakarta constraint is a Java annotation, so its Kotlin-applicable
> targets are `param`, `field`, and `get` — never `property`, which no Java
> annotation can declare. Under the pre-2.4 defaulting rule (`first-only`),
> `param` wins and the constraint lands **only on the constructor parameter**,
> where Spring's `@Valid` never looks: the DTO validates nothing and a blank
> `customerId` sails through to the service. Kotlin 2.4 changed the rule —
> per the
> [2.4 compatibility guide](https://kotlinlang.org/docs/compatibility-guide-24.html),
> the compiler "now uses `param` and `property` if they apply, and uses
> `field` only if `property` doesn't apply," so a bare constraint now also
> reaches the backing field and does fire. That is a fix, not a licence to
> stop writing the target: any project still on `-Xannotation-default-target=first-only`
> for source compatibility gets the old behaviour, and a reader should not
> have to know which. `@field:` is unambiguous in every version. See
> [Chapter 27](27-annotations-and-use-site-targets.md). **Suggestion.**

```kotlin
// bad — on Kotlin < 2.4, or with -Xannotation-default-target=first-only,
// these constraints exist only on the constructor parameter and never run
data class CreateOrderRequest(
    @NotNull val customerId: UUID,
    @NotEmpty val lines: List<LineItemRequest>,
    @Size(max = 280) val note: String? = null,
)

// good — targeted at the field, which is what @Valid inspects
data class CreateOrderRequest(
    @field:NotNull val customerId: UUID,
    @field:NotEmpty val lines: List<@Valid LineItemRequest>,
    @field:Size(max = 280) val note: String? = null,
)
```

## 44.15 Do not use a `value class` as a `@PathVariable` or `@RequestParam` type.

> Why? A `@JvmInline value class` is erased in the JVM signature, so Java
> reflection reports the parameter as the underlying `String`/`UUID`/`Long`
> while Kotlin reflection reports the wrapper. Spring's argument resolvers
> read one and its Kotlin-aware invoker reads the other, and the mismatch
> surfaces as `IllegalArgumentException: object is not an instance of
> declaring class` at request time. This is a known and largely unfixed
> corner of Spring Framework: "Support Kotlin value (JvmInline) classes as
> `suspend` handler method arguments"
> ([#27345](https://github.com/spring-projects/spring-framework/issues/27345))
> was **closed as not planned**; the annotated-parameter report
> ([#34458](https://github.com/spring-projects/spring-framework/issues/34458))
> was closed as a duplicate; and the `@ModelAttribute` variant
> ([#36183](https://github.com/spring-projects/spring-framework/issues/36183))
> is still open. Treat the pattern as unsupported rather than as a bug
> awaiting a fix. Registering a `Converter<String, OrderId>` does not reliably
> close the gap either, because the failure is in invocation, not conversion. Bind the
> underlying type at the HTTP edge and construct the value class in the first
> line of the method, where it is a compile-time-checked one-liner. See
> [Chapter 12](12-value-classes.md). **Suggestion.**

```kotlin
// bad — fails at request time, not compile time
@JvmInline value class OrderId(val raw: UUID)

@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: OrderId): OrderResponse = orderQueries.findById(id)

// good — the wire type at the edge, the domain type one line in
@GetMapping("/orders/{id}")
suspend fun get(@PathVariable id: UUID): OrderResponse = orderQueries.findById(OrderId(id))
```

## 44.16 Model the domain's failure modes as a `sealed interface` and map them in one `@RestControllerAdvice`.

> Why? `best-practice-java` §34.8 and §34.9 already require a single advice
> producing `ProblemDetail` bodies. Kotlin lets you make the *input* to that
> advice a closed set: a `sealed interface` of failure types means the
> compiler knows every case, so a `when` over it is exhaustive without an
> `else`, and adding a new failure becomes a compile error in the advice
> rather than a silent fall-through to the generic 500 handler. That is the
> single highest-value structural difference between a Kotlin and a Java error
> contract. See [Chapter 13](13-sealed-types.md). **Suggestion.**

```kotlin
// bad — open hierarchy plus a catch-all `else`; a new failure type compiles
// cleanly and ships as an unlabelled 500
abstract class CheckoutFailure(message: String) : RuntimeException(message)

@ExceptionHandler(CheckoutFailure::class)
fun handle(failure: CheckoutFailure): ProblemDetail =
    when (failure) {
        is OutOfStock -> problem(HttpStatus.CONFLICT, "Out of stock")
        else -> problem(HttpStatus.INTERNAL_SERVER_ERROR, "Checkout failed")
    }

// good — closed hierarchy, exhaustive mapping, no `else`
sealed interface CheckoutFailure {
    data class OutOfStock(val skus: List<String>) : CheckoutFailure
    data class PaymentDeclined(val reason: String) : CheckoutFailure
    data class UnknownCustomer(val customerId: UUID) : CheckoutFailure
}

class CheckoutException(val failure: CheckoutFailure) : RuntimeException(failure.toString())

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(CheckoutException::class)
    fun handle(exception: CheckoutException): ProblemDetail =
        when (val failure = exception.failure) {
            is CheckoutFailure.OutOfStock ->
                problem(HttpStatus.CONFLICT, "One or more items are out of stock").apply {
                    setProperty("skus", failure.skus)
                }
            is CheckoutFailure.PaymentDeclined ->
                problem(HttpStatus.PAYMENT_REQUIRED, "The payment was declined")
            is CheckoutFailure.UnknownCustomer ->
                problem(HttpStatus.NOT_FOUND, "No such customer")
        }

    private fun problem(status: HttpStatus, detail: String): ProblemDetail =
        ProblemDetail.forStatusAndDetail(status, detail)
}
```

## 44.17 Never put an exception message from a coroutine failure straight into the response body.

> Why? This is `best-practice-java` §34.10, and coroutines make it worse
> rather than better. A failure inside `coroutineScope`/`async` arrives
> wrapped, and the message you would be tempted to forward often contains the
> internal coroutine name, the dispatcher, and the full downstream URL —
> reconnaissance for an attacker and noise for a legitimate client. Log the
> whole thing with a correlation id, return the id. **Suggestion.**

```kotlin
// bad — leaks the internal cause chain to the caller
@ExceptionHandler(Exception::class)
fun handleAny(exception: Exception): ProblemDetail =
    ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, exception.message ?: "error")

// good — full detail to the log, an opaque id to the client
@ExceptionHandler(Exception::class)
fun handleAny(exception: Exception): ProblemDetail {
    val incidentId = UUID.randomUUID().toString()
    logger.error("unhandled request failure incidentId={}", incidentId, exception)
    return ProblemDetail.forStatusAndDetail(
        HttpStatus.INTERNAL_SERVER_ERROR,
        "The request could not be completed",
    ).apply {
        title = "Internal server error"
        setProperty("incidentId", incidentId)
    }
}
```
