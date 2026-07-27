<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 2. Names

Names are the most visible part of a Go API — more visible than comments,
because every call site repeats them. This chapter draws primarily from
[Effective Go: Names](https://go.dev/doc/effective_go#names), [Google Style
Decisions: Naming](https://google.github.io/styleguide/go/decisions#naming),
[Google Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming)
and [Variables](https://google.github.io/styleguide/go/best-practices#variables),
and Uber's guidance on
[package names](https://github.com/uber-go/guide/blob/master/style.md#package-names),
[function names](https://github.com/uber-go/guide/blob/master/style.md#function-names),
and [prefixing unexported globals with `_`](https://github.com/uber-go/guide/blob/master/style.md#prefix-unexported-globals-with-_).
Package-level organization is covered separately in
[Chapter 3](03-package-organization.md).

## 2.1 Name packages short, lowercase, and without underscores.

> Why? The package name is part of every call site (`json.Marshal`, not
> `JSON.Marshal`). Long or underscored names make every caller's code
> noisier. [Effective Go: Names](https://go.dev/doc/effective_go#names)
> recommends short, concise, evocative package names — lowercase, single
> word, no `snake_case` or `mixedCaps`.

```go
// bad
package String_Utils

// bad
package stringUtils

// good
package strutil
```

## 2.2 Name files for what they contain, in lowercase with underscores only for suffixes Go recognizes.

> Why? File names should describe their contents so a directory listing
> is navigable, but Go only special-cases suffixes like `_test.go`,
> `_linux.go`, or `_amd64.go` for build constraints. Anything else is
> just a name for humans, so keep it short and lowercase
> ([Google Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming)).

```go
// bad — file name: ClientHTTPRequestHandler.go
package api

func HandleRequest(w http.ResponseWriter, r *http.Request) {}

// good — file name: handler.go
package api

func HandleRequest(w http.ResponseWriter, r *http.Request) {}
```

## 2.3 Keep receiver names short (1-2 letters) and identical across all methods of a type.

> Why? Receivers are used on nearly every line of a method body, so a
> long name is friction. Google's style is to abbreviate the type name
> to one or two letters and reuse that same abbreviation for every
> method, so readers don't have to relearn the receiver identity per
> method ([Style Decisions: Receiver
> Names](https://google.github.io/styleguide/go/decisions#receiver-names)).

```go
// bad — verbose, and inconsistent across methods
func (client *Client) Send(msg string) error { return nil }
func (c *Client) Close() error                { return nil }

// good — short, consistent
func (c *Client) Send(msg string) error { return nil }
func (c *Client) Close() error          { return nil }
```

## 2.4 Scale variable name length with scope: short in tight scopes, descriptive at package scope.

> Why? A variable's name has to carry enough meaning to be understood at
> its point of use. In a three-line loop, `i` is unambiguous; the same
> `i` living for hundreds of lines at package scope would be a mystery.
> [Effective Go: Names](https://go.dev/doc/effective_go#names) and
> [Best Practices: Variables](https://google.github.io/styleguide/go/best-practices#variables)
> both favor terse names in small scopes and fuller names as scope grows.

```go
// bad — needlessly long name for a loop variable used on the next line
for index := 0; index < len(users); index++ {
	process(users[index])
}

// bad — a package-level variable named as tersely as a loop counter
var n int // exported package state named with no context

// good
for i := 0; i < len(users); i++ {
	process(users[i])
}

// good
var activeConnectionCount int
```

## 2.5 Use `MixedCaps` or `mixedCaps`; never `snake_case`, for any Go identifier.

> Why? Go's naming convention is one unbroken rule across the entire
> ecosystem: capitalization signals exported vs. unexported, and words
> are joined with capital letters, not underscores. Mixing styles reads
> as foreign to every Go developer and breaks tooling that assumes
> `MixedCaps` (like `golint`/`staticcheck` naming checks)
> ([Effective Go: Names](https://go.dev/doc/effective_go#names)).

```go
// bad
const max_retry_count = 3

func get_user_by_id(user_id string) (*User, error) { return nil, nil }

// good
const maxRetryCount = 3

func getUserByID(userID string) (*User, error) { return nil, nil }
```

> Enforced by: `revive` `var-naming`.

## 2.6 (Suggestion) Prefer a consistent case for initialisms: fully upper or fully lower, never mixed.

> Why? `Id`, `Url`, and `Http` split a single logical word across two
> casing conventions. Go's convention — codified in
> [Effective Go: Names](https://go.dev/doc/effective_go#names) and
> [Style Decisions: Initialisms](https://google.github.io/styleguide/go/decisions#initialisms) —
> is to keep initialisms like `ID`, `URL`, `HTTP`, and `API` at a single
> case: all-caps when the identifier is exported or the initialism
> starts a lowercase identifier internally, all-lowercase when the whole
> identifier is unexported and the initialism isn't the leading word.
> This is a code-review preference, not a build-breaking rule — treat it
> as a Suggestion rather than a Violation.

```go
// bad
type HttpClient struct {
	ApiUrl string
	UserId string
}

// good
type HTTPClient struct {
	APIURL string
	UserID string
}
```

> Enforced by: nothing in a typical CI gate. `staticcheck`'s ST1003
> check covers this class of naming issue, but teams commonly exempt
> ST1003 (poorly chosen identifier casing) because it's noisy against
> existing codebases. Where ST1003 is exempted, treat 2.6 as a
> code-review Suggestion, not a linter-enforced Violation — raise it in
> review, but don't block a merge on it alone.

## 2.7 Group related package-level `const`/`var` declarations instead of scattering single-name globals.

> Why? A reader scanning package-level state wants one place to see
> everything, and grouped declarations under a shared `const ( ... )` or
> `var ( ... )` block communicate that the values are related
> ([Effective Go: Names](https://go.dev/doc/effective_go#names) covers
> constant grouping; naming conventions for the identifiers themselves
> come from [Best Practices:
> Naming](https://google.github.io/styleguide/go/best-practices#naming)).

```go
// bad
const DefaultTimeout = 30
const MaxRetries = 3
const DefaultHost = "localhost"

// good
const (
	DefaultTimeout = 30
	MaxRetries     = 3
	DefaultHost    = "localhost"
)
```

## 2.8 Prefix unexported package-level globals with `_`.

> Why? An unexported global variable or constant can be shadowed by a
> local variable of the same short name without the compiler ever
> warning you, silently breaking the intended reference. Prefixing
> globals with `_` makes shadowing visually obvious at the point of use
> ([Uber Style: Prefix Unexported Globals with
> _](https://github.com/uber-go/guide/blob/master/style.md#prefix-unexported-globals-with-_)).

```go
// bad
var defaultPort = 8080

func Listen(defaultPort int) error { // silently shadows the package var
	return startServer(defaultPort)
}

// good
var _defaultPort = 8080

func Listen(port int) error {
	if port == 0 {
		port = _defaultPort
	}
	return startServer(port)
}
```

> Enforced by: no dedicated linter check for the `_` convention itself,
> but `redefines-builtin-id` (see 2.15) and `ineffassign` catch adjacent
> shadowing bugs this convention prevents. Treat as team convention
> backed by code review.

## 2.9 Give getters no `Get` prefix; name them for the value they return.

> Why? Go doesn't follow the Java/C++ convention of prefixing accessors
> with `Get`. The method signature already communicates that a value is
> returned, so the prefix is pure noise at every call site
> ([Style Decisions: Getters](https://google.github.io/styleguide/go/decisions#getters)).

```go
// bad
func (c *Config) GetTimeout() time.Duration { return c.timeout }

// good
func (c *Config) Timeout() time.Duration { return c.timeout }
```

## 2.10 Name functions and methods with verbs when they act, nouns only when they return a value.

> Why? A reader scans function names to predict behavior before reading
> the body. A noun-named function that mutates state, or a verb-named
> function that just fetches a value, misleads that scan
> ([Uber Style: Function Names](https://github.com/uber-go/guide/blob/master/style.md#function-names)
> and [Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming)).

```go
// bad — Validate reads like an action, but it only returns a bool with no side effect naming clue
func (o *Order) Total() { o.total = compute(o.items) } // mutates but named like a getter

// good
func (o *Order) Recalculate() { o.total = compute(o.items) }
func (o *Order) Total() float64 { return o.total }
```

## 2.11 Don't stutter the package name inside exported identifiers.

> Why? Callers already qualify identifiers with the package name
> (`config.Config`, `config.New`), so repeating it in the identifier
> itself duplicates information at every call site
> ([Style Decisions: Package Names](https://google.github.io/styleguide/go/decisions#package-names)).

```go
// bad
package config

type ConfigOptions struct{}

func NewConfigOptions() ConfigOptions { return ConfigOptions{} }

// good
package config

type Options struct{}

func NewOptions() Options { return Options{} }
```

## 2.12 Name test doubles by role: `Fake`, `Stub`, `Spy`, or `Mock`, not generic names.

> Why? A test reader needs to know at a glance whether a dependency is a
> real implementation or a double, and which kind of double it is — a
> `Fake` behaves like a lightweight real implementation, a `Stub`
> returns canned answers, and a `Spy` records calls for later assertion.
> Generic names like `TestThing` or `Dummy` erase that signal
> ([Best Practices: Naming — test
> doubles](https://google.github.io/styleguide/go/best-practices#naming)).

```go
// bad
type TestClient struct{}

func (TestClient) Send(msg string) error { return nil }

// good
type StubClient struct {
	err error
}

func (s StubClient) Send(msg string) error { return s.err }
```

## 2.13 Don't shadow standard-library package names with local variables.

> Why? Naming a variable `url`, `path`, or `time` shadows the
> corresponding stdlib package for the rest of that scope. Later code in
> the same function that tries to call `url.Parse` will fail to compile,
> or worse, silently resolve to an unrelated identifier
> ([Best Practices: Variables](https://google.github.io/styleguide/go/best-practices#variables)).

```go
// bad
func Fetch(url string) (*http.Response, error) {
	u, err := url.Parse(url) // url is now a string, not the package
	if err != nil {
		return nil, err
	}
	return http.Get(u.String())
}

// good
func Fetch(rawURL string) (*http.Response, error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return nil, err
	}
	return http.Get(u.String())
}
```

## 2.14 Use single-letter or short names only for the smallest, most obvious scopes.

> Why? `i`, `j`, `k` for loop counters and `r`/`w` for `io.Reader`/
> `io.Writer` are Go idiom because their role is obvious from context.
> Extending that terseness to function-level variables that live for
> dozens of lines forces the reader to keep re-deriving what they hold
> ([Effective Go: Names](https://go.dev/doc/effective_go#names)).

```go
// bad
func ProcessOrders(o []Order) (float64, error) {
	var t float64
	for _, x := range o {
		t += x.Total()
	}
	return t, nil
}

// good
func ProcessOrders(orders []Order) (float64, error) {
	var total float64
	for _, order := range orders {
		total += order.Total()
	}
	return total, nil
}
```

## 2.15 Don't redefine built-in identifiers (`len`, `cap`, `min`, `max`, `new`, `error`) as variable or parameter names.

> Why? Go allows shadowing built-ins like `len`, `min`, `max`, `new`, and
> `error` because they're predeclared identifiers, not reserved words —
> but doing so silently removes access to the built-in for the rest of
> that scope, producing confusing errors far from the actual shadowing
> line.

```go
// bad
func Clamp(min, max int, v int) int {
	if v < min {
		return min
	}
	if v > max {
		return max
	}
	return v
}

// good
func Clamp(lower, upper int, v int) int {
	if v < lower {
		return lower
	}
	if v > upper {
		return upper
	}
	return v
}
```

> Enforced by: `revive` `redefines-builtin-id`.
