<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 14. Hoisting

## 14.1 Know the difference: `var` hoists and initializes to
`undefined`; `let`/`const` hoist into the Temporal Dead Zone (TDZ) and
throw if read before their declaration.

> Why? Understanding the TDZ explains why `let`/`const` "feel" safer —
> they turn a whole class of "used before defined" bugs into an
> immediate `ReferenceError` instead of a silent `undefined`.

```js
// we know this wouldn't work (assuming there
// is no notDefined global variable)
function example() {
  console.log(notDefined)
  // => throws a ReferenceError
}

// creating a variable declaration after you
// reference the variable will work due to variable hoisting
// Note: the assignment value of `true` is not hoisted
function example() {
  console.log(declaredButNotAssigned)
  // => undefined
  var declaredButNotAssigned = true
}

// the interpreter is hoisting the variable
// declaration to the top of the scope,
// which means our example could be rewritten as:
function example() {
  let declaredButNotAssigned
  console.log(declaredButNotAssigned)
  // => undefined
  declaredButNotAssigned = true
}

// using const and let
function example() {
  console.log(declaredButNotAssigned)
  // => throws a ReferenceError
  console.log(typeof declaredButNotAssigned)
  // => throws a ReferenceError
  const declaredButNotAssigned = true
}
```

## 14.2 Anonymous function expressions hoist only the variable name,
not the assignment.

```js
function example() {
  console.log(anonymous)
  // => undefined

  anonymous()
  // => TypeError anonymous is not a function

  var anonymous = function () {
    console.log('anonymous function expression')
  }
}
```

## 14.3 Named function expressions hoist the variable name, not the
function name or body.

```js
function example() {
  console.log(named)
  // => undefined

  named()
  // => TypeError named is not a function

  superPower()
  // => ReferenceError superPower is not defined

  var named = function superPower() {
    console.log('Flying')
  }
}
```

## 14.4 Function declarations hoist both their name and their body.

> Why? This is precisely the surprising power that motivates §7.1 —
> preferring assigned function expressions makes execution order visible
> in the file, whereas a declaration is fully usable before its own line.

```js
function example() {
  superPower()
  // => Flying

  function superPower() {
    console.log('Flying')
  }
}
```

---
