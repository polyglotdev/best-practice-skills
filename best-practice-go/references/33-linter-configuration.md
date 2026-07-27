<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 33. Linter Configuration

Every chapter in this guide assumes a specific, enforced linter baseline —
this chapter documents that baseline so the rest of the guide's `Enforced
by:` callouts point at something concrete. The configuration below is the
project's actual `.golangci.yml`: a `golangci-lint` v2 setup covering
`bodyclose`, `contextcheck`, `copyloopvar`, `errcheck`, `errorlint`,
`gocritic`, `gosec`, `govet`, `ineffassign`, `misspell`, `nilerr`,
`nolintlint`, `revive`, `staticcheck`, `unconvert`, `unparam`, `unused`,
`wastedassign`, and `whitespace`, formatted by `gofmt` + `gofumpt` +
`goimports`. Where this configuration exempts a pattern this guide would
otherwise treat as a hard Violation, the relevant chapter says so
explicitly (see [Chapter 23.13](23-goroutines-and-lifecycle.md), [Chapter
27.12](27-testing.md), [Chapter 28.9](28-test-doubles.md), [Chapter
29.1–29.2, 29.10](29-godoc-and-commentary.md), [Chapter
30.3–30.4](30-global-state.md), and [Chapter 31.8](31-performance.md)).

## 33.1 Use `golangci-lint` v2 as the single lint runner.

> Why? Running individual linters separately (`go vet`, `staticcheck`,
> `errcheck` as standalone binaries) means maintaining separate
> invocations, separate exclusion rules, and separate CI steps.
> `golangci-lint` v2 runs all configured linters in one pass, applies a
> single exclusion and severity model, and is what this project's
> `version: '2'` config targets.

```go
// bad — separate tool invocations, no shared configuration
// (CI config)
// steps:
//	- run: go vet ./...
//	- run: staticcheck ./...
//	- run: errcheck ./...

// good — one runner, one config file, one CI step
// (CI config)
// steps:
//	- run: golangci-lint run
```

Minimal invocation once `.golangci.yml` exists at the repository root:

```bash
golangci-lint run ./...
```

## 33.2 Enable this linter set at minimum.

> Why? Each linter below catches a distinct class of bug or style
> deviation that `gofmt` and the compiler cannot. This is the enabled set
> in the project's `linters.enable` list, each mapped to the chapter that
> teaches its underlying rule.

- **bodyclose** — flags an `http.Response.Body` that is never closed on
  some code path ([Chapter 23.13](23-goroutines-and-lifecycle.md)).
- **contextcheck** — flags `context.Background()`/`context.TODO()` used
  where a `ctx` is already in scope and should be threaded through.
- **copyloopvar** — flags now-unnecessary manual loop-variable copies
  left over from pre-Go-1.22 code ([Chapter
  32.1](32-tooling-and-modernization.md), [Chapter 27.2](27-testing.md)).
- **errcheck** — flags discarded error return values, with
  `check-type-assertions: true` and `check-blank: true` for stricter
  coverage; exempts `(io.Closer).Close` and
  `(net/http.ResponseWriter).Write` ([Chapter
  23.13](23-goroutines-and-lifecycle.md)).
- **errorlint** — flags `%v` where `%w` should wrap an error, type
  assertions where `errors.As` should be used, and `==` comparisons where
  `errors.Is` should be used.
- **gocritic** — a broad diagnostic/performance/style analyzer; this
  project enables those three tags but disables `ifElseChain`,
  `hugeParam`, `rangeValCopy`, and `paramTypeCombine` ([Chapter
  33.10](33-linter-configuration.md)).
- **gosec** — flags common security issues (SQL injection shape,
  hardcoded credentials, weak crypto); this project excludes G104, G304,
  and G404, and exempts the `G115:` text ([Chapter
  33.9](33-linter-configuration.md)).
- **govet** — the standard Go vet analyzers, enabled in full except
  `fieldalignment` and `shadow` ([Chapter 33.11](33-linter-configuration.md)).
- **ineffassign** — flags assignments whose value is never read before
  being overwritten or the variable goes out of scope.
- **misspell** — flags common misspellings in comments and string
  literals ([Chapter 26.11](26-logging.md)).
- **nilerr** — flags `if err != nil { return nil }`, where a non-nil
  error is checked but a nil error is returned anyway.
- **nolintlint** — flags `//nolint` directives that are unscoped or
  unexplained ([Chapter 33.4](33-linter-configuration.md)).
