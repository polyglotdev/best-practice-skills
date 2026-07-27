# Session 0 handoff — 2026-07-27

Expansion of `best-practice-skills` from 5 skills to 7. **Java and Kotlin are
complete.** Ruby and Python are next and have not been started.

---

## 1. What shipped this session

### New skills

| Skill | Chapters | Rules | Lines | SKILL.md |
|---|---:|---:|---:|---:|
| `best-practice-java` | 38 | 798 | 27,119 | 248 |
| `best-practice-kotlin` | 47 | 851 | 31,302 | 303 |
| **Total** | **85** | **1,649** | **58,421** | |

Both SKILL.md files are well under the 500-line ceiling. The rule mass lives
in `references/NN-topic.md`, matching the existing Go/JS/TS/React pattern.

### New configuration

| File | Contents |
|---|---|
| `config/checkstyle/checkstyle.xml` | 84 modules, XML-validated |
| `config/checkstyle/checkstyle-suppressions.xml` | 7 suppressions, XML-validated |
| `config/detekt/detekt.yml` | 107 rules, YAML-validated, 0 fabricated, 0 misplaced |
| `.editorconfig` | Java block (2-space, 100 col), Kotlin block (4-space, 100 col, ktlint keys) |

### New documentation

- `README-java.md` (214 lines) — chapter inventory, tool division of labour,
  the two departures from upstream `google_checks.xml`, known gaps.
- `README-kotlin.md` — 47-chapter inventory, the 4-space divergence, the
  Kotlin 2.4 stable-vs-experimental split, the shipped detekt config, and the
  detekt 1.23.8-versus-2.0-alpha situation.
- `README.md` — updated for **both** new skills: skill table, install tree,
  Codex `AGENTS.md` snippet, invocation examples, root-config section, design
  principles.
- `docs/reference-data/` — harvested anchor ground truth (1,234 anchors across
  6 guides) plus regeneration commands and the extraction traps.
- This handoff.

Both skills are complete. No deliverable is outstanding for Java or Kotlin.

---

## 2. Decisions locked with the user

Do not re-litigate these. They were explicit choices, several of them
corrections to my initial recommendation.

| Decision | Value | Notes |
|---|---|---|
| Em dashes | **Use them in repo files** | Local override of the global CLAUDE.md ban. Chat replies stay em-dash-free. The 5 pre-existing skills use them pervasively. |
| Java floor | **Java 21 LTS** | Confirmed by the local JRE (21.0.5 LTS). |
| Java framework layer | **Spring Boot 3.x** | Chapters 32-37. |
| Kotlin floor | **Kotlin 2.4** | Confirmed locally: `kotlinc-jvm 2.4.10`, sdkman default. |
| Kotlin indent | **4 spaces** | Upstream wins over the user's global `KOTLIN.md` 2-space rule. Documented as a deliberate divergence in SKILL.md. |
| Kotlin framework layer | **Spring + coroutines deep-dive** | Chapters 33-40 coroutines, 41-46 Spring delta. |
| Kotlin vs existing skill | **Keep both** | Global `kotlin-best-practices` stays Micronaut/Arrow/Exposed. This one is Spring. Different skills. |
| Ship linter configs | **Yes, all four languages** | With per-rule `> Enforced by:` callouts, mirroring `.golangci.yml`. |
| Python/Ruby style | **Single quotes, 2-space indent** | For Python this deviates from PEP 8 and pyguide §3.4 and must be documented as a house override. |
| **Ruby floor** | **4.0** (revised) | Was 3.4. User installed 4.0.5 via asdf mid-session with rubocop. |
| **Python floor** | **3.12** (confirmed) | **3.12.10 installed and now the pyenv global default** (verified). See §6 for my retracted objection. |

---

## 3. The method that worked, and why it is not optional

Each skill was authored by a fan-out of subagents (14 for Java, 16 for
Kotlin), each batch followed immediately by an **adversarial verifier** told
to assume the author was wrong.

### Defects the verify pass caught and fixed

| Category | Java | Kotlin |
|---|---:|---:|
| Fabricated citation | 60 | 49 |
| Fake check / rule id | 48 | 14 |
| Code error | 41 | 35 |
| Contract drift | 32 | 39 |
| Hallucinated API | 6 | 10 |
| Wrong version claim | 3 | 8 |
| **Total** | **190** | **155** |

