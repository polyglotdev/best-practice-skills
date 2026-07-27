---
name: best-practice-js
description: Comprehensive, Airbnb-depth JavaScript best practices for ES2022+ on Node 20+ and evergreen browsers — types, references, objects, arrays, destructuring, functions, classes, modules, async/promises, error handling, security, performance, and testing. Load when writing or reviewing any .js/.mjs/.cjs file, or a .jsx file's non-JSX logic, and for refactor/lint/idiomatic-JS requests. Enforces the user's Prettier config (no semicolons, single quotes, 2-space indent, no trailing commas) rather than Airbnb's formatting opinions. Stacks with best-practice-react for .jsx/.tsx component code.
---

# best-practice-js

This skill codifies modern JavaScript best practices for ES2022+ running on
Node 20+ and evergreen browsers (Chrome, Firefox, Safari, Edge — last two
versions). It is modeled on the depth and structure of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript), but
modernized: ES5-era workarounds are replaced with native ES2022+ idioms,
`arguments` is banned outright, and new chapters cover async/await, error
handling, Node specifics, browser specifics, security, and performance that
Airbnb's guide predates or only gestures at. All formatting concerns —
semicolons, quote style, comma placement, indentation, line wrapping — are
owned by the user's Prettier config (see `references/prettier.md`) and are
never re-litigated here; where Airbnb's prose recommends a formatting choice
that conflicts with Prettier, this skill silently follows Prettier instead.
This skill covers plain JavaScript logic. For JSX/component-specific rules
(hooks, props, render patterns), stack this skill with `best-practice-react`
— that skill assumes this one is already loaded for the underlying `.js`
semantics inside `.jsx` files.

## When to use

- Writing new `.js`, `.mjs`, or `.cjs` files, or the non-JSX logic inside
  `.jsx` files.
- Reviewing, refactoring, or linting existing JavaScript for idiomatic style.
- Answering "is this good JavaScript?" or "how should I write this?"
  questions about language-level constructs (not framework-specific ones).
- Resolving a stylistic disagreement by citing a concrete rule and rationale.
- Setting up or auditing lint/format tooling defaults for a JS/Node project.

## Scope

- Language-level JavaScript: types, references, control flow, functions,
  classes, modules, iteration, async patterns, error handling.
- Runtime-adjacent conventions for Node 20+ (module resolution, `fs/promises`,
  environment config) and evergreen browsers (`fetch`, DOM APIs, storage).
- Baseline security and performance habits that are language- or
  runtime-level, not framework-level.
- Testing philosophy and conventions for plain JS/Node code (Vitest,
  `node:test`).

## Non-goals

- **Formatting.** Semicolons, quotes, commas, indentation, line length — all
  Prettier's job. This skill states our config's outcome briefly and moves on.
- **TypeScript.** No type annotations, interfaces, or generics appear in any
  example. If the project uses TypeScript, pair this skill with a TS-specific
  one.
- **React/JSX semantics.** Hooks, component structure, prop conventions, and
  JSX-specific formatting live in `best-practice-react`.
- **CSS, HTML, build-tool configuration** beyond the "Tooling defaults"
  chapter's linting/formatting/test-runner pointers.
- **Framework-specific idioms** (Express routing conventions, Next.js data
  fetching, etc.) — those belong to framework-specific skills.
