<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 29. Cancellation & Timeouts

Cancellation is normal in asyncio. Treat `CancelledError` as control
flow, not as a generic failure to log-and-swallow.

**Tool alignment:** Cancellation guidance is **Suggestion**.

## 29.1 Do not catch broad `Exception` around awaits without re-raising cancellation.

> Why? Swallowing cancel breaks shutdown.
> **Suggestion.**

```python
# bad
try:
  await work()
except Exception:
  return None

# good
try:
  await work()
except asyncio.CancelledError:
  raise
except ValueError:
  return None
```

## 29.2 Use `asyncio.timeout` (3.11+) instead of `wait_for` in new code.

> Why? Timeout contexts compose better.
> **Suggestion.**

```python
# bad
await asyncio.wait_for(work(), timeout=2)

# good
async with asyncio.timeout(2):
  await work()
```

## 29.3 Keep cleanup in `finally` / async context managers so cancel still releases resources.

> Why? Locks and sockets must free.
> **Suggestion.**

```python
# bad - no finally around lock
# good - async with lock:
```

## 29.4 Shield only the tiny critical sections that must complete; never shield whole requests.

> Why? Over-shielding ignores client disconnects.
> **Suggestion.**

```python
# bad - await asyncio.shield(entire_handler())
# good - shield only commit()
```

## 29.5 Document timeout budgets end-to-end (client, gateway, handler, upstream).

> Why? Nested 30s timeouts become minutes.
> **Suggestion.**

```python
# bad - every layer waits 30s
# good - budgeted deadlines
```

## 29.6 On timeout, fail clearly to clients (504/408) with correlation ids.

> Why? Silent hangs are worst.
> **Suggestion.**

```python
# bad - request hangs until worker recycle
# good - timeout -> HTTP 504
```

## 29.7 Do not replace cancellation with infinite retries.

> Why? Retries need budgets/jitter.
> **Suggestion.**

```python
# bad - while True: await call()
# good - bounded retry with timeout
```

## 29.8 Ensure ORM transactions do not stay open across long awaits without a strategy.

> Why? Idle-in-transaction kills pools.
> **Suggestion.**

```python
# bad - await external HTTP inside open transaction
# good - commit/close before slow IO
```

## 29.9 Test cancellation paths, not only happy paths.

> Why? Most production bugs are shutdown bugs.
> **Suggestion.**

```python
# bad - no cancel tests
# good - cancel task mid-await and assert cleanup
```

## 29.10 Prefer cooperative checkpoints in long CPU loops (`await asyncio.sleep(0)`).

> Why? Otherwise cancel cannot land.
> **Suggestion.**

```python
# bad - tight CPU loop in async def
# good - to_thread or periodic await sleep(0)
```

## 29.11 Do not log CancelledError as error at request boundaries unless unexpected.

> Why? Noise trains people to ignore logs.
> **Suggestion.**

```python
# bad - logger.exception on every disconnect cancel
# good - debug/info or silent propagate
```

## 29.12 When using TaskGroup, understand that one failure cancels peers - design idempotency accordingly.

> Why? Partial side effects need compensation.
> **Suggestion.**

```python
# bad - non-idempotent side effects in siblings
# good - idempotent ops / outbox
```
