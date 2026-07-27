"""Shared helpers for rendering best-practice-python chapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCES = ROOT / 'best-practice-python' / 'references'


@dataclass(frozen=True)
class Rule:
  title: str
  why: str
  severity: str  # 'Violation' or 'Suggestion'
  enforced_by: str | None
  code: str  # python fenced block body with # bad / # good


def render_rule(chapter_num: int, index: int, rule: Rule) -> str:
  if rule.severity == 'Violation':
    assert rule.enforced_by, f'{rule.title} Violation needs enforced_by'
    label = f'**Violation  -  enforced by `{rule.enforced_by}`.**'
  else:
    label = '**Suggestion.**'
  return (
    f'## {chapter_num}.{index} {rule.title}\n'
    f'\n'
    f'> Why? {rule.why}\n'
    f'> {label}\n'
    f'\n'
    f'```python\n'
    f'{rule.code.rstrip()}\n'
    f'```\n'
  )


def write_chapter(
  filename: str,
  title: str,
  intro: str,
  tool_alignment: str,
  rules: list[Rule],
) -> Path:
  chapter_num = int(filename.split('-', 1)[0])
  body_parts = [
    '<!-- Part of the `best-practice-python` skill. See SKILL.md for the index. -->',
    '',
    f'# {chapter_num}. {title}',
    '',
    intro.rstrip(),
    '',
    f'**Tool alignment:** {tool_alignment.rstrip()}',
    '',
  ]
  for i, rule in enumerate(rules, start=1):
    body_parts.append(render_rule(chapter_num, i, rule))
  path = REFERENCES / filename
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text('\n'.join(body_parts).rstrip() + '\n', encoding='utf-8')
  return path
