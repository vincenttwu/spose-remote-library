"""Run or finalize ONE identified SPOSE batch/pass, independent of other batches.

Infra 0002 replaces global 'latest snapshot' selection with explicit identity.
No implicit review/upload mutation; use activate_batch.py when YOU want the flat
view. Local experiments use per-snapshot sessions and remain disposable.

Examples:
  python scripts/run_registered_batch.py --phase baseline --plan batches/BATCH-002.json --blender "<EXE>"
  python scripts/local_refinement.py --session-snapshot snapshots/<run> status
  python scripts/run_registered_batch.py --phase finalize --snapshot snapshots/<run>
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from registry import ROOT,register_plan,ingest_snapshot,read,normalize_batch,normalize_pass,record_artifact,export_dict,write


def run_baseline(root,plan,blender,local_calibration='plan',max_local_attempts=None,collect=True,rerun=False):
    root=Path(root).resolve();plan=Path(plan)
    if not plan.is_absolute():plan=root/plan
    metadata=register_plan(root,plan)
    doc=read(plan)
    prefix=metadata['batch_id']+'-'+metadata['pass_id']+'_'
    before={p.name for p in (root/'snapshots').glob(prefix+'*') if p.is_dir()}
    # Respect original pose-module data contracts and save authoritative baseline scenes.
    from run_pose_batch import run
    result=run(plan,blender=blender,dry_run=False,save_blend=True,rerun=rerun,defer_feedback=True)
    after=[p for p in (root/'snapshots').glob(prefix+'*') if p.is_dir() and p.name not in before and (p/'batch-summary.json').is_file()]
    if len(after)!=1:raise RuntimeError('Expected exactly one new matching snapshot, got '+str(len(after)))
    snap=after[0];srel=snap.relative_to(root).as_posix()
    registration=ingest_snapshot(root,snap)
    write(snap/'registered-run.json',{'schema_version':1,'batch_id':metadata['batch_id'],'pass_id':metadata['pass_id'],
      'snapshot':srel,'plan_path':metadata['plan_path'],'status':'baseline_recorded'})
    calibration={'status':'skipped'}
    if collect:
        try:
            from collect_calibration import collect as collect_blender
            outcome=collect_blender(root=root,blender=blender,plan=plan)
            calibration={'status':'recorded','run_dir':outcome['calibration_run'],'poses_measured':outcome['poses_measured']}
            write(snap/'calibration-run.json',{'run_dir':Path(outcome['calibration_run']).resolve().relative_to(root).as_posix(),
                 'batch_label':metadata['batch_id'],'pass_label':metadata['pass_id'],
                 'poses_measured':outcome['poses_measured']})
        except Exception as ex:
            calibration={'status':'probe_error','error':f'{type(ex).__name__}: {ex}'}
            write(snap/'calibration-run.json',{'status':'probe_error','error':calibration['error'],
                    'batch_label':metadata['batch_id'],'pass_label':metadata['pass_id']})
    cfg=doc.get('local_calibration',{})
    enabled=bool(cfg.get('enabled', False)) if local_calibration=='plan' else local_calibration=='on'
    limit=int(cfg.get('max_refinement_attempts',2)) if max_local_attempts is None else max_local_attempts
    if not 0<=limit<=2:raise ValueError('max-local-attempts must be 0..2')
    enabled=enabled and limit>0
    local={'status':'disabled'}
    if enabled:
        try:
            from local_refinement import prepare
            old=os.environ.get('SPOSE_LOCAL_SNAPSHOT');os.environ['SPOSE_LOCAL_SNAPSHOT']=srel
            try:session=prepare(root=root,snapshot=snap,max_attempts=limit)
            finally:
                if old is None:os.environ.pop('SPOSE_LOCAL_SNAPSHOT',None)
                else:os.environ['SPOSE_LOCAL_SNAPSHOT']=old
            local={'status':'prepared','local_run':session['local_run'],'max_refinement_attempts':limit}
        except Exception as ex:local={'status':'prepare_error','error':f'{type(ex).__name__}: {ex}'}
    write(snap/'registered-run.json',{'schema_version':1,'batch_id':metadata['batch_id'],'pass_id':metadata['pass_id'],
      'snapshot':srel,'plan_path':metadata['plan_path'],'calibration':calibration,'local':local,'new_revision_count':result.get('new_revision_count',0),
      'reused_revision_count':result.get('reused_revision_count',0)})
    return {'snapshot':srel,'registration':registration,'calibration':calibration,'local':local,
            'new_revision_count':result.get('new_revision_count',0),'reused_revision_count':result.get('reused_revision_count',0),
            'next':'Review saved baseline images; use explicit --session-snapshot for trials, then --phase finalize --snapshot <path>'}


def finalize(root,snapshot):
    root=Path(root).resolve();s=Path(snapshot)
    snap=(s if s.is_absolute() else root/s).resolve()
    if not snap.is_relative_to((root/'snapshots').resolve()):raise ValueError('Invalid snapshot directory')
    summary=read(snap/'batch-summary.json')
    b=normalize_batch(summary['batch_label']);pa=normalize_pass(summary['pass_label'])
    if (snap/'local-session.json').is_file() and not (snap/'local-refinement-evidence.json').is_file():
        from local_refinement import finalize as local_finalize
        prior=os.environ.get('SPOSE_LOCAL_SNAPSHOT');os.environ['SPOSE_LOCAL_SNAPSHOT']=snap.relative_to(root).as_posix()
        try:local_finalize(root)
        finally:
            if prior is None:os.environ.pop('SPOSE_LOCAL_SNAPSHOT',None)
            else:os.environ['SPOSE_LOCAL_SNAPSHOT']=prior
    from feedback_bundle import create_feedback,timestamp
    from update_continuation import generate
    generate(root,snap)
    # Refresh registry before embedding it in the archive; export is read-only.
    registration=ingest_snapshot(root,snap)
    out=snap/f'spose-remote-feedback-{b}-{pa}_{timestamp()}.zip'
    feedback=create_feedback(snap,out,root,prefer_webp=True,include_context=True)
    registration=ingest_snapshot(root,snap)
    return {'snapshot':snap.relative_to(root).as_posix(),'feedback_zip':str(out),'feedback':feedback,
            'registry':registration,'view_changed':False,
            'next':'Use activate_batch.py --batch <n> --pass <n> if you want to refresh flat review/ and upload/'}


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--root',type=Path,default=ROOT)
    pa.add_argument('--phase',choices=['baseline','finalize'],required=True)
    pa.add_argument('--plan',type=Path)
    pa.add_argument('--snapshot',type=Path)
    pa.add_argument('--blender')
    pa.add_argument('--local-calibration',choices=['plan','on','off'],default='plan')
    pa.add_argument('--max-local-attempts',type=int,choices=[0,1,2])
    pa.add_argument('--no-probes',action='store_true')
    pa.add_argument('--rerun',action='store_true')
    args=pa.parse_args()
    if args.phase=='baseline':
        if not args.plan or not args.blender:pa.error('--phase baseline requires --plan and --blender')
        out=run_baseline(args.root,args.plan,args.blender,args.local_calibration,args.max_local_attempts,not args.no_probes,args.rerun)
    else:
        if not args.snapshot:pa.error('--phase finalize requires --snapshot')
        out=finalize(args.root,args.snapshot)
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
