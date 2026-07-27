# best-practice-skills

Three exhaustive, Airbnb-depth best-practice skills for modern JavaScript,
TypeScript, and React — packaged as [skills.sh](https://www.skills.sh)–compatible
Agent Skills that work in **Claude Code**, **Cursor** (chat + Agent mode),
**Windsurf**, and **JetBrains** (via the Claude plugin).

Every code example is written to conform to this Prettier configuration
(`.prettierrc.json`) — never adding semicolons, trailing commas, or double
quotes to JS/TS strings:

```json
{
  "arrowParens": "always",
  "bracketSameLine": false,
  "bracketSpacing": true,
  "embeddedLanguageFormatting": "auto",
  "htmlWhitespaceSensitivity": "css",
  "insertPragma": false,
  "jsxSingleQuote": false,
  "printWidth": 80,
  "proseWrap": "preserve",
  "quoteProps": "as-needed",
  "requirePragma": false,
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "none",
  "useTabs": false,
  "vueIndentScriptAndStyle": false
}
```

## Structure

Each skill uses the recommended slim-index + chapter-references pattern:

```
best-practice-<lang>/
├── SKILL.md                # short index (<200 lines): frontmatter,
│                           # When to use, Scope, Non-goals, chapter
│                           # table, Self-check
└── references/
    ├── prettier.md         # the exact Prettier config
    ├── 01-<chapter>.md     # one chapter per file, numbered
    ├── 02-<chapter>.md
    └── ...
```

The agent loads `SKILL.md` first (small, description-driven auto-load), then
opens only the chapter files it needs for the task at hand. For a full
review, it reads every chapter. Together the reference files hold roughly
**12,500 lines** of numbered rules, `> Why?` rationales, and `// bad` /
`// good` examples — modeled on the depth of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) but
modernized for ES2022+, Node 20+, and React 18/19.

## Skills in this repo

| Slash command             | Skill                  | Chapters | Use it when                                                                 |
| ------------------------- | ---------------------- | -------- | --------------------------------------------------------------------------- |
| `/best-practice-js`       | `best-practice-js`     | 34       | Reviewing, writing, or refactoring plain JavaScript (Node or browser).      |
| `/best-practice-ts`       | `best-practice-ts`     | 34       | Writing or reviewing TypeScript — libraries, apps, backends, or React apps. |
| `/best-practice-react`    | `best-practice-react`  | 43       | Any React work in JS **or** TS (components, hooks, RSC, Next.js, Vite).     |

## Install (global — recommended)

```bash
# Install all three globally so Claude Code / Cursor / Windsurf / JetBrains pick them up
npx skills add <your-github-user>/best-practice-skills -g -y

# Or install a single skill from the repo
npx skills add <your-github-user>/best-practice-skills --skill best-practice-js -g -y
npx skills add <your-github-user>/best-practice-skills --skill best-practice-ts -g -y
npx skills add <your-github-user>/best-practice-skills --skill best-practice-react -g -y
```

Globally installed skills land in `~/.claude/skills/<skill-name>/` and are
picked up automatically by Claude Code, Cursor, Windsurf, and the JetBrains
plugin — no restart or per-editor config required.

## Install (project-scoped)

Copy any skill folder into your repo under `.claude/skills/<skill-name>/`.
Cursor, Claude Code, and Windsurf will read it when opened in that project.
Recommended when you want the skill checked in with the code so the whole
team gets it.

```text
your-repo/
└── .claude/
    └── skills/
        ├── best-practice-js/{SKILL.md,references/}
        ├── best-practice-ts/{SKILL.md,references/}
        └── best-practice-react/{SKILL.md,references/}
```

## Codex / ChatGPT Codex CLI

Codex does not natively read `SKILL.md`, but the files are plain markdown.
Two supported paths:

1. **Project rules** — copy the whole skill folder into your repo and point
   Codex at it via `AGENTS.md` at the repo root:

   ```md
   # AGENTS.md
   When editing TypeScript, follow the rules in
   `.claude/skills/best-practice-ts/SKILL.md` and its `references/` chapters.
   When editing React, follow `.claude/skills/best-practice-react/SKILL.md`.
   When editing plain JavaScript, follow `.claude/skills/best-practice-js/SKILL.md`.
   Never violate `.prettierrc.json`.
   ```

