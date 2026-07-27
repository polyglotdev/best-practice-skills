<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 37. Spring: Footguns & Anti-patterns

Every trap in this chapter has the same shape: the code compiles, the
application starts, the tests pass, and the behaviour is wrong. Spring's
annotations look like language features, so they get read as language
features — but they are implemented by proxies, by classpath conditions, and
by a component scan, and each of those mechanisms has edges that annotations
do not advertise. A `@Transactional` that silently does nothing raises no
warning; an `@Async void` that throws leaves no trace at the call site; a
`@Cacheable` handing out a shared mutable object corrupts data for everyone
who touched it afterwards.

This chapter is the collected list of those edges. It draws on
[Spring Framework: Understanding AOP Proxies](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html),
[Task Execution and Scheduling](https://docs.spring.io/spring-framework/reference/integration/scheduling.html),
[Cache Annotations](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html),
[Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html),
[Spring Boot: Structuring Your Code](https://docs.spring.io/spring-boot/3.4/reference/using/structuring-your-code.html),
and
[Spring Boot: Actuator Endpoints](https://docs.spring.io/spring-boot/3.4/reference/actuator/endpoints.html).

Three rules here overlap deliberately with earlier chapters, because the
failure is worth stating twice: §37.1 and §37.2 generalise the transaction
self-invocation trap from
[Chapter 35, §35.3-§35.4](35-spring-data-and-transactions.md) to every
proxy-based annotation, and §37.15 restates the `@Value` guidance from
[Chapter 33](33-spring-configuration.md) as the runtime failure it produces.

**Tool alignment:** proxy correctness is invisible to Checkstyle and Error
Prone, so most rules below are **Suggestions** backed by review. The
`javax` → `jakarta` rule in §37.21 is the exception: Checkstyle's
`IllegalImport` check, configured with the legacy packages in `illegalPkgs`,
fails the build on any surviving import.

## 37.1 Remember that self-invocation defeats *every* proxy-based annotation, not just `@Transactional`.

> Why? [Understanding AOP Proxies](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)
> states the mechanism once and it applies to all of it: a call on `this`
> never leaves the target object, so it never passes through the proxy that
> implements the advice. `@Transactional`, `@Async`, `@Cacheable`,
> `@CacheEvict`, `@PreAuthorize`, `@Timed` (Micrometer), `@Retryable`
> (Spring Retry, a separate project from Spring Boot), and any custom
> `@Around` aspect all evaporate on an internal call. The
> `@Cacheable` case is the nastiest of the set, because the method still
> returns the right answer — it just recomputes it every time, so the bug
> presents as a latency regression six months later, not as a failure.
> **Suggestion.**

```java
// bad — none of these three annotations does anything on the internal calls
@Service
class QuoteService {
  QuoteBundle bundleFor(String customerId) {
    Rate rate = currentRate();          // @Cacheable — recomputed every call
    audit(customerId);                  // @Async — runs on the caller's thread
    return persist(customerId, rate);   // @Transactional — no transaction
  }

  @Cacheable("rates")
  public Rate currentRate() {
    return rateProvider.fetch();
  }

  @Async
  public void audit(String customerId) {
    auditLog.record(customerId);
  }

  @Transactional
  public QuoteBundle persist(String customerId, Rate rate) {
    return quotes.save(new Quote(customerId, rate));
  }
}

// good — each advised method lives on its own bean, so every call is external
@Service
class QuoteService {
  private final RateCache rateCache;
  private final QuoteAuditor auditor;
  private final QuoteWriter writer;

  QuoteService(RateCache rateCache, QuoteAuditor auditor, QuoteWriter writer) {
    this.rateCache = rateCache;
    this.auditor = auditor;
    this.writer = writer;
  }

  QuoteBundle bundleFor(String customerId) {
    Rate rate = rateCache.currentRate();
    auditor.audit(customerId);
    return writer.persist(customerId, rate);
  }
}
```

## 37.2 Never annotate a `final`, `private`, or `static` method, and never make a proxied class `final`.

> Why? A CGLIB proxy is a generated subclass, so it can only intercept what
> it can override. `private` and `static` methods are not overridable and
> `final` methods must not be, so an annotation on any of them is inert —
> the same silent failure as §37.1, with no call-site clue at all. A `final`
> *class* is worse: CGLIB cannot subclass it, so the container fails to
> create the proxy at startup, which at least fails loudly. One nuance is
> worth knowing, and it is annotation-specific rather than general: for
> transactions,
> [Using `@Transactional`](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)
> states that "As of 6.0, `protected` or package-visible methods can also be
> made transactional for class-based proxies by default." The caching
> annotations still say the opposite —
> [Cache Annotations](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html)
> warns that "If you do annotate protected, private, or package-visible
> methods with these annotations, no error is raised, but the annotated
> method does not exhibit the configured caching settings." Keep proxied
> methods `public` unless you have checked the rule for the specific
> annotation. **Suggestion.**

```java
// bad — final method: annotation silently ignored
@Service
class ReportService {
  @Cacheable("reports")
  public final Report render(long id) {
    return renderer.render(id);
  }
}

// bad — final class: proxy creation fails at startup
@Service
final class ReportService {
  @Transactional
  public void archive(long id) { }
}

// good
@Service
class ReportService {
  @Cacheable("reports")
  public Report render(long id) {
    return renderer.render(id);
  }
}
```

## 37.3 Fix self-invocation by extracting a bean; treat self-injection as a last resort and never do it with an `@Autowired` field.

> Why? Extraction is the fix that survives review, because it makes the two
> responsibilities the class had visible as two beans. Self-injection routes
> the internal call back out through the proxy and does work, but it leaves a
> class that calls itself through the container — a construction no reader
> can follow without knowing the proxy rules, and one that reintroduces the
> bug the moment somebody "simplifies" it back to `this`. If you must, inject
> `ObjectProvider<Self>` rather than an `@Autowired` field: the field form
> creates a circular reference that only resolves because Spring special-cases
> it, and it hides the dependency from the constructor where
> [Chapter 32](32-spring-beans-and-di.md) requires it to be visible.
> **Suggestion.**

```java
// bad — field self-injection: invisible dependency, circular by construction
@Service
class ImportService {
  @Autowired private ImportService self;

  void importAll(List<Row> rows) {
    rows.forEach(self::importOne);
  }

  @Transactional
  public void importOne(Row row) { }
}

// acceptable — lazy lookup, declared in the constructor
@Service
class ImportService {
  private final ObjectProvider<ImportService> self;

  ImportService(ObjectProvider<ImportService> self) {
    this.self = self;
  }

  void importAll(List<Row> rows) {
    rows.forEach(row -> self.getObject().importOne(row));
  }

  @Transactional
  public void importOne(Row row) { }
}

// good — two beans, no self-reference, no proxy subtlety
@Service
class ImportService {
  private final RowImporter rowImporter;

  ImportService(RowImporter rowImporter) {
    this.rowImporter = rowImporter;
  }

  void importAll(List<Row> rows) {
    rows.forEach(rowImporter::importOne);
  }
}
```

## 37.4 Never let an `@Async` method return `void` if it can fail.

> Why? [Task Execution and Scheduling](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)
> states the consequence precisely: "With a `void` return type, however, the
> exception is uncaught and cannot be transmitted." There is no `Future` for
> the caller to `get()`, so the exception reaches Spring's default handler
> and, by default, "the exception is merely logged" — at whatever level that
> handler chooses, on a thread whose name means nothing to your alerting.
> Returning `CompletableFuture<Void>` gives the caller a handle; installing an
> `AsyncUncaughtExceptionHandler` gives you a floor for the cases where
> fire-and-forget really is what you want. Do both. **Suggestion.**

```java
// bad — if reindex throws, nothing upstream ever learns
@Async
public void reindex(long documentId) {
  searchIndex.reindex(documentId);
}

// good — the caller can compose on the result and observe the failure
@Async
public CompletableFuture<Void> reindex(long documentId) {
  searchIndex.reindex(documentId);
  return CompletableFuture.completedFuture(null);
}

// good — and a floor for genuinely fire-and-forget tasks
@Configuration
@EnableAsync
class AsyncConfig implements AsyncConfigurer {
  private static final Logger log = LoggerFactory.getLogger(AsyncConfig.class);

  @Override
  public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
    return (ex, method, params) -> log.error("async task {} failed", method.getName(), ex);
  }
}
```

## 37.5 Configure an explicit, bounded `Executor` for `@Async` instead of accepting the default.

> Why? Spring Boot auto-configures an `AsyncTaskExecutor` and the reference
> documentation confirms "the auto-configured executor will be automatically
> used for: asynchronous task execution (`@EnableAsync`)". That is a
> reasonable default, but you inherit its sizing, and the numbers matter:
> Boot's `TaskExecutionProperties.Pool` ships `coreSize = 8`,
> `maxSize = Integer.MAX_VALUE`, and `queueCapacity = Integer.MAX_VALUE`. A
> `ThreadPoolTaskExecutor` only grows past its core size once the queue is
> full, and that queue never fills — so the pool is permanently eight
> threads wide and every excess task accumulates on the heap until the JVM
> dies. A bounded queue plus an explicit rejection policy turns that slow,
> invisible memory leak into a fast, loud failure. In plain Spring, without
> Boot's auto-configuration, the fallback is a `SimpleAsyncTaskExecutor`
> that creates a *new thread per task* and pools nothing at all.
> **Suggestion.**

```java
// bad — implicit sizing; an unbounded queue means max-size is never reached
@Configuration
@EnableAsync
class AsyncConfig { }

// good (option A) — bound it in configuration
// spring.task.execution.pool.core-size=8
// spring.task.execution.pool.max-size=32
// spring.task.execution.pool.queue-capacity=200

// good (option B) — a dedicated, named, bounded pool for one workload
@Configuration
@EnableAsync
class AsyncConfig {
  @Bean("indexingExecutor")
  ThreadPoolTaskExecutor indexingExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(4);
    executor.setMaxPoolSize(16);
    executor.setQueueCapacity(200);
    executor.setThreadNamePrefix("indexing-");
    executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    executor.initialize();
    return executor;
  }
}

@Async("indexingExecutor")
public CompletableFuture<Void> reindex(long documentId) {
  searchIndex.reindex(documentId);
  return CompletableFuture.completedFuture(null);
}
```

## 37.6 Never put `@Async` and `@Transactional` on the same method.

> Why? A transaction is bound to a thread. `@Async` hands the invocation to a
> different thread, so the caller's transaction is not there to join and the
> method starts a fresh one — meaning the async work commits independently of
> the business operation that triggered it, and can commit after that
> operation rolled back. Stacking two proxies on one method also makes
> behaviour depend on advice ordering, which is not visible in the source.
> Split the two concerns: an async entry point that delegates to a
> transactional bean. **Suggestion.**

```java
// bad — two proxies, one method; the transaction does not span the caller
@Async
@Transactional
public void archiveOldOrders(LocalDate before) {
  orders.archiveBefore(before);
}

// good — async boundary and transactional boundary on separate beans
@Service
class ArchiveScheduler {
  private final OrderArchiver archiver;

  ArchiveScheduler(OrderArchiver archiver) {
    this.archiver = archiver;
  }

  @Async("maintenanceExecutor")
  public CompletableFuture<Void> archiveOldOrders(LocalDate before) {
    archiver.archiveBefore(before);
    return CompletableFuture.completedFuture(null);
  }
}

@Service
class OrderArchiver {
  @Transactional
  public void archiveBefore(LocalDate before) {
    orders.archiveBefore(before);
  }
}
```

## 37.7 Assume nothing thread-bound survives an `@Async` hop — propagate it explicitly.

> Why? The `SecurityContext`, the SLF4J MDC, the request-scoped beans, and
> the transaction are all held in `ThreadLocal`s. The async thread has none
> of them, so `SecurityContextHolder.getContext().getAuthentication()`
> returns `null`, correlation IDs vanish from the logs, and any
> request-scoped injection throws. Each has a designated fix; the failure
> mode when you skip it is an authorisation check that silently passes
> because there is no principal to reject. **Suggestion.**

```java
// bad — the @PreAuthorize inside archive() sees no authentication
@Async
public CompletableFuture<Void> archive(long id) {
  archiver.archive(id);
  return CompletableFuture.completedFuture(null);
}

// good — capture what you need on the calling thread and pass it as data
@Async
public CompletableFuture<Void> archive(long id, String requestedBy) {
  archiver.archive(id, requestedBy);
  return CompletableFuture.completedFuture(null);
}

// good — or wrap the executor so the security context is carried across
@Bean("securityAwareExecutor")
Executor securityAwareExecutor(ThreadPoolTaskExecutor delegate) {
  return new DelegatingSecurityContextAsyncTaskExecutor(delegate);
}
```

## 37.8 Give `@Cacheable` an explicit `key`, and never key on a mutable or unbounded argument.

> Why? The default key generator derives a key from *all* the method's
> parameters. That is wrong in three common ways. If a parameter is a mutable
> object, mutating it after insertion changes its `hashCode` and the entry
> becomes unreachable — a permanent leak. If a parameter is a `Pageable`, a
> `Sort`, or a free-text search string, the key space is unbounded and the
> cache becomes a memory leak with a hit rate near zero. And if you add a
> parameter later, every existing key silently changes and the cache empties
> on deploy. An explicit SpEL key states which arguments actually identify
> the result. **Suggestion.**

```java
// bad — keyed on a mutable filter object and an unbounded Pageable
@Cacheable("products")
public List<Product> search(ProductFilter filter, Pageable pageable) {
  return products.search(filter, pageable);
}

// good — a small, stable, explicitly stated key
@Cacheable(cacheNames = "productsByCategory", key = "#categoryId")
public List<Product> byCategory(long categoryId, Pageable pageable) {
  return products.byCategory(categoryId, pageable);
}
```

## 37.9 Decide deliberately whether a `null` result is cached.

> Why? By default it is. The reference documentation notes the behaviour for
> the `Optional` case explicitly — "If an `Optional` value is not present,
> `null` will be stored in the associated cache" — and the same holds for a
> plain `null` return. Caching the negative is often exactly right: it is
> what stops a cache-penetration attack, where a flood of requests for
> non-existent IDs bypasses the cache and hits the database every time. But
> if a `null` means "not created *yet*", caching it means the entity stays
> invisible until the TTL expires. Pick one with `unless`, and say why in a
> comment. **Suggestion.**

```java
// bad — a lookup that misses just before the row is written caches the null,
// so the signup stays invisible for the whole TTL
@Cacheable("pendingSignups")
public Signup findPending(String token) {
  return signups.findPending(token).orElse(null);
}

// good — the negative is not cached, because the row appears moments later
@Cacheable(cacheNames = "pendingSignups", unless = "#result == null")
public Signup findPending(String token) {
  return signups.findPending(token).orElse(null);
}

// good — the negative IS cached, deliberately: unknown emails are attacker
// traffic and must not reach the database on every request
@Cacheable("usersByEmail") // null cached on purpose — see cache-penetration note
public User findByEmail(String email) {
  return users.findByEmail(email).orElse(null);
}
```

## 37.10 Use `sync = true` when many threads can request the same expensive value at once.

> Why? This is the cache stampede, and the documentation names it: "In a
> multi-threaded environment, certain operations might be concurrently
> invoked for the same argument (typically on startup). By default, the cache
> abstraction does not lock anything, and the same value may be computed
> several times, defeating the purpose of caching." On a cold cache under
> load, every in-flight request misses and every one of them runs the
> expensive computation — so the cache makes the thundering herd worse than
> no cache. With `sync`, "only one thread is busy computing the value, while
> the others are blocked until the entry is updated in the cache." Note that
> `sync` is mutually exclusive with `unless` and with multiple cache names.
> **Suggestion.**

```java
// bad — 200 concurrent cold requests run 200 identical rate lookups
@Cacheable(cacheNames = "exchangeRates", key = "#pair")
public Rate rateFor(String pair) {
  return rateProvider.fetch(pair); // 400ms remote call
}

// good — one computes, the rest wait for it
@Cacheable(cacheNames = "exchangeRates", key = "#pair", sync = true)
public Rate rateFor(String pair) {
  return rateProvider.fetch(pair);
}
```

## 37.11 Never return a mutable object from a `@Cacheable` method.

> Why? An in-process cache stores the reference, not a copy. Every caller
> receives the *same* instance, so one caller sorting the returned list, or
> setting a field on the returned object, corrupts the value every subsequent
> caller sees — and the corruption persists until eviction, long after the
> code that caused it has returned. This is one of the hardest production
> bugs to reproduce, because it requires two callers in a specific order.
> Return a `record`, an immutable collection, or a defensive copy. See
> [Chapter 20](20-collections.md) on unmodifiable views.
> **Suggestion.**

```java
// bad — the caller can mutate the cached list for everyone
@Cacheable("categories")
public List<Category> allCategories() {
  return new ArrayList<>(categories.findAll());
}

// caller, elsewhere, innocently:
List<Category> sorted = catalog.allCategories();
sorted.sort(comparing(Category::name)); // the cache is now sorted, forever

// good — the cached value cannot be mutated
@Cacheable("categories")
public List<Category> allCategories() {
  return List.copyOf(categories.findAll());
}
```

## 37.12 Never place `@SpringBootApplication` in the default package, and never widen the scan base to escape a layout problem.

> Why? [Structuring Your Code](https://docs.spring.io/spring-boot/3.4/reference/using/structuring-your-code.html)
> is direct about the worst case: the default package "can cause particular
> problems for Spring Boot applications that use the `@ComponentScan`,
> `@ConfigurationPropertiesScan`, `@EntityScan`, or `@SpringBootApplication`
> annotations, since every class from every jar is read." Scanning every
> class on the classpath adds seconds to every start and every test-context
> load, and can instantiate beans from libraries you never intended to
> activate. The same applies in weaker form to
> `@ComponentScan("com")` added to reach a stray package: "Using a root
> package also allows component scan to apply only on your project." Move the
> class, do not widen the scan. **Suggestion.**

```java
// bad — src/main/java/Application.java, no package declaration:
// every class from every jar on the classpath is scanned
@SpringBootApplication
public class Application {}

// bad — src/main/java/com/example/app/Application.java, scan widened to
// "com" to reach a class that was put in the wrong package
@SpringBootApplication
@ComponentScan({"com.example.app", "com.shared", "com"})
public class Application {}

// good — src/main/java/com/example/orders/Application.java, a root package
// above everything the application owns, with no @ComponentScan at all
@SpringBootApplication
public class Application {}
```

## 37.13 A singleton bean must not hold mutable per-request state.

> Why? `@Service`, `@Component`, `@Controller`, and `@Repository` beans are
> singletons, so one instance is shared by every request thread. A mutable
> field is therefore a data race whose symptom is one user seeing another
> user's data — the worst class of bug, because it is a security incident,
> it does not reproduce under single-threaded testing, and it looks like
> perfectly ordinary code. Every field on a singleton should be `final` and
> hold either an immutable value or a thread-safe collaborator. Per-request
> state belongs in a method parameter or a local variable.
> **Suggestion.**

```java
// bad — currentUser is shared across every concurrent request
@Service
class ReportService {
  private String currentUser;

  public Report generate(String user, ReportRequest request) {
    this.currentUser = user;
    return build(request); // reads this.currentUser — may be someone else's
  }
}

// good — per-request state stays on the stack
@Service
class ReportService {
  public Report generate(String user, ReportRequest request) {
    return build(user, request);
  }
}
```

## 37.14 Injecting a request- or session-scoped bean into a singleton requires a scoped proxy.

> Why? [Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)
> explains the mismatch: "dependencies are resolved at instantiation time",
> so a singleton created once at startup captures one instance of the
> shorter-lived bean and holds it forever. Depending on the scope this either
> fails immediately (no request is in progress at startup) or — far worse —
> succeeds and pins the first request's data into a singleton that every
> subsequent request reads, which is §37.13 by another route. The fix is a
> scoped proxy: the container injects "an object that exposes the exact same
> public interface", which resolves the real instance from the current scope
> on every call. **Suggestion.**

```java
// bad — one RequestContext captured at startup, shared by every request
@Component
@Scope("request")
class RequestContext {
  private String correlationId;
}

@Service
class AuditService {
  private final RequestContext context;

  AuditService(RequestContext context) {
    this.context = context;
  }
}

// good — a scoped proxy resolves the current request's instance per call
@Component
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
class RequestContext {
  private String correlationId;
}

// also good — an explicit lookup, with no proxy magic to explain
@Service
class AuditService {
  private final ObjectProvider<RequestContext> context;

  AuditService(ObjectProvider<RequestContext> context) {
    this.context = context;
  }
}
```

## 37.15 Prefer `@ConfigurationProperties` to `@Value`, because a bad `@Value` fails at bean creation, not at startup.

> Why? An unresolvable `@Value` placeholder throws when the bean holding it
> is created. For an eager singleton that is startup, which is tolerable. For
> a `@Lazy` bean, a prototype, a request-scoped bean, a
> `@ConditionalOnProperty` bean, or any application running with
> `spring.main.lazy-initialization=true`, bean creation happens on the first
> request that needs it — so a typo'd property key ships to production and
> fails as a 500 under load. `@ConfigurationProperties` binds a whole group
> at once, supports `@Validated` with Jakarta Bean Validation, gives you
> relaxed binding and IDE metadata, and turns the same typo into a startup
> failure with a message that names the property. See
> [Chapter 33](33-spring-configuration.md). **Suggestion.**

```java
// bad — a typo here surfaces whenever this bean is first created
@Service
class PaymentService {
  @Value("${payment.gateway.timeout-secondss}")
  private int timeoutSeconds;
}

// good — validated, grouped, bound and checked at startup
@ConfigurationProperties("payment.gateway")
@Validated
record PaymentGatewayProperties(
    @NotBlank String baseUrl, @Positive int timeoutSeconds, @Positive int maxRetries) {}

@Service
class PaymentService {
  private final PaymentGatewayProperties properties;

  PaymentService(PaymentGatewayProperties properties) {
    this.properties = properties;
  }
}
```

## 37.16 Treat `@DependsOn` as a smell — model the real dependency as an injected collaborator.

> Why? `@DependsOn` orders bean *creation* by name, using a string the
> compiler cannot check and a refactor will not rename. It is almost always
> compensating for hidden coupling: bean A reads state that bean B populates
> in `@PostConstruct`, and rather than expressing that, the author forced an
> order. The result is a startup sequence documented in an annotation nobody
> reads, which breaks silently when the bean is renamed. Inject B into A and
> the container derives the order itself, correctly and refactor-safely. The
> genuine remaining use is a side-effect-only bean with no injectable handle
> — a Flyway migration runner ahead of a cache warmer, say. **Suggestion.**

```java
// bad — string-named ordering standing in for a real dependency
@Component
@DependsOn("referenceDataLoader")
class PricingEngine {
  private final ReferenceDataCache cache = ReferenceDataCache.INSTANCE; // static state
}

// good — the dependency is in the constructor, so ordering is automatic
@Component
class PricingEngine {
  private final ReferenceDataLoader referenceData;

  PricingEngine(ReferenceDataLoader referenceData) {
    this.referenceData = referenceData;
  }
}
```

## 37.17 Never swallow an exception inside an `ApplicationRunner` or `CommandLineRunner`.

> Why? An exception escaping a runner fails `SpringApplication.run`, which is
> what you want: a broken migration, a missing schema, or an unreachable
> dependency should stop the deploy. Catching and logging it inverts that —
> the process reports healthy, the readiness probe passes, traffic arrives,
> and the application serves requests against state it knows is broken. The
> logged line is the only evidence, and it scrolls past. Note also that the
> embedded web server may already be accepting connections by the time
> runners execute, so startup work that must complete before traffic arrives
> is better placed in a readiness check than in a runner at all.
> **Suggestion.** See [Chapter 24](24-exceptions.md) on swallowed exceptions.

```java
// bad — the app starts "successfully" with an unmigrated schema
@Component
class SchemaCheckRunner implements ApplicationRunner {
  private static final Logger log = LoggerFactory.getLogger(SchemaCheckRunner.class);

  @Override
  public void run(ApplicationArguments args) {
    try {
      schemaValidator.verify();
    } catch (SchemaMismatchException e) {
      log.error("schema check failed", e); // and then we start serving anyway
    }
  }
}

// good — the failure stops the deploy
@Component
class SchemaCheckRunner implements ApplicationRunner {
  @Override
  public void run(ApplicationArguments args) {
    schemaValidator.verify(); // throws; SpringApplication.run fails
  }
}
```

## 37.18 Never expose Actuator endpoints beyond `health` without authentication.

> Why? [Actuator Endpoints](https://docs.spring.io/spring-boot/3.4/reference/actuator/endpoints.html)
> ships a safe default — "By default, only the health endpoint is exposed
> over HTTP and JMX" — and pairs any change to it with a direct instruction:
> "Before setting the `management.endpoints.web.exposure.include`, ensure
> that the exposed actuators do not contain sensitive information, are
> secured by placing them behind a firewall, or are secured by something like
> Spring Security." The wildcard form is the one that appears in incident
> reports: `/actuator/env` dumps every resolved property including decrypted
> credentials, `/actuator/heapdump` returns the whole heap, and
> `/actuator/loggers` lets an anonymous caller turn on `DEBUG` logging in
> production. **Suggestion.**

```properties
# bad — env, heapdump, threaddump, loggers, and mappings, unauthenticated
management.endpoints.web.exposure.include=*

# good — expose only what your platform actually scrapes
management.endpoints.web.exposure.include=health,info,prometheus
management.endpoint.health.show-details=when-authorized
```

```java
// good — and require a role for everything that is not the health probe
@Bean
SecurityFilterChain actuatorSecurity(HttpSecurity http) throws Exception {
  return http.securityMatcher(EndpointRequest.toAnyEndpoint())
      .authorizeHttpRequests(
          auth ->
              auth.requestMatchers(EndpointRequest.to(HealthEndpoint.class))
                  .permitAll()
                  .anyRequest()
                  .hasRole("ACTUATOR"))
      .httpBasic(Customizer.withDefaults())
      .build();
}
```

## 37.19 Do not override Boot auto-configuration by accident, and never enable bean-definition overriding to silence the conflict.

> Why? Most Boot auto-configuration is guarded by `@ConditionalOnMissingBean`,
> so declaring your own `ObjectMapper`, `RestClient.Builder`, `DataSource`, or
> `TaskExecutor` bean does not *supplement* Boot's — it silently replaces it,
> taking every customisation Boot applied with it. The classic symptom is an
> `ObjectMapper` bean added for one module that quietly reverts the whole
> application's date format and `snake_case` naming. The correct move is
> almost always a customiser (`Jackson2ObjectMapperBuilderCustomizer`,
> `RestClientCustomizer`) that adjusts Boot's instance instead of replacing
> it. And when two definitions genuinely collide, Boot's default of failing
> the startup is right — `spring.main.allow-bean-definition-overriding=true`
> converts a loud, fixable conflict into whichever definition happened to be
> registered last. **Suggestion.**

```java
// bad — replaces Boot's fully configured mapper, losing every module,
// property, and date setting it had applied
@Bean
ObjectMapper objectMapper() {
  return new ObjectMapper().registerModule(new JavaTimeModule());
}

// good — adjust Boot's mapper rather than replacing it
@Bean
Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
  return builder -> builder.featuresToDisable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
}
```

```properties
# bad — hides a real conflict behind registration order
spring.main.allow-bean-definition-overriding=true
```

## 37.20 Do not put `@Autowired` on a class's only constructor.

> Why? The reference documentation is explicit: "If a class only declares a
> single constructor to begin with, it will always be used, even if not
> annotated." The annotation is therefore pure noise, and noise with a cost —
> it implies to a reader that something non-default is happening, and it
> couples a plain Java class to a Spring annotation for no benefit, which
> makes it marginally harder to construct in a unit test's mind. Keep the
> annotation only when a class has several constructors and you must
> designate one. **Suggestion.** See
> [Chapter 32](32-spring-beans-and-di.md) for the wider injection rules.

```java
// bad — redundant on a single constructor
@Service
class OrderService {
  private final OrderRepository orders;

  @Autowired
  OrderService(OrderRepository orders) {
    this.orders = orders;
  }
}

// good
@Service
class OrderService {
  private final OrderRepository orders;

  OrderService(OrderRepository orders) {
    this.orders = orders;
  }
}
```

## 37.21 On Spring Boot 3, every Jakarta EE import is `jakarta.*` — never `javax.*`.

> Why? Spring Boot 3 baselines on Jakarta EE 9+, where the entire API
> namespace moved from `javax` to `jakarta`. This is not a rename you can
> partially adopt: `jakarta.persistence.Entity` and
> `javax.persistence.Entity` are unrelated types, so a single surviving
> `javax` import means the annotation is invisible to Hibernate, the
> validation constraint is never evaluated, or the servlet filter is never
> registered — all without a compile error, because the old artifact is often
> still on the classpath transitively. Audit every `javax.persistence`,
> `javax.validation`, `javax.servlet`, `javax.annotation`, and
> `javax.transaction` import. **Violation — enforced by Checkstyle
> `IllegalImport` with the legacy packages listed in `illegalPkgs`.**

```java
// bad — compiles, and is silently ignored by Hibernate and the validator
import javax.persistence.Entity;
import javax.validation.constraints.NotBlank;

// good
import jakarta.persistence.Entity;
import jakarta.validation.constraints.NotBlank;
```

```xml
<!-- config/checkstyle/checkstyle.xml -->
<module name="IllegalImport">
  <property
      name="illegalPkgs"
      value="javax.persistence,javax.validation,javax.servlet,javax.transaction,javax.annotation"/>
</module>
```

## 37.22 When migrating to Spring Boot 3, replace removed APIs rather than pinning old versions to keep them.

> Why? Boot 3 removed a set of APIs that had documented replacements for
> years, and each removal has a modern equivalent that is better, not merely
> different. Holding a dependency back to keep the old form works exactly
> once and then blocks every subsequent security patch on that library. The
> replacements worth knowing:
> `WebSecurityConfigurerAdapter` is gone in Spring Security 6 in favour of a
> `SecurityFilterChain` bean and the lambda DSL; auto-configuration is
> registered in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`
> rather than `spring.factories`; `RestTemplate` is in maintenance mode and
> `RestClient` (Spring Framework 6.1 / Boot 3.2) is the synchronous
> replacement; and `@MockBean` is deprecated in Boot 3.4 in favour of
> `@MockitoBean` (see [Chapter 36, §36.5](36-spring-testing.md)).
> **Suggestion.**

```java
// bad — removed in Spring Security 6; will not compile on Boot 3
@Configuration
class SecurityConfig extends WebSecurityConfigurerAdapter {
  @Override
  protected void configure(HttpSecurity http) throws Exception {
    http.authorizeRequests().antMatchers("/public/**").permitAll().anyRequest().authenticated();
  }
}

// good — a SecurityFilterChain bean with the lambda DSL
@Configuration
class SecurityConfig {
  @Bean
  SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http.authorizeHttpRequests(
            auth -> auth.requestMatchers("/public/**").permitAll().anyRequest().authenticated())
        .build();
  }
}
```
