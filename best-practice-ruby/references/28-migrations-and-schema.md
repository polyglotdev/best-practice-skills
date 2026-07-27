<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 28. Migrations & Schema

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

Migrations are irreversible history once they ship to production. Write
them so `db:rollback` works in development, so production expands /
contracts safely across deploys, and so the schema dump — not a pile of
drifted SQL files — remains the source of truth for structure.

Sources:
[migrations](https://rails.rubystyle.guide/#migrations),
[change-vs-up-down](https://rails.rubystyle.guide/#change-vs-up-down),
[reversible-migration](https://rails.rubystyle.guide/#reversible-migration),
[foreign-key-constraints](https://rails.rubystyle.guide/#foreign-key-constraints),
[three-state-boolean](https://rails.rubystyle.guide/#three-state-boolean),
[default-migration-values](https://rails.rubystyle.guide/#default-migration-values),
[define-model-class-migrations](https://rails.rubystyle.guide/#define-model-class-migrations),
[schema-version](https://rails.rubystyle.guide/#schema-version),
[db-schema-load](https://rails.rubystyle.guide/#db-schema-load),
and
[meaningful-foreign-key-naming](https://rails.rubystyle.guide/#meaningful-foreign-key-naming).

**Tool alignment (important):** the shipped `.rubocop.yml` enables
`Rails/ReversibleMigration`, `Rails/CreateTableWithTimestamps`,
`Rails/NotNullColumn`, `Rails/ThreeStateBooleanColumn`,
`Rails/AddColumnIndex`, `Rails/MigrationClassName`,
`Rails/DangerousColumnNames`, and related cops, but **excludes**
`db/migrate/**/*` and `db/schema.rb` under `AllCops`. Until a project
removes that exclude, migration-file rules below are **Suggestion** —
the cops exist and are configured, but they do not run on migration
paths in this repository's default config. Chapter 37 documents the
exclude and when to open it.

## 28.1 Prefer `change` over paired `up`/`down` when the operation is reversible.

> Why? [change-vs-up-down](https://rails.rubystyle.guide/#change-vs-up-down)
> keeps the inverse in the framework. Hand-written `down` drifts from
> `up` the first time someone edits only one side.
> **Suggestion** (migrate path excluded in shipped config).

```ruby
# bad
class AddPublishedAtToPosts < ActiveRecord::Migration[8.1]
  def up
    add_column :posts, :published_at, :datetime
  end

  def down
    remove_column :posts, :published_at
  end
end

# good
class AddPublishedAtToPosts < ActiveRecord::Migration[8.1]
  def change
    add_column :posts, :published_at, :datetime
  end
end
```

## 28.2 Make irreversible steps explicit with `reversible` or `up`/`down`.

> Why? [reversible-migration](https://rails.rubystyle.guide/#reversible-migration)
> — data backfills, `execute` DDL, and some type changes cannot be
> inferred. Spell the reverse or raise `ActiveRecord::IrreversibleMigration`.
> **Suggestion** here; **Violation** if you enable cops on `db/migrate`.
>
> Enforced by: Rails/ReversibleMigration (when migrate path is included).

```ruby
# bad — change with irreversible execute
def change
  execute 'UPDATE users SET legacy_flag = 0'
end

# good
def change
  reversible do |dir|
    dir.up { execute 'UPDATE users SET legacy_flag = 0' }
    dir.down { execute 'UPDATE users SET legacy_flag = NULL' }
  end
end
```

## 28.3 Name the migration class after the file's verb and table.

> Why? `Rails/MigrationClassName` expects the class to match the filename
> so `grep` and schema history stay aligned.
> **Suggestion** under shipped excludes.
>
> Enforced by: Rails/MigrationClassName (when migrate path is included).

```ruby
# bad — file: 20260101120000_add_published_at_to_posts.rb
class AddPublishTime < ActiveRecord::Migration[8.1]
  def change
    add_column :posts, :published_at, :datetime
  end
end

# good
class AddPublishedAtToPosts < ActiveRecord::Migration[8.1]
  def change
    add_column :posts, :published_at, :datetime
  end
end
```

## 28.4 Create tables with timestamps unless you have a documented reason not to.

> Why? `created_at` / `updated_at` are the default audit surface for
> every row. Omitting them is usually an accident.
> **Suggestion** under shipped excludes.
>
> Enforced by: Rails/CreateTableWithTimestamps (when migrate path is included).

```ruby
# bad
create_table :tags do |t|
  t.string :name, null: false
end

# good
create_table :tags do |t|
  t.string :name, null: false
  t.timestamps
end
```

## 28.5 Do not add a non-null column without a default (or a multi-deploy backfill).

> Why? Adding `null: false` with no default locks the table against
> existing rows and breaks expands/contracts deploys. Prefer nullable
> add → backfill → enforce, or a default that is safe for old rows.
> **Suggestion** under shipped excludes.
>
> Enforced by: Rails/NotNullColumn (when migrate path is included).

```ruby
# bad — fails on populated table
add_column :users, :locale, :string, null: false

# good — three-step expand/contract
add_column :users, :locale, :string
# deploy code that writes locale
# backfill
change_column_null :users, :locale, false
```

## 28.6 Avoid three-state booleans — add `null: false` and a default.

> Why? [three-state-boolean](https://rails.rubystyle.guide/#three-state-boolean)
> — a boolean that allows `NULL` is a tri-state flag in disguise.
> **Suggestion** under shipped excludes.
>
> Enforced by: Rails/ThreeStateBooleanColumn (when migrate path is included).

```ruby
# bad
add_column :users, :admin, :boolean

# good
add_column :users, :admin, :boolean, null: false, default: false
```

## 28.7 Add indexes in the same migration that adds the column when you always filter on it.

> Why? `Rails/AddColumnIndex` catches the "forgot the index" footgun
> when `index: true` was intended. Unique validations especially need a
> matching unique index ([Chapter 26](26-activerecord-models.md)).
> **Suggestion** under shipped excludes.
>
> Enforced by: Rails/AddColumnIndex (when migrate path is included).

```ruby
# bad
add_column :users, :email, :string, null: false
# forgotten index

# good
add_column :users, :email, :string, null: false
add_index :users, :email, unique: true

# also good
add_column :users, :email, :string, null: false, index: { unique: true }
```

## 28.8 Add foreign key constraints for real associations.

> Why? [foreign-key-constraints](https://rails.rubystyle.guide/#foreign-key-constraints)
> keep orphans out even when someone bypasses Active Record. Pair with
> `dependent:` on the model for the in-Ruby lifecycle story.
> **Suggestion.**

```ruby
# bad
create_table :memberships do |t|
  t.bigint :user_id, null: false
  t.bigint :account_id, null: false
  t.timestamps
end

# good
create_table :memberships do |t|
  t.references :user, null: false, foreign_key: true
  t.references :account, null: false, foreign_key: true
  t.timestamps
end
```

## 28.9 Use meaningful foreign key column names — `user_id`, not `uid`.

> Why? [meaningful-foreign-key-naming](https://rails.rubystyle.guide/#meaningful-foreign-key-naming)
> lets Rails infer `belongs_to :user`. Cryptic FK names force
> `foreign_key:` / `class_name:` everywhere.
> **Suggestion.**

```ruby
# bad
t.references :usr, null: false, foreign_key: { to_table: :users }

# good
t.references :user, null: false, foreign_key: true
```

## 28.10 Never reference the app's Active Record models inside a migration — define an anonymous model if you must touch data.

> Why? [define-model-class-migrations](https://rails.rubystyle.guide/#define-model-class-migrations)
> — tomorrow's `User` callbacks and validations will break yesterday's
> migration. Inline a minimal AR class bound to the table.
> **Suggestion.**

```ruby
# bad
class BackfillUserLocales < ActiveRecord::Migration[8.1]
  def up
    User.find_each { |user| user.update!(locale: 'en') }
  end
end

# good
class BackfillUserLocales < ActiveRecord::Migration[8.1]
  class MigrationUser < ApplicationRecord
    self.table_name = 'users'
  end

  def up
    MigrationUser.reset_column_information
    MigrationUser.find_each { |user| user.update_columns(locale: 'en') }
  end
end
```

## 28.11 Prefer schema load / structure load for empty databases over replaying hundreds of migrations.

> Why? [db-schema-load](https://rails.rubystyle.guide/#db-schema-load)
> and [schema-version](https://rails.rubystyle.guide/#schema-version) —
> `db:schema:load` is the fast path for new environments; migrations
> remain the incremental path for existing ones. Keep `schema.rb` (or
> `structure.sql`) committed and current.
> **Suggestion.**

```ruby
# bad — CI always runs every migration from 2014
bundle exec rails db:migrate

# good — empty DB in CI
bundle exec rails db:schema:load
# or
bundle exec rails db:prepare
```

## 28.12 Avoid dangerous column names that clash with AR internals.

> Why? Columns named `attributes`, `class`, `errors`, or similar collide
> with Active Record methods and produce surreal bugs.
> **Suggestion** under shipped excludes.
>
> Enforced by: Rails/DangerousColumnNames (when migrate path is included).

```ruby
# bad
add_column :widgets, :attributes, :jsonb
add_column :widgets, :errors, :text

# good
add_column :widgets, :metadata, :jsonb
add_column :widgets, :error_log, :text
```

## 28.13 Set defaults in the database for columns that always have a value.

> Why? [default-migration-values](https://rails.rubystyle.guide/#default-migration-values)
> — application-only defaults vanish for bulk SQL, consoles, and other
> writers. Put the truth in the schema when the default is universal.
> **Suggestion.**

```ruby
# bad — only in the model
class User < ApplicationRecord
  attribute :admin, :boolean, default: false
end

# good — schema carries the default
add_column :users, :admin, :boolean, null: false, default: false
```

## 28.14 Do not edit old migrations after they have run in shared environments.

> Why? Migrations are append-only history. Editing a shipped migration
> creates machines that can never agree on schema. Write a new migration
> to fix shape or data.
> **Suggestion.**

```ruby
# bad — rewriting 20240101120000_create_users.rb on main after deploy

# good — add 20260727180000_make_users_email_non_null.rb
class MakeUsersEmailNonNull < ActiveRecord::Migration[8.1]
  def change
    change_column_null :users, :email, false
  end
end
```

## 28.15 Prefer reversible index / column helpers over raw `execute` DDL when Rails supports the operation.

> Why? Helpers participate in `change` inversion and adapter portability.
> Raw SQL is sometimes necessary (partial indexes, concurrent indexes) —
> isolate it and document why.
> **Suggestion.**

```ruby
# bad — portable operation written as SQL
execute 'CREATE INDEX index_users_on_email ON users (email)'

# good
add_index :users, :email

# acceptable — Postgres concurrent index (non-transactional)
disable_ddl_transaction!
add_index :users, :email, algorithm: :concurrently
```
