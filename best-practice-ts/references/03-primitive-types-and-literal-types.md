<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 3. Primitive Types & Literal Types

## 3.1 Prefer literal types and literal unions over `string`/`number` when the domain is a closed set.

> Why? A closed set of allowed values caught at compile time eliminates an
> entire class of typo bugs that `string` cannot catch.

```ts
// bad
function setStatus(status: string) {}
setStatus('pendign') // compiles, wrong at runtime

// good
type Status = 'pending' | 'active' | 'archived'
function setStatus(status: Status) {}
setStatus('pendign') // Error: Argument of type 'pendign' is not assignable
```

## 3.2 Annotate the empty-collection and ambiguous-literal cases explicitly; let inference handle the rest.

> Why? TypeScript infers `string`, `number`, `boolean` correctly from
> literals, but widens an empty array to `any[]` or `never[]` depending on
> context, and inference cannot narrow a general-purpose literal to the
> specific union you intend.

```ts
// bad
const tags = [] // any[] in a loose file, or inferred too broadly
const status = 'pending' // widened to string in some contexts

// good
const tags: string[] = []
const status: Status = 'pending'
```

## 3.3 Never use the boxed wrapper types `Number`, `String`, `Boolean`, `Object` as type annotations.

> Why? These refer to the wrapper object types (`new Number(1)`), not the
> primitives, and accept values you did not intend, defeating the purpose of
> the annotation.

```ts
// bad
function double(n: Number): Number {
  return n.valueOf() * 2
}

// good
function double(n: number): number {
  return n * 2
}
```

## 3.4 Use `bigint` and `symbol` only when interoperating with an API that requires them; do not use them as ID types by default.

> Why? `bigint` cannot be serialized by `JSON.stringify`, and `symbol` cannot
> cross a network or storage boundary at all. A string or number ID is
> almost always the right choice for anything that will be persisted or
> transmitted.

```ts
// bad — breaks JSON.stringify(order)
type OrderId = bigint

// good
type OrderId = string
```
