<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 17. Conditional Types & `infer`

## 17.1 Use conditional types to branch a type based on an `extends` check, and format multi-line conditional types with each branch indented.

> Why? Long single-line conditional types are hard to scan; aligning the
> `?`/`:` branches on their own lines mirrors the readability rules for
> multi-line ternaries in `best-practice-js`.

```ts
// good
type ElementType<T> = T extends readonly (infer U)[]
  ? U
  : T extends Promise<infer U>
    ? U
    : T
```

## 17.2 Use `infer` to extract a nested type from within a larger generic type instead of duplicating the structure manually.

```ts
// bad
type UnwrapPromise<T> = T extends Promise<any> ? T['then'] extends (...a: any[]) => any ? any : never : T

// good
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T
```

## 17.3 Use distributive conditional types deliberately, and wrap the checked type in a tuple (`[T]`) when distribution over a union must be suppressed.

> Why? A naked type parameter on the left of `extends` distributes over
> unions member-by-member, which is usually desired but sometimes must be
> disabled to check the union as a whole.

```ts
// good — distributes: ToArray<string | number> = string[] | number[]
type ToArray<T> = T extends unknown ? T[] : never

// good — does not distribute: checks the union as one type
type IsUnion<T, U = T> = T extends U ? ([U] extends [T] ? false : true) : never
```

## 17.4 Keep recursive conditional types tail-bounded with an explicit base case to avoid "Type instantiation is excessively deep" errors.

> Why? TypeScript's recursion limit is a hard compiler error, not a
> warning; an unbounded recursive type fails to compile once it is used
> with a sufficiently large input type.

```ts
// good
type Flatten<T> = T extends readonly [infer Head, ...infer Rest]
  ? Head extends readonly unknown[]
    ? [...Flatten<Head>, ...Flatten<Rest>]
    : [Head, ...Flatten<Rest>]
  : []
```
