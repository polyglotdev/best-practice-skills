<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 13. State Hygiene & Secrets

State holds sensitive data. The style guide's [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore),
[state sharing](https://developer.hashicorp.com/terraform/language/style#state-sharing), and [secrets management](https://developer.hashicorp.com/terraform/language/style#secrets-management)
sections define what must never be committed, how to share data across states,
and how to keep credentials out of configuration. This chapter stays at that
language/workflow level - not a full cloud security audit.

## 13.1 Never commit `terraform.tfstate` or `terraform.tfstate.*` backups.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - state tracked in git

# good - gitignore terraform.tfstate and terraform.tfstate.*
```

## 13.2 Never commit the `.terraform` directory.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore): providers and modules are downloaded locally.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - .terraform/ committed

# good - .terraform/ ignored; lockfile committed
```

## 13.3 Never commit saved plan files from `terraform plan -out`.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - tfplan checked into the repo

# good - plan artifact stays in CI ephemeral storage
```

## 13.4 Never commit `.tfvars` files that contain secrets.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
# secrets.auto.tfvars
db_password = "hunter2"

# good - secrets from the environment, CI store, or Vault provider
```

## 13.5 Always commit Terraform code, `.terraform.lock.hcl`, `.gitignore`, and README.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore) "Always commit" list.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - lockfile ignored, README missing

# good - code + lockfile + gitignore + README tracked
```

## 13.6 Avoid sharing full state files between teams or stacks.

> Why? [State sharing](https://developer.hashicorp.com/terraform/language/style#state-sharing).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - scp terraform.tfstate to another team

# good - consume outputs via tfe_outputs or provider data sources
```

## 13.7 Prefer provider data sources (or `tfe_outputs` on HCP Terraform) over remote-state coupling when practical.

> Why? [State sharing](https://developer.hashicorp.com/terraform/language/style#state-sharing) recommends `tfe_outputs` or provider data sources instead of wholesale state sharing.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - every stack reads the entire remote state blob for one subnet ID

# good - aws_subnet data source lookup by tags, or tfe_outputs for one value
```

## 13.8 Configure remote state with encryption and locking for any shared environment.

> Why? Local state is plaintext on disk and lacks locking ([Secrets management](https://developer.hashicorp.com/terraform/language/style#secrets-management)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - local state on a shared workstation for prod

# good - remote backend with encryption and lock table / native locking
```

## 13.9 Prefer dynamic provider credentials or a secrets manager over static keys in CI.

> Why? [Secrets management](https://developer.hashicorp.com/terraform/language/style#secrets-management).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - long-lived AKIA keys in CI variables used for every plan

# good - OIDC / dynamic credentials / Vault-backed short-lived tokens
```

## 13.10 Remember `sensitive = true` does not remove values from state.

> Why? Called out under [Variables](https://developer.hashicorp.com/terraform/language/style#variables) and [Secrets management](https://developer.hashicorp.com/terraform/language/style#secrets-management).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - assuming sensitive variables never hit disk

# good - treat state as sensitive, restrict backend ACLs, rotate on exposure
```
