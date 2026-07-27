<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 6. Strings

## 6.1 Use template literals when building strings out of variables;
never concatenate with `+`.

> Why? Template literals read as the final shape of the string, avoid
> hunting for missing spaces around `+`, and support multiline content
> without escapes.

```js
// bad
function sayHi(name) {
  return 'How are you, ' + name + '?'
}

// bad
function sayHi(name) {
  return ['How are you, ', name, '?'].join()
}

// good
function sayHi(name) {
  return `How are you, ${name}?`
}
```

## 6.2 Do not write long strings across multiple lines using
backslash continuations or `+` concatenation.

> Why? Broken strings are painful to grep, diff, and read; let Prettier
> wrap the surrounding code and leave the string itself intact on one
> logical line.

```js
// bad
const errorMessage =
  'This is a super long error that was thrown because \
of Batman. When you stop to think about how Batman had anything to do \
with this, you would get nowhere fast.'

// good
const errorMessage =
  'This is a super long error that was thrown because of Batman. When you stop to think about how Batman had anything to do with this, you would get nowhere fast.'
```

## 6.3 Never use `eval()` on a string.

> Why? It executes arbitrary code with the full privileges of the calling
> context, which is one of the most common injection vectors in existence.

```js
// bad
const total = eval('2 + 2')

// good
const total = 2 + 2
```

## 6.4 Do not unnecessarily escape characters in strings.

> Why? Backslashes harm readability and should appear only when the
> character would otherwise terminate the string or literal.

```js
// bad
const foo = '\'this\' \i\s \"quoted\"'

// good
const foo = 'this is "quoted"'
const alsoGood = `my name is '${name}'`
```

## 6.5 Use `String.raw`, tagged templates, or well-known Node/Web APIs
instead of manual escaping for paths, regex source, and HTML.

> Why? Manual escaping is a common source of subtle security and
> correctness bugs; native tag functions and platform APIs already solved
> the escaping problem correctly.

```js
// bad
const pattern = new RegExp('\\d+\\.\\d+')

// good
const pattern = /\d+\.\d+/
```

---
