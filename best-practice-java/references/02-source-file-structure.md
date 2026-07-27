<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 2. Source File Basics & Structure

Everything above the first `{` of a class is decided before any interesting
code is written, and it is almost entirely mechanical. This chapter covers
[Google Java Style §2](https://google.github.io/styleguide/javaguide.html#s2-source-file-basics)
(file name, encoding, special characters) and
[§3](https://google.github.io/styleguide/javaguide.html#s3-source-file-structure)
(license block, package statement, imports, class declaration) in full,
plus the two file kinds §3 treats specially — `package-info.java` and
`module-info.java`.

The *layout* of what is here — where blank lines fall, what column an import
wraps at — belongs to `google-java-format` and is settled in
[Chapter 1](01-formatting-and-tooling.md). What this chapter governs is
different: which imports may exist at all, how many top-level types a file
may hold, and in what order a class presents its members. A formatter has no
opinion on any of that.

Naming the types and members themselves is
[Chapter 3](03-naming.md). What goes *in* a Javadoc block is
[Chapter 4](04-javadoc.md). The `@SuppressWarnings` and header-comment
conventions referenced below are specified in
[Chapter 38](38-static-analysis-configuration.md).

**Tool alignment:** most of this chapter is mechanically enforced by
Checkstyle — `OuterTypeFilename`, `OneTopLevelClass`, `PackageDeclaration`,
`AvoidStarImport`, `UnusedImports`, `IllegalImport`, `NoLineWrap`,
`CustomImportOrder`, `OverloadMethodsDeclarationOrder`, `IllegalTokenText`,
`AvoidEscapedUnicodeCharacters`, `FileTabCharacter`, and
`NewlineAtEndOfFile` — plus Spotless's `removeUnusedImports()` and
`licenseHeader` steps.

## 2.1 Name the file after the single top-level type it contains, case-sensitively.

> Why?
> [§2.1](https://google.github.io/styleguide/javaguide.html#s2.1-file-name)
> requires that "the file name consists of the case-sensitive name of the
> top-level class (of which there is exactly one), plus the `.java`
> extension." A public type is *required* by the JLS to match, but a
> package-private one is not, and a mismatched package-private type is the
> version that actually bites: every tool that maps a stack-trace frame or a
> `git blame` line back to a file — IDE navigation, coverage reports, code
> search — silently fails to find it.
> **Violation — enforced by `checkstyle/OuterTypeFilename`.**

```java
// bad — file OrderUtils.java
class OrderHelper {}

// bad — file orderhelper.java; compiles on a case-insensitive filesystem,
// fails on Linux CI
class OrderHelper {}

// good — file OrderHelper.java
class OrderHelper {}
```

## 2.2 Encode every source file as UTF-8 and declare that encoding in the build.

> Why?
> [§2.2](https://google.github.io/styleguide/javaguide.html#s2.2-file-encoding)
> is one sentence: "Source files are encoded in UTF-8." Leaving the build to
> the platform default means `javac` reads the file as Windows-1252 on one
> machine and UTF-8 on another, so a `é` in a string literal or a Javadoc
> block compiles to two different values depending on who ran the build.
> That failure survives into a released artifact and is invisible in review.

```xml
<!-- bad — no encoding declared; javac uses the platform default -->
<properties>
  <maven.compiler.release>21</maven.compiler.release>
</properties>

<!-- good -->
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
</properties>
```

```kotlin
// good — build.gradle.kts
tasks.withType<JavaCompile>().configureEach {
  options.encoding = "UTF-8"
}
```

## 2.3 Use the ASCII horizontal space as the only whitespace character in the file.

> Why?
> [§2.3.1](https://google.github.io/styleguide/javaguide.html#s2.3.1-whitespace-characters)
> states that "aside from the line terminator sequence, the ASCII horizontal
> space character (0x20) is the only whitespace character that appears
> anywhere in a source file." Tabs render at a different width in every
> viewer, so a tab-indented file is unreadable in half the tools that open
> it. Worse, a non-breaking space (U+00A0) pasted from a document or a
> browser is invisible in the editor and produces a compiler error the author
> cannot see. Any tab inside a string literal must be written `\t`.
> **Violation — the tab half is enforced by `spotlessCheck`;**
> google-java-format never emits a tab, so a tab-indented file fails the
> format check. Checkstyle's `FileTabCharacter` enforces the same rule and
> is deliberately left out of the shipped ruleset because the formatter owns
> it (chapter 38). No linter catches a stray non-breaking space; that one
> surfaces as a `javac` "illegal character" error, because U+00A0 is not
> whitespace under the JLS.

```java
// bad — a literal tab character indents the body, and a literal tab
// sits inside the string
class Report {
	String header() {
		return "name	total";
	}
}

// good — spaces for indentation, \t for the tab that is actually data
class Report {
  String header() {
    return "name\ttotal";
  }
}
```

## 2.4 Use a special escape sequence rather than the equivalent octal or Unicode escape.

> Why?
> [§2.3.2](https://google.github.io/styleguide/javaguide.html#s2.3.2-special-escape-sequences)
> requires that "for any character that has a special escape sequence (`\b`,
> `\t`, `\n`, `\f`, `\r`, `\s`, `\"`, `\'` and `\\`), that sequence is used
> rather than the corresponding octal or Unicode escape." `\u000A` is not
> merely less readable than `\n` — a Unicode escape is decoded by the
> compiler *before* lexing, so a `\u000A` written inside a `//` comment
> terminates that comment and changes what the program does. Octal escapes
> carry the same readability cost with none of the danger, and no upside.
> **Violation — enforced by `checkstyle/IllegalTokenText` configured with
> Google's octal/Unicode-escape pattern.**

```java
// bad — \u0009 is a tab and \042 is a quote; neither is readable,
// and a \u escape is decoded before the compiler even splits lines
String row = "name\u0009total";
String quoted = "\042hello\042";

// good
String row = "name\ttotal";
String quoted = "\"hello\"";
```

## 2.5 Choose between a literal non-ASCII character and its Unicode escape on readability alone.

> Why?
> [§2.3.3](https://google.github.io/styleguide/javaguide.html#s2.3.3-non-ascii-characters)
> says the choice "depends only on which makes the code easier to read and
> understand," and adds that escaping a printable character makes the code
> *harder* to read. The genuinely useful case for an escape is the opposite:
> a character that is invisible or ambiguous on screen — a zero-width space,
> a non-breaking space, a right-to-left mark — where the escape plus a
> comment is the only honest rendering.
> **Violation — enforced by `checkstyle/AvoidEscapedUnicodeCharacters` with
> `allowEscapesForControlCharacters` and `allowByTailComment` enabled.**

```java
// bad — nobody can read this, and the file is already UTF-8
String unitAbbrev = "\u03bcs";

// bad — the escape is right, but the reader still has no idea what it is
return "\uFEFF" + payload;

// good — printable character written literally
String unitAbbrev = "μs";

// good — invisible character escaped, and explained in a trailing comment
return "\uFEFF" + payload; // U+FEFF byte-order mark, required by the consumer
```

## 2.6 Lay the file out in exactly four sections, in order, separated by one blank line each.

> Why?
> [§3](https://google.github.io/styleguide/javaguide.html#s3-source-file-structure)
> fixes the order — license or copyright information (if present), package
> statement, imports, exactly one top-level class — and specifies that
> "exactly one blank line separates each section that is present." Fixing the
> order means a reader scanning an unfamiliar file finds the package and the
> dependency surface in the same place every time, and a `git diff` of a
> header change never entangles with a diff of the imports.

```java
// bad — copyright below the package, two blank lines, imports interleaved
package com.example.billing;

/* Copyright 2026 Example Inc. */

import java.util.List;


import java.time.Instant;

public final class Invoice {}

// good
/*
 * Copyright 2026 Example Inc.
 *
 * Licensed under the Apache License, Version 2.0.
 */

package com.example.billing;

import java.time.Instant;
import java.util.List;

public final class Invoice {}
```

## 2.7 Put the license or copyright block first, and let tooling maintain it.

> Why?
> [§3.1](https://google.github.io/styleguide/javaguide.html#s3.1-copyright-statement)
> puts this block at the top of the file when it belongs there at all. A
> hand-maintained header drifts — the year stops updating, new files miss it
> entirely, and a license change becomes a manual edit of every file in the
> tree. Spotless's `licenseHeaderFile` step inserts and updates the block on
> `spotlessApply`, including the `$YEAR` token, so the header is generated
> rather than remembered.
> **Violation — enforced by `spotlessCheck` (`licenseHeader` step);
> `checkstyle/RegexpHeader` is the alternative when Spotless is not in the
> chain.**

```kotlin
// bad — nothing checks the header; half the tree has it, half does not
spotless {
  java {
    googleJavaFormat("1.25.2")
  }
}

// good
spotless {
  java {
    googleJavaFormat("1.25.2")
    licenseHeaderFile(rootProject.file("config/spotless/license-header.txt"))
  }
}
```

## 2.8 Give every source file a package statement, and never line-wrap it.

> Why?
> [§3.2](https://google.github.io/styleguide/javaguide.html#s3.2-package-statement)
> requires the package statement and exempts it from the 100-column limit —
> it is never wrapped no matter how long the package name grows. Omitting it
> puts the type in the unnamed package, where it is unreachable by any named
> package, invisible to the module system, and impossible to import.
> **Violation — presence is enforced by `checkstyle/PackageDeclaration`; the
> no-wrap half by `spotlessCheck`,** since google-java-format joins a wrapped
> package statement back onto one line. Checkstyle's `NoLineWrap` covers the
> same ground (its default token set includes `PACKAGE_DEF`, `IMPORT`,
> `STATIC_IMPORT`, and `MODULE_IMPORT`) and is left out of the shipped
> ruleset because the formatter owns it (chapter 38).

```java
// bad — wrapped to satisfy a column limit that does not apply here
package com.example.platform.billing.invoicing
    .reconciliation;

// good — one line, however long
package com.example.platform.billing.invoicing.reconciliation;
```

## 2.9 Never use a wildcard import.

> Why?
> [§3.3.1](https://google.github.io/styleguide/javaguide.html#s3.3.1-wildcard-imports)
> is absolute: "Wildcard ('on-demand') imports, static or otherwise, are not
> used." A wildcard hides the file's real dependency surface, so a reviewer
> cannot tell what a class depends on without compiling it. It is also a
> forward-compatibility hazard — when an upstream library adds a type whose
> simple name collides with one you already import by wildcard, a file that
> compiled yesterday stops compiling today, and the diff that broke it
> contains none of your code.
> **Violation — enforced by `checkstyle/AvoidStarImport`.**

```java
// bad — which of the ~60 types in java.util does this file actually need?
import java.util.*;
import static org.assertj.core.api.Assertions.*;

// good — static block first, then the non-static block, per 2.12
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import java.util.Map;
```

Spotless can guard this on the formatter side as well, so the failure
surfaces at `spotlessApply` time rather than in a later Checkstyle run.
The step is recent — it landed as `removeWildcardImports()` and was renamed
to `forbidWildcardImports()` in the Spotless 4.x core, so check what your
pinned plugin version actually exposes:

```kotlin
spotless {
  java {
    forbidWildcardImports()
    googleJavaFormat("1.25.2")
  }
}
```

## 2.10 Never use a module import.

> Why?
> [§3.3.1.1](https://google.github.io/styleguide/javaguide.html#s3.3.1.1-module-imports)
> states plainly: "Module imports are not used." An `import module M;`
> declaration pulls in every public type from every package that module
> exports, transitively — a wildcard import with a far larger and less
> predictable blast radius, and the same collision hazard as 2.9 multiplied
> across an entire module graph. Note that the syntax **does not exist in
> Java 21** at all: module import declarations were preview in Java 23
> ([JEP 476](https://openjdk.org/jeps/476)) and final only in Java 25
> ([JEP 511](https://openjdk.org/jeps/511)). The rule matters the moment a
> project's language level moves past 21, which is exactly when someone will
> reach for it.
> **Violation — `checkstyle/IllegalImport` rejects module imports by module
> name via its `illegalModules` property (added in Checkstyle 12.3.0), so
> the ban has to be spelled out module by module; there is no blanket
> "no module imports" switch. On a Java 21 language level the construct
> simply does not compile, so nothing enforces it there either.**

```java
// bad — does not compile on Java 21; on Java 25 it imports every public
// top-level type in every package java.base exports, plus everything
// reachable through its `requires transitive` edges
import module java.base;

var config = new HashMap<String, Path>();

// good — the same code with explicit imports, on any release
import java.nio.file.Path;
import java.util.HashMap;

var config = new HashMap<String, Path>();
```

## 2.11 Never line-wrap an import statement.

> Why?
> [§3.3.2](https://google.github.io/styleguide/javaguide.html#s3.3.2-import-line-wrapping)
> exempts imports from the column limit entirely, so a wrapped import is
> both non-conforming and pointless. It also breaks the one thing imports are
> good for: a wrapped import block cannot be sorted, diffed, or grepped line
> by line, so `git diff` on a dependency change becomes unreadable.
> **Violation — enforced by `spotlessCheck`,** which rejoins a wrapped import.
> Checkstyle's `NoLineWrap` enforces the same rule and is left out of the
> shipped ruleset because the formatter owns it (chapter 38).

```java
// bad
import com.example.platform.billing.reconciliation
    .LedgerReconciliationService;

// good
import com.example.platform.billing.reconciliation.LedgerReconciliationService;
```

## 2.12 Order imports as one static block then one non-static block, ASCII-sorted within each, with a single blank line between.

> Why?
> [§3.3.3](https://google.github.io/styleguide/javaguide.html#s3.3.3-import-ordering-and-spacing)
> specifies all static imports in one block, all non-static imports in one
> block, a single blank line between the two when both are present, and
> ASCII sort order within each block. Note that ASCII order is *not*
> case-insensitive alphabetical order: uppercase letters sort before
> lowercase, so `com.example.Foo` precedes `com.example.bar`. Deviating —
> the popular `java` / `javax` / `org` / `com` grouping, for instance —
> guarantees a merge conflict every time two branches add an import,
> because each side inserts into a different position.
> **Violation — enforced by `checkstyle/CustomImportOrder` and by
> `google-java-format`'s own import sorting.**

```java
// bad — java/javax/org/com grouping, blank lines between groups
import java.util.List;

import javax.sql.DataSource;

import org.slf4j.Logger;

import com.example.billing.Invoice;

import static java.util.Objects.requireNonNull;

// good — static block, blank line, non-static block, ASCII order within each
import static java.util.Objects.requireNonNull;
import static org.assertj.core.api.Assertions.assertThat;

import com.example.billing.Invoice;
import java.util.List;
import javax.sql.DataSource;
import org.slf4j.Logger;
```

## 2.13 Import a static nested class with an ordinary import, never a static import.

> Why?
> [§3.3.4](https://google.github.io/styleguide/javaguide.html#s3.3.4-import-class-not-static)
> is unambiguous: "Static import is not used for static nested classes. They
> are imported with normal imports." Java permits both spellings for a
> nested type, which means a codebase that allows the static form ends up
> importing the same type two different ways, and neither the sort order nor
> a text search for the import finds both. Static import is for static
> *members* — methods, constants — not for types.
> **Suggestion — no check distinguishes a static import of a type from a
> static import of a member.**

```java
// bad — Map.Entry is a nested type, not a static member
import static java.util.Map.Entry;

// good
import java.util.Map.Entry;
```

## 2.14 Keep static imports rare, and only where the bare name is unambiguous at the call site.

> Why? A static import removes the qualifier that tells a reader where a name
> came from. For `assertThat`, `requireNonNull`, or `Duration.ofSeconds`
> imported as `ofSeconds`, the trade is worth it in test code where the name
> is idiomatic and repeated hundreds of times. For a domain constant such as
> `MAX`, it is not: the reader now has to scroll to the import block to
> discover which of four classes it came from. Google's guide permits static
> imports without limiting them, so this is a judgement call, not a
> mechanical rule.
> **Suggestion — `checkstyle/AvoidStaticImport` can enforce an explicit
> allowlist via its `excludes` property if a project wants a hard line.**

```java
// bad — MAX and of() are context-free at the call site
import static com.example.billing.Limits.MAX;
import static java.time.Duration.of;

if (amount.compareTo(MAX) > 0) {
  throw new IllegalArgumentException("over limit");
}

// good — the qualifier carries the meaning
import com.example.billing.Limits;
import java.time.Duration;

if (amount.compareTo(Limits.MAX_INVOICE_TOTAL) > 0) {
  throw new IllegalArgumentException("over limit");
}

// good — an idiomatic, repeated assertion name in a test
import static org.assertj.core.api.Assertions.assertThat;

assertThat(invoice.total()).isEqualByComparingTo("42.00");
```

## 2.15 Delete unused imports rather than suppressing the warning.

> Why? An unused import is a stale claim about what the file depends on. It
> keeps a module edge alive in dependency analysis, blocks a package from
> being deleted, and makes a reviewer believe the file touches something it
> does not. This one is entirely mechanical — the formatter removes them, so
> there is no reason for one to survive to review.
> **Violation — enforced by `checkstyle/UnusedImports` and Spotless
> `removeUnusedImports()`.**

```java
// bad — LegacyLedger was deleted from this class two refactors ago
import com.example.billing.LegacyLedger;
import java.util.List;

public final class Invoice {
  private final List<LineItem> items;
}

// good
import java.util.List;

public final class Invoice {
  private final List<LineItem> items;
}
```

## 2.16 Never import from a package the project treats as internal or forbidden.

> Why? `sun.*`, `com.sun.*`, `jdk.internal.*`, and a library's own
> `*.internal.*` packages carry no compatibility guarantee. Code that
> reaches into them compiles today and fails on the next JDK or dependency
> bump, usually at runtime rather than at compile time, and usually in
> production. The same mechanism is the cheapest way to enforce an
> architectural boundary — banning `javax.persistence` from a domain module,
> say, so the boundary is a build failure rather than a review convention.
> **Violation — enforced by `checkstyle/IllegalImport`.**

```java
// bad — unsupported, and gone without notice on the next JDK
import sun.misc.Unsafe;

// bad — a Spring internal, not part of its public API
import org.springframework.util.ConcurrentReferenceHashMap;

// good
import java.lang.invoke.VarHandle;
import java.util.concurrent.ConcurrentHashMap;
```

```xml
<!-- config/checkstyle/checkstyle.xml -->
<module name="IllegalImport">
  <property name="illegalPkgs" value="sun, com.sun, jdk.internal"/>
</module>
```

## 2.17 Put exactly one top-level class in each file.

> Why?
> [§3.4.1](https://google.github.io/styleguide/javaguide.html#s3.4.1-one-top-level-class)
> requires that "each top-level class resides in a source file of its own."
> A package-private helper tucked below the public class in the same file is
> invisible to anyone navigating by type name, produces confusing stack
> traces (`Invoice.java` reporting a frame in `InvoiceMath`), and makes both
> types move together forever. If the helper is genuinely tied to its host,
> the right answer is a nested type, which is scoped explicitly and reads as
> intentional; if it is not, it deserves its own file.
> **Violation — enforced by `checkstyle/OneTopLevelClass`.**

```java
// bad — Invoice.java holds two top-level types
public final class Invoice {
  // ...
}

final class InvoiceMath {
  static BigDecimal total(List<LineItem> items) {
    return items.stream().map(LineItem::price).reduce(BigDecimal.ZERO, BigDecimal::add);
  }
}

// good — Invoice.java, with the helper nested and its scope explicit.
// Note the name: calling the nested type `Math` would shadow
// java.lang.Math for the whole of Invoice.
public final class Invoice {
  // ...

  private static final class Totals {
    static BigDecimal total(List<LineItem> items) {
      return items.stream().map(LineItem::price).reduce(BigDecimal.ZERO, BigDecimal::add);
    }
  }
}
```

## 2.18 Order class members by a logic you could explain out loud — never by when you wrote them.

> Why?
> [§3.4.2](https://google.github.io/styleguide/javaguide.html#s3.4.2-class-member-ordering)
> deliberately declines to mandate a recipe, and instead requires only that
> "each class uses some logical order, which its maintainer could explain if
> asked." It then names the failure mode explicitly: habitually appending new
> methods to the end of the class produces chronological-by-date-added order,
> which is not a logical order. Chronological order is what you get by
> default, and it is precisely the order that carries no information for a
> reader. Common defensible orders are public API first then private helpers,
> or lifecycle order (construct, configure, execute, close). Pick one per
> class and hold it.
> **Suggestion — no tool can judge whether an order is logical.**

```java
// bad — read top to bottom, this is the order the author happened to
// write things in over six months
public final class OrderService {
  private BigDecimal applyDiscount(Order order) { /* ... */ }
  public Order place(NewOrder request) { /* ... */ }
  private static final Logger log = LoggerFactory.getLogger(OrderService.class);
  public void cancel(UUID orderId) { /* ... */ }
  private final OrderRepository repository;
  OrderService(OrderRepository repository) { /* ... */ }
}

// good — constants, fields, constructor, public API, private helpers
public final class OrderService {
  private static final Logger log = LoggerFactory.getLogger(OrderService.class);

  private final OrderRepository repository;

  OrderService(OrderRepository repository) {
    this.repository = requireNonNull(repository);
  }

  public Order place(NewOrder request) {
    /* ... */
  }

  public void cancel(UUID orderId) {
    /* ... */
  }

  private BigDecimal applyDiscount(Order order) {
    /* ... */
  }
}
```

## 2.19 Keep overloads contiguous, with no other member between them.

> Why?
> [§3.4.2.1](https://google.github.io/styleguide/javaguide.html#s3.4.2.1-overloads-never-split)
> requires that multiple constructors, or multiple methods sharing a name,
> appear sequentially with no other code in between — not even a private
> field. Overload resolution is one of the least intuitive parts of Java, and
> the only way to reason about a call site is to see the whole overload set
> at once. A set split across 200 lines guarantees somebody adds a seventh
> overload that silently steals calls from the third.
> **Violation — enforced by `checkstyle/OverloadMethodsDeclarationOrder`.**

```java
// bad — the two of() overloads are separated by an unrelated member
public static Money of(BigDecimal amount, Currency currency) {
  return new Money(amount, currency);
}

public Money plus(Money other) {
  return of(amount.add(other.amount), currency);
}

public static Money of(String amount, Currency currency) {
  return of(new BigDecimal(amount), currency);
}

// good — the overload set reads as one unit
public static Money of(BigDecimal amount, Currency currency) {
  return new Money(amount, currency);
}

public static Money of(String amount, Currency currency) {
  return of(new BigDecimal(amount), currency);
}

public Money plus(Money other) {
  return of(amount.add(other.amount), currency);
}
```

## 2.20 Put package-level Javadoc and package-wide annotations in `package-info.java`.

> Why? `package-info.java` is the only place the language lets you annotate
> or document a package, and it is the natural home for the nullability
> default a whole package opts into. Scattering `@NullMarked` across every
> class in a package is 40 edits instead of one, and the first class that
> misses it becomes a silent hole in the null contract. See
> [Chapter 25](25-nullability.md) for the nullability rules themselves and
> [Chapter 4](04-javadoc.md) for the Javadoc conventions.
> **Suggestion — presence of `package-info.java` is a project convention,
> not a check.**

```java
// bad — repeated on every class in the package, and forgotten on one
@NullMarked
public final class Invoice {}

@NullMarked
public final class LineItem {}

public final class TaxRate {} // silently unannotated

// good — com/example/billing/package-info.java
/**
 * Invoice construction, line-item arithmetic, and tax application.
 *
 * <p>All types in this package are immutable and safe for concurrent use.
 */
@NullMarked
package com.example.billing;

import org.jspecify.annotations.NullMarked;
```

Note the unusual ordering: in `package-info.java` the annotation precedes
the `package` statement, and imports follow it.

## 2.21 Order `module-info.java` directives `requires`, `exports`, `opens`, `uses`, `provides`.

> Why?
> [§3.5.1](https://google.github.io/styleguide/javaguide.html#s3.5.1-ordering-module-directives)
> fixes the order as all `requires`, then all `exports`, then all `opens`,
> then all `uses`, then all `provides`, with "a single blank line separates
> each block that is present." A module declaration is the one file that
> states a component's entire public contract; interleaving the directive
> kinds means a reviewer has to read all of it to answer "what does this
> module expose?" rather than one block. Sorting within each block is *not*
> part of §3.5.1 — it is an additional convention worth adopting, so
> additions land in a predictable place and stop conflicting on merge.
> **Suggestion — no Checkstyle check covers module directive ordering.**

```java
// bad — interleaved, so no block answers a question on its own
module com.example.billing {
  requires java.sql;
  exports com.example.billing.api;
  requires org.slf4j;
  uses com.example.billing.spi.TaxProvider;
  exports com.example.billing.model;
  provides com.example.billing.spi.TaxProvider with com.example.billing.VatProvider;
  requires transitive com.example.money;
}

// good — one block per directive kind, sorted by module name within each
module com.example.billing {
  requires transitive com.example.money;
  requires java.sql;
  requires org.slf4j;

  exports com.example.billing.api;
  exports com.example.billing.model;

  uses com.example.billing.spi.TaxProvider;

  provides com.example.billing.spi.TaxProvider with com.example.billing.VatProvider;
}
```
