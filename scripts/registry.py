"""SPOSE Infra 0002 registry: independent batch/pass/attempt/artifact inventory.

Only metadata is written to existing tracking/progress.sqlite; source, jobs,
pose revisions and Blender files are never mutated. Quality is descriptive.
All writes use BEGIN IMMEDIATE, foreign keys and idempotent identities.

CLI (inside library):
  python scripts/registry.py status
  python scripts/registry.py next
  python scripts/registry.py show --batch 0001
  python scripts/registry.py register-plan --plan batches/BATCH-001.json
  python scripts/registry.py ingest-snapshot --snapshot snapshots/<folder>
  python scripts/registry.py set-quality --batch 0001 --pass 05 --score 6.2 --notes "..."
  python scripts/registry.py export --output tracking/registry.json
"""
from __future__ import annotations
import argparse, contextlib, datetime, hashlib, json, re, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BATCH_RE=re.compile(r'^(?:batch[-_])?(\d{1,6})$',re.I)
PASS_RE=re.compile(r'^(?:pass[-_])?(\d{1,3}|legacy)$',re.I)


def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def normalize_batch(s):
    m=BATCH_RE.fullmatch(str(s).strip())
    if not m:raise ValueError('Invalid batch label: '+str(s))
    return f'batch-{int(m.group(1)):04d}'

def normalize_pass(s):
    m=PASS_RE.fullmatch(str(s).strip())
    if not m:raise ValueError('Invalid pass label: '+str(s))
    if m.group(1).lower()=='legacy':return 'pass-legacy'
    return f'pass-{int(m.group(1)):02d}'

def safe_relative(root, p, base=None):
    root=Path(root).resolve();p=Path(p)
    p=(p if p.is_absolute() else root/p).resolve()
    if not p.is_relative_to((root/base).resolve() if base else root):
        raise ValueError('Path outside approved library directory: '+str(p))
    return p.relative_to(root).as_posix()

def tables_exist(c):return c.execute("SELECT 1 FROM sqlite_master WHERE name='registry_batches'").fetchone() is not None

def connect(root=ROOT):
    db=Path(root)/'tracking/progress.sqlite'
    if not db.is_file():raise FileNotFoundError('Existing tracking/progress.sqlite required; do not create a second tracker')
    c=sqlite3.connect(db,timeout=30)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA busy_timeout=30000'); c.execute('PRAGMA foreign_keys=ON')
    return c

def initialize(c):
    c.executescript('''
CREATE TABLE IF NOT EXISTS registry_batches(
  batch_id TEXT PRIMARY KEY, family TEXT, pose_ids_json TEXT NOT NULL,
  plan_path TEXT, created_utc TEXT NOT NULL, updated_utc TEXT NOT NULL,
  notes_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS registry_passes(
  batch_id TEXT NOT NULL REFERENCES registry_batches(batch_id),
  pass_id TEXT NOT NULL, plan_sha256 TEXT, plan_path TEXT,
  calibration_enabled INTEGER, max_refinements INTEGER,
  status TEXT NOT NULL DEFAULT 'registered', visual_score REAL,
  score_notes TEXT, updated_utc TEXT NOT NULL,
  PRIMARY KEY(batch_id,pass_id));
CREATE TABLE IF NOT EXISTS registry_runs(
  run_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL,
  pass_id TEXT NOT NULL, snapshot_path TEXT NOT NULL UNIQUE,
  summary_sha256 TEXT NOT NULL, run_utc TEXT, imported_utc TEXT NOT NULL,
  result_count INTEGER, new_revision_count INTEGER, reused_revision_count INTEGER,
  FOREIGN KEY(batch_id,pass_id) REFERENCES registry_passes(batch_id,pass_id));
CREATE TABLE IF NOT EXISTS registry_attempts(
  run_id TEXT NOT NULL REFERENCES registry_runs(run_id),
  pose_id TEXT NOT NULL, attempt_no INTEGER NOT NULL,
  selected INTEGER NOT NULL DEFAULT 0, status TEXT,
  evidence_path TEXT, score REAL, PRIMARY KEY(run_id,pose_id,attempt_no));
CREATE TABLE IF NOT EXISTS registry_artifacts(
  artifact_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL, pass_id TEXT NOT NULL,
  run_id TEXT, role TEXT NOT NULL, relative_path TEXT NOT NULL,
  sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, recorded_utc TEXT NOT NULL,
  FOREIGN KEY(batch_id,pass_id) REFERENCES registry_passes(batch_id,pass_id));
CREATE TABLE IF NOT EXISTS registry_events(
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  occurred_utc TEXT NOT NULL, kind TEXT NOT NULL, batch_id TEXT, pass_id TEXT,
  detail_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_registry_artifacts_batch ON registry_artifacts(batch_id,pass_id);
CREATE INDEX IF NOT EXISTS ix_registry_runs_batch ON registry_runs(batch_id,pass_id);
''')

