<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 8. Strings

String handling in Go has a small number of high-leverage decisions: how
to build them up, how to format them, and how to avoid needless
conversions. This chapter draws from [Google Best Practices: String
concatenation](https://google.github.io/styleguide/go/best-practices#string-concatenation)
and Uber's guidance on [Use Raw String Literals to Avoid
Escaping](https://github.com/uber-go/guide/blob/master/style.md#use-raw-string-literals-to-avoid-escaping),
[Prefer strconv over
fmt](https://github.com/uber-go/guide/blob/master/style.md#prefer-strconv-over-fmt),
and avoiding repeated string-to-byte conversions. `strconv`/`fmt` choices
for numeric formatting overlap with constants in
[Chapter 9](09-constants.md).

## 8.1 Use `+` concatenation for a handful of known strings; switch to `strings.Builder` once you're accumulating in a loop.

> Why? `+` is perfectly efficient and readable for concatenating a
> small, fixed number of strings. Once concatenation happens inside a
> loop, each `+` allocates a new string, and cost grows quadratically
> with iteration count — `strings.Builder` accumulates into a single
> growable buffer instead
> ([Best Practices: String
> concatenation](https://google.github.io/styleguide/go/best-practices#string-concatenation)).

```go
// bad — quadratic allocations as the loop grows
func JoinNames(names []string) string {
	var result string
	for _, n := range names {
		result += n + ", "
	}
	return result
}

// good
func JoinNames(names []string) string {
	var b strings.Builder
	for _, n := range names {
		b.WriteString(n)
		b.WriteString(", ")
	}
	return b.String()
}

// good — fine to use + for a small, fixed number of strings
greeting := "Hello, " + name + "!"
```

## 8.2 Reach for `strings.Builder`, not `bytes.Buffer`, when the end product is a string.

> Why? `strings.Builder` is purpose-built for accumulating into a
> `string` result and avoids an extra copy that `bytes.Buffer.String()`
> would otherwise require internally. Use `bytes.Buffer` only when you
> genuinely need `[]byte` semantics (e.g. writing to an `io.Writer` that
> expects bytes)
> ([Best Practices: String
> concatenation](https://google.github.io/styleguide/go/best-practices#string-concatenation)).

```go
// bad — bytes.Buffer used purely to produce a string
func BuildCSVLine(fields []string) string {
	var buf bytes.Buffer
	for i, f := range fields {
		if i > 0 {
			buf.WriteByte(',')
		}
		buf.WriteString(f)
	}
	return buf.String()
}

// good
func BuildCSVLine(fields []string) string {
	var b strings.Builder
	for i, f := range fields {
		if i > 0 {
			b.WriteByte(',')
		}
		b.WriteString(f)
	}
	return b.String()
}
```

## 8.3 Use `fmt.Sprintf` when the result mixes literal text with formatted values.

> Why? `fmt.Sprintf` is the right tool once you're interpolating
> multiple typed values into a template string — trying to do the same
> with manual concatenation and `strconv` calls is harder to read and
> easier to get wrong
> ([Best Practices: String
> concatenation](https://google.github.io/styleguide/go/best-practices#string-concatenation)).

```go
// bad — manual concatenation of mixed types
msg := "user " + userID + " retried " + strconv.Itoa(retries) + " times"

// good
msg := fmt.Sprintf("user %s retried %d times", userID, retries)
```

## 8.4 Use raw string literals (`` `...` ``) for text containing backslashes or quotes, instead of escaping them.

> Why? Regular expressions, Windows file paths, and JSON snippets are
> full of characters that need escaping in an interpreted string
> literal. A raw string literal removes the need for any escaping,
> which makes the content visibly correct at a glance
> ([Uber Style: Use Raw String Literals to Avoid
> Escaping](https://github.com/uber-go/guide/blob/master/style.md#use-raw-string-literals-to-avoid-escaping)).

```go
// bad — heavily escaped, hard to visually verify
pattern := "^\\d{3}-\\d{2}-\\d{4}$"
path := "C:\\Users\\ana\\config.json"

// good
pattern := `^\d{3}-\d{2}-\d{4}$`
path := `C:\Users\ana\config.json`
```

## 8.5 Prefer `strconv` over `fmt.Sprintf` for simple type-to-string conversions.

> Why? `fmt.Sprintf("%d", n)` goes through the `fmt` package's
> reflection-based formatting machinery, which is measurably slower than
> `strconv.Itoa(n)` for the common case of converting a single primitive
> value. Reach for `strconv` when there's no template text to fill in
> ([Uber Style: Prefer strconv over
> fmt](https://github.com/uber-go/guide/blob/master/style.md#prefer-strconv-over-fmt)).

```go
// bad — reflection overhead for a single int-to-string conversion
id := fmt.Sprintf("%d", userID)

// good
id := strconv.Itoa(userID)
```

## 8.6 Use `strconv.ParseInt`/`ParseFloat`/`ParseBool` to parse strings into typed values, not `fmt.Sscanf`.

> Why? `strconv`'s parse functions return a clear `error` for malformed
> input and avoid `fmt.Sscanf`'s format-string parsing overhead and
> looser error reporting
> ([Uber Style: Prefer strconv over
> fmt](https://github.com/uber-go/guide/blob/master/style.md#prefer-strconv-over-fmt)).

```go
// bad
var n int
if _, err := fmt.Sscanf(input, "%d", &n); err != nil {
	return err
}

// good
n, err := strconv.Atoi(input)
if err != nil {
	return err
}
```

## 8.7 Avoid repeated `[]byte(s)` / `string(b)` conversions inside loops or hot paths.

> Why? Converting between `string` and `[]byte` copies the underlying
> data every time. Doing this conversion once outside a loop — instead
> of on every iteration — avoids repeated, unnecessary allocations
> ([Uber Style: Avoid repeated string-to-byte
> conversions](https://github.com/uber-go/guide/blob/master/style.md#avoid-string-to-byte-conversion-outside-tight-loops)).

```go
// bad — converts s to []byte on every iteration
for i := 0; i < maxAttempts; i++ {
	if bytes.Contains([]byte(s), []byte(needle)) {
		break
	}
}

// good — convert once, reuse
data := []byte(s)
target := []byte(needle)
for i := 0; i < maxAttempts; i++ {
	if bytes.Contains(data, target) {
		break
	}
}

// good — better still: strings.Contains needs no conversion at all
for i := 0; i < maxAttempts; i++ {
	if strings.Contains(s, needle) {
		break
	}
}
```

## 8.8 Compare strings with `==`/`strings.EqualFold`, not by converting both sides to the same case with `strings.ToUpper`/`ToLower` first for exact comparisons.

> Why? `strings.ToLower(a) == strings.ToLower(b)` allocates two new
> strings just to compare them. When you need a case-insensitive
> comparison, `strings.EqualFold` does it without any allocation.

```go
// bad — allocates two lowercased copies just to compare
if strings.ToLower(username) == strings.ToLower(input) {
	// match
}

// good
if strings.EqualFold(username, input) {
	// match
}
```

## 8.9 Use `strings.Contains`/`HasPrefix`/`HasSuffix` instead of manual index arithmetic or regular expressions for simple checks.

> Why? `strings` package functions are optimized, well-tested, and
> communicate intent directly. Reaching for `regexp` or manual
> `strings.Index` arithmetic for a plain substring or prefix check adds
> unnecessary complexity and a slower code path.

```go
// bad — regexp for a plain prefix check
matched, _ := regexp.MatchString("^https://", url)
if matched {
	// ...
}

// good
if strings.HasPrefix(url, "https://") {
	// ...
}
```

## 8.10 Build multi-line string templates with backtick raw strings, not chained `\n` concatenation.

> Why? A raw string literal spanning multiple lines in the source is
> visually identical to its output, whereas concatenating
> `"line one\n" + "line two\n"` forces the reader to mentally render the
> escape sequences
> ([Uber Style: Use Raw String Literals to Avoid
> Escaping](https://github.com/uber-go/guide/blob/master/style.md#use-raw-string-literals-to-avoid-escaping)).

```go
// bad
usage := "Usage: widget [flags]\n" +
	"\n" +
	"Flags:\n" +
	"  -v  verbose output\n"

// good
usage := `Usage: widget [flags]

Flags:
  -v  verbose output
`
```
