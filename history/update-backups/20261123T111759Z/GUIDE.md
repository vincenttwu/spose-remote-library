# GUIDE.md — Local agent: perform the WHOLE batch, with no review gates

The user wants **five poses executed per batch**. **Do not stop after one unsuccessful/unstable pose.** Do not request five separate approvals. Geometry diagnoses are status notes, not permission checks. Source `generation_gate=PASS/REVIEW/EXCLUDE` is descriptive only. Do not mark anything human accepted automatically.

## 1. Find installed library

User's last known full library: `C:\Users\hyper\Documents\GitHub\spose-remote-library`. Verify the real folder yourself; do not assume location. Its `project.json` should say `SPOSE-REMOTE-LIBRARY`; it must contain `pairs/CPL01/v001/template.blend`, `source/dataset.json`, `tracking/progress.sqlite`, and `scripts/`. The `remote/` wrapper is neither expected nor required.

The upgrade ZIP is *not* the full library. Extract it into a **temporary folder**, not over the installed library. Close any process currently writing to its tracking database. Make a normal backup before installation.

## 2. Install, safely and idempotently

From the extracted ZIP root:

```powershell
python install-update.py --library "C:\Users\hyper\Documents\GitHub\spose-remote-library"
python install-update.py --library "C:\Users\hyper\Documents\GitHub\spose-remote-library" --apply
```

Preflight verifies files without changing the library. Apply backs up replaced files under `history/update-backups/` and stages five new ZIPs under `incoming/`, plus `batches/BATCH-001.json`. Keep all prior revisions, renders, reviews and tracking unchanged. Verify `CURRENT-INSTALL.json` and `INSTALL-RECEIPT.json` where written.

## 3. Run the batch once, not one pose at a time

From inside the full installed library:

```powershell
python scripts/check_remote.py
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --dry-run
python scripts/run_pose_batch.py --plan batches/BATCH-001.json --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

The Blender path shown is **illustrative**: check your installed executable first. Use `--save-blend` only if full debug scenes are needed. Use `--rerun` if you intentionally want new revisions from packages already imported. The batch runner attempts all five even if a Blender build fails or geometry warnings are severe; it records those separately. Never silently omit FCDN or FROG because an earlier batch had only three pose folders.

## 4. Return one combined evidence ZIP

The command prints `combined_feedback_zip`, saved under `<LIBRARY>/reports/`. This ZIP contains a complete five-pose summary plus individual pose feedback ZIPs for each successfully imported revision. Upload that one combined ZIP to the remote assistant, along with a refreshed portable handoff when possible:

```powershell
python scripts/update_roadmap.py
python scripts/package-library-for-remote.py
```

If some poses have missing previews or failed, the report must still include those rows. No batch is globally “blocked.” Record stability as `needs_work`, `unreviewed`, or user-specified notes, without confusing them with `accepted`.

## 5. State semantics and continuation

- `draft`: successfully rendered, **usable even if geometry is poor**.
- `needs_work`: independent quality annotation, not a block.
- `failed`: execution did not complete; preserve logs and proceed to next pose.
- `accepted`: optional human label; NOT required to build another pose or batch.
- Source `REVIEW`, `EXCLUDE`: reference notes, NOT importer or review permission.
- `ROADMAP.md`: checked = built (includes historical blocked renders); not “approved.”

Advance to another batch whenever the user chooses. V00-family ordering is a planning preference, not a mechanism that prevents moving forward.

## 6. Important evidence for Batch 001

`DOGG-DOGG-V00` r002 previously showed A hip ~0.665m, B hip ~0.272m, and both ground supports technically passed. The new batch packages include tentative per-silhouette adjustments, and extra geometry reporting helps compare all five. **Do not assert that r003 is physically correct just because the batch runner completes.** Unstable results are still valid work products and can be revisited.
