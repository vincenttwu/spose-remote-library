"""Audit cold-start documentation for broken local references and outdated paths.

Advisory by default; use --strict only as a documentation integrity test.
Does not attempt to judge geometry, editorial quality or pose acceptance.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NEEDED=['README.md','AGENTS.md','SKILL.md','WORKFLOW.md','GUIDE.md','CONTINUATION.md',
        'docs/ARCHITECTURE.md','docs/SCHEMAS.md','docs/MAINTENANCE.md','docs/COLD-START.md',
        'scripts/run_pose_batch.py','scripts/refresh_exchange.py','scripts/compress_images.py',
        'scripts/verify_feedback.py','scripts/update_continuation.py']
STALE=['review/current/','upload/current/','remote/scripts/','reports/batches/']


def check(root=ROOT):
    root=Path(root);issues=[];coverage={}
    for rel in NEEDED:
        if not (root/rel).is_file():issues.append('missing required file: '+rel)
        else:coverage[rel]=(root/rel).stat().st_size
    for rel in NEEDED:
        p=root/rel
        if not p.is_file() or p.suffix!='.md':continue
        doc=p.read_text(encoding='utf-8')
        for marker in STALE:
            if marker in doc:
                issues.append(f'{rel}: stale path reference {marker}')
        if len(doc)<600 and p.name not in ('CONTINUATION.md',):
            issues.append(f'{rel}: suspiciously underspecified ({len(doc)} characters)')
    return {'ok':not issues,'issues':issues,'checked_files':len(NEEDED),'coverage_bytes':coverage}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--strict',action='store_true')
    args=p.parse_args()
    report=check(args.root)
    print(json.dumps(report,indent=2))
    if args.strict and not report['ok']:raise SystemExit(2)

if __name__=='__main__':main()
