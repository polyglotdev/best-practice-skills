<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 27. ActiveRecord Queries

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

Queries are part of the public API of your domain. A scope name is a
promise about SQL shape; a stringy `where` is a promise you will rewrite
it under injection review. Prefer the query interface, name reusable
fragments as scopes, and choose APIs that stream, project, and fail the
way the caller needs.

Sources:
[activerecord-queries](https://rails.rubystyle.guide/#activerecord-queries),
[find_by](https://rails.rubystyle.guide/#find_by),
[find-each](https://rails.rubystyle.guide/#find-each),
[hash-conditions](https://rails.rubystyle.guide/#hash-conditions),
[named-scopes](https://rails.rubystyle.guide/#named-scopes),
[pluck](https://rails.rubystyle.guide/#pluck),
[pick](https://rails.rubystyle.guide/#pick),
[where-not](https://rails.rubystyle.guide/#where-not),
[where-ranges](https://rails.rubystyle.guide/#where-ranges),
[order-arguments](https://rails.rubystyle.guide/#order-arguments),
[save-bang](https://rails.rubystyle.guide/#save-bang),
[redundant-all](https://rails.rubystyle.guide/#redundant-all),
and
[squished-heredocs](https://rails.rubystyle.guide/#squished-heredocs).

**Tool alignment:** `Rails/FindBy`, `Rails/FindById`, `Rails/FindEach`,
`Rails/DynamicFindBy`, `Rails/WhereEquals`, `Rails/WhereExists`,
`Rails/WhereMissing`, `Rails/WhereNot`,
`Rails/WhereNotWithMultipleConditions`, `Rails/WhereRange`,
`Rails/Pluck`, `Rails/PluckId`, `Rails/PluckInWhere`, `Rails/Pick`,
`Rails/OrderArguments`, `Rails/SaveBang`, `Rails/SkipsModelValidations`,
`Rails/RedundantActiveRecordAllMethod`, `Rails/UniqBeforePluck`,
`Rails/SelectMap`, `Rails/ScopeArgs`, `Rails/DuplicateScope`,
`Rails/ArelStar`, `Rails/SquishedSQLHeredocs`, `Rails/Blank`,
`Rails/Presence`, `Rails/Present`, and `Rails/CompactBlank` are enabled.

## 27.1 Prefer `find_by` over `where(...).first` for a single-row lookup.

> Why? [find_by](https://rails.rubystyle.guide/#find_by) states intent
> and applies a limit. `where.first` invites accidental large scans when
> the condition is wrong.
> **Violation.**
>
> Enforced by: Rails/FindBy.

```ruby
# bad
User.where(email: email).first

# good
User.find_by(email: email)
```

## 27.2 Prefer `find(id)` / `find_by(id:)` over `find_by_id`.

> Why? Dynamic finders hide arity mistakes and are a legacy API.
> `find` raises on miss; `find_by` returns `nil` — pick the failure mode
> deliberately.
> **Violation.**
>
> Enforced by: Rails/FindById, Rails/DynamicFindBy.

```ruby
# bad
User.find_by_id(params[:id])
User.find_by_email_and_role(email, 'admin')

# good
User.find(params[:id])
User.find_by(email: email, role: 'admin')
```

## 27.3 Use `find_each` / `find_in_batches` for large result sets.

> Why? [find-each](https://rails.rubystyle.guide/#find-each) streams by
> primary key in batches. `Model.all.each` loads the table into memory.
> **Violation.**
>
> Enforced by: Rails/FindEach.

```ruby
# bad
User.all.each { |user| user.reconcile! }

# good
User.find_each { |user| user.reconcile! }
```

## 27.4 Pass hash conditions (or binds), never interpolate SQL strings.

> Why? [hash-conditions](https://rails.rubystyle.guide/#hash-conditions)
> and named placeholders keep quoting correct.
> `"where email = '#{email}'"` is an injection bug waiting for review to
> miss it.
> **Suggestion** for the general rule; several cops below catch specific
> shapes.

```ruby
# bad
User.where("email = '#{email}'")
User.where("created_at > '#{1.day.ago}'")

# good
User.where(email: email)
User.where(created_at: 1.day.ago..)
User.where('email = :email', email: email)
```

## 27.5 Prefer range conditions and `where(column: range)` over hand-built SQL.

> Why? [where-ranges](https://rails.rubystyle.guide/#where-ranges) map
> cleanly to SQL `BETWEEN` / inequality and stay index-friendly.
> **Violation.**
>
> Enforced by: Rails/WhereRange.

```ruby
# bad
Order.where('created_at >= ? AND created_at <= ?', start_at, end_at)

# good
Order.where(created_at: start_at..end_at)
```

## 27.6 Use `where.not` carefully — especially with multiple attributes.

> Why? [where-not](https://rails.rubystyle.guide/#where-not) and
> [where-not-with-multiple-attributes](https://rails.rubystyle.guide/#where-not-with-multiple-attributes)
> document that `where.not(a: 1, b: 2)` is NOT `(a != 1 AND b != 2)` in
> the way many readers expect — it is a NAND-style predicate. Prefer
> chained `where.not` or explicit SQL with binds when you need AND of
> negations.
> **Violation** for the multi-attribute form the cop flags.
>
> Enforced by: Rails/WhereNot, Rails/WhereNotWithMultipleConditions.

```ruby
# bad — easy to misread
User.where.not(role: 'admin', active: false)

# good — explicit
User.where.not(role: 'admin').where.not(active: false)
User.where(role: roles_other_than_admin)
```

## 27.7 Prefer `exists?` over `present?` / `any?` / `count` for existence checks.

> Why? `exists?` selects `1` with a limit. Loading records or counting
> them to ask a boolean question wastes work.
> **Violation.**
>
> Enforced by: Rails/WhereExists.

```ruby
# bad
user.orders.where(state: 'open').present?
user.orders.where(state: 'open').count > 0

# good
user.orders.where(state: 'open').exists?
```

## 27.8 Prefer `where.missing` / `where.associated` for relationship presence.

> Why? [finding-missing-relationship-records](https://rails.rubystyle.guide/#finding-missing-relationship-records)
> is clearer and usually cheaper than `left_joins` + `WHERE fk IS NULL`
> hand-rolls.
> **Violation.**
>
> Enforced by: Rails/WhereMissing.

```ruby
# bad
User.left_joins(:profile).where(profiles: { id: nil })

# good
User.where.missing(:profile)
```

## 27.9 Use `pluck` / `pick` when you only need column values.

> Why? [pluck](https://rails.rubystyle.guide/#pluck) and
> [pick](https://rails.rubystyle.guide/#pick) skip model instantiation.
> Mapping `all.map(&:email)` builds objects you throw away.
> **Violation.**
>
> Enforced by: Rails/Pluck, Rails/Pick, Rails/PluckId.

```ruby
# bad
User.all.map(&:id)
User.where(active: true).map(&:email)
User.find_by(email: email)&.name

# good
User.pluck(:id)
User.where(active: true).pluck(:email)
User.where(email: email).pick(:name)
```

## 27.10 Do not `pluck` IDs to feed a `WHERE id IN (...)` when a subquery will do.

> Why? `pluck` materializes the full ID list in Ruby. A subquery keeps
> the work in the database and avoids huge `IN` lists.
> **Violation.**
>
> Enforced by: Rails/PluckInWhere.

```ruby
# bad
Order.where(user_id: User.active.pluck(:id))

# good
Order.where(user_id: User.active.select(:id))
```

## 27.11 Call `distinct` before `pluck` when uniqueness matters.

> Why? `pluck` does not dedupe. `uniq` in Ruby is late and allocates.
> **Violation.**
>
> Enforced by: Rails/UniqBeforePluck.

```ruby
# bad
User.joins(:roles).pluck(:email).uniq

# good
User.joins(:roles).distinct.pluck(:email)
```

## 27.12 Prefer hash / symbol `order` arguments over SQL fragments when equivalent.

> Why? [order-arguments](https://rails.rubystyle.guide/#order-arguments)
> stay portable and Arel-safe. Reserve strings for expressions the hash
> form cannot express.
> **Violation.**
>
> Enforced by: Rails/OrderArguments.

```ruby
# bad
User.order('created_at desc')

# good
User.order(created_at: :desc)
```

## 27.13 Name reusable queries as `scope` / class methods returning relations.

> Why? [named-scopes](https://rails.rubystyle.guide/#named-scopes) and
> [named-scope-class](https://rails.rubystyle.guide/#named-scope-class)
> keep controllers free of query soup. Scopes must take a lambda /
> callable — naked scopes are evaluated at boot.
> **Violation** for bad scope args / duplicates.
>
> Enforced by: Rails/ScopeArgs, Rails/DuplicateScope.

```ruby
# bad
scope :active, where(active: true)
scope :paid, -> { where(state: 'paid') }
scope :paid, -> { where(status: 'paid') } # duplicate name

# good
scope :active, -> { where(active: true) }
scope :paid, -> { where(state: 'paid') }

def self.created_after(time)
  where(created_at: time..)
end
```

## 27.14 Drop redundant `.all` before relation methods.

> Why? [redundant-all](https://rails.rubystyle.guide/#redundant-all) —
> `Model.all.where` is just `Model.where`.
> **Violation.**
>
> Enforced by: Rails/RedundantActiveRecordAllMethod.

```ruby
# bad
User.all.where(active: true)
User.all.find_each { }

# good
User.where(active: true)
User.find_each { }
```

## 27.15 Squish SQL heredocs; prefer `<<~SQL.squish` for multi-line SQL.

> Why? [squished-heredocs](https://rails.rubystyle.guide/#squished-heredocs)
> and [prefer-squiggly-heredoc](https://rails.rubystyle.guide/#prefer-squiggly-heredoc)
> keep whitespace out of the query string and logs.
> **Violation.**
>
> Enforced by: Rails/SquishedSQLHeredocs.

```ruby
# bad
User.find_by_sql(<<-SQL)
  SELECT * FROM users
  WHERE active = TRUE
SQL

# good
User.find_by_sql(<<~SQL.squish)
  SELECT * FROM users
  WHERE active = TRUE
SQL
```

## 27.16 Prefer `select` + `map` alternatives the Rails cops recommend (`select`/`map` → `filter_map` patterns via `Rails/SelectMap` where applicable).

> Why? Building arrays of attributes through `select` then `map` often
> has a cheaper relation API (`pluck`) or a single-pass Enumerable.
> **Violation** for the patterns `Rails/SelectMap` matches.
>
> Enforced by: Rails/SelectMap.

```ruby
# bad — instantiate then project
User.select(&:active?).map(&:email)

# good
User.where(active: true).pluck(:email)
```

## 27.17 Use `where(column: value)` equality helpers instead of `= ?` boilerplate.

> Why? `Rails/WhereEquals` rewrites verbose equality into hash form,
> which composes with other hash conditions.
> **Violation.**
>
> Enforced by: Rails/WhereEquals.

```ruby
# bad
Account.where('plan = ?', 'pro')

# good
Account.where(plan: 'pro')
```

## 27.18 Prefer `blank?` / `present?` / `presence` Active Support predicates consistently in query guards.

> Why? Mixing `nil? || empty?` with Rails predicates fragments style and
> misses `false`-aware behaviour. Cops unify the idioms.
> **Violation.**
>
> Enforced by: Rails/Blank, Rails/Present, Rails/Presence, Rails/CompactBlank.

```ruby
# bad
emails = params[:emails]
emails = emails.reject { |email| email.nil? || email.empty? }

# good
emails = Array(params[:emails]).compact_blank
name = params[:name].presence || 'guest'
```

## 27.19 Prefer `size` (or an explicit `count` / `length`) over habitually calling `count` on relations.

> Why? [size-over-count-or-length](https://rails.rubystyle.guide/#size-over-count-or-length)
> — `size` uses the loaded collection when present and otherwise issues a
> `COUNT` query. Blind `count` always hits the database even after
> `includes` / `load`. Prefer `length` only when you intentionally want
> the in-memory array size after loading.
> **Suggestion.**

```ruby
# bad — second query after the relation is already loaded
users = User.where(active: true).load
users.count

# good
users = User.where(active: true).load
users.size
```

## 27.20 Do not use `id` as a chronological sort key.

> Why? [order-by-id](https://rails.rubystyle.guide/#order-by-id) —
> primary-key order is not a guaranteed timeline (especially with UUIDs
> or imported rows). Order on a timestamp column when you mean
> "chronological."
> **Suggestion.**

```ruby
# bad
scope :chronological, -> { order(id: :asc) }

# good
scope :chronological, -> { order(created_at: :asc) }
```

## 27.21 Do not memoize `find_by` with `||=` when `nil` is a valid miss.

> Why? [find-by-memoization](https://rails.rubystyle.guide/#find-by-memoization)
> — `nil` is falsey, so `@user ||= User.find_by(...)` re-queries forever
> on a missing row. Use an explicit defined? / instance-variable check,
> `ActiveSupport::CurrentAttributes`, or accept the lookup cost.
> **Suggestion.**

```ruby
# bad
def current_user
  @current_user ||= User.find_by(id: session[:user_id])
end

# good
def current_user
  return @current_user if defined?(@current_user)

  @current_user = User.find_by(id: session[:user_id])
end
```

## 27.22 Prefer `find(id)` when a missing primary key must raise `RecordNotFound`.

> Why? [find](https://rails.rubystyle.guide/#find) is the idiomatic
> bang-on-miss lookup by id. `where(id:).take!` / `find_by!` work but
> obscure the failure mode reviewers expect on member routes.
> **Suggestion** (style); pair with 27.1 / 27.2 for the non-raising path.

```ruby
# bad
User.where(id: id).take!
User.find_by!(id: id)

# good
User.find(id)
```
