"""Whole-source contract tests for the mp-skills authored core.

Adapted from the pstack-generic test_core discipline: invariants that must hold
over the entire authored source regardless of adapter, checked against the
committed core tree, inventory, provenance records and upstream snapshot.
"""
from pathlib import Path
import difflib
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'core' / 'skills'
UPSTREAM = ROOT / 'upstream' / 'mattpocock-skills'
PIN = 'd81f3a183412e71a5b1e84ca21bc1a35eea03a60'
SLOTS = {'files', 'delegation', 'task_tracking', 'history', 'skill_loading',
         'skill_maintenance', 'configuration', 'integrations', 'persistent_work',
         'web', 'setup'}
UP_NAMES = sorted(['ask-matt', 'code-review', 'codebase-design', 'diagnosing-bugs',
                   'domain-modeling', 'grill-with-docs', 'implement', 'implement-spec',
                   'improve-codebase-architecture', 'pr', 'prototype', 'research',
                   'retro', 'setup-matt-pocock-skills', 'tdd', 'to-spec', 'to-tickets',
                   'triage', 'wayfinder', 'wizard', 'grill-me', 'grilling', 'handoff',
                   'teach', 'to-questionnaire', 'wait-what', 'writing-for-agents'],
                  key=len, reverse=True)

import importlib.util
_SPEC = importlib.util.spec_from_file_location('mp_specialize', ROOT / 'tools' / 'specialize.py')
specialize = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(specialize)


def inv():
    return json.loads((ROOT / 'inventory.json').read_text())


def inv_names():
    return {e['name'] for e in inv()['skills']}


def core_skills():
    return sorted(p.parent.name for p in CORE.glob('*/SKILL.md'))


def body_of(text):
    return text.split('\n---\n', 1)[1]


def bare_sibling_hits(body):
    hits = []
    for n in UP_NAMES:
        esc = re.escape(n)
        for pat in (rf'(?<![\w\-.])/{esc}(?![\w-])', rf'`{esc}`(?![\w-])', rf'(?<![\w\-]){esc} skill(?![\w-])'):
            for m in re.finditer(pat, body):
                if not body[max(0, m.start() - 3):m.start()].endswith('mp-'):
                    hits.append((n, body[:m.start()].count('\n') + 1))
    return hits


class InventoryContract(unittest.TestCase):
    def test_inventory_shape_and_scope(self):
        data = inv()
        self.assertEqual(len(data['skills']), 27)
        self.assertTrue(all(e['name'].startswith('mp-') for e in data['skills']))
        self.assertEqual(data['name_prefix'], 'mp-')
        self.assertEqual(data['default_set'], 'promoted')
        self.assertEqual(data['original_author'], 'Matt Pocock')
        self.assertEqual(data['original_license'], 'MIT')

    def test_inventory_matches_core_directories_exactly(self):
        self.assertEqual(set(core_skills()), inv_names())

    def test_inventory_pins_source_revision(self):
        self.assertEqual(inv()['revision'], PIN)

    def test_dispositions_match_audit_ledger(self):
        led = json.loads((ROOT / 'provenance' / 'audit-ledger.json').read_text())
        ledger = {s['skill']: s['disposition'] for s in led['skills']}
        for e in inv()['skills']:
            self.assertEqual(e['disposition'], ledger[e['upstream']], e['name'])


