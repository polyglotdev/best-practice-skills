<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 32. Spring: Beans & Dependency Injection

A Spring bean is an ordinary Java object that someone else constructs. Every
rule in this chapter follows from taking that sentence literally: if the
container is the only thing that can build your object, then your object is
untestable, its dependencies are invisible, and its invariants are
unenforceable. Good Spring code is code that would still work if you deleted
every annotation and wired it by hand in a `main` method — the container just
saves you the typing.

This chapter draws from
[Spring Framework: Dependency Injection](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html),
[Annotation-based Autowiring](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html),
[Fine-tuning with Qualifiers](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html),
[Classpath Scanning and Managed Components](https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html),
[Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html),
[Customizing the Nature of a Bean](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html),
[Basic Concepts: `@Bean` and `@Configuration`](https://docs.spring.io/spring-framework/reference/core/beans/java/basic-concepts.html),
and
[Spring Boot: Creating Your Own Auto-configuration](https://docs.spring.io/spring-boot/3.4/reference/features/developing-auto-configuration.html).

Three neighbouring topics live elsewhere. Binding external configuration into
beans is [Chapter 33](33-spring-configuration.md). Transaction proxies and
the self-invocation trap are [Chapter 35](35-spring-data-and-transactions.md).
Replacing beans in tests is [Chapter 36](36-spring-testing.md). The
non-Spring design rules these lean on — immutability, composition over
inheritance, constructor validation — are
[Chapter 8](08-object-creation.md) and
[Chapter 11](11-classes-and-interfaces.md).

**Tool alignment:** the Checkstyle and Error Prone configuration shipped with
this skill (chapter 38) contains **no Spring-aware checks** — Checkstyle does
not know what `@Autowired` is. Almost every rule below is therefore a
**Suggestion**. The two enforcement mechanisms that do exist are Spring
itself, which fails the context refresh on an unbroken circular reference
(§32.13) or on an ambiguity no qualifier resolves, and
[ArchUnit](https://www.archunit.org/), which can assert
structural rules like "no field is annotated with `@Autowired`" as an ordinary
JUnit test:

```java
ArchRule noFieldInjection =
    ArchRuleDefinition.noFields().should().beAnnotatedWith(Autowired.class);
```

## 32.1 Inject every mandatory collaborator through the constructor and store it in a `final` field.

> Why? The
> [Spring Framework reference](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
> states the team position directly: "The Spring team generally advocates
> constructor injection, as it lets you implement application components as
> immutable objects and ensures that required dependencies are not `null`.
> Furthermore, constructor-injected components are always returned to the
> client (calling) code in a fully initialized state." `final` is what makes
> that guarantee mechanical — the compiler, not a code reviewer, rejects a
> half-built bean. **Suggestion.**

```java
// bad — nothing stops the field being reassigned, and nothing proves it was
// ever assigned
@Service
public class CheckoutService {
  private PaymentGateway gateway;
  private OrderRepository orders;
}

// good
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private final OrderRepository orders;

  public CheckoutService(PaymentGateway gateway, OrderRepository orders) {
    this.gateway = gateway;
    this.orders = orders;
  }
}
```

## 32.2 Omit `@Autowired` when the class declares exactly one constructor.

> Why? The
> [autowiring reference](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html)
> says an "`@Autowired` annotation on such a constructor is not necessary if
> the target bean defines only one constructor." Keeping it adds a
> framework import to a class that would otherwise be plain Java, and it
> misleads the next reader into thinking a second constructor exists
> somewhere. Add the annotation back only when several constructors are
> available and Spring must be told which one to use. **Suggestion.**

```java
// bad — redundant annotation on the only constructor
@Service
public class CheckoutService {
  private final PaymentGateway gateway;

  @Autowired
  public CheckoutService(PaymentGateway gateway) {
    this.gateway = gateway;
  }
}

// good — no Spring import needed at all
@Service
public class CheckoutService {
  private final PaymentGateway gateway;

  public CheckoutService(PaymentGateway gateway) {
    this.gateway = gateway;
  }
}
```

## 32.3 Never inject into a field.

> Why? Field injection breaks four things at once. The field cannot be
> `final`, so the object is mutable for no reason. The dependency list is
> invisible at the constructor, so a class can accumulate fifteen
> collaborators and still look small. The object cannot be constructed in a
> unit test without a container or reflection. And because the field is
> populated after construction, the class silently tolerates the circular
> dependencies that §32.13 exists to prevent. **Suggestion.**

```java
// bad — untestable without reflection, non-final, hides the dependency count
@Service
public class CheckoutService {
  @Autowired private PaymentGateway gateway;
  @Autowired private OrderRepository orders;
  @Autowired private InventoryClient inventory;
  @Autowired private AuditLog audit;
  @Autowired private NotificationSender notifications;
}

// good — `new CheckoutService(...)` works in a plain JUnit test
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private final OrderRepository orders;

  public CheckoutService(PaymentGateway gateway, OrderRepository orders) {
    this.gateway = gateway;
    this.orders = orders;
  }
}
```

## 32.4 Never use setter injection for a mandatory dependency.

> Why? The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
> scopes setters narrowly: "Setter injection should primarily only be used
> for optional dependencies that can be assigned reasonable default values
> within the class. Otherwise, not-null checks must be performed everywhere
> the code uses the dependency." A mandatory dependency behind a setter
> means every method body has to defend against a `null` the constructor
> should have made impossible. For genuinely optional collaborators, use
> `ObjectProvider` (§32.17) rather than a setter. **Suggestion.**

```java
// bad — the bean exists in an unusable state between construction and the
// setter call, and every method must guard against it
@Service
public class CheckoutService {
  private PaymentGateway gateway;

  @Autowired
  public void setGateway(PaymentGateway gateway) {
    this.gateway = gateway;
  }

  public Receipt checkout(Order order) {
    if (gateway == null) {
      throw new IllegalStateException("gateway not set");
    }
    return gateway.charge(order.total());
  }
}

// good
@Service
public class CheckoutService {
  private final PaymentGateway gateway;

  public CheckoutService(PaymentGateway gateway) {
    this.gateway = gateway;
  }

  public Receipt checkout(Order order) {
    return gateway.charge(order.total());
  }
}
```

## 32.5 Treat a long constructor parameter list as a design defect, not an injection problem.

> Why? The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
> is blunt: "a large number of constructor arguments is a bad code smell,
> implying that the class likely has too many responsibilities and should be
> refactored to better address proper separation of concerns." Switching to
> field injection to hide seven dependencies does not remove them — it
> removes the signal. Extract a collaborator that owns the cohesive subset.
> **Suggestion.**

```java
// bad — eight collaborators, so the class does eight things
@Service
public class CheckoutService {
  public CheckoutService(
      PaymentGateway gateway,
      OrderRepository orders,
      InventoryClient inventory,
      TaxCalculator tax,
      ShippingQuoter shipping,
      EmailSender email,
      SmsSender sms,
      AuditLog audit) {
    // ...
  }
}

// good — pricing and notification are extracted behind their own interfaces
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private final OrderRepository orders;
  private final OrderPricer pricer;
  private final CustomerNotifier notifier;

  public CheckoutService(
      PaymentGateway gateway,
      OrderRepository orders,
      OrderPricer pricer,
      CustomerNotifier notifier) {
    this.gateway = gateway;
    this.orders = orders;
    this.pricer = pricer;
    this.notifier = notifier;
  }
}
```

## 32.6 Annotate each component with the most specific stereotype that fits, and fall back to `@Component` only when none does.

> Why? The
> [classpath-scanning reference](https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html)
> explains that `@Repository`, `@Service`, and `@Controller` "are
> specializations of `@Component` for more specific use cases" and that they
> "make ideal targets for pointcuts" — and it concludes that "if you are
> choosing between using `@Component` or `@Service` for your service layer,
> `@Service` is clearly the better choice." `@Repository` is not decorative:
> it is what enables "the automatic translation of exceptions" from a
> vendor-specific persistence exception into Spring's `DataAccessException`
> hierarchy. **Suggestion.**

```java
// bad — @Component everywhere; the persistence class gets no exception
// translation and the layer boundaries are invisible to pointcuts
@Component
public class JdbcOrderRepository implements OrderRepository { }

@Component
public class CheckoutService { }

// good
@Repository
public class JdbcOrderRepository implements OrderRepository { }

@Service
public class CheckoutService { }

@RestController
public class CheckoutController { }
```

## 32.7 Define beans for third-party types with `@Bean` methods on a `@Configuration` class.

> Why? You cannot put `@Component` on a class you do not compile. A `@Bean`
> factory method is the supported way to bring a third-party type under
> container management, and it keeps the construction logic — timeouts,
> credentials, interceptors — in one reviewable place instead of scattered
> across the call sites that would otherwise `new` it. It also gives the
> object a name and a lifecycle the container can shut down. **Suggestion.**

```java
// bad — every caller builds its own client with its own timeouts
@Service
public class InventoryClient {
  private final RestClient http = RestClient.create("https://inventory.internal");
}

// good — one definition, one place to change the timeout or add a filter
@Configuration(proxyBeanMethods = false)
public class HttpClientConfiguration {

  @Bean
  public RestClient inventoryRestClient(RestClient.Builder builder) {
    return builder.baseUrl("https://inventory.internal").build();
  }
}
```

## 32.8 Set `proxyBeanMethods = false` on any `@Configuration` class whose `@Bean` methods never call one another.

> Why? The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/java/basic-concepts.html)
> explains that full mode generates "a CGLIB subclass" so that "cross-method
> references … get redirected to the container's lifecycle management".
> When no `@Bean` method calls another, that proxy buys nothing and costs
> class generation at every startup — lite mode has a "reduced memory
> footprint and faster startup". Be deliberate: in lite mode "a custom Java
> call to such a method will not get intercepted by the container … creating
> a new instance every time", so if your methods *do* call each other, leave
> proxying on and take the dependency as a method parameter instead.
> **Suggestion.**

```java
// bad — CGLIB proxy generated for a class that never needs it
@Configuration
public class MetricsConfiguration {

  @Bean
  public MeterRegistryCustomizer<MeterRegistry> commonTags() {
    return registry -> registry.config().commonTags("service", "checkout");
  }
}

// good
@Configuration(proxyBeanMethods = false)
public class MetricsConfiguration {

  @Bean
  public MeterRegistryCustomizer<MeterRegistry> commonTags() {
    return registry -> registry.config().commonTags("service", "checkout");
  }
}
```

## 32.9 Never mutate a singleton bean's state after initialization.

> Why? Singleton is the default scope, so one instance serves every
> concurrent request. The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html)
> guarantees safe publication of configuration set during initialization, but
> it is explicit about the rest: fields changed "after the bean creation
> phase and its subsequent initial publication … need to be declared as
> `volatile` or guarded by a common lock whenever accessed", and "any runtime
> state accumulated between initialization and destruction should be kept in
> thread-safe structures". A per-request field on a singleton is not a race
> you will find in testing — it is a race you will find in production, as one
> user seeing another user's data. **Suggestion.**

```java
// bad — `currentOrder` is shared by every concurrent request
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private Order currentOrder;

  public CheckoutService(PaymentGateway gateway) {
    this.gateway = gateway;
  }

  public Receipt checkout(Order order) {
    this.currentOrder = order;
    return gateway.charge(currentOrder.total());
  }
}

// good — request state lives on the stack; shared counters are thread-safe
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private final AtomicLong completed = new AtomicLong();

  public CheckoutService(PaymentGateway gateway) {
    this.gateway = gateway;
  }

  public Receipt checkout(Order order) {
    Receipt receipt = gateway.charge(order.total());
    completed.incrementAndGet();
    return receipt;
  }
}
```

## 32.10 Obtain a prototype-scoped collaborator through `ObjectProvider`, never by injecting it into a singleton.

> Why? Dependency injection happens once, at singleton creation. The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)
> covers this under singleton/prototype interaction: injecting a prototype
> into a singleton hands you exactly one instance for the singleton's entire
> lifetime, which is the opposite of what `prototype` means. Asking the
> provider each time is the fix that does not require a scoped proxy.
> **Suggestion.**

```java
// bad — one ReportBuilder is created at startup and reused forever, despite
// the prototype scope
@Service
public class ReportService {
  private final ReportBuilder builder;

  public ReportService(ReportBuilder builder) {
    this.builder = builder;
  }
}

// good — a fresh instance per call, as the scope promises
@Service
public class ReportService {
  private final ObjectProvider<ReportBuilder> builders;

  public ReportService(ObjectProvider<ReportBuilder> builders) {
    this.builders = builders;
  }

  public Report build(ReportRequest request) {
    return builders.getObject().build(request);
  }
}
```

## 32.11 Disambiguate multiple implementations with a custom qualifier annotation, not a string literal.

> Why? The
> [qualifiers reference](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html)
> shows that any annotation meta-annotated with `@Qualifier` becomes a
> qualifier of its own. That converts a class of runtime failure into a class
> of compile failure: `@Qualifier("stripeGatway")` compiles happily and dies
> at context refresh, while `@Stripe` will not compile if the annotation does
> not exist, and renaming it is a safe IDE refactor rather than a
> grep-and-pray. **Suggestion.**

```java
// bad — the typo is invisible until the context refreshes
public CheckoutService(@Qualifier("stripeGatway") PaymentGateway gateway) {
  this.gateway = gateway;
}

// good — a typed qualifier; a typo is a compile error
@Qualifier
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER, ElementType.FIELD})
public @interface Stripe {}

@Service
@Stripe
public class StripePaymentGateway implements PaymentGateway {}

@Service
public class CheckoutService {
  private final PaymentGateway gateway;

  public CheckoutService(@Stripe PaymentGateway gateway) {
    this.gateway = gateway;
  }
}
```

## 32.12 Use `@Primary` only when one implementation is genuinely the default; never to silence an ambiguity you have not thought about.

> Why? The
> [qualifiers reference](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html)
> frames `@Primary` as the tool for when "one primary … candidate can be
> determined" — it answers "which one should an unqualified injection point
> get?", not "make the startup error go away". Used as a silencer, it means
> every new injection point silently picks the primary, so the day you add a
> second caller that needed the *other* implementation, nothing tells you.
> When there is no natural default, qualify every injection point instead.
> **Suggestion.**

```java
// bad — @Primary added to fix a startup failure; the sandbox gateway is now
// the silent default for every future injection point
@Service
@Primary
public class SandboxPaymentGateway implements PaymentGateway {}

@Service
public class StripePaymentGateway implements PaymentGateway {}

// good — no default; every injection point states what it wants
@Service
@Sandbox
public class SandboxPaymentGateway implements PaymentGateway {}

@Service
@Stripe
public class StripePaymentGateway implements PaymentGateway {}

public CheckoutService(@Stripe PaymentGateway gateway) {
  this.gateway = gateway;
}
```

## 32.13 Break a circular dependency by extracting the shared concern; never by adding `@Lazy` or switching to setter injection.

> Why? Circular references have been rejected by default since Spring
> Boot 2.6 — the context refresh fails rather than resolving the cycle by
> half-constructing a bean. `@Lazy`, setter injection, and
> `spring.main.allow-circular-references=true` all restore the old behaviour
> of injecting a proxy or a not-yet-initialized object, which converts a
> loud startup failure into a `NullPointerException` or an infinite
> recursion at some later, less convenient moment. A cycle means the two
> classes share a responsibility neither owns; extract it into a third.
> **Violation for the cycle itself — an unbroken constructor cycle fails the
> application context refresh. Suggestion for the rest: `@Lazy`, setter
> injection, and `spring.main.allow-circular-references=true` all suppress
> that failure rather than remove the cycle, so nothing mechanical catches
> them.**

```java
// bad — A needs B, B needs A, "fixed" by deferring one side
@Service
public class OrderService {
  private final InvoiceService invoices;

  public OrderService(@Lazy InvoiceService invoices) {
    this.invoices = invoices;
  }
}

@Service
public class InvoiceService {
  private final OrderService orders;

  public InvoiceService(OrderService orders) {
    this.orders = orders;
  }
}

// good — the shared concern (turning an order into invoice lines) is its own
// bean, and the cycle disappears
@Service
public class OrderInvoiceMapper {
  public List<InvoiceLine> toLines(Order order) {
    return order.items().stream().map(InvoiceLine::from).toList();
  }
}

@Service
public class OrderService {
  private final OrderInvoiceMapper mapper;

  public OrderService(OrderInvoiceMapper mapper) {
    this.mapper = mapper;
  }
}

@Service
public class InvoiceService {
  private final OrderInvoiceMapper mapper;

  public InvoiceService(OrderInvoiceMapper mapper) {
    this.mapper = mapper;
  }
}
```

## 32.14 Gate optional wiring with `@ConditionalOnProperty`, and give the condition an explicit `matchIfMissing`.

> Why? The
> [`@ConditionalOnProperty`
> javadoc](https://docs.spring.io/spring-boot/api/java/org/springframework/boot/autoconfigure/condition/ConditionalOnProperty.html)
> defaults `matchIfMissing` to `false`, so a feature guarded by an absent
> property is *off*. That is the right default for a new feature and the
> wrong default for one you are retrofitting a kill switch onto — stating it
> explicitly means the reader does not have to remember which. A property
> condition also keeps the alternative out of the context entirely, unlike an
> `if` inside the bean, which still constructs the collaborators.
> **Suggestion.**

```java
// bad — the bean is always created and decides at call time; both code paths
// and both sets of dependencies are always live
@Service
public class NotificationService {
  private final SmsSender sms;

  public NotificationService(SmsSender sms) {
    this.sms = sms;
  }

  public void notify(Customer customer, String message) {
    if (Boolean.parseBoolean(System.getenv("SMS_ENABLED"))) {
      sms.send(customer.phone(), message);
    }
  }
}

// good
@Configuration(proxyBeanMethods = false)
public class NotificationConfiguration {

  @Bean
  @ConditionalOnProperty(prefix = "checkout.sms", name = "enabled", matchIfMissing = false)
  public SmsSender smsSender(SmsProperties properties) {
    return new TwilioSmsSender(properties.accountSid(), properties.authToken());
  }
}
```

## 32.15 Put `@ConditionalOnMissingBean` only on auto-configuration classes.

> Why? The
> [Spring Boot reference](https://docs.spring.io/spring-boot/3.4/reference/features/developing-auto-configuration.html)
> warns that bean conditions "are evaluated based on what has been processed
> so far", and therefore recommends "using only `@ConditionalOnBean` and
> `@ConditionalOnMissingBean` annotations on auto-configuration classes
> (since these are guaranteed to load after any user-defined bean definitions
> have been added)". On an ordinary `@Configuration` class the result depends
> on definition-registration order, which is not something you control — the
> same code can back off in one build and not in the next. **Suggestion.**

```java
// bad — ordinary @Configuration; whether this backs off depends on
// registration order
@Configuration(proxyBeanMethods = false)
public class ClockConfiguration {

  @Bean
  @ConditionalOnMissingBean
  public Clock clock() {
    return Clock.systemUTC();
  }
}

// good — listed in
// META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports,
// so it is guaranteed to be processed after user beans
@AutoConfiguration
public class ClockAutoConfiguration {

  @Bean
  @ConditionalOnMissingBean
  public Clock clock() {
    return Clock.systemUTC();
  }
}
```

## 32.16 Inject `List<T>` or `Map<String, T>` to consume every implementation of a strategy interface, and pin the order with `@Order` when it matters.

> Why? The
> [autowiring reference](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html)
> supports injecting all beans of a type as an array, `List`, `Set`, or
> `Map` keyed by bean name. This turns "add a new validator" into "add a new
> `@Component`" with no edit to the consumer — the open/closed principle for
> free. Be aware of the ordering contract it also documents: target beans
> "can implement the `org.springframework.core.Ordered` interface or use the
> `@Order` or standard `@Priority` annotation", otherwise "their order
> follows the registration order of the corresponding target bean
> definitions". Registration order is not a contract; if your pipeline
> depends on sequence, declare it. **Suggestion.**

```java
// bad — every new rule requires editing this class
@Service
public class OrderValidator {
  private final StockRule stock;
  private final CreditRule credit;
  private final FraudRule fraud;

  public OrderValidator(StockRule stock, CreditRule credit, FraudRule fraud) {
    this.stock = stock;
    this.credit = credit;
    this.fraud = fraud;
  }

  public List<Violation> validate(Order order) {
    return Stream.of(stock, credit, fraud).flatMap(r -> r.check(order).stream()).toList();
  }
}

// good — adding a @Component that implements ValidationRule is the whole
// change; @Order makes the sequence explicit
@Service
public class OrderValidator {
  private final List<ValidationRule> rules;

  public OrderValidator(List<ValidationRule> rules) {
    this.rules = List.copyOf(rules);
  }

  public List<Violation> validate(Order order) {
    return rules.stream().flatMap(rule -> rule.check(order).stream()).toList();
  }
}

@Component
@Order(10)
public class StockRule implements ValidationRule {}
```

## 32.17 Express a genuinely optional dependency with `ObjectProvider<T>`, not `@Autowired(required = false)` and not `@Nullable`.

> Why? An optional constructor parameter typed `T` is a `null` you have to
> remember to check at every use — exactly the situation
> [Chapter 25](25-nullability.md) exists to prevent.
> [`ObjectProvider`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/beans/factory/ObjectProvider.html)
> makes the optionality part of the type, and its
> `getIfAvailable(Supplier<T>)` and `ifAvailable(Consumer<T>)` methods give
> you a default or a no-op without a single null check. **Suggestion.**

```java
// bad — a null that every method body must remember to guard
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private final AuditLog audit;

  public CheckoutService(PaymentGateway gateway, @Autowired(required = false) AuditLog audit) {
    this.gateway = gateway;
    this.audit = audit;
  }

  public Receipt checkout(Order order) {
    Receipt receipt = gateway.charge(order.total());
    if (audit != null) {
      audit.record(receipt);
    }
    return receipt;
  }
}

// good — optionality is in the type and the absence case is a no-op
@Service
public class CheckoutService {
  private final PaymentGateway gateway;
  private final ObjectProvider<AuditLog> audit;

  public CheckoutService(PaymentGateway gateway, ObjectProvider<AuditLog> audit) {
    this.gateway = gateway;
    this.audit = audit;
  }

  public Receipt checkout(Order order) {
    Receipt receipt = gateway.charge(order.total());
    audit.ifAvailable(log -> log.record(receipt));
    return receipt;
  }
}
```

## 32.18 Never call `new` on a type that is a Spring bean.

> Why? A bean is a bean because it needs something the container provides —
> injected collaborators, a transaction proxy, a cache proxy, lifecycle
> callbacks, or metrics instrumentation. `new` gives you an object that has
> none of those. This is the single most common cause of "why is
> `@Transactional` doing nothing?" (see
> [Chapter 35](35-spring-data-and-transactions.md)) and of
> `NullPointerException` on a field that "is definitely injected".
> **Suggestion.**

```java
// bad — the new instance has no injected repository and no transaction proxy
@RestController
public class CheckoutController {

  @PostMapping("/checkout")
  public ReceiptResponse checkout(@RequestBody CheckoutRequest request) {
    CheckoutService service = new CheckoutService(null, null);
    return ReceiptResponse.from(service.checkout(request.toOrder()));
  }
}

// good
@RestController
public class CheckoutController {
  private final CheckoutService checkout;

  public CheckoutController(CheckoutService checkout) {
    this.checkout = checkout;
  }

  @PostMapping("/checkout")
  public ReceiptResponse checkout(@RequestBody CheckoutRequest request) {
    return ReceiptResponse.from(checkout.checkout(request.toOrder()));
  }
}
```

## 32.19 Never call `ApplicationContext.getBean` from application code.

> Why? This is the service-locator anti-pattern: the class's real
> dependencies vanish from its signature and reappear as string or class
> literals inside method bodies, so the compiler can no longer tell you what
> it needs and a test can no longer supply it without a full context. The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html)
> makes the same point about the `*Aware` interfaces generally: they couple
> your code to Spring. Reserve `getBean` for framework and infrastructure
> code that genuinely cannot know its collaborator's type at compile time.
> **Suggestion.**

```java
// bad — dependency is invisible, unverifiable, and resolved by string
@Service
public class CheckoutService implements ApplicationContextAware {
  private ApplicationContext context;

  @Override
  public void setApplicationContext(ApplicationContext context) {
    this.context = context;
  }

  public Receipt checkout(Order order) {
    PaymentGateway gateway = (PaymentGateway) context.getBean("stripeGateway");
    return gateway.charge(order.total());
  }
}

// good
@Service
public class CheckoutService {
  private final PaymentGateway gateway;

  public CheckoutService(@Stripe PaymentGateway gateway) {
    this.gateway = gateway;
  }

  public Receipt checkout(Order order) {
    return gateway.charge(order.total());
  }
}
```

## 32.20 Use `@PostConstruct` for initialization callbacks, not `InitializingBean`.

> Why? The
> [reference](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html)
> states the preference and the reason: the JSR-250 annotations "are
> generally considered best practice for receiving lifecycle callbacks in a
> modern Spring application. Using these annotations means that your beans
> are not coupled to Spring-specific interfaces", and "we recommend that you
> do not use the `InitializingBean` interface, because it unnecessarily
> couples the code to Spring." For a third-party type you cannot annotate,
> `@Bean(initMethod = "...")` is the equivalent. **Suggestion.**

```java
// bad — the class now implements a Spring interface and cannot be
// constructed and initialized outside the container without importing it
@Service
public class RuleCache implements InitializingBean {
  @Override
  public void afterPropertiesSet() {
    reload();
  }
}

// good — jakarta.annotation.PostConstruct, no Spring type in the signature
@Service
public class RuleCache {
  @PostConstruct
  void warmUp() {
    reload();
  }
}
```

## 32.21 Do no real work in a bean constructor — no I/O, no thread starts, no remote calls.

> Why? A constructor runs during context refresh, before the rest of the
> application exists. A failure there surfaces as a
> `BeanCreationException` wrapping your real cause several frames down, and
> a slow call there is added directly to startup time — which matters for
> liveness probes and for autoscaling. Worse, a thread started in a
> constructor can observe a partially constructed object. Put the work in
> `@PostConstruct` (runs after injection completes) or, if it must happen
> after the whole context is ready, in an `ApplicationRunner`.
> **Suggestion.**

```java
// bad — a network call and a thread start during context refresh
@Service
public class RuleCache {
  private final Map<String, Rule> rules;

  public RuleCache(RuleClient client) {
    this.rules = client.fetchAll();
    new Thread(this::refreshForever).start();
  }
}

// good — construction is cheap and total; work happens on a defined callback
@Service
public class RuleCache {
  private final RuleClient client;
  private final AtomicReference<Map<String, Rule>> rules =
      new AtomicReference<>(Map.of());

  public RuleCache(RuleClient client) {
    this.client = client;
  }

  @PostConstruct
  void loadInitialRules() {
    rules.set(client.fetchAll());
  }
}
```
