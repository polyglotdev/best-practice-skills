<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 32. Testing

A Kotlin test suite has more choices in front of it than a Java one: two
plausible frameworks, three assertion libraries, a mocking library written
specifically for the language, and a naming convention that the two upstream
style guides actively disagree about. This chapter makes those choices and
explains the reasoning, then covers the rules that hold regardless of which
you pick — structure, determinism, and the discipline of testing behaviour
rather than implementation.

The defaults recommended here are **JUnit 5** as the runner, **`kotlin.test`**
or **AssertJ** for assertions, and **MockK** where a test double genuinely
needs to be a mock. Kotest is a legitimate alternative and §32.17 covers when
it earns its place.

Sources are the [JUnit 5 user guide](https://junit.org/junit5/docs/current/user-guide/),
the [`kotlin.test` API reference](https://kotlinlang.org/api/core/kotlin-test/kotlin.test/),
[MockK](https://mockk.io/), [Kotest](https://kotest.io/), and the two style
guides on test naming:
[Kotlin coding conventions: names for test methods](https://kotlinlang.org/docs/coding-conventions.html#names-for-test-methods)
and
[Android Kotlin style guide: function names](https://developer.android.com/kotlin/style-guide#function_names).

**Coroutine testing is deferred entirely to
[Chapter 39, Coroutine Testing](39-coroutine-testing.md)** — `runTest`,
`TestDispatcher`, `TestScope`, virtual time, and `Turbine` for `Flow`. Nothing
in this chapter covers suspending code beyond §32.12's mocking mechanics.
**Spring test slices, context caching, and `@SpringBootTest`** are
[Chapter 46, Spring: Testing in Kotlin](46-spring-testing-kotlin.md), which
in turn defers the framework-agnostic rules to `best-practice-java`
chapter 37.

**Tool alignment:** `detekt/FunctionNaming` matches function names against
`functionPattern`, which by default permits neither spaces nor underscores —
so it interacts directly with the naming decision in §32.2 for whichever
source sets it is configured to scan. `ktlint`'s `standard:function-naming`
handles test files on its own by detecting the test-framework import.
`detekt/CoroutineLaunchedInTestWithoutRunTest` catches a coroutine launched
in a `@Test` outside `runTest`, and `detekt/SleepInsteadOfDelay` catches
`Thread.sleep` in a suspending function. Rules a named check enforces are
marked **Violation**; the rest are **Suggestion**.

## 32.1 Run tests on the JUnit Platform with JUnit Jupiter; JUnit 4 is not a starting point in 2026.

> Why? Jupiter is what every current tool assumes: `@Nested`, `@DisplayName`,
> `@ParameterizedTest`, extensions instead of runners and rules, and a
> platform that other engines (including Kotest and Spek) plug into rather
> than replace. Staying on JUnit 4 costs you all of that and forces the
> vintage engine on every consumer of your test fixtures. The Gradle
> configuration is one line and is the thing people forget — without
> `useJUnitPlatform()` the build silently runs zero tests and reports
> success, which is the most dangerous green build there is. **Suggestion.**

```kotlin
// bad — no platform configured: `./gradlew test` finds no Jupiter tests and
// passes
tasks.test {
    maxHeapSize = "2g"
}

// good
dependencies {
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.14.4")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}
```

## 32.2 Pick one test-naming convention per project; know that the two upstream guides disagree.

> Why? The
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#names-for-test-methods)
> permit it: "in tests (and only in tests), you can use method names with
> spaces enclosed in backticks", adding that "such method names are only
> supported by Android runtime from API level 30" and that "underscores in
> method names are also allowed in test code". The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#function_names)
> takes the opposite line for exactly that reason: "function names should not
> contain spaces because this is not supported on every platform", and marks
> the backticked form `// WRONG!`, permitting only underscores. This skill is
> JVM server-side, where the platform objection does not apply, so backticks
> are the recommendation — but the decision is per project and must be
> written down, because a suite with both styles is unreadable and
> unsearchable. **Suggestion** — no tool can pick the convention for you,
> but both tools have an opinion once you have. `ktlint`'s
> `standard:function-naming` treats a file as a test file when it imports from
> `io.kotest`, `junit.framework`, `kotlin.test`, `org.junit` (which covers
> `org.junit.jupiter.api`), or `org.testng`, so backticked names pass without
> configuration. `detekt/FunctionNaming`
> matches against `functionPattern`, which permits neither spaces nor
> underscores — check that your `excludes` still cover the test source sets
> if you have customised the naming ruleset.

```kotlin
// bad — three conventions in one class
class PriceCalculatorTest {
    @Test fun test1() { ... }
    @Test fun `returns zero for empty basket`() { ... }
    @Test fun appliesDiscount_whenOverThreshold() { ... }
}

// good — JVM server-side: backticks, stating behaviour and condition
class PriceCalculatorTest {
    @Test
    fun `returns zero for an empty basket`() { ... }

    @Test
    fun `applies the bulk discount when the basket exceeds the threshold`() { ... }
}

// good — Android, or any project that chose underscores
class PriceCalculatorTest {
    @Test fun total_emptyBasket_isZero() { ... }

    @Test fun total_overThreshold_appliesBulkDiscount() { ... }
}
```

```yaml
# config/detekt/detekt.yml — required if you chose backticks
naming:
  FunctionNaming:
    active: true
    excludes: ['**/test/**', '**/androidTest/**']
```

```editorconfig
# .editorconfig — lets long backticked names past the line-length rule
[**/test/**/*.kt]
ktlint_ignore_back_ticked_identifier = true
```

## 32.3 One behaviour per test, in three visually separated phases.

> Why? A test that asserts five unrelated things reports one failure and
> hides the other four, because the first assertion aborts the method. Its
> name also cannot describe what it does, which is why such tests are always
> called `testFlow` or `worksCorrectly`. Arrange-Act-Assert is not
> ceremony — it makes the *act* line, the single call under test, visually
> findable, so a reader can answer "what is exercised here?" without reading
> the whole method. In Kotlin a blank line between phases is enough; comment
> labels add noise. **Suggestion.**

```kotlin
// bad — four behaviours, one name, and only the first failure is ever reported
@Test
fun `basket works`() {
    val basket = Basket()
    assertEquals(0, basket.size)
    basket.add(item("A"))
    assertEquals(1, basket.size)
    basket.remove(item("A"))
    assertEquals(0, basket.size)
    assertTrue(basket.isEmpty)
}

// good
@Test
fun `adding an item increases the basket size`() {
    val basket = Basket()

    basket.add(item("A"))

    assertEquals(1, basket.size)
}

@Test
fun `removing the last item empties the basket`() {
    val basket = Basket().apply { add(item("A")) }

    basket.remove(item("A"))

    assertTrue(basket.isEmpty)
}
```

## 32.4 Choose one assertion library for the project and use it in every test.

> Why? Mixing `assertEquals(expected, actual)` with `actual shouldBe
> expected` and `assertThat(actual).isEqualTo(expected)` in one suite means
> every reader has to re-derive the argument order at every call, and the
> three produce differently-shaped failure messages, so the suite has no
> consistent diagnostic quality. All three are reasonable choices:
> `kotlin.test` is dependency-free and multiplatform, AssertJ has the richest
> collection and exception assertions, Kotest's matchers read best.
> Consistency matters far more than which one. **Suggestion.**

```kotlin
// bad — three libraries, three argument orders, in one file
assertEquals(3, result.size)                      // kotlin.test: expected first
assertThat(result).hasSize(3)                     // AssertJ: actual first
result.size shouldBe 3                            // Kotest: actual first

// good — kotlin.test throughout
import kotlin.test.assertContains
import kotlin.test.assertEquals

assertEquals(3, result.size)
assertContains(result, expectedOrder)

// good — AssertJ throughout
import org.assertj.core.api.Assertions.assertThat

assertThat(result).hasSize(3).contains(expectedOrder)
```

## 32.5 Assert on a thrown exception with `assertFailsWith`, never with `try` / `fail` / `catch`.

> Why? The hand-rolled form is four lines of boilerplate with a subtle bug
> waiting in it: forget the `fail()` and the test passes when nothing throws,
> which is the exact case it exists to catch. `assertFailsWith<T> { }` fails
> if the block does not throw, fails if it throws the wrong type, and
> **returns the exception** so you can assert on its message, cause, or
> fields — which is usually the interesting part. AssertJ's
> `assertThatThrownBy` and Kotest's `shouldThrow<T>` are equivalent.
> **Suggestion.**

```kotlin
// bad — passes silently if withdraw() stops throwing
@Test
fun `withdrawal beyond the balance is rejected`() {
    try {
        account.withdraw(Money(1_000))
    } catch (e: InsufficientFundsException) {
        // expected
    }
}

// good — and the returned exception is available for further assertions
@Test
fun `withdrawal beyond the balance is rejected`() {
    val e = assertFailsWith<InsufficientFundsException> {
        account.withdraw(Money(1_000))
    }

    assertEquals(Money(250), e.availableBalance)
}
```

## 32.6 Use `assertNotNull` and `assertIs` for their return values instead of `!!` or a cast in a test.

> Why? The `!!` ban in [Chapter 6](06-null-safety.md) applies to test code
> too, and the argument is stronger there, not weaker: a `!!` that fires
> reports `NullPointerException` with no message, so the test failure tells
> you nothing about which value was absent or what the test was checking.
> `assertNotNull(actual)` fails with a proper assertion message *and* returns
> the value as a non-null type, so it replaces the `!!` rather than merely
> preceding it. `assertIs<T>(value)` does the same for a type check and
> returns the narrowed value. **Suggestion.**

```kotlin
// bad — NullPointerException with no message; nothing says what was expected
@Test
fun `finds the order`() {
    val order = repository.findById(id)
    assertEquals(Money(25), order!!.total)
}

// bad — ClassCastException instead of an assertion failure
val failure = result as Result.Failure

// good
@Test
fun `finds the order`() {
    val order = assertNotNull(repository.findById(id), "order $id should exist")
    assertEquals(Money(25), order.total)
}

// good
val failure = assertIs<Result.Failure>(result)
assertEquals("timeout", failure.reason)
```

## 32.7 Group related tests with `@Nested`, and add `@DisplayName` only where the function name cannot carry the meaning.

> Why? A 40-test class with no structure is a wall. `@Nested` inner classes
> group by the condition under test — "when the basket is empty", "when the
> customer is a member" — so the shared arrangement lives in the group and
> the report reads as a specification. Note the Kotlin mechanics: a `@Nested`
> class must be an **inner** class, because JUnit needs an instance bound to
> the outer one, and a plain nested class fails at runtime with a message
> that does not mention `inner`. `@DisplayName` is redundant when you already
> use backticked names (§32.2) — reach for it only for characters backticks
> cannot carry. **Suggestion.**

```kotlin
// bad — a nested class without `inner`; JUnit cannot instantiate it
class BasketTest {
    @Nested
    class WhenEmpty {
        @Test fun `total is zero`() { ... }
    }
}

// good
class BasketTest {
    private val basket = Basket()

    @Nested
    inner class WhenEmpty {
        @Test
        fun `the total is zero`() {
            assertEquals(Money.ZERO, basket.total)
        }
    }

    @Nested
    inner class WhenHoldingItems {
        @BeforeEach
        fun addItems() {
            basket.add(item("A", Money(10)))
        }

        @Test
        fun `the total is the sum of the item prices`() {
            assertEquals(Money(10), basket.total)
        }
    }
}
```

## 32.8 Use `@ParameterizedTest` for the same behaviour over many inputs — and mark a `@MethodSource` factory `@JvmStatic`.

> Why? Copying a test five times to change one literal produces five names to
> maintain and five places to update. `@ValueSource` and `@CsvSource` cover
> literal inputs; `@MethodSource` covers anything richer. The Kotlin-specific
> trap is in `@MethodSource`: JUnit requires the factory method to be
> `static`, and a function in a `companion object` is **not** static on the
> JVM unless annotated `@JvmStatic` (see
> [Chapter 28, §28.9](28-java-interop.md)). Without it the test fails at
> runtime with "Could not find factory method", which reads like a typo in
> the method name. The alternative is `@TestInstance(Lifecycle.PER_CLASS)` on
> the class, which lets the factory be an ordinary member. **Suggestion.**

```kotlin
// bad — five near-identical tests
@Test fun `rejects empty`() = assertFalse(isValid(""))
@Test fun `rejects blank`() = assertFalse(isValid("   "))
@Test fun `rejects no at sign`() = assertFalse(isValid("nope"))

// bad — companion function is not static; "Could not find factory method"
class EmailTest {
    companion object {
        fun invalidAddresses() = listOf("", "   ", "nope")
    }

    @ParameterizedTest
    @MethodSource("invalidAddresses")
    fun `rejects invalid addresses`(input: String) = assertFalse(isValid(input))
}

// good — literals
@ParameterizedTest
@ValueSource(strings = ["", "   ", "nope", "a@", "@b"])
fun `rejects invalid addresses`(input: String) {
    assertFalse(isValid(input))
}

// good — richer arguments, with the @JvmStatic that makes it resolvable
class EmailTest {
    companion object {
        @JvmStatic
        fun cases(): List<Arguments> = listOf(
            Arguments.of("a@b.com", true),
            Arguments.of("nope", false),
        )
    }

    @ParameterizedTest
    @MethodSource("cases")
    fun `validates addresses`(input: String, expected: Boolean) {
        assertEquals(expected, isValid(input))
    }
}
```

## 32.9 Put no logic in a test: no `if`, no loop, no computed expected value.

> Why? A test with a branch is itself untested code, and a bug in the branch
> makes the test pass while the production code is wrong — the worst possible
> outcome, because it also removes the pressure to notice. Computing the
> expected value with the same formula the production code uses is the
> purest form of this: the test asserts that the implementation equals
> itself and will pass no matter how wrong the formula is. Write the expected
> value as a literal, and use `@ParameterizedTest` (§32.8) where you were
> reaching for a loop. **Suggestion.**

```kotlin
// bad — the expected value is computed by the logic under test, so this test
// passes even if the VAT rate is wrong
@Test
fun `applies VAT`() {
    val net = Money(100)
    assertEquals(net * (1 + VAT_RATE), invoice.gross(net))
}

// bad — a loop with a branch: the assertion may never run
@Test
fun `all active users have an email`() {
    for (user in users) {
        if (user.isActive) {
            assertNotNull(user.email)
        }
    }
}

// good — a literal the reader can check by hand
@Test
fun `applies twenty percent VAT`() {
    assertEquals(Money(120), invoice.gross(Money(100)))
}

// good — a total assertion with no branch
@Test
fun `every active user has an email`() {
    val activeWithoutEmail = users.filter { it.isActive && it.email == null }

    assertEquals(emptyList(), activeWithoutEmail)
}
```

## 32.10 Prefer a hand-written fake to a mock, and never mock a type you do not own.

> Why? A mock encodes your *assumption* about how a collaborator behaves. For
> a type you own, that assumption is checked by the type's own tests. For a
> third-party type — a JDBC `Connection`, an SDK client, an HTTP library — it
> is checked by nothing, so the test passes against a fiction and production
> fails against reality. The recurring symptom is a green suite after a
> dependency upgrade that changed the contract. A fake — a real
> implementation of your own interface, backed by a map — is usually shorter
> than the stubbing it replaces, is reusable across the whole suite, and
> cannot drift from an interface you control because it must still compile.
> **Suggestion.**

```kotlin
// bad — stubbing a third-party type; the test asserts your belief about JDBC
val connection = mockk<Connection>()
every { connection.prepareStatement(any()) } returns statement

// bad — six lines of stubbing per test for your own repository
val repo = mockk<OrderRepository>()
every { repo.findById(id) } returns order
every { repo.save(any()) } returns order

// good — a fake that any test can use, and that must keep compiling
class InMemoryOrderRepository : OrderRepository {
    private val stored = mutableMapOf<OrderId, Order>()

    override fun findById(id: OrderId): Order? = stored[id]

    override fun save(order: Order): Order = order.also { stored[it.id] = it }
}
```

## 32.11 When you do need a mock, use MockK; Kotlin's final-by-default classes are what made the alternative painful.

> Why? Kotlin classes and members are `final` unless declared `open`, and
> Mockito's classic subclass-based mock maker cannot subclass a final class —
> which historically meant either `mockito-inline` or making production types
> `open` purely for tests, a real design compromise. Mockito 5 changed the
> default mock maker to the inline one, so that particular objection is gone.
> MockK is still the better fit for Kotlin because it handles the constructs
> Mockito has no notion of: `object` declarations (`mockkObject`), top-level
> and extension functions (`mockkStatic`), and `suspend` functions natively
> (§32.12). If a codebase is already invested in Mockito, `mockito-kotlin` on
> Mockito 5 is a defensible choice; do not run both. **Suggestion.**

```kotlin
// bad — making a production class `open` so a mocking library can subclass it
open class PricingService {
    open fun quote(basket: Basket): Money = ...
}

// good — MockK mocks the final class as written
class PricingService {
    fun quote(basket: Basket): Money = ...
}

val pricing = mockk<PricingService>()
every { pricing.quote(any()) } returns Money(42)

// good — MockK also covers what Mockito has no concept of
mockkObject(FeatureFlags)
every { FeatureFlags.isEnabled("new-pricing") } returns true
```

## 32.12 Stub and verify `suspend` functions with `coEvery` and `coVerify`, never `every` and `verify`.

> Why? `every { repo.load(id) }` does not compile against a `suspend fun`
> because the block is not a suspending lambda — and when a wrapper or a
> non-suspending overload lets it compile, the stub silently never matches,
> producing a "no answer found for" failure that points at the call rather
> than at the stub. `coEvery` and `coVerify` take suspending blocks and are
> the only correct form. This is mechanics only; the surrounding discipline
> — `runTest`, `TestDispatcher`, virtual time — is
> [Chapter 39](39-coroutine-testing.md). **Suggestion** — the adjacent
> `detekt/CoroutineLaunchedInTestWithoutRunTest` catches a related failure.

```kotlin
// bad — does not compile for a suspend fun, and its non-suspending sibling
// silently fails to match
every { repository.load(id) } returns order
verify { repository.save(order) }

// good
coEvery { repository.load(id) } returns order
coVerify { repository.save(order) }
```

## 32.13 Do not reach for `relaxed = true` by default.

> Why? A relaxed mock answers every unstubbed call with a default — `null`,
> `0`, an empty collection, a nested relaxed mock — which means a call your
> code makes by mistake returns something plausible instead of failing. That
> is precisely the feedback a mock exists to give. Relaxed mocks are
> defensible for a wide interface where the test genuinely cares about one
> method (a metrics recorder, a notifier), and `relaxUnitFun = true` is a
> narrower, safer version for interfaces that mostly return `Unit`. Reaching
> for `relaxed = true` to make a `NoAnswerFoundException` go away is
> suppressing a real signal. **Suggestion.**

```kotlin
// bad — a typo'd or unexpected call now returns a plausible empty result and
// the test still passes
val repository = mockk<OrderRepository>(relaxed = true)

// good — strict by default; every expectation is explicit
val repository = mockk<OrderRepository>()
coEvery { repository.findById(id) } returns order

// good — narrow relaxation for a Unit-returning collaborator
val metrics = mockk<MetricsRecorder>(relaxUnitFun = true)
```

## 32.14 Verify the interactions that are the point of the test; do not verify everything.

> Why? Every `verify` is an assertion about *how* the code works, not *what*
> it produces, and each one welds the test to the current implementation.
> Verify a call when the call is the observable outcome — an email was sent,
> a row was written, a payment was captured. Do not verify reads, do not
> assert call counts you do not care about, and use `confirmVerified` only in
> tests whose subject really is "nothing else happened". Reset state between
> tests, or MockK's recorded calls leak across them: `clearAllMocks()` (or
> `unmockkAll()` if you used `mockkObject`/`mockkStatic`) in an `@AfterEach`.
> **Suggestion.**

```kotlin
// bad — asserting the shape of the implementation; any refactor breaks it
verify(exactly = 1) { repository.findById(id) }
verify(exactly = 1) { pricing.quote(basket) }
verify(exactly = 1) { auditLog.debug(any()) }
confirmVerified(repository, pricing, auditLog)

// good — the side effect is the behaviour; the reads are not
@Test
fun `capturing a payment notifies the customer`() {
    service.capture(paymentId)

    coVerify { notifier.paymentCaptured(paymentId) }
}

@AfterEach
fun tearDown() {
    clearAllMocks()
}
```

## 32.15 Make every test deterministic: inject the `Clock`, seed the randomness, never `Thread.sleep`.

> Why? A flaky test is worse than no test, because a suite that fails once a
> week trains everyone to re-run it, and then a real regression gets re-run
> too. The three usual sources are all avoidable. Time: inject a `Clock` and
> use `Clock.fixed` — see [Chapter 30, §30.7](30-dates-and-times.md).
> Randomness: inject `Random(seed)` rather than the global `Random`.
> Waiting: `Thread.sleep` is either too short (flaky) or too long (slow), and
> in coroutine code it blocks the very thread the test needs — use awaitility,
> a latch, or the virtual time of [Chapter 39](39-coroutine-testing.md).
> **Suggestion** — the adjacent `detekt/SleepInsteadOfDelay` fires on
> `Thread.sleep` inside a suspending function.

```kotlin
// bad — fails at midnight, produces different data each run, and takes 2s
@Test
fun `expires yesterday's sessions`() {
    val service = SessionService(repo)
    val id = UUID.randomUUID()
    service.expireStale()
    Thread.sleep(2_000)
    assertTrue(repo.findById(id)!!.expired)
}

// good — the clock, the ids, and the completion are all controlled
@Test
fun `expires sessions older than the retention window`() {
    val clock = Clock.fixed(Instant.parse("2026-03-01T00:00:00Z"), ZoneOffset.UTC)
    val service = SessionService(repo, clock)
    val session = repo.save(session(id = SessionId("s-1"), lastSeen = clock.instant()))

    service.expireStale(olderThan = 7.days)

    assertTrue(assertNotNull(repo.findById(session.id)).expired)
}
```

## 32.16 Build test data with a factory function that has a default for every parameter.

> Why? Constructing a ten-field domain object inline in forty tests means
> forty places to edit when an eleventh field appears, and it buries the one
> value the test actually cares about in nine irrelevant ones. Kotlin's
> default arguments and named arguments make the Java builder pattern
> unnecessary: a single top-level function with a default per parameter lets
> each test name only what matters, and adding a field touches one line.
> Keep these in the test source set, not in production code. **Suggestion.**

```kotlin
// bad — the reader cannot tell which of these nine values the test is about
val order = Order(
    id = OrderId("o-1"),
    customerId = CustomerId("c-1"),
    status = OrderStatus.PLACED,
    total = Money(100),
    currency = Currency.GBP,
    placedAt = Instant.EPOCH,
    channel = Channel.WEB,
    notes = null,
    lines = emptyList(),
)

// good — one factory, and every test states only what it cares about
fun order(
    id: OrderId = OrderId("o-1"),
    customerId: CustomerId = CustomerId("c-1"),
    status: OrderStatus = OrderStatus.PLACED,
    total: Money = Money(100),
    currency: Currency = Currency.GBP,
    placedAt: Instant = Instant.EPOCH,
    channel: Channel = Channel.WEB,
    notes: String? = null,
    lines: List<OrderLine> = emptyList(),
) = Order(id, customerId, status, total, currency, placedAt, channel, notes, lines)

val cancelled = order(status = OrderStatus.CANCELLED)
```

## 32.17 If you choose Kotest instead of JUnit Jupiter, choose exactly one spec style and use it everywhere.

> Why? Kotest is a genuine alternative — it brings property-based testing,
> data-driven tests, and a matcher library that reads better than any
> assertion API here — and it runs on the JUnit Platform, so it coexists with
> Jupiter in the same build. Its cost is choice: its testing-styles page
> documents nine interchangeable spec styles (`BehaviorSpec`, `DescribeSpec`,
> `ExpectSpec`, `FeatureSpec`, `FunSpec`, `FreeSpec`, `ShouldSpec`,
> `StringSpec`, `WordSpec`), plus `AnnotationSpec` for JUnit-style migration,
> and a codebase using four of them has four
> layouts for the same idea with nothing gained. Pick one — `FunSpec` and
> `DescribeSpec` are the common defaults — and put the choice in the
> project's conventions alongside §32.2 and §32.4. **Suggestion.**

```kotlin
// bad — three spec styles across three files in the same module
class BasketTest : StringSpec({ ... })
class OrderTest : BehaviorSpec({ ... })
class PricingTest : WordSpec({ ... })

// good — one style throughout
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.shouldBe

class BasketTest : FunSpec({
    test("an empty basket has a zero total") {
        Basket().total shouldBe Money.ZERO
    }

    test("adding an item increases the size") {
        val basket = Basket()

        basket.add(item("A"))

        basket.size shouldBe 1
    }
})
```

## 32.18 Test through the public API; do not widen visibility so a test can reach inside.

> Why? Changing `private` to `internal` — or worse, to `public` — so a test
> can call a helper turns an implementation detail into a contract, and the
> next refactor breaks a test that was never about behaviour anyone cares
> about. A private function that is hard to reach through the public API is
> usually telling you it wants to be its own type with its own public
> surface. Two Kotlin specifics make this easier to get wrong here than in
> Java. First, the Gradle Kotlin plugin associates the `test` compilation
> with `main`, so `internal` *is* visible from tests — nothing stops the
> widening, which is exactly why it needs a rule. Second, `internal` is not
> an encapsulation guarantee on the JVM at all (see
> [Chapter 28, §28.16](28-java-interop.md)), and `@VisibleForTesting`
> documents intent without enforcing anything outside Android Lint.
> **Suggestion.**

```kotlin
// bad — visibility widened for a test, freezing a helper into the contract
class PriceCalculator {
    fun total(basket: Basket): Money = applyDiscounts(basket.subtotal())

    internal fun applyDiscounts(subtotal: Money): Money = ...  // was private
}

// good — the helper stays private and is exercised through the public entry
class PriceCalculator {
    fun total(basket: Basket): Money = applyDiscounts(basket.subtotal())

    private fun applyDiscounts(subtotal: Money): Money = ...
}

@Test
fun `applies the bulk discount above the threshold`() {
    assertEquals(Money(90), PriceCalculator().total(basketWorth(Money(100))))
}

// good — when the logic deserves its own tests, give it its own type
class DiscountPolicy {
    fun apply(subtotal: Money): Money = ...
}
```

## 32.19 For anything `suspend` or `Flow`, stop here and use Chapter 39.

> Why? Coroutine tests have their own failure modes that none of the rules
> above address: `runBlocking` in a test makes real time pass, so a test with
> a `delay(30.seconds)` takes thirty seconds; `Dispatchers.Main` is not
> installed outside Android; a `launch` inside a `@Test` body escapes the
> test's lifetime and its failure is reported against a later test or not at
> all. `runTest` and the `kotlinx-coroutines-test` dispatchers exist to
> solve all three, and they are covered in full in
> [Chapter 39, Coroutine Testing](39-coroutine-testing.md). **Suggestion** —
> the adjacent `detekt/CoroutineLaunchedInTestWithoutRunTest` catches the
> escaping-`launch` case.

```kotlin
// bad — real time passes, and the launched coroutine outlives the test
@Test
fun `retries after a backoff`() = runBlocking {
    launch { service.retryWithBackoff() }   // failures here may never surface
    delay(30_000)                            // the test genuinely takes 30s
    assertEquals(3, service.attempts)
}

// good — virtual time and a scope tied to the test; see Chapter 39
@Test
fun `retries after a backoff`() = runTest {
    service.retryWithBackoff()   // delays inside are skipped by virtual time

    assertEquals(3, service.attempts)
}
```
