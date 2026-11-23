"""Workspace exchange activator — mirrors top-level scripts/activate_batch.py & refresh_exchange.py.

Rebuilds disposable workspace/review/ and workspace/upload/ from any persistent
workspace/snapshots/<batch>-<pass>_<ts>/ + canonical workspace/poses/<POSE_ID>/CPL01/v001/rNNN/
with ZERO Blender rerenders. Optionally builds or refreshes the compact lossless WebP feedback ZIP.

Usage:
  python workspace/scripts/ws_activate_batch.py --batch batch-0003 --pass pass-02
  python workspace/scripts/ws_activate_batch.py --snapshot workspace/snapshots/batch-0003-pass-02_20261123T171633Z --rebuild-zip
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

from ws_common import (
    INCOMING_DIR,
    LIBRARY_ROOT,
    REVIEW_DIR,
    SNAPSHOTS_DIR,
    TRACKER_PATH,
    UPLOAD_DIR,
    WORKSPACE_ROOT,
    ensure_in_workspace,
    ensure_workspace_dirs,
    normalize_batch_label,
    normalize_pass_label,
    read_json,
    resolve_workspace_cli_path,
    sha256_bytes,
    sha256_file,
    utc_now_iso,
    utc_now_stamp,
    workspace_rel,
    write_json_workspace,
    write_text_workspace,
)
import ws_tracker


def build_feedback_zip(snapshot_dir: Path, prefer_webp: bool = True) -> dict:
    """Create a single compact lossless WebP feedback ZIP inside snapshot_dir."""
    snapshot_dir = ensure_in_workspace(snapshot_dir)
    summary_path = snapshot_dir / "batch-summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"Missing batch-summary.json in {snapshot_dir}")
    summary = read_json(summary_path)

    if str(LIBRARY_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(LIBRARY_ROOT / "scripts"))
    from compress_images import encode_verified

    b_label = normalize_batch_label(summary["batch_label"])
    p_label = normalize_pass_label(summary["pass_label"])

    payloads: dict[str, bytes] = {}
    warnings: list[str] = []

    for fn in ("plan.json", "batch-summary.json", "batch-summary.md", "AUDIT.md"):
        p = snapshot_dir / fn
        if p.is_file():
            payloads[fn] = p.read_bytes()

    image_count = 0
    for item in summary.get("results", []):
        pid = item["pose_id"]
        pkg_name = Path(item["package"]).name if item.get("package") else None
        if pkg_name:
            pkg_path = INCOMING_DIR / pkg_name
            if pkg_path.is_file():
                payloads[f"packages/{pkg_name}"] = pkg_path.read_bytes()

        rev_rel = item.get("revision_path")
        if not rev_rel:
            continue
        rev_dir = ensure_in_workspace(WORKSPACE_ROOT / rev_rel)
        for fn in ("blender-result.json", "build-settings.json", "build.log"):
            f = rev_dir / fn
            if f.is_file():
                payloads[f"poses/{pid}/{fn}"] = f.read_bytes()
        inp_dir = rev_dir / "inputs"
        if inp_dir.is_dir():
            for jf in sorted(inp_dir.glob("*.json")):
                payloads[f"poses/{pid}/inputs/{jf.name}"] = jf.read_bytes()
        pre_dir = rev_dir / "previews"
        if pre_dir.is_dir():
            for png in sorted(pre_dir.glob("*.png")):
                try:
                    blob, ext, _info = encode_verified(png, "webp" if prefer_webp else "original-png")
                except (RuntimeError, ImportError) as exc:
                    warnings.append(f"{pid}/{png.name}: {exc}; kept PNG")
                    blob, ext, _info = encode_verified(png, "original-png")
                payloads[f"poses/{pid}/images/{png.stem}{ext}"] = blob
                image_count += 1

    # Remove older feedback ZIPs in this snapshot so each snapshot keeps one canonical archive
    for old_z in snapshot_dir.glob("spose-workspace-feedback-*.zip"):
        old_z.unlink()

    ts = utc_now_stamp()
    zip_name = f"spose-workspace-feedback-{b_label}-{p_label}_{ts}.zip"
    manifest = {
        "schema_version": 2,
        "kind": "spose_workspace_feedback_bundle",
        "non_authoritative": True,
        "batch_label": b_label,
        "pass_label": p_label,
        "snapshot_dir": workspace_rel(snapshot_dir),
        "created_utc": utc_now_iso(),
        "image_count": image_count,
        "warnings": warnings,
        "members_sha256": {k: sha256_bytes(v) for k, v in sorted(payloads.items())},
    }
    payloads["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    out_zip = ensure_in_workspace(snapshot_dir / zip_name)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(payloads):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, payloads[name])

    return {
        "zip_path": out_zip,
        "zip_rel": workspace_rel(out_zip),
        "bytes": out_zip.stat().st_size,
        "sha256": sha256_file(out_zip),
        "image_count": image_count,
        "warnings": warnings,
    }


def _find_snapshot_for_batch_pass(batch_label: str, pass_label: str) -> Path:
    b_key = normalize_batch_label(batch_label)
    p_key = normalize_pass_label(pass_label)
    prefix = f"{b_key}-{p_key}_"
    matches = sorted(p for p in SNAPSHOTS_DIR.iterdir() if p.is_dir() and p.name.startswith(prefix))
    if not matches:
        raise FileNotFoundError(f"No snapshot found for {b_key}/{p_key} under workspace/snapshots/")
    return matches[-1]


def activate_snapshot(snapshot_dir: Path, rebuild_zip: bool = False) -> dict:
    """Populate disposable workspace/review/ and workspace/upload/ from snapshot_dir + workspace/poses/."""
    ensure_workspace_dirs()
    snapshot_dir = ensure_in_workspace(snapshot_dir)
    summary_path = snapshot_dir / "batch-summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"Missing batch-summary.json in {snapshot_dir}")
    summary = read_json(summary_path)
    b_label = normalize_batch_label(summary["batch_label"])
    p_label = normalize_pass_label(summary["pass_label"])

    existing_zips = sorted(snapshot_dir.glob("spose-workspace-feedback-*.zip"))
    if rebuild_zip or not existing_zips:
        zip_info = build_feedback_zip(snapshot_dir)
        fb_zip = zip_info["zip_path"]
    else:
        fb_zip = existing_zips[-1]
        zip_info = {
            "zip_rel": workspace_rel(fb_zip),
            "bytes": fb_zip.stat().st_size,
            "sha256": sha256_file(fb_zip),
        }

    for folder in (REVIEW_DIR, UPLOAD_DIR):
        folder = ensure_in_workspace(folder)
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    copied_pngs: list[str] = []
    for item in summary.get("results", []):
        pid = item["pose_id"]
        rev_rel = item.get("revision_path")
        if not rev_rel:
            continue
        pre_dir = ensure_in_workspace(WORKSPACE_ROOT / rev_rel / "previews")
        if not pre_dir.is_dir():
            continue
        for png in sorted(pre_dir.glob("*.png")):
            flat_name = f"{pid}_{png.name}"
            shutil.copy2(png, ensure_in_workspace(REVIEW_DIR / flat_name))
            shutil.copy2(png, ensure_in_workspace(UPLOAD_DIR / flat_name))
            copied_pngs.append(flat_name)

    # Copy single combined feedback ZIP into upload/
    upload_zip = ensure_in_workspace(UPLOAD_DIR / fb_zip.name)
    shutil.copy2(fb_zip, upload_zip)

    # Write SUMMARY.md and MANIFEST.json in both review/ and upload/
    summary_md_src = snapshot_dir / "batch-summary.md"
    summary_md_text = (
        summary_md_src.read_text(encoding="utf-8")
        if summary_md_src.is_file()
        else f"# Workspace Exchange: {b_label} / {p_label}\n\nSnapshot: `{workspace_rel(snapshot_dir)}`\n"
    )
    write_text_workspace(REVIEW_DIR / "SUMMARY.md", summary_md_text)
    write_text_workspace(UPLOAD_DIR / "SUMMARY.md", summary_md_text)

    manifest_base = {
        "schema_version": 2,
        "kind": "spose_workspace_exchange_manifest",
        "non_authoritative": True,
        "activated_utc": utc_now_iso(),
        "batch_label": b_label,
        "pass_label": p_label,
        "family": summary.get("family"),
        "snapshot_dir": workspace_rel(snapshot_dir),
        "images": copied_pngs,
    }
    write_json_workspace(REVIEW_DIR / "MANIFEST.json", manifest_base)
    write_json_workspace(
        UPLOAD_DIR / "MANIFEST.json",
        {**manifest_base, "feedback_zip": fb_zip.name, "feedback_zip_sha256": zip_info["sha256"]},
    )

    # Record active_exchange in tracker and regenerate ROADMAP.{md,json}
    ws_tracker.cmd_sync()
    tracker = read_json(TRACKER_PATH)
    tracker["active_exchange"] = {
        "batch_label": b_label,
        "pass_label": p_label,
        "family": summary.get("family"),
        "snapshot_dir": workspace_rel(snapshot_dir),
        "feedback_zip": workspace_rel(fb_zip),
        "activated_utc": manifest_base["activated_utc"],
    }
    write_json_workspace(TRACKER_PATH, tracker)
    ws_tracker.cmd_sync()

    return {
        "ok": True,
        "batch_label": b_label,
        "pass_label": p_label,
        "snapshot_dir": workspace_rel(snapshot_dir),
        "review_images": len(copied_pngs),
        "upload_zip": workspace_rel(upload_zip),
        "feedback_zip_bytes": zip_info["bytes"],
        "feedback_zip_sha256": zip_info["sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", help="Batch label, e.g. batch-0003")
    parser.add_argument("--pass", dest="pass_label", help="Pass label, e.g. pass-02")
    parser.add_argument("--snapshot", help="Explicit workspace snapshot directory")
    parser.add_argument("--rebuild-zip", action="store_true", help="Rebuild compact WebP feedback ZIP before activating")
    args = parser.parse_args()

    if args.snapshot:
        snap_dir = resolve_workspace_cli_path(args.snapshot)
    elif args.batch and args.pass_label:
        snap_dir = _find_snapshot_for_batch_pass(args.batch, args.pass_label)
    else:
        raise ValueError("Provide either --snapshot or both --batch and --pass")

    out = activate_snapshot(snap_dir, rebuild_zip=args.rebuild_zip)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
