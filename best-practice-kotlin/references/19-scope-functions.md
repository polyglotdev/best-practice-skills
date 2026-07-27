<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 19. Scope Functions

`let`, `run`, `with`, `apply`, and `also` do nothing you could not write with a
local `val` and a plain call. They exist to make an intent shorter, and they are
the single most misused feature in the language precisely because all five look
interchangeable at a glance. They are not: each one makes exactly two decisions,
and picking the wrong combination produces code that compiles, reads fluently,
and returns the wrong thing.

This chapter draws on the Kotlin coding conventions'
[scope functions](https://kotlinlang.org/docs/coding-conventions.html#scope-functions-apply-with-run-also-let)
pointer and the language documentation's
[Scope functions](https://kotlinlang.org/docs/scope-functions.html) page, which
carries the normative selection table and this warning: "Although scope
functions can make your code more concise, avoid overusing them: it can make
your code hard to read and lead to errors. We also recommend that you avoid
nesting scope functions and be careful when chaining them because it's easy to
get confused about the current context object and value of `this` or `it`."

Three neighbouring topics are deferred. The `?.`, `?:`, and smart-cast
machinery that `let` is so often used to imitate is
[Chapter 6, Null Safety](06-null-safety.md). Lambda parameter naming,
`inline`, and non-local returns in general are
[Chapter 9, Lambdas & Higher-Order Functions](09-lambdas-and-higher-order-functions.md).
Early returns, `if` versus `when`, and guard clauses are
[Chapter 22, Control Flow & `when`](22-control-flow-and-when.md) — and §19.17
argues that a guard clause beats a scope function more often than most Kotlin
code admits.

**Tool alignment:** several rules below are mechanically enforced.
detekt's `complexity/NestedScopeFunctions` fires on a scope function nested
inside another; `complexity/ReplaceSafeCallChainWithRun` fires on a `?.` chain
that needs only one null check; `style/UnnecessaryApply` and
`style/UnnecessaryLet` fire on the single-expression forms a direct call says
better; `style/AlsoCouldBeApply` fires on an `also` whose block is entirely
`it.`-prefixed; and `style/MultilineLambdaItParameter` fires on a multi-statement
lambda leaning on the implicit `it`. Rules a named check actually enforces are
marked **Violation**; the rest are **Suggestion**.

## 19.1 Choose a scope function from its two-axis contract, not from habit.

> Why? Every scope function answers exactly two questions: how is the context
> object bound inside the block (`this` receiver, or `it` argument), and what
> comes out (the lambda result, or the context object itself). The
> [Scope functions](https://kotlinlang.org/docs/scope-functions.html) page
> publishes this as a table, and it is the whole decision procedure. Choosing
> `apply` when you meant `run` does not fail to compile — it silently gives the
> expression the receiver's type instead of the computed one, and the mistake
> surfaces as a type error somewhere else, or not at all. **Suggestion.**
>
> | Function | Context object | Returns | Extension |
> |---|---|---|---|
> | `let` | `it` (argument) | lambda result | yes |
> | `run` | `this` (receiver) | lambda result | yes |
> | `run { }` (non-extension) | none | lambda result | no |
> | `with` | `this` (receiver) | lambda result | no |
> | `apply` | `this` (receiver) | the context object | yes |
> | `also` | `it` (argument) | the context object | yes |

```kotlin
// bad — `apply` returns the receiver, so `total` is an Order, not a Long; the
// sum inside the block is computed and thrown away
val total = order.apply {
    lines.sumOf { it.amountMinor }
}

// good — `run` binds `this` and returns the lambda result
val total: Long = order.run {
    lines.sumOf { it.amountMinor }
}
```

## 19.2 Use `?.let` when you are transforming a nullable value into another value.

> Why? This is the one job `let` is uniquely good at: the safe call handles the
> null, the block does the transformation, and the null propagates through the
> result type without a branch. The alternative is a temporary plus an `if` that
> exists only to satisfy the smart cast. **Suggestion.**

```kotlin
// bad — a temporary whose only purpose is to be smart-cast
val header: String? = request.getHeader("X-Request-Id")
val requestId: RequestId? = if (header != null) RequestId.parse(header) else null

// good — the null flows through; no temporary, no branch
val requestId: RequestId? = request.getHeader("X-Request-Id")?.let(RequestId::parse)
```

## 19.3 Do not use `?.let { }` as a statement-level null guard; use an early return or a plain `if`.

> Why? `let` is an expression that produces a value. When you use it purely for
> control flow the value is `Unit` and gets discarded, so the reader has to
> parse a transformation-shaped construct only to discover it was an `if`. An
> early return states the guard once and lets the compiler smart-cast the
> variable for the rest of the function, so the body reads with no `it` at all.
> **Suggestion** — `detekt/UnnecessaryLet` catches the single-call form
> (`a?.let { it.plus(1) }`), not the multi-statement form below.

```kotlin
// bad — reads as a transformation, is actually an if; the Unit result is dropped
fun handle(session: Session?) {
    session?.let {
        audit.record(it.userId)
        it.close()
    }
}

// good — one guard, then `session` is smart-cast for the whole body
fun handle(session: Session?) {
    if (session == null) return
    audit.record(session.userId)
    session.close()
}
```

## 19.4 Use `also` for a side effect that must not change the value being passed along.

> Why? `also` returns the context object, so it is the only scope function that
> can be dropped into the middle of an expression without altering its type or
> value. Using `let` for the same job forces you to repeat `it` as the last
> statement so the block returns the right thing — and the day someone appends a
> line after that trailing `it`, the return value silently changes.
> **Suggestion.**

```kotlin
// bad — `let` returns the lambda result, so the block needs a trailing `it`
// that a future edit can easily displace
fun save(order: Order): Order =
    repository.save(order).let {
        logger.info { "saved order ${it.id}" }
        it
    }

// good — `also` returns the receiver; nothing to remember, nothing to break
fun save(order: Order): Order =
    repository.save(order).also {
        logger.info { "saved order ${it.id}" }
    }
```

## 19.5 Use `apply` only where its return value is consumed.

> Why? `apply` exists to hand back the object it just configured, so it belongs
> in an expression position: `val x = Foo().apply { ... }`. Wrapping a block of
> statements in `apply` and discarding the result buys nothing over calling the
> members directly, or over `with` when you want the receiver in scope. detekt
> flags the single-expression form outright — `config.apply { version = "1.2" }`
> is an assignment wearing a costume.
> **Violation — enforced by `detekt/UnnecessaryApply`** for the single-expression
> form; the multi-statement variant is a **Suggestion**.

```kotlin
// bad — apply's return value is discarded; this is one assignment plus syntax
config.apply { environment = "production" }

// bad — same problem stretched over a block: `apply` promises a value nobody uses
fun configure(registry: MeterRegistry) {
    registry.apply {
        config().commonTags("app", "billing")
        counter("startups").increment()
    }
}

// good
config.environment = "production"

// good — `with` says "group these calls on this receiver" and returns nothing
fun configure(registry: MeterRegistry) {
    with(registry) {
        config().commonTags("app", "billing")
        counter("startups").increment()
    }
}
```

## 19.6 Prefer construction with named arguments to `apply`-based configuration on a type you own.

> Why? `apply`-style construction requires the type to expose mutable `var`
> properties and to be constructible in an invalid intermediate state. Every
> invariant then has to be checked at some later point, if at all, and the object
> stays mutable for the rest of its life. Kotlin has named arguments and default
> parameter values, so the builder-shaped workaround Java needs has no reason to
> exist here — see
> [Chapter 11, Data Classes](11-data-classes.md). Reserve `apply` for types you
> do not own, which is where you have no choice. **Suggestion.**

```kotlin
// bad — the type must be mutable and must permit a half-built state, and
// omitting `baseUrl` compiles cleanly
val client = HttpClientConfig().apply {
    baseUrl = "https://api.example.com"
    connectTimeout = Duration.ofSeconds(5)
}

// good — immutable, validated in one place, and omitting a required argument
// is a compile error
val client = HttpClientConfig(
    baseUrl = "https://api.example.com",
    connectTimeout = Duration.ofSeconds(5),
)

// good — `apply` where you genuinely do not own the type
val builder = Request.Builder().apply {
    url(endpoint)
    header("Accept", "application/json")
}
```

## 19.7 Prefer `apply` to `also` when every statement in the block only touches the receiver's members.

> Why? The whole reason to bind the context object as `this` is that member
> calls need no qualifier. An `also` block in which every line begins with `it.`
> is paying the cost of an argument binding and getting nothing for it, and it
> misleads the next reader into looking for the line where `it` is used as an
> argument. detekt describes the pattern as "an `also` block [that] contains only
> `it`-started expressions."
> **Violation — enforced by `detekt/AlsoCouldBeApply`.**

```kotlin
// bad — every statement is `it.something`; the `it` is pure noise
val request = Request.Builder().also {
    it.url(endpoint)
    it.header("Accept", "application/json")
    it.header("X-Tenant", tenantId)
}

// good
val request = Request.Builder().apply {
    url(endpoint)
    header("Accept", "application/json")
    header("X-Tenant", tenantId)
}
```

## 19.8 Use `with` for a non-null receiver already in hand; use `?.run` when the receiver may be null.

> Why? `with` is not an extension function, so it cannot be safe-called. The
> moment the receiver is nullable, `with` forces you to either write `!!` or
> safe-call every member inside the block. `run` *is* an extension, so `?.run`
> does one null check for the entire block and yields a nullable result. Picking
> between them is a mechanical consequence of the receiver's nullability, not a
> matter of taste. **Suggestion** — the `!!` in the bad example is a
> **Violation — enforced by `detekt/UnsafeCallOnNullableType`.** See
> [Chapter 6, Null Safety](06-null-safety.md).

```kotlin
// bad — `with` cannot be safe-called, so a bang appears to make it typecheck
val summary = with(maybeOrder!!) {
    "${lines.size} lines, $totalMinor minor units"
}

// good — one null check covers the whole block, and the result is nullable
val summary: String? = maybeOrder?.run {
    "${lines.size} lines, $totalMinor minor units"
}

// good — `with` where the receiver genuinely cannot be null
val summary = with(order) {
    "${lines.size} lines, $totalMinor minor units"
}
```

## 19.9 Do not use the non-extension `run { }` to manufacture a scope.

> Why? `run { }` with no receiver is an expression-shaped block. It is
> legitimate when you need statements where an expression is required — an
> `if` branch, an initialiser that genuinely requires several steps. Using it
> merely to keep two locals out of the enclosing scope is scope hygiene theatre:
> it adds a level of indentation, hides the computation behind an anonymous
> block, and gives the reader nothing to grep for. If the block is worth
> isolating, it is worth a name. **Suggestion.**

```kotlin
// bad — a block whose only job is to keep two locals private
val connection = run {
    val host = config.host
    val port = config.port
    Connection(host, port)
}

// good — the locals were never a problem
val connection = Connection(config.host, config.port)

// good — when the computation really is long, give it a name
private fun openConnection(config: Config): Connection {
    val host = config.host.ifBlank { DEFAULT_HOST }
    val port = config.port.takeIf { it in 1..65_535 } ?: DEFAULT_PORT
    return Connection(host, port)
}

val connection = openConnection(config)
```

## 19.10 Never nest one scope function inside another.

> Why? The language documentation says it outright: "we also recommend that you
> avoid nesting scope functions". Two nested blocks that both bind the implicit
> `it` produce silent shadowing — the inner `it` wins, the compiler emits no
> warning, and a reader tracking a value through the nest has to count braces to
> know which object `it` refers to on any given line.
> **Violation — enforced by `detekt/NestedScopeFunctions`.**

```kotlin
// bad — the middle `let` binds `it` to a User, the inner one rebinds it to an
// AddressId; nothing warns, and nothing tells the reader which is which
fun resolve(userId: UserId?): Address? =
    userId?.let { id ->
        repository.findUser(id)?.let {
            it.addressId?.let { addressRepository.find(it) }
        }
    }

// good — one step per line, each with a name, no shadowing anywhere
fun resolve(userId: UserId?): Address? {
    val user = userId?.let(repository::findUser) ?: return null
    val addressId = user.addressId ?: return null
    return addressRepository.find(addressId)
}
```

## 19.11 Name the lambda parameter whenever the block contains more than one statement.

> Why? The implicit `it` is fine when the block is a single expression and the
> binding is a line away. In a multi-statement block the reader has to scroll
> back to the receiver to learn what `it` even is, and every subsequent edit
> makes the distance longer. detekt puts it as: "when you are dealing with lambdas
> that contain multiple statements, you might end up with code that is hard to read
> if you don't specify a readable, descriptive parameter name explicitly."
> **Violation — enforced by `detekt/MultilineLambdaItParameter`.**

```kotlin
// bad — three uses of `it`, and the binding is off the top of the block
repository.save(order).also {
    metrics.counter("orders.saved").increment()
    outbox.enqueue(OrderSaved(it.id))
    logger.info { "saved ${it.id} for ${it.customerId}" }
}

// good
repository.save(order).also { saved ->
    metrics.counter("orders.saved").increment()
    outbox.enqueue(OrderSaved(saved.id))
    logger.info { "saved ${saved.id} for ${saved.customerId}" }
}
```

## 19.12 Keep any scope-function chain to at most two links.

> Why? Each link in a scope-function chain can change both the bound name
> (`this` versus `it`) and the type flowing through it, and none of that is
> visible without reading the whole chain. Past two links a reader is
> effectively simulating an interpreter. Break the chain at the point where the
> meaning changes and give the intermediate value a name — the name is the
> documentation the chain was hiding. **Suggestion.**

```kotlin
private const val BEARER_PREFIX = "Bearer "

// bad — four scope functions; the bound value changes meaning three times and
// the reader must hold all of it at once
val token = rawHeader
    ?.takeIf { it.startsWith(BEARER_PREFIX) }
    ?.let { it.removePrefix(BEARER_PREFIX) }
    ?.also { logger.debug { "parsed bearer token" } }
    ?.run { Token(value = this, issuedAt = clock.instant()) }

// good — two statements, each with a name
val bearer = rawHeader?.takeIf { it.startsWith(BEARER_PREFIX) }?.removePrefix(BEARER_PREFIX)
val token = bearer?.let { Token(value = it, issuedAt = clock.instant()) }
```

## 19.13 Collapse a chain of safe calls on an already-non-null value into a single `?.run`.

> Why? In `a?.b()?.c()?.d()` only the first `?.` can ever observe a null — the
> rest re-test a value the previous call already proved non-null, and each one
> costs a branch and a line of visual noise. `?.run { }` does the null check once
> and lets the block be an ordinary chain.
> **Violation — enforced by `detekt/ReplaceSafeCallChainWithRun`.**

```kotlin
// bad — three null checks for one nullable value
val length: Int? = header?.trim()?.removeSurrounding("\"")?.length

// good — one null check, then a plain chain inside the block
val length: Int? = header?.run { trim().removeSurrounding("\"").length }
```

## 19.14 Use `takeIf` / `takeUnless` only when the `null` they manufacture is consumed immediately.

> Why? `takeIf` turns a boolean test into a nullable value. That is a win when
> the very next operator is `?:`, `?.`, or a nullable `return` — the test and the
> fallback read as one expression. It is a loss the moment the null is stored in
> a variable, because you have converted a plain boolean condition into a
> nullability problem that every downstream reader now has to reason about.
> **Suggestion.**

```kotlin
// bad — `takeIf` manufactures a null that the next line has to check by hand
val trimmed = input.trim().takeIf { it.isNotBlank() }
if (trimmed != null) {
    register(trimmed)
}

// bad — takeIf + let + elvis where a plain `if` says the same thing
val discount = order.takeIf { it.totalMinor > FREE_SHIPPING_MINOR }?.let { FLAT } ?: 0

// good — the null goes straight into `?:` or a safe call and never lands
val name = input.trim().takeIf { it.isNotBlank() } ?: DEFAULT_NAME
input.trim().takeIf { it.isNotBlank() }?.let(::register)

// good — no null is involved, so no `takeIf`
val discount = if (order.totalMinor > FREE_SHIPPING_MINOR) FLAT else 0
```

## 19.15 Never put a side effect inside a `takeIf` or `takeUnless` predicate.

> Why? The predicate of `takeIf` looks like a filter, and readers treat filters
> as pure. Hiding a metric increment, a log line, or a mutation in there means
> the effect fires on every element of a chain, in an order the reader has to
> derive from the chain's laziness, and it will be deleted the first time someone
> "simplifies" the condition. Perform the effect unconditionally, above the test.
> **Suggestion.**

```kotlin
// bad — the counter is incremented from inside what looks like a pure predicate
val session = sessionCache.load(key).takeIf {
    metrics.counter("cache.hit").increment()
    it.expiresAt.isAfter(clock.instant())
}

// good — the effect is a statement, the predicate is a predicate
val cached = sessionCache.load(key)
metrics.counter("cache.lookup").increment()
val session = cached.takeIf { it.expiresAt.isAfter(clock.instant()) }
```

## 19.16 Do not hide a non-local `return` inside a scope-function lambda.

> Why? All five scope functions are `inline`, so a bare `return` inside the block
> returns from the *enclosing function*, not from the lambda. That is a genuine
> language feature, but inside a `?.let` it produces a construct whose control
> flow depends on the receiver's nullability and on the reader knowing that `let`
> is inlined. The equivalent guard clause is two lines and needs no such
> knowledge. See
> [Chapter 9, Lambdas & Higher-Order Functions](09-lambdas-and-higher-order-functions.md)
> for the general rule on non-local returns. **Suggestion.**

```kotlin
// bad — the `return` exits findUser, not the `let`; whether it runs at all
// depends on `id` being non-null
fun findUser(id: UserId?): User? {
    id?.let { return repository.find(it) }
    return null
}

// good — the control flow is on the page
fun findUser(id: UserId?): User? {
    if (id == null) return null
    return repository.find(id)
}
```

## 19.17 When a scope function does not make the code shorter or clearer, use a local `val` and an early return.

> Why? This is the honest default, and the rule the other sixteen collapse into.
> A scope function earns its place by removing a name that carried no
> information or a branch that carried no meaning. When it removes neither, it
> has added a level of indentation, a rebound `this` or `it`, and a return type
> the reader must derive from the table in §19.1. A named local plus a guard
> clause has none of those costs and is trivially debuggable — you can set a
> breakpoint on it. **Suggestion.**

```kotlin
// bad — three scope functions to express two conditions and one construction
fun price(sku: Sku?): Money? =
    sku?.let { catalog.find(it) }
        ?.takeIf { it.isAvailable }
        ?.run { Money.ofMinor(priceMinor, currency) }

// good — every intermediate has a name and every exit is visible
fun price(sku: Sku?): Money? {
    val item = sku?.let(catalog::find) ?: return null
    if (!item.isAvailable) return null
    return Money.ofMinor(item.priceMinor, item.currency)
}
```
