# Cold-start continuation (read before operating)

This is an independent standalone Blender library with flat-root ZIP update packages. Read `GUIDE.md`, `WORKFLOW.md`, `SKILL.md`, `CONTINUATION.md`, then the latest local `ROADMAP.json` and batch plan. A compact remote handoff contains metadata but not `.blend`, full CSV or SQLite. Do not extract it over the full library.

Current authoritative user decision: process **all five poses in each batch**. Never stop for poor geometry, unapproved characters, missing human review, source REVIEW/EXCLUDE, or an unstable previous family. Keep problems visible as warnings and follow-up items. Carry source/template checks and revision-safe installation as data-integrity safeguards.

Use `python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender <EXE>` on installed full library and send the one `reports/*combined_feedback.zip` plus compact handoff. Accept/approve labels are optional and not prerequisites for future work.
