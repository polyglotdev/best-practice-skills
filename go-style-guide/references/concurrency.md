# Concurrency — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

Concurrency bugs are the hardest class of bug in Go to catch by reading code alone — they depend on timing, and most of them pass every test run except the one that matters. The rules here are less about idiom and more about eliminating entire categories of race, leak, and deadlock by construction: give every goroutine an owner, never copy a mutex, size channels deliberately, and document what "safe for concurrent use" actually means for a given type.

## Goroutine ownership — every goroutine has a clear owner and a stop signal

**What Google/Effective Go says:** Google's guide doesn't use the word "ownership" directly, but the underlying discipline is implied throughout [Best Practices: Goroutine lifetimes](https://google.github.io/styleguide/go/best-practices#goroutine-lifetimes) — every goroutine should have a well-defined lifetime that some other piece of code can reason about, rather than running indefinitely with no way to observe or stop it.

**How to detect it:** For every `go func() {...}()` or `go someFunc(...)` call site, check: is there a mechanism (a `done`/`stop` channel, a `context.Context`, a `sync.WaitGroup`) that lets some other part of the program know when this goroutine exits, or ask it to exit? If the goroutine runs forever with no observable lifecycle, that's the smell.

**Example violation — nobody owns this goroutine's lifecycle:**
```go
func StartWatcher(url string) {
	go func() {
		for {
			poll(url)
			time.Sleep(time.Minute)
		}
	}()
	// no way to stop this, ever, for the lifetime of the process
}
```

**Corrected:**
```go
type Watcher struct {
	stop chan struct{}
	done chan struct{}
}

func StartWatcher(url string) *Watcher {
	w := &Watcher{stop: make(chan struct{}), done: make(chan struct{})}
	go func() {
		defer close(w.done)
		ticker := time.NewTicker(time.Minute)
		defer ticker.Stop()
		for {
			select {
			case <-w.stop:
				return
			case <-ticker.C:
				poll(url)
			}
		}
	}()
	return w
}

func (w *Watcher) Stop() {
	close(w.stop)
	<-w.done
}
```

**Severity:** Violation

**Enforced by:** not a single dedicated `golangci-lint` rule catches this holistically; `contextcheck` catches the narrower case of a goroutine not respecting an available `ctx` (see [context.md](context.md#always-thread-a-cancelable-context-into-long-running-work)) — the broader ownership pattern is a design-review item

**Why it matters:** A goroutine with no owner and no stop signal leaks for the life of the process — in a long-running service, `StartWatcher` called repeatedly (once per request, once per test) accumulates goroutines that never exit, eventually exhausting memory or file descriptors.

## Don't fire-and-forget goroutines

**What Google/Effective Go says:** "Every goroutine... must document... when and how it stops" — echoed directly in [Uber: Don't fire-and-forget goroutines](https://github.com/uber-go/guide/blob/master/style.md#dont-fire-and-forget-goroutines): "the caller has no way of knowing when the goroutine is done, or of stopping it."

**How to detect it:** Grep for `go func()` calls whose closure has no return value collection, no `WaitGroup.Done()`, and no error channel — the goroutine's outcome (success, failure, or panic) is simply discarded.

**Example violation:**
```go
func ProcessOrder(o Order) {
	go sendConfirmationEmail(o) // if this panics or fails, nobody ever finds out
}
```

**Corrected:**
```go
func ProcessOrder(ctx context.Context, o Order) error {
	g, ctx := errgroup.WithContext(ctx)
	g.Go(func() error {
		return sendConfirmationEmail(ctx, o)
	})
	return g.Wait()
}
```

If the email genuinely should not block order processing, at minimum log the outcome and bound the goroutine's lifetime:
```go
func ProcessOrder(ctx context.Context, o Order) {
	go func() {
		if err := sendConfirmationEmail(ctx, o); err != nil {
			slog.ErrorContext(ctx, "confirmation email failed", "order", o.ID, "err", err)
		}
	}()
}
```

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule; catch via the grep heuristic above and code review

**Why it matters:** A fire-and-forget goroutine that panics takes down the entire process (a panic in any goroutine is fatal unless recovered in that same goroutine), and one that merely fails silently means real failures — a lost confirmation email, an unwritten audit log — go undetected in production.

## No goroutines in `init()`

**What Google/Effective Go says:** Not covered in Google's guide directly (their guidance on `init()` focuses on determinism); Uber's [No goroutines in init()](https://github.com/uber-go/guide/blob/master/style.md#no-goroutines-in-init) rule states the concern precisely: a package should "expose a function ... or ... a type" that starts the goroutine, not spawn it as a side effect of being imported.

**How to detect it:** Grep `func init()` bodies for `go func` or `go someFunc(`.

**Example violation:**
```go
func init() {
	go pollConfigChanges() // starts as soon as anyone imports this package, no way to stop it
}
```

**Corrected:**
```go
type ConfigPoller struct {
	stop chan struct{}
}

func NewConfigPoller() *ConfigPoller {
	p := &ConfigPoller{stop: make(chan struct{})}
	return p
}

func (p *ConfigPoller) Start() {
	go p.pollLoop()
}

func (p *ConfigPoller) Stop() {
	close(p.stop)
}
```

**Severity:** Violation

**Enforced by:** not enforced by `golangci-lint` in this repo (`gochecknoinits` is referenced in the `cmd/` path-exclusion rule but is not itself in the enabled-linters list — see [golangci-lint.md](golangci-lint.md)); catch via the grep heuristic above

**Why it matters:** A goroutine started in `init()` runs the moment any code imports the package — transitively, possibly from a test binary or an unrelated tool that only needed one function from the package — with no handle for the importer to stop it or even know it's running.

## Zero-value mutexes are valid, but must never be copied

**What Google/Effective Go says:** "The zero value of a `sync.Mutex`... is valid and ready to use" — no explicit initialization is needed, but the mutex (and anything containing it) must never be copied after first use. ([Best Practices: Synchronization](https://google.github.io/styleguide/go/best-practices#synchronization); [Uber: Zero-value Mutexes are Valid](https://github.com/uber-go/guide/blob/master/style.md#zero-value-mutexes-are-valid))

**How to detect it:** For every struct containing a `sync.Mutex`/`sync.RWMutex`, check (a) that it's declared with `var mu sync.Mutex`, not `new(sync.Mutex)` or a pointer field, and (b) that the containing type is never passed or returned by value, and (c) that the mutex field is unexported and never embedded (an embedded mutex leaks `Lock`/`Unlock` into the type's public API).

**Example violation — embedded and copyable:**
```go
type Counter struct {
	sync.Mutex // embedded — leaks Lock/Unlock as public methods
	n          int
}

func Increment(c Counter) { // passed by value — copies the mutex
	c.Lock()
	c.n++
	c.Unlock()
}
```

**Corrected:**
```go
type Counter struct {
	mu sync.Mutex
	n  int
}

func (c *Counter) Increment() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.n++
}
```

**Severity:** Violation

**Enforced by:** `govet`'s `copylocks` analysis, part of `enable-all` in this repo's `.golangci.yml`, catches the copy-by-value case; the embedding-leaks-the-API concern is a separate style judgment not caught by any linter — see [naming.md](naming.md#receivers-consistent-value-vs-pointer-within-a-type)

**Why it matters:** Copying a mutex after it's been locked produces two independent locks guarding what the code still treats as one critical section — both copies report "unlocked" independently, so two goroutines can both believe they hold exclusive access simultaneously.

## `errgroup` for goroutines that share a cancellation and an error

**What Google/Effective Go says:** Not named directly in Google's prose guide; documented in [`golang.org/x/sync/errgroup`](https://pkg.go.dev/golang.org/x/sync/errgroup), which is the de facto standard extension of the standard library for exactly this pattern and is compatible with the guide's [goroutine lifetime](https://google.github.io/styleguide/go/best-practices#goroutine-lifetimes) principle.

**How to detect it:** Look for manual `sync.WaitGroup` + shared-error-variable patterns where multiple goroutines can fail independently and the code hand-rolls collecting the first error and canceling the rest.

**Example violation (hand-rolled, racy error capture):**
```go
func FetchAll(ctx context.Context, ids []string) ([]*Partner, error) {
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstErr error
	results := make([]*Partner, len(ids))
	for i, id := range ids {
		wg.Add(1)
		go func(i int, id string) {
			defer wg.Done()
			p, err := fetch(ctx, id)
			if err != nil {
				mu.Lock()
				if firstErr == nil {
					firstErr = err
				}
				mu.Unlock()
				return
			}
			results[i] = p
		}(i, id)
	}
	wg.Wait()
	return results, firstErr
}
```

**Corrected:**
```go
func FetchAll(ctx context.Context, ids []string) ([]*Partner, error) {
	g, ctx := errgroup.WithContext(ctx)
	results := make([]*Partner, len(ids))
	for i, id := range ids {
		g.Go(func() error {
			p, err := fetch(ctx, id)
			if err != nil {
				return err
			}
			results[i] = p
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return nil, err
	}
	return results, nil
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** `errgroup.WithContext` cancels the shared context the moment any goroutine returns a non-nil error, so sibling goroutines can observe cancellation and stop early — a hand-rolled `WaitGroup` version has to reimplement that cancellation propagation itself or, more often, simply omits it and lets every other goroutine run to completion even after the first failure.

## No bare `go func()` for anything beyond trivial, self-contained work

**What Google/Effective Go says:** Follows from [Best Practices: Goroutine lifetimes](https://google.github.io/styleguide/go/best-practices#goroutine-lifetimes) — a bare `go func(){}()` with no error handling, no context, and no way to observe completion is acceptable only for genuinely fire-and-forget, side-effect-free, unlikely-to-fail work.

**How to detect it:** For every `go func() {` literal (not calling a named, documented function), read the closure body. If it does I/O, can return an error, or exceeds a handful of lines, it likely deserves to be a named function with the ownership/error-handling patterns above.

**Example violation:**
```go
go func() {
	resp, err := http.Get(url)
	if err != nil {
		return // silently discarded
	}
	defer resp.Body.Close()
	data, _ := io.ReadAll(resp.Body) // error also discarded
	cache.Set(url, data)
}()
```

**Corrected:**
```go
g.Go(func() error {
	return refreshCache(ctx, cache, url)
})

// refreshCache is a named, independently testable, independently
// documented function with real error handling.
func refreshCache(ctx context.Context, cache *Cache, url string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("fetch %s: %w", url, err)
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read %s: %w", url, err)
	}
	cache.Set(url, data)
	return nil
}
```

**Severity:** Suggestion

**Enforced by:** `errcheck` will catch the discarded `io.ReadAll` error in the violation example regardless of whether it's inline or named; the broader "extract to a named function" judgment is not linter-enforced

**Why it matters:** An inline closure with real logic and discarded errors is untestable in isolation and invisible to code review's usual "does this function have a test" checklist — pulling it into a named function makes both the error handling and the test coverage obligations explicit.

## Channel size is one or none

**What Google/Effective Go says:** Not covered in Google's guide directly; documented as [Uber: Channel Size is One or None](https://github.com/uber-go/guide/blob/master/style.md#channel-size-is-one-or-none) — "channels should usually have a size of one or be unbuffered... any other size must be subject to a high level of scrutiny."

**How to detect it:** Grep `make(chan ` for a numeric capacity argument greater than 1. Each match needs a comment justifying the specific number, or should be reduced to 0 or 1.

**Example violation:**
```go
results := make(chan Result, 64) // why 64? what happens at 65?
```

**Corrected:**
```go
results := make(chan Result) // unbuffered: producer blocks until consumer is ready
// or, if a single pending result is a deliberate design choice:
results := make(chan Result, 1)
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** An arbitrary fixed buffer size just moves a capacity problem later — the channel will still eventually fill if the consumer is slower than the producer, but now the point of backpressure is an invisible constant instead of an explicit design decision, and the "why 64" question has no answer for the next reader.

## Direction-typed channel parameters

**What Google/Effective Go says:** "Specify the direction of a channel" whenever a function only sends or only receives, "to prevent [close/send] misuse." ([Best Practices: Channel direction](https://google.github.io/styleguide/go/best-practices#channel-direction)) See also [function-design.md](function-design.md#specify-channel-direction-in-function-signatures) and [variable-declarations.md](variable-declarations.md#specify-channel-direction-in-function-signatures) for the same rule from other angles.

**How to detect it:** Grep function signatures for `chan T` (bidirectional, no arrow). For each, read the body — if it only ranges/receives, the parameter should be `<-chan T`; if it only sends, `chan<- T`.

**Example violation:**
```go
func worker(jobs chan Job, results chan Result) {
	for j := range jobs {
		results <- process(j)
	}
}
```

**Corrected:**
```go
func worker(jobs <-chan Job, results chan<- Result) {
	for j := range jobs {
		results <- process(j)
	}
}
```

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule in this config

**Why it matters:** A directional channel type turns an entire class of runtime panics (closing a channel from the receiving side, sending on a channel meant to be read-only) into compile errors, and documents at the call site which side of the pipeline this function represents.

## Go 1.22 loop-variable semantics and `copyloopvar`

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the change); documented in the [Go 1.22 release notes](https://go.dev/blog/loopvar-preview) — each iteration of a `for` loop now gets its own copy of the loop variable, closing the historic "goroutine captures the loop variable by reference" trap. See [testing.md](testing.md#closure-capture-pattern-in-table-tests-the-loop-variable-trap) for the test-specific framing of this same change.

**How to detect it:** Check the module's `go.mod` Go version directive. On `go 1.22`+, a manual `x := x` capture line immediately inside a `for` loop, before a `go func()` or closure that uses `x`, is now redundant. On `go 1.21` or earlier, its **absence** before a goroutine or closure that outlives the loop iteration is a real bug.

**The pre-1.22 trap:**
```go
// go.mod: go 1.21
for _, job := range jobs {
	go func() {
		process(job) // BUG on Go <1.22: every goroutine may see the same, final job
	}()
}
```

**Pre-1.22 fix:**
```go
// go.mod: go 1.21
for _, job := range jobs {
	job := job // capture a per-iteration copy
	go func() {
		process(job)
	}()
}
```

**Go 1.22+ — safe without the capture line:**
```go
// go.mod: go 1.22 or later
for _, job := range jobs {
	go func() {
		process(job) // each iteration already has its own job
	}()
}
```

**Severity:** Violation on modules declaring `go 1.21` or earlier without the capture line; on `go 1.22`+ modules, an unnecessary capture line is flagged instead (see below)

**Enforced by:** copyloopvar — flags both the missing-capture bug on pre-1.22 semantics contexts and unnecessary capture lines once a module has opted into Go 1.22+ loop semantics

**Why it matters:** This was, for years, the single most common Go concurrency bug in code review — a `go func()` inside a `for range` loop silently operating on the wrong (usually the last) iteration's value because the loop variable was shared across all iterations. Go 1.22 eliminated the root cause at the language level; `copyloopvar` keeps code correct and idiomatic on both sides of that language version boundary.

## Always close `http.Response.Body`

**What Google/Effective Go says:** Not stated as a named rule in Google's prose guide, but follows from the general [Best Practices: Defer to clean up](https://google.github.io/styleguide/go/best-practices#defer) principle applied to the standard library's most common leak source; documented directly in the [`net/http` package documentation](https://pkg.go.dev/net/http#Client.Do): "If the returned error is nil, the Response will contain a non-nil Body which the user is expected to close."

**How to detect it:** Grep for `http.Get(`, `http.Post(`, `client.Do(`, and similar calls that return `(*http.Response, error)`. For each, confirm the response body is closed on every code path, including early returns after a non-2xx status check.

**Example violation — body never closed if the status check returns early:**
```go
func fetchPartner(ctx context.Context, url string) (*Partner, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %d", resp.StatusCode) // leaks resp.Body
	}
	defer resp.Body.Close()
	var p Partner
	if err := json.NewDecoder(resp.Body).Decode(&p); err != nil {
		return nil, err
	}
	return &p, nil
}
```

**Corrected:**
```go
func fetchPartner(ctx context.Context, url string) (*Partner, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %d", resp.StatusCode)
	}
	var p Partner
	if err := json.NewDecoder(resp.Body).Decode(&p); err != nil {
		return nil, err
	}
	return &p, nil
}
```

**Severity:** Violation

**Enforced by:** bodyclose (relaxed inside `_test.go` in this repo — see [testing.md](testing.md#test-file-linter-relaxations))

**Why it matters:** An unclosed response body leaks the underlying TCP connection — under load, this exhausts the HTTP client's connection pool (and eventually file descriptors), producing a slow, mysterious degradation rather than an obvious crash.

## Document concurrency assumptions on every mutating method

**What Google/Effective Go says:** "Mutating operations are not safe for concurrent use unless documented otherwise" — this is the runtime-safety half of the same rule documented from the writing angle in [documentation.md](documentation.md#document-concurrency-assumptions). ([Best Practices: Synchronization](https://google.github.io/styleguide/go/best-practices#synchronization))

**How to detect it:** For every exported type with mutating methods, check whether the type's internal synchronization (a mutex, channel-based serialization, or none at all) actually matches what the doc comment claims — this rule is about the implementation matching the contract, not just the contract existing.

**Example violation — doc comment promises safety the implementation doesn't provide:**
```go
// Cache is safe for concurrent use.
type Cache struct {
	data map[string]string // no mutex — the comment is not true
}

func (c *Cache) Set(k, v string) {
	c.data[k] = v // concurrent Set calls race
}
```

**Corrected:**
```go
// Cache is safe for concurrent use.
type Cache struct {
	mu   sync.Mutex
	data map[string]string
}

func (c *Cache) Set(k, v string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[k] = v
}
```

**Severity:** Violation

**Enforced by:** `go test -race` (see [testing.md](testing.md#go-test--race-is-mandatory-for-concurrent-code)) will surface the actual data race at runtime under concurrent test load; no static linter in this config verifies that a "safe for concurrent use" doc comment matches the implementation

**Why it matters:** A doc comment claiming concurrency safety is a contract callers will rely on without re-verifying; if the implementation doesn't actually provide it, the bug only surfaces under production concurrency, typically as sporadic, hard-to-reproduce data corruption.

## Defer cleanup immediately after a resource is acquired

**What Google/Effective Go says:** "Whenever a function creates an object that needs to be cleaned up... that responsibility should be discharged with `defer`, as close as possible to the object's creation" — the goroutine/lock-specific instance of the general rule in [function-design.md](function-design.md#defer-cleanup-at-the-point-of-ownership-handoff). ([Best Practices: Defer to clean up](https://google.github.io/styleguide/go/best-practices#defer); [Uber: Defer to Clean Up](https://github.com/uber-go/guide/blob/master/style.md#defer-to-clean-up))

**How to detect it:** For every `mu.Lock()` call, check that `defer mu.Unlock()` appears on the next line, not scattered before each return path.

**Example violation:**
```go
func (c *Cache) Get(k string) (string, bool) {
	c.mu.Lock()
	v, ok := c.data[k]
	if !ok {
		c.mu.Unlock() // easy to forget on a new return path
		return "", false
	}
	c.mu.Unlock()
	return v, true
}
```

**Corrected:**
```go
func (c *Cache) Get(k string) (string, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	v, ok := c.data[k]
	return v, ok
}
```

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule; `govet`'s general analysis (part of `enable-all`) does not specifically check lock/unlock pairing

**Why it matters:** `defer mu.Unlock()` immediately after `Lock()` means every future return path added to the function automatically releases the lock — manually placed `Unlock()` calls are one missed return statement away from a permanent deadlock.

## How to audit Go code against these rules

1. Grep `go func(` and `go \w+(` — for each, check whether there's an observable stop signal or completion mechanism (channel, `WaitGroup`, `errgroup`).
2. Grep `func init()` bodies for `go func`/`go \w+(` — flag any goroutine spawned from `init()`.
3. For every struct with a `sync.Mutex`/`sync.RWMutex` field, confirm it's unexported, not embedded, and the containing type is never passed/returned by value (`govet`'s `copylocks` catches the value-copy case automatically).
4. Look for hand-rolled `WaitGroup` + shared-error-variable patterns — suggest `errgroup`.
5. Grep `make(chan ` for capacity arguments greater than 1 without a justifying comment.
6. Grep function/method signatures for bidirectional `chan T` parameters — check the body for read-only or write-only usage.
7. Check `go.mod`'s Go version; for `for range` loops feeding a `go func()` or closure, verify capture-line correctness per the target Go version (`copyloopvar` covers this in CI).
8. Grep `http.Get(`, `http.Post(`, `client.Do(` — verify `resp.Body.Close()` is deferred immediately, before any early return (`bodyclose` covers this in CI, except in `_test.go`).
9. For every exported type claiming concurrency safety in its doc comment, verify the implementation actually synchronizes mutating methods; run `go test -race` to confirm empirically.
10. Grep `\.Lock()` calls — confirm the matching `Unlock()` is a `defer` on the very next line.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
