<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 25. Rails Application Structure

A Rails 8.x app is a directed graph of entry points — HTTP, jobs, mailers,
rake, console — all converging on the same domain objects. Structure is
what keeps that graph readable: every concrete class hangs off an
`Application*` base, configuration lives in one place per concern, and
the boot path never reaches into `ENV` from random model methods.

This chapter draws from the
[Rails Style Guide](https://github.com/rubocop/rails-style-guide)
(HTML mirror for deep links) sections on
[configuration](https://rails.rubystyle.guide/#configuration),
[config defaults](https://rails.rubystyle.guide/#config-defaults),
[initializers](https://rails.rubystyle.guide/#config-initializers),
[Bundler](https://rails.rubystyle.guide/#bundler), and
[environment configs](https://rails.rubystyle.guide/#dev-test-prod-configs).
Model, controller, job, and mailer internals are
[Chapter 26](26-activerecord-models.md),
[Chapter 29](29-controllers-and-strong-params.md),
[Chapter 32](32-jobs-and-activejob.md), and
[Chapter 33](33-mailers.md). RuboCop wiring is
[Chapter 37](37-rubocop-configuration.md).

**Tool alignment:** `Rails/ApplicationRecord`,
`Rails/ApplicationController`, `Rails/ApplicationJob`,
`Rails/ApplicationMailer`, `Rails/EnvironmentVariableAccess`,
`Rails/EnvironmentComparison`, `Rails/UnknownEnv`, `Rails/Exit`,
`Rails/Output`, `Rails/RakeEnvironment`, `Rails/FilePath`,
`Rails/RootPathnameMethods`, and `Style/FetchEnvVar` are enabled in the
shipped `.rubocop.yml`. Rules those cops catch are **Violation**; the rest
are **Suggestion**.

## 25.1 Inherit models from `ApplicationRecord`, not `ActiveRecord::Base`.

> Why? `ApplicationRecord` is the app-wide seam for shared scopes,
> default includes, and connection-pool behaviour. Inheriting
> `ActiveRecord::Base` bypasses that seam, so the next cross-cutting
> change has to be pasted into every model. The
> [Rails Style Guide](https://rails.rubystyle.guide/#keep-ar-defaults)
> keeps Active Record defaults intentional; the inheritance rule is how
> those defaults stay in one class.
> **Violation.**
>
> Enforced by: Rails/ApplicationRecord.

```ruby
# bad
class User < ActiveRecord::Base
end

# good
class User < ApplicationRecord
end
```

## 25.2 Inherit controllers from `ApplicationController`.

> Why? Authentication filters, rescue handlers, default layouts, and
> forgery protection belong on one base. A controller that subclasses
> `ActionController::Base` (or `API`) directly silently opts out of every
> app-wide policy you thought was universal.
> **Violation.**
>
> Enforced by: Rails/ApplicationController.

```ruby
# bad
class OrdersController < ActionController::Base
  def show
    render json: Order.find(params[:id])
  end
end

# good
class OrdersController < ApplicationController
  def show
    render json: Order.find(params[:id])
  end
end
```

## 25.3 Inherit jobs from `ApplicationJob` and mailers from `ApplicationMailer`.

> Why? Retry policy, queue adapter defaults, error reporting, and default
> from-addresses are app configuration, not per-class trivia. Skipping the
> application base means each job reinvents `retry_on` and each mailer
> reinvents `default from:`.
> **Violation.**
>
> Enforced by: Rails/ApplicationJob, Rails/ApplicationMailer.

```ruby
# bad
class DigestJob < ActiveJob::Base
  def perform(user_id)
    # ...
  end
end

class UserMailer < ActionMailer::Base
  def welcome(user)
    mail(to: user.email)
  end
end

# good
class DigestJob < ApplicationJob
  def perform(user_id)
    # ...
  end
end

class UserMailer < ApplicationMailer
  def welcome(user)
    mail(to: user.email)
  end
end
```

## 25.4 Keep custom config in `config/initializers/` or `config_for`, not scattered constants.

> Why? The
> [configuration](https://rails.rubystyle.guide/#configuration) and
> [initializer](https://rails.rubystyle.guide/#config-initializers)
> sections treat boot-time setup as a first-class location. Magic numbers
> and feature flags buried in models make environment-specific overrides
> impossible without editing domain code.
> **Suggestion.**

```ruby
# bad — app/models/invoice.rb
class Invoice < ApplicationRecord
  TAX_RATE = 0.0875
  LATE_FEE_CENTS = 1500
end

# good — config/invoice.yml + config/initializers/invoice.rb
# config/invoice.yml
# shared:
#   tax_rate: 0.0875
#   late_fee_cents: 1500

# config/initializers/invoice.rb
Rails.application.configure do
  config.x.invoice = config_for(:invoice)
end

# usage
rate = Rails.configuration.x.invoice.tax_rate
```

## 25.5 Prefer `Rails.application.config_for` and YAML over ad-hoc `YAML.load` of app files.

> Why? `config_for` merges environment sections, raises on missing keys
> when configured to, and stays inside the Rails boot story. Hand-rolled
> `YAML.load(File.read(...))` skips that merge and trips
> `Security/YAMLLoad` when the unsafe loader is used. See also
> [yaml-config](https://rails.rubystyle.guide/#yaml-config).
> **Suggestion** for structure; unsafe loaders are **Violation** under
> Security cops (chapter 36).

```ruby
# bad
settings = YAML.load(File.read(Rails.root.join('config/billing.yml')))

# good
settings = Rails.application.config_for(:billing)
```

## 25.6 Compare environments with `Rails.env.production?`, never string equality.

> Why? `Rails.env` is an `ActiveSupport::StringInquirer`. Comparing to a
> bare string invites typos (`'prodution'`) that silently take the wrong
> branch. The style guide's
> [environment configs](https://rails.rubystyle.guide/#dev-test-prod-configs)
> assume the predicate API.
> **Violation.**
>
> Enforced by: Rails/EnvironmentComparison.

```ruby
# bad
if Rails.env == 'production'
  enable_caching!
end

# good
if Rails.env.production?
  enable_caching!
end
```

## 25.7 Do not read `ENV` directly from `app/` and `lib/` — go through credentials or config.

> Why? Raw `ENV['SECRET']` scatters deployment coupling through domain
> code, makes tests set global state, and hides missing keys until
> runtime. The shipped config enables
> `Rails/EnvironmentVariableAccess` for `app/**/*.rb` and `lib/**/*.rb`,
> and `Style/FetchEnvVar` prefers `ENV.fetch`. Put secrets in
> `Rails.application.credentials` and non-secret knobs in `config_for`.
> **Violation** inside `app/` and `lib/`.

```ruby
# bad — app/services/billing_client.rb
class BillingClient
  def initialize
    @key = ENV['BILLING_API_KEY']
  end
end

# good
class BillingClient
  def initialize(key: Rails.application.credentials.billing_api_key)
    @key = key
  end
end
```

> Enforced by: Rails/EnvironmentVariableAccess (app/lib), Style/FetchEnvVar.

## 25.8 When `ENV` access is unavoidable at the edge, use `ENV.fetch` with a clear failure.

> Why? `ENV['X']` returns `nil` and lets a typo become a mysterious
> `NoMethodError` six frames later. `fetch` fails at the boundary with
> the missing key name.
> **Violation.**
>
> Enforced by: Style/FetchEnvVar.

```ruby
# bad — config/boot edge script
adapter = ENV['QUEUE_ADAPTER']

# good
adapter = ENV.fetch('QUEUE_ADAPTER')
```

## 25.9 Never call `exit`, `abort`, or `puts`/`p`/`print` from application code.

> Why? `exit` tears down the process from inside a request or job mid-
> transaction. `puts` bypasses the logger and disappears in production
> process managers. Console noise belongs in rake tasks with an explicit
> UI, not in models.
> **Violation.**
>
> Enforced by: Rails/Exit, Rails/Output.

```ruby
# bad
def import!
  puts 'starting'
  exit(1) if rows.empty?
end

# good
def import!
  Rails.logger.info('starting import')
  raise ImportError, 'no rows' if rows.empty?
end
```

## 25.10 Depend on `:environment` in every rake task that touches Rails.

> Why? Without `:environment`, constants are unloaded, `Rails.root` may
> be wrong, and the task silently runs against a half-booted process.
> The guide's process notes in
> [managing processes](https://rails.rubystyle.guide/#managing-processes)
> assume a full boot.
> **Violation.**
>
> Enforced by: Rails/RakeEnvironment.

```ruby
# bad
task :reindex do
  Post.find_each(&:reindex!)
end

# good
task reindex: :environment do
  Post.find_each(&:reindex!)
end
```

## 25.11 Build paths with `Rails.root.join` (and Pathname methods), not string concatenation.

> Why? String-glued paths break on Windows, double-insert separators, and
> hide intent. `Rails.root.join('app', 'models')` is the idiomatic
> Pathname chain; prefer Pathname methods over `to_s` soup. See
> [prefer-to-fs](https://rails.rubystyle.guide/#prefer-to-fs) for related
> filesystem style.
> **Violation.**
>
> Enforced by: Rails/FilePath, Rails/RootPathnameMethods, Rails/RootJoinChain.

```ruby
# bad
path = "#{Rails.root}/tmp/export.csv"
File.read(Rails.root.to_s + '/config/foo.yml')

# good
path = Rails.root.join('tmp', 'export.csv')
File.read(Rails.root.join('config', 'foo.yml'))
```

## 25.12 Keep the Gemfile lean; commit `Gemfile.lock`; group gems by environment.

> Why? The guide's
> [only-good-gems](https://rails.rubystyle.guide/#only-good-gems),
> [bundler](https://rails.rubystyle.guide/#bundler), and
> [gemfile-lock](https://rails.rubystyle.guide/#gemfile-lock) rules exist
> because transitive junk becomes production surface area. Dev/test-only
> tools belong in `:development` / `:test` groups so production images
> never install them.
> **Suggestion.**

```ruby
# bad — everything in the default group
gem 'rails', '~> 8.1'
gem 'debug'
gem 'rspec-rails'
gem 'faker'

# good
gem 'rails', '~> 8.1'

group :development, :test do
  gem 'debug'
  gem 'rspec-rails'
  gem 'faker'
end
```

## 25.13 Make staging behave like production for caches, hosts, and eager load.

> Why? A staging env that mirrors development hides the exact bugs
> production will hit — missing `config.hosts`, autoload surprises,
> SSL redirects. Follow
> [staging-like-prod](https://rails.rubystyle.guide/#staging-like-prod)
> and keep
> [dev-test-prod-configs](https://rails.rubystyle.guide/#dev-test-prod-configs)
> intentionally different only where they must be.
> **Suggestion.**

```ruby
# bad — config/environments/staging.rb copies development.rb
config.enable_reloading = true
config.eager_load = false
config.consider_all_requests_local = true

# good — staging tracks production, with staging credentials/hosts
config.enable_reloading = false
config.eager_load = true
config.consider_all_requests_local = false
config.hosts << 'staging.example.com'
```

## 25.14 Put gem monkey-patches and railtie setup in `config/initializers/`, named after the gem.

> Why? [gem-initializers](https://rails.rubystyle.guide/#gem-initializers)
> keeps third-party configuration discoverable. Dropping `Money.default_currency =`
> into `application.rb` or a random model makes upgrades un-grepable.
> **Suggestion.**

```ruby
# bad — config/application.rb
module Shop
  class Application < Rails::Application
    Money.default_currency = Money::Currency.new('USD')
  end
end

# good — config/initializers/money.rb
Money.default_currency = Money::Currency.new('USD')
Money.locale_backend = :i18n
```

## 25.15 Reject unknown `Rails.env` values at the boundary that cares.

> Why? Custom env names (`qa`, `demo`) are fine when intentional, but
> typos (`produciton`) should fail fast. `Rails/UnknownEnv` flags
> comparisons against undeclared environments when the cop's list is
> configured; keep the known set explicit in CI.
> **Violation** when the cop's environment list is configured; otherwise
> treat custom env names as a documented **Suggestion**.

```ruby
# bad — silent no-op on typo
if Rails.env.produciton?
  harden!
end

# good
if Rails.env.production?
  harden!
end
```

> Enforced by: Rails/UnknownEnv.

## 25.16 Keep cross-environment settings in `config/application.rb`; keep `load_defaults` on the Rails major you run.

> Why? [app-config](https://rails.rubystyle.guide/#app-config) puts shared
> configuration in one place and warns that upgrades leave
> `config.load_defaults` on an older framework version until you bump it.
> Env-specific overrides belong in `config/environments/*`.
> **Suggestion.**

```ruby
# bad — production-only defaults that every env needs, scattered
# config/environments/production.rb
config.time_zone = 'UTC'
config.active_record.belongs_to_required_by_default = true

# good — config/application.rb
module Shop
  class Application < Rails::Application
    config.load_defaults 8.1
    config.time_zone = 'UTC'
  end
end
```

## 25.17 Prefer Ruby stdlib string/array APIs over uncommon Active Support aliases.

> Why? [active_support_aliases](https://rails.rubystyle.guide/#active_support_aliases)
> and
> [active_support_extensions](https://rails.rubystyle.guide/#active_support_extensions)
> keep call sites portable and obvious (`start_with?` / `end_with?` /
> `include?` over `starts_with?` / `ends_with?` / `in?` for ordinary
> checks). Prefer `&.` over `try!`
> ([try-bang](https://rails.rubystyle.guide/#try-bang)).
> **Violation** for the `starts_with?` / `ends_with?` forms Performance
> cops rewrite; otherwise **Suggestion**.
>
> Enforced by: Performance/StartWith, Performance/EndWith.

```ruby
# bad
'the day'.starts_with?('th')
'the day'.ends_with?('ay')
obj.try!(:fly)
'two'.inquiry.two?

# good
'the day'.start_with?('th')
'the day'.end_with?('ay')
obj&.fly
'two' == 'two'
```
