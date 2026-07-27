<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 39. State Management

## 39.1 Default to local component state (`useState`/`useReducer`) unless a value genuinely needs to be shared beyond a single component.

> Why? Local state is the simplest tool, easiest to reason about, and
> carries none of the indirection cost of Context or an external store.
> Reach for something bigger only once local state actually can't do the
> job.

```jsx
// bad — global store for state only one component uses
const useUiStore = create((set) => ({
  isDropdownOpen: false,
  setDropdownOpen: (v) => set({ isDropdownOpen: v })
}))
```

```jsx
// good
function Dropdown() {
  const [isOpen, setIsOpen] = useState(false)
}
```

## 39.2 Lift state up to the nearest common ancestor once two sibling components need to share it.

> Why? Lifting state to the shared parent is the simplest fix for
> "siblings need the same value" and avoids reaching for Context or a
> store before it's actually necessary.

```jsx
// bad — two siblings each keep their own copy of the same logical state
function Tabs() {
  return (
    <>
      <TabButton />
      <TabPanel />
    </>
  )
}
```

```jsx
// good — shared state lives in the parent, passed down as props
function Tabs() {
  const [activeTab, setActiveTab] = useState('overview')
  return (
    <>
      <TabButton activeTab={activeTab} onSelect={setActiveTab} />
      <TabPanel activeTab={activeTab} />
    </>
  )
}
```

## 39.3 Reach for Context only for state that is truly global to a subtree — theme, current user/session, i18n locale, feature flags — not as a workaround for prop drilling two or three levels.

> Why? See §22.1 — Context trades explicit, traceable data flow for
> implicit access, which is worth it only for values that are legitimately
> needed everywhere below a given point in the tree.

```jsx
// bad — Context introduced just to skip passing one prop down two levels
const SelectedIdContext = createContext(null)
```

```jsx
// good — genuinely cross-cutting concern
const LocaleContext = createContext('en-US')
```

## 39.4 Split Context providers by how often their value changes; never combine a frequently-changing value and a rarely-changing value in one context.

> Why? See §22.2 — every consumer re-renders on every context value
> change, so bundling a hot value with a cold one forces unrelated
> consumers to re-render far more than necessary.

```jsx
// bad
const AppContext = createContext({ user: null, cursorPosition: { x: 0, y: 0 } })
```

```jsx
// good
const UserContext = createContext(null)
const CursorContext = createContext({ x: 0, y: 0 })
```

## 39.5 Reach for an external store (`zustand`, `jotai`, `valtio`) only once Context re-renders are a measured problem, not a hypothetical one.

> Why? External stores add a dependency, a new mental model, and often a
> devtools setup; the switch is worth it once profiling shows Context
> is actually causing wasted renders, not before.

```jsx
// bad — adopting zustand pre-emptively for a value with one or two consumers
const useThemeStore = create((set) => ({ theme: 'light', setTheme: (t) => set({ theme: t }) }))
```

```jsx
// good — Context is enough until proven otherwise
const ThemeContext = createContext('light')

// good — reach for a store once profiling shows Context causing excess re-renders
const useCartStore = create((set) => ({
  items: [],
  addItem: (item) => set((state) => ({ items: [...state.items, item] }))
}))
```

## 39.6 Do not introduce Redux for new projects; if a codebase already uses it, keep server-originated data out of the Redux store.

> Why? Redux's core value — a single global store with time-travel
> debugging — is rarely needed for typical CRUD apps today, and modern
> alternatives (Context, `zustand`, `react-query`) cover the same ground
> with far less boilerplate. Server data belongs in a server-cache layer,
> not duplicated into a separate client store.

```jsx
// bad — new project reaching for Redux, and storing fetched server data in it
const postsSlice = createSlice({
  name: 'posts',
  initialState: [],
  reducers: { setPosts: (state, action) => action.payload }
})
```

```jsx
// good — server data lives in a server-cache library
function usePosts() {
  return useQuery({ queryKey: ['posts'], queryFn: getPosts })
}
```

## 39.7 Keep server-originated data in a server-cache library (`react-query`, `swr`) or the framework's own data layer — never duplicated into a client-side store like `zustand`.

> Why? A client store has no concept of server cache invalidation,
> background refetching, or staleness; duplicating server data into it
> means you now own a second, easily-stale copy of the same data.

```jsx
// bad — fetched data copied into a zustand store
const usePostsStore = create((set) => ({
  posts: [],
  load: async () => set({ posts: await getPosts() })
}))
```

```jsx
// good
function usePosts() {
  return useQuery({ queryKey: ['posts'], queryFn: getPosts })
}
```

## 39.8 Put filters, active tab, sort order, and other shareable/bookmarkable UI state in the URL via `useSearchParams`, not in component state alone.

> Why? URL-backed state survives a page refresh, is shareable via a link,
> and works correctly with browser back/forward — plain component state
> does none of that.

```jsx
// bad — sort order lives only in component state, lost on refresh
function ProductList() {
  const [sort, setSort] = useState('price-asc')
}
```

```jsx
// good
function ProductList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const sort = searchParams.get('sort') ?? 'price-asc'
  function handleSortChange(next) {
    setSearchParams({ sort: next })
  }
}
```

## 39.9 Keep form field state inside the form library (`react-hook-form`) or uncontrolled `FormData`, rather than mirroring it into a separate global store.

> Why? Form state has its own lifecycle (dirty/touched tracking,
> validation, reset-on-submit) that form libraries already model
> correctly; mirroring it elsewhere creates two sources of truth for the
> same fields.

```jsx
// bad — form fields duplicated into a zustand store alongside react-hook-form
const useFormStore = create((set) => ({ email: '', setEmail: (v) => set({ email: v }) }))
```

```jsx
// good — react-hook-form owns all of the form's state
function SignupForm() {
  const { register, handleSubmit } = useForm()
}
```

## 39.10 Persist state to `localStorage` only behind an abstraction that safely handles JSON parse errors and quota-exceeded exceptions.

> Why? `localStorage` can contain corrupted or unexpected data (from an
> older app version, browser extension, or manual edit) and can throw when
> full; reading/writing it directly without guards crashes the app on
> either failure mode.

```jsx
// bad — throws if the stored value is corrupted or storage is full
function usePersistedState(key, initial) {
  const [value, setValue] = useState(JSON.parse(localStorage.getItem(key)) ?? initial)
  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value))
  }, [key, value])
  return [value, setValue]
}
```

```jsx
// good
function usePersistedState(key, initial) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored ? JSON.parse(stored) : initial
    } catch {
      return initial
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // storage full or unavailable; state still works in-memory
    }
  }, [key, value])

  return [value, setValue]
}
```
