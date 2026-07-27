<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 7. Outputs

[Outputs](https://developer.hashicorp.com/terraform/language/style#outputs) expose data on the CLI and to other
configurations. Provide a description for every output (and a type when your
Terraform version supports output types). Parameter order: type, description,
value, sensitive. Keep names as descriptive nouns with underscores. Prefer
exporting only what consumers need. Language reference:
[output values](https://developer.hashicorp.com/terraform/language/values/outputs).

## 7.1 Include a `description` on every output.

> Why? Required by [Outputs](https://developer.hashicorp.com/terraform/language/style#outputs) and the style summary.
> **Violation.**
>
> Enforced by: terraform_documented_outputs.

```hcl
# bad
output "web_public_ip" {
  value = aws_instance.web.public_ip
}

# good
output "web_public_ip" {
  description = "Public IP of the web instance"
  value       = aws_instance.web.public_ip
}
```

## 7.2 Follow output parameter order: type, description, value, sensitive.

> Why? From [Outputs](https://developer.hashicorp.com/terraform/language/style#outputs).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
output "web_public_ip" {
  value       = aws_instance.web.public_ip
  description = "Public IP of the web instance"
  type        = string
}

# good
output "web_public_ip" {
  type        = string
  description = "Public IP of the web instance"
  value       = aws_instance.web.public_ip
}
```

## 7.3 Mark outputs that echo secrets with `sensitive = true`.

> Why? Otherwise plan and apply print them. State still stores the value.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
output "db_password" {
  description = "Database password"
  value       = var.db_password
}

# good
output "db_password" {
  description = "Database password"
  value       = var.db_password
  sensitive   = true
}
```

## 7.4 Export stable identifiers consumers need; do not dump entire resources.

> Why? Whole-resource outputs couple callers to provider schema churn.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
output "web" {
  value = aws_instance.web
}

# good
output "web_instance_id" {
  description = "EC2 instance ID for the web tier"
  value       = aws_instance.web.id
}
```

## 7.5 Keep root-module outputs aligned with what other stacks actually consume.

> Why? [State sharing](https://developer.hashicorp.com/terraform/language/style#state-sharing) prefers narrow contracts over shipping the entire state.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - twenty unused outputs "just in case"

# good - vpc_id, private_subnet_ids, and nothing else until a consumer asks
```

## 7.6 Use for-expressions to reshape maps of instances from `for_each` resources.

> Why? Shown in [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - brittle index into a map
output "first_ip" {
  value = values(aws_instance.web)[0].private_ip
}

# good
output "web_private_ips" {
  description = "Private IPs of the web instances"
  value = {
    for k, v in aws_instance.web : k => v.private_ip
  }
}
```

## 7.7 Name outputs after the value, not after the resource type string.

> Why? Callers want `vpc_id`, not `aws_vpc_main_id`.
> **Violation.**
>
> Enforced by: terraform_naming_convention.

```hcl
# bad
output "aws_vpc_main_id" {
  value = aws_vpc.main.id
}

# good
output "vpc_id" {
  description = "ID of the application VPC"
  value       = aws_vpc.main.id
}
```

## 7.8 Do not compute expensive derived values in outputs when a local already holds them.

> Why? Outputs should usually reference resources, data sources, or locals - not hide a second copy of complex expressions.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - duplicated composition
output "name_prefix" {
  value = "${var.project}-${var.environment}"
}

# good
output "name_prefix" {
  description = "Prefix applied to resource names"
  value       = local.name_prefix
}
```

## 7.9 Prefer lists/maps with stable keys over depending on resource list order.

> Why? `count` index outputs reshuffle when you insert instances; `for_each` keys do not.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
output "web_ip_0" {
  value = aws_instance.web[0].private_ip
}

# good
output "web_ui_private_ip" {
  description = "Private IP of the web UI instance"
  value       = aws_instance.web["ui"].private_ip
}
```

## 7.10 Document units and format in output descriptions when relevant.

> Why? Downstream automation parses outputs; say whether an ARN, ID, or URL is returned.
> **Violation.**
>
> Enforced by: terraform_documented_outputs.

```hcl
# bad
output "connection_string" {
  value = aws_db_instance.main.endpoint
}

# good
output "db_endpoint" {
  description = "host:port endpoint for the primary database"
  value       = aws_db_instance.main.endpoint
}
```
