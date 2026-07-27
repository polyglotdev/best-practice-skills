<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 37. Background Tasks

FastAPI `BackgroundTasks` are for short after-response work on the
same worker. Per
[BackgroundTasks vs a real task queue](https://github.com/zhanymkanov/fastapi-best-practices#backgroundtasks-vs-a-real-task-queue),
they are not durable job infrastructure.

**Tool alignment:** Background-task guidance is **Suggestion**.

## 37.1 Use BackgroundTasks for short, reliable, in-process work only.

> Why? Email to a flaky SMTP may need a queue.
> **Suggestion.**

```python
# bad - video encoding in BackgroundTasks
# good - enqueue to worker
```

## 37.2 Do not pass ORM attached instances into background tasks.

> Why? Sessions close before tasks run.
> **Suggestion.**

```python
# bad - tasks.add_task(send, user_orm)
# good - tasks.add_task(send, user_id)
```

## 37.3 Prefer explicit job queues (RQ/Celery/Arq/NATS) for retries and durability.

> Why? Process death drops BackgroundTasks.
> **Suggestion.**

```python
# bad - payment capture in BackgroundTasks
# good - durable outbox/queue
```

## 37.4 Log start/finish/failure inside background callables.

> Why? Otherwise silent loss.
> **Suggestion.**

```python
# bad - task without logging
# good - try/except logger.exception
```

## 37.5 Keep task functions sync or async deliberately; know FastAPI scheduling rules.

> Why? Blocking tasks stall workers.
> **Suggestion.**

```python
# bad - blocking heavy work in sync background task
# good - queue or async+to_thread
```

## 37.6 Do not rely on BackgroundTasks for work that must complete before responding.

> Why? It runs after the response.
> **Suggestion.**

```python
# bad - audit write needed for compliance after response with no durability
# good - await audit or durable outbox
```

## 37.7 Pass settings/deps explicitly into tasks; do not assume request-scoped context remains.

> Why? Contextvars may be gone.
> **Suggestion.**

```python
# bad - task reads request contextvar
# good - pass request_id arg
```

## 37.8 Bound fan-out of tasks per request.

> Why? Easy DoS against yourself.
> **Suggestion.**

```python
# bad - 1000 background tasks per request
# good - one enqueue batch job
```

## 37.9 Document the durability story for each background call site.

> Why? Reviewers need to know loss tolerance.
> **Suggestion.**

```python
# bad - unexplained add_task
# good - comment: best-effort metrics only
```

## 37.10 Test background work by invoking the callable directly; do not only assert 200.

> Why? Response success != task success.
> **Suggestion.**

```python
# bad - only assert status 200
# good - assert task side effect / call args
```

## 37.11 Avoid capturing `Request` in tasks.

> Why? Lifecycle ends.
> **Suggestion.**

```python
# bad - add_task(fn, request)
# good - extract needed values first
```

## 37.12 Consider `after_response` patterns via ASGI middleware carefully; prefer obvious BackgroundTasks or queues.

> Why? Cleverness ages poorly.
> **Suggestion.**

```python
# bad - hidden middleware side effects
# good - explicit tasks/queue
```
