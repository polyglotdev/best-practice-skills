# Variable Declarations — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

Go gives you several ways to declare a variable; the style guide is opinionated about which to use when. The throughline: choose the form that conveys intent — initialising with a value? Use `:=`. Declaring something the zero value will fill later? Use `var`. Preallocating because you have a known size? Use `make` with a capacity hint.

## Use `:=` when initialising with a non-zero value, inside functions

**What Google/Effective Go says:** "The `:=` form... should be used... when declaring and initializing" inside function bodies; `var x = 42` says the same thing in two words instead of one. ([Style Decisions: Variable declarations](https://google.github.io/styleguide/go/decisions#variable-declarations))

**How to detect it:** Grep `var \w+ = ` inside function bodies (not at package scope — see the next rule for the package-scope exception) where the right-hand side is a literal or a call whose result isn't the zero value.

**Example violation:**
```go
func newCounter() *Counter {
	var i = 42
	var name = "acme"
	return &Counter{start: i, label: name}
}
```

**Corrected:**
```go
func newCounter() *Counter {
	i := 42
	name := "acme"
	return &Counter{start: i, label: name}
}
```

**Severity:** Suggestion

**Enforced by:** revive/var-declaration (flags redundant `var x = value` where `x := value` would do)

**Why it matters:** `:=` reads as one statement and is Go's idiomatic short form for local declarations; `var x = 42` is functionally identical but longer, and mixing the two styles arbitrarily in the same function makes the code harder to skim.

## `var` at package scope is reserved for constants-in-disguise and mutable package state

**What Google/Effective Go says:** `:=` is not available outside function bodies, so all package-level declarations use `var` or `const` by necessity — but the style guide's underlying intent principle still applies: package-level `var` should be reserved for values that are either genuinely mutable shared state or effectively constant values that `const` can't express (e.g., a `[]string` default list, a compiled `regexp.Regexp`, a `time.Duration` computed from arithmetic that isn't a valid constant expression). ([Style Decisions: Declaring empty slices](https://google.github.io/styleguide/go/decisions#declaring-empty-slices); [Uber: Avoid Mutable Globals](https://github.com/uber-go/guide/blob/master/style.md#avoid-mutable-globals))

**How to detect it:** For every package-level `var`, check whether its value is truly a runtime default (compiled regexp, computed duration, slice literal used as a fixed default) versus mutable state that changes during program execution and is read/written from multiple call sites without synchronization.

**Example — legitimate constant-in-disguise:**
```go
var defaultRetryBackoffs = []time.Duration{
	100 * time.Millisecond,
	500 * time.Millisecond,
	2 * time.Second,
} // can't be a const because slice literals aren't constant expressions

var partnerIDPattern = regexp.MustCompile(`^[a-z0-9-]{3,64}$`) // can't be a const
```

**Example violation — mutable global state that should be instance state instead:**
```go
var currentTenant string // set from a request handler, read everywhere — a data race waiting to happen

func SetTenant(id string) { currentTenant = id }
```

**Corrected:**
```go
type Context struct {
	TenantID string
}
// pass *Context explicitly instead of a package var
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` directly; `govet`'s general analyses (part of `enable-all`) may catch some racy global-state patterns under `go test -race`, but the "should this even be a package var" judgment call is a design review item — see [concurrency.md](concurrency.md) for the mutable-globals-and-goroutines angle

**Why it matters:** Package-level `var` outlives any single call and is implicitly shared by every goroutine in the process; using it for a genuine constant-like default is safe, but using it for state that changes during normal operation invites data races and makes the code impossible to unit test in isolation (tests can't have two different "current tenants" running in parallel).

## Use `var` for zero-value declarations

**What Google/Effective Go says:** "When declaring a variable without initializing it... use the `var` form" — this signals "I'm declaring a zero-valued thing on purpose," most commonly as an output parameter for `Unmarshal`. ([Style Decisions: Variable declarations](https://google.github.io/styleguide/go/decisions#variable-declarations))

**How to detect it:** Grep for `:= T{}` or `:= []T(nil)` patterns where a plain `var` declaration would be equivalent and clearer.

**Example violation:**
```go
coords := Point{}     // unnecessary composite literal
primes := []int(nil)  // unnecessary cast
```

**Corrected:**
```go
var coords Point
var primes []int
var magic [4]byte
```

The most common motivation is JSON/proto unmarshalling:
```go
var partner Partner
if err := json.Unmarshal(data, &partner); err != nil {
	return err
}
```

**Severity:** Suggestion

**Enforced by:** `gofumpt`'s `extra-rules` (part of this repo's formatter chain — see [golangci-lint.md](golangci-lint.md#format-chain)) rewrites some zero-value composite-literal patterns automatically; not all cases are auto-fixed, so flag the remainder manually

**Why it matters:** `var coords Point` unambiguously signals "the zero value is meaningful and intentional here," whereas `coords := Point{}` looks like a composite literal that might be about to gain field values, forcing the reader to check before concluding nothing was intended.

## `new(T)` vs `&T{}` — prefer the composite literal

**What Google/Effective Go says:** Effective Go notes both are equivalent for zero-valued allocation, but "the idiom in Go is nearly always... `&T{}`" once a struct has any fields worth naming, because it composes naturally with `&T{Field: val}` when fields are later added. ([Effective Go: Composite literals](https://go.dev/doc/effective_go#composite_literals); [Style Decisions: Variable declarations](https://google.github.io/styleguide/go/decisions#variable-declarations))

**How to detect it:** Grep `new(` calls on struct types. For each, check whether the same package uses `&T{Field: val}` elsewhere for the same type — if so, the `new(T)` call is a stylistic outlier.

**Example violation (inconsistent with the rest of the package):**
```go
func NewCounter(name string) *Counter {
	c := new(Counter)
	c.name = name
	registerCounter(name, c)
	return c
}
```

**Corrected:**
```go
func NewCounter(name string) *Counter {
	c := &Counter{name: name}
	registerCounter(name, c)
	return c
}
```

Both `new(Counter)` and `&Counter{}` are idiomatic in isolation; the rule is to **pick one per package and stick with it**, and to default to `&T{}` for anything that will ever have fields set at construction time, since it reads as one expression instead of a declaration followed by field assignments.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a style-consistency judgment call, not a mechanical rule

**Why it matters:** `&Counter{name: name}` sets fields in the same expression that allocates the value, while `new(Counter)` followed by field assignments spreads the same logical operation across multiple statements for no benefit once there's more than the zero value to set.

## Use `new` (or `&T{}`) when the type contains must-not-copy members

**What Google/Effective Go says:** If a struct embeds a `sync.Mutex` or similar, the zero value is still valid — but copying it after first use is a bug. Allocate on the heap and hand out a pointer. ([Best Practices: Zero-value mutexes](https://google.github.io/styleguide/go/best-practices#synchronization); [Uber: Zero-value Mutexes are Valid](https://github.com/uber-go/guide/blob/master/style.md#zero-value-mutexes-are-valid))

**How to detect it:** For every struct containing a `sync.Mutex`, `sync.RWMutex`, `sync.WaitGroup`, or `sync.Once` field, check that every constructor returns `*T`, never `T`, and that the type is never passed by value.

**Example:**
```go
type Counter struct {
	mu   sync.Mutex
	data map[string]int64
}

func NewCounter(name string) *Counter {
	c := new(Counter) // or: c := &Counter{}
	registerCounter(name, c)
	return c
}
```

Both `new(Counter)` and `&Counter{}` are idiomatic; per the rule above, pick one per package and stick with it.

**Severity:** Violation

**Enforced by:** `govet`'s `copylocks` analysis, part of `enable-all` in this repo's `.golangci.yml` — flags any expression that copies a value containing a `sync.Mutex` or similar no-copy type; see [concurrency.md](concurrency.md#zero-value-mutexes-are-valid-but-must-never-be-copied)

**Why it matters:** Copying a locked (or ever-to-be-locked) mutex produces two independent locks that no longer protect the same data — the bug is silent until two goroutines each acquire "their own" copy and both proceed into a supposedly-exclusive section simultaneously.

## Always declare protobuf messages as pointers

**What Google/Effective Go says:** Generated proto types are reference types in spirit — Marshal/Unmarshal, `proto.Equal`, and gRPC method signatures all take pointers, and a value type doesn't satisfy the `proto.Message` interface. ([Best Practices: Protos](https://google.github.io/styleguide/go/best-practices#import-protos))

**How to detect it:** Grep `pb.\w+{}` (without a leading `&`) or `var x pb.\w+` (non-pointer) for any generated proto type.

**Example violation:**
```go
msg := pb.Request{} // doesn't satisfy proto.Message
```

**Corrected:**
```go
msg := &pb.Request{} // or: msg := new(pb.Request)
```

**Severity:** Violation

**Enforced by:** not enforced by `golangci-lint` directly; this typically surfaces as a compile error at the first call that requires `proto.Message` (e.g., `proto.Marshal(msg)`), so the "audit" is largely the compiler itself plus grep for the pattern before it gets that far

**Why it matters:** A value-typed proto message fails to satisfy `proto.Message` and every generated accessor/setter method, so this is caught quickly — but it's worth flagging in code review before the compile error surfaces mid-refactor.

## Use composite literals when you know the initial values

**What Google/Effective Go says:** Composite literals are the natural form for "I know what I want this to be," and struct literals should name fields explicitly rather than relying on position. ([Style Decisions: Composite literals](https://google.github.io/styleguide/go/decisions#composite-literals))

**How to detect it:** Grep struct literals with positional (unnamed) fields — `Point{x, y}` instead of `Point{X: x, Y: y}` — especially for types imported from another package, where positional literals break the moment a field is inserted or reordered upstream.

**Example violation:**
```go
coords := Point{x, y} // fragile — breaks silently if Point's field order changes
```

**Corrected:**
```go
coords := Point{X: x, Y: y}
primes := []int{2, 3, 5, 7, 11}
captains := map[string]string{"Kirk": "James Tiberius"}
```

**Severity:** Violation for struct literals of types from another package; Suggestion for package-local types

**Enforced by:** `govet`'s `composites` check is part of `enable-all`, though it primarily targets unkeyed literals of *imported* struct types; package-local unkeyed literals are a style preference, not a lint failure, in this config

**Why it matters:** A positional literal for a type defined in another package has no compile-time protection against that package silently reordering, adding, or removing fields — the code keeps compiling but starts assigning the wrong values to the wrong fields.

## Preallocate slices and maps when you know the size

**What Google/Effective Go says:** "If the total number of elements is known, `make` can preallocate the correct amount up front, avoiding subsequent reallocation." ([Best Practices: Slices and maps](https://google.github.io/styleguide/go/best-practices#slices)); Uber's [Prefer Specifying Container Capacity](https://github.com/uber-go/guide/blob/master/style.md#specifying-container-capacity) is the same rule, applied to both `make([]T, 0, n)` (a guaranteed preallocation) and `make(map[K]V, n)` (an approximate hint).

**How to detect it:** Look at every `make([]T, 0)` (zero capacity, no hint) or bare `map[K]V{}`/`make(map[K]V)` immediately preceding a loop that appends/inserts a known or boundable number of times.

**Example:**
```go
// Good: empirically known capacity.
result := make([]Partner, 0, len(rows))
for _, r := range rows {
	result = append(result, partnerFromRow(r))
}
```

For maps, use the size hint:
```go
seen := make(map[string]bool, len(items))
```

**Caveat:** preallocating wildly (e.g., `make([]T, 0, 1_000_000)` for "just in case") wastes memory. Only preallocate when the size is genuinely known or empirically established.

**Severity:** Suggestion

**Enforced by:** `gocritic`'s `performance` tag (enabled in this repo) includes `preferPreallocated` / `appendCombine`-style checks that catch some but not all missed-preallocation cases

**Why it matters:** Appending past a slice's capacity forces a reallocation and a full copy of the existing elements; when the final size is known ahead of time, preallocating avoids that wasted work entirely — often a measurable win in a hot loop.

## `slices.Grow` for incremental capacity hints (Go 1.21+)

**What Google/Effective Go says:** Not covered in Google's guide (predates the `slices` package); documented in the standard library at [`slices.Grow`](https://pkg.go.dev/slices#Grow), consistent with this repo's Go 1.22+ modernization posture (see [tooling-and-modernization.md](tooling-and-modernization.md)).

**How to detect it:** Look for manual capacity-check-and-reallocate patterns (`if cap(s)-len(s) < n { ... }`) that could be replaced by a single `slices.Grow` call.

**Example violation (manual capacity management):**
```go
func appendMany(s []int, more []int) []int {
	if cap(s)-len(s) < len(more) {
		newS := make([]int, len(s), len(s)+len(more))
		copy(newS, s)
		s = newS
	}
	return append(s, more...)
}
```

**Corrected:**
```go
func appendMany(s []int, more []int) []int {
	s = slices.Grow(s, len(more))
	return append(s, more...)
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a modernization opportunity, not a lint failure

**Why it matters:** `slices.Grow` expresses the same guaranteed-capacity intent as the manual check in one call, and it's less error-prone than hand-rolling the copy — the standard library implementation is the one that gets fuzzed and optimized, not each call site's bespoke version.

## Zero-value slice is `nil` and immediately usable

**What Google/Effective Go says:** "There is a difference between the nil and the empty slice... but for most purposes... they can be treated the same." Prefer returning `nil` over an empty slice literal for an absent/empty result. ([Style Decisions: Declaring empty slices](https://google.github.io/styleguide/go/decisions#declaring-empty-slices); [Uber: nil is a valid slice](https://github.com/uber-go/guide/blob/master/style.md#nil-is-a-valid-slice-of-length-0))

**How to detect it:** Grep `return []T{}` in functions whose success path can also return `nil`. Also check emptiness tests — `s == nil` should almost always be `len(s) == 0`, since a non-nil empty slice and a nil slice should usually be treated identically by callers.

**Example violation:**
```go
func ActivePartners(all []Partner) []Partner {
	result := []Partner{} // forces an allocation even when nothing matches
	for _, p := range all {
		if p.Active {
			result = append(result, p)
		}
	}
	return result
}
```

**Corrected:**
```go
func ActivePartners(all []Partner) []Partner {
	var result []Partner // nil until the first append; no wasted allocation
	for _, p := range all {
		if p.Active {
			result = append(result, p)
		}
	}
	return result
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` directly

**Why it matters:** `var result []Partner` costs nothing until the first `append`, whereas `[]Partner{}` allocates an empty backing array immediately; both marshal to `[]` in JSON and both have `len(result) == 0`, so there's rarely a reason to prefer the literal.

## Specify channel direction in function signatures

**What Google/Effective Go says:** This rule also appears in [function-design.md](function-design.md#specify-channel-direction-in-function-signatures) — repeated here because it's also a variable-declaration concern: a channel created with `make(chan T, n)` is bidirectional at the creation site, but the function signatures it's passed to should narrow the direction. ([Best Practices: Channel direction](https://google.github.io/styleguide/go/best-practices#channel-direction))

**How to detect it:** For every channel passed as a function argument, check that the parameter type is directional (`<-chan T` or `chan<- T`) unless the function genuinely both sends and receives on it.

**Example:**
```go
func produce(out chan<- int) { /* ... */ }
func consume(in <-chan int) { /* ... */ }

func main() {
	ch := make(chan int, 16)
	go produce(ch)
	consume(ch)
}
```

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule in this config; see [concurrency.md](concurrency.md#direction-typed-channel-parameters) for the runtime-safety framing of the same rule

**Why it matters:** Narrowing the direction at the function boundary means the compiler — not a runtime panic — catches an accidental `close()` or send on a channel the function was only supposed to read from.

## Stomping vs. shadowing

**What Google/Effective Go says:** Not a named term in Google's guide, but the underlying concern — that nested-scope redeclaration can silently diverge from an outer variable of the same name — is the basis for [Style Decisions: Redundant else](https://google.github.io/styleguide/go/decisions#indent-error-flow) and covered as an audit concern here.

**How to detect it:** **Stomping** — reassigning a variable in the same scope (`x = newValue`) — is always fine when the original value is genuinely no longer needed; don't flag it. **Shadowing** — declaring a new variable in a nested scope with the same name as an outer one — needs a closer look: confirm the inner variable's value is never assumed to have propagated to the outer scope.

**Example violation (shadowing bug — not the `err`-specific exempted case):**
```go
total := 0
if data, ok := cache[key]; ok {
	total := data.Count // shadows outer total; the assignment below is lost
	total += bonus
}
// outer total here is still 0, not total+bonus as the author likely intended
```

**Corrected:**
```go
total := 0
if data, ok := cache[key]; ok {
	total = data.Count + bonus // assignment, not shadowed declaration
}
```

Note: the specific, extremely common case of `if err := f(); err != nil { ... }` shadowing an outer `err` is **not** flagged by this rule — see [error-handling.md](error-handling.md#intentional-err-shadowing-inside-an-if-is-not-a-bug) for why that particular pattern is idiomatic and exempted. This rule is about shadowing of ordinary (non-`err`) variables, and about any shadow — including of `err` — whose value silently fails to propagate to code after the block closes.

**Severity:** Violation

**Enforced by:** `govet`'s `shadow` analysis is **disabled** in this repo's `.golangci.yml` (`govet: disable: [shadow]`, plus the specific `err` text-exclusion rule) — see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation). With `shadow` off entirely, non-`err` shadowing bugs like the one above are **not caught by any linter in this config** and must be found by manual review.

**Why it matters:** Because this repo disables `govet`'s shadow check globally (not just for `err`), shadowing bugs for any variable name are invisible to CI. That raises the stakes on manual review for nested nested `:=` declarations that reuse an outer name — this is one of the few rules in this document where the audit is doing work the linter configuration has explicitly opted out of.

## No unnecessary type conversions

**What Google/Effective Go says:** Not covered in Google's prose guide directly; a mechanically-checkable tidiness rule consistent with the guide's general preference for minimal, intention-revealing code.

**How to detect it:** Grep for `T(x)` conversions where `x` is already statically typed as `T`.

**Example violation:**
```go
var n int64 = 5
m := int64(n) // n is already int64 — no-op conversion
```

**Corrected:**
```go
var n int64 = 5
m := n
```

**Severity:** Violation

**Enforced by:** unconvert

**Why it matters:** A no-op conversion doesn't change behavior, but it does make a reader stop and wonder whether a real type change was intended — removing it eliminates that momentary confusion for free.

## No assignments that are never read

**What Google/Effective Go says:** Not covered in Google's prose guide directly; a correctness-adjacent tidiness rule — an assignment whose value is never subsequently read is either dead code or, more dangerously, a sign the intended assignment target was something else.

**How to detect it:** Grep for variables assigned a value that is unconditionally overwritten or goes out of scope before being read.

**Example violation:**
```go
func loadConfig(path string) (*Config, error) {
	cfg := &Config{Timeout: 30 * time.Second} // this initial value is never read
	cfg = &Config{}                            // overwritten immediately below
	if err := populate(cfg, path); err != nil {
		return nil, err
	}
	return cfg, nil
}
```

**Corrected:**
```go
func loadConfig(path string) (*Config, error) {
	cfg := &Config{}
	if err := populate(cfg, path); err != nil {
		return nil, err
	}
	return cfg, nil
}
```

**Severity:** Violation

**Enforced by:** ineffassign (unread assignments) and wastedassign (assignments immediately overwritten before any read)

**Why it matters:** An ineffectual assignment is either simply dead code that should be deleted, or — more dangerously — evidence that the author meant to assign to a different variable, or in a different order, and the intended effect never happens.

## Integer conversions and overflow risk

**What Google/Effective Go says:** Not covered in Google's prose guide directly; a general defensive-programming concern about narrowing conversions (`int` → `int32`, `int64` → `int`) that can silently truncate or wrap on overflow.

**How to detect it:** Look for narrowing numeric conversions (`int32(someInt64)`, `int(someUint64)`) applied to values that come from user input, external APIs, or unvalidated arithmetic, without a preceding bounds check.

**Example — worth a second look, but not a hard rule in this repo:**
```go
func toInt32(n int64) int32 {
	return int32(n) // silently wraps if n is outside int32's range
}
```

**Preferred where the value's range isn't already guaranteed:**
```go
func toInt32(n int64) (int32, error) {
	if n < math.MinInt32 || n > math.MaxInt32 {
		return 0, fmt.Errorf("value %d out of int32 range", n)
	}
	return int32(n), nil
}
```

**Severity:** Suggestion (this repo's `.golangci.yml` excludes `gosec` rule G115 — "integer overflow conversion" — and has a text-based exclusion rule for `G115:` diagnostics specifically; see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation))

**Enforced by:** not enforced in this repo (G115 exempted) — mention overflow risk as a suggestion, do not treat it as a hard rule

**Why it matters:** Even though this repo doesn't fail CI on narrowing conversions, a silent wraparound on attacker-controlled or externally-sourced input can still turn into a real bug (e.g., a negative "count" after wraparound skipping a validation check) — worth a second look in code review even without lint enforcement.

## How to audit Go code against these rules

1. Grep `var .* = ` inside function bodies (with a non-zero RHS that isn't a composite literal) — each match is a candidate for `:=`.
2. Grep `\b\w+ := \w+{}\b` and `\b\w+ := \[\]\w+{}\b` — each candidate composite-literal-of-zero-value is a `var` candidate.
3. For every package-level `var`, judge whether it's a constant-in-disguise (fine) or mutable shared state (flag for review).
4. Grep `new(` calls on struct types — check consistency with `&T{}` usage elsewhere in the same package.
5. For every struct containing a `sync.Mutex`/`sync.RWMutex`/`sync.WaitGroup`/`sync.Once`, confirm every constructor returns a pointer and the type is never copied (`govet`'s `copylocks` catches most of this automatically).
6. Grep proto type usage in function signatures and locals: every `pb.Foo{}` should be `&pb.Foo{}`. Flag any value-type usage of generated types.
7. Grep struct literals with positional (unnamed) fields for types imported from another package.
8. Look at every `make([]T, 0)` (zero capacity, no hint) or bare `map[K]V{}`. If the surrounding loop appends/inserts a known/bounded number of times, suggest preallocation or `slices.Grow`.
9. Grep `return []T{}` in functions whose other return paths return `nil` — suggest `nil` for consistency, and check `== nil` emptiness tests that should be `len(s) == 0`.
10. Grep function signatures for `chan T` (bidirectional). For each match, read the function body. If it only reads, the signature should be `<-chan T`. If it only writes, `chan<- T`.
11. Look for nested `:=` declarations inside conditional blocks that shadow an outer variable of the same name (excluding the exempted `err`-in-`if` idiom) — these are shadowing bugs invisible to this repo's linter config, since `govet`'s `shadow` check is disabled entirely.
12. Grep `T(x)` conversions where `x` is already statically typed as `T` (`unconvert` will catch these in CI, but review-time awareness helps).
13. Look for assignments that are unconditionally overwritten or never read before going out of scope (`ineffassign`/`wastedassign` catch these in CI).
14. Flag narrowing integer conversions (`int32(int64Val)`) on externally-sourced values as a Suggestion, not a Violation — G115 is exempted in this repo.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