2. **On-demand** — paste at the start of a Codex session:
   `Follow the rules in .claude/skills/best-practice-ts/SKILL.md for this task.`

## Invocation

Once installed, invoke from your editor's chat panel:

```text
/best-practice-js review the open file
/best-practice-ts add types to this module and tighten null-handling
/best-practice-react split this component and lift state to a reducer
```

Or let the agent load them automatically based on the file extensions and
task keywords in each skill's `description`.

In **Cursor Agent mode** or **Windsurf Flows**, invoke the skill on the
**first turn** of the session — mid-session invocations only affect
subsequent turns.

## What each skill covers

### `best-practice-js` (34 chapters)

Types, References, Objects, Arrays, Destructuring, Strings, Functions,
Arrow Functions, Classes & Constructors, Modules, Iterators and Generators,
Properties, Variables, Hoisting, Comparison Operators & Equality, Blocks,
Control Statements, Comments, Whitespace (deferred to Prettier), Commas
(deferred to Prettier), Semicolons (deferred to Prettier), Type Casting &
Coercion, Naming Conventions, Accessors, Events, Async & Promises, Error
Handling, Standard Library, Node.js specifics, Browser specifics, Security,
Performance, Testing, Tooling defaults.

### `best-practice-ts` (34 chapters)

`tsconfig.json` baseline, Types vs Interfaces, Primitive & Literal Types,
Objects & Records, Arrays & Tuples, Union Types, Intersection Types,
Discriminated Unions & Exhaustiveness, `any` vs `unknown` vs `never`, Type
Assertions (`as`, `!`, `satisfies`), Type Narrowing, Nullability, Readonly &
Immutability, Generics, Utility Types, Mapped Types, Conditional Types &
`infer`, Template Literal Types, Functions, Classes, Enums, Modules &
`import type`, Declaration Files, Runtime Validation at Boundaries, Async &
Promise Types, Error Types, React Types (deferred), Node Types, Type-only
Configuration, Testing Types, Library Publishing, Migrating from JS to TS,
Comments, Naming Conventions.

### `best-practice-react` (43 chapters)

Basic Rules, Function Components, Class Components (Error Boundaries only),
Naming, Declaration & Exports, Alignment/Quotes/Spacing (deferred to
Prettier), Props, Refs, Parentheses, Tags, Event Handlers, Component File
Ordering, Rules of Hooks, `useState`, `useReducer`, `useEffect`,
`useLayoutEffect`, `useRef`, `useMemo` & `useCallback`, `useContext`,
`useId`, `useSyncExternalStore`, `useTransition` & `useDeferredValue`,
`use()` (React 19), Custom Hooks, Lists & Keys, Conditional Rendering,
Fragments, Portals, Error Boundaries, Suspense, Forms, Accessibility, Server
Components, Server Actions, Data Fetching, State Management, Styling,
Testing, Performance, Modernization Notes.

## Design notes

- **Airbnb depth, modern content.** Modeled on the depth and structure of
  the Airbnb JavaScript Style Guide — every rule is numbered per chapter
  (e.g. `### 3.1`, `### 3.2`), justified with a `> Why?`, and shown with
  `// bad` + `// good` examples. But the content is modernized: ES2022+
  idioms, `async`/`await`, native `fetch`/`AbortController`, `#private`
  class fields, `import type`, React hooks, RSC, Server Actions.
- **Prettier is source of truth for formatting.** Every code example
  complies with the config above. Where Airbnb's guide recommends the
  opposite (semicolons, trailing commas, double quotes for JS), this skill
  silently follows the Prettier config instead. Chapters like
  "Whitespace / Commas / Semicolons" simply defer to Prettier.
- **Procedural, not descriptive.** Each rule tells the agent what to do,
  what to reject, and how to rewrite — usable as a runbook, not just a
  reference.
