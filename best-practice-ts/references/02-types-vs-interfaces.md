<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 2. Types vs Interfaces

## 2.1 Use `type` for unions, intersections, tuples, and mapped/conditional shapes.

> Why? `interface` cannot express a union or a tuple directly, and mapped or
> conditional types require `type`'s aliasing mechanics.

```ts
// bad
interface Result {
  ok: boolean
  value?: string
  error?: Error
}

// good
type Result<T> = { ok: true; value: T } | { ok: false; error: Error }
```

## 2.2 Use `interface` for object shapes meant to be extended, implemented by a class, or merged via declaration merging.

> Why? `interface extends` produces clearer error messages than intersected
> type aliases on large object shapes, and only `interface` participates in
> declaration merging, which some third-party ambient typings rely on.

```ts
// good
interface UserService {
  getUser(id: string): Promise<User>
}

interface AdminUserService extends UserService {
  deleteUser(id: string): Promise<void>
}
```

## 2.3 Default to `type` for everything else; do not agonize over the choice for plain object shapes with no inheritance.

> Why? For a simple, non-extended object shape the two are functionally
> equivalent. Picking `type` as the default means the choice to use
> `interface` is always a deliberate signal — this shape merges or extends.

```ts
// good
type CreateUserInput = {
  email: string
  name: string
}
```

## 2.4 Do not mix declaration merging into ordinary application code.

> Why? Declaration merging (multiple `interface Foo` blocks with the same
> name) is a tool for augmenting ambient/third-party types (see Chapter 23),
> not a way to "add fields later" to your own interfaces. Scattering an
> interface's shape across a file makes it impossible to read its full
> contract at the definition site.

```ts
// bad
interface Config {
  apiUrl: string
}
// ...50 lines later
interface Config {
  timeout: number
}

// good
interface Config {
  apiUrl: string
  timeout: number
}
```
