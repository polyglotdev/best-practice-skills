<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 38. Data Fetching

## 38.1 Pick exactly one client data-fetching strategy per project — a framework loader (App Router async RSC, Remix loaders, TanStack Router loaders), `@tanstack/react-query`, or `swr` — and do not mix strategies within the same app.

> Why? Mixing strategies means two independent caching/invalidation
> systems that don't know about each other, producing stale-data bugs that
> only show up when a mutation in one system should have invalidated data
> owned by the other.

```jsx
// bad — react-query and swr both fetching the same resource in different parts of the app
function ProfileA() {
  const { data } = useQuery({ queryKey: ['user'], queryFn: getUser })
}
function ProfileB() {
  const { data } = useSWR('/api/user', fetcher)
}
```

```jsx
// good — one strategy, one cache, one invalidation model
function ProfileA() {
  const { data } = useQuery({ queryKey: ['user'], queryFn: getUser })
}
function ProfileB() {
  const { data } = useQuery({ queryKey: ['user'], queryFn: getUser })
}
```

## 38.2 Do not hand-roll a `useEffect` + `fetch` + `useState` data cache for production features.

> Why? A hand-rolled fetch effect reimplements — usually incompletely —
> caching, deduplication, retries, race-condition handling, and
> revalidation that `react-query`/`swr`/framework loaders already solve
> correctly. See §18.6-18.7 for the specific failure modes.

```jsx
// bad
function useUser(userId) {
  const [user, setUser] = useState(null)
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser)
  }, [userId])
  return user
}
```

```jsx
// good
function useUser(userId) {
  const { data } = useQuery({ queryKey: ['user', userId], queryFn: () => getUser(userId) })
  return data
}
```

## 38.3 Give every fetch an explicit timeout via `AbortSignal.timeout(ms)` or a manually managed `AbortController`.

> Why? Without a timeout, a hung server or dropped connection leaves the
> request pending indefinitely, stranding the UI in a loading state
> forever with no way to recover.

```jsx
// bad — no timeout, a hung request loads forever
async function getUser(userId) {
  const res = await fetch(`/api/users/${userId}`)
  return res.json()
}
```

```jsx
// good
async function getUser(userId) {
  const res = await fetch(`/api/users/${userId}`, { signal: AbortSignal.timeout(10000) })
  return res.json()
}
```

## 38.4 Validate every fetch response body against a `zod` schema at the boundary before it enters application state.

> Why? A backend response can drift from what the frontend expects (a
> renamed field, a null where a string was assumed); validating at the
> boundary turns that drift into one clear error instead of a confusing
> crash deep inside a component.

```jsx
// bad — response shape assumed, never checked
async function getUser(userId) {
  const res = await fetch(`/api/users/${userId}`)
  return res.json()
}
```

```jsx
// good
const userSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email()
})

async function getUser(userId) {
  const res = await fetch(`/api/users/${userId}`)
  return userSchema.parse(await res.json())
}
```

## 38.5 Render three distinct UI branches for loading, empty, and error — do not collapse "loading" and "no data" into a single check.

> Why? "Still loading" and "loaded, but there's nothing" are different
> states that need different messages; collapsing them either shows a
> spinner forever after a successful empty response, or briefly flashes an
> "empty" message before real data arrives.

```jsx
// bad — loading and empty are indistinguishable
function PostList({ posts, isLoading }) {
  if (!posts?.length) return <Spinner />
  return <List items={posts} />
}
```

```jsx
// good
function PostList({ posts, isLoading, error }) {
  if (isLoading) return <Spinner />
  if (error) return <ErrorMessage error={error} />
  if (posts.length === 0) return <EmptyState />
  return <List items={posts} />
}
```

## 38.6 Fetch independent resources in parallel with `Promise.all` rather than sequentially awaiting each one.

> Why? Sequential awaits on independent requests add each request's
> latency together; parallel requests take only as long as the slowest
> one.

