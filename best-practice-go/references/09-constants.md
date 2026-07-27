<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 9. Constants

Go's `const` and `iota` give you compile-time values and lightweight enums
without a dedicated enum keyword — but that flexibility means the
conventions around them matter more than in languages with built-in enum
support. This chapter draws from [Effective Go:
Constants](https://go.dev/doc/effective_go#constants) and its
[iota](https://go.dev/doc/effective_go#constants) discussion, plus Uber's
[Start Enums at
One](https://github.com/uber-go/guide/blob/master/style.md#start-enums-at-one)
and [Avoid Using Built-In
Names](https://github.com/uber-go/guide/blob/master/style.md#avoid-using-built-in-names)
guidance. Redefining built-in identifiers as ordinary variables is covered
in [Chapter 2](02-names.md); this chapter is scoped to constant and enum
declarations specifically.

## 9.1 Group related constants in a single `const ( ... )` block.

> Why? A `const` block signals to the reader that the values inside it
> are related and meant to be considered together — the same benefit
> grouped `var` blocks provide, covered in
> [Chapter 5](05-declarations.md#54-group-related-top-level-var-and-const-declarations-in-a-single-block)
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad
const StatusPending = 0
const StatusActive = 1
const StatusClosed = 2

// good
const (
	StatusPending = 0
	StatusActive  = 1
	StatusClosed  = 2
)
```

## 9.2 Use `iota` to generate sequential constant values instead of writing them by hand.

> Why? Manually numbered constants drift out of sequence the moment
> someone inserts or reorders a line, and nothing catches the mistake.
> `iota` derives each value automatically, so insertion or reordering
> can never produce a duplicate or a gap by accident
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — manually numbered; easy to duplicate or skip a value on edit
const (
	StatusPending = 0
	StatusActive  = 1
	StatusClosed  = 2
)

// good
const (
	StatusPending = iota
	StatusActive
	StatusClosed
)
```

## 9.3 Start `iota`-based enums at one, not zero, so the zero value means "unset" or "invalid."

> Why? A Go variable's zero value is used implicitly whenever a struct
> field is left unset. If your enum's zero value is a legitimate,
> meaningful state (like `StatusPending`), an uninitialized field
> silently looks like valid data instead of an obvious bug. Skipping the
> zero value with `iota + 1` (or an explicit blank identifier) reserves
> it for "unset"
> ([Uber Style: Start Enums at
> One](https://github.com/uber-go/guide/blob/master/style.md#start-enums-at-one)).

```go
// bad — StatusPending (0) is indistinguishable from an unset field
type Status int

const (
	StatusPending Status = iota
	StatusActive
	StatusClosed
)

// good — zero value is reserved for "unknown", a genuine invalid state
type Status int

const (
	StatusUnknown Status = iota
	StatusPending
	StatusActive
	StatusClosed
)
```

## 9.4 Give enum types their own named type instead of leaving constants as untyped `int`.

> Why? A named type (`type Status int`) lets the compiler catch a
> caller who passes an unrelated `int` where a `Status` was intended,
> and it gives you a place to attach a `String()` method. Untyped
> integer constants offer neither protection
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — plain int constants; any int compiles where a status is expected
const (
	StatusUnknown = iota
	StatusPending
	StatusActive
)

func SetStatus(s int) {}

// good
type Status int

const (
	StatusUnknown Status = iota
	StatusPending
	StatusActive
)

func SetStatus(s Status) {}
```

## 9.5 Give named enum types a `String() string` method so they print and log legibly.

> Why? Without a `String()` method, printing a `Status` value with
> `%v` or `%s` just shows the underlying integer, which forces anyone
> reading a log line to cross-reference the constant definitions. A
> `String()` method — often generated rather than hand-written — makes
> logs and error messages self-explanatory
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — logs show "status=2", meaningless without reading the source
type Status int

const (
	StatusUnknown Status = iota
	StatusPending
	StatusActive
)

log.Printf("status=%d", StatusActive)

// good
type Status int

const (
	StatusUnknown Status = iota
	StatusPending
	StatusActive
)

func (s Status) String() string {
	switch s {
	case StatusPending:
		return "pending"
	case StatusActive:
		return "active"
	default:
		return "unknown"
	}
}

log.Printf("status=%s", StatusActive)
```

## 9.6 Generate `String()` methods with `go:generate stringer` instead of hand-maintaining the switch statement.

> Why? A hand-written `String()` switch has to be updated every time a
> constant is added, renamed, or removed, and nothing forces that
> update to happen. `stringer` generates the method from the constant
> declarations themselves, so it can never drift out of sync as long as
> `go generate` is re-run
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)
> — the pattern is the standard companion tool for `iota`-based enums).

```go
// bad — hand-written, has to be manually kept in sync with the const block
type Status int

const (
	StatusUnknown Status = iota
	StatusPending
	StatusActive
)

func (s Status) String() string {
	switch s {
	case StatusPending:
		return "StatusPending"
	case StatusActive:
		return "StatusActive"
	default:
		return "StatusUnknown"
	}
}

// good — generated; add a directive and let stringer maintain the method
//go:generate stringer -type=Status
type Status int

const (
	StatusUnknown Status = iota
	StatusPending
	StatusActive
)
```

## 9.7 Use untyped constants for values meant to be used across multiple numeric types.

> Why? An untyped constant (`const Pi = 3.14159`) adapts to whatever
> numeric type it's used in — `float32`, `float64`, or a custom numeric
> type — without an explicit conversion. Giving it an explicit type
> prematurely (`const Pi float64 = 3.14159`) forces every use site with
> a different numeric type to convert explicitly
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — pins Pi to float64, forcing conversions anywhere else it's used
const Pi float64 = 3.14159

func CircleAreaF32(r float32) float32 {
	return float32(Pi) * r * r // explicit conversion required
}

// good — untyped constant adapts to the context it's used in
const Pi = 3.14159

func CircleAreaF32(r float32) float32 {
	return Pi * r * r
}
```

## 9.8 Use typed constants when the value only makes sense as one specific type.

> Why? Not every constant should be untyped — a constant representing a
> specific unit (like a `time.Duration` or a domain-specific `Status`)
> is more useful when the type system enforces that it's only used
> where that type is expected
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — untyped; nothing stops passing it where a different unit is expected
const DefaultTimeout = 30 // is this seconds? milliseconds?

// good — typed as time.Duration; unambiguous and type-checked
const DefaultTimeout time.Duration = 30 * time.Second
```

## 9.9 Don't name constants or variables after built-in identifiers (`true`, `false`, `iota`, `nil`, `len`).

> Why? Go allows shadowing these predeclared identifiers because
> they're not reserved words, but a constant or variable named `true`
> or `len` silently removes access to the real built-in for the rest of
> that scope — a bug that's confusing to track down because the error
> shows up far from the shadowing declaration
> ([Uber Style: Avoid Using Built-In
> Names](https://github.com/uber-go/guide/blob/master/style.md#avoid-using-built-in-names)).

```go
// bad
const true = false // absurd, but legal — and it breaks every "true" below it in scope

const len = 10 // shadows the len() builtin for the rest of the file

// good
const maxRetries = 10
```

## 9.10 Use `iota` with explicit skips or bit-shifting for bitmask constants, not manually written powers of two.

> Why? Hand-typing `1`, `2`, `4`, `8` for bitmask flags is easy to get
> wrong once the list grows past a few entries, and a typo (`4` written
> twice) silently breaks the bitmask. `iota` combined with a left-shift
> guarantees each constant is a distinct power of two
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — manually written; a repeated value silently breaks the bitmask
const (
	FlagRead    = 1
	FlagWrite   = 2
	FlagExecute = 4
	FlagDelete  = 4 // typo: duplicates FlagExecute
)

// good
const (
	FlagRead = 1 << iota
	FlagWrite
	FlagExecute
	FlagDelete
)
```

## 9.11 Keep enum constant names prefixed consistently with their type so call sites read unambiguously.

> Why? `StatusActive` and `RoleActive` are both clear on their own, but
> if two enum types both had a bare constant named `Active`, callers
> and readers would have to trace back to the type to know which one is
> meant. A consistent per-type prefix removes the ambiguity
> ([Effective Go: Constants](https://go.dev/doc/effective_go#constants)).

```go
// bad — two enums both use the unprefixed name "Active"
type Status int

const (
	Unknown Status = iota
	Active
)

type Role int

const (
	None Role = iota
	Active // collides in meaning with Status's Active, even though it compiles
)

// good — prefixed per type, unambiguous everywhere they're used
type Status int

const (
	StatusUnknown Status = iota
	StatusActive
)

type Role int

const (
	RoleNone Role = iota
	RoleActive
)
```
