<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 21. Strings

Kotlin's string support is one of the places where the language most clearly
diverges from Java, and where Java habits transfer most destructively. `==` is
structural, not referential. Raw strings process no escape sequences at all.
`String(bytes)` is UTF-8 rather than the platform default. A template makes
concatenation obsolete but also makes injection effortless. Every one of those
differences produces a distinct class of bug when a Java programmer writes
Kotlin on autopilot.

This chapter draws on the Kotlin coding conventions'
[Strings](https://kotlinlang.org/docs/coding-conventions.html#strings) and
[String templates](https://kotlinlang.org/docs/coding-conventions.html#string-templates)
sections, the Android Kotlin style guide's
[special escape sequences](https://developer.android.com/kotlin/style-guide#special_escape_sequences)
and [non-ASCII characters](https://developer.android.com/kotlin/style-guide#non-ascii_characters)
rules, and the language documentation's
[Strings](https://kotlinlang.org/docs/strings.html) page for `trimIndent`,
`trimMargin`, and multi-dollar interpolation.

Two topics are deferred. The general treatment of `==`, `===`, `equals`,
`hashCode`, and `Comparable` — including locale-aware ordering with
`java.text.Collator`, which `String.compareTo` does not give you — is
[Chapter 23, Equality & Ordering](23-equality-and-ordering.md); §21.11 covers
only the string-specific Java trap. Structured logging, lazy message
evaluation, and what must never reach a log line is
[Chapter 31, Logging](31-logging.md).

**Tool alignment:** ktlint's `standard:string-template` rewrites `${v}` to `$v`
for bare identifiers, and `standard:string-template-indent` normalises the
indentation of a `trimIndent()`-terminated raw string. detekt's
`style/StringShouldBeRawString`, `style/TrimMultilineRawString`,
`style/MultilineRawStringIndentation`, `style/UseIfEmptyOrIfBlank`,
`style/UseIsNullOrEmpty`, `potential-bugs/ImplicitDefaultLocale`,
`potential-bugs/AvoidReferentialEquality`, and
`potential-bugs/NullableToStringCall` cover most of the rest. Rules a named
check enforces are marked **Violation**; the rest are **Suggestion**.

## 21.1 Use a string template, never `+` concatenation.

> Why? The coding conventions state it in four words: "Prefer string templates to
> string concatenation." Concatenation splits one sentence across five operators
> and eight quote characters, so the shape of the resulting message is invisible
> until you mentally evaluate it — and a missing space between two fragments is
> genuinely hard to see in review. **Suggestion.**

```kotlin
// bad — the resulting sentence is not visible anywhere in the source
val message = "user " + user.id + " placed order " + order.id + " for " + total

// good — the sentence reads as a sentence
val message = "user ${user.id} placed order ${order.id} for $total"
```

## 21.2 Omit the braces when interpolating a bare identifier; use them only for an expression.

> Why? The coding conventions are explicit: "Don't use curly braces when
> inserting a simple variable into a string template. Use curly braces only for
> longer expressions," with `"$name has ${children.size} children"` as the
> canonical example. Beyond consistency, the braces become a signal: once
> `${...}` means "something is being computed here", a reader can skim a template
> and see exactly where the logic is.
> **Violation — enforced by `ktlint standard:string-template`.**

```kotlin
// bad — braces around bare identifiers erase the signal that ${...} carries
println("${name} has ${children.size} children")
val path = "${base}/${segment}"

// good
println("$name has ${children.size} children")
val path = "$base/$segment"
```

## 21.3 Extract a complex template expression into a named local.

> Why? A template is read left to right as prose; an expression inside it is read
> inside out as code. Nesting a `sumOf` with its own lambda, or a search over a
> collection, inside `${...}` forces the reader to switch modes mid-sentence, and
> it hides real cost (see [Chapter 20, §20.11](20-collections-and-sequences.md))
> inside what looks like formatting. Compute first, interpolate second: the local
> gets a name, which is the documentation the inline version was missing.
> **Suggestion.**

```kotlin
// bad — two nested lambdas and an O(n) scan inside a log message
logger.info {
    "order ${order.id} totalling ${order.lines.sumOf { it.amountMinor } / 100.0} " +
        "for ${customers.first { it.id == order.customerId }.displayName}"
}

// good — each value is named, and the template is just a template
val totalMajor = order.lines.sumOf { it.amountMinor } / 100.0
val customerName = customersById.getValue(order.customerId).displayName
logger.info { "order ${order.id} totalling $totalMajor for $customerName" }
```

## 21.4 Use a raw string instead of an escape-dense literal.

> Why? The coding conventions say to "prefer multiline strings to embedding `\n`
> escape sequences into regular string literals," and detekt reports "when the
> string can be converted to Kotlin raw string." An escaped SQL statement or JSON
> body is unreadable in the editor, undiffable in review, and impossible to paste
> into a database console without hand-unescaping it. A raw string shows the
> artefact in its real shape. Note that raw strings process *no* escape sequences
> at all — there is no `\n`, no `\"`, and no `\$` inside one.
> **Violation — enforced by `detekt/StringShouldBeRawString`.**

```kotlin
// bad — the shape of the query is invisible, and one missing \n breaks it silently
val sql = "SELECT id, email\nFROM users\nWHERE tenant_id = ?\n  AND deleted_at IS NULL"

// good — the query looks like the query
val sql = """
    SELECT id, email
    FROM users
    WHERE tenant_id = ?
      AND deleted_at IS NULL
""".trimIndent()
```

## 21.5 Always terminate a multiline raw string with `trimIndent()` or `trimMargin()`.

> Why? Without one, the string carries the source file's indentation into the
> value: a raw string nested three blocks deep silently gains twelve leading
> spaces on every line, and the value changes the next time someone extracts the
> enclosing code into a method. detekt states it flatly: "All the Raw strings that
> have more than one line should be followed by `trimMargin()` or `trimIndent()`."
> **Violation — enforced by `detekt/TrimMultilineRawString`.**
> `detekt/MultilineRawStringIndentation` and
> `ktlint standard:string-template-indent` (which runs only under the
> `ktlint_official` code style, or when enabled explicitly) cover the indentation
> itself.

```kotlin
// bad — the value depends on where in the file this happens to sit
fun body(): String =
    """
        {"status": "ok"}
    """

// good
fun body(): String =
    """
        {"status": "ok"}
    """.trimIndent()
```

## 21.6 Know that `trimIndent()` drops the first and last blank lines — add an extra blank line when you need a trailing newline.

> Why? The stdlib documents `trimIndent` as removing the common indent "and also
> [removing] the first and the last lines if they are blank." That is almost
> always what you want for the leading newline after the opening `"""` — and
> almost never noticed for the trailing one. The result is a file, HTTP body, or
> config blob written without its terminating newline, which breaks POSIX text
> tools and `diff` in ways that are tedious to trace back to a string literal.
> **Suggestion.**

```kotlin
// bad — the author expected a trailing newline; trimIndent removed the blank
// last line, so this writes "a\nb" with no terminator
val body = """
    a
    b
""".trimIndent()
file.writeText(body, Charsets.UTF_8)

// good — one extra blank line survives as the trailing "\n"
val body = """
    a
    b

""".trimIndent()

// good — or stop relying on the literal's shape entirely
val body = listOf("a", "b").joinToString(separator = "\n", postfix = "\n")
```

## 21.7 Use `trimMargin()` when any line may sit flush left, or when internal indentation is meaningful.

> Why? The coding conventions draw the line precisely: use "`trimIndent` when the
> resulting string does not require any internal indentation, or `trimMargin`
> when internal indentation is required." The failure mode is documented in
> `trimIndent`'s own KDoc: "In case if there are non-blank lines with no leading
> whitespace characters (no indent at all) then the common indent is 0, and
> therefore this function doesn't change the indentation." One flush-left line —
> a comment, a heredoc marker, a YAML document separator — silently disables the
> entire trim and ships the source indentation. `trimMargin` pins the left edge
> explicitly and cannot be defeated this way. **Suggestion.**

```kotlin
// bad — the flush-left comment makes the common indent 0, so trimIndent strips
// nothing and every line keeps its four leading spaces
val yaml = """
    server:
      port: 8080
# operator note: do not change the port
""".trimIndent()

// good — the margin prefix states the left edge, so no line can move it
val yaml = """
    |server:
    |  port: 8080
    |# operator note: do not change the port
""".trimMargin()
```

## 21.8 Use multi-dollar interpolation for text that contains literal dollar signs.

> Why? JSON Schema, jq paths, shell fragments, and regular expressions are full
> of `$`, and a raw string cannot escape it — `\$` inside `"""` emits a backslash
> followed by a dollar, because raw strings process no escapes. That leaves the
> `${'$'}` incantation, which is an entire interpolation used to emit one
> character and which the coding conventions now supersede: "Use multi-dollar
> string interpolation to treat the dollar sign chars `$` as string literals."
> Prefixing the literal with `$$` makes a single `$` literal and `$$` the
> interpolation opener. Multi-dollar interpolation has been **Stable since
> Kotlin 2.2**, so it needs no opt-in flag. **Suggestion.**

```kotlin
// bad — an interpolation whose only job is to emit one character
val jqPath = "${'$'}.items[0].id"

// bad — the same trick repeated across a document; note that `\$` would NOT
// work here, because raw strings have no escape sequences
val schema = """
    {
      "${'$'}schema": "https://json-schema.org/draft/2020-12/schema",
      "${'$'}id": "https://example.com/product.schema.json",
      "title": "$title"
    }
""".trimIndent()

// good — one `$` is a literal, `$$` opens an interpolation
val jqPath = $$"""$.items[0].id"""

val schema = $$"""
    {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "https://example.com/product.schema.json",
      "title": "$$title"
    }
""".trimIndent()
```

## 21.9 Build a string in a loop with `buildString`, never with `+=`.

> Why? `String` is immutable, so `out += part` allocates a new `String` and
> copies every character accumulated so far. Over `n` iterations that is O(n²)
> copying and `n` throwaway objects, and nothing at the call site hints at it —
> the operator looks like appending. `buildString` gives the block a
> `StringBuilder` receiver and returns the finished `String`, so the mutable
> buffer never escapes. **Suggestion.**

```kotlin
// bad — quadratic copying; one discarded String per iteration
fun render(lines: List<Line>): String {
    var out = ""
    for (line in lines) {
        out += "${line.sku} x${line.qty}\n"
    }
    return out
}

// good — a single buffer, scoped to the builder block
fun render(lines: List<Line>): String = buildString {
    for (line in lines) {
        append(line.sku).append(" x").append(line.qty).append('\n')
    }
}

// good — when you are simply joining, say so (see 21.10)
fun render(lines: List<Line>): String =
    lines.joinToString(separator = "\n") { "${it.sku} x${it.qty}" }
```

## 21.10 Join with `joinToString` and use its `prefix`, `postfix`, `limit`, and `truncated` parameters.

> Why? Hand-rolled joining means hand-rolled separator bookkeeping — the
> `if (i > 0) append(", ")` that is wrong on empty input roughly half the time —
> plus hand-rolled truncation for anything that might be logged. `joinToString`
> has all of it built in: `separator` (default `", "`), `prefix`, `postfix`,
> `limit` (default `-1`, meaning no limit), and `truncated` (default `"..."`).
> Naming them at the call site also documents the output format. **Suggestion.**

```kotlin
// bad — manual separators, manual brackets, manual truncation
val label = StringBuilder("[")
for ((i, id) in ids.withIndex()) {
    if (i > 0) {
        label.append(", ")
    }
    if (i == 5) {
        label.append("...")
        break
    }
    label.append(id)
}
label.append("]")

// good
val label = ids.joinToString(prefix = "[", postfix = "]", limit = 5, truncated = "...")
```

## 21.11 Compare strings with `==`, which is structural in Kotlin; never with `===`.

> Why? This is the single most dangerous Java habit to carry into Kotlin, and it
> runs both ways. In Java `==` on `String` is reference identity, which is why
> `equals` is drilled into every Java programmer; in Kotlin `a == b` compiles to
> `a?.equals(b) ?: (b === null)`, so it is structural *and* null-safe on the left.
> Meanwhile `===` still means reference identity, so a Java programmer reaching
> for "the strict one" gets a comparison that happens to pass in tests — where
> the literals are interned — and fails in production, where the string came off
> a socket. detekt's `AvoidReferentialEquality` defaults to flagging exactly
> `kotlin.String`.
> **Violation — enforced by `detekt/AvoidReferentialEquality`.** See
> [Chapter 23, Equality & Ordering](23-equality-and-ordering.md).

```kotlin
// bad — reference identity; true for interned literals, false for parsed input
if (input === "admin") { /* ... */ }

// bad — the Java form transliterated; correct but noisy, and NOT null-safe on
// a nullable receiver without a safe call
if (input.equals("admin")) { /* ... */ }

// good — structural, null-safe, and what every Kotlin reader expects
if (input == "admin") { /* ... */ }
```

## 21.12 Use `equals(other, ignoreCase = true)` rather than lowercasing both sides.

> Why? `a.lowercase() == b.lowercase()` allocates two strings to answer a boolean
> question, and — far worse — drags the default locale into a comparison that has
> nothing to do with locale (see §21.13). The `ignoreCase` parameter performs
> per-character case folding without consulting any `Locale`, allocates nothing,
> and short-circuits on the first mismatch. The same parameter exists on
> `startsWith`, `endsWith`, `contains`, `replace`, and `split`, so the lowercasing
> workaround is almost never needed. **Suggestion.**

```kotlin
// bad — two allocations, and the default locale decides what "lowercase" means
if (header.lowercase() == "content-type") { /* ... */ }

// good — no allocation, no locale, short-circuits
if (header.equals("content-type", ignoreCase = true)) { /* ... */ }

// good — the same parameter on the operations you would otherwise lowercase for
if (path.startsWith("/api/", ignoreCase = true)) { /* ... */ }
val redacted = body.replace("password", "***", ignoreCase = true)
```

## 21.13 Pass an explicit `Locale` to every case conversion and every `format` call.

> Why? `lowercase()` and `uppercase()` without an argument use
> `Locale.getDefault()`, which is a property of the machine the JVM happens to be
> running on. Under a Turkish default locale `"ID".lowercase()` is `"ıd"` — a
> dotless i — so a header comparison, a config key lookup, or an enum parse
> silently stops matching, and reproduces on exactly one region's servers. The
> same applies to `String.format`, where the default locale decides whether a
> decimal separator is `.` or `,` and therefore whether the JSON you emit parses.
> Use `Locale.ROOT` for anything machine-readable and the user's locale,
> explicitly, for anything a human reads.
> **Violation — enforced by `detekt/ImplicitDefaultLocale`.**

```kotlin
import java.util.Locale

// bad — the machine's default locale decides the result
if (header.lowercase() == "id") { /* never matches under tr-TR */ }
val code = countryCode.uppercase()
val amount = "%.2f".format(price)

// good — Locale.ROOT for machine-readable text
val code = countryCode.uppercase(Locale.ROOT)
val amount = "%.2f".format(Locale.ROOT, price)

// good — the user's locale, named, for anything a human reads
val shown = title.lowercase(userLocale)
val displayAmount = "%,.2f".format(userLocale, price)
```

## 21.14 Never build SQL, HTML, or a shell command by interpolation.

> Why? A string template is exactly as good at building an injection payload as
> it is at building a message, and it is more dangerous than Java concatenation
> because it reads so naturally that reviewers stop seeing the boundary between
> code and data. A tenant name of `' OR 1=1 --` reads every row; a comment body
> containing `<script>` executes in every viewer's browser; an author string
> containing `; rm -rf /` runs when the command goes through a shell. Bind
> parameters, escape through the template engine, and pass argv as a list so no
> shell ever parses it. **Suggestion** — no linter can tell a query from a
> message; `detekt/ForbiddenMethodCall` can be configured to ban the specific
> sinks (`java.sql.Statement.executeQuery`, `java.lang.Runtime.exec`) if you want
> mechanical coverage.

```kotlin
// bad — SQL injection: a tenant named "' OR 1=1 --" reads every row
val sql = "SELECT * FROM users WHERE tenant = '$tenant'"
statement.executeQuery(sql)

// bad — the same hole in HTML and in a shell command
val html = "<div>${comment.body}</div>"
Runtime.getRuntime().exec("git log --author=$author")

// good — bind parameters; the driver never parses the value as SQL
connection.prepareStatement("SELECT * FROM users WHERE tenant = ?").use { statement ->
    statement.setString(1, tenant)
    statement.executeQuery()
}

// good — let the renderer escape, and hand the process an argv list
val html = renderer.render("comment", mapOf("body" to comment.body))
ProcessBuilder(listOf("git", "log", "--author=$author")).start()
```

## 21.15 Distinguish `isBlank()` from `isEmpty()`, and use `isNullOrBlank()` / `ifBlank { }` instead of hand-rolled checks.

> Why? `isEmpty()` is true only for the zero-length string; `isBlank()` is also
> true for `"   "`, `"\t"`, and `"\n"`. Almost every validation of user input
> wants `isBlank`, and almost every one written from Java habit gets `isEmpty` —
> so a required field passes validation when it contains three spaces. The
> combined helpers exist for the same reason: detekt flags
> `x == null || x.isEmpty()` in favour of `isNullOrEmpty()`, and
> `if (s.isBlank()) "foo" else s` in favour of `s.ifBlank { "foo" }`.
> **Violation — enforced by `detekt/UseIsNullOrEmpty` and
> `detekt/UseIfEmptyOrIfBlank`.**

```kotlin
// bad — a field containing "   " passes this check
if (name.isEmpty()) return error("name is required")

// bad — the manual null-and-empty dance
if (input == null || input.isEmpty()) return

// bad — an if-else whose only job is to substitute a default
val label = if (title.isBlank()) "untitled" else title

// good
if (name.isBlank()) return error("name is required")
if (input.isNullOrBlank()) return // isNullOrEmpty() when empty really is the test
val label = title.ifBlank { "untitled" }
```

## 21.16 Never interpolate a nullable value without deciding what `null` should render as.

> Why? `"$middleName"` on a null value emits the four characters `null` into
> whatever the string is for — a user-facing name, a log line that a parser
> consumes, a cache key. Nothing warns, because interpolation calls `toString()`
> on `Any?` and that is a legal thing to do. detekt's rule exists precisely to
> report "`toString()` calls with a nullable receiver that may return the string
> `null`". Decide at the point where the null exists, not downstream in a bug
> report. **Violation — enforced by `detekt/NullableToStringCall`** for the
> explicit `toString()` form; the bare-template form is a **Suggestion**.

```kotlin
// bad — a null middleName renders "null" into a user-facing string
val display = "$firstName $middleName $lastName"

// bad — the explicit form of the same mistake
logger.info { "correlation=" + correlationId.toString() }

// good — the absent value is handled where it is absent
val display = listOfNotNull(firstName, middleName, lastName).joinToString(" ")
logger.info { "correlation=${correlationId ?: "none"}" }
```

## 21.17 Use a `Char` where a single character is meant, not a one-character `String`.

> Why? `Char` is a primitive on the JVM, so a `Char` overload compares and
> appends without allocating or without a length check on a `String` that the
> compiler already knows has length one. `startsWith`, `endsWith`, `split`,
> `indexOf`, `substringBefore`, `substringAfter`, `trim`, and
> `StringBuilder.append` all have `Char` overloads. Indexing a `String` yields a
> `Char`, so a mixed style also produces the confusing `line[0] == "#"` — which
> does not compile — or `line[0].toString() == "#"`, which allocates to answer a
> question `Char` equality answers for free. **Suggestion.**

```kotlin
// bad — one-character Strings where Chars exist
if (path.startsWith("/")) { /* ... */ }
val parts = csv.split(",")
builder.append("\n")
if (line.isNotEmpty() && line[0].toString() == "#") { /* ... */ }

// good
if (path.startsWith('/')) { /* ... */ }
val parts = csv.split(',')
builder.append('\n')
if (line.isNotEmpty() && line[0] == '#') { /* ... */ }
```

## 21.18 Split with the operation that matches the intent — `lines()`, a `Char` delimiter, or an explicit `limit`.

> Why? Three distinct mistakes hide in `split`. Compiling a `Regex` to split on a
> literal is wasted work and turns metacharacters into landmines — `split(Regex("."))`
> matches every single character and hands back a list of empty strings, whereas the
> `String`-delimiter overload `split(".")` splits on a literal dot; the two spellings
> look alike and behave nothing alike. Splitting text on `"\n"` leaves a stray `\r`
> on the end of every line of a CRLF file, whereas `lines()` handles `\r\n`, `\n`,
> and `\r`. And
> splitting a value that may itself contain the delimiter without a `limit`
> quietly produces the wrong number of parts, so a destructuring declaration
> throws `IndexOutOfBoundsException` at runtime. When you want a prefix or a
> suffix rather than a partition, say so with `substringBefore` /
> `substringAfterLast`, which take a `missingDelimiterValue`. **Suggestion.**

```kotlin
// bad — a Regex for a literal, a line split that breaks on CRLF, and a
// destructuring that throws when the input has no "@"
val fields = record.split(Regex("\\|"))
val rows = text.split("\n")
val (user, host) = email.split("@")

// good
val fields = record.split('|')
val rows = text.lines()
val user = email.substringBeforeLast('@')
val host = email.substringAfterLast('@', missingDelimiterValue = "")
```

## 21.19 Name the `Charset` at every boundary between bytes and text.

> Why? Kotlin's own helpers already default to UTF-8 — `String(bytes)`,
> `String.toByteArray()`, `File.readText()`, and `InputStream.bufferedReader()`
> all do — which is exactly why this rule is easy to forget: the danger begins
> the moment you drop into a Java type. `InputStreamReader(stream)`,
> `FileReader`, `FileWriter`, `PrintWriter(file)`, `Scanner(stream)`, and
> `java.lang.String(byte[])` all use `Charset.defaultCharset()`. JEP 400 made
> that UTF-8 by default from JDK 18 onward, but it is still overridable with
> `-Dfile.encoding`, still the platform encoding on older JDKs, and still not
> what `System.console()` uses. A pipeline that round-trips correctly on a
> developer's machine can therefore mangle every non-ASCII byte in a container
> configured differently, silently. Naming the charset costs six characters and
> removes the reader's need to know which default applies where. Also note that
> `URLEncoder.encode(String)` — the one-argument overload — is deprecated
> precisely for this reason. **Suggestion.**

```kotlin
// bad — every one of these takes the platform default charset
val text = InputStreamReader(stream).readText()
val report = Scanner(process.inputStream).useDelimiter("\\A").next()
val encoded = URLEncoder.encode(value)
FileWriter(file).use { it.write(report) }

// good — an explicit Charset at every boundary, in both directions
val text = stream.reader(Charsets.UTF_8).use { it.readText() }
val encoded = URLEncoder.encode(value, Charsets.UTF_8)
file.writeText(report, Charsets.UTF_8)

val bytes: ByteArray = payload.toByteArray(Charsets.UTF_8)
val roundTripped: String = bytes.toString(Charsets.UTF_8)
```

## 21.20 Use the special escape sequence for a character that has one, and the actual character for printable non-ASCII.

> Why? The Android Kotlin style guide legislates both halves. On escapes: "For
> any character that has a special escape sequence (`\b`, `\n`, `\r`, `\t`,
> `\'`, `\"`, `\\`, and `\$`), that sequence is used rather than the
> corresponding Unicode (e.g., `\u000a`) escape." On everything else: "Unicode
> escapes are discouraged for printable characters at any location," and the
> guide's own worked example ranks `val unitAbbrev = "μs"` as "best:
> perfectly clear even without a comment" against `val unitAbbrev =
> "\u03bcs"` as "poor: the reader has no idea what this is." Escapes earn
> their place only for characters you cannot see. **Suggestion.**

```kotlin
// bad — a Unicode escape where a special escape sequence exists
val separator = "\u000a"

// bad — a Unicode escape for a printable character; unreadable at the call site
val unitAbbrev = "\u03bcs"

// good
val separator = "\n"
val unitAbbrev = "μs"

// good — an escape is right for a non-printable character, and a comment helps
val byteOrderMark = "\ufeff"
```
