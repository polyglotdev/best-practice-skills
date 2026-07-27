<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 43. Spring: Configuration Properties

This is a **delta chapter**. The case for typed configuration over scattered
`@Value` lookups, the rules about nesting, secrets, profiles, precedence
order, `Duration` over `timeoutMs`, never reading `System.getenv`, never
injecting `Environment`, and never squatting in the `spring.*` namespace are
all **`best-practice-java` Chapter 33, "Spring: Configuration & Properties"**.
Read it first and apply it unchanged.

Kotlin changes three things, and each one has a failure mode you cannot see in
the source. First, the shape gets better: constructor binding into a `data
class` of `val`s is the immutability the Java chapter has to argue for, and
Kotlin default arguments genuinely participate in binding — which is not
obvious, and not documented in so many words, so §43.4 explains the mechanism
rather than asserting the outcome. Second, one property has two readers that
look at opposite JVM elements: the binder reads constructor *parameter*
annotations while the validator walks *fields*, so `@DefaultValue` and
`@NotBlank` want opposite use-site targets on the same property, and the
target that is right for one silently disables the other. Third, two Kotlin
types that look like obvious wins — `kotlin.time.Duration` and `value class` —
do not bind.

Sources are
[Spring Boot: Externalized Configuration](https://docs.spring.io/spring-boot/3.5/reference/features/external-config.html),
[Constructor binding](https://docs.spring.io/spring-boot/3.5/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.constructor-binding),
[the Configuration Metadata annotation processor](https://docs.spring.io/spring-boot/3.5/specification/configuration-metadata/annotation-processor.html),
and
[Spring Boot: Kotlin support](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html).

Two neighbouring topics are deferred. **How the properties object is injected
into the beans that use it** is [Chapter 42](42-spring-beans-and-injection.md),
whose §42.12 explains why `@Value` loses to this chapter in Kotlin by more
than it does in Java. **Why an annotation lands where it lands**, and the full
use-site target list, is
[Chapter 27](27-annotations-and-use-site-targets.md); §43.6 and §43.7 apply it
to the binder and the validator respectively.

**Tool alignment:** nothing in ktlint or detekt understands
`@ConfigurationProperties`, so most rules below are **Suggestion**. The
exception is the one that matters most: once a properties type carries
`@Validated` and jakarta constraints, an invalid value **fails the application
context refresh**, so the deployment pipeline catches it rather than the first
customer. That is real enforcement, and it is the main reason to prefer typed
properties at all.

## 43.1 Bind configuration into a `data class` whose components are `val`.

> Why? Spring Boot's
> [constructor binding](https://docs.spring.io/spring-boot/3.5/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.constructor-binding)
> triggers on "the presence of a single parameterized constructor", which a
> Kotlin `data class` has by construction. That gets you the immutable
> configuration object `best-practice-java` §33.2 argues for, with no
> boilerplate to argue about — plus `equals`, `hashCode`, and a real
> `toString` for free, which makes configuration trivially assertable in a
> test (§43.17) and legible in a startup log. A JavaBean-style class with
> `var` properties also binds, through setters, and is wrong for the same
> reason it is wrong in Java: configuration does not change after startup, and
> a mutable singleton invites a request thread to change it. **Suggestion.**

```kotlin
// bad — JavaBean binding: mutable, nullable-by-necessity, and constructible
// in a state that is valid to the compiler and useless at runtime
@ConfigurationProperties("payment")
class PaymentProperties {
    var baseUrl: URI? = null
    var timeout: Duration? = null
    var retryAttempts: Int = 0
}

// good
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val timeout: Duration,
    val retryAttempts: Int,
)
```

## 43.2 Register the type with `@ConfigurationPropertiesScan` or `@EnableConfigurationProperties` — never with `@Component`.

> Why? Both mechanisms route the type through the binder;
> `@Component` routes it through component scanning instead, and the Spring
> Boot reference is explicit that "You cannot use constructor binding with
> beans that are created by the regular Spring mechanisms (for example
> `@Component` beans, beans created by using `@Bean` methods or beans loaded
> by using `@Import`)". In Java the mistake half-works, because a
> JavaBean-style properties class still binds through its setters. In Kotlin
> it does not work at all and the error is baffling: component scanning tries
> to *autowire* the constructor, so `val baseUrl: URI` becomes "no qualifying
> bean of type `java.net.URI`" and the failure names a type nobody was trying
> to inject. Put `@ConfigurationPropertiesScan` on the application class once
> and stop thinking about it. **Violation — for a Kotlin data class whose
> components are not themselves beans, the application context fails to
> refresh.**

```kotlin
// bad — Spring tries to find a URI bean and a Duration bean
@Component
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val timeout: Duration,
)

// good — one annotation on the application class covers every properties type
@SpringBootApplication
@ConfigurationPropertiesScan
class BillingApplication

fun main(args: Array<String>) {
    runApplication<BillingApplication>(*args)
}

@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val timeout: Duration,
)
```

## 43.3 Omit `@ConstructorBinding` on a data class — and never write an empty primary constructor, which is the documented opt-*out*.

> Why? `@ConstructorBinding` exists to pick between several constructors, and
> the reference says so: "If your class has multiple constructors, the
> `@ConstructorBinding` annotation can be used to specify which constructor to
> use for constructor binding." A `data class` has exactly one primary
> constructor, so the annotation is noise. Note also that since Spring Boot 3
> it declares `@Target({CONSTRUCTOR, ANNOTATION_TYPE})`, so the Java-2.x habit
> of writing it on the type is now a compile error in Kotlin — you have to
> spell out `data class X @ConstructorBinding constructor(...)`, which is
> itself a hint that you are adding noise. The genuinely Kotlin-specific half
> of this rule is the reverse direction, which the reference also spells out:
> "Kotlin developers can use an empty primary constructor to opt-out of
> constructor binding." So `class PaymentProperties() { var baseUrl: URI? = null }`
> is not a stylistic variant of §43.1 — it is a documented instruction to
> Spring to bind through setters instead, and it is very easy to write by
> accident when converting a Java class. **Suggestion.**

```kotlin
// bad — redundant on a single-constructor data class, and it drags the
// `constructor` keyword back into the class header
@ConfigurationProperties("payment")
data class PaymentProperties @ConstructorBinding constructor(val baseUrl: URI)

// bad — the empty primary constructor silently switches off constructor
// binding; everything must now be a nullable `var`
@ConfigurationProperties("payment")
class PaymentProperties() {
    var baseUrl: URI? = null
    var timeout: Duration? = null
}

// good
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val timeout: Duration,
)

// good — the annotation earns its place only where there is a real choice
@ConfigurationProperties("payment")
data class PaymentProperties @ConstructorBinding constructor(
    val baseUrl: URI,
    val timeout: Duration,
) {
    constructor(baseUrl: URI) : this(baseUrl, Duration.ofSeconds(5))
}
```

## 43.4 Express defaults as Kotlin default arguments, and know why they work.

> Why? This is the one place in Spring where a Kotlin default argument
> genuinely participates — the opposite of the bean-constructor case in
> [Chapter 42](42-spring-beans-and-injection.md) §42.14 — and it is worth
> knowing the mechanism, because it explains every limit in §43.5 and §43.12.
> When a parameter has no bound value, `ValueObjectBinder` passes `null` for
> it, and `BeanUtils.instantiateClass` then takes its Kotlin path, which skips
> any parameter that `isOptional` and whose argument is `null` before calling
> `KFunction.callBy`. `callBy` applies the Kotlin default. Two consequences
> follow. The default must be a *Kotlin* default on the primary constructor —
> a `@DefaultValue("...")` **carrying a value** and a Kotlin default are two
> different mechanisms, and putting both on one parameter means the annotation
> always wins and the Kotlin default is dead code. (An *empty*
> `@DefaultValue`, which §43.5 needs, is a different instruction entirely: it
> means "construct this type from its own defaults", not "use this literal".)
> And the whole thing requires `kotlin-reflect` on the classpath
> ([Chapter 41](41-spring-kotlin-setup.md) §41.8); without it Spring takes the
> plain Java path, passes `null` into a non-null parameter, and Kotlin's own
> intrinsic check throws. **Suggestion.**

```kotlin
// bad — the default is stated three times, in three placeholder strings, and
// none of them is visible to the metadata processor
@Service
class PaymentService(
    @Value("\${payment.timeout:5s}") private val timeout: Duration,
    @Value("\${payment.retry-attempts:3}") private val retryAttempts: Int,
)

// bad — two default mechanisms on one parameter; the annotation wins and the
// Kotlin default is dead code
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    @param:DefaultValue("10s") val timeout: Duration = Duration.ofSeconds(5),
)

// good — the default lives beside the property it defaults, and is the same
// value the constructor uses when a test builds the object by hand
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val timeout: Duration = Duration.ofSeconds(5),
    val retryAttempts: Int = 3,
)
```

## 43.5 A nested type with no bound properties at all binds to `null`, however many defaults its components have — say `@param:DefaultValue` when you want the object itself defaulted.

> Why? §43.4's mechanism runs *per parameter*; whether the nested object gets
> created at all is decided one level up, and there the rule is different.
> `ValueObjectBinder` returns the object only if at least one of its
> properties bound; otherwise it returns `null`. The Spring Boot reference
> describes exactly this: "if no properties are bound to `Security`, the
> `MyProperties` instance will contain a `null` value for `security`. To make
> it contain a non-null instance of `Security` even when no properties are
> bound to it … use an empty `@DefaultValue` annotation." So a nested
> `data class` whose every component has a Kotlin default still arrives as
> `null` when the whole block is absent from the YAML — the most confusing
> possible outcome, because the defaults are right there in the source. An
> empty `@param:DefaultValue` tells the binder to construct the nested type
> anyway, at which point the Kotlin defaults do apply. **Suggestion.**

```yaml
# application.yaml — note there is no `payment.retry` block at all
payment:
  base-url: https://payments.internal
```

```kotlin
// bad — `retry` is null at runtime despite every component having a default,
// so the first read is a NullPointerException from a non-null type
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val retry: Retry,
) {
    data class Retry(
        val attempts: Int = 3,
        val backoff: Duration = Duration.ofMillis(200),
    )
}

// good — the empty @param:DefaultValue constructs the nested object, and its
// own Kotlin defaults then fill it in
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    @param:DefaultValue val retry: Retry,
) {
    data class Retry(
        val attempts: Int = 3,
        val backoff: Duration = Duration.ofMillis(200),
    )
}
```

## 43.6 Write `@DefaultValue`, `@Name`, `@DurationUnit`, and `@DataSizeUnit` with the `@param:` use-site target.

> Why? The binder reads these off the *constructor parameter*: for a Kotlin
> type, `ValueObjectBinder` builds each `ConstructorParameter` from
> `KParameter.getAnnotations()`, which is the `param` site and nothing else.
> An annotation you push onto the field with `@field:` is therefore invisible
> to binding — the property silently loses its default, its unit, or its
> alias, and no error mentions the annotation. `@DefaultValue` declares
> `@Target({ElementType.PARAMETER})`, so it cannot land anywhere else and the
> bare form is safe; `@Name`, `@DurationUnit`, and `@DataSizeUnit` all target
> `FIELD` *and* `PARAMETER`, so under Kotlin 2.4's default-target rule a bare
> annotation lands on both, which works — until someone "tidies" it to
> `@field:`. Spring Boot's own Kotlin sample writes
> `@param:DefaultValue("USER") val roles: List<String>`; follow it, and be
> explicit. **Suggestion.**

```kotlin
// bad — @field: takes every one of these off the parameter the binder reads,
// so the default, the unit, and the alias all silently stop applying
@ConfigurationProperties("payment")
data class PaymentProperties(
    @field:Name("endpoint") val baseUrl: URI,
    @field:DurationUnit(ChronoUnit.SECONDS) val circuitBreakerReset: Duration,
    @field:DataSizeUnit(DataUnit.MEGABYTES) val maxUpload: DataSize,
)

// good
@ConfigurationProperties("payment")
data class PaymentProperties(
    @param:Name("endpoint") val baseUrl: URI,
    @param:DurationUnit(ChronoUnit.SECONDS)
    @param:DefaultValue("30")
    val circuitBreakerReset: Duration,
    @param:DataSizeUnit(DataUnit.MEGABYTES)
    @param:DefaultValue("10")
    val maxUpload: DataSize,
)
```

## 43.7 Write every jakarta validation constraint with the `@field:` use-site target — the opposite of §43.6.

> Why? Validation does not inspect constructor parameters: Spring Boot's
> `ConfigurationPropertiesJsr303Validator` delegates to a
> `LocalValidatorFactoryBean`, which validates the already-constructed object
> by walking its fields and getters. So the constraint has to reach the
> *field*, and §43.6's `@param:` is exactly the wrong target for it — which is
> the trap, because §43.6 has just told you to write `@param:` on everything
> the binder reads. An explicit `@param:NotBlank` compiles, is plainly visible
> in review, starts the context cleanly, and validates nothing.
>
> Be precise about the bare form, because it is not the failure case here.
> Under Kotlin 2.4's now-stable defaulting rules a bare constraint on a
> primary-constructor `val` reaches the field on its own: the
> [Kotlin annotations reference](https://kotlinlang.org/docs/annotations.html#defaults-when-no-use-site-targets-are-specified)
> uses Jakarta's `@Email` as its worked example and says a bare `@Email` on a
> constructor property "is now equivalent to `@param:Email @field:Email`",
> because the property is declared in the primary constructor and has a
> generated backing field. Write `@field:` anyway, for three reasons: it makes
> the asymmetry with §43.6 deliberate rather than accidental; it is what
> Spring's own Kotlin documentation asks for — "If you use bean validation on
> classes with properties or a primary constructor with parameters, you may
> need to use annotation use-site targets, such as `@field:NotNull`,
> `@get:Size(min=5, max=15)`"; and it stays correct as the property changes
> shape, where the bare form does not. Move the property into the class body
> and the bare constraint resolves to `field` alone; give it a custom getter
> and none of `param`, `property`, or `field` is applicable, which the same
> reference calls invalid — so a bare `@Size` on a computed property is a
> compile error and `@get:` is the only site that works. See
> [Chapter 27](27-annotations-and-use-site-targets.md) §27.7. **Suggestion —
> and the reason it needs to be a rule is that the `@param:` form has no
> symptom.**

```kotlin
// bad — @param: puts every constraint on the constructor parameter, which the
// validator never walks; a blank API key and a retry count of -50 both start
// cleanly. Carrying §43.6's `@param:` habit onto constraints is the way in.
@ConfigurationProperties("payment")
@Validated
data class PaymentProperties(
    @param:NotNull val baseUrl: URI,
    @param:NotBlank val apiKey: String,
    @param:Min(0) @param:Max(10) val retryAttempts: Int = 3,
)

// good — constraints on the field, binder annotations on the parameter
@ConfigurationProperties("payment")
@Validated
data class PaymentProperties(
    @field:NotNull val baseUrl: URI,
    @field:NotBlank val apiKey: String,
    @field:Min(0) @field:Max(10) val retryAttempts: Int = 3,
) {
    // a computed property has no backing field, so target the getter instead
    @get:Size(max = 200)
    val callbackUrl: String get() = "$baseUrl/callback"
}
```

## 43.8 Annotate the properties type `@Validated`, and cascade into nested types with `@field:Valid`.

> Why? Spring Boot "attempts to validate `@ConfigurationProperties` classes
> whenever they are annotated with Spring's `@Validated` annotation", and the
> failure happens at context refresh — so a bad value is caught by the
> deployment pipeline rather than by the first request that reads it. That is
> the strongest enforcement available anywhere in this chapter, and it costs
> one annotation. The caveat everyone forgets is that validation does not
> recurse by default: "to cascade validation to nested properties the
> associated field must be annotated with `@Valid`". In Kotlin write it
> `@field:Valid`, for exactly the reason in §43.7 — `jakarta.validation.Valid`
> targets `PARAMETER` as well as `FIELD`, so an explicit `@param:Valid` puts it
> on the one site the validator never walks and the nested block goes
> unvalidated with no error anywhere.
> **Violation — the application context fails to refresh on an invalid
> value.**

```kotlin
// bad — @Validated present but the nested block is never validated, so a
// blank apiKey deploys successfully
@ConfigurationProperties("payment")
@Validated
data class PaymentProperties(
    @field:NotNull val baseUrl: URI,
    val credentials: Credentials,
) {
    data class Credentials(
        @field:NotBlank val apiKey: String,
        @field:NotBlank val webhookSecret: String,
    )
}

// good
@ConfigurationProperties("payment")
@Validated
data class PaymentProperties(
    @field:NotNull val baseUrl: URI,
    @field:Valid val credentials: Credentials,
) {
    data class Credentials(
        @field:NotBlank val apiKey: String,
        @field:NotBlank val webhookSecret: String,
    )
}
```

## 43.9 Declare a required property with a non-null type; use a nullable type only when absence is a genuine state.

> Why? Kotlin lets the type carry the requirement, which Java's records
> cannot. A non-null property with no default fails binding when the key is
> absent, at context refresh, naming the property — the deployment stops. A
> nullable property binds to `null` and pushes the question to every read
> site. The distinction is not stylistic: "no API key configured" is a
> deployment error, while "no optional webhook configured" is a state the code
> must handle. Reach for the nullable type only for the second, and never as a
> way to make a startup failure go away — that converts one loud failure into
> an unbounded number of quiet `?.` calls. Note the interaction with §43.5:
> the Spring Boot reference points out that making a nested block default to a
> constructed instance "will require the `username` and `password` parameters
> … to be declared as nullable as they do not have default values", so give
> nested components Kotlin defaults rather than making them nullable.
> **Suggestion.**

```kotlin
// bad — everything nullable, so nothing fails at startup and every consumer
// pays for it forever
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI?,
    val apiKey: String?,
    val webhookUrl: URI?,
)

@Service
class PaymentService(private val properties: PaymentProperties) {
    fun charge(order: Order): Receipt {
        val url = properties.baseUrl ?: error("payment.base-url is not configured")
        return post(url, properties.apiKey.orEmpty(), order)
    }
}

// good — required is required; optional is optional, and says so
@ConfigurationProperties("payment")
@Validated
data class PaymentProperties(
    @field:NotNull val baseUrl: URI,
    @field:NotBlank val apiKey: String,
    val webhookUrl: URI? = null,
)
```

## 43.10 Group related keys into nested `data class`es rather than flattening the prefix.

> Why? This is `best-practice-java` §33.12, and it survives the translation
> intact — a flat type with fourteen components is a fourteen-argument
> constructor, and passing the whole object to a collaborator that needs three
> of them hands out the API key alongside the retry policy. Kotlin adds one
> reason and one convenience. The reason: nested `data class`es are the units
> you can validate independently with `@field:Valid` (§43.8) and construct
> independently in a test. The convenience: nesting them *inside* the
> properties class keeps the namespace tidy — and Kotlin's nested classes are
> static by default, so unlike Java there is no `static` keyword to forget and
> no `inner` trap unless you go looking for one. **Suggestion.**

```kotlin
// bad — flat namespace; every consumer receives every key
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val apiKey: String,
    val webhookSecret: String,
    val connectTimeout: Duration,
    val readTimeout: Duration,
    val retryAttempts: Int,
    val retryBackoff: Duration,
)

// good
@ConfigurationProperties("payment")
@Validated
data class PaymentProperties(
    @field:NotNull val baseUrl: URI,
    @field:Valid val credentials: Credentials,
    @param:DefaultValue @field:Valid val retry: Retry,
    @param:DefaultValue @field:Valid val timeouts: Timeouts,
) {
    data class Credentials(
        @field:NotBlank val apiKey: String,
        @field:NotBlank val webhookSecret: String,
    )

    data class Retry(
        @field:Min(0) val attempts: Int = 3,
        val backoff: Duration = Duration.ofMillis(200),
    )

    data class Timeouts(
        val connect: Duration = Duration.ofSeconds(2),
        val read: Duration = Duration.ofSeconds(10),
    )
}
```

## 43.11 Bind durations to `java.time.Duration`, not `kotlin.time.Duration`.

> Why? Spring Boot's `ApplicationConversionService` registers
> `StringToDurationConverter`, `NumberToDurationConverter`, and their inverses
> for `java.time.Duration` — and for nothing else. `kotlin.time.Duration` is a
> different type with no registered converter, so binding `5s` to it fails at
> context refresh with a conversion error. The `java.time` type is also what
> `@DurationUnit`, `@DurationFormat`, and the readable `10s` / `PT10S` / `500ms`
> forms are defined against, so using it keeps the whole documented feature
> set. If your domain code genuinely wants `kotlin.time.Duration`, convert at
> the edge with `toKotlinDuration()` rather than pushing the Kotlin type into
> the binding boundary — the same edge-conversion discipline
> [Chapter 30](30-dates-and-times.md) applies elsewhere. **Violation — the
> application context fails to refresh.**

```kotlin
// bad — no converter exists for kotlin.time.Duration; `payment.timeout: 5s`
// fails to convert at startup
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val timeout: kotlin.time.Duration = 5.seconds,
)

// good — bind the java.time type; convert at the one edge that wants the
// Kotlin one. toKotlinDuration() has been stable since Kotlin 1.6.
@ConfigurationProperties("payment")
data class PaymentProperties(
    @field:NotNull val baseUrl: URI,
    val timeout: java.time.Duration = java.time.Duration.ofSeconds(5),
)

@Service
class PaymentService(
    private val properties: PaymentProperties,
) {
    suspend fun charge(order: Order): Receipt =
        withTimeout(properties.timeout.toKotlinDuration()) { post(order) }
}
```

## 43.12 Do not use a Kotlin `value class` as the type of a configuration property that has a default.

> Why? It is the obvious idea — wrap the tenant id or the API key in a
> `@JvmInline value class` so it cannot be confused with any other `String` —
> and Spring Boot has
> [documented it as unsupported](https://github.com/spring-projects/spring-boot/issues/41693).
> The combination fails at binding time: a `value class` is erased to its
> underlying type at the JVM boundary, so the binder's `null`-for-unbound
> convention (§43.4) collides with an inline primitive that cannot be `null`,
> and the result is a `NullPointerException` in generated conversion code with
> a stack trace that names none of your classes. Spring Boot triaged the issue
> as documentation rather than as a fix, which means "do not do this" is the
> supported answer. Bind the plain type and construct the value class in a
> derived property, where the wrapper still buys you type safety everywhere it
> matters. See [Chapter 12](12-value-classes.md). **Violation — binding fails
> at context refresh.**

```kotlin
// bad — documented as unsupported; fails with an NPE inside generated
// conversion code when `payment.entity-id` is absent
@JvmInline
value class EntityId(val value: Int)

@ConfigurationProperties("payment")
data class PaymentProperties(
    val entityId: EntityId = EntityId(1),
)

// good — bind the underlying type under the key you want, and wrap it in a
// derived property so every consumer still sees the value class
@JvmInline
value class EntityId(val value: Int)

@ConfigurationProperties("payment")
data class PaymentProperties(
    @param:Name("entity-id") @param:DefaultValue("1") val rawEntityId: Int,
) {
    val entityId: EntityId get() = EntityId(rawEntityId)
}
```

## 43.13 Declare any `@ConfigurationPropertiesBinding` converter as a `@JvmStatic` function in a companion object.

> Why? When you do need a custom type at the binding boundary — a domain
> `Money`, a `kotlin.time.Duration` after all, a compact enum spelling — the
> mechanism is a `Converter` bean qualified with
> `@ConfigurationPropertiesBinding`. Its javadoc states the constraint:
> "`@Bean` methods that declare a `@ConfigurationPropertiesBinding` bean
> should be `static` to ensure that 'bean is not eligible for getting
> processed by all BeanPostProcessors' warnings are not produced." Kotlin has
> no `static`, so the only way to satisfy that is `@JvmStatic` on a function
> inside a `companion object` — a mechanical detail with no Java analogue, and
> one that is easy to skip because the non-static version appears to work
> while filling the log with warnings and pulling the converter into a
> bean-creation ordering it should not be part of. The same
> `@JvmStatic`-in-companion shape is what any `static @Bean` needs in Kotlin,
> including `BeanFactoryPostProcessor` beans. **Suggestion.**

```kotlin
// bad — an instance @Bean method for a converter that must be static
@Configuration(proxyBeanMethods = false)
class BindingConfiguration {

    @Bean
    @ConfigurationPropertiesBinding
    fun moneyConverter(): Converter<String, Money> = Converter { Money.parse(it) }
}

// good
@Configuration(proxyBeanMethods = false)
class BindingConfiguration {

    companion object {

        @Bean
        @JvmStatic
        @ConfigurationPropertiesBinding
        fun moneyConverter(): Converter<String, Money> = Converter { Money.parse(it) }
    }
}
```

## 43.14 Generate configuration metadata with `kapt`, not `annotationProcessor` — and do not wait for KSP.

> Why? `spring-boot-configuration-processor` reads `@ConfigurationProperties`
> types at compile time and emits
> `META-INF/spring-configuration-metadata.json`, which is what gives an IDE
> completion, type checking, and documentation-on-hover inside
> `application.yaml`. It is a Java annotation processor, and Gradle's
> `annotationProcessor` configuration only sees the Java compile task — so on
> a Kotlin project it runs against no sources and silently produces nothing.
> The build is green, the jar contains no metadata, and the only symptom is
> that `application.yaml` stays an untyped text file. The route that works is
> `kapt`, which generates Java stubs from the Kotlin sources and feeds those
> to the processor. KSP is not an option: Spring Boot's
> [tracking issue](https://github.com/spring-projects/spring-boot/issues/28046)
> is open, targeted at a 4.x milestone, and labelled pending design work.
> **Suggestion.**

```kotlin
// bad — build.gradle.kts; the processor runs, sees no Kotlin, emits nothing
dependencies {
    annotationProcessor("org.springframework.boot:spring-boot-configuration-processor")
}

// good
plugins {
    kotlin("kapt") version "2.4.10"
}

dependencies {
    kapt("org.springframework.boot:spring-boot-configuration-processor")
}
```

## 43.15 Type collection and map properties as the read-only Kotlin interfaces.

> Why? `best-practice-java` §33.17 has to add a defensive `List.copyOf` in a
> compact constructor to stop a properties object handing out its own mutable
> internals. Kotlin removes the work: `List<String>` and `Map<String, Rule>`
> are the read-only interfaces, so declaring them is the defence, and the
> binder is happy to populate them. Declaring `MutableList<String>` instead
> gives a singleton bean — shared by every concurrent request — a collection
> any consumer can mutate, and the mutation neither survives a restart nor
> matches the deployed configuration. The `Map` case carries the extra rule
> from `best-practice-java` §33.19: bind to a map only for a genuinely open
> key set, and keep the *value* type a validated nested `data class` so only
> the keys are open. See [Chapter 25](25-immutability.md). **Suggestion.**

```kotlin
// bad — a mutable list on a singleton, and a Map<String, String> that
// defeats validation and metadata alike
@ConfigurationProperties("tenants")
data class TenantProperties(
    val allowedCurrencies: MutableList<String> = mutableListOf(),
    val settings: MutableMap<String, String> = mutableMapOf(),
)

// good — read-only in, read-only out; open key set, closed value type.
// @field:Valid on a Map cascades into its values.
@ConfigurationProperties("tenants")
@Validated
data class TenantProperties(
    val allowedCurrencies: List<String> = emptyList(),
    @field:Valid val settings: Map<String, TenantSettings> = emptyMap(),
) {
    data class TenantSettings(
        @field:NotNull val callbackUrl: URI,
        val timeout: Duration = Duration.ofSeconds(5),
        @field:Min(1) val maxConcurrency: Int = 4,
    )
}
```

## 43.16 Write keys in canonical kebab-case, and use `@param:Name` when a Kotlin keyword or an `is` prefix gets in the way.

> Why? Relaxed binding derives the key from the constructor parameter name, so
> a Kotlin `val retryAttempts: Int` binds from `payment.retry-attempts` — and
> `best-practice-java` §33.6 explains why that canonical kebab-case form is
> the one to write everywhere, including inside `${...}` placeholders. Two
> collisions are Kotlin-specific. First, Kotlin's reserved-word set is not
> Java's: `object`, `fun`, `val`, `var`, `is`, `in`, `when`, and `typealias`
> are all keywords here, so a configuration key named after one of them cannot
> be a parameter name without backticks. `@param:Name` is the documented
> escape — the reference calls it out for "a reserved keyword in the name of a
> property" — and it reads far better than a backticked identifier propagating
> through every call site. Second, a Kotlin property named `isEnabled` is a
> parameter named `isEnabled`, so the key is `is-enabled`, not `enabled` —
> which surprises everyone at least once. **Suggestion.**

```yaml
# bad — three spellings of one namespace, and a key that assumes the `is`
# prefix is stripped
payment:
  baseUrl: https://payments.internal
  retry_attempts: 3
  enabled: true

# good
payment:
  base-url: https://payments.internal
  retry-attempts: 3
  is-enabled: true
  object: invoice
```

```kotlin
// bad — a backticked keyword compiles, but every consumer now writes
// properties.`object`, forever
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val retryAttempts: Int = 3,
    val isEnabled: Boolean = true,
    val `object`: String = "invoice",
)

// good — the key stays readable and the Kotlin name stays legal
@ConfigurationProperties("payment")
data class PaymentProperties(
    val baseUrl: URI,
    val retryAttempts: Int = 3,
    val isEnabled: Boolean = true,
    @param:Name("object") val objectKind: String = "invoice",
)
```

## 43.17 Test binding and validation with `ApplicationContextRunner`, and let the data class do the asserting.

> Why? The rule is `best-practice-java` §33.18 — `ApplicationContextRunner`
> builds a throwaway context containing only the configuration under test, in
> milliseconds, and its AssertJ integration lets you assert on a *failed*
> refresh, which `@SpringBootTest` cannot express because a failed refresh
> fails the test. What Kotlin adds is that the assertions get shorter: a
> properties `data class` has a structural `equals`, so the whole bound object
> can be compared to an expected instance in one line, and a mismatch prints a
> generated `toString` that names the differing component. That matters most
> for the two rules in this chapter with no other symptom: a constraint on the
> wrong use-site target (§43.7) and a nested block that binds to `null`
> (§43.5). Write one test per properties type that asserts the all-defaults
> case and one that asserts a rejection. **Suggestion.**

```kotlin
// bad — boots the whole application to check one default, and cannot assert
// that a bad value is rejected at all
@SpringBootTest
class PaymentPropertiesTest(
    @Autowired private val properties: PaymentProperties,
) {
    @Test
    fun `default retry attempts`() {
        assertThat(properties.retry.attempts).isEqualTo(3)
    }
}

// good
class PaymentPropertiesTest {

    private val runner = ApplicationContextRunner()
        .withUserConfiguration(TestConfiguration::class.java)

    @Test
    fun `applies every default when only the required keys are present`() {
        runner
            .withPropertyValues(
                "payment.base-url=https://payments.test",
                "payment.credentials.api-key=k",
                "payment.credentials.webhook-secret=s",
            )
            .run { context ->
                assertThat(context.getBean(PaymentProperties::class.java))
                    .isEqualTo(
                        PaymentProperties(
                            baseUrl = URI.create("https://payments.test"),
                            credentials = PaymentProperties.Credentials("k", "s"),
                        ),
                    )
            }
    }

    @Test
    fun `rejects a blank api key`() {
        runner
            .withPropertyValues(
                "payment.base-url=https://payments.test",
                "payment.credentials.api-key=",
                "payment.credentials.webhook-secret=s",
            )
            .run { context -> assertThat(context).hasFailed() }
    }

    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(PaymentProperties::class)
    class TestConfiguration
}
```
