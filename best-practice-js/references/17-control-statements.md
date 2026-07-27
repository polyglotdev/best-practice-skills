<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 17. Control Statements

## 17.1 When a control statement's condition is too long, break the
condition, with each group of the logical operator starting a new line.

> Why? Requiring the operator on the new line keeps operators aligned in
> a similar place, which mirrors method chaining and keeps the visual
> pattern consistent.

```js
// bad
if (someReallyLongVariableNameThatIsUnwieldy && anotherLongVariableName) {
  thing1()
}

// good
if (
  someReallyLongVariableNameThatIsUnwieldy &&
  anotherLongVariableName
) {
  thing1()
}

// good
if (someReallyLongVariableNameThatIsUnwieldy) {
  thing1()
}
```

## 17.2 Don't use selection operators (`&&`, `||`, `?:`) in place of
control statements when the intent is a statement, not an expression.

> Why? `condition && doThing()` looks like a value-producing expression
> but is really an imperative statement in disguise, which surprises
> readers scanning for side effects.

```js
// bad
!isRunning && startProcess()

// good
if (!isRunning) {
  startProcess()
}
```

## 17.3 Prefer guard clauses and early returns over `if`/`else if`
ladders more than two branches deep.

```js
// bad
function getDiscount(customer) {
  if (customer.tier === 'gold') {
    return 0.2
  } else if (customer.tier === 'silver') {
    return 0.1
  } else if (customer.tier === 'bronze') {
    return 0.05
  } else {
    return 0
  }
}

// good
const DISCOUNTS_BY_TIER = {
  gold: 0.2,
  silver: 0.1,
  bronze: 0.05
}

function getDiscount(customer) {
  return DISCOUNTS_BY_TIER[customer.tier] ?? 0
}
```

## 17.4 Every `switch` must have a `default` case, and every
non-empty `case` must `break` or `return`.

> Why? An omitted `default` silently drops unanticipated values; a
> missing `break` silently falls through to the next case.

```js
// bad
switch (status) {
  case 'active':
    handleActive()
  case 'inactive':
    handleInactive()
    break
}

// good
switch (status) {
  case 'active':
    handleActive()
    break
  case 'inactive':
    handleInactive()
    break
  default:
    handleUnknown(status)
}
```

---
