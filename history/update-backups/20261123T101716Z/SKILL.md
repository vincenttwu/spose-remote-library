---
name: spose-remote-library
version: 0.8.0
scope: project-local
summary: Operate SPOSE's standalone Blender mannequin-pair library using modular V00 pose ZIPs, contact QA, an explicit acceptance tracker, deterministic roadmap and portable cold-start handoffs.
---

# SPOSE Remote skill — detailed operating playbook

**This is a project-local skill, not an installed global assistant tool.** A new session should read it as a procedure and consult related scripts. It is designed to remain useful even when the only upload is the small portable handoff ZIP and no Blender runtime is available.

## 1. Must-read order and identity

1. `CONTINUATION.md` (current checkpoint and exact source/asset IDs).
2. `ROADMAP.md`, `ROADMAP.json` (which V00s are complete, latest attempts and deferred variations).
3. `AGENTS.md` (authority and strict preservation rules), `WORKFLOW.md` (standard stages).
4. `project.json`, `source/dataset.json`, `pairs/CPL01/v001/pair.json`, `tooling/rig-maps/RIG001-v001.json`.
5. `schemas/pose-package-README.md` and `docs/POSE-MODULE-AND-FEEDBACK.md` for per-pose payloads.
6. Selected row from `source/SPOSE-FULL-20261122T013728Z.csv` in the full library or `source/V00-CATALOG.csv` in the portable handoff.

Do not assume a prior chat's answer is newer than the files. If a key file disagrees with the active registered catalog or tracker, stop that mutation, state the conflict, and preserve evidence rather than guessing.

## 2. Library and handoff modes

| Capability | Full local `remote/` library | Portable handoff `remote/` |
|---|---|---|
| Full 3,036-row 51-column catalog | Yes | No; 276 full V00 rows + ID/hash index of all records |
| BP001/CPL01 meshes and `.blend` | Yes | No; only versioned metadata and SHA fingerprints |
| SQLite authoritative tracker | Yes | No; read-only roadmap and progress snapshots |
| RIG001 rig-control mapping | Yes | Yes |
| Create data-only pose ZIP | `scripts/package_pose.py` | `scripts/package_pose_from_handoff.py` |
| Import/render a pose | Requires Blender locally | Not supported |
| Update acceptance | `scripts/review_pose.py` after user review | Not supported |
| Create fresh handoff | `scripts/package-library-for-remote.py` | Not supported (needs full catalog, scene hashes, tracker) |

Never extract a portable handoff over the user's runnable `remote/`. It has the same root path but deliberately omits assets and does not represent a deployable incremental update.

## 3. Source contract

- Active catalog `SRC003/v001`, checkpoint `20261122T013728Z`; 28 families, 276 bases, 3,036 records, 51 columns.
- Registered catalog SHA `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6`. Refer to `source/dataset.json` for current authority.
- Each pose ID, e.g. `DOGG-DOGG-V00`, uniquely identifies a source row; package manifest pins `source_row_sha256=sha256(specification.encode('utf-8'))`.
- JSON package metadata may quote the specification, but should not rewrite it as though it were the original. Implementing rig targets is a separate, provisional inference.
- Treat `generation_gate` as a **filter**, not Blender status; never equate a source `PASS` with workable contact.
- V01–V10 are present only as future source rows. The importer intentionally refuses non-V00 until the user explicitly releases the global V00-first gate.

## 4. Anatomy, rig and coordinate contract

- Pair: CPL01/v001 with A=ACTOR_1 (1.85 m) and B=ACTOR_2 (1.77 m); separate Rigify rigs; units meters; +Z up, -Y forward.
- Reference actor objects `CPL01_A_ROOT`, `CPL01_A_RIG`, `CPL01_A_BODY` and B equivalents.
- Verify rig controls using `tooling/rig-maps/RIG001-v001.json`; mapped bones include `root`, `hips`, `torso`, `chest`, `neck`, `head`, `hand_ik.L/R`, `foot_ik.L/R`, elbow and knee pole targets.
- Permitted control spaces: `OBJECT_WORLD_LOCATION_M`, `OBJECT_WORLD_ROTATION_DEG`, `POSE_LOCAL_ROTATION_DEG`, and `POSE_WORLD_HEAD_M`. Numeric triples only; Blender interprets Euler degrees in the build script. A local bone rotation is not the same as global pose orientation.
- Preserve body calibration offsets, independent rigs and shared profile dimensions. Never globally reset all bones. Do not embed source scripts in pose ZIPs.

## 5. How to select a V00

Start with the `ROADMAP.md` family table and choose a base with `not_started` and a tractable support topology. Prefer lower complexity and source `PASS`, but inspect geometry and previous feedback. A family being complete does not permit variants. `history/local-pilots/UFDG-FWCH-V00` was excluded and must not be silently used as an approved example.

For the selected row, explicitly record: target pose ID; source spec and row hash; front/rear/left-right roles; root placement; floor contact/support; pelvis and torso orientation; limb joint targets; hand/arm contact routes; camera/visibility expectations; failure risks; unresolved source ambiguity. Avoid inventing unsupported geometry without labeling it as a hypothesis.

## 6. How to author a data-only pose package

