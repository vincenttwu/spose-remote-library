"""Collect SPOSE pose-agnostic rig measurements and five rendered-scene probes.

Runs an isolated Blender process for neutral template and each saved scene.
All output is versioned JSON under tooling/calibration/CPL01-v001/runs/;
LATEST.json points to the last completed run for feedback inclusion. This
script never edits a Blender template, pose revision or SQLite tracker.

From library root:
  python scripts/collect_calibration.py --blender "<BLENDER_EXE>" --plan batches/BATCH-001.json
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json,save_json,sha_file


def timestamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def package_timestamp(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return json.loads(z.read('manifest.json'))['package_timestamp_utc']


def current_pose_scene(root,entry):
    """Never silently use an older scene when the new package failed."""
    pkg=root/'incoming'/entry['package']
    if not pkg.is_file():return None,'missing_input_pose_package'
    ts=package_timestamp(pkg)
    base=root/'poses'/entry['pose_id']/'CPL01'/'v001'
    for rev in sorted(base.glob('r[0-9][0-9][0-9]'),reverse=True):
        mi=rev/'inputs'/'manifest.json'
        if mi.is_file() and read_json(mi).get('package_timestamp_utc')==ts:
            sc=rev/'scene.blend'
            if sc.is_file():return sc,None
            return None,'matching_revision_has_no_scene_blend_run_batch_with_--save-blend'
    return None,'matching_revision_not_built'


def collect(root=ROOT,blender=None,plan=None,timeout=900):
    root=Path(root).resolve()
    blender=blender or os.environ.get('SPOSE_BLENDER') or shutil.which('blender')
    if not blender or not (Path(blender).is_file() or shutil.which(blender)):
        raise ValueError('Blender not found; specify --blender or SPOSE_BLENDER')
    plan=Path(plan) if plan else root/'batches'/'BATCH-001.json'
    if not plan.is_absolute():plan=root/plan
    doc=read_json(plan)
    if not isinstance(doc.get('poses'),list) or not doc['poses']:
        raise ValueError('Invalid batch plan')
    template=root/'pairs/CPL01/v001/template.blend'
    rig_map=root/'tooling/rig-maps/RIG001-v001.json'
    for p in [template,rig_map]:
        if not p.is_file():raise FileNotFoundError(p)
    stamp=timestamp()
    parent=root/'tooling'/'calibration'/'CPL01-v001'
    destination=parent/'runs'/f"{doc.get('batch_label','batch-0001')}-{doc.get('pass_label','pass-04')}_{stamp}"
    destination.mkdir(parents=True,exist_ok=False)
    probe=root/'scripts'/'calibration_probe_blender.py'
    result={'schema_version':1,'kind':'spose-calibration-run','run_utc':stamp,
            'batch_label':doc.get('batch_label'),'pass_label':doc.get('pass_label'),
            'template_sha256':sha_file(template),'rig_map_sha256':sha_file(rig_map),
            'blender_executable':str(blender),
            'note':'Read-only measurements; pose-specific scenes are inspected without saving any .blend',
            'entries':[]}

    def launch(mode,pose_id,scene,name):
        out=destination/f'{name}.json'
        logfile=destination/f'{name}.log'
        args=[str(blender),'--background','--factory-startup','--python',str(probe),'--',
              '--mode',mode,'--scene',str(scene),'--output',str(out),'--rig-map',str(rig_map)]
        if pose_id:args+=['--pose-id',pose_id]
        entry={'name':name,'mode':mode,'pose_id':pose_id,'status':'not_run',
               'source_scene':str(scene.relative_to(root)) if scene.is_relative_to(root) else str(scene)}
        try:
            p=subprocess.run(args,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
            logfile.write_text((p.stdout or '')+'\n---STDERR---\n'+(p.stderr or ''),encoding='utf-8')
            entry['returncode']=p.returncode
            if p.returncode==0 and out.is_file():
                json.loads(out.read_text(encoding='utf-8'))
                entry.update({'status':'measured','file':out.name,'sha256':sha_file(out)})
            else:
                entry.update({'status':'probe_failed','error':'Inspect '+logfile.name})
        except Exception as ex:
            logfile.write_text(f'{type(ex).__name__}: {ex}\n',encoding='utf-8')
            entry.update({'status':'probe_exception','error':str(ex)})
        result['entries'].append(entry)
        save_json(destination/'CALIBRATION-MANIFEST.json',result)
        return entry

    launch('neutral',None,template,'neutral-rig')
    for entry in doc['poses']:
        pose_id=entry['pose_id']
        scene,error=current_pose_scene(root,entry)
        if error:
            result['entries'].append({'name':pose_id,'pose_id':pose_id,'mode':'scene','status':'not_measured','reason':error})
            save_json(destination/'CALIBRATION-MANIFEST.json',result)
        else:launch('scene',pose_id,scene,pose_id)
    files={p.name:sha_file(p) for p in destination.glob('*.json') if p.name!='CALIBRATION-MANIFEST.json'}
    result['files_sha256']=files
    result['measurements_completed']=sum(x.get('status')=='measured' for x in result['entries'])
    result['poses_measured']=sum(x.get('status')=='measured' and x.get('mode')=='scene' for x in result['entries'])
    result['all_requested_pose_probes_attempted']=True
    save_json(destination/'CALIBRATION-MANIFEST.json',result)
    latest={'schema_version':1,'run_dir':destination.relative_to(parent).as_posix(),
            'run_utc':stamp,'batch_label':doc.get('batch_label'),'pass_label':doc.get('pass_label'),
            'measurements_completed':result['measurements_completed'],
            'poses_measured':result['poses_measured']}
    save_json(parent/'LATEST.json',latest)
    return {'calibration_run':str(destination),'latest_pointer':str(parent/'LATEST.json'),**latest,
            'statuses':[{k:e.get(k) for k in ('pose_id','name','status','reason','error')} for e in result['entries']]}


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--root',type=Path,default=ROOT)
    pa.add_argument('--blender')
    pa.add_argument('--plan',type=Path)
    pa.add_argument('--timeout',type=int,default=900)
    args=pa.parse_args()
    print(json.dumps(collect(args.root,args.blender,args.plan,args.timeout),indent=2))


if __name__=='__main__':main()
