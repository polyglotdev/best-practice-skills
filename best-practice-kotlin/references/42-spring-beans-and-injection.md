<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 42. Spring: Beans & Injection in Kotlin

This is a **delta chapter**. Every rule about how a Spring application should
be wired — constructor injection over field injection, the most specific
stereotype, `@Bean` methods for third-party types, `proxyBeanMethods = false`,
never mutating a singleton, `ObjectProvider` for prototypes, typed qualifiers
over string literals, breaking cycles by extraction, never calling `new` on a
bean, never reaching for `getBean` — is
**`best-practice-java` Chapter 32, "Spring: Beans & Dependency Injection"**.
Read it first and apply it unchanged.

What follows is only what Kotlin changes. Some of it is a gift: the Java rule
"store the collaborator in a `final` field" stops being a rule at all, because
a `val` in the primary constructor *is* a final field, and there is no way to
write the broken version. Some of it is a trap the Java chapter cannot warn
you about: an annotation that lands on the wrong JVM element, a `$` the Kotlin
compiler eats before Spring ever sees it, a name the compiler mangles, and a
default argument that looks like it should participate in autowiring and does
not.

Rules draw on
[Spring Framework: Classes and Interfaces](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/classes-interfaces.html),
[Spring Framework: Annotations](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/annotations.html),
[Spring Framework: Bean Definition DSL](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/bean-definition-dsl.html),
and
[Spring Boot: Kotlin support](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html).

Three neighbouring topics are deferred. **Why the compiler plugins exist at
all**, and what `kotlin-spring` opens, is
[Chapter 41](41-spring-kotlin-setup.md). **Binding external configuration into
a bean** is [Chapter 43](43-spring-configuration-properties.md); §42.12 states
only the language-level `@Value` hazard. **Which JVM element an annotation
lands on**, and the full use-site target list, is
[Chapter 27](27-annotations-and-use-site-targets.md); §42.9 applies it to one
specific case.

**Tool alignment:** no ktlint or detekt rule understands Spring, so almost
every rule below is a **Suggestion**. Three have real enforcement. An unbroken
constructor cycle fails the application context refresh (§42.15). detekt's
`LateinitUsage` (`potential-bugs` ruleset) catches the `lateinit var` half of
§42.3 when it is enabled — it is inactive by default in detekt's shipped
configuration, so check `config/detekt/detekt.yml` before relying on it.
detekt's `LongParameterList` (`complexity` ruleset) backs §42.16 and *is*
active by default.

## 42.1 Declare every mandatory collaborator as a `val` parameter of the primary constructor.

> Why? In Java, "use constructor injection" and "make the field `final`" are
> two separate rules that a reviewer has to check separately —
> `best-practice-java` §32.1 spends a paragraph on why the second one matters.
> In Kotlin they collapse into one declaration: a `val` primary-constructor
> parameter *is* a private final field plus a getter, so the immutability the
> Java rule asks for is not a convention you maintain but a thing the compiler
> emits. There is no way to write the half-done version. This also means the
> dependency list is the class header — a reader sees every collaborator
> before the first brace. **Suggestion.**

```kotlin
// bad — a body property assigned in an init block: mutable for no reason,
// duplicated names, and the dependency list is no longer the class header
@Service
class CheckoutService(gateway: PaymentGateway, orders: OrderRepository) {
    private var gateway: PaymentGateway
    private var orders: OrderRepository

    init {
        this.gateway = gateway
        this.orders = orders
    }
}

// good
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
    private val orders: OrderRepository,
)
```

## 42.2 Do not write `@Autowired` on a Kotlin class's only constructor.

> Why? Spring's rule is that the annotation "is not necessary if the target
> bean defines only one constructor" (see `best-practice-java` §32.2). A
> Kotlin class written the way §42.1 requires has exactly one constructor by
> construction — you would have to go out of your way to add a secondary one —
> so `@Autowired` on it is always redundant. Leaving it in costs a framework
> import on a class that is otherwise plain Kotlin, and it misleads the next
> reader into hunting for the second constructor that must exist somewhere.
> Note the syntax tax if you do need it: an annotation on a primary
> constructor requires the `constructor` keyword, which is itself a signal
> that you are adding noise. **Suggestion.**

