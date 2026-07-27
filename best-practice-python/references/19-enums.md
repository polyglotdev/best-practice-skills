<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 19. Enums

Enums replace stringly-typed status codes. Prefer `enum.Enum` /
`StrEnum` (3.11+) for closed sets of values.

**Tool alignment:** Enum style is **Suggestion**.

## 19.1 Use enums for closed sets of values that appear in APIs and DB columns.

> Why? Typos in string statuses become silent bugs.
> **Suggestion.**

```python
# bad
if status == 'acive':
  ...

# good
if status is Status.ACTIVE:
  ...
```

## 19.2 Prefer `StrEnum` when values serialize to strings (JSON, CSV).

> Why? Keeps wire format and type safety aligned.
> **Suggestion.**

```python
# bad
class Status(Enum):
  ACTIVE = 'active'

# good
class Status(StrEnum):
  ACTIVE = 'active'
```

## 19.3 Compare enums with `is` for singletons, or equality when values matter.

> Why? Identity works for enum members.
> **Suggestion.**

```python
# bad
if status == 'active':
  ...

# good
if status is Status.ACTIVE:
  ...
```

## 19.4 Do not add mutable state to enum members.

> Why? Enum members are singletons.
> **Suggestion.**

```python
# bad - member attributes that change at runtime
# good - keep enums as pure values
```

## 19.5 Use `enum.auto()` when values are opaque; use explicit values when they are part of a protocol.

> Why? Wire formats need stable values.
> **Suggestion.**

```python
# bad - auto() for HTTP-facing codes
# good - explicit string/int values for APIs
```

## 19.6 Namespace related values in one Enum rather than many module constants.

> Why? Discoverability beats scattered constants.
> **Suggestion.**

```python
# bad
STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'

# good
class Status(StrEnum):
  ACTIVE = 'active'
  INACTIVE = 'inactive'
```

## 19.7 Export enums from domain modules, not from route modules.

> Why? Routes should import domain types.
> **Suggestion.**

```python
# bad - Status defined in router.py
# good - Status in domain/orders.py
```

## 19.8 Teach Pydantic/FastAPI to use enums directly on fields.

> Why? OpenAPI then shows allowed values.
> **Suggestion.**

```python
# bad
status: str

# good
status: Status
```

## 19.9 Avoid `IntEnum` unless an external integer protocol requires it.

> Why? Ints invite accidental arithmetic.
> **Suggestion.**

```python
# bad - IntEnum for roles
# good - StrEnum for roles
```

## 19.10 Provide a parse helper that raises domain errors for unknown values.

> Why? Raw `Status(value)` tracebacks are harsh at boundaries.
> **Suggestion.**

```python
# bad
Status(raw)

# good
def parse_status(raw: str) -> Status:
  try:
    return Status(raw)
  except ValueError as err:
    raise ValidationError(f'unknown status {raw!r}') from err
```

## 19.11 Do not iterate enums for authorization logic without tests for new members.

> Why? Adding a member can widen access accidentally.
> **Suggestion.**

```python
# bad - for status in Status: allow()
# good - frozenset of allowed statuses tested explicitly
```

## 19.12 Keep enum names `UPPER_SNAKE` members and `CapWords` class names.

> Why? Matches pyguide naming.
> **Suggestion.**

```python
# bad
class status(Enum):
  Active = 'active'

# good
class Status(StrEnum):
  ACTIVE = 'active'
```
