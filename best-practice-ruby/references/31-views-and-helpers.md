<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 31. Views & Helpers

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

Views present state. Helpers format for presentation. Neither place
belongs to Active Record writes, HTTP redirects, or policy decisions.
Keep templates free of model queries, keep partials free of controller
instance variables, and push copy through I18n.

Sources:
[views](https://rails.rubystyle.guide/#views),
[partials](https://rails.rubystyle.guide/#partials),
[no-direct-model-view](https://rails.rubystyle.guide/#no-direct-model-view),
[no-instance-variables-in-partials](https://rails.rubystyle.guide/#no-instance-variables-in-partials),
[shared-instance-variables](https://rails.rubystyle.guide/#shared-instance-variables),
[no-complex-view-formatting](https://rails.rubystyle.guide/#no-complex-view-formatting),
[lazy-lookup](https://rails.rubystyle.guide/#lazy-lookup),
[short-i18n](https://rails.rubystyle.guide/#short-i18n),
[locale-texts](https://rails.rubystyle.guide/#locale-texts),
[translated-labels](https://rails.rubystyle.guide/#translated-labels),
[organize-locale-files](https://rails.rubystyle.guide/#organize-locale-files),
[avoid-interpolation](https://rails.rubystyle.guide/#avoid-interpolation),
and
[dot-separated-keys](https://rails.rubystyle.guide/#dot-separated-keys).

**Tool alignment:** `Rails/HelperInstanceVariable`,
`Rails/OutputSafety`, `Rails/I18nLazyLookup`, `Rails/I18nLocaleTexts`,
`Rails/I18nLocaleAssignment`, `Rails/ShortI18n`, `Rails/LinkToBlank`,
and `Rails/ContentTag` are enabled.

## 31.1 Never query Active Record directly from templates.

> Why? [no-direct-model-view](https://rails.rubystyle.guide/#no-direct-model-view)
> — a view that calls `User.where(...)` hides N+1s and makes caching
> impossible to reason about. Controllers / presenters pass data in.
> **Suggestion.**

```erb
<%# bad %>
<% User.active.each do |user| %>
  <%= user.name %>
<% end %>

<%# good — @users assigned in the controller %>
<% @users.each do |user| %>
  <%= user.name %>
<% end %>
```

## 31.2 Pass locals into partials; do not rely on controller instance variables inside them.

> Why? [no-instance-variables-in-partials](https://rails.rubystyle.guide/#no-instance-variables-in-partials)
> and
> [shared-instance-variables](https://rails.rubystyle.guide/#shared-instance-variables)
> — partials that read `@order` break when reused from a mailer or job
> preview.
> **Suggestion.**

```erb
<%# bad — partials/_line.html.erb %>
<%= @order.currency %>
<%= line.sku %>

<%# good %>
<%= order.currency %>
<%= line.sku %>
```

```ruby
# caller
render 'line', order: @order, line: line
```

## 31.3 Do not use instance variables inside helper modules.

> Why? Helpers should be pure functions of their arguments. Reading
> `@user` couples the helper to a single controller shape.
> **Violation.**
>
> Enforced by: Rails/HelperInstanceVariable.

```ruby
# bad
module UsersHelper
  def display_name
    @user.name.presence || @user.email
  end
end

# good
module UsersHelper
  def display_name(user)
    user.name.presence || user.email
  end
end
```

## 31.4 Move non-trivial formatting out of ERB into helpers or presenters.

> Why? [no-complex-view-formatting](https://rails.rubystyle.guide/#no-complex-view-formatting)
> — multi-branch money / date / state formatting in ERB is untestable
> without a render.
> **Suggestion.**

```erb
<%# bad %>
<% if order.state == 'paid' && order.refunded_at.nil? %>
  <span class="ok"><%= number_to_currency(order.total_cents / 100.0) %></span>
<% elsif order.refunded_at.present? %>
  <span class="muted">Refunded <%= l(order.refunded_at.to_date) %></span>
<% end %>

<%# good %>
<%= order_status_label(order) %>
```

## 31.5 Prefer I18n for user-visible copy; do not hardcode sentence strings in views.

> Why? [locale-texts](https://rails.rubystyle.guide/#locale-texts) —
> English literals in ERB block translation and A/B copy changes.
> **Violation** for the patterns `Rails/I18nLocaleTexts` detects.
>
> Enforced by: Rails/I18nLocaleTexts.

```erb
<%# bad %>
<h1>Your orders</h1>
<p>No orders yet.</p>

<%# good %>
<h1><%= t('.title') %></h1>
<p><%= t('.empty') %></p>
```

## 31.6 Use lazy lookup (`t('.key')`) inside controllers / views that own the key tree.

> Why? [lazy-lookup](https://rails.rubystyle.guide/#lazy-lookup) scopes
> keys to the current view path so renames stay local.
> **Violation.**
>
> Enforced by: Rails/I18nLazyLookup.

```ruby
# bad — in app/views/orders/index.html.erb context
t('orders.index.title')

# good
t('.title')
```

## 31.7 Prefer short I18n helpers (`t`, `l`) over long forms.

> Why? [short-i18n](https://rails.rubystyle.guide/#short-i18n) is the
> community default in Rails views.
> **Violation.**
>
> Enforced by: Rails/ShortI18n.

```erb
<%# bad %>
<%= I18n.t('orders.show.title') %>
<%= I18n.l(order.created_at.to_date) %>

<%# good %>
<%= t('orders.show.title') %>
<%= l(order.created_at.to_date) %>
```

## 31.8 Translate form labels and attribute names through Rails I18n, not literals.

> Why? [translated-labels](https://rails.rubystyle.guide/#translated-labels)
> — `activerecord.attributes.*` keeps forms and errors consistent.
> **Suggestion.**

```erb
<%# bad %>
<%= form.label :email, 'Email address' %>

<%# good %>
<%= form.label :email %>
```

```yaml
# config/locales/en.yml
en:
  activerecord:
    attributes:
      user:
        email: Email address
```

## 31.9 Organize locale files by domain; use dot-separated keys.

> Why? [organize-locale-files](https://rails.rubystyle.guide/#organize-locale-files)
> and [dot-separated-keys](https://rails.rubystyle.guide/#dot-separated-keys)
> — one giant `en.yml` becomes unmergeable.
> **Suggestion.**

```yaml
# bad — everything in config/locales/en.yml

# good
# config/locales/orders.en.yml
en:
  orders:
    index:
      title: Your orders
      empty: No orders yet.
```

## 31.10 Avoid string interpolation inside `t()` — pass variables.

> Why? [avoid-interpolation](https://rails.rubystyle.guide/#avoid-interpolation)
> — interpolated English cannot be reordered by translators.
> **Suggestion.**

```ruby
# bad
t('greetings.hello') + ", #{user.name}!"

# good
t('greetings.hello', name: user.name)
# en: "Hello, %{name}!"
```

## 31.11 Never assign `I18n.locale=` without restoring it (prefer `I18n.with_locale`).

> Why? Locale leaks across requests in threaded servers when you set a
> global and forget to reset.
> **Violation.**
>
> Enforced by: Rails/I18nLocaleAssignment.

```ruby
# bad
I18n.locale = user.locale
render :show

# good
I18n.with_locale(user.locale) do
  render :show
end
```

## 31.12 When opening links in a new tab, set `rel: 'noopener'`.

> Why? `target: '_blank'` without `noopener` lets the new page touch
> `window.opener` (tabnabbing).
> **Violation.**
>
> Enforced by: Rails/LinkToBlank.

```erb
<%# bad %>
<%= link_to 'Docs', docs_url, target: '_blank' %>

<%# good %>
<%= link_to 'Docs', docs_url, target: '_blank', rel: 'noopener' %>
```

## 31.13 Prefer `tag` / `content_tag` consistently; do not mark unsafe HTML safe.

> Why? `Rails/ContentTag` modernizes helpers; `Rails/OutputSafety`
> blocks `html_safe` / `raw` laundering of untrusted strings. See
> [Chapter 36](36-rails-security-and-footguns.md).
> **Violation.**
>
> Enforced by: Rails/ContentTag, Rails/OutputSafety.

```ruby
# bad
"<p>#{user.name}</p>".html_safe
raw(params[:html])

# good
tag.p(user.name)
sanitize(user.bio)
```

## 31.14 Keep view models / presenters for multi-method presentation state.

> Why? When a template needs five derived fields, a presenter object
> (PORO) beats a kitchen-sink helper module. Helpers stay for one-off
> formatting.
> **Suggestion.**

```ruby
# bad — Helpers::OrdersHelper grows 40 methods

# good
class OrderPresenter
  def initialize(order)
    @order = order
  end

  def status_label
    # ...
  end

  def total
    # ...
  end
end
```

## 31.15 Prefer partial collections and proper DOM IDs over manual loops with hand-built ids.

> Why? [partials](https://rails.rubystyle.guide/#partials) —
> `render @lines` uses conventions, cache keys, and `dom_id`.
> **Suggestion.**

```erb
<%# bad %>
<% @lines.each do |line| %>
  <div id="line-<%= line.id %>">
    <%= line.sku %>
  </div>
<% end %>

<%# good %>
<%= render @lines %>
```
