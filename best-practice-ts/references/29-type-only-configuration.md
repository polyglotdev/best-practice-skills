<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 29. Type-only Configuration

## 29.1 Use `satisfies` on framework config objects (bundler configs, CLI configs, ORM configs) instead of a plain object or a type annotation.

> Why? Framework config types are usually large unions of optional fields;
> `satisfies` catches a typo'd key immediately while still letting you
> `import` the resulting object and get literal-typed access to whatever
> you actually set.

```ts
// good — vite.config.ts-style example
import type { UserConfig } from 'some-bundler'

const config = {
  root: 'src',
  build: { outDir: 'dist', sourcemap: true }
} satisfies UserConfig

export default config
```

## 29.2 Prefer a defining function (`defineConfig`) exported by the framework over a bare `satisfies` when the framework provides one.

> Why? A `defineConfig` helper can offer better inference than a static
> `satisfies` check when the config shape depends on the environment or
> plugins passed in, since it can be a generic function rather than a fixed
> type.

```ts
// good
import { defineConfig } from 'some-bundler'

export default defineConfig({
  root: 'src',
  build: { outDir: 'dist', sourcemap: true }
})
```
