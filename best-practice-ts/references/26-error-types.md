<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 26. Error Types

## 26.1 Type `catch` variables as `unknown` (the default under `strict`) and narrow before use; never assume the caught value is an `Error`.

```ts
// bad
try {
  doSomething()
} catch (err: any) {
  console.log(err.message)
}

// good
try {
  doSomething()
} catch (err) {
  if (err instanceof Error) {
    console.log(err.message)
  } else {
    console.log('Unknown error', err)
  }
}
```

## 26.2 Model expected, recoverable failures with a `Result<T, E>` union instead of throwing, and reserve `throw` for truly exceptional, unrecoverable conditions.

> Why? A thrown exception is invisible in a function's type signature — a
> caller can forget to catch it and the compiler will not warn them. A
> `Result` return type forces the caller to handle both branches
> explicitly.

```ts
// bad
function parsePort(input: string): number {
  const port = Number(input)
  if (Number.isNaN(port)) throw new Error('Invalid port')
  return port
}

// good
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E }

function parsePort(input: string): Result<number> {
  const port = Number(input)
  if (Number.isNaN(port)) {
    return { ok: false, error: new Error('Invalid port') }
  }
  return { ok: true, value: port }
}

const result = parsePort(rawPort)
if (!result.ok) {
  console.error(result.error.message)
} else {
  startServer(result.value)
}
```

## 26.3 Define custom error subclasses with a literal `name` and a narrow, typed payload, so error types can be discriminated with `instanceof`.

```ts
// good
class ValidationError extends Error {
  override readonly name = 'ValidationError'
  constructor(
    message: string,
    public readonly field: string
  ) {
    super(message)
  }
}

try {
  validate(input)
} catch (err) {
  if (err instanceof ValidationError) {
    console.log(`${err.field}: ${err.message}`)
  }
}
```

## 26.4 Use the standard `Error` `cause` option to preserve an underlying error instead of swallowing it or interpolating it into a message string.

> Why? `cause` keeps the original error object (and its stack trace)
> attached and inspectable, whereas string interpolation discards the
> original error's type and stack entirely.

```ts
// bad
catch (err) {
  throw new Error(`Failed to load user: ${err}`)
}

// good
catch (err) {
  throw new Error('Failed to load user', { cause: err })
}
```
