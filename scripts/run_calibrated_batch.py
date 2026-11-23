"""SPOSE batch baseline, optional bounded local refinement, and one feedback export.

With local calibration enabled: baseline -> neutral/scene measurements -> prepare
local/ workspaces -> initial feedback. Agent makes 0..2 guided attempts per pose,
selects best individually, then calls --phase finalize. Without local calibration
this retains the original one-command render/measure/export workflow.
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from pose_common import ROOT,read_json


def invoke(argv):
    print('SPOSE command:', ' '.join(str(x) for x in argv),flush=True)
    return subprocess.run(argv,cwd=ROOT).returncode


def refresh_and_verify(scripts,statuses):
    statuses['refresh']=invoke([sys.executable,str(scripts/'refresh_exchange.py')])
    zips=sorted((ROOT/'upload').glob('spose-remote-feedback-*.zip'))
    statuses['feedback_zip']=str(zips[-1]) if zips else None
    statuses['verify']=invoke([sys.executable,str(scripts/'verify_feedback.py'),str(zips[-1])]) if zips else -1
    return 0 if statuses['refresh']==0 and statuses['verify']==0 else 2


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--blender',help='Required for baseline/render; not for finalize')
    pa.add_argument('--plan',default='batches/BATCH-001.json')
    pa.add_argument('--phase',choices=['baseline','finalize'],default='baseline')
    pa.add_argument('--local-calibration',choices=['plan','on','off'],default='plan')
    pa.add_argument('--max-local-attempts',type=int,choices=[0,1,2],default=None)
    pa.add_argument('--skip-blender',action='store_true',help='Use already saved matching Pass-04 baseline scenes, do not rerender')
    pa.add_argument('--rerun-baseline',action='store_true',help='Explicitly build new baseline revisions even when same package identity exists')
    args=pa.parse_args()
    scripts=Path(__file__).resolve().parent
    plan=ROOT/args.plan if not Path(args.plan).is_absolute() else Path(args.plan)
    doc=read_json(plan)
    cfg=doc.get('local_calibration',{})
    enabled=bool(cfg.get('enabled',False)) if args.local_calibration=='plan' else args.local_calibration=='on'
    max_attempts=args.max_local_attempts if args.max_local_attempts is not None else int(cfg.get('max_refinement_attempts',2))
    if not 0<=max_attempts<=2:raise ValueError('Local attempts must be between 0 and 2')
    enabled=enabled and max_attempts>0
    statuses={'mode':'finalize' if args.phase=='finalize' else 'baseline','local_calibration_enabled':enabled,'max_local_attempts':max_attempts}
    if args.phase=='finalize':
        if enabled:
            statuses['local_finalize']=invoke([sys.executable,str(scripts/'local_refinement.py'),'finalize'])
            if statuses['local_finalize']!=0:
                print(json.dumps(statuses,indent=2));return 2
        result=refresh_and_verify(scripts,statuses)
        print(json.dumps(statuses,indent=2));return result
    if not args.blender:raise ValueError('--blender required for baseline')
    if not args.skip_blender:
        cmd=[sys.executable,str(scripts/'run_pose_batch.py'),
            '--plan',str(plan),'--blender',args.blender,'--save-blend','--defer-feedback']
        if args.rerun_baseline:cmd.append('--rerun')
        statuses['batch']=invoke(cmd)
    statuses['calibration']=invoke([sys.executable,str(scripts/'collect_calibration.py'),
        '--blender',args.blender,'--plan',str(plan)])
    if enabled:
        from update_continuation import latest_snapshot
        snap=latest_snapshot(ROOT)
        if snap is None:
            statuses['prepare_error']='No persisted snapshot';print(json.dumps(statuses,indent=2));return 2
        prior=read_json(snap/'batch-summary.json')
        if (prior.get('batch_label'),prior.get('pass_label'))!=(doc.get('batch_label'),doc.get('pass_label')):
            statuses['prepare_error']='Latest snapshot is for a different batch/pass; refusing to attach unrelated local experiment'
            print(json.dumps(statuses,indent=2));return 2
        statuses['local_prepare']=invoke([sys.executable,str(scripts/'local_refinement.py'),'prepare',
            '--snapshot',str(snap),'--max-attempts',str(max_attempts)])
        if statuses['local_prepare']!=0:statuses['note']='Local preparation failed; use baseline results and repair configuration'
        else:statuses['next']='Review local/ACTIVE.json and proposal.json; run 0..2 trials per pose; select best; then --phase finalize'
    result=refresh_and_verify(scripts,statuses)
    print(json.dumps(statuses,indent=2));return result

if __name__=='__main__':sys.exit(main())
