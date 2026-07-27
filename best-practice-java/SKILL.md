---
name: best-practice-java
description: Comprehensive, Airbnb-depth Java best practices for Java 21 LTS — naming, Javadoc, records, sealed types, pattern matching, generics, streams, Optional, exceptions, virtual threads, structured concurrency, and a full Spring Boot 3.x layer (constructor injection, configuration properties, web layer, transactions, slice testing). Load when writing or reviewing any .java file, when the user mentions Java, Google Java Style Guide, Effective Java, Spring, or Spring Boot, or when the user asks "is this idiomatic Java?". Enforces the shipped Spotless + google-java-format + Checkstyle + Error Prone + NullAway configuration. Pairs with java-google-best-practices for structured code audits.
---

# best-practice-java

This skill codifies modern Java best practices for **Java 21 LTS** code. It is
modeled on the depth and structure of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) —
numbered rules per chapter, `> Why?` rationale, and `// bad` / `// good`
examples for every rule.

The rules trace to four upstream sources, in this precedence order:

1. **[Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)** —
   the normative source for
   [naming](https://google.github.io/styleguide/javaguide.html#s5-naming),
   [programming practices](https://google.github.io/styleguide/javaguide.html#s6-programming-practices),
   [Javadoc](https://google.github.io/styleguide/javaguide.html#s7-javadoc),
   and [source file structure](https://google.github.io/styleguide/javaguide.html#s3-source-file-structure).
2. **Effective Java, 3rd Edition (Joshua Bloch)** — the design-level
   rules Google's guide deliberately leaves open: object creation,
   equality contracts, generics variance, exception design, and
   API surface discipline.
3. **The [Java Language Specification](https://docs.oracle.com/javase/specs/)
   and [JDK 21 API docs](https://docs.oracle.com/en/java/javase/21/docs/api/)** —
   for records, sealed types, pattern matching, virtual threads, and
   every other language or library feature the style guides predate.
4. **[Spring Framework](https://docs.spring.io/spring-framework/reference/)
   and [Spring Boot](https://docs.spring.io/spring-boot/index.html) reference
   documentation** — for the framework layer in chapters 32–37 only.

All formatting concerns — indentation, braces, column limit, line
wrapping, horizontal alignment, import ordering — are owned by the
`google-java-format` / Spotless chain and are never re-litigated in prose.
Chapter 1 documents the tool chain and every subsequent chapter assumes the
code has been formatted. This is the same delegation `best-practice-go`
makes to `gofmt` and `best-practice-js` makes to Prettier.

Every rule that maps to an enabled check in the shipped
`config/checkstyle/checkstyle.xml`, Error Prone, or NullAway configuration
carries an **`> Enforced by: <tool/check-name>`** callout so you can trace
each rule from the guide to the CI check that catches its violations. Rules
that no tool can mechanically verify are labeled **Suggestion**, not
**Violation**.

## When to use

- Writing new `.java` files or reviewing existing Java code.
- Answering "is this idiomatic?" or "does this follow the style guide?"
  for Java.
- Deciding between a `record` and a class, a `sealed` hierarchy and an
  `enum`, an interface and an abstract class.
- Reviewing a Spring Boot service for injection, configuration,
  transaction, or test-slice correctness (chapters 32–37).
- Setting up or auditing Spotless / Checkstyle / Error Prone for a new
  Java project (chapter 38).
- Migrating a codebase from Java 8/11/17 to Java 21 (chapters 12–14, 27).
- Preparing a Java change for code review and wanting pre-review feedback.

## Scope

- Language-level Java through **Java 21 LTS**: types, control flow,
  methods, classes, interfaces, records, sealed types, pattern matching,
  generics, lambdas.
- Google Java Style Guide sections 2, 3, 5, 6, and 7 in full.
- Effective Java design rules: object creation, equality contracts,
  immutability, composition, API design, exception design.
- Standard-library idioms: collections, streams, `Optional`,
  `java.time`, `String`/text blocks, `java.util.concurrent`.
- Concurrency: platform threads, executors, virtual threads, structured
  concurrency, and the synchronization discipline each requires.
- Nullability conventions and JSpecify annotations.
- Logging via SLF4J, and testing via JUnit 5 + AssertJ.
- **Spring Boot 3.x**: bean definition, dependency injection,
  configuration properties, the web layer, transaction boundaries,
  test slices, and the framework's well-known footguns.
- Tooling: `google-java-format`, Spotless, Checkstyle, Error Prone,
  NullAway.

## Non-goals

- **Formatting.** `google-java-format` owns indentation, braces, the
  100-column limit, line wrapping, horizontal alignment, and import
  ordering — Google Java Style Guide
  [§4](https://google.github.io/styleguide/javaguide.html#s4-formatting)
  in its entirety. This skill states the chain in chapter 1 and moves on.
- **Non-Spring frameworks.** Micronaut, Quarkus, Jakarta EE, Dropwizard,
  and Android have their own idioms and their own skills. Chapters 32–37
  are Spring-specific and are explicitly labeled as such.
- **JPA/Hibernate entity design and Lombok.** Deliberately out of scope
  for this pass — flagged as a follow-up rather than half-covered.
- **Build tooling** beyond the static-analysis configuration in
  chapter 38. Gradle vs Maven, multi-module layout, and dependency
  management are out of scope.
- **Generated code.** Protobuf stubs, MapStruct mappers, OpenAPI
  clients, and anything under `build/generated/` follows the generator's
  conventions, not this skill's.
- **JVM tuning and profiling.** GC flags, heap sizing, JFR, and async
  profiler workflows are out of scope.

---

## Chapters

Each chapter is a self-contained reference file with numbered rules,
`> Why?` rationale, `// bad` / `// good` code, and `> Enforced by:`
tool callouts. Files live under `references/`.

### Part I — Google Java Style Guide foundation

| #   | Chapter                        | File                                                                                                   |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| 1   | Formatting & Tooling           | [`references/01-formatting-and-tooling.md`](references/01-formatting-and-tooling.md)                   |
| 2   | Source File Basics & Structure | [`references/02-source-file-structure.md`](references/02-source-file-structure.md)                     |
| 3   | Naming                         | [`references/03-naming.md`](references/03-naming.md)                                                   |
| 4   | Javadoc                        | [`references/04-javadoc.md`](references/04-javadoc.md)                                                 |
| 5   | Comments & TODOs               | [`references/05-comments-and-todos.md`](references/05-comments-and-todos.md)                           |
| 6   | Modifiers & Declaration Order  | [`references/06-modifiers-and-declaration-order.md`](references/06-modifiers-and-declaration-order.md) |
| 7   | Programming Practices          | [`references/07-programming-practices.md`](references/07-programming-practices.md)                     |

### Part II — Language core (Effective Java + JLS, Java 21)

| #   | Chapter                                        | File                                                                                                 |
| --- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 8   | Object Creation                                | [`references/08-object-creation.md`](references/08-object-creation.md)                               |
| 9   | Object Lifecycle & Resources                   | [`references/09-object-lifecycle-and-resources.md`](references/09-object-lifecycle-and-resources.md) |
| 10  | `equals`, `hashCode`, `toString`, `Comparable` | [`references/10-equals-hashcode-tostring.md`](references/10-equals-hashcode-tostring.md)             |
| 11  | Classes & Interfaces                           | [`references/11-classes-and-interfaces.md`](references/11-classes-and-interfaces.md)                 |
| 12  | Records                                        | [`references/12-records.md`](references/12-records.md)                                               |
| 13  | Sealed Types                                   | [`references/13-sealed-types.md`](references/13-sealed-types.md)                                     |
| 14  | Pattern Matching                               | [`references/14-pattern-matching.md`](references/14-pattern-matching.md)                             |
| 15  | Enums & Annotations                            | [`references/15-enums-and-annotations.md`](references/15-enums-and-annotations.md)                   |
| 16  | Generics                                       | [`references/16-generics.md`](references/16-generics.md)                                             |
| 17  | Lambdas & Method References                    | [`references/17-lambdas-and-method-references.md`](references/17-lambdas-and-method-references.md)   |
| 18  | Streams                                        | [`references/18-streams.md`](references/18-streams.md)                                               |
| 19  | `Optional`                                     | [`references/19-optional.md`](references/19-optional.md)                                             |
| 20  | Collections                                    | [`references/20-collections.md`](references/20-collections.md)                                       |
| 21  | Strings & Text Blocks                          | [`references/21-strings-and-text-blocks.md`](references/21-strings-and-text-blocks.md)               |
| 22  | Methods & Parameters                           | [`references/22-methods-and-parameters.md`](references/22-methods-and-parameters.md)                 |
| 23  | Control Structures & `switch`                  | [`references/23-control-structures-and-switch.md`](references/23-control-structures-and-switch.md)   |
| 24  | Exceptions                                     | [`references/24-exceptions.md`](references/24-exceptions.md)                                         |
| 25  | Nullability                                    | [`references/25-nullability.md`](references/25-nullability.md)                                       |
| 26  | Concurrency Fundamentals                       | [`references/26-concurrency-fundamentals.md`](references/26-concurrency-fundamentals.md)             |
| 27  | Virtual Threads & Structured Concurrency       | [`references/27-virtual-threads.md`](references/27-virtual-threads.md)                               |
| 28  | Dates & Times (`java.time`)                    | [`references/28-dates-and-times.md`](references/28-dates-and-times.md)                               |
| 29  | Numeric Types & Literals                       | [`references/29-numeric-types-and-literals.md`](references/29-numeric-types-and-literals.md)         |
| 30  | Logging                                        | [`references/30-logging.md`](references/30-logging.md)                                               |
| 31  | Testing                                        | [`references/31-testing.md`](references/31-testing.md)                                               |

### Part III — Spring Boot 3.x

| #   | Chapter                              | File                                                                                             |
| --- | ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| 32  | Spring: Beans & Dependency Injection | [`references/32-spring-beans-and-di.md`](references/32-spring-beans-and-di.md)                   |
| 33  | Spring: Configuration & Properties   | [`references/33-spring-configuration.md`](references/33-spring-configuration.md)                 |
| 34  | Spring: Web Layer                    | [`references/34-spring-web-layer.md`](references/34-spring-web-layer.md)                         |
| 35  | Spring: Data Access & Transactions   | [`references/35-spring-data-and-transactions.md`](references/35-spring-data-and-transactions.md) |
| 36  | Spring: Testing                      | [`references/36-spring-testing.md`](references/36-spring-testing.md)                             |
| 37  | Spring: Footguns & Anti-patterns     | [`references/37-spring-footguns.md`](references/37-spring-footguns.md)                           |

### Part IV — Tooling

| #   | Chapter                       | File                                                                                               |
| --- | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| 38  | Static Analysis Configuration | [`references/38-static-analysis-configuration.md`](references/38-static-analysis-configuration.md) |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells
   Claude/Cursor/Windsurf when to load `best-practice-java`. When it
   loads, this index is what the agent reads first.
2. **Targeted reads.** For one specific area (say, `Optional` discipline
   or transaction boundaries), the agent opens only the matching chapter
   under `references/` — this keeps the context window small.
3. **Full review.** For a comprehensive audit, the agent reads every
   chapter. Each is exhaustive on its own topic with numbered rules,
   `> Why?` rationale, `// bad` / `// good` examples, and
   `> Enforced by:` tool callouts where applicable.
4. **Plain Java vs Spring.** Chapters 1–31 apply to every Java codebase.
   Chapters 32–37 apply only to Spring Boot 3.x. If the code under
   review has no Spring on the classpath, skip Part III entirely.
5. **Sibling skill.** For structured audit reports (findings grouped by
   category, `file:line` citations, severity labels), pair with
   `java-google-best-practices` — this skill is the source of the rules;
   that skill is the workflow for producing an audit.
6. **Tool config.** The recommended Spotless, Checkstyle, Error Prone,
   and NullAway configuration ships in this repo's root and is
   documented in chapter 38.

## Self-check

Before treating any Java code you write or review as finished, verify:

- The file is clean under `./gradlew spotlessCheck` (or
  `mvn spotless:check`). If not, run `spotlessApply` first — nothing
  else in this list matters if formatting is off.
- Every visible class, member, and record component has Javadoc, or
  falls under a documented exception in
  [§7.3.1](https://google.github.io/styleguide/javaguide.html#s7.3.1-javadoc-exception-self-explanatory)
  /
  [§7.3.2](https://google.github.io/styleguide/javaguide.html#s7.3.2-javadoc-exception-overrides).
  Every Javadoc block opens with a **fragment**, not a complete sentence
  and not "This method returns…" (chapter 4).
- No identifier carries a Hungarian or scope prefix/suffix (`mName`,
  `s_name`, `kName`, `name_`). Constants are `UPPER_SNAKE_CASE` **only**
  when deeply immutable with side-effect-free methods (chapter 3).
- Every override carries `@Override`. Every caught exception is either
  handled, rethrown, or has a comment explaining why doing nothing is
  correct (chapter 7).
- No wildcard imports, no module imports, exactly one top-level class per
  file, and overloads are never split by another member (chapter 2).
- Every value carrier that is a transparent aggregate of its components
  is a `record`, not a hand-written class with a generated
  `equals`/`hashCode` (chapter 12).
- Every closed type hierarchy is `sealed` and every `switch` over it is
  exhaustive **without** a `default` label, so adding a permitted subtype
  becomes a compile error rather than a runtime surprise (chapters 13, 14, 23).
- `Optional` appears as a return type only. Never as a field, never as a
  parameter, never in a collection (chapter 19).
- No raw types, no unchecked-warning suppression without a scoped
  `@SuppressWarnings("unchecked")` and a comment proving safety
  (chapter 16).
- Every `AutoCloseable` is acquired in try-with-resources. No class
  overrides `Object.finalize` (chapters 7, 9).
- Every exception thrown across an API boundary is either a documented
  checked exception the caller can act on, or an unchecked exception
  representing a programming error. No exception is swallowed, and no
  control flow runs through exceptions (chapter 24).
- Every blocking call inside a virtual thread is genuinely blocking, not
  pinned by a `synchronized` block holding the carrier thread
  (chapter 27).
- Every log statement uses SLF4J placeholders (`log.info("id={}", id)`),
  never string concatenation, and never logs-and-rethrows the same
  failure twice (chapters 24, 30).
- No `java.util.Date`, `Calendar`, or `SimpleDateFormat` — `java.time`
  only, with explicit zone handling (chapter 28).
- Every monetary or exact-decimal value is `BigDecimal` constructed from
  a `String`, never from a `double` (chapter 29).
- **Spring only:** every bean uses constructor injection with `final`
  fields. No `@Autowired` on fields. `@Transactional` never relies on
  self-invocation. `@SpringBootTest` is used only when a slice test
  cannot do the job (chapters 32, 35, 36).
- The code compiles cleanly under the project's Checkstyle and Error
  Prone configuration (chapter 38). No new `@SuppressWarnings` or
  `// CHECKSTYLE:OFF` without a scoped target and an explanation.
