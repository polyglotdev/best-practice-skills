<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 33. Spring: Configuration & Properties

Configuration is an API. It has a schema, a set of invariants, a default
behaviour, and a compatibility contract with everyone who deploys the
service. Java gives you records, constructor validation, and a type system to
express all of that — and `@Value("${some.key}")` throws every bit of it away,
turning a typed contract into a scattering of untyped string lookups whose
only documentation is grep.

This chapter is about making the configuration surface of a Spring Boot
application as typed, as validated, and as discoverable as its Java API. It
draws from
[Spring Boot: Externalized Configuration](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html),
[Type-safe Configuration Properties](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties),
[Profiles](https://docs.spring.io/spring-boot/3.4/reference/features/profiles.html),
[the Configuration Metadata annotation processor](https://docs.spring.io/spring-boot/3.4/specification/configuration-metadata/annotation-processor.html),
and
[Spring Framework: Java Bean Validation](https://docs.spring.io/spring-framework/reference/core/validation/beanvalidation.html).

Two neighbouring topics live elsewhere. How a properties object gets injected
into the beans that need it — constructor injection, `final` fields, no
`getBean` — is [Chapter 32](32-spring-beans-and-di.md). Testing the rest of
the application is [Chapter 36](36-spring-testing.md); §33.18 here covers only
the narrow case of testing that binding and validation behave. The record
discipline that §33.2 depends on is [Chapter 12](12-records.md), and the
validation-at-the-boundary principle is
[Chapter 22](22-methods-and-parameters.md).

**Tool alignment:** as in chapter 32, the shipped Checkstyle and Error Prone
configuration has no Spring-aware checks, so most rules below are
**Suggestion**. The important exception is §33.5: once a properties type
carries `@Validated` and jakarta constraints, a bad value is caught by the
framework at context refresh and the application **fails to start** — that is
real enforcement, in production as well as in CI, and it is the main reason
to prefer typed properties at all.

## 33.1 Bind configuration with `@ConfigurationProperties`, not with scattered `@Value` annotations.

> Why? The
> [Spring Boot reference](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.vs-value-annotation)
> tabulates the difference: `@ConfigurationProperties` supports relaxed
> binding and metadata generation, `@Value` supports neither. Beyond the
> table, a properties type gives you one place to read the full
> configuration surface, one place to document it, one object to pass to a
> unit test, and one constructor in which to enforce cross-field invariants.
> `@Value` gives you N untyped lookups scattered across N classes, each of
> which fails independently and none of which appears in IDE completion.
> **Suggestion.**

```java
// bad — the configuration surface of this service is invisible; nothing lists
// these five keys, nothing validates them, nothing documents them
@Service
public class PaymentService {
  @Value("${payment.base-url}") private String baseUrl;
  @Value("${payment.api-key}") private String apiKey;
  @Value("${payment.timeout-ms:5000}") private long timeoutMs;
  @Value("${payment.retry-attempts:3}") private int retryAttempts;
  @Value("${payment.sandbox:false}") private boolean sandbox;
}

// good — one type is the schema, and the service takes it as a dependency
@ConfigurationProperties("payment")
public record PaymentProperties(
    URI baseUrl, String apiKey, Duration timeout, int retryAttempts, boolean sandbox) {}

@Service
public class PaymentService {
  private final PaymentProperties properties;

  public PaymentService(PaymentProperties properties) {
    this.properties = properties;
  }
}
```

## 33.2 Make the properties type immutable — a `record`, or a class whose fields are all `final`.

> Why? Configuration does not change after startup, so a mutable properties
> bean models the wrong thing and invites the bug in §33.17. Spring Boot's
> [constructor binding](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.constructor-binding)
> exists precisely to support "immutable configuration properties through
> parameterized constructors", and a record is the shortest possible spelling
> of one. As a bonus you get a real `toString`, `equals`, and `hashCode` for
> free, which makes configuration trivially assertable in a test.
> **Suggestion.**

```java
// bad — JavaBean binding: mutable, verbose, and constructible in an invalid
// state
@ConfigurationProperties("payment")
public class PaymentProperties {
  private URI baseUrl;
  private Duration timeout;

  public URI getBaseUrl() {
    return baseUrl;
  }

  public void setBaseUrl(URI baseUrl) {
    this.baseUrl = baseUrl;
  }

  public Duration getTimeout() {
    return timeout;
  }

  public void setTimeout(Duration timeout) {
    this.timeout = timeout;
  }
}

// good
@ConfigurationProperties("payment")
public record PaymentProperties(URI baseUrl, Duration timeout) {}
```

## 33.3 Add `@ConstructorBinding` only when the type declares more than one constructor.

> Why? The
> [reference](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.constructor-binding)
> is explicit that the annotation is not required when the class has a single
> parameterized constructor, and is required when several are available so
> Spring knows which to bind through. Since Spring Boot 3, `@ConstructorBinding`
> is declared on the *constructor*, not the type. Writing it on a record with
> one canonical constructor is noise; omitting it on a class with two
> constructors is a binding failure at startup. **Suggestion.**

```java
// bad — redundant on a record, which has exactly one canonical constructor
@ConfigurationProperties("payment")
public record PaymentProperties(URI baseUrl, Duration timeout) {
  @ConstructorBinding
  public PaymentProperties {}
}

// good — annotation appears only where there is a genuine choice to make
@ConfigurationProperties("payment")
public record PaymentProperties(URI baseUrl, Duration timeout, int retryAttempts) {

  @ConstructorBinding
  public PaymentProperties(URI baseUrl, Duration timeout, int retryAttempts) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
    this.retryAttempts = retryAttempts;
  }

  public PaymentProperties(URI baseUrl) {
    this(baseUrl, Duration.ofSeconds(5), 3);
  }
}
```

## 33.4 Register properties types with `@ConfigurationPropertiesScan` or `@EnableConfigurationProperties` — never with `@Component`.

> Why? The
> [reference](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.enabling-annotated-types)
> gives exactly these two mechanisms, and both go through the binder.
> `@Component` on a properties type makes it an ordinary bean created by
> component scanning, and the reference is explicit that "you cannot use
> constructor binding with beans that are created by the regular Spring
> mechanisms (for example `@Component` beans, beans created by using `@Bean`
> methods or beans loaded by using `@Import`)". A record annotated
> `@Component` therefore has its components treated as autowired
> collaborators and fails to instantiate; a JavaBean-style class still binds
> through its setters, so it looks like it works while quietly ruling out the
> immutability of §33.2 and any later move to a record. Put
> `@ConfigurationPropertiesScan` on the application class once and stop
> thinking about it. **Suggestion.**

```java
// bad — component scanning, not binding
@Component
@ConfigurationProperties("payment")
public record PaymentProperties(URI baseUrl, Duration timeout) {}

// good — one annotation on the application class covers every properties type
@SpringBootApplication
@ConfigurationPropertiesScan
public class CheckoutApplication {
  public static void main(String[] args) {
    SpringApplication.run(CheckoutApplication.class, args);
  }
}

@ConfigurationProperties("payment")
public record PaymentProperties(URI baseUrl, Duration timeout) {}
```

## 33.5 Annotate the properties type `@Validated` and constrain every field, so a bad value fails the deployment instead of the request.

> Why? The
> [reference](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.validation)
> says Spring Boot "attempts to validate `@ConfigurationProperties` classes
> whenever they are annotated with Spring's `@Validated` annotation", using
> "JSR-303 `jakarta.validation` constraint annotations directly on your
> configuration class". Failure happens at context refresh, which means a bad
> value is caught by the deployment pipeline rather than by the first
> customer to hit the code path that reads it. One caveat the docs call out
> and everyone forgets: "to cascade validation to nested properties the
> associated field must be annotated with `@Valid`". **Violation — the
> application context fails to start.**

```java
// bad — a blank API key or a negative retry count starts cleanly and fails at
// the first request; the nested Security block is never validated at all
@ConfigurationProperties("payment")
public record PaymentProperties(URI baseUrl, int retryAttempts, Security security) {
  public record Security(String apiKey) {}
}

// good
@ConfigurationProperties("payment")
@Validated
public record PaymentProperties(
    @NotNull URI baseUrl,
    @Min(0) @Max(10) int retryAttempts,
    @Valid @NotNull Security security) {

  public record Security(@NotBlank String apiKey) {}
}
```

## 33.6 Write every property key in canonical kebab-case, in YAML and in every `${...}` placeholder.

> Why? Relaxed binding means `payment.retry-attempts`,
> `payment.retryAttempts`, and `PAYMENT_RETRYATTEMPTS` all bind to the same
> component — but only for `@ConfigurationProperties`. The
> [reference](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.relaxed-binding)
> is unambiguous about placeholders: "You should always refer to property
> names in the placeholder using their canonical form (kebab-case using only
> lowercase letters). This will allow Spring Boot to use the same logic as it
> does when relaxed binding `@ConfigurationProperties`." Mixed spellings also
> defeat grep, which is the only tool anyone actually uses to find where a key
> is consumed. **Suggestion.**

```yaml
# bad — three spellings of one namespace, and a camelCase placeholder that
# will not resolve from an environment variable
payment:
  baseUrl: https://payments.internal
  retry_attempts: 3
messaging:
  callback: ${payment.baseUrl}/callback

# good
payment:
  base-url: https://payments.internal
  retry-attempts: 3
messaging:
  callback: ${payment.base-url}/callback
```

## 33.7 Put defaults in the properties type, not in a `${key:default}` expression.

> Why? A default embedded in a placeholder is invisible to the metadata
> processor, invisible in IDE completion, and duplicated at every injection
> point — so the day two classes disagree about what "the default timeout" is,
> nothing tells you. In a record, use
> [`@DefaultValue`](https://docs.spring.io/spring-boot/api/java/org/springframework/boot/context/properties/bind/DefaultValue.html);
> in a JavaBean-style class, use a field initializer. Either way the default
> lives beside the field it defaults, is picked up by the metadata processor,
> and is assertable in a test. **Suggestion.**

```java
// bad — the default lives in three placeholder strings across three classes
@Value("${payment.timeout:5s}") private Duration timeout;

// good — the default is part of the type
@ConfigurationProperties("payment")
@Validated
public record PaymentProperties(
    @NotNull URI baseUrl,
    @DefaultValue("5s") Duration timeout,
    @DefaultValue("3") @Min(0) int retryAttempts) {}
```

## 33.8 Bind time to `Duration` and sizes to `DataSize`, never to a bare `long` with the unit in the name.

> Why? `timeoutMs` is a unit encoded in an identifier, which the compiler
> cannot check — the classic failure is passing a value meant as seconds into
> a parameter that wants milliseconds. Spring Boot converts `5s`, `PT5S`, and
> `500ms` into a `Duration`, and `10MB` into a `DataSize`, out of the box; and
> [`@DurationUnit`](https://docs.spring.io/spring-boot/api/java/org/springframework/boot/convert/DurationUnit.html)
> or
> [`@DataSizeUnit`](https://docs.spring.io/spring-boot/api/java/org/springframework/boot/convert/DataSizeUnit.html)
> declares the unit for a bare number, so old unit-less config keeps working.
> A `Duration` is also self-documenting at every call site. See
> [Chapter 28](28-dates-and-times.md). **Suggestion.**

```java
// bad — is 30 seconds or milliseconds? the caller has to guess
@ConfigurationProperties("payment")
public record PaymentProperties(long timeoutMs, long maxUploadBytes) {}

// good
@ConfigurationProperties("payment")
public record PaymentProperties(
    @DefaultValue("5s") Duration timeout,
    @DurationUnit(ChronoUnit.SECONDS) @DefaultValue("30") Duration circuitBreakerReset,
    @DefaultValue("10MB") DataSize maxUpload) {}
```

## 33.9 Never put a secret in `application.yaml`, a profile file, or any other file under version control.

> Why? A secret committed to git is a secret forever — rotating the value does
> not remove it from history, from every developer's clone, from CI caches, or
> from whatever mirror your host keeps. Because
> [environment variables and command-line arguments outrank config files](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.order)
> in Spring Boot's precedence order, injecting a secret at deploy time
> requires no code change at all — just leave the key out of the file. For
> local development, use a `.env`-style file that is git-ignored, a config
> tree mounted from a secret store, or Spring Cloud Vault. **Suggestion.**

```yaml
# bad — now in git history permanently
payment:
  api-key: REDACTED_STRIPE_SECRET_KEY

# good — no default; the key must come from the environment, and its absence
# fails validation at startup (§33.5)
payment:
  base-url: https://payments.internal
# PAYMENT_API_KEY is supplied by the deployment platform's secret store
```

## 33.10 Add `spring-boot-configuration-processor` so your keys have metadata.

> Why? The
> [annotation processor](https://docs.spring.io/spring-boot/3.4/specification/configuration-metadata/annotation-processor.html)
> reads your `@ConfigurationProperties` types at compile time and emits
> `META-INF/spring-configuration-metadata.json`. That file is what gives an
> IDE completion, type checking, and Javadoc-on-hover inside
> `application.yaml` — the difference between configuration that is
> discoverable and configuration that requires reading source. It costs one
> `annotationProcessor` dependency and zero runtime weight. **Suggestion.**

```groovy
// bad — no metadata; application.yaml is an untyped text file to the IDE
dependencies {
  implementation 'org.springframework.boot:spring-boot-starter-web'
}

// good
dependencies {
  implementation 'org.springframework.boot:spring-boot-starter-web'
  annotationProcessor 'org.springframework.boot:spring-boot-configuration-processor'
}
```

## 33.11 Reserve `@Value` for a single flat value, and never use it for non-trivial SpEL.

> Why? `@Value` is not banned — one key read by one class does not justify a
> properties type. What it must not become is a place where logic hides. A
> SpEL expression in an annotation is a string the compiler never sees: it
> cannot be unit tested, it cannot be stepped through, its failure mode is a
> startup `SpelEvaluationException` naming a character offset, and refactoring
> a bean or method name silently breaks it. If the value needs computing,
> compute it in Java from typed properties. **Suggestion.**

```java
// bad — business logic in an annotation string
@Value("#{T(java.time.Duration).ofSeconds(${payment.timeout-seconds} * 2)}")
private Duration doubledTimeout;

// good — the properties type carries the input, Java carries the arithmetic
@Service
public class PaymentService {
  private final Duration doubledTimeout;

  public PaymentService(PaymentProperties properties) {
    this.doubledTimeout = properties.timeout().multipliedBy(2);
  }
}
```

## 33.12 Group related keys into nested types instead of flattening the prefix.

> Why? A flat record with fourteen components is the configuration equivalent
> of a fourteen-argument constructor — §32.5 applies. Nesting gives the YAML
> a shape that mirrors the domain, lets you pass just the relevant sub-object
> to the collaborator that needs it (so the retry policy does not receive the
> API key), and makes each nested type independently validatable and
> testable. **Suggestion.**

```java
// bad — flat namespace, and every consumer gets every key
@ConfigurationProperties("payment")
public record PaymentProperties(
    URI baseUrl,
    String apiKey,
    String webhookSecret,
    Duration connectTimeout,
    Duration readTimeout,
    int retryAttempts,
    Duration retryBackoff) {}

// good
@ConfigurationProperties("payment")
@Validated
public record PaymentProperties(
    @NotNull URI baseUrl, @Valid @NotNull Credentials credentials, @Valid @NotNull Retry retry) {

  public record Credentials(@NotBlank String apiKey, @NotBlank String webhookSecret) {}

  public record Retry(
      @DefaultValue("3") @Min(0) int attempts, @DefaultValue("200ms") Duration backoff) {}
}
```

## 33.13 Express environment differences with profile-specific files, not with `if` statements.

> Why? `application-{profile}.yaml` is loaded automatically for each active
> profile and layered over the base file, which means the base file documents
> the complete key set and each profile file documents only its delta — a
> reviewer can see exactly what production changes. The
> [profiles reference](https://docs.spring.io/spring-boot/3.4/reference/features/profiles.html#features.profiles.profile-specific-configuration-files)
> also warns that `spring.profiles.active`, `include`, `default`, and `group`
> "can only be used in non-profile-specific documents" — activating a profile
> from inside a profile file is silently ignored. **Suggestion.**

```java
// bad — environment branching compiled into the application
@Service
public class PaymentService {
  public URI endpoint() {
    if ("prod".equals(System.getenv("ENV"))) {
      return URI.create("https://payments.internal");
    }
    return URI.create("https://payments.sandbox.internal");
  }
}
```

```yaml
# good — application.yaml holds the full key set and the safe default
payment:
  base-url: https://payments.sandbox.internal
  retry-attempts: 3

# application-prod.yaml holds only the delta
payment:
  base-url: https://payments.internal
```

## 33.14 Keep the profile set small, and never branch business logic on `@Profile`.

> Why? Profiles multiply: five profiles that can be combined give you thirty-two
> possible configurations, of which you test maybe two. Every additional
> profile is another axis along which staging can diverge from production and
> another way for a bean to be missing in exactly one environment. Use
> profiles for *infrastructure* choices — which datasource, which message
> broker, which mail transport — and use `@ConditionalOnProperty` (§32.14) for
> feature toggles, because a property is one boolean rather than a new
> combinatorial dimension. When you do need several related profiles,
> [`spring.profiles.group`](https://docs.spring.io/spring-boot/3.4/reference/features/profiles.html#features.profiles.groups)
> collapses them behind one name. **Suggestion.**

```java
// bad — a business rule that exists only in one environment, so the code path
// that runs in production is never the one that runs in test
@Service
public class DiscountService {
  private final Environment environment;

  public BigDecimal discountFor(Customer customer) {
    if (environment.acceptsProfiles(Profiles.of("prod"))) {
      return customer.loyaltyTier().discount();
    }
    return BigDecimal.ZERO;
  }
}

// good — one code path everywhere; the number is configuration
@Service
public class DiscountService {
  private final DiscountProperties properties;

  public BigDecimal discountFor(Customer customer) {
    return properties.enabled() ? customer.loyaltyTier().discount() : BigDecimal.ZERO;
  }
}
```

## 33.15 Know the precedence order, and put each override at the level whose precedence matches its scope.

> Why? The
> [precedence list](https://docs.spring.io/spring-boot/3.4/reference/features/external-config.html#features.external-config.order)
> is ordered so that later sources win: config files inside the jar, then
> config files outside it, then OS environment variables, then system
> properties, then command-line arguments, then test property sources.
> Fighting that order is the root cause of "the value I set is being ignored"
> — for example, putting a production URL in `application.yaml` and then
> trying to override it from a profile file that is *also* baked into the same
> jar. The rule of thumb: baked-in files hold defaults, the environment holds
> per-deployment values, command-line arguments hold one-off overrides.
> **Suggestion.**

```yaml
# bad — a per-deployment value baked into the jar, then "overridden" by a
# second baked-in file whose precedence is barely different
# application.yaml
payment:
  base-url: https://payments.internal

# good — the jar carries the safe default; the platform supplies
# PAYMENT_BASE_URL, which is an OS environment variable and therefore wins
payment:
  base-url: https://payments.sandbox.internal
```

## 33.16 Never read configuration through `System.getenv` or `System.getProperty`.

> Why? Bypassing the `Environment` bypasses everything that makes Spring's
> configuration usable: relaxed binding, profile layering, type conversion,
> validation, metadata, and the precedence order in §33.15. It also makes the
> value untestable — a test cannot set an environment variable for one test
> method — and it hides the key from every tool that inventories your
> configuration surface. **Suggestion.**

```java
// bad — invisible to the Environment, untestable, unvalidated, and
// String-typed
@Service
public class PaymentService {
  private final String baseUrl = System.getenv("PAYMENT_BASE_URL");
  private final int retries = Integer.parseInt(System.getProperty("payment.retries", "3"));
}

// good — PAYMENT_BASE_URL still works, via relaxed binding, but now it is
// typed, validated, documented, and overridable in a test
@Service
public class PaymentService {
  private final PaymentProperties properties;

  public PaymentService(PaymentProperties properties) {
    this.properties = properties;
  }
}
```

## 33.17 Never mutate a properties object at runtime, and never expose a mutable collection from one.

> Why? A properties bean is a singleton (§32.9), so a setter call from a
> request thread is a data race visible to every other request. It is also a
> lie: whatever you set will not survive a restart and will not match the
> deployed configuration, so the running system no longer matches its own
> declared state. A record whose components are collections needs the same
> defensive copy any other value type does — see
> [Chapter 12](12-records.md) and [Chapter 20](20-collections.md).
> **Suggestion.**

```java
// bad — a JavaBean properties class with public setters, handing out its own
// mutable list
@ConfigurationProperties("payment")
public class PaymentProperties {
  private List<String> allowedCurrencies = new ArrayList<>();

  public List<String> getAllowedCurrencies() {
    return allowedCurrencies;
  }

  public void setAllowedCurrencies(List<String> allowedCurrencies) {
    this.allowedCurrencies = allowedCurrencies;
  }
}

// good — immutable in, immutable out
@ConfigurationProperties("payment")
public record PaymentProperties(List<String> allowedCurrencies) {

  public PaymentProperties {
    allowedCurrencies = List.copyOf(allowedCurrencies);
  }
}
```

## 33.18 Test binding and validation with `ApplicationContextRunner`, not `@SpringBootTest`.

> Why?
> [`ApplicationContextRunner`](https://docs.spring.io/spring-boot/api/java/org/springframework/boot/test/context/runner/ApplicationContextRunner.html)
> builds a throwaway context containing only the configuration under test, in
> milliseconds, and its AssertJ integration lets you assert on the *failure*
> as easily as on the success. That matters here more than anywhere else,
> because the interesting cases for a properties type are the ones where the
> context is supposed to refuse to start. `@SpringBootTest` cannot express
> that cleanly — a failed refresh fails the test. See
> [Chapter 36](36-spring-testing.md) for the wider slice-test rules.
> **Suggestion.**

```java
// bad — boots the whole application to check that one default is 3, and has
// no way to assert that a bad value is rejected
@SpringBootTest
class PaymentPropertiesTest {
  @Autowired private PaymentProperties properties;

  @Test
  void defaultRetryAttempts() {
    assertThat(properties.retry().attempts()).isEqualTo(3);
  }
}

// good
class PaymentPropertiesTest {

  private final ApplicationContextRunner runner =
      new ApplicationContextRunner().withUserConfiguration(TestConfiguration.class);

  @Test
  void appliesDefaultsWhenKeysAreAbsent() {
    runner
        .withPropertyValues("payment.base-url=https://payments.test")
        .run(context -> assertThat(context.getBean(PaymentProperties.class).retry().attempts())
            .isEqualTo(3));
  }

  @Test
  void rejectsNegativeRetryAttempts() {
    runner
        .withPropertyValues("payment.base-url=https://payments.test", "payment.retry.attempts=-1")
        .run(context -> assertThat(context).hasFailed());
  }

  @Configuration(proxyBeanMethods = false)
  @EnableConfigurationProperties(PaymentProperties.class)
  static class TestConfiguration {}
}
```

## 33.19 Bind to a `Map` only for a genuinely open key set, and keep the value type strong.

> Why? `Map<String, String>` is the configuration equivalent of `Object` — it
> defeats validation, defeats metadata, and pushes every parse and every
> missing-key check into the code that reads it. It is the right shape only
> when the *keys* are supplied by the deployment, not by you: per-tenant
> settings, per-queue overrides, per-region endpoints. Even then, make the
> value a validated nested type so only the key set is open.
> **Suggestion.**

```java
// bad — every value is a String and nothing checks any of them
@ConfigurationProperties("tenants")
public record TenantProperties(Map<String, String> settings) {}

// good — open key set, closed and validated value type
@ConfigurationProperties("tenants")
@Validated
public record TenantProperties(Map<String, @Valid TenantSettings> settings) {

  public record TenantSettings(
      @NotNull URI callbackUrl, @DefaultValue("5s") Duration timeout, @Min(1) int maxConcurrency) {}
}
```

## 33.20 Do not inject `Environment` to read a key.

> Why? `Environment.getProperty` returns `String` (or a converted type with no
> validation), takes the key as a literal, and reintroduces every problem
> §33.1 and §33.16 removed — with the added cost that the class now depends on
> a Spring type and cannot be constructed in a plain unit test. `Environment`
> is a framework-level abstraction for framework-level code: condition
> evaluation, property-source inspection, profile queries in infrastructure.
> Application beans take a properties object. **Suggestion.**

```java
// bad — untyped, unvalidated, and now coupled to a Spring interface
@Service
public class PaymentService {
  private final Environment environment;

  public PaymentService(Environment environment) {
    this.environment = environment;
  }

  public URI endpoint() {
    return URI.create(environment.getProperty("payment.base-url"));
  }
}

// good
@Service
public class PaymentService {
  private final PaymentProperties properties;

  public PaymentService(PaymentProperties properties) {
    this.properties = properties;
  }

  public URI endpoint() {
    return properties.baseUrl();
  }
}
```

## 33.21 Namespace your keys under a prefix you own, never under `spring.*` or another library's prefix.

> Why? `spring.*`, `server.*`, `management.*`, and `logging.*` belong to
> Spring Boot; `spring.datasource.*` and friends are bound by
> auto-configuration you do not control. Adding your own key inside one of
> those namespaces means a future Boot upgrade can define the same key with
> different semantics, and it means your value shows up in actuator
> configuration listings as if the framework owned it. Pick a prefix that
> matches your application or module and keep everything under it — that also
> makes the whole configuration surface greppable by one string.
> **Suggestion.**

```yaml
# bad — squatting inside a framework namespace
spring:
  datasource:
    read-replica-url: jdbc:postgresql://replica.internal:5432/checkout
management:
  alert-webhook: https://hooks.internal/alerts

# good
checkout:
  datasource:
    read-replica-url: jdbc:postgresql://replica.internal:5432/checkout
  alerting:
    webhook: https://hooks.internal/alerts
```
