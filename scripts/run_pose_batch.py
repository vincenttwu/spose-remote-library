"""Run EVERY pose in a SPOSE batch, record every outcome, and export one feedback bundle.

No geometry/source/human-review gates. A build can be unstable and still be a usable
'draft'. Failure of one pose never prevents attempting the remaining poses.

This runner also refreshes flat top-level workflow folders:
- snapshots/ : persistent batch/pass history
- review/    : disposable latest rendered images and summary
- upload/    : disposable latest feedback ZIP plus flat image copies for discussion/upload
"""
from __future__ import annotations
import argparse, datetime, json, os, shutil, subprocess, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pose_common import ROOT, load_package, read_json, save_json


def iso_stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def versions(pose_id, pair_id='CPL01', pair_version='v001'):
    base = ROOT / 'poses' / pose_id / pair_id / pair_version
    return {p.name: p for p in base.glob('r[0-9][0-9][0-9]') if p.is_dir()}


def matching_prior(pose_id, package_timestamp, pair_id='CPL01', pair_version='v001'):
    for p in sorted(versions(pose_id, pair_id, pair_version).values(), reverse=True):
        manifest = p / 'inputs' / 'manifest.json'
        if not manifest.is_file():
            continue
        try:
            if read_json(manifest).get('package_timestamp_utc') == package_timestamp:
                return p
        except Exception:
            continue
    return None


def report_one(pose_id, package_name, folder, build_status, build_output=None):
    result = {
        'pose_id': pose_id,
        'package': package_name,
        'revision_folder': str(folder.relative_to(ROOT)) if folder else None,
        'build_status': build_status,
        'accepted': False,
        'geometry_quality': 'not_measured',
        'issue_count': 0,
        'issues': [],
        'previews': [],
        'feedback_file': None,
    }
    if folder and (folder / 'pose.json').is_file():
        record = read_json(folder / 'pose.json')
        result['revision'] = record.get('revision')
        result['pose_status'] = record.get('status', 'unknown')
        result['accepted'] = record.get('status') == 'accepted'
        result['issues'] = record.get('issues', [])
        val = read_json(folder / 'validation.json') if (folder / 'validation.json').is_file() else {}
        result['geometry_quality'] = 'meets_reference' if val.get('hard_gate_pass') is True else 'needs_review'
        result['stability'] = val.get('stability', 'unreviewed')
        result['issue_count'] = len(result['issues'])
        result['previews'] = val.get('rendered_views', [])
        checks = val.get('technical_checks', {})
        result['posture_heights'] = checks.get('posture_heights', {})
        result['contact_checks'] = val.get('contact_checks', {})
    if build_output is not None:
        result['execution_output'] = build_output[-5000:]
    return result


def summarize(results, batch_id, created_at):
    lines = [
        f'# {batch_id} — complete batch execution',
        '',
        f'Run: `{created_at}`. **No geometry or approval gates; all available poses attempted.**',
        '',
        '| Pose | Revision | Build | Stability | Issues | Previews |',
        '|---|---|---|---|---:|---:|',
    ]
    for item in results:
        rev = 'r' + str(item.get('revision', '')).zfill(3) if item.get('revision') is not None else '—'
        lines.append(f"| `{item['pose_id']}` | {rev} | {item.get('build_status','unknown')} | {item.get('stability', item.get('geometry_quality','unknown'))} | {item.get('issue_count',0)} | {len(item.get('previews',[]))} |")
    lines += [
        '',
        'Build warnings are reference measurements, not reasons to pause other poses or other batches.',
        'Failed executions are recorded and can be repaired later. No pose is auto-accepted.',
        '',
    ]
    return '\n'.join(lines)


