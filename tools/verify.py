"""One-command verification chain for a fresh clone of this port.

Phases (each prints 'phase <n> <name>: PASS' or ': FAIL <reason>' and the chain
exits 0 only when every phase passed):
  1. unittest     - full committed test suite
  2. coverage     - upstream accounting ledger (--check) over all 172 pinned files
  3. adapters     - build BOTH authored adapters via tools/specialize.py CLI into
                    disposable temp dirs and verify_distribution each
  4. determinism  - build the hermes distribution twice (once under a path with
                    spaces) and compare skills-tree hash + core_sha256
  5. lifecycle    - install -> preview-uninstall -> uninstall -> reinstall ->
                    uninstall in a disposable skills dir, asserting skill/file
                    counts and that an unrelated file inside the skills dir
                    survives every step
  6. refusals     - a flipped receipt byte refuses uninstall; a flipped distributed
                    SKILL.md byte refuses verify_distribution
  7. frontmatter  - scan every SKILL.md of a freshly built hermes distribution with
                    the committed frontmatter dialect rules

The chain touches only tempfile-managed directories; the real profile at ~/.hermes
is never used.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ('hermes', 'generic')
EXPECTED_SKILLS = 27


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, 'tool module must be loadable: ' + str(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_hash(root):
    """Stable hash over the sorted relative paths and bytes of every file below root."""
    digest = hashlib.sha256()
    for path in sorted(Path(root).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b'\0')
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


class Chain:
    def __init__(self):
        self.failures = []

    def phase(self, number, name, function):
        try:
            detail = function() or {}
        except Exception as error:  # noqa: BLE001 - the chain must survive any phase
            print('phase %d %s: FAIL %s' % (number, name,
                                            str(error).replace('\n', ' | ')), flush=True)
            self.failures.append((number, name, str(error)))
            return None
        print('phase %d %s: PASS%s' % (number, name,
                                       (' :: ' + detail['summary']) if detail.get('summary') else ''),
              flush=True)
        return detail


def phase_unittest(base):
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'),
         '-p', 'test_*.py'],
        cwd=ROOT, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise AssertionError('unittest discover returned %d\n%s\n%s'
                             % (result.returncode, result.stdout[-2000:],
                                result.stderr[-2000:]))
    match = re.search(r'Ran (\d+) tests', result.stderr)
    return {'summary': '%s tests OK' % match.group(1) if match else 'tests OK'}


def phase_coverage(base):
    result = subprocess.run([sys.executable, str(ROOT / 'tools/coverage.py'), '--check'],
                            cwd=ROOT, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise AssertionError('coverage --check returned %d: %s'
                             % (result.returncode, (result.stdout + result.stderr)[-800:]))
    counts = json.loads(result.stdout)['counts']
    if counts['total'] != 172 or counts['promoted'] != 79:
        raise AssertionError('Unexpected coverage counts: %r' % counts)
    return {'summary': '%(promoted)dp+%(stash)ds+%(remainder)dr==%(total)d' % counts}


def build_adapter(base, runtime, dest):
    build_dir = base / ('build-%s-%s' % (runtime, dest))
    result = subprocess.run(
        [sys.executable, str(ROOT / 'tools/specialize.py'), 'build',
         '--runtime', runtime, '--output', str(build_dir)],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise AssertionError('build %s failed: %s' % (runtime, result.stderr[-600:]))
    summary = json.loads(result.stdout)
    check = subprocess.run(
        [sys.executable, str(ROOT / 'tools/specialize.py'), 'verify',
         '--distribution', str(build_dir)],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    if check.returncode != 0:
        raise AssertionError('verify %s failed: %s' % (runtime, check.stderr[-600:]))
    return build_dir, summary


def phase_adapters(base):
    detail = []
    for runtime in ADAPTERS:
        build_dir, summary = build_adapter(base, runtime, runtime)
        detail.append('%s=%d skills/%d files' % (runtime, summary['skills'],
                                                 summary['files']))
        if summary['skills'] != EXPECTED_SKILLS:
            raise AssertionError('%s build has %d skills, expected %d'
                                 % (runtime, summary['skills'], EXPECTED_SKILLS))
        module = load_module('mp_specialize_%s' % runtime, ROOT / 'tools/specialize.py')
        module.verify_distribution(build_dir)
    return {'summary': '; '.join(detail)}


def phase_determinism(base):
    first = base / 'det-plain'
    spaced = base / 'det with spaces'
    result = subprocess.run(
        [sys.executable, str(ROOT / 'tools/specialize.py'), 'build',
         '--runtime', 'hermes', '--output', str(first)],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise AssertionError('determinism build 1 failed: ' + result.stderr[-600:])
    result = subprocess.run(
        [sys.executable, str(ROOT / 'tools/specialize.py'), 'build',
         '--runtime', 'hermes', '--output', str(spaced)],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise AssertionError('determinism build 2 failed: ' + result.stderr[-600:])
    first_tree = tree_hash(first / 'skills')
    spaced_tree = tree_hash(spaced / 'skills')
    if first_tree != spaced_tree:
        raise AssertionError('skills tree hashes differ under a spaced build path')
    one = json.loads((first / 'distribution.json').read_text())
    two = json.loads((spaced / 'distribution.json').read_text())
    if one['core_sha256'] != two['core_sha256']:
        raise AssertionError('core_sha256 differs under a spaced build path')
    if one['files'] != two['files']:
        raise AssertionError('distribution manifests differ under a spaced build path')
    return {'summary': 'skills-tree %s.. core_sha256 %s.. equal'
                       % (first_tree[:8], one['core_sha256'][:8])}


def skills_cycle(base):
    module = load_module('mp_specialize_lifecycle', ROOT / 'tools/specialize.py')
    skills_dir = base / 'installed skills'
    ward = skills_dir / 'unrelated-file.txt'
    distribution = base / 'build-hermes-hermes-cycle'
    if not distribution.is_dir():
        distribution, _ = build_adapter(base, 'hermes', 'hermes-cycle')
    receipt = json.loads((distribution / 'distribution.json').read_text())
    expected_files = len(receipt['files'])

    installed = module.install(distribution, skills_dir, acknowledge_limits=True)
    ward.write_text('not owned by the runtime\n')
    if installed['installed_skills'] != EXPECTED_SKILLS \
            or installed['installed_files'] != expected_files:
        raise AssertionError('install counts off: %r' % installed)
    if tuple(sorted(p.name for p in skills_dir.glob('mp-*'))) != \
            tuple(sorted(receipt['skills'])):
        raise AssertionError('installed skill set differs from the receipt')

    preview = module.uninstall(skills_dir)
    if preview['dry_run'] is not True or preview['files'] != expected_files:
        raise AssertionError('uninstall preview counts off: %r' % preview)

    module.uninstall(skills_dir, confirm=True)
    if not ward.is_file() or ward.read_text() != 'not owned by the runtime\n':
        raise AssertionError('uninstall removed or altered the unrelated file')
    if any(p.name.startswith('mp-') for p in skills_dir.iterdir()):
        raise AssertionError('uninstall left skill directories behind')

    installed = module.install(distribution, skills_dir, acknowledge_limits=True)
    if installed['installed_skills'] != EXPECTED_SKILLS:
        raise AssertionError('reinstall counts off: %r' % installed)
    if not ward.is_file():
        raise AssertionError('reinstall disturbed the unrelated file')
    module.uninstall(skills_dir, confirm=True)
    if not ward.is_file():
        raise AssertionError('final uninstall disturbed the unrelated file')
    return {'summary': 'install/preview/uninstall/reinstall/uninstall over %d skills, %d '
                       'files; unrelated file survived' % (EXPECTED_SKILLS,
                                                           expected_files)}


def phase_lifecycle(base):
    return skills_cycle(base)


def flipped(path):
    data = bytearray(path.read_bytes())
    if not data:
        raise AssertionError('empty file cannot be corrupted: ' + str(path))
    data[len(data) // 2] ^= 0x20
    path.write_bytes(bytes(data))
    return data


def phase_refusals(base):
    module = load_module('mp_specialize_refusals', ROOT / 'tools/specialize.py')
    skills_dir = base / 'refusal skills'
    distribution, _ = build_adapter(base, 'hermes', 'hermes-refusals')

    module.install(distribution, skills_dir, acknowledge_limits=True)
    receipt = skills_dir / '.mp-runtime.json'
    flipped(receipt)
    refused = None
    try:
        module.uninstall(skills_dir, confirm=True)
    except ValueError as error:
        refused = str(error)
    if not refused:
        raise AssertionError('corrupted receipt did not refuse uninstall')

    victim = distribution / 'skills' / 'mp-tdd' / 'SKILL.md'
    flipped(victim)
    try:
        module.verify_distribution(distribution)
    except ValueError:
        pass
    else:
        raise AssertionError('corrupted distributed SKILL.md did not refuse verify')
    return {'summary': 'corrupted receipt refuses uninstall; corrupted SKILL.md '
                       'refuses verify_distribution'}


def phase_frontmatter(base):
    module = load_module('mp_specialize_frontmatter', ROOT / 'tools/specialize.py')
    distribution, _ = build_adapter(base, 'hermes', 'hermes-frontmatter')
    count = 0
    for path in sorted((distribution / 'skills').glob('*/SKILL.md')):
        module.validate_frontmatter(path.read_text(), path.parent.name)
        count += 1
    if count != EXPECTED_SKILLS:
        raise AssertionError('frontmatter scan covered %d skills, expected %d'
                             % (count, EXPECTED_SKILLS))
    return {'summary': '%d SKILL.md files pass the committed frontmatter dialect' % count}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keep', type=Path, help='Keep temp artifacts under this dir')
    args = parser.parse_args(argv)
    chain = Chain()
    if args.keep:
        args.keep.mkdir(parents=True, exist_ok=True)
        base = Path(tempfile.mkdtemp(prefix='mp-verify-', dir=args.keep.resolve()))
    else:
        base = Path(tempfile.mkdtemp(prefix='mp-verify-', dir=os.environ.get('TMPDIR')))
    try:
        chain.phase(1, 'unittest', lambda: phase_unittest(base))
        chain.phase(2, 'coverage', lambda: phase_coverage(base))
        chain.phase(3, 'adapters', lambda: phase_adapters(base))
        chain.phase(4, 'determinism', lambda: phase_determinism(base))
        chain.phase(5, 'lifecycle', lambda: phase_lifecycle(base))
        chain.phase(6, 'refusals', lambda: phase_refusals(base))
        chain.phase(7, 'frontmatter', lambda: phase_frontmatter(base))
    finally:
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)
    if chain.failures:
        print('VERIFY: FAIL (%d failing phases: %s)' % (
            len(chain.failures),
            ', '.join('%d-%s' % (number, name) for number, name, _ in chain.failures)))
        return 1
    print('VERIFY: PASS (all 7 phases)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
