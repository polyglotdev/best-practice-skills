<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 1. Formatting & Tooling

Kotlin has two normative style guides and, unusually, they agree about layout.
The [Android Kotlin style guide's Formatting
section](https://developer.android.com/kotlin/style-guide#formatting) and the
[Kotlin coding conventions'
Formatting section](https://kotlinlang.org/docs/coding-conventions.html#formatting)
both fix the indent at four spaces, put the opening brace at the end of the
line, and treat semicolons as noise. What they do not do is ship an
implementation. [`ktlint`](https://ktlint.github.io/ktlint/latest/) does, and
this chapter is about handing every layout decision to it and never having the
argument again.

That delegation is the same one
[`best-practice-go`](../../best-practice-go/references/01-formatting.md) makes
to `gofmt`, `best-practice-java` makes to `google-java-format`, and
`best-practice-js` makes to Prettier. Every code sample in every chapter of
this skill is written as ktlint's `ktlint_official` style would emit it, and no
later chapter re-litigates a single whitespace decision.

**Indentation in this skill is four spaces.** The Android guide's sentence is
unambiguous: "Each time a new block or block-like construct is opened, the
indent increases by four spaces." The Kotlin coding conventions'
[Indentation](https://kotlinlang.org/docs/coding-conventions.html#indentation)
section says the same thing in five words: "Use four spaces for indentation. Do
not use tabs." This differs from the two-space block indent used elsewhere in
this repository for Java and TypeScript. Four wins here because it is the
upstream Kotlin rule.

Formatting is not static analysis. `ktlint` reformats; `detekt` reasons about
semantics, complexity, and bug patterns; the Kotlin compiler owns nullability
and warnings. Those three concerns and their configuration are
[Chapter 47](47-ktlint-and-detekt.md). This chapter covers only the formatter
and the compiler flags that belong next to it.

**Tool alignment:** the rules below map to ktlint's `standard` rule set —
`standard:indent`, `standard:max-line-length`, `standard:no-semicolons`,
`standard:no-wildcard-imports`, `standard:import-ordering`,
`standard:no-unused-imports`, `standard:final-newline`,
`standard:no-trailing-whitespaces`, `standard:no-multi-spaces`,
`standard:trailing-comma-on-declaration-site`,
`standard:trailing-comma-on-call-site`, and `standard:ktlint-suppression` —
all driven from `.editorconfig`. Rules a named ktlint rule or a compiler flag
actually enforces are marked **Violation**; the rest are **Suggestion**.

## 1.1 Run `ktlintFormat` before every commit and `ktlintCheck` in CI.

> Why? `ktlintFormat` is the write path and `ktlintCheck` is the read-only
> gate. Running only the gate means every developer learns about formatting
> failures after pushing; running only the write path means an unformatted file
> can still reach `main` through a machine that skipped it. Both, in that
> order. A formatting failure is the cheapest possible build failure — one
> command fixes it, with zero judgement involved — so it belongs first in the
> pipeline, not last.
> **Violation — enforced by `ktlintCheck`.**

```kotlin
// bad — hand-laid-out; ktlint rewrites almost every line of this
class Rates
{
  fun convert(amount:BigDecimal,from:Currency,to:Currency):BigDecimal
  {
    if(amount.signum()<0) throw IllegalArgumentException("negative amount");
    return amount.multiply( rateFor(from,to) )
  }
}

// good — exactly what ktlint emits
class Rates {
    fun convert(amount: BigDecimal, from: Currency, to: Currency): BigDecimal {
        require(amount.signum() >= 0) { "negative amount" }
        return amount.multiply(rateFor(from, to))
    }
}
```

The local half is worth automating, and the Gradle plugin ships the hook task
so nobody has to write it:

```bash
# good — installs a pre-commit hook that formats staged Kotlin files
./gradlew addKtlintFormatGitPreCommitHook

# good — CI read-only gate
./gradlew ktlintCheck
```

## 1.2 Indent with four spaces. Never tabs, never two.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#indentation)
> fixes the block indent at four spaces and the
> [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html#indentation)
> repeat it verbatim, adding "Do not use tabs." A tab renders at a different
> width in every viewer, so a tab-indented file is unreadable in half the tools
> that open it. Two-space Kotlin is a habit imported from Java or JavaScript
> and it produces a whole-file diff the first time anyone runs the formatter.
> Whatever your continuation indent is, set it in `.editorconfig` alongside
> `indent_size` rather than leaving each IDE to pick its own (§1.4).
> **Violation — enforced by `standard:indent`.**

```kotlin
// bad — two-space blocks, a tab on the return line
class OrderService(
  private val repository: OrderRepository,
) {
  fun place(request: NewOrder): Order {
	return repository.save(Order.from(request))
  }
}

// good — four spaces, no tabs
class OrderService(
    private val repository: OrderRepository,
) {
    fun place(request: NewOrder): Order {
        return repository.save(Order.from(request))
    }
}
```

## 1.3 Accept the 100-column limit; never hand-wrap to something narrower.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#line_wrapping)
> sets the limit at 100 characters and names its own exceptions: lines where
> obeying the limit is impossible (a long URL in KDoc), `package` and `import`
> statements, and shell command lines inside comments. ktlint reads the limit
> from `max_line_length` and chooses break points using the guide's
> [where-to-break](https://developer.android.com/kotlin/style-guide#where_to_break)
> rules — break *after* an operator or infix function name, *before* a `.`,
> `?.`, or `::`. Hand-wrapping at 80 "for the side-by-side diff view" produces
> breaks the formatter immediately undoes, so the change never survives the
> next `ktlintFormat`.
> **Violation — enforced by `standard:max-line-length`.**

```kotlin
// bad — hand-wrapped to ~60 columns; ktlint rejoins these
val result =
    repository
        .findByStatus(
            Status.ACTIVE,
        )

// good — fits inside 100 columns, so it stays on one line
val result = repository.findByStatus(Status.ACTIVE)

// good — genuinely too long, so ktlint breaks each parameter onto its own
// line at +4, with the closing paren and return type unindented
fun <T> Iterable<T>.joinToString(
    separator: CharSequence = ", ",
    prefix: CharSequence = "",
    postfix: CharSequence = "",
): String {
    // ...
}
```

## 1.4 Put the entire ktlint configuration in `.editorconfig`, never in the build script.

> Why? `.editorconfig` is the only configuration surface both ktlint *and* the
> IDE read. Splitting the settings — indent in the build script, line length in
> the IDE profile, rule toggles in a third place — guarantees the editor
> reformats a file one way and CI rejects it the other way, and the developer
> caught between them has no single file to read. Every ktlint property is an
> `.editorconfig` key, so there is nothing the build script needs to say about
> style at all.
> **Suggestion — nothing fails a build for configuring ktlint in the wrong
> place; the symptom is drift between the IDE and CI.**

```kotlin
// bad — style settings hidden in build.gradle.kts, invisible to the IDE
ktlint {
    // hypothetical knobs that would disagree with whatever the editor does
}
```

```ini
# good — .editorconfig at the repository root, read by ktlint and the IDE
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{kt,kts}]
ktlint_code_style = ktlint_official
indent_style = space
indent_size = 4
max_line_length = 100
ij_kotlin_allow_trailing_comma = true
ij_kotlin_allow_trailing_comma_on_call_site = true
ij_kotlin_packages_to_use_import_on_demand = unset
```

`ij_kotlin_packages_to_use_import_on_demand = unset` is the setting that stops
IntelliJ collapsing five imports from one package into a wildcard the moment
you add a sixth. Without it the IDE reintroduces the violation §1.8 bans, on
every save.

## 1.5 Choose `ktlint_code_style` once, for the whole repository.

> Why? ktlint ships
> [three code styles](https://ktlint.github.io/ktlint/latest/rules/code-styles/)
> and they are not interchangeable.
> `ktlint_official` is the default from ktlint 1.0 and, in the project's own
> words, "combines the best elements from the Kotlin Coding conventions and
> Android's Kotlin styleguide" while adding formatting decisions neither guide
> makes. `intellij_idea` "aims to be compatible with default formatter of
> IntelliJ IDEA"; `android_studio` aims at Android Studio's. Setting different
> styles per module means every cross-module file move produces a full-file
> reformat, and every developer's IDE disagrees with somebody's CI.
> `ktlint_official` is the right default for a server-side Kotlin codebase and
> is what this skill assumes. The one thing to know going in is ktlint's own
> warning: `ktlint_official` "in some cases formats code in a way which is not
> accepted by the default code formatters in IntelliJ IDEA and Android Studio",
> so the IDE needs configuring to match (§1.19).
> **Suggestion — the style is a project decision, not a checkable rule.**

```ini
# bad — per-module divergence; moving a file reformats it entirely
# modules/core/.editorconfig
[*.{kt,kts}]
ktlint_code_style = intellij_idea

# modules/api/.editorconfig
[*.{kt,kts}]
ktlint_code_style = android_studio

# good — one decision, at the repository root, with root = true above it
[*.{kt,kts}]
ktlint_code_style = ktlint_official
```

## 1.6 Never hand-align code horizontally.

> Why? The Android guide's
> [horizontal whitespace](https://developer.android.com/kotlin/style-guide#horizontal)
> section enumerates every place a single ASCII space may appear and column
> alignment is not among them — "a single ASCII space also appears in the
> following places only". The practical cost is that a one-character rename
> reflows every aligned line, so a trivial change produces a five-line diff and
> `git blame` attributes four untouched lines to the wrong commit.
> **Violation — enforced by `standard:no-multi-spaces`.**

```kotlin
// bad — aligned by hand; renaming `id` reflows all three lines
private val id          : UUID
private val displayName : String
private val retryCount  : Int

// good — no space before the colon, one space after, always
private val id: UUID
private val displayName: String
private val retryCount: Int
```

## 1.7 Never write a semicolon.

> Why? The Kotlin coding conventions'
> [Semicolons](https://kotlinlang.org/docs/coding-conventions.html#semicolons)
> section is four words long: "Omit semicolons whenever possible." The Android
> guide's
> [one statement per line](https://developer.android.com/kotlin/style-guide#one_statement_per_line)
> rule says the same from the other direction: "Each statement is followed by a
> line break. Semicolons are not used." A trailing semicolon is Java muscle
> memory; a *separating* semicolon is worse, because it hides a second
> statement on a line where a reviewer will not look for one. The single place
> Kotlin still requires one is between an `enum` entry list and a following
> member declaration.
> **Violation — enforced by `standard:no-semicolons`.**

```kotlin
// bad — trailing semicolons, and two statements sharing one line
val total = subtotal + tax;
log.info("charging"); charge(total);

// good
val total = subtotal + tax
log.info("charging")
charge(total)

// good — the one semicolon the language requires
enum class Status {
    ACTIVE,
    SUSPENDED,
    ;

    val isOpen: Boolean get() = this == ACTIVE
}
```

## 1.8 Never write a wildcard import, and let ktlint own import order and unused-import removal.

> Why? The
> [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide#import_statements)
> is absolute — "Wildcard imports (of any type) are **not allowed**" — and
> requires that imports be "grouped together in a single list and ASCII
> sorted", with no `java` / `javax` / `kotlin` / `com` grouping and no blank
> lines between groups. A wildcard hides the file's real dependency surface,
> and it is a forward-compatibility hazard: when an upstream library adds a
> type whose simple name collides with one you already import by wildcard, a
> file that compiled yesterday stops compiling today, and the diff that broke
> it contains none of your code. Import *content* rules are
> [Chapter 2, §2.10 and §2.11](02-source-files-and-structure.md).
> **Violation — enforced by `standard:no-wildcard-imports`,
> `standard:import-ordering`, and `standard:no-unused-imports`.**

```kotlin
// bad — wildcard, custom grouping, blank lines between groups, and one
// import the file no longer uses
import java.util.*

import kotlinx.coroutines.flow.Flow

import com.example.billing.LegacyLedger
import com.example.billing.Invoice

// good — one ASCII-sorted block, explicit, nothing unused
import com.example.billing.Invoice
import java.time.Instant
import java.util.UUID
import kotlinx.coroutines.flow.Flow
```

The IDE is the usual source of a reintroduced wildcard. Pin it in
`.editorconfig` alongside everything else:

```ini
[*.{kt,kts}]
ij_kotlin_packages_to_use_import_on_demand = unset
ij_kotlin_imports_layout = *
```

## 1.9 Decide trailing commas once, in `.editorconfig`, and prefer allowing them.

> Why? The Kotlin coding conventions'
> [Trailing commas](https://kotlinlang.org/docs/coding-conventions.html#trailing-commas)
> section states that the style guide "encourages the use of trailing commas at
> the declaration site and leaves it at your discretion for the call site", and
> lists the reason: "It makes version-control diffs cleaner — as all the focus
> is on the changed value." Without a trailing comma, adding a parameter to a
> multi-line list touches two lines — the new one and the previous line that
> gains a comma — so every such diff implicates an author who did not change
> anything. ktlint reads two separate keys for the two sites, and leaving
> either unset means the formatter will happily *delete* trailing commas the
> team keeps adding back.
> **Violation — enforced by `standard:trailing-comma-on-declaration-site` and
> `standard:trailing-comma-on-call-site`, both driven by the `.editorconfig`
> keys below.**

```ini
# good — .editorconfig
[*.{kt,kts}]
ij_kotlin_allow_trailing_comma = true
ij_kotlin_allow_trailing_comma_on_call_site = true
```

```kotlin
// bad — no trailing comma; adding `age` also rewrites the `lastName` line
data class Person(
    val firstName: String,
    val lastName: String
)

// good — adding a component touches exactly one line
data class Person(
    val firstName: String,
    val lastName: String,
    val age: Int,
)
```

## 1.10 Drive ktlint through the Gradle plugin, pinned, not a hand-rolled `Exec` task.

> Why? The plugin resolves the ktlint distribution from Maven Central, so
> nobody installs a binary; it registers `ktlintCheck` and `ktlintFormat` as
> ordinary tasks; it wires `ktlintCheck` into `check`, so `./gradlew build`
> covers CI with no extra step; and it caches per source set. A hand-rolled
> `Exec` task reimplements all of that badly and silently drifts between
> developer machines and CI. Pinning both the plugin and the `version` inside
> the extension matters for the same reason it matters for any formatter:
> ktlint's output changes between releases, and an unpinned formatter means one
> developer's `ktlintFormat` reflows files another developer's version had
> already formatted.

```kotlin
// bad — a local binary nobody has, no caching, no check wiring
tasks.register<Exec>("format") {
    commandLine("ktlint", "-F", "src/**/*.kt")
}

// good — build.gradle.kts
import org.jlleitschuh.gradle.ktlint.reporter.ReporterType

plugins {
    kotlin("jvm") version "2.4.0"
    id("org.jlleitschuh.gradle.ktlint") version "14.2.0"
}

ktlint {
    version.set("1.8.0")
    ignoreFailures.set(false)
    reporters {
        reporter(ReporterType.PLAIN)
        reporter(ReporterType.CHECKSTYLE)
    }
}
```

Apply it from the root project so a new module inherits the configuration
rather than needing somebody to remember it:

```kotlin
subprojects {
    apply(plugin = "org.jlleitschuh.gradle.ktlint")
}
```

## 1.11 Wire the same formatter in Maven and bind the check goal to `verify`.

> Why? An unbound plugin is a plugin nobody runs. Binding the check goal to
> `verify` means `mvn verify` — and therefore every pipeline that already runs
> it — fails on unformatted source with no extra CI step to forget. The format
> goal stays bound to `process-sources` (or unbound entirely) so rewriting
> files is always an explicit act rather than a side effect of running tests.
> Two plugins can do this: `ktlint-maven-plugin`, whose `ktlint:check` goal
> already defaults to the `verify` phase and whose `ktlint:format` goal
> defaults to `process-sources`; or `spotless-maven-plugin` with a `<ktlint>`
> step inside `<kotlin>`, which is the right choice if the repository also
> formats Java or JSON and you want one plugin for all of it.

```xml
<!-- bad — declared but never bound; mvn verify passes on unformatted code -->
<plugin>
  <groupId>com.github.gantsign.maven</groupId>
  <artifactId>ktlint-maven-plugin</artifactId>
  <version>3.7.1</version>
</plugin>

<!-- good -->
<plugin>
  <groupId>com.github.gantsign.maven</groupId>
  <artifactId>ktlint-maven-plugin</artifactId>
  <version>3.7.1</version>
  <executions>
    <execution>
      <id>format-and-check</id>
      <goals>
        <goal>format</goal>
        <goal>check</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

```xml
<!-- good — the Spotless route, when the repo formats more than Kotlin -->
<plugin>
  <groupId>com.diffplug.spotless</groupId>
  <artifactId>spotless-maven-plugin</artifactId>
  <version>3.9.0</version>
  <configuration>
    <kotlin>
      <ktlint>
        <version>1.8.0</version>
      </ktlint>
      <licenseHeader>
        <content>/* (C)$YEAR Example Inc. */</content>
      </licenseHeader>
    </kotlin>
  </configuration>
  <executions>
    <execution>
      <goals>
        <goal>check</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

## 1.12 Choose `ktfmt` over ktlint only when you want a true reformatter — and then choose `KOTLINLANG` style.

> Why? The two tools are not the same kind of program. ktlint is a linter that
> also fixes: it preserves your line breaks unless a rule requires a change.
> `ktfmt` discards the existing layout entirely and re-emits one canonical
> rendering from the AST, the way `google-java-format` does. That is a real
> advantage — there is nothing left to have an opinion about — and a real cost:
> deliberate formatting that carried meaning is gone. If you pick it, pick
> `KOTLINLANG` style. `ktfmt`'s default is Google style with a **2-space**
> block indent; `--kotlinlang-style` "makes ktfmt use a block indent of 4 spaces
> instead of 2", which is the indent both Kotlin style guides mandate and the
> one every sample in this skill uses.
> **Suggestion — which formatter you adopt is a project decision.**

```kotlin
// bad — ktfmt at its default Google style, which is 2-space Kotlin
spotless {
    kotlin {
        ktfmt("0.64")
    }
}

// good — 4-space block indent, matching both style guides
spotless {
    kotlin {
        ktfmt("0.64").kotlinlangStyle()
    }
}
```

## 1.13 Never run two formatters over the same source set.

> Why? ktlint and ktfmt disagree about wrapping, and each will faithfully undo
> the other's output on every run. The file then oscillates: `ktlintFormat`
> makes it pass ktlint and fail ktfmt, `spotlessApply` reverses it, and the
> only stable resolution anybody finds is disabling one tool six months after
> both were wired in. The same failure appears in a subtler form when the
> Spotless `ktlint` step and the standalone ktlint Gradle plugin are both
> applied with different pinned ktlint versions.

```kotlin
// bad — two formatters, one source set; the file never converges
plugins {
    id("org.jlleitschuh.gradle.ktlint") version "14.2.0"
    id("com.diffplug.spotless") version "8.0.0"
}

spotless {
    kotlin {
        ktfmt("0.64").kotlinlangStyle()
    }
}

// good — pick one. If Spotless is the chain, let it run ktlint and drop the
// standalone plugin entirely.
plugins {
    id("com.diffplug.spotless") version "8.0.0"
}

spotless {
    kotlin {
        target("src/*/kotlin/**/*.kt")
        ktlint("1.8.0")
        licenseHeaderFile(rootProject.file("config/spotless/license-header.txt"))
    }
}
```

## 1.14 Turn on `-Xjsr305=strict`.

> Why? Kotlin's default handling of JSR-305 nullability annotations on Java
> declarations is `warn`: the annotation is reported but the declaration still
> arrives in Kotlin as a *platform type*, which the compiler will let you
> dereference without any null check at all. The
> [Java interop documentation](https://kotlinlang.org/docs/java-interop.html#jsr-305-support)
> is explicit that "only the `strict` mode affects the types in the annotated
> declarations as they are seen in Kotlin". Without the flag, a
> `@Nullable String` from a Java library is `String!` and
> `javaThing.name.length` compiles; with it, the same expression is a compile
> error until you handle the null. That is the whole point of the annotations,
> and it is off by default. Platform types themselves are
> [Chapter 6](06-null-safety.md) and [Chapter 28](28-java-interop.md).
> **Violation — enforced by the compiler once the flag is set.**

```kotlin
// bad — build.gradle.kts with no jsr305 setting; @Nullable is advisory
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
    }
}

// good
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}
```

```kotlin
// The difference at a call site, given a Java method annotated
// @Nullable String getName():

// bad — compiles under the default `warn`, throws at runtime when name is null
val length: Int = javaThing.name.length

// good — the only spelling that compiles under -Xjsr305=strict
val length: Int? = javaThing.name?.length
```

## 1.15 Turn on explicit API mode for every module you publish.

> Why? Kotlin's default visibility is `public` and its return types are
> inferred, so it is trivially easy to publish an API you never meant to. Two
> keystrokes — omitting `private` and omitting a return type — put an
> implementation detail and its inferred type into your compatibility contract,
> and the next refactor that narrows the type is a binary-incompatible change.
> [Explicit API mode](https://kotlinlang.org/docs/whatsnew14.html#explicit-api-mode-for-library-authors)
> makes both explicit, requiring "visibility modifiers ... for
> declarations if the default visibility exposes them to the public API" and
> "explicit type specifications ... for properties and functions that are
> exposed to the public API". Primary constructors, `data class` properties,
> getters and setters, and `override` members are excluded, and only production
> sources are analysed — so the cost on a real module is small.
> **Violation — enforced by the compiler in `strict` mode.**

```kotlin
// bad — build.gradle.kts for a published library, no explicit API mode
kotlin {
    jvmToolchain(21)
}

// good
kotlin {
    jvmToolchain(21)
    explicitApi() // or explicitApiWarning() while migrating
}
```

```kotlin
// bad — both of these are public, and the second's type is whatever the
// implementation happens to return today
fun parse(raw: String) = Invoice.from(raw)
val cache = mutableMapOf<UUID, Invoice>()

// good — visibility and type are both stated, so widening or narrowing
// either one is now a deliberate, reviewable change
public fun parse(raw: String): Invoice = Invoice.from(raw)
private val cache: MutableMap<UUID, Invoice> = mutableMapOf()
```

Use `explicitApiWarning()` while migrating an existing module and
`explicitApi()` once it is clean; the raw compiler form is
`-Xexplicit-api={strict|warning}`. Application modules that publish nothing do
not need it.

## 1.16 Treat compiler warnings as errors, and add the extra checks deliberately.

> Why? A warning in a build that emits four hundred of them is not a warning —
> it is scroll-back. Kotlin's warnings are unusually high-signal (unreachable
> code, unnecessary safe calls, deprecated APIs, unchecked casts), so the
> marginal cost of `allWarningsAsErrors` is low and the marginal benefit is
> that a deprecation is fixed the week it appears rather than the year the API
> is removed. Turn it on when the tree is already clean; turning it on with a
> backlog produces a build nobody can green and a `suppressWarnings` flag
> nobody can remove. `extraWarnings` enables additional declaration,
> expression, and type checks and is worth enabling separately, after
> `allWarningsAsErrors` has settled.
> **Violation — enforced by the compiler once `allWarningsAsErrors` is set.**

```kotlin
// bad — warnings accumulate until nobody reads the build log
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
    }
}

// worse — the backlog is hidden rather than paid down
kotlin {
    compilerOptions {
        suppressWarnings.set(true)
    }
}

// good
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
        allWarningsAsErrors.set(true)
        extraWarnings.set(true)
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}
```

## 1.17 Never use an experimental language feature without its opt-in flag and a comment saying why.

> Why? Kotlin 2.2 through 2.4 shipped several headline features that are still
> **Experimental** and require a compiler flag. An experimental feature can
> change shape or disappear between minor releases, so using one is a bet that
> needs to be visible in the build script rather than discovered by whoever
> hits the compile error after an upgrade. The flags, verified against the
> release notes, are `-Xcollection-literals` for
> [collection literals](https://kotlinlang.org/docs/whatsnew24.html)
> (Experimental in 2.4), `-Xexplicit-context-arguments` for explicit context
> arguments (Experimental in 2.4), and `-Xreturn-value-checker=check` or
> `=full` for the
> [unused return value checker](https://kotlinlang.org/docs/whatsnew23.html)
> (Experimental in 2.3). Collection literals carry two extra traps worth
> knowing before you opt in: they cannot construct a Java-defined collection
> type, and when the target type cannot be inferred they default to `List`.
> **Suggestion — the flag makes the feature compile; no tool judges whether the
> bet was justified.**

```kotlin
// bad — the feature is used, the flag is missing, and the build fails with a
// message that reads like a language bug rather than a configuration gap
val shapes: List<String> = ["triangle", "square", "circle"]

// good — build.gradle.kts, opt-in stated and justified in one place
kotlin {
    compilerOptions {
        // Experimental in Kotlin 2.4. Adopted for the DSL modules only;
        // revisit at 2.5 when the feature is expected to stabilise.
        freeCompilerArgs.addAll("-Xcollection-literals")
    }
}
```

```kotlin
// good — the return-value checker, opted in explicitly
kotlin {
    compilerOptions {
        // Experimental in Kotlin 2.3.
        freeCompilerArgs.addAll("-Xreturn-value-checker=check")
    }
}
```

## 1.18 Suppress a ktlint rule with `@Suppress("ktlint:<ruleset>:<rule-id>")`, never a `ktlint-disable` comment.

> Why? The `// ktlint-disable` comment directive stopped working in ktlint
> 0.50; the [FAQ](https://ktlint.github.io/ktlint/latest/faq/) states that "as
> of Ktlint 0.50, an error can only be suppressed using @Suppress or
> @SuppressWarnings annotations". The annotation is also strictly better: it
> attaches to a declaration, so it moves with the code and survives
> refactoring, whereas a comment pair attaches to line numbers — an edit
> between the disable and the enable silently widens its scope, and a lost
> re-enable disables the rule for the rest of the file. Import rules are the
> one case that needs the file-level form, because an import statement cannot
> carry an annotation. `@Suppress("ktlint")` silences every ktlint rule over
> its scope and should be treated the same way as `@Suppress("all")` in
> [Chapter 47, §47.16](47-ktlint-and-detekt.md): don't.
> **Violation — enforced by `standard:ktlint-suppression`, which flags the
> removed directive and can migrate it.**

```kotlin
// bad — deprecated directive, and the re-enable was lost in a merge
// ktlint-disable no-wildcard-imports
import java.util.*

// bad — blanket amnesty over a whole file
@file:Suppress("ktlint")

// good — one rule, file level because imports cannot be annotated, with the
// reason stated
@file:Suppress("ktlint:standard:no-wildcard-imports") // generated DSL, ~90 symbols

// good — one rule, smallest possible declaration scope
@Suppress("ktlint:standard:function-naming") // JUnit display name convention
fun `rejects a negative amount`() {
    // ...
}
```

## 1.19 Configure the IDE from the same `.editorconfig`, and format on save.

> Why? Any workflow that depends on a human remembering a command fails under
> deadline pressure, and the failure costs a reviewer's time rather than the
> author's. IntelliJ IDEA reads `.editorconfig` natively and there is an
> official ktlint plugin, so the setup is a checked-in file rather than
> tribal knowledge. The specific thing to check is that IntelliJ's Kotlin code
> style is set to follow `.editorconfig` rather than a stored IDE profile —
> ktlint's own documentation warns that `ktlint_official` "in some cases
> formats code in a way which is not accepted by the default code formatters in
> IntelliJ IDEA", and its advice for that case is to stop using the editor's
> own formatter rather than to try to reconcile the two. Do not go looking for
> a task that writes an IDE profile for you: ktlint removed the `applyToIDEA`
> functionality in 0.47, and `.editorconfig` is now the only supported way to
> keep the IDE and ktlint in step. `ktlintFormat` stays authoritative because
> it is the only path that runs ktlint itself.

```bash
# bad — every contributor picks their own IDE formatting profile
# (or none, and the pre-commit hook rewrites their file after the fact)

# good — the single source of truth is the checked-in .editorconfig from
# §1.4; point IntelliJ at it (Settings > Editor > Code Style > "Enable
# EditorConfig support"), and let the ktlint IDE plugin — not IntelliJ's own
# reformat action — be what runs on save

# good — install the local write path so formatting is never manual
./gradlew addKtlintFormatGitPreCommitHook
```

## 1.20 Introduce the formatter in one isolated commit and add that commit to `.git-blame-ignore-revs`.

> Why? Adopting a formatter on an existing codebase touches every file once.
> Doing it inside a feature branch buries the real change in thousands of
> whitespace lines and makes the review worthless. Doing it as its own commit
> and registering that commit's SHA in `.git-blame-ignore-revs` means
> `git blame` skips straight past it to the commit that actually wrote the
> line, so the reformat costs nothing in future archaeology.

```bash
# bad — reformat mixed into a behavioural change
git commit -am "add retry logic and format the repo"

# good
./gradlew ktlintFormat
git commit -am "chore: apply ktlint across the repository"
git rev-parse HEAD >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

When a single reformat genuinely cannot be merged — a long-lived release
branch, hundreds of open pull requests — the ktlint Gradle plugin's `baseline`
is the equivalent stopgap, and like every baseline it is temporary by
construction (see [Chapter 47, §47.14](47-ktlint-and-detekt.md)):

```kotlin
ktlint {
    baseline.set(file("config/ktlint/baseline.xml"))
}
```

## 1.21 Never spend a review comment on formatting.

> Why? Once the chain has run there is no formatting decision left to have an
> opinion about. "Add a blank line here", "align these", and "wrap this at 80"
> are not actionable against a formatted file — the author cannot comply
> without disabling the formatter. Every such comment displaces a comment about
> correctness or design, which is the only thing a human reviewer is actually
> better at than a tool. If a formatted line is genuinely hard to read, the fix
> is almost always a named intermediate value, and *that* is a design comment
> worth making.

```kotlin
// bad — reviewer asks for a hand-adjustment the next ktlintFormat undoes
// > "can you line the arguments up under the open paren?"
val order = orderFactory.create(customer, items, shipTo, PaymentMethod.CARD, promoCode)

// good — leave the formatting alone; name the thing that was hard to read
val payment = PaymentDetails(PaymentMethod.CARD, promoCode)
val order = orderFactory.create(customer, items, shipTo, payment)
```

## 1.22 Do not push semantic rules into ktlint, or formatting rules into detekt.

> Why? The two tools fail differently, and conflating them destroys the
> property that makes a formatter safe to block a build on. A ktlint failure is
> always fixable by running one command, so it can gate CI with zero human
> cost. A detekt failure may require a design change, so it needs review and
> occasionally a suppression. Running detekt's `MaxLineLength`,
> `TrailingWhitespace`, `NoTabs`, `NewLineAtEndOfFile`, or `ModifierOrder`
> alongside ktlint puts two tools in charge of one rule: they will eventually
> disagree, and the fix everyone reaches for is turning off the formatter,
> which is the wrong tool to lose. [Chapter 47](47-ktlint-and-detekt.md) sets
> out the full division of labour and the shipped configuration.

```yaml
# bad — config/detekt/detekt.yml re-litigating what ktlint already owns
style:
  MaxLineLength:
    active: true
    maxLineLength: 120
  TrailingWhitespace:
    active: true
  NoTabs:
    active: true
  NewLineAtEndOfFile:
    active: true

# good — detekt stays out of formatting entirely
style:
  MaxLineLength:
    active: false      # owned by standard:max-line-length
  TrailingWhitespace:
    active: false      # owned by standard:no-trailing-whitespaces
  NoTabs:
    active: false      # owned by standard:indent
  NewLineAtEndOfFile:
    active: false      # owned by standard:final-newline
  MagicNumber:
    active: true       # semantic — ktlint cannot see this
  ForbiddenComment:
    active: true
```
