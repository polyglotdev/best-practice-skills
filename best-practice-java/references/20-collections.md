<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 20. Collections

The `java.util` collections framework is the part of the JDK every Java
program touches, and the part where the largest number of avoidable bugs
live: a `null` return that should have been an empty list, an
`unmodifiableList` view that the caller can still mutate through the
backing list, a `HashMap` key whose `hashCode` changed after insertion, a
`ConcurrentModificationException` from a `for`-each loop that removes.

This chapter covers choosing the right collection, returning and accepting
collections across API boundaries, immutability and defensive copying,
iteration and mutation, sorting, and the Java 21 sequenced-collection
interfaces. It draws on **Effective Java, 3rd ed.**, Items 54 (return empty
collections, not nulls), 50 (make defensive copies when needed), and 64
(refer to objects by their interfaces), together with the
[JDK 21 API documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/package-summary.html)
for the sequenced interfaces added by JEP 431.

Stream pipelines that *produce* collections are covered in
[Chapter 18](18-streams.md); this chapter is about the collections
themselves. `Optional` never belongs inside a collection — see
[Chapter 19](19-optional.md). The `equals`/`hashCode` contract that
`HashSet` and `HashMap` depend on is
[Chapter 10](10-equals-hashcode-tostring.md). Generic variance
(`List<? extends T>` vs `List<? super T>`) in collection signatures is
[Chapter 16](16-generics.md). Concurrent collections and the memory model
are [Chapter 26](26-concurrency-fundamentals.md).

**Tool alignment:** Checkstyle's `IllegalType` check flags concrete
collection types used in declarations — its default `illegalClassNames` is
exactly `HashMap`, `HashSet`, `LinkedHashMap`, `LinkedHashSet`, `TreeMap`,
`TreeSet` (plus their fully qualified forms), so any other implementation
type you want banned has to be added to that property. Checkstyle's
`EqualsHashCode` check flags a class that overrides one of
`equals`/`hashCode` without the other, which is the adjacent failure to the
hash-collection rules below. Where a rule is mechanically checked it is
marked **Violation**; everything else is a **Suggestion**.

## 20.1 Choose the collection interface from the operations the code actually performs, not from habit.

> Why? `List`, `Set`, `Map`, and `Deque` encode different contracts —
> positional access, uniqueness, key lookup, and end access respectively.
> Reaching for `ArrayList` reflexively and then calling `contains` in a loop
> turns an O(1) membership test into an O(n) scan, and reaching for `List`
> when the domain forbids duplicates pushes uniqueness enforcement into
> every call site.

```java
// bad — a list used as a membership set: contains() is a linear scan, and
// nothing prevents the same role being added twice
private final List<String> grantedRoles = new ArrayList<>();

boolean hasRole(String role) {
  return grantedRoles.contains(role);
}

// good — the contract (uniqueness + O(1) membership) is in the type
private final Set<String> grantedRoles = new HashSet<>();

boolean hasRole(String role) {
  return grantedRoles.contains(role);
}
```

## 20.2 Declare fields, parameters, return types, and locals with the interface type, never the implementation type.

> Why? Effective Java, 3rd ed., Item 64: "Refer to objects by their
> interfaces." Naming `ArrayList` in a signature freezes an implementation
> choice into your API — swapping to `LinkedList`, `CopyOnWriteArrayList`,
> or `List.of` later becomes a breaking change for every caller. The only
> legitimate exception is a local variable whose implementation-specific
> behavior you deliberately depend on (see 20.11 for `LinkedHashMap`).
> **Violation — enforced by `checkstyle/IllegalType`** for the types in its
> default `illegalClassNames` list (`HashMap`, `HashSet`, `LinkedHashMap`,
> `LinkedHashSet`, `TreeMap`, `TreeSet`) — so the `HashMap` parameter below
> is flagged out of the box, and catching `ArrayList` in a signature requires
> adding it to that property.

