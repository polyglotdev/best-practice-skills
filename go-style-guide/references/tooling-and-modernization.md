# Tooling and Modernization — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

This repo targets Go 1.22+ (see [SOURCES.md](../../../SOURCES.md)'s modernization posture) and its `golangci-lint` configuration includes linters whose job is specifically to catch code that predates a language or standard-library improvement — `for range` over an integer, the `any` alias, `min`/`max`/`clear` builtins, typed atomics. This file also covers the two "meta" linters that police the audit's own tooling: `nolintlint` (are `//nolint` suppressions justified?) and `unused` (is anything just dead code?).

## `for range n` instead of a manual counting loop (Go 1.22+)

**What Google/Effective Go says:** Not covered in Google's guide directly (predates the feature); documented in the [Go 1.22 release notes](https://go.dev/blog/loopvar-preview) and [`for` statement spec](https://go.dev/ref/spec#For_statements) — `for i := range n` iterates `i` from `0` to `n-1` for any integer `n`, replacing the classic three-clause counting loop for the simple case.

**How to detect it:** Grep `for i := 0; i < n; i++` where the loop body only uses `i` as a counter (never as an index into something requiring the three-clause form's flexibility, like a non-unit step).

**Example violation:**
```go
for i := 0; i < 10; i++ {
	fmt.Println(i)
}
```

**Corrected:**
```go
for i := range 10 {
	fmt.Println(i)
}
```

**Not applicable — non-unit step still needs the three-clause form:**
```go
for i := 0; i < len(buf); i += chunkSize {
	process(buf[i : i+chunkSize])
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this config — a modernization opportunity, not a lint failure; tools like `gopls`'s modernize analyzer or `go fix` can suggest this outside CI

**Why it matters:** `for i := range n` states the loop's intent directly ("iterate n times") without the three-clause form's opportunity for off-by-one errors in the condition or increment — it's shorter and removes an entire class of loop-boundary mistakes for the common "just count" case.

## `any` instead of `interface{}`

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the alias); `any` was added in Go 1.18 as an exact alias for `interface{}`, and the [Go 1.18 release notes](https://go.dev/doc/go1.18) recommend it as the preferred spelling going forward.

**How to detect it:** Grep for `interface{}` in type positions (parameters, return types, struct fields, map values) — `any` is a drop-in replacement everywhere `interface{}` appears with zero methods.

**Example violation:**
```go
func Describe(v interface{}) string {
	m := make(map[string]interface{})
	_ = m
	return fmt.Sprintf("%v", v)
}
```

**Corrected:**
```go
func Describe(v any) string {
	m := make(map[string]any)
	_ = m
	return fmt.Sprintf("%v", v)
}
```

**Severity:** Suggestion

**Enforced by:** not enforced as a hard rule by `golangci-lint` in this config; `gocritic`'s style-tag checks (enabled via `enabled-tags: style` — see [golangci-lint.md](golangci-lint.md)) commonly include this class of suggestion depending on the checker set

**Why it matters:** `any` and `interface{}` are the exact same type — this is purely readability, but `any` is one word instead of two symbols and matches every current standard-library signature (`slices.Contains[S ~[]E, E comparable]`, `errors.As(err error, target any)`), so consistent use avoids a codebase where both spellings appear side by side for no reason.

## `min`/`max`/`clear` builtins instead of hand-rolled helpers (Go 1.21+)

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the builtins); documented in the [Go 1.21 release notes](https://go.dev/doc/go1.21) — `min`, `max`, and `clear` became universal builtins, replacing the small hand-rolled generic (or type-specific, pre-generics) helper functions that were common before.

**How to detect it:** Grep for locally defined `func Max[T ...](a, b T) T`, `func Min(...)`, or manual "loop and delete every key" patterns used to reset a map.

**Example violation:**
```go
func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func resetCounts(counts map[string]int) {
	for k := range counts {
		delete(counts, k)
	}
}
```

**Corrected:**
```go
// max(a, b) is a builtin — no import, no helper function needed
biggest := max(a, b)

func resetCounts(counts map[string]int) {
	clear(counts) // builtin since Go 1.21, clears a map or slice in place
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this config — a modernization opportunity

**Why it matters:** A hand-rolled `maxInt` (or a whole family of `maxInt`, `maxFloat64`, `maxString` before generics existed) is dead weight once the language provides `max` as a universal builtin — deleting it removes both the function and every future reader's need to confirm it does the obvious thing.

## `errors.Join` instead of hand-rolled multi-error aggregation (Go 1.20+)

**What Google/Effective Go says:** Cross-referenced from [error-handling.md](error-handling.md#errorsjoin-for-combining-independent-errors-go-120); documented directly in the [`errors` package](https://pkg.go.dev/errors#Join), added in Go 1.20 — covered here specifically as a modernization item: code written before Go 1.20 often hand-rolls a `MultiError` type that `errors.Join` now replaces.

**How to detect it:** Grep for locally defined multi-error aggregator types (`MultiError`, `ErrorList`, `Errors []error` with a custom `Error() string` that concatenates).

**Example violation:**
```go
type MultiError struct {
	Errors []error
}

func (m *MultiError) Error() string {
	var sb strings.Builder
	for _, e := range m.Errors {
		sb.WriteString(e.Error())
		sb.WriteString("; ")
	}
	return sb.String()
}
```

**Corrected:**
```go
// errors.Join(errs...) replaces the hand-rolled type entirely, and the
// result still works with errors.Is / errors.As across every joined error.
var errs []error
errs = append(errs, err1, err2)
return errors.Join(errs...)
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this config

**Why it matters:** A hand-rolled multi-error type has to reimplement `Is`/`As`/`Unwrap` support to work with the rest of the `errors` package ecosystem — `errors.Join`'s result already supports all three, so replacing a custom type with it is a strict improvement with less code.

## `log/slog` instead of `log` or ad hoc structured-logging wrappers (Go 1.21+)

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the package); documented in the [`log/slog` package](https://pkg.go.dev/log/slog), added in Go 1.21, as the standard library's answer to structured logging — a need most Go codebases previously filled with a third-party dependency or a thin wrapper over `log`.

**How to detect it:** Grep for `log.Printf("... %s=%v ...")`-style manual key-value string formatting used for what is actually structured log data.

**Example violation:**
```go
log.Printf("order processed order_id=%s status=%s duration_ms=%d", o.ID, o.Status, dur.Milliseconds())
```

**Corrected:**
```go
slog.Info("order processed",
	"order_id", o.ID,
	"status", o.Status,
	"duration_ms", dur.Milliseconds(),
)
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this config — an architectural/modernization decision, not a mechanical fix, since migrating an entire codebase's logging calls is a bigger change than a single-line swap

**Why it matters:** `slog`'s structured fields are queryable by downstream log-aggregation tooling without parsing a format string — `log.Printf` output is a single opaque string that a log pipeline has to regex apart to extract `order_id` or `duration_ms`, which is both slower and more fragile than structured fields emitted directly.

## Typed atomics instead of raw `int64`/`int32` with the `atomic` package's function API (Go 1.19+)

**What Google/Effective Go says:** Not covered by Google's guide directly (predates the types); documented in the [`sync/atomic` package](https://pkg.go.dev/sync/atomic), which added `atomic.Int64`, `atomic.Bool`, `atomic.Value`, and similar typed wrappers in Go 1.19, replacing the older pattern of a raw `int64` field manipulated only through `atomic.AddInt64(&x, ...)`-style function calls.

**How to detect it:** Grep for a struct field typed as a raw numeric type with a comment noting "accessed atomically" or "must use atomic.*" alongside every read/write — this convention is exactly what the typed atomics replace.

**Example violation — correctness depends entirely on every caller remembering to use the atomic functions:**
```go
type Stats struct {
	requestCount int64 // must access via atomic.AddInt64/LoadInt64 — nothing enforces this
}

func (s *Stats) Inc() {
	atomic.AddInt64(&s.requestCount, 1)
}

func (s *Stats) Count() int64 {
	return s.requestCount // BUG: direct read bypasses atomic — a data race under -race
}
```

**Corrected:**
```go
type Stats struct {
	requestCount atomic.Int64 // the type itself enforces atomic access
}

func (s *Stats) Inc() {
	s.requestCount.Add(1)
}

func (s *Stats) Count() int64 {
	return s.requestCount.Load()
}
```

**Severity:** Violation

**Enforced by:** `govet`'s general analysis (part of `enable-all`) does not specifically flag a raw-field direct-read bypassing atomic convention; `go test -race` (see [testing.md](testing.md#go-test--race-is-mandatory-for-concurrent-code)) will surface the resulting data race empirically at runtime

**Why it matters:** A raw `int64` field that's "supposed to" always be accessed atomically depends entirely on every single call site remembering the convention and never taking a shortcut — a typed `atomic.Int64` makes that impossible to get wrong, because the field has no exported way to read or write it except through the atomic methods.

## `strconv` instead of `fmt.Sprintf` for simple primitive-to-string conversions

**What Google/Effective Go says:** Not covered by Google's guide directly; documented in [Uber: Prefer strconv over fmt](https://github.com/uber-go/guide/blob/master/style.md#prefer-strconv-over-fmt) — `strconv.Itoa` is measurably faster than `fmt.Sprintf("%d", ...)` for the common case of converting a single primitive to a string, because it skips `fmt`'s reflection-based formatting machinery.

**How to detect it:** Grep for `fmt.Sprintf("%d", ...)`, `fmt.Sprintf("%s", ...)`, `fmt.Sprint(...)` calls whose only job is converting one primitive value to a string, especially inside loops or other hot paths.

**Example violation:**
```go
for _, id := range ids {
	key := fmt.Sprintf("%d", id) // fmt's reflection overhead, for a single int
	keys = append(keys, key)
}
```

**Corrected:**
```go
for _, id := range ids {
	key := strconv.Itoa(id)
	keys = append(keys, key)
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this config

**Why it matters:** `fmt.Sprintf` parses a format string and uses reflection to determine how to render each argument every single call — `strconv.Itoa` (and its siblings `FormatInt`, `FormatFloat`, `Quote`) skip all of that for the specific, common conversions they're built for, which adds up meaningfully in a loop processing many items.

## `slices.Grow` / capacity-aware growth instead of repeated `append` in a hot path

**What Google/Effective Go says:** Cross-referenced from [variable-declarations.md](variable-declarations.md#slicesgrow-for-incremental-capacity-hints-go-121); documented directly in the [`slices` package](https://pkg.go.dev/slices#Grow), added in Go 1.21 — covered here as a modernization item specific to code written before `slices.Grow` existed, which used to hand-roll capacity checks before an append-heavy loop.

**How to detect it:** Grep for a manual `if cap(s) < needed { news := make(...); copy(news, s); s = news }` block immediately preceding an append loop — `slices.Grow` replaces this pattern directly.

**Example violation:**
```go
if cap(results) < len(ids) {
	newResults := make([]Result, len(results), len(ids))
	copy(newResults, results)
	results = newResults
}
for _, id := range ids {
	results = append(results, fetch(id))
}
```

**Corrected:**
```go
results = slices.Grow(results, len(ids)-len(results))
for _, id := range ids {
	results = append(results, fetch(id))
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this config

**Why it matters:** `slices.Grow` expresses the same "make sure there's room for N more elements" intent in one line instead of a hand-rolled capacity check, copy, and reassignment — less code doing exactly the same job, maintained by the standard library instead of by this codebase.

## `//nolint` suppressions must be specific and explained

**What Google/Effective Go says:** Not a Google style-guide rule — a tooling-hygiene rule enforced directly by this repo's own `golangci-lint` configuration (`/home/user/workspace/go-skills-build/.golangci.yml`, `nolintlint` settings), and documented generally in the [`nolintlint` linter's own documentation](https://golangci-lint.run/usage/linters/#nolintlint), which requires every suppression comment to name the specific linter it suppresses and explain why.

**How to detect it:** Grep for `//nolint` comments. Flag any that (a) have no linter name (a bare `//nolint` suppressing every linter on that line), or (b) have a linter name but no explanation after a colon.

**Example violation — bare, unscoped, unexplained suppression:**
```go
result := parseUnsafe(input) //nolint
```

**Corrected:**
```go
result := parseUnsafe(input) //nolint:gosec // input is a compile-time constant, not user-controlled
```

**Severity:** Violation

**Enforced by:** nolintlint (`require-explanation: true`, `require-specific: true`, `allow-unused: false` — see [golangci-lint.md](golangci-lint.md))

**Why it matters:** A bare `//nolint` silences every linter on that line, including ones added to the configuration in the future — a scoped, explained suppression silences exactly one known issue for a stated reason, and `allow-unused: false` in this repo's config means a suppression that stops being needed (because the underlying issue was fixed) is itself flagged as stale, keeping the suppression list honest over time.

## `unused` — no dead code left behind

**What Google/Effective Go says:** Not a named Google-guide rule; a general hygiene expectation reinforced by this repo's enabled [`unused` linter](https://golangci-lint.run/usage/linters/#unused), which extends the compiler's unused-local-variable check to unexported functions, types, constants, and struct fields that are never referenced anywhere in the module.

**How to detect it:** This is largely self-enforcing via CI; the audit-relevant judgment is distinguishing genuinely dead code (delete it) from code that's part of a documented public contract even though nothing in this module currently calls it (e.g., an exported function meant for external consumers — `unused` does not flag exported identifiers for exactly this reason).

**Example violation — unexported helper nothing calls anymore, presumably left over from a refactor:**
```go
func normalizeLegacyID(id string) string { // unexported, unreferenced anywhere in the module
	return strings.TrimPrefix(id, "legacy-")
}
```

**Corrected:** delete it, or, if it's genuinely still needed, find and fix the call site that should be using it.

**Severity:** Violation

**Enforced by:** unused

**Why it matters:** Dead code isn't free even though it doesn't run — it still gets read during code review, still shows up in searches for how a concept is implemented, and still needs to be considered (and often re-verified) during larger refactors, all for zero runtime benefit.

## How to audit Go code against these rules

1. Grep three-clause counting loops (`for i := 0; i < n; i++`) whose body only uses `i` as a plain counter — suggest `for i := range n` (Go 1.22+).
2. Grep `interface{}` in type positions — suggest `any`.
3. Grep hand-rolled `Max`/`Min` helpers and manual "delete every key" map-reset loops — suggest the `min`/`max`/`clear` builtins (Go 1.21+).
4. Grep hand-rolled multi-error aggregator types — suggest `errors.Join` (Go 1.20+, cross-ref [error-handling.md](error-handling.md)).
5. Grep `log.Printf`-style manual key=value string formatting used for structured data — suggest `log/slog` (Go 1.21+) as an architectural improvement.
6. Grep raw numeric struct fields documented as "must access atomically" — suggest the typed `atomic.Int64`/`atomic.Bool`/etc. wrappers (Go 1.19+).
7. Grep `fmt.Sprintf`/`fmt.Sprint` used purely for primitive-to-string conversion, especially in loops — suggest `strconv`.
8. Grep manual capacity-check-then-copy blocks preceding an append loop — suggest `slices.Grow` (cross-ref [variable-declarations.md](variable-declarations.md)).
9. Grep `//nolint` comments — flag any without a specific linter name or without an explanation after the linter name (`nolintlint` covers this in CI).
10. Treat `unused` linter findings on unexported identifiers as deletions unless the audit can identify a genuine, documented reason the code should remain.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
