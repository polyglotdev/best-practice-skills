<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 33. Mailers

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

Mailers are another delivery adapter: they format a message and hand it
to the delivery method. Keep them thin, name them `SomethingMailer`,
send in the background by default, and never put business writes inside
a mailer action.

Sources:
[mailers](https://rails.rubystyle.guide/#mailers),
[mailer-name](https://rails.rubystyle.guide/#mailer-name),
[email-addresses](https://rails.rubystyle.guide/#email-addresses),
[html-plain-email](https://rails.rubystyle.guide/#html-plain-email),
[background-email](https://rails.rubystyle.guide/#background-email),
[delivery-method-smtp](https://rails.rubystyle.guide/#delivery-method-smtp),
[delivery-method-test](https://rails.rubystyle.guide/#delivery-method-test),
[enable-delivery-errors](https://rails.rubystyle.guide/#enable-delivery-errors),
[inline-email-styles](https://rails.rubystyle.guide/#inline-email-styles),
and
[default-hostname](https://rails.rubystyle.guide/#default-hostname).

**Tool alignment:** `Rails/ApplicationMailer`, `Rails/MailerName`,
`Rails/I18nLocaleTexts`, `Rails/OutputSafety`, and `Rails/TimeZone`
are enabled.

## 33.1 Inherit from `ApplicationMailer`.

> Why? Default `from`, layout, and rescue/delivery hooks live on the
> application base.
> **Violation.**
>
> Enforced by: Rails/ApplicationMailer.

```ruby
# bad
class UserMailer < ActionMailer::Base
  def welcome(user)
    mail(to: user.email)
  end
end

# good
class UserMailer < ApplicationMailer
  def welcome(user)
    mail(to: user.email)
  end
end
```

## 33.2 Name mailer classes with a `Mailer` suffix.

> Why? [mailer-name](https://rails.rubystyle.guide/#mailer-name) keeps
> Zeitwerk paths and reviewer expectations aligned (`user_mailer.rb`).
> **Violation.**
>
> Enforced by: Rails/MailerName.

```ruby
# bad
class UserEmail < ApplicationMailer
end

# good
class UserMailer < ApplicationMailer
end
```

## 33.3 Keep mailer actions free of persistence and orchestration.

> Why? A mailer that `user.update!`s is a hidden service object. Pass in
> the data you need; let the caller mutate state.
> **Suggestion.**

```ruby
# bad
def welcome(user)
  user.update!(welcome_sent_at: Time.current)
  mail(to: user.email)
end

# good
def welcome(user)
  @user = user
  mail(to: user.email, subject: default_i18n_subject)
end
```

## 33.4 Use `deliver_later` by default; reserve `deliver_now` for the rare sync path.

> Why? [background-email](https://rails.rubystyle.guide/#background-email)
> — SMTP latency must not sit on the request timeline.
> **Suggestion.**

```ruby
# bad
UserMailer.welcome(user).deliver_now

# good
UserMailer.welcome(user).deliver_later
```

## 33.5 Provide both HTML and plain-text templates for user email.

> Why? [html-plain-email](https://rails.rubystyle.guide/#html-plain-email)
> — clients and accessibility tooling still need text/plain.
> **Suggestion.**

```ruby
# bad — only app/views/user_mailer/welcome.html.erb

# good — both
# app/views/user_mailer/welcome.html.erb
# app/views/user_mailer/welcome.text.erb
```

## 33.6 Set explicit, valid from/reply-to addresses via defaults or `mail(from:)`.

> Why? [email-addresses](https://rails.rubystyle.guide/#email-addresses)
> — missing or spoofed From headers destroy deliverability.
> **Suggestion.**

```ruby
# bad
class AlertsMailer < ApplicationMailer
  def spike(account)
    mail(to: account.owner.email) # no from
  end
end

# good
class ApplicationMailer < ActionMailer::Base
  default from: 'App <noreply@example.com>',
          reply_to: 'Support <support@example.com>'
end
```

## 33.7 Configure SMTP (or your provider) in environment config; enable raise on delivery errors in non-prod as appropriate.

> Why? [delivery-method-smtp](https://rails.rubystyle.guide/#delivery-method-smtp)
> and
> [enable-delivery-errors](https://rails.rubystyle.guide/#enable-delivery-errors)
> — silent failures hide broken credentials until users complain.
> **Suggestion.**

```ruby
# config/environments/production.rb
config.action_mailer.delivery_method = :smtp
config.action_mailer.perform_deliveries = true
config.action_mailer.raise_delivery_errors = true
```

## 33.8 Use `:test` delivery in the test environment and assert on `ActionMailer::Base.deliveries`.

> Why? [delivery-method-test](https://rails.rubystyle.guide/#delivery-method-test)
> keeps specs offline and deterministic.
> **Suggestion.**

```ruby
# config/environments/test.rb
config.action_mailer.delivery_method = :test

# spec
expect {
  UserMailer.welcome(user).deliver_now
}.to change { ActionMailer::Base.deliveries.size }.by(1)
```

## 33.9 Set `default_url_options` host per environment.

> Why? [default-hostname](https://rails.rubystyle.guide/#default-hostname)
> — path helpers inside mailers need a host or every link is wrong.
> **Suggestion.**

```ruby
# config/environments/production.rb
config.action_mailer.default_url_options = { host: 'www.example.com', protocol: 'https' }

# config/environments/development.rb
config.action_mailer.default_url_options = { host: 'localhost', port: 3000 }
```

## 33.10 Inline CSS for HTML email; do not assume external stylesheets load.

> Why? [inline-email-styles](https://rails.rubystyle.guide/#inline-email-styles)
> — most clients strip remote stylesheets.
> **Suggestion.**

```erb
<%# bad %>
<link rel="stylesheet" href="<%= asset_url('email.css') %>">
<div class="header">Welcome</div>

<%# good %>
<div style="font-family: Helvetica, Arial, sans-serif; font-size: 16px;">
  Welcome
</div>
```

## 33.11 Subject lines and body copy go through I18n (`default_i18n_subject` / `t`).

> Why? Same locale discipline as views
> ([locale-texts](https://rails.rubystyle.guide/#locale-texts)).
> **Violation** when locale-text cops fire on literals.
>
> Enforced by: Rails/I18nLocaleTexts.

```ruby
# bad
mail(to: user.email, subject: 'Welcome to our app!')

# good
mail(to: user.email, subject: default_i18n_subject(name: user.name))
```

## 33.12 Do not mark mailer HTML as `html_safe` from user content.

> Why? Email HTML is still XSS / injection surface in clients that
> render it. Sanitize or escape.
> **Violation.**
>
> Enforced by: Rails/OutputSafety.

```erb
<%# bad %>
<%= raw @user.bio %>

<%# good %>
<%= simple_format(h(@user.bio)) %>
```

## 33.13 Pass instances or IDs consistently; avoid loading huge graphs in the mailer.

> Why? A mailer that `includes` half the database for one email blocks
> the worker. Preload in the caller or pass a presenter hash of
> primitives.
> **Suggestion.**

```ruby
# bad
def receipt(order_id)
  @order = Order.includes(lines: { product: :vendor }).find(order_id)
  mail(to: @order.user.email)
end

# good — caller preloads, or mailer loads a narrow scope
def receipt(order)
  @order = order
  @lines = order.lines.select(:sku, :quantity, :unit_price_cents)
  mail(to: order.user.email)
end
```

## 33.14 Preview mailers with `ActionMailer::Preview` classes under `test/mailers/previews`.

> Why? Previews catch layout bugs without sending. Keep preview data
> factories read-only.
> **Suggestion.**

```ruby
# test/mailers/previews/user_mailer_preview.rb
class UserMailerPreview < ActionMailer::Preview
  def welcome
    UserMailer.welcome(User.first)
  end
end
```

## 33.15 Use zone-aware times in mailer-rendered dates.

> Why? Receipts that show UTC for a local customer create support
> tickets.
> **Violation.**
>
> Enforced by: Rails/TimeZone.

```erb
<%# bad %>
<%= Time.now.strftime('%Y-%m-%d') %>

<%# good %>
<%= l(Time.current.to_date) %>
```

## 33.16 Use a local SMTP catcher in development (Mailcatcher, Mailhog, or Letter Opener).

> Why? [local-smtp](https://rails.rubystyle.guide/#local-smtp) keeps
> developers from accidentally hitting a real provider with fixture data
> while still exercising the full delivery path.
> **Suggestion.**

```ruby
# config/environments/development.rb
config.action_mailer.delivery_method = :smtp
config.action_mailer.smtp_settings = {
  address: 'localhost',
  port: 1025,
}
config.action_mailer.raise_delivery_errors = true
```

## 33.17 Prefer `I18n.t` / `I18n.l` short forms and shared locale files for formats.

> Why? [shared-localization](https://rails.rubystyle.guide/#shared-localization)
> and short I18n helpers keep date/currency formats out of mailer ERB.
> Put shared formats under `config/locales/` roots; keep mailer copy under
> the mailer namespace.
> **Violation** when short-form I18n cops fire.
>
> Enforced by: Rails/ShortI18n.

```ruby
# bad
I18n.translate('user_mailer.welcome.subject')
I18n.localize(Time.current.to_date)

# good
I18n.t('user_mailer.welcome.subject')
I18n.l(Time.current.to_date)
```
