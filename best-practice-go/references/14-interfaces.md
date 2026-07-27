<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 14. Interfaces

Interfaces are Go's substitute for inheritance-based polymorphism: a set of
method signatures that any type can satisfy implicitly. This chapter draws
from [Effective Go: Interfaces and other
types](https://go.dev/doc/effective_go#interfaces_and_types) and [Effective
Go: The blank identifier — interface
satisfaction](https://go.dev/doc/effective_go#blank_implements) for the
core language mechanics, and from [Uber Style: Verify Interface
Compliance](https://github.com/uber-go/guide/blob/master/style.md#verify-interface-compliance)
for the compile-time check idiom. Receiver mechanics that determine whether
a type satisfies an interface are covered in [Chapter
13](13-methods-and-receivers.md); embedding interfaces to compose behavior
is covered further in [Chapter 15](15-embedding.md). Type-asserting an
*error* specifically is governed by `errors.As`, covered in [Chapter
16](16-errors.md) — this chapter's compliance-check idiom is for
non-error interface satisfaction only.

## 14.1 Accept interfaces as parameters; return concrete types from constructors.

> Why? A function that accepts an interface can be called with any
> satisfying type, maximizing caller flexibility. A function that returns
> an interface hides the concrete type from callers who might need its
> full method set, and makes it harder to add methods later without
> breaking the interface's contract. This is the classic Go idiom implicit
> throughout [Effective Go: Interfaces and other
> types](https://go.dev/doc/effective_go#interfaces_and_types).

```go
// bad — constructor returns an interface, hiding the concrete type
func NewLogger() Logger {
	return &fileLogger{}
}

// good — constructor returns the concrete type; callers narrow if needed
func NewFileLogger() *FileLogger {
	return &FileLogger{}
}

func Process(w io.Writer, l *FileLogger) {
	// accepts an interface where flexibility helps
}
```

## 14.2 Keep interfaces small — one to three methods is the ideal size.

> Why? [Effective Go: Interfaces and other
> types](https://go.dev/doc/effective_go#interfaces_and_types) observes
> that "interfaces with only one or two methods are common in Go code."
> `io.Reader` and `io.Writer` are the model: each specifies exactly one
> behavior, so any type — a file, a buffer, a network connection — can
> satisfy it without adopting unrelated obligations.

```go
// bad — a bloated interface few types can fully, meaningfully implement
type Store interface {
	Get(key string) ([]byte, error)
	Set(key string, value []byte) error
	Delete(key string) error
	List() ([]string, error)
	Backup(w io.Writer) error
	Restore(r io.Reader) error
}

// good — small interfaces that compose (see Chapter 15 on embedding)
type Getter interface {
	Get(key string) ([]byte, error)
}

type Setter interface {
	Set(key string, value []byte) error
}
```

## 14.3 Define interfaces at the point of consumption, not next to the implementation.

> Why? A consumer package should declare the narrow interface it actually
> needs and accept any type that satisfies it; the producer package should
> export a concrete type. This keeps producer packages free to add methods
> without breaking consumers, and lets each consumer describe only the
> behavior it depends on — [Effective Go: Interfaces and other
> types](https://go.dev/doc/effective_go#interfaces_and_types) demonstrates
> this with `io.Reader`/`io.Writer`, which are declared in `io`, the
> consumer-facing package, not alongside every type that implements them.

```go
// bad — producer package pre-declares an interface for consumers to use,
// coupling every future consumer to this one shape
package storage

type Store interface {
	Get(key string) ([]byte, error)
	Set(key string, value []byte) error
}

type FileStore struct{ /* ... */ }

// good — producer exports only the concrete type
package storage

type FileStore struct{ /* ... */ }

func (f *FileStore) Get(key string) ([]byte, error) { return nil, nil }
func (f *FileStore) Set(key string, value []byte) error { return nil }

// consumer package declares the narrow interface it needs
package cache

type getter interface {
	Get(key string) ([]byte, error)
}

func Warm(g getter, keys []string) {
	// ...
}
```

## 14.4 Don't design interfaces before you have at least one real consumer with a concrete need.

> Why? An interface extracted "for testability" or "in case we swap
> implementations" before any second implementation or consumer exists
> tends to mirror its sole implementation's method set exactly, adding
> indirection without flexibility. Wait until a second concrete type or a
> test double actually needs to stand in, then extract the minimal
> interface the consumer requires (see 14.3).

```go
// bad — a one-implementation interface added "just in case"
type UserRepository interface {
	FindByID(id string) (*User, error)
	Save(u *User) error
	Delete(id string) error
	Count() (int, error)
	FindByEmail(email string) (*User, error)
}

type sqlUserRepository struct{ db *sql.DB }

// good — start with the concrete type; extract an interface once a
// second implementation or a test double actually needs one
type SQLUserRepository struct{ db *sql.DB }

func (r *SQLUserRepository) FindByID(id string) (*User, error) { return nil, nil }
```

## 14.5 Verify interface compliance at compile time when a type is required to implement an interface.

> Why? [Uber Style: Verify Interface
> Compliance](https://github.com/uber-go/guide/blob/master/style.md#verify-interface-compliance)
> and [Effective Go: The blank identifier — interface
> satisfaction](https://go.dev/doc/effective_go#blank_implements) both
> recommend `var _ Interface = (*Impl)(nil)` so that a missing or
> incorrectly-signed method fails the build immediately, at the
> declaration site, instead of surfacing later as a runtime type-assertion
> failure somewhere else. The user's linter config does not enforce this
> check, so treat it as a **Suggestion**, not a required rule — apply it
> for exported types with an explicit interface contract, collections of
> types sharing an interface, or anywhere breaking the interface would
> break callers.

```go
// bad — no compile-time check; a signature drift is only caught when
// something tries to use *Handler as http.Handler and fails
type Handler struct{}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {}

// good — suggestion: fails to compile immediately if the method set drifts
type Handler struct{}

var _ http.Handler = (*Handler)(nil)

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {}
```

## 14.6 Use `nil` (or the zero value) on the right-hand side of a compliance check, not a constructed value.

> Why? [Uber Style: Verify Interface
> Compliance](https://github.com/uber-go/guide/blob/master/style.md#verify-interface-compliance)
> specifies the right-hand side should be the zero value of the asserted
> type — `nil` for pointers, slices, and maps, an empty struct literal for
> struct types — because the check exists purely for the compiler; no
> runtime value is needed or should be paid for.

```go
// bad — allocates a real value just to satisfy a compile-time check
var _ io.Writer = NewBuffer()

// good
var _ io.Writer = (*Buffer)(nil)

// good — struct types use an empty literal
var _ fmt.Stringer = Point{}
```

## 14.7 Embed interfaces to compose larger contracts instead of re-listing methods.

> Why? [Effective Go:
> Embedding](https://go.dev/doc/effective_go#embedding) shows `io.ReadWriter`
> built by embedding `Reader` and `Writer` rather than re-declaring `Read`
> and `Write`. This keeps the composed interface's definition in sync with
> its parts automatically and documents the relationship between the small
> interfaces and the combined one. See [Chapter 15](15-embedding.md) for
> embedding in structs.

```go
// bad — re-declares methods that already exist on Reader and Writer
type ReadWriter interface {
	Read(p []byte) (n int, err error)
	Write(p []byte) (n int, err error)
}

// good — composes existing interfaces
type ReadWriter interface {
	Reader
	Writer
}
```

## 14.8 Use `any` instead of `interface{}` in new code (Go 1.18+).

> Why? `any` is an alias for `interface{}` introduced for generics support.
> It communicates "this holds a value of any type" more directly than the
> empty-interface literal, and it's the form the standard library and
> `gofmt`-adjacent tooling now favor going forward, per the Go 1.18 release
> and the modernization posture in this guide.

```go
// bad
func Dump(v interface{}) {
	fmt.Printf("%#v\n", v)
}

// good
func Dump(v any) {
	fmt.Printf("%#v\n", v)
}
```

## 14.9 Use a type switch, not a chain of type assertions, when branching on more than one possible concrete type.

> Why? [Effective Go: Interfaces and other
> types](https://go.dev/doc/effective_go#interfaces_and_types) presents
> the type switch as the idiomatic way to convert an interface value into
> one of several possible concrete types. A chain of individual `,ok`
> assertions repeats the same interface value and produces less readable
> branching than a single switch.

```go
// bad
if str, ok := value.(string); ok {
	return str
}
if s, ok := value.(fmt.Stringer); ok {
	return s.String()
}
return ""

// good
switch v := value.(type) {
case string:
	return v
case fmt.Stringer:
	return v.String()
default:
	return ""
}
```

## 14.10 Use the blank identifier when you only need to know whether a type satisfies an interface, not the asserted value itself.

> Why? [Effective Go: The blank identifier — interface
> satisfaction](https://go.dev/doc/effective_go#blank_implements) shows
> `if _, ok := val.(json.Marshaler); ok` for exactly this case: the check
> matters, the extracted value doesn't. Binding an unused variable instead
> just adds a name nobody reads.

```go
// bad — v is bound but never used
if v, ok := val.(json.Marshaler); ok {
	fmt.Printf("value implements json.Marshaler\n")
	_ = v
}

// good
if _, ok := val.(json.Marshaler); ok {
	fmt.Printf("value implements json.Marshaler\n")
}
```

## 14.11 Never use a bare type assertion (`x.(T)`) on a value that might not hold `T` — and never use it to inspect an error's concrete type.

> Why? A single-return type assertion panics if the interface doesn't hold
> the asserted type. For general interface values, always use the
> comma-ok form (see [Chapter 17](17-error-handling.md) for the full
> type-assertion-failure discussion). For errors specifically, use
> `errors.As` instead of any form of direct type assertion — the user's
> `errorlint` linter setting `asserts: true` fails the build on
> `err.(*MyError)` even in comma-ok form, because it bypasses wrapped-error
> unwrapping. See [Chapter 16, §16.9](16-errors.md) for the full
> `errors.As` rule. **Enforced by: `errorlint` (`asserts: true`).**

```go
// bad — panics if val does not hold a string; and for errors, a direct
// assertion misses wrapped causes entirely
name := val.(string)

var pathErr *fs.PathError
if pe, ok := err.(*fs.PathError); ok {
	pathErr = pe
}

// good — comma-ok for general interfaces; errors.As for errors
name, ok := val.(string)
if !ok {
	return fmt.Errorf("value is %T, not string", val)
}

var pathErr *fs.PathError
if errors.As(err, &pathErr) {
	// handle pathErr
}
```
