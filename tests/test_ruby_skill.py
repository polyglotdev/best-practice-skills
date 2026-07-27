#!/usr/bin/env python3
'''Structural and citation validators for best-practice-ruby.

Run from the repo root:

  python3 -m unittest tests.test_ruby_skill -v
'''

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'best-practice-ruby'
REFERENCES = SKILL / 'references'
SKILL_MD = SKILL / 'SKILL.md'
RUBOCOP_YML = ROOT / '.rubocop.yml'
COPS_CATALOGUE = ROOT / 'docs' / 'reference-data' / 'rubocop-cops.txt'
ENABLED_DEFAULT = ROOT / 'docs' / 'reference-data' / 'rubocop-enabled-default.txt'
RUBY_ANCHORS = ROOT / 'docs' / 'reference-data' / 'ruby-style-anchors.txt'
RAILS_ANCHORS = ROOT / 'docs' / 'reference-data' / 'rails-style-anchors.txt'

EXPECTED_CHAPTERS = [
  '01-formatting-and-tooling.md',
  '02-source-files-and-structure.md',
  '03-naming.md',
  '04-comments-and-yard.md',
  '05-classes-and-modules.md',
  '06-methods-and-arguments.md',
  '07-keyword-arguments-and-forwarding.md',
  '08-blocks-procs-and-lambdas.md',
  '09-modules-mixins-and-refinements.md',
  '10-metaprogramming-discipline.md',
  '11-exceptions-and-errors.md',
  '12-strings-and-symbols.md',
  '13-collections-and-enumerable.md',
  '14-hashes-and-keywords.md',
  '15-control-flow.md',
  '16-pattern-matching.md',
  '17-struct-data-and-value-objects.md',
  '18-numeric-types.md',
  '19-regular-expressions.md',
  '20-dates-and-times.md',
  '21-io-and-resources.md',
  '22-concurrency-and-ractors.md',
  '23-logging.md',
  '24-testing.md',
  '25-rails-application-structure.md',
  '26-activerecord-models.md',
  '27-activerecord-queries.md',
  '28-migrations-and-schema.md',
  '29-controllers-and-strong-params.md',
  '30-routing.md',
  '31-views-and-helpers.md',
  '32-jobs-and-activejob.md',
  '33-mailers.md',
  '34-service-objects.md',
  '35-rails-testing.md',
  '36-rails-security-and-footguns.md',
  '37-rubocop-configuration.md',
]

RULE_HEADER = re.compile(r'^## (\d+)\.(\d+) ', re.MULTILINE)
ENFORCED_BY = re.compile(
  r'(?:Enforced by:|enforced by)\s*`?([A-Za-z]+/[A-Za-z0-9]+)`?',
  re.IGNORECASE,
)
STYLE_GUIDE_LINK = re.compile(
  r'https://(?:rails\.)?rubystyle\.guide/(#[a-zA-Z0-9][a-zA-Z0-9._-]*)?'
)
FRONTMATTER = re.compile(r'^---\nname:\s*best-practice-ruby\n', re.MULTILINE)


def _load_lines(path: Path) -> set[str]:
  return {
    line.strip()
    for line in path.read_text(encoding='utf-8').splitlines()
    if line.strip() and not line.strip().startswith('#')
  }


def _enabled_cops_from_yml(text: str, defaults: set[str]) -> set[str]:
  '''Approximate effective enabled set: defaults, minus Enabled: false, plus Enabled: true.'''
  enabled = set(defaults)
  # Disable whole departments when a department key sets Enabled: false
  dept_disable = re.findall(
    r'^([A-Z][A-Za-z]+):\n(?:[ \t]+[^\n]+\n)*?[ \t]+Enabled:\s*false',
    text,
    re.MULTILINE,
  )
  for dept in dept_disable:
    enabled = {c for c in enabled if not c.startswith(dept + '/')}

  for match in re.finditer(
    r'^([A-Z][A-Za-z]+/[A-Za-z0-9]+):\n((?:[ \t]+[^\n]+\n)*)',
    text,
    re.MULTILINE,
  ):
    name, body = match.group(1), match.group(2)
    if re.search(r'^\s+Enabled:\s*false\s*$', body, re.MULTILINE):
      enabled.discard(name)
    elif re.search(r'^\s+Enabled:\s*true\s*$', body, re.MULTILINE):
      enabled.add(name)
  return enabled


