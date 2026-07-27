<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 1. tsconfig.json — required baseline

## 1.1 Always enable `strict: true`; never enable individual strict flags in isolation as a substitute.

> Why? `strict` is a bundle (`noImplicitAny`, `strictNullChecks`,
> `strictFunctionTypes`, `strictBindCallApply`,
> `strictPropertyInitialization`, `noImplicitThis`,
> `alwaysStrict`, `useUnknownInCatchVariables`). Turning it on wholesale
> prevents drift where a project silently reverts to loose checking after a
> TypeScript upgrade adds a new strict flag.

```json
// bad
{
  "compilerOptions": {
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}

// good
{
  "compilerOptions": {
    "strict": true
  }
}
```

## 1.2 Layer on the non-`strict` safety flags — they are not covered by `strict` but close real gaps.

> Why? `strict` does not catch unsafe index access, fallthrough switches,
> unchecked overrides, unsafe access through index signatures, or missing
> `return` on some code paths. Each of these is a common source of runtime
> `undefined` bugs that TypeScript can catch statically if asked.

```json
// good — required baseline for every project, library or app
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  }
}
```

## 1.3 Use a NodeNext module baseline for libraries and packages published to npm.

> Why? `NodeNext` mirrors Node's actual dual ESM/CJS resolution algorithm,
> including the `.js` extension requirement on relative specifiers and
> `package.json#exports` conditions. A library that type-checks under
> `NodeNext` will resolve correctly for consumers on real Node; `Bundler`
> mode hides resolution mistakes that only surface once published.

```json
// good — library tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "dist"
  }
}
```

## 1.4 Use an ESNext + Bundler baseline for application code built by Vite/webpack/Next.js/etc.

> Why? Application code never runs `tsc` as the emitter — a bundler resolves
> modules and often supports `.ts` extension imports and package
> conditions the bundler itself understands. `moduleResolution: "Bundler"`
> matches that resolution behavior instead of Node's stricter rules, while
> `noEmit` makes clear that `tsc` is a type-checker only in this setup.

```json
// good — app tsconfig.json (Vite/webpack/Next.js)
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ESNext", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "noEmit": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  }
}
```

## 1.5 Never disable `skipLibCheck`.

> Why? `skipLibCheck: false` re-checks every `.d.ts` in `node_modules`,
> including duplicated or slightly incompatible versions of the same
> library shipped transitively. This produces errors you cannot fix in code
> you do not own, and it is not a meaningful safety net — your own code was
> already checked against those types once.

```json
// bad
{ "compilerOptions": { "skipLibCheck": false } }

// good
{ "compilerOptions": { "skipLibCheck": true } }
```

## 1.6 Set `"type"` in `package.json` to match your module system and let it drive `.js`/`.d.ts` extension expectations.

> Why? Node determines whether a `.js` file is CJS or ESM from
> `package.json#type` (or a `.mjs`/`.cjs` extension). Leaving it unset
> defaults to CJS, which silently breaks `import`/`export` syntax compiled
> from `verbatimModuleSyntax` TypeScript.

```json
// good — package.json
{
  "type": "module"
}
```
