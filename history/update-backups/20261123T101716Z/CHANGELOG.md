# Library changelog

These versions describe library configuration and workflow releases. Body profiles and pairs retain their independent v001-style versions; pose outputs use r001-style revisions. Job attempts belong in the tracker.

## 0.6.0 — 2026-11-23

- Preserved V00 as user-skipped and created the separate UFDG-FWCH-V01 / CPL01 v001 / r001 pilot draft from SRC002 specification only.
- Added pose-specific build, source-palm/floor diagnostics, and saved-pilot verification helpers.
- Corrected native IK compression by disabling solver stretch and verifying actual segment lengths rather than relying on the Rigify property alone.
- Added floor-support proxies, static geometry/rest-rig preservation checks, source/appearance validation, and contact-region overlap reporting.
- Saved three review views, a region QA image, metadata, measurements, checksums, and a resumable tracker checkpoint. V01 contact fit remains pending review; no asset or pose was accepted and production remains disabled.

## 0.5.1 — 2026-11-23

- Moved the user-supplied CSV from Downloads into source/SPOSE-UFDG-v001.csv, verified identical SHA-256, and marked the file read-only.
- Registered SRC002 v001 (55 UFDG records) as the active specification source; preserved the original archive registration as dataset-original.json.
- Updated source pointers, pose record provenance, continuation, and status helper for config-relative source roots.
- No pose jobs or Blender assets changed.

## 0.5.0 — 2026-11-23

- Inspected native muscle/guide material controls and confirmed both referenced texture images are missing from the installed source asset.
- Added VP001 v001: proposed fixed cool A / warm B palettes with 11 broad body regions, plus a separate self-contained Blender study and region/plain previews.
- Reused the native muscle-group slider for independent material blending; verified samples 0, 0.135, 0.27 without geometry changes.
- Added required appearance metadata, QA preview checks, and the metadata validator; documented the controls in SKILL.md and workflow 0.1.2.
- Main character master and pair template geometry/materials remain unchanged. Palette acceptance and integration are pending user review.

## 0.4.0 — 2026-11-23

- Prepared BP001 v001 master and provisional CPL01 v001 pair as review drafts.
- Added reproducible Blender inspection, build, measurement, and reopen-verification helpers and RIG001 control maps.
- Verified 1.85 m/1.77 m evaluated heights, normalized matching geometry, independent rig/slider behavior, and embedded Rigify UI registration on Blender 5.2.2 LTS.
- Added body/pair preview images, technical validation reports, and checksums.
- Replaced unused source texture overlays with self-contained clay materials because the source references missing images.
- Calibrated workflow 0.1.1 to allow provisional pair preparation for full-character requests while retaining both user-review gates.
- Production remains disabled. Original dataset, reference image, source mannequin, and live Blender scene remain unchanged.

## 0.3.0 — 2026-11-23

- Separated ordered W01–W07 steps and completion criteria into WORKFLOW.md, workflow version 0.1.0.
- Refocused SKILL.md on detailed operation methods, with untested rig behavior explicitly pending.
- Updated entry-point pointers and machine-readable documentation roles.
- Replaced the duplicate continuation procedure with the active workflow position.
- Marked the workflow as initial and subject to calibration from observed results; no Blender production state changed.

## 0.2.1 — 2026-11-23

- Renamed START_HERE.md to README.md and updated active documentation pointers.

## 0.2.0 — 2026-11-23

- Established AGENTS.md as the instruction/pointer entry point.
- Added project-local SKILL.md procedures.
- Established CONTINUATION.md as the required cold-start file and single maintained handoff.
- Added this log and machine-readable documentation pointers.
- Replaced the old handoff with a pointer and simplified START_HERE.md to avoid competing status records.
- No Blender geometry, template approval, or pose job was created in this release.

## 0.1.0 — 2026-11-23

- Created library structure, BP001 v001 body profile, and CPL01 v001 pair configuration.
- Set proportional actor heights to 1.85 m and 1.77 m.
- Pinned source checkpoint, catalog checksum, and reference image checksum.
- Added record templates, milestones, empty SQLite tracker, exports, and status helper.
- Verified configuration, tracker integrity, and all 476 listed source checksums.
- Left rig inspection, calibration, templates, and pose production pending.

## 0.7.0-remote — independent remote baseline (2026-11-23)

- Forked the supplied local library into independent `remote/` structure without touching original.
- Promoted full 28-family / 3,036-record SRC003 dataset as active read-only source; SRC002 source retained historically.
- Moved prior local V00/V01 drafts and tracking into read-only historical context; initialized a fresh remote SQLite tracker.
- Added root `scripts/` importer, Blender builder, preview renderer, contact QA, tracking exporter and feedback packager.
- Updated AGENTS, WORKFLOW, SKILL, CONTINUATION and README for modular V00 pipeline and unapproved asset state.
- Scripts are not claimed as Blender-tested; validate locally before production use.

## 0.8.0 — 2026-11-23 — Portable cold start and global V00 roadmap

- Added authoritative **V00-first production plan**: all 276 V00 bases across 28 families must be accepted before enabling V01–V10.
- Added `scripts/update_roadmap.py` and derived `ROADMAP.md`/`ROADMAP.json`; pose and family states come from source catalog + independent remote SQLite, never manually checked boxes.
- Added manual `scripts/review_pose.py` decision workflow; only explicit human review may mark a revision `accepted`.
- Linked roadmap regeneration to transactional tracking snapshot exports.
- Added `scripts/package-library-for-remote.py` (and underlying `package_library_for_remote.py`) to produce a compact context-only ZIP, excluding `.blend`, renders, full 3,036-row CSV and SQLite while retaining source fingerprints, full V00 descriptions, all pose IDs, rig maps, docs, and lightweight revision metadata.
- Added `scripts/package_pose_from_handoff.py` for offline data-only V00 pose ZIP authoring from the small handoff; receiving full library still independently verifies source/template hashes.
- Expanded cold-start `SKILL.md`, `CONTINUATION.md`, `WORKFLOW.md`, `README.md`, `AGENTS.md` and `docs/` contracts; clarified full library vs portable handoff.
- No Blender execution performed by this documentation/handoff change; no new pose was accepted or marked ready for production.
