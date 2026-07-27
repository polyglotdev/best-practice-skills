#!/usr/bin/env python3
'''Chapters 5-15 for best-practice-terraform (imported by build_terraform_skill.py).'''

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_remaining(
  add: Callable[..., None],
  rule: Callable[..., str],
  STYLE: str,
  MOD_STRUCT: str,
  VARS_DOC: str,
  OUTS_DOC: str,
  LOCALS_DOC: str,
  COUNT_DOC: str,
  FOR_EACH_DOC: str,
  PROVIDERS_DOC: str,
  SETTINGS_DOC: str,
  TEST_DOC: str,
) -> None:
  _ = (MOD_STRUCT, VARS_DOC, OUTS_DOC, LOCALS_DOC, COUNT_DOC, FOR_EACH_DOC, PROVIDERS_DOC, SETTINGS_DOC, TEST_DOC)

  add(
    '05-resource-order-and-blocks.md',
    '5. Resource Order & Blocks',
    f'''Creation order is a graph, not a file order. [Resource order]({STYLE}#resource-order)
exists for humans: define data sources before the resources that reference them,
and keep a stable parameter order inside each resource block so reviews stay
predictable.''',
    [
      rule(
        '5.1',
        'Define data sources before the resources that reference them.',
        f'The style guide says code should "build on itself" '
        f'([Resource order]({STYLE}#resource-order)).',
        '''# bad - consumer first
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

data "aws_ami" "web" {
  most_recent = true
}''',
        '''# good - dependency first
data "aws_ami" "web" {
  most_recent = true
}

resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}''',
        suggestion=True,
      ),
      rule(
        '5.2',
        'Inside a resource, order parameters: count/for_each, arguments, nested blocks, lifecycle, depends_on.',
        f'Consistent parameter order is spelled out under '
        f'[Resource order]({STYLE}#resource-order).',
        '''# bad
resource "aws_instance" "web" {
  depends_on = [aws_iam_role_policy_attachment.web]
  ami        = data.aws_ami.web.id
  count      = 2
  lifecycle {
    create_before_destroy = true
  }
}''',
        '''# good
resource "aws_instance" "web" {
  count = 2

  ami = data.aws_ami.web.id

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_iam_role_policy_attachment.web]
}''',
        suggestion=True,
      ),
      rule(
        '5.3',
        'Prefer implicit dependencies via expressions over `depends_on`.',
        '`depends_on` hides the real edge. Reference an attribute when you can; '
        'reserve `depends_on` for side effects Terraform cannot see.',
        '''# bad - depends_on when an attribute reference suffices
resource "aws_instance" "web" {
  ami        = "ami-123"
  depends_on = [aws_security_group.web]
}

resource "aws_network_interface" "web" {
  subnet_id = aws_subnet.private.id
  security_groups = [aws_security_group.web.id]
}''',
        '''# good - expression creates the edge
resource "aws_instance" "web" {
  ami = "ami-123"

  vpc_security_group_ids = [aws_security_group.web.id]
}''',
        suggestion=True,
      ),
      rule(
        '5.4',
        'Group related nested blocks of the same family together.',
        f'[Code formatting]({STYLE}#code-formatting) allows mixing family blocks '
        '(for example block-device blocks on `aws_instance`) and otherwise '
        'discourages interleaving unrelated block types.',
        '''# bad - unrelated nested blocks interleaved
resource "aws_instance" "web" {
  ami = "ami-123"

  root_block_device {
    volume_size = 20
  }

  credit_specification {
    cpu_credits = "standard"
  }

  ebs_block_device {
    device_name = "/dev/sdf"
    volume_size = 100
  }
}''',
        '''# good - family of block-device blocks grouped
resource "aws_instance" "web" {
  ami = "ami-123"

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_size = 20
  }

  ebs_block_device {
    device_name = "/dev/sdf"
    volume_size = 100
  }
}''',
        suggestion=True,
      ),
      rule(
        '5.5',
        'Separate nested blocks with blank lines except when grouping same-type siblings.',
        f'From [Code formatting]({STYLE}#code-formatting).',
        '''# bad - dense nested blocks
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port = 443
  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  certificate_arn = aws_acm_certificate.app.arn
}''',
        '''# good
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  certificate_arn   = aws_acm_certificate.app.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}''',
        suggestion=True,
      ),
      rule(
        '5.6',
        'Colocate a data source with its primary consumer when the root is split across files.',
        f'[Resource order]({STYLE}#resource-order) recommends defining data sources '
        'alongside the resources that reference them.',
        '''# bad - all data sources in data.tf, all consumers far away with no locality''',
        '''# good - ami data source at the top of compute.tf above aws_instance.web''',
        suggestion=True,
      ),
      rule(
        '5.7',
        'Do not rely on file name order for apply order.',
        'Terraform builds a dependency graph. File order is for readers only; '
        'missing edges are fixed with references, not renaming files.',
        '''# bad - assuming network.tf always applies before compute.tf
resource "aws_instance" "web" {
  # subnet_id omitted; hoping alphabetical apply saves you
  ami = "ami-123"
}''',
        '''# good - explicit reference
resource "aws_instance" "web" {
  ami       = "ami-123"
  subnet_id = aws_subnet.private.id
}''',
        suggestion=True,
      ),
      rule(
        '5.8',
        'Keep `lifecycle` blocks intentional and minimal.',
        'Wide `ignore_changes` and habitual `create_before_destroy` without need '
        'hide drift. Prefer the smallest lifecycle surface that matches reality.',
        '''# bad
lifecycle {
  ignore_changes = all
}''',
        '''# good
lifecycle {
  ignore_changes = [tags["LastScaledAt"]]
}''',
        suggestion=True,
      ),
      rule(
        '5.9',
        'Place `provider` meta-arguments with other meta-arguments near the top of the resource.',
        f'Aliased providers are selected per resource '
        f'([Provider aliasing]({STYLE}#provider-aliasing)); keep the meta-argument visible.',
        '''# bad
resource "aws_instance" "failover" {
  ami           = "ami-123"
  instance_type = "t3.micro"
  provider      = aws.west
}''',
        '''# good
resource "aws_instance" "failover" {
  provider = aws.west

  ami           = "ami-123"
  instance_type = "t3.micro"
}''',
        suggestion=True,
      ),
      rule(
        '5.10',
        'Avoid `provisioner` blocks unless there is no provider-native alternative.',
        f'The style guide points at meta-arguments carefully; provisioners are a '
        f'last resort and complicate [secrets management]({STYLE}#secrets-management) '
        'and policy enforcement.',
        '''# bad - local-exec as default bootstrap
resource "aws_instance" "web" {
  ami = "ami-123"

  provisioner "local-exec" {
    command = "echo ${self.private_ip} > inventory"
  }
}''',
        '''# good - bake config into the image or use cloud-init / SSM
resource "aws_instance" "web" {
  ami = "ami-123"

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    app_port = var.app_port
  })
}''',
        suggestion=True,
      ),
    ],
  )

  add(
    '06-variables.md',
    '6. Variables',
    f'''[Variables]({STYLE}#variables) make modules flexible and overuse makes
roots unreadable. Expose a variable when a setting changes between deployments.
Every variable needs a `type` and `description`. Optional variables get a
reasonable `default`. Sensitive inputs set `sensitive = true`. Prefer input
validation only for uniquely restrictive rules. Parameter order: type,
description, default, sensitive, validation blocks. See also the language
[input variables]({VARS_DOC}) docs.''',
    [
      rule(
        '6.1',
        'Include `type` and `description` on every variable.',
        f'Required by [Variables]({STYLE}#variables).',
        '''# bad
variable "instance_type" {}''',
        '''# good
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web tier"
}''',
        enforced='terraform_typed_variables',
      ),
      rule(
        '6.2',
        'Follow variable parameter order: type, description, default, sensitive, validation.',
        f'Spelled out under [Variables]({STYLE}#variables).',
        '''# bad
variable "db_password" {
  sensitive   = true
  default     = null
  description = "Database password"
  type        = string
}''',
        '''# good
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}''',
        suggestion=True,
      ),
      rule(
        '6.3',
        'Give optional variables a reasonable `default`.',
        f'[Variables]({STYLE}#variables): if optional, define a reasonable default.',
        '''# bad - optional in practice but required in the interface
variable "enable_monitoring" {
  type        = bool
  description = "Enable detailed monitoring"
}''',
        '''# good
variable "enable_monitoring" {
  type        = bool
  description = "Enable detailed monitoring"
  default     = true
}''',
        suggestion=True,
      ),
      rule(
        '6.4',
        'Mark passwords, private keys, and tokens with `sensitive = true`.',
        f'[Variables]({STYLE}#variables) notes Terraform still stores the value in '
        'state, but suppresses it in plan/apply UI.',
        '''# bad
variable "db_password" {
  type        = string
  description = "Database password"
}''',
        '''# good
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}''',
        suggestion=True,
      ),
      rule(
        '6.5',
        'Use `validation` blocks only for uniquely restrictive requirements.',
        f'Type checks already cover shape. Add validation when business rules go '
        f'further ([Variables]({STYLE}#variables)).',
        '''# bad - validation that only repeats the type system
variable "name" {
  type = string
  validation {
    condition     = var.name != null
    error_message = "name must be set"
  }
}''',
        '''# good - domain constraint
variable "web_instance_count" {
  type        = number
  description = "Number of web instances. This application requires at least two."

  validation {
    condition     = var.web_instance_count > 1
    error_message = "This application requires at least two web instances."
  }
}''',
        suggestion=True,
      ),
      rule(
        '6.6',
        'Do not expose a variable for every resource argument.',
        f'Overusing variables makes code hard to understand '
        f'([Variables]({STYLE}#variables)). Hardcode stable internals; variable-ize '
        'deployment differences.',
        '''# bad - variable for an immutable internal detail
variable "root_volume_type" {
  type    = string
  default = "gp3"
}''',
        '''# good - only settings that change per environment
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web tier"
}''',
        suggestion=True,
      ),
      rule(
        '6.7',
        'Prefer object/map types over long parallel variable lists for related settings.',
        'A single object keeps related knobs together and documents the shape once.',
        '''# bad
variable "db_name" { type = string }
variable "db_user" { type = string }
variable "db_port" { type = number }''',
        '''# good
variable "database" {
  type = object({
    name = string
    user = string
    port = number
  })
  description = "Application database connection settings"
}''',
        suggestion=True,
      ),
      rule(
        '6.8',
        'Document units and allowed values in the description when not obvious.',
        'Descriptions are the module contract. Callers should not need to open '
        'resources to learn that `disk_size` is GiB.',
        '''# bad
variable "db_disk_size" {
  type        = number
  description = "Disk size"
}''',
        '''# good
variable "db_disk_size" {
  type        = number
  description = "Disk size for the API database, in GiB"
  default     = 100
}''',
        enforced='terraform_documented_variables',
      ),
      rule(
        '6.9',
        'Do not set defaults for secrets.',
        'A default password is a committed secret. Require sensitive inputs '
        'explicitly at apply time.',
        '''# bad
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
  default     = "changeme"
}''',
        '''# good
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}''',
        suggestion=True,
      ),
      rule(
        '6.10',
        'Name boolean variables so `true` reads naturally (`enable_*`, `create_*`).',
        'Negative booleans (`disable_x = false`) invert mental models in conditionals.',
        '''# bad
variable "disable_monitoring" {
  type    = bool
  default = false
}''',
        '''# good
variable "enable_monitoring" {
  type        = bool
  description = "When true, enable detailed monitoring"
  default     = true
}''',
        suggestion=True,
      ),
    ],
  )

  add(
    '07-outputs.md',
    '7. Outputs',
    f'''[Outputs]({STYLE}#outputs) expose data on the CLI and to other
configurations. Provide a description for every output (and a type when your
Terraform version supports output types). Parameter order: type, description,
value, sensitive. Keep names as descriptive nouns with underscores. Prefer
exporting only what consumers need. Language reference:
[output values]({OUTS_DOC}).''',
    [
      rule(
        '7.1',
        'Include a `description` on every output.',
        f'Required by [Outputs]({STYLE}#outputs) and the style summary.',
        '''# bad
output "web_public_ip" {
  value = aws_instance.web.public_ip
}''',
        '''# good
output "web_public_ip" {
  description = "Public IP of the web instance"
  value       = aws_instance.web.public_ip
}''',
        enforced='terraform_documented_outputs',
      ),
      rule(
        '7.2',
        'Follow output parameter order: type, description, value, sensitive.',
        f'From [Outputs]({STYLE}#outputs).',
        '''# bad
output "web_public_ip" {
  value       = aws_instance.web.public_ip
  description = "Public IP of the web instance"
  type        = string
}''',
        '''# good
output "web_public_ip" {
  type        = string
  description = "Public IP of the web instance"
  value       = aws_instance.web.public_ip
}''',
        suggestion=True,
      ),
      rule(
        '7.3',
        'Mark outputs that echo secrets with `sensitive = true`.',
        'Otherwise plan and apply print them. State still stores the value.',
        '''# bad
output "db_password" {
  description = "Database password"
  value       = var.db_password
}''',
        '''# good
output "db_password" {
  description = "Database password"
  value       = var.db_password
  sensitive   = true
}''',
        suggestion=True,
      ),
      rule(
        '7.4',
        'Export stable identifiers consumers need; do not dump entire resources.',
        'Whole-resource outputs couple callers to provider schema churn.',
        '''# bad
output "web" {
  value = aws_instance.web
}''',
        '''# good
output "web_instance_id" {
  description = "EC2 instance ID for the web tier"
  value       = aws_instance.web.id
}''',
        suggestion=True,
      ),
      rule(
        '7.5',
        'Keep root-module outputs aligned with what other stacks actually consume.',
        f'[State sharing]({STYLE}#state-sharing) prefers narrow contracts over '
        'shipping the entire state.',
        '''# bad - twenty unused outputs "just in case"''',
        '''# good - vpc_id, private_subnet_ids, and nothing else until a consumer asks''',
        suggestion=True,
      ),
      rule(
        '7.6',
        'Use for-expressions to reshape maps of instances from `for_each` resources.',
        f'Shown in [Dynamic resource count]({STYLE}#dynamic-resource-count).',
        '''# bad - brittle index into a map
output "first_ip" {
  value = values(aws_instance.web)[0].private_ip
}''',
        '''# good
output "web_private_ips" {
  description = "Private IPs of the web instances"
  value = {
    for k, v in aws_instance.web : k => v.private_ip
  }
}''',
        suggestion=True,
      ),
      rule(
        '7.7',
        'Name outputs after the value, not after the resource type string.',
        'Callers want `vpc_id`, not `aws_vpc_main_id`.',
        '''# bad
output "aws_vpc_main_id" {
  value = aws_vpc.main.id
}''',
        '''# good
output "vpc_id" {
  description = "ID of the application VPC"
  value       = aws_vpc.main.id
}''',
        enforced='terraform_naming_convention',
      ),
      rule(
        '7.8',
        'Do not compute expensive derived values in outputs when a local already holds them.',
        'Outputs should usually reference resources, data sources, or locals - '
        'not hide a second copy of complex expressions.',
        '''# bad - duplicated composition
output "name_prefix" {
  value = "${var.project}-${var.environment}"
}''',
        '''# good
output "name_prefix" {
  description = "Prefix applied to resource names"
  value       = local.name_prefix
}''',
        suggestion=True,
      ),
      rule(
        '7.9',
        'Prefer lists/maps with stable keys over depending on resource list order.',
        '`count` index outputs reshuffle when you insert instances; `for_each` keys do not.',
        '''# bad
output "web_ip_0" {
  value = aws_instance.web[0].private_ip
}''',
        '''# good
output "web_ui_private_ip" {
  description = "Private IP of the web UI instance"
  value       = aws_instance.web["ui"].private_ip
}''',
        suggestion=True,
      ),
      rule(
        '7.10',
        'Document units and format in output descriptions when relevant.',
        'Downstream automation parses outputs; say whether an ARN, ID, or URL is returned.',
        '''# bad
output "connection_string" {
  value = aws_db_instance.main.endpoint
}''',
        '''# good
output "db_endpoint" {
  description = "host:port endpoint for the primary database"
  value       = aws_db_instance.main.endpoint
}''',
        enforced='terraform_documented_outputs',
      ),
    ],
  )

  add(
    '08-local-values.md',
    '8. Local Values',
    f'''[Local values]({STYLE}#local-values) DRY repeated expressions. Overuse
makes code harder to follow. Prefer locals for composed names and repeated
maps; keep one-off expressions inline. Define cross-file locals in
`locals.tf`; file-private locals at the top of that file. Language reference:
[locals]({LOCALS_DOC}).''',
    [
      rule(
        '8.1',
        'Use locals sparingly for values referenced multiple times.',
        f'HashiCorp warns that overuse hurts readability '
        f'([Local values]({STYLE}#local-values)).',
        '''# bad - local wrapping a single use
locals {
  web_ami = data.aws_ami.web.id
}

resource "aws_instance" "web" {
  ami = local.web_ami
}''',
        '''# good - inline single use; local for repeated composition
locals {
  name_suffix = "${var.region}-${var.environment}"
}

resource "aws_instance" "web" {
  ami = data.aws_ami.web.id

  tags = {
    Name = "web-${local.name_suffix}"
  }
}''',
        suggestion=True,
      ),
      rule(
        '8.2',
        'Put cross-file locals in `locals.tf`.',
        f'From [Local values]({STYLE}#local-values).',
        '''# bad - same local copied into network.tf and compute.tf''',
        '''# good - locals.tf
locals {
  name_suffix = "${var.region}-${var.environment}"
}''',
        suggestion=True,
      ),
      rule(
        '8.3',
        'Keep file-specific locals at the top of that file.',
        f'Allowed alternative in [Local values]({STYLE}#local-values).',
        '''# bad - local buried under resources in compute.tf
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

locals {
  web_user_data = file("${path.module}/user-data.sh")
}''',
        '''# good - locals first in compute.tf
locals {
  web_user_data = file("${path.module}/user-data.sh")
}

resource "aws_instance" "web" {
  ami       = data.aws_ami.web.id
  user_data = local.web_user_data
}''',
        suggestion=True,
      ),
      rule(
        '8.4',
        'Name locals with nouns and underscores.',
        f'Same naming rule as other objects ([Local values]({STYLE}#local-values)).',
        '''# bad
locals {
  x = "${var.region}-${var.environment}"
}''',
        '''# good
locals {
  name_suffix = "${var.region}-${var.environment}"
}''',
        enforced='terraform_naming_convention',
      ),
      rule(
        '8.5',
        'Prefer flat locals over deep nested local maps that require archaeology.',
        'Deep `local.a.b.c.d` chains are hard to grep. Compose smaller named locals.',
        '''# bad
locals {
  cfg = {
    web = {
      prod = { instance = "m5.large" }
    }
  }
}''',
        '''# good
locals {
  web_instance_type = var.environment == "prod" ? "m5.large" : "t3.micro"
}''',
        suggestion=True,
      ),
      rule(
        '8.6',
        'Do not use locals as a substitute for variables at a module boundary.',
        'If callers must change a value, it is a variable. Locals are private '
        'composition inside the module.',
        '''# bad - forcing callers to fork the module to change a "local"
locals {
  instance_type = "t3.micro"
}''',
        '''# good
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}''',
        suggestion=True,
      ),
      rule(
        '8.7',
        'Centralize common tags in a local (or provider `default_tags`) instead of repeating maps.',
        'Repeated tag maps drift. One local (or provider default) keeps them honest.',
        '''# bad - copy/paste tags on every resource
tags = {
  Project     = "billing"
  Environment = "prod"
  ManagedBy   = "terraform"
}''',
        '''# good
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}''',
        suggestion=True,
      ),
      rule(
        '8.8',
        'Avoid locals that only rename `var.*` without adding meaning.',
        '`local.environment = var.environment` adds indirection for no gain.',
        '''# bad
locals {
  environment = var.environment
}''',
        '''# good - reference var.environment directly, or compose
locals {
  name_prefix = "${var.project}-${var.environment}"
}''',
        suggestion=True,
      ),
      rule(
        '8.9',
        'Keep conditional expressions in locals when reused; inline when used once.',
        'Reuse is the bar. A one-off ternary next to its resource is clearer than '
        'a distant local.',
        '''# bad - single-use local three files away
locals {
  monitoring = var.enable_monitoring ? "enabled" : "disabled"
}''',
        '''# good - reused local
locals {
  monitoring_tag = var.enable_monitoring ? "enabled" : "disabled"
}''',
        suggestion=True,
      ),
      rule(
        '8.10',
        'Do not hide provider data lookups behind unexplained locals without comments.',
        'A local that is really "the production AMI ID from a data source" should '
        'read that way in the name or a comment.',
        '''# bad
locals {
  image = data.aws_ami.web.id
}''',
        '''# good
locals {
  web_ami_id = data.aws_ami.web.id
}''',
        suggestion=True,
      ),
    ],
  )

  _register_9_to_15(add, rule, STYLE, MOD_STRUCT, PROVIDERS_DOC, SETTINGS_DOC, TEST_DOC, COUNT_DOC, FOR_EACH_DOC)


