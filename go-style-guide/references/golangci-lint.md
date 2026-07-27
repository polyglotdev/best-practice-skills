# golangci-lint — how this repo's configured linters map to the audit

This file is the bridge between the [Google Go Style Guide](https://google.github.io/styleguide/go/guide)-derived audit rules in every other file in this directory and the actual, running `golangci-lint` configuration in this repository (`/home/user/workspace/go-skills-build/.golangci.yml`, documented in `/home/user/workspace/go-skills-build/GOLANGCI_LINT_CONFIG.md`). The governing principle: **what the linter flags is a Violation in this audit; what the linter explicitly exempts is downgraded to a Suggestion (or omitted entirely).** Every other reference file in this directory has already been retrofitted against this mapping — this file exists so the mapping itself is documented in one place instead of scattered as inline `**Enforced by:**` lines.

## Linter-to-rule map

| Linter | What it catches | Audit category |
|---|---|---|
| `bodyclose` | `http.Response.Body` not closed on some code path | [concurrency.md](concurrency.md#always-close-httpresponsebody) — cleanup/leak prevention |
| `contextcheck` | A non-inherited `context.Context` used where an in-scope `ctx` should have been passed through (e.g. `context.Background()` called inside a function that already has `ctx`) | [context.md](context.md#contextbackground-contexttodo-only-when-no-context-is-already-in-scope) |
| `copyloopvar` | Go 1.22+ loop-variable-capture correctness: missing per-iteration copy on pre-1.22 semantics, or unnecessary copy lines once 1.22+ semantics apply | [concurrency.md](concurrency.md#go-122-loop-variable-semantics-and-copyloopvar) |
| `errcheck` | Discarded/unchecked error return values, including type assertions (`check-type-assertions: true`) and blank-assigned errors (`check-blank: true`) | [error-handling.md](error-handling.md) |
| `errorlint` | Non-wrapping `fmt.Errorf` (missing `%w`), unsafe type assertions on errors, `==` comparisons against sentinel errors instead of `errors.Is` | [error-handling.md](error-handling.md) |
| `gocritic` | Style, diagnostic, and performance heuristics (enabled tags: `diagnostic`, `performance`, `style`) | miscellaneous — spread across [function-design.md](function-design.md), [variable-declarations.md](variable-declarations.md), [tooling-and-modernization.md](tooling-and-modernization.md) depending on the specific check |
| `gosec` | Security-sensitive patterns (unsafe integer conversions, path traversal, weak randomness, etc., excluding G104/G304/G404 — see exemptions below) | security — cross-cutting, most visibly in [variable-declarations.md](variable-declarations.md#integer-conversions-and-overflow-risk) |
| `govet` | Broad static-analysis suite (`enable-all: true`), including `copylocks` (mutex copying), `lostcancel` (uncalled context cancel funcs), and more, with `fieldalignment` and `shadow` disabled repo-wide | varies — [concurrency.md](concurrency.md#zero-value-mutexes-are-valid-but-must-never-be-copied) for `copylocks`, [context.md](context.md#always-call-cancel) for `lostcancel` |
| `ineffassign` | A value assigned to a variable but never subsequently used before being overwritten or going out of scope | [variable-declarations.md](variable-declarations.md#no-assignments-that-are-never-read) |
| `misspell` | Misspelled English words in comments and string literals | [documentation.md](documentation.md#spelling-in-comments-and-strings) |
| `nilerr` | A function that checks `err != nil` but returns `nil` anyway (swallowing the error) | [error-handling.md](error-handling.md#no-if-err-nil-return-nil-dont-swallow-errors-as-success) |
| `nolintlint` | `//nolint` suppressions missing a specific linter name or an explanation | [tooling-and-modernization.md](tooling-and-modernization.md#nolint-suppressions-must-be-specific-and-explained) |
| `revive` | Configurable style rules (see the specific `rules:` list below) — blank/dot imports, context argument conventions, error naming/wrapping conventions, receiver naming, var naming, and more | varies — [naming.md](naming.md), [imports.md](imports.md), [context.md](context.md), [error-handling.md](error-handling.md) |
| `staticcheck` | The `staticcheck` analysis suite (`checks: all` minus the `ST1000`/`ST1003`/`ST1020`/`ST1021`/`ST1022` exemptions below) | varies — [documentation.md](documentation.md), [naming.md](naming.md) |
| `unconvert` | Unnecessary explicit type conversions where the source and target types already match | [variable-declarations.md](variable-declarations.md#no-unnecessary-type-conversions) |
| `unparam` | Function parameters that are never used, or always called with the same constant value (`check-exported: false`, so exported functions are exempt) | [function-design.md](function-design.md) |
| `unused` | Unexported functions, types, constants, variables, and struct fields that are never referenced | [variable-declarations.md](variable-declarations.md), [tooling-and-modernization.md](tooling-and-modernization.md#unused-no-dead-code-left-behind) |
| `wastedassign` | An assignment whose value is overwritten before ever being read (a stricter sibling of `ineffassign`) | [variable-declarations.md](variable-declarations.md#no-assignments-that-are-never-read) |
| `whitespace` | Unnecessary leading/trailing blank lines inside blocks | formatting — auto-fixable, not treated as a standalone audit rule anywhere in this directory |

## Rules the user exempts (map to Suggestion, not Violation)

This repo's `.golangci.yml` deliberately disables or excludes specific checks that upstream style guides otherwise treat as strict rules. Per this audit's governing principle, every rule below is downgraded from Violation to **Suggestion** in its home reference file, with the exemption noted inline:

| Exemption | What it normally catches | Where it's downgraded |
|---|---|---|
| `staticcheck` `-ST1000` | Missing or malformed package doc comment | [documentation.md](documentation.md#package-doc-comment-requirement) — Suggestion |
| `staticcheck` `-ST1003` | Non-standard initialism casing (`Url` instead of `URL`, `Id` instead of `ID`) | [naming.md](naming.md#initialisms-keep-consistent-case-url-id-http-not-url-id-http) — Suggestion |
| `staticcheck` `-ST1020` / `-ST1021` / `-ST1022` | Doc comments on exported functions/types/vars not starting with the identifier's name | [documentation.md](documentation.md#godoc-for-exported-identifiers-must-start-with-the-identifier-name) — Suggestion |
| `revive` `exported` rule with `disableStutteringCheck` argument | "Stuttering" names (`partner.PartnerID` repeating the package name) | [naming.md](naming.md#dont-repeat-the-package-name-in-exported-identifiers) and [naming.md](naming.md#package-names-avoid-utilcommonhelpermisc-and-avoid-stuttering) (cross-referenced from [packages.md](packages.md#no-utilcommonmisc-packages)) — Suggestion |
| `gosec` `G104` | Unchecked error return (broad, largely superseded by `errcheck`'s more precise coverage in this config) | not separately tracked — `errcheck` remains a Violation in [error-handling.md](error-handling.md) |
| `gosec` `G115` | Potentially unsafe integer conversion that could overflow (int64→int32, etc.) | [variable-declarations.md](variable-declarations.md#integer-conversions-and-overflow-risk) — Suggestion; also excluded via the `text: 'G115:'` issue rule |
| `gosec` `G304` | File path provided by a variable rather than a literal (potential path traversal) | not separately tracked as an audit rule in this directory — excluded repo-wide |
| `gosec` `G404` | Use of `math/rand` instead of `crypto/rand` | not separately tracked as an audit rule in this directory — excluded repo-wide |
| `gocritic` `ifElseChain` | Long `if`/`else if` chains that could be a `switch` | not separately tracked as a Violation anywhere in this directory |
| `gocritic` `hugeParam` | Large structs passed by value instead of by pointer | [function-design.md](function-design.md#use-an-option-struct-when-the-function-has-many-parameters) — Suggestion |
| `gocritic` `rangeValCopy` | Large struct copied as the loop variable in a `for range` | [function-design.md](function-design.md#use-an-option-struct-when-the-function-has-many-parameters) — Suggestion, same rule as `hugeParam` |
| `gocritic` `paramTypeCombine` | Adjacent same-typed parameters not combined (`a, b int` vs `a int, b int`) | not separately tracked as an audit rule in this directory |
| `govet` `fieldalignment` | Struct fields orderable to reduce memory padding | not separately tracked as a Violation anywhere in this directory — this repo prioritizes field grouping by meaning over byte-packing (see [variable-declarations.md](variable-declarations.md)) |
| `govet` `shadow` | Any shadowed variable, including `err` | [error-handling.md](error-handling.md#intentional-err-shadowing-inside-an-if-is-not-a-bug) — the `err`-shadow case is explicitly a non-issue in this repo (see the `text: 'shadow: declaration of "err"'` issue-exclusion rule below); shadowing that escapes its intended scope is still a Violation, just not detected by this disabled analysis |

## Test-file relaxations

This repo's `.golangci.yml` disables six linters specifically inside `_test.go` files via an `issues.exclusions.rules` path match on `_test\.go`:

```yaml
- path: _test\.go
  linters:
    - bodyclose
    - errcheck
    - errorlint
    - gosec
    - revive
    - unparam
```

The full rationale for each is documented in [testing.md](testing.md#test-file-linter-relaxations); summarized here:

| Linter | Why it's relaxed in tests |
|---|---|
| `bodyclose` | Test HTTP responses against `httptest` servers are frequently short-lived and inspected without the same leak risk as production code |
| `errcheck` | Test setup/teardown routinely discards errors from calls (`os.Remove`, `f.Close()`) whose failure isn't relevant to the test's assertion |
| `errorlint` | Table-driven tests often compare errors directly for simplicity where production code would need `errors.Is` |
| `gosec` | Test fixtures commonly include intentionally "insecure" patterns (hardcoded credentials, `math/rand` for deterministic-looking test data) that are fine in a non-production context |
| `revive` | Enables dot-imports for DSL-style test assertion libraries (e.g. Gomega) — see [imports.md](imports.md#no-dot-imports-outside-tests) |
| `unparam` | Table-driven test helpers often have parameters that are only exercised by a subset of table rows, which `unparam` would otherwise flag as effectively constant |

This repo's config additionally exempts `cmd/` packages from `gochecknoinits` (a linter not in this repo's enabled list, but referenced by the path rule) — the audit's own version of this exemption is documented in [packages.md](packages.md#init-is-avoided-everywhere-except-cmd-flag-registration).

## Format chain

Formatting is never re-litigated by hand in this audit (see [SOURCES.md](../../../SOURCES.md)) — it's entirely the responsibility of the configured formatter chain, run in this order:

1. **`gofmt`** — baseline Go formatting (tabs, brace placement, spacing).
2. **`gofumpt --extra-rules`** (`module-path: platform-backend`) — a stricter superset of `gofmt` that also enforces things like no empty lines at the start/end of a block, forced use of `%w` grouping in some cases, and simplification rules `gofmt` doesn't cover.
3. **`goimports -local platform-backend`** — import grouping and sorting, treating `platform-backend/...` as the module-local group (see [imports.md](imports.md#three-import-groups-standard-library-third-party-module-local)).

Any diff between a file's current state and what this chain produces is a Suggestion at most, and should be pointed at the exact command to run rather than manually reformatted in review.

## `//nolint` policy

This repo requires every `//nolint` suppression to (a) name the specific linter being suppressed, and (b) include an explanation, enforced by `nolintlint` with `require-explanation: true`, `require-specific: true`, and `allow-unused: false`. See [tooling-and-modernization.md](tooling-and-modernization.md#nolint-suppressions-must-be-specific-and-explained) for the full rule, examples, and severity. `allow-unused: false` additionally means a suppression that no longer matches any actual finding (because the underlying issue was fixed) is itself flagged — stale suppressions don't accumulate silently.

## Full `.golangci.yml` (verbatim)

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
