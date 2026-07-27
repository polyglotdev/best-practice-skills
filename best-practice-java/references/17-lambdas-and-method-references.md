<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 17. Lambdas & Method References

A lambda is an instance of a functional interface written as an expression.
Java has had function objects since 1.0 in the form of anonymous classes;
what Java 8 added was a syntax concise enough that passing behaviour around
stopped being a code smell. This chapter is about the discipline that makes
that concision pay off: when a lambda beats an anonymous class, when a
method reference beats a lambda, which functional interface to target, and
what a lambda can and cannot capture.

It covers **Effective Java, 3rd ed., Items 42–44** ("Prefer lambdas to
anonymous classes", "Prefer method references to lambdas", "Favor the use of
standard functional interfaces"), plus the parts of the
[`java.util.function` package](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html)
and the [`Comparator`
API](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html)
that determine which interface a lambda should target.

What you *do* with those function objects once you have them — pipelines,
collectors, laziness, parallelism — is [Chapter 18](18-streams.md).
Absence-of-value modelling with `Optional` is
[Chapter 19](19-optional.md). Interface and abstract-class design is
[Chapter 11](11-classes-and-interfaces.md), and the generics variance rules
that govern `? super T` / `? extends R` in functional-interface signatures
are [Chapter 16](16-generics.md).

**Tool alignment:** Error Prone ships several checks in this area —
`UnnecessaryLambda`, `UnnecessaryMethodReference`, `AmbiguousMethodReference`,
`FunctionalInterfaceClash`, and `FunctionalInterfaceMethodChanged`. Rules
below that map to one of these are labeled **Violation**; the rest are
**Suggestion**.

## 17.1 Prefer a lambda to an anonymous class whenever the target type is a functional interface.

> Why? Effective Java, 3rd ed., Item 42 is titled "Prefer lambdas to anonymous
> classes" for exactly this reason: the anonymous class was the only way to
> pass behaviour before Java 8, and its verbosity made function objects
> unattractive enough that Java code went out of its way to avoid them. Six
> lines of class ceremony around one comparison expression put the reader's
> attention on the ceremony.

```java
// bad — six lines of ceremony around one comparison
Collections.sort(
    words,
    new Comparator<String>() {
      @Override
      public int compare(String s1, String s2) {
        return Integer.compare(s1.length(), s2.length());
      }
    });

// good
words.sort(Comparator.comparingInt(String::length));
```

## 17.2 Use an anonymous class when the target is an abstract class, has more than one abstract method, or the body needs a reference to itself.

> Why? Lambdas are limited to functional interfaces — a single abstract
> method, no more, and no abstract class. Effective Java, Item 42 also notes
> the `this` difference: "in a lambda, the `this` keyword refers to the
> enclosing instance," so a body that needs to refer to *the function object
> itself* (to unregister a listener, to recurse, to log its own identity)
> cannot be a lambda. See 17.15.

```java
// bad — a lambda has no self-reference; `this` is the enclosing service,
// not the listener, so this unregisters the wrong object (or fails to compile)
bus.register(
    event -> {
      handle(event);
      bus.unregister(this); // wrong receiver
    });

// good — an anonymous class has its own identity
bus.register(
    new EventListener() {
      @Override
      public void onEvent(Event event) {
        handle(event);
        bus.unregister(this);
      }
    });
```

## 17.3 Omit lambda parameter types; add them back only when they genuinely aid the reader or you need an annotation.

> Why? Effective Java, Item 42 is unambiguous: "Omit the types of all lambda
> parameters unless their presence makes your program clearer." The compiler
> infers them from the target type, and repeating them adds noise without
> adding information. When you *do* need a modifier or a type-use annotation
> on a parameter, use `var` parameters so every parameter stays uniform —
> Java forbids mixing inferred, explicit, and `var` forms in one lambda.

```java
// bad — the types are already implied by Map<String, Integer>
counts.forEach((String key, Integer value) -> log.info("{}={}", key, value));

// bad — illegal: cannot mix `var` with an inferred parameter
BiFunction<String, String, String> join = (var a, b) -> a + b;

// good
counts.forEach((key, value) -> log.info("{}={}", key, value));

// good — the `var` form on every parameter, so a modifier can be attached
BiFunction<String, String, String> join = (final var left, final var right) -> left + right;
```

## 17.4 Keep a lambda to one expression; three lines is the practical ceiling.

> Why? Effective Java, Item 42: "Lambdas lack names and documentation; if a
> computation isn't self-explanatory, or exceeds a few lines, don't put it in
> a lambda." Lambdas are read inline, at the call site, with no signature and
> no Javadoc to lean on. A block-bodied lambda spanning ten lines is a method
> that has been denied a name — give it one and reference it (17.5).

```java
// bad — an unnamed, undocumented method wedged into an argument list
orders.stream()
    .filter(
        order -> {
          if (order.status() != Status.SETTLED) {
            return false;
          }
          BigDecimal net = order.gross().subtract(order.fees());
          return net.compareTo(MINIMUM_NET) >= 0 && !order.customer().isInternal();
        })
    .toList();

// good — the predicate has a name, a home, and a place to hang Javadoc
orders.stream().filter(OrderFilters::isBillableSettlement).toList();
```

## 17.5 Prefer a method reference to a lambda when the reference is at least as clear.

> Why? Effective Java, Item 43: "Method references usually result in shorter,
> clearer code" and "where method references are shorter and clearer, use
> them; where they aren't, stick with lambdas." A method reference names an
> existing operation instead of restating it, so the reader sees *what* is
> being done rather than the plumbing that does it.

```java
// bad — restates method calls that already have names
map.merge(key, 1, (count, increment) -> count + increment);
tokens.stream().map(token -> Integer.parseInt(token)).toList();

// good
map.merge(key, 1, Integer::sum);
tokens.stream().map(Integer::parseInt).toList();
```

## 17.6 Keep the lambda when the parameter names carry meaning the method reference throws away.

> Why? Effective Java, Item 43 offers the counterexample directly: in a class
> named `GoshThisClassNameIsHumongous`, `service.execute(() -> action())` beats
> `service.execute(GoshThisClassNameIsHumongous::action)`. The same applies
> whenever the lambda's parameter names document the domain — a reference
> like `Rules::check` hides which argument is the subject and which is the
> policy.

```java
// bad — the reader cannot tell what the two arguments are
policies.stream().anyMatch(ruleEngine::permits);

// good — parameter name states the domain role
policies.stream().anyMatch(policy -> ruleEngine.permits(actor, policy));
```

## 17.7 Know all five method-reference forms and pick the one that expresses the operation.

> Why? Effective Java, Item 43 tabulates exactly five kinds: static, bound
> instance, unbound instance, class constructor, and array constructor.
> Confusing the bound and unbound forms is the most common mistake — `String::length`
> (unbound) takes the receiver as its parameter, while `cutoff::isAfter`
> (bound) has already captured its receiver and takes only the argument.
> Getting this wrong is a compile error at best and a silently wrong target
> type at worst.

```java
// good — static: the class supplies the method, arguments supply everything else
Function<String, Integer> parse = Integer::parseInt;

// good — bound instance: `cutoff` is captured now, the argument comes later
Instant cutoff = Instant.now();
Predicate<Instant> isStale = cutoff::isAfter;

// good — unbound instance: the first argument becomes the receiver
Function<String, Integer> length = String::length;

// good — class constructor: a factory for the type
Supplier<TreeMap<String, Integer>> mapFactory = TreeMap::new;

// good — array constructor: length in, array out
IntFunction<String[]> arrayFactory = String[]::new;
```

## 17.8 Do not write a method reference that just re-references the variable it is called on.

> Why? A reference like `predicate::test` on a value that is already a
> `Predicate` allocates a new function object that delegates to the original
> for no benefit, and obscures that the two are the same thing. Error Prone
> flags it: "This method reference is unnecessary, and can be replaced with
> the variable itself." **Violation — enforced by Error Prone
> `UnnecessaryMethodReference`.**

```java
// bad — wraps an existing Predicate in an identical Predicate
Predicate<Order> isLarge = order -> order.total().compareTo(THRESHOLD) > 0;
List<Order> large = orders.stream().filter(isLarge::test).toList();

// good
Predicate<Order> isLarge = order -> order.total().compareTo(THRESHOLD) > 0;
List<Order> large = orders.stream().filter(isLarge).toList();
```

## 17.9 Do not hoist a lambda into a constant or return it from a helper method — write a real method and reference it.

> Why? A `private static final Function<...>` field is a method with the
> wrong shape: it has no name a stack trace will show, no parameter names, no
> Javadoc, and it forces a heap allocation at class-init time. Error Prone's
> guidance is to "implement the functional interface method directly and use
> a method reference instead." **Violation — enforced by Error Prone
> `UnnecessaryLambda`.**

```java
// bad — a method in disguise
private static final Function<Order, String> TO_LABEL =
    order -> order.customer().name() + " #" + order.id();

String label = TO_LABEL.apply(order);

// good — a real method, referenceable and stack-traceable
private static String toLabel(Order order) {
  return order.customer().name() + " #" + order.id();
}

String label = toLabel(order);
Stream<String> labels = orders.stream().map(OrderLabels::toLabel);
```

## 17.10 Favor the standard functional interfaces in `java.util.function` over declaring your own.

> Why? Effective Java, Item 44: "If one of the standard functional interfaces
> does the job, you should generally use it in preference to a
> purpose-built functional interface." The
> [package](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html)
> ships 43 interfaces, all derived from six basic shapes — `UnaryOperator<T>`,
> `BinaryOperator<T>`, `Predicate<T>`, `Function<T, R>`, `Supplier<T>`, and
> `Consumer<T>`. A custom clone of one of these means every caller must learn
> a new name for a shape they already know, and it cannot compose with the
> default methods (`andThen`, `compose`, `negate`, `or`) the standard
> interfaces provide.

```java
// bad — a hand-rolled Predicate<Map.Entry<K, V>> under a different name
@FunctionalInterface
interface EntryTest<K, V> {
  boolean shouldRemove(Map.Entry<K, V> entry);
}

// good — composes with negate(), and(), or()
Predicate<Map.Entry<String, Session>> isExpired =
    entry -> entry.getValue().expiresAt().isBefore(Instant.now());
sessions.entrySet().removeIf(isExpired);
```

## 17.11 Use the primitive specializations; never a boxed functional interface on a hot path.

> Why? Effective Java, Item 44: "Don't be tempted to use basic functional
> interfaces with boxed primitives instead of primitive functional
> interfaces… the performance consequences can be dire." Each
> `Function<Integer, Integer>` call boxes on the way in and on the way out;
> in a loop over a million elements that is two million short-lived objects
> the primitive specialization never allocates. Every basic shape has `Int`,
> `Long`, and `Double` variants, plus the `ToIntFunction` / `IntToLongFunction`
> cross-type forms.

```java
// bad — two boxing conversions per element
Function<Integer, Integer> doubled = n -> n * 2;
Predicate<Long> isEven = n -> n % 2 == 0;
Function<Order, Integer> weight = Order::weightGrams;

// good — no allocation
IntUnaryOperator doubled = n -> n * 2;
LongPredicate isEven = n -> n % 2 == 0;
ToIntFunction<Order> weight = Order::weightGrams;
```

## 17.12 Declare a custom functional interface only when it earns a descriptive name, a documented contract, or its own default methods.

> Why? Effective Java, Item 44 gives `Comparator<T>` as the model: it is
> structurally identical to `ToIntBiFunction<T, T>`, yet it deserves to exist
> because its name is descriptive and commonly used, it carries "a strong
> contract" (the total-order requirements `compare` must satisfy), and it
> benefits from a long list of custom default methods. If a candidate
> interface satisfies
> none of those three, it is a rename of a standard interface and should be
> deleted. Always annotate a genuine one with
> [`@FunctionalInterface`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/FunctionalInterface.html)
> so the compiler rejects a second abstract method.

```java
// bad — a rename of BiFunction<Money, TaxCode, Money>, no contract, no defaults
interface TaxCalc {
  Money calc(Money amount, TaxCode code);
}

// good — descriptive name, documented contract, its own composition default
@FunctionalInterface
public interface RetryPolicy {

  /**
   * Returns the delay before attempt {@code attempt}, or empty to stop retrying.
   *
   * <p>Implementations must be side-effect free and must return the same result
   * for the same attempt number.
   *
   * @param attempt the 1-based attempt number that just failed
   * @return the delay before the next attempt, or empty to give up
   */
  Optional<Duration> delayBefore(int attempt);

  /** Returns a policy that stops after {@code maxAttempts} attempts. */
  default RetryPolicy cappedAt(int maxAttempts) {
    return attempt -> attempt >= maxAttempts ? Optional.empty() : delayBefore(attempt);
  }
}
```

## 17.13 Never overload a method so that two overloads take different functional interfaces in the same argument position.

> Why? A lambda has no type of its own — the compiler picks the target type
> from the applicable overloads, and when two of them are functional
> interfaces the call becomes ambiguous or, worse, silently resolves to the
> wrong one. Effective Java, Item 44 cites `ExecutorService.submit`, which is
> overloaded for `Callable<T>` and `Runnable` and therefore forces callers to
> cast. Error Prone reports this at the *declaration* site: "Overloads will be
> ambiguous when passing lambda arguments." **Violation — enforced by Error
> Prone `FunctionalInterfaceClash`.**

```java
// bad — callers must cast to disambiguate
public void schedule(Runnable task) { ... }
public void schedule(Callable<Void> task) { ... }

scheduler.schedule(() -> cleanup()); // ambiguous

// good — distinct names, no cast, no ambiguity
public void scheduleRunnable(Runnable task) { ... }
public void scheduleCallable(Callable<Void> task) { ... }
```

## 17.14 A lambda captures only effectively final locals — restructure the computation rather than smuggling state out through a mutable holder.

> Why? The restriction exists because the lambda may outlive the frame that
> created it and may run on another thread; capturing a mutable local would
> make the value the lambda sees unpredictable. Defeating the rule with a
> one-element array does not make the code correct — it makes the data race
> invisible. If you need an accumulated result, use a reduction
> ([Chapter 18, §18.3](18-streams.md)); if you need shared mutable state, use
> an explicit concurrent type ([Chapter 26](26-concurrency-fundamentals.md)).

```java
// bad — the array is a loophole, not a fix; unsafe the moment this goes parallel
long[] total = new long[1];
orders.forEach(order -> total[0] += order.amountCents());
return total[0];

// good — a reduction, correct sequentially and in parallel
return orders.stream().mapToLong(Order::amountCents).sum();
```

## 17.15 Remember that `this` inside a lambda is the enclosing instance — a lambda that touches an instance member captures the whole enclosing object.

> Why? Effective Java, Item 42: "in a lambda, the `this` keyword refers to the
> enclosing instance," unlike an anonymous class where it refers to the
> anonymous instance. The consequence bites when the lambda is stored
> somewhere long-lived: registering `event -> handle(event)` in a static
> registry keeps the entire enclosing service reachable for as long as the
> registry holds the listener. Capture the specific values you need instead
> of an implicit `this`.

```java
// bad — implicitly captures `this`, pinning the whole service in the registry
class ReportService {
  private final ReportRenderer renderer;

  void register(GlobalRegistry registry) {
    registry.addListener(event -> renderer.render(event)); // captures this.renderer
  }
}

// good — capture only the collaborator the callback actually needs
class ReportService {
  private final ReportRenderer renderer;

  void register(GlobalRegistry registry) {
    ReportRenderer local = this.renderer;
    registry.addListener(local::render);
  }
}
```

## 17.16 Handle checked exceptions at the lambda boundary; never sneaky-throw them past the compiler.

> Why? A lambda may only throw what its target functional interface declares,
> and none of the `java.util.function` interfaces declare checked exceptions.
> The generic-cast "sneaky throw" trick smuggles an `IOException` out of a
> method whose signature says it cannot throw one, so no caller can catch it
> by type and no compiler can warn about it. Google Java Style
> [§6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> makes the related point that "it is very rarely correct to do nothing in
> response to a caught exception" — swallowing the exception inside the
> lambda is the other half of this anti-pattern. The sane options are to wrap
> into an unchecked exception at the boundary, to declare a throwing
> functional interface of your own, or to abandon the pipeline for a loop
> ([Chapter 18, §18.2](18-streams.md)).

```java
// bad — the compiler is lied to; callers cannot catch IOException by type
@SuppressWarnings("unchecked")
static <E extends Throwable> void sneakyThrow(Throwable t) throws E {
  throw (E) t;
}

Stream<String> bodies =
    paths.stream()
        .map(
            path -> {
              try {
                return Files.readString(path);
              } catch (IOException e) {
                sneakyThrow(e); // vanishes from the signature
                return null;
              }
            });

// good — wrap at the boundary in the JDK's own unchecked wrapper
Stream<String> bodies =
    paths.stream()
        .map(
            path -> {
              try {
                return Files.readString(path);
              } catch (IOException e) {
                throw new UncheckedIOException("read " + path, e);
              }
            });

// also good — a declared throwing interface, adapted once at the edge
@FunctionalInterface
interface IoFunction<T, R> {
  R apply(T input) throws IOException;
}

static <T, R> Function<T, R> unchecked(IoFunction<T, R> fn) {
  return input -> {
    try {
      return fn.apply(input);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  };
}

Stream<String> bodies = paths.stream().map(unchecked(Files::readString));
```

## 17.17 Do not serialize a lambda or a method reference.

> Why? Effective Java, Item 42: "you should rarely, if ever, serialize a
> lambda." The serialized form of a lambda depends on compiler-generated
> names that are explicitly unspecified and may change between compilations
> of the same source — a value serialized by one build can fail to
> deserialize under the next. When a function object genuinely must be
> serializable (a `Comparator` stored in a serialized `TreeMap`, say), use a
> private static nested class with a stable name. Note also that the cast only
> makes the object *declare* `Serializable`: anything the lambda captured must
> be serializable too, or writing it throws `NotSerializableException` at
> runtime.

```java
// bad — the intersection cast makes the lambda serializable, but its
// serialized form depends on unspecified synthetic naming
Comparator<Employee> bySeniority =
    (Comparator<Employee> & Serializable) (a, b) -> a.hiredOn().compareTo(b.hiredOn());

// good — a named type with a stable serialized form
private static final class BySeniority
    implements Comparator<Employee>, Serializable {

  private static final long serialVersionUID = 1L;

  @Override
  public int compare(Employee a, Employee b) {
    return a.hiredOn().compareTo(b.hiredOn());
  }
}
```

## 17.18 Build comparators from `Comparator` combinators instead of hand-written arithmetic lambdas.

> Why? `(a, b) -> a.weight() - b.weight()` overflows for weights that differ
> by more than `Integer.MAX_VALUE`, and it silently returns a wrong ordering
> rather than failing. The
> [`Comparator`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html)
> factories — `comparing`, `comparingInt`, `comparingLong`,
> `comparingDouble`, `thenComparing`, `reversed`, `nullsFirst` — are correct
> by construction and compose without nesting ternaries. `comparingInt` also
> avoids the boxing that plain `comparing` would incur (17.11).

```java
// bad — overflows, and the tiebreak is an unreadable nested ternary
Comparator<Item> order =
    (a, b) ->
        a.weight() != b.weight() ? a.weight() - b.weight() : a.name().compareTo(b.name());

// good
Comparator<Item> order =
    Comparator.comparingInt(Item::weight).thenComparing(Item::name);
```

## 17.19 Give lambda parameters real names once the lambda outgrows a single obvious argument.

> Why? Google Java Style
> [§5.2.6](https://google.github.io/styleguide/javaguide.html#s5.2.6-parameter-names)
> governs parameter naming, and a lambda parameter is a parameter. Single
> letters are fine for a truly generic operation (`s -> s.isBlank()`), but in
> a multi-argument lambda over domain types, `(a, b)` forces the reader to
> reconstruct the roles from the interface's type arguments. Named parameters
> are the only documentation a lambda gets.

```java
// bad — which is the accumulator and which is the element?
Map<String, Integer> totals =
    lines.stream()
        .collect(Collectors.toMap(Line::sku, Line::quantity, (a, b) -> a + b));

// good
Map<String, Integer> totals =
    lines.stream()
        .collect(
            Collectors.toMap(
                Line::sku, Line::quantity, (existing, duplicate) -> existing + duplicate));
```

## 17.20 Do not add a second abstract method to a published `@FunctionalInterface`, and do not narrow a functional interface by subtyping it just to change lambda behaviour.

> Why? `@FunctionalInterface` is a compile-time contract: adding a second
> abstract method breaks every lambda that targets it, across every caller,
> at compile time. The subtler failure is declaring
> `interface OrderFilter extends Predicate<Order>` purely to attach a
> different default implementation — Error Prone warns that "casting a lambda
> to this `@FunctionalInterface` can cause a behavior change from casting to a
> functional superinterface, which is surprising to users" and recommends
> decorator methods instead. **Violation — enforced by Error Prone
> `FunctionalInterfaceMethodChanged`.**

```java
// bad — a subinterface that redefines inherited default behaviour
@FunctionalInterface
interface OrderFilter extends Predicate<Order> {
  @Override
  default Predicate<Order> negate() {
    return order -> true; // surprising: differs from Predicate.negate()
  }
}

// good — a decorator method, no subtyping, no surprise
static Predicate<Order> excluding(Predicate<Order> filter) {
  return order -> !filter.test(order);
}
```
