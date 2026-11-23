"""Activate a selected registered batch/pass in disposable flat review/ and upload/.

No pose build. No changes to authoritative revisions or registry quality.
Concurrency: exclusive exchange directory lock; other rendering jobs write to
snapshots/ and are NOT allowed to implicitly update these shared folders.
"""
from __future__ import annotations
import argparse, json, os, shutil, uuid
from pathlib import Path
from registry import ROOT,connect,normalize_batch,normalize_pass,read,write,safe_relative


def lookup(root,batch,pas,snapshot=None):
    root=Path(root).resolve();b=normalize_batch(batch);p=normalize_pass(pas)
    if snapshot is not None:
        rel=safe_relative(root,snapshot,'snapshots')
        snap=root/rel
        summary=read(snap/'batch-summary.json')
        if normalize_batch(summary['batch_label'])!=b or normalize_pass(summary['pass_label'])!=p:
            raise ValueError('Selected snapshot does not belong to requested batch/pass')
        return snap
    with connect(root) as c:
        row=c.execute('''SELECT snapshot_path FROM registry_runs WHERE batch_id=? AND pass_id=?
            ORDER BY run_utc DESC, imported_utc DESC, snapshot_path DESC LIMIT 1''',(b,p)).fetchone()
    if not row:raise FileNotFoundError('No recorded run for '+b+' '+p+'; register/ingest a snapshot first')
    rel=safe_relative(root,row['snapshot_path'],'snapshots')
    return root/rel


def pick_views(root,snap,summary):
    data=read(snap/'local-refinement-evidence.json') if (snap/'local-refinement-evidence.json').is_file() else {}
    selections=data.get('pose_selections',{})
    for item in summary['results']:
        pid=item['pose_id'];rel=item.get('revision_folder')
        if not isinstance(pid,str) or '/' in pid or '\\' in pid or '..' in pid:raise ValueError('Unsafe pose ID')
        if not rel:continue
        rev=(root/Path(str(rel).replace('\\','/'))).resolve()
        if not rev.is_relative_to((root/'poses').resolve()):raise ValueError('Unsafe revision path')
        folder=rev/'previews';num=int(selections.get(pid,{}).get('selected_attempt',0))
        if num>0:
            alternate=snap/'local-evidence'/pid/f'attempt-{num:02d}'/'previews'
            if alternate.resolve().is_relative_to((snap/'local-evidence').resolve()) and alternate.is_dir():folder=alternate
        if not folder.is_dir():continue
        for p in sorted(folder.glob('*.png')):
            if p.is_symlink():raise ValueError('Symlink preview not allowed: '+str(p))
            yield pid+'_'+p.name,p


def activate(root=ROOT,batch='0001',pas='01',snapshot=None):
    root=Path(root).resolve();snap=lookup(root,batch,pas,snapshot)
    summary=read(snap/'batch-summary.json')
    # Every run has its own immutable archive. Creating a missing archive is
    # allowed, but nothing is exported from unrelated global LATEST state.
    zipped=sorted(snap.glob('spose-remote-feedback-*.zip'))
    if zipped:zipfile=zipped[-1]
    else:
        from feedback_bundle import create_feedback,timestamp
        zipfile=snap/f"spose-remote-feedback-{normalize_batch(batch)}-{normalize_pass(pas)}_{timestamp()}.zip"
        create_feedback(snap,zipfile,root,prefer_webp=True,include_context=True)
        from registry import ingest_snapshot
        ingest_snapshot(root,snap)
    lock=root/'tracking'/'exchange-activation.lock'
    try:lock.mkdir()
    except FileExistsError as e:
        raise RuntimeError('Another activation is updating review/ and upload/. Do not delete lock while that process is running.') from e
    stage_name='activate-'+uuid.uuid4().hex[:10]
    stages=[];old_dirs=[]
    try:
        for name in ('review','upload'):
            stage=root/(name+'.'+stage_name+'.tmp')
            if stage.exists():raise FileExistsError(stage)
            stage.mkdir();stages.append(stage)
        review,upload=stages
        copied=[]
        for name,file in pick_views(root,snap,summary):
            shutil.copy2(file,review/name);shutil.copy2(file,upload/name)
            copied.append(name)
        notes=snap/'batch-summary.md'
        md=notes.read_text(encoding='utf-8') if notes.is_file() else '# Registered batch snapshot\n'
        for stage in stages:
            (stage/'SUMMARY.md').write_text(md,encoding='utf-8')
            write(stage/'manifest.json',{'schema_version':1,'batch_label':normalize_batch(batch),
              'pass_label':normalize_pass(pas),'snapshot':snap.relative_to(root).as_posix(),
              'feedback_zip':zipfile.name,'pose_count':len(summary['results']),
              'flat_images':copied,'ephemeral':True})
        shutil.copy2(zipfile,upload/zipfile.name)
        # Reversible two-directory swap; never replace snapshot contents.
        for name,stage in zip(('review','upload'),stages):
            target=root/name;old=root/(name+'.'+stage_name+'.old')
            if target.exists():
                if target.is_symlink() or not target.is_dir():raise ValueError('Unsafe existing exchange folder '+str(target))
                target.rename(old);old_dirs.append((target,old))
            stage.rename(target)
        for target,old in old_dirs:
            if old.exists():shutil.rmtree(old)
        return {'batch_label':normalize_batch(batch),'pass_label':normalize_pass(pas),
            'snapshot':snap.relative_to(root).as_posix(), 'review':str(root/'review'),
            'upload_zip':str(root/'upload'/zipfile.name),'image_count':len(copied),'view_only':True}
    except Exception:
        for name in ('review','upload'):
            target=root/name
            prior=root/(name+'.'+stage_name+'.old')
            if prior.exists():
                if target.exists():shutil.rmtree(target)
                prior.rename(target)
        raise
    finally:
        for stage in stages:
            if stage.exists():shutil.rmtree(stage)
        if lock.exists():lock.rmdir()


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--root',type=Path,default=ROOT)
    pa.add_argument('--batch',required=True);pa.add_argument('--pass',dest='pas',required=True)
    pa.add_argument('--snapshot',type=Path)
    args=pa.parse_args();print(json.dumps(activate(args.root,args.batch,args.pas,args.snapshot),indent=2))
if __name__=='__main__':main()
