"""Workspace-only backward-roadmap tracker and Markdown roadmap generator.

Maintains workspace/workspace-tracker.json and workspace/WORKSPACE-ROADMAP.md
without touching any top-level tracking, roadmap, or pose files.

Commands:
  python workspace/scripts/ws_tracker.py init
  python workspace/scripts/ws_tracker.py sync
  python workspace/scripts/ws_tracker.py status
  python workspace/scripts/ws_tracker.py mark-audit --family UFDG --pass pass-01 --score 7.0 --notes "..."
  python workspace/scripts/ws_tracker.py mark-promoted --family UFDG --pass pass-01 --batch-id batch-0002 --pass-id pass-01 --snapshot snapshots/...
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path

from ws_common import (
    WORKSPACE_ROOT,
    ensure_in_workspace,
    read_json,
    read_top_level_built_poses,
    read_v00_catalog,
    sha256_file,
    utc_now_iso,
    workspace_rel,
    write_json_workspace,
    write_text_workspace,
)

TRACKER_PATH = WORKSPACE_ROOT / "workspace-tracker.json"
ROADMAP_MD_PATH = WORKSPACE_ROOT / "WORKSPACE-ROADMAP.md"
BATCHES_DIR = WORKSPACE_ROOT / "batches"


def backward_families(v00_rows: list[dict]) -> list[dict]:
    """Group V00 rows by family in exact reverse catalog order (UFDG -> UADG -> ... -> DOGG)."""
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in v00_rows:
        fam = row["family_id"]
        grouped.setdefault(fam, []).append(row)
    items = list(grouped.items())
    items.reverse()
    return [{"family_id": fam, "poses": poses} for fam, poses in items]


def load_or_create_tracker(auth: dict) -> dict:
    if TRACKER_PATH.is_file():
        return read_json(TRACKER_PATH)
    now = utc_now_iso()
    return {
        "schema_version": 1,
        "kind": "spose_workspace_backward_tracker",
        "non_authoritative_notice": (
            "Experimental workspace-only tracker. Does not alter top-level tracking/progress.sqlite or ROADMAP.md."
        ),
        "direction": "backward_from_roadmap_end",
        "catalog_reference": {
            "source_id": auth["source_id"],
            "source_revision": auth["source_revision"],
            "source_checkpoint": auth["source_checkpoint"],
            "catalog_sha256": auth["catalog_sha256"],
            "pair_id": auth["pair_id"],
            "pair_version": auth["pair_version"],
            "template_sha256": auth["template_sha256"],
        },
        "created_utc": now,
        "updated_utc": now,
        "families": {},
    }


def scan_workspace_batches(tracker: dict) -> dict:
    """Discover pass folders under workspace/batches/<FAMILY>/pass-NN/ and sync non-destructively."""
    BATCHES_DIR.mkdir(parents=True, exist_ok=True)
    families_state = tracker.setdefault("families", {})

    for fam_dir in sorted(p for p in BATCHES_DIR.iterdir() if p.is_dir()):
        family_id = fam_dir.name.upper()
        fam_rec = families_state.setdefault(family_id, {"passes": {}})
        passes_rec = fam_rec.setdefault("passes", {})

        for pass_dir in sorted(p for p in fam_dir.iterdir() if p.is_dir() and p.name.startswith("pass-")):
            pass_id = pass_dir.name
            existing = passes_rec.get(pass_id, {})
            pkg_dir = pass_dir / "packages"
            packages = []
            if pkg_dir.is_dir():
                for z in sorted(pkg_dir.glob("*.zip")):
                    packages.append(
                        {
                            "file": workspace_rel(z),
                            "pose_id": z.name.split("_")[0],
                            "sha256": sha256_file(z),
                            "bytes": z.stat().st_size,
                        }
                    )

            renders_dir = pass_dir / "renders"
            renders = {}
            if renders_dir.is_dir():
                for pose_dir in sorted(p for p in renders_dir.iterdir() if p.is_dir()):
                    res_path = pose_dir / "blender-result.json"
                    previews_dir = pose_dir / "previews"
                    png_count = len(list(previews_dir.glob("*.png"))) if previews_dir.is_dir() else 0
                    if res_path.is_file():
                        res = read_json(res_path)
                        renders[pose_dir.name] = {
                            "rendered": bool(res.get("rendered")),
                            "issue_count": len(res.get("issues", [])),
                            "preview_count": png_count,
                            "scene_blend_present": (pose_dir / "scene.blend").is_file(),
                            "result_file": workspace_rel(res_path),
                        }
                    else:
                        renders[pose_dir.name] = {
                            "rendered": False,
                            "issue_count": None,
                            "preview_count": png_count,
                            "scene_blend_present": (pose_dir / "scene.blend").is_file(),
                            "result_file": None,
                        }

            plan_file = pass_dir / "plan.json"
            audit_file = pass_dir / "AUDIT.md"
            summary_file = pass_dir / "pass-summary.json"
            audit_zip = pass_dir / "audit-bundle.zip"

            rendered_poses = [pid for pid, info in renders.items() if info.get("rendered")]
            if existing.get("promoted"):
                status = "promoted"
            elif existing.get("audit_completed"):
                status = "audited"
            elif rendered_poses:
                status = "rendered"
            elif packages:
                status = "packages_ready"
            else:
                status = "scaffolded"

            passes_rec[pass_id] = {
                "pass_dir": workspace_rel(pass_dir),
                "status": status,
                "plan_file": workspace_rel(plan_file) if plan_file.is_file() else None,
                "audit_md": workspace_rel(audit_file) if audit_file.is_file() else None,
                "pass_summary": workspace_rel(summary_file) if summary_file.is_file() else None,
                "audit_bundle_zip": workspace_rel(audit_zip) if audit_zip.is_file() else None,
                "package_count": len(packages),
                "packages": packages,
                "rendered_count": len(rendered_poses),
                "renders": renders,
                "audit_completed": bool(existing.get("audit_completed", False)),
                "audit_score": existing.get("audit_score"),
                "audit_notes": existing.get("audit_notes"),
                "promoted": bool(existing.get("promoted", False)),
                "promotion_ref": existing.get("promotion_ref"),
            }

    tracker["updated_utc"] = utc_now_iso()
    return tracker


def render_roadmap_markdown(tracker: dict, rev_families: list[dict], top_built: set[str]) -> str:
    total_poses = sum(len(f["poses"]) for f in rev_families)
    ws_rendered_poses: set[str] = set()
    ws_promoted_poses: set[str] = set()
    for fam_rec in tracker.get("families", {}).values():
        for pass_rec in fam_rec.get("passes", {}).values():
            for pid, info in pass_rec.get("renders", {}).items():
                if info.get("rendered"):
                    ws_rendered_poses.add(pid)
                    if pass_rec.get("promoted"):
                        ws_promoted_poses.add(pid)

    lines = [
        "# SPOSE Workspace — Backward V00 Experimental Roadmap",
        "",
        "> **Experimental workspace view only (auto-generated by `workspace/scripts/ws_tracker.py`).**",
        "> Top-level `ROADMAP.md` and `tracking/progress.sqlite` remain untouched until explicit user promotion.",
        "",
        f"**Direction:** Reverse catalog order (`UFDG` -> `UADG` -> `USDG` -> ... -> `DOGG`)  ",
        f"**Catalog:** `{tracker['catalog_reference']['source_id']}/{tracker['catalog_reference']['source_revision']}` "
        f"· {len(rev_families)} families · {total_poses} V00 bases  ",
        f"**Workspace rendered:** {len(ws_rendered_poses)}/{total_poses} · "
        f"**Promoted from workspace:** {len(ws_promoted_poses)} · "
        f"**Main library built (read-only ref):** {len(top_built)}/{total_poses}  ",
        f"**Updated (UTC):** `{tracker['updated_utc']}`",
        "",
        "## Family Order (Backward Queue)",
        "",
        "| Order | Family | V00 Total | Workspace Passes | WS Rendered | WS Promoted | Main Lib Built | Status |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]

    for idx, fam in enumerate(rev_families, 1):
        fid = fam["family_id"]
        pose_ids = [r["pose_id"] for r in fam["poses"]]
        fam_rec = tracker.get("families", {}).get(fid, {})
        passes = fam_rec.get("passes", {})
        fam_ws_rendered = {
            pid
            for pr in passes.values()
            for pid, info in pr.get("renders", {}).items()
            if info.get("rendered")
        }
        fam_ws_promoted = {
            pid
            for pr in passes.values()
            if pr.get("promoted")
            for pid, info in pr.get("renders", {}).items()
            if info.get("rendered")
        }
        main_count = sum(1 for pid in pose_ids if pid in top_built)

        if fam_ws_promoted and len(fam_ws_promoted) == len(pose_ids):
            state = "promoted"
        elif passes:
            latest_key = sorted(passes.keys())[-1]
            state = f"{latest_key}:{passes[latest_key]['status']}"
        elif main_count > 0:
            state = "active_in_main_lib"
        else:
            state = "queued"

        lines.append(
            f"| {idx} | `{fid}` | {len(pose_ids)} | {len(passes)} | "
            f"{len(fam_ws_rendered)} | {len(fam_ws_promoted)} | {main_count} | `{state}` |"
        )

    lines.extend(["", "## Per-Family Pose Checklist (Backward Order)", ""])
    for fam in rev_families:
        fid = fam["family_id"]
        fam_rec = tracker.get("families", {}).get(fid, {})
        passes = fam_rec.get("passes", {})
        pass_summary = ", ".join(f"`{k}` ({v['status']})" for k, v in sorted(passes.items())) or "none"
        lines.append(f"### {fid} — {len(fam['poses'])} V00 poses (workspace passes: {pass_summary})")
        lines.append("")
        for row in fam["poses"]:
            pid = row["pose_id"]
            name = row.get("pose_name", "")
            gate = row.get("generation_gate", "UNKNOWN")
            # Determine latest workspace state for this pose
            ws_tag = "not_started"
            checked = False
            for pk in sorted(passes.keys()):
                pr = passes[pk]
                rinfo = pr.get("renders", {}).get(pid)
                if rinfo and rinfo.get("rendered"):
                    checked = True
                    ws_tag = f"{pk} rendered ({rinfo.get('issue_count', 0)} issues)"
                    if pr.get("promoted"):
                        ws_tag += " [PROMOTED]"
                elif any(p.get("pose_id") == pid for p in pr.get("packages", [])):
                    ws_tag = f"{pk} packaged"
            main_note = " · main_lib: `built`" if pid in top_built else ""
            box = "x" if checked else " "
            lines.append(f"- [{box}] `{pid}` — {name} · ws: `{ws_tag}`{main_note} · source `{gate}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def cmd_sync() -> dict:
    auth, v00_rows = read_v00_catalog()
    rev_fams = backward_families(v00_rows)
    top_built = read_top_level_built_poses()
    tracker = load_or_create_tracker(auth)
    tracker = scan_workspace_batches(tracker)
    write_json_workspace(TRACKER_PATH, tracker)
    md = render_roadmap_markdown(tracker, rev_fams, top_built)
    write_text_workspace(ROADMAP_MD_PATH, md)
    return {
        "ok": True,
        "tracker": str(TRACKER_PATH),
        "roadmap": str(ROADMAP_MD_PATH),
        "families_total": len(rev_fams),
        "v00_total": len(v00_rows),
        "workspace_families_active": len(tracker.get("families", {})),
        "next_backward_family": next(
            (
                f["family_id"]
                for f in rev_fams
                if f["family_id"] not in tracker.get("families", {})
                and not any(r["pose_id"] in top_built for r in f["poses"])
            ),
            None,
        ),
    }


def cmd_status() -> dict:
    auth, v00_rows = read_v00_catalog()
    rev_fams = backward_families(v00_rows)
    top_built = read_top_level_built_poses()
    tracker = load_or_create_tracker(auth)
    active = {}
    for fid, frec in sorted(tracker.get("families", {}).items()):
        active[fid] = {
            pk: {
                "status": pr.get("status"),
                "packages": pr.get("package_count", 0),
                "rendered": pr.get("rendered_count", 0),
                "audit_score": pr.get("audit_score"),
                "promoted": pr.get("promoted", False),
            }
            for pk, pr in sorted(frec.get("passes", {}).items())
        }
    next_fam = next(
        (
            f["family_id"]
            for f in rev_fams
            if f["family_id"] not in tracker.get("families", {})
            and not any(r["pose_id"] in top_built for r in f["poses"])
        ),
        None,
    )
    return {
        "ok": True,
        "direction": "backward_from_roadmap_end",
        "tracker_exists": TRACKER_PATH.is_file(),
        "roadmap_exists": ROADMAP_MD_PATH.is_file(),
        "families_total": len(rev_fams),
        "v00_total": len(v00_rows),
        "top_level_built_count": len(top_built),
        "next_backward_family": next_fam,
        "workspace_active": active,
    }


def cmd_mark_audit(family: str, pass_id: str, score: float | None, notes: str) -> dict:
    auth, _ = read_v00_catalog()
    tracker = scan_workspace_batches(load_or_create_tracker(auth))
    fid = family.upper()
    if fid not in tracker.get("families", {}) or pass_id not in tracker["families"][fid].get("passes", {}):
        raise KeyError(f"Workspace pass not found: {fid}/{pass_id}")
    if score is not None and not (0.0 <= score <= 10.0):
        raise ValueError("Score must be between 0 and 10")
    pr = tracker["families"][fid]["passes"][pass_id]
    pr["audit_completed"] = True
    pr["audit_score"] = score
    pr["audit_notes"] = notes
    if not pr.get("promoted"):
        pr["status"] = "audited"
    write_json_workspace(TRACKER_PATH, tracker)
    return cmd_sync()


def cmd_mark_promoted(family: str, pass_id: str, batch_id: str, official_pass: str, snapshot: str) -> dict:
    auth, _ = read_v00_catalog()
    tracker = scan_workspace_batches(load_or_create_tracker(auth))
    fid = family.upper()
    if fid not in tracker.get("families", {}) or pass_id not in tracker["families"][fid].get("passes", {}):
        raise KeyError(f"Workspace pass not found: {fid}/{pass_id}")
    pr = tracker["families"][fid]["passes"][pass_id]
    pr["promoted"] = True
    pr["status"] = "promoted"
    pr["promotion_ref"] = {
        "batch_id": batch_id,
        "pass_id": official_pass,
        "snapshot": snapshot,
        "promoted_utc": utc_now_iso(),
    }
    write_json_workspace(TRACKER_PATH, tracker)
    return cmd_sync()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="Initialize workspace tracker and backward roadmap")
    sub.add_parser("sync", help="Rescan workspace/batches and regenerate tracker & roadmap")
    sub.add_parser("status", help="Show workspace tracker summary")

    aud = sub.add_parser("mark-audit", help="Record advisory visual audit result for a workspace pass")
    aud.add_argument("--family", required=True)
    aud.add_argument("--pass", dest="pass_id", required=True)
    aud.add_argument("--score", type=float)
    aud.add_argument("--notes", required=True)

    pro = sub.add_parser("mark-promoted", help="Record official promotion provenance for a workspace pass")
    pro.add_argument("--family", required=True)
    pro.add_argument("--pass", dest="pass_id", required=True)
    pro.add_argument("--batch-id", required=True)
    pro.add_argument("--pass-id", dest="official_pass", required=True)
    pro.add_argument("--snapshot", required=True)

    args = parser.parse_args()
    if args.cmd in ("init", "sync"):
        out = cmd_sync()
    elif args.cmd == "status":
        out = cmd_status()
    elif args.cmd == "mark-audit":
        out = cmd_mark_audit(args.family, args.pass_id, args.score, args.notes)
    else:
        out = cmd_mark_promoted(args.family, args.pass_id, args.batch_id, args.official_pass, args.snapshot)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
