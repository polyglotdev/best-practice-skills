#!/usr/bin/env python3
'''Generate best-practice-terraform reference chapters from structured rules.

Run from repo root:

  python3 scripts/build_terraform_skill.py
'''

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'best-practice-terraform' / 'references'

STYLE = 'https://developer.hashicorp.com/terraform/language/style'
MOD_STRUCT = 'https://developer.hashicorp.com/terraform/language/modules/develop/structure'
VARS_DOC = 'https://developer.hashicorp.com/terraform/language/values/variables'
OUTS_DOC = 'https://developer.hashicorp.com/terraform/language/values/outputs'
LOCALS_DOC = 'https://developer.hashicorp.com/terraform/language/values/locals'
COUNT_DOC = 'https://developer.hashicorp.com/terraform/language/meta-arguments/count'
FOR_EACH_DOC = 'https://developer.hashicorp.com/terraform/language/meta-arguments/for_each'
PROVIDERS_DOC = 'https://developer.hashicorp.com/terraform/language/providers/configuration'
SETTINGS_DOC = 'https://developer.hashicorp.com/terraform/language/settings'
TEST_DOC = 'https://developer.hashicorp.com/terraform/language/tests'
FMT_DOC = 'https://developer.hashicorp.com/terraform/cli/commands/fmt'
VALIDATE_DOC = 'https://developer.hashicorp.com/terraform/cli/commands/validate'
BACKEND_DOC = 'https://developer.hashicorp.com/terraform/language/backend'


def rule(
  num: str,
  title: str,
  why: str,
  bad: str,
  good: str,
  *,
  enforced: str | None = None,
  suggestion: bool = False,
  extra: str = '',
  lang: str = 'hcl',
) -> str:
  label = 'Suggestion' if suggestion or not enforced else 'Violation'
  enfline = ''
  if enforced:
    enfline = f'\n>\n> Enforced by: {enforced}.'
  elif suggestion or True:
    # Always clarify mechanical status.
    if suggestion or not enforced:
      enfline = '\n>\n> Not mechanically enforced by a tool this skill ships.'
  body = f'''## {num} {title}

> Why? {why}
> **{label}.**{enfline}

```{lang}
{bad.strip()}

{good.strip()}
```
'''
  if extra:
    body += '\n' + extra.strip() + '\n'
  return body


CHAPTERS: dict[str, tuple[str, str, list[str]]] = {}


def add(filename: str, title: str, intro: str, rules: list[str]) -> None:
  CHAPTERS[filename] = (title, intro, rules)


