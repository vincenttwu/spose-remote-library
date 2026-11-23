"""Run EVERY pose in a SPOSE batch, record every outcome, and export one feedback bundle.

No geometry/source/human-review gates. A build can be unstable and still be a usable
' draft'. Failure of one pose never prevents attempting the remaining poses.

Run from inside any standalone full-library root:
    python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
    python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "C:/.../blender.exe"
    python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "C:/.../blender.exe" --rerun

Package checks remain for identity, checksums and safe JSON only.
"""
from __future__ import annotations
import argparse, datetime, json, os, shutil, subprocess, sys, traceback, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT, load_package, read_json, save_json


def iso_stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def versions(pose_id, pair_id='CPL01', pair_version='v001'):
    base=ROOT/'poses'/pose_id/pair_id/pair_version
    return {p.name:p for p in base.glob('r[0-9][0-9][0-9]') if p.is_dir()}


def matching_prior(pose_id,package_timestamp, pair_id='CPL01', pair_version='v001'):
    for p in sorted(versions(pose_id,pair_id,pair_version).values(),reverse=True):
        manifest=p/'inputs'/'manifest.json'
        if not manifest.is_file():continue
        try:
            if read_json(manifest).get('package_timestamp_utc')==package_timestamp:
                return p
        except (ValueError,KeyError):continue
    return None


def report_one(pose_id,package_name,folder,build_status,build_output=None):
    result={'pose_id':pose_id,'package':package_name,'revision_folder':str(folder.relative_to(ROOT)) if folder else None,
            'build_status':build_status,'accepted':False,'geometry_quality':'not_measured',
            'issue_count':0,'issues':[],'previews':[],'feedback_file':None}
    if folder and (folder/'pose.json').is_file():
        record=read_json(folder/'pose.json')
        result['revision']=record.get('revision')
        result['build_status']=record.get('status',build_status)
        result['accepted']=record.get('status')=='accepted'
        result['issues']=record.get('issues',[])
        val=read_json(folder/'validation.json') if (folder/'validation.json').is_file() else {}
        result['geometry_quality']='meets_reference' if val.get('hard_gate_pass') is True else 'needs_review'
        result['stability']=val.get('stability','unreviewed')
        result['issue_count']=len(result['issues'])
        result['previews']=val.get('rendered_views',[])
        checks=val.get('technical_checks',{})
        result['posture_heights']=checks.get('posture_heights',{})
        result['contact_checks']=val.get('contact_checks',{})
    if build_output is not None:result['execution_output']=build_output[-5000:]
    return result


def summarize(results,batch_id,created_at):
    lines=[f'# {batch_id} — complete batch execution', '',
           f'Run: `{created_at}`. **No geometry or approval gates; all available poses attempted.**',
           '', '| Pose | Revision | Build | Stability | Issues | Previews |',
           '|---|---|---|---|---:|---:|']
    for item in results:
        rev='r'+str(item.get('revision','')).zfill(3) if item.get('revision') is not None else '—'
        lines.append(f"| `{item['pose_id']}` | {rev} | {item.get('build_status','unknown')} | {item.get('stability',item.get('geometry_quality','unknown'))} | {item.get('issue_count',0)} | {len(item.get('previews',[]))} |")
    lines += ['','Build warnings are reference measurements, not reasons to pause other poses or other batches.',
              'Failed executions are recorded and can be repaired later. No pose is auto-accepted.','']
    return '\n'.join(lines)


