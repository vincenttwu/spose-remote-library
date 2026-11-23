# SPOSE Remote — operating workflow 0.8.0 (V00-first)

**Scope:** This procedure operates a **separate, full remote Blender library** on the user's computer, plus portable context-only handoffs used in new assistant sessions. It is not a guarantee of automatic high-quality posing. See `CONTINUATION.md` for exact status, `SKILL.md` for implementation guidance, and `ROADMAP.md` for planned/accepted V00s.

## Workflow overview

```text
Authoring session / small handoff              User's full remote/ + Blender
Read ROADMAP / V00 source row
   ↓
Create rig-targets + contacts + render plan
   ↓
Package data-only {POSE_ID}_{UTC}.zip ────────> scripts/import_pose.py --dry-run
                                                  ↓ source/rig/hash checks
                                               scripts/import_pose.py --blender ...
                                                  ↓ shared CPL01 + rig targets
                                               renders + contact proxies
                                                  ↓
Feedback ZIP / previews <───────────────────── scripts/export_feedback.py
   ↓ review with user                              ↓
Revise package or accept ────────────────────> scripts/review_pose.py (human only)
                                                  ↓
                                               SQLite + ROADMAP.md/JSON
                                                  ↓
Portable context handoff <─────────────────── scripts/package-library-for-remote.py
```

## Stage R00 — Cold start, authority and files

**Full remote:** extract the full release only into a new `remote/` directory, parallel to any local library. Do not overwrite the user's `local/`. Verify source hashes, pair files and roadmap with `python scripts/check_remote.py` and `python scripts/update_roadmap.py --check`. Check whether Blender exists locally. Inspect source registration and `tracking/progress.sqlite` for latest revisions.

**Context-only handoff:** read `remote/handoff/SESSION-START.md` and manifest; this ZIP intentionally has no executable Blender assets or SQLite. Use `source/V00-CATALOG.csv`, source dependencies, rig map, roadmap and docs to author modules. Never install context-only archive over full remote.

## Stage R01 — Select the next V00 within a family

Use `ROADMAP.md` to choose one unaccepted V00. A family can be a scheduling batch, but **no family-level early V01–V10 launch**. Prefer a simple grounded pose first; consider `complexity_pose`, source `generation_gate`, contact topology, and predecessor pilot limitations. Never promote source `PASS` to actual pose acceptance. Read the exact source row and record its hash.

Required pre-build decisions: which actor is front/rear; support surfaces; actor-root relative position; torso/pelvis line; hand/arm support; foot/floor contact; constraints; render expectations; contact targets; reason for any approximation. If actual mesh landmarks are unavailable outside Blender, mark targets provisional.

## Stage R02 — Draft one modular pose

Create a draft folder with `pose.json`, `rig-targets.json`, `contacts.json`, and optional render/validation JSON. Use only controls mapped in RIG001; write location in meters, Euler degrees for rotations and explicit coordinate-space identifiers. Do not send code/meshes in a pose module. Prefer fewer, well-defined controls; the rig has calibrated offsets and IK dependencies, so increasing controls blindly can reduce coherence.

`pose.json` may include an algorithm revision, intent, hypotheses and referenced support points. In `contacts.json`, specify anchor names and tolerances as **measurement goals**, not proof of anatomical contact. Document expected floor support independently from body-body contact.

## Stage R03 — Build and validate package (assistant/offline)

On full remote, run:

```powershell
python scripts/package_pose.py DOGG-DOGG-V00 path/to/draft --output incoming/
python scripts/import_pose.py incoming/DOGG-DOGG-V00_YYYYMMDDTHHMMSSZ.zip --dry-run
```

On small handoff, run `python scripts/package_pose_from_handoff.py DOGG-DOGG-V00 path/to/draft --output ../pose-packages/`; this script pins hashes from handoff `pose-dependencies.json`, so the receiving full remote must still independently verify current source/template dependencies.

Reject wrong ID, bad file names, non-JSON payloads, missing required fields, unsupported control spaces, stale SHA hashes, unknown bones (at Blender runtime), source EXCLUDE, non-V00 or duplicate output names. Nothing in the pose ZIP is executed as Python.

