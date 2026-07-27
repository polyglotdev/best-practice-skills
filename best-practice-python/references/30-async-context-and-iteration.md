<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 30. Async Context Managers & Iteration

`async with` and `async for` are the resource and streaming primitives
for asyncio code.

**Tool alignment:** Async context/iteration guidance is **Suggestion**.

## 30.1 Use `async with` for async resources (DB sessions, HTTP clients, locks).

> Why? Manual close races cancel.
> **Suggestion.**

```python
# bad
session = await open_session()
...
await session.close()

# good
async with open_session() as session:
  ...
```

## 30.2 Implement `__aenter__`/`__aexit__` or `@asynccontextmanager` for custom resources.

> Why? Sync context managers are not enough.
> **Suggestion.**

```python
# bad - sync __enter__ around async client
# good - @asynccontextmanager async def client():
```

## 30.3 Use FastAPI lifespan (`asynccontextmanager`) for app startup/shutdown.

> Why? Deprecated `@app.on_event` is legacy.
> **Suggestion.**

```python
# bad
@app.on_event('startup')
async def start():
  ...

# good - lifespan context manager
```

## 30.4 Prefer `async for` when iterating async streams / cursors.

> Why? Materializing loses streaming benefits.
> **Suggestion.**

```python
# bad
rows = [row async for row in cursor]

# good
async for row in cursor:
  await handle(row)
```

## 30.5 Do not hold app-global async generators open across requests.

> Why? Generators carry connection state.
> **Suggestion.**

```python
# bad - module-level async gen reused
# good - per-request iteration
```

## 30.6 Close async generators with `aclose()` when abandoning early.

> Why? Otherwise cleanup stalls.
> **Suggestion.**

```python
# bad - break out and drop gen
# good - aclose in finally
```

## 30.7 Keep async context manager enter/exit fast; do heavy work in explicit methods.

> Why? Enter should not hide latency.
> **Suggestion.**

```python
# bad - __aenter__ downloads 100MB
# good - async with client; await client.download()
```

## 30.8 Nest async with carefully; prefer AsyncExitStack for dynamic sets.

> Why? Variable depth needs a stack.
> **Suggestion.**

```python
# bad - manually nested N clients
# good - AsyncExitStack
```

## 30.9 Do not mix sync `with` around blocking close methods on the event loop thread.

> Why? Use async close or to_thread.
> **Suggestion.**

```python
# bad - with blocking_lock inside async def
# good - asyncio.Lock
```

## 30.10 Annotate async iterators as `AsyncIterator[T]`.

> Why? Types document streaming contracts.
> **Suggestion.**

```python
# bad
async def stream(events):
  ...

# good
async def stream(events: AsyncIterable[Event]) -> AsyncIterator[Event]:
  async for event in events:
    yield event
```

## 30.11 For SSE/streaming responses, ensure cancellation closes upstream iterators.

> Why? Client disconnect must free servers.
> **Suggestion.**

```python
# bad - ignore disconnect
# good - finally/aclose on disconnect
```

## 30.12 Test lifespan startup failure (DB down) fails fast.

> Why? Half-booted apps are dangerous.
> **Suggestion.**

```python
# bad - swallow startup errors
# good - let lifespan raise
```
