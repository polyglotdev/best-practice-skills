<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 36. Server Components (Next App Router / Remix RSC)

## 36.1 Treat Server Components as the default for every new component; add `"use client"` only when the component actually needs client-only capabilities.

> Why? Server Components send zero JavaScript to the browser for their
> own logic, fetch data closer to its source, and keep secrets off the
> client by construction. Defaulting to `"use client"` throws all of that
> away for components that never needed it.

```tsx
// bad — client component with no client-only behavior at all
'use client'

function ProductCard({ product }: { product: Product }) {
  return <div>{product.name}</div>
}
```

```tsx
// good — plain Server Component, no directive needed
function ProductCard({ product }: { product: Product }) {
  return <div>{product.name}</div>
}
```

## 36.2 Add `"use client"` when a component uses state, effects, refs, browser event handlers, browser-only APIs, or is a Class Component.

> Why? These are precisely the capabilities that require the component to
> run (and hydrate) in the browser; the directive marks the module
> boundary where server rendering stops and client rendering takes over.

```tsx
// bad — uses useState with no directive; build fails
function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

```tsx
// good
'use client'

function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

## 36.3 Make data-fetching Server Components `async` and `await` the data directly — no hook, no client library required.

> Why? A Server Component runs once on the server per request; awaiting
> inline is simpler and cheaper than any client-side data-fetching
> abstraction, and the data is already resolved by the time HTML streams
> to the browser.

```tsx
// bad — client-side fetch for data that's available at request time
'use client'

function UserPage({ userId }: { userId: string }) {
  const [user, setUser] = useState(null)
  useEffect(() => {
    getUser(userId).then(setUser)
  }, [userId])
  return <div>{user?.name}</div>
}
```

```tsx
// good
async function UserPage({ userId }: { userId: string }) {
  const user = await getUser(userId)
  return <div>{user.name}</div>
}
```

## 36.4 Never call hooks from a Server Component; pass Client Components as JSX children or props when interactivity is needed inside a server-rendered tree.

> Why? Hooks require the client render/commit lifecycle that Server
> Components don't have. Composing a Client Component in as a child keeps
> everything above it on the server.

```tsx
// bad — hook call inside a Server Component
function Page() {
  const [open, setOpen] = useState(false)
  return <div>{open ? 'open' : 'closed'}</div>
}
```

```tsx
// good — server tree renders around a client leaf
function Page() {
  return (
    <div>
      <StaticHeader />
      <ExpandablePanel />
    </div>
  )
}
```

## 36.5 Only pass serializable values from a Server Component to a Client Component — primitives, plain objects/arrays, and Server Actions; never functions, class instances, or non-serializable objects.

> Why? Props crossing the server→client boundary are serialized over the
> network (in RSC payload form); anything that isn't serializable either
> throws at build/runtime or silently loses its behavior.

```tsx
// bad — passing a plain function down to a Client Component
function Page() {
  function handleClick() {
    console.log('clicked')
  }
  return <ClientButton onClick={handleClick} />
}
```

```tsx
// good — pass data, or a Server Action, which the framework knows how to serialize
async function likePost(postId: string) {
  'use server'
  await db.post.incrementLikes(postId)
}

function Page({ postId }: { postId: string }) {
  return <ClientButton action={likePost} postId={postId} />
}
```

## 36.6 Do not import client-only libraries (`react-hook-form`, `zustand`, `framer-motion`) into a Server Component module.

> Why? These libraries call hooks or touch browser globals at import or
> render time; importing them into a Server Component either crashes the
> render or silently forces the whole module into the client bundle.

```tsx
// bad — react-hook-form imported into a Server Component
import { useForm } from 'react-hook-form'

async function SettingsPage() {
  const settings = await getSettings()
  return <SettingsForm settings={settings} />
}
```

```tsx
// good — form logic lives in its own Client Component
async function SettingsPage() {
  const settings = await getSettings()
  return <SettingsForm settings={settings} />
}

// good — SettingsForm.tsx
'use client'
import { useForm } from 'react-hook-form'

function SettingsForm({ settings }: { settings: Settings }) {
  const { register, handleSubmit } = useForm({ defaultValues: settings })
  return <form onSubmit={handleSubmit(saveSettings)}>…</form>
}
```

## 36.7 Fetch data in Server Components with `fetch` (using the framework's cache directives) or a database client — never with `react-query`/`swr`.

> Why? Client-cache libraries exist to manage cache/refetch lifecycles in
> the browser; a Server Component already runs once per request on the
> server and has no client lifecycle for them to manage.

```tsx
// bad — react-query inside a Server Component
async function ProductPage({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['product', id], queryFn: () => getProduct(id) })
  return <div>{data?.name}</div>
}
```

```tsx
// good
async function ProductPage({ id }: { id: string }) {
  const product = await fetch(`https://api.example.com/products/${id}`, {
    next: { revalidate: 60 }
  }).then((res) => res.json())
  return <div>{product.name}</div>
}
```

## 36.8 Remember that importing a Client Component transitively makes everything it imports part of the client boundary; the `"use client"` directive marks a boundary, not a single file.

> Why? Once a module opts into `"use client"`, every module it imports is
> bundled for the client too, even if those modules never declared the
> directive themselves. Placing the directive too high in the tree drags
> unrelated modules into the client bundle.

```tsx
// bad — "use client" at the top of a large feature file drags every helper it imports into the client bundle
'use client'

import { formatCurrency } from './format-utils'
import { validateAddress } from './validation'
// ...500 lines of mixed client/server-safe logic
```

```tsx
// good — isolate the client-only piece to its own small file
// AddressForm.tsx
'use client'
function AddressForm() {
  /* ... */
}

// format-utils.ts and validation.ts stay plain server-safe modules,
// importable from Server Components elsewhere without pulling client code in
```

## 36.9 Never pass secrets (API keys, internal tokens, unredacted internal IDs) as props to a Client Component.

> Why? Anything passed to a Client Component is serialized into the page
> payload and visible in browser dev tools — it is not private, even if
> it never renders visibly.

```tsx
// bad — internal API key ends up in the client bundle payload
async function WeatherWidget() {
  return <ClientWeather apiKey={process.env.WEATHER_API_KEY} />
}
```

```tsx
// good — the key stays on the server; the client only gets the result
async function WeatherWidget() {
  const weather = await getWeather(process.env.WEATHER_API_KEY)
  return <ClientWeather weather={weather} />
}
```

## 36.10 Prefer streaming with `<Suspense>` boundaries around slow Server Components over blocking the whole page on every data dependency.

> Why? Streaming lets fast parts of the page reach the browser and paint
> immediately while slower parts continue loading in place — see §33.2.

```tsx
// bad — the whole page waits on the slowest data source
async function Dashboard() {
  const [profile, recommendations] = await Promise.all([getProfile(), getRecommendations()])
  return (
    <>
      <Profile profile={profile} />
      <Recommendations items={recommendations} />
    </>
  )
}
```

```tsx
// good — profile paints immediately, recommendations stream in when ready
async function Dashboard() {
  const profile = await getProfile()
  return (
    <>
      <Profile profile={profile} />
      <Suspense fallback={<RecommendationsSkeleton />}>
        <Recommendations />
      </Suspense>
    </>
  )
}

async function Recommendations() {
  const items = await getRecommendations()
  return <RecommendationsList items={items} />
}
```
