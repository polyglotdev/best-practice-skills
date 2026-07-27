<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 10. Metaprogramming Discipline

Ruby makes runtime definition easy; most codebases pay for that ease with
opaque call stacks and APIs that cannot be grepped. This chapter bans casual
`method_missing`, `eval`, and string-form `class_eval` / `module_eval` /
`instance_eval`, and steers toward `define_method`, careful `Module#prepend`,
and ordinary methods. Prefer writing the method when three lines of
metaprogramming would "save" ten lines of clarity.

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[metaprogramming](https://rubystyle.guide/#metaprogramming),
[no method_missing](https://rubystyle.guide/#no-method-missing),
[no needless metaprogramming](https://rubystyle.guide/#no-needless-metaprogramming),
[class_eval and define_method](https://rubystyle.guide/#class-eval-define_method),
[class_eval supply location](https://rubystyle.guide/#class-eval-supply-location),
[block class_eval](https://rubystyle.guide/#block-class-eval),
[eval comment docs](https://rubystyle.guide/#eval-comment-docs),
[prefer public_send](https://rubystyle.guide/#prefer-public-send),
[prefer __send__](https://rubystyle.guide/#prefer-__send__),
[alias method](https://rubystyle.guide/#alias-method),
[no monkey-patching](https://rubystyle.guide/#no-monkey-patching),
[no class vars](https://rubystyle.guide/#no-class-vars), and
[no DSL decorating](https://rubystyle.guide/#no-dsl-decorating).

**Tool alignment:** `Security/Eval`, `Style/EvalWithLocation`,
`Style/MissingRespondToMissing`, `Style/Alias`, `Style/ClassVars`,
`Lint/NestedMethodDefinition`, and related cops are effectively enabled.
Rules those cops catch are **Violation**; the rest are **Suggestion**.

## 10.1 Do not use `method_missing` for ordinary API surface; define the methods explicitly or with `define_method`.

> Why? The guide's
> [no method_missing](https://rubystyle.guide/#no-method-missing)
> rule treats `method_missing` as a last resort. It breaks `respond_to?`
> unless you also implement `respond_to_missing?`, hides typos, and makes
> editors and grep useless. Three explicit methods beat a clever dispatcher.
> **Suggestion.**

```ruby
# bad
class Config
  def method_missing(name, *args)
    if name.end_with?('=')
      data[name.to_s.chomp('=')] = args.first
    else
      data[name.to_s]
    end
  end
end

# good
class Config
  def host
    data['host']
  end

  def host=(value)
    data['host'] = value
  end

  def port
    data['port']
  end
end
```

## 10.2 If you must implement `method_missing`, always implement `respond_to_missing?` for the same names.

> Why? Without `respond_to_missing?`, `respond_to?` lies and
> `method(:name)` fails even when `method_missing` would handle the call.
> RuboCop's `Style/MissingRespondToMissing` catches the incomplete pair.
> Still prefer not having `method_missing` at all (see 10.1). **Violation.**
>
> Enforced by: Style/MissingRespondToMissing.

```ruby
# bad
class DynamicFinder
  def method_missing(name, *args, &block)
    return find_by(name, args.first) if name.start_with?('find_by_')

    super
  end
end

# good — complete pair, and still consider define_method instead
class DynamicFinder
  def method_missing(name, *args, &block)
    return find_by(name, args.first) if name.start_with?('find_by_')

    super
  end

  def respond_to_missing?(name, include_private = false)
    name.start_with?('find_by_') || super
  end
end
```

## 10.3 Prefer `define_method` over string-eval forms of `class_eval` / `module_eval` / `instance_eval`.

> Why? The guide's
> [class_eval and define_method](https://rubystyle.guide/#class-eval-define_method)
> and
> [block class_eval](https://rubystyle.guide/#block-class-eval)
> rules prefer block forms and `define_method` so you get real closures,
> normal syntax highlighting, and no injection surface. String eval is for
> code generation tools with locked-down input — not application code.
> **Suggestion.**

```ruby
# bad
%w[create update destroy].each do |action|
  class_eval <<-RUBY, __FILE__, __LINE__ + 1
    def #{action}!
      run_action(:#{action})
    end
  RUBY
end

# good
%i[create update destroy].each do |action|
  define_method(:"#{action}!") do
    run_action(action)
  end
end
```

## 10.4 Never pass untrusted or request-derived strings to `eval`, `instance_eval`, `class_eval`, `module_eval`, or `binding.eval`.

> Why? `Security/Eval` exists because string evaluation is remote code
> execution with extra steps. Template languages, serializers, and
> `Kernel#eval` on params are classic vulnerability shapes. If you need
> dynamic behaviour, use a whitelist of symbols dispatched with
> `public_send`, or `define_method` at load time. **Violation.**
>
> Enforced by: Security/Eval.

```ruby
# bad
expr = params[:formula]
result = eval(expr)

# good
ALLOWED = {
  'sum' => ->(values) { values.sum },
  'max' => ->(values) { values.max }
}.freeze

op = ALLOWED.fetch(params[:op])
result = op.call(values)
```

## 10.5 When string eval is unavoidable in a generator, pass `__FILE__` and `__LINE__` (or the source path) so backtraces point at real locations.

> Why? The guide's
> [class_eval supply location](https://rubystyle.guide/#class-eval-supply-location)
> and
> [eval comment docs](https://rubystyle.guide/#eval-comment-docs)
> rules, plus `Style/EvalWithLocation`, keep stack traces honest. Opaque
> `(eval)` frames waste hours in production incidents. **Violation.**
>
> Enforced by: Style/EvalWithLocation.

```ruby
# bad
class_eval('def generated; 1; end')

# good
class_eval('def generated; 1; end', __FILE__, __LINE__)
```

## 10.6 Do not reach for metaprogramming when a plain loop, hash, or ordinary method list would do.

> Why? The guide's
> [no needless metaprogramming](https://rubystyle.guide/#no-needless-metaprogramming)
> rule is the chapter's north star. Dynamic definition is justified when
> the set of methods is large *and* mechanical (hundreds of attribute
> readers from a schema). It is not justified for four similar methods
> a junior engineer will need to breakpoint tomorrow. **Suggestion.**

```ruby
# bad — metaprogramming for two methods
%i[start finish].each do |edge|
  define_method(edge) { events.fetch(edge) }
end

# good
def start
  events.fetch(:start)
end

def finish
  events.fetch(:finish)
end
```

## 10.7 Prefer `public_send` for dynamic calls with caller-controlled names; use `__send__` only when you intentionally bypass visibility.

> Why? The guide's
> [prefer public_send](https://rubystyle.guide/#prefer-public-send)
> and
> [prefer __send__](https://rubystyle.guide/#prefer-__send__)
> rules split the two needs. `send` calls private methods and turns a
> typo'd or attacker-controlled name into a privilege escalation.
> `public_send` respects visibility; `__send__` is the explicit escape
> hatch when a receiver might define its own `#send`. **Suggestion.**

```ruby
# bad — params can hit private methods
action = params[:action]
order.send(action)

# good
action = params[:action]
order.public_send(action) if order.respond_to?(action)
```

## 10.8 Prefer `alias_method` over the `alias` keyword for method aliases in modern code.

> Why? The guide's
> [alias method](https://rubystyle.guide/#alias-method)
> section and `Style/Alias` prefer `alias_method` because it is a method
> (works with expressions and metaprogramming) rather than a keyword that
> only accepts bare names. Keep aliases rare — rename call sites instead
> when you control them. **Violation.**
>
> Enforced by: Style/Alias.

```ruby
# bad
alias old_run run

# good
alias_method :old_run, :run
```

## 10.9 Prefer `Module#prepend` over alias-method chains when wrapping an existing method.

> Why? Alias chains (`alias_method :foo_without_timing, :foo`) mutate
> method tables in order-dependent ways and stack poorly across gems.
> `prepend` gives a clear `super` path and composes. Document why the
> wrapper must run before the original (see chapter 9). **Suggestion.**

```ruby
# bad — alias method chain
class Client
  alias_method :request_without_logging, :request

  def request(*args)
    logger.info('request')
    request_without_logging(*args)
  end
end

# good
module RequestLogging
  def request(*args)
    logger.info('request')
    super
  end
end

class Client
  prepend RequestLogging
end
```

## 10.10 Do not use class variables (`@@foo`) for shared state; prefer class instance variables or a dedicated object.

> Why? The guide's
> [no class vars](https://rubystyle.guide/#no-class-vars)
> rule and `Style/ClassVars` reject `@@` because subclasses share and
> stomp the same storage in surprising ways. Use `@foo` on the singleton
> class, `class_attribute` in Rails when inheritance is intentional, or an
> explicit registry object. **Violation.**
>
> Enforced by: Style/ClassVars.

```ruby
# bad
class Driver
  @@registry = {}

  def self.register(name, klass)
    @@registry[name] = klass
  end
end

# good
class Driver
  @registry = {}

  class << self
    attr_reader :registry

    def register(name, klass)
      @registry[name] = klass
    end
  end
end
```

## 10.11 Do not define methods inside other methods.

> Why? Nested `def` creates a new method on the receiver each call and
> confuses readers who expect a closure. `Lint/NestedMethodDefinition`
> flags it. Use a lambda, a private method, or `define_method` at load
> time. **Violation.**
>
> Enforced by: Lint/NestedMethodDefinition.

```ruby
# bad
def build_parser
  def parse(text)
    JSON.parse(text)
  end
end

# good
def build_parser
  ->(text) { JSON.parse(text) }
end

def parse(text)
  JSON.parse(text)
end
```

## 10.12 Avoid decorating core or library objects with singleton methods at runtime for DSLs.

> Why? The guide's
> [no DSL decorating](https://rubystyle.guide/#no-dsl-decorating)
> rule warns that `def obj.helper` and `obj.extend(Mod)` on shared objects
> create process-global behaviour that tests cannot isolate. Prefer plain
> methods on your own types, or block DSLs that yield a builder object you
> own. **Suggestion.**

```ruby
# bad
def configure(app)
  def app.shout(msg)
    warn msg.upcase
  end
end

# good
class AppConfigurator
  def initialize(app)
    @app = app
  end

  def shout(msg)
    warn msg.upcase
  end
end

def configure(app)
  yield AppConfigurator.new(app)
end
```

## 10.13 Prefer constants, hashes, or `Data.define` tables over `const_set` / `remove_const` in application code.

> Why? Runtime constant mutation breaks code loaders, reloaders, and
> readers who treat constants as immutable. Generate classes at boot in a
> single registry if you must, and freeze the registry. Hot-path
> `const_set` is a design smell. **Suggestion.**

```ruby
# bad
statuses.each do |name|
  Object.const_set(name.capitalize, Class.new(Status))
end

# good
STATUSES = {
  'open' => Class.new(Status),
  'closed' => Class.new(Status)
}.freeze
```

## 10.14 Prefer `define_singleton_method` over `instance_eval` / `class << obj` blocks when adding one method to one object.

> Why? A single `define_singleton_method` states intent; an `instance_eval`
> block is a scope gate that invites multi-method decoration and hidden
> instance variables on objects you do not own. **Suggestion.**

```ruby
# bad
tracker = Object.new
tracker.instance_eval do
  def track(event)
    events << event
  end
end

# good
tracker = Object.new
tracker.define_singleton_method(:track) do |event|
  events << event
end
```

## 10.15 Keep metaprogramming at load time; do not define methods inside request or job execution paths.

> Why? Defining methods per request races under threads, inflates method
> caches, and turns a traffic spike into CPU spent in the definition VM.
> Compute tables and `define_method` during boot, Zeitwerk load, or a
> single initializer. Per-call behaviour belongs in data, not new methods.
> **Suggestion.**

```ruby
# bad — defines a method on every call
def handler_for(name)
  define_singleton_method(name) { perform(name) }
  public_send(name)
end

# good — dispatch table built once
HANDLERS = {
  'welcome' => -> { perform(:welcome) },
  'farewell' => -> { perform(:farewell) }
}.freeze

def handler_for(name)
  HANDLERS.fetch(name).call
end
```
