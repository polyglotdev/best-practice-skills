<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 31. Security

## 31.1 Never use `eval`, `new Function(...)`, or a `setTimeout`/
`setInterval` string argument.

```js
// bad
setTimeout('doSomething()', 1000)

// good
setTimeout(doSomething, 1000)
```

## 31.2 Never build a query string by concatenating untrusted input
into SQL; use parameterized queries.

```js
// bad — SQL injection
const rows = await db.query(`SELECT * FROM users WHERE email = '${email}'`)

// good
const rows = await db.query('SELECT * FROM users WHERE email = $1', [email])
```

## 31.3 Never put secrets in client-bundled environment variables or
Web Storage.

> Why? Any variable a bundler inlines into the client bundle (for
> example a framework's `PUBLIC_`/`NEXT_PUBLIC_`-prefixed variables) ships
> in plain text to every visitor's browser — it is public by definition,
> not a secret store.

```js
// bad
// NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_...
const stripe = new Stripe(process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY)

// good — secret key only ever read on the server
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY)
```

## 31.4 Never disable TLS/certificate verification, even
temporarily for local debugging, in code that could ship.

```js
// bad
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'

// good — fix the underlying certificate problem instead
```

## 31.5 Validate and allowlist redirect targets, file paths, and
deserialization input; never trust a client-supplied path or class
name directly.

```js
// bad — path traversal
const filePath = path.join(uploadsDir, req.query.filename)

// good
const safeName = path.basename(req.query.filename)
const filePath = path.join(uploadsDir, safeName)
if (!filePath.startsWith(uploadsDir)) {
  throw new Error('invalid path')
}
```

## 31.6 Keep dependencies patched and run an automated audit in CI.

```bash
npm audit --omit=dev
```

---
