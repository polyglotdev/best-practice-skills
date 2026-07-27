<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 12. Options

Every exported function eventually faces the same pressure: a caller needs
one more knob. This chapter is about resisting the urge to add another
positional parameter and instead choosing, deliberately, from three shapes —
plain positional arguments, an options struct, or functional options. It
draws from [Google Best Practices:
Options](https://google.github.io/styleguide/go/best-practices#options) for
when and why to introduce an option type, and from [Uber Style: Functional
Options](https://github.com/uber-go/guide/blob/master/style.md#functional-options)
for the canonical `Option` implementation. Constructor patterns in general
are covered alongside [Chapter 9](09-constructors.md); this chapter is
specifically about configuring optional behavior, not about zero values or
construction sequencing.

## 12.1 Keep positional parameters until a function's signature actually gets hard to read.

> Why? Introducing an options abstraction has a real cost: more types, more
> indirection, and a less obvious call site for the common case. [Google
> Best Practices: Options](https://google.github.io/styleguide/go/best-practices#options)
> is explicit that these techniques are for when parameter lists have grown
> unwieldy, not a default starting point. Reach for them only once a
> function has several optional or rarely-changed parameters.

```go
// bad — reaching for functional options on a two-argument function
type OpenOption func(*openConfig)

func WithTimeout(d time.Duration) OpenOption { /* ... */ return nil }

func Open(addr string, opts ...OpenOption) (*Connection, error) {
	return nil, nil
}

// good — two required parameters read fine as plain arguments
func Open(addr string, timeout time.Duration) (*Connection, error) {
	return nil, nil
}
```

## 12.2 Once a function's parameter list gets long or growth-prone, stop adding positional parameters.

> Why? As [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> notes, "as more parameters are added to a function, the role of individual
> parameters becomes less clear, and adjacent parameters of the same type
> become easier to confuse." A call site with six same-typed booleans and
> strings in a row is unreadable and easy to get wrong without the compiler
> noticing.

```go
// bad
func EnableReplication(ctx context.Context, cfg *replicator.Config, primaryRegions, readonlyRegions []string, replicateExisting, overwritePolicies bool, interval time.Duration, workers int) error {
	return nil
}

// good — grouped into a config the call site must name explicitly
func EnableReplication(ctx context.Context, opts ReplicationOptions) error {
	return nil
}
```

## 12.3 Use an option struct when most callers need to set most fields, or when the values must be inspected or compared later.

> Why? [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> favors the option-struct shape when the values are frequently all
> required together, when they need to be constructed programmatically, or
> when logging/comparing the whole set of options is useful. A plain struct
> is also easier for callers to build with partial literals, since unset
> fields default to their zero values.

```go
// bad — caller must remember six positional arguments in order
func EnableReplication(ctx context.Context, cfg *replicator.Config, regions []string, existing, overwrite bool, interval time.Duration) error {
	return nil
}

// good
type ReplicationOptions struct {
	Config              *replicator.Config
	PrimaryRegions      []string
	ReplicateExisting   bool
	OverwritePolicies   bool
	ReplicationInterval time.Duration
}

func EnableReplication(ctx context.Context, opts ReplicationOptions) error {
	return nil
}
```

## 12.4 Never put a `context.Context` inside an option struct or a functional-options config.

> Why? [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> states plainly that contexts are never included in option structs. A
> context has request-scoped lifetime semantics that don't belong bundled
> with static configuration, and burying it inside a struct hides it from
> the conventional first-parameter position callers expect (see [Chapter
> 19](19-context.md)).

```go
// bad
type ReplicationOptions struct {
	Ctx    context.Context
	Config *replicator.Config
}

func EnableReplication(opts ReplicationOptions) error {
	return nil
}

// good — ctx stays a normal first parameter
func EnableReplication(ctx context.Context, opts ReplicationOptions) error {
	return nil
}
```

## 12.5 Prefer functional options when many callers only need a small subset of settings, or when the set of options must grow without breaking callers.

> Why? [Uber Style: Functional
> Options](https://github.com/uber-go/guide/blob/master/style.md#functional-options)
> recommends this pattern for "optional arguments in constructors and other
> public APIs that you foresee needing to expand, especially if you already
> have three or more arguments." Unlike an option struct, adding a new
> `WithX` function is always backward compatible — existing call sites
> don't need to change.

```go
// bad — every new setting requires touching every call site's struct literal
type Options struct {
	Cache  bool
	Logger *slog.Logger
}

func Open(addr string, opts Options) (*Connection, error) {
	return nil, nil
}

// good — new WithX functions can be added later without breaking callers
func Open(addr string, opts ...Option) (*Connection, error) {
	return nil, nil
}
```

## 12.6 Define `Option` as a function type that mutates an unexported config struct.

> Why? This is the canonical shape from both [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> and [Uber Style: Functional
> Options](https://github.com/uber-go/guide/blob/master/style.md#functional-options).
> Keeping the config type unexported restricts option construction to
> functions the package author controls, which keeps the option set closed
> and documented, while `Option` itself stays a small, easily testable
> value.

```go
// bad — caller mutates configuration directly, bypassing validation and docs
func Open(addr string, cache bool, logger *slog.Logger) (*Connection, error) {
	return nil, nil
}

// good
type config struct {
	cache  bool
	logger *slog.Logger
}

// Option configures a call to Open.
type Option func(*config)

func WithCache(enabled bool) Option {
	return func(c *config) { c.cache = enabled }
}

func WithLogger(l *slog.Logger) Option {
	return func(c *config) { c.logger = l }
}

func Open(addr string, opts ...Option) (*Connection, error) {
	cfg := config{logger: slog.Default()}
	for _, opt := range opts {
		opt(&cfg)
	}
	return dial(addr, cfg)
}
```

## 12.7 Guarantee the zero value of the config works — apply defaults before running options.

> Why? A function called with no options at all (`Open(addr)`) must behave
> sensibly. [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> shows building a `DefaultReplicationOptions` slice and applying it first;
> options passed by the caller then override defaults, in order, rather
> than the caller being forced to specify every field just to get a working
> call.

```go
// bad — no defaults; a caller who forgets WithLogger gets a nil logger
func Open(addr string, opts ...Option) (*Connection, error) {
	var cfg config
	for _, opt := range opts {
		opt(&cfg)
	}
	return dial(addr, cfg) // cfg.logger is nil unless the caller set it
}

// good — defaults are applied before user options, so the zero-args
// call is always valid
func Open(addr string, opts ...Option) (*Connection, error) {
	cfg := config{
		cache:  false,
		logger: slog.Default(),
	}
	for _, opt := range opts {
		opt(&cfg)
	}
	return dial(addr, cfg)
}
```

## 12.8 Give boolean options a parameter, don't encode the value in the function's presence.

> Why? [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> warns that "binary settings should accept a boolean... rather than"
> two separately named functions, because callers who must choose the value
> programmatically are otherwise forced to change which functions they call
> instead of simply changing an argument.

```go
// bad — caller must branch on which function to call
func EnableFailFast() Option { return func(c *config) { c.failFast = true } }
func DisableFailFast() Option { return func(c *config) { c.failFast = false } }

// good — caller passes a value, which composes with a variable
func FailFast(enabled bool) Option {
	return func(c *config) { c.failFast = enabled }
}

func dial(shouldFailFast bool) []Option {
	return []Option{FailFast(shouldFailFast)}
}
```

## 12.9 Give enumerated options a typed constant parameter, not one function per choice.

> Why? The same reasoning in [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> extends to enumerations: `log.Format(log.Capacitor)` is preferable to
> `log.CapacitorFormat()` because it lets a caller select the format
> dynamically, and because adding a new format later doesn't require a new
> top-level function name.

```go
// bad
func JSONFormat() Option  { return func(c *config) { c.format = formatJSON } }
func TextFormat() Option  { return func(c *config) { c.format = formatText } }

// good
type Format int

const (
	FormatText Format = iota + 1
	FormatJSON
)

func WithFormat(f Format) Option {
	return func(c *config) { c.format = f }
}
```

## 12.10 Process options in order and let the last one win on conflict.

> Why? [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> specifies that "in general, options should be processed in order. If
> there is a conflict... the last argument should win." Predictable
> last-write-wins semantics let callers layer defaults, environment-derived
> options, and explicit overrides without surprises.

```go
// bad — options applied in reverse, so explicit overrides are silently lost
func Open(addr string, opts ...Option) (*Connection, error) {
	cfg := config{logger: slog.Default()}
	for i := len(opts) - 1; i >= 0; i-- {
		opts[i](&cfg)
	}
	return dial(addr, cfg)
}

// good — forward order, last matching option wins
func Open(addr string, opts ...Option) (*Connection, error) {
	cfg := config{logger: slog.Default()}
	for _, opt := range opts {
		opt(&cfg)
	}
	return dial(addr, cfg)
}

// caller can layer a base profile then override just one field
func dialWithOverride(addr string, baseProfile []Option, requestLogger *slog.Logger) (*Connection, error) {
	opts := append(baseProfile, WithLogger(requestLogger))
	return Open(addr, opts...)
}
```

## 12.11 Keep the option constructor functions exported, but the config type and its fields unexported.

> Why? [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> treats the option's target struct as an implementation detail: "the
> parameter to the option function is generally unexported... to restrict
> the options to being defined only within the package itself." This keeps
> the set of valid options closed and documented via godoc on the `WithX`
> functions instead of via struct field visibility.

```go
// bad — exported config lets callers bypass the WithX functions entirely
// and mutate fields the package never validated
type Config struct {
	Cache  bool
	Logger *slog.Logger
}

func Open(addr string, cfg *Config) (*Connection, error) {
	return nil, nil
}

// good — config stays unexported; WithCache/WithLogger are the only way in
type config struct {
	cache  bool
	logger *slog.Logger
}

func WithCache(enabled bool) Option {
	return func(c *config) { c.cache = enabled }
}
```

## 12.12 Document each option's default and whether repeating it accumulates or overwrites.

> Why? [Google Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> calls out that some options (like adding read-only regions) are
> cumulative across repeated calls, while others (like an interval) simply
> overwrite. Without a comment stating which, callers can't predict what
> passing the same `Option` twice does.

```go
// bad — unclear whether calling this twice adds cells or replaces them
func ReadonlyCells(cells ...string) Option {
	return func(c *config) {
		c.readonlyCells = append(c.readonlyCells, cells...)
	}
}

// good
// ReadonlyCells adds additional cells that should contain read-only
// replicas of the data. Passing this option multiple times appends
// to the existing list rather than replacing it.
//
// Default: none
func ReadonlyCells(cells ...string) Option {
	return func(c *config) {
		c.readonlyCells = append(c.readonlyCells, cells...)
	}
}
```

## 12.13 Don't use functional options merely to avoid naming a struct — prefer the option struct when there is no forward-compatibility need.

> Why? Functional options carry real implementation overhead: an `Option`
> type, a `WithX` function per field, and a loop to apply them. [Google
> Best Practices:
> Options](https://google.github.io/styleguide/go/best-practices#options)
> frames the option struct as the simpler default and functional options as
> the "more advanced" technique reserved for APIs that need per-field
> optionality or backward-compatible growth. Internal or low-traffic
> functions rarely need that flexibility.

```go
// bad — functional options for an unexported helper with two fixed fields
type reportOption func(*reportConfig)

func withHeader(h string) reportOption {
	return func(c *reportConfig) { c.header = h }
}

func buildReport(opts ...reportOption) *reportConfig {
	var cfg reportConfig
	for _, opt := range opts {
		opt(&cfg)
	}
	return &cfg
}

// good — a plain struct is simpler and just as clear for internal use
type reportConfig struct {
	header string
	footer string
}

func buildReport(cfg reportConfig) *reportConfig {
	return &cfg
}
```
