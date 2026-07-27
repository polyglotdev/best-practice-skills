# Context — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

`context.Context` carries cancellation, deadlines, and request-scoped values across API boundaries. Google's guide devotes an entire section to it because contexts are easy to use in a way that compiles fine and silently breaks cancellation, leaks values into places they don't belong, or obscures a function's real lifetime contract. The rules here are about keeping context usage predictable enough that a reader never has to open the implementation to know how cancellation flows.

## `ctx` is always the first parameter

**What Google/Effective Go says:** "By convention, `ctx` is the first parameter of a function." ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts))

**How to detect it:** For every function or method accepting a `context.Context` anywhere in its parameter list, check that it's parameter 1.

**Example violation:**
```go
func FetchPartner(id string, ctx context.Context) (*Partner, error)
```

**Corrected:**
```go
func FetchPartner(ctx context.Context, id string) (*Partner, error)
```

**Severity:** Violation

**Enforced by:** revive/context-as-argument

**Why it matters:** Every function in the standard library that accepts a context puts it first (`http.NewRequestWithContext`, `sql.DB.QueryContext`, `exec.CommandContext`) — consistent placement means a reader recognizes a context-carrying function from its shape alone, without reading the full signature.

## Contexts are never stored in a struct

**What Google/Effective Go says:** "Contexts are not meant to be stored in a struct... Instead, pass a `Context` explicitly to each function that needs it." ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts))

