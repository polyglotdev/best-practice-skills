<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 26. Testing

pytest is the default test runner. Prefer fast unit tests; use
httpx/`TestClient` / `AsyncClient` for FastAPI (chapter 38).

**Tool alignment:** Testing style is **Suggestion** (no `PT` enabled).

## 26.1 Name tests `test_<behavior>_<condition>` and keep one assert-focus per test.

> Why? Long tests hide failures.
> **Suggestion.**

```python
# bad
def test_all():
  ...

# good
def test_discount_applies_for_loyalty_members():
  ...
```

## 26.2 Prefer plain asserts with pytest; do not reinvent assertion helpers that hide diffs.

> Why? pytest rewrites asserts.
> **Suggestion.**

```python
# bad
self.assertEqual(a, b)

# good
assert a == b
```

## 26.3 Use fixtures for arrangement; keep fixtures thin and composable.

> Why? God fixtures couple suites.
> **Suggestion.**

```python
# bad - fixture that builds entire prod graph
# good - small fixtures assembled in tests
```

## 26.4 Do not hit real networks in unit tests; fake at Protocol boundaries.

> Why? Flakes are not CI.
> **Suggestion.**

```python
# bad - tests call prod HTTP
# good - fake SupportsBilling
```

## 26.5 Parametrize edge cases with `@pytest.mark.parametrize`.

> Why? Copy-paste tests drift.
> **Suggestion.**

```python
# bad - five near-identical tests
# good - parametrize inputs/expected
```

## 26.6 Mark slow/integration tests explicitly and keep default suite fast.

> Why? Developers skip slow unmarked suites.
> **Suggestion.**

```python
# bad - 30s DB test in default path unlabeled
# good - @pytest.mark.integration
```

## 26.7 Avoid testing private functions directly when public behavior covers them.

> Why? Private tests brittle.
> **Suggestion.**

```python
# bad - assert _normalize()
# good - assert public parse() outcomes
```

## 26.8 Freeze time with a dedicated helper for time-dependent logic.

> Why? Sleeping in tests is banned.
> **Suggestion.**

```python
# bad - time.sleep(2)
# good - freezegun/clock fixture
```

## 26.9 Prefer deterministic seeds for any randomness.

> Why? Flaky tests are defects.
> **Suggestion.**

```python
# bad - random.random() unseeded
# good - random.Random(0)
```

## 26.10 Put shared helpers in `conftest.py` or `tests/helpers/`, not in production packages.

> Why? Prod must not import pytest.
> **Suggestion.**

```python
# bad - app/testing_utils.py imported by prod
# good - tests/helpers/factories.py
```

## 26.11 Assert on observable outcomes, not on log text, unless logging is the product.

> Why? Log wording changes constantly.
> **Suggestion.**

```python
# bad - assert 'saved' in caplog.text for business rule
# good - assert repository saved entity
```

## 26.12 Keep tests 2-space / single-quote consistent via Ruff; do not special-case test style.

> Why? Same formatter as prod.
> **Violation - enforced by `ruff format`.**

```python
# bad - four-space tests
# good - ruff format tests too
```
