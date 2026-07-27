# go-skills

Two exhaustive Go skills — an **authoring guide** and an **audit
workflow** — packaged as [skills.sh](https://www.skills.sh)–compatible
Agent Skills that work in **Claude Code**, **Cursor** (chat + Agent
mode), **Windsurf**, and **JetBrains** (via the Claude plugin).

Both skills are grounded in three upstream sources, in this precedence:

1. **[Google Go Style Guide](https://google.github.io/styleguide/go/)** —
   the Style Guide, Style Decisions, and Best Practices documents.
2. **[Effective Go](https://go.dev/doc/effective_go)** — the Go team's
   idioms document.
3. **[Uber Go Style Guide](https://github.com/uber-go/guide/blob/master/style.md)** —
   only where a rule is not covered by (1) or (2) and does not contradict
   them.

Both skills are also aligned to the exact linter set in the recommended
[`.golangci.yml`](.golangci.yml) at the repo root — bodyclose,
contextcheck, copyloopvar, errcheck, errorlint, gocritic, gosec, govet,
ineffassign, misspell, nilerr, nolintlint, revive, staticcheck,
unconvert, unparam, unused, wastedassign, whitespace — with per-`_test.go`
and `cmd/**` relaxations documented explicitly.

## Skills in this repo

| Slash command | Skill | Purpose | Files |
|---|---|---|---|
| `/best-practice-go` | `best-practice-go` | Authoring guide — how to write idiomatic Go. Airbnb-style rules with `// bad`/`// good` examples for every rule and `> Enforced by:` linter callouts. | 33 chapters |
| `/go-style-guide` | `go-style-guide` | Audit workflow — produces a structured findings report with `file:line` citations, categorized by naming/errors/context/concurrency/etc. | 13 reference files + workflow prose |

## Structure

Each skill uses the standard slim-index + chapter-references pattern:

```
best-practice-go/
├── SKILL.md
└── references/
    ├── 01-formatting.md
    ├── 02-names.md
    ├── ...
    └── 33-linter-configuration.md    # ships the .golangci.yml verbatim

go-style-guide/
├── SKILL.md                          # audit workflow + report template
└── references/
    ├── naming.md
    ├── packages.md
    ├── imports.md
    ├── function-design.md
    ├── error-handling.md
    ├── context.md
    ├── concurrency.md
    ├── generics.md
    ├── documentation.md
    ├── variable-declarations.md
    ├── testing.md
    ├── tooling-and-modernization.md
    └── golangci-lint.md              # linter → audit-category map

.golangci.yml                         # recommended linter config
```

**Total content:** ~10,900 lines across 47 markdown files — 33 authoring
chapters totaling ~7,700 lines + 13 audit reference files totaling
~5,300 lines. Each rule includes numbered numbering, `> Why?` rationale,
`// bad` / `// good` examples, an inline citation link to the upstream
source, and (where applicable) a `> Enforced by:` line naming the CI
linter that catches the violation.

## Install (global — recommended)

```bash
# Install both skills globally so Claude Code / Cursor / Windsurf / JetBrains pick them up
npx skills add <your-github-user>/go-skills -g -y

# Or install a single skill from the repo
npx skills add <your-github-user>/go-skills --skill best-practice-go -g -y
npx skills add <your-github-user>/go-skills --skill go-style-guide -g -y
```

Globally installed skills land in `~/.claude/skills/<skill-name>/` and
are picked up automatically. Note: since you already have
`~/.claude/skills/go-style-guide/` installed, the fresh version in this
archive **replaces** the existing folder when you copy it in.

## Install (project-scoped)

Copy either skill folder into your repo under
`.claude/skills/<skill-name>/`. Also drop the `.golangci.yml` at the repo
root so the linter matches what the skills enforce.

```text
your-repo/
├── .claude/
│   └── skills/
│       ├── best-practice-go/{SKILL.md,references/}
│       └── go-style-guide/{SKILL.md,references/}
└── .golangci.yml
```

## Codex / ChatGPT Codex CLI

Codex does not natively read `SKILL.md`, but the files are plain
markdown. Point Codex at them from `AGENTS.md`:

```md
# AGENTS.md

When writing Go, follow `.claude/skills/best-practice-go/SKILL.md`
and its `references/` chapters. Never violate `.golangci.yml`.

When reviewing Go, follow `.claude/skills/go-style-guide/SKILL.md`.
```

## Invocation

Once installed, invoke from your editor's chat panel:

```text
/best-practice-go implement this handler with context propagation and structured logging
/best-practice-go add generics to this collection type
/go-style-guide audit this package before I open the PR
/go-style-guide review the error handling in service/user
```

## What each skill covers

### `best-practice-go` (33 chapters)

Formatting; Names; Package Organization; Imports; Declarations; Types;
Slices, Maps, Arrays; Strings; Constants; Control Structures; Functions;
Options; Methods & Receivers; Interfaces; Embedding; Errors; Error
Handling; Panic & Recover; Context; Concurrency; Channels; Sync
Primitives; Goroutines & Lifecycle; Generics; Time; Logging; Testing;
Test Doubles; Godoc & Commentary; Global State; Performance; Tooling &
Modernization; Linter Configuration.

### `go-style-guide` (13 reference files + audit workflow)

Naming; Packages; Imports; Function design; Error handling; Context;
Concurrency; Generics; Documentation; Variable declarations; Testing;
Tooling & modernization; `golangci-lint` linter-to-rule map.

## Alignment to `.golangci.yml`

Every rule that maps to an enabled linter carries an
`> Enforced by: <linter-name>` callout. Rules that reflect a linter
*exemption* are labeled **Suggestion**, not **Violation**:

| Exemption | Impact on the skills |
|---|---|
| staticcheck **ST1000** (package doc required) | Doc-comment rules downgraded to Suggestion in chapter 29 and audit `documentation.md`. |
| staticcheck **ST1003** (initialism casing like `getURL`) | Initialism rule is a Suggestion in chapter 2 and audit `naming.md`. |
| staticcheck **ST1020/1021/1022** (doc starts with name) | Related godoc rules downgraded to Suggestion. |
| gosec **G104/G115/G304/G404** | Integer-overflow, path-injection, and math/rand use are Suggestions with positive-pattern guidance, not Violations. |
| gocritic **hugeParam / rangeValCopy** | Large-struct-copy is a Suggestion in chapter 31, not a Violation. |
| gocritic **ifElseChain / paramTypeCombine** | Not taught as rules at all — the linter deliberately allows both. |
| govet **fieldalignment** | Struct field ordering is out of scope. |
| govet **shadow** for `err` | Intentional `if err := f(); err != nil` shadow is taught as a Recommended idiom. |
| `_test.go` relaxation of bodyclose / errcheck / errorlint / gosec / revive / unparam | Chapter 27 (Testing) and audit `testing.md` document the relaxations as explicit permissions. |
| `cmd/**` `gochecknoinits` exemption | Chapter 30 (Global State) and audit `packages.md` note `init()` is permitted in `cmd/**` for flag registration. |

## Design notes

- **Airbnb depth, modern Go content.** Every rule is numbered per
  chapter (`### 16.1`, `### 16.2`), justified with a `> Why?`, and shown
  with `// bad` + `// good` examples. Rules assume Go 1.22+ language
  features (`for range int`, `for range func`, `slices`/`maps`/`cmp`
  stdlib, `errors.Join`, `log/slog`, `min`/`max`/`clear` builtins, typed
  `sync/atomic`).
- **`gofmt` / `gofumpt` / `goimports` are source of truth for
  formatting.** Chapter 1 documents the chain. No other chapter argues
  about whitespace or import order.
- **Procedural, not descriptive.** Each rule tells the agent what to
  do, what to reject, and how to rewrite — usable as a runbook, not
  just a reference.
- **Traceable citations.** Every rule links to the specific upstream
  section (Google's Style Decisions, Effective Go, Uber Style, or
  go.dev/pkg.go.dev where the style guides are silent — e.g. generics
  and the Go 1.22+ additions).
