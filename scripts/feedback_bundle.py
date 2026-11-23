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
    local_meta_path=snapshot/'local-refinement-evidence.json'
    local_meta=read_json(local_meta_path) if local_meta_path.is_file() else None
    if local_meta and (local_meta.get('batch_label')!=batch_label or local_meta.get('pass_label')!=pass_label):
        raise ValueError('Local evidence batch/pass mismatch')
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
            selection=local_meta.get('pose_selections',{}).get(pose_id,{}) if local_meta else {}
            selected=selection.get('selected_attempt',0)
            # Compact evidence: when a nonbaseline candidate was selected, baseline
            # contributes two diagnostic views; selected gets four views elsewhere.
            for file in sorted(pre.glob('*.png')):
                if selected>0 and file.stem not in ('side','three-quarter'):
                    continue
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
        if local_meta and local_meta.get('pose_selections',{}).get(pose_id,{}).get('selected_attempt',0)>0:
            item['compact_baseline_views_omitted']=item['missing_views']
            item['missing_views']=[]  # selected local candidate's four views are under local/
        if item['missing_views']:
            warnings.append(f"{pose_id}: missing views {', '.join(item['missing_views'])}")
        entries.append(item)
    local_export={'included':False,'selected':{},'attempts':{},'image_count':0,'evidence_mode':'compact'}
    if local_meta:
        local_export['included']=True
        local_export['selected']={k:v.get('selected_attempt',0) for k,v in local_meta['pose_selections'].items()}
        local_export['attempts']={k:len(v.get('attempts',[])) for k,v in local_meta['pose_selections'].items()}
        payloads['local/SELECTIONS.json']=local_meta_path.read_bytes()
        local_root=snapshot/'local-evidence'
        for evidence_file in sorted(local_root.rglob('*')):
            if not evidence_file.is_file():continue
            if evidence_file.is_symlink() or not evidence_file.resolve().is_relative_to(local_root.resolve()):
                raise ValueError('Unsafe local evidence file')
            relative=evidence_file.relative_to(snapshot).as_posix()
            # Prohibit accidental shipping of huge Blender scene files/logs.
            if evidence_file.suffix.lower() not in ('.json','.png'):
                continue
            if evidence_file.suffix.lower()=='.json':
                if evidence_file.stat().st_size>4_000_000:raise ValueError('Local evidence JSON unexpectedly large: '+relative)
                payloads['local/'+relative]=evidence_file.read_bytes()
            else:
                try:blob,ext,info=encode_verified(evidence_file,'webp' if prefer_webp else 'original-png')
                except (RuntimeError,ImportError) as exc:
                    warnings.append(str(exc)+'; kept PNG for '+relative)
                    blob,ext,info=encode_verified(evidence_file,'original-png')
                payloads['local/'+relative.removesuffix('.png')+ext]=blob
                codec_counter[info['codec']]=codec_counter.get(info['codec'],0)+1
                local_export['image_count']+=1
        if not all(x in local_export['selected'] for x in [r['pose_id'] for r in results]):
            warnings.append('Local selection map is incomplete; baseline will be used for missing entries')
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
    # Calibrator results ride inside the SAME exchange ZIP. Never require a
    # second handoff or separate calibration upload. Stale run results are
    # intentionally excluded rather than misrepresented as this pass.
    calibration_meta={'included':False,'reason':'not_run_or_no_matching_pass','files':[]}
    calib_root=root/'tooling'/'calibration'/'CPL01-v001'
    latest_path=calib_root/'LATEST.json'
    # Snapshot-owned calibration reference must win over global LATEST.json.
    explicit_path=snapshot/'calibration-run.json'
    try:
        if explicit_path.is_file():
            reference=read_json(explicit_path)
            if reference.get('status')=='probe_error':
                warnings.append('Calibration failed: '+str(reference.get('error')))
            if reference.get('run_dir'):
                run=(root/Path(reference['run_dir'])).resolve()
                if not run.is_relative_to(calib_root.resolve()):
                    raise ValueError('Unsafe snapshot calibration reference')
                latest={'run_dir':run.relative_to(calib_root).as_posix(),
                        'batch_label':reference['batch_label'],'pass_label':reference['pass_label'],
                        'poses_measured':reference.get('poses_measured'),'run_utc':run.name}
            else:latest={}
        elif (snapshot/'registered-run.json').is_file():
            # Registered run without its own probe: never borrow unrelated global LATEST.
            latest={}
        elif latest_path.is_file():
            latest=read_json(latest_path)
        else:latest={}
        if latest:
            if latest.get('batch_label')==batch_label and latest.get('pass_label')==pass_label:
                rel=Path(latest['run_dir'])
                run=(calib_root/rel).resolve()
                if not run.is_relative_to(calib_root.resolve()):
                    raise ValueError('Unsafe calibration run pointer')
                for f in sorted(run.glob('*.json')):
                    if f.is_symlink() or not f.is_file() or f.stat().st_size>4_000_000:
                        raise ValueError('Unexpected calibration member '+f.name)
                    key='calibration/'+f.name
                    payloads[key]=f.read_bytes()
                    calibration_meta['files'].append(key)
                calibration_meta.update({'included':bool(calibration_meta['files']),
                    'reason':'matching_run','run_utc':latest.get('run_utc'),
                    'poses_measured':latest.get('poses_measured')})
                payloads['calibration/REFERENCE.json']=(json.dumps(latest,indent=2)+'\n').encode('utf-8')
                calibration_meta['files'].append('calibration/REFERENCE.json')
            else:
                warnings.append('Calibration data exists but belongs to another batch/pass; not included')
    except Exception as exc:
        warnings.append(f'Calibration export skipped: {type(exc).__name__}: {exc}')
        calibration_meta={'included':False,'error':str(exc),'files':[]}
    # Read-only portable registry snapshot for out-of-order handoffs.
    try:
        from registry import export_dict as export_registry
        registry_data=export_registry(root)
        payloads['registry/registry.json']=(json.dumps(registry_data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        registry_embedded=not registry_data.get('migration_required',False)
    except Exception as exc:
        registry_embedded=False
        warnings.append(f'Registry snapshot unavailable: {type(exc).__name__}: {exc}')
    summary_text=pretty(results,batch_label,pass_label,warnings)
    if local_meta:
        summary_text+='\n## Selected additive local candidates (advisory, not accepted)\n\n'
        summary_text+='| Pose | Attempt | Recorded reason |\n|---|---:|---|\n'
        for pose,item in sorted(local_meta['pose_selections'].items()):
            reason=str(item.get('selection_reason','')).replace('|','/')
            summary_text+=f"| `{pose}` | {item.get('selected_attempt',0):02d} | {reason} |\n"
        summary_text+='\nAll recorded trial parameter changes and measured results are under `local/`.\n'
    payloads['SUMMARY.md']=summary_text.encode('utf-8')
    payloads['batch-summary.json']=(json.dumps(summary,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    payloads['START-HERE.md']=(
        '# SPOSE remote feedback — start here\n\n'
        +f'Batch: `{batch_label}`; pass: `{pass_label}`. One ZIP contains all {len(results)} pose results.\n\n'
        +'Read `SUMMARY.md`, `batch-summary.json`, and `manifest.json` first. '
        +'Images and source controls for each pose are under `poses/<POSE_ID>/`. '
        +'If calibration has been collected for this pass, measured neutral rig and pose scene data are under `calibration/`. '
        +'If `manifest.json` reports local refinement, selected candidates, per-attempt measurements and input deltas are under `local/`. Local candidates are NOT automatically promoted into authoritative revisions. '
        +'A complete portable (read-only) library context is under `context/` if `context_included` is true in the manifest. '
        +'If present, `registry/registry.json` contains the global read-only batch registry snapshot. '
        +'The authoritative, runnable Blender library and its `.blend` assets remain local. '
        +'Visual ratings are determined by the assistant/human after inspecting previews, not by the exporter.\n'
    ).encode('utf-8')
    manifest={
        'schema_version':2,'kind':'spose-remote-combined-feedback',
        'batch_label':batch_label,'pass_label':pass_label,
        'generated_at_utc':timestamp(),'pose_count':len(results),
        'pose_ids':[x['pose_id'] for x in results],
        'image_count':sum(len(x['images']) for x in entries)+local_export['image_count'],
        'image_codecs':codec_counter,
        'context_included':context_meta is not None,
        'registry_included':registry_embedded,
        'calibration':calibration_meta,
        'local_refinement':local_export,
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
            'calibration_included':calibration_meta['included'],
            'local_refinement_included':local_export['included'],
            'warnings':warnings}
