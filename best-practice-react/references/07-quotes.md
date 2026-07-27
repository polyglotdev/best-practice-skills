<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 7. Quotes

## 7.1 Use double quotes for JSX attribute values; use single quotes for every other string in JS/TS, including values inside `{}` expressions.

> Why? This matches the project's Prettier config (`jsxSingleQuote: false`,
> `singleQuote: true`) and mirrors how HTML attributes are typically
> quoted, while keeping ordinary JS/TS strings visually distinct from
> markup.

```jsx
// bad
<Foo bar='bar' />

// bad — this is a JS string INSIDE an expression, must be single-quoted
<Foo style={{ left: "20px" }} />
```

```jsx
// good
<Foo bar="bar" />

// good
<Foo style={{ left: '20px' }} />
```
