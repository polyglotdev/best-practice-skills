<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 39. Ruff Configuration

This skill ships `ruff.toml` at the repo root. Formatting is delegated
to `ruff format`; lint uses the minimal enabled set `E4`/`E7`/`E9`/`F`.
Expanding `select` is a deliberate product decision because it will surface
findings in existing code.

**Tool alignment:** Config rules that restate the shipped file are **Violation** where they map to enabled checks; expansion guidance is **Suggestion**.

## 39.1 Keep `target-version = 'py312'` aligned with the language floor.

> Why? A 3.11 target disables 3.12-aware fixes.
> **Suggestion.**

```python
# bad
target-version = 'py311'

# good
target-version = 'py312'
```

## 39.2 Keep `indent-width = 2` and `quote-style = 'single'` as house law.

> Why? Do not locally reintroduce 4-space/double-quote Python.
> **Violation - enforced by `ruff format`.**

```python
# bad - editor inserts 4 spaces
# good - editorconfig + ruff format
```

## 39.3 Do not claim a Ruff rule is enforced unless it is in the effective select set.

> Why? Reconciliation rule from the handoff.
> **Suggestion.**

```python
# bad - Enforced by: D100 when D is not selected
# good - Suggestion until select expands
```

## 39.4 Run `ruff format` and `ruff check` in CI.

> Why? Format drift is a CI failure.
> **Violation - enforced by `ruff format`.**

```python
# bad - format only on laptops
# good - CI runs both
```

## 39.5 Prefer scoped `# noqa: CODE` with reasons; ban file-wide ignores without review.

> Why? Unscoped noqa grows forever.
> **Suggestion.**

```python
# bad
# ruff: noqa

# good
import x  # noqa: F401  # re-export
```

## 39.6 When expanding select, add families deliberately (`I`, `UP`, `B`, `ASYNC`, `PT`).

> Why? Big-bang enablements stall teams.
> **Suggestion.**

```python
# bad - select = ['ALL'] overnight
# good - phased enablement
```

## 39.7 Keep exclude lists for virtualenvs/build dirs; do not exclude `src`/`tests`.

> Why? Excluding tests hides violations.
> **Suggestion.**

```python
# bad - exclude = ['tests']
# good - exclude only caches/build
```

## 39.8 Treat `.mypy_cache` (correct spelling) as excluded; never `.mymy_cache`.

> Why? Typo creates useless exclude noise.
> **Suggestion.**

```python
# bad
'.mymy_cache'

# good
'.mypy_cache'
```

## 39.9 Pin Ruff in project tooling (`uv add --dev ruff`) and invoke via `uv run`.

> Why? Global Ruff drifts (local 0.9 vs latest 0.16).
> **Suggestion.**

```python
# bad - random global ruff
# good - uv run ruff check .
```

## 39.10 Do not enable detekt-style semantic families in prose without enabling them in config.

> Why? Honesty over aspirational badges.
> **Suggestion.**

```python
# bad - claim ASYNC001 enforced
# good - Suggestion until ASYNC selected
```

## 39.11 Keep `line-length = 88` unless the whole org moves together.

> Why? Mixed lengths cause churn.
> **Violation - enforced by `ruff format`.**

```python
# bad - 80 in one package, 120 in another
# good - 88 everywhere
```

## 39.12 Document any future select expansions in README-python.md.

> Why? Skilled agents need the effective set.
> **Suggestion.**

```python
# bad - silent select change
# good - changelog note + callout reconciliation
```
