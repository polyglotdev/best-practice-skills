<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 29. Controllers & Strong Params

Canonical Rails source: [Rails Style Guide](https://github.com/rubocop/rails-style-guide) (deep links use the HTML mirror).

A controller translates HTTP into one domain call and translates the
result back into HTTP. When it grows a second responsibility — a query
builder, a policy tree, a multi-model write — extract it. Strong
parameters are the allow-list at the boundary; they are not optional
ceremony.

Sources:
[controllers](https://rails.rubystyle.guide/#controllers),
[skinny-controllers](https://rails.rubystyle.guide/#skinny-controllers),
[http-status-code-symbols](https://rails.rubystyle.guide/#http-status-code-symbols),
[lexically-scoped-action-filter](https://rails.rubystyle.guide/#lexically-scoped-action-filter),
[rendering](https://rails.rubystyle.guide/#rendering),
[inline-rendering](https://rails.rubystyle.guide/#inline-rendering),
and
[plain-text-rendering](https://rails.rubystyle.guide/#plain-text-rendering).

Service extraction is [Chapter 34](34-service-objects.md). Security
footguns (mass assignment, XSS) are
[Chapter 36](36-rails-security-and-footguns.md).

**Tool alignment:** `Rails/ApplicationController`, `Rails/HttpStatus`,
`Rails/LexicallyScopedActionFilter`, `Rails/RenderInline`,
`Rails/RenderPlainText`, `Rails/UnusedRenderContent`,
`Rails/ResponseParsedBody`, `Rails/OutputSafety`, and
`Rails/SafeNavigation` are enabled.

## 29.1 Keep controllers skinny — bind params, call one object, render.

> Why? [skinny-controllers](https://rails.rubystyle.guide/#skinny-controllers)
> are testable without the full request stack for every branch. Business
> rules in actions are business rules you will duplicate in jobs.
> **Suggestion.**

```ruby
# bad
class OrdersController < ApplicationController
  def create
    order = Order.new(order_params)
    order.total = order.lines.sum { |line| line.price * line.quantity }
    if order.total > current_user.credit_limit
      redirect_to store_path, alert: 'over limit'
      return
    end
    order.save!
    OrderMailer.receipt(order).deliver_later
    redirect_to order
  end
end

# good
class OrdersController < ApplicationController
  def create
    order = Orders::Place.new(user: current_user).call(order_params)
    redirect_to order
  rescue Orders::OverLimit => error
    redirect_to store_path, alert: error.message
  end
end
```

## 29.2 Inherit from `ApplicationController` (or your API base that does).

> Why? Shared auth, CSRF, and rescue_from live on the application base.
> **Violation.**
>
> Enforced by: Rails/ApplicationController.

```ruby
# bad
class HooksController < ActionController::Base
end

# good
class HooksController < ApplicationController
end
```

## 29.3 Use strong parameters — never `params` directly into `update` / `create`.

> Why? Mass assignment is still the classic Rails footgun. An allow-list
> per action (or shared private method) is the contract with the client.
> **Suggestion** (no dedicated "strong params" cop; treat as required
> review finding).

```ruby
# bad
def create
  User.create(params[:user])
end

def update
  @user.update(params.permit!)
end

# good
def create
  User.create!(user_params)
end

def update
  @user.update!(user_params)
end

private

def user_params
  params.require(:user).permit(:name, :email)
end
```

## 29.4 Prefer symbol status codes over numeric literals.

> Why? [http-status-code-symbols](https://rails.rubystyle.guide/#http-status-code-symbols)
> — `:not_found` reads; `404` is a magic number.
> **Violation.**
>
> Enforced by: Rails/HttpStatus.

```ruby
# bad
render json: { error: 'missing' }, status: 404
head 204

# good
render json: { error: 'missing' }, status: :not_found
head :no_content
```

## 29.5 Scope `before_action` filters to actions that exist in the class.

> Why? [lexically-scoped-action-filter](https://rails.rubystyle.guide/#lexically-scoped-action-filter)
> — `only: :export` on a controller that has no `export` action is a
> silent no-op after a rename.
> **Violation.**
>
> Enforced by: Rails/LexicallyScopedActionFilter.

```ruby
# bad
class ReportsController < ApplicationController
  before_action :authorize!, only: :export

  def show
  end
end

# good
class ReportsController < ApplicationController
  before_action :authorize!, only: :show

  def show
  end
end
```

## 29.6 Prefer template / JSON rendering over `render inline:`.

> Why? [inline-rendering](https://rails.rubystyle.guide/#inline-rendering)
> hides view code inside the controller and skips the usual template
> lookup / caching path.
> **Violation.**
>
> Enforced by: Rails/RenderInline.

```ruby
# bad
render inline: '<p><%= @user.name %></p>'

# good
render :show
```

## 29.7 Use `render plain:` for text, not `render text:`.

> Why? [plain-text-rendering](https://rails.rubystyle.guide/#plain-text-rendering)
> — `text:` is legacy; `plain:` is the supported API.
> **Violation.**
>
> Enforced by: Rails/RenderPlainText.

```ruby
# bad
render text: 'ok'

# good
render plain: 'ok'
```

## 29.8 Do not pass unused locals / content to `render`.

> Why? Dead render options are copy-paste residue that confuse readers
> about what the template consumes.
> **Violation.**
>
> Enforced by: Rails/UnusedRenderContent.

```ruby
# bad
render :show, plain: 'ignored when template renders'

# good
render :show
```

## 29.9 Find records with a clear 404 path — `find` or explicit rescue.

> Why? `find_by` returning `nil` followed by a NoMethodError becomes a
> 500. Prefer `Model.find(params[:id])` (404 via RecordNotFound) or a
> deliberate not-found response.
> **Suggestion.**

```ruby
# bad
def show
  @order = Order.find_by(id: params[:id])
  render json: @order # 500 if nil
end

# good
def show
  @order = Order.find(params[:id])
  render json: @order
end
```

## 29.10 Keep `respond_to` / format branches shallow; extract serializers for JSON shapes.

> Why? Fat `respond_to` blocks become a second view layer inside the
> controller. One format per action, or a serializer object, stays
> readable.
> **Suggestion.**

```ruby
# bad
def show
  respond_to do |format|
    format.html
    format.json do
      render json: {
        id: @order.id,
        total: @order.total_cents,
        lines: @order.lines.map { |line| { sku: line.sku, qty: line.quantity } },
      }
    end
  end
end

# good
def show
  respond_to do |format|
    format.html
    format.json { render json: OrderSerializer.new(@order) }
  end
end
```

## 29.11 Prefer bang persistence in create/update when failure should be exceptional.

> Why? Coupled with [save-bang](https://rails.rubystyle.guide/#save-bang)
> and `rescue_from ActiveRecord::RecordInvalid` (or form re-render with
> non-bang). Do not ignore boolean returns.
> **Violation** when returns are ignored.
>
> Enforced by: Rails/SaveBang.

```ruby
# bad
def create
  @user = User.new(user_params)
  @user.save
  redirect_to @user
end

# good — form re-render path
def create
  @user = User.new(user_params)
  if @user.save
    redirect_to @user
  else
    render :new, status: :unprocessable_entity
  end
end
```

## 29.12 Never mark strings `html_safe` / `raw` in controllers.

> Why? XSS belongs nowhere near the request layer. If you must emit HTML,
> build it in a sanitized helper or template. See
> [Chapter 36](36-rails-security-and-footguns.md).
> **Violation.**
>
> Enforced by: Rails/OutputSafety.

```ruby
# bad
render html: params[:q].html_safe

# good
render plain: params[:q].to_s
```

## 29.13 Prefer safe navigation for optional associations in controller-facing reads — but not for required ones.

> Why? `Rails/SafeNavigation` encourages `&.` where `try` was used.
> Required records should still use `find` / bang methods so missing data
> fails loudly.
> **Violation** for `try` → `&.` rewrites the cop owns.
>
> Enforced by: Rails/SafeNavigation.

```ruby
# bad
account.try(:owner).try(:email)

# good
account&.owner&.email
```

## 29.14 Do not parse response bodies with ad-hoc JSON in controller tests incorrectly — use the Rails helpers.

> Why? `Rails/ResponseParsedBody` pushes `response.parsed_body` over
> `JSON.parse(response.body)` in request specs.
> **Violation** in test code the cop covers.
>
> Enforced by: Rails/ResponseParsedBody.

```ruby
# bad
json = JSON.parse(response.body)

# good
json = response.parsed_body
```

## 29.15 Permit nested structures explicitly — arrays and hashes named field by field.

> Why? `permit(tags: [])` and `permit(address: [:city, :zip])` document
> shape. `permit!` and blanket scalar permits on nested keys reopen mass
> assignment.
> **Suggestion.**

```ruby
# bad
params.require(:order).permit!

# good
params.require(:order).permit(
  :note,
  line_items_attributes: [%i[sku quantity unit_price_cents]],
  shipping_address: %i[line1 city postal_code country],
)
```
