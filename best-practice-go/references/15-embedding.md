<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 15. Embedding

Embedding lets a struct or interface "borrow" another type's method set
without hand-written delegation. Used well, it's composition with almost no
boilerplate; used carelessly, it leaks implementation details into a public
API forever. This chapter draws from [Effective Go:
Embedding](https://go.dev/doc/effective_go#embedding) for the mechanics and
from [Uber Style: Avoid Embedding Types in Public
Structs](https://github.com/uber-go/guide/blob/master/style.md#avoid-embedding-types-in-public-structs)
and [Uber Style: Embedding in
Structs](https://github.com/uber-go/guide/blob/master/style.md#embedding-in-structs)
for when to say no. Embedding interfaces to compose contracts is also
touched on in [Chapter 14, §14.7](14-interfaces.md); this chapter covers
embedding concrete types in structs and the public-API risk that comes with
it.

## 15.1 Embed a type when you're building a new concrete type out of an existing behavior, and the composition itself is the point.

> Why? [Effective Go:
> Embedding](https://go.dev/doc/effective_go#embedding) shows `bufio.ReadWriter`
> embedding `*bufio.Reader` and `*bufio.Writer` to assemble a combined
> type "by combining a reader and a writer into one struct using
> embedding," picking up both method sets and both interface
> satisfactions for free. This is the idiomatic case: the embedding is the
> feature, not an implementation shortcut.

```go
// bad — hand-written forwarding methods for behavior composition
type ReadWriter struct {
	r *Reader
	w *Writer
}

func (rw *ReadWriter) Read(p []byte) (int, error)  { return rw.r.Read(p) }
func (rw *ReadWriter) Write(p []byte) (int, error) { return rw.w.Write(p) }

// good — embedding gives Read and Write for free
type ReadWriter struct {
	*Reader
	*Writer
}
```

## 15.2 Embed a concrete type to gain a useful zero value, like `*bytes.Buffer` inside a type that needs buffering.

> Why? Types with genuinely useful zero values — `bytes.Buffer` is the
> canonical example — are safe and idiomatic to embed because the outer
> type inherits that same "ready to use without initialization" property.
> [Uber Style: Embedding in
> Structs](https://github.com/uber-go/guide/blob/master/style.md#embedding-in-structs)
> calls out `type Book struct { bytes.Buffer }` as a good example for
> exactly this reason.

```go
// bad — reimplements buffering that bytes.Buffer already provides
type Log struct {
	data []byte
}

func (l *Log) Write(p []byte) (int, error) {
	l.data = append(l.data, p...)
	return len(p), nil
}

// good — embeds a type with a useful zero value
type Log struct {
	bytes.Buffer
}

var l Log
l.WriteString("started\n") // works immediately, no constructor needed
```

## 15.3 Never embed a type in a struct that is part of your package's public API.

> Why? [Uber Style: Avoid Embedding Types in Public
> Structs](https://github.com/uber-go/guide/blob/master/style.md#avoid-embedding-types-in-public-structs)
> warns that "these embedded types leak implementation details, inhibit
> type evolution, and obscure documentation." Every exported method and
> field of the embedded type becomes part of your struct's public contract
> whether you intended it or not, and removing or replacing the embed
> later is a breaking change.

```go
// bad — ConcreteList's public API now silently includes every exported
// method AbstractList ever has or will have
type ConcreteList struct {
	*AbstractList
}

// good — hand-write only the delegate methods you intend to support
type ConcreteList struct {
	list *AbstractList
}

func (l *ConcreteList) Add(e Entity) { l.list.Add(e) }

func (l *ConcreteList) Remove(e Entity) { l.list.Remove(e) }
```

## 15.4 Prefer explicit delegate methods over embedding when the embedded type's full method set isn't meant to be part of the contract.

> Why? [Uber Style: Avoid Embedding Types in Public
> Structs](https://github.com/uber-go/guide/blob/master/style.md#avoid-embedding-types-in-public-structs)
> applies a litmus test: "would all of these exported inner
> methods/fields be added directly to the outer type? If the answer is
> 'some' or 'no,' don't embed the inner type — use a field instead." The
> tedium of writing forwarding methods is the price of keeping your API
> surface intentional.

```go
// bad — Client exposes all of http.Client's methods, including ones
// that were never meant to be part of Client's contract
type Client struct {
	http.Client
	baseURL string
}

// good — Client exposes exactly the methods it chooses to
type Client struct {
	httpClient *http.Client
	baseURL    string
}

func (c *Client) Get(path string) (*http.Response, error) {
	return c.httpClient.Get(c.baseURL + path)
}
```

## 15.5 Never embed a mutex, even in an unexported struct.

> Why? [Uber Style: Embedding in
> Structs](https://github.com/uber-go/guide/blob/master/style.md#embedding-in-structs)
> singles this out as an explicit exception: embedding `sync.Mutex`
> promotes `Lock`/`Unlock` onto the outer type, which "become available,
> provide no functional benefit, and allow users to control details about
> the internals" of the type. See [Chapter 22](22-sync-primitives.md) for
> the full mutex-as-field rule.

```go
// bad — Lock/Unlock leak onto SMap's method set
type SMap struct {
	sync.Mutex
	data map[string]string
}

// good — mutex is a named field, not embedded
type SMap struct {
	mu   sync.Mutex
	data map[string]string
}

func (m *SMap) Get(k string) string {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.data[k]
}
```

## 15.6 Place embedded fields at the top of the struct, separated from named fields by a blank line.

> Why? [Uber Style: Embedding in
> Structs](https://github.com/uber-go/guide/blob/master/style.md#embedding-in-structs)
> requires this layout so a reader can immediately distinguish "behavior
> this type inherits" from "state this type owns," without cross-checking
> each field against the type's method set.

```go
// bad — embedded field buried among named fields
type Client struct {
	version int
	http.Client
	timeout time.Duration
}

// good
type Client struct {
	http.Client

	version int
	timeout time.Duration
}
```

## 15.7 Use keyed fields in composite literals for any struct that embeds a type, so `govet`'s composite-literal check stays clean.

> Why? An embedded field's key is the type's own name, and unkeyed
> composite literals list fields positionally — a struct with an embedded
> field mixed among named fields is easy to initialize with values in the
> wrong slot after a refactor. `govet`'s composite-literal checks
> (included under `enable-all`) flag unkeyed struct literals for exactly
> this reason. **Enforced by: `govet` (composite literal checks).**

```go
// bad — unkeyed literal; adding or reordering fields silently
// misassigns values
c := Client{http.Client{}, 3, 5 * time.Second}

// good — keyed literal makes every field assignment explicit and
// resistant to reordering
c := Client{
	Client:  http.Client{},
	version: 3,
	timeout: 5 * time.Second,
}
```

## 15.8 Resolve name collisions between an embedded type and the outer type explicitly, don't rely on shadowing rules readers must memorize.

> Why? [Effective Go:
> Embedding](https://go.dev/doc/effective_go#embedding) explains that "a
> field or method X hides any other item X in a more deeply nested part of
> the type," and that a same-level collision is an error unless the
> duplicate name is never referenced outside the type definition. Relying
> on this precedence rather than naming things to avoid the collision in
> the first place makes the type's behavior depend on rules most readers
> won't recall correctly.

```go
// bad — Job.Command silently hides any Command that *log.Logger might
// gain in a future version; fragile if log.Logger changes
type Job struct {
	Command string
	*log.Logger
}

// good — rename the outer field so there is no ambiguity to reason about
type Job struct {
	Cmd string
	*log.Logger
}
```

## 15.9 Use an embedded interface to provide a partial implementation that panics or no-ops on unimplemented methods, and document why.

> Why? Embedding an interface (rather than a concrete type) inside a
> struct lets that struct satisfy the interface immediately, with each
> concrete method overriding only the behavior it cares about; calls to
> any method the struct doesn't override panic with a nil-pointer
> dereference at the embedded interface. This pattern appears in the
> standard library (for example, forward-compatible gRPC server stubs) and
> must always be documented, since an unimplemented call fails at runtime,
> not compile time.

```go
// bad — implements every method of a large interface just to override one,
// with no signal to future maintainers about which methods are "real"
type loggingStore struct {
	realStore Store
}

func (s *loggingStore) Get(k string) ([]byte, error)          { return s.realStore.Get(k) }
func (s *loggingStore) Set(k string, v []byte) error          { return s.realStore.Set(k, v) }
func (s *loggingStore) Delete(k string) error                 { return s.realStore.Delete(k) }

// good — embeds the interface; only the method under test is overridden,
// and the doc comment makes the partial-implementation risk explicit
// UnimplementedStore embeds Store so callers can override only the
// methods they need. Calling any other method panics.
type UnimplementedStore struct {
	Store
}

type loggingGet struct {
	UnimplementedStore
	realStore Store
}

func (s *loggingGet) Get(k string) ([]byte, error) {
	return s.realStore.Get(k)
}
```
