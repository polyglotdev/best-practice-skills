<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 23. Naming Conventions

## 23.1 Avoid single-letter names except for well-understood loop
indices and math; make names searchable and descriptive.

```js
// bad
function q() {
  // ...
}

// good
function query() {
  // ...
}
```

## 23.2 Use camelCase for objects, functions, and instances.

```js
// bad
const OBJEcttsssss = {}
const this_is_my_object = {}
function c() {}

// good
const thisIsMyObject = {}
function thisIsMyFunction() {}
```

## 23.3 Use PascalCase for classes and constructors.

```js
// bad
function user(options) {
  this.name = options.name
}
const bad = new user({ name: 'nope' })

// good
class User {
  constructor(options) {
    this.name = options.name
  }
}
const good = new User({ name: 'yup' })
```

## 23.4 Do not use leading or trailing underscores to fake privacy.

> Why? Underscore-prefixed names are a convention only — nothing stops
> external code from reading or writing them. Use `#field` (§9.8) for
> real privacy.

```js
// bad
this.__firstName__ = 'Panda'
this.firstName_ = 'Panda'
this._firstName = 'Panda'

// good
class Person {
  #firstName = 'Panda'
}
```

## 23.5 Don't save references to `this`; use arrow functions or
class fields instead.

```js
// bad
function foo() {
  const self = this
  return function () {
    console.log(self)
  }
}

// good
function foo() {
  return () => {
    console.log(this)
  }
}
```

## 23.6 A base filename should match the name of its default export.

```js
// file 1 contents
class CheckBox {
  // ...
}
export default CheckBox

// file 2 contents
export default function fortyTwo() {
  return 42
}

// file 3 contents
export default function insideDirectory() {
  // ...
}

// in some other file
// bad
import CheckBox from './checkBox.js'
// PascalCase import/export, camelCase filename
import FortyTwo from './FortyTwo.js'
// PascalCase import/filename, camelCase export
import InsideDirectory from './InsideDirectory.js'

// bad
import CheckBox from './check_box.js'
import FortyTwo from './forty_two.js'
import InsideDirectory from './inside_directory.js'

// good
import CheckBox from './CheckBox.js'
import fortyTwo from './fortyTwo.js'
import insideDirectory from './insideDirectory.js'
```

## 23.7 Use camelCase when you export a default function; use
PascalCase when you export a constructor/class.

```js
function makeStyleGuide() {
  // ...
}
export default makeStyleGuide

class StyleGuide {
  // ...
}
export default StyleGuide
```

## 23.8 Use PascalCase or SCREAMING_SNAKE_CASE only for names that
are genuinely acronym-like singletons or true constants; do not
decorate every export.

> Why? Reserving SCREAMING_SNAKE_CASE for real constants (config
> values that never change, enum-like maps) keeps it meaningful; using it
> everywhere dilutes the signal.

```js
// bad
const PRIVATE_VARIABLE = 'should not be reassigned'
export const THING_TO_BE_CHANGED = 'should obviously not be reassigned'

// good
export const API_BASE_URL = 'https://api.example.com'
export const MAX_RETRIES = 3
```

---
