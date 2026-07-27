<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 17. Collections

Prefer the right collection and the abstract type at boundaries.
[pyguide §2.8](https://google.github.io/styleguide/pyguide.html#s2.8-default-iterators-and-operators) encourages
idiomatic membership and iteration.

**Tool alignment:** Collection choices are **Suggestion**. `F601`/`F602` catch repeated dict keys.

## 17.1 Annotate returns as `list`/`dict` when concrete; accept `Sequence`/`Mapping` as inputs.

> Why? Widened inputs, precise outputs.
> **Suggestion.**

```python
# bad
def ids(users: list[User]) -> list[str]:
  return [u.id for u in users]

# good
def ids(users: Sequence[User]) -> list[str]:
  return [u.id for u in users]
```

## 17.2 Use `in` for membership, not manual loops.

> Why? Idiomatic and clearer.
> **Suggestion.**

```python
# bad
found = False
for x in items:
  if x == target:
    found = True

# good
found = target in items
```

## 17.3 Prefer `dict` insertion order (3.7+) over `OrderedDict` unless you need its extras.

> Why? OrderedDict is rarely required now.
> **Suggestion.**

```python
# bad - OrderedDict by habit
# good - plain dict
```

## 17.4 Use `setdefault` / `defaultdict` carefully; prefer clarity over cleverness.

> Why? Hidden inserts surprise readers.
> **Suggestion.**

```python
# bad - dense setdefault chains
# good - defaultdict or explicit if/else
```

## 17.5 Do not use a list as a queue; use `collections.deque`.

> Why? List pop(0) is O(n).
> **Suggestion.**

```python
# bad
queue = []
queue.pop(0)

# good
queue: deque[str] = deque()
queue.popleft()
```

## 17.6 Catch duplicate literal keys in dict displays.

> Why? `F601` flags repeated keys.
> **Violation - enforced by `F601`.**

```python
# bad
config = {'host': 'a', 'host': 'b'}

# good
config = {'host': 'b'}
```

## 17.7 Prefer tuples for fixed-length records; lists for homogeneous sequences.

> Why? Tuples signal immutability of shape.
> **Suggestion.**

```python
# bad
point = [1, 2]

# good
point = (1, 2)
```

## 17.8 Use `enumerate` instead of `range(len(...))`.

> Why? Cleaner and harder to desync.
> **Suggestion.**

```python
# bad
for i in range(len(items)):
  print(i, items[i])

# good
for i, item in enumerate(items):
  print(i, item)
```

## 17.9 Use `zip(..., strict=True)` on 3.10+ when lengths must match.

> Why? Silent truncation hides bugs.
> **Suggestion.**

```python
# bad
for a, b in zip(left, right):
  ...

# good
for a, b in zip(left, right, strict=True):
  ...
```

## 17.10 Prefer `collections.Counter` for tallying.

> Why? Hand-rolled counters reimplement edge cases.
> **Suggestion.**

```python
# bad
counts: dict[str, int] = {}
for item in items:
  counts[item] = counts.get(item, 0) + 1

# good
counts = Counter(items)
```

## 17.11 Do not mutate dicts while iterating keys; iterate `list(keys)` or build a new dict.

> Why? RuntimeError awaits.
> **Suggestion.**

```python
# bad
for key in data:
  if stale(key):
    del data[key]

# good
data = {k: v for k, v in data.items() if not stale(k)}
```

## 17.12 Expose read-only views (`MappingProxyType` / tuples) when sharing internal collections.

> Why? Prevents accidental caller mutation.
> **Suggestion.**

```python
# bad
return self._items  # mutable alias

# good
return tuple(self._items)
```
