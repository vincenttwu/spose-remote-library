"""Package a portable, *context-only* SPOSE remote handoff for a fresh session.

The output ZIP has NO top-level remote/ wrapper. It intentionally excludes
Blender binaries, meshes, previews, full source CSV, historical .blend files,
SQLite database, secrets, and all pose-scene output. It does NOT replace the
runnable remote library.

Usage (from the library root):
  python scripts/package-library-for-remote.py
  python scripts/package-library-for-remote.py --output ../handoffs/
  python scripts/package-library-for-remote.py --dry-run
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,io,json,os,sys,zipfile,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json,sha_file,sha_bytes
from update_roadmap import save_roadmap

TEXT_EXT={'.md','.json','.py','.csv','.txt','.jsonl'}
MAX_TEXT_BYTES=2_500_000


def utc_stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def csv_bytes(rows,fieldnames):
    s=io.StringIO(newline='')
    w=csv.DictWriter(s,fieldnames=fieldnames,lineterminator='\n',extrasaction='ignore')
    w.writeheader();w.writerows(rows)
    return s.getvalue().encode('utf-8')


def build_payload(root=ROOT,include_latest_metadata=True):
    root=Path(root)
    p=read_json(root/'project.json')
    src_cfg=root/p['source_config']; src=read_json(src_cfg)
    source=(src_cfg.parent/src['root']/src['canonical_catalog']).resolve()
    if not source.is_relative_to(root.resolve()):raise ValueError('Source outside library root')
    if sha_file(source)!=src['catalog_sha256']:raise ValueError('Source hash mismatch')
    with source.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f); all_fields=list(r.fieldnames or []); rows=list(r)
    if len(rows)!=src['records'] or len(all_fields)!=src['columns']:
        raise ValueError('Source registration mismatch')
    v00=[row for row in rows if row['variation_code']=='V00']
    if len(v00)!=src['bases']:raise ValueError('V00 count mismatch')
    if len(set(r['pose_id'] for r in rows))!=len(rows):raise ValueError('Non-unique pose ID')
    roadmap=save_roadmap(root,check=True)
    if roadmap['summary']['base_total']!=len(v00):raise ValueError('Roadmap count mismatch')
    pair_config=root/p['default_pair']['config']
    pair=read_json(pair_config)
    template=root/'pairs'/pair['pair_id']/pair['version']/'template.blend'
    template_sha=sha_file(template)
    if pair.get('template_sha256') and pair['template_sha256']!=template_sha:
        raise ValueError('Pair template hash mismatch')
    rig=root/'tooling/rig-maps/RIG001-v001.json'
    rig_content=read_json(rig)

    # Explicit allow-list. Never walk the source ZIP wholesale.
    named=[
        'AGENTS.md','CONTINUATION.md','SKILL.md','WORKFLOW.md','README.md','GUIDE.md',
        'CHANGELOG.md','ROADMAP.md','ROADMAP.json','project.json','CURRENT-INSTALL.json',
        'source/dataset.json','source/dataset-SRC002-historical.json','source/dataset-original.json',
        'source/reference-map.json','tracking/milestones.json','tracking/progress.csv',
        'tracking/handoff.md','tracking/character-preparation-integrity.json',
        'pairs/CPL01/v001/pair.json','pairs/CPL01/v001/validation.json',
        'body_profiles/BP001/v001/profile.json','body_profiles/BP001/v001/validation.json',
        'visual_profiles/VP001/v001/visual.json',
        'pairs/CPL01/v001/studies/VP001-v001/study.json',
        'pairs/CPL01/v001/studies/VP001-v001/appearance-validation.json',
        'tooling/rig-maps/RIG001-v001.json',
        'tooling/rig-maps/RIG001-inspection-v001.json',
        'tooling/rig-maps/RIG001-source-materials-v001.json',
    ]
    files={}
    for rel in named:
        f=root/rel
        if f.is_file():
            if f.is_symlink() or f.suffix not in TEXT_EXT:raise ValueError('Disallowed handoff payload: '+rel)
            if f.stat().st_size>MAX_TEXT_BYTES:raise ValueError('Unexpectedly large metadata file: '+rel)
            files[rel]=f.read_bytes()
    for dirname in ('docs','schemas','scripts'):
        directory=root/dirname
        if directory.exists():
            for f in sorted(directory.rglob('*')):
                if not f.is_file():continue
                rel=f.relative_to(root).as_posix()
                if f.is_symlink():raise ValueError('Symlink not allowed in context pack: '+rel)
                if f.suffix in TEXT_EXT and f.stat().st_size<=MAX_TEXT_BYTES:
                    files[rel]=f.read_bytes()
                elif f.suffix not in ('.pyc',):
                    raise ValueError('Unexpected large/nontext doc or script: '+rel)
    for f in sorted((root/'tooling/scripts').glob('*.py')):
        files[f.relative_to(root).as_posix()]=f.read_bytes()

    # Complete row-level source for all V00 bases is kept; other variations remain
    # represented by IDs and immutable row hashes to keep handoff compact.
    files['source/V00-CATALOG.csv']=csv_bytes(v00,all_fields)
    index_fields=['pose_id','family_id','pose_code','variation_code','parent_pose_id','pose_name','complexity_family','complexity_pose','generation_gate','source_row_sha256']
    index=[]
    for row in rows:
        idx={k:row.get(k,'') for k in index_fields}
        idx['source_row_sha256']=sha_bytes(row['specification'].encode('utf-8'))
        index.append(idx)
    files['source/POSE-INDEX.csv']=csv_bytes(index,index_fields)

    dep_common={
        'source_id':src['source_id'],'source_checkpoint':src['checkpoint'],
        'pair_id':pair['pair_id'],'pair_version':pair['version'],
        'template_sha256':template_sha,'rig_map_id':rig_content.get('rig_map_id','RIG001'),
        'rig_map_version':rig_content.get('version','v001')
    }
    deps={r['pose_id']:{**dep_common,'source_row_sha256':sha_bytes(r['specification'].encode('utf-8'))} for r in v00}
    files['source/pose-dependencies.json']=(json.dumps({
        'schema_version':1,'purpose':'OFFLINE_V00_PACKAGE_AUTHORING_ONLY',
        'full_catalog_sha256':src['catalog_sha256'],
        'record_total':len(rows),'v00_total':len(v00),
        'dependencies_by_pose_id':deps,
    },indent=2,ensure_ascii=False)+'\n').encode('utf-8')

    # Latest tracker events, without shipping the authoritative SQLite file.
    with sqlite3.connect(root/p['tracker']) as db:
        db.row_factory=sqlite3.Row
        recent=[dict(r) for r in db.execute(
            'SELECT * FROM events ORDER BY event_id DESC LIMIT 200')]
    recent.reverse()
    files['tracking/recent-events.jsonl']=(''.join(json.dumps(ev,ensure_ascii=False)+'\n' for ev in recent)).encode('utf-8')

    # Dynamic summary prevents the baseline continuation text from being misread
    # as current state after the owner's local library has made progress.
    active=[r for r in roadmap['v00_poses'] if r['attempt_count']>0]
    textlines=[
        '# Snapshot status generated from the live remote tracker',
        '',
        f"**V00 accepted:** {roadmap['summary']['v00_accepted']}/{roadmap['summary']['base_total']}",
        f"**V00 attempted:** {roadmap['summary']['v00_attempted']}",
        f"**Remaining:** {roadmap['summary']['v00_remaining']}",
        f"**Recent events in this handoff:** {len(recent)} (last 200 maximum)",
        '',
        'The source/SQLite join and ROADMAP.json are authoritative for this snapshot; this page is only a quick synopsis.',
        'Variations are deferred until all V00 are accepted and the user explicitly authorizes the phase.',
        '',
        '## Bases with recorded attempts',
        '',
    ]
    if active:
        for q in active:
            textlines.append(f"- `{q['pose_id']}`: `{q['state']}` — latest r{q['latest_revision']:03d} ({q['latest_status']}); accepted r{q['accepted_revision']:03d}" if q['accepted_revision'] else
                             f"- `{q['pose_id']}`: `{q['state']}` — latest r{q['latest_revision']:03d} ({q['latest_status']})")
    else:
        textlines.append('- None yet in the remote branch')
    files['handoff/SNAPSHOT-STATUS.md']=('\n'.join(textlines)+'\n').encode('utf-8')

    # Include small, useful per-pose input/state metadata for latest revisions;
    # explicitly no renders, full scenes, binaries or potentially huge logs.
    pose_count=0
    if include_latest_metadata:
        for pose_folder in sorted((root/'poses').glob('*/CPL01/v001')):
            revisions=sorted([f for f in pose_folder.glob('r[0-9][0-9][0-9]') if f.is_dir()])
            if not revisions:continue
            revision=revisions[-1]
            for relname in ('pose.json','validation.json','checksums.json','blender-result.json',
                            'inputs/manifest.json','inputs/pose.json','inputs/rig-targets.json',
                            'inputs/contacts.json','inputs/validation-plan.json','inputs/render-config.json'):
                f=revision/relname
                if f.is_file() and not f.is_symlink() and f.stat().st_size<=MAX_TEXT_BYTES:
                    files[f.relative_to(root).as_posix()]=f.read_bytes()
            pose_count+=1

    details={
        'archive_root':'flat',
        'context_only':True,'standalone_runnable_library':False,
        'source':{'source_id':src['source_id'],'revision':src['source_revision'],
                  'checkpoint':src['checkpoint'],'catalog_sha256':src['catalog_sha256'],
                  'record_total':len(rows),'family_total':src['families'],
                  'v00_total':len(v00),'columns':len(all_fields)},
        'pair':{'pair_id':pair['pair_id'],'version':pair['version'],
                'template_sha256':template_sha},
        'rig':{'id':rig_content.get('rig_map_id','RIG001'),'version':rig_content.get('version','v001'),
               'rig_map_sha256':sha_file(rig)},
        'roadmap':roadmap['summary'],
        'phase':'ALL_FAMILIES_V00_FIRST',
        'latest_pose_metadata_count':pose_count,
        'recent_events_included':len(recent),
    }
    # Handoff-only documents make sense even when there are no pose revisions.
    session_start=f'''# SPOSE — start here (PORTABLE CONTEXT ONLY)\n\n**This ZIP is NOT a runnable Blender library.** It omits `.blend`, images, the full source CSV, SQLite, and all large assets. Never extract it over your active full library directory.

**Snapshot state:** {roadmap['summary']['v00_accepted']} / {roadmap['summary']['base_total']} V00 accepted; {roadmap['summary']['v00_attempted']} attempted; {len(recent)} recent tracker events included. Source {src['source_id']} / {src['source_revision']} at {src['checkpoint']}. Variations remain deferred until global V00 acceptance and separate user authorization.\n\n## What to read (in order)\n\n1. `CONTINUATION.md` — exact checkpoint, scope, blockers and next work.\n2. `ROADMAP.md` (or `ROADMAP.json`) — live V00-first status.\n3. `AGENTS.md`, `SKILL.md`, `WORKFLOW.md` — safety/authority rules and operating procedure.\n4. `docs/COLD-START.md`, `docs/HANDOFF-DESIGN.md`, `docs/POSE-MODULE-AND-FEEDBACK.md`.\n5. `source/V00-CATALOG.csv`, `source/POSE-INDEX.csv`, `source/pose-dependencies.json`; rig map and pair metadata.\n\n## From this handoff alone\n\nA future assistant can inspect full V00 specifications and rig-map names, plan one candidate module, generate a data-only pose ZIP with `python scripts/package_pose_from_handoff.py POSE_ID draft-folder --output .`, and explain exact local import commands. This is not a substitute for Blender, cannot reconstruct a scene, and cannot establish true 3D contact.\n\n## Who owns what\n\n- Your machine owns full standalone library: asset binaries, full source CSV, SQLite tracker, renders and approval history.\n- This context pack is a portable read-only snapshot; it is not authoritative for a newer local run.\n- If the local library changed since this handoff, regenerate this ZIP from the up-to-date library before making more packages.\n- Never mark a Blender pose as accepted just because the ZIP or offline checks pass.\n'''
    files['handoff/SESSION-START.md']=session_start.encode('utf-8')
    manifest={
        'schema_version':1,'kind':'spose_remote_context_handoff',
        **details,
        'archive_root':'flat','omissions':['*.blend','*.png','*.jpg','*.jpeg','*.webp','*.sqlite',
                    'full 3036-row catalog','full pose render previews','historical local pilot scenes',
                    'archive exports and pose ZIPs','credentials and user external paths'],
        'files_sha256':{k:sha_bytes(files[k]) for k in sorted(files)},
    }
    files['handoff/HANDOFF-MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    return files,details


def package(output=None,dry_run=False,root=ROOT):
    files,details=build_payload(root)
    if dry_run:
        return {'ok':True,'dry_run':True,'file_count':len(files),
                'uncompressed_bytes':sum(map(len,files.values())),**details}
    stamp=utc_stamp()
    name=f'spose-remote-handoff-{stamp}.zip'
    dest=Path(output) if output else Path(root).parent
    if dest.suffix.lower()=='.zip':
        dest.parent.mkdir(parents=True,exist_ok=True)
    else:
        dest.mkdir(parents=True,exist_ok=True)
        dest=dest/name
    if dest.exists():raise FileExistsError(dest)
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for rel,data in sorted(files.items()):
            z.writestr(rel,data)
    with zipfile.ZipFile(dest) as z:
        if z.testzip() is not None:raise ValueError('Archive integrity failed')
        names=z.namelist()
        if not names or any(n.startswith('remote/') or n.startswith('/') or '..' in Path(n).parts for n in names):
            raise ValueError('Invalid archive root')
        manifest=json.loads(z.read('handoff/HANDOFF-MANIFEST.json'))
        for rel,digest in manifest['files_sha256'].items():
            if sha_bytes(z.read(rel))!=digest:raise ValueError('Handoff checksum mismatch: '+rel)
    return {'ok':True,'path':str(dest),'bytes':dest.stat().st_size,'file_count':len(files),**details}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=None,help='ZIP filepath or output directory; defaults to parent of standalone library root')
    p.add_argument('--dry-run',action='store_true',help='Validate and show inclusion metrics without writing')
    a=p.parse_args()
    print(json.dumps(package(a.output,a.dry_run),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
