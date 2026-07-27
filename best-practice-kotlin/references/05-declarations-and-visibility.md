<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 5. Declarations & Visibility

A Kotlin declaration carries four decisions the reader will hold you to:
whether the binding can change, whether its type is written down, who can see
it, and where it lives. Kotlin's defaults get two of those right — `val` is
one keystroke shorter than `var`, and inference means you usually do not write
the type — and one of them exactly backwards: **every declaration you do not
annotate is `public`**. This chapter is about making all four deliberate.

The rules draw on the
[Kotlin coding conventions on immutability](https://kotlinlang.org/docs/coding-conventions.html#immutability),
[modifiers order](https://kotlinlang.org/docs/coding-conventions.html#modifiers-order),
[destructuring declarations](https://kotlinlang.org/docs/coding-conventions.html#destructuring-declarations),
and [coding conventions for libraries](https://kotlinlang.org/docs/coding-conventions.html#coding-conventions-for-libraries),
together with the Android Kotlin style guide's
[implicit return/property types](https://developer.android.com/kotlin/style-guide#implicit_returnproperty_types),
[top-level declarations](https://developer.android.com/kotlin/style-guide#top-level_declarations),
and [constant names](https://developer.android.com/kotlin/style-guide#constant_names)
sections. The language reference for
[visibility modifiers](https://kotlinlang.org/docs/visibility-modifiers.html)
and [properties](https://kotlinlang.org/docs/properties.html) supplies the
mechanics.

Three neighbouring topics are deferred. The full treatment of nullability —
`!!`, safe calls, platform types, and the deep case against a nullable `var`
— is [Chapter 6, Null Safety](06-null-safety.md); §5.16 states only the
three-way choice between `lateinit`, a nullable `var`, and `by lazy`.
Custom getters, setters, and backing properties are
[Chapter 17, Properties & Backing Fields](17-properties-and-backing-fields.md).
Naming — `UPPER_SNAKE_CASE` for constants, `camelCase` for everything else,
the leading-underscore backing-property convention — is
[Chapter 3, Naming](03-naming.md).

**Tool alignment:** several rules below are mechanically enforced.
`detekt/VarCouldBeVal` and `detekt/RedundantVisibilityModifier` fire on §5.1
and §5.6; `ktlint`'s `standard:modifier-order` fires on §5.10;
`detekt/DestructuringDeclarationWithTooManyEntries` fires on §5.13; and the
compiler itself enforces §5.4 and §5.9 once explicit API mode is on. Rules a
named check actually enforces are marked **Violation**; the rest are
**Suggestion**.

## 5.1 Declare every local variable and every property `val`, and reach for `var` only when the binding is genuinely reassigned.

> Why? The [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#immutability)
> are unambiguous: "Prefer using immutable data to mutable. Always declare
> local variables and properties as `val` rather than `var` if they are not
> modified after initialization." A `val` tells the reader the value they are
> looking at now is the value it will always have, which removes a whole class
> of "where else is this written?" reading. A `var` property additionally
> destroys smart casting (see [§6.8](06-null-safety.md)) and makes the object
> unusable as a hash key.
> **Violation — enforced by `detekt/VarCouldBeVal`.**

```kotlin
// bad — `var` where nothing is ever reassigned; VarCouldBeVal flags both
class Invoice(lines: List<Line>) {
    private var total = lines.sumOf { it.amount }

    fun formatted(): String {
        var currency = "EUR"
        return "$currency $total"
    }
}

// good
class Invoice(lines: List<Line>) {
    private val total = lines.sumOf { it.amount }

    fun formatted(): String {
        val currency = "EUR"
        return "$currency $total"
    }
}
```

## 5.2 Initialize at the declaration; use `if` or `when` as an *expression* instead of assigning into a `var` from a branch.

> Why? A declaration split from its initialization forces the reader to scan
> forward for every assignment before they know what the value is, and it
> turns a `val` into a `var` for no reason. Kotlin's `if` and `when` are
> expressions, so the branch *is* the initializer. The
> [coding conventions on `if` versus `when`](https://kotlinlang.org/docs/coding-conventions.html#if-versus-when)
> assume this expression form throughout. As a bonus, an expression-form
> `when` over a sealed type or enum must be exhaustive, so a new case becomes
> a compile error rather than a silently skipped assignment.
> **Suggestion.**

```kotlin
// bad — `var`, four assignment sites, and a new Tier compiles silently with
// discount left at 0.0
fun discountFor(tier: Tier): Double {
    var discount = 0.0
    when (tier) {
        Tier.FREE -> discount = 0.0
        Tier.PRO -> discount = 0.10
        Tier.ENTERPRISE -> discount = 0.25
    }
    return discount
}

// good — one `val`, and adding a Tier fails to compile
fun discountFor(tier: Tier): Double {
    val discount = when (tier) {
        Tier.FREE -> 0.0
        Tier.PRO -> 0.10
        Tier.ENTERPRISE -> 0.25
    }
    return discount
}
```

## 5.3 Omit the declared type when the initializer makes it obvious.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#implicit_returnproperty_types)
> says it directly: "If an expression function body or a property initializer
> is a scalar value or the return type can be clearly inferred from the body
> then it can be omitted." A redundant type annotation is duplicated
> information that can drift out of step with the initializer during a
> refactor, and it pushes the interesting part of the line to the right.
> **Suggestion.**

```kotlin
// bad — the type restates what the right-hand side already says
private val icon: Icon = IconLoader.getIcon("/icons/kotlin.png")
private val retries: Int = 3
override fun toString(): String = "Hey"

// good
private val icon = IconLoader.getIcon("/icons/kotlin.png")
private val retries = 3
override fun toString() = "Hey"
```

## 5.4 Write the return type and the property type explicitly on everything that is part of a published API.

> Why? The Android style guide qualifies §5.3 with one sentence: "When
> writing a library, retain the explicit type declaration when it is part of
> the public API." An inferred public type is an accident waiting to happen —
> change the body of an expression function and you have silently changed the
> signature your consumers compile against, with no diff on the declaration
> line to review. This is precisely what
> [explicit API mode](https://kotlinlang.org/docs/whatsnew14.html#explicit-api-mode-for-library-authors)
> mechanizes (see §5.9): it "requires explicit type specifications for
> properties and functions exposed to the public API," so "API users are aware
> of the types of API members they use."
> **Violation under explicit API mode — enforced by the compiler with
> `-Xexplicit-api=strict`.**

```kotlin
// bad — the public signature is whatever the body happens to infer; swapping
// `toList()` for `toSet()` is a binary-incompatible change with no visible
// signature edit
fun activeRegions() = regions.filter { it.enabled }.map { it.code }.toList()

// good — the contract is stated, and the body can be rewritten freely
public fun activeRegions(): List<RegionCode> =
    regions.filter { it.enabled }.map { it.code }.toList()
```

## 5.5 Write the type explicitly whenever inference would produce something other than the type you mean — empty collections and untyped numeric literals especially.

> Why? Inference is only as good as the right-hand side. `emptyList()` with
> no expected type infers its element type from context and produces a
> confusing error when there is no context; an integer literal is always
> `Int`, so `val timeoutMillis = 30_000` is an `Int` even when every consumer
> wants a `Long`; and `mapOf()` with no arguments cannot be inferred at all.
> Writing the type at the declaration puts the constraint where the reader
> looks for it rather than at the first call that fails.
> Note that Kotlin 2.4's collection literals (`val xs: List<String> = ["a"]`)
> are **Experimental** and need `-Xcollection-literals`; when the type cannot
> be inferred they default to `List` — one more reason to state the type.
> **Suggestion.**

```kotlin
// bad — does not compile: nothing constrains the element type
val pendingIds = emptyList()

// bad — compiles, but `budget` is an Int and every arithmetic site now needs
// a .toLong()
val budgetMillis = 2_000

// good
val pendingIds: List<OrderId> = emptyList()
val budgetMillis: Long = 2_000
val budgetMillisAlt = 2_000L
```

## 5.6 Never write `public`; it is already the default.

> Why? The
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#modifiers-order)
> close the modifier-order list with "Unless you're working on a library, omit
> redundant modifiers (for example, `public`)." A redundant `public` sprinkled
> on some declarations and not others makes the ones without it look
> *less* visible than they are, which is exactly the wrong signal. The
> exception is a module running explicit API mode (§5.9), where the compiler
> requires the modifier and detekt exempts it.
> **Suggestion — `detekt/RedundantVisibilityModifier` covers this, but it is absent from detekt 1.23.8's default config (the docs site is ahead of the latest stable release). Enable it once your detekt version ships it; see chapter 47.**

```kotlin
// bad — `public` on some members implies the others are narrower. They aren't.
public class ReportService(private val repo: ReportRepository) {
    public fun latest(): Report = repo.latest()

    fun archive(id: ReportId) = repo.archive(id) // also public
}

// good
class ReportService(private val repo: ReportRepository) {
    fun latest(): Report = repo.latest()

    fun archive(id: ReportId) = repo.archive(id)
}
```

## 5.7 Because the default is `public`, mark every declaration that is not part of your API surface `internal` or `private` — deliberately, at the moment you write it.

> Why? This is the one Kotlin default that runs against what you almost
> always want. [The language reference](https://kotlinlang.org/docs/visibility-modifiers.html)
> states plainly: "The default visibility is `public`." Java's package-private
> default at least confined an unannotated declaration to its package; Kotlin's
> exports it to the world. Every helper, every intermediate data holder, and
> every constant you forget to annotate becomes part of the contract someone
> else can depend on — and once depended upon, it is expensive to remove.
> `internal` means visible everywhere in the same
> [module](https://kotlinlang.org/docs/visibility-modifiers.html#modules), a
> Gradle source set or Maven project.
> **Suggestion** — no linter can tell an intentionally public helper from a
> forgotten one.

```kotlin
// bad — three accidental exports: the DTO, the mapper, and the constant are
// all part of this module's public API
data class RawLedgerRow(val account: String, val cents: Long)

fun RawLedgerRow.toEntry(): LedgerEntry = LedgerEntry(account, Money(cents))

const val LEDGER_PAGE_SIZE = 500

// good — only the type the caller needs is visible
internal data class RawLedgerRow(val account: String, val cents: Long)

internal fun RawLedgerRow.toEntry(): LedgerEntry = LedgerEntry(account, Money(cents))

private const val LEDGER_PAGE_SIZE = 500
```

## 5.8 Use `private` at the top level for helpers that belong to one file, and understand that it means *file*-private, not package-private.

> Why? Kotlin has no package-private. "If you mark a declaration as
> `private`, it will only be visible inside the file that contains the
> declaration." That makes top-level `private` genuinely useful — it is the
> tightest scope available for a free function or property — but it also means
> splitting a file in two silently widens every `private` top-level
> declaration you move. There is no compile error; the declaration simply has
> to become `internal` or the split has to be reconsidered.
> **Suggestion.**

```kotlin
// bad — a parsing helper and its regex exported from LedgerParser.kt to the
// whole world, because nothing was written
val AMOUNT_PATTERN = Regex("""^-?\d+\.\d{2}$""")

fun parseAmount(raw: String): Money? =
    if (AMOUNT_PATTERN.matches(raw)) Money.parse(raw) else null

// good — scoped to LedgerParser.kt
private val AMOUNT_PATTERN = Regex("""^-?\d+\.\d{2}$""")

private fun parseAmount(raw: String): Money? =
    if (AMOUNT_PATTERN.matches(raw)) Money.parse(raw) else null
```

## 5.9 Turn on explicit API mode in every module you publish as a library.

> Why? §5.4 and §5.7 are both easy to forget and impossible to lint reliably.
> Explicit API mode makes the compiler do it: it "requires visibility
> modifiers for declarations if the default visibility exposes them to the
> public API" and requires explicit types for public properties and functions,
> so "no declarations are exposed to the public API unintentionally." Primary
> constructors, `data class` properties, accessors, and `override` members are
> exempt for readability, and only production sources are analysed. Use
> `explicitApi()` for errors and `explicitApiWarning()` while migrating.
> **Violation — enforced by the compiler (`-Xexplicit-api=strict`).**

```kotlin
// bad — build.gradle.kts with nothing configured; the two declarations below
// compile cleanly and are both public
// (no kotlin { } configuration)

fun render(report: Report) = renderer.render(report)

val defaultLocale = Locale.forLanguageTag("en-GB")

// good — build.gradle.kts
kotlin {
    explicitApi() // or explicitApiWarning() while migrating
}

// good — the same declarations, now forced to say what they are
public fun render(report: Report): String = renderer.render(report)

internal val defaultLocale: Locale = Locale.forLanguageTag("en-GB")
```

## 5.10 Write modifiers in the order the coding conventions prescribe, and put annotations before all of them.

> Why? The
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#modifiers-order)
> fix one canonical order — visibility, then `expect`/`actual`, then
> `final`/`open`/`abstract`/`sealed`/`const`, `external`, `override`,
> `lateinit`, `tailrec`, `vararg`, `suspend`, `inner`,
> `enum`/`annotation`/`fun`, `companion`, `inline`/`value`, `infix`,
> `operator`, `data` — precisely so that a reader scanning a file finds
> visibility in the same column every time. They also state: "Place all
> annotations before modifiers."
> **Violation — enforced by `ktlint/standard:modifier-order`.**

```kotlin
interface Cache {
    suspend fun evict(key: String)
}

// bad — modifiers shuffled, annotation buried in the middle of them
class RedisCache(private val client: RedisClient) : Cache {
    suspend @Deprecated("Use evictAll") override fun evict(key: String) {
        client.del(key)
    }
}

// good — annotation first, then `override`, then `suspend`, per the list
class RedisCache(private val client: RedisClient) : Cache {
    @Deprecated("Use evictAll")
    override suspend fun evict(key: String) {
        client.del(key)
    }
}
```

## 5.11 Declare a local as close to its first use as possible, and inside the narrowest block that needs it.

> Why? A local declared at the top of a long function is in scope — and
> therefore in the reader's working memory — for every line in between, even
> the fifty that have nothing to do with it. Declaring at first use also
> means the declaration and its initializer are adjacent, which is what makes
> §5.1 and §5.2 achievable: a variable you cannot initialize where you declare
> it is usually a variable declared too early. The
> [coding conventions on source code organization](https://kotlinlang.org/docs/coding-conventions.html#source-code-organization)
> apply the same "close to usage" principle to declaration placement
> generally.
> **Suggestion.**

```kotlin
// bad — `formatter` and `sink` live for the whole function; `sink` is only
// used in one branch
fun export(report: Report, target: Target): ExportResult {
    val formatter = DateTimeFormatter.ISO_INSTANT
    val sink = target.openSink()
    if (report.isEmpty()) {
        return ExportResult.Skipped
    }
    validate(report)
    return sink.write(report.render(formatter))
}

// good — each declaration appears where it starts mattering
fun export(report: Report, target: Target): ExportResult {
    if (report.isEmpty()) {
        return ExportResult.Skipped
    }
    validate(report)
    val formatter = DateTimeFormatter.ISO_INSTANT
    val sink = target.openSink()
    return sink.write(report.render(formatter))
}
```

## 5.12 Destructure only when the component *order* is a stable part of the type's contract, and never for a type you do not own.

> Why? A destructuring declaration binds by position, not by name.
> `val (name, email) = user` compiles identically to
> `val name = user.component1(); val email = user.component2()` — so
> reordering two `String` properties in a `data class` five modules away
> silently swaps the two locals here, with no compile error and no diff on
> this line. The
> [coding conventions](https://kotlinlang.org/docs/coding-conventions.html#destructuring-declarations)
> only describe how to format destructuring, not when it is safe; the safety
> constraint is that the component order must be as stable as the type name.
> `Pair`, `Map.Entry`, and small local `data class`es qualify. A domain
> `data class` with six same-typed properties does not.
> **Suggestion.**

```kotlin
// bad — one property reorder in Customer, five modules away, silently swaps
// `city` and `country`, and the code still compiles and still "works"
data class Customer(val name: String, val city: String, val country: String)

fun label(customer: Customer): String {
    val (name, city, country) = customer
    return "$name, $city, $country"
}

// good — named access; a property rename is a compile error, a reorder is a
// no-op
fun label(customer: Customer): String =
    "${customer.name}, ${customer.city}, ${customer.country}"

// good — positional destructuring where position IS the contract
for ((code, region) in regionsByCode) {
    register(code, region)
}
```

## 5.13 Keep destructuring to a few entries, and use `_` for components you do not need.

> Why? Past three entries a destructuring declaration becomes a
> positional puzzle: the reader has to count commas against the declaration
> site to work out which binding is which. Binding a component you never use
> is worse — it looks like it matters, and it makes a subsequent reorder
> harder to spot. `_` says "position occupied, value ignored" without
> inventing a name — but note that a `_` still occupies an entry, so it
> lowers the reading cost without lowering the count.
> **Violation — enforced by `detekt/DestructuringDeclarationWithTooManyEntries`
> (`maxDestructuringEntries`, default 3).**

```kotlin
// bad — five positional bindings, two of them unused
val (id, _createdAt, amount, _currency, status) = row

// good — within the threshold, and `_` for the component you do not need
val (id, _, amount) = row

// good — past the threshold, stop destructuring entirely; `_` placeholders
// would still count as entries here
val id = row.id
val amount = row.amount
val status = row.status
```

## 5.14 Put a stateless function at the top level; do not wrap it in an `object` to imitate a Java utility class.

> Why? The Android style guide is explicit that "a `.kt` file can declare one
> or more types, functions, properties, or type aliases at the
> [top-level](https://developer.android.com/kotlin/style-guide#top-level_declarations)."
> A namespace-only `object` buys nothing Kotlin does not already have —
> imports already disambiguate, and the `object` adds an instance, a class
> file, and a `StringUtils.` prefix at every call site. Reserve `object` for
> something that genuinely has state or implements an interface, and
> `companion object` for members that need the enclosing type's private scope
> or its type parameters. See
> [Chapter 14, Objects, Companions & Factories](14-objects-and-companions.md)
> for the full decision.
> **Suggestion.**

```kotlin
// bad — a Java utility class transliterated into Kotlin
object StringUtils {
    fun truncate(value: String, maxLength: Int): String =
        if (value.length <= maxLength) value else value.take(maxLength)
}

val short = StringUtils.truncate(title, 40)

// good — a top-level extension; import it and call it
fun String.truncate(maxLength: Int): String =
    if (length <= maxLength) this else take(maxLength)

val short = title.truncate(40)

// good — `object` where there is genuinely one instance with behaviour
object SystemClock : Clock {
    override fun now(): Instant = Instant.now()
}
```

## 5.15 Use `const val` for compile-time constants, and know exactly what it requires.

> Why? `const val` inlines the value into every call site and emits a real
> `static final` field for Java callers; a plain `val` is a property with a
> getter, initialized at class-init time. The
> [language reference](https://kotlinlang.org/docs/properties.html#compile-time-constants)
> lists three hard requirements: the property "must be either a top-level
> property, or a member of an `object` declaration or a companion object", it
> "must be initialized with a value of type `String` or a primitive type", and
> it "can't have a custom getter". That rules out `List`, `Regex`,
> `Duration`, and anything constructed at runtime — those stay plain `val`.
> The Android style guide adds the naming half: constants use
> [`UPPER_SNAKE_CASE`](https://developer.android.com/kotlin/style-guide#constant_names),
> and "constants which are scalar values must use the `const` modifier."
> **Suggestion** — but a bare literal in an expression is a
> **Violation — enforced by `detekt/MagicNumber`.**

```kotlin
// bad — a magic literal, a scalar constant that should be `const`, and a
// `const` that will not compile
class RetryPolicy {
    fun shouldRetry(attempt: Int) = attempt < 3 // MagicNumber

    companion object {
        val MAX_ATTEMPTS = 3 // scalar, so it should be const
        const val BACKOFF = Duration.ofSeconds(2) // does not compile
    }
}

// good
class RetryPolicy {
    fun shouldRetry(attempt: Int) = attempt < MAX_ATTEMPTS

    companion object {
        const val MAX_ATTEMPTS = 3
        val BACKOFF: Duration = Duration.ofSeconds(2)
    }
}
```

## 5.16 Choose between `lateinit`, a nullable `var`, and `by lazy` by what "not available at construction" actually means here.

> Why? These are three answers to three different questions, and picking the
> wrong one costs you either safety or clarity. `by lazy` is for a value you
> can compute yourself on first read — it stays a `val` and there is no window
> in which it is absent. `lateinit var` is for a non-null value someone *else*
> assigns before first read: a DI container, a test `@BeforeEach`, a framework
> callback. A nullable `var` is for a value whose absence is a real,
> observable state the code must handle. Reaching for a nullable `var` when
> you meant `lateinit` forces a `!!` or a null check at every read that can
> never legitimately fail (see [Chapter 6](06-null-safety.md)); reaching for
> `lateinit` when the value really can be absent trades a typed `null` for an
> untyped `UninitializedPropertyAccessException`.
> [The reference](https://kotlinlang.org/docs/properties.html#late-initialized-properties-and-variables)
> constrains `lateinit` to `var` properties that are "non-nullable and must
> not be a primitive type", with no custom getter or setter and no place in
> the primary constructor; `this::prop.isInitialized` tests it.
> **Suggestion** — `detekt/LateinitUsage` can flag every `lateinit` in a
> package if you configure it to, but no rule can tell a legitimate framework
> injection from a dodge.

```kotlin
// bad — nullable var used purely because the value arrives late; every read
// pays a null check that can never legitimately fail
class ReportPrinter {
    private var template: Template? = null

    fun attach(template: Template) {
        this.template = template
    }

    fun print(report: Report): String = template!!.render(report)
}

// good — the framework assigns it before first read
class ReportPrinter {
    @Inject
    lateinit var template: Template

    fun print(report: Report): String = template.render(report)

    fun isReady(): Boolean = this::template.isInitialized
}

// good — you can compute it yourself, so it stays a val
class ReportPrinter(private val loader: TemplateLoader) {
    private val template: Template by lazy { loader.load("report") }

    fun print(report: Report): String = template.render(report)
}

// good — absence is a real state the caller asks about
class ReportPrinter {
    var lastFailure: Throwable? = null
        private set
}
```

## 5.17 Do not widen a declaration's visibility to make it testable.

> Why? A `private` turned `internal` "just for the test" is a permanent
> change to what the rest of the module may depend on, made for a reason that
> never appears at the declaration site. In Kotlin you usually do not need it:
> a module's `test` source set already sees its `main` source set's `internal`
> declarations — the reference lists a Gradle source set as a module "with the
> exception that the `test` source set can access the internal declarations of
> `main`". So `internal` is testable as-is. If a `private` member genuinely
> needs direct coverage, that is usually a signal it wants to be its own type
> with its own public surface.
> **Suggestion.**

```kotlin
// bad — visibility widened for a test, with nothing saying so; the whole
// module can now call it
class PriceEngine(private val rates: RateTable) {
    fun quote(order: Order): Money = applyRounding(rawQuote(order))

    fun applyRounding(amount: Money): Money = amount.roundTo(2) // was private

    private fun rawQuote(order: Order): Money = rates.priceOf(order)
}

// good — the rounding rule becomes its own testable type; PriceEngine's
// surface is unchanged
internal class RoundingPolicy(private val scale: Int) {
    fun apply(amount: Money): Money = amount.roundTo(scale)
}

class PriceEngine(
    private val rates: RateTable,
    private val rounding: RoundingPolicy = RoundingPolicy(scale = 2),
) {
    fun quote(order: Order): Money = rounding.apply(rawQuote(order))

    private fun rawQuote(order: Order): Money = rates.priceOf(order)
}
```
