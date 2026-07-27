---
name: best-practice-python
description: Comprehensive, Airbnb-depth Python best practices for Python 3.12+ with FastAPI and Pydantic v2 - Ruff formatting (2-space indent, single quotes, line-length 88), Google Python Style Guide language rules, asyncio, and FastAPI domain-package architecture. Load when writing or reviewing any .py file, when the user mentions Python, FastAPI, Pydantic, Ruff, pyguide, asyncio, or uv, or when the user asks "is this idiomatic Python?". Enforces the shipped ruff.toml.
---

# best-practice-python

This skill codifies modern Python best practices for **Python 3.12+**,
including an asyncio layer and a FastAPI + Pydantic v2 framework layer. It is
modeled on the depth and structure of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)  - 
numbered rules per chapter, `> Why?` rationale, and `# bad` / `# good`
examples for every rule.

The rules trace to these upstream sources, in this precedence order:

1. **Shipped [`ruff.toml`](../ruff.toml)** - formatting and the enabled lint
   set. House settings that **override** Google style where they conflict:
   `indent-width = 2`, `quote-style = 'single'`, `line-length = 88`,
   `target-version = 'py312'`, `select = ['E4', 'E7', 'E9', 'F']`.
2. **[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)**  - 
   language rules, naming, docstrings, imports, types, exceptions, and the
   rest of pyguide. When pyguide and `ruff.toml` disagree on layout (indent,
   quotes, line length), **Ruff wins**.
3. **[zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)**  - 
   FastAPI project structure, async route discipline, Pydantic/settings,
   dependencies, background tasks, and testing (chapters 31 to 38).
4. **Python 3.12 language docs / PEPs** - for features pyguide predates
   (PEP 695 generics, `TaskGroup`, `asyncio.timeout`, etc.).

All formatting concerns - indentation, quotes, line wrapping, trailing
commas - are owned by `ruff format` and are never re-litigated in prose.
Chapter 1 documents the chain; every later chapter assumes formatted code.
This is the same delegation `best-practice-go` makes to `gofmt`,
`best-practice-java` to `google-java-format`, and `best-practice-kotlin` to
`ktlint`.

