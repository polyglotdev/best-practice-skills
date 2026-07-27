<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 41. Spring: Kotlin Setup & Compiler Plugins

Spring works by wrapping your classes. `@Configuration` classes get a CGLIB
subclass so that one `@Bean` method calling another returns the container's
instance rather than a fresh object. `@Transactional`, `@Async`, and
`@Cacheable` beans get a proxy that opens a transaction, hands off to an
executor, or checks a cache before delegating. JPA instantiates entities
reflectively through a no-argument constructor and lazy-loads associations
through a generated subclass. Every one of those mechanisms assumes the Java
default: classes are open, and a no-arg constructor is one keystroke away.

Kotlin's defaults are the opposite. Classes and members are `final` unless
declared `open`, and a class with a primary constructor has no no-arg
constructor at all. That mismatch is not a style problem — it is a startup
crash, and it is the reason a Kotlin Spring project needs compiler plugins
that a Java one does not. This chapter is about those plugins and the rest of
the build configuration that only exists because the language is Kotlin.

This is a **delta chapter**. Everything that is the same in both languages —
starter selection, auto-configuration, profiles, actuator, packaging, and the
static-analysis setup — lives in **`best-practice-java` Chapters 32 to 38**
and is not repeated here. Read those first and apply them unchanged. What
follows is only what the Kotlin language forces you to add. It draws from
[Spring Boot: Kotlin support](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html),
[Spring Framework: Spring Projects in Kotlin](https://docs.spring.io/spring-framework/reference/languages/kotlin/spring-projects-in.html),
the
[Kotlin all-open compiler plugin](https://kotlinlang.org/docs/all-open-plugin.html)
and
[no-arg compiler plugin](https://kotlinlang.org/docs/no-arg-plugin.html)
documentation, and
[Kotlin Gradle plugin configuration](https://kotlinlang.org/docs/gradle-configure-project.html).

Three neighbouring topics are deferred. **Bean declaration and injection
style** — constructor `val`s, `@Bean` functions, the functional bean DSL — is
[Chapter 42](42-spring-beans-and-injection.md). **Configuration property
binding**, including the `kapt` requirement for metadata generation, is
[Chapter 43](43-spring-configuration-properties.md). The **language-level
meaning of platform types and nullability annotations**, which §41.9 turns
into a build flag, is [Chapter 6](06-null-safety.md) and
[Chapter 28](28-java-interop.md).

**Tool alignment:** no ktlint or detekt rule knows what Spring is, so nothing
in this chapter is caught by static analysis. The enforcement here is
different and stronger: a missing `kotlin-spring` plugin **fails the
application context refresh**, a missing `kotlin-jpa` plugin **fails entity
instantiation**, and a JVM-target mismatch **fails the Gradle build** under
the Kotlin Gradle plugin's default validation mode. Rules with one of those
consequences are marked **Violation**; the rest are **Suggestion**.

## 41.1 Apply the `kotlin-spring` compiler plugin instead of writing `open` on Spring-annotated classes by hand.

> Why? The
> [Spring Boot Kotlin reference](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html)
> states the problem and the fix in one sentence: "Since Kotlin classes are
> final by default, you are likely to want to configure the `kotlin-spring`
> plugin in order to automatically open Spring-annotated classes so that they
> can be proxied." Doing it by hand fails in exactly the way hand-maintained
> invariants always fail — someone adds a `@Service`, forgets the keyword, and
> the build is green until the context refreshes in CI. It also means every
> `@Bean` method needs its own `open`, because the CGLIB subclass overrides
> the *methods*, not just the class. The plugin
> ["automatically opens classes and their member functions"](https://docs.spring.io/spring-framework/reference/languages/kotlin/spring-projects-in.html)
> for the annotated types, and
> [start.spring.io enables it by default](https://start.spring.io/#!language=kotlin&type=gradle-project).
> **Violation — without it the application context fails to refresh with
> "Cannot subclass final class".**

```kotlin
// bad — hand-maintained `open`; the day someone adds a @Service without it,
// the failure is a context-refresh crash, not a compile error
@Configuration
class BillingConfiguration {

    @Bean
    fun invoiceNumberGenerator(): InvoiceNumberGenerator = SequentialInvoiceNumbers()
}

// bad — half-remembered: the class is open, the @Bean method is not, so CGLIB
// still cannot intercept cross-method calls
@Configuration
open class BillingConfiguration {

    @Bean
    fun invoiceNumberGenerator(): InvoiceNumberGenerator = SequentialInvoiceNumbers()
}

// good — build.gradle.kts; the plugin opens the class and its members
plugins {
    kotlin("jvm") version "2.4.10"
    kotlin("plugin.spring") version "2.4.10"
    id("org.springframework.boot") version "3.5.16"
    id("io.spring.dependency-management") version "1.1.7"
}

// good — and the source stays plain Kotlin
@Configuration
class BillingConfiguration {

    @Bean
    fun invoiceNumberGenerator(): InvoiceNumberGenerator = SequentialInvoiceNumbers()
}
```

## 41.2 Know the exact annotation set the `kotlin-spring` preset opens, and extend it with `allOpen { annotation(...) }` rather than adding `open` for anything outside it.

> Why? `kotlin-spring` is
> [a preconfigured version of `kotlin-allopen`](https://kotlinlang.org/docs/all-open-plugin.html)
> with a fixed list: `@Component`, `@Async`, `@Transactional`, `@Cacheable`,
> and `@SpringBootTest`, plus everything meta-annotated with `@Component` —
> which covers `@Configuration`, `@Controller`, `@RestController`,
> `@Service`, and `@Repository`. Anything else is *not* opened, and the list
> is easy to over-assume: `@Entity`, `@Aspect`, `@Scheduled` on a class,
> `@Validated` on a class, and your own meta-annotations are all outside it.
> When you need one of those opened, add it to the `allOpen` extension so the
> rule lives in one reviewable place instead of as a keyword scattered across
> class declarations. **Suggestion.**

```kotlin
// bad — `open` added by hand because a class annotated only with @Validated
// needs a proxy; nothing records why, and the next such class will be missed
@Validated
open class QuotaChecker {

    open fun check(@Min(1) quantity: Int) { /* ... */ }
}

// good — build.gradle.kts; the plugin knows the rule, the source does not
// need to
plugins {
    kotlin("plugin.spring") version "2.4.10"
}

allOpen {
    annotation("org.springframework.validation.annotation.Validated")
    annotation("com.example.billing.ProxiedForMetrics")
}

// good
@Validated
class QuotaChecker {

    fun check(@Min(1) quantity: Int) { /* ... */ }
}
```

## 41.3 Apply `kotlin-jpa` for entities — and add the JPA annotations to `allOpen` as well, because the no-arg plugin opens nothing.

> Why? These are two independent problems with two independent plugins, and
> fixing one hides the other until runtime. The
> [Hibernate User Guide §3.4.3](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#entity-pojo-constructor)
> requires a no-argument constructor, which a Kotlin primary constructor does
> not provide;
> [`kotlin-jpa`](https://kotlinlang.org/docs/no-arg-plugin.html) generates a
> *synthetic* one for `@Entity`, `@Embeddable`, and `@MappedSuperclass` —
> synthetic meaning "it can't be directly called from Java or Kotlin, but it
> can be called using reflection", which is exactly what a persistence
> provider needs. Separately,
> [Hibernate User Guide §3.4.2](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#entity-pojo-final)
> prefers non-final classes because lazy loading is implemented with a
> generated subclass — and `kotlin-jpa` does not open anything, while
> `kotlin-spring` does not cover `@Entity`. So a Kotlin entity with a lazy
> `@ManyToOne` needs *both* plugins configured. **Violation — a missing
> `kotlin-jpa` fails entity instantiation; a final entity fails Hibernate's
> lazy-proxy generation.**

```kotlin
// bad — only kotlin-jpa applied. Instantiation works, and then the first lazy
// association blows up because Hibernate cannot subclass a final entity.
plugins {
    kotlin("plugin.jpa") version "2.4.10"
}

// good — no-arg for the constructor, all-open for the proxy
plugins {
    kotlin("plugin.spring") version "2.4.10"
    kotlin("plugin.jpa") version "2.4.10"
}

allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}

// good — the entity itself stays plain Kotlin
@Entity
class Invoice(

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    var customer: Customer? = null,

    var totalMinorUnits: Long = 0L,
)
```

## 41.4 Do not make a JPA entity a `data class` — the no-arg plugin fixes the constructor, not the semantics.

> Why? `kotlin-jpa` makes a `data class` *instantiable* by Hibernate, which is
> precisely why this mistake survives review: it compiles, it starts, and it
> is wrong. A `data class` derives `equals`/`hashCode` from every component,
> including the generated `id`. Put a transient entity in a `Set`, flush, and
> its `id` changes from `null` to a database value — so its `hashCode` changes
> while it is in the set, and it is no longer findable. Derived `toString`
> touches every property, which triggers lazy loading from wherever the log
> statement happens to be, sometimes outside a session. And `copy()` hands out
> a detached twin that shares the same primary key. Use a plain class, and
> write `equals`/`hashCode` against a business key or a client-assigned id.
> See [Chapter 11](11-data-classes.md) for the general rule this specialises
> and [Chapter 23](23-equality-and-ordering.md) for the mutable-key hazard.
> **Suggestion.**

```kotlin
// bad — hashCode changes on flush, so the entity is lost from any Set it was
// added to before persisting; copy() produces a detached duplicate key
@Entity
data class Invoice(
    @Id @GeneratedValue val id: Long? = null,
    val reference: String,
    @OneToMany(mappedBy = "invoice") val lines: List<InvoiceLine> = emptyList(),
)

// good — identity is the business key, which never changes
@Entity
class Invoice(
    @Column(nullable = false, unique = true)
    val reference: String,
) {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null
        private set

    @OneToMany(mappedBy = "invoice", fetch = FetchType.LAZY)
    var lines: MutableList<InvoiceLine> = mutableListOf()
        protected set

    override fun equals(other: Any?): Boolean =
        this === other || (other is Invoice && reference == other.reference)

    override fun hashCode(): Int = reference.hashCode()

    override fun toString(): String = "Invoice(reference=$reference)"
}
```

## 41.5 Set `proxyBeanMethods = false` on a `@Configuration` class whose `@Bean` functions never call one another, and let the class stay effectively final.

> Why? All-open is a workaround for a requirement, not a licence to stop
> thinking about whether the requirement applies. Spring's own advice is that
> you can
> [avoid CGLIB proxies entirely with `@Configuration(proxyBeanMethods = false)`](https://docs.spring.io/spring-framework/reference/languages/kotlin/spring-projects-in.html),
> which removes the class-generation cost at every startup — see
> **`best-practice-java` §32.8** for the framework-level rationale, including
> when full proxy mode is genuinely needed. In Kotlin this also removes a
> whole class of
> confusion, because the class no longer *needs* to be open, so a reader who
> sees `final` in the decompiled output has learned something true rather than
> hit a bug. Be deliberate: if your `@Bean` functions do call each other, leave
> proxying on and take the dependency as a function parameter instead.
> **Suggestion.**

```kotlin
// bad — full proxy mode for a class that never needs it; the all-open plugin
// silently opens the class and both functions to support a proxy nothing uses
@Configuration
class ClientConfiguration {

    @Bean
    fun restClient(builder: RestClient.Builder): RestClient =
        builder.baseUrl("https://payments.internal").build()

    @Bean
    fun clock(): Clock = Clock.systemUTC()
}

// good
@Configuration(proxyBeanMethods = false)
class ClientConfiguration {

    @Bean
    fun restClient(builder: RestClient.Builder): RestClient =
        builder.baseUrl("https://payments.internal").build()

    @Bean
    fun clock(): Clock = Clock.systemUTC()
}
```

## 41.6 Do not assume that implementing an interface removes the `open` requirement — Spring Boot proxies the target class by default.

> Why? This is the folk remedy that does not work. The Java-era advice was
> "extract an interface and Spring will use a JDK dynamic proxy, which does
> not need to subclass anything." Spring Boot's `AopAutoConfiguration` sets
> `proxyTargetClass` to `true` unless you say otherwise: the javadoc states
> "The `proxyTargetClass` attribute will be `true`, by default, but can be
> overridden by specifying `spring.aop.proxy-target-class=false`." So a
> `@Transactional` class that implements a perfectly good interface is still
> proxied by subclassing, and still has to be open. Extract interfaces because
> they are the right design (see
> [Chapter 10](10-classes-and-interfaces.md)), not as a way to dodge the
> plugin. **Suggestion.**

```kotlin
// bad — "it implements an interface, so it doesn't need to be open" is false
// under Spring Boot's default AOP configuration
interface InvoiceService {
    fun issue(order: Order): Invoice
}

@Service
@Transactional
class DefaultInvoiceService(
    private val invoices: InvoiceRepository,
) : InvoiceService {
    override fun issue(order: Order): Invoice = invoices.save(Invoice(order.reference))
}

// good — apply kotlin-spring and keep the interface for design reasons.
// If you genuinely want JDK proxies, say so explicitly in configuration:
//   spring.aop.proxy-target-class=false
// and understand that every proxied bean must then be injected by its
// interface type, never by its implementation type.
```

## 41.7 Put `jackson-module-kotlin` on the classpath for any Kotlin type that crosses a JSON boundary.

> Why? Jackson databind constructs objects through a no-arg constructor plus
> setters, or through a creator whose parameter names it can read. A Kotlin
> `data class` has neither: no no-arg constructor, and Java-level parameter
> names only if `-parameters` was passed. Without the module, deserialising
> into a `data class` fails at runtime with a Jackson databind exception
> reporting that no suitable creator exists — a 500 on the first POST, not a
> compile error. The module reads the Kotlin metadata instead: it finds the
> primary constructor, recovers parameter names, honours default arguments,
> and enforces non-null types by failing rather than storing a `null` behind
> Kotlin's back. Spring Boot needs no configuration for it: "Jackson's Kotlin
> module is required for serializing / deserializing JSON data in Kotlin. It
> is automatically registered when found on the classpath"
> ([Spring Boot Kotlin reference](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html)).
> **Violation — deserialisation into a Kotlin class fails at runtime without
> it.**

```kotlin
// bad — build.gradle.kts; @RequestBody into a data class fails at runtime
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.jetbrains.kotlin:kotlin-reflect")
}

// good — version is managed by the Spring Boot dependency management plugin
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    implementation("org.jetbrains.kotlin:kotlin-reflect")
}

// good — with the module present this round-trips, and a missing `amount`
// in the request body is a 400, not a silently-null non-null property
data class ChargeRequest(
    val reference: String,
    val amountMinorUnits: Long,
    val description: String = "",
)
```

## 41.8 Keep `kotlin-reflect` on the classpath and never exclude it to trim the jar.

> Why? The
> [Spring Boot Kotlin reference](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html)
> is unambiguous: "To use Kotlin, `org.jetbrains.kotlin:kotlin-stdlib` and
> `org.jetbrains.kotlin:kotlin-reflect` must be present on the classpath."
> It is not optional infrastructure. Spring's `BeanUtils.instantiateClass`
> only takes its Kotlin path when `kotlin-reflect` is present, and that path
> is what makes `KFunction.callBy` apply Kotlin default arguments — which is
> what makes default values work in `@ConfigurationProperties` binding
> ([Chapter 43](43-spring-configuration-properties.md)) and in the bean
> definition DSL. Without it Spring falls back to
> `Constructor.newInstance(args)` with `null` in every unsupplied slot, and
> Kotlin's own intrinsic null check turns that into a
> `NullPointerException` at construction — for a class that has a perfectly
> good default. **Violation — Spring Boot documents it as a hard
> requirement.**

```kotlin
// bad — someone "slimmed the image" and Kotlin default arguments silently
// stopped being applied by every Spring construction path
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web") {
        exclude(group = "org.jetbrains.kotlin", module = "kotlin-reflect")
    }
}

// good
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    implementation("org.jetbrains.kotlin:kotlin-stdlib")
}
```

## 41.9 Compile a Spring Boot 3.x Kotlin project with `-Xjsr305=strict`.

> Why? Spring Framework 6.x annotates its API with `@Nullable` and
> `@NonNullApi` from `org.springframework.lang`, whose javadoc says they
> "Leverage JSR-305 meta-annotations to indicate nullability in Java to common
> tools with JSR-305 support and used by Kotlin to infer nullability of Spring
> API." But the Kotlin compiler's default for those meta-annotations is
> permissive: the
> [Java interop reference](https://kotlinlang.org/docs/java-interop.html)
> states "The default behavior is the same to `-Xjsr305=warn`". Under `warn`,
> `@NonNullApi`-covered return types stay **platform types** — the `T!` that
> [Chapter 6](06-null-safety.md) exists to keep out of your code — and a
> nullability mistake against Spring's API is a warning you will scroll past.
> `strict` turns those into real Kotlin types and the mistakes into compile
> errors. Note the boundaries: plain `javax.annotation.Nonnull` /`@Nullable`
> are "always enabled … regardless of compiler configuration with the
> `-Xjsr305` flag", so this flag is specifically about the
> `@TypeQualifierDefault` annotations Spring uses at package level. Note also
> that Spring Framework 7 moves to
> [JSpecify](https://jspecify.dev/), which Kotlin 2.1 and later already
> enforce strictly by default and which is governed by
> `-Xjspecify-annotations` rather than this flag — so this rule is
> specifically a Spring Boot 3.x concern. See
> [Chapter 28](28-java-interop.md). **Suggestion.**

```kotlin
// bad — build.gradle.kts; Spring API return types arrive as platform types,
// so a wrong nullability assumption compiles and becomes a runtime NPE
kotlin {
    jvmToolchain(21)
}

// good
kotlin {
    jvmToolchain(21)

    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict", "-java-parameters")
    }
}
```

## 41.10 Set the JVM target once, through the toolchain — never by setting `jvmTarget` and Java's `targetCompatibility` separately.

> Why? The Kotlin and Java compile tasks have independent target settings, and
> when they disagree you get a build that either fails opaquely or silently
> emits mixed bytecode versions. The
> [Kotlin Gradle configuration reference](https://kotlinlang.org/docs/gradle-configure-project.html)
> warns about the default case explicitly: "When there is no explicit
> information about the `jvmTarget` value in the build script, its default
> value is `null`, and the compiler translates it to the default value `1.8`.
> The `targetCompatibility` equals the current Gradle's JDK version" — so a
> project built on JDK 21 with no configuration ships Java 8 Kotlin bytecode
> in a jar that claims to need 21. Setting the toolchain via the `kotlin`
> extension fixes both at once: "Setting a toolchain via the `kotlin`
> extension updates the toolchain for Java compile tasks as well."
> **Violation — the Kotlin Gradle plugin's `jvmTargetValidationMode` defaults
> to `ERROR`, failing the build on a Kotlin/Java target mismatch.**

```kotlin
// bad — two sources of truth, and they will drift
kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_21
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

// good — one declaration configures both compile tasks
kotlin {
    jvmToolchain(21)
}
```

## 41.11 Let the Spring Boot Gradle plugin align the Kotlin and coroutines versions; never pin `kotlin.version` by hand.

> Why? A Spring Boot application pulls Kotlin artifacts from three directions
> at once: the Kotlin Gradle plugin, Spring Boot's own dependency management,
> and transitively through starters and coroutines-aware libraries. Mixing
> versions of `kotlin-stdlib` and `kotlin-reflect` produces
> `NoSuchMethodError` at runtime with a stack trace that names neither. Spring
> Boot solves this for you: "In order to avoid mixing different versions of
> Kotlin dependencies on the classpath, Spring Boot imports the Kotlin BOM …
> With Gradle, the Spring Boot plugin automatically aligns the
> `kotlin.version` with the version of the Kotlin plugin"
> ([Spring Boot Kotlin reference](https://docs.spring.io/spring-boot/3.5/reference/features/kotlin.html)).
> It manages coroutines the same way, "by importing the Kotlin Coroutines
> BOM", overridable through the `kotlin-coroutines.version` property. So the
> single lever is the Kotlin Gradle plugin version, and anything else you pin
> is a divergence waiting to happen. **Suggestion.**

```kotlin
// bad — three independent version declarations, one of which is now stale
plugins {
    kotlin("jvm") version "2.4.10"
    id("org.springframework.boot") version "3.5.16"
}

extra["kotlin.version"] = "2.3.20"

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.9.0")
    implementation("org.jetbrains.kotlin:kotlin-reflect:2.3.20")
}

// good — one lever; Boot's dependency management supplies every version
plugins {
    kotlin("jvm") version "2.4.10"
    kotlin("plugin.spring") version "2.4.10"
    id("org.springframework.boot") version "3.5.16"
    id("io.spring.dependency-management") version "1.1.7"
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor")
    implementation("org.jetbrains.kotlin:kotlin-reflect")
}
```

## 41.12 Add `-java-parameters` so Java-side parameter-name discovery keeps working.

> Why? Spring resolves Kotlin parameter names through a dedicated
> `KotlinReflectionParameterNameDiscoverer`, "which allows finding interface
> method parameter names without requiring the Java 8 `-parameters` compiler
> flag" — but the same page adds, "For completeness, we nevertheless recommend
> running the Kotlin compiler with its `-java-parameters` flag for standard
> Java parameter exposure"
> ([Spring Framework: Classes and Interfaces](https://docs.spring.io/spring-framework/reference/6.2/languages/kotlin/classes-interfaces.html)).
> The gap matters wherever something reads names from the JVM rather than from
> Kotlin metadata: `@PathVariable` and `@RequestParam` without an explicit
> name, Jackson creator detection on a class the Kotlin module does not
> handle, and any Java library doing plain reflection over your Kotlin
> classes. The flag costs a few bytes of class-file metadata. **Suggestion.**

```kotlin
// bad — @PathVariable with no explicit name relies on a name that may not
// exist in the bytecode
@GetMapping("/invoices/{reference}")
fun byReference(@PathVariable reference: String): InvoiceResponse = TODO()

// good — build.gradle.kts
kotlin {
    jvmToolchain(21)

    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict", "-java-parameters")
    }
}

// good — and name the binding anyway, so the mapping survives a refactor
@GetMapping("/invoices/{reference}")
fun byReference(@PathVariable("reference") reference: String): InvoiceResponse = TODO()
```

## 41.13 Adopt kotlinx.serialization deliberately, with the `plugin.serialization` compiler plugin — its converter outranks Jackson's the moment it is on the classpath.

> Why? kotlinx.serialization is a genuinely better fit for Kotlin than Jackson
> — the serializer is generated at compile time from `@Serializable`, so there
> is no reflection, no missing-module class of failure, and default arguments
> and non-null types are honoured by construction. But adopting it is not
> additive. Spring MVC's default converter list registers
> `KotlinSerializationJsonHttpMessageConverter` **before**
> `MappingJackson2HttpMessageConverter` whenever `kotlinx.serialization.json.Json`
> is on the classpath, so pulling the library in as a transitive dependency
> silently reroutes every `@Serializable` type away from your configured
> `ObjectMapper` — and away from its naming strategy, its date format, and its
> `@JsonIgnore` annotations. Decide once, per service, and note that the
> runtime dependency alone is not enough: without the
> [`plugin.serialization`](https://kotlinlang.org/docs/serialization.html)
> compiler plugin there is no generated serializer to find. **Suggestion.**

```kotlin
// bad — the runtime library is on the classpath (perhaps transitively) but
// the compiler plugin is not; `@Serializable` types now route to a converter
// that has no serializer for them
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json")
}

// good — plugin and runtime together, and every wire type marked
plugins {
    kotlin("plugin.serialization") version "2.4.10"
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json")
}

@Serializable
data class ChargeRequest(
    val reference: String,
    val amountMinorUnits: Long,
    val description: String = "",
)
```

## 41.14 Set `jvmDefault = JvmDefaultMode.NO_COMPATIBILITY` for a new service so Kotlin interface defaults become real JVM default methods.

> Why? By default the compiler generates both an interface default method and
> a `DefaultImpls` class plus bridge functions, so that older Kotlin binaries
> keep linking. An application is not a published library — nothing outside
> the build depends on its binary shape — so it pays that cost for nothing.
> The [Kotlin 2.2 release notes](https://kotlinlang.org/docs/whatsnew22.html)
> describe the option, now stable and replacing the deprecated
> `-Xjvm-default`: `no-compatibility` "generates only default implementations
> in interfaces. This mode skips compatibility bridges and `DefaultImpls`
> classes, making it suitable for new code." Beyond the smaller output, it is
> what makes a Kotlin interface's default method visible to Java callers and
> to frameworks that reflect over interface methods — including Spring Data
> repository fragments and any interface-based proxy. Do not set this on a
> published library without a deliberate binary-compatibility decision.
> **Suggestion.**

```kotlin
// bad — for an application, DefaultImpls classes and bridges are pure
// overhead, and the default method is not where a Java caller looks for it
interface AuditTrail {
    fun record(event: AuditEvent)

    fun recordAll(events: List<AuditEvent>) {
        events.forEach(::record)
    }
}

// good — build.gradle.kts
kotlin {
    compilerOptions {
        jvmDefault = JvmDefaultMode.NO_COMPATIBILITY
    }
}
```

## 41.15 Prove the plugin configuration with a context-loading test, because every failure mode in this chapter surfaces at runtime.

> Why? Not one rule in this chapter is checked by the Kotlin compiler. A
> missing `kotlin-spring` compiles cleanly and fails at context refresh; a
> missing `kotlin-jpa` compiles cleanly and fails on the first entity load; a
> missing `jackson-module-kotlin` compiles cleanly and fails on the first
> request body. All three are caught by a single test that starts the context
> and touches the relevant boundary — the cheapest safety net available, and
> the reason the Spring Initializr generates one. Make it exercise the
> boundaries the plugins actually cover: refresh the context, deserialise a
> request body, and load one lazily-associated entity. Note that
> `@SpringBootTest` is itself in the `kotlin-spring` preset, so the test class
> is opened for you. **Suggestion.**

```kotlin
// bad — no test at all; the first evidence that a plugin is missing is a
// failed deployment
class BillingApplicationTest

// good — note the @Autowired here is not the redundant kind Chapter 42 §42.2
// bans: the TestContext framework only autowires a test class's constructor
// parameters when they carry it, or when @TestConstructor(autowireMode = ALL)
// is set.
@SpringBootTest
@AutoConfigureMockMvc
class BillingApplicationTest(
    @Autowired private val mockMvc: MockMvc,
    @Autowired private val invoices: InvoiceRepository,
) {

    @Test
    fun `context loads`() {
        // Fails without kotlin-spring: CGLIB cannot subclass a final
        // @Configuration class.
    }

    @Test
    fun `deserialises a Kotlin data class request body`() {
        mockMvc.post("/charges") {
            contentType = MediaType.APPLICATION_JSON
            content = """{"reference":"INV-1","amountMinorUnits":1200}"""
        }.andExpect {
            status { isAccepted() }
        }
    }

    @Test
    fun `loads an entity and traverses a lazy association`() {
        // Fails without kotlin-jpa: no no-arg constructor.
        // Fails without @Entity in allOpen: Hibernate cannot proxy a final
        // class for lazy loading.
        val invoice = invoices.findByReference("INV-1")
        assertThat(invoice?.customer?.name).isNotNull()
    }
}
```
