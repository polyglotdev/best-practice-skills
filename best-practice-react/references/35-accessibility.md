<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 35. Accessibility

## 35.1 Use semantic interactive elements (`<button type="button">`, `<a href>`, native form inputs) — never attach `onClick` to a `<div>` or `<span>` to fake interactivity.

> Why? Native elements come with keyboard focusability, keyboard
> activation (`Enter`/`Space`), correct default `role`, and screen-reader
> semantics for free. A `<div onClick>` gives you none of that and forces
> you to reimplement all of it by hand, usually incompletely.

```jsx
// bad — not focusable, not keyboard-activatable, no accessible role
function SaveAction({ onSave }) {
  return <div onClick={onSave}>Save</div>
}
```

```jsx
// good
function SaveAction({ onSave }) {
  return (
    <button type="button" onClick={onSave}>
      Save
    </button>
  )
}
```

## 35.2 Give every `<button>` an explicit `type` attribute (`"button"`, `"submit"`, or `"reset"`).

> Why? A `<button>` with no `type` defaults to `"submit"` inside a
> `<form>`, silently submitting the form on click — a frequent source of
> accidental submissions from buttons that were only meant to toggle
> something.

```jsx
// bad — defaults to type="submit", submits the enclosing form by accident
function ClearFiltersButton({ onClear }) {
  return <button onClick={onClear}>Clear filters</button>
}
```

```jsx
// good
function ClearFiltersButton({ onClear }) {
  return (
    <button type="button" onClick={onClear}>
      Clear filters
    </button>
  )
}
```

## 35.3 Give every `<img>` an `alt` attribute — descriptive text for meaningful images, `alt=""` for purely decorative ones.

> Why? Screen readers announce an image's `src` path when `alt` is
> missing, which is meaningless noise; `alt=""` explicitly tells assistive
> technology to skip a decorative image rather than guess.

```jsx
// bad — missing alt, screen readers announce the raw file path
<img src="/hero.jpg" />
```

```jsx
// good
<img src="/team-photo.jpg" alt="The engineering team at the 2026 offsite" />

// good — decorative image, explicitly empty alt
<img src="/divider-swirl.svg" alt="" />
```

## 35.4 Give every form control an associated `<label>`, via `htmlFor`/`id` or by wrapping the control.

> Why? Without an association, a screen reader announces the input with no
> name at all, and clicking the label text does nothing instead of
> focusing the field. See also §34.3.

```jsx
// bad — visual label only, no programmatic association
<span>Email</span>
<input name="email" />
```

```jsx
// good
<label htmlFor="email">Email</label>
<input id="email" name="email" />

// good — wrapping form also creates a valid association
<label>
  Email
  <input name="email" />
</label>
```

## 35.5 Never remove the focus outline (`outline: none`) without providing a visible, equally clear alternative focus style.

> Why? Keyboard users rely entirely on the focus indicator to know where
> they are on the page. Removing it with no replacement makes the app
> unusable without a mouse.

```css
/* bad — focus becomes invisible for keyboard users */
button:focus {
  outline: none;
}
```

```css
/* good — custom style, still clearly visible */
button:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
```

## 35.6 Give every interactive element an accessible name — visible text when possible, `aria-label` when the visible content isn't descriptive text.

> Why? Screen readers and voice-control software announce elements by
> their accessible name; an element with no text and no `aria-label` is
> announced as a bare, meaningless "button" or "link."

```jsx
// bad — icon-only button has no accessible name
<button type="button" onClick={onClose}>
  <XIcon />
</button>
```

```jsx
// good
<button type="button" onClick={onClose} aria-label="Close dialog">
  <XIcon />
</button>
```

## 35.7 Modal dialogs must trap focus inside themselves while open, restore focus to the triggering element on close, close on `Escape`, and set `aria-modal="true"` with `role="dialog"`.

> Why? Without a focus trap, `Tab` can move focus behind the modal into
> content the user can't see; without focus restoration, keyboard users
> lose their place in the page every time they close a dialog.

```jsx
// bad — plain div, no focus trap, no Escape handling, no ARIA role
function Modal({ children, onClose }) {
  return <div className="modal">{children}</div>
}
```

