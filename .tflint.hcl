# TFLint configuration for best-practice-terraform.
# Aligns with HashiCorp's Terraform Style Guide linting guidance and
# chapter 15 (Linting & Static Analysis). Uses the bundled
# tflint-ruleset-terraform plugin only - this file does not enable AWS/GCP
# provider rulesets or Checkov/Trivy/tfsec.
#
# Drop this file at a Terraform repo root and run:
#   tflint --init
#   tflint --format compact

tflint {
  required_version = ">= 0.50"
}

config {
  format           = "compact"
  call_module_type = "local"
}

plugin "terraform" {
  enabled = true
  # recommended covers typed variables, required_version/providers,
  # module pins/versions, unused declarations, and other language defaults.
  preset = "recommended"
}

# ---------------------------------------------------------------------------
# Style-guide rules chapter 15 requires that are off in "recommended"
# ---------------------------------------------------------------------------

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

rule "terraform_comment_syntax" {
  enabled = true
}

rule "terraform_standard_module_structure" {
  enabled = true
}

# ---------------------------------------------------------------------------
# Chapter 15 / enforcement-callout rules already in "recommended", restated
# here so the enabled set is discoverable without reading the preset docs.
# ---------------------------------------------------------------------------

rule "terraform_typed_variables" {
  enabled = true
}

rule "terraform_module_pinned_source" {
  enabled = true
}

rule "terraform_module_version" {
  enabled = true
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}
