"""Chapters 1-10 for best-practice-python."""

from __future__ import annotations

from scripts.python_skill._render import Rule, write_chapter

PY = 'https://google.github.io/styleguide/pyguide.html'


def build() -> None:
  write_chapter(
    '01-formatting-and-tooling.md',
    'Formatting & Tooling',
    f"""Python's formatting debate is settled by a tool, not a committee.
[`ruff format`](https://docs.astral.sh/ruff/formatter/) owns layout the same
way `gofmt` owns Go, `google-java-format` owns Java, and `ktlint` owns Kotlin.
This chapter documents that chain and the house overrides that differ from
[Google Python Style Guide §3]({PY}#s3-python-style-rules).

**House overrides (deliberate):**

| Setting | This skill | Upstream |
|---|---|---|
| Indent | **2 spaces** (`indent-width = 2`) | [pyguide §3.4]({PY}#s3.4-indentation) and PEP 8 use 4 |
| Quotes | **single** (`quote-style = 'single'`) | Ruff / Black default to double |
| Line length | **88** | [pyguide §3.2]({PY}#s3.2-line-length) prefers 80 |
| Language floor | **Python 3.12** (`target-version = 'py312'`) |  -  |

These are not what Google says. They are project law. Every sample in every
chapter uses 2-space indent and single quotes. No later chapter re-litigates
whitespace, quote style, or line wrapping.

Formatting is not lint. `ruff format` rewrites layout; `ruff check` with the
shipped `select = ['E4', 'E7', 'E9', 'F']` catches a small set of correctness
and import issues. Semantic pyguide rules that need broader Ruff families
(`D`, `N`, `UP`, `B`, …) are labeled **Suggestion** until the project expands
`select`. See [Chapter 39](39-ruff-configuration.md).""",
    'Layout is enforced by `ruff format`. The few lint rules below that map to '
    'enabled codes (`E4`/`E7`/`E9`/`F`) are **Violation**; everything else is '
    '**Suggestion**.',
    [
      Rule(
        'Run `ruff format` before every commit and `ruff check` in CI.',
        'One canonical layout kills whitespace diffs and keeps `git blame` '
        'meaningful. A formatting failure is the cheapest CI failure. Pair '
        'the write path (`ruff format`) with the read-only gate '
        '(`ruff check`).',
        'Violation',
        'ruff format',
        """# bad  -  hand-laid-out; ruff format rewrites almost every line
def convert(amount:Decimal,from_c:str,to_c:str)->Decimal:
  if amount<0:raise ValueError("negative")
  return amount*rate_for(from_c,to_c)

# good  -  exactly what ruff format emits under this repo's ruff.toml
def convert(amount: Decimal, from_c: str, to_c: str) -> Decimal:
  if amount < 0:
    raise ValueError('negative')
  return amount * rate_for(from_c, to_c)""",
      ),
      Rule(
        'Indent with two spaces. Never tabs, never four.',
        f'This is a house override of [pyguide §3.4]({PY}#s3.4-indentation) '
        'and PEP 8. The shipped `ruff.toml` sets `indent-width = 2`. Mixing '
        '4-space Python into this repo produces a whole-file diff the first '
        'time anyone runs the formatter.',
        'Violation',
        'ruff format',
        """# bad  -  four-space blocks (PEP 8 / pyguide default)
def place(order: Order) -> Receipt:
    total = order.subtotal + order.tax
    return Receipt(total=total)

# good  -  two spaces, matching indent-width = 2
def place(order: Order) -> Receipt:
  total = order.subtotal + order.tax
  return Receipt(total=total)""",
      ),
      Rule(
        "Use single quotes for string literals. Use double only when the string contains a single quote and escaping would hurt readability.",
        "The shipped `ruff.toml` sets `quote-style = 'single'`. Consistency "
        'matters more than the quote character; the formatter picks one.',
        'Violation',
        'ruff format',
        """# bad  -  double quotes everywhere under a single-quote house style
name = "Ada"
msg = "hello"

# good
name = 'Ada'
msg = "Ada's laptop"  # double is fine when it avoids escaping""",
      ),
      Rule(
        'Keep lines within 88 columns unless a long URL or similar undivisible token forces a longer line.',
        f'[pyguide §3.2]({PY}#s3.2-line-length) prefers 80; this skill uses '
        'Black/Ruff\'s 88. Do not hand-wrap for aesthetics once `ruff format` '
        'has chosen breaks.',
        'Violation',
        'ruff format',
        """# bad  -  arbitrary mid-expression wrapping that fights the formatter
total = (
  price
  +
  tax
)

# good  -  let ruff format choose breaks at 88
total = price + tax + shipping""",
      ),
      Rule(
        'Put one import per line. Do not combine imports with commas.',
        f'[pyguide §3.13]({PY}#s3.13-imports-formatting) and PEP 8 require '
        'separate lines so diffs and conflict resolution stay readable.',
        'Violation',
        'E401',
        """# bad
import os, sys

# good
import os
import sys""",
      ),
      Rule(
        'Never compare to `None` with `==` or `!=`. Use `is` / `is not`.',
        'Identity is the correct test for `None`. `==` can be overloaded and '
        'hide bugs. Ruff `E711` catches this.',
        'Violation',
        'E711',
        """# bad
if value == None:
  return default

# good
if value is None:
  return default""",
      ),
      Rule(
        'Never compare booleans with `== True` or `== False`.',
        'Boolean comparisons with equality are noise and invite mistakes with '
        'truthy non-bools. Use the value directly (or `not`). `E712`.',
        'Violation',
        'E712',
        """# bad
if ready == True:
  start()

# good
if ready:
  start()""",
      ),
      Rule(
        'Do not use a bare `except:`. Catch specific exceptions.',
        'Bare `except` swallows `KeyboardInterrupt` and `SystemExit`. '
        f'[pyguide §2.4]({PY}#s2.4-exceptions) rejects it. `E722`.',
        'Violation',
        'E722',
        """# bad
try:
  parse(blob)
except:
  return None

# good
try:
  parse(blob)
except ValueError:
  return None""",
      ),
      Rule(
        'Do not assign a `lambda` to a name. Use `def`.',
        'Named lambdas defeat the point of both `def` (a real name and '
        'traceback) and `lambda` (an inline expression). `E731`.',
        'Violation',
        'E731',
        """# bad
add = lambda x, y: x + y

# good
def add(x: int, y: int) -> int:
  return x + y""",
      ),
      Rule(
        'Remove unused imports. Do not leave import residue after refactors.',
        'Unused imports slow reviews and confuse readers about real '
        'dependencies. `F401`.',
        'Violation',
        'F401',
        """# bad
import json  # never used
from pathlib import Path

def root() -> Path:
  return Path.cwd()

# good
from pathlib import Path

def root() -> Path:
  return Path.cwd()""",
      ),
      Rule(
        'Do not leave unused variables. Prefix intentionally unused names with `_`.',
        'Dead bindings hide incomplete refactors. The shipped '
        '`dummy-variable-rgx` allows underscore-prefixed names. `F841`.',
        'Violation',
        'F841',
        """# bad
def handle(event: Event) -> None:
  unused = event.payload
  dispatch(event.kind)

# good
def handle(event: Event) -> None:
  _payload = event.payload  # kept for a future branch; underscore-ok
  dispatch(event.kind)""",
      ),
      Rule(
        'Never put multiple statements on one line with semicolons.',
        f'[pyguide §3.1]({PY}#s3.1-semicolons) bans semicolons as statement '
        'separators. `E702` / `E703`.',
        'Violation',
        'E702',
        """# bad
x = 1; y = 2

# good
x = 1
y = 2""",
      ),
      Rule(
        'Drive formatting and lint through `uv run` (or the project venv), not a random global Ruff.',
        'Local Ruff versions drift. Pin Ruff in the project and invoke it '
        'through `uv` so CI and laptops agree on rule codes.',
        'Suggestion',
        None,
        """# bad  -  whatever `ruff` happens to be on PATH
ruff format .
ruff check .

# good  -  project-pinned tool
uv run ruff format .
uv run ruff check .""",
      ),
      Rule(
        'Do not disable Ruff with blanket `# noqa` or file-level ignores without a scoped rule code and a reason.',
        'Unscoped suppressions rot. Prefer fixing the code; when you must '
        'suppress, name the rule (`# noqa: F401`) and explain why.',
        'Suggestion',
        None,
        """# bad
# ruff: noqa
from .legacy import *  # noqa

# good
from .legacy import helper  # noqa: F401  # re-exported for compat""",
      ),
      Rule(
        'Treat the formatter as law: never fight it with manual alignment or trailing-comma games.',
        '`skip-magic-trailing-comma = false` means a trailing comma is a '
        'signal you want a multi-line form. Use that deliberately; do not '
        'hand-align columns the formatter will smash.',
        'Suggestion',
        None,
        """# bad  -  columnar alignment the formatter will destroy
user = User(id=1,   name='Ada',  role='admin')
guest = User(id=2,  name='Bob',  role='user')

# good  -  formatter-stable
user = User(id=1, name='Ada', role='admin')
guest = User(id=2, name='Bob', role='user')""",
      ),
    ],
  )

  write_chapter(
    '02-source-files-and-layout.md',
    'Source Files & Layout',
    f"""A Python module is a file; a package is a directory with imports that
define a public surface. This chapter covers file naming, `if __name__ ==
'__main__'`, shebangs, and the shape of a modern `src/` layout.
[pyguide §3.16.3]({PY}#s3.16.3-file-naming) and [§3.17]({PY}#s3.17-main)
are the primary upstream anchors. Project layout with `uv` is
[Chapter 41](41-project-layout-and-uv.md).""",
    'File naming and `__main__` guards are **Suggestion** under the shipped '
    'minimal Ruff select. Import hygiene that maps to `E4`/`F` is '
    '**Violation**.',
    [
      Rule(
        'Name modules `lowercase_with_underscores.py`. Never use CamelCase filenames.',
        f'[pyguide §3.16.3]({PY}#s3.16.3-file-naming) requires short, '
        'all-lowercase names with underscores. CamelCase filenames break '
        'imports on case-sensitive filesystems and look like class names.',
        'Suggestion',
        None,
        """# bad  -  file: OrderService.py
class OrderService:
  ...

# good  -  file: order_service.py
class OrderService:
  ...""",
      ),
      Rule(
        'Keep modules focused. Prefer more small modules over one thousand-line kitchen sink.',
        'A module should have one job a reader can name in a sentence. God '
        'modules destroy navigation and force circular imports.',
        'Suggestion',
        None,
        """# bad  -  billing.py also owns email, CSV export, and CLI parsing
# good  -  billing/charges.py, billing/invoices.py, billing/export.py""",
      ),
      Rule(
        'Put library code under `src/<package>/` (or a clear package root), not at the repo root.',
        'A `src/` layout stops accidental imports of the working tree and '
        'matches what `uv`/`hatch` scaffold. Tests and scripts stay outside.',
        'Suggestion',
        None,
        """# bad
./order_service.py
./test_order_service.py

# good
./src/orders/service.py
./tests/test_service.py""",
      ),
      Rule(
        "Guard script entry points with `if __name__ == '__main__':`.",
        f'[pyguide §3.17]({PY}#s3.17-main) requires this so importing the '
        'module for tests does not run side effects.',
        'Suggestion',
        None,
        """# bad
import sys
run(sys.argv)  # runs on import

# good
def main() -> None:
  run(sys.argv)


if __name__ == '__main__':
  main()""",
      ),
      Rule(
        'Keep `main()` thin: parse args, configure logging, call library code.',
        'Business logic in `__main__` blocks is untestable. Push work into '
        'importable functions.',
        'Suggestion',
        None,
        """# bad
if __name__ == '__main__':
  data = Path('in.csv').read_text()
  # 80 lines of transform...

# good
def main() -> None:
  args = parse_args()
  transform(Path(args.input), Path(args.output))


if __name__ == '__main__':
  main()""",
      ),
      Rule(
        'Omit shebang lines from library modules. Add `#!/usr/bin/env python3` only on executable scripts.',
        f'[pyguide §3.7]({PY}#s3.7-shebang-line) limits shebangs to files '
        'meant to be executed directly.',
        'Suggestion',
        None,
        """# bad  -  library module
#!/usr/bin/env python3
def add(a: int, b: int) -> int:
  return a + b

# good  -  no shebang in libraries; scripts may have one
def add(a: int, b: int) -> int:
  return a + b""",
      ),
      Rule(
        'Prefer explicit package exports via `__all__` when a package has a public API.',
        '`__all__` documents the supported surface and keeps `from pkg import *` '
        '(when unavoidable) honest. Internal helpers stay underscore-prefixed.',
        'Suggestion',
        None,
        """# bad  -  every name is accidentally public
from .service import OrderService, _cache_key

# good
from .service import OrderService

__all__ = ['OrderService']""",
      ),
      Rule(
        'Do not use star imports in application code.',
        f'[pyguide §2.2]({PY}#s2.2-imports) rejects `from module import *` '
        'because it obscures provenance. `F403` flags star import usage '
        'that prevents static analysis.',
        'Violation',
        'F403',
        """# bad
from orders.models import *

# good
from orders.models import Order, LineItem""",
      ),
      Rule(
        'Keep tests in a top-level `tests/` tree that mirrors the package, not mixed into production modules.',
        'Mixed `test_*.py` beside production code blurs packaging and '
        'encourages importing private test helpers from prod.',
        'Suggestion',
        None,
        """# bad
src/orders/service.py
src/orders/test_service.py

# good
src/orders/service.py
tests/orders/test_service.py""",
      ),
      Rule(
        'Avoid circular imports by depending on interfaces at the edges and pushing shared types down.',
        f'[pyguide §3.19.14]({PY}#s3.19.14-circular-dependencies) discusses '
        'typing-time cycles; runtime cycles are worse. Fix structure rather '
        'than importing inside functions as a habit.',
        'Suggestion',
        None,
        """# bad  -  a.py imports b.py which imports a.py at module level
# good  -  extract shared types to types.py both can import""",
      ),
      Rule(
        'Do not rely on import side effects for registration. Prefer explicit app wiring.',
        'Import-time registration makes test collection and tool import '
        'graphs fragile. Wire routers, plugins, and tasks in an explicit '
        '`create_app()` (FastAPI: chapter 32).',
        'Suggestion',
        None,
        """# bad  -  module import mutates global registry
from . import handlers  # noqa: F401  # side-effect import

# good
def create_app() -> FastAPI:
  app = FastAPI()
  app.include_router(handlers.router)
  return app""",
      ),
      Rule(
        'Keep `__init__.py` thin. Re-export sparingly; do not hide a whole package behind a mega-import.',
        'Fat `__init__.py` files create import cycles and slow cold start. '
        'Re-export the stable façade only.',
        'Suggestion',
        None,
        """# bad  -  __init__.py imports every submodule eagerly
from .a import *
from .b import *
from .c import *

# good  -  re-export the public façade only
from .service import OrderService

__all__ = ['OrderService']""",
      ),
      Rule(
        'Name test modules `test_<unit>.py` and keep them import-light at collection time.',
        'Heavy module-level I/O in test files slows every pytest run. Import '
        'expensive fixtures inside fixtures or tests.',
        'Suggestion',
        None,
        """# bad  -  tests/test_db.py
conn = connect_production()  # runs at collection

# good
@pytest.fixture
def conn():
  return connect_test()""",
      ),
    ],
  )

  write_chapter(
    '03-naming.md',
    'Naming',
    f"""Names are the primary documentation of a Python codebase.
[pyguide §3.16]({PY}#s3.16-naming) and [§3.16.2]({PY}#s3.16.2-naming-conventions)
are normative. This skill uses those conventions unchanged; only indentation
and quotes are house overrides.""",
    'Naming is almost entirely **Suggestion** under the shipped Ruff select '
    '(no `N` / pep8-naming). Ambiguous names caught by `E741` are '
    '**Violation**.',
    [
      Rule(
        'Use `snake_case` for functions, methods, modules, and variables.',
        f'[pyguide §3.16.2]({PY}#s3.16.2-naming-conventions) standardizes '
        'snake_case for functions and vars so readers can parse roles at a glance.',
        'Suggestion',
        None,
        """# bad
def GetOrder(OrderID: str) -> Order:
  ...

# good
def get_order(order_id: str) -> Order:
  ...""",
      ),
      Rule(
        'Use `CapWords` (PascalCase) for classes and exceptions.',
        'Class names that look like functions confuse instantiation sites and '
        'autocompletion.',
        'Suggestion',
        None,
        """# bad
class order_service:
  ...

# good
class OrderService:
  ...""",
      ),
      Rule(
        'Use `UPPER_SNAKE_CASE` for module-level constants.',
        'Constants should read as fixed. Mixing styles makes mutation harder to spot.',
        'Suggestion',
        None,
        """# bad
maxRetries = 3
Default_Timeout = 30

# good
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30""",
      ),
      Rule(
        'Prefix "internal use" helpers with a single leading underscore.',
        'A single underscore is the community signal for non-public API. It '
        'is not enforced by the language, but it guides `__all__` and reviews.',
        'Suggestion',
        None,
        """# bad
def normalize_internal(name: str) -> str:
  ...

# good
def _normalize(name: str) -> str:
  ...""",
      ),
      Rule(
        'Never use `l`, `O`, or `I` as names.',
        f'[pyguide §3.16.1]({PY}#s3.16.1-names-to-avoid) bans them because '
        'they are indistinguishable from `1` and `0` in many fonts. `E741`.',
        'Violation',
        'E741',
        """# bad
l = [1, 2, 3]
O = 0

# good
lengths = [1, 2, 3]
zero = 0""",
      ),
      Rule(
        'Name booleans as predicates: `is_`, `has_`, `can_`, `should_`.',
        '`flag` and `status` force readers to chase definitions. Predicate '
        'names document the true branch.',
        'Suggestion',
        None,
        """# bad
flag = user.role == 'admin'

# good
is_admin = user.role == 'admin'""",
      ),
      Rule(
        'Avoid redundant type suffixes in names (`user_list`, `name_string`) unless the type is the point.',
        'With annotations, `users: list[User]` is clearer than `user_list`. '
        'Reserve suffixes for disambiguation.',
        'Suggestion',
        None,
        """# bad
user_list: list[User] = load()

# good
users: list[User] = load()""",
      ),
      Rule(
        'Name exceptions `SomethingError` (or a narrow domain suffix), never bare `Error` in app code.',
        'Bare `Error` shadows builtins and reads as unfinished design.',
        'Suggestion',
        None,
        """# bad
class NotFound(Exception):
  ...

# good
class OrderNotFoundError(Exception):
  ...""",
      ),
      Rule(
        'Prefer full words over cryptic abbreviations, except widely known ones (`id`, `http`, `url`).',
        'Abbreviations tax every new reader. Consistency with domain language '
        'beats clever shortness.',
        'Suggestion',
        None,
        """# bad
def calc_ttl_for_usr(usr_id: str) -> int:
  ...

# good
def calculate_ttl_for_user(user_id: str) -> int:
  ...""",
      ),
      Rule(
        'Do not shadow builtins (`id`, `type`, `list`, `dict`, `str`, `input`).',
        'Shadowing builtins breaks later code in the same scope and confuses '
        'readers who expect the builtin.',
        'Suggestion',
        None,
        """# bad
def save(id: str, type: str) -> None:
  ...

# good
def save(entity_id: str, entity_type: str) -> None:
  ...""",
      ),
      Rule(
        'Name FastAPI path operation functions after the action, not the HTTP verb alone.',
        '`get` / `post` collide across routers. `get_order` / `create_order` '
        'show up clearly in OpenAPI and traces.',
        'Suggestion',
        None,
        """# bad
@router.get('/orders/{order_id}')
async def get(order_id: str) -> Order:
  ...

# good
@router.get('/orders/{order_id}')
async def get_order(order_id: str) -> Order:
  ...""",
      ),
      Rule(
        'Keep acronyms consistent: prefer `HttpClient` / `http_client` over mixed `HTTPClient` / `HttpURL`.',
        'Python communities usually treat short acronyms as CapWords words '
        '(`Http`, `Url`). Pick one scheme and stick to it.',
        'Suggestion',
        None,
        """# bad
class HTTPURLParser:
  ...

# good
class HttpUrlParser:
  ...""",
      ),
      Rule(
        'Use plural nouns for collections and singular nouns for single values.',
        'Agreement between name and shape prevents off-by-one thinking at call sites.',
        'Suggestion',
        None,
        """# bad
order: list[Order] = load_orders()

# good
orders: list[Order] = load_orders()
order: Order = orders[0]""",
      ),
    ],
  )

  write_chapter(
    '04-docstrings.md',
    'Docstrings',
    f"""Google-style docstrings are the documentation format for this skill.
[pyguide §3.8]({PY}#s3.8-comments-and-docstrings) and
[§3.8.1]({PY}#s3.8.1-comments-in-doc-strings) are normative. Use them for
public modules, classes, and functions. Inline comments explain *why*, not
*what*.""",
    'Docstring presence and style are **Suggestion** under the shipped Ruff '
    'select (no `D` / pydocstyle). Expand `select` with `D` and '
    '`[lint.pydocstyle] convention = "google"` if you want mechanical '
    'enforcement.',
    [
      Rule(
        'Write a docstring for every public module, class, and function.',
        f'[pyguide §3.8]({PY}#s3.8-comments-and-docstrings) requires '
        'docstrings on public surfaces. Private helpers may omit them when '
        'the name and signature are enough.',
        'Suggestion',
        None,
        """# bad
def discount(price: Decimal, rate: Decimal) -> Decimal:
  return price * (1 - rate)

# good
def discount(price: Decimal, rate: Decimal) -> Decimal:
  \"\"\"Return ``price`` reduced by ``rate`` (0-1 inclusive).\"\"\"
  return price * (1 - rate)""",
      ),
      Rule(
        'Use Google-style sections: `Args:`, `Returns:`, `Raises:`, `Yields:`, `Attributes:`.',
        'One convention keeps editor folding, Sphinx, and humans aligned. Do '
        'not invent section names.',
        'Suggestion',
        None,
        """# bad  -  ad-hoc sections
def load(path: Path) -> Config:
  \"\"\"Load config.
  Parameters:
    path: file to read
  \"\"\"

# good
def load(path: Path) -> Config:
  \"\"\"Load config from ``path``.

  Args:
    path: Path to a TOML file.

  Returns:
    Parsed configuration.

  Raises:
    FileNotFoundError: If ``path`` does not exist.
  \"\"\"""",
      ),
      Rule(
        'Keep the summary line imperative and under one line; put details in the body.',
        'The summary is what `help()` and many UIs show first. Make it a '
        'command-like sentence without restating the function name.',
        'Suggestion',
        None,
        """# bad
def save(order: Order) -> None:
  \"\"\"This function is used to save an order to the database.\"\"\"

# good
def save(order: Order) -> None:
  \"\"\"Persist ``order`` to the database.\"\"\"""",
      ),
      Rule(
        'Do not duplicate type information that annotations already express.',
        'Restating `str` in the docstring drifts when the annotation changes. '
        'Document semantics, units, and constraints instead.',
        'Suggestion',
        None,
        """# bad
def ttl(seconds: int) -> int:
  \"\"\"Args:
    seconds: int seconds
  \"\"\"

# good
def ttl(seconds: int) -> int:
  \"\"\"Args:
    seconds: Lifetime in seconds; must be >= 0.
  \"\"\"""",
      ),
      Rule(
        'Document raised exceptions that callers are expected to handle.',
        f'[pyguide §3.8.3]({PY}#s3.8.3-functions-and-methods) expects '
        '`Raises:` for non-obvious failures. Do not list every possible builtin.',
        'Suggestion',
        None,
        """# bad  -  silent contract
def find_order(order_id: str) -> Order:
  ...

# good
def find_order(order_id: str) -> Order:
  \"\"\"Return the order.

  Raises:
    OrderNotFoundError: If no order exists for ``order_id``.
  \"\"\"""",
      ),
      Rule(
        'Use `#` comments for non-obvious why; never narrate the next line.',
        f'[pyguide §3.8.5]({PY}#s3.8.5-block-and-inline-comments) wants '
        'comments that add information the code does not.',
        'Suggestion',
        None,
        """# bad
# increment retries by one
retries = retries + 1

# good
# Vendor API fails closed after 3 attempts; fourth is wasted spend.
retries = retries + 1""",
      ),
      Rule(
        'Mark temporary work with `TODO(username):` and actionable text.',
        f'[pyguide §3.12]({PY}#s3.12-todo-comments) standardizes TODOs so '
        'they are searchable and owned.',
        'Suggestion',
        None,
        """# bad
# TODO: fix later

# good
# TODO(ada): replace polling with webhook once vendor enables it""",
      ),
      Rule(
        'Do not use docstrings as a changelog. Put history in git.',
        'Changelog docstrings rot and contradict `git log`. Document current '
        'behavior only.',
        'Suggestion',
        None,
        """# bad
\"\"\"Order service.

Changed 2024-01-02: added retries.
Changed 2024-03-01: removed SOAP.
\"\"\"

# good
\"\"\"Create and retrieve orders against the billing service.\"\"\"""",
      ),
      Rule(
        'For overridden methods, prefer a short docstring that states the specialization, or omit if identical.',
        f'[pyguide §3.8.3.1]({PY}#s3.8.3.1-overridden-methods) allows '
        'omission when the base docstring still applies.',
        'Suggestion',
        None,
        """# bad  -  paste of the entire base docstring
# good  -  one line on what differs, or inherit silently""",
      ),
      Rule(
        'Document modules with a top-level docstring describing the package role.',
        f'[pyguide §3.8.2]({PY}#s3.8.2-comments-in-modules) expects a module '
        'docstring as the first statement.',
        'Suggestion',
        None,
        """# bad  -  empty module header
from .service import OrderService

# good
\"\"\"Order creation and retrieval helpers.\"\"\"

from .service import OrderService""",
      ),
      Rule(
        'Keep class docstrings focused on the abstraction, not every method.',
        f'[pyguide §3.8.4]({PY}#s3.8.4-comments-in-classes) puts method '
        'details on methods. The class docstring states invariants and role.',
        'Suggestion',
        None,
        """# bad
class Cart:
  \"\"\"Cart has add(), remove(), total(), checkout(), ...\"\"\"

# good
class Cart:
  \"\"\"Mutable shopping cart; totals are recomputed on mutation.\"\"\"""",
      ),
      Rule(
        'Prefer doctest-style examples only when they stay executable and small.',
        'Huge doctests become second test suites that nobody runs. Prefer '
        'pytest for behavior; keep docstring examples tiny.',
        'Suggestion',
        None,
        """# bad  -  multi-screen doctest nobody executes
# good
def clamp(value: int, low: int, high: int) -> int:
  \"\"\"Clamp ``value`` into ``[low, high]``.

  Examples:
    >>> clamp(5, 0, 10)
    5
  \"\"\"""",
      ),
    ],
  )

  write_chapter(
    '05-imports-and-packages.md',
    'Imports & Packages',
    f"""Imports define the dependency graph readers see first.
[pyguide §2.2]({PY}#s2.2-imports) and [§3.13]({PY}#s3.13-imports-formatting)
are normative. Prefer absolute imports; keep import blocks tidy; never hide
dependencies behind stars.""",
    '`E401`, `E402`, `F401`, `F403`, `F405`, and related import codes are '
    '**Violation**. Style preferences without a matching enabled code are '
    '**Suggestion**.',
    [
      Rule(
        'Prefer absolute imports for application code.',
        'Absolute imports survive file moves and read clearly in reviews. '
        'Relative imports are fine inside tightly related package internals.',
        'Suggestion',
        None,
        """# bad  -  deep relative maze
from ....utils.time import now

# good
from app.utils.time import now""",
      ),
      Rule(
        'Group imports: stdlib, third party, local. Separate groups with a blank line.',
        f'[pyguide §3.13]({PY}#s3.13-imports-formatting) defines the order. '
        'Without `I` (isort) enabled, this is convention enforced in review.',
        'Suggestion',
        None,
        """# bad
from app.models import Order
import os
import fastapi

# good
import os

import fastapi

from app.models import Order""",
      ),
      Rule(
        'Do not place imports after code (except typing-only lazy imports under a documented guard).',
        '`E402` flags module-level imports that are not at the top. Lazy '
        'imports belong inside functions only when they break cycles or defer '
        'optional deps.',
        'Violation',
        'E402',
        """# bad
print('starting')
import os

# good
import os

print('starting')""",
      ),
      Rule(
        'Import modules, not individual objects, when the name would be ambiguous.',
        f'[pyguide §2.2]({PY}#s2.2-imports) prefers `import x` when multiple '
        'modules expose the same attribute names.',
        'Suggestion',
        None,
        """# bad
from audio import path
from video import path  # collision

# good
from app import audio, video
audio.path / video.path""",
      ),
      Rule(
        'Never use star imports in library or application modules.',
        'Star imports destroy static analysis and create silent name clashes. '
        '`F403`.',
        'Violation',
        'F403',
        """# bad
from .models import *

# good
from .models import Order, Customer""",
      ),
      Rule(
        'Delete unused imports immediately.',
        'Unused imports are noise and false dependencies. `F401`.',
        'Violation',
        'F401',
        """# bad
import json
from pathlib import Path

def cwd() -> Path:
  return Path.cwd()

# good
from pathlib import Path

def cwd() -> Path:
  return Path.cwd()""",
      ),
      Rule(
        'Use `from __future__ import annotations` only when you still need postponed evaluation; on 3.12+ prefer native PEP 695 / modern forms.',
        f'[pyguide §2.20]({PY}#s2.20-modern-python) encourages modern '
        'syntax. Python 3.12 makes many future imports unnecessary.',
        'Suggestion',
        None,
        """# bad  -  cargo-cult future import on 3.12
from __future__ import annotations
from typing import List
def f(xs: List[int]) -> None: ...

# good
def f(xs: list[int]) -> None: ...""",
      ),
      Rule(
        'Avoid importing the same name twice under different aliases.',
        'Alias churn hides the real dependency. Pick one name.',
        'Suggestion',
        None,
        """# bad
import numpy as np
import numpy as numpy

# good
import numpy as np""",
      ),
      Rule(
        'Keep third-party imports at module top even in FastAPI routers; do not import FastAPI inside each function.',
        'Per-function imports of frameworks hide cost and break patterns '
        'type checkers expect.',
        'Suggestion',
        None,
        """# bad
async def get_order(...):
  from fastapi import HTTPException
  ...

# good
from fastapi import HTTPException

async def get_order(...):
  ...""",
      ),
      Rule(
        'Treat `TYPE_CHECKING` blocks as the home for import-time-only types that would create cycles.',
        f'[pyguide §3.19.13]({PY}#s3.19.13-conditional-imports) covers '
        'conditional imports. Use them for types, not for hiding runtime deps.',
        'Suggestion',
        None,
        """# bad  -  runtime import inside TYPE_CHECKING misuse
# good
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from app.models import Order""",
      ),
      Rule(
        'Do not catch `ImportError` to paper over missing required dependencies.',
        'Optional extras are fine; required deps must fail loudly at import.',
        'Suggestion',
        None,
        """# bad
try:
  import pydantic
except ImportError:
  pydantic = None

# good  -  declare pydantic in project deps and import normally
import pydantic""",
      ),
      Rule(
        'Prefer package-relative imports (`from .models import Order`) inside a package over reaching through the install name repeatedly.',
        'Intra-package relative imports make renames easier and clarify '
        '"this package" vs third party.',
        'Suggestion',
        None,
        """# bad  -  always going through install name for siblings
from orders.models import Order

# good  -  inside the orders package
from .models import Order""",
      ),
      Rule(
        'One statement per import line; never `import a, b`.',
        'Comma-combined imports hurt diffs. `E401`.',
        'Violation',
        'E401',
        """# bad
import sys, os

# good
import os
import sys""",
      ),
    ],
  )

  # Chapters 6-10 are built by chapters_06_41.build() for maintainability.
