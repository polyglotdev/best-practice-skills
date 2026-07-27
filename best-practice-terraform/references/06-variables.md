<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 6. Variables

[Variables](https://developer.hashicorp.com/terraform/language/style#variables) make modules flexible and overuse makes
roots unreadable. Expose a variable when a setting changes between deployments.
Every variable needs a `type` and `description`. Optional variables get a
reasonable `default`. Sensitive inputs set `sensitive = true`. Prefer input
validation only for uniquely restrictive rules. Parameter order: type,
description, default, sensitive, validation blocks. See also the language
[input variables](https://developer.hashicorp.com/terraform/language/values/variables) docs.

## 6.1 Include `type` and `description` on every variable.

> Why? Required by [Variables](https://developer.hashicorp.com/terraform/language/style#variables).
> **Violation.**
>
> Enforced by: terraform_typed_variables.

```hcl
# bad
variable "instance_type" {}

# good
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web tier"
}
```

## 6.2 Follow variable parameter order: type, description, default, sensitive, validation.

> Why? Spelled out under [Variables](https://developer.hashicorp.com/terraform/language/style#variables).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
variable "db_password" {
  sensitive   = true
  default     = null
  description = "Database password"
  type        = string
}

# good
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}
```

## 6.3 Give optional variables a reasonable `default`.

> Why? [Variables](https://developer.hashicorp.com/terraform/language/style#variables): if optional, define a reasonable default.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - optional in practice but required in the interface
variable "enable_monitoring" {
  type        = bool
  description = "Enable detailed monitoring"
}

# good
variable "enable_monitoring" {
  type        = bool
  description = "Enable detailed monitoring"
  default     = true
}
```

## 6.4 Mark passwords, private keys, and tokens with `sensitive = true`.

> Why? [Variables](https://developer.hashicorp.com/terraform/language/style#variables) notes Terraform still stores the value in state, but suppresses it in plan/apply UI.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
variable "db_password" {
  type        = string
  description = "Database password"
}

# good
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}
```

## 6.5 Use `validation` blocks only for uniquely restrictive requirements.

> Why? Type checks already cover shape. Add validation when business rules go further ([Variables](https://developer.hashicorp.com/terraform/language/style#variables)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - validation that only repeats the type system
variable "name" {
  type = string
  validation {
    condition     = var.name != null
    error_message = "name must be set"
  }
}

# good - domain constraint
variable "web_instance_count" {
  type        = number
  description = "Number of web instances. This application requires at least two."

  validation {
    condition     = var.web_instance_count > 1
    error_message = "This application requires at least two web instances."
  }
}
```

## 6.6 Do not expose a variable for every resource argument.

> Why? Overusing variables makes code hard to understand ([Variables](https://developer.hashicorp.com/terraform/language/style#variables)). Hardcode stable internals; variable-ize deployment differences.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - variable for an immutable internal detail
variable "root_volume_type" {
  type    = string
  default = "gp3"
}

# good - only settings that change per environment
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web tier"
}
```

## 6.7 Prefer object/map types over long parallel variable lists for related settings.

> Why? A single object keeps related knobs together and documents the shape once.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
variable "db_name" { type = string }
variable "db_user" { type = string }
variable "db_port" { type = number }

# good
variable "database" {
  type = object({
    name = string
    user = string
    port = number
  })
  description = "Application database connection settings"
}
```

## 6.8 Document units and allowed values in the description when not obvious.

> Why? Descriptions are the module contract. Callers should not need to open resources to learn that `disk_size` is GiB.
> **Violation.**
>
> Enforced by: terraform_documented_variables.

```hcl
# bad
variable "db_disk_size" {
  type        = number
  description = "Disk size"
}

# good
variable "db_disk_size" {
  type        = number
  description = "Disk size for the API database, in GiB"
  default     = 100
}
```

## 6.9 Do not set defaults for secrets.

> Why? A default password is a committed secret. Require sensitive inputs explicitly at apply time.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
  default     = "changeme"
}

# good
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}
```

## 6.10 Name boolean variables so `true` reads naturally (`enable_*`, `create_*`).

> Why? Negative booleans (`disable_x = false`) invert mental models in conditionals.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
variable "disable_monitoring" {
  type    = bool
  default = false
}

# good
variable "enable_monitoring" {
  type        = bool
  description = "When true, enable detailed monitoring"
  default     = true
}
```
