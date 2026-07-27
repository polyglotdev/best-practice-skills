#!/usr/bin/env python3
'''Structural and citation validators for best-practice-terraform.

Run from the repo root:

  python3 -m unittest tests.test_terraform_skill -v
'''

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'best-practice-terraform'
REFERENCES = SKILL / 'references'
SKILL_MD = SKILL / 'SKILL.md'
STYLE_ANCHORS = ROOT / 'docs' / 'reference-data' / 'terraform-style-anchors.txt'
TFLINT_RULES = ROOT / 'docs' / 'reference-data' / 'tflint-terraform-rules.txt'
TFLINT_HCL = ROOT / '.tflint.hcl'

# Rules chapter 15 / style-guide enforcement callouts require. The recommended
# preset covers most; the rest must be explicitly enabled in .tflint.hcl.
CHAPTER_15_TFLINT_RULES = (
  'terraform_documented_variables',
  'terraform_typed_variables',
  'terraform_documented_outputs',
  'terraform_module_pinned_source',
  'terraform_module_version',
  'terraform_required_version',
  'terraform_required_providers',
  'terraform_naming_convention',
  'terraform_unused_declarations',
  'terraform_comment_syntax',
  'terraform_standard_module_structure',
)

EXPECTED_CHAPTERS = [
  '01-formatting-and-tooling.md',
  '02-file-names-and-layout.md',
  '03-comments.md',
  '04-naming.md',
  '05-resource-order-and-blocks.md',
  '06-variables.md',
  '07-outputs.md',
  '08-local-values.md',
  '09-providers-and-aliasing.md',
  '10-count-and-for-each.md',
  '11-version-pinning.md',
  '12-modules-and-repository-structure.md',
  '13-state-hygiene-and-secrets.md',
  '14-environments-and-workflow.md',
  '15-linting-and-static-analysis.md',
]

RULE_HEADING_RE = re.compile(r'^## (\d+)\.(\d+) ', re.MULTILINE)
ENFORCED_BY_RE = re.compile(
  r'>\s*(?:\*\*)?Enforced by:\s*`?([^`\n*]+)`?(?:\*\*)?',
  re.IGNORECASE,
)
STYLE_LINK_RE = re.compile(
  r'https://developer\.hashicorp\.com/terraform/language/style#([a-zA-Z0-9][a-zA-Z0-9._-]*)'
)
EMOJI_RE = re.compile(
  '['
  '\U0001f300-\U0001f9ff'
  '\u2600-\u26ff'
  '\u2700-\u27bf'
  ']+'
)
EM_DASH_RE = re.compile('\u2014')

ALLOWED_TOOL_NAMES = {
  'terraform fmt',
  'terraform validate',
  'terraform test',
  'tflint',
}


def _load_lines(path: Path) -> set[str]:
  return {
    line.strip()
    for line in path.read_text(encoding='utf-8').splitlines()
    if line.strip() and not line.strip().startswith('#')
  }


class TestTerraformSkillStructure(unittest.TestCase):
  def test_skill_md_exists_and_under_500_lines(self) -> None:
    self.assertTrue(SKILL_MD.is_file(), 'SKILL.md missing')
    text = SKILL_MD.read_text(encoding='utf-8')
    self.assertIn('name: best-practice-terraform', text)
    self.assertLessEqual(len(text.splitlines()), 500)
    self.assertIn('terraform fmt', text)
    self.assertIn('developer.hashicorp.com/terraform/language/style', text)
    self.assertIsNone(EMOJI_RE.search(text))
    self.assertIsNone(EM_DASH_RE.search(text))

  def test_expected_chapters_exist(self) -> None:
    self.assertTrue(REFERENCES.is_dir(), 'references/ missing')
    missing = [name for name in EXPECTED_CHAPTERS if not (REFERENCES / name).is_file()]
    self.assertEqual(missing, [], f'missing chapters: {missing}')

  def test_no_unexpected_reference_files(self) -> None:
    found = sorted(p.name for p in REFERENCES.glob('*.md'))
    self.assertEqual(found, EXPECTED_CHAPTERS)

  def test_skill_md_indexes_every_chapter(self) -> None:
    text = SKILL_MD.read_text(encoding='utf-8')
    for name in EXPECTED_CHAPTERS:
      self.assertIn(f'references/{name}', text, f'SKILL.md missing link to {name}')

  def test_each_chapter_has_rules_and_structure(self) -> None:
    for name in EXPECTED_CHAPTERS:
      with self.subTest(chapter=name):
        text = (REFERENCES / name).read_text(encoding='utf-8')
        self.assertIn('Part of the `best-practice-terraform` skill', text)
        self.assertIsNone(EMOJI_RE.search(text), f'{name} contains emoji')
        self.assertIsNone(EM_DASH_RE.search(text), f'{name} contains em dash')
        rules = RULE_HEADING_RE.findall(text)
        self.assertGreaterEqual(len(rules), 8, f'{name} has fewer than 8 rules')
        chapter_num = int(name.split('-', 1)[0])
        for major, _minor in rules:
          self.assertEqual(int(major), chapter_num)
        self.assertGreaterEqual(text.count('> Why?'), 8)
        self.assertGreaterEqual(text.count('# bad'), 8)
        self.assertGreaterEqual(text.count('# good'), 8)


