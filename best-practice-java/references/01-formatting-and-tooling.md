<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 1. Formatting & Tooling

Java's formatting debate is over, and a tool settled it rather than a vote.
[Google Java Style §4](https://google.github.io/styleguide/javaguide.html#s4-formatting)
— [braces](https://google.github.io/styleguide/javaguide.html#s4.1-braces),
[block indentation](https://google.github.io/styleguide/javaguide.html#s4.2-block-indentation),
the [column limit](https://google.github.io/styleguide/javaguide.html#s4.4-column-limit),
[line wrapping](https://google.github.io/styleguide/javaguide.html#s4.5-line-wrapping),
[horizontal alignment](https://google.github.io/styleguide/javaguide.html#s4.6.3-horizontal-alignment),
and [whitespace](https://google.github.io/styleguide/javaguide.html#s4.6-whitespace)
— is implemented in full by
[`google-java-format`](https://github.com/google/google-java-format). The
formatter parses the file, discards its existing layout entirely, and
re-emits one canonical rendering. There is no config file, no width knob, no
"our team prefers" escape hatch. That is the entire point.

This chapter documents the chain that runs the formatter, and the small
residue of §4 that the formatter deliberately does **not** repair — braces
around single-statement bodies and one-variable-per-declaration are AST
changes, and a layout formatter refuses to make them. Those two rules stay
yours, and Checkstyle catches them.

Everything the formatter owns is stated once here and never re-litigated in
prose anywhere else in this skill. Every code sample in every chapter is
written as `google-java-format` would emit it. This is the same delegation
[`best-practice-go`](../../best-practice-go/references/01-formatting.md)
makes to `gofmt` and `best-practice-ts` makes to Prettier.

Formatting is not static analysis. Naming, Javadoc presence, import hygiene,
bug patterns, and null contracts are a separate tool chain with a separate
failure mode — see [Chapter 38](38-static-analysis-configuration.md).

**Tool alignment:** the rules below are enforced by `spotlessCheck` (Gradle)
/ `spotless:check` (Maven) running the `googleJavaFormat` step. The two AST
rules the formatter cannot fix are enforced by Checkstyle `NeedBraces` and
`MultipleVariableDeclarations`.

## 1.1 Run `google-java-format` on every file before it is committed.

> Why? The formatter produces exactly one layout for a given AST, so two
> engineers writing the same logic produce byte-identical files. That kills
> whitespace-only diffs, keeps `git blame` meaningful, and removes an entire
> category of review comment. Unformatted code is also a reliable signal
> that the author never ran the project's tool chain at all.
> **Violation — enforced by `spotlessCheck`.**

```java
// bad — hand-laid-out; the formatter rewrites every line of this
public final class Rates {
    public static BigDecimal convert(BigDecimal amount,Currency from,Currency to)
    {
        if(amount.signum()<0) throw new IllegalArgumentException("negative amount");
        return amount.multiply( rateFor(from,to) );
    }
}

// good — exactly what google-java-format emits
public final class Rates {
  public static BigDecimal convert(BigDecimal amount, Currency from, Currency to) {
    if (amount.signum() < 0) {
      throw new IllegalArgumentException("negative amount");
    }
    return amount.multiply(rateFor(from, to));
  }
}
```

## 1.2 Drive the formatter through Spotless in Gradle, not a hand-rolled `Exec` task.

> Why? Spotless gives you `spotlessApply` and `spotlessCheck` as ordinary
> Gradle tasks, wires `spotlessCheck` into `check` automatically, caches
> results so unchanged files are skipped, and resolves the formatter from
> Maven Central so nobody has to install a binary. A hand-rolled `Exec` task
> reimplements all of that badly and silently drifts between developer
> machines and CI.

```kotlin
// bad — a local binary nobody has, no caching, no check task
tasks.register<Exec>("format") {
  commandLine("google-java-format", "-r", "src/main/java")
}

// good — build.gradle.kts
plugins {
  java
  id("com.diffplug.spotless") version "7.0.2"
}

spotless {
  java {
    target("src/*/java/**/*.java")
    googleJavaFormat("1.25.2")
    removeUnusedImports()
    formatAnnotations()
    licenseHeaderFile(rootProject.file("config/spotless/license-header.txt"))
  }
}
```

## 1.3 Wire the same step in Maven and bind `spotless:check` to the `verify` phase.

> Why? An unbound Spotless plugin is a plugin nobody runs. Binding `check`
> to `verify` means `mvn verify` — and therefore every CI pipeline that
> already runs it — fails on unformatted source without any extra CI step to
> forget. `apply` stays unbound so it is always an explicit, deliberate act.

```xml
<!-- bad — plugin declared but never bound; mvn verify passes on unformatted code -->
<plugin>
  <groupId>com.diffplug.spotless</groupId>
  <artifactId>spotless-maven-plugin</artifactId>
  <version>2.44.0</version>
</plugin>

<!-- good -->
<plugin>
  <groupId>com.diffplug.spotless</groupId>
  <artifactId>spotless-maven-plugin</artifactId>
  <version>2.44.0</version>
  <configuration>
    <java>
      <googleJavaFormat>
        <version>1.25.2</version>
        <style>GOOGLE</style>
      </googleJavaFormat>
      <removeUnusedImports/>
      <trimTrailingWhitespace/>
      <endWithNewline/>
    </java>
  </configuration>
  <executions>
    <execution>
      <goals>
        <goal>check</goal>
      </goals>
      <phase>verify</phase>
    </execution>
  </executions>
</plugin>
```

## 1.4 Pin the `google-java-format` version explicitly.

> Why? The formatter's output changes between releases — new wrapping
> heuristics, new language constructs, bug fixes in how it lays out records
> and switch expressions. An unpinned step means one developer's
> `spotlessApply` reflows files another developer's version had already
> formatted, producing a diff war that nobody can resolve. Pin it, upgrade it
> in its own commit, and reformat the whole tree in that same commit.

```kotlin
// bad — version floats; two machines produce two different layouts
spotless {
  java {
    googleJavaFormat()
  }
}

// good — pinned, upgraded deliberately
spotless {
  java {
    googleJavaFormat("1.25.2")
  }
}
```

Note that recent `google-java-format` releases require **JDK 21 or newer to
run**, which is not a constraint on the language level of the code being
formatted — it will still format Java 8 sources happily.

## 1.5 Accept +2-space block indentation and +4-space continuation indentation.

> Why?
> [§4.2](https://google.github.io/styleguide/javaguide.html#s4.2-block-indentation)
> fixes block indent at two spaces and
> [§4.5.2](https://google.github.io/styleguide/javaguide.html#s4.5.2-line-wrapping-indent)
> fixes continuation indent at "at least +4". Hand-picking a different
> indent, or re-indenting a continuation line to line up under an opening
> paren, is the single most common way a file drifts out of formatter
> agreement and starts producing noisy diffs on every subsequent edit.
> **Violation — enforced by `spotlessCheck`.**

```java
// bad — 4-space blocks, continuation aligned under the paren
public Order place(Customer customer,
                   List<LineItem> items,
                   Address shipTo,
                   PaymentMethod paymentMethod) {
    return new Order(customer, items, shipTo, paymentMethod);
}

// good — +2 block, +4 continuation (this signature is 103 columns on one
// line, so the formatter genuinely has to wrap it)
public Order place(
    Customer customer, List<LineItem> items, Address shipTo, PaymentMethod paymentMethod) {
  return new Order(customer, items, shipTo, paymentMethod);
}
```

## 1.6 Accept the 100-column limit; never hand-wrap to a narrower width.

> Why?
> [§4.4](https://google.github.io/styleguide/javaguide.html#s4.4-column-limit)
> sets the limit at 100 characters, and the formatter chooses the break
> points that keep the highest syntactic level intact
> ([§4.5.1](https://google.github.io/styleguide/javaguide.html#s4.5.1-line-wrapping-where-to-break)).
> Hand-wrapping to 80 "for the side-by-side diff view" produces line breaks
> the formatter will immediately undo, so the change never survives the next
> `spotlessApply`. Import statements and text-block contents are explicitly
> exempt from the limit
> ([§3.3.2](https://google.github.io/styleguide/javaguide.html#s3.3.2-import-line-wrapping),
> [§4.8.9](https://google.github.io/styleguide/javaguide.html#s4.8.9-text-blocks)).

```java
// bad — hand-wrapped to ~72 columns; the formatter rejoins these
var result =
    repository
        .findByStatus(
            Status.ACTIVE);

// good — fits in 100 columns, so it stays on one line
var result = repository.findByStatus(Status.ACTIVE);
```

## 1.7 Never hand-align code horizontally.

> Why?
> [§4.6.3](https://google.github.io/styleguide/javaguide.html#s4.6.3-horizontal-alignment)
> states that horizontal alignment "is permitted, but is never required by
> Google Style," and the guide immediately notes that maintaining it forces
> unrelated lines to change when one identifier is renamed. `google-java-format`
> resolves the ambiguity by never producing alignment, so any you add by hand
> is deleted on the next run. The practical cost of alignment is that a
> one-character rename produces a five-line diff.
> **Violation — enforced by `spotlessCheck`.**

```java
// bad — aligned by hand; renaming `id` reflows all three lines
private final UUID   id;
private final String displayName;
private final int    retryCount;

// good — single space after the type, always
private final UUID id;
private final String displayName;
private final int retryCount;
```

## 1.8 Write braces on `if`, `else`, `for`, `do`, and `while` yourself — the formatter will not add them.

> Why?
> [§4.1.1](https://google.github.io/styleguide/javaguide.html#s4.1.1-braces-always-used)
> requires braces "even when the body is empty or contains only a single
> statement." Adding a brace changes the AST, so `google-java-format` — a
> pure layout formatter — leaves a braceless body alone. This is the classic
> `goto fail;` shape: appending a second statement to a braceless body
> silently detaches it from the condition. Lambda braces stay optional.
> **Violation — enforced by `checkstyle/NeedBraces`.**

```java
// bad — formatter accepts this; adding a second line silently breaks it
if (token == null) return Optional.empty();

for (var item : items) total = total.add(item.price());

// good
if (token == null) {
  return Optional.empty();
}

for (var item : items) {
  total = total.add(item.price());
}

// good — lambda braces remain optional per §4.1.1
items.forEach(item -> total.add(item.price()));
```

## 1.9 Declare one variable per declaration — the formatter will not split `int a, b;`.

> Why?
> [§4.8.2.1](https://google.github.io/styleguide/javaguide.html#s4.8.2.1-variables-per-declaration)
> is explicit: "declarations such as `int a, b;` are not used." Like braces,
> splitting a multi-variable declarator is an AST change the formatter won't
> make. Combined declarations also hide the C array-declaration trap, where
> `int[] a, b;` declares two arrays but `int a[], b;` declares one array and
> one `int`. A `for` loop header is the documented exception.
> **Violation — enforced by `checkstyle/MultipleVariableDeclarations`.**

```java
// bad — passes the formatter untouched
int retries = 0, backoffMillis = 100;
String[] names, aliases;

// good
int retries = 0;
int backoffMillis = 100;
String[] names;
String[] aliases;

// good — for-loop headers are the documented exception
for (int i = 0, n = items.size(); i < n; i++) {
  process(items.get(i));
}
```

## 1.10 Let the formatter own import ordering and unused-import removal.

> Why? `google-java-format` sorts imports into the two ASCII-ordered groups
> [§3.3.3](https://google.github.io/styleguide/javaguide.html#s3.3.3-import-ordering-and-spacing)
> requires and strips imports the file no longer references. Configuring a
> *different* order — an `importOrder()` step with custom groups, or an
> IDE-specific scheme — puts two tools in disagreement, and whichever runs
> last wins. Pick the formatter's order and delete the competing config. The
> import rules themselves are covered in
> [Chapter 2](02-source-file-structure.md).

```kotlin
// bad — a custom importOrder fights googleJavaFormat's own sorting
spotless {
  java {
    importOrder("java", "javax", "org", "com", "")
    googleJavaFormat("1.25.2")
  }
}

// good — googleJavaFormat sorts; removeUnusedImports is complementary,
// not competing
spotless {
  java {
    googleJavaFormat("1.25.2")
    removeUnusedImports()
  }
}
```

## 1.11 Know which way your chain sets long-string reflowing, and set it once.

> Why? The CLI and the Spotless step are opposite-polarity switches for the
> same behaviour: `google-java-format` reflows long string literals by
> default and `--skip-reflowing-long-strings` turns that off, while Spotless
> leaves reflowing off until you chain `.reflowLongStrings()`. Assuming the
> wrong default means a developer running the CLI locally and CI running
> Spotless disagree about a file that neither of them will admit is
> unformatted. Prefer text blocks
> ([§4.8.9](https://google.github.io/styleguide/javaguide.html#s4.8.9-text-blocks),
> [Chapter 21](21-strings-and-text-blocks.md)) over long concatenated
> literals and the question mostly disappears.

```kotlin
// bad — local CLI reflows, CI's Spotless does not; the file oscillates
// (developer runs: google-java-format -r Foo.java)
spotless { java { googleJavaFormat("1.25.2") } }

// good — reflowing enabled explicitly so both paths agree
spotless {
  java {
    googleJavaFormat("1.25.2").reflowLongStrings()
  }
}
```

## 1.12 Use the AOSP variant only in an AOSP or Android codebase, and choose it once for the whole repository.

> Why? `--aosp` (Spotless: `.aosp()`) switches block indentation from two
> spaces to four and changes nothing else; the 100-column limit and every
> other §4 rule are identical. It exists so Android platform code matches
> the AOSP style guide, not as a preference dial. Mixing the two variants
> across modules of one repository means every cross-module move produces a
> full-file reformat.

```kotlin
// bad — module-by-module divergence
// :core/build.gradle.kts
spotless { java { googleJavaFormat("1.25.2") } }
// :app/build.gradle.kts
spotless { java { googleJavaFormat("1.25.2").aosp() } }

// good — one decision, applied from the root project
subprojects {
  apply(plugin = "com.diffplug.spotless")
  configure<com.diffplug.gradle.spotless.SpotlessExtension> {
    java {
      googleJavaFormat("1.25.2")
    }
  }
}
```

## 1.13 Leave Javadoc formatting on.

> Why? The formatter reflows Javadoc paragraphs and normalizes block-tag
> layout to match
> [§7.1](https://google.github.io/styleguide/javaguide.html#s7.1-javadoc-formatting),
> which is one fewer thing for a reviewer to check by eye. Turning it off
> with `--skip-javadoc-formatting` (Spotless: `.skipJavadocFormatting()`) is
> justified only when the codebase contains hand-laid-out Javadoc that the
> reflow would destroy — ASCII tables, aligned parameter lists — and that
> content usually belongs in a `<pre>` block anyway. Javadoc *content* rules
> are [Chapter 4](04-javadoc.md).

```java
// bad — hand-wrapped Javadoc drifts from §7.1 with no tool keeping it honest
/**
 * Converts an amount between currencies
 *      using the rate table
 *   loaded at startup.
 */
BigDecimal convert(BigDecimal amount, Currency from, Currency to);

// good — the formatter reflows this to a consistent shape
/**
 * Converts an amount between currencies using the rate table loaded at startup.
 *
 * @param amount the amount to convert, never negative
 * @param from the source currency
 * @param to the target currency
 * @return the converted amount
 */
BigDecimal convert(BigDecimal amount, Currency from, Currency to);
```

## 1.14 Run `spotlessApply` before every commit and `spotlessCheck` in CI.

> Why? `spotlessApply` is the write path and `spotlessCheck` is the read-only
> gate. Running only the gate means every developer discovers formatting
> failures after pushing; running only the write path means an unformatted
> file can still reach `main` through a machine that skipped it. Both, always,
> in that order. Gradle's `check` task already depends on `spotlessCheck`, so
> `./gradlew build` covers CI without an extra step.

```bash
# bad — CI is the first place anyone learns the file was unformatted
./gradlew test

# good — local write path
./gradlew spotlessApply

# good — CI read-only gate (implied by `check`, stated here for clarity)
./gradlew spotlessCheck build
```

A pre-commit hook makes the local half automatic:

```bash
#!/bin/sh
# .git/hooks/pre-commit
./gradlew --quiet spotlessApply || exit 1
staged=$(git diff --cached --name-only --diff-filter=ACM -- '*.java')
[ -z "$staged" ] || printf '%s\n' "$staged" | xargs git add
```

## 1.15 Introduce the formatter in one isolated commit and add that commit to `.git-blame-ignore-revs`.

> Why? Adopting the formatter on an existing codebase touches every file
> once. Doing it inside a feature branch buries the real change in thousands
> of whitespace lines and makes the review worthless. Doing it as its own
> commit and registering that commit's SHA in `.git-blame-ignore-revs` means
> `git blame` skips straight past it to the commit that actually wrote the
> line.

```bash
# bad — reformat mixed into a behavioural change
git commit -am "add retry logic and format the repo"

# good
./gradlew spotlessApply
git commit -am "chore: apply google-java-format across the repository"
git rev-parse HEAD >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

When a single reformat genuinely cannot be merged — a long-lived release
branch, a repository with hundreds of open pull requests — use Spotless's
ratchet instead, and treat it as temporary:

```kotlin
spotless {
  ratchetFrom("origin/main")
  java {
    googleJavaFormat("1.25.2")
  }
}
```

## 1.16 Use `// spotless:off` only for genuinely tabular data, and turn it back on immediately.

> Why? The `toggleOffOn()` step exists for the rare case where layout carries
> meaning — a lookup table, a matrix literal, an ASCII diagram in a comment.
> Every other use is somebody preserving a personal preference, and it
> compounds: the disabled region stops receiving every future formatter
> improvement and becomes the one part of the file nobody dares touch. Keep
> the region to the smallest possible span.

```java
// bad — whole class excluded because the author dislikes the wrapping
// spotless:off
public final class OrderService {
  // ... 400 lines the formatter never sees again ...
}
// spotless:on

// good — three lines where the column layout is the documentation
// spotless:off
private static final int[][] KERNEL = {
  {1, 0, -1},
  {2, 0, -2},
  {1, 0, -1},
};
// spotless:on
```

Enable the directive explicitly, or it is inert:

```kotlin
spotless {
  java {
    toggleOffOn()
    googleJavaFormat("1.25.2")
  }
}
```

## 1.17 Configure format-on-save so the formatter is never a manual step.

> Why? Any workflow that relies on a human remembering a command fails under
> deadline pressure, and the failure mode — a pull request full of
> whitespace noise — costs a reviewer's time rather than the author's.
> IntelliJ IDEA has an official `google-java-format` plugin that runs the
> real formatter. VS Code's Java extension (`redhat.java`) does not: it
> formats through an Eclipse formatter profile, and the closest available
> profile is
> [`eclipse-java-google-style.xml`](https://github.com/google/styleguide/blob/gh-pages/eclipse-java-google-style.xml)
> from Google's styleguide repository, which *approximates* the formatter
> rather than reproducing it. Either way the editor config should be a
> checked-in file so a new contributor inherits the setup instead of
> discovering it — and `spotlessApply` stays authoritative, because it is
> the only path that runs `google-java-format` itself.

```jsonc
// bad — .vscode/settings.json absent; every contributor picks their own
// (or none, and the pre-commit hook rewrites their file after the fact)

// good — .vscode/settings.json, checked in. The referenced file is a
// checked-in copy of Google's eclipse-java-google-style.xml profile.
{
  "editor.formatOnSave": true,
  "java.format.settings.url": "config/eclipse/eclipse-java-google-style.xml",
  "[java]": {
    "editor.defaultFormatter": "redhat.java"
  }
}
```

## 1.18 Never spend a review comment on formatting.

> Why? Once the chain has run there is no formatting decision left to have
> an opinion about. "Add a blank line here," "align these," and "wrap this
> at 80" are not actionable against a formatted file — the author cannot
> comply without disabling the formatter. Every such comment displaces a
> comment about correctness or design, which is the only thing a human
> reviewer is actually better at than a tool.

```java
// bad — reviewer asks for a hand-adjustment the next spotlessApply undoes
// > "can you line up the arguments under the open paren?"
var order =
    orderFactory.create(customer, items, shipTo, PaymentMethod.CARD, promoCode);

// good — leave it; if the line is hard to read, the fix is a named
// intermediate variable, which is a design comment worth making
var payment = new PaymentDetails(PaymentMethod.CARD, promoCode);
var order = orderFactory.create(customer, items, shipTo, payment);
```

## 1.19 Do not push semantic rules into the formatter, or formatting rules into the linter.

> Why? The two tools fail differently. A formatter failure is always fixable
> by running one command, so it can block a build with zero human cost. A
> linter failure may require a design change, so it needs review and
> sometimes a suppression. Conflating them — a Checkstyle `Indentation` or
> `LineLength` module sitting alongside `googleJavaFormat` — produces
> failures that contradict each other, and the "fix" becomes disabling one
> tool. See [Chapter 38](38-static-analysis-configuration.md) for the full
> division of labour.

```xml
<!-- bad — Checkstyle re-litigating what the formatter already owns -->
<module name="TreeWalker">
  <module name="Indentation">
    <property name="basicOffset" value="4"/>
  </module>
  <module name="LineLength">
    <property name="max" value="80"/>
  </module>
</module>

<!-- good — Checkstyle only checks what a layout formatter cannot see -->
<module name="TreeWalker">
  <module name="NeedBraces"/>
  <module name="MultipleVariableDeclarations"/>
  <module name="AvoidStarImport"/>
  <module name="OverloadMethodsDeclarationOrder"/>
</module>
```
