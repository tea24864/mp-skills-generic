"""Behavior checks for setup-time specialization, isolated from installed profiles.

Adapted from the pstack-generic test discipline to the mp runtime parametrization:
receipt file is '.mp-runtime.json', the uninstall prefix guard is 'mp-', staging
uses the '.mp-uninstall-' prefix, and adapters live under adapters/*.json.
Fixture skills use 'mp-' names so they exercise the uninstall prefix gate.
"""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = '.mp-runtime.json'
STAGING_PREFIX = '.mp-uninstall-'
MP_NAME = 'mp-fixture-main'


def load_specialize(name, module_path):
    """Load tools/specialize.py from an explicit path as a fresh module."""
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec and spec.loader, 'specialize.py must be loadable'
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skill_text(name, description='Just a fixture skill.', license_field='MIT',
               body=None, head=''):
    if body is None:
        body = '# ' + name + '\n\n{{runtime.files}}\n'
    return ('---\nname: ' + name + '\ndescription: "' + description + '"\n'
            + head + 'license: ' + license_field + '\n---\n' + body)


class Specialization(unittest.TestCase):
    longMessage = False

    def setUp(self):
        path = ROOT / 'tools/specialize.py'
        self.assertTrue(path.exists(), 'Setup-time deterministic specializer is not implemented')
        self.module = load_specialize('mp_specialize', path)
        self.temp = tempfile.TemporaryDirectory(prefix='mp-specialize-', dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.core = self.base / 'core skills'
        self.skill = self.core / MP_NAME
        self.skill.mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text(skill_text(MP_NAME))
        (self.skill / 'reference.md').write_text('See {{runtime.history}} for the tracked source.\n')
        self.adapters_dir = self.base / 'reviewed adapters'
        self.adapters_dir.mkdir()
        self.ack_adapter = self.base / 'acknowledgement adapters' / 'ack-rt.json'
        self.ack_adapter.parent.mkdir()
        self.write_adapter(self.adapter_path(), self.adapt_mapping())
        self.write_adapter(self.ack_adapter, self.ack_mapping())

    # -- fixture helpers ---------------------------------------------------
    def adapt_mapping(self, **overrides):
        mapping = {'schema_version': 1, 'id': 'fixture-rt', 'identity_tools': ['mp_fixture_cmd'],
                   'capabilities': {'independent_delegation': False},
                   'limits': ['fixture adapter'],
                   'snippets': {slot: 'Fixture instruction for ' + slot
                                for slot in self.module.SLOTS}}
        mapping.update(overrides)
        return mapping

    def ack_mapping(self):
        return self.adapt_mapping(id='ack-rt', requires_acknowledgement=True)

    def adapter_path(self):
        return self.adapters_dir / 'fixture-rt.json'

    def write_adapter(self, path, mapping):
        path.write_text(json.dumps(mapping))

    def install(self, target_name='target', adapter=None, acknowledge_limits=False):
        output = self.base / 'output'
        self.module.build(self.core, adapter or self.adapter_path(), output)
        target = self.base / (target_name + ' skills')
        self.module.install(output, target, acknowledge_limits=acknowledge_limits)
        return output, target

    # -- adapter loading ---------------------------------------------------
    def test_adapter_loader_rejects_malformed_adapters(self):
        mapping = self.adapt_mapping()
        no_slot = json.loads(json.dumps(mapping))
        del no_slot['snippets']['files']
        over_limit = self.adapt_mapping()
        over_limit['snippets'] = {slot: 'x' * 2201 for slot in self.module.SLOTS}
        templated = self.adapt_mapping()
        templated['snippets'] = {slot: 'tpl {{x}} ' + slot for slot in self.module.SLOTS}
        missing_id = self.adapt_mapping()
        del missing_id['id']
        cases = [
            ('not a json object', [1, 2], 'Adapter'),
            ('identity not a list', self.adapt_mapping(identity_tools='mp_fixture_cmd'), 'identity_tools'),
            ('identity with an empty entry', self.adapt_mapping(identity_tools=['mp_fixture_cmd', '']), 'identity_tools'),
            ('identity with a non-string entry', self.adapt_mapping(identity_tools=[7]), 'identity_tools'),
            ('wrong schema version', self.adapt_mapping(schema_version=2), 'identity/schema'),
            ('invalid adapter id shape', self.adapt_mapping(id='Bad_Id'), 'identity/schema'),
            ('missing adapter id', missing_id, 'identity/schema'),
            ('snippets not the full slot set', no_slot, 'insertion points'),
            ('snippet exceeds the literal limit', over_limit, 'Adapter snippets'),
            ('snippet contains template syntax', templated, 'Adapter snippets'),
            ('limits not a list', self.adapt_mapping(limits='fixture adapter'), 'capability limits'),
            ('capabilities not a mapping', self.adapt_mapping(capabilities='nope'), 'capability limits'),
        ]
        for label, payload, message in cases:
            with self.subTest(case=label):
                candidate = self.base / ('broken ' + label + '.json')
                candidate.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError, message):
                    self.module.load_adapter(candidate)

    # -- build ---------------------------------------------------------------
    def test_build_adds_specialized_text_only_where_slotted(self):
        output = self.base / 'output'
        result = self.module.build(self.core, self.adapter_path(), output)
        self.assertEqual((result['runtime'], result['skills'], result['files']), ('fixture-rt', 1, 2))
        self.assertTrue((output / 'distribution.json').is_file())
        skill = output / 'skills' / MP_NAME
        skill_md = (skill / 'SKILL.md').read_text()
        self.assertIn('Fixture instruction for files', skill_md)
        self.assertNotIn('Fixture instruction for delegation', skill_md)
        self.assertNotIn('{{', skill_md)
        reference = (skill / 'reference.md').read_text()
        self.assertIn('Fixture instruction for history', reference)
        self.assertNotIn('Fixture instruction for files', reference)
        self.assertNotIn('{{', reference)

    def test_existing_build_output_is_never_overwritten(self):
        output = self.base / 'output'
        output.mkdir()
        (output / 'user.txt').write_text('untouched')
        with self.assertRaisesRegex(ValueError, 'existing output'):
            self.module.build(self.core, self.adapter_path(), output)
        self.assertEqual((output / 'user.txt').read_text(), 'untouched')

    def test_build_refuses_output_inside_authored_source(self):
        target = self.core / 'nested output'
        with self.assertRaisesRegex(ValueError, 'inside authored source'):
            self.module.build(self.core, self.adapter_path(), target)
        self.assertFalse(target.exists())

    def test_build_is_deterministic_including_paths_with_spaces(self):
        for folder in ('one', 'two with spaces'):
            self.module.build(self.core, self.adapter_path(), self.base / folder)
        for rel in ('distribution.json', 'skills/' + MP_NAME + '/SKILL.md',
                    'skills/' + MP_NAME + '/reference.md'):
            self.assertEqual((self.base / 'one' / rel).read_bytes(),
                             (self.base / 'two with spaces' / rel).read_bytes())

    def test_build_refuses_unknown_slot_and_unresolved_template(self):
        reference = self.skill / 'reference.md'
        reference.write_text('Introduces {{runtime.nonexistent}}.\n')
        with self.assertRaisesRegex(ValueError, 'Unknown insertion point'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())
        # Generic mustache text is legitimate upstream content (e.g. '{{repo name}}'
        # in a report template the agent fills at use time): it must build cleanly.
        reference.write_text('Falls back to {{arbitrary.expression}} and {{repo name}}.\n')
        result = self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertTrue((self.base / 'output').exists())
        self.assertIn('{{repo name}}', (self.base / 'output' / 'skills' / MP_NAME / 'reference.md').read_text())
        shutil.rmtree(self.base / 'output')
        # Spaced or padded runtime-shaped text is refused as unresolved runtime slot,
        # even when the slot name would otherwise be known.
        reference.write_text('Keeps a padded known slot {{ runtime.delegation }} unresolved.\n')
        with self.assertRaisesRegex(ValueError, 'Unresolved runtime slot'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())
        reference.write_text('Keeps a padded unknown slot {{ runtime.nope }} unresolved.\n')
        with self.assertRaisesRegex(ValueError, 'Unresolved runtime slot'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())

    def test_build_refuses_adapter_with_wrong_snippet_set(self):
        mapping = self.adapt_mapping()
        del mapping['snippets']['delegation']
        self.write_adapter(self.adapter_path(), mapping)
        with self.assertRaisesRegex(ValueError, 'insertion points'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())

    def test_build_refuses_malformed_frontmatter_variants(self):
        variants = {
            'missing description': '---\nname: ' + MP_NAME + '\nlicense: MIT\n---\n# Incomplete\n',
            'description over sixty chars': skill_text(MP_NAME, description='x' * 61 + '.'),
            'description without final period': skill_text(MP_NAME, description='Anything without a stop'),
            'license is not MIT': skill_text(MP_NAME, license_field='Apache-2.0'),
            'name disagrees with directory': '---\nname: other-name\ndescription: "Ok end."\nlicense: MIT\n---\nBody\n',
            'unsupported core field': skill_text(MP_NAME, head='unknown-field: value\n'),
            'duplicate core field': '---\nname: ' + MP_NAME + '\nname: ' + MP_NAME
                                    + '\ndescription: "Ok end."\nlicense: MIT\n---\nBody\n',
            'nested core metadata rejected': skill_text(MP_NAME, head='metadata:\n  depth: {"nested": 1}\n'),
            'boolean core metadata value': skill_text(MP_NAME, head='metadata:\n  depth: [3]\n'),
            'empty workflow body': skill_text(MP_NAME, body='\n'),
            'without standard frontmatter': 'name: ' + MP_NAME + '\nThis file has no header fence.\n',
        }
        (self.skill / 'reference.md').write_text('plain text only\n')
        output = self.base / 'output'
        for label, text in variants.items():
            with self.subTest(case=label):
                (self.skill / 'SKILL.md').write_text(text)
                with self.assertRaises(ValueError):
                    self.module.build(self.core, self.adapter_path(), output)
                self.assertFalse(output.exists())

    def test_build_refuses_core_metadata_contract_violations(self):
        (self.skill / 'SKILL.md').write_text(
            skill_text(MP_NAME, head='metadata:\n  author: "Fixture"\n'))
        self.module.build(self.core, self.adapter_path(), self.base / 'good')
        bad_cases = {
            'duplicate metadata key': skill_text(MP_NAME, head='metadata:\n  author: "A"\n  author: "B"\n'),
            'boolean metadata value': skill_text(MP_NAME, head='metadata:\n  author: true\n'),
            'mapping metadata value': skill_text(MP_NAME, head='metadata:\n  author: {"k": "v"}\n'),
        }
        for label, text in bad_cases.items():
            with self.subTest(case=label):
                (self.skill / 'SKILL.md').write_text(text)
                with self.assertRaisesRegex(ValueError, 'metadata'):
                    self.module.build(self.core, self.adapter_path(), self.base / ('bad ' + label))

    def test_build_refuses_symlinks_in_source(self):
        (self.skill / 'linked.md').symlink_to(self.skill / 'SKILL.md')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())

    def test_build_refuses_artifacts_outside_named_skill_dirs(self):
        (self.core / 'stray.md').write_text('not owned by any skill dir\n')
        with self.assertRaisesRegex(ValueError, 'outside a named skill'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())

    def test_build_requires_at_least_one_valid_entrypoint(self):
        empty = self.base / 'empty core'
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, 'No valid skill entrypoints'):
            self.module.build(empty, self.adapter_path(), self.base / 'output')

    def test_build_writes_populated_manifest_with_sorted_skills(self):
        self.module.build(self.core, self.adapter_path(), self.base / 'output')
        manifest = json.loads((self.base / 'output/distribution.json').read_text())
        self.assertEqual(manifest['schema_version'], 1)
        self.assertEqual(manifest['runtime'], 'fixture-rt')
        self.assertEqual(manifest['skills'], sorted(manifest['skills']))
        self.assertEqual(manifest['skills'], [MP_NAME])
        self.assertEqual(manifest['capabilities'], {'independent_delegation': False})
        self.assertTrue(manifest['limits'])
        self.assertFalse(manifest['requires_acknowledgement'])
        self.assertEqual(len(manifest['adapter_sha256']), 64)
        self.assertEqual(len(manifest['core_sha256']), 64)
        entries = {row['path']: row['sha256'] for row in manifest['source_files']}
        self.assertEqual(set(entries), {MP_NAME + '/SKILL.md', MP_NAME + '/reference.md'})
        for sha in entries.values():
            self.assertRegex(sha, r'[0-9a-f]{64}')
        files = {row['path']: row for row in manifest['files']}
        self.assertEqual(set(files), {'skills/' + MP_NAME + '/SKILL.md',
                                      'skills/' + MP_NAME + '/reference.md'})
        self.assertTrue(all(isinstance(row['bytes'], int) and row['bytes'] > 0 for row in files.values()))

    # -- metadata_by_skill injection ------------------------------------------
    def test_runtime_metadata_line_is_injected_without_changing_core(self):
        before = (self.skill / 'SKILL.md').read_bytes()
        optimized = self.adapt_mapping()
        self.write_adapter(self.adapter_path(), dict(
            optimized, metadata_namespace='fixturert',
            metadata_by_skill={MP_NAME: {'config': [{'key': 'mp.panel_size', 'default': 3}]}}))
        self.module.build(self.core, self.adapter_path(), self.base / 'output')
        text = (self.base / 'output/skills' / MP_NAME / 'SKILL.md').read_text()
        self.assertIn('  fixturert: {"config":', text)
        self.assertIn('"mp.panel_size"', text)
        self.assertNotIn('{{', text)
        self.assertEqual((self.skill / 'SKILL.md').read_bytes(), before)

    def test_runtime_metadata_block_reference_resolves_and_inserts_into_core_metadata(self):
        (self.skill / 'SKILL.md').write_text(
            skill_text(MP_NAME, description='Authored carryover case.',
                       head='metadata:\n  author: "Fixture"\nallowed-tools: mp_fixture_cmd\n'))
        self.write_adapter(self.adapter_path(), self.adapt_mapping(
            metadata_namespace='fixturert',
            metadata_by_skill={MP_NAME: 'panel-policy'},
            metadata_blocks={'panel-policy': {'tags': ['fixture']}}))
        self.module.build(self.core, self.adapter_path(), self.base / 'output')
        text = (self.base / 'output/skills' / MP_NAME / 'SKILL.md').read_text()
        self.assertIn('  author: "Fixture"', text)
        self.assertIn('  fixturert: {"tags": ["fixture"]}', text)
        self.assertLess(text.index('  fixturert:'), text.index('allowed-tools:'))
        self.assertNotIn('fixturert: "panel-policy"', text)

    def test_unknown_metadata_block_reference_is_refused(self):
        self.write_adapter(self.adapter_path(), self.adapt_mapping(
            metadata_namespace='fixturert',
            metadata_by_skill={MP_NAME: 'missing-block'}))
        with self.assertRaisesRegex(ValueError, 'Missing runtime metadata block'):
            self.module.build(self.core, self.adapter_path(), self.base / 'output')
        self.assertFalse((self.base / 'output').exists())

    def test_conflicting_or_invalid_metadata_namespace_is_refused(self):
        (self.skill / 'SKILL.md').write_text(
            skill_text(MP_NAME, head='metadata:\n  fixturert: "authored"\n'))
        self.write_adapter(self.adapter_path(), self.adapt_mapping(
            metadata_namespace='fixturert',
            metadata_by_skill={MP_NAME: {'tags': ['x']}}))
        with self.assertRaisesRegex(ValueError, 'metadata namespace'):
            self.module.build(self.core, self.adapter_path(), self.base / 'conflict')
        self.write_adapter(self.adapter_path(), self.adapt_mapping(
            metadata_namespace='bad namespace!',
            metadata_by_skill={MP_NAME: {'tags': ['x']}}))
        with self.assertRaisesRegex(ValueError, 'metadata namespace'):
            self.module.build(self.core, self.adapter_path(), self.base / 'bad namespace')
        self.assertFalse((self.base / 'conflict').exists())
        self.assertFalse((self.base / 'bad namespace').exists())

    # -- verify_distribution ---------------------------------------------------
    def test_verify_distribution_passes_on_intact_build(self):
        output = self.base / 'verify ok'
        self.module.build(self.core, self.adapter_path(), output)
        manifest = self.module.verify_distribution(output)
        self.assertEqual(manifest['runtime'], 'fixture-rt')
        self.assertEqual(manifest['skills'], [MP_NAME])

    def test_verify_distribution_refuses_changed_added_and_missing_files(self):
        for change in ('changed', 'added', 'missing'):
            with self.subTest(change=change):
                source = self.base / ('base ' + change)
                self.module.build(self.core, self.adapter_path(), source)
                mirror = self.base / ('mirror ' + change)
                shutil.copytree(source, mirror)
                skill = mirror / 'skills' / MP_NAME
                if change == 'changed':
                    (skill / 'SKILL.md').write_text('modified after generation')
                    with self.assertRaisesRegex(ValueError, 'artifact changed'):
                        self.module.verify_distribution(mirror)
                elif change == 'added':
                    (skill / 'unexpected.md').write_text('new unreviewed file')
                    with self.assertRaisesRegex(ValueError, 'artifact set changed'):
                        self.module.verify_distribution(mirror)
                else:
                    (skill / 'reference.md').unlink()
                    with self.assertRaisesRegex(ValueError, 'artifact set changed'):
                        self.module.verify_distribution(mirror)

    def test_verify_distribution_refuses_skill_name_set_mismatch(self):
        output = self.base / 'mismatch output'
        self.module.build(self.core, self.adapter_path(), output)
        manifest = json.loads((output / 'distribution.json').read_text())
        manifest['skills'].append('mp-not-built')
        (output / 'distribution.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'skill names'):
            self.module.verify_distribution(output)

    # -- install ---------------------------------------------------------------
    def test_install_writes_exact_fileset_with_verified_hashes_and_receipt(self):
        output = self.base / 'output'
        self.module.build(self.core, self.adapter_path(), output)
        target = self.base / 'agent skills dir'
        result = self.module.install(output, target)
        self.assertIn('skills_dir', result)
        self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
        self.assertEqual(result['installed_skills'], 1)
        self.assertEqual(result['installed_files'], 2)
        manifest = json.loads((output / 'distribution.json').read_text())
        installed = {('skills' / p.relative_to(target)).as_posix()
                     for p in target.rglob('*') if p.is_file() and p.name != RECEIPT}
        self.assertEqual(installed, {row['path'] for row in manifest['files']})
        for row in manifest['files']:
            data = (target / Path(row['path']).relative_to('skills')).read_bytes()
            self.assertEqual(self.module.digest(data), row['sha256'], row['path'])
        receipt = json.loads((target / RECEIPT).read_text())
        self.assertEqual(receipt['runtime'], 'fixture-rt')
        self.assertIn('runtime_version', receipt)
        self.assertIsNone(receipt['runtime_version'])
        self.assertEqual(receipt['core_sha256'], manifest['core_sha256'])
        self.assertEqual(receipt['skills'], manifest['skills'])
        self.assertEqual(receipt['files'], manifest['files'])

    def test_install_refuses_existing_skills_and_existing_receipt(self):
        output = self.base / 'output'
        self.module.build(self.core, self.adapter_path(), output)
        target = self.base / 'target'
        self.module.install(output, target)
        with self.assertRaisesRegex(ValueError, 'existing'):
            self.module.install(output, target)
        preexisting = self.base / 'preexisting skills'
        (preexisting / MP_NAME).mkdir(parents=True)
        (preexisting / MP_NAME / 'SKILL.md').write_text(
            skill_text(MP_NAME, description='An earlier install.'))
        with self.assertRaisesRegex(ValueError, 'existing'):
            self.module.install(output, preexisting)

    def test_install_refuses_symlinked_target_name(self):
        output, target = self.base / 'output', self.base / 'target'
        self.module.build(self.core, self.adapter_path(), output)
        target.mkdir()
        (target / MP_NAME).symlink_to(self.skill)
        with self.assertRaisesRegex(ValueError, 'existing'):
            self.module.install(output, target)
        self.assertTrue((target / MP_NAME).is_symlink())
        self.assertFalse((target / RECEIPT).exists())

    def test_install_refuses_distribution_that_differs_from_manifest(self):
        output = self.base / 'output'
        self.module.build(self.core, self.adapter_path(), output)
        for change in ('modified', 'extra'):
            with self.subTest(change=change):
                mirror = self.base / ('out ' + change)
                shutil.copytree(output, mirror)
                skill = mirror / 'skills' / MP_NAME
                if change == 'modified':
                    (skill / 'SKILL.md').write_text('replaced after generation')
                else:
                    (skill / 'graft.py').write_text('print("unreviewed")\n')
                with self.assertRaises(ValueError):
                    self.module.install(mirror, self.base / ('target ' + change))

    def test_generic_limits_require_explicit_acknowledgement(self):
        output, target = self.base / 'ack output', self.base / 'ack target'
        self.module.build(self.core, self.ack_adapter, output)
        with self.assertRaisesRegex(ValueError, 'acknowledgement'):
            self.module.install(output, target)
        self.assertFalse(target.exists())
        result = self.module.install(output, target, acknowledge_limits=True)
        self.assertEqual(result['runtime'], 'ack-rt')
        receipt = json.loads((target / RECEIPT).read_text())
        self.assertTrue(receipt['limits'])

    def test_partial_copy_failure_rolls_back_owned_targets_and_receipt(self):
        output, target = self.base / 'output', self.base / 'target'
        self.module.build(self.core, self.adapter_path(), output)
        unrelated = target / 'unrelated'
        unrelated.mkdir(parents=True)
        (unrelated / 'SKILL.md').write_text('user content')

        def fail(source, destination, **kwargs):
            (destination / 'partial.txt').write_text('partial copy')
            raise OSError('simulated disk failure')

        with patch.object(self.module.shutil, 'copytree', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.module.install(output, target)
        self.assertFalse((target / MP_NAME).exists())
        self.assertFalse((target / RECEIPT).exists())
        self.assertEqual((unrelated / 'SKILL.md').read_text(), 'user content')

    def test_copy_addition_is_refused_and_owned_tree_rolled_back(self):
        output, target = self.base / 'output', self.base / 'target'
        self.module.build(self.core, self.adapter_path(), output)
        original = self.module.shutil.copytree

        def injected(source, destination, **kwargs):
            result = original(source, destination, **kwargs)
            (destination / 'unreviewed.py').write_text('raise RuntimeError("unreviewed")')
            return result

        with patch.object(self.module.shutil, 'copytree', side_effect=injected):
            with self.assertRaisesRegex(ValueError, 'Installed artifact set'):
                self.module.install(output, target)
        self.assertFalse((target / MP_NAME).exists())
        self.assertFalse((target / RECEIPT).exists())
        self.module.install(output, target)
        self.assertTrue((target / RECEIPT).is_file())

    def test_runtime_version_is_recorded_from_the_observed_flag_only(self):
        self.module.build(self.core, self.adapter_path(), self.base / 'bare output')
        self.module.install(self.base / 'bare output', self.base / 'bare target')
        self.assertIsNone(
            json.loads((self.base / 'bare target' / RECEIPT).read_text())['runtime_version'])
        self.module.build(self.core, self.adapter_path(), self.base / 'versioned output',
                          runtime_version='9.8.7')
        self.module.install(self.base / 'versioned output', self.base / 'versioned target')
        receipt = json.loads((self.base / 'versioned target' / RECEIPT).read_text())
        self.assertEqual(receipt['runtime_version'], '9.8.7')

    def test_collision_in_another_sibling_dir_preserves_local_edit(self):
        output = self.base / 'output'
        self.module.build(self.core, self.adapter_path(), output)
        existing = self.base / 'target/other-category' / MP_NAME
        existing.mkdir(parents=True)
        (existing / 'SKILL.md').write_text('local edit')
        with self.assertRaisesRegex(ValueError, 'existing skills'):
            self.module.install(output, self.base / 'target')
        self.assertEqual((existing / 'SKILL.md').read_text(), 'local edit')
        self.assertFalse((self.base / 'target' / MP_NAME).exists())

    # -- detect ------------------------------------------------------------------
    def test_detect_uses_observed_tool_evidence_only(self):
        result = self.module.detect(
            {'tool_names': ['mp_fixture_cmd'], 'runtime_hint': 'somewhere-else'},
            [self.adapter_path()])
        self.assertEqual(result['runtime'], 'fixture-rt')
        self.assertFalse(result['needs_selection'])
        unknown = self.module.detect({'tool_names': ['mp_unrecognized']}, [self.adapter_path()])
        self.assertIsNone(unknown['runtime'])
        self.assertTrue(unknown['needs_selection'])

    def test_detect_requires_selection_when_candidates_are_ambiguous(self):
        self.write_adapter(self.adapters_dir / 'second-rt.json',
                           dict(self.adapt_mapping(), id='second-rt',
                                identity_tools=['mp_fixture_cmd']))
        result = self.module.detect({'tool_names': ['mp_fixture_cmd']},
                                    sorted(self.adapters_dir.glob('*.json')))
        self.assertIsNone(result['runtime'])
        self.assertTrue(result['needs_selection'])
        self.assertEqual(result['candidates'], ['fixture-rt', 'second-rt'])

    def test_detect_rejects_structurally_invalid_evidence(self):
        with self.assertRaisesRegex(ValueError, 'Evidence'):
            self.module.detect({'tool_names': 'mp_fixture_cmd'}, [self.adapter_path()])
        with self.assertRaisesRegex(ValueError, 'Evidence'):
            self.module.detect({'tool_names': ['mp_fixture_cmd', 7]}, [self.adapter_path()])
        broken = self.base / 'broken identity.json'
        broken.write_text(json.dumps(self.adapt_mapping(identity_tools='mp_fixture_cmd')))
        with self.assertRaisesRegex(ValueError, 'identity_tools'):
            self.module.detect({'tool_names': ['mp_fixture_cmd']}, [broken])

    # -- uninstall ----------------------------------------------------------------
    def test_uninstall_preview_then_confirm_removes_only_owned_paths(self):
        output, target = self.install('cycle')
        orphan = target / 'sibling'
        orphan.mkdir()
        (orphan / 'SKILL.md').write_text('unrelated user skill')
        outside = self.base / 'unrelated.txt'
        outside.write_text('keep me')
        self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
        preview = self.module.uninstall(target)
        self.assertTrue(preview['dry_run'])
        self.assertEqual(preview['skills'], [MP_NAME])
        self.assertEqual(preview['files'], 2)
        self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
        self.assertTrue((target / RECEIPT).is_file())
        result = self.module.uninstall(target, confirm=True)
        self.assertFalse(result['dry_run'])
        self.assertEqual(result['removed_skills'], 1)
        self.assertEqual(result['removed_files'], 2)
        self.assertFalse((target / RECEIPT).exists())
        self.assertFalse((target / MP_NAME).exists())
        self.assertEqual((orphan / 'SKILL.md').read_text(), 'unrelated user skill')
        self.assertEqual(outside.read_text(), 'keep me')
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.module.uninstall(target, confirm=True)
        self.assertEqual(self.module.install(output, target)['installed_skills'], 1)

    def test_uninstall_refuses_missing_or_linked_receipt(self):
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.module.uninstall(self.base / 'never installed', confirm=True)
        output, target = self.install('linked')
        record = target / RECEIPT
        saved = self.base / 'saved receipt.json'
        record.rename(saved)
        record.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.module.uninstall(target, confirm=True)
        self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
        self.assertTrue(saved.is_file())

    def test_uninstall_refuses_names_without_the_mp_prefix(self):
        output, target = self.install('prefix')
        record = target / RECEIPT
        receipt = json.loads(record.read_text())
        for name in ('not-mp-name', 'mpother', 'MP-upper'):
            with self.subTest(name=name):
                record.write_text(json.dumps(dict(receipt, skills=[name])))
                with self.assertRaisesRegex(ValueError, 'Invalid uninstall skill names'):
                    self.module.uninstall(target, confirm=True)
                self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
        record.write_text(json.dumps(receipt))

    def test_uninstall_refuses_invalid_artifact_paths_and_hashes(self):
        output, target = self.install('paths')
        record = target / RECEIPT
        clean = record.read_text()
        receipt = json.loads(clean)
        extra = lambda path, sha: receipt['files'] + [{'path': path, 'sha256': sha}]  # noqa: E731
        foreign_names = dict(receipt, skills=[MP_NAME, 'mp-other'],
                             files=extra('skills/mp-other/x.md', '0' * 64))
        cases_in_order = [
            ('absolute path', dict(receipt, files=extra('/etc/passwd', '0' * 64))),
            ('traversal path', dict(receipt, files=extra('skills/' + MP_NAME + '/../../escape', '0' * 64))),
            ('foreign top dir', dict(receipt, files=extra('other/' + MP_NAME + '/x.md', '0' * 64))),
            ('structurally invalid hash', dict(receipt, files=extra('skills/' + MP_NAME + '/bogus.md', 'not-a-hash'))),
            ('duplicate path', dict(receipt, files=receipt['files'] * 2)),
            ('unowned non-mp skill claim', foreign_names),
        ]
        for label, tampered in cases_in_order:
            with self.subTest(case=label):
                record.write_text(json.dumps(tampered))
                with self.assertRaises(ValueError):
                    self.module.uninstall(target, confirm=True)
                self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
                record.write_text(clean)
        self.assertEqual(json.loads(record.read_text()), receipt)

    def test_uninstall_requires_every_entrypoint_in_the_receipt(self):
        output, target = self.install('entry')
        record = target / RECEIPT
        receipt = json.loads(record.read_text())
        receipt['files'] = [row for row in receipt['files'] if not row['path'].endswith('/SKILL.md')]
        record.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'entrypoint'):
            self.module.uninstall(target, confirm=True)
        self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())

    def test_uninstall_refuses_foreign_or_legacy_receipts(self):
        output, target = self.install('legacy')
        record = target / RECEIPT
        saved = record.read_text()
        for override in ({'schema_version': 2}, {'files': []}, {'skills': []},
                         {'files': 'no list'}, {'skills': 'no list'}):
            with self.subTest(override=str(override)):
                tampered = json.loads(saved)
                tampered.update(override)
                record.write_text(json.dumps(tampered))
                with self.assertRaisesRegex(ValueError, 'uninstall ownership'):
                    self.module.uninstall(target, confirm=True)
                self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
                record.write_text(saved)

    def test_uninstall_refuses_edits_added_missing_and_linked_artifacts(self):
        output = self.base / 'output'
        self.module.build(self.core, self.adapter_path(), output)
        for change in ('edit', 'added', 'missing', 'symlink'):
            with self.subTest(change=change):
                mirror = self.base / ('tamper ' + change)
                self.module.install(output, mirror)
                skill = mirror / MP_NAME
                if change == 'edit':
                    (skill / 'SKILL.md').write_text('user edit after install')
                elif change == 'added':
                    (skill / 'user.txt').write_text('user content')
                elif change == 'missing':
                    (skill / 'reference.md').unlink()
                else:
                    (skill / 'linked.md').symlink_to(self.skill / 'SKILL.md')
                with self.assertRaises(ValueError):
                    self.module.uninstall(mirror, confirm=True)
                self.assertTrue(skill.is_dir())
                self.assertTrue((mirror / RECEIPT).is_file())

    def test_uninstall_refuses_unrecorded_directories(self):
        output, target = self.install('dirs')
        (target / MP_NAME / 'user-work').mkdir()
        with self.assertRaisesRegex(ValueError, 'directory'):
            self.module.uninstall(target, confirm=True)
        self.assertTrue((target / MP_NAME / 'user-work').is_dir())

    def test_uninstall_refuses_linked_installed_artifacts(self):
        output, target = self.install('dirs')
        (target / MP_NAME / 'linked.md').symlink_to(self.skill / 'SKILL.md')
        with self.assertRaisesRegex(ValueError, 'Linked'):
            self.module.uninstall(target, confirm=True)
        self.assertTrue((target / MP_NAME / 'linked.md').is_symlink())

    def test_uninstall_staging_failure_restores_full_installation(self):
        output, target = self.install('staging-fail')
        rename = Path.rename

        def fail_record(path, destination):
            # Fail only the receipt rename INTO the staging area; the renames back
            # out (rollback) must keep working so owned paths are restored.
            if path.name == RECEIPT and STAGING_PREFIX not in destination.name:
                raise OSError('simulated staging failure')
            return rename(path, destination)

        with patch.object(Path, 'rename', fail_record):
            with self.assertRaisesRegex(OSError, 'simulated staging failure'):
                self.module.uninstall(target, confirm=True)
        self.assertTrue((target / MP_NAME / 'SKILL.md').is_file())
        self.assertTrue((target / RECEIPT).is_file())
        self.assertEqual(list(target.glob(STAGING_PREFIX + '*')), [])

    def test_uninstall_cleanup_failure_reports_recoverable_staging(self):
        output, target = self.install('staging-keep')
        with patch.object(self.module.shutil, 'rmtree', side_effect=OSError('simulated cleanup failure')):
            with self.assertRaisesRegex(OSError, 'cleanup incomplete'):
                self.module.uninstall(target, confirm=True)
        staging = list(target.glob(STAGING_PREFIX + '*'))
        self.assertEqual(len(staging), 1)
        self.assertTrue((staging[0] / MP_NAME / 'SKILL.md').is_file())
        self.assertTrue((staging[0] / RECEIPT).is_file())

    # -- CLI smoke through main(argv) ---------------------------------------------
    def run_main(self, *arguments):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = self.module.main(list(arguments))
        return code, captured.getvalue()

    def test_cli_build_verify_install_roundtrip_with_explicit_destinations(self):
        output = self.base / 'cli output'
        code, line = self.run_main('build', '--runtime', 'fixture-rt', '--core', str(self.core),
                                   '--output', str(output), '--adapters-dir', str(self.adapters_dir))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(line)['runtime'], 'fixture-rt')
        code, line = self.run_main('verify', '--distribution', str(output))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(line)['verified'])
        code, line = self.run_main('install', '--distribution', str(output),
                                   '--skills-dir', str(self.base / 'cli skills'))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(line)['installed_skills'], 1)
        self.assertTrue((self.base / 'cli skills' / MP_NAME / 'SKILL.md').is_file())
        with self.assertRaises(SystemExit) as refusal:
            self.run_main('install', '--distribution', str(output),
                          '--skills-dir', str(self.base / 'cli skills'))
        self.assertEqual(refusal.exception.code, 2)

    def test_cli_rejects_unreviewed_runtime_names_without_writing(self):
        output = self.base / 'never written'
        with self.assertRaises(SystemExit) as bad_name:
            self.run_main('build', '--runtime', 'has..dots', '--output', str(output),
                          '--adapters-dir', str(self.adapters_dir))
        self.assertEqual(bad_name.exception.code, 2)
        with self.assertRaises(SystemExit) as no_adapter:
            self.run_main('build', '--runtime', 'unreviewed-rt', '--output', str(output),
                          '--adapters-dir', str(self.adapters_dir))
        self.assertEqual(no_adapter.exception.code, 2)
        self.assertFalse(output.exists())

    def test_cli_uninstall_requires_confirmation_and_allows_repeat_cycles(self):
        output, target = self.base / 'cli out', self.base / 'cli cycle skills'
        self.module.build(self.core, self.adapter_path(), output)
        for cycle in range(2):
            self.module.install(output, target)
            code, line = self.run_main('uninstall', '--skills-dir', str(target))
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(line)['dry_run'])
            self.assertTrue((target / MP_NAME).exists())
            code, line = self.run_main('uninstall', '--skills-dir', str(target), '--yes')
            self.assertEqual(code, 0)
            self.assertFalse((target / MP_NAME).exists())
            self.assertFalse((target / RECEIPT).exists())

    def test_cli_detect_single_match_and_ambiguous_selection(self):
        evidence = self.base / 'evidence.json'
        evidence.write_text(json.dumps({'tool_names': ['mp_fixture_cmd', 'other_local_tool']}))
        code, line = self.run_main('detect', '--evidence', str(evidence),
                                   '--adapters-dir', str(self.adapters_dir))
        self.assertEqual(code, 0)
        result = json.loads(line)
        self.assertEqual(result['runtime'], 'fixture-rt')
        self.assertFalse(result['needs_selection'])
        self.write_adapter(self.adapters_dir / 'second-rt.json',
                           dict(self.adapt_mapping(), id='second-rt',
                                identity_tools=['mp_fixture_cmd']))
        code, line = self.run_main('detect', '--evidence', str(evidence),
                                   '--adapters-dir', str(self.adapters_dir))
        self.assertEqual(code, 2)
        result = json.loads(line)
        self.assertIsNone(result['runtime'])
        self.assertTrue(result['needs_selection'])
        self.assertEqual(sorted(result['candidates']), ['fixture-rt', 'second-rt'])

    # -- completeness gate against the committed inventory ------------------------
    def test_build_on_the_default_core_enforces_inventory_coverage(self):
        sandbox = self.base / 'repo copy'
        (sandbox / 'tools').mkdir(parents=True)
        (sandbox / 'core' / 'skills').mkdir(parents=True)
        inventory_source = ROOT / 'inventory.json'
        self.assertTrue(inventory_source.is_file(), 'inventory.json must be committed')
        shutil.copy2(ROOT / 'tools/specialize.py', sandbox / 'tools/specialize.py')
        gate = load_specialize('mp_specialize_gate', sandbox / 'tools/specialize.py')
        self.assertEqual(gate.SLOTS, self.module.SLOTS)
        self.assertEqual(gate.ROOT, sandbox)
        names = {row['name'] for row in json.loads(inventory_source.read_text())['skills']}
        self.assertEqual(len(names), 27)
        for name in names:
            self.assertRegex(name, r'^mp-[a-z0-9-]+$')
            self.assertLessEqual(len(name), 64)

        def skill_doc(name, description):
            return skill_text(name, description=description,
                              body='# ' + name + '\n\nplain authored body\n')

        def gate_build(core_names, inventory_names):
            for existing in (sandbox / 'core' / 'skills').iterdir():
                if existing.name not in core_names:
                    shutil.rmtree(existing)
            for name in core_names:
                (sandbox / 'core' / 'skills' / name).mkdir(parents=True, exist_ok=True)
                (sandbox / 'core' / 'skills' / name / 'SKILL.md').write_text(
                    skill_doc(name, str(len(name)) + ' chars fixture skill.'))
            (sandbox / 'inventory.json').write_text(json.dumps(
                {'skills': [{'name': name} for name in inventory_names]}))
            label = 'gate ' + '-'.join(sorted(core_names)) + ' ' + '-'.join(sorted(inventory_names))
            output = sandbox / label
            captured = io.StringIO()
            try:
                with contextlib.redirect_stdout(captured):
                    code = gate.main(['build', '--runtime', 'fixture-rt', '--output', str(output),
                                      '--adapters-dir', str(self.adapters_dir)])
            except SystemExit as exit_code:
                code = exit_code.code
            return code, output

        code, output = gate_build(['mp-gate-one'], ['mp-gate-one'])
        self.assertEqual(code, 0)
        self.assertTrue((output / 'distribution.json').is_file())
        for core_names, inventory_names in ((['mp-gate-one', 'mp-gate-two'], ['mp-gate-one']),
                                            (['mp-gate-one'], ['mp-gate-one', 'mp-gate-two'])):
            with self.subTest(core=core_names, inventory=inventory_names):
                code, gate_output = gate_build(core_names, inventory_names)
                self.assertEqual(code, 2)
                self.assertFalse(gate_output.exists())

    def test_committed_adapters_load_and_declare_the_full_slot_set(self):
        adapters = sorted((ROOT / 'adapters').glob('*.json'))
        self.assertEqual({path.stem for path in adapters}, {'generic', 'hermes'})
        for path in adapters:
            adapter = self.module.load_adapter(path)
            with self.subTest(adapter=path.name):
                self.assertEqual(adapter['schema_version'], 1)
                self.assertEqual(set(adapter['snippets']), self.module.SLOTS)
                self.assertEqual(adapter['id'], path.stem)


if __name__ == '__main__':
    unittest.main()
