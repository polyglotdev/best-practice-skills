<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 2. Source Files & Structure

Everything above the first `{` of a declaration is decided before any
interesting code is written, and almost all of it is mechanical. This chapter
covers the
[Android Kotlin style guide's Source files
section](https://developer.android.com/kotlin/style-guide#source_files) —
file naming, encoding, special characters, and the fixed
[file structure](https://developer.android.com/kotlin/style-guide#structure) —
together with the Kotlin coding conventions'
[Source code organization](https://kotlinlang.org/docs/coding-conventions.html#source-code-organization)
section, which goes further on
[directory structure](https://kotlinlang.org/docs/coding-conventions.html#directory-structure),
[class layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout),
and where extension functions belong.

Kotlin's file model differs from Java's in one consequential way, and it is the
reason this chapter exists as more than a restatement: a `.kt` file may declare
any number of top-level types, functions, properties, and type aliases, and the
file name is not required to match any of them. Java's compiler enforces the
one-public-class-per-file rule; Kotlin's does not. That freedom is genuinely
useful and it is also the single easiest thing to abuse, so most of the rules
below are about spending it deliberately.

The *layout* of what is here — where blank lines fall, what column an import
wraps at, whether the import list is ASCII sorted — belongs to `ktlint` and is
settled in [Chapter 1](01-formatting-and-tooling.md). What this chapter governs
is different: which imports may exist at all, how many declarations a file may
hold, and in what order a class presents its members. A formatter has no
opinion on any of that. Naming the types and members themselves is
[Chapter 3](03-naming.md); what goes *inside* a KDoc block is
[Chapter 4](04-kdoc.md); visibility modifiers are
[Chapter 5](05-declarations-and-visibility.md).

**Tool alignment:** ktlint's `standard:filename`, `standard:package-name`,
`standard:no-wildcard-imports`, `standard:import-ordering`,
`standard:no-unused-imports`, `standard:final-newline`, and
`standard:no-empty-file` cover the mechanical half; detekt's
`MatchingDeclarationName`, `InvalidPackageDeclaration`,
`MissingPackageDeclaration`, `ClassOrdering`, `AbsentOrWrongFileLicense`,
`UtilityClassWithPublicConstructor`, and `TooManyFunctions` cover most of the
rest. Rules a named check enforces are marked **Violation**; the ordering rules
that require judgement are **Suggestion**.

## 2.1 Name a file that holds a single top-level class after that class, case-sensitively.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#source_files)
> requires that "if a source file contains only a single top-level class, the
> file name should reflect the case-sensitive name plus the `.kt` extension",
> and the
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#source-file-names)
> extend it to interfaces and to a class "potentially with related top-level
> declarations". Kotlin will not stop you doing otherwise, which is exactly why
> the rule needs stating: every tool that maps a stack-trace frame or a
> `git blame` line back to a file — IDE navigation, coverage reports, code
> search — depends on the mapping being predictable. A mismatched name also
> breaks on the first case-sensitive filesystem it meets, so it compiles on a
> developer's macOS machine and fails on Linux CI.
> **Violation — enforced by `standard:filename` and
> `detekt/MatchingDeclarationName`.**

```kotlin
// bad — file OrderUtils.kt
class OrderHelper

// bad — file orderhelper.kt; fine on a case-insensitive filesystem,
// broken on Linux CI
class OrderHelper

// good — file OrderHelper.kt
class OrderHelper

// good — file Invoice.kt; one class plus the extensions that belong to it
class Invoice(val lines: List<LineItem>)

fun Invoice.total(): Money = lines.fold(Money.ZERO) { acc, line -> acc + line.price }
```

## 2.2 Give a multi-declaration file a descriptive PascalCase name — never `Util`, `Helper`, or `Misc`.

> Why? The
> [Android guide's](https://developer.android.com/kotlin/style-guide#source_files)
> rule for a file with several top-level declarations is to "choose a name that
> describes the contents of the file, apply PascalCase ... and append the `.kt`
> extension". The
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#source-file-names)
> add the negative half explicitly: "The name of the file should describe what
> the code in the file does. Therefore, you should avoid using meaningless
> words such as `Util` in file names." A file called `Utils.kt` has no
> membership criterion, so nothing ever leaves it and everything eventually
> joins it. Six months later it is 1,400 lines, every module depends on it, and
> the only honest description of its contents is "things".
> **Suggestion — `detekt/ForbiddenClassName` can ban specific name patterns for
> classes, but nothing checks a file name for meaninglessness.**

```kotlin
// bad — StringUtils.kt; no membership criterion, so it grows forever
fun String.slugify(): String = ...
fun String.truncate(max: Int): String = ...
fun parseIban(raw: String): Iban = ...
fun formatMoney(amount: Money, locale: Locale): String = ...

// good — split by theme, each name describing the contents
// SlugFormatting.kt
fun String.slugify(): String = ...
fun String.truncate(max: Int): String = ...

// IbanParsing.kt
fun parseIban(raw: String): Iban = ...

// MoneyFormatting.kt
fun formatMoney(amount: Money, locale: Locale): String = ...
```

## 2.3 Encode every file as UTF-8, and use the ASCII horizontal space as the only whitespace character.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#source_files)
> opens its Source files section with "All source files must be encoded as
> UTF-8" and then
> [narrows the whitespace rule](https://developer.android.com/kotlin/style-guide#whitespace_characters)
> to a single
> character: "Aside from the line terminator sequence, the **ASCII horizontal
> space character (0x20)** is the only whitespace character that appears
> anywhere in a source file." Two consequences follow, and the guide states
> both: "all other whitespace characters in string and character literals are
> escaped", and "tab characters are *not* used for indentation." The failure
> mode that actually bites is neither of those — it is a non-breaking space
> (U+00A0) pasted from a browser or a design document, which is invisible in
> the editor and produces a compiler error the author cannot see.
> **Violation — the tab half is enforced by `standard:indent` (ktlint never
> emits a tab). Nothing catches a stray non-breaking space; it surfaces as a
> Kotlin "unresolved reference" or "expecting a top level declaration" error.**

```kotlin
// bad — a literal tab indents the body, and a literal tab sits in the string
class Report {
	fun header(): String {
		return "name	total"
	}
}

// good — spaces for indentation, \t for the tab that is actually data
class Report {
    fun header(): String = "name\ttotal"
}
```

Declare the encoding in the build so no machine falls back to a platform
default:

```kotlin
// build.gradle.kts — Kotlin defaults to UTF-8, javac does not
tasks.withType<JavaCompile>().configureEach {
    options.encoding = "UTF-8"
}
```

```xml
<!-- pom.xml -->
<properties>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
</properties>
```

## 2.4 Use a special escape sequence rather than the equivalent Unicode escape.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#special_escape_sequences)
> lists the set exactly — "for any character that has a
> special escape sequence (`\b`, `\n`, `\r`, `\t`, `\'`, `\"`, `\\`, and `\$`),
> that sequence is used rather than the corresponding Unicode (e.g.,
> `\u000a`) escape". Kotlin's set includes one Java does not: `\$`, which is
> how you write a literal dollar sign without starting a string template. Getting
> that one wrong is not a readability problem but a behaviour problem — an
> unescaped `$` followed by an identifier silently becomes an interpolation.
> **Suggestion — no ktlint or detekt rule checks escape-sequence choice.**

```kotlin
// bad — Unicode escapes for characters that have a named form, and a bare
// dollar that turns into a template
val row = "name\u0009total"
val quoted = "\u0022hello\u0022"
val label = "cost in $" + "USD"

// good
val row = "name\ttotal"
val quoted = "\"hello\""
val label = "cost in \$USD"
```

## 2.5 Write printable non-ASCII characters literally; escape only invisible ones, and comment them.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#non-ascii_characters)
> makes this a readability decision and nothing else:
> "The choice depends only on which makes the code **easier to read and
> understand.** Unicode escapes are discouraged for printable characters at any
> location and are strongly discouraged outside of string literals and
> comments." Its own examples grade `val unitAbbrev = "μs"` as "Best: perfectly
> clear even without a comment" and `val unitAbbrev = "\u03bcs"` as "Poor: the
> reader has no idea what this is." The genuinely useful case runs the other
> way — a zero-width space, a byte-order mark, a right-to-left mark — where the
> escape plus a comment is the only honest rendering, because the literal
> character would be invisible on screen.
> **Suggestion — no check distinguishes a justified escape from a gratuitous
> one.**

```kotlin
// bad — the file is already UTF-8 and nobody can read this
val unitAbbrev = "\u03bcs"

// bad — the escape is right, but the reader has no idea what it is
fun withBom(payload: String) = "\uFEFF" + payload

// good — printable character, written literally
val unitAbbrev = "μs"

// good — invisible character escaped, and explained
fun withBom(payload: String) = "\uFEFF" + payload // U+FEFF BOM, required downstream
```

## 2.6 Lay the file out in exactly five sections, in order, separated by one blank line each.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#structure)
> fixes the order and the spacing: a `.kt` file
> comprises "Copyright and/or license header (optional), File-level
> annotations, Package statement, Import statements, Top-level declarations",
> and "exactly one blank line separates each of these sections." A fixed order
> means a reader scanning an unfamiliar file finds the package and the
> dependency surface in the same place every time, and a diff to the header
> never entangles with a diff to the imports. The section that gets misplaced
> in practice is file-level annotations, because Kotlin permits them almost
> anywhere above the package statement and IDE quick-fixes are inconsistent
> about where they land.
> **Suggestion — `standard:import-ordering` and `standard:package-name` cover
> parts of this, but nothing checks the five-section order as a whole.**

```kotlin
// bad — annotations below the package statement, two blank lines,
// imports separated from each other
package com.example.billing

@file:JvmName("Invoices")

import java.time.Instant


import java.util.UUID

class Invoice

// good
/*
 * Copyright 2026 Example Inc.
 *
 * Licensed under the Apache License, Version 2.0.
 */

@file:JvmName("Invoices")

package com.example.billing

import java.time.Instant
import java.util.UUID

class Invoice(val id: UUID, val issuedAt: Instant)
```

## 2.7 Put a license header in a `/* */` block comment — never KDoc, never `//`.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#copyright_license)
> is unusually specific here, and gives both the rule
> and the two spellings it rejects: "If a copyright or license header belongs in
> the file it should be placed at the immediate top in a multi-line comment ...
> Do not use a KDoc-style or single-line-style comment." The reason is not
> aesthetic. A `/** */` block at the top of a file is picked up by tooling as
> documentation for whatever follows it, so a Dokka run publishes your Apache
> licence as the description of your first class. Let the build maintain the
> header rather than each author remembering it — a hand-maintained header
> drifts, the year stops updating, and new files miss it entirely.
> **Violation — enforced by `detekt/AbsentOrWrongFileLicense` once
> `licenseTemplate` is configured, or by the Spotless `licenseHeaderFile`
> step.**

```kotlin
// bad — KDoc; Dokka attributes this to the class below it
/**
 * Copyright 2026 Example Inc.
 */
class Invoice

// bad — line comments
// Copyright 2026 Example Inc.
//
// Licensed under the Apache License, Version 2.0.
class Invoice

// good
/*
 * Copyright 2026 Example Inc.
 *
 * Licensed under the Apache License, Version 2.0.
 */

package com.example.billing

class Invoice
```

```kotlin
// good — build.gradle.kts, so the header is generated rather than remembered
spotless {
    kotlin {
        ktlint("1.8.0")
        licenseHeaderFile(rootProject.file("config/spotless/license-header.txt"))
    }
}
```

## 2.8 Put file-level annotations between the header comment and the package statement.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#file-level_annotations)
> places them precisely: "Annotations with the 'file'
> use-site target are placed between any header comment and the package
> declaration." This is the one part of a Kotlin file whose ordering surprises
> people coming from Java, where an annotation always precedes the thing it
> annotates and `package` is first. The practical consequence of getting it
> wrong is worse than untidiness: `@file:JvmName` and `@file:JvmMultifileClass`
> change the generated class name that Java callers link against, so an
> annotation that silently fails to apply is a binary-compatibility break
> discovered by a downstream Java module. See
> [Chapter 27](27-annotations-and-use-site-targets.md) for use-site targets and
> [Chapter 28](28-java-interop.md) for what `@file:JvmName` actually does.
> **Suggestion — no check enforces the position.**

```kotlin
// bad — after the package statement; the compiler rejects this outright,
// and the IDE's "move" quick-fix is what usually produces the next variant
package com.example.billing

@file:JvmName("Invoices")

fun parse(raw: String): Invoice = ...

// good
/*
 * Copyright 2026 Example Inc.
 */

@file:JvmName("Invoices")
@file:JvmMultifileClass

package com.example.billing

fun parse(raw: String): Invoice = ...
```

## 2.9 Give every file a package statement, and never line-wrap it — or an import.

> Why? The Android guide exempts both from the column limit and says so twice, in
> [Package statement](https://developer.android.com/kotlin/style-guide#package_statement)
> and in [Import statements](https://developer.android.com/kotlin/style-guide#import_statements):
> "The package statement is not subject to any column limit and is never
> line-wrapped", and "Similar to the package statement, import statements are
> not subject to a column limit and they are never line-wrapped." Omitting the
> package statement entirely puts the declarations in the root package, where
> nothing in a named package can import them, and where two files with the same
> declaration names collide at the JVM level. A wrapped import is worse than
> merely non-conforming: it cannot be sorted, diffed, or grepped line by line,
> so `git diff` on a dependency change becomes unreadable.
> **Violation — presence is enforced by `detekt/MissingPackageDeclaration`; the
> no-wrap half by ktlint, which rejoins a wrapped package or import statement.**

```kotlin
// bad — wrapped to satisfy a column limit that does not apply here
package com.example.platform.billing.invoicing
    .reconciliation

import com.example.platform.billing.reconciliation
    .LedgerReconciliationService

// good — one line each, however long
package com.example.platform.billing.invoicing.reconciliation

import com.example.platform.billing.reconciliation.LedgerReconciliationService
```

## 2.10 Never write a wildcard import.

> Why? The
> [Android guide's](https://developer.android.com/kotlin/style-guide#import_statements)
> wording is one sentence and admits no exception:
> "Wildcard imports (of any type) are **not allowed.**" Kotlin makes this
> tempting in a way Java does not, because IntelliJ's default Kotlin profile
> collapses imports into a wildcard once a threshold is crossed — so the
> violation arrives from the IDE rather than from the author. The cost is the
> same as in any language: a wildcard hides the file's real dependency surface,
> and when an upstream library adds a type whose simple name collides with one
> you already import by wildcard, a file that compiled yesterday stops
> compiling today and the diff that broke it contains none of your code. See
> [Chapter 1, §1.8](01-formatting-and-tooling.md) for the `.editorconfig` key
> that stops the IDE reintroducing it on every save.
> **Violation — enforced by `standard:no-wildcard-imports`. detekt's
> `WildcardImport` covers the same ground and should be left off, per
> [§47.2](47-ktlint-and-detekt.md).**

```kotlin
// bad — which of the ~60 declarations in kotlinx.coroutines.flow does this
// file actually need?
import kotlinx.coroutines.flow.*
import java.util.*

// good
import java.util.UUID
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
```

## 2.11 Keep imports as one ASCII-sorted list, and import a name rather than fully-qualifying it inline.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#import_statements)
> requires that "import statements for classes,
> functions, and properties are grouped together in a single list and ASCII
> sorted" — one list, not the `java` / `javax` / `kotlin` / `com` grouping Java
> codebases use. The grouping habit is not merely non-conforming; it guarantees
> a merge conflict every time two branches add an import, because each side
> inserts into a different position. Note that ASCII order is *not*
> case-insensitive alphabetical order: uppercase sorts before lowercase, so
> `com.example.Foo` precedes `com.example.bar`. The inline half of this rule is
> the same idea one level down — a fully-qualified name written in an
> expression hides a dependency from the import block, which is the only place
> a reviewer looks for one.
> **Violation — ordering is enforced by `standard:import-ordering`.** The
> inline half is covered by `detekt/UnnecessaryFullyQualifiedName`, which is
> absent from detekt 1.23.8's default config (the docs site is ahead of the
> latest stable release), so treat that half as a **Suggestion** until your
> detekt version ships it; see chapter 47.

```kotlin
// bad — java/kotlin/com grouping with blank lines, plus a dependency that
// never appears in the import block at all
import java.util.UUID

import kotlinx.coroutines.flow.Flow

import com.example.billing.Invoice

fun newId(): String = java.util.UUID.randomUUID().toString()

// good — one ASCII-sorted block; every dependency is visible in it
import com.example.billing.Invoice
import java.util.UUID
import kotlinx.coroutines.flow.Flow

fun newId(): String = UUID.randomUUID().toString()
```

## 2.12 Mirror the package structure in the directory structure.

> Why? The Kotlin coding conventions describe the JVM rule and the pure-Kotlin
> relaxation separately, and the difference matters. For a mixed codebase:
> "Kotlin source files should reside in the same source root as the Java source
> files, and follow the same directory structure: each file should be stored in
> the directory corresponding to each package statement." For pure Kotlin, the
> conventions permit "the package structure with the common root package
> omitted" — so `org.example.kotlin.network.socket` may live in
> `network/socket/` directly under the source root. Take the relaxation only if
> you take it consistently. Half-applied, it produces the worst of both: a
> reader cannot infer a package from a path or a path from a package, and every
> file move becomes a manual `package` edit that someone will forget.
> **Violation — enforced by `detekt/InvalidPackageDeclaration`, which compares
> the declared package against the file's directory. Set its `rootPackage`
> option when you use the common-root-omitted layout, or it will flag the whole
> tree.**

```kotlin
// bad — src/main/kotlin/BillingService.kt
package com.example.platform.billing.invoicing

class BillingService

// good — mixed Java/Kotlin project: full path mirrors the full package
// src/main/kotlin/com/example/platform/billing/invoicing/BillingService.kt
package com.example.platform.billing.invoicing

class BillingService

// good — pure Kotlin project that has committed to omitting the common root
// `com.example.platform`, consistently, everywhere
// src/main/kotlin/billing/invoicing/BillingService.kt
package com.example.platform.billing.invoicing

class BillingService
```

```yaml
# config/detekt/detekt.yml — required for the common-root-omitted layout
naming:
  InvalidPackageDeclaration:
    active: true
    rootPackage: 'com.example.platform'
```

## 2.13 Keep a file focused on one theme; put closely related declarations together and unrelated ones apart.

> Why? The two guides approach this from opposite directions and land in the
> same place.
> [Android](https://developer.android.com/kotlin/style-guide#top-level_declarations):
> "The contents of a file should be focused on a single theme ... Unrelated
> declarations should be separated into their own files and public declarations
> within a single file should be minimized."
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#source-file-organization):
> "Placing multiple declarations ... in the same Kotlin
> source file is encouraged as long as these declarations are closely related to
> each other semantically, and the file size remains reasonable (not exceeding
> a few hundred lines)." Neither guide sets a hard count — Android says
> explicitly that "no explicit restriction is placed on the number nor order of
> the contents of a file." What both reject is the *ungrounded* file: a
> collection whose only shared property is that someone happened to write these
> things on the same afternoon.
> **Suggestion — `detekt/TooManyFunctions` with `allowedFunctionsPerFile` set
> (`thresholdInFiles` under detekt 1.23) will flag the extreme case, but no
> tool can judge whether declarations are semantically related.**

```kotlin
// bad — BillingCore.kt; four unrelated public types sharing a file because
// they were all needed for one ticket
class Invoice(val id: UUID)
class RetryPolicy(val maxAttempts: Int)
interface AuditSink { fun record(event: AuditEvent) }
fun formatIban(raw: String): String = ...

// good — Invoice.kt: one public type plus the declarations that only make
// sense alongside it
class Invoice(
    val id: UUID,
    val lines: List<LineItem>,
)

internal fun Invoice.subtotal(): Money =
    lines.fold(Money.ZERO) { acc, line -> acc + line.price }

// good — Money.kt: a set of extensions performing the same operation on
// several receiver types is exactly the theme Android names
fun Int.toMoney(currency: Currency): Money = Money(toBigDecimal(), currency)
fun Long.toMoney(currency: Currency): Money = Money(toBigDecimal(), currency)
fun BigDecimal.toMoney(currency: Currency): Money = Money(this, currency)
```

## 2.14 Order top-level declarations and class members by a logic you could explain out loud — never by when you wrote them.

> Why? The
> [Android guide](https://developer.android.com/kotlin/style-guide#top-level_declarations)
> declines to mandate a recipe and instead sets a
> standard the author has to meet: "What is important is that each file uses
> **some** logical order, which its maintainer could explain if asked." It then
> names the failure mode outright: "new functions are not just habitually added
> to the end of the file, as that would yield 'chronological by date added'
> ordering, which is not a logical ordering." Chronological order is what you
> get by default, and it is precisely the order that carries no information for
> a reader. The guide's positive guidance is that "declarations higher up will
> inform understanding of those farther down" — so define before you use, and
> put the entry point above its helpers. The same rule governs
> [class members](https://developer.android.com/kotlin/style-guide#class_member_ordering):
> "The order of members within a class follow the same rules as the top-level
> declarations."
> **Suggestion — no tool can judge whether an order is logical.**

```kotlin
// bad — read top to bottom, this is the order the author happened to write
// things in over six months
class OrderService(
    private val repository: OrderRepository,
) {
    private fun applyDiscount(order: Order): Money = ...

    fun place(request: NewOrder): Order = ...

    private val log = LoggerFactory.getLogger(OrderService::class.java)

    fun cancel(orderId: UUID) { ... }

    companion object {
        private const val MAX_LINE_ITEMS = 200
    }
}

// good — properties, public API in call order, private helpers, companion
class OrderService(
    private val repository: OrderRepository,
) {
    private val log = LoggerFactory.getLogger(OrderService::class.java)

    fun place(request: NewOrder): Order { ... }

    fun cancel(orderId: UUID) { ... }

    private fun applyDiscount(order: Order): Money = ...

    companion object {
        private const val MAX_LINE_ITEMS = 200
    }
}
```

## 2.15 Inside a class, declare properties and init blocks first, then secondary constructors, then methods, then the companion object.

> Why? The Kotlin coding conventions'
> [Class layout](https://kotlinlang.org/docs/coding-conventions.html#class-layout)
> section fixes this order exactly, and adds two prohibitions that matter more
> than the order itself: "Do not sort the method declarations alphabetically or
> by visibility, and do not separate regular methods from extension methods.
> Instead, put related stuff together, so that someone reading the class from
> top to bottom can follow the logic of what's happening." Alphabetical order
> is the classic false economy — it looks principled, it survives review, and
> it scatters every cohesive group of methods across the file. The companion
> object goes last because it is almost never what a reader came for.
> **Violation — enforced by `detekt/ClassOrdering`.**

```kotlin
// bad — companion first, secondary constructor buried among the methods,
// methods sorted alphabetically
class Ledger() {
    companion object {
        fun empty(): Ledger = Ledger()
    }

    fun append(entry: Entry) { ... }

    constructor(seed: List<Entry>) : this() {
        entries += seed
    }

    fun balance(): Money = ...

    private val entries = mutableListOf<Entry>()
}

// good — properties and init, secondary constructors, methods, companion
class Ledger() {
    private val entries = mutableListOf<Entry>()

    constructor(seed: List<Entry>) : this() {
        entries += seed
    }

    fun append(entry: Entry) { ... }

    fun balance(): Money = ...

    companion object {
        fun empty(): Ledger = Ledger()
    }
}
```

## 2.16 Keep overloads adjacent, with nothing between them.

> Why? The Kotlin coding conventions'
> [Overload layout](https://kotlinlang.org/docs/coding-conventions.html#overload-layout)
> section is one sentence: "Always put overloads next to each other in a
> class." Overload resolution is one of the least intuitive parts of the
> language — Kotlin adds default arguments and `@JvmOverloads` to the Java
> rules — and the only way to reason about a call site is to see the whole
> overload set at once. A set split across 200 lines guarantees somebody adds a
> fourth overload that silently steals calls from the second. Note that Kotlin
> gives you a way to avoid the question entirely: a single function with
> default argument values is usually better than three overloads, and is
> covered in [Chapter 8](08-functions.md).
> **Suggestion — `detekt/MethodOverloading` caps how *many* overloads a
> declaration may have, but no check enforces adjacency.**

```kotlin
// bad — the two `of` overloads are separated by an unrelated member
companion object {
    fun of(amount: BigDecimal, currency: Currency): Money = Money(amount, currency)

    val ZERO: Money = Money(BigDecimal.ZERO, Currency.USD)

    fun of(amount: String, currency: Currency): Money = of(BigDecimal(amount), currency)
}

// good — the overload set reads as one unit
companion object {
    val ZERO: Money = Money(BigDecimal.ZERO, Currency.USD)

    fun of(amount: BigDecimal, currency: Currency): Money = Money(amount, currency)

    fun of(amount: String, currency: Currency): Money = of(BigDecimal(amount), currency)
}

// good — often better still: one function, default argument, no overload set
fun of(amount: BigDecimal, currency: Currency = Currency.USD): Money =
    Money(amount, currency)
```

## 2.17 Implement interface members in the order the interface declares them.

> Why? The Kotlin coding conventions'
> [Interface implementation layout](https://kotlinlang.org/docs/coding-conventions.html#interface-implementation-layout)
> section: "When implementing an interface, keep the implementing members in
> the same order as members of the interface (if necessary, interspersed with
> additional private methods used for the implementation)." The payoff is
> mechanical — reviewing an implementation against its contract becomes a
> two-column read rather than a search — and it compounds across implementations,
> because two classes implementing the same interface can be diffed against each
> other directly. This is also the cheapest way to notice a member you forgot to
> override before the compiler tells you in less helpful terms.
> **Suggestion — no check compares declaration order against a supertype.**

```kotlin
interface PaymentGateway {
    suspend fun authorize(request: AuthRequest): AuthResult
    suspend fun capture(authId: AuthId, amount: Money): CaptureResult
    suspend fun refund(captureId: CaptureId, amount: Money): RefundResult
}

// bad — implementation in a third order, so reviewing it against the
// interface means jumping around
class StripeGateway(private val client: StripeClient) : PaymentGateway {
    override suspend fun refund(captureId: CaptureId, amount: Money): RefundResult = ...

    override suspend fun authorize(request: AuthRequest): AuthResult = ...

    override suspend fun capture(authId: AuthId, amount: Money): CaptureResult = ...
}

// good — same order as the interface, with helpers interspersed where used
class StripeGateway(private val client: StripeClient) : PaymentGateway {
    override suspend fun authorize(request: AuthRequest): AuthResult = ...

    override suspend fun capture(authId: AuthId, amount: Money): CaptureResult = ...

    private fun toStripeAmount(amount: Money): Long = ...

    override suspend fun refund(captureId: CaptureId, amount: Money): RefundResult = ...
}
```

## 2.18 Prefer a top-level function to a companion-object method or a Java-style utility holder.

> Why? Kotlin has genuine top-level functions, so the two constructs Java uses
> to fake them are pure overhead. A `class Utils { companion object { ... } }`
> allocates a nested class, hides the function behind a qualifier that carries
> no meaning, and — because the companion is a real object — invites somebody to
> put state in it. An `object Utils { ... }` is marginally better and still
> wrong for the same reason: nothing about these functions is related except
> their container. Reach for a companion object when the function genuinely
> belongs to the type — a factory returning `Invoice`, a `fromJson` parser —
> and for a top-level function otherwise. Companion object design is
> [Chapter 14](14-objects-and-companions.md).
> **Violation for the worst form — `detekt/UtilityClassWithPublicConstructor`
> flags a class whose members are all in a companion but which still exposes a
> public constructor. The wider preference is a Suggestion.**

```kotlin
// bad — a Java utility class transliterated into Kotlin
class StringUtils {
    companion object {
        fun slugify(value: String): String = ...
    }
}

val slug = StringUtils.slugify(title)

// bad — an object holder, for functions with nothing in common but a name
object StringUtils {
    fun slugify(value: String): String = ...
}

// good — a top-level function, in SlugFormatting.kt
fun slugify(value: String): String = ...

val slug = slugify(title)

// good — an extension, when there is an obvious receiver
fun String.slugify(): String = ...

val slug = title.slugify()

// good — a companion object where the function really does belong to the type
class Invoice private constructor(val id: UUID) {
    companion object {
        fun fromJson(raw: String): Invoice = ...
    }
}
```

## 2.19 Put extensions that every client needs in the class's own file, and client-specific extensions next to the client.

> Why? The
> [Kotlin coding conventions' Source file organization
> section](https://kotlinlang.org/docs/coding-conventions.html#source-file-organization)
> gives the placement rule and the anti-pattern in the same breath: "when defining extension functions for a
> class which are relevant for all clients of this class, put them in the same
> file with the class itself. When defining extension functions that make sense
> only for a specific client, put them next to the code of that client. Avoid
> creating files just to hold all extensions of some class." An
> `InvoiceExtensions.kt` file is the `Utils.kt` problem in a costume — it has
> no membership criterion, so every extension anyone ever writes on `Invoice`
> lands in it, including the three that only one caller uses and that should
> have been `private` in that caller's file.
> **Suggestion — no check knows which clients an extension is for.**

```kotlin
// bad — InvoiceExtensions.kt; a file whose only theme is a receiver type
fun Invoice.total(): Money = ...
fun Invoice.toPdfModel(): PdfModel = ...        // only the PDF renderer uses this
fun Invoice.toSearchDocument(): SearchDoc = ... // only the indexer uses this

// good — Invoice.kt: extensions every client of Invoice needs
class Invoice(val lines: List<LineItem>)

fun Invoice.total(): Money =
    lines.fold(Money.ZERO) { acc, line -> acc + line.price }

// good — PdfInvoiceRenderer.kt: private to the one client that needs it
class PdfInvoiceRenderer {
    fun render(invoice: Invoice): ByteArray = invoice.toPdfModel().render()
}

private fun Invoice.toPdfModel(): PdfModel = ...
```

## 2.20 Put a nested class next to the code that uses it; put externally-used nested classes after the companion object.

> Why? The
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#class-layout)
> give both halves: "Put nested classes next
> to the code that uses those classes. If the classes are intended to be used
> externally and aren't referenced inside the class, put them in the end, after
> the companion object." The split matters because the two kinds of nested
> class are doing different jobs. One is a local implementation detail whose
> definition is part of understanding the method above it; the other is part of
> the enclosing type's public vocabulary — a `Builder`, a result type, an
> options struct — and a reader looking for it wants it in a predictable place,
> not interleaved with private machinery. Kotlin's default nested class is
> *static* in Java terms, so an `inner` class is a deliberate choice that
> captures the outer instance; see [Chapter 10](10-classes-and-interfaces.md).
> **Suggestion — `detekt/NestedClassesVisibility` flags a nested class that is
> more visible than its container, but nothing checks position.**

```kotlin
// bad — the public result type is buried between two private helpers, and
// the private state machine sits far from the method that drives it
class Reconciler {
    private enum class State { IDLE, RUNNING, DONE }

    data class Result(val matched: Int, val unmatched: Int)

    private fun advance(state: State): State = ...

    fun reconcile(ledger: Ledger): Result { ... }
}

// good — private helper next to its user, public type after the companion
class Reconciler {
    fun reconcile(ledger: Ledger): Result {
        var state = State.IDLE
        // ...
        return Result(matched, unmatched)
    }

    private fun advance(state: State): State = ...

    private enum class State { IDLE, RUNNING, DONE }

    companion object {
        private const val BATCH_SIZE = 500
    }

    data class Result(val matched: Int, val unmatched: Int)
}
```
