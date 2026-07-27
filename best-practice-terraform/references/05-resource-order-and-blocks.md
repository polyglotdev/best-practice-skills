<!-- Part of the `best-practice-terraform` skill. See SKILL.md for the index. -->

# 5. Resource Order & Blocks

Creation order is a graph, not a file order. [Resource order](https://developer.hashicorp.com/terraform/language/style#resource-order)
exists for humans: define data sources before the resources that reference them,
and keep a stable parameter order inside each resource block so reviews stay
predictable.

## 5.1 Define data sources before the resources that reference them.

> Why? The style guide says code should "build on itself" ([Resource order](https://developer.hashicorp.com/terraform/language/style#resource-order)).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - consumer first
resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}

data "aws_ami" "web" {
  most_recent = true
}

# good - dependency first
data "aws_ami" "web" {
  most_recent = true
}

resource "aws_instance" "web" {
  ami = data.aws_ami.web.id
}
```

## 5.2 Inside a resource, order parameters: count/for_each, arguments, nested blocks, lifecycle, depends_on.

> Why? Consistent parameter order is spelled out under [Resource order](https://developer.hashicorp.com/terraform/language/style#resource-order).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
resource "aws_instance" "web" {
  depends_on = [aws_iam_role_policy_attachment.web]
  ami        = data.aws_ami.web.id
  count      = 2
  lifecycle {
    create_before_destroy = true
  }
}

# good
resource "aws_instance" "web" {
  count = 2

  ami = data.aws_ami.web.id

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_iam_role_policy_attachment.web]
}
```

## 5.3 Prefer implicit dependencies via expressions over `depends_on`.

> Why? `depends_on` hides the real edge. Reference an attribute when you can; reserve `depends_on` for side effects Terraform cannot see.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - depends_on when an attribute reference suffices
resource "aws_instance" "web" {
  ami        = "ami-123"
  depends_on = [aws_security_group.web]
}

resource "aws_network_interface" "web" {
  subnet_id = aws_subnet.private.id
  security_groups = [aws_security_group.web.id]
}

# good - expression creates the edge
resource "aws_instance" "web" {
  ami = "ami-123"

  vpc_security_group_ids = [aws_security_group.web.id]
}
```

## 5.4 Group related nested blocks of the same family together.

> Why? [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting) allows mixing family blocks (for example block-device blocks on `aws_instance`) and otherwise discourages interleaving unrelated block types.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - unrelated nested blocks interleaved
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
}

# good - family of block-device blocks grouped
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
}
```

## 5.5 Separate nested blocks with blank lines except when grouping same-type siblings.

> Why? From [Code formatting](https://developer.hashicorp.com/terraform/language/style#code-formatting).
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - dense nested blocks
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port = 443
  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  certificate_arn = aws_acm_certificate.app.arn
}

# good
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  certificate_arn   = aws_acm_certificate.app.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

## 5.6 Colocate a data source with its primary consumer when the root is split across files.

> Why? [Resource order](https://developer.hashicorp.com/terraform/language/style#resource-order) recommends defining data sources alongside the resources that reference them.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - all data sources in data.tf, all consumers far away with no locality

# good - ami data source at the top of compute.tf above aws_instance.web
```

## 5.7 Do not rely on file name order for apply order.

> Why? Terraform builds a dependency graph. File order is for readers only; missing edges are fixed with references, not renaming files.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - assuming network.tf always applies before compute.tf
resource "aws_instance" "web" {
  # subnet_id omitted; hoping alphabetical apply saves you
  ami = "ami-123"
}

# good - explicit reference
resource "aws_instance" "web" {
  ami       = "ami-123"
  subnet_id = aws_subnet.private.id
}
```

## 5.8 Keep `lifecycle` blocks intentional and minimal.

> Why? Wide `ignore_changes` and habitual `create_before_destroy` without need hide drift. Prefer the smallest lifecycle surface that matches reality.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
lifecycle {
  ignore_changes = all
}

# good
lifecycle {
  ignore_changes = [tags["LastScaledAt"]]
}
```

## 5.9 Place `provider` meta-arguments with other meta-arguments near the top of the resource.

> Why? Aliased providers are selected per resource ([Provider aliasing](https://developer.hashicorp.com/terraform/language/style#provider-aliasing)); keep the meta-argument visible.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad
resource "aws_instance" "failover" {
  ami           = "ami-123"
  instance_type = "t3.micro"
  provider      = aws.west
}

# good
resource "aws_instance" "failover" {
  provider = aws.west

  ami           = "ami-123"
  instance_type = "t3.micro"
}
```

## 5.10 Avoid `provisioner` blocks unless there is no provider-native alternative.

> Why? The style guide points at meta-arguments carefully; provisioners are a last resort and complicate [secrets management](https://developer.hashicorp.com/terraform/language/style#secrets-management) and policy enforcement.
> **Suggestion.**
>
> Not mechanically enforced by a tool this skill ships.

```hcl
# bad - local-exec as default bootstrap
resource "aws_instance" "web" {
  ami = "ami-123"

  provisioner "local-exec" {
    command = "echo ${self.private_ip} > inventory"
  }
}

# good - bake config into the image or use cloud-init / SSM
resource "aws_instance" "web" {
  ami = "ami-123"

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    app_port = var.app_port
  })
}
```
