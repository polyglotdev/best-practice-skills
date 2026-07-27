<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 12. Strings & Symbols

Strings are the default textual type; symbols are interned names for
identifiers, hash keys, and enum-like tokens. This chapter covers the
frozen-string-literal pragma (still required on Ruby 4.0.5 — literals are
**not** frozen by language default), quote style, interpolation, percent
literals, heredocs, and when to prefer a symbol over a string. **Prefer
single quotes** wherever
[rubystyle.guide](https://rubystyle.guide/#consistent-string-literals-single-quote)
allows; use double quotes only for interpolation or embedded apostrophes.
Formatting details RuboCop already owns (line length, encoding comments)
stay out of scope.

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[strings](https://rubystyle.guide/#strings),
[consistent string literals](https://rubystyle.guide/#consistent-string-literals),
[consistent string literals single quote](https://rubystyle.guide/#consistent-string-literals-single-quote),
[percent q](https://rubystyle.guide/#percent-q),
[percent q shorthand](https://rubystyle.guide/#percent-q-shorthand),
[percent literals](https://rubystyle.guide/#percent-literals),
[percent s](https://rubystyle.guide/#percent-s),
[heredocs](https://rubystyle.guide/#heredocs),
[heredoc delimiters](https://rubystyle.guide/#heredoc-delimiters),
[heredoc long strings](https://rubystyle.guide/#heredoc-long-strings),
[squiggly heredocs](https://rubystyle.guide/#squiggly-heredocs),
[string interpolation](https://rubystyle.guide/#string-interpolation),
[curlies interpolate](https://rubystyle.guide/#curlies-interpolate),
[concat strings](https://rubystyle.guide/#concat-strings),
[no to_s](https://rubystyle.guide/#no-to-s),
[symbols as keys](https://rubystyle.guide/#symbols-as-keys),
[snake case symbols](https://rubystyle.guide/#snake-case-symbols-methods-vars),
[magic comments](https://rubystyle.guide/#magic-comments), and
[separate magic comments from code](https://rubystyle.guide/#separate-magic-comments-from-code),
together with the [Ruby 4.0 string docs](https://docs.ruby-lang.org/en/4.0/String.html)
for chilled/frozen literal behaviour.

**Ruby 4.0.5 fact:** string literals are **not** frozen by default. Mutating
a literal without `# frozen_string_literal: true` emits a deprecation
warning under `-W:deprecated` (`literal string will be frozen in the
future`). Require the pragma on every file.

**Tool alignment:** `Style/FrozenStringLiteralComment`,
`Style/StringLiterals`, `Style/PercentQLiterals`,
`Style/RedundantPercentQ`, `Style/BarePercentLiterals`,
`Naming/HeredocDelimiterNaming`, `Naming/HeredocDelimiterCase`,
`Layout/HeredocIndentation`, `Style/MutableConstant`, and related cops are
effectively enabled. Rules those cops catch are **Violation**; the rest
are **Suggestion**.

## 12.1 Put `# frozen_string_literal: true` at the top of every Ruby file.

> Why? On Ruby **4.0.5**, frozen string literals are still pragma-driven —
> they are **not** the language default. The pragma freezes string
> literals in that file, matching the direction of the language and
> eliminating accidental mutation. Without it, mutating a literal warns
> under `-W:deprecated`. The guide's
> [magic comments](https://rubystyle.guide/#magic-comments)
> section and `Style/FrozenStringLiteralComment` require the comment.
> **Violation.**
>
> Enforced by: Style/FrozenStringLiteralComment.

```ruby
# bad — no pragma; literal mutation is deprecated behaviour
name = 'Ada'
name << ' Lovelace'

# good
# frozen_string_literal: true

name = 'Ada'
full = +"#{name} Lovelace" # explicit mutable string when mutation is required
```

## 12.2 Leave a blank line after magic comments before the first code or ordinary comment block.

> Why? The guide's
> [separate magic comments from code](https://rubystyle.guide/#separate-magic-comments-from-code)
> rule and `Layout/EmptyLineAfterMagicComment` keep the pragma visually
> distinct from `require` and the file body. **Violation.**
>
> Enforced by: Layout/EmptyLineAfterMagicComment.

```ruby
# bad
# frozen_string_literal: true
require 'json'

# good
# frozen_string_literal: true

require 'json'
```

## 12.3 Prefer single-quoted strings unless you need interpolation or embedded apostrophe-heavy text that double quotes express more clearly.

> Why? The guide's
> [consistent string literals single quote](https://rubystyle.guide/#consistent-string-literals-single-quote)
> preference and `Style/StringLiterals` (single quotes enforced in this
> repo) make quote style mechanical. Double quotes are for
> `"#{value}"`, escape sequences you actually need, or strings that
> contain many single quotes. **Violation.**
>
> Enforced by: Style/StringLiterals.

```ruby
# bad
greeting = "hello"
path = "tmp/cache"

# good
greeting = 'hello'
path = 'tmp/cache'
interpolated = "hello #{name}"
```

## 12.4 Prefer string interpolation over `String#+` concatenation for building messages from parts.

> Why? The guide's
> [string interpolation](https://rubystyle.guide/#string-interpolation)
> and
> [concat strings](https://rubystyle.guide/#concat-strings)
> rules, plus `Style/StringConcatenation`, prefer `"#{a} #{b}"` over
> `a + ' ' + b` for readability and fewer intermediate strings.
> **Violation.**
>
> Enforced by: Style/StringConcatenation.

```ruby
# bad
message = 'Hello, ' + name + '!'

# good
message = "Hello, #{name}!"
```

## 12.5 Prefer `#{}` interpolation over `Kernel#sprintf` / `%` formatting for simple substitutions; use format templates when the template is reused or localized.

> Why? The guide's
> [curlies interpolate](https://rubystyle.guide/#curlies-interpolate)
> guidance keeps ordinary messages in interpolation. Reach for
> `format` / `sprintf` when you need width, padding, or named tokens
> (`%<name>s`) for i18n. Prefer named tokens over positional `%s` when
> using format strings. **Suggestion** for the choice;
> `Style/FormatStringToken` applies when format strings are used.

```ruby
# bad — sprintf for a trivial join
message = sprintf('Hello, %s!', name)

# good — interpolation for simple cases
message = "Hello, #{name}!"

# good — format when the template is data
template = 'Hello, %<name>s!'
message = format(template, name: name)
```

## 12.6 Do not call `to_s` on values already interpolated into a string.

> Why? The guide's
> [no to_s](https://rubystyle.guide/#no-to-s)
> rule notes that interpolation calls `to_s` for you.
> `Lint/RedundantStringCoercion` flags the noise. **Violation.**
>
> Enforced by: Lint/RedundantStringCoercion.

```ruby
# bad
label = "id=#{id.to_s}"

# good
label = "id=#{id}"
```

## 12.7 Prefer `%q(...)` / `%Q(...)` only when the delimiter choice avoids a thicket of escapes; otherwise use ordinary quotes.

> Why? The guide's
> [percent q](https://rubystyle.guide/#percent-q)
> and
> [percent q shorthand](https://rubystyle.guide/#percent-q-shorthand)
> rules, with `Style/PercentQLiterals` / `Style/RedundantPercentQ`, keep
> percent-q for strings that contain both quote styles. `%q` is
> single-quote semantics (no interpolation); `%Q` is double-quote
> semantics. Prefer `%q{}` / `%Q{}` brace delimiters consistently when
> you do use them. **Violation** when RuboCop's percent-q cops apply.
>
> Enforced by: Style/RedundantPercentQ.

```ruby
# bad — percent-q with nothing to escape
title = %q(Reports)

# good — ordinary quotes
title = 'Reports'

# good — percent-q earns its keep
sql = %q(SELECT * FROM "users" WHERE name = 'Ada')
```

## 12.8 Prefer symbols for controlled identifiers and hash keys; prefer strings for free-form, user-facing, or externally supplied text.

> Why? Symbols are interned and compared by identity; they are ideal for
> fixed vocabularies (`:admin`, `:json`). They are a poor fit for
> unbounded input (params, file contents, CSV cells) because symbols are
> not garbage-collected in older mental models and still signal "this is
> program structure" to readers. Convert at the boundary with
> `to_sym` only for allow-listed values. See also
> [symbols as keys](https://rubystyle.guide/#symbols-as-keys).
> **Suggestion.**

```ruby
# bad — symbol from unbounded input
status = params[:status].to_sym
cache[raw_header.to_sym] = value

# good — string for external text; symbol for fixed vocabulary
status = params[:status] # string
MODE_READ = :read
MODE_WRITE = :write
```

## 12.9 Prefer bareword or quoted symbol literals that match `Naming` cops; avoid spaces and operators in symbol names.

> Why? `Style/SymbolLiteral` and
> [snake case symbols](https://rubystyle.guide/#snake-case-symbols-methods-vars)
> keep symbols looking like method names: `:created_at`, not
> `:"Created At"`, unless the key must match an external protocol.
> **Violation.**
>
> Enforced by: Style/SymbolLiteral.

```ruby
# bad
state = :"in progress"

# good
state = :in_progress

# good — external protocol demands the stringly key
headers['Content-Type'] = 'application/json'
```

## 12.10 Prefer `%s` only for symbols that would otherwise need awkward quoting; otherwise use ordinary `:symbol` literals.

> Why? The guide's
> [percent s](https://rubystyle.guide/#percent-s)
> rule keeps `%s|awkward-name|` rare. Ordinary `:name` is clearer for
> identifiers. **Suggestion.**

```ruby
# bad
kind = %s(order)

# good
kind = :order
```

## 12.11 Prefer squiggly heredocs (`<<~`) for indented multiline strings, and choose descriptive uppercase delimiters.

> Why? The guide's
> [squiggly heredocs](https://rubystyle.guide/#squiggly-heredocs),
> [heredoc delimiters](https://rubystyle.guide/#heredoc-delimiters), and
> [heredoc long strings](https://rubystyle.guide/#heredoc-long-strings)
> rules, plus `Naming/HeredocDelimiterNaming`,
> `Naming/HeredocDelimiterCase`, and `Layout/HeredocIndentation`, keep
> multiline SQL/HTML/messages readable inside indented methods. Avoid
> `EOF` / `END` as delimiters when a domain word (`SQL`, `MESSAGE`) is
> clearer. **Violation.**
>
> Enforced by: Naming/HeredocDelimiterNaming.

```ruby
# bad
query = <<-EOF
SELECT *
FROM users
EOF

# good
def inactive_users_sql
  <<~SQL
    SELECT *
    FROM users
    WHERE active = FALSE
  SQL
end
```

## 12.12 Prefer heredocs for long multiline text; prefer ordinary quoted strings (or `%q`) for short one-liners.

> Why? The guide's
> [heredoc long strings](https://rubystyle.guide/#heredoc-long-strings)
> and
> [heredocs](https://rubystyle.guide/#heredocs)
> sections reserve heredocs for content that is genuinely multiline.
> A two-word heredoc is ceremony. **Suggestion.**

```ruby
# bad
label = <<~TEXT
  OK
TEXT

# good
label = 'OK'

# good — heredoc for real multiline content
mail_body = <<~BODY
  Hello #{name},

  Your report is ready.
BODY
```

## 12.13 Prefer freezing constants that hold string or mutable collection values when the file does not use frozen-string-literal, and avoid mutable string constants generally.

> Why? `Style/MutableConstant` requires `.freeze` on constants assigned
> mutable objects. With `# frozen_string_literal: true`, string literals
> are already frozen, but arrays/hashes of strings still need
> `.freeze` (or nested freezes) when treated as immutable constants.
> **Violation.**
>
> Enforced by: Style/MutableConstant.

```ruby
# bad
STATES = ['open', 'closed']

# good
# frozen_string_literal: true

STATES = %w[open closed].freeze
```

## 12.14 Prefer an explicitly mutable string (`String.new`, `+''`, or `dup`) when you must mutate; do not mutate a literal under the frozen pragma.

> Why? With `# frozen_string_literal: true`, `<<` and `concat!` on a
> literal raise `FrozenError`. Build with interpolation or join, or
> allocate a mutable buffer intentionally. Under Ruby 4.0.5 without the
> pragma, literal mutation still warns as deprecated — do not rely on
> that transitional behaviour. **Suggestion.**

```ruby
# bad under frozen_string_literal
buffer = ''
buffer << 'a'
buffer << 'b'

# good — build immutably
buffer = "#{'a'}#{'b'}"
buffer = %w[a b].join

# good — explicit mutable buffer when appending in a loop
buffer = +''
items.each { |item| buffer << item }
```

## 12.15 Prefer symbols as hash keys for internal Ruby hashes; prefer string keys for protocol payloads that are strings end-to-end.

> Why? The guide's
> [symbols as keys](https://rubystyle.guide/#symbols-as-keys)
> rule matches idiomatic Ruby hashes (`status: :ok`). JSON and HTTP
> headers are stringly; converting every key to a symbol with
> `deep_symbolize_keys` on untrusted input is unnecessary work and a
> footgun. Pick one key type per hash and document boundary conversions.
> **Suggestion.**

```ruby
# bad — mixed key types without reason
config = { 'host' => 'localhost', port: 443 }

# good — symbol keys for internal config
config = { host: 'localhost', port: 443 }

# good — string keys for JSON-shaped data
payload = { 'user_id' => 1, 'name' => 'Ada' }
```

## 12.16 Prefer `%()` / `%Q()` brace style consistently when a percent literal is justified; do not nest percent literals.

> Why? The guide's
> [percent literals](https://rubystyle.guide/#percent-literals)
> section, `Style/BarePercentLiterals`, `Style/PercentLiteralDelimiters`,
> and `Lint/NestedPercentLiteral` keep delimiters predictable and forbid
> nested percent forms that confuse parsers and readers. **Violation.**
>
> Enforced by: Lint/NestedPercentLiteral.

```ruby
# bad
nested = %W[#{%w[a b]} c]

# good
inner = %w[a b]
nested = %W[#{inner.join} c]
```
