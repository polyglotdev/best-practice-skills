<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 16. Errors

Errors in Go are ordinary values, created and consumed by ordinary code —
there is no exception mechanism to opt into or out of. This chapter draws
from [Google Style Decisions:
Errors](https://google.github.io/styleguide/go/decisions#errors), [Google
Best Practices: Errors](https://google.github.io/styleguide/go/best-practices#errors),
[Effective Go: Errors](https://go.dev/doc/effective_go#errors), and [Uber
Style: Errors](https://github.com/uber-go/guide/blob/master/style.md#errors)
and [Handle Errors
Once](https://github.com/uber-go/guide/blob/master/style.md#handle-errors-once).
It covers how to construct, wrap, and compare error values. What to *do*
with an error once you have one — propagate, log, or handle — is covered in
[Chapter 17](17-error-handling.md); this chapter is about error value
design.

**Linter alignment:** several rules below are compiled-checked by this
project's `errorlint` (`errorf: true`, `asserts: true`, `comparison: true`)
and `revive` (`error-naming`, `error-return`) settings — see
`.golangci.yml`. Where a rule is enforced, it's marked **Violation** rather
than **Suggestion**.

## 16.1 Return `error` as the last result value of any function that can fail.

> Why? [Google Style Decisions:
> Errors](https://google.github.io/styleguide/go/decisions#errors)
> establishes this as the convention every Go reader expects: "by
> convention, error is the last result parameter." `revive`'s
> `error-return` rule fails the build if an error isn't last. **Violation
> — enforced by `revive/error-return`.**

```go
// bad — error is not the last return value
func Lookup(key string) (error, string) {
	return nil, ""
}

// good
func Lookup(key string) (string, error) {
	return "", nil
}
```

## 16.2 Use a sentinel error value (a package-level `var`) when callers need to compare against a specific, known failure.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> recommends giving errors "structure so that [comparison] can be done
> programmatically rather than having the caller perform string matching."
> A sentinel is the simplest structured error: one unparameterized value
> the caller can compare against directly (via `errors.Is`, see 16.7).

```go
// bad — caller has no reliable way to detect this specific failure
func process(animal Animal) error {
	if seen[animal] {
		return errors.New("duplicate")
	}
	return nil
}

// good
var ErrDuplicate = errors.New("duplicate")

func process(animal Animal) error {
	if seen[animal] {
		return ErrDuplicate
	}
	return nil
}
```

## 16.3 Name exported sentinel errors with an `Err` prefix, and unexported ones with `err`.

> Why? [Uber Style: Error
> Naming](https://github.com/uber-go/guide/blob/master/style.md#error-naming)
> requires this prefix for global error variables, "regardless of whether
> they're exported," so a reader can identify an error value at the
> declaration site without reading its initializer. `revive`'s
> `error-naming` rule enforces the exported case. **Violation — enforced
> by `revive/error-naming`.**

```go
// bad
var NotFound = errors.New("not found")
var duplicateEntry = errors.New("duplicate entry")

// good
var ErrNotFound = errors.New("not found")
var errDuplicateEntry = errors.New("duplicate entry")
```

## 16.4 Name custom error types with an `Error` suffix.

> Why? [Uber Style: Error
> Naming](https://github.com/uber-go/guide/blob/master/style.md#error-naming)
> pairs the `Err`/`err` variable convention with an `Error` suffix for
> types, so `NotFoundError`, `*ValidationError`, and similar names signal
> "this type implements the `error` interface" on sight. `revive`'s
> `error-naming` rule covers this form too. **Violation — enforced by
> `revive/error-naming`.**

```go
// bad
type NotFound struct {
	Key string
}

func (e *NotFound) Error() string {
	return fmt.Sprintf("key %q not found", e.Key)
}

// good
type NotFoundError struct {
	Key string
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("key %q not found", e.Key)
}
```

## 16.5 Give an error structure (a custom type) when the caller needs data from the failure, not just its identity.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> points to `os.PathError` as the model: it "places the pathname of the
> failing operation in a struct field which the caller can easily access,"
> instead of forcing callers to parse a formatted string.

```go
// bad — path is only recoverable by parsing the error string
func Open(path string) error {
	return fmt.Errorf("could not open %s", path)
}

// good — structured error exposes the path programmatically
type NotFoundError struct {
	Path string
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s: not found", e.Path)
}

func Open(path string) error {
	return &NotFoundError{Path: path}
}
```

## 16.6 Wrap an error with `fmt.Errorf("...: %w", err)` when the caller should be able to unwrap it; use `%v` to obfuscate it.

> Why? [Uber Style: Error
> Wrapping](https://github.com/uber-go/guide/blob/master/style.md#error-wrapping)
> frames this as a deliberate choice: "use `%w` if the caller should have
> access to the underlying error... use `%v` to obfuscate the underlying
> error." `%w` expands your package's API surface (see 16.10), so it
> should be intentional, not default. The user's `errorlint` setting
> (`errorf: true`) fails the build if an error argument is formatted with
> `%v` or `%s` where `%w` was clearly intended — i.e., any format verb
> other than `%w` applied to a wrapped error argument in `fmt.Errorf` is
> flagged. **Violation — enforced by `errorlint` (`errorf: true`).**

```go
// bad — errorlint flags formatting an error with %v instead of %w
if err := os.Open(path); err != nil {
	return fmt.Errorf("open config: %v", err)
}

// good — %w preserves the chain for errors.Is/errors.As
if err := os.Open(path); err != nil {
	return fmt.Errorf("open config: %w", err)
}
```

## 16.7 Compare against sentinel errors with `errors.Is`, never `==`.

> Why? An error returned through several layers of wrapping is no longer
> `==` to the original sentinel, even though it still represents the same
> failure. [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> shows `errors.Is` as the wrapping-safe replacement for direct equality.
> The user's `errorlint` setting (`comparison: true`) fails the build on
> any `err == sentinelErr` or `switch err` comparison. **Violation —
> enforced by `errorlint` (`comparison: true`).**

```go
// bad — errorlint flags direct equality against a sentinel error
if err == ErrNotFound {
	// handle
}

// good
if errors.Is(err, ErrNotFound) {
	// handle
}
```

## 16.8 Extract a typed error's fields with `errors.As`, never a direct type assertion.

> Why? Like `errors.Is`, `errors.As` walks the full wrap chain to find a
> matching type, while a raw type assertion only ever sees the outermost
> error. The user's `errorlint` setting (`asserts: true`) fails the build
> on `err.(*NotFoundError)`, comma-ok or not. **Violation — enforced by
> `errorlint` (`asserts: true`).** See also [Chapter 14, §14.11](14-interfaces.md)
> for the general type-assertion rule this specializes.

```go
// bad — errorlint flags a direct type assertion on an error value
if nf, ok := err.(*NotFoundError); ok {
	log.Printf("missing key: %s", nf.Key)
}

// good
var nf *NotFoundError
if errors.As(err, &nf) {
	log.Printf("missing key: %s", nf.Key)
}
```

## 16.9 Give a custom error type an `Unwrap() error` method when it wraps another error.

> Why? `errors.Is` and `errors.As` traverse a chain by repeatedly calling
> `Unwrap`. [Uber Style: Error
> Types](https://github.com/uber-go/guide/blob/master/style.md#error-types)
> and the standard library's own `fs.PathError` follow this shape so a
> custom error type participates fully in the wrapping ecosystem instead
> of acting as a dead end that swallows the underlying cause.

```go
// bad — Cause is inaccessible to errors.Is/errors.As
type QueryError struct {
	Query string
	Cause error
}

func (e *QueryError) Error() string {
	return fmt.Sprintf("query %q failed: %v", e.Query, e.Cause)
}

// good
type QueryError struct {
	Query string
	Cause error
}

func (e *QueryError) Error() string {
	return fmt.Sprintf("query %q failed: %v", e.Query, e.Cause)
}

func (e *QueryError) Unwrap() error {
	return e.Cause
}
```

## 16.10 Use `errors.Join` (Go 1.20+) to combine multiple independent errors instead of picking just one or concatenating strings.

> Why? Operations like closing several resources or validating several
> fields can each fail independently. `errors.Join` preserves every
> underlying error so `errors.Is`/`errors.As` still work against any of
> them, which string concatenation destroys. This is the modern
> replacement for hand-rolled multi-error types.

```go
// bad — was idiomatic pre-1.20; only the last error survives, and the
// others are lost to a log line
func closeAll(closers []io.Closer) error {
	var err error
	for _, c := range closers {
		if cerr := c.Close(); cerr != nil {
			log.Printf("close error: %v", cerr)
			err = cerr
		}
	}
	return err
}

// good — every error is preserved and still matchable with errors.Is/As
func closeAll(closers []io.Closer) error {
	var errs []error
	for _, c := range closers {
		if cerr := c.Close(); cerr != nil {
			errs = append(errs, cerr)
		}
	}
	return errors.Join(errs...)
}
```

## 16.11 Don't distinguish errors by matching their string form.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> is explicit: "do not attempt to distinguish errors based on their string
> form." Error message text is documentation for humans, not a stable API
> — changing wording anywhere in the wrap chain silently breaks string
> matching, whereas `errors.Is`/`errors.As` survive message changes.

```go
// bad — breaks the moment the underlying message wording changes
func handlePet(err error) {
	if regexp.MustCompile(`duplicate`).MatchString(err.Error()) {
		// ...
	}
}

// good
func handlePet(err error) {
	if errors.Is(err, ErrDuplicate) {
		// ...
	}
}
```

## 16.12 Place the `%w` verb at the end of the format string.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> shows that error chains are always traversed newest-to-oldest by
> `Unwrap`, but the printed order only matches that traversal — reading
> naturally as "newest cause first" — when `%w` sits at the end of the
> format string (`"...: %w"`). Placing it earlier or mixing multiple
> verbs makes the printed message contradict the actual unwrap order.

```go
// bad — printed message doesn't match the actual wrap order
err1 := errors.New("err1")
err2 := fmt.Errorf("%w: err2", err1)
fmt.Println(err2) // err1: err2 — reads backwards

// good — %w at the end keeps print order aligned with wrap order
err1 := errors.New("err1")
err2 := fmt.Errorf("err2: %w", err1)
fmt.Println(err2) // err2: err1
```

## 16.13 Document any error variables or types your package returns as part of its exported contract.

> Why? [Google Best Practices:
> Errors](https://google.github.io/styleguide/go/best-practices#errors)
> calls this out for `os`, which "advertises that its errors contain path
> information when it is available." Once you use `%w`, you are extending
> your package's API surface (per Uber's wrapping guidance in 16.6) —
> undocumented sentinel or typed errors leave callers guessing which
> failures are actually stable enough to match against.

```go
// bad — ErrClosed exists but nothing documents that callers can rely on it
var ErrClosed = errors.New("connection closed")

// good
// ErrClosed is returned by Read and Write after the connection has
// been closed. Callers may test for it with errors.Is.
var ErrClosed = errors.New("connection closed")
```
