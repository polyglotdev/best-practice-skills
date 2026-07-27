<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 18. Template Literal Types

## 18.1 Use template literal types to model string formats instead of a loose `string` when the format is significant to correctness.

> Why? A template literal type rejects malformed strings at compile time
> for call sites that use literals, catching typos that a plain `string`
> parameter cannot.

```ts
// bad
function setCssVar(name: string, value: string) {}

// good
type CssVarName = `--${string}`
function setCssVar(name: CssVarName, value: string) {}
setCssVar('--color-primary', '#000') // ok
setCssVar('color-primary', '#000') // Error
```

## 18.2 Combine template literal types with `Uppercase`/`Lowercase`/`Capitalize`/`Uncapitalize` for casing transforms instead of hand-writing the casing logic in the type.

```ts
// good
type EventName<T extends string> = `on${Capitalize<T>}`
type ClickEvent = EventName<'click'> // 'onClick'
```

## 18.3 Use template literal types to derive a union of valid route strings from a route-parameter object, rather than typing routes as a plain `string`.

```ts
// good
type Route = `/users/${string}` | `/orders/${string}` | '/'
function navigate(route: Route) {}
```
