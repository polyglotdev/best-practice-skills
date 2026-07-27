<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 36. Spring: Testing

Spring's testing support is a ladder, and the cost of each rung is roughly
an order of magnitude above the one below it. A plain JUnit test that
constructs the class under test with `new` runs in microseconds. A slice
test that boots a fraction of the context runs in a second or two. A
`@SpringBootTest` that starts the whole application, a web server, and a
database container runs in tens of seconds — and, if it happens to need a
context nobody else needs, it pays that cost again for every distinct
configuration in the suite.

The single most consequential decision in a Spring test suite is therefore
which rung you climb to, and the default answer is "the lowest one that can
actually observe the behaviour you care about." A suite that reaches for
`@SpringBootTest` reflexively does not fail; it just gets slower every
sprint until nobody runs it locally.

This chapter draws on
[Spring Boot: Testing Spring Boot Applications](https://docs.spring.io/spring-boot/3.4/reference/testing/spring-boot-applications.html),
[Spring Boot: Testcontainers](https://docs.spring.io/spring-boot/3.4/reference/testing/testcontainers.html),
and
[Spring Framework: Context Caching](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/ctx-management/caching.html).
It assumes Spring Boot 3.4+ for `@MockitoBean` and 3.1+ for
`@ServiceConnection`.

Two neighbouring topics live elsewhere. General testing discipline — naming,
arrange/act/assert, one behaviour per test, AssertJ over JUnit assertions,
what not to mock — is [Chapter 31](31-testing.md) and is not repeated here.
Transaction semantics, including what `@Transactional` actually does to a
unit of work, are [Chapter 35](35-spring-data-and-transactions.md); §36.17
covers only what those semantics mean inside a test.

**Tool alignment:** none of this is mechanically enforced. Checkstyle and
Error Prone cannot tell a necessary `@SpringBootTest` from a lazy one, so
every rule below is a **Suggestion**. The one measurable proxy is your
build's context-load count — Spring logs each context refresh, and a suite
that refreshes more than a handful of times is violating §36.11.

## 36.1 Default to a plain JUnit test with no Spring context at all.

> Why? Business logic does not need a container to run. If a class's
> collaborators arrive through its constructor — which
> [Chapter 32](32-spring-beans-and-di.md) requires — then a test can
> construct it directly with test doubles and observe it in microseconds.
> Booting a context to test a method that does arithmetic buys nothing and
> costs seconds per test class. The rule of thumb: if the behaviour under
> test does not involve Spring (no proxying, no wiring, no auto-configuration,
> no HTTP), Spring should not be in the test.

```java
// bad — a whole application context to test a pure calculation
@SpringBootTest
class PricingServiceTest {
  @Autowired private PricingService pricing;
  @MockitoBean private DiscountRepository discounts;

  @Test
  void appliesPercentageDiscount() {
    given(discounts.findFor("SUMMER")).willReturn(Optional.of(new Discount(10)));
    assertThat(pricing.priceFor("SUMMER", new BigDecimal("100.00")))
        .isEqualByComparingTo("90.00");
  }
}

// good — no context, same coverage, ~1000x faster
class PricingServiceTest {
  private final DiscountRepository discounts = mock(DiscountRepository.class);
  private final PricingService pricing = new PricingService(discounts);

  @Test
  void appliesPercentageDiscount() {
    given(discounts.findFor("SUMMER")).willReturn(Optional.of(new Discount(10)));
    assertThat(pricing.priceFor("SUMMER", new BigDecimal("100.00")))
        .isEqualByComparingTo("90.00");
  }
}
```

## 36.2 Never reach for `@Autowired` field injection to assemble a unit test.

> Why? `@Autowired` on a test field is the symptom that tells you a context
> is being booted for no reason. It also hides the class's real dependency
> list: a constructor with five parameters is visibly too big, while five
> `@Autowired` fields look tidy. Constructing the subject explicitly makes
> the design pressure visible in the test, which is one of the main things
> tests are for.

```java
// bad — the test can't be read without knowing what the context wires up
@SpringBootTest
class OrderServiceTest {
  @Autowired private OrderService orderService;
}

// good — every collaborator is named, and the constructor's size is obvious
class OrderServiceTest {
  private final OrderRepository orders = mock(OrderRepository.class);
  private final InventoryClient inventory = mock(InventoryClient.class);
  private final OrderService orderService = new OrderService(orders, inventory);
}
```

## 36.3 When you do need Spring, reach for the narrowest slice that covers the behaviour.

> Why? Slice annotations exist so you can boot the part of the context a
> layer needs and nothing else. `@WebMvcTest` "limits scanned beans to
> `@Controller`, `@ControllerAdvice`, … `Filter`, `HandlerInterceptor`,
> `WebMvcConfigurer`", and explicitly notes that "Regular `@Component` and
> `@ConfigurationProperties` beans are not scanned." That exclusion is the
> point: a controller test that cannot accidentally reach the database is a
> controller test.

```java
// bad — full context to assert an HTTP status code
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderControllerTest { }

// good — web layer only
@WebMvcTest(OrderController.class)
class OrderControllerTest { }
```

## 36.4 Test the web layer with `@WebMvcTest` naming the controller under test, and drive it through `MockMvc`.

> Why? `@WebMvcTest` "also auto-configures `MockMvc`", which exercises the
> full Spring MVC stack — argument resolution, validation, content
> negotiation, `@ControllerAdvice` exception mapping, JSON serialisation —
> without binding a socket. Naming the controller class narrows the slice
> further: an unqualified `@WebMvcTest` loads *every* controller in the
> application, which reintroduces the cost you were avoiding and creates a
> second distinct context (§36.11). Boot 3.4+ also offers `MockMvcTester`,
> which wraps `MockMvc` with AssertJ assertions; prefer it in new code for
> consistency with the rest of the suite.

```java
// bad — loads every controller, and asserts on the service instead of the
// HTTP contract the slice exists to verify
@WebMvcTest
class OrderControllerTest {
  @Autowired private OrderController controller;

  @Test
  void returnsOrder() {
    assertThat(controller.get(1L).status()).isEqualTo("PAID");
  }
}

// good — one controller, driven over the real MVC stack
@WebMvcTest(OrderController.class)
class OrderControllerTest {
  @Autowired private MockMvc mockMvc;
  @MockitoBean private OrderService orderService;

  @Test
  void returnsOrderAsJson() throws Exception {
    given(orderService.find(1L)).willReturn(new OrderView(1L, "PAID"));

    mockMvc
        .perform(get("/orders/1"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value(1))
        .andExpect(jsonPath("$.status").value("PAID"));
  }

  @Test
  void returns404WhenMissing() throws Exception {
    given(orderService.find(99L)).willThrow(new OrderNotFoundException(99L));

    mockMvc.perform(get("/orders/99")).andExpect(status().isNotFound());
  }
}
```

## 36.5 Use `@MockitoBean` rather than the deprecated `@MockBean`, and mock only the layer directly beneath the slice.

> Why? Spring Framework 6.2 introduced
> `org.springframework.test.context.bean.override.mockito.MockitoBean` as
> the replacement for Boot's `@MockBean`, which is deprecated as of Spring
> Boot 3.4. The bean-override mechanism is part of the TestContext framework
> proper, so it composes with the rest of Spring's testing support instead of
> sitting beside it. The second half of the rule matters more: each
> `@MockitoBean` you add is a lie you have to maintain, and — per §36.11 —
> a new cache key. Mock the boundary the slice deliberately excludes, and
> nothing else.

```java
// bad — deprecated annotation, and mocking three layers down means the test
// no longer proves the controller talks to the service correctly
@WebMvcTest(OrderController.class)
class OrderControllerTest {
  @MockBean private OrderRepository orders;
  @MockBean private InventoryClient inventory;
  @MockBean private PricingService pricing;
}

// good — one mock, at the exact boundary the slice cuts
@WebMvcTest(OrderController.class)
class OrderControllerTest {
  @Autowired private MockMvc mockMvc;
  @MockitoBean private OrderService orderService;
}
```

## 36.6 Test repository queries with `@DataJpaTest`, and let it configure the persistence slice.

> Why? `@DataJpaTest` loads the JPA infrastructure, the entity scan, and
> Spring Data repositories, and skips everything else — no controllers, no
> `@Service` beans, no web server. It also supplies `TestEntityManager`,
> whose `persistAndFlush` and `clear` let you set up rows and then force a
> genuine database read rather than a first-level-cache hit, which is the
> difference between testing your query and testing Hibernate's cache.

```java
// bad — without flush and clear the rows come straight back out of the
// first-level cache, so the mapping the query depends on is never round-tripped
@DataJpaTest
class OrderRepositoryTest {
  @Autowired private OrderRepository orders;

  @Test
  void findsByStatus() {
    orders.save(new Order("PAID"));
    assertThat(orders.findByStatus("PAID")).hasSize(1);
  }
}

// good — flush and clear force a real round trip
@DataJpaTest
class OrderRepositoryTest {
  @Autowired private TestEntityManager entityManager;
  @Autowired private OrderRepository orders;

  @Test
  void findsByStatus() {
    entityManager.persistAndFlush(new Order("PAID"));
    entityManager.persistAndFlush(new Order("PENDING"));
    entityManager.clear();

    assertThat(orders.findByStatus("PAID")).extracting(Order::getStatus).containsExactly("PAID");
  }
}
```

## 36.7 Pin the wire format of a serialised type with `@JsonTest`.

> Why? A DTO's JSON shape is a published contract, and it changes silently:
> rename a record component, add a `@JsonInclude`, upgrade Jackson, and a
> client breaks with no compile error anywhere. `@JsonTest` boots only the
> object mapper and supplies `JacksonTester`, so a contract test costs
> milliseconds and fails at exactly the commit that changed the shape.

```java
// bad — asserting on a string built by the mapper you're trying to test
class OrderViewTest {
  @Test
  void serialises() throws Exception {
    String json = new ObjectMapper().writeValueAsString(new OrderView(1L, "PAID"));
    assertThat(json).contains("PAID"); // passes even if the field is renamed
  }
}

// good — the application's configured mapper, asserted field by field
@JsonTest
class OrderViewJsonTest {
  @Autowired private JacksonTester<OrderView> json;

  @Test
  void serialisesToPublishedContract() throws Exception {
    JsonContent<OrderView> written = json.write(new OrderView(1L, "PAID"));

    assertThat(written).extractingJsonPathNumberValue("$.id").isEqualTo(1);
    assertThat(written).extractingJsonPathStringValue("$.status").isEqualTo("PAID");
  }
}
```

## 36.8 Test outbound HTTP clients with `@RestClientTest` and `MockRestServiceServer`.

> Why? An HTTP client has three things worth testing — the request it
> builds, the response it parses, and what it does with an error status —
> and none of them require a real server. `@RestClientTest` auto-configures
> `MockRestServiceServer`, which intercepts at the `ClientHttpRequestFactory`
> level, so the client's own interceptors, message converters, and error
> handler all run. Stubbing the client interface with Mockito instead tests
> nothing but your stub.

```java
// bad — mocks the class under test; the URL, headers, and parsing are
// never exercised
class InventoryClientTest {
  private final RestClient restClient = mock(RestClient.class);
}

// good
@RestClientTest(InventoryClient.class)
class InventoryClientTest {
  @Autowired private InventoryClient client;
  @Autowired private MockRestServiceServer server;

  @Test
  void requestsStockBySku() {
    server
        .expect(requestTo("/inventory/ABC-1"))
        .andRespond(withSuccess("{\"sku\":\"ABC-1\",\"onHand\":7}", MediaType.APPLICATION_JSON));

    assertThat(client.stockFor("ABC-1").onHand()).isEqualTo(7);
    server.verify();
  }
}
```

## 36.9 Use `@SpringBootTest(webEnvironment = RANDOM_PORT)` only for genuine end-to-end coverage.

> Why? `RANDOM_PORT` "Loads a `WebServerApplicationContext` and provides a
> real web environment. Embedded servers are started and listen on a random
> port." That is the right tool for a handful of tests that prove the whole
> stack agrees: real HTTP, real serialisation, real filters, real security,
> real database. It is the wrong tool for everything else, and the random
> port matters — a fixed `DEFINED_PORT` makes the suite fail when a
> developer has the app running locally, and makes parallel execution
> impossible. Drive it with `TestRestTemplate`, which is pre-configured with
> the server's base URL.

```java
// bad — full stack booted to check one branch of one service method
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class DiscountRoundingTest { }

// good — a small number of genuinely end-to-end journeys
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderCheckoutEndToEndTest {
  @Autowired private TestRestTemplate restTemplate;

  @Test
  void checkoutPersistsOrderAndReturnsReceipt() {
    ResponseEntity<ReceiptView> response =
        restTemplate.postForEntity("/orders/1/checkout", null, ReceiptView.class);

    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    assertThat(response.getBody().reference()).isNotBlank();
  }
}
```

## 36.10 Never use `@SpringBootTest` to test a single class.

> Why? This is §36.1 and §36.3 restated as the thing reviewers actually see.
> `@SpringBootTest` on a class whose test doubles are all `@MockitoBean`
> stubs is a unit test wearing a container: it proves nothing the plain
> constructor test would not, and it adds a full context refresh plus — per
> §36.11 — a cache key that nothing else shares. If the only Spring feature
> the test exercises is dependency injection, it does not need Spring.

```java
// bad — the context exists solely to hand you one bean
@SpringBootTest
class ShippingCalculatorTest {
  @Autowired private ShippingCalculator calculator;
  @MockitoBean private RateRepository rates;
}

// good
class ShippingCalculatorTest {
  private final RateRepository rates = mock(RateRepository.class);
  private final ShippingCalculator calculator = new ShippingCalculator(rates);
}
```

## 36.11 Keep the number of distinct context configurations small, and make the ones you keep identical.

> Why? This is the rule that decides whether your suite takes ninety seconds
> or nine minutes. "Spring's test framework caches application contexts
> between tests. Therefore, as long as your tests share the same
> configuration (no matter how it is discovered), the potentially
> time-consuming process of loading the context happens only once." The
> cache key is built from a specific list: `locations`, `classes`,
> `contextInitializerClasses`, `contextCustomizers`, `contextLoader`,
> `parent`, `activeProfiles`, `propertySourceDescriptors`,
> `propertySourceProperties`, and `resourceBasePath`. Crucially,
> `contextCustomizers` "includes `@DynamicPropertySource` methods, bean
> overrides (such as `@TestBean`, `@MockitoBean`, `@MockitoSpyBean` etc.)"
> — so **every distinct set of `@MockitoBean` declarations is a distinct
> context**. Add to that a bounded cache: "The size of the context cache is
> bounded with a default maximum size of 32. Whenever the maximum size is
> reached, a least recently used (LRU) eviction policy is used to evict and
> close stale contexts." Past 32 configurations you begin re-loading
> contexts you already built.

```java
// bad — three classes, three different mock sets, three separate contexts
@SpringBootTest
class OrderFlowTest {
  @MockitoBean private PaymentGateway payments;
}

@SpringBootTest
class RefundFlowTest {
  @MockitoBean private PaymentGateway payments;
  @MockitoBean private Mailer mailer;
}

@SpringBootTest
class CancellationFlowTest {
  @MockitoBean private Mailer mailer;
}

// good — one shared configuration, one context, loaded once
@SpringBootTest
abstract class AbstractIntegrationTest {
  @MockitoBean protected PaymentGateway payments;
  @MockitoBean protected Mailer mailer;
}

class OrderFlowTest extends AbstractIntegrationTest { }

class RefundFlowTest extends AbstractIntegrationTest { }

class CancellationFlowTest extends AbstractIntegrationTest { }
```

## 36.12 Do not add per-class `properties`, `@TestPropertySource`, or `@ActiveProfiles` variations.

> Why? Each of these appears verbatim in the cache key from §36.11:
> `propertySourceDescriptors` and `propertySourceProperties` come from
> `@TestPropertySource`, and `activeProfiles` from `@ActiveProfiles`. A
> one-line `properties = {"feature.x.enabled=true"}` on a single test class
> therefore costs a full extra application context. If a handful of tests
> need a flag flipped, either group them all under one shared base class
> that carries the override, or — better — make the flag an ordinary
> constructor parameter so a plain unit test can set it.

```java
// bad — one property override, one whole extra context
@SpringBootTest(properties = "features.express-checkout.enabled=true")
class ExpressCheckoutTest { }

// good (option A) — one shared configuration for every test that needs it
@SpringBootTest(properties = "features.express-checkout.enabled=true")
abstract class AbstractExpressCheckoutTest { }

// good (option B) — the flag is a constructor parameter, so no context at all
class ExpressCheckoutTest {
  private final OrderRepository orders = mock(OrderRepository.class);
  private final CheckoutService checkout =
      new CheckoutService(orders, new FeatureFlags(/* expressCheckout= */ true));
}
```

## 36.13 Treat `@DirtiesContext` as a last resort, and never put it on a base class.

> Why? `@DirtiesContext` "instructs Spring to remove the context from the
> cache and rebuild the application context before running the next test
> that requires the same application context." On one test class that is a
> few extra seconds. On a shared base class it means every subclass rebuilds
> the context, which converts a cached suite into a serial re-boot and is
> the most common cause of a suite that takes minutes for no visible reason.
> If a test dirties the context, the usual fix is to stop mutating shared
> state — reset the mock, roll back the transaction, or clear the cache in an
> `@AfterEach` — not to throw the context away.

```java
// bad — every subclass reloads the whole context
@SpringBootTest
@DirtiesContext
abstract class AbstractIntegrationTest { }

// good — undo the specific mutation instead
@SpringBootTest
abstract class AbstractIntegrationTest {
  @Autowired private CacheManager cacheManager;

  @AfterEach
  void clearCaches() {
    for (String name : cacheManager.getCacheNames()) {
      Cache cache = cacheManager.getCache(name);
      if (cache != null) {
        cache.clear();
      }
    }
  }
}
```

## 36.14 Test against the real database engine with Testcontainers, never an in-memory substitute.

> Why? H2 in PostgreSQL compatibility mode is a different database. It
> diverges on upserts, JSON and array columns, partial and expression
> indexes, `for update skip locked`, sequence semantics, collation, and the
> vendor error codes your constraint-violation handling switches on. Every
> divergence is a test that passes in CI and fails in production — the worst
> possible outcome, because it consumed the budget a real test would have
> used. Testcontainers starts the actual engine, so the SQL under test is the
> SQL you ship. See [Chapter 35, §35.21](35-spring-data-and-transactions.md).

```java
// bad — Boot silently replaces the DataSource with embedded H2
@DataJpaTest
class OrderRepositoryTest { }

// good
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {
  @Container @ServiceConnection
  static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");
}
```

## 36.15 Wire the container with `@ServiceConnection`, not a hand-written `@DynamicPropertySource`.

> Why? `org.springframework.boot.testcontainers.service.connection.ServiceConnection`
> (Spring Boot 3.1+) derives the connection details from the container type
> itself, so a `PostgreSQLContainer` produces `JdbcConnectionDetails` with no
> property names written by hand. The `@DynamicPropertySource` form works,
> but it hardcodes property keys that move between Boot versions, silently
> does nothing if a key is misspelled, and has to be copied into every base
> class. It also participates in the cache key (§36.11), so two
> near-identical registrars are two contexts.

```java
// bad — three property keys to keep in sync by hand
@Testcontainers
@SpringBootTest
class OrderRepositoryTest {
  @Container
  static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

  @DynamicPropertySource
  static void datasourceProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
    registry.add("spring.datasource.username", POSTGRES::getUsername);
    registry.add("spring.datasource.password", POSTGRES::getPassword);
  }
}

// good
@Testcontainers
@SpringBootTest
class OrderRepositoryTest {
  @Container @ServiceConnection
  static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");
}
```

## 36.16 Start one container for the whole suite, not one per test class.

> Why? A PostgreSQL container takes one to three seconds to start and become
> healthy. `@Container` on a `static` field scopes the container to the test
> class, so a suite with forty persistence test classes pays that cost forty
> times. The singleton pattern — a `static` container started once in a
> static initialiser and never stopped, left to Testcontainers' Ryuk reaper
> to clean up at JVM exit — pays it once. Put it on the shared base class
> that already exists for §36.11 so the container and the cached context
> have the same lifetime.

```java
// bad — one container per test class
@Testcontainers
@DataJpaTest
class OrderRepositoryTest {
  @Container @ServiceConnection
  static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");
}

// good — one container, one context, shared by every persistence test
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
abstract class AbstractRepositoryTest {
  @ServiceConnection
  static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

  static {
    POSTGRES.start(); // started once; reaped at JVM exit
  }
}

class OrderRepositoryTest extends AbstractRepositoryTest { }

class CustomerRepositoryTest extends AbstractRepositoryTest { }
```

## 36.17 Know what `@Transactional` on a test does — it rolls back, and it hides flush errors.

> Why? A `@Transactional` test runs inside a transaction that Spring rolls
> back afterwards, which is a genuinely good way to keep tests isolated. It
> also changes what the test can see. Everything the test wrote stays in the
> persistence context, so the assertions read the first-level cache rather
> than the database, and any constraint violation, `not null` failure, or
> optimistic-lock conflict that would surface at flush time never surfaces at
> all — the transaction is rolled back before it commits. Note that
> `@DataJpaTest` is transactional by default. If the behaviour you are
> testing includes "does this actually persist", flush explicitly, or drop
> the transaction and clean up yourself.

```java
// bad — the unique-constraint violation never happens; the test passes
@DataJpaTest
class CustomerRepositoryTest {
  @Autowired private CustomerRepository customers;

  @Test
  void rejectsDuplicateEmail() {
    customers.save(new Customer("a@example.com"));
    customers.save(new Customer("a@example.com"));
    // no flush, no commit, no violation — nothing is asserted
  }
}

// good — force the flush so the database gets a say
@DataJpaTest
class CustomerRepositoryTest {
  @Autowired private TestEntityManager entityManager;
  @Autowired private CustomerRepository customers;

  @Test
  void rejectsDuplicateEmail() {
    entityManager.persistAndFlush(new Customer("a@example.com"));

    customers.save(new Customer("a@example.com"));

    assertThatExceptionOfType(PersistenceException.class).isThrownBy(entityManager::flush);
  }
}
```

## 36.18 Build test data with typed builders in the test source, not with shared `data.sql` fixtures.

> Why? A shared fixture file is global mutable state with a slow feedback
> loop. Every test depends on rows it did not create, so the test cannot be
> read on its own; adding a row for one test can break three others; and
> when the schema changes, the file breaks every test at once with a SQL
> error rather than a compile error. A builder with sensible defaults puts
> exactly the relevant field in the test body, keeps everything else out of
> the reader's way, and moves schema drift to compile time.

```java
// bad — the test's meaning lives in a file it doesn't mention
@Sql("/fixtures/orders.sql")
@Test
void findsPaidOrders() {
  assertThat(orders.findByStatus("PAID")).hasSize(3); // why 3? read the SQL.
}

// good — the one attribute that matters is visible; the rest is defaulted
@Test
void findsPaidOrders() {
  entityManager.persistAndFlush(anOrder().withStatus("PAID").build());
  entityManager.persistAndFlush(anOrder().withStatus("PAID").build());
  entityManager.persistAndFlush(anOrder().withStatus("PENDING").build());
  entityManager.clear();

  assertThat(orders.findByStatus("PAID")).hasSize(2);
}
```

`@Sql` still has a legitimate use: schema bootstrap and genuinely global
reference data (currency codes, country lists) that no test varies. The rule
is about the arrange step of a specific test, not about seeding.

## 36.19 Declare test-only beans with `@TestConfiguration`, never `@Configuration`.

> Why? A nested `@Configuration` class is picked up by component scanning
> and becomes part of the *application's* configuration wherever the scan
> reaches it — which, for a class nested inside a test, means it silently
> replaces or supplements production beans in other tests that happen to
> scan the same package. `@TestConfiguration` is excluded from scanning and
> is contributed only when the test explicitly imports it or declares it as
> a nested class, which is exactly the scoping you want.

```java
// bad — picked up by component scanning; leaks into other tests
@SpringBootTest
class OrderFlowTest {
  @Configuration
  static class FixedClockConfig {
    @Bean
    Clock clock() {
      return Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);
    }
  }
}

// good — contributed to this test's context only
@SpringBootTest
class OrderFlowTest {
  @TestConfiguration
  static class FixedClockConfig {
    @Bean
    Clock clock() {
      return Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);
    }
  }
}
```

## 36.20 Never assert on log output.

> Why? A log line is a diagnostic for a human, not an API. Asserting on it
> couples the test to wording that any reviewer is entitled to reword, to a
> log level any operator is entitled to change, and to an appender
> configuration that differs between local and CI. If the fact being logged
> matters enough to test, it matters enough to be observable some other way:
> a returned value, a published event, a metric counter, or a record written
> to a repository. See [Chapter 30](30-logging.md).

```java
// bad — breaks on a wording change that alters no behaviour
@ExtendWith(OutputCaptureExtension.class)
class ClaimServiceTest {
  @Test
  void logsRejection(CapturedOutput output) {
    service.submit(invalidClaim());
    assertThat(output).contains("Claim rejected: invalid policy number");
  }
}

// good — assert on the outcome the log line was describing
@Test
void rejectsClaimWithInvalidPolicyNumber() {
  SubmissionResult result = service.submit(invalidClaim());

  assertThat(result.status()).isEqualTo(SubmissionStatus.REJECTED);
  assertThat(result.reason()).isEqualTo(RejectionReason.INVALID_POLICY_NUMBER);
}
```

## 36.21 Assert on observable behaviour through the boundary, not on how many times a mock was called.

> Why? `verify(repository, times(1)).save(any())` pins an implementation
> detail: it fails when a refactor batches two saves into one, and it passes
> when the saved object is completely wrong. The test that survives refactors
> asserts on what changed — the HTTP response, the returned value, the row
> that now exists. Interaction verification earns its place only when the
> interaction *is* the behaviour, as with "this must send exactly one email"
> or "this must not call the payment gateway twice"; then use an argument
> captor so you also assert on *what* was sent.

```java
// bad — passes with a completely wrong Order, fails on a harmless refactor
@Test
void savesOrder() {
  service.placeOrder(request);
  verify(orders, times(1)).save(any(Order.class));
}

// good — the interaction is the behaviour, and its content is asserted
@Test
void chargesTheOrderTotalExactlyOnce() {
  service.placeOrder(request);

  ArgumentCaptor<Money> charged = ArgumentCaptor.forClass(Money.class);
  verify(paymentGateway).charge(charged.capture());
  assertThat(charged.getValue()).isEqualTo(Money.of("42.50", "EUR"));
}
```

## 36.22 Never point a test at a shared external environment.

> Why? A test that talks to a shared staging database, a team Kafka cluster,
> or a vendor sandbox is not a test — it is a monitor for someone else's
> uptime. It fails when a colleague runs their own suite, it cannot run on a
> laptop offline, it cannot run in parallel, and its failures carry no
> information about the commit that triggered them. Everything it needs is
> available locally: Testcontainers for real infrastructure (§36.14),
> `MockRestServiceServer` or WireMock for third-party HTTP (§36.8).

```java
// bad — the suite is green or red depending on someone else's deploy
@SpringBootTest(properties = "spring.datasource.url=jdbc:postgresql://staging-db:5432/app")
class OrderRepositoryTest { }

// good — every dependency is started by the test itself; the slice and
// container configuration are inherited from the shared base of §36.16
class OrderRepositoryTest extends AbstractRepositoryTest { }
```
