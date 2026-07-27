<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 23. Control Structures & `switch`

Control flow is where Java's oldest syntax and its newest syntax sit side by
side. The `if`/`for`/`while` forms have not changed since 1.0; `switch` has
two entirely different syntaxes — the colon-style *statement* inherited from
C, and the arrow-style *rule* that also works as an expression. This chapter
takes the position that new code uses the new form, and treats the old form
as something you read rather than write.

The formatting-adjacent rules here come from Google Java Style
[§4.1.1](https://google.github.io/styleguide/javaguide.html#s4.1.1-braces-always-used),
[§4.3](https://google.github.io/styleguide/javaguide.html#s4.3-one-statement-per-line),
and the whole of
[§4.8.4](https://google.github.io/styleguide/javaguide.html#s4.8.4-switch).
The rest — guard clauses, loop shape, ternary discipline — is not covered by
Google's guide and is cited to Effective Java or left as a Suggestion.

This chapter deliberately defers three things. The *syntax and semantics* of
type patterns and record patterns belong to
[Chapter 14](14-pattern-matching.md); this chapter only covers how patterns
interact with `switch` control flow. Designing the closed hierarchy you
switch over belongs to [Chapter 13](13-sealed-types.md). And the reason
"never use exceptions for control flow" is a rule at all is developed in
[Chapter 24](24-exceptions.md); §23.19 states it and points there.

**Tool alignment:** Checkstyle's `NeedBraces`, `OneStatementPerLine`,
`FallThrough`, `InnerAssignment`, `ModifiedControlVariable`,
`SimplifyBooleanExpression`, `SimplifyBooleanReturn`,
`MissingNullCaseInSwitch`, `UseEnhancedSwitch`, and `WhenShouldBeUsed`
checks, plus Error Prone's `FallThrough`, `MissingCasesInEnumSwitch`,
`UnnecessaryDefaultInEnumSwitch`, and `StatementSwitchToExpressionSwitch`,
mechanically cover most of §23.1-§23.10 and §23.14-§23.17. Rules those tools
cannot see are labeled **Suggestion**.

## 23.1 Use braces with `if`, `else`, `for`, `do`, and `while`, even when the body is a single statement or empty.

> Why? Google Java Style
> [§4.1.1](https://google.github.io/styleguide/javaguide.html#s4.1.1-braces-always-used)
> is unconditional: "Braces are used with `if`, `else`, `for`, `do` and
> `while` statements, even when the body is empty or contains only a single
> statement." A brace-less body silently swallows the second statement
> someone adds later — the indentation says one thing and the parser does
> another. **Violation — enforced by `checkstyle/NeedBraces`.**

```java
// bad — the second line is not part of the if; it always runs
if (account.isClosed())
  audit.record(account);
  notifier.send(account);

// good
if (account.isClosed()) {
  audit.record(account);
  notifier.send(account);
}
```

## 23.2 Put exactly one statement on a line.

> Why? Google Java Style
> [§4.3](https://google.github.io/styleguide/javaguide.html#s4.3-one-statement-per-line)
> requires that "each statement is followed by a line break." Two statements
> on one line hide the second from a skimming reader, and they make a
> line-oriented diff or a line-based coverage report lie about which
> statement actually ran. **Violation — enforced by
> `checkstyle/OneStatementPerLine`.**

```java
// bad — the increment is invisible in a diff and uncovered in a report
for (Order order : orders) { total += order.amount(); count++; }

// good
for (Order order : orders) {
  total += order.amount();
  count++;
}
```

## 23.3 Prefer a `switch` *expression* with arrow labels over a `switch` statement that assigns a variable.

> Why? Google Java Style
> [§4.8.4](https://google.github.io/styleguide/javaguide.html#s4.8.4-switch)
> names the two forms *old-style* (colon) and *new-style* (arrow), and
> [§4.8.4.4](https://google.github.io/styleguide/javaguide.html#s4.8.4.4-switch-expressions)
> requires that "switch expressions must be new-style switches." The
> expression form buys three guarantees the statement form cannot give: no
> fall-through
> ([§4.8.4.2](https://google.github.io/styleguide/javaguide.html#s4.8.4.2-switch-fall-through):
> "there is no fall-through in new-style switches"), compiler-checked
> exhaustiveness, and definite assignment — the target can be `final`
> because the compiler proves every path assigns it exactly once.
> **Violation — enforced by Error Prone
> `StatementSwitchToExpressionSwitch` and `checkstyle/UseEnhancedSwitch`.**

```java
// bad — mutable local, a break to forget on every arm, and nothing forces
// the default arm to assign
String label;
switch (status) {
  case ACTIVE:
    label = "Active";
    break;
  case SUSPENDED:
    label = "Suspended";
    break;
  default:
    label = "Unknown";
}

// good — final target, no breaks, exhaustiveness checked by the compiler
String label =
    switch (status) {
      case ACTIVE -> "Active";
      case SUSPENDED -> "Suspended";
      case CLOSED -> "Closed";
    };
```

## 23.4 Use `yield` only when an arm genuinely needs statements; otherwise let the arrow's expression be the value.

> Why? `yield` exists so a block-bodied arm can still produce a value. Using
> a block plus `yield` for a bare constant adds three lines and a keyword to
> say what `->` already says, and it visually flattens the cheap arms into
> the expensive ones so a reader can no longer tell at a glance which arms
> do work. **Suggestion.**

```java
// bad — a block and a yield to deliver a constant
int weight =
    switch (priority) {
      case HIGH -> {
        yield 3;
      }
      case LOW -> {
        yield 1;
      }
    };

// good — constants inline, and yield reserved for the arm that does work
int weight =
    switch (priority) {
      case HIGH -> {
        log.debug("escalating request {}", requestId);
        yield 3;
      }
      case LOW -> 1;
    };
```

## 23.5 Collapse labels that share a body into one comma-separated arrow rule.

> Why? Stacking bare colon labels to share a statement group is the
> old-style idiom for "these cases behave the same," and it is
> indistinguishable at a glance from an accidental missing `break` (§23.6).
> A comma-separated arrow label states the grouping as a fact the compiler
> understands rather than as a fall-through the reader has to infer.
> **Suggestion.**

```java
// bad — is SATURDAY intentionally sharing SUNDAY's body, or is a break
// missing?
switch (day) {
  case SATURDAY:
  case SUNDAY:
    return Rate.WEEKEND;
  default:
    return Rate.WEEKDAY;
}

// good — the grouping is explicit and cannot be a mistake
return switch (day) {
  case SATURDAY, SUNDAY -> Rate.WEEKEND;
  case MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY -> Rate.WEEKDAY;
};
```

## 23.6 In an old-style `switch`, every statement group either terminates abruptly or carries a comment saying it falls through.

> Why? Google Java Style
> [§4.8.4.2](https://google.github.io/styleguide/javaguide.html#s4.8.4.2-switch-fall-through)
> requires that "each statement group either terminates abruptly (with a
> `break`, `continue`, `return` or thrown exception), or is marked with a
> comment to indicate that execution will or *might* continue into the next
> statement group." The comment is not decoration: it is the only signal
> that distinguishes deliberate fall-through from a dropped `break`, which
> is one of the highest-frequency defect classes in C-family languages. The
> guide notes the comment "is not required in the last statement group."
> **Violation — enforced by `checkstyle/FallThrough` and Error Prone
> `FallThrough`.**

```java
// bad — did the author mean TRIAL to also run the PAID logic?
switch (plan) {
  case TRIAL:
    grantTrialCredits(account);
  case PAID:
    enableBilling(account);
    break;
  default:
    throw new IllegalStateException("unknown plan: " + plan);
}

// good — the intent is stated, and the checker accepts the comment
switch (plan) {
  case TRIAL:
    grantTrialCredits(account);
    // fall through
  case PAID:
    enableBilling(account);
    break;
  default:
    throw new IllegalStateException("unknown plan: " + plan);
}
```

## 23.7 Make every `switch` exhaustive, including the ones the language does not require to be.

> Why? Google Java Style
> [§4.8.4.3](https://google.github.io/styleguide/javaguide.html#s4.8.4.3-switch-default)
> states that "Google Style requires *every* switch to be exhaustive, even
> those where the language itself does not require it. This may require
> adding a `default` label, even if it contains no code." A `switch` over an
> `int`, a `String`, or any other open domain will silently do nothing for
> an unmatched value, which turns a bad input into a missing side effect
> rather than an error. **Violation — enforced by
> `checkstyle/MissingSwitchDefault`,** which flags any `switch` *statement*
> with no `default`, colon-style or arrow-style alike. It deliberately
> stands down on `switch` expressions and on statements using pattern or
> `null` labels, because there the compiler already proves exhaustiveness.
> See §23.8 for why enums and sealed types need no `default` at all.

```java
// bad — an unrecognised header is silently ignored
switch (header) {
  case "content-type" -> contentType = value;
  case "content-length" -> contentLength = Long.parseLong(value);
}

// good — the open domain is closed by an explicit default
switch (header) {
  case "content-type" -> contentType = value;
  case "content-length" -> contentLength = Long.parseLong(value);
  default -> extras.put(header, value);
}
```

## 23.8 Achieve exhaustiveness over an `enum` or a sealed type by listing every case — never by adding a `default`.

> Why? Google's exhaustiveness requirement
> ([§4.8.4.3](https://google.github.io/styleguide/javaguide.html#s4.8.4.3-switch-default))
> is satisfied "for example if the value being switched on is an enum and
> every value of the enum is matched by a switch label" — a `default` is one
> way to get there, not the required way. For a closed domain it is the
> *wrong* way: a `default` arm absorbs every constant or permitted subtype
> added later, converting what should be a compile error into a silent
> wrong answer at runtime. Omitting it makes the compiler your migration
> checklist. **Violation — enforced by Error Prone
> `UnnecessaryDefaultInEnumSwitch` and `MissingCasesInEnumSwitch`.**
>
> Note the one place this collides with §23.7's tooling:
> `checkstyle/MissingSwitchDefault` demands a `default` on an enum `switch`
> *statement* — colon-style or arrow-style — even when every constant is
> covered, because Checkstyle is not type-aware. Its documented exemptions
> are switch *expressions* and switch statements that use pattern or `null`
> labels, in both cases because "the compiler requires switch expressions to
> be exhaustive." That is a further reason to write closed-domain dispatch
> as a `switch` expression (§23.3), where the check stands down and the
> compiler takes over.

```java
// bad — adding Grade.DISTINCTION compiles clean and silently scores 0
static int score(Grade grade) {
  return switch (grade) {
    case PASS -> 1;
    case MERIT -> 2;
    default -> 0;
  };
}

// bad — same failure over a sealed hierarchy
sealed interface Shape permits Circle, Square, Triangle {}

static double area(Shape shape) {
  return switch (shape) {
    case Circle c -> Math.PI * c.radius() * c.radius();
    default -> 0.0;
  };
}

// good — adding a constant or a permitted subtype breaks the build here
static int score(Grade grade) {
  return switch (grade) {
    case PASS -> 1;
    case MERIT -> 2;
    case FAIL -> 0;
  };
}

static double area(Shape shape) {
  return switch (shape) {
    case Circle c -> Math.PI * c.radius() * c.radius();
    case Square s -> s.side() * s.side();
    case Triangle t -> 0.5 * t.base() * t.height();
  };
}
```

## 23.9 Handle `null` with an explicit `case null` label rather than a separate pre-switch null check.

> Why? A `switch` on a reference throws `NullPointerException` before any
> label is considered, and a lone `default` does *not* catch it — `default`
> only matches non-null values that no other label matched. Java 21 makes
> `case null` a legal label in a pattern `switch` (and `case null, default`
> for "null behaves like everything else"), which keeps the null decision
> inside the same construct as every other decision instead of stranding it
> in a guard the next editor can drop. **Violation — enforced by
> `checkstyle/MissingNullCaseInSwitch`.**

```java
// bad — NPE before any arm runs; the default arm never sees null
static String describe(Object value) {
  return switch (value) {
    case Integer i -> "int " + i;
    case String s -> "string of length " + s.length();
    default -> "other";
  };
}

// good — null is a case like any other
static String describe(Object value) {
  return switch (value) {
    case null -> "absent";
    case Integer i -> "int " + i;
    case String s -> "string of length " + s.length();
    default -> "other";
  };
}
```

## 23.10 Refine a pattern with a `when` guard instead of an `if` inside the case body.

> Why? A guarded pattern keeps one outcome per arm, so the `switch` stays a
> flat table of conditions the reader can scan. Re-testing the bound
> variable inside the body reintroduces nesting, forces a block plus
> `yield`, and — worst — hides a case from the exhaustiveness analysis,
> because the compiler sees one arm where the code really has two.
> **Violation — enforced by `checkstyle/WhenShouldBeUsed`.**

```java
// bad — the arm is really two outcomes wearing one label
static String classify(Object value) {
  return switch (value) {
    case String s -> {
      if (s.isBlank()) {
        yield "blank";
      }
      yield "text of length " + s.length();
    }
    default -> "other";
  };
}

// good — one arm per outcome, guard first
static String classify(Object value) {
  return switch (value) {
    case String s when s.isBlank() -> "blank";
    case String s -> "text of length " + s.length();
    default -> "other";
  };
}
```

## 23.11 Peel failure cases off with guard clauses so the happy path stays at the leftmost indentation.

> Why? Deep `if` nesting forces the reader to hold every enclosing condition
> in working memory to understand the innermost line, and it makes the
> success path the hardest branch to find. Guard clauses invert that: each
> early return disposes of one precondition permanently, and by the time the
> real work appears every assumption behind it has already been established
> on a line of its own. **Suggestion.**

```java
// bad — the one line that matters is four levels deep
String resolve(User user) {
  if (user != null) {
    if (user.isActive()) {
      Profile profile = user.profile();
      if (profile != null) {
        return profile.displayName();
      }
    }
  }
  return "unknown";
}

// good — each guard removes one case; the result is flat
String resolve(User user) {
  if (user == null || !user.isActive()) {
    return "unknown";
  }
  Profile profile = user.profile();
  if (profile == null) {
    return "unknown";
  }
  return profile.displayName();
}
```

## 23.12 Write the condition in its positive form, and drop the `else` after a branch that returns.

> Why? `if (!x) { A } else { B }` asks the reader to invert the condition
> mentally and then re-associate the branches, for no benefit over
> `if (x) { B } else { A }`. And once a branch returns, `else` adds an
> indentation level that carries no information — the code after the `if`
> is *already* the else. **Suggestion.**

```java
// bad — negated test plus an else that a return already implies
if (!cache.containsKey(key)) {
  return load(key);
} else {
  return cache.get(key);
}

// good
if (cache.containsKey(key)) {
  return cache.get(key);
}
return load(key);
```

## 23.13 Use the enhanced `for` loop unless you genuinely need the index.

> Why? Effective Java, 3rd ed., Item 58 ("Prefer for-each loops to
> traditional for loops") notes that the enhanced form removes the index
> and iterator variables entirely, which removes the whole family of bugs
> that live on them: off-by-one bounds, the wrong list indexed inside a
> nested loop, and `get(i)` on a `LinkedList` turning an O(n) loop into
> O(n²). Keep the indexed form only when the index is part of the result.
> **Suggestion.**

```java
// bad — the index exists only to fetch the element
for (int i = 0; i < orders.size(); i++) {
  total = total.add(orders.get(i).amount());
}

// good
for (Order order : orders) {
  total = total.add(order.amount());
}
```

## 23.14 Never reassign a `for` loop's control variable inside the loop body.

> Why? A `for` header is a contract: the reader takes the init, condition,
> and update clauses as the complete description of how the variable moves.
> Mutating it in the body breaks that contract silently, and the resulting
> skip or infinite loop is invisible at the header where everyone looks
> first. Whatever the reassignment was trying to express — an early exit, a
> variable stride — has a direct spelling. **Violation — enforced by
> `checkstyle/ModifiedControlVariable`.**

```java
// bad — "break", spelled the hard way
for (int i = 0; i < items.size(); i++) {
  if (items.get(i).isTerminal()) {
    i = items.size();
    continue;
  }
  process(items.get(i));
}

// good
for (Item item : items) {
  if (item.isTerminal()) {
    break;
  }
  process(item);
}
```

## 23.15 Never assign inside a condition.

> Why? An assignment nested in a subexpression makes a line do two things
> while looking like it does one, and it is the classic camouflage for the
> `=`/`==` typo. Hoisting it to its own statement costs one line and makes
> both the value and the test independently reviewable. **Violation —
> enforced by `checkstyle/InnerAssignment`.**

```java
// bad — the assignment hides inside the test
int matched;
if ((matched = count(pattern, text)) > 0) {
  log.info("matched {} times", matched);
}

// good
int matched = count(pattern, text);
if (matched > 0) {
  log.info("matched {} times", matched);
}
```

## 23.16 Use the ternary operator only when the whole expression fits on one line, and never nest one.

> Why? A single short ternary reads as one idea and is often clearer than a
> four-line `if`/`else`. A nested one does not: `a ? b : c ? d : e` has no
> visual grouping, and the reader has to recover the precedence by counting
> colons. Once you have more than two outcomes, the construct you want is a
> method with early returns (§23.11) or a `switch` expression (§23.3).
> **Suggestion.**

```java
// bad — three chained ternaries in one expression, wrapped to fit
String tier = points > 1000 ? "gold" : points > 500 ? "silver"
    : points > 100 ? "bronze" : "none";

// good — one condition per line, in a method that names the concept
static String tier(int points) {
  if (points > 1000) {
    return "gold";
  }
  if (points > 500) {
    return "silver";
  }
  if (points > 100) {
    return "bronze";
  }
  return "none";
}

// good — a single, short ternary is fine
String noun = count == 1 ? "item" : "items";
```

## 23.17 Never compare a boolean to a literal, and never wrap a boolean expression in `if`/`return true`/`return false`.

> Why? `x == true` is `x` with extra opportunities to typo `=`, and
> `if (p) return true; else return false;` is `return p;` written in five
> lines. Both forms bury the actual predicate, which is the thing a reviewer
> needs to check. **Violation — enforced by
> `checkstyle/SimplifyBooleanExpression` and
> `checkstyle/SimplifyBooleanReturn`.**

```java
// bad
boolean isEligible(Account account) {
  if (account.isVerified() == true && account.isClosed() == false) {
    return true;
  } else {
    return false;
  }
}

// good
boolean isEligible(Account account) {
  return account.isVerified() && !account.isClosed();
}
```

## 23.18 Treat a labelled `break` or `continue` as a signal to extract a method.

> Why? A label is the only construct in Java that lets control jump across
> more than one enclosing block, so it defeats the reader's normal
> assumption that a `break` ends the nearest loop. In practice almost every
> labelled break is a search that wants to be a method: `return` does the
> same job, names the result, and lets the caller see the outcome as a
> value rather than as a mutated local. **Suggestion.**

```java
// bad — a label to escape two loops, and a mutable "found" holder
Site found = null;
outer:
for (Region region : regions) {
  for (Site site : region.sites()) {
    if (site.id().equals(target)) {
      found = site;
      break outer;
    }
  }
}

// good — extraction turns the label into a return
static Optional<Site> findSite(List<Region> regions, String target) {
  for (Region region : regions) {
    for (Site site : region.sites()) {
      if (site.id().equals(target)) {
        return Optional.of(site);
      }
    }
  }
  return Optional.empty();
}
```

## 23.19 Never use an exception to terminate a loop or select a branch.

> Why? Effective Java, 3rd ed., Item 69 ("Use exceptions only for
> exceptional conditions") gives the canonical failure: an exception-driven
> loop is slower (the JVM cannot optimise across a `try` block the way it
> optimises a bounds check), and — far worse — the `catch` will also swallow
> an unrelated exception thrown from deep inside the loop body, silently
> converting a real bug into a normal-looking termination. See
> [Chapter 24, §24.1-§24.2](24-exceptions.md) for the full treatment,
> including what to offer callers instead. **Suggestion.**

```java
// bad — the loop ends by throwing, and any AIOOBE from process() is eaten
try {
  int i = 0;
  while (true) {
    process(items[i++]);
  }
} catch (ArrayIndexOutOfBoundsException e) {
  // done
}

// good
for (Item item : items) {
  process(item);
}
```
