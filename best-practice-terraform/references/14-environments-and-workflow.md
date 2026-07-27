<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 14. Environments, Workflow & Testing

[Workflow style](https://developer.hashicorp.com/terraform/language/style#workflow-style) covers branching, multiple
environments, testing, and policy. Prefer GitHub flow
([branching strategy](https://developer.hashicorp.com/terraform/language/style#branching-strategy)), keep `main` as the source
of truth, isolate environments via workspaces or directories
([multiple environments](https://developer.hashicorp.com/terraform/language/style#multiple-environments)), write
[`terraform test`](https://developer.hashicorp.com/terraform/language/tests) for modules
([integration and unit testing](https://developer.hashicorp.com/terraform/language/style#integration-and-unit-testing)), and
store policies separately when using HCP policy enforcement
([Policy](https://developer.hashicorp.com/terraform/language/style#policy)).

## 14.1 Use short-lived branches and pull requests (GitHub flow).

> Why? [Branching strategy](https://developer.hashicorp.com/terraform/language/style#branching-strategy).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - committing straight to main for production changes

# good - feature branch, PR, review, merge, delete branch
```

## 14.2 Treat `main` as the source of truth for all environments.

> Why? [Multiple environments](https://developer.hashicorp.com/terraform/language/style#multiple-environments).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - long-lived prod branch that diverges from main

# good - main defines config; workspaces/dirs select env parameters
```

## 14.3 Isolate environments with separate workspaces (HCP) or directories with separate state.

> Why? [Multiple environments](https://developer.hashicorp.com/terraform/language/style#multiple-environments).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - one state file, switched by a lone var.environment, shared by all envs

# good - prod/ and dev/ roots (or prod-* workspaces) each with own state
```

## 14.4 Split large systems across multiple state files / workspaces by blast radius.

> Why? Recommended for larger codebases in [Multiple environments](https://developer.hashicorp.com/terraform/language/style#multiple-environments).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - one state containing network + databases + every app

# good - networking, database, and compute states composed via outputs/data
```

## 14.5 Run speculative plans on pull requests before merge.

> Why? HCP Terraform speculative plans are called out under [Branching strategy](https://developer.hashicorp.com/terraform/language/style#branching-strategy); Community Edition CI should `plan` on PRs without auto-apply.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - apply from the PR branch without a reviewed plan

# good - plan on PR, apply only from main after merge
```

## 14.6 Write `terraform test` coverage for reusable modules.

> Why? [Integration and unit testing](https://developer.hashicorp.com/terraform/language/style#integration-and-unit-testing).
> **Violation.**
>
> Enforced by: terraform test.

```hcl
# bad - shared module with zero tests

# good - tests/*.tftest.hcl exercising the module contract
```

## 14.7 Do not confuse `terraform test` with variable validation / checks alone.

> Why? Tests validate module logic; validation/checks verify deployed assumptions ([Integration and unit testing](https://developer.hashicorp.com/terraform/language/style#integration-and-unit-testing)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - "we have validation blocks, so we do not need tests"

# good - validation for inputs, tests for module behavior, checks for runtime
```

## 14.8 Store Sentinel/OPA-style policies in a separate VCS repository from Terraform code.

> Why? [Policy](https://developer.hashicorp.com/terraform/language/style#policy).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - ad-hoc policy files mixed into every app root without ownership

# good - dedicated policy repo enforced by HCP Terraform
```

## 14.9 Never auto-apply from unreviewed pull requests.

> Why? Plans on PRs are speculative. Apply belongs to the protected trunk pipeline.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - CI apply on every PR sync

# good - plan on PR; apply on main with approvals
```

## 14.10 Keep environment differences in tfvars / workspace variables, not forked module copies.

> Why? Divergent copies of the same module per environment is how drift wins.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - modules/vpc-dev and modules/vpc-prod as near-duplicates

# good - one module; dev.tfvars / prod.tfvars (or workspace vars) supply deltas
```
