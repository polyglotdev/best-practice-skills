<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 7. Slices, Maps, Arrays

Slices and maps are reference-like types built on top of pointers, which
makes their copy and zero-value semantics easy to get subtly wrong. This
chapter draws from Uber's guidance on [Copy Slices and Maps at
Boundaries](https://github.com/uber-go/guide/blob/master/style.md#copy-slices-and-maps-at-boundaries),
[nil is a valid
slice](https://github.com/uber-go/guide/blob/master/style.md#nil-is-a-valid-slice),
[Initializing
Maps](https://github.com/uber-go/guide/blob/master/style.md#initializing-maps),
and [Prefer Specifying Container
Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity),
plus [Effective Go:
Data](https://go.dev/doc/effective_go#slices) (arrays, slices,
two-dimensional slices, maps). Declaration mechanics for `var` vs. literal
initialization are covered in [Chapter 5](05-declarations.md).

## 7.1 Copy slices and maps at package or API boundaries instead of sharing the caller's backing array.

> Why? Slices and maps are reference types: storing a caller's slice or
> map directly, or returning your internal one, lets either side mutate
> shared state without the other knowing. Copying at the boundary makes
> ownership unambiguous
> ([Uber Style: Copy Slices and Maps at
> Boundaries](https://github.com/uber-go/guide/blob/master/style.md#copy-slices-and-maps-at-boundaries)).

```go
// bad — caller's slice becomes shared, mutable state inside Cache
type Cache struct {
	items []string
}

func NewCache(items []string) *Cache {
	return &Cache{items: items} // aliases the caller's backing array
}

// good — copy on the way in
func NewCache(items []string) *Cache {
	owned := make([]string, len(items))
	copy(owned, items)
	return &Cache{items: owned}
}
```

## 7.2 Copy slices and maps on the way out of an API, too — don't return internal state directly.

> Why? Returning your internal slice or map lets any caller mutate your
> type's private state through the returned reference, bypassing every
> invariant your methods enforce
> ([Uber Style: Copy Slices and Maps at
> Boundaries](https://github.com/uber-go/guide/blob/master/style.md#copy-slices-and-maps-at-boundaries)).

```go
// bad — caller can mutate c.items directly through the returned slice
func (c *Cache) Items() []string {
	return c.items
}

// good — return a copy
func (c *Cache) Items() []string {
	out := make([]string, len(c.items))
	copy(out, c.items)
	return out
}
```

## 7.3 Treat `nil` as a valid, usable slice — don't force an empty literal to avoid it.

> Why? Unlike a `nil` map, a `nil` slice supports `len()`, `range`, and
> `append()` without panicking. `var s []string` is the idiomatic,
> allocation-free way to represent "no elements yet"
> ([Uber Style: nil is a valid
> slice](https://github.com/uber-go/guide/blob/master/style.md#nil-is-a-valid-slice)).

```go
// bad — forces an allocation to avoid nil, with no behavioral benefit
func FilterActive(users []User) []string {
	names := []string{}
	for _, u := range users {
		if u.Active {
			names = append(names, u.Name)
		}
	}
	return names
}

// good — nil slice works identically for len/range/append
func FilterActive(users []User) []string {
	var names []string
	for _, u := range users {
		if u.Active {
			names = append(names, u.Name)
		}
	}
	return names
}
```

## 7.4 Return an explicitly empty (non-nil) slice only when the API contract requires distinguishing "empty" from "absent" — e.g. JSON encoding.

> Why? `encoding/json` marshals a `nil` slice as `null` and an empty,
> non-nil slice as `[]`. If your API's JSON contract promises an array,
> initialize with `make([]T, 0)` or a literal so callers never see
> `null` where they expect `[]`
> ([Uber Style: nil is a valid
> slice](https://github.com/uber-go/guide/blob/master/style.md#nil-is-a-valid-slice)).

```go
// bad — no results marshals to `"tags":null`, breaking a client expecting an array
type Response struct {
	Tags []string `json:"tags"`
}

func BuildResponse(tags []string) Response {
	var r Response
	r.Tags = tags // may be nil
	return r
}

// good — guarantee `"tags":[]` when there are no tags
func BuildResponse(tags []string) Response {
	r := Response{Tags: make([]string, 0, len(tags))}
	r.Tags = append(r.Tags, tags...)
	return r
}
```

## 7.5 Initialize maps you intend to write to with `make` or a literal, never leave them at their `nil` zero value.

> Why? A `nil` map (its zero value) panics on write, unlike a `nil`
> slice. If the map will be populated, initialize it explicitly
> ([Uber Style: Initializing
> Maps](https://github.com/uber-go/guide/blob/master/style.md#initializing-maps)).

```go
// bad
var counts map[string]int
counts["widgets"]++ // panics: assignment to entry in nil map

// good
counts := make(map[string]int)
counts["widgets"]++
```

## 7.6 Specify container capacity up front when the final size is known or estimable — using modern APIs where available.

> Why? Appending to a slice or writing to a map without a capacity hint
> forces the runtime to repeatedly reallocate and copy as the container
> grows. A capacity hint lets it allocate once
> ([Uber Style: Prefer Specifying Container
> Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity)).
> Go 1.21+ adds `slices.Grow`, which is often clearer than a manual
> `make(..., 0, n)` when growing an existing slice rather than
> allocating a fresh one.

```go
// bad — legacy idiom pre-1.21: works, but was the only option for growing
// an existing slice before slices.Grow existed
func Expand(base []int, extra int) []int {
	grown := make([]int, len(base), len(base)+extra)
	copy(grown, base)
	return grown
}

// good — allocate with capacity up front when building fresh
func CollectIDs(users []User) []string {
	ids := make([]string, 0, len(users))
	for _, u := range users {
		ids = append(ids, u.ID)
	}
	return ids
}

// good — slices.Grow when extending an existing slice (Go 1.21+)
func Expand(base []int, extra int) []int {
	return slices.Grow(base, extra)
}
```

## 7.7 Give maps a capacity hint with `make(map[K]V, n)` when the entry count is known ahead of time.

> Why? Like slices, maps benefit from a size hint: Go's runtime can
> size the underlying hash table's buckets once instead of growing and
> rehashing repeatedly as entries are added
> ([Uber Style: Prefer Specifying Container
> Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity)).

```go
// bad — no hint; map grows and rehashes repeatedly for a known-size input
func IndexByID(users []User) map[string]User {
	index := make(map[string]User)
	for _, u := range users {
		index[u.ID] = u
	}
	return index
}

// good
func IndexByID(users []User) map[string]User {
	index := make(map[string]User, len(users))
	for _, u := range users {
		index[u.ID] = u
	}
	return index
}
```

## 7.8 Never rely on map iteration order; sort explicitly if order matters.

> Why? Go deliberately randomizes map iteration order between runs to
> prevent code from accidentally depending on an implementation detail.
> Code that appears to work in testing can produce different output in
> production ([Effective Go: Data](https://go.dev/doc/effective_go#maps)).

```go
// bad — assumes iteration order matches insertion order
func FormatTags(tags map[string]string) string {
	var b strings.Builder
	for k, v := range tags {
		fmt.Fprintf(&b, "%s=%s;", k, v)
	}
	return b.String()
}

// good — explicit sort makes output deterministic
func FormatTags(tags map[string]string) string {
	keys := make([]string, 0, len(tags))
	for k := range tags {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var b strings.Builder
	for _, k := range keys {
		fmt.Fprintf(&b, "%s=%s;", k, tags[k])
	}
	return b.String()
}
```

## 7.9 Remember arrays are values — assigning or passing one copies every element.

> Why? Unlike slices, a Go array's type includes its length, and array
> values are copied on assignment, function call, and channel send.
> Passing a large array by value where a slice was intended silently
> duplicates the whole thing on every call
> ([Effective Go: Data](https://go.dev/doc/effective_go#arrays)).

```go
// bad — [1000]int copied on every call; mutations don't propagate to the caller
func ZeroOut(data [1000]int) {
	for i := range data {
		data[i] = 0
	}
}

// good — slice shares the backing array; use a slice unless a fixed-size
// value type is specifically what you want
func ZeroOut(data []int) {
	for i := range data {
		data[i] = 0
	}
}
```

## 7.10 Use `slices` and `maps` standard-library helpers instead of hand-rolled loops for common operations.

> Why? Go 1.21+ ships `slices.Contains`, `slices.Sort`, `slices.Equal`,
> `maps.Keys`, `maps.Clone`, and similar helpers in the standard
> library. Hand-rolled equivalents are more code to review and more
> places to introduce an off-by-one bug for behavior the standard
> library already provides and tests.

```go
// bad — legacy idiom pre-1.21: hand-rolled contains check
func hasTag(tags []string, target string) bool {
	for _, t := range tags {
		if t == target {
			return true
		}
	}
	return false
}

// good — slices.Contains (Go 1.21+)
func hasTag(tags []string, target string) bool {
	return slices.Contains(tags, target)
}
```

## 7.11 Prefer `clear(m)` / `clear(s)` over manual delete loops or reallocation when emptying a container.

> Why? Go 1.21 added the `clear` built-in, which empties a map in place
> or zeroes every element of a slice without the overhead of allocating
> a brand-new container or looping over keys by hand.

```go
// bad — legacy idiom pre-1.21: delete loop to empty a map
func Reset(counts map[string]int) {
	for k := range counts {
		delete(counts, k)
	}
}

// good — clear (Go 1.21+)
func Reset(counts map[string]int) {
	clear(counts)
}
```

## 7.12 Use two-dimensional slices (`[][]T`), not fixed 2D arrays, when row lengths can vary or sizes aren't known at compile time.

> Why? A Go 2D array (`[3][4]int`) has a fixed shape baked into its
> type, which is rarely what's needed for real-world data like a
> jagged matrix or a dynamically sized grid. A slice of slices allows
> each row to be allocated and sized independently
> ([Effective Go: Data](https://go.dev/doc/effective_go#two_dimensional_slices)).

```go
// bad — fixed shape, can't represent a jagged structure or runtime-determined size
var grid [3][4]int

// good — each row allocated to its own length
grid := make([][]int, rows)
for i := range grid {
	grid[i] = make([]int, cols)
}
```
