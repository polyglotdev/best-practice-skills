<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 11. Functions

A function's signature is its contract with every caller, and Go gives you
a small set of tools — multiple return values, named results, `defer` —
to make that contract clear and safe to use. This chapter draws from
[Google Best Practices: Function
parameters](https://google.github.io/styleguide/go/best-practices#function-parameters),
[Effective Go:
Functions](https://go.dev/doc/effective_go#functions) (multiple return
values, named result parameters, `Defer`), and Uber's [Avoid Naked
Parameters](https://github.com/uber-go/guide/blob/master/style.md#avoid-naked-parameters)
guidance. Argument-order conventions for `context.Context` overlap with
the concurrency chapter of the audit skill; this chapter covers the
general shape of function signatures and bodies.

## 11.1 Return `(result, error)` for operations that can fail — don't encode failure in a sentinel result value.

> Why? A dedicated `error` return makes failure explicit in the type
> system and forces callers to at least acknowledge it exists, unlike a
> sentinel value (`-1`, `""`, `nil`) that's easy to forget to check and
> can collide with a legitimate result
> ([Effective Go: Functions](https://go.dev/doc/effective_go#multiple_return))).

```go
// bad — -1 is used as both a real index and a failure signal
func IndexOf(items []string, target string) int {
	for i, item := range items {
		if item == target {
			return i
		}
	}
	return -1
}

// good
func IndexOf(items []string, target string) (int, error) {
	for i, item := range items {
		if item == target {
			return i, nil
		}
	}
	return 0, fmt.Errorf("%q not found", target)
}
```

## 11.2 Return `(value, ok)` for lookups where "not found" is a normal, expected outcome rather than a failure.

> Why? Not every "didn't find it" case deserves the weight of an
> `error` — a map lookup or cache check where absence is a routine
> result reads more naturally as a boolean flag, matching the idiom
> the standard library itself uses for map indexing
> ([Effective Go: Functions](https://go.dev/doc/effective_go#multiple_return)).

```go
// bad — treats an ordinary cache miss as an error
func (c *Cache) Get(key string) (string, error) {
	v, ok := c.data[key]
	if !ok {
		return "", errors.New("cache miss")
	}
	return v, nil
}

// good — absence is a normal, expected outcome
func (c *Cache) Get(key string) (string, bool) {
	v, ok := c.data[key]
	return v, ok
}
```

## 11.3 Use named result parameters to document what each return value means, especially when multiple values share a type.

> Why? `func Split(s string) (string, string, error)` doesn't tell the
> reader which string is which without checking the implementation or
> the doc comment. Naming the results (`prefix`, `suffix`) documents
> the contract directly in the signature
> ([Effective Go: Functions](https://go.dev/doc/effective_go#named_results)).

```go
// bad — ambiguous which return value is which
func Split(s, sep string) (string, string, error) {
	i := strings.Index(s, sep)
	if i < 0 {
		return "", "", fmt.Errorf("separator %q not found", sep)
	}
	return s[:i], s[i+len(sep):], nil
}

// good — the signature alone documents the contract
func Split(s, sep string) (prefix, suffix string, err error) {
	i := strings.Index(s, sep)
	if i < 0 {
		return "", "", fmt.Errorf("separator %q not found", sep)
	}
	return s[:i], s[i+len(sep):], nil
}
```

## 11.4 Don't rely on naked `return` except in short functions where every named result is set immediately above it.

> Why? A naked `return` in a long function forces the reader to scroll
> back through the entire body to find where each named result was
> last assigned. In a short function where the assignment is right
> above the `return`, the naked form is harmless and common
> ([Effective Go: Functions](https://go.dev/doc/effective_go#named_results)).

```go
// bad — naked return in a long function; unclear what's being returned without scrolling
func ParseConfig(data []byte) (cfg Config, err error) {
	if len(data) == 0 {
		err = errors.New("empty config")
		return
	}
	if jsonErr := json.Unmarshal(data, &cfg); jsonErr != nil {
		err = fmt.Errorf("unmarshal: %w", jsonErr)
		return
	}
	if cfg.Timeout == 0 {
		cfg.Timeout = 30 * time.Second
	}
	// ... ten more lines of validation and defaulting ...
	return
}

// good — explicit values at each return, easy to verify at a glance
func ParseConfig(data []byte) (Config, error) {
	if len(data) == 0 {
		return Config{}, errors.New("empty config")
	}
	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return Config{}, fmt.Errorf("unmarshal: %w", err)
	}
	if cfg.Timeout == 0 {
		cfg.Timeout = 30 * time.Second
	}
	return cfg, nil
}

// good — naked return is fine: short function, one assignment right above it
func Halve(n int) (half int) {
	half = n / 2
	return
}
```

## 11.5 Use `defer` to pair cleanup with acquisition, right after the resource is acquired.

> Why? Placing `defer Close()` (or `Unlock()`, or similar) immediately
> after the line that opens or locks the resource guarantees the
> cleanup can never be skipped by an early return added later, and it
> keeps the acquire/release pair visually adjacent
> ([Effective Go: Defer](https://go.dev/doc/effective_go#defer)).

```go
// bad — cleanup added at the bottom; any early return above it leaks the file
func ReadConfig(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	data, err := io.ReadAll(f)
	if err != nil {
		return nil, err // f is never closed on this path
	}
	f.Close()
	return data, nil
}

// good — defer right after acquisition; every exit path closes f
func ReadConfig(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	return io.ReadAll(f)
}
```

## 11.6 Take `context.Context` as the first parameter, named `ctx`, on any function that does I/O or can be canceled.

> Why? This is Go's universal convention for cancellation and
> deadline propagation — putting `ctx` anywhere else in the parameter
> list, or giving it an inconsistent name, breaks the pattern every Go
> developer scans for
> ([Best Practices: Function
> parameters](https://google.github.io/styleguide/go/best-practices#function-parameters)).

```go
// bad — ctx is not first, and not named consistently
func FetchUser(id string, c context.Context) (*User, error) {
	return nil, nil
}

// good
func FetchUser(ctx context.Context, id string) (*User, error) {
	return nil, nil
}
```

## 11.7 Put variadic and options-style parameters last in the parameter list.

> Why? Go's variadic syntax (`...T`) only works as the final parameter,
> and functional-options parameters (`...Option`) follow the same
> convention by analogy — placing configuration last keeps the required
> arguments visually grouped at the front of every call site
> ([Best Practices: Function
> parameters](https://google.github.io/styleguide/go/best-practices#function-parameters)).

```go
// bad — this doesn't even compile: variadic must be the final parameter
func Connect(opts ...Option, host string) (*Client, error) {
	return nil, nil
}

// good
func Connect(host string, opts ...Option) (*Client, error) {
	return nil, nil
}
```

## 11.8 Avoid bare boolean parameters; use a named type or split into two functions when the call site would otherwise be unreadable.

> Why? A call like `Send(msg, true, false)` gives the reader no way to
> know what `true` and `false` mean without looking up the signature.
> A named type turns each value into a self-documenting identifier at
> the call site
> ([Uber Style: Avoid Naked
> Parameters](https://github.com/uber-go/guide/blob/master/style.md#avoid-naked-parameters)).

```go
// bad — meaningless at the call site
func Send(msg string, urgent, retry bool) error { return nil }

Send("server down", true, false)

// good — named types document intent directly
type Priority bool

const (
	PriorityNormal Priority = false
	PriorityUrgent Priority = true
)

func Send(msg string, priority Priority) error { return nil }

Send("server down", PriorityUrgent)
```

## 11.9 Keep unexported function parameters used — delete or underscore-name any that aren't.

> Why? An unused parameter in an unexported function is either dead
> weight from a refactor or a sign the function doesn't do what its
> signature implies. Exported functions are held to a looser standard
> here because dropping a parameter would break every caller's
> compiled code — an unused parameter in an exported function is often
> unavoidable API-compatibility scaffolding, not a defect.

```go
// bad — unexported helper with an unused parameter, likely leftover from a refactor
func computeTotal(items []Item, discount float64, taxRate float64) float64 {
	total := 0.0
	for _, item := range items {
		total += item.Price
	}
	return total * (1 - discount)
	// taxRate is never used
}

// good — remove the unused parameter, or use it
func computeTotal(items []Item, discount float64) float64 {
	total := 0.0
	for _, item := range items {
		total += item.Price
	}
	return total * (1 - discount)
}
```

> Enforced by: `revive` `unused-parameter` and `unparam` (commonly
> configured with `check-exported: false`, meaning unexported functions
> are checked for unused parameters but exported functions are exempt,
> since removing a parameter from an exported signature is a breaking
> API change that may be justified for other reasons).

## 11.10 Give every exported function that returns an `error` a genuine chance of returning a non-nil one — don't return a hardcoded `nil` forever.

> Why? A function signature that promises `error` but can never
> actually produce one misleads every caller into writing error-handling
> code for a path that will never trigger, and it hides the fact that
> the function might need real error handling added later without a
> signature change going unnoticed.

```go
// bad — signature promises error, but nothing can ever produce one
func Validate(name string) error {
	fmt.Println("validating", name)
	return nil // always nil, forever
}

// good — either drop the error return, or make it meaningful
func Validate(name string) error {
	if name == "" {
		return errors.New("name must not be empty")
	}
	return nil
}
```

> Enforced by: `revive` `error-return` (flags error results that
> don't carry meaningful information, such as always-nil returns or
> error as a non-final return value).

## 11.11 Keep functions short enough that a reader can hold the whole thing in their head; extract helpers once a function does more than one job.

> Why? A function that handles validation, transformation, persistence,
> and logging all in one body forces every caller and every reviewer to
> load all four responsibilities into working memory at once. Splitting
> by responsibility makes each piece independently testable and
> nameable ([Effective Go: Functions](https://go.dev/doc/effective_go#functions)).

```go
// bad — one function doing validation, transformation, and persistence
func HandleSignup(req SignupRequest) error {
	if req.Email == "" || !strings.Contains(req.Email, "@") {
		return errors.New("invalid email")
	}
	if len(req.Password) < 8 {
		return errors.New("password too short")
	}
	hashed := hash(req.Password)
	user := User{Email: req.Email, PasswordHash: hashed, CreatedAt: time.Now()}
	return db.Save(user)
}

// good — split by responsibility
func HandleSignup(req SignupRequest) error {
	if err := validateSignup(req); err != nil {
		return err
	}
	return db.Save(newUserFromSignup(req))
}

func validateSignup(req SignupRequest) error {
	if req.Email == "" || !strings.Contains(req.Email, "@") {
		return errors.New("invalid email")
	}
	if len(req.Password) < 8 {
		return errors.New("password too short")
	}
	return nil
}

func newUserFromSignup(req SignupRequest) User {
	return User{Email: req.Email, PasswordHash: hash(req.Password), CreatedAt: time.Now()}
}
```

## 11.12 Order parameters from most to least essential, with output-like or configuration parameters last.

> Why? Callers read parameter lists left to right; putting the most
> important, most-obviously-required arguments first (after `ctx`) and
> secondary configuration last makes call sites easier to scan and
> keeps optional-feeling parameters visually separated from required
> ones ([Best Practices: Function
> parameters](https://google.github.io/styleguide/go/best-practices#function-parameters)).

```go
// bad — the essential "what to fetch" argument buried after configuration
func FetchOrder(timeout time.Duration, retries int, orderID string) (*Order, error) {
	return nil, nil
}

// good — essential argument first, configuration last
func FetchOrder(orderID string, timeout time.Duration, retries int) (*Order, error) {
	return nil, nil
}
```
