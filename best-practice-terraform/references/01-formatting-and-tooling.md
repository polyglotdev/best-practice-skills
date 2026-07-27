<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 1. Formatting & Tooling

Terraform settled formatting the same way Go settled `gofmt`: one command,
one idiomatic subset, no style arguments in review. The HashiCorp
[Style Guide](https://developer.hashicorp.com/terraform/language/style#code-formatting) fixes two-space indent, equals-sign
alignment for consecutive single-line arguments, argument-then-block order
inside bodies, and blank-line separation of top-level blocks. [`terraform
fmt`](https://developer.hashicorp.com/terraform/cli/commands/fmt) implements a subset of those rules. [`terraform
validate`](https://developer.hashicorp.com/terraform/cli/commands/validate) owns syntactic and internal consistency checks.
This chapter hands every layout decision to that pair and moves on.

**Indentation in this skill is two spaces.** That is the upstream HashiCorp
rule. Every HCL sample in every chapter is written as `terraform fmt` would
emit it.

Formatting is not linting. `terraform fmt` rewrites layout; `terraform
validate` checks types and references; TFLint (chapter 15) enforces org
rules. No later chapter re-litigates whitespace.

## 1.1 Run `terraform fmt -recursive` before every commit and `terraform fmt -check -recursive` in CI.

> Why? The [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting) section recommends running `terraform fmt` before each commit. The write path is `fmt` (or `fmt -recursive`); the read-only gate is `fmt -check`. A formatting failure is the cheapest possible CI failure.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - mixed indent and unaligned equals; fmt rewrites this
resource "aws_instance" "web" {
ami = "ami-123"
    instance_type="t3.micro"
}

# good - two-space indent, aligned equals (terraform fmt)
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}
```

## 1.2 Indent with two spaces. Never tabs.

> Why? The style guide states "Indent two spaces for each nesting level" under [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting). Tabs render at different widths and produce noisy diffs the first time anyone runs fmt.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - four-space habit from another language (never use tab indents)
resource "aws_s3_bucket" "logs" {
    bucket = "example-logs"
}

# good - two spaces
resource "aws_s3_bucket" "logs" {
  bucket = "example-logs"
}
```

## 1.3 Align equals signs for consecutive single-line arguments at the same nesting level.

> Why? HashiCorp calls this out explicitly in [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting). `terraform fmt` performs the alignment.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - jagged assignment columns
resource "aws_instance" "api" {
  ami = "ami-abc"
  instance_type = "t3.small"
  subnet_id = aws_subnet.private.id
}

# good - aligned equals
resource "aws_instance" "api" {
  ami           = "ami-abc"
  instance_type = "t3.small"
  subnet_id     = aws_subnet.private.id
}
```

## 1.4 Place arguments above nested blocks; separate them with one blank line.

> Why? [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting) requires arguments first, then nested blocks, with one blank line between the groups.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - nested block interleaved before sibling arguments
resource "aws_instance" "web" {
  ami = "ami-123"

  root_block_device {
    volume_size = 20
  }
  instance_type = "t3.micro"
}

# good - arguments, blank line, then blocks
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"

  root_block_device {
    volume_size = 20
  }
}
```

## 1.5 List meta-arguments first; place meta-argument blocks last.

> Why? `count` / `for_each` go first; `lifecycle` / `provisioner` blocks go last, separated by blank lines ([Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting), [Dynamic resource count](https://developer.hashicorp.com/terraform/language/style#dynamic-resource-count)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - lifecycle buried between arguments
resource "aws_instance" "web" {
  ami = "ami-123"
  lifecycle {
    create_before_destroy = true
  }
  instance_type = "t3.micro"
  count         = 2
}

# good - meta-argument, arguments, nested blocks, meta-argument block
resource "aws_instance" "web" {
  count = 2

  ami           = "ami-123"
  instance_type = "t3.micro"

  root_block_device {
    volume_size = 20
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

## 1.6 Separate top-level blocks with one blank line.

> Why? [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting) requires a blank line between top-level blocks so scanners can find resource boundaries quickly.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - stacked top-level blocks
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

# good - blank line between top-level blocks
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}
```

## 1.7 Run `terraform validate` after fmt and before commit or CI merge.

> Why? [Code validation](https://developer.hashicorp.com/terraform/language/style#code-validation) says validate is safe to run automatically and frequently. It catches type mistakes and broken references without touching state.
> **Violation.**
>
> Enforced by: terraform validate.

```hcl
# bad - never validated; typo survives until plan in CI
resource "aws_instance" "web" {
  ami           = data.aws_ami.web.id
  instance_type = var.instance_tipe
}

# good - validate catches unknown variable before review
resource "aws_instance" "web" {
  ami           = data.aws_ami.web.id
  instance_type = var.instance_type
}
```

```bash
# good - local / CI sequence
terraform fmt -recursive
terraform validate
```

## 1.8 Do not hand-format around `terraform fmt`; treat fmt output as canonical.

> Why? Fighting the formatter creates thrash. The style guide delegates a subset of layout to [`terraform fmt`](https://developer.hashicorp.com/terraform/cli/commands/fmt); accept its output.
> **Violation.**
>
> Enforced by: terraform fmt.

```hcl
# bad - "pretty" layout fmt will undo on the next save
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}

# good - whatever terraform fmt emits is correct
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}
```

## 1.9 Use empty lines to separate logical groups of arguments within a block.

> Why? Called out in [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting). Grouping by concern (identity, networking, tags) beats a single dense argument list.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - unrelated arguments jammed together with no grouping
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private.id
  tags = {
    Name = "web"
  }
  monitoring = true
}

# good - blank line between logical groups
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
  monitoring    = true

  subnet_id = aws_subnet.private.id

  tags = {
    Name = "web"
  }
}
```

## 1.10 Keep editor and CI on the same Terraform version that `required_version` allows.

> Why? Fmt and validate behavior can differ across major/minor lines. Pin the binary in CI to a version satisfying [version pinning](https://developer.hashicorp.com/terraform/language/style#version-pinning).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - laptop on 1.5, CI on 1.9, validate disagrees on syntax features
# (no HCL sample - this is a toolchain mismatch)

# good - .terraform-version / asdf / CI image matches required_version
# terraform {
#   required_version = ">= 1.7"
# }
```
