<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 23. Logging

Logging is part of your public operational API: structure it, level it, and
never let it become an accidental PII dump. The Ruby Style Guide's small
surface area for warnings —
[warn](https://rubystyle.guide/#warn) and
[always-warn](https://rubystyle.guide/#always-warn) — plus
[global-stdout](https://rubystyle.guide/#global-stdout) — pairs with Rails'
logger helpers. Prefer the framework logger in apps (`Rails.logger`) and a
injected `Logger` (or equivalent) in libraries.

**Tool alignment:** `Style/GlobalStdStream`, `Style/StderrPuts`,
`Rails/EagerEvaluationLogMessage`, and `Rails/Output` are enabled. Most
semantic logging rules remain **Suggestion**.

## 23.1 Prefer the application logger over `puts` / `print` in library and app code.

> Why? `puts` bypasses levels, formatting, and log drains.
> `Rails/Output` flags stdout printing in Rails app code. Use
> `Rails.logger` or an injected logger. **Violation** in Rails apps;
> **Suggestion** elsewhere.

> Enforced by: Rails/Output.

```ruby
# bad
puts "User #{user.id} created"
print debug_payload

# good
Rails.logger.info { "User #{user.id} created" }
logger.debug { debug_payload.inspect }
```

## 23.2 Prefer block forms for expensive log messages.

> Why? `logger.debug("…#{expensive}…")` builds the string even when debug
> is disabled. The block form defers interpolation.
> `Rails/EagerEvaluationLogMessage` catches eager forms in Rails.
> **Violation.**

> Enforced by: Rails/EagerEvaluationLogMessage.

```ruby
# bad
Rails.logger.debug("Payload: #{payload.deep_inspect}")

# good
Rails.logger.debug { "Payload: #{payload.deep_inspect}" }
```

## 23.3 Prefer `warn` for warning-shaped diagnostics; do not invent a parallel channel.

> Why? [warn](https://rubystyle.guide/#warn) integrates with Ruby's warning
> system. `Style/StderrPuts` rejects `$stderr.puts` for that role.
> **Violation.**

> Enforced by: Style/StderrPuts.

```ruby
# bad
$stderr.puts 'configuration X is deprecated'

# good
warn 'configuration X is deprecated'
```

## 23.4 Prefer `Warning.warn` / category-aware warnings when you need filterable deprecations.

> Why? [always-warn](https://rubystyle.guide/#always-warn) discusses making
> warnings visible. On modern Ruby, categorized warnings can be directed and
> tested. Use them for deprecations libraries emit. **Suggestion.**

```ruby
# bad — unstructured stderr
$stderr.puts 'DEPRECATION: OldApi.call'

# good
warn 'OldApi.call is deprecated; use NewApi.call', category: :deprecated
```

## 23.5 Prefer `$stdout` / `$stderr` over `STDOUT` / `STDERR` when you must write streams.

> Why? [global-stdout](https://rubystyle.guide/#global-stdout) — same rule
> as chapter 21. Log frameworks may redirect globals. **Violation.**

> Enforced by: Style/GlobalStdStream.

```ruby
# bad
STDOUT.puts(JSON.generate(event))

# good
$stdout.puts(JSON.generate(event))
```

## 23.6 Prefer semantic levels: debug / info / warn / error / fatal — and mean them.

> Why? If everything is `info`, nothing is. Reserve `error` for failures
> that need human attention, `warn` for recoverable unusual states, `info`
> for lifecycle milestones, `debug` for investigator detail. **Suggestion.**

```ruby
# bad
logger.info("cache miss for #{key}")
logger.info("payment failed: #{e.message}")
logger.info('starting boot')

# good
logger.debug { "cache miss for #{key}" }
logger.error("payment failed: #{e.class}: #{e.message}")
logger.info('starting boot')
```

## 23.7 Prefer structured key/value (or JSON) logs for services; keep free-text for humans.

> Why? Greppable `key=value` or JSON fields power metrics pipelines. Put
> stable identifiers in fields, not only in prose. **Suggestion.**

```ruby
# bad
logger.info("Finished checkout for #{user.id} total=#{total} ms=#{ms}")

# good — structured payload to your logger / lograge / OTel bridge
logger.info(
  message: 'checkout.finished',
  user_id: user.id,
  total_cents: total,
  duration_ms: ms
)
```

## 23.8 Never log secrets, raw passwords, session tokens, or full payment payloads.

> Why? Logs are widely retained and broadly accessible. Redact tokens,
> authorize only last-4 of PANs, and prefer IDs over bodies. **Suggestion.**

```ruby
# bad
logger.info("login params=#{params.inspect}")
logger.debug("Authorization: #{request.headers['Authorization']}")

# good
logger.info(message: 'login.attempt', user_id: user&.id, ip: request.remote_ip)
logger.debug { "Authorization present=#{request.headers['Authorization'].present?}" }
```

## 23.9 Prefer logging exceptions with class, message, and backtrace — once.

> Why? `logger.error(e.message)` drops the class and stack. Log
> `full_message` (or your error reporter) at the boundary; do not re-log the
> same exception at every rescue layer. **Suggestion.**

```ruby
# bad
rescue StandardError => e
  logger.error(e.message)
  raise

# good
rescue StandardError => e
  logger.error(e.full_message)
  raise
```

## 23.10 Prefer correlation / request IDs on every line in request-oriented apps.

> Why? Without a request id, concurrent logs are unmergeable. Use Rails'
> tagged logging or your tracer's current span id. **Suggestion.**

```ruby
# good
Rails.logger.tagged(request.request_id) do
  Rails.logger.info('PaymentsController#create')
end
```

## 23.11 Prefer injectable loggers in gems; do not hard-code `Rails.logger`.

> Why? Libraries that assume Rails cannot be used elsewhere and are harder
> to test. Accept `logger:` with a default of `Logger.new($stdout)`.
> **Suggestion.**

```ruby
# bad
class Client
  def call
    Rails.logger.info('calling')
  end
end

# good
class Client
  def initialize(logger: Logger.new($stdout))
    @logger = logger
  end

  def call
    @logger.info('calling')
  end
end
```

## 23.12 Prefer adjusting log level via configuration, not commented-out log lines.

> Why? Commented logs rot and get uncommented in production under stress.
> Keep stable debug lines behind levels / feature flags. **Suggestion.**

```ruby
# bad
# logger.debug { payload.inspect }
logger.info('done')

# good
logger.debug { payload.inspect }
logger.info('done')
# run with LOG_LEVEL=debug when needed
```

## 23.13 Prefer sampling or rate limits for high-volume debug paths.

> Why? Per-request debug logging of large payloads can DoS your log sink
> and your disk. Sample, truncate, or gate on a flag. **Suggestion.**

```ruby
# bad
requests.each { |req| logger.debug { req.body.read } }

# good
requests.each do |req|
  logger.debug { req.body.read } if sample?(rate: 0.01)
end
```

## 23.14 Prefer UTC timestamps in log formatters for distributed systems.

> Why? Local-time log lines make multi-region incident response harder.
> Configure the formatter once; do not invent per-call stamps. **Suggestion.**

```ruby
# good — configure at boot
logger.formatter = proc do |severity, time, progname, msg|
  "#{time.utc.iso8601(3)} #{severity} #{progname}: #{msg}\n"
end
```

## 23.15 Prefer failing loud for fatal misconfiguration rather than logging and continuing.

> Why? Logging `ERROR: DATABASE_URL missing` and then continuing boots a
> zombie process. Raise at boot; log the failure in the process supervisor.
> **Suggestion.**

```ruby
# bad
if ENV['DATABASE_URL'].nil?
  logger.error('DATABASE_URL missing')
end

# good
ENV.fetch('DATABASE_URL')
```
