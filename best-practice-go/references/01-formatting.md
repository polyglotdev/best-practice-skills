<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 1. Formatting

Go settled the formatting debate before most projects even start: whitespace,
alignment, brace placement, and import ordering are not style choices you
make — they are the output of a tool chain. This chapter is intentionally
short because there is almost nothing to decide by hand. It draws from
[Effective Go: Formatting](https://go.dev/doc/effective_go#formatting) and
treats `gofmt` as the baseline, non-negotiable formatter, with `gofumpt`
and `goimports` layered on top as a stricter, project-configurable chain.
Naming and package layout — the parts of style formatters can't enforce —
are covered in [Chapter 2](02-names.md) and [Chapter
3](03-package-organization.md). Where this chapter names a specific
linter, the callout reflects a representative `golangci-lint` setup; teams
adopting this guide should configure their own `.golangci.yml` to match.

## 1.1 Run `gofmt` on every file before it is committed.

> Why? `gofmt` produces one canonical layout for Go source. When every
> file is formatted the same way, code review stops wasting time on tabs
> vs. spaces or brace placement and focuses on logic. Unformatted code is
> also a signal the author never ran their toolchain.

```go
// bad
func Add(a int,b int) int {
  if a>0 {
      return a+b
  }
	return b
}

// good
func Add(a int, b int) int {
	if a > 0 {
		return a + b
	}
	return b
}
```

Per [Effective Go: Formatting](https://go.dev/doc/effective_go#formatting),
`gofmt` reads a Go program and emits the source in a standard style of
indentation and vertical alignment, retaining and reformatting comments.
Nobody hand-formats Go code in a reviewed codebase; it is a build-time
guarantee, not a preference.

> Enforced by: `formatters: gofmt` (baseline of every `golangci-lint`
> formatter chain).

## 1.2 Indent with tabs; let the formatter chain own the character, not the editor.

> Why? Mixed tabs and spaces produce diffs that look identical but are
> byte-different, which pollutes `git blame` and causes spurious merge
> conflicts. `gofmt` always emits tabs for indentation — fighting it in
> editor settings only creates churn.

```go
// bad
type Config struct {
    Host string
    Port int
}

// good
type Config struct {
	Host string
	Port int
}
```

> Enforced by: `formatters: gofmt`, `whitespace` (flags stray leading and
> trailing whitespace inside function bodies that the formatters alone
> may not normalize).

## 1.3 Layer `gofumpt` on top of `gofmt` for a stricter, more opinionated baseline.

> Why? `gofmt` deliberately leaves some inconsistencies alone (empty
> lines at the start of a block, multi-line composite literals that
> could fit one field per line, unnecessary `var x = T{}` forms).
> `gofumpt` is a strict superset of `gofmt` that closes those gaps so
> two engineers never produce different-looking code from the same
> logic. Run it with `extra-rules: true` for the full stricter subset.

```go
// bad — passes plain gofmt, but gofumpt (extra-rules) flags every one of these
func New() *Client {

	c := &Client{
		host: "localhost", port: 8080,
	}
	return c
}

// good — gofumpt's stricter rules applied: no leading blank line in the
// block, one field per line once a composite literal wraps
func New() *Client {
	c := &Client{
		host: "localhost",
		port: 8080,
	}
	return c
}
```

> Enforced by: `formatters: gofumpt` with `extra-rules: true`.

## 1.4 Run `goimports` with your module's local-prefix configured, so imports settle into three groups.

> Why? `goimports` is a superset of `gofmt`: it formats the file *and*
> inserts or removes import lines to match what the code actually
> references. Configured with a `local-prefixes` value matching your
> module path, it also splits imports into three groups — standard
> library, third-party, and your own module's packages — so a reader
> can immediately see how much of a file's dependency surface is
> "ours" versus external. See [Chapter 4](04-imports.md) for the full
> grouping and aliasing rules.

```go
// bad — saved with gofmt only; groups collapsed, one import stale
import (
	"fmt"
	"platform-backend/internal/store"
	"os"
	"github.com/google/uuid"
)

// good — goimports with local-prefixes: platform-backend produces
// three groups: stdlib / third-party / module-local
import (
	"fmt"
	"os"

	"github.com/google/uuid"

	"platform-backend/internal/store"
)
```

> Enforced by: `formatters: goimports` with `local-prefixes:
> platform-backend` (adjust the prefix to your own module path).

## 1.5 Wire the full formatter chain into editor format-on-save, not a manual step.

> Why? Manual formatting is forgotten under deadline pressure. A
> pre-commit hook or editor integration that runs `gofmt` → `gofumpt` →
> `goimports` on save makes the standard format the path of least
> resistance instead of an extra chore. Effective Go assumes this
> tooling is always running, so hand-formatted examples in review are
> treated as bugs, not style opinions.

```go
// bad — developer manually aligns struct fields, drifts from the formatter chain
type User struct {
	ID    int
	Name string
	Email    string
}

// good — gofmt/gofumpt (via format-on-save) align fields consistently
type User struct {
	ID    int
	Name  string
	Email string
}
```

## 1.6 Treat `go vet` as part of formatting-adjacent hygiene, not optional linting.

> Why? `go vet` catches mistakes formatters cannot, such as `Printf`
> calls with mismatched verbs, struct tags that don't parse, or copying
> a `sync.Mutex` by value. These are cheap, automatic checks that should
> run on every build; skipping them lets trivially detectable bugs reach
> review.

```go
// bad — compiles, but go vet flags the format-verb mismatch
fmt.Printf("user id: %s\n", 42)

// good — go vet is clean; the verb matches the argument type
fmt.Printf("user id: %d\n", 42)
```

> Enforced by: `govet` with `enable-all: true` (a team may selectively
> disable specific analyzers, such as `fieldalignment` or `shadow`, when
> they don't match the team's priorities).

## 1.7 Layer `staticcheck` and `golangci-lint` on top of `gofmt`/`go vet`.

> Why? `gofmt` guarantees layout and `go vet` catches a narrow set of
> correctness bugs, but neither enforces the broader idioms in this
> guide (unused parameters, shadowed errors, inefficient string building,
> and so on). `staticcheck` and `golangci-lint` (which bundles
> `staticcheck`, `govet`, and dozens of other analyzers) close that gap
> and should run in CI, not just locally.

```go
// bad — CI only runs "go build"; a shadowed err ships to production
func Load() error {
	data, err := os.ReadFile("config.json")
	if err != nil {
		return err
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		log.Println(err) // err handled but swallowed, not returned — staticcheck flags this pattern
	}
	return nil
}

// good — golangci-lint (staticcheck, errcheck, govet) runs in CI and blocks the merge
func Load() error {
	data, err := os.ReadFile("config.json")
	if err != nil {
		return err
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		return fmt.Errorf("unmarshal config: %w", err)
	}
	return nil
}
```

> Enforced by: `linters: staticcheck`, `errcheck` (with
> `check-type-assertions: true` and `check-blank: true` for the
> strictest posture).

## 1.8 Scope and explain every `//nolint` suppression; never leave one bare.

> Why? An unscoped `//nolint` silences every linter on that line, which
> can hide a real problem introduced later by an unrelated change. A
> bare `//nolint` with no explanation also leaves the next reader unable
> to tell whether the suppression is still justified. Scope it to the
> specific linter and say why.

```go
// bad — silences every linter on this line, no explanation
key := os.Getenv("API_KEY") //nolint

// bad — scoped, but no explanation
path := filepath.Join(root, userInput) //nolint:gosec

// good — scoped to one linter, with a concrete reason
path := filepath.Join(root, userInput) //nolint:gosec // userInput is validated against an allowlist above
```

> Enforced by: `nolintlint` with `require-explanation: true`,
> `require-specific: true`, `allow-unused: false`.

## 1.9 Fix comment and string typos as part of routine review; don't let them accumulate.

> Why? Misspelled words in comments, log messages, and error strings
> undermine grep-based searches and look unpolished to anyone reading
> generated documentation. This is a cheap, entirely mechanical class of
> defect a linter can catch for you.

```go
// bad
// Cancle the pending request and release resources.
func (c *Client) Cancel() {}

// good
// Cancel the pending request and release resources.
func (c *Client) Cancel() {}
```

> Enforced by: `misspell`.

## 1.10 Never hand-edit formatting to "win" a code review nit.

> Why? Once the formatter chain has run, there is no remaining
> formatting decision to debate. Comments in review like "add a blank
> line here" or "align these" are not actionable against a formatted
> file and waste reviewer time that should go to correctness and
> design.

```go
// bad — reviewer manually re-wraps a formatted line to "look nicer"
result := computeTotal(
	items, discount,
) // hand-adjusted spacing that the formatter chain will immediately undo

// good — leave the formatter's output as-is; spend review comments on logic
result := computeTotal(items, discount)
```
