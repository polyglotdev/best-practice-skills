<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 15. Linting & Static Analysis

Terraform has no built-in linter. The style guide recommends
[TFLint](https://github.com/terraform-linters/tflint) under
[Linting and static code analysis](https://developer.hashicorp.com/terraform/language/style#linting-and-static-code-analysis).
This skill treats TFLint's `terraform` ruleset as the honest mechanical layer
alongside `terraform fmt` and `terraform validate`. Broader IaC scanners such
as Checkov or Trivy are useful organization policy tools when *you* configure
them; this repo does not ship their configs, so this chapter does not pretend
they enforce rules here.

## 15.1 Run TFLint in CI with the Terraform ruleset enabled.

> Why? HashiCorp points at TFLint explicitly ([Linting and static code analysis](https://developer.hashicorp.com/terraform/language/style#linting-and-static-code-analysis)).
> **Violation.**
>
> Enforced by: tflint.

```hcl
# bad - only fmt in CI

# good - fmt -check, validate, tflint --format compact
```

## 15.2 Enable `terraform_documented_variables` and `terraform_typed_variables`.

> Why? These map directly to the style guide variable requirements.
> **Violation.**
>
> Enforced by: terraform_documented_variables.

```hcl
# bad - variables without type/description surviving review

# good - TFLint fails the build on missing type/description
```

## 15.3 Enable `terraform_documented_outputs`.

> Why? Outputs need descriptions per the style guide.
> **Violation.**
>
> Enforced by: terraform_documented_outputs.

```hcl
# bad - bare output blocks

# good - documented outputs enforced in CI
```

## 15.4 Enable `terraform_module_pinned_source` / `terraform_module_version`.

> Why? Unpinned modules violate [version pinning]({STYLE}#version-pinning).
> **Violation.**
>
> Enforced by: terraform_module_pinned_source.

```hcl
# bad - registry module with no version

# good - version pinned; TFLint guards regressions
```

## 15.5 Enable `terraform_required_version` and `terraform_required_providers`.

> Why? Roots without constraints drift across laptops and CI images.
> **Violation.**
>
> Enforced by: terraform_required_version.

```hcl
# bad - implicit providers, no required_version

# good - constraints present; TFLint enforces
```

## 15.6 Enable `terraform_naming_convention` aligned to snake_case nouns.

> Why? Matches [resource naming]({STYLE}#resource-naming).
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad - WebAPI-style names

# good - snake_case names; TFLint naming rule on
```

## 15.7 Enable `terraform_unused_declarations` to keep roots lean.

> Why? Dead variables and locals accumulate quickly in shared modules.
> **Violation.**
>
> Enforced by: terraform_unused_declarations.

```hcl
# bad - unused variable left "for later"

# good - unused declarations fail CI
```

## 15.8 Enable `terraform_comment_syntax` so `#` stays idiomatic.

> Why? Aligns with [Comments](https://developer.hashicorp.com/terraform/language/style#comments).
> **Violation.**
>
> Enforced by: terraform_comment_syntax.

```hcl
# bad - // comments creeping back in

# good - TFLint rejects non-idiomatic comment syntax when configured
```

## 15.9 Treat Checkov/Trivy/tfsec as optional org policy layers, not as this skill's defaults.

> Why? The HashiCorp style guide names TFLint. Other scanners are valuable for cloud misconfiguration policy when your org pins and owns their configs. Do not cite them as `Enforced by` unless that config actually exists in the target repo.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - claiming "Enforced by: checkov" with no checkov config in the repo

# good - document org-required scanners in the service repo; keep this skill honest
```

## 15.10 Keep the CI order cheap-to-expensive: fmt check, validate, tflint, then plan/tests.

> Why? Fail fast on formatting before spending minutes on providers and plans.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - plan first, fmt last

# good - fmt -check -> validate -> tflint -> test/plan
```