class CoreEntrypointContract(unittest.TestCase):
    def test_every_entrypoint_validates_frontmatter(self):
        for name in core_skills():
            text = (CORE / name / 'SKILL.md').read_text()
            specialize.validate_frontmatter(text, name)

    def test_every_entrypoint_metadata_is_exact(self):
        for name in core_skills():
            text = (CORE / name / 'SKILL.md').read_text()
            head = text[4:text.index('\n---\n', 4)]
            self.assertIn('license: MIT', head)
            self.assertIn('author: "Matt Pocock (original), tea24864 (port)"', head)
            self.assertIn('version: "0.1.0"', head)
            self.assertIn(f'source-revision: "{PIN}"', head)

    def test_descriptions_at_most_60_chars_ending_with_period(self):
        for name in core_skills():
            text = (CORE / name / 'SKILL.md').read_text()
            fields = specialize.validate_frontmatter(text, name)
            self.assertLessEqual(len(fields['description']), 60, name)

    def test_bodies_contain_only_known_exact_slot_tokens(self):
        token = re.compile(r'\{\{runtime\.([a-z_]+)\}\}')
        for name in core_skills():
            body = body_of((CORE / name / 'SKILL.md').read_text())
            used = set(token.findall(body))
            self.assertTrue(used <= SLOTS, (name, used - SLOTS))
            # no padded/loose runtime shapes in core (the renderer refuses them):
            # strip the well-formed tokens, then any residual '{{ runtime' is an error
            stripped = token.sub('', body)
            loose = re.findall(r'\{\{\s*runtime', stripped)
            self.assertEqual(loose, [], name)

    def test_no_bare_upstream_sibling_references(self):
        for name in core_skills():
            body = body_of((CORE / name / 'SKILL.md').read_text())
            hits = bare_sibling_hits(body)
            allowed = {('research', None), ('prototype', None), ('grilling', None)}
            real = [h for h in hits if h[1] is not None]
            # wayfinder ticket-type labels legitimately use the bare words
            unexpected = [h for h in real if not (name == 'mp-wayfinder' and h[0] in ('research', 'prototype', 'grilling'))]
            self.assertEqual(unexpected, [], (name, unexpected))

    def test_no_host_tool_names_in_core(self):
        for name in core_skills():
            text = (CORE / name / 'SKILL.md').read_text()
            for token in ('Skill tool', 'Task tool', 'openai.yaml'):
                self.assertNotIn(token, text, (name, token))

    def test_agent_instruction_files_are_never_hardcoded_as_universal(self):
        """CLAUDE.md/AGENTS.md may appear only as examples of a user-chosen file."""
        for name in core_skills():
            text = (CORE / name / 'SKILL.md').read_text()
            for m in re.finditer(r'(CLAUDE|AGENTS)\.md', text):
                start = max(0, m.start() - 260)
                context = text[start:m.end() + 260].lower()
                self.assertTrue(
                    any(w in context for w in ('user', 'their agent', 'chosen', 'whichever', 'other runtimes', 'upstream')),
                    (name, 'hardcoded instruction file near: ' + text[m.start() - 60:m.end() + 60]))

    def test_serial_fallback_present_where_delegation_used(self):
        for name in core_skills():
            body = body_of((CORE / name / 'SKILL.md').read_text())
            if '{{runtime.delegation}}' in body:
                self.assertIn('If independent delegation is unavailable in this runtime', body, name)


