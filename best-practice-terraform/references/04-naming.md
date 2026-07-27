<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 4. Naming

[Resource naming](https://developer.hashicorp.com/terraform/language/style#resource-naming) is short: descriptive nouns,
underscores between words, no resource type in the name, and double quotes
around type and name. The same noun + underscore pattern applies to variables,
outputs, and locals. Module addresses follow the same readability bar; registry
module repositories use the `terraform-<PROVIDER>-<NAME>` form covered in
chapter 12.

## 4.1 Name resources with a descriptive noun; separate words with underscores.

> Why? [Resource naming](https://developer.hashicorp.com/terraform/language/style#resource-naming) requires nouns and underscores for consistency and readability.
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
resource "aws_instance" "WebAPI-aws-instance" {
  ami = "ami-123"
}

# good
resource "aws_instance" "web_api" {
  ami = "ami-123"
}
```

## 4.2 Do not include the resource type in the resource name.

> Why? The resource address already includes the type ([Resource naming](https://developer.hashicorp.com/terraform/language/style#resource-naming)).
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
resource "aws_instance" "web_aws_instance" {
  ami = "ami-123"
}

# good
resource "aws_instance" "web" {
  ami = "ami-123"
}
```

## 4.3 Always quote the resource type and name.

> Why? The style guide shows quoted type and name as the good form ([Resource naming](https://developer.hashicorp.com/terraform/language/style#resource-naming)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - unquoted identifiers (legacy HCL habit)
resource aws_instance web {
  ami = "ami-123"
}

# good
resource "aws_instance" "web" {
  ami = "ami-123"
}
```

## 4.4 Name variables with descriptive nouns and underscores.

> Why? [Variables](https://developer.hashicorp.com/terraform/language/style#variables) / [Outputs](https://developer.hashicorp.com/terraform/language/style#outputs) recommend the same noun + underscore pattern as resources.
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
variable "DBDiskSize" {
  type = number
}

# good
variable "db_disk_size" {
  type        = number
  description = "Disk size for the API database"
}
```

## 4.5 Name outputs with descriptive nouns and underscores.

> Why? Same naming rule as variables ([Outputs](https://developer.hashicorp.com/terraform/language/style#outputs)).
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
output "WebPublicIP" {
  value = aws_instance.web.public_ip
}

# good
output "web_public_ip" {
  description = "Public IP of the web instance"
  value       = aws_instance.web.public_ip
}
```

## 4.6 Name locals with descriptive nouns and underscores.

> Why? [Local values](https://developer.hashicorp.com/terraform/language/style#local-values) applies the same naming pattern.
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
locals {
  NameSuffix = "${var.region}-${var.environment}"
}

# good
locals {
  name_suffix = "${var.region}-${var.environment}"
}
```

## 4.7 Prefer `this` only when a module manages a single primary object of that type; otherwise be descriptive.

> Why? A single-resource module may use `this` for the primary object. A root module with many peers should use role nouns (`web`, `api`, `db`).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - meaningless in a multi-resource root
resource "aws_instance" "this" {
  ami = data.aws_ami.web.id
}

resource "aws_instance" "this2" {
  ami = data.aws_ami.web.id
}

# good - role nouns in the root; `this` inside a focused module
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

resource "aws_instance" "api" {
  ami = data.aws_ami.api.id
}
```

## 4.8 Name module calls with nouns that describe the capability, not the source.

> Why? Callers read `module.database`, not `module.terraform_aws_modules_rds`.
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
module "terraform-aws-modules-rds-aws" {
  source = "./modules/rds"
}

# good
module "database" {
  source = "./modules/rds"
}
```

## 4.9 Keep data source names aligned with the resource names that consume them.

> Why? [Resource order](https://developer.hashicorp.com/terraform/language/style#resource-order) pairs data sources with consumers; matching names (`data.aws_ami.web` -> `aws_instance.web`) reduces chase time.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
data "aws_ami" "latest_ubuntu_thing" {
  most_recent = true
}

resource "aws_instance" "web" {
  ami = data.aws_ami.latest_ubuntu_thing.id
}

# good
data "aws_ami" "web" {
  most_recent = true
}

resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}
```

## 4.10 Avoid encoding environment or account IDs into resource names when a variable or local already carries that context.

> Why? Hardcoding `prod` into every name fights multi-environment roots. Compose from `local.name_suffix` instead (see locals chapter).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
resource "aws_s3_bucket" "prod_logs_us_east_1" {
  bucket = "acme-prod-logs-us-east-1"
}

# good
resource "aws_s3_bucket" "logs" {
  bucket = "${local.name_prefix}-logs"
}
```
