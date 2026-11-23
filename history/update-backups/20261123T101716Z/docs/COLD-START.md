# Cold-start guide — resume SPOSE Remote in a new session

This is written for an assistant or operator who **has no previous conversation history**. The user owns a standalone Blender library called `remote/` and wants to construct modular V00 pose candidates for 28 SPOSE families. The original user's local library is a separate branch and must never be overwritten by this fork.

## The first thing to identify: which ZIP is this?

| ZIP | Contents | Intended use | What to NEVER do |
|---|---|---|---|
| `spose-remote-library-<UTC>.zip` | Full `remote/` including Blender assets, full source catalog and SQLite | Install/maintain local runnable remote library | Modify the user's separate `local/` or silently replace live remote progress |
| `spose-remote-handoff-<UTC>.zip` | Small `remote/` subset: docs, rig/source metadata, full 276 V00 rows, progress snapshots, scripts | Upload to assistant in any future session to resume authoring | Replace full `remote/` or claim this package can execute Blender |
| `{POSE_ID}_{UTC}.zip` | Six-or-fewer allowed declarative pose JSON files | Import ONE pose candidate into the full remote library | Execute Python supplied inside ZIP or treat hashes as digital signatures |
| `{POSE_ID}_rNNN_feedback_<UTC>.zip` | Preview PNGs, validation, measured proxies and build log | Diagnose/revise a specific Blender attempt | Treat feedback as complete library state |

All ZIPs above have different roles. The pose package ZIP does **not** contain `remote/` as root; the two library/handoff ZIPs do.

## Session boot checklist

- [ ] Inspect ZIP name and root. Full/handoff ZIPs have only `remote/`; pose ZIP is a flat root with `manifest.json` and JSON payloads.
- [ ] Read `CONTINUATION.md` and `ROADMAP.md` before deciding which base to work on.
- [ ] Read `AGENTS.md`, `SKILL.md`, `WORKFLOW.md`, `project.json`, `source/dataset.json` and package contract.
- [ ] Check that active catalog is `SRC003/v001`, source checkpoint `20261122T013728Z` or newer only if documented, and that the pinned SHA-256 matches.
- [ ] Confirm whether the user has supplied the latest tracker snapshot and (when applicable) pose feedback ZIP.
- [ ] Confirm V00-only phase; do not begin V01–V10 merely because a selected family is complete.
- [ ] Record the selected V00 ID, complexity/gate, row hash, pair template hash, expected bone controls and contact hypotheses.
- [ ] Never claim successful Blender execution unless actual rendered artifacts/logs from that run are provided.

## Starting from full remote library

Extract full ZIP to a new temporary folder. Avoid overwriting an active working copy. From inside `remote/`:

```powershell
python scripts/check_remote.py
python scripts/update_roadmap.py --check
python scripts/package-library-for-remote.py --dry-run
```

If check fails, investigate rather than altering source hashes. Read `source/SPOSE-FULL-20261122T013728Z.csv` for the selected `V00`. Inspect `pairs/CPL01/v001/pair.json`, `body_profiles/BP001/v001/profile.json`, `tooling/rig-maps/RIG001-v001.json` and historical failure notes. Build one data-only package with `scripts/package_pose.py` and verify with importer `--dry-run`. Only the user's machine with Blender can render.

## Starting from portable context-only handoff

After extraction, look for `remote/handoff/HANDOFF-MANIFEST.json`, `remote/handoff/SESSION-START.md`, `remote/source/V00-CATALOG.csv`, `remote/source/POSE-INDEX.csv`, and `remote/source/pose-dependencies.json`. The full source CSV, Blender files and SQLite DB are **intentionally absent**. Read V00 row text from `V00-CATALOG.csv`; source dependencies contain the exact frozen row/spec and template hashes needed to create a data-only input ZIP.

Use:

```powershell
python remote/scripts/package_pose_from_handoff.py DOGG-DOGG-V00 draft-folder --output outgoing/
```

That only constructs and structurally validates the pose ZIP; it does not test geometry. Send the resulting pose ZIP to the user, who runs the full importer locally. If the user's real remote source/template has changed, importer will reject the stale package. Re-export the small handoff from the new real library before creating further modules.

## What exactly can be done without Blender?

A new assistant can inspect all 276 V00 definitions, compare source family geometry, create draft root/IK targets, write contact hypotheses, validate package names/types/hashes, update operating scripts/docs, and produce pose ZIPs. It **cannot** observe evaluated meshes, solve constraints reliably, certify contact, save a visually verified `.blend`, or mark source errors as resolved. When the user provides feedback previews and measurements, the assistant can iterate by creating a new revision package.

## How to choose a first family

The intent is **complete all V00 bases, family by family, before variants**. The family roadmap table and per-base checkboxes are automatically generated. Choose a family with straightforward, low-complexity support first, such as grounded/reclining arrangements. Avoid using an excluded historical pilot as an approved template. Prefer source `PASS` over `REVIEW` for early tests, but `PASS` does not certify physical or rendered validity. Work one pose at a time until contact QA is reliable, then scale family-wise.

## What evidence is needed for each imported pose?

At minimum: source row hash, input package hash, control list, Blender log/version, saved preview images (front, side, three-quarter), contact proxy results, human visual review note, and revision status. If accepted, the user runs `scripts/review_pose.py` with an explicit decision; the tracker and generated roadmap advance. An image render without a human review note remains a draft.

## When to generate a new handoff

- After a pose is imported or reviewed, before switching to a new AI session.
- After scripts or documentation change, because an old handoff will not contain new tooling.
- After source catalog, pair, appearance or rig versions change—template SHA pinning prevents stale input packages.
- After a difficult contact review, include the separate pose feedback ZIP if images matter: handoff intentionally omits images to stay small.

**Never describe a context ZIP as a self-contained Blender library.** It preserves enough verified context to continue authoring; the runnable assets and authoritative SQLite state live on the user's machine.
