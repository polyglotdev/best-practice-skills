<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 13. Context Managers

Context managers own setup/teardown. [pyguide §3.11](https://google.github.io/styleguide/pyguide.html#s3.11-files-sockets-closeables)
requires closing files, sockets, and similar resources.

**Tool alignment:** Resource-closing discipline is **Suggestion** under the shipped select (no `SIM`/`PTH`).

## 13.1 Always open files with a `with` statement.

> Why? Manual `close()` is easy to skip on exceptions.
> **Suggestion.**

```python
# bad
handle = open(path)
data = handle.read()
handle.close()

# good
with path.open() as handle:
  data = handle.read()
```

## 13.2 Prefer `contextlib.contextmanager` / `asynccontextmanager` for ad-hoc helpers.

> Why? Lightweight generators beat full classes for simple cases.
> **Suggestion.**

```python
# bad - 40-line class for a lock helper
# good
@contextmanager
def locked(lock: Lock):
  lock.acquire()
  try:
    yield
  finally:
    lock.release()
```

## 13.3 Do not open resources in `__init__` without a matching close protocol.

> Why? Prefer context managers for lifetimes.
> **Suggestion.**

```python
# bad
client = ApiClient()  # opens sockets in __init__
# good
with ApiClient() as client:
  ...
```

## 13.4 Use `ExitStack` when the number of context managers is dynamic.

> Why? Variable `with` depth needs a stack.
> **Suggestion.**

```python
# bad - nested with that grows with N files
# good - ExitStack enters each path in a loop
```

## 13.5 Keep context-manager bodies short; do not hide business transactions inside unrelated `with` blocks.

> Why? Readers should see what is being protected.
> **Suggestion.**

```python
# bad - entire request inside a file with
# good - with only wraps the file IO section
```

## 13.6 For FastAPI, use lifespan/`asynccontextmanager` for app-scoped resources.

> Why? Global clients at import time complicate tests.
> **Suggestion.**

```python
# bad
redis = Redis.from_url(URL)

# good - attach to app.state in lifespan
```

## 13.7 Do not suppress exceptions in `__exit__` unless that is the documented contract.

> Why? Returning true swallows bugs.
> **Suggestion.**

```python
# bad
def __exit__(self, *args):
  return True

# good
def __exit__(self, exc_type, exc, tb):
  self.close()
  return False
```

## 13.8 Prefer `pathlib.Path.open` over bare `open` for path-typed APIs.

> Why? Keeps path types consistent.
> **Suggestion.**

```python
# bad
open(str(path))

# good
path.open()
```

## 13.9 Close DB sessions via dependency/context managers, never leak them across requests.

> Why? Session-per-request is the default web pattern.
> **Suggestion.**

```python
# bad - module-level Session()
# good - yield session in a FastAPI dependency
```

## 13.10 Use `closing()` for objects that have `.close()` but no context manager.

> Why? stdlib helper fills gaps.
> **Suggestion.**

```python
# bad - manual close on urlopen-like objects
# good
from contextlib import closing
with closing(obj) as handle:
  ...
```

## 13.11 Avoid context managers that perform surprising remote calls on enter.

> Why? Enter should be cheap and local when possible.
> **Suggestion.**

```python
# bad - with Client() hits network for auth every time
# good - explicit connect(); with only scopes the session
```

## 13.12 Pair every lock acquisition with a context manager.

> Why? Manual acquire/release deadlocks under exceptions.
> **Suggestion.**

```python
# bad
lock.acquire()
mutate()
lock.release()

# good
with lock:
  mutate()
```
