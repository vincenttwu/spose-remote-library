# Data contracts and state fields

This document describes existing live interfaces observed in Batch 0001 and the new infrastructure feedback schema. Do not invent required fields when consuming future versions; inspect actual JSON, source rows and schema metadata first. Keep unknown fields intact.

## Canonical identifiers

- Source: `SRC003/v001` checkpoint `20261122T013728Z` in the existing library; full catalog SHA-256 registered in `source/dataset.json`.
- Pair: `CPL01/v001` and shared `template.blend` fingerprint.
- Rig map: `RIG001/v001` from `tooling/rig-maps/RIG001-v001.json`.
- Pose ID example: `DOGG-DOGG-V00` where `V00` is the base variation; source row has additional name, complexity, anchors and source invariants.
- Batch: human-safe `batch-0001`, pass `pass-01`/`pass-02`, in batch plan and feedback filename.

All IDs and hashes must be read from actual packages/live assets when verifying compatibility; examples are not universal constants.

## 1. Data-only pose package ZIP (existing schema 1)

Filename `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip`; typical members:

| Member | Purpose |
|---|---|
| `manifest.json` | `schema_version`, `package_type=spose_pose_module`, `pose_id`, `package_timestamp_utc`, `dependencies`, `payload_sha256` |
| `pose.json` | source specification, actor mapping, approach, source invariants, expected support, authoring/calibration notes |
| `rig-targets.json` | world/object controls, IK/FK and body targets, floor calibration, posture/support assertions and engine metadata |
| `contacts.json` | anchor proxy IDs, actor/bone-target mapping and tolerance meters |
| `validation-plan.json` | requirements, caveats and checks to report |
| `render-config.json` | expected render resolution and QA/adaptive-camera options |

Package manifest dependencies include `source_id`, `source_checkpoint`, `source_row_sha256`, `pair_id`, `pair_version`, `template_sha256`, `rig_map_id`, `rig_map_version`. `payload_sha256` hashes member JSON bytes. There must be **no executable pose scripts or `.blend` data** in these incoming ZIPs.

Example control (not an exhaustive rig schema):

```json
{"actor":"A","object_role":"root","space":"OBJECT_WORLD_LOCATION_M","value":[0,0,0]}
```

Keep exact rig-map keys and coordinate units; never fabricate joint names. Region-floor calibration and contact proxy checks are independent measurements; they are not approvals.

## 2. Installed pose revision

Path `poses/<POSE_ID>/CPL01/v001/rNNN/`, typically containing `pose.json`, `validation.json`, `checksums.json`, `blender-result.json`, `build.log`, `inputs/*.json`, `previews/{front,side,three-quarter,qa-regions}.png` and optionally `scene.blend` for explicit debugging. Revision folders and input hashes are not overwritten.

`validation.json` includes `rendered_views`, `technical_checks`, `contact_checks`, `issues`, `user_accepted`, legacy `hard_gate_pass`, `geometry_reference_pass`, `stability`, and `geometry_engine`. Some older revisions lack newer fields. `contact_checks.anchors` measures *bone-head proximity*; `contact_checks.mesh_sample` is a separate approximate surface measurement. `technical_checks.posture_heights` and floor support are additional diagnostics.

**Terminology:** `draft` means a rendered usable artifact; `needs_work` means quality concerns; `accepted` is optional human label; `hard_gate_pass=false` is not a work restriction. Historical `blocked` revisions may still have usable renders and count as built in the ROADMAP.

## 3. Batch plan and run summary

`batches/BATCH-001.json` uses `schema_version=1`, `batch_id`, explicit `batch_label` and `pass_label`, and `poses[]` entries containing `pose_id` and timestamped package basename. The runner verifies identity, attempts all entries, and saves `snapshots/batch-XXXX-pass-YY_<UTC>/batch-summary.json`.

Summary result fields include `pose_id`, `package`, `revision`, `revision_folder`, `build_status`, `pose_status`, `geometry_quality`, `stability`, `issues`, `issue_count`, `previews`, `contact_checks`, `posture_heights`, `new_revision_created`, `import_returncode` where available. `build_status=reused_existing_package` plus `new_revision_created=false` is explicit: **no newly generated geometry for that pose**.

No pass is accepted automatically based on a numeric check. File-integrity failures of an individual package become a result row while later poses still run.

## 4. Combined feedback ZIP (NEW schema 2)

This **single ZIP** replaces five nested per-pose ZIPs as the default return artifact:

```text
START-HERE.md
SUMMARY.md
batch-summary.json
manifest.json
poses/<POSE_ID>/pose.json
poses/<POSE_ID>/validation.json
poses/<POSE_ID>/build.log
poses/<POSE_ID>/inputs/manifest.json
poses/<POSE_ID>/inputs/rig-targets.json
poses/<POSE_ID>/images/front.webp         # PNG fallback possible
poses/<POSE_ID>/images/side.webp
poses/<POSE_ID>/images/three-quarter.webp
poses/<POSE_ID>/images/qa-regions.webp
context/AGENTS.md
context/SKILL.md
context/CONTINUATION.md
context/ROADMAP.json
context/source/V00-CATALOG.csv
context/handoff/HANDOFF-MANIFEST.json
... other portable context metadata
```

`manifest.json` contains `schema_version=2`, `kind=spose-remote-combined-feedback`, `batch_label`, `pass_label`, `generated_at_utc`, `pose_ids`, `pose_count`, `image_count`, `image_codecs`, `context_included`, `warnings`, `pose_results[]`, and `files_sha256` for all **other** ZIP members (no manifest self-hash). Per-image records include original PNG SHA-256, codec, lossless verification and dimensions. Embedded `context/` contains portable docs, scripts and derived source rows; **it is not a runnable library**.

Member integrity must be checked independently of visual-quality scores. If Pillow is unavailable, include byte-identical original PNG with a warning. If decoded pixel bytes differ after lossless conversion, export raises an integrity error and must not present the data as lossless.

## 5. Portable context manifest

`context/handoff/HANDOFF-MANIFEST.json` remains the existing handoff contract with `files_sha256`, data/source/pair/rig identifiers, roadmap summary and explicit omissions of heavy assets. For bundled feedback these paths are prefixed with `context/`; hashes apply to the files **inside that prefix**. The ZIP includes complete source **V00 rows** and all pose IDs/index; it omits the full 3,036-row catalog, `.blend`, SQLite and large scenes.

## 6. Infrastructure update manifest (NEW schema 2)

One `spose-remote-bundle-infra-0001_<UTC>.zip` has flat root `install-update.py`, `UPDATE-MANIFEST.json`, `APPLY.md`, `updates/` payload and offline tests. The `kind=spose_remote_infrastructure_update` manifest lists `release_id`, source/template fingerprints, and `payloads[{source,target,sha256}]`. Only docs, root operating Markdown and canonical `scripts/*.py` may be updated. Manifest does **not** hash itself. Installer receipts and rollback record exact before/after file hashes.
