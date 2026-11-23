"""Mirrored workspace batch runner — executes workspace/batches/BATCH-XXXX-PASS-YY.json.

Mirrors top-level run_pose_batch.py / run_registered_batch.py strictly inside workspace/:
  - Reads data-only packages from workspace/incoming/
  - Validates dependencies against pinned top-level catalog & pair template (read-only)
  - Creates immutable revisions under workspace/poses/<POSE_ID>/CPL01/v001/rNNN/
    (or reuses an existing revision if package SHA-256 matches, emitting reused_existing_package=true)
  - Creates a persistent snapshot under workspace/snapshots/<batch>-<pass>_<ts>/
  - Builds a compact lossless WebP feedback ZIP and activates disposable workspace/review/ & workspace/upload/
  - Syncs workspace/tracking/workspace-tracker.json and regenerates workspace/ROADMAP.{md,json}

Never writes outside workspace/.

Usage:
  python workspace/scripts/ws_run_batch.py --plan workspace/batches/BATCH-0004-PASS-01.json --dry-run
  python workspace/scripts/ws_run_batch.py --plan workspace/batches/BATCH-0004-PASS-01.json --blender "<BLENDER_EXE>"
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from ws_common import (
    INCOMING_DIR,
    LIBRARY_ROOT,
    SNAPSHOTS_DIR,
    ensure_in_workspace,
    ensure_workspace_dirs,
    list_pose_revisions,
    next_pose_revision_dir,
    normalize_batch_label,
    normalize_pass_label,
    pose_common,
    read_json,
    read_library_authority,
    resolve_workspace_cli_path,
    sha256_file,
    utc_now_iso,
    utc_now_stamp,
    workspace_rel,
    write_json_workspace,
    write_text_workspace,
)
import ws_activate_batch
import ws_tracker


def _find_existing_revision_for_sha(
    pose_id: str, pkg_sha256: str, pair_id: str, pair_version: str
) -> tuple[str, Path] | None:
    for rdir in list_pose_revisions(pose_id, pair_id, pair_version):
        meta_path = rdir / "package-meta.json"
        if meta_path.is_file():
            if read_json(meta_path).get("package_sha256") == pkg_sha256:
                return rdir.name, rdir
    return None


def validate_plan(plan_path: Path) -> tuple[dict, list[dict]]:
    plan_path = ensure_in_workspace(plan_path)
    plan = read_json(plan_path)
    if not plan.get("batch_label") or not plan.get("pass_label"):
        raise ValueError(f"Plan missing batch_label or pass_label: {plan_path}")
    poses_list = plan.get("poses", [])
    if not poses_list:
        raise ValueError(f"Plan has empty poses list: {plan_path}")

    validated = []
    for item in poses_list:
        pkg_name = Path(item["package"]).name
        zpath = ensure_in_workspace(INCOMING_DIR / pkg_name)
        if not zpath.is_file():
            raise FileNotFoundError(f"Package missing in workspace/incoming/: {zpath}")
        manifest, data = pose_common.load_package(zpath, validate_dependencies=True)
        if manifest["pose_id"] != item["pose_id"]:
            raise ValueError(f"Pose ID mismatch: plan={item['pose_id']} vs zip={manifest['pose_id']}")
        validated.append(
            {
                "pose_id": manifest["pose_id"],
                "package_name": pkg_name,
                "zip_path": zpath,
                "zip_rel": workspace_rel(zpath),
                "zip_sha256": sha256_file(zpath),
                "package_timestamp_utc": manifest["package_timestamp_utc"],
                "data": data,
            }
        )
    return plan, validated


def render_batch_summary_md(summary: dict) -> str:
    lines = [
        f"# Workspace Batch Summary — `{summary['batch_label']}` / `{summary['pass_label']}`",
        "",
        f"- **Family:** `{summary.get('family') or 'MIXED'}`",
        f"- **Run (UTC):** `{summary['run_utc']}`",
        f"- **Plan:** `{summary['plan_file']}`",
        f"- **Snapshot:** `{summary['snapshot_dir']}`",
        f"- **Blender:** `{summary.get('blender_executable') or 'none'}`",
        f"- **Rendered:** `{summary['rendered_count']}/{summary['pose_count']}`",
        "",
        "| Pose ID | Revision | Reused | Exit | Rendered | Issues | Previews | Package |",
        "|---|---|---|---:|---|---:|---:|---|",
    ]
    for r in summary["results"]:
        lines.append(
            f"| `{r['pose_id']}` | `{r['revision']}` | `{r['reused_existing_package']}` | "
            f"{r['exit_code']} | `{r['rendered']}` | {r['issue_count']} | {r['preview_count']} | `{r['package']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def run_batch(
    plan_path: Path,
    blender: str | None = None,
    dry_run: bool = False,
    save_blend: bool = True,
    activate: bool = True,
    author_script: Path | None = None,
) -> dict:
    ensure_workspace_dirs()
    auth = read_library_authority()
    plan, validated = validate_plan(plan_path)
    b_label = normalize_batch_label(plan["batch_label"])
    p_label = normalize_pass_label(plan["pass_label"])

    if dry_run:
        return {
            "ok": True,
            "mode": "dry_run",
            "batch_label": b_label,
            "pass_label": p_label,
            "family": plan.get("family"),
            "plan_file": workspace_rel(plan_path),
            "validated_packages": [
                {
                    "pose_id": v["pose_id"],
                    "package": v["package_name"],
                    "sha256": v["zip_sha256"],
                }
                for v in validated
            ],
            "blender_executed": False,
        }

    if not blender:
        raise ValueError("--blender is required unless --dry-run is specified")
    blender_exe = Path(blender)
    if not blender_exe.is_file():
        raise FileNotFoundError(f"Blender executable not found: {blender_exe}")

    builder_script = (LIBRARY_ROOT / "scripts" / "blender_build.py").resolve()
    pair_id = auth["pair_id"]
    pair_ver = auth["pair_version"]
    results = []

    for item in validated:
        pose_id = item["pose_id"]
        existing = _find_existing_revision_for_sha(pose_id, item["zip_sha256"], pair_id, pair_ver)
        if existing is not None:
            rev_label, rev_dir = existing
            res_path = rev_dir / "blender-result.json"
            b_res = read_json(res_path) if res_path.is_file() else {"rendered": False, "issues": []}
            previews_dir = rev_dir / "previews"
            png_count = len(list(previews_dir.glob("*.png"))) if previews_dir.is_dir() else 0
            results.append(
                {
                    "pose_id": pose_id,
                    "package": item["package_name"],
                    "package_sha256": item["zip_sha256"],
                    "revision": rev_label,
                    "revision_path": workspace_rel(rev_dir),
                    "reused_existing_package": True,
                    "exit_code": 0,
                    "rendered": bool(b_res.get("rendered")),
                    "issue_count": len(b_res.get("issues", [])),
                    "issues": b_res.get("issues", []),
                    "preview_count": png_count,
                    "scene_blend_saved": (rev_dir / "scene.blend").is_file(),
                }
            )
            continue

        rev_label, rev_dir = next_pose_revision_dir(pose_id, pair_id, pair_ver)
        inputs_dir = ensure_in_workspace(rev_dir / "inputs")
        previews_dir = ensure_in_workspace(rev_dir / "previews")
        inputs_dir.mkdir(parents=True, exist_ok=True)
        previews_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(item["zip_path"], "r") as zf:
            for name in zf.namelist():
                ensure_in_workspace(inputs_dir / name).write_bytes(zf.read(name))

        write_json_workspace(
            rev_dir / "package-meta.json",
            {
                "pose_id": pose_id,
                "revision": rev_label,
                "package": item["package_name"],
                "package_sha256": item["zip_sha256"],
                "package_timestamp_utc": item["package_timestamp_utc"],
                "batch_label": b_label,
                "pass_label": p_label,
                "imported_utc": utc_now_iso(),
            },
        )

        render_cfg = item["data"].get("render-config.json")
        settings = {
            "pose_id": pose_id,
            "output": str(rev_dir),
            "template_file": str(auth["appearance_path"]),
            "fallback_template": str(auth["template_path"]),
            "save_blend": bool(save_blend),
            "render_config": render_cfg,
        }
        settings_path = write_json_workspace(rev_dir / "build-settings.json", settings)

        cmd = [
            str(blender_exe),
            "--background",
            "--factory-startup",
            "--python-exit-code",
            "1",
            "--python",
            str(builder_script),
            "--",
            "--settings",
            str(settings_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        ensure_in_workspace(rev_dir / "build.log").write_text(
            f"CMD: {' '.join(cmd)}\nEXIT: {proc.returncode}\n\n--- STDOUT ---\n{proc.stdout}\n\n--- STDERR ---\n{proc.stderr}\n",
            encoding="utf-8",
        )

        result_path = rev_dir / "blender-result.json"
        b_res = read_json(result_path) if result_path.is_file() else {"rendered": False, "issues": []}
        png_count = len(list(previews_dir.glob("*.png"))) if previews_dir.is_dir() else 0

        results.append(
            {
                "pose_id": pose_id,
                "package": item["package_name"],
                "package_sha256": item["zip_sha256"],
                "revision": rev_label,
                "revision_path": workspace_rel(rev_dir),
                "reused_existing_package": False,
                "exit_code": proc.returncode,
                "rendered": bool(b_res.get("rendered")),
                "issue_count": len(b_res.get("issues", [])),
                "issues": b_res.get("issues", []),
                "preview_count": png_count,
                "scene_blend_saved": (rev_dir / "scene.blend").is_file(),
            }
        )

    snap_ts = utc_now_stamp()
    snap_dir = ensure_in_workspace(SNAPSHOTS_DIR / f"{b_label}-{p_label}_{snap_ts}")
    snap_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan_path, ensure_in_workspace(snap_dir / "plan.json"))
    if author_script is not None and author_script.is_file():
        shutil.copy2(author_script, ensure_in_workspace(snap_dir / "author.py"))

    summary = {
        "schema_version": 2,
        "kind": "spose_workspace_batch_summary",
        "non_authoritative": True,
        "batch_label": b_label,
        "pass_label": p_label,
        "family": plan.get("family"),
        "plan_file": workspace_rel(plan_path),
        "snapshot_dir": workspace_rel(snap_dir),
        "run_utc": utc_now_iso(),
        "blender_executable": str(blender_exe),
        "pose_count": len(results),
        "rendered_count": sum(1 for r in results if r["rendered"]),
        "results": results,
    }
    write_json_workspace(snap_dir / "batch-summary.json", summary)
    write_text_workspace(snap_dir / "batch-summary.md", render_batch_summary_md(summary))

    exchange_out = (
        ws_activate_batch.activate_snapshot(snap_dir, rebuild_zip=True)
        if activate
        else ws_activate_batch.build_feedback_zip(snap_dir)
    )
    sync_out = ws_tracker.cmd_sync()

    return {
        "ok": True,
        "mode": "rendered",
        "batch_label": b_label,
        "pass_label": p_label,
        "snapshot_dir": workspace_rel(snap_dir),
        "pose_count": summary["pose_count"],
        "rendered_count": summary["rendered_count"],
        "results": [
            {
                "pose_id": r["pose_id"],
                "revision": r["revision"],
                "reused": r["reused_existing_package"],
                "rendered": r["rendered"],
                "exit_code": r["exit_code"],
                "issue_count": r["issue_count"],
                "previews": r["preview_count"],
            }
            for r in results
        ],
        "exchange": exchange_out if activate else {"feedback_zip": exchange_out["zip_rel"]},
        "tracker_sync": sync_out,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Path to workspace/batches/BATCH-XXXX-PASS-YY.json")
    parser.add_argument("--blender", help="Path to Blender 5.2 executable")
    parser.add_argument("--dry-run", action="store_true", help="Validate packages only; do not launch Blender")
    parser.add_argument("--no-save-blend", action="store_true", help="Skip saving scene.blend")
    parser.add_argument("--no-activate", action="store_true", help="Do not update disposable workspace/review/ & upload/")
    parser.add_argument("--author-script", help="Optional authoring script to archive in the snapshot")
    args = parser.parse_args()

    plan_path = resolve_workspace_cli_path(args.plan)
    author_path = resolve_workspace_cli_path(args.author_script) if args.author_script else None
    out = run_batch(
        plan_path=plan_path,
        blender=args.blender,
        dry_run=args.dry_run,
        save_blend=not args.no_save_blend,
        activate=not args.no_activate,
        author_script=author_path,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
