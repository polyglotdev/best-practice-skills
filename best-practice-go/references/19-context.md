<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 19. Context

`context.Context` carries cancellation, deadlines, and request-scoped
values across API boundaries. This chapter draws from [Google Best
Practices:
Contexts](https://google.github.io/styleguide/go/best-practices#contexts),
with the underlying cancellation model implied throughout [Effective Go:
Concurrency](https://go.dev/doc/effective_go#concurrency). Goroutine
lifetime management that context cancellation often drives is covered in
[Chapter 20](20-concurrency.md).

**Linter alignment:** this chapter is one of the most heavily enforced in
this project's `.golangci.yml` — `contextcheck` and `revive`'s
`context-as-argument` and `context-keys-type` rules turn several rules
below into hard, build-failing **Violations**.

## 19.1 Make `ctx context.Context` the first parameter of any function that needs one.

> Why? This is the single most consistent convention in Go code that
> touches concurrency or cancellation, and `revive`'s
> `context-as-argument` rule fails the build if `ctx` is placed anywhere
> else in the parameter list. Consistent placement means a reader can
> always find the cancellation/deadline source at a glance. **Violation —
> enforced by `revive/context-as-argument`.**

```go
// bad — ctx is not first
func FetchUser(id string, ctx context.Context) (*User, error) {
	return nil, nil
}

// good
func FetchUser(ctx context.Context, id string) (*User, error) {
	return nil, nil
}
```

## 19.2 Never store a `context.Context` inside a struct field.

> Why? [Google Best Practices:
> Contexts](https://google.github.io/styleguide/go/best-practices#contexts)
> treats context as strictly request- or call-scoped: it should flow
> through a call chain as an explicit parameter, not be captured and
> reused later, because a stored context can outlive the request it was
> created for and silently carry stale cancellation or values into
> unrelated work.

```go
// bad — ctx captured at construction time, reused across unrelated calls
type Client struct {
	ctx context.Context
	hc  *http.Client
}

func (c *Client) Get(path string) (*http.Response, error) {
	req, _ := http.NewRequestWithContext(c.ctx, http.MethodGet, path, nil)
	return c.hc.Do(req)
}

// good — ctx flows through the call, not the struct
type Client struct {
	hc *http.Client
}

func (c *Client) Get(ctx context.Context, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}
	return c.hc.Do(req)
}
```

## 19.3 Never pass `nil` for a `context.Context` parameter — use `context.TODO()` when no context is available yet.

> Why? A `nil` context panics the first time any context-aware function
> tries to call a method on it. `context.TODO()` is the standard library's
> explicit placeholder for "this code should take a context eventually,
> but doesn't have one wired through yet" — it behaves like
> `context.Background()` but documents the gap for future cleanup.

```go
// bad — panics on first use inside FetchUser if it calls ctx.Done() etc.
user, err := FetchUser(nil, "u123")

// good
user, err := FetchUser(context.TODO(), "u123")
```

## 19.4 Never call `context.Background()` or `context.TODO()` inside a function that already has a `ctx` parameter in scope.

> Why? Creating a fresh background context inside a function that already
> received one detaches all downstream calls from the caller's
> cancellation and deadline — a request that should be cancelable no
> longer is, and the bug is invisible from the call site. This project's
> `contextcheck` linter exists specifically to catch this. **Violation —
> enforced by `contextcheck`.**

```go
// bad — contextcheck flags this: ctx is already in scope but ignored
func (s *Server) handle(ctx context.Context, req *Request) error {
	dbCtx := context.Background()
	return s.db.Query(dbCtx, req.Query)
}

// good — propagate the caller's context
func (s *Server) handle(ctx context.Context, req *Request) error {
	return s.db.Query(ctx, req.Query)
}
```

## 19.5 Don't derive a fresh `context.Background()` inside library code — accept a context from the caller instead.

> Why? Only `main`, top-level test setup, or a true program entry point
> should call `context.Background()`. Library code that manufactures its
> own root context can't be cancelled or bounded by whatever called it,
> which reintroduces exactly the coupling problem `contextcheck` (19.4)
> flags, just one level higher — at the API boundary instead of inside a
> single function.

```go
// bad — library package creates its own root context, ignoring any
// deadline or cancellation the caller wanted to impose
package httpclient

func Get(url string) (*http.Response, error) {
	ctx := context.Background()
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	return http.DefaultClient.Do(req)
}

// good — caller controls cancellation and deadlines
package httpclient

func Get(ctx context.Context, url string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	return http.DefaultClient.Do(req)
}
```

## 19.6 Always call the `cancel` function returned by `WithCancel`, `WithTimeout`, or `WithDeadline` — defer it immediately.

> Why? Every derived, cancelable context registers resources with its
> parent that are released when `cancel` runs. Skipping the call leaks
> that association (and, for timers backing `WithTimeout`/`WithDeadline`,
> a live timer) until the parent context itself is cancelled — which, for
> a long-lived parent, may be never.

```go
// bad — cancel is never called; the timer and parent linkage leak
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
result, err := fetch(ctx)

// good — defer cancel immediately, right next to creation
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
result, err := fetch(ctx)
```

## 19.7 Use `context.WithoutCancel` (Go 1.21+) to intentionally detach background work from a request's cancellation.

> Why? Some work legitimately needs to outlive the request that triggered
> it — for example, an audit log write that should complete even if the
> client disconnects. Before Go 1.21, this required manually copying
> values into a fresh `context.Background()`, losing request-scoped values
> in the process. `context.WithoutCancel` keeps the values while dropping
> the cancellation signal and deadline.

```go
// bad — was idiomatic pre-1.21: manually re-creating a background
// context loses any request-scoped values that downstream code needs
func (s *Server) handle(ctx context.Context, req *Request) {
	go func() {
		auditCtx := context.Background()
		s.audit.Log(auditCtx, req)
	}()
}

// good — detaches cancellation but preserves request-scoped values
func (s *Server) handle(ctx context.Context, req *Request) {
	go func() {
		auditCtx := context.WithoutCancel(ctx)
		s.audit.Log(auditCtx, req)
	}()
}
```

## 19.8 Use `context.AfterFunc` (Go 1.21+) to run cleanup when a context is cancelled, instead of a manual goroutine watching `Done()`.

> Why? Before Go 1.21, reacting to cancellation required spawning a
> goroutine that blocked on `<-ctx.Done()`, which itself needed a separate
> mechanism to stop if the work finished before cancellation happened.
> `context.AfterFunc` registers the callback directly against the context
> and automatically stops watching once the function returns or the
> registration is cancelled, removing that extra goroutine entirely.

```go
// bad — was idiomatic pre-1.21: an extra goroutine just to watch Done()
func watch(ctx context.Context, cleanup func()) {
	go func() {
		<-ctx.Done()
		cleanup()
	}()
}

// good — no extra goroutine to manage or leak
func watch(ctx context.Context, cleanup func()) func() bool {
	stop := context.AfterFunc(ctx, cleanup)
	return stop
}
```

## 19.9 Use context values only for request-scoped data that crosses API boundaries — never for optional parameters.

> Why? [Google Best Practices:
> Contexts](https://google.github.io/styleguide/go/best-practices#contexts)
> treats context values as an escape hatch for things like a request ID or
> an authenticated principal that must flow through layers that don't
> otherwise know about them — not a substitute for a normal function
> argument. Passing ordinary parameters through context values makes a
> function's real dependencies invisible in its signature.

```go
// bad — a normal, always-required parameter smuggled through context
func Process(ctx context.Context) error {
	limit := ctx.Value(limitKey).(int)
	return doWork(limit)
}

// good — normal parameters stay in the signature
func Process(ctx context.Context, limit int) error {
	return doWork(limit)
}
```

## 19.10 Define a private, unexported type for context keys — never use a primitive like `string` or `int`.

> Why? Two packages that both use a bare `string` key like `"userID"` can
> collide and silently overwrite each other's values, because context
> value lookups compare keys with `==` across the whole program. `revive`'s
> `context-keys-type` rule fails the build on a primitive-typed key.
> **Violation — enforced by `revive/context-keys-type`.**

```go
// bad — revive flags a string used directly as a context key; any other
// package using "userID" collides with this one
func WithUserID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, "userID", id)
}

// good — an unexported type makes the key impossible to collide with
// a key from another package, even if the underlying value looks similar
type ctxKey int

const userIDKey ctxKey = iota

func WithUserID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, userIDKey, id)
}

func UserID(ctx context.Context) (string, bool) {
	id, ok := ctx.Value(userIDKey).(string)
	return id, ok
}
```

## 19.11 Provide a typed accessor function for every context value instead of letting callers call `ctx.Value` directly.

> Why? Exposing the raw key alongside a manual `ctx.Value(key).(T)` at
> every call site duplicates the type assertion and the key everywhere the
> value is read. A single accessor function centralizes both, and it's the
> only place that needs updating if the stored type ever changes.

```go
// bad — every caller repeats the same unchecked assertion
val := ctx.Value(userIDKey)
id := val.(string)

// good — one accessor, comma-ok internally, reused everywhere
func UserID(ctx context.Context) (string, bool) {
	id, ok := ctx.Value(userIDKey).(string)
	return id, ok
}
```
