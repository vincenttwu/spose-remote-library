"""Create one SPOSE batch feedback ZIP from stored pose revisions, not nested ZIPs.

The archive includes flat review summaries, per-pose inputs/validation/images,
portable read-only context, and a SHA-256 member inventory. Image data uses
RGBA-verified lossless WebP; original PNG is retained if Pillow/WebP unavailable.
No Blender execution is performed here.
"""
from __future__ import annotations
import datetime, hashlib, io, json, os, sys, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT, read_json
from compress_images import encode_verified

POSE_TEXT=('pose.json','validation.json','checksums.json','blender-result.json','build-settings.json','build.log')


def digest(data):return hashlib.sha256(data).hexdigest()


def timestamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def pretty(results, batch_label, pass_label, feedback_notes):
    rows=[f'# SPOSE {batch_label} {pass_label} — combined feedback','',
          'Five-pose batch. Quality warnings do not block imports or progression.','',
          '| Pose | Revision | Build status | Stability | Issues | Views |',
          '|---|---|---|---|---:|---:|']
    for r in results:
        rv=r.get('revision')
        rev=f'r{int(rv):03d}' if isinstance(rv,int) else '—'
        rows.append(f"| `{r.get('pose_id')}` | {rev} | {r.get('build_status','unknown')} | {r.get('stability', 'unreviewed')} | {r.get('issue_count',0)} | {len(r.get('previews', []))} |")
    rows += ['', '## Export notes', '']
    rows += ['- '+x for x in feedback_notes] if feedback_notes else ['- No exporter warnings.']
    rows += ['', '## Interpretation','',
             '- `draft` means the Blender revision is available for use; it does not assert visual quality.',
             '- `reused_existing_package` means **no new pose revision** was produced. Never count reuse as a successful calibration pass.',
             '- Human visual/source fidelity scores are not synthesized by this exporter.',
             '- For a fresh assistant session, read `START-HERE.md`, `context/AGENTS.md`, `context/SKILL.md`, and `context/handoff/SNAPSHOT-STATUS.md`.', '']
    return '\n'.join(rows)


