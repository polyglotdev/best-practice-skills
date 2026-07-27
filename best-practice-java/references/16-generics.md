<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 16. Generics

Generics are a compile-time-only feature. The compiler checks your types and
then throws almost all of that information away — a process called *erasure*
([JLS 21 §4.6](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.6)).
Every rule in this chapter follows from that one fact: the guarantees you get
are the ones you arrange at compile time, because at run time there is no type
argument left to check.

This chapter draws on *Effective Java*, 3rd ed., Items 26–33, and on the JLS
sections defining
[raw types](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.8)
and erasure. Google's Java Style Guide is largely silent on generics beyond
[§5.2.8](https://google.github.io/styleguide/javaguide.html#s5.2.8-type-variable-names)
on type-variable naming, covered in [Chapter 3](03-naming.md); the design rules
here therefore cite *Effective Java* and the JLS.

Deliberately deferred: collection selection and the sequenced-collection
interfaces are [Chapter 20](20-collections.md); generic functional interfaces
and the variance of `Function`/`Consumer`/`Supplier` are
[Chapter 17](17-lambdas-and-method-references.md); `Optional<T>` discipline is
[Chapter 19](19-optional.md); sealed generic hierarchies are
[Chapter 13](13-sealed-types.md).

**Tool alignment:** the load-bearing enforcement here is `javac` itself. Build
with `-Xlint:all -Werror` so the `rawtypes`, `unchecked`, and `varargs` lint
categories fail the build rather than scroll past. Error Prone adds
`TypeParameterUnusedInFormals`. Where a rule is enforced, it is marked
**Violation** rather than **Suggestion**.

## 16.1 Never use a raw type in new code.

> Why? *Effective Java*, 3rd ed., Item 26: "Don't use raw types." A raw type
> exists only "to facilitate interfacing with non-generic legacy code"
> ([JLS 21 §4.8](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.8)),
> and using one opts the whole expression out of generic type checking. The
> error does not surface where you made it — it surfaces as a
> `ClassCastException` at some unrelated read, possibly in another class,
> possibly months later. **Violation — enforced by `javac -Xlint:rawtypes
> -Werror`.**

```java
// bad — the compiler accepts the coin; the failure lands on whoever iterates
private final Collection stamps = new ArrayList();

stamps.add(new Coin());

for (Iterator i = stamps.iterator(); i.hasNext(); ) {
  Stamp stamp = (Stamp) i.next(); // ClassCastException, far from the real bug
}

// good — the error is reported at the offending add()
private final Collection<Stamp> stamps = new ArrayList<>();

stamps.add(new Coin()); // compile error: incompatible types
```

## 16.2 Know that `List`, `List<Object>`, and `List<?>` are three different types, and pick deliberately.

> Why? *Effective Java*, 3rd ed., Item 26 draws the distinction precisely. Raw
> `List` says "I have opted out of type checking" — it accepts anything and
> checks nothing. `List<Object>` says "this holds arbitrary objects" and *is*
> checked, but because generics are invariant you cannot pass a `List<String>`
> where a `List<Object>` is expected. `List<?>` says "a list of some unknown
> type" — fully type-safe, accepts any parameterization, and in exchange forbids
> adding anything but `null`. Choosing raw `List` because `List<?>` "wouldn't let
> me add" is choosing to disable the check that was telling you the code was
> unsound.

```java
// bad — raw type; the unsound add is silently accepted
static void addToAll(List list, Object element) {
  list.add(element); // corrupts a List<String> without complaint
}

// good — three distinct, deliberate signatures
static int countCommon(Set<?> a, Set<?> b) { // reads only; any parameterization
  return (int) a.stream().filter(b::contains).count();
}

static void addAnything(List<Object> sink, Object element) { // genuinely heterogeneous
  sink.add(element);
}

static void addName(List<String> sink, String element) { // homogeneous and specific
  sink.add(element);
}
```

## 16.3 Use a raw type only where the language forces you to: class literals and `instanceof`.

> Why? *Effective Java*, 3rd ed., Item 26 lists the two exceptions. Class
> literals must be raw — `List.class` is legal, `List<String>.class` is a
> compile error, because there is only one `Class` object per erasure. And
> because erasure removes the type argument, `instanceof` cannot test a
> parameterized type; the idiomatic form is an unbounded wildcard, which since
> Java 16 combines with a pattern variable so no cast is needed at all. See
> [Chapter 14](14-pattern-matching.md).

```java
// bad — neither of these compiles
Class<List<String>> type = List<String>.class;

if (o instanceof Set<String>) {
  // ...
}

// good
Class<?> type = List.class;

if (o instanceof Set<?> set) {
  // set is a Set<?>; reading is safe, adding is (correctly) refused
  System.out.println(set.size());
}
```

## 16.4 Eliminate every unchecked warning you can, and build with `-Xlint:all -Werror`.

> Why? *Effective Java*, 3rd ed., Item 27: "Eliminate unchecked warnings." Every
> unchecked warning is the compiler saying it cannot prove a cast is safe —
> which means the corresponding `ClassCastException` is possible at run time. The
> practical failure is cumulative: once a build emits fifty warnings nobody
> reads, the fifty-first, which is the real one, is invisible. Failing the build
> on warnings keeps the count at zero, which is the only count anyone maintains.

```java
// bad — warning: [unchecked] unchecked conversion; nobody looks
Set<Order> orders = new HashSet();

// bad — warning: [unchecked] unchecked cast out of an Object-typed store
private final Map<String, Object> cache = new HashMap<>();

List<String> names = (List<String>) cache.get(key);

// good — the diamond infers the type argument, no warning
Set<Order> orders = new HashSet<>();

// good — parameterize the store, and there is nothing left to cast
private final Map<String, List<String>> cache = new HashMap<>();

List<String> names = cache.get(key);
```

## 16.5 Scope `@SuppressWarnings("unchecked")` to the narrowest declaration possible, and prove the safety in a comment.

> Why? *Effective Java*, 3rd ed., Item 27: "Always use the `SuppressWarnings`
> annotation on the smallest scope possible," and "every time you use a
> `@SuppressWarnings("unchecked")` annotation, add a comment saying why it is
> safe." A suppression on a class or a long method also hides the *next*
> unchecked operation someone adds there — you have silenced a warning you never
> evaluated. Java permits the annotation on a local variable declaration, so
> introducing a one-line local usually shrinks the scope to exactly the cast in
> question. The comment is not decoration: if you cannot state the invariant that
> makes the cast safe, the cast is not safe.

```java
// bad — suppresses every present and future unchecked operation in the method,
// and offers no argument that any of them are sound
@SuppressWarnings("unchecked")
public <T> T[] toArray(T[] a) {
  if (a.length < size) {
    return (T[]) Arrays.copyOf(elements, size, a.getClass());
  }
  System.arraycopy(elements, 0, a, 0, size);
  return a;
}

// good — suppression covers one declaration, with the invariant stated
public <T> T[] toArray(T[] a) {
  if (a.length < size) {
    // Safe: the array we create has the same runtime type as the T[] the caller
    // passed in, so every element stored in it is assignable to T.
    @SuppressWarnings("unchecked")
    T[] result = (T[]) Arrays.copyOf(elements, size, a.getClass());
    return result;
  }
  System.arraycopy(elements, 0, a, 0, size);
  return a;
}
```

## 16.6 Prefer lists to arrays.

> Why? *Effective Java*, 3rd ed., Item 28: "Prefer lists to arrays." Arrays are
> *covariant* (`String[]` is a subtype of `Object[]`) and *reified* (they carry
> their element type at run time). Generics are *invariant* and erased. The
> combination means arrays defer type errors to run time while generics catch
> them at compile time, and it is why generic array creation (`new E[n]`,
> `new List<String>[10]`) is illegal: a reified array of an erased type could not
> enforce its own invariant.

```java
// bad — compiles cleanly, throws ArrayStoreException at run time
Object[] objects = new Long[1];
objects[0] = "I don't fit in here"; // ArrayStoreException

// good — the same mistake is a compile error
List<Object> objects = new ArrayList<Long>(); // compile error: incompatible types
```

## 16.7 Back a generic collection with `Object[]` and cast on read, not with a `(E[]) new Object[n]` field.

> Why? *Effective Java*, 3rd ed., Item 29 presents both options and notes the
> hazard of the first. Casting the array once in the constructor is tidier at the
> declaration, but the field is then *typed* `E[]` while its runtime type is
> `Object[]` — heap pollution. That is harmless while the array stays private and
> becomes a `ClassCastException` in the caller's frame the moment anything
> returns it. Declaring the store as `Object[]` keeps the type honest and moves
> the single unchecked cast to the read site, where the invariant justifying it is
> visible.

```java
// bad — the field lies about its runtime type; toArray corrupts the caller
public class Stack<E> {
  @SuppressWarnings("unchecked")
  private E[] elements = (E[]) new Object[16];

  public E[] toArray() {
    return elements; // String[] s = stack.toArray(); -> ClassCastException
  }
}

// good — honest field type, one narrowly scoped cast on read
public final class Stack<E> {
  private Object[] elements = new Object[16];
  private int size;

  public void push(E element) {
    if (size == elements.length) {
      elements = Arrays.copyOf(elements, 2 * size + 1);
    }
    elements[size++] = element;
  }

  public E pop() {
    if (size == 0) {
      throw new NoSuchElementException("stack is empty");
    }
    // Safe: push is the only writer, and it accepts only E.
    @SuppressWarnings("unchecked")
    E result = (E) elements[--size];
    elements[size] = null; // let the popped element be collected
    return result;
  }
}
```

## 16.8 Make the method generic instead of making callers cast.

> Why? *Effective Java*, 3rd ed., Item 30: "Favor generic methods." A method
> taking and returning raw or `Object`-typed values pushes an unchecked cast onto
> every call site — one warning per caller, and one place per caller for the cast
> to be wrong. Making the method generic moves the type relationship into the
> signature, where the compiler both checks it and infers it, so the call site
> needs neither a cast nor an explicit type argument.

```java
// bad — raw types, and every caller must cast the result
public static Set union(Set s1, Set s2) {
  Set result = new HashSet(s1);
  result.addAll(s2);
  return result;
}

// good — the relationship between inputs and output is in the signature
public static <E> Set<E> union(Set<? extends E> s1, Set<? extends E> s2) {
  Set<E> result = new HashSet<>(s1);
  result.addAll(s2);
  return result;
}

// Set<String> merged = union(admins, editors);  // no cast, no type argument
```

## 16.9 Use a recursive type bound when a type must be comparable to itself.

> Why? *Effective Java*, 3rd ed., Item 30 covers this under "recursive type
> bounds." `<E extends Comparable<E>>` is the naive form and is too strict: a
> type may legitimately implement `Comparable` against a *supertype* of itself —
> `class ScheduledTask extends Task implements Comparable<Task>` — and the naive
> bound rejects it. `<E extends Comparable<? super E>>` accepts both cases, and
> is the bound the JDK itself uses for methods like `Collections.max`.

```java
// bad — no bound, so the method casts and can fail at run time
public static Object max(Collection<?> values) {
  Object result = null;
  for (Object candidate : values) {
    if (result == null || ((Comparable<Object>) candidate).compareTo(result) > 0) { // unchecked
      result = candidate;
    }
  }
  return result;
}

// good — recursive bound plus a producer wildcard on the input
public static <E extends Comparable<? super E>> E max(Collection<? extends E> values) {
  Iterator<? extends E> it = values.iterator();
  if (!it.hasNext()) {
    throw new IllegalArgumentException("empty collection");
  }
  E result = it.next();
  while (it.hasNext()) {
    E candidate = it.next();
    if (candidate.compareTo(result) > 0) {
      result = candidate;
    }
  }
  return result;
}
```

## 16.10 Apply PECS to every input parameter: `? extends E` for producers, `? super E` for consumers.

> Why? *Effective Java*, 3rd ed., Item 31: "Use bounded wildcards to increase API
> flexibility," with the mnemonic **PECS — producer-`extends`,
> consumer-`super`**. Because generics are invariant, a parameter declared
> `Iterable<E>` rejects a `List<Integer>` when `E` is `Number`, even though every
> `Integer` *is* a `Number`. That rejection protects nobody: the method only
> reads. A wildcard states which direction data flows and restores the subtyping
> the caller expected. `Comparator<T>` and `Comparable<T>` are always consumers,
> so they are almost always written `? super T`.

```java
// bad — Stack<Number>.pushAll(List<Integer>) does not compile
public void pushAll(Iterable<E> src) {
  for (E element : src) {
    push(element);
  }
}

public void popAll(Collection<E> dst) {
  while (!isEmpty()) {
    dst.add(pop());
  }
}

// good — src produces E, dst consumes E
public void pushAll(Iterable<? extends E> src) {
  for (E element : src) {
    push(element);
  }
}

public void popAll(Collection<? super E> dst) {
  while (!isEmpty()) {
    dst.add(pop());
  }
}

// Stack<Number> stack = new Stack<>();
// stack.pushAll(List.of(1, 2, 3));        // List<Integer> — now legal
// stack.popAll(new ArrayList<Object>());  // Collection<Object> — now legal
```

## 16.11 Never let a wildcard type appear in a return type.

> Why? *Effective Java*, 3rd ed., Item 31 is explicit that bounded wildcard types
> should not be used as return types: rather than giving callers extra
> flexibility, "it would force them to use wildcard types in client code." A
> wildcard in a return type is contagious — every local, field, and parameter
> touching the result inherits it, and the caller loses the ability to add to the
> returned collection for no benefit. If a user of your API has to think about a
> wildcard, the API is wrong.

```java
// bad — every caller now writes List<? extends Shape> too, and none of them
// can add to it
public List<? extends Shape> visibleShapes() {
  return shapes;
}

// good — wildcards belong on the way in, not on the way out
public List<Shape> visibleShapes() {
  return List.copyOf(shapes);
}
```

## 16.12 If a type parameter appears only once in a method signature, replace it with a wildcard.

> Why? *Effective Java*, 3rd ed., Item 31: "If a type parameter appears only once
> in a method declaration, replace it with a wildcard." A type parameter exists to
> express a *relationship* between two positions; one occurrence relates nothing,
> so it is noise in the published signature. When the body genuinely needs a named
> type — because it both reads and writes the same list — keep the wildcard on the
> public signature and delegate to a private helper that captures it.

```java
// bad — E appears once, so it tells the reader nothing
public static <E> void swap(List<E> list, int i, int j) {
  list.set(i, list.set(j, list.get(i)));
}

// good — simple public signature, private capture helper does the work
public static void swap(List<?> list, int i, int j) {
  swapCaptured(list, i, j);
}

private static <E> void swapCaptured(List<E> list, int i, int j) {
  list.set(i, list.set(j, list.get(i)));
}
```

## 16.13 Treat a generic varargs parameter as unsafe unless the method neither stores into the array nor lets it escape.

> Why? *Effective Java*, 3rd ed., Item 32: "Combine generics and varargs
> judiciously." A varargs parameter is an array, so a generic varargs parameter is
> a generic array — the very thing 16.6 says the language forbids you to create.
> The compiler creates it anyway, which produces *heap pollution*: a variable of
> type `List<String>[]` referring to an array holding a `List<Integer>`. The
> resulting `ClassCastException` is thrown at a line containing no visible cast,
> which makes it exceptionally hard to diagnose. The two conditions are: nothing
> is ever stored into the varargs array, and no reference to it ever escapes the
> method. **Violation — enforced by `javac -Xlint:varargs -Werror`.**

```java
// bad — stores into the array, polluting the heap
static void dangerous(List<String>... stringLists) {
  Object[] objects = stringLists;
  objects[0] = List.of(42); // legal, because arrays are covariant
  String s = stringLists[0].get(0); // ClassCastException — with no cast in sight
}

// good — reads only, and the array never leaves the method, so the safety
// assertion of @SafeVarargs (16.14) is honest and the varargs warning goes away
@SafeVarargs
static <T> List<T> flatten(List<? extends T>... lists) {
  List<T> result = new ArrayList<>();
  for (List<? extends T> list : lists) {
    result.addAll(list);
  }
  return result;
}
```

## 16.14 Mark a provably safe generic varargs method `@SafeVarargs`, and know it is legal only on `static`, `final`, or `private` methods and on constructors.

> Why?
> [`@SafeVarargs`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/SafeVarargs.html)
> is your assertion that the method satisfies 16.13, and it suppresses the warning
> at *every call site* rather than at the declaration — which is the point, since
> callers cannot inspect the body to judge safety themselves. The legality
> restriction is not arbitrary: it is "a compile-time error if… the declaration is
> a variable arity method that is neither `static` nor `final` nor `private`,"
> because a subclass could otherwise break a safety guarantee you already
> certified. Never substitute `@SuppressWarnings("varargs")` — that hides the
> warning at the declaration and leaves every caller warning.

```java
// bad — compile error: @SafeVarargs is not allowed on a non-final instance
// method, because a subclass could override it unsafely
public class Merger<T> {
  @SafeVarargs
  public List<T> merge(List<? extends T>... lists) {
    return flatten(lists);
  }
}

// good — final makes the certification un-overridable and the annotation legal
public class Merger<T> {
  @SafeVarargs
  public final List<T> merge(List<? extends T>... lists) {
    List<T> result = new ArrayList<>();
    for (List<? extends T> list : lists) {
      result.addAll(list);
    }
    return result;
  }
}
```

## 16.15 Prefer a `List<T>` parameter to a generic varargs parameter when you cannot prove safety.

> Why? *Effective Java*, 3rd ed., Item 32 recommends replacing the varargs
> parameter with a `List` when the method must store or return the array. The
> canonical trap is a method that returns its own varargs array: it cannot be
> `@SafeVarargs`, and the array it hands back has runtime type `Object[]`, so the
> caller's implicit cast to `T[]` fails. `List.of` makes the call site almost as
> convenient and completely safe, at the cost of one allocation.

```java
// bad — toArray leaks its varargs array, so pickTwo returns an Object[]
// dressed as a T[]
static <T> T[] toArray(T... args) {
  return args;
}

static <T> T[] pickTwo(T a, T b, T c) {
  return switch (ThreadLocalRandom.current().nextInt(3)) {
    case 0 -> toArray(a, b);
    case 1 -> toArray(a, c);
    default -> toArray(b, c);
  };
}

// String[] attributes = pickTwo("Good", "Fast", "Cheap"); // ClassCastException

// good — a List carries its element type honestly
static <T> List<T> pickTwo(T a, T b, T c) {
  return switch (ThreadLocalRandom.current().nextInt(3)) {
    case 0 -> List.of(a, b);
    case 1 -> List.of(a, c);
    default -> List.of(b, c);
  };
}
```

## 16.16 Use a typesafe heterogeneous container when the key determines the value's type.

> Why? *Effective Java*, 3rd ed., Item 33: "Consider typesafe heterogeneous
> containers." A `Map<K, V>` fixes one value type for the whole map, which is
> wrong for registries, attribute bags, and dependency lookups where each key has
> its own type. Parameterizing the *key* instead of the container — with a
> `Class<T>` type token — gives unlimited type parameters with full safety. The
> cast is performed by
> [`Class.cast`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Class.html),
> which is checked at run time and throws `ClassCastException` at the point of
> error rather than propagating a corrupt value.

```java
// bad — Object values, so every caller casts and every cast can be wrong
public final class Attributes {
  private final Map<String, Object> values = new HashMap<>();

  public Object get(String name) {
    return values.get(name);
  }
}

// Integer retries = (Integer) attributes.get("retries"); // unchecked by the reader

// good — the key carries the type; get needs no cast at the call site
public final class Attributes {
  private final Map<Class<?>, Object> values = new HashMap<>();

  public <T> void put(Class<T> type, T value) {
    values.put(Objects.requireNonNull(type), Objects.requireNonNull(value));
  }

  public <T> T get(Class<T> type) {
    return type.cast(values.get(type));
  }
}

// attributes.put(Integer.class, 3);
// int retries = attributes.get(Integer.class); // no cast, no warning
```

## 16.17 Design around erasure: no `instanceof` on a parameterized type, no generic array creation, no type parameter in a static context.

> Why? Erasure
> ([JLS 21 §4.6](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.6))
> deletes type arguments during compilation, so at run time there is nothing left
> to test, allocate, or reference. These are not arbitrary restrictions and no
> flag lifts them — working around them with casts just moves the failure to run
> time. When you genuinely need the type at run time, pass a `Class<T>` token
> (16.16); when you need an array, use a `List` (16.6).

```java
// bad — none of these compile
class Box<T> {
  private static T defaultValue; // non-static type variable in a static context

  T[] newArray(int size) {
    return new T[size]; // generic array creation
  }

  boolean holdsStrings(Object o) {
    return o instanceof Box<String>; // illegal generic type for instanceof
  }
}

// good — a Class token supplies what erasure removed
final class Box<T> {
  private final Class<T> type;
  private final List<T> contents = new ArrayList<>();

  Box(Class<T> type) {
    this.type = Objects.requireNonNull(type);
  }

  boolean accepts(Object o) {
    return type.isInstance(o);
  }

  T[] toArray(IntFunction<T[]> arrayFactory) {
    return contents.toArray(arrayFactory);
  }
}
```

## 16.18 Never declare two methods whose erasures are identical.

> Why? Overload resolution happens after erasure, so `process(List<String>)` and
> `process(List<Integer>)` are the same method as far as the class file is
> concerned. The compiler rejects the class with a *name clash* error saying the
> two methods have the same erasure, and the fix is not a cast — it is a
> different name. That is a good
> outcome: two overloads differing only in a type argument were going to be
> ambiguous to human readers too. See
> [Chapter 22](22-methods-and-parameters.md) for overload design generally.

```java
// bad — compile error: name clash, both erase to process(List)
public void process(List<String> names) { /* ... */ }

public void process(List<Integer> ids) { /* ... */ }

// good — distinct names say what each one does anyway
public void processNames(List<String> names) { /* ... */ }

public void processIds(List<Integer> ids) { /* ... */ }
```

## 16.19 Do not declare a type parameter that appears only in the return type.

> Why? A type parameter used only in the return position is inferred entirely
> from the assignment context, which means the *caller* decides what it is and
> the method has no way to honor that decision. In practice the pattern is an
> unchecked cast wearing a friendly signature: it compiles at every call site and
> throws at the first real use. Take a `Class<T>` token instead, so the type is an
> argument the method can actually check. **Violation — enforced by Error Prone
> `TypeParameterUnusedInFormals`.**

```java
// bad — T is whatever the caller assigns to; the cast is unchecked
static <T> T fromJson(String json) {
  @SuppressWarnings("unchecked")
  T result = (T) parse(json);
  return result;
}

// String name = fromJson("{\"n\":1}"); // compiles; ClassCastException at run time

// good — the type is an argument, and it is verified
static <T> T fromJson(String json, Class<T> type) {
  return type.cast(parse(json));
}
```

## 16.20 Use the diamond operator, and never pair a bare diamond with `var`.

> Why? The diamond (`<>`) infers type arguments from the target type and has been
> legal on anonymous classes since Java 9, so there is no remaining reason to
> repeat on the right-hand side a type argument the left-hand side already
> spells out. But `var` and the diamond cancel each other out: with no declared
> target type, `new ArrayList<>()` infers
> `ArrayList<Object>`, so the collection silently accepts anything and every read
> yields `Object`. Pick one — name the type on the left and use the diamond, or
> use `var` and spell the type argument on the right.

```java
// bad — infers ArrayList<Object>; the "names" list happily accepts an Integer
var names = new ArrayList<>();
names.add(42); // compiles

// bad — redundant type argument
Map<String, List<Order>> byCustomer = new HashMap<String, List<Order>>();

// good — declared type on the left, diamond on the right
Map<String, List<Order>> byCustomer = new HashMap<>();

// good — var on the left, explicit type argument on the right
var names = new ArrayList<String>();

// good — the diamond works on anonymous classes too (Java 9+)
Comparator<String> byLength =
    new Comparator<>() {
      @Override
      public int compare(String a, String b) {
        return Integer.compare(a.length(), b.length());
      }
    };
```
