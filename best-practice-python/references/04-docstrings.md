<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 4. Docstrings

Google-style docstrings are the documentation format for this skill.
[pyguide §3.8](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) and
[§3.8.1](https://google.github.io/styleguide/pyguide.html#s3.8.1-comments-in-doc-strings) are normative. Use them for
public modules, classes, and functions. Inline comments explain *why*, not
*what*.

**Tool alignment:** Docstring presence and style are **Suggestion** under the shipped Ruff select (no `D` / pydocstyle). Expand `select` with `D` and `[lint.pydocstyle] convention = "google"` if you want mechanical enforcement.

## 4.1 Write a docstring for every public module, class, and function.

> Why? [pyguide §3.8](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) requires docstrings on public surfaces. Private helpers may omit them when the name and signature are enough.
> **Suggestion.**

```python
# bad
def discount(price: Decimal, rate: Decimal) -> Decimal:
  return price * (1 - rate)

# good
def discount(price: Decimal, rate: Decimal) -> Decimal:
  """Return ``price`` reduced by ``rate`` (0-1 inclusive)."""
  return price * (1 - rate)
```

## 4.2 Use Google-style sections: `Args:`, `Returns:`, `Raises:`, `Yields:`, `Attributes:`.

> Why? One convention keeps editor folding, Sphinx, and humans aligned. Do not invent section names.
> **Suggestion.**

```python
# bad - ad-hoc sections
def load(path: Path) -> Config:
  """Load config.
  Parameters:
    path: file to read
  """

# good
def load(path: Path) -> Config:
  """Load config from ``path``.

  Args:
    path: Path to a TOML file.

  Returns:
    Parsed configuration.

  Raises:
    FileNotFoundError: If ``path`` does not exist.
  """
```

## 4.3 Keep the summary line imperative and under one line; put details in the body.

> Why? The summary is what `help()` and many UIs show first. Make it a command-like sentence without restating the function name.
> **Suggestion.**

```python
# bad
def save(order: Order) -> None:
  """This function is used to save an order to the database."""

# good
def save(order: Order) -> None:
  """Persist ``order`` to the database."""
```

## 4.4 Do not duplicate type information that annotations already express.

> Why? Restating `str` in the docstring drifts when the annotation changes. Document semantics, units, and constraints instead.
> **Suggestion.**

```python
# bad
def ttl(seconds: int) -> int:
  """Args:
    seconds: int seconds
  """

# good
def ttl(seconds: int) -> int:
  """Args:
    seconds: Lifetime in seconds; must be >= 0.
  """
```

## 4.5 Document raised exceptions that callers are expected to handle.

> Why? [pyguide §3.8.3](https://google.github.io/styleguide/pyguide.html#s3.8.3-functions-and-methods) expects `Raises:` for non-obvious failures. Do not list every possible builtin.
> **Suggestion.**

```python
# bad - silent contract
def find_order(order_id: str) -> Order:
  ...

# good
def find_order(order_id: str) -> Order:
  """Return the order.

  Raises:
    OrderNotFoundError: If no order exists for ``order_id``.
  """
```

## 4.6 Use `#` comments for non-obvious why; never narrate the next line.

> Why? [pyguide §3.8.5](https://google.github.io/styleguide/pyguide.html#s3.8.5-block-and-inline-comments) wants comments that add information the code does not.
> **Suggestion.**

```python
# bad
# increment retries by one
retries = retries + 1

# good
# Vendor API fails closed after 3 attempts; fourth is wasted spend.
retries = retries + 1
```

## 4.7 Mark temporary work with `TODO(username):` and actionable text.

> Why? [pyguide §3.12](https://google.github.io/styleguide/pyguide.html#s3.12-todo-comments) standardizes TODOs so they are searchable and owned.
> **Suggestion.**

```python
# bad
# TODO: fix later

# good
# TODO(ada): replace polling with webhook once vendor enables it
```

## 4.8 Do not use docstrings as a changelog. Put history in git.

> Why? Changelog docstrings rot and contradict `git log`. Document current behavior only.
> **Suggestion.**

```python
# bad
"""Order service.

Changed 2024-01-02: added retries.
Changed 2024-03-01: removed SOAP.
"""

# good
"""Create and retrieve orders against the billing service."""
```

## 4.9 For overridden methods, prefer a short docstring that states the specialization, or omit if identical.

> Why? [pyguide §3.8.3.1](https://google.github.io/styleguide/pyguide.html#s3.8.3.1-overridden-methods) allows omission when the base docstring still applies.
> **Suggestion.**

```python
# bad - paste of the entire base docstring
# good - one line on what differs, or inherit silently
```

## 4.10 Document modules with a top-level docstring describing the package role.

> Why? [pyguide §3.8.2](https://google.github.io/styleguide/pyguide.html#s3.8.2-comments-in-modules) expects a module docstring as the first statement.
> **Suggestion.**

```python
# bad - empty module header
from .service import OrderService

# good
"""Order creation and retrieval helpers."""

from .service import OrderService
```

## 4.11 Keep class docstrings focused on the abstraction, not every method.

> Why? [pyguide §3.8.4](https://google.github.io/styleguide/pyguide.html#s3.8.4-comments-in-classes) puts method details on methods. The class docstring states invariants and role.
> **Suggestion.**

```python
# bad
class Cart:
  """Cart has add(), remove(), total(), checkout(), ..."""

# good
class Cart:
  """Mutable shopping cart; totals are recomputed on mutation."""
```

## 4.12 Prefer doctest-style examples only when they stay executable and small.

> Why? Huge doctests become second test suites that nobody runs. Prefer pytest for behavior; keep docstring examples tiny.
> **Suggestion.**

```python
# bad - multi-screen doctest nobody executes
# good
def clamp(value: int, low: int, high: int) -> int:
  """Clamp ``value`` into ``[low, high]``.

  Examples:
    >>> clamp(5, 0, 10)
    5
  """
```
