<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 34. Spring: Web Layer

A controller is a translation layer, not a place where things happen. It
converts HTTP into a call on a domain type, and converts the result back into
HTTP. Everything that makes a controller hard to read, hard to test, or
dangerous to deploy comes from putting something else in it: a query, a
branch, a transaction, an entity, or an exception message written for a
developer and shipped to a customer.

This chapter covers inbound HTTP (controllers, DTOs, validation, error
responses, status codes, pagination) and outbound HTTP (declarative clients).
It draws from
[Spring MVC: Annotated Controllers](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html),
[Exception Handling with `@ExceptionHandler`](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html),
[Error Responses / RFC 9457](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html),
[Controller Method Validation](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html),
[CORS](https://docs.spring.io/spring-framework/reference/web/webmvc-cors.html),
and
[REST Clients](https://docs.spring.io/spring-framework/reference/integration/rest-clients.html).

Three neighbouring topics live elsewhere. Which exception type to throw in the
first place, and why swallowing one is always wrong, is
[Chapter 24](24-exceptions.md) — this chapter is only about turning an
exception into a response. `@Transactional` placement, and why it must not
land on a controller method, is
[Chapter 35](35-spring-data-and-transactions.md). Writing `@WebMvcTest` slices
against the controllers described here is
[Chapter 36](36-spring-testing.md). The record and validation discipline the
DTO rules assume is [Chapter 12](12-records.md) and
[Chapter 22](22-methods-and-parameters.md).

**Tool alignment:** the shipped Checkstyle and Error Prone configuration has
no Spring MVC checks, so every rule below is a **Suggestion** — no linter in
the shipped configuration catches any of them. The shipped
`EmptyCatchBlock` check covers only the narrower case of a catch block whose
body is entirely empty, which is not the failure §34.8 is about. The one
practical enforcement mechanism for this chapter is an
[ArchUnit](https://www.archunit.org/) layer test for §34.2 and §34.4 — assert
that no class in `..controller..` depends on `..repository..` or on any
`@Entity` type.

## 34.1 Keep the controller thin: bind input, delegate to one service call, map the result.

> Why? Logic in a controller can only be exercised through the HTTP stack, so
> every branch needs a MockMvc test with a serialized body instead of a
> three-line unit test. It is also the logic most likely to be duplicated, as
> soon as a second entry point — a scheduled job, a message listener, a CLI —
> needs the same behaviour and finds it welded to `HttpServletRequest`. A
> controller method should read as three statements: map in, call, map out.
> **Suggestion.**

```java
// bad — pricing rules, inventory policy, and persistence decisions all live
// in the HTTP layer
@RestController
public class CheckoutController {

  @PostMapping("/orders")
  public OrderResponse create(@RequestBody OrderRequest request) {
    BigDecimal total = BigDecimal.ZERO;
    for (LineRequest line : request.lines()) {
      Product product = productRepository.findById(line.sku()).orElseThrow();
      if (product.stock() < line.quantity()) {
        throw new IllegalStateException("out of stock");
      }
      total = total.add(product.price().multiply(BigDecimal.valueOf(line.quantity())));
    }
    Order order = orderRepository.save(new Order(request.customerId(), total));
    return new OrderResponse(order.getId(), order.getTotal());
  }
}

// good
@RestController
public class CheckoutController {
  private final CheckoutService checkout;

  public CheckoutController(CheckoutService checkout) {
    this.checkout = checkout;
  }

  @PostMapping("/orders")
  public OrderResponse create(@Valid @RequestBody OrderRequest request) {
    return OrderResponse.from(checkout.placeOrder(request.toCommand()));
  }
}
```

## 34.2 Never inject a repository, an `EntityManager`, or a `JdbcTemplate` into a controller.

> Why? A controller that queries directly has no transaction boundary — each
> repository call runs in its own transaction, so a method that reads twice can
> see two different states of the database. It also means the read is
> unavailable to any non-HTTP caller, and it puts persistence types on the
> wrong side of the layer boundary, which is how entities end up in responses
> (§34.4). The service layer exists to own the transaction and the
> entity-to-DTO conversion; see
> [Chapter 35](35-spring-data-and-transactions.md). **Suggestion.**

```java
// bad — two independent transactions, and the entity is now one `return`
// statement away from the wire
@RestController
public class OrderController {
  private final OrderRepository orders;
  private final CustomerRepository customers;

  public OrderController(OrderRepository orders, CustomerRepository customers) {
    this.orders = orders;
    this.customers = customers;
  }

  @GetMapping("/orders/{id}")
  public Order get(@PathVariable UUID id) {
    Order order = orders.findById(id).orElseThrow();
    order.setCustomer(customers.findById(order.getCustomerId()).orElseThrow());
    return order;
  }
}

// good
@RestController
public class OrderController {
  private final OrderQueryService orderQueries;

  public OrderController(OrderQueryService orderQueries) {
    this.orderQueries = orderQueries;
  }

  @GetMapping("/orders/{id}")
  public OrderResponse get(@PathVariable UUID id) {
    return orderQueries.findById(id);
  }
}
```

## 34.3 Use `@RestController`, not `@Controller` plus `@ResponseBody` on every method.

> Why? `@RestController` is a composed annotation that applies `@ResponseBody`
> at the type level, so the intent — "every method on this class returns a
> body, not a view name" — is stated once at the top instead of repeated N
> times. The failure mode it removes is real: forget `@ResponseBody` on one
> method of a `@Controller` and Spring treats the returned `String` as a view
> name, producing a 404 or a template error rather than the JSON you expected.
> **Suggestion.**

```java
// bad — one missing @ResponseBody turns a payload into a view name
@Controller
@RequestMapping("/orders")
public class OrderController {

  @GetMapping("/{id}")
  @ResponseBody
  public OrderResponse get(@PathVariable UUID id) {
    return orderQueries.findById(id);
  }

  @GetMapping("/{id}/status")
  public String status(@PathVariable UUID id) {
    return orderQueries.statusOf(id);
  }
}

// good
@RestController
@RequestMapping("/orders")
public class OrderController {

  @GetMapping("/{id}")
  public OrderResponse get(@PathVariable UUID id) {
    return orderQueries.findById(id);
  }

  @GetMapping("/{id}/status")
  public String status(@PathVariable UUID id) {
    return orderQueries.statusOf(id);
  }
}
```

## 34.4 Never expose a persistence entity over HTTP — define dedicated request and response DTOs.

> Why? Returning an entity welds your database schema to your public API:
> renaming a column becomes a breaking API change, and adding a field
> publishes it to every client whether you meant to or not — which is how
> password hashes and internal flags leak. It is also a correctness problem,
> not just a design one: serializing a JPA entity outside a transaction
> triggers `LazyInitializationException`, and serializing one *inside* a
> transaction triggers N+1 queries as Jackson walks the associations. Accepting
> an entity as a `@RequestBody` is worse still — it lets a client set any
> field, including the identifier and the ownership column. **Suggestion.**

```java
// bad — the entity is the API; passwordHash and internalNotes ship to the
// client, and the client can set `status` and `customerId` on the way in
@PostMapping("/orders")
public Order create(@RequestBody Order order) {
  return orders.save(order);
}

// good — the wire format is a type you own and can evolve independently
public record CreateOrderRequest(
    @NotNull UUID customerId, @NotEmpty List<@Valid LineItemRequest> lines) {}

public record OrderResponse(UUID id, OrderStatus status, BigDecimal total, Instant placedAt) {
  public static OrderResponse from(Order order) {
    return new OrderResponse(order.id(), order.status(), order.total(), order.placedAt());
  }
}

@PostMapping("/orders")
public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) {
  return OrderResponse.from(checkout.placeOrder(request.toCommand()));
}
```

## 34.5 Model request and response bodies as records.

> Why? A DTO is a transparent carrier of its components, which is the exact
> definition of a record (see [Chapter 12](12-records.md)). You get
> immutability, a correct `equals` for test assertions, a useful `toString`
> for logs, and — the part that matters here — a compact constructor in which
> to normalize or reject values before any of your code sees them. Jackson
> binds records natively. A mutable JavaBean DTO gives you none of that and
> lets a filter or interceptor mutate a request body mid-flight.
> **Suggestion.**

```java
// bad — mutable, no equals, and every field is separately settable to null
public class CreateOrderRequest {
  private UUID customerId;
  private List<LineItemRequest> lines;

  public UUID getCustomerId() {
    return customerId;
  }

  public void setCustomerId(UUID customerId) {
    this.customerId = customerId;
  }

  public List<LineItemRequest> getLines() {
    return lines;
  }

  public void setLines(List<LineItemRequest> lines) {
    this.lines = lines;
  }
}

// good — immutable, defensively copied, and assertable in one line
public record CreateOrderRequest(
    @NotNull UUID customerId, @NotEmpty List<@Valid LineItemRequest> lines) {

  public CreateOrderRequest {
    lines = List.copyOf(lines);
  }
}
```

## 34.6 Validate every `@RequestBody` with `@Valid`.

> Why? Without it, the constraint annotations on the DTO are documentation.
> With it, Spring rejects a malformed body before your method runs and raises
> `MethodArgumentNotValidException`, which the advice in §34.8 turns into a
> 400 listing exactly which fields failed. The
> [reference](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html)
> confirms the mechanism: validation "is applied individually to an
> `@ModelAttribute`, `@RequestBody`, and `@RequestPart` method parameter
> annotated with `@jakarta.validation.Valid` or Spring's `@Validated`". Note
> that `@Valid` on the parameter does not recurse into a collection's elements
> unless the element type is itself annotated — hence
> `List<@Valid LineItemRequest>`. **Suggestion.**

```java
// bad — the constraints on CreateOrderRequest never run; a null customerId
// reaches the service and fails somewhere deeper with a worse message
@PostMapping("/orders")
public OrderResponse create(@RequestBody CreateOrderRequest request) {
  return OrderResponse.from(checkout.placeOrder(request.toCommand()));
}

// good
@PostMapping("/orders")
public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) {
  return OrderResponse.from(checkout.placeOrder(request.toCommand()));
}
```

## 34.7 Constrain `@RequestParam` and `@PathVariable` directly, and do not add class-level `@Validated` on Spring 6.1+.

> Why? Spring Framework 6.1 (Spring Boot 3.2) added built-in method validation
> for controllers, and the
> [reference](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html)
> is explicit about the consequence: "In order to take advantage of the Spring
> MVC built-in support for method validation added in Spring Framework 6.1,
> you need to remove the class level `@Validated` annotation from the
> controller." Leaving it on routes validation through an AOP proxy instead,
> producing `ConstraintViolationException` — which nothing handles by default,
> so it surfaces as a 500. Without it you get
> `HandlerMethodValidationException`, which is an `ErrorResponse` and maps to
> 400 automatically. On Spring Boot 3.0/3.1 (Framework 6.0) the class-level
> `@Validated` is still required. **Suggestion.**

```java
// bad on Spring Boot 3.2+ — AOP method validation, so an out-of-range `size`
// becomes a 500 ConstraintViolationException
@RestController
@Validated
public class OrderController {

  @GetMapping("/orders")
  public List<OrderResponse> list(@RequestParam @Min(1) @Max(100) int size) {
    return orderQueries.page(size);
  }
}

// good — built-in method validation; the same input is a 400
@RestController
public class OrderController {

  @GetMapping("/orders")
  public List<OrderResponse> list(@RequestParam @Min(1) @Max(100) int size) {
    return orderQueries.page(size);
  }
}
```

## 34.8 Handle exceptions in one `@RestControllerAdvice`, never with `try`/`catch` in a controller method.

> Why? Per-method `try`/`catch` produces a different error shape at every
> endpoint, so clients cannot write one error handler — and it is where
> exceptions get swallowed, which
> [§6.2 of the Google Java Style Guide](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> calls out: "It is very rarely correct to do nothing in response to a caught
> exception." One `@RestControllerAdvice` gives every endpoint the same
> mapping from domain failure to status code, in a class you can read top to
> bottom to see the full error contract. Checkstyle's `EmptyCatchBlock` fires
> only when a catch block body is entirely empty, which the bad example below
> is not — nothing mechanical catches this. **Suggestion.**

```java
// bad — a different shape per endpoint, and the cause is destroyed
@PostMapping("/orders")
public ResponseEntity<?> create(@Valid @RequestBody CreateOrderRequest request) {
  try {
    return ResponseEntity.ok(OrderResponse.from(checkout.placeOrder(request.toCommand())));
  } catch (OutOfStockException e) {
    return ResponseEntity.badRequest().body(Map.of("error", "out of stock"));
  } catch (Exception e) {
    return ResponseEntity.status(500).body("error");
  }
}

// good — the controller stays thin; one advice owns the whole error contract
@RestControllerAdvice
public class ApiExceptionHandler {

  @ExceptionHandler(OutOfStockException.class)
  public ProblemDetail handleOutOfStock(OutOfStockException exception) {
    ProblemDetail problem =
        ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, "One or more items are out of stock");
    problem.setTitle("Out of stock");
    problem.setType(URI.create("https://api.example.com/problems/out-of-stock"));
    problem.setProperty("skus", exception.unavailableSkus());
    return problem;
  }
}
```

## 34.9 Return RFC 9457 problem details, using `ProblemDetail`, rather than an ad-hoc error map.

> Why?
> [`ProblemDetail`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/ProblemDetail.html)
> is Spring 6's container for the standard `type`, `title`, `status`,
> `detail`, and `instance` fields, served as `application/problem+json`. A
> standard shape means clients can parse errors with an off-the-shelf library,
> and the `type` URI gives each failure a stable, documentable identifier that
> survives message rewording — which an English `"error"` string does not. Use
> `setProperty` for machine-readable extras rather than inventing a parallel
> envelope. **Suggestion.**

```java
// bad — bespoke shape; the client has to string-match on `message`
@ExceptionHandler(OrderNotFoundException.class)
public ResponseEntity<Map<String, Object>> handleNotFound(OrderNotFoundException exception) {
  return ResponseEntity.status(HttpStatus.NOT_FOUND)
      .body(Map.of("success", false, "message", "Order " + exception.orderId() + " not found"));
}

// good — application/problem+json with a stable type URI
@ExceptionHandler(OrderNotFoundException.class)
public ProblemDetail handleNotFound(OrderNotFoundException exception) {
  ProblemDetail problem =
      ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "No order with that identifier");
  problem.setTitle("Order not found");
  problem.setType(URI.create("https://api.example.com/problems/order-not-found"));
  problem.setProperty("orderId", exception.orderId());
  return problem;
}
```

## 34.10 Never put an exception message, stack trace, or SQL fragment in a response body.

> Why? Exception messages are written for the engineer debugging the system
> and routinely contain table names, file paths, internal hostnames, query
> text, and occasionally credentials — all of which is reconnaissance for an
> attacker and noise for a legitimate client. The correlation identifier is
> what the client actually needs: it lets support find the full stack trace in
> the logs, where it belongs. Note that Spring Boot's default error page
> already hides the stack trace unless `server.error.include-stacktrace` is
> changed — never change it in a deployed profile. **Suggestion.**

```java
// bad — leaks the internal message, and logs nothing
@ExceptionHandler(Exception.class)
public ProblemDetail handleAny(Exception exception) {
  return ProblemDetail.forStatusAndDetail(
      HttpStatus.INTERNAL_SERVER_ERROR, exception.getMessage());
}

// good — full detail to the log, a correlation id to the client
@ExceptionHandler(Exception.class)
public ProblemDetail handleAny(Exception exception) {
  String incidentId = UUID.randomUUID().toString();
  log.error("unhandled request failure incidentId={}", incidentId, exception);

  ProblemDetail problem =
      ProblemDetail.forStatusAndDetail(
          HttpStatus.INTERNAL_SERVER_ERROR, "The request could not be completed");
  problem.setTitle("Internal server error");
  problem.setProperty("incidentId", incidentId);
  return problem;
}
```

## 34.11 Extend `ResponseEntityExceptionHandler` so framework exceptions get the same body shape as yours.

> Why? Validation failures, unreadable bodies, unsupported media types, and
> missing parameters are raised by Spring, not by your code, so an advice that
> only handles your own exception types leaves those endpoints returning
> Spring's default error body — a second error shape your clients must also
> parse. The
> [reference](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html)
> describes `ResponseEntityExceptionHandler` as the "convenient base class for
> `@ControllerAdvice`" that "handles all Spring MVC exceptions and any
> `ErrorResponseException`", rendering them with an RFC 9457 body. Overriding
> a single hook lets you add your own extension fields to every one of them.
> **Suggestion.**

```java
// bad — MethodArgumentNotValidException falls through to Spring's default
// error body, which looks nothing like the ProblemDetail above
@RestControllerAdvice
public class ApiExceptionHandler {

  @ExceptionHandler(OrderNotFoundException.class)
  public ProblemDetail handleNotFound(OrderNotFoundException exception) {
    return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "No order with that identifier");
  }
}

// good — framework exceptions and domain exceptions share one contract
@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

  @Override
  protected ResponseEntity<Object> handleMethodArgumentNotValid(
      MethodArgumentNotValidException exception,
      HttpHeaders headers,
      HttpStatusCode status,
      WebRequest request) {
    ProblemDetail problem =
        ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Request body is invalid");
    problem.setTitle("Validation failed");
    problem.setProperty(
        "fieldErrors",
        exception.getBindingResult().getFieldErrors().stream()
            .collect(
                Collectors.toMap(
                    FieldError::getField,
                    error -> Objects.requireNonNullElse(error.getDefaultMessage(), "invalid"),
                    (first, second) -> first)));
    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(problem);
  }

  @ExceptionHandler(OrderNotFoundException.class)
  public ProblemDetail handleNotFound(OrderNotFoundException exception) {
    return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "No order with that identifier");
  }
}
```

## 34.12 Return the payload type directly; reach for `ResponseEntity` only when you must control the status or headers.

> Why? `ResponseEntity<OrderResponse>` hides the actual payload type one level
> down in a generic, which costs you readability at the signature and makes
> `@WebMvcTest` assertions noisier. Worse is `ResponseEntity<?>` or
> `ResponseEntity<Object>`, which erases the contract entirely — the reader
> and the OpenAPI generator both lose the ability to see what the endpoint
> returns. Plain return types get 200 and the correct content type
> automatically. **Suggestion.**

```java
// bad — the response type is unknowable from the signature
@GetMapping("/orders/{id}")
public ResponseEntity<?> get(@PathVariable UUID id) {
  return ResponseEntity.ok(orderQueries.findById(id));
}

// good — plain type when there is nothing to control
@GetMapping("/orders/{id}")
public OrderResponse get(@PathVariable UUID id) {
  return orderQueries.findById(id);
}

// good — ResponseEntity where a header genuinely must be set
@PostMapping("/orders")
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
  OrderResponse created = OrderResponse.from(checkout.placeOrder(request.toCommand()));
  return ResponseEntity.created(URI.create("/orders/" + created.id())).body(created);
}
```

## 34.13 Use `@ResponseStatus` for a fixed non-200 status instead of wrapping the payload in a `ResponseEntity`.

> Why? When the status is a constant of the endpoint, not a runtime decision,
> `@ResponseStatus` says so declaratively and leaves the return type as the
> payload — which keeps §34.12 satisfied. The same annotation on a custom
> exception type gives it a default status without an `@ExceptionHandler`
> entry, useful for the simple cases; reach for a handler when the response
> needs a body richer than the status line. **Suggestion.**

```java
// bad — ResponseEntity used only to set a constant status
@PostMapping("/orders/{id}/cancellations")
public ResponseEntity<Void> cancel(@PathVariable UUID id) {
  checkout.cancel(id);
  return ResponseEntity.accepted().build();
}

// good
@PostMapping("/orders/{id}/cancellations")
@ResponseStatus(HttpStatus.ACCEPTED)
public void cancel(@PathVariable UUID id) {
  checkout.cancel(id);
}

// good — a domain exception carrying its own default status
@ResponseStatus(HttpStatus.NOT_FOUND)
public class OrderNotFoundException extends RuntimeException {
  public OrderNotFoundException(UUID orderId) {
    super("order not found: " + orderId);
  }
}
```

## 34.14 Declare `produces` and `consumes` explicitly on every mapping.

> Why? Without `consumes`, a mapping accepts any content type, so a client
> that posts `text/plain` reaches your method and fails at deserialization
> with a confusing message instead of getting a clean 415. Without `produces`,
> the response type is decided by content negotiation, which can change when
> someone adds an XML or CBOR converter to the classpath. Declaring both makes
> the contract explicit at the endpoint and lets Spring reject mismatches
> before your code runs. **Suggestion.**

```java
// bad — accepts anything, produces whatever negotiation picks
@PostMapping("/orders")
public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) {
  return OrderResponse.from(checkout.placeOrder(request.toCommand()));
}

// good
@PostMapping(
    path = "/orders",
    consumes = MediaType.APPLICATION_JSON_VALUE,
    produces = MediaType.APPLICATION_JSON_VALUE)
public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) {
  return OrderResponse.from(checkout.placeOrder(request.toCommand()));
}
```

## 34.15 Return the status code the outcome actually means.

> Why? Status codes are the part of your API that infrastructure reads: load
> balancers, CDNs, retry libraries, and monitoring all branch on them. An API
> that returns 200 with `{"success": false}` is invisible to every one of
> those — your error rate dashboard reads zero while customers fail. The
> distinctions that matter most in practice: **201** with a `Location` header
> for a created resource, **204** for a successful operation with no body,
> **404** for a resource that does not exist versus **403** for one you may not
> see, **409** for a conflict with current state, and **422** for a
> semantically invalid but well-formed body. **Suggestion.**

```java
// bad — everything is a 200, so retry logic and alerting are both blind
@PostMapping("/orders")
public Map<String, Object> create(@Valid @RequestBody CreateOrderRequest request) {
  try {
    Order order = checkout.placeOrder(request.toCommand());
    return Map.of("success", true, "id", order.id());
  } catch (OutOfStockException e) {
    return Map.of("success", false, "error", "out of stock");
  }
}

// good — 201 + Location on success; the advice in §34.8 maps OutOfStock to 409
@PostMapping("/orders")
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
  OrderResponse created = OrderResponse.from(checkout.placeOrder(request.toCommand()));
  return ResponseEntity.created(URI.create("/orders/" + created.id())).body(created);
}

@DeleteMapping("/orders/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void delete(@PathVariable UUID id) {
  checkout.delete(id);
}
```

## 34.16 Make every retryable unsafe operation idempotent, keyed by a client-supplied identifier.

> Why? Any client with a retry policy — and every mobile client, every proxy,
> every message consumer has one — will eventually send the same POST twice
> because the response was lost, not because the operation failed. Without a
> deduplication key that means two orders and two charges. An
> `Idempotency-Key` header, recorded with the result inside the same
> transaction that performs the work, turns the retry into a replay of the
> original response. GET, PUT, and DELETE are idempotent by HTTP's own
> definition; POST is the one you must make so. **Suggestion.**

```java
// bad — a retried request charges the customer twice
@PostMapping("/payments")
public PaymentResponse pay(@Valid @RequestBody PaymentRequest request) {
  return PaymentResponse.from(payments.charge(request.toCommand()));
}

// good — the key is part of the contract and the service replays on repeat
@PostMapping("/payments")
public PaymentResponse pay(
    @RequestHeader("Idempotency-Key") @NotBlank String idempotencyKey,
    @Valid @RequestBody PaymentRequest request) {
  return PaymentResponse.from(payments.charge(idempotencyKey, request.toCommand()));
}
```

## 34.17 Paginate every collection endpoint, and return a stable envelope rather than a framework page type.

> Why? An unpaginated `findAll` is a latency and memory incident waiting for
> the table to grow — it is fine in development with 40 rows and fatal in
> production with 40 million. On the response side, serializing Spring Data's
> `Page` directly writes out the internals of `PageImpl`, a shape that is
> explicitly not a stable contract and has changed between Spring Data
> versions; Spring Data 3.3 added `org.springframework.data.web.PagedModel`
> and the `@EnableSpringDataWebSupport(pageSerializationMode = VIA_DTO)`
> switch precisely because of this. Either use those or define your own
> envelope record — but never let `PageImpl` be your JSON schema.
> **Suggestion.**

```java
// bad — unbounded query, and PageImpl's internals become the wire format
@GetMapping("/orders")
public Page<Order> list(Pageable pageable) {
  return orders.findAll(pageable);
}

// good — an envelope you own, over a bounded query
public record PageResponse<T>(List<T> items, int page, int size, long totalElements) {

  public static <E, T> PageResponse<T> from(Page<E> page, Function<E, T> mapper) {
    return new PageResponse<>(
        page.getContent().stream().map(mapper).toList(),
        page.getNumber(),
        page.getSize(),
        page.getTotalElements());
  }
}

@GetMapping("/orders")
public PageResponse<OrderResponse> list(
    @PageableDefault(size = 20) @SortDefault(sort = "placedAt", direction = Direction.DESC)
        Pageable pageable) {
  return PageResponse.from(orderQueries.findAll(pageable), OrderResponse::from);
}
```

## 34.18 Declare outbound HTTP clients as `@HttpExchange` interfaces, not hand-written call sites.

> Why? A declarative HTTP interface makes the remote contract a Java type: the
> URL template, method, and body shape live in one place, the return type is
> checked by the compiler, and the interface can be mocked in a unit test
> without an HTTP stub server. The
> [reference](https://docs.spring.io/spring-framework/reference/integration/rest-clients.html#rest-http-service-client)
> describes the wiring — build a
> [`HttpServiceProxyFactory`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/service/invoker/HttpServiceProxyFactory.html)
> over a `RestClientAdapter` and call `createClient`. The alternative,
> `restClient.get().uri(...).retrieve().body(...)` scattered through a service,
> puts URL strings and error handling at every call site. **Suggestion.**

```java
// bad — the remote contract is spread across every method that calls it
@Service
public class ReservationService {
  private final RestClient http;

  public StockLevel stockLevel(String sku) {
    return http.get()
        .uri("https://inventory.internal/inventory/{sku}", sku)
        .retrieve()
        .body(StockLevel.class);
  }
}

// good — one interface is the contract, and it mocks like any other
@HttpExchange(url = "/inventory", accept = MediaType.APPLICATION_JSON_VALUE)
public interface InventoryClient {

  @GetExchange("/{sku}")
  StockLevel stockLevel(@PathVariable String sku);

  @PostExchange("/reservations")
  Reservation reserve(@RequestBody ReservationRequest request);
}

@Configuration(proxyBeanMethods = false)
public class InventoryClientConfiguration {

  @Bean
  public InventoryClient inventoryClient(RestClient.Builder builder) {
    RestClient restClient = builder.baseUrl("https://inventory.internal").build();
    return HttpServiceProxyFactory.builderFor(RestClientAdapter.create(restClient))
        .build()
        .createClient(InventoryClient.class);
  }
}
```

## 34.19 Use `RestClient` for new synchronous HTTP calls, not `RestTemplate`.

> Why? `RestTemplate` is not deprecated, but its
> [javadoc](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/client/RestTemplate.html)
> states the position plainly: "As of 6.1, `RestClient` offers a more modern
> API for synchronous HTTP access", and "`RestClient` is the focus for new
> higher-level features." They share the same request factories, interceptors,
> and message converters, so migration is mechanical and mixed use is safe.
> `RestClient` also has a fluent error-handling hook (`onStatus`), which
> `RestTemplate` only offers through a global `ResponseErrorHandler`.
> **Suggestion.**

```java
// bad — the template API for new code, with exchange() generics and a
// ParameterizedTypeReference to get a generic body back
ResponseEntity<List<StockLevel>> response =
    restTemplate.exchange(
        "https://inventory.internal/inventory",
        HttpMethod.GET,
        null,
        new ParameterizedTypeReference<List<StockLevel>>() {});
List<StockLevel> levels = response.getBody();

// good
List<StockLevel> levels =
    restClient
        .get()
        .uri("/inventory")
        .retrieve()
        .onStatus(
            HttpStatusCode::is5xxServerError,
            (request, response) -> {
              throw new InventoryUnavailableException(response.getStatusCode());
            })
        .body(new ParameterizedTypeReference<List<StockLevel>>() {});
```

## 34.20 Never block inside a WebFlux reactive chain.

> Why? A reactive pipeline runs on a small, fixed-size event-loop pool — often
> one thread per core. A `block()`, a JDBC call, or a `Thread.sleep` inside a
> `map` parks one of those threads, and a handful of concurrent requests will
> stall the entire server, including requests that touch none of the blocking
> code. The failure is not a slow endpoint; it is a dead process. If a
> blocking call is unavoidable, push it onto
> `Schedulers.boundedElastic()` so it parks a thread from a pool designed to
> be parked. [BlockHound](https://github.com/reactor/BlockHound) instruments
> the JVM to fail a test the moment a blocking call runs on a non-blocking
> thread — wire it into the test suite of any WebFlux service. **Suggestion.**

```java
// bad — a JDBC call and a block() on the event loop
@GetMapping("/orders/{id}")
public Mono<OrderResponse> get(@PathVariable UUID id) {
  return Mono.just(id)
      .map(orderId -> jdbcOrderRepository.findById(orderId).orElseThrow())
      .map(order -> enrichmentClient.enrich(order).block());
}

// good — blocking work is isolated on boundedElastic; the rest stays reactive
@GetMapping("/orders/{id}")
public Mono<OrderResponse> get(@PathVariable UUID id) {
  return Mono.fromCallable(() -> jdbcOrderRepository.findById(id).orElseThrow())
      .subscribeOn(Schedulers.boundedElastic())
      .flatMap(enrichmentClient::enrich)
      .map(OrderResponse::from);
}
```

## 34.21 Configure CORS centrally, not with `@CrossOrigin` on individual controllers.

> Why? CORS is a security policy, and a policy scattered across thirty
> controllers is a policy nobody can audit — the one endpoint that was
> annotated `@CrossOrigin(origins = "*")` during a debugging session is
> invisible in review and permanent in production. A single
> `WebMvcConfigurer` puts the whole policy in one file that a security
> reviewer can read in thirty seconds. Note also that
> [`allowCredentials(true)` cannot be combined with a `*` origin](https://docs.spring.io/spring-framework/reference/web/webmvc-cors.html);
> use `allowedOriginPatterns` if you need wildcards with credentials.
> **Suggestion.**

```java
// bad — per-controller policy, and a wildcard that nobody will find again
@RestController
@CrossOrigin(origins = "*")
public class OrderController {}

// good — one auditable policy for the whole API surface
@Configuration(proxyBeanMethods = false)
public class WebCorsConfiguration implements WebMvcConfigurer {

  private final CorsProperties properties;

  public WebCorsConfiguration(CorsProperties properties) {
    this.properties = properties;
  }

  @Override
  public void addCorsMappings(CorsRegistry registry) {
    registry
        .addMapping("/api/**")
        .allowedOrigins(properties.allowedOrigins().toArray(String[]::new))
        .allowedMethods("GET", "POST", "PUT", "DELETE")
        .allowedHeaders("Authorization", "Content-Type", "Idempotency-Key")
        .allowCredentials(true)
        .maxAge(3600);
  }
}
```
