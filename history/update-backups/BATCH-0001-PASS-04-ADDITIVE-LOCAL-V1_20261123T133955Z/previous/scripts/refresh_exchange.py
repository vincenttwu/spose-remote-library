"""Regenerate disposable flat review/ and upload/ from immutable pose revisions.

No Blender call, no import and no state acceptance. Uses latest batch snapshot
unless --snapshot is specified. Generates one fully-contained compressed
feedback ZIP under upload/. Historical copy stays under snapshots/.
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json
from feedback_bundle import create_feedback, timestamp
from update_continuation import generate as generate_continuation, latest_snapshot


def refresh(snapshot=None, root=ROOT, prefer_webp=True, include_context=True):
    root=Path(root)
    snap=Path(snapshot) if snapshot else latest_snapshot(root)
    if snap is not None and not snap.is_absolute():
        snap=root/snap
    if snap is None or not (snap/'batch-summary.json').is_file():
        raise FileNotFoundError('No batch snapshot. Run a five-pose batch first, or use --snapshot.')
    summary=read_json(snap/'batch-summary.json')
    batch_label=summary.get('batch_label','batch-unknown')
    pass_label=summary.get('pass_label','pass-unknown')
    # Current state text must be up to date before context is packaged.
    generate_continuation(root,snap)
    ts=timestamp()
    dest=snap/f'spose-remote-feedback-{batch_label}-{pass_label}_{ts}.zip'
    export=create_feedback(snap,dest,root,prefer_webp,include_context)
    # Do not clear live preview directories until the ZIP has been built and verified.
    stage_rev=root/'review.next';stage_up=root/'upload.next'
    for stage in (stage_rev,stage_up):
        if stage.exists():shutil.rmtree(stage)
        stage.mkdir(parents=True)
    try:
        notes=(snap/'batch-summary.md').read_text(encoding='utf-8') if (snap/'batch-summary.md').is_file() else '# Batch summary\n'
        (stage_rev/'SUMMARY.md').write_text(notes,encoding='utf-8')
        (stage_up/'SUMMARY.md').write_text(notes,encoding='utf-8')
        image_names=[]
        for r in summary.get('results',[]):
            rel=r.get('revision_folder')
            if not rel:continue
            pre=root/Path(str(rel).replace('\\','/'))/'previews'
            if not pre.resolve().is_relative_to((root/'poses').resolve()):
                raise ValueError('Unsafe revision preview path: '+str(rel))
            if not pre.is_dir():continue
            for src in sorted(pre.glob('*.png')):
                name=f"{r['pose_id']}_{src.name}"
                shutil.copy2(src,stage_rev/name)
                shutil.copy2(src,stage_up/name)
                image_names.append(name)
        index={'batch_label':batch_label,'pass_label':pass_label,'source_snapshot':str(snap.relative_to(root)),
               'feedback_zip':dest.name,'images':image_names,'image_count':len(image_names),
               'pose_count':len(summary.get('results',[])),
               'ephemeral':True,'lossless_webp_feedback':prefer_webp}
        for stage in (stage_rev,stage_up):
            (stage/'manifest.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
        shutil.copy2(dest,stage_up/dest.name)
        for stage,target in ((stage_rev,root/'review'),(stage_up,root/'upload')):
            if target.exists():shutil.rmtree(target)
            stage.rename(target)
    finally:
        for stage in (stage_rev,stage_up):
            if stage.exists():shutil.rmtree(stage)
    return {**export,'review_folder':str(root/'review'),'upload_folder':str(root/'upload'),
            'snapshot_folder':str(snap),'flat_png_count':len(image_names)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--image-format',choices=['webp','png'],default='webp')
    parser.add_argument('--no-context',action='store_true',help='Diagnostic use only; default single feedback includes portable context')
    args=parser.parse_args()
    print(json.dumps(refresh(args.snapshot,args.root,args.image_format=='webp',not args.no_context),indent=2))

if __name__=='__main__':main()
