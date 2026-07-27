<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 40. Styling

## 40.1 Pick exactly one styling strategy per project — Tailwind, CSS Modules, vanilla-extract, or a single CSS-in-JS library — and do not mix strategies.

> Why? Mixing strategies means specificity and build-tooling conflicts
> that are hard to debug, plus two mental models for "where does this
> style live" across the codebase.

```jsx
// bad — Tailwind utility classes and a CSS-in-JS library both used in the same component
const StyledCard = styled.div`
  padding: 16px;
`
function Card({ children }) {
  return <StyledCard className="rounded-lg shadow-md">{children}</StyledCard>
}
```

```jsx
// good — one strategy, consistently
function Card({ children }) {
  return <div className="rounded-lg p-4 shadow-md">{children}</div>
}
```

## 40.2 Do not use inline `style={{ ... }}` for values that are static; express them as a CSS class instead.

> Why? Inline styles can't be themed, media-queried, or overridden by
> normal CSS specificity rules, and they bypass whatever styling strategy
> the rest of the app uses.

```jsx
// bad — static styling values inlined
function Card({ children }) {
  return <div style={{ padding: 16, borderRadius: 8, boxShadow: '0 1px 2px #0002' }}>{children}</div>
}
```

```jsx
// good
function Card({ children }) {
  return <div className="card">{children}</div>
}
```

## 40.3 Reserve inline `style` for genuinely computed, per-instance values — positions, dynamic widths/heights, animation-driven transforms.

> Why? These values are inherently instance-specific and can't be
> expressed as a static class ahead of time; inline `style` is the correct
> tool exactly here.

```jsx
// good — position depends on runtime measurement, a static class can't express it
function Tooltip({ top, left, children }) {
  return (
    <div className="tooltip" style={{ top, left }}>
      {children}
    </div>
  )
}
```

## 40.4 Keep design tokens (colors, spacing, radii, type scale) in CSS custom properties or the Tailwind config — never as literal values scattered across components.

> Why? A literal `#3366ff` repeated across fifty components can't be
> updated in one place; a token (`var(--color-primary)` or a Tailwind
> theme color) can.

```jsx
// bad — the same brand color hard-coded in multiple components
function PrimaryButton({ children }) {
  return <button style={{ background: '#3366ff' }}>{children}</button>
}
```

```jsx
// good
function PrimaryButton({ children }) {
  return <button className="bg-primary">{children}</button>
}
```

## 40.5 With Tailwind, compose conditional classes with `clsx` (or a `cn` helper) combined with `tailwind-merge`, rather than manual string concatenation.

> Why? Manual string concatenation for conditional classes gets unreadable
> fast, and doesn't resolve conflicting Tailwind utilities (`p-2` vs
> `p-4`) the way `tailwind-merge` does.

```jsx
// bad — manual concatenation, and conflicting padding utilities both survive
function Button({ isActive, className }) {
  return <button className={'btn ' + (isActive ? 'btn-active ' : '') + className}>Go</button>
}
```

```jsx
// good
function Button({ isActive, className }) {
  return <button className={cn('btn', isActive && 'btn-active', className)}>Go</button>
}
```

## 40.6 Extract long, repeated class strings to a `const` at module scope instead of repeating them inline across the file.

> Why? A repeated 15-utility class string is unreadable inline, and
> duplicating it across multiple elements means a fix has to be applied
> in every place it was pasted.

```jsx
// bad — same long class string repeated in three places in the file
function Card() {
  return <div className="rounded-lg border border-gray-200 p-4 shadow-sm">…</div>
}
function OtherCard() {
  return <div className="rounded-lg border border-gray-200 p-4 shadow-sm">…</div>
}
```

```jsx
// good
const cardStyles = 'rounded-lg border border-gray-200 p-4 shadow-sm'

function Card() {
  return <div className={cardStyles}>…</div>
}
function OtherCard() {
  return <div className={cardStyles}>…</div>
}
```

## 40.7 Never hard-code a hex/RGB color value directly in a component; use a design token.

> Why? See 40.4 — hard-coded colors can't be swapped for a theme change
> (including dark mode) and drift out of sync with the design system over
> time.

```jsx
// bad
<div style={{ color: '#e11d48' }}>Error</div>
```

```jsx
// good
<div className="text-danger">Error</div>
```

## 40.8 Keep global stylesheets limited to reset rules, design tokens, and base typography; component-specific styles live scoped to the component.

> Why? Global rules that target component-level concerns (`.card { ... }`
> in a global stylesheet) create action-at-a-distance bugs where editing
> one file breaks an unrelated component elsewhere in the app.

```css
/* bad — component-specific rule in a global stylesheet */
.card {
  padding: 16px;
  border-radius: 8px;
}
```

```css
/* good — global.css limited to resets, tokens, and base typography */
:root {
  --color-primary: #3366ff;
  --radius-md: 8px;
}
body {
  font-family: var(--font-sans);
}
```

## 40.9 Prefer logical CSS properties (`padding-inline`, `margin-block`, `inset-inline-start`) over physical ones (`padding-left`, `margin-top`) to support right-to-left layouts.

> Why? Logical properties automatically flip direction under `dir="rtl"`;
> physical properties require a separate RTL override for every rule that
> uses them.

```css
/* bad — breaks in RTL layouts without a separate override */
.card {
  padding-left: 16px;
  margin-top: 8px;
}
```

```css
/* good — flips automatically under dir="rtl" */
.card {
  padding-inline-start: 16px;
  margin-block-start: 8px;
}
```

## 40.10 Never use `!important` in application CSS; restructure selectors or the cascade instead.

> Why? `!important` wins by brute force rather than by correct
> specificity, and once one rule uses it, overriding it later requires
> another `!important`, starting an arms race that makes the cascade
> unmaintainable.

```css
/* bad */
.button {
  color: blue !important;
}
```

```css
/* good — fix the specificity/ordering issue instead */
.button {
  color: var(--color-primary);
}
```
