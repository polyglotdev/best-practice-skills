"""Structural and contract tests for the best-practice-python skill."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'best-practice-python'
REFERENCES = SKILL / 'references'
RUFF_TOML = ROOT / 'ruff.toml'
PYGUIDE_ANCHORS = ROOT / 'docs' / 'reference-data' / 'pyguide-anchors.txt'

EXPECTED_CHAPTERS = [
  '01-formatting-and-tooling.md',
  '02-source-files-and-layout.md',
  '03-naming.md',
  '04-docstrings.md',
  '05-imports-and-packages.md',
  '06-types-and-annotations.md',
  '07-functions.md',
  '08-classes.md',
  '09-dataclasses.md',
  '10-protocols-and-abcs.md',
  '11-generics-and-pep695.md',
  '12-exceptions.md',
  '13-context-managers.md',
  '14-iterators-and-generators.md',
  '15-comprehensions.md',
  '16-strings.md',
  '17-collections.md',
  '18-pattern-matching.md',
  '19-enums.md',
  '20-dates-and-times.md',
  '21-truthiness-and-comparisons.md',
  '22-properties-and-descriptors.md',
  '23-decorators.md',
  '24-concurrency.md',
  '25-logging.md',
  '26-testing.md',
  '27-asyncio-fundamentals.md',
  '28-structured-concurrency.md',
  '29-cancellation-and-timeouts.md',
  '30-async-context-and-iteration.md',
  '31-blocking-call-trap.md',
  '32-fastapi-app-structure.md',
  '33-fastapi-dependency-injection.md',
  '34-fastapi-request-response-models.md',
  '35-pydantic-validation-and-settings.md',
  '36-fastapi-error-handling.md',
  '37-fastapi-background-tasks.md',
  '38-fastapi-testing.md',
  '39-ruff-configuration.md',
  '40-type-checking.md',
  '41-project-layout-and-uv.md',
]

# Rules enabled by select = ["E4", "E7", "E9", "F"] in the shipped ruff.toml.
# Prefix "F" is Pyflakes only; FA/FAST/FBT/etc. are separate families.
ENABLED_RUFF_CODES = {
  'E401',
  'E402',
  'E701',
  'E702',
  'E703',
  'E711',
  'E712',
  'E713',
  'E714',
  'E721',
  'E722',
  'E731',
  'E741',
  'E742',
  'E743',
  'E902',
  'E999',
  'F401',
  'F402',
  'F403',
  'F404',
  'F405',
  'F406',
  'F407',
  'F501',
  'F502',
  'F503',
  'F504',
  'F505',
  'F506',
  'F507',
  'F508',
  'F509',
  'F521',
  'F522',
  'F523',
  'F524',
  'F525',
  'F541',
  'F601',
  'F602',
  'F621',
  'F622',
  'F631',
  'F632',
  'F633',
  'F634',
  'F701',
  'F702',
  'F704',
  'F706',
  'F707',
  'F722',
  'F811',
  'F821',
  'F822',
  'F823',
  'F841',
  'F842',
  'F901',
}

ENFORCED_BY_RE = re.compile(
  r'>\s*(?:\*\*)?Enforced by:\s*`?([^`\n*]+)`?(?:\*\*)?',
  re.IGNORECASE,
)
VIOLATION_RE = re.compile(r'\*\*Violation[^*]*\*\*', re.IGNORECASE)
RULE_HEADING_RE = re.compile(r'^## (\d+)\.(\d+) ', re.MULTILINE)
PYGUIDE_LINK_RE = re.compile(
  r'https://google\.github\.io/styleguide/pyguide\.html#([a-zA-Z0-9._-]+)'
)
EMOJI_RE = re.compile(
  '['
  '\U0001f300-\U0001f9ff'
  '\u2600-\u26ff'
  '\u2700-\u27bf'
  ']+'
)
EM_DASH_RE = re.compile('\u2014')


@pytest.fixture(scope='module')
def anchors() -> set[str]:
  return {
    line.strip()
    for line in PYGUIDE_ANCHORS.read_text(encoding='utf-8').splitlines()
    if line.strip()
  }


def test_ruff_toml_exists_with_house_style() -> None:
  assert RUFF_TOML.is_file()
  data = tomllib.loads(RUFF_TOML.read_text(encoding='utf-8'))
  assert data['line-length'] == 88
  assert data['indent-width'] == 2
  assert data['target-version'] == 'py312'
  assert data['lint']['select'] == ['E4', 'E7', 'E9', 'F']
  assert data['format']['quote-style'] == 'single'
  assert data['format']['indent-style'] == 'space'
  assert data['format']['docstring-code-format'] is True
  assert '.mypy_cache' in data['exclude']
  assert '.mymy_cache' not in data['exclude']


def test_skill_md_exists_and_under_500_lines() -> None:
  skill_md = SKILL / 'SKILL.md'
  assert skill_md.is_file()
  lines = skill_md.read_text(encoding='utf-8').splitlines()
  assert len(lines) <= 500
  text = '\n'.join(lines)
  assert 'name: best-practice-python' in text
  assert 'Python 3.12' in text
  assert 'FastAPI' in text
  assert 'ruff.toml' in text


def test_all_expected_chapters_exist() -> None:
  assert REFERENCES.is_dir()
  found = sorted(p.name for p in REFERENCES.glob('*.md'))
  assert found == EXPECTED_CHAPTERS


@pytest.mark.parametrize('chapter', EXPECTED_CHAPTERS)
def test_chapter_has_numbered_rules_and_structure(chapter: str) -> None:
  text = (REFERENCES / chapter).read_text(encoding='utf-8')
  assert text.startswith('<!-- Part of the `best-practice-python` skill.')
  assert '# ' in text[:200]
  rules = RULE_HEADING_RE.findall(text)
  assert len(rules) >= 12, f'{chapter} has only {len(rules)} rules'
  chapter_num = int(chapter.split('-', 1)[0])
  for major, _minor in rules:
    assert int(major) == chapter_num
  assert text.count('> Why?') >= 12
  assert text.count('# bad') >= 12 or text.count('# bad') + text.count('// bad') >= 12
  assert text.count('# good') >= 12 or text.count('# good') + text.count('// good') >= 12
  assert EMOJI_RE.search(text) is None
  assert EM_DASH_RE.search(text) is None


@pytest.mark.parametrize('chapter', EXPECTED_CHAPTERS)
def test_enforcement_callouts_only_cite_enabled_rules(chapter: str) -> None:
  text = (REFERENCES / chapter).read_text(encoding='utf-8')
  for match in ENFORCED_BY_RE.finditer(text):
    raw = match.group(1).strip()
    # Allow ruff format and comma-separated lists.
    parts = [p.strip() for p in re.split(r'[,/]', raw) if p.strip()]
    for part in parts:
      part = part.replace('ruff ', '').replace('Ruff ', '')
      if part.lower() in {'ruff format', 'format', 'ruff check'}:
        continue
      # Strip wording like "E711 (comparison to None)"
      code = part.split()[0].strip('()`*')
      if code.upper() == 'RUFF' or code.lower() == 'format':
        continue
      assert code in ENABLED_RUFF_CODES, (
        f'{chapter}: Enforced by cites {code!r} which is not enabled '
        f'by ruff.toml select={["E4", "E7", "E9", "F"]}'
      )


@pytest.mark.parametrize('chapter', EXPECTED_CHAPTERS)
def test_pyguide_anchors_resolve(chapter: str, anchors: set[str]) -> None:
  text = (REFERENCES / chapter).read_text(encoding='utf-8')
  for match in PYGUIDE_LINK_RE.finditer(text):
    anchor = match.group(1)
    assert anchor in anchors, f'{chapter}: unknown pyguide anchor #{anchor}'


def test_readme_python_exists() -> None:
  readme = ROOT / 'README-python.md'
  assert readme.is_file()
  text = readme.read_text(encoding='utf-8')
  assert 'best-practice-python' in text
  assert 'indent-width = 2' in text or 'indent-width=2' in text or '2-space' in text
  assert 'single quote' in text.lower() or "quote-style = 'single'" in text
  assert 'py312' in text or '3.12' in text
  assert EMOJI_RE.search(text) is None
  assert EM_DASH_RE.search(text) is None


def test_root_readme_lists_python() -> None:
  text = (ROOT / 'README.md').read_text(encoding='utf-8')
  assert 'best-practice-python' in text
  assert 'README-python.md' in text


def test_editorconfig_has_python_block() -> None:
  text = (ROOT / '.editorconfig').read_text(encoding='utf-8')
  assert '[*.py]' in text
  assert 'indent_size = 2' in text