def run(plan,blender=None,dry_run=False,save_blend=False,rerun=False):
    doc=read_json(plan)
    if doc.get('schema_version')!=1 or not isinstance(doc.get('poses'),list) or not doc['poses']:
        raise ValueError('Invalid batch plan: expected nonempty poses[]')
    name=doc.get('batch_id','SPOSE-BATCH')
    if not all(isinstance(x,dict) and x.get('pose_id') and x.get('package') for x in doc['poses']):
        raise ValueError('Each batch item needs pose_id and package')
    if len({x['pose_id'] for x in doc['poses']})!=len(doc['poses']):
        raise ValueError('Duplicate pose ID in one plan')
    if not dry_run:
        blender=blender or os.environ.get('SPOSE_BLENDER') or shutil.which('blender')
        if not blender or not (Path(blender).is_file() or shutil.which(blender)):
            raise ValueError('Blender executable required, pass --blender or set SPOSE_BLENDER')
    stamp=iso_stamp()
    folder=ROOT/'reports'/'batches'/f'{name}_{stamp}'
    if not dry_run:folder.mkdir(parents=True,exist_ok=False)
    results=[]
    for entry in doc['poses']:
        pose_id=entry['pose_id'];pkg_name=entry['package']
        if Path(pkg_name).name!=pkg_name:  # packages always in local incoming/, no external source
            results.append({'pose_id':pose_id,'package':pkg_name,'build_status':'package_path_error','issue_count':1,'issues':['Unsafe package filename']})
            continue
        archive=ROOT/'incoming'/pkg_name
        try:
            manifest,data=load_package(archive)
            if manifest['pose_id']!=pose_id:raise ValueError('Pose ID and plan mismatch')
            pair=manifest['dependencies'];pair_id=pair['pair_id'];pair_version=pair['pair_version']
            if dry_run:
                results.append({'pose_id':pose_id,'package':pkg_name,'build_status':'package_verified',
                                'geometry_quality':'not_measured','controls':len(data['rig-targets.json']['controls'])})
                continue
            existing=matching_prior(pose_id,manifest['package_timestamp_utc'],pair_id,pair_version)
            if existing and not rerun:
                item=report_one(pose_id,pkg_name,existing,'previously_built')
                item['execution_note']='Already imported this exact package; reused revision. --rerun creates another.'
            else:
                before=set(versions(pose_id,pair_id,pair_version))
                cmd=[sys.executable,str(ROOT/'scripts/import_pose.py'),str(archive),'--blender',str(blender)]
                if save_blend:cmd.append('--save-blend')
                try:
                    proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,
                                        encoding='utf-8',errors='replace',timeout=2400)
                    output=(proc.stdout or '')+'\n'+(proc.stderr or '')
                    rc=proc.returncode
                except Exception as ex:
                    output=traceback.format_exc();rc=-1
                after=versions(pose_id,pair_id,pair_version)
                new=[p for k,p in after.items() if k not in before]
                found=max(new,key=lambda p:p.name) if new else matching_prior(pose_id,manifest['package_timestamp_utc'],pair_id,pair_version)
                item=report_one(pose_id,pkg_name,found,'execution_failed' if rc else 'attempted',output)
                item['import_returncode']=rc
            pose_rev=item.get('revision')
            if pose_rev is not None:
                feedback=folder/f'{pose_id}_r{pose_rev:03d}_feedback.zip'
                cmd=[sys.executable,str(ROOT/'scripts/export_feedback.py'),pose_id,'--revision',str(pose_rev),'--output',str(feedback)]
                exp=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
                if exp.returncode==0 and feedback.is_file():item['feedback_file']=feedback.name
                else:item['feedback_export_error']=(exp.stderr or exp.stdout or '')[-1000:]
        except Exception as ex:
            item={'pose_id':pose_id,'package':pkg_name,'build_status':'package_or_import_error',
                  'issue_count':1,'issues':[str(ex)],'exception':traceback.format_exc()[-2000:]}
        results.append(item)
        if not dry_run:save_json(folder/'batch-summary.partial.json',{'batch_id':name,'results':results})
    summary={'schema_version':1,'batch_id':name,'run_utc':stamp,'mode':'dry_run' if dry_run else 'render_all',
             'progression_policy':'record_and_continue_no_gates','input_count':len(doc['poses']),
             'result_count':len(results),'blender_used':not dry_run,'results':results}
    if dry_run:return summary
    save_json(folder/'batch-summary.json',summary)
    (folder/'batch-summary.md').write_text(summarize(results,name,stamp),encoding='utf-8')
    feedback_bundle=ROOT/'reports'/f'{name}_{stamp}_combined_feedback.zip'
    with zipfile.ZipFile(feedback_bundle,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.name!='batch-summary.partial.json':z.write(p,p.name)
    summary['combined_feedback_zip']=str(feedback_bundle)
    summary['report_folder']=str(folder)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=ROOT/'batches/BATCH-001.json')
    parser.add_argument('--blender',help='Blender 5.2 executable; uses SPOSE_BLENDER or PATH if omitted')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--save-blend',action='store_true')
    parser.add_argument('--rerun',action='store_true',help='Rerender even if this exact package already has a revision')
    a=parser.parse_args()
    print(json.dumps(run(a.plan,a.blender,a.dry_run,a.save_blend,a.rerun),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
