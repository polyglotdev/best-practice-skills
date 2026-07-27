# Reference data

Harvested ground truth for the upstream style guides each skill cites.

## Why this exists

Broken style-guide anchors were the **single largest defect class** when
authoring `best-practice-java`: 22 distinct bad anchors across the corpus,
plus 60 fabricated citations caught by the verify pass.

The root cause is worth remembering. Asking a summarizing model "what are the
section anchors on this page?" produces anchors that look right and are wrong,
because the model infers them from the section *titles* rather than reading
them off the page. Google's Java guide, for example, titles a section
"Exception: self-explanatory members" and the plausible-looking anchor
`#s7.3.1-javadoc-self-explanatory` does not exist; the real one is
`#s7.3.1-javadoc-exception-self-explanatory`.

These files are extracted from the **raw HTML** of each guide. Authoring
agents are instructed to use only anchors present here, and verifiers check
every link against them.

## Files

| File | Source | Anchors |
|---|---|---|
| `java-styleguide-anchors.txt` | <https://google.github.io/styleguide/javaguide.html> | 98 |
| `android-kotlin-anchors.txt` | <https://developer.android.com/kotlin/style-guide> | 50 |
| `kotlin-conventions-anchors.txt` | <https://kotlinlang.org/docs/coding-conventions.html> | 74 |
| `ruby-style-anchors.txt` | <https://rubystyle.guide/> | 359 |
| `rails-style-anchors.txt` | <https://github.com/rubocop/rails-style-guide> (HTML mirror <https://rails.rubystyle.guide/>) | 150 |
| `rubocop-cops.txt` | `rubocop --show-cops` under Ruby 4.0.5 + plugins | 911 |
| `rubocop-effective-enabled.txt` | defaults adjusted by repo-root `.rubocop.yml` | - |
| `pyguide-anchors.txt` | <https://google.github.io/styleguide/pyguide.html> | 503 |
| `terraform-style-anchors.txt` | <https://developer.hashicorp.com/terraform/language/style> | 27 |
| `tflint-terraform-rules.txt` | terraform-linters/tflint-ruleset-terraform rule names | 16 |

Harvested 2026-07-27. Upstream guides change; re-harvest before a new
authoring run rather than trusting these indefinitely.

## Regenerating

Anchors, for any of the guides above:

```bash
curl -sSL -o page.html <GUIDE_URL>
python3 - <<'PY'
import re
s = open('page.html', encoding='utf-8', errors='replace').read()
ids = sorted(set(re.findall(r'id=["\']?([a-zA-Z0-9][a-zA-Z0-9._-]{2,70})["\'\s>]', s)))
print('\n'.join(i for i in ids if not i.startswith(('devsite', 'gc-', 'app-', 'main-'))))
PY
```

Two traps that produced silent empty results the first time:

- Some pages write **unquoted** attributes (`id=globalcoroutineusage`). A
  regex expecting `id="..."` returns zero matches and looks like proof the
  names are fabricated. The pattern above tolerates both.
- Anchor hrefs may omit the `.html` suffix (`href="bugpattern/Name"`).

**An empty result set is a broken query until proven otherwise.** Always
sanity-check the extractor against a value you already know is present.

## Tool check catalogues

Not committed here, because they are large and tied to a specific tool
version. Regenerate against the version the project actually pins:

```bash
rubocop --show-cops | grep -oE '^[A-Z][A-Za-z]+/[A-Za-z0-9]+' | sort -u
```

```bash
ruff rule --all --output-format json | python3 -c "import json,sys; print('\n'.join(sorted({r['code'] for r in json.load(sys.stdin)})))"
```

```bash
curl -sSL https://errorprone.info/bugpatterns | grep -oE 'href="bugpattern/[A-Za-z0-9_]+"' | sed 's|href="bugpattern/||; s|"||' | sort -u
```

```bash
curl -sSL https://raw.githubusercontent.com/checkstyle/checkstyle/master/src/main/resources/google_checks.xml
```

detekt rule names, per department, noting the unquoted-`id` trap:

```bash
for c in comments complexity coroutines empty-blocks exceptions naming performance potential-bugs style; do
  curl -sSL "https://detekt.dev/docs/rules/$c" \
    | grep -oE '<h3[^>]*id=[a-z0-9-]+>[^<]+</h3>' \
    | sed 's|.*>\(.*\)</h3>|\1|'
done | sort -u
```

## The reconciliation rule

Citing a check that *exists* is not the same as citing a check the shipped
configuration *enables*. Both must hold before a rule may be labeled
**Violation**. After any authoring run, diff every `> Enforced by:` name
against both the catalogue above and the enabled rule set in the shipped
config, then either enable the check or downgrade the callout to
**Suggestion**.