# ---------------------------------------------------------------------------
# Chapter 1
# ---------------------------------------------------------------------------
add(
  '01-formatting-and-tooling.md',
  '1. Formatting & Tooling',
  f'''Terraform settled formatting the same way Go settled `gofmt`: one command,
one idiomatic subset, no style arguments in review. The HashiCorp
[Style Guide]({STYLE}#code-formatting) fixes two-space indent, equals-sign
alignment for consecutive single-line arguments, argument-then-block order
inside bodies, and blank-line separation of top-level blocks. [`terraform
fmt`]({FMT_DOC}) implements a subset of those rules. [`terraform
validate`]({VALIDATE_DOC}) owns syntactic and internal consistency checks.
This chapter hands every layout decision to that pair and moves on.

**Indentation in this skill is two spaces.** That is the upstream HashiCorp
rule. Every HCL sample in every chapter is written as `terraform fmt` would
emit it.

Formatting is not linting. `terraform fmt` rewrites layout; `terraform
validate` checks types and references; TFLint (chapter 15) enforces org
rules. No later chapter re-litigates whitespace.''',
  [
    rule(
      '1.1',
      'Run `terraform fmt -recursive` before every commit and `terraform fmt -check -recursive` in CI.',
      f'The [Code formatting]({STYLE}#code-formatting) section recommends running '
      '`terraform fmt` before each commit. The write path is `fmt` (or '
      '`fmt -recursive`); the read-only gate is `fmt -check`. A formatting '
      'failure is the cheapest possible CI failure.',
      '''# bad - mixed indent and unaligned equals; fmt rewrites this
resource "aws_instance" "web" {
ami = "ami-123"
    instance_type="t3.micro"
}''',
      '''# good - two-space indent, aligned equals (terraform fmt)
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}''',
      enforced='terraform fmt',
    ),
    rule(
      '1.2',
      'Indent with two spaces. Never tabs.',
      f'The style guide states "Indent two spaces for each nesting level" under '
      f'[Code formatting]({STYLE}#code-formatting). Tabs render at different '
      'widths and produce noisy diffs the first time anyone runs fmt.',
      '''# bad - four-space habit from another language (never use tab indents)
resource "aws_s3_bucket" "logs" {
    bucket = "example-logs"
}''',
      '''# good - two spaces
resource "aws_s3_bucket" "logs" {
  bucket = "example-logs"
}''',
      enforced='terraform fmt',
    ),
    rule(
      '1.3',
      'Align equals signs for consecutive single-line arguments at the same nesting level.',
      f'HashiCorp calls this out explicitly in [Code formatting]({STYLE}#code-formatting). '
      '`terraform fmt` performs the alignment.',
      '''# bad - jagged assignment columns
resource "aws_instance" "api" {
  ami = "ami-abc"
  instance_type = "t3.small"
  subnet_id = aws_subnet.private.id
}''',
      '''# good - aligned equals
resource "aws_instance" "api" {
  ami           = "ami-abc"
  instance_type = "t3.small"
  subnet_id     = aws_subnet.private.id
}''',
      enforced='terraform fmt',
    ),
    rule(
      '1.4',
      'Place arguments above nested blocks; separate them with one blank line.',
      f'[Code formatting]({STYLE}#code-formatting) requires arguments first, then '
      'nested blocks, with one blank line between the groups.',
      '''# bad - nested block interleaved before sibling arguments
resource "aws_instance" "web" {
  ami = "ami-123"

  root_block_device {
    volume_size = 20
  }
  instance_type = "t3.micro"
}''',
      '''# good - arguments, blank line, then blocks
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"

  root_block_device {
    volume_size = 20
  }
}''',
      suggestion=True,
    ),
    rule(
      '1.5',
      'List meta-arguments first; place meta-argument blocks last.',
      f'`count` / `for_each` go first; `lifecycle` / `provisioner` blocks go last, '
      f'separated by blank lines ([Code formatting]({STYLE}#code-formatting), '
      f'[Dynamic resource count]({STYLE}#dynamic-resource-count)).',
      '''# bad - lifecycle buried between arguments
resource "aws_instance" "web" {
  ami = "ami-123"
  lifecycle {
    create_before_destroy = true
  }
  instance_type = "t3.micro"
  count         = 2
}''',
      '''# good - meta-argument, arguments, nested blocks, meta-argument block
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
}''',
      suggestion=True,
    ),
    rule(
      '1.6',
      'Separate top-level blocks with one blank line.',
      f'[Code formatting]({STYLE}#code-formatting) requires a blank line between '
      'top-level blocks so scanners can find resource boundaries quickly.',
      '''# bad - stacked top-level blocks
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}''',
      '''# good - blank line between top-level blocks
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}''',
      enforced='terraform fmt',
    ),
    rule(
      '1.7',
      'Run `terraform validate` after fmt and before commit or CI merge.',
      f'[Code validation]({STYLE}#code-validation) says validate is safe to run '
      'automatically and frequently. It catches type mistakes and broken '
      'references without touching state.',
      '''# bad - never validated; typo survives until plan in CI
resource "aws_instance" "web" {
  ami           = data.aws_ami.web.id
  instance_type = var.instance_tipe
}''',
      '''# good - validate catches unknown variable before review
resource "aws_instance" "web" {
  ami           = data.aws_ami.web.id
  instance_type = var.instance_type
}''',
      enforced='terraform validate',
      extra='''```bash
# good - local / CI sequence
terraform fmt -recursive
terraform validate
```''',
    ),
    rule(
      '1.8',
      'Do not hand-format around `terraform fmt`; treat fmt output as canonical.',
      f'Fighting the formatter creates thrash. The style guide delegates a subset '
      f'of layout to [`terraform fmt`]({FMT_DOC}); accept its output.',
      '''# bad - "pretty" layout fmt will undo on the next save
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}''',
      '''# good - whatever terraform fmt emits is correct
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}''',
      enforced='terraform fmt',
    ),
    rule(
      '1.9',
      'Use empty lines to separate logical groups of arguments within a block.',
      f'Called out in [Code formatting]({STYLE}#code-formatting). Grouping by '
      'concern (identity, networking, tags) beats a single dense argument list.',
      '''# bad - unrelated arguments jammed together with no grouping
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private.id
  tags = {
    Name = "web"
  }
  monitoring = true
}''',
      '''# good - blank line between logical groups
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
  monitoring    = true

  subnet_id = aws_subnet.private.id

  tags = {
    Name = "web"
  }
}''',
      suggestion=True,
    ),
    rule(
      '1.10',
      'Keep editor and CI on the same Terraform version that `required_version` allows.',
      f'Fmt and validate behavior can differ across major/minor lines. Pin the '
      f'binary in CI to a version satisfying [version pinning]({STYLE}#version-pinning).',
      '''# bad - laptop on 1.5, CI on 1.9, validate disagrees on syntax features
# (no HCL sample - this is a toolchain mismatch)''',
      '''# good - .terraform-version / asdf / CI image matches required_version
# terraform {
#   required_version = ">= 1.7"
# }''',
      suggestion=True,
    ),
  ],
)

