"""Regenerate ROADMAP.md and ROADMAP.json from the pinned catalog and SQLite tracker.

Tracker = authority for pose execution/acceptance, catalog = authority for planned IDs.
Roadmap files are derived read-only views; never edit them to change a pose status.

Usage:
  python scripts/update_roadmap.py
  python scripts/update_roadmap.py --check
"""
from __future__ import annotations
import argparse,csv,hashlib,json,sqlite3,sys
from collections import defaultdict,Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json,sha_file

JOB_STATES={'queued','working','draft','validated','accepted','blocked','failed','excluded'}


def build_roadmap(root=ROOT):
    root=Path(root)
    project=read_json(root/'project.json')
    source_path=root/project['source_config']
    source=read_json(source_path)
    csv_path=(source_path.parent/source['root']/source['canonical_catalog']).resolve()
    if not csv_path.is_relative_to(root.resolve()):
        raise ValueError('Catalog escaped remote root')
    if sha_file(csv_path)!=source['catalog_sha256']:
        raise ValueError('Catalog SHA mismatch — refuse roadmap regeneration')
    with csv_path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames
        rows=list(reader)
    if not cols or len(cols)!=source['columns'] or len(rows)!=source['records']:
        raise ValueError('Catalog row/column count does not match source registration')
    ids=[r['pose_id'] for r in rows]
    if len(set(ids))!=len(ids): raise ValueError('Duplicate pose ID in catalog')
    v00=[r for r in rows if r['variation_code']=='V00']
    if len(v00)!=source['bases']:
        raise ValueError('V00 count does not match pinned source')
    family_ids=[]
    for r in v00:
        if r['family_id'] not in family_ids:family_ids.append(r['family_id'])
    if len(family_ids)!=source['families']:
        raise ValueError('Family count does not match pinned source')
    with sqlite3.connect(root/project['tracker']) as db:
        db.row_factory=sqlite3.Row
        jobs=[dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY pose_id,revision')]
    by_id=defaultdict(list)
    for job in jobs:
        if job['status'] not in JOB_STATES:raise ValueError('Unexpected tracker job status')
        by_id[job['pose_id']].append(job)
    output_bases=[]
    counts=Counter()
    family_bases=defaultdict(list)
    for row in v00:
        pid=row['pose_id']
        expected_sha=hashlib.sha256(row['specification'].encode('utf-8')).hexdigest()
        relevant=[j for j in by_id.get(pid,[]) if j.get('source_checkpoint')==source['checkpoint'] and j.get('source_row_sha256')==expected_sha]
        accepted=[j for j in relevant if j['status']=='accepted']
        latest=by_id[pid][-1] if by_id[pid] else None
        if accepted:
            state='accepted'
            accepted_revision=max(j['revision'] for j in accepted)
        elif latest is None:
            state='not_started'; accepted_revision=None
        elif not relevant:
            state='stale_source'; accepted_revision=None
        else:
            state='in_progress' if latest['status'] in ('queued','working') else latest['status']
            accepted_revision=None
        record={
            'pose_id':pid,
            'family_id':row['family_id'],
            'pose_code':row['pose_code'],
            'pose_name':row.get('pose_name',''),
            'source_gate':row.get('generation_gate',''),
            'complexity_family':row.get('complexity_family',''),
            'complexity_pose':row.get('complexity_pose',''),
            'state':state,
            'attempt_count':len(by_id.get(pid,[])),
            'latest_revision':latest['revision'] if latest else None,
            'latest_status':latest['status'] if latest else None,
            'latest_updated_at':latest['updated_at'] if latest else None,
            'accepted_revision':accepted_revision,
            'source_row_sha256':expected_sha,
        }
        counts[state]+=1
        output_bases.append(record)
        family_bases[row['family_id']].append(record)
    families=[]
    for fid in family_ids:
        poses=family_bases[fid]; total=len(poses)
        accepted=sum(p['state']=='accepted' for p in poses)
        attempted=sum(p['attempt_count']>0 for p in poses)
        family_state='v00_complete' if accepted==total else ('in_progress' if attempted else 'not_started')
        families.append({
            'family_id':fid,'v00_total':total,'v00_accepted':accepted,
            'v00_attempted':attempted,'v00_remaining':total-accepted,
            'v00_state':family_state,'variations_state':'DEFERRED_GLOBAL_V00_FIRST',
            'bases':[p['pose_id'] for p in poses],
        })
    accepted=sum(f['v00_accepted'] for f in families)
    roadmap={
        'schema_version':1,
        'kind':'derived_roadmap_snapshot',
        'authority':{'catalog':source['canonical_catalog'],'catalog_sha256':source['catalog_sha256'],
                     'source_id':source['source_id'],'source_revision':source['source_revision'],
                     'source_checkpoint':source['checkpoint'],'tracker':project['tracker']},
        'policy':{'current_phase':'ALL_FAMILIES_V00_FIRST',
                  'v00_completion_requires':'accepted revision matching active source row hash and checkpoint',
                  'variation_phase_eligible':accepted==len(v00),
                  'variation_phase_enabled':accepted==len(v00) and project.get('variation_phase_authorized',False) is True,
                  'variation_phase_rule':'DO NOT begin V01-V10 until all V00 bases across all families are accepted and separately authorized',
                  'source_generation_gate_is_not_job_status':True,
                  'acceptance_is_not_automatic':True},
        'summary':{'family_total':len(families),'base_total':len(v00),
                   'v00_accepted':accepted,'v00_remaining':len(v00)-accepted,
                   'v00_attempted':sum(p['attempt_count']>0 for p in output_bases),
                   'base_state_counts':dict(sorted(counts.items())),
                   'catalog_record_total':len(rows),'later_variation_record_total':len(rows)-len(v00)},
        'families':families,'v00_poses':output_bases,
    }
    return roadmap


def render_markdown(d):
    summary=d['summary']; policy=d['policy']; auth=d['authority'];
    lines=[
        '# SPOSE Remote — V00-first ROADMAP',
        '',
        '**Auto-generated view, do not manually edit.** Run `python scripts/update_roadmap.py` after pose-tracker changes.',
        '',
        f"**Active source:** `{auth['source_id']}/{auth['source_revision']}` · catalog checkpoint `{auth['source_checkpoint']}` · {summary['family_total']} families · {summary['catalog_record_total']} records.",
        f"**Priority milestone:** complete **all {summary['base_total']} V00 bases across all families**, then explicitly decide whether to unlock V01–V10 ({summary['later_variation_record_total']} records).",
        '',
        f"**V00 accepted:** **{summary['v00_accepted']} / {summary['base_total']}** · attempted {summary['v00_attempted']} · remaining {summary['v00_remaining']}.",
        f"**Variation work:** {'READY_FOR_EXPLICIT_APPROVAL' if policy['variation_phase_eligible'] else 'LOCKED / DEFERRED — no V01–V10 production yet'}.",
        '',
        '## Family-level roadmap',
        '',
        '| Done | Family | V00 accepted | Attempted | Remaining | State | Variations |',
        '|:---:|---|---:|---:|---:|---|---|',
    ]
    for f in d['families']:
        lines.append(f"| {'[x]' if f['v00_state']=='v00_complete' else '[ ]'} | `{f['family_id']}` | {f['v00_accepted']}/{f['v00_total']} | {f['v00_attempted']} | {f['v00_remaining']} | `{f['v00_state']}` | Deferred |")
    lines += [
        '', '## Per-base checklist (V00 only)', '',
        'A checkbox is checked **only** when a matching-source revision is explicitly `accepted` in SQLite. `draft` or successful render is not completion.',
        ''
    ]
    by_family=defaultdict(list)
    for p in d['v00_poses']:by_family[p['family_id']].append(p)
    for f in d['families']:
        lines.append(f"### {f['family_id']} — {f['v00_accepted']}/{f['v00_total']} accepted")
        lines.append('')
        for p in by_family[f['family_id']]:
            detail=p['state']
            if p['latest_revision'] is not None: detail+=f" · latest r{p['latest_revision']:03d} ({p['latest_status']})"
            title=p.get('pose_name','').replace('\n',' ').replace('|','/')
            lines.append(f"- [{'x' if p['state']=='accepted' else ' '}] `{p['pose_id']}` — {title} · `{detail}` · complexity {p['complexity_pose']}/5 · gate `{p['source_gate']}`")
        lines.append('')
    lines += [
        '## Stage gates and authority', '',
        '1. **Planned** — source V00 row exists; no remote job means `not_started`.',
        '2. **Working/draft/validated** — a modular package was imported or checked; no automatic acceptance.',
        '3. **Accepted** — explicit user approval recorded in `tracking/progress.sqlite` for the active source row hash. A later unsuccessful draft does not invalidate an earlier accepted revision.',
        '4. **Family V00 complete** — all V00 bases in that family accepted.',
        '5. **Global V00 complete** — all base records accepted. Variations still require an explicit user decision and importer-scope revision.',
        '6. **Source EXCLUDE/REVIEW** — reference metadata only, separate from Blender job status and acceptance.',
        '', 'The *tracking SQLite database* is the authority for job states. `ROADMAP.json`, `ROADMAP.md`, `tracking/progress.csv`, and feedback exports are derived snapshots.',
        'Run `python scripts/update_roadmap.py --check` before making a handoff ZIP to detect stale snapshots.',
        ''
    ]
    return '\n'.join(lines)


def save_roadmap(root=ROOT,check=False):
    root=Path(root);d=build_roadmap(root)
    target_json=root/'ROADMAP.json';target_md=root/'ROADMAP.md'
    expected_json=json.dumps(d,ensure_ascii=False,indent=2)+'\n'
    expected_md=render_markdown(d)
    if check:
        if not target_json.is_file() or not target_md.is_file():raise ValueError('Roadmap files missing')
        if target_json.read_text(encoding='utf-8')!=expected_json or target_md.read_text(encoding='utf-8')!=expected_md:
            raise ValueError('Roadmap snapshots are stale: run scripts/update_roadmap.py')
    else:
        target_json.write_text(expected_json,encoding='utf-8')
        target_md.write_text(expected_md,encoding='utf-8')
    return d

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Fail if derived roadmap differs from tracked state')
    a=parser.parse_args()
    try:
        d=save_roadmap(check=a.check)
        print(json.dumps({'ok':True,'action':'checked' if a.check else 'regenerated',**d['summary']},indent=2))
    except Exception as e:
        print(f'ROADMAP ERROR: {e}',file=sys.stderr);sys.exit(1)
