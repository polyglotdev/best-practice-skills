<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 32. Tooling & Modernization

Go 1.22 and 1.23 changed enough language and standard-library surface
area that idioms taught even a few years ago are now outdated. This
chapter is not directly sourced from the Google Style Guide, which
predates most of these changes — it synthesizes the [Go 1.22 release
notes](https://go.dev/doc/go1.22), the [Go 1.23 release
notes](https://go.dev/doc/go1.23), and the standard-library
[`slices`](https://pkg.go.dev/slices), [`maps`](https://pkg.go.dev/maps),
and [`cmp`](https://pkg.go.dev/cmp) package documentation. Several rules
here map directly onto linters in the user's `.golangci.yml`; those are
marked with `Enforced by:`. See [Chapter 33](33-linter-configuration.md)
for the full linter baseline this chapter assumes.

## 32.1 Rely on Go 1.22's per-iteration loop variable semantics; do not add the manual `x := x` capture workaround to new code.

> Why? Prior to Go 1.22, `for _, x := range xs` declared `x` once and
> reused it across iterations, so a closure or goroutine capturing `x`
> would see whatever value it held when the closure actually ran — often
> the last one. [Go 1.22's release
> notes](https://go.dev/doc/go1.22#language) changed `for` loops to give
> each iteration its own copy of the loop variable, eliminating an entire
> class of bugs at the language level.

> Enforced by: copyloopvar (flags the now-unnecessary manual copy)

```go
// bad — was required pre-1.22; now dead code that copyloopvar flags
for _, url := range urls {
	url := url // unnecessary on Go 1.22+
	go func() {
		fetch(url)
	}()
}

// good — Go 1.22+ gives each iteration its own url automatically
for _, url := range urls {
	go func() {
		fetch(url)
	}()
}
```

## 32.2 Use `for range n` to iterate a fixed number of times instead of a manual counting loop, when the index value itself is unused.

> Why? [Go 1.22's release notes](https://go.dev/doc/go1.22#language)
> added support for ranging directly over an integer, which reads as "do
> this n times" without introducing an index variable the body never
> uses.

```go
// bad — a manual counter that nothing in the body actually reads
for i := 0; i < 5; i++ {
	fmt.Println("retrying...")
}

// good — for range n states the intent directly
for range 5 {
	fmt.Println("retrying...")
}
```

## 32.3 Use `for range n` with the index variable when the body only needs the index, not a manual three-clause loop.

> Why? The same Go 1.22 [`range`-over-int](https://go.dev/doc/go1.22#language)
> feature covers the common case of an index-only loop, removing the
> boilerplate `i := 0; i < n; i++` clauses when there is no slice or map
> to range over.

```go
// bad — three-clause loop just to get consecutive integers
for i := 0; i < len(workers); i++ {
	workers[i].ID = i
}

// good — range over the count directly
for i := range len(workers) {
	workers[i].ID = i
}
```

## 32.4 Use range-over-func iterators (Go 1.23) for custom sequence types instead of exposing a channel or requiring a callback parameter.

> Why? [Go 1.23's release notes](https://go.dev/doc/go1.23#language)
> added the ability to `range` over a function value matching
> `iter.Seq[V]` or `iter.Seq2[K, V]`, letting custom container and
> algorithm types support idiomatic `for ... range` syntax without
> forcing callers into callback-passing or building an intermediate
> slice.

```go
// bad — callback-style API; caller can't use range or break naturally
func (t *Tree) Walk(visit func(v int) bool) {
	t.walk(t.root, visit)
}

// good — an iter.Seq[int] lets callers range over the tree directly
func (t *Tree) All() iter.Seq[int] {
	return func(yield func(int) bool) {
		t.walk(t.root, yield)
	}
}

// caller:
// for v := range tree.All() {
//	fmt.Println(v)
// }
```

## 32.5 Use the `slices` package for sort, search, and containment checks instead of hand-written loops or `sort.Slice`.

> Why? [`slices.Sort`](https://pkg.go.dev/slices#Sort),
> [`slices.Contains`](https://pkg.go.dev/slices#Contains), and
> [`slices.Index`](https://pkg.go.dev/slices#Index) are generic,
> reflection-free, and communicate intent in one call. See [Chapter
> 24.9–24.10](24-generics.md) for the generics rationale behind these
> functions; this chapter treats them as the default modernization
> target when reviewing older code.

```go
// bad — hand-written loop reimplements slices.Index
func indexOf(names []string, target string) int {
	for i, n := range names {
		if n == target {
			return i
		}
	}
	return -1
}

// good — slices.Index says exactly what the code does
func indexOf(names []string, target string) int {
	return slices.Index(names, target)
}
```

## 32.6 Use the `maps` package's `Keys`, `Values`, and `Clone` instead of manual accumulation or copy loops.

> Why? [`maps.Clone`](https://pkg.go.dev/maps#Clone) and the
> iterator-returning [`maps.Keys`](https://pkg.go.dev/maps#Keys) /
> [`maps.Values`](https://pkg.go.dev/maps#Values) replace hand-written
> loops that are easy to get subtly wrong (forgetting to preallocate,
> mutating the source while copying).

```go
// bad — manual copy loop for what maps.Clone already does
func copyConfig(src map[string]string) map[string]string {
	dst := make(map[string]string, len(src))
	for k, v := range src {
		dst[k] = v
	}
	return dst
}

// good — maps.Clone expresses the same operation directly
func copyConfig(src map[string]string) map[string]string {
	return maps.Clone(src)
}
```

## 32.7 Use `cmp.Compare` and `cmp.Or` instead of hand-written multi-field comparison chains.

> Why? [`cmp.Compare`](https://pkg.go.dev/cmp#Compare) returns -1/0/1 for
> any ordered type without a manual if/else chain, and
> [`cmp.Or`](https://pkg.go.dev/cmp#Or) picks the first non-zero value
> from a list — ideal for multi-field tie-breaking comparisons used in
> `slices.SortFunc`.

```go
// bad — manual tie-breaking chain for a multi-field sort
slices.SortFunc(users, func(a, b User) int {
	if a.LastName != b.LastName {
		if a.LastName < b.LastName {
			return -1
		}
		return 1
	}
	if a.FirstName < b.FirstName {
		return -1
	} else if a.FirstName > b.FirstName {
		return 1
	}
	return 0
})

// good — cmp.Or chains comparisons, falling through on ties
slices.SortFunc(users, func(a, b User) int {
	return cmp.Or(
		cmp.Compare(a.LastName, b.LastName),
		cmp.Compare(a.FirstName, b.FirstName),
	)
})
```

## 32.8 Use `errors.Join` to combine multiple independent errors instead of concatenating error strings or returning only the first error.

> Why? `errors.Join` (Go 1.20+) produces a single error value that
> `errors.Is`/`errors.As` can still unwrap into its constituents,
> preserving each error's identity. String concatenation destroys that,
> and returning only the first error silently discards the others.

```go
// bad — string concatenation loses each error's identity and type
func closeAll(closers []io.Closer) error {
	var msg string
	for _, c := range closers {
		if err := c.Close(); err != nil {
			msg += err.Error() + "; "
		}
	}
	if msg != "" {
		return errors.New(msg)
	}
	return nil
}

// good — errors.Join preserves each error for errors.Is/As
func closeAll(closers []io.Closer) error {
	var errs []error
	for _, c := range closers {
		if err := c.Close(); err != nil {
			errs = append(errs, err)
		}
	}
	return errors.Join(errs...)
}
```

## 32.9 Use `log/slog` for all new structured logging; see Chapter 26 for the full logging rule set.

> Why? `log/slog` shipped in the standard library in Go 1.21 and is now
> the default structured logger — see [Chapter 26](26-logging.md) for
> the complete set of logging rules. This entry exists here only as the
> modernization pointer: code still using `log.Printf` or a third-party
> structured logger predating `slog` should migrate.

```go
// bad — predates slog; unstructured and requires a third-party import
logrus.WithField("user_id", userID).Info("user logged in")

// good — log/slog is the standard-library structured logger
slog.Info("user logged in", "user_id", userID)
```

## 32.10 Use the `min`, `max`, and `clear` builtins instead of hand-written helper functions or manual loops.

> Why? Go 1.21 added `min`, `max`, and `clear` as predeclared builtins
> that work on any ordered type (for `min`/`max`) or any map/slice (for
> `clear`), removing the need for the small helper functions or manual
> loops every codebase used to write for these operations.

```go
// bad — hand-written helpers for what are now builtins
func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func clearMap(m map[string]int) {
	for k := range m {
		delete(m, k)
	}
}

// good — min, max, and clear are predeclared builtins
biggest := max(a, b)
clear(m)
```

## 32.11 Prefer `any` over `interface{}` in new code.

> Why? `any` is a predeclared alias for `interface{}` introduced in Go
> 1.18 alongside generics, and is now the idiomatic spelling everywhere
> an empty interface is meant. `interface{}` still compiles, but mixing
> both spellings in the same codebase is inconsistent for no benefit.

```go
// bad — the older, more verbose spelling
func Store(key string, value interface{}) {
	cache[key] = value
}

// good — any is the idiomatic Go 1.18+ spelling
func Store(key string, value any) {
	cache[key] = value
}
```

## 32.12 Use `context.WithoutCancel` to intentionally detach a context's cancellation while preserving its values, instead of passing `context.Background()` and losing request-scoped data.

> Why? `context.WithoutCancel` (Go 1.21) returns a context that carries
> the same values as its parent but is never canceled or deadlined —
> useful for background work that should outlive the request but still
> needs the request's trace ID or auth claims. Falling back to
> `context.Background()` for this case silently drops all of that
> request-scoped data.

```go
// bad — context.Background() drops trace ID, auth claims, everything
func (s *Service) enqueueAsync(ctx context.Context, job Job) {
	go func() {
		process(context.Background(), job) // lost all request-scoped values
	}()
}

// good — WithoutCancel preserves values while detaching from cancellation
func (s *Service) enqueueAsync(ctx context.Context, job Job) {
	detached := context.WithoutCancel(ctx)
	go func() {
		process(detached, job)
	}()
}
```

## 32.13 Use `context.AfterFunc` to run cleanup when a context is canceled, instead of a manual goroutine that polls `ctx.Done()`.

> Why? `context.AfterFunc` (Go 1.21) registers a function to run in its
> own goroutine as soon as the context is canceled or times out, and
> returns a `stop` function to cancel that registration — replacing the
> common hand-written pattern of a goroutine blocked on `<-ctx.Done()`.
> See also [Chapter 23.11](23-goroutines-and-lifecycle.md) for the
> goroutine-leak angle on this same API.

```go
// bad — a dedicated goroutine just to wait for cancellation
func watch(ctx context.Context, conn io.Closer) {
	go func() {
		<-ctx.Done()
		conn.Close()
	}()
}

// good — context.AfterFunc replaces the hand-written watcher goroutine
func watch(ctx context.Context, conn io.Closer) (stop func() bool) {
	return context.AfterFunc(ctx, func() {
		conn.Close()
	})
}
```

## 32.14 Use typed `sync/atomic` types (`atomic.Int64`, `atomic.Bool`, `atomic.Value`) instead of the older function-based `atomic.AddInt64`/`atomic.LoadInt64` API.

> Why? Go 1.19 added typed atomic wrapper types that hold their own
> value and expose methods (`Add`, `Load`, `Store`, `CompareAndSwap`),
> eliminating the risk of mismatching a raw `*int64` pointer with the
> wrong atomic function, which the older function-based API allowed.

```go
// bad — was idiomatic pre-1.19: raw int64 plus free functions, easy to misuse
var requestCount int64

func handle() {
	atomic.AddInt64(&requestCount, 1)
}

func current() int64 {
	return atomic.LoadInt64(&requestCount)
}

// good — atomic.Int64 carries its own synchronization; no pointer mismatch possible
var requestCount atomic.Int64

func handle() {
	requestCount.Add(1)
}

func current() int64 {
	return requestCount.Load()
}
```

## 32.15 Run `go vet`, `staticcheck`, `golangci-lint`, and `govulncheck` in CI; use `gopls` locally for real-time diagnostics.

> Why? Each tool catches a different class of problem: `go vet` catches
> compiler-adjacent mistakes, `staticcheck`/`golangci-lint` catch style
> and correctness issues (see [Chapter 33](33-linter-configuration.md)
> for the exact configuration this guide assumes), `govulncheck` checks
> your dependency graph against the Go vulnerability database, and
> `gopls` (the Go language server) surfaces diagnostics as you type
> instead of only at commit or CI time.

> Enforced by: staticcheck, revive, and the other linters detailed in [Chapter 33.2](33-linter-configuration.md)

```go
// bad — CI only runs "go build && go test"; vulnerable dependencies ship silently
// (CI config)
// steps:
//	- run: go build ./...
//	- run: go test ./...

// good — vet, lint, and vulnerability scanning all run before merge
// (CI config)
// steps:
//	- run: go vet ./...
//	- run: golangci-lint run
//	- run: govulncheck ./...
//	- run: go test -race ./...
```
