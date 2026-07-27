<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 46. Spring: Testing in Kotlin

This is a **delta chapter**. The test pyramid, slice selection, why a plain
JUnit test beats `@SpringBootTest`, the context cache and everything that
perturbs its key, `@DirtiesContext`, Testcontainers over H2, `@JsonTest`,
`@RestClientTest`, `@TestConfiguration`, and the rules about asserting on
behaviour rather than on mock call counts or log output are all in
**`best-practice-java` Chapter 36, "Spring: Testing"** — read it first and
apply it unchanged. Everything there is true of a Kotlin suite.

What changes in Kotlin is the mocking library (classes are `final` by
default, which Mockito does not like), the way a test class receives its
collaborators (Spring supports constructor injection, so `lateinit var` and
`@Autowired` on fields are unnecessary), the way JUnit's lifecycle interacts
with Kotlin's lack of statics, and the whole question of how to test a
`suspend` handler or a `suspend` transactional boundary.

Rules draw on
[Spring Boot: Kotlin Support](https://docs.spring.io/spring-boot/reference/features/kotlin.html),
[Spring Framework: Testing with the SpringExtension](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/support-classes.html),
[Spring Framework: MockMvc Async Requests](https://docs.spring.io/spring-framework/reference/testing/mockmvc/hamcrest/async-requests.html),
and the [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html).
General Kotlin testing discipline — what to assert, what not to mock, naming
— is [Chapter 32](32-testing.md); the coroutine testing primitives are
[Chapter 39](39-coroutine-testing.md). The `suspend` + `@Transactional`
behaviour §46.12 probes is [Chapter 45](45-spring-data-and-transactions.md).

**Tool alignment:** no linter can tell a good Spring test from a bad one, so
every rule below is a **Suggestion** unless marked otherwise. The one
measurable proxy, as in Java, is the suite's context-refresh count.

## 46.1 Use MockK, not Mockito, for Kotlin collaborators.

> Why? Kotlin classes and methods are `final` unless opened, and Mockito's
> default subclass mock maker cannot mock a `final` type at all. In a Spring
> project the `kotlin-spring` plugin opens `@Component`-family classes, so
> Mockito appears to work — right up to the first collaborator that is a plain
> domain class, a `sealed` type, or an interface implementation the plugin does
> not cover, at which point you get `MockitoException: Cannot mock/spy class`.
> Enabling the inline mock maker hides the symptom but leaves you with a
> library that has no notion of `suspend`. Spring Boot's own
> [Kotlin guidance](https://docs.spring.io/spring-boot/reference/features/kotlin.html)
> is unambiguous: "To mock Kotlin classes, MockK is recommended." Pick one and
> use it everywhere; a suite with both has two stubbing DSLs and two failure
> vocabularies. **Suggestion.**

```kotlin
// bad — works only for as long as every collaborator happens to be open
class CheckoutServiceTest {
    private val pricing: PricingPolicy = Mockito.mock(PricingPolicy::class.java)
    private val checkout = CheckoutService(pricing)
}

// good
class CheckoutServiceTest {
    private val pricing = mockk<PricingPolicy>()
    private val checkout = CheckoutService(pricing)

    @Test
    fun `applies the configured discount`() {
        every { pricing.discountFor("SUMMER") } returns Percentage(10)

        assertThat(checkout.priceFor("SUMMER", BigDecimal("100.00")))
            .isEqualByComparingTo("90.00")
    }
}
```

## 46.2 Replace `@MockitoBean` with SpringMockK's `@MockkBean`, and keep it at the slice boundary.

> Why? Once §46.1 has settled on MockK, a bean override that installs a
> *Mockito* mock is a second mocking library smuggled into the context, with
> its own strictness rules and its own `verify`. SpringMockK exists exactly
> for this: it provides `@MockkBean` and `@SpykBean` as drop-in replacements
> for Spring's `@MockitoBean` and `@MockitoSpyBean`, and Spring Boot's Kotlin
> documentation names it as the recommended option. The second half of the
> rule is `best-practice-java` §36.5 and §36.11 unchanged: every distinct set
> of bean overrides is a distinct context-cache key, so mock the layer the
> slice deliberately excludes and nothing else. **Suggestion.**

```kotlin
// bad — Mockito mocks in a MockK codebase, and three layers of them, so the
// test no longer proves the controller talks to the service correctly
@WebMvcTest(OrderController::class)
class OrderControllerTest {
    @MockitoBean private lateinit var orders: OrderRepository
    @MockitoBean private lateinit var inventory: InventoryClient
    @MockitoBean private lateinit var pricing: PricingService
}

// good — one MockK mock, at the exact boundary the slice cuts
@WebMvcTest(OrderController::class)
class OrderControllerTest(
    @Autowired private val mockMvc: MockMvc,
) {
    @MockkBean private lateinit var orderService: OrderService

    @Test
    fun `returns the order as JSON`() {
        every { orderService.find(1L) } returns OrderView(1L, OrderStatus.PAID)

        mockMvc.get("/orders/1").andExpect {
            status { isOk() }
            jsonPath("$.status") { value("PAID") }
        }
    }
}
```

## 46.3 Stub and verify `suspend` collaborators with `coEvery` and `coVerify`.

> Why? A `suspend` function compiles to a JVM method with a trailing
> `Continuation` parameter, and it can only be called from inside a coroutine.
> MockK's `every { }` and `verify { }` take ordinary lambdas, so a `suspend`
> call inside one does not compile at all. That is the good case: the compiler
> stops you. Use the
> `co`-prefixed variants, which take suspending lambdas: `coEvery`,
> `coVerify`, `coJustRun`, and `coAnswers`. See
> [Chapter 32](32-testing.md). **Suggestion.**

```kotlin
// bad — every { } cannot host a suspending call
class CheckoutServiceTest {
    private val inventory = mockk<InventoryClient>()

    @Test
    fun `reserves stock`() = runTest {
        every { inventory.reserve("ABC-1", 2) } returns Reservation("r-1") // does not compile
    }
}

// good
class CheckoutServiceTest {
    private val inventory = mockk<InventoryClient>()
    private val checkout = CheckoutService(inventory)

    @Test
    fun `reserves the requested quantity exactly once`() = runTest {
        coEvery { inventory.reserve("ABC-1", 2) } returns Reservation("r-1")

        checkout.placeOrder(orderFor("ABC-1", quantity = 2))

        coVerify(exactly = 1) { inventory.reserve("ABC-1", 2) }
    }
}
```

## 46.4 Keep mocks strict; reach for `relaxed = true` only for a collaborator you never assert on.

> Why? MockK is strict by default: an unstubbed call throws rather than
> returning a zero value, so the test fails at the interaction you forgot to
> describe instead of two assertions later with a baffling `0` or `null`.
> `relaxed = true` turns that off globally for the mock, which means a
> production change that adds a new call to the collaborator produces a green
> test. The narrow legitimate use is a `Unit`-returning side-effect
> collaborator — a metrics recorder, an audit sink — and even then
> `relaxUnitFun = true` is the smaller hammer, since it relaxes only the
> `Unit` returns and leaves value-returning calls strict. **Suggestion.**

```kotlin
// bad — a new pricing call added in production returns 0 and the test passes
private val pricing = mockk<PricingPolicy>(relaxed = true)

// good — strict for anything whose return value the test depends on
private val pricing = mockk<PricingPolicy>()

// good — relaxed only where the return type carries no information
private val metrics = mockk<MetricsRecorder>(relaxUnitFun = true)
```

## 46.5 Take test collaborators through the test class constructor, not `@Autowired lateinit var` fields.

> Why? `SpringExtension` supports constructor injection for JUnit Jupiter test
> classes, so the Java habit of field injection buys nothing and costs the two
> things `lateinit` always costs: the property is `var` where it should be
> `val`, and reading it before assignment throws
> `UninitializedPropertyAccessException` rather than failing to compile.
> Constructor parameters are `val`, non-null, and visible as a list — which is
> the design pressure `best-practice-java` §36.2 wants a test to expose. Spring
> considers a constructor autowirable when "the constructor is annotated with
> `@Autowired`", when `@TestConstructor` sets `autowireMode` to `ALL`, or when
> the default has been changed; set the default once in
> `junit-platform.properties` and drop the annotation everywhere.
> **Suggestion.**

```kotlin
// bad — nullable-by-construction, mutable, and invisible as a dependency list
@WebMvcTest(OrderController::class)
class OrderControllerTest {
    @Autowired private lateinit var mockMvc: MockMvc
    @Autowired private lateinit var objectMapper: ObjectMapper
}

// good — src/test/resources/junit-platform.properties
// spring.test.constructor.autowire.mode = all

@WebMvcTest(OrderController::class)
class OrderControllerTest(
    private val mockMvc: MockMvc,
    private val objectMapper: ObjectMapper,
) {
    @MockkBean private lateinit var orderService: OrderService
}
```

Bean overrides are the exception: `@MockkBean` and `@MockitoBean` install the
mock into the context *after* construction, so those properties genuinely
must be `lateinit var`. That is the one place the modifier is correct in a
test class.

## 46.6 Turn on `@TestInstance(PER_CLASS)` so `@BeforeAll` and `@MethodSource` need no `@JvmStatic` companion.

> Why? JUnit's default `PER_METHOD` lifecycle requires `@BeforeAll`,
> `@AfterAll`, and `@MethodSource` factories to be `static` — a concept Kotlin
> does not have, so every one of them becomes a `companion object` plus
> `@JvmStatic`, which is four lines of ceremony around one setup call and puts
> the fixture out of reach of the test class's own constructor-injected
> properties. `PER_CLASS` instantiates the class once and lets all three be
> ordinary member functions. Spring Boot's Kotlin documentation calls this out
> as "a good fit for Kotlin". The trade is real and worth stating: with one
> instance for the whole class, mutable state written by one test is visible
> to the next, so reset it in `@BeforeEach`. **Suggestion.**

```kotlin
// bad — a companion object exists solely to satisfy JUnit's static requirement
class TaxCalculatorTest {
    companion object {
        @JvmStatic
        fun rates(): Stream<Arguments> =
            Stream.of(Arguments.of("IE", "0.23"), Arguments.of("DE", "0.19"))

        @BeforeAll
        @JvmStatic
        fun loadTables() { /* ... */ }
    }
}

// good
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class TaxCalculatorTest {

    @BeforeAll
    fun loadTables() { /* ... */ }

    fun rates(): List<Arguments> =
        listOf(Arguments.of("IE", "0.23"), Arguments.of("DE", "0.19"))

    @ParameterizedTest
    @MethodSource("rates")
    fun `applies the country rate`(country: String, rate: String) { /* ... */ }
}
```

## 46.7 Name tests as backticked sentences.

> Why? This is the one place Kotlin permits spaces in a function name, and the
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#names-for-test-methods)
> sanction it explicitly: "In tests (and only in tests), you can use method
> names with spaces enclosed in backticks." A test name is a specification
> line read in a failure report, so `shouldReturn404WhenOrderIsMissing` is
> strictly worse than the sentence it is encoding. Note the one exception the
> conventions attach — backticked names "are only supported by Android runtime
> from API level 30" — and the
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#function_names)
> bans them outright for that reason: "Function names should not contain
> spaces because this is not supported on every platform (notably, this is not
> fully supported in Android)." On a server-side
> Spring service neither constraint applies, and the conventions' underscore
> form is the fallback if your team wants one rule across both. **Suggestion.**

```kotlin
// bad — camelCase run together; the failure report is unreadable
@Test
fun returns404WhenOrderDoesNotExist() { /* ... */ }

// good
@Test
fun `returns 404 when the order does not exist`() { /* ... */ }

// acceptable — the underscore form, if a shared Android module forbids spaces
@Test
fun get_returns404_whenOrderDoesNotExist() { /* ... */ }
```

## 46.8 Wrap a test body that calls a `suspend` function in `runTest`, never `runBlocking`.

> Why? `runBlocking` parks the test thread and uses the real clock, so a
> service with a retry backoff or a `delay` makes the suite genuinely wait.
> `runTest` from `kotlinx-coroutines-test` runs on a `TestScheduler` with
> virtual time: `delay` calls on its dispatcher complete immediately, the test
> body still observes them in order, and unfinished child coroutines fail the
> test instead of being silently abandoned. It also enforces a timeout rather
> than hanging a CI job forever. See
> [Chapter 39](39-coroutine-testing.md). **Suggestion.**

```kotlin
// bad — reserveWithRetry backs off for two real seconds, and so does the suite
@Test
fun `retries a failed reservation`() = runBlocking {
    coEvery { inventory.reserve(any(), any()) } throws IOException() andThen Reservation("r-1")

    assertThat(checkout.reserveWithRetry("ABC-1", 1).id).isEqualTo("r-1")
}

// good — virtual time; the same coverage in microseconds
@Test
fun `retries a failed reservation`() = runTest {
    coEvery { inventory.reserve(any(), any()) } throws IOException() andThen Reservation("r-1")

    assertThat(checkout.reserveWithRetry("ABC-1", 1).id).isEqualTo("r-1")
}
```

## 46.9 Do not expect `runTest`'s virtual clock to advance anything running inside the Spring context.

> Why? Virtual time belongs to the `TestDispatcher` that `runTest` installs,
> and it only skips `delay` for coroutines that actually run on that
> dispatcher. A Spring bean that does its work under
> `withContext(Dispatchers.IO)`, a `@Scheduled` method, a Reactor pipeline
> behind `WebClient`, a Testcontainers database — none of them are on the test
> scheduler, so their timings are real, `advanceUntilIdle()` does nothing for
> them, and `runTest`'s own timeout is now racing genuine wall-clock work.
> Integration tests are where this bites, because the mixture is invisible in
> the test source. The fix is the same fix as
> [Chapter 45, §45.5](45-spring-data-and-transactions.md): inject the dispatcher, so
> the test can hand the bean a `TestDispatcher` and bring it under the
> scheduler. **Suggestion.**

```kotlin
// bad — the bean hardcodes Dispatchers.IO, so advanceUntilIdle() is a no-op
// and the assertion races real work
@SpringBootTest
class ReconciliationServiceTest(private val reconciliation: ReconciliationService) {

    @Test
    fun `settles every pending order`() = runTest {
        reconciliation.runOnce()
        advanceUntilIdle()
        assertThat(reconciliation.settledCount()).isEqualTo(3)
    }
}

// good — the dispatcher is a bean, and the test replaces it
@TestConfiguration(proxyBeanMethods = false)
class TestDispatcherConfiguration {
    @Bean
    fun ioDispatcher(): CoroutineDispatcher = StandardTestDispatcher()
}

@SpringBootTest
@Import(TestDispatcherConfiguration::class)
class ReconciliationServiceTest(
    private val reconciliation: ReconciliationService,
    private val ioDispatcher: CoroutineDispatcher,
) {
    @Test
    fun `settles every pending order`() =
        runTest(ioDispatcher) {
            reconciliation.runOnce()
            advanceUntilIdle()
            assertThat(reconciliation.settledCount()).isEqualTo(3)
        }
}
```

## 46.10 Drive a `suspend` MVC handler through `WebTestClient`, or perform the async dispatch by hand.

> Why? Spring MVC completes a suspending handler through the Servlet async
> path, so the first `MockMvc` exchange returns before the handler's value
> exists. The async-started response already carries status 200 and an empty
> body, so a naive `andExpect { status { isOk() } }` passes for the wrong
> reason, and any body assertion added next fails against an empty body with
> an error that says nothing about async dispatching. The
> [reference](https://docs.spring.io/spring-framework/reference/testing/mockmvc/hamcrest/async-requests.html)
> describes the manual sequence: assert the async result, then "manually
> performing the async dispatch, and finally verifying the response". It also
> gives the shortcut: "If using MockMvc through the `WebTestClient`, there is
> nothing special to do to make asynchronous requests work as the
> `WebTestClient` automatically does what is described in this section." Every
> `suspend` handler you add converts its existing MockMvc tests into this
> shape, which is one more reason not to add the modifier without a purpose
> ([Chapter 44, §44.3](44-spring-web-and-coroutines.md)). **Suggestion.**

```kotlin
// bad — asserts on the async-started response, before the handler produced
// anything: the status check passes vacuously, the jsonPath check blows up
// on an empty body
@Test
fun `returns the order`() {
    mockMvc.get("/orders/1").andExpect {
        status { isOk() }
        jsonPath("$.status") { value("PAID") }
    }
}

// good — the two-step dispatch MockMvc requires
@Test
fun `returns the order`() {
    val started = mockMvc.get("/orders/1").andExpect { request { asyncStarted() } }.andReturn()

    mockMvc
        .perform(MockMvcRequestBuilders.asyncDispatch(started))
        .andExpect(MockMvcResultMatchers.jsonPath("$.status").value("PAID"))
}
```

Note the second call drops out of the Kotlin `MockMvc` DSL: `perform` returns
a Java `ResultActions`, whose `andExpect` takes a `ResultMatcher` rather than
the DSL's trailing lambda. That asymmetry is itself a reason to prefer
`WebTestClient` for any controller that has suspending handlers.

## 46.11 Test WebFlux and `coRouter` endpoints with `WebTestClient` bound to the context, not to a port.

> Why? `WebTestClient` is the only client that speaks the full WebFlux stack —
> codecs, `WebFilter`s, `@ControllerAdvice`, and the functional routes built by
> `coRouter` ([Chapter 44, §44.12](44-spring-web-and-coroutines.md)), which
> `MockMvc` cannot see at all because there is no
> `DispatcherServlet` involved. Binding it to the application context rather
> than to a running server keeps the test in-process: no socket, no port
> collision when a developer has the app running locally, and no obstacle to
> parallel execution. Reserve `@SpringBootTest(webEnvironment = RANDOM_PORT)`
> with an injected `WebTestClient` for the handful of genuinely end-to-end
> journeys `best-practice-java` §36.9 permits. **Suggestion.**

```kotlin
// bad — a real server booted to check one route's status code
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OrderRoutesTest(private val client: WebTestClient) {

    @Test
    fun `lists orders`() {
        client.get().uri("/orders").exchange().expectStatus().isEqualTo(HttpStatus.OK)
    }
}

// good — the WebFlux slice, in process
@WebFluxTest
@Import(OrderRoutesConfiguration::class, OrderHandler::class)
class OrderRoutesTest(private val client: WebTestClient) {

    @MockkBean private lateinit var orderService: OrderService

    @Test
    fun `streams orders as newline-delimited JSON`() {
        // stream() returns Flow and is therefore not suspend, so `every`, not `coEvery`
        every { orderService.stream() } returns flowOf(OrderView(1L, OrderStatus.PAID))

        client
            .get()
            .uri("/orders/events")
            .accept(MediaType.APPLICATION_NDJSON)
            .exchange()
            .expectStatus()
            .isEqualTo(HttpStatus.OK)
            .expectBodyList(OrderView::class.java)
            .hasSize(1)
    }
}
```

## 46.12 Write the `suspend` + `@Transactional` test so that it is capable of failing.

> Why? [Chapter 45, §45.1](45-spring-data-and-transactions.md) explains why
> `@Transactional` on a `suspend` function backed by a
> `PlatformTransactionManager` commits at the first suspension point. The
> defect is invisible to a naive test for two compounding reasons. First, if
> nothing in the method body actually reaches a suspension point — every call
> resolves synchronously, as it will when the collaborators are mocks — the
> JVM method returns normally and the transaction behaves. Second, a test
> annotated `@Transactional` runs inside its own outer transaction that Spring
> rolls back afterwards, so *everything* looks rolled back regardless of what
> the code under test did. A test that proves the boundary must therefore
> force a genuine suspension inside the method and must read the database from
> outside any test-managed transaction. **Suggestion.**

```kotlin
// bad — @Transactional on the test hides the outcome, and the mocked
// collaborator never suspends, so the boundary is never exercised
@SpringBootTest
@Transactional
class TransferServiceTest(private val transfers: TransferService) {

    @MockkBean private lateinit var auditClient: AuditClient

    @Test
    fun `rolls back a failed transfer`() = runTest {
        coEvery { auditClient.record(any(), any(), any()) } returns Unit

        assertThrows<InsufficientFundsException> {
            transfers.transfer("A", "B", BigDecimal.TEN)
        }
    }
}

// good — no test transaction, a real suspension inside the unit, and the
// assertion reads committed state
@SpringBootTest
class TransferServiceTest(
    private val transfers: TransferService,
    private val accounts: AccountRepository,
) {
    @MockkBean private lateinit var auditClient: AuditClient

    @AfterEach
    fun cleanUp() {
        accounts.deleteAll()
    }

    @Test
    fun `rolls back the debit when the credit fails`() = runTest {
        accounts.save(AccountEntity(number = "A", balance = BigDecimal("100.00")))
        // coAnswers with a real delay forces an actual suspension inside the unit
        coEvery { auditClient.record(any(), any(), any()) } coAnswers { delay(1) }

        assertThrows<UnknownAccountException> {
            transfers.transfer("A", "MISSING", BigDecimal.TEN)
        }

        assertThat(accounts.balanceOf("A")).isEqualByComparingTo("100.00")
    }
}
```

## 46.13 Give every Testcontainers container an explicit type argument.

> Why? Testcontainers' Java API uses a self-referential generic —
> `PostgreSQLContainer<SELF extends PostgreSQLContainer<SELF>>` — which Kotlin's
> inference cannot resolve, so `PostgreSQLContainer("postgres:16-alpine")`
> fails with "Not enough information to infer type variable SELF". This is a
> pure Kotlin-Java interop problem with two accepted fixes: supply `Nothing`
> as the type argument, which is concise and fine when you configure the
> container through property assignment rather than a fluent chain; or declare
> a one-line subclass that closes the recursion, which restores the fluent
> builder methods. Pick one per project so a reader is not surprised.
> **Suggestion.**

```kotlin
// bad — does not compile: "Not enough information to infer type variable SELF"
val postgres = PostgreSQLContainer("postgres:16-alpine")

// good — Nothing closes the recursion
val postgres = PostgreSQLContainer<Nothing>(DockerImageName.parse("postgres:16-alpine"))

// good — a named subclass, when the fluent configuration methods are wanted
class AppPostgresContainer :
    PostgreSQLContainer<AppPostgresContainer>(DockerImageName.parse("postgres:16-alpine"))

val postgres = AppPostgresContainer().withDatabaseName("app").withReuse(true)
```

## 46.14 Declare containers as `@Bean`s carrying `@ServiceConnection` inside one shared `@TestConfiguration`.

> Why? `best-practice-java` §36.15 and §36.16 already require
> `@ServiceConnection` over a hand-written `@DynamicPropertySource`, and one
> container for the whole suite rather than one per class. Kotlin adds a
> reason to prefer the bean form over the `@Container` static field: a static
> field in Kotlin means a `companion object` with `@JvmStatic`, and the
> lifecycle annotations then sit on a member of a different object from the
> test itself. A `@TestConfiguration` with `@Bean` methods avoids all of that
> and is imported explicitly, so nothing is picked up by component scanning.
> Note Spring Boot's constraint on the bean form: "the return type of the bean
> method is used to find out which connection detail should be used," so the
> method must declare a typed container, which is exactly what §46.13 already
> forces you to write. **Suggestion.**

```kotlin
// bad — a companion object plus @JvmStatic, repeated in every test class
@Testcontainers
@SpringBootTest
class OrderRepositoryTest {
    companion object {
        @Container
        @ServiceConnection
        @JvmStatic
        val postgres = PostgreSQLContainer<Nothing>(DockerImageName.parse("postgres:16-alpine"))
    }
}

// good — one configuration, imported by one base class
@TestConfiguration(proxyBeanMethods = false)
class ContainerConfiguration {

    @Bean
    @ServiceConnection
    fun postgres(): PostgreSQLContainer<Nothing> =
        PostgreSQLContainer(DockerImageName.parse("postgres:16-alpine"))
}
```

## 46.15 Put the shared configuration on exactly one `abstract` base class.

> Why? This is `best-practice-java` §36.11 — every distinct context
> configuration is a distinct cache key, and the way to keep the count at one
> is a shared base class — with one Kotlin-specific correction: Kotlin classes
> are `final`, so a base class that a Java suite would leave as a plain `class`
> must be declared `abstract` (or `open`) here or nothing can extend it. Make
> it `abstract` rather than `open`: it is not a test itself, and `abstract`
> stops JUnit from trying to run it. Keep the container configuration, the
> profile, and any property overrides on that one class, because each of those
> attributes appears verbatim in the cache key. **Suggestion.**

```kotlin
// bad — `class` is final in Kotlin, so this does not compile as a base; and
// the per-class properties override would fork the context even if it did
@SpringBootTest(properties = ["features.express-checkout.enabled=true"])
class IntegrationTest

// good — one abstract base, one context, one container
@SpringBootTest
@Import(ContainerConfiguration::class)
@ActiveProfiles("test")
abstract class AbstractIntegrationTest

class OrderFlowTest(private val orders: OrderRepository) : AbstractIntegrationTest()

class RefundFlowTest(private val refunds: RefundRepository) : AbstractIntegrationTest()
```

## 46.16 Adopt Kotest only if the whole suite adopts it, and wire it with the Kotest Spring extension.

> Why? Kotest's spec styles and its `shouldBe`/`shouldThrow` matchers are a
> genuine readability gain, and its `coroutineTestScope` support makes
> suspending assertions natural. The cost is that it is a different test engine
> with a different lifecycle, so a mixed suite has two ways to write a test,
> two failure formats, two IDE run configurations, and two places to configure
> parallelism — which is exactly the friction that stops people running the
> suite. It also does not get Spring for free: without the
> `kotest-extensions-spring` module and its `SpringExtension` registered — in
> project config, or per spec with `@ApplyExtension` — the Spring annotations
> on a spec are inert, no context is created, and constructor parameters are
> not autowired. Decide once, at the module level, and write it down.
> **Suggestion.**

```kotlin
// bad — @SpringBootTest on a Kotest spec with no SpringExtension registered:
// no context is loaded and orderService is never injected
class OrderServiceSpec : FunSpec({
    test("prices an order") { /* ... */ }
})

// good — the extension is registered, so the spec is a real Spring test
class ProjectConfig : AbstractProjectConfig() {
    override val extensions = listOf(SpringExtension())
}

// the collaborator is a plain constructor parameter captured by the spec
// lambda, which is the idiom the Kotest Spring extension documents
@SpringBootTest
class OrderServiceSpec(orderService: OrderService) : FunSpec({

    test("returns null for an unknown order") {
        orderService.find(unknownId) shouldBe null
    }

    test("prices an order including tax") {
        orderService.priceOf(orderId) shouldBe Money.of("123.00", "EUR")
    }
})
```
