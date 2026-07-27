<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 47. ktlint & detekt Configuration

Every `> Enforced by:` and **Violation** callout in this skill points at a real
check in a real tool. This chapter is the configuration those callouts refer
to: **[ktlint](https://ktlint.github.io/ktlint/latest/)** for formatting,
**[detekt](https://detekt.dev/)** for semantic smells and complexity, and the
**Kotlin compiler itself** for nullability, warnings, and API surface. Three
tools, three disjoint concerns, one build.

The division of labour is the whole design, and it is worth stating before any
configuration:

| Tool | Owns | Sees | Fix cost |
|---|---|---|---|
| ktlint | Indentation, wrapping, column limit, blank lines, import order, semicolons, trailing commas | The PSI tree of one file | One command |
| Kotlin compiler | Nullability, platform types, exhaustiveness, deprecation, unreachable code, public API surface | Full type information | Code change |
| detekt (no type resolution) | Naming, file structure, complexity, empty blocks, obvious smells | The PSI tree of one file | Small edit to a design change |
| detekt (with type resolution) | `!!` on a nullable receiver, platform types in public APIs, coroutine misuse, impossible casts | PSI plus resolved types | Design change |

The ordering is by fix cost, not by importance. A ktlint failure is always
repairable by running `ktlintFormat`, so it can block a build with zero human
judgement involved. A detekt `LongMethod` finding may mean the method is wrong.
Conflating the two produces a build that fails for reasons of wildly different
weight, and the predictable response is to turn something off.

Formatting itself is [Chapter 1](01-formatting-and-tooling.md) and is not
repeated here — that chapter also covers `-Xjsr305=strict`, `explicitApi()`,
and `allWarningsAsErrors`, which are the compiler's third of the table above.
The rules each detekt check backs are spread across Chapters 2 to 46; the `!!`
ban that `UnsafeCallOnNullableType` implements is
[Chapter 6](06-null-safety.md).

**Tool alignment:** this chapter *is* the tool alignment. The shipped ktlint
configuration lives in `.editorconfig` at the repository root and the shipped
detekt ruleset at `config/detekt/detekt.yml`.

## 47.1 Run all three tools, and give each exactly one concern.

> Why? A single "linter" that owns everything has one severity, one suppression
> mechanism, and one failure mode, so the cheap failures and the expensive ones
> become indistinguishable. Three tools with disjoint scopes means the pipeline
> can tell a developer *which kind* of problem they have before they read a
> line of output, and each tool can be tuned, suppressed, or upgraded without
> touching the others. It also means each finding is reported exactly once —
> see §47.2 and §47.3 for the two ways that property gets destroyed.

```kotlin
// bad — detekt asked to do all three jobs, badly: it re-checks formatting,
// runs without type resolution so it cannot see nullability, and nothing
// tells the compiler to be strict about anything
plugins {
    kotlin("jvm") version "2.4.0"
    id("dev.detekt") version "2.0.0-alpha.5"
}

// good — build.gradle.kts: three plugins, three scopes
plugins {
    kotlin("jvm") version "2.4.0"
    id("org.jlleitschuh.gradle.ktlint") version "14.2.0"
    id("dev.detekt") version "2.0.0-alpha.5"
}

kotlin {
    jvmToolchain(21)
    compilerOptions {
        allWarningsAsErrors.set(true)
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

ktlint {
    version.set("1.8.0")
    ignoreFailures.set(false)
}

detekt {
    buildUponDefaultConfig = true
    config.setFrom(rootProject.file("config/detekt/detekt.yml"))
    ignoreFailures = false
}
```

## 47.2 Never encode a formatting rule in detekt.

> Why? detekt ships a handful of rules that look like formatting because they
> were written before ktlint became the default Kotlin formatter:
> `MaxLineLength`, `TrailingWhitespace`, `NoTabs`, `NewLineAtEndOfFile`,
> `SpacingAfterPackageAndImports`, `ModifierOrder`, `WildcardImport`,
> `UnusedImport`, `BracesOnIfStatements`. Every one of them duplicates a ktlint
> standard rule, and duplication is not merely redundant — when the two
> definitions diverge slightly, satisfying one violates the other, and the only
> way out is disabling a tool. The tool that gets disabled is usually the
> formatter, which is the wrong one to lose.
> **Violation — enforced by the shipped `detekt.yml` below, which sets each of
> these to `active: false` with a comment naming the ktlint rule that owns it.**

```yaml
# bad — config/detekt/detekt.yml re-litigating what ktlint already owns,
# at a different column limit
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
  ModifierOrder:
    active: true
  WildcardImport:
    active: true

# good — each one turned off, with the owner named
style:
  MaxLineLength:
    active: false                 # standard:max-line-length
  TrailingWhitespace:
    active: false                 # standard:no-trailing-whitespaces
  NoTabs:
    active: false                 # standard:indent
  NewLineAtEndOfFile:
    active: false                 # standard:final-newline
  SpacingAfterPackageAndImports:
    active: false                 # ktlint owns blank lines around the imports
  ModifierOrder:
    active: false                 # standard:modifier-order
  WildcardImport:
    active: false                 # standard:no-wildcard-imports
  UnusedImport:
    active: false                 # standard:no-unused-imports
```

## 47.3 Never ask ktlint to make a semantic judgement.

> Why? ktlint sees one file's PSI tree and no types at all. It cannot know that
> a receiver is nullable, that a `when` is already exhaustive, that a caught
> exception is being swallowed, or that `Thread.sleep` sits inside a `suspend`
> function — every one of those needs the resolved type of something. Custom
> ktlint rule sets that try to express a semantic rule end up matching on
> identifier text, which produces false positives nobody can suppress cleanly
> and false negatives nobody notices. If you find yourself writing a ktlint
> rule that inspects what a name *means* rather than where it *sits*, the rule
> belongs in detekt with type resolution on.

```kotlin
// A custom ktlint rule matching on the text `Thread.sleep` cannot tell these
// two apart — the first is a bug, the second is fine.
suspend fun poll() {
    Thread.sleep(1_000)          // blocks the dispatcher thread
}

fun blockingPoll() {
    Thread.sleep(1_000)          // a plain blocking function; legitimate
}
```

```yaml
# good — detekt with type resolution knows which call sites are suspending
coroutines:
  SleepInsteadOfDelay:
    active: true
```

## 47.4 Build your ruleset on top of detekt's default, and check the file in.

> Why? detekt's default configuration is a curated set with sensible
> activations — most `potential-bugs` and `exceptions` rules are on,
> most `comments` rules are off — and reproducing it by hand means
> re-deriving several hundred decisions and getting some of them wrong.
> `buildUponDefaultConfig = true` layers your file over that baseline, so your
> `detekt.yml` contains only the deltas and is short enough to review. Checking
> it in rather than relying on the bundled resource means a detekt upgrade
> cannot silently change what the build enforces without a visible diff. Put it
> at `config/detekt/detekt.yml`, which is the convention every Kotlin project
> uses and the path `detektGenerateConfig` writes to.

```kotlin
// bad — buildUponDefaultConfig left at its default of false, so the checked-in
// file REPLACES the default and every rule it does not mention is off
detekt {
    config.setFrom(rootProject.file("config/detekt/detekt.yml"))
}

// good
detekt {
    buildUponDefaultConfig = true
    config.setFrom(rootProject.file("config/detekt/detekt.yml"))
    ignoreFailures = false
    parallel = true
    basePath = rootProject.projectDir.absolutePath
}
```

```bash
# good — generate the starting point once, then prune it to the deltas
./gradlew detektGenerateConfig
```

## 47.5 Know which detekt major version you are on — the configuration schema changed.

> Why? detekt 2.0 removed configuration keys that every pre-2.0 tutorial still
> shows, and a stale key is not a warning by default: with
> `config.validation: true` it is a hard failure, and without it, it is
> silently ignored. The differences that matter are: the Gradle plugin id moved
> from `io.gitlab.arturbosch.detekt` to `dev.detekt`; the whole `build:` block
> — `maxIssues`, `weights`, `excludeCorrectable` — is gone, replaced by
> "any finding with severity `Error` fails the build"; the `output-reports:`
> block is gone, and reports are configured in the Gradle plugin or on the CLI;
> and the threshold keys were renamed (`LongMethod.threshold` →
> `allowedLines`, `CyclomaticComplexMethod.threshold` → `allowedComplexity`,
> `LongParameterList.functionThreshold` → `allowedFunctionParameters`).
> Compatibility is also tighter than most tools: detekt embeds the Kotlin
> compiler, so **Kotlin 2.4 requires detekt 2.0.0-alpha.5**; detekt 1.23.8 is
> built against Kotlin 2.0.21 and will not parse everything a 2.4 codebase
> contains.
> **Violation — enforced by `config: validation: true`, which fails on an
> unknown or removed key.**

```yaml
# bad — detekt 1.x schema running under detekt 2.x
build:
  maxIssues: 10
  weights:
    complexity: 2

complexity:
  LongMethod:
    threshold: 60
  LongParameterList:
    functionThreshold: 6

output-reports:
  active: true

# good — detekt 2.x schema
config:
  validation: true
  warningsAsErrors: true
  checkExhaustiveness: true

complexity:
  LongMethod:
    active: true
    allowedLines: 60
  LongParameterList:
    active: true
    allowedFunctionParameters: 5
    allowedConstructorParameters: 6
```

## 47.6 Run the source-set tasks so detekt has type resolution — the plain `detekt` task does not.

> Why? This is the single highest-leverage line in the chapter. Roughly a third
> of detekt's most valuable rules cannot run at all without a resolved type,
> and detekt does not fail when they are skipped — it just reports nothing.
> `UnsafeCallOnNullableType` (the `!!` ban), `HasPlatformType`, `UnsafeCast`,
> `CastNullableToNonNullableType`, `MapGetWithNotNullAssertionOperator`,
> `NullableToStringCall`, `ElseCaseInsteadOfExhaustiveWhen`,
> `IgnoredReturnValue`, and **every coroutines rule except
> `GlobalCoroutineUsage`** are all documented as requiring type resolution. A
> pipeline that runs `./gradlew detekt` therefore has a green build, a
> configured ruleset, and no null-safety enforcement whatsoever. The
> autogenerated per-source-set tasks — `detektMain`, `detektTest`, and the
> per-compilation variants — carry the compile classpath and do run them.
> In detekt 2.x type resolution is the default for those tasks; in 1.23.x a
> custom `Detekt` task needs `classpath` and `jvmTarget` set explicitly.
> **Violation — the rules are enforced only when the right task runs.**

```bash
# bad — silently skips UnsafeCallOnNullableType and every coroutines rule
./gradlew detekt

# good
./gradlew detektMain detektTest
```

```kotlin
// good — wire the type-resolving tasks into `check` so nobody has to remember
tasks.named("check") {
    dependsOn(tasks.named("detektMain"), tasks.named("detektTest"))
}
```

```kotlin
// The rule this buys you. Without type resolution detekt reports nothing here.

// bad — UnsafeCallOnNullableType
fun labelUnsafely(order: Order?): String {
    return order!!.customerName
}

// good
fun label(order: Order?): String {
    return order?.customerName ?: "unknown"
}
```

## 47.7 Raise `UnsafeCallOnNullableType` to error — it is the mechanical form of the `!!` ban.

> Why? [Chapter 6](06-null-safety.md) bans `!!` outright, and this is the check
> that makes the ban real. detekt describes the rule as reporting "unsafe calls
> on nullable types. These calls will throw a NullPointerException in case the
> nullable value is null" — which is precisely the failure `!!` exists to
> create. Two neighbouring rules complete the set:
> `MapGetWithNotNullAssertionOperator` catches the specific `map[key]!!` idiom
> that people reach for when they "know" a key is present, and
> `CastNullableToNonNullableType` catches the `as` spelling of the same
> mistake. Leaving these at warning severity in a build that emits warnings is
> the same as leaving them off.
> **Violation — enforced by `detekt/UnsafeCallOnNullableType`, with type
> resolution (§47.6).**

```yaml
# good — config/detekt/detekt.yml
potential-bugs:
  UnsafeCallOnNullableType:
    active: true
  MapGetWithNotNullAssertionOperator:
    active: true
  CastNullableToNonNullableType:
    active: true
  UnsafeCast:
    active: true
  HasPlatformType:
    active: true
  NullableToStringCall:
    active: true
  ElseCaseInsteadOfExhaustiveWhen:
    active: true
```

```kotlin
// bad — three spellings of the same NullPointerException
val name = order!!.customerName
val rate = rates[currency]!!
val id = maybeId as String

// good
val name = order?.customerName ?: error("order missing for $orderId")
val rate = rates[currency] ?: throw UnknownCurrencyException(currency)
val id = maybeId as? String ?: return null
```

## 47.8 Turn the whole `exceptions` rule set on, and tune its two allowlists rather than disabling rules.

> Why? `SwallowedException` and `TooGenericExceptionCaught` are both on by
> default and both are routinely disabled, because their defaults fire on
> patterns a team believes are legitimate. Disabling them is the wrong repair:
> each rule carries an `allowedExceptionNameRegex` (default
> `'_|(ignore|expected).*'`) that lets you name the intentional case, and
> `SwallowedException` additionally has `ignoredExceptionTypes`. Naming the
> exception `ignored` in the one place you genuinely mean to drop it turns an
> invisible swallow into a documented one. There is one Kotlin-specific
> addition worth making: `CancellationException` must never be swallowed, and
> `TooGenericExceptionCaught` firing on `catch (e: Exception)` inside a
> coroutine is usually pointing at exactly that bug — see
> [Chapter 35](35-cancellation-and-timeouts.md).
> **Violation — enforced by `detekt/SwallowedException` and
> `detekt/TooGenericExceptionCaught`.**

```yaml
# bad — the rules are off, so every swallow in the codebase is invisible
exceptions:
  SwallowedException:
    active: false
  TooGenericExceptionCaught:
    active: false

# good — on, with the deliberate cases named rather than the rules removed
exceptions:
  SwallowedException:
    active: true
    ignoredExceptionTypes:
      - 'InterruptedException'
      - 'NumberFormatException'
      - 'ParseException'
    allowedExceptionNameRegex: '_|(ignore|expected).*'
  TooGenericExceptionCaught:
    active: true
    allowedExceptionNameRegex: '_|(ignore|expected).*'
  TooGenericExceptionThrown:
    active: true
  ThrowingExceptionsWithoutMessageOrCause:
    active: true
  PrintStackTrace:
    active: true
  ReturnFromFinally:
    active: true
  RethrowCaughtException:
    active: true
  NotImplementedDeclaration:
    active: true
```

```kotlin
// bad — the cause is gone, and a CancellationException is quietly eaten
try {
    remoteCall()
} catch (e: Exception) {
    return Fallback
}

// good — the intentional drop is named, so a reader sees the decision
try {
    Integer.parseInt(raw)
} catch (ignored: NumberFormatException) {
    0
}

// good — the cause is preserved and cancellation is re-thrown
try {
    remoteCall()
} catch (e: CancellationException) {
    throw e
} catch (e: IOException) {
    throw RemoteCallFailedException("calling $endpoint", e)
}
```

## 47.9 Enable every `coroutines` rule, not just the four that are on by default.

> Why? Only `InjectDispatcher`, `RedundantSuspendModifier`,
> `SleepInsteadOfDelay`, and `SuspendFunWithFlowReturnType` are active out of
> the box. The five that are off — `GlobalCoroutineUsage`,
> `SuspendFunInFinallySection`, `SuspendFunSwallowedCancellation`,
> `SuspendFunWithCoroutineScopeReceiver`, and
> `CoroutineLaunchedInTestWithoutRunTest` — cover the exact failures Chapters
> 33 to 40 spend the most words on: unowned scopes, cleanup that cannot run
> during cancellation, `runCatching` eating a `CancellationException`, and
> tests whose coroutines outlive the assertion. Every one of them except
> `GlobalCoroutineUsage` requires type resolution, so §47.6 is a prerequisite
> for this rule, not an optional companion.
> **Violation — enforced by the `coroutines` rule set with type resolution.**

```yaml
# good — config/detekt/detekt.yml
coroutines:
  active: true
  CoroutineLaunchedInTestWithoutRunTest:
    active: true
  GlobalCoroutineUsage:
    active: true
  InjectDispatcher:
    active: true
    dispatcherNames:
      - 'IO'
      - 'Default'
      - 'Unconfined'
  RedundantSuspendModifier:
    active: true
  SleepInsteadOfDelay:
    active: true
  SuspendFunInFinallySection:
    active: true
  SuspendFunSwallowedCancellation:
    active: true
  SuspendFunWithCoroutineScopeReceiver:
    active: true
  SuspendFunWithFlowReturnType:
    active: true
```

```kotlin
// bad — every line here is a default-off coroutines finding
class Importer {
    fun start() {
        GlobalScope.launch { import() }            // GlobalCoroutineUsage
    }

    suspend fun safeImport(): Result<Unit> =
        runCatching { import() }                   // SuspendFunSwallowedCancellation
}

// good
class Importer(
    private val scope: CoroutineScope,
    private val ioDispatcher: CoroutineDispatcher,  // InjectDispatcher satisfied
) {
    fun start(): Job = scope.launch(ioDispatcher) { import() }

    suspend fun safeImport(): Result<Unit> =
        try {
            Result.success(import())
        } catch (e: CancellationException) {
            throw e
        } catch (e: ImportException) {
            Result.failure(e)
        }
}
```

## 47.10 Make findings fail the build; never `ignoreFailures = true`.

> Why? A check that reports without failing is a check that gets ignored, and
> then a check that gets deleted a year later because "nobody looks at it".
> detekt gives you two independent switches and both have to be right:
> `config.warningsAsErrors: true` promotes every finding's severity so it
> counts, and Gradle's `ignoreFailures = false` (the default, but worth stating
> because it is the first thing people flip during adoption) makes a counted
> finding stop the build. In detekt 2.x there is no `maxIssues` budget any more
> — the build fails on any finding with severity `Error` — so severity is the
> only dial, which is a simplification worth having.
> **Violation — enforced by the Gradle plugin once `ignoreFailures` is false.**

```kotlin
// bad — reports generated, nothing blocked, and the number creeps upward
detekt {
    ignoreFailures = true
}

// good
detekt {
    buildUponDefaultConfig = true
    config.setFrom(rootProject.file("config/detekt/detekt.yml"))
    ignoreFailures = false
}
```

```yaml
# good — config/detekt/detekt.yml
config:
  validation: true
  warningsAsErrors: true
  checkExhaustiveness: false   # see 47.11 — a delta file is not exhaustive
```

## 47.11 Leave `config.validation` on, and decide `checkExhaustiveness` against how you keep the config.

> Why? The two flags catch opposite mistakes, but only one of them is free.
> `validation: true` fails the run when your file contains a key detekt does
> not recognise, which is what stops a rule silently doing nothing after a
> rename — §47.5's `threshold` → `allowedLines` migration is exactly this
> failure. It costs nothing and should always be on.
> `checkExhaustiveness: true` runs the other way: it fails when a rule exists
> in detekt's defaults but is *absent* from your file, so a new rule introduced
> by an upgrade cannot land in your build unreviewed. That is genuinely
> valuable, and it is incompatible with the short delta file of §47.4 — an
> exhaustive config has to name every rule detekt ships, which is the full
> `detektGenerateConfig` output rather than a reviewable diff. Pick one shape
> and be honest about it: a delta file layered on `buildUponDefaultConfig` with
> `checkExhaustiveness: false`, or the full generated config with
> `checkExhaustiveness: true` and an upgrade ritual that re-generates and diffs
> it. This skill ships the delta file.
> **Violation — enforced by detekt itself, before any rule runs.**

```yaml
# bad — a typo'd key is silently ignored, and a rename silently deactivates
# the rule it was attached to
config:
  validation: false

complexity:
  LongMethod:
    activee: true      # never noticed
    allowedLines: 60

# good — the delta-file shape this skill ships (see 47.4)
config:
  validation: true
  warningsAsErrors: true
  checkExhaustiveness: false   # a delta file is not exhaustive by definition
  excludes: []

# good — the alternative: the full generated config, re-generated and diffed
# on every detekt upgrade
config:
  validation: true
  warningsAsErrors: true
  checkExhaustiveness: true
  excludes: []
```

## 47.12 Set the complexity thresholds deliberately, once, and treat them as review triggers rather than hard caps.

> Why? detekt's defaults — `LongMethod.allowedLines: 60`,
> `LongParameterList.allowedFunctionParameters: 5`,
> `CyclomaticComplexMethod.allowedComplexity: 14`,
> `NestedBlockDepth`, `LargeClass.allowedLines: 600` — are a reasonable
> starting point and a terrible thing to leave unexamined, because Kotlin's
> line economy differs from Java's. A 60-line Kotlin function is genuinely
> long; a `when` over a twelve-case sealed hierarchy is *not* complex despite
> what `CyclomaticComplexMethod` scores it, which is what
> `ignoreSimpleWhenEntries` exists for. Pick numbers you will actually enforce
> and write down why, because the alternative is a threshold that gets raised
> once per quarter until it means nothing.
> **Violation — enforced by the `complexity` rule set.**

```yaml
# bad — thresholds raised reactively, each time someone hit one
complexity:
  LongMethod:
    allowedLines: 250
  LongParameterList:
    allowedFunctionParameters: 12
  CyclomaticComplexMethod:
    allowedComplexity: 40

# good — chosen once, with the Kotlin-specific exemptions turned on
complexity:
  active: true
  LongMethod:
    active: true
    allowedLines: 60
  LargeClass:
    active: true
    allowedLines: 600
  LongParameterList:
    active: true
    allowedFunctionParameters: 5
    allowedConstructorParameters: 6
    ignoreDefaultParameters: false
    ignoreDataClasses: true
  CyclomaticComplexMethod:
    active: true
    allowedComplexity: 14
    ignoreSimpleWhenEntries: true   # exhaustive `when` over a sealed type
  ComplexCondition:
    active: true
    allowedConditions: 3
  NestedBlockDepth:
    active: true
  TooManyFunctions:
    active: true
```

## 47.13 Configure `MagicNumber` and `ForbiddenComment` for your project rather than accepting the defaults.

> Why? These are the two rules most likely to be switched off in the first
> week, and in both cases the default is the problem rather than the rule.
> `MagicNumber` fires on every literal outside a named constant, which is right
> in business logic and noise in a test's expected values or a `data class`
> default — it carries `ignoreNumbers`, `ignorePropertyDeclaration`,
> `ignoreAnnotation`, and `excludes` for exactly that. `ForbiddenComment`
> defaults to flagging `TODO:`, `FIXME:`, and `STOPSHIP:`, which is either
> vital or actively harmful depending on whether your team tracks TODOs in the
> issue tracker or in the code. Decide, configure, and keep the rule; a
> configured rule keeps working as the codebase changes, a disabled one is
> gone forever.
> **Violation — enforced by `detekt/MagicNumber` and
> `detekt/ForbiddenComment`.**

```yaml
# bad — turned off after one noisy run, and never revisited
style:
  MagicNumber:
    active: false
  ForbiddenComment:
    active: false

# good — kept on, scoped to where it earns its keep
style:
  MagicNumber:
    active: true
    excludes: ['**/test/**', '**/*Test.kt', '**/*Spec.kt']
    ignoreNumbers: ['-1', '0', '1', '2']
    ignorePropertyDeclaration: true
    ignoreAnnotation: true
    ignoreEnums: true
  ForbiddenComment:
    active: true
    comments:
      - reason: 'Track work in the issue tracker, not in a comment.'
        value: 'FIXME:'
      - reason: 'STOPSHIP must never reach a release branch.'
        value: 'STOPSHIP:'
```

```kotlin
// bad — three unexplained literals, one of which is a timeout
fun retryPolicy() = RetryPolicy(3, 250, 30_000)

// good — named, so the number and its meaning travel together
private const val MAX_ATTEMPTS = 3
private val INITIAL_BACKOFF = 250.milliseconds
private val OVERALL_TIMEOUT = 30.seconds

fun retryPolicy() = RetryPolicy(MAX_ATTEMPTS, INITIAL_BACKOFF, OVERALL_TIMEOUT)
```

## 47.14 Adopt the chain on a legacy codebase with a dated, shrinking baseline — never with `ignoreFailures`.

> Why? Turning these tools on against an existing codebase produces thousands
> of findings, and only two responses survive contact with a deadline: fix them
> all first, or grandfather what exists and block anything new.
> `ignoreFailures = true` is neither — it enforces nothing while looking like it
> does, and it never gets turned off. A checked-in `baseline.xml` covering
> exactly today's findings is a debt register instead: it is reviewable, every
> line in it is a to-do with a file name attached, and because new findings are
> not in it, new code is fully enforced from day one. The failure mode to guard
> against is the baseline becoming permanent, so date it in the commit message,
> put a line count in the README, and regenerate it *never* — a regenerated
> baseline silently re-grandfathers everything anyone added since.
> **Violation — new findings still fail the build; baselined ones do not.**

```kotlin
// bad — enforces nothing, and will still be here in two years
detekt {
    ignoreFailures = true
}

// good — new code is fully enforced; the baseline is visible and shrinking
detekt {
    buildUponDefaultConfig = true
    config.setFrom(rootProject.file("config/detekt/detekt.yml"))
    baseline = rootProject.file("config/detekt/baseline.xml")
    ignoreFailures = false
}
```

```bash
# good — generate once, at adoption, and never again
./gradlew detektBaseline
```

```xml
<!-- config/detekt/baseline.xml — generated 2026-03-04, 812 entries.
     CurrentIssues shrinks as the debt is paid down; ManuallySuppressedIssues
     holds reviewed false positives and should stay near zero. -->
<SmellBaseline>
  <ManuallySuppressedIssues/>
  <CurrentIssues>
    <ID>LongMethod:LedgerImporter.kt$LedgerImporter$fun import()</ID>
    <ID>TooGenericExceptionCaught:LegacyGateway.kt$LegacyGateway$e: Exception</ID>
  </CurrentIssues>
</SmellBaseline>
```

The ktlint Gradle plugin has the equivalent mechanism, and the same rule
applies to it — see [Chapter 1, §1.20](01-formatting-and-tooling.md):

```kotlin
ktlint {
    baseline.set(rootProject.file("config/ktlint/baseline.xml"))
}
```

## 47.15 Suppress a detekt finding with `@Suppress("<RuleId>")` at the smallest scope, and say why.

> Why? `@Suppress` is legal on a class, and on a class it disables the check
> for every member — including members written years later by someone who never
> saw the annotation. Scoped to the one function or the one property that
> genuinely needs it, the suppression stays true as the code changes. detekt
> accepts the bare rule id (`@Suppress("LongMethod")`), the rule-set-qualified
> form (`@Suppress("complexity:LongParameterList")`), and a detekt-qualified
> form (`@Suppress("detekt:LongMethod")`); prefer the plain rule id, which is
> what the finding output prints. A few rules — `TooManyFunctions` among them —
> can only be suppressed at file level with `@file:Suppress`, which is a signal
> in itself: if you need the file-level form, ask whether the file should be
> split ([Chapter 2, §2.13](02-source-files-and-structure.md)) before reaching
> for it. The comment is what lets the next reader decide whether the
> suppression is still justified, which is the only question that matters when
> they meet one.

```kotlin
// bad — the whole class exempted from a complexity rule, forever
@Suppress("CyclomaticComplexMethod")
class TaxCalculator {
    fun calculate(order: Order): Money { /* 300 lines */ }

    fun rateFor(region: Region): BigDecimal { /* added later, also exempt */ }
}

// good — one declaration, with the reason and the exit condition
class TaxCalculator {
    // Regional tax rules genuinely branch 20 ways; the branching mirrors the
    // statutory table 1:1 and splitting it would obscure the mapping.
    @Suppress("CyclomaticComplexMethod")
    fun calculate(order: Order): Money { /* ... */ }

    fun rateFor(region: Region): BigDecimal { /* not exempt */ }
}
```

## 47.16 Never write `@Suppress("all")`, and use `ForbiddenSuppress` to make that unwriteable.

> Why? `@Suppress("all")` — and its detekt spellings `@Suppress("detekt:all")`
> and `@Suppress("detekt.all")` — silences every check over its scope,
> including checks that did not exist when the suppression was written. The
> failure mode is specific and nasty: a new `potential-bugs` rule is added by
> an upgrade, it finds a genuine null-safety bug inside the suppressed region,
> and it reports nothing. A suppression that names its target degrades
> gracefully; one that does not becomes a permanent blind spot. detekt's
> `ForbiddenSuppress` rule turns the policy into a build failure by naming the
> rules whose suppression is not allowed, and the rule "cannot be suppressed"
> itself.
> **Violation — enforced by `detekt/ForbiddenSuppress` once `rules` is
> populated.**

```yaml
# good — config/detekt/detekt.yml
style:
  ForbiddenSuppress:
    active: true
    rules:
      - 'UnsafeCallOnNullableType'
      - 'MapGetWithNotNullAssertionOperator'
      - 'CastNullableToNonNullableType'
      - 'SwallowedException'
      - 'GlobalCoroutineUsage'
      - 'SleepInsteadOfDelay'
```

```kotlin
// bad — a blanket amnesty over a whole file
@file:Suppress("all")

// bad — the one rule the codebase most needs, suppressed
@Suppress("UnsafeCallOnNullableType")
fun load(id: UUID): Order = repository.find(id)!!

// good — the null case is handled instead of the check being removed
fun load(id: UUID): Order =
    repository.find(id) ?: throw OrderNotFoundException(id)
```

## 47.17 Suppress a ktlint rule with `@Suppress("ktlint:<ruleset>:<rule-id>")`; the `ktlint-disable` comment is gone.

> Why? ktlint removed the `// ktlint-disable` comment directive in favour of
> `@Suppress` / `@SuppressWarnings` as of 0.50, and the annotation form is
> strictly better for the same reason as §47.15: it attaches to a declaration,
> so it moves with the code and survives refactoring, whereas a comment pair
> attaches to line numbers and silently widens its scope on the next edit
> between the two markers. Imports are the one case that needs the file-level
> form, because an import statement cannot carry an annotation. Treat
> `@Suppress("ktlint")` — the everything form — exactly as §47.16 treats
> `@Suppress("all")`.
> **Violation — enforced by `standard:ktlint-suppression`, which flags the
> removed directive and can migrate it.**

```kotlin
// bad — removed directive; ktlint no longer honours it at all
// ktlint-disable no-wildcard-imports
import java.util.*

// good — one rule, file level because imports cannot be annotated,
// with the reason stated
@file:Suppress("ktlint:standard:no-wildcard-imports") // generated DSL, ~90 symbols

// good — one rule, smallest possible declaration scope
@Suppress("ktlint:standard:function-naming") // JUnit @DisplayName convention
fun `rejects a negative amount`() {
    // ...
}
```

## 47.18 Exclude generated code by path, never by suppression.

> Why? Generated sources — protobuf stubs, OpenAPI clients, jOOQ classes,
> KSP output, Wire adapters — follow the generator's conventions rather than
> yours, and you cannot fix a finding in a file that is rewritten on every
> build. Injecting `@Suppress` into a template means the suppressions are also
> regenerated away, and per-file baseline entries invalidate on the next
> codegen run. Excluding by path removes the whole tree from analysis in one
> visible place, and keeps the exclusion in the build script rather than
> scattered through machine-written files. Note that both tools need telling
> separately, and that Gradle's `build/generated` is not always where a
> generator writes.

```kotlin
// bad — a @Suppress in a Mustache template, or a baseline entry the next
// codegen run silently invalidates

// good — one path exclusion per tool, in the root build script.
// The Detekt task type moved package between majors, so import it rather than
// spelling it out inline: `dev.detekt.gradle.Detekt` in 2.x,
// `io.gitlab.arturbosch.detekt.Detekt` in 1.23.x.
import dev.detekt.gradle.Detekt

tasks.withType(Detekt::class).configureEach {
    exclude("**/build/generated/**", "**/generated/**")
}

ktlint {
    filter {
        exclude("**/build/generated/**", "**/generated/**")
    }
}
```

## 47.19 Relax test-source rules deliberately, in a second config, and keep the correctness rules on.

> Why? Test code has different tradeoffs. `MagicNumber` on an expected value is
> noise, `LongMethod` on a table-driven test is usually fine, and
> `TooManyFunctions` on a test class is the point. But the relaxation has to be
> a recorded decision rather than an accident of `detektTest` never having been
> wired up. Correctness rules stay on without exception: a swallowed exception
> or a `!!` in a test produces a test that passes for the wrong reason, which
> is strictly worse than a failing test. Note the Kotlin-specific addition —
> `CoroutineLaunchedInTestWithoutRunTest` only ever fires on test sources, so
> switching detekt off for tests disables it entirely.

```kotlin
// bad — tests silently unchecked because only detektMain was wired in
tasks.named("check") {
    dependsOn(tasks.named("detektMain"))
}

// good — tests are checked, with a named, narrower ruleset
tasks.named("check") {
    dependsOn(tasks.named("detektMain"), tasks.named("detektTest"))
}

tasks.named<Detekt>("detektTest") {
    config.setFrom(rootProject.file("config/detekt/detekt-test.yml"))
}
```

```yaml
# config/detekt/detekt-test.yml — differs from the main ruleset ONLY here
style:
  MagicNumber:
    active: false
complexity:
  LongMethod:
    active: false
  TooManyFunctions:
    active: false
# Everything else — potential-bugs, exceptions, coroutines, naming — is
# inherited unchanged and stays on.
```

## 47.20 Pin every tool version, and upgrade each in its own commit.

> Why? Each of these tools changes what it flags between releases, and detekt
> additionally embeds a Kotlin compiler, so a detekt bump can change *parsing*
> as well as *rules*. An unpinned version means a build that passed yesterday
> fails today with no local change, and the developer who hits it cannot tell a
> new check from a regression they caused. Pinning turns every upgrade into a
> reviewable diff whose entire content is "these findings are new". Pin four
> things, not two: the Gradle plugin versions *and* the underlying tool
> versions they resolve, because the plugin and the tool version float
> independently.

```kotlin
// bad — three floating versions, three sources of unreproducible failure
plugins {
    id("org.jlleitschuh.gradle.ktlint")
    id("dev.detekt")
}

// good — every version explicit, ideally in the version catalog
plugins {
    kotlin("jvm") version "2.4.0"
    id("org.jlleitschuh.gradle.ktlint") version "14.2.0"
    id("dev.detekt") version "2.0.0-alpha.5"
}

ktlint {
    version.set("1.8.0")        // the ktlint engine, not the plugin
}

detekt {
    toolVersion = "2.0.0-alpha.5"
}
```

## 47.21 Order the pipeline by fix cost: format, then compile, then detekt, then tests.

> Why? Feedback should arrive cheapest-first. `ktlintCheck` runs in seconds and
> its fix is one command, so it belongs before anything that takes a minute.
> The compiler is next because `allWarningsAsErrors`, `-Xjsr305=strict`, and
> explicit API mode all fail during compilation and you have to compile anyway.
> detekt comes third — it *requires* the compiled classpath for type resolution
> (§47.6), so it cannot run earlier even if you wanted it to. Tests are last
> because they are the slowest and because there is no value in running them
> against code that will not merge.

```yaml
# bad — a 12-minute test run, then a formatting failure
- run: ./gradlew test
- run: ./gradlew ktlintCheck detektMain

# good — .github/workflows/ci.yml
- run: ./gradlew ktlintCheck
- run: ./gradlew compileKotlin compileTestKotlin
- run: ./gradlew detektMain detektTest
- run: ./gradlew test
```

## 47.22 Read **Violation** and **Suggestion** as claims about tooling, not about importance.

> Why? Throughout this skill, **Violation** means "some tool in the chain above
> fails the build on this", and **Suggestion** means "no tool can mechanically
> verify this, so it is a review judgement". The distinction is about
> *enforceability*, not severity — several of the most consequential rules in
> the guide are Suggestions precisely because no analyser can judge them.
> Treating Suggestions as optional is the misreading this rule exists to
> prevent: a Suggestion is the class of rule that needs a human reviewer *most*,
> because nothing else will catch it. The Kotlin-specific twist is that a rule's
> label can change with your configuration: `UnsafeCallOnNullableType` is a
> Violation only when type resolution is on (§47.6), so the same `!!` is
> mechanically caught in one repository and purely a review matter in another.

```kotlin
// Violation — standard:no-wildcard-imports fails the build
import java.util.*

// Violation — detekt/UnsafeCallOnNullableType fails the build, but ONLY if
// the pipeline runs detektMain rather than detekt
val name = order!!.customerName

// Suggestion — no tool can tell that this member ordering is chronological
// rather than logical (Chapter 2, §2.14). A reviewer can.
class OrderService(private val repository: OrderRepository) {
    private fun applyDiscount(order: Order): Money = TODO()

    fun place(request: NewOrder): Order = TODO()

    private val log = LoggerFactory.getLogger(OrderService::class.java)
}
```

## The shipped `detekt.yml`

The complete delta file, to be layered over detekt's defaults with
`buildUponDefaultConfig = true`. Everything not mentioned keeps its default
activation.

```yaml
# config/detekt/detekt.yml
config:
  validation: true
  warningsAsErrors: true
  checkExhaustiveness: false   # see 47.11 — a delta file is not exhaustive
  excludes: []

comments:
  AbsentOrWrongFileLicense:
    active: true
    licenseTemplateIsRegex: false
    licenseTemplate: |-
      /*
       * Copyright 2026 Example Inc.
       *
       * Licensed under the Apache License, Version 2.0.
       */

complexity:
  ComplexCondition:
    active: true
    allowedConditions: 3
  CyclomaticComplexMethod:
    active: true
    allowedComplexity: 14
    ignoreSimpleWhenEntries: true
  LargeClass:
    active: true
    allowedLines: 600
  LongMethod:
    active: true
    allowedLines: 60
  LongParameterList:
    active: true
    allowedFunctionParameters: 5
    allowedConstructorParameters: 6
    ignoreDataClasses: true
  NestedBlockDepth:
    active: true
  TooManyFunctions:
    active: true

coroutines:
  CoroutineLaunchedInTestWithoutRunTest:
    active: true
  GlobalCoroutineUsage:
    active: true
  InjectDispatcher:
    active: true
  RedundantSuspendModifier:
    active: true
  SleepInsteadOfDelay:
    active: true
  SuspendFunInFinallySection:
    active: true
  SuspendFunSwallowedCancellation:
    active: true
  SuspendFunWithCoroutineScopeReceiver:
    active: true
  SuspendFunWithFlowReturnType:
    active: true

empty-blocks:
  EmptyCatchBlock:
    active: true
  EmptyFunctionBlock:
    active: true

exceptions:
  NotImplementedDeclaration:
    active: true
  PrintStackTrace:
    active: true
  RethrowCaughtException:
    active: true
  ReturnFromFinally:
    active: true
  SwallowedException:
    active: true
    allowedExceptionNameRegex: '_|(ignore|expected).*'
  ThrowingExceptionsWithoutMessageOrCause:
    active: true
  TooGenericExceptionCaught:
    active: true
    allowedExceptionNameRegex: '_|(ignore|expected).*'
  TooGenericExceptionThrown:
    active: true

naming:
  InvalidPackageDeclaration:
    active: true
    rootPackage: 'com.example.platform'
  MatchingDeclarationName:
    active: true
  NoNameShadowing:
    active: true

performance:
  CouldBeSequence:
    active: true
  SpreadOperator:
    active: true

potential-bugs:
  CastNullableToNonNullableType:
    active: true
  ElseCaseInsteadOfExhaustiveWhen:
    active: true
  HasPlatformType:
    active: true
  LateinitUsage:
    active: true
    excludes: ['**/test/**', '**/*Test.kt']
  MapGetWithNotNullAssertionOperator:
    active: true
  MissingPackageDeclaration:
    active: true
  NullableToStringCall:
    active: true
  UnsafeCallOnNullableType:
    active: true
  UnsafeCast:
    active: true

style:
  # Owned by ktlint — see 47.2
  MaxLineLength:
    active: false
  ModifierOrder:
    active: false
  NewLineAtEndOfFile:
    active: false
  NoTabs:
    active: false
  SpacingAfterPackageAndImports:
    active: false
  TrailingWhitespace:
    active: false
  UnusedImport:
    active: false
  WildcardImport:
    active: false

  # Semantic — ktlint cannot see any of these
  CanBeNonNullable:
    active: true
  ClassOrdering:
    active: true
  ForbiddenComment:
    active: true
  ForbiddenSuppress:
    active: true
    rules:
      - 'UnsafeCallOnNullableType'
      - 'MapGetWithNotNullAssertionOperator'
      - 'CastNullableToNonNullableType'
      - 'SwallowedException'
      - 'GlobalCoroutineUsage'
      - 'SleepInsteadOfDelay'
  MagicNumber:
    active: true
    excludes: ['**/test/**', '**/*Test.kt']
    ignorePropertyDeclaration: true
    ignoreAnnotation: true
    ignoreEnums: true
  ReturnCount:
    active: true
  ThrowsCount:
    active: true
  UnnecessaryFullyQualifiedName:
    active: true
  UnusedParameter:
    active: true
  UnusedPrivateClass:
    active: true
  UnusedPrivateFunction:
    active: true
  UnusedPrivateProperty:
    active: true
  UseCheckOrError:
    active: true
  UseRequire:
    active: true
  UseRequireNotNull:
    active: true
  UtilityClassWithPublicConstructor:
    active: true
  VarCouldBeVal:
    active: true
```
