<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 11. Exceptions & Errors

Exceptions signal failure that the current stack frame cannot usefully
continue past. This chapter covers raising specific classes with messages,
rescue ordering, avoiding bare and `Exception` rescues, preferring `raise`
over `fail`, and keeping exceptions out of ordinary control flow. Result
objects and monadic error types are out of scope; the default Ruby style
is raise/rescue with narrow classes.

The rules draw on the [Ruby Style Guide](https://rubystyle.guide/) sections
[exceptions](https://rubystyle.guide/#exceptions),
[no blind rescues](https://rubystyle.guide/#no-blind-rescues),
[prefer raise over fail](https://rubystyle.guide/#prefer-raise-over-fail),
[standard exceptions](https://rubystyle.guide/#standard-exceptions),
[don't hide exceptions](https://rubystyle.guide/#dont-hide-exceptions),
[no exceptional flows](https://rubystyle.guide/#no-exceptional-flows),
[no rescue modifiers](https://rubystyle.guide/#no-rescue-modifiers),
[exception class messages](https://rubystyle.guide/#exception-class-messages),
[exception ordering](https://rubystyle.guide/#exception-ordering),
[no explicit RuntimeError](https://rubystyle.guide/#no-explicit-runtimeerror),
[begin implicit](https://rubystyle.guide/#begin-implicit), and
[no return ensure](https://rubystyle.guide/#no-return-ensure).

**Tool alignment:** `Lint/RescueException`, `Lint/SuppressedException`,
`Lint/ShadowedException`, `Lint/InheritException`, `Lint/RaiseException`,
`Lint/EnsureReturn`, `Style/SignalException`, `Style/RescueModifier`,
`Style/RescueStandardError`, `Style/RaiseArgs`, `Style/RedundantException`,
`Naming/RescuedExceptionsVariableName`, and related cops are effectively
enabled. Rules those cops catch are **Violation**; the rest are
**Suggestion**.

## 11.1 Prefer `raise` over `fail` for raising exceptions.

> Why? The guide's
> [prefer raise over fail](https://rubystyle.guide/#prefer-raise-over-fail)
> rule and `Style/SignalException` standardize on `raise`. `fail` is an
> alias that reads like a soft assertion and splits a codebase for no
> gain. **Violation.**
>
> Enforced by: Style/SignalException.

```ruby
# bad
fail 'missing config' unless config

# good
raise 'missing config' unless config
```

## 11.2 Do not rescue `Exception`; rescue `StandardError` or a more specific subclass.

> Why? The guide's
> [no blind rescues](https://rubystyle.guide/#no-blind-rescues)
> rule and `Lint/RescueException` exist because `Exception` includes
> `NoMemoryError`, `SignalException`, `SystemExit`, and
> `Interrupt`. Swallowing those breaks process shutdown and Ctrl-C.
> Bare `rescue` already means `StandardError` — name a tighter class when
> you can. **Violation.**
>
> Enforced by: Lint/RescueException.

```ruby
# bad
begin
  risky_call
rescue Exception => e
  logger.error(e)
end

# good
begin
  risky_call
rescue IOError => e
  logger.error(e)
end
```

## 11.3 Prefer a specific exception class over rescuing the entire `StandardError` hierarchy.

> Why? Broad rescues hide programmer mistakes (`NoMethodError`,
> `ArgumentError`, `NameError` from typos) inside "retry later" handlers.
> Catch the errors the callee documents (`Timeout::Error`,
> `JSON::ParserError`, `Errno::ENOENT`). When you truly intend to catch
> every `StandardError`, prefer bare `rescue` over the redundant
> `rescue StandardError` spelling — that redundancy is what
> `Style/RescueStandardError` flags. **Suggestion** for choosing a narrow
> class; the redundant spelling is a **Violation.**
>
> Enforced by: Style/RescueStandardError.

```ruby
# bad — redundant StandardError spelling, and far too broad for JSON
begin
  JSON.parse(payload)
rescue StandardError
  {}
end

# good — narrow class
begin
  JSON.parse(payload)
rescue JSON::ParserError
  {}
end

# good — intentional broad catch uses bare rescue
begin
  maybe_raise
rescue => e
  logger.error(e)
  raise
end
```
## 11.4 Do not use rescue as a modifier (`do_something rescue nil`).

> Why? The guide's
> [no rescue modifiers](https://rubystyle.guide/#no-rescue-modifiers)
> rule and `Style/RescueModifier` ban one-line rescues because they hide
> the failure class and encourage `rescue nil`. Expand to a
> `begin`/`rescue` (or implicit-begin method body) that names the class.
> **Violation.**
>
> Enforced by: Style/RescueModifier.

```ruby
# bad
value = Integer(input) rescue nil

# good
begin
  value = Integer(input)
rescue ArgumentError
  value = nil
end
```

## 11.5 Prefer an implicit `begin` on a whole method body over a redundant `begin`/`end` wrapper.

> Why? The guide's
> [begin implicit](https://rubystyle.guide/#begin-implicit)
> rule and `Style/RedundantBegin` remove noise when the method's only job
> is the protected call plus handlers. Keep an explicit `begin` when only
> part of the method should be rescued. **Violation.**
>
> Enforced by: Style/RedundantBegin.

```ruby
# bad
def load_config
  begin
    YAML.load_file(path)
  rescue Errno::ENOENT
    {}
  end
end

# good
def load_config
  YAML.load_file(path)
rescue Errno::ENOENT
  {}
end
```

## 11.6 Order rescue clauses from most specific to least specific so earlier handlers are not shadowed.

> Why? The guide's
> [exception ordering](https://rubystyle.guide/#exception-ordering)
> rule and `Lint/ShadowedException` catch superclass-before-subclass
> lists that never run. Put `JSON::ParserError` before `StandardError`,
> never the reverse. **Violation.**
>
> Enforced by: Lint/ShadowedException.

```ruby
# bad — ParserError branch is unreachable
begin
  JSON.parse(body)
rescue StandardError => e
  handle_generic(e)
rescue JSON::ParserError => e
  handle_parse(e)
end

# good
begin
  JSON.parse(body)
rescue JSON::ParserError => e
  handle_parse(e)
rescue StandardError => e
  handle_generic(e)
end
```

## 11.7 Prefer `raise SomeError, 'message'` (or `raise SomeError.new('message')` consistently) and avoid empty raises without context.

> Why? The guide's
> [exception class messages](https://rubystyle.guide/#exception-class-messages)
> rule and `Style/RaiseArgs` keep construction consistent. A message that
> names the bad value saves a reproduction. Prefer the two-argument form
> `raise Class, message` unless you need a custom constructor.
> **Violation.**
>
> Enforced by: Style/RaiseArgs.

```ruby
# bad
raise ArgumentError.new

# good
raise ArgumentError, "id must be positive, got #{id.inspect}"
```

## 11.8 Prefer standard library exception classes over inventing synonyms for the same meaning.

> Why? The guide's
> [standard exceptions](https://rubystyle.guide/#standard-exceptions)
> rule keeps callers on vocabulary they already know:
> `ArgumentError` for bad caller input, `RuntimeError` only for generic
> failures, `KeyError` / `IndexError` for missing entries,
> `NotImplementedError` for abstract stubs. Custom classes are for domain
> failures callers must distinguish. **Suggestion.**

```ruby
# bad
class BadIdError < StandardError; end
raise BadIdError, 'id blank' if id.nil?

# good
raise ArgumentError, 'id must be present' if id.nil?
```

## 11.9 Prefer `raise 'message'` over `raise RuntimeError, 'message'` for generic failures.

> Why? The guide's
> [no explicit RuntimeError](https://rubystyle.guide/#no-explicit-runtimeerror)
> rule and `Style/RedundantException` treat bare `raise 'msg'` as already
> a `RuntimeError`. Spelling the class adds noise without information.
> When the failure is not generic, pick a better class instead.
> **Violation.**
>
> Enforced by: Style/RedundantException.

```ruby
# bad
raise RuntimeError, 'should never happen'

# good
raise 'should never happen'
```

## 11.10 Do not use exceptions for ordinary, expected control flow.

> Why? The guide's
> [no exceptional flows](https://rubystyle.guide/#no-exceptional-flows)
> rule rejects `raise StopIteration`-style loops and "not found" raises
> that callers always rescue. Expected absences return `nil`, use
> `find_by`, or return a Result — reserve exceptions for broken
> invariants and truly unexpected I/O. **Suggestion.**

```ruby
# bad
def find_user!(id)
  user = users[id]
  raise NotFound if user.nil?

  user
end

users.map { |id| find_user!(id) rescue nil }

# good
def find_user(id)
  users[id]
end

users.filter_map { |id| find_user(id) }
```

## 11.11 Do not swallow exceptions without logging, re-raising, or intentionally documenting why silence is safe.

> Why? The guide's
> [don't hide exceptions](https://rubystyle.guide/#dont-hide-exceptions)
> rule and `Lint/SuppressedException` flag empty rescue bodies. Silence is
> sometimes correct (optional cache parse) but must be obvious — a comment
> or an explicit metric. **Violation.**
>
> Enforced by: Lint/SuppressedException.

```ruby
# bad
begin
  cache.write(key, value)
rescue Redis::BaseError
end

# good
begin
  cache.write(key, value)
rescue Redis::BaseError => e
  logger.warn("cache write failed: #{e.class}: #{e.message}")
end
```

## 11.12 Name the rescued exception variable `e` (or the project's configured name), not a one-off synonym per file.

> Why? `Naming/RescuedExceptionsVariableName` keeps rescue clauses
> scannable. `err`, `ex`, `exception`, and `error` rotate through code
> reviews for no semantic gain. Use `_e` or omit the variable when unused.
> **Violation.**
>
> Enforced by: Naming/RescuedExceptionsVariableName.

```ruby
# bad
rescue IOError => io_fail
  logger.error(io_fail)

# good
rescue IOError => e
  logger.error(e)
```

## 11.13 Inherit application exceptions from `StandardError`, not from `Exception`.

> Why? `Lint/InheritException` and library convention keep custom errors
> inside the default rescue band. Inheriting from `Exception` forces every
> caller into the dangerous broad rescue. For frameworks that require a
> base (`ApplicationError < StandardError`), put domain errors under that
> base. **Violation.**
>
> Enforced by: Lint/InheritException.

```ruby
# bad
class PaymentError < Exception; end

# good
class PaymentError < StandardError; end
```

## 11.14 Do not `raise Exception` (or other non-`StandardError` roots); raise a `StandardError` subclass.

> Why? `Lint/RaiseException` flags raising `Exception` and other roots
> outside the `StandardError` tree. Those classes are reserved for VM and
> system events callers should not treat as application failures. Raise
> `StandardError` subclasses (or a bare message, which is `RuntimeError`).
> **Violation.**
>
> Enforced by: Lint/RaiseException.

```ruby
# bad
raise Exception, 'broken'
raise SystemExit, 'nope'

# good
raise StandardError, 'broken'
raise ArgumentError, 'invalid payload'
```
## 11.15 Do not `return` (or `break` / `next` into outer flow) from an `ensure` body.

> Why? The guide's
> [no return ensure](https://rubystyle.guide/#no-return-ensure)
> rule and `Lint/EnsureReturn` forbid returns in `ensure` because they
> swallow the pending exception or overwrite the method's return value
> silently. Use `ensure` only for cleanup; put control-flow returns in
> `rescue` or after the `begin` block. **Violation.**
>
> Enforced by: Lint/EnsureReturn.

```ruby
# bad
def read
  file = File.open(path)
  file.read
ensure
  file&.close
  return '' # swallows errors and forces empty string
end

# good
def read
  file = File.open(path)
  file.read
ensure
  file&.close
end
```

## 11.16 Prefer raising from bang methods and returning failure status from non-bang methods; do not mix both styles on one name.

> Why? Contiguous with the style guide's dangerous-method conventions:
> `save` returns false, `save!` raises. A method that sometimes returns
> `nil` and sometimes raises for the same condition trains callers to
> miss failures. Pick one contract and document it. **Suggestion.**

```ruby
# bad
def publish(strict: false)
  return false unless valid?
  raise Invalid if strict && !persist
  persist
end

# good
def publish
  return false unless valid?

  persist
end

def publish!
  raise Invalid, 'not valid' unless valid?

  persist!
end
```
