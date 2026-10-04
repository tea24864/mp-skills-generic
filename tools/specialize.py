"""Deterministically specialize neutral skill source without a runtime engine."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
SLOTS = frozenset('files delegation task_tracking history skill_loading skill_maintenance configuration integrations persistent_work web setup'.split())
SLOT = re.compile(r'\{\{runtime\.([a-z_]+)\}\}')
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_adapter(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError('Adapter must be a JSON object')
    identity = data.get('identity_tools')
    if not isinstance(identity, list) or any(not isinstance(tool, str) or not tool for tool in identity):
        raise ValueError('identity_tools must be a list of actual tool names')
    if data.get('schema_version') != 1 or not NAME.fullmatch(data.get('id', '')):
        raise ValueError('Invalid runtime adapter identity/schema')
    snippets = data.get('snippets', {})
    if set(snippets) != SLOTS:
        raise ValueError('Adapter must define exactly the supported insertion points')
    if any(not isinstance(value, str) or len(value) > 2200 or '{{' in value for value in snippets.values()):
        raise ValueError('Adapter snippets must be short literal instructions, not templates or code')
    if not isinstance(data.get('limits'), list) or not isinstance(data.get('capabilities'), dict):
        raise ValueError('Adapter must declare capability limits')
    return data


def detect(evidence, adapter_paths):
    """Identify only reviewed adapters whose actual identity tools were observed."""
    tools = evidence.get('tool_names')
    if not isinstance(tools, list) or any(not isinstance(tool, str) for tool in tools):
        raise ValueError('Evidence must list actually observed tool_names')
    candidates = []
    for path in adapter_paths:
        adapter = load_adapter(path)
        identity = adapter.get('identity_tools', [])
        if identity and set(identity) <= set(tools):
            candidates.append(adapter['id'])
    candidates.sort()
    return {'runtime': candidates[0] if len(candidates) == 1 else None,
            'candidates': candidates, 'needs_selection': len(candidates) != 1,
            'reason': 'Observed identity tools' if len(candidates) == 1 else 'Unknown or ambiguous runtime; explicit selection/review required'}


def validate_frontmatter(text, directory_name):
    """Validate the deliberately small, standard-format authored YAML dialect."""
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError('Missing standard skill frontmatter')
    head, body = text[4:].split('\n---\n', 1)
    fields, metadata = {}, {}
    in_metadata = False
    allowed = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}
    for line in head.splitlines():
        if not line.strip():
            continue
        if line.startswith('  '):
            match = re.fullmatch(r'  ([a-zA-Z0-9_-]+): (.+)', line)
            if not in_metadata or not match:
                raise ValueError('Core metadata must be a flat string mapping')
            key, literal = match.groups()
            if key in metadata:
                raise ValueError('Duplicate core metadata field: ' + key)
            value = json.loads(literal) if literal.startswith('"') else literal
            if not isinstance(value, str) or literal in ('true', 'false', 'null') or literal.startswith(('[', '{')):
                raise ValueError('Core metadata values must be strings: ' + key)
            metadata[key] = value
            continue
        match = re.fullmatch(r'([a-z-]+):(?: (.+))?', line)
        if not match or match.group(1) not in allowed:
            raise ValueError('Unsupported core frontmatter field')
        key, literal = match.groups()
        if key in fields:
            raise ValueError('Duplicate core frontmatter field: ' + key)
        in_metadata = key == 'metadata'
        if in_metadata:
            if literal is not None:
                raise ValueError('Core metadata must be a flat string mapping')
            fields[key] = metadata
        else:
            fields[key] = json.loads(literal) if literal and literal.startswith('"') else literal
    if fields.get('name') != directory_name:
        raise ValueError('Skill frontmatter/directory name mismatch')
    description = fields.get('description')
    if not isinstance(description, str) or not description or len(description) > 60 or not description.endswith('.'):
        raise ValueError('Invalid or missing description')
    if fields.get('license') != 'MIT' or not body.strip():
        raise ValueError('MIT license and nonempty workflow body are required')
    return fields


def file_paths(root):
    paths = []
    for p in sorted(Path(root).rglob('*')):
        if '__pycache__' in p.parts or p.suffix == '.pyc':
            continue
        if p.is_symlink():
            raise ValueError('Symlink in skill source/distribution: ' + str(p))
        if p.is_file():
            paths.append(p)
    return paths


def build(core, adapter_path, output, *, runtime_version=None):
    core, output = Path(core).resolve(), Path(output).resolve()
    adapter_path = Path(adapter_path).resolve()
    adapter = load_adapter(adapter_path)
    if output.exists():
        raise ValueError('Refusing existing output: ' + str(output))
    if output == core or core in output.parents:
        raise ValueError('Output must not be inside authored source')
    paths = file_paths(core)
    skills = {p.parent.name for p in paths if p.name == 'SKILL.md'}
    if not skills or any(not NAME.fullmatch(name) or len(name) > 64 for name in skills):
        raise ValueError('No valid skill entrypoints')
    source_files, rendered = [], []
    for p in paths:
        rel = p.relative_to(core)
        if rel.parts[0] not in skills:
            raise ValueError('Artifact is outside a named skill: ' + str(rel))
        data = p.read_bytes()
        source_files.append({'path': rel.as_posix(), 'sha256': digest(data)})
        if p.suffix == '.md':
            text = data.decode('utf-8')
            keys = set(SLOT.findall(text))
            if not keys <= SLOTS:
                raise ValueError('Unknown insertion point in ' + str(rel))
            text = SLOT.sub(lambda match: adapter['snippets'][match.group(1)], text)
            if '{{' in text or '}}' in text:
                raise ValueError('Unresolved template syntax in ' + str(rel))
            if p.name == 'SKILL.md':
                fields = validate_frontmatter(text, rel.parts[0])
                extension = adapter.get('metadata_by_skill', {}).get(rel.parts[0])
                if isinstance(extension, str):
                    extension = adapter.get('metadata_blocks', {}).get(extension)
                    if not isinstance(extension, dict):
                        raise ValueError('Missing runtime metadata block')
                if extension:
                    namespace = adapter.get('metadata_namespace', '')
                    if not NAME.fullmatch(namespace) or namespace in fields.get('metadata', {}):
                        raise ValueError('Invalid or conflicting runtime metadata namespace')
                    head, body = text[4:].split('\n---\n', 1)
                    lines = head.splitlines()
                    if 'metadata' not in fields:
                        lines.append('metadata:')
                    lines.insert(lines.index('metadata:') + 1, '  ' + namespace + ': ' + json.dumps(extension))
                    text = '---\n' + '\n'.join(lines) + '\n---\n' + body
            data = text.encode('utf-8')
        rendered.append((rel, data, stat.S_IMODE(p.stat().st_mode)))
    manifest = {'schema_version': 1, 'runtime': adapter['id'], 'runtime_version': runtime_version,
                'capabilities': adapter['capabilities'],
                'limits': adapter['limits'], 'requires_acknowledgement': adapter.get('requires_acknowledgement', False),
                'adapter_sha256': digest(adapter_path.read_bytes()),
                'core_sha256': digest(json.dumps(source_files, sort_keys=True).encode()),
                'skills': sorted(skills), 'source_files': source_files,
                'files': [{'path': ('skills' / rel).as_posix(), 'sha256': digest(data), 'bytes': len(data)}
                          for rel, data, mode in rendered]}
    output.mkdir(parents=True, exist_ok=False)
    try:
        for rel, data, mode in rendered:
            target = output / 'skills' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(mode)
        (output / 'distribution.json').write_text(json.dumps(manifest, indent=2) + '\n')
    except Exception:
        shutil.rmtree(output)
        raise
    return {'runtime': adapter['id'], 'skills': len(skills), 'files': len(rendered),
            'output': str(output), 'capabilities': adapter['capabilities'], 'limits': adapter['limits']}


def verify_distribution(distribution):
    distribution = Path(distribution).resolve()
    manifest = json.loads((distribution / 'distribution.json').read_text())
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported distribution schema')
    expected = {record['path'] for record in manifest['files']}
    actual = {p.relative_to(distribution).as_posix() for p in file_paths(distribution / 'skills')}
    if expected != actual or len(expected) != len(manifest['files']):
        raise ValueError('Distribution artifact set changed')
    names = {p.parent.name for p in (distribution / 'skills').glob('*/SKILL.md')}
    if names != set(manifest['skills']) or any(not NAME.fullmatch(n) or len(n) > 64 for n in names):
        raise ValueError('Distribution skill names invalid')
    for record in manifest['files']:
        if digest((distribution / record['path']).read_bytes()) != record['sha256']:
            raise ValueError('Distribution artifact changed: ' + record['path'])
    return manifest


def install(distribution, skills_dir, *, acknowledge_limits=False):
    distribution = Path(distribution).resolve()
    skills_dir = Path(skills_dir).expanduser().resolve()
    manifest = verify_distribution(distribution)
    if manifest.get('requires_acknowledgement') and not acknowledge_limits:
        raise ValueError('Explicit acknowledgement of generic capability limits is required')
    names = manifest['skills']
    existing = [p for p in skills_dir.rglob('SKILL.md') if p.parent.name in names]
    record = skills_dir / '.pstack-runtime.json'
    if existing or record.exists() or any((skills_dir / name).exists() for name in names):
        raise ValueError('Refusing existing skills/runtime record; use a reviewed migration')
    skills_dir.mkdir(parents=True, exist_ok=True)
    owned = []
    record_owned = False
    try:
        for name in names:
            target = skills_dir / name
            target.mkdir(exist_ok=False)
            owned.append(target)
            shutil.copytree(distribution / 'skills' / name, target, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        actual = {('skills' / p.relative_to(skills_dir)).as_posix()
                  for name in names for p in file_paths(skills_dir / name)}
        if actual != {item['path'] for item in manifest['files']}:
            raise ValueError('Installed artifact set differs from generated distribution')
        for item in manifest['files']:
            rel = Path(item['path']).relative_to('skills')
            if digest((skills_dir / rel).read_bytes()) != item['sha256']:
                raise ValueError('Installed artifact readback mismatch: ' + str(rel))
        with record.open('x') as stream:
            record_owned = True
            json.dump({k: manifest[k] for k in ('schema_version', 'runtime', 'runtime_version', 'capabilities', 'limits',
                                               'adapter_sha256', 'core_sha256', 'skills', 'files')}, stream, indent=2)
            stream.write('\n')
        if json.loads(record.read_text())['core_sha256'] != manifest['core_sha256']:
            raise ValueError('Installed runtime record readback mismatch')
    except Exception:
        if record_owned:
            record.unlink(missing_ok=True)
        for target in reversed(owned):
            shutil.rmtree(target)
        raise
    return {'runtime': manifest['runtime'], 'installed_skills': len(names),
            'installed_files': len(manifest['files']), 'skills_dir': str(skills_dir),
            'limits': manifest['limits']}


def uninstall(skills_dir, *, confirm=False):
    """Remove only a complete, unchanged installation recorded by this setup tool."""
    skills_dir = Path(skills_dir).expanduser().resolve()
    record = skills_dir / '.pstack-runtime.json'
    if record.is_symlink() or not record.is_file():
        raise ValueError('Missing or linked uninstall receipt; no removal authorized')
    receipt = json.loads(record.read_text())
    names = receipt.get('skills')
    files = receipt.get('files')
    if receipt.get('schema_version') != 1 or not isinstance(names, list) or not names or not isinstance(files, list) or not files:
        raise ValueError('Missing uninstall ownership hashes; legacy installs require a reviewed migration')
    if len(set(names)) != len(names) or any(not isinstance(n, str) or not NAME.fullmatch(n) or not n.startswith('pstack-') or len(n) > 64 for n in names):
        raise ValueError('Invalid uninstall skill names')
    expected = {}
    for item in files:
        path = item['path']
        rel = Path(path)
        if rel.as_posix() != path or rel.is_absolute() or '..' in rel.parts or len(rel.parts) < 3 or rel.parts[0] != 'skills' or rel.parts[1] not in names:
            raise ValueError('Invalid uninstall artifact path')
        sha = item['sha256']
        if path in expected or not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
            raise ValueError('Invalid uninstall artifact hash/duplicate')
        expected[path] = sha
    if any('skills/' + name + '/SKILL.md' not in expected for name in names):
        raise ValueError('Missing uninstall entrypoint ownership hash')
    expected_dirs = {Path(path).parent for path in expected}
    expected_dirs = {parent.as_posix() for path in expected_dirs for parent in (path, *path.parents)}
    actual = {}
    for name in names:
        target = skills_dir / name
        if target.is_symlink() or not target.is_dir():
            raise ValueError('Missing or linked installed skill: ' + name)
        for path in target.rglob('*'):
            if path.is_symlink():
                raise ValueError('Linked installed artifact: ' + str(path))
            if path.is_file():
                actual[('skills' / path.relative_to(skills_dir)).as_posix()] = digest(path.read_bytes())
            elif path.is_dir():
                if ('skills' / path.relative_to(skills_dir)).as_posix() not in expected_dirs:
                    raise ValueError('Unrecorded installed directory: ' + str(path))
            else:
                raise ValueError('Unsupported installed artifact: ' + str(path))
    if actual != expected:
        raise ValueError('Installed files changed, missing or added; preserve/review local edits before uninstall')
    result = {'runtime': receipt['runtime'], 'skills_dir': str(skills_dir), 'dry_run': not confirm,
              'skills': sorted(names), 'files': len(expected)}
    if not confirm:
        return result
    import tempfile
    staging = Path(tempfile.mkdtemp(prefix='.pstack-uninstall-', dir=skills_dir))
    moved = []
    try:
        for source in [*(skills_dir / name for name in names), record]:
            destination = staging / source.name
            source.rename(destination)
            moved.append((source, destination))
    except Exception:
        for source, destination in reversed(moved):
            destination.rename(source)
        staging.rmdir()
        raise
    try:
        shutil.rmtree(staging)
    except OSError as error:
        raise OSError('Uninstall cleanup incomplete; inspect recoverable staging at ' + str(staging)) from error
    if record.exists() or any((skills_dir / name).exists() for name in names):
        raise ValueError('Uninstall readback failed')
    result['removed_skills'] = len(names)
    result['removed_files'] = len(expected)
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    detector = commands.add_parser('detect', help='Propose a runtime using actual observed tool evidence')
    detector.add_argument('--evidence', type=Path, required=True)
    detector.add_argument('--adapters-dir', type=Path, default=ROOT / 'adapters')
    builder = commands.add_parser('build', help='Render one reviewed runtime without changing installed skills')
    builder.add_argument('--runtime', required=True)
    builder.add_argument('--runtime-version', help='Actually observed version; omitted means unreported, not inferred')
    builder.add_argument('--output', type=Path, required=True)
    builder.add_argument('--core', type=Path, default=ROOT / 'core/skills')
    builder.add_argument('--adapters-dir', type=Path, default=ROOT / 'adapters')
    installer = commands.add_parser('install', help='Install a verified distribution into one confirmed destination')
    installer.add_argument('--distribution', type=Path, required=True)
    destination = installer.add_mutually_exclusive_group(required=True)
    destination.add_argument('--skills-dir', type=Path)
    destination.add_argument('--home', type=Path, help='Hermes only: explicitly selected home')
    installer.add_argument('--acknowledge-limits', action='store_true')
    remover = commands.add_parser('uninstall', help='Preview receipt-owned removal; --yes applies after integrity checks')
    removal_target = remover.add_mutually_exclusive_group(required=True)
    removal_target.add_argument('--skills-dir', type=Path)
    removal_target.add_argument('--home', type=Path, help='Hermes only: explicitly selected home')
    remover.add_argument('--yes', action='store_true', help='Confirm removal of the verified installation')
    checker = commands.add_parser('verify', help='Verify generated artifact set/hashes')
    checker.add_argument('--distribution', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == 'detect':
            result = detect(json.loads(args.evidence.read_text()), sorted(args.adapters_dir.glob('*.json')))
        elif args.action == 'build':
            if not NAME.fullmatch(args.runtime):
                raise ValueError('Select a reviewed adapter by exact runtime name')
            adapter = args.adapters_dir / (args.runtime + '.json')
            if not adapter.is_file():
                raise ValueError('No reviewed adapter for runtime ' + args.runtime + '; review a new adapter or explicitly select the limited generic baseline')
            if args.core.resolve() == (ROOT / 'core/skills').resolve():
                names = {p.parent.name for p in args.core.glob('*/SKILL.md')}
                expected = {e['name'] for e in json.loads((ROOT / 'inventory.json').read_text())['skills']}
                if names != expected:
                    raise ValueError('Incomplete authored skill coverage')
            result = build(args.core, adapter, args.output, runtime_version=args.runtime_version)
        elif args.action == 'install':
            manifest = verify_distribution(args.distribution)
            if args.home is not None and manifest['runtime'] != 'hermes':
                raise ValueError('Only the Hermes adapter defines --home; choose --skills-dir explicitly')
            target = args.skills_dir if args.skills_dir is not None else args.home.expanduser() / 'skills'
            result = install(args.distribution, target, acknowledge_limits=args.acknowledge_limits)
        elif args.action == 'uninstall':
            target = args.skills_dir if args.skills_dir is not None else args.home.expanduser() / 'skills'
            if args.home is not None:
                receipt = json.loads((target / '.pstack-runtime.json').read_text())
                if receipt.get('runtime') != 'hermes':
                    raise ValueError('Only the Hermes adapter defines --home; choose --skills-dir explicitly')
            result = uninstall(target, confirm=args.yes)
        else:
            manifest = verify_distribution(args.distribution)
            result = {'runtime': manifest['runtime'], 'skills': len(manifest['skills']),
                      'files': len(manifest['files']), 'verified': True, 'limits': manifest['limits']}
        print(json.dumps(result, indent=2))
        if args.action == 'detect' and result['needs_selection']:
            return 2
        return 0
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, 'Setup refused: ' + str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
