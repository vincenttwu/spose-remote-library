"""Shared helpers for the isolated SPOSE experimental workspace/.

Hard boundary: every write helper refuses any path outside workspace/.
Top-level library files are accessed strictly read-only.
Mirrors top-level layout inside workspace/:
  workspace/incoming/
  workspace/batches/
  workspace/poses/<POSE_ID>/<PAIR_ID>/<PAIR_VERSION>/rNNN/
  workspace/snapshots/<batch>-<pass>_<ts>/
  workspace/review/
  workspace/upload/
  workspace/tracking/workspace-tracker.json
  workspace/ROADMAP.md, workspace/ROADMAP.json
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = WORKSPACE_ROOT.parent

INCOMING_DIR = WORKSPACE_ROOT / "incoming"
BATCHES_DIR = WORKSPACE_ROOT / "batches"
POSES_DIR = WORKSPACE_ROOT / "poses"
SNAPSHOTS_DIR = WORKSPACE_ROOT / "snapshots"
REVIEW_DIR = WORKSPACE_ROOT / "review"
UPLOAD_DIR = WORKSPACE_ROOT / "upload"
TRACKING_DIR = WORKSPACE_ROOT / "tracking"
TRACKER_PATH = TRACKING_DIR / "workspace-tracker.json"
ROADMAP_MD_PATH = WORKSPACE_ROOT / "ROADMAP.md"
ROADMAP_JSON_PATH = WORKSPACE_ROOT / "ROADMAP.json"

if str(LIBRARY_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(LIBRARY_ROOT / "scripts"))

import pose_common  # noqa: E402


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_in_workspace(path: Path | str) -> Path:
    """Resolve path and raise ValueError if it escapes workspace/."""
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / p
    resolved = p.resolve()
    ws_resolved = WORKSPACE_ROOT.resolve()
    if not resolved.is_relative_to(ws_resolved):
        raise ValueError(f"Non-pollution guard: refused path outside workspace/: {resolved}")
    return resolved


def resolve_workspace_cli_path(raw: Path | str) -> Path:
    """Resolve a CLI path passed relative to repo root or workspace/ and guard boundary."""
    p = Path(raw)
    if not p.is_absolute():
        candidate_lib = (LIBRARY_ROOT / p).resolve()
        if candidate_lib.is_relative_to(WORKSPACE_ROOT.resolve()):
            p = candidate_lib
    return ensure_in_workspace(p)


def workspace_rel(path: Path | str) -> str:
    return ensure_in_workspace(path).relative_to(WORKSPACE_ROOT.resolve()).as_posix()


def read_json(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_workspace(path: Path | str, payload: dict | list) -> Path:
    target = ensure_in_workspace(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


def write_text_workspace(path: Path | str, text: str) -> Path:
    target = ensure_in_workspace(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)
    return target


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_batch_label(label: str) -> str:
    s = label.strip().lower()
    m = re.fullmatch(r"batch[-_]?(\d+)", s)
    if m:
        return f"batch-{int(m.group(1)):04d}"
    return s


def normalize_pass_label(label: str) -> str:
    s = label.strip().lower()
    m = re.fullmatch(r"pass[-_]?(\d+)", s)
    if m:
        return f"pass-{int(m.group(1)):02d}"
    return s


def ensure_workspace_dirs() -> None:
    for d in (INCOMING_DIR, BATCHES_DIR, POSES_DIR, SNAPSHOTS_DIR, REVIEW_DIR, UPLOAD_DIR, TRACKING_DIR):
        ensure_in_workspace(d).mkdir(parents=True, exist_ok=True)


def pose_version_dir(pose_id: str, pair_id: str = "CPL01", pair_version: str = "v001") -> Path:
    return ensure_in_workspace(POSES_DIR / pose_id / pair_id / pair_version)


def list_pose_revisions(pose_id: str, pair_id: str = "CPL01", pair_version: str = "v001") -> list[Path]:
    vdir = pose_version_dir(pose_id, pair_id, pair_version)
    if not vdir.is_dir():
        return []
    revs = [p for p in vdir.iterdir() if p.is_dir() and re.fullmatch(r"r\d{3}", p.name)]
    return sorted(revs, key=lambda p: int(p.name[1:]))


def next_pose_revision_dir(pose_id: str, pair_id: str = "CPL01", pair_version: str = "v001") -> tuple[str, Path]:
    revs = list_pose_revisions(pose_id, pair_id, pair_version)
    next_num = (int(revs[-1].name[1:]) + 1) if revs else 1
    rev_label = f"r{next_num:03d}"
    return rev_label, ensure_in_workspace(pose_version_dir(pose_id, pair_id, pair_version) / rev_label)


def read_library_authority() -> dict:
    """Read pinned top-level source/pair/rig metadata read-only."""
    project = read_json(LIBRARY_ROOT / "project.json")
    src_cfg_path = LIBRARY_ROOT / project["source_config"]
    src_cfg = read_json(src_cfg_path)
    catalog_path = (src_cfg_path.parent / src_cfg["root"] / src_cfg["canonical_catalog"]).resolve()
    pair_cfg = read_json(LIBRARY_ROOT / project["default_pair"]["config"])
    pair_id = pair_cfg["pair_id"]
    pair_ver = pair_cfg["version"]
    template_path = (LIBRARY_ROOT / "pairs" / pair_id / pair_ver / "template.blend").resolve()
    appearance_path = (
        LIBRARY_ROOT / "pairs" / pair_id / pair_ver / "studies" / "VP001-v001" / "appearance-study.blend"
    ).resolve()
    rig_cfg = read_json(LIBRARY_ROOT / "tooling" / "rig-maps" / "RIG001-v001.json")
    return {
        "project_id": project["project_id"],
        "source_id": src_cfg["source_id"],
        "source_revision": src_cfg.get("revision", "v001"),
        "source_checkpoint": src_cfg["checkpoint"],
        "catalog_path": catalog_path,
        "catalog_sha256": src_cfg["catalog_sha256"],
        "pair_id": pair_id,
        "pair_version": pair_ver,
        "template_path": template_path,
        "template_sha256": pair_cfg["template_sha256"],
        "appearance_path": appearance_path,
        "rig_map_id": rig_cfg.get("rig_map_id", "RIG001"),
        "rig_map_version": rig_cfg.get("version", "v001"),
    }


def read_v00_catalog() -> tuple[dict, list[dict]]:
    """Return (authority, v00_rows) from the pinned source CSV read-only."""
    auth = read_library_authority()
    if sha256_file(auth["catalog_path"]) != auth["catalog_sha256"]:
        raise ValueError("Top-level catalog SHA-256 mismatch; aborting workspace read")
    with auth["catalog_path"].open("r", encoding="utf-8-sig", newline="") as f:
        rows = [row for row in csv.DictReader(f) if row.get("variation_code") == "V00"]
    return auth, rows


def read_top_level_built_poses() -> set[str]:
    """Read-only lookup of pose IDs already built in top-level ROADMAP.json."""
    roadmap_path = LIBRARY_ROOT / "ROADMAP.json"
    if not roadmap_path.is_file():
        return set()
    doc = read_json(roadmap_path)
    built = set()
    for base in doc.get("v00_poses", doc.get("bases", [])):
        if base.get("built") or base.get("latest_revision") is not None:
            built.add(base["pose_id"])
    return built


def build_pose_package_zip(
    dest_dir: Path | str | None,
    pose_id: str,
    pose_json: dict,
    rig_targets: dict,
    contacts: dict,
    render_config: dict | None = None,
    validation_plan: dict | None = None,
    timestamp_utc: str | None = None,
) -> Path:
    """Create a schema-valid spose_pose_module ZIP in workspace/incoming/ (or dest_dir) and validate via pose_common."""
    out_dir = ensure_in_workspace(dest_dir if dest_dir is not None else INCOMING_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp_utc or utc_now_stamp()
    auth, rows = read_v00_catalog()
    matches = [r for r in rows if r["pose_id"] == pose_id]
    if len(matches) != 1:
        raise ValueError(f"Pose ID not found uniquely in V00 catalog: {pose_id}")
    row = matches[0]
    row_sha = sha256_bytes(row["specification"].encode("utf-8"))

    members: dict[str, dict] = {
        "pose.json": pose_json,
        "rig-targets.json": rig_targets,
        "contacts.json": contacts,
    }
    if render_config is not None:
        members["render-config.json"] = render_config
    if validation_plan is not None:
        members["validation-plan.json"] = validation_plan

    encoded = {
        name: (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        for name, obj in sorted(members.items())
    }
    manifest = {
        "schema_version": 1,
        "package_type": "spose_pose_module",
        "pose_id": pose_id,
        "package_timestamp_utc": ts,
        "dependencies": {
            "source_id": auth["source_id"],
            "source_checkpoint": auth["source_checkpoint"],
            "source_row_sha256": row_sha,
            "pair_id": auth["pair_id"],
            "pair_version": auth["pair_version"],
            "template_sha256": auth["template_sha256"],
            "rig_map_id": auth["rig_map_id"],
            "rig_map_version": auth["rig_map_version"],
        },
        "payload_sha256": {name: sha256_bytes(blob) for name, blob in encoded.items()},
    }
    encoded["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    zip_path = ensure_in_workspace(out_dir / f"{pose_id}_{ts}.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(encoded):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, encoded[name])

    # Validate immediately against the real top-level package contract.
    pose_common.load_package(zip_path, validate_dependencies=True)
    return zip_path
