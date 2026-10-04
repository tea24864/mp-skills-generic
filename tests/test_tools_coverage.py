"""Accounting-contract tests for tools/coverage.py (upstream ledger coverage).

Mirrors the pstack-generic coverage role: every pinned upstream file must be
accounted for exactly once (promoted / stash / remainder) and any unknown
upstream file must make --check fail. Built on real repository data (the whole
point: 79 + 87 + remainder == 172) plus isolated sandbox corruptions.
"""
from pathlib import Path
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
import contextlib
import os

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'provenance/coverage.json'
STAGED_SRC = 'upstream/mattpocock-skills'


def load_coverage(name, module_path):
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec and spec.loader, 'coverage.py must be loadable'
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoverageAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_coverage('mp_coverage', ROOT / 'tools/coverage.py')
        cls.fresh = cls.module.build(ROOT)

    def test_accounting_sums_to_the_pinned_revision(self):
        counts = self.fresh['counts']
        self.assertEqual(counts['promoted'] + counts['stash'] + counts['remainder'],
                         counts['total'])
        self.assertEqual(counts, {'promoted': 79, 'stash': 87, 'remainder': 6,
                                  'total': 172})

    def test_every_upstream_file_accounted_exactly_once(self):
        fresh = self.fresh
        paths = [r['upstream_path'] for r in fresh['files']]
        self.assertEqual(len(paths), len(set(paths)))
        upstream = set(json.loads(
            (ROOT / 'provenance/upstream-full-revision-hashes.json').read_text()
        )['sha256_by_path'])
        self.assertEqual(set(paths), upstream)

    def test_dispositions_have_targets_or_recorded_verdicts(self):
        for record in self.fresh['files']:
            if record['disposition'] == 'stash':
                self.assertTrue(record['target'])
                self.assertEqual(record['relationship'], 'byte-identical')
            elif record['disposition'] == 'promoted' and record['target'] is None:
                self.assertEqual(record['relationship'], 'carried-declined')
            elif record['disposition'] == 'remainder':
                self.assertIsNone(record['target'])
                self.assertIn(record['upstream_path'], self.fresh['remainder_detail'])

    def test_ledger_on_disk_matches_recomputation(self):
        fresh = self.module.consume(ROOT, 'provenance/coverage.json')
        self.assertEqual(fresh['counts']['promoted'], 79)
        self.assertEqual(fresh['counts']['total'], 172)

    def test_check_cli_passes_and_writes_nothing(self):
        before = LEDGER.read_text()
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = self.module.main(['--check'])
        self.assertEqual(code, 0)
        self.assertIn('172', stream.getvalue())
        self.assertEqual(LEDGER.read_text(), before)


class CoverageFailureModes(unittest.TestCase):
    """Unknown upstream files and tampered records must break --check/refusals."""

    def setUp(self):
        load = load_coverage
        self.module = load('mp_coverage_failure', ROOT / 'tools/coverage.py')
        self.temp = tempfile.TemporaryDirectory(prefix='mp-coverage-', dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.temp.cleanup)
        self.sandbox = Path(self.temp.name)
        for name in ('provenance/upstream-full-revision-hashes.json',
                     'provenance/promoted-files.json',
                     'provenance/reference-only-stash.json',
                     'provenance/remainder-review.json',
                     'provenance/coverage.json',
                     'inventory.json'):
            (self.sandbox / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, self.sandbox / name)
        shutil.copytree(ROOT / 'provenance/reference-only',
                        self.sandbox / 'provenance/reference-only')
        shutil.copytree(ROOT / 'core', self.sandbox / 'core')
        shutil.copytree(ROOT / STAGED_SRC, self.sandbox / STAGED_SRC)

    def check(self):
        """Run a fresh --check against the sandbox and return exit code/stderr."""
        stream = io.StringIO()
        exit_code = None
        try:
            with contextlib.redirect_stderr(stream):
                code = self.module.main(['--check'], repo=self.sandbox)
            exit_code = code
        except SystemExit as error:
            exit_code = error.code or 0
        return exit_code, stream.getvalue()

    def recompute_ledger_in_sandbox(self):
        """--check compares against a committed ledger; rebuild it after tampering."""
        fresh = self.module.build(self.sandbox)
        self.module.write(self.sandbox, 'provenance/coverage.json', fresh)

    def test_unknown_upstream_file_fails_check(self):
        manifest_path = self.sandbox / 'provenance/upstream-full-revision-hashes.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['sha256_by_path']['skills/engineering/alien/SKILL.md'] = '0' * 64
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Unaccounted upstream file'):
            self.module.build(self.sandbox)
        exit_code, stderr = self.check()
        self.assertNotEqual(exit_code, 0)
        self.assertIn('coverage refused', stderr)

    def test_unknown_upstream_file_in_fresh_build_fails_summary_arithmetic(self):
        manifest_path = self.sandbox / 'provenance/upstream-full-revision-hashes.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['sha256_by_path']['skills/engineering/alien/SKILL.md'] = 'a' * 64
        manifest_path.write_text(json.dumps(manifest))
        exit_code, stderr = self.check()
        self.assertNotEqual(exit_code, 0)
        self.assertIn('Unaccounted upstream file', stderr)

    def test_remainder_review_removal_breaks_check(self):
        review_path = self.sandbox / 'provenance/remainder-review.json'
        review = json.loads(review_path.read_text())
        review['files'] = [e for e in review['files'] if e['path'] != 'LICENSE']
        review_path.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'Unaccounted upstream file'):
            self.module.build(self.sandbox)

    def test_stash_corruption_fails_build(self):
        victim = self.sandbox / ('provenance/reference-only/infra/'
                                 '.changeset/config.json')
        data = victim.read_bytes()
        victim.write_bytes(data[:-1] + bytes([data[-1] ^ 0x20]))
        with self.assertRaisesRegex(ValueError, 'differs from pinned'):
            self.module.build(self.sandbox)

    def test_promoted_target_corruption_fails_build(self):
        # mp-wizard/template.sh is one of the 24 byte-identical carriers; a flipped
        # byte breaks the pinned sha and must flip the subset arithmetic failure.
        victim = self.sandbox / 'core/skills/mp-wizard/template.sh'
        data = victim.read_bytes()
        victim.write_bytes(data[:-1] + bytes([data[-1] ^ 0x20]))
        with self.assertRaisesRegex(ValueError, 'arithmetic changed'):
            self.module.build(self.sandbox)


if __name__ == '__main__':
    unittest.main()
