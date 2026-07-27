<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 1. Formatting & Tooling

Ruby settled the formatting debate the same way Go and Kotlin did: pick one
tool, run it everywhere, and stop arguing about whitespace. The normative
layout rules live in the Ruby Style Guide's
[Source Code Layout](https://rubystyle.guide/#source-code-layout) section —
two-space indent, single quotes by default, 100-column soft limit, no
trailing whitespace, final newline. RuboCop implements those decisions (and
the house overrides in the shipped [`.rubocop.yml`](../../.rubocop.yml)) as
`Layout/*` and `Style/*` cops. This chapter is about handing every layout
decision to `bundle exec rubocop -A` and never having the argument again.

That delegation is the same one
[`best-practice-go`](../../best-practice-go/references/01-formatting.md) makes
to `gofmt`, `best-practice-java` makes to `google-java-format`, and
`best-practice-kotlin` makes to `ktlint`. Every code sample in every chapter
of this skill is written as RuboCop with the shipped config would emit it, and
no later chapter re-litigates a single whitespace decision.

**Indentation is two spaces. String literals prefer single quotes.** Both are
RuboCop and rubystyle.guide defaults, already pinned in `.rubocop.yml`.

Formatting is not static analysis. RuboCop reformats with `-A` / `-a` and also
reasons about semantics, complexity, and bug patterns. Configuration depth —
plugin pins, department toggles, `# rubocop:disable` policy — is
[Chapter 37](37-rubocop-configuration.md). This chapter covers only the
formatter workflow and the Layout/Style surface every commit must already
satisfy.

**Tool alignment:** the rules below map to RuboCop departments driven from the
repo-root `.rubocop.yml` — notably `Layout/IndentationWidth`,
`Layout/LineLength`, `Layout/TrailingWhitespace`, `Style/StringLiterals`,
`Style/TrailingCommaIn*`, `Style/HashSyntax`, and `Style/Semicolon`. Rules a
named enabled cop actually enforces are marked **Violation**; the rest are
**Suggestion**.

## 1.1 Run `bundle exec rubocop -A` before every commit and `bundle exec rubocop` in CI.

> Why? `-A` (auto-correct all) is the write path and plain `rubocop` is the
> read-only gate. Running only the gate means every developer learns about
> formatting failures after pushing; running only the write path means an
> unformatted file can still reach `main` through a machine that skipped it.
> Both, in that order. A formatting failure is the cheapest possible build
> failure — one command fixes it, with zero judgement involved — so it belongs
> first in the pipeline, not last. Prefer `bundle exec` so the pinned RuboCop
> 1.88.2 (and plugins) from the Gemfile are what actually run.
> **Violation.**
>
> Enforced by: Layout/TrailingWhitespace.

```ruby
# bad — hand-laid-out; rubocop -A rewrites almost every line of this
class Rates
  def convert( amount,from,to )
      if amount<0
          raise ArgumentError,"negative"
      end
  amount*rate_for(from,to)
  end
end

# good — exactly what rubocop -A emits under the shipped config
class Rates
  def convert(amount, from, to)
    raise ArgumentError, 'negative' if amount.negative?

    amount * rate_for(from, to)
  end
end
```

```bash
# good — local write path
bundle exec rubocop -A

# good — CI read-only gate (no -A)
bundle exec rubocop
```

## 1.2 Indent with two spaces. Never tabs, never four.

> Why? The guide's
> [spaces indentation](https://rubystyle.guide/#spaces-indentation) rule and
> [tabs or spaces](https://rubystyle.guide/#tabs-or-spaces) both fix the block
> indent at two spaces and forbid tabs. A tab renders at a different width in
> every viewer, so a tab-indented file is unreadable in half the tools that
> open it. Four-space Ruby is a habit imported from Java or Kotlin and it
> produces a whole-file diff the first time anyone runs `rubocop -A`.
> **Violation.**
>
> Enforced by: Layout/IndentationWidth.

```ruby
# bad — four-space blocks, a tab on the return line
class OrderService
    def place(request)
	repository.save(Order.from(request))
    end
end

# good — two spaces, no tabs
class OrderService
  def place(request)
    repository.save(Order.from(request))
  end
end
```

Also enforced by: Layout/IndentationStyle.

## 1.3 Accept the 100-column soft limit; never hand-wrap to something narrower.

> Why? The guide's
> [max line length](https://rubystyle.guide/#max-line-length) sets the limit at
> 100 characters. RuboCop's `Layout/LineLength` Max is 100 in the shipped
> config, with comment lines exempted via `AllowedPatterns`. Hand-wrapping at
> 80 "for the side-by-side diff view" produces breaks the formatter immediately
> undoes, so the change never survives the next `rubocop -A`. When a line is
> genuinely too long, break on a natural seam (after a comma, before a `.`)
> and let Layout/MultilineMethodCallIndentation own the continuation indent.
> **Violation.**
>
> Enforced by: Layout/LineLength.

```ruby
# bad — hand-wrapped to ~50 columns; rubocop rejoins or rewraps these
result =
  repository
    .find_by(
      status: :active
    )

# good — fits inside 100 columns, so it stays on one line
result = repository.find_by(status: :active)

# good — genuinely too long; each argument on its own line
def join_labels(
  separator: ', ',
  prefix: '',
  postfix: ''
)
  # ...
end
```

## 1.4 Prefer single-quoted strings; use double quotes only when you interpolate or need an escape double quotes cannot avoid.

> Why? The guide's
> [consistent string literals](https://rubystyle.guide/#consistent-string-literals)
> and
> [single-quote preference](https://rubystyle.guide/#consistent-string-literals-single-quote)
> make single quotes the default. Double quotes imply interpolation or escape
> processing to a reader scanning the file; using them for a plain ASCII
> string is noise. The shipped config sets `Style/StringLiterals` to
> `single_quotes` and the same for interpolation fragments.
> **Violation.**
>
> Enforced by: Style/StringLiterals.

```ruby
# bad — double quotes with nothing to interpolate
name = "Ada"
path = "tmp/cache"

# good
name = 'Ada'
path = 'tmp/cache'

# good — double quotes earned by interpolation or embedded apostrophe
greeting = "Hello, #{name}"
possessive = "Ada's ledger"
```

Also enforced by: Style/StringLiteralsInInterpolation.

## 1.5 Put trailing commas on multiline arrays, hashes, and argument lists.

> Why? Without a trailing comma, adding an element to a multiline list touches
> two lines — the new one and the previous line that gains a comma — so every
> such diff implicates an author who did not change anything. The shipped
> config sets `EnforcedStyleForMultiline: consistent_comma` on
> `Style/TrailingCommaInArrayLiteral`, `Style/TrailingCommaInHashLiteral`, and
> `Style/TrailingCommaInArguments`. That is a deliberate house choice over the
> guide's older
> [no trailing array commas](https://rubystyle.guide/#no-trailing-array-commas)
> wording; RuboCop wins here because it is the tool that owns layout.
> **Violation.**
>
> Enforced by: Style/TrailingCommaInArrayLiteral.

```ruby
# bad — no trailing comma; adding :age also rewrites the :name line
person = {
  id: 1,
  name: 'Ada'
}

# good — adding a key touches exactly one line
person = {
  id: 1,
  name: 'Ada',
  age: 36,
}
```

Also enforced by: Style/TrailingCommaInHashLiteral and
Style/TrailingCommaInArguments.

## 1.6 Use the Ruby 1.9 hash syntax with symbol keys; never mix rocket and colon styles in one literal.

> Why? The guide's
> [symbols as keys](https://rubystyle.guide/#symbols-as-keys) and
> [no mixed hash syntaxes](https://rubystyle.guide/#no-mixed-hash-syntaxes)
> prefer `key:` over `:key =>` for symbol keys, and forbid mixing the two in
> one literal. Rockets remain correct for non-symbol keys (`'Content-Type' =>`
> or `1 =>`). The shipped config sets `Style/HashSyntax` to
> `ruby19_no_mixed_keys`.
> **Violation.**
>
> Enforced by: Style/HashSyntax.

```ruby
# bad — rockets for symbol keys, and mixed styles in one hash
headers = { :accept => 'application/json', content_type: 'text/plain' }

# good
headers = { accept: 'application/json', content_type: 'text/plain' }

# good — rocket required because the key is not a bare symbol
headers = { 'Content-Type' => 'application/json' }
```

## 1.7 Never write a semicolon to terminate or combine statements.

> Why? The guide's
> [no semicolon](https://rubystyle.guide/#no-semicolon) and
> [no semicolon ifs](https://rubystyle.guide/#no-semicolon-ifs) treat
> statement-ending semicolons as noise and forbids using them to jam two
> statements onto one line. Ruby is not C; a newline ends a statement. The
> rare legal use is inside a single-line `rescue`/`ensure` body that RuboCop's
> other cops have not yet rewritten into a multiline form — and even there,
> prefer multiline.
> **Violation.**
>
> Enforced by: Style/Semicolon.

```ruby
# bad — trailing semicolon, and two statements sharing one line
total = subtotal + tax;
log.info('charging'); charge(total)

# good
total = subtotal + tax
log.info('charging')
charge(total)
```

## 1.8 Align multiline arguments and parameters with fixed indentation, not under the open paren.

> Why? "Lined up under the opening delimiter" looks tidy until a rename moves
> the open paren and reflows every continuation line. Fixed indentation (+2
> from the start of the statement) survives renames and matches
> `Layout/ArgumentAlignment` and `Layout/ParameterAlignment` both set to
> `with_fixed_indentation` in the shipped config. Method-call continuations
> use `indented_relative_to_receiver` via
> `Layout/MultilineMethodCallIndentation`.
> **Violation.**
>
> Enforced by: Layout/ArgumentAlignment.

```ruby
# bad — hanging indent under the open paren; renaming `create` reflows all
order = factory.create(customer, items,
                       ship_to, payment)

# good — fixed +2 indent
order = factory.create(
  customer,
  items,
  ship_to,
  payment,
)
```

Also enforced by: Layout/ParameterAlignment.

## 1.9 Align hash rockets and colons by key, not by value.

> Why? Value-column alignment makes a one-character key rename reflow every
> neighbouring line. Key alignment (`EnforcedColonStyle: key` /
> `EnforcedHashRocketStyle: key` on `Layout/HashAlignment`) keeps each entry
> self-contained: one key, one value, one line when it wraps.
> **Violation.**
>
> Enforced by: Layout/HashAlignment.

```ruby
# bad — value-aligned; renaming `id` reflows the other lines
person = {
  id:           1,
  display_name: 'Ada',
  retry_count:  3
}

# good — key-aligned, single space after the colon
person = {
  id: 1,
  display_name: 'Ada',
  retry_count: 3,
}
```

## 1.10 Never spend a review comment on formatting.

> Why? Once `rubocop -A` has run there is no formatting decision left to have
> an opinion about. "Add a blank line here", "align these", and "wrap this at
> 80" are not actionable against a formatted file — the author cannot comply
> without disabling a Layout cop. Every such comment displaces a comment about
> correctness or design, which is the only thing a human reviewer is actually
> better at than a tool. If a formatted line is genuinely hard to read, the
> fix is almost always a named intermediate value, and *that* is a design
> comment worth making.
> **Suggestion.**

```ruby
# bad — reviewer asks for a hand-adjustment the next rubocop -A undoes
# > "can you line the arguments up under the open paren?"
order = order_factory.create(customer, items, ship_to, :card, promo_code)

# good — leave the formatting alone; name the thing that was hard to read
payment = PaymentDetails.new(method: :card, promo_code: promo_code)
order = order_factory.create(customer, items, ship_to, payment)
```

## 1.11 Introduce the formatter in one isolated commit and add that commit to `.git-blame-ignore-revs`.

> Why? Adopting RuboCop autocorrect on an existing codebase touches every file
> once. Doing it inside a feature branch buries the real change in thousands of
> whitespace lines and makes the review worthless. Doing it as its own commit
> and registering that commit's SHA in `.git-blame-ignore-revs` means
> `git blame` skips straight past it to the commit that actually wrote the
> line, so the reformat costs nothing in future archaeology.
> **Suggestion.**

```bash
# bad — reformat mixed into a behavioural change
git commit -am "add retry logic and format the repo"

# good
bundle exec rubocop -A
git commit -am "chore: apply rubocop -A across the repository"
git rev-parse HEAD >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

When a single reformat genuinely cannot be merged — a long-lived release
branch, hundreds of open pull requests — a RuboCop `--auto-gen-config`
baseline is the equivalent stopgap, and like every baseline it is temporary by
construction (see [Chapter 37](37-rubocop-configuration.md)).

## 1.12 Pin RuboCop and its plugins in the Gemfile; never rely on a globally installed binary.

> Why? RuboCop's autocorrect output changes between minor releases. An
> unpinned `gem install rubocop` on one machine and `1.88.2` on another means
> one developer's `-A` reflows files another developer's version had already
> formatted. Pin `rubocop`, `rubocop-rails`, `rubocop-performance`, and
> `rubocop-rspec` together (this skill verifies under 1.88.2 / 2.36.0 / 1.26.1 /
> 3.10.2) and run exclusively through `bundle exec`.
> **Suggestion.**

```ruby
# bad — Gemfile with floating cops
gem 'rubocop'
gem 'rubocop-rails'

# good — pinned set matching the skill floor
gem 'rubocop', '1.88.2'
gem 'rubocop-rails', '2.36.0'
gem 'rubocop-performance', '1.26.1'
gem 'rubocop-rspec', '3.10.2'
```

## 1.13 Keep the entire style configuration in the repo-root `.rubocop.yml`, not in IDE-only profiles.

> Why? `.rubocop.yml` is the only configuration surface both RuboCop *and*
> editor integrations should read. Splitting settings — indent in the IDE,
> line length in a personal `~/.rubocop.yml`, trailing commas in a third place —
> guarantees the editor reformats a file one way and CI rejects it the other
> way. Inherit or require the root file from engine/gem subprojects; do not
> fork a second opinionated config.
> **Suggestion.**

```yaml
# bad — per-developer ~/.rubocop.yml silently overrides CI
Layout/LineLength:
  Max: 80

# good — repo-root .rubocop.yml is the single source of truth
Layout/LineLength:
  Max: 100
```

## 1.14 Never disable a Layout or Style formatting cop inline to "win" an argument.

> Why? `# rubocop:disable Layout/LineLength` on a line you could rename or
> extract is how formatting debt becomes permanent. The shipped config enables
> `Style/DisableCopsWithinSourceCodeDirective`, which flags disable comments
> that omit a cop list — but even a scoped disable for a Layout cop should be
> rare and temporary. Prefer extracting a local variable, shortening a name, or
> breaking the expression. Policy for necessary disables is
> [Chapter 37](37-rubocop-configuration.md).
> **Violation.**
>
> Enforced by: Style/DisableCopsWithinSourceCodeDirective.

```ruby
# bad — blanket disable, and a Layout cop silenced for convenience
# rubocop:disable all
result = service.call(very_long_argument_one, very_long_argument_two, very_long_argument_three)

# good — no disable; name the intermediate values
args = [
  very_long_argument_one,
  very_long_argument_two,
  very_long_argument_three,
]
result = service.call(*args)
```

## 1.15 Prefer `%w` / `%i` for word and symbol arrays of two or more simple elements.

> Why? The guide's [`%w`](https://rubystyle.guide/#percent-w) and
> [`%i`](https://rubystyle.guide/#percent-i) forms remove quote and comma noise
> from homogeneous arrays. The shipped config sets `Style/WordArray` and
> `Style/SymbolArray` to `percent`. Do not use them for elements that need
> interpolation, spaces you care about preserving with quotes, or a single
> element where a normal literal is clearer.
> **Violation.**
>
> Enforced by: Style/WordArray.

```ruby
# bad
STATES = ['draft', 'paid', 'void']
ROLES = [:admin, :member, :guest]

# good
STATES = %w[draft paid void]
ROLES = %i[admin member guest]
```

Also enforced by: Style/SymbolArray.

## 1.16 End every file with a single newline; strip trailing whitespace on every line.

> Why? The guide's
> [newline eof](https://rubystyle.guide/#newline-eof) and
> [no trailing whitespace](https://rubystyle.guide/#no-trailing-whitespace)
> rules exist because POSIX text files end in a newline and trailing spaces
> create invisible diffs. Both are free under `rubocop -A`. Configure the IDE
> to trim on save so the hook is not the first time the author sees the churn.
> **Violation.**
>
> Enforced by: Layout/TrailingWhitespace.

```ruby
# bad — trailing spaces after `end`, and no final newline
class Order
  def total
    items.sum(&:price)
  end••
end
# (•• = spaces; EOF with no newline)

# good — clean lines, exactly one newline at EOF
class Order
  def total
    items.sum(&:price)
  end
end
```

Also enforced by: Layout/TrailingEmptyLines and Layout/EndOfLine.

## 1.17 Do not push semantic rules into ad-hoc scripts, or formatting rules into custom greps.

> Why? The property that makes a formatter safe to block a build on is that a
> failure is always fixable by running one command. A custom `grep`-based CI
> check for "line longer than 100" or "tab character" duplicates
> `Layout/LineLength` / `Layout/IndentationStyle`, will eventually disagree with
> RuboCop's exceptions (comment allowlists, heredocs), and trains the team to
> disable the wrong tool. Semantic rules (complexity, Rails footguns, security)
> stay in Lint / Metrics / Rails / Security cops; layout stays in Layout/Style.
> **Suggestion.**

```bash
# bad — CI script re-litigating what RuboCop already owns
git grep -n $'\t' -- '*.rb' && exit 1

# good — one tool, one config
bundle exec rubocop --format github
```

## 1.18 Wire the same RuboCop invocation in pre-commit and in CI; never format only on the server.

> Why? A workflow that depends on a human remembering a command fails under
> deadline pressure, and the failure costs a reviewer's time rather than the
> author's. A pre-commit hook (Overcommit, Lefthook, husky+bundler, or a plain
> `.git/hooks/pre-commit`) that runs `bundle exec rubocop -A --staged` or
> equivalent keeps the write path local. CI still runs read-only `rubocop` so a
> skipped hook cannot land. Editor format-on-save via the RuboCop LSP or
> Solargraph integration is encouraged but is not a substitute for the hook.
> **Suggestion.**

```bash
# bad — only CI formats; every PR starts with a "fix lint" commit
bundle exec rubocop  # in CI only

# good — local write + CI gate
bundle exec rubocop -A --force-exclusion
bundle exec rubocop
```
