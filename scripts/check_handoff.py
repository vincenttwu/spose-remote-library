"""Verify an extracted context-only SPOSE remote handoff (no Blender assets needed).

Usage: python scripts/check_handoff.py
This does not attest the packager/creator's identity and is not a runnable library test.
"""
from __future__ import annotations
import csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,sha_bytes,read_json


def check(root=ROOT):
    root=Path(root)
    manifest_path=root/'handoff/HANDOFF-MANIFEST.json'
    if not manifest_path.is_file():raise FileNotFoundError('Missing handoff manifest: not a context-only handoff')
    m=read_json(manifest_path)
    if m.get('kind')!='spose_remote_context_handoff' or m.get('context_only') is not True or m.get('standalone_runnable_library') is not False:
        raise ValueError('Unexpected handoff manifest flags')
    for rel,expected in m['files_sha256'].items():
        p=(root/rel).resolve()
        if not p.is_relative_to(root.resolve()):raise ValueError('Escaping member path')
        if not p.is_file() or sha_bytes(p.read_bytes())!=expected:
            raise ValueError('Missing/corrupted handoff member: '+rel)
    for forbidden in list(root.rglob('*.blend'))+list(root.rglob('*.sqlite')):
        raise ValueError('Context handoff unexpectedly contains heavy runnable asset: '+str(forbidden))
    with (root/'source/V00-CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
        v00=list(csv.DictReader(f))
    with (root/'source/POSE-INDEX.csv').open(encoding='utf-8-sig',newline='') as f:
        all_ids=list(csv.DictReader(f))
    deps=read_json(root/'source/pose-dependencies.json')
    if len(v00)!=m['source']['v00_total'] or len(all_ids)!=m['source']['record_total']:
        raise ValueError('Source handoff counts incorrect')
    for r in v00:
        key=r['pose_id']
        if key not in deps['dependencies_by_pose_id']:raise ValueError('Missing pose dependency: '+key)
        sh=sha_bytes(r['specification'].encode('utf-8'))
        if deps['dependencies_by_pose_id'][key]['source_row_sha256']!=sh:
            raise ValueError('Pose row hash mismatch: '+key)
    roadmap=read_json(root/'ROADMAP.json')
    if roadmap['summary']['base_total']!=len(v00):raise ValueError('Roadmap count mismatch')
    return {'ok':True,'context_only':True,'files_verified':len(m['files_sha256']),
            'v00_rows':len(v00),'all_pose_ids':len(all_ids),'v00_accepted':roadmap['summary']['v00_accepted']}

if __name__=='__main__':
    try:print(json.dumps(check(),indent=2))
    except Exception as e:
        print('HANDOFF CHECK FAILED: '+str(e),file=sys.stderr);sys.exit(1)