```jsx
// bad — sequential, latency adds up
async function Dashboard() {
  const profile = await getProfile()
  const notifications = await getNotifications()
  return <DashboardView profile={profile} notifications={notifications} />
}
```

```jsx
// good
async function Dashboard() {
  const [profile, notifications] = await Promise.all([getProfile(), getNotifications()])
  return <DashboardView profile={profile} notifications={notifications} />
}
```

## 38.7 Use stable, structured cache keys as arrays (`['user', userId, 'posts']`) rather than ad hoc strings.

> Why? Structured keys let the cache library invalidate by prefix (e.g.
> everything under `['user', userId]`) and avoid subtle key collisions
> from string concatenation typos.

```jsx
// bad — string keys are easy to mistype and hard to invalidate by prefix
useQuery({ queryKey: [`user-${userId}-posts`], queryFn: getUserPosts })
```

```jsx
// good
useQuery({ queryKey: ['user', userId, 'posts'], queryFn: () => getUserPosts(userId) })
```

## 38.8 Keep server-cache libraries (`react-query`, `swr`) on the client; server data belongs in the framework loader/RSC layer, not duplicated into a client cache on first load.

> Why? Double-fetching the same data once on the server (to render HTML)
> and again on the client (to populate a client cache) wastes a request
> and risks a flash of different data if the two responses disagree.

```tsx
// bad — Server Component fetches, then the client re-fetches the same thing again
async function Page() {
  const initialPosts = await getPosts()
  return <PostsClient />
}

// PostsClient re-fetches everything itself
function PostsClient() {
  const { data } = useQuery({ queryKey: ['posts'], queryFn: getPosts })
}
```

```tsx
// good — server data seeds the client cache, no duplicate fetch
async function Page() {
  const initialPosts = await getPosts()
  return <PostsClient initialPosts={initialPosts} />
}

function PostsClient({ initialPosts }) {
  const { data } = useQuery({ queryKey: ['posts'], queryFn: getPosts, initialData: initialPosts })
}
```

## 38.9 Implement optimistic updates with `useOptimistic` (React 19) or the calling library's built-in mutation hooks (`onMutate` in `react-query`) rather than hand-rolled temporary state.

> Why? These APIs already handle the rollback-on-error case correctly; a
> hand-rolled optimistic update tends to forget to revert on failure,
> leaving the UI showing a change that never actually happened.

```jsx
// bad — hand-rolled optimistic state with no rollback on failure
function LikeButton({ postId, likes }) {
  const [optimisticLikes, setOptimisticLikes] = useState(likes)
  function handleClick() {
    setOptimisticLikes((n) => n + 1)
    likePost(postId)
  }
  return <button onClick={handleClick}>{optimisticLikes}</button>
}
```

```jsx
// good
function LikeButton({ postId, likes }) {
  const [optimisticLikes, addOptimisticLike] = useOptimistic(likes, (state) => state + 1)
  async function handleClick() {
    addOptimisticLike()
    await likePost(postId)
  }
  return <button onClick={handleClick}>{optimisticLikes}</button>
}
```

## 38.10 Prefetch data on hover/focus for links and buttons that lead to a known next view, to reduce perceived navigation latency.

> Why? A prefetch triggered on hover often completes before the user
> finishes their click, making the subsequent navigation feel instant
> instead of waiting on the network at click time.

```jsx
// bad — fetch only starts after the click, user waits on the network
function ProductLink({ id, children }) {
  return <Link to={`/products/${id}`}>{children}</Link>
}
```

```jsx
// good
function ProductLink({ id, children }) {
  const queryClient = useQueryClient()
  function handleMouseEnter() {
    queryClient.prefetchQuery({ queryKey: ['product', id], queryFn: () => getProduct(id) })
  }
  return (
    <Link to={`/products/${id}`} onMouseEnter={handleMouseEnter}>
      {children}
    </Link>
  )
}
```
