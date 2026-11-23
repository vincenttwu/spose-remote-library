# GUIDE.md — Local Agent Operator Runbook (SPOSE Batch 001 Rebuild)

**Purpose:** This document is written for a local agent that has access to the user's computer, the installed SPOSE Blender library, and Blender 5.2.2 LTS. The user may give the agent **only this ZIP** and say "handle the batch." Follow these instructions from top to bottom. The assistant that produced this upgrade could not execute Blender; this is a **hypothesis and instrumentation repair**, not a verified pose fix.

## 0. What this is, and what it is not

- **One update ZIP**, containing rewritten `scripts/`, `docs/`, `SKILL.md`, `WORKFLOW.md`, `CONTINUATION.md`, `GUIDE.md`, a checksum manifest, and five **data-only pose ZIPs** under `pose-packages/`.
- **No `remote/` wrapper** is required. The ZIP must be extracted into its own *temporary* folder. Its root contains `install-update.py` and `UPDATE-MANIFEST.json` directly.
- The user's separately installed, runnable SPOSE library is another folder, identifiable by `project.json` with `project_id: "SPOSE-REMOTE-LIBRARY"`, plus `source/`, `pairs/`, `scripts/`, `tracking/`, `poses/`. The name of that folder is immaterial. **Do not install into the older local-origin library.**
- Do not copy or extract this bundle wholesale over the runnable library; use the installer to update only explicitly listed files and to preserve source, templates, database, and previous pose attempts.
- This batch does **not** contain the large `.blend` templates, full CSV, or a replacement tracking DB. Those must already exist in the full installed library.

## 1. Find the runnable library and Blender executable

