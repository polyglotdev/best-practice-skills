<!-- Part of the `best-practice-go` skill. See SKILL.md for the index. -->

# 4. Imports

Import statements are the wiring between packages, and Go treats their
formatting as mechanical — but a few decisions (grouping, aliasing, dot
imports) are still yours to get right. This chapter draws from [Google
Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports),
[Effective Go](https://go.dev/doc/effective_go#formatting) (for the
formatting baseline `goimports` builds on), and Uber's [Import Group
Ordering](https://github.com/uber-go/guide/blob/master/style.md#import-group-ordering)
and [Import
Aliasing](https://github.com/uber-go/guide/blob/master/style.md#import-aliasing)
guidance. Package boundary decisions are covered in [Chapter
3](03-package-organization.md).

## 4.1 Let `goimports` group and order imports; never hand-arrange them.

> Why? `goimports` sorts imports alphabetically within groups and
> separates the standard library from everything else automatically.
> Hand-arranging imports produces churn on every save and inconsistent
> diffs across a team
> ([Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports)).

```go
// bad — manually ordered, mixed grouping
import (
	"github.com/acme/widget/internal/store"
	"fmt"
	"github.com/google/uuid"
	"context"
)

// good — goimports produces this automatically
import (
	"context"
	"fmt"

	"github.com/google/uuid"

	"github.com/acme/widget/internal/store"
)
```

## 4.2 Separate standard library, third-party, and module-local imports into three distinct groups.

> Why? Three visually distinct groups let a reader instantly see how
> much of a file's dependency surface is standard library versus
> external versus your own module's code — a useful signal when
> auditing dependencies or reviewing a diff
> ([Uber Style: Import Group
> Ordering](https://github.com/uber-go/guide/blob/master/style.md#import-group-ordering)).
> `goimports` produces exactly these three groups automatically when
> configured with `local-prefixes` set to your module path — don't
> invent a fourth group (e.g. splitting "internal" from other
> module-local packages); the module-local group covers all of it.

```go
// bad — everything in one group
import (
	"context"
	"github.com/acme/widget/internal/store"
	"fmt"
	"github.com/google/uuid"
)

// good — stdlib / third-party / module-local, each its own group
import (
	"context"
	"fmt"

	"github.com/google/uuid"

	"github.com/acme/widget/internal/store"
)
```

> Enforced by: `formatters: goimports` with `local-prefixes` set to your
> module path (e.g. `github.com/acme/widget`).

## 4.3 Never use dot imports (`import . "pkg"`) outside of test files that need it for a DSL.

> Why? A dot import pulls every exported identifier from the imported
> package into the current file's namespace with no qualifier, so
> readers can no longer tell which package an identifier came from. The
> narrow exception is test files using assertion DSLs designed for it
> ([Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports)).

```go
// bad — production code, unqualified identifiers from math
package geometry

import . "math"

func Circumference(r float64) float64 { return 2 * Pi * r }

// good
package geometry

import "math"

func Circumference(r float64) float64 { return 2 * math.Pi * r }
```

> Enforced by: `revive` `dot-imports`. Note the exception: inside
> `_test.go` files, teams commonly relax this rule for assertion DSLs
> that are designed around dot-importing, such as
> `. "github.com/onsi/gomega"`. Outside test files, treat this as a
> hard Violation, not a Suggestion.

## 4.4 Document every blank import (`import _ "pkg"`) with a comment explaining the side effect.

> Why? A blank import exists purely for its `init()` side effects (e.g.
> registering a SQL driver or image codec) — there's no identifier at
> the call site to explain why it's there. Without a comment, the next
> reader can't tell if the import is dead weight or load-bearing
> ([Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports)).

```go
// bad
import _ "github.com/lib/pq"

// good
import (
	// Registers the "postgres" driver with database/sql.
	_ "github.com/lib/pq"
)
```

> Enforced by: `revive` `blank-imports`. This is a hard rule in
> production code; there is no test-file relaxation for it since an
> undocumented blank import is equally confusing in a test.

## 4.5 Alias an import only to resolve a name collision or avoid a non-identifier package name.

> Why? Gratuitous aliasing (`import cfg "config"`) removes the reader's
> ability to recognize the real package name at a glance and search for
> it elsewhere in the codebase. Aliasing should be reserved for genuine
> conflicts — two imports that would otherwise share the same identifier
> ([Uber Style: Import
> Aliasing](https://github.com/uber-go/guide/blob/master/style.md#import-aliasing)).

```go
// bad — aliased with no collision to resolve
import (
	cfg "github.com/acme/widget/config"
)

func Load() cfg.Config { return cfg.Config{} }

// good — no alias needed; import as-is
import (
	"github.com/acme/widget/config"
)

func Load() config.Config { return config.Config{} }

// good — alias only because two packages both default to "trace"
import (
	stdtrace "runtime/trace"
	oteltrace "go.opentelemetry.io/otel/trace"
)
```

## 4.6 When aliasing is required, choose a name that reflects the real package, not an arbitrary abbreviation.

> Why? An alias that doesn't map obviously back to the real package
> name forces readers to jump to the import block every time they hit
> the identifier. Uber's convention is to base the alias on the last
> element of the import path plus enough of the parent directory to
> disambiguate ([Uber Style: Import
> Aliasing](https://github.com/uber-go/guide/blob/master/style.md#import-aliasing)).

```go
// bad — arbitrary alias with no relationship to the package
import (
	x "github.com/acme/widget/internal/store"
)

func Load() x.Store { return x.Store{} }

// good — alias reflects the true package path
import (
	widgetstore "github.com/acme/widget/internal/store"
)

func Load() widgetstore.Store { return widgetstore.Store{} }
```

## 4.7 Never use relative import paths.

> Why? Go's module system resolves imports by full module path, not
> filesystem-relative paths like `"./store"`. Relative-style paths
> aren't valid Go import syntax and signal the author is thinking in
> terms of another language's module system
> ([Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports)).

```go
// bad — not valid Go and won't compile
import "./store"

// good — full module-qualified import path
import "github.com/acme/widget/internal/store"
```

## 4.8 Keep import paths import-only; don't import a package solely to reference its doc comments or constants you could inline.

> Why? Every import is a dependency edge that has to be built, vetted,
> and kept compatible. Importing a heavy package for a single trivial
> constant you could define locally adds a needless dependency and
> coupling ([Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports)).

```go
// bad — imports an entire third-party package for one constant
import "github.com/acme/bigsdk/constants"

const defaultRegion = constants.RegionUSEast1

// good — inline the value directly if the SDK isn't otherwise needed
const defaultRegion = "us-east-1"
```

## 4.9 Run `goimports` (or an editor integration) automatically, not as a manual afterthought.

> Why? Manual import maintenance is exactly the kind of mechanical task
> that should never depend on a human remembering to do it — the same
> principle from [Chapter 1](01-formatting.md) applies to imports as a
> subset of formatting. A forgotten unused import fails the build; a
> forgotten missing import fails the build too, but only after the
> compiler tells you, whereas `goimports` fixes both before you ever
> see an error ([Style Decisions: Imports](https://google.github.io/styleguide/go/decisions#imports)).

```go
// bad — developer manually deletes an import line, misses that another is now unused
import (
	"context"
	"fmt" // now unused after a refactor, left behind — build fails
)

func Ping(ctx context.Context) {}

// good — goimports removes it automatically on save
import (
	"context"
)

func Ping(ctx context.Context) {}
```

## 4.10 Group standard-library test-only imports (e.g. `testing`) the same way as production imports — no special-casing.

> Why? Test files follow the same three-group convention as production
> files; `testing` is just another standard-library import and belongs
> in the standard-library group, not singled out
> ([Uber Style: Import Group
> Ordering](https://github.com/uber-go/guide/blob/master/style.md#import-group-ordering)).

```go
// bad — testing pulled out of its natural stdlib group
import (
	"testing"

	"context"
	"fmt"

	"github.com/acme/widget/internal/store"
)

// good
import (
	"context"
	"fmt"
	"testing"

	"github.com/acme/widget/internal/store"
)
```