- **revive** — a configurable style linter; this project enables a
  specific rule list detailed in [Chapter 33.2](33-linter-configuration.md)'s
  table below.
- **staticcheck** — the broad `staticcheck` correctness and style
  analyzer, enabled in full except ST1000, ST1003, ST1020, ST1021, and
  ST1022 ([Chapter 33.8](33-linter-configuration.md)).
- **unconvert** — flags redundant type conversions where the value is
  already the target type.
- **unparam** — flags unused function parameters in unexported functions
  (`check-exported: false` exempts exported functions).
- **unused** — flags dead code: unused variables, functions, types, and
  constants ([Chapter 30.8](30-global-state.md)).
- **wastedassign** — flags an assignment that is overwritten before ever
  being read.
- **whitespace** — flags leading/trailing whitespace inside function
  bodies and blocks.

The enabled `revive` rules map to specific chapters:

| revive rule | Chapter |
|---|---|
| blank-imports | 4 (imports) |
| context-as-argument | 19 (context) |
| context-keys-type | 19 (context) |
| dot-imports | 4 (imports), exempted in `_test.go` ([28.9](28-test-doubles.md)) |
| error-return | 16 (errors) |
| error-strings | 17 (error handling) |
| error-naming | 16 (errors) |
| exported (disableStutteringCheck) | 3 (packages), 29 (godoc) |
| if-return | 10 (control flow) |
| increment-decrement | 10 (control flow) |
| indent-error-flow | 10 (control flow) |
| range | 10 (control flow) |
| receiver-naming | 13 (methods) |
| redefines-builtin-id | 2 (names), 9 (constants) |
| superfluous-else | 10 (control flow) |
| time-naming | 25 (time) |
| unreachable-code | 10 (control flow) |
| unused-parameter | 11 (functions) |
| var-declaration | 5 (declarations) |
| var-naming | 2 (names) |

## 33.3 Chain three formatters — `gofmt`, `gofumpt`, `goimports`.

> Why? `gofmt` is the non-negotiable baseline (see [Chapter
> 1](01-formatting.md)). `gofumpt` enforces a stricter superset —
> disallowing things like a leading empty line inside a block or a
> multi-line composite literal with one field per line only inconsistently
> applied — that `gofmt` alone accepts. `goimports` additionally groups
> and sorts imports by category. Running all three keeps formatting
> fully automated with no remaining manual decisions.

```yaml
formatters:
  enable:
    - gofmt
    - gofumpt
    - goimports
  settings:
    gofumpt:
      module-path: platform-backend
      extra-rules: true
    goimports:
      local-prefixes:
        - platform-backend
```

With `local-prefixes` set, `goimports` groups imports into three blocks —
standard library, third-party, and anything under the `platform-backend`
module path — not a fourth block for "same package" imports.

## 33.4 Every `//nolint` must be scoped and explained.

> Why? An unscoped `//nolint` silences every linter on that line, which
> can hide a genuinely new problem introduced later on the same line. An
> unexplained one gives the next reader no way to judge whether the
> suppression is still justified. The project's `nolintlint` settings —
> `require-explanation: true`, `require-specific: true`,
> `allow-unused: false` — enforce both requirements and additionally flag
> a `//nolint` that no longer suppresses anything (meaning it can be
> deleted).

> Enforced by: nolintlint

