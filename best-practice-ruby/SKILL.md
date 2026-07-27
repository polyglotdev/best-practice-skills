---
name: best-practice-ruby
description: Comprehensive, Airbnb-depth Ruby best practices for Ruby 4.0 — naming, classes and modules, methods and argument forwarding, blocks/procs/lambdas, mixins and refinements, metaprogramming discipline, exceptions, frozen-string-aware strings and symbols, collections, pattern matching, Struct/Data, concurrency and Ractors, plus a Rails 8.x layer (ActiveRecord, migrations, controllers, routes, jobs, mailers, service objects, testing) and RuboCop alignment. Load when writing or reviewing any .rb, .rake, .gemspec, Gemfile, or Rails file, when the user mentions Ruby, Rails, RuboCop, rubystyle.guide, or asks "is this idiomatic Ruby?". Enforces the shipped .rubocop.yml.
---

# best-practice-ruby

This skill codifies modern Ruby best practices for **Ruby 4.0** and
**Rails 8.x**. It is modeled on the depth and structure of the
[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) —
numbered rules per chapter, `> Why?` rationale, and `# bad` / `# good`
examples for every rule.

The rules trace to four upstream sources, in this precedence order:

1. **[The Ruby Style Guide](https://rubystyle.guide/)** —
   the community normative source for formatting, naming, classes, methods,
   collections, exceptions, and metaprogramming. Prefer **single quotes**
   wherever the guide allows (see
   [consistent string literals](https://rubystyle.guide/#consistent-string-literals)).
   Anchors were harvested from raw HTML into
   [`docs/reference-data/ruby-style-anchors.txt`](../docs/reference-data/ruby-style-anchors.txt).
2. **[The Rails Style Guide](https://github.com/rubocop/rails-style-guide)**
   (`rubocop/rails-style-guide`) — Rails-specific conventions for
   ActiveRecord, controllers, migrations, jobs, mailers, and views. The
   HTML mirror at [rails.rubystyle.guide](https://rails.rubystyle.guide/)
   carries the same section anchors for deep links; those anchors live in
   [`docs/reference-data/rails-style-anchors.txt`](../docs/reference-data/rails-style-anchors.txt).
3. **[Ruby language documentation](https://docs.ruby-lang.org/en/4.0/)** and
   the [Ruby 4.0 NEWS](https://github.com/ruby/ruby/blob/ruby_4_0/NEWS.md) —
   for language features the style guides predate or under-specify
   (pattern matching refinements, `Data`, Ractor, chilled/frozen strings).
4. **[Rails Guides](https://guides.rubyonrails.org/)** for Rails 8.x — only
   where the Rails style guide is silent on framework behaviour.

All formatting concerns — indentation, quotes, line length, trailing commas,
hash alignment — are owned by **RuboCop** (`rubocop -A` / `rubocop -a`) and
are never re-litigated in prose. Chapter 1 documents the tool chain and every
subsequent chapter assumes the code has been autocorrected. This is the same
delegation `best-practice-go` makes to `gofmt`, `best-practice-java` makes to
`google-java-format`, and `best-practice-kotlin` makes to `ktlint`.

**Indentation is two spaces. String literals prefer single quotes.** Both are
already RuboCop and rubystyle.guide defaults, so unlike the Python skill this
needs no house-override note.

Every rule that maps to an enabled cop in the shipped [`.rubocop.yml`](../.rubocop.yml)
carries an **`> Enforced by: Department/CopName`** callout. Rules no tool can
mechanically verify are labeled **Suggestion**, not **Violation**.

## Language version and frozen strings

The floor is **Ruby 4.0** (verified locally as **4.0.5** via asdf). RuboCop is
pinned to **1.88.2** with `rubocop-rails` **2.36.0**,
`rubocop-performance` **1.26.1**, and `rubocop-rspec` **3.10.2**.

**Frozen string literals are not the language default on Ruby 4.0.** Mutating a
literal still emits a deprecation warning (`literal string will be frozen in
the future`) under `-W:deprecated`, and the migration toward a frozen default
continues. This skill therefore requires the
`# frozen_string_literal: true` magic comment on every file (chapter 2 and
chapter 12) and treats mutable literals without the pragma as a finding.
Do not claim that Ruby 4.0 freezes every literal by default — that is false
on 4.0.5.

`rubystyle.guide` still documents several rules relative to Ruby 2.7 / 3.0 /
3.1 feature introductions. Where the guide's wording is older than 4.0, chapters
cite the guide for the _style_ rule and the Ruby 4.0 docs for the _language_
fact.

## When to use

- Writing new `.rb` / `.rake` / `.gemspec` files or reviewing existing Ruby.
- Answering "is this idiomatic?" or "does this follow the style guide?" for
  Ruby or Rails.
- Reviewing ActiveRecord queries, callbacks, migrations, strong params,
  jobs, or mailers (chapters 26 to 36).
- Setting up or auditing RuboCop for a new Ruby or Rails project (chapter 37).
- Preparing a Ruby change for code review and wanting pre-review feedback.

## Scope

- Language-level Ruby through **4.0**: classes, modules, methods, keyword
  arguments and forwarding, blocks/procs/lambdas, mixins, refinements,
  disciplined metaprogramming, exceptions, strings/symbols, collections,
  pattern matching, `Struct`/`Data`, numerics, regexps, dates/times, IO,
  concurrency and Ractors, logging, testing.
- The Ruby Style Guide and Rails Style Guide in full, with live anchors.
- **Rails 8.x**: application structure, ActiveRecord models and queries,
  migrations, controllers and strong params, routing, views/helpers, ActiveJob,
  mailers, service objects, Rails testing, and common footguns.
- Tooling: RuboCop core + Rails + Performance + RSpec departments, and the
  shipped `.rubocop.yml`. Minitest-only apps treat `RSpec/*` as N/A and
  keep core/Rails/Security enabled (chapter 37.15).

## Non-goals

- **Formatting arguments.** RuboCop owns indentation, quotes, wrapping, and
  trailing commas. Chapter 1 states the chain and later chapters move on.
- **Hanami, Sinatra, Roda, or Dry-rb stacks.** Rails is the framework layer.
- **Sorbet / RBS deep design.** Type signatures may appear as Suggestions
  where they clarify an API; a full gradual-typing skill is out of scope.
- **Frontend asset pipelines** beyond what the Rails style guide covers for
  helpers and views.
- **Deploy / infra** beyond a mention of `RAILS_ENV` and credentials access.

---

## Chapters

Each chapter is a self-contained reference file with numbered rules,
`> Why?` rationale, `# bad` / `# good` code, and `> Enforced by:` tool
callouts. Files live under `references/`.

### Part I — Style foundation

| #   | Chapter                  | File                                                                                         |
| --- | ------------------------ | -------------------------------------------------------------------------------------------- |
| 1   | Formatting & Tooling     | [`references/01-formatting-and-tooling.md`](references/01-formatting-and-tooling.md)         |
| 2   | Source Files & Structure | [`references/02-source-files-and-structure.md`](references/02-source-files-and-structure.md) |
| 3   | Naming                   | [`references/03-naming.md`](references/03-naming.md)                                         |
| 4   | Comments & YARD          | [`references/04-comments-and-yard.md`](references/04-comments-and-yard.md)                   |

### Part II — Language core

| #   | Chapter                        | File                                                                                                     |
| --- | ------------------------------ | -------------------------------------------------------------------------------------------------------- |
| 5   | Classes & Modules              | [`references/05-classes-and-modules.md`](references/05-classes-and-modules.md)                           |
| 6   | Methods & Arguments            | [`references/06-methods-and-arguments.md`](references/06-methods-and-arguments.md)                       |
| 7   | Keyword Arguments & Forwarding | [`references/07-keyword-arguments-and-forwarding.md`](references/07-keyword-arguments-and-forwarding.md) |
| 8   | Blocks, Procs & Lambdas        | [`references/08-blocks-procs-and-lambdas.md`](references/08-blocks-procs-and-lambdas.md)                 |
| 9   | Modules, Mixins & Refinements  | [`references/09-modules-mixins-and-refinements.md`](references/09-modules-mixins-and-refinements.md)     |
| 10  | Metaprogramming Discipline     | [`references/10-metaprogramming-discipline.md`](references/10-metaprogramming-discipline.md)             |
| 11  | Exceptions & Errors            | [`references/11-exceptions-and-errors.md`](references/11-exceptions-and-errors.md)                       |
| 12  | Strings & Symbols              | [`references/12-strings-and-symbols.md`](references/12-strings-and-symbols.md)                           |
| 13  | Collections & Enumerable       | [`references/13-collections-and-enumerable.md`](references/13-collections-and-enumerable.md)             |
| 14  | Hashes & Keywords              | [`references/14-hashes-and-keywords.md`](references/14-hashes-and-keywords.md)                           |
| 15  | Control Flow                   | [`references/15-control-flow.md`](references/15-control-flow.md)                                         |
| 16  | Pattern Matching               | [`references/16-pattern-matching.md`](references/16-pattern-matching.md)                                 |
| 17  | Struct, Data & Value Objects   | [`references/17-struct-data-and-value-objects.md`](references/17-struct-data-and-value-objects.md)       |
| 18  | Numeric Types                  | [`references/18-numeric-types.md`](references/18-numeric-types.md)                                       |
| 19  | Regular Expressions            | [`references/19-regular-expressions.md`](references/19-regular-expressions.md)                           |
| 20  | Dates & Times                  | [`references/20-dates-and-times.md`](references/20-dates-and-times.md)                                   |
| 21  | IO & Resources                 | [`references/21-io-and-resources.md`](references/21-io-and-resources.md)                                 |
| 22  | Concurrency & Ractors          | [`references/22-concurrency-and-ractors.md`](references/22-concurrency-and-ractors.md)                   |
| 23  | Logging                        | [`references/23-logging.md`](references/23-logging.md)                                                   |
| 24  | Testing                        | [`references/24-testing.md`](references/24-testing.md)                                                   |

### Part III — Rails 8.x

| #   | Chapter                     | File                                                                                               |
| --- | --------------------------- | -------------------------------------------------------------------------------------------------- |
| 25  | Rails Application Structure | [`references/25-rails-application-structure.md`](references/25-rails-application-structure.md)     |
| 26  | ActiveRecord Models         | [`references/26-activerecord-models.md`](references/26-activerecord-models.md)                     |
| 27  | ActiveRecord Queries        | [`references/27-activerecord-queries.md`](references/27-activerecord-queries.md)                   |
| 28  | Migrations & Schema         | [`references/28-migrations-and-schema.md`](references/28-migrations-and-schema.md)                 |
| 29  | Controllers & Strong Params | [`references/29-controllers-and-strong-params.md`](references/29-controllers-and-strong-params.md) |
| 30  | Routing                     | [`references/30-routing.md`](references/30-routing.md)                                             |
| 31  | Views & Helpers             | [`references/31-views-and-helpers.md`](references/31-views-and-helpers.md)                         |
| 32  | Jobs & ActiveJob            | [`references/32-jobs-and-activejob.md`](references/32-jobs-and-activejob.md)                       |
| 33  | Mailers                     | [`references/33-mailers.md`](references/33-mailers.md)                                             |
| 34  | Service Objects             | [`references/34-service-objects.md`](references/34-service-objects.md)                             |
| 35  | Rails Testing               | [`references/35-rails-testing.md`](references/35-rails-testing.md)                                 |
| 36  | Rails Security & Footguns   | [`references/36-rails-security-and-footguns.md`](references/36-rails-security-and-footguns.md)     |

### Part IV — Tooling

| #   | Chapter               | File                                                                               |
| --- | --------------------- | ---------------------------------------------------------------------------------- |
| 37  | RuboCop Configuration | [`references/37-rubocop-configuration.md`](references/37-rubocop-configuration.md) |

## How to use this skill

1. **Automatic loading.** The `description` in the frontmatter tells the
   agent when to load `best-practice-ruby`. When it loads, this index is
   what it reads first.
2. **Targeted reads.** For one area (say, pattern matching or ActiveRecord
   queries), open only the matching chapter under `references/`.
3. **Full review.** For a comprehensive audit, read every chapter. Each is
   exhaustive on its own topic.
4. **Layering.** Chapters 1 to 24 apply to every Ruby codebase. Chapters 25
   to 36 apply to Rails 8.x. Chapter 37 is the shipped RuboCop config.
5. **Tool config.** The recommended `.rubocop.yml` ships at this repo's root
   and is documented in chapter 37.

## Self-check

Before treating any Ruby code you write or review as finished, verify:

- The file is clean under `bundle exec rubocop`. If not, run
  `bundle exec rubocop -A` first — nothing else matters if Layout/Style
  autocorrects are pending.
- Every file starts with `# frozen_string_literal: true` (chapters 2, 12).
- String literals use single quotes unless interpolation or embedded
  apostrophes require double quotes (chapter 1).
- No `Hash[]` / `Array()` coercions for ordinary construction; prefer
  literals (chapter 13).
- No `method_missing` / `eval` / `class_eval` without a documented
  alternative and a narrow scope (chapter 10).
- Exceptions are specific classes with messages; no bare `rescue` or
  `rescue Exception` (chapter 11).
- Prefer `Data.define` or a small class over an open `Struct` for new
  value objects (chapter 17).
- **Rails only:** models inherit `ApplicationRecord`, queries use
  `find_by` / `find_each` / scopes rather than SQL string soup, controllers
  are thin, strong params are explicit, jobs inherit `ApplicationJob`,
  and bang methods (`save!`, `update!`) are used when failure must raise
  (chapters 26 to 36).
- No new `# rubocop:disable` without a scoped cop name and a reason
  (chapter 37).
