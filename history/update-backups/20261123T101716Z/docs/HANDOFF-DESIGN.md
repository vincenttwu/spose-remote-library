# Portable handoff design — `package-library-for-remote.py`

## Goal

Enable future assistant sessions to resume anywhere from a small uploaded ZIP, without repeatedly uploading the ~60 MB full remote library and its Blender scene assets. Preserve enough context for **V00 authoring, source consistency, rig target naming, progress status and workflow rules**, while keeping the full runnable library on the user's machine.

## Two-layer architecture

1. **Full runnable `remote/` (local):** canonical full CSV, scene `.blend` files, shared BP001/CPL01/VP001 assets, Rigify maps, authoritative SQLite tracker, original imported pose packages, renders, QA artifacts, logs, history and generated roadmap. This is the operational state.
2. **Portable handoff `remote/` (upload):** docs, scripts, schemas, rig maps/metadata, source registration/cryptographic fingerprints, all V00 specifications, index/hash for every pose ID, derived roadmap, tracking summaries, and *latest lightweight* pose-state/rig-target metadata when any exists. This is **context only**.

The identical root name `remote/` keeps paths readable in future sessions but creates a serious collision risk. **Never unzip a portable handoff into the live full `remote/` directory.** Extract into a new temporary review directory or upload directly to a chat.

## Input and command

From the full `remote/` folder:

```powershell
python scripts/update_roadmap.py --check
python scripts/package-library-for-remote.py --dry-run
python scripts/package-library-for-remote.py
# or specify a handoff destination:
python scripts/package-library-for-remote.py --output "C:\SPOSE\handoffs"
```

Result: `spose-remote-handoff-YYYYMMDDTHHMMSSZ.zip` next to `remote/` by default. The ZIP root is exactly `remote/`; its manifest is `remote/handoff/HANDOFF-MANIFEST.json`. All member hashes (except self-referential manifest) are computed from bytes at export.

## Included material and why

| File group | Included | Why |
|---|---|---|
| `AGENTS.md`, `SKILL.md`, `CONTINUATION.md`, `WORKFLOW.md`, README, `ROADMAP.*` | Yes | Controlling instructions, current plan and progress |
| `docs/`, `schemas/`, `scripts/*.py`, original `tooling/scripts/*.py` | Yes | Complete procedural and implementation knowledge for future edits |
| `project.json`, `source/dataset.json`, reference registrations | Yes | Exact active dependency identities |
| `source/V00-CATALOG.csv` | **Generated, yes** | Full 51-column source rows for all 276 V00 bases (includes full original specification text) |
| `source/POSE-INDEX.csv` | **Generated, yes** | All 3,036 IDs, family, variation, title, complexity/gate and specification SHA |
| `source/pose-dependencies.json` | **Generated, yes** | Frozen per-V00 source-row SHA and template/pair/rig dependencies for offline package creation |
| `tooling/rig-maps/*.json`, pair/profile/visual metadata | Yes | Rig control names, actor dimensions, scene metadata and asset fingerprints |
| `tracking/progress.csv`, milestones, roadmap | Yes | Current derived status; not writable authority |
| Latest `poses/*/rNNN/*.json` and input JSON | Yes, if small | Target controls/contact metadata for continuity after successful local imports |
| `.blend`, large source CSV, full SQLite, renders, JPG/PNG, ZIPs, all history | **No** | Heavy, not needed for textual session restart, and would bloat chat uploads |

The generated V00 CSV is **a read-only derivative** from the pinned full catalog. It does not replace `source/SPOSE-FULL-20261122T013728Z.csv` in the real library. The full CSV remains authority. A fresh session cannot reconstruct arbitrary V01–V10 specifications from the handoff; that's intentional because the current production phase is V00-only.

## Safety and integrity properties

- Explicit allowlist avoids carrying large or unknown files accidentally; no recursive archive of data binaries.
- Validates active source SHA, registered counts, pair template SHA and generated roadmap consistency before packing.
- Creates and verifies a SHA-256 map for all context members. SHA-256 catches accidental corruption but is **not a digital signature** against malicious replacement.
- Does not store passwords, secret keys, scene asset data or original absolute local files. Historical Windows paths may still appear inside provenance metadata; treat as labels, not runtime dependencies.
- Does not mutate the full catalog or the authoritative SQLite.
- Fails on unexpected oversized/non-text docs or scripts rather than silently including them.

## Offline authoring from handoff

A fresh assistant reads `source/pose-dependencies.json` and the V00 row. Drafts `pose.json`, `rig-targets.json` and `contacts.json`, then runs:

```powershell
python remote/scripts/package_pose_from_handoff.py UFDG-QUAD-V00 draft-folder --output outgoing/
```

The output is exactly the standard `{POSE_ID}_{UTC}.zip` module, with dependencies taken from the handoff. The full remote's `scripts/import_pose.py --dry-run` recomputes live source/template hashes and refuses stale metadata. The offline script does **not** render a pose or verify joint reach.

## Freshness rule

If the user has imported/reviewed any pose since handoff creation, the handoff's roadmap is stale. Request the updated handoff or relevant feedback before deciding work is complete. If the template, source or rig map changed, **always regenerate** the handoff before authoring new packages. Don't patch hashes manually.

## Size strategy

A full source has 3,036 × 51 fields and shared `.blend` files; a cold-start assistant only needs 276 full V00 rows plus all IDs+hashes and minimal metadata. ZIP compression will reduce repeated text further. The exact output size depends on future text and revision counts; the packager reports the actual byte size. The included last-revision JSON only avoids requiring large PNG/scene files until a specific pose needs visual feedback.

## What if the user loses the full library?

The handoff is **not a backup**. It does not contain the mannequin rig, character meshes, complete variation descriptions, SQLite event history, or rendered outputs. Full archive/backups must still be kept separately. The small handoff preserves **working context**, not all binaries.
