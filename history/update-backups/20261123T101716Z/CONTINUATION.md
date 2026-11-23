# SPOSE Remote — Cold-start continuation / authoritative handoff

> **Purpose:** A fresh assistant should be able to resume from *this file plus the portable context ZIP*, without previous chat history. This file states the current project decisions, exact source and asset identities, execution boundaries, status authorities, and next required action. Read alongside `ROADMAP.md` and `SKILL.md`.

## 1. Project identity and checkpoint

- Branch: **standalone `remote/` SPOSE Blender library**, initially cloned from user-supplied `library.zip`. It lives alongside the user's independent local library, not within it. Local assets/history are immutable in this fork.
- Active source: `SRC003/v001`, checkpoint `20261122T013728Z`.
- Source path: `source/SPOSE-FULL-20261122T013728Z.csv`, registered through `source/dataset.json`.
- Source SHA-256: `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6`.
- 28 families; 276 V00 bases; 3,036 records; 51 canonical CSV columns. 2,760 V01–V10 rows are deferred.
- Pair and rig: `CPL01/v001`, `BP001/v001`, `RIG001/v001`, `VP001/v001`; actor A / ACTOR_1 = 1.85 m; actor B / ACTOR_2 = 1.77 m.
- Reference rig observed in Blender 5.2.2 LTS; this assistant runtime has **not** executed the newly built remote Blender pipeline.
- Current remote baseline: **zero imported remote pose jobs and zero accepted V00 bases**. Historical local pilot work is under `history/local-pilots/`, not remote production.
- `production_enabled=false`; characters and appearance remain unapproved review drafts.

**If the user's newly uploaded library differs:** inspect `ROADMAP.json`, `tracking/progress.csv`/SQLite and `project.json` instead of repeating this initial zero-progress claim. These files represent the checkpoint in the uploaded version. Never infer a newer status without evidence.

## 2. User's explicit production strategy

1. Maintain a fully independent `remote/` library; preserve local as a separate user-controlled branch.
2. Clone the pair/master rigs once; keep all pose outputs modular. Default pose ZIP = data-only JSON, **no per-pose scene `.blend`**. Optional `.blend` for targeted debugging.
3. Deliver individual pose input packages as `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip`.
4. User runs `python scripts/import_pose.py <ZIP> --blender <EXE>` in the **full local remote library**; the script applies controls, renders previews, writes pose revisions and tracking.
5. User sends compact feedback ZIP (`scripts/export_feedback.py`) with images/measures; assistant revises into a new pose package.
6. **Prioritize V00 bases for every family before working on variations.** Family grouping is useful for scheduling, but no V01–V10 production until global V00 milestone passes and user authorizes it.
7. Produce a small portable cold-start ZIP with `scripts/package-library-for-remote.py`; this is the preferred file for future chat uploads when large Blender assets are unchanged.
8. `ROADMAP.md` is the human-readable family table and per-base checklist; `ROADMAP.json` is the machine-readable projection. Both are generated from the source + SQLite tracking, not manually maintained status lists.

## 3. What is actually implemented

