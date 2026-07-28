'''Regression: go-style-guide must require secret redaction in audit output.

Snyk ToxicSkills W007 failed go-style-guide because SKILL.md instructed the
agent to reproduce audited source in fenced blocks after grep/rg, which can
echo embedded credentials. These tests keep the redaction contract in place.
'''

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / 'go-style-guide' / 'SKILL.md'

# Unqualified instruction that triggered W007 on skills.sh.
UNSAFE_OFFENDING_CODE = re.compile(
  r'Show the offending code in a small fenced block',
  re.IGNORECASE,
)

REQUIRED_PHRASES = (
  'redact',
  '[REDACTED',
  'API keys',
  'tokens',
  'passwords',
)


class TestGoStyleGuideCredentialSafety(unittest.TestCase):
  def setUp(self) -> None:
    self.text = SKILL_MD.read_text(encoding='utf-8')

  def test_skill_md_exists(self) -> None:
    self.assertTrue(SKILL_MD.is_file(), f'missing {SKILL_MD}')

  def test_no_unqualified_offending_code_instruction(self) -> None:
    match = UNSAFE_OFFENDING_CODE.search(self.text)
    self.assertIsNone(
      match,
      'SKILL.md must not instruct agents to dump offending source into '
      'fenced blocks without a redaction requirement (Snyk W007).',
    )

  def test_requires_credential_redaction(self) -> None:
    lowered = self.text.lower()
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase.lower() not in lowered]
    self.assertEqual(
      missing,
      [],
      'go-style-guide/SKILL.md must require redacting credentials in audit '
      f'output; missing: {missing}',
    )

  def test_has_credential_safety_section(self) -> None:
    self.assertRegex(
      self.text,
      r'(?im)^##\s+Credential safety\s*$',
      'Expected a "## Credential safety" section in go-style-guide/SKILL.md',
    )


if __name__ == '__main__':
  unittest.main()