1. Identify the project folder from a direct user path, desktop workspace or file search. Its `project.json` must declare `SPOSE-REMOTE-LIBRARY`; verify `source/dataset.json`, `pairs/CPL01/v001/template.blend`, and `tracking/progress.sqlite` exist.
2. Locate the Blender 5.2.2 LTS executable. On Windows a typical path is `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, but **do not assume** that exact path. `blender --version` is an alternative if Blender is on `PATH`.
3. Make a normal backup of the library before running the upgrade. The installer additionally creates *per-file* backups, but these are not a substitute for a copy of the library's DB and assets if the machine is unreliable.
4. Ensure no Blender process or Python process is currently writing to the SPOSE library.

## 2. Install (always preflight first)

Assume `<BUNDLE>` is the extracted folder with this file, and `<LIBRARY>` is the confirmed installed independent remote library.

```powershell
cd "<BUNDLE>"
python install-update.py --library "<LIBRARY>"
python install-update.py --library "<LIBRARY>" --apply
```

- The first command **must be dry-run** and should report `"ok": true` and `"mode": "dry_run"`. Stop if hashes, template, catalog, project identity or incoming package collision checks fail.
- The second command creates `history/update-backups/<UTC>/` backups and an install receipt. It adds the five current ZIPs to `<LIBRARY>/incoming/` without importing them.
- The installer updates only `project.json -> portable_handoff.archive_root` to `flat` (preserving other settings) and creates a current-install receipt. Existing jobs and ROADMAP progress are **not** reset.
- Do not manually overwrite files to bypass a failed preflight. If the library already contains a different file with one of these identical incoming filenames, stop and ask for a revisioned package.

## 3. Check installed state

```powershell
cd "<LIBRARY>"
python scripts/check_remote.py
python scripts/check_batch_001.py
python scripts/update_roadmap.py --check
python scripts/package-library-for-remote.py --dry-run
```

Verify source is `SRC003/v001`, checkpoint `20261122T013728Z`, SHA-256 `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6`, 28 families, 276 V00 and 3036 source records. None of these checks renders anything. If they fail, **do not import**.

## 4. Rebuild the first pose only (calibration gate)

**Do not run all five immediately.** `DOGG-DOGG-V00` is the calibration target. The other four ZIPs are staged but should stay unexecuted until its result is examined.

```powershell
python scripts/import_pose.py incoming/DOGG-DOGG-V00_20261123T091501Z.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOGG-V00_20261123T091501Z.zip --blender "<BLENDER_EXE>" --save-blend
```

- The dry-run validates JSON shape, source/template hashes and required V2 support/posture assertions; **it cannot validate geometry**.
- The real run should produce a new `poses/DOGG-DOGG-V00/CPL01/v001/rNNN/` revision, preserving the failed previous revision. `--save-blend` is intentional for this *single debugging/calibration run*, not a default for later poses.
- If Blender fails, inspect `build.log` and `blender-result.json`; preserve any incomplete `.pose-stage-*` directory. Do not report success based on the dry-run alone.
- Recommended later execution order after the first pose is visually credible: `DOGG-CLSD-V00`, `DOGG-FCDN-V00`, `DOGG-FROG-V00`, then `DOGG-DOWN-V00`. This keeps the batch inside the current DOGG family set while broadening calibration coverage.
- If rendered geometry is wrong, status should be `blocked` or `failed`. Even `draft` is **not an acceptance decision**.

### Expected first-pose posture

- Actor **A** is the **rear** mannequin (`ACTOR_1`): *kneeling* with both knees near floor, flexed knees and shins arranged without leg intersections.
- Actor **B** is the **front** mannequin (`ACTOR_2`): quadruped, both palms and knees supported near floor. Feet may be near the floor but **feet do not substitute for knees** in the support assertion.
- Both face anatomical forward (-Y); B's torso is lowered with explicit world-space torso placement. A's hands should be close to B's hip region. A must not be a standing mannequin using hands as an optical substitute for body proximity.
- All expected floor regions should be near Z=0, with no visibly sinking feet, floating palms, inverted wrists or implausible shin/knee fold.

### Inspect these files

1. `validation.json`: `hard_gate_pass`, `status`, support/posture/penetration issues.
2. `blender-result.json`: `checks.floor_calibration`, `checks.posture_heights`, `checks.geometry`, contact metrics and `issues`.
3. `previews/front.png`, `side.png`, `three-quarter.png`, `qa-regions.png` if available.
4. `build.log` and (when produced) `scene.blend` for targeted Rigify inspection.
5. Compare against `tooling/scripts/build_pilot_underarm_pose.py` for **rig control methods only**; old pilots are not approved posture templates.

**Critical note:** a minimum mesh-to-mesh distance near zero can also indicate penetration; it does not prove correct surface contact. Trust the actual renders and diagnostic hard gates, not merely an anchor score.

## 5. Export a compact feedback ZIP

Find the actual revision `rNNN` from the import command output. Then:

```powershell
python scripts/export_feedback.py DOGG-DOGG-V00 --revision <NNN>
```

The output goes into `<LIBRARY>/reports/` and includes images, JSON measurements, original input JSONs, validation and logs—without a large `.blend` scene. Give the **feedback ZIP** to the remote authoring assistant; attach screenshots if they add value. Report the actual problem succinctly, for example "A still standing", "B knee off ground", "B left palm 7cm above floor", "feet sink", or "pelvis gap". If the run fails before the importer finalizes the revision, include `build.log` or the preserved staging directory evidence instead.

## 6. Only after the first result is credible

Import and inspect these **one at a time**, each with its own new revision folder:

```powershell
python scripts/import_pose.py incoming/DOGG-CLSD-V00_20261123T091502Z.zip --dry-run
python scripts/import_pose.py incoming/DOGG-CLSD-V00_20261123T091502Z.zip --blender "<BLENDER_EXE>"
python scripts/import_pose.py incoming/DOGG-DOWN-V00_20261123T091503Z.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOWN-V00_20261123T091503Z.zip --blender "<BLENDER_EXE>"
```

- CLSD: A kneeling, B quadruped, **B's knees closer together** than basic DOGG. No standing substitute.
- DOWN: **both are supposed to be standing**; B folds forward with both palms and feet near the floor. Verify foot soles and palm surfaces, not only IK handle Z.
- If the basic DOGG candidate is blocked or visually poor, **stop** and send feedback before investing in the other four. They share the unverified engine.

## 7. Accept only with explicit user approval

The agent may inspect and recommend, but **must never invoke `review_pose.py --decision accepted` without explicit user approval**. If a pose fails technical gates, do not force its review state. If a user has visually approved a technically passing revision, use the documented review command in `WORKFLOW.md`, `SKILL.md` or `scripts/review_pose.py --help`.

`ROADMAP.md` and `ROADMAP.json` are derived from SQLite. All 276 V00s across all 28 families must be accepted before variations are considered, and the user must separately approve variation work.

## 8. Cold-start handoff after the local run

```powershell
python scripts/package-library-for-remote.py
```

This creates a **small, flat-root** `spose-remote-handoff-<UTC>.zip` in the parent directory. It contains current roadmap, tracker snapshots, scripts, source fingerprints, V00 rows and lightweight pose metadata. It deliberately excludes `.blend`, renders, full 42 MB catalog, SQLite and large assets. Never extract that handoff over the runnable library.

For the next remote ChatGPT session, upload the handoff **and** the relevant pose feedback ZIP. The handoff alone is enough for context/candidate packaging, but **not enough to visually diagnose contact**.

## 9. Failure, rollback, and agent report

- If install preflight fails: stop. Do not guess source/template hashes or overwrite the different branch.
- If install partially fails: inspect the install receipt and backup directory; the updater attempts to restore files on exceptions. Restore from a whole-library backup if machine/process termination occurred mid-write.
- If Blender geometry hard gates fail: retain the `blocked` revision and feedback; do not alter generated measurements manually to force acceptance.
- If a new template/catalog revision exists: stop and rebase rather than patching the pose ZIP dependency checksums.

At completion, report **(a)** library path and update receipt, **(b)** installed script engine version, **(c)** executed pose and revision, **(d)** outcome `draft`/`blocked`/`failed`, **(e)** concrete failing diagnostics, **(f)** feedback ZIP path, **(g)** whether visual review was done. Never claim a success that the evidence doesn't establish.

## 10. Design limitations

The engine restores critical historical rig-control mechanics (Rigify IK setup, world torso movement, palm-frame orientation, evaluated-mesh floor calibration) and adds more useful *failure detection*. The initial numerical targets are unverified. Knee contact patches are approximated from material regions around deformation-joint heads; a near-zero patch height is not a complete stability solution. No full signed mesh penetration solver, physics, anatomical validation or user approval is available in this upgrade. Expect further calibration iterations.
