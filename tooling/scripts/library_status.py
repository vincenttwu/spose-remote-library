"""Read library status; --export refreshes only the derived tracking exports."""
from pathlib import Path
import argparse, csv, hashlib, json, sqlite3

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    project=json.loads((root/'project.json').read_text(encoding='utf-8'))
    source_config=root/project['source_config']
    source=json.loads(source_config.read_text(encoding='utf-8'))
    pair_config=root/project['default_pair']['config']
    pair=json.loads(pair_config.read_text(encoding='utf-8'))
    profile_ref=pair['shared_body_profile']
    profile_dir=root/'body_profiles'/profile_ref['profile_id']/profile_ref['version']
    profile=json.loads((profile_dir/'profile.json').read_text(encoding='utf-8'))
    source_root=Path(source['root'])
    if not source_root.is_absolute():
        assert source.get('root_relative_to')=='config_file', 'Relative source root needs an explicit anchor'
        source_root=(source_config.parent/source_root).resolve()
    catalog=source_root/source['canonical_catalog']
    actual=hashlib.sha256(catalog.read_bytes()).hexdigest()
    assert actual==source['catalog_sha256'], 'Source catalog changed; stop and reconcile'
    db=sqlite3.connect((root/'tracking/progress.sqlite').as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    jobs=[dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY pose_id,pair_id,pair_version,revision')]
    counts=dict(db.execute('SELECT status,COUNT(*) FROM jobs GROUP BY status').fetchall())
    print(json.dumps({'phase':project['phase'],'default_pair':project['default_pair'],
        'production_enabled':project['production_enabled'],'source_catalog_hash_matches':True,
        'source_id':source.get('source_id'),'source_checkpoint':source['checkpoint'],
        'source_records':source['records'],'source_catalog':str(catalog),
        'job_count':len(jobs),'counts':counts,
        'master_exists':(profile_dir/profile['master_file']).is_file(),
        'pair_template_exists':(pair_config.parent/pair['template_file']).is_file(),
        'profile_status':profile['status'],'pair_status':pair['status'],
        'user_approved':bool(profile['approved_at'] and pair['approved_at']),
        'master_height_measured_m':profile['master_height_measured_m']},indent=2))
    if args.export:
        columns=[r[1] for r in db.execute('PRAGMA table_info(jobs)')]
        target=root/'tracking/progress.csv'
        temporary=target.with_suffix('.csv.tmp')
        with temporary.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(jobs)
        temporary.replace(target)
        target=root/'tracking/events.jsonl'
        temporary=target.with_suffix('.jsonl.tmp')
        with temporary.open('w',encoding='utf-8') as f:
            for row in db.execute('SELECT * FROM events ORDER BY event_id'):
                event=dict(row);event['details']=json.loads(event.pop('details_json'))
                f.write(json.dumps(event,ensure_ascii=False)+'\n')
        temporary.replace(target)
    db.close()

if __name__=='__main__':
    main()
