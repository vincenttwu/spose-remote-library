# SPOSE Remote — controlling instructions for future AI sessions

**Status:** Independent remote development library, not the user's authoritative local working library. These instructions apply to this project checkout and to portable *context handoffs* made from it. Do not confuse historical source evidence, source reference ratings, Blender build results, and explicit user acceptance.

## Mandatory cold-start sequence

1. Read `CONTINUATION.md`, `ROADMAP.md`, and `ROADMAP.json` before making any new pose or altering a file.
2. Read `SKILL.md`, `WORKFLOW.md`, `project.json`, `source/dataset.json`, and the relevant `docs/` contracts.
3. Inspect `tooling/rig-maps/RIG001-v001.json`, `pairs/CPL01/v001/pair.json`, and `schemas/pose-package-README.md` before creating rig targets.
4. Verify whether the upload is the **full runnable remote library** or a **small context-only handoff** (look for `handoff/HANDOFF-MANIFEST.json`). A handoff does not contain `.blend` assets or the full CSV and must NOT be used as a replacement for the local runnable remote library.
5. Consult the latest tracker and feedback for the selected pose before editing. Never assume a successful ZIP import indicates accepted visual geometry.

## Core project priorities

- **Global V00-first milestone:** all 276 V00 bases across all 28 families are to be developed and reviewed before beginning any V01–V10 variations. Family-by-family V00 work is allowed, but family completion does **not** unlock that family's variations. The global phase gate remains locked until all 276 are accepted **and the user explicitly authorizes the next phase**.
- Source catalog `SRC003/v001` is read-only, 3,036 records / 51 columns, checkpoint `20261122T013728Z`.
- The owner maintains the independent Blender `remote/` library on their computer; generated modules are exchanged via `{POSE_ID}_{UTC_TIMESTAMP}.zip` with JSON-only inputs, not duplicated `.blend` scenes.
- Do not overwrite `local/`, source catalogs, mesh assets, shared rig profiles, previously imported pose revisions, or historical attempts. New revisions get `rNNN` directories.
- Do not use a rejected or skipped historical pilot (`history/local-pilots/UFDG-FWCH-V00`) as an accepted V00 parent.

## Technical rules

- `ACTOR_1` maps to pair A (1.85 m), `ACTOR_2` maps to pair B (1.77 m); up axis +Z, forward -Y, meters.
- Rigify body profiles may contain deliberate calibration offsets. Do **not** zero all bones or mutate rig mesh/proportions to force contact. Only edit mapped controls in `rig-targets.json` and explicit supported spaces.
- Every intended floor, body-body, and hand-body contact should have a documented target; proxy bone distances alone do not demonstrate correct mesh contact or safe physical posture.
- The contact and rendering system is an **unverified development scaffold** until locally run with Blender. When the assistant has no Blender runtime, work only from source metadata, scripts, and user-provided render evidence; don't claim a scene was rendered or approved.
- Source `generation_gate` (`PASS`, `REVIEW`, `EXCLUDE`) is **not** the Blender job state. `PASS` never proves actual feasibility. A Blender draft, even if images exist, is not `accepted`.
- `review_pose.py` records **explicit human review**. Do not execute that script to approve poses on behalf of the user or forge confirmations.

## Source of truth and derived files

| Domain | Authority | Derived read-only views |
|---|---|---|
| Geometry specifications | `source/SPOSE-FULL-20261122T013728Z.csv` and its SHA-256 registration | `ROADMAP.json`, portable V00 subset |
| Pair and rig | `pairs/CPL01/v001/template.blend`, BP001, RIG001 map and manifests | Context-only metadata/fingerprints |
| Pose revisions and reviews | `tracking/progress.sqlite` and versioned `poses/` data | `tracking/progress.csv`, `ROADMAP.json`, `ROADMAP.md` |
| Process | This file, `SKILL.md`, `WORKFLOW.md`, `CONTINUATION.md`, plus relevant contracts | Handoff `SESSION-START.md` |

Regenerate roadmap using `python scripts/update_roadmap.py`; never edit `ROADMAP.md` checkboxes or `ROADMAP.json` state manually. The tracker remains authoritative.

## Required operations and deliverables

- Before pose work: check `ROADMAP.md`, source row, dependency SHA hashes, rig map, and previous feedback; design one V00 module with contact intent and explicit rig transforms.
- Before user execution: run `python scripts/import_pose.py <ZIP> --dry-run` on a full library, or `scripts/package_pose_from_handoff.py` plus offline contract checks from a context-only handoff.
- User machine: Blender background build, previews and measurements. Follow with visual review; record `accepted` only through explicit user choice.
- After import or review: regenerate tracking exports/roadmap, then create a new portable handoff using `python scripts/package-library-for-remote.py`.
- After substantive workflow/source changes: update SKILL, WORKFLOW, CONTINUATION, docs, README, CHANGELOG, and release manifest; retain a clear checkpoint.

## Prohibited shortcuts

No automatic "all V00 accepted", no variation-phase start by family alone, no source metadata being interpreted as success-rate evidence, no Blender execution claims in an environment without Blender, no pose package Python execution, no copying huge shared assets into each pose module, no unreviewed approval promotion, and no pretending a small handoff ZIP can run Blender itself.
