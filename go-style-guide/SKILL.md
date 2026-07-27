---
name: go-style-guide
description: Use when auditing existing Go code against Google's Go Style Guide (https://google.github.io/styleguide/go/), Effective Go, Uber's Go Style Guide, and the user's `.golangci.yml`. Trigger on "audit this Go file/package", "is this idiomatic Go", "Go code review", or when the user mentions any of the source guides. Produces a structured findings report grouped by category with file:line citations. Do NOT use to write new Go code — load `best-practice-go` for that.
---

# Evaluate Go code against Google's Go Style Guide

This skill audits Go source files, packages, or whole codebases against the rules in Google's Go Style Guide, Effective Go, Uber's Go Style Guide, and the user's `.golangci.yml`. It produces a structured report grouped by category (Naming, Package Organization, Imports, Function Design, Error Handling, Documentation, Variable Declarations, Concurrency, Context, Generics, Tooling & Modernization, Testing) with file:line references and concrete suggested fixes. Findings that are enforced by an enabled linter in `.golangci.yml` are labeled **Violation**; those the linter exempts (e.g. staticcheck ST1003, ST1020-1022) are labeled **Suggestion**.

The goal is to give the user something they can act on, not just a list of issues. Every finding includes the rule it violates, why it matters, and what to change.

## When to invoke this skill

- The user explicitly asks for a Go code review, Go style audit, or Google best-practice check.
- The user asks "is this idiomatic", "does this follow Go conventions", or similar.
- The user has just finished writing a substantial Go function, file, or package and wants feedback.
- The user mentions Google's Go style guide or links the URL.
- The user is preparing a Go change for review and wants pre-review feedback.

Do not invoke for: non-Go languages, formatting questions answered by `gofmt`/`goimports` (those are deterministic — let the tools handle them), or pure performance tuning (use a Go profiling/benchmarking workflow for that).

## Workflow

### 1. Identify scope

Before reading any code, confirm what's being audited. Ask the user once if unclear:

- A single file? — read it in full.
- A package? — read every `.go` file in that directory (skip generated files like `*.pb.go`, `*_string.go`, `mock_*.go`).
- A whole module? — list the directories, prioritise the ones with hand-written code (skip `gen/`, `vendor/`, `mocks/`, `*_test.go` get separate treatment under the Testing category).

Read generated files only when the user explicitly asks. Skim third-party `vendor/` only if the question is about how the codebase consumes them, not their internals.

### 2. Decide which reference files to load

Each category has a detailed checklist in `references/`. Load only the ones relevant to the code in scope. For example:

- Code with several functions and methods → load `references/naming.md` and `references/function-design.md`.
- Code that handles errors or wraps them → load `references/error-handling.md`.
- Code with goroutines, channels, mutexes → load `references/concurrency.md`.
- Code that threads `context.Context` → load `references/context.md`.
- Code with `import` groups or blank imports → load `references/imports.md`.
- Code using type parameters or `slices`/`maps`/`cmp` → load `references/generics.md`.
- Test files (`*_test.go`) → load `references/testing.md`.
- Package-level audit → load `references/packages.md` and `references/documentation.md`.
- Modernization pass (Go 1.22+) → load `references/tooling-and-modernization.md`.
- Mapping findings back to CI → load `references/golangci-lint.md`.

When in doubt, load multiple references — context is cheap compared to missing a real issue.

### 3. Walk the code against each rule

For each rule in the loaded references, check the code. Some rules are mechanical (e.g., "function returns a value and starts with `Get`" — grep for it). Others need judgement (e.g., "is this error annotation redundant" — read the wrapped error and the new context).

When grepping helps, use `grep` / `rg` via Bash to find candidate violations across files quickly, then read each candidate in context before flagging.

### 4. Compile findings into the structured report

Use the report template in the "Output format" section below. Group findings by category, sort within each category from highest to lowest severity. For each finding:

- Cite the specific rule and link to the relevant section of `https://google.github.io/styleguide/go/best-practices`.
- Give the `file:line` reference using markdown links so the user can click through.
- Show the offending code in a small fenced block (1–5 lines), then show the suggested fix in a second fenced block.
- Briefly explain the *why* — "this violates X because Y" — not just "this violates X." Theory of mind matters; the user is more likely to internalize the rule if they understand it.

### 5. Honest scope and confidence

The Go style guide is opinionated, and some rules are judgement calls. When a finding is judgement-based (e.g., "this package name feels generic"), say so — call it `Suggestion` rather than `Violation`. Reserve `Violation` for clear breaches (e.g., `Get` prefix on a value-returning function, panic escaping a public API, error string-match).

If the code is mostly fine, say so plainly. A short report that says "this file follows the guide well; one minor naming suggestion" is more useful than a padded list of low-confidence nits.

## Output format

Use this exact template:

