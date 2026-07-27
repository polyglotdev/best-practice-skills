<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 18. Panic & Recover

`panic` and `recover` exist for a narrow purpose: signaling and containing
truly unrecoverable failures, not everyday error handling. This chapter
draws from [Google Best Practices:
Panic](https://google.github.io/styleguide/go/best-practices#panic),
[Effective Go: Panic](https://go.dev/doc/effective_go#panic) and
[Recover](https://go.dev/doc/effective_go#recover), and [Uber Style: Don't
Panic](https://github.com/uber-go/guide/blob/master/style.md#dont-panic).
Chapter 17 covers ordinary error propagation; this chapter covers the much
smaller set of cases where `panic` is the right tool, and where `recover`
is allowed to catch it.

**Linter note:** this project's `gosec` linter has G104 (unhandled
errors), G304 (file path from variable), and G404 (weak RNG) excluded —
those exclusions don't loosen anything in this chapter, since panic
avoidance here is a design principle rather than a specific gosec check.
Treat every rule below as a code-quality rule on its own merits.

## 18.1 Never let a panic cross a public API boundary.

> Why? [Google Best Practices:
> Panic](https://google.github.io/styleguide/go/best-practices#panic) and
> [Uber Style: Don't
> Panic](https://github.com/uber-go/guide/blob/master/style.md#dont-panic)
> agree that "code running in production must avoid panics" because "a
> program must panic only when something irrecoverable happens." A caller
> of your package has no way to know your internals panic unless they read
> your source; an `error` return is the contract they can rely on.

```go
// bad — panics instead of returning an error to the caller
func Parse(input string) *Document {
	if input == "" {
		panic("input must not be empty")
	}
	return parse(input)
}

// good
func Parse(input string) (*Document, error) {
	if input == "" {
		return nil, errors.New("input must not be empty")
	}
	return parse(input)
}
```

## 18.2 Reserve `panic` for programmer errors and invariant violations the caller cannot have caused.

> Why? [Effective Go: Panic](https://go.dev/doc/effective_go#panic) frames
> panic as reporting "that something impossible has happened." The
> standard library follows this for API misuse — indexing past a slice's
> length, a failed type assertion, `reflect` misuse — situations code
> review and tests should catch long before production, not conditions a
> well-formed caller can trigger through normal use.

```go
// bad — a malformed but plausible user request causes a panic
func (s *Server) handle(req *Request) {
	if req.Limit < 0 {
		panic("limit must be non-negative")
	}
	// ...
}

// good — user input errors are returned, not panicked
func (s *Server) handle(req *Request) error {
	if req.Limit < 0 {
		return fmt.Errorf("limit must be non-negative, got %d", req.Limit)
	}
	// ...
	return nil
}
```

## 18.3 Never use panic/recover as a substitute for normal control flow or error returns.

> Why? [Uber Style: Don't
> Panic](https://github.com/uber-go/guide/blob/master/style.md#dont-panic)
> is direct: "panic/recover is not an error handling strategy." Using
> panic to jump out of deeply nested loops or early-exit a function
> obscures the actual control flow and forces every caller in the chain to
> worry about an undocumented non-local exit.

```go
// bad — panic used as an early-exit mechanism, not a real failure
func findFirst(items []Item, pred func(Item) bool) (found Item) {
	defer func() {
		if r := recover(); r != nil {
			found = r.(Item)
		}
	}()
	for _, it := range items {
		if pred(it) {
			panic(it)
		}
	}
	return Item{}
}

// good — ordinary return
func findFirst(items []Item, pred func(Item) bool) (Item, bool) {
	for _, it := range items {
		if pred(it) {
			return it, true
		}
	}
	return Item{}, false
}
```

## 18.4 Only `recover` at a goroutine's root or a top-level request handler — never deep inside business logic.

> Why? [Effective Go:
> Recover](https://go.dev/doc/effective_go#recover) demonstrates `recover`
> guarding an entire goroutine's entry point (`safelyDo`) so "the result
> will be logged and the goroutine will exit cleanly without disturbing
> the others." [Google Best Practices:
> Panic](https://google.github.io/styleguide/go/best-practices#panic)
> warns that recovering closer to the panic site risks "propagating a
> corrupted state" because you know less about what invariants the panic
> may have already broken.

```go
// bad — recovers deep inside a call chain, papering over corrupted state
func processItem(it Item) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("recovered: %v", r)
		}
	}()
	mutateSharedCache(it) // may have partially mutated state before panicking
	return nil
}

// good — recover only at the goroutine root, after all work for this
// unit is done or clearly abandoned
func worker(jobs <-chan Item) {
	for it := range jobs {
		func() {
			defer func() {
				if r := recover(); r != nil {
					slog.Error("job panicked", "recovered", r)
				}
			}()
			process(it)
		}()
	}
}
```

## 18.5 In HTTP servers, recover only in top-level middleware, and always after logging the panic value and stack.

> Why? [Google Best Practices:
> Panic](https://google.github.io/styleguide/go/best-practices#panic)
> calls out that `net/http`'s built-in panic recovery in request handlers
> is "consensus among experienced Go engineers... a historical mistake"
> when it silently swallows panics; if you must recover at all (to keep
> one bad request from taking down the server), do it in a single,
> explicit middleware layer that logs loudly, not implicitly and silently.

```go
// bad — recovers silently; the underlying bug is never surfaced
func recoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			recover()
		}()
		next.ServeHTTP(w, r)
	})
}

// good — logs the panic and stack before responding, so the bug gets fixed
func recoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				slog.Error("panic in handler", "recovered", rec, "stack", string(debug.Stack()))
				http.Error(w, "internal error", http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}
```

## 18.6 Don't recover a panic just to avoid a crash — fix the underlying bug instead.

> Why? [Google Best Practices:
> Panic](https://google.github.io/styleguide/go/best-practices#panic)
> warns that recovering unexpected panics "can result in propagating a
> corrupted state," and recommends using monitoring to surface and fix the
> root cause "with a high priority" rather than suppressing the symptom.
> A recovered-and-ignored panic just delays the failure to a more
> confusing point later.

```go
// bad — silences every panic in the whole program, hiding real bugs
func main() {
	defer func() {
		recover()
	}()
	run()
}

// good — let it crash loudly during development and in CI; fix root
// causes instead of blanket-recovering
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

## 18.7 Use `log.Fatal`/`os.Exit` only in `main`, and only for startup failures — never inside a library.

> Why? [Google Best Practices:
> Panic](https://google.github.io/styleguide/go/best-practices#panic)
> directs that "program initialization errors... should be propagated
> upward to `main`, which should call `log.Exit`," because `main` is the
> only place with enough context to decide the whole process should stop.
> A library calling `os.Exit` takes that decision away from every
> program that ever imports it.

```go
// bad — a library function unilaterally kills the process
package config

func Load(path string) *Config {
	cfg, err := parse(path)
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}
	return cfg
}

// good — library returns an error; only main decides to exit
package config

func Load(path string) (*Config, error) {
	return parse(path)
}

func main() {
	cfg, err := config.Load("app.yaml")
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}
	run(cfg)
}
```

## 18.8 It is acceptable to panic during package-level initialization when there is truly no way to continue.

> Why? [Effective Go: Panic](https://go.dev/doc/effective_go#panic) allows
> this exception explicitly: "during initialization: if the library truly
> cannot set itself up, it might be reasonable to panic." [Uber Style:
> Don't
> Panic](https://github.com/uber-go/guide/blob/master/style.md#dont-panic)
> gives the same exception for `template.Must`-style helpers used at
> package scope, where there is no caller to return an error to.

```go
// bad — swallows a genuinely fatal setup error and continues with a
// broken template
var statusTemplate, _ = template.New("status").Parse(statusHTML)

// good — package-level init has no caller to report to; panic is the
// only reasonable signal that setup failed
var statusTemplate = template.Must(template.New("status").Parse(statusHTML))
```

## 18.9 Even in tests, prefer `t.Fatal`/`t.FailNow` over panicking to signal failure.

> Why? [Uber Style: Don't
> Panic](https://github.com/uber-go/guide/blob/master/style.md#dont-panic)
> notes this explicitly: a panic inside a test can crash the whole test
> binary or be swallowed by a recover elsewhere, whereas `t.Fatal` reliably
> marks the specific test as failed and stops it cleanly.

```go
// bad — a panic in a test can take down the entire test binary
func TestLoad(t *testing.T) {
	cfg, err := Load("testdata/app.yaml")
	if err != nil {
		panic(err)
	}
	_ = cfg
}

// good
func TestLoad(t *testing.T) {
	cfg, err := Load("testdata/app.yaml")
	if err != nil {
		t.Fatalf("Load() failed: %v", err)
	}
	_ = cfg
}
```
