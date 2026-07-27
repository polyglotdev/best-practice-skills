<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 3. Comments

Under [Comments](https://developer.hashicorp.com/terraform/language/style#comments) / [Linting and static code
analysis](https://developer.hashicorp.com/terraform/language/style#linting-and-static-code-analysis), HashiCorp treats `#` as
the idiomatic comment marker for single- and multi-line comments. `//` and
`/* */` remain for HCL backward compatibility and are not idiomatic. Write
code that needs few comments; comment complexity, not the obvious.

## 3.1 Use `#` for single-line and multi-line comments.

> Why? The style guide states `#` is idiomatic; `//` and `/* */` are legacy ([Comments](https://developer.hashicorp.com/terraform/language/style#comments)).
> **Violation.**
>
> Enforced by: terraform_comment_syntax.

```hcl
# bad - C-style comments
// temporary dual-run of the blue target group
resource "aws_lb_target_group" "blue" {
  /* name = "app-blue" */
  name = "app-blue"
}

# good - hash comments
# temporary dual-run of the blue target group
resource "aws_lb_target_group" "blue" {
  name = "app-blue"
}
```

## 3.2 Comment why, not what, when the HCL is not already obvious.

> Why? HashiCorp: write code that is easy to understand; comment only when necessary ([Comments](https://developer.hashicorp.com/terraform/language/style#comments)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - narrates the syntax
# Create an aws_instance resource named web
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

# good - explains a non-obvious constraint
# Pin to this AMI name filter; the golden image pipeline rotates weekly.
data "aws_ami" "web" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["web-golden-*"]
  }
}
```

## 3.3 Prefer a multi-line `#` block over `/* */` for longer notes.

> Why? `/* */` is supported for compatibility, not style ([Comments](https://developer.hashicorp.com/terraform/language/style#comments)).
> **Violation.**
>
> Enforced by: terraform_comment_syntax.

```hcl
# bad
/*
  Each tunnel encrypts traffic for its gateway.
*/
resource "google_compute_vpn_tunnel" "tunnel1" {
  name = "tunnel1"
}

# good
# Each tunnel is responsible for encrypting and decrypting traffic exiting
# and leaving its associated gateway.
resource "google_compute_vpn_tunnel" "tunnel1" {
  name = "tunnel1"
}
```

## 3.4 Clarify non-obvious `count` / `for_each` with a short comment.

> Why? [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count) says if the effect of a meta-argument is not immediately obvious, comment it.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - silent conditional
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0
  ami   = data.aws_ami.web.id
}

# good - intent is explicit
# Metrics hosts are optional in lower environments.
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0

  ami = data.aws_ami.web.id
}
```

## 3.5 Do not leave large blocks of commented-out resources in the main branch.

> Why? Commented-out HCL bitrots against provider upgrades and hides dead intent. Delete and rely on git history.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - zombie resource
# resource "aws_instance" "legacy" {
#   ami = "ami-old"
# }

# good - removed; recover from git if needed
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}
```

## 3.6 Document non-obvious `lifecycle` ignore_changes with a comment.

> Why? Ignoring changes silently is a common source of drift confusion. A one-line comment next to `ignore_changes` records the external mutator.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
lifecycle {
  ignore_changes = [desired_capacity]
}

# good
# ASG desired_capacity is scaled by the application scheduler outside Terraform.
lifecycle {
  ignore_changes = [desired_capacity]
}
```

## 3.7 Keep TODO comments rare and actionable (owner or issue link).

> Why? Bare `# TODO` comments accumulate. Prefer a tracked issue and a short pointer, or fix the gap before merge.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
# TODO fix this later
resource "aws_security_group_rule" "tmp" {
  cidr_blocks = ["0.0.0.0/0"]
}

# good
# Temporary until ticket INFRA-482 lands the shared SG module.
resource "aws_security_group_rule" "tmp" {
  cidr_blocks = ["10.0.0.0/8"]
}
```

## 3.8 Do not use comments to disable formatter or hide invalid HCL.

> Why? If fmt or validate fails, fix the code. Comments are not a suppressions system for broken configuration.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - "fmt: off" folklore does nothing useful in Terraform
# fmt: off
resource "aws_instance" "web"{ami="ami-1"}
# fmt: on

# good - valid, formatted HCL
resource "aws_instance" "web" {
  ami = "ami-1"
}
```
