<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 6. Union Types

## 6.1 Sort union members with the most likely / primary case first when order carries meaning for readers, otherwise alphabetize for long unions.

> Why? Consistent ordering makes unions diffable and easy to scan; without a
> convention, unrelated PRs reorder members and create noisy diffs.

```ts
// good
type Theme = 'light' | 'dark' | 'system'
```

## 6.2 Use a leading `|` and one member per line once a union no longer fits on one line.

> Why? Vertical alignment with a leading pipe makes it trivial to add,
> remove, or diff a single member without touching neighboring lines.

```ts
// bad
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'

// good
type HttpMethod =
  | 'GET'
  | 'POST'
  | 'PUT'
  | 'PATCH'
  | 'DELETE'
  | 'HEAD'
  | 'OPTIONS'
```

## 6.3 Avoid unions that mix structurally incompatible shapes without a discriminant.

> Why? Without a common tag, narrowing requires ad hoc property checks that
> break the moment either shape gains an overlapping field. See Chapter 8
> for the fix.

```ts
// bad
type Event = { type: 'click'; x: number } | { x: number; y: number }

// good
type Event =
  | { type: 'click'; x: number; y: number }
  | { type: 'scroll'; deltaY: number }
```
