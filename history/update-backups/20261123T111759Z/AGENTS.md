# AGENTS.md — SPOSE batch operator contract

**User priority: run all five poses per batch. Geometry, source flags, approval and milestone states are NOT gates.** Record every item, continue after failure, and export a combined report. A rendered `draft` remains usable even with `needs_work` stability. `accepted` is an optional human label and never required to proceed. Do not suppress warnings or fake clean geometry.

Read `GUIDE.md`, `WORKFLOW.md`, `CONTINUATION.md`, `SKILL.md`. Respect library project ID `SPOSE-REMOTE-LIBRARY`; do not overwrite original local library, source catalog, shared `.blend` templates, existing revisions, SQLite tracker or human review records. ZIP format, checksums, no script execution from modules, path safety and installer backups remain mandatory for data integrity.

Batch scope: five DOGG V00 modules. Render **all five** using `scripts/run_pose_batch.py`; one combined feedback ZIP. Quality review is optional and may happen later. Do not tell the user they must approve any individual pose before moving on.
