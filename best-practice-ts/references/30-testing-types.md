<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 30. Testing Types

## 30.1 Write compile-time type tests for exported generic utilities and complex conditional types, not just runtime unit tests.

> Why? A runtime test only exercises one concrete instantiation of a
> generic type; a type-level test can assert the type relationship holds
> for the general case, catching regressions a runtime test would miss
> entirely.

```ts
// good — using vitest's built-in expectTypeOf
import { expectTypeOf, test } from 'vitest'
import { pick } from './pick'

test('pick narrows to the selected keys', () => {
  const result = pick({ id: '1', name: 'Ada', age: 30 }, ['id', 'name'])
  expectTypeOf(result).toEqualTypeOf<{ id: string; name: string }>()
})
```

## 30.2 Use `tsd` for type tests in libraries that do not already depend on a test runner with built-in type assertions.

```ts
// good — test-d/pick.test-d.ts
import { expectType } from 'tsd'
import { pick } from '../src/pick'

const result = pick({ id: '1', name: 'Ada', age: 30 }, ['id', 'name'])
expectType<{ id: string; name: string }>(result)
```

## 30.3 Assert both the positive case (types that should be assignable) and the negative case (types that should error) for validation-sensitive utilities.

```ts
// good
import { expectTypeOf, test } from 'vitest'

test('Result narrows by discriminant', () => {
  type R = { ok: true; value: number } | { ok: false; error: string }
  const success: R = { ok: true, value: 1 }
  if (success.ok) {
    expectTypeOf(success.value).toBeNumber()
  }
})
```
