"""Report five pose-package contracts as reference notes. No geometry or posture gates."""
from __future__ import annotations
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,load_package,read_json

def check():
    plan=read_json(ROOT/'batches/BATCH-001.json')
    records=[]
    for entry in plan['poses']:
        pid=entry['pose_id'];f=ROOT/'incoming'/entry['package']
        try:
            m,d=load_package(f)
            rt=d['rig-targets.json']
            records.append({'pose_id':pid,'package':f.name,'available':True,
                            'engine':rt.get('engine'),'controls':len(rt.get('controls',[])),
                            'postures':{x['actor']:x['kind'] for x in rt.get('posture_assertions',[])},
                            'source_gate':'metadata_only','status':'available_for_batch'})
        except Exception as e:
            records.append({'pose_id':pid,'package':f.name,'available':False,'error':str(e),
                            'status':'input_error_record_and_continue'})
    return {'batch_id':plan['batch_id'],'count':len(records),'data_only':True,
            'quality_gates':False,'continue_after_failure':True,'records':records}
if __name__=='__main__':
    print(json.dumps(check(),indent=2))
