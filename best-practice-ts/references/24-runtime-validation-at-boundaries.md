<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 24. Runtime Validation at Boundaries

## 24.1 Treat every value that enters the program from outside the type checker's view as `unknown` until validated: `process.env`, `JSON.parse`, `fetch` responses, message-queue payloads, LLM tool-call arguments, and form data.

> Why? TypeScript's types are erased at runtime and verified only against
> the code you wrote — they provide zero protection against a value that
> actually came from a network call, a file, an environment variable, or a
> user, all of which can violate the declared type at runtime with no
> compiler error.

```ts
// bad — trusts the network response's shape with no runtime check
async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`)
  return res.json() // typed as any, asserted as User by convention only
}

// good
import { z } from 'zod'

const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string()
})
type User = z.infer<typeof userSchema>

async function getUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`)
  return userSchema.parse(await res.json())
}
```

## 24.2 Validate `process.env` once, at startup, into a typed config object; never read `process.env.X` directly elsewhere in the codebase.

> Why? `process.env` is typed as `Record<string, string | undefined>` — every
> untyped read anywhere in the codebase is a potential `undefined` at
> runtime; a single validated config object gives the rest of the codebase
> a fully-typed, guaranteed-present config to import instead.

```ts
// bad
const port = Number(process.env.PORT)
const dbUrl = process.env.DATABASE_URL // string | undefined, used unchecked

// good — env.ts
import { z } from 'zod'

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']),
  PORT: z.coerce.number().int().positive().default(3000),
  DATABASE_URL: z.string().url()
})

export const env = envSchema.parse(process.env)
// every other file: import { env } from './env'; env.PORT is number
```

## 24.3 Validate `JSON.parse` output before use; never assert the parsed value's shape.

```ts
// bad
const config = JSON.parse(rawConfig) as AppConfig

// good
const configSchema = z.object({ apiUrl: z.string().url(), retries: z.number() })
const config = configSchema.parse(JSON.parse(rawConfig))
```

## 24.4 Validate LLM tool-call arguments and message-queue payloads with the same rigor as an HTTP request body — both are untrusted external input.

> Why? A tool-call argument or queue message is generated outside your
> process (by a model or another service) and can be malformed, missing
> fields, or an unexpected shape despite a declared schema on the sending
> side.

```ts
// good
const toolArgsSchema = z.object({
  query: z.string().min(1),
  limit: z.number().int().min(1).max(100).default(10)
})

function handleToolCall(rawArgs: unknown) {
  const args = toolArgsSchema.parse(rawArgs)
  return search(args.query, args.limit)
}
```

## 24.5 Prefer `.safeParse` over `.parse` at boundaries where a validation failure is an expected, recoverable outcome rather than a program bug.

> Why? `.parse` throws, which is appropriate for startup config where a
> failure should crash immediately; `.safeParse` returns a discriminated
> result, which is appropriate for per-request validation where a failure
> should produce a 400 response, not a crash.

```ts
// good
function parseCreateUserBody(body: unknown) {
  const result = createUserSchema.safeParse(body)
  if (!result.success) {
    return { ok: false as const, error: result.error.flatten() }
  }
  return { ok: true as const, data: result.data }
}
```
