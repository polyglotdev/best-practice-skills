<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 8. Classes

Classes own invariants. Prefer simple data carriers
([Chapter 9](09-dataclasses.md)) and functions when you do not need
encapsulation. [pyguide §2.13](https://google.github.io/styleguide/pyguide.html#s2.13-properties) and
[§3.15](https://google.github.io/styleguide/pyguide.html#s3.15-access-control) inform access patterns.

**Tool alignment:** Class design rules are **Suggestion** under the shipped select.

## 8.1 Do not write a class when a function or module-level helpers suffice.

> Why? Classes for namespacing alone add ceremony. Modules are namespaces.
> **Suggestion.**

```python
# bad
class MathUtils:
  @staticmethod
  def add(a: int, b: int) -> int:
    return a + b

# good
def add(a: int, b: int) -> int:
  return a + b
```

## 8.2 Make illegal states unrepresentable: validate in `__init__` / `__post_init__`.

> Why? Failing at construction beats failing deep in a call stack.
> **Suggestion.**

```python
# bad
class Period:
  def __init__(self, start: date, end: date) -> None:
    self.start = start
    self.end = end  # may be before start

# good
class Period:
  def __init__(self, start: date, end: date) -> None:
    if end < start:
      raise ValueError('end before start')
    self.start = start
    self.end = end
```

## 8.3 Prefer composition over deep inheritance.

> Why? Deep hierarchies couple unrelated changes. Compose collaborators.
> **Suggestion.**

```python
# bad
class AdminUser(AuthenticatedUser(LoggedUser(User))):
  ...

# good
class UserService:
  def __init__(self, auth: AuthClient, audit: AuditLog) -> None:
    self._auth = auth
    self._audit = audit
```

## 8.4 Use `@property` for derived values, not for hiding expensive IO.

> Why? [pyguide §2.13](https://google.github.io/styleguide/pyguide.html#s2.13-properties) wants properties that are cheap and unsurprising. IO belongs in methods.
> **Suggestion.**

```python
# bad
@property
def report(self) -> Report:
  return self._client.fetch_report()  # hidden network call

# good
def load_report(self) -> Report:
  return self._client.fetch_report()
```

## 8.5 Keep instance state private with a leading underscore and expose a narrow API.

> Why? [pyguide §3.15](https://google.github.io/styleguide/pyguide.html#s3.15-access-control) prefers accessors only when they add value.
> **Suggestion.**

```python
# bad
class Account:
  def __init__(self) -> None:
    self.balance = 0

# good
class Account:
  def __init__(self) -> None:
    self._balance = 0

  @property
  def balance(self) -> int:
    return self._balance
```

## 8.6 Implement `__repr__` for every nontrivial domain object.

> Why? `repr` is for developers. Include identifying fields; omit secrets.
> **Suggestion.**

```python
# bad
class User:
  def __init__(self, user_id: str, email: str) -> None:
    self.user_id = user_id
    self.email = email

# good
class User:
  def __init__(self, user_id: str, email: str) -> None:
    self.user_id = user_id
    self.email = email

  def __repr__(self) -> str:
    return f'User(user_id={self.user_id!r})'
```

## 8.7 Do not override `__eq__` without `__hash__` (or set `__hash__ = None`).

> Why? Inconsistent equality/hashing breaks set/dict membership.
> **Suggestion.**

```python
# bad
class Point:
  def __eq__(self, other: object) -> bool:
    ...

# good
@dataclass(frozen=True)
class Point:
  x: int
  y: int
```

## 8.8 Prefer `@classmethod` factories over ambiguous multi-purpose constructors.

> Why? Named factories document provenance (`from_json`, `from_row`).
> **Suggestion.**

```python
# bad
User(None, None, raw_json)  # magic overload

# good
User.from_json(raw_json)
```

## 8.9 Avoid deep nesting of classes; nest only when the inner type is meaningless alone.

> Why? [pyguide §2.6](https://google.github.io/styleguide/pyguide.html#s2.6-nested) discourages unnecessary nesting.
> **Suggestion.**

```python
# bad - nested helper class used elsewhere
# good - top-level private class `_Node` or a module-level helper
```

## 8.10 Do not store mutable class attributes as shared defaults.

> Why? Class-attribute lists/dicts are shared across instances.
> **Suggestion.**

```python
# bad
class Team:
  members: list[str] = []

# good
class Team:
  def __init__(self) -> None:
    self.members: list[str] = []
```

## 8.11 Prefer protocols / ABCs for shared behavior across unrelated classes.

> Why? See [Chapter 10](10-protocols-and-abcs.md). Nominal inheritance is not required for duck typing with type checkers.
> **Suggestion.**

```python
# bad
class FileLike(ABC):
  ...

# good - when structural typing is enough
class SupportsRead(Protocol):
  def read(self, n: int = -1) -> str: ...
```

## 8.12 Keep `__init__` for assignment and validation; do not launch threads or network calls there.

> Why? Constructors that do IO make testing and lifetimes painful. Use an explicit `open()` / async context manager.
> **Suggestion.**

```python
# bad
class Client:
  def __init__(self, url: str) -> None:
    self._session = httpx.Client(base_url=url)
    self._session.get('/health')

# good
class Client:
  def __init__(self, url: str) -> None:
    self._url = url
    self._session: httpx.Client | None = None

  def connect(self) -> None:
    self._session = httpx.Client(base_url=self._url)
```
