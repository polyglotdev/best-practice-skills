<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 22. Methods & Parameters

A method signature is the smallest unit of API design, and it is the one
that is hardest to change once it ships. This chapter is about the decisions
that go into a signature — what the parameters are, what types they have,
how many of them there are, what the method does with them before it starts
working, and what it hands back.

It covers parameter validation and where each kind belongs, defensive
copying and the ordering rule that makes it actually safe, naming, parameter
count and the three ways to fix a long list, interface parameters, boolean
parameters, overloading, varargs, and return-value discipline. It draws on
**Effective Java, 3rd ed.**, Items 49 ("Check parameters for validity"), 50
("Make defensive copies when needed"), 51 ("Design method signatures
carefully"), 52 ("Use overloading judiciously"), 53 ("Use varargs
judiciously"), 54 ("Return empty collections or arrays, not nulls"), 55
("Return optionals judiciously"), and 56 ("Write doc comments for all
exposed API elements"), together with the Google Java Style Guide's rules on
[method names](https://google.github.io/styleguide/javaguide.html#s5.2.3-method-names)
and
[Javadoc block tags](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags).

Two topics are deliberately deferred. The `Optional` return type gets one
cross-referencing rule here and its full treatment in
[Chapter 19](19-optional.md). Exception *design* — checked versus unchecked,
which standard exception to reuse, how to attach failure-capture data — is
[Chapter 24](24-exceptions.md); this chapter only covers documenting and
throwing them at a method's boundary. Javadoc form and the summary-fragment
rule are [Chapter 4](04-javadoc.md).

**Tool alignment:** Checkstyle enforces `MethodName` (default pattern
`^[a-z][a-zA-Z0-9]*$`, i.e. lowerCamelCase), `ParameterNumber` (a
parameter-count ceiling whose `max` property defaults to 7), and
`ParameterAssignment` (no reassigning a parameter). Checkstyle's
`JavadocMethod` can also cross-check `@throws` tags against declared
exceptions, but only when its `validateThrows` property is turned on — it is
`false` by default, so nothing here treats it as a baseline. Rules those
checks cover are marked **Violation**; everything else is a **Suggestion**.

## 22.1 Validate a public method's parameters at the top of the method, before it changes any state.

> Why? Effective Java, 3rd ed., Item 49: "Most methods and constructors have
> some restrictions on what values may be passed into them… You should
> clearly document all such restrictions and enforce them with checks at the
> beginning of the method body." Validating late means a method can fail
> partway through with the object left in an inconsistent state — the
> failure-atomicity violation that turns a rejected request into corrupt
> data.

```java
// bad — the balance is already debited when the amount check fires
public void transfer(Account target, BigDecimal amount) {
  this.balance = this.balance.subtract(amount);
  if (amount.signum() <= 0) {
    throw new IllegalArgumentException("amount must be positive");
  }
  target.credit(amount);
}

// good — nothing has changed when validation rejects the call
public void transfer(Account target, BigDecimal amount) {
  Objects.requireNonNull(target, "target");
  if (amount.signum() <= 0) {
    throw new IllegalArgumentException("amount must be positive: " + amount);
  }
  this.balance = this.balance.subtract(amount);
  target.credit(amount);
}
```

## 22.2 Null-check public parameters with `Objects.requireNonNull`, and always pass the message argument.

> Why? `Objects.requireNonNull(obj, String)` throws
> `NullPointerException` with a message naming the offending parameter,
> which turns a stack trace that says nothing into one that says exactly
> which argument was null. Without the message you are relying on the JVM's
> helpful-NullPointerException output, which is only enabled by default from
> JDK 15 and only helps when the dereference happens in the same frame — not
> when the null was stored and dereferenced an hour later (see 22.5).

```java
// bad — throws somewhere downstream with no indication of which input was null
public Receipt charge(Card card, Money amount) {
  return gateway.submit(card.token(), amount.cents());
}

// bad — a message-less check names nothing
public Receipt charge(Card card, Money amount) {
  Objects.requireNonNull(card);
  return gateway.submit(card.token(), amount.cents());
}

// good
public Receipt charge(Card card, Money amount) {
  Objects.requireNonNull(card, "card");
  Objects.requireNonNull(amount, "amount");
  return gateway.submit(card.token(), amount.cents());
}
```

## 22.3 Use an `assert` for the preconditions of a private or package-private method, not a thrown exception.

> Why? Effective Java, 3rd ed., Item 49: "For an unexported method, you, as
> the package author, control the circumstances under which the method is
> called, so you can and should ensure that only valid parameter values are
> ever passed in… you can use assertions." A private method's caller is your
> own code, so a violated precondition is a bug in your package, not bad
> input. Assertions cost nothing in production (they are disabled unless the
> JVM runs with `-ea`) and they document the invariant in place.

```java
// bad — a public-API-style check on a private helper, paid for on every call
private static long midpoint(long low, long high) {
  if (low > high) {
    throw new IllegalArgumentException("low > high");
  }
  return low + (high - low) / 2;
}

// good — the invariant is documented and checked in tests, free in production
private static long midpoint(long low, long high) {
  assert low <= high : "low=" + low + " high=" + high;
  return low + (high - low) / 2;
}
```

## 22.4 Document every unchecked exception a method can throw with `@throws`, and do not list it in the `throws` clause.

> Why? Effective Java, 3rd ed., Item 74: "Use the Javadoc `@throws` tag to
> document each exception that a method can throw, but do not use the
> `throws` keyword on unchecked exceptions." A `throws` clause listing a
> runtime exception blurs the compiler-enforced contract (checked
> exceptions) with the documented one, so callers can no longer tell which
> failures they must handle. Google Java Style Guide
> [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> adds that these tags "never appear with an empty description."
> **Suggestion** — no check verifies either half of this rule out of the box.
> `checkstyle/JavadocMethod` will cross-check `@throws` against the declared
> exceptions once `validateThrows` is enabled (it defaults to `false`), but it
> does not police unchecked exceptions in the `throws` clause or empty tag
> descriptions.

```java
// bad — an empty description, and an unchecked exception in the throws clause
/**
 * Charges the card.
 *
 * @throws IllegalArgumentException
 */
public Receipt charge(Card card, Money amount) throws IllegalArgumentException {
  return null;
}

// good
/**
 * Charges {@code amount} to {@code card} and returns the settled receipt.
 *
 * @param card the card to charge; must not be null
 * @param amount the amount to charge; must be positive
 * @return the settled receipt
 * @throws IllegalArgumentException if {@code amount} is zero or negative
 * @throws NullPointerException if {@code card} or {@code amount} is null
 * @throws GatewayException if the payment gateway rejects the charge
 */
public Receipt charge(Card card, Money amount) throws GatewayException {
  return gateway.submit(card.token(), amount.cents());
}
```

## 22.5 Validate a parameter that is stored for later use, even when the method itself never touches it.

> Why? Effective Java, 3rd ed., Item 49 calls this out specifically: a
> constructor or setter that stashes a bad value produces a failure "far
> removed in time and space" from the call that caused it. The
> `NullPointerException` surfaces from a getter three requests later, and
> the stack trace points at the innocent reader rather than the guilty
> writer.

```java
// bad — the null is accepted here and explodes in some later request
public final class Subscription {
  private final Plan plan;

  public Subscription(Plan plan) {
    this.plan = plan;
  }

  public BigDecimal monthlyCost() {
    return plan.price();  // NullPointerException, far from the real bug
  }
}

// good — the bad argument is rejected at the point it was supplied
public final class Subscription {
  private final Plan plan;

  public Subscription(Plan plan) {
    this.plan = Objects.requireNonNull(plan, "plan");
  }
}
```

## 22.6 Make a defensive copy of every mutable parameter you retain.

> Why? Effective Java, 3rd ed., Item 50: "You must program defensively, with
> the assumption that clients of your class will do their best to destroy
> its invariants." Storing the caller's `List`, array, or mutable object
> gives them a permanent handle on your internal state, so a class you
> declared `final` with all-`final` fields is still mutable from outside.
> See [Chapter 20, §20.9](20-collections.md) for the collection-specific
> form.

```java
// bad — the caller can mutate the array after construction
public final class Batch {
  private final Order[] orders;

  public Batch(Order[] orders) {
    this.orders = orders;
  }
}

Order[] mine = {orderA, orderB};
Batch batch = new Batch(mine);
mine[0] = forgedOrder;  // batch's contents just changed

// good
public final class Batch {
  private final List<Order> orders;

  public Batch(Order[] orders) {
    this.orders = List.of(orders);  // copies, and rejects nulls
  }
}
```

## 22.7 Copy first, then validate the copy — never validate the caller's object and then copy it.

> Why? Effective Java, 3rd ed., Item 50: "the copy is made *before* checking
> the validity of the parameters, and the validity check is performed on the
> copy rather than on the original." Otherwise there is a window between the
> check and the copy in which another thread can change the object — a
> time-of-check/time-of-use (TOCTOU) attack that lets an invalid value past
> a validation you wrote correctly. This is the ordering rule; getting it
> backwards makes the defensive copy decorative.

```java
// bad — another thread can mutate `range` between the check and the copy
public Reservation(DateRange range) {
  if (range.start().isAfter(range.end())) {
    throw new IllegalArgumentException("start after end");
  }
  this.range = new DateRange(range.start(), range.end());
}

// good — copy, then validate what you actually kept
public Reservation(DateRange range) {
  this.range = new DateRange(range.start(), range.end());
  if (this.range.start().isAfter(this.range.end())) {
    throw new IllegalArgumentException("start after end: " + this.range);
  }
}
```

## 22.8 Do not use `clone()` to defensively copy a parameter whose type can be subclassed.

> Why? Effective Java, 3rd ed., Item 50: "the `clone` method of a parameter
> whose type is subclassable by untrusted parties" must not be used, because
> `clone` is dispatched on the *runtime* type — a malicious subclass can
> return an object that keeps a reference to itself, defeating the copy
> entirely. A constructor or static factory of the declared type cannot be
> subverted that way. Arrays are the exception: `array.clone()` is safe,
> because an array's runtime type is fixed and its `clone` is not
> overridable.

```java
// bad — a hostile Date subclass's clone() can return an object it still owns
public Period(Date start, Date end) {
  this.start = (Date) start.clone();
  this.end = (Date) end.clone();
}

// good — the constructor of the declared type cannot be overridden
public Period(Date start, Date end) {
  this.start = new Date(start.getTime());
  this.end = new Date(end.getTime());
}

// best — an immutable type needs no copy at all (see chapter 28)
public Period(Instant start, Instant end) {
  this.start = Objects.requireNonNull(start, "start");
  this.end = Objects.requireNonNull(end, "end");
}
```

## 22.9 Return a copy or an immutable snapshot of mutable internal state, never the field itself.

> Why? The mirror image of 22.6. An accessor that returns the live
> `ArrayList` field lets any caller call `clear()` on your object's guts.
> Effective Java, 3rd ed., Item 50 applies the same reasoning to return
> values as to parameters: "you should think twice before returning a
> reference to an internal component that is mutable." The cheapest fix is
> to make the field immutable in the first place, so the accessor can hand
> it out safely.

```java
// bad — the caller can empty the order
public List<Item> items() {
  return items;
}

// good — the field is already immutable, so sharing it is safe
private final List<Item> items;  // assigned via List.copyOf in the constructor

public List<Item> items() {
  return items;
}

// good — when the field must stay mutable, hand out a snapshot
public List<Item> items() {
  return List.copyOf(items);
}
```

## 22.10 Name a method for what a reader of the call site expects, following the conventions of the package and the platform.

> Why? Google Java Style Guide
> [§5.2.3](https://google.github.io/styleguide/javaguide.html#s5.2.3-method-names):
> "Method names are written in lowerCamelCase. Method names are typically
> verbs or verb phrases." Effective Java, 3rd ed., Item 51 adds the harder
> half: be consistent within the package and with the wider platform, so
> `size`/`isEmpty`/`get` mean here what they mean in `java.util`. A method
> named `getSize` in a package where everything else uses `size` costs every
> future reader a lookup. **Violation — the lowerCamelCase half is enforced by
> `checkstyle/MethodName`** (default pattern `^[a-z][a-zA-Z0-9]*$`, which
> rejects both `GetSize` and `fetch_order`); the consistency half is a
> judgement no check can make.

```java
// bad — inconsistent with the platform and with itself
public interface OrderBook {
  int GetSize();

  boolean empty();  // java.util spells this isEmpty

  Order fetch_order(OrderId id);
}

// good
public interface OrderBook {
  int size();

  boolean isEmpty();

  Order getOrder(OrderId id);
}
```

## 22.11 Do not provide a convenience method for every plausible combination of arguments.

> Why? Effective Java, 3rd ed., Item 51: "Don't go overboard in providing
> convenience methods. Every method should 'pull its weight.'" Each extra
> overload is another entry a reader has to scan, another signature you
> cannot change, and another candidate for the ambiguity traps in 22.16.
> "When in doubt, leave it out" — a caller can always compose two calls; you
> can never un-ship a method.

```java
// bad — six ways to say the same thing
public interface OrderFinder {
  List<Order> find(String customerId);

  List<Order> find(String customerId, Status status);

  List<Order> find(String customerId, Status status, int limit);

  List<Order> findRecent(String customerId);

  List<Order> findRecentByStatus(String customerId, Status status);

  List<Order> findRecentByStatusWithLimit(
      String customerId, Status status, int limit);
}

// good — one general method plus the single shortcut that earns its keep
public interface OrderFinder {
  List<Order> find(OrderQuery query);

  default List<Order> findByCustomer(String customerId) {
    return find(OrderQuery.forCustomer(customerId));
  }
}
```

## 22.12 Keep parameter lists to four or fewer.

> Why? Effective Java, 3rd ed., Item 51: "Long parameter lists should be
> avoided. Aim for four parameters or fewer." Past that, callers stop being
> able to read a call site without opening the declaration, and a run of
> same-typed parameters means transposed arguments compile cleanly and fail
> at runtime — `move(x, y, width, height)` called as
> `move(width, height, x, y)` is a silent bug.
> **Violation — enforced by `checkstyle/ParameterNumber`**, but only once you
> configure it: its `max` property defaults to 7, so the seven-parameter
> method below passes a stock configuration. Set `max` to 4 to enforce the
> limit this rule states.

```java
// bad — seven parameters, four of them String; transpose any two and it
// still compiles
public Shipment create(
    String orderId,
    String carrier,
    String trackingNumber,
    String destinationCountry,
    int weightGrams,
    boolean expedited,
    boolean signatureRequired) {
  return null;
}

// good — see 22.13 for the three ways to get here
public Shipment create(ShipmentRequest request) {
  return null;
}
```

## 22.13 Fix a long parameter list by splitting the method, by introducing a parameter object, or by using a builder.

> Why? Effective Java, 3rd ed., Item 51 gives exactly three techniques, and
> they are not interchangeable. *Split* when the parameters describe
> independent operations that were fused together. *Parameter object* — in
> Java 21, a `record` — when a group of parameters always travels together
> and has a name. *Builder* (Item 2) when there are many optional
> parameters, so callers name each one at the call site. Reaching for a
> builder where a record would do adds ceremony; reaching for a record where
> the group has no meaning just relocates the problem.

```java
// bad — the parameters describe two unrelated concerns
public interface OrderArchive {
  List<Order> findAndArchive(
      String customerId, Status status, Instant before, Path archiveDir);
}

// good (split) — two operations, each with a short list
public interface OrderArchive {
  List<Order> find(String customerId, Status status, Instant before);

  void archive(List<Order> orders, Path archiveDir);
}

// good (parameter object) — the group has a name and travels together
public record Dimensions(int width, int height, int depth) {}

public interface Resizer {
  Box resize(Dimensions dimensions);
}

// good (builder) — many optional parameters, named at the call site
Shipment shipment =
    Shipment.builder()
        .orderId(orderId)
        .carrier(Carrier.UPS)
        .expedited(true)
        .build();
```

## 22.14 Declare a parameter with the most general interface that supports the operations the method performs.

> Why? Effective Java, 3rd ed., Item 51: "Favor interfaces over classes for
> parameter types." Declaring `ArrayList<Order>` instead of
> `List<Order>`, or `HashMap` instead of `Map`, forces every caller to
> convert — including callers whose data is already in an equally valid
> form. If the method only iterates, `Collection` or even `Iterable` is
> more general still. See [Chapter 20, §20.2](20-collections.md) and, for
> `? extends` / `? super` bounds on those interfaces,
> [Chapter 16](16-generics.md).

```java
// bad — a caller holding a LinkedList or a Set has to copy
public BigDecimal total(ArrayList<Order> orders) {
  return null;
}

// good
public BigDecimal total(Collection<Order> orders) {
  return null;
}

// good — a producer parameter that only needs to be read from
public void addAll(Collection<? extends Order> orders) { }
```

## 22.15 Prefer a two-element enum to a `boolean` parameter.

> Why? Effective Java, 3rd ed., Item 51: "Prefer two-element enum types to
> `boolean` parameters." `apply(true)` at the call site tells a reader
> nothing, and adding a third mode later means a source-incompatible
> signature change. An enum names both states, reads at the call site, and
> can grow. This is doubly true when the method already has another boolean
> — `create(order, true, false)` is unreadable and transposable.

```java
// bad — what do the booleans mean at the call site?
public interface ShipmentFactory {
  Shipment create(Order order, boolean expedited, boolean signature);
}

shipmentFactory.create(order, true, false);

// good
public enum Speed {
  STANDARD,
  EXPEDITED
}

public enum SignaturePolicy {
  NOT_REQUIRED,
  REQUIRED
}

public interface ShipmentFactory {
  Shipment create(Order order, Speed speed, SignaturePolicy signature);
}

shipmentFactory.create(order, Speed.EXPEDITED, SignaturePolicy.NOT_REQUIRED);
```

## 22.16 Never write two same-arity overloads when a single argument could match both — overload selection happens at compile time.

> Why? Effective Java, 3rd ed., Item 52: "selection among overloaded methods
> is static, while selection among overridden methods is dynamic." The
> compiler picks the overload from the argument's *declared* type; the
> runtime type is irrelevant. So a loop over `Collection<?>` calls the
> `Collection` overload for every element, even when the elements are
> `Set`s and `List`s — a behavior that surprises every reader, because
> overriding works the other way around.

```java
// bad — prints "unknown" three times, not "set", "list", "unknown"
static String classify(Set<?> s) {
  return "set";
}

static String classify(List<?> l) {
  return "list";
}

static String classify(Collection<?> c) {
  return "unknown";
}

Collection<?>[] all = {new HashSet<>(), new ArrayList<>(), new ArrayDeque<>()};
for (Collection<?> c : all) {
  System.out.println(classify(c));  // "unknown", "unknown", "unknown"
}

// good — one method, runtime dispatch made explicit with a pattern switch
static String classify(Collection<?> c) {
  return switch (c) {
    case Set<?> set -> "set of " + set.size();
    case List<?> list -> "list of " + list.size();
    default -> "unknown collection of " + c.size();
  };
}
```

## 22.17 When two methods of the same arity do genuinely different things, give them different names.

> Why? Effective Java, 3rd ed., Item 52: "a safe, conservative policy is
> never to export two overloadings with the same number of parameters." You
> are never *required* to overload — names are free. `ObjectOutputStream`
> is the standard example of the right shape: `writeBoolean(boolean)`,
> `writeInt(int)`, `writeLong(long)`. The classic counterexample is in
> `java.util.List` itself, where `remove(int)` and `remove(Object)` differ
> in meaning and pick different overloads for `Integer` versus `int`.

```java
// bad — remove(1) removes the element at index 1, not the value 1
List<Integer> ids = new ArrayList<>(List.of(10, 11, 12));
ids.remove(1);  // ids is now [10, 12] — removed index 1, not the value 1

// good — say which overload you mean
List<Integer> ids = new ArrayList<>(List.of(10, 11, 12));
ids.remove(Integer.valueOf(11));  // removes the value 11 -> [10, 12]
ids.remove(1);                    // removes index 1, deliberately -> [10]

// good — in your own API, distinct names for distinct behavior
public void writeInt(int value) { }

public void writeString(String value) { }
```

## 22.18 Do not overload a varargs method, and do not use varargs for a fixed arity.

> Why? Effective Java, 3rd ed., Item 53. A varargs method matches *any*
> number of trailing arguments, so any overload of it is ambiguous or
> shadowed in ways the compiler resolves by rules almost nobody remembers.
> And a varargs parameter on a method that always takes exactly two
> arguments loses all compile-time arity checking — the caller who passes
> one gets an `ArrayIndexOutOfBoundsException` at runtime instead of a
> compile error.

```java
// bad — no arity checking; average() compiles and then throws at runtime
static int average(int... values) {
  return (values[0] + values[1]) / 2;
}

average();  // compiles, then ArrayIndexOutOfBoundsException

// good — a fixed arity belongs in the signature
static int average(int first, int second) {
  return (first + second) / 2;
}
```

## 22.19 Put the mandatory first argument in the signature when a varargs method requires at least one.

> Why? Effective Java, 3rd ed., Item 53 gives this exact idiom for "min of a
> list of arguments": declare `min(int firstArg, int... remainingArgs)` so
> that "a zero-argument call won't even compile." The alternative — a plain
> `int...` with a length check in the body — moves an error the compiler
> could have caught into production, and forces you to invent an exception
> for it.

```java
// bad — the arity error is a runtime exception, not a compile error
static int min(int... args) {
  if (args.length == 0) {
    throw new IllegalArgumentException("at least one argument required");
  }
  int min = args[0];
  for (int i = 1; i < args.length; i++) {
    min = Math.min(min, args[i]);
  }
  return min;
}

// good — min() does not compile
static int min(int first, int... rest) {
  int min = first;
  for (int value : rest) {
    min = Math.min(min, value);
  }
  return min;
}
```

## 22.20 Add fixed-arity overloads in front of a varargs method only when profiling proves the array allocation matters.

> Why? Every varargs call allocates an array. Effective Java, 3rd ed., Item
> 53 describes the mitigation used by `EnumSet.of`: declare overloads for
> the common small arities and let varargs catch the rest, so you pay for the
> array only in the small minority of calls whose argument count exceeds the
> overload set. This is a real technique in
> library code on a hot path, and premature clutter anywhere else — it
> directly contradicts 22.11 and 22.18, so it needs evidence.

```java
// bad — a five-deep overload set added "for speed" on a method called twice
// per request, where the array allocation is unmeasurable
public static Report of(Metric m1) {
  return of(new Metric[] {m1});
}

public static Report of(Metric m1, Metric m2) {
  return of(new Metric[] {m1, m2});
}

// ... three more, none of which any profile asked for ...

// good — the shape EnumSet.of uses (bodies sketched, not the JDK source):
// fixed-arity overloads for the common cases, varargs only as the fallback,
// adopted only after measurement
public static <E extends Enum<E>> EnumSet<E> of(E e) {
  EnumSet<E> result = EnumSet.noneOf(e.getDeclaringClass());
  result.add(e);
  return result;
}

public static <E extends Enum<E>> EnumSet<E> of(E e1, E e2) {
  EnumSet<E> result = EnumSet.noneOf(e1.getDeclaringClass());
  result.add(e1);
  result.add(e2);
  return result;
}

// ... e3, e4, e5 overloads ...

public static <E extends Enum<E>> EnumSet<E> of(E first, E... rest) {
  EnumSet<E> result = EnumSet.noneOf(first.getDeclaringClass());
  result.add(first);
  Collections.addAll(result, rest);
  return result;
}
```

## 22.21 Return an empty collection or array, never `null`.

> Why? Effective Java, 3rd ed., Item 54: "Never return `null` in place of an
> empty array or collection." The performance argument for `null` does not
> survive contact with `List.of()` and the shared zero-length array idiom,
> both of which allocate nothing. What `null` reliably buys you is a
> `NullPointerException` at the one call site that forgot the guard. The
> collection-specific version of this rule is
> [Chapter 20, §20.5](20-collections.md).

```java
// bad
public Order[] pending() {
  return pendingOrders.isEmpty() ? null : pendingOrders.toArray(new Order[0]);
}

// good — the shared empty array costs no allocation
private static final Order[] EMPTY_ORDER_ARRAY = new Order[0];

public Order[] pending() {
  return pendingOrders.toArray(EMPTY_ORDER_ARRAY);
}
```

## 22.22 Return `Optional<T>` only when absence is a normal outcome the caller must handle — never for a collection, and never to avoid a null check you should have made.

> Why? Effective Java, 3rd ed., Item 55: "Optionals are similar in spirit to
> checked exceptions… in that they force the user of an API to confront the
> fact that there may be no value returned." That force is the whole point,
> and it costs an allocation plus a level of indirection, so it is
> unjustified where absence is already expressible — an empty collection
> already says "nothing here," so `Optional<List<T>>` gives the caller two
> ways to spell empty. Full treatment in [Chapter 19](19-optional.md).

```java
// bad — two representations of "no orders", and one extra unwrap for nothing
public Optional<List<Order>> findOrders(String customerId) {
  return Optional.of(repository.query(customerId));
}

// good — an empty list is the absence
public List<Order> findOrders(String customerId) {
  return repository.query(customerId);
}

// good — a single result that legitimately may not exist
public Optional<Order> findOrder(OrderId id) {
  return repository.byId(id);
}
```

## 22.23 Do not reassign a parameter.

> Why? A parameter's name is the caller's argument, and reassigning it means
> the rest of the method body silently talks about something else — so a
> reader debugging line 40 has to scan back to line 12 to learn that
> `input` is no longer the input. It also destroys the value for a debugger
> and for any later exception message. Introduce a new local instead; the
> compiler will optimize it away. **Violation — enforced by
> `checkstyle/ParameterAssignment`.**

```java
// bad — by the time we throw, `path` no longer names what the caller passed
public Config load(String path) throws IOException {
  if (path == null) {
    path = DEFAULT_PATH;
  }
  path = path.strip();
  return parse(Files.readString(Path.of(path), StandardCharsets.UTF_8));
}

// good
public Config load(String path) throws IOException {
  String resolved = Objects.requireNonNullElse(path, DEFAULT_PATH).strip();
  return parse(Files.readString(Path.of(resolved), StandardCharsets.UTF_8));
}
```

## 22.24 Keep commands and queries separate — a method either changes state or answers a question, never both.

> Why? A method that mutates and returns makes every call site a potential
> side effect, so `if (queue.next() != null)` inside a condition silently
> consumes an element and reordering the condition changes behavior. The
> JDK's own violations of this rule are the ones people get wrong most
> often: `Iterator.next()` advances, `Map.put` returns the *previous* value,
> and `Queue.poll` removes. When you must combine them, say so in the name
> (`poll`, `take`, `pollFirstEntry`) so the call site reads as a mutation.

```java
// bad — a getter that mutates; calling it twice gives different answers
public int getNextId() {
  return ++lastId;
}

if (getNextId() > 0 && getNextId() < MAX) {  // consumed two ids
}

// good — the query is pure, the command is named as a command
public int currentId() {
  return lastId;
}

public int allocateId() {
  return ++lastId;
}
```
