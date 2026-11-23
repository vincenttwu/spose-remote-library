# Troubleshooting — record and continue

If an individual pose has floating support, poor posture, misaligned hips, mesh penetration, or a failing contact proxy, record the issue and **continue the other four**. A rendered draft stays usable with a `needs_work` annotation. Generate combined feedback after all five attempts, not a per-pose approval request.

If Blender raises a fatal exception for one pose, preserve its output/logs and continue processing the other items. If source/template hashes or ZIP safety checks fail, do not install unsafe input; report the affected item and continue to the next valid package. This is data protection, **not** quality gating.

`ROADMAP.md` updates built/attempted progress regardless of approval. Run `python scripts/update_roadmap.py` to regenerate if snapshots appear stale. Report actual Blender failures honestly; an offline ZIP dry-run cannot establish geometry quality. Do not modify the full library's original assets, historical revisions or tracking database manually.
