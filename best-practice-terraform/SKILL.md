---
name: best-practice-terraform
description: Comprehensive Terraform best practices grounded in HashiCorp's Terraform language Style Guide - formatting (terraform fmt), validation, file layout, naming, variables/outputs/locals, providers and aliases, count/for_each, version pinning, modules, state hygiene, environments/workflow, terraform test, and TFLint. Load when writing or reviewing any .tf / .tfvars / .tftest.hcl file, when the user mentions Terraform, HCL, terraform fmt, TFLint, modules, or state, or when the user asks "is this idiomatic Terraform?".
---

# best-practice-terraform

This skill codifies Terraform configuration language best practices. It is
modeled on the depth and structure of the sibling language skills in this
repo - numbered rules per chapter, `> Why?` rationale, and `# bad` /
`# good` examples for every rule.

The rules trace to these upstream sources, in this precedence order:

1. **[Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)** -
   the normative HashiCorp guide for
   [code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting),
   [file names](https://developer.hashicorp.com/terraform/language/style#file-names),
   [naming](https://developer.hashicorp.com/terraform/language/style#resource-naming),
   [variables](https://developer.hashicorp.com/terraform/language/style#variables) /
   [outputs](https://developer.hashicorp.com/terraform/language/style#outputs) /
   [locals](https://developer.hashicorp.com/terraform/language/style#local-values),
   [providers](https://developer.hashicorp.com/terraform/language/style#provider-aliasing),
   [count/for_each](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count),
   [version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning),
   [modules](https://developer.hashicorp.com/terraform/language/style#module-structure),
   [state/secrets](https://developer.hashicorp.com/terraform/language/style#secrets-management),
   and [workflow](https://developer.hashicorp.com/terraform/language/style#workflow-style).
2. **Closely related HashiCorp language docs** - standard module structure,
   variables/outputs/locals, meta-arguments, providers, settings, and
   `terraform test` - when the style guide points at them.
3. **TFLint**
   ([terraform-linters/tflint](https://github.com/terraform-linters/tflint)
   and
   [ruleset-terraform](https://github.com/terraform-linters/tflint-ruleset-terraform)) -
   the linter the style guide itself names. This skill ships
   [`.tflint.hcl`](../.tflint.hcl) at the repo root. Only real
   ruleset-terraform rule IDs appear in `> Enforced by:` callouts.

All formatting concerns that `terraform fmt` owns are delegated to it.
Chapter 1 documents the tool chain; later chapters assume formatted HCL.

**Indentation is two spaces.** That is the HashiCorp style-guide rule.
Every sample in this skill uses two-space HCL.

Every rule that maps to `terraform fmt`, `terraform validate`,
`terraform test`, or an enabled TFLint terraform-ruleset rule carries an
**`> Enforced by: <tool-or-rule>`** callout. Rules no tool in that set can
verify are labeled **Suggestion**, not **Violation**. Broader scanners
(Checkov, Trivy, tfsec) are mentioned honestly as optional org policy tools
and are never cited as enforcement unless the target repo actually configures
them.

## When to use

- Writing new `.tf` / `.tfvars` / `.tftest.hcl` files or reviewing existing ones.
- Answering "is this idiomatic Terraform?" against the HashiCorp style guide.
- Structuring roots and modules (`terraform.tf`, `providers.tf`, `modules/`).
- Pinning Terraform, provider, and module versions.
- Setting up fmt / validate / TFLint in CI.
- Reviewing state hygiene, `.gitignore`, and secret handling at the style level.

## Scope

- Configuration language style: formatting, comments, file layout, naming.
- Resource/data ordering and meta-argument layout.
- Variables, outputs, locals.
- Providers, aliases, and `required_providers`.
- `count` / `for_each` discipline.
- Version pinning and lockfiles.
- Module and repository structure (including local `./modules/<name>`).
- State hygiene, `.gitignore`, state sharing, and secrets *as the style guide
  frames them*.
- Environments, branching, `terraform test`, and policy placement at overview
  depth.
- TFLint terraform-ruleset alignment.

## Non-goals

- **Cloud provider design encyclopedias.** AWS/GCP/Azure resource-by-resource
  hardening belongs in provider-specific skills or Checkov/Trivy policy packs
  your org owns.
- **Full platform security audits.** Chapter 13 covers style-guide state and
  secrets hygiene, not CIS benchmarks.
- **HCP Terraform product administration** beyond what the style guide says
  about workspaces, speculative plans, `tfe_outputs`, and policy repos.
- **Re-litigating `terraform fmt`.** Accept its output.

---

## Chapters

Each chapter is a self-contained reference file with numbered rules,
`> Why?` rationale, `# bad` / `# good` HCL, and honest `> Enforced by:`
callouts. Files live under `references/`.

### Part I - Style foundation

| #   | Chapter                  | File                                                                                         |
| --- | ------------------------ | -------------------------------------------------------------------------------------------- |
| 1   | Formatting & Tooling     | [`references/01-formatting-and-tooling.md`](references/01-formatting-and-tooling.md)         |
| 2   | File Names & Layout      | [`references/02-file-names-and-layout.md`](references/02-file-names-and-layout.md)           |
| 3   | Comments                 | [`references/03-comments.md`](references/03-comments.md)                                     |
| 4   | Naming                   | [`references/04-naming.md`](references/04-naming.md)                                         |
| 5   | Resource Order & Blocks  | [`references/05-resource-order-and-blocks.md`](references/05-resource-order-and-blocks.md)   |

### Part II - Language objects

| #   | Chapter                 | File                                                                                       |
| --- | ----------------------- | ------------------------------------------------------------------------------------------ |
| 6   | Variables               | [`references/06-variables.md`](references/06-variables.md)                                 |
| 7   | Outputs                 | [`references/07-outputs.md`](references/07-outputs.md)                                     |
| 8   | Local Values            | [`references/08-local-values.md`](references/08-local-values.md)                           |
| 9   | Providers & Aliasing    | [`references/09-providers-and-aliasing.md`](references/09-providers-and-aliasing.md)       |
| 10  | Count & for_each        | [`references/10-count-and-for-each.md`](references/10-count-and-for-each.md)               |

### Part III - Modules, state, workflow

| #   | Chapter                          | File                                                                                                       |
| --- | -------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 11  | Version Pinning                  | [`references/11-version-pinning.md`](references/11-version-pinning.md)                                     |
| 12  | Modules & Repository Structure   | [`references/12-modules-and-repository-structure.md`](references/12-modules-and-repository-structure.md)   |
| 13  | State Hygiene & Secrets          | [`references/13-state-hygiene-and-secrets.md`](references/13-state-hygiene-and-secrets.md)                 |
| 14  | Environments, Workflow & Testing | [`references/14-environments-and-workflow.md`](references/14-environments-and-workflow.md)                 |

### Part IV - Tooling

| #   | Chapter                    | File                                                                                             |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------ |
| 15  | Linting & Static Analysis  | [`references/15-linting-and-static-analysis.md`](references/15-linting-and-static-analysis.md)   |

## How to use this skill

1. **Automatic loading.** The frontmatter `description` tells the agent when
   to load this skill. This index is what it reads first.
2. **Targeted reads.** For one area (say, variables or modules), open only
   that chapter under `references/`.
3. **Full review.** For a comprehensive audit, walk every chapter.
4. **Tooling.** Run `terraform fmt`, `terraform validate`, and TFLint
   against the shipped [`.tflint.hcl`](../.tflint.hcl) before treating a
   change as finished. See chapter 15.
5. **Tool config.** Root [`.tflint.hcl`](../.tflint.hcl) is authoritative
   for the terraform ruleset (`preset = "recommended"` plus documented
   variables/outputs, snake_case naming, `#` comments, and standard module
   structure). It does not ship AWS/GCP rulesets or Checkov/Trivy/tfsec.

## Self-check

Before treating Terraform code as finished, verify:

- `terraform fmt -check -recursive` is clean (chapter 1).
- `terraform validate` passes (chapter 1).
- Variables have `type` + `description`; outputs have `description` (chapters 6-7).
- Resource names are snake_case nouns without repeating the type (chapter 4).
- Providers live in `providers.tf` with a default configuration (chapters 2, 9).
- Registry/git modules are version-pinned; `.terraform.lock.hcl` is committed
  (chapter 11).
- State, `.terraform/`, plan files, and secret `.tfvars` are gitignored
  (chapter 13).
- `tflint --format compact` is clean against root `.tflint.hcl` (chapter 15).
