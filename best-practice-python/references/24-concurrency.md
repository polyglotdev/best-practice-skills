<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 24. Concurrency

[pyguide §2.18](https://google.github.io/styleguide/pyguide.html#s2.18-threading) is brief: threads need care.
Prefer asyncio for IO-bound FastAPI services; use threads/processes
deliberately for blocking or CPU work.

**Tool alignment:** Concurrency guidance is **Suggestion**.

## 24.1 Do not share mutable state across threads without locks or queues.

> Why? Races are silent.
> **Suggestion.**

```python
# bad - global counter += 1 from threads
# good - queue workers or asyncio
```

## 24.2 Prefer `concurrent.futures` over raw `ThreadPoolExecutor` management when bridging blocking IO.

> Why? Clear lifecycle.
> **Suggestion.**

```python
# bad - hand-managed threads
# good - asyncio.to_thread / run_in_executor
```

## 24.3 Never call blocking IO directly inside async request handlers.

> Why? See chapter 31.
> **Suggestion.**

```python
# bad
async def get():
  return Path('x').read_text()

# good
async def get():
  return await asyncio.to_thread(Path('x').read_text)
```

## 24.4 Use processes (or native extensions) for CPU-bound work, not threads, because of the GIL.

> Why? Threads will not speed pure Python CPU loops.
> **Suggestion.**

```python
# bad - ThreadPool for CPU crunch
# good - ProcessPoolExecutor or a worker service
```

## 24.5 Give every thread/task a clear owner and shutdown path.

> Why? Orphan workers hang exits.
> **Suggestion.**

```python
# bad - fire thread and forget
# good - lifespan starts/stops workers
```

## 24.6 Prefer immutable messages over shared objects between workers.

> Why? Queues of values beat shared graphs.
> **Suggestion.**

```python
# bad - pass live ORM object across threads
# good - pass ids/DTOs
```

## 24.7 Do not ignore `threading`/`asyncio` cancellation semantics when shutting down.

> Why? Clean flush matters.
> **Suggestion.**

```python
# bad - os._exit from worker
# good - cooperative shutdown event
```

## 24.8 Avoid `time.sleep` in async code; use `asyncio.sleep`.

> Why? Sleep blocks the event loop.
> **Suggestion.**

```python
# bad
awaitable = time.sleep(1)

# good
await asyncio.sleep(1)
```

## 24.9 Document thread-safety of public helpers.

> Why? Callers cannot guess.
> **Suggestion.**

```python
# bad - silent non-thread-safe cache
# good - docstring: not thread-safe
```

## 24.10 Prefer one concurrency model per service: asyncio-first for FastAPI.

> Why? Mixing models needs explicit bridges.
> **Suggestion.**

```python
# bad - threads + asyncio + processes ad hoc
# good - asyncio core; to_thread at edges
```

## 24.11 Protect caches with locks or use asyncio-safe structures.

> Why? Torn reads produce ghosts.
> **Suggestion.**

```python
# bad - dict cache from many tasks without care
# good - dedicated cache with locking or Redis
```

## 24.12 Do not daemonize threads to avoid writing shutdown code.

> Why? Daemon threads drop work on exit.
> **Suggestion.**

```python
# bad - Thread(daemon=True) for billing
# good - managed worker with flush
```
