"""Fresh-session behavior probes for mp skills using generated files, not the live installation.

Adapted from pstack-generic tools/live_specialized.py run_case mechanics. Fixtures are
authored here for the mp skill set (no import of pstack's live_smoke). Each case embeds
the built mp-<skill>/SKILL.md verbatim in query.txt; supporting files resolve beside it
in the built distribution. Probes are read/write within an isolated temp fixture only.
"""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]

DISCOUNT_MODULE = '''"""Order discounts for the store frontend."""

# Discount tiers: (units_at_or_above, percent_off)
TIER_RATES = [(100, 20.0), (50, 12.0), (10, 10.0), (1, 0.0)]


def bulk_discount_rate(units):
    """Percent off for an order of `units` items.

    Business rule: an order of 10 or more units earns the 10% bulk tier,
    50+ earns 12%, 100+ earns 20%. Reported bug: an order of exactly 10
    units is charged the wrong tier.
    """
    for threshold, rate in TIER_RATES:
        if units > threshold:
            return rate
    return 0.0


def discounted_price(price, units):
    """Final unit price after the bulk discount."""
    return price * (1 - bulk_discount_rate(units) / 100)
'''

AUDIT_LOG = '''"""Append-only event log helpers for the pipeline runner."""
def append_event(event, event_log=[]):
    """Record one event in the run's event log."""
    event_log.append(event)
    return event_log


def count_events(event_log=[]):
    """Number of events recorded for the run."""
    return len(event_log)
'''

SIMULATE = '''"""Run one import batch and report how many events were recorded."""
import audit_log


def process(batch):
    events = []
    total = 0
    for item in batch:
        audit_log.append_event({"item": item, "stage": "import"})
        total = audit_log.count_events()
    return total, len(events)


if __name__ == "__main__":
    total, local = process(["invoice-1", "invoice-2", "invoice-3"])
    print(f"count_events() -> {total} (expected 3)")
    print(f"local list size -> {local} (expected 3)")
'''

USER_FIELD_STUB = '''"""User profile access (stub). Proliferated per-field accessors."""
def get_user_name(user_id):
    raise NotImplementedError

def set_user_name(user_id, value):
    raise NotImplementedError

def get_user_email(user_id):
    raise NotImplementedError

def set_user_email(user_id, value):
    raise NotImplementedError

def get_user_locale(user_id):
    raise NotImplementedError

def set_user_locale(user_id, value):
    raise NotImplementedError

def get_user_timezone(user_id):
    raise NotImplementedError

def set_user_timezone(user_id, value):
    raise NotImplementedError

def get_user_preference(user_id, key):
    raise NotImplementedError

def set_user_preference(user_id, key, value):
    raise NotImplementedError

def clear_user_preference(user_id, key):
    raise NotImplementedError
'''

ORDER_SERVICE_CALLER = '''"""Callers of the user profile module (representative of 14 production call sites)."""
import user_field_stub as user


def render_order(order):
    name = user.get_user_name(order["user_id"])
    email = user.get_user_email(order["user_id"])
    locale = user.get_user_locale(order["user_id"])
    return {
        "display": f"{name} <{email}>",
        "locale_tag": locale,
    }


def notify_shipped(order):
    user.set_user_preference(order["user_id"], "last_shipped_at", order["shipped_at"])
    tz = user.get_user_timezone(order["user_id"])
    return {"recipient": order["user_id"], "tz": tz}
'''

FIXTURES = {
    'tdd': {'discount.py': DISCOUNT_MODULE},
    'diagnosing': {'audit_log.py': AUDIT_LOG, 'simulate.py': SIMULATE},
    'design': {'user_field_stub.py': USER_FIELD_STUB, 'order_service.py': ORDER_SERVICE_CALLER},
}

PROMPTS = {
    'tdd': ('mp-tdd', 'Use the skill to fix this bug test-first. Reported bug: bulk_discount_rate(10) returns the wrong tier — the business rule is that an order of 10 or more units earns the 10% bulk discount. This is a bug regression: write a focused test first for the intended behavior, show it failing for the intended reason, then fix and show the test passing. One slice only: no speculative extra tests or features. Keep the test at the module\'s public seam.'),
    'diagnosing': ('mp-diagnosing-bugs', 'Use the skill to diagnose why the script fails. Running `python3 simulate.py` prints "count_events() -> 0 (expected 3)" even though three events were processed. Reproduce and record the exact failure before proposing causes, state explicit hypotheses, eliminate them with real evidence (read the actual code, run the trigger), and only fix after the cause is reproduced. If you cannot establish the cause, say plainly what you tried and what remains unknown — no confidence theater.'),
    'design': ('mp-codebase-design', 'Use the skill to redesign this module interface. user_field_stub.py is an interface-heavy stub with proliferated per-field accessors; order_service.py shows real callers. Compare at least two structurally distinct candidate designs against an explicit rubric, then name the concrete interface signature you would commit and quantify the callers\' burden under your choice. Design work only: do not implement the redesign or rewrite the fixture sources.'),
}

# Bounds appended to each request, mirroring the reference harness's compact-fixture line.
BOUNDS = ('For this small bounded fixture, keep discovery light, produce the deliverable inline'
          ' (or as one small file in the fixture directory), reserve time for the finish step and'
          ' finish within the run budget.')

