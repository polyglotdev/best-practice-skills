<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 23. Goroutines & Lifecycle

Starting a goroutine is one line of code; knowing when it stops is the hard
part. This chapter draws from [Google Best Practices:
Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency),
[Google Best Practices:
Cleanup](https://google.github.io/styleguide/go/best-practices#cleanup-functions-and-defer),
and Uber's guidance on [avoiding fire-and-forget
goroutines](https://github.com/uber-go/guide/blob/master/style.md#no-goroutines-in-init)
and [deferring to clean
up](https://github.com/uber-go/guide/blob/master/style.md#defer-to-clean-up).
The unifying rule: every goroutine you start must have a clear owner who
knows how it terminates, and every resource acquired must have a `defer`
that releases it on the same code path that acquired it. Error handling and
`context` propagation are covered in more depth in the errors and contexts
chapters; this chapter focuses on lifecycle and shutdown.

## 23.1 Never start a goroutine without knowing how and when it stops.

> Why? A goroutine with no owner and no exit condition is a leak. It keeps
> its stack, keeps whatever it closed over alive, and keeps running after
> the request or process that spawned it should have ended. [Google Best
> Practices: Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> emphasizes that goroutine lifetimes must be well understood, not left
> implicit.

```go
// bad — goroutine has no exit signal and outlives the request
func handleUpload(ctx context.Context, r io.Reader) {
	go func() {
		processSlowly(r)
	}()
}

// good — goroutine is bounded by ctx and the caller can wait for it
func handleUpload(ctx context.Context, r io.Reader) error {
	done := make(chan error, 1)
	go func() {
		done <- processSlowly(ctx, r)
	}()

	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}
```

## 23.2 Use `errgroup.Group` for structured concurrency instead of raw goroutines and channels.

> Why? `errgroup` gives a group of goroutines a shared cancellation context
> and collects the first error, which is exactly the pattern hand-rolled
> `sync.WaitGroup` plus error-channel code tries to reinvent, usually with
> subtle bugs. [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> recommends reaching for well-tested concurrency helpers over ad hoc
> primitives.

```go
// bad — manual WaitGroup, no cancellation, first error silently dropped
func fetchAll(urls []string) error {
	var wg sync.WaitGroup
	var firstErr error
	for _, u := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			if err := fetch(u); err != nil {
				firstErr = err // data race on firstErr
			}
		}(u)
	}
	wg.Wait()
	return firstErr
}

// good — errgroup shares a context and returns the first error safely
func fetchAll(ctx context.Context, urls []string) error {
	g, ctx := errgroup.WithContext(ctx)
	for _, u := range urls {
		u := u
		g.Go(func() error {
			return fetch(ctx, u)
		})
	}
	return g.Wait()
}
```

## 23.3 Propagate `context` cancellation into every goroutine you start; never let a child goroutine outlive its parent's context.

> Why? [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> treats `context.Context` as the mechanism for signaling that work should
> stop. A goroutine that ignores the context it was handed keeps running
> — and keeps consuming resources — after the caller has moved on or the
> request has been canceled.

```go
// bad — the spawned goroutine has no way to learn the caller gave up
func Watch(ctx context.Context, ch <-chan Event) {
	go func() {
		for e := range ch {
			handle(e)
		}
	}()
}

// good — ctx.Done() is part of the select, so the goroutine exits promptly
func Watch(ctx context.Context, ch <-chan Event) {
	go func() {
		for {
			select {
			case e, ok := <-ch:
				if !ok {
					return
				}
				handle(e)
			case <-ctx.Done():
				return
			}
		}
	}()
}
```

## 23.4 Pair every resource acquisition with a `defer` release at the point of ownership, not deep in a later branch.

> Why? [Google Best Practices:
> Cleanup](https://google.github.io/styleguide/go/best-practices#cleanup-functions-and-defer)
> and Uber's [Defer to Clean
> Up](https://github.com/uber-go/guide/blob/master/style.md#defer-to-clean-up)
> both call out `defer` immediately after acquisition as the way to
> guarantee cleanup runs on every exit path, including panics and early
> returns added later by someone who forgets the cleanup at the bottom.

```go
// bad — cleanup is easy to forget on the error return added later
func readConfig(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	data, err := io.ReadAll(f)
	if err != nil {
		return nil, err // f.Close() never runs
	}
	f.Close()
	return data, nil
}

// good — defer runs on every exit path, present or future
func readConfig(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	return io.ReadAll(f)
}
```

## 23.5 Use `sync.WaitGroup` only when you need to wait for goroutines with no per-goroutine error to report; otherwise prefer `errgroup`.

> Why? `sync.WaitGroup` has no built-in way to surface an error or cancel
> siblings when one fails, which is why [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> and the `errgroup` package exist for the common case of fan-out work
> that can fail. Reserve raw `WaitGroup` for fire-and-join work where
> failure isn't part of the contract, such as flushing independent
> metrics.

```go
// bad — WaitGroup used for fallible work, errors go nowhere
func flushAndFetch(items []Item) {
	var wg sync.WaitGroup
	for _, it := range items {
		wg.Add(1)
		go func(it Item) {
			defer wg.Done()
			_ = fetchRemote(it) // error dropped on the floor
		}(it)
	}
	wg.Wait()
}

// good — WaitGroup for genuinely error-free, independent work
func flushCounters(counters []*Counter) {
	var wg sync.WaitGroup
	for _, c := range counters {
		wg.Add(1)
		go func(c *Counter) {
			defer wg.Done()
			c.FlushToMetrics()
		}(c)
	}
	wg.Wait()
}
```

## 23.6 Add every goroutine to its `WaitGroup` before starting it, never inside it.

> Why? `wg.Add` must happen-before the `wg.Wait` call it is meant to be
> counted by. Calling `Add` from inside the goroutine races with `Wait`
> and can let `Wait` return before the goroutine has even registered
> itself — a classic bug flagged by `go test -race` and covered by
> [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency).

```go
// bad — Add races with a concurrent Wait
func run(jobs []Job) {
	var wg sync.WaitGroup
	for _, j := range jobs {
		go func(j Job) {
			wg.Add(1) // too late; Wait may already have returned
			defer wg.Done()
			j.Run()
		}(j)
	}
	wg.Wait()
}

// good — Add happens on the goroutine that starts the work
func run(jobs []Job) {
	var wg sync.WaitGroup
	for _, j := range jobs {
		wg.Add(1)
		go func(j Job) {
			defer wg.Done()
			j.Run()
		}(j)
	}
	wg.Wait()
}
```

## 23.7 Implement graceful shutdown by canceling a root context and waiting for in-flight work to finish before the process exits.

> Why? Killing a server without draining in-flight requests corrupts
> client-visible state and drops responses that were nearly done. [Google
> Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> expects long-running programs to listen for shutdown signals and stop
> cleanly rather than being killed mid-request.

```go
// bad — os.Exit or an unhandled SIGTERM cuts off in-flight requests
func main() {
	srv := &http.Server{Addr: ":8080", Handler: newRouter()}
	log.Fatal(srv.ListenAndServe())
}

// good — SIGTERM triggers a bounded, graceful drain
func main() {
	srv := &http.Server{Addr: ":8080", Handler: newRouter()}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("serve: %v", err)
		}
	}()

	<-ctx.Done()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Printf("shutdown: %v", err)
	}
}
```

## 23.8 Bound fan-out concurrency with a worker pool or semaphore instead of spawning one goroutine per item.

> Why? Unbounded fan-out over a large or attacker-controlled input size
> can exhaust memory, file descriptors, or downstream connection pools.
> [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> calls out bounding concurrency as part of understanding goroutine
> lifetimes and resource usage.

```go
// bad — one goroutine per URL, no ceiling on concurrency
func fetchAll(urls []string) {
	var wg sync.WaitGroup
	for _, u := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			fetch(u)
		}(u)
	}
	wg.Wait()
}

// good — a bounded worker pool caps concurrent fetches
func fetchAll(ctx context.Context, urls []string, workers int) error {
	g, ctx := errgroup.WithContext(ctx)
	sem := make(chan struct{}, workers)

	for _, u := range urls {
		u := u
		sem <- struct{}{}
		g.Go(func() error {
			defer func() { <-sem }()
			return fetch(ctx, u)
		})
	}
	return g.Wait()
}
```

## 23.9 Ensure every goroutine a function starts has terminated — or is guaranteed to terminate independently — before that function returns.

> Why? A function that spawns a goroutine and returns without joining it
> makes the goroutine's lifetime invisible to its caller. [Google Best
> Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> treats this invisibility as the root cause of most goroutine leaks:
> nobody can reason about when the work actually finishes.

```go
// bad — Start returns immediately; caller has no way to know the
// goroutine ever stops, including during tests
func (s *Scheduler) Start() {
	go s.loop()
}

// good — Start returns a stop function that waits for loop to exit
func (s *Scheduler) Start() (stop func()) {
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})

	go func() {
		defer close(done)
		s.loop(ctx)
	}()

	return func() {
		cancel()
		<-done
	}
}
```

## 23.10 Close channels from the sender side only, and only when no more values will be sent.

> Why? Closing a channel signals "no more values" to receivers. Closing
> from a receiver, or closing twice, panics at runtime. [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#concurrency) establishes
> that the sender, not the receiver, should be the one to close a
> channel, since only the sender knows when sending is truly done.

```go
// bad — receiver closes the channel; a second send panics
func consume(ch chan int) {
	for v := range ch {
		process(v)
	}
	close(ch) // wrong goroutine, wrong role
}

// good — the producer closes once it is done sending
func produce(ch chan<- int, values []int) {
	defer close(ch)
	for _, v := range values {
		ch <- v
	}
}
```

## 23.11 Use `context.AfterFunc` or a `select` with `ctx.Done()` instead of leaking a goroutine that blocks on a channel forever.

> Why? A goroutine blocked on `<-ch` with no timeout and no cancellation
> path lives as long as the process if `ch` is never written to or
> closed. [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> expects every blocking wait to have an associated cancellation
> mechanism.

```go
// bad — blocks forever if the event never arrives
func waitForReady(ready <-chan struct{}) {
	go func() {
		<-ready
		log.Println("ready")
	}()
}

// good — context.AfterFunc ties the wait to cancellation
func waitForReady(ctx context.Context, ready <-chan struct{}) {
	stop := context.AfterFunc(ctx, func() {
		log.Println("gave up waiting for ready")
	})
	go func() {
		defer stop()
		select {
		case <-ready:
			log.Println("ready")
		case <-ctx.Done():
		}
	}()
}
```

## 23.12 Recover from panics inside a goroutine only at the top of that goroutine, and always re-signal completion.

> Why? A panic in a spawned goroutine that is not recovered crashes the
> whole process, since `recover` only works in the same goroutine that
> panicked. [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> notes that goroutines doing background work need their own panic
> containment so one failing task doesn't take down unrelated work.

```go
// bad — a panic in the goroutine crashes the entire process
func (s *Server) handleAsync(job Job) {
	go func() {
		job.Run() // panics here kill the process, not just this job
	}()
}

// good — panic is contained, logged, and completion is still signaled
func (s *Server) handleAsync(job Job) {
	go func() {
		defer func() {
			if r := recover(); r != nil {
				s.logger.Error("job panicked", "job", job.ID, "panic", r)
			}
		}()
		job.Run()
	}()
}
```

## 23.13 Always close `http.Response.Body`, and know when a discarded `Close` error is acceptable versus when it must be checked.

> Why? Every `*http.Response` returned with a non-nil error must have its
> `Body` closed on every code path, including error branches, or the
> underlying connection cannot be reused and eventually the connection
> pool is exhausted. The user's lint configuration enforces this via
> `bodyclose`, and separately exempts `(io.Closer).Close` from `errcheck`
> — an unchecked `Close()` on a read-only body is safe to ignore because a
> failed close on an already-fully-read response carries no recoverable
> information. That exemption does not extend to closers whose `Close`
> can signal a real, actionable failure — most notably `os.File` opened
> for writing, where a failed `Close` can mean buffered data was never
> flushed to disk.

> Enforced by: bodyclose (missing `resp.Body.Close()`); errcheck exempts `(io.Closer).Close` (see [Chapter 33.9](33-linter-configuration.md))

```go
// bad — response body never closed; connection cannot be reused
func fetch(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	return io.ReadAll(resp.Body)
}

// good — Body is always closed; the discarded Close error is acceptable
// for a read-only response body
func fetch(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	return io.ReadAll(resp.Body)
}

// good — a write-oriented closer's error IS worth checking: a failed
// Close on a file opened for writing can mean data was never flushed
func writeReport(path string, data []byte) (err error) {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() {
		if cerr := f.Close(); cerr != nil && err == nil {
			err = fmt.Errorf("close report file: %w", cerr)
		}
	}()

	_, err = f.Write(data)
	return err
}
```
