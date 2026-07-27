# best-practice-ruby

An exhaustive, Airbnb-depth **Agent Skill** for writing and reviewing Ruby
4.0 and Rails 8.x, aligned to RuboCop.

**610 numbered rules across 37 chapters, ~14.5k lines.** Every rule is
justified with a `> Why?`, shown with `# bad` / `# good` code, and where a
shipped-enabled RuboCop cop catches it, labeled
`> Enforced by: Department/CopName`.

## Upstream sources, in precedence order

1. **[The Ruby Style Guide](https://rubystyle.guide/)** — normative for
   formatting, naming, classes, methods, collections, exceptions, and
   metaprogramming. Prefer **single quotes** wherever the guide allows
   ([consistent string literals](https://rubystyle.guide/#consistent-string-literals)).
2. **[The Rails Style Guide](https://github.com/rubocop/rails-style-guide)** —
   Rails conventions for ActiveRecord, controllers, migrations, jobs,
   mailers, and views. Deep links use the HTML mirror at
   [rails.rubystyle.guide](https://rails.rubystyle.guide/) (same section
   anchors).
3. **[Ruby 4.0 language docs](https://docs.ruby-lang.org/en/4.0/)** and
   [NEWS](https://github.com/ruby/ruby/blob/ruby_4_0/NEWS.md).
4. **[Rails Guides](https://guides.rubyonrails.org/)** where the style
   guide is silent on framework behaviour.

Anchors were harvested from raw HTML into [`docs/reference-data/`](docs/reference-data/)
rather than inferred from section titles.

## Style defaults

| Setting | Value | Notes |
|---|---|---|
| Indent | 2 spaces | rubystyle.guide + RuboCop default |
| Quotes | Single quotes | `Style/StringLiterals` |
| Column soft limit | 100 | `Layout/LineLength` |
| Frozen strings | `# frozen_string_literal: true` required | **Not** language-default on Ruby 4.0.5 |

## Tooling

| Tool | Role |
|---|---|
| RuboCop 1.88.2 | Formatter (`rubocop -A`) and linter |
| rubocop-rails 2.36.0 | Rails Style Guide cops |
| rubocop-performance 1.26.1 | Hot-path / Enumerable cops |
| rubocop-rspec 3.10.2 | Suite hygiene |

Config ships at repo-root [`.rubocop.yml`](.rubocop.yml). Unlike Java/Kotlin,
there is no separate formatter binary — RuboCop owns Layout and Style
autocorrect.

## Language floor

**Ruby 4.0** (verified locally as 4.0.5 via asdf). Framework layer is
**Rails 8.x**.

Frozen string literals remain pragma-driven on 4.0.5; mutating a literal
without the pragma warns under `-W:deprecated`. Chapters 2 and 12 state
this explicitly so agents do not claim a frozen-by-default language.

## Chapters

### Part I — Style foundation

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 1 | Formatting & Tooling | 18 | 524 |
| 2 | Source Files & Structure | 15 | 401 |
| 3 | Naming | 18 | 518 |
| 4 | Comments & YARD | 14 | 350 |

### Part II — Language core

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 5 | Classes & Modules | 15 | 519 |
| 6 | Methods & Arguments | 17 | 473 |
| 7 | Keyword Arguments & Forwarding | 14 | 353 |
| 8 | Blocks, Procs & Lambdas | 17 | 424 |
| 9 | Modules, Mixins & Refinements | 15 | 528 |
| 10 | Metaprogramming Discipline | 15 | 432 |
| 11 | Exceptions & Errors | 16 | 420 |
| 12 | Strings & Symbols | 16 | 399 |
| 13 | Collections & Enumerable | 18 | 383 |
| 14 | Hashes & Keywords | 18 | 375 |
| 15 | Control Flow | 17 | 460 |
| 16 | Pattern Matching | 16 | 462 |
| 17 | Struct, Data & Value Objects | 15 | 394 |
| 18 | Numeric Types | 16 | 308 |
| 19 | Regular Expressions | 17 | 328 |
| 20 | Dates & Times | 15 | 307 |
| 21 | IO & Resources | 16 | 300 |
| 22 | Concurrency & Ractors | 15 | 329 |
| 23 | Logging | 15 | 263 |
| 24 | Testing | 20 | 440 |

### Part III — Rails 8.x

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 25 | Rails Application Structure | 17 | 452 |
| 26 | ActiveRecord Models | 21 | 559 |
| 27 | ActiveRecord Queries | 22 | 439 |
| 28 | Migrations & Schema | 15 | 345 |
| 29 | Controllers & Strong Params | 15 | 358 |
| 30 | Routing | 14 | 302 |
| 31 | Views & Helpers | 15 | 324 |
| 32 | Jobs & ActiveJob | 15 | 322 |
| 33 | Mailers | 17 | 322 |
| 34 | Service Objects | 14 | 318 |
| 35 | Rails Testing | 20 | 374 |
| 36 | Rails Security & Footguns | 20 | 368 |

### Part IV — Tooling

| # | Chapter | Rules | Lines |
|---|---------|------:|------:|
| 37 | RuboCop Configuration | 17 | 308 |

## Verification

```bash
python3 -m unittest tests.test_ruby_skill -v
```

The suite checks chapter presence, rule headers, SKILL.md index links,
style-guide anchors against harvested lists, and every `Enforced by:`
cop against the effective enabled set of `.rubocop.yml`.

## Known gaps / follow-ups

- Depth is closer to the Go track than the 30k-line Kotlin track. Rails
  chapters 25-27, 33, and 35-37 were thickened against unused
  rails.rubystyle.guide anchors; remaining thin chapters (routing,
  views, jobs, service objects, migrations) can still grow.
- Live citation pass against rubystyle.guide / rails.rubystyle.guide HTML
  (2026-07-27): **0 broken cited anchors**. Harvest refreshed with
  `app-config` and `app-validators`. A full adversarial per-batch rewrite
  verify (Java/Kotlin method) was not re-run end-to-end.
- `rubocop-rspec` remains in the shipped config. Minitest-only apps treat
  `RSpec/*` as **N/A** (chapters 24, 35, 37.15) and must not disable
  core/Rails/Security departments to quiet RSpec.
