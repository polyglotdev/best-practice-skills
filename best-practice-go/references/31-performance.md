<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 31. Performance

Go's performance idioms are mostly about avoiding unnecessary allocation
and unnecessary work the compiler and runtime cannot optimize away for
you. This chapter draws primarily from Uber's [Prefer Specifying Container
Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity),
[Avoid Strings to Byte Slice
Conversions](https://github.com/uber-go/guide/blob/master/style.md#avoid-string-to-byte-conversion),
and [Prefer strconv over
fmt](https://github.com/uber-go/guide/blob/master/style.md#prefer-strconv-over-fmt)
sections, with performance implications from [Effective
Go](https://go.dev/doc/effective_go) noted throughout. The user's
`gocritic` configuration enables the `performance` tag but disables
`rangeValCopy` and `hugeParam` (see [Chapter
33.10](33-linter-configuration.md)) — this chapter marks the
by-pointer-for-large-structs guidance as a Suggestion, not a Violation,
to match that configuration. As with any performance work, measure before
optimizing; the last rule in this chapter covers benchmarking discipline.

## 31.1 Preallocate slices with `make([]T, 0, n)` (or `slices.Grow`) when the final size is known or estimable ahead of time.

> Why? Appending to a nil or zero-capacity slice forces repeated
> reallocation and copying as it grows. [Uber Style: Prefer Specifying
> Container
> Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity)
> recommends preallocating to the known or estimated final size so
> `append` never has to grow the backing array.

```go
// bad — repeated reallocation as the slice grows one element at a time
func toNames(users []User) []string {
	var names []string
	for _, u := range users {
		names = append(names, u.Name)
	}
	return names
}

// good — capacity is known up front; append never reallocates
func toNames(users []User) []string {
	names := make([]string, 0, len(users))
	for _, u := range users {
		names = append(names, u.Name)
	}
	return names
}
```

## 31.2 Use `slices.Grow` when adding a known number of elements to an existing, possibly non-empty slice.

> Why? `slices.Grow(s, n)` (Go 1.21+) ensures capacity for at least `n`
> more elements without the caller re-deriving the correct `make` size
> and copying manually. It supersedes the older idiom of pre-1.21 manual
> capacity math for the "extend an existing slice" case, per the
> [`slices`](https://pkg.go.dev/slices#Grow) package documentation.

```go
// bad — was idiomatic pre-1.21: manual capacity math to extend a slice
func appendAll(dst []int, src []int) []int {
	if cap(dst)-len(dst) < len(src) {
		grown := make([]int, len(dst), len(dst)+len(src))
		copy(grown, dst)
		dst = grown
	}
	return append(dst, src...)
}

// good — slices.Grow expresses the same intent directly
func appendAll(dst []int, src []int) []int {
	dst = slices.Grow(dst, len(src))
	return append(dst, src...)
}
```

## 31.3 Preallocate maps with `make(map[K]V, n)` when the approximate final size is known.

> Why? Like slices, maps that grow past their initial bucket allocation
> incur rehashing. [Uber Style: Prefer Specifying Container
> Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity)
> extends the same preallocation guidance to maps constructed from a
> known-size input.

```go
// bad — map starts with no size hint and rehashes as it grows
func indexByID(users []User) map[string]User {
	byID := make(map[string]User)
	for _, u := range users {
		byID[u.ID] = u
	}
	return byID
}

// good — size hint avoids rehashing during population
func indexByID(users []User) map[string]User {
	byID := make(map[string]User, len(users))
	for _, u := range users {
		byID[u.ID] = u
	}
	return byID
}
```

## 31.4 Build strings with `strings.Builder`, not repeated `+`/`+=` concatenation, in any loop.

> Why? Each `+=` on a string allocates a brand-new string and copies both
> operands into it, making an N-iteration concatenation loop O(N²).
> [Google Best Practices: String
> concatenation](https://google.github.io/styleguide/go/best-practices#string-concatenation)
> and [Uber's performance
> guidance](https://github.com/uber-go/guide/blob/master/style.md#performance)
> both point to `strings.Builder`, which grows its internal buffer
> instead of reallocating a full copy on every append.

```go
// bad — O(n²) allocation from repeated string concatenation
func joinLines(lines []string) string {
	var out string
	for _, l := range lines {
		out += l + "\n"
	}
	return out
}

// good — strings.Builder amortizes allocation across the whole loop
func joinLines(lines []string) string {
	var b strings.Builder
	for _, l := range lines {
		b.WriteString(l)
		b.WriteByte('\n')
	}
	return b.String()
}
```

## 31.5 Avoid repeated `[]byte(s)` / `string(b)` conversions of the same value inside a loop or hot path.

> Why? Converting a `string` to `[]byte` or back allocates a new copy of
> the underlying data every time, because strings are immutable and
> `[]byte` is not — the runtime cannot safely share the backing array.
> [Uber Style: Avoid Strings to Byte Slice
> Conversions](https://github.com/uber-go/guide/blob/master/style.md#avoid-string-to-byte-conversion)
> recommends converting once and reusing the result rather than
> reconverting on every use.

```go
// bad — converts the same string to []byte on every loop iteration
func containsAny(s string, targets []string) bool {
	for _, t := range targets {
		if bytes.Contains([]byte(s), []byte(t)) {
			return true
		}
	}
	return false
}

// good — convert once, outside the loop
func containsAny(s string, targets []string) bool {
	for _, t := range targets {
		if strings.Contains(s, t) {
			return true
		}
	}
	return false
}
```

## 31.6 Use `strconv` functions (`Itoa`, `FormatInt`, `ParseFloat`) instead of `fmt.Sprintf`/`fmt.Sscanf` for simple type-to-string conversions.

> Why? [Uber Style: Prefer strconv over
> fmt](https://github.com/uber-go/guide/blob/master/style.md#prefer-strconv-over-fmt)
> notes that `fmt.Sprintf` parses a format string and uses reflection to
> dispatch on argument types at runtime, which is measurably slower than
> `strconv`'s direct, type-specific conversion functions for simple
> cases.

```go
// bad — fmt.Sprintf pays a format-parsing and reflection cost
id := fmt.Sprintf("%d", userID)

// good — strconv.Itoa converts directly with no format parsing
id := strconv.Itoa(userID)
```

## 31.7 Use `sync.Pool` to reuse short-lived, frequently allocated objects on hot paths — not as a general-purpose object cache.

> Why? `sync.Pool` reduces garbage collector pressure by letting hot-path
> code reuse buffers instead of allocating and discarding one per
> operation. It is not a correctness mechanism — the runtime may clear a
> `Pool` between GC cycles — so it must only be used to *avoid*
> allocation, never to hold state that must survive.

```go
// bad — a fresh buffer is allocated on every call, on a hot request path
func encode(v any) ([]byte, error) {
	buf := new(bytes.Buffer)
	if err := json.NewEncoder(buf).Encode(v); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// good — sync.Pool reuses buffers across calls, reducing GC pressure
var bufPool = sync.Pool{
	New: func() any { return new(bytes.Buffer) },
}

func encode(v any) ([]byte, error) {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer bufPool.Put(buf)

	if err := json.NewEncoder(buf).Encode(v); err != nil {
		return nil, err
	}
	out := make([]byte, buf.Len())
	copy(out, buf.Bytes())
	return out, nil
}
```

## 31.8 Consider passing large structs by pointer to avoid copy costs, but treat this as a Suggestion, not a Violation, given the project's `gocritic` configuration.

> Why? Passing a large struct by value copies every field on every call.
> In general this is worth avoiding on hot paths. However, the project's
> `.golangci.yml` disables `gocritic`'s `hugeParam` and `rangeValCopy`
> checks (see [Chapter 33.10](33-linter-configuration.md)) — meaning
> large-struct-by-value is a deliberate non-issue for this codebase's
> linting baseline. Do not litigate by-value vs. by-pointer struct
> passing in code review as if it were a hard rule; raise it only when a
> profile shows it actually matters.

```go
// bad — a profiled hot path that is measurably slower due to the copy;
// worth fixing once data shows it, even though gocritic won't flag it
func Summarize(s OrderSnapshot) string {
	return fmt.Sprintf("order %s: %d items", s.ID, len(s.Items))
}

// good — pointer avoids the copy; suggested once a profile shows it matters
func Summarize(s *OrderSnapshot) string {
	return fmt.Sprintf("order %s: %d items", s.ID, len(s.Items))
}

// acceptable under this project's linter config either way — hugeParam
// and rangeValCopy are disabled, so gocritic will not flag OrderSnapshot
// passed by value even though it is a large struct
type OrderSnapshot struct {
	ID       string
	Items    [50]LineItem
	Metadata map[string]string
}
```

## 31.9 Reuse a single `[]byte` or string-building buffer across iterations of a hot loop instead of allocating a new one per iteration.

> Why? Allocating inside a tight loop multiplies allocation count by
> iteration count. Hoisting the buffer out of the loop and resetting it
> each iteration turns N allocations into roughly one, which is the same
> principle behind `sync.Pool` in rule 31.7 applied within a single
> function.

```go
// bad — a new buffer is allocated on every iteration
func renderAll(records []Record) [][]byte {
	var out [][]byte
	for _, r := range records {
		buf := new(bytes.Buffer)
		render(buf, r)
		out = append(out, buf.Bytes())
	}
	return out
}

// good — one buffer, reset and reused across iterations
func renderAll(records []Record) [][]byte {
	out := make([][]byte, 0, len(records))
	var buf bytes.Buffer
	for _, r := range records {
		buf.Reset()
		render(&buf, r)
		rendered := make([]byte, buf.Len())
		copy(rendered, buf.Bytes())
		out = append(out, rendered)
	}
	return out
}
```

## 31.10 Never optimize based on intuition alone; write a `go test -bench` benchmark first and confirm the change with `-benchmem`.

> Why? Go's allocator, escape analysis, and inliner routinely make
> "obvious" optimizations meaningless or even counterproductive.
> [Effective Go](https://go.dev/doc/effective_go) and the wider Go
> community's performance guidance treat benchmarking as mandatory before
> and after a performance change — without it, you cannot tell whether
> the change helped, did nothing, or made things worse.

```go
// bad — "optimizing" without measuring anything before or after
func Sum(nums []int) int {
	// rewritten to be "faster" based on a hunch, never benchmarked
	total := 0
	for i := 0; i < len(nums); i++ {
		total += nums[i]
	}
	return total
}

// good — a benchmark quantifies the change; -benchmem shows allocations
func BenchmarkSum(b *testing.B) {
	nums := make([]int, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Sum(nums)
	}
}

// run as: go test -bench=. -benchmem
// interpret ns/op for speed and B/op, allocs/op for allocation pressure
func Sum(nums []int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	return total
}
```