def create_feedback(snapshot:Path, output:Path, root:Path=ROOT, prefer_webp:bool=True, include_context:bool=True):
    """Build a single, complete, self-contained feedback archive. No state gates."""
    root=Path(root);snapshot=Path(snapshot);output=Path(output)
    summary=read_json(snapshot/'batch-summary.json')
    results=summary['results']
    batch_label=summary.get('batch_label','batch-unknown')
    pass_label=summary.get('pass_label','pass-unknown')
    warnings=[]; codec_counter={}; payloads={}
    entries=[]
    for result in results:
        pose_id=result['pose_id']
        rel=result.get('revision_folder')
        rev=(root/Path(str(rel).replace('\\','/'))) if rel else None
        if rev is not None and not rev.resolve().is_relative_to((root/'poses').resolve()):
            raise ValueError('Revision path must stay under library poses/: '+str(rel))
        item={'pose_id':pose_id,'revision':result.get('revision'), 'source_revision_folder':rel,
              'status':result.get('build_status'), 'images':[], 'missing_views':[], 'files':[]}
        if not rev or not rev.is_dir():
            warnings.append(pose_id+': no stored revision; recorded failure without preview')
            entries.append(item)
            continue
        for name in POSE_TEXT:
            file=rev/name
            if file.is_file():
                key=f'poses/{pose_id}/{name}'
                payloads[key]=file.read_bytes(); item['files'].append(key)
        inputs=rev/'inputs'
        if inputs.is_dir():
            for file in sorted(inputs.glob('*.json')):
                key=f'poses/{pose_id}/inputs/{file.name}'
                payloads[key]=file.read_bytes();item['files'].append(key)
        pre=rev/'previews'
        if pre.is_dir():
            for file in sorted(pre.glob('*.png')):
                try:
                    blob,ext,info=encode_verified(file, 'webp' if prefer_webp else 'original-png')
                except (RuntimeError, ImportError) as err:
                    # Missing optional dependency must not block the batch.
                    warnings.append(f'{pose_id}/{file.name}: {err}; included unchanged lossless PNG')
                    blob,ext,info=encode_verified(file,'original-png')
                # Real pixel conversion mismatch IS an integrity error.
                key=f'poses/{pose_id}/images/{file.stem}{ext}'
                payloads[key]=blob
                item['images'].append({'member':key,'original_png_sha256':digest(file.read_bytes()),**info})
                codec_counter[info['codec']]=codec_counter.get(info['codec'],0)+1
        expected={'front','side','three-quarter','qa-regions'}
        present={Path(k['member']).stem for k in item['images']}
        item['missing_views']=sorted(expected-present)
        if item['missing_views']:
            warnings.append(f"{pose_id}: missing views {', '.join(item['missing_views'])}")
        entries.append(item)
    # A portable handoff nested as normal members rather than a second ZIP.
    context_meta=None
    if include_context:
        try:
            from package_library_for_remote import build_payload
            context_files,context_meta=build_payload(root)
            for name, blob in context_files.items():
                payloads['context/'+name]=blob
        except Exception as exc:
            # The feedback stays usable even if optional context generation fails,
            # but the manifest makes absence explicit rather than silently omitting.
            warnings.append(f'Portable context generation failed: {type(exc).__name__}: {exc}')
    summary_text=pretty(results,batch_label,pass_label,warnings)
    payloads['SUMMARY.md']=summary_text.encode('utf-8')
    payloads['batch-summary.json']=(json.dumps(summary,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    payloads['START-HERE.md']=(
        '# SPOSE remote feedback — start here\n\n'
        +f'Batch: `{batch_label}`; pass: `{pass_label}`. One ZIP contains all {len(results)} pose results.\n\n'
        +'Read `SUMMARY.md`, `batch-summary.json`, and `manifest.json` first. '
        +'Images and source controls for each pose are under `poses/<POSE_ID>/`. '
        +'A complete portable (read-only) library context is under `context/` if `context_included` is true in the manifest. '
        +'The authoritative, runnable Blender library and its `.blend` assets remain local. '
        +'Visual ratings are determined by the assistant/human after inspecting previews, not by the exporter.\n'
    ).encode('utf-8')
    manifest={
        'schema_version':2,'kind':'spose-remote-combined-feedback',
        'batch_label':batch_label,'pass_label':pass_label,
        'generated_at_utc':timestamp(),'pose_count':len(results),
        'pose_ids':[x['pose_id'] for x in results],
        'image_count':sum(len(x['images']) for x in entries),
        'image_codecs':codec_counter,
        'context_included':context_meta is not None,
        'context_summary':context_meta,
        'warnings':warnings,'pose_results':entries,
        'files_sha256':{name:digest(blob) for name,blob in sorted(payloads.items())},
    }
    payloads['manifest.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.is_file():raise FileExistsError('Refusing to overwrite existing feedback: '+str(output))
    # Write atomically: unfinished artifacts never appear as complete ZIPs.
    stage=output.with_name(output.name+'.partial')
    try:
        with zipfile.ZipFile(stage,'w',allowZip64=True) as z:
            for name,blob in sorted(payloads.items()):
                method=zipfile.ZIP_STORED if name.endswith('.webp') else zipfile.ZIP_DEFLATED
                z.writestr(name,blob,compress_type=method,compresslevel=6 if method==zipfile.ZIP_DEFLATED else None)
        with zipfile.ZipFile(stage) as z:
            if z.testzip() is not None:raise RuntimeError('Corrupt ZIP after export')
            for name, sha in manifest['files_sha256'].items():
                if digest(z.read(name))!=sha:raise RuntimeError('Feedback archive member checksum mismatch: '+name)
        os.replace(stage,output)
    finally:
        if stage.exists():stage.unlink()
    return {'path':str(output),'size_bytes':output.stat().st_size,
            'pose_count':len(results),'image_count':manifest['image_count'],
            'image_codecs':codec_counter,'context_included':manifest['context_included'],
            'warnings':warnings}
