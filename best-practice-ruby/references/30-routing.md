<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 30. Routing

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

Routes are the public URL API of the application. Prefer resourceful
routing, keep nesting shallow, name member/collection actions sparingly,
and avoid catch-all `match` routes that accept every verb.

Sources:
[routing](https://rails.rubystyle.guide/#routing),
[nested-routes](https://rails.rubystyle.guide/#nested-routes),
[shallow-routes](https://rails.rubystyle.guide/#shallow-routes),
[member-collection-routes](https://rails.rubystyle.guide/#member-collection-routes),
[many-member-collection-routes](https://rails.rubystyle.guide/#many-member-collection-routes),
[namespaced-routes](https://rails.rubystyle.guide/#namespaced-routes),
[no-match-routes](https://rails.rubystyle.guide/#no-match-routes),
[no-wild-routes](https://rails.rubystyle.guide/#no-wild-routes),
[user-friendly-urls](https://rails.rubystyle.guide/#user-friendly-urls),
and
[override-the-to_param-method-of-the-model](https://rails.rubystyle.guide/#override-the-to_param-method-of-the-model).

**Tool alignment:** `Rails/MatchRoute` is enabled and catches broad
`match` usage. Most routing taste rules are **Suggestion**.

## 30.1 Prefer resourceful routes over hand-drawn GET/POST maps.

> Why? [routing](https://rails.rubystyle.guide/#routing) — `resources`
> gives you path helpers, consistent verbs, and a controller shape
> reviewers already know.
> **Suggestion.**

```ruby
# bad
get 'orders', to: 'orders#index'
get 'orders/new', to: 'orders#new'
post 'orders', to: 'orders#create'
get 'orders/:id', to: 'orders#show'
patch 'orders/:id', to: 'orders#update'
delete 'orders/:id', to: 'orders#destroy'

# good
resources :orders
```

## 30.2 Limit nesting — one level deep in normal cases; use `shallow: true` when children have their own identity.

> Why? [nested-routes](https://rails.rubystyle.guide/#nested-routes) and
> [shallow-routes](https://rails.rubystyle.guide/#shallow-routes) —
> `/users/1/posts/2/comments/3/likes/4` is unusable. Shallow routes keep
> nested creates while exposing member actions at the top level.
> **Suggestion.**

```ruby
# bad
resources :users do
  resources :posts do
    resources :comments do
      resources :likes
    end
  end
end

# good
resources :users do
  resources :posts, shallow: true
end

resources :comments, only: %i[show edit update destroy]
```

## 30.3 Declare member and collection routes inside `member` / `collection` blocks.

> Why? [member-collection-routes](https://rails.rubystyle.guide/#member-collection-routes)
> keep path helpers predictable (`close_order_path` vs ad-hoc strings).
> **Suggestion.**

```ruby
# bad
get 'orders/:id/close', to: 'orders#close'
get 'orders/search', to: 'orders#search'

# good
resources :orders do
  member do
    post :close
  end

  collection do
    get :search
  end
end
```

## 30.4 If a resource accumulates many member/collection actions, extract a new resource or controller.

> Why? [many-member-collection-routes](https://rails.rubystyle.guide/#many-member-collection-routes)
> — a dozen member routes means the resource is really several resources.
> **Suggestion.**

```ruby
# bad
resources :accounts do
  member do
    post :suspend
    post :reinstate
    post :rotate_keys
    post : Imp_billing
    post :export_audit
  end
end

# good
resources :accounts do
  resource :suspension, only: %i[create destroy]
  resource :billing_profile, only: %i[show create update]
  resources :key_rotations, only: :create
  resources :audit_exports, only: :create
end
```

## 30.5 Namespace admin / API surfaces with `namespace` or `scope module:`.

> Why? [namespaced-routes](https://rails.rubystyle.guide/#namespaced-routes)
> mirror directory layout (`Admin::OrdersController`) and keep path
> helpers prefixed.
> **Suggestion.**

```ruby
# bad
get 'admin/orders', to: 'admin_orders#index'

# good
namespace :admin do
  resources :orders
end

# good — same module, custom path
scope module: :admin do
  resources :orders, path: 'backoffice/orders'
end
```

## 30.6 Do not use `match` without an explicit `via:` — prefer verb helpers.

> Why? [no-match-routes](https://rails.rubystyle.guide/#no-match-routes)
> — bare `match` accepts every HTTP verb, including ones you never
> tested.
> **Violation.**
>
> Enforced by: Rails/MatchRoute.

```ruby
# bad
match 'photos/:id' => 'photos#show'

# good
get 'photos/:id', to: 'photos#show'
match 'photos/:id', to: 'photos#show', via: :get
```

## 30.7 Avoid wildcard / glob routes except for deliberate front-end catch-alls.

> Why? [no-wild-routes](https://rails.rubystyle.guide/#no-wild-routes)
> — `*path` swallows mis-typed URLs and hides 404s. If you need an SPA
> fallback, put it last and constrain it.
> **Suggestion.**

```ruby
# bad
get '*path', to: 'home#index'

# good — last route, HTML only
get '*path', to: 'home#index', constraints: ->(req) { !req.xhr? && req.format.html? }
```

## 30.8 Restrict verbs and actions with `only` / `except` on resources you do not fully expose.

> Why? Extra routes are attack surface and documentation debt. If there
> is no `destroy`, do not route it.
> **Suggestion.**

```ruby
# bad
resources :sessions

# good
resources :sessions, only: %i[new create destroy]
```

## 30.9 Prefer readable slugs via `to_param` (or a slug column) over opaque-only URLs when users see the link.

> Why? [user-friendly-urls](https://rails.rubystyle.guide/#user-friendly-urls)
> and
> [override-the-to_param-method-of-the-model](https://rails.rubystyle.guide/#override-the-to_param-method-of-the-model)
> — `/posts/how-to-deploy` beats `/posts/4815162342` for shareable
> content. Keep `find` compatible (`friendly.find` or find-by-slug).
> **Suggestion.**

```ruby
# bad
# always /orders/12345 with no human context

# good
class Post < ApplicationRecord
  def to_param
    "#{id}-#{title.parameterize}"
  end
end

# finder must tolerate the suffix
Post.find(params[:id].to_i)
```

## 30.10 Draw engine / mount points explicitly and away from ambiguous root paths.

> Why? Mounted engines at `/` collide with app routes in confusing ways.
> Prefer `/admin`, `/letter_opener`, `/sidekiq` with auth constraints.
> **Suggestion.**

```ruby
# bad
mount Sidekiq::Web => '/'

# good
authenticate :user, ->(user) { user.admin? } do
  mount Sidekiq::Web => '/sidekiq'
end
```

## 30.11 Keep `root` singular and intentional.

> Why? Multiple competing "home" routes produce ambiguous helpers and
> redirect loops. One `root`, everything else named.
> **Suggestion.**

```ruby
# bad
root 'marketing#home'
root 'dashboard#show'

# good
root 'marketing#home'
get 'dashboard', to: 'dashboard#show', as: :dashboard
```

## 30.12 Put concerns for shared nested routing in `routes.rb` concerns, not copy-paste blocks.

> Why? Repeated `member` blocks drift. A `concern` keeps the shared
> shape DRY without inventing a DSL outside Rails.
> **Suggestion.**

```ruby
# bad — copy-pasted across three resources
resources :posts do
  member { post :publish }
end
resources :pages do
  member { post :publish }
end

# good
concern :publishable do
  member { post :publish }
end

resources :posts, concerns: :publishable
resources :pages, concerns: :publishable
```

## 30.13 Scope locale or account tenants with `scope` / `constraints`, not string prefixes in every path helper call.

> Why? URL structure for tenancy belongs in the router so helpers stay
> consistent (`account_order_path` with default URL options).
> **Suggestion.**

```ruby
# bad
get '/:account_id/orders', to: 'orders#index'

# good
scope '/:account_id', as: :account do
  resources :orders
end
```

## 30.14 Document non-resourceful routes next to why they cannot be resourceful.

> Why? One-off `get` routes are sometimes correct (OAuth callbacks,
> health checks). Require a comment so they are not mistaken for
> unfinished resource conversions.
> **Suggestion.**

```ruby
# bad
get 'oauth/callback', to: 'oauth#callback'

# good
# Provider redirects here; not a resource because the provider owns the URL.
get 'oauth/callback', to: 'oauth#callback'
```
