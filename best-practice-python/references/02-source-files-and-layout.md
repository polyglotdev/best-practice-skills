<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 2. Source Files & Layout

A Python module is a file; a package is a directory with imports that
define a public surface. This chapter covers file naming, `if __name__ ==
'__main__'`, shebangs, and the shape of a modern `src/` layout.
[pyguide §3.16.3](https://google.github.io/styleguide/pyguide.html#s3.16.3-file-naming) and [§3.17](https://google.github.io/styleguide/pyguide.html#s3.17-main)
are the primary upstream anchors. Project layout with `uv` is
[Chapter 41](41-project-layout-and-uv.md).

**Tool alignment:** File naming and `__main__` guards are **Suggestion** under the shipped minimal Ruff select. Import hygiene that maps to `E4`/`F` is **Violation**.

## 2.1 Name modules `lowercase_with_underscores.py`. Never use CamelCase filenames.

> Why? [pyguide §3.16.3](https://google.github.io/styleguide/pyguide.html#s3.16.3-file-naming) requires short, all-lowercase names with underscores. CamelCase filenames break imports on case-sensitive filesystems and look like class names.
> **Suggestion.**

```python
# bad - file: OrderService.py
class OrderService:
  ...

# good - file: order_service.py
class OrderService:
  ...
```

## 2.2 Keep modules focused. Prefer more small modules over one thousand-line kitchen sink.

> Why? A module should have one job a reader can name in a sentence. God modules destroy navigation and force circular imports.
> **Suggestion.**

```python
# bad - billing.py also owns email, CSV export, and CLI parsing
# good - billing/charges.py, billing/invoices.py, billing/export.py
```

## 2.3 Put library code under `src/<package>/` (or a clear package root), not at the repo root.

> Why? A `src/` layout stops accidental imports of the working tree and matches what `uv`/`hatch` scaffold. Tests and scripts stay outside.
> **Suggestion.**

```python
# bad
./order_service.py
./test_order_service.py

# good
./src/orders/service.py
./tests/test_service.py
```

## 2.4 Guard script entry points with `if __name__ == '__main__':`.

> Why? [pyguide §3.17](https://google.github.io/styleguide/pyguide.html#s3.17-main) requires this so importing the module for tests does not run side effects.
> **Suggestion.**

```python
# bad
import sys
run(sys.argv)  # runs on import

# good
def main() -> None:
  run(sys.argv)


if __name__ == '__main__':
  main()
```

## 2.5 Keep `main()` thin: parse args, configure logging, call library code.

> Why? Business logic in `__main__` blocks is untestable. Push work into importable functions.
> **Suggestion.**

```python
# bad
if __name__ == '__main__':
  data = Path('in.csv').read_text()
  # 80 lines of transform...

# good
def main() -> None:
  args = parse_args()
  transform(Path(args.input), Path(args.output))


if __name__ == '__main__':
  main()
```

## 2.6 Omit shebang lines from library modules. Add `#!/usr/bin/env python3` only on executable scripts.

> Why? [pyguide §3.7](https://google.github.io/styleguide/pyguide.html#s3.7-shebang-line) limits shebangs to files meant to be executed directly.
> **Suggestion.**

```python
# bad - library module
#!/usr/bin/env python3
def add(a: int, b: int) -> int:
  return a + b

# good - no shebang in libraries; scripts may have one
def add(a: int, b: int) -> int:
  return a + b
```

## 2.7 Prefer explicit package exports via `__all__` when a package has a public API.

> Why? `__all__` documents the supported surface and keeps `from pkg import *` (when unavoidable) honest. Internal helpers stay underscore-prefixed.
> **Suggestion.**

```python
# bad - every name is accidentally public
from .service import OrderService, _cache_key

# good
from .service import OrderService

__all__ = ['OrderService']
```

## 2.8 Do not use star imports in application code.

> Why? [pyguide §2.2](https://google.github.io/styleguide/pyguide.html#s2.2-imports) rejects `from module import *` because it obscures provenance. `F403` flags star import usage that prevents static analysis.
> **Violation - enforced by `F403`.**

```python
# bad
from orders.models import *

# good
from orders.models import Order, LineItem
```

## 2.9 Keep tests in a top-level `tests/` tree that mirrors the package, not mixed into production modules.

> Why? Mixed `test_*.py` beside production code blurs packaging and encourages importing private test helpers from prod.
> **Suggestion.**

```python
# bad
src/orders/service.py
src/orders/test_service.py

# good
src/orders/service.py
tests/orders/test_service.py
```

## 2.10 Avoid circular imports by depending on interfaces at the edges and pushing shared types down.

> Why? [pyguide §3.19.14](https://google.github.io/styleguide/pyguide.html#s3.19.14-circular-dependencies) discusses typing-time cycles; runtime cycles are worse. Fix structure rather than importing inside functions as a habit.
> **Suggestion.**

```python
# bad - a.py imports b.py which imports a.py at module level
# good - extract shared types to types.py both can import
```

## 2.11 Do not rely on import side effects for registration. Prefer explicit app wiring.

> Why? Import-time registration makes test collection and tool import graphs fragile. Wire routers, plugins, and tasks in an explicit `create_app()` (FastAPI: chapter 32).
> **Suggestion.**

```python
# bad - module import mutates global registry
from . import handlers  # noqa: F401  # side-effect import

# good
def create_app() -> FastAPI:
  app = FastAPI()
  app.include_router(handlers.router)
  return app
```

## 2.12 Keep `__init__.py` thin. Re-export sparingly; do not hide a whole package behind a mega-import.

> Why? Fat `__init__.py` files create import cycles and slow cold start. Re-export the stable façade only.
> **Suggestion.**

```python
# bad - __init__.py imports every submodule eagerly
from .a import *
from .b import *
from .c import *

# good - re-export the public façade only
from .service import OrderService

__all__ = ['OrderService']
```

## 2.13 Name test modules `test_<unit>.py` and keep them import-light at collection time.

> Why? Heavy module-level I/O in test files slows every pytest run. Import expensive fixtures inside fixtures or tests.
> **Suggestion.**

```python
# bad - tests/test_db.py
conn = connect_production()  # runs at collection

# good
@pytest.fixture
def conn():
  return connect_test()
```
