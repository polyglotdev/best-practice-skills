<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->

# 20. Dates & Times

Always be explicit about timezones. Prefer aware datetimes and store UTC.

**Tool alignment:** Datetime rules are **Suggestion** (no `DTZ` enabled in shipped select).

## 20.1 Prefer timezone-aware datetimes; ban naive datetimes at boundaries.

> Why? Naive datetimes are ambiguous.
> **Suggestion.**

```python
# bad
datetime.now()

# good
datetime.now(UTC)
```

## 20.2 Store and transmit UTC; convert to local zones only at the UI edge.

> Why? Server-local time is not a format.
> **Suggestion.**

```python
# bad - store America/New_York in DB
# good - store UTC, convert on display
```

## 20.3 Use `datetime.UTC` (3.11+) instead of `timezone.utc` in new code.

> Why? Shorter and canonical.
> **Suggestion.**

```python
# bad
from datetime import timezone
datetime.now(timezone.utc)

# good
from datetime import UTC
datetime.now(UTC)
```

## 20.4 Do not use `datetime.utcnow()`; it returns naive UTC.

> Why? Deprecated footgun.
> **Suggestion.**

```python
# bad
datetime.utcnow()

# good
datetime.now(UTC)
```

## 20.5 Prefer `date` when the value has no time component.

> Why? Fake midnights create DST bugs.
> **Suggestion.**

```python
# bad
birthday = datetime(1990, 1, 1, tzinfo=UTC)

# good
birthday = date(1990, 1, 1)
```

## 20.6 Use `timedelta` for durations; do not invent second-int APIs without units in the name.

> Why? Units belong in names (`timeout_s`).
> **Suggestion.**

```python
# bad
sleep(5)  # minutes or seconds?

# good
sleep(timedelta(seconds=5).total_seconds())
```

## 20.7 Serialize with ISO 8601 (`datetime.isoformat` / `date.fromisoformat`).

> Why? Custom formats break clients.
> **Suggestion.**

```python
# bad
ts.strftime('%m/%d/%Y')

# good
ts.isoformat()
```

## 20.8 Parse external timestamps with explicit zone handling.

> Why? Reject ambiguous inputs.
> **Suggestion.**

```python
# bad - assume local
# good - fromisoformat and require tzinfo
```

## 20.9 Do not compare aware and naive datetimes.

> Why? Python raises (or worse, in older code paths).
> **Suggestion.**

```python
# bad
aware > naive

# good - normalize both sides
```

## 20.10 Use monotonic clocks (`time.monotonic`) for measuring durations.

> Why? Wall clocks jump.
> **Suggestion.**

```python
# bad
start = time.time()
...
elapsed = time.time() - start

# good
start = time.monotonic()
...
elapsed = time.monotonic() - start
```

## 20.11 Keep cron/business calendars in well-tested helpers; do not sprinkle DST math.

> Why? Calendar math is a library problem.
> **Suggestion.**

```python
# bad - hand-rolled DST adjust
# good - zoneinfo / trusted library
```

## 20.12 In Pydantic models, prefer `datetime` fields with aware values and configure JSON encoders consistently.

> Why? See chapter 35.
> **Suggestion.**

```python
# bad - str timestamps mixed with datetime fields
# good - datetime fields throughout
```
