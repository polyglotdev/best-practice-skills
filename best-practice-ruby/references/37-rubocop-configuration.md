<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 37. RuboCop Configuration

Every `> Enforced by:` and **Violation** callout in this skill points at a
real cop that is effectively enabled by the shipped
[`.rubocop.yml`](../../.rubocop.yml). This chapter is that configuration:
how RuboCop relates to
[The Ruby Style Guide](https://rubystyle.guide/) and the
[Rails Style Guide](https://github.com/rubocop/rails-style-guide), which
plugins ship, and how to suppress findings without lying to CI.

Unlike Java (formatter vs Checkstyle vs Error Prone) or Kotlin (ktlint vs
detekt), **RuboCop is both formatter and linter**. `bundle exec rubocop -A`
owns Layout and autocorrectable Style; the same process reports Lint,
Security, Rails, Performance, Metrics, and RSpec. Chapter 1 covers the
day-to-day format workflow; this chapter covers the config those commands
read.

**Pins (verified under asdf Ruby 4.0.5):** RuboCop **1.88.2**,
`rubocop-rails` **2.36.0**, `rubocop-performance` **1.26.1**,
`rubocop-rspec` **3.10.2**.

## 37.1 Ship one root `.rubocop.yml` and run it through `bundle exec`.

> Why? Editor-global RuboCop and project RuboCop diverge. `bundle exec`
> forces the Gemfile pins so CI and laptops share cop names and defaults.
> **Suggestion.**

```bash
# bad — whatever gem the OS Ruby has
rubocop

# good
bundle exec rubocop
bundle exec rubocop -A
```

## 37.2 Set `AllCops/TargetRubyVersion` to the skill floor (4.0).

> Why? Cops that gate on language syntax (arguments forwarding, numbered
> parameters, pattern matching) enable or disable based on this value. A
> 3.2 target on a 4.0 codebase hides modern autocorrects.
> **Suggestion.**

```yaml
# good — excerpt from the shipped config
AllCops:
  TargetRubyVersion: 4.0
  NewCops: enable
```

## 37.3 Enable the Rails, Performance, and RSpec plugins explicitly.

> Why? Core RuboCop does not know about `ApplicationRecord` or
> `have_http_status`. The Rails Style Guide's mechanical rules live in
> `rubocop-rails`; RSpec suite hygiene lives in `rubocop-rspec`. For
> Minitest-only apps, see 37.15 before copying this block wholesale.
> **Suggestion.**

```yaml
plugins:
  - rubocop-rails
  - rubocop-performance
  - rubocop-rspec
```

## 37.4 Prefer single quotes via `Style/StringLiterals`.

> Why? [consistent-string-literals](https://rubystyle.guide/#consistent-string-literals)
> and this skill both prefer single quotes wherever Ruby style allows.
> Double quotes remain correct for interpolation and embedded apostrophes;
> RuboCop switches those automatically under `-A`.
> **Violation.**
>
> Enforced by: Style/StringLiterals.

```yaml
Style/StringLiterals:
  EnforcedStyle: single_quotes

Style/StringLiteralsInInterpolation:
  EnforcedStyle: single_quotes
```

```ruby
# bad
name = "Ada"

# good
name = 'Ada'

# good — interpolation requires double quotes
greeting = "Hello, #{name}"
```

## 37.5 Require `# frozen_string_literal: true` on every file.

> Why? Ruby 4.0.5 still does **not** freeze literals by default; mutating a
> literal warns under `-W:deprecated`. The pragma is the honest contract
> until the language default flips.
> **Violation.**
>
> Enforced by: Style/FrozenStringLiteralComment.

```yaml
Style/FrozenStringLiteralComment:
  Enabled: true
  EnforcedStyle: always
```

## 37.6 Keep Layout cops enabled — do not split formatting into a second tool.

> Why? Introducing Prettier-for-Ruby *and* RuboCop Layout guarantees fights.
> RuboCop owns indentation width (2), line length (100), trailing commas,
> and hash alignment in this repo.
> **Suggestion.**

```yaml
Layout/IndentationWidth:
  Width: 2

Layout/LineLength:
  Max: 100
```

## 37.7 Exclude generated and third-party trees, not `app/` and `lib/`.

> Why? Broad `Exclude: ['**/*']` with tiny includes is how teams disable
> RuboCop without admitting it. Exclude schema, vendor, bundles, and build
> products only.
> **Suggestion.**

```yaml
AllCops:
  Exclude:
    - 'db/schema.rb'
    - 'vendor/**/*'
    - 'node_modules/**/*'
    - 'tmp/**/*'
```

## 37.8 Treat Metrics ceilings as soft; tune with evidence, do not delete the department.

> Why? `Metrics/AbcSize` and friends are heuristics. Raising a limit for a
> known parser method is fine; deleting Metrics because one file hurts is
> how complexity returns unnoticed.
> **Suggestion.**

```yaml
Metrics/MethodLength:
  Max: 20
  CountAsOne: ['array', 'hash', 'heredoc']
```

## 37.9 Keep Security cops on for application code.

> Why? `Security/Eval`, `JSONLoad`, `MarshalLoad`, `Open`, and `YAMLLoad`
> catch the chapter 36 footguns mechanically. Disabling them for one rake
> task belongs in a scoped disable, not a global off switch.
> **Violation** when those patterns appear.
>
> Enforced by: Security/Eval.

```yaml
Security/Eval:
  Enabled: true
```

## 37.10 Map Rails Style Guide rules to `Rails/*` cops rather than prose-only reviews.

> Why? The GitHub Rails Style Guide and `rubocop-rails` are maintained
> together. Prefer enabling `Rails/SaveBang`, `Rails/FindEach`,
> `Rails/OutputSafety`, `Rails/TimeZone`, and friends over hoping reviewers
> remember.
> **Suggestion.**

```yaml
Rails/SaveBang:
  Enabled: true
  AllowImplicitReturn: false

Rails/OutputSafety:
  Enabled: true

Rails/TimeZone:
  Enabled: true
```

## 37.11 Scope `# rubocop:disable` to one cop and one region, with a reason.

> Why? File-wide `# rubocop:disable all` trains the suite to ignore real
> defects. Disable the specific cop, wrap the smallest block, and leave a
> comment a future reader can act on.
> **Violation.**
>
> Enforced by: Style/DisableCopsWithinSourceCodeDirective.

```ruby
# bad
# rubocop:disable all
def generate
  # ...
end

# good
# Metrics/AbcSize: generated state machine; do not hand-simplify.
# rubocop:disable Metrics/AbcSize
def generate
  # ...
end
# rubocop:enable Metrics/AbcSize
```

## 37.12 Reconcile every skill `Enforced by:` against the effective enabled set.

> Why? Citing a cop that exists but is disabled is a false Violation. After
> config edits, diff callouts against
> `docs/reference-data/rubocop-effective-enabled.txt` (or regenerate it from
> `rubocop --show-cops` under this `.rubocop.yml`). Downgrade to
> **Suggestion** or enable the cop — never leave a false claim.
> **Suggestion.**

```bash
# regenerate catalogues after bumping RuboCop
bundle exec rubocop --show-cops | \
  grep -oE '^[A-Z][A-Za-z]+/[A-Za-z0-9]+' | sort -u
```

## 37.13 Run autocorrect in CI only as an explicit job, never as the gate.

> Why? A gate that rewrites files mid-pipeline produces dirty checkouts.
> CI should run `bundle exec rubocop` (read-only). Developers and a
> scheduled "apply" job run `-A`.
> **Suggestion.**

```yaml
# good — CI
script: bundle exec rubocop

# good — local / maintenance
bundle exec rubocop -A
```

## 37.14 Document plugin and RuboCop version pins next to the config.

> Why? Cop renames between minors are a real failure mode (this skill
> already dropped fabricated `Rails/*` names that do not exist on 2.36.0).
> The header comment in `.rubocop.yml` is the source of truth for pins.
> **Suggestion.**

```yaml
# Pin: rubocop 1.88.2, rubocop-rails 2.36.0,
# rubocop-performance 1.26.1, rubocop-rspec 3.10.2
```

## 37.15 Minitest-only apps: treat `RSpec/*` as N/A; never disable core or Rails departments to silence them.

> Why? This skill ships `rubocop-rspec` because many Rails apps use RSpec.
> A Minitest suite should either omit the RSpec plugin, exclude
> `spec/**/*`, or ignore `RSpec/*` findings as **N/A**. Turning off
> `Rails`, `Security`, `Lint`, or `Performance` because "we are not on
> RSpec" deletes the cops that still apply to `app/` and `test/`.
> **Suggestion.**

```yaml
# good — Minitest app keeps Rails/Security; drops only RSpec
plugins:
  - rubocop-rails
  - rubocop-performance
  # rubocop-rspec intentionally omitted

# bad — silencing the wrong departments
Rails:
  Enabled: false
Security:
  Enabled: false
```

## 37.16 Keep `NewCops: enable` so RuboCop minors surface new guide-aligned cops.

> Why? RuboCop and `rubocop-rails` add cops between releases. Pending
> new cops stay silent unless `NewCops: enable` (as in the shipped
> config). Review new findings on upgrade; do not leave them pending
> forever.
> **Suggestion.**

```yaml
AllCops:
  TargetRubyVersion: 4.0
  NewCops: enable
```

## 37.17 Prefer department-level excludes over global `# rubocop:disable` in generated files only.

> Why? Migrations and schema dumps are already excluded at the root.
> Adding more path excludes is fine for generated clients; sprinkling
> file-level disables through `app/` hides real defects. Pair with 37.11.
> **Suggestion.**

```yaml
# good — generated GraphQL client
Metrics/MethodLength:
  Exclude:
    - 'app/graphql/generated/**/*'

# bad — blanket disable copied into every controller
```