1. Create a local draft folder containing `pose.json`, `rig-targets.json`, `contacts.json`, optionally `render-config.json`, `validation-plan.json`. All files JSON, no code, meshes, images, or absolute paths.
2. `pose.json` at minimum `{ "schema_version":1, "pose_id":"DOGG-DOGG-V00", "status":"proposal" }`; include rationale and geometry intent if useful.
3. In `rig-targets.json`, list explicit ordered actor root and mapped pose-bone controls, with coordinate-space declaration. Do not use an empty control array.
4. In `contacts.json`, list intended anchor pairs and tolerances; annotate contact semantics and areas of concern separately. Contact anchors are diagnostic proxies; their thresholds are not physical proof.
5. In full library: `python scripts/package_pose.py POSE_ID draft-folder --output incoming/`; the packager derives source and template hashes from current bytes.
6. In context-only handoff: `python scripts/package_pose_from_handoff.py POSE_ID draft-folder --output ../pose-packages/`; this uses a frozen dependency map included in that handoff. The user's full importer rejects stale dependencies.
7. Use a fresh UTC timestamp, never overwrite an earlier package. Each ZIP is `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip` with six or fewer root-level JSON members and per-payload SHA-256 entries in `manifest.json`.
8. From full remote: `python scripts/import_pose.py incoming/<ZIP> --dry-run` before running Blender.

**Important:** The importer validates structure and pinning, not body plausibility. A package with perfect JSON can still be an awkward pose.

## 7. Local Blender build and feedback loop

1. User runs `python scripts/import_pose.py incoming/<ZIP> --blender <PATH_TO_BLENDER>` in a full remote library. The script uses a background process; `--save-blend` is optional.
2. The build creates `poses/<POSE_ID>/CPL01/v001/rNNN/` with original package JSON, applied control log, rendered previews, contact proxy metrics, `validation.json`, `pose.json`, `checksums.json`, and logs. Never duplicate all BP001/CPL01 meshes per pose by default.
3. The job state normally becomes `draft` if Blender produced previews; the script does not auto-accept. Failed builds remain auditable.
4. Review actual images: rear/front relative alignment, support continuity, floor/foot placement, hand target region, finger orientation, mesh intersections, rig IK behavior and clear contact. Nearest-mesh and bone-head distances alone are insufficient.
5. User runs `python scripts/export_feedback.py POSE_ID --revision N` and returns that compact ZIP. Assistant inspects evidence and issues `r(N+1)` input package.
6. Only an explicit human review may change a revision to `accepted`, `validated`, or `blocked`: use `python scripts/review_pose.py POSE_ID --revision N --decision accepted --reviewer user --note "..." --confirm-reviewed` after reviewing images. Source `REVIEW` requires `--acknowledge-source-review`.
7. Every job/review regenerates `tracking/progress.csv`, `tracking/events.jsonl`, `ROADMAP.md`, and `ROADMAP.json` from SQLite.

## 8. V00-first roadmap rules

- `ROADMAP.json` is a derived machine snapshot with all 276 V00 IDs, per-family counts/states, latest attempts and source gates.
- `ROADMAP.md` is the human checkbox view. An `[x]` means an accepted revision for that row's exact source hash/checkpoint; it is **not** a checked package build.
- `scripts/update_roadmap.py --check` detects stale snapshots; `scripts/update_roadmap.py` regenerates them. Manual edits are forbidden.
- Each family has `v00_total`, `v00_accepted`, `v00_remaining`; global milestone requires 276 accepted V00s.
- All 2,760 variation records are deferred even after one family's V00 bases are accepted. Unlocking variations globally requires explicit user authorization and workflow/version change.
- Older accepted revision remains the base milestone even if a newer experimental draft fails. Record which revision is accepted.

## 9. Portable cold-start package and recovery

From the user's **full remote library**, after exporting current tracking snapshots, run:

```powershell
python scripts/update_roadmap.py --check
python scripts/package-library-for-remote.py
```

This writes `spose-remote-handoff-<UTC>.zip` adjacent to `remote/`. It contains only `remote/` as root, but intentionally excludes `.blend`, preview images, the full source CSV, and SQLite. It **does include all V00 source specifications, all pose ID+hash references, rig maps, docs, scripts, latest small pose metadata, the roadmap and hash manifest**.

A future assistant should request/use this small handoff when the rigs are unchanged. When body profile/pair template/source changes, the user should create a fresh handoff. To audit run `python scripts/package-library-for-remote.py --dry-run`; for file integrity check `handoff/HANDOFF-MANIFEST.json` after extraction.

Do not upload only an old handoff and assume new local Blender work is included. A newer feedback ZIP or regenerated handoff is needed for progress made since its timestamp.

## 10. Troubleshooting and honesty

- **No Blender runtime:** provide and validate JSON-only pose modules and scripts; never claim actual `.blend` modifications or contact tests occurred.
- **Rig target missing:** validate against map; inspect actual Blender armature locally before reauthoring. Do not invent bone names.
- **Proximity passes but pose looks wrong:** prioritize evaluated contact geometry and visual evidence; adjust root alignment/IK targets, not just tolerance.
- **Source/template hash mismatch:** old handoff; stop and regenerate from current runnable library. Never bypass hash checks by editing manifest hashes arbitrarily.
- **Unexpected V01–V10:** blocked by phase gate until all V00 and user authorization.
- **Different local hardware/Blender versions:** preserve logs and environment, mark unverified until tested.

See `docs/TROUBLESHOOTING.md` and `docs/COLD-START.md` for detailed recovery paths.

## 11. Completion definitions

- **Package valid:** ZIP schema and declared source dependencies pass.
- **Build complete:** Blender executed and produced expected artifacts (not an acceptance claim).
- **Geometry reviewed:** human inspected previews and contact; may mark `validated` or `blocked`.
- **Pose accepted:** explicit human `accepted` review recorded for exact source row, independent of characters' production approval status.
- **Family V00 complete:** every V00 ID in family accepted.
- **All V00 complete:** 276 accepted; variation stage still awaits user instruction.

The goal is *reproducible progress without large recurring uploads*, not an unsupported claim that offline pose modules guarantee realistic contact.