def event(c,kind,batch=None,pas=None,details=None):
    c.execute('INSERT INTO registry_events(occurred_utc,kind,batch_id,pass_id,detail_json) VALUES(?,?,?,?,?)',
              (utc(),kind,batch,pas,json.dumps(details or {},sort_keys=True)))

def register_plan(root,plan,c=None):
    root=Path(root).resolve();own=c is None
    if own:c=connect(root)
    p=root/plan if not Path(plan).is_absolute() else Path(plan)
    rel=safe_relative(root,p,'batches')
    doc=read(p);b=normalize_batch(doc.get('batch_label') or doc.get('batch_id',''))
    pa=normalize_pass(doc.get('pass_label','pass-legacy'))
    entries=doc.get('poses',[])
    ids=[x['pose_id'] for x in entries if isinstance(x,dict) and isinstance(x.get('pose_id'),str)]
    if not ids or len(set(ids))!=len(ids):raise ValueError('Plan requires distinct pose IDs')
    if any('/' in x or '\\' in x or '..' in x or Path(x).name!=x for x in ids):raise ValueError('Unsafe pose ID in plan')
    fam=doc.get('family') or ids[0].split('-',1)[0]
    now=utc();ph=sha(p.read_bytes());cfg=doc.get('local_calibration',{})
    try:
        if own:c.execute('BEGIN IMMEDIATE')
        existing=c.execute('SELECT pose_ids_json FROM registry_batches WHERE batch_id=?',(b,)).fetchone()
        if existing and json.loads(existing['pose_ids_json'])!=ids:
            raise ValueError('Batch identity already has different pose IDs; create a new batch ID')
        c.execute('INSERT INTO registry_batches(batch_id,family,pose_ids_json,plan_path,created_utc,updated_utc) VALUES(?,?,?,?,?,?) ON CONFLICT(batch_id) DO UPDATE SET updated_utc=excluded.updated_utc,plan_path=excluded.plan_path',
                  (b,fam,json.dumps(ids),rel,now,now))
        prev=c.execute('SELECT plan_sha256 FROM registry_passes WHERE batch_id=? AND pass_id=?',(b,pa)).fetchone()
        c.execute('''INSERT INTO registry_passes(batch_id,pass_id,plan_sha256,plan_path,calibration_enabled,max_refinements,status,updated_utc)
            VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(batch_id,pass_id) DO UPDATE SET
            plan_sha256=excluded.plan_sha256,plan_path=excluded.plan_path,
            calibration_enabled=excluded.calibration_enabled,max_refinements=excluded.max_refinements,updated_utc=excluded.updated_utc''',
                  (b,pa,ph,rel,1 if cfg.get('enabled') else 0,min(2,max(0,int(cfg.get('max_refinement_attempts',0)))), 'registered',now))
        if not prev or prev['plan_sha256']!=ph:event(c,'plan_registered',b,pa,{'path':rel,'sha256':ph,'pose_count':len(ids)})
        if own:c.commit()
        return {'batch_id':b,'pass_id':pa,'plan_path':rel,'pose_count':len(ids),'plan_sha256':ph}
    except Exception:
        if own:c.rollback()
        raise
    finally:
        if own:c.close()

