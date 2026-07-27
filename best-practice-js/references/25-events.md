<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 25. Events

## 25.1 When attaching data payloads to events (DOM events, Node
`EventEmitter`, or a custom pub/sub), pass a single object payload
instead of a raw value.

> Why? A single payload object lets you add fields later without
> touching every dispatch and every listener signature.

```js
// bad
emitter.emit('uploadProgress', percentComplete)

emitter.on('uploadProgress', (percentComplete) => {
  // ...
})

// good
emitter.emit('uploadProgress', { percentComplete })

emitter.on('uploadProgress', ({ percentComplete }) => {
  // ...
})
```

## 25.2 Always remove listeners you add, using `AbortSignal` where
available instead of manually tracking handler references.

> Why? An `AbortController` lets you cancel a whole group of listeners
> with one call, instead of keeping named references to each handler
> just to call `removeEventListener` later.

```js
// bad — must remember the exact function reference to ever remove it
function handleClick() {
  // ...
}
button.addEventListener('click', handleClick)
// later, easy to forget:
button.removeEventListener('click', handleClick)

// good
const controller = new AbortController()

button.addEventListener(
  'click',
  () => {
    // ...
  },
  { signal: controller.signal }
)

// stops the listener (and any others sharing the signal) in one call
controller.abort()
```

## 25.3 Name custom event types as past-tense or noun phrases that
describe what happened, not commands.

```js
// bad — sounds like a command, not a notification
emitter.emit('saveUser', user)

// good
emitter.emit('userSaved', user)
```

---
