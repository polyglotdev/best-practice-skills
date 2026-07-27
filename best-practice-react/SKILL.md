---
name: best-practice-react
description: Exhaustive React best practices for React 18.2+, forward-compatible with React 19 — function components, hooks, and Server Components in JS (.jsx) or TS (.tsx). Load for any React file, any component/hook/Server Component/Server Action work, or files with React imports. Stacks on best-practice-js for .jsx and best-practice-ts for .tsx. Enforces the user's Prettier config (double-quoted JSX attributes, single-quoted JS, no semicolons, no trailing commas, 2-space indent).
---

# best-practice-react

This skill governs React code written in JavaScript (`.jsx`) or TypeScript
(`.tsx`), targeting **React 18.2+** and written to remain forward-compatible
with **React 19**. It assumes function components, hooks, and — where the
framework supports them — **React Server Components (RSC)** and **Server
Actions**. Class components are covered only where they remain the only
option (Error Boundaries, §32).

This skill **stacks on top of**:

- `best-practice-js` — for all `.jsx` files, and for the non-JSX parts of any
  React codebase.
- `best-practice-ts` — for all `.tsx` files. Type-level rules (generics,
  `interface` vs `type`, utility types) live there, not here.

This skill does not repeat generic JS/TS rules. It only adds rules specific
to React: components, hooks, JSX, rendering, and the React ecosystem.

Every example in this file honors the user's Prettier configuration:

- JSX attribute values use **double quotes** (`className="foo"`), matching
  Airbnb React §Quotes.
- Every other string is **single-quoted**.
- **No semicolons.**
- **No trailing commas.**
- **2-space indentation.**
- Single arrow-function params are **parenthesized**: `(x) => x + 1`.
- In multiline JSX, the closing `>` sits **on its own line**
  (`bracketSameLine: false`).

Do not deviate from these formatting rules in any example, snippet, or
generated code, even if you recall a different convention from an older
version of the Airbnb guide.

## When to use

Load this skill whenever you are:

- Writing, reviewing, or refactoring a `.jsx` or `.tsx` file.
- Writing a file that imports `react`, `react-dom`, or a React meta-framework
  (Next.js, Remix, React Router v7, Gatsby, Expo/React Native).
- Designing a component API, a custom hook, a Server Component, or a Server
  Action.
- Reviewing pull requests that touch component trees, hooks, or JSX.

## Scope

- Function components, hooks (built-in and custom), JSX authoring rules.
- Component file organization, naming, props, refs, forms, lists, keys.
- Accessibility rules for JSX (`eslint-plugin-jsx-a11y` surface).
- React Server Components and Server Actions (Next.js App Router, Remix,
  Waku, and equivalents).
- Data fetching, state management, styling, and testing **decisions** as
  they relate to component architecture (not full API references for every
  library).
- Performance patterns specific to React's render model.

## Non-goals

- General JavaScript/TypeScript style (naming, imports, control flow,
  destructuring) — see `best-practice-js` / `best-practice-ts`.
- Build tooling (bundlers, Babel/SWC configuration).
- CSS language rules beyond "pick one styling strategy and stay consistent."
- Backend/database design beyond the shape of a Server Action's contract.
- React Native platform-specific APIs (only cross-cutting hook/component
  rules apply).

## Chapters

Each chapter is a self-contained reference file. Load the whole skill for a full review, or open a single chapter for a targeted question. Files live under `references/`.

