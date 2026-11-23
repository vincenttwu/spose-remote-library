# SPOSE Standalone Library — Workflow v2 / batch upgrade and geometry calibration

## W00: Branch contract

One independent standalone Blender library (no required parent `remote/`). Root contains `project.json`, `scripts/`, `pairs/`, `source/`, `tracking/`, `poses/`. The original local branch is separate. Full library assets copied only once; each pose delivery is modular and source-pinned. `V00` milestone global: 276 bases and 28 families. Variations remain locked.

## W01: Install shared engine update (rare)

Extract the latest *batch upgrade* ZIP into a **temporary separate directory**. Confirm it has `install-update.py`, `UPDATE-MANIFEST.json`, `scripts/`, `docs/`, `pose-packages/` directly at root; NOT `remote/`.

Run `python install-update.py --library <FULL_LIBRARY_ROOT>` for a read-only preflight. When verified, repeat with `--apply`. Installer validates catalog SHA, referenced assets, individual file hashes, incoming collision rules; backs up replaced scripts and docs under `history/update-backups/<UTC>/`; copies new pose ZIPs to `incoming/`; preserves catalog, `.blend` shared templates, SQLite, old revisions and human approval history. Re-running the same bundle is idempotent when destination hashes match.

## W02: Library preflight

Current production focus: **Batch 001 = five DOGG-family V00 poses** (`DOGG-DOGG-V00`, `DOGG-CLSD-V00`, `DOGG-DOWN-V00`, `DOGG-FCDN-V00`, `DOGG-FROG-V00`). This is still the same family batch, not a move to the next family.


From actual full-library root, run `python scripts/check_remote.py` and `python scripts/check_batch_001.py`. Must find 28 families, 276 V00 and valid template hash. The project is still provisional. For a future session, run `python scripts/package-library-for-remote.py` to create small flat-root handoff and upload it; a handoff is not a full runnable install.

## W03: Candidate authoring

Read the specific source V00 row, not merely the pose code. Encode exact support topology and family identity. Each pose ZIP name is `{POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip`; flat internal JSON members `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`, optional `render-config.json`, `validation-plan.json`. `rig-targets.json` MUST specify `engine: rigify_floor_v2`, `geometry_contract_version: 2`, full explicit ordered controls, floor-calibration stages, support assertions and posture assertions **for both actors**. Every support assertion must have a corresponding calibration stage. `package_pose.py` or `package_pose_from_handoff.py` signs *by hashes only*, not cryptographic identity.

## W04: Import dry-run

`python scripts/import_pose.py incoming/<POSE>.zip --dry-run` checks pose identity, source row hash, pair/template hash, allowed input members, numeric bounds, v2 geometry contract, source V00 gate and declared supports. **It does not start Blender, apply controls, measure geometry or render images.** Legacy Batch 001 files must be rejected at this stage.

## W05: Blender build

`python scripts/import_pose.py incoming/<POSE>.zip --blender <EXE> [--save-blend]`. The importer creates a new `poses/<POSE_ID>/CPL01/v001/rNNN/` (never overwrites old revision). Blender uses supplied appearance-study template if present, else canonical pair template. First initialize Rigify arms/legs with IK enabled and no stretch, then place world torso heads/angles, foot IK and knee poles, supporting front hand IK/palms and elbow poles. Calibrate the *actual evaluated support mesh* in stages: knee patch (adjust torso Z), palms (hand IK Z), feet (foot IK Z). After floor calibration perform a bounded nearest-mesh pelvis-region approach along Y, then aim rear hands relative to the evaluated front hip. Finally measure contact proxy and validate support/posture. Rendering and geometry checks run locally in Blender 5.2.2 LTS, not in assistant environment.

## W06: Hard-gate handling

`validate_pose.py` checks grounded supports (near Z 0), knee joint height/bend for kneeling/quad, head drop for forward fold, sampled mesh below floor, and hip-head proximity. Failures become `blocked` with diagnostic codes even if images rendered. Blender exceptions become `failed`. A successful render that clears checks remains **draft**, not `accepted`. Do NOT label a standing renderer as a correct kneeling pose. `review_pose.py` refuses accepted/validated when `hard_gate_pass=false` or job blocked.

## W07: Visual review and feedback

Inspect `previews/front.png`, `side.png`, `three-quarter.png`, `qa-regions.png` and `validation.json`. Proxy distances can indicate overlap or missed targets without distinguishing clipping. Compare source contacts, knee/thigh support, pelvis-to-pelvis adjacency, arm reach, wrists/fingers, footprint and stage floor. Export `python scripts/export_feedback.py <POSE> --revision <N>`. Feedback ZIP contains images, reports, pose input and log; upload it to next session for targeted rNNN fixes. If geometry invalid, keep blocked. If visually acceptable and hard gate passed, user may explicitly record accepted via `review_pose.py` with `--confirm-reviewed`.

## W08: Track and handoff

Importer and review commands update SQLite and generate `tracking/progress.csv`, `tracking/events.jsonl`, `ROADMAP.md`, `ROADMAP.json`. Do not hand-edit roadmap. Generate portable handoff with `scripts/package-library-for-remote.py` after each progress milestone. It has flat ZIP root and excludes expensive binary assets and full catalog. If local catalog/assets change, regenerate all pose dependency hash mappings; old packages should not be patched.

## W09: Batch progression

Only run the rebuilt `DOGG-DOGG-V00` first. Once geometry is plausible, continue `DOGG-CLSD-V00`, then `DOGG-DOWN-V00`. Failures prompt shared-engine fixes or corrected specific modules; no spraying untested numeric presets across 276 V00s. When all 276 V00 are accepted and user separately authorizes it, only then begin V01–V10.

## W10: Failure/recovery

Keep backups under `history/update-backups/`; never delete tracker/old scenes. `build.log` captures bpy execution. An interrupted import may leave hidden staging; preserve it for diagnosis. Installer preflight prevents overwriting a different incoming pose ZIP of identical name. If updater fails during a write, it restores replaced files from backups and removes newly written files. Recovery should use the user's last known good copy of the full library, not a context-only handoff.
