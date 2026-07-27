---
name: best-practice-go
description: Comprehensive, Airbnb-depth Go best practices for Go 1.22+ — naming, packages, errors, context, concurrency, channels, generics, testing, and modernization. Load when writing or reviewing any .go file, when the user mentions Go/Golang, Effective Go, Uber Go Style, or Google's Go Style Guide, or when the user asks "is this idiomatic Go?". Enforces the exact linter set in the user's `.golangci.yml` (bodyclose, contextcheck, copyloopvar, errcheck, errorlint, gocritic, gosec, govet, ineffassign, misspell, nilerr, nolintlint, revive, staticcheck, unconvert, unparam, unused, wastedassign, whitespace) with test-file and cmd/ relaxations. Pairs with go-style-guide for structured code audits.
---

# best-practice-go

This skill codifies modern Go best practices for Go 1.22+ code. It is
modeled on the depth and structure of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) —
numbered rules per chapter, `> Why?` rationale, and `// bad` / `// good`
examples for every rule.

The rules trace to three upstream sources, in this precedence order:

1. **[Google Go Style Guide](https://google.github.io/styleguide/go/)** —
   the [Style Guide](https://google.github.io/styleguide/go/guide), the
   [Style Decisions](https://google.github.io/styleguide/go/decisions),
   and the [Best Practices](https://google.github.io/styleguide/go/best-practices)
   documents.
2. **[Effective Go](https://go.dev/doc/effective_go)** — the language
   idioms document from the Go team.
3. **[Uber Go Style Guide](https://github.com/uber-go/guide/blob/master/style.md)** —
   only where a rule is not covered by (1) or (2) and does not contradict
   them.

All formatting concerns — indentation, alignment, import ordering, line
breaks — are owned by the `gofmt` / `gofumpt` / `goimports` chain and are
never re-litigated in prose. Chapter 1 documents the tool chain and every
subsequent chapter assumes the code has been formatted.

Every rule that maps to an enabled linter in the recommended
`.golangci.yml` (ships in this repo's root) carries an
**`> Enforced by: <linter-name>`** callout so you can trace each rule from
the guide to the CI check that catches its violations. Rules that reflect
a linter _exemption_ (e.g. staticcheck ST1003 initialism casing) are
labeled **Suggestion**, not **Violation**.

## When to use

- Writing new `.go` files or reviewing existing Go code.
- Answering "is this idiomatic?" or "does this follow the style guide?"
  for Go.
- Setting up or auditing a `.golangci.yml` for a new Go project.
- Migrating a codebase to a newer Go release (see chapter 32).
- Preparing a Go change for code review and wanting pre-review feedback.

## Scope

- Language-level Go: types, control flow, functions, methods, receivers,
  interfaces, embedding, generics.
- Runtime-adjacent conventions: errors, panics, context, concurrency,
  channels, sync primitives, goroutine lifecycle.
- Standard-library idioms: `slices`/`maps`/`cmp`, `log/slog`, `errors`,
  `time`, `strings`.
- Testing: `testing.T`, table tests, helpers, test doubles.
- Godoc and commentary conventions.
- Global state and initialization discipline.
- Performance patterns that are language- or runtime-level.
- Tooling: `gofmt`, `gofumpt`, `goimports`, `go vet`, `staticcheck`,
  `golangci-lint`, `gopls`, `govulncheck`.

## Non-goals

- **Formatting.** `gofmt` + `gofumpt` + `goimports` own indentation,
  alignment, import order, and line breaks. This skill states the chain
  in chapter 1 and moves on.
- **Framework-specific idioms.** Gin, Echo, chi, gRPC service patterns,
  Cobra CLI structure, sqlx query patterns — those live in framework
  skills.
- **Deployment or build tooling** beyond a one-time mention of
  `go build`, `go mod`, and `go test`.
- **Generated code.** `*.pb.go`, `*_string.go`, `mock_*.go`, and anything
  under `gen/` or `vendor/` follows the generator's conventions, not this
  skill's.
- **Deep performance tuning.** Chapter 31 covers language-level
  allocation and hot-path patterns; profiling and `pprof` workflows are
  out of scope.

---

## Chapters

Each chapter is a self-contained reference file with numbered rules,
`> Why?` rationale, `// bad` / `// good` code, and `> Enforced by:`
linter callouts. Files live under `references/`.

| #   | Chapter                 | File                                                                                       |
| --- | ----------------------- | ------------------------------------------------------------------------------------------ |
| 1   | Formatting              | [`references/01-formatting.md`](references/01-formatting.md)                               |
| 2   | Names                   | [`references/02-names.md`](references/02-names.md)                                         |
| 3   | Package Organization    | [`references/03-package-organization.md`](references/03-package-organization.md)           |
| 4   | Imports                 | [`references/04-imports.md`](references/04-imports.md)                                     |
| 5   | Declarations            | [`references/05-declarations.md`](references/05-declarations.md)                           |
| 6   | Types                   | [`references/06-types.md`](references/06-types.md)                                         |
| 7   | Slices, Maps, Arrays    | [`references/07-slices-maps-arrays.md`](references/07-slices-maps-arrays.md)               |
| 8   | Strings                 | [`references/08-strings.md`](references/08-strings.md)                                     |
| 9   | Constants               | [`references/09-constants.md`](references/09-constants.md)                                 |
| 10  | Control Structures      | [`references/10-control-structures.md`](references/10-control-structures.md)               |
| 11  | Functions               | [`references/11-functions.md`](references/11-functions.md)                                 |
| 12  | Options                 | [`references/12-options.md`](references/12-options.md)                                     |
| 13  | Methods & Receivers     | [`references/13-methods-and-receivers.md`](references/13-methods-and-receivers.md)         |
| 14  | Interfaces              | [`references/14-interfaces.md`](references/14-interfaces.md)                               |
| 15  | Embedding               | [`references/15-embedding.md`](references/15-embedding.md)                                 |
| 16  | Errors                  | [`references/16-errors.md`](references/16-errors.md)                                       |
| 17  | Error Handling          | [`references/17-error-handling.md`](references/17-error-handling.md)                       |
| 18  | Panic & Recover         | [`references/18-panic-and-recover.md`](references/18-panic-and-recover.md)                 |
| 19  | Context                 | [`references/19-context.md`](references/19-context.md)                                     |
| 20  | Concurrency             | [`references/20-concurrency.md`](references/20-concurrency.md)                             |
| 21  | Channels                | [`references/21-channels.md`](references/21-channels.md)                                   |
| 22  | Sync Primitives         | [`references/22-sync-primitives.md`](references/22-sync-primitives.md)                     |
| 23  | Goroutines & Lifecycle  | [`references/23-goroutines-and-lifecycle.md`](references/23-goroutines-and-lifecycle.md)   |
| 24  | Generics                | [`references/24-generics.md`](references/24-generics.md)                                   |
| 25  | Time                    | [`references/25-time.md`](references/25-time.md)                                           |
| 26  | Logging                 | [`references/26-logging.md`](references/26-logging.md)                                     |
| 27  | Testing                 | [`references/27-testing.md`](references/27-testing.md)                                     |
| 28  | Test Doubles            | [`references/28-test-doubles.md`](references/28-test-doubles.md)                           |
| 29  | Godoc & Commentary      | [`references/29-godoc-and-commentary.md`](references/29-godoc-and-commentary.md)           |
| 30  | Global State            | [`references/30-global-state.md`](references/30-global-state.md)                           |
| 31  | Performance             | [`references/31-performance.md`](references/31-performance.md)                             |
| 32  | Tooling & Modernization | [`references/32-tooling-and-modernization.md`](references/32-tooling-and-modernization.md) |
| 33  | Linter Configuration    | [`references/33-linter-configuration.md`](references/33-linter-configuration.md)           |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells
   Claude/Cursor/Windsurf when to load `best-practice-go`. When it loads,
   this index is what the agent reads first.
2. **Targeted reads.** For one specific area (say, error wrapping or
   context propagation), the agent opens only the matching chapter under
   `references/` — this keeps the context window small.
3. **Full review.** For a comprehensive audit, the agent reads every
   chapter. Each is exhaustive on its own topic with numbered rules,
   `> Why?` rationale, `// bad` / `// good` examples, and
   `> Enforced by:` linter callouts where applicable.
4. **Sibling skill.** For structured audit reports (findings grouped by
   category, `file:line` citations, severity labels), pair with
   `go-style-guide` — this skill is the source of the rules; that skill
   is the workflow for producing an audit.
5. **Linter config.** The recommended `.golangci.yml` ships in this
   repo's root and is documented in chapter 33.

## Self-check

Before treating any Go code you write or review as finished, verify:

- The file compiles under `gofmt -d`, `gofumpt`, and `goimports` with no
  diff. If not, run the formatters first — nothing else in this list
  matters if formatting is off.
- No function returns an error that a caller cannot handle — every error
  is either wrapped with `fmt.Errorf("...: %w", err)`, compared with
  `errors.Is`/`errors.As`, or explicitly discarded with a
  `//nolint:errcheck // <reason>` comment.
- Every exported identifier has a doc comment. It starts with a capital
  letter and ends with a period. (Starting-with-name is Recommended
  per the user's config, not required — see chapter 29.)
- Every `context.Context` is passed as the first argument, never stored
  in a struct, never `nil`. Every `WithCancel`/`WithTimeout`/`WithDeadline`
  cancel is deferred.
- Every goroutine has a clear owner and a defined stop condition. No
  `go func() { ... }()` fires-and-forgets. No goroutines start in
  `init()`.
- Every channel has an obvious closer (usually the sender). Every
  channel used across goroutines is either unbuffered (size 0) or
  buffered with size 1 unless there's a documented reason otherwise.
- Every `sync.Mutex`/`sync.RWMutex` is a struct field (not a pointer),
  and no struct containing one is copied.
- Every table-driven test uses `t.Run` subtests and calls
  `t.Parallel()` at both levels where safe. Every test helper calls
  `t.Helper()`.
- The code compiles cleanly under the project's `.golangci.yml` (see
  chapter 33). No new `//nolint` directives added without a scoped
  linter name and an explanation.
- If the file is under `cmd/`, `init()` may be used for flag
  registration and framework hooks. Everywhere else it is not.
- If the file is a `_test.go`, the relaxed linter set applies — see
  chapter 27.12.
