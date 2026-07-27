<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 26. ActiveRecord Models

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

An ActiveRecord model is the persistence boundary: associations,
validations, scopes that name a query, and the smallest amount of domain
logic that is inseparable from the row. Everything else — multi-model
workflows, IO, orchestration — belongs in a service object
([Chapter 34](34-service-objects.md)) or a query object
([Chapter 27](27-activerecord-queries.md)).

Normative sources:
[models](https://rails.rubystyle.guide/#models),
[model classes](https://rails.rubystyle.guide/#model-classes),
[meaningful names](https://rails.rubystyle.guide/#meaningful-model-names),
[callbacks order](https://rails.rubystyle.guide/#callbacks-order),
[dependent option](https://rails.rubystyle.guide/#has_many-has_one-dependent-option),
[enums](https://rails.rubystyle.guide/#enums),
[new-style validations](https://rails.rubystyle.guide/#new-style-validations),
[macro-style methods](https://rails.rubystyle.guide/#macro-style-methods),
and
[beware skip validations](https://rails.rubystyle.guide/#beware-skip-model-validations).

**Tool alignment:** `Rails/ApplicationRecord`,
`Rails/ActiveRecordCallbacksOrder`, `Rails/HasManyOrHasOneDependent`,
`Rails/HasAndBelongsToMany`, `Rails/EnumHash`, `Rails/EnumSyntax`,
`Rails/Validation`, `Rails/SkipsModelValidations`,
`Rails/DuplicateAssociation`, `Rails/InverseOf`,
`Rails/RedundantForeignKey`,
`Rails/RedundantPresenceValidationOnBelongsTo`,
`Rails/UniqueValidationWithoutIndex`, `Rails/TableNameAssignment`,
`Rails/IgnoredColumnsAssignment`, `Rails/UnusedIgnoredColumns`,
`Rails/ActiveRecordOverride`, `Rails/ReadWriteAttribute`,
`Rails/Delegate`, and `Rails/DangerousColumnNames` are enabled.
Matching rules are **Violation**.

## 26.1 Keep models named for the business concept, not the table trick.

> Why? [Meaningful model names](https://rails.rubystyle.guide/#meaningful-model-names)
> beat clever abbreviations. `User` and `InvoiceLine` communicate;
> `Usr` and `InvLn` force every reader to expand the alias.
> **Suggestion.**

```ruby
# bad
class Usr < ApplicationRecord
end

class InvLn < ApplicationRecord
  self.table_name = 'invoice_lines'
end

# good
class User < ApplicationRecord
end

class InvoiceLine < ApplicationRecord
end
```

## 26.2 Prefer `has_many :through` over `has_and_belongs_to_many`.

> Why? HABTM hides the join model, so the day you need a timestamp or
> role on the membership you rewrite the association. The guide prefers
> [has-many-through](https://rails.rubystyle.guide/#has-many-through).
> **Violation.**
>
> Enforced by: Rails/HasAndBelongsToMany.

```ruby
# bad
class User < ApplicationRecord
  has_and_belongs_to_many :accounts
end

# good
class User < ApplicationRecord
  has_many :memberships
  has_many :accounts, through: :memberships
end

class Membership < ApplicationRecord
  belongs_to :user
  belongs_to :account
end
```

## 26.3 Always set `dependent:` on `has_many` / `has_one` that own records.

> Why? Without `dependent:`, destroying a parent leaves orphans or
> foreign-key errors depending on the database. Name the lifecycle
> explicitly — `:destroy`, `:delete_all`, `:nullify`, or `:restrict_with_exception`.
> See
> [has_many-has_one-dependent-option](https://rails.rubystyle.guide/#has_many-has_one-dependent-option).
> **Violation.**
>
> Enforced by: Rails/HasManyOrHasOneDependent.

```ruby
# bad
class Account < ApplicationRecord
  has_many :invoices
  has_one :billing_profile
end

# good
class Account < ApplicationRecord
  has_many :invoices, dependent: :restrict_with_exception
  has_one :billing_profile, dependent: :destroy
end
```

## 26.4 Declare `inverse_of` when Rails cannot infer it.

> Why? Bi-directional associations without `inverse_of` load duplicate
> in-memory copies of the same row, breaking in-memory consistency and
> doubling writes. Explicit `inverse_of` is cheap documentation.
> **Violation** when the cop can see the ambiguity.
>
> Enforced by: Rails/InverseOf.

```ruby
# bad
class Patient < ApplicationRecord
  has_many :appointments
end

class Appointment < ApplicationRecord
  belongs_to :patient
  belongs_to :scheduler, class_name: 'User'
end

# good
class Patient < ApplicationRecord
  has_many :appointments, inverse_of: :patient
end

class Appointment < ApplicationRecord
  belongs_to :patient, inverse_of: :appointments
  belongs_to :scheduler, class_name: 'User', inverse_of: :scheduled_appointments
end
```

## 26.5 Order Active Record callbacks in the canonical lifecycle order.

> Why? Readers expect `before_validation` before `before_save` before
> `after_commit`. Scrambled callbacks hide dependency bugs. Follow
> [callbacks-order](https://rails.rubystyle.guide/#callbacks-order).
> **Violation.**
>
> Enforced by: Rails/ActiveRecordCallbacksOrder.

```ruby
# bad
class Order < ApplicationRecord
  after_commit :notify!
  before_validation :normalize_currency
  before_save :calculate_totals
end

# good
class Order < ApplicationRecord
  before_validation :normalize_currency
  before_save :calculate_totals
  after_commit :notify!
end
```

## 26.6 Prefer `after_commit` for external side effects; never do IO in `after_save`.

> Why? `after_save` runs inside the transaction. If the mailer or job
> enqueue succeeds and the transaction rolls back, you notified the
> world about a row that does not exist. Push side effects to
> `after_commit` (or an explicit service call after `save!`).
> **Suggestion.**

```ruby
# bad
class User < ApplicationRecord
  after_save :send_welcome_email

  def send_welcome_email
    UserMailer.welcome(self).deliver_later
  end
end

# good
class User < ApplicationRecord
  after_commit :send_welcome_email, on: :create

  def send_welcome_email
    UserMailer.welcome(self).deliver_later
  end
end
```

## 26.7 Use the modern validation macros, not `validates_presence_of`-style methods.

> Why? [New-style validations](https://rails.rubystyle.guide/#new-style-validations)
> are the maintained API. The old `validates_*_of` helpers are legacy
> surface.
> **Violation.**
>
> Enforced by: Rails/Validation.

```ruby
# bad
class Account < ApplicationRecord
  validates_presence_of :name
  validates_uniqueness_of :slug
end

# good
class Account < ApplicationRecord
  validates :name, presence: true
  validates :slug, uniqueness: true
end
```

## 26.8 Keep single-attribute validations on one `validates` line when they share the attribute.

> Why? [Single-attribute validations](https://rails.rubystyle.guide/#single-attribute-validations)
> stay readable when options group under one attribute. Splitting them
> across macros makes overrides harder to see.
> **Suggestion.**

```ruby
# bad
validates :email, presence: true
validates :email, uniqueness: true
validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }

# good
validates :email, presence: true,
                  uniqueness: true,
                  format: { with: URI::MailTo::EMAIL_REGEXP }
```

## 26.9 Do not add a redundant `presence` validation on a required `belongs_to`.

> Why? Rails already validates `belongs_to` presence by default. A second
> `validates :user, presence: true` duplicates the error and confuses
> readers about which check owns the message.
> **Violation.**
>
> Enforced by: Rails/RedundantPresenceValidationOnBelongsTo.

```ruby
# bad
class Membership < ApplicationRecord
  belongs_to :user
  validates :user, presence: true
end

# good
class Membership < ApplicationRecord
  belongs_to :user
end
```

## 26.10 Pair `uniqueness` validations with a unique database index.

> Why? Validations race. Two requests can both pass `validates
> uniqueness` and both insert. The index is the real guarantee;
> the validation is UX. See also migration chapter for the index itself.
> **Violation.**
>
> Enforced by: Rails/UniqueValidationWithoutIndex.

```ruby
# bad — validation only
class User < ApplicationRecord
  validates :email, uniqueness: true
end

# good — validation plus unique index in a migration
class User < ApplicationRecord
  validates :email, uniqueness: true
end

# db/migrate/xxx_add_index_to_users_email.rb
# add_index :users, :email, unique: true
```

## 26.11 Declare enums with a hash mapping (and the current enum syntax).

> Why? Array enums break when you reorder values; hash enums keep the
> integer stable. Follow [enums](https://rails.rubystyle.guide/#enums).
> **Violation.**
>
> Enforced by: Rails/EnumHash, Rails/EnumSyntax.

```ruby
# bad
enum :status, [:pending, :paid, :void]

# good
enum :status, { pending: 0, paid: 1, void: 2 }
```

## 26.12 Never use `update_attribute`, `update_column`, `update_columns`, or `save(validate: false)` casually.

> Why? These APIs
> [skip validations](https://rails.rubystyle.guide/#beware-skip-model-validations)
> (and often callbacks). They exist for deliberate migrations and
> hot-path counters, not for ordinary writes. Prefer `update!` /
> `save!`.
> **Violation.**
>
> Enforced by: Rails/SkipsModelValidations.

```ruby
# bad
user.update_attribute(:admin, true)
user.update_columns(login_count: user.login_count + 1)
user.save(validate: false)

# good
user.update!(admin: true)
user.with_lock do
  user.update!(login_count: user.login_count + 1)
end
```

## 26.13 Prefer bang writers when failure must raise; check return values otherwise.

> Why? [save-bang](https://rails.rubystyle.guide/#save-bang) makes the
> failure mode visible. Silent `false` from `save` is how invalid rows
> look "successful" in controllers.
> **Violation** when `Rails/SaveBang` sees an ignored return value
> (shipped with `AllowImplicitReturn: false`).
>
> Enforced by: Rails/SaveBang.

```ruby
# bad
def activate!
  user.update(active: true)
end

# good
def activate!
  user.update!(active: true)
end
```

## 26.14 Do not override Active Record core methods (`create`, `update`, `save`, `destroy`) to inject business flow.

> Why? Overrides of persistence verbs break every caller that expects
> framework semantics — including nested attributes, associations, and
> `update_all` relatives. Put orchestration in a service; keep models
> predictable. `Rails/ActiveRecordOverride` flags the dangerous ones.
> **Violation.**
>
> Enforced by: Rails/ActiveRecordOverride.

```ruby
# bad
class Order < ApplicationRecord
  def save(**)
    apply_discounts
    super
  end
end

# good
class Orders::Checkout
  def call(order)
    order.apply_discounts
    order.save!
  end
end
```

## 26.15 Prefer `attribute` readers/writers over `read_attribute` / `write_attribute` / `self[:attr]`.

> Why? [read-attribute](https://rails.rubystyle.guide/#read-attribute)
> and [write-attribute](https://rails.rubystyle.guide/#write-attribute)
> are escape hatches. Normal code should use the generated methods so
> type casting and dirty tracking stay consistent.
> **Violation.**
>
> Enforced by: Rails/ReadWriteAttribute.

```ruby
# bad
def display_name
  read_attribute(:name).presence || email
end

def name=(value)
  write_attribute(:name, value.to_s.strip)
end

# good
def display_name
  name.presence || email
end

def name=(value)
  super(value.to_s.strip)
end
```

## 26.16 Avoid assigning `self.table_name` unless you are mapping a legacy table.

> Why? Convention exists so renames stay mechanical. Manual
> `table_name=` is a permanent tax. When you must map legacy schemas,
> document why next to the assignment.
> **Violation** for unnecessary assignment patterns the cop flags.
>
> Enforced by: Rails/TableNameAssignment.

```ruby
# bad — modern app inventing a nickname
class User < ApplicationRecord
  self.table_name = 'people'
end

# good — default convention
class User < ApplicationRecord
end

# acceptable — documented legacy mapping
class LegacyPayment < ApplicationRecord
  # Maps to the 2012 billing database table name.
  self.table_name = 'tbl_payments'
end
```

## 26.17 Manage `ignored_columns` carefully — assign once, prune unused entries.

> Why? [append-ignored-columns](https://rails.rubystyle.guide/#append-ignored-columns)
> exists for zero-downtime column drops. Leaving stale ignored columns
> forever hides schema drift; reassigning incorrectly can wipe the list.
> **Violation.**
>
> Enforced by: Rails/IgnoredColumnsAssignment, Rails/UnusedIgnoredColumns.

```ruby
# bad — clobbering previous ignores
self.ignored_columns = ['legacy_flag']

# good — append during the deploy window, then remove after drop
self.ignored_columns += ['legacy_flag']
```

## 26.18 Keep fat workflows out of the model; extract service objects when a method orchestrates collaborators.

> Why? [model-business-logic](https://rails.rubystyle.guide/#model-business-logic)
> allows domain rules that belong to the entity; it does not bless a
> 200-line `fulfill!` that talks to payments, inventory, and mailers.
> See [Chapter 34](34-service-objects.md).
> **Suggestion.**

```ruby
# bad
class Order < ApplicationRecord
  def fulfill!
    charge_card!
    reserve_stock!
    OrderMailer.receipt(self).deliver_later
    update!(state: :fulfilled)
  end
end

# good
class Order < ApplicationRecord
  def mark_fulfilled!
    update!(state: :fulfilled)
  end
end

class Orders::Fulfill
  def call(order)
    Payments.charge!(order)
    Inventory.reserve!(order)
    order.mark_fulfilled!
    OrderMailer.receipt(order).deliver_later
  end
end
```

## 26.19 Call validating `before_destroy` callbacks with `prepend: true` when `dependent:` associations also destroy.

> Why? [before_destroy](https://rails.rubystyle.guide/#before_destroy) —
> Rails installs `dependent: :destroy` callbacks that can run before your
> guard. Without `prepend: true`, `ensure_deletable` never sees the
> children and the row is already gone.
> **Suggestion.**

```ruby
# bad — roles may already be destroyed when the guard runs
class Account < ApplicationRecord
  has_many :roles, dependent: :destroy
  before_destroy :ensure_deletable

  def ensure_deletable
    throw(:abort) if roles.exists?(name: 'owner')
  end
end

# good
class Account < ApplicationRecord
  has_many :roles, dependent: :destroy
  before_destroy :ensure_deletable, prepend: true
end
```

## 26.20 Name custom validation methods as statements, not predicates.

> Why? [custom-validation-methods](https://rails.rubystyle.guide/#custom-validation-methods)
> wants `validate :expiration_date_cannot_be_in_the_past` to read as a
> natural rule. Predicate names (`valid_email?`) look like query methods
> and hide that they add errors.
> **Suggestion.**

```ruby
# bad
validate :email_ok?
validate :valid_dates?

# good
validate :email_must_look_like_an_address
validate :expiration_date_cannot_be_in_the_past

def expiration_date_cannot_be_in_the_past
  return if expires_on.blank? || expires_on >= Date.current

  errors.add(:expires_on, 'must be today or later')
end
```

## 26.21 Extract reused format/domain validations into `app/validators`.

> Why? [custom-validator-file](https://rails.rubystyle.guide/#custom-validator-file)
> and [app-validators](https://rails.rubystyle.guide/#app-validators) keep
> regex and multi-attribute rules out of every model. One
> `EmailValidator` beats five copy-pasted `format:` hashes.
> **Suggestion.**

```ruby
# bad — duplicated across User, Invite, BillingContact
validates :email, format: { with: /\A[^@\s]+@[^@\s]+\z/ }

# good — app/validators/email_validator.rb
class EmailValidator < ActiveModel::EachValidator
  def validate_each(record, attribute, value)
    return if value.to_s.match?(/\A[^@\s]+@[^@\s]+\z/)

    record.errors.add(attribute, options.fetch(:message, 'is not an email'))
  end
end

# good — in the model
validates :email, email: true
```