```go
// bad — unscoped, unexplained; nolintlint rejects this
func readSecret(path string) []byte { //nolint
	data, _ := os.ReadFile(path)
	return data
}

// good — scoped to the specific linter, with a reason
func readSecret(path string) []byte {
	//nolint:gosec // path is validated by validateConfigPath before this call
	data, _ := os.ReadFile(path)
	return data
}
```

## 33.5 Test files (`_test.go`) relax `bodyclose`, `errcheck`, `errorlint`, `gosec`, `revive`, and `unparam`.

> Why? The project's `.golangci.yml` disables these six linters
> specifically for paths matching `_test\.go`. Test code has different
> risk and readability tradeoffs than production code — a failed setup
> helper surfaces as an obviously failing test regardless of whether its
> error is explicitly checked, and DSL-style test libraries rely on
> patterns these linters would otherwise flag. See [Chapter
> 27.12](27-testing.md) and [Chapter 28.9](28-test-doubles.md) for the
> full rules this backs.

Concretely, inside `_test.go`:

```go
// good — errcheck relaxed: a failed setup helper will fail the test anyway
func TestHandler(t *testing.T) {
	srv, _ := newTestServer()
	defer srv.Close()
	// ...
}

// good — bodyclose relaxed, though closing is still good practice
resp, _ := http.Get(srv.URL)
_ = resp.Body // not closed; won't fail lint in _test.go

// good — revive's dot-imports relaxed for assertion DSLs
import (
	. "github.com/onsi/gomega"
)

// good — gosec's math/rand warning relaxed: no crypto/rand needed for jitter in tests
delay := time.Duration(rand.Intn(100)) * time.Millisecond

// good — unparam relaxed: a test helper's unused parameter can stay
// for signature symmetry across table-driven cases
func newFixture(t *testing.T, _ bool) *Fixture {
	return &Fixture{}
}
```

Outside `_test.go`, all six linters are fully enforced — do not treat this
relaxation as a codebase-wide license.

## 33.6 `cmd/**` binaries may use `init()` for flag registration.

> Why? The project's `.golangci.yml` excludes `cmd/**` paths from
> `gochecknoinits` — even though `gochecknoinits` itself is not in the
> `enable` list, this exclusion rule signals the project's intended
> policy: `init()` is acceptable in `cmd/`-level `main` packages for CLI
> flag registration and framework entry hooks (`flag.Var`,
> `cobra.OnInitialize`), and should be avoided everywhere else. See
> [Chapter 30.3–30.4](30-global-state.md) for the full rule and rationale.

```yaml
rules:
  - path: cmd/
    linters:
      - gochecknoinits
```

## 33.7 The intentional-err-shadow pattern is permitted.

> Why? The project's `govet` settings disable the `shadow` analyzer
> specifically for `'shadow: declaration of "err"'`, which means the
> common Go idiom of scoping a fresh `err` to an `if` statement — even
> when an outer `err` variable already exists in the enclosing scope — is
> not flagged. This is a deliberate exemption for a pattern that is
> idiomatic and safe, not an invitation to shadow other variables freely.

> Enforced by: govet `shadow` is disabled for this specific text pattern

```go
// good — the inner err is intentionally scoped to this if statement,
// even though an outer err already exists in Process's scope
func Process(id string) (err error) {
	rec, err := lookup(id)
	if err != nil {
		return fmt.Errorf("lookup: %w", err)
	}

	if err := rec.Validate(); err != nil {
		return fmt.Errorf("validate: %w", err)
	}

	return nil
}
```

## 33.8 The following `staticcheck` checks are exempt: ST1000, ST1003, ST1020, ST1021, ST1022.

> Why? The project's `staticcheck.checks` list is `all` minus these five
> IDs. Each is a documentation- or naming-convention check that this
> guide still recommends as a Suggestion (see the cross-referenced
> chapters), but none of them fail CI in this configuration.

- **ST1000** — requires a package doc comment. Recommended in [Chapter
  29.2](29-godoc-and-commentary.md) as a Suggestion.
