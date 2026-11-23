"""Isolated Blender pass runner & audit packager for workspace/.

Reads top-level source/templates/scripts strictly read-only.
Writes ALL outputs exclusively inside workspace/batches/<FAMILY>/pass-NN/.
Never modifies top-level poses/, snapshots/, tracking/, review/, or upload/.

Usage:
  python workspace/scripts/ws_run_pass.py --pass-dir workspace/batches/UFDG/pass-01 --dry-run
  python workspace/scripts/ws_run_pass.py --pass-dir workspace/batches/UFDG/pass-01 --blender "<BLENDER_EXE>" --save-blend
  python workspace/scripts/ws_run_pass.py --pass-dir workspace/batches/UFDG/pass-01 --export-audit-zip
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from ws_common import (
    LIBRARY_ROOT,
    ensure_in_workspace,
    pose_common,
    read_json,
    read_library_authority,
    sha256_bytes,
    sha256_file,
    utc_now_iso,
    workspace_rel,
    write_json_workspace,
)
import ws_tracker


def resolve_pass_dir(raw: Path | str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        candidate_lib = (LIBRARY_ROOT / p).resolve()
        if candidate_lib.is_relative_to((LIBRARY_ROOT / "workspace").resolve()):
            p = candidate_lib
    return ensure_in_workspace(p)


def validate_pass_packages(pass_dir: Path) -> list[dict]:
    """Validate every pose package ZIP in packages/ against top-level dependencies."""
    pkg_dir = ensure_in_workspace(pass_dir / "packages")
    if not pkg_dir.is_dir():
        raise FileNotFoundError(f"Missing packages/ directory in {pass_dir}")

    plan_path = pass_dir / "plan.json"
    ordered_zips: list[Path] = []
    if plan_path.is_file():
        plan = read_json(plan_path)
        for item in plan.get("poses", []):
            zname = Path(item["package"]).name
            zpath = ensure_in_workspace(pkg_dir / zname)
            if not zpath.is_file():
                raise FileNotFoundError(f"Planned package missing: {zpath}")
            ordered_zips.append(zpath)
    else:
        ordered_zips = sorted(pkg_dir.glob("*.zip"))

    if not ordered_zips:
        raise ValueError(f"No pose package ZIPs found in {pkg_dir}")

    validated = []
    for zpath in ordered_zips:
        manifest, data = pose_common.load_package(zpath, validate_dependencies=True)
        validated.append(
            {
                "pose_id": manifest["pose_id"],
                "zip_path": zpath,
                "zip_rel": workspace_rel(zpath),
                "zip_sha256": sha256_file(zpath),
                "package_timestamp_utc": manifest["package_timestamp_utc"],
                "data": data,
            }
        )
    return validated


def run_pass(
    pass_dir: Path,
    blender: str | None = None,
    dry_run: bool = False,
    save_blend: bool = True,
) -> dict:
    pass_dir = ensure_in_workspace(pass_dir)
    auth = read_library_authority()
    validated = validate_pass_packages(pass_dir)

    if dry_run:
        return {
            "ok": True,
            "mode": "dry_run",
            "pass_dir": workspace_rel(pass_dir),
            "validated_packages": [
                {
                    "pose_id": v["pose_id"],
                    "zip": v["zip_rel"],
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

    renders_root = ensure_in_workspace(pass_dir / "renders")
    review_root = ensure_in_workspace(pass_dir / "review")
    renders_root.mkdir(parents=True, exist_ok=True)
    if review_root.exists():
        shutil.rmtree(review_root)
    review_root.mkdir(parents=True, exist_ok=True)

    builder_script = (LIBRARY_ROOT / "scripts" / "blender_build.py").resolve()
    results = []

    for item in validated:
        pose_id = item["pose_id"]
        pose_out = ensure_in_workspace(renders_root / pose_id)
        inputs_dir = ensure_in_workspace(pose_out / "inputs")
        previews_dir = ensure_in_workspace(pose_out / "previews")
        inputs_dir.mkdir(parents=True, exist_ok=True)
        previews_dir.mkdir(parents=True, exist_ok=True)

        # Unpack verified JSON inputs from package ZIP into sandbox renders/<POSE_ID>/inputs/
        with zipfile.ZipFile(item["zip_path"], "r") as zf:
            for name in zf.namelist():
                out_file = ensure_in_workspace(inputs_dir / name)
                out_file.write_bytes(zf.read(name))

        render_cfg = item["data"].get("render-config.json")
        settings = {
            "pose_id": pose_id,
            "output": str(pose_out),
            "template_file": str(auth["appearance_path"]),
            "fallback_template": str(auth["template_path"]),
            "save_blend": bool(save_blend),
            "render_config": render_cfg,
        }
        settings_path = write_json_workspace(pose_out / "build-settings.json", settings)

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
        log_path = ensure_in_workspace(pose_out / "build.log")
        log_path.write_text(
            f"CMD: {' '.join(cmd)}\nEXIT: {proc.returncode}\n\n--- STDOUT ---\n{proc.stdout}\n\n--- STDERR ---\n{proc.stderr}\n",
            encoding="utf-8",
        )

        result_path = pose_out / "blender-result.json"
        b_res = read_json(result_path) if result_path.is_file() else {"rendered": False, "issues": []}

        copied_views = []
        for png in sorted(previews_dir.glob("*.png")):
            dest_png = ensure_in_workspace(review_root / f"{pose_id}_{png.name}")
            shutil.copy2(png, dest_png)
            copied_views.append(dest_png.name)

        results.append(
            {
                "pose_id": pose_id,
                "zip": item["zip_rel"],
                "zip_sha256": item["zip_sha256"],
                "exit_code": proc.returncode,
                "rendered": bool(b_res.get("rendered")),
                "issue_count": len(b_res.get("issues", [])),
                "issues": b_res.get("issues", []),
                "previews": copied_views,
                "render_dir": workspace_rel(pose_out),
                "scene_blend_saved": (pose_out / "scene.blend").is_file(),
            }
        )

    summary = {
        "schema_version": 1,
        "kind": "spose_workspace_pass_summary",
        "pass_dir": workspace_rel(pass_dir),
        "run_utc": utc_now_iso(),
        "blender_executable": str(blender_exe),
        "pose_count": len(results),
        "rendered_count": sum(1 for r in results if r["rendered"]),
        "results": results,
    }
    summary_path = write_json_workspace(pass_dir / "pass-summary.json", summary)
    sync_out = ws_tracker.cmd_sync()
    return {
        "ok": True,
        "mode": "rendered",
        "pass_summary": workspace_rel(summary_path),
        "pose_count": summary["pose_count"],
        "rendered_count": summary["rendered_count"],
        "results": [
            {
                "pose_id": r["pose_id"],
                "rendered": r["rendered"],
                "exit_code": r["exit_code"],
                "issue_count": r["issue_count"],
                "previews": len(r["previews"]),
            }
            for r in results
        ],
        "tracker_sync": sync_out,
    }


def export_audit_zip(pass_dir: Path, prefer_webp: bool = True) -> dict:
    """Create a self-contained compact audit-bundle.zip inside the workspace pass folder."""
    pass_dir = ensure_in_workspace(pass_dir)
    if str(LIBRARY_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(LIBRARY_ROOT / "scripts"))
    from compress_images import encode_verified

    payloads: dict[str, bytes] = {}
    warnings: list[str] = []

    for fn in ("plan.json", "pass-summary.json", "AUDIT.md"):
        p = pass_dir / fn
        if p.is_file():
            payloads[fn] = p.read_bytes()

    pkg_dir = pass_dir / "packages"
    if pkg_dir.is_dir():
        for z in sorted(pkg_dir.glob("*.zip")):
            payloads[f"packages/{z.name}"] = z.read_bytes()

    renders_dir = pass_dir / "renders"
    image_count = 0
    if renders_dir.is_dir():
        for pose_dir in sorted(p for p in renders_dir.iterdir() if p.is_dir()):
            pid = pose_dir.name
            for fn in ("blender-result.json", "build-settings.json", "build.log"):
                f = pose_dir / fn
                if f.is_file():
                    payloads[f"renders/{pid}/{fn}"] = f.read_bytes()
            inp = pose_dir / "inputs"
            if inp.is_dir():
                for jf in sorted(inp.glob("*.json")):
                    payloads[f"renders/{pid}/inputs/{jf.name}"] = jf.read_bytes()
            pre = pose_dir / "previews"
            if pre.is_dir():
                for png in sorted(pre.glob("*.png")):
                    try:
                        blob, ext, _info = encode_verified(png, "webp" if prefer_webp else "original-png")
                    except (RuntimeError, ImportError) as exc:
                        warnings.append(f"{pid}/{png.name}: {exc}; kept PNG")
                        blob, ext, _info = encode_verified(png, "original-png")
                    payloads[f"renders/{pid}/images/{png.stem}{ext}"] = blob
                    image_count += 1

    manifest = {
        "schema_version": 1,
        "kind": "spose_workspace_audit_bundle",
        "non_authoritative": True,
        "pass_dir": workspace_rel(pass_dir),
        "created_utc": utc_now_iso(),
        "image_count": image_count,
        "warnings": warnings,
        "members_sha256": {k: sha256_bytes(v) for k, v in sorted(payloads.items())},
    }
    payloads["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    out_zip = ensure_in_workspace(pass_dir / "audit-bundle.zip")
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(payloads):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, payloads[name])

    ws_tracker.cmd_sync()
    return {
        "ok": True,
        "audit_bundle_zip": workspace_rel(out_zip),
        "bytes": out_zip.stat().st_size,
        "sha256": sha256_file(out_zip),
        "image_count": image_count,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass-dir", required=True, help="Path inside workspace/batches/<FAMILY>/pass-NN")
    parser.add_argument("--blender", help="Path to Blender 5.2 executable")
    parser.add_argument("--dry-run", action="store_true", help="Validate packages only; do not launch Blender")
    parser.add_argument("--no-save-blend", action="store_true", help="Skip saving scene.blend in renders/")
    parser.add_argument("--export-audit-zip", action="store_true", help="Build compact audit-bundle.zip")
    args = parser.parse_args()

    pass_dir = resolve_pass_dir(args.pass_dir)
    if args.export_audit_zip:
        out = export_audit_zip(pass_dir)
    else:
        out = run_pass(
            pass_dir=pass_dir,
            blender=args.blender,
            dry_run=args.dry_run,
            save_blend=not args.no_save_blend,
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
