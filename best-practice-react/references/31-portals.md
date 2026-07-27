<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 31. Portals

## 31.1 Use `createPortal` to render overlays (modals, tooltips, toasts) outside the DOM hierarchy of a scrolling/clipping/`overflow:hidden` ancestor.

> Why? A modal rendered as a normal descendant inherits any ancestor's
> `overflow: hidden`, `transform`, or `z-index` stacking context, which can
> clip or mis-stack it. A portal renders the same React tree (same context,
> same event bubbling) into a different DOM node, avoiding that.

```jsx
// bad — modal is a normal child, clipped by any ancestor with overflow:hidden
function Card({ children, isModalOpen }) {
  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      {children}
      {isModalOpen && <div className="modal">…</div>}
    </div>
  )
}
```

```jsx
// good
import { createPortal } from 'react-dom'

function Modal({ children }) {
  return createPortal(<div className="modal">{children}</div>, document.body)
}

function Card({ children, isModalOpen }) {
  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      {children}
      {isModalOpen && <Modal>…</Modal>}
    </div>
  )
}
```

## 31.2 Remember that events from a portal still bubble through the React tree (not the DOM tree); do not add redundant `stopPropagation` calls assuming otherwise.

> Why? React intentionally propagates portal events along the component
> tree's parent chain so that `onClick` handlers on logical ancestors still
> fire, even though the DOM node lives elsewhere. Relying on DOM-only
> bubbling assumptions leads to handlers that "mysteriously" fire or don't.

```jsx
// good — a click inside the portal still triggers the outer onClick handler
function App() {
  function handleAppClick() {
    console.log('bubbled from the portal, as expected')
  }
  return (
    <div onClick={handleAppClick}>
      <Modal>
        <button>Click me</button>
      </Modal>
    </div>
  )
}
```