```java
// bad — the implementation leaks into the signature
public ArrayList<Order> findOrders(HashMap<String, String> filters) {
  ArrayList<Order> results = new ArrayList<>();
  return results;
}

// good — interfaces in the signature, implementation only at construction
public List<Order> findOrders(Map<String, String> filters) {
  List<Order> results = new ArrayList<>();
  return results;
}
```

## 20.3 Choose the concrete implementation from the ordering and complexity guarantees you need, and know what each one costs.

> Why? The implementations are not interchangeable. `HashMap` gives O(1)
> lookup with *no* order guarantee — including no stable order between JVM
> runs. `LinkedHashMap` adds insertion order. `TreeMap` adds sorted order at
> O(log n). Picking `HashSet` and then depending on its iteration order is
> the single most common source of tests that pass locally and fail in CI.
> The same applies to the end-access types: `ArrayDeque` is the default
> `Deque` and `Queue` implementation, and it supersedes both the legacy
> synchronized `Stack` and `LinkedList`, whose per-element node objects cost
> more than the contiguous array `ArrayDeque` uses.

```java
// bad — iteration order of a HashMap is unspecified; this "top 3" is
// whatever the hash buckets happen to produce
Map<String, Integer> scores = new HashMap<>();
List<String> topThree = scores.keySet().stream().limit(3).toList();

// good — say which order you mean
// insertion order:
Map<String, Integer> byArrival = new LinkedHashMap<>();
// key-sorted order:
NavigableMap<String, Integer> byName = new TreeMap<>();
// explicit ranking, independent of any map's iteration order:
List<String> topThree =
    scores.entrySet().stream()
        .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
        .limit(3)
        .map(Map.Entry::getKey)
        .toList();

// bad — Stack is a synchronized Vector subclass whose iteration order is
// bottom-to-top, the opposite of pop order; LinkedList allocates a node
// object per element
Deque<Frame> pending = new LinkedList<>();
Stack<Frame> legacy = new Stack<>();

// good
Deque<Frame> pending = new ArrayDeque<>();
```

## 20.4 Use `EnumSet` and `EnumMap` whenever the elements or keys are enum constants.

