<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 37. Server Actions (React 19 / Next)

## 37.1 Mark every server function with `'use server'`, either at the top of the function body or at the top of a module dedicated to server actions.

> Why? The directive is what tells the framework's build tooling to
> generate a callable network endpoint for the function instead of
> bundling it for the client — omit it and the function either fails to
> build or runs somewhere you didn't intend.

```ts
// bad — server-only logic with no directive, callable from a client form action
async function deletePost(postId: string) {
  await db.post.delete(postId)
}
```

```ts
// good
async function deletePost(postId: string) {
  'use server'
  await db.post.delete(postId)
}
```

## 37.2 Validate every input with `zod` (or an equivalent schema library) inside the action; never trust `FormData` values as already the right type or shape.

> Why? A Server Action is a public network endpoint the moment it exists —
> anyone can construct a request to it directly, bypassing your form's own
> client-side constraints entirely.

```ts
// bad — trusts FormData.get() results without any validation
async function createPost(formData: FormData) {
  'use server'
  const title = formData.get('title')
  await db.post.create({ title })
}
```

```ts
// good
const schema = z.object({
  title: z.string().min(1).max(200)
})

async function createPost(formData: FormData) {
  'use server'
  const result = schema.safeParse({ title: formData.get('title') })
  if (!result.success) return { ok: false, error: 'Invalid title' }
  await db.post.create({ title: result.data.title })
  return { ok: true, data: null }
}
```

## 37.3 Return a typed result union (`{ ok: true, data } | { ok: false, error }`) from a Server Action rather than throwing across the server/client boundary.

> Why? An uncaught throw in a Server Action surfaces to the client as a
> generic, unhelpful error boundary trigger; a typed result lets the
> calling Client Component render the specific error inline.

```ts
// bad — throws, client only sees a generic failure
async function updateEmail(email: string) {
  'use server'
  if (!isValidEmail(email)) throw new Error('Invalid email')
  await db.user.updateEmail(email)
}
```

```ts
// good
type ActionResult<T> = { ok: true; data: T } | { ok: false; error: string }

async function updateEmail(email: string): Promise<ActionResult<null>> {
  'use server'
  if (!isValidEmail(email)) return { ok: false, error: 'Invalid email' }
  await db.user.updateEmail(email)
  return { ok: true, data: null }
}
```

## 37.4 Never include secrets, stack traces, or raw database errors in the value a Server Action returns to the client.

> Why? The return value is serialized straight to the browser; leaking an
> internal error message or stack trace exposes implementation details an
> attacker can use, and can leak credentials embedded in connection
> strings.

```ts
// bad — raw error message (and potentially a stack trace) sent to the client
async function createOrder(formData: FormData) {
  'use server'
  try {
    await db.order.create(parseOrder(formData))
  } catch (error) {
    return { ok: false, error: String(error) }
  }
}
```

```ts
// good — log the detail server-side, return a safe generic message
async function createOrder(formData: FormData) {
  'use server'
  try {
    await db.order.create(parseOrder(formData))
    return { ok: true, data: null }
  } catch (error) {
    logger.error('createOrder failed', { error })
    return { ok: false, error: 'Could not create order. Please try again.' }
  }
}
```

## 37.5 Call `revalidatePath` or `revalidateTag` after any mutation that changes data a cached Server Component depends on.

> Why? Without revalidation, the framework's data cache keeps serving the
> pre-mutation snapshot, so the UI appears not to have updated even though
> the mutation succeeded.

```ts
// bad — mutation succeeds but the cached list page still shows stale data
async function deletePost(postId: string) {
  'use server'
  await db.post.delete(postId)
}
```

```ts
// good
async function deletePost(postId: string) {
  'use server'
  await db.post.delete(postId)
  revalidatePath('/posts')
}
```

## 37.6 Use `useFormStatus` for the pending state of the form currently submitting, and `useActionState` (React 19) to track the action's returned result.

> Why? These hooks are purpose-built to read a Server Action's in-flight
> and settled state without hand-rolled `isLoading`/`error` state that can
> drift out of sync with the actual request.

