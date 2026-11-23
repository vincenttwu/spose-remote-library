# workspace/AGENTS.md — Experimental Backward-Roadmap Sandbox Rules

> **EXPERIMENTAL SUBPATH ONLY.** Everything under `workspace/` is an isolated local authoring, rendering, and pre-audit sandbox. It is **not** part of the authoritative SPOSE library. Root `../AGENTS.md` remains supreme for the main library.

## 1. Purpose

`workspace/` allows local agents to author, build in Blender, calibrate, and prepare **audit-ready** data-only pose batches independently when the remote assistant is unavailable, working **backwards from the bottom of the V00 roadmap** (`UFDG` → `UADG` → `USDG` → `OFEL` → `OCUN` → …) so pose IDs do not collide with the main forward production line (`DOGG` → `GARD` → `MISS` → …).

Work produced here stays cleanly quarantined until explicitly audited and promoted by the user.

---

## 2. Non-Negotiable Non-Pollution Constraints

When operating inside `workspace/`, an agent **MUST NEVER** create, modify, overwrite, or delete any file outside `workspace/` unless the user explicitly initiates a separate **Promotion** step.

### Strictly forbidden writes (top-level library)
- **Tracking & roadmaps:** `../tracking/progress.sqlite`, `../tracking/registry.json`, `../tracking/progress.csv`, `../tracking/events.jsonl`, `../ROADMAP.md`, `../ROADMAP.json`, `../CONTINUATION.md`
- **Authoritative assets & revisions:** `../poses/`, `../snapshots/`, `../batches/`, `../incoming/`, `../pairs/`, `../body_profiles/`, `../visual_profiles/`, `../source/`
- **Shared exchange & scratch:** `../review/`, `../upload/`, `../local/`, `../reports/`
- **Core tooling & docs:** `../scripts/`, `../docs/`, `../schemas/`, `../tooling/`, `../project.json`, `../AGENTS.md`

### Permitted read-only top-level dependencies
- Read `../source/SPOSE-FULL-20261122T013728Z.csv` and `../source/dataset.json` (never modify).
- Read `../pairs/CPL01/v001/template.blend`, `../pairs/CPL01/v001/studies/VP001-v001/appearance-study.blend`, and `../tooling/rig-maps/RIG001-v001.json` (never modify or save over them).
- Import/invoke `../scripts/pose_common.py`, `../scripts/blender_build.py`, `../scripts/rigify_floor_engine.py`, and `../scripts/compress_images.py` strictly with output targets constrained inside `workspace/`.
- **No symlinks or directory junctions** anywhere under `workspace/`.
- **No direct edits to `../scripts/`.** If a new posture family requires solver/engine changes beyond `rigify_floor_v2`, prototype them inside `workspace/scripts/` (or a separate Git worktree/branch) and document the delta for formal infrastructure review; never silently patch root `../scripts/`.

---

## 3. Folder Structure & Workspace-Only Tracking

All tracking for experimental batches lives exclusively inside `workspace/`:

```text
workspace/
  AGENTS.md                     # This contract
  WORKSPACE-ROADMAP.md          # Backward V00 progress checklist (independent of ../ROADMAP.md)
  workspace-tracker.json        # Workspace-only state index (batches, passes, hashes, audit/promotion status)
  scripts/                      # Optional sandbox runner/helper scripts (outputs locked inside workspace/)
  batches/
    <FAMILY>/
      pass-01/
        packages/               # Standard spose_pose_module ZIPs ({POSE_ID}_{YYYYMMDDTHHMMSSZ}.zip)
        plan.json               # Infra-0002-compatible batch plan (data-only)
        renders/
          <POSE_ID>/            # scene.blend, previews/*.png, validation.json, calibration.json, build.log
        review/                 # Flat prefixed PNGs (<POSE_ID>_<view>.png) for quick visual inspection
        AUDIT.md                # Spec-vs-render visual critique, measurements, and pass notes
        audit-bundle.zip        # Optional single compact archive (lossless WebP + packages + AUDIT.md)
      pass-02/
        ...
```

- Every pass gets its own folder (`pass-01/`, `pass-02/`, …); never overwrite an earlier pass's `packages/`, `plan.json`, or `AUDIT.md`.
- Keep the pose list order identical across passes of the same batch/family so future Infra 0002 registration stays cleanly aligned.
- Never start a family in `workspace/` that already has active work in `../ROADMAP.md` without explicit user instruction.

---

## 4. End-to-End Experimental Workflow

