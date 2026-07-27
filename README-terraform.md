# best-practice-terraform

An exhaustive **Agent Skill** for writing and reviewing Terraform
configuration language, grounded in HashiCorp's Style Guide.

**148 numbered rules across 15 chapters, 3,079 lines.** Every rule is
justified with a `> Why?`, shown with `# bad` / `# good` HCL, and where a
real tool catches it, labeled `> Enforced by: <tool-or-tflint-rule>`.

## Upstream sources, in precedence order

1. **[Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)** -
   normative for
   [formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting),
   [file names](https://developer.hashicorp.com/terraform/language/style#file-names),
   [naming](https://developer.hashicorp.com/terraform/language/style#resource-naming),
   variables / outputs / locals, providers, `count` / `for_each`, version
   pinning, modules, state/secrets, and workflow.
2. **Closely related HashiCorp language docs** (standard module structure,
   values, meta-arguments, providers, settings, tests) when the style guide
   points at them.
3. **TFLint** + **tflint-ruleset-terraform** - the linter the style guide
   names. Config ships at repo-root [`.tflint.hcl`](.tflint.hcl). Only real
   rule IDs appear in enforcement callouts.

Anchors were harvested from the upstream style guide headings into
[`docs/reference-data/terraform-style-anchors.txt`](docs/reference-data/terraform-style-anchors.txt).
TFLint terraform-ruleset rule names live in
[`docs/reference-data/tflint-terraform-rules.txt`](docs/reference-data/tflint-terraform-rules.txt).

## Style defaults

| Setting | Value | Notes |
| --- | --- | --- |
| Indent | 2-space | HashiCorp Style Guide + `terraform fmt` |
| Comments | `#` only (idiomatic) | `//` and `/* */` are legacy HCL |
| Formatter | `terraform fmt` | Owns a subset of layout rules |
| Validate | `terraform validate` | Syntax + internal consistency |
| Linter | TFLint via [`.tflint.hcl`](.tflint.hcl) | `recommended` preset + chapter 15 extras |

## Tooling (honest enforcement)

| Tool | Role in this skill |
| --- | --- |
| `terraform fmt` | Formatter; `> Enforced by: terraform fmt` |
| `terraform validate` | Consistency checks |
| `terraform test` | Module tests (chapter 14) |
| TFLint + [`.tflint.hcl`](.tflint.hcl) | Documented variables/outputs, pins, naming, `#` comments, standard module structure |
| Checkov / Trivy / tfsec | Optional org scanners; **not** claimed as enforcement unless the target repo configures them |

## Shipped `.tflint.hcl`

Root [`.tflint.hcl`](.tflint.hcl) enables the bundled `terraform` plugin with
`preset = "recommended"`, then explicitly turns on the style-guide rules that
are off in that preset: `terraform_documented_variables`,
`terraform_documented_outputs`, `terraform_naming_convention` (`snake_case`),
`terraform_comment_syntax`, and `terraform_standard_module_structure`. Chapter
15 rules already in `recommended` are restated in the file for discoverability.
No provider rulesets and no Checkov/Trivy/tfsec.

## Chapters

### Part I - Style foundation

| # | Chapter | Rules | Lines |
| --- | --------- | ------: | ------: |
| 1 | Formatting & Tooling | 10 | 274 |
| 2 | File Names & Layout | 10 | 250 |
| 3 | Comments | 8 | 185 |
| 4 | Naming | 10 | 219 |
| 5 | Resource Order & Blocks | 10 | 276 |

### Part II - Language objects

| # | Chapter | Rules | Lines |
| --- | --------- | ------: | ------: |
| 6 | Variables | 10 | 240 |
| 7 | Outputs | 10 | 211 |
| 8 | Local Values | 10 | 230 |
| 9 | Providers & Aliasing | 10 | 233 |
| 10 | Count & for_each | 10 | 197 |

### Part III - Modules, state, workflow

| # | Chapter | Rules | Lines |
| --- | --------- | ------: | ------: |
| 11 | Version Pinning | 10 | 182 |
| 12 | Modules & Repository Structure | 10 | 153 |
| 13 | State Hygiene & Secrets | 10 | 142 |
| 14 | Environments, Workflow & Testing | 10 | 144 |

### Part IV - Tooling

| # | Chapter | Rules | Lines |
| --- | --------- | ------: | ------: |
| 15 | Linting & Static Analysis | 10 | 143 |

## Regenerating chapters

Reference chapters are generated from structured rules:

```bash
python3 scripts/build_terraform_skill.py
python3 -m unittest tests.test_terraform_skill -v
```

## Install

```bash
npx skills add <your-github-user>/best-practice-skills --skill best-practice-terraform -g -y
```

Or copy `best-practice-terraform/` into `.claude/skills/best-practice-terraform/`
and drop [`.tflint.hcl`](.tflint.hcl) at the target repo root.
