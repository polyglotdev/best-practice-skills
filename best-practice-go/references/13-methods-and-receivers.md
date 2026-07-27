<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 13. Methods & Receivers

A method's receiver is a small piece of syntax with outsized consequences:
it decides whether a call mutates the caller's data, whether the type
satisfies interfaces built around pointers, and how consistent a type feels
across its whole method set. This chapter draws from [Effective Go:
Methods](https://go.dev/doc/effective_go#methods) and [Effective Go:
Interfaces](https://go.dev/doc/effective_go#interfaces_and_types) for the
pointer-vs-value rules, and from [Uber Style: Receivers and
Interfaces](https://github.com/uber-go/guide/blob/master/style.md#receivers-and-interfaces)
and [Uber Style: Pointers to
Interfaces](https://github.com/uber-go/guide/blob/master/style.md#pointers-to-interfaces)
for the addressability pitfalls. Interface design itself is covered in
[Chapter 14](14-interfaces.md); this chapter is about the receiver
declaration, not the interface it may satisfy.

## 13.1 Use a pointer receiver whenever the method mutates the receiver.

> Why? [Effective Go: Methods](https://go.dev/doc/effective_go#pointers_vs_values)
> explains that "pointer methods can modify the receiver; invoking them on
> a value would cause the method to receive a copy of the value, so any
> modifications would be discarded." A value receiver silently makes
> mutation impossible instead of failing loudly.

```go
// bad — mutates a copy; caller's Counter never changes
type Counter struct {
	n int
}

func (c Counter) Increment() {
	c.n++
}

// good
func (c *Counter) Increment() {
	c.n++
}
```

## 13.2 Use a pointer receiver for large structs to avoid copying on every call.

> Why? A value receiver copies the entire struct into the method's stack
> frame on every call. [Effective Go:
> Methods](https://go.dev/doc/effective_go#pointers_vs_values) notes this
> cost directly; for large or growing structs, a pointer receiver avoids
> paying it repeatedly, and avoids a performance cliff when a field is
> later added.

```go
// bad — every call copies the whole struct
type Report struct {
	Rows    [1000]Row
	Headers []string
	Footer  string
}

func (r Report) RowCount() int {
	return len(r.Rows)
}

// good
func (r *Report) RowCount() int {
	return len(r.Rows)
}
```

## 13.3 Use a pointer receiver on any type containing a `sync.Mutex`, `sync.WaitGroup`, or similar synchronization primitive.

> Why? Copying a struct that embeds or contains a `sync.Mutex` copies its
> internal state, producing a second, independent lock that no longer
> protects the same data — a classic data race. A pointer receiver ensures
> every method call operates on the same underlying value. See [Chapter
> 22](22-sync-primitives.md) for the full "don't copy sync types" rule;
> `go vet`'s `copylocks` check (enabled by
> [`govet enable-all`](https://pkg.go.dev/cmd/vet)) will fail the build on
> a value receiver over such a type. **Enforced by: `govet`
> (`copylocks`).**

```go
// bad — value receiver copies the mutex on every call
type Cache struct {
	mu   sync.Mutex
	data map[string]string
}

func (c Cache) Get(key string) string {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.data[key]
}

// good
func (c *Cache) Get(key string) string {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.data[key]
}
```

## 13.4 Pick one receiver type per type and use it for every method — never mix pointer and value receivers on the same type.

> Why? [Uber Style: Receivers and
> Interfaces](https://github.com/uber-go/guide/blob/master/style.md#receivers-and-interfaces)
> shows that value-stored instances (e.g. in a `map[int]S`) are not
> addressable, so pointer-receiver methods become uncallable on them while
> value-receiver methods on the same type still work. Mixing receiver
> kinds on one type means the type's method set depends on how a value
> happens to be stored, which is a surprising and inconsistent API.

```go
// bad — Read has a value receiver, Write has a pointer receiver
type S struct {
	data string
}

func (s S) Read() string {
	return s.data
}

func (s *S) Write(v string) {
	s.data = v
}

// sVals := map[int]S{1: {"A"}}
// sVals[1].Read()          // fine
// sVals[1].Write("test")   // compile error: not addressable

// good — every method uses a pointer receiver
type S struct {
	data string
}

func (s *S) Read() string {
	return s.data
}

func (s *S) Write(v string) {
	s.data = v
}
```

## 13.5 Once any method on a type needs a pointer receiver, make the constructor return a pointer too.

> Why? If callers hold a value (`S{}`) instead of `*S`, calling a
> pointer-receiver method may still compile when the value is addressable,
> but storage in maps, interfaces, or `range` variables often is not
> addressable. Returning `*S` from the constructor keeps the type's usage
> pattern consistent with its method set.

```go
// bad — constructor returns a value, but methods need a pointer
func NewCache() Cache {
	return Cache{data: make(map[string]string)}
}

// good
func NewCache() *Cache {
	return &Cache{data: make(map[string]string)}
}
```

## 13.6 Name the receiver with a short abbreviation of the type — one or two characters — not `this`, `self`, or the full type name.

> Why? Go convention treats the receiver as a lightweight reference to the
> method's subject, not an object-oriented `this`. [Effective
> Go](https://go.dev/doc/effective_go#methods) and the standard library
> consistently use one- or two-letter receivers (`b *Buffer`, `f *File`)
> so the receiver reads as a natural abbreviation rather than competing
> with the method's real parameters for attention.

```go
// bad
func (this *Buffer) Write(p []byte) (int, error) { return 0, nil }
func (self *Buffer) Read(p []byte) (int, error)  { return 0, nil }
func (buffer *Buffer) Reset()                    {}

// good
func (b *Buffer) Write(p []byte) (int, error) { return 0, nil }
func (b *Buffer) Read(p []byte) (int, error)  { return 0, nil }
func (b *Buffer) Reset()                      {}
```

## 13.7 Use the exact same receiver name on every method of a type.

> Why? A receiver name that changes from method to method (`b` in one
> function, `buf` in the next) forces readers to re-learn the type's local
> alias every time they jump to a new method, with no benefit. `revive`'s
> `receiver-naming` rule enforces a single, consistent name per type.
> **Enforced by: `revive/receiver-naming`.**

```go
// bad — same type, three different receiver names
func (b *Buffer) Write(p []byte) (int, error) { return 0, nil }
func (buf *Buffer) Read(p []byte) (int, error) { return 0, nil }
func (x *Buffer) Reset()                       {}

// good — one name, consistent everywhere
func (b *Buffer) Write(p []byte) (int, error) { return 0, nil }
func (b *Buffer) Read(p []byte) (int, error)  { return 0, nil }
func (b *Buffer) Reset()                      {}
```

## 13.8 Don't use a pointer to an interface — pass the interface by value.

> Why? [Uber Style: Pointers to
> Interfaces](https://github.com/uber-go/guide/blob/master/style.md#pointers-to-interfaces)
> explains that an interface value is already a two-word pair (type
> pointer, data pointer). If the underlying data needs mutation, the
> concrete type stored in the interface should itself be a pointer — a
> `*MyInterface` parameter almost never does what its author intended.

```go
// bad — pointer to an interface adds a layer of indirection nobody needs
func Configure(w *io.Writer) {
	(*w).Write([]byte("configured\n"))
}

// good — pass the interface value; mutation happens through the
// concrete pointer type already stored inside it
func Configure(w io.Writer) {
	w.Write([]byte("configured\n"))
}
```

## 13.9 Remember that a value receiver's method is promoted to pointers automatically, but not the reverse.

> Why? [Effective Go: Methods](https://go.dev/doc/effective_go#pointers_vs_values)
> states the rule precisely: "value methods can be invoked on pointers and
> values, but pointer methods can only be invoked on pointers." Relying on
> a value receiver because "it works when called on `&x` too" is fine —
> but designing a pointer-receiver method and expecting it to work on a
> non-addressable value (a map element, an interface holding a value, a
> function's return value) will fail to compile.

```go
// bad — assumes a pointer method works on a returned value
type Point struct{ X, Y int }

func (p *Point) Scale(f int) {
	p.X *= f
	p.Y *= f
}

func origin() Point { return Point{} }

// origin().Scale(2) // compile error: origin() is not addressable

// good — call through an addressable variable, or use a value receiver
// if the method never needs to mutate
p := origin()
p.Scale(2) // fine: p is an addressable local variable
```

## 13.10 Don't define methods on types you don't own just to change their behavior — wrap them instead.

> Why? Go only allows methods on named types declared in the same package
> ([Effective Go: Methods](https://go.dev/doc/effective_go#methods)
> implicitly assumes locally declared types). Trying to work around this
> with package-level state or global hooks breaks encapsulation and makes
> behavior depend on import order.

```go
// bad — can't add a method to time.Duration from another package to
// change its String output, so mutable global state is used instead
var globalDurationFormat = "default"

// good — define a local named type and put the method on that
type FriendlyDuration time.Duration

func (d FriendlyDuration) String() string {
	return time.Duration(d).Round(time.Second).String()
}
```

## 13.11 Prefer a method over a free function when the operation's meaning depends on a specific type's state.

> Why? [Effective Go:
> Methods](https://go.dev/doc/effective_go#pointers_vs_values) shows this
> with `(p *ByteSlice) Append`, converting an awkward free function that
> had to return the updated slice into a method that mutates through a
> pointer receiver. A method call also groups discoverably with the type
> in documentation and editor autocomplete, whereas an unrelated free
> function does not.

```go
// bad — free function; caller must remember to reassign the result
func AppendByte(slice ByteSlice, data []byte) ByteSlice {
	return append(slice, data...)
}

func useBad(s ByteSlice) ByteSlice {
	return AppendByte(s, []byte("more"))
}

// good — method reads naturally and groups with the type
func (s *ByteSlice) Append(data []byte) {
	*s = append(*s, data...)
}

func useGood(s *ByteSlice) {
	s.Append([]byte("more"))
}
```