def ensure_batch_for_snapshot(c,root,summary):
    b=normalize_batch(summary['batch_label']);pa=normalize_pass(summary['pass_label'])
    ids=[x.get('pose_id') for x in summary['results']]
    if not ids or any(not isinstance(x,str) or not x for x in ids) or len(ids)!=len(set(ids)):raise ValueError('Invalid snapshot pose results')
    if any('/' in x or '\\' in x or '..' in x or Path(x).name!=x for x in ids):raise ValueError('Unsafe pose ID in snapshot')
    existing=c.execute('SELECT pose_ids_json FROM registry_batches WHERE batch_id=?',(b,)).fetchone()
    if existing and json.loads(existing['pose_ids_json'])!=ids:
        raise ValueError('Snapshot pose list conflicts with registered batch identity')
    now=utc()
    c.execute('INSERT OR IGNORE INTO registry_batches(batch_id,family,pose_ids_json,created_utc,updated_utc,notes_json) VALUES(?,?,?,?,?,?)',
              (b,ids[0].split('-')[0],json.dumps(ids),now,now,json.dumps({'migrated_from':'snapshot'})))
    c.execute("INSERT OR IGNORE INTO registry_passes(batch_id,pass_id,status,updated_utc) VALUES(?,?,?,?)",(b,pa,'observed',now))
    return b,pa

def add_artifact(c,root,b,pa,run,role,file):
    root=Path(root).resolve();rel=safe_relative(root,file)
    p=root/rel
    if not p.is_file() or p.is_symlink():raise FileNotFoundError('Artifact must be existing regular file: '+str(p))
    data=p.read_bytes();fingerprint=sha(data)
    aid=sha((b+'|'+pa+'|'+role+'|'+rel+'|'+fingerprint).encode('utf-8'))
    c.execute('INSERT OR IGNORE INTO registry_artifacts VALUES(?,?,?,?,?,?,?,?,?)',
              (aid,b,pa,run,role,rel,fingerprint,len(data),utc()))
    return {'artifact_id':aid,'path':rel,'sha256':fingerprint,'bytes':len(data)}

def ingest_snapshot(root,snapshot):
    root=Path(root).resolve();rel=safe_relative(root,snapshot,'snapshots');p=root/rel
    summary_path=p/'batch-summary.json'
    doc=read(summary_path)
    for key in ('batch_label','pass_label','results'):
        if key not in doc:raise ValueError('Snapshot missing '+key)
    digest=sha(summary_path.read_bytes());run_id=sha(rel.encode('utf-8'))[:24]
    with contextlib.closing(connect(root)) as c:
        c.execute('BEGIN IMMEDIATE')
        try:
            b,pa=ensure_batch_for_snapshot(c,root,doc)
            old=c.execute('SELECT summary_sha256 FROM registry_runs WHERE run_id=?',(run_id,)).fetchone()
            if old and old['summary_sha256']!=digest:
                # Snapshot summary may gain export metadata after initial capture;
                # record latest hash and event, never discard earlier artifacts.
                c.execute('UPDATE registry_runs SET summary_sha256=? WHERE run_id=?',(digest,run_id))
                event(c,'snapshot_summary_refreshed',b,pa,{'snapshot':rel,'sha256':digest})
            elif not old:
                c.execute('''INSERT INTO registry_runs(run_id,batch_id,pass_id,snapshot_path,summary_sha256,run_utc,imported_utc,result_count,new_revision_count,reused_revision_count)
                      VALUES(?,?,?,?,?,?,?,?,?,?)''',(run_id,b,pa,rel,digest,doc.get('run_utc'),utc(),len(doc['results']),
                      doc.get('new_revision_count'),doc.get('reused_revision_count')))
                event(c,'snapshot_registered',b,pa,{'snapshot':rel,'run_id':run_id})
            c.execute('UPDATE registry_passes SET status=?,updated_utc=? WHERE batch_id=? AND pass_id=?',('results_recorded',utc(),b,pa))
            artifact=add_artifact(c,root,b,pa,run_id,'batch_summary',summary_path)
            lm=p/'local-refinement-evidence.json'
            if lm.is_file():
                loc=read(lm)
                for pose,selected in loc.get('pose_selections',{}).items():
                    for attempt in selected.get('attempts',[]):
                        num=int(attempt['attempt'])
                        if not 0<=num<=2:raise ValueError('Invalid local attempt in snapshot')
                        path=f'{rel}/local-evidence/{pose}/attempt-{num:02d}'
                        c.execute('''INSERT INTO registry_attempts VALUES(?,?,?,?,?,?,?)
                            ON CONFLICT(run_id,pose_id,attempt_no) DO UPDATE SET selected=excluded.selected,status=excluded.status,
                            evidence_path=excluded.evidence_path,score=excluded.score''',
                            (run_id,pose,num,1 if num==selected.get('selected_attempt') else 0,
                             attempt.get('status'),path,selected.get('local_visual_score_out_of_10') if num==selected.get('selected_attempt') else None))
                add_artifact(c,root,b,pa,run_id,'local_evidence',lm)
            feedbacks=sorted(p.glob('spose-remote-feedback-*.zip'))
            for fb in feedbacks:add_artifact(c,root,b,pa,run_id,'feedback_zip',fb)
            c.commit()
            return {'batch_id':b,'pass_id':pa,'run_id':run_id,'snapshot':rel,'results':len(doc['results']),
                    'feedback_archives':len(feedbacks),'summary_artifact':artifact}
        except Exception:c.rollback();raise

