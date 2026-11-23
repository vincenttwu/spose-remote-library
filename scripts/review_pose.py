"""Record a *human* review decision for an existing remote Blender pose revision.

This is never called by the importer. `accepted` is a user's explicit judgment,
not automatic technical validation. It does not approve shared character assets
or enable production / variation stages.

Examples:
  python scripts/review_pose.py DOGG-DOGG-V00 --revision 1 --decision accepted --reviewer user --note "Viewed all QA renders" --confirm-reviewed
  python scripts/review_pose.py DOGG-DOGG-V00 --revision 1 --decision blocked --reviewer user --note "Hands miss target" --confirm-reviewed
"""
from __future__ import annotations
import argparse,datetime,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json,save_json,sha_bytes,artifact_hashes,source_and_row
from update_tracking import export_snapshots


def record_review(pose_id,revision,decision,reviewer,note,confirm=False,ack_source_review=False):
    if not confirm:raise ValueError('Require explicit --confirm-reviewed; never auto-accept')
    if not note or len(note.strip())<8:raise ValueError('Require meaningful --note with review evidence/reason')
    project,src,row=source_and_row(pose_id)
    # Source gates and variation phase are descriptive: manual review is optional.
    pair=read_json(ROOT/project['default_pair']['config'])
    path=ROOT/'poses'/pose_id/pair['pair_id']/pair['version']/f'r{revision:03d}'
    if not path.is_dir():raise FileNotFoundError('Revision directory does not exist: '+str(path))
    metadata=read_json(path/'pose.json')
    if metadata.get('pose_id')!=pose_id or metadata.get('revision')!=revision:
        raise ValueError('Pose revision metadata mismatch')
    if metadata.get('source_row_sha256')!=sha_bytes(row['specification'].encode('utf-8')):
        raise ValueError('Source row hash mismatch; revalidate from current source')
    validation=read_json(path/'validation.json')
    # Geometry diagnostics are advisory. Human judgment may record any state.
    tracker=ROOT/project['tracker']
    ts=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with sqlite3.connect(tracker) as db:
        db.row_factory=sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        job=db.execute('SELECT * FROM jobs WHERE pose_id=? AND pair_id=? AND pair_version=? AND revision=?',
                (pose_id,pair['pair_id'],pair['version'],revision)).fetchone()
        if job is None:raise ValueError('Revision not registered in tracker')
        if job['source_checkpoint']!=src['checkpoint'] or job['source_row_sha256']!=metadata['source_row_sha256']:
            raise ValueError('Tracker source does not match current registration')
        # Historical failed/blocked revisions remain registered and may be reviewed.
        db.execute('UPDATE jobs SET status=?, updated_at=? WHERE pose_id=? AND pair_id=? AND pair_version=? AND revision=?',
                   (decision,ts,pose_id,pair['pair_id'],pair['version'],revision))
        detail={'decision':decision,'reviewer':reviewer,'note':note,'confirmed':True,
                'source_review_acknowledged':ack_source_review}
        db.execute('INSERT INTO events(occurred_at,pose_id,pair_id,pair_version,revision,event_type,details_json) VALUES (?,?,?,?,?,?,?)',
            (ts,pose_id,pair['pair_id'],pair['version'],revision,'manual_pose_review',json.dumps(detail,ensure_ascii=False)))
        db.commit()
    # DB is the authority; these files are post-commit derived artifacts.
    save_json(path/'review.json',{'schema_version':1,'reviewed_at':ts,**detail})
    metadata['status']=decision
    metadata['accepted_at']=ts if decision=='accepted' else None
    save_json(path/'pose.json',metadata)
    # Human review must not leave the generated validation report claiming
    # 'user_accepted: false' after the user actually approved this revision.
    # Technical measurements remain unchanged.
    validation['user_accepted']=(decision=='accepted')
    validation['status']={
        'validated':'HUMAN_REVIEWED_NOT_ACCEPTED',
        'accepted':'HUMAN_ACCEPTED',
        'blocked':'HUMAN_BLOCKED',
    }[decision]
    validation['last_human_review_at']=ts
    save_json(path/'validation.json',validation)
    save_json(path/'checksums.json',artifact_hashes(path))
    export_snapshots()
    return {'pose_id':pose_id,'revision':revision,'decision':decision,'reviewer':reviewer,
            'note':note,'roadmap':'ROADMAP.md/ROADMAP.json refreshed'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pose_id');p.add_argument('--revision',type=int,required=True)
    p.add_argument('--decision',required=True,choices=['validated','accepted','blocked'])
    p.add_argument('--reviewer',required=True)
    p.add_argument('--note',required=True)
    p.add_argument('--confirm-reviewed',action='store_true')
    p.add_argument('--acknowledge-source-review',action='store_true',help='Legacy compatibility; not required')
    a=p.parse_args()
    print(json.dumps(record_review(a.pose_id,a.revision,a.decision,a.reviewer,a.note,
                  a.confirm_reviewed,a.acknowledge_source_review),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
