<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 5. Comments & TODOs

This chapter covers **implementation comments** — the `//` and `/* … */` text
that lives inside method bodies, beside declarations, and above blocks. It
draws from [Google Java Style
§4.8.6](https://google.github.io/styleguide/javaguide.html#s4.8.6-comments),
[§4.8.6.1 Block comment
style](https://google.github.io/styleguide/javaguide.html#s4.8.6.1-block-comment-style),
and [§4.8.6.2 TODO
comments](https://google.github.io/styleguide/javaguide.html#s4.8.6.2-todo-comments).

Javadoc is a different artifact with different rules and it is covered in
[Chapter 4](04-javadoc.md). The line between them is the audience: **Javadoc
documents the contract for someone calling the code; an implementation
comment explains a decision to someone changing the code.** Google's guide
draws the same line explicitly — §4.8.6 opens by saying it "addresses
*implementation comments*. Javadoc is addressed separately in Section 7."
Rule 5.16 below is the one place the two touch.

Google's normative text here is short: two subsections covering comment
indentation, the `/* … */` continuation form, boxes, and the `TODO` format.
Everything after §5.8 in this chapter is judgment — the rules that decide
whether a comment earns its line at all. Those rules are labeled
**Suggestion** because no tool can evaluate them.

Physical formatting of a comment — its indentation, whether the formatter
rewraps it, blank lines around it — belongs to `google-java-format` and is
settled in [Chapter 1](01-formatting-and-tooling.md). This chapter is about
what the comment *says*.

**Tool alignment:** `checkstyle/CommentsIndentation` checks comment
indentation against the surrounding block, `checkstyle/TrailingComment`
rejects any comment on a line that also contains code, and
`checkstyle/TodoComment` is a generic regex matcher over comment text whose
`format` property defaults to `TODO:` — out of the box it *reports* TODOs
rather than validating their shape. Only `CommentsIndentation` enforces one
of this chapter's rules with its stock configuration, so it is the only
**Violation** below outside of the Javadoc rule 5.16; everything else is a
**Suggestion**.

## 5.1 Indent a block comment to the same level as the code it describes.

> Why? [§4.8.6.1](https://google.github.io/styleguide/javaguide.html#s4.8.6.1-block-comment-style)
> requires that "block comments are indented at the same level as the
> surrounding code." A comment parked at column 0 inside a nested block
> reads as if it belongs to the enclosing scope, so a reader scanning
> indentation attaches it to the wrong statement.
> **Violation — enforced by `spotlessCheck`.** google-java-format re-indents
> comments to the surrounding block level, so a misplaced comment is a
> formatting failure rather than a lint finding. Checkstyle's
> `CommentsIndentation` enforces the same rule and is deliberately left out
> of the shipped ruleset to avoid duplicate findings the formatter already
> fixes (chapter 38).

```java
// bad — the comment is detached from the statement it explains
void reconcile(Ledger ledger) {
  if (ledger.isStale()) {
// The provider reports balances a day behind, so shift the window back.
    ledger.shiftWindow(Duration.ofDays(1));
  }
}

// good
void reconcile(Ledger ledger) {
  if (ledger.isStale()) {
    // The provider reports balances a day behind, so shift the window back.
    ledger.shiftWindow(Duration.ofDays(1));
  }
}
```

## 5.2 Use `/* … */` for a multi-line comment the formatter may need to rewrap, and align every continuation line's `*`.

> Why? [§4.8.6.1](https://google.github.io/styleguide/javaguide.html#s4.8.6.1-block-comment-style)
> states that for multi-line `/* … */` comments "subsequent lines must
> start with `*` aligned with the `*` on the previous line," and adds the
> tip: "use the `/* ... */` style if you want automatic code formatters to
> re-wrap the lines when necessary (paragraph-style). Most formatters don't
> re-wrap lines in `// ...` style comment blocks." A run of `//` lines is
> opaque to a reflowing formatter; a `/* … */` block is not.

```java
// bad — ragged continuation lines that no formatter can safely reflow
/*
 The retry budget is shared across every shard, so one hot shard
can starve the rest. Read the capacity note before raising this.
   */
private static final int MAX_RETRIES = 3;

// good
/*
 * The retry budget is shared across every shard, so one hot shard can
 * starve the rest. Read the capacity note before raising this.
 */
private static final int MAX_RETRIES = 3;
```

## 5.3 Never draw a box around a comment.

> Why? [§4.8.6.1](https://google.github.io/styleguide/javaguide.html#s4.8.6.1-block-comment-style)
> is unambiguous: "Comments are not enclosed in boxes drawn with asterisks
> or other characters." A box is pure maintenance debt — every edit to the
> text forces a manual realignment of the right-hand border, and the first
> person in a hurry leaves it crooked forever.

```java
// bad — a box that has to be hand-maintained on every wording change
/************************************
 *  Connection pool bootstrap       *
 *  Do not reorder these calls.     *
 ************************************/
private void startPool() {
  driver.register();
  pool.warmUp();
}

// good
/*
 * Connection pool bootstrap. The driver must be registered before the
 * pool warms up, or the first N connections fail to resolve a dialect.
 */
private void startPool() {
  driver.register();
  pool.warmUp();
}
```

## 5.4 Never use a banner comment to carve a class into sections.

> Why? Section banners (`// ===== PUBLIC API =====`) are a symptom, not a
> solution: a class that needs signposting to be navigable is a class that
> should be split, or one whose member ordering has drifted from the
> "logical order" [§3.4.2](https://google.github.io/styleguide/javaguide.html#s3.4.2-ordering-class-contents)
> requires. The banner also rots silently — nothing keeps members inside
> the section they were filed under. **Suggestion.**

```java
// bad — banners standing in for a class that wants to be three classes
final class OrderService {
  // ======================= VALIDATION =======================
  private boolean isValid(Order order) {
    return order.total().signum() > 0;
  }

  // ======================= PERSISTENCE ======================
  private void save(Order order) {
    jdbc.update(INSERT_ORDER, order.id(), order.total());
  }

  // ======================= NOTIFICATION =====================
  private void notifyCustomer(Order order) {
    mailer.send(order.customerEmail(), "order-confirmed", order.id());
  }
}

// good — collaborators, each with a name that does the signposting
final class OrderService {
  private final OrderValidator validator;
  private final OrderRepository repository;
  private final CustomerNotifier notifier;

  OrderService(OrderValidator validator, OrderRepository repository, CustomerNotifier notifier) {
    this.validator = validator;
    this.repository = repository;
    this.notifier = notifier;
  }
}
```

## 5.5 Write a TODO as `TODO:` in all caps, a colon, a link to a tracked issue, then a hyphen and an explanation.

> Why? [§4.8.6.2](https://google.github.io/styleguide/javaguide.html#s4.8.6.2-todo-comments)
> specifies the exact shape: a `TODO` comment "begins with the word `TODO`
> in all caps, a following colon, and a link to a resource that contains
> the context, ideally a bug reference," followed by "an explanatory string
> introduced with a hyphen." The point of the fixed shape is that the
> codebase becomes greppable — one regex finds every deferred decision and
> every one of them leads to a ticket with the full story. **Suggestion** —
> no stock check validates TODO *shape*. `checkstyle/TodoComment` is a
> generic comment matcher whose `format` defaults to `TODO:`, so by default
> it reports every TODO rather than only the malformed ones; a project can
> point `format` at the malformed shape, but that is local configuration,
> not a shipped default.

```java
// bad — no marker case, no link, no explanation; ungreppable and untraceable
// todo fix this properly
private BigDecimal convert(Money money) {
  return money.amount();
}

// good
// TODO: issues.example.com/BILL-4127 - Apply the FX rate once the rates
// service ships; today every currency is treated as the base currency.
private BigDecimal convert(Money money) {
  return money.amount();
}
```

## 5.6 Point a TODO at an issue, not at a person or a team.

> Why? [§4.8.6.2](https://google.github.io/styleguide/javaguide.html#s4.8.6.2-todo-comments)
> advises against naming an individual or a team as the TODO's context.
> People change teams and leave; an issue tracker entry outlives both and
> carries the reasoning, the decision history, and a live owner. A
> `TODO(jsmith)` two years after jsmith's last commit is an archaeological
> artifact, not an action item.

```java
// bad — the context lives in one person's memory, and they have left
// TODO(jsmith): revisit the batching heuristic
int batchSize = 500;

// good
// TODO: issues.example.com/PERF-882 - Batch size is a guess from the
// 2026-Q1 load test; the ticket tracks the measurement that replaces it.
int batchSize = 500;
```

## 5.7 Give a time-bound TODO a concrete trigger — a date, a release, or an event.

> Why? [§4.8.6.2](https://google.github.io/styleguide/javaguide.html#s4.8.6.2-todo-comments)
> recommends naming a specific date or event for TODOs that are meant to
> expire, and its own example does exactly that: "Remove this after the
> 2047q4 compatibility window expires." "Later" and "eventually" are not
> triggers — nobody can ever tell whether the condition has been met, so
> the comment becomes permanent.

```java
// bad — no condition, so no one can ever decide this is safe to delete
// TODO: issues.example.com/API-91 - Remove the legacy field eventually.
private final String legacyCustomerId;

// good
// TODO: issues.example.com/API-91 - Remove legacyCustomerId after the
// v1 API sunset on 2027-01-31, when no client can still send it.
private final String legacyCustomerId;
```

## 5.8 Use `TODO` as the only deferred-work marker — no `FIXME`, `XXX`, or `HACK`.

> Why? Four markers means four regexes, four dashboards, and four
> conventions for what "urgent" means. [§4.8.6.2](https://google.github.io/styleguide/javaguide.html#s4.8.6.2-todo-comments)
> defines exactly one marker and states that the point of the format is "to
> have a consistent TODO format that can be searched." Severity belongs in
> the linked issue, where it can be re-triaged; it does not belong encoded
> in the marker word, where it can never change. **Suggestion** — a second
> `checkstyle/TodoComment` instance with `format` set to
> `FIXME|XXX|HACK` will catch the alternative markers, but that is a
> configuration a project has to add; the check's default `format` is
> `TODO:`.

```java
// bad — three markers, three conventions, none of them linked
// FIXME: this breaks on leap seconds
// XXX why is this a double?
// HACK: works around the broken upstream parser

// good
// TODO: issues.example.com/TIME-14 - Leap seconds shift this by 1s; the
// ticket holds the reproduction and the upstream parser bug it depends on.
```

## 5.9 Explain why the code is the way it is, not what it does.

> Why? The compiler already states what the code does, and it is never out
> of date. A comment restating the mechanics adds a second source of truth
> that drifts on the first refactor. The information a maintainer cannot
> recover from the code is the *reason*: the constraint, the incident, the
> upstream bug, the benchmark. That is what the comment is for.
> **Suggestion.**

```java
// bad — narrates the mechanics; the code already says all of this
// Loop over the entries and add each amount to the total.
BigDecimal total = BigDecimal.ZERO;
for (Entry entry : entries) {
  total = total.add(entry.amount());
}

// good — states the constraint the code exists to satisfy
// Summed sequentially rather than with a parallel stream: entries arrive
// pre-sorted by posting time and BigDecimal.add is not associative for
// mixed scales, so reordering changes the result.
BigDecimal total = BigDecimal.ZERO;
for (Entry entry : entries) {
  total = total.add(entry.amount());
}
```

## 5.10 Delete commented-out code.

> Why? Version control already holds every line that ever existed, with the
> author, the date, and the message explaining why it went away — a
> commented-out block holds none of that. Worse, it is invisible to the
> compiler, to refactoring tools, and to static analysis, so it silently
> decays into code that could no longer compile if uncommented. It also
> defeats "find all usages," making the surrounding code look more used
> than it is. **Suggestion.**

```java
// bad — dead code preserved in a comment, with no history and no compiler
BigDecimal fee = schedule.feeFor(order);
// BigDecimal fee = order.amount().multiply(FLAT_RATE);
// if (customer.isPremium()) {
//   fee = fee.multiply(PREMIUM_DISCOUNT);
// }
return fee;

// good
return schedule.feeFor(order);
```

## 5.11 Keep changelogs, author tags, and modification dates out of source files.

> Why? Every one of these facts is already recorded, accurately and
> immutably, by version control. Hand-maintained copies are wrong the first
> time someone forgets to update them, and there is no mechanism that can
> ever notice. They also generate merge conflicts on files whose actual
> content did not conflict. **Suggestion.**

```java
// bad — a hand-maintained mirror of `git log`, already wrong
/*
 * PaymentGateway
 *
 * @author a.chen
 * Last modified: 2024-03-11
 *
 * Change history:
 *   2023-06-02 a.chen  - initial version
 *   2023-11-19 r.patel - added retry support
 *   2024-03-11 a.chen  - fixed timeout handling
 */
public final class PaymentGateway {
  // ... fields and methods
}

// good — the Javadoc says what the type is for; git says who changed it when
/** Sends authorization and capture requests to the upstream card network. */
public final class PaymentGateway {
  // ... fields and methods
}
```

## 5.12 Delete a comment that restates its declaration.

> Why? [§7.3.1](https://google.github.io/styleguide/javaguide.html#s7.3.1-javadoc-exception-self-explanatory)
> already lets you omit Javadoc for a member that is "simple, obvious";
> the same logic applies with more force to implementation comments, which
> have no tooling requiring them at all. A comment that repeats the
> identifier costs a line, adds nothing, and trains readers to skip
> comments — including the one comment on the next screen that mattered.
> **Suggestion.**

```java
// bad — every line of comment is recoverable from the line below it
// The customer id.
private final UUID customerId;

// Increment the retry count.
retryCount++;

// Return the total.
return total;

// good
private final UUID customerId;

retryCount++;

return total;
```

## 5.13 When a block needs a paragraph of explanation, extract a named method or a named constant instead.

> Why? A name is checked by the compiler and travels with the code to every
> call site; a comment does neither. If the only way to make a block
> comprehensible is prose above it, the block is doing something that
> deserves its own identifier. Extracting turns the comment into a name and
> deletes the drift risk entirely. **Suggestion.**

```java
// bad — the comment is compensating for an unnamed condition
// A subscription counts as churned if it lapsed more than 30 days ago and
// the customer has not started a new one since, and it was never a trial.
if (sub.lapsedAt() != null
    && sub.lapsedAt().isBefore(now.minus(Duration.ofDays(30)))
    && customer.activeSubscription().isEmpty()
    && !sub.wasTrial()) {
  churnReport.record(customer);
}

// good — the condition names itself
if (isChurned(sub, customer, now)) {
  churnReport.record(customer);
}

private static boolean isChurned(Subscription sub, Customer customer, Instant now) {
  return sub.lapsedAt() != null
      && sub.lapsedAt().isBefore(now.minus(CHURN_GRACE_PERIOD))
      && customer.activeSubscription().isEmpty()
      && !sub.wasTrial();
}
```

## 5.14 Update or delete the comment in the same change that touches the code it describes.

> Why? A stale comment is worse than no comment: a missing comment makes a
> reader read the code, while a wrong comment makes them trust it. Comments
> have no compiler and no test, so the only moment they can be kept honest
> is the moment the surrounding code changes. If the comment no longer
> applies after your edit, delete it in that same commit. **Suggestion.**

```java
// bad — the comment survived a change that inverted its claim
// Retries are disabled for idempotent reads.
private RetryPolicy policyFor(Request request) {
  return request.isIdempotent() ? RetryPolicy.exponential(3) : RetryPolicy.none();
}

// good
// Only idempotent reads are retried; a replayed write could double-charge.
private RetryPolicy policyFor(Request request) {
  return request.isIdempotent() ? RetryPolicy.exponential(3) : RetryPolicy.none();
}
```

## 5.15 Keep an end-of-line comment to a few words; put anything longer on its own line above the code.

> Why? [§4.4](https://google.github.io/styleguide/javaguide.html#s4.4-column-limit)
> caps lines at 100 columns, so a long trailing comment either forces the
> code itself to wrap awkwardly or pushes the comment off the edge of a
> side-by-side diff. A comment above the statement has the full line width
> and survives any later reformatting of the statement. **Suggestion** —
> Google caps the column, not the comment position. Note that
> `checkstyle/TrailingComment`, where a project enables it, is stricter
> than this rule: it rejects *any* comment on a line that also holds code,
> including a short one.

```java
// bad — 109 columns; the explanation is crammed onto the end of the line
int backoffMillis = 250; // 250 because the upstream gateway rate-limits at 4 rps and anything lower trips it

// good
// The upstream gateway rate-limits at 4 rps; anything below 250ms trips it.
int backoffMillis = 250;
```

## 5.16 Use Javadoc, not an implementation comment, wherever Javadoc is required.

> Why? [§7.3](https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required)
> requires that "at the minimum, Javadoc is present for every visible
> class, member, or record component." A `//` comment above a public method
> satisfies none of that: it never reaches the generated API docs, never
> reaches an IDE hover, and is not checked by any Javadoc lint. See
> [Chapter 4](04-javadoc.md) for the block-tag order and the summary
> fragment rules that apply once you switch to `/** … */`.
> **Violation — enforced by `checkstyle/MissingJavadocMethod` and
> `checkstyle/MissingJavadocType`; `checkstyle/JavadocMethod` and
> `checkstyle/SummaryJavadoc` then police the contents.**

```java
// bad — documentation that no tool will ever surface to a caller
// Charges the card and returns the authorization code. Throws if declined.
public String authorize(Card card, Money amount) throws DeclinedException {
  return network.reserve(card, amount);
}

// good
/**
 * Reserves {@code amount} against {@code card} and returns the network's
 * authorization code.
 *
 * @param card the card to authorize against
 * @param amount the amount to reserve, in the card's billing currency
 * @return the authorization code issued by the card network
 * @throws DeclinedException if the network declines the authorization
 */
public String authorize(Card card, Money amount) throws DeclinedException {
  return network.reserve(card, amount);
}
```

## 5.17 Disable a test with `@Disabled` and a reason — never by commenting it out.

> Why? A commented-out test reports as green: the suite passes, the
> coverage report does not flag it, and nothing tells anyone that a
> behavior stopped being verified. JUnit 5's
> `org.junit.jupiter.api.Disabled` takes a reason string and the skip shows
> up in every test report, so the gap stays visible until someone closes
> it. See [Chapter 31](31-testing.md). **Suggestion.**

```java
// bad — the suite goes green and nothing records that coverage was lost
// @Test
// void refundsPartialCapture() {
//   assertThat(gateway.refund(capture, Money.of("5.00"))).isSuccessful();
// }

// good
@Test
@Disabled("issues.example.com/PAY-233 - sandbox gateway rejects partial refunds")
void refundsPartialCapture() {
  assertThat(gateway.refund(capture, Money.of("5.00"))).isSuccessful();
}
```
