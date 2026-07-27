# Imports — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md). Severities below are cross-checked against `/home/user/workspace/go-skills-build/.golangci.yml`; see [golangci-lint.md](golangci-lint.md).

Import statements are the first thing a reader sees in a file, and they're the part of Go source most amenable to full automation — `goimports` and `gofumpt` will happily rewrite grouping and sorting for you. The rules here focus on what the formatters *don't* fix automatically: which imports are allowed at all (dot imports, blank imports), when renaming is appropriate, and how this repo's specific `goimports -local` configuration groups things.

## Three import groups: standard library, third-party, module-local

**What Google/Effective Go says:** Google's canonical grouping is stdlib, then everything else, with optional additional groups for generated proto imports and blank imports. ([Style Decisions: Import grouping](https://google.github.io/styleguide/go/decisions#import-grouping)) This repo's `goimports` is configured with `local-prefixes: platform-backend` (see [golangci-lint.md](golangci-lint.md#format-chain)), which collapses that into exactly **three** practical groups for everyday code: standard library, third-party, and same-module (`platform-backend/...`).

**How to detect it:** Run `goimports -local platform-backend -d <file>`. Any diff between the current import block and the tool's output is drift, not a judgment call.

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

**Enforced by:** `goimports` formatter with `local-prefixes: platform-backend` (see [golangci-lint.md](golangci-lint.md#format-chain)) — auto-fixed by `goimports -local platform-backend -w`, so don't hand-flag beyond pointing at the command

**Why it matters:** Grouping makes it instantly visible which imports are standard library, which are external dependencies that need a `go.sum` entry, and which are same-module code that can be refactored freely — and because it's auto-fixable, there's no reason to spend review time on it manually.

## Uber's simpler two-group model does not apply here — Google's grouping wins

**What Google/Effective Go says:** Uber's guide describes exactly two import groups — standard library, then everything else — matching plain `goimports` defaults with no `-local` flag. ([Uber: Import Group Ordering](https://github.com/uber-go/guide/blob/master/style.md#import-group-ordering)) Per this repo's [SOURCES.md](../../../SOURCES.md) precedence rule, Google's guide (which supports an explicit module-local group via `-local`) takes priority whenever the two disagree, and this repo's own `.golangci.yml` explicitly configures `local-prefixes: platform-backend` — so the three-group model above is the one to enforce, not Uber's two-group default.

**How to detect it:** If you see an import layout with only two groups (stdlib, then everything else including `platform-backend/...` imports mixed with third-party ones), that's the wrong model for this repo specifically — it would be correct under a plain `goimports` default, but not under this repo's configured `-local` flag.

**Example — correct under Uber's own default, but wrong for this repo's configured `-local` flag:**
```go
import (
	"fmt"
	"os"

	"github.com/google/uuid"
	"platform-backend/internal/partner"
)
```

**Corrected for this repo:**
```go
import (
	"fmt"
	"os"

	"github.com/google/uuid"

	"platform-backend/internal/partner"
)
```

**Severity:** Suggestion

**Enforced by:** `goimports` formatter with `local-prefixes: platform-backend`

**Why it matters:** This is a case where a well-known style guide's general default (Uber's two groups) is superseded by a project-specific configuration choice (this repo's three groups via `-local`) — worth calling out explicitly so nobody "corrects" a three-group import block back to two because they remembered Uber's rule from a different codebase.

## No dot imports outside tests

**What Google/Effective Go says:** "`import .`... [is] not allowed [outside test files] in the Google codebase." ([Style Decisions: Import renaming](https://google.github.io/styleguide/go/decisions#import-renaming))

**How to detect it:** Grep for `import . "` or `import (\n\t. "` in any non-`_test.go` file.

**Example violation:**
```go
// partner.go
import (
	. "example.com/internal/assertlib" // pulls every exported name into this file's namespace
)
```

**Corrected:**
```go
import (
	"example.com/internal/assertlib"
)
// call assertlib.Equal(...) explicitly
```

**Acceptable — DSL-style testing package in a `_test.go` file, per this repo's test-file relaxations (see [testing.md](testing.md#test-file-linter-relaxations)):**
```go
// partner_test.go
import (
	. "github.com/onsi/gomega"
)
```

**Severity:** Violation outside `_test.go`; permitted inside `_test.go`

**Enforced by:** revive/dot-imports — relaxed inside `_test.go` in this repo (`revive` is one of the six linters disabled for test files; see [golangci-lint.md](golangci-lint.md#test-file-relaxations))

**Why it matters:** A dot import pulls every exported identifier from the imported package directly into the current file's namespace with no qualifying prefix — a reader can no longer tell, at a call site, which package a given identifier came from, and a later addition to the imported package can silently shadow a name already in use.

## Blank imports must be documented and are restricted to `main` packages and tests

**What Google/Effective Go says:** "Blank imports... are only allowed in `main` packages, or tests that require them," with narrow exceptions for bypassing static-analysis tools and `//go:embed` companion imports. Every blank import should carry a comment explaining why. ([Style Decisions: Import renaming](https://google.github.io/styleguide/go/decisions#import-renaming))

**How to detect it:** Grep `_ "` inside import blocks. For each match, check (a) whether the file is in a `main` package or a test, and (b) whether a comment on the same line or immediately above explains the side effect being relied upon.

**Example violation — undocumented blank import in a library package:**
```go
// package partner — not main, not a test
import (
	_ "github.com/lib/pq"
)
```

**Corrected — documented, and relocated to where it belongs (a `main` package):**
```go
// cmd/partnersvc/main.go
import (
	_ "github.com/lib/pq" // registers the "postgres" driver with database/sql
)
```

**Acceptable exception — `//go:embed` companion import:**
```go
import (
	_ "embed" // required alongside a //go:embed directive
)

//go:embed schema.sql
var schemaSQL string
```

**Severity:** Violation

**Enforced by:** revive/blank-imports

**Why it matters:** A blank import's entire purpose is an invisible side effect (driver registration, format registration) — without a comment, a reader has no way to know the import is load-bearing and might "clean it up" as apparently unused, silently breaking whatever registration it was providing.

## Import aliasing only for collisions, uninformative names, or generated-package underscores

**What Google/Effective Go says:** Renaming is appropriate "to avoid a name collision... to improve the readability of an otherwise unintelligible name... or to avoid a clash with a local variable name." Uber's [Import Aliasing](https://github.com/uber-go/guide/blob/master/style.md#import-aliasing) rule adds: alias only when the local package name doesn't match the last path element. ([Style Decisions: Import renaming](https://google.github.io/styleguide/go/decisions#import-renaming))

**How to detect it:** Grep for import aliases (`alias "path"`). For each, check whether it falls into one of the legitimate categories below — if not, flag it as unnecessary noise.

**Example violation — alias with no purpose (matches the package's own name):**
```go
import (
	partner "platform-backend/internal/partner" // "partner" already matches the package name — redundant
)
```

**Corrected:**
```go
import (
	"platform-backend/internal/partner"
)
```

**Legitimate — resolving a genuine collision:**
```go
import (
	iopartner "platform-backend/io/partner"
	dbpartner "platform-backend/db/partner"
)
```

**Legitimate — local package name would otherwise be uninformative:**
```go
import (
	client "example.com/client-go" // last path element "client-go" isn't a valid identifier as-is
)
```

**Legitimate — removing underscores from a generated proto package (see the proto naming rule below):**
```go
import (
	pushqueueservicepb "example.com/proto/push_queue_service_go_proto"
)
```

**Severity:** Suggestion

**Enforced by:** not a dedicated `golangci-lint` rule; `goimports`/`gofumpt` do not remove unnecessary aliases automatically — catch via code review

**Why it matters:** An alias that doesn't resolve a real collision or naming problem adds a layer of indirection for no reason — a reader has to remember that `partner` in this file actually refers to a package that could just as easily have used its own name.

## Proto-generated package import naming

**What Google/Effective Go says:** Prefer whole-word aliases over short abbreviations — `pushqueueservicepb` over `pqsvc` or `xpb` — with a `pb` suffix marking generated proto packages and a `grpc` suffix marking generated gRPC packages. This is the import-specific half of the rule also covered in [packages.md](packages.md#proto-generated-package-import-naming). ([Best Practices: Protos](https://google.github.io/styleguide/go/best-practices#import-protos))

**How to detect it:** For every `_pb.go`/`_grpc.go` import, check the alias used against the whole-word, suffixed convention.

**Example violation:**
```go
import xpb "example.com/proto/push_queue_service_go_proto"
```

**Corrected:**
```go
import pushqueueservicepb "example.com/proto/push_queue_service_go_proto"
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — convention and code review only

**Why it matters:** A generated-package alias that reads as a whole word with its `pb`/`grpc` suffix (`pushqueueservicepb.Request{}`) signals "this is a generated type from package X" at the call site; a cryptic abbreviation forces the reader to jump to the import block to decode it.

## Never shadow a standard-library package name with a local variable

**What Google/Effective Go says:** This is the import-adjacent half of the naming rule in [naming.md](naming.md#dont-shadow-standard-library-package-names-with-variables); rooted in the general shadowing guidance of [Effective Go: Redeclaration and reassignment](https://go.dev/doc/effective_go#redeclaration) — a local variable or parameter with the same name as an imported package makes that package's identifiers unreachable for the rest of the scope.

**How to detect it:** For every imported package, grep the file for a local variable, parameter, or field with the exact same identifier as the package's default name.

**Example violation:**
```go
import "net/url"

func normalize(url string) (string, error) { // shadows the url package for this function's body
	u, err := url.Parse(url) // compile error: url is a string here, not the package
	if err != nil {
		return "", err
	}
	return u.String(), nil
}
```

**Corrected:**
```go
import "net/url"

func normalize(rawURL string) (string, error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return "", err
	}
	return u.String(), nil
}
```

**Severity:** Violation

**Enforced by:** `govet` (part of `enable-all`, with the `shadow` diagnostic specifically disabled for `err` only — package-name shadowing is a different, still-active class of check within `govet`'s broader analyses); this exact example is also a straightforward compile error the moment `url.Parse` is called, since `url` resolves to the local string parameter

**Why it matters:** Package-name shadowing usually surfaces immediately as a compile error the moment the package is actually used inside the shadowed scope — but in a large function where the package's identifiers aren't used until deep in the body, the shadowing can sit unnoticed for many lines before the compiler objects, costing a confusing debugging detour.

## Group and alphabetize within each import block (formatter-owned)

**What Google/Effective Go says:** "Within each group... imports should be sorted alphabetically" — but this is explicitly a formatter's job in this repo's toolchain, not something to review by eye. ([Style Decisions: Import grouping](https://google.github.io/styleguide/go/decisions#import-grouping); see [SOURCES.md](../../../SOURCES.md) on formatting being gofmt's domain, never re-litigated by hand)

**How to detect it:** Run `goimports -local platform-backend -d`. Any ordering diff is automatically fixable; don't spend review comments on manual reordering.

**Example — formatter output is authoritative:**
```go
import (
	"context"
	"fmt"
	"net/http"

	"github.com/google/uuid"
	"golang.org/x/sync/errgroup"

	"platform-backend/internal/partner"
)
```

**Severity:** Suggestion

**Enforced by:** `goimports` formatter (see [golangci-lint.md](golangci-lint.md#format-chain))

**Why it matters:** Sorting is exactly the kind of mechanical concern formatters exist to remove from human attention — flagging it manually in review just duplicates what `goimports -w` already does for free on every save.

## Import only what's used — no unused imports left as dead weight

**What Google/Effective Go says:** Not a stylistic preference — the Go compiler itself refuses to build a file with an unused, non-blank import. Google's guide references this as a baseline expectation rather than a rule to teach. ([Effective Go: Imports](https://go.dev/doc/effective_go#imports))

**How to detect it:** This one is self-enforcing: `go build` fails outright on an unused import. The audit-relevant version of this rule is checking for imports kept alive *artificially* — e.g., an import aliased to `_` specifically to suppress the compiler error, without the documented-side-effect justification the blank-import rule requires.

**Example violation — blank-aliased purely to dodge the compiler, no side effect intended:**
```go
import (
	_ "platform-backend/internal/partner" // added to "keep it around for later" — not a real blank import use case
)
```

**Corrected:**
```go
// remove the import entirely until the code that uses it actually exists
```

**Severity:** Violation

**Enforced by:** the Go compiler (`go build`/`go vet`) rejects unused non-blank imports outright; `unused` (part of this repo's enabled linters) catches unused identifiers more broadly, though a deliberately blank-aliased "for later" import evades both and requires human judgment

**Why it matters:** A blank import kept around "for later" with no actual side effect being relied upon defeats the entire purpose of the blank-import convention — every other blank import in the codebase now has to be individually checked for whether it's a real side-effect dependency or leftover scaffolding.

## How to audit Go code against these rules

1. Run `goimports -local platform-backend -d` across every changed file — any diff is auto-fixable grouping/sorting drift, not a manual finding.
2. Grep `import . "` outside `_test.go` files — flag as a Violation; permitted inside `_test.go`.
3. Grep `_ "` inside import blocks — confirm the file is `main` or a test, and confirm a comment explains the side effect relied upon.
4. Grep import aliases — for each, confirm it resolves a real collision, an uninformative last-path-element, or a generated-proto-package underscore; flag aliases that don't fall into one of those categories.
5. For every `_pb.go`/`_grpc.go` import, check the alias for whole-word, suffixed naming (`pushqueueservicepb`, not `xpb`).
6. For every imported package, grep the file for a local variable/parameter shadowing the package's default name.
7. Check for blank-aliased imports with no documented side effect — likely leftover scaffolding, should be removed.

Cross-check every finding's severity against [golangci-lint.md](golangci-lint.md) before reporting.
