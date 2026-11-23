# Remote tracking handoff

The full remote's `tracking/progress.sqlite` is the only authority for imported job/review states. At this documentation checkpoint there are no remote jobs and no accepted V00 poses. Old local pilot attempts are historical under `history/`, excluded from this tracker. All 276 V00 bases are pending according to the new ROADMAP.

Generated views: `tracking/progress.csv`, `tracking/events.jsonl`, `ROADMAP.md`, `ROADMAP.json`.

After each import or manual review, update_tracking exports snapshots and regenerates the roadmap. Run `python scripts/update_roadmap.py --check` to confirm. A future session with only a small handoff sees a read-only snapshot, not the live SQLite. Regenerate the portable handoff whenever the user has new local progress.

Global project gate: all 276 V00 first, no V01–V10 until all are accepted and the user separately authorizes variations.