# ---------------------------------------------------------------------------
# Chapter 2
# ---------------------------------------------------------------------------
add(
  '02-file-names-and-layout.md',
  '2. File Names & Layout',
  f'''The [File names]({STYLE}#file-names) section defines the default file
set for a root module: `backend.tf`, `main.tf`, `outputs.tf`, `providers.tf`,
`terraform.tf`, `variables.tf`, `locals.tf`, and sparingly `override.tf`. When
that set becomes hard to navigate, split resources by logical group
(`network.tf`, `storage.tf`, `compute.tf`) while keeping the standard files for
providers, versions, variables, and outputs.''',
  [
    rule(
      '2.1',
      'Put `required_version` and `required_providers` in `terraform.tf`.',
      f'[File names]({STYLE}#file-names) assigns versioning to `terraform.tf` so '
      'operators always know where constraints live.',
      '''# bad - versions buried in main.tf next to resources
# main.tf
terraform {
  required_version = ">= 1.7"
}''',
      '''# good - terraform.tf owns version constraints
# terraform.tf
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}''',
      suggestion=True,
    ),
    rule(
      '2.2',
      'Put backend configuration in `backend.tf`.',
      f'The style guide recommends a dedicated [`backend.tf`]({STYLE}#file-names) '
      f'and notes you may use multiple `terraform` blocks to separate backend '
      f'from versioning ([backend docs]({BACKEND_DOC})).',
      '''# bad - backend mixed into terraform.tf with providers
terraform {
  required_version = ">= 1.7"
  backend "s3" {
    bucket = "example-state"
    key    = "app/terraform.tfstate"
    region = "us-east-1"
  }
}''',
      '''# good - backend.tf is the only place for backend config
# backend.tf
terraform {
  backend "s3" {}
}''',
      suggestion=True,
    ),
    rule(
      '2.3',
      'Put provider blocks in `providers.tf`.',
      f'[File names]({STYLE}#file-names) and [Provider aliasing]({STYLE}#provider-aliasing) '
      'keep all provider configuration in one file.',
      '''# bad - provider block at the top of main.tf
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}''',
      '''# good - providers.tf
provider "aws" {
  region = var.aws_region
}''',
      suggestion=True,
    ),
    rule(
      '2.4',
      'Keep variables in `variables.tf` in alphabetical order.',
      f'[File names]({STYLE}#file-names) says `variables.tf` contains all variable '
      'blocks alphabetically so reviewers can scan the interface.',
      '''# bad - variables scattered across files in call order
# network.tf
variable "vpc_cidr" { type = string }
# compute.tf
variable "instance_type" { type = string }''',
      '''# good - variables.tf, alphabetical
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web tier"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}''',
      suggestion=True,
    ),
    rule(
      '2.5',
      'Keep outputs in `outputs.tf` in alphabetical order.',
      f'Same convention as variables under [File names]({STYLE}#file-names).',
      '''# bad - outputs declared next to each resource
output "vpc_id" {
  value = aws_vpc.main.id
}

resource "aws_subnet" "private" {
  # ...
}

output "subnet_id" {
  value = aws_subnet.private.id
}''',
      '''# good - outputs.tf alphabetical
output "subnet_id" {
  description = "Private subnet ID"
  value       = aws_subnet.private.id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}''',
      suggestion=True,
    ),
    rule(
      '2.6',
      'Define shared locals in `locals.tf`; file-local locals may sit at the top of that file.',
      f'[Local values]({STYLE}#local-values) allows `locals.tf` for cross-file '
      'locals, or the top of a single file when the local is private to it.',
      '''# bad - same local redefined in multiple files
# network.tf
locals { name_prefix = "${var.project}-${var.environment}" }
# compute.tf
locals { name_prefix = "${var.project}-${var.environment}" }''',
      '''# good - locals.tf once
locals {
  name_prefix = "${var.project}-${var.environment}"
}''',
      suggestion=True,
    ),
    rule(
      '2.7',
      'Start with `main.tf` for resources; split by logical group when navigation suffers.',
      f'[File names]({STYLE}#file-names) starts with `main.tf`, then permits '
      '`network.tf` / `storage.tf` / `compute.tf` when size demands it. It must '
      'stay obvious where a resource lives.',
      '''# bad - 800-line main.tf mixing VPC, RDS, IAM, and DNS with no split''',
      '''# good - clear homes
# network.tf  - VPC, subnets, routes
# data.tf     - data sources for this stack
# compute.tf  - instances / ASG
# main.tf     - only if the root stays small''',
      suggestion=True,
    ),
    rule(
      '2.8',
      'Use `override.tf` / `*_override.tf` sparingly and comment the original resource.',
      f'Override files load last and make reasoning harder '
      f'([File names]({STYLE}#file-names)). Prefer an explicit variable or local.',
      '''# bad - silent override with no pointer at the source resource
# override.tf
resource "aws_instance" "web" {
  instance_type = "m5.large"
}''',
      '''# good - avoid overrides; parameterize instead
variable "web_instance_type" {
  type        = string
  description = "Instance type for the web tier"
  default     = "t3.micro"
}

resource "aws_instance" "web" {
  instance_type = var.web_instance_type
}''',
      suggestion=True,
    ),
    rule(
      '2.9',
      'Do not put provider blocks inside reusable child modules.',
      f'Provider configuration belongs in the root `providers.tf`. Child modules '
      f'declare `required_providers` in their own `terraform` block and inherit '
      f'configuration from the caller ([providers]({PROVIDERS_DOC})).',
      '''# bad - provider inside modules/vpc/main.tf
provider "aws" {
  region = "us-east-1"
}''',
      '''# good - module only declares required_providers
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}''',
      suggestion=True,
    ),
    rule(
      '2.10',
      'Keep `.tfvars` for non-secret values next to the root; never commit secret `.tfvars`.',
      f'[.gitignore]({STYLE}#gitignore) forbids committing sensitive `.tfvars`. '
      'Non-secret defaults may live in committed `terraform.tfvars` or '
      '`*.auto.tfvars` when your team agrees.',
      '''# bad - secrets.tfvars committed
db_password = "hunter2"''',
      '''# good - non-secret tfvars committed; secrets via env / CI / Vault
# terraform.tfvars
environment = "dev"
instance_type = "t3.micro"''',
      suggestion=True,
    ),
  ],
)