PREFACE = ('This is a bounded verification fixture for a generated, not yet installed skill.'
           ' The exact selected SKILL.md is embedded below. Its supporting paths resolve beneath'
           ' {source}. Use actual native file/shell operations on those references, not same-named'
           ' skills from the live profile. Do not install, configure, publish, activate automation'
           ' or modify this skill distribution. Report exact tool evidence.')


def build_distribution(out_dir):
    cmd = [sys.executable, str(ROOT / 'tools/specialize.py'), 'build',
           '--runtime', 'hermes', '--output', str(out_dir)]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit('Distribution build failed:\n' + result.stdout + result.stderr)
    return out_dir


def fingerprint(folder):
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.py')}
    if (folder / 'GLOSSARY.md').exists():
        files['GLOSSARY.md'] = hashlib.sha256((folder / 'GLOSSARY.md').read_bytes()).hexdigest()
    return files


def run_case(case, parent, args, dist):
    folder = parent / case
    folder.mkdir()
    for name, text in FIXTURES[case].items():
        (folder / name).write_text(text)
    skill_name, request = PROMPTS[case]
    source = dist / 'skills' / skill_name
    text = (source / 'SKILL.md').read_text()
    query = folder / 'query.txt'
    preface = PREFACE.format(source=source) + '\n'
    preface += ('This run deliberately exposes file/terminal capabilities only. No delegation is'
                ' available or authorized: do the work in this session and do not spawn another'
                ' process or simulate an absent API.\n')
    query.write_text(preface + '\nREQUEST\n' + request + ' ' + BOUNDS
                     + '\n\nSELECTED GENERATED SKILL\n' + text)
    before = fingerprint(folder)
    command = ['hermes', 'chat', '--provider', args.provider, '--model', args.model,
               '--query-file', str(query), '--oneshot', '--format', 'stream-json',
               '--ignore-rules', '--ignore-user-config', '--toolsets', 'file,terminal',
               '--max-turns', '24', '--run-budget', str(args.budget), '--in', str(folder),
               '--source', 'tool']
    start = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True, cwd=str(folder))
    timeout = False
    try:
        stdout, stderr = process.communicate(timeout=args.budget + 60)
    except subprocess.TimeoutExpired:
        timeout = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    reports = ROOT / 'reports/probes-mp'
    reports.mkdir(parents=True, exist_ok=True)
    stem = case + '-' + args.attempt
    (reports / (stem + '.jsonl')).write_text(stdout)
    (reports / (stem + '.stderr.txt')).write_text(stderr)
    result = {'case': case, 'skill': skill_name, 'attempt': args.attempt,
              'returncode': process.returncode, 'timeout': timeout,
              'seconds': round(time.monotonic() - start, 2), 'fixture': str(folder),
              'fixture_left': str(folder), 'skill_sha256': hashlib.sha256(text.encode()).hexdigest(),
              'before': before, 'after': fingerprint(folder),
              'code_unchanged': before == fingerprint(folder),
              'stdout_path': str(reports / (stem + '.jsonl')),
              'stderr_path': str(reports / (stem + '.stderr.txt')), 'command': command}
    # Independent post-run checks of final fixture state (agent may have run them itself too).
    if case == 'tdd':
        checked = subprocess.run(['python3', '-B', '-m', 'unittest', 'discover', '-v'],
                                 cwd=folder, capture_output=True, text=True, timeout=60)
        result['independent_tests'] = {'returncode': checked.returncode,
                                       'stdout': checked.stdout, 'stderr': checked.stderr}
    if case == 'diagnosing':
        checked = subprocess.run(['python3', '-B', 'simulate.py'],
                                 cwd=folder, capture_output=True, text=True, timeout=60)
        result['repro_after_run'] = {'returncode': checked.returncode,
                                     'stdout': checked.stdout, 'stderr': checked.stderr}
    (reports / (stem + '.result.json')).write_text(json.dumps(result, indent=2) + '\n')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', default='openai-codex')
    p.add_argument('--model', default='gpt-6.1-sol')
    p.add_argument('--budget', type=int, default=1200)
    p.add_argument('--attempt', required=True, help='Distinct label; old evidence must not be overwritten')
    p.add_argument('--cases', nargs='+', choices=tuple(FIXTURES), default=list(FIXTURES))
    p.add_argument('--workers', type=int, default=1)
    p.add_argument('--distribution', type=Path, default=None,
                   help='Reuse a prebuilt distribution instead of building one')
    args = p.parse_args(argv)
    if not args.attempt.replace('-', '').replace('_', '').isalnum():
        p.error('Use a plain attempt label')
    if args.distribution is not None:
        dist = args.distribution.resolve()
    else:
        parent = Path(tempfile.mkdtemp(prefix='mp-dist-'))
        dist = parent / 'distribution'
        build_distribution(dist)
    root = Path(tempfile.mkdtemp(prefix='mp-probe-'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda case: run_case(case, root, args, dist), args.cases))
    print(json.dumps(results, indent=2))
    if any(row['returncode'] or row['timeout'] for row in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
