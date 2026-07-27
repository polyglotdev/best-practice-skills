<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 18. Streams

The Streams API is a fluent syntax for expressing a computation over a
sequence as a pipeline of transformations. It is not a replacement for
iteration, and treating it as one produces the single most common failure
mode in modern Java: a correct pipeline nobody can read. This chapter is
about knowing which computations belong in a pipeline, which belong in a
loop, and how to express the pipeline ones so the next reader can follow
them.

It covers **Effective Java, 3rd ed., Items 45–48** ("Use streams
judiciously", "Prefer side-effect-free functions in streams", "Prefer
Collection to Stream as a return type", "Use caution when making streams
parallel"), grounded in the normative
[`java.util.stream` package
documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html)
and the
[`Stream`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html)
and
[`Collectors`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html)
API docs.

The lambdas and method references that populate a pipeline are
[Chapter 17](17-lambdas-and-method-references.md). `Optional`, which several
terminal operations return, is [Chapter 19](19-optional.md). Collection type
selection and immutability are [Chapter 20](20-collections.md), and the
threading model that `parallel()` quietly opts you into is
[Chapter 26](26-concurrency-fundamentals.md).

**Tool alignment:** Error Prone enforces several rules below —
`StreamToString`, `StreamResourceLeak`, `StreamToIterable`,
`ReturnValueIgnored`, `MixedMutabilityReturnType`, and
`CollectorShouldNotUseState`. Rules mapping to one of these are labeled
**Violation**; the rest are **Suggestion**.

## 18.1 Use a stream only where it makes the computation clearer than a loop.

> Why? Effective Java, Item 45: "Overusing streams makes programs hard to
> read and maintain," and "in the absence of explicit types, careful naming
> of lambda parameters is essential to the readability of stream pipelines."
> A stream buys you declarative composition; it costs you named intermediate
> variables, a debugger you can step through, and a stack trace that points
> at your own line numbers. Spend the cost only when the pipeline is a
> genuine map/filter/reduce shape.

```java
// bad — a loop wearing a stream costume; every step is obscured
words.stream()
    .collect(
        Collectors.groupingBy(
            word ->
                word.chars()
                    .sorted()
                    .collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append)
                    .toString()))
    .values()
    .stream()
    .filter(group -> group.size() >= minGroupSize)
    .map(group -> group.size() + ": " + group)
    .forEach(System.out::println);

// good — the classifier gets a name, and the pipeline reads as three steps
Map<String, List<String>> byAnagram =
    words.stream().collect(Collectors.groupingBy(Anagrams::alphabetize));

byAnagram.values().stream()
    .filter(group -> group.size() >= minGroupSize)
    .forEach(group -> System.out.println(group.size() + ": " + group));
```

## 18.2 Keep the loop when the body must mutate a local, `break`, `continue`, `return` from the enclosing method, or throw a checked exception.

> Why? Effective Java, Item 45 lists exactly this: "from a code block, you can
> read or modify any local variable in scope; from a lambda, you can only read
> final or effectively final variables… from a code block, you can `return`
> from the enclosing method, `break` or `continue` an enclosing loop, or
> throw any checked exception… from a lambda you can do none of these
> things." A pipeline that has to fake these with flags, sentinel values, or
> sneaky throws ([Chapter 17, §17.16](17-lambdas-and-method-references.md)) is
> strictly worse than the loop it replaced.

```java
// bad — checked exception laundered, early return faked with a sentinel
Optional<Config> first =
    paths.stream()
        .map(
            path -> {
              try {
                return parse(Files.readString(path)); // throws IOException
              } catch (IOException e) {
                return null; // sentinel, then filtered away, cause lost
              }
            })
        .filter(Objects::nonNull)
        .findFirst();

// good — the loop says what it means
for (Path path : paths) {
  String source = Files.readString(path); // enclosing method declares throws IOException
  Config config = parse(source);
  if (config.isComplete()) {
    return Optional.of(config);
  }
}
return Optional.empty();
```

## 18.3 Never build a result by mutating an external collection from `forEach`.

> Why? The package documentation is explicit that this is an "unnecessary use
> of side-effects," and that it "can often lead to unwitting violations of the
> statelessness requirement, as well as other thread-safety hazards." Effective
> Java, Item 46 puts it as a rule: "The `forEach` operation should be used only
> to report the result of a stream computation, not to perform the
> computation." An external `ArrayList` mutated from a lambda is a data race
> waiting for someone to add `.parallel()`.

```java
// bad — side-effecting accumulation; breaks the instant this goes parallel
List<String> results = new ArrayList<>();
lines.stream().filter(pattern.asMatchPredicate()).forEach(line -> results.add(line));

// good — a reduction, safe sequentially and in parallel
List<String> results = lines.stream().filter(pattern.asMatchPredicate()).toList();
```

## 18.4 Keep behavioural parameters stateless and non-interfering.

> Why? The package documentation defines a stateful lambda as "one whose
> result depends on any state which might change during the execution of the
> stream pipeline," and warns that "stream pipeline results may be
> nondeterministic or incorrect" when one is used. It also forbids
> interference: "preventing interference means ensuring that the data source
> is *not modified at all* during the execution of the stream pipeline." Both
> failures are silent — you get a plausible wrong answer, not an exception.

```java
// bad — stateful mapper; the same input can produce different output per run
Set<Integer> seen = ConcurrentHashMap.newKeySet();
List<Integer> marked =
    ids.parallelStream().map(id -> seen.add(id) ? 0 : id).toList();

// bad — interference: the source is mutated mid-pipeline
list.stream().filter(Item::isStale).forEach(list::remove); // may throw or corrupt

// good — the same "seen before?" intent, expressed statelessly
List<Integer> distinctIds = ids.stream().distinct().toList();

// good — removal is a collection operation, not a pipeline side effect
list.removeIf(Item::isStale);
```

## 18.5 Prefer `Stream.toList()` to `collect(Collectors.toList())`, and know that they differ.

> Why? `Collectors.toList()` documents that "there are no guarantees on the
> type, mutability, serializability, or thread-safety of the `List`
> returned" — in practice it hands back a mutable `ArrayList`, which callers
> then mutate, which then becomes an accidental part of your contract.
> [`Stream.toList()`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html)
> (Java 16+) is explicit: "The returned List is unmodifiable; calls to any
> mutator method will always cause `UnsupportedOperationException` to be
> thrown." The one behavioural difference worth knowing:
> `Collectors.toUnmodifiableList()` "disallows null values and will throw
> `NullPointerException` if it is presented with a null value," while
> `Stream.toList()` permits them — its documented implementation is
> `Collections.unmodifiableList(new ArrayList<>(Arrays.asList(this.toArray())))`.

```java
// bad — mutable by accident, and longer to say
List<String> names = users.stream().map(User::name).collect(Collectors.toList());

// good — unmodifiable, permits nulls
List<String> names = users.stream().map(User::name).toList();

// good — unmodifiable and null-hostile, when nulls must be a hard error
List<String> names =
    users.stream().map(User::name).collect(Collectors.toUnmodifiableList());
```

## 18.6 Always supply a merge function to `Collectors.toMap` when duplicate keys are possible.

> Why? The two-argument `toMap` documents that "if the mapped keys contain
> duplicates (according to `Object.equals(Object)`), an
> `IllegalStateException` is thrown when the collection operation is
> performed." That is a production failure triggered by data, not by code, so
> it will not show up in a test that uses distinct fixtures. The three-argument
> overload takes a `BinaryOperator<U>` and makes the collision policy
> explicit. Both overloads also reject null values.

```java
// bad — throws IllegalStateException the first time two users share an email
Map<String, User> byEmail =
    users.stream().collect(Collectors.toMap(User::email, Function.identity()));

// good — collision policy stated: last write wins
Map<String, User> byEmail =
    users.stream()
        .collect(Collectors.toMap(User::email, Function.identity(), (first, second) -> second));

// good — when duplicates are genuinely illegal, fail with a message you can act on
Map<String, User> byEmail =
    users.stream()
        .collect(
            Collectors.toMap(
                User::email,
                Function.identity(),
                (first, second) -> {
                  throw new IllegalStateException("duplicate email: " + first.email());
                }));
```

## 18.7 Never rely on the concrete type, mutability, or iteration order of a collector's result — pass a factory when it matters.

> Why? `groupingBy` documents that "there are no guarantees on the type,
> mutability, serializability, or thread-safety of the `Map` or `List` objects
> returned." Code that iterates a `groupingBy` result and expects insertion or
> sorted order is relying on the current `HashMap` implementation, and will
> reorder on a JDK upgrade or a change in key distribution. The three-argument
> overloads of `groupingBy` and `toMap` take a map factory; `toCollection`
> takes a collection factory.

```java
// bad — depends on unspecified HashMap ordering
Map<Department, List<Employee>> byDept =
    employees.stream().collect(Collectors.groupingBy(Employee::department));
byDept.forEach(this::renderSection); // iteration order is not defined

// good — ordering is part of the request, so ask for it
Map<Department, List<Employee>> byDept =
    employees.stream()
        .collect(
            Collectors.groupingBy(
                Employee::department, TreeMap::new, Collectors.toList()));
```

## 18.8 Use a downstream collector instead of grouping and then re-streaming each group.

> Why? `groupingBy(classifier, downstream)` reduces each group as it is built,
> in one traversal. Grouping into lists and then mapping over `entrySet()` builds
> every intermediate list only to throw it away, and doubles the amount of
> pipeline the reader has to hold in their head. `counting`, `summingInt`,
> `mapping`, `filtering`, `flatMapping`, `reducing`, and `collectingAndThen`
> all compose here.

```java
// bad — materializes every group, then discards it
Map<Department, Long> headcount =
    employees.stream()
        .collect(Collectors.groupingBy(Employee::department))
        .entrySet()
        .stream()
        .collect(Collectors.toMap(Map.Entry::getKey, entry -> (long) entry.getValue().size()));

// good — one traversal, one collector
Map<Department, Long> headcount =
    employees.stream()
        .collect(Collectors.groupingBy(Employee::department, Collectors.counting()));

// good — mapping downstream, so the groups hold names rather than whole records
Map<Department, Set<String>> namesByDept =
    employees.stream()
        .collect(
            Collectors.groupingBy(
                Employee::department,
                Collectors.mapping(Employee::name, Collectors.toSet())));
```

## 18.9 Use `partitioningBy` when the classifier is a predicate.

> Why? `partitioningBy` documents that "the returned `Map` always contains
> mappings for both `false` and `true` keys," so downstream code never has to
> null-check an absent branch. `groupingBy` on a boolean-returning classifier
> gives you a `Map<Boolean, List<T>>` whose keys are boxed `Boolean` objects
> and which omits a branch entirely when no element falls into it — the exact
> case that produces a `NullPointerException` in production and never in
> tests.

```java
// bad — the `true` key is missing when every order is small
Map<Boolean, List<Order>> split =
    orders.stream().collect(Collectors.groupingBy(order -> order.total().compareTo(BIG) > 0));
List<Order> large = split.get(true); // null when there are none

// good — both keys always present
Map<Boolean, List<Order>> split =
    orders.stream()
        .collect(Collectors.partitioningBy(order -> order.total().compareTo(BIG) > 0));
List<Order> large = split.get(true); // empty list, never null
```

## 18.10 Use `Collectors.joining` to build a delimited string, never `reduce` with `+` or a shared `StringBuilder`.

> Why? Reducing with string concatenation allocates a new `String` per element
> and is quadratic in the total length; a `StringBuilder` mutated from a lambda
> is the side-effect anti-pattern of 18.3 with a thread-safety bug attached.
> `joining` handles the delimiter, prefix, and suffix, and its accumulator is
> a `StringBuilder` the collector owns and combines correctly under
> parallelism.

```java
// bad — quadratic, and the separator handling is fiddly
String csv = names.stream().reduce("", (acc, name) -> acc.isEmpty() ? name : acc + "," + name);

// bad — shared mutable state in a lambda
StringBuilder sb = new StringBuilder();
names.forEach(name -> sb.append(name).append(','));

// good
String csv = String.join(",", names);
String rendered = names.stream().collect(Collectors.joining(", ", "[", "]"));
```

## 18.11 Use `Collectors.teeing` when you need two independent results from one traversal.

> Why? Traversing the same source twice is wrong when the source is
> resource-backed or single-use (18.14), and merely wasteful otherwise.
> [`teeing`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html)
> (Java 12+) feeds every element to two collectors and merges their results
> with a `BiFunction`, so min-and-max, count-and-sum, or matched-and-rejected
> come out of a single pass.

```java
// bad — two traversals over a stream that may not be re-traversable
long count = orders.stream().count();
BigDecimal total =
    orders.stream().map(Order::amount).reduce(BigDecimal.ZERO, BigDecimal::add);

// good — one traversal, one result
record Totals(long count, BigDecimal amount) {}

Totals totals =
    orders.stream()
        .collect(
            Collectors.teeing(
                Collectors.counting(),
                Collectors.reducing(BigDecimal.ZERO, Order::amount, BigDecimal::add),
                Totals::new));
```

## 18.12 Return a `Collection`, not a `Stream`, from a public API.

> Why? Effective Java, Item 47: "`Collection` or an appropriate subtype is
> generally the best return type for a public, sequence-returning method." A
> `Stream` cannot be iterated with a for-each loop without an awkward cast, it
> cannot be traversed twice, and it cannot be `size()`-checked — so every
> caller who wanted a collection must immediately collect it. Return a
> `Stream` only when the sequence is unbounded, expensive enough that laziness
> is the point, or backed by a resource that must be closed (18.13).

```java
// bad — forces every caller to collect, and forbids re-traversal
public Stream<Order> ordersFor(CustomerId id) {
  return repository.findAll().stream().filter(order -> order.customer().equals(id));
}

// good
public List<Order> ordersFor(CustomerId id) {
  return repository.findAll().stream()
      .filter(order -> order.customer().equals(id))
      .toList();
}

// good — Stream is right here: lazily produced and resource-backed

/**
 * Returns the parsed records of {@code file}, read lazily.
 *
 * <p>The returned stream holds an open file handle and must be closed by the
 * caller, ideally in a try-with-resources statement.
 */
public Stream<LogRecord> records(Path file) throws IOException {
  return Files.lines(file).map(LogRecord::parse);
}
```

## 18.13 Close every resource-backed stream with try-with-resources.

> Why? `Stream` extends `AutoCloseable`, and factories such as
> [`Files.lines`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/Files.html)
> and `Files.walk` hold an open file handle until the stream is closed. A
> terminal operation does not close it. Error Prone treats the leak as a bug:
> "Streams that encapsulate a closeable resource should be closed using
> try-with-resources." **Violation — enforced by Error Prone
> `StreamResourceLeak`.** Note the corollary for 18.12: if you return a
> resource-backed stream, its Javadoc must tell the caller to close it.

```java
// bad — the file handle leaks; on Windows the file stays locked
List<String> errors =
    Files.lines(path).filter(line -> line.contains("ERROR")).toList();

// good
try (Stream<String> lines = Files.lines(path)) {
  List<String> errors = lines.filter(line -> line.contains("ERROR")).toList();
}
```

## 18.14 A stream may be consumed exactly once — never store one in a field or pass it to two consumers.

> Why? The package documentation states that "after the terminal operation is
> performed, the stream pipeline is considered consumed, and can no longer be
> used; if you need to traverse the same data source again, you must return to
> the data source to get a new stream." The JDK's implementation signals reuse
> with `IllegalStateException: stream has already been operated upon or
> closed` — a runtime failure that only surfaces on the second call path,
> which is often the error path.

```java
// bad — the second terminal operation throws IllegalStateException
Stream<Order> pending = orders.stream().filter(Order::isPending);
long count = pending.count();
List<Order> list = pending.toList(); // IllegalStateException

// good — hold the source, derive a fresh stream per traversal
List<Order> pending = orders.stream().filter(Order::isPending).toList();
long count = pending.size();
```

## 18.15 Never call `toString()` on a stream, and never expose one as an `Iterable` via `stream::iterator`.

> Why? `Stream` does not override `Object.toString`, so logging one prints an
> implementation class name and an identity hash — Error Prone: "Calling
> `toString` on a `Stream` does not provide useful information." **Violation —
> enforced by Error Prone `StreamToString`.** The `stream::iterator` trick has
> the same shape of problem one level up: it produces "a one-shot `Iterable`,
> which may cause surprising failures" when anything iterates it twice.
> **Violation — enforced by Error Prone `StreamToIterable`.**

```java
// bad — logs "java.util.stream.ReferencePipeline$2@6d06d69c"
log.info("pending orders: {}", orders.stream().filter(Order::isPending));

// bad — a one-shot Iterable handed to code that assumes re-iteration
Stream<Order> pending = orders.stream().filter(Order::isPending);
process(pending::iterator);

// good
log.info("pending orders: {}", orders.stream().filter(Order::isPending).toList());
process(orders.stream().filter(Order::isPending).toList());
```

## 18.16 A pipeline without a terminal operation does nothing — never discard the result of an intermediate operation.

> Why? Intermediate operations "are always *lazy*; executing an intermediate
> operation such as `filter()` does not actually perform any filtering."
> Traversal begins only at the terminal operation, so a statement whose value
> is a `Stream` is dead code that looks like work. Error Prone flags the
> discarded return value: "Return value of this method must be used."
> **Violation — enforced by Error Prone `ReturnValueIgnored`.**

```java
// bad — filter is lazy; nothing is ever removed or evaluated
orders.stream().filter(Order::isStale);
names.stream().map(String::strip);

// good
List<Order> fresh = orders.stream().filter(Predicate.not(Order::isStale)).toList();
List<String> stripped = names.stream().map(String::strip).toList();
```

## 18.17 Use `peek` only for debugging, and never as a way to mutate elements.

> Why? The package documentation warns that "with the exception of terminal
> operations `forEach` and `forEachOrdered`, side-effects of behavioral
> parameters may not always be executed when the stream implementation can
> optimize away the execution of behavioral parameters without affecting the
> result of the computation." `peek` is precisely such an operation — a
> pipeline whose count can be computed without traversal may never invoke it.
> Logic that must run belongs in `map`, `forEach`, or a collector.

```java
// bad — audit() may never be called; the count is known from the source size
long total = orders.stream().peek(auditLog::record).count();

// good — the effect is the terminal operation, so it always runs
orders.forEach(auditLog::record);
long total = orders.size();
```

## 18.18 Return the same mutability from every path of a sequence-returning method.

> Why? A method that returns `List.of()` on the empty path and a mutable
> `ArrayList` on the populated path has a contract that depends on the data.
> Callers write `result.add(...)`, it passes in tests with non-empty
> fixtures, and it throws `UnsupportedOperationException` in production.
> Error Prone: "This method returns both mutable and immutable collections or
> maps from different paths. This may be confusing for users of the method."
> **Violation — enforced by Error Prone `MixedMutabilityReturnType`.**

```java
// bad — immutable on one path, mutable on the other
List<Order> pending(List<Order> all) {
  if (all.isEmpty()) {
    return List.of();
  }
  return new ArrayList<>(all.stream().filter(Order::isPending).toList());
}

// good — unmodifiable on every path
List<Order> pending(List<Order> all) {
  return all.stream().filter(Order::isPending).toList();
}
```

## 18.19 Make a stream parallel only when the source splits well, the pipeline is stateless and associative, and you have measured a win.

> Why? Effective Java, Item 48: "Do not parallelize stream pipelines
> indiscriminately. The performance consequences may be disastrous." The
> package documentation adds that "a properly constructed reduce operation is
> inherently parallelizable, so long as the function(s) used to process the
> elements are *associative* and *stateless*," and that a `collect()` producing
> a `Map` "may actually be counterproductive to perform in parallel" because
> merging maps by key is expensive. Sources that split well are arrays,
> `ArrayList`, `HashMap`, `HashSet`, `ConcurrentHashMap`, and
> `IntStream.range`. Sources that do not are `Stream.iterate`, `LinkedList`,
> and anything followed by `limit`. Adding `.parallel()` also silently
> enlists the common ForkJoinPool, which is shared process-wide.

```java
// bad — Stream.iterate cannot split, and limit forces sequential-like work;
// this is slower than the sequential version and may not terminate usefully
long primes =
    Stream.iterate(BigInteger.TWO, BigInteger::nextProbablePrime)
        .parallel()
        .limit(50)
        .filter(n -> n.isProbablePrime(50))
        .count();

// good — a splittable range, a stateless mapper, an associative reduction
long total =
    IntStream.range(0, tiles.length).parallel().mapToLong(i -> weigh(tiles[i])).sum();
```

## 18.20 Use `takeWhile` and `dropWhile` for prefix conditions on an ordered stream, not `filter`.

> Why? `filter` evaluates the predicate against every element;
> [`takeWhile`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html)
> (Java 9+) short-circuits at the first element that fails it, which is the
> difference between reading one log line and reading the whole file. They are
> also semantically different: `filter` keeps every matching element anywhere
> in the sequence, `takeWhile` keeps the longest matching prefix. Using one
> where you meant the other is a correctness bug, not a performance one.

```java
// bad — reads every event in the file to collect a bounded prefix
List<Event> recent =
    eventsNewestFirst.stream().filter(event -> event.at().isAfter(cutoff)).toList();

// good — stops at the first event older than the cutoff
List<Event> recent =
    eventsNewestFirst.stream().takeWhile(event -> event.at().isAfter(cutoff)).toList();
```

## 18.21 Use the three-argument `Stream.iterate` when the stop condition is a predicate.

> Why? `Stream.iterate(seed, hasNext, next)` (Java 9+) expresses the classic
> `for (T t = seed; hasNext.test(t); t = next.apply(t))` loop directly. The
> two-argument form plus `limit` only works when you can compute the *count*
> in advance, so expressing a value-based stop condition with it forces you to
> either over-generate or hand-roll the arithmetic.

```java
// bad — the caller has to derive the iteration count by hand
Stream<LocalDate> days =
    Stream.iterate(start, day -> day.plusDays(1))
        .limit(ChronoUnit.DAYS.between(start, end));

// good — the stop condition is the stop condition
Stream<LocalDate> days = Stream.iterate(start, day -> day.isBefore(end), day -> day.plusDays(1));
```

## 18.22 Use `Stream.ofNullable` instead of a null check that produces `Stream.empty()`.

> Why? `Stream.ofNullable(T)` (Java 9+) returns a stream of zero or one
> element, which is exactly what a nullable lookup inside a `flatMap` needs.
> The hand-written ternary says the same thing in more characters and gives
> the reader a null to reason about.

```java
// bad — a null to reason about, and two lookups per key
Stream<Config> configs =
    keys.stream()
        .flatMap(
            key ->
                registry.get(key) == null ? Stream.empty() : Stream.of(registry.get(key)));

// good
Stream<Config> configs = keys.stream().flatMap(key -> Stream.ofNullable(registry.get(key)));
```

## 18.23 Use `mapMulti` when the mapper yields zero or a few elements and per-element stream allocation dominates.

> Why?
> [`mapMulti`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html)
> (Java 16+) has the signature
> `<R> Stream<R> mapMulti(BiConsumer<? super T, ? super Consumer<R>> mapper)` —
> the mapper pushes results into a consumer instead of returning a `Stream`,
> so a one-to-few expansion does not allocate a `Stream` object per input
> element. Prefer `flatMap` when the mapper naturally has a stream in hand;
> prefer `mapMulti` when you would be calling `Stream.of` or `Stream.empty()`
> to satisfy the signature. `mapMultiToInt`, `mapMultiToLong`, and
> `mapMultiToDouble` cover the primitive cases. The Javadoc warns that with an
> implicitly typed lambda "additional type information may be necessary for
> proper inference of the element type `<R>`" — a target type supplies it, as
> below; without one, write `.<R>mapMulti(...)`.

```java
// bad — allocates a Stream per element to emit zero or one result
Stream<Number> numbers =
    values.stream()
        .flatMap(value -> value instanceof Number n ? Stream.of(n) : Stream.empty());

// good — no intermediate Stream per element
Stream<Number> numbers =
    values.stream()
        .mapMulti(
            (value, downstream) -> {
              if (value instanceof Number n) {
                downstream.accept(n);
              }
            });
```

## 18.24 Never give a custom `Collector` mutable state of its own.

> Why? A `Collector`'s state lives in the accumulator object its `supplier`
> creates, one per thread under parallelism. Fields on the collector itself
> are shared across every accumulation, so a parallel run corrupts them and a
> second sequential run sees leftovers from the first. Error Prone:
> "`Collector.of()` should not use state." **Violation — enforced by Error
> Prone `CollectorShouldNotUseState`.**

```java
// bad — `total` is shared by every accumulation of this collector
BigDecimal[] total = {BigDecimal.ZERO};
Collector<Order, ?, BigDecimal> summing =
    Collector.of(
        () -> total,
        (acc, order) -> acc[0] = acc[0].add(order.amount()),
        (a, b) -> a,
        acc -> acc[0]);

// good — every accumulation gets its own state from the supplier
Collector<Order, ?, BigDecimal> summing =
    Collector.of(
        () -> new BigDecimal[] {BigDecimal.ZERO},
        (acc, order) -> acc[0] = acc[0].add(order.amount()),
        (a, b) -> new BigDecimal[] {a[0].add(b[0])},
        acc -> acc[0]);
```

## 18.25 Do not stream over `String.chars()` without converting back — it is an `IntStream`.

> Why? Effective Java, Item 45 uses this as the canonical stream-misuse trap:
> `"Hello world!".chars().forEach(System.out::print)` prints
> `72101108108111...` because `chars()` returns "a stream of `int`
> zero-extending the `char` values from this sequence" and `print(int)` wins
> overload resolution. The fix is to make the conversion explicit with
> `mapToObj`, or — per Item 45's own conclusion — to avoid streaming over
> `char` values at all. Note that `chars()` is *not* a stream of code points:
> surrogates are "passed through uninterpreted," so a cast back to `char`
> mangles anything outside the BMP. `codePoints()` is the method that combines
> surrogate pairs.

```java
// bad — prints the numeric code points
"Hello".chars().forEach(System.out::print);

// good — explicit conversion back to characters (BMP only)
"Hello".chars().mapToObj(c -> String.valueOf((char) c)).forEach(System.out::print);

// better — no stream at all
for (char c : "Hello".toCharArray()) {
  System.out.print(c);
}
```
