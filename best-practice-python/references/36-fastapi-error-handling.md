<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 36. FastAPI Error Handling

Map domain errors to HTTP at the edge. Prefer consistent error
payloads over ad-hoc `HTTPException` strings everywhere.

**Tool alignment:** Error-handling guidance is **Suggestion**.

## 36.1 Raise domain exceptions in services/repos; convert in exception handlers.

> Why? HTTP concerns stay at the edge.
> **Suggestion.**

```python
# bad - HTTPException in repository
# good - OrderNotFoundError -> 404 handler
```

## 36.2 Use `HTTPException` for transport-level failures when no domain type exists.

> Why? Do not invent 20 wrappers for one-offs.
> **Suggestion.**

```python
# bad - DomainHttpError soup
# good - HTTPException(status_code=400, detail='...') for simple cases
```

## 36.3 Return stable error shapes (problem+json or a single ErrorResponse model).

> Why? Clients parse one schema.
> **Suggestion.**

```python
# bad - sometimes str, sometimes dict
# good - ErrorResponse everywhere
```

## 36.4 Do not leak internal exception messages to clients.

> Why? Log internally; return safe detail.
> **Suggestion.**

```python
# bad - detail=str(err)
# good - detail='order not found'; log exception
```

## 36.5 Preserve 422 validation errors from FastAPI/Pydantic; do not replace with opaque 400s without cause.

> Why? Field errors help clients.
> **Suggestion.**

```python
# bad - catch ValidationError -> 400 blank
# good - default 422 or shaped translation
```

## 36.6 Log 5xx with stack traces; log 4xx at info/warning without stacks by default.

> Why? Noise vs signal.
> **Suggestion.**

```python
# bad - exception stack on every 404
# good - info for 404, exception for 500
```

## 36.7 Map auth failures to 401/403 correctly; do not use 404 to hide existence unless that is a deliberate anti-enumeration policy.

> Why? Be consistent.
> **Suggestion.**

```python
# bad - random status codes
# good - documented auth error policy
```

## 36.8 Include correlation/request ids in error responses when you have them.

> Why? Support needs handles.
> **Suggestion.**

```python
# bad - uncorrelated errors
# good - error.request_id
```

## 36.9 Write handlers for your top domain errors; avoid one mega handler for Exception that returns 400.

> Why? Catch-all 400 hides outages.
> **Suggestion.**

```python
# bad - except Exception: 400
# good - specific handlers + 500 fallback
```

## 36.10 Do not use assertions for request validation.

> Why? Use Pydantic / HTTPException.
> **Suggestion.**

```python
# bad - assert body.n > 0
# good - Field(gt=0)
```

## 36.11 Ensure background tasks have their own error logging; failures will not reach the client.

> Why? Chapter 37.
> **Suggestion.**

```python
# bad - assume client sees background failure
# good - log/metrics in task
```

## 36.12 Add tests for each mapped domain error status code.

> Why? Prevent regressions in handlers.
> **Suggestion.**

```python
# bad - no tests for 404 mapping
# good - assert response.status_code == 404
```
