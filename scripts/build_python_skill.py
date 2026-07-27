#!/usr/bin/env python3
"""Generate best-practice-python reference chapters."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from scripts.python_skill.chapters_01_10 import build as build_01_10  # noqa: E402
from scripts.python_skill.chapters_06_41 import build as build_06_10  # noqa: E402
from scripts.python_skill.chapters_11_26 import build as build_11_26  # noqa: E402
from scripts.python_skill.chapters_27_41 import build as build_27_41  # noqa: E402


def main() -> None:
  build_01_10()
  build_06_10()
  build_11_26()
  build_27_41()
  refs = sorted((ROOT / 'best-practice-python' / 'references').glob('*.md'))
  print(f'wrote {len(refs)} chapters')


if __name__ == '__main__':
  main()
