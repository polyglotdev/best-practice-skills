<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 45. Spring: Data & Transactions with Coroutines

This is a **delta chapter**. Everything a Spring transaction requires of a
Java service it requires of a Kotlin one, and none of it is repeated here.
Boundary placement on the application service, self-invocation, `readOnly`,
propagation and `REQUIRES_NEW`, `rollbackFor`, remote IO inside a
transaction, `@TransactionalEventListener`, `open-in-view`, N+1 and fetch
joins, pagination cost, batch flush intervals, and testing against the real
engine are all in **`best-practice-java` Chapter 35, "Spring: Data Access &
Transactions"** — read it first and apply it unchanged.

What follows is the Kotlin delta, and it opens with the single most expensive
mistake available to a Kotlin Spring service: **`@Transactional` on a
`suspend` function**. The rest is entity modelling, where Kotlin's defaults
(final classes, no no-arg constructor, `data class` value semantics) collide
with what JPA and Hibernate assume, and repository shape, where Spring Data's
coroutine support has rules of its own.

Rules draw on
[Spring Framework: Coroutines](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html),
[Spring Framework: Programmatic Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/programmatic.html),
[Spring Data Commons: Coroutines](https://docs.spring.io/spring-data/commons/reference/kotlin/coroutines.html),
and the Kotlin
[all-open](https://kotlinlang.org/docs/all-open-plugin.html) and
[no-arg](https://kotlinlang.org/docs/no-arg-plugin.html) compiler-plugin
documentation. Dispatcher selection is
[Chapter 34](34-dispatchers-and-context.md); the plugin and build setup this
chapter assumes is [Chapter 41](41-spring-kotlin-setup.md).

**Tool alignment:** detekt's `InjectDispatcher` catches exactly one of the
mistakes below (§45.5). Nothing in ktlint or detekt understands Spring
proxies or JPA mapping, so every other rule is a **Suggestion**, best
enforced by an ArchUnit rule — no `@Transactional` on a `suspend` function
in a module whose transaction manager is a `PlatformTransactionManager`, and
no `@Entity` type declared as a `data class` — plus review.

## 45.1 Never put `@Transactional` on a `suspend` function backed by a `PlatformTransactionManager`.

> Why? This is the headline trap, and it fails silently. Spring's imperative
> transaction management is thread-bound: `TransactionSynchronizationManager`
> keeps the active transaction and its connection in a `ThreadLocal`, and
> `TransactionInterceptor` is an ordinary synchronous around-advice. A
> `suspend` function compiles to a JVM method with a trailing `Continuation`
> parameter that returns the `COROUTINE_SUSPENDED` marker the instant its body
> actually suspends. The interceptor cannot distinguish that marker from a
> real return value, so it **commits and closes the transaction right there**,
> while the rest of the body has not run. When the coroutine resumes — often
> on a different thread — the `ThreadLocal` on that thread holds nothing, so
> every subsequent repository call runs in its own auto-commit unit. You get
> partial writes, no rollback, and connections returned to the pool early,
> with no exception and no log line. It is worse than useless because a test
> whose body happens never to reach a real suspension point will pass; see
> [Chapter 46, §46.12](46-spring-testing-kotlin.md). **Suggestion.**

```kotlin
// bad — the debit commits at the first suspension point; the credit runs
// outside any transaction, and a failure between them cannot roll back
@Service
class TransferService(private val accounts: AccountRepository) {

    @Transactional
    suspend fun transfer(from: String, to: String, amount: BigDecimal) {
        withContext(Dispatchers.IO) { accounts.debit(from, amount) }
        auditClient.record(from, to, amount) // suspends
        withContext(Dispatchers.IO) { accounts.credit(to, amount) }
    }
}

// good — the transactional unit is a plain function; the coroutine boundary
// sits outside it (see 45.2)
@Service
class TransferService(private val ledger: LedgerWriter) {

    suspend fun transfer(from: String, to: String, amount: BigDecimal) =
        withContext(Dispatchers.IO) { ledger.transfer(from, to, amount) }
}

@Service
class LedgerWriter(private val accounts: AccountRepository) {

    @Transactional
    fun transfer(from: String, to: String, amount: BigDecimal) {
        accounts.debit(from, amount)
        accounts.credit(to, amount)
    }
}
```

`@Transactional` on a `suspend` function is **not** universally wrong. Spring
routes suspending functions through its reactive transaction infrastructure
when the configured manager is a `ReactiveTransactionManager` — an
`R2dbcTransactionManager`, for instance — because a reactive transaction is
bound to the Reactor context that the coroutine carries with it, not to a
thread. JPA is fully synchronous and has no reactive manager, so on a
JPA/JDBC stack the rule above holds without exception.

## 45.2 Keep the transactional unit a non-`suspend` function on its own bean, called from `withContext(Dispatchers.IO)`.

> Why? Two constraints have to be satisfied at once. The transaction must run
> start to finish on one thread with no suspension inside it (§45.1), and the
> blocking JDBC work must not run on a caller's event loop or on
> `Dispatchers.Default` (§45.5). Putting the whole unit in a plain function
> on a separate bean satisfies both: the coroutine boundary is *outside* the
> proxy, so the interceptor sees a normal synchronous call, and
> `withContext(Dispatchers.IO)` moves that whole synchronous call onto a
> dispatcher designed to be blocked. The separate bean is not optional — a
> `private fun` or a call on `this` bypasses the proxy entirely
> (`best-practice-java` §35.3). **Suggestion.**

```kotlin
// bad — withContext is inside the transaction, so the transaction ends at
// the dispatch and the writes happen on a thread that has no transaction
@Service
class ImportService(private val customers: CustomerRepository) {

    @Transactional
    suspend fun importAll(rows: List<CustomerRow>) {
        withContext(Dispatchers.IO) { rows.forEach { customers.save(it.toEntity()) } }
    }
}

// good — one dispatch, then a wholly synchronous transactional call
@Service
class ImportService(private val writer: CustomerWriter) {

    suspend fun importAll(rows: List<CustomerRow>): Int =
        withContext(Dispatchers.IO) { writer.saveAll(rows) }
}

@Service
class CustomerWriter(private val customers: CustomerRepository) {

    @Transactional
    fun saveAll(rows: List<CustomerRow>): Int {
        rows.forEach { customers.save(it.toEntity()) }
        return rows.size
    }
}
```

## 45.3 On a genuinely reactive stack, use `TransactionalOperator.executeAndAwait` rather than reaching for the annotation.

> Why? When the data access is R2DBC or reactive Mongo, transactions are
> real and coroutine-safe — but the programmatic form states the boundary in
> the source instead of hiding it behind a proxy whose behaviour depends on
> which transaction manager happens to be configured. The
> [reference](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html)
> ships exactly this extension: "For suspending functions, a
> `TransactionalOperator.executeAndAwait` extension is provided." Spring's own
> guidance in the
> [programmatic transaction chapter](https://docs.spring.io/spring-framework/reference/data-access/transaction/programmatic.html)
> is that the team "generally recommends the `TransactionTemplate` for
> programmatic transaction management in imperative flows and
> `TransactionalOperator` for reactive code." **Suggestion.**

```kotlin
// bad — an imperative TransactionTemplate on a reactive stack: the callback
// blocks, and the reactive transaction context never sees it
@Service
class ProfileService(
    private val transactionTemplate: TransactionTemplate,
    private val profiles: ProfileRepository,
) {
    suspend fun rename(id: UUID, name: String) =
        transactionTemplate.executeWithoutResult { runBlocking { profiles.rename(id, name) } }
}

// good — the boundary is explicit, and it spans suspension points correctly
@Service
class ProfileService(
    transactionManager: ReactiveTransactionManager,
    private val profiles: ProfileRepository,
    private val audits: AuditRepository,
) {
    private val transactionalOperator = TransactionalOperator.create(transactionManager)

    suspend fun rename(id: UUID, name: String): Profile =
        transactionalOperator.executeAndAwait {
            val profile = profiles.rename(id, name)
            audits.record(id, "profile.renamed")
            profile
        }
}
```

## 45.4 Bracket a reactive stream with `Flow<T>.transactional`, and never assume a `Flow` you return still has a transaction when someone else collects it.

> Why? A `Flow` is cold: nothing runs until a collector arrives. Returning a
> repository `Flow` out of a transactional scope therefore returns a *recipe*,
> and by the time the caller collects it the transaction has long committed.
> The
> [reference](https://docs.spring.io/spring-framework/reference/languages/kotlin/coroutines.html)
> supplies the fix for the reactive case: "For Kotlin `Flow`, a
> `Flow<T>.transactional` extension is provided," which attaches the boundary
> to the stream itself so it opens on subscription and closes on completion.
> On a blocking stack there is no such fix, which is another way of saying
> §45.17: collect and map inside the boundary, return values. **Suggestion.**

```kotlin
// bad — the transaction is gone before the collector arrives
@Service
class LedgerService(
    private val transactionalOperator: TransactionalOperator,
    private val entries: EntryRepository,
) {
    suspend fun entriesFor(account: String): Flow<Entry> =
        transactionalOperator.executeAndAwait { entries.findAllByAccount(account) }
}

// good — the boundary travels with the stream
@Service
class LedgerService(
    transactionManager: ReactiveTransactionManager,
    private val entries: EntryRepository,
) {
    private val transactionalOperator = TransactionalOperator.create(transactionManager)

    fun entriesFor(account: String): Flow<Entry> =
        entries.findAllByAccount(account).transactional(transactionalOperator)
}
```

## 45.5 Never call a blocking repository from a coroutine without `withContext(Dispatchers.IO)`.

> Why? A `suspend` function is expected by every caller to be main-safe: safe
> to call from any dispatcher without parking that dispatcher's thread. A JDBC
> or JPA repository call breaks that contract silently. On `Dispatchers.Default`
> — which has as many threads as CPU cores — a handful of concurrent queries
> starves every other computation in the process. On a WebFlux event loop it
> stalls the server. `Dispatchers.IO` exists precisely to absorb blocking
> calls, with a default parallelism of 64 that you can narrow per subsystem
> with `limitedParallelism`. Inject the dispatcher rather than hardcoding it,
> so tests can substitute one.
> **Violation — enforced by `detekt/InjectDispatcher`.**

```kotlin
// bad — a JDBC call on whatever dispatcher the caller happened to be on
@Service
class OrderQueryService(private val orders: OrderRepository) {

    suspend fun findById(id: UUID): OrderView? = orders.findById(id)?.let(OrderView::from)
}

// bad — the right dispatcher, hardcoded; detekt flags the reference
@Service
class OrderQueryService(private val orders: OrderRepository) {

    suspend fun findById(id: UUID): OrderView? =
        withContext(Dispatchers.IO) { orders.findById(id)?.let(OrderView::from) }
}

// good — injected, so a test can pass a TestDispatcher
@Service
class OrderQueryService(
    private val orders: OrderRepository,
    private val ioDispatcher: CoroutineDispatcher,
) {
    suspend fun findById(id: UUID): OrderView? =
        withContext(ioDispatcher) { orders.findById(id)?.let(OrderView::from) }
}
```

## 45.6 Never call `runBlocking` inside a `@Transactional` method.

> Why? `runBlocking` parks the calling thread until the coroutine completes,
> and that thread is the one holding the transaction's `ThreadLocal` and its
> pooled connection. Every suspension inside the block therefore extends the
> lifetime of an open transaction and a checked-out connection, held while
> waiting on work that may itself be waiting for a connection — a
> straightforward pool deadlock under load. It is also the same defect as
> `best-practice-java` §35.11 (remote IO inside a transaction) with the IO
> hidden one layer down. If a transactional method needs a suspending
> collaborator, the design is wrong: call the collaborator first, then open
> the transaction. **Suggestion.**

```kotlin
// bad — the transaction and its connection are pinned for the duration of a
// remote call, and the pool can deadlock against itself
@Transactional
fun settle(orderId: UUID) {
    val order = orders.findById(orderId) ?: throw OrderNotFoundException(orderId)
    val receipt = runBlocking { paymentClient.charge(order.total) }
    order.markPaid(receipt.reference)
}

// good — remote call outside the boundary, two short transactions
suspend fun settle(orderId: UUID) {
    val total = withContext(ioDispatcher) { orderReader.totalOf(orderId) }
    val receipt = paymentClient.charge(total)
    withContext(ioDispatcher) { orderWriter.markPaid(orderId, receipt.reference) }
}
```

## 45.7 Apply the `kotlin-spring` plugin instead of marking `@Transactional` classes `open` by hand.

> Why? Kotlin classes and members are `final` by default, and a CGLIB
> transaction proxy works by subclassing and overriding — so a `final` class
> or a `final` method cannot be advised. Spring Boot detects the case and
> fails fast in most configurations, but the correct fix is not to sprinkle
> `open` through the codebase; it is the `all-open` compiler plugin, whose
> `kotlin-spring` preset covers `@Component`, `@Async`, `@Transactional`,
> `@Cacheable`, and `@SpringBootTest`, plus everything meta-annotated
> `@Component` — `@Configuration`, `@Controller`, `@RestController`,
> `@Service`, `@Repository`. Hand-written `open` is noise that a reader
> cannot distinguish from deliberate extensibility, and it is one refactor
> away from being forgotten. Full build configuration is
> [Chapter 41](41-spring-kotlin-setup.md). **Suggestion.**

```kotlin
// bad — `open` written by hand on every class and every advised method
@Service
open class LedgerWriter(private val accounts: AccountRepository) {

    @Transactional
    open fun transfer(from: String, to: String, amount: BigDecimal) { /* ... */ }
}

// good — build.gradle.kts opens them, so the source stays clean
plugins {
    kotlin("jvm") version "2.4.0"
    kotlin("plugin.spring") version "2.4.0"
}

@Service
class LedgerWriter(private val accounts: AccountRepository) {

    @Transactional
    fun transfer(from: String, to: String, amount: BigDecimal) { /* ... */ }
}
```

## 45.8 Never make a JPA entity a `data class`.

> Why? A `data class` derives `equals`, `hashCode`, `toString`, `componentN`,
> and `copy` from the primary-constructor properties, and every one of those
> is wrong for a persistent object. `hashCode` computed over mutable fields
> changes when the entity is flushed and its generated id is assigned, so an
> entity added to a `HashSet` before persist becomes unfindable in that set
> afterwards — the classic "the collection contains it but `contains` says no"
> bug. `equals` over all fields makes two rows with the same identity unequal
> because one has a lazily-loaded association populated. `copy()` produces a
> **detached** clone the persistence context knows nothing about, so saving it
> silently inserts a duplicate row. And `toString` walks every property,
> including lazy associations. `data class` is for value carriers; a JPA
> entity is an identity carrier with mutable state, which is the opposite
> thing. See [Chapter 11](11-data-classes.md). **Suggestion.**

```kotlin
// bad — hashCode changes at flush, copy() detaches, toString triggers loads
@Entity
@Table(name = "orders")
data class OrderEntity(
    @Id @GeneratedValue val id: Long? = null,
    var status: OrderStatus,
    @OneToMany(mappedBy = "order") var lines: MutableList<OrderLineEntity> = mutableListOf(),
)

// good — a plain class, identity-based equality, constant hash
@Entity
@Table(name = "orders")
class OrderEntity(
    @Column(nullable = false)
    var customerId: UUID,
    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    var status: OrderStatus,
) {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null

    @OneToMany(mappedBy = "order", cascade = [CascadeType.ALL], orphanRemoval = true)
    var lines: MutableList<OrderLineEntity> = mutableListOf()

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is OrderEntity) return false
        return id != null && id == other.id
    }

    override fun hashCode(): Int = OrderEntity::class.hashCode()

    override fun toString(): String = "OrderEntity(id=$id, status=$status)"
}
```

## 45.9 Apply the `kotlin-jpa` plugin rather than hand-writing a no-arg constructor.

> Why? JPA requires a no-argument constructor on every entity, and Kotlin does
> not generate one for a class with constructor parameters. The usual hand
> fixes are both bad: defaulting every constructor parameter makes
> `OrderEntity()` a legal call from application code, producing entities with
> nonsense state; a secondary `constructor() : this(...)` puts sentinel values
> in the source. The
> [no-arg plugin](https://kotlinlang.org/docs/no-arg-plugin.html) does it
> properly — its `kotlin-jpa` preset covers `@Entity`, `@Embeddable`, and
> `@MappedSuperclass`, and "the generated constructor is synthetic, so it
> can't be directly called from Java or Kotlin, but it can be called using
> reflection," which is exactly the visibility you want: Hibernate can reach
> it and your code cannot. **Suggestion.**

```kotlin
// bad — every property defaulted so that OrderEntity() compiles; now the
// application can construct an order with no customer and no status
@Entity
class OrderEntity(
    var customerId: UUID = UUID(0L, 0L),
    var status: OrderStatus = OrderStatus.DRAFT,
)

// good — build.gradle.kts, and the constructor stays honest
plugins {
    kotlin("plugin.jpa") version "2.4.0"
}

@Entity
class OrderEntity(
    var customerId: UUID,
    var status: OrderStatus,
)
```

## 45.10 Open entity classes and their persistent properties with `all-open`, not with `open` keywords.

> Why? Hibernate creates a runtime subclass of the entity to implement lazy
> `@ManyToOne` proxies and, when bytecode enhancement is off, to intercept
> property access. A `final` class cannot be subclassed and a `final` getter
> cannot be overridden, so a Kotlin entity left at the defaults cannot be
> proxied. The exact symptom is Hibernate-version and configuration
> dependent — commonly a "could not create proxy factory" warning at startup
> followed by every lazy association silently degrading to eager, and, with
> bytecode enhancement enabled, an outright "Getters of lazy classes cannot
> be final" failure. Neither outcome is one you want to discover in
> production, and both are the same root cause. The
> `kotlin-jpa` plugin only supplies the constructor; opening is a separate
> concern handled by `all-open`, and its Spring preset does not include the
> `jakarta.persistence` annotations, so you must list them. **Suggestion.**

```kotlin
// bad — allopen configured only via the Spring preset; entities stay final
plugins {
    kotlin("plugin.spring") version "2.4.0"
    kotlin("plugin.jpa") version "2.4.0"
}

// good — the persistence annotations are opened explicitly
plugins {
    kotlin("plugin.spring") version "2.4.0"
    kotlin("plugin.jpa") version "2.4.0"
    kotlin("plugin.allopen") version "2.4.0"
}

allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}
```

## 45.11 Give a database-generated identifier a nullable `var id: Long? = null`, never `lateinit`.

> Why? `lateinit` does not work on `Long`, `Int`, or any other primitive type
> at all — the compiler rejects it — so the only way to use it for an id is to
> box the type, which changes the mapping. Even where it compiles (a `UUID`
> id, say) it is the wrong model: an entity genuinely has no identifier
> between construction and flush, and `lateinit` expresses that state as
> "reading this throws `UninitializedPropertyAccessException`" rather than as
> "this is `null`." A nullable `Long?` makes the transient state visible in
> the type, which is what §45.8's `equals` relies on to distinguish "not yet
> persisted" from "persisted with id 0". See
> [Chapter 6](06-null-safety.md). **Suggestion.**

```kotlin
// bad — does not compile: 'lateinit' modifier is not allowed on properties
// of primitive types
@Entity
class OrderEntity {
    @Id @GeneratedValue lateinit var id: Long
}

// bad — compiles for a boxed id, but reading it before flush throws
@Entity
class OrderEntity {
    @Id @GeneratedValue lateinit var id: UUID
}

// good — the transient state is in the type
@Entity
class OrderEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null
}
```

## 45.12 Base entity `equals` on identity and make `hashCode` a constant.

> Why? An entity's hash code must not change over its lifetime, or it will be
> lost inside any `HashSet` or `HashMap` it was placed in before flush.
> Since the only stable identity of a generated-id entity arrives *after* the
> insert, no field-based hash can satisfy that. A constant derived from the
> class satisfies the `equals`/`hashCode` contract — equal objects hash
> equally — at the cost of degrading a same-type hash bucket to a linear scan,
> which is irrelevant for the handful of entities that live in a set. `equals`
> then compares ids and returns `false` while either side is transient, so two
> unsaved instances are equal only if they are the same object. Note the
> `other !is OrderEntity` check is proxy-safe: a Hibernate proxy is a subclass,
> so it passes, whereas `this.javaClass != other.javaClass` would not. See
> [Chapter 23](23-equality-and-ordering.md). **Suggestion.**

```kotlin
// bad — hash computed from mutable state; the entity vanishes from any set
// it was added to before persist
override fun hashCode(): Int = Objects.hash(id, customerId, status)

// bad — proxy-hostile: a lazy OrderEntity proxy has a different javaClass
override fun equals(other: Any?): Boolean =
    other != null && javaClass == other.javaClass && id == (other as OrderEntity).id

// good
override fun equals(other: Any?): Boolean {
    if (this === other) return true
    if (other !is OrderEntity) return false
    return id != null && id == other.id
}

override fun hashCode(): Int = OrderEntity::class.hashCode()
```

## 45.13 Keep every lazy association out of `toString`.

> Why? Kotlin makes this trap easier to fall into than Java does, because
> `data class` generates a `toString` over all constructor properties for
> free and the IDE generates one over all properties on request. Either way,
> a single `logger.debug("saving {}", order)` walks the lazy `lines`
> collection: inside a transaction that is a surprise N+1, and outside one it
> is a `LazyInitializationException` thrown from a *logging statement*, which
> is a genuinely awful thing to debug. List the identifier and the scalar
> fields you actually want, and nothing else. **Suggestion.**

```kotlin
// bad — logging an order loads every line, or throws
override fun toString(): String =
    "OrderEntity(id=$id, customerId=$customerId, status=$status, lines=$lines)"

// good — identifier and scalars only
override fun toString(): String =
    "OrderEntity(id=$id, customerId=$customerId, status=$status)"
```

## 45.14 Model a nullable column as a nullable Kotlin type; reserve `lateinit` for values a framework genuinely assigns before first read.

> Why? `lateinit` turns a nullability question into a runtime exception with a
> worse message, and it removes the compiler's ability to force the caller to
> handle the empty case. On an entity it is almost always wrong, because
> "loaded from a row where the column was `NULL`" is a normal state, not a
> programming error. The narrow legitimate use is a property a container
> assigns during initialisation and that is never read before then. Everything
> else takes a nullable type and a `?:` at the point of use. See
> [Chapter 6](06-null-safety.md). **Suggestion.**

```kotlin
// bad — a nullable column behind lateinit; reading it throws
// UninitializedPropertyAccessException instead of returning null
@Entity
class CustomerEntity {
    @Column(name = "phone_number")
    lateinit var phoneNumber: String
}

// good — the column's nullability is in the type
@Entity
class CustomerEntity {
    @Column(name = "phone_number")
    var phoneNumber: String? = null
}
```

## 45.15 Declare a reactive Spring Data repository as a `CoroutineCrudRepository`, with `suspend` for a single value and `Flow` for a stream.

> Why? Spring Data only wires the coroutine machinery when it recognises the
> shape: "Coroutines repositories are only discovered when the repository
> extends the `CoroutineCrudRepository` interface." The `suspend`/`Flow` split
> is not stylistic either — a suspending function returns one value and a
> `Flow` returns many, so the return type declares the cardinality of the
> query and the compiler checks it at every call site. Coroutines support
> needs `kotlinx-coroutines-core`, `kotlinx-coroutines-reactive`, and
> `kotlinx-coroutines-reactor` on the classpath. **Suggestion.**

```kotlin
// bad — a reactive repository exposing Reactor types into Kotlin code, so
// every caller has to bridge by hand
interface OrderRepository : ReactiveCrudRepository<OrderRow, UUID> {
    fun findByReference(reference: String): Mono<OrderRow>
    fun findAllByStatus(status: OrderStatus): Flux<OrderRow>
}

// good — cardinality is in the return type, and context propagates
interface OrderRepository : CoroutineCrudRepository<OrderRow, UUID> {
    suspend fun findByReference(reference: String): OrderRow?
    fun findAllByStatus(status: OrderStatus): Flow<OrderRow>
}
```

## 45.16 Never give a Coroutines repository method a plain, non-`suspend`, non-`Flow` return type.

> Why? Spring Data is explicit about the cost: `fun getUser(): User`
> "retrieve[s] data once **blocking the thread** and without context
> propagation. This should be avoided." Both halves matter. Blocking a
> coroutine's thread is §45.5. Losing context propagation means the
> reactive/coroutine context — which is where a reactive transaction lives
> (§45.3) — is unavailable to the query, so it runs outside the transaction
> you thought you were in. The documentation states the remedy directly:
> "To retain access to the context, either declare your method using `suspend`
> or return a type that enables context propagation such as `Flow`."
> **Suggestion.**

```kotlin
// bad — blocks, and runs outside the surrounding reactive transaction
interface OrderRepository : CoroutineCrudRepository<OrderRow, UUID> {
    fun findByReference(reference: String): OrderRow?
    fun findAllByStatus(status: OrderStatus): List<OrderRow>
}

// good
interface OrderRepository : CoroutineCrudRepository<OrderRow, UUID> {
    suspend fun findByReference(reference: String): OrderRow?
    suspend fun findAllByStatus(status: OrderStatus): List<OrderRow>
    fun streamAllByStatus(status: OrderStatus): Flow<OrderRow>
}
```

## 45.17 Never let a JPA entity cross a coroutine boundary; map it to a DTO inside the transaction.

> Why? `best-practice-java` §35.14 already forbids returning an entity to the
> web layer. Coroutines sharpen the rule: `withContext` is a *thread* boundary
> as well as a scope boundary, so an entity returned out of
> `withContext(ioDispatcher) { ... }` is detached, on a different thread, with
> a closed persistence context. Every lazy association on it now throws
> `LazyInitializationException` — and the throw happens wherever the caller
> happens to touch it, which with coroutines can be several suspensions and
> one dispatcher away from the query. Build the immutable `data class` inside
> the block and return that. **Suggestion.**

```kotlin
// bad — the entity leaves the transaction and the thread at the same time;
// `order.lines` throws from whichever coroutine touches it next
suspend fun load(id: UUID): OrderEntity =
    withContext(ioDispatcher) { orderReader.findById(id) }

// good — the mapping happens where the context is still open
suspend fun load(id: UUID): OrderView =
    withContext(ioDispatcher) { orderReader.viewOf(id) }

@Service
class OrderReader(private val orders: OrderRepository) {

    @Transactional(readOnly = true)
    fun viewOf(id: UUID): OrderView {
        val order = orders.findByIdWithLines(id) ?: throw OrderNotFoundException(id)
        return OrderView(
            id = requireNotNull(order.id) { "persisted order must have an id" },
            status = order.status,
            lines = order.lines.map { OrderLineView(it.sku, it.quantity) },
        )
    }
}

data class OrderView(val id: Long, val status: OrderStatus, val lines: List<OrderLineView>)
```
