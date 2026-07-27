<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 11. Version Pinning

[Version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning) prevents surprise upgrades.
Pin providers in `required_providers`, set `required_version` for the Terraform
CLI, pin registry modules with `version`, and commit
`.terraform.lock.hcl`. Language reference: [Terraform settings](https://developer.hashicorp.com/terraform/language/settings).

## 11.1 Set `required_version` in the root `terraform` block.

> Why? Recommended in [Version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning).
> **Violation.**
>
> Enforced by: terraform_required_version.

```hcl
# bad
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

# good
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.34.0"
    }
  }
}
```

## 11.2 Pin provider versions in `required_providers`.

> Why? [Version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning) example pins exact provider versions.
> **Violation.**
>
> Enforced by: terraform_required_providers.

```hcl
# bad
aws = {
  source = "hashicorp/aws"
}

# good
aws = {
  source  = "hashicorp/aws"
  version = "5.34.0"
}
```

## 11.3 Pin registry module versions with the `version` argument.

> Why? Shown under [Version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning). Local modules ignore `version`.
> **Violation.**
>
> Enforced by: terraform_module_pinned_source.

```hcl
# bad
module "vault_starter" {
  source = "hashicorp/vault-starter/aws"
}

# good
module "vault_starter" {
  source  = "hashicorp/vault-starter/aws"
  version = "1.0.0"
}
```

## 11.4 Pin git module sources with a `?ref=` version tag.

> Why? Unpinned branches move under you. Prefer tags over `main`.
> **Violation.**
>
> Enforced by: terraform_module_pinned_source.

```hcl
# bad
module "network" {
  source = "git::https://github.com/example/terraform-modules.git//network"
}

# good
module "network" {
  source = "git::https://github.com/example/terraform-modules.git//network?ref=v1.4.0"
}
```

## 11.5 Commit `.terraform.lock.hcl` for roots that providers are installed into.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore) says always commit the dependency lock file.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - lockfile gitignored

# good - .terraform.lock.hcl tracked in git
```

## 11.6 Prefer pessimistic constraints (`~>`) only when you knowingly accept minor updates.

> Why? Exact pins maximize reproducibility; `~>` is a conscious trade for patches/minors.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - floating latest
version = ">= 0"

# good - exact or deliberate pessimistic constraint
version = "5.34.0"
# or
version = "~> 5.34"
```

## 11.7 Do not leave `required_providers` empty when the module uses providers.

> Why? Implicit legacy providers hide source addresses and break newer Terraform.
> **Violation.**
>
> Enforced by: terraform_required_providers.

```hcl
# bad - provider used with no required_providers entry

# good - every provider sourced and versioned
```

## 11.8 Upgrade providers deliberately with `terraform init -upgrade` and reviewed plans.

> Why? Surprise upgrades in CI without a human-reviewed plan are incidents waiting to happen.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - CI always runs init -upgrade on main

# good - upgrade on a branch, review plan, merge lockfile
```

## 11.9 Keep module `version` constraints as tight as your promotion process allows.

> Why? Pin major.minor for stability ([Version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning)).
> **Violation.**
>
> Enforced by: terraform_module_version.

```hcl
# bad
version = ">= 1.0.0"

# good
version = "1.0.0"
```

## 11.10 Record the minimum Terraform version that matches language features you use.

> Why? Using `check` blocks or newer test features while allowing ancient `required_version` floors fails operators unpredictably.
> **Violation.**
>
> Enforced by: terraform_required_version.

```hcl
# bad - uses terraform test / modern features with required_version = ">= 0.12"

# good - required_version floor matches features actually used
```
