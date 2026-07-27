<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 26. Logging

Logging is one of the few things a library or service does that is
explicitly *not* part of its type-checked contract, which is exactly why
[Google Best Practices:
Logging](https://google.github.io/styleguide/go/best-practices#logging)
devotes a section to disciplining it. This chapter uses `log/slog`, the
structured logger that shipped in the standard library in Go 1.21, as the
default logging idiom throughout. See [Chapter
16](16-error-handling.md)-style error-wrapping guidance (referenced, not
restated) for the related "log or return, never both" rule as it applies
to error propagation specifically.

## 26.1 Use `log/slog` for structured logging instead of `fmt.Println`/`log.Println`-style unstructured output.

> Why? [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> favors log output that downstream systems can parse and query.
> `log/slog` attaches typed key-value attributes to every record instead
> of embedding values in a free-form string that has to be parsed back
> out later.

```go
// bad — unstructured message; fields must be parsed out of a string later
log.Printf("user %d logged in from %s", userID, ip)

// good — structured attributes are queryable without string parsing
slog.Info("user logged in", "user_id", userID, "ip", ip)
```

## 26.2 Never call logging functions from library (non-`main`) packages; return an error and let the caller decide whether and how to log it.

> Why? A library that logs on its own has no idea whether the caller is a
> CLI tool, a server, or another library — and duplicate logging happens
> when both the library and its caller log the same failure. [Google Best
> Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> states that only `main` packages and a small set of designated
> top-level handlers should own logging decisions.

```go
// bad — a library package logs directly, out of the caller's control
package storage

func (s *Store) Get(id string) (*Record, error) {
	rec, err := s.db.Query(id)
	if err != nil {
		log.Printf("storage: query failed: %v", err) // caller can't suppress or redirect this
		return nil, err
	}
	return rec, nil
}

// good — the library returns an error; the caller (main-adjacent code) logs it
package storage

func (s *Store) Get(id string) (*Record, error) {
	rec, err := s.db.Query(id)
	if err != nil {
		return nil, fmt.Errorf("query record %q: %w", id, err)
	}
	return rec, nil
}
```

## 26.3 Either log an error or return it — never both at the same call site.

> Why? Logging and returning the same error means it gets recorded once
> for every layer that both logs and re-propagates it, producing many log
> lines for a single failure and making incident logs noisy and
> misleading. [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> treats "log xor return" as the rule that keeps one failure to one log
> line, emitted by whichever layer actually stops propagating it.

```go
// bad — every layer up the call stack logs the same underlying error again
func (s *Service) Process(ctx context.Context, id string) error {
	rec, err := s.store.Get(id)
	if err != nil {
		slog.Error("failed to get record", "id", id, "err", err)
		return err // caller will likely log this same error again
	}
	return s.handle(rec)
}

// good — only the layer that stops propagating the error logs it
func (s *Service) Process(ctx context.Context, id string) error {
	rec, err := s.store.Get(id)
	if err != nil {
		return fmt.Errorf("get record %q: %w", id, err)
	}
	return s.handle(rec)
}

// at the top-level handler, the final consumer logs once
func handleRequest(ctx context.Context, svc *Service, id string) {
	if err := svc.Process(ctx, id); err != nil {
		slog.Error("process failed", "id", id, "err", err)
	}
}
```

## 26.4 Choose the log level deliberately: `Debug` for developer diagnostics, `Info` for expected operational events, `Warn` for recoverable anomalies, `Error` for failures that need attention.

> Why? [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> notes that undisciplined level choice — everything at `Info`, or
> routine events at `Error` — trains operators to ignore alerts or
> obscures real incidents in noise.

```go
// bad — a routine cache miss logged at Error triggers false alarms
func (c *Cache) Get(key string) (string, bool) {
	v, ok := c.data[key]
	if !ok {
		slog.Error("cache miss", "key", key)
	}
	return v, ok
}

// good — level matches severity; a cache miss is expected, not an error
func (c *Cache) Get(key string) (string, bool) {
	v, ok := c.data[key]
	if !ok {
		slog.Debug("cache miss", "key", key)
	}
	return v, ok
}
```

## 26.5 Pass structured attributes as key-value pairs, not interpolated into the message with `fmt.Sprintf`.

> Why? Interpolating values into the message string defeats the purpose
> of a structured logger: the resulting field is unqueryable text again.
> [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> expects call sites to hand values to the logger as attributes so the
> logging backend can index them.

```go
// bad — order ID is baked into the message string
slog.Info(fmt.Sprintf("processing order %s for user %d", orderID, userID))

// good — order ID and user ID are separate, queryable attributes
slog.Info("processing order", "order_id", orderID, "user_id", userID)
```

## 26.6 Use `slog.With` to attach request- or operation-scoped context once, instead of repeating the same attributes on every log call.

> Why? Repeating `"request_id", reqID` on every call site is error-prone
> — one call site will eventually be missed — and clutters each call.
> `slog.With` returns a logger that carries those attributes on every
> subsequent call, which keeps the correlating fields consistent for the
> life of the request.

```go
// bad — request_id must be remembered and repeated at every call site
func handle(reqID string, userID int) {
	slog.Info("start", "request_id", reqID, "user_id", userID)
	if err := doWork(userID); err != nil {
		slog.Error("work failed", "request_id", reqID, "user_id", userID, "err", err)
		return
	}
	slog.Info("done", "request_id", reqID, "user_id", userID)
}

// good — slog.With binds the shared attributes once
func handle(reqID string, userID int) {
	logger := slog.With("request_id", reqID, "user_id", userID)
	logger.Info("start")
	if err := doWork(userID); err != nil {
		logger.Error("work failed", "err", err)
		return
	}
	logger.Info("done")
}
```

## 26.7 Never log sensitive data — auth tokens, passwords, full payment details, or other PII — even at `Debug` level.

> Why? Log storage is typically less access-controlled and retained
> longer than the primary datastore, so sensitive values written to logs
> become a durable secondary copy that is much easier to leak. [Google
> Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> calls out avoiding sensitive data in logs as a security requirement, not
> a style preference.

```go
// bad — the bearer token ends up in every log aggregator and log file
slog.Debug("authenticating request", "authorization_header", req.Header.Get("Authorization"))

// good — log identifying, non-sensitive context instead
slog.Debug("authenticating request", "user_id", claims.UserID, "auth_scheme", "bearer")
```

## 26.8 Include the error itself as a structured attribute (`"err", err`), not folded into the message text.

> Why? A structured `err` attribute lets log tooling group, filter, and
> alert on error type or message independent of the surrounding text,
> consistent with [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)'s
> preference for structured fields over free-form strings.

```go
// bad — error text is concatenated into the message
slog.Error(fmt.Sprintf("failed to save user: %v", err))

// good — err is a distinct, queryable attribute
slog.Error("failed to save user", "err", err)
```

## 26.9 Configure the log level and handler (text vs. JSON) once at program startup, not per call site.

> Why? Scattering `if debugEnabled { slog.Debug(...) }` checks or handler
> construction throughout the codebase makes log configuration
> inconsistent and hard to change centrally. [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> expects the logging configuration — level, format, destination — to be
> a single decision made where the program starts.

```go
// bad — every package builds its own handler with its own settings
package worker

var logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))

// good — main configures the default logger once; packages use slog's package-level functions
func main() {
	level := slog.LevelInfo
	if os.Getenv("DEBUG") == "1" {
		level = slog.LevelDebug
	}
	handler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: level})
	slog.SetDefault(slog.New(handler))

	run()
}
```

## 26.10 Do not use logging as a substitute for metrics or tracing; log discrete events, not high-frequency per-iteration noise.

> Why? [Google Best Practices:
> Logging](https://google.github.io/styleguide/go/best-practices#logging)
> distinguishes logs (discrete, human-readable events for debugging) from
> metrics (aggregated counters and histograms) and traces (request-scoped
> timing). Logging inside a tight loop produces volume that drowns out
> genuinely actionable log lines and belongs in a counter instead.

```go
// bad — one log line per item in a large batch floods the log stream
func processBatch(items []Item) {
	for _, it := range items {
		slog.Info("processing item", "id", it.ID)
		process(it)
	}
}

// good — a single summary log line; per-item counts go to metrics
func processBatch(items []Item) {
	var failed int
	for _, it := range items {
		if err := process(it); err != nil {
			failed++
			itemsFailedCounter.Add(1)
		}
	}
	slog.Info("batch processed", "total", len(items), "failed", failed)
}
```

## 26.11 Spell log messages correctly; don't rely on log readers to guess a typo'd event name.

> Why? Log messages are searched and alerted on by exact or fuzzy string
> match; a misspelled event name (`"proccessing order"` vs `"processing
> order"`) silently splits what should be one queryable event into two,
> and breaks saved dashboard queries. There is no dedicated logging
> linter for this, but the user's lint configuration runs `misspell`
> across all comments and string literals, which catches common
> misspellings in log message text the same way it catches them in
> comments.

> Enforced by: misspell (see [Chapter 33.2](33-linter-configuration.md))

```go
// bad — typo splits one logical event into two distinct log strings
slog.Info("proccessing order", "order_id", orderID)
// ... elsewhere, the correctly spelled version also exists:
slog.Info("processing order", "order_id", orderID)

// good — one correctly spelled, consistent event name
slog.Info("processing order", "order_id", orderID)
```
