# Testing — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md) — and see the dedicated **Test-file linter relaxations** section near the end of this file, since several rules elsewhere in this guide are deliberately *not* enforced inside `_test.go`.

Tests are code, but tests carry an extra responsibility: when they fail, the message should make it obvious what's broken without requiring the reader to step into a debugger. The style guide's testing rules push toward inline assertions, table-driven tests, and the discipline that failure handling belongs in the `Test` function — not in helpers.

## Test logic belongs in the Test function, not in assertion helpers

**What Google/Effective Go says:** Go doesn't have RSpec-style `should_equal` matchers. "Bugs are easier to diagnose when failure messages... clearly express the failing property." The idiomatic pattern is: call the function under test, compare the result to what you expected, and report the diff inline. ([Best Practices: Test functions](https://google.github.io/styleguide/go/best-practices#assert-tests))

**How to detect it:** Grep for functions named `assert*` or `expect*` that take `*testing.T`. Each is a candidate assertion-helper antipattern.

**Example violation (assertion-helper antipattern):**
```go
func assertPartnerEqual(t *testing.T, got, want *Partner) {
	if got.Name != want.Name {
		t.Fatalf("Name mismatch: got %q want %q", got.Name, want.Name)
	}
	if got.Status != want.Status {
		t.Fatalf("Status mismatch: got %q want %q", got.Status, want.Status)
	}
}

func TestLoadPartner(t *testing.T) {
	got := loadPartner("acme")
	assertPartnerEqual(t, got, &Partner{Name: "Acme", Status: "active"})
}
```

This hides the actual assertion from `TestLoadPartner` and forces the reader to jump to `assertPartnerEqual` to understand what failed.

**Corrected (inline diff via cmp):**
```go
func TestLoadPartner(t *testing.T) {
	got := loadPartner("acme")
	want := &Partner{Name: "Acme", Status: "active"}
	if diff := cmp.Diff(want, got); diff != "" {
		t.Errorf("loadPartner mismatch (-want +got):\n%s", diff)
	}
}
```

Now the test failure shows the diff inline, and the reader sees the whole story in one function.

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a readability convention, not a mechanical rule

**Why it matters:** When the comparison logic lives in the `Test` function itself, a failing test's stack trace points directly at the meaningful line; when it's buried in a shared assertion helper, every failure looks the same and the reader must open a second function to learn what actually differed.

## `t.Helper()` is for setup, not for assertions