> Why? Effective Java, 3rd ed., Item 36 ("Use `EnumSet` instead of bit
> fields") and Item 37 ("Use `EnumMap` instead of ordinal indexing").
> `EnumSet` is a bit-vector internally, so it is smaller and faster than
> `HashSet` while still being a full `Set`; `EnumMap` is an array indexed by
> ordinal, with iteration in natural (declaration) order for free. Neither
> requires hashing at all.

```java
// bad — hashing enum constants, and iteration order is unspecified
Set<Permission> allowed = new HashSet<>();
allowed.add(Permission.READ);
Map<Status, Integer> counts = new HashMap<>();

// good — compact, fast, and iterates in declaration order
Set<Permission> allowed = EnumSet.of(Permission.READ, Permission.WRITE);
Map<Status, Integer> counts = new EnumMap<>(Status.class);
```

## 20.5 Return an empty collection, never `null`, from a method whose return type is a collection.

> Why? Effective Java, 3rd ed., Item 54: "Never return `null` in place of an
> empty array or collection." A `null` return forces every caller to write a
> guard, and the one caller that forgets gets a `NullPointerException` in
> production instead of a harmless zero-iteration loop. `List.of()` and
> `Collections.emptyList()` are both documented to return an immutable empty
> list, and on OpenJDK both hand back a shared instance rather than
> allocating — so there is no performance argument for `null`.

```java
// bad — every caller must guard, and one of them won't
public List<Order> findOrders(String customerId) {
  List<Order> found = repository.query(customerId);
  return found.isEmpty() ? null : found;
}

// good
public List<Order> findOrders(String customerId) {
  return repository.query(customerId);  // already empty when nothing matched
}

// good — when there is genuinely nothing to return
public List<Order> findOrders(String customerId) {
  if (!isKnownCustomer(customerId)) {
    return List.of();
  }
  return repository.query(customerId);
}
```

## 20.6 Build fixed constant collections with `List.of`, `Set.of`, and `Map.of`; use `Map.entry` with `Map.ofEntries` past ten pairs.

> Why? The `of` factories added in Java 9 produce genuinely immutable
> collections — no wrapper, no backing array the caller can reach — in one
> expression. `Map.of` has overloads only up to ten key/value pairs, so
> beyond that the compiler will not help you and `Map.ofEntries` with
> `Map.entry` is the intended form. See the
> [`Map` API docs](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Map.html#unmodifiable).

```java
// bad — mutable, verbose, and the static initializer can be forgotten
private static final Set<String> RETRYABLE_CODES = new HashSet<>();

static {
  RETRYABLE_CODES.add("429");
  RETRYABLE_CODES.add("503");
}

// good
private static final Set<String> RETRYABLE_CODES = Set.of("429", "503");

private static final Map<String, Integer> PRIORITY =
    Map.ofEntries(
        Map.entry("critical", 0),
        Map.entry("high", 1),
        Map.entry("normal", 2));
```

## 20.7 Do not use `List.of` / `Set.of` / `Map.of` where `null` is a legal element or value.

> Why? These factories are null-hostile by design: the
> [`List.of` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/List.html#unmodifiable)
> states they "disallow `null` elements. Attempts to create them with `null`
> elements result in `NullPointerException`." The trap is `Map.of`, whose
> resulting map also throws `NullPointerException` from `get(null)` and
> `containsKey(null)` — a silent behavior change if you swap it in for a
> `HashMap` that previously tolerated a null probe.

```java
// bad — throws NullPointerException at construction if middleName is null
List<String> nameParts = List.of(firstName, middleName, lastName);

// bad — throws NullPointerException, not returns false
Map<String, User> byId = Map.of("u1", alice);
if (byId.containsKey(possiblyNullId)) { }

// good — a null-tolerant collection when nulls are genuinely possible
List<String> nameParts = new ArrayList<>();
nameParts.add(firstName);
nameParts.add(middleName);  // may be null
nameParts.add(lastName);

// good — normalize before building, so the immutable form stays safe
List<String> nameParts =
    Stream.of(firstName, middleName, lastName).filter(Objects::nonNull).toList();
```

## 20.8 Use `List.copyOf` / `Set.copyOf` / `Map.copyOf` for an unmodifiable snapshot; `Collections.unmodifiableList` gives you a *view*, not a copy.

> Why? `Collections.unmodifiableList(source)` returns a wrapper that rejects
> mutation *through the wrapper* while still reflecting every change made to
> `source`. If `source` is a field you keep mutating, you have handed the
> caller a live window into your internal state that changes under them.
> `List.copyOf` takes a snapshot, so the result is genuinely fixed. Both are
> useful — the bug is reaching for the view when you meant the copy.

```java
// bad — the caller's "unmodifiable" list mutates under them
private final List<Item> items = new ArrayList<>();

public List<Item> items() {
  return Collections.unmodifiableList(items);
}

// good — a snapshot the caller can rely on
public List<Item> items() {
  return List.copyOf(items);
}

// also good — a view is correct when the caller is documented to want live
// read-only access and you never hand it across a trust boundary
/** Returns a live, read-only view of the current items. */
public List<Item> itemsView() {
  return Collections.unmodifiableList(items);
}
```

## 20.9 Copy every mutable collection that crosses an API boundary, in both directions.

> Why? Effective Java, 3rd ed., Item 50: "Make defensive copies when
> needed." A constructor that stores the caller's `List` directly hands the
> caller a permanent back door into the object's state, defeating any
> immutability you thought you had. The same applies to accessors that hand
> the internal list out. See [Chapter 22, §22.6](22-methods-and-parameters.md)
> for the general parameter-copying rule and the copy-then-validate
> ordering.

```java
// bad — the caller keeps a reference and can mutate the "immutable" order
public final class Order {
  private final List<Item> items;

  public Order(List<Item> items) {
    this.items = items;  // aliased, not copied
  }

  public List<Item> items() {
    return items;  // and handed straight back out
  }
}

// good
public final class Order {
  private final List<Item> items;

  public Order(List<Item> items) {
    this.items = List.copyOf(items);  // also rejects nulls, see 20.7
  }

  public List<Item> items() {
    return items;  // already immutable, safe to share
  }
}
```

## 20.10 Use the Java 21 sequenced-collection methods instead of index arithmetic and reversal idioms.

> Why? Java 21 finalized `SequencedCollection`, `SequencedSet`, and
> `SequencedMap` (JEP 431), retrofitting `List`, `Deque`, `SortedSet`, and
> `LinkedHashSet` with `getFirst()`, `getLast()`, `addFirst(E)`,
> `addLast(E)`, `removeFirst()`, `removeLast()`, and `reversed()`. The old
> idioms — `get(list.size() - 1)`, `new ArrayList<>(set).get(0)`,
> `Collections.reverse` on a defensive copy — are each an opportunity for an
> off-by-one or an unnecessary allocation. `reversed()` returns a *view*, so
> it does not copy.

```java
// bad — off-by-one waiting to happen, and an allocation just to read a head
Item last = items.get(items.size() - 1);
Item first = new ArrayList<>(orderedSet).get(0);
List<Item> backwards = new ArrayList<>(items);
Collections.reverse(backwards);

// good
Item last = items.getLast();
Item first = orderedSet.getFirst();
List<Item> backwards = items.reversed();  // a view, no copy
```

## 20.11 Reach for `SequencedMap` methods on a `LinkedHashMap` instead of iterating its entry set to find the ends.

> Why? `LinkedHashMap` implements `SequencedMap` in Java 21, so
> `firstEntry()`, `lastEntry()`, `pollFirstEntry()`, `pollLastEntry()`,
> `putFirst(K, V)`, `putLast(K, V)`, and `reversed()` are all available
> directly. Walking `entrySet()` to find the oldest entry is O(n) and
> obscures the intent; `pollFirstEntry()` is the natural primitive for an
> LRU-style eviction. Note that this is one of the few places where
> declaring the variable as `LinkedHashMap` (or `SequencedMap`) rather than
> `Map` is correct — you are depending on the encounter-order contract.

```java
// bad — O(n) walk to get the oldest entry, then a second lookup to remove it
Map<String, Session> cache = new LinkedHashMap<>();

void evictOldest() {
  Iterator<Map.Entry<String, Session>> it = cache.entrySet().iterator();
  if (it.hasNext()) {
    it.next();
    it.remove();
  }
}

// good — the ordering contract is in the declared type, and the operation
// is a single call
SequencedMap<String, Session> cache = new LinkedHashMap<>();

void evictOldest() {
  cache.pollFirstEntry();
}
```

## 20.12 Never structurally modify a collection while iterating it — use `Iterator.remove`, `removeIf`, or iterate a copy.

> Why? The `java.util` collections are *fail-fast*: an `add` or `remove`
> during a `for`-each loop bumps a modification counter the iterator
> checks, and the next `next()` throws `ConcurrentModificationException`.
> Worse, removing the second-to-last element can leave the loop terminating
> *without* throwing, so the bug hides in tests and appears in production
> with a different data shape. Fail-fast behavior is best-effort and must
> never be relied on for correctness.

```java
// bad — ConcurrentModificationException, or worse, a silent skipped element
for (Order order : orders) {
  if (order.isCancelled()) {
    orders.remove(order);
  }
}

// good — the iterator's own remove keeps the modification count in sync
for (Iterator<Order> it = orders.iterator(); it.hasNext(); ) {
  if (it.next().isCancelled()) {
    it.remove();
  }
}

// good — when the loop body also needs to touch the original collection
for (Order order : List.copyOf(orders)) {
  if (order.isCancelled()) {
    orders.remove(order);
  }
}
```

## 20.13 Use `removeIf` when the predicate is the entire loop body.

> Why? `Collection.removeIf(Predicate)` states the intent in one line and
> lets the implementation choose an efficient strategy — `ArrayList`
> overrides `removeIf` so that removal is one compacting pass instead of the
> repeated element shifting a `remove` per match causes. The explicit iterator
> loop from 20.12 is still correct; it is just longer and slower here.

```java
// bad — correct but O(n^2) on ArrayList, and four lines of ceremony
for (Iterator<Order> it = orders.iterator(); it.hasNext(); ) {
  if (it.next().isCancelled()) {
    it.remove();
  }
}

// good
orders.removeIf(Order::isCancelled);
```

## 20.14 Do not use `Arrays.asList` when you need a growable list, and never when you need a snapshot.

> Why? `Arrays.asList` returns a fixed-size list *backed by the array you
> passed in*. `add` and `remove` throw `UnsupportedOperationException`, and
> `set` writes through to the original array — so it is neither mutable nor
> immutable, which is the worst of both. Its one remaining use is a cheap
> `List` view over an existing array you control. `List.of` is the right
> factory for a literal, and `new ArrayList<>(...)` for a growable copy.

```java
// bad — throws UnsupportedOperationException on the first add
List<String> tags = Arrays.asList("alpha", "beta");
tags.add("gamma");

// bad — set() writes through and corrupts the caller's array
String[] source = readTags();
List<String> view = Arrays.asList(source);
view.set(0, "redacted");  // source[0] is now "redacted"

// good — immutable literal
List<String> fixedTags = List.of("alpha", "beta");

// good — growable copy
List<String> growableTags = new ArrayList<>(List.of("alpha", "beta"));

// good — an explicit, isolated snapshot of an array
List<String> snapshot = List.of(source);
```

## 20.15 Convert a collection to a typed array with `toArray(new T[0])` or `toArray(T[]::new)`, never the zero-argument `toArray`.

> Why? `Collection.toArray()` returns `Object[]`, so casting the result to
> `String[]` throws `ClassCastException` at runtime — the array's *runtime*
> component type really is `Object`. The generic overloads produce an array
> of the right runtime type. `new T[0]` is the idiomatic argument: it avoids
> the trailing-`null` semantics of an oversized array, and the presizing it
> gives up is not a reliable win — do not presize for speed without a
> measurement of your own.

```java
// bad — compiles, then throws ClassCastException at runtime
String[] cast = (String[]) nameSet.toArray();

// bad — if nameSet shrinks between size() and toArray(), the trailing slots
// are silently null
String[] presized = nameSet.toArray(new String[nameSet.size()]);

// good
String[] names = nameSet.toArray(new String[0]);

// good — Java 11+, reads better in a stream-adjacent context
String[] names = nameSet.toArray(String[]::new);
```

## 20.16 Build comparators from the `Comparator` factory chain rather than hand-writing `compare`.

> Why? A hand-written `compare` that subtracts two `int`s overflows for
> values spanning `Integer.MIN_VALUE`/`MAX_VALUE` and silently returns the
> wrong sign; a hand-written multi-key comparator is a nest of nested `if`s
> that is easy to get non-transitive. `Comparator.comparing`,
> `thenComparing`, `comparingInt`, and `reversed` compose into a single
> readable expression with none of those failure modes. A non-transitive
> comparator makes `List.sort` throw
> `IllegalArgumentException: Comparison method violates its general contract!`.

```java
// bad — subtraction overflows, and the tiebreak logic is hand-rolled
orders.sort(
    (a, b) -> {
      int byPriority = a.priority() - b.priority();
      if (byPriority != 0) {
        return byPriority;
      }
      return a.createdAt().compareTo(b.createdAt());
    });

// good
orders.sort(
    Comparator.comparingInt(Order::priority).thenComparing(Order::createdAt));

// good — descending on the primary key, ascending on the tiebreak
orders.sort(
    Comparator.comparingInt(Order::priority)
        .reversed()
        .thenComparing(Order::createdAt));
```

## 20.17 Wrap a comparator in `Comparator.nullsFirst` or `nullsLast` whenever the sort key can be null.

> Why? `Comparator.comparing(Order::assignee)` throws
> `NullPointerException` the moment one element's key is null, and it throws
> from inside `List.sort`, so the stack trace points at the sort, not at the
> data. `nullsFirst`/`nullsLast` make the null policy explicit and part of
> the comparator, where a reader can see it.

```java
// bad — NullPointerException from inside sort() when any assignee is null
orders.sort(Comparator.comparing(Order::assignee));

// good — nulls sort last, explicitly
orders.sort(
    Comparator.comparing(
        Order::assignee, Comparator.nullsLast(Comparator.naturalOrder())));

// good — an entire comparator made null-tolerant at the element level
Comparator<Order> byAssignee =
    Comparator.nullsLast(Comparator.comparing(Order::assignee));
```

## 20.18 Never mutate an object after using it as a `HashSet` element or a `HashMap` key.

> Why? Hash-based collections place an element in a bucket derived from its
> `hashCode` *at insertion time*. Mutating a field that participates in
> `hashCode` moves the element's logical bucket without moving the element,
> so `contains` returns `false` for an object that is demonstrably in the
> set and `remove` silently does nothing — a leak that is invisible until
> the set grows unbounded. Use immutable key types (a `record` with only
> immutable components is ideal — see [Chapter 12](12-records.md)).
> **Suggestion** — no check detects a key mutated after insertion. Note that
> `checkstyle/EqualsHashCode` does *not* cover this rule: it flags a class
> that overrides one of `equals`/`hashCode` without the other, and the
> `MutableKey` below correctly overrides both.

```java
// bad — mutable key; after the rename, the map cannot find its own entry
final class MutableKey {
  private String name;

  void setName(String name) {
    this.name = name;
  }

  @Override
  public boolean equals(Object o) {
    return o instanceof MutableKey other && Objects.equals(name, other.name);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name);
  }
}

MutableKey key = new MutableKey();
Map<MutableKey, Order> byKey = new HashMap<>();
byKey.put(key, order);
key.setName("renamed");
byKey.get(key);  // null — the entry is stranded in the old bucket

// good — an immutable key cannot drift out of its bucket
record OrderKey(String tenantId, String name) {}

Map<OrderKey, Order> byOrderKey = new HashMap<>();
byOrderKey.put(new OrderKey("acme", "initial"), order);
```

## 20.19 Use `computeIfAbsent`, `merge`, and `getOrDefault` instead of get-then-null-check-then-put.

> Why? The three-step idiom hashes the key two or three times, and in the
> multi-value-map case it is easy to write a version that discards an
> existing list. The `Map` default methods added in Java 8 do a single
> lookup and read as a statement of intent. Note the one hazard:
> `computeIfAbsent` must not modify the same map from inside its mapping
> function — the `Map` javadoc states "the mapping function should not modify
> this map during computation," and non-concurrent implementations such as
> `HashMap` throw `ConcurrentModificationException` on a best-effort basis
> when they detect it.

```java
// bad — two hash lookups, and a shape that invites "= new ArrayList<>()"
// to be written on the wrong branch
List<Order> forCustomer = byCustomer.get(customerId);
if (forCustomer == null) {
  forCustomer = new ArrayList<>();
  byCustomer.put(customerId, forCustomer);
}
forCustomer.add(order);

// good
byCustomer.computeIfAbsent(customerId, id -> new ArrayList<>()).add(order);

// good — counting, without a null branch at all
counts.merge(status, 1, Integer::sum);

// good — a read that needs a fallback but must not insert one
int limit = quotas.getOrDefault(tenantId, DEFAULT_QUOTA);
```

## 20.20 Presize a `HashMap` or `ArrayList` when the final size is known, and use the Java 19+ `newHashMap` factories.

> Why? `HashMap` resizes and rehashes every entry when it passes its load
> factor; `ArrayList` copies its backing array when it grows. Both are
> avoidable when the size is known. The subtlety is that
> `new HashMap<>(n)` takes an *initial capacity*, not an expected entry
> count — with the default 0.75 load factor a map given capacity `n` still
> resizes before it holds `n` entries.
> `HashMap.newHashMap(int numMappings)` (and the matching
> `LinkedHashMap.newLinkedHashMap`, `HashSet.newHashSet`) do that arithmetic
> for you.

```java
// bad — an initial capacity of 100 resizes before it holds 100 entries
Map<String, Order> byId = new HashMap<>(100);

// bad — grows and copies repeatedly for a known-size result
List<Summary> summaries = new ArrayList<>();
for (Order order : orders) {
  summaries.add(summarize(order));
}

// good
Map<String, Order> byId = HashMap.newHashMap(100);
List<Summary> summaries = new ArrayList<>(orders.size());
for (Order order : orders) {
  summaries.add(summarize(order));
}
```

## 20.21 Use primitive arrays or primitive streams when a collection is primitive-heavy and on a hot path.

> Why? `List<Integer>` stores a reference per element and boxes on every
> `add` and unboxes on every read; an `int[]` of the same length is
> typically several times smaller and has no indirection. Boxed arithmetic
> in a tight loop also allocates, which is what turns a "just a list of ids"
> into GC pressure. This is a targeted optimization — do not contort ordinary
> code for it — but the choice matters for large or hot collections. See
> [Chapter 29](29-numeric-types-and-literals.md) for the boxing rules
> themselves.

```java
// bad — an Integer object per element, boxed on add and unboxed on read
List<Integer> ids = new ArrayList<>();
for (int i = 0; i < 1_000_000; i++) {
  ids.add(i);
}
long total = 0;
for (Integer id : ids) {
  total += id;
}

// good — no boxing at all
int[] ids = new int[1_000_000];
for (int i = 0; i < ids.length; i++) {
  ids[i] = i;
}
long total = Arrays.stream(ids).asLongStream().sum();
```

## 20.22 Prefer a `List` to an array for reference element types, and reserve arrays for primitives.

> Why? Effective Java, 3rd ed., Item 28: "Prefer lists to arrays." Arrays
> are covariant (`Object[] o = new String[1]` compiles) and reified, so a
> bad store fails at *runtime* with `ArrayStoreException`; generic `List`s
> are invariant and erased, so the same mistake fails at *compile* time.
> Arrays remain correct for primitives (20.21) and for fixed-length numeric
> buffers; everywhere else the list is the safer default.

```java
// bad — compiles, then throws ArrayStoreException at runtime
Object[] objects = new String[1];
objects[0] = 42;

// good — the equivalent list mistake does not compile at all
List<Object> objects = new ArrayList<String>();  // compile error
```

## 20.23 Do not synchronize a collection with `Collections.synchronizedMap` when a `java.util.concurrent` type exists.

> Why? `Collections.synchronizedMap` guards each individual method with one
> lock, which serializes all access and still leaves every compound
> operation (check-then-act, iterate) racy — its javadoc requires the caller
> to hold the wrapper's monitor manually when iterating.
> `ConcurrentHashMap` gives lock-striped concurrent access plus atomic
> compound operations (`putIfAbsent`, `compute`, `merge`) as first-class
> methods. See [Chapter 26](26-concurrency-fundamentals.md) for the full
> concurrency treatment.

```java
// bad — a serializing lock, and the check-then-act below is still racy
Map<String, Session> sessions = Collections.synchronizedMap(new HashMap<>());
if (!sessions.containsKey(id)) {
  sessions.put(id, newSession(id));  // two threads can both get here
}

// good — the compound operation is atomic
Map<String, Session> sessions = new ConcurrentHashMap<>();
sessions.computeIfAbsent(id, this::newSession);
```
