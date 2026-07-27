<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 2. Source Files & Structure

A Ruby source file is a unit of load order, naming, and frozen-string policy
before it is a unit of design. This chapter covers magic comments, encoding,
file and directory names, `require` / `require_relative`, and how many
concepts belong in one file. Normative anchors live in the Ruby Style Guide's
[Source Files](https://rubystyle.guide/#files),
[magic comments](https://rubystyle.guide/#magic-comments),
[snake_case files](https://rubystyle.guide/#snake-case-files), and
[one class per file](https://rubystyle.guide/#one-class-per-file) sections.

Formatting inside the file is owned by [Chapter 1](01-formatting-and-tooling.md).
What to *name* the classes and methods those files contain is
[Chapter 3](03-naming.md). Rails-specific load paths (`app/`, `config/`,
Zeitwerk) are [Chapter 25](25-rails-application-structure.md).

**Frozen string literals are not the language default on Ruby 4.0.5.** Mutating
a literal still emits a deprecation warning under `-W:deprecated` (`literal
string will be frozen in the future`). This skill therefore requires
`# frozen_string_literal: true` on every file. Do not claim that Ruby 4.0
freezes every literal by default — that is false on 4.0.5.

**Tool alignment:** `Style/FrozenStringLiteralComment`,
`Layout/EmptyLineAfterMagicComment`, `Naming/FileName`, `Style/Encoding`, and
`Lint/OrderedMagicComments` cover the mechanical half. Judgement about one
class per file and require graphs is **Suggestion** unless a named cop catches
it.

## 2.1 Put `# frozen_string_literal: true` at the top of every Ruby file.

> Why? On Ruby 4.0.5, string literals are still mutable by default. The magic
> comment freezes every literal in the file, catches accidental mutation at
> runtime, and prepares the codebase for the eventual language default. The
> guide's [magic comments](https://rubystyle.guide/#magic-comments) section is
> the style home; the language fact is Ruby 4.0's continued pragma-driven
> behaviour. Omitting the comment is a finding even when the file currently
> mutates nothing — the next edit will.
> **Violation.**
>
> Enforced by: Style/FrozenStringLiteralComment.

```ruby
# bad — no frozen_string_literal; literals remain mutable on 4.0.5
class Greeter
  def hello
    'hi'
  end
end

# good
# frozen_string_literal: true

class Greeter
  def hello
    'hi'
  end
end
```

## 2.2 Place magic comments first (after an optional shebang), one per line, then a blank line before code.

> Why? The guide requires magic comments
> [first](https://rubystyle.guide/#magic-comments-first),
> [one per line](https://rubystyle.guide/#one-magic-comment-per-line),
> [below the shebang](https://rubystyle.guide/#below-shebang) when present, and
> [separated from code](https://rubystyle.guide/#separate-magic-comments-from-code)
> by a blank line. RuboCop's `Layout/EmptyLineAfterMagicComment` and
> `Lint/OrderedMagicComments` encode the blank line and ordering. Crowding the
> pragma against `class` makes it easy to miss in review.
> **Violation.**
>
> Enforced by: Layout/EmptyLineAfterMagicComment.

```ruby
# bad — pragma jammed against the class, two pragmas on one line
# frozen_string_literal: true encoding: utf-8
class Order
end

# good
#!/usr/bin/env ruby
# frozen_string_literal: true

class Order
end
```

Also enforced by: Lint/OrderedMagicComments.

## 2.3 Do not add a `# encoding: utf-8` comment; UTF-8 is the default.

> Why? The guide's [UTF-8](https://rubystyle.guide/#utf-8) rule states that
> UTF-8 is the default source encoding and an explicit encoding comment is
> redundant for UTF-8. `Style/Encoding` flags the unnecessary comment. Keep an
> encoding magic comment only when the file is genuinely not UTF-8 — which
> should be almost never in a modern codebase.
> **Violation.**
>
> Enforced by: Style/Encoding.

```ruby
# bad — redundant encoding comment
# frozen_string_literal: true
# encoding: utf-8

class Order
end

# good
# frozen_string_literal: true

class Order
end
```

## 2.4 Name ordinary source files in snake_case that mirrors the primary constant.

> Why? The guide's
> [snake_case files](https://rubystyle.guide/#snake-case-files) rule maps
> `SomethingReallyCool` to `something_really_cool.rb`. Zeitwerk and classic
> Rails autoloading both depend on that mapping; a mismatched path means the
> constant is not found until something eagerly `require`s it, which fails in
> production under lazy load. Acronyms follow the same compression as the
> constant: `HTTPClient` → `http_client.rb`, not `h_t_t_p_client.rb`.
> **Violation.**
>
> Enforced by: Naming/FileName.

```ruby
# bad — file name does not map to the constant
# file: HTTPClient.rb or http-client.rb
class HTTPClient
end

# good — file: http_client.rb
class HTTPClient
end

# good — file: order_service.rb
class OrderService
end
```

## 2.5 Name directories in snake_case; keep path segments lowercase.

> Why? The guide's
> [snake_case dirs](https://rubystyle.guide/#snake-case-dirs) rule matches
> file naming. Mixed-case directory segments break on case-insensitive
> filesystems when two casings collide, and they break Zeitwerk expectations
> for nested namespaces (`Admin::Reports` → `admin/reports.rb` under
> `app/models` or `lib/`).
> **Suggestion.**

```text
# bad
lib/PaymentGateway/
app/models/AdminUsers/

# good
lib/payment_gateway/
app/models/admin_users/
```

## 2.6 Prefer one well-named class or module per file; nest tiny collocations only when they are private implementation details.

> Why? The guide's
> [one class per file](https://rubystyle.guide/#one-class-per-file) rule keeps
> autoload maps obvious and diffs reviewable. A file that defines five
> public classes forces every change to one of them to present as a change to
> the whole grab-bag. Exceptions: a small private `Error` hierarchy living next
> to the only type that raises it, or a `Data.define` value used only inside
> that file. The moment a nested type is referenced from elsewhere, give it its
> own file.
> **Suggestion.**

```ruby
# bad — payment_stuff.rb defines unrelated public types
class PaymentGateway
end

class RefundPolicy
end

class LedgerEntry
end

# good — payment_gateway.rb
class PaymentGateway
  Error = Class.new(StandardError)
  Timeout = Class.new(Error)
end

# good — refund_policy.rb and ledger_entry.rb are separate files
```

## 2.7 Prefer `require_relative` for files inside the same project tree.

> Why? The guide's
> [use require_relative whenever possible](https://rubystyle.guide/#use-require_relative-whenever-possible)
> rule avoids `$LOAD_PATH` searches for code you own. `require_relative`
> resolves from the current file's directory, which is stable under chdir and
> clearer in gems that have not yet been activated. Use bare `require` for
> gems and stdlib (`require 'json'`, `require 'some_gem'`).
> **Suggestion.**

```ruby
# bad — hopes lib/ is on the load path
require 'payment/gateway'
require 'payment/refund_policy'

# good — explicit relative load for project files
require_relative 'payment/gateway'
require_relative 'payment/refund_policy'

# good — bare require for gems and stdlib
require 'json'
require 'faraday'
```

## 2.8 Do not write `require 'foo.rb'` with an explicit `.rb` suffix.

> Why? `Style/RedundantFileExtensionInRequire` (enabled by default) and the
> guide's load-path conventions treat the extension as redundant. Adding `.rb`
> also blocks Ruby from selecting a native extension of the same basename when
> one exists. Omit the suffix for both `require` and `require_relative`.
> **Violation.**
>
> Enforced by: Style/RedundantFileExtensionInRequire.

```ruby
# bad
require 'json.rb'
require_relative 'order_service.rb'

# good
require 'json'
require_relative 'order_service'
```

## 2.9 Keep the Gemfile and gemspec declarative; do not put Ruby version constraints only in one of them.

> Why? The guide's
> [Gemfile and gemspec](https://rubystyle.guide/#gemfile-and-gemspec) section
> and RuboCop's Gemspec cops expect a single story about dependencies. For a
> gem, runtime deps belong in the gemspec; the Gemfile should `gemspec` and add
> only development tools. Declare the required Ruby version in the gemspec
> (`spec.required_ruby_version`) and keep `.rubocop.yml`'s
> `TargetRubyVersion: 4.0` aligned with it.
> **Suggestion.**

```ruby
# bad — version floor only in Gemfile, invisible to gem consumers
# Gemfile
ruby '4.0.5'
gem 'my_gem'

# good — gemspec carries the floor; Gemfile uses it
# my_gem.gemspec
spec.required_ruby_version = '>= 4.0'

# Gemfile
gemspec
gem 'rubocop', '1.88.2'
```

Also related: Gemspec/RequiredRubyVersion.

## 2.10 Use LF line endings; never commit CRLF in `.rb` files.

> Why? The guide's [CRLF](https://rubystyle.guide/#crlf) rule forbids Windows
> line endings in Ruby source. Mixed endings produce noisy diffs and fail
> `Layout/EndOfLine` under the default `lf` style. Set `core.autocrlf` /
> `.gitattributes` so contributors on Windows do not reintroduce CRLF.
> **Violation.**
>
> Enforced by: Layout/EndOfLine.

```text
# bad — CRLF endings in app/models/order.rb

# good — LF only; .gitattributes contains:
*.rb text eol=lf
```

## 2.11 Do not leave a file empty, and do not leave leading blank lines above the magic comment.

> Why? An empty file is almost always a mistaken path or a deleted type that
> left its shell behind — `Lint/EmptyFile` catches it. Leading blank lines
> before the magic comment break the
> [magic comments first](https://rubystyle.guide/#magic-comments-first)
> placement rule and are cleaned by `Layout/LeadingEmptyLines`.
> **Violation.**
>
> Enforced by: Lint/EmptyFile.

```ruby
# bad — entire file is whitespace / empty

# bad — blank lines above the pragma
# frozen_string_literal: true

class Order
end

# good
# frozen_string_literal: true

class Order
end
```

Also enforced by: Layout/LeadingEmptyLines.

## 2.12 Order requires consistently: stdlib, then gems, then `require_relative` project files, with a blank line between groups.

> Why? A stable require order makes missing or duplicate requires obvious in
> review and reduces merge conflicts. RuboCop does not mandate the grouping by
> default the way `goimports` does, so this is a team convention — but
> `Lint/DuplicateRequire` still catches duplicates inside the list. Prefer
> alphabetical order within each group.
> **Suggestion.**

```ruby
# bad — interleaved, with a duplicate
require_relative 'order'
require 'json'
require 'faraday'
require 'json'
require_relative 'customer'

# good
require 'json'

require 'faraday'

require_relative 'customer'
require_relative 'order'
```

Duplicates are enforced by: Lint/DuplicateRequire.

## 2.13 Prefer Zeitwerk-friendly constant paths in Rails; avoid manual `require` of `app/` code.

> Why? Rails 8 autoloads `app/**` from file paths. An explicit
> `require './app/models/order'` (or `require_dependency`) fights reloading and
> duplicates the autoloader's job. Point constants at the right path, name the
> file correctly (§2.4), and let Zeitwerk load. Non-Rails libraries still use
> §2.7. Full Rails structure is
> [Chapter 25](25-rails-application-structure.md).
> **Suggestion.**

```ruby
# bad — manual require of autoloaded app code
require Rails.root.join('app/models/order')

# good — reference the constant; Zeitwerk loads app/models/order.rb
order = Order.find(id)
```

## 2.14 Keep executable scripts' shebang on line one, then magic comments, then a `require`/`require_relative` boot, then code.

> Why? The guide's [below shebang](https://rubystyle.guide/#below-shebang)
> placement only works if the shebang is literally line one — no BOM, no blank
> line above it. After the frozen-string pragma and the blank line, boot the
> bundler environment (`require 'bundler/setup'` or `require_relative
> '../config/environment'` for Rails runners) before referencing application
> constants.
> **Suggestion.**

```ruby
# bad — shebang not first; application code before boot
# frozen_string_literal: true
#!/usr/bin/env ruby
Order.delete_all

# good
#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative '../config/environment'

Order.delete_all
```

## 2.15 Do not commit generated noise next to source — `tmp/`, `log/`, `coverage/`, and `vendor/bundle/` stay ignored.

> Why? The shipped `.rubocop.yml` already excludes `tmp/**/*`, `log/**/*`,
> `coverage/**/*`, and `vendor/**/*` so RuboCop does not waste time on them.
> They still must not enter git: generated files create meaningless diffs and
> can leak credentials from logs. Mirror those excludes in `.gitignore`.
> **Suggestion.**

```text
# good — .gitignore fragments aligned with RuboCop Exclude
/tmp/
/log/
/coverage/
/vendor/bundle/
```
