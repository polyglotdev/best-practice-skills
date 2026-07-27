<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 33. FastAPI Dependency Injection

Dependencies are FastAPI's DI system and, per
[fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices),
also the place for request validation that needs the DB or other services.
Prefer `Annotated[T, Depends(...)]`, chain small deps, prefer `async`
dependencies, and rely on per-request caching of dependency results.

**Tool alignment:** DI guidance is **Suggestion**.

## 33.1 Use `Annotated` for dependencies and path/query/body params.

> Why? Keeps defaults from colliding with Depends.
> **Suggestion.**

```python
# bad
async def get(user: User = Depends(get_user)):
  ...

# good
async def get(user: Annotated[User, Depends(get_user)]):
  ...
```

## 33.2 Depend on Protocols/interfaces, not concrete infrastructure types, at service boundaries.

> Why? Tests swap fakes.
> **Suggestion.**

```python
# bad - Depends(SqlAlchemyOrderRepo)
# good - Depends(get_orders_repo) -> OrdersRepo protocol
```

## 33.3 Use `dependency_overrides` in tests rather than patching internals.

> Why? Official escape hatch.
> **Suggestion.**

```python
# bad - monkeypatch private imports
# good - app.dependency_overrides[get_repo] = fake
```

## 33.4 Keep dependencies small and reusable; avoid hidden mega-dependencies.

> Why? A Depends that does five things is middleware.
> **Suggestion.**

```python
# bad - get_context loads user+flags+db+redis+audit
# good - split dependencies
```

## 33.5 Yield dependencies for resources that need teardown (sessions).

> Why? Ensures close even on errors.
> **Suggestion.**

```python
# bad - request-scoped session never closed
# good
def get_session():
  session = Session()
  try:
    yield session
  finally:
    session.close()
```

## 33.6 Do not perform authorization only inside nested helpers; put `require_permission` in the signature.

> Why? Visible security beats hidden checks.
> **Suggestion.**

```python
# bad - check buried in service
# good - user: Annotated[User, Depends(require_permission(...))]
```

## 33.7 Cache expensive pure deps with `lru_cache` only when settings-safe.

> Why? Do not cache request-scoped state.
> **Suggestion.**

```python
# bad - lru_cache on get_current_user
# good - lru_cache on get_settings
```

## 33.8 Prefer shared deps modules (`deps.py`) per package over circular imports across routers.

> Why? Import cycles follow messy deps.
> **Suggestion.**

```python
# bad - routers import each other's deps
# good - package deps.py
```

## 33.9 Keep side-effecting deps obvious (names like `require_`, `get_db`).

> Why? Readers scan signatures for security/IO.
> **Suggestion.**

```python
# bad - Depends(load)
# good - Depends(require_admin)
```

## 33.10 Avoid Depends on concrete FastAPI Request unless necessary.

> Why? Couples logic to transport.
> **Suggestion.**

```python
# bad - every service takes Request
# good - extract headers in deps; pass values
```

## 33.11 For multi-tenant apps, resolve tenant in a dependency and thread it explicitly.

> Why? Globals will leak across awaits.
> **Suggestion.**

```python
# bad - global context tenant
# good - tenant: Annotated[Tenant, Depends(get_tenant)]
```

## 33.12 Document override points for tests in README/dev docs.

> Why? Unknown seams slow everyone.
> **Suggestion.**

```python
# bad - tribal knowledge overrides
# good - list overridable deps
```
