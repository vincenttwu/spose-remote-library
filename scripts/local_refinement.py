"""Disposable, agent-guided SPOSE local calibration attempts (zero, one or two).

No authoritative pose revisions are written here. No SQLite updates, template
changes, or silent promotion. An agent must edit each attempt's proposal.json
with a causal hypothesis and bounded data-only control changes before running.
Each attempt builds in local/, probes its saved Blender scene, and writes an
immutable observed result. Finalize copies selected controls, attempts, selected
images and measurements into persistent snapshots/ before any local/ cleanup.

Commands (from installed library root):
 python scripts/local_refinement.py prepare --snapshot snapshots/<LATEST>
 python scripts/local_refinement.py status
 python scripts/local_refinement.py run --pose DOGG-DOGG-V00 --attempt 1 --blender <EXE>
 python scripts/local_refinement.py select --pose DOGG-DOGG-V00 --attempt 1 --reason "..."
 python scripts/local_refinement.py finalize
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, math, os, shutil, subprocess, sys, traceback
from pathlib import Path
from pose_common import ROOT, read_json, save_json

VIEWS=('front','side','three-quarter','qa-regions')
DIAGNOSTIC=('side','three-quarter')
CONTROL_SECTIONS={'controls','styling_controls'}
OBJECT_SECTIONS={
    'head_aim':{'target_elevation_deg'},
    'pelvic_alignment':{'target_distance_m','max_forward_shift_m'},
    'palm_surface_contact':{'target_gap_m','max_translation_m'},
    'head_side_floor':set(),
}
VECTOR_FIELDS={'value','direction_world','normal_world'}
ANGLE_FIELDS={'angle_deg','pitch_x_deg','yaw_z_deg'}
MAX_LOCAL_ATTEMPTS=2


def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def sha_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsonout(p, obj):p.parent.mkdir(parents=True,exist_ok=True);save_json(p,obj)

def active(root=ROOT):
    root=Path(root).resolve()
    # Explicit per-snapshot selection is the concurrency-safe Infra 0002 path.
    # Legacy ACTIVE.json remains available for manual single-batch workflows.
    configured=os.environ.get('SPOSE_LOCAL_SNAPSHOT')
    if configured:
        snap=(root/configured).resolve()
        if not snap.is_relative_to((root/'snapshots').resolve()):raise ValueError('Unsafe selected snapshot')
        pointer=snap/'local-session.json'
        if not pointer.is_file():raise FileNotFoundError('No local session for '+str(snap))
        obj=read_json(pointer)
        run=(root/obj['local_run']).resolve()
        if not run.is_relative_to((root/'local').resolve()):raise ValueError('Unsafe local workspace')
        session=read_json(run/'SESSION.json')
        if session.get('snapshot')!=snap.relative_to(root).as_posix():raise ValueError('Session/snapshot mismatch')
        return session,run,snap
    pointer=root/'local'/'ACTIVE.json'
    if not pointer.is_file():raise FileNotFoundError('No local session: run prepare after baseline render')
    obj=read_json(pointer)
    run=(root/obj['local_run']).resolve()
    if not run.is_relative_to((root/'local').resolve()):raise ValueError('Unsafe local workspace')
    snap=(root/obj['snapshot']).resolve()
    if not snap.is_relative_to((root/'snapshots').resolve()):raise ValueError('Unsafe snapshot path')
    if not run.is_dir() or not (snap/'batch-summary.json').is_file():raise FileNotFoundError('Missing session or snapshot')
    return obj,run,snap


def numbered_path(work,pose,n):return work/pose/f'attempt-{n:02d}'

def prepare(root=ROOT,snapshot=None, max_attempts=2):
    root=Path(root).resolve()
    if not 0<=max_attempts<=MAX_LOCAL_ATTEMPTS:raise ValueError('Maximum two local refinements per pose')
    if snapshot is None:
        from update_continuation import latest_snapshot
        snapshot=latest_snapshot(root)
    snap=Path(snapshot)
    if not snap.is_absolute():snap=root/snap
    snap=snap.resolve()
    if not snap.is_relative_to((root/'snapshots').resolve()):raise ValueError('Must select stored snapshot')
    summary=read_json(snap/'batch-summary.json')
    label=f"{summary['batch_label']}-{summary['pass_label']}_{summary['run_utc']}"
    work=root/'local'/label
    if work.exists():
        if (work/'SESSION.json').is_file() and read_json(work/'SESSION.json').get('snapshot')==snap.relative_to(root).as_posix():
            old=read_json(work/'SESSION.json')
            if old.get('max_refinement_attempts')!=max_attempts:raise ValueError('Existing local session has a different attempt limit; do not silently change experiment contract')
            return old
        raise FileExistsError('Local workspace exists with different source; preserve it before restarting')
    work.mkdir(parents=True)
    config={'schema_version':1,'kind':'spose-local-refinement-session','snapshot':snap.relative_to(root).as_posix(),
            'local_run':work.relative_to(root).as_posix(),'batch_label':summary['batch_label'],
            'pass_label':summary['pass_label'],'created_utc':now(),'max_refinement_attempts':max_attempts,
            'status':'prepared','poses':{}}
    registered=read_json(snap/'registered-run.json') if (snap/'registered-run.json').is_file() else {}
    plan_rel=registered.get('plan_path','batches/BATCH-001.json')
    plan_path=(root/plan_rel).resolve()
    if not plan_path.is_relative_to((root/'batches').resolve()):raise ValueError('Unsafe registered plan reference')
    if plan_path.is_file():
        plan_doc=read_json(plan_path)
        if plan_doc.get('batch_label')!=summary['batch_label'] or plan_doc.get('pass_label')!=summary['pass_label']:
            raise ValueError('Local plan and snapshot identity mismatch')
        config['guidance']=plan_doc.get('local_calibration',{}).get('guidance',{})
    for item in summary['results']:
        pose=item['pose_id']
        relative=item.get('revision_folder')
        baseline=root/Path(str(relative).replace('\\','/')) if relative else None
        pose_record={'baseline_revision':relative,'selected_attempt':0,'selection_reason':'Unchanged remote baseline (default)',
                     'available_attempts':[0] if baseline and (baseline/'inputs'/'rig-targets.json').is_file() else [],
                     'attempt_status':'baseline_available' if baseline and (baseline/'inputs'/'rig-targets.json').is_file() else 'baseline_unavailable'}
        config['poses'][pose]=pose_record
        if not pose_record['available_attempts']:continue
        folder=numbered_path(work,pose,0)
        (folder/'inputs').mkdir(parents=True)
        for p in sorted((baseline/'inputs').glob('*.json')):
            shutil.copy2(p,folder/'inputs'/p.name)
        (folder/'previews').mkdir()
        for p in sorted((baseline/'previews').glob('*.png')):
            shutil.copy2(p,folder/'previews'/p.name)
        for fn in ('validation.json','blender-result.json','pose.json'):
            if (baseline/fn).is_file():shutil.copy2(baseline/fn,folder/fn)
        jsonout(folder/'result.json',{'attempt':0,'pose_id':pose,'kind':'authoritative_baseline',
                 'revision_folder':relative,'status':item.get('build_status'),
                 'hypothesis':'remote baseline; no local changes','rig_targets_sha256':sha_file(folder/'inputs'/'rig-targets.json')})
        for n in range(1,max_attempts+1):
            proposal={
                'schema_version':1,'pose_id':pose,'attempt':n,'base_attempt':0,
                'hypothesis':'REPLACE: observation from baseline or preceding render',
                'expected_effect':'REPLACE: specify one measurable/visible change',
                'changes':[],
                'visual_review_note':'Not yet rendered',
                '_instructions':{
                    'example_change':{'section':'controls','actor':'A','bone':'hand_ik.L','field':'value','value':[0.16,0.08,-0.005]},
                    'control_keys':['actor','bone','space'],'sections':['controls','styling_controls','head_aim','pelvic_alignment','palm_surface_contact'],
                    'limits':'control offsets <=0.09m per attempt and <=0.16m from baseline; angles <=20deg per attempt and <=35deg from baseline',
                    'no_quality_gate':'Failed/poor attempts are logged. No automatic promotion.'}}
            jsonout(numbered_path(work,pose,n)/'proposal.json',proposal)
    jsonout(work/'SESSION.json',config)
    if not os.environ.get('SPOSE_LOCAL_SNAPSHOT'):
        jsonout(root/'local'/'ACTIVE.json',config)
    jsonout(snap/'local-session.json',{'schema_version':1,'local_run':config['local_run'],'enabled':True,'max_refinement_attempts':max_attempts})
    return config


def finite_number(v):return type(v) in (int,float) and math.isfinite(float(v))
def vec_distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def find_field(doc, change):
    section=change.get('section');field=change.get('field')
    if section in CONTROL_SECTIONS:
        if field not in VECTOR_FIELDS|ANGLE_FIELDS:raise ValueError('Field not allowed: '+str(field))
        actor=change.get('actor');bone=change.get('bone')
        if actor not in ('A','B') or not isinstance(bone,str):raise ValueError('Control needs actor A/B and bone')
        found=[x for x in doc.get(section,[]) if x.get('actor')==actor and x.get('bone')==bone
               and (not change.get('space') or x.get('space')==change['space'])]
        if len(found)!=1:raise ValueError('Control selector must match exactly one: '+str(change))
        if field not in found[0]:raise ValueError('Field not present in chosen control: '+str(field))
        return found[0]
    if section in OBJECT_SECTIONS:
        if field not in OBJECT_SECTIONS[section]:raise ValueError('Field not allowed for section '+str(section))
        target=doc.get(section)
        if not isinstance(target,dict) or field not in target:raise ValueError('Field absent in package: '+str(change))
        return target
    raise ValueError('Unknown change section '+str(section))


def apply_changes(data,baseline,proposal):
    data=copy.deepcopy(data)
    changes=proposal.get('changes')
    if not isinstance(changes,list) or not changes:raise ValueError('No changes provided: do not call unchanged pose a refinement')
    if len(changes)>16:raise ValueError('Too many simultaneous changes; limit each attempt to a focused hypothesis')
    applied=[];selectors=set()
    for c in changes:
        if not isinstance(c,dict):raise ValueError('Changes must be objects')
        key=(c.get('section'),c.get('actor'),c.get('bone'),c.get('space'),c.get('field'))
        if key in selectors:raise ValueError('Duplicate change selector')
        selectors.add(key)
        target=find_field(data,c);original=find_field(baseline,c)
        field=c['field'];value=c.get('value');prior=target[field];origin=original[field]
        if field in VECTOR_FIELDS:
            if not isinstance(value,list) or len(value)!=3 or not all(finite_number(x) for x in value):
                raise ValueError('Vector changes must be 3 finite floats')
            if not isinstance(prior,list) or len(prior)!=3 or not isinstance(origin,list):raise ValueError('Non-vector original')
            step=vec_distance(value,prior);total=vec_distance(value,origin)
            if field=='value':step_limit,total_limit=.09,.16
            else:step_limit,total_limit=.45,.70
            if step>step_limit+1e-8 or total>total_limit+1e-8:
                raise ValueError(f'{key}: change exceeds bounded step/total ({step:.3f}/{total:.3f})')
        elif field in ANGLE_FIELDS or field=='target_elevation_deg':
            if not finite_number(value) or not finite_number(prior) or not finite_number(origin):raise ValueError('Angle must be finite')
            if abs(value-prior)>20.0+1e-7 or abs(value-origin)>35.0+1e-7:raise ValueError('Angle step/total exceeds 20/35 deg')
            if field=='target_elevation_deg' and not -40<=value<=40:raise ValueError('Outside safe head aim range')
        else:
            if not finite_number(value) or not finite_number(prior) or not finite_number(origin):raise ValueError('Expected finite scalar')
            if not 0<=value<=.25 or abs(value-prior)>.07+1e-8 or abs(value-origin)>.12+1e-8:raise ValueError('Contact policy scalar outside bounded range')
        if value==prior:raise ValueError('No-op change listed: '+str(key))
        target[field]=value
        applied.append({'selector':{k:c[k] for k in ('section','actor','bone','space','field') if k in c},
                        'before':prior,'after':value,'baseline':origin})
    return data,applied


def run_attempt(root,pose,attempt,blender,timeout=1800):
    if attempt not in (1,2):raise ValueError('Only attempts 01 and 02 can be rendered as local refinements')
    _,work,snap=active(root)
    session=read_json(work/'SESSION.json')
    if session.get('status')=='finalized':raise ValueError('Already finalized; cannot append unrecorded attempts to persisted selection')
    if attempt>session['max_refinement_attempts']:raise ValueError('Configured refinement attempt limit reached')
    if pose not in session['poses']:raise ValueError('Pose is not in this batch')
    target=numbered_path(work,pose,attempt);proposal_path=target/'proposal.json'
    proposal=read_json(proposal_path)
    if proposal.get('pose_id')!=pose or proposal.get('attempt')!=attempt:raise ValueError('Proposal identity mismatch')
    parent=int(proposal.get('base_attempt',0))
    if parent not in (0,1) or parent>=attempt:raise ValueError('Invalid parent attempt')
    parent_dir=numbered_path(work,pose,parent)
    if not (parent_dir/'result.json').is_file() or (parent>0 and read_json(parent_dir/'result.json').get('status')!='rendered'):
        raise ValueError('Parent attempt not available')
    if (target/'result.json').exists():raise FileExistsError('Attempt already executed; never overwrite observations')
    data=read_json(parent_dir/'inputs'/'rig-targets.json')
    baseline=read_json(numbered_path(work,pose,0)/'inputs'/'rig-targets.json')
    result={'pose_id':pose,'attempt':attempt,'base_attempt':parent,'created_utc':now(),
            'hypothesis':proposal.get('hypothesis',''), 'expected_effect':proposal.get('expected_effect',''),
            'visual_review_note':proposal.get('visual_review_note',''), 'status':'started','applied_changes':[]}
    # Read-only probing and failed attempts are still valuable evidence.
    try:
        altered,changes=apply_changes(data,baseline,proposal)
        result['applied_changes']=changes
        target.joinpath('inputs').mkdir(exist_ok=False)
        for src in sorted((parent_dir/'inputs').glob('*.json')):shutil.copy2(src,target/'inputs'/src.name)
        jsonout(target/'inputs'/'rig-targets.json',altered)
        pair_root=Path(root)/'pairs/CPL01/v001'
        settings={'template_file':str(pair_root/'studies/VP001-v001/appearance-study.blend'),
                  'fallback_template':str(pair_root/'template.blend'),
                  'pair_id':'CPL01','pair_version':'v001','pose_id':pose,'output':str(target.resolve()),
                  'save_blend':True,'render_config':read_json(target/'inputs'/'render-config.json'),
                  'validation_plan':read_json(target/'inputs'/'validation-plan.json')}
        jsonout(target/'build-settings.json',settings)
        cmd=[str(blender),'--background','--factory-startup','--python',str(Path(root)/'scripts/blender_build.py'),
             '--','--settings',str(target/'build-settings.json')]
        proc=subprocess.run(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            text=True,encoding='utf-8',errors='replace',timeout=timeout)
        (target/'build.log').write_text(proc.stdout,encoding='utf-8')
        result['blender_returncode']=proc.returncode
        br=read_json(target/'blender-result.json') if (target/'blender-result.json').is_file() else {}
        result['builder_rendered']=bool(br.get('rendered'))
        result['builder_issues']=br.get('issues',[])
        result['preview_count']=len(list((target/'previews').glob('*.png'))) if (target/'previews').is_dir() else 0
        result['status']='rendered' if proc.returncode==0 and br.get('rendered') else 'build_failed'
        result['rig_targets_sha256']=sha_file(target/'inputs'/'rig-targets.json')
        scene=target/'scene.blend'
        if scene.is_file():
            probe=target/'calibration.json'
            rigmap=Path(root)/'tooling/rig-maps/RIG001-v001.json'
            pcmd=[str(blender),'--background','--factory-startup','--python',str(Path(root)/'scripts/calibration_probe_blender.py'),
                  '--','--mode','scene','--scene',str(scene),'--output',str(probe),'--pose-id',pose,
                  '--rig-map',str(rigmap)]
            try:
                pp=subprocess.run(pcmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                  text=True,encoding='utf-8',errors='replace',timeout=900)
                (target/'calibration.log').write_text(pp.stdout,encoding='utf-8')
                result['probe_status']='measured' if pp.returncode==0 and probe.is_file() else 'probe_failed'
            except Exception as exc:result['probe_status']='probe_exception';result['probe_error']=str(exc)
        else:result['probe_status']='no_scene'
    except Exception as exc:
        result['status']='attempt_error';result['error']=f'{type(exc).__name__}: {exc}'
        result['traceback']=traceback.format_exc()[-2500:]
    jsonout(target/'result.json',result)
    # Run errors are observations. Do not fail the remaining poses.
    return result


def select(root,pose,attempt,reason,score=None):
    _,work,snap=active(root)
    session=read_json(work/'SESSION.json')
    if session.get('status')=='finalized':raise ValueError('Already finalized; cannot silently change persistent candidate selection')
    if pose not in session['poses']:raise ValueError('Unknown pose')
    candidate=numbered_path(work,pose,attempt)
    if not (candidate/'result.json').is_file():raise ValueError('No candidate observation')
    observation=read_json(candidate/'result.json')
    if attempt>0 and observation.get('status')!='rendered':raise ValueError('Cannot select non-rendered candidate')
    if not isinstance(reason,str) or not reason.strip():raise ValueError('Selection requires local visual reasoning')
    entry=session['poses'][pose];entry['selected_attempt']=attempt;entry['selection_reason']=reason.strip()
    if score is not None:
        if not 0<=score<=10:raise ValueError('Score outside 0 to 10')
        entry['local_visual_score_out_of_10']=score
    jsonout(work/'SESSION.json',session)
    if not os.environ.get('SPOSE_LOCAL_SNAPSHOT'):jsonout(Path(root)/'local/ACTIVE.json',session)
    return {'pose_id':pose,'selected_attempt':attempt,'reason':reason,'score':score}


def finalize(root=ROOT):
    root=Path(root).resolve();_,work,snap=active(root)
    session=read_json(work/'SESSION.json')
    if session.get('status')=='finalized' and (snap/'local-refinement-evidence.json').is_file():
        return read_json(snap/'local-refinement-evidence.json')
    manifest={'schema_version':1,'kind':'spose-local-refinement-evidence','session':session['local_run'],
              'batch_label':session['batch_label'],'pass_label':session['pass_label'],
              'max_refinement_attempts':session['max_refinement_attempts'],'finalized_utc':now(),
              'pose_selections':{},'files_sha256':{},'warning':'Local candidate is not an authoritative library revision'}
    evidence=snap/'local-evidence';evidence.mkdir(exist_ok=True)
    for pose,entry in session['poses'].items():
        selected=int(entry.get('selected_attempt',0))
        attempted=[]
        for n in range(0,session['max_refinement_attempts']+1):
            src=numbered_path(work,pose,n)
            if not (src/'result.json').is_file():continue
            obs=read_json(src/'result.json')
            dst=evidence/pose/f'attempt-{n:02d}'
            dst.mkdir(parents=True,exist_ok=True)
            for name in ('result.json','proposal.json','calibration.json','blender-result.json'):
                if (src/name).is_file():shutil.copy2(src/name,dst/name)
            if n==selected:
                # Selected full control payload makes the candidate reconstructable
                if (src/'inputs'/'rig-targets.json').is_file():
                    shutil.copy2(src/'inputs'/'rig-targets.json',dst/'rig-targets.json')
            if n>0:
                (dst/'previews').mkdir(exist_ok=True)
                for name in (VIEWS if n==selected else DIAGNOSTIC):
                    path=src/'previews'/f'{name}.png'
                    if path.is_file():shutil.copy2(path,dst/'previews'/path.name)
            attempted.append({'attempt':n,'status':obs.get('status'),'reported_image_count':obs.get('preview_count',4 if n==0 else 0),
                              'probe_status':obs.get('probe_status','baseline_from_collector'),
                              'applied_changes':len(obs.get('applied_changes',[]))})
        manifest['pose_selections'][pose]={'selected_attempt':selected,'selection_reason':entry.get('selection_reason'),
            'local_visual_score_out_of_10':entry.get('local_visual_score_out_of_10'),
            'baseline_revision_folder':entry.get('baseline_revision'),'attempts':attempted,
            'selected_is_authoritative_baseline':selected==0}
    for f in sorted(evidence.rglob('*')):
        if f.is_file():manifest['files_sha256'][f.relative_to(snap).as_posix()]=sha_file(f)
    jsonout(snap/'local-refinement-evidence.json',manifest)
    session['status']='finalized';jsonout(work/'SESSION.json',session)
    if not os.environ.get('SPOSE_LOCAL_SNAPSHOT'):
        jsonout(root/'local'/'ACTIVE.json',session)
    return manifest


def status(root=ROOT):
    _,work,snap=active(root)
    state=read_json(work/'SESSION.json')
    out={'snapshot':str(snap),'status':state['status'],'max_attempts':state['max_refinement_attempts'],'poses':{}}
    for pose,item in state['poses'].items():
        out['poses'][pose]={'selected':item.get('selected_attempt',0),'attempts':[{'attempt':n,'status':read_json(numbered_path(work,pose,n)/'result.json').get('status')}
             for n in range(state['max_refinement_attempts']+1) if (numbered_path(work,pose,n)/'result.json').is_file()]}
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-snapshot',help='Explicit persistent snapshot path for independent local sessions; required for parallel batch use')
    sub=parser.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--snapshot',type=Path);prep.add_argument('--max-attempts',type=int,default=2)
    r=sub.add_parser('run');r.add_argument('--pose',required=True);r.add_argument('--attempt',type=int,choices=[1,2],required=True);r.add_argument('--blender',required=True)
    s=sub.add_parser('select');s.add_argument('--pose',required=True);s.add_argument('--attempt',type=int,choices=[0,1,2],required=True);s.add_argument('--reason',required=True);s.add_argument('--score',type=float)
    sub.add_parser('status');sub.add_parser('finalize')
    a=parser.parse_args()
    if a.session_snapshot:
        os.environ['SPOSE_LOCAL_SNAPSHOT']=a.session_snapshot
    if a.command=='prepare':out=prepare(snapshot=a.snapshot or a.session_snapshot,max_attempts=a.max_attempts)
    elif a.command=='run':out=run_attempt(ROOT,a.pose,a.attempt,a.blender)
    elif a.command=='select':out=select(ROOT,a.pose,a.attempt,a.reason,a.score)
    elif a.command=='finalize':out=finalize()
    else:out=status()
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
