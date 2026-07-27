<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 30. Fragments

## 30.1 Use `<>...</>` for a fragment with no need for a key; use `<React.Fragment key={...}>` only when the fragment needs a key (e.g. inside a `.map()`).

> Why? The shorthand is more concise and is all you need when there's no
> key to attach; `React.Fragment` is required syntax only because the
> shorthand doesn't accept attributes.

```jsx
// bad — verbose Fragment used where the shorthand would do
function Labels() {
  return (
    <React.Fragment>
      <dt>Name</dt>
      <dd>Ada</dd>
    </React.Fragment>
  )
}
```

```jsx
// good
function Labels() {
  return (
    <>
      <dt>Name</dt>
      <dd>Ada</dd>
    </>
  )
}

// good — key required, so the full Fragment form is necessary
function DefinitionList({ entries }) {
  return (
    <dl>
      {entries.map((entry) => (
        <Fragment key={entry.id}>
          <dt>{entry.term}</dt>
          <dd>{entry.definition}</dd>
        </Fragment>
      ))}
    </dl>
  )
}
```

## 30.2 Use a fragment instead of an unnecessary wrapper `<div>` when the extra DOM node has no styling or semantic purpose.

> Why? Superfluous wrapper `div`s bloat the DOM, can break CSS that assumes
> a specific parent-child relationship (flex/grid children), and offer no
> benefit over a fragment.

```jsx
// bad — div only exists to satisfy "one root element"
function NameFields() {
  return (
    <div>
      <input name="first" />
      <input name="last" />
    </div>
  )
}
```

```jsx
// good
function NameFields() {
  return (
    <>
      <input name="first" />
      <input name="last" />
    </>
  )
}
```
