<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 9. Lambdas & Higher-Order Functions

Kotlin makes functions first-class in a way Java's functional interfaces never
quite managed: a lambda is a value with a structural type, `inline` can erase
it at the call site entirely, and `reified` lets an inlined function see its
own type arguments at runtime. That power comes with a set of rules that are
genuinely non-obvious — a bare `return` inside a lambda does not return from
the lambda, `inline` on the wrong function is a pessimisation the compiler
warns about, and `crossinline` exists to close a hole most people never notice
until the compiler refuses to build.

This chapter covers the lambda as written and the higher-order function that
receives it. It draws on the Kotlin coding conventions'
[lambdas](https://kotlinlang.org/docs/coding-conventions.html#lambdas),
[lambda parameters](https://kotlinlang.org/docs/coding-conventions.html#lambda-parameters),
[parameters in lambdas](https://kotlinlang.org/docs/coding-conventions.html#parameters-in-lambdas),
and [returns in a lambda](https://kotlinlang.org/docs/coding-conventions.html#returns-in-a-lambda)
sections, plus the language reference for
[higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html),
[returns and jumps](https://kotlinlang.org/docs/returns.html),
[inline functions](https://kotlinlang.org/docs/inline-functions.html), and
[functional (SAM) interfaces](https://kotlinlang.org/docs/fun-interfaces.html).

Three neighbouring topics are deferred. **The signature side of a function** —
expression bodies, default arguments, parameter ordering, extensions — is
[Chapter 8](08-functions.md); §9.20 here is the higher-order-function
elaboration of §8.6 there, and §9.3 is the call-site syntax both enable.
**Scope functions** (`let`, `run`, `apply`, `also`, `with`), which
are just inline higher-order functions with a house style of their own, are
[Chapter 19](19-scope-functions.md). **`suspend` lambdas**, `suspend` function
types, and why `inline` interacts with cancellation are
[Chapter 33](33-coroutine-fundamentals.md) onward.

**Tool alignment:** ktlint's `standard:unnecessary-parentheses-before-trailing-lambda`
(stable since ktlint 1.0) and `standard:lambda-return` (experimental since
ktlint 2.0, enable it explicitly) both fire in the format step. detekt's `ReturnCount`
(on by default, capped at two) and `LabeledExpression` (off by default) cover
the multiple-exit-point rules in the analysis step. The Kotlin compiler itself
warns on a useless `inline`, and refuses outright to compile the `noinline` and
`crossinline` cases below. Rules a named check actually covers are marked
**Violation**; the rest are **Suggestion**.

## 9.1 Use the implicit `it` only in a short lambda that is not nested; declare parameters explicitly everywhere else.

> Why? The Kotlin coding conventions'
> [lambda parameters](https://kotlinlang.org/docs/coding-conventions.html#lambda-parameters)
> section draws the line exactly here: "In lambdas which are short and not
> nested, it's recommended to use the `it` convention instead of declaring the
> parameter explicitly. In nested lambdas with parameters, always declare
> parameters explicitly." The reason is shadowing — an inner `it` hides the
> outer one, so the outer value becomes unreachable and a reader has to count
> brace levels to work out which object a given `it` refers to. The compiler
> warns about the shadowing, but the readability cost lands even when the
> shadowing is intentional. **Suggestion.**

```kotlin
// bad — nested lambdas both using `it`; the inner one shadows the outer, so
// the order is unreachable inside the inner body
orders.forEach {
    it.lines.forEach {
        println(it.sku)
    }
}

// bad — long enough that `it` no longer says anything
records.map {
    Report(it.id, it.tenantId, it.createdAt, it.total, it.currency, it.status)
}

// good — `it` in a short, flat lambda
val activeIds = users.filter { it.isActive }.map { it.id }

// good — named parameters once there is nesting or length
orders.forEach { order ->
    order.lines.forEach { line ->
        println("${order.id}: ${line.sku}")
    }
}
```

## 9.2 Name an unused lambda parameter `_`.

> Why? The
> [lambdas reference](https://kotlinlang.org/docs/lambdas.html#underscore-for-unused-variables)
> notes that "if the lambda parameter is unused, you can place an underscore
> instead of its name." A real name on an unused parameter is a lie the reader
> has to disprove — they will look for the use, not find it, and wonder what
> they missed. `_` says "deliberately ignored" in one character, and it is
> especially valuable in destructured `Map.Entry` lambdas where the shape
> forces you to accept both components. **Suggestion.**

```kotlin
// bad — `key` is declared and never used; a reader has to scan for it
headers.forEach { (key, value) ->
    logger.debug(value)
}

// bad — the same problem in a non-destructured position
retryWith { attempt, error ->
    logger.warn("retrying", error)
}

// good
headers.forEach { (_, value) ->
    logger.debug(value)
}

retryWith { _, error ->
    logger.warn("retrying", error)
}
```

## 9.3 Move a trailing lambda outside the parentheses, and drop the parentheses when the lambda is the only argument.

> Why? The
> [lambdas reference](https://kotlinlang.org/docs/lambdas.html#passing-trailing-lambdas)
> states the convention: "if the last parameter of a function is a function,
> then a lambda expression passed as the corresponding argument can be placed
> outside the parentheses," and "if the lambda is the only argument in that
> call, the parentheses can be omitted entirely." This is what makes
> `transaction { ... }`, `measureTime { ... }`, and every Kotlin DSL read like
> a language construct instead of a method call. Leaving an empty `()` in
> front of the lambda is pure noise.
> **Violation — enforced by
> `ktlint standard:unnecessary-parentheses-before-trailing-lambda`** for the
> empty-parentheses case.

```kotlin
// bad — the lambda is the last argument but sits inside the parentheses
val product = items.fold(1, { acc, item -> acc * item.quantity })

// bad — empty parentheses before a trailing lambda
transaction() {
    repository.save(order)
}

// good
val product = items.fold(1) { acc, item -> acc * item.quantity }

transaction {
    repository.save(order)
}
```

## 9.4 Keep the parenthesised, named form when a call takes more than one lambda.

> Why? Only the *last* lambda can be lifted out of the parentheses, so a call
> with two function arguments ends up with one inside and one outside. That
> shape reads as though the trailing lambda were the body of the operation and
> the other one were configuration, when in fact the two are peers. Naming
> both and keeping both inside the parentheses restores the symmetry and makes
> the argument order impossible to get wrong. This is the call-site
> counterpart to §8.8's named-argument rule. **Suggestion.**

```kotlin
// bad — the two branches are peers but the syntax makes one look primary,
// and nothing at the call site says which is which
result.fold({ value -> render(value) }) { error -> logger.warn("failed", error) }

// good — both named, both inside the parentheses, order irrelevant
result.fold(
    onSuccess = { value -> render(value) },
    onFailure = { error -> logger.warn("failed", error) },
)
```

## 9.5 Do not use a labelled return for the last statement of a lambda.

> Why? The Kotlin coding conventions'
> [returns in a lambda](https://kotlinlang.org/docs/coding-conventions.html#returns-in-a-lambda)
> section says it outright: "Do not use a labeled return for the last
> statement in a lambda." The value of a lambda's last expression *is* its
> result, so `return@map name` on the final line adds a keyword, a label, and
> a false suggestion that there is some other exit path the reader has to find.
> **Violation — enforced by `ktlint standard:lambda-return`** (experimental
> since ktlint 2.0; enable it explicitly).

```kotlin
// bad — a labelled return on the last statement
val names = users.map { user ->
    val name = user.displayName ?: user.email
    return@map name
}

// good — the last expression is the result
val names = users.map { user ->
    user.displayName ?: user.email
}
```

## 9.6 Do not put more than one labelled return in a single lambda.

> Why? The same conventions section continues: "Avoid using multiple labeled
> returns in a lambda. Consider restructuring the lambda so that it will have
> a single exit point. If that's not possible or not clear enough, consider
> converting the lambda into an anonymous function." Multiple `return@forEach`
> statements are `continue` in disguise — the reference makes the analogy
> explicitly — and a reader has to simulate the whole body to work out which
> elements actually reach the bottom. A `filter` in front of the loop says the
> same thing declaratively.
> **Violation — enforced by `detekt/LabeledExpression`** (in the `complexity`
> ruleset; it ships `active: false`, so turn it on). `detekt/ReturnCount`
> catches the same shape in named functions and *is* on by default, capped at
> two returns.

```kotlin
// bad — three exit points; the reader has to simulate the body
orders.forEach { order ->
    if (order.isCancelled) return@forEach
    if (order.total.isZero()) return@forEach
    if (!order.isPaid) return@forEach
    ship(order)
}

// good — one exit point, and the predicate has a name worth testing
orders
    .filter { it.isShippable() }
    .forEach { ship(it) }

private fun Order.isShippable(): Boolean =
    !isCancelled && !total.isZero() && isPaid
```

## 9.7 Know that a bare `return` inside a lambda exits the *enclosing function*, and only compiles when the lambda is inlined.

> Why? This is the single most misread construct in Kotlin. The
> [lambdas reference](https://kotlinlang.org/docs/lambdas.html#anonymous-functions)
> spells it out: "a `return` statement without a label always returns from the
> function declared with the `fun` keyword. This means that a `return` inside
> a lambda expression will return from the enclosing function." The
> [returns reference](https://kotlinlang.org/docs/returns.html#return-to-labels)
> adds the constraint that makes this legal at all: such "non-local returns
> are located in a lambda but exit the enclosing inline function," so the same
> code inside a lambda passed to a *non-inline* function is a compile error.
> The practical consequence: `forEach { return x }` works (because `forEach`
> is `inline`) and does something quite different from what a Java reader
> expects, while the identical line inside your own non-inline higher-order
> function will not build. **Suggestion.**

```kotlin
// bad — `return user` exits findFirstAdmin, not the lambda. It happens to be
// what was meant here, but every reader has to stop and check.
fun findFirstAdmin(users: List<User>): User? {
    users.forEach { user ->
        if (user.isAdmin) return user
    }
    return null
}

// bad — does not compile: `runLater` is not inline, so there is no enclosing
// frame for the non-local return to unwind to
fun runLater(block: () -> Unit) {
    queue += block
}

fun schedule(user: User) {
    runLater {
        if (user.isAdmin) return // error: 'return' is not allowed here
        audit(user)
    }
}

// good — say what you mean; no control flow to decode
fun findFirstAdmin(users: List<User>): User? = users.firstOrNull { it.isAdmin }

fun schedule(user: User) {
    runLater {
        if (!user.isAdmin) {
            audit(user)
        }
    }
}
```

## 9.8 Use an anonymous function when you need a declared return type or an ordinary local `return`.

> Why? The
> [lambdas reference](https://kotlinlang.org/docs/lambdas.html#anonymous-functions)
> gives anonymous functions exactly two jobs a lambda cannot do. First, lambda
> syntax lacks "the ability to specify the function's return type," and an
> anonymous function is the "alternative syntax" the reference names for when
> "you do need to specify it explicitly." Second, "a `return` inside an
> anonymous function will return from the anonymous function itself" — no
> label, no non-local surprise. The conventions point
> here too, as the escape hatch when a lambda genuinely needs more than one
> exit point (§9.6). The cost is verbosity, so reach for this only when one of
> those two needs is real. **Suggestion.**

```kotlin
// bad — a lambda forced into labelled returns to express early exit, with no
// declared return type to check the branches against
val kept = candidates.filter { value ->
    if (value.isBlank()) return@filter false
    if (value.length <= 3) return@filter false
    value.first().isLetter()
}

// good — an anonymous function: real signature, ordinary returns
val kept = candidates.filter(fun(value: String): Boolean {
    if (value.isBlank()) return false
    if (value.length <= 3) return false
    return value.first().isLetter()
})

// good — better still, name the predicate
val kept = candidates.filter(::isUsableToken)
```

## 9.9 Prefer a callable reference to a lambda whose body is a single forwarding call.

> Why? A lambda whose entire body is `{ x -> f(x) }` introduces a parameter
> name that carries no information and a pair of braces that suggest there is
> a body worth reading. The
> [lambdas reference](https://kotlinlang.org/docs/lambdas.html#instantiating-a-function-type)
> lists function references (`::isOdd`, `String::toInt`) as a first-class way
> to instantiate a function type, and at the call site they read as the name
> of the operation rather than as a block of code. Stop short of contorting a
> reference to avoid a lambda: `{ it.total * 2 }` is not a forwarding call and
> should stay a lambda. **Suggestion.**

```kotlin
// bad — the lambda exists only to name a parameter and hand it straight on
val parsed: List<Int> = tokens.map { token -> token.toInt() }
val trimmed: List<String> = raw.map { value -> value.trim() }

// good
val parsed: List<Int> = tokens.map(String::toInt)
val trimmed: List<String> = raw.map(String::trim)

// good — not a forwarding call; leave it as a lambda
val doubled: List<Long> = orders.map { it.totalMinorUnits * 2 }
```

## 9.10 Use a bound callable reference when the receiver is fixed, and an unbound one when the receiver is the parameter.

> Why? The two forms produce different function types and mixing them up
> produces a confusing type error rather than a helpful one. An unbound
> reference such as `String::uppercase` turns the receiver into the function's
> first parameter, giving `(String) -> String`. A
> [bound callable reference](https://kotlinlang.org/docs/lambdas.html#instantiating-a-function-type)
> such as `repository::findName` fixes the receiver at the point the reference
> is created, giving `(UserId) -> String`. Choosing the bound form when the
> receiver is a collaborator removes a captured variable and a lambda from the
> call site. Note that a bound reference evaluates its receiver expression
> *once*, when the reference is created — not on each invocation. **Suggestion.**

```kotlin
// unbound — the receiver becomes the first parameter
val toUpper: (String) -> String = String::uppercase
val shouted: List<String> = words.map(toUpper)

// bound — the receiver is fixed when the reference is created
val greeting = "hello"
val shout: () -> String = greeting::uppercase

// bad — the lambda captures `repository` only to forward the parameter
val names: List<String> = ids.map { id -> repository.findName(id) }

// good — a bound reference says the same thing with no capture
val names: List<String> = ids.map(repository::findName)
```

## 9.11 Use a constructor reference instead of a lambda that only calls a constructor.

> Why? `::OrderId` is listed alongside function references in the
> [lambdas reference](https://kotlinlang.org/docs/lambdas.html#instantiating-a-function-type)
> as a way to instantiate a function type, and it reads as "make one of
> these," which is exactly the intent. It also survives a constructor
> signature change more gracefully than a lambda: adding a parameter turns the
> reference into a type error at the point of use rather than a silently
> still-valid lambda that now calls a different overload. **Suggestion.**

```kotlin
// bad
val ids: List<OrderId> = raw.map { value -> OrderId(value) }
val patterns: List<Regex> = sources.map { source -> Regex(source) }

// good
val ids: List<OrderId> = raw.map(::OrderId)
val patterns: List<Regex> = sources.map(::Regex)
```

## 9.12 Mark a function `inline` only when it takes a lambda parameter or needs a `reified` type parameter.

> Why? `inline` is not a general speed knob. The
> [inline functions reference](https://kotlinlang.org/docs/inline-functions.html)
> is blunt about the useless case: "If an inline function has no inlinable
> function parameters and no reified type parameters, the compiler will issue
> a warning, since inlining such functions is very unlikely to be beneficial."
> The two things inlining actually buys are real — the lambda is never
> allocated, and the caller gains non-local returns (§9.7) — and neither
> exists without a lambda parameter. Meanwhile the costs are unconditional:
> every call site grows, and the inlined body becomes part of your binary
> compatibility surface, so changing it requires recompiling every consumer.
> **Violation — the Kotlin compiler warns on the useless case.** Whether a
> particular `inline` earns its keep is otherwise a **Suggestion**.

```kotlin
// bad — no lambda parameter, no reified type parameter; the compiler warns
// and every call site grows for nothing
inline fun formatCents(cents: Long): String = "%.2f".format(cents / 100.0)

inline fun Order.isSettled(): Boolean = paidAt != null && shippedAt != null

// good — plain functions; the JIT already handles a small non-virtual call
fun formatCents(cents: Long): String = "%.2f".format(cents / 100.0)

fun Order.isSettled(): Boolean = paidAt != null && shippedAt != null

// good — inline earns its keep: the predicate is never allocated, and the
// caller may return non-locally from inside it
inline fun <T> List<T>.firstMatching(predicate: (T) -> Boolean): T? {
    for (element in this) {
        if (predicate(element)) return element
    }
    return null
}
```

## 9.13 Keep an inline function's body small; push the work into a non-inline function.

> Why? The
> [inline functions reference](https://kotlinlang.org/docs/inline-functions.html)
> qualifies the win: "Inlining may cause the generated code to grow. However,
> if you do it in a reasonable way (avoiding inlining large functions), it
> will pay off in performance." A sixty-line inline body multiplied by forty
> call sites is forty copies in the bytecode, which pushes methods past the
> JIT's inlining thresholds and slows down exactly the code it was supposed to
> speed up. Keep the inline function as a shim that carries the lambda or the
> reified type, and let a normal function do the work. If the shim is `public`
> and the worker is `internal`, the worker needs `@PublishedApi` — an inline
> public function may not reference non-public declarations. **Suggestion.**

```kotlin
// bad — sixty lines copied into every call site so that `T` can be reified
inline fun <reified T> ObjectMapper.readOrDefault(json: String, default: T): T {
    // sixty lines of parsing, validation, metrics, and error mapping
}

// good — the inline function is a one-line shim; the work compiles once
inline fun <reified T> ObjectMapper.readOrDefault(json: String, default: T): T =
    readOrDefault(json, T::class.java, default)

@PublishedApi
internal fun <T> ObjectMapper.readOrDefault(
    json: String,
    type: Class<T>,
    default: T,
): T {
    // sixty lines, compiled once
}
```

## 9.14 Use `noinline` on a lambda parameter the function stores, returns, or hands to a non-inline function.

> Why? An inlined lambda has no object to pass around — it has been spliced
> into the caller — so the compiler forbids treating it as a value. The
> [inline functions reference](https://kotlinlang.org/docs/inline-functions.html#noinline)
> states the two regimes: "inlinable lambdas can only be called inside inline
> functions or passed as inlinable arguments. `noinline` lambdas, however, can
> be manipulated in any way you like, including being stored in fields or
> passed around." Without `noinline` the code simply does not compile. The
> corollary matters as much as the rule: if *every* lambda parameter needs
> `noinline` and there is no reified type parameter, the function should not
> be `inline` at all (§9.12). **Suggestion** — the compiler enforces the
> mechanics; deciding to drop `inline` entirely is yours.

```kotlin
// bad — does not compile: an inlinable lambda cannot be stored in a field
inline fun <reified T> registerCodec(decode: (String) -> T) {
    codecs[T::class.java] = decode // error: illegal usage of inline-parameter
}

// good — noinline lets the lambda escape; the reified T still justifies inline
inline fun <reified T> registerCodec(noinline decode: (String) -> T) {
    codecs[T::class.java] = decode
}

// good — no reified parameter and the only lambda escapes, so drop `inline`
fun registerCodec(type: Class<*>, decode: (String) -> Any) {
    codecs[type] = decode
}
```

## 9.15 Use `crossinline` on a lambda the function invokes from another execution context.

> Why? Non-local return (§9.7) works by unwinding the caller's frame. If the
> inlined lambda is invoked from inside a nested object or a nested function
> — a `Runnable`, a listener, a callback the executor runs later — that frame
> may be long gone, so the compiler refuses to inline it. The
> [inline functions reference](https://kotlinlang.org/docs/inline-functions.html#non-local-jump-expressions)
> gives the fix: "to indicate that the lambda parameter of the inline function
> cannot use non-local returns, mark the lambda parameter with the
> `crossinline` modifier." The error you get without it —
> "can't inline 'block' here: it may contain non-local returns" — is the
> compiler protecting you from a jump into a dead stack frame, not a
> formality. **Suggestion** — the compiler enforces it.

```kotlin
// bad — does not compile: `block` is invoked from inside a lambda handed to
// a non-inline API, so a non-local return from it would have nowhere to go
inline fun onBackground(executor: Executor, block: () -> Unit) {
    executor.execute { block() }
}

// good — crossinline forbids non-local returns in `block`, which makes the
// indirect invocation legal
inline fun onBackground(executor: Executor, crossinline block: () -> Unit) {
    executor.execute { block() }
}

onBackground(executor) {
    // `return` here is a compile error, which is the point: the enclosing
    // function has already returned by the time this runs
    reindex()
}
```

## 9.16 Use a `reified` type parameter to remove the `Class<T>` token and the unchecked cast.

> Why? On the JVM a normal generic function cannot see its own type argument,
> which is why so many Java APIs take a `Class<T>` alongside the value and
> then cast. The
> [inline functions reference](https://kotlinlang.org/docs/inline-functions.html#reified-type-parameters)
> removes both: inside an `inline fun <reified T>`, `T` is a real type at
> runtime, so `is T`, `as? T`, and `T::class.java` all work. This is the one
> case where `inline` is justified with no lambda parameter at all. Remember
> the constraint: "normal functions (not marked as `inline`) cannot have
> reified parameters," so a reified type parameter forces the function to be
> inline — apply §9.13 and keep the body to a shim. **Suggestion.**

```kotlin
// bad — the caller repeats the type, and the cast is unchecked
fun <T> Any?.asOrNull(type: Class<T>): T? =
    if (type.isInstance(this)) type.cast(this) else null

val order = payload.asOrNull(Order::class.java)

// good — the type argument is available at runtime; `as?` is checked
inline fun <reified T> Any?.asOrNull(): T? = this as? T

val order = payload.asOrNull<Order>()

// good — the pattern that makes deserialization APIs readable
inline fun <reified T> ObjectMapper.readValue(json: String): T =
    readValue(json, T::class.java)
```

## 9.17 Do not assume a lambda is free, and do not add `inline` to chase the cost.

> Why? Be honest about the machine. Since
> [Kotlin 2.0](https://kotlinlang.org/docs/whatsnew20.html#generation-of-lambda-functions-using-invokedynamic),
> a lambda passed to a *non-inline* function is generated with
> `invokedynamic` rather than as an anonymous class — smaller binaries, and
> the JVM's own `LambdaMetafactory` decides how to represent it. It is still a
> function-type instance: one that captures nothing can be shared by the
> runtime, while one that captures a variable has to be materialised per
> capture. A lambda passed to an `inline` function has no instance at all,
> which is precisely why `map`, `filter`, `forEach`, `let`, and `run` are all
> inline in the standard library. The wrong conclusion is to sprinkle `inline`
> across your own code (§9.12); the right one is to notice capture inside hot
> loops and hoist what does not vary. **Suggestion** — measure before acting;
> nothing here is checkable.

```kotlin
// bad — the comparator captures nothing but is rebuilt as an expression on
// every call, and `inline` was added by reflex to try to fix it
inline fun sortByTotal(orders: List<Order>): List<Order> =
    orders.sortedWith(Comparator { a, b -> a.total.compareTo(b.total) })

// bad — a capturing lambda created inside the loop, once per element
fun dispatch(events: List<Event>, executor: Executor) {
    events.forEach { event ->
        executor.execute { handler.handle(event) } // captures `event`
    }
}

// good — hoist the invariant function object out of the call
private val BY_TOTAL: Comparator<Order> = compareBy { it.total }

fun sortByTotal(orders: List<Order>): List<Order> = orders.sortedWith(BY_TOTAL)

// good — one submission carrying the whole batch, one capture
fun dispatch(events: List<Event>, executor: Executor) {
    executor.execute { events.forEach(handler::handle) }
}
```

## 9.18 Declare a `fun interface` when you own a single-method abstraction that deserves a name; rely on plain SAM conversion for Java interfaces.

> Why? Kotlin converts a lambda to a *Java* single-abstract-method interface
> automatically — `executor.execute { ... }` and `Runnable { ... }` both work
> with no ceremony. It does **not** do that for a Kotlin interface unless the
> interface is declared `fun`. The
> [functional interfaces reference](https://kotlinlang.org/docs/fun-interfaces.html)
> defines the constraint: a functional interface "can have several
> non-abstract member functions but only one abstract member function." Adding
> the `fun` modifier costs nothing and turns every implementation site from a
> four-line `object` expression into a lambda. Forgetting it is the reason
> callback-heavy Kotlin APIs sometimes read worse than the Java ones they
> replaced. **Suggestion.**

```kotlin
// bad — one abstract method, but no `fun` modifier, so every implementation
// has to be spelled out as an object expression
interface RetryPolicy {
    fun shouldRetry(attempt: Int, error: Throwable): Boolean
}

val policy = object : RetryPolicy {
    override fun shouldRetry(attempt: Int, error: Throwable): Boolean = attempt < 3
}

// good — `fun interface` enables SAM conversion at every call site
fun interface RetryPolicy {
    fun shouldRetry(attempt: Int, error: Throwable): Boolean
}

val policy = RetryPolicy { attempt, _ -> attempt < 3 }

// good — Java SAM interfaces need nothing; conversion is automatic
executor.execute { reindex() }
val task = Runnable { reindex() }
```

## 9.19 Prefer a plain function type or type alias when the API only needs "any function of this shape".

> Why? The
> [functional interfaces reference](https://kotlinlang.org/docs/fun-interfaces.html#functional-interfaces-vs-type-aliases)
> gives the decision rule directly: "if your API needs to accept a function
> (any function) with some specific parameter and return types — use a simple
> functional type or define a type alias to give a shorter name to the
> corresponding functional type," whereas "if your API accepts a more complex
> entity than a function — for example, it has non-trivial contracts and/or
> operations on it that can't be expressed in a functional type's signature —
> declare a separate functional interface for it." A `fun interface` creates a
> new
> nominal type, so callers must construct it and cannot pass an ordinary
> function value or a callable reference without a conversion. That nominal
> identity is worth having when the contract needs a name, extra non-abstract
> members, or its own extensions — and is pure friction when it does not. See
> [Chapter 7](07-types-and-type-aliases.md) for the type-alias rules.
> **Suggestion.**

```kotlin
// bad — a nominal type that adds nothing over the function type it wraps
fun interface StringMapper {
    fun map(value: String): String
}

fun transform(values: List<String>, mapper: StringMapper): List<String> =
    values.map { mapper.map(it) }

transform(values, StringMapper(String::trim))

// good — the API just needs a function of that shape
typealias StringMapper = (String) -> String

fun transform(values: List<String>, mapper: StringMapper): List<String> =
    values.map(mapper)

transform(values, String::trim)

// good — a fun interface when the contract genuinely needs a name and members
fun interface BackoffStrategy {
    fun delayFor(attempt: Int): Duration

    fun capped(max: Duration): BackoffStrategy =
        BackoffStrategy { attempt -> minOf(delayFor(attempt), max) }
}
```

## 9.20 Declare a higher-order function's lambda parameter last, and give it a receiver when the lambda is a builder body.

> Why? Two design consequences that outlive every call site. The lambda must
> be last for trailing-lambda syntax to be available at all (§9.3 is the
> call-site form, and §8.6 states the general parameter-ordering rule this
> specialises) — put it in the middle and no caller can ever use the DSL form.
> And when the lambda's job is to configure something, a
> [function literal with receiver](https://kotlinlang.org/docs/lambdas.html#function-literals-with-receiver)
> (`Builder.() -> Unit`) removes the parameter name from every line of the
> body: "inside the body of the function literal, the receiver object passed
> to a call becomes an implicit `this`, so that you can access the members of
> that receiver object without any additional qualifiers." That is exactly the
> mechanism behind `buildList`, `apply`, and every Kotlin DSL. Use a plain
> `(T) -> Unit` when the lambda *consumes* a value and a receiver lambda when
> it *builds* one. **Suggestion.**

```kotlin
// bad — the lambda is not last, so no call site can use trailing-lambda
// syntax, and the builder is named on every line of the body
fun buildRequest(configure: (RequestBuilder) -> Unit, method: HttpMethod): Request {
    val builder = RequestBuilder(method)
    configure(builder)
    return builder.build()
}

buildRequest({ builder ->
    builder.header("Accept", "application/json")
    builder.timeout(Duration.ofSeconds(5))
}, HttpMethod.GET)

// good — lambda last, receiver lambda, and the call site reads as a DSL
fun buildRequest(method: HttpMethod, configure: RequestBuilder.() -> Unit): Request {
    val builder = RequestBuilder(method)
    builder.configure()
    return builder.build()
}

buildRequest(HttpMethod.GET) {
    header("Accept", "application/json")
    timeout(Duration.ofSeconds(5))
}

// good — a plain function type when the lambda consumes rather than builds
fun onEachFailure(results: List<Result<Order>>, action: (Throwable) -> Unit) {
    results.forEach { result -> result.exceptionOrNull()?.let(action) }
}
```
