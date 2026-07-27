<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 30. Global State

Package-level mutable state turns every function that touches it into a
function with a hidden, untyped extra parameter — one that tests can't
easily control and concurrent callers can silently corrupt. This chapter
draws from [Google Best Practices: Global
state](https://google.github.io/styleguide/go/best-practices#global-state)
and Uber's [Avoid Mutable
Globals](https://github.com/uber-go/guide/blob/master/style.md#avoid-mutable-globals)
and [Avoid
init()](https://github.com/uber-go/guide/blob/master/style.md#avoid-init)
sections. The `cmd/`-level exemption for `init()` described here reflects
the user's own `.golangci.yml`, which excludes `cmd/**` from
`gochecknoinits` — see [Chapter 33.6](33-linter-configuration.md) for the
full linter configuration.

## 30.1 Do not declare mutable state at package scope; pass dependencies explicitly instead.

> Why? [Google Best Practices: Global
> state](https://google.github.io/styleguide/go/best-practices#global-state)
> and [Uber Style: Avoid Mutable
> Globals](https://github.com/uber-go/guide/blob/master/style.md#avoid-mutable-globals)
> both treat mutable package-level variables as a hidden dependency:
> every function that reads or writes them has an implicit input/output
> that doesn't appear in its signature, making the function's behavior
> depend on call order and global program state instead of its
> arguments.

```go
// bad — mutable package-level state is a hidden, shared dependency
var currentUser *User

func SetCurrentUser(u *User) {
	currentUser = u
}

func Greet() string {
	return "Hello, " + currentUser.Name
}

// good — the dependency is explicit in the function signature
func Greet(u *User) string {
	return "Hello, " + u.Name
}
```

## 30.2 Use `var` at package scope only for true constants-in-disguise (values `const` can't express) or for explicit dependency-injection roots wired once at startup.

> Why? [Google Best Practices: Global
> state](https://google.github.io/styleguide/go/best-practices#global-state)
> allows package-level `var` for genuinely immutable values — a compiled
> regular expression, a fixed lookup table — because these behave like
> constants even though Go's `const` can't express their type. The
> distinction is mutability: never written to after initialization.

```go
// bad — a package-level var that gets reassigned during normal operation
var defaultTimeout = 30 * time.Second

func Configure(t time.Duration) {
	defaultTimeout = t // mutated at runtime; hidden shared state
}

// good — an immutable, never-reassigned package-level value
var validSKUPattern = regexp.MustCompile(`^[A-Z]{2}-\d{6}$`)

func IsValidSKU(sku string) bool {
	return validSKUPattern.MatchString(sku)
}
```

## 30.3 Avoid `init()` outside `cmd/`-level main packages; prefer an explicit `New()` constructor the caller invokes deliberately.

> Why? [Uber Style: Avoid
> init()](https://github.com/uber-go/guide/blob/master/style.md#avoid-init)
> explains that `init()` runs implicitly at import time, in an order
> that's hard to predict across multiple files and packages, and can't
> return an error to signal failed setup. An explicit `New()` function
> runs when and where the caller chooses, can return an error, and is
> visible in a stack trace or call graph. The user's own lint
> configuration concedes exactly one exception: `cmd/**` binaries are
> exempted from `gochecknoinits` for CLI flag registration and similar
> program-entry wiring (see rule 30.4 and [Chapter
> 33.6](33-linter-configuration.md)). This is currently a Suggestion, not
> a linter-enforced Violation, since `gochecknoinits` itself is not
> enabled — but it remains the recommended default everywhere outside
> `cmd/`.

```go
// bad — init() silently wires a global client at import time
var defaultClient *http.Client

func init() {
	defaultClient = &http.Client{Timeout: 10 * time.Second}
}

// good — an explicit constructor the caller invokes deliberately
func NewClient() *http.Client {
	return &http.Client{Timeout: 10 * time.Second}
}
```

## 30.4 In `cmd/`-level binaries, `init()` is acceptable for CLI flag registration and framework entry hooks.

> Why? The user's `.golangci.yml` excludes `cmd/**` paths from
> `gochecknoinits` (see [Chapter 33.6](33-linter-configuration.md)),
> reflecting a deliberate, scoped exception: registering flags with the
> standard `flag` package, or wiring a framework hook like Cobra's
> `OnInitialize`, has to run before `main` executes its own logic, and
> both `flag` and Cobra are designed around `init()`-time registration.
> This exemption applies only to `cmd/` binaries, not to library or
> service packages.

```go
// bad — outside cmd/, an init() doing the same thing is a real
// violation: it wires global state implicitly at import time
package config

var settings *Settings

func init() {
	settings = loadFromEnv()
}

// good — acceptable in cmd/server/main.go: flag registration via init()
package main

var (
	addr  = flag.String("addr", ":8080", "listen address")
	debug = flag.Bool("debug", false, "enable debug logging")
)

func init() {
	flag.Parse()
}

func main() {
	run(*addr, *debug)
}
```

## 30.5 Use `sync.Once` for expensive, one-time lazy initialization instead of an `init()` function or an ad hoc "already initialized" boolean flag.

> Why? [Google Best Practices: Global
> state](https://google.github.io/styleguide/go/best-practices#global-state)
> recommends `sync.Once` when initialization is genuinely expensive and
> should happen lazily on first use rather than eagerly at import time —
> `sync.Once` guarantees the initializer runs exactly once even under
> concurrent first access, which a hand-rolled boolean flag does not.

```go
// bad — a boolean flag race: two goroutines can both see initialized == false
var (
	initialized bool
	client      *ExpensiveClient
)

func getClient() *ExpensiveClient {
	if !initialized {
		client = newExpensiveClient()
		initialized = true
	}
	return client
}

// good — sync.Once guarantees exactly-once initialization under concurrency
var (
	clientOnce sync.Once
	client     *ExpensiveClient
)

func getClient() *ExpensiveClient {
	clientOnce.Do(func() {
		client = newExpensiveClient()
	})
	return client
}
```

## 30.6 Prefer dependency injection over a package-level singleton, even for things that feel inherently singular (a logger, a database pool).

> Why? [Google Best Practices: Global
> state](https://google.github.io/styleguide/go/best-practices#global-state)
> notes that "there's only one of these in production" doesn't mean code
> should hard-wire that assumption — tests need a different instance per
> test, and a singleton makes that impossible without global mutable
> state that leaks between tests.

```go
// bad — a package-level singleton database handle
var DB *sql.DB

func GetUser(id string) (*User, error) {
	return queryUser(DB, id)
}

// good — the database handle is a field, injected explicitly
type UserStore struct {
	db *sql.DB
}

func NewUserStore(db *sql.DB) *UserStore {
	return &UserStore{db: db}
}

func (s *UserStore) GetUser(id string) (*User, error) {
	return queryUser(s.db, id)
}
```

## 30.7 Prefix unexported package-level variables with `_` when they hold mutable or sensitive shared state, to flag them visually at every use site.

> Why? [Uber Style: Avoid Mutable
> Globals](https://github.com/uber-go/guide/blob/master/style.md#avoid-mutable-globals)
> recommends the `_` prefix convention specifically so that every
> reference to a package-level variable is visually distinct from a
> local variable, making it obvious at the call site that the code is
> touching shared state.

```go
// bad — looks like an ordinary local variable at every call site
var requestCounter int64

func handle() {
	atomic.AddInt64(&requestCounter, 1)
}

// good — the _ prefix flags this as package-level shared state
var _requestCounter int64

func handle() {
	atomic.AddInt64(&_requestCounter, 1)
}
```

## 30.8 Delete unused package-level declarations instead of leaving them "just in case."

> Why? Dead package-level variables, constants, and functions are extra
> surface area a reader has to determine is safe to ignore, and they
> accumulate silently since nothing forces their removal. The user's
> `.golangci.yml` enables `unused`, which flags declarations that are
> never referenced.

> Enforced by: unused (see [Chapter 33.2](33-linter-configuration.md))

```go
// bad — dead code left behind after a refactor
var legacyAPIKey = "unused-since-migration" // nothing reads this anymore

func currentAPIKey() string {
	return os.Getenv("API_KEY")
}

// good — the dead declaration is removed
func currentAPIKey() string {
	return os.Getenv("API_KEY")
}
```

## 30.9 Guard any package-level state that genuinely must be mutable (metrics counters, connection pools) with a mutex or atomic type — never leave concurrent access unsynchronized.

> Why? [Google Best Practices: Global
> state](https://google.github.io/styleguide/go/best-practices#global-state)
> accepts that some global state (process-wide metrics, for instance) is
> unavoidable, but requires it to be concurrency-safe, since package-level
> state is by definition reachable from every goroutine in the program.

```go
// bad — concurrent increments race; go test -race flags this
var requestCount int

func handle() {
	requestCount++
}

// good — sync/atomic makes concurrent access to the shared counter safe
var requestCount atomic.Int64

func handle() {
	requestCount.Add(1)
}
```

## 30.10 Do not use package-level state to pass values between unrelated packages; use explicit function parameters, return values, or a `context.Context` value for request-scoped data.

> Why? [Google Best Practices: Global
> state](https://google.github.io/styleguide/go/best-practices#global-state)
> treats package-level variables used as an ad hoc communication channel
> between packages as one of the worst forms of hidden coupling: neither
> package's public API reveals that this indirect dependency exists.

```go
// bad — package "audit" reads a global set by package "auth"
package auth

var CurrentUserID string

// package audit
func Log(action string) {
	fmt.Printf("user %s did %s\n", auth.CurrentUserID, action)
}

// good — the value flows explicitly through function parameters
package audit

func Log(userID, action string) {
	fmt.Printf("user %s did %s\n", userID, action)
}
```
