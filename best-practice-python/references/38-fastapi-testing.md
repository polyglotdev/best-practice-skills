<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 38. FastAPI Testing

Test FastAPI with httpx ASGI transport / `AsyncClient` from day zero
([fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices#set-tests-client-async-from-day-0)),
plus dependency overrides and deterministic fakes.

**Tool alignment:** FastAPI testing guidance is **Suggestion**.

## 38.1 Prefer app-factory + fresh app per test module when overrides are needed.

> Why? Shared global app state leaks.
> **Suggestion.**

```python
# bad - mutate global app in tests
# good - create_app() per test
```

## 38.2 Use `dependency_overrides` for DB/auth/clock seams.

> Why? Patching internals is brittle.
> **Suggestion.**

```python
# bad - mock.patch path strings
# good - app.dependency_overrides[get_db] = fake_db
```

## 38.3 Use `httpx.AsyncClient(transport=ASGITransport(app=app))` for async tests.

> Why? Real network optional.
> **Suggestion.**

```python
# bad - live server required for unit tests
# good - ASGI transport in-process
```

## 38.4 Clear `dependency_overrides` after tests.

> Why? Order-dependent suites follow.
> **Suggestion.**

```python
# bad - leave overrides set
# good - fixture finalizer clears
```

## 38.5 Assert status code and payload shape; do not only assert 200.

> Why? Wrong body still 200s.
> **Suggestion.**

```python
# bad
assert response.status_code == 200

# good
assert response.status_code == 200
assert response.json()['id'] == order_id
```

## 38.6 Test authz negative cases (401/403) for every protected route class.

> Why? Happy path is not security.
> **Suggestion.**

```python
# bad - only authorized tests
# good - anonymous/forbidden cases
```

## 38.7 Keep DB integration tests transactional/isolated.

> Why? Shared DB state flakes.
> **Suggestion.**

```python
# bad - leftover rows
# good - transaction rollback fixture
```

## 38.8 Do not start uvicorn in tests.

> Why? In-process ASGI is enough.
> **Suggestion.**

```python
# bad - subprocess uvicorn
# good - TestClient/AsyncClient
```

## 38.9 Freeze time for expiring tokens/signatures.

> Why? Sleep-based tests flake.
> **Suggestion.**

```python
# bad - sleep until expiry
# good - clock dependency override
```

## 38.10 Contract-test OpenAPI for intentional breaks when external clients exist.

> Why? Silent schema drift hurts.
> **Suggestion.**

```python
# bad - ignore schema diffs
# good - snapshot or schemathesis selectively
```

## 38.11 Prefer factory helpers for JSON payloads over giant literals everywhere.

> Why? Literals rot.
> **Suggestion.**

```python
# bad - 40-line JSON dict duplicated
# good - make_order_payload(**overrides)
```

## 38.12 Run unit tests by default; mark and separate e2e.

> Why? Default suite must be fast.
> **Suggestion.**

```python
# bad - e2e in unmarked default
# good - -m 'not e2e' default
```
