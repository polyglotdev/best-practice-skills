<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 10. Control Structures

Go deliberately has fewer control-flow constructs than most languages —
one loop keyword, no ternary operator, `switch` without fallthrough by
default — and the idioms around them are unusually consistent across the
ecosystem. This chapter draws from [Effective Go: Control
structures](https://go.dev/doc/effective_go#control-structures) (if, for,
switch, type switch) and Uber's [Reduce
Nesting](https://github.com/uber-go/guide/blob/master/style.md#reduce-nesting)
and [Unnecessary
Else](https://github.com/uber-go/guide/blob/master/style.md#unnecessary-else)
guidance. Error-specific control flow (wrapping, sentinel checks) belongs
in the error-handling chapter of the audit skill, not here — this chapter
covers the shape of `if`/`for`/`switch` themselves. Where a rule
corresponds to a specific `revive` check or the Go 1.22 loop-variable
change, the callout after the example names it explicitly; teams should
adapt the exact linter set to their own `.golangci.yml`.

## 10.1 Use early returns to keep the common-case code path unindented.

> Why? A guard clause that returns immediately on failure keeps the
> function's main logic at the outermost indentation level, so the
> reader doesn't have to track how deeply nested the "happy path" is.
> This is the single biggest lever for readable Go control flow
> ([Uber Style: Reduce
> Nesting](https://github.com/uber-go/guide/blob/master/style.md#reduce-nesting)).

```go
// bad — happy path buried inside nested ifs
func Process(order Order) error {
	if order.Valid() {
		if order.Total > 0 {
			return charge(order)
		}
		return errors.New("total must be positive")
	}
	return errors.New("invalid order")
}

// good — guard clauses first, happy path unindented
func Process(order Order) error {
	if !order.Valid() {
		return errors.New("invalid order")
	}
	if order.Total <= 0 {
		return errors.New("total must be positive")
	}
	return charge(order)
}
```

> Enforced by: `revive` `indent-error-flow` (flags code that indents the
> "success" branch instead of the error branch).

## 10.2 Never write `else` after a block that already returns, continues, or breaks.

> Why? If the `if` branch unconditionally exits the function or loop,
> the code inside `else` runs in exactly the same conditions as code
> placed after the whole `if` statement — the `else` adds a nesting
> level for no semantic benefit
> ([Uber Style: Unnecessary
> Else](https://github.com/uber-go/guide/blob/master/style.md#unnecessary-else)).

```go
// bad
func Grade(score int) string {
	if score >= 60 {
		return "pass"
	} else {
		return "fail"
	}
}

// good
func Grade(score int) string {
	if score >= 60 {
		return "pass"
	}
	return "fail"
}
```

> Enforced by: `revive` `superfluous-else`.

## 10.3 Collapse `if cond { return true } else { return false }` shapes into a direct boolean return.

> Why? This is a special case of unnecessary `else`: when both branches
> only return a boolean literal, the whole statement can be replaced
> with the condition itself, removing four lines of pure boilerplate
> ([Uber Style: Unnecessary
> Else](https://github.com/uber-go/guide/blob/master/style.md#unnecessary-else)).

```go
// bad
func IsValid(order Order) bool {
	if order.Total > 0 {
		return true
	} else {
		return false
	}
}

// good
func IsValid(order Order) bool {
	return order.Total > 0
}
```

> Enforced by: `revive` `if-return` (flags redundant `if x { return
> true } else { return false }`, and `if x { return true }; return
> false` patterns that should collapse to `return x`).

## 10.4 Use `if err != nil { return ... }` immediately after every fallible call, not batched checks.

> Why? Checking each error immediately, right where the call happens,
> keeps the failure attributable to a specific line. Deferring error
> checks or batching several calls before checking any of them makes it
> ambiguous which call actually failed
> ([Effective Go: Control
> structures](https://go.dev/doc/effective_go#control-structures)).

```go
// bad — three calls before any error is checked; unclear which one failed
func LoadAll() error {
	a, errA := loadA()
	b, errB := loadB()
	c, errC := loadC()
	if errA != nil || errB != nil || errC != nil {
		return fmt.Errorf("load failed: %v %v %v", errA, errB, errC)
	}
	return save(a, b, c)
}

// good — each error checked at its own call site
func LoadAll() error {
	a, err := loadA()
	if err != nil {
		return fmt.Errorf("load a: %w", err)
	}
	b, err := loadB()
	if err != nil {
		return fmt.Errorf("load b: %w", err)
	}
	c, err := loadC()
	if err != nil {
		return fmt.Errorf("load c: %w", err)
	}
	return save(a, b, c)
}
```

## 10.5 Scope `err` to the narrowest `if` statement when the value is only needed for that check.

> Why? `if err := f(); err != nil { ... }` declares `err` inside the
> `if` statement's own scope, so it can't leak into surrounding code or
> be mistaken for an unrelated later error. This intentionally shadows
> any outer `err` in scope, which is the desired behavior here, not a
> bug to avoid.

```go
// bad — err declared at function scope purely to check one call
func Save(order Order) error {
	var err error
	err = validate(order)
	if err != nil {
		return err
	}
	return persist(order)
}

// good — err scoped to the if, intentionally shadowing any outer err
func Save(order Order) error {
	if err := validate(order); err != nil {
		return err
	}
	return persist(order)
}
```

> Enforced by: nothing flags this pattern as an error — it's the
> idiomatic Go form. Teams that enable `govet`'s `shadow` analyzer
> often carve out an explicit exemption for `shadow: declaration of
> "err"` specifically because this intentional-shadow pattern is so
> common; without that exemption, `govet shadow` would flag correct,
> idiomatic code.

## 10.6 Use `i++`/`i--`, never `i += 1`/`i -= 1`, for single-unit increments and decrements.

> Why? `i++` and `i--` are Go's dedicated increment/decrement
> statements — using `+=`/`-=` for the single-unit case is longer to
> read and signals unfamiliarity with the idiom
> ([Effective Go: Control
> structures](https://go.dev/doc/effective_go#for)).

```go
// bad
for i := 0; i < len(items); i += 1 {
	process(items[i])
}

// good
for i := 0; i < len(items); i++ {
	process(items[i])
}
```

> Enforced by: `revive` `increment-decrement`.

## 10.7 Prefer `for range` over manual indexing when you don't need the index, and use `for range` with no variables at all when you need neither index nor value.

> Why? `for i := 0; i < len(s); i++` re-derives what `range` already
> gives you directly, and the extra indexing is one more place to make
> an off-by-one mistake. Use the form that matches what you actually
> need from the loop
> ([Effective Go: Control
> structures](https://go.dev/doc/effective_go#for)).

```go
// bad — manual indexing when only the value is needed
for i := 0; i < len(users); i++ {
	fmt.Println(users[i].Name)
}

// good
for _, u := range users {
	fmt.Println(u.Name)
}

// good — neither index nor value needed, just repetition
for range 3 {
	retry()
}
```

> Enforced by: `revive` `range` (flags redundant value-only or
> index-only range clauses, e.g. `for i, _ := range s` or `for _, v :=
> range s` where `v` is unused).

## 10.8 Use `for range n` to iterate a fixed number of times (Go 1.22+), not a manual counter loop.

> Why? Go 1.22 added support for ranging directly over an integer,
> which replaces the classic `for i := 0; i < n; i++` counting idiom
> when the counter itself isn't used for anything but counting.

```go
// bad — legacy idiom pre-1.22: manual counter loop
for i := 0; i < 5; i++ {
	fmt.Println("tick")
}

// good — for range int (Go 1.22+)
for range 5 {
	fmt.Println("tick")
}
```

## 10.9 Capture the loop variable correctly when passing it to a goroutine or closure — but know Go 1.22+ already does this for you.

> Why? Before Go 1.22, `for _, v := range items` reused the same
> variable `v` across every iteration, so a goroutine or closure
> capturing `v` by reference could observe the wrong (usually the
> final) value unless you copied it into a new variable each iteration.
> Go 1.22 changed the language so each iteration gets its own copy of
> the loop variable, eliminating the entire bug class — but code
> running on, or intended to be compatible with, pre-1.22 toolchains
> still needs the manual copy.

```go
// bad — legacy idiom pre-1.22: without a per-iteration copy, every
// goroutine could observe the same, final value of item
for _, item := range items {
	go func() {
		process(item) // pre-1.22: item is shared across iterations
	}()
}

// bad — legacy idiom pre-1.22: manual copy, required only on old toolchains
for _, item := range items {
	item := item // shadow copy per iteration
	go func() {
		process(item)
	}()
}

// good — Go 1.22+: each iteration already has its own item; no copy needed
for _, item := range items {
	go func() {
		process(item)
	}()
}
```

> Enforced by: `copyloopvar` (flags manual per-iteration copy workarounds
> that are unnecessary once the module's Go version is 1.22+, and can
> also flag genuine capture bugs on older language versions).

## 10.10 Avoid a bare C-style `for (;;)` when a `for` with a condition, or `for range`, expresses the loop more precisely.

> Why? Go's `for` statement can be written with no clauses at all as an
> infinite loop (`for { ... }`), with just a condition (`for cond {
> ... }`), or with the full three-clause form. Using the full
> three-clause form when only a condition is needed adds two empty
> clauses that carry no information
> ([Effective Go: Control
> structures](https://go.dev/doc/effective_go#for)).

```go
// bad — empty init/post clauses add noise
for ; retries < maxRetries; {
	retries++
}

// good
for retries < maxRetries {
	retries++
}

// good — true infinite loop, exited explicitly
for {
	if done() {
		break
	}
}
```

## 10.11 Use a tagless `switch` as a readable replacement for a long `if`/`else if` chain.

> Why? A `switch` with no expression after the keyword evaluates each
> `case` as a boolean condition, which reads as a flat, scannable list
> of conditions instead of a chain of nested `else if`s
> ([Effective Go: Control
> structures](https://go.dev/doc/effective_go#switch)).

```go
// bad
if score >= 90 {
	grade = "A"
} else if score >= 80 {
	grade = "B"
} else if score >= 70 {
	grade = "C"
} else {
	grade = "F"
}

// good
switch {
case score >= 90:
	grade = "A"
case score >= 80:
	grade = "B"
case score >= 70:
	grade = "C"
default:
	grade = "F"
}
```

## 10.12 Use a type switch to branch on an interface value's dynamic type, not a chain of type assertions.

> Why? A type switch checks every candidate type in one construct and
> lets the compiler ensure each `case` binds a correctly typed variable.
> A chain of individual type assertions repeats the interface value on
> every line and is easy to get out of sync when a type is added
> ([Effective Go: Type
> switch](https://go.dev/doc/effective_go#type_switch)).

```go
// bad — repeated assertions, easy to miss a case
func Describe(v any) string {
	if s, ok := v.(string); ok {
		return "string: " + s
	}
	if n, ok := v.(int); ok {
		return fmt.Sprintf("int: %d", n)
	}
	return "unknown"
}

// good
func Describe(v any) string {
	switch x := v.(type) {
	case string:
		return "string: " + x
	case int:
		return fmt.Sprintf("int: %d", x)
	default:
		return "unknown"
	}
}
```

## 10.13 Delete code after an unconditional `return`, `break`, `continue`, or `panic` — don't leave it unreachable.

> Why? Statements placed after an unconditional exit from that block
> can never execute. Unreachable code is either a leftover from a
> refactor or a sign the control flow doesn't do what the author
> thinks it does — either way, it should be deleted or the logic fixed.

```go
// bad — the log line can never run
func Fetch(id string) (*Item, error) {
	return nil, errors.New("not implemented")
	log.Printf("fetching %s", id) // unreachable
}

// good
func Fetch(id string) (*Item, error) {
	log.Printf("fetching %s", id)
	return nil, errors.New("not implemented")
}
```

> Enforced by: `revive` `unreachable-code`.

## 10.14 Avoid labeled `break`/`continue` except when breaking out of a nested loop from an inner `switch` or `select`.

> Why? Labels are Go's only mechanism for breaking or continuing an
> outer loop from inside a nested construct — `break` alone inside a
> `switch` or `select` only exits that `switch`/`select`, not the
> surrounding loop. Reach for a label in that specific situation; avoid
> it anywhere a restructured guard clause or extracted function would
> read more clearly
> ([Effective Go: Control
> structures](https://go.dev/doc/effective_go#for)).

```go
// bad — break here only exits the switch, not the loop; likely a bug
func FindFirstMatch(items []Item, want string) *Item {
	for _, item := range items {
		switch item.Kind {
		case "match":
			if item.Name == want {
				break // only breaks the switch, loop continues
			}
		}
	}
	return nil
}

// good — label targets the loop explicitly
func FindFirstMatch(items []Item, want string) *Item {
	var found *Item
search:
	for _, item := range items {
		switch item.Kind {
		case "match":
			if item.Name == want {
				found = &item
				break search
			}
		}
	}
	return found
}
```