| # | Chapter | File |
|---|---------|------|
| 1 | Basic Rules | [`references/01-basic-rules.md`](references/01-basic-rules.md) |
| 2 | Function Components | [`references/02-function-components.md`](references/02-function-components.md) |
| 3 | Class Components | [`references/03-class-components.md`](references/03-class-components.md) |
| 4 | Naming | [`references/04-naming.md`](references/04-naming.md) |
| 5 | Declaration & Exports | [`references/05-declaration-and-exports.md`](references/05-declaration-and-exports.md) |
| 6 | Alignment | [`references/06-alignment.md`](references/06-alignment.md) |
| 7 | Quotes | [`references/07-quotes.md`](references/07-quotes.md) |
| 8 | Spacing | [`references/08-spacing.md`](references/08-spacing.md) |
| 9 | Props | [`references/09-props.md`](references/09-props.md) |
| 9b | Prop Types (superseded by TypeScript) | [`references/09b-prop-types.md`](references/09b-prop-types.md) |
| 10 | Refs | [`references/10-refs.md`](references/10-refs.md) |
| 11 | Parentheses | [`references/11-parentheses.md`](references/11-parentheses.md) |
| 12 | Tags | [`references/12-tags.md`](references/12-tags.md) |
| 13 | Methods → Event Handlers | [`references/13-methods-event-handlers.md`](references/13-methods-event-handlers.md) |
| 14 | Ordering | [`references/14-ordering.md`](references/14-ordering.md) |
| 15 | Hooks — Rules of Hooks | [`references/15-hooks-rules-of-hooks.md`](references/15-hooks-rules-of-hooks.md) |
| 16 | useState | [`references/16-usestate.md`](references/16-usestate.md) |
| 16b | State (shape & philosophy) | [`references/16b-state.md`](references/16b-state.md) |
| 17 | useReducer | [`references/17-usereducer.md`](references/17-usereducer.md) |
| 18 | useEffect | [`references/18-useeffect.md`](references/18-useeffect.md) |
| 19 | useLayoutEffect | [`references/19-uselayouteffect.md`](references/19-uselayouteffect.md) |
| 20 | useRef | [`references/20-useref.md`](references/20-useref.md) |
| 21 | useMemo & useCallback | [`references/21-usememo-and-usecallback.md`](references/21-usememo-and-usecallback.md) |
| 22 | useContext | [`references/22-usecontext.md`](references/22-usecontext.md) |
| 23 | useId | [`references/23-useid.md`](references/23-useid.md) |
| 24 | useSyncExternalStore | [`references/24-usesyncexternalstore.md`](references/24-usesyncexternalstore.md) |
| 25 | useTransition & useDeferredValue | [`references/25-usetransition-and-usedeferredvalue.md`](references/25-usetransition-and-usedeferredvalue.md) |
| 26 | use() (React 19) | [`references/26-use-react-19.md`](references/26-use-react-19.md) |
| 27 | Custom Hooks | [`references/27-custom-hooks.md`](references/27-custom-hooks.md) |
| 28 | Lists & Keys | [`references/28-lists-and-keys.md`](references/28-lists-and-keys.md) |
| 29 | Conditional Rendering | [`references/29-conditional-rendering.md`](references/29-conditional-rendering.md) |
| 30 | Fragments | [`references/30-fragments.md`](references/30-fragments.md) |
| 31 | Portals | [`references/31-portals.md`](references/31-portals.md) |
| 32 | Error Boundaries | [`references/32-error-boundaries.md`](references/32-error-boundaries.md) |
| 33 | Suspense | [`references/33-suspense.md`](references/33-suspense.md) |
| 34 | Forms | [`references/34-forms.md`](references/34-forms.md) |
| 35 | Accessibility | [`references/35-accessibility.md`](references/35-accessibility.md) |
| 36 | Server Components (Next App Router / Remix RSC) | [`references/36-server-components-next-app-router-remix-rsc.md`](references/36-server-components-next-app-router-remix-rsc.md) |
| 37 | Server Actions (React 19 / Next) | [`references/37-server-actions-react-19-next.md`](references/37-server-actions-react-19-next.md) |
| 38 | Data Fetching | [`references/38-data-fetching.md`](references/38-data-fetching.md) |
| 39 | State Management | [`references/39-state-management.md`](references/39-state-management.md) |
| 40 | Styling | [`references/40-styling.md`](references/40-styling.md) |
| 41 | Testing | [`references/41-testing.md`](references/41-testing.md) |
| 42 | Performance | [`references/42-performance.md`](references/42-performance.md) |
| 43 | Modernization Notes (what Airbnb React says that is now outdated) | [`references/43-modernization-notes-what-airbnb-react-says-that-is-now-outdated.md`](references/43-modernization-notes-what-airbnb-react-says-that-is-now-outdated.md) |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells Claude/Cursor/Windsurf when to load `best-practice-react`. When it loads, this index is what the agent reads first.
2. **Targeted reads.** When the agent needs one specific area (say, `useEffect` rules or generics), it opens only the matching chapter under `references/` — this keeps the context window small.
3. **Full review.** For a comprehensive review, the agent reads every referenced chapter file. Each one is exhaustive on its own topic with numbered rules, `> Why?` rationale, and `// bad` / `// good` examples.
4. **Prettier config.** Every code example in every chapter honors the user's Prettier configuration (no semicolons, single quotes, 2-space indent, no trailing commas, arrow-fn single param parenthesized, spaces inside object braces; for JSX: double-quoted attribute values, multiline closing `>` on its own line).

