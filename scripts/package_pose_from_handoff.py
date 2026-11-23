"""Offline pose ZIP authoring from an extracted *context-only* remote handoff.

Does NOT require Blender, a pair template, SQLite or the large full catalog.
The receiving runnable remote library still validates all hashes on import.

Usage:
  python scripts/package_pose_from_handoff.py DOGG-DOGG-V00 draft-folder/ --output ../outgoing/
"""
from __future__ import annotations
import argparse,datetime,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,sha_bytes,read_json,load_package,ALLOWED


def make(pose_id,folder,output,timestamp=None):
    deps_path=ROOT/'source/pose-dependencies.json'
    if not deps_path.is_file():raise RuntimeError('Requires extracted context-only handoff with source/pose-dependencies.json')
    depfile=read_json(deps_path)
    dep=depfile['dependencies_by_pose_id'].get(pose_id)
    if not dep:raise ValueError('V00 ID not available in handoff dependency map')
    folder=Path(folder)
    members={f.name:f.read_bytes() for f in folder.iterdir() if f.is_file()}
    required={'pose.json','rig-targets.json','contacts.json'}
    if not required.issubset(members) or 'manifest.json' in members or set(members)-ALLOWED:
        raise ValueError('Expected exactly allowed JSON input files excluding manifest.json')
    for name,payload in members.items():
        if not name.endswith('.json'):raise ValueError('Only JSON payloads allowed')
        json.loads(payload)
    if json.loads(members['pose.json']).get('pose_id')!=pose_id:
        raise ValueError('pose.json pose_id differs from requested pose')
    ts=timestamp or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    dest=output/f'{pose_id}_{ts}.zip'
    if dest.exists():raise FileExistsError(dest)
    manifest={'schema_version':1,'package_type':'spose_pose_module','pose_id':pose_id,
              'package_timestamp_utc':ts,'dependencies':dep,
              'payload_sha256':{name:sha_bytes(content) for name,content in sorted(members.items())}}
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for name,data in sorted(members.items()):z.writestr(name,data)
    load_package(dest,validate_dependencies=False)
    return dest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pose_id');p.add_argument('folder',type=Path)
    p.add_argument('--output',type=Path,default=ROOT.parent/'pose-packages')
    p.add_argument('--timestamp',help='UTC YYYYMMDDTHHMMSSZ override')
    a=p.parse_args()
    print(make(a.pose_id,a.folder,a.output,a.timestamp))

if __name__=='__main__':main()