**How to detect it:** Grep struct definitions for a `context.Context` field. Each match is almost always a bug, with the narrow exception of a type whose entire purpose is to *represent* an operation lifetime tied to that context (rare, and should be called out explicitly in the type's doc comment when it happens).

**Example violation:**
```go
type Fetcher struct {
	ctx    context.Context // storing ctx here — which request's ctx does this represent later?
	client *http.Client
}

func NewFetcher(ctx context.Context, client *http.Client) *Fetcher {
	return &Fetcher{ctx: ctx, client: client}
}

func (f *Fetcher) Fetch(url string) (*http.Response, error) {
	req, _ := http.NewRequestWithContext(f.ctx, http.MethodGet, url, nil)
	return f.client.Do(req)
}
```

**Corrected:**
```go
type Fetcher struct {
	client *http.Client
}

func NewFetcher(client *http.Client) *Fetcher {
	return &Fetcher{client: client}
}

func (f *Fetcher) Fetch(ctx context.Context, url string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	return f.client.Do(req)
}
```

The documented exception: a type like `NewReceiver(ctx)` may legitimately hold a context if its own doc comment states the lifetime relationship explicitly (see the "documented lifetime exception" rule below) — but this should be rare and always called out, never silent.

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule in this config; `contextcheck` checks a related but distinct concern (see below) — catch stored contexts via the grep heuristic above and code review

**Why it matters:** A `Fetcher` built once at startup and reused across many requests, but holding one `ctx` from construction time, will use that single context's deadline and cancellation for every subsequent call — a request-scoped lifetime silently becomes a process-scoped one, and cancelling one caller's context cancels the operation for every other caller sharing the `Fetcher`.

## No `nil` context

**What Google/Effective Go says:** "Never pass a nil Context, even if a function permits it... Use `context.TODO`" when it's unclear which context to use, or `context.Background()` at the top of `main`, a test, or an incoming request handler. ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts); [`context` package documentation](https://pkg.go.dev/context))

**How to detect it:** Grep for `context.Context(nil)` or a literal `nil` passed as an argument at a `context.Context` parameter position.

**Example violation:**
```go
resp, err := client.Do(nil, req) // nil context — will panic inside most context-aware APIs
```

**Corrected:**
```go
resp, err := client.Do(context.Background(), req)
// or, if it's genuinely unclear which context applies yet:
resp, err := client.Do(context.TODO(), req)
```

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule; `govet`'s general analysis (part of `enable-all`) does not specifically flag `nil` context arguments — catch via grep and code review

**Why it matters:** Most context-aware standard-library and third-party functions call methods on the context they're given (`ctx.Done()`, `ctx.Value(...)`) without a nil check, because the convention promises it's never `nil` — passing `nil` anyway produces a nil-pointer panic at a call site far from where the mistake was made.

## `context.Background()` / `context.TODO()` only when no context is already in scope

**What Google/Effective Go says:** Implied by the "pass a Context explicitly" principle in [Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts) — if a `ctx` is already available as a parameter, calling `context.Background()` instead discards whatever cancellation, deadline, or values the caller already established.

**How to detect it:** Grep for `context.Background()` and `context.TODO()` calls inside functions that already accept a `ctx context.Context` parameter.

**Example violation:**
```go
func (r *Repository) Get(ctx context.Context, id string) (*Partner, error) {
	// ctx is right here as a parameter, but this call ignores it:
	row := r.db.QueryRowContext(context.Background(), "SELECT * FROM partners WHERE id = $1", id)
	return scanPartner(row)
}
```

**Corrected:**
```go
func (r *Repository) Get(ctx context.Context, id string) (*Partner, error) {
	row := r.db.QueryRowContext(ctx, "SELECT * FROM partners WHERE id = $1", id)
	return scanPartner(row)
}
```

**Severity:** Violation

**Enforced by:** contextcheck

**Why it matters:** Calling `context.Background()` inside a function that already has a `ctx` parameter silently detaches the downstream call from the caller's cancellation and deadline — a client that gives up and cancels its request will not stop this now-orphaned database query, which keeps running to completion regardless.

## Always call `cancel`

**What Google/Effective Go says:** "Cancel functions... [must] be called once you are finished with a context." Every `context.WithCancel`, `WithTimeout`, and `WithDeadline` returns a `cancel` function that must be called on every code path, typically via `defer`. ([`context` package documentation](https://pkg.go.dev/context#WithCancel))

**How to detect it:** Grep `context.WithCancel(`, `context.WithTimeout(`, `context.WithDeadline(` — for each match, confirm the returned `cancel` is deferred (or otherwise unconditionally called) on the very next line.

**Example violation:**
```go
func fetchWithTimeout(ctx context.Context, url string) (*http.Response, error) {
	ctx, _ = context.WithTimeout(ctx, 5*time.Second) // cancel discarded — timer leaks
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	return http.DefaultClient.Do(req)
}
```

**Corrected:**
```go
func fetchWithTimeout(ctx context.Context, url string) (*http.Response, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	return http.DefaultClient.Do(req)
}
```

**Severity:** Violation

**Enforced by:** `govet`'s `lostcancel` analysis, part of `enable-all` in this repo's `.golangci.yml`

**Why it matters:** An uncalled `cancel` function leaks the timer or goroutine backing that context's deadline machinery until the parent context itself is cancelled or expires — in a hot path, this accumulates leaked timers far faster than the garbage collector can reason about them, since the standard library keeps them alive intentionally until `cancel` runs.

## `context.WithoutCancel` to intentionally detach from a parent's cancellation (Go 1.21+)

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the function); documented in the [`context` package](https://pkg.go.dev/context#WithoutCancel), added in Go 1.21, for the specific case where background work should outlive the request that triggered it — e.g., an audit log write that should complete even if the triggering HTTP request is cancelled.

**How to detect it:** Look for the historical workaround pattern — constructing a fresh `context.Background()` and manually re-attaching known values — where the actual intent was "keep the values, drop the cancellation."

**Example — the old workaround, error-prone because it's easy to forget a value:**
```go
func logAuditEvent(ctx context.Context, event Event) {
	// old workaround: rebuild a context from scratch, hoping to carry the values that matter
	detached := context.Background()
	if tenant, ok := ctx.Value(tenantKey{}).(string); ok {
		detached = context.WithValue(detached, tenantKey{}, tenant)
	}
	go writeAuditLog(detached, event) // any other value on ctx is silently lost
}
```

**Corrected:**
```go
func logAuditEvent(ctx context.Context, event Event) {
	// keeps every value already attached to ctx, but detaches from its cancellation
	detached := context.WithoutCancel(ctx)
	go writeAuditLog(detached, event)
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a modernization opportunity, not a lint failure

**Why it matters:** `context.WithoutCancel` preserves every value already attached to the parent context while detaching only cancellation and deadline, which is exactly the "outlive the request, keep the request's identity/tracing values" pattern that background work usually needs — the manual workaround is both more code and silently drops any value the author didn't think to re-attach.

## `context.AfterFunc` for cancellation-triggered cleanup (Go 1.21+)

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the function); documented in the [`context` package](https://pkg.go.dev/context#AfterFunc), added in Go 1.21, as the standard-library-native alternative to hand-rolling a `select` on `ctx.Done()` purely to run a cleanup callback.

**How to detect it:** Look for a goroutine whose only job is `select { case <-ctx.Done(): cleanup() }` with no other work in the loop.

**Example violation (hand-rolled):**
```go
func watchAndCleanup(ctx context.Context, res *Resource) {
	go func() {
		<-ctx.Done()
		res.Close()
	}()
}
```

**Corrected:**
```go
func watchAndCleanup(ctx context.Context, res *Resource) (stop func() bool) {
	return context.AfterFunc(ctx, func() {
		res.Close()
	})
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** `context.AfterFunc` returns a `stop` function that can cancel the registration if the cleanup is no longer needed (avoiding a goroutine that outlives its usefulness), and it's one line instead of a hand-rolled goroutine plus `select`.

## Typed, unexported keys for context values

**What Google/Effective Go says:** "The type of the [context] key... should be unexported" — never use a plain `string` or other exported/shared type as a context key, since two packages using the string `"userID"` will silently collide. ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts))

**How to detect it:** Grep `context.WithValue(` and `ctx.Value(` calls for a key argument that's a string literal or an exported type, rather than an unexported named type.

**Example violation:**
```go
ctx = context.WithValue(ctx, "userID", id) // string key — collides with any other package using "userID"
```

**Corrected:**
```go
type userIDKey struct{}

func withUserID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, userIDKey{}, id)
}

func userIDFromContext(ctx context.Context) (string, bool) {
	id, ok := ctx.Value(userIDKey{}).(string)
	return id, ok
}
```

**Severity:** Violation

**Enforced by:** revive/context-keys-type

**Why it matters:** Two unrelated packages that both use the string `"userID"` as a context key will silently overwrite or read each other's values — an unexported struct type defined inside one package can never collide with a key defined anywhere else, because Go's type identity includes the defining package.

## Values on a context are for request-scoped metadata, not optional parameters

**What Google/Effective Go says:** "Use context Values only for request-scoped data that transits process or API boundaries, not for passing optional parameters to functions." ([`context` package documentation](https://pkg.go.dev/context))

**How to detect it:** For every `context.WithValue` call, ask: is this value something that flows across an API/process boundary and is genuinely tied to the lifetime of a single request (a trace ID, an authenticated principal), or is it a parameter that would be clearer as an explicit function argument?

**Example violation — using context values as a way to avoid changing a function signature:**
```go
func Process(ctx context.Context, order Order) error {
	dryRun, _ := ctx.Value(dryRunKey{}).(bool) // should just be a parameter
	if dryRun {
		return nil
	}
	return commit(order)
}
```

**Corrected:**
```go
func Process(ctx context.Context, order Order, dryRun bool) error {
	if dryRun {
		return nil
	}
	return commit(order)
}
```

**Legitimate use — request-scoped metadata crossing an API boundary:**
```go
func Principal(ctx context.Context) (Identity, error) {
	// the context must have a value attached by security.NewContext,
	// established once at the API boundary (e.g. an auth middleware)
	id, ok := ctx.Value(principalKey{}).(Identity)
	if !ok {
		return Identity{}, errors.New("no principal in context")
	}
	return id, nil
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a design judgment call about what belongs on the context versus in the signature

**Why it matters:** A context value is invisible in the function signature — a reader has to search the function body (and everything it calls) to discover that behavior depends on it, whereas an explicit parameter is documented by the compiler itself and impossible to silently omit.

## Document context behavior only when it deviates from convention

**What Google/Effective Go says:** Context cancellation is assumed; document only when a function's context handling has a special lifetime, an alternate interrupt mechanism, or specific value expectations. This is the context-specific instance of the broader rule in [documentation.md](documentation.md#document-context-behaviour-only-when-it-deviates-from-convention). ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts))

**How to detect it:** For every function taking `context.Context`, check whether its documented behavior matches its actual behavior in the three deviation cases: (1) does it return something other than `ctx.Err()` on cancellation? (2) does it have another interrupt mechanism (e.g., a `Stop()` method)? (3) does it have unusual context lifetime or value expectations?

**Example — deserves documentation because it deviates from the assumed convention:**
```go
// Run executes the job until ctx is cancelled or the job completes.
// Returns nil, not ctx.Err(), if ctx is cancelled before the job
// produces a result — callers should check Done() to distinguish
// "cancelled" from "completed with no error."
func Run(ctx context.Context, j Job) error
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** A function that quietly swallows `ctx.Err()` and returns `nil` instead breaks the caller's ability to distinguish "cancelled" from "succeeded" unless that behavior is documented — the convention-following case needs no comment, but every deviation is a trap for a caller who assumes the convention holds everywhere.

## Always thread a cancelable context into long-running work

**What Google/Effective Go says:** Implied throughout [Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts) and [Goroutine lifetimes](https://google.github.io/styleguide/go/best-practices#goroutine-lifetimes) — long-running or background work should observe the same cancellation signal as the rest of the call chain, rather than running to completion regardless of whether anyone still needs the result.

**How to detect it:** For any goroutine or long-running loop started with an available `ctx`, check whether the work actually selects on `ctx.Done()` anywhere, or whether it silently ignores the context it was handed.

**Example violation — ctx is accepted but never actually observed:**
```go
func StreamEvents(ctx context.Context, out chan<- Event) {
	for {
		ev := blockingPoll() // no ctx awareness — runs forever regardless of ctx
		out <- ev
	}
}
```

**Corrected:**
```go
func StreamEvents(ctx context.Context, out chan<- Event) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}
		ev, err := pollWithContext(ctx)
		if err != nil {
			return
		}
		select {
		case out <- ev:
		case <-ctx.Done():
			return
		}
	}
}
```

**Severity:** Violation

**Enforced by:** contextcheck catches the narrower case of ignoring an in-scope `ctx` in favor of `context.Background()`; a `ctx` parameter that's accepted but never read anywhere in the function body is not caught by any linter in this config and needs a manual check

**Why it matters:** Accepting a `context.Context` parameter is a promise that the function respects cancellation; a function that accepts `ctx` but never checks `ctx.Done()` gives callers false confidence that cancelling will actually stop the work, when in fact it silently runs to completion regardless.

## How to audit Go code against these rules

1. For every function/method accepting `context.Context`, confirm it's parameter 1.
2. Grep struct definitions for a `context.Context` field — flag unless the type's doc comment explicitly documents and justifies the stored lifetime.
3. Grep for `nil` passed at a context parameter position.
4. Grep `context.Background()`/`context.TODO()` inside functions that already have a `ctx` parameter in scope (`contextcheck` covers this in CI).
5. Grep `context.WithCancel(`, `WithTimeout(`, `WithDeadline(` — confirm the returned `cancel` is deferred immediately (`govet`'s `lostcancel` covers this in CI).
6. Look for hand-rolled "rebuild a background context and copy known values" patterns — suggest `context.WithoutCancel` (Go 1.21+).
7. Look for goroutines whose only job is `select { case <-ctx.Done(): cleanup() }` — suggest `context.AfterFunc` (Go 1.21+).
8. Grep `context.WithValue(`/`ctx.Value(` for string-literal or exported-type keys — flag and require an unexported key type (`revive/context-keys-type` covers this in CI).
9. For every `context.WithValue` call, judge whether the value is genuinely request-scoped metadata or should be an explicit function parameter instead.
10. For functions with unusual context behavior (non-`ctx.Err()` cancellation return, alternate interrupt mechanism, special lifetime expectations), confirm the doc comment says so.
11. For goroutines/loops that accept a `ctx`, confirm the body actually selects on or checks `ctx.Done()` somewhere, rather than merely accepting the parameter without using it.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
