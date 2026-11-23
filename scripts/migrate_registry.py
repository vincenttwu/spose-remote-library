"""One-time, idempotent registry schema migration and honest legacy snapshot import.

Creates registry_* tables IN EXISTING tracking/progress.sqlite only; never
relabels pose history or invents missing Pass-01 results. Makes an online SQLite
backup before schema migration. Can be rerun to discover new snapshots.
"""
from __future__ import annotations
import argparse, datetime, json, sqlite3
from pathlib import Path
from registry import ROOT,connect,initialize,tables_exist,register_plan,ingest_snapshot,export_dict


def snapshot_folders(root):
    return sorted(p for p in (root/'snapshots').glob('batch-*-pass-*') if p.is_dir() and (p/'batch-summary.json').is_file())


def migrate(root=ROOT,execute=False):
    root=Path(root).resolve();db=root/'tracking/progress.sqlite'
    if not db.is_file():raise FileNotFoundError(db)
    with connect(root) as c:
        existing=tables_exist(c)
    plans=sorted((root/'batches').glob('*.json'))
    snaps=snapshot_folders(root)
    report={'schema_already_exists':existing,'legacy_plan_files':len(plans),'legacy_snapshot_folders':len(snaps),
            'method':'migrate_existing_tracker_no_pose_revision_rewrites','execute':execute}
    if not execute:return report
    if not existing:
        folder=root/'history'/'registry-migration-backups';folder.mkdir(parents=True,exist_ok=True)
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup=folder/f'progress-before-registry_{stamp}.sqlite'
        # sqlite3.backup includes WAL and is safe for an idle local writer; live imports
        # should be paused before migration per APPLY.md.
        with sqlite3.connect(db,timeout=30) as source, sqlite3.connect(backup) as target:
            source.backup(target)
        report['pre_migration_backup']=str(backup)
    # CREATE IF NOT EXISTS also repairs an interrupted partial migration on rerun.
    with connect(root) as c:initialize(c)
    good=[];warnings=[]
    for plan in plans:
        try:good.append({'kind':'plan',**register_plan(root,plan)})
        except Exception as exc:warnings.append({'source':plan.relative_to(root).as_posix(),'reason':f'{type(exc).__name__}: {exc}'})
    for snap in snaps:
        try:good.append({'kind':'snapshot',**ingest_snapshot(root,snap)})
        except Exception as exc:warnings.append({'source':snap.relative_to(root).as_posix(),'reason':f'{type(exc).__name__}: {exc}'})
    doc=export_dict(root)
    report.update({'registered_batches':len(doc['batches']),'registered_passes':len(doc['passes']),
                   'registered_runs':len(doc['runs']),'results':good,'warnings':warnings,
                   'notes':['Only present snapshots are migrated; missing earlier runs are not invented.',
                            'No pose revisions, Blender files, source rows, or prior tracking jobs/events are modified.']})
    return report


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--root',type=Path,default=ROOT);pa.add_argument('--apply',action='store_true')
    args=pa.parse_args(); print(json.dumps(migrate(args.root,args.apply),indent=2,ensure_ascii=False))
if __name__=='__main__':main()
