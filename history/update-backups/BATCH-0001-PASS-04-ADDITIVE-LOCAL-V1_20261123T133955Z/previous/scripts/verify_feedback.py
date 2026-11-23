"""Verify new SPOSE single combined feedback ZIP: hashes, members and coverage.

Missing preview images, failed runs, or missing context are warnings and are
reported without preventing the next batch. Corrupt archive/member hashes are
integrity failures. No approvals or geometry decisions are made here.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import PurePosixPath,Path


def sha(data):return hashlib.sha256(data).hexdigest()


def verify(path:Path):
    errors=[];warnings=[]
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        for x in names:
            pp=PurePosixPath(x)
            if x.startswith('/') or '\\' in x or '..' in pp.parts or len(names)!=len(set(names)):
                errors.append('Unsafe/duplicate member: '+x)
        if z.testzip() is not None:errors.append('ZIP CRC failure')
        manifest=json.loads(z.read('manifest.json'))
        if manifest.get('kind')!='spose-remote-combined-feedback' or manifest.get('schema_version')!=2:
            errors.append('Unsupported feedback schema')
        for rel, digest in manifest.get('files_sha256',{}).items():
            if rel not in names or sha(z.read(rel))!=digest:
                errors.append('Missing or corrupt member: '+rel)
        results=json.loads(z.read('batch-summary.json')).get('results',[])
        if len(results)!=manifest.get('pose_count'):
            errors.append('Pose result count mismatch')
        if len(results)!=5:
            warnings.append(f'Expected five poses by normal policy; found {len(results)}')
        if not manifest.get('context_included'):
            warnings.append('Portable context absent; cold-start may need separate handoff')
        if manifest.get('context_included'):
            for required in ('context/AGENTS.md','context/SKILL.md','context/handoff/HANDOFF-MANIFEST.json','context/source/V00-CATALOG.csv'):
                if required not in names:errors.append('Required portable context member missing: '+required)
        if manifest.get('context_included') and 'context/handoff/HANDOFF-MANIFEST.json' in names:
            inner=json.loads(z.read('context/handoff/HANDOFF-MANIFEST.json'))
            for rel,d in inner.get('files_sha256',{}).items():
                target='context/'+rel
                if target not in names or sha(z.read(target))!=d:
                    errors.append('Embedded portable handoff checksum mismatch: '+target)
        for pose in manifest.get('pose_results',[]):
            miss=pose.get('missing_views',[])
            if miss:warnings.append(pose['pose_id']+' missing views: '+', '.join(miss))
        for p in results:
            if p.get('revision') is None:warnings.append(p['pose_id']+' has no built revision')
        warnings.extend(manifest.get('warnings',[]))
        count=sum(len(x.get('images',[])) for x in manifest.get('pose_results',[]))
        if count!=manifest.get('image_count'):errors.append('Image count mismatch')
    return {'ok':not errors,'path':str(path),'file_bytes':Path(path).stat().st_size,
            'pose_count':len(results),'image_count':count,'context_included':manifest.get('context_included'),
            'batch_label':manifest.get('batch_label'),'pass_label':manifest.get('pass_label'),
            'errors':errors,'warnings':warnings}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip',type=Path)
    a=p.parse_args()
    report=verify(a.zip)
    print(json.dumps(report,indent=2))
    if not report['ok']:raise SystemExit(2)

if __name__=='__main__':main()