- **ST1003** — flags poorly cased identifiers, including initialism
  casing (`getUrl` vs. `getURL`). Recommended in [Chapter
  29.10](29-godoc-and-commentary.md) as a Suggestion.
- **ST1020** — requires an exported function's doc comment to start with
  the function's name. Recommended in [Chapter
  29.1](29-godoc-and-commentary.md) as a Suggestion.
- **ST1021** — requires an exported type's doc comment to start with the
  type's name. Same rule family as ST1020, same Suggestion status.
- **ST1022** — requires an exported var/const's doc comment to start with
  its name. Same rule family, same Suggestion status.

Everything else in `staticcheck` — including correctness checks like
`SA` (staticcheck analysis) diagnostics — remains fully enforced.

## 33.9 `gosec` exemptions: G104, G304, G404 (and the G115 text).

> Why? Each exemption below removes a specific `gosec` rule ID that would
> otherwise produce noisy or duplicate findings, while this guide still
> teaches the underlying positive pattern.

- **G104** (unhandled errors) — excluded because `errcheck` already
  covers unhandled errors more precisely; a separate `gosec` finding for
  the same thing would be a duplicate. Continue checking errors per
  [Chapter 16](16-errors.md).
- **G304** (file path provided by a variable) — excluded so that
  `os.Open(path)` with a parameterized `path` doesn't flag on every call.
  Still validate untrusted paths — join against a fixed root directory
  and call `filepath.Clean` — as a Suggestion, not because `gosec`
  requires it here.
- **G404** (`math/rand` used where `gosec` assumes cryptographic
  randomness is needed) — excluded so that `math/rand` is not flagged for
  legitimate non-cryptographic uses like jitter or backoff delay.
  Continue to use `crypto/rand` for anything security-sensitive (tokens,
  keys, nonces) as a matter of correctness, not because `gosec` enforces
  it.
- **G115** (integer conversion overflow, e.g. `int` → `int32`) — the
  project exempts the `G115:` text specifically. Overflow risk on
  narrowing integer conversions is still worth a second look in review,
  but it is a Suggestion here, not a blocking Violation.

```go
// acceptable under this project's gosec config — G304 not flagged
func readUserFile(path string) ([]byte, error) {
	return os.ReadFile(path)
}

// good — still validated as a matter of correctness, not lint compliance
func readUserFile(baseDir, name string) ([]byte, error) {
	path := filepath.Join(baseDir, filepath.Clean(name))
	if !strings.HasPrefix(path, baseDir) {
		return nil, fmt.Errorf("invalid file name %q", name)
	}
	return os.ReadFile(path)
}
```

## 33.10 `gocritic` disabled checks: `ifElseChain`, `hugeParam`, `rangeValCopy`, `paramTypeCombine`.

> Why? These four `gocritic` checks are explicitly disabled in
> `gocritic.disabled-checks`. Do not raise their underlying patterns as
> blocking issues in code review, since the project's own lint
> configuration has already decided not to enforce them.

- **ifElseChain** — would suggest converting long `if`/`else if` chains
  to a `switch`. Disabled; either form is acceptable here.
- **hugeParam** — would flag large structs passed by value as function
  parameters. Disabled; see [Chapter 31.8](31-performance.md) for the
  Suggestion-level guidance this guide still offers.
- **rangeValCopy** — would flag a `for _, v := range largeStructSlice`
  loop that copies each large element. Disabled for the same reason as
  `hugeParam`; raise only when a profile shows it matters.
- **paramTypeCombine** — would suggest combining adjacent parameters of
  the same type (`func f(a, b int)` vs. `func f(a int, b int)`). Disabled;
  both forms are acceptable.

## 33.11 `govet` disabled: `fieldalignment`, `shadow`.

> Why? The project enables `govet` with `enable-all: true` but disables
> two specific analyzers.

