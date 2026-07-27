<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 36. Rails Security & Footguns

Most Rails security failures are ordinary style failures with sharp edges:
SQL built with interpolation, HTML marked safe too early, mass assignment
through loose strong params, validations skipped "just this once," and
secrets read from the wrong place. This chapter collects those footguns
against the
[Rails Style Guide](https://github.com/rubocop/rails-style-guide)
([avoid-interpolation](https://rails.rubystyle.guide/#avoid-interpolation),
[named-placeholder](https://rails.rubystyle.guide/#named-placeholder),
[beware-skip-model-validations](https://rails.rubystyle.guide/#beware-skip-model-validations),
[save-bang](https://rails.rubystyle.guide/#save-bang))
and the enabled `Security/*` / `Rails/*` cops.

Prefer **single quotes** unless a string needs interpolation.

**Tool alignment:** `Rails/OutputSafety`, `Rails/SkipsModelValidations`,
`Rails/DynamicFindBy`, `Security/Eval`, `Security/JSONLoad`,
`Security/MarshalLoad`, `Security/Open`, `Security/YAMLLoad`,
`Rails/EnvironmentVariableAccess`.

## 36.1 Never interpolate user input into SQL strings.

> Why? [avoid-interpolation](https://rails.rubystyle.guide/#avoid-interpolation)
> is the classic injection footgun. Use binds or hash conditions.
> **Suggestion** (query construction); pair with chapter 27.

```ruby
# bad
User.where("email = '#{params[:email]}'")

# good
User.where(email: params[:email])

# good — named placeholder when SQL is unavoidable
User.where('email = :email', email: params[:email])
```

## 36.2 Prefer named placeholders over `?` when SQL is required.

> Why? [named-placeholder](https://rails.rubystyle.guide/#named-placeholder)
> keeps multi-bind queries readable and harder to reorder incorrectly.
> **Suggestion.**

```ruby
# bad
User.where('created_at > ? AND plan = ?', start, plan)

# good
User.where('created_at > :start AND plan = :plan', start: start, plan: plan)
```

## 36.3 Treat `html_safe` / `raw` as a last resort with an explicit sanitize path.

> Why? Marking a string HTML-safe without sanitizing is XSS. Prefer view
> helpers that escape by default; when you must emit markup, sanitize first.
> **Violation.**
>
> Enforced by: Rails/OutputSafety.

```ruby
# bad
<%= body.html_safe %>

# good — escape by default
<%= body %>

# good — intentional HTML after sanitize
<%= sanitize(body) %>
```

## 36.4 Keep strong parameters explicit; never permit nested hashes wholesale.

> Why? `params.require(:user).permit!` and `permit(preferences: {})` without
> a key allowlist reopen mass assignment. List every scalar and nested key.
> Covered procedurally with controllers in chapter 29; restated here as a
> security gate. **Suggestion.**

```ruby
# bad
params.require(:user).permit!

# bad — open nested hash
params.require(:user).permit(:name, preferences: {})

# good
params.require(:user).permit(:name, :email, preferences: [:theme, :tz])
```

## 36.5 Never skip validations or callbacks to force a write.

> Why? [beware-skip-model-validations](https://rails.rubystyle.guide/#beware-skip-model-validations)
> lists `update_attribute`, `update_column`, `update_columns`,
> `save(validate: false)`. Attackers love half-updated rows; so do subtle
> production bugs.
> **Violation.**
>
> Enforced by: Rails/SkipsModelValidations.

```ruby
# bad
user.update_attribute(:admin, true)

# good
user.update!(admin: true)
```

## 36.6 Do not use dynamic finders built from request params.

> Why? `find_by_*` chains assembled from keys blur the allowlist. Prefer
> explicit `find_by` with known columns (`Rails/DynamicFindBy` also prefers
> the modern API).
> **Violation.**
>
> Enforced by: Rails/DynamicFindBy.

```ruby
# bad
User.find_by_email(params[:email])

# good
User.find_by(email: params[:email])
```

## 36.7 Never `eval` request data or template strings from users.

> Why? `Security/Eval` exists because `eval(params[:formula])` is remote
> code execution with extra steps.
> **Violation.**
>
> Enforced by: Security/Eval.

```ruby
# bad
result = eval(params[:expression])

# good — parse with a safe library or a constrained DSL
result = Calculator.evaluate(params[:expression])
```

## 36.8 Prefer `JSON.parse` over `JSON.load` for untrusted input.

> Why? `JSON.load` can deserialize unexpected objects depending on quirks
> mode historically; RuboCop's `Security/JSONLoad` pushes the safer parse
> API for data you do not fully trust.
> **Violation.**
>
> Enforced by: Security/JSONLoad.

```ruby
# bad
payload = JSON.load(request.body.read)

# good
payload = JSON.parse(request.body.read)
```

## 36.9 Never `Marshal.load` untrusted bytes.

> Why? Marshal can instantiate arbitrary objects and run `_load` hooks.
> **Violation.**
>
> Enforced by: Security/MarshalLoad.

```ruby
# bad
session_data = Marshal.load(cookies.signed[:blob])

# good — JSON or a dedicated serializer with an allowlist
session_data = JSON.parse(cookies.signed[:blob])
```

## 36.10 Open URIs carefully; do not pass user-controlled URLs to `open`.

> Why? `Kernel#open` / `open-uri` can hit the filesystem or the network.
> `Security/Open` flags the dangerous form.
> **Violation.**
>
> Enforced by: Security/Open.

```ruby
# bad
open(params[:url]) { |io| io.read }

# good — explicit HTTP client with allowlisted hosts
HTTP.get(validated_url(params[:url])).body.to_s
```

## 36.11 Prefer `YAML.safe_load` (or `YAML.load` with permitted classes) for untrusted YAML.

> Why? Psych can deserialize Ruby objects from YAML. `Security/YAMLLoad`
> exists for that reason.
> **Violation.**
>
> Enforced by: Security/YAMLLoad.

```ruby
# bad
config = YAML.load(File.read(path))

# good
config = YAML.safe_load(File.read(path), permitted_classes: [Date, Time])
```

## 36.12 Do not read secrets from `ENV` inside models and random POROs.

> Why? Scattering `ENV['STRIPE_KEY']` makes audits impossible and breaks
> credential rotation. Use `Rails.application.credentials` or a single
> settings object loaded at boot. `Rails/EnvironmentVariableAccess` covers
> app/lib surfaces in the shipped config.
> **Violation.**
>
> Enforced by: Rails/EnvironmentVariableAccess.

```ruby
# bad — deep in app/models/payment.rb
key = ENV['STRIPE_SECRET']

# good — injected or read from a settings object configured at boot
key = Rails.application.credentials.stripe.fetch(:secret_key)
```

## 36.13 Keep CSRF protection on for browser-facing HTML controllers.

> Why? Turning off `protect_from_forgery` for convenience on a session
> cookie app is a classic footgun. API-only token auth is a different
> design; do not copy its skips into Hotwire controllers.
> **Suggestion.**

```ruby
# bad — HTML app
class ApplicationController < ActionController::Base
  skip_forgery_protection
end

# good — default protect_from_forgery; API controllers use their own auth
```

## 36.14 Prefer single quotes for privilege flags and role strings.

> Why? Role tokens (`'admin'`, `'member'`) are ordinary strings under
> [consistent-string-literals](https://rubystyle.guide/#consistent-string-literals).
> **Violation.**
>
> Enforced by: Style/StringLiterals.

```ruby
# bad
user.update!(role: "admin")

# good
user.update!(role: 'admin')
```

## 36.15 Validate redirect targets; never send users to an open `params[:return_to]`.

> Why? Open redirects are phishing helpers. Allow only relative paths or
> an allowlisted host before `redirect_to`.
> **Suggestion.**

```ruby
# bad
redirect_to params[:return_to]

# good
def safe_return_path(raw)
  uri = URI.parse(raw.to_s)
  return root_path unless uri.relative? || uri.host.nil?

  raw
rescue URI::InvalidURIError
  root_path
end

redirect_to safe_return_path(params[:return_to])
```

## 36.16 Prefer `&.` over `try!`; prefer comparisons over `String#inquiry` / `Array#inquiry`.

> Why? [try-bang](https://rails.rubystyle.guide/#try-bang) and
> [inquiry](https://rails.rubystyle.guide/#inquiry) push modern Ruby over
> Active Support conveniences that hide nil and invent predicate APIs.
> **Violation** when `Rails/Inquiry` fires; otherwise **Suggestion**.
>
> Enforced by: Rails/Inquiry.

```ruby
# bad
user.try!(:profile).try!(:timezone)
status = params[:status].to_s.inquiry
render_admin if status.admin?

# good
user&.profile&.timezone
render_admin if params[:status] == 'admin'
```

## 36.17 Never log secrets, tokens, or raw card data.

> Why? Rails parameter filtering only helps when you keep sensitive keys
> in `config.filter_parameters`. Logging `request.headers['Authorization']`
> or `params[:card_number]` bypasses that list.
> **Suggestion.**

```ruby
# bad
Rails.logger.info("token=#{user.api_token} auth=#{request.authorization}")

# good — rely on filtered params; log ids only
Rails.logger.info({ user_id: user.id, event: 'api_token_rotated' }.to_json)
```

## 36.18 Keep `serialize` / custom coders on an allowlist; prefer JSON columns.

> Why? Legacy `serialize :preferences, Hash` and YAML coders reopen the
> Psych gadget surface covered by `Security/YAMLLoad`. Prefer
> `jsonb` / `json` columns with explicit schemas.
> **Suggestion.**

```ruby
# bad
serialize :preferences, coder: YAML

# good
# db/migrate: add_column :users, :preferences, :jsonb, null: false, default: {}
store_accessor :preferences, :theme, :tz
```

## 36.19 Fail closed on authorization: deny by default in controllers and policies.

> Why? A missing `before_action :authorize` on one member action is a
> privilege bug. Centralize authorization (Pundit, Action Policy, or a
> single `ApplicationController` helper) so new actions inherit the deny.
> **Suggestion.**

```ruby
# bad — only some actions checked
before_action :require_admin, only: [:destroy]

# good — deny by default, allowlist public endpoints
before_action :require_admin
skip_before_action :require_admin, only: [:index, :show]
```

## 36.20 Treat file uploads as untrusted: validate content type and store outside the web root.

> Why? Trusting `content_type` from the client alone is insufficient;
> combine allowlisted MIME types, size limits, and Active Storage (or
> equivalent) disk/service configuration that is not publicly executable.
> **Suggestion.**

```ruby
# bad
File.binwrite(Rails.root.join('public', params[:file].original_filename), params[:file].read)

# good
class Avatar
  CONTENT_TYPES = %w[image/jpeg image/png].freeze

  def self.attach!(user, upload)
    raise ArgumentError unless CONTENT_TYPES.include?(upload.content_type)

    user.avatar.attach(upload)
  end
end
```
