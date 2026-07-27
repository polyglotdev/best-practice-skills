<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 9. Providers & Aliasing

[Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing) covers default and aliased
provider configurations. Always include a default provider configuration, define
providers in `providers.tf`, put the default first, and set `alias` as the first
argument of non-default blocks. Select aliases with the resource `provider`
meta-argument or the module `providers` map. Language reference:
[Providers](https://developer.hashicorp.com/terraform/language/providers/configuration).

## 9.1 Always include a default (unaliased) provider configuration.

> Why? Required by [Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing) and the code-style summary.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - only aliased providers
provider "aws" {
  alias  = "east"
  region = "us-east-1"
}

# good - default first
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "west"
  region = "us-west-2"
}
```

## 9.2 Define all provider blocks in `providers.tf`.

> Why? [Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing) / [File names](https://developer.hashicorp.com/terraform/language/style#file-names).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - provider next to resources in main.tf
provider "aws" {
  region = var.aws_region
}

# good - providers.tf only
provider "aws" {
  region = var.aws_region
}
```

## 9.3 For non-default providers, set `alias` as the first parameter.

> Why? From [Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
provider "aws" {
  region = "us-west-2"
  alias  = "west"
}

# good
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}
```

## 9.4 Select an aliased provider explicitly on resources that need it.

> Why? Shown in [Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - unclear which provider region applies
resource "aws_instance" "failover" {
  ami = "ami-west"
}

# good
resource "aws_instance" "failover" {
  provider = aws.west

  ami = "ami-west"
}
```

## 9.5 Pass providers into modules with the `providers` meta-argument map.

> Why? Module example in [Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - hoping child module somehow "knows" about aws.west

# good
module "vpc_west" {
  source = "./modules/vpc"

  providers = {
    aws = aws.west
  }
}
```

## 9.6 Do not hardcode long-lived static credentials in provider blocks.

> Why? [Secrets management](https://developer.hashicorp.com/terraform/language/style#secrets-management) prefers environment variables, dynamic credentials, or a secrets manager.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIA..."
  secret_key = "..."
}

# good - provider relies on the environment / SSO / IRSA
provider "aws" {
  region = var.aws_region
}
```

## 9.7 Declare every provider in `required_providers` with source and version.

> Why? [Version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning) and [settings](https://developer.hashicorp.com/terraform/language/settings).
> **Violation.**
>
> Enforced by: terraform_required_providers.

```hcl
# bad
terraform {
  required_version = ">= 1.7"
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

## 9.8 Prefer provider `default_tags` (when supported) over repeating identical tag maps.

> Why? Reduces drift between resources and keeps identity metadata consistent.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - tags copy/pasted on every resource

# good
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

## 9.9 Limit the number of aliases to real operational boundaries (regions, accounts).

> Why? Each alias expands the mental graph. Do not create aliases for stylistic grouping inside one region.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - alias per microservice in one region
provider "aws" {
  alias  = "payments"
  region = "us-east-1"
}

# good - alias per region or account
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}
```

## 9.10 Keep child modules free of `provider` blocks; only declare `required_providers`.

> Why? Reusable modules must inherit configuration from the root.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - modules/vpc/providers.tf
provider "aws" {
  region = "us-east-1"
}

# good - modules/vpc/versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```
