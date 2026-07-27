<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 27. Asyncio Fundamentals

Asyncio is the concurrency model for FastAPI. Know the event loop,
`async def`, awaitables, and when not to use async at all.

**Tool alignment:** Async rules are **Suggestion** under the shipped select (no `ASYNC`).

## 27.1 Only use `async def` when the function awaits something (or is a required framework signature).

> Why? Async without awaits is overhead and lies.
> **Suggestion.**

```python
# bad
async def add(a: int, b: int) -> int:
  return a + b

# good
def add(a: int, b: int) -> int:
  return a + b
```

## 27.2 Await every coroutine you create; do not fire-and-forget without an owned task.

> Why? Unawaited coroutines warn and drop work.
> **Suggestion.**

```python
# bad
async def handle():
  send_email(user)  # forgot await

# good
async def handle():
  await send_email(user)
```

## 27.3 Do not call `asyncio.run` from inside a running loop.

> Why? Nested run breaks servers/tests.
> **Suggestion.**

```python
# bad - asyncio.run inside FastAPI handler
# good - await directly
```

## 27.4 Prefer `asyncio.TaskGroup` (3.11+) over ad-hoc `gather` for sibling tasks.

> Why? See chapter 28.
> **Suggestion.**

```python
# bad - create_task without supervision
# good - TaskGroup
```

## 27.5 Keep CPU-bound work off the loop (`asyncio.to_thread` / process pool).

> Why? CPU loops starve IO.
> **Suggestion.**

```python
# bad
async def handler():
  return crunch(data)

# good
async def handler():
  return await asyncio.to_thread(crunch, data)
```

## 27.6 Use timeout APIs deliberately (`asyncio.timeout`).

> Why? Hung awaits need bounds.
> **Suggestion.**

```python
# bad - await forever
# good
async with asyncio.timeout(2):
  await upstream()
```

## 27.7 Do not mix blocking clients (`requests`) into async handlers.

> Why? Use httpx/async SDK or to_thread.
> **Suggestion.**

```python
# bad
async def get():
  return requests.get(url).json()

# good
async def get(client: httpx.AsyncClient):
  response = await client.get(url)
  return response.json()
```

## 27.8 Cancel scopes intentionally; do not ignore `CancelledError`/`BaseException`.

> Why? See chapter 29.
> **Suggestion.**

```python
# bad
except Exception:
  pass

# good - let cancellation propagate
```

## 27.9 Create one shared `httpx.AsyncClient` / DB pool per app, not per request.

> Why? Connection storms follow per-request clients.
> **Suggestion.**

```python
# bad - AsyncClient() inside every handler
# good - lifespan-managed client on app.state
```

## 27.10 Annotate async functions with the real return type, not `Coroutine[...]` at user APIs.

> Why? Callers await and get T.
> **Suggestion.**

```python
# bad
async def load() -> Coroutine[Any, Any, User]:
  ...

# good
async def load() -> User:
  ...
```

## 27.11 Prefer async libraries end-to-end once a path is async.

> Why? Sync islands need explicit bridges.
> **Suggestion.**

```python
# bad - async route calling sync ORM without to_thread
# good - async ORM or to_thread boundary
```

## 27.12 Write deterministic async tests with pytest-asyncio (chapter 38).

> Why? Real sleeps make flakes.
> **Suggestion.**

```python
# bad - time.sleep in async test
# good - await asyncio.sleep(0) / fake clock
```
