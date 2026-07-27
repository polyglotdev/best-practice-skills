<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 31. Library Publishing

## 31.1 Emit declaration files with declaration maps for every published package.

> Why? `declarationMap` lets consumers' editors "go to definition" straight
> into your original `.ts` source instead of stopping at the generated
> `.d.ts`, which is far more useful for debugging a consumer's type error.

```json
// good — tsconfig.json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true
  }
}
```

## 31.2 Define an explicit `exports` map in `package.json` with both `types` and `import` (and `require`, if publishing dual CJS/ESM) conditions, and put `types` first in each conditions block.

> Why? Node and bundlers resolve `exports` conditions in the order they are
> listed; `types` must come before `import`/`require` or some resolvers
> will pick a runtime entry point before finding the matching type
> declaration, causing consumers to see `any`.

```json
// bad — no explicit types condition, resolvers may guess wrong
{
  "exports": {
    ".": "./dist/index.js"
  }
}

// good
{
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    }
  }
}
```

## 31.3 Run `attw` (`are-the-types-wrong`) against every published package as a CI check.

> Why? `attw` catches the specific class of packaging bug that `tsc` cannot
> — missing `exports` conditions, mismatched ESM/CJS type resolution, and
> "masquerading as CJS/ESM" issues — that only manifest once a real
> consumer tries to `import` your package.

```json
// good — package.json scripts
{
  "scripts": {
    "check-types-published": "attw --pack ."
  }
}
```

## 31.4 Never hand-edit the emitted `.d.ts` output; fix the source `.ts` and regenerate.

> Why? Emitted declarations are a build artifact — any manual edit is lost
> on the next build and creates a divergence between what consumers see and
> what your source actually implements.

```ts
// bad — editing dist/index.d.ts directly to 'fix' a type
// good — fix src/index.ts, then rebuild
```
