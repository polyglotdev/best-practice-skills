<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 28. Structured Concurrency

`asyncio.TaskGroup` (Python 3.11+) is the default way to run sibling
tasks with proper lifetimes and error propagation.

**Tool alignment:** Structured concurrency guidance is **Suggestion**.

## 28.1 Prefer `TaskGroup` over bare `create_task` for request-scoped fan-out.

> Why? Owned lifetimes cancel cleanly.
> **Suggestion.**

```python
# bad
asyncio.create_task(fetch_a())
asyncio.create_task(fetch_b())

# good
async with asyncio.TaskGroup() as group:
  a = group.create_task(fetch_a())
  b = group.create_task(fetch_b())
```

## 28.2 Let TaskGroup cancel siblings when one fails; do not swallow the first error.

> Why? Half-success states are worse.
> **Suggestion.**

```python
# bad - gather(return_exceptions=True) then ignore
# good - TaskGroup default failure propagation
```

## 28.3 Do not use `asyncio.gather` with `return_exceptions=True` as a silent best-effort default.

> Why? Make partial failure explicit.
> **Suggestion.**

```python
# bad
results = await asyncio.gather(*tasks, return_exceptions=True)

# good - TaskGroup or explicit per-task error policy
```

## 28.4 Keep task bodies small and named; avoid giant closures capturing mutable state.

> Why? Hard to debug races.
> **Suggestion.**

```python
# bad - closure mutates shared list without sync
# good - return values from tasks and merge
```

## 28.5 Bound fan-out size; do not create unbounded tasks per request.

> Why? Task storms kill the loop.
> **Suggestion.**

```python
# bad - one task per row in unbounded query
# good - chunk / semaphore
```

## 28.6 Use semaphores for concurrency limits against upstreams.

> Why? Respect neighbor services.
> **Suggestion.**

```python
# bad - 10k concurrent upstream calls
# good - asyncio.Semaphore(n)
```

## 28.7 Do not store tasks on globals without ownership.

> Why? Orphans outlive requests.
> **Suggestion.**

```python
# bad - module-level set of tasks
# good - app.state workers managed by lifespan
```

## 28.8 Propagate request context (ids) into tasks explicitly.

> Why? Contextvars may need copying.
> **Suggestion.**

```python
# bad - child task loses request_id
# good - pass request_id into task args
```

## 28.9 Prefer returning values from tasks over mutating shared structures.

> Why? Join by results.
> **Suggestion.**

```python
# bad - tasks append to shared list
# good - results = [t.result() for t in tasks]
```

## 28.10 Cancel owned tasks on request timeout/cancellation.

> Why? Chapter 29.
> **Suggestion.**

```python
# bad - background work continues after client disconnect with no policy
# good - document and enforce cancellation policy
```

## 28.11 Use `asyncio.Barrier`/`Event` sparingly; prefer dataflow via results.

> Why? Coordination primitives hide design issues.
> **Suggestion.**

```python
# bad - complex event choreography
# good - TaskGroup results
```

## 28.12 Test failure injection: one sibling raises and others cancel.

> Why? Prove structure works.
> **Suggestion.**

```python
# bad - only happy-path gather tests
# good - unit test TaskGroup cancellation behavior
```
