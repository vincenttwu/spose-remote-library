"""SPOSE remote: portable package validation and read-only source utilities.
Only stdlib is used here. No executable code is accepted from a pose ZIP.
"""
from pathlib import Path
import csv,hashlib,json,os,re,zipfile

ROOT=Path(__file__).resolve().parents[1]
POSE_RE=re.compile(r'^[A-Z0-9]{4,6}-[A-Z0-9]{3,6}-V\d{2}$')
PACKAGE_RE=re.compile(r'^(?P<id>[A-Z0-9]{4,6}-[A-Z0-9]{3,6}-V\d{2})_(?P<ts>\d{8}T\d{6}Z)\.zip$')
ALLOWED={'manifest.json','pose.json','rig-targets.json','contacts.json','render-config.json','validation-plan.json'}
REQUIRED={'manifest.json','pose.json','rig-targets.json','contacts.json'}
MAX_TOTAL=4*1024*1024

def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()
def save_json(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name(p.name+'.tmp')
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)

def source_and_row(pose_id):
 project=read_json(ROOT/'project.json')
 reg_path=ROOT/project['source_config'];src=read_json(reg_path)
 if src.get('root_relative_to')!='config_file': raise ValueError('Non-relocatable source registration')
 path=(reg_path.parent/src['root']/src['canonical_catalog']).resolve()
 if not path.is_relative_to(ROOT.resolve()): raise ValueError('Source path outside library')
 if sha_file(path)!=src['catalog_sha256']: raise ValueError('Source catalog hash mismatch')
 with path.open('r',encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  rows=[r for r in reader if r['pose_id']==pose_id]
 if len(rows)!=1: raise ValueError('Pose ID not unique or not present in source')
 return project,src,rows[0]

def load_package(zip_path,validate_dependencies=True):
 path=Path(zip_path)
 m=PACKAGE_RE.fullmatch(path.name)
 if not m: raise ValueError('Filename must be {POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip')
 if not path.is_file():raise FileNotFoundError(path)
 with zipfile.ZipFile(path) as z:
  names=z.namelist()
  if not REQUIRED.issubset(names) or len(set(names))!=len(names) or (set(names)-ALLOWED):
   raise ValueError('Unexpected, duplicate, or missing ZIP members; packages contain only allowed JSON files')
  if any(i.is_dir() or i.file_size>MAX_TOTAL or i.flag_bits & 0x1 or ((i.external_attr>>16) & 0o170000)==0o120000 for i in z.infolist()):
   raise ValueError('Directories, symlinks, encrypted entries or oversized files are not allowed')
  if sum(i.file_size for i in z.infolist())>MAX_TOTAL:raise ValueError('Oversized ZIP payload')
  payload={name:z.read(name) for name in names}
 data={k:json.loads(v) for k,v in payload.items()}
 manifest=data['manifest.json']
 if manifest.get('schema_version')!=1 or manifest.get('package_type')!='spose_pose_module':raise ValueError('Unsupported pose manifest version/type')
 if manifest.get('pose_id')!=m.group('id') or manifest.get('package_timestamp_utc')!=m.group('ts'):raise ValueError('Filename and manifest identity mismatch')
 if manifest.get('payload_sha256')!={name:sha_bytes(payload[name]) for name in sorted(set(names)-{'manifest.json'})}:
  raise ValueError('Payload checksum mismatch')
 if data['pose.json'].get('pose_id')!=manifest['pose_id'] or data['rig-targets.json'].get('schema_version')!=1:
  raise ValueError('Pose identity or rig targets schema invalid')
 if data['contacts.json'].get('schema_version')!=1:raise ValueError('Contacts schema invalid')
 if not isinstance(data['contacts.json'].get('anchors',[]),list):raise ValueError('Contacts anchors must be a list')
 if not isinstance(data['rig-targets.json'].get('controls'),list) or not data['rig-targets.json']['controls']:
  raise ValueError('At least one explicit rig control is required')
 # Mandatory v2 engine marker: legacy v1 payloads led to standing-only poses.
 rt=data['rig-targets.json']
 if rt.get('engine')!='rigify_floor_v2' or rt.get('geometry_contract_version')!=2:
  raise ValueError('GEOMETRY_ENGINE_V2_REQUIRED: old Batch 001 controls cannot produce valid kneeling geometry')
 def triplet(v,role,bound=20):
  import math
  if not(isinstance(v,list) and len(v)==3 and all(type(x) in (int,float) and math.isfinite(x) and abs(x)<=bound for x in v)):
   raise ValueError(f'{role} requires a bounded finite three-number vector')
 valid_spaces={'POSE_LOCAL_ROTATION_DEG','POSE_WORLD_HEAD_M',
  'POSE_WORLD_HEAD_ROT_X_DEG','POSE_WORLD_HAND_FRAME','POSE_RELATIVE_BONE_HEAD_HAND',
  'POSE_LOCAL_REST_AXIS_ROT_X_DEG','OBJECT_WORLD_LOCATION_M','OBJECT_WORLD_ROTATION_DEG'}
 from math import isfinite
 for c in rt['controls']:
  if c.get('actor') not in ('A','B') or c.get('space') not in valid_spaces:raise ValueError('Unknown actor/control space')
  if c['space'].startswith('POSE_') and (not isinstance(c.get('bone'),str) or not c['bone']):raise ValueError('Missing bone')
  if c['space'].startswith('OBJECT_') and c.get('object_role')!='root':raise ValueError('Only pair roots allowed')
  triplet(c.get('value'),'control.value',180 if c['space'].endswith('ROTATION_DEG') else 5)
  if c['space']=='POSE_WORLD_HEAD_ROT_X_DEG':
   if type(c.get('pitch_x_deg')) not in (float,int) or not -180<=c['pitch_x_deg']<=180:raise ValueError('Missing bounded pitch_x_deg')
   if type(c.get('yaw_z_deg',0)) not in (float,int) or not -180<=c.get('yaw_z_deg',0)<=180:raise ValueError('Invalid yaw_z_deg')
  if c['space'] in ('POSE_WORLD_HAND_FRAME','POSE_RELATIVE_BONE_HEAD_HAND'):
   triplet(c.get('direction_world'),'hand direction',2)
   triplet(c.get('normal_world'),'hand normal',2)
  if c['space']=='POSE_RELATIVE_BONE_HEAD_HAND':
   if c.get('target_actor') not in ('A','B') or not isinstance(c.get('target_bone'),str):raise ValueError('Relative target missing')
  if c['space']=='POSE_LOCAL_REST_AXIS_ROT_X_DEG':
   if type(c.get('angle_deg')) not in (float,int) or not -180<=c['angle_deg']<=180:raise ValueError('Invalid rest-axis angle')
 if not rt.get('floor_calibration') or not rt.get('support_assertions') or not rt.get('posture_assertions'):
  raise ValueError('v2 requires floor_calibration, support_assertions and posture_assertions')
 for st in rt['floor_calibration']:
  if st.get('actor') not in ('A','B') or st.get('region') not in ('hands','feet','knees') or not isinstance(st.get('adjust_bone'),str):
   raise ValueError('Invalid floor-calibration stage')
  if st.get('side') not in ('L','R',None):raise ValueError('Invalid floor-calibration side')
  if not 0<float(st.get('max_total_shift_m',.22))<=.40:raise ValueError('Floor shift limit exceeded')
 for s in rt['support_assertions']:
  if s.get('actor') not in ('A','B') or s.get('region') not in ('hands','feet','knees') or s.get('side') not in ('L','R',None):
   raise ValueError('Invalid support assertion')
 for s in rt['posture_assertions']:
  if s.get('actor') not in ('A','B') or s.get('kind') not in ('kneeling','quadruped','standing','forward_fold_standing'):
   raise ValueError('Invalid posture assertion')
 if {s['actor'] for s in rt['posture_assertions']} != {'A','B'}:raise ValueError('Posture contract requires both actors')
 # Every declared support must have a calibration path.
 cal={(s['actor'],s['region'],s.get('side')) for s in rt['floor_calibration']}
 for st in rt['support_assertions']:
  if (st['actor'],st['region'],st.get('side')) not in cal:
   raise ValueError('Support has no corresponding floor calibration stage')
 if validate_dependencies:
  project,src,row=source_and_row(manifest['pose_id'])
  pair=read_json(ROOT/project['default_pair']['config'])
  dep=manifest.get('dependencies',{})
  req={'source_id':src['source_id'],'source_checkpoint':src['checkpoint'],'source_row_sha256':sha_bytes(row['specification'].encode('utf-8')),
      'pair_id':pair['pair_id'],'pair_version':pair['version'],'template_sha256':sha_file(ROOT/project['default_pair']['config'].replace('pair.json','template.blend')),
      'rig_map_id':'RIG001','rig_map_version':'v001'}
  for k,v in req.items():
   if dep.get(k)!=v:raise ValueError(f'Package dependency mismatch for {k}: expected {v}')
  if row['variation_code']!='V00':raise ValueError('Remote starting scope is V00 only; other variations require an explicit workflow revision')
  if row['generation_gate']=='EXCLUDE':raise ValueError('Source record has EXCLUDE gate')
 return manifest,data

def artifact_hashes(folder):
 root=Path(folder)
 return {p.relative_to(root).as_posix():sha_file(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='checksums.json'}
