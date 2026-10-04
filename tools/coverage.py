"""Rebuild/verify the full upstream-accounting ledger (provenance/coverage.json).

Every file of the pinned upstream revision (provenance/upstream-full-revision-hashes.json,
172 tracked files at pin d81f3a183412e71a5b1e84ca21bc1a35eea03a60) must be accounted
for exactly once, with a disposition, a relationship and a target:

  * promoted  - the 79 staged files (provenance/promoted-files.json). 52 map to an
                authored target under core/skills/mp-<skill>/ (24 byte-identical, 28
                adapted); 25 agents/openai.yaml OpenAI agent-registration carriers were
                declined by the review and are recorded with disposition 'promoted',
                relationship 'carried-declined', no target.
  * stash     - reference-only files under provenance/reference-only/ (87 total: 65
                infra copies listed in provenance/reference-only-stash.json 'copied',
                plus the 22 on-disk in-progress/misc skill files). Copies are stored
                at reference-only/infra/<upstream path> and
                reference-only/skills/<group>/<skill>/<upstream rest>.
  * remainder - upstream files intentionally not staged (6). Each must be named
                verbatim in provenance/remainder-review.json with a written reason;
                count may not drift.

The committed upstream/mattpocock-skills/ snapshot must contain exactly the promoted
skills tree plus the upstream LICENSE (MIT license provenance for the promoted texts);
any other file from the revision staged there is an error.

--check verifies the committed ledger against a freshly recomputed pass and exits
nonzero on any unaccounted or double-claimed upstream file; without --check the
ledger is (re)written. Only provenance/coverage.json is written, nothing else.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
LEDGER = 'provenance/coverage.json'
PIN_MANIFEST = 'provenance/upstream-full-revision-hashes.json'
PROMOTED = 'provenance/promoted-files.json'
STASH = 'provenance/reference-only-stash.json'
INVENTORY = 'inventory.json'
REMAINDER_REVIEW = 'provenance/remainder-review.json'
SNAPSHOT = 'provenance/snapshot-manifest.json'
STAGED = 'upstream/mattpocock-skills'
CORE = 'core/skills'
CARRIER_SUFFIX = '/agents/openai.yaml'
CHECKED_FIELDS = ('disposition', 'relationship', 'target', 'target_sha256',
                  'upstream_sha256')
EXPECTED_PROMOTED_DETAIL = {'byte_identical': 24, 'adapted': 28, 'carrier_declined': 27}


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(repo, name):
    return json.loads((repo / name).read_text())


def load_stash(repo, stash):
    """{upstream_path: on-disk path} for every reference-only stash file.

    Infra copies live at reference-only/infra/<upstream path>; the in-progress and
    misc skill files at reference-only/skills/<group>/<skill>/<upstream rest>.
    """
    mapping = {path: repo / 'provenance/reference-only/infra' / path
               for path in stash['infra'].get('copied', [])}
    reference = repo / 'provenance/reference-only'
    for group_name, group in stash['groups'].items():
        for entry in group['skills']:
            base = reference / 'skills' / group_name / entry['name']
            for candidate in sorted(base.rglob('*')):
                if not candidate.is_file():
                    continue
                rel = candidate.relative_to(reference).as_posix()
                if rel in mapping:
                    raise ValueError('Stash file double-claimed: ' + rel)
                mapping[rel] = candidate
    declared = sum(group['total_files'] for group in stash['groups'].values())
    if len(mapping) != len(stash['infra'].get('copied', [])) + declared:
        raise ValueError('Reference-only stash does not match its own declaration '
                         '(%d declared, %d found)' % (declared, len(mapping)))
    return mapping


def promoted_rel(entry):
    """Map a promoted upstream path onto its authored target under core/skills/."""
    parts = entry['upstream_path'].split('/')
    return 'mp-' + entry['skill'] + '/' + '/'.join(parts[3:])


def build(repo):
    """Recompute the full accounting from provenance records, disk and the core tree."""
    pin_manifest = read_json(repo, PIN_MANIFEST)
    pin, upstream = pin_manifest['pin'], pin_manifest['sha256_by_path']
    staged_doc = read_json(repo, PROMOTED)
    if staged_doc['pin'] != pin:
        raise ValueError('Promoted-set pin differs from full-revision pin')
    stash_doc = read_json(repo, STASH)
    if stash_doc['pin'] != pin:
        raise ValueError('Reference-only stash pin differs from full-revision pin')
    inv = read_json(repo, INVENTORY)
    by_upstream = {e['upstream'] for e in inv['skills']}

    promoted, declared_targets = {}, set()
    for entry in staged_doc['files']:
        path = entry['upstream_path']
        rel = promoted_rel(entry)
        if entry['skill'] not in by_upstream:
            raise ValueError('Promoted skill missing from inventory: ' + entry['skill'])
        if path in promoted:
            raise ValueError('Duplicate promoted upstream path: ' + path)
        if rel in declared_targets:
            raise ValueError('Two promoted upstream files map to: ' + rel)
        if not path.endswith(CARRIER_SUFFIX):
            declared_targets.add(rel)
        promoted[path] = entry

    stash_paths = load_stash(repo, stash_doc)
    overlap = sorted(promoted.keys() & stash_paths.keys())
    if overlap:
        raise ValueError('Upstream file claimed by both promoted set and stash: '
                         + str(overlap))

    # Verdicts for the six intentionally-unstaged files; an upstream file that is
    # neither promoted, nor stashed, nor verdict-covered here is unaccounted.
    remainder_doc = read_json(repo, REMAINDER_REVIEW)
    if remainder_doc.get('pin') != pin:
        raise ValueError('Remainder review pin differs from full-revision pin')
    recorded = {e['path']: e for e in remainder_doc.get('files', [])
                if isinstance(e, dict) and e.get('path') and e.get('reason')}
    recorded_sha = {e['path']: e for e in remainder_doc.get('files', [])
                    if isinstance(e, dict) and e.get('path')}

    rows = []
    for path in sorted(upstream):
        sha = upstream[path]
        if path in promoted:
            record = {'upstream_path': path, 'disposition': 'promoted',
                      'mp_skill': 'mp-' + promoted[path]['skill'],
                      'target': None, 'target_sha256': None, 'upstream_sha256': sha,
                      'relationship': ('carried-declined'
                                       if path.endswith(CARRIER_SUFFIX) else None)}
            if not record['relationship']:
                rel = promoted_rel(promoted[path])
                target = repo / CORE / rel
                if not target.is_file():
                    raise ValueError('Promoted file has no authored target: ' + path)
                actual = sha256_of(target)
                if actual != sha and promoted[path]['sha256'] != sha:
                    raise ValueError('Promoted ledger sha256 differs from the pinned '
                                     'upstream revision: ' + path)
                record['target'] = rel
                record['target_sha256'] = actual
                record['relationship'] = ('byte-identical' if actual == sha
                                          else 'adapted')
        elif path in stash_paths:
            if sha256_of(stash_paths[path]) != sha:
                raise ValueError('Reference-only stash copy differs from pinned '
                                 'upstream: ' + path)
            record = {'upstream_path': path, 'disposition': 'stash',
                      'target': 'provenance/reference-only/' + path,
                      'target_sha256': sha, 'upstream_sha256': sha,
                      'relationship': 'byte-identical'}
        else:
            if path not in recorded:
                raise ValueError('Unaccounted upstream file: ' + path)
            verdict_sha = recorded_sha[path].get('sha256')
            if verdict_sha not in (None, sha):
                raise ValueError('Remainder review sha256 differs from the pinned '
                                 'upstream file: ' + path)
            record = {'upstream_path': path, 'disposition': 'remainder',
                      'target': None, 'target_sha256': None, 'upstream_sha256': sha,
                      'relationship': 'declined-not-staged'}
        rows.append(record)

    counts = {
        'promoted': len(promoted),
        'stash': sum(1 for r in rows if r['disposition'] == 'stash'),
        'remainder': sum(1 for r in rows if r['disposition'] == 'remainder'),
        'total': len(upstream)}
    rows_by_path = {r['upstream_path'] for r in rows}
    missing = sorted(upstream.keys() - rows_by_path)
    extra = sorted(rows_by_path - upstream.keys())
    if missing or extra:
        raise ValueError('Upstream accounting is not one-to-one; missing=%s extra=%s'
                         % (missing[:4], extra[:4]))
    if counts['promoted'] + counts['stash'] + counts['remainder'] != len(upstream):
        raise ValueError('Coverage does not sum to the upstream revision: %r vs %d '
                         'files' % (counts, len(upstream)))
    if len(promoted) != 79 or len(upstream) != 172 or len(stash_paths) != 87:
        raise ValueError('Coverage contract counts changed: %d promoted, %d upstream, '
                         '%d stash' % (len(promoted), len(upstream), len(stash_paths)))

    detail = {'byte_identical': sum(1 for r in rows if r['disposition'] == 'promoted'
                                    and r['relationship'] == 'byte-identical'),
              'adapted': sum(1 for r in rows if r['disposition'] == 'promoted'
                             and r['relationship'] == 'adapted'),
              'carrier_declined': sum(1 for r in rows if r['disposition'] == 'promoted'
                                      and r['relationship'] == 'carried-declined')}
    if detail != EXPECTED_PROMOTED_DETAIL:
        raise ValueError('Promoted subset arithmetic changed: ' + json.dumps(detail))

    # Every verdict-covered file must actually be a remainder row and vice versa;
    # the recorded sha256 (when present) must match the pinned upstream entry.
    remainder = [r['upstream_path'] for r in rows if r['disposition'] == 'remainder']
    if set(recorded) != set(remainder):
        raise ValueError('Remainder review coverage mismatch; recorded=%s rows=%s'
                         % (sorted(set(recorded) - set(remainder))[:4],
                            sorted(set(remainder) - set(recorded))[:4]))

    staged_root = repo / STAGED
    if staged_root.is_dir():
        staged = {p.relative_to(staged_root).as_posix() for p in staged_root.rglob('*')
                  if p.is_file()}
        staged_skills = {p for p in staged if p.startswith('skills/')}
        if staged_skills != {p for p in promoted if p.startswith('skills/')}:
            raise ValueError('Staged skills tree is not exactly the promoted set')
        # The snapshot root may carry the upstream LICENSE (MIT license provenance for
        # the promoted skill texts); any other revision file staged there is an error.
        expressive = (staged - staged_skills) - {'LICENSE'}
        if expressive:
            raise ValueError('Staged snapshot carries non-skill upstream files: '
                             + str(sorted(expressive)[:4]))
        if 'LICENSE' in staged and sha256_of(staged_root / 'LICENSE') != upstream['LICENSE']:
            raise ValueError('Staged LICENSE differs from the pinned upstream LICENSE')

    core_names = {p.parent.name for p in (repo / CORE).glob('*/SKILL.md')}
    if core_names != {e['name'] for e in inv['skills']}:
        raise ValueError('Authored core differs from the inventory skill set')
    promoted_targets = {r['target'] for r in rows if r['target']
                        and r['disposition'] == 'promoted'}
    core_files = {p.relative_to(repo / CORE).as_posix()
                  for p in (repo / CORE).rglob('*') if p.is_file()}
    if core_files != promoted_targets:
        raise ValueError('Authored core contains unmapped files: %s; missing: %s'
                         % (sorted(core_files - promoted_targets)[:4],
                            sorted(promoted_targets - core_files)[:4]))

    return {'schema_version': 1, 'pin': pin, 'counts': counts,
            'promoted_detail': detail,
            'stash_detail': {'infra': len(stash_doc['infra'].get('copied', [])),
                             'in_progress': stash_doc['groups']['in-progress']['total_files'],
                             'misc': stash_doc['groups']['misc']['total_files']},
            'remainder_detail': recorded,
            'files': rows}


def consume(repo, ledger):
    """Verify the committed ledger equals the freshly recomputed accounting."""
    committed = read_json(repo, ledger)
    fresh = build(repo)
    rows = committed.get('files')
    if not isinstance(rows, list):
        raise ValueError('Committed ledger has no file rows')
    seen = [r.get('upstream_path') for r in rows]
    if len(set(seen)) != len(seen):
        raise ValueError('Committed ledger lists an upstream path more than once')
    fresh_rows = {r['upstream_path']: r for r in fresh['files']}
    if set(seen) != set(fresh_rows):
        raise ValueError('Committed ledger diverges; missing=%s extra=%s'
                         % (sorted(set(fresh_rows) - set(seen))[:4],
                            sorted(set(seen) - set(fresh_rows))[:4]))
    by_path = {r.get('upstream_path'): r for r in rows}
    for path, row in fresh_rows.items():
        for field in CHECKED_FIELDS:
            if by_path[path].get(field) != row.get(field):
                raise ValueError('Committed ledger field %s differs for %s'
                                 % (field, path))
    for key in ('schema_version', 'pin', 'counts', 'promoted_detail', 'stash_detail',
                'remainder_detail'):
        if committed.get(key) != fresh[key]:
            raise ValueError('Committed ledger summary differs for: ' + key)
    return fresh


def write(repo, ledger, result):
    (repo / ledger).write_text(json.dumps(result, indent=2) + '\n')


def main(argv=None, repo=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='Verify the committed ledger only; do not rewrite')
    args = parser.parse_args(argv)
    repo = repo or ROOT
    try:
        if args.check:
            fresh = consume(repo, LEDGER)
            print(json.dumps({'verified': True, 'pin': fresh['pin'],
                              'counts': fresh['counts'],
                              'promoted_detail': fresh['promoted_detail'],
                              'stash_detail': fresh['stash_detail'],
                              'remainder': sorted(fresh['remainder_detail'])},
                             indent=2))
            return 0
        fresh = build(repo)
        write(repo, LEDGER, fresh)
        print(json.dumps({'written': LEDGER, 'pin': fresh['pin'],
                          'counts': fresh['counts']}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, 'coverage refused: ' + str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
