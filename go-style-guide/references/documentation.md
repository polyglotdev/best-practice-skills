# Documentation — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

godoc-style comments are the user-facing manual for a Go package. The style guide is opinionated about *what* to document, not just *how*: focus on the non-obvious. The audience is someone using the package, not someone reading the source.

## Document the non-obvious; skip the rest

**What Google/Effective Go says:** "Comments... document the non-obvious" — don't enumerate every parameter or restate the type signature in prose. Focus on pre/post-conditions, side effects, concurrency assumptions, cleanup responsibilities, and error semantics. ([Best Practices: Comments](https://google.github.io/styleguide/go/best-practices#comments))

**How to detect it:** For every doc comment, check whether it says anything the function name and signature don't already say. A comment that's a grammatical restatement of the identifier adds nothing.

**Example violation (useless):**
```go
// Name returns the name.
func (p *Partner) Name() string { return p.name }
```

**Corrected (useful, or just omit the comment):**
```go
// Name returns the partner's display name. Returns the partner ID as a
// fallback when the name has not yet been set during onboarding.
func (p *Partner) Name() string { return p.displayNameOrFallback() }
```

If the function name and signature say it all, no comment is needed — except for exported identifiers, where godoc requires *some* comment. In those cases, keep it one line and useful.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — comment *quality* isn't mechanically checkable; comment *presence* on exported identifiers is a separate rule below

**Why it matters:** A comment that only restates the signature adds a maintenance burden (it can drift from the code) without adding any information the reader didn't already have from the declaration itself.

## Every exported identifier needs a godoc comment

