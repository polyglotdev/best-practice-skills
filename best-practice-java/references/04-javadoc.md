<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 4. Javadoc

Javadoc is the only part of a Java codebase that is compiled for humans.
It has a formal grammar, a required position, a mandatory shape for its
first sentence, and a fixed tag order — and Google's guide legislates all
of it in [§7](https://google.github.io/styleguide/javaguide.html#s7-javadoc).
The first half of this chapter is that specification:
[§7.1 formatting](https://google.github.io/styleguide/javaguide.html#s7.1-javadoc-formatting),
[§7.2 the summary
fragment](https://google.github.io/styleguide/javaguide.html#s7.2-summary-fragment),
and [§7.3 where Javadoc is
used](https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required).

The second half is the part no style guide states and every reviewer
wishes someone had: what to actually put in the comment. Javadoc that
restates the signature is worse than no Javadoc, because it costs the same
to maintain and goes stale just as fast while telling a reader nothing they
could not read off the declaration. The rules from 4.14 onward are about
documenting the *contract* — nullability, thread safety, ownership,
encounter order, and the unchecked exceptions a caller must be ready for.

This chapter covers documentation comments only. Implementation comments
(`//` inside a method body), commented-out code, and `TODO` conventions
belong to [Chapter 5](05-comments-and-todos.md). The nullability
*annotations* that back rule 4.15 are
[Chapter 25](25-nullability.md)'s subject; here we only require that the
contract be stated in prose. Exception design — checked versus unchecked,
what to throw and when — is [Chapter 24](24-exceptions.md).

**Tool alignment:** Javadoc is unusually well covered by static analysis.
Checkstyle contributes `SummaryJavadoc`, `JavadocMethod`,
`MissingJavadocType`, `MissingJavadocMethod`, `AtclauseOrder`,
`NonEmptyAtclauseDescription`, `JavadocTagContinuationIndentation`,
`JavadocParagraph`, `RequireEmptyLineBeforeBlockTagGroup`,
`SingleLineJavadoc`, `JavadocBlockTagLocation`, and
`InvalidJavadocPosition`. Error Prone contributes `MissingSummary`,
`EmptyBlockTag`, `InvalidParam`, `InvalidLink`, `InvalidBlockTag`,
`InvalidInlineTag`, `InvalidThrows`, `InheritDoc`, `ReturnFromVoid`,
`EscapedEntity`, `UnescapedEntity`, and `AlmostJavadoc`. Rules that depend
on judgement are marked **Suggestion**.

## 4.1 Write Javadoc in the multi-line block form, and use the single-line form only when the entire comment fits on one line with no block tags.

> Why? [§7.1.1](https://google.github.io/styleguide/javaguide.html#s7.1.1-javadoc-multi-line)
> defines the two permitted shapes and constrains the short one: the
> single-line form "may be substituted when the entirety of the Javadoc
> block (including comment markers) can fit on a single line", and adds
> that "this only applies when there are no block tags such as `@param`."
> Squeezing a `@param` onto a
> single line produces a comment the doclet parses differently from how it
> reads, and the first line-length change silently reformats it into
> something ugly.
> **Violation — enforced by Checkstyle `SingleLineJavadoc`.**

```java
// bad — single-line form carrying a block tag
/** Returns the customer ID. @return the customer ID */
public CustomerId customerId() { ... }

// good — short and tag-free, so the single-line form is legal
/** An immutable snapshot of one warehouse's stock levels. */
public record InventorySnapshot(WarehouseId warehouse, Map<Sku, Integer> quantities) {}

// good — block tags force the multi-line form
/**
 * Returns the stock level for {@code sku}, or zero if the warehouse has never
 * carried it.
 *
 * @param sku the stock-keeping unit to look up
 * @return the on-hand quantity, never negative
 */
public int quantityOf(Sku sku) { ... }
```

## 4.2 Open every Javadoc block with a summary fragment — a noun phrase or a verb phrase, not a complete sentence.

> Why? [§7.2](https://google.github.io/styleguide/javaguide.html#s7.2-summary-fragment)
> requires that "each Javadoc block begins with a brief summary fragment",
> and that this fragment "is a fragment — a noun phrase or verb phrase, not
> a complete sentence." The reason is mechanical rather than aesthetic: the
> doclet lifts exactly this fragment into the class and method summary
> tables, where it appears in a single narrow column next to dozens of
> siblings. A fragment scans in that table; a full sentence with a subject
> does not, and a missing fragment leaves the row blank.
> **Violation — enforced by Checkstyle `SummaryJavadoc` and Error Prone
> `MissingSummary` ("A summary line is required on public/protected
> Javadocs").**

```java
// bad — no summary at all; the index row renders empty
/**
 * @param sku the stock-keeping unit
 * @return the quantity on hand
 */
public int quantityOf(Sku sku) { ... }

// good — verb phrase, third person, no subject
/**
 * Returns the quantity of {@code sku} currently on hand.
 *
 * @param sku the stock-keeping unit to look up
 * @return the on-hand quantity, never negative
 */
public int quantityOf(Sku sku) { ... }
```

## 4.3 Never open a summary with "A `Foo` is a...", "This method returns...", or a bare imperative sentence.

> Why? [§7.2](https://google.github.io/styleguide/javaguide.html#s7.2-summary-fragment)
> names all three failure modes explicitly: the fragment "does not begin
> with `A {@code Foo} is a...`, or `This method returns...`, nor does it
> form a complete imperative sentence like `Save the record.`" The first
> two waste the summary column restating what the reader already knows from
> the declaration they clicked. The imperative is subtler and far more
> common — "Save the record." reads as an instruction to the *reader*
> rather than a description of what the method does; the correct third-person
> form is "Saves the record."
> **Violation — enforced by Checkstyle `SummaryJavadoc`, whose Google
> configuration sets `forbiddenSummaryFragments` to match `@return the`,
> `This method returns`, and `A {@code Foo} is a`.**

```java
// bad — restates the declaration
/** A {@code CustomerId} is a wrapper around a UUID. */
public record CustomerId(UUID value) {}

// bad — announces itself instead of describing behaviour
/** This method returns the total price of the order. */
public Money total() { ... }

// bad — imperative; instructs the reader rather than describing the method
/** Save the record. */
public void save(Order order) { ... }

// good
/** An opaque, immutable identifier for one customer. */
public record CustomerId(UUID value) {}

/** Returns the total price of every line item, including tax. */
public Money total() { ... }

/** Saves {@code order}, overwriting any previously stored revision. */
public void save(Order order) { ... }
```

## 4.4 Capitalize and punctuate the summary fragment as if it were a complete sentence.

> Why? [§7.2](https://google.github.io/styleguide/javaguide.html#s7.2-summary-fragment)
> pairs the fragment requirement with a formatting one: the fragment "is
> capitalized and punctuated as if it were a complete sentence." The
> trailing period is what the doclet uses to find the end of the summary —
> omit it and the doclet keeps consuming text into the summary column until
> it hits one, dragging the second and third sentences into the index.
> **Violation — enforced by Checkstyle `SummaryJavadoc`, which reports a
> first sentence missing its ending period. The capitalization half needs
> configuration: Google's Checkstyle configuration gets it by appending
> `^[a-z]` to `forbiddenSummaryFragments`.**

```java
// bad — no capital, no period; the doclet swallows the next sentence too
/**
 * returns the total price of every line item
 *
 * <p>Tax is applied per jurisdiction.
 */
public Money total() { ... }

// good
/**
 * Returns the total price of every line item, including tax.
 *
 * <p>Tax is applied per jurisdiction using the rate in effect at
 * {@link #placedAt()}.
 */
public Money total() { ... }
```

## 4.5 Never let a `@return` tag stand in for the summary — write `Returns ...` or use `{@return ...}`.

> Why? [§7.2](https://google.github.io/styleguide/javaguide.html#s7.2-summary-fragment)
> singles this out: avoid `/** @return the customer ID */` and write
> `/** Returns the customer ID. */` or `/** {@return the customer ID} */`
> instead. A block tag is not a summary, so the doclet leaves the summary
> column blank and the method becomes invisible in the index. The inline
> `{@return}` form — added to the standard doclet in JDK 16 and available
> throughout Java 21 — solves the duplication properly: it supplies both
> the first sentence of the description *and* the "Returns" section from a
> single phrase.
> **Violation — enforced by Error Prone `MissingSummary` and Checkstyle
> `SummaryJavadoc`.**

```java
// bad — a block tag masquerading as a summary
/** @return the customer ID */
public CustomerId customerId() { ... }

// good — explicit prose summary plus a block tag
/**
 * Returns the customer ID.
 *
 * @return the customer ID, never {@code null}
 */
public CustomerId customerId() { ... }

// good — {@return} generates both the summary and the Returns section
/** {@return the customer ID, never {@code null}} */
public CustomerId customerId() { ... }
```

## 4.6 Separate paragraphs with a blank aligned-asterisk line, and open every paragraph after the first with `<p>`.

> Why? [§7.1.2](https://google.github.io/styleguide/javaguide.html#s7.1.2-javadoc-paragraphs)
> requires "one blank line — that is, a line containing only the aligned
> leading asterisk (`*`) — ... between paragraphs, and before the group of
> block tags if present", with `<p>` placed "immediately before the first
> word, with no space after it." Javadoc is rendered as HTML, and HTML
> collapses newlines: without the `<p>`, three carefully separated
> paragraphs render as one unbroken wall of text.
> **Violation — enforced by Checkstyle `JavadocParagraph` and
> `RequireEmptyLineBeforeBlockTagGroup`.**

```java
// bad — no <p>, no blank line before the block tags; renders as one blob
/**
 * Reserves stock for an order.
 * Reservations expire after fifteen minutes.
 * @param order the order to reserve against
 */
public Reservation reserve(Order order) { ... }

// bad — space after <p>
/**
 * Reserves stock for an order.
 *
 * <p> Reservations expire after fifteen minutes.
 */
public Reservation reserve(Order order) { ... }

// good
/**
 * Reserves stock for an order.
 *
 * <p>Reservations expire fifteen minutes after creation and are released
 * automatically by the sweeper.
 *
 * @param order the order to reserve stock against
 * @return the reservation, which the caller must confirm or cancel
 */
public Reservation reserve(Order order) { ... }
```

## 4.7 Don't precede a block-level HTML element with `<p>`.

> Why? [§7.1.2](https://google.github.io/styleguide/javaguide.html#s7.1.2-javadoc-paragraphs)
> ends with the exception most people miss: "HTML tags for other block-level
> elements, such as `<ul>` or `<table>`, are *not* preceded with `<p>`."
> `<p>` opens a paragraph, and a `<ul>` is not paragraph content — the
> browser closes the empty paragraph before the list, leaving a stray blank
> line in the rendered output that no reviewer ever notices in source.

```java
// bad — <p> immediately before a list produces an empty rendered paragraph
/**
 * Reserves stock for an order.
 *
 * <p>
 * <ul>
 *   <li>Reservations expire after fifteen minutes.
 *   <li>Confirming a reservation is idempotent.
 * </ul>
 */
public Reservation reserve(Order order) { ... }

// good
/**
 * Reserves stock for an order.
 *
 * <ul>
 *   <li>Reservations expire after fifteen minutes.
 *   <li>Confirming a reservation is idempotent.
 * </ul>
 */
public Reservation reserve(Order order) { ... }
```

## 4.8 Emit block tags in the order `@param`, `@return`, `@throws`, `@deprecated`.

> Why? [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> fixes the sequence: "any of the standard 'block tags' that are used
> appear in the order `@param`, `@return`, `@throws`, `@deprecated`."
> A fixed order means a reader
> scanning a page of unfamiliar API knows where to look for the throws
> clause without reading the whole block, and it makes diffs on
> documentation minimal instead of reordering churn.
> **Violation — enforced by Checkstyle `AtclauseOrder`.**

```java
// bad — @throws before @param, @return last
/**
 * Transfers {@code amount} between two accounts.
 *
 * @throws InsufficientFundsException if {@code source} cannot cover the amount
 * @param source the account to debit
 * @param destination the account to credit
 * @param amount the amount to move, strictly positive
 * @return the resulting ledger entry
 */
public LedgerEntry transfer(Account source, Account destination, Money amount) { ... }

// good
/**
 * Transfers {@code amount} between two accounts.
 *
 * @param source the account to debit
 * @param destination the account to credit
 * @param amount the amount to move, strictly positive
 * @return the resulting ledger entry
 * @throws InsufficientFundsException if {@code source} cannot cover the amount
 */
public LedgerEntry transfer(Account source, Account destination, Money amount) { ... }
```

## 4.9 Never write `@param`, `@return`, `@throws`, or `@deprecated` with an empty description.

> Why? [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> states that "these four types never appear with an empty description." An
> empty tag is pure cost: it renders as a labelled row with nothing in it,
> it satisfies naive "has Javadoc" tooling, and it actively conceals the
> fact that the parameter is undocumented. `@deprecated` with no
> description is the worst offender — it tells a caller to stop using the
> method without telling them what to use instead.
> **Violation — enforced by Checkstyle `NonEmptyAtclauseDescription` and
> Error Prone `EmptyBlockTag` ("A block tag (@param, @return, @throws,
> @deprecated) has an empty description").**

```java
// bad — three empty tags and a deprecation with no migration path
/**
 * Reserves stock.
 *
 * @param order
 * @return
 * @deprecated
 */
@Deprecated
public Reservation reserve(Order order) { ... }

// good
/**
 * Reserves stock for an order.
 *
 * @param order the order to reserve stock against
 * @return the reservation, which the caller must confirm or cancel
 * @deprecated since 4.2, use {@link #reserve(Order, Duration)} to set an
 *     explicit expiry; this overload will be removed in 5.0
 */
@Deprecated(since = "4.2", forRemoval = true)
public Reservation reserve(Order order) { ... }
```

## 4.10 Indent block-tag continuation lines four or more spaces from the `@`.

> Why? [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> requires that "when a block tag doesn't fit on a single line, continuation
> lines are indented four (or more) spaces from the position of the `@`."
> Without the indent, a wrapped `@param` description is visually
> indistinguishable from the start of a new tag, and a reader skimming the
> tag block loses the boundary between parameters.

```java
// bad — the continuation lines up with the tags; where does @param end?
/**
 * Reserves stock for an order.
 *
 * @param order the order to reserve stock against; must already have passed
 * validation and must contain at least one line item
 * @return the reservation
 */
public Reservation reserve(Order order) { ... }

// good — four-space continuation indent from the @
/**
 * Reserves stock for an order.
 *
 * @param order the order to reserve stock against; must already have passed
 *     validation and must contain at least one line item
 * @return the reservation
 */
public Reservation reserve(Order order) { ... }
```

## 4.11 Write Javadoc for every visible class, member, and record component.

> Why? [§7.3](https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required)
> sets the floor: "at the minimum, Javadoc is present for every visible
> class, member, or record component, with a few exceptions noted below."
> "Visible" is precisely defined — a top-level class is visible if it is
> `public`; a member is visible if it is `public` or `protected` *and* its
> containing class is visible; a record component is visible if its
> containing record is visible. That definition is the useful part: it
> means package-private helpers and `private` fields carry no obligation,
> so the requirement lands exactly on the surface other people depend on.
> **Violation for types and members — enforced by Checkstyle
> `MissingJavadocType` and `MissingJavadocMethod`, and by Error Prone
> `MissingSummary`. Suggestion for record components: no check requires a
> `@param` per component, so only review catches the record below.**

```java
// bad — a public record whose components are undocumented
public record Reservation(ReservationId id, Instant expiresAt, boolean confirmed) {}

// good — the record and every visible component are documented
/**
 * A time-limited hold on warehouse stock.
 *
 * @param id the identifier assigned at creation, never {@code null}
 * @param expiresAt the instant after which the hold is released automatically
 * @param confirmed whether the caller has committed to the reservation
 */
public record Reservation(ReservationId id, Instant expiresAt, boolean confirmed) {}
```

## 4.12 Invoke the self-explanatory exception only when there is genuinely nothing to say beyond the member's own name.

> Why? [§7.3.1](https://google.github.io/styleguide/javaguide.html#s7.3.1-javadoc-exception-self-explanatory)
> makes Javadoc optional for "simple, obvious" members "if there really and
> truly is nothing else worthwhile to say but 'the foo'" — and then
> immediately fences it: "it is not appropriate to cite this exception to
> justify omitting relevant information that a typical reader might need to
> know." This is the most abused clause in the entire
> guide, because "it's just a getter" is used to skip documenting units,
> ranges, nullability, and mutability. `getTimeout()` is not
> self-explanatory: is it milliseconds or seconds? `getItems()` is not
> self-explanatory: is the returned list live, or a copy? If the answer to
> any such question is not literally in the name, the exception does not
> apply.

```java
// bad — "just a getter", so nobody documented the unit or the sentinel value
public long getTimeout() { ... }

// bad — "just a getter", so nobody documented that the list is live
public List<LineItem> getItems() { ... }

// good — genuinely self-explanatory: the name is the whole contract
public CustomerId customerId() { ... }

// good — the facts that are not in the name are stated
/** Returns the request timeout in milliseconds, where {@code 0} means "never". */
public long getTimeout() { ... }

/** Returns an unmodifiable view of the line items, in insertion order. */
public List<LineItem> getItems() { ... }
```

## 4.13 On an override, either document the specialization or omit the block — never paste a bare `{@inheritDoc}`.

> Why? [§7.3.2](https://google.github.io/styleguide/javaguide.html#s7.3.2-javadoc-exception-overrides)
> notes that "Javadoc is not always present on a method that overrides a
> supertype method" — the doclet already inherits the supertype's
> documentation automatically when a comment is absent. A block containing
> nothing but `{@inheritDoc}` therefore adds five lines and zero
> information, while creating a place for a future author to add a
> contradiction. Write a comment only when the override *narrows* the
> contract: a stronger guarantee, a new exception, a different complexity
> class, a nullability change.
> **Suggestion — a block containing only a valid `{@inheritDoc}` is legal,
> so no check removes it. Error Prone's `InheritDoc` ("Invalid use of
> @inheritDoc") covers the adjacent error: the tag placed where there is
> nothing to inherit, such as on a method that overrides nothing.**

```java
// bad — five lines that say exactly what silence would have said
/**
 * {@inheritDoc}
 */
@Override
public Optional<Order> findById(OrderId id) { ... }

// good — no comment; the interface's contract is inherited verbatim
@Override
public Optional<Order> findById(OrderId id) { ... }

// good — the override genuinely strengthens the contract, so say so
/**
 * {@inheritDoc}
 *
 * <p>This implementation caches results in memory, so a lookup that has
 * already succeeded runs in constant time and never touches the database.
 * Entries are evicted after {@link #ttl()}.
 */
@Override
public Optional<Order> findById(OrderId id) { ... }
```

## 4.14 Document the contract, not the implementation.

> Why? A **Suggestion** — Google's guide does not legislate content — but
> it is the difference between documentation that survives a refactor and
> documentation that lies after one. Javadoc is read by callers who cannot
> see the body; describing the algorithm ("iterates the list and sums each
> price") tells them nothing they can rely on and becomes false the moment
> someone swaps in a stream or a cache. Describe the observable
> guarantees instead: what is returned, under what preconditions, with what
> complexity, and what is *not* guaranteed. Where implementation notes are
> genuinely valuable to a subclass author, keep them visually separate —
> the JDK's own API docs use `@implSpec` and `@implNote` for this split,
> though neither is listed among the standard tags in the JDK 21 doc
> comment specification, so treat them as a project convention rather than
> a portable guarantee.

```java
// bad — describes the body, which the next refactor invalidates
/**
 * Loops over the internal ArrayList, adds up each line item's price using
 * BigDecimal.add, and then multiplies by the tax rate field.
 */
public Money total() { ... }

// good — describes what a caller can depend on
/**
 * Returns the order total, including tax at the rate in effect when the order
 * was placed.
 *
 * <p>Runs in time linear in the number of line items. The result is exact:
 * intermediate sums use {@link java.math.BigDecimal} and are rounded once, at
 * the end, using {@link java.math.RoundingMode#HALF_EVEN}.
 *
 * @return the total, never {@code null} and never negative
 */
public Money total() { ... }
```

## 4.15 Document nullability for every parameter and return value that admits `null`.

> Why? A **Suggestion**, but the highest-value sentence you can add to any
> Javadoc block. `null` is the one part of a Java signature the type system
> does not express, so the only place a caller can learn it is the comment
> — and the cost of guessing wrong is a `NullPointerException` in
> production rather than a compile error. State it for both directions:
> whether a parameter may be `null`, and whether the return value ever is.
> A method that never returns `null` should say so explicitly, because
> "the docs are silent" and "it can be null" are indistinguishable to a
> careful caller. See [Chapter 25](25-nullability.md) for the JSpecify
> annotations that let NullAway check these claims mechanically.

```java
// bad — the caller has to read the body to find out
/**
 * Returns the shipping address for the order.
 *
 * @param order the order
 * @return the shipping address
 */
public Address shippingAddressOf(Order order) { ... }

// good
/**
 * Returns the shipping address recorded on {@code order}.
 *
 * @param order the order to inspect; must not be {@code null}
 * @return the shipping address, or {@code null} if the order is a digital-only
 *     purchase with no physical delivery
 * @throws NullPointerException if {@code order} is {@code null}
 */
public Address shippingAddressOf(Order order) { ... }
```

## 4.16 Document the thread-safety guarantee of any type that could plausibly be shared.

> Why? A **Suggestion**, and one Effective Java, 3rd ed., Item 82
> ("Document thread safety") makes at length: "the presence of the
> `synchronized` modifier in a method declaration is an implementation
> detail, not a part of its API." A caller deciding whether to put your
> object in a static field, a `ConcurrentHashMap`, or a request-scoped
> local has no way to answer that from the signature. Name the level
> explicitly — immutable, thread-safe, conditionally thread-safe (and under
> which lock), or not thread-safe — because "not thread-safe" is a
> perfectly good answer that saves the reader an investigation.

```java
// bad — silence; every caller has to read the source to decide
public final class RateLimiter {
  public boolean tryAcquire() { ... }
}

// good — the guarantee is named, and the alternative is signposted
/**
 * A token-bucket rate limiter over a fixed window.
 *
 * <p><b>Not thread-safe.</b> Confine each instance to a single thread, or guard
 * every call to {@link #tryAcquire()} with an external lock. Use
 * {@link ConcurrentRateLimiter} if you need to share one instance.
 */
public final class RateLimiter {
  public boolean tryAcquire() { ... }
}
```

## 4.17 Document ownership: say whether a returned collection is a view, a copy, or unmodifiable, and whether you retain a mutable argument.

> Why? A **Suggestion**, and the root cause of a whole class of aliasing
> bugs. `List<LineItem> getItems()` has four plausible contracts — a live
> internal list the caller may mutate, a live list that throws on mutation,
> an unmodifiable *view* that still reflects later internal changes, and a
> defensive copy — and they are indistinguishable from the signature. The
> same applies in reverse: if a constructor stores the `List` it is handed
> rather than copying it, the caller needs to know they must stop mutating
> it. Effective Java, 3rd ed., Item 50 ("Make defensive copies when needed")
> covers the code side; this rule covers stating which choice you made.

```java
// bad — four possible contracts, no way to tell which one applies
public List<LineItem> getItems() {
  return Collections.unmodifiableList(items);
}

public Order(List<LineItem> items) {
  this.items = items;
}

// good
/**
 * Returns an unmodifiable <em>view</em> of the line items, in insertion order.
 *
 * <p>The view is backed by this order: later calls to {@link #addItem} are
 * visible through it. Call {@link List#copyOf} if you need a stable snapshot.
 */
public List<LineItem> getItems() {
  return Collections.unmodifiableList(items);
}

/**
 * Creates an order over a defensive copy of {@code items}.
 *
 * @param items the initial line items; copied, so the caller may keep mutating
 *     the list it passed in
 */
public Order(List<LineItem> items) {
  this.items = List.copyOf(items);
}
```

## 4.18 Document encounter order — or its deliberate absence.

> Why? A **Suggestion**, but the one every caller silently assumes. A
> method returning a `Set` or a `Map`'s `keySet` has no defined iteration
> order unless you say otherwise, yet callers routinely write tests that
> pass on `HashMap`'s incidental ordering and break on a JDK upgrade or a
> different input size. Say either "in insertion order", "sorted by
> {@code name}", or "in no particular order; do not rely on it." If order
> *is* part of the contract, prefer returning a Java 21
> `SequencedCollection` or `SequencedMap` so the type states it too.

```java
// bad — callers will assume insertion order and be wrong
public Set<Sku> outOfStockSkus() {
  return new HashSet<>(missing);
}

// good — order is explicitly not part of the contract
/**
 * Returns the SKUs with zero on-hand stock, in no particular order.
 *
 * <p>Callers must not depend on iteration order; it varies with the size and
 * contents of the underlying map.
 */
public Set<Sku> outOfStockSkus() {
  return Set.copyOf(missing);
}

// good — order is part of the contract, and the type says so
/** Returns the audit entries for this order, oldest first. */
public SequencedCollection<AuditEntry> auditTrail() {
  return Collections.unmodifiableList(entries);
}
```

## 4.19 Document `@throws` for the unchecked exceptions that are part of the contract, and never for one the method cannot throw.

> Why? A **Suggestion** on the first half, a **Violation** on the second.
> Checked exceptions appear in the signature; unchecked ones do not, so
> `@throws IllegalArgumentException if {@code amount} is negative` is the
> only place a caller can learn that a negative amount is a programming
> error rather than a supported input. Effective Java, 3rd ed., Item 74
> ("Document all exceptions thrown by each method") requires exactly this.
> The inverse is a hard error: documenting a checked exception the method
> cannot throw makes the doclet emit a `Throws` row that no caller can ever
> trigger, and misleads anyone writing a `catch`.
> **Violation on the second half — enforced by Error Prone `InvalidThrows`
> ("The documented method doesn't actually throw this checked exception").
> Checkstyle `JavadocMethod` covers the opposite direction, flagging a
> thrown or declared exception that has no `@throws` tag, but only once
> `validateThrows` is set to `true`; it is `false` by default.**

```java
// bad — the unchecked contract is undocumented, and a checked exception the
// method cannot possibly throw is documented instead
/**
 * Withdraws {@code amount} from the account.
 *
 * @param amount the amount to withdraw
 * @throws java.io.IOException if the ledger cannot be reached
 */
public void withdraw(Money amount) {
  if (amount.isNegative()) {
    throw new IllegalArgumentException("amount must be positive: " + amount);
  }
  ...
}

// good
/**
 * Withdraws {@code amount} from the account.
 *
 * @param amount the amount to withdraw; must be strictly positive
 * @throws IllegalArgumentException if {@code amount} is zero or negative
 * @throws InsufficientFundsException if the balance is below {@code amount}
 */
public void withdraw(Money amount) { ... }
```

## 4.20 Use `{@code}` for identifiers and literals, and `{@link}` for references worth navigating to.

> Why? A **Suggestion** on which to pick, a **Violation** on getting the
> syntax right. `{@code}` renders in code font without interpreting its
> contents as HTML, which is what you want for `null`, `true`, a parameter
> name, or a generic type like `List<String>` — written bare, the angle
> brackets are swallowed as an HTML tag. `{@link}` additionally generates a
> hyperlink, so it is right when the reader will plausibly want to go
> there, and wrong when repeated on every mention: four links to the same
> class in one paragraph is noise. Use `{@link}` on first mention and
> `{@code}` thereafter.
> **Violation — enforced by Error Prone `InvalidLink` ("This @link tag
> looks wrong") and `InvalidInlineTag`.**

```java
// bad — bare generics eaten as HTML, and the same link repeated three times
/**
 * Returns a List<LineItem> of the items. Each {@link LineItem} in the
 * {@link LineItem} list wraps a {@link LineItem} price. Returns null if empty.
 */
public List<LineItem> items() { ... }

// good
/**
 * Returns the {@code List<LineItem>} backing this order.
 *
 * <p>Each {@link LineItem} carries its own price and quantity; an item with a
 * quantity of {@code 0} is never present. Returns {@code null} only if this
 * order has not yet been persisted.
 */
public List<LineItem> items() { ... }
```

## 4.21 Escape `<`, `>`, and `&` in prose, and never write HTML entities inside `{@code}` or `{@literal}`.

> Why? Javadoc is HTML, so an unescaped `<` in prose starts a tag and
> silently deletes everything until the next `>` — a comment saying
> "quantity must be > 0 and < 100" renders as "quantity must be > 0 and".
> The mirror-image mistake is writing `&lt;` inside `{@code}`, where the
> contents are *not* interpreted as HTML, so the reader sees the literal
> characters `&lt;` in the rendered docs.
> **Violation — enforced by Error Prone `UnescapedEntity` ("Javadoc is
> interpreted as HTML, so HTML entities such as &, <, > must be escaped")
> and `EscapedEntity` ("HTML entities in @code/@literal tags will appear
> literally in the rendered javadoc").**

```java
// bad — the unescaped < swallows the rest of the sentence
/** Accepts a quantity where 0 < quantity < 1000, and a name that is non-blank. */
public void addItem(Sku sku, int quantity, String name) { ... }

// bad — &lt; inside {@code} renders as the literal characters "&lt;"
/** Accepts a {@code Map&lt;Sku, Integer&gt;} of requested quantities. */
public void addAll(Map<Sku, Integer> quantities) { ... }

// good — entities in prose, raw characters inside {@code}
/**
 * Adds a line item.
 *
 * @param quantity the number of units, where 0 &lt; quantity &lt; 1000
 */
public void addItem(Sku sku, int quantity, String name) { ... }

/** Adds every entry of the given {@code Map<Sku, Integer>} as a line item. */
public void addAll(Map<Sku, Integer> quantities) { ... }
```

## 4.22 Use `{@snippet}` rather than `<pre>{@code ...}</pre>` for example code.

> Why? A **Suggestion**. `{@snippet}` was added to the standard doclet in
> JDK 18 and is fully available on a Java 21 baseline. Unlike
> `<pre>{@code ...}</pre>`, it preserves indentation without HTML
> whitespace games, supports highlighting and region markup, and — in its
> external form — can pull the sample from a real file under `snippet-files/`
> that the compiler actually compiles. That last property is the point: an
> example inside a comment rots silently, while an external snippet breaks
> the build when the API it demonstrates changes.

```java
// bad — indentation is at the mercy of HTML, and nothing compiles this
/**
 * Creates a money value.
 *
 * <pre>{@code
 * Money price = Money.of(new BigDecimal("19.99"), Currency.getInstance("EUR"));
 * }</pre>
 */
public static Money of(BigDecimal amount, Currency currency) { ... }

// good
/**
 * Creates a money value with the given amount and currency.
 *
 * {@snippet :
 * Money price = Money.of(new BigDecimal("19.99"), Currency.getInstance("EUR"));
 * Money doubled = price.multiply(2);
 * }
 *
 * @param amount the amount; scale is preserved exactly
 * @param currency the currency the amount is denominated in
 * @return the money value, never {@code null}
 */
public static Money of(BigDecimal amount, Currency currency) { ... }
```

## 4.23 Never write Javadoc that restates the signature.

> Why? A **Suggestion**, and the single most common form of useless
> documentation. "Sets the name" on `setName(String name)` costs a code
> review, a merge conflict, and a maintenance obligation, and repays none
> of it — the reader already has the signature. Worse, its presence
> defeats the tooling: `MissingJavadocMethod` goes quiet, so nobody ever
> notices that the genuinely non-obvious facts (that the name is trimmed,
> that blank is rejected, that the change is not persisted until
> `save()`) remain undocumented. If you cannot say something the signature
> does not, [§7.3.1](https://google.github.io/styleguide/javaguide.html#s7.3.1-javadoc-exception-self-explanatory)
> lets you write nothing at all — take that option.

```java
// bad — pure restatement; satisfies the linter, informs nobody
/**
 * Sets the name.
 *
 * @param name the name
 */
public void setName(String name) { ... }

// good — either say the non-obvious part...
/**
 * Sets the display name, trimming surrounding whitespace.
 *
 * <p>The change is held in memory until {@link #save()} is called.
 *
 * @param name the new display name; must not be blank after trimming
 * @throws IllegalArgumentException if {@code name} is blank after trimming
 */
public void setName(String name) { ... }

// good — ...or, if there is genuinely nothing to add, write nothing
public void setName(String name) { ... }
```

## 4.24 Open a documentation comment with `/**`, not `/*`.

> Why? A single-asterisk comment containing `@param` tags or HTML looks
> like Javadoc in the editor, passes review as Javadoc, and is then
> discarded entirely by the doclet — the generated API page shows the
> member with no description at all. The failure is invisible unless
> someone actually reads the generated HTML, which is why it survives for
> years. The mirror-image error is a `/**` block in a position where
> Javadoc is not legal (before an `import`, or between an annotation and
> its target), which the doclet also silently drops.
> **Violation — enforced by Error Prone `AlmostJavadoc` ("This comment
> contains Javadoc or HTML tags, but isn't started with a double asterisk
> (`/**`); is it meant to be Javadoc?") and Checkstyle
> `InvalidJavadocPosition`, which recognizes Javadoc "only when placed
> immediately before module, package, class, interface, constructor,
> method, or field declarations".**

```java
// bad — looks like Javadoc, generates nothing
/*
 * Reserves stock for an order.
 *
 * @param order the order to reserve stock against
 */
public Reservation reserve(Order order) { ... }

// good
/**
 * Reserves stock for an order.
 *
 * @param order the order to reserve stock against
 * @return the reservation, which the caller must confirm or cancel
 */
public Reservation reserve(Order order) { ... }
```
