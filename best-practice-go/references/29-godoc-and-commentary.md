<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 29. Godoc & Commentary

Comments in Go are not free-form prose — `godoc` extracts and renders them
mechanically, so the convention for *where* a comment starts and *what its
first word is* has real, tool-visible consequences. This chapter follows
[Google Style Decisions:
Commentary](https://google.github.io/styleguide/go/decisions#commentary),
[Google Best Practices:
Comments](https://google.github.io/styleguide/go/best-practices#comments),
and [Effective Go:
Commentary](https://go.dev/doc/effective_go#commentary). Where the user's
`staticcheck` configuration exempts specific doc-comment checks, this
chapter still teaches the convention — as a Suggestion, not a
Violation — because the underlying practice remains good style even when
unenforced; see [Chapter 33.8](33-linter-configuration.md) for the exact
exemption list.

## 29.1 Start every exported identifier's doc comment with that identifier's name.

> Why? [Effective Go:
> Commentary](https://go.dev/doc/effective_go#commentary) and [Google
> Style Decisions:
> Commentary](https://google.github.io/styleguide/go/decisions#commentary)
> both rely on this convention so that `godoc`-generated documentation
> reads as complete sentences and so that tools (and readers scanning
> quickly) can identify which comment documents which symbol without
> ambiguity. The user's `staticcheck` configuration exempts the automated
> checks for this (ST1020/ST1021/ST1022 — see [Chapter
> 33.8](33-linter-configuration.md)), so it is a Suggestion here, not a
> hard Violation, but it remains the convention this guide recommends.

```go
// bad — comment doesn't start with the identifier name
// Returns a new client configured with the given options.
func NewClient(opts ...Option) *Client {
	return &Client{opts: opts}
}

// good — comment starts with "NewClient", matching the identifier
// NewClient returns a new client configured with the given options.
func NewClient(opts ...Option) *Client {
	return &Client{opts: opts}
}
```

## 29.2 Give every package a package doc comment on the file that best represents the package (typically `doc.go` for larger packages).

> Why? [Google Style Decisions:
> Commentary](https://google.github.io/styleguide/go/decisions#commentary)
> and [Effective Go:
> Commentary](https://go.dev/doc/effective_go#commentary) treat the
> package comment as the front page of the package's documentation — the
> first thing `pkg.go.dev` and `go doc` show. The user's `staticcheck`
> configuration exempts the automated check for this (ST1000 — see
> [Chapter 33.8](33-linter-configuration.md)), so a missing package
> comment won't fail CI, but it is still a Suggestion worth following for
> any package with external consumers.

```go
// bad — no package comment; go doc shows nothing about the package's purpose
package ratelimit

type Limiter struct{ /* ... */ }

// good — a package comment explains what the package is for
// Package ratelimit provides token-bucket rate limiters for bounding
// request throughput to external dependencies.
package ratelimit

type Limiter struct{ /* ... */ }
```

## 29.3 Write doc comments as complete sentences: capitalized start, period at the end.

> Why? `godoc` concatenates consecutive comment lines into paragraphs and
> displays them as prose. [Google Style Decisions:
> Commentary](https://google.github.io/styleguide/go/decisions#commentary)
> expects that prose to read like normal written English, which requires
> sentence casing and terminal punctuation — not sentence fragments.

```go
// bad — reads as a fragment, not a sentence
// returns the current queue depth
func (q *Queue) Depth() int {
	return len(q.items)
}

// good — a complete, properly punctuated sentence
// Depth returns the current queue depth.
func (q *Queue) Depth() int {
	return len(q.items)
}
```

## 29.4 Skip doc comments on trivial, self-explanatory getters and setters.

> Why? [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> warns against comments that restate what the code already says with no
> added information. A getter named `Name()` returning a `name` field
> needs no comment explaining that it returns the name — the signature
> already says that.

```go
// bad — the comment adds zero information beyond the signature
// Name returns the name.
func (u *User) Name() string {
	return u.name
}

// good — no comment needed; the signature is already self-explanatory
func (u *User) Name() string {
	return u.name
}
```

## 29.5 Document non-obvious behavior, preconditions, and concurrency semantics — not the mechanical "what" that the signature already shows.

> Why? [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> directs comments toward information the reader cannot get from the
> signature alone: is this safe to call concurrently, does it retain the
> input slice, what happens on an empty input.

```go
// bad — restates the signature; omits the actually useful information
// Merge merges two slices.
func Merge(a, b []int) []int {
	// ...
	return merged
}

// good — documents the non-obvious contract: ordering and aliasing
// Merge returns a new sorted slice containing all elements of a and b.
// It does not modify a or b, and the result shares no backing array
// with either input.
func Merge(a, b []int) []int {
	// ...
	return merged
}
```

## 29.6 Add runnable documentation with `Example` functions in `_test.go` files instead of prose-only usage snippets in doc comments.

> Why? An `Example` function is compiled and, if it has an `// Output:`
> comment, executed by `go test`, so it can never silently drift out of
> sync with the API the way a hand-written usage snippet in a comment
> can. [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> favors documentation that the toolchain verifies.

```go
// bad — usage sketch in a comment; nothing checks it still compiles or runs
// Parse parses a duration string.
//
// Example usage:
//   d := Parse("5s")
//   fmt.Println(d)
//   // Output: 5s
func Parse(s string) time.Duration {
	// ...
}

// good — an Example function in duration_test.go, checked by go test
func ExampleParse() {
	d := Parse("5s")
	fmt.Println(d)
	// Output: 5s
}
```

## 29.7 Mark deprecated identifiers with a `// Deprecated:` paragraph that says what to use instead.

> Why? Tooling (including `gopls` and `go vet`-adjacent editors)
> recognizes the exact `// Deprecated:` marker and surfaces a warning at
> every call site. [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> expects deprecation notices to point migrating callers at the
> replacement, not just announce that something is old.

```go
// bad — says it's deprecated but tooling can't detect this free-form note
// NewClientV1 creates a client. This is old, use the new one.
func NewClientV1(addr string) *Client {
	return &Client{addr: addr}
}

// good — the exact "Deprecated:" marker is machine-recognizable
// NewClientV1 creates a client using the legacy connection protocol.
//
// Deprecated: use NewClient, which supports connection pooling and
// automatic retries.
func NewClientV1(addr string) *Client {
	return &Client{addr: addr}
}
```

## 29.8 Use `TODO(username): ...` for deferred work, not a bare `TODO` or `FIXME` with no owner.

> Why? [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> requires an attributable owner on every TODO so a reader knows who to
> ask about it and so TODOs don't become permanent, ownerless clutter
> that nobody feels responsible for resolving.

```go
// bad — no owner, no way to follow up
// TODO: handle the retry case here
func fetch(url string) error {
	// ...
	return nil
}

// good — TODO is attributed to a specific person or team
// TODO(jchen): handle the retry case once the backoff policy is finalized.
func fetch(url string) error {
	// ...
	return nil
}
```

## 29.9 Do not restate the obvious inline; reserve inline comments for the "why," not the "what."

> Why? [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> treats inline comments that just narrate the following line
> (`i++ // increment i`) as noise. The valuable inline comment explains a
> non-obvious reason for a choice — why this magic number, why this
> ordering, why this workaround.

```go
// bad — comment narrates code that is already self-explanatory
count++ // increment count by one

// good — comment explains a non-obvious reason for the value
retries := 3 // matches the upstream gateway's own retry budget
```

## 29.10 Treat initialism casing (`URL`, `ID`, `HTTP`) as a Suggestion, not a hard Violation, given the user's `staticcheck` configuration.

> Why? Go convention capitalizes initialisms consistently (`UserID`, not
> `UserId`; `ParseURL`, not `ParseUrl`), and this guide still recommends
> following it for readability. The user's `staticcheck` configuration
> exempts ST1003 (see [Chapter 33.8](33-linter-configuration.md)), which
> covers initialism casing among other identifier-quality checks, so
> inconsistent casing will not fail CI. Treat it as something to fix
> opportunistically in review, not something to block a merge over.

```go
// bad — inconsistent initialism casing; still compiles and CI won't
// block it, but it reads against Go convention
type UserId struct {
	Value string
}

func ParseUrl(s string) (*url.URL, error) {
	return url.Parse(s)
}

// good — consistent initialism casing, recommended but not lint-enforced
type UserID struct {
	Value string
}

func ParseURL(s string) (*url.URL, error) {
	return url.Parse(s)
}
```

## 29.11 Do not duplicate a struct field's doc comment across every place the struct is constructed; document the field once, at its declaration.

> Why? [Google Best Practices:
> Comments](https://google.github.io/styleguide/go/best-practices#comments)
> favors documentation living in exactly one place — the declaration —
> so it cannot drift out of sync with copies scattered at every call
> site.

```go
// bad — the same explanation is repeated at every construction site
cfg := Config{
	Timeout: 30 * time.Second, // Timeout is how long to wait for a response
}

// good — the explanation lives once, on the field itself
type Config struct {
	// Timeout is how long to wait for a response before giving up.
	Timeout time.Duration
}

cfg := Config{Timeout: 30 * time.Second}
```
