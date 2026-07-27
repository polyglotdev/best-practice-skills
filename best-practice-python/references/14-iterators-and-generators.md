<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 14. Iterators & Generators

Iterators and generators express streaming work.
[pyguide §2.9](https://google.github.io/styleguide/pyguide.html#s2.9-generators) covers generator decisions.

**Tool alignment:** Iterator style is **Suggestion**.

## 14.1 Prefer generators for large or infinite sequences.

> Why? Materializing huge lists wastes memory.
> **Suggestion.**

```python
# bad
def read_lines(path: Path) -> list[str]:
  return path.read_text().splitlines()

# good
def read_lines(path: Path) -> Iterator[str]:
  with path.open() as handle:
    for line in handle:
      yield line.rstrip('\n')
```

## 14.2 Use generator `send`/`throw` rarely; prefer plain iterators and async streams.

> Why? Coroutines-as-generators are hard to follow.
> **Suggestion.**

```python
# bad - send-based protocol for ordinary pipelines
# good - next()/for-loops or async iterators
```

## 14.3 Annotate generators as `Iterator[T]` / `Iterable[T]` / `Generator[T, None, R]`.

> Why? Precise types document yield vs return.
> **Suggestion.**

```python
# bad
def walk(nodes):
  yield from nodes

# good
def walk(nodes: Iterable[Node]) -> Iterator[Node]:
  yield from nodes
```

## 14.4 Prefer `yield from` when delegating to another iterable.

> Why? Manual loops reimplement delegation badly.
> **Suggestion.**

```python
# bad
for item in inner:
  yield item

# good
yield from inner
```

## 14.5 Do not mutate a list while iterating it; iterate a copy or build a new list.

> Why? Live mutation skips elements.
> **Suggestion.**

```python
# bad
for item in items:
  if bad(item):
    items.remove(item)

# good
items[:] = [item for item in items if not bad(item)]
```

## 14.6 Exhaust or close generators that hold resources.

> Why? Contextlib and `closing` help.
> **Suggestion.**

```python
# bad - leave a generator holding a file open
# good - wrap in context manager that closes
```

## 14.7 Prefer stdlib iterators (`itertools`) over hand-rolled index arithmetic.

> Why? Index loops hide off-by-ones.
> **Suggestion.**

```python
# bad
i = 0
while i < len(items):
  ...
  i += 1

# good
for item in items:
  ...
```

## 14.8 Return iterators from public APIs only when streaming is part of the contract; otherwise return concrete collections.

> Why? Callers often need `len` and multiple passes.
> **Suggestion.**

```python
# bad - returns mysterious generator from a small in-memory API
# good - list[User] for small results; Iterator for streams
```

## 14.9 Do not implement `__iter__` that returns `self` unless the object is a single-pass iterator.

> Why? Reusable iterables should return a fresh iterator.
> **Suggestion.**

```python
# bad - container exhausted after one for-loop
# good - __iter__ returns iter(self._items)
```

## 14.10 Use generator expressions for one-shot pipelines; use lists when you need reuse.

> Why? Genexps are lazy and single-pass.
> **Suggestion.**

```python
# bad
rows = (normalize(r) for r in raw)
first = list(rows)
second = list(rows)  # empty

# good
rows = [normalize(r) for r in raw]
```

## 14.11 Avoid `next()` without a default when emptiness is expected.

> Why? Catching `StopIteration` at call sites is noisy.
> **Suggestion.**

```python
# bad
item = next(iterator)

# good
item = next(iterator, None)
```

## 14.12 Name generator functions as verbs that imply streaming (`iter_`, `walk_`, `stream_`).

> Why? Names that look eager surprise callers.
> **Suggestion.**

```python
# bad
def users() -> Iterator[User]:
  ...

# good
def iter_users() -> Iterator[User]:
  ...
```