class CarrierContract(unittest.TestCase):
    def carriers(self):
        for skill_dir in sorted(CORE.iterdir()):
            if not skill_dir.is_dir():
                continue
            for p in sorted(skill_dir.rglob('*')):
                if p.is_file() and p.name != 'SKILL.md':
                    yield skill_dir.name, p

    def test_all_content_carriers_byte_identical_to_upstream(self):
        rel_map = {e['name']: e for e in inv()['skills']}
        for name, p in self.carriers():
            rel = p.relative_to(CORE / name).as_posix()
            if rel == 'SKILL-MECHANICS.md':
                continue
            up = UPSTREAM / 'skills' / rel_map[name]['bucket'] / rel_map[name]['upstream'] / rel
            self.assertTrue(up.exists(), (name, rel))
            self.assertEqual(p.read_bytes(), up.read_bytes(), (name, rel))

    def test_reauthored_carrier_is_runtime_neutral(self):
        p = CORE / 'mp-writing-for-agents' / 'SKILL-MECHANICS.md'
        text = p.read_text()
        up = (UPSTREAM / 'skills' / 'productivity' / 'writing-for-agents' / 'SKILL-MECHANICS.md').read_text()
        self.assertNotEqual(text, up)
        # it may name the upstream switch only as historical/informational, never as instruction
        instructionish = [ln for ln in text.splitlines()
                          if 'disable-model-invocation' in ln and not any(w in ln.lower() for w in ('upstream', 'where that field exists', 'some hosts', 'express it as'))]
        self.assertEqual(instructionish, [], instructionish)

    def test_no_adapter_metadata_files_in_core(self):
        for name, p in self.carriers():
            self.assertNotIn('openai.yaml', p.as_posix())

    def test_body_referenced_files_resolve_inside_the_skill(self):
        link = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
        for name in core_skills():
            body = body_of((CORE / name / 'SKILL.md').read_text())
            for target in link.findall(body):
                if target.startswith(('http://', 'https://')) or target.startswith('#'):
                    continue
                path = target.split('#', 1)[0]
                if not path or path == 'link':  # 'link' is upstream's own placeholder prose
                    continue
                self.assertTrue((CORE / name / path).exists(), (name, target))

    def test_shell_carriers_keep_executable_bit(self):
        mp_wizard = CORE / 'mp-wizard' / 'template.sh'
        self.assertTrue(mp_wizard.exists())
        self.assertTrue(mp_wizard.stat().st_mode & 0o111)

    def test_dex_horthy_credit_preserved(self):
        credits = (CORE / 'mp-pr' / 'CREDITS.md').read_text()
        self.assertIn('Horthy', credits)


class ProvenanceContract(unittest.TestCase):
    def test_upstream_snapshot_matches_recorded_hashes(self):
        records = {r['upstream_path']: r['sha256']
                   for r in json.loads((ROOT / 'provenance' / 'promoted-files.json').read_text())['files']}
        import hashlib
        self.assertEqual(len(records), 79)
        for rel, sha in records.items():
            p = UPSTREAM / rel
            self.assertTrue(p.exists(), rel)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), sha, rel)

    def test_full_revision_hash_record_covers_upstream(self):
        data = json.loads((ROOT / 'provenance' / 'upstream-full-revision-hashes.json').read_text())
        self.assertEqual(data['pin'], PIN)
        self.assertEqual(len(data['sha256_by_path']), 172)

    def test_reference_only_stash_records_scope_decision(self):
        data = json.loads((ROOT / 'provenance' / 'reference-only-stash.json').read_text())
        self.assertIn('promoted skills only', data['note'])
        self.assertEqual(set(data['groups']), {'in-progress', 'misc'})
        self.assertEqual({g['name'] for g in data['groups']['in-progress']['skills']},
                         {'claude-handoff', 'loop-me', 'setup-ts-deep-modules', 'writing-beats', 'writing-fragments', 'writing-shape'})
        for rel in data['infra']['copied']:
            self.assertTrue((ROOT / 'provenance' / 'reference-only' / 'infra' / rel).exists(), rel)

    def test_adapters_load_and_define_exact_slots(self):
        for rt in ('hermes', 'generic'):
            adapter = specialize.load_adapter(ROOT / 'adapters' / f'{rt}.json')
            self.assertEqual(set(adapter['snippets']), SLOTS)
            self.assertTrue(all('{{' not in s for s in adapter['snippets'].values()))
            self.assertTrue(all(len(s) <= 2200 for s in adapter['snippets'].values()))
        # adapters must not leak pstack wording
        for rt in ('hermes', 'generic'):
            text = (ROOT / 'adapters' / f'{rt}.json').read_text()
            self.assertNotIn('pstack', text)

    def test_ledger_evidence_lines_resolve(self):
        led = json.loads((ROOT / 'provenance' / 'audit-ledger.json').read_text())
        for s in led['skills']:
            for t in s.get('runtime_tokens_found', []):
                p = UPSTREAM / 'skills' / t['file']
                self.assertTrue(p.exists(), (s['skill'], t['file']))


if __name__ == '__main__':
    unittest.main()