class TestTerraformSkillCitations(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    cls.style_anchors = _load_lines(STYLE_ANCHORS)
    cls.tflint_rules = _load_lines(TFLINT_RULES)

  def test_reference_data_files_exist(self) -> None:
    self.assertTrue(STYLE_ANCHORS.is_file())
    self.assertTrue(TFLINT_RULES.is_file())
    self.assertIn('code-formatting', self.style_anchors)
    self.assertIn('terraform_documented_variables', self.tflint_rules)

  def test_enforcement_callouts_are_honest(self) -> None:
    bad: list[str] = []
    for path in REFERENCES.glob('*.md'):
      text = path.read_text(encoding='utf-8')
      for match in ENFORCED_BY_RE.finditer(text):
        raw = match.group(1).strip().rstrip('.')
        for part in [p.strip() for p in re.split(r',\s*', raw) if p.strip()]:
          token = part.strip('()`*')
          lower = token.lower()
          if lower in ALLOWED_TOOL_NAMES:
            continue
          base = re.split(r'\s*\(', lower, maxsplit=1)[0].strip()
          if base in ALLOWED_TOOL_NAMES:
            continue
          if token not in self.tflint_rules and base not in self.tflint_rules:
            bad.append(f'{path.name}:{token}')
    self.assertEqual(bad, [], f'dishonest Enforced by citations: {bad[:30]}')

  def test_style_guide_anchors_resolve(self) -> None:
    broken: list[str] = []
    for path in REFERENCES.glob('*.md'):
      text = path.read_text(encoding='utf-8')
      for match in STYLE_LINK_RE.finditer(text):
        anchor = match.group(1)
        if anchor not in self.style_anchors:
          broken.append(f'{path.name}:#{anchor}')
    self.assertEqual(broken, [], f'broken style anchors: {broken[:30]}')


class TestTerraformSkillRegistration(unittest.TestCase):
  def test_readme_terraform_exists(self) -> None:
    readme = ROOT / 'README-terraform.md'
    self.assertTrue(readme.is_file())
    text = readme.read_text(encoding='utf-8')
    self.assertIn('best-practice-terraform', text)
    self.assertIn('terraform fmt', text)
    self.assertTrue(
      '2-space' in text or 'two spaces' in text or 'two-space' in text
    )
    self.assertIn('developer.hashicorp.com/terraform/language/style', text)
    self.assertIsNone(EMOJI_RE.search(text))
    self.assertIsNone(EM_DASH_RE.search(text))

  def test_root_readme_lists_terraform(self) -> None:
    text = (ROOT / 'README.md').read_text(encoding='utf-8')
    self.assertIn('best-practice-terraform', text)
    self.assertIn('README-terraform.md', text)

  def test_editorconfig_has_terraform_block(self) -> None:
    text = (ROOT / '.editorconfig').read_text(encoding='utf-8')
    self.assertTrue('[*.tf]' in text or '[*.{tf,tfvars}]' in text)
    block_match = re.search(
      r'\[\*\.\{tf,tfvars\}\]\n(.*?)(?:\n\[|\Z)',
      text,
      re.DOTALL,
    )
    if block_match is None:
      block_match = re.search(
        r'\[\*\.tf\]\n(.*?)(?:\n\[|\Z)',
        text,
        re.DOTALL,
      )
    self.assertIsNotNone(block_match, 'missing Terraform editorconfig block')
    assert block_match is not None
    self.assertIn('indent_size = 2', block_match.group(1))

  def test_tflint_hcl_ships_chapter_15_rules(self) -> None:
    self.assertTrue(TFLINT_HCL.is_file(), '.tflint.hcl missing at repo root')
    text = TFLINT_HCL.read_text(encoding='utf-8')
    self.assertIn('plugin "terraform"', text)
    self.assertIn('preset', text)
    self.assertIn('recommended', text)
    for rule in CHAPTER_15_TFLINT_RULES:
      self.assertIn(rule, text, f'.tflint.hcl missing {rule}')
    # Only the bundled terraform plugin; no provider rulesets.
    plugin_names = re.findall(r'plugin\s+"([^"]+)"', text)
    self.assertEqual(plugin_names, ['terraform'])
    # No Checkov/Trivy/tfsec config blocks (comments may name them as out of scope).
    self.assertIsNone(re.search(r'^\s*(plugin|rule)\s+"(checkov|trivy|tfsec)', text, re.M | re.I))

  def test_root_readme_mentions_tflint_hcl(self) -> None:
    text = (ROOT / 'README.md').read_text(encoding='utf-8')
    self.assertIn('.tflint.hcl', text)
    self.assertIn('best-practice-terraform', text)


if __name__ == '__main__':
  unittest.main()
