<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 2. File Names & Layout

The [File names](https://developer.hashicorp.com/terraform/language/style#file-names) section defines the default file
set for a root module: `backend.tf`, `main.tf`, `outputs.tf`, `providers.tf`,
`terraform.tf`, `variables.tf`, `locals.tf`, and sparingly `override.tf`. When
that set becomes hard to navigate, split resources by logical group
(`network.tf`, `storage.tf`, `compute.tf`) while keeping the standard files for
providers, versions, variables, and outputs.

## 2.1 Put `required_version` and `required_providers` in `terraform.tf`.

> Why? [File names](https://developer.hashicorp.com/terraform/language/style#file-names) assigns versioning to `terraform.tf` so operators always know where constraints live.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - versions buried in main.tf next to resources
# main.tf
terraform {
  required_version = ">= 1.7"
}

# good - terraform.tf owns version constraints
# terraform.tf
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## 2.2 Put backend configuration in `backend.tf`.

> Why? The style guide recommends a dedicated [`backend.tf`](https://developer.hashicorp.com/terraform/language/style#file-names) and notes you may use multiple `terraform` blocks to separate backend from versioning ([backend docs](https://developer.hashicorp.com/terraform/language/backend)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - backend mixed into terraform.tf with providers
terraform {
  required_version = ">= 1.7"
  backend "s3" {
    bucket = "example-state"
    key    = "app/terraform.tfstate"
    region = "us-east-1"
  }
}

# good - backend.tf is the only place for backend config
# backend.tf
terraform {
  backend "s3" {}
}
```

## 2.3 Put provider blocks in `providers.tf`.

> Why? [File names](https://developer.hashicorp.com/terraform/language/style#file-names) and [Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing) keep all provider configuration in one file.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - provider block at the top of main.tf
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# good - providers.tf
provider "aws" {
  region = var.aws_region
}
```

## 2.4 Keep variables in `variables.tf` in alphabetical order.

> Why? [File names](https://developer.hashicorp.com/terraform/language/style#file-names) says `variables.tf` contains all variable blocks alphabetically so reviewers can scan the interface.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - variables scattered across files in call order
# network.tf
variable "vpc_cidr" { type = string }
# compute.tf
variable "instance_type" { type = string }

# good - variables.tf, alphabetical
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web tier"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}
```

## 2.5 Keep outputs in `outputs.tf` in alphabetical order.

> Why? Same convention as variables under [File names](https://developer.hashicorp.com/terraform/language/style#file-names).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - outputs declared next to each resource
output "vpc_id" {
  value = aws_vpc.main.id
}

resource "aws_subnet" "private" {
  # ...
}

output "subnet_id" {
  value = aws_subnet.private.id
}

# good - outputs.tf alphabetical
output "subnet_id" {
  description = "Private subnet ID"
  value       = aws_subnet.private.id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}
```

## 2.6 Define shared locals in `locals.tf`; file-local locals may sit at the top of that file.

> Why? [Local values](https://developer.hashicorp.com/terraform/language/style#local-values) allows `locals.tf` for cross-file locals, or the top of a single file when the local is private to it.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - same local redefined in multiple files
# network.tf
locals { name_prefix = "${var.project}-${var.environment}" }
# compute.tf
locals { name_prefix = "${var.project}-${var.environment}" }

# good - locals.tf once
locals {
  name_prefix = "${var.project}-${var.environment}"
}
```

## 2.7 Start with `main.tf` for resources; split by logical group when navigation suffers.

> Why? [File names](https://developer.hashicorp.com/terraform/language/style#file-names) starts with `main.tf`, then permits `network.tf` / `storage.tf` / `compute.tf` when size demands it. It must stay obvious where a resource lives.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - 800-line main.tf mixing VPC, RDS, IAM, and DNS with no split

# good - clear homes
# network.tf  - VPC, subnets, routes
# data.tf     - data sources for this stack
# compute.tf  - instances / ASG
# main.tf     - only if the root stays small
```

## 2.8 Use `override.tf` / `*_override.tf` sparingly and comment the original resource.

> Why? Override files load last and make reasoning harder ([File names](https://developer.hashicorp.com/terraform/language/style#file-names)). Prefer an explicit variable or local.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - silent override with no pointer at the source resource
# override.tf
resource "aws_instance" "web" {
  instance_type = "m5.large"
}

# good - avoid overrides; parameterize instead
variable "web_instance_type" {
  type        = string
  description = "Instance type for the web tier"
  default     = "t3.micro"
}

resource "aws_instance" "web" {
  instance_type = var.web_instance_type
}
```

## 2.9 Do not put provider blocks inside reusable child modules.

> Why? Provider configuration belongs in the root `providers.tf`. Child modules declare `required_providers` in their own `terraform` block and inherit configuration from the caller ([providers](https://developer.hashicorp.com/terraform/language/providers/configuration)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - provider inside modules/vpc/main.tf
provider "aws" {
  region = "us-east-1"
}

# good - module only declares required_providers
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

## 2.10 Keep `.tfvars` for non-secret values next to the root; never commit secret `.tfvars`.

> Why? [.gitignore](https://developer.hashicorp.com/terraform/language/style#gitignore) forbids committing sensitive `.tfvars`. Non-secret defaults may live in committed `terraform.tfvars` or `*.auto.tfvars` when your team agrees.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - secrets.tfvars committed
db_password = "hunter2"

# good - non-secret tfvars committed; secrets via env / CI / Vault
# terraform.tfvars
environment = "dev"
instance_type = "t3.micro"
```
