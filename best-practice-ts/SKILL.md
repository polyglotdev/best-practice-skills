---
name: best-practice-ts
description: TypeScript 5.x best practices — the type-system layer on top of best-practice-js. Covers strict-mode tsconfig baselines, types vs interfaces, narrowing, generics, utility/mapped/conditional types, satisfies, runtime validation at trust boundaries, declaration files, and library publishing. Load when writing or reviewing .ts/.tsx files. Enforces the user's Prettier config (no semicolons, single quotes, no trailing commas).
---

# best-practice-ts

This skill is the TypeScript layer. It assumes `best-practice-js` is already
applied underneath — every rule about `const`/`let`, destructuring, arrow
functions, module syntax, control flow, naming, and so on still holds. This
document does not restate those rules. It only covers what changes, or gets
added, once a file has a type system: `tsconfig.json`, the `type` system
itself (unions, generics, narrowing, mapped/conditional types), declaration
files, and the runtime-validation boundary that TypeScript cannot enforce for
you.

Target: TypeScript 5.4+. All examples assume `strict: true` and the
`tsconfig.json` baselines in [Chapter 1](#1-tsconfigjson--required-baseline).
All code honors the user's Prettier config: no semicolons at statement end,
single quotes, 2-space indent, no trailing commas, parenthesized single arrow
params, double quotes only in JSX attributes. Semicolons **do** appear between
members inside `interface`/`type` object bodies — Prettier leaves those alone.

## When to use

Load this skill whenever you are writing, reviewing, or reviewing a diff for
any `.ts`, `.tsx`, `.mts`, or `.cts` file, or a `tsconfig.json`. Load it
alongside `best-practice-js` (for underlying JS rules) and, for React
component code, alongside `best-practice-react` (this skill only briefly
touches typed-React ergonomics in Chapter 27).

## Scope

- `tsconfig.json` baselines for libraries and apps.
- The type-system layer: types vs interfaces, primitives, objects, arrays,
  tuples, unions, intersections, discriminated unions, generics, utility
  types, mapped types, conditional types, template literal types.
- Narrowing, assertions, `satisfies`, nullability, readonly/immutability.
- Functions, classes, and enums as seen through the type system.
- Modules, declaration files, and runtime validation at I/O boundaries.
- Type-testing, library publishing, and JS→TS migration.

## Non-goals

- General JavaScript style (variable declarations, loops, operators,
  formatting) — see `best-practice-js`.
- React component patterns, hooks, JSX structure — see `best-practice-react`.
  Chapter 27 here covers only the type-level surface.
- Build tooling beyond `tsconfig.json` (bundlers, monorepo orchestration,
  CI).

## Chapters

Each chapter is a self-contained reference file. Load the whole skill for a full review, or open a single chapter for a targeted question. Files live under `references/`.

| # | Chapter | File |
|---|---------|------|
| 1 | tsconfig.json — required baseline | [`references/01-tsconfig-json-required-baseline.md`](references/01-tsconfig-json-required-baseline.md) |
| 2 | Types vs Interfaces | [`references/02-types-vs-interfaces.md`](references/02-types-vs-interfaces.md) |
| 3 | Primitive Types & Literal Types | [`references/03-primitive-types-and-literal-types.md`](references/03-primitive-types-and-literal-types.md) |
| 4 | Objects & Records | [`references/04-objects-and-records.md`](references/04-objects-and-records.md) |
| 5 | Arrays & Tuples | [`references/05-arrays-and-tuples.md`](references/05-arrays-and-tuples.md) |
| 6 | Union Types | [`references/06-union-types.md`](references/06-union-types.md) |
| 7 | Intersection Types | [`references/07-intersection-types.md`](references/07-intersection-types.md) |
| 8 | Discriminated Unions & Exhaustiveness | [`references/08-discriminated-unions-and-exhaustiveness.md`](references/08-discriminated-unions-and-exhaustiveness.md) |
| 9 | `any` vs `unknown` vs `never` | [`references/09-any-vs-unknown-vs-never.md`](references/09-any-vs-unknown-vs-never.md) |
| 10 | Type Assertions (`as`, `!`, `satisfies`) | [`references/10-type-assertions-as-satisfies.md`](references/10-type-assertions-as-satisfies.md) |
| 11 | Type Narrowing | [`references/11-type-narrowing.md`](references/11-type-narrowing.md) |
| 12 | Nullability | [`references/12-nullability.md`](references/12-nullability.md) |
| 13 | Readonly & Immutability | [`references/13-readonly-and-immutability.md`](references/13-readonly-and-immutability.md) |
| 14 | Generics | [`references/14-generics.md`](references/14-generics.md) |
| 15 | Utility Types | [`references/15-utility-types.md`](references/15-utility-types.md) |
| 16 | Mapped Types | [`references/16-mapped-types.md`](references/16-mapped-types.md) |
| 17 | Conditional Types & `infer` | [`references/17-conditional-types-and-infer.md`](references/17-conditional-types-and-infer.md) |
| 18 | Template Literal Types | [`references/18-template-literal-types.md`](references/18-template-literal-types.md) |
| 19 | Functions | [`references/19-functions.md`](references/19-functions.md) |
| 20 | Classes | [`references/20-classes.md`](references/20-classes.md) |
| 21 | Enums | [`references/21-enums.md`](references/21-enums.md) |
| 22 | Modules & `import type` | [`references/22-modules-and-import-type.md`](references/22-modules-and-import-type.md) |
| 23 | Declaration Files | [`references/23-declaration-files.md`](references/23-declaration-files.md) |
| 24 | Runtime Validation at Boundaries | [`references/24-runtime-validation-at-boundaries.md`](references/24-runtime-validation-at-boundaries.md) |
| 25 | Async & Promise Types | [`references/25-async-and-promise-types.md`](references/25-async-and-promise-types.md) |
| 26 | Error Types | [`references/26-error-types.md`](references/26-error-types.md) |
| 27 | React Types (deferred to best-practice-react) | [`references/27-react-types-deferred-to-best-practice-react.md`](references/27-react-types-deferred-to-best-practice-react.md) |
| 28 | Node Types | [`references/28-node-types.md`](references/28-node-types.md) |
| 29 | Type-only Configuration | [`references/29-type-only-configuration.md`](references/29-type-only-configuration.md) |
| 30 | Testing Types | [`references/30-testing-types.md`](references/30-testing-types.md) |
| 31 | Library Publishing | [`references/31-library-publishing.md`](references/31-library-publishing.md) |
| 32 | Migrating from JS to TS | [`references/32-migrating-from-js-to-ts.md`](references/32-migrating-from-js-to-ts.md) |
| 33 | Comments | [`references/33-comments.md`](references/33-comments.md) |
| 34 | Naming Conventions | [`references/34-naming-conventions.md`](references/34-naming-conventions.md) |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells Claude/Cursor/Windsurf when to load `best-practice-ts`. When it loads, this index is what the agent reads first.
2. **Targeted reads.** When the agent needs one specific area (say, generics or discriminated unions), it opens only the matching chapter under `references/` — this keeps the context window small.
3. **Full review.** For a comprehensive review, the agent reads every referenced chapter file. Each one is exhaustive on its own topic with numbered rules, `> Why?` rationale, and `// bad` / `// good` examples.
4. **Prettier config.** Every code example in every chapter honors the user's Prettier configuration (no semicolons, single quotes, 2-space indent, no trailing commas, arrow-fn single param parenthesized, spaces inside object braces; for JSX: double-quoted attribute values, multiline closing `>` on its own line).

## Self-check

Before finishing any TypeScript change, verify:

- [ ] `tsconfig.json` includes every flag from [Chapter 1](#1-tsconfigjson--required-baseline); `strict` is not partially applied.
- [ ] No `any` appears in an exported signature ([9.1](#9-any-vs-unknown-vs-never)); `unknown` is narrowed before use.
- [ ] Every discriminated union has an `assertNever`/`satisfies Record` exhaustiveness check ([8.2](#8-discriminated-unions--exhaustiveness), [8.4](#8-discriminated-unions--exhaustiveness)).
- [ ] No `as` bypasses validation for external data — network, env, JSON, queue, or LLM tool input is validated at the boundary ([Chapter 24](#24-runtime-validation-at-boundaries)).
- [ ] No `!` non-null assertions or `as unknown as T` double-casts outside test fixtures ([10.2](#10-type-assertions-as--satisfies), [10.3](#10-type-assertions-as--satisfies)).
- [ ] `catch` variables are treated as `unknown` and narrowed with `instanceof` ([26.1](#26-error-types)).
- [ ] `import type`/inline `type` modifiers are used for every type-only import under `verbatimModuleSyntax` ([22.1](#22-modules--import-type), [22.2](#22-modules--import-type)).
- [ ] No `enum` or `const enum` was introduced; literal unions or `as const` objects were used instead ([Chapter 21](#21-enums)).
- [ ] Utility types (`Pick`, `Omit`, `Partial`, `Awaited`, etc.) are used to derive types instead of hand-duplicating shapes ([Chapter 15](#15-utility-types)).
- [ ] Config-like object literals use `satisfies` rather than a widening type annotation ([10.4](#10-type-assertions-as--satisfies)–[10.6](#10-type-assertions-as--satisfies), [29.1](#29-type-only-configuration)).
- [ ] Every code example and real diff honors the Prettier config: no semicolons at statement end, single quotes, no trailing commas, 2-space indent.

