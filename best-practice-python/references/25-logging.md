<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 25. Logging

[pyguide §3.10.1](https://google.github.io/styleguide/pyguide.html#s3.10.1-logging) requires lazy interpolation for
logging. Prefer structured logs in services.

**Tool alignment:** Logging style is **Suggestion** (no `G`/`LOG` rules enabled).

## 25.1 Use `logging` (or a structured wrapper) rather than `print` for diagnostics.

> Why? Print bypasses levels and aggregation.
> **Suggestion.**

```python
# bad
print('user', user_id)

# good
logger.info('user_login', extra={'user_id': user_id})
```

## 25.2 Use lazy %-style or structured fields; avoid eager f-strings in hot log lines.

> Why? Formatting cost matters under load.
> **Suggestion.**

```python
# bad
logger.info(f'user={user_id}')

# good
logger.info('user=%s', user_id)
```

## 25.3 Name loggers after modules: `logger = logging.getLogger(__name__)`.

> Why? Hierarchy enables filtering.
> **Suggestion.**

```python
# bad
logger = logging.getLogger('app')

# good
logger = logging.getLogger(__name__)
```

## 25.4 Log errors with `logger.exception` inside except blocks.

> Why? Captures stack traces.
> **Suggestion.**

```python
# bad
except Exception as err:
  logger.error(str(err))

# good
except Exception:
  logger.exception('handler failed')
```

## 25.5 Never log secrets, tokens, or raw PII.

> Why? Redact at the source.
> **Suggestion.**

```python
# bad
logger.info('token=%s', token)

# good
logger.info('token_fingerprint=%s', hash_token(token))
```

## 25.6 Prefer structured key/value fields over prose paragraphs.

> Why? Queryable logs beat novels.
> **Suggestion.**

```python
# bad
logger.info(f'User {user} did {action} at {ts}')

# good
logger.info('user_action', extra={'user_id': user, 'action': action})
```

## 25.7 Configure logging in one place (lifespan / dictConfig), not in every module.

> Why? Module-level basicConfig races.
> **Suggestion.**

```python
# bad - basicConfig in library imports
# good - configure in create_app/lifespan
```

## 25.8 Use appropriate levels: debug for diagnostics, info for lifecycle, warning for recoverable, error for failures.

> Why? Everything-as-info is useless.
> **Suggestion.**

```python
# bad - logger.info for stack traces
# good - logger.exception for failures
```

## 25.9 Include request/correlation ids in context for FastAPI services.

> Why? Otherwise incidents are unsearchable.
> **Suggestion.**

```python
# bad - log lines with no request id
# good - bind request_id in middleware/contextvar
```

## 25.10 Do not catch-and-log-and-ignore unless the error is truly optional.

> Why? Logged-and-dropped errors still drop work.
> **Suggestion.**

```python
# bad
except Exception:
  logger.exception('ignored')

# good - re-raise or return explicit fallback
```

## 25.11 Avoid logging entire request bodies by default.

> Why? Size and PII hazards.
> **Suggestion.**

```python
# bad - logger.debug(await request.body())
# good - log route, user, latency, status
```

## 25.12 Test that failure paths emit the log record you claim in runbooks.

> Why? Unlogged failures waste oncall.
> **Suggestion.**

```python
# bad - assume logger.exception exists
# good - caplog assertion in unit test
```
