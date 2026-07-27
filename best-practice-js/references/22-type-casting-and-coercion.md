<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 22. Type Casting & Coercion

## 22.1 Perform explicit type coercion at the start of a statement.

> Why? Coercion that happens implicitly mid-expression is easy to miss;
> doing it explicitly up front documents your intent.

```js
// bad
const totalScore = new String(this.reviewScore)
// typeof totalScore is "object", not "string"

// good
const totalScore = String(this.reviewScore)
```

## 22.2 Coerce numbers with `Number()` or `parseInt` with a radix,
never with `+` or unary tricks that hide intent.

> Why? `Number()`/`parseInt(str, 10)` name the operation; `+input` is
> easy to misread as an arithmetic typo.

```js
const inputValue = '4'

// bad
const val = new Number(inputValue)

// bad
const val = +inputValue

// bad
const val = parseInt(inputValue)

// good
const val = Number(inputValue)

// good
const val = parseInt(inputValue, 10)
```

## 22.3 If `parseInt` is ever slow for your use case (rare), consider
bitwise shift for the very specific case of an integer, but comment
heavily since it reduces readability.

```js
// good
/**
 * parseInt was the reason my code was slow.
 * Bitshifting the String to coerce it to a
 * Number made it a lot faster.
 */
const val = inputValue >> 0
```

## 22.4 Coerce booleans with `Boolean()` or `!!`, and comment any
bitwise usage.

```js
const age = 0

// bad
const hasAge = new Boolean(age)

// good
const hasAge = Boolean(age)

// good
const hasAge = !!age
```

---
