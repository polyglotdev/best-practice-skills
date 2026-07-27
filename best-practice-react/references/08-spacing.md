<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 8. Spacing

Spacing (self-closing tag spacing, curly-brace padding, indentation) is
delegated to Prettier. Do not hand-tune it. The output you should expect:

```jsx
// bad
<Foo/>

// bad
<Foo bar={ baz } />
```

```jsx
// good
<Foo />

// good
<Foo bar={baz} />
```
