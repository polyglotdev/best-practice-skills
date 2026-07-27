<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 31. Testing

A test suite has two jobs and they pull in opposite directions. It has to
catch regressions, which argues for testing everything; and it has to stay
cheap to change, which argues for testing as little as possible. The way
out is to test *behaviour* — the promises the type makes to its callers —
and to leave the implementation free to move underneath. A suite that
breaks on every refactor is not protecting the code, it is duplicating it.

The second thing a test does, and the thing most suites do badly, is
explain the failure. A test that fails with `expected: <true> but was:
<false>` has told you nothing; you now have to reproduce it locally to find
out what happened. Most of the AssertJ and JUnit rules below exist because
the alternative produces a diagnostic nobody can act on from a CI log.

This chapter covers naming, structure, assertion style, parameterization,
lifecycle, test doubles, and determinism. It draws on
[JUnit 5](https://docs.junit.org/current/user-guide/), the
[AssertJ documentation](https://assertj.github.io/doc/), the
[Mockito reference](https://javadoc.io/doc/org.mockito/mockito-core/latest/org.mockito/org/mockito/Mockito.html),
and Google Java Style
[§5.2.3 Method names](https://google.github.io/styleguide/javaguide.html#s5.2.3-method-names),
which carves out the one place underscores are permitted in a Java method
name. Determinism around time picks up the `Clock` injection rule from
[Chapter 28, §28.8](28-dates-and-times.md). Everything Spring-specific —
`@SpringBootTest`, the test slices, `@MockBean`, Testcontainers wiring — is
[Chapter 36](36-spring-testing.md) and is deliberately not repeated here.

**Tool alignment:** Error Prone's `MissingFail`, `TryFailThrowable`,
`AssertionFailureIgnored`, `JUnit4TestNotRun`, `JUnitIncompatibleType`, and
`ReturnValueIgnored` catch the structural mistakes; Checkstyle's
`MethodName` needs a test-aware pattern so that §31.1 does not fight it.
Design rules — which double to use, what to assert — are **Suggestions**.

## 31.1 Name a test for the behaviour it pins, using the JUnit underscore form.

> Why?
> [Google Java Style §5.2.3](https://google.github.io/styleguide/javaguide.html#s5.2.3-method-names)
> makes exactly one exception to lowerCamelCase: "Underscores may appear in
> JUnit test method names to separate logical components of the name, with
> each component written in lowerCamelCase, for example
> `transferMoney_deductsFromSource`." Use it, because a name of the shape
> `unitUnderTest_condition_expectedOutcome` turns the CI failure list into a
> readable specification — you learn what broke without opening the file. A
> name like `testTransfer2` tells the reader nothing and, worse, tells the
> *author* nothing about whether the case is already covered.
> **Suggestion** — but note the default Checkstyle `MethodName` pattern
> rejects underscores, so test sources need a pattern such as
> `^[a-z][a-zA-Z0-9]*(_[a-z][a-zA-Z0-9]*)*$`.

```java
// bad — numbered, unsearchable, and silent about the behaviour
@Test
void testTransfer2() {}

@Test
void shouldWork() {}

// good
@Test
void transferMoney_deductsFromSource() {}

@Test
void transferMoney_insufficientFunds_leavesBothBalancesUnchanged() {}
```

## 31.2 Add `@DisplayName` when the report needs a sentence the method name cannot carry.

> Why? The method name is constrained by §31.1 and by the identifier
> grammar; `@DisplayName` is free text, so it can carry punctuation, a
> currency symbol, or the exact wording of the requirement being pinned.
> That matters when the audience for the report includes someone who does
> not read Java. Do not use it to restate the method name — a
> `@DisplayName` that is the method name with spaces is pure duplication
> that will drift out of sync on the next rename. **Suggestion.**

```java
// bad — duplicates the method name and will drift
@Test
@DisplayName("transfer money deducts from source")
void transferMoney_deductsFromSource() {}

// good — carries what the identifier grammar cannot
@Test
@DisplayName("A £0.00 transfer is rejected before any balance is read")
void transfer_zeroAmount_isRejectedWithoutReadingBalances() {}
```

## 31.3 Structure every test as Arrange, Act, Assert — with the act as a single statement.

> Why? The three phases answer the three questions a reader has: what state
> was this in, what did we do, what should be true now. Interleaving them
> forces the reader to reconstruct the sequence, and it hides the most
> important defect a test can have — more than one action, so a failure
> does not identify which one broke. Keeping the act to a single statement
> also makes §31.4 self-enforcing: if you cannot express the action in one
> call, the test is covering more than one behaviour. A blank line between
> phases is enough; comment labels are usually noise. **Suggestion.**

```java
// bad — three actions interleaved with assertions; a failure identifies nothing
@Test
void accountFlow() {
  Account account = new Account();
  account.deposit(Money.of(100));
  assertThat(account.balance()).isEqualTo(Money.of(100));
  account.withdraw(Money.of(30));
  assertThat(account.balance()).isEqualTo(Money.of(70));
  account.close();
  assertThat(account.isClosed()).isTrue();
}

// good
@Test
void withdraw_reducesBalanceByTheRequestedAmount() {
  Account account = accountWithBalance(Money.of(100));

  account.withdraw(Money.of(30));

  assertThat(account.balance()).isEqualTo(Money.of(70));
}
```

## 31.4 Assert one logical behaviour per test, and use `assertAll` when several assertions describe one outcome.

> Why? JUnit stops at the first failed assertion, so a test with five
> unrelated assertions reports one failure and hides the other four — you
> fix, rerun, and discover the next one, which is the slowest possible
> feedback loop. Splitting by behaviour fixes that. Where several
> assertions genuinely describe *one* outcome (every field of a returned
> record, say), `assertAll` evaluates all of them and reports every failure
> together, which is exactly the diagnostic you want. AssertJ's
> `SoftAssertions.assertSoftly` does the same with the fluent API.
> **Suggestion.**

```java
// bad — one failure masks the rest; you learn about them one rerun at a time
@Test
void parse_returnsAllFields() {
  Config config = Config.parse(RAW);
  assertThat(config.host()).isEqualTo("db.internal");
  assertThat(config.port()).isEqualTo(5432);
  assertThat(config.timeout()).isEqualTo(Duration.ofSeconds(30));
}

// good — all failures reported in one run
@Test
void parse_returnsAllFields() {
  Config config = Config.parse(RAW);

  assertAll(
      () -> assertThat(config.host()).isEqualTo("db.internal"),
      () -> assertThat(config.port()).isEqualTo(5432),
      () -> assertThat(config.timeout()).isEqualTo(Duration.ofSeconds(30)));
}
```

## 31.5 Use AssertJ's `assertThat` rather than JUnit's `assertEquals`.

> Why? Two reasons, and the second is the important one. First, argument
> order: `assertEquals(expected, actual)` is silently reversible, so a
> transposed call reports the failure backwards and sends the reader
> looking at the wrong side. AssertJ's `assertThat(actual).isEqualTo(expected)`
> cannot be transposed. Second, diagnostics: AssertJ produces a structural
> diff for collections and objects — which element differs, which field —
> where `assertEquals` on a list prints both lists whole and leaves you to
> find the difference by eye. Add `as(...)` when the assertion needs a name.
> **Suggestion.**

```java
// bad — reversible, and the failure prints both lists in full
assertEquals(expectedOrders, service.findAll());
assertTrue(order.total().compareTo(BigDecimal.ZERO) > 0);

// good — unambiguous, and the diff names the offending element
assertThat(service.findAll()).isEqualTo(expectedOrders);
assertThat(order.total()).as("order total").isGreaterThan(BigDecimal.ZERO);
```

## 31.6 Assert against the collection as a whole, not size-then-index.

> Why? `assertThat(result).hasSize(2)` followed by `result.get(0)` gives a
> failure message about a size when the real defect is ordering or content,
> and it throws `IndexOutOfBoundsException` rather than an assertion
> failure when the list is short — an error, not a diagnosis. The
> collection assertions state the intent directly and print the actual
> contents on failure. `extracting` narrows to the fields under test so the
> assertion does not depend on unrelated ones.
> **Suggestion.**

```java
// bad — the message talks about size, and a short list throws IOOBE
List<Order> result = service.findAll();
assertThat(result).hasSize(2);
assertThat(result.get(0).id()).isEqualTo(FIRST_ID);
assertThat(result.get(1).id()).isEqualTo(SECOND_ID);

// good — one assertion, ordering included, contents printed on failure
assertThat(service.findAll())
    .extracting(Order::id)
    .containsExactly(FIRST_ID, SECOND_ID);
```

## 31.7 Assert on exceptions with `assertThatThrownBy` or `assertThatExceptionOfType` — never try/fail/catch.

> Why? The hand-written form has a failure mode that is invisible on
> inspection: if the `fail()` call is missing, or is placed where the
> exception path skips it, the test passes when nothing is thrown at all —
> a test that can never fail. Worse, catching `Throwable` around a `fail()`
> swallows the very `AssertionError` that `fail()` raised. The AssertJ
> forms cannot be written wrong, and they chain into assertions on the
> message, the cause, and the type. Always assert the *type* and something
> about the message; `assertThatThrownBy(...)` with no chained assertion
> only proves that something, somewhere, threw.
> **Violation — enforced by Error Prone `MissingFail` and
> `TryFailThrowable`.**

```java
// bad — passes even when nothing throws, because fail() was forgotten
@Test
void withdraw_overdraft_throws() {
  try {
    account.withdraw(Money.of(1_000));
  } catch (InsufficientFundsException e) {
    // expected
  }
}

// good
@Test
void withdraw_overdraft_throwsWithTheShortfall() {
  assertThatThrownBy(() -> account.withdraw(Money.of(1_000)))
      .isInstanceOf(InsufficientFundsException.class)
      .hasMessageContaining("shortfall=900");
}

// also good — when the exception type leads the sentence
assertThatExceptionOfType(InsufficientFundsException.class)
    .isThrownBy(() -> account.withdraw(Money.of(1_000)))
    .withMessageContaining("shortfall=900");
```

## 31.8 Never catch an exception around an assertion.

> Why? An assertion failure is an `AssertionError`, and a `catch (Throwable)`
> or `catch (Error)` around it swallows the failure and turns a red test
> green. Even `catch (Exception)` is wrong here: it converts an unexpected
> failure in the code under test into a passing run, which is the single
> most dangerous defect a suite can contain because it removes coverage
> silently. If a checked exception forces your hand, let the test method
> declare `throws` — JUnit 5 permits it and reports the exception as a
> failure. **Violation — enforced by Error Prone
> `AssertionFailureIgnored`.**

```java
// bad — swallows the AssertionError; this test can never fail
@Test
void loadsConfig() {
  try {
    assertThat(loader.load(path)).isNotNull();
  } catch (Exception e) {
    // ignore
  }
}

// good — declare the checked exception and let JUnit report it
@Test
void load_validFile_returnsConfig() throws IOException {
  assertThat(loader.load(path)).isNotNull();
}
```

## 31.9 Use `@ParameterizedTest` instead of looping over cases inside a test.

> Why? A loop reports one result for N cases, so the first failure hides
> the rest and the report cannot tell you *which* input broke.
> `@ParameterizedTest` runs each case as a separate test with the arguments
> in the display name, so a CI failure names the offending input directly.
> It also stops the loop body from accumulating state between iterations,
> which is a real source of order-dependent flakes. Set `name` so the
> report is readable. **Suggestion.**

```java
// bad — one test, N cases, and the report names none of them
@Test
void isValid_rejectsMalformedEmails() {
  for (String candidate : List.of("", "a@", "@b", "a b@c.com")) {
    assertThat(Email.isValid(candidate)).isFalse();
  }
}

// good — one test per case, and the failing input is in the report
@ParameterizedTest(name = "[{index}] rejects \"{0}\"")
@ValueSource(strings = {"", "a@", "@b", "a b@c.com"})
void isValid_malformedInput_returnsFalse(String candidate) {
  assertThat(Email.isValid(candidate)).isFalse();
}
```

## 31.10 Choose the argument source that matches the shape of the data.

> Why? Each source exists for a different shape and using the wrong one
> costs readability. `@ValueSource` is for a single parameter of a literal
> type. `@CsvSource` is for a small fixed table of two or more columns, and
> its `textBlock` form keeps the table aligned and readable in source.
> `@EnumSource` covers a whole enum and — this is the valuable part —
> automatically covers any constant added later, so a new enum value cannot
> slip through untested. `@MethodSource` is for anything that needs real
> objects or computation; its factory must be `static` unless the class is
> annotated `@TestInstance(Lifecycle.PER_CLASS)`. **Suggestion.**

```java
// bad — a multi-column table crammed into one delimiter-joined string
@ParameterizedTest
@ValueSource(strings = {"1|USD|1.00", "2|EUR|0.92"})
void converts(String packed) {
  String[] parts = packed.split("\\|");
}

// good — the table is a table
@ParameterizedTest
@CsvSource(
    textBlock =
        """
        1, USD, 1.00
        2, EUR, 0.92
        """)
void convert_knownCurrency_returnsRate(int id, Currency currency, BigDecimal rate) {}

// good — every enum constant, including ones added tomorrow
@ParameterizedTest
@EnumSource(OrderStatus.class)
void render_everyStatus_producesALabel(OrderStatus status) {
  assertThat(renderer.label(status)).isNotBlank();
}

// good — real objects need a factory
@ParameterizedTest
@MethodSource("overlappingRanges")
void overlaps_returnsTrue(DateRange left, DateRange right) {
  assertThat(left.overlaps(right)).isTrue();
}

static Stream<Arguments> overlappingRanges() {
  return Stream.of(
      Arguments.of(range("2024-01-01", "2024-01-31"), range("2024-01-15", "2024-02-15")),
      Arguments.of(range("2024-01-01", "2024-01-31"), range("2024-01-31", "2024-02-01")));
}
```

## 31.11 Group cases that share a precondition with `@Nested`.

> Why? Without nesting, a shared precondition is either repeated in every
> test or hoisted into a `@BeforeEach` that also runs for the tests that do
> not want it — the second is how a "given an empty account" setup ends up
> silently applying to the "given a closed account" cases. `@Nested` scopes
> the `@BeforeEach` to the group that needs it and produces a hierarchical
> report that reads as a specification. Name the inner class for the
> precondition, not for the method under test. **Suggestion.**

```java
// bad — one setup that half the tests have to undo
class AccountTest {
  private Account account;

  @BeforeEach
  void setUp() {
    account = new Account();
    account.close();
  }

  @Test
  void deposit_onOpenAccount_succeeds() {
    account = new Account(); // undoing the shared setup
  }
}

// good
class AccountTest {

  @Nested
  class WhenClosed {
    private final Account account = closedAccount();

    @Test
    void deposit_isRejected() {
      assertThatThrownBy(() -> account.deposit(Money.of(1)))
          .isInstanceOf(AccountClosedException.class);
    }
  }

  @Nested
  class WhenOpen {
    private final Account account = new Account();

    @Test
    void deposit_increasesBalance() {
      account.deposit(Money.of(1));
      assertThat(account.balance()).isEqualTo(Money.of(1));
    }
  }
}
```

## 31.12 Build fixtures in `@BeforeEach`; reserve `@BeforeAll` for genuinely immutable or genuinely expensive shared state.

> Why? `@BeforeEach` gives each test a fresh fixture, which is what makes
> tests independent and order-insensitive. `@BeforeAll` runs once for the
> class, so any object it creates is shared, and any test that mutates that
> object changes the input to every test that runs after it — producing a
> suite that passes in the IDE and fails in CI because the execution order
> differs. Use `@BeforeAll` for things that are read-only (a parsed
> schema, a loaded fixture file) or too expensive to repeat (a container, a
> shared connection pool), and make what it produces immutable.
> **Suggestion.**

```java
// bad — every test mutates the shared list, so results depend on order
class BasketTest {
  private static List<Item> items;

  @BeforeAll
  static void setUp() {
    items = new ArrayList<>(List.of(item("a"), item("b")));
  }

  @Test
  void add_appends() {
    items.add(item("c")); // leaks into the next test
  }
}

// good — fresh per test; the expensive, read-only thing stays in @BeforeAll
class BasketTest {
  private static Catalogue catalogue; // immutable, loaded once

  @BeforeAll
  static void loadCatalogue() {
    catalogue = Catalogue.load(CATALOGUE_PATH);
  }

  private Basket basket;

  @BeforeEach
  void setUp() {
    basket = new Basket(catalogue);
  }
}
```

## 31.13 Never let one test depend on another having run.

> Why? JUnit 5 gives no ordering guarantee by default, and it is free to
> run methods in a different order on a different JVM. A test that depends
> on a predecessor therefore passes locally and fails in CI, or fails only
> when the suite is filtered to a single method — the worst debugging
> experience the suite can offer. `@TestMethodOrder` exists but does not
> fix the coupling; it hides it, and the tests still cannot be run
> individually. If two tests share expensive setup, share the *setup*, not
> the *result*. **Suggestion.**

```java
// bad — the second test only passes if the first ran, in this order, and
// neither can be run on its own
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class UserServiceTest {
  private static String createdId;

  @Test
  @Order(1)
  void createsUser() {
    createdId = service.create(request).id();
  }

  @Test
  @Order(2)
  void findsUser() {
    assertThat(service.find(createdId)).isPresent();
  }
}

// good — each test establishes what it needs
@Test
void find_existingUser_returnsIt() {
  String id = service.create(request).id();

  assertThat(service.find(id)).isPresent();
}
```

## 31.14 No logic in a test — no conditionals, no loops, no arithmetic in the assertion.

> Why? A test is a specification and specifications do not branch. Once
> there is an `if` in a test, some path is not being exercised and nothing
> tells you which; once there is a loop, a failure does not identify the
> iteration. And a test containing logic is itself untested code, so a bug
> in the test produces a false pass that nobody will find. If you need a
> branch, you need two tests (§31.9 gives you the parameterized form for
> the common case). **Suggestion.**

```java
// bad — the else branch may never run, and nobody would know
@Test
void discount_isApplied() {
  Order order = orderFor(customer);
  if (customer.isPremium()) {
    assertThat(order.discount()).isEqualTo(Percent.of(10));
  } else {
    assertThat(order.discount()).isEqualTo(Percent.ZERO);
  }
}

// good — two named cases, both guaranteed to run
@Test
void discount_premiumCustomer_isTenPercent() {
  assertThat(orderFor(premiumCustomer()).discount()).isEqualTo(Percent.of(10));
}

@Test
void discount_standardCustomer_isZero() {
  assertThat(orderFor(standardCustomer()).discount()).isEqualTo(Percent.ZERO);
}
```

## 31.15 Never recompute the expected value with the production algorithm.

> Why? An assertion that calls the same formula the code under test uses is
> a tautology: it passes for any implementation, including a wrong one,
> because both sides are wrong in the same way. It also survives the exact
> refactor it was supposed to catch. Write the expected value as a literal
> you worked out by hand, or from the specification. If the literal is hard
> to derive, that difficulty is information about the design — it usually
> means the method is doing too much. **Suggestion.**

```java
// bad — asserts the code equals itself
@Test
void totalIncludesTax() {
  BigDecimal expected = order.subtotal().multiply(TAX_RATE).add(order.subtotal());

  assertThat(calculator.total(order)).isEqualByComparingTo(expected);
}

// good — a literal derived from the specification
@Test
void total_includesTaxAtTwentyPercent() {
  Order order = orderWithSubtotal(new BigDecimal("100.00"));

  assertThat(calculator.total(order)).isEqualByComparingTo(new BigDecimal("120.00"));
}
```

## 31.16 Prefer the real collaborator, then a fake, then a stub — and reach for a mock last.

> Why? A test double is a claim about how the collaborator behaves, and
> every claim can be wrong. The real object cannot be wrong about itself,
> so use it whenever it is fast, deterministic, and side-effect free — a
> value object, a pure function, an in-memory collection. A *fake* (a
> working in-memory implementation of the interface) is next best because
> it enforces the interface's contract for every test that uses it. A stub
> that returns canned values is fine for a narrow case. A mock that records
> and verifies interactions couples the test to the call sequence, which is
> implementation, and is the double that breaks most often under refactor.
> **Suggestion.**

```java
// bad — mocking a pure value object; the test now asserts on stubbing
Money total = mock(Money.class);
when(total.isPositive()).thenReturn(true);

// good — the real value object
Money total = Money.of(100);

// good — a fake for the repository, reusable across the whole suite
final class InMemoryOrderRepository implements OrderRepository {
  private final Map<OrderId, Order> byId = new LinkedHashMap<>();

  @Override
  public void save(Order order) {
    byId.put(order.id(), order);
  }

  @Override
  public Optional<Order> find(OrderId id) {
    return Optional.ofNullable(byId.get(id));
  }
}
```

## 31.17 Never mock a type you do not own.

> Why? A mock of a third-party type encodes your *belief* about that
> library's behaviour, and the test then verifies that belief rather than
> reality — it keeps passing after an upgrade changes the behaviour you
> mocked, which is precisely when you needed a warning. Third-party APIs
> are also wide, so the mock covers one method out of forty and the other
> thirty-nine return `null`. Wrap the dependency behind an interface you do
> own, mock or fake that, and cover the real library with a small
> integration test. **Suggestion.**

```java
// bad — asserts your assumptions about a library you do not control
HttpClient client = mock(HttpClient.class);
when(client.send(any(), any())).thenReturn(cannedResponse);

// good — an interface you own, faked freely; the adapter gets one real test
interface PaymentGateway {
  PaymentResult charge(PaymentRequest request);
}

final class StubPaymentGateway implements PaymentGateway {
  @Override
  public PaymentResult charge(PaymentRequest request) {
    return PaymentResult.approved(request.amount());
  }
}
```

## 31.18 Keep Mockito strict — never blanket-`lenient()` to silence unnecessary stubbing.

> Why? `MockitoExtension` defaults to `STRICT_STUBS`, which fails a test
> whose stubbing is never used. That failure is a genuine signal: the stub
> is either dead (the code path changed and nobody noticed) or wrong (it
> does not match the arguments the code actually passes). Switching the
> class to `Strictness.LENIENT` to make the message go away removes the
> signal from every test in the file, and leaves behind stubs that document
> behaviour the code no longer has. Fix the stub, or move it into the one
> test that needs it. **Suggestion.**

```java
// bad — silences the signal for the whole class
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class OrderServiceTest {
  @Mock private OrderRepository repository;

  @BeforeEach
  void setUp() {
    when(repository.find(any())).thenReturn(Optional.of(ORDER)); // unused by most tests
  }
}

// good — stub in the test that needs it, and keep strict stubs on
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
  @Mock private OrderRepository repository;

  @Test
  void cancel_existingOrder_marksItCancelled() {
    when(repository.find(ORDER_ID)).thenReturn(Optional.of(ORDER));

    service.cancel(ORDER_ID);

    assertThat(ORDER.status()).isEqualTo(OrderStatus.CANCELLED);
  }
}
```

## 31.19 Verify the observable outcome, not the interaction, whenever the outcome is observable.

> Why? `verify(repository).save(order)` asserts that a particular method
> was called on a particular collaborator — which is implementation. Rename
> the method, batch two saves into one, or move persistence behind a unit
> of work, and the test fails despite the behaviour being unchanged.
> Asserting the *result* (the fake repository now contains the order)
> survives all three. Reserve `verify` for outcomes that genuinely have no
> observable state: a message published to a broker, an audit event, a
> retry that must not happen. **Suggestion.**

```java
// bad — pinned to the call, so any refactor of persistence breaks it
service.place(order);
verify(repository).save(order);
verify(repository, times(1)).flush();

// good — pinned to the outcome
service.place(order);
assertThat(repository.find(order.id())).contains(order);

// good use of verify — a side effect with no queryable state
service.place(order);
verify(auditLog).record(AuditEvent.orderPlaced(order.id()));
```

## 31.20 Inject a `Clock` — never assert against `Instant.now()`.

> Why? A test that computes its expectation from the current time is racing
> the code under test: the two `now()` calls differ by microseconds, so
> `isEqualTo` fails intermittently and the usual "fix" is a tolerance that
> hides real drift. Worse, a test that asserts "expires tomorrow" fails
> when CI runs across midnight or in a different zone. Injecting a `Clock`
> ([§28.8](28-dates-and-times.md)) makes now a constant you chose, so the
> assertion is exact and the DST and midnight cases become testable rather
> than avoided. **Suggestion.**

```java
// bad — races the implementation and fails across midnight
@Test
void issue_setsExpiry() {
  Token token = issuer.issue();

  assertThat(token.expiresAt()).isCloseTo(Instant.now().plus(Duration.ofDays(1)), within(1, SECONDS));
}

// good
@Test
void issue_setsExpiryOneDayAfterIssue() {
  Instant now = Instant.parse("2024-03-31T00:30:00Z");
  TokenIssuer issuer = new TokenIssuer(Clock.fixed(now, ZoneOffset.UTC));

  Token token = issuer.issue();

  assertThat(token.expiresAt()).isEqualTo(Instant.parse("2024-04-01T00:30:00Z"));
}
```

## 31.21 Seed randomness, or inject the generator.

> Why? An unseeded generator makes the test a different test on every run:
> it passes a hundred times and fails once in CI with an input nobody can
> reproduce. Seeding makes the case deterministic *and* reproducible from
> the source. Injecting a `RandomGenerator`
> ([§29.22](29-numeric-types-and-literals.md)) goes further and lets a test
> pin the exact sequence. If you deliberately want randomised inputs, use a
> property-based framework that reports the failing seed, not an ad-hoc
> `Random` that reports nothing. **Suggestion.**

```java
// bad — a different test on every run, unreproducible when it fails
@Test
void shuffle_preservesAllElements() {
  List<Card> shuffled = deck.shuffle(new Random());

  assertThat(shuffled).containsExactlyInAnyOrderElementsOf(deck.cards());
}

// good — deterministic, and the seed is in the source
@Test
void shuffle_preservesAllElements() {
  List<Card> shuffled = deck.shuffle(new Random(20240331L));

  assertThat(shuffled).containsExactlyInAnyOrderElementsOf(deck.cards());
}
```

## 31.22 Never `Thread.sleep` in a test — await a condition.

> Why? A sleep encodes a guess about someone else's timing. Too short and
> the test is flaky on a loaded CI agent; too long and it is a permanent
> tax on every run, multiplied by every test that copied the pattern.
> Neither value is ever right, because the correct wait is "until the thing
> happened", which is a condition, not a duration. Await the condition with
> a bounded timeout so a genuine hang still fails, and fails fast when the
> condition is met. **Suggestion.**

```java
// bad — flaky under load, and slow when it is not
@Test
void publish_deliversToSubscriber() throws InterruptedException {
  publisher.publish(event);
  Thread.sleep(2_000);

  assertThat(subscriber.received()).containsExactly(event);
}

// good — returns as soon as the condition holds, fails if it never does
@Test
void publish_deliversToSubscriber() {
  publisher.publish(event);

  await()
      .atMost(Duration.ofSeconds(5))
      .untilAsserted(() -> assertThat(subscriber.received()).containsExactly(event));
}
```

## 31.23 Test the published contract, not the private internals.

> Why? A test that reaches into private state through reflection, or that
> widens a method's visibility "so it can be tested", pins a decision the
> class is entitled to change. Every subsequent refactor then costs a test
> rewrite, which is how a suite stops being an asset. If a private method
> is complex enough to want direct tests, that is evidence it wants to be
> its own type with its own public contract — extract it and test the
> extraction. Coverage of a private method comes for free through the
> public API that calls it. **Suggestion.**

```java
// bad — visibility widened for the test, and the assertion pins an internal
class PricingEngine {
  @VisibleForTesting
  BigDecimal applyTierDiscount(BigDecimal subtotal, Tier tier) {}
}

@Test
void applyTierDiscount_gold_takesTwentyPercent() {
  assertThat(engine.applyTierDiscount(new BigDecimal("100.00"), Tier.GOLD))
      .isEqualByComparingTo(new BigDecimal("80.00"));
}

// good — the rule is a type with its own contract, tested through it
public record TierDiscount(Tier tier) {
  public BigDecimal applyTo(BigDecimal subtotal) {}
}

@Test
void applyTo_goldTier_takesTwentyPercent() {
  assertThat(new TierDiscount(Tier.GOLD).applyTo(new BigDecimal("100.00")))
      .isEqualByComparingTo(new BigDecimal("80.00"));
}
```
