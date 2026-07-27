<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 28. Test Doubles

"Test double" is the umbrella term for anything that stands in for a real
dependency in a test — fakes, stubs, spies, and mocks are different tools
with different tradeoffs, and conflating them leads to brittle tests. This
chapter draws from [Google Best Practices: Test
helpers](https://google.github.io/styleguide/go/best-practices#test-helpers)
and the naming conventions implicit in [Google Style
Decisions](https://google.github.io/styleguide/go/decisions), applied to
the fake/stub/mock distinction. It complements [Chapter
27](27-testing.md), which covers test structure and mechanics; this
chapter is specifically about what stands in for a real dependency and how
to name it.

## 28.1 Reserve the name "Fake" for a lightweight but behaviorally real implementation, not for any test double in general.

> Why? A fake actually implements the behavior of the thing it replaces —
> an in-memory key-value store that really stores and retrieves values —
> just without the production backend. Calling every test double a
> "mock" regardless of what it actually does makes it impossible to tell,
> from the name alone, whether a test is exercising real logic or just
> checking that a method was called.

```go
// bad — called "Mock" but it's actually a behavioral fake
type MockUserStore struct {
	users map[string]User
}

func (m *MockUserStore) Save(u User) error {
	m.users[u.ID] = u
	return nil
}

func (m *MockUserStore) Get(id string) (User, bool) {
	u, ok := m.users[id]
	return u, ok
}

// good — named for what it actually is: a real, in-memory implementation
type FakeUserStore struct {
	users map[string]User
}

func (f *FakeUserStore) Save(u User) error {
	f.users[u.ID] = u
	return nil
}

func (f *FakeUserStore) Get(id string) (User, bool) {
	u, ok := f.users[id]
	return u, ok
}
```

## 28.2 Reserve the name "Stub" for a double that returns canned answers with no real logic behind them.

> Why? A stub's entire job is to return a fixed, pre-arranged value
> regardless of input. Naming it accurately signals to the reader that
> the double has no behavior worth testing on its own — it's a fixed
> input to the system under test, not something exercising real logic
> like a fake would.

```go
// bad — called a "Fake" but has no real behavior, just canned returns
type FakePriceLookup struct{}

func (FakePriceLookup) Price(sku string) (float64, error) {
	return 9.99, nil // always returns the same value, no matter the sku
}

// good — named Stub because it returns a fixed answer with no real logic
type StubPriceLookup struct{}

func (StubPriceLookup) Price(sku string) (float64, error) {
	return 9.99, nil
}
```

## 28.3 Reserve the name "Spy" for a double that records calls made to it so the test can assert on them afterward.

> Why? A spy's distinguishing feature is that it observes and records
> interactions — arguments, call counts, order — for later assertions,
> as opposed to a stub (fixed output) or a mock (assertions built into
> the double itself). Naming it precisely tells the reader what kind of
> assertion the test is about to make.

```go
// bad — called "Mock" but only records calls; assertions happen outside it
type MockNotifier struct {
	sent []string
}

func (m *MockNotifier) Notify(msg string) {
	m.sent = append(m.sent, msg)
}

// good — named Spy: it records interactions for the test to inspect
type SpyNotifier struct {
	sent []string
}

func (s *SpyNotifier) Notify(msg string) {
	s.sent = append(s.sent, msg)
}

func TestOrder_NotifiesOnShip(t *testing.T) {
	spy := &SpyNotifier{}
	svc := NewOrderService(spy)

	svc.Ship(Order{ID: "123"})

	if len(spy.sent) != 1 {
		t.Errorf("len(sent) = %d, want 1", len(spy.sent))
	}
}
```

## 28.4 Reserve the name "Mock" for a double with built-in expectation verification (calls that fail the test if an expected interaction never happens).

> Why? A true mock encodes expectations up front — "this method must be
> called exactly twice with these arguments" — and fails the test itself
> if that contract is violated. Calling a plain recording spy a "mock"
> overstates what it does and obscures whether the test's real assertion
> logic lives inside the double or in the test body.

```go
// bad — this is a spy (records calls); calling the type "Mock" overstates it
type MockEmailer struct {
	sentTo []string
}

func (m *MockEmailer) Send(to string) {
	m.sentTo = append(m.sentTo, to)
}

// good — a real mock enforces the expectation itself
type MockEmailer struct {
	t        *testing.T
	wantTo   string
	callCount int
}

func (m *MockEmailer) Send(to string) {
	m.callCount++
	if to != m.wantTo {
		m.t.Errorf("Send(%q), want Send(%q)", to, m.wantTo)
	}
}

func (m *MockEmailer) Verify() {
	if m.callCount != 1 {
		m.t.Errorf("Send called %d times, want 1", m.callCount)
	}
}
```

## 28.5 Prefer a hand-written fake over a mocking framework for interfaces you own.

> Why? [Google Best Practices: Test
> helpers](https://google.github.io/styleguide/go/best-practices#test-helpers)
> favors simple, purpose-built test support code over generalized
> frameworks. A hand-written fake is plain Go, debuggable with the same
> tools as production code, and doesn't require the reader to learn a
> separate mocking DSL to understand what a test is actually checking.

```go
// bad — a generated mock's expectation setup obscures the actual test intent
func TestCharge(t *testing.T) {
	ctrl := gomock.NewController(t)
	m := mocks.NewMockGateway(ctrl)
	m.EXPECT().Charge(gomock.Any(), gomock.Eq(1000)).Return(nil).Times(1)

	svc := NewBillingService(m)
	if err := svc.Charge(context.Background(), 1000); err != nil {
		t.Fatalf("Charge() error = %v", err)
	}
}

// good — a small hand-written fake reads like ordinary Go
type FakeGateway struct {
	charged []int
}

func (f *FakeGateway) Charge(_ context.Context, amount int) error {
	f.charged = append(f.charged, amount)
	return nil
}

func TestCharge(t *testing.T) {
	fake := &FakeGateway{}
	svc := NewBillingService(fake)

	if err := svc.Charge(context.Background(), 1000); err != nil {
		t.Fatalf("Charge() error = %v", err)
	}
	if len(fake.charged) != 1 || fake.charged[0] != 1000 {
		t.Errorf("charged = %v, want [1000]", fake.charged)
	}
}
```

## 28.6 Prefer a real dependency over any test double when a lightweight real version is available.

> Why? A test that exercises the real implementation catches integration
> bugs a fake cannot — wrong SQL, wrong HTTP status handling, wrong JSON
> shape. `httptest.Server` and in-memory or containerized databases give
> most of a fake's speed and determinism while testing real code paths.

```go
// bad — a hand-rolled fake HTTP client bypasses real HTTP semantics
type FakeHTTPClient struct {
	response *http.Response
}

func (f *FakeHTTPClient) Do(*http.Request) (*http.Response, error) {
	return f.response, nil
}

// good — httptest.Server exercises the real net/http client and server code
func TestClient_Get(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	}))
	defer srv.Close()

	client := NewClient(srv.URL)
	if _, err := client.Get(context.Background(), "/health"); err != nil {
		t.Fatalf("Get() error = %v", err)
	}
}
```

## 28.7 Use `TestMain` to start expensive, shared real dependencies (a containerized database, a test broker) once per package, not once per test.

> Why? [Google Best Practices:
> TestMain](https://google.github.io/styleguide/go/best-practices#testmain)
> exists precisely for this case: bringing up a real Postgres container
> for every individual test would make the suite too slow to run
> routinely, while sharing one instance across the package keeps tests
> fast without falling back to a fake.

```go
// bad — every test starts and tears down its own database container
func TestUserStore_Save(t *testing.T) {
	db := startPostgresContainer(t) // slow, repeated per test
	defer db.Close()
	store := NewUserStore(db)
	// ...
}

// good — TestMain starts the container once for the whole package
var testDB *sql.DB

func TestMain(m *testing.M) {
	db, cleanup := startPostgresContainer()
	testDB = db
	code := m.Run()
	cleanup()
	os.Exit(code)
}

func TestUserStore_Save(t *testing.T) {
	store := NewUserStore(testDB)
	// ...
}
```

## 28.8 Name test double types with the pattern `<Kind><InterfaceName>` (`FakeUserStore`, `StubPriceLookup`, `SpyNotifier`, `MockGateway`), not generic names like `TestUserStore` or `UserStoreImpl`.

> Why? A name that states both the kind of double and the interface it
> implements tells the reader everything they need before looking at the
> implementation: what role it plays in the test and which real type it
> stands in for.

```go
// bad — generic names give no signal about the double's behavior
type TestStore struct{ data map[string]User }
type UserStoreImpl2 struct{ data map[string]User }

// good — the name states both the kind of double and the interface
type FakeUserStore struct{ data map[string]User }
```

## 28.9 In `_test.go` files, dot-imports for a DSL-style assertion library are permitted even though `revive`'s `dot-imports` rule is enforced elsewhere.

> Why? The user's `.golangci.yml` (see [Chapter
> 33.5](33-linter-configuration.md)) disables `revive` — which includes
> the `dot-imports` rule — inside `_test.go` files specifically because
> assertion DSLs like Gomega are designed to read as unqualified English
> (`Expect(err).To(BeNil())`) and lose that readability if every
> identifier must be package-qualified. This exemption is scoped to test
> files; a dot-import in a non-test file is still a violation (see
> [Chapter 4](04-imports.md)).

> Enforced by: (relaxation of) revive `dot-imports` for `_test.go` (see [Chapter 33.5](33-linter-configuration.md))

```go
// bad — in a non-test file, a dot-import is a real violation:
// revive's dot-imports rule is fully enforced outside _test.go
package svc

import (
	. "github.com/some/helperpkg"
)

func Charge(amount int) error {
	return Validate(amount) // unclear which package Validate comes from
}

// good — acceptable only in _test.go, where the DSL's readability
// depends on unqualified names
package svc_test

import (
	"testing"

	. "github.com/onsi/gomega"
)

func TestCharge(t *testing.T) {
	g := NewWithT(t)

	err := Charge(1000)

	g.Expect(err).To(BeNil())
}
```

## 28.10 Fakes and stubs used only within one package's tests do not need exported names or their own doc comments.

> Why? A test double that never crosses a package boundary is an
> implementation detail of that package's test suite. [Google Best
> Practices: Test
> helpers](https://google.github.io/styleguide/go/best-practices#test-helpers)
> treats unexported test support types the same as any other unexported
> helper: useful internally, not part of any public contract that needs
> documentation for external readers.

```go
// bad — exported and documented as if other packages might import it
// FakeClock is a fake implementation of a clock for use in tests.
type FakeClock struct {
	now time.Time
}

// good — unexported; it's purely an internal test fixture
type fakeClock struct {
	now time.Time
}

func (f *fakeClock) Now() time.Time { return f.now }
```
