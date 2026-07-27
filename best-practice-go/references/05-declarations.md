<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 5. Declarations

How and where you declare variables shapes how easy a function is to read
and how many bugs sneak in through unintended zero values or overly broad
scope. This chapter draws from [Google Best Practices:
Variables](https://google.github.io/styleguide/go/best-practices#variables)
and [Zero
values](https://google.github.io/styleguide/go/best-practices#zero-values),
[Effective Go: Data](https://go.dev/doc/effective_go#allocation_new) (`new`
vs. composite literals) and
[Semicolons](https://go.dev/doc/effective_go#semicolons), and Uber's
guidance on [Top-level Variable
Declarations](https://github.com/uber-go/guide/blob/master/style.md#top-level-variable-declarations),
[Local Variable
Declarations](https://github.com/uber-go/guide/blob/master/style.md#local-variable-declarations),
[nil is a valid
slice](https://github.com/uber-go/guide/blob/master/style.md#nil-is-a-valid-slice),
[Reduce Scope of
Variables](https://github.com/uber-go/guide/blob/master/style.md#reduce-scope-of-variables),
[Use var for Zero Value
Structs](https://github.com/uber-go/guide/blob/master/style.md#use-var-for-zero-value-structs),
[Initializing Struct
References](https://github.com/uber-go/guide/blob/master/style.md#initializing-struct-references),
and [Initializing
Maps](https://github.com/uber-go/guide/blob/master/style.md#initializing-maps).
Struct literal conventions get deeper treatment in [Chapter
6](06-types.md); slice/map capacity and copying semantics are in
[Chapter 7](07-slices-maps-arrays.md).

## 5.1 Use `:=` when the type is obvious from the right-hand side; use `var` when it isn't, or when you want the zero value.

> Why? `:=` is the idiomatic default because it's shorter and the type
> is inferred from an explicit initializer. Reach for `var` when there's
> no meaningful initial value yet, or when spelling out the type makes
> the code clearer than inferring it
> ([Uber Style: Local Variable
> Declarations](https://github.com/uber-go/guide/blob/master/style.md#local-variable-declarations)).

```go
// bad — var with an obvious inferred type adds no clarity
var count = 0
var name = "widget"

// good
count := 0
name := "widget"

// good — var makes sense here: no initializer yet, zero value is wanted
var buf bytes.Buffer
var total float64
```

> Enforced by: `revive` `var-declaration` (flags redundant type/value
> combinations such as `var x int = 0` and needless `var` where `:=`
> would be clearer, and vice versa).

## 5.2 Don't use `x := 0` when you mean the zero value — prefer `var x int`.

> Why? `var x int` communicates "start at the zero value" directly; `x
> := 0` forces the reader to notice that `0` happens to be `int`'s zero
> value rather than a meaningful starting point. This matters more as
> types get more complex — `var s []string` vs. `s := []string{}` signals
> different intent (see [Chapter 7](07-slices-maps-arrays.md) on nil vs.
> empty slices) ([Google Best Practices: Zero
> values](https://google.github.io/styleguide/go/best-practices#zero-values)).

```go
// bad
x := 0
s := ""
var errs []error
errs = append(errs, nil) // works, but the ":=0" pattern above obscures the zero-value intent elsewhere

// good
var x int
var s string
var errs []error
```

## 5.3 Prefer `&T{}` over `new(T)` for composite types; reserve `new` for rare cases needing only allocation.

> Why? `&T{}` and `new(T)` both allocate a zero-valued `T` and return a
> pointer to it, but `&T{}` reads more naturally next to other composite
> literals and extends naturally when you want to set fields. `new(T)` is
> idiomatic mainly for simple scalar types where there's no literal
> syntax advantage ([Effective Go:
> Data](https://go.dev/doc/effective_go#allocation_new)).

```go
// bad
p := new(Point)
p.X = 1
p.Y = 2

// good
p := &Point{X: 1, Y: 2}
```

## 5.4 Group related top-level `var` and `const` declarations in a single block.

> Why? A `var ( ... )` block signals to the reader that these
> declarations are related and should be read together, the same way
> grouped imports signal a coherent dependency set
> ([Uber Style: Top-level Variable
> Declarations](https://github.com/uber-go/guide/blob/master/style.md#top-level-variable-declarations)).

```go
// bad
var ErrNotFound = errors.New("not found")
var ErrTimeout = errors.New("timeout")
var ErrCanceled = errors.New("canceled")

// good
var (
	ErrNotFound = errors.New("not found")
	ErrTimeout  = errors.New("timeout")
	ErrCanceled = errors.New("canceled")
)
```

## 5.5 Declare variables as close as possible to their first use.

> Why? A variable declared far from where it's used forces the reader
> to hold its declaration in mind across intervening lines. Declaring it
> right before first use keeps the reader's working context small
> ([Uber Style: Reduce Scope of
> Variables](https://github.com/uber-go/guide/blob/master/style.md#reduce-scope-of-variables)).

```go
// bad
func ProcessOrder(o Order) error {
	var total float64
	discount := computeDiscount(o)
	// ... 20 unrelated lines using o and discount ...
	total = o.Subtotal - discount
	return charge(total)
}

// good
func ProcessOrder(o Order) error {
	discount := computeDiscount(o)
	// ... 20 unrelated lines using o and discount ...
	total := o.Subtotal - discount
	return charge(total)
}
```

## 5.6 Prefer the narrowest scope that still satisfies every use of a variable.

> Why? A variable scoped to an `if` block or a single case can't leak
> into surrounding code or be reused incorrectly later. Widening scope
> "just in case" invites accidental reuse and makes the function harder
> to reason about in isolation ([Uber Style: Reduce Scope of
> Variables](https://github.com/uber-go/guide/blob/master/style.md#reduce-scope-of-variables)).

```go
// bad — err declared at function scope, reused across unrelated calls
func SyncUser(id string) error {
	var err error
	user, err := fetchUser(id)
	if err != nil {
		return err
	}
	err = saveUser(user)
	return err
}

// good — each err is scoped to its own check
func SyncUser(id string) error {
	user, err := fetchUser(id)
	if err != nil {
		return err
	}
	if err := saveUser(user); err != nil {
		return err
	}
	return nil
}
```

> Enforced by: `ineffassign` (flags assignments to a variable that are
> never read before being overwritten or going out of scope — a common
> symptom of declaring at too wide a scope).

## 5.7 Use `var s SomeStruct` for a zero-value struct instead of `s := SomeStruct{}`.

> Why? When every field should start at its zero value, `var` states
> that intent directly and is shorter than an empty composite literal.
> Reserve `T{}` literal syntax for when you're actually setting fields
> ([Uber Style: Use var for Zero Value
> Structs](https://github.com/uber-go/guide/blob/master/style.md#use-var-for-zero-value-structs)).

```go
// bad
user := User{}
user.Name = "Ana"

// good
var user User
user.Name = "Ana"
```

## 5.8 Initialize struct references with `&T{}`, not `new(T)` followed by field assignment.

> Why? `&T{Field: value}` sets fields at the point of construction in
> one expression; `new(T)` followed by several assignment statements
> spreads construction across multiple lines with no benefit
> ([Uber Style: Initializing Struct
> References](https://github.com/uber-go/guide/blob/master/style.md#initializing-struct-references)).

```go
// bad
u := new(User)
u.Name = "Ana"
u.Email = "ana@example.com"

// good
u := &User{
	Name:  "Ana",
	Email: "ana@example.com",
}
```

## 5.9 Initialize maps with `make(map[K]V, size)` or a literal — never `var m map[K]V` followed by writes.

> Why? A `nil` map (the zero value of a map type) panics on write. If
> you intend to populate the map, initialize it explicitly with `make`
> or a composite literal; only leave a map as its `nil` zero value when
> you genuinely won't write to it in that branch
> ([Uber Style: Initializing
> Maps](https://github.com/uber-go/guide/blob/master/style.md#initializing-maps)).

```go
// bad
var counts map[string]int
counts["widgets"] = 1 // panics: assignment to entry in nil map

// good
counts := make(map[string]int)
counts["widgets"] = 1

// good — literal form when initial contents are known
counts := map[string]int{
	"widgets": 1,
	"gadgets": 2,
}
```

## 5.10 Remember that a `nil` slice is valid and usable — don't force an empty literal just to avoid `nil`.

> Why? Unlike maps, a `nil` slice supports `len()`, `range`, and
> `append()` without panicking, so `var s []string` is a perfectly
> functional zero value and the idiomatic way to declare "no items yet"
> ([Uber Style: nil is a valid
> slice](https://github.com/uber-go/guide/blob/master/style.md#nil-is-a-valid-slice)).

```go
// bad — forces an allocation with no behavioral benefit over nil
results := []string{}
for _, id := range ids {
	if valid(id) {
		results = append(results, id)
	}
}

// good — nil slice behaves identically for len/range/append
var results []string
for _, id := range ids {
	if valid(id) {
		results = append(results, id)
	}
}
```

## 5.11 Don't use naked semicolons or C-style statement terminators; let Go's parser insert them.

> Why? Go's lexer automatically inserts semicolons at the end of lines
> that look like the end of a statement, which is why Go code has no
> visible semicolons. Writing them explicitly is dead code that
> `gofmt` will strip and that signals unfamiliarity with the language
> ([Effective Go: Semicolons](https://go.dev/doc/effective_go#semicolons)).

```go
// bad
x := 1;
y := 2;
z := x + y;

// good
x := 1
y := 2
z := x + y
```

## 5.12 Declare multiple related variables of the same type on one line only when it improves readability, not by default.

> Why? `a, b := 1, 2` can be clear for tightly related pairs (like
> multi-value returns) but becomes unreadable once the values or types
> diverge conceptually. Default to separate declarations unless the
> grouping itself carries meaning
> ([Uber Style: Local Variable
> Declarations](https://github.com/uber-go/guide/blob/master/style.md#local-variable-declarations)).

```go
// bad — unrelated values crammed onto one line
name, retries, ok := "widget", 3, true

// good — related pair from a single logical operation
min, max := bounds(values)

// good — unrelated values declared separately
name := "widget"
retries := 3
```

## 5.13 Don't assign a value that gets overwritten before it is ever read.

> Why? An assignment whose result is discarded by a subsequent
> unconditional assignment is dead code — it either signals a bug (you
> meant to use the first value somewhere) or a leftover from a refactor
> that should be deleted.

```go
// bad — the first assignment to total is never read
func Sum(values []int) int {
	total := 0
	total = 0
	for _, v := range values {
		total += v
	}
	return total
}

// good
func Sum(values []int) int {
	total := 0
	for _, v := range values {
		total += v
	}
	return total
}
```

> Enforced by: `wastedassign`.

## 5.14 Don't convert a value to the type it already has.

> Why? `T(x)` where `x` is already of type `T` is a no-op conversion
> that adds visual noise and can mask a genuine type mismatch the
> author intended to fix but didn't.

```go
// bad
var count int = 5
scaled := int(count) * 2

// good
var count int = 5
scaled := count * 2
```

> Enforced by: `unconvert`.

## 5.15 Don't shadow predeclared identifiers when declaring local variables.

> Why? This is the declaration-site half of the naming rule in
> [Chapter 2](02-names.md#215-dont-redefine-built-in-identifiers-len-cap-min-max-new-error-as-variable-or-parameter-names):
> declaring a local `var new int` or `var len string` removes access to
> the built-in for the rest of the enclosing scope, which surfaces as a
> confusing compiler error far from the actual declaration.

```go
// bad
func Truncate(s string, max int) string {
	len := len(s)
	if len > max {
		return s[:max]
	}
	return s
}

// good
func Truncate(s string, max int) string {
	length := len(s)
	if length > max {
		return s[:max]
	}
	return s
}
```

> Enforced by: `revive` `redefines-builtin-id`.

## 5.16 (Suggestion) Watch for silent truncation when narrowing integer types; validate the range explicitly for untrusted input.

> Why? Converting a wider integer type to a narrower one (`int64` to
> `int32`, `int` to `uint8`) silently wraps on overflow instead of
> failing loudly. This matters most when the value comes from
> user-controlled input, file offsets, or network data, but is often a
> non-issue for internal, already-bounded values — treat it as a
> Suggestion to check the call site's trust boundary, not a blanket
> Violation on every narrowing conversion.

```go
// bad — untrusted length from a request header narrowed with no bounds check
func ParseChunkSize(header string) (int32, error) {
	n, err := strconv.ParseInt(header, 10, 64)
	if err != nil {
		return 0, err
	}
	return int32(n), nil // silently wraps if n exceeds math.MaxInt32
}

// good — explicit range check before narrowing
func ParseChunkSize(header string) (int32, error) {
	n, err := strconv.ParseInt(header, 10, 64)
	if err != nil {
		return 0, err
	}
	if n < 0 || n > math.MaxInt32 {
		return 0, fmt.Errorf("chunk size %d out of range", n)
	}
	return int32(n), nil
}
```

> Enforced by: `gosec` has a check for this (G115), but many teams
> exempt it because it flags a large volume of already-safe, bounded
> conversions. Where G115 is exempted, rely on code review and explicit
> range checks at trust boundaries instead of a linter gate.
