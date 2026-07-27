<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 4. Comments & YARD

Comments are for intent, trade-offs, and contracts the code cannot state.
They are not for narrating the next line. This chapter covers when to write a
comment, how to keep it honest, annotation tags (`TODO`, `FIXME`), and YARD
for public APIs. Normative anchors live in the Ruby Style Guide's
[Comments](https://rubystyle.guide/#comments),
[no superfluous comments](https://rubystyle.guide/#no-superfluous-comments),
[comment annotations](https://rubystyle.guide/#comment-annotations),
[English comments](https://rubystyle.guide/#english-comments), and
[YARD](https://rubystyle.guide/#yard) / [API documentation](https://rubystyle.guide/#api-documentation)
sections.

`Style/Documentation` is **disabled** in the shipped `.rubocop.yml` — missing
class doc comments are not a CI failure. That does not mean public gems should
ship undocumented APIs; it means this skill treats class-level docs as
**Suggestion** judged by audience, not by a cop. Formatting of comment
spacing is still owned by Layout cops from [Chapter 1](01-formatting-and-tooling.md).

## 4.1 Do not write a comment that restates the next line of code.

> Why? The guide's
> [no superfluous comments](https://rubystyle.guide/#no-superfluous-comments)
> rule rejects narration (`# increment counter`) that a reader already gets
> from the identifier. Superfluous comments rot first: the code changes, the
> comment lies, and reviewers stop trusting every other comment. If the line
> needs a comment to be understood, the usual fix is a better name, not a
> caption.
> **Suggestion.**

```ruby
# bad
# Increment the retry counter
retry_count += 1

# Sum all line totals
total = lines.sum(&:amount)

# good — names carry the meaning; comment only the non-obvious
retry_count += 1
total = lines.sum(&:amount)

# good — explains a non-obvious constraint
# Payment gateway rejects retries older than 15 minutes; wall clock, not monotonic.
retry_count += 1 if Time.now - started_at < 15 * 60
```

## 4.2 Prefer refactoring unclear code over explaining it with a comment.

> Why? The guide's
> [refactor, don't comment](https://rubystyle.guide/#refactor-dont-comment)
> rule is the escalation of §4.1. A paragraph above a dense expression is a
> signal to extract a method or local variable. Comments that exist only to
> apologize for structure become the only documentation of a design that
> should be obvious from types and names.
> **Suggestion.**

```ruby
# bad
# Check whether the user is allowed to refund: must be admin, or the original
# purchaser within 30 days, and the payment must not be a gift card.
if user.admin? || (user == order.purchaser && order.created_at > 30.days.ago && !order.gift_card?)
  refund!(order)
end

# good — extract until the call site reads as the policy name
refund!(order) if RefundPolicy.allowed?(user: user, order: order)
```

## 4.3 Write comments in English, with complete sentences when they are more than a short phrase.

> Why? The guide's
> [English comments](https://rubystyle.guide/#english-comments) rule matches
> [English identifiers](https://rubystyle.guide/#english-identifiers). A mixed
> language codebase makes search and onboarding harder. Short end-of-line notes
> may be fragments; block comments that explain a trade-off should be proper
> sentences with a period.
> **Suggestion.**

```ruby
# bad
# cuidado: nao mudar a ordem

# good
# The gateway authenticates headers in this order; swapping breaks HMAC verification.
```

## 4.4 Use `TODO`, `FIXME`, `OPTIMIZE`, `HACK`, and `REVIEW` annotations sparingly, with enough context to act.

> Why? The guide's
> [comment annotations](https://rubystyle.guide/#comment-annotations) list is
> the conventional set. `Style/CommentAnnotation` enforces the keyword shape
> (colon or space per config). An annotation without an owner, ticket, or
> removal condition is a permanent apology. Prefer linking an issue id and a
> what-done-looks-like clause.
> **Violation.**
>
> Enforced by: Style/CommentAnnotation.

```ruby
# bad — vague, undated
# TODO: fix this
# HACK: weird stuff

# good
# TODO: Remove once Payments API v1 is retired (BILL-1421).
# FIXME: Off-by-one when period spans DST; add tz regression in next sprint.
```

## 4.5 Never use block comments (`=begin` / `=end`) for ordinary commentary.

> Why? The guide's
> [no block comments](https://rubystyle.guide/#no-block-comments) rule and
> `Style/BlockComments` reject `=begin` bodies. They do not nest, they are easy
> to leave half-removed, and they hide large dead regions from reviewers who
> skim `#` lines. Use `#` per line, or delete the code and rely on git.
> **Violation.**
>
> Enforced by: Style/BlockComments.

```ruby
# bad
=begin
def legacy_charge
  ...
end
=end

# good — delete it, or keep a short rationale if historically important
# Removed legacy_charge in 2026-03; see git history for the PayPal path.
```

## 4.6 Keep a blank space after `#` on ordinary comments.

> Why? `Layout/LeadingCommentSpace` requires `# comment` not `#comment` for
> normal commentary, which matches the guide's layout expectations and keeps
> annotations visually consistent. RDoc/YARD tags still use `# @param` with a
> space after `#`.
> **Violation.**
>
> Enforced by: Layout/LeadingCommentSpace.

```ruby
# bad
#TODO: retire
#This charges the card.

# good
# TODO: retire
# This charges the card.
```

## 4.7 Document the why of a non-obvious algorithm, edge case, or invariant — not the how.

> Why? The guide's
> [rationale comments](https://rubystyle.guide/#rationale-comments) framing is
> that the code already shows *how*. Useful comments state the invariant a
> maintainer would otherwise break ("headers must be sorted before signing"),
> the bug that forced a branch, or the link to an external spec. Restating
> control flow fails §4.1.
> **Suggestion.**

```ruby
# bad
# Loop through items and add tax
items.each do |item|
  item.total = item.price * tax_rate
end

# good
# Tax rate is inclusive for EU invoices; do not also add VAT at the gateway.
items.each do |item|
  item.total = item.price * tax_rate
end
```

## 4.8 Use YARD tags on public gem APIs; do not YARD every private Rails model method.

> Why? The guide's [YARD](https://rubystyle.guide/#yard) and
> [API documentation](https://rubystyle.guide/#api-documentation) sections
> target *library* surfaces. A public gem method without `@param` / `@return`
> forces readers into the implementation. Inside a Rails app, a one-off private
> model method with an obvious signature gains little from a full YARD block —
> and `Style/Documentation` is off precisely so CI does not demand class
> comments on every ActiveRecord model. Match documentation density to the
> audience that cannot read your private source.
> **Suggestion.**

```ruby
# bad — YARD noise on an obvious private helper
class Order < ApplicationRecord
  # @param user [User] the user
  # @return [Boolean] whether ok
  private

  def owned_by?(user)
    self.user_id == user.id
  end
end

# good — YARD on a gem's public API
# Charges the given order idempotently.
#
# @param order [Order]
# @param idempotency_key [String]
# @return [Receipt]
# @raise [PaymentError] when the gateway declines
def charge(order, idempotency_key:)
  # ...
end
```

## 4.9 Keep YARD types and signatures truthful; update them in the same commit as the code.

> Why? A wrong `@return [String]` when the method returns `nil` or a
> `Receipt` is worse than no comment — callers trust it. Treat YARD as part of
> the public contract: the same PR that changes the return value changes the
> tag. Prefer specific types over `Object` / `Hash`.
> **Suggestion.**

```ruby
# bad — lies after a refactor to a Receipt object
# @return [Hash] raw gateway payload
def charge(order)
  Receipt.new(...)
end

# good
# @return [Receipt]
def charge(order)
  Receipt.new(...)
end
```

## 4.10 Prefer a single space before an end-of-line comment; keep EOL comments rare.

> Why? The guide's
> [rare EOL annotations](https://rubystyle.guide/#rare-eol-annotations)
> advice exists because trailing comments fight line length and wrap badly.
> When used, `Layout/SpaceBeforeComment` wants space before `#`. Prefer a
> preceding full-line comment for anything longer than a few words.
> **Violation.**
>
> Enforced by: Layout/SpaceBeforeComment.

```ruby
# bad
total = net*rate# include tax

# good — rare, short
total = net * rate # inclusive VAT

# good — preferred for real explanations
# Inclusive VAT for EU invoices.
total = net * rate
```

## 4.11 Do not comment out dead code; delete it.

> Why? Commented-out methods are untested, drift from APIs they call, and
> create review noise. Git already stores history. A short comment pointing at
> a commit or ticket is enough when the removal needs rationale
> ([comment upkeep](https://rubystyle.guide/#comment-upkeep)).
> **Suggestion.**

```ruby
# bad
# def old_charge(order)
#   Gateway.charge(order.total)
# end

# good
# Old charge path removed in favour of IdempotentCharge (BILL-99).
```

## 4.12 Annotate a non-obvious `# rubocop:disable` with the reason on the same or next line.

> Why? A bare disable is indistinguishable from drive-by silencing. Chapter 37
> owns the full policy; here the comment rule is: state *why* the cop is wrong
> for this spot, and prefer the tightest scope (`Disable`/`Enable` around one
> method, or end-of-line disable). `Style/DisableCopsWithinSourceCodeDirective`
> already rejects disables that omit cop names.
> **Violation.**
>
> Enforced by: Style/DisableCopsWithinSourceCodeDirective.

```ruby
# bad
# rubocop:disable Metrics/AbcSize
def compute
  # 200 lines
end

# good
# rubocop:disable Metrics/AbcSize -- mirrors audited tax worksheet steps 1-12
def compute
  # ...
end
# rubocop:enable Metrics/AbcSize
```

## 4.13 Do not use comments as a substitute for tests or types.

> Why? "Must never be called with nil" in a comment will be violated; a
> precondition (`raise ArgumentError if user.nil?`), a typed YARD contract in a
> gem, or an RSpec example will not. Comments that restate testable behaviour
> become stale the first time someone "fixes" the edge case without reading
> them.
> **Suggestion.**

```ruby
# bad
# user must not be nil
def greet(user)
  "hi #{user.name}"
end

# good
def greet(user)
  raise ArgumentError, 'user is required' if user.nil?

  "hi #{user.name}"
end
```

## 4.14 Keep copyright / license headers short and out of the way of magic comments.

> Why? Magic comments must come first ([§2.2](02-source-files-and-structure.md)).
> A twenty-line license banner between the shebang and `frozen_string_literal`
> breaks tooling. Prefer a single SPDX line after the frozen pragma, or a
> repo-level LICENSE file with no per-file banner.
> **Suggestion.**

```ruby
# bad — banner before frozen_string_literal
# Copyright 2026 Example Inc.
# All rights reserved.
# ...
# frozen_string_literal: true

# good
# frozen_string_literal: true

# SPDX-License-Identifier: MIT

class Order
end
```