**345 defects across 85 chapters.** Roughly four per chapter. Authoring
without the verify pass would have shipped every one of them.

### Defects my own reconciliation caught afterward

The verifiers are not sufficient on their own. A mechanical pass over the
finished corpus found more:

- **Java: 22 distinct broken style-guide anchors** across 196 links, plus 5
  `Enforced by:` callouts naming a real check that the shipped config did not
  enable.
- **Kotlin: 58 callouts** naming a real detekt rule that was not effective;
  31 needed enabling, 20 were already on by detekt's defaults, 7 do not exist
  in the stable release at all.

Final state for both skills: **0 broken anchors, 0 fabricated tool names,
0 false enforcement claims.**

### Things I got wrong, and how they were caught

Recording these because they are the failure modes to expect next session.

1. **My "verified" anchor list was partly fabricated.** I asked WebFetch for
   the Google Java Style Guide's section anchors. The summarizing model
   *inferred* them from section titles rather than reading the page. About a
   third were wrong. A verifier caught it by curling raw HTML.
   **Lesson: never take anchors from a summarizer. Curl the HTML.**

2. **Two scrapes returned zero and looked like evidence.** Error Prone anchors
   have no `.html` suffix; detekt writes **unquoted** `id=` attributes. Both
   produced clean "NOT FOUND" lists that would have read as proof that real
   check names were fabricated. **Lesson: an empty result set is a broken
   query until proven otherwise. Sanity-check the extractor against a value
   you know is present.**

3. **I dropped `MissingSwitchDefault` from checkstyle.xml for a wrong reason.**
   I claimed it fights sealed exhaustive switches. Its docs say it skips
   switch *expressions* and pattern/null-label switches entirely. The real
   conflict is only old-style colon-form enum switches. Now enabled, with the
   narrow caveat documented.

4. **A YAML append silently destroyed 9 detekt rules**, including the flagship
   `UnsafeCallOnNullableType` (`!!` ban). Appending a second `style:` key is
   valid YAML; the parser keeps only the last occurrence. `yaml.safe_load`
   succeeded and reported nothing. **Lesson: "it parses" is not "it is
   intact." Probe for known keys after any structural edit.**

5. **I told the Kotlin agents that context parameters and explicit backing
   fields were Experimental.** Kotlin 2.4 promoted both to **Stable**. A
   verifier caught it against the 2.4 release notes. SKILL.md and chapter 29
   corrected.

