<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 11. Parentheses

Wrapping multiline JSX in parentheses is handled by Prettier automatically
based on the printed width and structure; you do not need to add or remove
parentheses by hand. The one rule worth stating explicitly:

## 11.1 Wrap a JSX expression in parentheses when it spans multiple lines inside a return, ternary, or logical expression.

> Why? Parentheses make the JSX block visually distinct from surrounding
> control flow and prevent automatic semicolon insertion from breaking a
> `return` split across lines.

```jsx
// bad — return and JSX on awkward lines invite ASI bugs
function Card() {
  return <MyComponent variant="long body" foo="bar">
    <MyChild />
  </MyComponent>
}
```

```jsx
// good
function Card() {
  return (
    <MyComponent variant="long body" foo="bar">
      <MyChild />
    </MyComponent>
  )
}

// good — single line JSX needs no wrapping
function Card() {
  const body = <div>hello</div>
  return <MyComponent>{body}</MyComponent>
}
```
