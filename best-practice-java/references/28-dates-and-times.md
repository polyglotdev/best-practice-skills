<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 28. Dates & Times (`java.time`)

Almost every date bug is a type error that the old API let you make.
`java.util.Date` is a mutable instant that prints itself in the system
default zone; `Calendar` numbers months from zero; `SimpleDateFormat` is a
mutable parser that people share across threads. Those three classes have
produced more production incidents than any other corner of the JDK, and
`java.time` exists because the JSR-310 authors decided the fix was not a
patch but a different set of types.

The whole discipline of this chapter is *pick the type that says what you
actually have*. An `Instant` is a point on the timeline and knows nothing
about calendars. A `LocalDate` is a calendar date and knows nothing about
the timeline. A `ZonedDateTime` is the bridge, and the bridge is where the
edge cases live. Getting the type right at the boundary makes most of the
remaining rules automatic, because the compiler stops you from asking a
value a question it cannot answer.

This chapter draws on the
[JDK 21 `java.time` package](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/package-summary.html)
documentation, the
[`Clock`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/Clock.html)
and
[`ZoneRules`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/zone/ZoneRules.html)
API contracts, and the
[IANA Time Zone Database](https://www.iana.org/time-zones) that
`ZoneId` resolves against. Google's Java Style Guide is silent on dates, so
no rule here carries a Google anchor. Formatting and parsing *text* is
[Chapter 21](21-strings-and-text-blocks.md); the immutability argument that
makes `java.time` values safe to share is Effective Java, 3rd ed., Item 17.
Testing with an injected `Clock` is picked up again in
[Chapter 31, §31.20](31-testing.md).

**Tool alignment:** Error Prone carries an unusually strong `java.time`
rule set — `JavaUtilDate`, `JavaTimeDefaultTimeZone`, `InstantTemporalUnit`,
`ZoneIdOfZ`, `ThreeLetterTimeZoneID`, `InvalidZoneId`, `MisusedWeekYear`,
`MisusedDayOfYear`, `PreferJavaTimeOverload`,
`JavaInstantGetSecondsGetNano`, `JavaDurationGetSecondsGetNano`,
`JavaPeriodGetDays`, and `PeriodFrom` — and Checkstyle's `IllegalImport`
(with `illegalClasses`) and `IllegalType` can ban the legacy classes
outright. Rules those checks cover are marked **Violation**; design rules
about which type to reach for are **Suggestions**.

## 28.1 Use `java.time` for every date and time value — never `java.util.Date`, `Calendar`, `SimpleDateFormat`, or `java.sql.Timestamp` in new code.

> Why? Each legacy type fails in a different way and all four fail
> silently. `java.util.Date` is mutable, so handing one to a collaborator
> hands over the right to change it; it is also an instant that formats
> itself in the system default zone, which makes `toString()` output
> machine-dependent. `Calendar` numbers months from zero, so
> `Calendar.set(2024, 1, 1)` is February. `SimpleDateFormat` holds parse
> state in fields, so a shared instance produces corrupt results under
> concurrency rather than throwing. `java.sql.Timestamp` extends `Date` and
> breaks the `equals` symmetry contract with it. Every `java.time` type is
> immutable, thread-safe, and month-1-is-January.
> **Violation — enforced by Error Prone `JavaUtilDate`.**

```java
// bad — mutable, zero-based months, and a formatter that is not thread-safe
private static final SimpleDateFormat FORMAT = new SimpleDateFormat("yyyy-MM-dd");

Calendar calendar = Calendar.getInstance();
calendar.set(2024, 1, 1); // February 1st, not January 1st
Date startOfMonth = calendar.getTime();
String rendered = FORMAT.format(startOfMonth); // data race if shared

// good
private static final DateTimeFormatter FORMAT = DateTimeFormatter.ISO_LOCAL_DATE;

LocalDate startOfMonth = LocalDate.of(2024, Month.JANUARY, 1);
String rendered = FORMAT.format(startOfMonth);
```

## 28.2 Represent the timestamp of something that happened as an `Instant`, and never attach a zone to it.

> Why? "When this order was placed" is a single point on the timeline. It
> is the same point for every observer; only its *rendering* differs. An
> `Instant` carries exactly that and nothing more, so it cannot be
> accidentally reinterpreted in another zone. Storing the event's zone
> alongside it invites two bugs: comparison and ordering start depending on
> which zone each row happened to be written in, and a later reader treats
> the stored zone as "where the user was", which it usually is not. If you
> genuinely need the actor's location, model it as a separate field with a
> name that says so. **Suggestion.**

```java
// bad — the zone is noise on a past event and corrupts ordering
public record Order(OrderId id, ZonedDateTime placedAt, ZoneId placedIn) {}

// good — the moment is a moment; location is a separate, honest field
public record Order(OrderId id, Instant placedAt, ZoneId customerZone) {}
```

## 28.3 Use `LocalDate`, `LocalTime`, or `LocalDateTime` only for values that genuinely have no instant.

> Why? A date of birth, a public holiday, a shop's 09:00 opening time, and
> a contract's expiry date are calendar facts, not moments — they are the
> same value in Auckland and in Lisbon. Forcing them into an `Instant`
> requires inventing a zone, and the invented zone leaks into every
> comparison afterwards. The converse mistake is worse: a `LocalDateTime`
> used as a timestamp is an instant with the zone silently deleted, which
> means the value is ambiguous during a DST overlap and non-existent during
> a gap. **Suggestion.**

```java
// bad — a timestamp with the zone thrown away; ambiguous twice a year
public record AuditEntry(String actor, LocalDateTime occurredAt) {}

// good — calendar facts are Local*, timeline facts are Instant
public record Employee(String name, LocalDate dateOfBirth) {}

public record BusinessHours(LocalTime opensAt, LocalTime closesAt) {}

public record AuditEntry(String actor, Instant occurredAt) {}
```

## 28.4 Use `ZonedDateTime` for a wall-clock time in a named region, and `OffsetDateTime` only when the protocol hands you a fixed offset.

> Why? These two look interchangeable and are not. `ZonedDateTime` holds an
> IANA region and therefore knows the *rules* — it can add a day across a
> DST transition and produce the right wall-clock answer. `OffsetDateTime`
> holds a raw `±hh:mm` and knows nothing, so arithmetic on it silently
> ignores DST. Use `ZonedDateTime` for anything scheduled in a place ("the
> 09:00 standup in Dublin"), and `OffsetDateTime` only as a wire or
> database type where a fixed offset is what the format actually carries.
> **Suggestion.**

```java
// bad — scheduling in a region using a fixed offset; wrong after a DST shift
OffsetDateTime standup =
    OffsetDateTime.of(LocalDate.of(2024, 3, 25), LocalTime.of(9, 0), ZoneOffset.ofHours(0));
OffsetDateTime nextWeek = standup.plusWeeks(1); // still 09:00+00:00 — now 10:00 in Dublin

// good — the region knows its own rules
ZonedDateTime standup =
    ZonedDateTime.of(LocalDate.of(2024, 3, 25), LocalTime.of(9, 0), ZoneId.of("Europe/Dublin"));
ZonedDateTime nextWeek = standup.plusWeeks(1); // 09:00 local, offset adjusts itself
```

## 28.5 Identify a zone with an IANA region ID — never a fixed offset, never a three-letter abbreviation.

> Why? An offset is a *result*, not an identity: `+05:30` is what
> `Asia/Kolkata` happens to be, and `+01:00` is what `Europe/Dublin` is for
> part of the year. Storing the offset throws away the rules that produced
> it, so any future arithmetic straddling a transition is wrong.
> Three-letter abbreviations are worse. `IST` is India, Ireland, or Israel
> depending on who wrote it, and the JDK's `ZoneId.SHORT_IDS` map silently
> decides it means `Asia/Kolkata`. `TimeZone.getTimeZone("EST")` and
> `ZoneId.of("EST", ZoneId.SHORT_IDS)` both give a fixed `-05:00` with no
> DST at all, which is not what anyone means by "Eastern". A bare
> `ZoneId.of("EST")` or `ZoneId.of("IST")` does not even resolve: neither is
> an IANA region ID, so both throw `ZoneRulesException` at runtime. Region
> IDs (`Europe/Dublin`, `America/New_York`) resolve against the IANA
> database and track the rule changes governments actually make.
> **Violation — enforced by Error Prone `ThreeLetterTimeZoneID`,
> `InvalidZoneId`, and `ZoneIdOfZ`.**

```java
// bad — an offset masquerading as a zone
ZoneId zone = ZoneId.of("+05:30");

// bad — not an IANA region ID; throws ZoneRulesException at runtime
ZoneId other = ZoneId.of("IST");

// bad — resolves, but to whatever the abbreviation map decided:
// Asia/Kolkata, and a fixed -05:00 with no DST rather than America/New_York
ZoneId india = ZoneId.of("IST", ZoneId.SHORT_IDS);
TimeZone eastern = TimeZone.getTimeZone("EST");

// bad — an offset written as a zone id
ZoneId utc = ZoneId.of("Z");

// good
ZoneId zone = ZoneId.of("Asia/Kolkata");
ZoneId other = ZoneId.of("Europe/Dublin");
ZoneId utc = ZoneOffset.UTC;
```

## 28.6 Store and transmit UTC; convert to a local zone only at the display boundary.

> Why? A system with one canonical representation on the wire and in the
> database has one place where zone logic can be wrong. A system that
> converts at each hop has as many places as it has hops, and the bugs only
> reproduce for users in the zones nobody on the team lives in. Push the
> `atZone` call as far out as it will go — ideally into the rendering layer,
> using a zone the *request* supplied rather than one the server assumed.
> **Suggestion.**

```java
// bad — the service converts to a local zone, so every downstream consumer
// receives a value it must guess the meaning of
public String describe(Order order) {
  LocalDateTime local = LocalDateTime.ofInstant(order.placedAt(), ZoneId.systemDefault());
  return "placed " + local;
}

// good — the service keeps UTC; the caller supplies the display zone
public String describe(Order order, ZoneId displayZone, Locale locale) {
  ZonedDateTime local = order.placedAt().atZone(displayZone);
  return "placed " + DISPLAY_FORMAT.withLocale(locale).format(local);
}

private static final DateTimeFormatter DISPLAY_FORMAT =
    DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM);
```

## 28.7 Never call a `now()` overload that reads the system default zone.

> Why? `LocalDate.now()`, `LocalDateTime.now()`, `ZonedDateTime.now()`, and
> `ZoneId.systemDefault()` all consult the JVM's default zone, which is set
> by the host, can be changed at runtime by any code calling
> `TimeZone.setDefault`, and differs between a developer's laptop and the
> container in production. That makes the result of an otherwise pure
> function depend on ambient global state, so the test that passes locally
> fails at 23:30 UTC in CI. Pass the zone explicitly.
> **Violation — enforced by Error Prone `JavaTimeDefaultTimeZone`.**

```java
// bad — silently depends on the host's default zone
LocalDate today = LocalDate.now();
ZonedDateTime nowHere = ZonedDateTime.now();

// good — the zone is an input, not ambient state
LocalDate today = LocalDate.now(billingZone);
ZonedDateTime nowThere = ZonedDateTime.now(billingZone);
```

## 28.8 Inject a `Clock` instead of scattering `Instant.now()` through business logic.

> Why? `Instant.now()` is a hidden dependency on the wall clock. Any method
> that calls it is untestable at boundaries — expiry, retention windows,
> rate limits, "is this token still valid" — precisely the logic most worth
> testing. A `Clock` is a first-class, injectable source of time;
> `Clock.systemUTC()` in production and `Clock.fixed` in tests give you the
> same code path with a deterministic answer. Declare the field `final` and
> take it in the constructor like any other collaborator
> ([Chapter 32](32-spring-beans-and-di.md) for the Spring bean form).
> **Suggestion.**

```java
// bad — nothing can pin the current time, so the expiry branch is untestable
public final class TokenValidator {
  public boolean isValid(Token token) {
    return token.expiresAt().isAfter(Instant.now());
  }
}

// good
public final class TokenValidator {
  private final Clock clock;

  public TokenValidator(Clock clock) {
    this.clock = clock;
  }

  public boolean isValid(Token token) {
    return token.expiresAt().isAfter(clock.instant());
  }
}
```

## 28.9 Build test time with `Clock.fixed`, and step it with `Clock.offset` — never with `Thread.sleep`.

> Why? A test that sleeps is slow, flaky, and still does not pin the value
> under assertion; a test that asserts `isCloseTo(Instant.now(), …)` is
> asserting on the machine, not the code. `Clock.fixed(instant, zone)`
> makes "now" a constant you chose, so the assertion is exact.
> `Clock.offset(base, duration)` advances it without waiting. Note that
> `Clock.fixed` requires a zone even when the code only calls `instant()` —
> pass `ZoneOffset.UTC` so the test does not inherit a host zone.
> **Suggestion.**

```java
// bad — sleeps for real time and still asserts against a moving target
@Test
void tokenExpires() throws InterruptedException {
  Token token = issuer.issue(Duration.ofSeconds(1));
  Thread.sleep(1_100);
  assertThat(validator.isValid(token)).isFalse();
}

// good — deterministic and instant
@Test
void tokenExpiresOnceTheTtlHasElapsed() {
  Instant issuedAt = Instant.parse("2024-01-01T00:00:00Z");
  Clock clock = Clock.fixed(issuedAt, ZoneOffset.UTC);
  Token token = new TokenIssuer(clock).issue(Duration.ofSeconds(60));

  Clock later = Clock.offset(clock, Duration.ofSeconds(61));

  assertThat(new TokenValidator(later).isValid(token)).isFalse();
}
```

## 28.10 Use `Duration` for machine time and `Period` for calendar time — never treat them as interchangeable.

> Why? They answer different questions. `Duration` is an exact count of
> seconds and nanoseconds, so `Duration.ofDays(1)` is always exactly 86,400
> seconds. `Period` is a calendar amount, so `Period.ofDays(1)` means "the
> same wall-clock time tomorrow", which is 23 or 25 hours across a DST
> transition and exactly the answer a human expects. Using the wrong one
> produces a value that is right for most of the year and off by an hour
> twice — the hardest class of date bug to reproduce.
> **Suggestion.**

```java
// bad — a timeout expressed as a calendar amount, and a calendar age
// expressed as machine time
Period timeout = Period.ofDays(1);
long ageInYears = Duration.between(birth, now).toDays() / 365;

// good
Duration timeout = Duration.ofHours(24);
int ageInYears = Period.between(dateOfBirth, today).getYears();
```

## 28.11 Do DST-sensitive arithmetic with the calendar methods, not by adding a `Duration` of days.

> Why? `zdt.plusDays(1)` keeps the wall-clock time and lets the offset
> move; `zdt.plus(Duration.ofDays(1))` adds exactly 24 hours and lets the
> wall-clock time move. On the night a region springs forward, those two
> give answers an hour apart. "Same time tomorrow" is a calendar operation
> and must use `plusDays`. Only reach for `Duration` when you genuinely
> mean elapsed physical time, such as a lease or a timeout — and in that
> case work on the `Instant`, not the `ZonedDateTime`, so the intent is
> unmistakable. **Suggestion.**

```java
// bad — "the same alarm tomorrow" drifts by an hour across a DST boundary
ZonedDateTime alarm =
    ZonedDateTime.of(LocalDate.of(2024, 3, 30), LocalTime.of(7, 0), ZoneId.of("Europe/Dublin"));
ZonedDateTime tomorrow = alarm.plus(Duration.ofDays(1)); // 08:00 local

// good — calendar arithmetic keeps the wall clock and moves the offset
ZonedDateTime tomorrow = alarm.plusDays(1); // 07:00 local

// also good — a genuine 24-hour lease, expressed on the timeline
Instant leaseExpiry = acquiredAt.plus(Duration.ofHours(24));
```

## 28.12 Resolve DST gaps and overlaps deliberately when converting a `LocalDateTime` to an instant.

> Why? `ZonedDateTime.of(localDateTime, zone)` never throws: in a spring
> gap it pushes the time forward by the gap length, and in an autumn
> overlap it silently picks the *earlier* offset. Both defaults are
> reasonable and both are wrong for some domains — a billing job that runs
> at 01:30 wants to know it ran twice, and a booking system wants to reject
> a non-existent 01:30 rather than quietly move it to 02:30. Ask
> `ZoneRules.getValidOffsets` when the answer matters: an empty list is a
> gap, two entries are an overlap.
> **Suggestion.**

```java
// bad — a non-existent local time is silently shifted, and an ambiguous one
// silently resolves to whichever offset the JDK picks
ZonedDateTime slot = ZonedDateTime.of(requested, zone);

// good — the caller decides what a gap and an overlap mean
List<ZoneOffset> offsets = zone.getRules().getValidOffsets(requested);
ZonedDateTime slot =
    switch (offsets.size()) {
      case 0 -> throw new IllegalArgumentException("local time does not exist: " + requested);
      case 1 -> ZonedDateTime.ofLocal(requested, zone, offsets.get(0));
      // Overlap: bill against the first pass so the job is not double-charged.
      default -> ZonedDateTime.ofLocal(requested, zone, offsets.get(0));
    };
```

## 28.13 Measure elapsed time with `Duration.between` or `ChronoUnit.between` — never by subtracting epoch millis.

> Why? Hand-rolled millisecond arithmetic loses the unit in the type
> system, so a `long` that means milliseconds and a `long` that means
> seconds are the same type and get mixed up. It also invites the wrong
> divisor (`/ 1000 / 60 / 60 / 24` is not days across a DST boundary, and
> is off by leap seconds nowhere but is still unreadable).
> `Duration.between` returns a self-describing value;
> `ChronoUnit.DAYS.between` gives whole calendar days between two dates.
> For measuring code execution use `System.nanoTime`, which is monotonic —
> `Instant.now()` can move backwards when NTP corrects the clock.
> **Suggestion.**

```java
// bad — units live only in the variable name, and the divisor chain is unchecked
long elapsedMillis = end.toEpochMilli() - start.toEpochMilli();
long days = elapsedMillis / 1000 / 60 / 60 / 24;

// good
Duration elapsed = Duration.between(start, end);
long days = ChronoUnit.DAYS.between(startDate, endDate);

// good — monotonic source for measuring code, not wall time
long startNanos = System.nanoTime();
doWork();
Duration took = Duration.ofNanos(System.nanoTime() - startNanos);
```

## 28.14 Serialize with ISO-8601 using the predefined formatters, not a hand-rolled pattern.

> Why? ISO-8601 is unambiguous, sorts lexicographically in UTC, and every
> language on the other side of the wire can parse it. A hand-written
> pattern re-derives it slightly wrong — a missing `'Z'`, a space instead of
> `T`, three fractional digits where the value has six — and the mismatch
> only surfaces at a consumer you do not control. `DateTimeFormatter`
> already ships `ISO_INSTANT`, `ISO_OFFSET_DATE_TIME`, `ISO_LOCAL_DATE`,
> and friends; `Instant.toString()` and `Instant.parse` are ISO-8601 by
> definition. **Suggestion.**

```java
// bad — reinvents ISO-8601 and drops the zone designator
private static final DateTimeFormatter WIRE =
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

String json = WIRE.format(LocalDateTime.ofInstant(placedAt, ZoneOffset.UTC));

// good
String json = DateTimeFormatter.ISO_INSTANT.format(placedAt);
Instant parsed = Instant.parse(json);
```

## 28.15 Hoist `DateTimeFormatter` into a `static final` field and give it an explicit `Locale`.

> Why? Unlike `SimpleDateFormat`, `DateTimeFormatter` is immutable and
> thread-safe, so a single shared instance is correct and avoids rebuilding
> the pattern on every call. But a formatter built without a `Locale`
> inherits `Locale.getDefault(Locale.Category.FORMAT)`, which means month
> and day names — and, for a handful of locales, the *numerals* and even
> the calendar system — change with the host. A machine-readable format
> must pin `Locale.ROOT`; a human-readable one must take the user's locale
> as a parameter. **Suggestion.**

```java
// bad — rebuilt per call, and the month name depends on the host locale
public String render(LocalDate date) {
  return DateTimeFormatter.ofPattern("dd MMM yyyy").format(date);
}

// good — shared, immutable, and locale-explicit
private static final DateTimeFormatter MACHINE =
    DateTimeFormatter.ofPattern("dd MMM yyyy", Locale.ROOT);

public String render(LocalDate date) {
  return MACHINE.format(date);
}

public String renderFor(LocalDate date, Locale locale) {
  return DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).withLocale(locale).format(date);
}
```

## 28.16 Never write `YYYY` when you mean `yyyy`, or `DD` when you mean `dd`.

> Why? `YYYY` is the *week-based* year and `DD` is the day *of the year*.
> They agree with the calendar year and day-of-month for most of the
> calendar, which is exactly why the bug ships: `YYYY-MM-dd` on 30 December
> 2019 formats as `2020-12-30`, because that date falls in ISO week 1 of
> 2020. The defect appears for a few days each December and disappears
> again, so it survives every review that happens in March.
> **Violation — enforced by Error Prone `MisusedWeekYear` and
> `MisusedDayOfYear`.**

```java
// bad — week-based year; wrong for a few days every December
DateTimeFormatter.ofPattern("YYYY-MM-dd", Locale.ROOT);

// bad — DD is day-of-year, so 1 February 2024 formats as 2024-02-32
// (and 31 January formats as 2024-01-31, which is why the bug ships)
DateTimeFormatter.ofPattern("yyyy-MM-DD", Locale.ROOT);

// good
DateTimeFormatter.ofPattern("yyyy-MM-dd", Locale.ROOT);
```

## 28.17 Truncate precision deliberately at a persistence or wire boundary, and compare at the same precision.

> Why? `Instant` carries nanoseconds. PostgreSQL `timestamptz` stores
> microseconds, MySQL `DATETIME` defaults to whole seconds, and a JSON
> consumer may keep milliseconds. So a value that round-trips through
> storage is not `equals` to the value you wrote, and an
> `assertThat(read).isEqualTo(written)` fails on a machine whose clock
> happens to produce sub-microsecond digits. Truncate on the way in with
> `truncatedTo` so the in-memory value and the stored value agree by
> construction. Note that `Instant.truncatedTo` only accepts units of
> `DAYS` or smaller — larger units throw.
> **Violation for the unit constraint — enforced by Error Prone
> `InstantTemporalUnit`.**

```java
// bad — nanosecond precision written, microsecond precision read back
Order order = new Order(id, clock.instant());
repository.save(order);
assertThat(repository.findById(id)).isEqualTo(order); // fails intermittently

// bad — MONTHS is not a valid truncation unit for Instant; throws at runtime
Instant month = clock.instant().truncatedTo(ChronoUnit.MONTHS);

// good — truncate to the precision the store actually keeps
Order order = new Order(id, clock.instant().truncatedTo(ChronoUnit.MICROS));
repository.save(order);
assertThat(repository.findById(id)).isEqualTo(order);
```

## 28.18 Compare temporal values with `isBefore`, `isAfter`, and `compareTo` — not with `equals`.

> Why? `equals` on `java.time` types is exact and type-sensitive, which is
> almost never the question being asked. Two `ZonedDateTime` values
> representing the same instant in different zones are *not* `equals`, and
> two `Instant` values a nanosecond apart are not `equals` either, so an
> equality check on timestamps is a test that passes only by luck.
> `isBefore` and `isAfter` compare positions on the timeline and ignore the
> zone, which is what "did this happen before that" means. For "same
> moment" on `ZonedDateTime`, compare `toInstant()` or use `isEqual`.
> **Suggestion.**

```java
// bad — same moment, different zones; equals is false
ZonedDateTime dublin = instant.atZone(ZoneId.of("Europe/Dublin"));
ZonedDateTime tokyo = instant.atZone(ZoneId.of("Asia/Tokyo"));
boolean same = dublin.equals(tokyo); // false

// good
boolean same = dublin.isEqual(tokyo); // true — compares the instant
boolean expired = token.expiresAt().isBefore(clock.instant());
```

## 28.19 Do not decompose an `Instant`, `Duration`, or `Period` into its raw parts to do arithmetic.

> Why? `getEpochSecond()` plus `getNano()` looks like the whole value and is
> a trap: the nanosecond field is a *positive* remainder, so for instants
> before the epoch the naive `seconds * 1_000_000_000 + nanos`
> reconstruction is off by up to a second. `Duration.getSeconds()` has the
> same shape, and `Period.getDays()` returns only the day *component* — a
> `Period` of one month has zero days, so treating `getDays()` as a total
> silently reports 0. Use the total-value accessors (`toEpochMilli`,
> `toNanos`, `toMillis`) or `ChronoUnit.between`.
> **Violation — enforced by Error Prone `JavaInstantGetSecondsGetNano`,
> `JavaDurationGetSecondsGetNano`, and `JavaPeriodGetDays`.**

```java
// bad — wrong for pre-epoch instants, and getDays() is a component not a total
long nanos = instant.getEpochSecond() * 1_000_000_000L + instant.getNano();
int elapsedDays = Period.between(start, end).getDays(); // 0 for a whole month

// good
long millis = instant.toEpochMilli();
long elapsedDays = ChronoUnit.DAYS.between(start, end);
```

## 28.20 Expose `java.time` types in your own API rather than a `long` plus a `TimeUnit`.

> Why? A `long timeout, TimeUnit unit` pair is two parameters that can be
> passed in the wrong order, and a bare `long millis` has no unit at all —
> the caller who passes seconds gets a timeout a thousand times too short
> and no diagnostic. A `Duration` parameter carries its unit in the type,
> reads at the call site (`Duration.ofSeconds(30)`), and cannot be
> transposed. Where you must call a legacy API, convert at the boundary.
> **Violation — enforced by Error Prone `PreferJavaTimeOverload`.**

```java
// bad — unit lives in the parameter name, or in a second argument
public void awaitCompletion(long timeoutMillis) {}

public void awaitCompletion(long timeout, TimeUnit unit) {}

// good
public void awaitCompletion(Duration timeout) {}

// converting at a legacy boundary
legacyClient.setReadTimeout(Math.toIntExact(timeout.toMillis()));
```

## 28.21 Map database and wire columns to `java.time` types end to end.

> Why? A single `java.sql.Timestamp` anywhere in the chain reintroduces
> everything §28.1 removed — mutability, default-zone rendering, and a
> broken `equals` against `Date`. JDBC 4.2 maps `TIMESTAMP WITH TIME ZONE`
> to `OffsetDateTime` and `DATE` to `LocalDate` through
> `ResultSet.getObject(String, Class)`, and Jakarta Persistence 3.1 accepts
> `Instant`, `LocalDate`, `LocalDateTime`, and `OffsetDateTime` as basic
> attribute types without an `AttributeConverter`, so a JPA-mapped field can
> be declared `Instant` directly. Use those and the legacy types never enter
> the process. (Entity mapping itself is out of scope for this skill; the
> point here is only the column type.) **Suggestion.**

```java
// bad — a legacy type in the middle of an otherwise clean chain
Timestamp raw = resultSet.getTimestamp("placed_at");
Instant placedAt = raw.toInstant();

// good — the driver hands back a java.time value directly
Instant placedAt = resultSet.getObject("placed_at", OffsetDateTime.class).toInstant();
LocalDate settlementDate = resultSet.getObject("settles_on", LocalDate.class);
```

## 28.22 Configure the JSON layer to emit ISO-8601 strings, not epoch numbers.

> Why? Jackson's default for `java.time` types is a numeric timestamp,
> which is compact and unreadable: a support engineer looking at a captured
> payload cannot tell seconds from milliseconds, and a consumer in another
> language has to guess the unit and the precision. Registering
> `JavaTimeModule` and disabling `WRITE_DATES_AS_TIMESTAMPS` produces
> `"2024-01-01T00:00:00Z"`, which is self-describing. Spring Boot does both
> automatically when `jackson-datatype-jsr310` is on the classpath — verify
> it rather than assume it, because a hand-built `ObjectMapper` bypasses
> the auto-configuration ([Chapter 33](33-spring-configuration.md)).
> **Suggestion.**

```java
// bad — a hand-built mapper that emits 1704067200.000000000
ObjectMapper mapper = new ObjectMapper();

// good
ObjectMapper mapper =
    JsonMapper.builder()
        .addModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .build();
```

## 28.23 Keep the JVM, the containers, and the database in UTC, and treat the default zone as unset rather than as a value you may read.

> Why? Every rule above assumes the default zone is never consulted. Pinning
> the process to UTC (`TZ=UTC` in the container, `-Duser.timezone=UTC` on
> the JVM, the database session in UTC) turns any accidental default-zone
> read into a no-op rather than a silent regional bug, and makes logs from
> every host directly comparable. It is a safety net, not a substitute for
> §28.7 — code that reads the default zone is still wrong, it just fails
> less visibly. And never call `TimeZone.setDefault` from application code:
> it mutates a JVM-wide global that every other thread and library shares.
> **Suggestion.**

```java
// bad — mutates process-global state that every other component observes
TimeZone.setDefault(TimeZone.getTimeZone("UTC"));

// good — pin it outside the code, and assert it at startup if it matters
// Dockerfile:  ENV TZ=UTC
// JVM flag:    -Duser.timezone=UTC
@PostConstruct
void verifyUtc() {
  // normalized() collapses a fixed-offset zone to its ZoneOffset; comparing
  // the ZoneId directly would fail even under TZ=UTC, because the id of
  // ZoneId.of("UTC") is "UTC" and the id of ZoneOffset.UTC is "Z".
  ZoneId actual = ZoneId.systemDefault();
  if (!ZoneOffset.UTC.equals(actual.normalized())) {
    throw new IllegalStateException("JVM default zone must be UTC but was " + actual);
  }
}
```
