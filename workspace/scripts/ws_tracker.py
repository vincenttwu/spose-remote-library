"""Workspace-only sequential batch/pass registry & derived roadmap generator.

Mirrors the top-level library authority model strictly inside workspace/:
  - Authority: workspace/tracking/workspace-tracker.json
  - Derived:   workspace/ROADMAP.md and workspace/ROADMAP.json
  - Scans:     workspace/poses/, workspace/snapshots/, workspace/batches/, workspace/incoming/

Supports sequential 5-pose batches (batch-0001, batch-0002, ...) across families of any size
(including 20+ pose families like OFEL split cleanly into multiple sequential batches).

Commands:
  python workspace/scripts/ws_tracker.py init
  python workspace/scripts/ws_tracker.py sync
  python workspace/scripts/ws_tracker.py status
  python workspace/scripts/ws_tracker.py next-batch [--size 5]
  python workspace/scripts/ws_tracker.py mark-audit --batch batch-0003 --pass pass-02 --score 6.88 --notes "..."
  python workspace/scripts/ws_tracker.py mark-promoted --batch batch-0001 --pass pass-03 --official-batch batch-0002 --official-pass pass-01 --snapshot snapshots/...
"""
from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path

from ws_common import (
    BATCHES_DIR,
    INCOMING_DIR,
    POSES_DIR,
    ROADMAP_JSON_PATH,
    ROADMAP_MD_PATH,
    SNAPSHOTS_DIR,
    TRACKER_PATH,
    ensure_workspace_dirs,
    list_pose_revisions,
    normalize_batch_label,
    normalize_pass_label,
    read_json,
    read_top_level_built_poses,
    read_v00_catalog,
    utc_now_iso,
    workspace_rel,
    write_json_workspace,
    write_text_workspace,
)


def backward_families(v00_rows: list[dict]) -> list[dict]:
    """Group V00 rows by family in exact reverse catalog order (UFDG -> UADG -> USDG -> OFEL -> ... -> DOGG)."""
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in v00_rows:
        fam = row["family_id"]
        grouped.setdefault(fam, []).append(row)
    items = list(grouped.items())
    items.reverse()
    return [{"family_id": fam, "poses": poses} for fam, poses in items]


