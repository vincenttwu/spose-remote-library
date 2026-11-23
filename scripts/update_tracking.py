"""Transactionally record one remote pose revision and export status snapshots."""
from pathlib import Path
import sqlite3,json,datetime,csv,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT

def record_job(pose_id,pair_id,pair_version,revision,status,checkpoint,rowhash,gate,templatehash,out,issues):
 assert status in {'queued','working','draft','validated','accepted','blocked','failed','excluded'}
 ts=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=ROOT/'tracking'/'progress.sqlite';con=sqlite3.connect(p)
 try:
  con.execute('BEGIN IMMEDIATE')
  con.execute('INSERT INTO jobs (pose_id,pair_id,pair_version,revision,status,source_checkpoint,source_row_sha256,source_gate,template_sha256,output_directory,issues_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
   (pose_id,pair_id,pair_version,revision,status,checkpoint,rowhash,gate,templatehash,str(out),json.dumps(issues,ensure_ascii=False),ts,ts))
  con.execute('INSERT INTO events(occurred_at,pose_id,pair_id,pair_version,revision,event_type,details_json) VALUES (?,?,?,?,?,?,?)',
   (ts,pose_id,pair_id,pair_version,revision,'remote_pose_imported',json.dumps({'status':status,'output_directory':str(out),'issues':issues},ensure_ascii=False)))
  con.commit()
 except:con.rollback();raise
 finally:con.close()

def export_snapshots():
 con=sqlite3.connect(ROOT/'tracking'/'progress.sqlite'); con.row_factory=sqlite3.Row
 try:
  cols=[r[1] for r in con.execute('PRAGMA table_info(jobs)')]
  path=ROOT/'tracking'/'progress.csv';temp=path.with_suffix('.csv.tmp')
  with temp.open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows([dict(r) for r in con.execute('SELECT * FROM jobs ORDER BY pose_id,revision')])
  temp.replace(path)
  path=ROOT/'tracking'/'events.jsonl';temp=path.with_suffix('.jsonl.tmp')
  with temp.open('w',encoding='utf-8') as f:
   for row in con.execute('SELECT * FROM events ORDER BY event_id'):
    obj=dict(row);obj['details']=json.loads(obj.pop('details_json'))
    f.write(json.dumps(obj,ensure_ascii=False)+'\n')
  temp.replace(path)
 finally:con.close()
 # The roadmap is a deterministic derived view of the committed tracker.
 # A failed regeneration must be surfaced to the caller and can be retried safely.
 from update_roadmap import save_roadmap
 save_roadmap()
