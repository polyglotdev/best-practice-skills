<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 17. Error Handling

Chapter 16 is about designing error *values*; this chapter is about what a
caller does the moment it receives one. It draws from [Google Best
Practices: Errors](https://google.github.io/styleguide/go/best-practices#errors)
and [Logging](https://google.github.io/styleguide/go/best-practices#logging),
and from [Uber Style: Handle Errors
Once](https://github.com/uber-go/guide/blob/master/style.md#handle-errors-once)
and [Handle Type Assertion
Failures](https://github.com/uber-go/guide/blob/master/style.md#handle-type-assertion-failures).

**Linter alignment:** this chapter maps directly to `errcheck`
(`check-type-assertions: true`, `check-blank: true`), `nilerr`, and
`revive`'s `error-strings` and `indent-error-flow` rules in this project's
`.golangci.yml`. Rules backed by those linters are marked **Violation**;
everything else is a **Recommended** idiom.

## 17.1 Handle every error exactly once — never both log it and return it.

> Why? [Uber Style: Handle Errors
> Once](https://github.com/uber-go/guide/blob/master/style.md#handle-errors-once)
> states that "the caller should not... log the error and then return it,
> because its callers may handle the error as well," which produces one
> failure logged multiple times up the call stack — noisy, duplicated, and
> hard to correlate back to a single root cause.

```go
// bad — logs here, and the caller likely logs again when it receives err
func loadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		log.Printf("failed to read config: %v", err)
		return nil, err
	}
	return parse(data)
}

// good — wrap with context and return; let one layer decide to log
func loadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}
	return parse(data)
}
```

## 17.2 Start error messages with a lowercase letter and no trailing punctuation.

> Why? [Google Style Decisions:
> Errors](https://google.github.io/styleguide/go/decisions#errors) and
> [Uber Style: Error
> Wrapping](https://github.com/uber-go/guide/blob/master/style.md#error-wrapping)
> agree: error strings are usually embedded inside other context before a
> human ever reads them ("read config: open settings.txt: permission
> denied"), so a capital letter or a period mid-sentence looks wrong.
> `revive`'s `error-strings` rule enforces both the case and the
> punctuation. **Violation — enforced by `revive/error-strings`.**

```go
// bad
return fmt.Errorf("Could not open file.")

// good
return fmt.Errorf("could not open file")
```

## 17.3 Keep wrapped-error context succinct — don't prefix with "failed to" or "error:".

> Why? [Uber Style: Error
> Wrapping](https://github.com/uber-go/guide/blob/master/style.md#error-wrapping)
> notes that phrases like "failed to" "state the obvious and pile up as
> the error percolates up through the stack." A message wrapped five
> layers deep with "failed to failed to failed to..." carries no more
> information than the same message without the filler.

```go
// bad — each layer adds noise, not information
return fmt.Errorf("failed to load config: %w", err)

// good
return fmt.Errorf("load config: %w", err)
```

## 17.4 Never discard an error with `_ = f()` without a `//nolint` comment explaining why it's safe.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> allows discarding an error only "in the rare circumstance where it is
> appropriate," and requires "an accompanying comment [that] should
> explain why this is safe." The project's `errcheck` linter
> (`check-blank: true`) fails the build on an unexplained blank-assigned
> error, and `nolintlint` (`require-explanation: true`,
> `require-specific: true`) requires that any suppression name the linter
> and state a reason. **Violation — enforced by `errcheck`
> (`check-blank: true`) and `nolintlint`.**

```go
// bad — silently discards an error errcheck would otherwise catch
var b *bytes.Buffer
_, _ = b.Write(p)

// good — documented and explicitly suppressed
var b *bytes.Buffer
n, err := b.Write(p) //nolint:errcheck // bytes.Buffer.Write never returns a non-nil error
_ = n
_ = err
```

## 17.5 Never ignore an error return value implicitly by omitting the check.

> Why? `errcheck` (`check-blank: true`) also flags a completely dropped
> return value, such as calling `f()` for its side effect while ignoring a
> trailing `error` result. Two standard-library methods are pre-approved
> exceptions in this project's config — `(io.Closer).Close` and
> `(net/http.ResponseWriter).Write` — because their error returns are
> conventionally best-effort. Every other error-returning call must be
> checked. **Violation — enforced by `errcheck`.**

```go
// bad — os.Remove's error is silently dropped
os.Remove(tmpFile)

// good
if err := os.Remove(tmpFile); err != nil {
	return fmt.Errorf("remove temp file: %w", err)
}

// good — pre-approved exception: Close() error is conventionally
// best-effort and excluded from errcheck in this project
defer resp.Body.Close()
```

## 17.6 Never return `nil` for an error after actually failing — that's a `nilerr` bug, not error handling.

> Why? The pattern `if err != nil { return nil }` silently converts every
> failure into a false "success," which is far worse than propagating the
> error: callers proceed as if the operation worked. The project's
> `nilerr` linter exists specifically to catch this. **Violation —
> enforced by `nilerr`.**

```go
// bad — nilerr: swallows the failure and reports success
func save(path string, data []byte) error {
	if err := os.WriteFile(path, data, 0o644); err != nil {
		log.Printf("write failed: %v", err)
		return nil
	}
	return nil
}

// good
func save(path string, data []byte) error {
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write %s: %w", path, err)
	}
	return nil
}
```

## 17.7 Use the comma-ok idiom for type assertions instead of letting a failed assertion panic.

> Why? [Uber Style: Handle Type Assertion
> Failures](https://github.com/uber-go/guide/blob/master/style.md#handle-type-assertion-failures)
> states plainly: "the single return value form of a type assertion will
> panic on an incorrect type. Therefore, always use the 'comma ok'
> idiom." The project's `errcheck` setting (`check-type-assertions: true`)
> fails the build on a bare, unchecked assertion. **Violation — enforced
> by `errcheck` (`check-type-assertions: true`).**

```go
// bad — panics if i does not hold a string
t := i.(string)

// good
t, ok := i.(string)
if !ok {
	// handle the unexpected type gracefully
	return fmt.Errorf("expected string, got %T", i)
}
```

## 17.8 Use the comma-ok idiom for map lookups when the zero value is ambiguous with "not present."

> Why? A plain `v := m[key]` returns the zero value both when `key` maps
> to the zero value and when `key` is absent. Whenever that distinction
> matters, the two-value form is the only way to tell them apart — this is
> the same comma-ok shape Go uses for type assertions and channel receives,
> applied to maps.

```go
// bad — can't tell "count is 0" from "key never seen"
counts := map[string]int{}
n := counts[key]
if n == 0 {
	// is this a genuine zero, or a missing key? Ambiguous.
}

// good
n, ok := counts[key]
if !ok {
	// key was never recorded
}
```

## 17.9 Indent the error path, not the happy path — return early instead of wrapping success in `else`.

> Why? [Google Style Decisions: Indent Error
> Flow](https://google.github.io/styleguide/go/decisions#indent-error-flow)
> explains that handling the error first and returning "improves the
> readability of the code by enabling the reader to find the normal path
> quickly." `revive`'s `indent-error-flow` rule enforces this shape.
> **Violation — enforced by `revive/indent-error-flow`.**

```go
// bad — normal code buried inside an else, extra nesting for no reason
func load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	} else {
		return parse(data)
	}
}

// good
func load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return parse(data)
}
```

## 17.10 Shadow `err` intentionally inside `if`-with-initializer statements — this is a recommended idiom, not a bug to avoid.

> Why? Writing `if err := f(); err != nil { ... }` declares a new `err`
> scoped to the `if` block, shadowing any outer `err` of the same name.
> This project explicitly disables `govet`'s `shadow` check for `err`
> declarations, because the idiom is both idiomatic and safe: the inner
> `err` is fully handled (wrapped and returned, or handled) before the
> block ends, so there is no risk of silently reading the wrong variable.
> **Recommended idiom — `govet` shadow check is disabled for
> `"declaration of \"err\""` in this project.**

```go
// bad — hoists err to the function scope for no benefit, and now it
// stays live (and reassignable) long after each check is done
func loadAll(paths []string) error {
	var err error
	for _, p := range paths {
		err = validate(p)
		if err != nil {
			return fmt.Errorf("validate %s: %w", p, err)
		}
	}
	return nil
}

// good — err is intentionally scoped to the if; no ambiguity results
// because it's fully handled before the block exits
func loadAll(paths []string) error {
	for _, p := range paths {
		if err := validate(p); err != nil {
			return fmt.Errorf("validate %s: %w", p, err)
		}
	}
	return nil
}
```

## 17.11 Use `if _, err := f(); err != nil` when the non-error result isn't needed, instead of naming and discarding it separately.

> Why? Binding an unused result to `_` inline keeps the error check
> compact and makes it visually obvious that only the error matters here —
> matching the shape Go's standard library itself uses throughout (for
> example, `if _, err := w.Write(p); err != nil`).

```go
// bad — extra lines and an unused named variable
n, err := w.Write(p)
_ = n
if err != nil {
	return err
}

// good
if _, err := w.Write(p); err != nil {
	return err
}
```

## 17.12 Follow a decision tree for each error: propagate with context, handle and degrade, log at the boundary, or panic only for programmer bugs.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> and [Logging](https://google.github.io/styleguide/go/best-practices#logging)
> frame error handling as a deliberate choice at every call site, not a
> reflex. A simple decision tree keeps that choice consistent: (1) if this
> function can't meaningfully act on the error, wrap with context and
> return it; (2) if the error is recoverable here, handle it and continue;
> (3) only at a true boundary (a `main`, an HTTP handler, a worker loop)
> log it, because nothing above will see it again; (4) reserve `panic` for
> invariant violations that mean the program's internal state is already
> corrupt (see [Chapter 18](18-panic-and-recover.md)).

```go
// bad — logs deep in a library function that has a perfectly good
// caller waiting for the error, then also returns it
func (s *Server) handle(req *Request) error {
	user, err := s.db.FindUser(req.UserID)
	if err != nil {
		log.Printf("find user failed: %v", err) // logged here...
		return err                              // ...and again by the caller
	}
	return process(user)
}

// good — propagate with context; the HTTP layer (the boundary) logs once
func (s *Server) handle(req *Request) error {
	user, err := s.db.FindUser(req.UserID)
	if err != nil {
		return fmt.Errorf("find user %d: %w", req.UserID, err)
	}
	return process(user)
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if err := s.handle(parseRequest(r)); err != nil {
		slog.Error("request failed", "error", err) // boundary: log once
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
```