```tsx
// bad — hand-rolled pending/error state duplicating what the hooks give you
'use client'
function DeleteButton({ postId }: { postId: string }) {
  const [pending, setPending] = useState(false)
  async function handleClick() {
    setPending(true)
    await deletePost(postId)
    setPending(false)
  }
  return (
    <button type="button" disabled={pending} onClick={handleClick}>
      Delete
    </button>
  )
}
```

```tsx
// good
'use client'
function DeleteForm({ postId }: { postId: string }) {
  const [state, formAction] = useActionState(deletePost, { ok: true, error: null })
  return (
    <form action={formAction}>
      <input type="hidden" name="postId" value={postId} />
      <SubmitButton />
      {!state.ok && <p role="alert">{state.error}</p>}
    </form>
  )
}

function SubmitButton() {
  const { pending } = useFormStatus()
  return (
    <button type="submit" disabled={pending}>
      Delete
    </button>
  )
}
```

## 37.7 Re-check authorization (session, permissions, ownership) inside every Server Action — never assume the UI already prevented an unauthorized call.

> Why? A Server Action is directly callable over the network by anyone who
> constructs the right request, regardless of whether your UI hides the
> button that would normally trigger it.

```ts
// bad — assumes only the owner's UI ever calls this, doesn't check
async function deletePost(postId: string) {
  'use server'
  await db.post.delete(postId)
}
```

```ts
// good
async function deletePost(postId: string) {
  'use server'
  const session = await getSession()
  const post = await db.post.findById(postId)
  if (!session || post.authorId !== session.userId) {
    return { ok: false, error: 'Not authorized' }
  }
  await db.post.delete(postId)
  return { ok: true, data: null }
}
```

## 37.8 Log Server Action invocations with structured logging, redacting personally identifiable information before it reaches the log sink.

> Why? Server Actions are effectively API endpoints; you need the same
> observability you'd want for any endpoint, and unredacted PII in logs is
> a compliance and security liability.

```ts
// bad — logs the entire raw form submission, including PII
async function updateProfile(formData: FormData) {
  'use server'
  logger.info('updateProfile called', { formData: Object.fromEntries(formData) })
}
```

```ts
// good
async function updateProfile(formData: FormData) {
  'use server'
  logger.info('updateProfile called', { userId: getCurrentUserId() })
}
```

## 37.9 Do not use Server Actions to read data; use Server Components (or route handlers) for reads and reserve actions for mutations.

> Why? Server Actions are designed and cached around the mutation
> lifecycle (form submission, revalidation); using them for reads bypasses
> the framework's data-fetching cache model and loses the benefits of §36.

```tsx
// bad — a Server Action used purely to fetch data for display
'use client'
function ProductPage({ id }: { id: string }) {
  const [product, setProduct] = useState(null)
  useEffect(() => {
    getProductAction(id).then(setProduct)
  }, [id])
  return <div>{product?.name}</div>
}
```

```tsx
// good — read happens in the Server Component itself
async function ProductPage({ id }: { id: string }) {
  const product = await getProduct(id)
  return <div>{product.name}</div>
}
```

## 37.10 Rate-limit Server Actions at the edge or in middleware, especially ones that write to a database or send external requests (email, SMS).

> Why? Without a limit, a Server Action is just as exploitable for abuse
> (spamming, credential stuffing, cost-driving external calls) as any
> other unauthenticated or lightly-authenticated network endpoint.

```ts
// bad — no rate limiting on an action that sends an email every call
async function sendInvite(email: string) {
  'use server'
  await sendEmail(email, 'invite')
}
```

```ts
// good
async function sendInvite(email: string) {
  'use server'
  const allowed = await rateLimit(`invite:${getCurrentUserId()}`, { max: 5, window: '1h' })
  if (!allowed) return { ok: false, error: 'Too many invites sent. Try again later.' }
  await sendEmail(email, 'invite')
  return { ok: true, data: null }
}
```
