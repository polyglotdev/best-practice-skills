<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 34. Tooling defaults

## 34.1 Format with Prettier using the project's committed config;
never hand-format to "match" the style guide.

See `references/prettier.md` for the exact config this skill assumes.
Run the formatter as a pre-commit hook and in CI so no PR can drift.

## 34.2 Lint with ESLint using a modern flat config
(`eslint.config.js`) built on `@eslint/js` recommended plus a
project-appropriate plugin set; let ESLint own correctness rules and
Prettier own formatting — do not enable formatting-related ESLint rules
that fight the formatter.

```js
// eslint.config.js
import js from '@eslint/js'

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module'
    },
    rules: {
      'no-console': 'warn',
      'no-unused-vars': 'error'
    }
  }
]
```

## 34.3 Pin Node's engine version in `package.json` and enforce it
in CI.

```json
{
  "engines": {
    "node": ">=20"
  }
}
```

## 34.4 Use `type: "module"` in `package.json` for new projects so
`.js` files are ESM by default; reserve `.cjs` only for files that
genuinely must stay CommonJS.

```json
{
  "type": "module"
}
```

## 34.5 Run type-checking (via JSDoc + `tsc --checkJs`, or actual
TypeScript) in CI even in a plain-JS project, if the team wants type
safety without adopting the TypeScript build step.

---
