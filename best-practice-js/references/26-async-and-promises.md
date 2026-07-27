<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 26. Async & Promises

## 26.1 Prefer `async`/`await` over raw `.then()` chains.

> Why? `await` reads top-to-bottom like synchronous code, and `try`/
> `catch` handles errors with the same construct you already use
> everywhere else — a `.then()` chain forces you to track control flow
> across nested callbacks.

```js
// bad
function loadUser(id) {
  return fetchUser(id).then((user) => {
    return fetchPosts(user.id).then((posts) => {
      return { user, posts }
    })
  })
}

// good
async function loadUser(id) {
  const user = await fetchUser(id)
  const posts = await fetchPosts(user.id)
  return { user, posts }
}
```

## 26.2 Run independent async work concurrently with
`Promise.all`/`Promise.allSettled`, not sequential `await`.

> Why? Sequential `await` on unrelated work serializes latency that
> could otherwise overlap. `Promise.allSettled` is the right choice when
> individual failures shouldn't cancel the whole batch.

```js
// bad — pays the latency of both requests, one after another
async function loadDashboard(userId) {
  const profile = await fetchProfile(userId)
  const stats = await fetchStats(userId)
  return { profile, stats }
}

// good — runs concurrently
async function loadDashboard(userId) {
  const [profile, stats] = await Promise.all([
    fetchProfile(userId),
    fetchStats(userId)
  ])
  return { profile, stats }
}

// good — tolerates individual failures
async function loadWidgets(ids) {
  const results = await Promise.allSettled(ids.map((id) => fetchWidget(id)))
  return results
    .filter((result) => result.status === 'fulfilled')
    .map((result) => result.value)
}
```

## 26.3 Use `Promise.any` when you want the first success among
redundant sources, and race timeouts with `AbortSignal.timeout`, not
manual `setTimeout` + `Promise.race` plumbing.

```js
// good — first mirror to respond wins
const fastest = await Promise.any([
  fetch('https://mirror-a.example.com/data'),
  fetch('https://mirror-b.example.com/data')
])

// good — native request timeout, no manual timer bookkeeping
const response = await fetch('https://api.example.com/data', {
  signal: AbortSignal.timeout(5000)
})
```

## 26.4 Never leave a rejected promise unhandled.

> Why? An unhandled rejection crashes a Node process (as of Node 15+)
> and is silently swallowed in browsers otherwise, hiding real failures.

```js
// bad
fetchUser(id)

// good
try {
  await fetchUser(id)
} catch (error) {
  logger.error('failed to fetch user', { cause: error })
}
```

## 26.5 Don't mix `await` and `.then()` in the same function.

> Why? Mixing styles forces the reader to track two different control-
> flow mental models in one place.

```js
// bad
async function loadUser(id) {
  const user = await fetchUser(id)
  return fetchPosts(user.id).then((posts) => ({ user, posts }))
}

// good
async function loadUser(id) {
  const user = await fetchUser(id)
  const posts = await fetchPosts(user.id)
  return { user, posts }
}
```

## 26.6 Avoid `async` functions with no `await` inside; they're a
sign the function doesn't need to be async.

```js
// bad — needlessly wraps a sync value in a promise
async function double(x) {
  return x * 2
}

// good
function double(x) {
  return x * 2
}
```

## 26.7 Use an `AbortController` to make async work cancelable, and
plumb the signal through every layer that awaits.

```js
async function search(query, signal) {
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
    signal
  })
  return response.json()
}

const controller = new AbortController()
search('cats', controller.signal)

// user navigated away — cancel the in-flight request
controller.abort()
```

---
