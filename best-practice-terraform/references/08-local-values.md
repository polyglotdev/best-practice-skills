<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 8. Local Values

[Local values](https://developer.hashicorp.com/terraform/language/style#local-values) DRY repeated expressions. Overuse
makes code harder to follow. Prefer locals for composed names and repeated
maps; keep one-off expressions inline. Define cross-file locals in
`locals.tf`; file-private locals at the top of that file. Language reference:
[locals](https://developer.hashicorp.com/terraform/language/values/locals).

## 8.1 Use locals sparingly for values referenced multiple times.

> Why? HashiCorp warns that overuse hurts readability ([Local values](https://developer.hashicorp.com/terraform/language/style#local-values)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - local wrapping a single use
locals {
  web_ami = data.aws_ami.web.id
}

resource "aws_instance" "web" {
  ami = local.web_ami
}

# good - inline single use; local for repeated composition
locals {
  name_suffix = "${var.region}-${var.environment}"
}

resource "aws_instance" "web" {
  ami = data.aws_ami.web.id

  tags = {
    Name = "web-${local.name_suffix}"
  }
}
```

## 8.2 Put cross-file locals in `locals.tf`.

> Why? From [Local values](https://developer.hashicorp.com/terraform/language/style#local-values).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - same local copied into network.tf and compute.tf

# good - locals.tf
locals {
  name_suffix = "${var.region}-${var.environment}"
}
```

## 8.3 Keep file-specific locals at the top of that file.

> Why? Allowed alternative in [Local values](https://developer.hashicorp.com/terraform/language/style#local-values).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - local buried under resources in compute.tf
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

locals {
  web_user_data = file("${path.module}/user-data.sh")
}

# good - locals first in compute.tf
locals {
  web_user_data = file("${path.module}/user-data.sh")
}

resource "aws_instance" "web" {
  ami       = data.aws_ami.web.id
  user_data = local.web_user_data
}
```

## 8.4 Name locals with nouns and underscores.

> Why? Same naming rule as other objects ([Local values](https://developer.hashicorp.com/terraform/language/style#local-values)).
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
locals {
  x = "${var.region}-${var.environment}"
}

# good
locals {
  name_suffix = "${var.region}-${var.environment}"
}
```

## 8.5 Prefer flat locals over deep nested local maps that require archaeology.

> Why? Deep `local.a.b.c.d` chains are hard to grep. Compose smaller named locals.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
locals {
  cfg = {
    web = {
      prod = { instance = "m5.large" }
    }
  }
}

# good
locals {
  web_instance_type = var.environment == "prod" ? "m5.large" : "t3.micro"
}
```

## 8.6 Do not use locals as a substitute for variables at a module boundary.

> Why? If callers must change a value, it is a variable. Locals are private composition inside the module.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - forcing callers to fork the module to change a "local"
locals {
  instance_type = "t3.micro"
}

# good
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}
```

## 8.7 Centralize common tags in a local (or provider `default_tags`) instead of repeating maps.

> Why? Repeated tag maps drift. One local (or provider default) keeps them honest.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - copy/paste tags on every resource
tags = {
  Project     = "billing"
  Environment = "prod"
  ManagedBy   = "terraform"
}

# good
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

## 8.8 Avoid locals that only rename `var.*` without adding meaning.

> Why? `local.environment = var.environment` adds indirection for no gain.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
locals {
  environment = var.environment
}

# good - reference var.environment directly, or compose
locals {
  name_prefix = "${var.project}-${var.environment}"
}
```

## 8.9 Keep conditional expressions in locals when reused; inline when used once.

> Why? Reuse is the bar. A one-off ternary next to its resource is clearer than a distant local.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - single-use local three files away
locals {
  monitoring = var.enable_monitoring ? "enabled" : "disabled"
}

# good - reused local
locals {
  monitoring_tag = var.enable_monitoring ? "enabled" : "disabled"
}
```

## 8.10 Do not hide provider data lookups behind unexplained locals without comments.

> Why? A local that is really "the production AMI ID from a data source" should read that way in the name or a comment.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
locals {
  image = data.aws_ami.web.id
}

# good
locals {
  web_ami_id = data.aws_ami.web.id
}
```
