# Workflow — batch-first, no approval gates (0.9.2)

## W00. Goals

The standalone SPOSE remote library uses a fixed mannequin pair, catalog-pinned data-only pose ZIPs, versioned Blender outputs and SQLite tracking. Deliver **one bundle per five poses** as the default. Current schedule: all V00 bases, family by family; variations can be scheduled later. No completed/accepted prerequisite is required to begin any next batch.

## W01. One-time update per engine revision

Extract update ZIP outside the full library; use `install-update.py --library <PATH>` dry-run and `--apply`. Only manifested files and incoming ZIPs are copied; old scene files, CSV and tracking are not replaced. Backup is automatic. Bundle ZIP has a **flat root**.

## W02. Prepare all five

A batch plan under `batches/*.json` gives five pose ZIP filenames, each with source/pair/rig fingerprints and v2 controls. The module cannot execute scripts embedded in a ZIP. Geometry targets are numerical hypotheses, not approval criteria.

## W03. Execute all five

`python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender <BLENDER_EXE>`.

The runner processes every item in order, regardless of other items' instability or execution errors. It never uses the first item to stop the batch. It retains individual versioned `poses/POSE-ID/CPL01/v001/rNNN/` revisions. A failure is recorded and the next item proceeds.

## W04. Record measurements, not barriers

Each Blender build measures floor support, knees, hips, head height, contact proxies and surface proximity. It renders front, side, three-quarter and QA views. Geometry deviations appear as warnings. A rendered revision is **draft/usable** whether or not those warnings exist. `hard_gate_pass` remains in legacy diagnostic JSON for compatibility only; **no code treats it as permission**. Human acceptance is optional and separate.

## W05. Combined batch feedback

After executing all five, write one `reports/BATCH-..._combined_feedback.zip` containing the batch JSON/Markdown matrix and individual feedback ZIPs. If an item failed, its error and log extract are still represented. Send this combined ZIP instead of five separate chat uploads.

## W06. Roadmap and next batch

SQLite records each attempted revision. Generated `ROADMAP.md` and `ROADMAP.json` distinguish **attempted**, **built**, **stability warnings**, and **accepted**. A built V00 counts as processed; unreviewed or unstable is not a reason to pause or ask for permission. Refresh portable handoff after a batch. Continue to next five whenever user directs.

## W07. Data and file safety (not quality gates)

ZIP identity checks, path-traversal protection, known dependency fingerprints, immutable historical revisions, and installer backup/rollback remain necessary to avoid accidental corruption. These are integrity checks, not source or geometry approvals.