6. **My audit test for detekt was wrong.** I checked "is this rule in my
   config file" when the config is applied with `buildUponDefaultConfig =
   true`, so an unmentioned rule keeps its detekt default. The correct test is
   against `config ∪ detekt-defaults`.

### The reconciliation rule (apply to Ruby and Python)

> Citing a check that **exists** is not the same as citing a check the shipped
> configuration **enables**. Both must hold before a rule may be labeled
> **Violation**. After authoring, diff every `> Enforced by:` name against
> both the tool's catalogue and the effective enabled set, then either enable
> the check or downgrade the callout to **Suggestion**.

---

## 4. Notable technical decisions embedded in the artifacts

- **Formatting is always delegated**, never argued in prose. `gofmt` for Go,
  Prettier for JS/TS/React, `google-java-format` for Java, `ktlint` for
  Kotlin. Chapter 1 of each skill states the chain; no later chapter
  re-litigates whitespace. Ruby and Python must follow the same shape
  (`rubocop -a` / `ruff format`).
- **`checkstyle.xml` is derived, not copied.** Every formatting check from
  upstream `google_checks.xml` is removed, and ~30 Effective Java design
  checks Google omits are added, so chapters can carry honest callouts.
- **detekt 2.0 is alpha-only** (`v2.0.0-alpha.5`, 2026-06-17); latest stable
  is **1.23.8**. detekt.dev documents 2.x. That mismatch is why 7 cited rules
  are absent from the stable default config. Those callouts are downgraded to
  **Suggestion** with a re-check-on-upgrade note.
- **Java non-goals**: Lombok and JPA/Hibernate entity design were deliberately
  left out rather than half-covered. Flagged in `README-java.md`.

---

## 5. Starting point: Ruby

### Settled

| Item | Value |
|---|---|
| Skill name | `best-practice-ruby` |
| Language floor | **Ruby 4.0** |
| Local install | **4.0.5** via **asdf** (`~/.asdf/installs/ruby/4.0.5`), with bundler, pry, ripper-tags, cocoapods, rubocop |
| Primary source | <https://rubystyle.guide/> (359 anchors harvested) |
| Framework layer | **Rails**, from <https://rails.rubystyle.guide/> (150 anchors harvested) |
| Linter | **RuboCop** — local 1.81.7, latest 1.88.2, 588 cops across 9 departments (Style 282, Lint 152, Layout 100, Naming 19, Metrics 10, Gemspec 10, Security 7, Bundler 7, Migration 1) |
| Rails cops | `rubocop-rails` latest 2.36.0 |
| Style | Single quotes, 2-space indent — **both are already RuboCop/rubystyle defaults**, so unlike Python this needs no deviation note |
| Ship config | `.rubocop.yml` at repo root |

Ruby stable line per ruby-lang.org is **4.0.6**; the 3.4 line is at 3.4.10.
The user installed 4.0.5.

### Open questions to resolve first

1. **Ruby 4.0 feature set.** My training predates it. Before authoring, read
   the 4.0 release notes and NEWS. Do not write 4.0 chapters from memory.
   Specifically confirm what changed around frozen string literals, which was
   a long-running 3.x deprecation path and directly affects a string chapter.
2. **Does rubystyle.guide target 4.0 yet?** If the guide still says 3.x in
   places, chapters must say so rather than silently modernise it.
3. **RuboCop version to pin.** Local is 1.81.7 but the fresh 4.0.5 install
   pulled a newer rubocop. Run `rubocop -v` under the asdf 4.0.5 shim and pin
   the config to that. Cop names change between minors.
4. **Rails version target.** Not yet chosen. Needed before chapters 
   on ActiveRecord, callbacks, and strong params.
5. **Additional cop gems**: `rubocop-rspec`, `rubocop-performance`,
   `rubocop-rails` — decide which ship in `.rubocop.yml`.

### Suggested chapter shape

Roughly 40-45 chapters, mirroring the Java/Kotlin split:
Part I style foundation (formatting/tooling, source layout, naming,
documentation/YARD), Part II language core (objects, methods, blocks and
procs, modules and mixins, metaprogramming discipline, exceptions, strings,
collections, pattern matching, Struct/Data, comparable/enumerable), Part III
Rails (ActiveRecord, migrations, controllers, views, routes, jobs, mailers,
service objects, testing), Part IV tooling (`.rubocop.yml`).

---

## 6. Starting point: Python

### Settled

| Item | Value |
|---|---|
| Skill name | `best-practice-python` |
| Language floor | **Python 3.12** (installing 3.12.10 via pyenv) |
| Primary source | Google pyguide, <https://google.github.io/styleguide/pyguide.html> (503 anchors harvested) |
| Framework layer | **FastAPI + Pydantic v2** |
| Linter/formatter | **Ruff, replacing pylint entirely** — local 0.13.1, latest 0.16.0, 929 rules across 60 families |
| Env management | **uv** (0.10.9) for all projects |
| Local interpreter | **3.12.10**, now the pyenv global default (verified) |
| Style | **Single quotes, 2-space indent** — a deliberate house override |
| Ship config | `ruff.toml` at repo root, based on the user's canonical file |

**Retracted objection.** Mid-session I argued the floor should drop to 3.11
because every pyenv venv on the machine is 3.11.11. The user corrected me:
they use `uv` for project environments, and the pyenv listing reflects nothing
about current work. **The 3.12 floor stands.** I was reading stale evidence.

### The user's canonical `ruff.toml`

Saved verbatim at `docs/reference-data/` is *not* where it lives — it is in
the session scratchpad only. **Re-request it from the user or reconstruct
from this summary.** Key settings:

```toml
line-length = 88          # Black default, vs pyguide §3.2's 80
indent-width = 2          # house override, vs PEP 8 / pyguide §3.4's 4
target-version = "py311"  # NEEDS CHANGING to py312