```kotlin
// bad — redundant, and it forces the `constructor` keyword back into the
// class header
@Service
class CheckoutService @Autowired constructor(
    private val gateway: PaymentGateway,
)

// good
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
)
```

## 42.3 Never inject into a field — in Kotlin the price is a `lateinit var` or a nullable type, and both discard a language guarantee.

> Why? Field injection is bad in Java for four reasons (`best-practice-java`
> §32.3). In Kotlin it costs a fifth, and the fifth is the expensive one. A
> field Spring populates after construction cannot be a `val`, and it cannot
> be non-null at construction — so you must write either `lateinit var`, which
> converts "this bean was not wired" from a startup failure into an
> `UninitializedPropertyAccessException` on some later request, or `Foo?`,
> which forces `?.` or `!!` at every single use of a dependency that is not
> actually optional. Both throw away exactly the guarantee
> [Chapter 6](06-null-safety.md) exists to protect. `lateinit` belongs where a
> framework genuinely assigns before first read and you have no constructor to
> use — a JUnit `@BeforeEach` field, not a Spring collaborator. **Suggestion —
> detekt's `LateinitUsage` rule catches the `lateinit var` form when
> enabled.**

```kotlin
// bad — five collaborators, none final, none visible at the constructor, and
// a failure mode that fires on a request rather than at startup
@Service
class CheckoutService {
    @Autowired private lateinit var gateway: PaymentGateway
    @Autowired private lateinit var orders: OrderRepository
    @Autowired private var audit: AuditLog? = null

    fun checkout(order: Order): Receipt {
        val receipt = gateway.charge(order.total)
        audit?.record(receipt)
        return receipt
    }
}

// good — `CheckoutService(gateway, orders)` works in a plain unit test, and
// `gateway` can never be null or unassigned
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
    private val orders: OrderRepository,
) {
    fun checkout(order: Order): Receipt = gateway.charge(order.total)
}
```

## 42.4 Express "this dependency may be absent" with a nullable type, not with `@Autowired(required = false)`.

> Why? Spring reads Kotlin's nullability directly. The
> [Spring Framework annotations reference](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/annotations.html)
> gives the rule for `@Bean` functions — for `@Bean fun play(toy: Toy, car: Car?)`,
> "A bean of type `Toy` **must** be registered" while "a bean of type `Car`
> **may or may not** exist" — and then adds that "this behavior also applies
> to autowired constructor parameters." So the type *is* the `required`
> attribute, and writing both means one of them is redundant and the other is
> a lie waiting to happen. The Java workaround of `@Autowired(required = false)`
> on a non-null Kotlin type is worse than redundant: it tells Spring the
> parameter is optional while the Kotlin type says it cannot be null, so an
> absent bean becomes a `NullPointerException` from Kotlin's own intrinsic
> check rather than a clear `NoSuchBeanDefinitionException`. **Suggestion.**

```kotlin
// bad — the annotation says "optional", the type says "non-null"; when the
// bean is missing you get an intrinsic null-check NPE, not a Spring error
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
    @Autowired(required = false) private val audit: AuditLog,
)

// good — one source of truth, and the call site is forced to handle absence
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
    private val audit: AuditLog?,
) {
    fun checkout(order: Order): Receipt {
        val receipt = gateway.charge(order.total)
        audit?.record(receipt)
        return receipt
    }
}
```

## 42.5 Use `ObjectProvider<T>` when you need a *deferred or repeated* lookup, not merely an optional one.