def load_or_create_tracker(auth: dict) -> dict:
    if TRACKER_PATH.is_file():
        doc = read_json(TRACKER_PATH)
        if doc.get("schema_version") == 2 and doc.get("kind") == "spose_workspace_registry":
            return doc
    now = utc_now_iso()
    return {
        "schema_version": 2,
        "kind": "spose_workspace_registry",
        "non_authoritative_notice": (
            "Experimental workspace-only registry mirroring top-level layout. "
            "Never modifies top-level tracking/progress.sqlite, ROADMAP.*, poses/, or snapshots/."
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
        "active_exchange": None,
        "batches": {},
        "poses": {},
    }


def _scan_poses(auth: dict) -> dict:
    """Scan canonical workspace/poses/<POSE_ID>/<PAIR_ID>/<PAIR_VERSION>/rNNN/ tree."""
    pair_id = auth["pair_id"]
    pair_ver = auth["pair_version"]
    poses_index: dict[str, dict] = {}
    if not POSES_DIR.is_dir():
        return poses_index
    for pose_dir in sorted(p for p in POSES_DIR.iterdir() if p.is_dir()):
        pid = pose_dir.name
        revs = list_pose_revisions(pid, pair_id, pair_ver)
        if not revs:
            continue
        rev_entries = {}
        latest_rev = None
        for rdir in revs:
            rname = rdir.name
            latest_rev = rname
            res_path = rdir / "blender-result.json"
            previews_dir = rdir / "previews"
            png_count = len(list(previews_dir.glob("*.png"))) if previews_dir.is_dir() else 0
            manifest_path = rdir / "inputs" / "manifest.json"
            pkg_ts = read_json(manifest_path).get("package_timestamp_utc") if manifest_path.is_file() else None
            if res_path.is_file():
                res = read_json(res_path)
                rendered = bool(res.get("rendered"))
                issue_count = len(res.get("issues", []))
            else:
                rendered = False
                issue_count = None
            rev_entries[rname] = {
                "revision": rname,
                "path": workspace_rel(rdir),
                "package_timestamp_utc": pkg_ts,
                "rendered": rendered,
                "issue_count": issue_count,
                "preview_count": png_count,
                "scene_blend_present": (rdir / "scene.blend").is_file(),
                "result_file": workspace_rel(res_path) if res_path.is_file() else None,
            }
        poses_index[pid] = {
            "pose_id": pid,
            "pair_id": pair_id,
            "pair_version": pair_ver,
            "latest_revision": latest_rev,
            "revision_count": len(rev_entries),
            "built": any(v["rendered"] for v in rev_entries.values()),
            "revisions": rev_entries,
        }
    return poses_index


def _scan_batches_and_snapshots(tracker: dict) -> dict:
    """Synchronize workspace/batches/*.json and workspace/snapshots/* non-destructively."""
    batches = tracker.setdefault("batches", {})

    # 1. Discover batch plans in workspace/batches/BATCH-XXXX-PASS-YY.json
    if BATCHES_DIR.is_dir():
        for plan_file in sorted(BATCHES_DIR.glob("*.json")):
            try:
                plan = read_json(plan_file)
            except Exception:
                continue
            b_raw = plan.get("batch_label") or plan.get("batch_id")
            p_raw = plan.get("pass_label")
            if not b_raw or not p_raw:
                continue
            b_label = normalize_batch_label(b_raw)
            p_label = normalize_pass_label(p_raw)
            brec = batches.setdefault(
                b_label,
                {
                    "batch_label": b_label,
                    "family": plan.get("family"),
                    "pose_ids": [item["pose_id"] for item in plan.get("poses", [])],
                    "passes": {},
                },
            )
            if not brec.get("family") and plan.get("family"):
                brec["family"] = plan.get("family")
            if not brec.get("pose_ids") and plan.get("poses"):
                brec["pose_ids"] = [item["pose_id"] for item in plan.get("poses", [])]

            prec = brec.setdefault("passes", {}).setdefault(
                p_label,
                {
                    "pass_label": p_label,
                    "status": "planned",
                    "plan_file": workspace_rel(plan_file),
                    "snapshot_dir": None,
                    "batch_summary": None,
                    "audit_md": None,
                    "feedback_zip": None,
                    "pose_count": len(plan.get("poses", [])),
                    "rendered_count": 0,
                    "pose_revisions": {},
                    "audit_completed": False,
                    "audit_score": None,
                    "audit_notes": None,
                    "promoted": False,
                    "promotion_ref": None,
                },
            )
            prec["plan_file"] = workspace_rel(plan_file)
            prec["pose_count"] = len(plan.get("poses", []))

    # 2. Discover snapshots in workspace/snapshots/<batch>-<pass>_<ts>/
    if SNAPSHOTS_DIR.is_dir():
        for snap_dir in sorted(p for p in SNAPSHOTS_DIR.iterdir() if p.is_dir()):
            summary_path = snap_dir / "batch-summary.json"
            if not summary_path.is_file():
                continue
            summary = read_json(summary_path)
            b_label = normalize_batch_label(summary["batch_label"])
            p_label = normalize_pass_label(summary["pass_label"])
            brec = batches.setdefault(
                b_label,
                {
                    "batch_label": b_label,
                    "family": summary.get("family"),
                    "pose_ids": [r["pose_id"] for r in summary.get("results", [])],
                    "passes": {},
                },
            )
            if not brec.get("family") and summary.get("family"):
                brec["family"] = summary.get("family")
            if not brec.get("pose_ids") and summary.get("results"):
                brec["pose_ids"] = [r["pose_id"] for r in summary.get("results", [])]

            existing = brec.setdefault("passes", {}).get(p_label, {})
            audit_md = snap_dir / "AUDIT.md"
            zips = sorted(snap_dir.glob("*.zip"))
            fb_zip = zips[-1] if zips else None
            pose_revs = {
                r["pose_id"]: {
                    "revision": r.get("revision"),
                    "revision_path": r.get("revision_path"),
                    "package": r.get("package"),
                    "package_sha256": r.get("package_sha256"),
                    "rendered": bool(r.get("rendered")),
                    "issue_count": r.get("issue_count"),
                    "reused_existing_package": bool(r.get("reused_existing_package", False)),
                }
                for r in summary.get("results", [])
            }
            rendered_count = sum(1 for v in pose_revs.values() if v["rendered"])

            if existing.get("promoted"):
                status = "promoted"
            elif existing.get("audit_completed"):
                status = "audited"
            elif rendered_count > 0:
                status = "rendered"
            else:
                status = existing.get("status", "planned")

            brec["passes"][p_label] = {
                "pass_label": p_label,
                "status": status,
                "plan_file": existing.get("plan_file") or summary.get("plan_file"),
                "snapshot_dir": workspace_rel(snap_dir),
                "run_utc": summary.get("run_utc"),
                "batch_summary": workspace_rel(summary_path),
                "audit_md": workspace_rel(audit_md) if audit_md.is_file() else None,
                "feedback_zip": workspace_rel(fb_zip) if fb_zip else None,
                "pose_count": len(pose_revs) or existing.get("pose_count", 0),
                "rendered_count": rendered_count,
                "pose_revisions": pose_revs,
                "audit_completed": bool(existing.get("audit_completed", False)),
                "audit_score": existing.get("audit_score"),
                "audit_notes": existing.get("audit_notes"),
                "promoted": bool(existing.get("promoted", False)),
                "promotion_ref": existing.get("promotion_ref"),
            }

    return tracker


def compute_next_batch(tracker: dict, rev_families: list[dict], top_built: set[str], size: int = 5) -> dict:
    """Compute next sequential batch label and next up-to-5 unstarted backward V00 poses."""
    existing_nums = []
    for bl in tracker.get("batches", {}):
        m = re.fullmatch(r"batch-(\d+)", bl)
        if m:
            existing_nums.append(int(m.group(1)))
    next_num = (max(existing_nums) + 1) if existing_nums else 1
    next_label = f"batch-{next_num:04d}"

    ws_poses = set(tracker.get("poses", {}).keys())
    # Also include poses already planned in any batch
    for brec in tracker.get("batches", {}).values():
        ws_poses.update(brec.get("pose_ids", []))

    for fam in rev_families:
        fid = fam["family_id"]
        remaining = [r for r in fam["poses"] if r["pose_id"] not in ws_poses and r["pose_id"] not in top_built]
        if remaining:
            slice_rows = remaining[:size]
            return {
                "next_batch_label": next_label,
                "family": fid,
                "family_total_v00": len(fam["poses"]),
                "family_remaining_after_this": max(0, len(remaining) - len(slice_rows)),
                "pose_ids": [r["pose_id"] for r in slice_rows],
                "poses": [{"pose_id": r["pose_id"], "pose_name": r.get("pose_name", "")} for r in slice_rows],
            }
    return {"next_batch_label": next_label, "family": None, "pose_ids": [], "poses": []}


def build_roadmap_json(tracker: dict, rev_families: list[dict], top_built: set[str]) -> dict:
    poses_map = tracker.get("poses", {})
    v00_entries = []
    for fam in rev_families:
        for row in fam["poses"]:
            pid = row["pose_id"]
            pinfo = poses_map.get(pid)
            v00_entries.append(
                {
                    "pose_id": pid,
                    "family_id": fam["family_id"],
                    "pose_name": row.get("pose_name", ""),
                    "generation_gate": row.get("generation_gate", "UNKNOWN"),
                    "workspace_built": bool(pinfo and pinfo.get("built")),
                    "workspace_latest_revision": pinfo.get("latest_revision") if pinfo else None,
                    "workspace_revision_count": pinfo.get("revision_count", 0) if pinfo else 0,
                    "main_library_built": pid in top_built,
                }
            )
    return {
        "schema_version": 2,
        "kind": "spose_workspace_roadmap",
        "non_authoritative": True,
        "direction": "backward_from_roadmap_end",
        "updated_utc": tracker["updated_utc"],
        "catalog_reference": tracker["catalog_reference"],
        "active_exchange": tracker.get("active_exchange"),
        "summary": {
            "families_total": len(rev_families),
            "v00_total": len(v00_entries),
            "workspace_built": sum(1 for e in v00_entries if e["workspace_built"]),
            "workspace_batches": len(tracker.get("batches", {})),
            "main_library_built": len(top_built),
        },
        "next_batch_suggestion": compute_next_batch(tracker, rev_families, top_built),
        "v00_poses": v00_entries,
    }


def render_roadmap_markdown(tracker: dict, rev_families: list[dict], top_built: set[str]) -> str:
    poses_map = tracker.get("poses", {})
    batches = tracker.get("batches", {})
    total_poses = sum(len(f["poses"]) for f in rev_families)
    ws_built_poses = {pid for pid, info in poses_map.items() if info.get("built")}
    ws_promoted_poses: set[str] = set()
    for brec in batches.values():
        for prec in brec.get("passes", {}).values():
            if prec.get("promoted"):
                ws_promoted_poses.update(prec.get("pose_revisions", {}).keys())

    next_sug = compute_next_batch(tracker, rev_families, top_built)
    active_ex = tracker.get("active_exchange")
    active_str = (
        f"`{active_ex['batch_label']}` / `{active_ex['pass_label']}` (`{active_ex['snapshot_dir']}`)"
        if isinstance(active_ex, dict)
        else "none"
    )

    lines = [
        "# SPOSE Workspace — Backward V00 Experimental Roadmap",
        "",
        "> **Derived view inside `workspace/` (auto-generated from `workspace/tracking/workspace-tracker.json`).**",
        "> Mirrors top-level `ROADMAP.md` layout. Top-level `ROADMAP.md` and `tracking/progress.sqlite` remain untouched until explicit user promotion.",
        "",
        f"**Direction:** Reverse catalog order (`UFDG` -> `UADG` -> `USDG` -> `OFEL` -> ... -> `DOGG`)  ",
        f"**Catalog:** `{tracker['catalog_reference']['source_id']}/{tracker['catalog_reference']['source_revision']}` "
        f"· {len(rev_families)} families · {total_poses} V00 bases  ",
        f"**Workspace built:** {len(ws_built_poses)}/{total_poses} across {len(batches)} sequential batches · "
        f"**Promoted:** {len(ws_promoted_poses)} · "
        f"**Main library built (read-only ref):** {len(top_built)}/{total_poses}  ",
        f"**Active workspace exchange (`review/` & `upload/`):** {active_str}  ",
        f"**Next sequential batch:** `{next_sug['next_batch_label']}` (`{next_sug['family']}`: {', '.join(next_sug['pose_ids']) or 'none'})  ",
        f"**Updated (UTC):** `{tracker['updated_utc']}`",
        "",
        "## Sequential Workspace Batches",
        "",
        "| Batch | Family | Poses | Passes | Latest Pass | Latest Score | Status | Latest Snapshot |",
        "|---|---|---:|---:|---|---:|---|---|",
    ]

    for b_label in sorted(batches.keys()):
        brec = batches[b_label]
        passes = brec.get("passes", {})
        if passes:
            lp_key = sorted(passes.keys())[-1]
            lp = passes[lp_key]
            score_str = f"{lp['audit_score']:.2f}/10" if lp.get("audit_score") is not None else "—"
            status = lp.get("status", "planned")
            snap = lp.get("snapshot_dir") or "—"
        else:
            lp_key, score_str, status, snap = "—", "—", "empty", "—"
        lines.append(
            f"| `{b_label}` | `{brec.get('family') or 'MIXED'}` | {len(brec.get('pose_ids', []))} | "
            f"{len(passes)} | `{lp_key}` | {score_str} | `{status}` | `{snap}` |"
        )

    lines.extend(
        [
            "",
            "## Family Queue (Backward Order)",
            "",
            "| Order | Family | V00 Total | WS Built | Batches | Main Lib Built | Status |",
            "|---:|---|---:|---:|---|---:|---|",
        ]
    )

    for idx, fam in enumerate(rev_families, 1):
        fid = fam["family_id"]
        pids = [r["pose_id"] for r in fam["poses"]]
        ws_cnt = sum(1 for pid in pids if pid in ws_built_poses)
        main_cnt = sum(1 for pid in pids if pid in top_built)
        fam_batches = [bl for bl, br in sorted(batches.items()) if br.get("family") == fid]
        if ws_cnt == len(pids) and pids:
            state = "all_ws_built"
        elif ws_cnt > 0:
            state = f"partial ({ws_cnt}/{len(pids)})"
        elif main_cnt > 0:
            state = "active_in_main_lib"
        else:
            state = "queued"
        b_str = ", ".join(f"`{b}`" for b in fam_batches) if fam_batches else "—"
        lines.append(
            f"| {idx} | `{fid}` | {len(pids)} | {ws_cnt} | {b_str} | {main_cnt} | `{state}` |"
        )

    lines.extend(["", "## Per-Family Pose Library Checklist (Backward Order)", ""])
    for fam in rev_families:
        fid = fam["family_id"]
        lines.append(f"### {fid} — {len(fam['poses'])} V00 poses")
        lines.append("")
        for row in fam["poses"]:
            pid = row["pose_id"]
            name = row.get("pose_name", "")
            gate = row.get("generation_gate", "UNKNOWN")
            pinfo = poses_map.get(pid)
            if pinfo and pinfo.get("built"):
                latest = pinfo["latest_revision"]
                rinfo = pinfo["revisions"][latest]
                ws_tag = f"`poses/{pid}/CPL01/v001/{latest}` ({rinfo.get('issue_count', 0)} issues)"
                box = "x"
            else:
                ws_tag = "`not_started`"
                box = " "
            main_note = " · main_lib: `built`" if pid in top_built else ""
            lines.append(f"- [{box}] `{pid}` — {name} · ws: {ws_tag}{main_note} · source `{gate}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def cmd_sync() -> dict:
    ensure_workspace_dirs()
    auth, v00_rows = read_v00_catalog()
    rev_fams = backward_families(v00_rows)
    top_built = read_top_level_built_poses()
    tracker = load_or_create_tracker(auth)
    tracker["poses"] = _scan_poses(auth)
    tracker = _scan_batches_and_snapshots(tracker)
    tracker["updated_utc"] = utc_now_iso()

    write_json_workspace(TRACKER_PATH, tracker)
    rm_json = build_roadmap_json(tracker, rev_fams, top_built)
    write_json_workspace(ROADMAP_JSON_PATH, rm_json)
    rm_md = render_roadmap_markdown(tracker, rev_fams, top_built)
    write_text_workspace(ROADMAP_MD_PATH, rm_md)

    return {
        "ok": True,
        "tracker": workspace_rel(TRACKER_PATH),
        "roadmap_md": workspace_rel(ROADMAP_MD_PATH),
        "roadmap_json": workspace_rel(ROADMAP_JSON_PATH),
        "batches_count": len(tracker["batches"]),
        "workspace_poses_built": sum(1 for p in tracker["poses"].values() if p["built"]),
        "next_batch": rm_json["next_batch_suggestion"],
    }


def cmd_status() -> dict:
    auth, v00_rows = read_v00_catalog()
    rev_fams = backward_families(v00_rows)
    top_built = read_top_level_built_poses()
    tracker = load_or_create_tracker(auth)
    summary_batches = {}
    for b_label, brec in sorted(tracker.get("batches", {}).items()):
        summary_batches[b_label] = {
            "family": brec.get("family"),
            "pose_count": len(brec.get("pose_ids", [])),
            "passes": {
                pk: {
                    "status": pr.get("status"),
                    "rendered": pr.get("rendered_count", 0),
                    "audit_score": pr.get("audit_score"),
                    "snapshot": pr.get("snapshot_dir"),
                    "promoted": pr.get("promoted", False),
                }
                for pk, pr in sorted(brec.get("passes", {}).items())
            },
        }
    return {
        "ok": True,
        "direction": "backward_from_roadmap_end",
        "v00_total": len(v00_rows),
        "workspace_poses_built": sum(1 for p in tracker.get("poses", {}).values() if p.get("built")),
        "top_level_built": len(top_built),
        "active_exchange": tracker.get("active_exchange"),
        "next_batch": compute_next_batch(tracker, rev_fams, top_built),
        "batches": summary_batches,
    }


def cmd_mark_audit(batch_label: str, pass_label: str, score: float | None, notes: str) -> dict:
    auth, _ = read_v00_catalog()
    tracker = _scan_batches_and_snapshots(load_or_create_tracker(auth))
    b_key = normalize_batch_label(batch_label)
    p_key = normalize_pass_label(pass_label)
    if b_key not in tracker.get("batches", {}) or p_key not in tracker["batches"][b_key].get("passes", {}):
        raise KeyError(f"Workspace batch/pass not found: {b_key}/{p_key}")
    if score is not None and not (0.0 <= score <= 10.0):
        raise ValueError("Score must be between 0 and 10")
    pr = tracker["batches"][b_key]["passes"][p_key]
    pr["audit_completed"] = True
    pr["audit_score"] = score
    pr["audit_notes"] = notes
    if not pr.get("promoted"):
        pr["status"] = "audited"
    write_json_workspace(TRACKER_PATH, tracker)
    return cmd_sync()


def cmd_mark_promoted(
    batch_label: str,
    pass_label: str,
    official_batch: str,
    official_pass: str,
    snapshot: str,
) -> dict:
    auth, _ = read_v00_catalog()
    tracker = _scan_batches_and_snapshots(load_or_create_tracker(auth))
    b_key = normalize_batch_label(batch_label)
    p_key = normalize_pass_label(pass_label)
    if b_key not in tracker.get("batches", {}) or p_key not in tracker["batches"][b_key].get("passes", {}):
        raise KeyError(f"Workspace batch/pass not found: {b_key}/{p_key}")
    pr = tracker["batches"][b_key]["passes"][p_key]
    pr["promoted"] = True
    pr["status"] = "promoted"
    pr["promotion_ref"] = {
        "official_batch_id": official_batch,
        "official_pass_id": official_pass,
        "official_snapshot": snapshot,
        "promoted_utc": utc_now_iso(),
    }
    write_json_workspace(TRACKER_PATH, tracker)
    return cmd_sync()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="Initialize mirrored workspace directories, tracker, and roadmap")
    sub.add_parser("sync", help="Scan workspace/poses, batches, snapshots and regenerate tracker + ROADMAP.{md,json}")
    sub.add_parser("status", help="Show sequential batch status and next-batch suggestion")

    nxt = sub.add_parser("next-batch", help="Show the next sequential 5-pose batch suggestion")
    nxt.add_argument("--size", type=int, default=5)

    aud = sub.add_parser("mark-audit", help="Record advisory visual audit score for a workspace batch/pass")
    aud.add_argument("--batch", required=True, help="e.g. batch-0003")
    aud.add_argument("--pass", dest="pass_label", required=True, help="e.g. pass-02")
    aud.add_argument("--score", type=float)
    aud.add_argument("--notes", required=True)

    pro = sub.add_parser("mark-promoted", help="Record official promotion provenance")
    pro.add_argument("--batch", required=True)
    pro.add_argument("--pass", dest="pass_label", required=True)
    pro.add_argument("--official-batch", required=True)
    pro.add_argument("--official-pass", required=True)
    pro.add_argument("--snapshot", required=True)

    args = parser.parse_args()
    if args.cmd in ("init", "sync"):
        out = cmd_sync()
    elif args.cmd == "status":
        out = cmd_status()
    elif args.cmd == "next-batch":
        auth, v00_rows = read_v00_catalog()
        out = compute_next_batch(
            load_or_create_tracker(auth),
            backward_families(v00_rows),
            read_top_level_built_poses(),
            size=args.size,
        )
    elif args.cmd == "mark-audit":
        out = cmd_mark_audit(args.batch, args.pass_label, args.score, args.notes)
    else:
        out = cmd_mark_promoted(
            args.batch, args.pass_label, args.official_batch, args.official_pass, args.snapshot
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
