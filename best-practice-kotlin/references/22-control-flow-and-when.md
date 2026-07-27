<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 22. Control Flow & `when`

Kotlin's control flow constructs are expressions, and that single fact changes
how they should be written. `if`, `when`, and `try` all produce values, so the
idiomatic shape of a branch is "compute a value" rather than "assign to a
variable that was declared uninitialized three lines up." This chapter covers
`when` in depth, `if` as an expression, loops and ranges, and the discipline
of keeping nesting shallow.

The rules draw on the Kotlin coding conventions sections on
[conditional statements](https://kotlinlang.org/docs/coding-conventions.html#conditional-statements),
[if versus when](https://kotlinlang.org/docs/coding-conventions.html#if-versus-when),
[guard conditions in when expression](https://kotlinlang.org/docs/coding-conventions.html#guard-conditions-in-when-expression),
[loops](https://kotlinlang.org/docs/coding-conventions.html#loops),
[loops on ranges](https://kotlinlang.org/docs/coding-conventions.html#loops-on-ranges),
and
[nullable Boolean values in conditions](https://kotlinlang.org/docs/coding-conventions.html#nullable-boolean-values-in-conditions);
on the Android Kotlin style guide's
[braces](https://developer.android.com/kotlin/style-guide#braces) and
[expressions](https://developer.android.com/kotlin/style-guide#expressions)
rules; and on the language reference for
[conditions and loops](https://kotlinlang.org/docs/control-flow.html).

The single most important rule in this chapter is §22.3 — a `when` over a
sealed type or an enum must have no `else`, so that adding a subtype becomes a
compile error rather than a silent fallthrough. That rule is the entire payoff
of the modelling advice in [Chapter 13, Sealed Types](13-sealed-types.md) and
[Chapter 15, Enums](15-enums.md); without it, a sealed hierarchy is just a
class hierarchy with extra ceremony. Exception-based control flow is ruled out
here and covered properly in
[Chapter 24, Exceptions & `Result`](24-exceptions-and-result.md).

Two features used below were **Experimental in earlier releases and are Stable
as of Kotlin 2.2**, so they need no opt-in flag on the 2.4 floor: guard
conditions in `when` with a subject, and non-local `break`/`continue` in inline
lambdas. Both are used as default idiom here.

**Tool alignment:** several rules are mechanically enforced. detekt's
`ElseCaseInsteadOfExhaustiveWhen`, `UseIfInsteadOfWhen`,
`RangeUntilInsteadOfRangeTo`, `NullableBooleanCheck`,
`UnconditionalJumpStatementInLoop`, `LoopWithTooManyJumpStatements`,
`LabeledExpression`, `NestedBlockDepth`, `ReturnCount`, `ComplexCondition`,
and `CollapsibleIfStatements` all fire on rules below. Several of them
(`UseIfInsteadOfWhen`, `RangeUntilInsteadOfRangeTo`, `NullableBooleanCheck`,
`LabeledExpression`, `CollapsibleIfStatements`) ship **inactive by default**,
so a project that has not enabled them will see no finding. Rules a named
check actually enforces are marked **Violation**; the rest are **Suggestion**.

## 22.1 Use `when` and `if` as expressions whenever every branch produces the same value.

> Why? The Kotlin coding conventions on
> [conditional statements](https://kotlinlang.org/docs/coding-conventions.html#conditional-statements)
> say plainly: "Prefer using the expression form of `try`, `if`, and `when`."
> The statement form requires a `var` (or a repeated `return`), which means the
> compiler can no longer prove the variable is assigned exactly once, and a
> branch that forgets to assign compiles cleanly. The expression form makes an
> unassigned branch a type error. **Suggestion.**

```kotlin
// bad — a mutable local, and a forgotten branch is not a compile error
fun describe(code: Int): String {
    var label: String = ""
    when (code) {
        0 -> label = "zero"
        1 -> label = "one"
        else -> label = "many"
    }
    return label
}

// good — one expression, every branch must produce a String
fun describe(code: Int): String = when (code) {
    0 -> "zero"
    1 -> "one"
    else -> "many"
}
```

## 22.2 Use `if` for a binary condition and `when` for three or more branches.

> Why? The coding conventions
> [if versus when](https://kotlinlang.org/docs/coding-conventions.html#if-versus-when)
> section is explicit: "Prefer using `if` for binary conditions instead of
> `when`... Prefer using `when` if there are three or more options." A
> two-branch `when` costs a subject, an arrow, and an `else` to express what
> `if`/`else` says with one keyword, and it reads as though a third case is
> coming. **Violation — enforced by `detekt/UseIfInsteadOfWhen`.**

```kotlin
// bad — a two-branch when where if says the same thing
fun label(user: User?): String = when (user) {
    null -> "anonymous"
    else -> user.displayName
}

// good
fun label(user: User?): String = if (user == null) "anonymous" else user.displayName

// good — three or more options earns the when
fun tier(score: Int): Tier = when {
    score >= 90 -> Tier.GOLD
    score >= 70 -> Tier.SILVER
    score >= 50 -> Tier.BRONZE
    else -> Tier.NONE
}
```

## 22.3 Never write an `else` branch on a `when` over a sealed type or an enum.

> Why? This is the central rule of the chapter. The language reference states
> that when the subject is "a `Boolean`, `enum` class, `sealed` class, or their
> nullable counterparts... you can cover all cases without an `else` branch" —
> and if you do, the compiler checks exhaustiveness for you. Add an `else` and
> that check evaporates: a new subtype or a new enum constant silently routes
> to the fallback, at every call site, forever. Without `else`, adding
> `PaymentResult.Chargeback` breaks the build in exactly the places that need
> updating. Since Kotlin 1.7 this holds for `when` *statements* too, not just
> expressions — the
> [compatibility guide for 1.7](https://kotlinlang.org/docs/compatibility-guide-17.html)
> records that a non-exhaustive `when` statement over an enum, sealed, or
> `Boolean` subject went from a warning in 1.6 to an error in 1.7. See
> [Chapter 13](13-sealed-types.md) and [Chapter 15](15-enums.md) for the
> modelling side. The one honest exception is a large third-party enum you do
> not own — `java.time.DayOfWeek` is tolerable, a sixty-constant HTTP status
> enum is not worth enumerating — and there the better answer is usually to map
> it to a closed type of your own at the boundary and switch on that.
> **Violation — enforced by `detekt/ElseCaseInsteadOfExhaustiveWhen`.**

```kotlin
sealed interface PaymentResult {
    data class Settled(val reference: String) : PaymentResult
    data class Declined(val reason: String) : PaymentResult
    data object Pending : PaymentResult
}

// bad — adding PaymentResult.Chargeback compiles and silently becomes "unknown"
fun render(result: PaymentResult): String = when (result) {
    is PaymentResult.Settled -> "settled ${result.reference}"
    is PaymentResult.Declined -> "declined: ${result.reason}"
    else -> "unknown"
}

// good — adding a subtype is a compile error here and nowhere else
fun render(result: PaymentResult): String = when (result) {
    is PaymentResult.Settled -> "settled ${result.reference}"
    is PaymentResult.Declined -> "declined: ${result.reason}"
    PaymentResult.Pending -> "pending"
}
```

## 22.4 Keep `else` for open subjects — `Int`, `String`, and anything else the compiler cannot close.

> Why? §22.3 is not "never write `else`." Over an open subject the compiler has
> no finite case list to check, so a `when` *expression* without `else` does not
> compile at all, and a `when` *statement* without `else` silently does nothing
> for unmatched input. Make the fallback deliberate: either produce a real
> default or fail loudly with `error` (see
> [Chapter 24, §24.6](24-exceptions-and-result.md)). **Suggestion.**

```kotlin
// bad — no else on an open subject; unmatched input silently does nothing
fun applyCommand(name: String, session: Session) {
    when (name) {
        "start" -> session.start()
        "stop" -> session.stop()
    }
}

// good — the fallback is a decision, not an omission
fun applyCommand(name: String, session: Session) {
    when (name) {
        "start" -> session.start()
        "stop" -> session.stop()
        else -> error("unknown command: $name")
    }
}
```

## 22.5 Give the `when` a subject when every branch tests the same value; drop the subject only when the branches test unrelated conditions.

> Why? A subject states the axis of the decision once, in the header, where a
> reader sees it before any branch. Repeating `status ==` on every line buries
> that axis in noise, and it forfeits the exhaustiveness check of §22.3
> entirely — a subjectless `when` over an enum *always* requires an `else`,
> because the compiler has no subject to enumerate. Conversely, forcing a
> subject onto genuinely unrelated conditions produces the `when (true)`
> anti-pattern. **Suggestion.**

```kotlin
enum class Outcome { ACCEPTED, THROTTLED, UPSTREAM_ERROR, TIMEOUT }

// bad — a subject exists but is not used, so exhaustiveness cannot be checked
// and the else is forced on you
fun retryDelay(outcome: Outcome): Duration = when {
    outcome == Outcome.THROTTLED -> 30.seconds
    outcome == Outcome.UPSTREAM_ERROR -> 5.seconds
    outcome == Outcome.TIMEOUT -> 5.seconds
    else -> Duration.ZERO
}

// good — the compiler enumerates the subject, so no else is needed and a new
// constant becomes a compile error (22.3)
fun retryDelay(outcome: Outcome): Duration = when (outcome) {
    Outcome.THROTTLED -> 30.seconds
    Outcome.UPSTREAM_ERROR, Outcome.TIMEOUT -> 5.seconds
    Outcome.ACCEPTED -> Duration.ZERO
}

// good — unrelated conditions genuinely have no common subject
fun classify(request: Request): Route = when {
    request.isInternal -> Route.DIRECT
    request.payloadBytes > MAX_INLINE_BYTES -> Route.STREAMED
    else -> Route.QUEUED
}
```

## 22.6 Bind the subject in the `when` header when a branch needs it.

> Why? `when (val x = expr)` scopes `x` to the `when` itself — the language
> reference notes that "the scope of a variable introduced as the subject is
> restricted to the body of the `when` expression or statement." Hoisting the
> binding to an enclosing `val` leaks it into the rest of the function, where a
> later reader has to prove it is not reused, and it separates the computation
> from the only place it is consumed. **Suggestion.**

```kotlin
// bad — `parsed` outlives the when and is visible for the rest of the function
fun describe(input: String): String {
    val parsed = input.toIntOrNull()
    return when (parsed) {
        null -> "not a number: $input"
        0 -> "zero"
        else -> "number $parsed"
    }
}

// good — the binding lives exactly as long as the decision that needs it
fun describe(input: String): String = when (val parsed = input.toIntOrNull()) {
    null -> "not a number: $input"
    0 -> "zero"
    else -> "number $parsed"
}
```

## 22.7 Use a guard condition instead of nesting a second `if` or `when` inside a branch.

> Why? Guard conditions — a secondary `if` after the branch condition — became
> **Stable in Kotlin 2.2** and need no opt-in flag on the 2.4 floor. They let a
> branch refine its match without opening a nested block, which keeps the
> decision table flat and keeps every outcome visible in one column. Nesting an
> `if` inside a branch hides one of the outcomes a level deeper than its peers.
> Note the two restrictions the
> [language reference](https://kotlinlang.org/docs/control-flow.html) records:
> guards require a subject, and "you can't use guard conditions when you have
> multiple conditions separated by a comma." The coding conventions on
> [guard conditions](https://kotlinlang.org/docs/coding-conventions.html#guard-conditions-in-when-expression)
> add that combined boolean expressions must be parenthesized. **Suggestion.**

```kotlin
sealed interface Delivery {
    data class Shipped(val trackingId: String?, val carrier: String) : Delivery
    data object Preparing : Delivery
}

// bad — the refinement is nested, so "shipped without tracking" reads as a
// second-class outcome
fun status(delivery: Delivery): String = when (delivery) {
    is Delivery.Shipped -> {
        if (delivery.trackingId == null) {
            "shipped, tracking pending"
        } else {
            "tracking ${delivery.trackingId}"
        }
    }
    Delivery.Preparing -> "preparing"
}

// good — every outcome is one branch, and the boolean combination is
// parenthesized as the conventions require
fun status(delivery: Delivery): String = when (delivery) {
    is Delivery.Shipped if (delivery.trackingId == null || delivery.carrier.isBlank()) ->
        "shipped, tracking pending"
    is Delivery.Shipped -> "tracking ${delivery.trackingId}"
    Delivery.Preparing -> "preparing"
}
```

## 22.8 Group branches that share a body with comma-separated conditions rather than duplicating the body.

> Why? Duplicated branch bodies drift. Two enum constants that must always
> behave alike are a fact about the domain, and a comma states it; two identical
> right-hand sides state it only by coincidence, and the next edit to one of
> them breaks the invariant with no diagnostic. The coding conventions'
> [when entry](https://kotlinlang.org/docs/coding-conventions.html#when-entry)
> formatting example shows the multi-line comma-separated form, trailing comma
> included. **Suggestion.**

```kotlin
// bad — three identical bodies that must be kept in sync by hand
fun isRetryable(outcome: Outcome): Boolean = when (outcome) {
    Outcome.THROTTLED -> true
    Outcome.UPSTREAM_ERROR -> true
    Outcome.TIMEOUT -> true
    Outcome.ACCEPTED -> false
}

// good — one body, and the grouping is the statement
fun isRetryable(outcome: Outcome): Boolean = when (outcome) {
    Outcome.THROTTLED,
    Outcome.UPSTREAM_ERROR,
    Outcome.TIMEOUT,
    -> true
    Outcome.ACCEPTED -> false
}
```

## 22.9 Use `is` in a `when` branch and rely on the smart cast; never cast again inside the body.

> Why? An `is` branch smart-casts the subject for the whole branch body, so a
> further `as` cast is noise that a reader must still verify. Worse, a
> hand-written `as` is a second, unchecked assertion — change the branch
> condition and the cast becomes a `ClassCastException` at runtime rather than
> a compile error, because the compiler stops relating the two. Note that
> `detekt/UnsafeCast` does **not** catch this: it "reports casts that will
> never succeed," and a redundant cast always succeeds. **Suggestion.**

```kotlin
// bad — the cast repeats what `is` already proved, and can go stale
fun summarize(event: Any): String = when (event) {
    is OrderPlaced -> "order ${(event as OrderPlaced).orderId}"
    is OrderShipped -> "shipped ${(event as OrderShipped).trackingId}"
    else -> "unknown"
}

// good — smart cast covers the whole branch body
fun summarize(event: Any): String = when (event) {
    is OrderPlaced -> "order ${event.orderId}"
    is OrderShipped -> "shipped ${event.trackingId}"
    else -> "unknown"
}
```

## 22.10 Use `in` with a range or a collection rather than chained comparisons.

> Why? `x >= 1 && x <= 10` states a range with four tokens and two chances to
> invert an operator; `x in 1..10` states it once, with the boundary
> inclusiveness visible in the operator itself. `in` also works against
> collections, so a membership test does not degrade into a chain of `||`.
> detekt's `ComplexCondition` fires when the `&&`/`||` chain grows past the
> configured threshold, which is exactly the symptom `in` removes.
> **Suggestion** for the range rewrite itself; the resulting complexity
> reduction is what tooling sees.

```kotlin
// bad — four comparisons and a disjunction chain
fun band(score: Int): Band = when {
    score >= 0 && score <= 39 -> Band.FAIL
    score >= 40 && score <= 69 -> Band.PASS
    score >= 70 && score <= 100 -> Band.DISTINCTION
    else -> Band.INVALID
}

fun isTerminal(status: String): Boolean =
    status == "settled" || status == "refunded" || status == "cancelled"

// good
fun band(score: Int): Band = when (score) {
    in 0..39 -> Band.FAIL
    in 40..69 -> Band.PASS
    in 70..100 -> Band.DISTINCTION
    else -> Band.INVALID
}

private val TERMINAL_STATUSES = setOf("settled", "refunded", "cancelled")

fun isTerminal(status: String): Boolean = status in TERMINAL_STATUSES
```

## 22.11 Use `..<` for an open-ended range; never write `0..n - 1`.

> Why? The coding conventions'
> [loops on ranges](https://kotlinlang.org/docs/coding-conventions.html#loops-on-ranges)
> section marks `for (i in 0..n - 1)` as "bad" and `for (i in 0..<n)` as
> "good," and the reason is the off-by-one it removes: `n - 1` is an arithmetic
> expression that must be re-derived by every reader, and it is wrong when `n`
> is zero (`0..-1` is empty, which happens to be right, but `1..n - 1` for a
> one-based loop is not). The `..<` operator was previewed in Kotlin 1.7.20 and
> became Stable in 1.8.0; the
> [1.9.0 release notes](https://kotlinlang.org/docs/whatsnew19.html#stable-operator-for-open-ended-ranges)
> record that the open-ended-range standard library API became Stable in 1.9.0.
> Either way it needs no opt-in on the 2.4 floor. **Suggestion — `detekt/RangeUntilInsteadOfRangeTo` covers this, but it is
> absent from detekt 1.23.8's default config (the docs site is ahead of the
> latest stable release), so it cannot be enabled on that version. Re-check on
> upgrade; see chapter 47.**

```kotlin
// bad
for (i in 0..items.size - 1) {
    process(items[i])
}

// good
for (i in 0..<items.size) {
    process(items[i])
}

// good — descending and stepped ranges keep their own operators
for (i in items.size - 1 downTo 0) {
    process(items[i])
}
for (i in 0..100 step 5) {
    sample(i)
}
```

## 22.12 Iterate the collection itself; reach for `indices` or `withIndex()` only when you genuinely need the position.

> Why? Indexing through a `List` re-does a bounds check and a lookup on every
> iteration, and it puts an `items[i]` expression between the reader and the
> element. When the index really is part of the computation, `withIndex()`
> destructures both at once — which is strictly better than `indices` plus a
> manual lookup, because it cannot desynchronise the two. **Suggestion.**

```kotlin
// bad — index used only to reach the element
for (i in items.indices) {
    render(items[i])
}

// bad — index and element fetched separately; easy to index the wrong list
for (i in items.indices) {
    render(i, items[i])
}

// good
for (item in items) {
    render(item)
}

// good — index is genuinely part of the output
for ((index, item) in items.withIndex()) {
    render(index, item)
}
```

## 22.13 Prefer `filter`/`map` to a loop, and a plain `for` loop to `forEach`.

> Why? The coding conventions'
> [loops](https://kotlinlang.org/docs/coding-conventions.html#loops) section
> gives both halves of this rule: "Prefer using higher-order functions
> (`filter`, `map` etc.) to loops. Exception: `forEach` (prefer using a regular
> `for` loop instead, unless the receiver of `forEach` is nullable or `forEach`
> is used as part of a longer call chain)." `forEach` buys nothing over `for` —
> it is the same imperative loop with a lambda's `it` in place of a named
> variable — while `filter`/`map` change the shape of the code from "how" to
> "what." The same section warns to "keep performance considerations in mind"
> when a chain replaces a loop; see
> [Chapter 20](20-collections-and-sequences.md) for when to reach for a
> `Sequence`. **Suggestion.**

```kotlin
// bad — imperative accumulation
fun activeEmails(users: List<User>): List<String> {
    val result = mutableListOf<String>()
    users.forEach { user ->
        if (user.isActive) {
            result += user.email
        }
    }
    return result
}

// good
fun activeEmails(users: List<User>): List<String> =
    users.filter { it.isActive }.map { it.email }

// good — a side-effecting loop is a `for`, not a `forEach`
for (user in users) {
    auditLog.record(user.id)
}

// good — forEach earns its place at the end of a chain
users.asSequence()
    .filter { it.isActive }
    .take(BATCH_SIZE)
    .forEach { auditLog.record(it.id) }
```

## 22.14 Use `repeat(n)` when the loop body ignores the index.

> Why? `for (i in 0..<n)` declares `i` and then never reads it, which forces a
> reader to scan the body to confirm the index is genuinely unused, and it
> tempts the next editor to start using it. `repeat` says "n times" in the
> construct itself. It still passes the index to the lambda when you want it, so
> nothing is given up. **Suggestion.**

```kotlin
// bad — `attempt` is declared and never read
for (attempt in 0..<MAX_ATTEMPTS) {
    warmUpCache()
}

// good
repeat(MAX_ATTEMPTS) {
    warmUpCache()
}

// good — repeat still supplies the index when it matters
repeat(MAX_ATTEMPTS) { attempt ->
    logger.debug { "warm-up pass $attempt" }
    warmUpCache()
}
```

## 22.15 Use `while` and `do-while` only when the iteration count is genuinely unknown in advance.

> Why? A `while` with a hand-maintained index is a `for` loop with three extra
> failure modes: the counter can be initialised wrong, incremented in the wrong
> place, or not incremented at all on an early `continue` — the last of which is
> an infinite loop that no test with a small fixture will catch. Reserve `while`
> for genuinely unbounded iteration (draining a queue, polling until a
> condition), and reserve `do-while` for the narrow case where the body must run
> at least once. **Suggestion.**

```kotlin
// bad — a for loop written the hard way; `continue` skips the increment
var i = 0
while (i < items.size) {
    if (items[i].isSkipped) continue // never terminates
    process(items[i])
    i++
}

// good
for (item in items) {
    if (item.isSkipped) continue
    process(item)
}

// good — genuinely unbounded: while is the right construct
while (true) {
    val batch = queue.poll(POLL_TIMEOUT) ?: break
    process(batch)
}
```

## 22.16 Return early with a guard clause instead of nesting the happy path.

> Why? Every level of nesting adds a condition the reader must hold in mind to
> understand the innermost line. A guard clause discharges one condition and
> forgets it, so the happy path stays at a single indent level regardless of how
> many preconditions there are. **Suggestion** — no tool enforces the rewrite
> itself. detekt's `NestedBlockDepth` is active by default but only reports past
> its default `allowedDepth` of `4`, which the three-deep example below does not
> reach; `ReturnCount` (active by default, `max` of `2`,
> `excludeGuardClauses` defaulting to `false`) pushes the other way and will
> flag the rewritten version until guard clauses are excluded in configuration.
> See also `detekt/CollapsibleIfStatements` for the adjacent case of two nested
> `if`s that should be one.

```kotlin
// bad — the one line that does the work is four levels deep
fun publish(draft: Draft?, actor: Actor): PublishResult {
    if (draft != null) {
        if (actor.canPublish) {
            if (draft.body.isNotBlank()) {
                return repository.publish(draft, actor)
            } else {
                return PublishResult.Rejected("empty body")
            }
        } else {
            return PublishResult.Rejected("not permitted")
        }
    } else {
        return PublishResult.Rejected("no draft")
    }
}

// good — each precondition is discharged and forgotten
fun publish(draft: Draft?, actor: Actor): PublishResult {
    if (draft == null) return PublishResult.Rejected("no draft")
    if (!actor.canPublish) return PublishResult.Rejected("not permitted")
    if (draft.body.isBlank()) return PublishResult.Rejected("empty body")

    return repository.publish(draft, actor)
}
```

## 22.17 Use the elvis-with-`return` idiom to discharge a nullable precondition in a single line.

> Why? `?:` accepts any expression of type `Nothing` on its right-hand side —
> `return`, `throw`, `continue`, `break` — because `Nothing` is a subtype of
> every type. That makes "unwrap or leave" a single expression instead of a
> four-line `if (x == null) { ... }` block, and it smart-casts the value to
> non-null for the rest of the function. This is the idiom that makes `!!`
> unnecessary; see [Chapter 6, Null Safety](06-null-safety.md).
> **Suggestion.**

```kotlin
// bad — three lines and a second mention of the name to unwrap one value
fun rate(order: Order): Money {
    val customer = customers.find(order.customerId)
    if (customer == null) {
        return Money.ZERO
    }
    return pricing.rate(customer, order)
}

// good — unwrap and exit in one expression; `customer` is non-null below
fun rate(order: Order): Money {
    val customer = customers.find(order.customerId) ?: return Money.ZERO
    return pricing.rate(customer, order)
}

// good — the same idiom inside a loop, using `continue`
for (id in orderIds) {
    val order = orders.find(id) ?: continue
    process(order)
}
```

## 22.18 Use non-local `break` and `continue` inside an inline lambda rather than restructuring around it.

> Why? Since **Kotlin 2.2** this is Stable and needs no flag: `break` and
> `continue` work inside a lambda passed to an inline function that is enclosed
> by a loop. Before it, the only way to abandon an iteration from inside a
> `run`, `let`, or `also` block was a labelled return plus a sentinel value the
> loop then had to re-test — two constructs to express one intent. The
> [inline functions reference](https://kotlinlang.org/docs/inline-functions.html)
> gives the canonical form. Note this applies to *inline* functions only; a
> lambda passed to a non-inline function still cannot `break` the enclosing
> loop. **Suggestion.**

```kotlin
// bad — a sentinel and a re-test to express "skip this element"
for (element in elements) {
    val variable = element.nullableMethod() ?: run {
        log.warning("Element is null or invalid")
        null
    }
    if (variable == null) continue
    if (variable == 0) return true
}

// good — continue directly from inside the inline lambda
for (element in elements) {
    val variable = element.nullableMethod() ?: run {
        log.warning("Element is null or invalid, continuing...")
        continue
    }
    if (variable == 0) return true
}
```

## 22.19 Treat a label as a last resort, after extracting a function has failed.

> Why? A label makes a jump's target non-local, so a reader must scan outward
> to find where control lands — the same objection that applies to `goto`. Nine
> times out of ten the labelled loop is a search, and extracting it into a
> function replaces `break@outer` with `return`, which needs no label at all and
> gives the search a name. detekt treats labels and jump-heavy loops as smells
> in their own right. **Violation — enforced by `detekt/LabeledExpression`**
> (complexity rule set; **not active in detekt's default configuration**, so it
> must be switched on deliberately) **and `detekt/LoopWithTooManyJumpStatements`**
> (style rule set, active by default, `maxJumpCount` of `1`); see also
> `detekt/UnconditionalJumpStatementInLoop` for the degenerate case of a loop
> that always jumps on its first iteration.

```kotlin
// bad — labelled break; the reader must find `outer@` to know where this lands
fun findPair(rows: List<List<Int>>, target: Int): Pair<Int, Int>? {
    var found: Pair<Int, Int>? = null
    outer@ for (row in rows) {
        for (value in row) {
            if (value == target) {
                found = row.first() to value
                break@outer
            }
        }
    }
    return found
}

// good — extracting the search turns the jump into a plain return
fun findPair(rows: List<List<Int>>, target: Int): Pair<Int, Int>? =
    rows.firstNotNullOfOrNull { row -> row.findMatch(target) }

private fun List<Int>.findMatch(target: Int): Pair<Int, Int>? =
    firstOrNull { it == target }?.let { first() to it }
```

## 22.20 Compare a nullable `Boolean` with `== true` or `== false`; never with `!!` or `?: false`.

> Why? The coding conventions are unambiguous: "If you need to use a nullable
> `Boolean` in a conditional statement, use `if (value == true)` or
> `if (value == false)` checks." `== true` handles all three states in one
> token, whereas `?: false` restates the default at every use site and `!!`
> converts an ordinary null into a crash. Note that `== true` and `!= false`
> are *different* — they disagree on `null` — so the choice must be deliberate.
> **Violation — enforced by `detekt/NullableBooleanCheck`,** which flags the
> elvis form in favour of the equality form.

```kotlin
// bad — !! crashes on null; ?: restates the default at every call site
if (user.preferences?.wantsEmail!!) {
    send(user)
}
if (user.preferences?.wantsEmail ?: false) {
    send(user)
}

// good — null is handled by the comparison itself
if (user.preferences?.wantsEmail == true) {
    send(user)
}

// good — the opposite default, stated deliberately
if (user.preferences?.suppressEmail != true) {
    send(user)
}
```

## 22.21 Never use an exception to direct ordinary control flow.

> Why? An exception is a non-local jump with no declared target, no type
> checking at the throw site, and — because Kotlin has no checked exceptions —
> nothing in the signature to warn a caller it exists. Using one to escape a
> loop or signal "not found" makes the control flow invisible in the code and
> costs a stack trace capture on a path that is not exceptional at all. Model
> absence with a nullable return, and model a closed set of outcomes with a
> sealed type ([Chapter 13](13-sealed-types.md)). The full treatment, including
> `require`/`check`/`error` and why `Result` is not the answer either, is
> [Chapter 24](24-exceptions-and-result.md). **Suggestion** for the design; the
> individual symptoms are caught by `detekt/TooGenericExceptionThrown` and
> `detekt/SwallowedException`.

```kotlin
// bad — an exception used as a loop exit and as a "not found" signal
private class Found(val user: User) : RuntimeException()

fun firstAdmin(users: List<User>): User? {
    try {
        users.forEach { if (it.isAdmin) throw Found(it) }
    } catch (e: Found) {
        return e.user
    }
    return null
}

// good — absence is a nullable return, and the search is a library call
fun firstAdmin(users: List<User>): User? = users.firstOrNull { it.isAdmin }
```
