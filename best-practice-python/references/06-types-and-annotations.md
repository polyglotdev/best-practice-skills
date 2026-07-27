<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 6. Types & Annotations

Type annotations are required on public APIs in this skill.
[pyguide §2.21](https://google.github.io/styleguide/pyguide.html#s2.21-type-annotated-code) and
[§3.19](https://google.github.io/styleguide/pyguide.html#s3.19-type-annotations) are normative. Floor is Python 3.12:
use `X | Y`, builtin generics (`list[str]`), and PEP 695 where it clarifies.

**Tool alignment:** Annotation style is **Suggestion** under the shipped Ruff select (no `ANN`/`UP`). Undefined names that annotations accidentally introduce still fail `F821`.

## 6.1 Annotate every public function parameter and return type.

> Why? [pyguide §3.19.1](https://google.github.io/styleguide/pyguide.html#s3.19.1-general-rules) expects annotations on typed code. Untyped public APIs force every caller to guess.
> **Suggestion.**

```python
# bad
def add(a, b):
  return a + b

# good
def add(a: int, b: int) -> int:
  return a + b
```

## 6.2 Use `X | None` for optional values, not `Optional[X]` unless supporting older checkers that require it.

> Why? [pyguide §3.19.5](https://google.github.io/styleguide/pyguide.html#s3.19.5-none-type) discusses `None`. On 3.12, the union operator is the default idiom.
> **Suggestion.**

```python
# bad
from typing import Optional
def find(name: str) -> Optional[User]:
  ...

# good
def find(name: str) -> User | None:
  ...
```

## 6.3 Prefer builtin generics (`list`, `dict`, `set`, `tuple`) over `typing.List` and friends.

> Why? PEP 585 made builtin generics the modern form. `typing.List` is legacy on 3.12.
> **Suggestion.**

```python
# bad
from typing import Dict, List
def index(rows: List[str]) -> Dict[str, int]:
  ...

# good
def index(rows: list[str]) -> dict[str, int]:
  ...
```

## 6.4 Use `collections.abc` for parameter types (`Sequence`, `Mapping`, `Iterable`).

> Why? Accepting abstract collections lets callers pass tuples, lists, and custom sequences without over-constraining.
> **Suggestion.**

```python
# bad
def sum_lengths(items: list[str]) -> int:
  return sum(len(i) for i in items)

# good
from collections.abc import Sequence

def sum_lengths(items: Sequence[str]) -> int:
  return sum(len(i) for i in items)
```

## 6.5 Prefer `TypeAlias` / PEP 695 `type` aliases for repeated complex types.

> Why? [pyguide §3.19.6](https://google.github.io/styleguide/pyguide.html#s3.19.6-type-aliases) encourages aliases. On 3.12, `type UserId = str` is valid and readable.
> **Suggestion.**

```python
# bad
def get(user_id: str) -> dict[str, list[dict[str, str]]]:
  ...

# good
type JsonObject = dict[str, object]

def get(user_id: str) -> JsonObject:
  ...
```

## 6.6 Do not use stringified annotations unless required for a forward reference the checker cannot resolve.

> Why? [pyguide §3.19.3](https://google.github.io/styleguide/pyguide.html#s3.19.3-forward-declarations) covers forward refs. Prefer defining types in an order that avoids quotes.
> **Suggestion.**

```python
# bad
def bind(node: 'Node') -> None:
  ...

# good
class Node:
  def bind(self, node: Node) -> None:
    ...
```

## 6.7 Never write `# type: ignore` without an error code and a reason.

> Why? [pyguide §3.19.7](https://google.github.io/styleguide/pyguide.html#s3.19.7-ignoring-types) requires scoped ignores. Blanket ignores hide real bugs.
> **Suggestion.**

```python
# bad
reveal = legacy()  # type: ignore

# good
reveal = legacy()  # type: ignore[no-untyped-call]  # vendor stub missing
```

## 6.8 Annotate class attributes that form the public state.

> Why? Class-level annotations document invariants and feed dataclasses / Pydantic / SQLAlchemy mapping.
> **Suggestion.**

```python
# bad
class Counter:
  def __init__(self) -> None:
    self.value = 0

# good
class Counter:
  value: int

  def __init__(self) -> None:
    self.value = 0
```

## 6.9 Use `object` for "any object" and `Any` only at true trust boundaries.

> Why? `Any` disables checking. Prefer `object` plus narrowing, or a Protocol.
> **Suggestion.**

```python
# bad
from typing import Any
def dump(data: Any) -> str:
  return str(data)

# good
def dump(data: object) -> str:
  return str(data)
```

## 6.10 Prefer `TypedDict` or a Pydantic model over `dict[str, Any]` for structured records.

> Why? Untyped dicts lose keys and value shapes. Structured types catch renames.
> **Suggestion.**

```python
# bad
def handle(payload: dict[str, Any]) -> None:
  print(payload['userId'])

# good
class Payload(TypedDict):
  user_id: str

def handle(payload: Payload) -> None:
  print(payload['user_id'])
```

## 6.11 Keep return types precise; do not return `Any` from helpers to silence the checker.

> Why? Pushing `Any` outward infects callers. Fix the helper instead.
> **Suggestion.**

```python
# bad
def parse(raw: str) -> Any:
  return json.loads(raw)

# good
def parse(raw: str) -> JsonObject:
  data = json.loads(raw)
  if not isinstance(data, dict):
    raise TypeError('expected object')
  return data
```

## 6.12 Use `Self` for fluent methods that return the same class.

> Why? `Self` keeps subclasses correct without repeating the class name.
> **Suggestion.**

```python
# bad
class Builder:
  def with_name(self, name: str) -> 'Builder':
    self.name = name
    return self

# good
from typing import Self

class Builder:
  def with_name(self, name: str) -> Self:
    self.name = name
    return self
```
