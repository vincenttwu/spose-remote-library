"""Offline Batch 001 v2 contract smoke test. Does NOT run Blender.

Usage: python scripts/check_batch_001.py (from inside installed SPOSE library)
Verifies all five current DOGG-family packages, both actor postures, and core supports.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,load_package

FILES={
  'DOGG-DOGG-V00':'DOGG-DOGG-V00_20261123T091501Z.zip',
  'DOGG-CLSD-V00':'DOGG-CLSD-V00_20261123T091502Z.zip',
  'DOGG-DOWN-V00':'DOGG-DOWN-V00_20261123T091503Z.zip',
  'DOGG-FCDN-V00':'DOGG-FCDN-V00_20261123T100501Z.zip',
  'DOGG-FROG-V00':'DOGG-FROG-V00_20261123T100502Z.zip',
}
EXPECTED={
  'DOGG-DOGG-V00':{'A':'kneeling','B':'quadruped'},
  'DOGG-CLSD-V00':{'A':'kneeling','B':'quadruped'},
  'DOGG-DOWN-V00':{'A':'standing','B':'forward_fold_standing'},
  'DOGG-FCDN-V00':{'A':'kneeling','B':'quadruped'},
  'DOGG-FROG-V00':{'A':'kneeling','B':'quadruped'},
}

def check():
  details=[]
  for pid,name in FILES.items():
    manifest,payload=load_package(ROOT/'incoming'/name)
    rt=payload['rig-targets.json']
    postures={p['actor']:p['kind'] for p in rt['posture_assertions']}
    if postures!=EXPECTED[pid]:
      raise ValueError(f'{pid} has wrong fundamental posture assertions: {postures}')
    supports={(p['actor'],p['region'],p['side']) for p in rt['support_assertions']}
    if pid=='DOGG-DOWN-V00':
      required={( 'B','hands','L'),('B','hands','R'),('B','feet','L'),('B','feet','R'),('A','feet','L'),('A','feet','R')}
    elif pid=='DOGG-FROG-V00':
      required={( 'A','knees','L'),('A','knees','R'),('B','hands','L'),('B','hands','R'),('B','feet','L'),('B','feet','R')}
    else:
      required={( 'B','hands','L'),('B','hands','R'),('A','knees','L'),('A','knees','R'),('B','knees','L'),('B','knees','R')}
    if not required.issubset(supports):
      raise ValueError(f'{pid} is missing bilateral support assertions: {sorted(required-supports)}')
    details.append({'pose_id':pid,'controls':len(rt['controls']),'supports':len(rt['support_assertions']),
                    'postures':postures,'source_checkpoint':manifest['dependencies']['source_checkpoint'],
                    'geometry_engine':'rigify_floor_v2'})
  return {'ok':True,'scope':'OFFLINE_CONTRACT_ONLY','blender_executed':False,'poses':details}

if __name__=='__main__':
  try:print(json.dumps(check(),indent=2))
  except Exception as e:
    print('BATCH 001 CONTRACT CHECK FAILED: '+str(e),file=sys.stderr)
    sys.exit(1)
