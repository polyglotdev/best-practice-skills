<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 22. useContext

## 22.1 Reach for `useContext` only for values that are genuinely global to a subtree (theme, auth session, locale) — not as a shortcut around prop drilling two or three levels deep.

> Why? Context makes a component's dependencies invisible from its call
> site, which is fine for truly cross-cutting concerns but harmful for
> ordinary data flow that would be perfectly readable as props.

```jsx
// bad — context used to avoid passing one prop two levels
const NameContext = createContext('')

function App() {
  return (
    <NameContext.Provider value="Ada">
      <Toolbar />
    </NameContext.Provider>
  )
}
```

```jsx
// good — plain prop, still trivially readable
function App() {
  return <Toolbar name="Ada" />
}

// good — context for a true cross-cutting concern
const ThemeContext = createContext('light')

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Toolbar />
    </ThemeContext.Provider>
  )
}
```

## 22.2 Split contexts by concern and by update frequency; do not put frequently-changing and rarely-changing values in the same context.

> Why? Every consumer of a context re-renders whenever the context value
> changes, regardless of which field it actually reads. Bundling a
> frequently-changing value (e.g. cursor position) with a rarely-changing
> one (e.g. theme) forces theme consumers to re-render on every cursor
> move.

```jsx
// bad — one context mixes a stable value and a rapidly-changing one
const AppContext = createContext({ theme: 'light', mouseX: 0 })
```

```jsx
// good — separate contexts, separate update cadence
const ThemeContext = createContext('light')
const PointerContext = createContext({ x: 0, y: 0 })
```

## 22.3 Always provide a custom hook (`useTheme`, `useAuth`) as the public API for a context, rather than exporting the raw context object.

> Why? A custom hook can throw a clear error when used outside its
> provider, hides `useContext` plumbing, and gives you one place to change
> the underlying implementation later.

```jsx
// bad — consumers import the context directly and can forget the provider
export const AuthContext = createContext(null)

function Profile() {
  const auth = useContext(AuthContext)
  return <div>{auth.user.name}</div>
}
```

```jsx
// good
const AuthContext = createContext(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === null) throw new Error('useAuth must be used within AuthProvider')
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>
}

function Profile() {
  const { user } = useAuth()
  return <div>{user.name}</div>
}
```

## 22.4 Memoize a context's `value` object when the provider re-renders often, to avoid re-rendering every consumer on unrelated provider re-renders.

> Why? Like any object literal, `value={{ ... }}` written inline creates a
> new reference every render, which context treats as "the value changed"
> even if the contents are identical.

```jsx
// bad
function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>
}
```

```jsx
// good
function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const value = useMemo(() => ({ user, setUser }), [user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
```
