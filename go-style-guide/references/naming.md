# Naming — Google Go Style Guide audit checklist

Source hierarchy: [Google Style Guide](https://google.github.io/styleguide/go/guide) → [Style Decisions](https://google.github.io/styleguide/go/decisions) → [Best Practices](https://google.github.io/styleguide/go/best-practices) → [Effective Go](https://go.dev/doc/effective_go) → [Uber Style Guide](https://github.com/uber-go/guide/blob/master/style.md) (only where not already covered). See `/home/user/workspace/go-skills-build/SOURCES.md` for the full precedence rule.

The Go community treats names as part of the API. They communicate intent, and they're the most visible thing about your code at the call site. Most of the rules below exist to make call-sites read well — when you read `config.JobName("worker")` it's already clear what's happening; `config.GetJobName("worker")` adds a verb that conveys nothing ([Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming)).

## Don't prefix value-returning functions with `Get`

**What Google/Effective Go says:** "Function and method names should avoid the prefix `Get`... Functions that return something are given noun-like names." ([Style Decisions: Getters](https://google.github.io/styleguide/go/decisions#getters))

**How to detect it:** `grep -nE 'func .* Get[A-Z]'` — flag every match that returns a value. Exempt cases that are a genuine HTTP-style GET or where "get" is the domain verb (rare).

**Example violation:**
```go
func (c *Config) GetJobName(key string) (value string, ok bool) {
	v, ok := c.jobs[key]
	return v, ok
}
```

**Corrected:**
```go
func (c *Config) JobName(key string) (value string, ok bool) {
	v, ok := c.jobs[key]
	return v, ok
}
```

**Severity:** Violation

**Enforced by:** revive/exported (Getters are flagged as part of the `exported` rule's naming checks under `golangci-lint`; see [golangci-lint.md](golangci-lint.md))

**Why it matters:** The return type and signature already communicate "this returns a value." `Get` is a carryover from Java/C++ naming conventions and adds noise at every call site.

## Functions that perform actions use verb-like names

**What Google/Effective Go says:** "Functions that do something are given verb-like names," e.g. `WriteDetail`, not `Detail`. ([Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming))

**How to detect it:** Read every exported function whose body performs I/O, mutation, or a side effect (writes, sends, registers, publishes). Check whether the name is a noun. Flag nouns used for action functions.

**Example violation:**
```go
func (w *Logger) Detail(entry string) error {
	return w.write(entry)
}
```

**Corrected:**
```go
func (w *Logger) WriteDetail(entry string) error {
	return w.write(entry)
}
```

**Severity:** Suggestion

**Why it matters:** Mixing verbs and nouns codebase-wide is fine, but a single function whose name is a noun while its body performs an action misleads the reader about whether calling it is free or has side effects.

## Don't repeat the package name in exported identifiers

**What Google/Effective Go says:** "For functions, do not repeat the name of the package." Example: `package yamlconfig` should export `Parse`, not `ParseYAMLConfig`. ([Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming); [Style Decisions: Repetition](https://google.github.io/styleguide/go/decisions#repetition))

**How to detect it:** For each exported function/type, check whether the identifier starts with (or contains) the package name. Call sites already have the package name as a prefix, so `yamlconfig.ParseYAMLConfig(x)` reads as "yamlconfig.parseYAMLconfig" — YAML appears three times.

**Example violation:**
```go
// in package yamlconfig
func ParseYAMLConfig(input string) (*Config, error)

type YAMLConfig struct{ /* ... */ }
```

**Corrected:**
```go
// in package yamlconfig
func Parse(input string) (*Config, error)

type Config struct{ /* ... */ }
```

**Severity:** Suggestion (downgraded from Violation — `disableStutteringCheck` is set on revive's `exported` rule in this repo's `.golangci.yml`, so the linter itself does not fail the build on package-name stutter; see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation))

**Enforced by:** not enforced by `golangci-lint` in this repo (stuttering check disabled) — flag as a readability suggestion only

**Why it matters:** Redundant prefixes make call sites longer without adding information, and they make it harder to search for the "real" name of a type or function.

## Don't repeat the receiver type in method names

**What Google/Effective Go says:** "For methods, do not repeat the name of the method receiver." ([Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming))

**How to detect it:** For every method, check whether the method name includes the receiver type name (`func (c *Config) WriteConfigTo(...)`).

**Example violation:**
```go
func (c *Config) WriteConfigTo(w io.Writer) (int64, error)
```

**Corrected:**
```go
func (c *Config) WriteTo(w io.Writer) (int64, error)
```

**Severity:** Violation

**Enforced by:** revive/receiver-naming (flags receiver-name inconsistency; the method-name-repeats-receiver-type pattern itself is caught by revive/exported and code review, not a dedicated revive rule)

**Why it matters:** The receiver is already visible at the call site (`c.WriteTo(w)`); repeating it in the method name is pure redundancy.

## Don't repeat parameter names or return types/names in the function name

**What Google/Effective Go says:** "Do not repeat the names of variables passed as parameters" and "Do not repeat the names and types of the return values." Example: `OverrideFirstWithSecond(dest, source *Config)` should be `Override(dest, source *Config)`; `TransformToJSON(input *Config) *jsonconfig.Config` should be `Transform(...)`. ([Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming))

**How to detect it:** Read the parameter and return-type names for each exported function. If the function name spells out a parameter name or the return type, flag it — unless it disambiguates a family of similarly named functions.

**Example violation:**
```go
func OverrideFirstWithSecond(dest, source *Config) error

func TransformToJSON(input *Config) *jsonconfig.Config
```

**Corrected:**
```go
func Override(dest, source *Config) error

func Transform(input *Config) *jsonconfig.Config
```

When disambiguation is genuinely needed, add the type suffix only to non-primary variants:
```go
func ParseInt(s string) (int, error)
func ParseInt64(s string) (int64, error)
func ParseFloat(s string) (float64, error)

// In encoding/json, the "primary" version has no suffix:
func Marshal(v any) ([]byte, error)
```

**Severity:** Violation

**Enforced by:** not directly enforced by a single `golangci-lint` rule; catch via `revive/exported` naming review and code review

**Why it matters:** The signature already shows the parameter and return types; naming them again just adds length without adding information, and makes renaming a parameter type a breaking rename of the function too.

## Initialisms keep consistent case (`URL`, `ID`, `HTTP`, not `Url`, `Id`, `Http`)

**What Google/Effective Go says:** "Words in names that are initialisms or acronyms... should have the same case. `URL` should appear as `URL` or `url`... never as `Url`." Multi-initialism names like `XMLAPI` keep each initialism internally consistent even if the two initialisms differ in case from each other; lowercase-led initialisms like `gRPC`/`iOS`/`DDoS` follow prose casing except where exportedness forces a change (`GRPC`, `IOS`, `DDoS` stays `DDoS` when exported). ([Style Decisions: Initialisms](https://google.github.io/styleguide/go/decisions#initialisms))

**How to detect it:** `grep -nE '\b(Url|Id|Http|Api|Json|Xml|Uuid|Db|Grpc)\b'` across identifiers (exported and unexported) — case-sensitive. Each match where the word is meant to be an initialism (not an unrelated word) is a violation. Cross-check against the reference table: `ID`/`id`, `DB`/`db`, `URL`/`url`, `HTTP`/`http`, `API`/`api`, `JSON`/`json`, `XML`/`xml`, `GRPC`/`gRPC`.

**Example violation:**
```go
type UserId struct {
	Id  string
	Url string
}

func FetchJsonApi(httpClient *http.Client, apiUrl string) ([]byte, error)
```

**Corrected:**
```go
type UserID struct {
	ID  string
	URL string
}

func FetchJSONAPI(httpClient *http.Client, apiURL string) ([]byte, error)
```

**Severity:** Suggestion (downgraded from Violation — this repo's `.golangci.yml` disables `staticcheck` check ST1003 "poorly chosen identifier," which is what flags `Url`/`Id`/`Http` casing; see [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation))

**Enforced by:** not enforced in this repo (staticcheck ST1003 exempted) — recommend for readability only, do not block review on it

**Why it matters:** Inconsistent initialism casing (`Id` vs `ID`) breaks the visual scanning readers rely on to recognize well-known abbreviations, and forces call sites to guess the exact casing instead of pattern-matching. Even though this repo does not fail CI on it, it is still worth flagging as a suggestion since it is Google's documented convention.

## Test-double packages append `test` to the production package name

**What Google/Effective Go says:** "A safe choice is to append the word `test` to the original package name," e.g. `creditcard` → `creditcardtest`. ([Best Practices: Naming test doubles](https://google.github.io/styleguide/go/best-practices#naming-test-doubles))

**How to detect it:** Find directories that contain only test-double types (stubs, fakes, spies, mocks) for a sibling production package. Check whether the package name is `<production>test`.

**Example violation:**
```go
// package creditcardmocks — doesn't signal it's for creditcard
package creditcardmocks

type Stub struct{}
```

**Corrected:**
```go
package creditcardtest

import "example.com/creditcard"

// Stub stubs creditcard.Service and provides no behavior of its own.
type Stub struct{}

func (Stub) Charge(*creditcard.Card, money.Money) error { return nil }
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — organizational convention only

**Why it matters:** This makes imports immediately recognisable as test-only, and if the package is built with Bazel it pairs with marking the `go_library` rule `testonly`.

## Test-double type names match their behaviour (Fake/Stub/Spy)

**What Google/Effective Go says:** "If you anticipate only test doubles for one type... you can take a concise approach," using bare `Stub`, `Fake`, or `Spy`; when a package has multiple doubles, "we recommend naming the stubs according to the behavior they emulate" (`AlwaysCharges`, `AlwaysDeclines`); when multiple *types* need doubles, use full names (`StubService`, `StubStoredValue`). ([Best Practices: Naming test doubles](https://google.github.io/styleguide/go/best-practices#naming-test-doubles))

**How to detect it:** In `*test` packages, list exported types. A single-type package should have concise names (`Stub`, `Fake`, `Spy`) rather than `StubCreditCardService`. A package with multiple behaviors or multiple production types should use behavior-based or type-qualified names, not a single generic `Stub` that silently means different things over time.

**Example violation:**
```go
package creditcardtest

// Too generic once a second behavior/type is added later.
type Stub struct{}
func (Stub) Charge(*creditcard.Card, money.Money) error { return nil }

type Stub2 struct{} // meaningless disambiguation
func (Stub2) Charge(*creditcard.Card, money.Money) error { return creditcard.ErrDeclined }
```

**Corrected:**
```go
package creditcardtest

// AlwaysCharges stubs creditcard.Service and simulates success.
type AlwaysCharges struct{}
func (AlwaysCharges) Charge(*creditcard.Card, money.Money) error { return nil }

// AlwaysDeclines stubs creditcard.Service and simulates declined charges.
type AlwaysDeclines struct{}
func (AlwaysDeclines) Charge(*creditcard.Card, money.Money) error {
	return creditcard.ErrDeclined
}
```

For local variables holding test-double values, prefix with the double kind so the test reader knows it's a fake:
```go
// good: "spy" tells the reader this is a test double
var spyCC creditcardtest.Spy

// worse: looks like a production type at a glance
var cc creditcardtest.Spy
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — readability convention only. Note this repo also disables `errcheck`, `errorlint`, `gosec`, `revive`, `bodyclose`, and `unparam` inside `_test.go` (see [golangci-lint.md](golangci-lint.md#test-file-relaxations)), so test-double files will pass lint even with looser error handling; naming quality is still worth a human review pass.

**Why it matters:** Vague or colliding double names force the reader to open the double's source to learn what behavior it simulates; behavior-based names make the test's setup self-explanatory.

## Receiver naming — short, consistent, no `this`/`self`

**What Google/Effective Go says:** Receiver variable names must be "Short (usually one or two letters)... Abbreviations for the type itself... Applied consistently to every receiver for that type... Not an underscore; omit the name if it is unused." ([Style Decisions: Receiver names](https://google.github.io/styleguide/go/decisions#receiver-names))

**How to detect it:** For every type with methods, list the receiver identifier used across all methods. Flag inconsistent choices (`c` in one method, `cfg` in another) and flag `this`/`self`/long words as receiver names.

**Example violation:**
```go
func (tray Tray) Weight() float64 { /* ... */ }
func (this *Tray) AddItem(i Item) { /* ... */ }
func (self *Tray) Empty() { /* ... */ }
```

**Corrected:**
```go
func (t Tray) Weight() float64 { /* ... */ }
func (t *Tray) AddItem(i Item) { /* ... */ }
func (t *Tray) Empty() { /* ... */ }
```

**Severity:** Violation

**Enforced by:** revive/receiver-naming

**Why it matters:** `this`/`self` import an OOP convention Go doesn't use, and inconsistent receiver names across a type's methods make it harder to skim the method set and confirm they all operate on "the same kind of thing."

## Receivers — consistent value vs. pointer within a type

**What Google/Effective Go says:** Mixing pointer and value receivers on the same type is a documented anti-pattern in [Effective Go: Pointers vs. Values](https://go.dev/doc/effective_go#pointers_vs_values); the rule of thumb is to pick one based on whether any method mutates state, and apply it to every method.

**How to detect it:** For each type, list every method's receiver. If some are `T` and others are `*T` with no clear justification (e.g. one tiny read-only accessor kept as a value for a large type), flag it.

**Example violation:**
```go
func (c Config) Name() string      { return c.name }
func (c *Config) SetName(s string) { c.name = s }
```

**Corrected:**
```go
func (c *Config) Name() string      { return c.name }
func (c *Config) SetName(s string) { c.name = s }
```

**Severity:** Suggestion

**Enforced by:** not a dedicated `golangci-lint` rule in this config; `govet`'s `copylocks` check (part of `enable-all`) will catch the specific case of copying a type containing a mutex or other no-copy field, which often co-occurs with mixed receivers

**Why it matters:** Mixed receivers are confusing for readers and can hide subtle bugs — a value receiver silently operates on a copy, so mutations inside it never propagate, which is surprising next to a pointer-receiver sibling method that does mutate.

## Don't shadow standard-library package names with variables

**What Google/Effective Go says:** "It is not a good idea to use variables with the same name as standard packages other than very small scopes, because that renders free functions and values from that package inaccessible." ([Style Decisions: Variable names](https://google.github.io/styleguide/go/decisions#variable-names))

**How to detect it:** Grep for `:=` or `var` declarations assigning to `url`, `path`, `context`, `time`, `net`, `sort`, `strings`, etc., in files that import the same-named stdlib package later or already.

**Example violation:**
```go
func LongFunction() {
	url := "https://example.com/"
	// Oops, now we can't use net/url in code below.
}
```

**Corrected:**
```go
func LongFunction() {
	u := "https://example.com/"
	parsed, err := url.Parse(u)
	// ...
}
```

**Severity:** Violation

**Enforced by:** `govet` (part of `enable-all`) catches many shadowing cases generally, though this repo specifically disables the `shadow: declaration of "err"` diagnostic (see [error-handling.md](error-handling.md#intentional-err-shadowing-inside-an-if-is-not-a-bug) and [golangci-lint.md](golangci-lint.md#rules-the-user-exempts-map-to-suggestion-not-violation)); package-name shadowing (`url`, `path`, etc.) is unaffected by that exemption and is still flagged

**Why it matters:** Once shadowed, the package's functions become unreachable for the rest of that scope; a later line that calls `url.Parse` will fail to compile or, worse, silently resolve to the wrong `url`.

## Package names avoid `util`/`common`/`helper`/`misc` and avoid stuttering

**What Google/Effective Go says:** "Go package names should not have underscores... Avoid uninformative package names like `util`, `utility`, `common`, `helper`, `model`, `testhelper`" ([Style Decisions: Package names](https://google.github.io/styleguide/go/decisions#package-names)); consider the call site: `spannertest.NewDatabaseFromFile(...)` reads better than `test.NewDatabaseFromFile(...)`. ([Best Practices: Naming](https://google.github.io/styleguide/go/best-practices#naming))

**How to detect it:** Read the `package` declaration and directory name for each package. Flag `util`, `utils`, `helper`, `helpers`, `common`, `misc`, `model`, `base`, `shared`, `lib`. Separately, check whether the package name is repeated inside its own exported identifiers (`yamlconfig.YAMLConfig` stutters — see the repetition rule above).

**Example violation:**
```go
package util

func NewDatabaseFromFile(path string) (*DB, error) { /* ... */ }

// call site:
db := util.NewDatabaseFromFile("data.db")
```

**Corrected:**
```go
package spannertest

func NewDatabaseFromFile(path string) (*DB, error) { /* ... */ }

// call site:
db := spannertest.NewDatabaseFromFile("data.db")
```

**Severity:** Violation

**Enforced by:** not enforced by a specific `golangci-lint` rule (no linter inspects package-name semantics); enforce via code review and the [packages.md](packages.md) checklist

**Why it matters:** Uninformative names give the call site no information about what the package does, and because they're so common, they collide across many projects and tempt every importer into a rename.

## File names are lowercase with underscores, not Go identifiers

**What Google/Effective Go says:** "Filenames of source code are not Go identifiers and do not have to follow these conventions. They may contain underscores." Convention in the wild and in the standard library is lowercase, `snake_case` where multiple words are needed (e.g. `tabwriter.go`, `client_test.go`). ([Style Decisions: Underscores](https://google.github.io/styleguide/go/decisions#underscores))

**How to detect it:** List filenames in the package directory. Flag `CamelCase.go`, `mixedCase.go`, or filenames containing characters other than lowercase letters, digits, and underscores.

**Example violation:**
```
partnerRepository.go
PartnerStatus.go
```

**Corrected:**
```
partner_repository.go
partner_status.go
```

**Severity:** Suggestion

**Enforced by:** not enforced by `golangci-lint` — filesystem/organizational convention only

**Why it matters:** Consistent lowercase-with-underscores filenames match the standard library and every major linter's expectations, and avoid case-sensitivity bugs on case-insensitive filesystems (notably macOS default configurations).

## How to audit Go code against these rules

For a file or package:

1. `grep -nE 'func .* Get[A-Z]'` — flag every match that returns a value.
2. For every exported function/type/method, read the package name. Does the identifier start with the package name? Flag.
3. For every method, read the receiver type. Does the method name include the receiver type? Flag.
4. For every package, look at the directory name and the `package` declaration. Is it `util`, `helper`, `common`? Flag.
5. For test files, look at variable names holding test-double types. Are they prefixed (`spyCC`, `stubService`)? If not, suggest.
6. For local variables, grep for `:=` followed by `url`, `path`, `ctx`, `context`, `time`, `net`, etc. — flag any that shadow a stdlib package the file imports.
7. Grep identifiers for `Id`, `Url`, `Http`, `Api`, `Json`, `Xml`, `Db` as substrings (case-sensitive) — flag any that should be all-caps initialisms.
8. For each type, list receiver names across all its methods — flag inconsistency and flag `this`/`self`.
9. List filenames in the package — flag any that aren't lowercase-with-underscores.

When flagging, link to the exact section of the source guide and explain *why* — not just "rule says no." Cross-check severity against [golangci-lint.md](golangci-lint.md) before reporting: if this repo's `.golangci.yml` does not enforce a rule (ST1003 initialism casing, stutter-check-disabled `exported`), report it as a Suggestion even though the upstream guide treats it as a hard rule.
