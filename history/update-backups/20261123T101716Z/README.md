# SPOSE Remote Blender Library

**Standalone experimental branch of the user's mannequin-pair Blender library.** This release uses a full 28-family SPOSE source and a V00-first modular pose pipeline; it does not overwrite the separate local library.

## Current source and goals

| Item | Value |
|---|---|
| Active source | `SRC003/v001`, checkpoint `20261122T013728Z` |
| Source rows | 3,036 records, 28 families, 51 columns |
| First milestone | All 276 distinct V00 bases across all families |
| Later phase | Remaining 2,760 V01–V10 records, only after global V00 completion and explicit authorization |
| Rig pair | `CPL01/v001`, BP001/v001, RIG001/v001 and VP001/v001 |
| Current acceptance | See `ROADMAP.md`/`ROADMAP.json` (derived from SQLite) |
| Blender test status | Remote scripts not verified in Blender in the authoring environment |

## Read this first

- [CONTINUATION.md](CONTINUATION.md) — authoritative cold-start handoff and current decisions.
- [ROADMAP.md](ROADMAP.md) — family-level progress table plus checkbox for every V00; generated, not hand-edited.
- [ROADMAP.json](ROADMAP.json) — machine-readable states and source fingerprints; generated.
- [AGENTS.md](AGENTS.md) — AI/operator preservation and authority rules.
- [SKILL.md](SKILL.md) — full operational playbook.
- [WORKFLOW.md](WORKFLOW.md) — detailed action stages R00–R09.
- [docs/COLD-START.md](docs/COLD-START.md) — step-by-step fresh-session and laptop start.
- [docs/HANDOFF-DESIGN.md](docs/HANDOFF-DESIGN.md) — full-vs-portable library contract.
- [docs/POSE-MODULE-AND-FEEDBACK.md](docs/POSE-MODULE-AND-FEEDBACK.md) — JSON module and revision loop.

## First commands (run from inside the **full** `remote/` folder)

```powershell
python scripts/check_remote.py
python scripts/update_roadmap.py --check
python scripts/package-library-for-remote.py --dry-run
python scripts/package-library-for-remote.py
```

To import a V00 package from a future authoring session:

```powershell
python scripts/import_pose.py incoming/DOGG-DOGG-V00_YYYYMMDDTHHMMSSZ.zip --dry-run
python scripts/import_pose.py incoming/DOGG-DOGG-V00_YYYYMMDDTHHMMSSZ.zip --blender "C:\path\to\blender.exe"
python scripts/export_feedback.py DOGG-DOGG-V00 --revision 1
```

**Do not run `review_pose.py` until you have actually inspected renders and chosen a decision.** A draft package or successful Blender execution is not an accepted pose.

## Two ZIPs: very different purposes

1. **Full library:** `spose-remote-library-YYYYMMDDTHHMMSSZ.zip` contains only root `remote/`, including the large shared `.blend` assets, full CSV, tracker, scripts and documentation. Install this once on the user's Blender machine; keep backups before upgrades.
2. **Portable context handoff:** `spose-remote-handoff-YYYYMMDDTHHMMSSZ.zip` created by `scripts/package-library-for-remote.py`, also root `remote/` but deliberately **not runnable**. It excludes meshes, `.blend`, images, SQLite and the huge full catalog. Instead it carries the 276 full V00 source rows, all pose IDs+hashes, rig maps, process docs, roadmap and latest lightweight status. Upload this smaller ZIP to future assistant sessions. **Never extract this handoff over the runnable library.**

The portable handoff lets a future assistant prepare a data-only V00 package with `scripts/package_pose_from_handoff.py`. The owner executes and verifies it in their own full remote Blender library. If local assets/catalog changed, regenerate the handoff.

## Folder map

```text
remote/
  AGENTS.md, SKILL.md, WORKFLOW.md, CONTINUATION.md, ROADMAP.md, ROADMAP.json
  docs/                         detailed cold-start, contracts, troubleshooting
  project.json                  configuration, asset versions, production flags
  source/                       3,036-row catalog, frozen source references
  body_profiles/                shared character master and metadata
  pairs/                        shared CPL01 pair template and appearance study
  visual_profiles/              independent actor color/region profiles
  tooling/                      original character/rig inspection utilities
  scripts/                      modular imports, renders, QA, tracking and handoffs
  schemas/                      pose ZIP schema and examples
  incoming/                     one ZIP per requested pose/revision
  poses/<POSE_ID>/.../rNNN/      versioned modular results (no full scene by default)
  tracking/progress.sqlite       remote job/review authority
  history/                      frozen local pilots, not active remote work
  reports/                      feedback ZIPs and QA
```

All paths are intended to be relative to the `remote/` root. The existing local pilot `UFDG-FWCH-V00` is explicitly excluded; `UFDG-FWCH-V01` remains a contact-review draft. Both are historical evidence, not approved templates. Shared body/pair/appearance profiles remain unapproved, so this is a development library.
