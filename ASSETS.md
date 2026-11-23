# External Core Assets (Backup & Restore Reference)

This Git repository is **data-only**: it tracks all scripts, documentation, batch plans, data-only pose packages (`incoming/`), pose target JSONs, calibration measurements, snapshot metadata, and the SQLite tracker (`tracking/progress.sqlite`).

Heavy rebuildable artifacts (`poses/**/scene.blend`, rendered `.png`/`.webp` previews, generated feedback `.zip`s, and disposable `local/`, `review/`, `upload/`, `reports/` folders) are excluded via `.gitignore` and can be regenerated with Blender from the tracked data.

## Required External Core Assets (~94 MB total)

Four immutable base files are **not** stored in Git and must be restored into a fresh clone before running Blender builds or `scripts/check_remote.py`:

| Relative path in library | Size | Verified SHA-256 | Role |
| --- | ---: | --- | --- |
| `pairs/CPL01/v001/template.blend` | 21,787,155 B (~20.8 MB) | `154ca2f56e4daf23f85ad788a55aacd4849ecd3a19ab7cf1dbadcf4f2cb229d0` | Authoritative CPL01 pair template (hash-checked by `check_remote.py` & `import_pose.py`) |
| `pairs/CPL01/v001/studies/VP001-v001/appearance-study.blend` | 22,512,734 B (~21.5 MB) | `aa36d89d3f44b2864741661d031dd65afe345326087bcfc6cea5a8299aa25fad` | Appearance study scene opened by `scripts/blender_build.py` to build poses |
| `body_profiles/BP001/v001/master.blend` | 12,304,882 B (~11.7 MB) | `e4b02d8894079b54a5033b3dfe8c9a3d485d04e59faa0a4b3ad9f05932138e04` | Base BP001 mannequin/rig master asset |
| `source/SPOSE-FULL-20261122T013728Z.csv` | 41,915,931 B (~40.0 MB) | `a8fa0f89656dbc8505cdf6af64fc707ae377726bf1bfa3ea1bb72585720e10a6` | Authoritative SRC003/v001 full catalog (`3,036` records, `28` families, `276` V00 bases) |

## Backup Location

- **Original base library archive:** `spose-remote-library-20261123T082056Z.zip` (contains all 4 files above)
- **External core-pack download / cloud backup link:** _(fill in your private Drive / OneDrive / NAS link here)_
- **Reference Blender version:** `Blender 5.2.2 LTS`

## Restore & Verify on a Fresh Machine

1. Clone this repository.
2. Copy the 4 core files above into their exact relative paths inside the cloned library root.
3. Verify all core hashes, catalog integrity, docs, and registry status:

```powershell
python scripts/check_remote.py
python scripts/check_documentation.py
python scripts/registry.py status
```

4. *(Optional)* Rebuild any pose `scene.blend` and preview `.png` files from its tracked `poses/<POSE_ID>/CPL01/v001/rNNN/inputs/` JSON (or `snapshots/<RUN>/local-evidence/`) using Blender `5.2.2 LTS`.

## Git Hygiene Notes

- `tracking/progress.sqlite` is tracked directly in Git (~50–100 KB). Always pull before running local batches on a second machine, because binary SQLite files cannot be 3-way merged.
- Never commit `local/`, `review/`, `upload/`, or `tracking/exchange-activation.lock`.
