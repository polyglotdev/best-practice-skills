<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 9. Dataclasses

`dataclasses` are the stdlib tool for value carriers. Prefer them over
hand-written `__init__`/`__repr__`/`__eq__` for plain data. For API schemas
and validation, prefer Pydantic models ([Chapter 34](34-fastapi-request-response-models.md)).

**Tool alignment:** Dataclass design is **Suggestion** under the shipped select.

## 9.1 Use `@dataclass` for plain data aggregates with little behavior.

> Why? Hand-rolled boilerplate drifts. Dataclasses generate the boring parts.
> **Suggestion.**

```python
# bad
class Point:
  def __init__(self, x: int, y: int) -> None:
    self.x = x
    self.y = y
  # eq/repr omitted or wrong

# good
@dataclass(frozen=True)
class Point:
  x: int
  y: int
```

## 9.2 Prefer `frozen=True` for value objects used as dict keys or shared widely.

> Why? Frozen instances catch accidental mutation and enable safe hashing.
> **Suggestion.**

```python
# bad
@dataclass
class UserId:
  value: str

# good
@dataclass(frozen=True)
class UserId:
  value: str
```

## 9.3 Use `field(default_factory=...)` for mutable defaults.

> Why? The same shared-mutable trap as function defaults applies.
> **Suggestion.**

```python
# bad
@dataclass
class Basket:
  items: list[str] = []

# good
@dataclass
class Basket:
  items: list[str] = field(default_factory=list)
```

## 9.4 Put fields without defaults before fields with defaults.

> Why? Dataclass field ordering rules match Python signature rules.
> **Suggestion.**

```python
# bad
@dataclass
class User:
  role: str = 'user'
  email: str

# good
@dataclass
class User:
  email: str
  role: str = 'user'
```

## 9.5 Use `__post_init__` for normalization and invariant checks.

> Why? Keep derived fields and validation next to construction.
> **Suggestion.**

```python
# bad - validate at every call site
# good
@dataclass(frozen=True)
class Email:
  value: str

  def __post_init__(self) -> None:
    if '@' not in self.value:
      raise ValueError('invalid email')
```

## 9.6 Do not use dataclasses as ORM entities or Pydantic stand-ins when those frameworks need their own base classes.

> Why? SQLAlchemy / Pydantic own persistence and validation semantics. Dataclasses are for in-process values.
> **Suggestion.**

```python
# bad - mixing concerns
@dataclass
class UserRow:
  id: str
  email: str  # also used as request body somehow

# good - separate types for DB, domain, and API
```

## 9.7 Mark non-init / derived fields with `field(init=False)` explicitly.

> Why? Hidden computed fields confuse construction call sites.
> **Suggestion.**

```python
# bad
@dataclass
class Rect:
  width: int
  height: int
  area: int = 0

# good
@dataclass
class Rect:
  width: int
  height: int
  area: int = field(init=False)

  def __post_init__(self) -> None:
    self.area = self.width * self.height
```

## 9.8 Use `slots=True` on 3.10+ when instances are numerous and the layout is fixed.

> Why? Slots cut memory and catch accidental attribute assignment.
> **Suggestion.**

```python
# bad - millions of open instances with __dict__
@dataclass
class Tick:
  ts: float
  price: float

# good
@dataclass(slots=True, frozen=True)
class Tick:
  ts: float
  price: float
```

## 9.9 Prefer `kw_only=True` when constructors gain many optional fields.

> Why? Keyword-only dataclasses prevent positional pile-ups.
> **Suggestion.**

```python
# bad
User('a@x.com', 'Ada', 'admin', True)

# good
@dataclass(kw_only=True)
class User:
  email: str
  name: str
  role: str = 'user'
  active: bool = True
```

## 9.10 Do not mutate frozen dataclass internals via `object.__setattr__` outside `__post_init__`.

> Why? Escaping frozen is a footgun. If you need mutation, do not freeze.
> **Suggestion.**

```python
# bad - random helper mutates frozen instance
object.__setattr__(user, 'email', new_email)

# good - return a replace()d copy
user = replace(user, email=new_email)
```

## 9.11 Use `replace()` for updates to frozen instances.

> Why? `dataclasses.replace` keeps value semantics clear.
> **Suggestion.**

```python
# bad
user.email = 'x'  # fails when frozen

# good
user = replace(user, email='x@example.com')
```

## 9.12 Keep methods on dataclasses thin; move workflows to services/functions.

> Why? Fat dataclasses become hidden services. Behavior that needs collaborators belongs elsewhere.
> **Suggestion.**

```python
# bad
@dataclass
class Order:
  def charge(self, gateway: Gateway) -> None:
    gateway.charge(self.total)

# good
def charge_order(order: Order, gateway: Gateway) -> None:
  gateway.charge(order.total)
```
