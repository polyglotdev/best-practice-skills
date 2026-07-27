# best-practice-java

An exhaustive, Airbnb-depth **Agent Skill** for writing and reviewing Java 21
LTS, including a full Spring Boot 3.x layer.

**798 numbered rules across 38 chapters, 27,119 lines.** Every rule is
justified with a `> Why?`, shown with `// bad` / `// good` code, and where a
tool can catch it, labeled `> Enforced by: <tool/check>`.

## The two Java skills

| Slash command | Skill | Shape | Purpose |
|---|---|---|---|
| `/best-practice-java` | `best-practice-java` (this repo) | **Authoring** | The rule corpus. Load when writing or reviewing Java. |
| `/java-google-best-practices` | `java-google-best-practices` (global) | **Audit** | The workflow for producing a structured findings report with `file:line` citations and Violation/Suggestion severities. |

This mirrors the Go pairing exactly: `best-practice-go` is the rule corpus,
`go-style-guide` is the audit workflow. One is the source of truth, the other
is the report generator. Load the authoring skill to write code; load the audit
skill to review a codebase and produce a report.

## Upstream sources, in precedence order

1. **[Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)** —
   normative for
   [naming (§5)](https://google.github.io/styleguide/javaguide.html#s5-naming),
   [programming practices (§6)](https://google.github.io/styleguide/javaguide.html#s6-programming-practices),
   [Javadoc (§7)](https://google.github.io/styleguide/javaguide.html#s7-javadoc),
   and [source file structure (§3)](https://google.github.io/styleguide/javaguide.html#s3-source-file-structure).
2. **Effective Java, 3rd Edition (Joshua Bloch)** — cited by item number for
   every design-level rule Google's guide deliberately leaves open.
3. **The [JLS](https://docs.oracle.com/javase/specs/) and
   [JDK 21 API docs](https://docs.oracle.com/en/java/javase/21/docs/api/)** —
   for records, sealed types, pattern matching, sequenced collections, and
   virtual threads, all of which postdate most of Google's guide.
4. **[Spring Framework](https://docs.spring.io/spring-framework/reference/) and
   [Spring Boot](https://docs.spring.io/spring-boot/index.html) reference docs** —
   for chapters 32 to 37 only.

All 196 style-guide links in the skill were verified to resolve against the
live page. Google's guide uses short-form anchors such as
`#s6.1-override-annotation` and `#s7.3.1-javadoc-exception-self-explanatory`,
and carries some legacy aliases; the corpus uses only anchors confirmed present
in the page source.

## Chapters

### Part I — Google Java Style Guide foundation

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 1 | Formatting & Tooling | 19 | 608 |
| 2 | Source File Basics & Structure | 21 | 728 |
| 3 | Naming | 20 | 649 |
| 4 | Javadoc | 24 | 902 |
| 5 | Comments & TODOs | 17 | 511 |
| 6 | Modifiers & Declaration Order | 21 | 621 |
| 7 | Programming Practices | 22 | 725 |

### Part II — Language core (Effective Java + JLS, Java 21)

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 8 | Object Creation | 16 | 627 |
| 9 | Object Lifecycle & Resources | 18 | 642 |
| 10 | `equals`, `hashCode`, `toString`, `Comparable` | 23 | 824 |
| 11 | Classes & Interfaces | 17 | 683 |
| 12 | Records | 19 | 621 |
| 13 | Sealed Types | 18 | 536 |
| 14 | Pattern Matching | 19 | 657 |
| 15 | Enums & Annotations | 18 | 729 |
| 16 | Generics | 20 | 677 |
| 17 | Lambdas & Method References | 20 | 577 |
| 18 | Streams | 25 | 679 |
| 19 | `Optional` | 22 | 591 |
| 20 | Collections | 23 | 709 |
| 21 | Strings & Text Blocks | 23 | 619 |
| 22 | Methods & Parameters | 24 | 808 |
| 23 | Control Structures & `switch` | 19 | 626 |
| 24 | Exceptions | 22 | 761 |
| 25 | Nullability | 20 | 656 |
| 26 | Concurrency Fundamentals | 28 | 1035 |
| 27 | Virtual Threads & Structured Concurrency | 22 | 645 |
| 28 | Dates & Times (`java.time`) | 23 | 651 |
| 29 | Numeric Types & Literals | 24 | 658 |
| 30 | Logging | 19 | 583 |
| 31 | Testing | 23 | 814 |

### Part III — Spring Boot 3.x

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 32 | Spring: Beans & Dependency Injection | 21 | 907 |
| 33 | Spring: Configuration & Properties | 21 | 726 |
| 34 | Spring: Web Layer | 21 | 853 |
| 35 | Spring: Data Access & Transactions | 21 | 977 |
| 36 | Spring: Testing | 22 | 779 |
| 37 | Spring: Footguns & Anti-patterns | 22 | 891 |

### Part IV — Tooling

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 38 | Static Analysis Configuration | 21 | 834 |

Chapters 1 to 31 apply to every Java codebase. Chapters 32 to 37 apply only
when Spring is on the classpath; if it is not, skip Part III entirely.

## Division of labour between tools

The skill never argues about anything a formatter decides. Each tool owns a
disjoint slice:

| Tool | Owns |
|---|---|
| **google-java-format** (via Spotless) | Google Java Style [§4](https://google.github.io/styleguide/javaguide.html#s4-formatting) in full — braces, +2 block indent, +4 continuation, the 100-column limit, line wrapping, horizontal alignment, import ordering. |
| **Checkstyle** | Naming, Javadoc presence and shape, import hygiene, and the Effective Java design rules a formatter cannot see. |
| **Error Prone** | Semantic bug patterns — `MissingOverride`, `ReferenceEquality`, `EqualsHashCode`, `BoxedPrimitiveConstructor`, and ~640 others. |
| **NullAway** | Null contracts, driven by JSpecify `@Nullable` / `@NullMarked` (chapter 25). |

Chapter 1 states the chain; no later chapter re-litigates whitespace. This is
the same delegation `best-practice-go` makes to `gofmt` and `best-practice-js`
makes to Prettier.

## The shipped Checkstyle configuration

[`config/checkstyle/checkstyle.xml`](config/checkstyle/checkstyle.xml) is
**derived from**, not a copy of, the Checkstyle project's
[`google_checks.xml`](https://github.com/checkstyle/checkstyle/blob/master/src/main/resources/google_checks.xml).
84 modules. Two deliberate departures, both documented in the file header:

**1. Every formatting check is removed.** `Indentation`, `LineLength`,
`WhitespaceAround`, `LeftCurly`, `RightCurly`, `EmptyLineSeparator`,
`NoLineWrap`, `FileTabCharacter`, `CommentsIndentation`, and ~18 others are
gone. google-java-format already guarantees all of them, and running the same
rule in two tools produces duplicate findings a developer cannot fix without
fighting the formatter.

**2. Checks are added that Google's own ruleset omits.** Google's guide is
silent on most design questions, so `google_checks.xml` is silent too. The
config adds `EqualsHashCode`, `CovariantEquals`, `StringLiteralEquality`,
`FinalClass`, `HideUtilityClassConstructor`, `InterfaceIsType`, `IllegalCatch`,
`IllegalThrows`, `IllegalType`, `ParameterAssignment`, `ParameterNumber`,
`HiddenField`, `UnusedImports`, `UseEnhancedSwitch`, `MissingNullCaseInSwitch`,
`WhenShouldBeUsed`, `UnnecessaryNullCheckWithInstanceOf`, and others — each one
backing a rule the skill states from Effective Java or the JLS, so those
chapters can carry an honest `> Enforced by:` callout instead of a bare opinion.

### A note on `MissingSwitchDefault`

The check is enabled, but its scope is narrower than its name suggests. Per its
own documentation it does **not** validate switch *expressions*, and does
**not** validate switch statements using pattern or `null` labels, because
javac already proves both exhaustive. So it does not fight pattern switches
over `sealed` hierarchies, which is the idiom chapters 13, 14, and 23 teach.

It does still flag an old-style colon-form statement switch over an enum that
already matches every constant. That is the single point where the check and
this skill disagree, since adding a `default` there converts what should become
a compile error when a new enum constant appears into a silent runtime
fallthrough. The resolution is to write it as a switch expression with arrow
labels, which chapter 23 requires anyway and which the check exempts.

## Install

```bash
# All skills, globally
npx skills add <your-github-user>/best-practice-skills -g -y

# Just this one
npx skills add <your-github-user>/best-practice-skills --skill best-practice-java -g -y
```

Project-scoped: copy `best-practice-java/` into `.claude/skills/` and drop
`config/checkstyle/` at the repo root.

## Invocation

```text
/best-practice-java  convert this DTO to a record and validate its components in a compact constructor
/best-practice-java  this switch over a sealed interface has a default — should it?
/best-practice-java  review this @Transactional service for self-invocation and boundary problems
/best-practice-java  replace this thread pool with virtual threads, and tell me where it would pin
/best-practice-java  audit this @SpringBootTest — should it be a slice test?
```

## Design notes

- **Java 21 LTS is the floor.** Records, sealed types, pattern matching for
  `switch`, record patterns, text blocks, sequenced collections, and virtual
  threads are all final in 21 and are used as default idiom. Structured
  concurrency (JEP 453) and scoped values (JEP 446) are **preview** in 21;
  chapter 27 labels them as such throughout and gives supported equivalents
  rather than recommending `--enable-preview` in production.
- **Every rule cites something.** Google by anchored section, Effective Java by
  item number, or the JDK / Spring reference docs. No rule is attributed to
  Google that Google does not actually make.
- **Verified, not remembered.** The corpus was checked against the live Google
  Java Style Guide HTML, the 647-entry Error Prone bug-pattern index, and the
  Checkstyle check catalogue. Final state: 0 broken style-guide anchors,
  0 fabricated tool or check names, and 0 `Enforced by:` callouts naming a
  check the shipped configuration does not enable.

## Known gaps

Deliberately out of scope for this pass, flagged rather than half-covered:

- **Lombok.** Which annotations are safe, which fight records and JPA.
- **JPA / Hibernate entity design.** `equals`/`hashCode` on entities, lazy
  loading, cascade semantics, DTO projection. Chapter 35 covers transaction
  boundaries and the N+1 problem, but not entity modelling itself.
- **Non-Spring frameworks.** Micronaut, Quarkus, Jakarta EE, Android.
- **Build tooling** beyond static analysis. Gradle vs Maven, multi-module
  layout, dependency management.