- **Airbnb's `jQuery`, `ECMAScript 5 Compatibility`, and `ECMAScript 6+
  Compatibility` sections.** Intentionally omitted — jQuery is legacy, and
  every rule in the ES5/ES6 compat sections is already satisfied by Node
  20+ and evergreen browsers. Where an idiom from those sections is still
  relevant (e.g. never use `arguments`, prefer `const`/`let`, native class
  syntax), it appears inline in the relevant modern chapter.

---

## Chapters

Each chapter is a self-contained reference file. Load the whole skill for a full review, or open a single chapter for a targeted question. Files live under `references/`.

| # | Chapter | File |
|---|---------|------|
| 1 | Types | [`references/01-types.md`](references/01-types.md) |
| 2 | References | [`references/02-references.md`](references/02-references.md) |
| 3 | Objects | [`references/03-objects.md`](references/03-objects.md) |
| 4 | Arrays | [`references/04-arrays.md`](references/04-arrays.md) |
| 5 | Destructuring | [`references/05-destructuring.md`](references/05-destructuring.md) |
| 6 | Strings | [`references/06-strings.md`](references/06-strings.md) |
| 7 | Functions | [`references/07-functions.md`](references/07-functions.md) |
| 8 | Arrow Functions | [`references/08-arrow-functions.md`](references/08-arrow-functions.md) |
| 9 | Classes & Constructors | [`references/09-classes-and-constructors.md`](references/09-classes-and-constructors.md) |
| 9b | Constructors (deep dive) | [`references/09b-constructors.md`](references/09b-constructors.md) |
| 10 | Modules | [`references/10-modules.md`](references/10-modules.md) |
| 11 | Iterators and Generators | [`references/11-iterators-and-generators.md`](references/11-iterators-and-generators.md) |
| 12 | Properties | [`references/12-properties.md`](references/12-properties.md) |
| 13 | Variables | [`references/13-variables.md`](references/13-variables.md) |
| 14 | Hoisting | [`references/14-hoisting.md`](references/14-hoisting.md) |
| 15 | Comparison Operators & Equality | [`references/15-comparison-operators-and-equality.md`](references/15-comparison-operators-and-equality.md) |
| 16 | Blocks | [`references/16-blocks.md`](references/16-blocks.md) |
| 17 | Control Statements | [`references/17-control-statements.md`](references/17-control-statements.md) |
| 18 | Comments | [`references/18-comments.md`](references/18-comments.md) |
| 19 | Whitespace | [`references/19-whitespace.md`](references/19-whitespace.md) |
| 20 | Commas | [`references/20-commas.md`](references/20-commas.md) |
| 21 | Semicolons | [`references/21-semicolons.md`](references/21-semicolons.md) |
| 22 | Type Casting & Coercion | [`references/22-type-casting-and-coercion.md`](references/22-type-casting-and-coercion.md) |
| 23 | Naming Conventions | [`references/23-naming-conventions.md`](references/23-naming-conventions.md) |
| 24 | Accessors | [`references/24-accessors.md`](references/24-accessors.md) |
| 25 | Events | [`references/25-events.md`](references/25-events.md) |
| 26 | Async & Promises | [`references/26-async-and-promises.md`](references/26-async-and-promises.md) |
| 27 | Error Handling | [`references/27-error-handling.md`](references/27-error-handling.md) |
| 28 | Standard Library | [`references/28-standard-library.md`](references/28-standard-library.md) |
| 29 | Node.js specifics | [`references/29-node-js-specifics.md`](references/29-node-js-specifics.md) |
| 30 | Browser specifics | [`references/30-browser-specifics.md`](references/30-browser-specifics.md) |
| 31 | Security | [`references/31-security.md`](references/31-security.md) |
| 32 | Performance | [`references/32-performance.md`](references/32-performance.md) |
| 33 | Testing | [`references/33-testing.md`](references/33-testing.md) |
| 34 | Tooling defaults | [`references/34-tooling-defaults.md`](references/34-tooling-defaults.md) |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells Claude/Cursor/Windsurf when to load `best-practice-js`. When it loads, this index is what the agent reads first.
2. **Targeted reads.** When the agent needs one specific area (say, async/promise rules or module conventions), it opens only the matching chapter under `references/` — this keeps the context window small.
3. **Full review.** For a comprehensive review, the agent reads every referenced chapter file. Each one is exhaustive on its own topic with numbered rules, `> Why?` rationale, and `// bad` / `// good` examples.
4. **Prettier config.** Every code example in every chapter honors the user's Prettier configuration (no semicolons, single quotes, 2-space indent, no trailing commas, arrow-fn single param parenthesized, spaces inside object braces; for JSX: double-quoted attribute values, multiline closing `>` on its own line).

## Self-check

Before treating any JavaScript you write or review as finished, verify:

- No `var`, no `arguments`, no `eval`, no `new Object()`/`new Array()`.
- Every multiline block uses braces; no single-statement bodies
  without them.
- `===`/`!==` only; `??` for defaults where `0`/`''`/`false` are valid
  values.
- Async code uses `async`/`await`, not manual `.then()` chains, and no
  rejected promise is left unhandled.
- Every `throw` throws an `Error` (or subclass); wrapped errors carry
  `{ cause }`.
- No untrusted input reaches `innerHTML`, a SQL string, `eval`, or a
  file path without validation.
- No secret reaches a client bundle, `localStorage`, or a
  `NEXT_PUBLIC_`/`PUBLIC_`-style variable.
- The code compiles cleanly under the project's Prettier config: no
  semicolons, single quotes, 2-space indent, no trailing commas, arrow
  params parenthesized, spaces inside `{ }`.
- Tests (if present) use sentence-style names, fake timers for
  time-based logic, and assert on public behavior, not internals.
- If this file lives beside `.jsx`, confirm `best-practice-react` is
  also loaded for the component-level rules this skill doesn't cover.

