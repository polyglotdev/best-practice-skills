<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 12. Modules & Repository Structure

Modules group resources provisioned together. Follow
[module structure](https://developer.hashicorp.com/terraform/language/style#module-structure), store local modules under
`./modules/<module_name>` ([local modules](https://developer.hashicorp.com/terraform/language/style#local-modules)), publish
registry modules as `terraform-<PROVIDER>-<NAME>`
([module repository names](https://developer.hashicorp.com/terraform/language/style#module-repository-names)), and prefer
separating module code from live infrastructure roots
([repository structure](https://developer.hashicorp.com/terraform/language/style#repository-structure)). Also see
[Standard Module Structure](https://developer.hashicorp.com/terraform/language/modules/develop/structure).

## 12.1 Store local child modules under `./modules/<module_name>`.

> Why? [Local modules](https://developer.hashicorp.com/terraform/language/style#local-modules).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
module "vpc" {
  source = "./vpc"
}

# good
module "vpc" {
  source = "./modules/vpc"
}
```

## 12.2 Give published module repositories the `terraform-<PROVIDER>-<NAME>` name.

> Why? [Module repository names](https://developer.hashicorp.com/terraform/language/style#module-repository-names).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - repo name: infra-helpers

# good - repo name: terraform-aws-vpc
```

## 12.3 Follow standard module file layout: main.tf, variables.tf, outputs.tf, README.

> Why? [Module structure](https://developer.hashicorp.com/terraform/language/style#module-structure) points at the standard module structure.
> **Violation.**
>
> Enforced by: terraform_standard_module_structure.

```hcl
# bad - everything in one unlabeled file with no README

# good
# modules/vpc/main.tf
# modules/vpc/variables.tf
# modules/vpc/outputs.tf
# modules/vpc/README.md
```

## 12.4 Prefer publishing shared modules to a registry over copy/pasting local clones.

> Why? [Local modules](https://developer.hashicorp.com/terraform/language/style#local-modules) recommends a registry when you can.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - five roots each with a divergent copy of modules/vpc

# good - one versioned registry module consumed by each root
```

## 12.5 Separate module source repositories from live infrastructure configuration when practical.

> Why? [Repository structure](https://developer.hashicorp.com/terraform/language/style#repository-structure).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - editing a shared module and prod root in one mixed commit with no version boundary

# good - module repo tagged v1.2.0; live root bumps the module version
```

## 12.6 If you use a monorepo, scope workspaces/roots to directories deliberately.

> Why? HashiCorp notes monorepos complicate CI and access control ([Repository structure](https://developer.hashicorp.com/terraform/language/style#repository-structure)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - one root that plans the entire company monorepo every PR

# good - workspace rooted at networking/ or app/billing/
```

## 12.7 Group module resources that must change together; do not build kitchen-sink modules.

> Why? Examples in [Module structure](https://developer.hashicorp.com/terraform/language/style#module-structure): networking stack, app stack.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - module "everything" with VPC + SaaS DNS + paging + laptops

# good - module "network" and module "application" composed at the root
```

## 12.8 Expose a narrow variable/output contract; hide internals.

> Why? Callers should not need to know every security group rule resource name.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - output every intermediate SG rule ID

# good - output vpc_id and private_subnet_ids only
```

## 12.9 Include a module README that lists inputs, outputs, and examples.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore) / workflow expectations include a README describing code, variables, and outputs.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - undocumented module directory

# good - README with purpose, example call, inputs, outputs
```

## 12.10 Do not configure backends inside reusable child modules.

> Why? Backends belong to roots/workspaces that own state.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - modules/vpc/backend.tf with a terraform backend block

# good - backend only in live roots (dev/, prod/, or workspaces)
```