[lint]
select = ["E4", "E7", "E9", "F"]   # Ruff's minimal default
ignore = []
fixable = ["ALL"]
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[format]
quote-style = "single"    # house override, vs Ruff's double default
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
docstring-code-format = true
docstring-code-line-length = "dynamic"
```

### Three tensions to resolve before authoring

1. **`target-version = "py311"` contradicts the 3.12 floor.** PEP 695 `type`
   alias and generic-parameter syntax are 3.12-only, and Ruff's `UP040` will
   not fire at `py311`. A 3.12-floored skill teaching PEP 695 while the linter
   is pinned to 3.11 is incoherent. **Change to `py312`.**

2. **`select = ["E4","E7","E9","F"]` reaches ~100 of 929 rules.** It enforces
   almost nothing pyguide cares about, which would force nearly every Python
   rule to be labeled **Suggestion** and collapse the linter-anchoring that
   makes the Go and Java skills actionable. Families that map directly onto
   pyguide sections:

   | Family | Count | Maps to |
   |---|---:|---|
   | `D` | 46 | pyguide §3.8 docstrings — set `[lint.pydocstyle] convention = "google"` |
   | `N` | 16 | pyguide §3.16 naming |
   | `I` | 2 | pyguide §3.13 imports formatting |
   | `ANN` | 11 | pyguide §2.22 / §3.19 type annotations |
   | `UP` | 47 | modern idiom enforcement |
   | `B` | 41 | bugbear, programming practices |
   | `PL*` | 113 | the literal pylint replacement the user asked for |
   | `S` | 73 | bandit security |
   | `ASYNC` | 14 | **FastAPI async correctness** |
   | `PT` | 31 | pytest conventions |
   | `DTZ` | 10 | timezone-aware datetimes |
   | `RUF`, `SIM`, `RET`, `PTH`, `TC`, `TRY`, `C4`, `ARG` | ~180 | general |

   Recommend proposing an expanded `select` and getting explicit sign-off,
   since it will surface findings in existing code.

3. **`line-length = 88` vs pyguide §3.2's 80, and `indent-width = 2` vs
   §3.4's 4.** Both are legitimate house overrides. They must be documented in
   the formatting chapter as *overrides of the cited upstream*, never
   presented as what Google says. Ruby has no equivalent problem.

Also note: local ruff is 0.13.1, latest is 0.16.0. Pin the config to whichever
version the project actually runs; rule codes are added between minors.

### Suggested chapter shape

Roughly 40-45 chapters: Part I style foundation (formatting/Ruff tooling,
source layout, naming, docstrings), Part II language core (types and
annotations, functions, classes, dataclasses, protocols, generics/PEP 695,
exceptions, context managers, iterators/generators, comprehensions, strings,
collections, pattern matching, enums, dates), Part III async (asyncio,
structured concurrency via TaskGroup, cancellation, async context managers,
the blocking-call trap), Part IV FastAPI + Pydantic v2 (app structure,
dependency injection, request/response models, validation, settings, error
handling, background tasks, testing), Part V tooling (`ruff.toml`, mypy or
pyright, pytest).

---

## 7. Recommended first moves next session

1. Read this file and `docs/reference-data/README.md`.
2. Re-harvest anchors if more than a few days have passed
   (`docs/reference-data/README.md` has the commands). Upstream guides move.
3. Resolve the Ruby open questions (§5) and the Python tensions (§6) with the
   user **before** authoring anything. Both sets change what gets written.
4. Author Ruby, then Python, using the same three-stage method: fan-out
   authoring, adversarial verify per batch, then mechanical reconciliation of
   every `> Enforced by:` callout against the effective enabled rule set.
5. Write `README-ruby.md` and `README-python.md`, and update the root
   `README.md` skill table, install tree, `AGENTS.md` snippet, invocation
   examples, and root-config list for each.

## 8. Verification commands

```bash
python3 -c "import xml.dom.minidom as m; d=m.parse('config/checkstyle/checkstyle.xml'); print('modules:', len(d.getElementsByTagName('module')))"
```

```bash
grep -cE '^  [A-Z][A-Za-z0-9]+:$' config/detekt/detekt.yml
```

The `python3 -c "import yaml; ..."` form is more precise but `pyyaml` is not
installed on the current pyenv default (3.12.10 is a fresh interpreter).
`uv run --with pyyaml python -c ...` works if you want the parsed count.

```bash
for s in best-practice-java best-practice-kotlin; do echo "$s: $(ls $s/references/*.md | wc -l) chapters, $(cat $s/references/*.md | grep -cE '^## [0-9]+\.[0-9]+ ') rules"; done
```
