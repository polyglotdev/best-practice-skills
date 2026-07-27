<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 41. Project Layout & uv

`uv` is the package/environment manager for this skill. Prefer
`src/` layouts, locked deps, and `uv run` for every tool invocation.

**Tool alignment:** Layout/tooling guidance is **Suggestion**.

## 41.1 Manage environments with `uv`; do not hand-maintain ad-hoc venvs as the primary workflow.

> Why? Reproducibility matters.
> **Suggestion.**

```python
# bad - pip install -r requirements.txt on system Python
# good - uv sync && uv run pytest
```

## 41.2 Use a `src/<package>/` layout for libraries and services.

> Why? Avoids accidental imports from CWD.
> **Suggestion.**

```python
# bad - package at repo root mixed with tests
# good - src/orders + tests/
```

## 41.3 Commit the lockfile (`uv.lock`) for applications.

> Why? Unpinned builds drift.
> **Suggestion.**

```python
# bad - floating deps only
# good - uv.lock committed
```

## 41.4 Declare Python requires as `>=3.12` (and not older) for new projects following this skill.

> Why? Floor is 3.12.
> **Suggestion.**

```python
# bad - requires-python = '>=3.9'
# good - requires-python = '>=3.12'
```

## 41.5 Put Ruff config at project root (`ruff.toml` or `[tool.ruff]`) and keep it authoritative.

> Why? Per-package drift hurts.
> **Suggestion.**

```python
# bad - each package different quotes
# good - root ruff.toml
```

## 41.6 Invoke tools via `uv run` (ruff, pytest, pyright).

> Why? PATH pollution disappears.
> **Suggestion.**

```python
# bad - globally installed pytest
# good - uv run pytest
```

## 41.7 Keep secrets out of the repo; use env / secret managers.

> Why? `.env` is local-only.
> **Suggestion.**

```python
# bad - commit .env with keys
# good - .env.example without secrets
```

## 41.8 Separate optional deps (`dev`, `test`) from runtime deps.

> Why? Prod images stay lean.
> **Suggestion.**

```python
# bad - pytest in main deps
# good - dependency-groups / optional-deps
```

## 41.9 Do not start long-lived web servers from agent automation sessions.

> Why? Policy: run checks, not servers.
> **Suggestion.**

```python
# bad - uvicorn in background during skill authoring
# good - pytest + ruff only
```

## 41.10 Document the exact bootstrap commands in README.

> Why? New contributors should not guess.
> **Suggestion.**

```python
# bad - undocumented poetry leftovers
# good - uv sync / uv run pytest
```

## 41.11 Keep scripts under `scripts/` and make them `uv run`-able.

> Why? Random bash with system python fails.
> **Suggestion.**

```python
# bad - #!/usr/bin/env python relying on system 3.9
# good - uv run scripts/build_python_skill.py
```

## 41.12 Align CI with local: same uv version policy, same ruff/pytest commands.

> Why? Works-on-my-machine dies here.
> **Suggestion.**

```python
# bad - CI pip, laptop uv
# good - uv in both
```
