<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 10. Modules

## 10.1 Always use ES modules (`import`/`export`), not `require`.

> Why? `import`/`export` is the language-native module system, statically
> analyzable by tools, and works identically in Node 20+ and the browser.

```js
// bad
const { es6 } = require('./airbnb-style-guide')
module.exports = es6

// good
import { es6 } from './airbnb-style-guide.js'
export default es6
```

## 10.2 Do not use wildcard imports.

> Why? A wildcard import hides which bindings you actually depend on and
> defeats tree-shaking.

```js
// bad
import * as AirbnbStyleGuide from './airbnb-style-guide.js'

// good
import AirbnbStyleGuide from './airbnb-style-guide.js'
```

## 10.3 Do not export directly from an import.

> Why? Having one clear line that imports and one clear line that exports
> is more consistent than a one-liner that does both.

```js
// bad
export { es6 as default } from './airbnb-style-guide.js'

// good
import { es6 } from './airbnb-style-guide.js'
export default es6
```

## 10.4 Only import from a given path once.

> Why? Multiple import statements from the same module scatter what you're
> pulling from it and are harder to maintain than one combined statement.

```js
// bad
import { func1 } from './module.js'
import { func2 } from './module.js'

// good
import { func1, func2 } from './module.js'
```

## 10.5 Do not export mutable bindings.

> Why? A consumer that observes a mutating exported binding is coupled to
> internal mutation timing. Export a constant reference, or a function
> that returns the current value.

```js
// bad
export let count = 0

// good
let count = 0
export function getCount() {
  return count
}
export function increment() {
  count += 1
}
```

## 10.6 In a module with a single export, prefer a default export.

> Why? It encourages one file, one responsibility, and gives the importer
> the freedom to name the binding however fits their file.

```js
// good
export default function parseConfig(raw) {
  // ...
}
```

## 10.7 Put all `import`s above any non-import statement.

> Why? Imports are hoisted by the module system regardless of where they
> appear in the file, so writing them anywhere else misleads the reader
> about execution order.

```js
// bad
import foo from './foo.js'
foo.init()
import bar from './bar.js'

// good
import foo from './foo.js'
import bar from './bar.js'

foo.init()
```

## 10.8 Use named exports for anything a consumer might want to
test, mock, or import selectively; reserve default exports for a
module's single primary artifact.

> Why? Named exports are easier to re-export, tree-shake, and mock
> individually in tests; a default export is fine for "this file is
> fundamentally one thing."

```js
// good
export function formatCurrency(amount, currency = 'USD') {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  })
  return formatter.format(amount)
}

export function formatPercent(value) {
  return new Intl.NumberFormat('en-US', { style: 'percent' }).format(value)
}
```

## 10.9 Use top-level `await` in modules instead of wrapping
startup code in an async IIFE.

> Why? Top-level `await` is now standard in ES modules and Node 20+; the
> `(async () => { ... })()` wrapper it replaces was only ever a workaround.

```js
// bad
async function main() {
  const config = await loadConfig()
  startServer(config)
}
main()

// good
const config = await loadConfig()
startServer(config)
```

## 10.10 Always include file extensions in relative import
specifiers.

> Why? Node's ESM resolver, unlike some bundlers, requires an explicit
> extension for relative specifiers. Being explicit avoids environment-
> specific breakage.

```js
// bad
import { parseConfig } from './config'

// good
import { parseConfig } from './config.js'
```

---
