<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 6. Types

Struct literals are one of the most repeated constructs in any Go
codebase, so small conventions here compound across a whole project. This
chapter draws from Uber's guidance on [Initializing
Structs](https://github.com/uber-go/guide/blob/master/style.md#use-field-names-to-initialize-structs)
(Use Field Names, Omit Zero Value Fields, Use var for Zero Value Structs,
Initializing Struct References), [Google Best Practices: Zero
values](https://google.github.io/styleguide/go/best-practices#zero-values),
and [Effective Go:
Data](https://go.dev/doc/effective_go#composite_literals) and
[Constructors and composite
literals](https://go.dev/doc/effective_go#composite_literals). Zero-value
declaration mechanics (`var` vs. `:=`) are covered in [Chapter
5](05-declarations.md); this chapter focuses on the shape of the struct
literal itself.

## 6.1 Use field names in struct literals with three or more fields, or any exported struct.

> Why? Positional struct literals break silently when a field is added,
> removed, or reordered — the values shift into the wrong fields without
> a compile error if the types happen to align. Field names make the
> literal robust to struct changes and self-documenting at the call
> site ([Uber Style: Use Field Names to Initialize
> Structs](https://github.com/uber-go/guide/blob/master/style.md#use-field-names-to-initialize-structs)).

```go
// bad — positional; breaks silently if Config's field order changes
cfg := Config{"localhost", 8080, true, 30}

// good
cfg := Config{
	Host:      "localhost",
	Port:      8080,
	TLS:       true,
	TimeoutMS: 30,
}
```

## 6.2 Omit zero-value fields from struct literals.

> Why? Explicitly writing `Retries: 0` or `Debug: false` implies the
> value is meaningful, when it's actually just the type's default.
> Omitting zero-value fields keeps literals focused on the values that
> actually differ from the default
> ([Uber Style: Omit Zero Value
> Fields](https://github.com/uber-go/guide/blob/master/style.md#omit-zero-value-fields-in-structs)).

```go
// bad
cfg := Config{
	Host:    "localhost",
	Port:    8080,
	Retries: 0,
	Debug:   false,
}

// good
cfg := Config{
	Host: "localhost",
	Port: 8080,
}
```

## 6.3 Declare a zero-value struct with `var`, not an empty `T{}` literal.

> Why? This is the struct-specific case of the rule in [Chapter
> 5](05-declarations.md#57-use-var-ssomestruct-for-a-zero-value-struct-instead-of-s--somestruct): if every
> field should start at its zero value, `var s SomeStruct` says that
> directly instead of writing an empty composite literal that implies
> fields might be set
> ([Uber Style: Use var for Zero Value
> Structs](https://github.com/uber-go/guide/blob/master/style.md#use-var-for-zero-value-structs)).

```go
// bad
opts := Options{}

// good
var opts Options
```

## 6.4 Initialize struct references (pointers to structs) with `&T{...}`.

> Why? `&T{Field: value}` constructs and takes the address of the
> struct in a single expression, which is shorter and less error-prone
> than allocating with `new(T)` and assigning fields afterward
> ([Uber Style: Initializing Struct
> References](https://github.com/uber-go/guide/blob/master/style.md#initializing-struct-references)).

```go
// bad
u := new(User)
u.Name = "Ana"
u.Active = true

// good
u := &User{
	Name:   "Ana",
	Active: true,
}
```

## 6.5 Prefer value types (`T{}`) over pointer types (`&T{}`) unless the type needs pointer semantics.

> Why? A value type is simpler to reason about — no nil checks, no
> shared mutable state, no heap allocation pressure. Reach for a pointer
> only when you need mutation to be visible to callers, the type is
> large enough that copying is expensive, or the type contains fields
> (like a `sync.Mutex`) that must not be copied
> ([Effective Go: Data](https://go.dev/doc/effective_go#composite_literals)).

```go
// bad — pointer used with no need for shared mutation or size concerns
type Point struct{ X, Y int }

func Translate(p *Point, dx, dy int) *Point {
	return &Point{X: p.X + dx, Y: p.Y + dy}
}

// good — small, immutable-in-effect value type passed and returned by value
type Point struct{ X, Y int }

func Translate(p Point, dx, dy int) Point {
	return Point{X: p.X + dx, Y: p.Y + dy}
}
```

## 6.6 Embed types only when you intend to promote their entire method set as part of your API.

> Why? Embedding isn't inheritance — it promotes the embedded type's
> methods onto the outer type's exported API, permanently. If you only
> need to reuse an implementation internally, hold it as a named field
> instead of embedding it, so your type's API surface stays under your
> control ([Effective Go: Embedding](https://go.dev/doc/effective_go#embedding)).

```go
// bad — embeds *log.Logger, silently exposing every *log.Logger method
// (SetOutput, SetFlags, ...) as part of Service's public API
type Service struct {
	*log.Logger
	name string
}

// good — held as a named field; Service controls exactly what it exposes
type Service struct {
	logger *log.Logger
	name   string
}

func (s *Service) Infof(format string, args ...any) {
	s.logger.Printf(format, args...)
}
```

## 6.7 Use `type Marker struct{}` as an empty, comparable marker or signal type.

> Why? An empty struct occupies zero bytes and is the idiomatic Go way
> to represent "presence" without a meaningful value — the classic
> example is `map[string]struct{}` for a set. Using `bool` instead
> wastes a byte per entry and implies a meaningful false/true state that
> doesn't exist for pure membership checks
> ([Effective Go: Data](https://go.dev/doc/effective_go#composite_literals)).

```go
// bad — bool implies a meaningful "false" state that isn't real
seen := make(map[string]bool)
seen["alice"] = true
if seen["bob"] {
	// ...
}

// good — struct{} communicates "presence only," zero extra memory
seen := make(map[string]struct{})
seen["alice"] = struct{}{}
if _, ok := seen["bob"]; ok {
	// ...
}
```

## 6.8 Give constructor functions (`NewT`) a clear job: validate and assemble, don't just wrap a literal.

> Why? If `NewT()` does nothing but return `&T{}`, it adds an
> indirection with no benefit — callers should just use the literal. A
> constructor earns its place when it validates arguments, computes
> derived fields, or enforces invariants a literal can't
> ([Effective Go: Constructors and composite
> literals](https://go.dev/doc/effective_go#composite_literals)).

```go
// bad — NewClient adds nothing over a literal
func NewClient(host string) *Client {
	return &Client{host: host}
}

// good — NewClient enforces an invariant the literal can't
func NewClient(host string) (*Client, error) {
	if host == "" {
		return nil, errors.New("client: host must not be empty")
	}
	return &Client{host: host, timeout: 30 * time.Second}, nil
}
```

## 6.9 Keep struct field order grouped by logical relationship, not forced into a specific memory-layout order.

> Why? Field ordering primarily affects readability — group
> configuration fields together, group derived/internal fields together
> — rather than reordering fields purely to save a few bytes of padding.
> Byte-level field alignment is a micro-optimization that most teams
> deliberately don't enforce as a style rule, since it trades away
> readability for a marginal, rarely-measured memory win
> ([Effective Go: Data](https://go.dev/doc/effective_go#composite_literals)).

```go
// bad — fields ordered arbitrarily, unrelated concerns interleaved
type Server struct {
	Timeout    time.Duration
	logger     *log.Logger
	Port       int
	mu         sync.Mutex
	Host       string
	conns      int
}

// good — grouped: public config, then internal state
type Server struct {
	Host    string
	Port    int
	Timeout time.Duration

	mu     sync.Mutex
	conns  int
	logger *log.Logger
}
```

## 6.10 Define behavior-based interfaces at the point of use, sized to what the caller actually needs.

> Why? A small, consumer-defined interface (one or two methods) is easy
> to satisfy with a real implementation or a test double. A large
> interface that mirrors an entire concrete type's method set forces
> every implementer — including tests — to implement methods they don't
> use ([Effective Go: Interfaces](https://go.dev/doc/effective_go#interfaces)).

```go
// bad — huge interface forces every implementation to satisfy all of it
type Store interface {
	Get(id string) (Item, error)
	Put(id string, item Item) error
	Delete(id string) error
	List() ([]Item, error)
	Backup(w io.Writer) error
	Restore(r io.Reader) error
}

// good — the function only needs one capability; the interface reflects that
type ItemGetter interface {
	Get(id string) (Item, error)
}

func Render(g ItemGetter, id string) (string, error) {
	item, err := g.Get(id)
	if err != nil {
		return "", err
	}
	return item.Name, nil
}
```

## 6.11 Verify interface satisfaction at compile time with a blank assignment, not at runtime.

> Why? Without an explicit check, a type that's supposed to implement an
> interface can silently drift out of compliance (a method gets renamed
> or its signature changes) and the failure only shows up later at the
> call site that assigns it to the interface — often with a confusing
> error. A blank `var _ Interface = (*Impl)(nil)` fails at compile time,
> right next to the type definition
> ([Uber Style: Verify Interface
> Compliance](https://github.com/uber-go/guide/blob/master/style.md#verify-interface-compliance)).

```go
// bad — no compile-time check; a signature drift is only caught wherever Impl is used as Interface
type Notifier interface {
	Notify(ctx context.Context, msg string) error
}

type EmailNotifier struct{}

func (e *EmailNotifier) Notify(msg string) error { return nil } // wrong signature, compiles fine here

// good — the mismatch fails to compile right where EmailNotifier is defined
type Notifier interface {
	Notify(ctx context.Context, msg string) error
}

type EmailNotifier struct{}

var _ Notifier = (*EmailNotifier)(nil)

func (e *EmailNotifier) Notify(ctx context.Context, msg string) error { return nil }
```
