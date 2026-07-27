# Error Handling — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

Errors in Go are values — and the style guide treats them as part of the API. Callers want to *do* something with errors, not just report them. The rules here are about giving callers structured information they can branch on, without making error chains illegible or smuggling implementation details across boundaries.

## Provide structure so callers can branch programmatically

**What Google/Effective Go says:** Google's guide and Uber's [Error Types](https://github.com/uber-go/guide/blob/master/style.md#error-types) table converge on three accepted shapes depending on whether callers need to match the error and whether the message is static or dynamic. ([Best Practices: Adding context to errors](https://google.github.io/styleguide/go/best-practices#adding-context))

**How to detect it:** For every exported error-returning function, check whether callers ever need to distinguish *why* it failed. If they do today (via string matching, see below) or plausibly will, confirm a sentinel, typed error, or wrapped chain exists for them to match on instead.

**(a) Sentinel error values** for simple, finite vocabularies:
```go
var (
	ErrDuplicate = errors.New("partner: duplicate id")
	ErrNotFound  = errors.New("partner: not found")
)

if errors.Is(err, partner.ErrNotFound) {
	return http.StatusNotFound
}
```

**(b) Custom error types** when the error carries useful structured data:
```go
type ValidationError struct {
	Field  string
	Reason string
}

func (e *ValidationError) Error() string { return e.Field + ": " + e.Reason }

var vErr *ValidationError
if errors.As(err, &vErr) {
	log.Printf("validation failed on field %q", vErr.Field)
}
```

**(c) Wrapped errors with `errors.Is`/`errors.As`** when an error layer needs to expose underlying causes:
```go
if err := repo.Get(ctx, id); err != nil {
	return fmt.Errorf("load partner %q: %w", id, err)
}
```

**Severity:** Suggestion

**Enforced by:** `errorlint` with `asserts: true` (flags type assertions on errors that should use `errors.As`) — see [golangci-lint.md](golangci-lint.md)

**Why it matters:** Structured errors let a caller programmatically decide what to do next (retry, map to an HTTP status, degrade gracefully) instead of guessing from a message string.

## Never branch on error strings

**What Google/Effective Go says:** This is one of the few hard rules: string matching on `err.Error()` couples callers to error message wording — a one-line wording change becomes a silent behavioral change for every caller. ([Style Decisions: Errors](https://google.github.io/styleguide/go/decisions#errors))

**How to detect it:** Grep for `err.Error()` followed by `strings.`, `regexp.`, `Contains(`, `HasPrefix(`, or `==`. Each match is almost always a bug. Also grep for direct `err == someErr` comparisons where `someErr` is a wrapped sentinel — that needs `errors.Is`, not `==`.

**Example violation:**
```go
if strings.Contains(err.Error(), "duplicate") {
	return retryWithSuffix()
}

// also a violation — bypasses wrapping
if err == partner.ErrDuplicate {
	return retryWithSuffix()
}
```

**Corrected:**
```go
if errors.Is(err, partner.ErrDuplicate) {
	return retryWithSuffix()
}
```

**Severity:** Violation

**Enforced by:** `errorlint` with `comparison: true` (flags `==`/`switch` comparisons against error values that should use `errors.Is`) and `asserts: true` (flags type assertions that should use `errors.As`) — see [golangci-lint.md](golangci-lint.md)

**Why it matters:** String matching and raw `==` comparison both silently break the moment the underlying error is wrapped or its message is reworded; `errors.Is`/`errors.As` walk the full wrap chain and don't care about message text.

## Add context without redundancy

**What Google/Effective Go says:** "Additional context can be added... but be judicious" — each wrapping layer should add information the underlying error doesn't already have. ([Best Practices: Adding context to errors](https://google.github.io/styleguide/go/best-practices#adding-context))

**How to detect it:** For each `fmt.Errorf` wrapping call, compare the literal text against the type of error being wrapped. If the wrapped error is a `*fs.PathError` or similar that already names the file/operation, and the wrapper repeats the same path or verb, that's redundant.

**Example violation (redundant):**
```go
if err := os.Open("settings.txt"); err != nil {
	return fmt.Errorf("could not open settings.txt: %v", err)
}
```

The underlying `*PathError` already says `open settings.txt: ...`. The wrapper duplicates the file path.

**Corrected (adds genuinely new context):**
```go
if err := os.Open(path); err != nil {
	return fmt.Errorf("loading launch codes: %v", err)
}
```

Or, if there's no useful context to add:
```go
if err := os.Open(path); err != nil {
	return err
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a judgment call about message content, not a mechanical check

**Why it matters:** Redundant wrapping bloats error messages without giving the reader (or an on-call engineer at 2 a.m.) any new information to act on.

## `%w` to wrap for unwrap-ability; `%v` for human-readable

**What Google/Effective Go says:** Use `%w` when callers need to call `errors.Is`/`errors.As` on the result; use `%v` when transforming the error at a system boundary where the original isn't meant to be unwrapped further. ([Best Practices: Adding context to errors](https://google.github.io/styleguide/go/best-practices#adding-context); [Uber: Error Wrapping](https://github.com/uber-go/guide/blob/master/style.md#error-wrapping))

**How to detect it:** For every `fmt.Errorf` call with an `err` argument, check whether the verb is `%w` or `%v`. Then check whether any caller up the stack calls `errors.Is`/`errors.As` on the result — if so and the verb is `%v`, that's a bug (the chain is broken); if nobody unwraps it and the verb is `%w`, it's at worst a missed opportunity, not a bug.

**Internal error propagation up your own call stack:**
```go
return fmt.Errorf("load partner %q: %w", id, err)
```

**External representation (logs, RPC error messages, HTTP responses) — not meant to be unwrapped:**
```go
log.Printf("partner load failed: %v", err)
```

Two-line rule of thumb:
- *Internal* propagation up your own call stack → `%w`.
- *External* representation (logs, RPC error messages, HTTP responses) → `%v`.

**Severity:** Violation

**Enforced by:** `errorlint` with `errorf: true` (flags `fmt.Errorf` calls that pass an error but don't use `%w`, and flags `%w` misuse with multiple wrapped errors pre-`errors.Join`) — see [golangci-lint.md](golangci-lint.md)

**Why it matters:** `errorlint`'s `errorf` check exists precisely because this distinction is easy to get backwards under review pressure, and getting it wrong either breaks `errors.Is`/`errors.As` for every caller or leaks internal error chain structure across a boundary that should have sanitized it.

## `errors.Join` for combining independent errors (Go 1.20+)

**What Google/Effective Go says:** Not covered in Google's guide directly (predates `errors.Join`); the mechanism is documented in the [`errors` package](https://pkg.go.dev/errors#Join) and is the standard-library-native replacement for hand-rolled multi-error aggregation, consistent with this repo's Go 1.22+ modernization posture (see [tooling-and-modernization.md](tooling-and-modernization.md)).

**How to detect it:** Grep for hand-rolled multi-error types (`type multiError []error` with a custom `Error() string` that concatenates with newlines) predating Go 1.20. Also check validation functions that return only the *first* failure when several independent checks could all be reported at once.

**Example violation (pre-1.20 hand-rolled aggregation):**
```go
type multiError []error

func (m multiError) Error() string {
	var sb strings.Builder
	for _, e := range m {
		sb.WriteString(e.Error())
		sb.WriteString("; ")
	}
	return sb.String()
}

func ValidatePartner(p *Partner) error {
	var errs multiError
	if p.Name == "" {
		errs = append(errs, errors.New("name required"))
	}
	if p.Email == "" {
		errs = append(errs, errors.New("email required"))
	}
	if len(errs) == 0 {
		return nil
	}
	return errs
}
```

**Corrected:**
```go
func ValidatePartner(p *Partner) error {
	var errs []error
	if p.Name == "" {
		errs = append(errs, errors.New("name required"))
	}
	if p.Email == "" {
		errs = append(errs, errors.New("email required"))
	}
	return errors.Join(errs...) // returns nil if errs is empty
}
```

`errors.Is`/`errors.As` both walk into every error joined by `errors.Join`, so callers can still match on any individual cause.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a modernization opportunity, not a lint failure

**Why it matters:** `errors.Join` returns `nil` automatically when given zero non-nil errors, composes correctly with `errors.Is`/`errors.As`, and removes the need to hand-write and maintain a bespoke multi-error type.

## Don't add useless "failed" prefixes

**What Google/Effective Go says:** Echoed in Uber's [Error Wrapping](https://github.com/uber-go/guide/blob/master/style.md#error-wrapping) guidance against stacking "failed to" phrases — the fact that something failed is implicit in returning an error at all.

**How to detect it:** Grep `fmt.Errorf("failed` and `fmt.Errorf("error` — read the surrounding context; if the prefix carries no information beyond "this failed," flag it.

**Example violation:**
```go
return fmt.Errorf("failed: %v", err)
```

**Corrected:**
```go
return err
// or, with real context:
return fmt.Errorf("loading launch codes: %w", err)
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** "Failed to X: failed to Y: failed to Z: connection refused" is a wall of restated failure with one useful word at the end; each layer should add what was being attempted, not restate that an attempt failed.

## Error messages start lowercase with no trailing punctuation

**What Google/Effective Go says:** "Error strings should not be capitalized... and should not end with punctuation, since they are usually printed following other context." ([Style Decisions: Errors](https://google.github.io/styleguide/go/decisions#errors))

**How to detect it:** Grep `errors.New("` and `fmt.Errorf("` for string literals starting with an uppercase letter (excluding proper nouns/acronyms/initialisms) or ending in `.`/`!`.

**Example violation:**
```go
return errors.New("Partner ID is required.")
```

**Corrected:**
```go
return errors.New("partner ID is required")
```

Exception: leading proper nouns and acronyms keep their natural casing (`errors.New("HTTP request failed")` is fine — `HTTP` isn't lowercased for the sake of the rule).

**Severity:** Violation

**Enforced by:** revive/error-strings

**Why it matters:** Error strings are usually composed into a larger sentence by an outer wrapper (`fmt.Errorf("loading config: %w", err)`) — a capitalized, punctuated fragment in the middle of that sentence reads as broken English, while a lowercase, unpunctuated fragment composes cleanly at any nesting depth.

## Handle-once rule — log OR return, not both

**What Google/Effective Go says:** "In most cases... code should not log and then return the error" — pick one boundary to handle the error, because propagating **and** logging produces duplicate noise at every layer that also logs. ([Best Practices: Adding context to errors](https://google.github.io/styleguide/go/best-practices#adding-context); [Uber: Handle Errors Once](https://github.com/uber-go/guide/blob/master/style.md#handle-errors-once))

**How to detect it:** For every `if err != nil` block, check whether it contains both a logging call (`log.*`, `logger.*`, `slog.*`) and a `return err`/`return nil, err`. That combination, repeated at every layer, is the smell.

**Example violation — log AND return, gets logged at every layer that also logs:**
```go
func loadPartner(ctx context.Context, id string) (*Partner, error) {
	p, err := repo.Get(ctx, id)
	if err != nil {
		log.Printf("partner %q load failed: %v", id, err) // gets logged twice
		return nil, err
	}
	return p, nil
}
```

**Corrected — propagate; let exactly one boundary log it:**
```go
func loadPartner(ctx context.Context, id string) (*Partner, error) {
	p, err := repo.Get(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("load partner %q: %w", id, err)
	}
	return p, nil
}
```

Uber's guide also accepts two other legitimate "handle once" shapes: wrap-and-return (above), or match a specific error and degrade gracefully without ever propagating it further:
```go
p, err := repo.Get(ctx, id)
if err != nil {
	if errors.Is(err, partner.ErrNotFound) {
		return defaultPartner(), nil // handled: degrade, don't also log+return
	}
	return nil, fmt.Errorf("load partner %q: %w", id, err)
}
```

**Severity:** Violation

**Enforced by:** not a single dedicated `golangci-lint` rule; `nilerr` catches the closely related "swallow the error but return nil" mistake (see next rule) — the log-and-return duplication itself is caught in code review

**Why it matters:** When every layer in a call chain both logs and re-raises the same error, one failure produces one log line per layer instead of one, making incident logs noisy and harder to correlate.

## No `if err != nil { return nil }` — don't swallow errors as success

**What Google/Effective Go says:** Not named explicitly in Google's prose guide, but directly implied by the "must make a deliberate choice" language in [Style Decisions: Errors](https://google.github.io/styleguide/go/decisions#errors) — discarding an error by returning `nil` in its place is the most dangerous form of discarding it.

**How to detect it:** Grep `if err != nil {` blocks whose body returns `nil` (or `nil, nil`) for the error position instead of the error itself or a wrapped version of it.

**Example violation:**
```go
func loadPartner(ctx context.Context, id string) (*Partner, error) {
	p, err := repo.Get(ctx, id)
	if err != nil {
		return nil, nil // swallows the failure — caller thinks it succeeded with no partner
	}
	return p, nil
}
```

**Corrected:**
```go
func loadPartner(ctx context.Context, id string) (*Partner, error) {
	p, err := repo.Get(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("load partner %q: %w", id, err)
	}
	return p, nil
}
```

**Severity:** Violation

**Enforced by:** `nilerr` — see [golangci-lint.md](golangci-lint.md)

**Why it matters:** Returning `nil` for an error that actually occurred is worse than a panic: the caller has no idea anything went wrong and proceeds on the assumption of success, often with a zero-value or partially-populated result.

## No discarded errors without a documented reason

**What Google/Effective Go says:** "You must not discard [errors]... without at least explicitly acknowledging receipt of the error" — a bare `_ = f()` is only acceptable with a comment justifying the choice. ([Style Decisions: Errors](https://google.github.io/styleguide/go/decisions#errors))

**How to detect it:** Grep `_ = ` followed by a function call that returns an error, and any expression statement calling an error-returning function with the return value not checked at all (bare `f()` where `f` returns `error`).

**Example violation:**
```go
f, _ := os.Open(path) // no comment, no acknowledgment of the failure mode
defer f.Close()
```

**Corrected:**
```go
f, err := os.Open(path)
if err != nil {
	return fmt.Errorf("open %q: %w", path, err)
}
defer f.Close() //nolint:errcheck // best-effort close; read already succeeded
```

**Severity:** Violation

**Enforced by:** errcheck with `check-blank: true` (flags `_ = f()` discards) and `check-type-assertions: true`; note `errcheck` is configured with `exclude-functions: (io.Closer).Close, (net/http.ResponseWriter).Write` in this repo, so a bare unchecked `defer f.Close()` is intentionally allowed without a `//nolint` — see [golangci-lint.md](golangci-lint.md)

**Why it matters:** Every discarded error is a decision, even if the decision is "this can't meaningfully fail here" — writing that decision down (via a `//nolint` reason or a comment) means the next reader doesn't have to re-derive whether the omission was intentional or an oversight.

## Intentional `err` shadowing inside an `if` is not a bug

**What Google/Effective Go says:** Not a named rule in Google's guide; this is a repo-specific linter-alignment clarification. The idiom `if err := f(); err != nil { ... }` is one of the most common Go control-flow patterns and deliberately shadows any outer `err` for the scope of the `if`.

**How to detect it:** For every `if err := ...; err != nil` statement, confirm the shadowed `err` is read and handled entirely within that `if`'s block (or its `else`) and never referenced after the `if` closes as though it were the outer `err`. **That** — an inner `err` silently leaking past the block where the outer `err` is expected to still hold its prior value — is the actual bug to flag, not the shadowing itself.

**Not a bug — shadow is contained to the `if` scope:**
```go
// good — err is intentionally scoped to the if
if err := f(); err != nil {
	return fmt.Errorf("f: %w", err)
}
```

**A real bug — the inner `err` silently shadows and the outer one is never actually set:**
```go
var err error
if result, err := f(); err == nil { // BUG: this err is a new variable
	process(result)
}
// outer `err` here is still nil even if f() failed — caller sees a
// false "no error" even though nothing checked the real failure.
if err != nil {
	return err
}
```

**Corrected:**
```go
var err error
var result Result
result, err = f() // assignment, not a new shadowed declaration
if err != nil {
	return err
}
process(result)
```

**Severity:** Violation (only when the shadow escapes its intended scope) — the contained, idiomatic form above is not flagged at all

**Enforced by:** not enforced — this repo's `.golangci.yml` explicitly disables `govet`'s `shadow` diagnostic for the text `shadow: declaration of "err"` (see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation)). Because the linter is silent here, this check must be done by reading the code: confirm every shadowed `err` is fully consumed inside its own block.

**Why it matters:** The contained shadow (`if err := f(); err != nil`) is standard, idiomatic Go and disabling `govet`'s blanket shadow check for `err` avoids constant false positives on this pattern. The actual risk — a shadowed `err` that silently diverges from an outer `err` the rest of the function still checks — is rare but genuinely dangerous, so it needs a manual read rather than a lint rule tuned to avoid noise on the common case.

## Never panic across a public API boundary

**What Google/Effective Go says:** `panic` is for genuinely unrecoverable internal-state corruption, not for input validation, missing config, or transient failures. Libraries should return `error`. ([Best Practices: Panic](https://google.github.io/styleguide/go/best-practices#panic); [Uber: Don't Panic](https://github.com/uber-go/guide/blob/master/style.md#dont-panic))

**How to detect it:** Grep `panic(` in non-`main`, non-`init`, non-test files. For each match, trace whether the panic can escape a public API. If yes, flag it. If a panic is used as an internal control-flow shortcut, confirm it's caught with `recover` before crossing the package boundary.

**Example violation:**
```go
func ParseConfig(s string) *Config {
	if s == "" {
		panic("empty config") // never escape package; never inflict on caller
	}
	// ...
	return &Config{}
}
```

**Corrected:**
```go
func ParseConfig(s string) (*Config, error) {
	if s == "" {
		return nil, errors.New("empty config")
	}
	// ...
	return &Config{}, nil
}
```

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule for general panic use; `govet`'s general analysis (part of `enable-all`) catches some misuse patterns, but "no panic across API boundaries" is primarily a code-review check

**Why it matters:** A panicking library forces every caller to either accept crashes or wrap every call in `recover`, which defeats Go's explicit error-return convention and makes failure handling inconsistent across the codebase.

## Program initialization errors — propagate to `main`, exit cleanly

**What Google/Effective Go says:** In `main`, log the error and call `os.Exit(1)` (or the equivalent `log.Exit`). Don't use `log.Fatal` deep inside library code — it skips deferred cleanups and produces a stack trace that's usually noise. ([Best Practices: Program initialization](https://google.github.io/styleguide/go/best-practices#error-handling); [Uber: Exit Once](https://github.com/uber-go/guide/blob/master/style.md#exit-once))

**How to detect it:** Grep `log.Fatal` and `log.Fatalf` outside `main.go`/`cmd/**`. Each match outside those locations is a candidate violation.

**Example violation (library file):**
```go
func MustLoadConfig(path string) *Config {
	cfg, err := loadConfig(path)
	if err != nil {
		log.Fatalf("config load failed: %v", err) // library code should not exit
	}
	return cfg
}
```

**Corrected:**
```go
// In library:
func LoadConfig(path string) (*Config, error) { /* ... */ return nil, nil }

// In main:
func main() {
	cfg, err := LoadConfig(*configPath)
	if err != nil {
		log.Printf("config load failed: %v", err)
		os.Exit(1)
	}
	_ = cfg
}
```

**Severity:** Violation

**Enforced by:** not enforced by `golangci-lint` directly; `revive/error-return` and `revive/error-naming` catch adjacent mistakes but not `log.Fatal` placement specifically — enforce via grep in review, per the "How to detect it" heuristic above

**Why it matters:** `log.Fatal` calls `os.Exit` internally, which skips every deferred cleanup in the call stack — acceptable at the very top of `main`, but catastrophic inside library code where callers expect to be able to handle the error and continue.

## `log.Fatal` is acceptable only for unrecoverable invariant breaks

**What Google/Effective Go says:** If an invariant check inside the program finds the world is impossibly broken — internal state corrupt, no way to recover — `log.Fatal` is acceptable. `panic` is *not* preferred for this because deferred functions can deadlock or corrupt state further. ([Best Practices: Program initialization](https://google.github.io/styleguide/go/best-practices#error-handling))

**How to detect it:** For every `log.Fatal`/`log.Fatalf` call (including ones in `main`), read the surrounding context. Is this genuinely an unrecoverable invariant break (e.g., a required config file is structurally corrupt and no sane default exists), or is it a routine, expected failure mode that should instead be handled or retried?

**Example — acceptable, invariant genuinely broken:**
```go
func main() {
	cfg, err := LoadConfig(*configPath)
	if err != nil {
		log.Fatalf("config load failed, cannot continue: %v", err)
	}
	_ = cfg
}
```

**Example — not acceptable, this is a routine and recoverable failure:**
```go
func handleRequest(w http.ResponseWriter, r *http.Request) {
	p, err := repo.Get(r.Context(), r.PathValue("id"))
	if err != nil {
		log.Fatalf("lookup failed: %v", err) // takes down the whole server for one bad request
	}
	writeJSON(w, p)
}
```

**Severity:** Violation

**Enforced by:** not enforced by `golangci-lint` — requires judgment about whether the failure is genuinely unrecoverable

**Why it matters:** `log.Fatal` terminates the entire process. Calling it from a per-request code path turns one bad request into a full outage; it should be reserved for startup-time invariant checks where continuing would be worse than exiting.

## How to audit Go code against these rules

1. Grep `err.Error()` — every result that's followed by `strings.`, `regexp.`, `Contains`, `HasPrefix`, `==` is almost certainly a violation.
2. Grep `fmt.Errorf` — for each match, read the format string. Does it duplicate information that's already in the wrapped error? Does it have a useless "failed:" prefix? Should it use `%w` instead of `%v` (or vice versa)?
3. Grep string literals passed to `errors.New`/`fmt.Errorf` for a leading capital letter or trailing punctuation.
4. Grep hand-rolled multi-error aggregation types — suggest `errors.Join` (Go 1.20+).
5. Look for cases where the same error is both logged and returned in the same function. That's the duplicate-noise pattern — unless the log-and-degrade or match-and-degrade pattern applies instead.
6. Grep `if err != nil {` blocks that return `nil`/`nil, nil` for the error position — that's error swallowing, not error handling.
7. Grep `_ = ` before error-returning calls, and bare unchecked calls, for a missing justification comment (exempt `(io.Closer).Close` and `(net/http.ResponseWriter).Write`, which this repo's `errcheck` config excludes).
8. For every `if err := ...; err != nil` shadow, confirm the inner `err` is fully consumed inside its own block and never assumed to have set an outer `err` variable.
9. Grep `panic(` — for each match, trace whether the panic can escape a public API. If yes, flag as a violation.
10. Grep `log.Fatal` and `log.Fatalf` — for each match outside `main.go`/`cmd/**`, flag and suggest returning an error. For matches inside `main`, confirm the failure is genuinely unrecoverable.
11. Look for missing error-wrapping context: a function calls a repository, gets an error, and returns it bare — fine if the caller has enough context, otherwise suggest wrapping with the operation name.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
