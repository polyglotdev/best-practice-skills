<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 3. Package Organization

A Go package is the unit of compilation, encapsulation, and API surface —
getting its boundaries wrong causes pain that no amount of good naming
inside the package can fix. This chapter draws from [Google Best
Practices: Packages, package names, and file
names](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)
and Uber's [Package
Names](https://github.com/uber-go/guide/blob/master/style.md#package-names)
guidance. Naming rules for identifiers inside a package are covered in
[Chapter 2](02-names.md); import grouping is covered in [Chapter
4](04-imports.md).

## 3.1 Give every package a single, clear purpose.

> Why? A package is the unit callers reason about and depend on. A
> package that does three unrelated things forces every caller to pull
> in dependencies and API surface they don't need, and makes the
> package's own tests harder to reason about
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — one package mixing HTTP handling, DB access, and email sending
package server

func HandleSignup(w http.ResponseWriter, r *http.Request) {}
func SaveUser(db *sql.DB, u User) error                     { return nil }
func SendWelcomeEmail(addr string) error                    { return nil }

// good — split by responsibility
package httpapi // handlers only

func HandleSignup(w http.ResponseWriter, r *http.Request) {}

package userstore // persistence only

func Save(db *sql.DB, u User) error { return nil }

package mailer // notifications only

func SendWelcome(addr string) error { return nil }
```

## 3.2 Never name a package `util`, `common`, `misc`, or `helpers`.

> Why? These names describe nothing about what the package contains,
> so they become dumping grounds that grow without bound and accumulate
> unrelated code. A concrete name forces you to say what the package
> actually does
> ([Uber Style: Package Names](https://github.com/uber-go/guide/blob/master/style.md#package-names)).

```go
// bad
package util

func FormatDate(t time.Time) string   { return "" }
func RetryWithBackoff(f func() error) error { return nil }
func HashPassword(pw string) string   { return "" }

// good — split into packages named for what they provide
package dateutil

func Format(t time.Time) string { return "" }

package retry

func WithBackoff(f func() error) error { return nil }

package passwordhash

func Hash(pw string) string { return "" }
```

## 3.3 (Suggestion) Avoid stutter between the package name and its exported identifiers.

> Why? Callers write `pkg.Identifier`; if the identifier repeats the
> package name, every call site reads redundantly. The standard library
> models this well: `bytes.Buffer`, not `bytes.BytesBuffer`
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).
> Treat this as a code-review Suggestion rather than a hard Violation —
> teams that run `revive`'s `exported` rule with `disableStutteringCheck`
> intentionally don't gate merges on it, since it's judgment-dependent
> (e.g. `config.Config` is idiomatic despite the repetition).

```go
// bad
package bytes

type BytesBuffer struct{}

func NewBytesBuffer() *BytesBuffer { return &BytesBuffer{} }

// good
package bytes

type Buffer struct{}

func NewBuffer() *Buffer { return &Buffer{} }
```

> Enforced by: `revive`'s `exported` rule can flag stutter, but with
> `disableStutteringCheck` set (a common configuration), it does not.
> Raise stutter in code review instead of relying on CI to catch it.

## 3.4 Use `internal/` to hide implementation packages from external importers.

> Why? Anything under a directory named `internal/` is only importable
> by code rooted at the parent of that `internal/` directory — the Go
> tool enforces this. It lets you share code across your own packages
> without committing to a stable public API for it
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — implementation detail exported at the module root, becomes public API by accident
// module github.com/acme/widget
package sqlhelpers // github.com/acme/widget/sqlhelpers — importable by anyone

func BuildDSN(cfg Config) string { return "" }

// good — same code, but unreachable from outside the module
// module github.com/acme/widget
package sqlhelpers // github.com/acme/widget/internal/sqlhelpers

func BuildDSN(cfg Config) string { return "" }
```

## 3.5 Keep `package main` thin — orchestration only, logic lives in importable packages.

> Why? `main` can't be imported or unit-tested by other packages, so
> logic left there is untestable except via slow end-to-end tests.
> Moving logic into an importable package makes it directly unit
> testable and reusable ([Best Practices:
> Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — all logic embedded directly in main
package main

func main() {
	cfg := loadConfigFromEnv()
	db := mustConnect(cfg.DSN)
	http.ListenAndServe(cfg.Addr, buildRouter(db))
}

// good — main only wires dependencies together
package main

import "github.com/acme/widget/internal/server"

func main() {
	cfg := server.LoadConfig()
	srv := server.New(cfg)
	srv.Run()
}
```

## 3.6 Split large packages by concept into multiple files instead of one monolithic file.

> Why? A single file holding every type and function in a package
> forces readers and `git blame` to wade through unrelated code to find
> what they need. File-per-concept (e.g. `client.go`, `options.go`,
> `errors.go`) gives navigable, independently reviewable units
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — one 2,000-line file: client.go contains client, options, retry logic, and errors

// good — split by concept
// client.go     — Client type and its core methods
// options.go    — functional options (WithTimeout, WithRetries)
// errors.go     — sentinel errors and error types
// client_test.go — tests for client.go
```

## 3.7 Keep small, cohesive packages together in one file when splitting adds no value.

> Why? File-per-concept is a tool for managing size, not a mandate.
> A package with one type and three tiny methods gains nothing from
> being split across five files — it just adds navigation overhead
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — three files for ~15 total lines of code
// stack.go: type Stack struct{...}
// stack_push.go: func (s *Stack) Push(...)
// stack_pop.go: func (s *Stack) Pop() ...

// good — one file is proportionate to the package's size
// stack.go
package stack

type Stack struct{ items []int }

func (s *Stack) Push(v int) { s.items = append(s.items, v) }
func (s *Stack) Pop() (int, bool) {
	if len(s.items) == 0 {
		return 0, false
	}
	v := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return v, true
}
```

## 3.8 Store fixture files under `testdata/`, never alongside production source.

> Why? The Go tool ignores any directory named `testdata` during
> builds, so fixtures placed there can't accidentally get compiled,
> vetted as production code, or imported
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — fixture JSON lives next to source, gets treated like a build input
// widget/sample_response.json
// widget/client.go

// good — fixtures under testdata/, ignored by the go tool
// widget/testdata/sample_response.json
// widget/client.go
// widget/client_test.go

func TestParseResponse(t *testing.T) {
	data, err := os.ReadFile("testdata/sample_response.json")
	if err != nil {
		t.Fatal(err)
	}
	_ = data
}
```

## 3.9 Don't create a package for a single exported function unless it stands alone conceptually.

> Why? Over-splitting produces a maze of tiny packages that all have to
> be imported and remembered separately, with no benefit over grouping
> related functionality under one cohesive package
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — a whole package for one helper
package isevenutil

func IsEven(n int) bool { return n%2 == 0 }

// good — belongs with related numeric helpers in one package
package mathutil

func IsEven(n int) bool { return n%2 == 0 }
func IsOdd(n int) bool  { return n%2 != 0 }
```

## 3.10 Depend on interfaces defined by the consumer package, not exported by the producer, when decoupling matters.

> Why? A package that only needs to call a couple of methods on a
> dependency shouldn't force every implementation to satisfy a large
> interface defined far away. Consumer-defined interfaces keep coupling
> minimal and make substituting test doubles trivial
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — consumer imports the concrete producer type just to call one method
package report

import "github.com/acme/widget/store"

func Generate(s *store.PostgresStore) ([]byte, error) {
	rows, err := s.FetchAll()
	if err != nil {
		return nil, err
	}
	return render(rows), nil
}

// good — consumer declares only the interface it needs
package report

type RowFetcher interface {
	FetchAll() ([]Row, error)
}

func Generate(f RowFetcher) ([]byte, error) {
	rows, err := f.FetchAll()
	if err != nil {
		return nil, err
	}
	return render(rows), nil
}
```

## 3.11 Avoid import cycles by keeping shared types in a lower-level package both sides can depend on.

> Why? Go's compiler rejects import cycles outright, but the design
> smell shows up before the compiler error: two packages both want to
> reference each other's types. Extracting the shared type into a
> package both can import — without importing each other — breaks the
> cycle ([Best Practices:
> Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — order imports customer, customer imports order: cycle
package order

import "github.com/acme/widget/customer"

type Order struct{ Buyer customer.Customer }

package customer

import "github.com/acme/widget/order"

type Customer struct{ History []order.Order }

// good — shared type lives in a package neither depends on for the other
package model

type Order struct{ BuyerID string }
type Customer struct{ ID string }

package order

import "github.com/acme/widget/model"

func Place(c model.Customer) model.Order { return model.Order{BuyerID: c.ID} }
```

## 3.12 Name the package directory to match the package's declared name.

> Why? Tooling, `go doc`, and human navigation all assume the import
> path's last segment matches the `package` clause. A mismatch (e.g.
> directory `httpclient/` declaring `package client`) means every
> importer's alias silently disagrees with the directory name, which
> confuses readers browsing the repository
> ([Best Practices: Packages](https://google.github.io/styleguide/go/best-practices#packages-package-names-and-file-names)).

```go
// bad — directory is "httpclient/", but the package declares a different name
// httpclient/client.go
package client

// good — directory name and package name match
// httpclient/client.go
package httpclient
```
