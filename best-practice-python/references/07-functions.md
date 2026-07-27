<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 7. Functions

Functions should be small, typed, and free of surprising defaults.
[pyguide §2.12](https://google.github.io/styleguide/pyguide.html#s2.12-default-argument-values),
[§2.10](https://google.github.io/styleguide/pyguide.html#s2.10-lambda-functions), and
[§3.18](https://google.github.io/styleguide/pyguide.html#s3.18-function-length) guide this chapter.

**Tool alignment:** `E731` (lambda assignment) is **Violation**. Length and default-arg mutability are **Suggestion**.

## 7.1 Never use mutable default arguments.

> Why? [pyguide §2.12](https://google.github.io/styleguide/pyguide.html#s2.12-default-argument-values) bans mutable defaults because they are shared across calls.
> **Suggestion.**

```python
# bad
def append_item(item: str, items: list[str] = []) -> list[str]:
  items.append(item)
  return items

# good
def append_item(item: str, items: list[str] | None = None) -> list[str]:
  if items is None:
    items = []
  items.append(item)
  return items
```

## 7.2 Keep functions short enough to read without scrolling mental context.

> Why? [pyguide §3.18](https://google.github.io/styleguide/pyguide.html#s3.18-function-length) pushes for focused functions. Extract helpers when a function has multiple stages.
> **Suggestion.**

```python
# bad - 120-line function mixing IO, validation, and formatting
# good - validate(), load(), format() called from a thin orchestrator
```

## 7.3 Prefer keyword-only arguments for parameters that are easy to swap by position.

> Why? Boolean and option flags at the end should be keyword-only to avoid `do(True, False)` call sites.
> **Suggestion.**

```python
# bad
def copy(src: Path, dst: Path, overwrite: bool = False) -> None:
  ...

# good
def copy(src: Path, dst: Path, *, overwrite: bool = False) -> None:
  ...
```

## 7.4 Do not assign lambdas to names; use `def`.

> Why? Named lambdas lose annotations and produce worse tracebacks. `E731`.
> **Violation - enforced by `E731`.**

```python
# bad
square = lambda n: n * n

# good
def square(n: int) -> int:
  return n * n
```

## 7.5 Use early returns to keep the happy path unindented.

> Why? Guard clauses beat nested pyramids for readability.
> **Suggestion.**

```python
# bad
def handle(user: User | None) -> None:
  if user is not None:
    if user.active:
      process(user)

# good
def handle(user: User | None) -> None:
  if user is None:
    return
  if not user.active:
    return
  process(user)
```

## 7.6 Prefer pure functions for business rules; push IO to the edges.

> Why? Pure helpers are trivial to test. FastAPI handlers should orchestrate, not embed SQL.
> **Suggestion.**

```python
# bad
async def total(order_id: str) -> Decimal:
  order = await db.fetch(order_id)
  return sum(line.price for line in order.lines)

# good
def order_total(lines: Sequence[Line]) -> Decimal:
  return sum((line.price for line in lines), start=Decimal('0'))
```

## 7.7 Do not use `*args` / `**kwargs` to avoid designing a real signature.

> Why? Variadic bags hide required parameters and break autocomplete.
> **Suggestion.**

```python
# bad
def create_user(**kwargs: object) -> User:
  return User(**kwargs)

# good
def create_user(*, email: str, name: str) -> User:
  return User(email=email, name=name)
```

## 7.8 Return consistent types; do not return `None` and a value interchangeably without `| None` in the signature.

> Why? Inconsistent returns force every caller to guess. Annotate optionality.
> **Suggestion.**

```python
# bad
def find(name: str):
  if not name:
    return None
  return User(name)

# good
def find(name: str) -> User | None:
  if not name:
    return None
  return User(name)
```

## 7.9 Raise exceptions for exceptional failures; do not return magic error codes.

> Why? [pyguide §2.4](https://google.github.io/styleguide/pyguide.html#s2.4-exceptions) prefers exceptions over status tuples for errors.
> **Suggestion.**

```python
# bad
def load(path: Path) -> tuple[Config | None, str]:
  ...

# good
def load(path: Path) -> Config:
  if not path.exists():
    raise FileNotFoundError(path)
  ...
```

## 7.10 Name boolean arguments carefully and prefer enums when there are more than two modes.

> Why? `send(True)` is opaque. An enum or keyword-only flag reads clearly.
> **Suggestion.**

```python
# bad
notify(user, True)

# good
notify(user, channel=Channel.EMAIL)
```

## 7.11 Avoid ternary expressions for multi-statement logic; keep them for simple value selection.

> Why? [pyguide §2.11](https://google.github.io/styleguide/pyguide.html#s2.11-conditional-expressions) allows conditionals when they stay readable.
> **Suggestion.**

```python
# bad
value = do_a() if ready else do_b() if other else do_c()

# good
if ready:
  value = do_a()
elif other:
  value = do_b()
else:
  value = do_c()
```

## 7.12 Document side effects in the docstring or name (`save_`, `send_`, `write_`).

> Why? Readers assume functions are side-effect light unless the name says otherwise.
> **Suggestion.**

```python
# bad
def user(email: str) -> User:
  db.insert(...)
  return User(email)

# good
def create_user(email: str) -> User:
  db.insert(...)
  return User(email)
```
