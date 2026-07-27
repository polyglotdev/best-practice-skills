<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 24. Generics (Go 1.18+)

Generics postdate the Google Go Style Guide, so this chapter models its
guidance on the Go team's own [type parameters
proposal](https://go.dev/blog/intro-generics) and [tutorial: getting
started with
generics](https://go.dev/doc/tutorial/generics), together with the Go
1.21+ [`slices`](https://pkg.go.dev/slices), [`maps`](https://pkg.go.dev/maps),
and [`cmp`](https://pkg.go.dev/cmp) standard-library packages that generics
made possible. It cross-references [Effective Go:
Interfaces](https://go.dev/doc/effective_go#interfaces), since constraint
interfaces are ordinary interfaces used in a new position. The governing
principle carried over from the rest of this guide: reach for the simplest
tool that solves the problem. Generics remove duplicated container and
algorithm code; they are not a general substitute for interfaces or a way
to look more sophisticated.

## 24.1 Reach for generics when writing container types or algorithms that operate identically over many element types.

> Why? Before generics, a type-safe stack, set, or `Map`/`Filter` helper
> required either code generation or falling back to `interface{}` with
> runtime type assertions. The [Go blog's generics
> introduction](https://go.dev/blog/intro-generics) describes exactly this
> class of problem — container types and element-agnostic algorithms — as
> the motivating use case.

```go
// bad — duplicated stack implementation per element type
type IntStack struct{ items []int }

func (s *IntStack) Push(v int) { s.items = append(s.items, v) }
func (s *IntStack) Pop() int {
	n := len(s.items) - 1
	v := s.items[n]
	s.items = s.items[:n]
	return v
}

// good — one implementation, safe for any element type
type Stack[T any] struct{ items []T }

func (s *Stack[T]) Push(v T) { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() T {
	n := len(s.items) - 1
	v := s.items[n]
	s.items = s.items[:n]
	return v
}
```

## 24.2 Keep concrete types when a function only ever operates on one type in practice.

> Why? A type parameter is only worth its added signature complexity when
> callers actually instantiate it with more than one type. The [Go
> tutorial on generics](https://go.dev/doc/tutorial/generics) introduces
> type parameters specifically to replace *duplicated* functions — not to
> pre-generalize code that has a single caller.

```go
// bad — generic for a function that only ever handles Order
func Total[T Order](items []T) float64 {
	var sum float64
	for _, it := range items {
		sum += it.Price()
	}
	return sum
}

// good — concrete type; simpler signature, same behavior today
func Total(items []Order) float64 {
	var sum float64
	for _, it := range items {
		sum += it.Price()
	}
	return sum
}
```

## 24.3 Use `[T any]` when the function body never needs to compare, order, or operate arithmetically on values of `T`.

> Why? `any` (an alias for `interface{}`) is the correct constraint when a
> type parameter is only stored, passed through, or compared with `==`
> implicitly by the caller's own logic. Over-constraining with a narrower
> interface than the function needs limits which types callers can use for
> no benefit, per the [Go generics
> tutorial](https://go.dev/doc/tutorial/generics#getting_started).

```go
// bad — needlessly constrains T to Ordered when the body never compares
func First[T cmp.Ordered](items []T) (T, bool) {
	var zero T
	if len(items) == 0 {
		return zero, false
	}
	return items[0], true
}

// good — any is sufficient; nothing in the body requires ordering
func First[T any](items []T) (T, bool) {
	var zero T
	if len(items) == 0 {
		return zero, false
	}
	return items[0], true
}
```

## 24.4 Use `[T comparable]` when the function needs `==`/`!=` or uses `T` as a map key.

> Why? `comparable` is a predeclared constraint satisfied by any type
> valid as a map key. Using `any` for a type parameter that is later used
> as a map key fails to compile with a clear error, so the constraint
> should say up front what the function requires, as shown in the [Go
> generics tutorial](https://go.dev/doc/tutorial/generics#getting_started).

```go
// bad — any does not compile: map key type must be comparable
func Dedupe[T any](items []T) []T {
	seen := make(map[T]bool)
	var out []T
	for _, it := range items {
		if !seen[it] {
			seen[it] = true
			out = append(out, it)
		}
	}
	return out
}

// good — comparable states the real requirement and compiles
func Dedupe[T comparable](items []T) []T {
	seen := make(map[T]bool)
	var out []T
	for _, it := range items {
		if !seen[it] {
			seen[it] = true
			out = append(out, it)
		}
	}
	return out
}
```

## 24.5 Let the compiler infer type arguments from function arguments; only write them out explicitly when inference fails.

> Why? Explicit type arguments on every call site add noise the compiler
> already resolves from the arguments passed in. The [Go generics
> tutorial](https://go.dev/doc/tutorial/generics#getting_started) writes
> calls without explicit type arguments precisely because inference
> handles the common case.

```go
// bad — explicit type argument is redundant; the argument type is unambiguous
total := Sum[int]([]int{1, 2, 3})

// good — the compiler infers T from the argument
total := Sum([]int{1, 2, 3})
```

## 24.6 Define a named constraint interface once a constraint is reused across more than one function or method set.

> Why? Repeating an inline constraint like `interface{ ~int | ~int64 }` on
> every function signature is harder to read and easy to drift out of
> sync. The [Go generics tutorial's constraint
> section](https://go.dev/doc/tutorial/generics#getting_started) defines a
> reusable constraint type for exactly this reason.

```go
// bad — same inline union constraint repeated on every function
func SumInts[T interface{ ~int | ~int32 | ~int64 }](vs []T) T {
	var s T
	for _, v := range vs {
		s += v
	}
	return s
}

func MaxInts[T interface{ ~int | ~int32 | ~int64 }](vs []T) T {
	m := vs[0]
	for _, v := range vs[1:] {
		if v > m {
			m = v
		}
	}
	return m
}

// good — one named constraint, reused
type Integer interface {
	~int | ~int32 | ~int64
}

func SumInts[T Integer](vs []T) T {
	var s T
	for _, v := range vs {
		s += v
	}
	return s
}

func MaxInts[T Integer](vs []T) T {
	m := vs[0]
	for _, v := range vs[1:] {
		if v > m {
			m = v
		}
	}
	return m
}
```

## 24.7 Avoid `interface{}`/`any` parameters with runtime type switches when a type parameter would let the compiler check callers.

> Why? A function that takes `any` and type-switches inside pushes type
> errors to runtime panics or silent no-ops. A type parameter moves the
> same check to compile time. This is the core motivation in the [Go
> blog's generics introduction](https://go.dev/blog/intro-generics) for
> adding type parameters to the language at all.

```go
// bad — runtime type switch, easy to add a case and forget another
func Double(v any) any {
	switch x := v.(type) {
	case int:
		return x * 2
	case float64:
		return x * 2
	default:
		panic("unsupported type")
	}
}

// good — compiler enforces that T supports multiplication by a constant
type Number interface {
	~int | ~float64
}

func Double[T Number](v T) T {
	return v * 2
}
```

## 24.8 Use `cmp.Ordered` instead of hand-rolling an ordering constraint for numeric and string types.

> Why? `cmp.Ordered` in the standard [`cmp`](https://pkg.go.dev/cmp)
> package already unions every built-in ordered type. Redefining it
> locally duplicates a well-tested standard constraint and can drift as
> new built-in types are added.

```go
// bad — a hand-rolled constraint duplicates cmp.Ordered
type Ordered interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
		~float32 | ~float64 | ~string
}

func Max[T Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

// good — cmp.Ordered from the standard library
func Max[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}
```

## 24.9 Prefer the standard library's `slices` and `maps` generic helpers over hand-written loops.

> Why? [`slices.Sort`](https://pkg.go.dev/slices#Sort),
> [`slices.Contains`](https://pkg.go.dev/slices#Contains), and
> [`maps.Keys`](https://pkg.go.dev/maps#Keys) are generic, well-tested,
> and communicate intent in one call instead of a hand-written loop the
> reader has to verify line by line.

```go
// bad — manual loop reimplements slices.Contains
func hasUser(users []string, name string) bool {
	for _, u := range users {
		if u == name {
			return true
		}
	}
	return false
}

// good — slices.Contains says exactly what the code does
func hasUser(users []string, name string) bool {
	return slices.Contains(users, name)
}
```

## 24.10 Use `slices.Sort`/`slices.SortFunc` instead of `sort.Slice` for new code.

> Why? `sort.Slice` takes an untyped `interface{}` and a closure with
> manual index bookkeeping, and it isn't type-checked against the element
> type. `slices.Sort` and `slices.SortFunc` in the
> [`slices`](https://pkg.go.dev/slices) package are generic, avoid
> reflection, and read closer to the intent.

```go
// bad — sort.Slice uses reflection and untyped indices
sort.Slice(users, func(i, j int) bool {
	return users[i].Name < users[j].Name
})

// good — slices.SortFunc is generic and reflection-free
slices.SortFunc(users, func(a, b User) int {
	return cmp.Compare(a.Name, b.Name)
})
```

## 24.11 Use `maps.Keys`/`maps.Values` from the standard `maps` package instead of manual accumulation loops.

> Why? Extracting keys or values from a map is common enough that the
> standard [`maps`](https://pkg.go.dev/maps) package now provides
> iterator-based helpers; a hand-written loop is more code to read for the
> same result.

```go
// bad — manual accumulation loop
func userNames(byID map[int]User) []string {
	names := make([]string, 0, len(byID))
	for _, u := range byID {
		names = append(names, u.Name)
	}
	return names
}

// good — maps.Values plus slices.Collect
func userNames(byID map[int]User) []string {
	users := slices.Collect(maps.Values(byID))
	names := make([]string, len(users))
	for i, u := range users {
		names[i] = u.Name
	}
	return names
}
```

## 24.12 Do not add a type parameter "for future flexibility" when only one concrete type is ever instantiated.

> Why? Speculative generics add cognitive overhead — constraint reasoning,
> inference edge cases, an extra symbol in every signature — for a
> flexibility nobody uses. The [Go generics
> tutorial](https://go.dev/doc/tutorial/generics) introduces type
> parameters to eliminate *existing* duplication, not to pre-empt
> hypothetical future callers.

```go
// bad — parameterized "just in case", but Config is the only real user
type Registry[T any] struct {
	items map[string]T
}

func NewConfigRegistry() *Registry[Config] {
	return &Registry[Config]{items: make(map[string]Config)}
}

// good — concrete type until a second real caller appears
type ConfigRegistry struct {
	items map[string]Config
}

func NewConfigRegistry() *ConfigRegistry {
	return &ConfigRegistry{items: make(map[string]Config)}
}
```

## 24.13 Accept narrow, well-known interfaces as ordinary (non-generic) parameters even in generic code; don't generify what Effective Go already solves with interfaces.

> Why? [Effective Go:
> Interfaces](https://go.dev/doc/effective_go#interfaces) already solves
> "accept behavior, not concrete types" with plain interfaces like
> `io.Reader`. Wrapping such a parameter in a type parameter adds no
> capability — the function still only calls the interface's methods —
> and just adds a type parameter the reader must resolve.

```go
// bad — R is constrained to io.Reader but never used generically
func CountBytes[R io.Reader](r R) (int64, error) {
	return io.Copy(io.Discard, r)
}

// good — a plain io.Reader parameter is simpler and equally capable
func CountBytes(r io.Reader) (int64, error) {
	return io.Copy(io.Discard, r)
}
```