# ---------------------------------------------------------------------------
# Chapter 3
# ---------------------------------------------------------------------------
add(
  '03-comments.md',
  '3. Comments',
  f'''Under [Comments]({STYLE}#comments) / [Linting and static code
analysis]({STYLE}#linting-and-static-code-analysis), HashiCorp treats `#` as
the idiomatic comment marker for single- and multi-line comments. `//` and
`/* */` remain for HCL backward compatibility and are not idiomatic. Write
code that needs few comments; comment complexity, not the obvious.''',
  [
    rule(
      '3.1',
      'Use `#` for single-line and multi-line comments.',
      f'The style guide states `#` is idiomatic; `//` and `/* */` are legacy '
      f'([Comments]({STYLE}#comments)).',
      '''# bad - C-style comments
// temporary dual-run of the blue target group
resource "aws_lb_target_group" "blue" {
  /* name = "app-blue" */
  name = "app-blue"
}''',
      '''# good - hash comments
# temporary dual-run of the blue target group
resource "aws_lb_target_group" "blue" {
  name = "app-blue"
}''',
      enforced='terraform_comment_syntax',
    ),
    rule(
      '3.2',
      'Comment why, not what, when the HCL is not already obvious.',
      f'HashiCorp: write code that is easy to understand; comment only when '
      f'necessary ([Comments]({STYLE}#comments)).',
      '''# bad - narrates the syntax
# Create an aws_instance resource named web
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}''',
      '''# good - explains a non-obvious constraint
# Pin to this AMI name filter; the golden image pipeline rotates weekly.
data "aws_ami" "web" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["web-golden-*"]
  }
}''',
      suggestion=True,
    ),
    rule(
      '3.3',
      'Prefer a multi-line `#` block over `/* */` for longer notes.',
      f'`/* */` is supported for compatibility, not style '
      f'([Comments]({STYLE}#comments)).',
      '''# bad
/*
  Each tunnel encrypts traffic for its gateway.
*/
resource "google_compute_vpn_tunnel" "tunnel1" {
  name = "tunnel1"
}''',
      '''# good
# Each tunnel is responsible for encrypting and decrypting traffic exiting
# and leaving its associated gateway.
resource "google_compute_vpn_tunnel" "tunnel1" {
  name = "tunnel1"
}''',
      enforced='terraform_comment_syntax',
    ),
    rule(
      '3.4',
      'Clarify non-obvious `count` / `for_each` with a short comment.',
      f'[Dynamic resource count]({STYLE}#dynamic-resource-count) says if the '
      'effect of a meta-argument is not immediately obvious, comment it.',
      '''# bad - silent conditional
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0
  ami   = data.aws_ami.web.id
}''',
      '''# good - intent is explicit
# Metrics hosts are optional in lower environments.
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0

  ami = data.aws_ami.web.id
}''',
      suggestion=True,
    ),
    rule(
      '3.5',
      'Do not leave large blocks of commented-out resources in the main branch.',
      'Commented-out HCL bitrots against provider upgrades and hides dead '
      'intent. Delete and rely on git history.',
      '''# bad - zombie resource
# resource "aws_instance" "legacy" {
#   ami = "ami-old"
# }''',
      '''# good - removed; recover from git if needed
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}''',
      suggestion=True,
    ),
    rule(
      '3.6',
      'Document non-obvious `lifecycle` ignore_changes with a comment.',
      'Ignoring changes silently is a common source of drift confusion. A one-line '
      'comment next to `ignore_changes` records the external mutator.',
      '''# bad
lifecycle {
  ignore_changes = [desired_capacity]
}''',
      '''# good
# ASG desired_capacity is scaled by the application scheduler outside Terraform.
lifecycle {
  ignore_changes = [desired_capacity]
}''',
      suggestion=True,
    ),
    rule(
      '3.7',
      'Keep TODO comments rare and actionable (owner or issue link).',
      'Bare `# TODO` comments accumulate. Prefer a tracked issue and a short '
      'pointer, or fix the gap before merge.',
      '''# bad
# TODO fix this later
resource "aws_security_group_rule" "tmp" {
  cidr_blocks = ["0.0.0.0/0"]
}''',
      '''# good
# Temporary until ticket INFRA-482 lands the shared SG module.
resource "aws_security_group_rule" "tmp" {
  cidr_blocks = ["10.0.0.0/8"]
}''',
      suggestion=True,
    ),
    rule(
      '3.8',
      'Do not use comments to disable formatter or hide invalid HCL.',
      'If fmt or validate fails, fix the code. Comments are not a suppressions '
      'system for broken configuration.',
      '''# bad - "fmt: off" folklore does nothing useful in Terraform
# fmt: off
resource "aws_instance" "web"{ami="ami-1"}
# fmt: on''',
      '''# good - valid, formatted HCL
resource "aws_instance" "web" {
  ami = "ami-1"
}''',
      enforced='terraform fmt',
    ),
  ],
)