def record_artifact(root,batch,pas,file,role='bundle_zip',snapshot=None):
    root=Path(root).resolve();b=normalize_batch(batch);pa=normalize_pass(pas)
    with contextlib.closing(connect(root)) as c:
        c.execute('BEGIN IMMEDIATE')
        try:
            if not c.execute('SELECT 1 FROM registry_passes WHERE batch_id=? AND pass_id=?',(b,pa)).fetchone():
                raise ValueError('Register batch/pass first')
            run_id=None
            if snapshot:
                s=safe_relative(root,snapshot,'snapshots')
                row=c.execute('SELECT run_id FROM registry_runs WHERE snapshot_path=?',(s,)).fetchone()
                if not row:raise ValueError('Ingest snapshot first: '+s)
                run_id=row['run_id']
            item=add_artifact(c,root,b,pa,run_id,role,file)
            event(c,'artifact_recorded',b,pa,item)
            c.commit();return item
        except Exception:c.rollback();raise

def set_quality(root,batch,pas,score,notes):
    b=normalize_batch(batch);pa=normalize_pass(pas)
    if score is not None and not 0<=score<=10:raise ValueError('Score must be between 0 and 10')
    with contextlib.closing(connect(root)) as c:
        c.execute('BEGIN IMMEDIATE')
        try:
            cur=c.execute('UPDATE registry_passes SET visual_score=?,score_notes=?,updated_utc=? WHERE batch_id=? AND pass_id=?',
                          (score,notes,utc(),b,pa))
            if not cur.rowcount:raise ValueError('Batch/pass not found')
            event(c,'quality_noted',b,pa,{'score':score,'notes':notes})
            c.commit();return {'batch_id':b,'pass_id':pa,'score':score,'notes':notes}
        except Exception:c.rollback();raise

def export_dict(root=ROOT):
    root=Path(root).resolve()
    with contextlib.closing(connect(root)) as c:
        if not tables_exist(c):return {'schema_version':1,'kind':'spose_batch_registry','migration_required':True,'batches':[],'passes':[],'runs':[],'attempts':[],'artifacts':[],'events':[]}
        def rows(sql):return [dict(x) for x in c.execute(sql)]
        b=rows('SELECT * FROM registry_batches ORDER BY batch_id')
        for r in b:r['pose_ids']=json.loads(r.pop('pose_ids_json'));r['notes']=json.loads(r.pop('notes_json'))
        return {'schema_version':1,'kind':'spose_batch_registry',
                'batches':b,'passes':rows('SELECT * FROM registry_passes ORDER BY batch_id,pass_id'),
                'runs':rows('SELECT * FROM registry_runs ORDER BY batch_id,pass_id,run_utc'),
                'attempts':rows('SELECT * FROM registry_attempts ORDER BY run_id,pose_id,attempt_no'),
                'artifacts':rows('SELECT * FROM registry_artifacts ORDER BY batch_id,pass_id,recorded_utc'),
                'events':rows('SELECT * FROM registry_events ORDER BY event_id DESC LIMIT 500')}

