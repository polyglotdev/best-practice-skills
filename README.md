# best-practice-skills

Exhaustive, Airbnb-depth **Agent Skills** for writing and reviewing
JavaScript, TypeScript, React, Go, Java, Kotlin, Ruby, Python, and
Terraform. Compatible with **Claude Code**, **Cursor** (chat + Agent
mode), **Windsurf**, and **JetBrains** (via the Claude plugin).

Every rule across every skill is numbered per chapter, justified with a
`> Why?`, and shown with `// bad` + `// good` (or `# bad` / `# good` for
Ruby, Python, and Terraform) examples. Grounded in authoritative upstream
sources: Airbnb's JavaScript and React style guides for the JS/TS/React
skills; Google's Go Style Guide, Effective Go, and Uber's Go Style Guide
for the Go skills; Google's Java Style Guide and Effective Java for the
Java skill; the Android Kotlin style guide and JetBrains' Kotlin coding
conventions for the Kotlin skill; [rubystyle.guide](https://rubystyle.guide/)
and the [Rails Style Guide](https://github.com/rubocop/rails-style-guide)
for the Ruby skill; Google's Python Style Guide, the shipped `ruff.toml`,
and
[fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
for the Python skill; HashiCorp's
[Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)
for the Terraform skill.

## Skills in this repo

### Authoring skills (write code)

| Slash command              | Skill                     | Language                                        | Chapters | Rules |
| -------------------------- | ------------------------- | ----------------------------------------------- | -------- | ----- |
| `/best-practice-js`        | `best-practice-js`        | JavaScript (ES2020+)                            | 22       | —     |
| `/best-practice-ts`        | `best-practice-ts`        | TypeScript (5.x, `strict`)                      | 15       | —     |
| `/best-practice-react`     | `best-practice-react`     | React 18/19 (hooks-first, RSC-aware)            | 15       | —     |
| `/best-practice-go`        | `best-practice-go`        | Go 1.22+                                        | 33       | —     |
| `/best-practice-java`      | `best-practice-java`      | Java 21 LTS + Spring Boot 3.x                   | 38       | 798   |
| `/best-practice-kotlin`    | `best-practice-kotlin`    | Kotlin 2.4 (JVM) + coroutines + Spring Boot 3.x | 47       | 851   |
| `/best-practice-ruby`      | `best-practice-ruby`      | Ruby 4.0 + Rails 8.x + RuboCop                  | 37       | 610   |
| `/best-practice-python`    | `best-practice-python`    | Python 3.12+ + FastAPI + Pydantic v2            | 41       | 498   |
| `/best-practice-terraform` | `best-practice-terraform` | Terraform (HCL) + fmt / validate / TFLint       | 15       | 148   |

### Audit skill (review code)

| Slash command     | Skill            | Purpose                                                                                                                                              |
| ----------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/go-style-guide` | `go-style-guide` | Structured audit of an existing Go file, package, or codebase — findings grouped by category with `file:line` citations, aligned to `.golangci.yml`. |

The JS/TS/React skills are authoring-first — the same rule set is used
when reviewing existing code by asking the agent to audit against
`/best-practice-js`, `/best-practice-ts`, or `/best-practice-react`.

Java follows the Go pattern of an authoring/audit pair. The audit half,
`java-google-best-practices`, lives in the global skills directory rather
than this repo; `best-practice-java` is the rule corpus it reports
against.

## Structure

Each skill uses the same slim-index + chapter-references pattern:

```bash
<skill-name>/
├── SKILL.md              # slim frontmatter + chapter index (≤ 500 lines)
└── references/
    ├── 01-<topic>.md     # numbered chapter with ### N.M rules
    ├── 02-<topic>.md
    └── ...
```

## Install (global, recommended)

Install all skills globally. The CLI detects agents on your machine
(Cursor, Claude Code, Codex, Warp, Windsurf, and others) and installs
into those targets. Do not use `--all`: that expands to every known
agent, including project-only ones that reject global installs.

```bash
npx skills add polyglotdev/best-practice-skills -g -y
```

Install one skill (repeat `--skill` for a short list):

```bash
npx skills add polyglotdev/best-practice-skills -g -y --skill best-practice-go
npx skills add polyglotdev/best-practice-skills -g -y --skill best-practice-ts
npx skills add polyglotdev/best-practice-skills -g -y --skill go-style-guide
npx skills add polyglotdev/best-practice-skills -g -y \
  --skill best-practice-js \
  --skill best-practice-react
```

Skills land in `~/.agents/skills/<skill-name>/`, with agent-specific
symlinks (for example `~/.claude/skills/` and `~/.cursor/skills/`).

## Install (project-scoped)

Copy any skill folder into your repo under
`.claude/skills/<skill-name>/`. Drop the matching root config
(`.golangci.yml`, `.rubocop.yml`, `ruff.toml`, `.tflint.hcl`, etc.) at
the repo root for the languages you use.

```bash
your-repo/
├── .claude/
│   └── skills/
│       ├── best-practice-js/
│       ├── best-practice-ts/
│       ├── best-practice-react/
│       ├── best-practice-go/
│       ├── best-practice-java/
│       ├── best-practice-kotlin/
│       ├── best-practice-ruby/
│       ├── best-practice-python/
│       ├── best-practice-terraform/
│       └── go-style-guide/
├── .golangci.yml
├── .rubocop.yml
├── ruff.toml
├── .tflint.hcl
├── config/
│   ├── checkstyle/
│   │   ├── checkstyle.xml
│   │   └── checkstyle-suppressions.xml
│   └── detekt/
│       └── detekt.yml
└── .editorconfig
```

## Codex / ChatGPT Codex CLI

Codex does not natively read `SKILL.md`, but the files are plain
markdown — point Codex at them from `AGENTS.md`:

```md
# AGENTS.md

When writing JavaScript, follow `.claude/skills/best-practice-js/SKILL.md`.
When writing TypeScript, follow `.claude/skills/best-practice-ts/SKILL.md`.
When writing React, follow `.claude/skills/best-practice-react/SKILL.md`.
When writing Go, follow `.claude/skills/best-practice-go/SKILL.md`
and never violate `.golangci.yml`.
When reviewing Go, follow `.claude/skills/go-style-guide/SKILL.md`.
When writing Java, follow `.claude/skills/best-practice-java/SKILL.md`
and never violate `config/checkstyle/checkstyle.xml`.
When writing Kotlin, follow `.claude/skills/best-practice-kotlin/SKILL.md`
and never violate `config/detekt/detekt.yml`.
When writing Ruby, follow `.claude/skills/best-practice-ruby/SKILL.md`
and never violate `.rubocop.yml`.
When writing Python, follow `.claude/skills/best-practice-python/SKILL.md`
and never violate `ruff.toml`.
When writing Terraform, follow `.claude/skills/best-practice-terraform/SKILL.md`
and never violate `.tflint.hcl` (plus `terraform fmt` / `terraform validate`).
```

## Invocation

Once installed, invoke from your editor's chat panel:

```text
/best-practice-js  refactor this module to use ESM and remove the CommonJS require
/best-practice-ts  add strict types to this API client and remove all `any` usages
/best-practice-react  convert this class component to a hook-based function component
/best-practice-go  implement this handler with context propagation and structured logging
/best-practice-java  convert this DTO to a record and validate it in a compact constructor
/best-practice-java  review this @Transactional service for self-invocation problems
/best-practice-kotlin  replace every !! in this file and say which hid a design problem
/best-practice-kotlin  review this suspend function for cancellation correctness
/best-practice-ruby  add frozen_string_literal and make this idiomatic under rubocop -A
/best-practice-ruby  review this ActiveRecord query for N+1 and find_each
/best-practice-python  review this async def for blocking calls
/best-practice-python  split this FastAPI app into src/<domain>/ packages
/best-practice-terraform  pin providers and split this root by file layout
/best-practice-terraform  review this module for style-guide variables and outputs
/go-style-guide  audit this package before I open the PR
```

## Root configuration files

- **`.golangci.yml`** — the exact linter config both Go skills align to.
  bodyclose, contextcheck, copyloopvar, errcheck, errorlint, gocritic,
  gosec, govet, ineffassign, misspell, nilerr, nolintlint, revive,
  staticcheck, unconvert, unparam, unused, wastedassign, whitespace —
  with per-`_test.go` and `cmd/**` relaxations. Drop it at the root of
  any Go project.
- **`config/checkstyle/checkstyle.xml`** — the Checkstyle ruleset the
  Java skill aligns to. 84 modules, derived from the Checkstyle
  project's `google_checks.xml` with every formatting check removed
  (google-java-format owns those) and ~30 Effective Java design checks
  added that Google's own ruleset omits. Ships with
  `checkstyle-suppressions.xml` for generated sources and test slices.
- **`config/detekt/detekt.yml`** — the detekt ruleset the Kotlin skill
  aligns to. 107 rules, applied as an override on top of detekt's
  defaults (`buildUponDefaultConfig = true`). Targets detekt 1.23.x.
  Formatting rules are deliberately absent because ktlint owns them.
- **`.rubocop.yml`** — the RuboCop config the Ruby skill aligns to.
  TargetRubyVersion 4.0, single quotes, frozen-string-literal comment
  required, plus `rubocop-rails`, `rubocop-performance`, and
  `rubocop-rspec` plugins. RuboCop is both formatter (`rubocop -A`) and
  linter for Ruby.
- **`ruff.toml`** — the Ruff config the Python skill aligns to. House
  style: indent-width 2, quote-style single, line-length 88,
  target-version py312, lint select `E4`/`E7`/`E9`/`F`. When this
  conflicts with Google pyguide on indent/quotes/line length, Ruff wins.
- **`.tflint.hcl`** — the TFLint config the Terraform skill aligns to.
  Bundled `terraform` plugin with `preset = "recommended"`, plus explicit
  enables for documented variables/outputs, snake_case naming, `#` comment
  syntax, and standard module structure (chapter 15). No AWS/GCP ruleset
  and no Checkov/Trivy/tfsec. Drop it at the root of any Terraform project.
- **`.editorconfig`** — Go uses tabs; Kotlin uses 4-space (the Android
  Kotlin style guide's rule) plus ktlint keys; Ruby, Python, and Terraform
  (`.tf` / `.tfvars`) use 2-space; Java and everything else use 2-space
  (Google Java Style §4.2 is +2, not 4); UTF-8; LF; trailing newlines.

## Per-language deep dives

- [`README-js-ts-react.md`](README-js-ts-react.md) — full write-up of
  the JS/TS/React skills (chapter list, install variations, design
  notes).
- [`README-go.md`](README-go.md) — full write-up of the Go skills,
  linter alignment matrix (which staticcheck/gosec/gocritic/govet rules
  are Suggestions because the user's `.golangci.yml` exempts them), and
  invocation examples.
- [`README-kotlin.md`](README-kotlin.md) — full write-up of the Kotlin
  skill: the 47-chapter inventory, the 4-space divergence, the Kotlin 2.4
  stable-vs-experimental split, the shipped detekt configuration, and the
  detekt 1.23.8-versus-2.0-alpha situation.
- [`README-ruby.md`](README-ruby.md) — full write-up of the Ruby skill:
  37-chapter inventory, rubystyle.guide + GitHub Rails Style Guide
  sources, single-quote default, frozen-string pragma on Ruby 4.0.5, and
  the shipped `.rubocop.yml`.
- [`README-python.md`](README-python.md) — full write-up of the Python
  skill: 41-chapter inventory, Ruff house overrides vs Google pyguide,
  FastAPI best-practices alignment, and the minimal lint select.
- [`README-terraform.md`](README-terraform.md) — full write-up of the
  Terraform skill: 15-chapter inventory, HashiCorp Style Guide grounding,
  two-space HCL, shipped `.tflint.hcl`, and honest fmt / validate / TFLint
  enforcement.
- [`docs/reference-data/`](docs/reference-data/) — harvested style-guide
  anchor ground truth and the commands to regenerate it.
- [`README-java.md`](README-java.md) — full write-up of the Java skill:
  the 38-chapter inventory with per-chapter rule counts, the
  tool division-of-labour matrix, the two documented departures from
  upstream `google_checks.xml`, the `MissingSwitchDefault` exhaustiveness
  note, and the known gaps (Lombok, JPA entity design).

## Design principles (shared across all skills)

- **Airbnb depth.** Every rule is numbered per chapter (`## 16.1` /
  `### 16.1` depending on the skill), justified with a `> Why?`, and
  shown with `// bad` / `// good` (or `# bad` / `# good` for Ruby, Python,
  and Terraform) examples.
- **Formatting is delegated.** JS/TS/React chapters assume Prettier owns
  whitespace and quote style. Go chapters assume
  `gofmt` / `gofumpt` / `goimports` own indentation and import order.
  Java chapters assume `google-java-format` (via Spotless) owns Google
  Java Style §4 in full. Kotlin chapters assume `ktlint` owns indentation,
  wrapping, and import order. Ruby chapters assume `rubocop -A` owns
  indentation (2), quotes (single), and Layout. Python chapters assume
  `ruff format` owns indentation (2), quotes (single), and line length
  (88). Terraform chapters assume `terraform fmt` owns two-space indent
  and equals alignment. No chapter re-litigates formatting.
- **Procedural, not descriptive.** Each rule tells the agent what to
  do, what to reject, and how to rewrite — usable as a runbook, not
  just a reference.
- **Traceable citations.** Every rule links to a specific upstream
  section (Airbnb JS / React, Google Style Guide, Style Decisions,
  Style Best Practices, Effective Go, Uber Style, rubystyle.guide,
  rubocop/rails-style-guide, HashiCorp Terraform Style Guide, or
  go.dev/pkg.go.dev and MDN/tc39 where the style guides are silent).
- **Linter-aware for Go, Java, Kotlin, Ruby, Python, and Terraform.** Each
  rule mapped to an enabled linter or check has a
  `> Enforced by: <tool/check-name>` callout. Rules no tool can
  mechanically verify are labeled **Suggestion**, not **Violation**. For
  Java this is machine-verified against Error Prone, Checkstyle, and
  `config/checkstyle/checkstyle.xml`. For Kotlin, against detekt and
  `config/detekt/detekt.yml`. For Ruby, against the RuboCop catalogue and
  the effective enabled set of root `.rubocop.yml`. For Python, against
  the enabled Ruff codes in root `ruff.toml` (`E4`/`E7`/`E9`/`F` plus
  `ruff format`).   For Terraform, against `terraform fmt` /
  `terraform validate` / `terraform test` and the enabled TFLint
  ruleset-terraform rules in root `.tflint.hcl` (catalogue in
  `docs/reference-data/tflint-terraform-rules.txt`; Checkov/Trivy are not
  claimed unless a target repo configures them).
