<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 14. Ordering

## 14.1 Order a component file: imports → types → constants → the component → local helper functions → export.

> Why? A predictable top-to-bottom order lets any reader find "what does
> this file export" and "what are its dependencies" without hunting.

```tsx
// good
import { useState } from 'react'
import { Avatar } from './Avatar'

type UserCardProps = {
  name: string
  imageUrl: string
}

const MAX_NAME_LENGTH = 40

export function UserCard({ name, imageUrl }: UserCardProps) {
  const [expanded, setExpanded] = useState(false)
  const displayName = truncate(name, MAX_NAME_LENGTH)

  return (
    <div>
      <Avatar src={imageUrl} />
      <button onClick={() => setExpanded(!expanded)}>{displayName}</button>
    </div>
  )
}

function truncate(value: string, max: number) {
  return value.length > max ? `${value.slice(0, max)}…` : value
}
```

## 14.2 Inside a function component, order statements: hooks first (in the order they're needed) → derived values → event handlers → early returns → JSX return.

> Why? Grouping all hook calls at the top makes the Rules of Hooks (§15)
> trivially easy to verify by eye, and puts the "what does this component
> render" answer at the bottom where readers expect it.

```jsx
// bad — hooks interleaved with logic and an early return, hard to audit
function Profile({ userId }) {
  const [tab, setTab] = useState('posts')
  if (!userId) return null
  const { data } = useUser(userId)
  useEffect(() => {
    document.title = data?.name ?? 'Profile'
  }, [data])

  return <div>{data?.name}</div>
}
```

```jsx
// good
function Profile({ userId }) {
  const [tab, setTab] = useState('posts')
  const { data } = useUser(userId)

  useEffect(() => {
    document.title = data?.name ?? 'Profile'
  }, [data])

  if (!userId) return null

  return <div>{data?.name}</div>
}
```

## 14.3 Group related hook calls together (e.g. all `useState` for one concern), but do not force unrelated state into a single object just to reduce hook count.

> Why? Readability comes from grouping by *purpose*, not from minimizing
> the raw number of `useState` calls. Merging unrelated state into one
> object forces every update to spread the rest of the object and
> re-renders on unrelated changes.

```jsx
// bad — unrelated concerns crammed into one state object
function Form() {
  const [state, setState] = useState({
    name: '',
    isModalOpen: false,
    submitCount: 0
  })
}
```

```jsx
// good — separate concerns, separate state
function Form() {
  const [name, setName] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [submitCount, setSubmitCount] = useState(0)
}
```