```markdown
# Go best-practice audit: <scope>

**Scope reviewed:** <files or packages>
**Source rules:** https://google.github.io/styleguide/go/best-practices

## Summary

- **Violations:** <N>
- **Suggestions:** <N>
- **Overall:** <one-sentence honest assessment>

## Findings

### Naming
<violations and suggestions, or "No issues found.">

### Package organization
<violations and suggestions, or "No issues found.">

### Imports
<violations and suggestions, or "No issues found.">

### Function design (arguments, options, signatures)
<violations and suggestions, or "No issues found.">

### Error handling
<violations and suggestions, or "No issues found.">

### Context
<violations and suggestions, or "No issues found.">

### Concurrency
<violations and suggestions, or "No issues found.">

### Generics
<violations and suggestions, or "No issues found.">

### Documentation
<violations and suggestions, or "No issues found.">

### Variable declarations
<violations and suggestions, or "No issues found.">

### Testing
<violations and suggestions, or "No issues found.">

### Tooling & modernization
<violations and suggestions, or "No issues found.">

## Recommended next steps

<1–3 specific actions the user should take, ranked by impact>
```

Each finding within a category looks like:

```markdown
**Violation: <short rule name>** — [path/to/file.go:42](path/to/file.go:42)

> The current code:
> ```go
> func (c *Config) GetJobName(key string) string { ... }
> ```
>
> Should become:
> ```go
> func (c *Config) JobName(key string) string { ... }
> ```
>
> Why: Google's guide says functions that return a value use noun-like names without a `Get` prefix. The `Get` prefix is a Java/C++ idiom that adds visual noise without conveying information; in Go the value-returning shape is conventional. ([reference](https://google.github.io/styleguide/go/best-practices#naming))
```

## Severity calibration

- **Violation** — A clear rule breach the guide names explicitly with a do/don't example. Examples: `Get` prefix on a value-returning function, `panic` escaping a public API boundary, string-match on `err.Error()`, `t.Fatal` from a goroutine in a test.
- **Suggestion** — A guideline that the code is on the wrong side of but where reasonable people disagree, or where the rule is context-sensitive. Examples: a package named `util` (often bad, sometimes defensible), preallocation choices, whether to use Option-struct vs variadic-options.

Use both labels honestly. A list of 30 violations where 25 should be suggestions trains the user to ignore the report.

## Anti-patterns to avoid in your own report

- Do not flag rules that are owned by `gofmt`/`goimports` (alignment, import grouping order, etc.). Those are deterministic; the user runs the tool. Mention "run `goimports -w`" once at the bottom if you see obvious formatting drift, no more.
- Do not invent rules. Every finding ties back to a specific section of the linked guide.
- Do not flag generated code (`*.pb.go`, `*_connect.go`, `*_string.go`, `mock_*.go`, anything under `gen/`). Generated code follows generator conventions, not Google's guide.
- Do not flag rules the user has explicitly opted out of via `.golangci.yml` or `//nolint:` directives — check for those first.

## Reference files

For the full rule text per category, read the file as needed:

- [`references/naming.md`](references/naming.md) — function, method, package, test-double, and variable naming (with initialism-casing Suggestion note per ST1003 exemption)
- [`references/packages.md`](references/packages.md) — package size, util packages, proto import naming, file organization, `cmd/` init() exemption
- [`references/imports.md`](references/imports.md) — three-group `goimports -local` layout, blank imports, dot-import test relaxation
- [`references/function-design.md`](references/function-design.md) — option structs, variadic options, signature shape, channel directions, `unparam` exported exemption
- [`references/error-handling.md`](references/error-handling.md) — sentinel errors, `%w` wrapping, `errors.Is`/`errors.As`, `err`-shadow permitted pattern
- [`references/context.md`](references/context.md) — `ctx` as first param, no struct storage, cancel discipline, `contextcheck` linter
- [`references/concurrency.md`](references/concurrency.md) — goroutine ownership, `errgroup`, `sync.Mutex` no-copy, `bodyclose`, `copyloopvar`
- [`references/generics.md`](references/generics.md) — when to use type parameters, `cmp.Ordered`, `slices`/`maps` idioms
- [`references/documentation.md`](references/documentation.md) — godoc conventions with ST1000/1020/1021/1022 exemptions noted as Suggestions
- [`references/variable-declarations.md`](references/variable-declarations.md) — `:=` vs `var`, zero values, `slices.Grow` (Go 1.21+), G115 as Suggestion
- [`references/testing.md`](references/testing.md) — `t.Helper()`, `t.Cleanup`, table tests, per-`_test.go` linter relaxations
- [`references/tooling-and-modernization.md`](references/tooling-and-modernization.md) — Go 1.22+ modernization audit points (`for range int`, `slices`/`maps`, typed atomics, `any` over `interface{}`)
- [`references/golangci-lint.md`](references/golangci-lint.md) — linter-to-rule map, exempted rules, test-file relaxations, `//nolint` policy, and the recommended `.golangci.yml`

Each reference file is structured the same way: rule statement, why it matters, what to look for in code, an example violation, the corrected example. Load only what's relevant to the code in scope.
