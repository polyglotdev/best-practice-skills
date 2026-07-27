<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 3. Naming

Naming is the one part of Java style that no formatter can fix for you.
`google-java-format` will indent your code and wrap your lines, but it will
never tell you that `mCustomerList` carries a Hungarian prefix, that
`static final Set<String> COLORS = new HashSet<>()` is not a constant, or
that `XMLHTTPRequest` violates the camel case algorithm. This chapter is
the normative reference for all of it.

The rules below cover [Google Java Style
§5](https://google.github.io/styleguide/javaguide.html#s5-naming) in full —
[§5.1 rules common to all
identifiers](https://google.github.io/styleguide/javaguide.html#s5.1-identifier-names),
[§5.2 rules by identifier
type](https://google.github.io/styleguide/javaguide.html#s5.2-specific-identifier-names),
and [§5.3 the camel case
algorithm](https://google.github.io/styleguide/javaguide.html#s5.3-camel-case) —
plus the design-level naming discipline from Effective Java, 3rd ed., Item
68 ("Adhere to generally accepted naming conventions"), which Google's guide
deliberately leaves open.

This chapter deliberately defers three neighbouring topics. Import
ordering, package-per-file layout, and the one-top-level-class rule belong
to [Chapter 2](02-source-file-structure.md). The Javadoc that explains what
a name means belongs to [Chapter 4](04-javadoc.md). The order in which
named members appear inside a class belongs to
[Chapter 6](06-modifiers-and-declaration-order.md). Nothing here concerns
whitespace, wrapping, or alignment — that is
[Chapter 1](01-formatting-and-tooling.md)'s territory.

**Tool alignment:** almost every rule in this chapter is mechanically
checkable. Checkstyle ships a dedicated check per identifier kind
(`PackageName`, `TypeName`, `MethodName`, `ConstantName`, `MemberName`,
`StaticVariableName`, `ParameterName`, `LocalVariableName`,
`LocalFinalVariableName`, `ClassTypeParameterName`,
`MethodTypeParameterName`, `InterfaceTypeParameterName`,
`RecordTypeParameterName`, `RecordComponentName`, `CatchParameterName`,
`LambdaParameterName`, `PatternVariableName`, `AbbreviationAsWordInName`),
and Error Prone contributes `ConstantField` and `TypeParameterNaming`.
Where a rule is enforced it is marked **Violation**; where it depends on
human judgement it is marked **Suggestion**.

## 3.1 Restrict every identifier to ASCII letters and digits, with underscores only where §5 explicitly allows them.

> Why? [§5.1](https://google.github.io/styleguide/javaguide.html#s5.1-identifier-names)
> is unambiguous: "Identifiers use only ASCII letters and digits, and, in a
> small number of cases noted below, underscores." Valid names match `\w+`.
> The JLS permits far more — currency symbols, Unicode letters, combining
> marks — and every one of those is a trap: they render inconsistently in
> terminals and diffs, they are unsearchable with a plain `grep`, and two
> visually identical identifiers can differ by an invisible codepoint. The
> only permitted underscores are those in §5.2.4 constant names, §5.2.3
> JUnit test method names, and §5.3's multipart numeric separator.
> **Violation — the default `format` patterns on Checkstyle's
> `MemberName`, `LocalVariableName`, `MethodName`, and `TypeName` are
> ASCII-only and reject anything else.**

```java
// bad — non-ASCII identifiers, and a currency symbol the JLS happens to allow
private final BigDecimal preçoTotal = BigDecimal.ZERO;
private int $counter;
private String naïveName;

// good
private final BigDecimal totalPrice = BigDecimal.ZERO;
private int counter;
private String naiveName;
```

## 3.2 Never attach a scope, type, or Hungarian prefix or suffix to an identifier.

> Why? [§5.1](https://google.github.io/styleguide/javaguide.html#s5.1-identifier-names)
> prohibits "special prefixes or suffixes" and names four offenders
> explicitly: `name_`, `mName`, `s_name`, and `kName`. Every one of these
> encodes information the compiler and the IDE already track, so the moment
> a field is promoted to a local or a static becomes an instance member,
> the prefix becomes an active lie. Java has no header files and no
> ambiguity about scope at the declaration site — the prefix buys nothing
> and costs a rename.
> **Violation — enforced by Checkstyle `MemberName`, `StaticVariableName`,
> `LocalVariableName`, and `ParameterName`.**

```java
// bad — m/s/k prefixes and a trailing underscore
public final class OrderCache {
  private static final int kMaxEntries = 1_000;
  private static Clock s_clock;
  private final Map<String, Order> mEntries;
  private int size_;
}

// good
public final class OrderCache {
  private static final int MAX_ENTRIES = 1_000;
  private static Clock clock;
  private final Map<String, Order> entries;
  private int size;
}
```

## 3.3 Write package names as lowercase letters and digits with consecutive words concatenated.

> Why? [§5.2.1](https://google.github.io/styleguide/javaguide.html#s5.2.1-package-names)
> requires that package and module names "use only lowercase letters and
> digits (no underscores)" and that "consecutive words are simply
> concatenated together": `com.example.deepspace`, never
> `com.example.deepSpace` or `com.example.deep_space`. Package names map
> directly onto directory names, and directory case-sensitivity differs
> between macOS, Linux, and Windows — a camel-cased package that compiles
> on one developer's machine can fail to resolve on another's.
> **Violation — enforced by Checkstyle `PackageName`.**

```java
// bad — camel case and an underscore in a package name
package com.example.orderProcessing.line_items;

// good
package com.example.orderprocessing.lineitems;
```

## 3.4 Write class, interface, enum, record, and annotation names in UpperCamelCase, as nouns or noun phrases.

> Why? [§5.2.2](https://google.github.io/styleguide/javaguide.html#s5.2.2-class-names)
> states that "class names are written in UpperCamelCase" and are
> "typically nouns or noun phrases", such as `Character` or
> `ImmutableList`. Interfaces follow the same rule but "may sometimes be
> adjectives or adjective phrases instead (for example, `Readable`)" —
> which is exactly right for capability interfaces. A verb-phrase type
> name (`ProcessOrder`) reads as a command and misleads the reader into
> expecting a method.
> **Violation — enforced by Checkstyle `TypeName`.**

```java
// bad — a verb phrase for a type, and a shouty acronym
public final class ProcessOrder { /* ... */ }

public interface HTTPClient { /* ... */ }

// good — noun for the class, adjective for the capability interface
public final class OrderProcessor { /* ... */ }

public interface HttpClient { /* ... */ }

public interface Retryable { /* ... */ }
```

## 3.5 Don't prefix an interface with `I`, and don't name the sole implementation `-Impl`.

> Why? Google's guide does not legislate this, so it is a **Suggestion**,
> but Effective Java, 3rd ed., Item 64 ("Refer to objects by their
> interfaces") explains the consequence: the interface is the name callers
> type against every day, so it should get the good name. `IOrderRepository`
> wastes a character on every reference to encode something `implements`
> already says. `OrderRepositoryImpl` is worse — it names the class after
> the fact that it is a class, telling the reader nothing about *how* it
> implements the contract. Name the implementation for its strategy
> (`JdbcOrderRepository`, `InMemoryOrderRepository`), which also survives
> the day a second implementation appears.

```java
// bad — the interface pays for the prefix, the class says nothing
public interface IOrderRepository {
  Optional<Order> findById(OrderId id);
}

public final class OrderRepositoryImpl implements IOrderRepository { /* ... */ }

// good — the abstraction gets the clean name, the class names its strategy
public interface OrderRepository {
  Optional<Order> findById(OrderId id);
}

public final class JdbcOrderRepository implements OrderRepository { /* ... */ }

public final class InMemoryOrderRepository implements OrderRepository { /* ... */ }
```

## 3.6 Suffix every test class with `Test`.

> Why? [§5.2.2](https://google.github.io/styleguide/javaguide.html#s5.2.2-class-names)
> requires that "a test class has a name that ends with `Test`", giving
> `HashIntegrationTest` and `HashImplTest` as models. This is not
> cosmetic: Maven Surefire's default include patterns are `Test*.java`,
> `*Test.java`, `*Tests.java`, and `*TestCase.java`, so a class named
> `OrderProcessorSpec` compiles, passes review, and is then silently never
> executed by CI. A test that never runs is worse than no test, because it
> reports coverage you do not have.

```java
// bad — never picked up by Surefire's default includes
final class OrderProcessorSpec {
  @Test
  void rejectsNegativeQuantity() { /* ... */ }
}

// good
final class OrderProcessorTest {
  @Test
  void rejectsNegativeQuantity() { /* ... */ }
}
```

## 3.7 Write method names in lowerCamelCase, as verbs or verb phrases.

> Why? [§5.2.3](https://google.github.io/styleguide/javaguide.html#s5.2.3-method-names)
> requires lowerCamelCase and notes methods are "typically verbs or verb
> phrases", such as `sendMessage` or `stop`. A noun-named method
> (`configuration()`, `orderTotal()`) reads as a field access, which hides
> the fact that calling it may be expensive, may throw, or may return a
> different value each time. Reserve bare-noun names for record accessors
> and true property reads.
> **Violation — enforced by Checkstyle `MethodName`.**

```java
// bad — a noun name hides an expensive network round-trip
public InventorySnapshot inventory(WarehouseId id) {
  return remoteClient.query(id); // blocking call
}

// good
public InventorySnapshot fetchInventory(WarehouseId id) {
  return remoteClient.query(id);
}
```

## 3.8 Use underscores in JUnit test method names to separate logical components, each written in lowerCamelCase.

> Why? [§5.2.3](https://google.github.io/styleguide/javaguide.html#s5.2.3-method-names)
> carves out exactly one exception to the no-underscores rule: "underscores
> may appear in JUnit test method names to separate logical components of
> the name, with each component written in lowerCamelCase", giving
> `transferMoney_deductsFromSource`. The payoff is a failure report you can
> read without opening the file: the method name states the unit under
> test, the scenario, and the expected outcome as separate fields. Note
> that Checkstyle's default `MethodName` pattern rejects underscores, so
> the test source set needs a relaxed `format` such as
> `^[a-z][a-z0-9][a-zA-Z0-9_]*$`.

```java
// bad — one undifferentiated blob; the failure report tells you nothing
@Test
void testTransfer2() { /* ... */ }

// bad — SCREAMING_SNAKE_CASE is not the exception §5.2.3 grants
@Test
void TRANSFER_MONEY_INSUFFICIENT_FUNDS() { /* ... */ }

// good — unit under test, scenario, expected outcome
@Test
void transferMoney_deductsFromSource() { /* ... */ }

@Test
void transferMoney_insufficientFunds_throwsInsufficientFundsException() { /* ... */ }
```

## 3.9 Reserve `UPPER_SNAKE_CASE` for fields that are `static final`, deeply immutable, and whose methods have no detectable side effects.

> Why? This is the single most misapplied rule in
> [§5.2.4](https://google.github.io/styleguide/javaguide.html#s5.2.4-constant-names).
> Constants are defined as "static final fields whose contents are *deeply
> immutable* and whose methods have *no detectable side effects*" —
> `static final` alone is not sufficient. A `static final Set<String>` bound
> to a `HashSet` is `final` only in its reference; the set itself is
> mutable, so it is not a constant and must not be styled as one. Styling
> it as a constant is an active lie that invites a caller to treat it as
> safe to share across threads. A `static final Logger` is likewise not a
> constant — logging is a detectable side effect. Note the inverse trap
> too: `static final SomeMutableType[] EMPTY_ARRAY = {}` *is* a constant,
> because a zero-length array has no mutable state.
> **Violation — enforced by Checkstyle `ConstantName` and Error Prone
> `ConstantField` ("Fields with CONSTANT_CASE names should be both static
> and final").**

```java
// bad — final reference, mutable contents: not a constant
static final Set<String> SUPPORTED_CURRENCIES = new HashSet<>();

// bad — logging is a detectable side effect
private static final Logger LOGGER = LoggerFactory.getLogger(OrderService.class);

// bad — CONSTANT_CASE on something that is neither static nor final
private String DEFAULT_REGION = "eu-west-1";

// good — deeply immutable, side-effect free
static final Set<String> SUPPORTED_CURRENCIES = Set.of("EUR", "GBP", "USD");
static final int MAX_RETRIES = 3;
static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(5);
static final String[] EMPTY_ARGS = {};

// good — not a constant, so lowerCamelCase
private static final Logger logger = LoggerFactory.getLogger(OrderService.class);
```

## 3.10 Write every non-constant field name in lowerCamelCase, whether or not it is `static`.

> Why? [§5.2.5](https://google.github.io/styleguide/javaguide.html#s5.2.5-non-constant-field-names)
> is explicit that "non-constant field names (static or otherwise) are
> written in lowerCamelCase", typically as nouns or noun phrases such as
> `computedValues` or `index`. The corollary matters more than the rule:
> `UPPER_SNAKE_CASE` in this codebase is a *promise* that the value is
> deeply immutable. Reserving it strictly means a reader can trust the
> casing without checking the initializer.
> **Violation — enforced by Checkstyle `MemberName` and
> `StaticVariableName`.**

```java
// bad — mutable shared state dressed up as a constant
private static Map<OrderId, Order> ORDER_CACHE = new ConcurrentHashMap<>();
private int RETRY_COUNT;

// good
private static final Map<OrderId, Order> orderCache = new ConcurrentHashMap<>();
private int retryCount;
```

## 3.11 Write local variable names in lowerCamelCase even when the local is `final`.

> Why? [§5.2.7](https://google.github.io/styleguide/javaguide.html#s5.2.7-local-variable-names)
> states it directly: "even when final and immutable, local variables are
> not considered to be constants, and should not be styled as constants."
> A local exists for the duration of one invocation; the whole point of
> `UPPER_SNAKE_CASE` is to flag a value shared across the entire class or
> program, and applying it to a local drains the signal. §5.2.7 states no
> further constraint, which is why one-character loop indices and catch
> parameters are acceptable here in a way §5.2.6 explicitly rules out for a
> public signature (see 3.12).
> **Violation — enforced by Checkstyle `LocalVariableName` and
> `LocalFinalVariableName`.**

```java
// bad — a local styled as a constant
void process(List<Order> orders) {
  final int BATCH_SIZE = 50;
  for (List<Order> BATCH : Lists.partition(orders, BATCH_SIZE)) {
    submit(BATCH);
  }
}

// good
void process(List<Order> orders) {
  final int batchSize = 50;
  for (List<Order> batch : Lists.partition(orders, batchSize)) {
    submit(batch);
  }
}
```

## 3.12 Write parameter names in lowerCamelCase, and avoid one-character parameter names in public methods.

> Why? [§5.2.6](https://google.github.io/styleguide/javaguide.html#s5.2.6-parameter-names)
> requires lowerCamelCase and adds that "one-character parameter names in
> public methods should be avoided." Parameter names are API: they appear
> in the generated Javadoc, in IDE parameter hints, and in the
> `-parameters` reflection metadata that Jackson and Spring bind against.
> `void transfer(Account a, Account b, BigDecimal x)` gives a caller no way
> to know which account is debited. Record components inherit this rule
> exactly, since a component name becomes both a field and an accessor.
> **Violation on the casing — enforced by Checkstyle `ParameterName` and
> `RecordComponentName`, whose default `format` patterns require
> lowerCamelCase. Suggestion on the length: those defaults accept a
> one-character name, so nothing catches `a` but review.**

```java
// bad — the caller cannot tell which account is debited
public void transfer(Account a, Account b, BigDecimal x) { /* ... */ }

public record Money(BigDecimal a, Currency c) {}

// good
public void transfer(Account source, Account destination, BigDecimal amount) { /* ... */ }

public record Money(BigDecimal amount, Currency currency) {}
```

## 3.13 Name type variables either as a single capital letter with an optional numeral, or as a class-style name suffixed with `T` — and never mix the two styles in one declaration.

> Why? [§5.2.8](https://google.github.io/styleguide/javaguide.html#s5.2.8-type-variable-names)
> permits exactly two styles: "a single capital letter, optionally followed
> by a single numeral (such as `E`, `T`, `X`, `T2`)" or "a name in the form
> used for classes, followed by the capital letter `T` (examples:
> `RequestT`, `FooBarT`)". A bare `Request` type variable is
> indistinguishable from a class name at the use site, which is precisely
> the confusion the mandatory `T` suffix removes. Mixing `<K, ValueT>` in
> one declaration forces the reader to hold two conventions at once.
> **Violation — enforced by Checkstyle `ClassTypeParameterName`,
> `MethodTypeParameterName`, `InterfaceTypeParameterName`, and
> `RecordTypeParameterName`, and by Error Prone `TypeParameterNaming`
> ("Type parameters must be a single letter with an optional numeric
> suffix, or an UpperCamelCase name followed by the letter 'T'").**

```java
// bad — a type variable indistinguishable from a class, and mixed styles
public interface Codec<Request, Response> {
  Response encode(Request request);
}

public final class Cache<K, ValueT> { /* ... */ }

// good — single letters for a small, obvious arity
public interface Codec<I, O> {
  O encode(I input);
}

// good — descriptive style, applied consistently, when the arity is higher
public interface Handler<RequestT, ResponseT, ContextT> {
  ResponseT handle(RequestT request, ContextT context);
}
```

## 3.14 Prefer the unnamed variable `_` for bindings you genuinely never read — but only once your baseline is Java 22.

> Why? [§5.2.9](https://google.github.io/styleguide/javaguide.html#s5.2.9-unnamed-variables)
> allows "the `_` syntax for unnamed variables and parameters ... wherever
> it is applicable", because a name you never read is noise that a reader
> must still check for a use. **Be precise about the version, though:
> unnamed variables and patterns shipped as a *preview* feature in Java 21
> ([JEP 443](https://openjdk.org/jeps/443)) and were finalized in Java 22
> (JEP 456). On a Java 21 baseline without `--enable-preview`, `_` is not
> available** — fall back to a short conventional name that announces the
> intent, such as `unused` or `ignored`. Error Prone's `UnusedVariable`
> documents the first of these as its opt-out: "False positives on fields
> and parameters can be suppressed by prefixing the variable name with
> `unused`." `ignored` carries no such tooling meaning; it is a convention
> for catch parameters only.

```java
// bad — a real name for a binding nobody reads; the reader must scan for a use
for (Map.Entry<OrderId, Order> entry : cache.entrySet()) {
  total++;
}
try {
  return Integer.parseInt(raw);
} catch (NumberFormatException exception) {
  return fallback;
}

// good on Java 21 — short conventional names that announce "deliberately unused"
for (Map.Entry<OrderId, Order> unused : cache.entrySet()) {
  total++;
}
try {
  return Integer.parseInt(raw);
} catch (NumberFormatException ignored) {
  return fallback;
}

// good on Java 22+ (preview in 21) — the binding is explicitly unnamed
for (Map.Entry<OrderId, Order> _ : cache.entrySet()) {
  total++;
}
try {
  return Integer.parseInt(raw);
} catch (NumberFormatException _) {
  return fallback;
}
```

## 3.15 Apply the camel case algorithm mechanically: lowercase every word including acronyms, then title-case each word.

> Why? [§5.3](https://google.github.io/styleguide/javaguide.html#s5.3-camel-case)
> defines camel case as a deterministic algorithm rather than a matter of
> taste, precisely so that two engineers converting the same prose arrive
> at the same identifier. Step 3 is the one everybody skips: "lowercase
> everything (including acronyms), then uppercase only the first character
> of each word." The guide notes "the casing of the original words is
> almost entirely disregarded." Preserving an acronym's shouty case
> produces `XMLHTTPRequest`, where the word boundary between `XML` and
> `HTTP` is invisible, and it breaks the moment two acronyms sit adjacent.
> **Violation — enforced by Checkstyle `AbbreviationAsWordInName`, which
> caps runs of consecutive capitals.**

```java
// bad — acronym casing preserved; word boundaries disappear
public final class XMLHTTPRequest {
  private String newCustomerID;

  boolean supportsIPv6OnIOS() { /* ... */ }
}

// good — §5.3 applied literally
public final class XmlHttpRequest {
  private String newCustomerId;

  boolean supportsIpv6OnIos() { /* ... */ }
}
```

## 3.16 Use underscores to separate adjacent numerals only where digits would otherwise run together.

> Why? [§5.3](https://google.github.io/styleguide/javaguide.html#s5.3-camel-case)
> grants this narrow exception: "in very rare circumstances (for example,
> multipart version numbers), you may need to use underscores to separate
> adjacent numbers, since numbers do not have upper and lower case
> variants." The guide's own example is `guava33_4_6` for "Guava 33.4.6" —
> without the separators you get `guava3346`, which is ambiguous between
> 33.4.6, 3.34.6, and 334.6. This is the *only* place outside constants and
> JUnit method names where an underscore is licensed; do not generalize it.

```java
// bad — digits collide, so 33.4.6, 3.34.6 and 334.6 all produce the same name
private final Dependency guava3346 = resolve("com.google.guava:guava:33.4.6");

// bad — "Turn on 2SV" title-cased mid-token; §5.3 lowercases the acronym first
void turnOn2Sv() { /* ... */ }

// bad — an underscore used for readability where no digits collide
void turn_on_2sv() { /* ... */ }

// good — separators only where numerals would run together
private final Dependency guava33_4_6 = resolve("com.google.guava:guava:33.4.6");

void turnOn2sv() { /* ... */ }
```

## 3.17 Name a variable for what it holds, not for the type that holds it.

> Why? A **Suggestion**, and Effective Java, 3rd ed., Item 68's advice to
> pick "grammatically consistent" names points the same way. `customerList`
> encodes a fact the declaration already states, and it becomes wrong the
> moment the type changes to a `Set` or a `Deque` — leaving you with a
> misleading name or a rename that touches every use site. The plural noun
> `customers` carries the multiplicity without binding you to an
> implementation. The same logic rules out `strName`, `objOrder`, and
> `mapIdToUser`.

```java
// bad — the name repeats the type and goes stale on the first refactor
Map<OrderId, Order> orderIdToOrderMap = load();
List<Customer> customerList = repository.findAll();
String strRegion = config.region();

// good
Map<OrderId, Order> ordersById = load();
List<Customer> customers = repository.findAll();
String region = config.region();
```

## 3.18 Name booleans as predicates that read as positive assertions.

> Why? A **Suggestion**, grounded in Effective Java, 3rd ed., Item 68's
> guidance that method names follow a consistent grammar. A boolean named
> for a negative forces every reader to evaluate a double negative at the
> call site: `if (!order.isNotShippable())` is genuinely harder to reason
> about than `if (order.isShippable())`, and the negation survives into log
> messages and config keys. Prefer the `is`/`has`/`can`/`should` prefixes,
> which make the identifier read as a claim that is either true or false.

```java
// bad — negative naming forces a double negative at every call site
private boolean notReady;

boolean isNotShippable() {
  return notReady || items.isEmpty();
}

if (!order.isNotShippable()) {
  ship(order);
}

// good
private boolean ready;

boolean isShippable() {
  return ready && !items.isEmpty();
}

if (order.isShippable()) {
  ship(order);
}
```

## 3.19 Follow the JDK's established method-name grammar for conversions, factories, and accessors.

> Why? A **Suggestion**, and Effective Java, 3rd ed., Item 1 ("Consider
> static factory methods instead of constructors") catalogues the
> vocabulary the JDK itself uses: `of` and `valueOf` for a value-preserving
> factory, `from` for a type conversion, `toX` for a new independent
> object, `asX` for a view backed by the receiver, `getInstance` for a
> managed instance, `newX` when each call must return a distinct object.
> These names carry real semantics — `asList` returning a *view* and
> `toList` returning a *copy* is a distinction callers depend on — so
> reusing them for different behaviour actively misleads. Note that a
> record accessor is named for the component with no prefix at all
> (`money.amount()`, not `money.getAmount()`); adopt the JavaBeans `getX`
> form only where a framework's reflection genuinely requires it.

```java
// bad — factory names that contradict the JDK's meanings
public static Money makeMoney(BigDecimal amount) { /* new value */ }

public static List<String> toNames(Order order) {
  return Collections.unmodifiableList(order.names()); // a view, not a copy
}

public record Money(BigDecimal amount, Currency currency) {
  public BigDecimal getAmount() {
    return amount;
  }
}

// good
public static Money of(BigDecimal amount, Currency currency) { /* ... */ }

public static Money from(MonetaryAmount source) { /* ... */ }

public static List<String> asNames(Order order) {
  return Collections.unmodifiableList(order.names());
}

public record Money(BigDecimal amount, Currency currency) {
  // amount() and currency() are generated; no getX wrapper is needed
}
```

## 3.20 Use exactly one name for one concept across the whole codebase.

> Why? A **Suggestion**, and the closing point of Effective Java, 3rd ed.,
> Item 68: naming conventions exist so that a name means the same thing
> everywhere. When `userId`, `accountId`, `customerRef`, and `principal`
> all denote the same identifier, no reader can tell whether a mismatch at
> a boundary is a bug or a synonym, and no `grep` finds all the call sites.
> Pick the term, write it into the domain vocabulary, and rename the
> stragglers — the cost is one mechanical refactor, and the alternative is
> a permanent tax on every future reader.

```java
// bad — four names for one concept across one call chain
public Receipt charge(String customerRef, BigDecimal amount) {
  Account account = accounts.byPrincipal(customerRef);
  return ledger.post(account.userId(), amount);
}

interface AccountRepository {
  Account byPrincipal(String accountId);
}

// good — one term, applied end to end
public Receipt charge(CustomerId customerId, BigDecimal amount) {
  Account account = accounts.byCustomerId(customerId);
  return ledger.post(customerId, amount);
}

interface AccountRepository {
  Account byCustomerId(CustomerId customerId);
}
```
