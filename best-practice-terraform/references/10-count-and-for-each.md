<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 10. Count & for_each

[Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count) covers `count`
and `for_each`. Use them sparingly. Prefer `count` when instances are nearly
identical; prefer `for_each` when instances need distinct keys/values. Conditional
creation with `count = cond ? 1 : 0` is common; comment non-obvious cases.
Language refs: [`count`](https://developer.hashicorp.com/terraform/language/meta-arguments/count), [`for_each`](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each).

## 10.1 Use `count` and `for_each` sparingly.

> Why? Stated in the [code style summary](https://developer.hashicorp.com/terraform/language/style#code-style) and [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - meta-arguments wrapping every resource "for flexibility"

# good - concrete resources until duplication is real
```

## 10.2 Prefer `for_each` when instances need distinct identities; use `count` for near-identical replicas.

> Why? Guidance in [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - count with lookup tables keyed by index
resource "aws_instance" "web" {
  count = length(var.web_names)
  tags = {
    Name = var.web_names[count.index]
  }
}

# good
resource "aws_instance" "web" {
  for_each = toset(var.web_names)

  tags = {
    Name = "web_${each.key}"
  }
}
```

## 10.3 Convert lists to sets with `toset` when using `for_each` over a list of strings.

> Why? Example pattern in [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
resource "aws_instance" "web" {
  for_each = var.web_instances # list(string) - error
}

# good
resource "aws_instance" "web" {
  for_each = toset(var.web_instances)
}
```

## 10.4 Use `count = condition ? 1 : 0` for simple optional resources; comment intent.

> Why? Shown under [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0
  ami   = data.aws_ami.web.id
}

# good
# Optional metrics host for non-prod profiles.
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0

  ami = data.aws_ami.web.id
}
```

## 10.5 Address `for_each` instances by key, not by `values(...)[0]`.

> Why? Keys are stable; list order is not a contract.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
output "ui_ip" {
  value = values(aws_instance.web)[0].public_ip
}

# good
output "web_ui_public_ip" {
  description = "Public IP of the web UI instance"
  value       = aws_instance.web["ui"].public_ip
}
```

## 10.6 Do not stretch `count` across resources that later need stable identities.

> Why? Inserting an element at index 0 forces replacements. `for_each` keys avoid that.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - adding a name at the front reshuffles all indices
variable "web_names" {
  default = ["api", "ui"]
}

# good - set/map keys
variable "web_instances" {
  type        = set(string)
  description = "Logical names for web instances"
  default     = ["api", "ui"]
}
```

## 10.7 Avoid `count`/`for_each` driven by remote data that is unknown at plan time when possible.

> Why? Unknown-at-plan counts force messy plans. Prefer explicit maps from variables.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - for_each over a data source that appears during apply only

# good - for_each over var.subnets supplied by the root
```

## 10.8 When using `count`, reference with `[count.index]` carefully and prefer splat only for simple cases.

> Why? Legacy splat alone does not replace clear indexing or `for_each`.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - unclear which instance is special-cased
resource "aws_eip" "web" {
  instance = aws_instance.web.*.id[0]
}

# good
resource "aws_eip" "web" {
  instance = aws_instance.web[0].id
}
```

## 10.9 Do not mix `count` and `for_each` on the same resource block.

> Why? Terraform rejects it; pick one model per resource.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
resource "aws_instance" "web" {
  count    = 2
  for_each = toset(["a", "b"])
}

# good
resource "aws_instance" "web" {
  for_each = toset(["a", "b"])
}
```

## 10.10 Document why a module uses meta-arguments when the effect is non-obvious.

> Why? HashiCorp asks for comments when the effect is not obvious ([Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - silent triple nested for_each in a shared module

# good - module README + inline comment describing the key space
```
