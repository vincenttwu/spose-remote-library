# CONTINUATION — SPOSE standalone remote, batch-first checkpoint

## Exact project identity

Project ID: `SPOSE-REMOTE-LIBRARY`. The full library is independent of the local-origin library; its folder name need not be `remote/`. Full active catalog: `SRC003/v001`, checkpoint `20261122T013728Z`, SHA-256 `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6`, 3,036 rows / 28 families / 276 V00 bases. Rig: `CPL01/v001`, `RIG001/v001`, pair reference Blender 5.2.2 LTS. The attached current portable handoff is the evidence of actual tracker status, not this static document.

## User-confirmed policy, latest and authoritative

- **All five pose modules per batch are attempted and rendered in the same workflow**, with one combined batch report. Never reduce a batch to testing one pose and stop because of a geometric issue.
- **No gating by source PASS/REVIEW/EXCLUDE, geometry score, human review/acceptance, or family milestone.** All are reference/status information. Unstable and unreviewed Blender drafts remain usable.
- V00-first is only a scheduling preference; complete family sets over time, move to next batches even when previous batches need refinement. Variations are planned later, not forbidden by a validator.
- Preserve versioned work; never overwrite prior rNNN or original template. The portable handoff, used for new chat uploads, is context only and must not overwrite the full library.

## Technical state and r002 feedback

Earlier V1 batch of DOGG, CLSD, DOWN rendered wrong standing and floating contacts. V2 r002 calibration DOGG-DOGG shows rear kneeling established (A hip 0.665m, knee 96°), front over-folded (B hip 0.272m, knee 44.86°), ten floor supports close to zero and pelvis bone anchor gap 0.476m. It is **not stable geometry**. These numbers came from uploaded feedback; they do not verify current revisions.

This release changes the workflow to run all five and emits r003+ numerical hypotheses for DOGG/CLSD, smaller correction for FROG, and preserves the face-down and standing character of FCDN/DOWN respectively. None of the five new modules were Blender-rendered in the assistant environment.

## Expected Batch 001

`DOGG-DOGG-V00`, `DOGG-CLSD-V00`, `DOGG-DOWN-V00`, `DOGG-FCDN-V00`, `DOGG-FROG-V00`, all under `batches/BATCH-001.json` and one bundle ZIP. The local agent executes `scripts/run_pose_batch.py` and produces a combined feedback ZIP. No pose needs accepted/validated state before next batch.

## Cold-start procedure

Read `GUIDE.md` and `WORKFLOW.md`; then read current local `ROADMAP.json` or handoff `handoff/SNAPSHOT-STATUS.md`, then the `batches/` plan. If source/rig changed, do not invent compatibility; update source fingerprint safely. Produce one small pose-package bundle, not another complete library. Enforce data safety, not quality approvals.