## Self-check

Before returning any React code, verify:

- [ ] Every code block honors Prettier: single quotes for JS/TS, double
      quotes for JSX attributes, no semicolons, no trailing commas,
      2-space indent, `(x) => ...` parenthesized single params.
- [ ] No hook is called conditionally, in a loop, or after an early
      return (except `use()`, per §26.1).
- [ ] Every `useEffect`/`useMemo`/`useCallback` dependency array is
      exhaustive — no suppressed `exhaustive-deps` warnings.
- [ ] Every `useEffect` is actually justified per §18 — not standing in
      for a render-time computation, an event handler, or a data fetch
      that a framework loader/RSC should own instead.
- [ ] Every list render has a stable, data-derived `key` — never array
      index for a list that can reorder/filter/grow (§28).
- [ ] Interactive elements are semantic (`<button type="...">`, `<a href>`,
      native inputs) — never a `<div onClick>` (§35.1).
- [ ] Every image has `alt`; every form control has an associated label;
      every icon-only button has an `aria-label` (§35).
- [ ] `"use client"` appears only where state/effects/refs/handlers/browser
      APIs are actually used, and is placed as low in the tree as possible
      (§36).
- [ ] No Client-only library is imported into a Server Component module
      (§36.6).
- [ ] No hand-rolled `useEffect` + `fetch` + `useState` data cache where a
      framework loader, `react-query`, or `swr` is available (§38.2).
- [ ] Server Actions validate input with `zod`, return a typed result
      union, and re-check authorization — never trust `FormData` or the
      caller's identity blindly (§37).
- [ ] `useMemo`/`useCallback` appear only for one of the three legitimate
      reasons in §21 — not applied by default "just in case."
- [ ] Loading, empty, and error states are three distinct UI branches, not
      collapsed into one check (§38.5).
- [ ] Every fetch has a timeout and validates its response shape (§38.3,
      §38.4).
- [ ] Colors meet WCAG AA contrast; focus is never removed without a
      visible replacement (§35.5, §35.9).
- [ ] Tests query by role via Testing Library, use `userEvent`, and assert
      on user-visible behavior — not internals or framework details
      (§41).
- [ ] No `!important`, no hard-coded hex colors, and only one styling
      strategy is used throughout the file (§40).
- [ ] Any memoization (`memo`, `useMemo`, `useCallback`) is tied to a
      measured or clearly-justified need, not applied speculatively
      (§42.1, §42.6, §42.7).
- [ ] No class component appears except an Error Boundary (§32, §43.1).
- [ ] Forms disable/show a pending state on submit and use uncontrolled
      inputs or a form library appropriately for their complexity (§34,
      §37.6).

