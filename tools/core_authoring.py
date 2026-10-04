"""Shared neutral frontmatter authoring for runtime-specialized mp-skills."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'inventory.json').read_text())
SLOTS = frozenset('files delegation task_tracking history skill_loading skill_maintenance configuration integrations persistent_work web setup'.split())


def save(name, description, body, *, compatibility=None):
    """Write one standard-format authored core entrypoint, never installed skills."""
    assert name in {e['name'] for e in DATA['skills']}, name
    assert description and len(description) <= 60, description
    lines = ['---', 'name: ' + name, 'description: ' + json.dumps(description),
             'license: MIT',
             'metadata:',
             '  author: "Matt Pocock (original), tea24864 (port)"',
             '  version: "0.1.0"',
             '  source-revision: ' + json.dumps(DATA['revision']),
             '---', '', body.rstrip(), '']
    path = ROOT / 'core/skills' / name / 'SKILL.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')
    return path


def save_reference(name, rel, content):
    """Write one carrier/reference file inside a core skill directory."""
    path = ROOT / 'core/skills' / name / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path
