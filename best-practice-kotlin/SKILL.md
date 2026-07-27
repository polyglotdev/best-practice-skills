---
name: best-practice-kotlin
description: Comprehensive, Airbnb-depth Kotlin best practices for Kotlin 2.4 on the JVM — null safety, data and value classes, sealed types, delegation, scope functions, generics variance, Java interop, plus a full coroutines deep-dive (structured concurrency, Flow, StateFlow, cancellation, testing) and a Kotlin-specific Spring Boot 3.x layer (compiler plugins, suspend controllers, suspend + @Transactional). Load when writing or reviewing any .kt or .kts file, when the user mentions Kotlin, the Android Kotlin style guide, Kotlin coding conventions, coroutines, Flow, ktlint, detekt, or Spring with Kotlin, or when the user asks "is this idiomatic Kotlin?". Enforces the shipped ktlint and detekt configuration.
---

# best-practice-kotlin

This skill codifies modern Kotlin best practices for **Kotlin 2.4** on the
JVM. It is modeled on the depth and structure of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) —
numbered rules per chapter, `> Why?` rationale, and `// bad` / `// good`
examples for every rule.

The rules trace to five upstream sources, in this precedence order:

1. **[Android Kotlin style guide](https://developer.android.com/kotlin/style-guide)** —
   the normative source for
   [formatting](https://developer.android.com/kotlin/style-guide#formatting),
   [naming](https://developer.android.com/kotlin/style-guide#naming),
   [source file structure](https://developer.android.com/kotlin/style-guide#source_files),
   and [documentation](https://developer.android.com/kotlin/style-guide#documentation).
   Despite the name, everything it says about the language itself applies to
   server-side Kotlin unchanged.
2. **[Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)** —
   JetBrains' own guide, which goes further than Android's on
   [idiomatic language use](https://kotlinlang.org/docs/coding-conventions.html#idiomatic-use-of-language-features),
   [scope functions](https://kotlinlang.org/docs/coding-conventions.html#scope-functions-apply-with-run-also-let),
   and [library API design](https://kotlinlang.org/docs/coding-conventions.html#coding-conventions-for-libraries).
3. **The [Kotlin language documentation](https://kotlinlang.org/docs/home.html)
   and [standard library API reference](https://kotlinlang.org/api/core/)** —
   for every language and library feature the style guides predate.
4. **The [kotlinx.coroutines documentation](https://kotlinlang.org/docs/coroutines-guide.html)** —
   for the coroutines deep-dive in chapters 33 to 40.
5. **[Spring Framework](https://docs.spring.io/spring-framework/reference/languages/kotlin.html)
   and [Spring Boot](https://docs.spring.io/spring-boot/index.html) Kotlin
   documentation** — for the framework layer in chapters 41 to 46 only.

All formatting concerns — indentation, braces, line wrapping, blank lines,
horizontal whitespace, import ordering — are owned by the `ktlint` (or
`ktfmt`) chain and are never re-litigated in prose. Chapter 1 documents the
tool chain and every subsequent chapter assumes the code has been formatted.
This is the same delegation `best-practice-go` makes to `gofmt`,
`best-practice-java` makes to `google-java-format`, and `best-practice-js`
makes to Prettier.

**Indentation is four spaces.** The Android Kotlin style guide states that
"each time a new block or block-like construct is opened, the indent increases
by four spaces," and ktlint defaults to the same. Every code sample in this
skill uses four. Note this differs from the two-space default used elsewhere
in this repo, and from Google Java Style's +2 for Java — it is the upstream
Kotlin rule and it wins here.

Every rule that maps to an enabled rule in the shipped `.editorconfig`
(ktlint) or `config/detekt/detekt.yml` carries an
**`> Enforced by: <tool/rule-id>`** callout so you can trace each rule from
the guide to the CI check that catches its violations. Rules that no tool can
mechanically verify are labeled **Suggestion**, not **Violation**.

## Language version and experimental features

The floor is **Kotlin 2.4** with the **K2** compiler. Everything stable
through 2.4 is treated as default idiom.

Kotlin 2.4 **promoted several 2.2/2.3 Experimental features to Stable**. Per
the [2.4 release notes](https://kotlinlang.org/docs/whatsnew24.html), these
are now Stable and need no opt-in flag:

| Feature | Introduced | Status on 2.4 |
|---|---|---|
| Context parameters | 2.2 | **Stable** (except context arguments and callable references) |
| Explicit backing fields | 2.3 | **Stable** |
| `@all` meta-target for properties | 2.2 | **Stable** |
| New defaulting rules for use-site annotation targets | 2.2 | **Stable** |

These remain **Experimental** on 2.4 and require an opt-in compiler flag.
This skill never presents them as default idiom, and every rule that touches
one says so explicitly with the flag required:

| Feature | Version | Status | Opt-in |
|---|---|---|---|
| Collection literals (`[...]`) | 2.4 | Experimental | opt-in required |
| Explicit context arguments | 2.4 | Experimental | `-Xexplicit-context-arguments` |
| Unused return value checker | 2.3 | Experimental | `-Xreturn-value-checker=check` |

Treat an unflagged use of anything in the second table as a finding, the same
way `best-practice-java` treats a Java 21 preview API. Note the split inside
context parameters specifically: the feature is Stable, but *explicit context
arguments* and *callable references* to context-parameter declarations are
not.

## When to use

- Writing new `.kt`/`.kts` files or reviewing existing Kotlin code.
- Answering "is this idiomatic?" or "does this follow the style guide?"
  for Kotlin.
- Deciding between a `data class`, a `value class`, and a plain class; or
  between a `sealed interface` and an `enum`.
- Reviewing anything involving `suspend`, `Flow`, `StateFlow`, coroutine
  scopes, or cancellation (chapters 33 to 40).
- Reviewing a Spring Boot service written in Kotlin, especially
  `suspend` controllers and the `suspend` + `@Transactional` interaction
  (chapters 41 to 46).
- Setting up or auditing ktlint / detekt for a new Kotlin project
  (chapter 47).
- Preparing a Kotlin change for code review and wanting pre-review feedback.

## Scope

- Language-level Kotlin through **2.4**: declarations, null safety, types,
  functions, lambdas, classes, data and value classes, sealed types, objects,
  enums, delegation, properties, generics and variance, operators,
  annotations.
- Android Kotlin style guide and Kotlin coding conventions in full.
- Idiom: scope functions, collections and sequences, strings, control flow,
  equality, immutability.
- Error handling: exceptions, `Result`, `runCatching`, and why Kotlin has no
  checked exceptions.
- **Java interop**: platform types, `@JvmStatic` / `@JvmOverloads` /
  `@JvmField` / `@JvmName`, SAM conversion, nullability annotations,
  and calling Kotlin from Java.
- **Coroutines, in depth**: structured concurrency, scopes and jobs,
  dispatchers, cancellation and timeouts, `Flow`, `StateFlow`/`SharedFlow`,
  channels, `select`, coroutine testing, and the standard anti-patterns.
- **Spring Boot 3.x, Kotlin delta only**: the compiler plugins
  (`all-open`, `no-arg`, `kotlin-spring`, `kotlin-jpa`), constructor
  injection with `val`, `data class` configuration properties, `suspend`
  controllers and coroutine web layers, `suspend` with `@Transactional`,
  and MockK-based testing.
- Tooling: `ktlint`, `ktfmt`, `detekt`, and the Kotlin compiler's own
  warning and explicit-API modes.

## Non-goals

- **Formatting.** `ktlint` owns indentation, braces, wrapping, blank lines,
  and import order. This skill states the chain in chapter 1 and moves on.
- **Restating the Java Spring rules.** Chapters 41 to 46 cover only what is
  genuinely *different* in Kotlin. For the shared Spring rules — bean
  scoping, `@ConfigurationProperties` design, transaction propagation, test
  slices, context caching — see `best-practice-java` chapters 32 to 37.
- **Micronaut, Arrow, and Exposed.** Those live in the separate
  `kotlin-best-practices` skill. This one is Spring.
- **Kotlin Multiplatform, Kotlin/Native, Kotlin/JS, and Compose.** JVM only.
- **Android framework idioms.** The Android *style guide* is a source here;
  Android *framework* patterns (Activity/Fragment lifecycle, ViewModel,
  Jetpack) are not.
- **Build tooling** beyond the static-analysis configuration in chapter 47.

---

## Chapters

Each chapter is a self-contained reference file with numbered rules,
`> Why?` rationale, `// bad` / `// good` code, and `> Enforced by:`
tool callouts. Files live under `references/`.

### Part I — Style foundation

| # | Chapter | File |
|---|---------|------|
| 1 | Formatting & Tooling | [`references/01-formatting-and-tooling.md`](references/01-formatting-and-tooling.md) |
| 2 | Source Files & Structure | [`references/02-source-files-and-structure.md`](references/02-source-files-and-structure.md) |
| 3 | Naming | [`references/03-naming.md`](references/03-naming.md) |
| 4 | KDoc | [`references/04-kdoc.md`](references/04-kdoc.md) |

### Part II — Language core

| # | Chapter | File |
|---|---------|------|
| 5 | Declarations & Visibility | [`references/05-declarations-and-visibility.md`](references/05-declarations-and-visibility.md) |
| 6 | Null Safety | [`references/06-null-safety.md`](references/06-null-safety.md) |
| 7 | Types & Type Aliases | [`references/07-types-and-type-aliases.md`](references/07-types-and-type-aliases.md) |
| 8 | Functions | [`references/08-functions.md`](references/08-functions.md) |
| 9 | Lambdas & Higher-Order Functions | [`references/09-lambdas-and-higher-order-functions.md`](references/09-lambdas-and-higher-order-functions.md) |
| 10 | Classes & Interfaces | [`references/10-classes-and-interfaces.md`](references/10-classes-and-interfaces.md) |
| 11 | Data Classes | [`references/11-data-classes.md`](references/11-data-classes.md) |
| 12 | Value Classes | [`references/12-value-classes.md`](references/12-value-classes.md) |
| 13 | Sealed Types | [`references/13-sealed-types.md`](references/13-sealed-types.md) |
| 14 | Objects, Companions & Factories | [`references/14-objects-and-companions.md`](references/14-objects-and-companions.md) |
| 15 | Enums | [`references/15-enums.md`](references/15-enums.md) |
| 16 | Delegation | [`references/16-delegation.md`](references/16-delegation.md) |
| 17 | Properties & Backing Fields | [`references/17-properties-and-backing-fields.md`](references/17-properties-and-backing-fields.md) |
| 18 | Generics & Variance | [`references/18-generics-and-variance.md`](references/18-generics-and-variance.md) |
| 19 | Scope Functions | [`references/19-scope-functions.md`](references/19-scope-functions.md) |
| 20 | Collections & Sequences | [`references/20-collections-and-sequences.md`](references/20-collections-and-sequences.md) |
| 21 | Strings | [`references/21-strings.md`](references/21-strings.md) |
| 22 | Control Flow & `when` | [`references/22-control-flow-and-when.md`](references/22-control-flow-and-when.md) |
| 23 | Equality & Ordering | [`references/23-equality-and-ordering.md`](references/23-equality-and-ordering.md) |
| 24 | Exceptions & `Result` | [`references/24-exceptions-and-result.md`](references/24-exceptions-and-result.md) |
| 25 | Immutability | [`references/25-immutability.md`](references/25-immutability.md) |
| 26 | Operators & Conventions | [`references/26-operators-and-conventions.md`](references/26-operators-and-conventions.md) |
| 27 | Annotations & Use-Site Targets | [`references/27-annotations-and-use-site-targets.md`](references/27-annotations-and-use-site-targets.md) |
| 28 | Java Interop | [`references/28-java-interop.md`](references/28-java-interop.md) |
| 29 | Context Parameters | [`references/29-context-parameters.md`](references/29-context-parameters.md) |
| 30 | Dates & Times | [`references/30-dates-and-times.md`](references/30-dates-and-times.md) |
| 31 | Logging | [`references/31-logging.md`](references/31-logging.md) |
| 32 | Testing | [`references/32-testing.md`](references/32-testing.md) |

### Part III — Coroutines

| # | Chapter | File |
|---|---------|------|
| 33 | Coroutine Fundamentals | [`references/33-coroutine-fundamentals.md`](references/33-coroutine-fundamentals.md) |
| 34 | Dispatchers & Coroutine Context | [`references/34-dispatchers-and-context.md`](references/34-dispatchers-and-context.md) |
| 35 | Cancellation & Timeouts | [`references/35-cancellation-and-timeouts.md`](references/35-cancellation-and-timeouts.md) |
| 36 | `Flow` | [`references/36-flow.md`](references/36-flow.md) |
| 37 | `StateFlow` & `SharedFlow` | [`references/37-stateflow-and-sharedflow.md`](references/37-stateflow-and-sharedflow.md) |
| 38 | Channels & `select` | [`references/38-channels-and-select.md`](references/38-channels-and-select.md) |
| 39 | Coroutine Testing | [`references/39-coroutine-testing.md`](references/39-coroutine-testing.md) |
| 40 | Coroutine Anti-patterns | [`references/40-coroutine-anti-patterns.md`](references/40-coroutine-anti-patterns.md) |

### Part IV — Spring Boot 3.x (Kotlin delta)

| # | Chapter | File |
|---|---------|------|
| 41 | Spring: Kotlin Setup & Compiler Plugins | [`references/41-spring-kotlin-setup.md`](references/41-spring-kotlin-setup.md) |
| 42 | Spring: Beans & Injection in Kotlin | [`references/42-spring-beans-and-injection.md`](references/42-spring-beans-and-injection.md) |
| 43 | Spring: Configuration Properties | [`references/43-spring-configuration-properties.md`](references/43-spring-configuration-properties.md) |
| 44 | Spring: Web Layer & Coroutines | [`references/44-spring-web-and-coroutines.md`](references/44-spring-web-and-coroutines.md) |
| 45 | Spring: Data & Transactions with Coroutines | [`references/45-spring-data-and-transactions.md`](references/45-spring-data-and-transactions.md) |
| 46 | Spring: Testing in Kotlin | [`references/46-spring-testing-kotlin.md`](references/46-spring-testing-kotlin.md) |

### Part V — Tooling

| # | Chapter | File |
|---|---------|------|
| 47 | ktlint & detekt Configuration | [`references/47-ktlint-and-detekt.md`](references/47-ktlint-and-detekt.md) |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells
   Claude/Cursor/Windsurf when to load `best-practice-kotlin`. When it
   loads, this index is what the agent reads first.
2. **Targeted reads.** For one specific area (say, scope functions or
   cancellation), the agent opens only the matching chapter under
   `references/` — this keeps the context window small.
3. **Full review.** For a comprehensive audit, the agent reads every
   chapter. Each is exhaustive on its own topic.
4. **Layering.** Chapters 1 to 32 apply to every Kotlin codebase.
   Chapters 33 to 40 apply wherever `suspend` or `Flow` appears.
   Chapters 41 to 46 apply only to Spring Boot 3.x, and assume
   `best-practice-java` chapters 32 to 37 for the framework rules that are
   not Kotlin-specific.
5. **Sibling skills.** For Micronaut, Arrow `Either`, and Exposed ORM
   patterns, use `kotlin-best-practices` instead. For the Java side of a
   mixed codebase, use `best-practice-java`.
6. **Tool config.** The recommended ktlint `.editorconfig` block and
   `config/detekt/detekt.yml` ship in this repo's root and are documented
   in chapter 47.

## Self-check

Before treating any Kotlin code you write or review as finished, verify:

- The file is clean under `./gradlew ktlintCheck detekt`. If not, run
  `ktlintFormat` first — nothing else matters if formatting is off.
- **No `!!` anywhere.** Every nullable access uses `?.`, `?:`, a null
  check that enables smart casting, or `requireNotNull`/`checkNotNull`
  with a message (chapter 6).
- No platform type from Java crosses into Kotlin code without being
  given an explicit nullable or non-null type at the boundary
  (chapters 6, 28).
- `lateinit` is used only where a non-null value is genuinely assigned
  before first read by a framework, never as a way to dodge nullability
  (chapter 6).
- Every closed hierarchy is a `sealed interface` or `sealed class`, and
  every `when` over it is exhaustive **without** an `else`, so adding a
  subtype becomes a compile error (chapters 13, 22).
- `data class` is used only for genuine value carriers. No `data class`
  with mutable `var` components used as a map key or in a `Set`
  (chapters 11, 23).
- Scope functions are chosen by their contract, not by habit: `let` for
  nullable transformation, `run` for a block returning a result, `apply`
  for configuration returning the receiver, `also` for side effects,
  `with` for a non-null receiver. No nested scope functions that shadow
  `it` (chapter 19).
- Collection types at API boundaries are the read-only interfaces
  (`List`, `Set`, `Map`), never the `Mutable*` variants, and never a
  concrete implementation type (chapters 20, 25).
- No experimental feature is used without its opt-in flag and a comment
  justifying it: context parameters, explicit backing fields, collection
  literals, explicit context arguments, the return-value checker
  (chapters 20, 29).
- **Coroutines:** no `GlobalScope`. No `runBlocking` outside `main` or a
  test. Every `launch` has an owning scope with a defined lifetime. Every
  `suspend` function is main-safe or documents its dispatcher requirement.
  `withContext(Dispatchers.IO)` wraps every blocking call
  (chapters 33, 34, 40).
- **Cancellation:** no `catch (e: Exception)` that swallows
  `CancellationException`. Every long loop checks `ensureActive()` or uses
  a cancellable suspend point. Cleanup uses `NonCancellable` only where
  genuinely required (chapter 35).
- **Flow:** every `Flow` is cold unless deliberately shared. `StateFlow`
  for state, `SharedFlow` for events. No `collect` in a scope that
  outlives the consumer (chapters 36, 37).
- **Spring only:** every bean uses constructor injection with `val`. The
  `kotlin-spring` and `kotlin-jpa` plugins are applied rather than marking
  classes `open` by hand. No `suspend` function carries `@Transactional`
  without understanding that the proxy does not span the suspension
  (chapters 41, 42, 45).
- The code compiles cleanly under the project's ktlint and detekt
  configuration (chapter 47). No new `@Suppress` or `ktlint-disable`
  without a scoped rule id and an explanation.
