<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 21. Strings & Text Blocks

`String` is the type Java programmers reach for when they have not yet
decided what they are modeling. That reflex produces stringly-typed APIs,
quadratic concatenation loops, SQL injection, and locale bugs that only
reproduce for users in Turkey. This chapter is about resisting the reflex,
and about using the string API the JDK actually ships instead of the one
from 2004.

It covers when *not* to use a `String` at all, concatenation and its
performance cliff, the formatting options and when each is right, the
whitespace and line APIs added in Java 11–15, text blocks in full, string
comparison, locale-sensitive operations, and charset discipline at I/O
boundaries. It draws on **Effective Java, 3rd ed.**, Items 62 ("Avoid
strings where other types are more appropriate") and 63 ("Beware the
performance of string concatenation"), the
[Google Java Style Guide §4.8.9 Text blocks](https://google.github.io/styleguide/javaguide.html#s4.8.9-text-blocks)
and
[§2.3.3 Non-ASCII characters](https://google.github.io/styleguide/javaguide.html#s2.3.3-non-ascii-characters),
and the
[JDK 21 `String` API](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html).

Formatting log messages is deliberately deferred to
[Chapter 30](30-logging.md) — SLF4J placeholders are not `String.format`
and must not be conflated with it. Parsing and rendering dates is
[Chapter 28](28-dates-and-times.md). Enum design, which is the destination
for most of the strings this chapter tells you to stop using, is
[Chapter 15](15-enums-and-annotations.md).

**Tool alignment:** Checkstyle's `StringLiteralEquality` check flags `==`
and `!=` against a string literal, and Error Prone's `ReferenceEquality`
catches the general case; Error Prone's `StreamToString` catches a `Stream`
concatenated into a message. Rules those checks cover are marked
**Violation**; the rest are **Suggestions**.

## 21.1 Do not use a `String` where an enum, a record, or a numeric type says what you mean.

> Why? Effective Java, 3rd ed., Item 62: "Strings are poor substitutes for
> other value types." A `String` parameter accepts every misspelling, every
> wrong-case variant, and every value from an unrelated domain, so the
> compiler cannot help and every consumer has to re-validate. An enum makes
> the legal set closed and exhaustively switchable
> ([Chapter 23](23-control-structures-and-switch.md)); a record makes an
> aggregate a real type ([Chapter 12](12-records.md)).

```java
// bad — "DELIVERED", "delivered", and "DELIVRED" are all accepted
public void updateStatus(String orderId, String status) {
  if (status.equals("SHIPPED")) { }
}

// good
public enum OrderStatus {
  PENDING,
  SHIPPED,
  DELIVERED
}

public void updateStatus(OrderId orderId, OrderStatus status) {
  switch (status) {
    case SHIPPED -> notifyCarrier(orderId);
    case PENDING, DELIVERED -> {}
  }
}
```

## 21.2 Do not use a `String` as an aggregate type — no delimiter-joined composite keys.

> Why? Effective Java, 3rd ed., Item 62 again: "Strings are poor substitutes
> for aggregate types." A `tenantId + "#" + orderId` key is a parser waiting
> to fail the first time a tenant id contains `#`, it has no type safety at
> the call site, and every consumer must reimplement the split. A record with
> the two components costs one line and gets `equals`, `hashCode`, and
> `toString` for free — and is a safe `HashMap` key (see
> [Chapter 20, §20.18](20-collections.md)).

```java
// bad — a stringly-typed composite key
String key = tenantId + "#" + orderId;
cache.put(key, order);
// ... elsewhere, and wrong the moment tenantId contains '#'
String[] parts = key.split("#");

// good
record OrderKey(String tenantId, String orderId) {}

cache.put(new OrderKey(tenantId, orderId), order);
```

## 21.3 Never build a string by repeated `+=` in a loop.

> Why? Effective Java, 3rd ed., Item 63: "Using the string concatenation
> operator repeatedly to concatenate n strings requires time quadratic in
> n." Java strings are immutable, so each `+=` allocates a new string and
> copies every character accumulated so far. For a few dozen elements it is
> invisible; for a few thousand it is the profile's top frame.
> `StringBuilder` appends into a growable buffer in linear total time.

```java
// bad — O(n^2): every iteration reallocates and copies the whole result
String csv = "";
for (Order order : orders) {
  csv += order.id() + ",";
}

// good
StringBuilder csv = new StringBuilder();
for (Order order : orders) {
  csv.append(order.id()).append(',');
}
return csv.toString();

// better still — see 21.4; the delimiter logic disappears
return orders.stream().map(Order::id).collect(Collectors.joining(","));
```

## 21.4 Join a sequence with `String.join` or `Collectors.joining`, not manual delimiter bookkeeping.

> Why? Hand-rolled joining is where the trailing-comma bug and the
> `isFirst` boolean live. `String.join` handles an `Iterable<? extends
> CharSequence>` directly; `Collectors.joining` handles a stream and takes
> an optional prefix and suffix, so building `[a, b, c]` needs no manual
> trimming. `StringJoiner` is the imperative equivalent when you are
> appending in a loop that also does other work.

```java
// bad — trailing separator, then a fragile substring to remove it
StringBuilder sb = new StringBuilder();
for (String tag : tags) {
  sb.append(tag).append(", ");
}
String result = sb.substring(0, sb.length() - 2);

// good
String result = String.join(", ", tags);

// good — with delimiters, from a stream
String result =
    orders.stream().map(Order::id).collect(Collectors.joining(", ", "[", "]"));
```

## 21.5 Do not reach for `StringBuilder` for a fixed, small number of concatenations.

> Why? `javac` compiles a single `a + b + c` expression into one efficient
> concatenation (on Java 9+ via `invokedynamic` and
> `StringConcatFactory`), so hand-written `StringBuilder` chains for
> straight-line code are strictly more verbose with no benefit. Item 63's
> warning is about *repeated* concatenation in a loop, not about the `+`
> operator itself.

```java
// bad — hand-optimizing something javac already does
String label = new StringBuilder()
    .append(user.firstName())
    .append(' ')
    .append(user.lastName())
    .toString();

// good
String label = user.firstName() + " " + user.lastName();
```

## 21.6 Choose between `+`, `String.format`, `StringBuilder`, and a text block by what the string *is*.

> Why? Each tool has a domain where it is clearly right, and using the wrong
> one is the readability cost. `+` for a couple of pieces of straight-line
> text. `String.format` (or `formatted`) when there is genuine formatting —
> padding, precision, alignment — because the format string shows the shape
> of the output in one place. `StringBuilder` for accumulation in a loop.
> A text block for anything with embedded newlines. Note that
> `String.format` parses its format string at runtime, so it is the slowest
> of the four and does not belong on a hot path.

```java
// bad — formatting concerns smeared across concatenation
String row = padRight(name, 20) + " " + String.valueOf(amount).substring(0, 6);

// good — the output shape is legible in one place
String row = String.format(Locale.ROOT, "%-20s %8.2f", name, amount);

// good — Java 15+, when the format string is the subject of the sentence
String row = "%-20s %8.2f".formatted(name, amount);
```

## 21.7 Compare strings with `equals` or `equalsIgnoreCase`, never with `==`.

> Why? `==` on `String` compares references. It appears to work for
> compile-time constants because `javac` interns them into a shared pool,
> and then fails for the identical text read from a socket, a database, or
> `new String(...)`. The bug is doubly nasty because it passes every unit
> test that uses literals. **Violation — enforced by
> `checkstyle/StringLiteralEquality` and Error Prone `ReferenceEquality`.**

```java
// bad — true for a literal, false for the same text read from input
if (header == "application/json") { }

// good
if ("application/json".equals(header)) { }

// good — null-safe on both sides, no literal-first contortion
if (Objects.equals(header, expectedContentType)) { }
```

## 21.8 Do not call `String.intern()` to make `==` work.

> Why? Interning does not fix the design; it hides the reference-equality
> bug behind a global, JVM-wide table that every interned string stays in
> for the life of the process. Any string that reaches your code through a
> path you did not intern reintroduces the failure. Use `equals`, and if you
> need canonical instances for memory reasons, use an explicit
> `Map<String, String>` you control.

```java
// bad — a global side effect used to enable a comparison that should be equals
if (header.intern() == "application/json") { }

// good
if ("application/json".equals(header)) { }
```

## 21.9 Pass an explicit `Locale` to every case conversion and every format call.

> Why? `toUpperCase()` with no argument uses the JVM's default locale. In a
> Turkish locale (`tr`), `"i".toUpperCase()` returns `"İ"` (dotted capital
> I), so `"title".toUpperCase().equals("TITLE")` is *false* — the classic
> Turkish-I bug, which only reproduces on machines configured for that
> locale. Use `Locale.ROOT` for machine-facing text (protocol tokens,
> identifiers, keys) and the user's locale for user-facing text. The same
> applies to `String.format`, where the default locale decides the decimal
> separator.

```java
// bad — locale-dependent; breaks for tr, az, and lt users
if (scheme.toUpperCase().equals("HTTPS")) { }
String price = String.format("%.2f", amount);  // "1,50" in de-DE

// good — machine-facing text is locale-independent
if (scheme.toUpperCase(Locale.ROOT).equals("HTTPS")) { }
String price = String.format(Locale.ROOT, "%.2f", amount);

// better — no case conversion at all for an ASCII protocol token
if (scheme.equalsIgnoreCase("https")) { }

// good — user-facing text uses the user's locale, explicitly
String displayPrice = String.format(userLocale, "%.2f", amount);
```

## 21.10 Use `isBlank` and `strip`, not `isEmpty` and `trim`, when the intent is whitespace-insensitive.

> Why? `trim()` predates Unicode-aware whitespace: it removes only
> characters with a code point at or below `U+0020`, so a non-breaking space
> or an ideographic space survives it. `strip()` (Java 11) uses
> `Character.isWhitespace`, which is the definition a reader assumes.
> `isBlank()` is `strip().isEmpty()` without the allocation, and it says
> what the check means — `isEmpty()` on an un-stripped string returns
> `false` for `"   "`.

```java
// bad — a non-breaking space (U+00A0) survives trim(), and a string of
// ordinary spaces is not "empty"
if (input == null || input.trim().isEmpty()) {
  throw new IllegalArgumentException("input required");
}

// good
if (input == null || input.isBlank()) {
  throw new IllegalArgumentException("input required");
}

String normalized = input.strip();
```

## 21.11 Use `lines()` to iterate lines, not `split("\n")`.

> Why? `split("\n")` misses `\r\n` (Windows) and `\r` (classic Mac) line
> terminators, leaving stray carriage returns on the end of every element,
> and it materializes the whole array. `String.lines()` returns a
> `Stream<String>` that recognizes all three terminators and is lazy. It
> also drops a trailing empty line, which is almost always what you want for
> a file that ends in a newline.

```java
// bad — every element ends with '\r' on Windows-authored input
for (String line : payload.split("\n")) {
  process(line.trim());
}

// good
payload.lines().forEach(this::process);

// good — when you need a list
List<String> lines = payload.lines().toList();
```

## 21.12 Escape the delimiter, or avoid `split` entirely, when the separator is a regex metacharacter.

> Why? `String.split` takes a *regular expression*, not a literal. `"."`,
> `"|"`, `"*"`, `"+"`, `"("`, and `"["` all mean something else to the regex
> engine — `"a.b.c".split(".")` returns an empty array, because `.` matches
> every character. Use `Pattern.quote`, an escaped literal, or a non-regex
> method. And when a pattern is used more than once, compile it once into a
> `static final Pattern` rather than recompiling it on every call.

```java
// bad — returns an empty array; '.' is "any character"
String[] parts = version.split(".");

// good
String[] parts = version.split("\\.");

// good — no regex at all
int dot = version.indexOf('.');
String major = version.substring(0, dot);

// good — a reused pattern is compiled once
private static final Pattern SEMVER = Pattern.compile("^(\\d+)\\.(\\d+)\\.(\\d+)$");
```

## 21.13 Use a text block for any literal that contains newlines.

> Why? Google Java Style Guide
> [§4.8.9](https://google.github.io/styleguide/javaguide.html#s4.8.9-text-blocks):
> "The contents of a text block may exceed the column limit" — precisely so
> that embedded SQL, JSON, and HTML can be written in their natural shape.
> Escaped-newline concatenation hides the real structure of the payload
> behind `\n" +` noise, which is where mismatched quotes and missing spaces
> come from.

```java
// bad — the actual shape of the JSON is invisible
String body = "{\n"
    + "  \"orderId\": \"" + orderId + "\",\n"
    + "  \"status\": \"SHIPPED\"\n"
    + "}";

// good
String body =
    """
    {
      "orderId": "%s",
      "status": "SHIPPED"
    }
    """.formatted(orderId);
```

## 21.14 Control a text block's indentation with the position of the closing delimiter, and open the block on its own line.

> Why? Google Java Style Guide §4.8.9: "The opening `"""` of a text block is
> always on a new line", "The closing `"""` is on a new line with the same
> indentation as the opening `"""`", and "Each line of text in the text block
> is indented at least as much as the opening and closing `"""`." The compiler
> computes the common minimal indentation across all content lines *and the
> closing delimiter line*, then strips it as incidental whitespace. Pulling
> the closing delimiter to column 1 opts out of stripping entirely — which
> is almost never what you want inside an indented method, because it bakes
> the source indentation into the value.

```java
// bad — the closing delimiter at column 1 disables stripping, so every line
// of the value carries the method's source indentation
String query =
    """
        SELECT id FROM orders
        WHERE status = ?
""";
// value is "        SELECT id FROM orders\n        WHERE status = ?\n"

// good — the closing delimiter sets the margin; content lines align to it
String query =
    """
    SELECT id FROM orders
    WHERE status = ?
    """;
// value is "SELECT id FROM orders\nWHERE status = ?\n"

// good — indent the closing delimiter less than the content to keep a
// deliberate two-space indent in the value
String yaml =
    """
      key:
        nested: true
    """;
// value is "  key:\n    nested: true\n"
```

## 21.15 Know that a text block strips trailing whitespace, and use `\s` when you need it kept.

> Why? The compiler treats trailing whitespace on every line as incidental
> and removes it, so an editor that strips trailing spaces cannot silently
> change your string's value. The consequence is that you cannot express a
> line that genuinely ends in a space by typing one. The `\s` escape
> translates to a single space *after* stripping has run, so it acts as a
> fence that preserves everything to its left.

```java
// bad — the trailing spaces are silently removed, so the columns don't align
String table =
    """
    red
    green
    blue
    """;

// good — \s fences the trailing whitespace, so every line is 6 chars wide
String table =
    """
    red  \s
    green\s
    blue \s
    """;
```

## 21.16 Use the `\<line-terminator>` escape to wrap a long single-line value across source lines.

> Why? A text block inserts a newline at the end of every content line. When
> the value is logically one line that is simply too long for the column
> limit, the trailing-backslash escape suppresses that newline, so you get
> source-level wrapping without changing the value. The same escape on the
> last content line suppresses the final newline that a text block otherwise
> always adds.

```java
// bad — this value contains newlines the protocol does not allow
String userAgent =
    """
    AcmeClient/2.1
    (Linux; x86_64)
    Java/21
    """;

// good — \ suppresses the line break; the trailing \ also drops the final
// newline, so the value is exactly one line with no terminator
String userAgent =
    """
    AcmeClient/2.1 \
    (Linux; x86_64) \
    Java/21\
    """;
```

## 21.17 Never build SQL by concatenation or by interpolating into a text block — parameterize.

> Why? Every `+ userInput +` inside a query is an SQL injection. A text
> block does not change that: `"""SELECT ... WHERE id = '%s'""".formatted(id)`
> is exactly as injectable as the concatenated version, and the tidier
> formatting makes it look safer than it is. Bind parameters go through the
> driver as data and are never parsed as SQL. The text block is still the
> right way to *write* the query — with `?` placeholders.

```java
// bad — SQL injection, whether concatenated or interpolated into a block
String concatenated =
    "SELECT * FROM orders WHERE customer_id = '" + customerId + "'";
String interpolated =
    """
    SELECT * FROM orders WHERE customer_id = '%s'
    """.formatted(customerId);

// good — the text block carries the query shape, the driver carries the data
private static final String FIND_BY_CUSTOMER =
    """
    SELECT id, status, total
    FROM orders
    WHERE customer_id = ?
      AND status <> 'CANCELLED'
    ORDER BY created_at DESC
    """;

try (PreparedStatement stmt = connection.prepareStatement(FIND_BY_CUSTOMER)) {
  stmt.setString(1, customerId);
  try (ResultSet rs = stmt.executeQuery()) {
    return readOrders(rs);
  }
}
```

## 21.18 Never build HTML, JSON, XML, or a URL by string concatenation.

> Why? The same argument as 21.17, with different exploits: unescaped HTML
> is cross-site scripting, unescaped JSON is a parse failure or an injected
> field, and an unencoded query parameter silently truncates at the first
> `&`. Every one of these formats has a library that escapes correctly for
> its grammar, and the escaping rules are subtler than they look — HTML
> attribute context and HTML text context need different escapes.

```java
// bad — XSS if displayName contains "<script>", and a broken URL if the
// query contains '&'
String html = "<div class='name'>" + displayName + "</div>";
String url = "https://api.example.com/search?q=" + query;

// good — the serializer owns escaping for its grammar
String json = objectMapper.writeValueAsString(new SearchResult(displayName));

// good — the encoder owns percent-encoding
URI uri =
    URI.create(
        "https://api.example.com/search?q="
            + URLEncoder.encode(query, StandardCharsets.UTF_8));
```

## 21.19 Specify a `Charset` explicitly at every byte-to-string boundary.

> Why? Since JEP 400 (JDK 18) the JVM's default charset is UTF-8 — the
> [`Charset.defaultCharset` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/charset/Charset.html#defaultCharset())
> states "the default charset is `UTF-8`, unless changed in an
> implementation specific manner." But it *can* still be changed: launching
> with `-Dfile.encoding=COMPAT` derives it from `native.encoding` and
> reintroduces platform dependence. An explicit `StandardCharsets.UTF_8`
> costs nothing, survives that flag, and tells the reader which encoding the
> data actually is.

```java
// bad — depends on a JVM-wide setting a deployment can change
byte[] payload = body.getBytes();
String decoded = new String(bytes);
try (Reader reader = new FileReader(path.toFile())) { }

// good
byte[] payload = body.getBytes(StandardCharsets.UTF_8);
String decoded = new String(bytes, StandardCharsets.UTF_8);
String contents = Files.readString(path, StandardCharsets.UTF_8);
try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { }
```

## 21.20 Use `repeat`, `strip`, `indent`, and the other modern `String` methods instead of hand-rolled loops.

> Why? Java 11–15 added the string utilities that everyone previously
> imported a library for. `repeat(int)` replaces a `StringBuilder` loop,
> `stripIndent()` applies the text-block stripping algorithm to a runtime
> string, and `formatted(Object...)` puts the arguments after the template
> where they read naturally. Reimplementing these produces more code with
> more edge cases (`repeat(0)`, negative counts) and no upside.

```java
// bad
StringBuilder sep = new StringBuilder();
for (int i = 0; i < width; i++) {
  sep.append('-');
}
String separator = sep.toString();

// good
String separator = "-".repeat(width);
String banner = "=".repeat(3) + " done " + "=".repeat(3);
```

## 21.21 Do not concatenate a `Stream`, an array, or a lambda into a string.

> Why? `Stream`, `int[]`, and functional interfaces all inherit
> `Object.toString`, so concatenating one yields
> `java.util.stream.ReferencePipeline$Head@1b6d3586` — a debugging dead end,
> and for a `Stream` also a hint that the pipeline was never consumed.
> `Arrays.toString` / `Arrays.deepToString` handle arrays; a stream must be
> collected first. The `Stream` case is caught mechanically —
> **Violation — enforced by Error Prone `StreamToString`.** The array case is
> a **Suggestion**: no check catches it.

```java
// bad — logs an object identity, not the data
log.info("ids: " + ids.stream().map(Order::id));
throw new IllegalArgumentException("bad tags: " + tagArray);

// good
log.info("ids: {}", ids.stream().map(Order::id).toList());
throw new IllegalArgumentException("bad tags: " + Arrays.toString(tagArray));
```

## 21.22 Iterate code points, not `char` values, when the text can contain characters outside the Basic Multilingual Plane.

> Why? A Java `char` is a UTF-16 code unit, not a character. Emoji,
> historic scripts, and many CJK extension characters are encoded as
> surrogate *pairs*, so `chars()` and `charAt` split them in half:
> `"👍".length()` is 2, and iterating `chars()` yields two meaningless
> halves. `codePoints()` yields one `int` per actual character. This matters
> the moment user-supplied text reaches a truncation, a reversal, or a
> per-character validation.

```java
// bad — splits surrogate pairs; "length" is wrong for any non-BMP input
long letterCount = displayName.chars().filter(Character::isLetter).count();
String preview = displayName.substring(0, 10);  // can cut a pair in half

// good
long letterCount = displayName.codePoints().filter(Character::isLetter).count();
String preview =
    displayName.codePoints().limit(10)
        .collect(StringBuilder::new, StringBuilder::appendCodePoint,
            StringBuilder::append)
        .toString();
```

## 21.23 Keep non-ASCII characters in string literals as literal characters, not escapes, when they are printable.

> Why? Google Java Style Guide
> [§2.3.3](https://google.github.io/styleguide/javaguide.html#s2.3.3-non-ascii-characters)
> makes the criterion readability: use the actual Unicode character when it
> is printable, and a Unicode escape only for a non-printable character —
> with an explanatory comment. An escape like `\u221e` tells a reviewer
> nothing about what the string contains; the source file is UTF-8
> ([§2.2](https://google.github.io/styleguide/javaguide.html#s2.2-file-encoding)),
> so the character itself is safe to write.

```java
// bad — the reader has to look up each code point to know what this is
String infinity = "\u221e";
String microseconds = "\u00b5s";

// good
String infinity = "∞";
String microseconds = "µs";

// good — a non-printable character genuinely needs the escape, plus a comment
String softBreak = "\u200b";  // zero-width space, a soft break point
```
