# Tracking and roadmap — progress without approval gates

**Tracker authority:** `tracking/progress.sqlite`. Imports and optional manual reviews write independent versioned pose records. `ROADMAP.json`, `ROADMAP.md`, and CSV are derived reports; regenerate with `python scripts/update_roadmap.py`.

**Count separately:** `attempted` = pose has at least one tracked job (failed or successful); `built` = has at least one matching-source `draft`, `validated`, `accepted` or historical `blocked` rendered revision; `accepted` = optional human label on a revision. `needs_work` stability warnings do not turn a usable draft into a failed import.

Roadmap checkbox `[x]` means **built**, *not* stable, correct, or accepted. Families can move to next batches at any time even if a former batch is unstable. V00-first is only a scheduling preference. Source `generation_gate` values are metadata and must never alter progress permissions.

`hard_gate_pass` remains in older result JSON for compatibility only; new `geometry_reference_pass`/`stability` express warnings. No validation flag may stop a batch runner or stop future scheduling. Keep all measurements for future improvement.
