<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 3. Naming

Names are the primary documentation of a Python codebase.
[pyguide §3.16](https://google.github.io/styleguide/pyguide.html#s3.16-naming) and [§3.16.2](https://google.github.io/styleguide/pyguide.html#s3.16.2-naming-conventions)
are normative. This skill uses those conventions unchanged; only indentation
and quotes are house overrides.

**Tool alignment:** Naming is almost entirely **Suggestion** under the shipped Ruff select (no `N` / pep8-naming). Ambiguous names caught by `E741` are **Violation**.

## 3.1 Use `snake_case` for functions, methods, modules, and variables.

> Why? [pyguide §3.16.2](https://google.github.io/styleguide/pyguide.html#s3.16.2-naming-conventions) standardizes snake_case for functions and vars so readers can parse roles at a glance.
> **Suggestion.**

```python
# bad
def GetOrder(OrderID: str) -> Order:
  ...

# good
def get_order(order_id: str) -> Order:
  ...
```

## 3.2 Use `CapWords` (PascalCase) for classes and exceptions.

> Why? Class names that look like functions confuse instantiation sites and autocompletion.
> **Suggestion.**

```python
# bad
class order_service:
  ...

# good
class OrderService:
  ...
```

## 3.3 Use `UPPER_SNAKE_CASE` for module-level constants.

> Why? Constants should read as fixed. Mixing styles makes mutation harder to spot.
> **Suggestion.**

```python
# bad
maxRetries = 3
Default_Timeout = 30

# good
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

## 3.4 Prefix "internal use" helpers with a single leading underscore.

> Why? A single underscore is the community signal for non-public API. It is not enforced by the language, but it guides `__all__` and reviews.
> **Suggestion.**

```python
# bad
def normalize_internal(name: str) -> str:
  ...

# good
def _normalize(name: str) -> str:
  ...
```

## 3.5 Never use `l`, `O`, or `I` as names.

> Why? [pyguide §3.16.1](https://google.github.io/styleguide/pyguide.html#s3.16.1-names-to-avoid) bans them because they are indistinguishable from `1` and `0` in many fonts. `E741`.
> **Violation - enforced by `E741`.**

```python
# bad
l = [1, 2, 3]
O = 0

# good
lengths = [1, 2, 3]
zero = 0
```

## 3.6 Name booleans as predicates: `is_`, `has_`, `can_`, `should_`.

> Why? `flag` and `status` force readers to chase definitions. Predicate names document the true branch.
> **Suggestion.**

```python
# bad
flag = user.role == 'admin'

# good
is_admin = user.role == 'admin'
```

## 3.7 Avoid redundant type suffixes in names (`user_list`, `name_string`) unless the type is the point.

> Why? With annotations, `users: list[User]` is clearer than `user_list`. Reserve suffixes for disambiguation.
> **Suggestion.**

```python
# bad
user_list: list[User] = load()

# good
users: list[User] = load()
```

## 3.8 Name exceptions `SomethingError` (or a narrow domain suffix), never bare `Error` in app code.

> Why? Bare `Error` shadows builtins and reads as unfinished design.
> **Suggestion.**

```python
# bad
class NotFound(Exception):
  ...

# good
class OrderNotFoundError(Exception):
  ...
```

## 3.9 Prefer full words over cryptic abbreviations, except widely known ones (`id`, `http`, `url`).

> Why? Abbreviations tax every new reader. Consistency with domain language beats clever shortness.
> **Suggestion.**

```python
# bad
def calc_ttl_for_usr(usr_id: str) -> int:
  ...

# good
def calculate_ttl_for_user(user_id: str) -> int:
  ...
```

## 3.10 Do not shadow builtins (`id`, `type`, `list`, `dict`, `str`, `input`).

> Why? Shadowing builtins breaks later code in the same scope and confuses readers who expect the builtin.
> **Suggestion.**

```python
# bad
def save(id: str, type: str) -> None:
  ...

# good
def save(entity_id: str, entity_type: str) -> None:
  ...
```

## 3.11 Name FastAPI path operation functions after the action, not the HTTP verb alone.

> Why? `get` / `post` collide across routers. `get_order` / `create_order` show up clearly in OpenAPI and traces.
> **Suggestion.**

```python
# bad
@router.get('/orders/{order_id}')
async def get(order_id: str) -> Order:
  ...

# good
@router.get('/orders/{order_id}')
async def get_order(order_id: str) -> Order:
  ...
```

## 3.12 Keep acronyms consistent: prefer `HttpClient` / `http_client` over mixed `HTTPClient` / `HttpURL`.

> Why? Python communities usually treat short acronyms as CapWords words (`Http`, `Url`). Pick one scheme and stick to it.
> **Suggestion.**

```python
# bad
class HTTPURLParser:
  ...

# good
class HttpUrlParser:
  ...
```

## 3.13 Use plural nouns for collections and singular nouns for single values.

> Why? Agreement between name and shape prevents off-by-one thinking at call sites.
> **Suggestion.**

```python
# bad
order: list[Order] = load_orders()

# good
orders: list[Order] = load_orders()
order: Order = orders[0]
```