def status(root=ROOT):
    x=export_dict(root)
    latest={(p['batch_id'],p['pass_id']):p for p in x['passes']}
    runs={}
    for r in x['runs']:runs[(r['batch_id'],r['pass_id'])]=runs.get((r['batch_id'],r['pass_id']),0)+1
    return {'registered_batches':len(x['batches']),'registered_passes':len(x['passes']),'recorded_runs':len(x['runs']),
      'batches':[{'batch_id':b['batch_id'],'family':b['family'],'pose_count':len(b['pose_ids']),
                  'passes':[{'pass_id':p['pass_id'],'status':p['status'],'runs':runs.get((p['batch_id'],p['pass_id']),0),
                             'visual_score':p['visual_score']} for p in x['passes'] if p['batch_id']==b['batch_id']]} for b in x['batches']]}

def next_actions(root=ROOT):
    x=export_dict(root);out=[]
    for p in x['passes']:
        has_run=any(r['batch_id']==p['batch_id'] and r['pass_id']==p['pass_id'] for r in x['runs'])
        action='run_or_collect_feedback' if not has_run else ('audit_and_record_quality' if p['visual_score'] is None else 'decide_next_pass_or_continue')
        out.append({'batch_id':p['batch_id'],'pass_id':p['pass_id'],'suggested_action':action,'advisory':True})
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=ROOT)
    sub=ap.add_subparsers(dest='cmd',required=True)
    for n in ['status','next','export']:sub.add_parser(n)
    show=sub.add_parser('show');show.add_argument('--batch',required=True)
    rg=sub.add_parser('register-plan');rg.add_argument('--plan',required=True)
    ing=sub.add_parser('ingest-snapshot');ing.add_argument('--snapshot',required=True)
    ar=sub.add_parser('add-artifact');ar.add_argument('--batch',required=True);ar.add_argument('--pass',dest='pas',required=True);ar.add_argument('--file',required=True);ar.add_argument('--role',default='bundle_zip');ar.add_argument('--snapshot')
    q=sub.add_parser('set-quality');q.add_argument('--batch',required=True);q.add_argument('--pass',dest='pas',required=True);q.add_argument('--score',type=float,required=True);q.add_argument('--notes',default='')
    sub.choices['export'].add_argument('--output')
    args=ap.parse_args();root=args.root
    if args.cmd=='status':out=status(root)
    elif args.cmd=='next':out=next_actions(root)
    elif args.cmd=='show':
        x=export_dict(root);b=normalize_batch(args.batch)
        out={k:([y for y in v if y.get('batch_id')==b] if isinstance(v,list) else v) for k,v in x.items()}
    elif args.cmd=='register-plan':out=register_plan(root,args.plan)
    elif args.cmd=='ingest-snapshot':out=ingest_snapshot(root,args.snapshot)
    elif args.cmd=='add-artifact':out=record_artifact(root,args.batch,args.pas,args.file,args.role,args.snapshot)
    elif args.cmd=='set-quality':out=set_quality(root,args.batch,args.pas,args.score,args.notes)
    else:
        out=export_dict(root);path=Path(args.output) if args.output else root/'tracking/registry.json'
        if not path.is_absolute():path=root/path
        if not path.resolve().is_relative_to((root/'tracking').resolve()):raise ValueError('Registry export must stay inside tracking/')
        write(path,out);out={'written':str(path),'batch_count':len(out['batches']),'pass_count':len(out['passes'])}
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
