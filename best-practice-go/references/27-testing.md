<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 27. Testing

Tests are the one place where this guide's own rules are deliberately
loosened, because a test's job is to fail loudly and clearly, not to be
production-hardened. This chapter draws from [Google Style Decisions:
Useful test
failures](https://google.github.io/styleguide/go/decisions#useful-test-failures)
and [Test
structure](https://google.github.io/styleguide/go/decisions#test-structure),
[Google Best Practices: Test
functions](https://google.github.io/styleguide/go/best-practices#test-functions),
[`t.Error` vs.
`t.Fatal`](https://google.github.io/styleguide/go/best-practices#t-error-vs-t-fatal),
[Test
helpers](https://google.github.io/styleguide/go/best-practices#test-helpers),
and [TestMain
entrypoint](https://google.github.io/styleguide/go/best-practices#testmain),
plus Uber's [Test
Tables](https://github.com/uber-go/guide/blob/master/style.md#test-tables)
convention. It also documents where the user's `.golangci.yml` explicitly
relaxes linting inside `_test.go` files — see [Chapter
33.5](33-linter-configuration.md) for the full rationale. [Chapter
28](28-test-doubles.md) covers fakes, stubs, and mocks specifically.

## 27.1 Write table-driven tests with named cases and drive them through `t.Run` subtests.

> Why? [Uber Style: Test
> Tables](https://github.com/uber-go/guide/blob/master/style.md#test-tables)
> and [Google Style Decisions: Test
> structure](https://google.github.io/styleguide/go/decisions#test-structure)
> both converge on table-driven tests as the default shape: one test
> function exercises many cases, each case gets an independent pass/fail
> via `t.Run`, and a failing case's name appears directly in the test
> output.

```go
// bad — repeated near-identical test functions, no shared structure
func TestAdd_Positive(t *testing.T) {
	if Add(2, 3) != 5 {
		t.Fail()
	}
}

func TestAdd_Negative(t *testing.T) {
	if Add(-2, -3) != -5 {
		t.Fail()
	}
}

// good — one table, one loop, independently reported subtests
func TestAdd(t *testing.T) {
	tests := []struct {
		name     string
		a, b     int
		want     int
	}{
		{name: "positive", a: 2, b: 3, want: 5},
		{name: "negative", a: -2, b: -3, want: -5},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := Add(tt.a, tt.b)
			if got != tt.want {
				t.Errorf("Add(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
			}
		})
	}
}
```

## 27.2 On Go 1.22+, capture the loop variable directly; do not add the pre-1.22 `tt := tt` workaround.

> Why? Before Go 1.22, `for _, tt := range tests` reused a single
> variable across iterations, so a subtest launched with `t.Parallel()`
> that closed over `tt` would see the last table entry instead of its
> own. Go 1.22 changed loop semantics so each iteration gets its own
> copy, making the manual `tt := tt` shadow unnecessary. See [Chapter
> 32.1](32-tooling-and-modernization.md) for the language change itself.

> Enforced by: copyloopvar (flags the now-unnecessary manual copy; see [Chapter 33.2](33-linter-configuration.md))

```go
// bad — was required pre-1.22, now dead code that copyloopvar flags
for _, tt := range tests {
	tt := tt // unnecessary on Go 1.22+
	t.Run(tt.name, func(t *testing.T) {
		t.Parallel()
		assertResult(t, tt)
	})
}

// good — Go 1.22+ gives each iteration its own tt automatically
for _, tt := range tests {
	t.Run(tt.name, func(t *testing.T) {
		t.Parallel()
		assertResult(t, tt)
	})
}
```

## 27.3 Call `t.Helper()` at the top of every test helper function.

> Why? [Google Best Practices: Test
> helpers](https://google.github.io/styleguide/go/best-practices#test-helpers)
> explains that `t.Helper()` tells the testing package to attribute a
> failure to the helper's caller's line number, not the line inside the
> helper. Without it, every failure reported from a shared helper points
> at the same unhelpful line regardless of which call site triggered it.

```go
// bad — a failure always reports the line inside assertStatus, not the caller
func assertStatus(t *testing.T, got, want int) {
	if got != want {
		t.Errorf("status = %d, want %d", got, want)
	}
}

// good — t.Helper() attributes the failure to the calling test's line
func assertStatus(t *testing.T, got, want int) {
	t.Helper()
	if got != want {
		t.Errorf("status = %d, want %d", got, want)
	}
}
```

## 27.4 Register cleanup with `t.Cleanup` instead of `defer` inside a test or helper.

> Why? `t.Cleanup` runs even if the test calls `t.Fatal` from a different
> function than the one that registered the cleanup, and cleanups
> registered by a helper run before the helper returns control, not just
> when the enclosing test function exits. `defer` inside a helper cleans
> up when the *helper* returns, which is usually too early if the
> resource needs to live for the rest of the test.

```go
// bad — defer inside a helper releases the resource before the test using it runs
func newTempDB(t *testing.T) *DB {
	db := openTestDB()
	defer db.Close() // closes immediately when newTempDB returns
	return db
}

// good — t.Cleanup ties the resource's lifetime to the whole test
func newTempDB(t *testing.T) *DB {
	t.Helper()
	db := openTestDB()
	t.Cleanup(func() {
		db.Close()
	})
	return db
}
```

## 27.5 Use `t.Fatal`/`t.Fatalf` when a failed check makes the rest of the test meaningless; use `t.Error`/`t.Errorf` when later checks can still run independently.

> Why? [Google Best Practices: `t.Error` vs.
> `t.Fatal`](https://google.github.io/styleguide/go/best-practices#t-error-vs-t-fatal)
> distinguishes "this precondition failing means everything after it is
> garbage" (`Fatal`) from "this is one of several independent assertions"
> (`Error`). Using `Fatal` everywhere hides other real failures in the
> same run; using `Error` everywhere can cascade into confusing nil
> dereferences after a setup step silently failed.

```go
// bad — Error after a failed setup step; the nil client causes a panic below
func TestClient_Get(t *testing.T) {
	client, err := NewClient(testConfig)
	if err != nil {
		t.Errorf("NewClient() error = %v", err) // test keeps running with client == nil
	}
	resp, err := client.Get("/health") // panics: client is nil
	if err != nil {
		t.Errorf("Get() error = %v", err)
	}
	_ = resp
}

// good — Fatal on setup failure; Error on independent assertions after
func TestClient_Get(t *testing.T) {
	client, err := NewClient(testConfig)
	if err != nil {
		t.Fatalf("NewClient() error = %v", err)
	}

	resp, err := client.Get("/health")
	if err != nil {
		t.Errorf("Get() error = %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Errorf("status = %d, want %d", resp.StatusCode, http.StatusOK)
	}
}
```

## 27.6 Write failure messages in "got X, want Y" form with enough context to diagnose without re-running the test.

> Why? [Google Style Decisions: Useful test
> failures](https://google.github.io/styleguide/go/decisions#useful-test-failures)
> requires that a failure message alone — as seen in CI output — is
> enough to tell what was wrong, without a debugger or local re-run. A
> bare `t.Fail()` or `"unexpected result"` gives the reader nothing to
> act on.

```go
// bad — no values in the failure message; reader must add prints to debug
func TestParse(t *testing.T) {
	got, err := Parse("2026-07-27")
	if err != nil || got.Year() != 2026 {
		t.Fail()
	}
}

// good — the failure message includes both the actual and expected values
func TestParse(t *testing.T) {
	got, err := Parse("2026-07-27")
	if err != nil {
		t.Fatalf("Parse(%q) error = %v", "2026-07-27", err)
	}
	if got.Year() != 2026 {
		t.Errorf("Parse(%q).Year() = %d, want %d", "2026-07-27", got.Year(), 2026)
	}
}
```

## 27.7 Mark independent, side-effect-free subtests with `t.Parallel()`.

> Why? [Google Best Practices: Test
> functions](https://google.github.io/styleguide/go/best-practices#test-functions)
> notes that parallel subtests cut wall-clock test time substantially in
> large table-driven suites, as long as each case doesn't share mutable
> state with its siblings.

```go
// bad — cases run sequentially even though each is fully independent
func TestValidate(t *testing.T) {
	for _, tt := range validationCases {
		t.Run(tt.name, func(t *testing.T) {
			assertValidation(t, tt)
		})
	}
}

// good — t.Parallel lets independent subtests run concurrently
func TestValidate(t *testing.T) {
	for _, tt := range validationCases {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			assertValidation(t, tt)
		})
	}
}
```

## 27.8 Do not build a panicking, `require`-style assertion helper that calls `t.Fatal` from a goroutine other than the test's own.

> Why? The `testing` package documents that `FailNow` (which backs
> `Fatal`) must be called from the goroutine running the test function,
> not from a helper goroutine spawned by the test — calling it elsewhere
> causes the test binary to hang or produce misleading output rather than
> failing cleanly. [Google Best Practices: Test
> functions](https://google.github.io/styleguide/go/best-practices#test-functions)
> assumes assertions run on the main test goroutine.

```go
// bad — t.Fatal called from a spawned goroutine; may hang the test binary
func TestWorker(t *testing.T) {
	done := make(chan struct{})
	go func() {
		defer close(done)
		result, err := worker.Process(input)
		if err != nil {
			t.Fatal(err) // wrong goroutine
		}
		_ = result
	}()
	<-done
}

// good — the error crosses back to the test goroutine before failing
func TestWorker(t *testing.T) {
	errCh := make(chan error, 1)
	go func() {
		_, err := worker.Process(input)
		errCh <- err
	}()
	if err := <-errCh; err != nil {
		t.Fatal(err)
	}
}
```

## 27.9 Accept `testing.TB`, not `*testing.T`, in helper functions shared between tests and benchmarks.

> Why? `testing.TB` is the interface implemented by both `*testing.T` and
> `*testing.B`. [Google Best Practices: Test
> helpers](https://google.github.io/styleguide/go/best-practices#test-helpers)
> recommends `testing.TB` for any helper that doesn't need
> test-only or benchmark-only methods, so the same helper works in both
> contexts without duplication.

```go
// bad — *testing.T signature forces a duplicate helper for benchmarks
func newFixture(t *testing.T) *Fixture {
	t.Helper()
	return &Fixture{DB: openTestDB(t)}
}

// good — testing.TB works for both TestXxx and BenchmarkXxx callers
func newFixture(tb testing.TB) *Fixture {
	tb.Helper()
	return &Fixture{DB: openTestDB(tb)}
}
```

## 27.10 Use `TestMain` only for expensive, process-wide setup and teardown shared by every test in the package.

> Why? [Google Best Practices:
> TestMain](https://google.github.io/styleguide/go/best-practices#testmain)
> reserves `TestMain` for setup that is genuinely shared — starting a
> single test database container, seeding a fixture once — not as a
> dumping ground for per-test logic that belongs in individual test
> functions or `t.Cleanup`.

```go
// bad — TestMain does per-test-like work that belongs in individual tests
func TestMain(m *testing.M) {
	resetDatabase() // this only needs to happen for tests that mutate data
	os.Exit(m.Run())
}

// good — TestMain owns only the expensive, package-wide resource lifecycle
var testDB *sql.DB

func TestMain(m *testing.M) {
	testDB = mustStartTestDatabase()
	code := m.Run()
	testDB.Close()
	os.Exit(code)
}
```

## 27.11 Run `go test -race` in CI for any package with concurrent code.

> Why? Go's race detector finds data races that are otherwise invisible
> in normal test runs and may only manifest under production load.
> [Google Best Practices:
> Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency)
> assumes race detection is part of the standard test loop for
> concurrent packages, not an occasional manual check.

```go
// bad — CI runs "go test ./..." only; races ship silently to production
// (Makefile)
// test:
//	go test ./...

// good — race detection runs on every CI invocation
// (Makefile)
// test:
//	go test -race ./...
```

## 27.12 Inside `_test.go` files, the project's linter relaxes `bodyclose`, `errcheck`, `errorlint`, `gosec`, `revive`, and `unparam` — use that room deliberately, not as an excuse for sloppiness.

> Why? The user's `.golangci.yml` (see [Chapter
> 33.5](33-linter-configuration.md)) explicitly disables these six
> linters for `_test.go` paths, because test code has different risk and
> readability tradeoffs than production code: a failed setup helper will
> surface as a failing test regardless of whether its error is checked,
> and DSL-style test libraries rely on patterns (dot-imports,
> unparameterized signatures) that would be flagged in production code.
> This is a deliberate, scoped exemption, not a general license to write
> test code carelessly — checked errors in tests still produce more
> useful failure messages than unchecked ones.

> Enforced by: (relaxation of) bodyclose, errcheck, errorlint, gosec, revive, unparam for `_test.go` (see [Chapter 33.5](33-linter-configuration.md))

```go
// bad — in a non-test (production) file, dropping this error is a real
// violation: errcheck is fully enforced outside _test.go
func newServer() (*Server, error) {
	srv, _ := buildServer() // errcheck flags this outside _test.go
	return srv, nil
}

// good — acceptable only in _test.go: setup helper's error is dropped
// because a failure here always surfaces as a nil-pointer test failure
// immediately afterward
func TestHandler_Serve(t *testing.T) {
	srv, _ := newTestServer() // errcheck relaxed in _test.go
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/health")
	if err != nil {
		t.Fatalf("GET /health: %v", err)
	}
	defer resp.Body.Close() // bodyclose relaxed in _test.go, but still good practice

	if resp.StatusCode != http.StatusOK {
		t.Errorf("status = %d, want %d", resp.StatusCode, http.StatusOK)
	}
}

// good — a production (non-test) file must still check the same error
func newServer() (*Server, error) {
	srv, err := buildServer()
	if err != nil {
		return nil, fmt.Errorf("build server: %w", err)
	}
	return srv, nil
}
```

## 27.13 Structure test functions as arrange-act-assert, keeping setup, execution, and verification visually distinct.

> Why? [Google Style Decisions: Test
> structure](https://google.github.io/styleguide/go/decisions#test-structure)
> expects a reader to be able to tell, at a glance, what is being set up,
> what is under test, and what is being verified. Interleaving setup and
> assertions throughout the function forces the reader to track state
> changes across the whole body.

```go
// bad — setup, execution, and assertions are interleaved
func TestOrder_Total(t *testing.T) {
	order := &Order{}
	order.AddItem(Item{Price: 10})
	if len(order.Items) != 1 {
		t.Fatalf("len(Items) = %d, want 1", len(order.Items))
	}
	order.AddItem(Item{Price: 20})
	got := order.Total()
	if got != 30 {
		t.Errorf("Total() = %d, want 30", got)
	}
}

// good — arrange, act, assert are visually separated
func TestOrder_Total(t *testing.T) {
	// Arrange.
	order := &Order{}
	order.AddItem(Item{Price: 10})
	order.AddItem(Item{Price: 20})

	// Act.
	got := order.Total()

	// Assert.
	if got != 30 {
		t.Errorf("Total() = %d, want 30", got)
	}
}
```
