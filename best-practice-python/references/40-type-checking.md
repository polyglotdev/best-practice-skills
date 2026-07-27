<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 40. Type Checking

Ruff is not a type checker. Use Pyright or mypy for static types.
This skill assumes a strict checker is available in CI even though types
are Suggestions under Ruff's minimal select.

**Tool alignment:** Type-checker setup is **Suggestion**.

## 40.1 Run a type checker in CI (pyright or mypy) on application packages.

> Why? Ruff F rules are not enough.
> **Suggestion.**

```python
# bad - only ruff check
# good - ruff + pyright
```

## 40.2 Prefer pyright/`basedpyright` for FastAPI+Pydantic v2 projects unless the team is already on mypy.

> Why? Pydantic plugins differ; pick one.
> **Suggestion.**

```python
# bad - neither checker configured
# good - pyrightconfig.json / [tool.pyright]
```

## 40.3 Keep `strict` (or gradually strict) mode; do not celebrate `Any` silence.

> Why? Loose mode hides the bugs you wanted.
> **Suggestion.**

```python
# bad - type checker optional locally
# good - strict on app packages
```

## 40.4 Do not `# type: ignore` without an error code.

> Why? Same discipline as Ruff noqa.
> **Suggestion.**

```python
# bad
value = legacy()  # type: ignore

# good
value = legacy()  # type: ignore[no-untyped-call]
```

## 40.5 Commit stubs only when upstream lacks them; prefer upstream typing.

> Why? Local stubs rot.
> **Suggestion.**

```python
# bad - sprawling custom stubs
# good - typeshed/upstream first
```

## 40.6 Type FastAPI deps and handlers fully; OpenAPI will not save your internals.

> Why? Handlers are code.
> **Suggestion.**

```python
# bad - untyped **kwargs handler
# good - Annotated models throughout
```

## 40.7 Avoid `cast` as a habit; narrow with isinstance/TypeGuards.

> Why? cast is an unchecked assertion.
> **Suggestion.**

```python
# bad - cast(User, data)
# good - User.model_validate(data)
```

## 40.8 Keep third-party untyped libs behind typed adapters.

> Why? Contain the fire.
> **Suggestion.**

```python
# bad - Any spreads from vendor SDK
# good - adapter returns domain types
```

## 40.9 Ensure `target-version`/pyright pythonVersion match 3.12.

> Why? Mismatch causes false diagnostics.
> **Suggestion.**

```python
# bad - pyright pythonVersion 3.10
# good - 3.12
```

## 40.10 Type test helpers enough to catch broken fakes.

> Why? Untyped fakes diverge.
> **Suggestion.**

```python
# bad - fake repo returns Any
# good - FakeOrdersRepo implements Protocol
```

## 40.11 Do not disable the checker on whole packages to ship.

> Why? Fix or quarantine with a plan.
> **Suggestion.**

```python
# bad - exclude src/legacy forever
# good - tracked quarantine list
```

## 40.12 Reconcile type-ignore counts in CI budgets.

> Why? Unbounded ignores become culture.
> **Suggestion.**

```python
# bad - ignore count climbs unnoticed
# good - budget gate
```
