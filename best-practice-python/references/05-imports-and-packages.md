<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 5. Imports & Packages

Imports define the dependency graph readers see first.
[pyguide §2.2](https://google.github.io/styleguide/pyguide.html#s2.2-imports) and [§3.13](https://google.github.io/styleguide/pyguide.html#s3.13-imports-formatting)
are normative. Prefer absolute imports; keep import blocks tidy; never hide
dependencies behind stars.

**Tool alignment:** `E401`, `E402`, `F401`, `F403`, `F405`, and related import codes are **Violation**. Style preferences without a matching enabled code are **Suggestion**.

## 5.1 Prefer absolute imports for application code.

> Why? Absolute imports survive file moves and read clearly in reviews. Relative imports are fine inside tightly related package internals.
> **Suggestion.**

```python
# bad - deep relative maze
from ....utils.time import now

# good
from app.utils.time import now
```

## 5.2 Group imports: stdlib, third party, local. Separate groups with a blank line.

> Why? [pyguide §3.13](https://google.github.io/styleguide/pyguide.html#s3.13-imports-formatting) defines the order. Without `I` (isort) enabled, this is convention enforced in review.
> **Suggestion.**

```python
# bad
from app.models import Order
import os
import fastapi

# good
import os

import fastapi

from app.models import Order
```

## 5.3 Do not place imports after code (except typing-only lazy imports under a documented guard).

> Why? `E402` flags module-level imports that are not at the top. Lazy imports belong inside functions only when they break cycles or defer optional deps.
> **Violation - enforced by `E402`.**

```python
# bad
print('starting')
import os

# good
import os

print('starting')
```

## 5.4 Import modules, not individual objects, when the name would be ambiguous.

> Why? [pyguide §2.2](https://google.github.io/styleguide/pyguide.html#s2.2-imports) prefers `import x` when multiple modules expose the same attribute names.
> **Suggestion.**

```python
# bad
from audio import path
from video import path  # collision

# good
from app import audio, video
audio.path / video.path
```

## 5.5 Never use star imports in library or application modules.

> Why? Star imports destroy static analysis and create silent name clashes. `F403`.
> **Violation - enforced by `F403`.**

```python
# bad
from .models import *

# good
from .models import Order, Customer
```

## 5.6 Delete unused imports immediately.

> Why? Unused imports are noise and false dependencies. `F401`.
> **Violation - enforced by `F401`.**

```python
# bad
import json
from pathlib import Path

def cwd() -> Path:
  return Path.cwd()

# good
from pathlib import Path

def cwd() -> Path:
  return Path.cwd()
```

## 5.7 Use `from __future__ import annotations` only when you still need postponed evaluation; on 3.12+ prefer native PEP 695 / modern forms.

> Why? [pyguide §2.20](https://google.github.io/styleguide/pyguide.html#s2.20-modern-python) encourages modern syntax. Python 3.12 makes many future imports unnecessary.
> **Suggestion.**

```python
# bad - cargo-cult future import on 3.12
from __future__ import annotations
from typing import List
def f(xs: List[int]) -> None: ...

# good
def f(xs: list[int]) -> None: ...
```

## 5.8 Avoid importing the same name twice under different aliases.

> Why? Alias churn hides the real dependency. Pick one name.
> **Suggestion.**

```python
# bad
import numpy as np
import numpy as numpy

# good
import numpy as np
```

## 5.9 Keep third-party imports at module top even in FastAPI routers; do not import FastAPI inside each function.

> Why? Per-function imports of frameworks hide cost and break patterns type checkers expect.
> **Suggestion.**

```python
# bad
async def get_order(...):
  from fastapi import HTTPException
  ...

# good
from fastapi import HTTPException

async def get_order(...):
  ...
```

## 5.10 Treat `TYPE_CHECKING` blocks as the home for import-time-only types that would create cycles.

> Why? [pyguide §3.19.13](https://google.github.io/styleguide/pyguide.html#s3.19.13-conditional-imports) covers conditional imports. Use them for types, not for hiding runtime deps.
> **Suggestion.**

```python
# bad - runtime import inside TYPE_CHECKING misuse
# good
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from app.models import Order
```

## 5.11 Do not catch `ImportError` to paper over missing required dependencies.

> Why? Optional extras are fine; required deps must fail loudly at import.
> **Suggestion.**

```python
# bad
try:
  import pydantic
except ImportError:
  pydantic = None

# good - declare pydantic in project deps and import normally
import pydantic
```

## 5.12 Prefer package-relative imports (`from .models import Order`) inside a package over reaching through the install name repeatedly.

> Why? Intra-package relative imports make renames easier and clarify "this package" vs third party.
> **Suggestion.**

```python
# bad - always going through install name for siblings
from orders.models import Order

# good - inside the orders package
from .models import Order
```

## 5.13 One statement per import line; never `import a, b`.

> Why? Comma-combined imports hurt diffs. `E401`.
> **Violation - enforced by `E401`.**

```python
# bad
import sys, os

# good
import os
import sys
```