class TestRubySkillStructure(unittest.TestCase):
  def test_skill_md_exists_with_frontmatter(self) -> None:
    self.assertTrue(SKILL_MD.is_file(), 'SKILL.md missing')
    text = SKILL_MD.read_text(encoding='utf-8')
    self.assertRegex(text, FRONTMATTER)
    self.assertLessEqual(len(text.splitlines()), 500)

  def test_expected_chapters_exist(self) -> None:
    self.assertTrue(REFERENCES.is_dir(), 'references/ missing')
    missing = [name for name in EXPECTED_CHAPTERS if not (REFERENCES / name).is_file()]
    self.assertEqual(missing, [], f'missing chapters: {missing}')

  def test_no_unexpected_reference_files(self) -> None:
    found = sorted(p.name for p in REFERENCES.glob('*.md'))
    self.assertEqual(found, EXPECTED_CHAPTERS)

  def test_each_chapter_has_rules_and_header(self) -> None:
    for name in EXPECTED_CHAPTERS:
      with self.subTest(chapter=name):
        text = (REFERENCES / name).read_text(encoding='utf-8')
        self.assertIn('Part of the `best-practice-ruby` skill', text)
        rules = RULE_HEADER.findall(text)
        self.assertGreaterEqual(len(rules), 8, f'{name} has fewer than 8 rules')
        chapter_num = int(name.split('-', 1)[0])
        for major, _minor in rules:
          self.assertEqual(int(major), chapter_num)

  def test_skill_md_indexes_every_chapter(self) -> None:
    text = SKILL_MD.read_text(encoding='utf-8')
    for name in EXPECTED_CHAPTERS:
      self.assertIn(f'references/{name}', text, f'SKILL.md missing link to {name}')


class TestRubySkillCitations(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    cls.cops = _load_lines(COPS_CATALOGUE)
    cls.defaults = _load_lines(ENABLED_DEFAULT)
    cls.ruby_anchors = _load_lines(RUBY_ANCHORS)
    cls.rails_anchors = _load_lines(RAILS_ANCHORS)
    cls.rubocop_yml = RUBOCOP_YML.read_text(encoding='utf-8')
    cls.enabled = _enabled_cops_from_yml(cls.rubocop_yml, cls.defaults)

  def test_rubocop_yml_exists(self) -> None:
    self.assertTrue(RUBOCOP_YML.is_file())
    self.assertIn('TargetRubyVersion: 4.0', self.rubocop_yml)
    self.assertIn('rubocop-rails', self.rubocop_yml)
    self.assertIn('rubocop-performance', self.rubocop_yml)
    self.assertIn('rubocop-rspec', self.rubocop_yml)

  def test_enforced_by_cops_exist_and_are_enabled(self) -> None:
    unknown: list[str] = []
    disabled: list[str] = []
    for path in REFERENCES.glob('*.md'):
      text = path.read_text(encoding='utf-8')
      for cop in ENFORCED_BY.findall(text):
        if cop not in self.cops:
          unknown.append(f'{path.name}:{cop}')
        elif cop not in self.enabled:
          disabled.append(f'{path.name}:{cop}')
    self.assertEqual(unknown, [], f'unknown cops: {unknown[:20]}')
    self.assertEqual(disabled, [], f'cops not effectively enabled: {disabled[:20]}')

  def test_style_guide_anchors_are_harvested(self) -> None:
    broken: list[str] = []
    for path in REFERENCES.glob('*.md'):
      text = path.read_text(encoding='utf-8')
      for match in STYLE_GUIDE_LINK.finditer(text):
        url = match.group(0)
        frag = match.group(1)
        if not frag:
          continue
        anchor = frag.lstrip('#')
        if 'rails.rubystyle.guide' in url:
          if anchor not in self.rails_anchors:
            broken.append(f'{path.name}:rails#{anchor}')
        else:
          if anchor not in self.ruby_anchors:
            broken.append(f'{path.name}:ruby#{anchor}')
    self.assertEqual(broken, [], f'broken anchors: {broken[:30]}')


if __name__ == '__main__':
  unittest.main()