- **fieldalignment** — would flag struct field ordering that wastes
  memory to padding. Disabled; this guide does not teach manual field
  reordering for alignment as a rule (see the absence of any such rule in
  [Chapter 5](05-declarations.md) — this is intentional).
- **shadow** — would flag variable shadowing generally, but the project
  further narrows this by only suppressing the specific `'shadow:
  declaration of "err"'` text (see rule 33.7); shadowing of other
  variable names is generally still worth catching in review even though
  the analyzer itself is off.

## 33.12 Ship the config.

> Why? A concrete, working `.golangci.yml` is more useful as a starting
> point than a description of one. This is the exact configuration this
> chapter — and every `Enforced by:` callout in this guide — is written
> against. Individual repositories should trim linters or settings that
> don't fit their own risk profile, but should change the baseline
> deliberately rather than by accident.

```yaml
version: '2'

run:
  timeout: 5m
  tests: true
  modules-download-mode: readonly
  allow-parallel-runners: true

linters:
  default: none
  enable:
    - bodyclose
    - contextcheck
    - copyloopvar
    - errcheck
    - errorlint
    - gocritic
    - gosec
    - govet
    - ineffassign
    - misspell
    - nilerr
    - nolintlint
    - revive
    - staticcheck
    - unconvert
    - unparam
    - unused
    - wastedassign
    - whitespace
  settings:
    errcheck:
      check-type-assertions: true
      check-blank: true
      exclude-functions:
        - (io.Closer).Close
        - (net/http.ResponseWriter).Write
    errorlint:
      errorf: true
      asserts: true
      comparison: true
    gocritic:
      enabled-tags:
        - diagnostic
        - performance
        - style
      disabled-checks:
        - ifElseChain
        - hugeParam
        - rangeValCopy
        - paramTypeCombine
    gosec:
      excludes:
        - G104
        - G304
        - G404
    govet:
      enable-all: true
      disable:
        - fieldalignment
        - shadow
    nolintlint:
      require-explanation: true
      require-specific: true
      allow-unused: false
    revive:
      severity: warning
      rules:
        - name: blank-imports
        - name: context-as-argument
        - name: context-keys-type
        - name: dot-imports
        - name: error-return
        - name: error-strings
        - name: error-naming
        - name: exported
          arguments:
            - disableStutteringCheck
        - name: if-return
        - name: increment-decrement
        - name: indent-error-flow
        - name: range
        - name: receiver-naming
        - name: redefines-builtin-id
        - name: superfluous-else
        - name: time-naming
        - name: unreachable-code
        - name: unused-parameter
        - name: var-declaration
        - name: var-naming
    staticcheck:
      checks:
        - all
        - '-ST1000'
        - '-ST1003'
        - '-ST1020'
        - '-ST1021'
        - '-ST1022'
    unparam:
      check-exported: false
  exclusions:
    generated: lax
    presets:
      - comments
      - common-false-positives
      - legacy
      - std-error-handling
    paths:
      - third_party$
      - builtin$
      - examples$
      - vendor$
      - .*\.pb\.go$
      - .*_mock\.go$
      - mocks/.*
    rules:
      - path: _test\.go
        linters:
          - bodyclose
          - errcheck
          - errorlint
          - gosec
          - revive
          - unparam
      - path: cmd/
        linters:
          - gochecknoinits
      - text: 'shadow: declaration of "err"'
        linters:
          - govet
      - text: 'G115:'
        linters:
          - gosec

formatters:
  enable:
    - gofmt
    - gofumpt
    - goimports
  settings:
    gofumpt:
      module-path: platform-backend
      extra-rules: true
    goimports:
      local-prefixes:
        - platform-backend
  exclusions:
    generated: lax
    paths:
      - third_party$
      - builtin$
      - examples$
      - vendor$
      - .*\.pb\.go$

issues:
  max-issues-per-linter: 0
  max-same-issues: 0

output:
  formats:
    text:
      path: stdout
      print-linter-name: true
      print-issued-lines: true
  sort-order:
    - file
    - linter
```