def _register_9_to_15(
  add: Callable[..., None],
  rule: Callable[..., str],
  STYLE: str,
  MOD_STRUCT: str,
  PROVIDERS_DOC: str,
  SETTINGS_DOC: str,
  TEST_DOC: str,
  COUNT_DOC: str,
  FOR_EACH_DOC: str,
) -> None:
  add(
    '09-providers-and-aliasing.md',
    '9. Providers & Aliasing',
    f'''[Provider aliasing]({STYLE}#provider-aliasing) covers default and aliased
provider configurations. Always include a default provider configuration, define
providers in `providers.tf`, put the default first, and set `alias` as the first
argument of non-default blocks. Select aliases with the resource `provider`
meta-argument or the module `providers` map. Language reference:
[Providers]({PROVIDERS_DOC}).''',
    [
      rule(
        '9.1',
        'Always include a default (unaliased) provider configuration.',
        f'Required by [Provider aliasing]({STYLE}#provider-aliasing) and the '
        'code-style summary.',
        '''# bad - only aliased providers
provider "aws" {
  alias  = "east"
  region = "us-east-1"
}''',
        '''# good - default first
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "west"
  region = "us-west-2"
}''',
        suggestion=True,
      ),
      rule(
        '9.2',
        'Define all provider blocks in `providers.tf`.',
        f'[Provider aliasing]({STYLE}#provider-aliasing) / [File names]({STYLE}#file-names).',
        '''# bad - provider next to resources in main.tf
provider "aws" {
  region = var.aws_region
}''',
        '''# good - providers.tf only
provider "aws" {
  region = var.aws_region
}''',
        suggestion=True,
      ),
      rule(
        '9.3',
        'For non-default providers, set `alias` as the first parameter.',
        f'From [Provider aliasing]({STYLE}#provider-aliasing).',
        '''# bad
provider "aws" {
  region = "us-west-2"
  alias  = "west"
}''',
        '''# good
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}''',
        suggestion=True,
      ),
      rule(
        '9.4',
        'Select an aliased provider explicitly on resources that need it.',
        f'Shown in [Provider aliasing]({STYLE}#provider-aliasing).',
        '''# bad - unclear which provider region applies
resource "aws_instance" "failover" {
  ami = "ami-west"
}''',
        '''# good
resource "aws_instance" "failover" {
  provider = aws.west

  ami = "ami-west"
}''',
        suggestion=True,
      ),
      rule(
        '9.5',
        'Pass providers into modules with the `providers` meta-argument map.',
        f'Module example in [Provider aliasing]({STYLE}#provider-aliasing).',
        '''# bad - hoping child module somehow "knows" about aws.west''',
        '''# good
module "vpc_west" {
  source = "./modules/vpc"

  providers = {
    aws = aws.west
  }
}''',
        suggestion=True,
      ),
      rule(
        '9.6',
        'Do not hardcode long-lived static credentials in provider blocks.',
        f'[Secrets management]({STYLE}#secrets-management) prefers environment '
        'variables, dynamic credentials, or a secrets manager.',
        '''# bad
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIA..."
  secret_key = "..."
}''',
        '''# good - provider relies on the environment / SSO / IRSA
provider "aws" {
  region = var.aws_region
}''',
        suggestion=True,
      ),
      rule(
        '9.7',
        'Declare every provider in `required_providers` with source and version.',
        f'[Version pinning]({STYLE}#version-pinning) and '
        f'[settings]({SETTINGS_DOC}).',
        '''# bad
terraform {
  required_version = ">= 1.7"
}''',
        '''# good
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.34.0"
    }
  }
}''',
        enforced='terraform_required_providers',
      ),
      rule(
        '9.8',
        'Prefer provider `default_tags` (when supported) over repeating identical tag maps.',
        'Reduces drift between resources and keeps identity metadata consistent.',
        '''# bad - tags copy/pasted on every resource''',
        '''# good
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}''',
        suggestion=True,
      ),
      rule(
        '9.9',
        'Limit the number of aliases to real operational boundaries (regions, accounts).',
        'Each alias expands the mental graph. Do not create aliases for stylistic '
        'grouping inside one region.',
        '''# bad - alias per microservice in one region
provider "aws" {
  alias  = "payments"
  region = "us-east-1"
}''',
        '''# good - alias per region or account
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}''',
        suggestion=True,
      ),
      rule(
        '9.10',
        'Keep child modules free of `provider` blocks; only declare `required_providers`.',
        'Reusable modules must inherit configuration from the root.',
        '''# bad - modules/vpc/providers.tf
provider "aws" {
  region = "us-east-1"
}''',
        '''# good - modules/vpc/versions.tf
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
    ],
  )

  add(
    '10-count-and-for-each.md',
    '10. Count & for_each',
    f'''[Dynamic resource count]({STYLE}#dynamic-resource-count) covers `count`
and `for_each`. Use them sparingly. Prefer `count` when instances are nearly
identical; prefer `for_each` when instances need distinct keys/values. Conditional
creation with `count = cond ? 1 : 0` is common; comment non-obvious cases.
Language refs: [`count`]({COUNT_DOC}), [`for_each`]({FOR_EACH_DOC}).''',
    [
      rule(
        '10.1',
        'Use `count` and `for_each` sparingly.',
        f'Stated in the [code style summary]({STYLE}#code-style) and '
        f'[Dynamic resource count]({STYLE}#dynamic-resource-count).',
        '''# bad - meta-arguments wrapping every resource "for flexibility"''',
        '''# good - concrete resources until duplication is real''',
        suggestion=True,
      ),
      rule(
        '10.2',
        'Prefer `for_each` when instances need distinct identities; use `count` for near-identical replicas.',
        f'Guidance in [Dynamic resource count]({STYLE}#dynamic-resource-count).',
        '''# bad - count with lookup tables keyed by index
resource "aws_instance" "web" {
  count = length(var.web_names)
  tags = {
    Name = var.web_names[count.index]
  }
}''',
        '''# good
resource "aws_instance" "web" {
  for_each = toset(var.web_names)

  tags = {
    Name = "web_${each.key}"
  }
}''',
        suggestion=True,
      ),
      rule(
        '10.3',
        'Convert lists to sets with `toset` when using `for_each` over a list of strings.',
        f'Example pattern in [Dynamic resource count]({STYLE}#dynamic-resource-count).',
        '''# bad
resource "aws_instance" "web" {
  for_each = var.web_instances # list(string) - error
}''',
        '''# good
resource "aws_instance" "web" {
  for_each = toset(var.web_instances)
}''',
        suggestion=True,
      ),
      rule(
        '10.4',
        'Use `count = condition ? 1 : 0` for simple optional resources; comment intent.',
        f'Shown under [Dynamic resource count]({STYLE}#dynamic-resource-count).',
        '''# bad
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0
  ami   = data.aws_ami.web.id
}''',
        '''# good
# Optional metrics host for non-prod profiles.
resource "aws_instance" "metrics" {
  count = var.enable_metrics ? 1 : 0

  ami = data.aws_ami.web.id
}''',
        suggestion=True,
      ),
      rule(
        '10.5',
        'Address `for_each` instances by key, not by `values(...)[0]`.',
        'Keys are stable; list order is not a contract.',
        '''# bad
output "ui_ip" {
  value = values(aws_instance.web)[0].public_ip
}''',
        '''# good
output "web_ui_public_ip" {
  description = "Public IP of the web UI instance"
  value       = aws_instance.web["ui"].public_ip
}''',
        suggestion=True,
      ),
      rule(
        '10.6',
        'Do not stretch `count` across resources that later need stable identities.',
        'Inserting an element at index 0 forces replacements. `for_each` keys avoid that.',
        '''# bad - adding a name at the front reshuffles all indices
variable "web_names" {
  default = ["api", "ui"]
}''',
        '''# good - set/map keys
variable "web_instances" {
  type        = set(string)
  description = "Logical names for web instances"
  default     = ["api", "ui"]
}''',
        suggestion=True,
      ),
      rule(
        '10.7',
        'Avoid `count`/`for_each` driven by remote data that is unknown at plan time when possible.',
        'Unknown-at-plan counts force messy plans. Prefer explicit maps from variables.',
        '''# bad - for_each over a data source that appears during apply only''',
        '''# good - for_each over var.subnets supplied by the root''',
        suggestion=True,
      ),
      rule(
        '10.8',
        'When using `count`, reference with `[count.index]` carefully and prefer splat only for simple cases.',
        'Legacy splat alone does not replace clear indexing or `for_each`.',
        '''# bad - unclear which instance is special-cased
resource "aws_eip" "web" {
  instance = aws_instance.web.*.id[0]
}''',
        '''# good
resource "aws_eip" "web" {
  instance = aws_instance.web[0].id
}''',
        suggestion=True,
      ),
      rule(
        '10.9',
        'Do not mix `count` and `for_each` on the same resource block.',
        'Terraform rejects it; pick one model per resource.',
        '''# bad
resource "aws_instance" "web" {
  count    = 2
  for_each = toset(["a", "b"])
}''',
        '''# good
resource "aws_instance" "web" {
  for_each = toset(["a", "b"])
}''',
        suggestion=True,
      ),
      rule(
        '10.10',
        'Document why a module uses meta-arguments when the effect is non-obvious.',
        f'HashiCorp asks for comments when the effect is not obvious '
        f'([Dynamic resource count]({STYLE}#dynamic-resource-count)).',
        '''# bad - silent triple nested for_each in a shared module''',
        '''# good - module README + inline comment describing the key space''',
        suggestion=True,
      ),
    ],
  )

  add(
    '11-version-pinning.md',
    '11. Version Pinning',
    f'''[Version pinning]({STYLE}#version-pinning) prevents surprise upgrades.
Pin providers in `required_providers`, set `required_version` for the Terraform
CLI, pin registry modules with `version`, and commit
`.terraform.lock.hcl`. Language reference: [Terraform settings]({SETTINGS_DOC}).''',
    [
      rule(
        '11.1',
        'Set `required_version` in the root `terraform` block.',
        f'Recommended in [Version pinning]({STYLE}#version-pinning).',
        '''# bad
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}''',
        '''# good
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.34.0"
    }
  }
}''',
        enforced='terraform_required_version',
      ),
      rule(
        '11.2',
        'Pin provider versions in `required_providers`.',
        f'[Version pinning]({STYLE}#version-pinning) example pins exact provider versions.',
        '''# bad
aws = {
  source = "hashicorp/aws"
}''',
        '''# good
aws = {
  source  = "hashicorp/aws"
  version = "5.34.0"
}''',
        enforced='terraform_required_providers',
      ),
      rule(
        '11.3',
        'Pin registry module versions with the `version` argument.',
        f'Shown under [Version pinning]({STYLE}#version-pinning). Local modules ignore `version`.',
        '''# bad
module "vault_starter" {
  source = "hashicorp/vault-starter/aws"
}''',
        '''# good
module "vault_starter" {
  source  = "hashicorp/vault-starter/aws"
  version = "1.0.0"
}''',
        enforced='terraform_module_pinned_source',
      ),
      rule(
        '11.4',
        'Pin git module sources with a `?ref=` version tag.',
        'Unpinned branches move under you. Prefer tags over `main`.',
        '''# bad
module "network" {
  source = "git::https://github.com/example/terraform-modules.git//network"
}''',
        '''# good
module "network" {
  source = "git::https://github.com/example/terraform-modules.git//network?ref=v1.4.0"
}''',
        enforced='terraform_module_pinned_source',
      ),
      rule(
        '11.5',
        'Commit `.terraform.lock.hcl` for roots that providers are installed into.',
        f'[.gitignore]({STYLE}#gitignore) says always commit the dependency lock file.',
        '''# bad - lockfile gitignored''',
        '''# good - .terraform.lock.hcl tracked in git''',
        suggestion=True,
      ),
      rule(
        '11.6',
        'Prefer pessimistic constraints (`~>`) only when you knowingly accept minor updates.',
        'Exact pins maximize reproducibility; `~>` is a conscious trade for patches/minors.',
        '''# bad - floating latest
version = ">= 0"''',
        '''# good - exact or deliberate pessimistic constraint
version = "5.34.0"
# or
version = "~> 5.34"''',
        suggestion=True,
      ),
      rule(
        '11.7',
        'Do not leave `required_providers` empty when the module uses providers.',
        'Implicit legacy providers hide source addresses and break newer Terraform.',
        '''# bad - provider used with no required_providers entry''',
        '''# good - every provider sourced and versioned''',
        enforced='terraform_required_providers',
      ),
      rule(
        '11.8',
        'Upgrade providers deliberately with `terraform init -upgrade` and reviewed plans.',
        'Surprise upgrades in CI without a human-reviewed plan are incidents waiting to happen.',
        '''# bad - CI always runs init -upgrade on main''',
        '''# good - upgrade on a branch, review plan, merge lockfile''',
        suggestion=True,
      ),
      rule(
        '11.9',
        'Keep module `version` constraints as tight as your promotion process allows.',
        f'Pin major.minor for stability ([Version pinning]({STYLE}#version-pinning)).',
        '''# bad
version = ">= 1.0.0"''',
        '''# good
version = "1.0.0"''',
        enforced='terraform_module_version',
      ),
      rule(
        '11.10',
        'Record the minimum Terraform version that matches language features you use.',
        'Using `check` blocks or newer test features while allowing ancient '
        '`required_version` floors fails operators unpredictably.',
        '''# bad - uses terraform test / modern features with required_version = ">= 0.12"''',
        '''# good - required_version floor matches features actually used''',
        enforced='terraform_required_version',
      ),
    ],
  )

  add(
    '12-modules-and-repository-structure.md',
    '12. Modules & Repository Structure',
    f'''Modules group resources provisioned together. Follow
[module structure]({STYLE}#module-structure), store local modules under
`./modules/<module_name>` ([local modules]({STYLE}#local-modules)), publish
registry modules as `terraform-<PROVIDER>-<NAME>`
([module repository names]({STYLE}#module-repository-names)), and prefer
separating module code from live infrastructure roots
([repository structure]({STYLE}#repository-structure)). Also see
[Standard Module Structure]({MOD_STRUCT}).''',
    [
      rule(
        '12.1',
        'Store local child modules under `./modules/<module_name>`.',
        f'[Local modules]({STYLE}#local-modules).',
        '''# bad
module "vpc" {
  source = "./vpc"
}''',
        '''# good
module "vpc" {
  source = "./modules/vpc"
}''',
        suggestion=True,
      ),
      rule(
        '12.2',
        'Give published module repositories the `terraform-<PROVIDER>-<NAME>` name.',
        f'[Module repository names]({STYLE}#module-repository-names).',
        '''# bad - repo name: infra-helpers''',
        '''# good - repo name: terraform-aws-vpc''',
        suggestion=True,
      ),
      rule(
        '12.3',
        'Follow standard module file layout: main.tf, variables.tf, outputs.tf, README.',
        f'[Module structure]({STYLE}#module-structure) points at the standard module structure.',
        '''# bad - everything in one unlabeled file with no README''',
        '''# good
# modules/vpc/main.tf
# modules/vpc/variables.tf
# modules/vpc/outputs.tf
# modules/vpc/README.md''',
        enforced='terraform_standard_module_structure',
      ),
      rule(
        '12.4',
        'Prefer publishing shared modules to a registry over copy/pasting local clones.',
        f'[Local modules]({STYLE}#local-modules) recommends a registry when you can.',
        '''# bad - five roots each with a divergent copy of modules/vpc''',
        '''# good - one versioned registry module consumed by each root''',
        suggestion=True,
      ),
      rule(
        '12.5',
        'Separate module source repositories from live infrastructure configuration when practical.',
        f'[Repository structure]({STYLE}#repository-structure).',
        '''# bad - editing a shared module and prod root in one mixed commit with no version boundary''',
        '''# good - module repo tagged v1.2.0; live root bumps the module version''',
        suggestion=True,
      ),
      rule(
        '12.6',
        'If you use a monorepo, scope workspaces/roots to directories deliberately.',
        f'HashiCorp notes monorepos complicate CI and access control '
        f'([Repository structure]({STYLE}#repository-structure)).',
        '''# bad - one root that plans the entire company monorepo every PR''',
        '''# good - workspace rooted at networking/ or app/billing/''',
        suggestion=True,
      ),
      rule(
        '12.7',
        'Group module resources that must change together; do not build kitchen-sink modules.',
        f'Examples in [Module structure]({STYLE}#module-structure): networking stack, app stack.',
        '''# bad - module "everything" with VPC + SaaS DNS + paging + laptops''',
        '''# good - module "network" and module "application" composed at the root''',
        suggestion=True,
      ),
      rule(
        '12.8',
        'Expose a narrow variable/output contract; hide internals.',
        'Callers should not need to know every security group rule resource name.',
        '''# bad - output every intermediate SG rule ID''',
        '''# good - output vpc_id and private_subnet_ids only''',
        suggestion=True,
      ),
      rule(
        '12.9',
        'Include a module README that lists inputs, outputs, and examples.',
        f'[.gitignore]({STYLE}#gitignore) / workflow expectations include a README '
        'describing code, variables, and outputs.',
        '''# bad - undocumented module directory''',
        '''# good - README with purpose, example call, inputs, outputs''',
        suggestion=True,
      ),
      rule(
        '12.10',
        'Do not configure backends inside reusable child modules.',
        'Backends belong to roots/workspaces that own state.',
        '''# bad - modules/vpc/backend.tf with a terraform backend block''',
        '''# good - backend only in live roots (dev/, prod/, or workspaces)''',
        suggestion=True,
      ),
    ],
  )

  add(
    '13-state-hygiene-and-secrets.md',
    '13. State Hygiene & Secrets',
    f'''State holds sensitive data. The style guide's [.gitignore]({STYLE}#gitignore),
[state sharing]({STYLE}#state-sharing), and [secrets management]({STYLE}#secrets-management)
sections define what must never be committed, how to share data across states,
and how to keep credentials out of configuration. This chapter stays at that
language/workflow level - not a full cloud security audit.''',
    [
      rule(
        '13.1',
        'Never commit `terraform.tfstate` or `terraform.tfstate.*` backups.',
        f'[.gitignore]({STYLE}#gitignore).',
        '''# bad - state tracked in git''',
        '''# good - gitignore terraform.tfstate and terraform.tfstate.*''',
        suggestion=True,
      ),
      rule(
        '13.2',
        'Never commit the `.terraform` directory.',
        f'[.gitignore]({STYLE}#gitignore): providers and modules are downloaded locally.',
        '''# bad - .terraform/ committed''',
        '''# good - .terraform/ ignored; lockfile committed''',
        suggestion=True,
      ),
      rule(
        '13.3',
        'Never commit saved plan files from `terraform plan -out`.',
        f'[.gitignore]({STYLE}#gitignore).',
        '''# bad - tfplan checked into the repo''',
        '''# good - plan artifact stays in CI ephemeral storage''',
        suggestion=True,
      ),
      rule(
        '13.4',
        'Never commit `.tfvars` files that contain secrets.',
        f'[.gitignore]({STYLE}#gitignore).',
        '''# bad
# secrets.auto.tfvars
db_password = "hunter2"''',
        '''# good - secrets from the environment, CI store, or Vault provider''',
        suggestion=True,
      ),
      rule(
        '13.5',
        'Always commit Terraform code, `.terraform.lock.hcl`, `.gitignore`, and README.',
        f'[.gitignore]({STYLE}#gitignore) "Always commit" list.',
        '''# bad - lockfile ignored, README missing''',
        '''# good - code + lockfile + gitignore + README tracked''',
        suggestion=True,
      ),
      rule(
        '13.6',
        'Avoid sharing full state files between teams or stacks.',
        f'[State sharing]({STYLE}#state-sharing).',
        '''# bad - scp terraform.tfstate to another team''',
        '''# good - consume outputs via tfe_outputs or provider data sources''',
        suggestion=True,
      ),
      rule(
        '13.7',
        'Prefer provider data sources (or `tfe_outputs` on HCP Terraform) over remote-state coupling when practical.',
        f'[State sharing]({STYLE}#state-sharing) recommends `tfe_outputs` or '
        'provider data sources instead of wholesale state sharing.',
        '''# bad - every stack reads the entire remote state blob for one subnet ID''',
        '''# good - aws_subnet data source lookup by tags, or tfe_outputs for one value''',
        suggestion=True,
      ),
      rule(
        '13.8',
        'Configure remote state with encryption and locking for any shared environment.',
        'Local state is plaintext on disk and lacks locking '
        f'([Secrets management]({STYLE}#secrets-management)).',
        '''# bad - local state on a shared workstation for prod''',
        '''# good - remote backend with encryption and lock table / native locking''',
        suggestion=True,
      ),
      rule(
        '13.9',
        'Prefer dynamic provider credentials or a secrets manager over static keys in CI.',
        f'[Secrets management]({STYLE}#secrets-management).',
        '''# bad - long-lived AKIA keys in CI variables used for every plan''',
        '''# good - OIDC / dynamic credentials / Vault-backed short-lived tokens''',
        suggestion=True,
      ),
      rule(
        '13.10',
        'Remember `sensitive = true` does not remove values from state.',
        f'Called out under [Variables]({STYLE}#variables) and '
        f'[Secrets management]({STYLE}#secrets-management).',
        '''# bad - assuming sensitive variables never hit disk''',
        '''# good - treat state as sensitive, restrict backend ACLs, rotate on exposure''',
        suggestion=True,
      ),
    ],
  )

  add(
    '14-environments-and-workflow.md',
    '14. Environments, Workflow & Testing',
    f'''[Workflow style]({STYLE}#workflow-style) covers branching, multiple
environments, testing, and policy. Prefer GitHub flow
([branching strategy]({STYLE}#branching-strategy)), keep `main` as the source
of truth, isolate environments via workspaces or directories
([multiple environments]({STYLE}#multiple-environments)), write
[`terraform test`]({TEST_DOC}) for modules
([integration and unit testing]({STYLE}#integration-and-unit-testing)), and
store policies separately when using HCP policy enforcement
([Policy]({STYLE}#policy)).''',
    [
      rule(
        '14.1',
        'Use short-lived branches and pull requests (GitHub flow).',
        f'[Branching strategy]({STYLE}#branching-strategy).',
        '''# bad - committing straight to main for production changes''',
        '''# good - feature branch, PR, review, merge, delete branch''',
        suggestion=True,
      ),
      rule(
        '14.2',
        'Treat `main` as the source of truth for all environments.',
        f'[Multiple environments]({STYLE}#multiple-environments).',
        '''# bad - long-lived prod branch that diverges from main''',
        '''# good - main defines config; workspaces/dirs select env parameters''',
        suggestion=True,
      ),
      rule(
        '14.3',
        'Isolate environments with separate workspaces (HCP) or directories with separate state.',
        f'[Multiple environments]({STYLE}#multiple-environments).',
        '''# bad - one state file, switched by a lone var.environment, shared by all envs''',
        '''# good - prod/ and dev/ roots (or prod-* workspaces) each with own state''',
        suggestion=True,
      ),
      rule(
        '14.4',
        'Split large systems across multiple state files / workspaces by blast radius.',
        f'Recommended for larger codebases in [Multiple environments]({STYLE}#multiple-environments).',
        '''# bad - one state containing network + databases + every app''',
        '''# good - networking, database, and compute states composed via outputs/data''',
        suggestion=True,
      ),
      rule(
        '14.5',
        'Run speculative plans on pull requests before merge.',
        f'HCP Terraform speculative plans are called out under '
        f'[Branching strategy]({STYLE}#branching-strategy); Community Edition CI '
        'should `plan` on PRs without auto-apply.',
        '''# bad - apply from the PR branch without a reviewed plan''',
        '''# good - plan on PR, apply only from main after merge''',
        suggestion=True,
      ),
      rule(
        '14.6',
        'Write `terraform test` coverage for reusable modules.',
        f'[Integration and unit testing]({STYLE}#integration-and-unit-testing).',
        '''# bad - shared module with zero tests''',
        '''# good - tests/*.tftest.hcl exercising the module contract''',
        enforced='terraform test',
      ),
      rule(
        '14.7',
        'Do not confuse `terraform test` with variable validation / checks alone.',
        f'Tests validate module logic; validation/checks verify deployed assumptions '
        f'([Integration and unit testing]({STYLE}#integration-and-unit-testing)).',
        '''# bad - "we have validation blocks, so we do not need tests"''',
        '''# good - validation for inputs, tests for module behavior, checks for runtime''',
        suggestion=True,
      ),
      rule(
        '14.8',
        'Store Sentinel/OPA-style policies in a separate VCS repository from Terraform code.',
        f'[Policy]({STYLE}#policy).',
        '''# bad - ad-hoc policy files mixed into every app root without ownership''',
        '''# good - dedicated policy repo enforced by HCP Terraform''',
        suggestion=True,
      ),
      rule(
        '14.9',
        'Never auto-apply from unreviewed pull requests.',
        'Plans on PRs are speculative. Apply belongs to the protected trunk pipeline.',
        '''# bad - CI apply on every PR sync''',
        '''# good - plan on PR; apply on main with approvals''',
        suggestion=True,
      ),
      rule(
        '14.10',
        'Keep environment differences in tfvars / workspace variables, not forked module copies.',
        'Divergent copies of the same module per environment is how drift wins.',
        '''# bad - modules/vpc-dev and modules/vpc-prod as near-duplicates''',
        '''# good - one module; dev.tfvars / prod.tfvars (or workspace vars) supply deltas''',
        suggestion=True,
      ),
    ],
  )

  add(
    '15-linting-and-static-analysis.md',
    '15. Linting & Static Analysis',
    f'''Terraform has no built-in linter. The style guide recommends
[TFLint](https://github.com/terraform-linters/tflint) under
[Linting and static code analysis]({STYLE}#linting-and-static-code-analysis).
This skill treats TFLint's `terraform` ruleset as the honest mechanical layer
alongside `terraform fmt` and `terraform validate`. Broader IaC scanners such
as Checkov or Trivy are useful organization policy tools when *you* configure
them; this repo does not ship their configs, so this chapter does not pretend
they enforce rules here.''',
    [
      rule(
        '15.1',
        'Run TFLint in CI with the Terraform ruleset enabled.',
        f'HashiCorp points at TFLint explicitly '
        f'([Linting and static code analysis]({STYLE}#linting-and-static-code-analysis)).',
        '''# bad - only fmt in CI''',
        '''# good - fmt -check, validate, tflint --format compact''',
        enforced='tflint',
      ),
      rule(
        '15.2',
        'Enable `terraform_documented_variables` and `terraform_typed_variables`.',
        'These map directly to the style guide variable requirements.',
        '''# bad - variables without type/description surviving review''',
        '''# good - TFLint fails the build on missing type/description''',
        enforced='terraform_documented_variables',
      ),
      rule(
        '15.3',
        'Enable `terraform_documented_outputs`.',
        'Outputs need descriptions per the style guide.',
        '''# bad - bare output blocks''',
        '''# good - documented outputs enforced in CI''',
        enforced='terraform_documented_outputs',
      ),
      rule(
        '15.4',
        'Enable `terraform_module_pinned_source` / `terraform_module_version`.',
        'Unpinned modules violate [version pinning]({STYLE}#version-pinning).',
        '''# bad - registry module with no version''',
        '''# good - version pinned; TFLint guards regressions''',
        enforced='terraform_module_pinned_source',
      ),
      rule(
        '15.5',
        'Enable `terraform_required_version` and `terraform_required_providers`.',
        'Roots without constraints drift across laptops and CI images.',
        '''# bad - implicit providers, no required_version''',
        '''# good - constraints present; TFLint enforces''',
        enforced='terraform_required_version',
      ),
      rule(
        '15.6',
        'Enable `terraform_naming_convention` aligned to snake_case nouns.',
        'Matches [resource naming]({STYLE}#resource-naming).',
        '''# bad - WebAPI-style names''',
        '''# good - snake_case names; TFLint naming rule on''',
        enforced='terraform_naming_convention',
      ),
      rule(
        '15.7',
        'Enable `terraform_unused_declarations` to keep roots lean.',
        'Dead variables and locals accumulate quickly in shared modules.',
        '''# bad - unused variable left "for later"''',
        '''# good - unused declarations fail CI''',
        enforced='terraform_unused_declarations',
      ),
      rule(
        '15.8',
        'Enable `terraform_comment_syntax` so `#` stays idiomatic.',
        f'Aligns with [Comments]({STYLE}#comments).',
        '''# bad - // comments creeping back in''',
        '''# good - TFLint rejects non-idiomatic comment syntax when configured''',
        enforced='terraform_comment_syntax',
      ),
      rule(
        '15.9',
        'Treat Checkov/Trivy/tfsec as optional org policy layers, not as this skill\'s defaults.',
        'The HashiCorp style guide names TFLint. Other scanners are valuable for '
        'cloud misconfiguration policy when your org pins and owns their configs. '
        'Do not cite them as `Enforced by` unless that config actually exists in '
        'the target repo.',
        '''# bad - claiming "Enforced by: checkov" with no checkov config in the repo''',
        '''# good - document org-required scanners in the service repo; keep this skill honest''',
        suggestion=True,
      ),
      rule(
        '15.10',
        'Keep the CI order cheap-to-expensive: fmt check, validate, tflint, then plan/tests.',
        'Fail fast on formatting before spending minutes on providers and plans.',
        '''# bad - plan first, fmt last''',
        '''# good - fmt -check -> validate -> tflint -> test/plan''',
        enforced='terraform fmt',
      ),
    ],
  )
