<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 38. Static Analysis Configuration

Every `> Enforced by:` and `**Violation**` callout in this skill points at a
real check in a real tool. This chapter is the configuration those callouts
refer to: **Spotless + google-java-format** for formatting, **Checkstyle**
with a Google-derived ruleset for the structural rules a formatter cannot
see, **Error Prone** for semantic bug patterns, and **NullAway** for null
contracts. Four tools, four disjoint concerns, one build.

The division of labour is the whole design, and it is worth stating before
any configuration:

| Tool | Owns | Sees | Fix cost |
|---|---|---|---|
| google-java-format (via Spotless) | Whitespace, braces layout, wrapping, column limit, import order | Token stream | One command |
| Checkstyle | Naming, Javadoc presence, import hygiene, file and class structure | Parse tree, one file at a time | Small edit |
| Error Prone | Semantic bug patterns, misused APIs | Full `javac` type information | Code change |
| NullAway | Null contracts and field initialization | `javac` types plus a dataflow analysis | Design change |

The ordering is not arbitrary — it is by fix cost. A formatting failure is
always repairable by running `spotlessApply`, so it can block a build with
zero human judgement. A NullAway failure may mean the API's nullability was
designed wrong. Conflating the two produces a build that fails for reasons of
wildly different weight, and the predictable response is to turn something
off.

Formatting itself is [Chapter 1](01-formatting-and-tooling.md) and is not
repeated here. The rules each Checkstyle module backs are in
[Chapters 2-7](02-source-file-structure.md); the nullability conventions
NullAway enforces are in [Chapter 25](25-nullability.md).

**Tool alignment:** this chapter *is* the tool alignment. The shipped
ruleset lives at `config/checkstyle/checkstyle.xml` at the repository root,
which is Gradle's own convention for the `checkstyle` plugin, so the Gradle
wiring below needs no `configFile` override.

## 38.1 Run all four tools, and give each exactly one concern.

> Why? A single "linter" that owns everything has one severity, one
> suppression mechanism, and one failure mode, so the cheap failures and the
> expensive ones become indistinguishable. Four tools with disjoint scopes
> means the pipeline can tell a developer *which kind* of problem they have
> before they read a single line of output, and each tool can be tuned,
> suppressed, or upgraded without touching the others.

```kotlin
// bad — Checkstyle asked to do all four jobs badly
checkstyle {
  // Indentation, LineLength, plus hand-written regex modules trying to
  // approximate Error Prone's ReferenceEquality and NullAway's analysis
}

// good — build.gradle.kts, four plugins, four scopes
plugins {
  java
  checkstyle
  id("com.diffplug.spotless") version "7.0.2"
  id("net.ltgt.errorprone") version "4.1.0"
}
```

## 38.2 Never encode a whitespace, indentation, or wrapping rule in Checkstyle.

