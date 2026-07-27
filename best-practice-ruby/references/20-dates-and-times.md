<!-- Part of the `best-practice-ruby` skill. See SKILL.md for the index. -->

# 20. Dates & Times

Time handling is where "works on my machine" becomes a production incident.
Ruby gives you `Time`, `Date`, and legacy `DateTime`. The Ruby Style Guide
discourages `DateTime` under
[no-datetime](https://rubystyle.guide/#no-datetime) and discusses choosing
among the remaining types under [date-time](https://rubystyle.guide/#date-time)
and [time-now](https://rubystyle.guide/#time-now). In Rails apps, prefer
ActiveSupport zone-aware APIs documented at
[time](https://rails.rubystyle.guide/#time),
[time-now](https://rails.rubystyle.guide/#time-now),
[time-parse](https://rails.rubystyle.guide/#time-parse),
[to-time](https://rails.rubystyle.guide/#to-time),
[freeze-time](https://rails.rubystyle.guide/#freeze-time), and
[date-time-range](https://rails.rubystyle.guide/#date-time-range).

**Rule of thumb on Ruby 4.0 / Rails 8:** use zone-aware `Time` (via
`Time.zone` / `Time.current` in Rails) at application edges; use `Date` for
calendar dates without a clock component; do not introduce `DateTime` in new
code. Convert at boundaries; keep UTC in storage when you can.

**Tool alignment:** `Rails/TimeZone`, `Rails/TimeZoneAssignment`,
`Rails/Date`, `Rails/DurationArithmetic`, `Rails/RelativeDateConstant`, and
`Rails/RedundantTravelBack` are enabled for Rails code. Core Ruby has no
enabled `Style/DateTime` in this skill's effective config — treat
`DateTime` avoidance as a style-guide **Suggestion** unless a Rails cop
fires.

## 20.1 Prefer `Time` (zone-aware at app edges) over `DateTime`.

> Why? `DateTime` is slower, surprising around offsets, and explicitly
> discouraged by [no-datetime](https://rubystyle.guide/#no-datetime). Use
> `Time` for instants and `Date` for civil dates. In Rails, construct via
> `Time.zone` so the app time zone applies. **Suggestion** for plain Ruby;
> Rails call sites that ignore zones are **Violation** under Rails cops
> below.

```ruby
# bad
require 'date'
created = DateTime.now
created = DateTime.parse('2026-07-27 18:00')

# good — plain Ruby instant
created = Time.now.utc

# good — Rails app edge
created = Time.zone.parse('2026-07-27 18:00')
created = Time.current
```

## 20.2 In Rails, prefer `Time.zone` / `Time.current` over `Time.now` and `Time.parse`.

> Why? `Time.now` uses the system zone, not `config.time_zone`.
> [time-now](https://rails.rubystyle.guide/#time-now) and
> [time-parse](https://rails.rubystyle.guide/#time-parse) require the
> zone-aware API. **Violation.**

> Enforced by: Rails/TimeZone.

```ruby
# bad
Time.now
Time.parse('2026-07-27 09:00')
Time.at(timestamp)

# good
Time.current
Time.zone.now
Time.zone.parse('2026-07-27 09:00')
Time.zone.at(timestamp)
```

## 20.3 Do not assign `Time.zone` ad hoc in request or job code.

> Why? Mutating `Time.zone` leaks across requests/threads.
> `Rails/TimeZoneAssignment` flags assignment; use `Time.use_zone` for a
> temporary override. **Violation.**

> Enforced by: Rails/TimeZoneAssignment.

```ruby
# bad
Time.zone = 'America/New_York'
run_report

# good
Time.use_zone('America/New_York') do
  run_report
end
```

## 20.4 Prefer `Date.current` over `Date.today` in Rails.

> Why? `Date.today` ignores `Time.zone` and can disagree with
> `Time.current.to_date` near midnight.
> `Rails/Date` enforces the zone-aware helpers. **Violation.**

> Enforced by: Rails/Date.

```ruby
# bad
Date.today
Date.tomorrow

# good
Date.current
Time.zone.tomorrow.to_date
```

## 20.5 Use `Date` for calendar dates; do not fake them as midnight `Time` values unless an instant is required.

> Why? Birthdays, fiscal periods, and "due on" fields are dates. Storing
> them as `2026-07-27 00:00:00` in a zone creates off-by-one bugs when the
> zone offset shifts the calendar day. Prefer `date` columns and `Date`
> objects. **Suggestion.**

```ruby
# bad
user.born_at = Time.zone.parse('1990-01-15 00:00:00')

# good
user.born_on = Date.new(1990, 1, 15)
```

## 20.6 Prefer ActiveSupport duration arithmetic over raw integer second math when expressing domain time.

> Why? `2.days.ago` states intent; `Time.now - 172_800` does not.
> Prefer `from_now` / `ago` over `since` / `until` when the qualifier is
> "now"
> ([duration-application](https://rails.rubystyle.guide/#duration-application),
> [duration-arithmetic](https://rails.rubystyle.guide/#duration-arithmetic)).
> Avoid mixing duration objects with bare integers incorrectly.
> `Rails/DurationArithmetic` catches hazardous forms. **Violation** when
> the cop fires; otherwise **Suggestion**.

> Enforced by: Rails/DurationArithmetic.

```ruby
# bad
cutoff = Time.current - (60 * 60 * 24 * 7)
expires_at = 15.minutes.since

# good
cutoff = 7.days.ago
expires_at = 15.minutes.from_now
```

## 20.7 Do not put relative dates in constants that evaluate once at load time.

> Why? `CUTOFF = 1.day.ago` freezes at boot.
> `Rails/RelativeDateConstant` flags it. Use a method or lambda.
> **Violation.**

> Enforced by: Rails/RelativeDateConstant.

```ruby
# bad
CUTOFF = 1.day.ago

# good
def cutoff
  1.day.ago
end
```

## 20.8 Prefer `travel_to` / `freeze_time` in tests; clean up with the block form.

> Why? [freeze-time](https://rails.rubystyle.guide/#freeze-time) keeps
> time-dependent tests deterministic. Prefer block forms so teardown is
> automatic; `Rails/RedundantTravelBack` removes useless `travel_back`.
> **Suggestion** for the practice; **Violation** when the redundant
> teardown cop fires.

> Enforced by: Rails/RedundantTravelBack.

```ruby
# bad
travel_to Time.zone.parse('2026-01-01 12:00')
example.run
travel_back

# good
freeze_time do
  # assertions against Time.current
end

travel_to(Time.zone.parse('2026-01-01 12:00')) do
  # ...
end
```

## 20.9 Prefer inclusive/exclusive range APIs that match the domain when querying date spans.

> Why? [date-time-range](https://rails.rubystyle.guide/#date-time-range)
> matters for `where(created_at: start..finish)` vs `...` exclusion.
> Be explicit about end-of-day boundaries (`end_of_day`) and whether the
> end is inclusive. **Suggestion.**

```ruby
# bad — unclear whether end_date's entire day is included
User.where(created_at: start_date..end_date)

# good
User.where(created_at: start_date.beginning_of_day..end_date.end_of_day)

# good — exclusive end
User.where(created_at: start_time...end_time)
```

## 20.10 Prefer UTC for persistence and interchange; convert to local zones at the UI edge.

> Why? Storing local wall times without offsets loses information across DST
> and server moves. Persist UTC (or offset-aware timestamps), convert with
> `in_time_zone` for display. **Suggestion.**

```ruby
# bad — persist ambiguous local time
record.update!(occurred_at: Time.zone.parse('2026-11-01 01:30'))

# good — store UTC instant; present in zone
record.update!(occurred_at: Time.find_zone!('UTC').parse('2026-11-01 05:30'))
display = record.occurred_at.in_time_zone('America/New_York')
```

## 20.11 Prefer `to_fs` / explicit formats over relying on `to_s` for timestamps in APIs.

> Why? Default string forms vary and are a poor interchange format. Use ISO
> 8601 (`xmlschema` / `iso8601`) for APIs and I18n formats for humans.
> Rails' `Rails/ToFormattedS` may apply depending on call shape.
> **Suggestion.**

```ruby
# bad
payload = { created_at: record.created_at.to_s }

# good
payload = { created_at: record.created_at.utc.iso8601 }
```

## 20.12 Prefer `ActiveSupport::TimeWithZone` awareness when converting strings with `to_time`.

> Why? [to-time](https://rails.rubystyle.guide/#to-time) warns that
> `String#to_time` behaviour depends on configuration. Prefer
> `Time.zone.parse` when you mean app zone. **Suggestion.**

```ruby
# bad — zone behaviour is easy to misread
stamp = '2026-07-27 18:00'.to_time

# good
stamp = Time.zone.parse('2026-07-27 18:00')
```

## 20.13 Prefer monotonic clocks for measuring durations, not wall-clock `Time.now` deltas.

> Why? NTP steps and DST make wall-clock unsuitable for benchmarks and
> timeouts. Use `Process.clock_gettime(Process::CLOCK_MONOTONIC)` (or
> `Benchmark.monotonic`) for elapsed time. **Suggestion.**

```ruby
# bad
started = Time.now
work
elapsed = Time.now - started

# good
started = Process.clock_gettime(Process::CLOCK_MONOTONIC)
work
elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - started
```

## 20.14 Prefer parsing with an explicit format when the input is not ISO-8601.

> Why? `Time.parse` / `Date.parse` guess formats and can swap month/day.
> Use `strptime` with a format string for user input and logs. **Suggestion.**

```ruby
# bad
Date.parse('01/02/2026') # Jan 2 or Feb 1?

# good
Date.strptime('01/02/2026', '%m/%d/%Y')
Time.zone.strptime('01/02/2026 15:04', '%m/%d/%Y %H:%M')
```

## 20.15 Keep business "today" decisions behind a clock seam for tests.

> Why? Direct `Date.current` scattered through domain objects is hard to
> stub consistently. Inject a clock or wrap "today" in one method, then
> `travel_to` in tests. **Suggestion.**

```ruby
# bad — untestable sprawl
def overdue?
  due_on < Date.current
end

# good
class Invoice
  def overdue?(today: Date.current)
    due_on < today
  end
end
```
