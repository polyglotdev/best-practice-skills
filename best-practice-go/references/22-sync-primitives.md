<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 22. Sync Primitives

Channels aren't always the right tool — sometimes protecting a piece of
shared state with a mutex is simpler and faster than routing every access
through a goroutine. This chapter draws from [Uber Style: Zero-value
Mutexes are
Valid](https://github.com/uber-go/guide/blob/master/style.md#zero-value-mutexes-are-valid)
and [Use
go.uber.org/atomic](https://github.com/uber-go/guide/blob/master/style.md#use-goubercomatomic),
with the underlying shared-memory model discussed in the concurrency
subsections of [Effective Go](https://go.dev/doc/effective_go#concurrency).
Channel-based alternatives are covered in [Chapter 21](21-channels.md);
this chapter is about `sync` and `sync/atomic` specifically.

**Linter alignment:** this chapter maps to `govet`'s `copylocks` check
(part of `enable-all` in this project's `.golangci.yml`) and to `unused`
for dead mutex fields.

## 22.1 Declare mutexes with their zero value — never `new(sync.Mutex)` or a pointer field.

> Why? [Uber Style: Zero-value Mutexes are
> Valid](https://github.com/uber-go/guide/blob/master/style.md#zero-value-mutexes-are-valid)
> states "the zero-value of `sync.Mutex` and `sync.RWMutex` is valid, so
> you almost never need a pointer to a mutex." A `var mu sync.Mutex` is
> already ready to lock; wrapping it in `new()` or a pointer just adds an
> unnecessary allocation and an extra nil-check risk.

```go
// bad
mu := new(sync.Mutex)
mu.Lock()

// good
var mu sync.Mutex
mu.Lock()
```

## 22.2 Store a mutex as a plain (non-pointer) field on the struct it protects.

> Why? [Uber Style: Zero-value Mutexes are
> Valid](https://github.com/uber-go/guide/blob/master/style.md#zero-value-mutexes-are-valid)
> requires this: "if you use a struct by pointer, then the mutex should be
> a non-pointer field on it." Since the containing struct is already
> accessed through a pointer, the mutex field doesn't need its own
> indirection — and a pointer field just adds a nil-dereference risk if
> the struct is ever constructed with its zero value directly.

```go
// bad — unnecessary pointer indirection
type Cache struct {
	mu   *sync.Mutex
	data map[string]string
}

func NewCache() *Cache {
	return &Cache{mu: new(sync.Mutex), data: make(map[string]string)}
}

// good
type Cache struct {
	mu   sync.Mutex
	data map[string]string
}

func NewCache() *Cache {
	return &Cache{data: make(map[string]string)}
}
```

## 22.3 Never copy a struct that contains a `sync.Mutex` (or any `sync` type) — pass it by pointer everywhere.

> Why? Copying a locked or previously-used mutex duplicates its internal
> state, producing two mutexes that no longer protect the same critical
> section — each goroutine may believe it holds the lock while the other
> proceeds unguarded. `govet`'s `copylocks` analyzer (included under
> `enable-all` in this project's config) fails the build the moment a
> `sync.Mutex`-containing value is copied by assignment, by value
> parameter, or by range. **Violation — enforced by `govet`
> (`copylocks`).**

```go
// bad — govet flags this: passing Cache by value copies its mutex
func snapshot(c Cache) map[string]string {
	c.mu.Lock()
	defer c.mu.Unlock()
	out := make(map[string]string, len(c.data))
	for k, v := range c.data {
		out[k] = v
	}
	return out
}

// good — pass by pointer; only one mutex ever exists
func snapshot(c *Cache) map[string]string {
	c.mu.Lock()
	defer c.mu.Unlock()
	out := make(map[string]string, len(c.data))
	for k, v := range c.data {
		out[k] = v
	}
	return out
}
```

## 22.4 Never embed a mutex — always give it a named field. (See also [Chapter 15, §15.5](15-embedding.md).)

> Why? Embedding `sync.Mutex` promotes `Lock`/`Unlock` onto the outer
> type's own exported method set, letting any caller lock or unlock your
> internal state directly. A named field keeps the mutex an
> implementation detail the type controls entirely on its own terms.

```go
// bad — Lock/Unlock leak into SMap's public API
type SMap struct {
	sync.Mutex
	data map[string]string
}

// good
type SMap struct {
	mu   sync.Mutex
	data map[string]string
}
```

## 22.5 Use typed atomics from `sync/atomic` (`atomic.Int64`, `atomic.Bool`, etc., Go 1.19+) instead of raw `atomic.AddInt64`-style functions on plain fields.

> Why? [Uber Style: Use
> go.uber.org/atomic](https://github.com/uber-go/guide/blob/master/style.md#use-goubercomatomic)
> explains the risk with raw atomics: "it is easy to forget to use the
> atomic operation to read or modify the variables," since the field
> itself is just a plain `int32`/`int64` that compiles fine when accessed
> non-atomically by mistake. Go 1.19 added typed atomics
> (`atomic.Int64`, `atomic.Bool`, `atomic.Value`, and others) to the
> standard library, making the third-party `go.uber.org/atomic` package
> unnecessary in modern code — the type itself now hides the underlying
> representation and forces every access through its methods.

```go
// bad — was idiomatic pre-1.19: nothing stops a direct, non-atomic
// read of running elsewhere in the file
type foo struct {
	running int32 // atomic
}

func (f *foo) start() {
	if atomic.SwapInt32(&f.running, 1) == 1 {
		return
	}
}

func (f *foo) isRunning() bool {
	return f.running == 1 // race! bypasses the atomic package entirely
}

// good — the type itself only exposes atomic operations
type foo struct {
	running atomic.Bool
}

func (f *foo) start() {
	if f.running.Swap(true) {
		return
	}
}

func (f *foo) isRunning() bool {
	return f.running.Load()
}
```

## 22.6 Use `sync.Once` for lazy, one-time initialization instead of a boolean guard plus a mutex.

> Why? A hand-rolled "initialized" flag checked under a mutex is easy to
> get subtly wrong — checking the flag before acquiring the lock races,
> and checking it only after the lock defeats the purpose of avoiding lock
> contention on the common path. `sync.Once` implements the correct
> double-checked pattern once, correctly, in the standard library.

```go
// bad — check-then-lock-then-check-again, hand-rolled and easy to get wrong
type Client struct {
	mu          sync.Mutex
	initialized bool
	conn        *Connection
}

func (c *Client) conn() *Connection {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.initialized {
		c.connVal = dial()
		c.initialized = true
	}
	return c.connVal
}

// good
type Client struct {
	once sync.Once
	conn *Connection
}

func (c *Client) getConn() *Connection {
	c.once.Do(func() {
		c.conn = dial()
	})
	return c.conn
}
```

## 22.7 Use `sync.Pool` only for reusing short-lived, GC-heavy allocations — not as a general object cache.

> Why? `sync.Pool` items can be evicted by the garbage collector at any
> time, with no eviction callback and no guaranteed retention across a GC
> cycle. It's designed to reduce allocator pressure for transient objects
> (buffers, scratch slices) that are cheap to recreate — treating it as a
> cache for expensive-to-construct or long-lived objects will silently
> lose them and force reconstruction anyway, without any correctness
> signal.

```go
// bad — expects Pool to retain expensive, long-lived connections;
// they can be evicted at any GC and silently reconstructed
var connPool = sync.Pool{
	New: func() any { return dialExpensiveConnection() },
}

// good — Pool used for its intended purpose: cheap, short-lived scratch
// buffers that reduce allocator churn on a hot path
var bufPool = sync.Pool{
	New: func() any { return new(bytes.Buffer) },
}

func render(w io.Writer, data any) error {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer bufPool.Put(buf)

	if err := json.NewEncoder(buf).Encode(data); err != nil {
		return err
	}
	_, err := w.Write(buf.Bytes())
	return err
}
```

## 22.8 Prefer channels when transferring ownership of a value between goroutines; prefer a mutex when protecting shared state that many goroutines read and write in place.

> Why? These are different problems. Handing a value from a producer
> goroutine to a consumer goroutine, once, is ownership transfer — a
> channel expresses that transfer directly, and after the send, only one
> goroutine touches the value. Protecting a long-lived piece of shared
> state (a cache, a counter, a connection pool) that many goroutines read
> and mutate in place is what a mutex is for; forcing that through a
> channel-owning goroutine adds a serialization bottleneck and message-
> passing overhead the mutex avoids.

```go
// bad — routes every cache read/write through a single owner goroutine
// and a channel, adding latency and a bottleneck for no ownership benefit
type getReq struct {
	key   string
	reply chan string
}

func runCache(gets <-chan getReq, sets <-chan [2]string) {
	data := map[string]string{}
	for {
		select {
		case req := <-gets:
			req.reply <- data[req.key]
		case kv := <-sets:
			data[kv[0]] = kv[1]
		}
	}
}

// good — a mutex protects genuinely shared, long-lived state directly
type Cache struct {
	mu   sync.Mutex
	data map[string]string
}

func (c *Cache) Get(key string) string {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.data[key]
}

func (c *Cache) Set(key, value string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[key] = value
}
```

## 22.9 Remove a mutex field entirely once nothing in the type accesses it — don't leave it "just in case."

> Why? A `sync.Mutex` field that no method ever locks is dead weight: it
> misleads readers into thinking the type is concurrency-safe when it
> isn't, and adds a copy hazard (22.3) for no protective benefit. This
> project's `unused` linter flags genuinely dead fields, but an
> unlocked-everywhere mutex often isn't structurally "unused" in the
> compiler's sense — so review for this manually during refactors.

```go
// bad — mu is declared but never locked anywhere in the type; it
// suggests safety the type doesn't actually have
type Registry struct {
	mu    sync.Mutex
	items map[string]Item
}

func (r *Registry) Add(name string, it Item) {
	r.items[name] = it // mu is never used; this is not actually safe
}

// good — either use the mutex everywhere shared state is touched,
// or remove it and document that the type is not concurrency-safe
type Registry struct {
	mu    sync.Mutex
	items map[string]Item
}

func (r *Registry) Add(name string, it Item) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items[name] = it
}
```
