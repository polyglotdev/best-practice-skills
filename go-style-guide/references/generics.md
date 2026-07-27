# Generics — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

Generics (type parameters) shipped in Go 1.18 and the standard library gained `cmp`, `slices`, and `maps` in 1.21. The temptation with any new language feature is to reach for it everywhere; the rules here are about using generics where they remove real duplication — one written-once, well-tested container or algorithm instead of five near-identical copies — without turning every function into an abstract type-parameter puzzle that's harder to read than the duplication it replaced.

## Prefer the standard library's generic `slices`/`maps`/`cmp` packages over hand-rolled equivalents

**What Google/Effective Go says:** Not stated as a named rule in Google's prose guide (the `slices`/`maps` packages postdate most of the guide's generics-adjacent commentary); the general principle — don't hand-roll what the standard library already provides — is well-established Go practice reinforced by the packages' own documentation. ([`slices` package](https://pkg.go.dev/slices); [`maps` package](https://pkg.go.dev/maps); [`cmp` package](https://pkg.go.dev/cmp))

**How to detect it:** Grep for hand-written generic helper functions named `Contains`, `Map`, `Filter`, `Keys`, `Values`, `SortBy`, or similar, defined in application code rather than imported from `slices`/`maps`.

**Example violation:**
```go
func Contains[T comparable](s []T, v T) bool {
	for _, x := range s {
		if x == v {
			return true
		}
	}
	return false
}

func SortInts(s []int) {
	sort.Slice(s, func(i, j int) bool { return s[i] < s[j] })
}
```

**Corrected:**
```go
import (
	"slices"
)

// slices.Contains(s, v) and slices.Sort(s) replace both helpers above,
// are maintained by the Go team, and are used identically at every call site.
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a modernization opportunity flagged by convention, not tooling, in this config

**Why it matters:** A hand-rolled `Contains[T comparable]` is one more function this codebase has to maintain, document, and test, when `slices.Contains` already does the same job, is maintained by the Go team, and is instantly recognizable to any Go developer who has used the standard library.

## `cmp.Ordered` instead of a hand-rolled numeric-union constraint

**What Google/Effective Go says:** Not covered by Google's guide directly (predates `cmp`); documented in [`cmp` package](https://pkg.go.dev/cmp#Ordered), added in Go 1.21, as the standard replacement for the `constraints.Ordered`-style hand-rolled interfaces that were common in early Go-1.18-era generics code.

**How to detect it:** Grep for a locally defined constraint interface listing `~int | ~int8 | ~int16 | ... | ~float64 | ~string` or similar — this is almost always reinventing `cmp.Ordered`.

**Example violation:**
```go
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
```

**Corrected:**
```go
import "cmp"

func Max[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

// or, since Go 1.21, the builtin max() often removes the need for this
// function entirely — see tooling-and-modernization.md.
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** `cmp.Ordered` is the exact same constraint every hand-rolled version reimplements, kept up to date by the Go team as new numeric types are added to the language — defining it locally means this codebase's copy can silently drift from the standard one and adds a constraint definition every new contributor has to read before understanding the function that uses it.

## `comparable` for map keys and equality checks, not a hand-rolled `Equal` constraint

**What Google/Effective Go says:** Documented in the [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) — the built-in `comparable` constraint exists specifically to allow a type parameter to be used as a map key or compared with `==`/`!=`.

**How to detect it:** For any generic function that uses its type parameter as a map key or with `==`/`!=`, confirm the constraint includes (or is exactly) `comparable`.

**Example violation — constraint too loose for what the function body actually requires:**
```go
func Dedup[T any](s []T) []T { // any doesn't guarantee T is comparable
	seen := make(map[T]bool) // compile error: any does not support comparison
	var out []T
	for _, v := range s {
		if !seen[v] {
			seen[v] = true
			out = append(out, v)
		}
	}
	return out
}
```

**Corrected:**
```go
func Dedup[T comparable](s []T) []T {
	seen := make(map[T]bool, len(s))
	out := make([]T, 0, len(s))
	for _, v := range s {
		if !seen[v] {
			seen[v] = true
			out = append(out, v)
		}
	}
	return out
}
```

**Severity:** Violation

**Enforced by:** the Go compiler rejects this outright — `any` does not satisfy the implicit `comparable` requirement of a map key type parameter, so this is a compile error, not a silent bug; listed here because the audit should recognize the fix (tightening to `comparable`) rather than working around it with `reflect.DeepEqual`

**Why it matters:** Reaching for `reflect.DeepEqual` or a manual equality loop to work around an overly-loose `any` constraint is slower and more error-prone than simply using the correct, compiler-enforced `comparable` constraint that already expresses the function's real requirement.

## Reusable named constraints instead of repeating inline unions

**What Google/Effective Go says:** Documented in the [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) — define a named constraint interface once and reuse it across every function that needs the same type restriction, rather than repeating the union inline at each generic function's declaration.

**How to detect it:** Grep for the same inline type-union (e.g. `~int64 | ~float64`) repeated across more than one function's type-parameter list in the same package.

**Example violation:**
```go
func Sum[T ~int64 | ~float64](vals []T) T { /* ... */ }

func Average[T ~int64 | ~float64](vals []T) float64 { /* ... */ }
```

**Corrected:**
```go
type Number interface {
	~int64 | ~float64
}

func Sum[T Number](vals []T) T { /* ... */ }

func Average[T Number](vals []T) float64 { /* ... */ }
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** A named constraint documents its own intent (`Number` reads clearly at every call site) and gives a single place to extend the allowed type set later — repeating the same inline union at every function risks the unions drifting apart as only some of them get updated.

## Type arguments should usually be inferred, not written out explicitly

**What Google/Effective Go says:** Documented in the [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) — Go's type inference determines type arguments from the types of the regular arguments in most calls, so explicit instantiation (`Max[int](a, b)`) is usually unnecessary noise.

**How to detect it:** Grep for explicit type-argument instantiation (`FuncName[Type](`) at call sites where the argument types alone would let the compiler infer the same type.

**Example violation:**
```go
result := Max[int](3, 5) // [int] is redundant — inferrable from the arguments
```

**Corrected:**
```go
result := Max(3, 5)
```

**Legitimate — inference is impossible because the type parameter doesn't appear in any argument:**
```go
zero := Zero[int]() // no argument to infer int from — explicit instantiation required
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** An unnecessary explicit type argument adds visual noise without adding information the compiler couldn't already determine — reserving explicit instantiation for the cases where inference genuinely can't work makes those cases stand out as the ones that need it.

## Don't reach for generics when a type switch or `any` is simpler and sufficient

**What Google/Effective Go says:** Not stated as a named rule in Google's prose guide; a judgment call flowing from the same "clarity over cleverness" thread that runs through [function-design.md](function-design.md) — the [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) itself frames generics as a tool for a specific problem (writing functions and data structures that work across multiple concrete types with compile-time type safety), not a default choice.

**How to detect it:** For a generic function or type with only one or two call sites, each with a concrete, unrelated type, ask whether a simple type switch, an `any`-typed function with a runtime assertion, or just two separate concrete functions would be clearer than the generic version.

**Example violation — generic machinery for a problem that doesn't need it:**
```go
func Describe[T Stringer | int | string](v T) string {
	switch x := any(v).(type) {
	case Stringer:
		return x.String()
	case int:
		return strconv.Itoa(x)
	case string:
		return x
	default:
		return fmt.Sprintf("%v", x)
	}
}
```

**Corrected — a type switch over `any` says the same thing more directly, since the function immediately re-asserts the concrete type anyway:**
```go
func Describe(v any) string {
	switch x := v.(type) {
	case Stringer:
		return x.String()
	case int:
		return strconv.Itoa(x)
	case string:
		return x
	default:
		return fmt.Sprintf("%v", x)
	}
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a design judgment call

**Why it matters:** A generic type parameter is worth its complexity when it lets the compiler enforce a real type-safety guarantee across many call sites (a `Cache[K comparable, V any]`, a `slices.Contains[T comparable]`) — when the function immediately type-switches back to concrete cases anyway, the type parameter added compile-time ceremony without adding compile-time safety.

## Constrain generic containers with `comparable`/`any` deliberately, not defensively with `any` everywhere

**What Google/Effective Go says:** Documented implicitly throughout the [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) — choose the tightest constraint the implementation actually needs, since a looser constraint than necessary (defaulting everything to `any`) gives up compile-time guarantees for no benefit.

**How to detect it:** For each type parameter, check whether the function body's actual usage (comparisons, arithmetic, map keys) requires a tighter constraint than `any`, and whether the declared constraint matches.

**Example violation — constraint looser than the body's actual requirements:**
```go
type Set[T any] struct { // any is too loose: the body needs comparable
	items map[T]struct{}
}

func (s *Set[T]) Add(v T) {
	s.items[v] = struct{}{} // requires T to be a valid map key — needs comparable
}
```

**Corrected:**
```go
type Set[T comparable] struct {
	items map[T]struct{}
}

func (s *Set[T]) Add(v T) {
	s.items[v] = struct{}{}
}
```

**Severity:** Violation

**Enforced by:** the Go compiler rejects `any` as a map-key type parameter outright, making this a compile error rather than a silent issue; listed here so the audit recommends tightening the constraint (`comparable`) as the fix, rather than a workaround

**Why it matters:** The whole benefit of a type constraint is documenting, at the type's declaration, exactly what operations it supports — a `Set[T any]` reads as "works with anything" even though the implementation secretly requires comparability, misleading anyone deciding whether to instantiate it with a non-comparable type like a slice or a map.

## Generic function and type names follow the same naming rules as everything else

**What Google/Effective Go says:** No special exemption — the naming conventions in [naming.md](naming.md) apply identically to generic functions, types, and their type parameters; the [go.dev generics tutorial](https://go.dev/doc/tutorial/generics) itself uses the conventional single-letter names (`T`, `K`, `V`) throughout its own examples.

**How to detect it:** Check type-parameter names for single-letter, conventional choices (`T`, `K`, `V`, `E`) unless a longer name meaningfully improves clarity for a non-obvious constraint; check that the generic function/type itself still follows exported/unexported and MixedCaps conventions.

**Example violation — type parameter named to look like a regular variable, generic type not exported per convention:**
```go
type cache[dataType comparable, valueType any] struct { // unexported "cache" hides an API meant to be exported; dataType/valueType stray from convention with no added clarity
	mu   sync.Mutex
	data map[dataType]valueType
}
```

**Corrected:**
```go
// Cache is a generic, exported type. K and V are the conventional
// short names for "key type" and "value type."
type Cache[K comparable, V any] struct {
	mu   sync.Mutex
	data map[K]V
}
```

**Severity:** Suggestion

**Enforced by:** revive/var-naming (part of `enable-all`-adjacent `revive` config) applies its general naming checks to type parameters as it does to any other identifier; the single-letter-convention judgment itself is not linter-enforced

**Why it matters:** `K`/`V`/`T`/`E` for key/value/type/element are conventions every Go developer already recognizes from the standard library's own generic types (`map[K]V` conceptually, `slices.Index[S ~[]E, E comparable]`) — using them consistently means a reader doesn't have to relearn a new naming scheme for every generic type in the codebase.

## How to audit Go code against these rules

1. Grep for hand-written `Contains`, `Map`, `Filter`, `Keys`, `Values`, sort-related helpers — check whether `slices`/`maps`/`cmp` already provides the same function.
2. Grep for locally defined `~int | ~int8 | ... | ~float64 | ~string`-style constraint interfaces — check whether `cmp.Ordered` already covers the same set.
3. For any generic function using its type parameter as a map key or with `==`/`!=`, confirm the constraint is or includes `comparable` (the compiler will reject a mismatch, but the audit should recommend tightening the constraint as the fix).
4. Grep for the same inline type-union repeated across more than one function in a package — suggest extracting a named, reusable constraint.
5. Grep for explicit type-argument instantiation (`Func[Type](`) — check whether the compiler could have inferred the same type from the arguments.
6. For low-call-count generic functions/types, ask whether a type switch over `any` or a couple of concrete functions would be clearer.
7. For every type parameter, compare the declared constraint against what the function body actually requires — flag constraints looser than the implementation needs.
8. Check type-parameter naming (`T`/`K`/`V`/`E` conventions) and confirm the generic type/function itself still follows standard exported/unexported naming.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
