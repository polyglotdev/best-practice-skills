<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 6. Alignment

Alignment of JSX attributes and closing brackets is fully delegated to
Prettier — do not hand-format it. The relevant behavior with this project's
config (`bracketSameLine: false`):

```jsx
// bad — hand-aligned, fights Prettier
<Foo superLongParam="bar"
     anotherSuperLongParam="baz" />
```

```jsx
// good — Prettier's output: one prop per line, closing `>` on its own line
<Foo
  superLongParam="bar"
  anotherSuperLongParam="baz"
/>

// good — short enough to stay on one line
<Foo bar="bar" />
```

Do not manually re-wrap or re-indent JSX that Prettier would reformat on
save; write the simplest version and let the formatter own layout.
