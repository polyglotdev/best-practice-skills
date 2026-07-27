"""Chapters 6-41 for best-practice-python."""

from __future__ import annotations

from scripts.python_skill._render import Rule, write_chapter

PY = 'https://google.github.io/styleguide/pyguide.html'


def _rules(*items: Rule) -> list[Rule]:
  assert len(items) >= 12
  return list(items)


def build() -> None:
  """Build chapters 6-10. Later chapters live in sibling modules."""
  write_chapter(
    '06-types-and-annotations.md',
    'Types & Annotations',
    f"""Type annotations are required on public APIs in this skill.
[pyguide §2.21]({PY}#s2.21-type-annotated-code) and
[§3.19]({PY}#s3.19-type-annotations) are normative. Floor is Python 3.12:
use `X | Y`, builtin generics (`list[str]`), and PEP 695 where it clarifies.""",
    'Annotation style is **Suggestion** under the shipped Ruff select (no '
    '`ANN`/`UP`). Undefined names that annotations accidentally introduce '
    'still fail `F821`.',
    _rules(
      Rule(
        'Annotate every public function parameter and return type.',
        f'[pyguide §3.19.1]({PY}#s3.19.1-general-rules) expects annotations '
        'on typed code. Untyped public APIs force every caller to guess.',
        'Suggestion',
        None,
        """# bad
def add(a, b):
  return a + b

# good
def add(a: int, b: int) -> int:
  return a + b""",
      ),
      Rule(
        'Use `X | None` for optional values, not `Optional[X]` unless supporting older checkers that require it.',
        f'[pyguide §3.19.5]({PY}#s3.19.5-none-type) discusses `None`. On '
        '3.12, the union operator is the default idiom.',
        'Suggestion',
        None,
        """# bad
from typing import Optional
def find(name: str) -> Optional[User]:
  ...

# good
def find(name: str) -> User | None:
  ...""",
      ),
      Rule(
        'Prefer builtin generics (`list`, `dict`, `set`, `tuple`) over `typing.List` and friends.',
        'PEP 585 made builtin generics the modern form. `typing.List` is '
        'legacy on 3.12.',
        'Suggestion',
        None,
        """# bad
from typing import Dict, List
def index(rows: List[str]) -> Dict[str, int]:
  ...

# good
def index(rows: list[str]) -> dict[str, int]:
  ...""",
      ),
      Rule(
        'Use `collections.abc` for parameter types (`Sequence`, `Mapping`, `Iterable`).',
        'Accepting abstract collections lets callers pass tuples, lists, and '
        'custom sequences without over-constraining.',
        'Suggestion',
        None,
        """# bad
def sum_lengths(items: list[str]) -> int:
  return sum(len(i) for i in items)

# good
from collections.abc import Sequence

def sum_lengths(items: Sequence[str]) -> int:
  return sum(len(i) for i in items)""",
      ),
      Rule(
        'Prefer `TypeAlias` / PEP 695 `type` aliases for repeated complex types.',
        f'[pyguide §3.19.6]({PY}#s3.19.6-type-aliases) encourages aliases. '
        'On 3.12, `type UserId = str` is valid and readable.',
        'Suggestion',
        None,
        """# bad
def get(user_id: str) -> dict[str, list[dict[str, str]]]:
  ...

# good
type JsonObject = dict[str, object]

def get(user_id: str) -> JsonObject:
  ...""",
      ),
      Rule(
        'Do not use stringified annotations unless required for a forward reference the checker cannot resolve.',
        f'[pyguide §3.19.3]({PY}#s3.19.3-forward-declarations) covers '
        'forward refs. Prefer defining types in an order that avoids quotes.',
        'Suggestion',
        None,
        """# bad
def bind(node: 'Node') -> None:
  ...

# good
class Node:
  def bind(self, node: Node) -> None:
    ...""",
      ),
      Rule(
        'Never write `# type: ignore` without an error code and a reason.',
        f'[pyguide §3.19.7]({PY}#s3.19.7-ignoring-types) requires scoped '
        'ignores. Blanket ignores hide real bugs.',
        'Suggestion',
        None,
        """# bad
reveal = legacy()  # type: ignore

# good
reveal = legacy()  # type: ignore[no-untyped-call]  # vendor stub missing""",
      ),
      Rule(
        'Annotate class attributes that form the public state.',
        'Class-level annotations document invariants and feed dataclasses / '
        'Pydantic / SQLAlchemy mapping.',
        'Suggestion',
        None,
        """# bad
class Counter:
  def __init__(self) -> None:
    self.value = 0

# good
class Counter:
  value: int

  def __init__(self) -> None:
    self.value = 0""",
      ),
      Rule(
        'Use `object` for "any object" and `Any` only at true trust boundaries.',
        '`Any` disables checking. Prefer `object` plus narrowing, or a Protocol.',
        'Suggestion',
        None,
        """# bad
from typing import Any
def dump(data: Any) -> str:
  return str(data)

# good
def dump(data: object) -> str:
  return str(data)""",
      ),
      Rule(
        'Prefer `TypedDict` or a Pydantic model over `dict[str, Any]` for structured records.',
        'Untyped dicts lose keys and value shapes. Structured types catch '
        'renames.',
        'Suggestion',
        None,
        """# bad
def handle(payload: dict[str, Any]) -> None:
  print(payload['userId'])

# good
class Payload(TypedDict):
  user_id: str

def handle(payload: Payload) -> None:
  print(payload['user_id'])""",
      ),
      Rule(
        'Keep return types precise; do not return `Any` from helpers to silence the checker.',
        'Pushing `Any` outward infects callers. Fix the helper instead.',
        'Suggestion',
        None,
        """# bad
def parse(raw: str) -> Any:
  return json.loads(raw)

# good
def parse(raw: str) -> JsonObject:
  data = json.loads(raw)
  if not isinstance(data, dict):
    raise TypeError('expected object')
  return data""",
      ),
      Rule(
        'Use `Self` for fluent methods that return the same class.',
        '`Self` keeps subclasses correct without repeating the class name.',
        'Suggestion',
        None,
        """# bad
class Builder:
  def with_name(self, name: str) -> 'Builder':
    self.name = name
    return self

# good
from typing import Self

class Builder:
  def with_name(self, name: str) -> Self:
    self.name = name
    return self""",
      ),
    ),
  )

  write_chapter(
    '07-functions.md',
    'Functions',
    f"""Functions should be small, typed, and free of surprising defaults.
[pyguide §2.12]({PY}#s2.12-default-argument-values),
[§2.10]({PY}#s2.10-lambda-functions), and
[§3.18]({PY}#s3.18-function-length) guide this chapter.""",
    '`E731` (lambda assignment) is **Violation**. Length and default-arg '
    'mutability are **Suggestion**.',
    _rules(
      Rule(
        'Never use mutable default arguments.',
        f'[pyguide §2.12]({PY}#s2.12-default-argument-values) bans mutable '
        'defaults because they are shared across calls.',
        'Suggestion',
        None,
        """# bad
def append_item(item: str, items: list[str] = []) -> list[str]:
  items.append(item)
  return items

# good
def append_item(item: str, items: list[str] | None = None) -> list[str]:
  if items is None:
    items = []
  items.append(item)
  return items""",
      ),
      Rule(
        'Keep functions short enough to read without scrolling mental context.',
        f'[pyguide §3.18]({PY}#s3.18-function-length) pushes for focused '
        'functions. Extract helpers when a function has multiple stages.',
        'Suggestion',
        None,
        """# bad  -  120-line function mixing IO, validation, and formatting
# good  -  validate(), load(), format() called from a thin orchestrator""",
      ),
      Rule(
        'Prefer keyword-only arguments for parameters that are easy to swap by position.',
        'Boolean and option flags at the end should be keyword-only to avoid '
        '`do(True, False)` call sites.',
        'Suggestion',
        None,
        """# bad
def copy(src: Path, dst: Path, overwrite: bool = False) -> None:
  ...

# good
def copy(src: Path, dst: Path, *, overwrite: bool = False) -> None:
  ...""",
      ),
      Rule(
        'Do not assign lambdas to names; use `def`.',
        'Named lambdas lose annotations and produce worse tracebacks. `E731`.',
        'Violation',
        'E731',
        """# bad
square = lambda n: n * n

# good
def square(n: int) -> int:
  return n * n""",
      ),
      Rule(
        'Use early returns to keep the happy path unindented.',
        'Guard clauses beat nested pyramids for readability.',
        'Suggestion',
        None,
        """# bad
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
  process(user)""",
      ),
      Rule(
        'Prefer pure functions for business rules; push IO to the edges.',
        'Pure helpers are trivial to test. FastAPI handlers should orchestrate, '
        'not embed SQL.',
        'Suggestion',
        None,
        """# bad
async def total(order_id: str) -> Decimal:
  order = await db.fetch(order_id)
  return sum(line.price for line in order.lines)

# good
def order_total(lines: Sequence[Line]) -> Decimal:
  return sum((line.price for line in lines), start=Decimal('0'))""",
      ),
      Rule(
        'Do not use `*args` / `**kwargs` to avoid designing a real signature.',
        'Variadic bags hide required parameters and break autocomplete.',
        'Suggestion',
        None,
        """# bad
def create_user(**kwargs: object) -> User:
  return User(**kwargs)

# good
def create_user(*, email: str, name: str) -> User:
  return User(email=email, name=name)""",
      ),
      Rule(
        'Return consistent types; do not return `None` and a value interchangeably without `| None` in the signature.',
        'Inconsistent returns force every caller to guess. Annotate optionality.',
        'Suggestion',
        None,
        """# bad
def find(name: str):
  if not name:
    return None
  return User(name)

# good
def find(name: str) -> User | None:
  if not name:
    return None
  return User(name)""",
      ),
      Rule(
        'Raise exceptions for exceptional failures; do not return magic error codes.',
        f'[pyguide §2.4]({PY}#s2.4-exceptions) prefers exceptions over status '
        'tuples for errors.',
        'Suggestion',
        None,
        """# bad
def load(path: Path) -> tuple[Config | None, str]:
  ...

# good
def load(path: Path) -> Config:
  if not path.exists():
    raise FileNotFoundError(path)
  ...""",
      ),
      Rule(
        'Name boolean arguments carefully and prefer enums when there are more than two modes.',
        '`send(True)` is opaque. An enum or keyword-only flag reads clearly.',
        'Suggestion',
        None,
        """# bad
notify(user, True)

# good
notify(user, channel=Channel.EMAIL)""",
      ),
      Rule(
        'Avoid ternary expressions for multi-statement logic; keep them for simple value selection.',
        f'[pyguide §2.11]({PY}#s2.11-conditional-expressions) allows '
        'conditionals when they stay readable.',
        'Suggestion',
        None,
        """# bad
value = do_a() if ready else do_b() if other else do_c()

# good
if ready:
  value = do_a()
elif other:
  value = do_b()
else:
  value = do_c()""",
      ),
      Rule(
        'Document side effects in the docstring or name (`save_`, `send_`, `write_`).',
        'Readers assume functions are side-effect light unless the name says '
        'otherwise.',
        'Suggestion',
        None,
        """# bad
def user(email: str) -> User:
  db.insert(...)
  return User(email)

# good
def create_user(email: str) -> User:
  db.insert(...)
  return User(email)""",
      ),
    ),
  )

  write_chapter(
    '08-classes.md',
    'Classes',
    f"""Classes own invariants. Prefer simple data carriers
([Chapter 9](09-dataclasses.md)) and functions when you do not need
encapsulation. [pyguide §2.13]({PY}#s2.13-properties) and
[§3.15]({PY}#s3.15-access-control) inform access patterns.""",
    'Class design rules are **Suggestion** under the shipped select.',
    _rules(
      Rule(
        'Do not write a class when a function or module-level helpers suffice.',
        'Classes for namespacing alone add ceremony. Modules are namespaces.',
        'Suggestion',
        None,
        """# bad
class MathUtils:
  @staticmethod
  def add(a: int, b: int) -> int:
    return a + b

# good
def add(a: int, b: int) -> int:
  return a + b""",
      ),
      Rule(
        'Make illegal states unrepresentable: validate in `__init__` / `__post_init__`.',
        'Failing at construction beats failing deep in a call stack.',
        'Suggestion',
        None,
        """# bad
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
    self.end = end""",
      ),
      Rule(
        'Prefer composition over deep inheritance.',
        'Deep hierarchies couple unrelated changes. Compose collaborators.',
        'Suggestion',
        None,
        """# bad
class AdminUser(AuthenticatedUser(LoggedUser(User))):
  ...

# good
class UserService:
  def __init__(self, auth: AuthClient, audit: AuditLog) -> None:
    self._auth = auth
    self._audit = audit""",
      ),
      Rule(
        'Use `@property` for derived values, not for hiding expensive IO.',
        f'[pyguide §2.13]({PY}#s2.13-properties) wants properties that are '
        'cheap and unsurprising. IO belongs in methods.',
        'Suggestion',
        None,
        """# bad
@property
def report(self) -> Report:
  return self._client.fetch_report()  # hidden network call

# good
def load_report(self) -> Report:
  return self._client.fetch_report()""",
      ),
      Rule(
        'Keep instance state private with a leading underscore and expose a narrow API.',
        f'[pyguide §3.15]({PY}#s3.15-access-control) prefers accessors only '
        'when they add value.',
        'Suggestion',
        None,
        """# bad
class Account:
  def __init__(self) -> None:
    self.balance = 0

# good
class Account:
  def __init__(self) -> None:
    self._balance = 0

  @property
  def balance(self) -> int:
    return self._balance""",
      ),
      Rule(
        'Implement `__repr__` for every nontrivial domain object.',
        '`repr` is for developers. Include identifying fields; omit secrets.',
        'Suggestion',
        None,
        """# bad
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
    return f'User(user_id={self.user_id!r})'""",
      ),
      Rule(
        'Do not override `__eq__` without `__hash__` (or set `__hash__ = None`).',
        'Inconsistent equality/hashing breaks set/dict membership.',
        'Suggestion',
        None,
        """# bad
class Point:
  def __eq__(self, other: object) -> bool:
    ...

# good
@dataclass(frozen=True)
class Point:
  x: int
  y: int""",
      ),
      Rule(
        'Prefer `@classmethod` factories over ambiguous multi-purpose constructors.',
        'Named factories document provenance (`from_json`, `from_row`).',
        'Suggestion',
        None,
        """# bad
User(None, None, raw_json)  # magic overload

# good
User.from_json(raw_json)""",
      ),
      Rule(
        'Avoid deep nesting of classes; nest only when the inner type is meaningless alone.',
        f'[pyguide §2.6]({PY}#s2.6-nested) discourages '
        'unnecessary nesting.',
        'Suggestion',
        None,
        """# bad  -  nested helper class used elsewhere
# good  -  top-level private class `_Node` or a module-level helper""",
      ),
      Rule(
        'Do not store mutable class attributes as shared defaults.',
        'Class-attribute lists/dicts are shared across instances.',
        'Suggestion',
        None,
        """# bad
class Team:
  members: list[str] = []

# good
class Team:
  def __init__(self) -> None:
    self.members: list[str] = []""",
      ),
      Rule(
        'Prefer protocols / ABCs for shared behavior across unrelated classes.',
        'See [Chapter 10](10-protocols-and-abcs.md). Nominal inheritance is '
        'not required for duck typing with type checkers.',
        'Suggestion',
        None,
        """# bad
class FileLike(ABC):
  ...

# good  -  when structural typing is enough
class SupportsRead(Protocol):
  def read(self, n: int = -1) -> str: ...""",
      ),
      Rule(
        'Keep `__init__` for assignment and validation; do not launch threads or network calls there.',
        'Constructors that do IO make testing and lifetimes painful. Use an '
        'explicit `open()` / async context manager.',
        'Suggestion',
        None,
        """# bad
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
    self._session = httpx.Client(base_url=self._url)""",
      ),
    ),
  )

  write_chapter(
    '09-dataclasses.md',
    'Dataclasses',
    """`dataclasses` are the stdlib tool for value carriers. Prefer them over
hand-written `__init__`/`__repr__`/`__eq__` for plain data. For API schemas
and validation, prefer Pydantic models ([Chapter 34](34-fastapi-request-response-models.md)).""",
    'Dataclass design is **Suggestion** under the shipped select.',
    _rules(
      Rule(
        'Use `@dataclass` for plain data aggregates with little behavior.',
        'Hand-rolled boilerplate drifts. Dataclasses generate the boring parts.',
        'Suggestion',
        None,
        """# bad
class Point:
  def __init__(self, x: int, y: int) -> None:
    self.x = x
    self.y = y
  # eq/repr omitted or wrong

# good
@dataclass(frozen=True)
class Point:
  x: int
  y: int""",
      ),
      Rule(
        'Prefer `frozen=True` for value objects used as dict keys or shared widely.',
        'Frozen instances catch accidental mutation and enable safe hashing.',
        'Suggestion',
        None,
        """# bad
@dataclass
class UserId:
  value: str

# good
@dataclass(frozen=True)
class UserId:
  value: str""",
      ),
      Rule(
        'Use `field(default_factory=...)` for mutable defaults.',
        'The same shared-mutable trap as function defaults applies.',
        'Suggestion',
        None,
        """# bad
@dataclass
class Basket:
  items: list[str] = []

# good
@dataclass
class Basket:
  items: list[str] = field(default_factory=list)""",
      ),
      Rule(
        'Put fields without defaults before fields with defaults.',
        'Dataclass field ordering rules match Python signature rules.',
        'Suggestion',
        None,
        """# bad
@dataclass
class User:
  role: str = 'user'
  email: str

# good
@dataclass
class User:
  email: str
  role: str = 'user'""",
      ),
      Rule(
        'Use `__post_init__` for normalization and invariant checks.',
        'Keep derived fields and validation next to construction.',
        'Suggestion',
        None,
        """# bad  -  validate at every call site
# good
@dataclass(frozen=True)
class Email:
  value: str

  def __post_init__(self) -> None:
    if '@' not in self.value:
      raise ValueError('invalid email')""",
      ),
      Rule(
        'Do not use dataclasses as ORM entities or Pydantic stand-ins when those frameworks need their own base classes.',
        'SQLAlchemy / Pydantic own persistence and validation semantics. '
        'Dataclasses are for in-process values.',
        'Suggestion',
        None,
        """# bad  -  mixing concerns
@dataclass
class UserRow:
  id: str
  email: str  # also used as request body somehow

# good  -  separate types for DB, domain, and API""",
      ),
      Rule(
        'Mark non-init / derived fields with `field(init=False)` explicitly.',
        'Hidden computed fields confuse construction call sites.',
        'Suggestion',
        None,
        """# bad
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
    self.area = self.width * self.height""",
      ),
      Rule(
        'Use `slots=True` on 3.10+ when instances are numerous and the layout is fixed.',
        'Slots cut memory and catch accidental attribute assignment.',
        'Suggestion',
        None,
        """# bad  -  millions of open instances with __dict__
@dataclass
class Tick:
  ts: float
  price: float

# good
@dataclass(slots=True, frozen=True)
class Tick:
  ts: float
  price: float""",
      ),
      Rule(
        'Prefer `kw_only=True` when constructors gain many optional fields.',
        'Keyword-only dataclasses prevent positional pile-ups.',
        'Suggestion',
        None,
        """# bad
User('a@x.com', 'Ada', 'admin', True)

# good
@dataclass(kw_only=True)
class User:
  email: str
  name: str
  role: str = 'user'
  active: bool = True""",
      ),
      Rule(
        'Do not mutate frozen dataclass internals via `object.__setattr__` outside `__post_init__`.',
        'Escaping frozen is a footgun. If you need mutation, do not freeze.',
        'Suggestion',
        None,
        """# bad  -  random helper mutates frozen instance
object.__setattr__(user, 'email', new_email)

# good  -  return a replace()d copy
user = replace(user, email=new_email)""",
      ),
      Rule(
        'Use `replace()` for updates to frozen instances.',
        '`dataclasses.replace` keeps value semantics clear.',
        'Suggestion',
        None,
        """# bad
user.email = 'x'  # fails when frozen

# good
user = replace(user, email='x@example.com')""",
      ),
      Rule(
        'Keep methods on dataclasses thin; move workflows to services/functions.',
        'Fat dataclasses become hidden services. Behavior that needs '
        'collaborators belongs elsewhere.',
        'Suggestion',
        None,
        """# bad
@dataclass
class Order:
  def charge(self, gateway: Gateway) -> None:
    gateway.charge(self.total)

# good
def charge_order(order: Order, gateway: Gateway) -> None:
  gateway.charge(order.total)""",
      ),
    ),
  )

  write_chapter(
    '10-protocols-and-abcs.md',
    'Protocols & ABCs',
    """Structural typing with `typing.Protocol` is the preferred way to express
"needs a `.read()`" without forcing inheritance. ABCs remain useful when you
need virtual subclasses or shared concrete helpers.""",
    'Protocol design is **Suggestion** under the shipped select.',
    _rules(
      Rule(
        'Prefer `Protocol` for consumer-defined interfaces.',
        'Callers should define the shape they need. Implementers should not '
        'be forced to inherit a library base class.',
        'Suggestion',
        None,
        """# bad
class Repository(ABC):
  @abstractmethod
  def get(self, key: str) -> Order: ...

# good
class OrderRepository(Protocol):
  def get(self, key: str) -> Order: ...""",
      ),
      Rule(
        'Mark runtime-checkable protocols only when you truly need `isinstance`.',
        '`@runtime_checkable` is limited (presence of attributes, not types). '
        'Prefer typing-time checks.',
        'Suggestion',
        None,
        """# bad  -  isinstance everywhere
@runtime_checkable
class SupportsClose(Protocol):
  def close(self) -> None: ...

# good  -  annotate parameters; skip runtime isinstance""",
      ),
      Rule(
        'Keep protocols small (ISP). Split read/write surfaces.',
        'Fat protocols force fake methods on implementers.',
        'Suggestion',
        None,
        """# bad
class Store(Protocol):
  def get(self, key: str) -> bytes: ...
  def put(self, key: str, value: bytes) -> None: ...
  def list_keys(self) -> list[str]: ...
  def migrate(self) -> None: ...

# good  -  SupportsGet / SupportsPut separately""",
      ),
      Rule(
        'Use ABCs when you need shared concrete code or `@abstractmethod` enforcement at runtime.',
        'ABCs help framework authors; Protocols help application authors.',
        'Suggestion',
        None,
        """# bad  -  ABC for a one-method callback
# good  -  Protocol for callbacks; ABC for framework base with helpers""",
      ),
      Rule(
        'Do not mix Protocol and concrete inheritance casually.',
        'A class can implement a Protocol structurally without listing it. '
        'Explicit subclassing of Protocol is rarely needed.',
        'Suggestion',
        None,
        """# bad
class FileReader(SupportsRead, BaseModel):
  ...

# good  -  structural match without inheriting Protocol""",
      ),
      Rule(
        'Name protocols `SupportsX` / `XLike` / noun interfaces that read as capabilities.',
        'Clear names document intent at annotation sites.',
        'Suggestion',
        None,
        """# bad
class IReader(Protocol):
  ...

# good
class SupportsRead(Protocol):
  def read(self, n: int = -1) -> str: ...""",
      ),
      Rule(
        'Annotate FastAPI dependencies with Protocols when tests need fakes.',
        'Protocols make `Annotated[OrdersRepo, Depends(...)]` easy to fake.',
        'Suggestion',
        None,
        """# bad  -  depend on a concrete SQLAlchemy repo type everywhere
# good
class OrdersRepo(Protocol):
  async def get(self, order_id: str) -> Order: ...""",
      ),
      Rule(
        'Prefer `collections.abc` protocols (`Mapping`, `Sequence`) over custom ones when they fit.',
        'Stdlib ABCs are understood by every type checker.',
        'Suggestion',
        None,
        """# bad
class StringList(Protocol):
  def __iter__(self) -> Iterator[str]: ...

# good
from collections.abc import Sequence
def join(parts: Sequence[str]) -> str:
  return ','.join(parts)""",
      ),
      Rule(
        'Document module-level protocols next to the functions that consume them.',
        'Orphan protocol files become dumping grounds. Keep them near use.',
        'Suggestion',
        None,
        """# bad  -  app/types/protocols.py with 40 unrelated protocols
# good  -  protocols defined above the service that needs them""",
      ),
      Rule(
        'Avoid empty marker protocols used only for branding.',
        'If a Protocol has no members, it is not an interface.',
        'Suggestion',
        None,
        """# bad
class Entity(Protocol):
  ...

# good  -  give it the members callers need""",
      ),
      Rule(
        'Use `TypeVar` bounds with Protocols for generic callables.',
        'Bounded TypeVars express "any T that supports X".',
        'Suggestion',
        None,
        """# bad  -  Any
def close_all(resources: list[Any]) -> None:
  for r in resources:
    r.close()

# good
class SupportsClose(Protocol):
  def close(self) -> None: ...

def close_all(resources: list[SupportsClose]) -> None:
  for r in resources:
    r.close()""",
      ),
      Rule(
        'Do not invent home-grown plugin registries when a Protocol + explicit wiring will do.',
        'Magic entry-point registries obscure the running graph. Wire plugins '
        'in `create_app()`.',
        'Suggestion',
        None,
        """# bad  -  import side-effect registration
# good  -  pass a list[Plugin] into create_app(plugins=[...])""",
      ),
    ),
  )