# ---------------------------------------------------------------------------
# Chapter 4
# ---------------------------------------------------------------------------
add(
  '04-naming.md',
  '4. Naming',
  f'''[Resource naming]({STYLE}#resource-naming) is short: descriptive nouns,
underscores between words, no resource type in the name, and double quotes
around type and name. The same noun + underscore pattern applies to variables,
outputs, and locals. Module addresses follow the same readability bar; registry
module repositories use the `terraform-<PROVIDER>-<NAME>` form covered in
chapter 12.''',
  [
    rule(
      '4.1',
      'Name resources with a descriptive noun; separate words with underscores.',
      f'[Resource naming]({STYLE}#resource-naming) requires nouns and underscores '
      'for consistency and readability.',
      '''# bad
resource "aws_instance" "WebAPI-aws-instance" {
  ami = "ami-123"
}''',
      '''# good
resource "aws_instance" "web_api" {
  ami = "ami-123"
}''',
      enforced='terraform_naming_convention',
    ),
    rule(
      '4.2',
      'Do not include the resource type in the resource name.',
      f'The resource address already includes the type '
      f'([Resource naming]({STYLE}#resource-naming)).',
      '''# bad
resource "aws_instance" "web_aws_instance" {
  ami = "ami-123"
}''',
      '''# good
resource "aws_instance" "web" {
  ami = "ami-123"
}''',
      enforced='terraform_naming_convention',
    ),
    rule(
      '4.3',
      'Always quote the resource type and name.',
      f'The style guide shows quoted type and name as the good form '
      f'([Resource naming]({STYLE}#resource-naming)).',
      '''# bad - unquoted identifiers (legacy HCL habit)
resource aws_instance web {
  ami = "ami-123"
}''',
      '''# good
resource "aws_instance" "web" {
  ami = "ami-123"
}''',
      suggestion=True,
    ),
    rule(
      '4.4',
      'Name variables with descriptive nouns and underscores.',
      f'[Variables]({STYLE}#variables) / [Outputs]({STYLE}#outputs) recommend the '
      'same noun + underscore pattern as resources.',
      '''# bad
variable "DBDiskSize" {
  type = number
}''',
      '''# good
variable "db_disk_size" {
  type        = number
  description = "Disk size for the API database"
}''',
      enforced='terraform_naming_convention',
    ),
    rule(
      '4.5',
      'Name outputs with descriptive nouns and underscores.',
      f'Same naming rule as variables ([Outputs]({STYLE}#outputs)).',
      '''# bad
output "WebPublicIP" {
  value = aws_instance.web.public_ip
}''',
      '''# good
output "web_public_ip" {
  description = "Public IP of the web instance"
  value       = aws_instance.web.public_ip
}''',
      enforced='terraform_naming_convention',
    ),
    rule(
      '4.6',
      'Name locals with descriptive nouns and underscores.',
      f'[Local values]({STYLE}#local-values) applies the same naming pattern.',
      '''# bad
locals {
  NameSuffix = "${var.region}-${var.environment}"
}''',
      '''# good
locals {
  name_suffix = "${var.region}-${var.environment}"
}''',
      enforced='terraform_naming_convention',
    ),
    rule(
      '4.7',
      'Prefer `this` only when a module manages a single primary object of that type; otherwise be descriptive.',
      'A single-resource module may use `this` for the primary object. A root '
      'module with many peers should use role nouns (`web`, `api`, `db`).',
      '''# bad - meaningless in a multi-resource root
resource "aws_instance" "this" {
  ami = data.aws_ami.web.id
}

resource "aws_instance" "this2" {
  ami = data.aws_ami.web.id
}''',
      '''# good - role nouns in the root; `this` inside a focused module
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

resource "aws_instance" "api" {
  ami = data.aws_ami.api.id
}''',
      suggestion=True,
    ),
    rule(
      '4.8',
      'Name module calls with nouns that describe the capability, not the source.',
      'Callers read `module.database`, not `module.terraform_aws_modules_rds`.',
      '''# bad
module "terraform-aws-modules-rds-aws" {
  source = "./modules/rds"
}''',
      '''# good
module "database" {
  source = "./modules/rds"
}''',
      enforced='terraform_naming_convention',
    ),
    rule(
      '4.9',
      'Keep data source names aligned with the resource names that consume them.',
      f'[Resource order]({STYLE}#resource-order) pairs data sources with consumers; '
      'matching names (`data.aws_ami.web` -> `aws_instance.web`) reduces chase time.',
      '''# bad
data "aws_ami" "latest_ubuntu_thing" {
  most_recent = true
}

resource "aws_instance" "web" {
  ami = data.aws_ami.latest_ubuntu_thing.id
}''',
      '''# good
data "aws_ami" "web" {
  most_recent = true
}

resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}''',
      suggestion=True,
    ),
    rule(
      '4.10',
      'Avoid encoding environment or account IDs into resource names when a variable or local already carries that context.',
      'Hardcoding `prod` into every name fights multi-environment roots. Compose '
      'from `local.name_suffix` instead (see locals chapter).',
      '''# bad
resource "aws_s3_bucket" "prod_logs_us_east_1" {
  bucket = "acme-prod-logs-us-east-1"
}''',
      '''# good
resource "aws_s3_bucket" "logs" {
  bucket = "${local.name_prefix}-logs"
}''',
      suggestion=True,
    ),
  ],
)

# Remaining chapters live in build_terraform_skill_chapters.py
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_terraform_skill_chapters import register_remaining

register_remaining(
  add,
  rule,
  STYLE,
  MOD_STRUCT,
  VARS_DOC,
  OUTS_DOC,
  LOCALS_DOC,
  COUNT_DOC,
  FOR_EACH_DOC,
  PROVIDERS_DOC,
  SETTINGS_DOC,
  TEST_DOC,
)


def render_chapter(filename: str, title: str, intro: str, rules: list[str]) -> str:
  header = (
    '<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->\n\n'
    f'# {title}\n\n'
    f'{intro.strip()}\n\n'
  )
  body = header + '\n'.join(rules)
  return body.rstrip() + '\n'


def main() -> None:
  OUT.mkdir(parents=True, exist_ok=True)
  for filename, (title, intro, rules) in CHAPTERS.items():
    path = OUT / filename
    path.write_text(render_chapter(filename, title, intro, rules), encoding='utf-8')
    print(f'wrote {path.relative_to(ROOT)} ({len(rules)} rules)')
  expected = sorted(CHAPTERS)
  print(f'total chapters: {len(expected)}')


if __name__ == '__main__':
  main()