> Why? §42.4 covers optionality; `ObjectProvider` covers everything else the
> nullable type cannot express. A prototype-scoped collaborator injected once
> into a singleton is one instance for the singleton's whole life
> (`best-practice-java` §32.10) — the nullable type does not help, because the
> problem is *when* the lookup happens, not whether the bean exists. Likewise a
> zero-implementations strategy set: a non-null `List<Rule>` parameter is
> required, so a module with no rules registered fails to start, while
> `ObjectProvider<Rule>` gives you `orderedStream()` over however many there
> are. Reach for it for those reasons, and keep the nullable parameter for the
> plain "this bean may not be configured" case, because
> `provider.getIfAvailable()` is a `T?` you have to unwrap anyway.
> **Suggestion.**

```kotlin
// bad — one ReportBuilder is created at startup and reused forever, despite
// the prototype scope
@Service
class ReportService(
    private val builder: ReportBuilder,
) {
    fun build(request: ReportRequest): Report = builder.build(request)
}

// good — a fresh instance per call, as the scope promises
@Service
class ReportService(
    private val builders: ObjectProvider<ReportBuilder>,
) {
    fun build(request: ReportRequest): Report = builders.getObject().build(request)
}

// good — zero registered rules is a legitimate state, not a startup failure
@Service
class OrderValidator(
    private val rules: ObjectProvider<ValidationRule>,
) {
    fun validate(order: Order): List<Violation> =
        rules.orderedStream().toList().flatMap { it.check(order) }
}
```

## 42.6 Write each `@Bean` function as a single expression with an explicit declared return type.

> Why? The expression body is the idiomatic Kotlin form and it removes the
> `return` that added nothing (see [Chapter 8](08-functions.md)). The explicit
> return type is not decoration: Spring resolves the bean's type from the
> method's declared return type, and with an inferred type that declared type
> is whatever the compiler happened to conclude from the body. Change
> `mutableMapOf()` to `ConcurrentHashMap()` inside the function and you have
> silently changed the bean's type, which changes which injection points
> match. Declaring the API type also keeps the implementation swappable
> without touching a single consumer — the same reason
> [Chapter 20](20-collections-and-sequences.md) wants read-only interfaces at
> boundaries. **Suggestion.**

```kotlin
// bad — the bean's type is `ConcurrentHashMap<String, Rule>`, so a consumer
// injecting `Map<String, Rule>` may or may not match, depending on what else
// is registered; and swapping the implementation is a breaking change
@Configuration(proxyBeanMethods = false)
class RuleConfiguration {

    @Bean
    fun ruleCache() = ConcurrentHashMap<String, Rule>()

    @Bean
    fun clock(): Clock {
        return Clock.systemUTC()
    }
}

// good
@Configuration(proxyBeanMethods = false)
class RuleConfiguration {

    @Bean
    fun ruleCache(): MutableMap<String, Rule> = ConcurrentHashMap()

    @Bean
    fun clock(): Clock = Clock.systemUTC()
}
```

## 42.7 Declare `@Configuration` classes at the top level or as `nested` classes — never as `inner` classes.

> Why? The
> [Spring Framework reference](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/classes-interfaces.html)
> states the constraint and its cause: "You can declare configuration classes
> as top level or nested but not inner, since the latter requires a reference
> to the outer class." Kotlin nested classes are static by default and
> `inner` is the opt-in — the reverse of Java, where a nested class is inner
> unless you write `static`. So the mistake a Java developer makes here is
> spelled with an extra keyword, which at least makes it visible; the mistake
> a Kotlin developer makes is copying a Java example that had `static` and
> "translating" it to `inner`. An `inner` `@Configuration` class cannot be
> instantiated by the container, because there is no outer instance to
> construct it against. **Suggestion.**

```kotlin
// bad — `inner` needs an enclosing instance the container cannot supply
@SpringBootApplication
class BillingApplication {

    @Configuration(proxyBeanMethods = false)
    inner class ClockConfiguration {

        @Bean
        fun clock(): Clock = Clock.systemUTC()
    }
}

// good — nested is static in Kotlin, which is what the container needs
@SpringBootApplication
class BillingApplication {

    @Configuration(proxyBeanMethods = false)
    class ClockConfiguration {

        @Bean
        fun clock(): Clock = Clock.systemUTC()
    }
}
```

