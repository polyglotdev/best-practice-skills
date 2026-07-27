<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 20. Concurrency

Goroutines are cheap to start and easy to forget about — which is exactly
the problem this chapter addresses. It draws from [Google Best Practices:
Concurrency and
synchronization](https://google.github.io/styleguide/go/best-practices#concurrency-and-synchronization),
[Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency),
and [Uber Style: Don't fire-and-forget
goroutines](https://github.com/uber-go/guide/blob/master/style.md#dont-fire-and-forget-goroutines)
and [No goroutines in
init()](https://github.com/uber-go/guide/blob/master/style.md#no-goroutines-in-init).
Channel-specific idioms (buffering, direction typing, `select`) are covered
in [Chapter 21](21-channels.md); mutexes and other synchronization
primitives are covered in [Chapter 22](22-sync-primitives.md).

**Linter alignment:** `bodyclose` is relevant here for any goroutine that
issues HTTP requests; it's relaxed inside `_test.go` files per this
project's `.golangci.yml` exclusions.

## 20.1 Give every goroutine a clear owner responsible for stopping it and waiting for it to exit.

> Why? [Uber Style: Don't fire-and-forget
> goroutines](https://github.com/uber-go/guide/blob/master/style.md#dont-fire-and-forget-goroutines)
> states the rule directly: "every goroutine must have a predictable time
> at which it will stop running; or there must be a way to signal to the
> goroutine that it should stop. In both cases, there must be a way [for]
> code to block and wait for the goroutine to finish." A goroutine with no
> owner is a goroutine nobody can stop, drain, or account for.

```go
// bad — nothing owns this goroutine; it runs until the process exits,
// with no way to stop it or know when it's done
func startFlusher(delay time.Duration) {
	go func() {
		ticker := time.NewTicker(delay)
		defer ticker.Stop()
		for range ticker.C {
			flush()
		}
	}()
}

// good — explicit stop/done channels give the caller ownership
func startFlusher(delay time.Duration) (stop func()) {
	stopCh := make(chan struct{})
	done := make(chan struct{})
	go func() {
		defer close(done)
		ticker := time.NewTicker(delay)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				flush()
			case <-stopCh:
				return
			}
		}
	}()
	return func() {
		close(stopCh)
		<-done
	}
}
```

## 20.2 Never spawn a bare `go func() { ... }()` without a plan for how it stops and how errors surface.

> Why? A goroutine literal launched inline, with no handle returned to the
> caller, is fire-and-forget by construction — [Uber Style: Don't
> fire-and-forget
> goroutines](https://github.com/uber-go/guide/blob/master/style.md#dont-fire-and-forget-goroutines)
> warns these "can also cause other issues like preventing unused objects
> from being garbage collected and holding onto resources that are
> otherwise no longer used." Before writing `go func() {`, know how it
> will be stopped and where its error, if any, will go.

```go
// bad — no reference to this goroutine exists anywhere after this line
func (s *Server) onRequest(req *Request) {
	go func() {
		if err := s.audit.Log(context.Background(), req); err != nil {
			log.Println(err) // the only trace this goroutine ever ran
		}
	}()
}

// good — bounded by the request's own lifetime, errors surfaced via errgroup
func (s *Server) onRequest(ctx context.Context, req *Request) error {
	g, ctx := errgroup.WithContext(ctx)
	g.Go(func() error {
		return s.audit.Log(ctx, req)
	})
	return g.Wait()
}
```

## 20.3 Use `errgroup.Group` when you need to coordinate multiple goroutines and propagate the first error.

> Why? [Google Best Practices: Concurrency and
> synchronization](https://google.github.io/styleguide/go/best-practices#concurrency-and-synchronization)
> recommends `errgroup` as "a convenient abstraction for a group of
> operations that can all fail or be canceled as a group," since "often
> only the first error is useful." It also cancels the shared context for
> the remaining goroutines the moment one fails, which a hand-rolled
> `sync.WaitGroup` doesn't do on its own.

```go
// bad — hand-rolled coordination; only the last error survives, and
// nothing cancels sibling goroutines when one fails
func fetchAll(ctx context.Context, urls []string) ([]*http.Response, error) {
	var wg sync.WaitGroup
	var mu sync.Mutex
	var lastErr error
	results := make([]*http.Response, len(urls))
	for i, u := range urls {
		wg.Add(1)
		go func(i int, u string) {
			defer wg.Done()
			resp, err := http.Get(u)
			mu.Lock()
			defer mu.Unlock()
			if err != nil {
				lastErr = err
				return
			}
			results[i] = resp
		}(i, u)
	}
	wg.Wait()
	return results, lastErr
}

// good — errgroup propagates the first error and cancels the group
func fetchAll(ctx context.Context, urls []string) ([]*http.Response, error) {
	g, ctx := errgroup.WithContext(ctx)
	results := make([]*http.Response, len(urls))
	for i, u := range urls {
		i, u := i, u
		g.Go(func() error {
			req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
			if err != nil {
				return err
			}
			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				return err
			}
			results[i] = resp
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return nil, err
	}
	return results, nil
}
```

## 20.4 Use `sync.WaitGroup` when you only need to wait for completion and don't need error propagation or cancellation.

> Why? Not every fan-out needs `errgroup`'s cancellation machinery.
> [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#concurrency) shows the
> channel-based drain pattern for this same purpose; `sync.WaitGroup` is
> the standard-library primitive for "block until N goroutines finish"
> when there's nothing to fail and nothing to cancel.

```go
// bad — reaches for errgroup where there's no error and nothing to cancel
func warmCaches(keys []string) {
	g := new(errgroup.Group)
	for _, k := range keys {
		k := k
		g.Go(func() error {
			warm(k)
			return nil
		})
	}
	_ = g.Wait()
}

// good — WaitGroup is the simpler, sufficient tool
func warmCaches(keys []string) {
	var wg sync.WaitGroup
	for _, k := range keys {
		wg.Add(1)
		go func(k string) {
			defer wg.Done()
			warm(k)
		}(k)
	}
	wg.Wait()
}
```

## 20.5 Never spawn a goroutine from an `init()` function.

> Why? [Uber Style: No goroutines in
> init()](https://github.com/uber-go/guide/blob/master/style.md#no-goroutines-in-init)
> requires that "if a package has need of a background goroutine, it must
> expose an object that is responsible for managing [the] goroutine's
> lifetime," with explicit `Close`/`Stop`/`Shutdown` methods. A goroutine
> started in `init()` runs before `main` even begins and has no owner that
> can ever stop it.

```go
// bad — goroutine starts at import time with no owner and no way to stop it
func init() {
	go func() {
		for {
			flushMetrics()
			time.Sleep(time.Minute)
		}
	}()
}

// good — caller owns the lifetime explicitly
type MetricsFlusher struct {
	stop chan struct{}
	done chan struct{}
}

func NewMetricsFlusher() *MetricsFlusher {
	f := &MetricsFlusher{stop: make(chan struct{}), done: make(chan struct{})}
	go f.run()
	return f
}

func (f *MetricsFlusher) run() {
	defer close(f.done)
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			flushMetrics()
		case <-f.stop:
			return
		}
	}
}

func (f *MetricsFlusher) Close() {
	close(f.stop)
	<-f.done
}
```

## 20.6 Design concurrent code around structured concurrency: a goroutine's lifetime should nest inside the lifetime of the code that started it.

> Why? [Google Best Practices: Concurrency and
> synchronization](https://google.github.io/styleguide/go/best-practices#concurrency-and-synchronization)'s
> emphasis on documenting cleanup and ownership reflects a broader
> principle: a function that starts goroutines should not return until it
> knows their fate, mirroring how a function that opens a resource should
> not return without closing it (see [Chapter 23](23-cleanup.md)).
> Goroutines that outlive their parent call, with no defined relationship
> to it, make reasoning about shutdown and error propagation nearly
> impossible.

```go
// bad — DoAll returns while its goroutines might still be running
func (v Vector) DoAll(u Vector) {
	for i := 0; i < numCPU; i++ {
		go v.doSome(i, u)
	}
	// returns immediately; caller has no idea when the work finishes
}

// good — DoAll doesn't return until every goroutine it started has
func (v Vector) DoAll(u Vector) {
	var wg sync.WaitGroup
	for i := 0; i < numCPU; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			v.doSome(i, u)
		}(i)
	}
	wg.Wait()
}
```

## 20.7 Close every `http.Response.Body`, including inside goroutines, with `defer` right after the error check.

> Why? An `http.Response.Body` that's never closed leaks the underlying
> connection, and leaks compound quickly in a goroutine that runs
> repeatedly (a poller, a fan-out worker). This project's `bodyclose`
> linter enforces this everywhere except `_test.go` files, where it's
> excluded because short-lived test HTTP calls are lower risk and often
> use throwaway servers. **Violation — enforced by `bodyclose` (outside
> `_test.go`; excluded in `_test.go` per this project's `.golangci.yml`).**

```go
// bad — bodyclose flags this: resp.Body is never closed
func poll(ctx context.Context, url string) error {
	for {
		req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return err
		}
		process(resp)
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
		}
	}
}

// good
func poll(ctx context.Context, url string) error {
	for {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
		if err != nil {
			return err
		}
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return err
		}
		process(resp)
		resp.Body.Close()
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
		}
	}
}
```

## 20.8 Bound the number of concurrently running goroutines when the work source is unbounded (incoming requests, queue items).

> Why? [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#concurrency) shows that
> spawning one goroutine per incoming request without a limit "can consume
> unlimited resources if the requests come in too fast," and fixes it
> either with a buffered semaphore channel or a fixed pool of worker
> goroutines reading from a shared channel.

```go
// bad — unbounded goroutine creation, one per request
func Serve(queue <-chan *Request) {
	for req := range queue {
		go handle(req)
	}
}

// good — a fixed pool of workers bounds concurrent work
func Serve(queue <-chan *Request, workers int) {
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for req := range queue {
				handle(req)
			}
		}()
	}
	wg.Wait()
}
```

## 20.9 Document whether a type's methods are safe for concurrent use, especially when it's not obvious from the method name.

> Why? [Google Best Practices: Concurrency and
> synchronization](https://google.github.io/styleguide/go/best-practices#concurrency-and-synchronization)
> asks authors to call out concurrency safety "if it is unclear whether
> the operation is read-only or mutating" — a cache `Lookup` that promotes
> an entry internally, for example, mutates state even though its name
> suggests otherwise.

```go
// bad — Lookup looks read-only, but promotes entries in the LRU list
// internally; nothing warns callers this needs synchronization
package lrucache

func (c *Cache) Lookup(key string) (data []byte, ok bool) {
	return c.lookup(key)
}

// good
package lrucache

// Lookup returns the data associated with the key from the cache.
//
// This operation is not safe for concurrent use.
func (c *Cache) Lookup(key string) (data []byte, ok bool) {
	return c.lookup(key)
}
```

## 20.10 Treat read-only operations as concurrency-safe by default; only call out synchronization requirements for mutating ones.

> Why? [Google Best Practices: Concurrency and
> synchronization](https://google.github.io/styleguide/go/best-practices#concurrency-and-synchronization)
> notes "Go users assume that conceptually read-only operations are safe
> for concurrent use and do not require extra synchronization" — so a
> godoc reminder on every read-only method is redundant. Reserve the
> explicit callout for methods that actually mutate shared state.

```go
// bad — redundant remark; readers already assume this
// Len returns the number of bytes of the unread portion of the buffer.
//
// It is safe to be called concurrently by multiple goroutines.
func (b *Buffer) Len() int { return len(b.buf) }

// good — the remark is dropped where it adds nothing
// Len returns the number of bytes of the unread portion of the buffer.
func (b *Buffer) Len() int { return len(b.buf) }
```

## 20.11 Prefer sharing memory by communicating over synchronizing access to shared state, when the design allows it.

> Why? [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#sharing_by_communicating)
> states Go's guiding principle directly: "do not communicate by sharing
> memory; instead, share memory by communicating." Passing ownership of a
> value through a channel eliminates an entire class of races that a
> shared variable plus a mutex only manages, rather than eliminates.

```go
// bad — shared counter guarded by a mutex from multiple goroutines
type Aggregator struct {
	mu    sync.Mutex
	total int
}

func (a *Aggregator) Add(n int) {
	a.mu.Lock()
	a.total += n
	a.mu.Unlock()
}

// good — a single owner goroutine receives values over a channel;
// nothing else ever touches `total` directly
func runAggregator(values <-chan int) <-chan int {
	totals := make(chan int)
	go func() {
		defer close(totals)
		total := 0
		for v := range values {
			total += v
		}
		totals <- total
	}()
	return totals
}
```

## 20.12 Use `go.uber.org/goleak` (or equivalent) in package tests that spawn goroutines, to catch leaks automatically.

> Why? [Uber Style: Don't fire-and-forget
> goroutines](https://github.com/uber-go/guide/blob/master/style.md#dont-fire-and-forget-goroutines)
> recommends this directly: "use `go.uber.org/goleak` to test for
> goroutine leaks inside packages that may spawn goroutines." A leaked
> goroutine in a unit test is a preview of the same leak in production,
> caught while it's cheap to fix.

```go
// bad — no leak detection; a goroutine started by New() that never
// stops will silently pass every test
func TestNew(t *testing.T) {
	f := New()
	f.Close()
}

// good
func TestMain(m *testing.M) {
	goleak.VerifyTestMain(m)
}

func TestNew(t *testing.T) {
	f := New()
	defer f.Close()
}
```

## 20.13 Distinguish concurrency (structuring independent components) from parallelism (running work simultaneously for speed) when choosing a design.

> Why? [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#parallelization) warns
> against conflating the two: "Go is a concurrent language, not a parallel
> one, and not all parallelization problems fit Go's model." Reaching for
> goroutines purely to "make it faster" without an actual independent unit
> of work to parallelize adds synchronization overhead without benefit.

```go
// bad — spawns goroutines for a computation with no independent pieces
// to parallelize; the shared accumulator serializes everything anyway
func sumSquares(nums []int) int {
	var mu sync.Mutex
	total := 0
	var wg sync.WaitGroup
	for _, n := range nums {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			mu.Lock()
			total += n * n
			mu.Unlock()
		}(n)
	}
	wg.Wait()
	return total
}

// good — this workload has no independent chunks worth the overhead;
// a plain loop is simpler, correct, and just as fast
func sumSquares(nums []int) int {
	total := 0
	for _, n := range nums {
		total += n * n
	}
	return total
}
```
