<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 21. Semicolons

Handled by Prettier — see `references/prettier.md`. Our config sets
`semi: false`: no semicolons at the end of statements, ever. The one
place this needs deliberate care is a line that would otherwise start
with `(`, `[`, `` ` ``, `+`, `-`, or `/` right after a line with no
semicolon — Prettier already inserts a disambiguating leading `;` for
you in that rare case, so write natural code and let the formatter
handle ASI edge cases rather than avoiding the construct altogether.

---
