#!/usr/bin/env python3
'''Regression tests: skill chapters must not embed scanner-tripping secret literals.

GitHub push protection blocked this repo for a didactic Stripe live-key example
in best-practice-java/references/33-spring-configuration.md. These tests keep
documentation placeholders from matching vendor secret detectors again.
'''

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# High-confidence Stripe secret key shape (live or test). Truncated examples
# that stop before 16 alphanumerics (e.g. sk_live_...) are allowed.
STRIPE_SECRET_KEY_RE = re.compile(r'sk_(?:live|test)_[A-Za-z0-9]{16,}')

# AWS access key id shape.
AWS_ACCESS_KEY_RE = re.compile(r'AKIA[0-9A-Z]{16}')

# GitHub PAT (classic) shape.
GITHUB_PAT_RE = re.compile(r'ghp_[A-Za-z0-9]{36}')

SCAN_GLOBS = (
  'best-practice-*/references/**/*.md',
  'go-style-guide/references/**/*.md',
  'README*.md',
  'docs/**/*.md',
)


def iter_scanned_files() -> list[Path]:
  files: set[Path] = set()
  for pattern in SCAN_GLOBS:
    files.update(ROOT.glob(pattern))
  return sorted(files)


class TestNoSecretLiterals(unittest.TestCase):
  def test_no_stripe_secret_key_literals(self) -> None:
    hits = self._hits(STRIPE_SECRET_KEY_RE)
    self.assertEqual(
      hits,
      [],
      'Stripe-like secret literals trip GitHub push protection; use '
      'REDACTED_STRIPE_SECRET_KEY or sk_live_<redacted> instead:\n'
      + '\n'.join(hits),
    )

  def test_no_aws_access_key_literals(self) -> None:
    hits = self._hits(AWS_ACCESS_KEY_RE)
    self.assertEqual(hits, [], 'AWS access-key-shaped literals found:\n' + '\n'.join(hits))

  def test_no_github_pat_literals(self) -> None:
    hits = self._hits(GITHUB_PAT_RE)
    self.assertEqual(hits, [], 'GitHub PAT-shaped literals found:\n' + '\n'.join(hits))

  def _hits(self, pattern: re.Pattern[str]) -> list[str]:
    found: list[str] = []
    for path in iter_scanned_files():
      text = path.read_text(encoding='utf-8')
      for match in pattern.finditer(text):
        line_no = text.count('\n', 0, match.start()) + 1
        found.append(f'{path.relative_to(ROOT)}:{line_no}:{match.group(0)}')
    return found


if __name__ == '__main__':
  unittest.main()
