# Function Design — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

Function signatures are the part of an API the caller is forced to read every time. Long argument lists, parameters that should obviously have been one struct, boolean flags whose meaning disappears at the call site, and channels passed without direction are recurring patterns the style guide calls out.

## Use an option struct when the function has many parameters

**What Google/Effective Go says:** When a function has many parameters, "consider... an option struct" so the call site is self-documenting and fields can be omitted (zero-valued) rather than forcing every caller to enumerate every positional argument. ([Best Practices: Function argument lists](https://google.github.io/styleguide/go/best-practices#function-argument-lists))

**How to detect it:** Grep function signatures for more than 4 comma-separated parameters (excluding a trailing `...T`). Read the call sites — if any call passes two or more bare `true`/`false` literals in a row, that's a strong signal regardless of parameter count.

**Example violation:**
```go
func EnableReplication(ctx context.Context, config *replicator.Config, primaryRegions []string, readonlyCells []string, replicateExisting bool, dryRun bool, timeout time.Duration) error {
	// ...
	return nil
}
```

Calling that is misery: `EnableReplication(ctx, cfg, []string{"us-east-1"}, nil, false, false, 30*time.Second)`. You cannot tell from the call site what `false, false` means.

**Corrected:**
```go
type ReplicationOptions struct {
	Config            *replicator.Config
	PrimaryRegions    []string
	ReadonlyCells     []string
	ReplicateExisting bool
	DryRun            bool
	Timeout           time.Duration
}

func EnableReplication(ctx context.Context, opts ReplicationOptions) error {
	// ...
	return nil
}
```

Call site:
```go
err := EnableReplication(ctx, ReplicationOptions{
	Config:         cfg,
	PrimaryRegions: []string{"us-east-1"},
	Timeout:        30 * time.Second,
})
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` (`gocritic`'s `hugeParam` check, which flags large parameters passed by value, is disabled in this repo — see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation)); this is a design-review checklist item

**Why it matters:** A call site with several positional `bool`/numeric arguments is unreadable without opening the function signature, and adding a new parameter to a long positional list is a breaking change for every caller. An option struct absorbs new fields without breaking existing calls.

## Never put `context.Context` inside an option struct

**What Google/Effective Go says:** "Contexts are never included in option structs." `ctx` is always the first parameter, by convention. ([Best Practices: Function argument lists](https://google.github.io/styleguide/go/best-practices#function-argument-lists))

**How to detect it:** Grep struct definitions used as option types for a `context.Context` field.

**Example violation:**
```go
type ReplicationOptions struct {
	Ctx    context.Context // never do this
	Config *replicator.Config
}
```

**Corrected:**
```go
type ReplicationOptions struct {
	Config *replicator.Config
}

func EnableReplication(ctx context.Context, opts ReplicationOptions) error
```

**Severity:** Violation

**Enforced by:** revive/context-as-argument (flags `ctx` not being a plain leading parameter); see also [context.md](context.md#ctx-is-always-the-first-parameter)

**Why it matters:** Burying `ctx` inside a struct breaks the "ctx is always visible at the call site" expectation reviewers and tooling rely on, and it makes it easy to accidentally store a request-scoped context past the lifetime of the request.

## `context.Context` as the first parameter

**What Google/Effective Go says:** "By convention, `ctx` is the first parameter of a function... Even when a function accepts other typed context-like values (which should be rare), `ctx` should still come first." ([Best Practices: Contexts](https://google.github.io/styleguide/go/best-practices#contexts))

**How to detect it:** For every exported function that accepts a `context.Context` anywhere in its signature, check that it's parameter 1.

**Example violation:**
```go
func FetchPartner(id string, ctx context.Context) (*Partner, error)
```

**Corrected:**
```go
func FetchPartner(ctx context.Context, id string) (*Partner, error)
```

**Severity:** Violation

**Enforced by:** revive/context-as-argument

**Why it matters:** A consistent position lets readers and static-analysis tools recognize context-carrying functions at a glance, and it matches every function in the standard library (`http.NewRequestWithContext`, `sql.DB.QueryContext`, etc.).

## Use variadic options when most callers don't customise

**What Google/Effective Go says:** Variadic functional options keep the common call site clean while preserving extensibility, and are Google's recommended alternative to option structs when "most callers will not need to override the defaults." ([Best Practices: Function argument lists](https://google.github.io/styleguide/go/best-practices#function-argument-lists))

**How to detect it:** Look for functions with 2+ boolean/tuning parameters where most call sites pass the same values — a candidate for collapsing into optional variadic parameters.

**Example — Google's closure-based canonical form:**
```go
type ReplicationOption func(*replicationOptions)

type replicationOptions struct {
	readonlyCells []string
	failFast      bool
}

func ReadonlyCells(cells ...string) ReplicationOption {
	return func(opts *replicationOptions) {
		opts.readonlyCells = append(opts.readonlyCells, cells...)
	}
}

func FailFast(enable bool) ReplicationOption {
	return func(opts *replicationOptions) {
		opts.failFast = enable
	}
}

func EnableReplication(ctx context.Context, config *Config, opts ...ReplicationOption) error {
	resolved := replicationOptions{}
	for _, opt := range opts {
		opt(&resolved)
	}
	// ...
	return nil
}
```

Most callers: `EnableReplication(ctx, cfg)`.
Custom: `EnableReplication(ctx, cfg, ReadonlyCells("us-west-2"), FailFast(true))`.

**Uber's interface-based variant** (used when options need to be comparable or introspected — see [Uber: Functional Options](https://github.com/uber-go/guide/blob/master/style.md#functional-options)):
```go
type Option interface {
	apply(*replicationOptions)
}

type failFastOption bool

func (f failFastOption) apply(opts *replicationOptions) {
	opts.failFast = bool(f)
}

func FailFast(enable bool) Option {
	return failFastOption(enable)
}
```

Prefer Google's simpler closure form for new code in this repo unless the option set needs to be compared, logged, or programmatically inspected, in which case Uber's interface form pays for its extra ceremony.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — an API design choice, not a mechanical rule

**Why it matters:** Functional options let the zero-configuration path stay a two-argument call while still allowing arbitrary extension later, without ever breaking existing callers by adding a new parameter.

## Variadic options should take arguments, not encode state via presence

**What Google/Effective Go says:** "Options should take a parameter" — Google's example is `FailFast(enable bool)`, not a presence-based `EnableFailFast()`, "so that the setting can be explicitly disabled as well as enabled." ([Best Practices: Function argument lists](https://google.github.io/styleguide/go/best-practices#function-argument-lists))

**How to detect it:** For every functional-option constructor, check whether it takes a parameter. Flag no-argument constructors whose only signal is "was this option passed at all."

**Example violation:**
```go
func EnableFailFast() ReplicationOption {
	return func(opts *replicationOptions) {
		opts.failFast = true // can never be turned off downstream
	}
}
```

**Corrected:**
```go
func FailFast(enable bool) ReplicationOption {
	return func(opts *replicationOptions) {
		opts.failFast = enable
	}
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** A presence-only option can't be overridden by a wrapping API or a later option in the chain — `FailFast(false)` lets a caller explicitly restore the default, while `EnableFailFast()` can only ever turn the behavior on.

## Choosing between option struct and variadic options

**What Google/Effective Go says:** Google's guide lays out when each shape fits: structs when "most callers need to specify most of the fields" or when third-party extension isn't required; variadic options when "most calls... will use the default behavior" or when options may need validation on application. ([Best Practices: Function argument lists](https://google.github.io/styleguide/go/best-practices#function-argument-lists))

**How to detect it:** Read every option-carrying function in a package. Confirm the shape (struct vs. variadic) is consistent for functions with similar call patterns, and confirm a single function doesn't mix both an option struct parameter and variadic options.

**Example violation — mixing both styles in one signature:**
```go
func EnableReplication(ctx context.Context, opts ReplicationOptions, extra ...ReplicationOption) error
```

**Corrected — pick one:**
```go
func EnableReplication(ctx context.Context, opts ReplicationOptions) error
// or
func EnableReplication(ctx context.Context, config *Config, opts ...ReplicationOption) error
```

Use a **struct** when:
- All or most callers will set most fields.
- Options are shared across multiple related functions.
- You want per-field godoc that shows on the struct page.
- You don't need third-party packages to define options.

Use **variadic options** when:
- Most callers want defaults.
- Options are numerous and infrequently used.
- Some options can fail or need validation when applied.
- Third-party packages should be able to define their own option constructors.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** Mixing both styles in the same function signature (or inconsistently across a package's public API) forces every caller to learn two different idioms for what should be one mental model.

## No boolean args — use a named type instead

**What Google/Effective Go says:** Not a single named rule in Google's guide, but follows directly from the [Function argument lists](https://google.github.io/styleguide/go/best-practices#function-argument-lists) guidance against unreadable call sites — a bare `bool` at a call site carries no label, unlike a named constant.

**How to detect it:** Grep function signatures for two or more `bool` parameters, or a single `bool` parameter on an exported function whose call sites are far from the declaration (i.e., the reader can't easily check the parameter name).

**Example violation:**
```go
func Connect(host string, useTLS bool, keepAlive bool) (*Conn, error)

// call site — meaning of the two bools is invisible
conn, err := Connect("db.internal", true, false)
```

**Corrected:**
```go
type TransportMode int

const (
	TransportPlaintext TransportMode = iota
	TransportTLS
)

func Connect(host string, mode TransportMode, keepAlive bool) (*Conn, error)

// call site — self-documenting
conn, err := Connect("db.internal", TransportTLS, false)
```

If more than one boolean is involved, prefer collapsing them into an option struct or functional options (see above) rather than a pile of named types.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` (`gocritic`'s style checks don't include a bare-bool-argument rule in this repo's enabled tag set); flag in code review

**Why it matters:** `Connect("db.internal", true, false)` requires the reader to open the function declaration to know what `true` and `false` mean; a named type turns the call site into documentation.

## Specify channel direction in function signatures

**What Google/Effective Go says:** "Specify the direction of a channel" in the parameter type — `<-chan T` for receive-only, `chan<- T` for send-only — because "this prevents the... class of bugs" where a function closes or sends on a channel it should only read. ([Best Practices: Channel direction](https://google.github.io/styleguide/go/best-practices#channel-direction))

**How to detect it:** Grep function signatures for `chan ` (bidirectional, with trailing space, no arrow) parameters. For each match, read the function body — if it only ever ranges/receives, or only ever sends, the signature is under-specified.

**Example violation:**
```go
func Sum(values chan int) int {
	total := 0
	for v := range values {
		total += v
	}
	return total
}
```

The caller can't tell from the signature whether `Sum` reads only or also writes/closes. If a future implementation calls `close(values)` while another goroutine sends, the program panics.

**Corrected:**
```go
func Sum(values <-chan int) int {
	total := 0
	for v := range values {
		total += v
	}
	return total
}
```

Now the signature documents intent and the compiler refuses `close(values)`.

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule in this config; catch via `govet`'s general analysis pass and code review — see also [concurrency.md](concurrency.md#direction-typed-channel-parameters)

**Why it matters:** A directional channel type documents ownership and makes an entire class of close/send misuse bugs a compile error instead of a runtime panic.

## Keep interfaces small and focused

**What Google/Effective Go says:** The guide's broader principle, echoed in [Effective Go: Interfaces](https://go.dev/doc/effective_go#interfaces): an interface should have the fewest methods needed for its purpose. `io.Reader` is one method; `io.ReadWriteCloser` is three. Sprawling interfaces invite ad-hoc test doubles and make consumers depend on capabilities they don't use.

**How to detect it:** Count methods per interface declaration. More than ~6 is worth a second look at whether it's doing too much, or whether it should be decomposed into smaller interfaces that get embedded where a caller genuinely needs the wider set.

**Example violation:**
```go
type PartnerStore interface {
	Get(ctx context.Context, id string) (*Partner, error)
	List(ctx context.Context) ([]*Partner, error)
	Create(ctx context.Context, p *Partner) error
	Update(ctx context.Context, p *Partner) error
	Delete(ctx context.Context, id string) error
	Archive(ctx context.Context, id string) error
	Restore(ctx context.Context, id string) error
	Export(ctx context.Context, w io.Writer) error
	Import(ctx context.Context, r io.Reader) error
	Subscribe(ctx context.Context) (<-chan Event, error)
}
```

**Corrected — decomposed by capability, composed where needed:**
```go
type PartnerReader interface {
	Get(ctx context.Context, id string) (*Partner, error)
	List(ctx context.Context) ([]*Partner, error)
}

type PartnerWriter interface {
	Create(ctx context.Context, p *Partner) error
	Update(ctx context.Context, p *Partner) error
	Delete(ctx context.Context, id string) error
}

type PartnerStore interface {
	PartnerReader
	PartnerWriter
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** When consumers depend on a narrow interface (often just `PartnerReader`), test doubles only need to implement the methods actually exercised, and the production type's freedom to add unrelated methods is no longer constrained by every consumer's mock.

## Receivers — consistent within a type

**What Google/Effective Go says:** "Prefer pointer receivers... a mix of pointer and value receivers for the same type is generally bad practice." Also see the mirrored naming-focused rule in [naming.md](naming.md#receivers-consistent-value-vs-pointer-within-a-type). ([Best Practices: Receiver type](https://google.github.io/styleguide/go/decisions#receiver-type))

**How to detect it:** For each type, list receivers across all its methods. Flag any type with a mix of `T` and `*T` receivers, unless the type is a small, clearly-immutable value type in a package that's deliberately value-only.

**Example violation:**
```go
func (c Config) Name() string      { return c.name }  // value receiver
func (c *Config) SetName(s string) { c.name = s }     // pointer receiver
```

**Corrected:**
```go
func (c *Config) Name() string      { return c.name }
func (c *Config) SetName(s string)  { c.name = s }
```

**Severity:** Violation

**Enforced by:** not a single dedicated `golangci-lint` rule; `govet`'s general analyses (part of `enable-all`) catch some related mistakes, but mixed receivers themselves require a manual check across each type's method set

**Why it matters:** Mixing receivers is confusing for readers and can hide subtle bugs — a value receiver silently operates on a copy, so mutations inside it never propagate, which is surprising next to a pointer-receiver sibling method that does mutate.

## Named returns only for documentation, not control flow

**What Google/Effective Go says:** Google's guide treats named result parameters as a documentation aid, not a mechanism to rely on for bare `return` statements: use them "if it helps communicate meaning... when two return values would otherwise have the same type and be ambiguous" — see [Effective Go: Named result parameters](https://go.dev/doc/effective_go#named-results) and Google's [Style Decisions on doc comments for exported items](https://google.github.io/styleguide/go/decisions#named-result-parameters).

**How to detect it:** Grep for named returns followed by a bare `return` (no arguments) in a function body longer than ~15 lines. Long functions with bare returns hide what value is actually flowing out at each exit point.

**Example violation:**
```go
func ParseRange(s string) (start, end int, err error) {
	parts := strings.Split(s, "-")
	if len(parts) != 2 {
		err = fmt.Errorf("invalid range %q", s)
		return
	}
	start, err = strconv.Atoi(parts[0])
	if err != nil {
		return
	}
	end, err = strconv.Atoi(parts[1])
	if err != nil {
		return
	}
	return
}
```

**Corrected — named returns purely for godoc clarity, explicit values at every exit:**
```go
// ParseRange parses "start-end" into its two integer bounds.
func ParseRange(s string) (start, end int, err error) {
	parts := strings.Split(s, "-")
	if len(parts) != 2 {
		return 0, 0, fmt.Errorf("invalid range %q: %w", s, errInvalidRange)
	}
	start, err = strconv.Atoi(parts[0])
	if err != nil {
		return 0, 0, err
	}
	end, err = strconv.Atoi(parts[1])
	if err != nil {
		return 0, 0, err
	}
	return start, end, nil
}
```

**Severity:** Suggestion

**Enforced by:** `revive/unreachable-code` and `revive/if-return` catch narrower related mistakes; bare returns after long function bodies are not directly flagged by any linter in this config

**Why it matters:** Named returns are excellent free documentation on the function signature (`(start, end int, err error)` tells the reader what three things come back), but relying on bare `return` to send those values back forces the reader to scroll up to remember what's in flight at that exact point.

## Defer cleanup at the point of ownership handoff

**What Google/Effective Go says:** "Whenever a function creates an object that needs to be cleaned up... that responsibility should be discharged with `defer`, as close as possible to the object's creation." ([Best Practices: Defer to clean up](https://google.github.io/styleguide/go/best-practices#defer)) See also [concurrency.md](concurrency.md#defer-cleanup-immediately-after-a-resource-is-acquired) for the goroutine-lifecycle variant of this rule.

**How to detect it:** For every function that acquires a resource (`os.Open`, `sql.DB.Begin`, a mutex `Lock`, an `http.Response.Body`), check whether the corresponding cleanup (`Close`, `Rollback`/`Commit`, `Unlock`) appears as a `defer` on the line immediately after acquisition — not scattered before each `return`.

**Example violation:**
```go
func ReadPartnerConfig(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	b, err := io.ReadAll(f)
	if err != nil {
		f.Close() // easy to forget on every new return path
		return nil, err
	}
	f.Close()
	return b, nil
}
```

**Corrected:**
```go
func ReadPartnerConfig(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	return io.ReadAll(f)
}
```

**Severity:** Violation

**Enforced by:** `bodyclose` (specifically for `http.Response.Body`); general resource-close patterns beyond HTTP responses are not mechanically enforced in this config and rely on code review

**Why it matters:** Deferring cleanup immediately after acquisition means every future `return` added to the function is automatically safe — nobody has to remember to add the matching cleanup call on a new exit path.

## How to audit Go code against these rules

1. For every exported function with more than 4 parameters: flag and suggest an option struct.
2. For every option struct: confirm it does NOT contain a `context.Context` field.
3. For every function accepting `context.Context`: confirm it's parameter 1.
4. For every variadic option type: check that each option takes arguments rather than encoding state via presence.
5. Grep function signatures for 2+ `bool` parameters — suggest a named type or option struct.
6. For every channel parameter: grep `chan ` (with trailing space, no arrow) in function signatures. If the channel is read-only or write-only in the function body, the signature should say so.
7. For every interface declaration: count methods. More than ~6 is worth a second look at whether it's doing too much.
8. For every type with methods: list all methods and check that receivers are consistent (all `T` or all `*T`).
9. Grep named returns followed by a bare `return` in functions longer than ~15 lines — check whether the exit-time values are still obvious to a reader.
10. For every function that acquires a closeable/unlockable resource: confirm cleanup is a `defer` immediately after acquisition, not duplicated before each return.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
