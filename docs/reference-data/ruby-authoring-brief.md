# Ruby chapter authoring brief

Read before writing any `best-practice-ruby/references/*.md` chapter.

## Locked decisions

| Item | Value |
|---|---|
| Language floor | Ruby **4.0** (local 4.0.5 via asdf) |
| Framework | Rails **8.x** (latest gem line 8.1.x) |
| Linter | RuboCop **1.88.2** + rails 2.36.0 + performance 1.26.1 + rspec 3.10.2 |
| Config | Repo-root `.rubocop.yml` |
| Indent | 2 spaces |
| Quotes | **Single quotes** wherever Ruby/Rails style allows (rubystyle.guide + RuboCop `Style/StringLiterals`) |
| Ruby source | <https://rubystyle.guide/> |
| Rails source | <https://github.com/rubocop/rails-style-guide> (HTML mirror: rails.rubystyle.guide for `#anchor` deep links) |
| Frozen strings | **Not** language-default on 4.0.5. Require `# frozen_string_literal: true`. Mutation of literals warns under `-W:deprecated`. |
| Em dashes | Allowed in repo markdown (local override). |

## Chapter file contract

1. First line comment: `<!-- Part of the \`best-practice-ruby\` skill. See SKILL.md for the index. -->`
2. Title: `# N. Title`
3. 1-3 short intro paragraphs naming upstream sources with **real anchors only**.
4. Rules as `## N.M Title.` (exactly two spaces indent in prose/code samples).
5. Each rule has `> Why?` block, then a fenced `ruby` code block with `# bad` / `# good`.
6. If a shipped-enabled RuboCop cop catches it: end the Why block or follow with
   `> Enforced by: Department/CopName.` and label **Violation**.
7. Otherwise label **Suggestion** — never invent a cop name.
8. Minimum **12 rules** per chapter (tests require >= 8; aim for 12-18).
9. No emoji. Markdownlint-clean (ATX headers, fenced code with language, no trailing spaces on blank lines unnecessarily).
10. Code samples use single quotes and 2-space indent.

## Citation ground truth (mandatory)

- Ruby style anchors: `docs/reference-data/ruby-style-anchors.txt`
- Rails style anchors: `docs/reference-data/rails-style-anchors.txt`
- Cop catalogue: `docs/reference-data/rubocop-cops.txt`
- Default-enabled cops (with plugins + NewCops: enable):
  `docs/reference-data/rubocop-enabled-default.txt`
- Effective enabled set = defaults adjusted by `.rubocop.yml`

**Never** cite an anchor or cop that is not in those files.

Deep-link forms:

- Ruby: `https://rubystyle.guide/#anchor`
- Rails: cite the GitHub repo as the guide; deep-link fragments may use
  `https://rails.rubystyle.guide/#anchor` (same content as
  `rubocop/rails-style-guide`, stable HTML anchors).

## Reconciliation rule

Citing a check that exists is not enough. It must be **effectively enabled**
by `.rubocop.yml` before a rule may be labeled Violation / `Enforced by:`.
If unsure, use **Suggestion**.

## Depth target

Match sibling skills: each rule is procedural (what to do / reject / rewrite),
not a restatement of the guide title. Prefer ~300-700 lines per chapter.
Look at `best-practice-kotlin/references/03-naming.md` and
`best-practice-go/references/01-formatting.md` for tone.

## Ruby 4.0 facts that must not be wrong

- Frozen string literals are still pragma-driven on 4.0.5.
- Prefer `Data.define` for new immutable value objects; `Struct` remains valid
  but chapters should say when each wins.
- Pattern matching is stable; use `case ... in` idioms from current docs.
- Ractor exists; do not oversell it as the default concurrency model — Threads
  + Fibers remain the common path; Ractor is for CPU isolation.
