"""Import a signed-by-hash (not cryptographically signed) data-only SPOSE V00 module.

Usage: python scripts/import_pose.py incoming/POSE-ID_YYYYMMDDTHHMMSSZ.zip --blender "C:/.../blender.exe"
Use --dry-run to verify the package without Blender. For output, no user asset is overwritten.
"""
import argparse,datetime,json,os,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,load_package,source_and_row,save_json,sha_bytes,sha_file,artifact_hashes,read_json
from update_tracking import record_job,export_snapshots

def main():
 pa=argparse.ArgumentParser(description=__doc__)
 pa.add_argument('package',type=Path)
 pa.add_argument('--blender',help='Path to local Blender executable (or SPOSE_BLENDER env var)')
 pa.add_argument('--dry-run',action='store_true',help='Validate ZIP and dependencies without writing anything')
 pa.add_argument('--save-blend',action='store_true',help='Save a full scene.blend in the pose revision (default off)')
 args=pa.parse_args()
 manifest,data=load_package(args.package)
 project,src,row=source_and_row(manifest['pose_id'])
 pair=read_json(ROOT/project['default_pair']['config'])
 pair_id,pair_version=pair['pair_id'],pair['version']
 if args.dry_run:
  print(json.dumps({'valid':True,'pose_id':manifest['pose_id'],'source_id':src['source_id'],'source_checkpoint':src['checkpoint'],'controls':len(data['rig-targets.json']['controls']),'geometry_engine':'rigify_floor_v2','validated_contract':True,'note':'No Blender execution or scene validation performed'},indent=2));return
 blender=args.blender or os.environ.get('SPOSE_BLENDER') or shutil.which('blender')
 if not blender or not Path(blender).is_file() and shutil.which(blender) is None:
  raise SystemExit('Blender unavailable. Set --blender to local blender.exe or SPOSE_BLENDER; run --dry-run for package-only verification.')
 base=ROOT/'poses'/manifest['pose_id']/pair_id/pair_version
 base.mkdir(parents=True,exist_ok=True)
 existing=[int(p.name[1:]) for p in base.glob('r[0-9][0-9][0-9]') if p.name[1:].isdigit()]
 revision=max(existing,default=0)+1
 final=base/f'r{revision:03d}'
 if final.exists():raise RuntimeError('Revision collision; refused overwrite')
 stage=Path(tempfile.mkdtemp(prefix='.pose-stage-',dir=base))
 issues=[];status='failed'
 try:
  (stage/'inputs').mkdir()
  with zipfile.ZipFile(args.package) as z:
   for name in z.namelist(): (stage/'inputs'/name).write_bytes(z.read(name))
  settings={'template_file':str((ROOT/'pairs'/pair_id/pair_version/'studies/VP001-v001/appearance-study.blend').resolve()),
   'fallback_template':str((ROOT/'pairs'/pair_id/pair_version/'template.blend').resolve()),
   'pair_id':pair_id,'pair_version':pair_version,'pose_id':manifest['pose_id'],'output':str(stage),
   'save_blend':args.save_blend,'render_config':data.get('render-config.json',{}),'validation_plan':data.get('validation-plan.json',{})}
  save_json(stage/'build-settings.json',settings)
  cmd=[str(blender),'--background','--factory-startup','--python',str(ROOT/'scripts'/'blender_build.py'),'--','--settings',str(stage/'build-settings.json')]
  proc=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',timeout=1800)
  (stage/'build.log').write_text(proc.stdout,encoding='utf-8')
  if proc.returncode!=0:
   issues.append({'code':'BLENDER_EXECUTION_FAILED','detail':f'Exit status {proc.returncode}; inspect build.log'})
  result=read_json(stage/'blender-result.json') if (stage/'blender-result.json').is_file() else {}
  if result.get('error'):issues.append({'code':'BLENDER_BUILD_ERROR','detail':str(result['error'])[:1000]})
  previews=[p.relative_to(stage).as_posix() for p in (stage/'previews').glob('*.png')] if (stage/'previews').exists() else []
  expected=['front.png','side.png','three-quarter.png']
  if any(not (stage/'previews'/n).is_file() for n in expected):issues.append({'code':'PREVIEWS_MISSING','detail':'Required front, side, three-quarter previews not all available'})
  if not (stage/'previews'/'qa-regions.png').is_file():issues.append({'code':'QA_REGIONS_MISSING','detail':'No region QA render; appearance not visually verified'})
  if proc.returncode==0 and result.get('rendered') and not issues and result.get('checks',{}).get('hard_gate_pass') is True:status='draft'
  if result.get('issues'):issues.extend(result['issues'])
  # Hard geometry failures cannot become ordinary drafts; preserve previews as evidence.
  if proc.returncode==0 and previews and result.get('checks',{}).get('hard_gate_pass') is False:
   status='blocked'
  # No Blender execution, successful render, or proxy can auto-accept a pose.
  validation={'schema_version':1,'status':'UNREVIEWED_CANDIDATE' if status=='draft' else ('GEOMETRY_BLOCKED' if status=='blocked' else 'BUILD_FAILED'),
      'blender_executed':proc.returncode==0,'rendered_views':previews,'technical_checks':result.get('checks',{}),
      'contact_checks':result.get('contact_checks',{}),'issues':issues,'user_accepted':False,'hard_gate_pass':result.get('checks',{}).get('hard_gate_pass') is True,'geometry_engine':'rigify_floor_v2'}
  save_json(stage/'validation.json',validation)
  record={'schema_version':1,'pose_id':manifest['pose_id'],'pair_id':pair_id,'pair_version':pair_version,'revision':revision,'status':status,
      'source_id':src['source_id'],'source_checkpoint':src['checkpoint'],'source_row_sha256':sha_bytes(row['specification'].encode('utf-8')),
      'source_parent_pose_id':row['parent_pose_id'],'source_generation_gate':row['generation_gate'],'source_catalog_sha256':src['catalog_sha256'],
      'rig_map_id':'RIG001','rig_map_version':'v001','template_sha256':manifest['dependencies']['template_sha256'],
      'body_profile_id':'BP001','body_profile_version':'v001','accepted_at':None,'issues':issues,
      'appearance':{'visual_profile_id':'VP001','visual_profile_version':'v001','actor_palette_ids':{'A':'COOL01','B':'WARM01'},'mode':'regions','qa_regions_preview':'previews/qa-regions.png' if (stage/'previews'/'qa-regions.png').exists() else None},
      'artifacts':{'scene':'scene.blend' if (stage/'scene.blend').exists() else None,'previews':previews,'validation':'validation.json','inputs':'inputs/'}}
  save_json(stage/'pose.json',record)
  save_json(stage/'checksums.json',artifact_hashes(stage))
  stage.rename(final)
  rel=final.relative_to(ROOT).as_posix()
  record_job(manifest['pose_id'],pair_id,pair_version,revision,status,src['checkpoint'],record['source_row_sha256'],row['generation_gate'],record['template_sha256'],rel,issues)
  export_snapshots()
  print(json.dumps({'status':status,'pose_id':manifest['pose_id'],'revision':revision,'output':rel,'previews':previews,'issues':issues},indent=2))
 finally:
  if stage.exists():
   # Preserve failures for forensics; never silently discard a live staged run.
   print(f'Incomplete staging retained: {stage}',file=sys.stderr)

if __name__=='__main__':main()
