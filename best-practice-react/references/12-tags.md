<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 12. Tags

## 12.1 Always self-close tags that have no children.

> Why? A self-closed tag communicates "this element intentionally has no
> children" at a glance, and avoids an easy-to-miss empty-children bug.

```jsx
// bad
<Foo variant="stuff"></Foo>
```

```jsx
// good
<Foo variant="stuff" />
```

## 12.2 If a component's props span multiple lines, put the closing tag/bracket on its own line.

> Why? This is what the project's Prettier config produces
> (`bracketSameLine: false`) and keeps multi-prop components visually
> scannable.

```jsx
// bad
<Foo
  bar="bar"
  baz="baz" />
```

```jsx
// good
<Foo
  bar="bar"
  baz="baz"
/>
```

## 12.3 Never use a lowercase tag name for a component; lowercase tags are reserved for native DOM elements.

> Why? JSX uses case to decide whether a tag compiles to
> `createElement('div', ...)` or `createElement(Div, ...)`. A component
> referenced in lowercase silently renders as a broken DOM element instead
> of throwing at compile time.

```jsx
// bad
function card() {
  return <div />
}

const el = <card />
```

```jsx
// good
function Card() {
  return <div />
}

const el = <Card />
```
