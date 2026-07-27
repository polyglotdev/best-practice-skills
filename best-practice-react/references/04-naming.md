<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 4. Naming

## 4.1 Use `.tsx` for TypeScript React component files, `.jsx` for plain-JS ones; never rely on a `.js`/`.ts` file containing JSX.

> Why? Tooling (bundlers, editors, `tsc`) uses the extension to decide
> whether to parse JSX syntax. A `.ts` file with JSX inside it will fail to
> compile.

```
// bad
UserCard.ts        // contains JSX — will not parse

// good
UserCard.tsx
UserCard.jsx
```

## 4.2 Use PascalCase for component filenames and for the component itself; camelCase for instances.

> Why? PascalCase signals "this is a component, and JSX will treat a
> lowercase tag name as an HTML element instead" — a real semantic
> distinction in JSX, not just style.

```jsx
// bad
import reservationCard from './reservationCard'

const ReservationItem = <reservationCard />
```

```jsx
// good
import ReservationCard from './ReservationCard'

const reservationItem = <ReservationCard />
```

## 4.3 Name the component after its file; for a directory's root component, use `index.tsx` and name the component after the directory.

> Why? A consistent file-to-component mapping means you can always guess
> the import path from the component name and vice versa.

```jsx
// bad
import Footer from './Footer/Footer'

// bad
import Footer from './Footer/index'

// good
import Footer from './Footer'
```

## 4.4 Name Higher-Order Components with a `with` prefix, and set `displayName` to a composite of both names.

> Why? `displayName` shows up in React DevTools and error messages; a
> composite name like `withAuth(UserCard)` tells you exactly which HOC
> wrapped which component without digging through source.

```jsx
// bad
export default function withAuth(WrappedComponent) {
  return function WithAuth(props) {
    return <WrappedComponent {...props} />
  }
}
```

```jsx
// good
export default function withAuth(WrappedComponent) {
  function WithAuth(props) {
    return <WrappedComponent {...props} />
  }

  const wrappedName = WrappedComponent.displayName || WrappedComponent.name || 'Component'
  WithAuth.displayName = `withAuth(${wrappedName})`
  return WithAuth
}
```

## 4.5 Never reuse DOM prop names (`style`, `className`, `href`) for a different purpose.

> Why? Consumers of your component bring expectations from HTML. Repurposing
> `style` to mean something other than a style object breaks that mental
> model and IDE tooling.

```jsx
// bad
<MyComponent style="fancy" />
```

```jsx
// good
<MyComponent variant="fancy" />
```

## 4.6 Name event-handler props `on<Event>` and their implementations `handle<Event>`.

> Why? This pairing makes it instantly clear, from either side, which prop
> is connected to which internal handler.

```jsx
// bad
function SearchBox({ onQuery }) {
  function submitted(event) {
    event.preventDefault()
    onQuery(event.target.value)
  }
  return <form onSubmit={submitted} />
}
```

```jsx
// good
function SearchBox({ onSearch }) {
  function handleSubmit(event) {
    event.preventDefault()
    onSearch(event.target.value)
  }
  return <form onSubmit={handleSubmit} />
}
```
