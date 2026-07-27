<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 19. useLayoutEffect

## 19.1 Use `useLayoutEffect` only when you must read layout (DOM measurements) and synchronously apply a DOM mutation before the browser paints; otherwise use `useEffect`.

> Why? `useLayoutEffect` runs synchronously after DOM mutations but before
> the browser paints, blocking visual updates until it finishes. Using it
> by default (instead of `useEffect`) adds unnecessary blocking work and
> can hurt perceived performance.

```jsx
// bad — useLayoutEffect for something that doesn't need to block paint
function Logger({ value }) {
  useLayoutEffect(() => {
    console.log('value changed', value)
  }, [value])
}
```

```jsx
// good — useLayoutEffect reserved for measure-then-mutate-before-paint
function Tooltip({ targetRef }) {
  const tooltipRef = useRef(null)

  useLayoutEffect(() => {
    const { bottom } = targetRef.current.getBoundingClientRect()
    tooltipRef.current.style.top = `${bottom}px`
  }, [targetRef])

  return <div ref={tooltipRef} className="tooltip" />
}
```

## 19.2 On the server (SSR/RSC), `useLayoutEffect` never runs and React warns; guard it or use `useEffect` for code that must also run during server rendering's client hydration pass.

> Why? Server rendering has no DOM to measure, so React emits a warning if
> `useLayoutEffect` is reached during SSR. If the component can render on
> the server, avoid the warning by deferring purely visual layout logic
> until the client, or by using an isomorphic wrapper.

```jsx
// bad — warns during SSR
function Tooltip() {
  useLayoutEffect(() => {
    measure()
  }, [])
}
```

```jsx
// good — isomorphic hook: useLayoutEffect on the client, no-op on the server
const useIsomorphicLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect

function Tooltip() {
  useIsomorphicLayoutEffect(() => {
    measure()
  }, [])
}
```
