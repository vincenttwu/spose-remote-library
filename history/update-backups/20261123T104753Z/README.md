# SPOSE Standalone Remote Library (fork)

This is a self-contained independent Blender library and may live in a folder of any name. No outer `remote/` prefix. Shared assets `BP001/v001`, `CPL01/v001`, `RIG001/v001`, `VP001/v001`. Active source `SRC003/v001`, 28 families, 276 V00, 3,036 rows. All 276 V00 first, then variants only with explicit approval. Status is `ROADMAP.md`/`ROADMAP.json` generated from local tracking.

**Geometry engine v2** fixes first-batch standing-only regression by introducing world-space torso placement, Rigify IK setup, mesh-floor calibration and posture/support hard gates. Old pose ZIPs without the v2 marker intentionally cannot import after upgrade. New candidates still require actual local Blender test.

Read `CONTINUATION.md`, `SKILL.md`, `WORKFLOW.md`, `docs/GEOMETRY-ENGINE-V2.md` before continuing. Run `python scripts/check_remote.py` for library readiness. Run `python scripts/package-library-for-remote.py` for a context-only, **flat-root** handoff to new sessions. The handoff must not replace the runnable library.

## For the local agent

Start with **`GUIDE.md`** in this bundle. It describes safe installation, the first-only calibration run, diagnostics, feedback ZIP exports and explicit-review rules. This is one upgrade bundle; the individual pose ZIPs are already nested under `pose-packages/`. The current Batch 001 scope is five DOGG-family V00 candidates: DOGG, CLSD, DOWN, FCDN and FROG.