**Indentation is two spaces. Quotes are single.** That is deliberate house
law via Ruff, not what [pyguide §3.4](https://google.github.io/styleguide/pyguide.html#s3.4-indentation)
or PEP 8 prescribe. Document the departure; do not silently pretend Google
says 2-space/single-quote.

Every rule that maps to an enabled check in the shipped `ruff.toml`
(`E4` / `E7` / `E9` / `F`, or `ruff format`) carries an
**`> Enforced by: <code>`** callout. Rules no enabled tool can verify are
labeled **Suggestion**, not **Violation**. Expanding `select` is a separate
product decision; until then, do not claim enforcement that would not fire.

## Language version

The floor is **Python 3.12**. Prefer 3.12 idioms: `X | Y` unions, builtin
generics (`list[str]`), PEP 695 `type` / `[T]` syntax, `datetime.UTC`,
`asyncio.TaskGroup`, `asyncio.timeout`. Env management is **`uv`**.

## When to use

- Writing or reviewing `.py` files on Python 3.12+.
- Answering "is this idiomatic?" for Python, FastAPI, or Pydantic v2.
- Setting up or auditing `ruff.toml`, pytest, or pyright/mypy.
- Reviewing async correctness, blocking calls in `async def`, or FastAPI
  domain package layout.
- Preparing a Python change for code review.

## Scope

- Style foundation: Ruff format/lint, source layout, naming, Google-style
  docstrings.
- Language core: imports, types, functions, classes, dataclasses, protocols,
  generics/PEP 695, exceptions, context managers, iterators/generators,
  comprehensions, strings, collections, pattern matching, enums, datetimes,
  truthiness, properties, decorators, concurrency, logging, pytest.
- Asyncio: fundamentals, structured concurrency, cancellation/timeouts,
  async context/iteration, the blocking-call trap.
- FastAPI + Pydantic v2: domain packages, DI, request/response models,
  settings/validation, errors, background tasks, testing.
- Tooling: `ruff.toml`, type checkers, `uv` project layout.

## Non-goals

- **Formatting debates.** `ruff format` owns layout. Chapter 1 states the
  chain and moves on.
- **Django / Flask / Starlette-only frameworks** as first-class targets.
  Patterns here are FastAPI-shaped.
- **Data science notebook style** (pandas-first exploratory workflows).
- **Expanding Ruff `select` without an explicit decision.** The shipped
  minimal set is intentional; broader families stay Suggestions until enabled.

---

## Chapters

Each chapter is a self-contained reference file with numbered rules,
`> Why?` rationale, `# bad` / `# good` code, and `> Enforced by:`
tool callouts. Files live under `references/`.

### Part I - Style foundation

| # | Chapter | File |
|---|---------|------|
| 1 | Formatting & Tooling | [`references/01-formatting-and-tooling.md`](references/01-formatting-and-tooling.md) |
| 2 | Source Files & Layout | [`references/02-source-files-and-layout.md`](references/02-source-files-and-layout.md) |
| 3 | Naming | [`references/03-naming.md`](references/03-naming.md) |
| 4 | Docstrings | [`references/04-docstrings.md`](references/04-docstrings.md) |

### Part II - Language core

| # | Chapter | File |
|---|---------|------|
| 5 | Imports & Packages | [`references/05-imports-and-packages.md`](references/05-imports-and-packages.md) |
| 6 | Types & Annotations | [`references/06-types-and-annotations.md`](references/06-types-and-annotations.md) |
| 7 | Functions | [`references/07-functions.md`](references/07-functions.md) |
| 8 | Classes | [`references/08-classes.md`](references/08-classes.md) |
| 9 | Dataclasses | [`references/09-dataclasses.md`](references/09-dataclasses.md) |
| 10 | Protocols & ABCs | [`references/10-protocols-and-abcs.md`](references/10-protocols-and-abcs.md) |
| 11 | Generics & PEP 695 | [`references/11-generics-and-pep695.md`](references/11-generics-and-pep695.md) |
| 12 | Exceptions | [`references/12-exceptions.md`](references/12-exceptions.md) |
| 13 | Context Managers | [`references/13-context-managers.md`](references/13-context-managers.md) |
| 14 | Iterators & Generators | [`references/14-iterators-and-generators.md`](references/14-iterators-and-generators.md) |
| 15 | Comprehensions | [`references/15-comprehensions.md`](references/15-comprehensions.md) |
| 16 | Strings | [`references/16-strings.md`](references/16-strings.md) |
| 17 | Collections | [`references/17-collections.md`](references/17-collections.md) |
| 18 | Pattern Matching | [`references/18-pattern-matching.md`](references/18-pattern-matching.md) |
| 19 | Enums | [`references/19-enums.md`](references/19-enums.md) |
| 20 | Dates & Times | [`references/20-dates-and-times.md`](references/20-dates-and-times.md) |
| 21 | Truthiness & Comparisons | [`references/21-truthiness-and-comparisons.md`](references/21-truthiness-and-comparisons.md) |
| 22 | Properties & Descriptors | [`references/22-properties-and-descriptors.md`](references/22-properties-and-descriptors.md) |
| 23 | Decorators | [`references/23-decorators.md`](references/23-decorators.md) |
| 24 | Concurrency | [`references/24-concurrency.md`](references/24-concurrency.md) |
| 25 | Logging | [`references/25-logging.md`](references/25-logging.md) |
| 26 | Testing | [`references/26-testing.md`](references/26-testing.md) |

### Part III - Async

| # | Chapter | File |
|---|---------|------|
| 27 | Asyncio Fundamentals | [`references/27-asyncio-fundamentals.md`](references/27-asyncio-fundamentals.md) |
| 28 | Structured Concurrency | [`references/28-structured-concurrency.md`](references/28-structured-concurrency.md) |
| 29 | Cancellation & Timeouts | [`references/29-cancellation-and-timeouts.md`](references/29-cancellation-and-timeouts.md) |
| 30 | Async Context & Iteration | [`references/30-async-context-and-iteration.md`](references/30-async-context-and-iteration.md) |
| 31 | The Blocking-Call Trap | [`references/31-blocking-call-trap.md`](references/31-blocking-call-trap.md) |

### Part IV - FastAPI + Pydantic v2

| # | Chapter | File |
|---|---------|------|
| 32 | FastAPI App Structure | [`references/32-fastapi-app-structure.md`](references/32-fastapi-app-structure.md) |
| 33 | FastAPI Dependency Injection | [`references/33-fastapi-dependency-injection.md`](references/33-fastapi-dependency-injection.md) |
| 34 | Request & Response Models | [`references/34-fastapi-request-response-models.md`](references/34-fastapi-request-response-models.md) |
| 35 | Pydantic Validation & Settings | [`references/35-pydantic-validation-and-settings.md`](references/35-pydantic-validation-and-settings.md) |
| 36 | FastAPI Error Handling | [`references/36-fastapi-error-handling.md`](references/36-fastapi-error-handling.md) |
| 37 | FastAPI Background Tasks | [`references/37-fastapi-background-tasks.md`](references/37-fastapi-background-tasks.md) |
| 38 | FastAPI Testing | [`references/38-fastapi-testing.md`](references/38-fastapi-testing.md) |

### Part V - Tooling

| # | Chapter | File |
|---|---------|------|
| 39 | Ruff Configuration | [`references/39-ruff-configuration.md`](references/39-ruff-configuration.md) |
| 40 | Type Checking | [`references/40-type-checking.md`](references/40-type-checking.md) |
| 41 | Project Layout & uv | [`references/41-project-layout-and-uv.md`](references/41-project-layout-and-uv.md) |

## How to use this skill

1. **Automatic loading.** The frontmatter `description` tells the agent when
   to load this skill. The index is what it reads first.
2. **Targeted reads.** Open only the matching chapter under `references/`.
3. **Full review.** Read every chapter for a comprehensive audit.
4. **Layering.** Chapters 1 to 26 apply to every Python codebase. Chapters
   27 to 31 apply wherever `async`/`await` appears. Chapters 32 to 38 apply
   to FastAPI + Pydantic v2 services.
5. **Tool config.** Root [`ruff.toml`](../ruff.toml) is authoritative; see
   chapter 39.

## Self-check

Before treating Python work as finished, verify:

- `uv run ruff format --check .` and `uv run ruff check .` are clean.
- Samples use **2-space indent** and **single quotes**.
- Public APIs are typed; prefer 3.12 forms (`list[str]`, `X | None`, PEP 695).
- No bare `except:`; no mutable defaults; no blocking IO inside `async def`
  without a bridge.
- FastAPI domains live under `src/<domain>/` with thin routers and separate
  schemas/models/services.
- Domain errors map to HTTP at the edge; BackgroundTasks are not a job queue.
- No new `# noqa` / `# type: ignore` without a scoped code and a reason.