## 42.8 Keep implementation *classes* `internal` if you like, but never mark a `@Bean` function or any framework callback `internal`.

> Why? `internal` is a Kotlin-only lever with no Java equivalent, and it is
> genuinely useful here: a public interface plus an `internal` implementation
> class gives you a module boundary the compiler enforces, and Spring wires it
> anyway, because — per the
> [Java interop reference](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
> — "the names of public members of `internal` classes aren't mangled and
> remain callable from Java." Members are the other story: "The Kotlin compiler
> mangles the names of `internal` members in bytecode." A `@Bean` function's
> bean name defaults to the method name Spring reads out of the class file, so
> an `internal fun clock()` registers under a mangled name like
> `clock$billing_main` — and every `@Qualifier("clock")`, every
> `getBean("clock")`, and every `@ConditionalOnMissingBean` that matched by
> name stops matching. The same applies to `@EventListener`, `@PostConstruct`,
> and `@Scheduled` methods that anything resolves by name. **Suggestion.**

```kotlin
// bad — the registered bean is not called "clock", and no compiler error says
// so; the failure is a NoSuchBeanDefinitionException at refresh
@Configuration(proxyBeanMethods = false)
class ClockConfiguration {

    @Bean
    internal fun clock(): Clock = Clock.systemUTC()
}

// good — public @Bean function, and an internal implementation class, which
// is where `internal` actually buys you something
@Configuration(proxyBeanMethods = false)
class ClockConfiguration {

    @Bean
    fun clock(): Clock = Clock.systemUTC()
}

interface InvoiceNumberGenerator {
    fun next(): String
}

@Service
internal class SequentialInvoiceNumbers(
    private val counters: CounterRepository,
) : InvoiceNumberGenerator {
    override fun next(): String = "INV-${counters.increment("invoice")}"
}
```

## 42.9 Put `@Qualifier` where the container reads it — on the constructor parameter, never `@field:Qualifier`.

> Why? Autowiring a constructor resolves each argument from the annotations on
> the *constructor parameter*.
> `org.springframework.beans.factory.annotation.Qualifier` declares
> `@Target({FIELD, METHOD, PARAMETER, TYPE, ANNOTATION_TYPE})` — note the
> absence of any Kotlin `property` target — so on a primary-constructor `val`
> a bare `@Qualifier` resolves to the parameter (and the field), which works.
> Writing `@field:Qualifier` explicitly, however, moves it off the parameter
> entirely, and the qualifier silently stops applying: Spring picks by type,
> finds two candidates, and fails at refresh with an ambiguity error that
> points at a line where the qualifier is plainly visible. This is
> [Chapter 27](27-annotations-and-use-site-targets.md) §27.5 applied to one
> annotation. Prefer a typed qualifier annotation over a string literal for
> the reasons in `best-practice-java` §32.11. **Suggestion.**

```kotlin
// bad — @field: takes the qualifier off the constructor parameter, so
// autowiring never sees it
@Service
class CheckoutService(
    @field:Qualifier("stripeGateway") private val gateway: PaymentGateway,
)

// good — a typed qualifier, on the parameter where resolution reads it
@Qualifier
@Retention(AnnotationRetention.RUNTIME)
@Target(
    AnnotationTarget.CLASS,
    AnnotationTarget.FUNCTION,
    AnnotationTarget.VALUE_PARAMETER,
    AnnotationTarget.FIELD,
)
annotation class Stripe

@Service
@Stripe
class StripePaymentGateway(
    private val http: RestClient,
) : PaymentGateway {
    override fun charge(amount: Money): Receipt = TODO()
}

@Service
class CheckoutService(
    @Stripe private val gateway: PaymentGateway,
)
```

## 42.10 Inject `List<T>` or `Map<String, T>` to consume every implementation of a strategy interface, and keep the read-only type.

> Why? The mechanism is the same as Java's (`best-practice-java` §32.16) —
> Spring injects every bean of the element type, and a `Map` is keyed by bean
> name — but Kotlin makes one thing better and one thing sharper. Better:
> `List<T>` is `kotlin.collections.List`, which is read-only, so the
> defensive `List.copyOf` the Java rule needs is already implied by the type.
> Sharper: a non-null `List<T>` parameter is *required*, so a build with zero
> implementations of `T` fails at context refresh rather than quietly
> injecting an empty list — which is usually what you want, and is worth
> knowing before it happens. Where zero is legitimate, use `ObjectProvider`
> (§42.5). Never declare the parameter `MutableList<T>`; you do not own that
> list. **Suggestion.**

```kotlin
// bad — every new rule requires editing this class, and the mutable type
// invites someone to add to a list the container owns
@Service
class OrderValidator(
    private val rules: MutableList<ValidationRule>,
) {
    fun validate(order: Order): List<Violation> = rules.flatMap { it.check(order) }
}

// good — adding a @Component that implements ValidationRule is the whole
// change; @Order makes the sequence explicit rather than registration-dependent
@Service
class OrderValidator(
    private val rules: List<ValidationRule>,
) {
    fun validate(order: Order): List<Violation> = rules.flatMap { it.check(order) }
}

interface ValidationRule {
    fun check(order: Order): List<Violation>
}

@Component
@Order(10)
class StockRule(
    private val inventory: InventoryClient,
) : ValidationRule {
    override fun check(order: Order): List<Violation> =
        order.items.filterNot(inventory::isInStock).map(Violation::outOfStock)
}
```

## 42.11 Use the functional bean DSL when registration is conditional or generated — not as a blanket replacement for annotations.

> Why? `beans { }` is a Kotlin-only option with no Java equivalent, and it is
> the right tool for exactly one thing: registration that is itself logic. The
> [reference](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/bean-definition-dsl.html)
> makes both the pitch and the limit. The pitch: "This mechanism is very
> efficient, as it does not require any reflection or CGLIB proxies," and
> "This DSL is programmatic, meaning it allows custom registration logic of
> beans through an `if` expression, a `for` loop, or any other Kotlin
> constructs" — so registering one adapter per configured tenant becomes a
> loop instead of a hand-written class per tenant. The limit: "Spring Boot is
> based on JavaConfig and does not yet provide specific support for functional
> bean definition, but you can experimentally use functional bean definitions
> through Spring Boot's `ApplicationContextInitializer` support." Read
> *experimentally* literally. Beans registered this way are outside
> `@Configuration` processing, which means auto-configuration ordering,
> `@ConditionalOnMissingBean` back-off, and test-slice bean overriding all
> behave differently. Keep the bulk of the application on annotations.
> **Suggestion.**

```kotlin
// bad — the whole application moved to the DSL for style reasons, giving up
// auto-configuration back-off and test-slice overriding for nothing
val allBeans = beans {
    bean<CheckoutService>()
    bean<StripePaymentGateway>()
    bean<JdbcOrderRepository>()
}

// good — annotations for the application, the DSL for the one thing
// annotations cannot express: one bean per configured tenant
fun tenantBeans(tenants: List<TenantId>): BeanDefinitionDsl = beans {
    for (tenant in tenants) {
        bean(name = "gateway-$tenant") {
            TenantScopedGateway(tenant, ref())
        }
    }
    profile("sandbox") {
        bean<SandboxPaymentGateway>()
    }
}

@SpringBootApplication
class BillingApplication

fun main(args: Array<String>) {
    runApplication<BillingApplication>(*args) {
        addInitializers(tenantBeans(TenantId.configured()))
    }
}
```

## 42.12 Escape the `$` in every `@Value` placeholder — and reach for `@ConfigurationProperties` instead.

> Why? `$` opens a string template in Kotlin, so `@Value("${billing.base-url}")`
> is not a Spring placeholder at all — the compiler tries to interpolate a
> `billing` symbol and the file does not compile, or worse, compiles against
> something that happens to exist. The fix is `\$`, or a `$$`-prefixed literal
> under Kotlin 2.2's stable multi-dollar interpolation. But the deeper point
> is that the escape is a smell: an annotation argument containing an escaped
> sigil is a string the compiler cannot check, describing configuration the
> type system does not know about. `best-practice-java` §33.1 explains why
> `@ConfigurationProperties` wins; in Kotlin it wins by more, because a
> properties `data class` gives you a typed, immutable, `equals`-comparable
> configuration object for free. See
> [Chapter 43](43-spring-configuration-properties.md). **Suggestion.**

```kotlin
// bad — does not compile: Kotlin reads ${billing.base-url} as a template
@Service
class PaymentService(
    @Value("${billing.base-url}") private val baseUrl: String,
)

// bad — compiles, works, and still scatters the configuration surface across
// N untyped, unvalidated, undocumented string lookups
@Service
class PaymentService(
    @Value("\${billing.base-url}") private val baseUrl: String,
    @Value("\${billing.timeout:5s}") private val timeout: Duration,
)

// good — one type is the schema, and the service takes it as a dependency
@ConfigurationProperties("billing")
data class BillingProperties(
    val baseUrl: URI,
    val timeout: Duration = Duration.ofSeconds(5),
)

@Service
class PaymentService(
    private val properties: BillingProperties,
)
```

## 42.13 A Kotlin `object` is not a Spring bean.

> Why? An `object` declaration is a JVM class with a private constructor and a
> static `INSTANCE` field, initialised by the class loader. Putting `@Service`
> on it does nothing useful: component scanning wants to construct the class,
> and even where the container manages to register something, the instance
> your Kotlin code reaches by writing `TaxRates.forRegion(...)` is the static
> one, which has no injected collaborators, no transaction proxy, and no
> lifecycle callbacks. This is `best-practice-java` §32.18 — "never call `new`
> on a type that is a Spring bean" — in the form Kotlin makes available, and
> it is harder to spot, because there is no `new` to see. An `object` is
> exactly right for stateless, dependency-free constants and pure functions;
> the moment it needs a collaborator, it needs to be a class.
> **Suggestion.**

```kotlin
// bad — @Service on an object; `repository` is never injected and every call
// site silently reaches the un-managed static instance
@Service
object TaxCalculator {

    @Autowired
    lateinit var rates: TaxRateRepository

    fun taxFor(order: Order): Money = rates.rateFor(order.region) * order.net
}

// good — a class with its dependency in the constructor
@Service
class TaxCalculator(
    private val rates: TaxRateRepository,
) {
    fun taxFor(order: Order): Money = rates.rateFor(order.region) * order.net
}

// good — an object is right when there is nothing to inject
object TaxRounding {
    fun toMinorUnits(amount: BigDecimal): Long =
        amount.setScale(2, RoundingMode.HALF_EVEN).movePointRight(2).toLong()
}
```

## 42.14 A Kotlin default argument on a bean constructor is not a Spring default.

> Why? Two mechanisms that look alike do different things at different times.
> `class Foo(private val clock: Clock = Clock.systemUTC())` says "a *Kotlin
> caller* that omits `clock` gets `Clock.systemUTC()`." It does not say "if no
> `Clock` bean exists, use this." When Spring autowires the constructor it
> supplies every parameter, so a registered `Clock` bean always wins and the
> default never runs; and when no `Clock` bean exists, resolution fails
> against a non-null parameter type rather than falling back. The result is a
> default that is dead in production and live in unit tests — which is
> precisely the configuration most likely to make a test pass while the
> deployed behaviour differs. If a default belongs to the *application*,
> register it as a `@Bean` so one thing decides. Note the one place Kotlin
> defaults genuinely do participate: `@ConfigurationProperties` constructor
> binding, which goes through `KFunction.callBy` — see
> [Chapter 43](43-spring-configuration-properties.md) §43.4. **Suggestion.**

```kotlin
// bad — the default is unreachable when a Clock bean exists and irrelevant
// when it does not; the test and the deployment exercise different code
@Service
class InvoiceService(
    private val invoices: InvoiceRepository,
    private val clock: Clock = Clock.systemUTC(),
)

// good — one place decides what the default clock is, and it is the same
// place in every environment
@Configuration(proxyBeanMethods = false)
class TimeConfiguration {

    @Bean
    @ConditionalOnMissingBean
    fun clock(): Clock = Clock.systemUTC()
}

@Service
class InvoiceService(
    private val invoices: InvoiceRepository,
    private val clock: Clock,
)
```

## 42.15 Break a circular dependency by extracting the shared concern — `@Lazy` is worse in Kotlin, not better.

> Why? Spring Boot has rejected circular references by default since 2.6, so
> the cycle itself already fails the context refresh — that part is
> `best-practice-java` §32.13 and does not change. What changes is the
> temptation. `@Lazy` injects a proxy of the declared type, and a proxy is
> non-null, so in Kotlin it satisfies the type system perfectly: the property
> is a `val`, it is not nullable, nothing looks wrong. All the language's
> safety signals go quiet while the actual failure moves to the first method
> call on a bean that may still be mid-construction. A cycle means two classes
> share a responsibility neither owns; extract it into a third.
> **Violation for the cycle itself — an unbroken constructor cycle fails the
> application context refresh. Suggestion for the rest: `@Lazy` and
> `spring.main.allow-circular-references=true` suppress that failure rather
> than remove the cycle.**

```kotlin
// bad — a non-null val holding an uninitialised proxy; the type system says
// this is fine right up until the first call
@Service
class OrderService(
    @Lazy private val invoices: InvoiceService,
)

@Service
class InvoiceService(
    private val orders: OrderService,
)

// good — the shared concern becomes its own bean and the cycle disappears
@Service
class OrderInvoiceMapper {
    fun toLines(order: Order): List<InvoiceLine> = order.items.map(InvoiceLine::from)
}

@Service
class OrderService(
    private val mapper: OrderInvoiceMapper,
)

@Service
class InvoiceService(
    private val mapper: OrderInvoiceMapper,
)
```

## 42.16 Treat a long constructor parameter list as a design defect, and do not let named arguments talk you out of noticing.

> Why? Spring's own guidance is that "a large number of constructor arguments
> is a bad code smell, implying that the class likely has too many
> responsibilities" (`best-practice-java` §32.5). Kotlin blunts the symptom
> without touching the disease: named arguments make an eight-argument call
> site readable, trailing commas make adding a ninth a one-line diff, and the
> class header formats beautifully at any length. So the discomfort that
> normally prompts the refactor never arrives, and the class keeps
> accumulating. Use the count itself as the signal — detekt's
> `LongParameterList` does it for you, and unlike `LateinitUsage` it is active
> by default: `allowedConstructorParameters` defaults to 6, so the eight-argument
> class below already reports. Check one option before relying on it, though —
> `ignoreDataClasses` defaults to `true`, which exempts a properties `data class`
> ([Chapter 43](43-spring-configuration-properties.md)) from the count. Then
> extract the collaborator that owns the cohesive subset. **Suggestion —
> detekt's `LongParameterList` (`complexity` ruleset) covers it.**

```kotlin
// bad — eight collaborators, so the class does eight things; Kotlin's syntax
// makes that comfortable rather than obvious
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
    private val orders: OrderRepository,
    private val inventory: InventoryClient,
    private val tax: TaxCalculator,
    private val shipping: ShippingQuoter,
    private val email: EmailSender,
    private val sms: SmsSender,
    private val audit: AuditLog,
)

// good — pricing and notification are extracted behind their own interfaces
@Service
class CheckoutService(
    private val gateway: PaymentGateway,
    private val orders: OrderRepository,
    private val pricer: OrderPricer,
    private val notifier: CustomerNotifier,
)
```
