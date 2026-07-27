<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 21. Channels

Channels are Go's mechanism for passing ownership of a value between
goroutines, and their design rewards small, direction-typed, minimally
buffered usage. This chapter draws from [Google Best Practices: Channel
directions](https://google.github.io/styleguide/go/best-practices#channel-directions),
[Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency)
(channels, channels of channels, and parallelization), and [Uber Style:
Channel Size is One or
None](https://github.com/uber-go/guide/blob/master/style.md#channel-size-is-one-or-none).
Goroutine lifetime and ownership are covered in [Chapter
20](20-concurrency.md); this chapter is specifically about the channel
values themselves.

## 21.1 Default new channels to unbuffered (size zero) or, when a handoff needs slack, size one.

> Why? [Uber Style: Channel Size is One or
> None](https://github.com/uber-go/guide/blob/master/style.md#channel-size-is-one-or-none)
> states plainly: "channels should usually have a size of one or be
> unbuffered... any other size must be subject to a high level of
> scrutiny." An unbuffered channel keeps sender and receiver synchronized;
> a size-one buffer allows exactly one outstanding handoff without
> blocking the sender.

```go
// bad — an arbitrary large buffer with no stated reason
c := make(chan int, 64)

// good — unbuffered: sender and receiver rendezvous directly
c := make(chan int)

// good — size one: exactly one outstanding value, no more
c := make(chan int, 1)
```

## 21.2 Treat any channel buffer larger than one as a design smell requiring explicit justification.

> Why? [Uber Style: Channel Size is One or
> None](https://github.com/uber-go/guide/blob/master/style.md#channel-size-is-one-or-none)
> asks: "how is the size determined, what prevents the channel from
> filling up under load and blocking writers, and what happens when this
> occurs?" A large buffer doesn't remove backpressure, it just delays
> when it's felt — usually until production load reveals the channel was
> undersized after all.

```go
// bad — "ought to be enough for anybody," with no analysis behind it
jobs := make(chan Job, 1000)

// good — bounded, and the size is derived from an explicit, documented
// concurrency limit rather than guessed
const maxInFlight = 10 // matches the downstream worker pool size

jobs := make(chan Job, maxInFlight)
```

## 21.3 Type channel parameters with a direction (`chan<-`, `<-chan`) whenever the function only sends or only receives.

> Why? [Google Best Practices: Channel
> directions](https://google.github.io/styleguide/go/best-practices#channel-directions)
> recommends specifying direction because it "prevents casual programming
> errors" — a function that only reads from a channel can't accidentally
> close it or send on it, and the compiler catches the mistake instead of
> it surfacing as a runtime panic.

```go
// bad — sum could accidentally close or send on values
func sum(values chan int) (out int) {
	for v := range values {
		out += v
	}
	return
}

// good — <-chan makes misuse a compile error
func sum(values <-chan int) int {
	out := 0
	for v := range values {
		out += v
	}
	return out
}
```

## 21.4 Let the sender close a channel, never the receiver.

> Why? [Google Best Practices: Channel
> directions](https://google.github.io/styleguide/go/best-practices#channel-directions)
> demonstrates the failure mode directly: if a receiver closes a channel
> the sender might still write to (or close again), "a second close
> triggers a panic." Only the goroutine that knows no more values are
> coming — the sender — is in a position to close it safely.

```go
// bad — receiver closes a channel the sender may still be writing to
func consume(values chan int) {
	for v := range values {
		process(v)
	}
	close(values) // sender may already be gone, or may send again — panic risk
}

// good — sender closes when done producing
func produce(values chan<- int, nums []int) {
	defer close(values)
	for _, n := range nums {
		values <- n
	}
}

func consume(values <-chan int) {
	for v := range values {
		process(v)
	}
}
```

## 21.5 Use `range` over a channel to drain it until it's closed, instead of manually checking the ok-value in a loop.

> Why? `for v := range ch` already stops cleanly the moment `ch` is closed
> and drained, matching the idiom [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#concurrency) uses
> throughout its channel examples (`for req := range queue`). A manual
> comma-ok loop achieves the same result with more code and more room for
> a mistake in the exit condition.

```go
// bad — manually replicates what range already does
for {
	v, ok := <-values
	if !ok {
		break
	}
	process(v)
}

// good
for v := range values {
	process(v)
}
```

## 21.6 Use the comma-ok form when receiving from a channel that might be closed and you need to distinguish a zero value from closure.

> Why? A closed channel yields the zero value on every subsequent receive
> with no error — silently indistinguishable from a real zero value sent
> deliberately. The two-value receive form (`v, ok := <-ch`) is the only
> way to tell "channel closed" apart from "received an actual zero."

```go
// bad — can't tell a real 0 from a closed channel
v := <-values
if v == 0 {
	// closed, or genuinely received 0? Ambiguous.
}

// good
v, ok := <-values
if !ok {
	// channel closed and drained
	return
}
```

## 21.7 Use `select` with a `default` case for a non-blocking send or receive.

> Why? A bare `ch <- v` or `<-ch` blocks until a corresponding operation
> is ready. Adding `default` to a `select` around it makes the operation
> opportunistic — try once, and if nothing is ready, move on — which is
> the standard pattern for polling a channel without stalling the calling
> goroutine.

```go
// bad — blocks indefinitely if nothing is reading from results
results <- computed

// good — non-blocking: drop the value rather than stall if the
// receiver isn't ready
select {
case results <- computed:
default:
	// receiver not ready; caller decides what "dropped" means here
}
```

## 21.8 Use `ctx.Done()` inside a `select` to make a channel operation cancelable.

> Why? A goroutine blocked on a plain channel receive has no way to notice
> that the surrounding operation was cancelled. Racing the receive against
> `ctx.Done()` in a `select` lets the goroutine exit promptly when the
> context is cancelled, instead of leaking until the channel eventually
> produces a value (see [Chapter 19](19-context.md) for context
> propagation rules).

```go
// bad — blocks forever if nothing is ever sent, ignoring cancellation
func await(ctx context.Context, results <-chan int) (int, error) {
	return <-results, nil
}

// good
func await(ctx context.Context, results <-chan int) (int, error) {
	select {
	case v := <-results:
		return v, nil
	case <-ctx.Done():
		return 0, ctx.Err()
	}
}
```

## 21.9 Use a `chan struct{}` for pure signaling channels, not `chan bool` or `chan int`.

> Why? A signal-only channel never actually needs a payload — closing it
> or sending an empty struct is the signal itself. `struct{}` occupies no
> memory per element, and its type communicates "this value's payload is
> irrelevant" more clearly than a `bool` that's always sent as `true`.

```go
// bad — the bool value is never inspected; it's always true
done := make(chan bool)
go func() {
	work()
	done <- true
}()
<-done

// good
done := make(chan struct{})
go func() {
	work()
	close(done)
}()
<-done
```

## 21.10 Pass a `chan *http.Request`-style reply channel inside a request struct when each caller needs its own private response path.

> Why? [Effective Go: Channels of
> channels](https://go.dev/doc/effective_go#chan_of_chan) shows this
> pattern for a demultiplexed RPC-like system: bundling a dedicated
> reply channel inside each request lets many callers share one work
> queue while each still gets its own, uncontended response path — "a
> framework for a rate-limited, parallel, non-blocking RPC system, and
> there's not a mutex in sight."

```go
// bad — a single shared response channel forces callers to filter for
// their own response among everyone else's
type Request struct {
	Args []int
	F    func([]int) int
}

var sharedResults = make(chan int)

// good — each request carries its own reply channel
type Request struct {
	Args       []int
	F          func([]int) int
	ResultChan chan int
}

func handle(queue <-chan *Request) {
	for req := range queue {
		req.ResultChan <- req.F(req.Args)
	}
}
```

## 21.11 Use a buffered channel as a counting semaphore only when you also document its capacity as the concurrency limit.

> Why? [Effective Go:
> Concurrency](https://go.dev/doc/effective_go#concurrency) shows
> `sem := make(chan int, MaxOutstanding)` used exactly this way: the
> buffer capacity *is* the concurrency limit, so it must be named and
> documented as such — otherwise a reader sees just another channel and
> has no way to know its size encodes a deliberate throttling decision.

```go
// bad — magic number with no indication it's a concurrency limit
var sem = make(chan int, 20)

func handle(r *Request) {
	sem <- 1
	defer func() { <-sem }()
	process(r)
}

// good — named constant documents the limit's purpose
// maxOutstanding bounds the number of concurrent calls to process.
const maxOutstanding = 20

var sem = make(chan struct{}, maxOutstanding)

func handle(r *Request) {
	sem <- struct{}{}
	defer func() { <-sem }()
	process(r)
}
```

## 21.12 Drain a channel fully with `range` when collecting results from a known, fixed number of goroutines — don't guess with a fixed sleep.

> Why? [Effective Go:
> Parallelization](https://go.dev/doc/effective_go#parallelization) uses a
> completion channel drained exactly `numCPU` times: "we just count the
> completion signals by draining the channel after launching all the
> goroutines." Waiting on a timer instead of a channel receive races
> against the actual completion of the work and either wastes time or
> finishes too early.

```go
// bad — guesses how long the work takes instead of waiting for it
func (v Vector) doAll(u Vector) {
	for i := 0; i < numCPU; i++ {
		go v.doSome(i, u)
	}
	time.Sleep(2 * time.Second) // hope that's long enough
}

// good — waits precisely for every piece to finish, no guessing
func (v Vector) doAll(u Vector) {
	c := make(chan int, numCPU)
	for i := 0; i < numCPU; i++ {
		go v.doSome(i, u, c)
	}
	for i := 0; i < numCPU; i++ {
		<-c
	}
}
```
