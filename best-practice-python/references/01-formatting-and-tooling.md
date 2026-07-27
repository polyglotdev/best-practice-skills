<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 1. Formatting & Tooling

Python's formatting debate is settled by a tool, not a committee.
[`ruff format`](https://docs.astral.sh/ruff/formatter/) owns layout the same
way `gofmt` owns Go, `google-java-format` owns Java, and `ktlint` owns Kotlin.
This chapter documents that chain and the house overrides that differ from
[Google Python Style Guide §3](https://google.github.io/styleguide/pyguide.html#s3-python-style-rules).

**House overrides (deliberate):**

| Setting | This skill | Upstream |
|---|---|---|
| Indent | **2 spaces** (`indent-width = 2`) | [pyguide §3.4](https://google.github.io/styleguide/pyguide.html#s3.4-indentation) and PEP 8 use 4 |
| Quotes | **single** (`quote-style = 'single'`) | Ruff / Black default to double |
| Line length | **88** | [pyguide §3.2](https://google.github.io/styleguide/pyguide.html#s3.2-line-length) prefers 80 |
| Language floor | **Python 3.12** (`target-version = 'py312'`) | - |

These are not what Google says. They are project law. Every sample in every
chapter uses 2-space indent and single quotes. No later chapter re-litigates
whitespace, quote style, or line wrapping.

Formatting is not lint. `ruff format` rewrites layout; `ruff check` with the
shipped `select = ['E4', 'E7', 'E9', 'F']` catches a small set of correctness
and import issues. Semantic pyguide rules that need broader Ruff families
(`D`, `N`, `UP`, `B`, …) are labeled **Suggestion** until the project expands
`select`. See [Chapter 39](39-ruff-configuration.md).

**Tool alignment:** Layout is enforced by `ruff format`. The few lint rules below that map to enabled codes (`E4`/`E7`/`E9`/`F`) are **Violation**; everything else is **Suggestion**.

## 1.1 Run `ruff format` before every commit and `ruff check` in CI.

> Why? One canonical layout kills whitespace diffs and keeps `git blame` meaningful. A formatting failure is the cheapest CI failure. Pair the write path (`ruff format`) with the read-only gate (`ruff check`).
> **Violation - enforced by `ruff format`.**

```python
# bad - hand-laid-out; ruff format rewrites almost every line
def convert(amount:Decimal,from_c:str,to_c:str)->Decimal:
  if amount<0:raise ValueError("negative")
  return amount*rate_for(from_c,to_c)

# good - exactly what ruff format emits under this repo's ruff.toml
def convert(amount: Decimal, from_c: str, to_c: str) -> Decimal:
  if amount < 0:
    raise ValueError('negative')
  return amount * rate_for(from_c, to_c)
```

## 1.2 Indent with two spaces. Never tabs, never four.

> Why? This is a house override of [pyguide §3.4](https://google.github.io/styleguide/pyguide.html#s3.4-indentation) and PEP 8. The shipped `ruff.toml` sets `indent-width = 2`. Mixing 4-space Python into this repo produces a whole-file diff the first time anyone runs the formatter.
> **Violation - enforced by `ruff format`.**

```python
# bad - four-space blocks (PEP 8 / pyguide default)
def place(order: Order) -> Receipt:
    total = order.subtotal + order.tax
    return Receipt(total=total)

# good - two spaces, matching indent-width = 2
def place(order: Order) -> Receipt:
  total = order.subtotal + order.tax
  return Receipt(total=total)
```

## 1.3 Use single quotes for string literals. Use double only when the string contains a single quote and escaping would hurt readability.

> Why? The shipped `ruff.toml` sets `quote-style = 'single'`. Consistency matters more than the quote character; the formatter picks one.
> **Violation - enforced by `ruff format`.**

```python
# bad - double quotes everywhere under a single-quote house style
name = "Ada"
msg = "hello"

# good
name = 'Ada'
msg = "Ada's laptop"  # double is fine when it avoids escaping
```

## 1.4 Keep lines within 88 columns unless a long URL or similar undivisible token forces a longer line.

> Why? [pyguide §3.2](https://google.github.io/styleguide/pyguide.html#s3.2-line-length) prefers 80; this skill uses Black/Ruff's 88. Do not hand-wrap for aesthetics once `ruff format` has chosen breaks.
> **Violation - enforced by `ruff format`.**

```python
# bad - arbitrary mid-expression wrapping that fights the formatter
total = (
  price
  +
  tax
)

# good - let ruff format choose breaks at 88
total = price + tax + shipping
```

## 1.5 Put one import per line. Do not combine imports with commas.

> Why? [pyguide §3.13](https://google.github.io/styleguide/pyguide.html#s3.13-imports-formatting) and PEP 8 require separate lines so diffs and conflict resolution stay readable.
> **Violation - enforced by `E401`.**

```python
# bad
import os, sys

# good
import os
import sys
```

## 1.6 Never compare to `None` with `==` or `!=`. Use `is` / `is not`.

> Why? Identity is the correct test for `None`. `==` can be overloaded and hide bugs. Ruff `E711` catches this.
> **Violation - enforced by `E711`.**

```python
# bad
if value == None:
  return default

# good
if value is None:
  return default
```

## 1.7 Never compare booleans with `== True` or `== False`.

> Why? Boolean comparisons with equality are noise and invite mistakes with truthy non-bools. Use the value directly (or `not`). `E712`.
> **Violation - enforced by `E712`.**

```python
# bad
if ready == True:
  start()

# good
if ready:
  start()
```

## 1.8 Do not use a bare `except:`. Catch specific exceptions.

> Why? Bare `except` swallows `KeyboardInterrupt` and `SystemExit`. [pyguide §2.4](https://google.github.io/styleguide/pyguide.html#s2.4-exceptions) rejects it. `E722`.
> **Violation - enforced by `E722`.**

```python
# bad
try:
  parse(blob)
except:
  return None

# good
try:
  parse(blob)
except ValueError:
  return None
```

## 1.9 Do not assign a `lambda` to a name. Use `def`.

> Why? Named lambdas defeat the point of both `def` (a real name and traceback) and `lambda` (an inline expression). `E731`.
> **Violation - enforced by `E731`.**

```python
# bad
add = lambda x, y: x + y

# good
def add(x: int, y: int) -> int:
  return x + y
```

## 1.10 Remove unused imports. Do not leave import residue after refactors.

> Why? Unused imports slow reviews and confuse readers about real dependencies. `F401`.
> **Violation - enforced by `F401`.**

```python
# bad
import json  # never used
from pathlib import Path

def root() -> Path:
  return Path.cwd()

# good
from pathlib import Path

def root() -> Path:
  return Path.cwd()
```

## 1.11 Do not leave unused variables. Prefix intentionally unused names with `_`.

> Why? Dead bindings hide incomplete refactors. The shipped `dummy-variable-rgx` allows underscore-prefixed names. `F841`.
> **Violation - enforced by `F841`.**

```python
# bad
def handle(event: Event) -> None:
  unused = event.payload
  dispatch(event.kind)

# good
def handle(event: Event) -> None:
  _payload = event.payload  # kept for a future branch; underscore-ok
  dispatch(event.kind)
```

## 1.12 Never put multiple statements on one line with semicolons.

> Why? [pyguide §3.1](https://google.github.io/styleguide/pyguide.html#s3.1-semicolons) bans semicolons as statement separators. `E702` / `E703`.
> **Violation - enforced by `E702`.**

```python
# bad
x = 1; y = 2

# good
x = 1
y = 2
```

## 1.13 Drive formatting and lint through `uv run` (or the project venv), not a random global Ruff.

> Why? Local Ruff versions drift. Pin Ruff in the project and invoke it through `uv` so CI and laptops agree on rule codes.
> **Suggestion.**

```python
# bad - whatever `ruff` happens to be on PATH
ruff format .
ruff check .

# good - project-pinned tool
uv run ruff format .
uv run ruff check .
```

## 1.14 Do not disable Ruff with blanket `# noqa` or file-level ignores without a scoped rule code and a reason.

> Why? Unscoped suppressions rot. Prefer fixing the code; when you must suppress, name the rule (`# noqa: F401`) and explain why.
> **Suggestion.**

```python
# bad
# ruff: noqa
from .legacy import *  # noqa

# good
from .legacy import helper  # noqa: F401  # re-exported for compat
```

## 1.15 Treat the formatter as law: never fight it with manual alignment or trailing-comma games.

> Why? `skip-magic-trailing-comma = false` means a trailing comma is a signal you want a multi-line form. Use that deliberately; do not hand-align columns the formatter will smash.
> **Suggestion.**

```python
# bad - columnar alignment the formatter will destroy
user = User(id=1,   name='Ada',  role='admin')
guest = User(id=2,  name='Bob',  role='user')

# good - formatter-stable
user = User(id=1, name='Ada', role='admin')
guest = User(id=2, name='Bob', role='user')
```
