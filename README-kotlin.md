# best-practice-kotlin

An exhaustive, Airbnb-depth **Agent Skill** for writing and reviewing Kotlin
2.4 on the JVM, including a coroutines deep-dive and a Kotlin-specific Spring
Boot 3.x layer.

**851 numbered rules across 47 chapters, 31,302 lines.** Every rule is
justified with a `> Why?`, shown with `// bad` / `// good` code, and where a
tool can catch it, labeled `> Enforced by: <tool/rule-id>`.

## Upstream sources, in precedence order

1. **[Android Kotlin style guide](https://developer.android.com/kotlin/style-guide)** —
   normative for
   [formatting](https://developer.android.com/kotlin/style-guide#formatting),
   [naming](https://developer.android.com/kotlin/style-guide#naming),
   [source files](https://developer.android.com/kotlin/style-guide#source_files),
   and [documentation](https://developer.android.com/kotlin/style-guide#documentation).
   Despite the name, everything it says about the language applies to
   server-side Kotlin unchanged.
2. **[Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)** —
   JetBrains' guide, which goes further on
   [idiomatic language use](https://kotlinlang.org/docs/coding-conventions.html#idiomatic-use-of-language-features)
   and [scope functions](https://kotlinlang.org/docs/coding-conventions.html#scope-functions-apply-with-run-also-let).
3. **[Kotlin language docs](https://kotlinlang.org/docs/home.html)** and the
   [stdlib API reference](https://kotlinlang.org/api/core/).
4. **[kotlinx.coroutines docs](https://kotlinlang.org/docs/coroutines-guide.html)** —
   chapters 33 to 40.
5. **[Spring Kotlin docs](https://docs.spring.io/spring-framework/reference/languages/kotlin.html)** —
   chapters 41 to 46 only.

Every style-guide link resolves against the live pages; anchors were harvested
from raw HTML into [`docs/reference-data/`](docs/reference-data/) rather than
inferred from section titles.

## Indentation is four spaces

The Android Kotlin style guide states that "each time a new block or
block-like construct is opened, the indent increases by **four spaces**," and
ktlint defaults to the same. Every sample in this skill uses four.

This deliberately differs from the 2-space default used elsewhere in this repo
and from Google Java Style's +2 for Java. It is the upstream Kotlin rule and
it wins here. `.editorconfig` carries a `[*.{kt,kts}]` block so an editor does
not fight ktlint before it runs.

## Kotlin 2.4: what is Stable and what is not

The floor is **Kotlin 2.4** with the **K2** compiler. Getting this split wrong
is the single easiest way to write a plausible, wrong Kotlin rule, so it is
stated explicitly in SKILL.md and enforced by the verify pass.

Kotlin 2.4 **promoted these from Experimental to Stable**, so they need no
opt-in flag:

| Feature | Introduced | Status on 2.4 |
|---|---|---|
| Context parameters | 2.2 | **Stable**, except context arguments and callable references |
| Explicit backing fields | 2.3 | **Stable** |
| `@all` meta-target for properties | 2.2 | **Stable** |
| New defaulting rules for use-site annotation targets | 2.2 | **Stable** |

These are still **Experimental** on 2.4 and require an opt-in flag. The skill
never presents them as default idiom:

| Feature | Version | Opt-in |
|---|---|---|
| Collection literals (`[...]`) | 2.4 | opt-in required |
| Explicit context arguments | 2.4 | `-Xexplicit-context-arguments` |
| Unused return value checker | 2.3 | `-Xreturn-value-checker=check` |

An unflagged use of anything in the second table is a finding, the same way
`best-practice-java` treats a Java 21 preview API.

## Chapters

### Part I — Style foundation

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 1 | Formatting & Tooling | 22 | 889 |
| 2 | Source Files & Structure | 20 | 884 |
| 3 | Naming | 21 | 753 |
| 4 | KDoc | 21 | 769 |

### Part II — Language core

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 5 | Declarations & Visibility | 17 | 616 |
| 6 | Null Safety | 19 | 689 |
| 7 | Types & Type Aliases | 18 | 625 |
| 8 | Functions | 18 | 732 |
| 9 | Lambdas & Higher-Order Functions | 20 | 722 |
| 10 | Classes & Interfaces | 17 | 696 |
| 11 | Data Classes | 18 | 660 |
| 12 | Value Classes | 17 | 574 |
| 13 | Sealed Types | 16 | 609 |
| 14 | Objects, Companions & Factories | 17 | 655 |
| 15 | Enums | 17 | 626 |
| 16 | Delegation | 16 | 610 |
| 17 | Properties & Backing Fields | 15 | 649 |
| 18 | Generics & Variance | 18 | 591 |
| 19 | Scope Functions | 17 | 489 |
| 20 | Collections & Sequences | 19 | 583 |
| 21 | Strings | 20 | 583 |
| 22 | Control Flow & `when` | 21 | 755 |
| 23 | Equality & Ordering | 20 | 617 |
| 24 | Exceptions & `Result` | 22 | 768 |
| 25 | Immutability | 18 | 670 |
| 26 | Operators & Conventions | 19 | 688 |
| 27 | Annotations & Use-Site Targets | 18 | 655 |
| 28 | Java Interop | 19 | 692 |
| 29 | Context Parameters | 15 | 511 |
| 30 | Dates & Times | 19 | 549 |
| 31 | Logging | 17 | 546 |
| 32 | Testing | 19 | 762 |

### Part III — Coroutines

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 33 | Coroutine Fundamentals | 16 | 481 |
| 34 | Dispatchers & Coroutine Context | 15 | 458 |
| 35 | Cancellation & Timeouts | 15 | 511 |
| 36 | `Flow` | 20 | 642 |
| 37 | `StateFlow` & `SharedFlow` | 18 | 590 |
| 38 | Channels & `select` | 18 | 609 |
| 39 | Coroutine Testing | 19 | 688 |
| 40 | Coroutine Anti-patterns | 20 | 680 |

### Part IV — Spring Boot 3.x (Kotlin delta)

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 41 | Spring: Kotlin Setup & Compiler Plugins | 15 | 700 |
| 42 | Spring: Beans & Injection in Kotlin | 16 | 729 |
| 43 | Spring: Configuration Properties | 17 | 828 |
| 44 | Spring: Web Layer & Coroutines | 17 | 620 |
| 45 | Spring: Data & Transactions with Coroutines | 17 | 673 |
| 46 | Spring: Testing in Kotlin | 16 | 662 |

### Part V — Tooling

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 47 | ktlint & detekt Configuration | 22 | 1214 |

Chapters 1 to 32 apply to every Kotlin codebase. Chapters 33 to 40 apply
wherever `suspend` or `Flow` appears. Chapters 41 to 46 are a **delta**: they
cover only what is genuinely different in Kotlin and cross-reference
`best-practice-java` chapters 32 to 37 for the shared Spring rules rather than
restating them.

## Division of labour between tools

| Tool | Owns |
|---|---|
| **ktlint** (or ktfmt) | Formatting: 4-space indent, 100-column limit, brace style, blank lines, wrapping, import order, trailing commas. |
| **detekt** | Semantic smells, complexity, and correctness. |
| **kotlinc** | Nullability, exhaustiveness, unreachable code, explicit API mode. |

detekt's own `formatting` ruleset is a ktlint wrapper and is deliberately
**not** enabled: running ktlint through two front ends produces duplicate
findings that disagree about severity.

## The shipped detekt configuration

[`config/detekt/detekt.yml`](config/detekt/detekt.yml) is an **override**
config, applied with `buildUponDefaultConfig = true`. 107 rules, all verified
against detekt's catalogue and correctly placed by ruleset.

Highlights, chosen because each one mechanically backs a stated rule:

- `UnsafeCallOnNullableType` and `MapGetWithNotNullAssertionOperator` make the
  `!!` ban enforceable rather than aspirational (chapter 6).
- `HasPlatformType` catches a Java platform type escaping into Kotlin without
  an explicit type (chapters 6 and 28).
- `ElseCaseInsteadOfExhaustiveWhen` enforces the sealed-exhaustiveness rule: a
  new subtype must become a compile error, and an `else` swallows it
  (chapters 13, 15, 22).
- All nine coroutine rules are on, including `SuspendFunSwallowedCancellation`,
  which is precisely the "never swallow `CancellationException`" rule
  (chapters 24, 35, 40).
- `NestedScopeFunctions` and `MultilineLambdaItParameter` catch the two
  headline scope-function anti-patterns (chapter 19).

Several rules need **type resolution** and are silently inert without it. Run
`detektMain` / `detektTest`, which have the compile classpath, not the plain
`detekt` task. The config marks which rules this matters for.

### detekt 1.23.8 versus the 2.0 alpha

Latest **stable** detekt is **1.23.8**. detekt 2.0 exists only as an alpha
(`v2.0.0-alpha.5`), but **detekt.dev documents 2.x**. That gap is real and
visible in the corpus: seven rules the docs describe
(`AbstractClassCanBeConcreteClass`, `ErrorUsageWithThrowable`, `MayBeConstant`,
`MissingUseCall`, `RangeUntilInsteadOfRangeTo`, `RedundantVisibilityModifier`,
`UnnecessaryFullyQualifiedName`) are absent from the 1.23.8 default config and
cannot be enabled there. Chapters citing them are labeled **Suggestion** with
a re-check-on-upgrade note rather than claiming enforcement that would not
happen.

Some rule *options* also differ between the lines, for example
`TooManyFunctions.thresholdInFiles` (1.23) versus `allowedFunctionsPerFile`
(2.x). Chapter 47 notes both spellings.

## Install

```bash
npx skills add <your-github-user>/best-practice-skills --skill best-practice-kotlin -g -y
```

Project-scoped: copy `best-practice-kotlin/` into `.claude/skills/`, drop
`config/detekt/` at the repo root, and merge the `[*.{kt,kts}]` block from
`.editorconfig`.

## Invocation

```text
/best-practice-kotlin  replace every !! in this file and tell me which ones hid a real design problem
/best-practice-kotlin  this when over a sealed interface has an else — should it?
/best-practice-kotlin  review this suspend function for cancellation correctness
/best-practice-kotlin  should this be a data class, a value class, or neither?
/best-practice-kotlin  audit this @Transactional suspend function
/best-practice-kotlin  this chain of four scope functions is unreadable — fix it
```

## Design notes

- **Two Kotlin skills exist and they are not interchangeable.** This one is
  language + **Spring**. The separate global `kotlin-best-practices` skill is
  Micronaut, Arrow `Either`, and Exposed ORM. Load whichever matches the stack.
- **The Spring chapters are a delta by design.** Bean scoping, transaction
  propagation, test slices, and context caching are language-neutral and live
  in `best-practice-java`. What lives here is what actually differs: the
  `all-open` / `no-arg` compiler plugins, `val` constructor injection,
  `data class` configuration properties, validation annotations needing
  `@field:` targets, `suspend` controllers, and the `suspend` +
  `@Transactional` thread-binding trap.
- **Verified, not remembered.** 155 defects were found and fixed by an
  adversarial verify pass (49 fabricated citations, 39 contract drifts,
  35 code errors, 14 fake rule ids, 10 hallucinated APIs, 8 experimental-vs-
  stable errors), then a mechanical reconciliation fixed 58 enforcement
  callouts. Final state: 0 broken anchors, 0 fabricated rule names,
  0 false enforcement claims.

## Known gaps

- **Kotlin Multiplatform, Kotlin/Native, Kotlin/JS, Compose.** JVM only.
- **Micronaut, Arrow, Exposed.** See `kotlin-best-practices`.
- **Android framework patterns.** The Android *style guide* is a source; the
  Android *framework* (lifecycle, ViewModel, Jetpack) is not.
- **Build tooling** beyond the static-analysis configuration in chapter 47.
