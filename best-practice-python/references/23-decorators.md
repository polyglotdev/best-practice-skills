<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 23. Decorators

[pyguide §2.17](https://google.github.io/styleguide/pyguide.html#s2.17-function-and-method-decorators) covers
decorator discipline. Preserve signatures with `functools.wraps`.

**Tool alignment:** Decorator rules are **Suggestion**.

## 23.1 Always use `@functools.wraps(fn)` in decorator wrappers.

> Why? Otherwise tracebacks and OpenAPI names break.
> **Suggestion.**

```python
# bad
def deco(fn):
  def wrapper(*args, **kwargs):
    return fn(*args, **kwargs)
  return wrapper

# good
def deco(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    return fn(*args, **kwargs)
  return wrapper
```

## 23.2 Prefer ParamSpec/`Concatenate` when typing decorators.

> Why? Keeps FastAPI routes typed.
> **Suggestion.**

```python
# bad - wrapper -> Callable[..., Any]
# good - ParamSpec typed decorator
```

## 23.3 Keep decorators tiny and composable; avoid mega-decorators that auth+log+retry+trace.

> Why? Split cross-cutting concerns.
> **Suggestion.**

```python
# bad - @swiss_army
# good - @retry @traced @require_auth
```

## 23.4 Do not use decorators to mutate global registries at import time without an explicit app wiring path.

> Why? Import side effects hurt tests.
> **Suggestion.**

```python
# bad - @register_handler on import
# good - explicit router.includes
```

## 23.5 Preserve async-ness: async wrappers for async callables.

> Why? Awaiting a sync wrapper is a bug.
> **Suggestion.**

```python
# bad - sync wrapper around async def
# good - async def wrapper with await fn()
```

## 23.6 Document decorator semantics (pre/post, exception policy) in the decorator docstring.

> Why? Call sites cannot see the wrapper body.
> **Suggestion.**

```python
# bad - undocumented retry policy
# good - docstring states attempts/backoff
```

## 23.7 Avoid stacking more than three decorators without a strong reason.

> Why? Order becomes unknowable.
> **Suggestion.**

```python
# bad - six stacked decorators
# good - combine or simplify middleware
```

## 23.8 Prefer FastAPI dependencies over custom decorators for request-scoped auth/DB.

> Why? Dependencies are testable and visible in signatures.
> **Suggestion.**

```python
# bad - @auth_required hiding Depends
# good - user: Annotated[User, Depends(require_user)]
```

## 23.9 Do not swallow exceptions inside decorators unless that is the product behavior.

> Why? Silent failures cross every call site.
> **Suggestion.**

```python
# bad - except Exception: return None in wrapper
# good - let it raise; log at boundary
```

## 23.10 Use class decorators sparingly; prefer functions or metaclasses only when required.

> Why? Class decorators obscure construction.
> **Suggestion.**

```python
# bad - @register on every model class
# good - explicit registry.add(Model)
```

## 23.11 Ensure decorators work on methods (mind `self`/`cls`).

> Why? Broken method decorators show up late.
> **Suggestion.**

```python
# bad - wrapper loses self
# good - tests cover instance method decoration
```

## 23.12 Prefer context managers for temporary state over decorators that mutate process globals.

> Why? Globals + decorators race.
> **Suggestion.**

```python
# bad - @use_timezone mutates global TZ
# good - with timezone_context(...):
```
