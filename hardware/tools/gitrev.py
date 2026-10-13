"""Revision stamp for generated review/doc artifacts.

`git describe --dirty` would always say -dirty here: the generated outputs
(docs/review/, DATASHEET.md, docs/img, docs/3d, fab/) are tracked, so each
generator sees its siblings' fresh output as uncommitted. Only changes to
anything ELSE (the sources) count as dirty.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ("docs/review", "DATASHEET.md", "docs/img", "docs/3d", "fab")


def gitrev():
    run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                                    text=True).stdout.strip()
    rev = run("describe", "--tags", "--always")
    dirty = run("status", "--porcelain", "--", ".", *[f":!{g}" for g in GENERATED])
    return rev + ("-dirty" if dirty else "")
