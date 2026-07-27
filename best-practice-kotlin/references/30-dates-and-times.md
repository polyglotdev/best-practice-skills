<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 30. Dates & Times

Kotlin has no date and time library of its own on the JVM, and it does not
need one. `java.time` — JSR-310 — is a well-designed, immutable, thread-safe
API that Kotlin consumes cleanly, and this skill is JVM-only, so **`java.time`
is the recommendation throughout this chapter**.
[`kotlinx-datetime`](https://github.com/Kotlin/kotlinx-datetime) exists for
Kotlin Multiplatform, and `kotlin.time` contributes a `Duration` type (and,
since Kotlin 2.3, `Instant` and `Clock` in the common standard library) that
are worth using in Kotlin-facing signatures. §30.9 and §30.19 draw the
boundary between them.

Almost every date-and-time bug in production is one of four mistakes: storing
a zoneless type for a moment that happened, treating a UTC offset as if it
were a time zone, calling `now()` deep inside business logic so nothing can
be tested, or doing calendar arithmetic with a fixed number of seconds. This
chapter is organised around preventing those four.

Sources are the
[`java.time` package documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/package-summary.html),
the [`kotlin.time` API reference](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.time/),
and the [IANA time zone database](https://www.iana.org/time-zones), which is
what `ZoneId` identifiers resolve against. Neither the Android Kotlin style
guide nor the Kotlin coding conventions legislate on dates, so no rule here
carries a style-guide citation.

Two neighbouring topics are deferred. **Value classes** — the right shape for
a domain-specific wrapper such as `BillingPeriod` — are
[Chapter 12](12-value-classes.md). **Testability of injected collaborators in
general**, including the `Clock` this chapter insists on, is
[Chapter 32, Testing](32-testing.md), §32.15.

**Tool alignment:** `detekt/MagicNumber` catches the hardcoded `3600` that
should have been `1.hours`, and `detekt/ImplicitDefaultLocale` catches
`String.format` and case conversions performed without an explicit `Locale`
— though it does **not** inspect `DateTimeFormatter`, so §30.14 is a
**Suggestion**. Most rules here are Suggestions: no analyser can tell that
your `LocalDateTime` should have been an `Instant`.

## 30.1 Use `java.time` exclusively; `java.util.Date`, `Calendar`, and `SimpleDateFormat` have no place in new code.

> Why? The legacy trio is mutable, not thread-safe, and wrong in ways that
> compile. `java.util.Date` is not a date — it is a millisecond offset with a
> `toString` that lies to you by rendering in the default zone.
> `Calendar.MONTH` is zero-based, so January is `0`, forever.
> `SimpleDateFormat`'s own javadoc warns that "date formats are not
> synchronized" and recommends "separate format instances for each thread" —
> a shared static one produces silently corrupted output under load, not an
> exception. Every one of these problems is designed out of `java.time`.
> **Suggestion.**

```kotlin
// bad — mutable, zero-based months, and a formatter that corrupts output when
// two threads touch it
private val FORMAT = SimpleDateFormat("yyyy-MM-dd")

fun startOfYear(year: Int): Date {
    val cal = Calendar.getInstance()
    cal.set(year, 0, 1)          // 0 means January
    return cal.time
}

// good
private val ISO_DATE: DateTimeFormatter = DateTimeFormatter.ISO_LOCAL_DATE

fun startOfYear(year: Int): LocalDate = LocalDate.of(year, Month.JANUARY, 1)
```

## 30.2 Choose the type by what the value *means*, not by what is convenient to print.

> Why? `java.time` has six commonly used types and each answers a different
> question. Picking the wrong one is the root cause of most timezone
> incidents, because the wrong type silently discards the information you
> later need. The mapping is not a matter of taste:
>
> | Type | Means | Use for |
> |---|---|---|
> | `Instant` | a point on the UTC timeline, no zone | anything that *happened* |
> | `LocalDate` | a calendar date, no time, no zone | birthday, invoice date |
> | `LocalTime` | a wall-clock time, no date, no zone | "shop opens at 09:00" |
> | `LocalDateTime` | wall clock, no zone — **not a moment** | a form value before a zone is known |
> | `ZonedDateTime` | a moment plus an IANA zone, DST-aware | a scheduled future event |
> | `OffsetDateTime` | a moment plus a fixed offset | a wire format that carries `+01:00` |
>
> **Suggestion.**

```kotlin
// bad — every field is the same type, so none of them carries its meaning
data class Booking(
    val createdAt: LocalDateTime,   // a moment, stored without a zone
    val serviceDate: LocalDateTime, // a date; the 00:00 is noise
    val opensAt: LocalDateTime,     // a wall-clock time; the date is noise
)

// good
data class Booking(
    val createdAt: Instant,
    val serviceDate: LocalDate,
    val opensAt: LocalTime,
    val startsAt: ZonedDateTime,    // scheduled: needs the zone to survive DST
)
```

## 30.3 A timestamp for something that already happened is an `Instant` with no zone attached.

> Why? A past event happened at exactly one point on the universal timeline.
> Storing it as a `LocalDateTime` throws that point away and keeps a wall
> clock reading that is meaningless without knowing which clock — and the
> answer is usually "whatever zone the server happened to have when the row
> was written", which changes when the service moves region. Storing it as a
> `ZonedDateTime` keeps a zone that is not part of the fact: `created_at` in
> `Europe/London` and the same instant in `UTC` are the same event.
> `Instant` is the only type that says exactly what is true and nothing more.
> Zone belongs on *display* (§30.5) or as a separate user preference.
> **Suggestion.**

```kotlin
// bad — the moment is unrecoverable once the server's zone changes, and the
// two rows are not comparable across a DST boundary
data class AuditEntry(
    val action: String,
    val at: LocalDateTime,
)

// good
data class AuditEntry(
    val action: String,
    val at: Instant,
)
```

## 30.4 Identify a time zone by its IANA id, never by a fixed offset.

> Why? An offset is a *result*, not a zone. `+01:00` describes London in July
> and Berlin in January and neither of them the rest of the year; it cannot
> tell you when the next transition is, so any arithmetic you do with it
> drifts by an hour twice a year. An IANA id — `Europe/London`,
> `America/New_York`, `Asia/Kolkata` — resolves through the tz database and
> knows every historical and scheduled transition for that region. Kotlin
> lets you write either, and the offset form looks tidier, which is exactly
> the trap. **Suggestion.**

```kotlin
// bad — "+01:00" is correct for London for roughly seven months a year
val zone = ZoneId.of("+01:00")
val opensAt = ZonedDateTime.of(date, LocalTime.of(9, 0), zone)

// bad — a three-letter abbreviation is ambiguous ("CST" names four zones)
val zone = ZoneId.of("CST", ZoneId.SHORT_IDS)

// good
val zone = ZoneId.of("Europe/London")
val opensAt = ZonedDateTime.of(date, LocalTime.of(9, 0), zone)
```

## 30.5 Keep UTC everywhere inside the system; convert to a zone only at the point of display.

> Why? Every conversion is a chance to convert twice, or with the wrong zone,
> or in the wrong direction. Constraining conversion to a single boundary
> means the whole interior — persistence, business logic, messaging, logs —
> has exactly one representation, comparisons are trivially correct, and the
> only code that needs a zone is the code that also knows *whose* zone it is.
> Databases follow the same rule: store `timestamptz`/UTC and let the client
> localise. **Suggestion.**

```kotlin
// bad — the service converts on the way in, so what is stored depends on the
// server's location, and every later comparison is suspect
fun record(event: DomainEvent) {
    val local = LocalDateTime.ofInstant(event.at, ZoneId.systemDefault())
    repository.save(event.name, local)
}

// good — UTC inside, zone only where a human reads it
fun record(event: DomainEvent) {
    repository.save(event.name, event.at)   // Instant
}

fun renderFor(user: User, at: Instant): String =
    at.atZone(user.zone).format(DISPLAY_FORMAT)
```

## 30.6 Never call `ZoneId.systemDefault()`, `LocalDate.now()`, or any other implicitly-zoned `now()` inside business logic.

> Why? `ZoneId.systemDefault()` reads a JVM-wide mutable setting whose value
> is a deployment accident — the host's `/etc/localtime`, a `TZ` environment
> variable, a container base image. Two replicas of the same service can
> disagree. Worse, any code that depends on it produces different results in
> CI than in production and cannot be tested without mutating global state.
> `LocalDate.now()` is the same bug wearing a disguise: it silently uses the
> default zone to decide which day "today" is, which is a real question with
> a real answer only once you say *whose* today. **Suggestion.**

```kotlin
// bad — "today" depends on where the process happens to run
fun isExpired(subscription: Subscription): Boolean =
    LocalDate.now() > subscription.expiresOn

// good — the zone is a stated input, and the clock is injectable (§30.7)
fun isExpired(subscription: Subscription, clock: Clock, zone: ZoneId): Boolean =
    LocalDate.now(clock.withZone(zone)) > subscription.expiresOn
```

## 30.7 Inject a `Clock`; in Kotlin, give it a constructor default so production call sites stay clean.

> Why? `Instant.now()` scattered through business logic makes time an
> untestable global. A `Clock` is the seam `java.time` provides for exactly
> this: `Clock.systemUTC()` in production, `Clock.fixed(instant, zone)` in a
> test, `Clock.offset(base, duration)` to simulate elapsed time. Kotlin's
> default arguments make this cost nothing at the call site — unlike Java,
> where injecting a `Clock` usually means a second constructor. Note that the
> default belongs on the *constructor*, not on the method: a per-call default
> reintroduces the untestable path for anyone who forgets the argument.
> **Suggestion.** See [Chapter 32, §32.15](32-testing.md).

```kotlin
// bad — nothing can test the expiry boundary without sleeping or mocking a
// static
class SessionService(private val repo: SessionRepository) {
    fun expire(id: SessionId) {
        repo.markExpired(id, Instant.now())
    }
}

// good — one default argument makes production call sites unchanged and tests
// deterministic
class SessionService(
    private val repo: SessionRepository,
    private val clock: Clock = Clock.systemUTC(),
) {
    fun expire(id: SessionId) {
        repo.markExpired(id, clock.instant())
    }
}

// in a test
val clock = Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC)
val service = SessionService(repo, clock)
```

## 30.8 Use `Duration` for elapsed machine time and `Period` for calendar amounts; never substitute one for the other.

> Why? They answer different questions and are not interchangeable.
> `Duration` is an exact count of seconds and nanoseconds — the right type
> for a timeout, a latency, a retry backoff. `Period` is a count of years,
> months, and days — the right type for "one month from now", which is 28,
> 29, 30, or 31 days depending on where you start. `Duration.ofDays(30)` is
> not a month, and adding it across a DST transition moves the wall clock by
> an hour (§30.11). **Suggestion.**

```kotlin
// bad — "one month" expressed as exact seconds; wrong in every month that is
// not 30 days, and wrong across a DST boundary
val start: ZonedDateTime = subscription.startedAt.atZone(zone)
val renewal = start.plus(Duration.ofDays(30))

// good — calendar arithmetic for a calendar concept. Note the receiver has to
// support it: ZonedDateTime and LocalDate take a Period, Instant does not.
val renewal = start.plus(Period.ofMonths(1))

// good — exact time for an exact concept
val deadline = Instant.now(clock).plus(Duration.ofSeconds(30))
```

## 30.9 Express durations in Kotlin-facing signatures as `kotlin.time.Duration`; convert at the `java.time` boundary.

> Why? `kotlin.time.Duration` (Stable since Kotlin 1.6) has the extension
> properties that make a call site self-documenting — `5.seconds`,
> `250.milliseconds`, `2.hours` — plus arithmetic, a readable `toString`, and
> destructuring via `toComponents`. `java.time.Duration` requires
> `Duration.ofSeconds(5)` and reads as ceremony. The two convert in one call
> each: `toJavaDuration()` and `toKotlinDuration()`, both JVM-only extensions
> in `kotlin.time`, both Stable since Kotlin 1.6. Use the Kotlin type in your
> own API, convert only where a Java or framework API demands the other.
> **Suggestion.**

```kotlin
// bad — a Kotlin API forcing java.time ceremony on every caller
fun httpClient(connectTimeout: java.time.Duration): HttpClient = ...

httpClient(java.time.Duration.ofMillis(250))

// good — Kotlin duration in, conversion only at the boundary that needs it
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.toJavaDuration

fun httpClient(connectTimeout: Duration): HttpClient =
    HttpClient.newBuilder()
        .connectTimeout(connectTimeout.toJavaDuration()) // java.net.http wants java.time
        .build()

httpClient(connectTimeout = 250.milliseconds)
```

## 30.10 Never express a duration as a bare `Long`, and never name the unit in the parameter name instead of the type.

> Why? `fun poll(intervalMs: Long)` puts the unit in a name the compiler does
> not check, so `poll(30)` compiles whether the author meant 30 milliseconds
> or 30 seconds — and the reader at the call site has to open the declaration
> to find out. A `Duration` parameter makes `poll(30.seconds)` unambiguous,
> makes the mistake unrepresentable, and removes the magic numbers that
> `detekt/MagicNumber` would otherwise report. This is the same argument as
> [Chapter 12](12-value-classes.md) makes for domain wrappers, applied to the
> one primitive obsession every codebase has. **Suggestion** — the adjacent
> `detekt/MagicNumber` fires on the literal, not on the missing type.

```kotlin
// bad — 30 what? And 1_800_000 is a magic number nobody will re-derive
fun schedule(delayMs: Long, timeoutMs: Long) { ... }

schedule(30, 1_800_000)

// good
import kotlin.time.Duration
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

fun schedule(delay: Duration, timeout: Duration) { ... }

schedule(delay = 30.seconds, timeout = 30.minutes)
```

## 30.11 Across a DST transition, `plusDays(1)` and `plus(Duration.ofDays(1))` give different answers — pick the one you mean.

> Why? On a `ZonedDateTime`, `plusDays(1)` is *calendar* arithmetic: it keeps
> the local wall-clock time and adjusts the offset, so 09:00 today becomes
> 09:00 tomorrow even if the day in between was 23 or 25 hours long.
> `plus(Duration.ofDays(1))` is *exact* arithmetic: it adds 86,400 seconds,
> so 09:00 becomes 08:00 or 10:00 across a transition. Both are correct
> operations; the bug is not knowing which one you invoked. "Remind me at 9am
> tomorrow" is calendar. "Retry in 24 hours" is exact. **Suggestion.**

```kotlin
// bad — a daily 09:00 reminder that silently becomes 08:00 for half the year
val zone = ZoneId.of("Europe/London")
val next = reminder.atZone(zone).plus(Duration.ofDays(1))

// good — calendar arithmetic keeps the wall-clock time the user asked for
val next = reminder.atZone(zone).plusDays(1)

// good — exact arithmetic where an exact interval is what was promised
val retryAt = Instant.now(clock).plus(Duration.ofHours(24))
```

## 30.12 Never assume a day is 24 hours, a month 30 days, or a year 365; ask `ChronoUnit` or `Period`.

> Why? A day is 23 or 25 hours twice a year in most of the world. A month is
> 28 to 31 days. A year is 365 or 366. Hand-rolled arithmetic against those
> constants is wrong on a schedule you cannot predict, and the failure is
> off-by-one-day in a billing period or an expiry check — the kind of bug
> that reaches customers before it reaches a test.
> `ChronoUnit.DAYS.between(a, b)` and `Period.between(a, b)` do the real
> calculation. **Suggestion.**

```kotlin
// bad — integer division by a constant that is not always true
val daysBetween = (end.toEpochMilli() - start.toEpochMilli()) / 86_400_000
val ageYears = daysBetween / 365

// good
val daysBetween = ChronoUnit.DAYS.between(startDate, endDate)
val age = Period.between(dateOfBirth, today).years
```

## 30.13 Hoist a `DateTimeFormatter` to a top-level `private val`; it is immutable and thread-safe, unlike its predecessor.

> Why? `DateTimeFormatter`'s javadoc states that the class "is immutable and
> thread-safe", so one shared instance is correct and parsing a pattern on
> every call is pure waste — pattern compilation is not cheap. The rule is
> the exact inverse of the `SimpleDateFormat` habit it replaces: sharing
> *that* was the bug. In Kotlin the natural home is a top-level `private val`
> in the file that formats, or a `companion object` constant if the formatter
> is part of a type's contract. See
> [Chapter 14, Objects, Companions & Factories](14-objects-and-companions.md).
> **Suggestion.**

```kotlin
// bad — parses the pattern on every invocation
fun render(at: Instant, zone: ZoneId): String =
    DateTimeFormatter.ofPattern("d MMM yyyy, HH:mm").format(at.atZone(zone))

// good — compiled once; safe to share because the type is immutable
private val DISPLAY_FORMAT: DateTimeFormatter =
    DateTimeFormatter.ofPattern("d MMM yyyy, HH:mm", Locale.UK)

fun render(at: Instant, zone: ZoneId): String =
    DISPLAY_FORMAT.format(at.atZone(zone))
```

## 30.14 Pass an explicit `Locale` to any formatter that has locale-sensitive fields.

> Why? `DateTimeFormatter.ofPattern("d MMM yyyy")` with no `Locale` uses
> `Locale.getDefault(Locale.Category.FORMAT)` — another JVM-wide deployment
> accident, like `ZoneId.systemDefault()` in §30.6. The output changes with
> the host: `3 Mar 2026` on one machine, `3 mars 2026` on another, `3 3月
> 2026` on a third. When the formatter is used for *parsing*, a locale
> mismatch is not cosmetic, it is a `DateTimeParseException` in production
> and nowhere else. Pass `Locale.UK`/`Locale.US` for machine-facing output,
> or the user's locale for display. **Suggestion** — `detekt/ImplicitDefaultLocale`
> covers `String.format` and case conversions, but not `DateTimeFormatter`.

```kotlin
// bad — output and parsing both depend on the host's default locale
private val MONTH_FORMAT = DateTimeFormatter.ofPattern("MMMM yyyy")

// good — machine-facing output, pinned
private val MONTH_FORMAT = DateTimeFormatter.ofPattern("MMMM yyyy", Locale.UK)

// good — user-facing output, explicit about whose locale it is
fun renderMonth(date: LocalDate, locale: Locale): String =
    DateTimeFormatter.ofPattern("MMMM yyyy", locale).format(date)
```

## 30.15 Serialise dates and times as ISO-8601; never invent a wire format.

> Why? ISO-8601 is the one format every language, database, and log
> aggregator already parses, it sorts lexicographically in the same order it
> sorts chronologically, and it carries the offset explicitly so `Z` is
> unambiguous. A custom pattern in a JSON payload forces every consumer to
> mirror your format string, guarantees a mismatch the first time someone
> adds a millisecond, and loses zone information the moment a
> `LocalDateTime` is written without one. `Instant.toString()` already emits
> ISO-8601, and `DateTimeFormatter.ISO_INSTANT` /
> `ISO_OFFSET_DATE_TIME` cover the rest. **Suggestion.**

```kotlin
// bad — the consumer must reverse-engineer this, and it carries no zone
private val WIRE = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss")

data class EventPayload(val occurredAt: String) {
    companion object {
        fun of(at: Instant): EventPayload =
            EventPayload(WIRE.format(at.atZone(ZoneOffset.UTC)))
    }
}

// good — ISO-8601, UTC, unambiguous
data class EventPayload(val occurredAt: Instant)   // serialises as 2026-03-03T09:15:00Z
```

## 30.16 Do not format an `Instant` with a pattern containing date or time fields.

> Why? An `Instant` has no zone, so it genuinely does not know what year,
> month, or hour it is — asking for one throws
> `UnsupportedTemporalTypeException` at runtime, not at compile time. This
> catches people who correctly followed §30.3 and then reached for their
> existing display formatter. The fix is to supply the zone at the formatting
> call: `instant.atZone(zone)`, or `formatter.withZone(zone)`.
> **Suggestion.**

```kotlin
// bad — throws UnsupportedTemporalTypeException: Unsupported field: YearOfEra
private val DISPLAY = DateTimeFormatter.ofPattern("d MMM yyyy", Locale.UK)

fun render(at: Instant): String = DISPLAY.format(at)

// good — give the formatter the zone it needs
fun render(at: Instant, zone: ZoneId): String = DISPLAY.format(at.atZone(zone))

// good — or bind the zone into the formatter once
private val DISPLAY_UTC: DateTimeFormatter =
    DateTimeFormatter.ofPattern("d MMM yyyy", Locale.UK).withZone(ZoneOffset.UTC)
```

## 30.17 Normalise timestamp precision at the persistence boundary.

> Why? Java 9 raised the resolution of the system clock beyond milliseconds
> on platforms that support it, so `Instant.now()` can carry microseconds or
> nanoseconds. Storage rarely matches: PostgreSQL `timestamptz` keeps
> microseconds, MySQL `DATETIME` keeps whole seconds unless told otherwise,
> and a JSON round trip may keep three decimal places. The result is a test
> that writes an object, reads it back, and fails an equality assertion for
> reasons that look like magic. Truncate deliberately, at one place, to the
> precision your store actually keeps. **Suggestion.**

```kotlin
// bad — the round trip loses sub-microsecond digits and the assertion fails
val saved = repo.save(Order(placedAt = Instant.now(clock)))
assertEquals(saved, repo.findById(saved.id))

// good — one explicit truncation where the value enters the system
fun placeOrder(request: PlaceOrder): Order =
    Order(placedAt = clock.instant().truncatedTo(ChronoUnit.MICROS))
```

## 30.18 Compare moments with `isBefore` / `isAfter` / `isEqual`, not with `equals` on a zoned type.

> Why? `ZonedDateTime.equals` compares the local date-time, the offset, *and*
> the zone — so `2026-06-01T12:00+01:00[Europe/London]` and
> `2026-06-01T11:00Z` are the same moment and are **not** equal. That is the
> documented behaviour, and it is a genuine bug source in deduplication and
> cache keys. `isEqual` compares the instant, which is almost always the
> question you meant. On `Instant` itself, `==` is safe, but `isBefore` and
> `isAfter` still read better than `compareTo`. See
> [Chapter 23, Equality & Ordering](23-equality-and-ordering.md).
> **Suggestion.**

```kotlin
// bad — false, even though both describe the same moment
val a = ZonedDateTime.parse("2026-06-01T12:00+01:00[Europe/London]")
val b = ZonedDateTime.parse("2026-06-01T11:00Z")
if (a == b) { ... }

// good
if (a.isEqual(b)) { ... }

// good — comparison on the zoneless type reads naturally
if (order.placedAt.isBefore(cutoff)) { ... }
```

## 30.19 Use `kotlinx-datetime` only when multiplatform is a real requirement; on the JVM, `java.time` wins.

> Why? `kotlinx-datetime` exists to give Kotlin Multiplatform a common
> date-time API where `java.time` does not exist. On a JVM-only service it
> buys you nothing and costs you a dependency, a second vocabulary
> (`kotlinx.datetime.LocalDate` is not `java.time.LocalDate`), conversion
> functions at every framework boundary, and a smaller surface than the
> platform library it wraps. Note that `kotlin.time.Instant` and
> `kotlin.time.Clock` have been in the common standard library since Kotlin
> 2.3 and are a reasonable choice for shared multiplatform code; on the JVM
> they still convert to `java.time` at every JDBC, Jackson, or Spring
> boundary. This skill is JVM-only, so the default is `java.time`.
> **Suggestion.**

```kotlin
// bad — a JVM-only Spring service importing a multiplatform date library, then
// converting at every boundary anyway
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import kotlinx.datetime.toJavaInstant

@Entity
class Order(
    val placedAt: java.time.Instant = Clock.System.now().toJavaInstant(),
)

// good — one vocabulary, no conversions
import java.time.Clock
import java.time.Instant

@Entity
class Order(
    val placedAt: Instant,
)
```
