<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 11. Generics & PEP 695

Python 3.12 makes PEP 695 type-parameter syntax the preferred way to
write generics. [pyguide §3.19.15](https://google.github.io/styleguide/pyguide.html#s3.19.15-generics) and
[§3.19.10](https://google.github.io/styleguide/pyguide.html#s3.19.10-typevars) remain relevant; prefer the new form
when it clarifies.

**Tool alignment:** Generics guidance is **Suggestion** (no `UP` enabled). Keep `target-version = 'py312'` so Ruff can eventually enforce modern forms.

## 11.1 Prefer PEP 695 `def f[T](...):` / `class Box[T]:` over `TypeVar` for new code.

> Why? The new syntax scopes type params to the declaration and reads like other languages.
> **Suggestion.**

```python
# bad
from typing import TypeVar
T = TypeVar('T')
def first(items: list[T]) -> T: ...

# good
def first[T](items: list[T]) -> T:
  return items[0]
```

## 11.2 Use bounds and constraints on type parameters explicitly.

> Why? Unbounded params become `Any`-shaped in practice.
> **Suggestion.**

```python
# bad
def sort_key[T](value: T) -> T: ...

# good
def sort_key[T: str](value: T) -> T:
  return value.lower()  # type: ignore[return-value]
```

## 11.3 Prefer `type Alias[T] = ...` for generic aliases on 3.12.

> Why? PEP 695 aliases are clearer than `TypeAlias` assignments.
> **Suggestion.**

```python
# bad
from typing import TypeAlias
Result: TypeAlias = tuple[bool, str]

# good
type Result = tuple[bool, str]
```

## 11.4 Do not mix old `TypeVar` and PEP 695 params in one declaration.

> Why? Mixing styles confuses checkers and readers.
> **Suggestion.**

```python
# bad - TypeVar plus [T] in the same API surface
# good - pick PEP 695 for new APIs
```

## 11.5 Use `TypeVarTuple` / `*` unpacking only when variadic types are real.

> Why? Most APIs need one or two params, not variadic generics.
> **Suggestion.**

```python
# bad - Variadic for a fixed pair
# good - tuple[T, U] or a dataclass
```

## 11.6 Parametrize protocols and ABCs the same way you parametrize classes.

> Why? Generic protocols keep repositories and factories honest.
> **Suggestion.**

```python
# bad
class Repo(Protocol):
  def get(self, key: str) -> object: ...

# good
class Repo[T](Protocol):
  def get(self, key: str) -> T: ...
```

## 11.7 Avoid `Any` as a generic escape hatch.

> Why? If you need escape, isolate it at a boundary with a comment.
> **Suggestion.**

```python
# bad
def parse[T](raw: str) -> T:
  return json.loads(raw)  # type: ignore

# good
def parse_object(raw: str) -> dict[str, object]:
  data = json.loads(raw)
  if not isinstance(data, dict):
    raise TypeError('object expected')
  return data
```

## 11.8 Keep variance explicit only when declaring libraries that need it.

> Why? Application code rarely needs `covariant=True` TypeVars.
> **Suggestion.**

```python
# bad - cargo-cult variance in app code
# good - default invariance unless you ship a typed library API
```

## 11.9 Prefer concrete aliases at application edges over leaking bare type params.

> Why? Call sites should see `OrderRepo`, not `Repo[Order]` everywhere if one binding dominates.
> **Suggestion.**

```python
# bad - Repo[Order] repeated 40 times
# good
type OrderRepo = Repo[Order]
```

## 11.10 Do not invent phantom type parameters that never appear in the signature.

> Why? Unused type params are lies.
> **Suggestion.**

```python
# bad
class Service[T]:
  def ping(self) -> str:
    return 'ok'

# good
class Service:
  def ping(self) -> str:
    return 'ok'
```

## 11.11 Use `typing.overload` for small finite signature sets; do not fake them with generics.

> Why? Overloads document distinct return types per input.
> **Suggestion.**

```python
# bad - return Any
# good - @overload pairs for str vs bytes inputs
```

## 11.12 Test generic helpers with at least two concrete type arguments in unit tests.

> Why? Generics that only ever see one type are premature.
> **Suggestion.**

```python
# bad - only tested with str
# good - tests for str and int specializations
```
