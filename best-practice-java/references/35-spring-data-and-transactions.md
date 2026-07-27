<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 35. Spring: Data Access & Transactions

A Spring transaction is not a language construct. It is an AOP proxy wrapped
around a bean, and every rule in this chapter follows from that one fact.
The proxy can only see calls that arrive from outside the bean, it can only
intercept methods it is able to override, and it decides to commit or roll
back based on what escapes the method it wrapped. Almost every transaction
defect in a Spring codebase is a case of the author reasoning about
`@Transactional` as if it were a keyword.

This chapter draws on
[Spring Framework: Using `@Transactional`](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html),
[Transaction Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html),
[Transaction-bound Events](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html),
and
[Spring Boot: SQL Databases](https://docs.spring.io/spring-boot/3.4/reference/data/sql.html).
Query-shape rules cite
[Spring Data JPA: Query Methods](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html).

Three neighbouring topics live elsewhere. Bean construction and injection —
including why every collaborator here is a `final` constructor parameter —
is [Chapter 32](32-spring-beans-and-di.md). The DTO discipline that §35.14
depends on is [Chapter 34](34-spring-web-layer.md). Testing the persistence
layer is [Chapter 36](36-spring-testing.md); this chapter states what to
test, not how to wire the harness. Entity mapping design — association
types, identifier strategies, inheritance — is explicitly out of scope for
this skill, so the rules below are about *transaction boundaries and query
shape* only.

**Tool alignment:** almost nothing here is mechanically enforced. Checkstyle
and Error Prone have no model of a Spring proxy, so proxy-correctness rules
are labeled **Suggestion** and are best enforced by an ArchUnit layer test
plus review. The two exceptions are noted inline.

## 35.1 Put `@Transactional` on the application service, never on the controller and never on the repository.

> Why? The transaction boundary must match the unit of work. A controller
> boundary drags request parsing, validation, and response serialisation
> inside the transaction and holds a pooled connection for the whole HTTP
> exchange. A repository boundary is the opposite failure: each repository
> call gets its own transaction, so a two-write use case can commit the
> first write and fail the second, which is precisely the atomicity the
> transaction existed to provide. The service method is the only layer that
> knows what "one unit of work" means. **Suggestion** — enforceable with an
> ArchUnit rule that no `@Controller` or `@Repository` type is annotated
> `@Transactional`.

```java
// bad — boundary on the controller; the transaction spans JSON binding,
// validation, and response rendering
@RestController
class TransferController {
  private final TransferService transferService;

  TransferController(TransferService transferService) {
    this.transferService = transferService;
  }

  @PostMapping("/transfers")
  @Transactional
  TransferResponse transfer(@Valid @RequestBody TransferRequest request) {
    return transferService.transfer(request.from(), request.to(), request.amount());
  }
}

// good — boundary on the service, exactly around the unit of work
@RestController
class TransferController {
  private final TransferService transferService;

  TransferController(TransferService transferService) {
    this.transferService = transferService;
  }

  @PostMapping("/transfers")
  TransferResponse transfer(@Valid @RequestBody TransferRequest request) {
    return transferService.transfer(request.from(), request.to(), request.amount());
  }
}

@Service
class TransferService {
  private final AccountRepository accounts;

  TransferService(AccountRepository accounts) {
    this.accounts = accounts;
  }

  @Transactional
  TransferResponse transfer(String from, String to, BigDecimal amount) {
    accounts.debit(from, amount);
    accounts.credit(to, amount);
    return new TransferResponse(from, to, amount);
  }
}
```

## 35.2 Annotate the concrete class or its methods, never the interface.

> Why? [Spring Framework: Using `@Transactional`](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)
> states the recommendation and the reason together: "The Spring team
> recommends that you annotate methods of concrete classes with the
> `@Transactional` annotation, rather than relying on annotated methods in
> interfaces… Since Java annotations are not inherited from interfaces,
> interface-declared annotations are still not recognized by the weaving
> infrastructure when using AspectJ mode, so the aspect does not get
> applied. As a consequence, your transaction annotations may be silently
> ignored." A configuration change that flips proxying mode should not
> silently remove your transactions. **Suggestion.**

```java
// bad — annotation on the interface; silently ignored under AspectJ weaving
interface InvoiceService {
  @Transactional
  void issue(InvoiceDraft draft);
}

class DefaultInvoiceService implements InvoiceService {
  @Override
  public void issue(InvoiceDraft draft) {
    // ...
  }
}

// good
interface InvoiceService {
  void issue(InvoiceDraft draft);
}

class DefaultInvoiceService implements InvoiceService {
  @Override
  @Transactional
  public void issue(InvoiceDraft draft) {
    // ...
  }
}
```

## 35.3 Never rely on self-invocation — a `@Transactional` method called from inside the same bean runs with no transaction at all.

> Why? This is the single most expensive Spring defect, because it produces
> no error, no warning, and no log line. The reference documentation is
> unambiguous: "In proxy mode (which is the default), only external method
> calls coming in through the proxy are intercepted. This means that
> self-invocation (in effect, a method within the target object calling
> another method of the target object) does not lead to an actual
> transaction at runtime even if the invoked method is marked with
> `@Transactional`." In the worked example below, `importAll` calls
> `importOne` on `this`, so the annotation on `importOne` is inert: each row
> is written in its own auto-commit, and a failure halfway leaves the
> database in a partial state that the code appears to forbid.
> **Suggestion.**

```java
// bad — this.importOne(...) bypasses the proxy; @Transactional does nothing
@Service
class CustomerImportService {
  private final CustomerRepository customers;
  private final AuditRepository audits;

  CustomerImportService(CustomerRepository customers, AuditRepository audits) {
    this.customers = customers;
    this.audits = audits;
  }

  void importAll(List<CustomerRow> rows) {
    for (CustomerRow row : rows) {
      importOne(row); // internal call — no proxy, no transaction
    }
  }

  @Transactional
  void importOne(CustomerRow row) {
    customers.save(row.toCustomer());
    audits.record("import", row.id());
  }
}

// good (fix 1, preferred) — extract the transactional unit into its own bean
@Service
class CustomerImportService {
  private final CustomerRowImporter importer;

  CustomerImportService(CustomerRowImporter importer) {
    this.importer = importer;
  }

  void importAll(List<CustomerRow> rows) {
    for (CustomerRow row : rows) {
      importer.importOne(row); // external call through the proxy
    }
  }
}

@Service
class CustomerRowImporter {
  private final CustomerRepository customers;
  private final AuditRepository audits;

  CustomerRowImporter(CustomerRepository customers, AuditRepository audits) {
    this.customers = customers;
    this.audits = audits;
  }

  @Transactional
  public void importOne(CustomerRow row) {
    customers.save(row.toCustomer());
    audits.record("import", row.id());
  }
}
```

The other two fixes, in descending order of preference. **Fix 2** is
`TransactionTemplate` — programmatic, explicit, and immune to proxying
entirely (see §35.20). **Fix 3** is self-injection via `ObjectProvider`,
which routes the call back through the proxy; it works, but it advertises
that the bean has two responsibilities and should have been split.

```java
// acceptable (fix 2) — programmatic boundary, no proxy involved
@Service
class CustomerImportService {
  private final TransactionTemplate transactionTemplate;
  private final CustomerRepository customers;

  CustomerImportService(TransactionTemplate transactionTemplate, CustomerRepository customers) {
    this.transactionTemplate = transactionTemplate;
    this.customers = customers;
  }

  void importAll(List<CustomerRow> rows) {
    for (CustomerRow row : rows) {
      transactionTemplate.executeWithoutResult(status -> customers.save(row.toCustomer()));
    }
  }
}

// last resort (fix 3) — self-injection; a smell that the bean should split
@Service
class CustomerImportService {
  private final ObjectProvider<CustomerImportService> self;

  CustomerImportService(ObjectProvider<CustomerImportService> self) {
    this.self = self;
  }

  void importAll(List<CustomerRow> rows) {
    rows.forEach(row -> self.getObject().importOne(row));
  }

  @Transactional
  public void importOne(CustomerRow row) {
    // ...
  }
}
```

## 35.4 Never put `@Transactional` on a `private`, `static`, or `final` method.

> Why? A CGLIB proxy works by subclassing and overriding. `private` and
> `static` methods cannot be overridden, and `final` methods must not be —
> so the annotation is silently ignored in all three cases, exactly as in
> §35.3. Note the nuance the reference documentation adds for Spring
> Framework 6.x: "`protected` or package-visible methods can also be made
> transactional for class-based proxies by default," while "transactional
> methods in interface-based proxies must always be `public` and defined in
> the proxied interface." Non-`public` therefore is not automatically wrong
> — `private`, `static`, and `final` always are. **Suggestion.**

```java
// bad — private method can't be overridden; the annotation is inert
@Service
class ReportService {
  @Transactional
  private void persist(Report report) {
    // never runs in a transaction
  }
}

// bad — final method can't be overridden by the CGLIB subclass
@Service
class ReportService {
  @Transactional
  public final void persist(Report report) {
    // never runs in a transaction
  }
}

// good
@Service
class ReportService {
  @Transactional
  public void persist(Report report) {
    // ...
  }
}
```

## 35.5 Mark every query-only service method `@Transactional(readOnly = true)`.

> Why? `readOnly` is a hint that pays three ways. It sets the JDBC
> connection read-only so the driver and database can skip write-path work;
> it lets a routing `DataSource` send the statement to a read replica; and
> with Hibernate it puts the session in `FlushMode.MANUAL`, which skips
> dirty-checking on every loaded entity — the dominant cost in a large
> read. It also documents intent: a reader knows at a glance that this
> method cannot mutate anything. The reference documentation notes it is
> "Only applicable to values of `REQUIRED` or `REQUIRES_NEW`", so a
> `readOnly` flag on a `SUPPORTS` method is decoration, not behaviour.
> **Suggestion.**

```java
// bad — read path pays for dirty-checking and pins a read-write connection
@Service
class CatalogService {
  private final ProductRepository products;

  CatalogService(ProductRepository products) {
    this.products = products;
  }

  @Transactional
  public List<ProductSummary> search(String term, Pageable pageable) {
    return products.search(term, pageable).map(ProductSummary::from).toList();
  }
}

// good
@Service
class CatalogService {
  private final ProductRepository products;

  CatalogService(ProductRepository products) {
    this.products = products;
  }

  @Transactional(readOnly = true)
  public List<ProductSummary> search(String term, Pageable pageable) {
    return products.search(term, pageable).map(ProductSummary::from).toList();
  }
}
```

## 35.6 Leave propagation at the default `REQUIRED` unless you can name the reason another value is correct.

> Why? `REQUIRED` "enforces a physical transaction, either locally for the
> current scope if no transaction exists yet or participating in an existing
> 'outer' transaction." That is what almost every service method wants: join
> the caller's unit of work if there is one, otherwise start one. Choosing a
> non-default propagation without a stated reason is how a codebase acquires
> transactions that commit independently of the business operation they
> belong to. **Suggestion.**

```java
// bad — REQUIRES_NEW copied from another method; the audit row now commits
// even when the order that produced it rolls back
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void placeOrder(OrderRequest request) {
  orders.save(request.toOrder());
  audits.record("order.placed", request.id());
}

// good
@Transactional
public void placeOrder(OrderRequest request) {
  orders.save(request.toOrder());
  audits.record("order.placed", request.id());
}
```

## 35.7 Use `REQUIRES_NEW` only when the inner work must survive the outer rollback, and budget a second connection for it.

> Why? `REQUIRES_NEW` "always uses an independent physical transaction for
> each affected transaction scope, never participating in an existing
> transaction for an outer scope," and it suspends the outer transaction
> while the inner one runs. That is exactly right for a failure-audit row
> that must persist even when the business transaction rolls back. It is
> exactly wrong for anything that should be atomic with the caller. The cost
> is real: each nested `REQUIRES_NEW` holds a second pooled connection for
> the duration, so a pool sized for N concurrent requests will deadlock at
> N/2 if every request opens one. **Suggestion.**

```java
// bad — the "new" transaction is atomic work that should have joined the
// caller, and it silently commits when placeOrder later fails
@Transactional
public void placeOrder(OrderRequest request) {
  Order order = orders.save(request.toOrder());
  reserveStock(order); // @Transactional(REQUIRES_NEW) — stock stays reserved
  payments.charge(order);
}

// good — REQUIRES_NEW reserved for work that must outlive an outer rollback
@Service
class FailureAuditService {
  private final AuditRepository audits;

  FailureAuditService(AuditRepository audits) {
    this.audits = audits;
  }

  @Transactional(propagation = Propagation.REQUIRES_NEW)
  public void recordFailure(String operation, String reason) {
    audits.record(operation, reason);
  }
}
```

## 35.8 Use `NESTED` only on a JDBC-backed transaction manager, and only for a partial rollback you will actually recover from.

> Why? "`PROPAGATION_NESTED` uses a single physical transaction with
> multiple savepoints that it can roll back to… This setting is typically
> mapped onto JDBC savepoints, so it works only with JDBC resource
> transactions." On a `JpaTransactionManager` it will throw rather than
> quietly degrade, and on JTA it is not supported at all. Reach for it only
> when the outer transaction genuinely continues after the inner scope
> fails; if you are not writing the recovery branch, you wanted `REQUIRED`.
> **Suggestion.**

```java
// bad — NESTED on a JPA transaction manager; fails at runtime, and the
// caller has no recovery branch anyway
@Transactional(propagation = Propagation.NESTED)
public void applyOptionalDiscount(long orderId, String code) {
  discounts.apply(orderId, code);
}

// good — savepoint semantics on a JDBC manager, with an explicit recovery
@Transactional
public ImportOutcome importBatch(List<Row> rows) {
  List<String> skipped = new ArrayList<>();
  for (Row row : rows) {
    try {
      rowImporter.importWithSavepoint(row); // @Transactional(NESTED)
    } catch (DataIntegrityViolationException e) {
      skipped.add(row.id()); // outer transaction continues past the savepoint
    }
  }
  return new ImportOutcome(rows.size() - skipped.size(), skipped);
}
```

## 35.9 Declare `rollbackFor` when a checked exception must roll back the transaction.

> Why? The default rule is narrow and surprising: "Any `RuntimeException` or
> `Error` triggers rollback, and any checked `Exception` does not." A
> service that throws a checked `InsufficientFundsException` after
> half-writing its state will *commit* that half-write. Either declare
> `rollbackFor`, or — better, and consistent with
> [Chapter 24](24-exceptions.md) — make the exception unchecked so the
> default rule is already correct. Spring Framework 6.2 (Spring Boot 3.4+)
> also allows flipping the global default with
> `@EnableTransactionManagement(rollbackOn = RollbackOn.ALL_EXCEPTIONS)`;
> if you adopt it, adopt it once, at the configuration class, not
> per-method. **Suggestion.**

```java
// bad — checked exception does not roll back; the debit is committed
@Transactional
public void withdraw(String account, BigDecimal amount) throws InsufficientFundsException {
  accounts.debit(account, amount);
  if (accounts.balanceOf(account).signum() < 0) {
    throw new InsufficientFundsException(account);
  }
}

// good (option A) — declare the rollback rule explicitly
@Transactional(rollbackFor = InsufficientFundsException.class)
public void withdraw(String account, BigDecimal amount) throws InsufficientFundsException {
  accounts.debit(account, amount);
  if (accounts.balanceOf(account).signum() < 0) {
    throw new InsufficientFundsException(account);
  }
}

// good (option B, preferred) — an unchecked exception needs no special rule
@Transactional
public void withdraw(String account, BigDecimal amount) {
  accounts.debit(account, amount);
  if (accounts.balanceOf(account).signum() < 0) {
    throw new InsufficientFundsException(account); // extends RuntimeException
  }
}
```

## 35.10 Never catch an exception inside a transactional method and continue as if nothing happened.

> Why? By the time your `catch` block runs, the proxy has already marked the
> transaction rollback-only. Swallowing the exception does not un-mark it;
> it only defers the failure to commit time, where the caller receives an
> `UnexpectedRollbackException` from a stack frame that has nothing to do
> with the real cause. The reference documentation describes exactly this:
> "if an inner transaction (of which the outer caller is not aware) silently
> marks a transaction as rollback-only, the outer caller still calls commit.
> The outer caller needs to receive an `UnexpectedRollbackException` to
> indicate clearly that a rollback was performed instead." If the work is
> genuinely optional, it belongs in a `REQUIRES_NEW` bean (§35.7) or after
> the commit (§35.12) — not in a `catch` inside the boundary.
> **Suggestion.** See also
> [Chapter 24](24-exceptions.md) on swallowed exceptions generally.

```java
// bad — the catch hides nothing; commit throws UnexpectedRollbackException
// from a frame that never mentions the constraint violation
@Transactional
public void register(Signup signup) {
  users.save(signup.toUser());
  try {
    newsletter.subscribe(signup.email()); // writes via the same transaction
  } catch (DataIntegrityViolationException e) {
    log.warn("newsletter subscribe failed for {}", signup.email(), e);
  }
}

// good — the optional work runs in its own transaction and can fail alone
@Transactional
public void register(Signup signup) {
  users.save(signup.toUser());
  newsletterSubscriber.subscribeInNewTransaction(signup.email());
}

@Service
class NewsletterSubscriber {
  @Transactional(propagation = Propagation.REQUIRES_NEW)
  public void subscribeInNewTransaction(String email) {
    // ...
  }
}
```

When you deliberately want to abort the transaction without throwing to the
caller, say so explicitly rather than relying on the implicit marker:

```java
// good — explicit rollback-only, so the intent is in the source
@Transactional
public RegistrationResult register(Signup signup) {
  if (!users.reserve(signup.email())) {
    TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
    return RegistrationResult.duplicate(signup.email());
  }
  users.save(signup.toUser());
  return RegistrationResult.created(signup.email());
}
```

## 35.11 Never perform an HTTP call, a message publish, a file write, or any other remote IO inside a transaction.

> Why? A transaction holds a pooled database connection and, on most
> isolation levels, row locks. A remote call inside that scope ties the
> lifetime of both to a service you do not control: a 30-second HTTP timeout
> becomes a 30-second lock. The failure mode is a connection-pool exhaustion
> cascade under exactly the conditions — a slow downstream — where you most
> need the database to stay responsive. It is also semantically wrong: you
> cannot roll back a sent message. **Suggestion.**

```java
// bad — the payment gateway's latency is now the row lock's duration
@Transactional
public void checkout(long orderId) {
  Order order = orders.findById(orderId).orElseThrow();
  PaymentReceipt receipt = paymentGateway.charge(order.total()); // remote HTTP
  order.markPaid(receipt.reference());
  orders.save(order);
}

// good — remote call outside the boundary; each transaction is short
public void checkout(long orderId) {
  OrderSnapshot snapshot = orderService.loadForCheckout(orderId); // @Transactional(readOnly)
  PaymentReceipt receipt = paymentGateway.charge(snapshot.total());
  orderService.markPaid(orderId, receipt.reference()); // @Transactional
}
```

## 35.12 Publish post-commit side effects with `@TransactionalEventListener`, not from inside the transactional method.

> Why? An event published and handled synchronously inside the boundary runs
> before the commit, so a downstream consumer can observe — or act on — a
> row that is about to disappear. `@TransactionalEventListener` defaults to
> `TransactionPhase.AFTER_COMMIT`, which is the correct default for
> "tell the world this happened": the listener runs only if the transaction
> actually committed, and it is skipped entirely if no transaction is
> running. **Suggestion.**

```java
// bad — the email goes out before commit; a later rollback can't recall it
@Transactional
public void placeOrder(OrderRequest request) {
  Order order = orders.save(request.toOrder());
  mailer.sendConfirmation(order); // fires inside the transaction
}

// good
@Transactional
public void placeOrder(OrderRequest request) {
  Order order = orders.save(request.toOrder());
  events.publishEvent(new OrderPlaced(order.id(), order.customerEmail()));
}

@Component
class OrderConfirmationMailer {
  private final Mailer mailer;

  OrderConfirmationMailer(Mailer mailer) {
    this.mailer = mailer;
  }

  @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
  public void onOrderPlaced(OrderPlaced event) {
    mailer.sendConfirmation(event.orderId(), event.customerEmail());
  }
}
```

## 35.13 Set `spring.jpa.open-in-view=false` and fetch everything you need inside the transaction.

> Why? [Spring Boot: SQL Databases](https://docs.spring.io/spring-boot/3.4/reference/data/sql.html)
> describes the default: "If you are running a web application, Spring Boot
> by default registers `OpenEntityManagerInViewInterceptor` to apply the
> 'Open EntityManager in View' pattern, to allow for lazy loading in web
> views." That convenience is the problem. It keeps the persistence context
> — and its connection — open for the whole request, so lazy loads succeed
> during response serialisation and issue unbounded, invisible queries from
> the view layer. Turning it off converts those hidden queries into a loud
> `LazyInitializationException` at development time, which is where you want
> to find them. Spring Boot also logs a startup warning when the property is
> left unset, which is the framework asking you to make the choice
> explicitly. **Suggestion.**

```properties
# bad — the default: lazy loads leak into view rendering, invisibly
# (property absent)

# good
spring.jpa.open-in-view=false
```

```java
// bad — relies on open-in-view; the lazy collection loads during
// serialisation, outside any transaction you declared
@Transactional(readOnly = true)
public Order load(long id) {
  return orders.findById(id).orElseThrow();
}

// good — fetch what the caller needs, inside the boundary
@Transactional(readOnly = true)
public OrderDetail load(long id) {
  Order order = orders.findByIdWithLines(id).orElseThrow(() -> new OrderNotFoundException(id));
  return OrderDetail.from(order);
}
```

## 35.14 Never return a JPA entity across the transactional boundary to the web layer.

> Why? An entity outside its persistence context is a half-object: every
> lazy association throws `LazyInitializationException` on access, and with
> `open-in-view` disabled (§35.13) that is guaranteed rather than
> occasional. Worse, serialising an entity publishes your schema as your API
> contract, so a column rename becomes a breaking change for clients. Map to
> a `record` DTO inside the transaction and return that.
> [Chapter 34](34-spring-web-layer.md) states the API-contract half of this
> rule; this is the persistence half. **Suggestion** — enforceable with an
> ArchUnit rule that no `@Entity` type appears in a controller signature.

```java
// bad — entity crosses the boundary; lazy fields explode during rendering
@Transactional(readOnly = true)
public Customer find(long id) {
  return customers.findById(id).orElseThrow();
}

// good — a record built while the context is still open
public record CustomerView(long id, String name, String email, List<String> tags) {
  static CustomerView from(Customer customer) {
    return new CustomerView(
        customer.getId(),
        customer.getName(),
        customer.getEmail(),
        customer.getTags().stream().map(Tag::getLabel).toList());
  }
}

@Transactional(readOnly = true)
public CustomerView find(long id) {
  Customer customer = customers.findById(id).orElseThrow(() -> new CustomerNotFoundException(id));
  return CustomerView.from(customer); // tags resolved inside the transaction
}
```

## 35.15 Fix an N+1 query with a fetch join, an entity graph, or a projection — never by making the association eager.

> Why? An N+1 is one query for the parents plus one per parent for the
> children, so a page of 50 orders issues 51 round trips. Switching the
> association to `FetchType.EAGER` "fixes" that call site and breaks every
> other one, because the join is now unconditional — including on the
> queries that never touch the association. The three targeted fixes each
> keep the association lazy and opt in per query: a JPQL `join fetch`, a
> Spring Data `@EntityGraph(attributePaths = …)`, or an interface/DTO
> projection that never loads the entity at all. Detect the problem by
> logging SQL in tests (`spring.jpa.properties.hibernate.show_sql`) or by
> asserting the statement count. **Suggestion.**

```java
// bad — one query for orders, then one per order for its lines
@Query("select o from Order o where o.customerId = :customerId")
List<Order> findByCustomer(@Param("customerId") long customerId);

// bad — "fixing" it on the mapping punishes every other query
@OneToMany(mappedBy = "order", fetch = FetchType.EAGER)
private List<OrderLine> lines;

// good (option A) — explicit fetch join, scoped to this query
@Query("select distinct o from Order o join fetch o.lines where o.customerId = :customerId")
List<Order> findByCustomerWithLines(@Param("customerId") long customerId);

// good (option B) — entity graph, same effect without hand-written JPQL
@EntityGraph(attributePaths = {"lines"})
List<Order> findByCustomerId(long customerId);

// good (option C) — projection; the association is never loaded
interface OrderSummary {
  long getId();

  BigDecimal getTotal();
}

List<OrderSummary> findSummaryByCustomerId(long customerId);
```

## 35.16 Return `Slice` when the caller does not need a total, and give every `@Query`-backed `Page` method an explicit `countQuery`.

> Why? `Page` costs two queries: the page itself and a `count(*)` over the
> whole filtered set. On a large table with a non-trivial `where` clause the
> count is frequently the more expensive of the two, and an infinite-scroll
> UI never reads it. `Slice` fetches `limit + 1` rows and reports only
> `hasNext()`. When you do need a `Page` from a custom `@Query`, Spring Data
> derives the count query by rewriting your JPQL, and that derivation is
> wrong as soon as the query has joins it does not need for counting —
> supply `countQuery` yourself. **Suggestion.**

```java
// bad — infinite scroll pays for a full count on every page
@Query("select o from Order o where o.status = :status")
Page<Order> findByStatus(@Param("status") OrderStatus status, Pageable pageable);

// good (option A) — no total needed, so don't compute one
@Query("select o from Order o where o.status = :status")
Slice<Order> findByStatus(@Param("status") OrderStatus status, Pageable pageable);

// good (option B) — total genuinely needed; the count query drops the join
// that only exists to shape the selected rows
@Query(
    value =
        "select o from Order o join o.customer c "
            + "where o.status = :status and c.region = :region",
    countQuery =
        "select count(o) from Order o join o.customer c "
            + "where o.status = :status and c.region = :region")
Page<Order> findByStatusAndRegion(
    @Param("status") OrderStatus status, @Param("region") String region, Pageable pageable);
```

One combination is always wrong: a **collection** `join fetch` together with a
`Pageable`. Hibernate cannot apply a SQL `limit` to a result set whose rows
have been multiplied by the join without cutting a collection in half, so it
loads the *entire* result set and paginates in memory — logging
`HHH000104: firstResult/maxResults specified with collection fetch; applying
in memory!`. Page two of a large table therefore materialises the whole
table. Fetch the page of root entities first, then load their collections in
a second query (an entity graph on a `findAllById` call, or Hibernate's
`@BatchSize`), and set
`spring.jpa.properties.hibernate.query.fail_on_pagination_over_collection_fetch=true`
so the mistake fails loudly instead of quietly consuming the heap.

```java
// bad — collection fetch join plus Pageable: full table into memory
@Query("select distinct o from Order o join fetch o.lines where o.status = :status")
Page<Order> findByStatus(@Param("status") OrderStatus status, Pageable pageable);

// good — page the roots, then fetch the collections for that page only
@Query("select o.id from Order o where o.status = :status")
Page<Long> findIdsByStatus(@Param("status") OrderStatus status, Pageable pageable);

@EntityGraph(attributePaths = {"lines"})
List<Order> findByIdIn(Collection<Long> ids);
```

## 35.17 Cap the page size the caller may request; never pass a client-supplied `Pageable` straight through.

> Why? `Pageable` is bound from query parameters, so `?size=1000000` is a
> single-request denial of service: it materialises a million rows into the
> persistence context and the heap. Spring Data's
> `spring.data.web.pageable.max-page-size` property caps the bound value
> globally; where you construct the `Pageable` yourself, clamp it in code so
> the bound is visible at the call site. **Suggestion.**

```java
// bad — the client chooses how much of your heap to consume
@GetMapping("/orders")
Page<OrderView> list(OrderFilter filter, Pageable pageable) {
  return orderService.search(filter, pageable);
}

// good — bounded in configuration
// application.properties:
//   spring.data.web.pageable.max-page-size=100
//   spring.data.web.pageable.default-page-size=20

// good — bounded in code where the Pageable is constructed
private static final int MAX_PAGE_SIZE = 100;

Pageable bounded(int page, int size, Sort sort) {
  return PageRequest.of(Math.max(page, 0), Math.clamp(size, 1, MAX_PAGE_SIZE), sort);
}
```

## 35.18 In a batch write, flush and clear the persistence context on a fixed interval, and configure the JDBC batch size to match.

> Why? Hibernate keeps every entity you persist in the first-level cache
> until the transaction ends, so a 100 000-row insert holds 100 000 managed
> entities and dirty-checks all of them on every flush — quadratic work
> ending in an `OutOfMemoryError`. Flushing and clearing on an interval
> bounds the context. Separately, without `hibernate.jdbc.batch_size` the
> driver sends one `INSERT` per row regardless of how you loop, so both
> settings are needed: the flush bounds memory, the batch size bounds round
> trips. Keep the interval and the batch size equal so each flush emits
> exactly one batch. **Suggestion.**

```properties
# good — without this, every insert is its own round trip
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

```java
// bad — 100 000 managed entities, dirty-checked on every flush
@Transactional
public void importAll(List<CustomerRow> rows) {
  for (CustomerRow row : rows) {
    entityManager.persist(row.toCustomer());
  }
}

// good — bounded context, one JDBC batch per flush
private static final int BATCH_SIZE = 50;

@Transactional
public void importAll(List<CustomerRow> rows) {
  for (int i = 0; i < rows.size(); i++) {
    entityManager.persist(rows.get(i).toCustomer());
    if ((i + 1) % BATCH_SIZE == 0) {
      entityManager.flush();
      entityManager.clear();
    }
  }
  entityManager.flush();
  entityManager.clear();
}
```

## 35.19 Never call a `@Transactional` method from `@PostConstruct` or from a constructor.

> Why? The reference documentation states the constraint directly: "the
> proxy must be fully initialized to provide the expected behavior, so you
> should not rely on this feature in your initialization code — for example,
> in a `@PostConstruct` method." At `@PostConstruct` time you are the raw
> target object, not the proxy, so this is §35.3 with a lifecycle twist —
> and it is worse, because the call also happens before the transaction
> infrastructure is guaranteed to be ready. Do startup work in an
> `ApplicationRunner` or an `ApplicationReadyEvent` listener, both of which
> run against the finished context. **Suggestion.**

```java
// bad — runs before the proxy exists; no transaction, possibly no manager
@Service
class ReferenceDataService {
  @PostConstruct
  void warmUp() {
    loadDefaults(); // @Transactional — inert here
  }

  @Transactional
  public void loadDefaults() {
    // ...
  }
}

// good — runs after the context is fully refreshed, through the proxy
@Component
class ReferenceDataWarmUp implements ApplicationRunner {
  private final ReferenceDataService referenceData;

  ReferenceDataWarmUp(ReferenceDataService referenceData) {
    this.referenceData = referenceData;
  }

  @Override
  public void run(ApplicationArguments args) {
    referenceData.loadDefaults();
  }
}
```

## 35.20 Use `TransactionTemplate` when the transactional scope is narrower than a whole method.

> Why? `@Transactional` can only bracket an entire method, so a method that
> does one short write surrounded by expensive preparation must either
> extend the transaction over the preparation (violating §35.11) or be split
> into two beans purely to satisfy the proxy. `TransactionTemplate` puts the
> boundary exactly where the work is, is immune to self-invocation, and
> makes the scope visible in the source rather than in an annotation
> elsewhere. It is the right tool for loops, for retry wrappers, and for any
> code where a reader would otherwise have to trace a proxy to know whether
> a transaction is open. **Suggestion.**

```java
// bad — the boundary is the whole method, so the CSV parse and the S3 read
// both run inside the transaction
@Transactional
public ImportResult importFromFile(String key) {
  byte[] bytes = objectStore.read(key);        // remote IO inside the transaction
  List<CustomerRow> rows = CsvParser.parse(bytes); // CPU work inside it too
  rows.forEach(row -> customers.save(row.toCustomer()));
  return ImportResult.of(rows.size());
}

// good — the transaction brackets only the write
public ImportResult importFromFile(String key) {
  byte[] bytes = objectStore.read(key);
  List<CustomerRow> rows = CsvParser.parse(bytes);
  transactionTemplate.executeWithoutResult(
      status -> rows.forEach(row -> customers.save(row.toCustomer())));
  return ImportResult.of(rows.size());
}
```

## 35.21 Test the persistence layer against the real database engine, not H2.

> Why? Everything in this chapter — lock behaviour, savepoints, `readOnly`
> routing, batch inserts, the exact SQL a fetch join generates — is
> engine-specific. H2's PostgreSQL compatibility mode diverges on precisely
> the features you are trying to verify: upserts, JSON columns, partial
> indexes, `for update skip locked`, and error codes for constraint
> violations. A green H2 suite that fails in production is worse than no
> suite, because it consumed the budget you would have spent on a real one.
> Use `@DataJpaTest` with `@AutoConfigureTestDatabase(replace = NONE)` and a
> Testcontainers instance; [Chapter 36, §36.14-§36.16](36-spring-testing.md)
> covers the harness in full. **Suggestion.**

```java
// bad — the in-memory replacement is a different database
@DataJpaTest
class OrderRepositoryTest {
  // Boot swaps in an embedded H2 DataSource by default
}

// good — the engine under test is the engine you ship
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {
  @Container @ServiceConnection
  static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

  @Autowired private OrderRepository orders;

  @Test
  void findByCustomerWithLines_loadsLinesInOneQuery() {
    // ...
  }
}
```
