<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 25. Time

Time-related bugs are disproportionately expensive because they are
timezone- and load-dependent, and often invisible in a developer's local
environment. This chapter follows the Uber Go Style Guide's [Use "time" to
handle
time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time)
section, the only one of our three sources with dedicated time guidance.
Its central idea is to let the type system distinguish instants from
durations rather than encoding both as bare integers. See [Chapter
23](23-goroutines-and-lifecycle.md) for how timers interact with goroutine
lifecycles and cancellation.

## 25.1 Represent an instant in time with `time.Time`, never with an integer count of seconds or milliseconds.

> Why? An `int64` of "seconds since epoch" carries no information about
> which epoch, which unit, or which timezone was intended, and arithmetic
> on it is easy to get wrong. [Uber Style: Use "time" to handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time)
> calls for `time.Time` specifically so the compiler and the standard
> library carry that information for you.

> Enforced by: revive `time-naming` (flags fields/vars typed `time.Time` or `time.Duration` whose names don't match their type's convention; see [Chapter 33.2](33-linter-configuration.md))

```go
// bad — an int64 could be seconds, millis, or nanos; nothing enforces which
type Session struct {
	CreatedAtUnix int64
}

func isExpired(s Session, ttlSeconds int64) bool {
	return time.Now().Unix()-s.CreatedAtUnix > ttlSeconds
}

// good — time.Time and time.Duration make the units unambiguous
type Session struct {
	CreatedAt time.Time
}

func isExpired(s Session, ttl time.Duration) bool {
	return time.Since(s.CreatedAt) > ttl
}
```

## 25.2 Represent a span of time with `time.Duration`, never with a bare integer of an assumed unit.

> Why? [Uber Style: Use "time" to handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time)
> notes that a plain integer duration forces every caller to remember
> which unit the API uses; `time.Duration` is self-documenting and
> supports arithmetic and comparison directly.

> Enforced by: revive `time-naming` (see [Chapter 33.2](33-linter-configuration.md))

```go
// bad — callers must know this is milliseconds by reading the doc comment
func Poll(intervalMs int) {
	for {
		time.Sleep(time.Duration(intervalMs) * time.Millisecond)
		check()
	}
}

// good — the type itself carries the unit
func Poll(interval time.Duration) {
	for {
		time.Sleep(interval)
		check()
	}
}
```

## 25.3 Never accept or return `int64` seconds/millis in a public API when `time.Time`/`time.Duration` will do.

> Why? Once an integer-based time API ships, every caller bakes in an
> assumption about units that cannot be changed without breaking them.
> [Uber Style: Use "time" to handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time)
> treats `time.Time`/`time.Duration` in public signatures as the default,
> reserving integers for wire formats that require them.

```go
// bad — public API takes and returns raw epoch millis
func (c *Client) SetDeadline(unixMillis int64) {
	c.deadline = unixMillis
}

func (c *Client) Deadline() int64 {
	return c.deadline
}

// good — public API speaks in time.Time
func (c *Client) SetDeadline(t time.Time) {
	c.deadline = t
}

func (c *Client) Deadline() time.Time {
	return c.deadline
}
```

## 25.4 Call `time.Now()` only from production code paths; inject a clock abstraction so tests control the current time.

> Why? Tests that call `time.Now()` directly are flaky by construction —
> they race against the wall clock and can't exercise edge cases like
> "exactly at expiry." [Uber Style: Use "time" to handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time)
> recommends injecting time as a dependency so it can be replaced with a
> fake in tests.

```go
// bad — Session.IsExpired is untestable without sleeping in real time
func (s *Session) IsExpired(ttl time.Duration) bool {
	return time.Since(s.CreatedAt) > ttl
}

// good — now is injected, so tests can supply a fixed clock
type nowFunc func() time.Time

func (s *Session) IsExpired(now nowFunc, ttl time.Duration) bool {
	return now().Sub(s.CreatedAt) > ttl
}
```

## 25.5 Use `time.NewTimer` with an explicit `Stop`, not a bare `time.After`, inside loops or `select` statements that may run many times.

> Why? Each call to `time.After` allocates a `Timer` that is not garbage
> collected until it fires, even if the surrounding `select` picks a
> different case. In a loop, this leaks one live timer per iteration.
> [Uber Style: Use "time" to handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time)
> calls out this exact leak and recommends `time.NewTimer` plus `Stop`
> instead.

```go
// bad — a new, unstoppable timer is allocated on every loop iteration
func poll(ctx context.Context, ch <-chan Event) {
	for {
		select {
		case e := <-ch:
			handle(e)
		case <-time.After(5 * time.Second):
			log.Println("no event in 5s")
		case <-ctx.Done():
			return
		}
	}
}

// good — one timer, reset each iteration, stopped on exit
func poll(ctx context.Context, ch <-chan Event) {
	timer := time.NewTimer(5 * time.Second)
	defer timer.Stop()

	for {
		if !timer.Stop() {
			<-timer.C
		}
		timer.Reset(5 * time.Second)

		select {
		case e := <-ch:
			handle(e)
		case <-timer.C:
			log.Println("no event in 5s")
		case <-ctx.Done():
			return
		}
	}
}
```

