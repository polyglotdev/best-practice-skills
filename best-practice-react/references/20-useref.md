<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 20. useRef

## 20.1 Use `useRef` for values that must persist across renders but whose changes should never trigger a re-render (timer ids, previous values, imperative handles, mutable flags).

> Why? Unlike state, updating `ref.current` does not schedule a re-render.
> That is exactly the behavior you want for bookkeeping values the UI
> doesn't directly display.

```jsx
// bad — using state for a value the UI never displays, causing extra renders
function Stopwatch() {
  const [intervalId, setIntervalId] = useState(null)
  function start() {
    setIntervalId(setInterval(tick, 1000))
  }
}
```

```jsx
// good
function Stopwatch() {
  const intervalIdRef = useRef(null)
  function start() {
    intervalIdRef.current = setInterval(tick, 1000)
  }
  function stop() {
    clearInterval(intervalIdRef.current)
  }
}
```

## 20.2 Do not use a ref for anything the UI needs to display; use state instead.

> Why? Because mutating `ref.current` doesn't re-render, using a ref for
> display data means the screen silently goes stale.

```jsx
// bad — UI never updates because refs don't trigger renders
function Counter() {
  const countRef = useRef(0)
  function handleClick() {
    countRef.current += 1
  }
  return <button onClick={handleClick}>{countRef.current}</button>
}
```

```jsx
// good
function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount((c) => c + 1)}>{count}</button>
}
```

## 20.3 Use `useImperativeHandle` sparingly, and only alongside a ref prop, to expose a deliberately small imperative API from a component.

> Why? Exposing an entire DOM node or internal instance invites callers to
> reach in and mutate things you don't control. A curated imperative handle
> keeps the component's contract intentional.

```tsx
// bad — exposes the raw DOM node, callers can do anything to it
function VideoPlayer({ ref, src }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  return <video ref={videoRef ?? ref} src={src} />
}
```

```tsx
// good — exposes exactly play/pause, nothing else
type VideoPlayerHandle = {
  play: () => void
  pause: () => void
}

function VideoPlayer({ ref, src }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useImperativeHandle(ref, () => ({
    play: () => videoRef.current?.play(),
    pause: () => videoRef.current?.pause()
  }))

  return <video ref={videoRef} src={src} />
}
```
