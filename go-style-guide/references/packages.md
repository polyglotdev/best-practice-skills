# Package Organization — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). This repo's enabled linters are documented in [golangci-lint.md](golangci-lint.md); severities below are aligned to `/home/user/workspace/go-skills-build/.golangci.yml`.

Packages are the unit of distribution and the unit of API. The style guide's package-organization rules are less about line counts and more about coupling — if two parts of the code can't be used independently, they probably want to live together. If a package's purpose can't be summarised in one short sentence, it's probably doing too much ([Best Practices: Choosing a package name / package size](https://google.github.io/styleguide/go/best-practices#package-size)).

## Package size is about coupling, not line count

**What Google/Effective Go says:** "Go style is flexible about file size... As a rule of thumb, files should be focused enough that a maintainer can tell which file contains something, and the files should be small enough that it will be easy to find once there." ([Best Practices: File organization](https://google.github.io/styleguide/go/best-practices#package-size))

**How to detect it:** Read the import statements of the package's own callers. Do they always pair this import with another from the same module? Read the `_test.go` files — do tests of this package routinely set up types from a sibling package? That's coupling. Read the public API — is the godoc page a coherent story, or does it read as two unrelated APIs concatenated?

**Example violation:**
```go
// package accountutil — half the file is about billing, half is about auth
package accountutil

func ComputeInvoiceTotal(acct *Account) money.Money { /* ... */ }
func VerifyPassword(acct *Account, pw string) bool  { /* ... */ }
```

**Corrected:**
```go
// package billing
package billing

func InvoiceTotal(acct *Account) money.Money { /* ... */ }

// package auth
package auth

func VerifyPassword(acct *Account, pw string) bool { /* ... */ }
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — no linter measures package cohesion; this is a design-review checklist item

**Why it matters:** A package should have one clear purpose statable in a sentence. When callers must import two packages to do anything meaningful with either, splitting or merging usually improves the API.

## No "one type per file" rule

**What Google/Effective Go says:** "There is no 'one type, one file' convention as in some other languages." ([Best Practices: File organization](https://google.github.io/styleguide/go/best-practices#package-size))

**How to detect it:** Count `.go` files (excluding tests and generated code) per package. Read the names; if they're all `partner_*.go` with 5-15 lines each, or if there's a single 4000-line file, that's a smell in either direction.

**Reasonable layout for a `partner` package:**
```
partner/
├── partner.go              // the Partner type, core methods
├── repository.go           // storage interface + pgx implementation
├── repository_test.go
├── status.go               // the Status enum and state transitions
└── doc.go                  // optional package overview if non-trivial
```

**Bad smell layout (too fragmented):**
```
partner/
├── partner_id.go           // 8 lines
├── partner_name.go         // 4 lines
├── partner_status.go       // 12 lines
├── partner_sla.go          // 10 lines
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`

**Why it matters:** Go has no convention that each exported type goes in its own file. Group files by topic and reader convenience — the aim is that someone opening the package can navigate it quickly. Too many tiny files is as bad as one mega-file.

## Use `doc.go` for lengthy package-level documentation

**What Google/Effective Go says:** "If there is no obvious primary file or if the package comment is extraordinarily long, it is acceptable to put the doc comment in a file named `doc.go` with only the comment and the package clause." ([Style Decisions: Package comments](https://google.github.io/styleguide/go/decisions#package-comments))

**How to detect it:** Check whether the module has any `doc.go` files. Not required, but their absence in a complex package with substantial public API is worth a suggestion.

**Example violation:**
```go
// partner.go — package comment crammed above an unrelated first type
// Package partner provides repositories and domain models for managed
// partner records... (40 lines of prose)
package partner

type Partner struct{ /* ... */ }
```

**Corrected:**
```go
// doc.go
// Package partner provides repositories and domain models for managed
// partner records in the Crossing platform.
//
// The Partner type ...
package partner
```

**Severity:** Suggestion

**Enforced by:** `staticcheck` ST1000 ("package doc comment required") is **exempted** in this repo's `.golangci.yml` — see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation). Treat package doc comments as recommended, not a lint-blocking requirement.

**Why it matters:** A long package overview belongs in `doc.go` as a file-level comment, not crammed onto the first non-doc file, so the file that defines the primary type isn't dominated by prose.

## Proto-generated package import naming

**What Google/Effective Go says:** "Prefer whole-word aliases over short abbreviations... `pushqueueservicepb` over `pqsvc` or `xpb`." The `pb` suffix marks generated proto packages; `grpc` suffix marks generated gRPC packages. ([Best Practices: Proto](https://google.github.io/styleguide/go/best-practices#import-protos); [Style Decisions: Import renaming](https://google.github.io/styleguide/go/decisions#import-renaming))

**How to detect it:** For each `_pb.go` and `_grpc.go` import in the codebase, check the alias used. Flag any short alias like `xpb` or two-letter aliases in new code.

**Example violation:**
```go
import xpb "example.com/proto/push_queue_service_go_proto"
```

**Corrected:**
```go
import pushqueueservicepb "example.com/proto/push_queue_service_go_proto"
```

For gRPC packages, the convention is the `grpc` suffix:
```go
import pushqueueservicegrpc "example.com/proto/push_queue_service_go_grpc"
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` in this repo (no rule inspects proto import aliases); enforced by convention and code review

**Why it matters:** The `pb`/`grpc` suffix signals "this is a generated package" at every call site, e.g. `pushqueueservicepb.Request{}` immediately reads as a generated type.

## Import grouping — three blocks: stdlib / third-party / module-local

**What Google/Effective Go says:** Google's canonical grouping is stdlib, then other, then optional proto/blank-import groups ([Style Decisions: Import grouping](https://google.github.io/styleguide/go/decisions#import-grouping)). This repo's `goimports` is configured with `local-prefixes: platform-backend`, which produces **three** blocks: standard library, third-party, and module-local (`platform-backend/...`) — see [imports.md](imports.md) for the full ruleset.

**How to detect it:** Run `goimports -local platform-backend -d <file>` and diff against the current import block. Any diff is drift, not a style judgment call.

**Example violation:**
```go
import (
	"fmt"
	"platform-backend/internal/partner"
	"os"

	"github.com/google/uuid"
)
```

**Corrected:**
```go
import (
	"fmt"
	"os"

	"github.com/google/uuid"

	"platform-backend/internal/partner"
)
```

**Severity:** Suggestion

**Enforced by:** `goimports` formatter with `local-prefixes: platform-backend` (see [golangci-lint.md](golangci-lint.md#format-chain)) — this is auto-fixed by the formatter chain, so don't hand-flag it beyond "run `goimports -local platform-backend -w`."

**Why it matters:** Consistent grouping makes it easy to see at a glance which imports are standard library, which are external dependencies, and which are same-module code — and since it's auto-fixable, there's no reason for a human reviewer to spend time on it manually.

## No `util`/`common`/`misc` packages

**What Google/Effective Go says:** "Avoid uninformative package names like `util`, `utility`, `common`, `helper`, `model`, `testhelper`... that would tempt users of the package to rename it when importing." ([Style Decisions: Package names](https://google.github.io/styleguide/go/decisions#package-names))

**How to detect it:** List every directory name and `package` declaration in the module. Flag `util`, `utils`, `helper`, `helpers`, `common`, `misc`, `shared`, `base`, `lib`.

**Example violation:**
```go
// package util — grab-bag of unrelated helpers
package util

func RetryWithBackoff(fn func() error) error { /* ... */ }
func FormatCurrency(cents int64) string      { /* ... */ }
```

**Corrected:**
```go
// package retry
package retry

func WithBackoff(fn func() error) error { /* ... */ }

// package money
package money

func FormatCurrency(cents int64) string { /* ... */ }
```

**Severity:** Violation

**Enforced by:** not enforced by a specific `golangci-lint` rule (no linter inspects package-name semantics) — this is the same rule documented in [naming.md](naming.md#package-names-avoid-utilcommonhelpermisc-and-avoid-stuttering); enforce via code review

**Why it matters:** Uninformative package names give callers no signal about what's inside, and grab-bag packages tend to accumulate unrelated code indefinitely because nothing about the name discourages new unrelated additions.

## `internal/` boundary discipline

**What Google/Effective Go says:** The `internal/` directory convention is part of the Go toolchain itself (any import path containing an `internal/` segment is only importable by code rooted at the parent of that `internal` directory) — see the [Go command documentation on internal packages](https://go.dev/cmd/go/#hdr-Internal_Directories), referenced from Google's [package-size guidance](https://google.github.io/styleguide/go/best-practices#package-size) on scoping visibility.

**How to detect it:** For every package under `internal/`, check whether anything outside the module (or outside the directory rooted at `internal/`'s parent) imports it — this will already fail to build, so the real audit is the inverse: check whether code that *should* be internal (unstable APIs, implementation details, generated helpers not meant for external consumption) is sitting *outside* `internal/` where any importer can reach it.

**Example violation:**
```
platform-backend/
├── pkg/
│   └── billingcore/        // implementation detail, but publicly importable
└── cmd/
    └── billingsvc/
```

**Corrected:**
```
platform-backend/
├── internal/
│   └── billingcore/        // only importable from within platform-backend
└── cmd/
    └── billingsvc/
```

**Severity:** Suggestion

**Enforced by:** the Go compiler itself enforces the *mechanical* import restriction (a build failure, not a lint warning) once code is under `internal/`; `golangci-lint` has no rule that tells you what should move *into* `internal/` — that's a design judgment call

**Why it matters:** Every package outside `internal/` is part of your public API surface the moment anything imports it — internally or externally. Placing implementation-detail packages under `internal/` lets you refactor them freely without a compatibility promise.

## `testdata/` convention for test fixtures

**What Google/Effective Go says:** The `go` tool itself ignores any directory named `testdata` for build purposes, which is why it's the standard place for fixture files, golden files, and sample inputs — documented in [`go help packages`](https://pkg.go.dev/cmd/go#hdr-Package_lists_and_patterns) and used throughout the standard library (e.g. [`encoding/json/testdata`](https://cs.opensource.google/go/go/+/refs/tags/go1.22.0:src/encoding/json/testdata/)).

**How to detect it:** Look for fixture files (`.json`, `.golden`, `.txt` sample inputs) sitting directly in a package directory rather than under a `testdata/` subdirectory.

**Example violation:**
```
partner/
├── partner.go
├── partner_test.go
├── sample_response.json     // fixture file mixed with source
```

**Corrected:**
```
partner/
├── partner.go
├── partner_test.go
├── testdata/
│   └── sample_response.json
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint`; the Go toolchain itself skips `testdata/` during builds, which is the practical reason to use it

**Why it matters:** Keeping fixtures in `testdata/` prevents the `go` tool from trying to compile them as part of the package and gives every reader an immediately recognizable location for sample inputs.

## One purpose per package — the "must import both" test

**What Google/Effective Go says:** "A good test for this coupling is to imagine a hypothetical user of two packages, where the packages cover closely related topics: if the user must import both packages in order to use either in any meaningful way, combining them together is usually the right thing to do." ([Best Practices: Choosing a package name](https://google.github.io/styleguide/go/best-practices#package-size))

**How to detect it:** For every pair of sibling packages, ask: does a typical caller import both to accomplish one task? If yes, and the pairing is not coincidental, that's a signal to merge. Conversely, if a package's godoc page reads as "two unrelated APIs concatenated," that's a signal to split.

**Example violation:**
```go
// package orderitems — nothing useful without package orders
package orderitems

type Item struct {
	OrderID string
	SKU     string
}
```

**Corrected:**
```go
// package orders — Item lives alongside Order because callers
// always need both.
package orders

type Order struct{ /* ... */ }
type Item struct{ /* ... */ }
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — a design judgment call, not a mechanical check

**Why it matters:** Splitting tightly coupled types into separate packages doesn't reduce coupling; it just adds an import statement and hides the coupling from the compiler's package-level encapsulation. Keep coupled implementation details in one package so unexported fields and helpers stay usable between them.

## `main` packages — keep them thin

**What Google/Effective Go says:** Comments for `main` packages follow a special convention: "The seed_generator command is a utility that generates a Finch seed file from a set of JSON study configs." — the doc comment names the *binary*, not the package. ([Style Decisions: Package comments](https://google.github.io/styleguide/go/decisions#package-comments)) Uber's [Exit in Main](https://github.com/uber-go/guide/blob/master/style.md#exit-in-main) rule reinforces this: business logic belongs in a testable `run()` function, not directly in `main()`.

**How to detect it:** Read every `func main()`. Flag bodies that contain business logic, error-handling branches deeper than flag parsing/wiring, or more than one `os.Exit`/`log.Fatal` call site.

**Example violation:**
```go
func main() {
	args := os.Args[1:]
	if len(args) != 1 {
		log.Fatal("missing file")
	}
	f, err := os.Open(args[0])
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close() // never runs if a later log.Fatal fires
	b, err := io.ReadAll(f)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(string(b))
}
```

**Corrected:**
```go
func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func run() error {
	args := os.Args[1:]
	if len(args) != 1 {
		return errors.New("missing file")
	}
	f, err := os.Open(args[0])
	if err != nil {
		return err
	}
	defer f.Close()
	b, err := io.ReadAll(f)
	if err != nil {
		return err
	}
	fmt.Println(string(b))
	return nil
}
```

**Severity:** Suggestion

**Enforced by:** not directly enforced by `golangci-lint`, though `bodyclose` and `errcheck` will still fire inside `main()` like anywhere else in non-test code

**Why it matters:** A `main()` with only wiring and a single exit point is trivially testable (`run()` can be unit tested without exiting the test binary) and never skips deferred cleanup because of an early `log.Fatal` deeper in the call chain.

## `init()` is avoided everywhere except `cmd/` flag registration

**What Google/Effective Go says:** Not covered directly by Google's guide; Uber's [Avoid init()](https://github.com/uber-go/guide/blob/master/style.md#avoid-init) rule applies: `init()` should "be completely deterministic," "avoid depending on the ordering... of other `init()` functions," and "avoid I/O."

**How to detect it:** `grep -rn 'func init()'`. For each match, check the file's path. Outside `cmd/`, flag any `init()` that does I/O, reads environment/global state, or has an ordering dependency on another `init()`. Inside `cmd/`, `init()` is expected for CLI flag registration (`flag.Var`, `cobra.OnInitialize`) and similar program-entry wiring — do not flag those.

**Example violation:**
```go
// internal/config/config.go — NOT under cmd/
package config

var _config Config

func init() {
	cwd, _ := os.Getwd()
	raw, _ := os.ReadFile(filepath.Join(cwd, "config.yaml")) // I/O in init
	yaml.Unmarshal(raw, &_config)
}
```

**Corrected:**
```go
package config

func Load() (Config, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return Config{}, err
	}
	raw, err := os.ReadFile(filepath.Join(cwd, "config.yaml"))
	if err != nil {
		return Config{}, err
	}
	var cfg Config
	if err := yaml.Unmarshal(raw, &cfg); err != nil {
		return Config{}, err
	}
	return cfg, nil
}
```

Acceptable, because it's flag registration under `cmd/`:
```go
// cmd/billingsvc/main.go
package main

var region = flag.String("region", "us-east-1", "deployment region")

func init() {
	flag.Var(&extraTags, "tag", "additional metadata tag (repeatable)")
}
```

**Severity:** Violation outside `cmd/`; not flagged inside `cmd/`

**Enforced by:** `gochecknoinits` is scoped to exclude `cmd/` via a `path:` rule in this repo's `.golangci.yml` (`- path: cmd/` → disables `gochecknoinits`). Note `gochecknoinits` itself is **not** in this repo's enabled-linters list (see [golangci-lint.md](golangci-lint.md)), so today nothing in CI blocks `init()` anywhere — treat this as a Violation in audit output regardless, since it is Uber's documented rule and the config's `cmd/` exclusion only makes sense if the rule is otherwise active.

**Why it matters:** `init()` functions run implicitly at program startup in an order that's easy to get wrong across files and packages, and they make unit testing harder because their side effects can't be skipped or mocked. Flag registration in `cmd/` is the one place the pattern is idiomatic because Go's own `flag` and common CLI frameworks are designed around it.

## How to audit a Go module against these rules

1. List the directories in `<module>/internal/` (or wherever the module lives). For each: read the `package X` declaration and the first 30 lines of every file. Can you state the package's purpose in one sentence? If not, flag as Suggestion.
2. Does the package name appear in `util`, `helper`, `common`, `misc`, `lib`, `pkg`? Flag as Violation.
3. For each package, count `.go` files (excluding tests and generated code). Fewer than 2 with more than 50 lines each is fine. More than 12 hand-written files might be a smell — read the names; if they're all `partner_*.go`, suggest consolidating.
4. For each `_pb.go` and `_grpc.go` import, check the alias. Flag any short alias like `xpb` or two-letter aliases in new code.
5. Check whether the module has any `doc.go` files. Their absence in a complex package is a Suggestion, not a Violation (staticcheck ST1000 is exempted in this repo).
6. Run `goimports -local platform-backend -d` across the module; any diff is import-grouping drift, auto-fixable, not worth a manual finding beyond "run goimports."
7. Grep for fixture files (`.json`, `.golden`, sample inputs) outside `testdata/` directories.
8. Grep `func init()` outside `cmd/` — flag any that does I/O or depends on init ordering. Skip flag-registration `init()` under `cmd/`.
9. Read every `func main()` — flag business logic or multiple exit points; suggest extracting a `run() error`.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
