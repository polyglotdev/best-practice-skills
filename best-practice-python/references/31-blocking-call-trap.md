<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 31. The Blocking-Call Trap

The most common FastAPI performance bug: calling blocking IO or CPU
work directly inside `async def` handlers, stalling the event loop.
Normative treatment is the
[Async Routes](https://github.com/zhanymkanov/fastapi-best-practices#async-routes)
section of fastapi-best-practices: async routes must stay non-blocking;
sync routes run in a threadpool; CPU work needs processes/queues.

**Tool alignment:** Blocking-call guidance is **Suggestion** (enable `ASYNC` later to catch more).

## 31.1 Never call blocking IO in `async def` without a bridge.

> Why? One slow `time.sleep` stalls all requests on the worker.
> **Suggestion.**

```python
# bad
async def handle():
  time.sleep(1)

# good
async def handle():
  await asyncio.sleep(1)
```

## 31.2 Wrap known-blocking stdlib calls with `asyncio.to_thread`.

> Why? Files, subprocess, zipfile often block.
> **Suggestion.**

```python
# bad
async def read():
  return Path('x').read_text()

# good
async def read():
  return await asyncio.to_thread(Path('x').read_text)
```

## 31.3 Do not use sync `requests` in async routes; use `httpx.AsyncClient`.

> Why? requests blocks.
> **Suggestion.**

```python
# bad
requests.get(url)

# good
await client.get(url)
```

## 31.4 Watch ORMs: sync SQLAlchemy in async routes needs `to_thread` or migrate to async Session.

> Why? DB drivers are classic stalls.
> **Suggestion.**

```python
# bad - session.execute in async def
# good - AsyncSession or to_thread
```

## 31.5 Profile with blocking detectors in staging (`blockbuster`, custom middlewares).

> Why? Guessing is insufficient.
> **Suggestion.**

```python
# bad - assume nothing blocks
# good - enable a blocker detector in staging
```

## 31.6 Keep CPU-bound cryptography/image work off the loop.

> Why? Use to_thread/process pool.
> **Suggestion.**

```python
# bad - PIL process in async handler
# good - await asyncio.to_thread(process, image)
```

## 31.7 Avoid sync locks (`threading.Lock`) inside async code; use `asyncio.Lock`.

> Why? Sync locks block the loop thread.
> **Suggestion.**

```python
# bad
lock = threading.Lock()
async def handle():
  with lock:
    ...

# good
lock = asyncio.Lock()
async def handle():
  async with lock:
    ...
```

## 31.8 Treat `run_until_complete` / nested loops as a smell in libraries.

> Why? Callers own the loop.
> **Suggestion.**

```python
# bad - library calls asyncio.run
# good - expose async API; let app await
```

## 31.9 Document sync parts of hybrid codebases clearly.

> Why? Surprises cause stalls.
> **Suggestion.**

```python
# bad - async facade over sync-only client undocumented
# good - docstring: blocking; use to_thread
```

## 31.10 Prefer async SDKs when available rather than wrapping everything.

> Why? Wrappers still occupy threads.
> **Suggestion.**

```python
# bad - to_thread every AWS call forever
# good - aiobotocore/async SDK where viable
```

## 31.11 Load-test event-loop lag, not only RPS.

> Why? Healthy RPS can hide 95p stalls.
> **Suggestion.**

```python
# bad - only measure throughput
# good - track event loop delay metrics
```

## 31.12 In reviews, treat new sync IO in `async def` as a defect until proven bridged.

> Why? Default deny.
> **Suggestion.**

```python
# bad - 'we'll optimize later'
# good - bridge or make sync def route deliberately
```