### Step 1 — Author & Validate Data-Only Packages
1. Read exact specifications for the target family's V00 poses from `../source/SPOSE-FULL-20261122T013728Z.csv` (prefer 5 poses per batch, or the full family if it has 4–5 poses).
2. Author data-only `spose_pose_module` ZIPs in `workspace/batches/<FAMILY>/pass-NN/packages/` containing only allowed JSON members (`manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`, plus optional `render-config.json` / `validation-plan.json`).
3. Validate every ZIP with `../scripts/pose_common.py::load_package(..., validate_dependencies=True)` against the real pinned source catalog and pair template SHA-256 hashes.
4. Write a matching data-only `plan.json` for the pass.

### Step 2 — Isolated Blender Build & Measurement
1. Run Blender (`5.2.2 LTS`) using the read-only appearance study template and write all outputs (`scene.blend`, 4 views: `front`, `side`, `three-quarter`, `qa-regions`, `validation.json`, `blender-result.json`, `build.log`) strictly inside `workspace/batches/<FAMILY>/pass-NN/renders/<POSE_ID>/`.
2. Copy flat prefixed PNGs (`<POSE_ID>_<view>.png`) into `workspace/batches/<FAMILY>/pass-NN/review/` for fast inspection.
3. Run neutral/scene measurement probes when applicable, saving JSON results under `renders/<POSE_ID>/`.
4. Update `workspace/workspace-tracker.json` and regenerate `workspace/WORKSPACE-ROADMAP.md`.

### Step 3 — Anti-Bias Audit & Calibration
- **No fabricated scores, no blocking quality gates.** Record failures, warnings, and unstable drafts honestly.
- **Avoid grading your own homework:** inspect all 4 views per pose against the CSV specification, and before authoring Pass 02 either:
  - ask the user for a quick visual check of `workspace/batches/<FAMILY>/pass-NN/review/`, and/or
  - invoke a fresh-context reviewer subagent (given only the CSV spec + rendered images + metrics, without authoring rationale) to write an unbiased critique.
- Document per-pose visual judgments, contact/floor diagnostics, and proposed Pass 02 adjustments in `AUDIT.md`.
- Optionally export a single compact `audit-bundle.zip` (lossless WebP images + `packages/*.zip` + `AUDIT.md` + metrics) so a remote assistant can audit asynchronously without touching root `../upload/`.

---

## 5. Promotion to the Authoritative Library (Explicit User Action Only)

Nothing in `workspace/` is ever automatically promoted into the official library.

When the user explicitly approves a workspace pass for official entry:
1. Verify `../scripts/check_remote.py` passes before starting.
2. Copy the approved data-only `packages/*.zip` into `../incoming/`.
3. Write a uniquely named Infra 0002 plan (e.g., `../batches/BATCH-XXXX-PASS-01.json`) with an official batch ID chosen by the user.
4. Run the official pipeline (`../scripts/run_registered_batch.py`) so authoritative `../poses/`, `../snapshots/`, and `../tracking/progress.sqlite` records are created through the normal verified path.
5. Update `workspace/workspace-tracker.json` to mark `"promoted": true` with the official `batch_id`, `pass_id`, and `snapshot` path, and refresh `workspace/WORKSPACE-ROADMAP.md`.

---

## 6. Workspace CLI Commands

Run from the repository root:

```powershell
python workspace/scripts/ws_tracker.py init
python workspace/scripts/ws_tracker.py status
python workspace/scripts/ws_tracker.py sync
python workspace/scripts/ws_run_pass.py --pass-dir workspace/batches/<FAMILY>/pass-01 --dry-run
python workspace/scripts/ws_run_pass.py --pass-dir workspace/batches/<FAMILY>/pass-01 --blender "<BLENDER_EXE>"
python workspace/scripts/ws_run_pass.py --pass-dir workspace/batches/<FAMILY>/pass-01 --export-audit-zip
python workspace/scripts/ws_tracker.py mark-audit --family <FAMILY> --pass pass-01 --score 7.0 --notes "..."
```

All workspace scripts enforce `ws_common.ensure_in_workspace()` and refuse any write path outside `workspace/`.

---

## 7. Verification & Git Hygiene

- After any `workspace/` run, confirm zero top-level pollution by checking `git status` (no modified files outside `workspace/`).
- Report offline Python/ZIP validation separately from actual Blender renders; if Blender did not run, state so explicitly.
- **Data-only Git policy (if `workspace/` is tracked in Git):**
  - Track: `workspace/AGENTS.md`, `workspace/WORKSPACE-ROADMAP.md`, `workspace/workspace-tracker.json`, `workspace/scripts/`, `workspace/batches/**/packages/*.zip`, `plan.json`, `AUDIT.md`, and render JSON/log files.
  - Ignore: `workspace/**/*.blend`, `workspace/**/*.png`, `workspace/**/*.webp`, `workspace/**/audit-bundle.zip`, and `workspace/**/review/`.