## Stage R04 — Local Blender execution

```powershell
python scripts/import_pose.py incoming/DOGG-DOGG-V00_YYYYMMDDTHHMMSSZ.zip --blender "C:\path\to\blender.exe"
```

The importer starts a separate Blender process, selects CPL01 appearance-study template or fallback pair template, applies ordered controls, renders standard views, obtains provisional contact proxies, writes logs and JSON artifacts, and creates a new immutable `rNNN` directory. `--save-blend` writes optional `scene.blend` for troubleshooting; default is lightweight JSON + previews. On error, retain stage/log information; don't overwrite previous revisions.

## Stage R05 — Contact and quality review

Review frontal, side, three-quarter and optional region QA renders. Examine foot-to-floor support, front/rear pose silhouette, hip alignment, hands actually touching specified surfaces, collision/interpenetration, camera coverage, upper-limb occlusion, pole vector behavior and finger configuration. `validate_pose.py` outputs sampled unsigned mesh proximity and bone-head anchors only; small values can coexist with wrong contact. Review both broad body alignment and local contact fit separately.

Output statuses: `draft`, `failed`, etc. **No automatic `accepted`.**

## Stage R06 — Feedback and corrective iteration

Generate feedback via `python scripts/export_feedback.py POSE_ID --revision N`. Share this compact ZIP, not the full character library. The next session inspects all images, validation, logs and original inputs before issuing a new data-only package. New package creates `r(N+1)`; it does not mutate the previous revision.

## Stage R07 — Explicit human decision and roadmap update

After the owner visually reviews the outputs, record a decision in the full remote library:

```powershell
python scripts/review_pose.py DOGG-DOGG-V00 --revision 1 --decision accepted --reviewer user --note "Reviewed front, side and three-quarter and verified contacts visually" --confirm-reviewed
```

For source `REVIEW` gate, also pass `--acknowledge-source-review`. A failed/unrendered build cannot be accepted. `blocked` can record a rejected draft with notes. Pose approval is not automatic character/appearance approval and never sets `production_enabled=true`.

This updates SQLite and derived tracking plus roadmap. A family's checkbox becomes `[x]` only when all its V00 rows have accepted revisions. The global V00 milestone remains active until 276/276 have accepted source-matching revisions.

## Stage R08 — Snapshot and cold-start handoff

After important progress, run:

```powershell
python scripts/update_roadmap.py --check
python scripts/package-library-for-remote.py --dry-run
python scripts/package-library-for-remote.py
```

This emits `spose-remote-handoff-YYYYMMDDTHHMMSSZ.zip` beside the full `remote/` directory. The ZIP contains only `remote/` root and a compact context snapshot, not a runnable library. Upload it in the next assistant session. If the feedback from the latest pose is visually important, also upload that pose's feedback ZIP; the small handoff intentionally excludes renders.

## Stage R09 — Gate for variations, future only

**Not active yet.** Even a fully accepted family remains V00-only while any other V00 is outstanding. When all 276 V00 are accepted, pause, audit the V00 families and ask the user to explicitly authorize enabling V01–V10. Version the workflow/schema as needed; ensure every variation inherits the correct V01–V05 mechanism and source row. The present importer explicitly rejects V01–V10.

## Exceptions and recovery

- Source/template mismatch → stop, regenerate handoff, never edit hashes to bypass the check.
- Missing control bone → inspect RIG001 map and actual Blender rig; do not invent bone names.
- Good technical result but poor image/contact → draft/review, not accepted; send feedback.
- Pose imported twice → new revision, not overwrite.
- Failed Blender run → retain logs/staging, inspect and repackage with a new timestamp.
- Roadmap stale → `python scripts/update_roadmap.py`, then verify with `--check`.
- Full Blender assets unavailable in a new session → work only on context and data-only poses; state unverified limits.

For exact file layouts and checklists, see the `docs/` folder. All states and commands in this file are designed for a cold start without prior chat context.
