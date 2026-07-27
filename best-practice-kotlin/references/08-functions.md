<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 8. Functions

A Kotlin function declaration carries far more design decisions than a Java
method does. The body may be an expression or a block. The return type may be
written or inferred. Parameters may carry defaults, which removes the need for
overloads but changes what Java callers see. The function may hang off a
receiver it does not own. Each of those choices is cheap to make and expensive
to reverse once callers exist, so this chapter is about the *signature and the
body shape* — the part of a function that is API.

The upstream rules come from the Kotlin coding conventions'
[Functions](https://kotlinlang.org/docs/coding-conventions.html#functions)
cluster —
[expression bodies](https://kotlinlang.org/docs/coding-conventions.html#expression-bodies),
[unit return type](https://kotlinlang.org/docs/coding-conventions.html#unit-return-type),
[default parameter values](https://kotlinlang.org/docs/coding-conventions.html#default-parameter-values),
[named arguments](https://kotlinlang.org/docs/coding-conventions.html#named-arguments),
[extension functions](https://kotlinlang.org/docs/coding-conventions.html#extension-functions),
[infix functions](https://kotlinlang.org/docs/coding-conventions.html#infix-functions),
and [functions vs properties](https://kotlinlang.org/docs/coding-conventions.html#functions-vs-properties)
— together with the Android Kotlin style guide's
[expression functions](https://developer.android.com/kotlin/style-guide#expression_functions)
and [implicit return/property types](https://developer.android.com/kotlin/style-guide#implicit_returnproperty_types)
sections, and the language reference for
[functions](https://kotlinlang.org/docs/functions.html) and
[extensions](https://kotlinlang.org/docs/extensions.html).

Four neighbouring topics are deferred. **Function naming** — camelCase, verb
phrases, the test-name underscore exception — is
[Chapter 3](03-naming.md). **Everything about the lambdas a function takes or
returns**, including `inline`, `noinline`, `crossinline`, `reified`, trailing
lambda syntax, and returns inside a lambda, is
[Chapter 9](09-lambdas-and-higher-order-functions.md); §8.6 states only the
parameter-ordering rule that chapter builds on. **`operator` functions** —
`plus`, `invoke`, `get`, `compareTo`, and the conventions that make them
resolve — are [Chapter 26](26-operators-and-conventions.md). **Factory
functions and companion-object construction** are
[Chapter 14](14-objects-and-companions.md). `suspend` functions are
[Chapter 33](33-coroutine-fundamentals.md) onward, and context parameters are
[Chapter 29](29-context-parameters.md).

**Tool alignment:** several rules below are mechanically enforced. ktlint's
`standard:function-expression-body` (stable since ktlint 1.3, active in every
code style) and `standard:no-unit-return` fire in the format step; detekt's
`ExpressionBodySyntax`, `OptionalUnit`, `LongMethod`, `LongParameterList`,
`NamedArguments`, and `SpreadOperator` fire in the analysis step; the Kotlin
compiler's explicit API mode (`explicitApi()` / `-Xexplicit-api=strict`)
enforces the public-return-type rule outright. Rules a named check actually
covers are marked **Violation**; the rest are **Suggestion**, even where a
nearby check catches an adjacent symptom.

## 8.1 Use an expression body when the entire function body is a single expression.

> Why? The Kotlin coding conventions'
> [expression bodies](https://kotlinlang.org/docs/coding-conventions.html#expression-bodies)
> section is unambiguous: "Prefer using an expression body for functions with
> the body consisting of a single expression." The Android guide agrees —
> "when a function contains only a single expression it can be represented as
> an expression function." A block body around a lone `return` adds two lines
> of syntax and one level of indentation while communicating nothing, and it
> hides the fact that the function is total and side-effect-free.
> **Violation — enforced by `ktlint standard:function-expression-body`**
> (stable since ktlint 1.3, and active in every code style) **and
> `detekt/ExpressionBodySyntax`** (off by default; enable it if you want the
> analysis step to catch it too).

```kotlin
// bad — a block body wrapped around a single return
fun displayName(user: User): String {
    return user.nickname ?: user.email
}

override fun toString(): String {
    return "Order(${id.value})"
}

// good
fun displayName(user: User): String = user.nickname ?: user.email

override fun toString(): String = "Order(${id.value})"
```

## 8.2 Do not give an expression body to a function that exists for its side effect.

> Why? An expression body publishes whatever the expression evaluates to as
> the function's return type. `fun save(order: Order) = repository.insert(order)`
> silently returns whatever `insert` returns — today an `Int` row count,
> tomorrow a generated `OrderId` — and every change to the collaborator
> silently changes this function's public signature. A block body pins the
> return type at `Unit` and states plainly that the caller is meant to ignore
> the value. This is the one place where the expression-body preference in
> §8.1 does not apply. **Suggestion.**

```kotlin
// bad — the return type is whatever `insert` happens to return, and it
// changes under you when the repository changes
fun save(order: Order) = repository.insert(order)

fun evict(key: CacheKey) = cache.remove(key)

// good — a side-effecting function has a block body and returns Unit
fun save(order: Order) {
    repository.insert(order)
}

fun evict(key: CacheKey) {
    cache.remove(key)
}
```

## 8.3 Declare an explicit return type on every function that is part of a public or `internal` API, expression body or not.

> Why? The Kotlin coding conventions'
> [library guidance](https://kotlinlang.org/docs/coding-conventions.html#coding-conventions-for-libraries)
> requires you to "always explicitly specify function return types and
> property types (to avoid accidentally changing the return type when the
> implementation changes)," and the Android guide echoes it: "when writing a
> library, retain the explicit type declaration when it is part of the public
> API." Inference is a convenience for the author and a hazard for the
> consumer — swapping a `mutableListOf` for a `buildList` inside an
> expression-bodied function changes the declared type of the function without
> anyone editing its signature. Note also that a recursive or
> mutually-recursive function *must* declare its return type; the compiler
> cannot infer it.
> **Violation — enforced by the compiler in explicit API mode
> (`explicitApi()` in the Gradle Kotlin DSL, or `-Xexplicit-api=strict`),
> which also excuses overrides, primary constructors, and property
> accessors.** Private and local functions may rely on inference freely.

```kotlin
// bad — the public return type is whatever the body infers today
fun activeRoles(user: User) = user.roles.filter { it.isActive }

fun parseAll(lines: List<String>) = lines.map(::parse)

// bad — does not compile: a recursive function cannot infer its return type
fun factorial(n: Int) = if (n <= 1) 1L else n * factorial(n - 1)

// good
fun activeRoles(user: User): List<Role> = user.roles.filter { it.isActive }

fun parseAll(lines: List<String>): List<Record> = lines.map(::parse)

fun factorial(n: Int): Long = if (n <= 1) 1L else n * factorial(n - 1)

// good — inference is fine for a private helper
private fun normalize(value: String) = value.trim().lowercase()
```

## 8.4 Omit `Unit` as a return type.

> Why? The Kotlin coding conventions'
> [unit return type](https://kotlinlang.org/docs/coding-conventions.html#unit-return-type)
> section says it in one line: "If a function returns `Unit`, the return type
> should be omitted." The language reference adds the reason it is safe —
> "if a function has a block body and does not return a useful value, the
> compiler assumes its return type is `Unit`" — so writing it out is pure
> noise. The one exception the reference names is a *functional type
> parameter*, where `() -> Unit` must be spelled in full.
> **Violation — enforced by `ktlint standard:no-unit-return`**, which is on by
> default. `detekt/OptionalUnit` covers the same ground plus the lone `Unit`
> statement, but ships `active: false`; enable it if you want the analysis step
> to catch it too.

```kotlin
// bad
fun publish(event: DomainEvent): Unit {
    bus.send(event)
}

fun reset(): Unit = Unit

// good
fun publish(event: DomainEvent) {
    bus.send(event)
}

// good — Unit is required here; it is part of a function type, not a
// declared return type
fun onComplete(callback: () -> Unit) {
    callbacks += callback
}
```

## 8.5 Prefer default parameter values to overloads.

> Why? The Kotlin coding conventions'
> [default parameter values](https://kotlinlang.org/docs/coding-conventions.html#default-parameter-values)
> section is explicit: "Prefer declaring functions with default parameter
> values to declaring overloaded functions." An overload chain forces a reader
> to diff several signatures to discover what the defaults actually are, and
> every new option doubles the chain. A single declaration puts the default
> next to the parameter it belongs to, where the KDoc can describe it once.
> Two caveats: the conventions still say to
> [put any overloads you do keep next to each other](https://kotlinlang.org/docs/coding-conventions.html#overload-layout),
> and when you *override* a method that has default parameter values, the
> language reference requires you to "omit the default parameter values from
> the signature" — the base declaration's defaults still apply.
> **Suggestion** — no check can tell an overload chain from a legitimate set
> of overloads. `detekt/MethodOverloading` flags a class carrying more than a
> configured number of overloads, but it ships `active: false`.

```kotlin
// bad — three declarations the reader must diff to find the defaults
fun format(amount: BigDecimal): String = format(amount, Locale.US)

fun format(amount: BigDecimal, locale: Locale): String = format(amount, locale, true)

fun format(amount: BigDecimal, locale: Locale, showSymbol: Boolean): String {
    // ...
}

// good — one declaration, defaults where the reader looks for them
fun format(
    amount: BigDecimal,
    locale: Locale = Locale.US,
    showSymbol: Boolean = true,
): String {
    // ...
}
```

## 8.6 Order parameters so required ones come first, defaulted ones follow, and any function type is last.

> Why? Two mechanical consequences, both stated in the language reference on
> [functions](https://kotlinlang.org/docs/functions.html). First, "when you
> declare a parameter with a default value before a parameter without a
> default value, you can only use the default value by naming the argument" —
> a default placed before a required parameter is unreachable positionally, so
> it is not really a default at all. Second, a lambda can only be lifted out
> of the parentheses when it is the *last* argument, so burying a function
> type in the middle of the list makes trailing-lambda syntax impossible at
> every call site forever. Ordering is API, and reordering later is a source
> break. See [Chapter 9, §9.20](09-lambdas-and-higher-order-functions.md) for
> the higher-order-function elaboration of the lambda-last half, and §9.3 there
> for the call-site syntax it unlocks. **Suggestion.**

```kotlin
// bad — the defaulted parameter sits before a required one, so no caller can
// ever reach the default without naming the argument after it
fun sendReceipt(locale: Locale = Locale.US, orderId: OrderId) {
    // ...
}

sendReceipt(orderId)           // does not compile
sendReceipt(orderId = orderId) // the only way to get the default

// bad — the callback is not last, so no call site can use a trailing lambda
fun retry(onFailure: (Throwable) -> Unit, attempts: Int) {
    // ...
}

// good — required first, defaulted next, function type last
fun sendReceipt(
    orderId: OrderId,
    locale: Locale = Locale.US,
    onSent: (Receipt) -> Unit = {},
) {
    // ...
}

sendReceipt(orderId) { receipt -> logger.info("sent {}", receipt.id) }
```

## 8.7 Annotate a defaulted function with `@JvmOverloads` when Java code has to call it.

> Why? Default arguments are a Kotlin-compiler feature, not a JVM one. As the
> [Java interop reference](https://kotlinlang.org/docs/java-to-kotlin-interop.html#overloads-generation)
> puts it, "normally, if you write a Kotlin function with default parameter
> values, it's visible in Java only as a full signature, with all parameters
> present." Java callers therefore have to pass every argument explicitly,
> defeating the entire point of §8.5. `@JvmOverloads` generates one additional
> overload per defaulted parameter, each dropping that parameter and every
> parameter to the right of it. The annotation "also works for constructors,
> static methods, and so on. It can't be used on abstract methods, including
> methods defined in interfaces" — plan the interop shape accordingly. Do
> **not** add it
> reflexively to a Kotlin-only module: it emits synthetic methods that widen
> the binary API for no benefit. See
> [Chapter 28](28-java-interop.md) for the rest of the interop annotations.
> **Suggestion.**

```kotlin
// bad — a Java caller must supply every argument
class Notifier {
    fun notify(message: String, priority: Int = 0, retry: Boolean = false) {
        // ...
    }
}
// Java: notifier.notify("deploy finished", 0, false);

// good
class Notifier {
    @JvmOverloads
    fun notify(message: String, priority: Int = 0, retry: Boolean = false) {
        // ...
    }
}
// Java: notifier.notify("deploy finished");
```

## 8.8 Use named arguments for every `Boolean` literal and for adjacent arguments of the same type.

> Why? The Kotlin coding conventions'
> [named arguments](https://kotlinlang.org/docs/coding-conventions.html#named-arguments)
> section draws the line here: "use the named argument syntax when a method
> takes multiple parameters of the same primitive type, or for parameters of
> `Boolean` type, unless the meaning of all parameters is absolutely clear
> from context." A bare `true` at a call site is unreadable without opening
> the declaration, and two adjacent `Int` parameters can be swapped by a
> refactor with no compile error and no test failure until production. Note
> the language reference's ordering constraint: "after the first skipped
> argument, you must name all subsequent arguments."
> **Suggestion.** `detekt/NamedArguments` applies a weaker count-based form of
> this — named arguments once a call exceeds a configured argument count — but
> it ships `active: false`, and no check can see that two adjacent `Int`
> arguments mean different things.

```kotlin
// bad — four positional Ints and a bare Boolean; swapping width and height
// compiles cleanly and ships
drawSquare(10, 10, 100, 100, true)

createUser("ada@example.com", "Ada", true, false)

// good
drawSquare(x = 10, y = 10, width = 100, height = 100, fill = true)

createUser(
    email = "ada@example.com",
    displayName = "Ada",
    isActive = true,
    requiresPasswordReset = false,
)
```

## 8.9 Prefer an extension function when the operation is primarily *about* one object, and restrict its visibility.

> Why? The Kotlin coding conventions'
> [extension functions](https://kotlinlang.org/docs/coding-conventions.html#extension-functions)
> section says to "use extension functions liberally. Every time you have a
> function that works primarily on an object, consider making it an extension
> function accepting that object as a receiver." An extension puts the verb
> where a reader looks for it — after the noun — and chains cleanly, which a
> `Utils` object never does. The same section supplies the constraint that
> makes this safe: "to minimize API pollution, restrict the visibility of
> extension functions as much as it makes sense. As necessary, use local
> extension functions, member extension functions, or top-level extension
> functions with private visibility." A `public` top-level extension on a
> widely used type is imported by autocomplete everywhere and is very hard to
> withdraw. **Suggestion.**

```kotlin
// bad — a utility holder for a function that is entirely about Order, and a
// call site that reads inside-out
object OrderUtils {
    fun totalMinorUnits(order: Order): Long =
        order.lines.sumOf { it.quantity * it.unitPriceMinorUnits }
}

val total = OrderUtils.totalMinorUnits(order)

// bad — correct shape, but public: now every module sees it
fun Order.totalMinorUnits(): Long =
    lines.sumOf { it.quantity * it.unitPriceMinorUnits }

// good — extension, scoped to the module that owns the billing rules
internal fun Order.totalMinorUnits(): Long =
    lines.sumOf { it.quantity * it.unitPriceMinorUnits }

val total = order.totalMinorUnits()
```

## 8.10 Never expect an extension function to dispatch polymorphically or to override a member.

> Why? Extensions look like members and behave like static helpers. The
> [extensions reference](https://kotlinlang.org/docs/extensions.html) states
> both halves: "extension functions are dispatched statically, meaning the
> compiler determines which function to call based on the receiver type at
> compile time," and "if a class has a member function and there's an
> extension function with the same receiver type, the same name, and
> compatible arguments, the member function takes precedence." So an extension
> on a supertype wins over an extension on the subtype whenever the *static*
> type is the supertype, and any member with the same signature silently
> shadows your extension entirely — including a member added later by the
> class's owner. If you need dynamic dispatch, you need a member. **Suggestion.**

```kotlin
// bad — reads as an override, resolves as a static call on the declared type
open class Shape
class Rectangle : Shape()

fun Shape.describe(): String = "shape"
fun Rectangle.describe(): String = "rectangle"

fun render(shape: Shape): String = shape.describe()

render(Rectangle()) // "shape" — the static type of the parameter decides

// bad — the member always wins; this extension is dead code the day the
// class's owner adds `describe()`
class Payment {
    fun describe(): String = "payment"
}

fun Payment.describe(): String = "custom description" // never called

// good — a member function, which does dispatch dynamically
open class Shape {
    open fun describe(): String = "shape"
}

class Rectangle : Shape() {
    override fun describe(): String = "rectangle"
}

render(Rectangle()) // "rectangle"
```

## 8.11 Declare an extension property only for a value derived on each access; it can never hold state.

> Why? The
> [extensions reference](https://kotlinlang.org/docs/extensions.html#extension-properties)
> explains the constraint precisely: "since extensions don't actually add
> members to classes, there's no efficient way for an extension property to
> have a backing field. That's why initializers are not allowed for extension
> properties. You can define their behavior only by explicitly providing
> getters and setters." An initializer is a compile error, and the usual
> workaround — a module-level `Map` keyed by the receiver — leaks memory,
> is not thread-safe, and ties the value's lifetime to the map rather than to
> the object. If a type needs state, that state belongs on the type. See
> [Chapter 17](17-properties-and-backing-fields.md) for the general property
> rules. **Suggestion.**

```kotlin
// bad — does not compile: extension properties cannot have initializers
val Order.isPaid: Boolean = paidAt != null

// bad — compiles, and leaks every Order that ever passes through
private val shippedAt = mutableMapOf<Order, Instant>()

var Order.shipped: Instant?
    get() = shippedAt[this]
    set(value) {
        if (value != null) shippedAt[this] = value
    }

// good — a getter that derives the value from what the receiver already has
val Order.isPaid: Boolean
    get() = paidAt != null

val Order.lineCount: Int
    get() = lines.size
```

## 8.12 Give an extension a nullable receiver only when `null` is a meaningful input.

> Why? The
> [extensions reference](https://kotlinlang.org/docs/extensions.html#nullable-receivers)
> notes that "you can define extension functions with a nullable receiver
> type, which allows you to call them on a variable even if its value is
> `null`. When the receiver is `null`, `this` is also `null`." That is exactly
> right for predicates where absence has a natural answer — this is why the
> standard library ships `CharSequence?.isNullOrBlank()` and
> `Collection<*>?.isNullOrEmpty()`. It is exactly wrong for a transformation,
> where a nullable receiver just moves the null check inside the function and
> hides it from the caller and from the reader. See
> [Chapter 6](06-null-safety.md) for the null-handling rules this specialises.
> **Suggestion.**

```kotlin
// bad — every call site pays for a safe call plus an elvis to answer a
// question that has an obvious answer when the discount is absent
fun Discount.isActive(now: Instant): Boolean = now < expiresAt

val active = discount?.isActive(now) ?: false

// bad — a nullable receiver on a transformation hides the null case from the
// signature; the caller cannot tell that "" means "there was no discount"
fun Discount?.describe(): String = this?.code ?: ""

// good — null is a meaningful input to the question being asked
fun Discount?.isActive(now: Instant): Boolean = this != null && now < expiresAt

val active = discount.isActive(now)

// good — a transformation keeps its non-null receiver; the caller decides
fun Discount.describe(): String = code

val label = discount?.describe() ?: "no discount"
```

## 8.13 Declare a function `infix` only when it joins two objects of similar role, and never when it mutates the receiver.

> Why? The Kotlin coding conventions'
> [infix functions](https://kotlinlang.org/docs/coding-conventions.html#infix-functions)
> section gives both halves of the test: "Declare a function as `infix` only
> when it works on two objects which play a similar role. Good examples:
> `and`, `to`, `zip`. Bad example: `add`," and "do not declare a method as
> `infix` if it mutates the receiver object." Infix notation drops the dot,
> which is what makes `a to b` and `x and y` read like operators — and which
> is also what makes `cart put item` read like a symmetric expression when it
> is really a mutation. Infix also binds more loosely than arithmetic and more
> tightly than boolean operators, so mixed expressions need parentheses that
> readers will not expect. **Suggestion.**

```kotlin
// bad — asymmetric roles, and the receiver is mutated
infix fun ShoppingCart.put(item: Item) {
    items += item
}

cart put item // reads like an expression, is a mutation

// bad — one operand is a container and the other is a key; not similar roles
infix fun Config.valueFor(key: String): String? = entries[key]

// good — two operands of the same kind, no mutation
infix fun <T> Set<T>.overlaps(other: Set<T>): Boolean = any(other::contains)

if (requiredRoles overlaps grantedRoles) {
    grantAccess()
}
```

## 8.14 Prefer a collection parameter to `vararg`, and never spread an array you did not just build.

> Why? `vararg` looks free at the declaration and costs at every call site
> that already holds a collection: the caller has to write
> `*names.toTypedArray()`, which allocates an array, and then the spread
> allocates again. detekt's `SpreadOperator` rule states the cost plainly —
> "in most cases using a spread operator causes a full copy of the array to be
> created before calling a method." The language reference also notes the
> hard limit that "only one parameter can be marked as `vararg`," so a second
> variable-arity concept can never be added to the same signature. Reserve
> `vararg` for call sites that are genuinely literal and short.
> **Violation — enforced by `detekt/SpreadOperator`** for the spread half;
> the parameter-shape choice is a **Suggestion**.

```kotlin
// bad — every caller holding a List pays for two array copies
fun tag(vararg names: String) {
    // ...
}

val names: List<String> = loadTagNames()
tag(*names.toTypedArray())

// good — take the type the callers already have
fun tag(names: Collection<String>) {
    // ...
}

tag(names)

// good — vararg earns its place when call sites are literal
fun requireAllPresent(vararg values: Any?) {
    require(values.none { it == null }) { "all values must be present" }
}

requireAllPresent(id, name, email)
```

## 8.15 Use a local function only for duplication that is private to one function, and promote it the moment a second caller appears.

> Why? A local function, per the
> [language reference](https://kotlinlang.org/docs/functions.html#local-functions),
> "can access local variables of outer functions (the closure)." That closure
> is the whole point and the whole hazard: the helper's real inputs are
> invisible in its parameter list, so a reader cannot tell what it depends on
> without reading the enclosing body, and it cannot be unit-tested. Once the
> same helper is copy-pasted into a sibling function, the copies drift. A
> `private` member (or file-level) function has an explicit signature, one
> definition, and a test. **Suggestion.**

```kotlin
// bad — the same helper redefined in two sibling functions, and each closes
// over a different `strict` so the two copies are not actually the same
fun parseHeader(line: String, strict: Boolean): Header {
    fun field(raw: String): String =
        if (strict) raw.trim('"') else raw.trim('"').trim()
    // ...
}

fun parseFooter(line: String, strict: Boolean): Footer {
    fun field(raw: String): String = raw.trim('"').trim()
    // ...
}

// good — one definition, an explicit signature, and a testable unit
private fun field(raw: String, strict: Boolean): String =
    if (strict) raw.trim('"') else raw.trim('"').trim()

fun parseHeader(line: String, strict: Boolean): Header {
    // ... uses field(raw, strict)
}

fun parseFooter(line: String, strict: Boolean): Footer {
    // ... uses field(raw, strict)
}
```

## 8.16 Treat a long function or a long parameter list as a design signal, not a formatting problem.

> Why? Length is the cheapest available proxy for "this function has more than
> one responsibility." A 90-line body cannot be held in a reader's head, so
> reviewers stop reviewing it and start skimming it; a nine-parameter
> signature cannot be called without named arguments and usually means a
> parameter object is missing. The fix is never to wrap the lines differently
> — ktlint has already done that — it is to name the steps. Extracting each
> step into a function with a real name turns the top-level function into a
> table of contents.
> **Violation — enforced by `detekt/LongMethod` and
> `detekt/LongParameterList`**, with `detekt/CyclomaticComplexMethod` and
> `detekt/NestedBlockDepth` covering the branching form of the same problem.

```kotlin
// bad — one function doing parse, validate, persist, and notify, with a
// parameter list that no call site can read
fun handle(
    payload: String,
    tenantId: TenantId,
    actorId: UserId,
    correlationId: String,
    dryRun: Boolean,
    skipValidation: Boolean,
    notify: Boolean,
    retryCount: Int,
) {
    // 90 lines
}

// good — a parameter object, and a body that names its four steps
data class HandleCommand(
    val payload: String,
    val tenantId: TenantId,
    val actorId: UserId,
    val correlationId: String,
    val options: HandleOptions = HandleOptions(),
)

fun handle(command: HandleCommand) {
    val request = parse(command.payload)
    validate(request, command.options)
    val order = persist(request, command.tenantId)
    notify(order, command.actorId)
}
```

## 8.17 Mark a self-recursive function `tailrec` only where the recursive call is genuinely the last operation.

> Why? `tailrec` is an optimisation request, not a guarantee. The
> [language reference](https://kotlinlang.org/docs/functions.html#tail-recursive-functions)
> lists the conditions: "you can apply the `tailrec` modifier to a function
> only when it calls itself as its final operation," and "you cannot use tail
> recursion when there is more code after the recursive call, within
> `try`/`catch`/`finally` blocks, or when the function is `open`." When a
> condition is not
> met the compiler emits a *warning* and quietly compiles ordinary recursion —
> so a `tailrec` you believe protects you from a deep input may still overflow
> the stack in production. The `try`/`catch` case is the one that catches
> people: adding error handling around a working `tailrec` function silently
> removes the optimisation. **Suggestion** — the compiler warns, but the
> warning is easy to miss unless the build treats warnings as errors.

```kotlin
// bad — the recursive call is not the last operation; the addition is. The
// compiler warns and generates plain recursion.
tailrec fun sum(values: List<Int>, index: Int = 0): Int =
    if (index == values.size) 0 else values[index] + sum(values, index + 1)

// bad — tailrec is silently ineffective inside a try block
tailrec fun drain(queue: Queue<Task>) {
    try {
        val task = queue.poll() ?: return
        task.run()
        drain(queue)
    } catch (e: TaskFailedException) {
        logger.warn("task failed", e)
    }
}

// good — an accumulator moves the recursive call into tail position
tailrec fun sum(values: List<Int>, index: Int = 0, acc: Int = 0): Int =
    if (index == values.size) acc else sum(values, index + 1, acc + values[index])

// good — the loop the optimisation would have produced, written directly, so
// nothing can silently un-optimise it
fun drain(queue: Queue<Task>) {
    while (true) {
        val task = queue.poll() ?: return
        runCatching { task.run() }
            .onFailure { logger.warn("task failed", it) }
    }
}
```

## 8.18 Prefer a read-only property to a zero-argument function when the computation is cheap, total, and stable.

> Why? The Kotlin coding conventions'
> [functions vs properties](https://kotlinlang.org/docs/coding-conventions.html#functions-vs-properties)
> section gives three conditions, and all three must hold. Prefer a property
> when the underlying algorithm "does not throw," "is cheap to calculate (or
> cached on the first run)," and "returns the same result over invocations if
> the object state hasn't changed." The signal matters because callers treat
> property access as free — they will read it inside a loop, inside a log
> statement, inside a `toString()`. A property that opens a socket or throws
> on a bad state violates every expectation that dot-access sets up. When any
> condition fails, use a function and name the work it does. **Suggestion.**

```kotlin
// bad — a function for a cheap, total, stable derivation
class Order(val lines: List<OrderLine>) {
    fun lineCount(): Int = lines.size
}

// bad — a property that performs I/O and can throw; callers will read it in
// a loop because it looks free
val Order.pdfBytes: ByteArray
    get() = pdfRenderer.render(this)

// good
class Order(val lines: List<OrderLine>) {
    val lineCount: Int
        get() = lines.size
}

fun Order.renderPdf(): ByteArray = pdfRenderer.render(this)
```