```jsx
// good — native <dialog> gets most of this for free
function Modal({ children, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    const dialog = dialogRef.current
    dialog.showModal()
    return () => dialog.close()
  }, [])

  return (
    <dialog ref={dialogRef} onClose={onClose} aria-modal="true">
      {children}
    </dialog>
  )
}
```

## 35.8 Icon-only buttons must pair an `aria-label` with a visually-hidden text alternative or a tooltip, not rely on the icon alone.

> Why? An icon alone communicates nothing to a screen reader, and a
> tooltip alone is invisible to touch and keyboard-only users unless it's
> also exposed through `aria-label` or visually-hidden text.

```jsx
// bad — icon carries all the meaning, nothing for assistive tech
<button type="button" onClick={onDelete}>
  <TrashIcon />
</button>
```

```jsx
// good
<button type="button" onClick={onDelete} aria-label="Delete item">
  <TrashIcon />
  <span className="visually-hidden">Delete item</span>
</button>
```

## 35.9 Every text/background color pairing must meet WCAG AA contrast — 4.5:1 for normal body text, 3:1 for large text (18pt+ or 14pt+ bold).

> Why? Below these ratios, users with low vision or color-vision
> deficiencies cannot reliably read the text, regardless of font size or
> weight choices elsewhere.

```css
/* bad — light gray on white, fails 4.5:1 for body text */
.caption {
  color: #b0b0b0;
  background: #ffffff;
}
```

```css
/* good — passes AA at normal text size */
.caption {
  color: #595959;
  background: #ffffff;
}
```

## 35.10 Treat `eslint-plugin-jsx-a11y` errors as build-blocking, not warnings to suppress.

> Why? The plugin encodes exactly the rules in this section (labels, alt
> text, semantic roles, keyboard handlers) as static checks; disabling or
> ignoring them removes the one automated guardrail catching regressions
> before code review.

```jsx
// bad — lint error suppressed instead of fixed
// eslint-disable-next-line jsx-a11y/alt-text
<img src="/logo.png" />
```

```jsx
// good — fix the underlying issue
<img src="/logo.png" alt="Acme company logo" />
```

## 35.11 Never use `role` to override the semantics of a native element that already has the correct role; a `role="button"` on a `<div>` is a sign the element should be a real `<button>`.

> Why? An ARIA role changes how the element is *announced*, but does not
> grant any of the native keyboard behavior, focusability, or event
> handling that comes with the real element — you'd still have to
> reimplement all of it by hand, and it's easy to miss something.

```jsx
// bad — a div pretending to be a button
<div role="button" tabIndex={0} onClick={onSave} onKeyDown={handleKeyDown}>
  Save
</div>
```

```jsx
// good — use the real element, get all the behavior for free
<button type="button" onClick={onSave}>
  Save
</button>
```

## 35.12 Never use a positive `tabIndex` value.

> Why? A positive `tabIndex` reorders the tab sequence away from visual
> document order, which is confusing and gets harder to maintain as the
> page grows. Use `tabIndex={0}` to make a custom element focusable in
> natural order, or `tabIndex={-1}` to make it focusable only
> programmatically.

```jsx
// bad — pulls this element ahead of everything else in tab order
<div tabIndex={1}>Custom widget</div>
```

```jsx
// good
<div tabIndex={0}>Custom widget</div>
```

## 35.13 Announce asynchronous state changes (save confirmations, validation errors, loading completion) to screen readers with `aria-live`.

> Why? A screen reader only announces content that changes inside a
> live region; a status message that simply appears in the DOM elsewhere
> is silent to non-visual users.

```jsx
// bad — sighted users see the message, screen reader users hear nothing
function SaveStatus({ message }) {
  return <p>{message}</p>
}
```

```jsx
// good
function SaveStatus({ message }) {
  return (
    <p role="status" aria-live="polite">
      {message}
    </p>
  )
}
```

## 35.14 Provide a "skip to main content" link as the first focusable element on every page.

> Why? Without it, a keyboard or screen-reader user must tab through the
> entire navigation on every single page before reaching the actual
> content.

```jsx
// bad — no way to bypass repeated navigation
function Layout({ children }) {
  return (
    <>
      <NavBar />
      <main>{children}</main>
    </>
  )
}
```

```jsx
// good
function Layout({ children }) {
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <NavBar />
      <main id="main-content">{children}</main>
    </>
  )
}
```
