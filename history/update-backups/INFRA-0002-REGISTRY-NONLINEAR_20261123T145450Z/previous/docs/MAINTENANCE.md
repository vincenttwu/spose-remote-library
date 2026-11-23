# Maintenance — installer, scripts, compression, rollback

## Safe release installation

A maintenance bundle is a *separate release*, not a pose pass. Extract outside the live library. Use `install-update.py --library "<LIBRARY>"` for dry-run and add `--apply` only after confirming replacement paths. The installer preflights every manifest SHA-256, catalog and shared template fingerprint, and restricts destinations to named root Markdown, `docs/*.md` and `scripts/*.py`. It does **not** touch the tracker, source, rig assets, pair template, incoming modules or pose revisions.

The update ZIP has a flat root with `updates/<DESTINATION>` files as payload. The installer copies those to canonical locations. Local `updates/installed/` contains infrastructure receipts/pointers; the active executable is under `scripts/`, not duplicated inside a persistent update payload folder. A rollback receipt resides under `history/update-backups/<RELEASE>_<UTC>/INSTALL-RECEIPT.json` with original files and before/after hashes.

Rollback command (from extracted upgrade folder):

```powershell
python install-update.py --library "<LIBRARY>" --rollback "<LIBRARY>/history/update-backups/<RELEASE>_<UTC>/INSTALL-RECEIPT.json"
```

If a target has changed since installation, rollback refuses to overwrite it. Inspect changed files and reconcile manually. Never run cleanup against source, SQLite or historical pose revision directories.

## Script inventory

| Canonical local script | When to run | Output/notes |
|---|---|---|
| `run_pose_batch.py` | Whole five-pose batch | Five result rows, permanent snapshot; triggers one feedback export |
| `refresh_exchange.py` | After an existing run or deletion of disposable folders | Fresh flat PNGs and one feedback ZIP, **no Blender rerender** |
| `feedback_bundle.py` | Called by refresh; library function | One ZIP with per-pose evidence and embedded context |
| `compress_images.py` | Compression test/individual conversion | Lossless WebP/optimized PNG, verifies RGBA byte equality |
| `verify_feedback.py` | Before sending single ZIP | Checks ZIP members, hashes, pose count and available images |
| `update_continuation.py` | After a run; on cold start | Regenerates `CONTINUATION.md` from live metadata |
| `check_documentation.py` | After install or docs changes | Warns about absent/underspecified/stale operating docs |
| `package_library_for_remote.py` | Compatibility/context export | Produces compact context-only handoff; embedded by feedback exporter |
| `update_roadmap.py` | Derived state refresh | Derived ROADMAP; SQLite remains authoritative |
| `check_remote.py` | Technical library sanity | Asset/source/rig preflight, not a geometry approval |

Legacy `scripts/export_feedback.py` remains available for isolated pose debugging, but is not the routine batch exchange. Do not call it five times and nest five ZIPs under another ZIP as the default workflow.

## Python dependencies

The compression scripts run in regular Python on the user's computer, not necessarily in Blender's embedded interpreter. `Pillow` supplies exact-pixel lossless WebP. Check with `python -c "from PIL import Image; print(Image.__version__)"`. If unavailable: `python -m pip install Pillow`. Do not require installation for safe batch execution; default fallback is original PNG and a warning.

## Compression and reproducibility

The exporter reads only stored `poses/<ID>/.../previews/*.png`. For opaque RGBA, converts to RGB WebP lossless, then decodes to RGBA and checks exact byte identity. For nonopaque RGBA, preserves transparency and verifies the same way. Exact-pixel mismatch raises an integrity error; absence of WebP support triggers original-PNG fallback. The original PNGs, reference render settings and validation JSON remain unchanged.

To compact an existing batch *without rendering*: `python scripts/refresh_exchange.py`. Validate with `python scripts/verify_feedback.py "upload/<ZIP>"`. Check `upload/manifest.json` for selected snapshot and PNG list, and ZIP `manifest.json` for codec counts, warnings and embedded context. If optional context packing fails, the manifest must say `context_included=false`; repair source/handoff dependencies rather than silently claiming self-contained export.

## Freshness vs. truth

`CONTINUATION.md`, `ROADMAP.json`, review images and feedback are **derived**. Their snapshot timestamp matters. The authoritative current state is the actual local library and tracker. For true Pass 02/03 geometry improvement, author new module contents and package timestamp/identity; a new pass label alone does not regenerate. Do not alter the geometry quality score by changing validation tolerances. A quality failure never stops the rest of a batch.

## Verification expectations

Offline installer tests: digest verification, no self-hash manifest, traversal guards, backups/rollback, idempotence and target library identity. Evidence tests: all five result rows even with partial failed builds, correct view naming, exact-pixel codec verification, embedded context checksum, refresh after disposable folders deleted. A fake/simulated Blender test covers orchestration **only**. Real Blender rig/pose fidelity requires rendered evidence and user evaluation.
