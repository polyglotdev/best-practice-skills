<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 9. Props

## 9.1 Always use camelCase for prop names, or PascalCase if the prop value is itself a React component.

> Why? camelCase matches ordinary JS identifier convention; PascalCase for
> a component-valued prop signals "this value is a component, not data" at
> the call site.

```jsx
// bad
<Foo
  UserName="hello"
  phone_number={12345678}
/>
```

```jsx
// good
<Foo
  userName="hello"
  phoneNumber={12345678}
  Component={SomeComponent}
/>
```

## 9.2 Omit the prop value when it is explicitly `true`.

> Why? `hidden={true}` and `hidden` are equivalent; the shorthand is
> shorter and reads closer to an HTML boolean attribute.

```jsx
// bad
<Foo hidden={true} />
```

```jsx
// good
<Foo hidden />
```

## 9.3 Always include a meaningful `alt` prop on `<img>`; use `alt=""` only for purely decorative images.

> Why? Screen-reader users rely on `alt` text to know what an image
> conveys. Omitting it, or filling it with noise, breaks accessibility.
> Enforced by `eslint-plugin-jsx-a11y`'s `alt-text` rule — see §35.

```jsx
// bad
<img src="hello.jpg" />
```

```jsx
// good
<img src="hello.jpg" alt="Ada waving hello" />

// good — decorative image
<img src="divider.svg" alt="" />
```

## 9.4 Do not use "image", "photo", or "picture" inside `alt` text.

> Why? Screen readers already announce the element as an image; repeating
> that in the text is redundant noise. Enforced by
> `jsx-a11y/img-redundant-alt`.

```jsx
// bad
<img src="hello.jpg" alt="Picture of Ada waving hello" />
```

```jsx
// good
<img src="hello.jpg" alt="Ada waving hello" />
```

## 9.5 Make every prop's requiredness and shape explicit in its type; never accept an untyped catch-all `object` or `any`.

> Why? A loosely typed prop defeats the entire purpose of typing
> components — callers get no guidance and typos go undetected until
> runtime.

```tsx
// bad
type CardProps = {
  data: any
}
```

```tsx
// good
type CardProps = {
  data: {
    id: string
    title: string
    tags: string[]
  }
}
```

## 9.6 Give every non-required prop a real default via a JS default parameter, not a separate `defaultProps` object.

> Why? `defaultProps` on function components is deprecated by React itself
> as of React 18.3 in favor of JS default parameters, which work
> identically and need no separate static property to keep in sync.

```jsx
// bad — defaultProps on a function component (deprecated by React)
function Badge({ tone, children }) {
  return <span className={tone}>{children}</span>
}
Badge.defaultProps = {
  tone: 'neutral'
}
```

```jsx
// good
function Badge({ tone = 'neutral', children }) {
  return <span className={tone}>{children}</span>
}
```

## 9.7 Use spread props sparingly, and only when every spread key is known and intentional.

> Why? Blind prop spreading (`{...props}`) forwards attributes you didn't
> intend to expose, makes the component's real contract invisible at the
> call site, and can leak internal-only props onto DOM nodes.

```jsx
// bad — forwards everything, including props the component doesn't want to expose
function Button(props) {
  return <button {...props} />
}
```

```jsx
// good — pull out what you consume, forward only what's left intentionally
function Button({ variant, ...rest }) {
  return <button className={variant} {...rest} />
}
```

## 9.8 In a props-forwarding HOC or thin wrapper, exclude irrelevant props before spreading.

> Why? Otherwise unrelated internal props (e.g. `isLoading` used only by the
> wrapper) leak onto the wrapped component or the DOM.

```jsx
// bad
function withLoading(Wrapped) {
  return function WithLoading(props) {
    return <Wrapped {...props} />
  }
}
```

```jsx
// good
function withLoading(Wrapped) {
  function WithLoading({ isLoading, ...rest }) {
    if (isLoading) return <Spinner />
    return <Wrapped {...rest} />
  }
  return WithLoading
}
```
