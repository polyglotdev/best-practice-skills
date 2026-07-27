<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 19. Functions

## 19.1 Use overload signatures when a function's return type depends on a discrete set of input shapes that a union parameter cannot express precisely.

> Why? A single union-typed signature forces every caller to narrow the
> return type themselves; overloads let the compiler pick the precise
> return type at the call site automatically.

```ts
// bad
function createElement(tag: string): HTMLElement {
  return document.createElement(tag)
}
const div = createElement('div') // HTMLElement, not HTMLDivElement

// good
function createElement(tag: 'div'): HTMLDivElement
function createElement(tag: 'span'): HTMLSpanElement
function createElement(tag: string): HTMLElement {
  return document.createElement(tag)
}
const div = createElement('div') // HTMLDivElement
```

## 19.2 Keep overload signatures ordered from most specific to least specific, and give the implementation signature a broad, compatible type that is never directly visible to callers.

> Why? TypeScript picks the first matching overload; ordering general
> before specific would make the specific overloads unreachable.

```ts
// good
function query(id: string): Promise<Record>
function query(ids: string[]): Promise<Record[]>
function query(idOrIds: string | string[]): Promise<Record | Record[]> {
  // implementation
}
```

## 19.3 Type the `this` parameter explicitly for functions that are called with a meaningful receiver, and disallow `this` where it should not be used.

> Why? An explicit `this` parameter (which is erased at runtime and does not
> count toward the function's arity) lets the compiler check that the
> function is only invoked with a compatible receiver.

```ts
// good
function handleClick(this: HTMLButtonElement, event: MouseEvent) {
  this.disabled = true
}

function pureHelper(this: void, value: number): number {
  return value * 2
}
```

## 19.4 Prefer function-type aliases over repeating a full function signature inline across multiple related declarations.

```ts
// bad
function map(items: number[], fn: (item: number, index: number) => number): number[]
function filter(items: number[], fn: (item: number, index: number) => boolean): number[]

// good
type NumberMapper = (item: number, index: number) => number
type NumberPredicate = (item: number, index: number) => boolean
function map(items: number[], fn: NumberMapper): number[]
function filter(items: number[], fn: NumberPredicate): number[]
```