> Why? `google-java-format` and Checkstyle will disagree, because Checkstyle
> modules such as `Indentation`, `LineLength`, `WhitespaceAround`, and
> `OperatorWrap` were written for a world without a canonical formatter. When
> they disagree, `spotlessApply` reintroduces the Checkstyle violation on
> every run, so the only way out is to disable one tool — and the one that
> gets disabled is usually the formatter, which is the wrong answer. The
> formatter is authoritative for everything in
> [Google Java Style §4](https://google.github.io/styleguide/javaguide.html#s4-formatting).

```xml
<!-- bad — every one of these fights googleJavaFormat -->
<module name="TreeWalker">
  <module name="Indentation"/>
  <module name="LineLength">
    <property name="max" value="100"/>
  </module>
  <module name="WhitespaceAround"/>
  <module name="OperatorWrap"/>
  <module name="LeftCurly"/>
  <module name="RightCurly"/>
</module>

<!-- good — Checkstyle stays out of §4 entirely -->
<module name="TreeWalker">
  <module name="NeedBraces"/>
  <module name="MultipleVariableDeclarations"/>
  <module name="OneStatementPerLine"/>
</module>
```

`NeedBraces`, `MultipleVariableDeclarations`, and `OneStatementPerLine` are
the exception that proves the rule: they look like formatting but are AST
changes, which a layout formatter will never make. See
[§1.8](01-formatting-and-tooling.md) and
[§1.9](01-formatting-and-tooling.md).

## 38.3 Derive the ruleset from `google_checks.xml`, check it in, and ship it at `config/checkstyle/checkstyle.xml`.

> Why? Checkstyle's bundled `sun_checks.xml` — the Maven plugin's default —
> encodes a 2004 style guide that contradicts this skill in dozens of places.
> Starting from Google's own `google_checks.xml` means the ruleset already
> agrees with the guide every rule in this skill cites. Checking the file in
> rather than referencing the bundled resource means an upgrade of the
> Checkstyle jar cannot silently change what the build enforces. Placing it
> at `config/checkstyle/checkstyle.xml` matches Gradle's convention, so the
> build script needs no path configuration and every contributor knows where
> to look.

```kotlin
// bad — pulls whatever ruleset the pinned Checkstyle jar happens to bundle
checkstyle {
  config = resources.text.fromArchiveEntry(configurations.checkstyle, "google_checks.xml")
}

// good — the ruleset is a reviewed artifact of this repository
checkstyle {
  toolVersion = "10.21.1"
  // configFile defaults to config/checkstyle/checkstyle.xml
  maxWarnings = 0
  isIgnoreFailures = false
}
```

## 38.4 Give Checkstyle only the rules a formatter cannot see: naming, Javadoc presence, import hygiene, and file structure.

> Why? These four categories share one property — they are decidable from a
> single file's parse tree without type information, which is exactly what
> Checkstyle has and exactly what a formatter does not. Naming
> ([Chapter 3](03-naming.md)), Javadoc *presence* as opposed to Javadoc
> quality ([Chapter 4](04-javadoc.md)), imports
> ([Chapter 2](02-source-file-structure.md)), and file structure are the
> whole of Checkstyle's useful territory. Anything requiring types belongs to
> Error Prone.

```xml
<!-- config/checkstyle/checkstyle.xml -->
<module name="Checker">
  <property name="charset" value="UTF-8"/>
  <property name="severity" value="error"/>
  <property name="fileExtensions" value="java, properties, xml"/>

  <module name="NewlineAtEndOfFile"/>
  <module name="FileTabCharacter"/>
  <module name="SuppressionFilter">
    <property name="file" value="${config_loc}/suppressions.xml"/>
    <property name="optional" value="true"/>
  </module>

  <module name="TreeWalker">
    <module name="SuppressWarningsHolder"/>

    <!-- File and class structure (Chapter 2) -->
    <module name="OuterTypeFilename"/>
    <module name="OneTopLevelClass"/>
    <module name="PackageDeclaration"/>
    <module name="OverloadMethodsDeclarationOrder"/>
    <module name="NoLineWrap"/>

    <!-- Import hygiene (Chapter 2) -->
    <module name="AvoidStarImport"/>
    <module name="UnusedImports"/>
    <module name="RedundantImport"/>
    <module name="IllegalImport">
      <property name="illegalPkgs" value="sun, com.sun, jdk.internal"/>
    </module>
    <module name="CustomImportOrder">
      <property name="sortImportsInGroupAlphabetically" value="true"/>
      <property name="separateLineBetweenGroups" value="true"/>
      <property name="customImportOrderRules" value="STATIC###THIRD_PARTY_PACKAGE"/>
    </module>

    <!-- Naming (Chapter 3) -->
    <module name="PackageName"/>
    <module name="TypeName"/>
    <module name="RecordComponentName"/>
    <module name="MethodName"/>
    <module name="MemberName"/>
    <module name="ConstantName"/>
    <module name="ParameterName"/>
    <module name="LocalVariableName"/>
    <module name="AbbreviationAsWordInName"/>

    <!-- Javadoc presence and shape (Chapter 4) -->
    <module name="MissingJavadocType"/>
    <module name="MissingJavadocMethod">
      <property name="scope" value="public"/>
      <property name="allowMissingPropertyJavadoc" value="true"/>
    </module>
    <module name="JavadocMethod"/>
    <module name="SummaryJavadoc"/>
    <module name="JavadocParagraph"/>
    <module name="AtclauseOrder"/>
    <module name="NonEmptyAtclauseDescription"/>

    <!-- AST-level rules the formatter will not make (Chapters 1, 7) -->
    <module name="NeedBraces"/>
    <module name="MultipleVariableDeclarations"/>
    <module name="OneStatementPerLine"/>
    <module name="ArrayTypeStyle"/>
    <module name="UpperEll"/>
    <module name="ModifierOrder"/>
    <module name="NoFinalizer"/>
    <module name="EmptyCatchBlock">
      <property name="exceptionVariableName" value="expected|ignored"/>
    </module>
    <module name="AvoidEscapedUnicodeCharacters">
      <property name="allowEscapesForControlCharacters" value="true"/>
      <property name="allowByTailComment" value="true"/>
      <property name="allowNonPrintableEscapes" value="true"/>
    </module>
    <module name="IllegalTokenText">
      <property name="tokens" value="STRING_LITERAL, CHAR_LITERAL"/>
      <property name="format"
                value="\\u00(09|0(a|A)|0(c|C)|0(d|D)|22|27|5(C|c))|\\(0(10|11|12|14|15|42|47)|134)"/>
      <property name="message"
                value="Consider using special escape sequence instead of octal value or Unicode escaped value."/>
    </module>
  </module>

  <module name="SuppressWarningsFilter"/>
</module>
```

Note that `SuppressWarningsFilter` sits on `Checker` while its companion
`SuppressWarningsHolder` must sit inside `TreeWalker`. Omitting the holder
makes every `@SuppressWarnings("checkstyle:...")` in the codebase silently
inert.

## 38.5 Run Error Prone for the bug patterns that need type information.

> Why? Error Prone runs as a `javac` plugin, so it sees resolved types,
> inheritance, and the whole compilation unit graph. That is what lets it
> know `MissingOverride` applies because the supertype declares the method,
> or that `ReferenceEquality` matters because both operands are boxed
> `Integer`. Checkstyle cannot answer either question, because it never
> resolves a type. Anything you find yourself trying to express as a
> Checkstyle regex almost certainly belongs here instead.

```java
// bad — Checkstyle cannot see that Integer == Integer is a reference compare
if (order.id() == cachedId) { // both Integer; true only under the cache
  return cached;
}

// good — Error Prone's ReferenceEquality flags the above at compile time
if (Objects.equals(order.id(), cachedId)) {
  return cached;
}
```

## 38.6 Promote the Error Prone checks you rely on to `ERROR`, explicitly.

> Why? Error Prone ships most of its checks at `WARNING` severity, and a
> warning in a build that produces a thousand of them is not a check — it is
> noise. Naming each check you depend on and setting it to
> `CheckSeverity.ERROR` turns it into a contract: the check cannot silently
> stop firing because a default changed, and the list itself documents what
> the project actually enforces.

```kotlin
// bad — the plugin is applied and nothing else is said, so every check
// stays at its shipped default and the build stays green through all of them
plugins {
  id("net.ltgt.errorprone") version "4.1.0"
}

// good — the enforced set is explicit and fails the build
import net.ltgt.gradle.errorprone.CheckSeverity
import net.ltgt.gradle.errorprone.errorprone

tasks.withType<JavaCompile>().configureEach {
  options.errorprone {
    disableWarningsInGeneratedCode.set(true)
    check("MissingOverride", CheckSeverity.ERROR)
    check("ReferenceEquality", CheckSeverity.ERROR)
    check("EqualsHashCode", CheckSeverity.ERROR)
    check("FallThrough", CheckSeverity.ERROR)
    check("UnusedVariable", CheckSeverity.ERROR)
    check("DoNotCall", CheckSeverity.ERROR)
    check("StreamToString", CheckSeverity.ERROR)
  }
}
```

## 38.7 Run NullAway, and scope it with `NullAway:AnnotatedPackages`.

> Why? NullAway's entire model is that *your* code is null-annotated and the
> rest of the world is not. Without `AnnotatedPackages` it has no way to draw
> that line, so it either analyses nothing or drowns the build in findings
> about third-party return values it cannot reason about. Scoping it to your
> own package root makes every dereference inside that root a checked
> operation while treating library boundaries as unknown — which is exactly
> the contract [Chapter 25](25-nullability.md) describes.

```kotlin
// bad — NullAway on the classpath but never told what it owns
dependencies {
  errorprone("com.uber.nullaway:nullaway:0.12.3")
}

// good
dependencies {
  errorprone("com.google.errorprone:error_prone_core:2.36.0")
  errorprone("com.uber.nullaway:nullaway:0.12.3")
  implementation("org.jspecify:jspecify:1.0.0")
}

tasks.withType<JavaCompile>().configureEach {
  options.errorprone {
    check("NullAway", CheckSeverity.ERROR)
    option("NullAway:AnnotatedPackages", "com.example")
    option("NullAway:JSpecifyMode", "true")
    option("NullAway:HandleTestAssertionLibraries", "true")
  }
}
```

## 38.8 Wire the whole chain once, in the root Gradle build.

> Why? Configuring four plugins per module means four chances per module to
> get it wrong, and the module that gets it wrong is invisible until
> something ships from it. A single `subprojects` (or convention-plugin)
> block makes the configuration a property of the repository rather than of
> whoever created the module last.

```kotlin
// build.gradle.kts — the complete chain
import net.ltgt.gradle.errorprone.CheckSeverity
import net.ltgt.gradle.errorprone.errorprone

plugins {
  java
  checkstyle
  id("com.diffplug.spotless") version "7.0.2"
  id("net.ltgt.errorprone") version "4.1.0"
}

java {
  toolchain {
    languageVersion.set(JavaLanguageVersion.of(21))
  }
}

repositories {
  mavenCentral()
}

dependencies {
  errorprone("com.google.errorprone:error_prone_core:2.36.0")
  errorprone("com.uber.nullaway:nullaway:0.12.3")
  implementation("org.jspecify:jspecify:1.0.0")
}

spotless {
  java {
    target("src/*/java/**/*.java")
    googleJavaFormat("1.25.2")
    removeUnusedImports()
    formatAnnotations()
    toggleOffOn()
  }
}

checkstyle {
  toolVersion = "10.21.1"
  maxWarnings = 0
  isIgnoreFailures = false
}

tasks.withType<JavaCompile>().configureEach {
  options.encoding = "UTF-8"
  options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror"))
  options.errorprone {
    disableWarningsInGeneratedCode.set(true)
    excludedPaths.set(".*/build/generated/.*")
    check("MissingOverride", CheckSeverity.ERROR)
    check("ReferenceEquality", CheckSeverity.ERROR)
    check("EqualsHashCode", CheckSeverity.ERROR)
    check("FallThrough", CheckSeverity.ERROR)
    check("UnusedVariable", CheckSeverity.ERROR)
    check("DoNotCall", CheckSeverity.ERROR)
    check("StreamToString", CheckSeverity.ERROR)
    check("NullAway", CheckSeverity.ERROR)
    option("NullAway:AnnotatedPackages", "com.example")
  }
}
```

## 38.9 Wire the same four tools in Maven, with Error Prone through `annotationProcessorPaths`.

> Why? Error Prone is a `javac` plugin, not an annotation processor, so
> Maven needs three specific compiler arguments to load it —
> `-XDcompilePolicy=simple`, `--should-stop=ifError=FLOW`, and
> `-Xplugin:ErrorProne`. Omit any one and the build compiles cleanly while
> running no checks at all, which is the worst possible outcome: a green
> pipeline that enforces nothing.

```xml
<!-- bad — the plugin is on the processor path but javac never loads it -->
<plugin>
  <artifactId>maven-compiler-plugin</artifactId>
  <configuration>
    <annotationProcessorPaths>
      <path>
        <groupId>com.google.errorprone</groupId>
        <artifactId>error_prone_core</artifactId>
        <version>2.36.0</version>
      </path>
    </annotationProcessorPaths>
  </configuration>
</plugin>

<!-- good -->
<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-compiler-plugin</artifactId>
      <version>3.13.0</version>
      <configuration>
        <release>21</release>
        <compilerArgs>
          <arg>-XDcompilePolicy=simple</arg>
          <arg>--should-stop=ifError=FLOW</arg>
          <arg>-Xplugin:ErrorProne -Xep:NullAway:ERROR -XepOpt:NullAway:AnnotatedPackages=com.example</arg>
        </compilerArgs>
        <annotationProcessorPaths>
          <path>
            <groupId>com.google.errorprone</groupId>
            <artifactId>error_prone_core</artifactId>
            <version>2.36.0</version>
          </path>
          <path>
            <groupId>com.uber.nullaway</groupId>
            <artifactId>nullaway</artifactId>
            <version>0.12.3</version>
          </path>
        </annotationProcessorPaths>
      </configuration>
    </plugin>

    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-checkstyle-plugin</artifactId>
      <version>3.6.0</version>
      <dependencies>
        <dependency>
          <groupId>com.puppycrawl.tools</groupId>
          <artifactId>checkstyle</artifactId>
          <version>10.21.1</version>
        </dependency>
      </dependencies>
      <configuration>
        <configLocation>config/checkstyle/checkstyle.xml</configLocation>
        <consoleOutput>true</consoleOutput>
        <failOnViolation>true</failOnViolation>
        <violationSeverity>warning</violationSeverity>
        <includeTestSourceDirectory>true</includeTestSourceDirectory>
      </configuration>
      <executions>
        <execution>
          <id>checkstyle</id>
          <phase>verify</phase>
          <goals>
            <goal>check</goal>
          </goals>
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

Note that `maven-checkstyle-plugin` defaults `configLocation` to
`sun_checks.xml` and `violationSeverity` to `error`. Both defaults must be
overridden or the build enforces the wrong ruleset at the wrong threshold.

## 38.10 Make every tool fail the build.

> Why? A check that reports without failing is a check that gets ignored,
> and then a check that gets deleted six months later because "nobody looks
> at it." Gradle's Checkstyle plugin defaults `ignoreFailures` to `false` but
> leaves `maxWarnings` unbounded, so a ruleset whose modules emit at
> `warning` severity produces a green build with hundreds of findings. Set
> the severity to `error` in the ruleset and `maxWarnings = 0` in the build,
> so there is no gap between the two.

```kotlin
// bad — reports generated, nothing blocked
checkstyle {
  isIgnoreFailures = true
}

// good
checkstyle {
  toolVersion = "10.21.1"
  maxWarnings = 0
  maxErrors = 0
  isIgnoreFailures = false
}
```

## 38.11 Order the pipeline by fix cost: format, then compile, then Checkstyle, then tests.

> Why? Feedback should arrive cheapest-first. `spotlessCheck` runs in
> seconds and its fix is one command, so it belongs before anything that
> takes a minute. Error Prone and NullAway run inside compilation, so they
> cost nothing extra once you are compiling anyway. Checkstyle needs
> compiled output in Gradle's task graph. Tests are last because they are
> the slowest and because there is no point running them against code that
> will not merge.

```yaml
# bad — 12-minute test run, then a formatting failure
- run: ./gradlew test
- run: ./gradlew spotlessCheck checkstyleMain

# good — .github/workflows/ci.yml
- run: ./gradlew spotlessCheck
- run: ./gradlew compileJava compileTestJava   # Error Prone + NullAway
- run: ./gradlew checkstyleMain checkstyleTest
- run: ./gradlew test
```

## 38.12 Scope every `@SuppressWarnings` to the smallest possible declaration, and give it a comment.

> Why? `@SuppressWarnings` is legal on a class, and on a class it disables
> the check for every member — including members written years later by
> someone who never saw the annotation. Scoped to the one local variable or
> the one method that genuinely needs it, the suppression stays true as the
> code changes. The comment is what lets the next reader decide whether the
> suppression is still justified, which is the only question that matters
> when they encounter one.

```java
// bad — suppresses unchecked for the entire class, forever
@SuppressWarnings("unchecked")
public final class TypeRegistry {
  private final Map<Class<?>, Object> instances = new HashMap<>();

  <T> T get(Class<T> type) {
    return (T) instances.get(type);
  }

  <T> void put(Class<T> type, T instance) {
    instances.put(type, instance);
  }
}

// good — one statement, with the proof the cast is safe
public final class TypeRegistry {
  private final Map<Class<?>, Object> instances = new HashMap<>();

  <T> T get(Class<T> type) {
    // Safe: put() is the only writer and it stores a value of exactly
    // `type` under the key `type`, so the map is heterogeneously typed.
    @SuppressWarnings("unchecked")
    T instance = (T) instances.get(type);
    return instance;
  }

  <T> void put(Class<T> type, T instance) {
    instances.put(type, type.cast(instance));
  }
}
```

## 38.13 Never write `@SuppressWarnings("all")` or a bare `// CHECKSTYLE:OFF`.

> Why? Both silence *every* check over their scope, including checks that
> did not exist when the suppression was written. The failure mode is
> specific and nasty: a new NullAway or Error Prone check is added to the
> build, finds a genuine bug inside the suppressed region, and reports
> nothing. A suppression that names its target degrades gracefully; one that
> does not becomes a permanent blind spot.

```java
// bad — a blanket amnesty over 60 lines
// CHECKSTYLE:OFF
public void reconcile(Ledger ledger) {
  // ...
}
// CHECKSTYLE:ON

// bad
@SuppressWarnings("all")
private void legacyPath() {}

// good — one check, one reason, smallest possible span
// CHECKSTYLE.OFF: AbbreviationAsWordInName - IBAN and BIC are ISO terms
public String buildIBANFromBIC(String bic) {
  // ...
}
// CHECKSTYLE.ON: AbbreviationAsWordInName
```

## 38.14 Configure the comment filter so a `// CHECKSTYLE:OFF` is *required* to name its check.

> Why? A policy nobody can violate is better than a policy nobody remembers.
> Checkstyle's `SuppressionCommentFilter` defaults to `CHECKSTYLE:OFF` and
> `CHECKSTYLE:ON` with no check name at all, which is the unscoped form 38.13
> bans. Reconfiguring `offCommentFormat` with a capture group and feeding it
> to `checkFormat` makes a bare directive simply stop working, so the rule
> enforces itself.

```xml
<!-- bad — the default format; a bare CHECKSTYLE:OFF disables everything -->
<module name="SuppressionCommentFilter"/>

<!-- good — the directive must name a check, and the trailing text
     documents why (inside TreeWalker) -->
<module name="SuppressionCommentFilter">
  <property name="offCommentFormat" value="CHECKSTYLE.OFF: ([\w|]+)"/>
  <property name="onCommentFormat" value="CHECKSTYLE.ON: ([\w|]+)"/>
  <property name="checkFormat" value="$1"/>
</module>
```

## 38.15 Prefer `@SuppressWarnings` to comment filters wherever the check supports it.

> Why? An annotation is attached to a declaration, so it moves with the code,
> survives refactoring, and is visible in the IDE at the point of use. A
> comment pair is attached to line numbers, so an edit between the `OFF` and
> the `ON` silently widens its scope, and a deleted `ON` silently disables
> the check for the rest of the file. Checkstyle supports the annotation via
> `SuppressWarningsFilter` + `SuppressWarningsHolder` (see 38.4), Error Prone
> supports it natively with the check name as the value, and NullAway honours
> `@SuppressWarnings("NullAway")`.

```java
// bad — line-based, and the ON was lost in a merge
// CHECKSTYLE.OFF: MethodName - JNI naming
public native void Java_com_example_Native_init();

// good — declaration-scoped, moves with the method
@SuppressWarnings("checkstyle:MethodName") // JNI requires this exact spelling
public native void Java_com_example_Native_init();

// good — Error Prone check names work the same way
@SuppressWarnings("ReferenceEquality") // interned sentinel; identity is the contract
boolean isSentinel(String value) {
  return value == SENTINEL;
}
```

## 38.16 Exclude generated code by path, never by suppression.

> Why? Generated sources — protobuf stubs, MapStruct mappers, OpenAPI
> clients, jOOQ classes — follow the generator's conventions, not yours, and
> you cannot fix a finding in a file that is rewritten on every build.
> Suppressing per-file means the suppressions are also regenerated away.
> Excluding by path removes the whole tree from analysis in one place, and
> keeps the exclusion visible in the build script rather than scattered
> through machine-written files.

```kotlin
// bad — @SuppressWarnings injected into a template, or a per-file
// suppressions entry that the next codegen run invalidates

// good — one path exclusion per tool
tasks.withType<Checkstyle>().configureEach {
  exclude("**/generated/**")
}

tasks.withType<JavaCompile>().configureEach {
  options.errorprone {
    disableWarningsInGeneratedCode.set(true)
    excludedPaths.set(".*/(build|target)/generated/.*")
  }
}

spotless {
  java {
    targetExclude("**/generated/**")
  }
}
```

## 38.17 Relax test-source rules deliberately, in one place, and only where the relaxation is justified.

> Why? Test code has different tradeoffs — a missing Javadoc on a
> `@Test` method costs nothing, and an assertion DSL relies on static imports
> the production ruleset would question. But the relaxation must be a
> decision recorded in the build, not an accident of `checkstyleTest` never
> having been wired up. Correctness checks stay on: a `ReferenceEquality`
> bug in a test produces a test that passes for the wrong reason, which is
> worse than a failing test.

```kotlin
// bad — tests silently unchecked because nobody added the task to `check`
tasks.named("check") {
  dependsOn("checkstyleMain")
}

// good — tests are checked, with a named, narrower ruleset
tasks.named<Checkstyle>("checkstyleTest") {
  configFile = rootProject.file("config/checkstyle/checkstyle-test.xml")
}
```

`checkstyle-test.xml` should differ from the main ruleset only by dropping
the Javadoc-presence modules (`MissingJavadocType`, `MissingJavadocMethod`).
Everything else — naming, imports, structure — stays.

## 38.18 Pin every tool version, and upgrade each in its own commit.

> Why? Each of these tools changes what it flags between releases. An
> unpinned Checkstyle or Error Prone means a build that passed yesterday
> fails today with no local change, and the developer who hits it has no way
> to tell a new check from a regression they caused. Pinning turns every
> upgrade into a reviewable diff whose whole content is "these findings are
> new."

```kotlin
// bad — three floating versions, three sources of unreproducible failure
plugins {
  id("com.diffplug.spotless")
  id("net.ltgt.errorprone")
}
checkstyle { /* toolVersion left at the Gradle default */ }

// good — every version explicit, in the version catalog where possible
plugins {
  id("com.diffplug.spotless") version "7.0.2"
  id("net.ltgt.errorprone") version "4.1.0"
}

checkstyle {
  toolVersion = "10.21.1"
}

dependencies {
  errorprone("com.google.errorprone:error_prone_core:2.36.0")
  errorprone("com.uber.nullaway:nullaway:0.12.3")
}
```

## 38.19 Never enforce the same rule in two tools.

> Why? Two tools checking one rule produce two findings for one defect, two
> suppression sites when it needs waiving, and — when their definitions
> diverge slightly — a state where satisfying one violates the other.
> `MissingOverride` is the canonical trap: Checkstyle's version fires only
> when `{@inheritDoc}` is present, Error Prone's fires whenever the
> annotation is legal. They are not the same check, and running both means
> the weaker one contributes nothing but noise. Pick the tool with the most
> information — which for anything semantic is Error Prone — and disable the
> other.

```xml
<!-- bad — a strictly weaker duplicate of Error Prone's MissingOverride -->
<module name="TreeWalker">
  <module name="MissingOverride"/>
  <module name="EqualsHashCode"/>
  <module name="FallThrough"/>
</module>

<!-- good — leave all three to Error Prone, which sees the type hierarchy -->
<module name="TreeWalker">
  <!-- MissingOverride, EqualsHashCode, FallThrough: owned by Error Prone -->
</module>
```

## 38.20 Read `Violation` and `Suggestion` as claims about tooling, not about importance.

> Why? Throughout this skill, **Violation** means "some tool in the chain
> above fails the build on this," and **Suggestion** means "no tool can
> mechanically verify this, so it is a review judgement." The distinction is
> about *enforceability*, not severity — several of the most consequential
> rules in the guide are Suggestions precisely because no analyser can judge
> them. Treating Suggestions as optional is the misreading this rule exists
> to prevent: a Suggestion is the class of rule that needs a human reviewer
> most, because nothing else will catch it.

```java
// Violation — checkstyle/AvoidStarImport fails the build
import java.util.*;

// Suggestion — no tool can tell that this class-content ordering is
// chronological rather than logical (Chapter 2, rule 2.18). A reviewer can.
public final class OrderService {
  private BigDecimal applyDiscount(Order order) { /* ... */ }
  public Order place(NewOrder request) { /* ... */ }
  private final OrderRepository repository;
}
```

## 38.21 Adopt the chain on a legacy codebase with a frozen baseline, never with `ignoreFailures`.

> Why? Turning the tools on against an existing codebase produces thousands
> of findings, and the only two survivable responses are "fix them all first"
> or "grandfather what exists and block anything new." `ignoreFailures =
> true` is neither: it enforces nothing while looking like it does, and it
> never gets turned off. A checked-in `suppressions.xml` covering exactly
> today's findings is a debt register — it shrinks, it is reviewable, and
> every line in it is a to-do with a file name attached.

```kotlin
// bad — enforces nothing, and will still be here in two years
checkstyle {
  isIgnoreFailures = true
  maxWarnings = 2000
}

// good — new code is fully enforced; the baseline is visible and shrinking
checkstyle {
  isIgnoreFailures = false
  maxWarnings = 0
}
```

```xml
<?xml version="1.0"?>
<!DOCTYPE suppressions PUBLIC
    "-//Checkstyle//DTD SuppressionFilter Configuration 1.2//EN"
    "https://checkstyle.org/dtds/suppressions_1_2.dtd">
<!-- config/checkstyle/suppressions.xml — generated once, then only ever
     shrinks; every entry is a tracked to-do -->
<suppressions>
  <suppress files="[/\\]legacy[/\\]LedgerImporter\.java$"
            checks="MissingJavadocMethod|AbbreviationAsWordInName"/>
</suppressions>
```

For the formatter, Spotless's `ratchetFrom("origin/main")` is the equivalent
mechanism — see [§1.15](01-formatting-and-tooling.md). Both are temporary by
construction: the baseline file and the ratchet should be deleted once the
tree is clean.
