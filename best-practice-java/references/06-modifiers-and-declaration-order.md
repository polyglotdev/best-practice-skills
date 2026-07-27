<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 6. Modifiers & Declaration Order

This chapter covers the modifier keywords themselves and the discipline of
declaring things — which modifiers, in what order, with what visibility, and
where in the method body a local is allowed to appear. It draws from [Google
Java Style §4.8.7
Modifiers](https://google.github.io/styleguide/javaguide.html#s4.8.7-modifiers),
[§4.8.2 Variable
declarations](https://google.github.io/styleguide/javaguide.html#s4.8.2-variable-declarations),
[§4.8.3 Arrays](https://google.github.io/styleguide/javaguide.html#s4.8.3-arrays),
[§4.3 One statement per
line](https://google.github.io/styleguide/javaguide.html#s4.3-one-statement-per-line),
and from Effective Java, 3rd ed., Items 15 (Minimize the accessibility of
classes and members), 17 (Minimize mutability), and 57 (Minimize the scope of
local variables).

Two adjacent topics are deliberately elsewhere. The **order of members
within a class** — constructors before methods, overloads never split —
is [§3.4.2](https://google.github.io/styleguide/javaguide.html#s3.4.2-ordering-class-contents)
and lives in [Chapter 2](02-source-file-structure.md). The **names** given
to fields, constants, and locals are [§5](https://google.github.io/styleguide/javaguide.html#s5-naming)
and live in [Chapter 3](03-naming.md). This chapter takes both as settled
and covers everything to the left of the identifier.

`var` gets three rules here because Java 21 makes it ubiquitous and because
it is the one declaration decision with no mechanical answer. Those rules
follow the OpenJDK Amber team's [Local Variable Type Inference: Style
Guidelines](https://openjdk.org/projects/amber/guides/lvti-style-guide),
which is the closest thing to a normative source — Google's guide predates
the feature and says nothing about it.

**Tool alignment:** `checkstyle/ModifierOrder`, `checkstyle/RedundantModifier`,
`checkstyle/MultipleVariableDeclarations`,
`checkstyle/VariableDeclarationUsageDistance`, `checkstyle/ArrayTypeStyle`,
`checkstyle/VisibilityModifier`, `checkstyle/ExplicitInitialization`,
`checkstyle/ParameterAssignment`, `checkstyle/ModifiedControlVariable`,
`checkstyle/HiddenField`, `checkstyle/OneStatementPerLine`,
`checkstyle/FinalLocalVariable`, `checkstyle/UnusedLocalVariable`, and Error
Prone's `UnusedVariable` cover most of this chapter mechanically.

## 6.1 Write class and member modifiers in the canonical JLS order.

> Why? [§4.8.7](https://google.github.io/styleguide/javaguide.html#s4.8.7-modifiers)
> fixes the order as **`public protected private abstract default static
> final sealed non-sealed transient volatile synchronized native
> strictfp`**, "the order recommended by the Java Language Specification."
> The order carries no semantics — which is precisely why it must be fixed.
> A reader scanning a class body for `static` members finds them at a
> constant column offset only if every declaration agrees.
> **Violation — enforced by `checkstyle/ModifierOrder`.**

```java
// bad — legal Java, but every declaration puts the keywords somewhere new
static public final synchronized void flush() {
  buffer.drain();
}

volatile private transient long lastSeenAt;

// good
public static final synchronized void flush() {
  buffer.drain();
}

private transient volatile long lastSeenAt;
```

## 6.2 Order `requires` module directive modifiers `transitive static`.

> Why? [§4.8.7](https://google.github.io/styleguide/javaguide.html#s4.8.7-modifiers)
> gives module directives their own two-keyword order: "Modifiers on
> `requires` module directives, when present, appear in the following
> order: **transitive static**." It is the opposite of what most people
> guess from the class-member order, which is exactly why it is worth
> stating rather than deriving.

```java
// bad — reads naturally, contradicts §4.8.7
module com.example.billing {
  requires static transitive java.sql;
}

// good
module com.example.billing {
  requires transitive static java.sql;
}
```

## 6.3 Omit modifiers the language already implies.

> Why? Interface members are implicitly `public`, interface methods without
> a body implicitly `abstract`, interface fields implicitly `public static
> final`, enum constructors implicitly `private`, and record components
> implicitly `private final`. Writing them out is not extra clarity — it is
> noise that makes the one member carrying a *meaningful* modifier (a
> `default` method, a `static` factory) harder to spot.
> **Violation — enforced by `checkstyle/RedundantModifier`.**

```java
// bad — every modifier here is already implied by the declaration context
public interface Ledger {
  public static final int MAX_ENTRIES = 10_000;

  public abstract void post(Entry entry);

  public abstract int size();

  public default boolean isEmpty() {
    return size() == 0;
  }
}

// good — only `default`, which genuinely changes the meaning, survives
public interface Ledger {
  int MAX_ENTRIES = 10_000;

  void post(Entry entry);

  int size();

  default boolean isEmpty() {
    return size() == 0;
  }
}
```

## 6.4 Declare every field `final` unless it genuinely has to change after construction.

> Why? Effective Java, 3rd ed., Item 17 ("Minimize mutability") makes this
> the default because a `final` field is a proof, checked by the compiler,
> that no code path anywhere can reassign it. That proof is what makes an
> instance safe to publish across threads without synchronization, and it
> removes an entire class of question from every future reader: "who else
> writes this?" is answered by the keyword. Non-final should be a decision
> you can defend, not the default you fell into.

```java
// bad — nothing prevents a later caller from swapping the clock mid-flight
final class InvoiceService {
  private Clock clock;
  private List<Listener> listeners;

  InvoiceService(Clock clock) {
    this.clock = clock;
    this.listeners = new ArrayList<>();
  }
}

// good
final class InvoiceService {
  private final Clock clock;
  private final List<Listener> listeners = new ArrayList<>();

  InvoiceService(Clock clock) {
    this.clock = Objects.requireNonNull(clock, "clock");
  }
}
```

## 6.5 Give every class, member, and field the narrowest access that works.

> Why? Effective Java, 3rd ed., Item 15 ("Minimize the accessibility of
> classes and members") frames accessibility as the primary mechanism for
> decoupling: anything not `private` is a promise you have to keep, and
> every public member you can never take back. A `public` mutable field is
> the extreme case — it forfeits invariant enforcement, thread-safety
> control, and the ability to ever compute the value instead of storing it.
> **Violation — enforced by `checkstyle/VisibilityModifier`.**

```java
// bad — the parser's scratch state is part of the published API forever
public final class CsvParser {
  public StringBuilder buffer = new StringBuilder();
  public int column;

  public String[] parse(String line) {
    return line.split(",", -1);
  }
}

// good
public final class CsvParser {
  private final StringBuilder buffer = new StringBuilder();
  private int column;

  public String[] parse(String line) {
    return line.split(",", -1);
  }
}
```

## 6.6 Prefer package-private to public for a type that only collaborates inside its own package.

> Why? Effective Java, 3rd ed., Item 15 notes that a package-private
> top-level class is "part of the implementation rather than the exported
> API" — you can change it, rename it, or delete it in a later release
> without breaking anyone. Marking every class `public` by reflex converts
> internal wiring into a compatibility obligation, and the obligation is
> permanent.

```java
// bad — an internal helper published to the whole application
public final class RetryBudgetCalculator {
  public int budgetFor(int shardCount) {
    return Math.max(1, shardCount / 4);
  }
}

// good — visible to its package, invisible to everyone else
final class RetryBudgetCalculator {
  int budgetFor(int shardCount) {
    return Math.max(1, shardCount / 4);
  }
}
```

## 6.7 Never expose a mutable object through a `public static final` field.

> Why? `final` on a reference field freezes the *reference*, not the
> object. Effective Java, 3rd ed., Item 15 is explicit that "it is wrong
> for a class to have a public static final array field, or an accessor
> that returns such a field" — any caller can write through it, and the
> compiler will not object. `List.of`, `Map.of`, and `Set.of` produce
> genuinely unmodifiable values that satisfy the [§5.2.4](https://google.github.io/styleguide/javaguide.html#s5.2.4-constant-names)
> definition of a constant ("deeply immutable"). See [Chapter 3](03-naming.md).
> **Violation — enforced by `errorprone/MutablePublicArray` ("Non-empty
> arrays are mutable, so this `public static final` array is not a
> constant and can be modified").** The mutable-`Map` case is not covered
> by that check; treat it as a **Suggestion**.

```java
// bad — SUPPORTED[0] = "XXX" compiles, and SCALE.clear() compiles
public static final String[] SUPPORTED = {"USD", "EUR", "GBP"};
public static final Map<String, Integer> SCALE = new HashMap<>();

// good
public static final List<String> SUPPORTED = List.of("USD", "EUR", "GBP");
public static final Map<String, Integer> SCALE = Map.of("USD", 2, "JPY", 0);
```

## 6.8 Declare exactly one variable per declaration.

> Why? [§4.8.2.1](https://google.github.io/styleguide/javaguide.html#s4.8.2.1-variables-per-declaration)
> requires that "every variable declaration (field or local) declares only
> one variable: declarations such as `int a, b;` are not used." Grouped
> declarations make a line-based diff report a change to two variables when
> only one moved, and they invite the classic `String a, b = ""` bug where
> only the last variable is initialized. The one exception the guide grants
> is the header of a `for` loop.
> **Violation — enforced by `checkstyle/MultipleVariableDeclarations`.**

```java
// bad — only `last` is initialized, and the diff can't isolate either one
int width, height;
String first, last = "";

// good
int width = bounds.width();
int height = bounds.height();

// good — the for-header exception §4.8.2.1 grants
for (int i = 0, n = entries.size(); i < n; i++) {
  merge(entries.get(i), i == n - 1);
}
```

## 6.9 Declare a local close to its first use, with an initializer.

> Why? [§4.8.2.2](https://google.github.io/styleguide/javaguide.html#s4.8.2.2-variables-limited-scope)
> states that "local variables are **not** habitually declared at the start
> of their containing block... Instead, local variables are declared close
> to the point they are first used (within reason), to minimize their
> scope," and that "local variable declarations typically have
> initializers, or are initialized immediately after declaration."
> Effective Java, 3rd ed., Item 57 ("Minimize the scope of local
> variables") gives the reason: a variable declared far from its use is
> live across code that has no business seeing it, so a stray reassignment
> in between is invisible at the point that matters.
> **Violation for the distance half — enforced by
> `checkstyle/VariableDeclarationUsageDistance`** (default `allowedDistance`
> is 3, and intervening declarations are not counted, so tighten it if you
> want the rule enforced strictly). The "with an initializer" half is a
> **Suggestion**; no check covers it.

```java
// bad — `total` is in scope, uninitialized, across four unrelated statements
void settle(List<Payment> payments) {
  BigDecimal total;
  Instant startedAt = clock.instant();
  auditLog.record(startedAt);
  validate(payments);
  total = payments.stream().map(Payment::amount).reduce(BigDecimal.ZERO, BigDecimal::add);
  ledger.post(total);
}

// good
void settle(List<Payment> payments) {
  Instant startedAt = clock.instant();
  auditLog.record(startedAt);
  validate(payments);

  BigDecimal total =
      payments.stream().map(Payment::amount).reduce(BigDecimal.ZERO, BigDecimal::add);
  ledger.post(total);
}
```

## 6.10 Put the square brackets on the type, never after the variable name.

> Why? [§4.8.3.2](https://google.github.io/styleguide/javaguide.html#s4.8.3.2-array-declarations)
> states it directly: "The square brackets form a part of the *type*, not
> the variable: `String[] args`, not `String args[]`." The C-style form is
> not just unfashionable — combined with 6.8's ban it is the source of the
> `int a[], b;` trap, where `a` is an array and `b` is not.
> **Violation — enforced by `checkstyle/ArrayTypeStyle`.**

```java
// bad — `values` is a double[], `scale` is a plain double
double values[], scale;

// good
double[] values = new double[capacity];
double scale = 1.0d;
```

## 6.11 Format a multi-line array initializer as a block-like construct.

> Why? [§4.8.3.1](https://google.github.io/styleguide/javaguide.html#s4.8.3.1-array-initializers)
> allows any array initializer to "optionally be formatted as if it were a
> 'block-like construct'," which is what `google-java-format` produces when
> the initializer will not fit on one line. Taking the block form means
> adding an element changes exactly one line in the diff instead of
> rewrapping the whole literal.

Note the naming: an array is never deeply immutable, so §5.2.4 classes a
`static final String[]` as a non-constant field and §5.2.5 names it in
lowerCamelCase. See 6.7 and 6.20.

```java
// bad — hand-wrapped mid-literal; adding one entry reflows the whole literal
private static final String[] isoCodes = {"USD", "EUR", "GBP", "JPY",
    "CHF", "SEK", "NOK"};

// good
private static final String[] isoCodes = {
  "USD", "EUR", "GBP",
  "JPY", "CHF", "SEK",
  "NOK",
};
```

## 6.12 Do not explicitly initialize a field to its default value.

> Why? Java zeroes every instance field before the constructor body runs
> and every static field before the class initializer runs, so `= 0`,
> `= false`, and `= null` are pure noise — and worse, they are misleading
> noise, because they suggest the value was chosen rather than inherited.
> Checkstyle's own rationale puts it as "each instance variable gets
> initialized twice, to the same value."
> **Violation — enforced by `checkstyle/ExplicitInitialization`, whose
> `onlyObjectReferences` property defaults to `false`, so it flags the
> numeric and `boolean` cases too.**

```java
// bad — three assignments that the JVM has already performed
private int retries = 0;
private boolean closed = false;
private String lastError = null;

// good
private int retries;
private boolean closed;
private String lastError;
```

## 6.13 Never reassign a parameter.

> Why? A reassigned parameter destroys the only record of what the caller
> actually passed, which makes the method impossible to debug from a stack
> trace and impossible to reason about from the signature. It also blocks
> the parameter from being captured by a lambda or an inner class, since
> those require the variable to be effectively final. A new local costs one
> line and keeps both values.
> **Violation — enforced by `checkstyle/ParameterAssignment`.**

```java
// bad — by the time an exception is thrown, the original argument is gone
String normalize(String value) {
  value = value.strip();
  value = value.toLowerCase(Locale.ROOT);
  return value;
}

// good
String normalize(String value) {
  String stripped = value.strip();
  return stripped.toLowerCase(Locale.ROOT);
}
```

## 6.14 Never modify a `for` loop's control variable inside the loop body.

> Why? The `for` header is a contract about how the loop advances; changing
> the counter in the body silently breaks it, and the reader has to
> simulate the whole body to work out the real step. Off-by-one bugs from
> this pattern survive review reliably because the header still looks
> correct. If the traversal is not a simple step, use `while` and make the
> advance explicit.
> **Violation — enforced by `checkstyle/ModifiedControlVariable`.**

```java
// bad — the header says +1, the body sometimes does +2
for (int i = 0; i < entries.size(); i++) {
  if (entries.get(i).isContinuation()) {
    merge(entries.get(i - 1), entries.get(i));
    i++;
  }
}

// good — the advance is stated where it happens
int i = 0;
while (i < entries.size()) {
  if (entries.get(i).isContinuation()) {
    merge(entries.get(i - 1), entries.get(i));
    i += 2;
  } else {
    i += 1;
  }
}
```

## 6.15 Do not shadow a field with a local variable.

> Why? A local that shadows a field makes every unqualified use in the rest
> of the method silently refer to the local, so an assignment intended to
> update instance state quietly updates nothing. The sanctioned exceptions
> are constructor and setter parameters, where `this.x = x` is the
> idiomatic form and the shadow is deliberate and immediately resolved.
> **Violation — enforced by `checkstyle/HiddenField`** (configure
> `ignoreConstructorParameter` and `ignoreSetter`).

```java
// bad — the field is never updated; `timeout` refers to the local throughout
final class HttpClientHolder {
  private Duration timeout = Duration.ofSeconds(30);

  void reconfigure(ClientConfig config) {
    Duration timeout = config.timeout();
    log.info("reconfigured timeout={}", timeout);
  }
}

// good
final class HttpClientHolder {
  private Duration timeout = Duration.ofSeconds(30);

  void reconfigure(ClientConfig config) {
    this.timeout = config.timeout();
    log.info("reconfigured timeout={}", this.timeout);
  }
}
```

## 6.16 Use `var` only when the initializer already tells the reader the type.

> Why? [LVTI Style Guidelines
> G3](https://openjdk.org/projects/amber/guides/lvti-style-guide) says to
> "consider `var` when the initializer provides sufficient information to
> the reader" — a constructor call or a well-named static factory does;
> an arbitrary method call does not. G1 pairs with it: replacing an
> explicit type with `var` "should often be accompanied by improving the
> variable name," because the name is now the only channel left. The cost
> of getting this wrong is that a reader must open another file to learn
> what they are holding. **Suggestion.**

```java
// bad — nothing at this declaration says what `x` is
var x = dbConnection.executeQuery(query);

// good — the constructor names the type
var outputStream = new ByteArrayOutputStream();

// good — the type is implicit but the variable name carries the meaning
var customers = dbConnection.executeQuery(query);

// good — keep the explicit type when neither channel is informative
Duration timeout = config.resolve(TIMEOUT_KEY);
```

## 6.17 Never combine `var` with the diamond operator or a bare generic factory.

> Why? [LVTI Style Guidelines
> G6](https://openjdk.org/projects/amber/guides/lvti-style-guide) labels
> this combination **dangerous**: with no target type on the left, diamond
> inference "falls back to the broadest applicable type, which is often
> `Object`." `var queue = new PriorityQueue<>()` compiles cleanly and
> infers `PriorityQueue<Object>`, so the first `queue.peek().amount()` call
> fails to compile hundreds of lines away with a message about `Object`.
> **Suggestion.**

```java
// bad — infers PriorityQueue<Object> and List<Object>, silently
var queue = new PriorityQueue<>();
var empty = List.of();

// good — the type argument is supplied on the right-hand side
var queue = new PriorityQueue<Item>();
var empty = List.<Item>of();

// good — or supply it on the left and use diamond as usual
PriorityQueue<Item> queue2 = new PriorityQueue<>();
```

## 6.18 Keep `var` declarations inside a small scope.

> Why? [LVTI Style Guidelines
> G2](https://openjdk.org/projects/amber/guides/lvti-style-guide) shows the
> failure mode: swapping `new ArrayList<>()` for `new HashSet<>()` under a
> `var` declaration changes iteration order with no visible type change at
> all. If the uses are adjacent the bug is obvious; a hundred lines away it
> is invisible. G2's conclusion is not "avoid `var`" but "reduce the scope,
> then use `var`." **Suggestion.**

```java
// bad — the ArrayList-to-HashSet change is invisible 100 lines later
var items = new HashSet<Item>();

// ... 100 lines of unrelated code ...

items.add(MUST_BE_PROCESSED_LAST);
for (var item : items) {
  process(item);
}

// good — declaration and use are adjacent, so the ordering bug is obvious
var items = new ArrayList<Item>(candidates);
items.add(MUST_BE_PROCESSED_LAST);
for (var item : items) {
  process(item);
}
```

## 6.19 Put one statement on each line.

> Why? [§4.3](https://google.github.io/styleguide/javaguide.html#s4.3-one-statement-per-line)
> requires that "each statement is followed by a line break." A line
> holding two statements can only ever be half-covered by a coverage
> report, half-attributed by `git blame`, and half-breakpointed by a
> debugger — every line-oriented tool in the chain degrades.
> **Violation — enforced by `checkstyle/OneStatementPerLine`.**

```java
// bad — a debugger cannot break between these, and coverage reports "hit"
int width = bounds.width(); int height = bounds.height(); resize(width, height);

// good
int width = bounds.width();
int height = bounds.height();
resize(width, height);
```

## 6.20 Reserve `UPPER_SNAKE_CASE` for `static final` fields that are deeply immutable.

> Why? [§5.2.4](https://google.github.io/styleguide/javaguide.html#s5.2.4-constant-names)
> defines constants as "static final fields whose contents are deeply
> immutable and whose methods have no detectable side effects" — the
> casing is a claim about semantics, not about the `static final` keywords.
> A `static final` mutable `List` named `DEFAULTS` tells every reader they
> may cache it, share it across threads, and never re-read it. All three
> are wrong. No check can evaluate "deeply immutable," so this one is on
> you — `checkstyle/ConstantName` keys off `static final` alone: it will
> happily bless a mutable `List` in screaming case, and it will flag the
> correct lowerCamelCase name for a mutable static. Google's own §5.2.4
> example list files `static final Set<String> mutableCollection = new
> HashSet<String>();` under "Not constants," so follow the guide here and
> exempt the check, not the other way round. See
> [Chapter 3](03-naming.md) for the full naming rules. **Suggestion.**

```java
// bad — the name promises a constant; the value is a shared mutable buffer
static final List<String> DEFAULT_SCOPES = new ArrayList<>(List.of("read"));
static final SimpleDateFormat TIMESTAMP = new SimpleDateFormat("yyyy-MM-dd");

// good — deeply immutable values keep the constant casing
static final List<String> DEFAULT_SCOPES = List.of("read");
static final DateTimeFormatter TIMESTAMP = DateTimeFormatter.ISO_LOCAL_DATE;

// good — a mutable static is a variable, and is named like one
private static final Map<String, Session> activeSessions = new ConcurrentHashMap<>();
```

## 6.21 Delete an unused local or parameter rather than annotating around it.

> Why? An unused declaration is either dead code or a bug — a value that
> was computed and then forgotten. Suppressing the warning preserves the
> ambiguity permanently, and the suppression outlives the reason for it.
> Deleting is the only action that resolves which of the two it was.
> **Violation — enforced by `errorprone/UnusedVariable` and
> `checkstyle/UnusedLocalVariable`.**
>
> Java 21 note: unnamed variables and patterns (`_`) are a **preview**
> feature in Java 21 (JEP 443) and must not be used in production code
> targeting 21. Delete the declaration instead.

```java
// bad — the computed value is discarded, and the suppression hides which
@SuppressWarnings("unused")
void publish(Event event) {
  String correlationId = event.headers().get("x-correlation-id");
  broker.send(event.topic(), event.payload());
}

// good — either use it or delete it; here it was meant to be used
void publish(Event event) {
  String correlationId = event.headers().get("x-correlation-id");
  broker.send(event.topic(), event.payload(), correlationId);
}
```
