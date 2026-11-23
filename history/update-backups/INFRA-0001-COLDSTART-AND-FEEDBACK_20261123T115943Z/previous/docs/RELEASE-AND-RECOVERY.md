# Release installation and recovery

The ZIP is a flat-root incremental update (not a full library). Extract to a separate temporary folder. Verify `project.json` identity in the installed standalone library; run `python install-update.py --library <PATH>` to preflight, then `--apply`. Only manifested docs/scripts, the batch plan and new pose ZIPs are installed. Catalog, `.blend` pair templates, SQLite, existing pose revisions and human review history are preserved.

Installer's hashes, path traversal controls, immutable revision naming and backup/rollback are **file-integrity controls**. They do not enforce source REVIEW/EXCLUDE values, geometry accuracy, acceptance, or global V00 completion. If install fails due genuine file corruption, repair the input or recover from the timestamped backup. If a pose's geometry is wrong, do not roll back the entire library: record it as `needs_work` and keep processing.

One batch execution produces a combined feedback ZIP, and a later handoff can be generated with `scripts/package-library-for-remote.py`. Context handoffs are not runnable and must not replace the full installed library. Never pretend a simulated offline run is a Blender physical verification.