## 25.6 Rely on `time.Now()`'s monotonic reading for measuring elapsed durations; never derive elapsed time by subtracting two wall-clock timestamps read from storage.

> Why? `time.Time` values returned by `time.Now()` carry a monotonic clock
> reading specifically so that `time.Since`/`Sub` are immune to
> wall-clock adjustments like NTP corrections or manual clock changes.
> Timestamps that have been serialized (to a database, JSON, or a log
> line) lose the monotonic reading, so subtracting two of those can go
> backward if the wall clock was adjusted in between.

```go
// bad — timestamps loaded from storage have no monotonic reading;
// elapsed can go negative across an NTP adjustment
start := loadStartTime(db)
elapsed := time.Now().Sub(start)

// good — measure elapsed time from an in-process time.Now() call
start := time.Now()
doWork()
elapsed := time.Since(start)
```

## 25.7 Marshal and parse timestamps as RFC 3339 strings, not as custom formats or bare Unix integers.

> Why? RFC 3339 is unambiguous about timezone offset, is what
> `time.Time`'s `MarshalJSON` already produces, and is directly parseable
> by `time.Parse(time.RFC3339, ...)`. Custom string formats or naked
> integers require every consumer to reimplement parsing correctly,
> including timezone handling — a common source of off-by-hours bugs.

```go
// bad — custom format loses the timezone and needs bespoke parsing
type Event struct {
	OccurredAt string `json:"occurred_at"` // "2026-07-27 13:37:00"
}

// good — time.Time marshals to RFC 3339 automatically
type Event struct {
	OccurredAt time.Time `json:"occurred_at"`
}
```

## 25.8 Truncate or round `time.Time` values explicitly when comparing for equality; never compare wall-clock timestamps with `==` across serialization boundaries.

> Why? `time.Time` carries a monotonic component, a wall-clock component,
> and a location pointer, and `==` compares all of them field-by-field.
> Two `time.Time` values representing "the same instant" can compare
> unequal if one has a monotonic reading and the other does not (for
> example, after a round trip through JSON). The standard library's
> `Equal` method compares instants, not internal representation.

```go
// bad — == can report two equal instants as different
func sameInstant(a, b time.Time) bool {
	return a == b
}

// good — Equal compares the instant, ignoring monotonic/location differences
func sameInstant(a, b time.Time) bool {
	return a.Equal(b)
}
```

## 25.9 Use `context.WithTimeout`/`context.WithDeadline` to bound operations, not manual `time.Sleep` polling loops.

> Why? A hand-written sleep-and-check loop duplicates what `context`
> already does atomically, and it doesn't compose with cancellation from
> callers the way a `context.Context` deadline does. This follows the
> same "let the standard library own time-based coordination" principle
> as [Uber Style: Use "time" to handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time).

```go
// bad — hand-rolled polling loop with a magic sleep interval
func waitForReady(check func() bool, timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if check() {
			return true
		}
		time.Sleep(50 * time.Millisecond)
	}
	return false
}

// good — context.WithTimeout composes with cancellation and is explicit
func waitForReady(ctx context.Context, check func() bool, timeout time.Duration) bool {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop()

	for {
		if check() {
			return true
		}
		select {
		case <-ticker.C:
		case <-ctx.Done():
			return false
		}
	}
}
```

## 25.10 Store and compare durations with `time.Duration` arithmetic, not by converting to `float64` seconds.

> Why? Converting to `float64` introduces floating-point rounding error
> and throws away the compiler's unit safety that motivated using
> `time.Duration` in the first place, per [Uber Style: Use "time" to
> handle
> time](https://github.com/uber-go/guide/blob/master/style.md#use-time-to-handle-time).

```go
// bad — float64 seconds loses precision and type safety
func retryDelay(attempt int) float64 {
	return 0.1 * float64(attempt) // seconds, as a float
}

// good — time.Duration arithmetic stays exact and typed
func retryDelay(attempt int) time.Duration {
	return 100 * time.Millisecond * time.Duration(attempt)
}
```

## 25.11 Name `time.Duration` variables with a duration-shaped suffix (`timeout`, `retryInterval`, `pollPeriod`), and never give a `time.Time` variable a duration-shaped name.

> Why? A variable named `timeout` that actually holds a `time.Time`
> deadline, or a variable named `startTime` that actually holds a
> `time.Duration`, misleads every reader who has to check the
> declaration to know what arithmetic is even valid on it. `revive`'s
> `time-naming` rule enforces this naming convention mechanically so
> reviewers don't have to catch it by hand.

> Enforced by: revive `time-naming` (see [Chapter 33.2](33-linter-configuration.md))

```go
// bad — a Duration named like an instant, and vice versa
type Client struct {
	requestTimeoutAt time.Duration // reads like a Time, holds a Duration
	retryInterval    time.Time     // reads like a Duration, holds a Time
}

// good — the name matches what the type actually represents
type Client struct {
	requestTimeout time.Duration
	nextRetryAt    time.Time
}
```