**Runnable library (user's machine):**
- Project structures and shared files under `body_profiles/`, `pairs/`, `visual_profiles/`, `tooling/`.
- Full pinned catalog under `source/`; historical 55-row UFDG-only source retained.
- `scripts/package_pose.py` creates hashed data-only pose input packages.
- `scripts/import_pose.py` validates package names, allowed JSON members, row/pair/template hashes, rig fields and V00 scope; uses background Blender to build revision folders.
- `scripts/blender_build.py` applies explicit root and pose-bone controls to the supplied pair; `scripts/render_previews.py` generates front/side/three-quarter and optional region QA renders; `scripts/validate_pose.py` captures *proxy* nearest-surface and anchor distances.
- `scripts/update_tracking.py` writes transactional job/events and exports status files, now regenerating ROADMAP.
- `scripts/review_pose.py` records explicit human `validated`, `accepted`, or `blocked` decisions; never automatic.
- `scripts/export_feedback.py` packages previews, validation and logs from an existing local revision.

**Cold-start / portable context:**
- `scripts/package-library-for-remote.py` (implementation in `package_library_for_remote.py`) exports documentation, configs, rig maps, source registration/fingerprints, **all 276 V00 rows**, all 3,036 pose IDs and row hashes, roadmap, tracking snapshots, and latest lightweight pose metadata when available.
- The small ZIP excludes `.blend`, meshes, preview PNGs, SQLite DB, full 3,036-row CSV, full scene caches, historical pilot scenes and redundant external assets.
- A fresh assistant can create a properly hashed pose ZIP with `scripts/package_pose_from_handoff.py` using the included `source/pose-dependencies.json`; then the user imports it into their runnable library. This does NOT recreate Blender assets.

## 4. Exact key directories

```text
remote/
  AGENTS.md / SKILL.md / WORKFLOW.md / CONTINUATION.md / README.md
  ROADMAP.md / ROADMAP.json   # derived source+tracker views
  docs/                      # detailed cold-start and operating contracts
  project.json               # source, pair, tracker, paths, feature flags
  source/                    # active full catalog + reference source configs
  body_profiles/BP001/v001/  # shared original master.blend
  pairs/CPL01/v001/          # shared template.blend; appearance study
  tooling/rig-maps/          # exact named control map
  scripts/                   # importer, packagers, roadmap, review, feedback
  schemas/                   # declarative pose ZIP schema
  incoming/                  # user drops modular pose ZIPs here
  poses/<POSE_ID>/CPL01/v001/rNNN/ # immutable revisions
  tracking/progress.sqlite   # authoritative job/review state
  tracking/progress.csv      # derived status view
  history/                   # local pilot snapshots, not active remote jobs
  reports/                   # feedback and QA exports
```

## 5. Critical historical facts

- The old local `UFDG-FWCH-V00` pilot was skipped/excluded and is not an accepted template. The local `UFDG-FWCH-V01` is a contact-review draft despite basic rig and floor tests. Both are archived under `history/`.
- Their failure mode: root alignments and IK targets can be syntactically valid while actual hand-to-shoulder/chest contact and body proximity remain wrong. Do not infer contact correctness from a small nearest-mesh number; use images plus anatomical target checks.
- Actor A and B have independent Rigify rigs, but their skeleton/proportions were provisionally calibrated. Existing calibration offsets must not be zeroed.
- Source `generation_gate` is a reference filter. `PASS` is not Blender validation, user approval, physical feasibility, or a render-success prediction.
- Some source poses have anatomical uncertainty; do not silently change their original 51-column specifications. Document proposed corrections in pose-module metadata and separate notes.
- No full natural-language-to-Rigify pose solver is currently implemented. Rig targets must be authored explicitly for each V00 candidate, with cautious reuse of validated controls.

## 6. Cold-start tasks based on upload type

### A. If uploaded file is `spose-remote-library-<UTC>.zip` (full library)

1. Verify ZIP contains only one root `remote/` and extract to a temporary directory, never overwrite the user's live library.
2. Read this file and ROADMAP; run `python remote/scripts/check_remote.py`, `python remote/scripts/update_roadmap.py --check`.
3. Select the next V00 base using ROADMAP (not a previously excluded local draft).
4. Read that pose's full row, review base posture/support, and consult rig map and pair geometry.
5. Produce a **candidate pose ZIP** with explicit rig transforms/contact anchors; offline dry-run against current full library.
6. Request user Blender execution and feedback. Until then mark it as **candidate, unrendered**.

### B. If uploaded file is `spose-remote-handoff-<UTC>.zip` (context only)

1. Read `handoff/SESSION-START.md` and `handoff/HANDOFF-MANIFEST.json`; verify it declares `context_only=true`.
2. Read `source/V00-CATALOG.csv`, `source/POSE-INDEX.csv`, `source/pose-dependencies.json` and rig map. These let you create V00 input ZIPs without the large assets.
3. Do **not** attempt Blender builds or full-library integrity checks inside the context handoff, and do not overwrite active full remote with it.
4. Author one data-only pose module; run `python remote/scripts/package_pose_from_handoff.py <ID> <draft_folder> --output <folder>`.
5. User runs the real importer on their full local remote library. If source/template hashes differ, stop and request a **new** handoff.
6. Read returned feedback ZIP before further revision; it is the only evidence of actual Blender execution or contact fit.

## 7. Status model and roadmap

- SQLite `tracking/progress.sqlite`: authority for job states, revision history and human reviews.
- `ROADMAP.json` and `ROADMAP.md`: deterministic *derived* views. `scripts/update_roadmap.py` recalculates 28 family entries and each V00 status. No hand-edited checkmarks.
- States: `not_started` (no job), `in_progress`, `draft`, `validated`, `accepted`, `blocked`, `failed`, `excluded`, or `stale_source` (tracker row references a prior catalog row). Acceptance checks exact active-row SHA and source checkpoint.
- If any accepted revision exists for a V00 base, its milestone remains accepted even when a newer experiment fails; the latest attempt is recorded separately.
- Family V00 complete = every base accepted; *global V00 complete* = all 276 accepted. Variations remain locked until separately authorized.

## 8. Standard commands (run from inside the full `remote/` folder)

```powershell
python scripts/check_remote.py
python scripts/update_roadmap.py --check
python scripts/package_pose.py DOGG-DOGG-V00 path/to/draft-folder --output incoming/
python scripts/import_pose.py incoming/DOGG-DOGG-V00_YYYYMMDDTHHMMSSZ.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOGG-V00_YYYYMMDDTHHMMSSZ.zip --blender "C:\path\to\blender.exe"
python scripts/export_feedback.py DOGG-DOGG-V00 --revision 1
# After visual inspection of rendered previews:
python scripts/review_pose.py DOGG-DOGG-V00 --revision 1 --decision accepted --reviewer user --note "Reviewed front, side and three-quarter contact alignment" --confirm-reviewed
python scripts/package-library-for-remote.py
```

Only execute `review_pose.py` on the user's actual review decision. For a source `REVIEW` gate, that command additionally requires `--acknowledge-source-review`.

## 9. Next work / requested milestone

**Do not start a batch of all 276 automatically.** First develop one easy, grounded V00 pilot from source and rig map, run it locally through Blender, inspect failure modes, then improve the shared contact method before generalization. Once the prototype works, process each family V00 set in ROADMAP order, recording individual revisions. After all families' V00 bases pass user review, the user can explicitly authorize a future V01–V10 expansion and workflow version change.

## 10. Known limitations and honest status

- In the authoring environment, `bpy`/Blender execution is unavailable. Python-only contract checks can pass; actual rig articulation, IK, mesh collision, camera framing and contact cannot be verified here.
- `POSE_WORLD_HEAD_M` control targets and Euler rotations are relatively low-level; constraint interactions may require Blender-side adjustments and repeat feedback. This is not a full inverse-kinematics solver.
- `validate_pose.py` uses unsigned sampled nearest-mesh distances and bone-head distances, not a physically valid collision/balance simulation.
- Historical absolute Windows paths may appear as provenance. Runtime scripts should resolve assets relative to `remote/` and must not require the original user's drive layout.
- The tiny handoff ZIP is context-only. It cannot itself be imported as a pose package or used as a full runnable remote checkout.

**Current scope decision:** all V00 first, with `ROADMAP.md` + `ROADMAP.json` tracking and paired `package-library-for-remote.py` for cold-start continuity.

## Release snapshot — `20261123T082056Z`

- Full runnable library ZIP: `spose-remote-library-20261123T082056Z.zip` — root is exactly `remote/`.
- Portable context-only ZIP: `spose-remote-handoff-20261123T082056Z.zip` — root also `remote/`, but must never be installed over the runnable library.
- This checkpoint is for **global V00-first authoring and validation**; no Blender render was run in the authoring environment.
- To continue in a future conversation, upload the portable context ZIP plus the most recent pose feedback ZIP if visual corrections are needed.