def run(plan, blender=None, dry_run=False, save_blend=False, rerun=False, defer_feedback=False):
    doc = read_json(plan)
    if doc.get('schema_version') != 1 or not isinstance(doc.get('poses'), list) or not doc['poses']:
        raise ValueError('Invalid batch plan: expected nonempty poses[]')
    name = doc.get('batch_id', 'SPOSE-BATCH')
    # Older plans predate explicit labels. Keep them runnable and visibly mark
    # their unknown pass instead of silently pretending it is Pass 02.
    import re
    batch_match = re.search(r'BATCH[-_ ]*(\d+)', str(name), re.IGNORECASE)
    batch_label = doc.get('batch_label') or (f'batch-{int(batch_match.group(1)):04d}' if batch_match else 'batch-unlabeled')
    pass_label = doc.get('pass_label') or 'pass-legacy'
    batch_slug = f'{batch_label}-{pass_label}'
    if not all(isinstance(x, dict) and x.get('pose_id') and x.get('package') for x in doc['poses']):
        raise ValueError('Each batch item needs pose_id and package')
    if len({x['pose_id'] for x in doc['poses']}) != len(doc['poses']):
        raise ValueError('Duplicate pose ID in one plan')
    if not dry_run:
        blender = blender or os.environ.get('SPOSE_BLENDER') or shutil.which('blender')
        if not blender or not (Path(blender).is_file() or shutil.which(blender)):
            raise ValueError('Blender executable required, pass --blender or set SPOSE_BLENDER')
    stamp = iso_stamp()
    folder = ROOT / 'snapshots' / f'{batch_slug}_{stamp}'
    if not dry_run:
        folder.mkdir(parents=True, exist_ok=False)
    results = []
    for entry in doc['poses']:
        pose_id = entry['pose_id']
        pkg_name = entry['package']
        if Path(pkg_name).name != pkg_name:
            results.append({'pose_id': pose_id, 'package': pkg_name, 'build_status': 'package_path_error', 'issue_count': 1, 'issues': ['Unsafe package filename']})
            continue
        archive = ROOT / 'incoming' / pkg_name
        try:
            manifest, data = load_package(archive)
            if manifest['pose_id'] != pose_id:
                raise ValueError('Pose ID and plan mismatch')
            pair = manifest['dependencies']
            pair_id = pair['pair_id']
            pair_version = pair['pair_version']
            if dry_run:
                results.append({'pose_id': pose_id, 'package': pkg_name, 'build_status': 'package_verified', 'geometry_quality': 'not_measured', 'controls': len(data['rig-targets.json']['controls'])})
                continue
            existing = matching_prior(pose_id, manifest['package_timestamp_utc'], pair_id, pair_version)
            if existing and not rerun:
                item = report_one(pose_id, pkg_name, existing, 'reused_existing_package')
                item['new_revision_created'] = False
                item['execution_note'] = 'Reused exact package identity. NO new calibration revision created. Supply a newly authored package for a genuine new pass.'
            else:
                before = set(versions(pose_id, pair_id, pair_version))
                cmd = [sys.executable, str(ROOT / 'scripts/import_pose.py'), str(archive), '--blender', str(blender)]
                if save_blend:
                    cmd.append('--save-blend')
                try:
                    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=2400)
                    output = (proc.stdout or '') + '\n' + (proc.stderr or '')
                    rc = proc.returncode
                except Exception:
                    output = traceback.format_exc()
                    rc = -1
                after = versions(pose_id, pair_id, pair_version)
                new = [p for k, p in after.items() if k not in before]
                found = max(new, key=lambda p: p.name) if new else matching_prior(pose_id, manifest['package_timestamp_utc'], pair_id, pair_version)
                item = report_one(pose_id, pkg_name, found, 'execution_failed' if rc else ('built_new_revision' if new else 'no_new_revision'), output)
                item['new_revision_created'] = bool(new)
                item['import_returncode'] = rc
        except Exception as ex:
            item = {'pose_id': pose_id, 'package': pkg_name, 'build_status': 'package_or_import_error', 'issue_count': 1, 'issues': [str(ex)], 'exception': traceback.format_exc()[-2000:]}
        results.append(item)
        if not dry_run:
            save_json(folder / 'batch-summary.partial.json', {'batch_id': name, 'results': results})
    summary = {
        'schema_version': 1,
        'batch_id': name,
        'batch_label': batch_label,
        'pass_label': pass_label,
        'run_utc': stamp,
        'mode': 'dry_run' if dry_run else 'attempt_all',
        'progression_policy': 'record_and_continue_no_gates',
        'input_count': len(doc['poses']),
        'result_count': len(results),
        'blender_used': any('import_returncode' in r for r in results),
        'new_revision_count': sum(1 for r in results if r.get('new_revision_created') is True),
        'reused_revision_count': sum(1 for r in results if r.get('build_status')=='reused_existing_package'),
        'results': results,
    }
    if dry_run:
        return summary
    summary_md = summarize(results, name, stamp)
    save_json(folder / 'batch-summary.json', summary)
    (folder / 'batch-summary.md').write_text(summary_md, encoding='utf-8')
    if defer_feedback:
        summary["feedback_export_deferred"] = True
        save_json(folder / "batch-summary.json", summary)
        return summary
    from refresh_exchange import refresh
    try:
        result = refresh(snapshot=folder, root=ROOT)
        summary['combined_feedback_zip'] = result['path'] if result['path'].startswith(str(ROOT/'upload')) else str(ROOT/'upload'/Path(result['path']).name)
        summary['snapshot_folder'] = str(folder)
        summary['review_folder'] = result['review_folder']
        summary['upload_folder'] = result['upload_folder']
        summary['feedback_export'] = {'image_count':result['image_count'], 'context_included':result['context_included'], 'warnings':result['warnings']}
    except Exception as exc:
        # Preserve the completed batch and every revision even if optional export breaks.
        summary['feedback_export_error'] = f'{type(exc).__name__}: {exc}'
        summary['feedback_export_traceback'] = traceback.format_exc()[-5000:]
        print('WARNING: batch complete, but combined feedback export failed; run scripts/refresh_exchange.py', file=sys.stderr)
    save_json(folder / 'batch-summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=ROOT / 'batches/BATCH-001.json')
    parser.add_argument('--blender', help='Path to Blender executable')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--save-blend', action='store_true')
    parser.add_argument('--rerun', action='store_true')
    parser.add_argument('--defer-feedback', action='store_true', help='Only for combined render+calibration workflow: export after probing')
    args = parser.parse_args()
    out = run(args.plan, blender=args.blender, dry_run=args.dry_run, save_blend=args.save_blend, rerun=args.rerun, defer_feedback=args.defer_feedback)
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