**What Google/Effective Go says:** `t.Helper()` exists for genuine helpers — functions that perform setup or cleanup, where the helper failing means "the test environment is wrong," not "the system under test is wrong." ([Best Practices: Argument checking in helpers](https://google.github.io/styleguide/go/best-practices#assert-tests))

**How to detect it:** Grep `t.Helper()` inside functions whose body calls `t.Error`/`t.Errorf` for equality comparisons (not just `t.Fatal` for setup preconditions). These are likely assertion helpers, not setup helpers.

**Acceptable — genuine setup helper:**
```go
func mustWriteFile(t *testing.T, path string, data []byte) {
	t.Helper()
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatalf("setup: write %s: %v", path, err)
	}
}
```

**Not acceptable — assertion helper wearing a setup-helper's clothing:**
```go
func assertEq(t *testing.T, got, want any) {
	t.Helper() // smell: this is an assertion helper, not a setup helper
	if got != want {
		t.Errorf("got %v, want %v", got, want)
	}
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** `t.Helper()` exists to correct failure-line attribution for genuine setup/cleanup code; using it to paper over an assertion helper hides both the antipattern and, ironically, still doesn't fully solve the "which case failed" problem that inlining the assertion would.

## Use `t.Error`/`t.Errorf` in table-driven loops; `t.Fatal`/`t.Fatalf` ends the whole test

**What Google/Effective Go says:** "Test cases... should continue after one failure so that all the failures for a given run can be seen at once" — use `t.Error` inside a table loop, not `t.Fatal`, unless the failure is a setup precondition. ([Best Practices: Keep going](https://google.github.io/styleguide/go/best-practices#keep-going))

**How to detect it:** Grep `t.Fatal`/`t.Fatalf` inside `for _, tc := range tests {` loops at the top level (not inside `t.Run`). Each is a candidate violation.

**Example violation:**
```go
for _, tc := range tests {
	got := f(tc.in)
	if got != tc.want {
		t.Fatalf("%s: got %v want %v", tc.name, got, tc.want) // hides later failures
	}
}
```

**Corrected:**
```go
for _, tc := range tests {
	got := f(tc.in)
	if got != tc.want {
		t.Errorf("%s: got %v want %v", tc.name, got, tc.want)
	}
}
```

Or — better — use subtests, which give you both isolation and the option to use `t.Fatal` per case (see the dedicated table-driven-tests rule below).

**Severity:** Violation

**Enforced by:** not a dedicated `golangci-lint` rule; catch via the grep heuristic above

**Why it matters:** Table-driven tests exist to exercise many cases in one function; if the first failing case aborts the entire loop via `t.Fatal`, every subsequent case goes unreported and a single CI run can hide several distinct regressions behind one reported failure.

## Never call `t.Fatal` from a goroutine other than the test's main goroutine

**What Google/Effective Go says:** "`t.FailNow` (and consequently `t.Fatal`) must be called from the goroutine running the test... not from other goroutines created during the test." `runtime.Goexit` only terminates the calling goroutine, which can leave the test deadlocked or falsely passing. ([Best Practices: Uses of goroutines in tests](https://google.github.io/styleguide/go/best-practices#goroutines-in-tests))

**How to detect it:** Grep `go func() {` inside `_test.go` files. For each match, read the closure body. Any `t.Fatal*` or `t.Skip*` call inside is a violation; `t.Parallel` does not change this rule.

**Example violation:**
```go
go func() {
	if err := worker(); err != nil {
		t.Fatalf("worker: %v", err) // wrong goroutine
	}
}()
```

**Corrected — hand the result back to the main test goroutine:**
```go
errCh := make(chan error, 1)
go func() {
	errCh <- worker()
}()
if err := <-errCh; err != nil {
	t.Fatalf("worker: %v", err) // main test goroutine
}
```

Or use `t.Error` in the goroutine and `return`:
```go
go func() {
	defer wg.Done()
	if err := worker(); err != nil {
		t.Errorf("worker: %v", err) // safe: records failure
		return
	}
}()
wg.Wait()
```

**Severity:** Violation

**Enforced by:** not enforced by `golangci-lint` in this repo — `bodyclose`, `errcheck`, `errorlint`, `gosec`, `revive`, and `unparam` are all *relaxed* in `_test.go` (see the Test-file linter relaxations section below), and none of the linters remaining enabled in test files check goroutine/`t.Fatal` interaction; catch via the grep heuristic above and `go test -race`, which sometimes (not reliably) surfaces the resulting goroutine leak or panic

**Why it matters:** `t.Fatal` from a background goroutine kills only that goroutine — the test's main goroutine keeps running, unaware anything failed, and the test can then hang waiting on a channel the dead goroutine was supposed to write to, or report a false PASS.

## Use field names in table-driven struct literals

**What Google/Effective Go says:** Positional struct-literal initialization is fragile — this is the test-specific instance of [Style Decisions: Composite literals](https://google.github.io/styleguide/go/decisions#composite-literals), which requires named fields especially where the field list is likely to grow.

**How to detect it:** Grep table-driven test case slices for struct literals without field names.

**Example violation:**
```go
tests := []struct {
	name string
	in   int
	want string
}{
	{"zero", 0, "0"},
	{"one", 1, "1"},
}
```

**Corrected:**
```go
tests := []struct {
	name string
	in   int
	want string
}{
	{name: "zero", in: 0, want: "0"},
	{name: "one", in: 1, want: "1"},
}
```

**Severity:** Violation

**Enforced by:** `govet`'s `composites` analysis (part of `enable-all`) flags unkeyed struct literals of imported types; a package-local anonymous table-case struct is not always caught, so also check by hand

**Why it matters:** Adding a field to the case struct at the wrong position silently shifts every existing test case's values into the wrong fields — named fields make that class of bug a compile-time impossibility.

## Table-driven tests use `t.Run` for isolation and per-case naming

**What Google/Effective Go says:** "Table-driven tests... run as subtests via `t.Run`" to get isolated pass/fail reporting, per-case `-run` filtering, and (when combined with `t.Parallel`) per-case concurrency. ([Best Practices: Table-driven tests](https://google.github.io/styleguide/go/best-practices#table-tests)) See also [Uber: Test Tables](https://github.com/uber-go/guide/blob/master/style.md#test-tables) for the `tt`/`give`/`want` naming convention.

**How to detect it:** Grep for `for _, tc := range tests {` loops in `_test.go` files that do NOT contain a nested `t.Run(tc.name, ...)` call.

**Example violation — flat loop, no subtests:**
```go
for _, tc := range tests {
	got := f(tc.in)
	if got != tc.want {
		t.Errorf("%s: got %v want %v", tc.name, got, tc.want)
	}
}
```

**Corrected:**
```go
for _, tt := range tests {
	tt := tt // see the closure-capture rule below for when this line is/isn't needed
	t.Run(tt.name, func(t *testing.T) {
		got := f(tt.in)
		if got != tt.want {
			t.Errorf("got %v, want %v", got, tt.want)
		}
	})
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** `t.Run` gives each case its own pass/fail line in test output, lets you re-run a single failing case with `-run TestFoo/case_name`, and is a prerequisite for per-case `t.Parallel` (see below) — a flat loop gets none of these for free.

## Closure-capture pattern in table tests — the loop-variable trap

**What Google/Effective Go says:** Not covered in Google's guide directly (the underlying Go language semantics changed after the guide's baseline); documented in the [Go 1.22 release notes](https://go.dev/blog/loopvar-preview) and [Uber's Parallel Tests section](https://github.com/uber-go/guide/blob/master/style.md#parallel-tests), which predates the language change.

**How to detect it:** Check the module's `go.mod` Go version. If it declares `go 1.22` or later, the classic `tt := tt` capture line is no longer required — flag its *absence* as nothing, but don't flag its presence as wrong either (it's harmless, just redundant). If the module targets Go 1.21 or earlier, its **absence** before a `t.Parallel()` call inside a `t.Run` closure is a real bug.

**The pre-1.22 trap (legacy code, `go.mod` says `go 1.21` or earlier):**
```go
// go.mod: go 1.21
for _, tt := range tests {
	t.Run(tt.name, func(t *testing.T) {
		t.Parallel()
		// BUG on Go <1.22: tt is the SAME variable across all iterations.
		// By the time these parallel subtests actually run, the loop has
		// finished and tt holds the value from the LAST iteration for
		// every subtest.
		got := f(tt.in)
		if got != tt.want {
			t.Errorf("got %v, want %v", got, tt.want)
		}
	})
}
```

**Pre-1.22 fix — capture a per-iteration copy before the closure:**
```go
// go.mod: go 1.21
for _, tt := range tests {
	tt := tt // capture — without this line, every subtest sees the last tt
	t.Run(tt.name, func(t *testing.T) {
		t.Parallel()
		got := f(tt.in)
		if got != tt.want {
			t.Errorf("got %v, want %v", got, tt.want)
		}
	})
}
```

**Go 1.22+ — safe without the capture line, because each iteration gets its own `tt`:**
```go
// go.mod: go 1.22 or later
for _, tt := range tests {
	t.Run(tt.name, func(t *testing.T) {
		t.Parallel()
		got := f(tt.in)
		if got != tt.want {
			t.Errorf("got %v, want %v", got, tt.want)
		}
	})
}
```

**Severity:** Violation on Go <1.22 modules without the capture line; not flagged on Go 1.22+ modules either way

**Enforced by:** copyloopvar — on Go 1.22+ modules, this linter instead flags *unnecessary* `tt := tt` capture lines as redundant, since the compiler now allocates a fresh variable per iteration; see [concurrency.md](concurrency.md#go-122-loop-variable-semantics-and-copyloopvar) for the general (non-test) framing of this same rule

**Why it matters:** This is one of the most common historical sources of flaky, order-dependent table-test failures — every parallel subtest silently operating on the last table row's data instead of its own. Go 1.22 fixed the language semantics, but code and reviewers trained on the old behavior may still add (or remove) the capture line incorrectly depending on which Go version the module actually targets.

## `t.Parallel` at both the test level and the subtest level

**What Google/Effective Go says:** Not a named single rule in Google's guide; standard library documentation for [`testing.T.Parallel`](https://pkg.go.dev/testing#T.Parallel) notes that parallel subtests only actually run concurrently with each other once the outer test function has also called `t.Parallel` and returned control to the test driver.

**How to detect it:** For a table-driven test whose subtests call `t.Parallel()`, check whether the outer `Test` function itself also calls `t.Parallel()` near the top (before setting up the table). Its absence doesn't break correctness, but it means the outer test still blocks other top-level parallel tests from starting until this one's subtests finish.

**Example — subtests parallel, but outer test is not, so this whole test still runs serially relative to its sibling top-level tests:**
```go
func TestValidate(t *testing.T) {
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			// ...
		})
	}
}
```

**Corrected — parallel at both levels:**
```go
func TestValidate(t *testing.T) {
	t.Parallel()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			// ...
		})
	}
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** Without the outer `t.Parallel()`, this test function still occupies a serial execution slot relative to other top-level tests, even though its own subtests eventually run concurrently with each other — missing half the available speedup on a large table-driven suite.

## `go test -race` is mandatory for concurrent code

**What Google/Effective Go says:** Not phrased as a named rule in Google's guide; documented as standard practice in the [Go race detector documentation](https://go.dev/doc/articles/race_detector) and implied throughout Google's [Best Practices: Concurrency](https://google.github.io/styleguide/go/best-practices#concurrency) guidance, which assumes race-free code is the baseline expectation.

**How to detect it:** Check the CI configuration (`Makefile`, GitHub Actions workflow, etc.) for whether `go test` invocations include `-race`. For any package containing goroutines, channels, or shared mutable state accessed from a test, confirm its test run includes the flag.

**Example violation — CI runs tests without the race detector:**
```yaml
- run: go test ./...
```

**Corrected:**
```yaml
- run: go test -race ./...
```

**Severity:** Violation for packages containing concurrent code

**Enforced by:** not enforced by `golangci-lint` (it's a `go test` runtime flag, not a static-analysis rule) — verify directly in CI configuration, not via `golangci-lint run`

**Why it matters:** Data races are undefined behavior in Go — a racy program can appear to work correctly for months and then corrupt data or crash unpredictably under load. `-race` catches a large fraction of these at test time, when they're cheap to fix, instead of in production.

## Use real transports for integration tests

**What Google/Effective Go says:** "Prefer real implementations to mocking whenever practical, especially at API boundaries." For HTTP/gRPC integration points, use a real listener rather than hand-rolling a fake of the transport protocol. ([Best Practices: Prefer real implementations](https://google.github.io/styleguide/go/best-practices#interfaces))

**How to detect it:** Look for hand-implemented `http.RoundTripper` or gRPC transport fakes. Check whether `httptest.Server` or the service's own test harness (`bufconn`, etc.) would work instead.

**Example — real transport, real client, fake backend logic:**
```go
mux := http.NewServeMux()
mux.Handle("/", svcconnect.NewServiceHandler(fakeBackend{}))
srv := httptest.NewServer(mux)
defer srv.Close()
client := svcconnect.NewServiceClient(srv.Client(), srv.URL)
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** The cost of a real transport in tests is a few milliseconds per test case; the benefit is catching real serialization, header, and routing bugs that a hand-rolled `RoundTripper` fake would never exercise because it never actually serializes anything.

## Setup failures: `t.Fatal` and name the operation that failed

**What Google/Effective Go says:** When a helper performs setup and the setup itself fails, it's appropriate to call `t.Fatalf` with a message that clearly identifies it as a setup failure, distinct from a system-under-test failure. ([Best Practices: Argument checking in helpers](https://google.github.io/styleguide/go/best-practices#assert-tests))

**How to detect it:** Read every `t.Fatalf` call inside a helper function. Confirm the message names the operation attempted (e.g., "setup: open test db") rather than a bare error dump.

**Example:**
```go
func mustOpenDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("postgres", testDSN())
	if err != nil {
		t.Fatalf("setup: open test db: %v", err)
	}
	return db
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** A message like "setup: open test db: connection refused" tells the reader immediately that the test environment is broken, not the code under test — saving a debugging detour into application logic that was never at fault.

## Use `t.Cleanup` over `defer` for cross-helper cleanup

**What Google/Effective Go says:** "`t.Cleanup`... registers a function to be called when the test... completes" — unlike `defer`, which is bound to the lexical scope of the function it's written in, `t.Cleanup` works across helper boundaries: a setup helper can register cleanup that runs after the *test* completes, even though the helper itself returns first. ([Best Practices: Cleaning up](https://google.github.io/styleguide/go/best-practices#cleanup)); `t.Cleanup` has been available since Go 1.14.

**How to detect it:** Look for setup helpers that use `defer` for cleanup of a resource returned to the caller — that doesn't work as intended, because the `defer` runs when the helper returns, before the test has a chance to use the resource.

**Example violation — `defer` inside the helper runs too early:**
```go
func mustOpenDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("postgres", testDSN())
	if err != nil {
		t.Fatalf("setup: open test db: %v", err)
	}
	defer db.Close() // runs immediately when mustOpenDB returns — db is closed before any test uses it
	return db
}
```

**Corrected:**
```go
func mustOpenDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("postgres", testDSN())
	if err != nil {
		t.Fatalf("setup: open test db: %v", err)
	}
	t.Cleanup(func() {
		if err := db.Close(); err != nil {
			t.Errorf("cleanup: close db: %v", err)
		}
	})
	return db
}
```

**Severity:** Violation

**Enforced by:** not enforced by `golangci-lint` — catch via the "does this helper `defer` a resource it also returns" heuristic

**Why it matters:** `defer` inside a helper that returns a resource to its caller runs at the wrong time — before the caller ever gets to use the resource. `t.Cleanup` correctly defers to the end of the *test*, regardless of which function registered it, and also runs cleanups in LIFO order across all callers, matching `defer`'s ordering guarantee at the right scope.

## `TestMain` for expensive shared setup

**What Google/Effective Go says:** "Use `TestMain`... when all the tests in a package need the same expensive setup and teardown," typically for functional/integration tests rather than unit tests. ([Best Practices: TestMain](https://google.github.io/styleguide/go/best-practices#testmain))

**How to detect it:** Look for repeated identical expensive setup (spinning up a test database container, starting a test server) inside every `Test` function or every `TestMain`-less package where one `TestMain` could do it once.

**Example violation — every test re-creates the same expensive fixture:**
```go
func TestFoo(t *testing.T) {
	db := mustStartPostgresContainer(t) // slow, repeated per test
	// ...
}

func TestBar(t *testing.T) {
	db := mustStartPostgresContainer(t) // slow, repeated per test
	// ...
}
```

**Corrected — `TestMain` with a separate `runMain` helper so defers still execute and `os.Exit` doesn't skip cleanup:**
```go
var testDB *sql.DB

func TestMain(m *testing.M) {
	code, err := runMain(m)
	if err != nil {
		log.Fatal(err)
	}
	os.Exit(code)
}

func runMain(m *testing.M) (code int, err error) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	container, err := startPostgresContainer(ctx)
	if err != nil {
		return 0, fmt.Errorf("start postgres container: %w", err)
	}
	defer container.Close()

	testDB = container.DB()
	return m.Run(), nil
}

func TestFoo(t *testing.T) {
	// uses the package-level testDB, started once for the whole package
}
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** Repeating expensive setup per test multiplies total test-suite time by the number of tests; `TestMain` amortizes it across the whole package. The `runMain` indirection matters because `TestMain` itself calls `os.Exit`, which — like everywhere else in this guide — skips deferred cleanup if it's called directly inside a function that also holds open resources.

## Test-file linter relaxations

**What Google/Effective Go says:** Not from Google's guide; this section documents this repo's specific `.golangci.yml` configuration, which intentionally disables several linters inside `_test.go` files. See [golangci-lint.md](golangci-lint.md#test-file-relaxations) for the authoritative list.

**How to detect it:** Before flagging any of the following patterns in a `_test.go` file, check whether the underlying linter is one of the six relaxed for tests in this repo: `bodyclose`, `errcheck`, `errorlint`, `gosec`, `revive`, `unparam`.

Concretely, in `_test.go` files in this repo:

- **`bodyclose` is off** — an `http.Response.Body` opened in a test via `httptest.NewServer` and not explicitly closed will not fail lint, though closing it is still good practice.
- **`errcheck` is off** — test bodies MAY ignore return errors from setup helpers where a `t.Fatal` would trigger anyway on the next line, or where the error is genuinely inconsequential to the test's purpose.
- **`errorlint` is off** — tests MAY compare errors with `==` or type-assert directly instead of `errors.Is`/`errors.As`, though the production-code guidance in [error-handling.md](error-handling.md) is still worth following where it costs nothing.
- **`gosec` is off** — test bodies MAY use `math/rand` without a `crypto/rand` justification, and MAY read/write fixture files without the path-sanitization suggestions in [tooling-and-modernization.md](tooling-and-modernization.md).
- **`revive` is off** — tests MAY use dot-imports for DSL-style testing packages (e.g. `. "github.com/onsi/gomega"`), which [imports.md](imports.md#no-dot-imports-outside-tests) explicitly permits only in this location, and MAY otherwise deviate from `revive`'s naming/style rules.
- **`unparam` is off** — test helper functions MAY have parameters that are always passed the same value across all call sites (common with table-driven helper signatures that stay uniform for future extensibility).

**Severity:** Not applicable — this section defines what NOT to flag, rather than a rule to enforce

**Enforced by:** the `rules:` exclusion block in `.golangci.yml` matching `path: _test\.go` against the six linters listed above

**Why it matters:** Outside `_test.go`, all six of these linters are enforced because production code failure modes (unclosed response bodies, swallowed errors, weak randomness, unsafe imports) have real runtime and security consequences. Inside tests, the same patterns are frequently intentional simplifications — a test double doesn't need `crypto/rand`, and a `t.Fatal` two lines later makes an unchecked error in a setup helper harmless. Applying the same strict rules to test code produces false-positive noise without a corresponding safety benefit.

## How to audit Go test code against these rules

1. Grep for functions named `assert*` or `expect*` that take `*testing.T`. Each is a candidate assertion-helper antipattern. Inspect: if it asserts equality on a complex type, suggest `cmp.Diff` inline in the Test.
2. Grep `t.Helper()` inside functions whose body calls `t.Error` or `t.Errorf` (not just `t.Fatal`). These are likely assertion helpers, not setup helpers.
3. Grep `t.Fatal` and `t.Fatalf` inside `for _, tc := range tests {` loops at the top level (not inside `t.Run`). Each is a candidate violation; either switch to `t.Error` or wrap in `t.Run`.
4. Grep `go func() {` inside `_test.go` files. For each match, read the closure body. Any `t.Fatal*` or `t.Skip*` call inside is a violation.
5. Look at table-driven test definitions. Are field names used in struct literals? Flag positional inits.
6. Grep `for _, tc := range tests {` loops without a nested `t.Run(...)` — suggest converting to subtests.
7. Check `go.mod` for the declared Go version. For loop-scoped `tt := tt` capture lines before `t.Parallel()`: flag as a real bug if missing on Go ≤1.21; don't flag either way on Go 1.22+ (and note `copyloopvar` will instead flag the capture line as unnecessary on 1.22+ modules).
8. For subtests that call `t.Parallel()`, check whether the enclosing `Test` function also calls `t.Parallel()` near the top.
9. Check CI configuration for `go test -race` on any package containing goroutines or shared mutable state.
10. Look at integration-y tests that mock HTTP or gRPC by hand-implementing a `RoundTripper` or similar. Suggest `httptest.Server` or the service's own test harness.
11. Look for setup helpers that use `defer` for cleanup of a resource returned to the caller — that doesn't work (the defer runs when the helper returns, before the test uses the resource). Suggest `t.Cleanup`.
12. Look for repeated expensive setup duplicated across every `Test` function in a package — suggest `TestMain` with a `runMain(m) (code int, err error)` helper.
13. Before flagging `bodyclose`/`errcheck`/`errorlint`/`gosec`/`revive`/`unparam`-style issues inside a `_test.go` file, confirm whether this repo's config already relaxes that linter for tests (see the Test-file linter relaxations section above) — if so, downgrade or omit the finding.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
