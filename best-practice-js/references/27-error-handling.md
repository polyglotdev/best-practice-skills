<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 27. Error Handling

## 27.1 Always throw `Error` objects (or subclasses), never strings
or plain values.

> Why? Only `Error` instances carry a stack trace, and every catch
> block, logger, and monitoring tool expects one.

```js
// bad
throw 'Something broke'

// good
throw new Error('Something broke')
```

## 27.2 Create domain-specific error subclasses for conditions
callers need to distinguish.

> Why? A named error class lets a caller `catch` and branch on `error
> instanceof ValidationError` instead of parsing a message string.

```js
class ValidationError extends Error {
  constructor(message, { field } = {}) {
    super(message)
    this.name = 'ValidationError'
    this.field = field
  }
}

function assertValidEmail(email) {
  if (!email.includes('@')) {
    throw new ValidationError('Invalid email address', { field: 'email' })
  }
}
```

## 27.3 Preserve the original error using the `cause` option when
you wrap it.

> Why? `cause` keeps the full failure chain visible in logs instead of
> discarding the low-level reason once you add higher-level context.

```js
// bad — the original stack and message are lost
try {
  await saveOrder(order)
} catch {
  throw new Error('Failed to save order')
}

// good
try {
  await saveOrder(order)
} catch (error) {
  throw new Error('Failed to save order', { cause: error })
}
```

## 27.4 Never swallow an error silently; at minimum, log it.

```js
// bad
try {
  await sendNotification(user)
} catch {
  // nothing
}

// good
try {
  await sendNotification(user)
} catch (error) {
  logger.warn('notification failed', { userId: user.id, cause: error })
}
```

## 27.5 Only catch errors you can meaningfully handle; let the rest
propagate to a top-level handler.

> Why? A `catch` that can't do anything useful except rethrow just adds
> noise. Centralize unrecoverable-error handling at process/request
> boundaries (an Express error middleware, a top-level `unhandledRejection`
> listener, etc.).

```js
// bad — catches only to immediately rethrow, adding nothing
async function getUser(id) {
  try {
    return await db.users.findById(id)
  } catch (error) {
    throw error
  }
}

// good — let it propagate; handle at the boundary
async function getUser(id) {
  return db.users.findById(id)
}
```

## 27.6 Validate inputs at the boundary and fail fast with a clear
message, rather than letting a bad value cause a confusing failure
deep in the call stack.

```js
// bad — fails deep inside with a cryptic TypeError
function chargeCard(amountInCents) {
  return paymentGateway.charge(amountInCents.toFixed(2))
}

// good
function chargeCard(amountInCents) {
  if (!Number.isInteger(amountInCents) || amountInCents <= 0) {
    throw new ValidationError('amountInCents must be a positive integer')
  }
  return paymentGateway.charge(amountInCents)
}
```

## 27.7 In Node, register process-level handlers for
`unhandledRejection` and `uncaughtException` that log and exit, rather
than letting the process limp along in a corrupted state.

```js
process.on('unhandledRejection', (reason) => {
  logger.error('unhandled rejection', { cause: reason })
  process.exitCode = 1
})

process.on('uncaughtException', (error) => {
  logger.error('uncaught exception', { cause: error })
  process.exit(1)
})
```

---
