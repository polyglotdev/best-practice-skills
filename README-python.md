# best-practice-python

An exhaustive, Airbnb-depth **Agent Skill** for writing and reviewing
Python 3.12+, including asyncio and a FastAPI + Pydantic v2 layer.

**498 numbered rules across 41 chapters.** Every rule is justified with a
`> Why?`, shown with `# bad` / `# good` code, and where a tool can catch
it, labeled `> Enforced by: <code>`.

## Upstream sources, in precedence order

1. **Shipped [`ruff.toml`](ruff.toml)** - formatting and the enabled lint
   set (`E4`, `E7`, `E9`, `F`). House overrides that win over Google style:
   - `indent-width = 2` (pyguide §3.4 / PEP 8 use 4)
   - `quote-style = 'single'` (Ruff/Black default is double)
   - `line-length = 88` (pyguide §3.2 prefers 80)
   - `target-version = 'py312'`
2. **[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)**  - 
   language rules, naming, docstrings, imports, types, exceptions.
   Anchors were harvested into [`docs/reference-data/pyguide-anchors.txt`](docs/reference-data/pyguide-anchors.txt).
3. **[zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)**  - 
   FastAPI domain packages, async route discipline, Pydantic/settings, DI,
   background tasks, and async test clients (chapters 31 to 38).
4. **Python 3.12 docs / PEPs** - for features pyguide does not yet cover.

When Google style and `ruff.toml` conflict on layout, **Ruff wins**. Chapters
document that departure explicitly rather than misquoting Google.

## House style (Ruff)

| Setting | Value |
|---|---|
| Indent | 2 spaces |
| Quotes | single |
| Line length | 88 |
| Target | py312 |
| Lint select | `E4`, `E7`, `E9`, `F` (minimal Ruff default families) |

Formatting is always delegated to `ruff format`. The minimal `select` means
most pyguide/FastAPI rules are labeled **Suggestion** until the project
expands `select` (recommended candidates: `I`, `UP`, `B`, `ASYNC`, `PT`,
`D` with Google pydocstyle). Citing a rule that exists but is not enabled
is not allowed for **Violation** callouts.

## Chapters

### Part I - Style foundation

| # | Chapter |
|---|---------|
| 1 | Formatting & Tooling |
| 2 | Source Files & Layout |
| 3 | Naming |
| 4 | Docstrings |

### Part II - Language core

| # | Chapter |
|---|---------|
| 5 | Imports & Packages |
| 6 | Types & Annotations |
| 7 | Functions |
| 8 | Classes |
| 9 | Dataclasses |
| 10 | Protocols & ABCs |
| 11 | Generics & PEP 695 |
| 12 | Exceptions |
| 13 | Context Managers |
| 14 | Iterators & Generators |
| 15 | Comprehensions |
| 16 | Strings |
| 17 | Collections |
| 18 | Pattern Matching |
| 19 | Enums |
| 20 | Dates & Times |
| 21 | Truthiness & Comparisons |
| 22 | Properties & Descriptors |
| 23 | Decorators |
| 24 | Concurrency |
| 25 | Logging |
| 26 | Testing |

### Part III - Async

| # | Chapter |
|---|---------|
| 27 | Asyncio Fundamentals |
| 28 | Structured Concurrency |
| 29 | Cancellation & Timeouts |
| 30 | Async Context & Iteration |
| 31 | The Blocking-Call Trap |

### Part IV - FastAPI + Pydantic v2

| # | Chapter |
|---|---------|
| 32 | FastAPI App Structure |
| 33 | FastAPI Dependency Injection |
| 34 | Request & Response Models |
| 35 | Pydantic Validation & Settings |
| 36 | FastAPI Error Handling |
| 37 | FastAPI Background Tasks |
| 38 | FastAPI Testing |

### Part V - Tooling

| # | Chapter |
|---|---------|
| 39 | Ruff Configuration |
| 40 | Type Checking |
| 41 | Project Layout & uv |

Chapters 1 to 26 apply to every Python codebase. Chapters 27 to 31 apply
wherever asyncio appears. Chapters 32 to 38 apply to FastAPI services and
follow the domain-package layout from fastapi-best-practices.

## Division of labour between tools

| Tool | Owns |
|---|---|
| **ruff format** | Indent (2), quotes (single), line length (88), wrapping, trailing commas |
| **ruff check** (`E4`/`E7`/`E9`/`F`) | Import hygiene, a small pycodestyle subset, Pyflakes correctness |
| **pyright / mypy** | Static types (not Ruff) |
| **pytest** | Tests |

## Install

```bash
npx skills add <your-github-user>/best-practice-skills --skill best-practice-python -g -y
```

Project-scoped: copy `best-practice-python/` into `.claude/skills/` and drop
`ruff.toml` at the repo root (merge carefully if one already exists).

## Invocation

```text
/best-practice-python  rewrite this module to 2-space indent and single quotes under ruff format
/best-practice-python  is this FastAPI router thin enough or is SQL leaking in?
/best-practice-python  review this async def for blocking calls
/best-practice-python  split this god-package into src/<domain>/ layout
/best-practice-python  map OrderNotFoundError to HTTP without leaking internals
```

## Design notes

- **Ruff is the formatter and the lint baseline.** Google pyguide is the
  language guide. FastAPI best practices is the framework guide.
- **Minimal select is intentional.** It matches the user's canonical config.
  Most semantic rules are Suggestions until `select` expands.
- **Verified anchors.** pyguide links resolve against
  `docs/reference-data/pyguide-anchors.txt`.

## Known gaps

- Broader Ruff families (`D`, `N`, `I`, `UP`, `B`, `ASYNC`, `PT`, `S`) are
  not enabled in the shipped config.
- Django/Flask are out of scope.
- SQLAlchemy deep ORM design is only covered where FastAPI boundaries touch
  it (no full data-layer skill).
- Sonatype/Safety MCP auth was unavailable during package version checks;
  pin FastAPI/Pydantic/pytest via `uv` against current PyPI when scaffolding
  apps.
