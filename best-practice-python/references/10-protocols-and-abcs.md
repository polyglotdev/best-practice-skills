<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 10. Protocols & ABCs

Structural typing with `typing.Protocol` is the preferred way to express
"needs a `.read()`" without forcing inheritance. ABCs remain useful when you
need virtual subclasses or shared concrete helpers.

**Tool alignment:** Protocol design is **Suggestion** under the shipped select.

## 10.1 Prefer `Protocol` for consumer-defined interfaces.

> Why? Callers should define the shape they need. Implementers should not be forced to inherit a library base class.
> **Suggestion.**

```python
# bad
class Repository(ABC):
  @abstractmethod
  def get(self, key: str) -> Order: ...

# good
class OrderRepository(Protocol):
  def get(self, key: str) -> Order: ...
```

## 10.2 Mark runtime-checkable protocols only when you truly need `isinstance`.

> Why? `@runtime_checkable` is limited (presence of attributes, not types). Prefer typing-time checks.
> **Suggestion.**

```python
# bad - isinstance everywhere
@runtime_checkable
class SupportsClose(Protocol):
  def close(self) -> None: ...

# good - annotate parameters; skip runtime isinstance
```

## 10.3 Keep protocols small (ISP). Split read/write surfaces.

> Why? Fat protocols force fake methods on implementers.
> **Suggestion.**

```python
# bad
class Store(Protocol):
  def get(self, key: str) -> bytes: ...
  def put(self, key: str, value: bytes) -> None: ...
  def list_keys(self) -> list[str]: ...
  def migrate(self) -> None: ...

# good - SupportsGet / SupportsPut separately
```

## 10.4 Use ABCs when you need shared concrete code or `@abstractmethod` enforcement at runtime.

> Why? ABCs help framework authors; Protocols help application authors.
> **Suggestion.**

```python
# bad - ABC for a one-method callback
# good - Protocol for callbacks; ABC for framework base with helpers
```

## 10.5 Do not mix Protocol and concrete inheritance casually.

> Why? A class can implement a Protocol structurally without listing it. Explicit subclassing of Protocol is rarely needed.
> **Suggestion.**

```python
# bad
class FileReader(SupportsRead, BaseModel):
  ...

# good - structural match without inheriting Protocol
```

## 10.6 Name protocols `SupportsX` / `XLike` / noun interfaces that read as capabilities.

> Why? Clear names document intent at annotation sites.
> **Suggestion.**

```python
# bad
class IReader(Protocol):
  ...

# good
class SupportsRead(Protocol):
  def read(self, n: int = -1) -> str: ...
```

## 10.7 Annotate FastAPI dependencies with Protocols when tests need fakes.

> Why? Protocols make `Annotated[OrdersRepo, Depends(...)]` easy to fake.
> **Suggestion.**

```python
# bad - depend on a concrete SQLAlchemy repo type everywhere
# good
class OrdersRepo(Protocol):
  async def get(self, order_id: str) -> Order: ...
```

## 10.8 Prefer `collections.abc` protocols (`Mapping`, `Sequence`) over custom ones when they fit.

> Why? Stdlib ABCs are understood by every type checker.
> **Suggestion.**

```python
# bad
class StringList(Protocol):
  def __iter__(self) -> Iterator[str]: ...

# good
from collections.abc import Sequence
def join(parts: Sequence[str]) -> str:
  return ','.join(parts)
```

## 10.9 Document module-level protocols next to the functions that consume them.

> Why? Orphan protocol files become dumping grounds. Keep them near use.
> **Suggestion.**

```python
# bad - app/types/protocols.py with 40 unrelated protocols
# good - protocols defined above the service that needs them
```

## 10.10 Avoid empty marker protocols used only for branding.

> Why? If a Protocol has no members, it is not an interface.
> **Suggestion.**

```python
# bad
class Entity(Protocol):
  ...

# good - give it the members callers need
```

## 10.11 Use `TypeVar` bounds with Protocols for generic callables.

> Why? Bounded TypeVars express "any T that supports X".
> **Suggestion.**

```python
# bad - Any
def close_all(resources: list[Any]) -> None:
  for r in resources:
    r.close()

# good
class SupportsClose(Protocol):
  def close(self) -> None: ...

def close_all(resources: list[SupportsClose]) -> None:
  for r in resources:
    r.close()
```

## 10.12 Do not invent home-grown plugin registries when a Protocol + explicit wiring will do.

> Why? Magic entry-point registries obscure the running graph. Wire plugins in `create_app()`.
> **Suggestion.**

```python
# bad - import side-effect registration
# good - pass a list[Plugin] into create_app(plugins=[...])
```
