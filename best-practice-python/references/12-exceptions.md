<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 12. Exceptions

Exceptions are the error mechanism. [pyguide §2.4](https://google.github.io/styleguide/pyguide.html#s2.4-exceptions)
rejects using them for normal control flow and rejects bare excepts.

**Tool alignment:** `E722` (bare except) is **Violation**. Hierarchy and raising style are **Suggestion**.

## 12.1 Catch specific exceptions; never bare `except:`.

> Why? Bare except catches `KeyboardInterrupt` and `SystemExit`.
> **Violation - enforced by `E722`.**

```python
# bad
try:
  parse(raw)
except:
  return None

# good
try:
  parse(raw)
except ValueError:
  return None
```

## 12.2 Do not use exceptions for ordinary control flow.

> Why? Expected emptiness is a return value or Result-like type, not `raise`.
> **Suggestion.**

```python
# bad
def find(name: str) -> User:
  raise StopIteration

# good
def find(name: str) -> User | None:
  return None
```

## 12.3 Raise `ValueError` / `TypeError` / domain errors with actionable messages.

> Why? Empty raises waste operators.
> **Suggestion.**

```python
# bad
raise ValueError()

# good
raise ValueError(f'rate must be in [0, 1], got {rate}')
```

## 12.4 Define a small domain exception hierarchy rooted at one package error type.

> Why? Callers catch the root; internals raise leaves.
> **Suggestion.**

```python
# bad - raise Exception('nope')
# good
class OrdersError(Exception):
  ...

class OrderNotFoundError(OrdersError):
  ...
```

## 12.5 Prefer exception chaining with `raise ... from err` when translating errors.

> Why? Chaining preserves cause for logs and Sentry.
> **Suggestion.**

```python
# bad
except KeyError:
  raise OrderNotFoundError(order_id)

# good
except KeyError as err:
  raise OrderNotFoundError(order_id) from err
```

## 12.6 Do not catch `Exception` unless at a process/request boundary that logs and re-shapes.

> Why? Broad catches in libraries hide bugs.
> **Suggestion.**

```python
# bad
def helper():
  try:
    work()
  except Exception:
    pass

# good - boundary only
try:
  work()
except Exception:
  logger.exception('request failed')
  raise
```

## 12.7 Never use `assert` for runtime input validation in production APIs.

> Why? `assert` can be stripped with `-O`. Use `raise` / Pydantic.
> **Suggestion.**

```python
# bad
assert rate >= 0

# good
if rate < 0:
  raise ValueError('rate must be >= 0')
```

## 12.8 Map domain errors to HTTP errors at the FastAPI boundary, not deep in repositories.

> Why? See chapter 36. Repositories raise domain exceptions.
> **Suggestion.**

```python
# bad - HTTPException inside SQL helper
# good - OrderNotFoundError in repo; handler maps to 404
```

## 12.9 Avoid returning `(value, error)` tuples when exceptions express failure better.

> Why? Dual returns recreate Go without its compiler help.
> **Suggestion.**

```python
# bad
def load() -> tuple[Config | None, Exception | None]:
  ...

# good
def load() -> Config:
  ...
```

## 12.10 Clean up with `finally` or context managers, not duplicated cleanup in `except` and success paths.

> Why? See chapter 13.
> **Suggestion.**

```python
# bad - close() copied three times
# good - with open(...) as handle:
```

## 12.11 Do not raise string exceptions or non-`BaseException` values.

> Why? Only exception instances are valid.
> **Suggestion.**

```python
# bad
raise 'failed'  # type: ignore[misc]

# good
raise RuntimeError('failed')
```

## 12.12 Keep `except` clauses ordered from most specific to least specific.

> Why? Broad handlers first shadow useful specifics.
> **Suggestion.**

```python
# bad
except Exception:
  ...
except ValueError:
  ...

# good
except ValueError:
  ...
except Exception:
  ...
```
