# Prettier config this skill assumes

Every code example in `SKILL.md` is written to satisfy this exact
Prettier configuration. When in doubt, defer to the formatter's output
rather than to prose in this document.

```json
{
  "arrowParens": "always",
  "bracketSameLine": false,
  "bracketSpacing": true,
  "embeddedLanguageFormatting": "auto",
  "htmlWhitespaceSensitivity": "css",
  "insertPragma": false,
  "jsxSingleQuote": false,
  "printWidth": 80,
  "proseWrap": "preserve",
  "quoteProps": "as-needed",
  "requirePragma": false,
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "none",
  "useTabs": false,
  "vueIndentScriptAndStyle": false
}
```

## What this means concretely

1. **No trailing semicolons.** Statements end with a newline, not `;`.
   Prettier inserts a leading `;` automatically only in the rare case a
   line would otherwise be misparsed (for example a line starting with
   `(`, `[`, or a template literal right after a line with no
   semicolon) — write natural code and let the formatter handle it.
2. **Single quotes** for all JS/TS strings. JSX attribute values use
   double quotes (`className="foo"`) per `jsxSingleQuote: false`.
3. **2-space indentation**, spaces only, never tabs.
4. **No trailing commas** anywhere — arrays, objects, function
   parameters, imports.
5. **Arrow functions always parenthesize their parameter list**, even
   with exactly one parameter: `(x) => x + 1`.
6. **Spaces inside object braces**: `{ a: 1 }`, not `{a: 1}`.
7. **80-column print width** — Prettier decides the exact wrap points;
   don't hand-wrap to a different width.
8. **Multiline JSX** puts the closing `>` on its own line
   (`bracketSameLine: false`).

## Why this skill never restates Airbnb's formatting opinions

Airbnb's guide predates widespread Prettier adoption and encodes its
own formatting preferences (semicolons required, trailing commas
required, etc.) directly into "the style guide." Those opinions are
exactly the class of decision Prettier now owns mechanically. Rather
than debate them, this skill always defers to the config above:
wherever Airbnb's prose or examples conflict with it, the config wins
silently, with no need to call out the disagreement in review comments
or documentation.
