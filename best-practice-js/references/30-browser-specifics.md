<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 30. Browser specifics

## 30.1 Use native `fetch` with `AbortController` instead of `XMLHttpRequest`.

```js
// bad
const xhr = new XMLHttpRequest()
xhr.open('GET', '/api/data')
xhr.onload = () => console.log(xhr.responseText)
xhr.send()

// good
const response = await fetch('/api/data')
const data = await response.json()
```

## 30.2 Never assign untrusted content to `innerHTML`; use
`textContent` or DOM APIs, and sanitize explicitly when HTML really is
required.

> Why? `innerHTML` parses and executes its input as HTML/script,
> making it a direct cross-site-scripting (XSS) vector whenever the
> content includes anything a user controlled.

```js
// bad
element.innerHTML = `Hello, ${userSuppliedName}`

// good
element.textContent = `Hello, ${userSuppliedName}`

// good — only when HTML is genuinely required, sanitize explicitly first
element.innerHTML = sanitizeHtml(trustedRichTextFromCms)
```

## 30.3 Store only non-sensitive, non-PII data in `localStorage`/
`sessionStorage`.

> Why? Anything in Web Storage is readable by any script running on
> the page, including injected third-party or compromised scripts — it
> is not a secure place for tokens or personal data.

```js
// bad
localStorage.setItem('authToken', token)

// good — short-lived, httpOnly, secure cookie set by the server instead
// (nothing to write client-side)
```

## 30.4 Debounce or throttle high-frequency DOM event handlers
(`scroll`, `resize`, `input`) instead of doing expensive work on every
event.

```js
// bad — runs the expensive layout calc on every pixel of scroll
window.addEventListener('scroll', updateStickyHeader)

// good
function throttle(fn, waitMs) {
  let lastCall = 0
  return (...args) => {
    const now = Date.now()
    if (now - lastCall >= waitMs) {
      lastCall = now
      fn(...args)
    }
  }
}

window.addEventListener('scroll', throttle(updateStickyHeader, 100))
```

## 30.5 Use `requestAnimationFrame` for visual updates, not
`setTimeout`/`setInterval`.

> Why? `requestAnimationFrame` synchronizes with the browser's paint
> cycle, avoiding both dropped frames and wasted work on a hidden tab.

```js
// bad
setInterval(updatePosition, 16)

// good
function animate() {
  updatePosition()
  requestAnimationFrame(animate)
}
requestAnimationFrame(animate)
```

---