**What Google/Effective Go says:** "Every exported... identifier... needs a doc comment." ([Best Practices: Comments](https://google.github.io/styleguide/go/best-practices#comments); [Effective Go: Doc comments](https://go.dev/doc/effective_go#commentary))

**How to detect it:** For every exported `func`, `type`, `var`, and `const`, check whether an immediately preceding `//` comment exists.

**Example violation:**
```go
func Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Corrected:**
```go
// Get returns the partner with the given ID.
func Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Severity:** Violation

**Enforced by:** `revive/exported` — flags exported identifiers with missing (or malformed) doc comments

**Why it matters:** godoc.org and `go doc` render only what's written above the declaration; an undocumented exported identifier is invisible to anyone browsing the package's generated documentation instead of its source.

## Godoc for exported identifiers must start with the identifier name

**What Google/Effective Go says:** "Doc comments should... begin with the name of the thing being described" so that tools (and `go doc`) can extract a one-line summary. ([Style Decisions: Doc comments](https://google.github.io/styleguide/go/decisions#doc-comments))

**How to detect it:** For every exported identifier's doc comment, check whether the first word of the comment matches the identifier name exactly.

**Example violation:**
```go
// Returns the partner with the given ID.
func Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Corrected:**
```go
// Get returns the partner with the given ID.
func Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Severity:** Suggestion (downgraded from Violation — this repo's `.golangci.yml` disables `staticcheck` checks ST1020 (exported func), ST1021 (exported type), and ST1022 (exported var/const), all of which enforce "doc comment starts with the identifier name"; see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation))

**Enforced by:** not enforced in this repo (ST1020/ST1021/ST1022 exempted) — recommend for godoc-rendering quality, do not block review on it

**Why it matters:** `go doc` and godoc.org synthesize a package's identifier index from the first sentence of each comment; when the sentence doesn't start with the identifier name, the generated summary index reads oddly (e.g., "partner: Returns the..." instead of "partner: Get returns the...").

## Package doc comment requirement

**What Google/Effective Go says:** "Every package should have a package comment... introducing the package and providing information relevant to the package as a whole." ([Style Decisions: Package comments](https://google.github.io/styleguide/go/decisions#package-comments); [Effective Go: Commentary](https://go.dev/doc/effective_go#commentary))

**How to detect it:** For every package, check whether exactly one file has a `// Package <name> ...` comment immediately above the `package` clause (in the primary file or in `doc.go`).

**Example violation:**
```go
// partner.go — no package comment anywhere in the package
package partner

type Partner struct{ /* ... */ }
```

**Corrected:**
```go
// Package partner provides repositories and domain models for managed
// partner records in the Crossing platform.
package partner

type Partner struct{ /* ... */ }
```

**Severity:** Suggestion (downgraded from Violation — this repo's `.golangci.yml` disables `staticcheck` check ST1000 ("package doc comment required"); see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation))

**Enforced by:** not enforced in this repo (ST1000 exempted) — recommend for non-trivial packages, especially ones with a meaningful public API, but do not block review on its absence

**Why it matters:** The package comment is the first thing a reader sees on the package's godoc page — without one, `go doc partner` shows nothing but a bare list of identifiers with no orienting context about what the package is for.

## `// Deprecated:` marker syntax

**What Google/Effective Go says:** "To signal that an identifier should not be used, add a paragraph to its doc comment that begins with `Deprecated:` followed by information about the deprecation." This is the standard [godoc deprecation convention](https://go.dev/wiki/Deprecated), referenced from Google's [Best Practices: Comments](https://google.github.io/styleguide/go/best-practices#comments).

**How to detect it:** Grep comments for the word "deprecated" (case-insensitive) that do NOT match the exact `// Deprecated: ` prefix on its own paragraph. Tools like `staticcheck` and IDE deprecation strikethrough rendering only recognize the exact syntax.

**Example violation:**
```go
// FetchLegacy fetches a partner using the old v1 API. Deprecated, use Fetch instead.
func FetchLegacy(id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Corrected:**
```go
// FetchLegacy fetches a partner using the old v1 API.
//
// Deprecated: use Fetch instead. FetchLegacy will be removed after the
// v1 API sunset date (2027-01-01).
func FetchLegacy(id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Severity:** Violation

**Enforced by:** `staticcheck` (the `SA1019` check, part of `checks: [all]` minus the ST10xx exemptions, flags *usage* of identifiers marked `Deprecated:`; it does not, however, verify that a prose "deprecated" mention uses the exact marker syntax — that half is a manual/code-review check)

**Why it matters:** Only the exact `Deprecated: ` paragraph syntax is machine-readable — `staticcheck`'s `SA1019`, godoc's strikethrough rendering, and most IDEs all key off that literal string. A prose mention of "deprecated" anywhere else in the comment is invisible to every one of those tools.

## Document context behaviour only when it deviates from convention

**What Google/Effective Go says:** Context cancellation is *assumed* — every Go developer reads `ctx context.Context` as "this function obeys cancellation." Document only when a function's context handling is unusual: it stores the context, requires specific attached values, has its own interrupt mechanism, or has special lifetime expectations. ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts))

**How to detect it:** For every function taking `context.Context`, read its doc comment. If it says only "ctx allows cancellation" or similar, that's redundant. If the function's actual behavior around `ctx` is unusual — see the corrected examples — check that the comment says so.

**Don't say (redundant, restates the assumed convention):**
```go
// Run executes the job. ctx can be used to cancel the operation.
func Run(ctx context.Context, j Job) error
```

**Do say (deviates from convention — must document):**
```go
// Run executes the job. Returns nil, not ctx.Err(), if ctx is
// cancelled before the job produces a result.
func Run(ctx context.Context, j Job) error

// NewReceiver returns a Receiver that reads from addr. The context
// should not have a deadline; use Receiver.Close to stop reading.
func NewReceiver(ctx context.Context, addr string) (*Receiver, error)

// Principal returns the authenticated identity attached to ctx. The
// context must have a value attached by security.NewContext.
func Principal(ctx context.Context) (Identity, error)
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`; see [context.md](context.md) for the corresponding non-documentation context rules that `contextcheck` and `revive/context-as-argument` do enforce

**Why it matters:** Restating the assumed convention on every function is noise that trains readers to skip context-related doc paragraphs entirely — which means the rare function that genuinely behaves unusually with its context won't get read either.

## Document concurrency assumptions

**What Google/Effective Go says:** "Read-only operations... on data structures are generally understood to be safe for concurrent use... Document...if a type's mutating methods are also safe for concurrent use, since that is not the default assumption." ([Best Practices: Synchronization](https://google.github.io/styleguide/go/best-practices#synchronization))

**How to detect it:** For every mutating method, check whether the doc comment states its concurrency safety (or lack thereof). Read-only methods do not need this — don't flag their absence.

**Example:**
```go
// Add appends a job to the queue. Safe for concurrent use.
func (q *Queue) Add(j Job) { /* ... */ }

// Drain returns all queued jobs and resets the queue. Drain must not
// be called concurrently with Add or with other Drain calls.
func (q *Queue) Drain() []Job { /* ... */ return nil }
```

If the type's synchronization is provided entirely by an external mechanism (e.g., an RPC layer), say so explicitly rather than leaving it ambiguous:
```go
// NewFortuneTellerClient returns a client safe for simultaneous use by
// multiple goroutines; the underlying Stubby connection provides its
// own synchronization.
func NewFortuneTellerClient(addr string) (*FortuneTellerClient, error) { /* ... */ return nil, nil }
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`; see [concurrency.md](concurrency.md) for the corresponding runtime concurrency rules

**Why it matters:** Concurrent misuse bugs are notoriously hard to reproduce and debug; a one-line comment stating the safety contract prevents callers from having to read the implementation (or get it wrong) to find out.

## Document cleanup responsibilities

**What Google/Effective Go says:** "If a function returns some type that requires cleanup and the cleanup behavior is not obvious... document it." ([Best Practices: Comments](https://google.github.io/styleguide/go/best-practices#comments))

**How to detect it:** For every function returning an `io.Closer`, a lock, a file handle, a channel meant to be drained, or a network connection, check that the comment states who is responsible for cleanup and how.

**Example:**
```go
// Open returns a connected client. Call Close when done to release the
// underlying TCP connection.
func Open(addr string) (*Client, error) { /* ... */ return nil, nil }

// Get returns the response body. Caller must Close the body to release
// the connection back to the pool.
func (c *Client) Get(url string) (*Response, error) { /* ... */ return nil, nil }
```

**Severity:** Suggestion

**Enforced by:** `bodyclose` enforces the *runtime* half of this rule for `http.Response.Body` specifically (the caller must actually call `Close`, not just be told to in a comment) — see [concurrency.md](concurrency.md#always-close-httpresponsebody) and [golangci-lint.md](golangci-lint.md)

**Why it matters:** The reader cannot guess cleanup responsibility from a type signature alone; a returned `*Client` gives no syntactic hint that it holds an open TCP connection until the doc comment says so.

## Document significant error returns

**What Google/Effective Go says:** "If a function can return errors that the caller may need to explicitly handle, mention these error values in the doc comment." ([Best Practices: Comments](https://google.github.io/styleguide/go/best-practices#comments))

**How to detect it:** For every function that returns a documented sentinel or typed error, check that the function's own doc comment lists which ones callers might need to branch on.

**Example:**
```go
// Get returns the partner with the given ID.
//
// Returns ErrNotFound if no partner with that ID exists.
// Returns *ValidationError if the ID format is malformed.
func (r *Repository) Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

If a package has a consistent error convention (e.g., "all errors are wrapped with `fmt.Errorf` and unwrap to one of the package sentinels"), document that in the *package* godoc once instead of repeating on every function.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`; see [error-handling.md](error-handling.md#provide-structure-so-callers-can-branch-programmatically) for the corresponding structural rule

**Why it matters:** Without documented error values, callers either over-handle (wrapping every possible error generically) or under-handle (missing an important branch like `ErrNotFound`) because they have no contract to code against beyond "returns an error."

## Godoc formatting basics

**What Google/Effective Go says:** "Comments should be full sentences... a blank line separates paragraphs... indent by 2 spaces for verbatim formatting." ([Style Decisions: Comments](https://google.github.io/styleguide/go/decisions#commentary))

**How to detect it:** Read each multi-line doc comment. Check for sentence casing/punctuation, blank-line paragraph breaks, and consistent 2-space indentation for any verbatim blocks.

- Sentences. Capital letter. Full punctuation.
- Blank line separates paragraphs.
- Indent two spaces for verbatim formatting (code, tables, ASCII diagrams).
- A single line in all-capitals followed by a paragraph is a section header.
- Runnable examples live in `_test.go` files as `ExampleXxx` functions; they appear in godoc and double as tests.

**Example:**
```go
// Package partner provides repositories and domain models for managed
// partner records.
//
// USAGE
//
// Construct a Repository with New, then call Get or List:
//
//   repo := partner.New(db)
//   p, err := repo.Get(ctx, "acme")
package partner
```

**Severity:** Suggestion

**Enforced by:** `gofmt`/`gofumpt` reformat code but do not rewrite comment prose; `misspell` catches spelling errors within comments and strings (see next rule) but not grammar, capitalization, or paragraph structure

**Why it matters:** Consistent comment formatting is what makes `go doc` output (and godoc.org rendering) readable — a comment with no paragraph breaks or with inconsistent indentation renders as a wall of text or with broken verbatim blocks.

## Spelling in comments and strings

**What Google/Effective Go says:** Not covered by Google's prose guide directly, but is a mechanically-checkable subset of the [Style Decisions: Commentary](https://google.github.io/styleguide/go/decisions#commentary) requirement for professional, readable documentation.

**How to detect it:** Run `misspell` (either standalone or via `golangci-lint run`) — it flags common English misspellings in comments, string literals, and identifiers.

**Example violation:**
```go
// Get returns the partner wth the given ID. Retuns ErrNotFound if
// the partner deosn't exist.
func Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Corrected:**
```go
// Get returns the partner with the given ID. Returns ErrNotFound if
// the partner doesn't exist.
func Get(ctx context.Context, id string) (*Partner, error) { /* ... */ return nil, nil }
```

**Severity:** Violation

**Enforced by:** misspell

**Why it matters:** Misspellings in godoc-visible comments ship straight to `pkg.go.dev` and any generated documentation site; `misspell` catches the common cases (transposed letters, doubled words) essentially for free with no false-positive cost.

## Signal-boost surprising conditionals with a comment

**What Google/Effective Go says:** Not a named rule in Google's guide; a practical extension of the "document the non-obvious" principle to control flow that reads ambiguously, such as `if err := f(); err == nil { ... }` where the *absence* of an error is the success path.

**How to detect it:** Read `if` conditions that test `== nil` on an error (rather than the more common `!= nil`) — these read against the grain and benefit from a one-line comment marking which branch is the happy path.

**Example:**
```go
// Good: clarifies success path.
if err := f(); err == nil {
	// happy path
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** This isn't a hard rule, but in code with a lot of error returns, an `== nil` branch reads against the grain of the far more common `!= nil` idiom, and a one-line comment saves the reader a double-take.

## Use a `doc.go` for long package overviews

**What Google/Effective Go says:** "If there is no obvious primary file... it is acceptable to put the doc comment in a file named `doc.go`." ([Style Decisions: Package comments](https://google.github.io/styleguide/go/decisions#package-comments)) See also [packages.md](packages.md#use-docgo-for-lengthy-package-level-documentation) for the corresponding package-organization rule.

**How to detect it:** For packages with a multi-paragraph package comment, check whether it's isolated in `doc.go` rather than crammed above an unrelated first type in another file.

**Example:**
```go
// doc.go
// Package crossing provides the managed file transfer pipeline that
// replaces GoAnywhere for HealthBridge partner integrations.
//
// The package is organised around four core types: Partner, Job, ...
package crossing
```

**Severity:** Suggestion

**Enforced by:** `staticcheck` ST1000 (package doc comment required) is exempted in this repo — see the package-doc-comment rule above; `doc.go` file placement itself is not separately enforced

**Why it matters:** Isolating a long package overview in `doc.go` keeps the file that defines the primary type free of unrelated prose, while still giving `go doc` a single obvious place to find the package-level comment.

## How to audit Go code against these rules

1. For every exported identifier (`func`, `type`, `var`, `const`), check whether a godoc comment is present. Missing comments on exported identifiers should be flagged as a Violation (`revive/exported`).
2. For each existing comment, judge: does it say something the signature doesn't? If it just restates the name and signature in English, suggest deletion or rewriting (Suggestion).
3. Check whether each exported identifier's doc comment starts with the identifier's own name. Flag as Suggestion only — `staticcheck` ST1020/1021/1022 are exempted in this repo.
4. Check whether the package has a package-level doc comment. Flag as Suggestion only — `staticcheck` ST1000 is exempted in this repo.
5. Grep comments for "deprecated" (case-insensitive) that don't match the exact `// Deprecated: ` paragraph syntax — flag as Violation.
6. For every function that takes `context.Context`, check whether the comment says anything about cancellation. If it just says "ctx allows cancellation," flag as redundant (that's the assumed convention). If the function behaves unusually with context, confirm that's documented.
7. For every function that returns a value that must be cleaned up (`io.Closer`, channel, file handle, network connection, lock), check that the comment says *who closes/releases what*. If not, flag.
8. For every function that returns a typed error or wraps a sentinel, check that the comment lists the returned error types. If not, flag.
9. For each type with methods, check whether the type's godoc says anything about concurrency. If multiple methods exist and concurrency intent is unclear, suggest a one-liner.
10. Run `misspell` (or `golangci-lint run --enable-only=misspell`) across the package and flag every hit as a Violation.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
