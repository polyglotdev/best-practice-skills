<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 29. Node.js specifics

## 29.1 Use the `node:` prefix for built-in modules.

> Why? It disambiguates a core module from a same-named package in
> `node_modules`, and it's required for some built-ins to be importable
> at all in newer Node versions.

```js
// bad
import fs from 'fs'
import path from 'path'

// good
import fs from 'node:fs'
import path from 'node:path'
```

## 29.2 Use `node:fs/promises`, never the callback-style `fs` API,
in new code.

```js
// bad
import fs from 'node:fs'

fs.readFile('config.json', 'utf8', (err, data) => {
  if (err) throw err
  console.log(data)
})

// good
import { readFile } from 'node:fs/promises'

const data = await readFile('config.json', 'utf8')
console.log(data)
```

## 29.3 Build and validate URLs with the `URL` class, not string
concatenation.

```js
// bad
const endpoint = baseUrl + '/users/' + userId + '?active=' + isActive

// good
const endpoint = new URL(`/users/${userId}`, baseUrl)
endpoint.searchParams.set('active', String(isActive))
```

## 29.4 Read configuration from `process.env`, validate it once at
startup, and never scatter raw `process.env.X` reads through business
logic.

> Why? Centralizing env access gives you one place to validate
> required variables and fail fast, instead of discovering a missing
> variable deep in a request handler at runtime.

```js
// bad — scattered, unvalidated
function connectToDb() {
  return createConnection(process.env.DATABASE_URL)
}

// good
function loadConfig() {
  const databaseUrl = process.env.DATABASE_URL
  if (!databaseUrl) {
    throw new Error('DATABASE_URL is required')
  }
  return { databaseUrl }
}

const config = loadConfig()
```

## 29.5 Use `node --test` or Vitest's watch mode during
development; never `console.log`-driven debugging as the primary
verification method for shipped code.

## 29.6 Prefer native `fetch` (global since Node 18) over `http`/
`https` request boilerplate or third-party HTTP clients for simple
requests.

```js
// bad
import https from 'node:https'

function getJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let body = ''
      res.on('data', (chunk) => {
        body += chunk
      })
      res.on('end', () => resolve(JSON.parse(body)))
      res.on('error', reject)
    })
  })
}

// good
async function getJson(url) {
  const response = await fetch(url)
  return response.json()
}
```

## 29.7 Use `import.meta.url` (not `__dirname`/`__filename`, which
don't exist in ESM) when you need the current module's location.

```js
// good
import { fileURLToPath } from 'node:url'

const currentFile = fileURLToPath(import.meta.url)
```

---
