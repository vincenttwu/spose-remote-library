# Pose data JSON contract (geometry V2, non-gating)

Required in a flat pose ZIP: `manifest.json`, `pose.json`, `rig-targets.json`, `contacts.json`. Optional `render-config.json`, `validation-plan.json`. `rig-targets.json` has `schema_version: 1`, `engine: rigify_floor_v2`, `geometry_contract_version: 2`, numeric `controls`, `floor_calibration`, `support_assertions` and `posture_assertions`. Sources, rig, template and payload files are hash-pinned. Source `generation_gate` is advisory only.

These fields request rig behavior and measurements; none promise correct support or physical contact. Builder runs and exports a draft regardless of geometry warnings. A batch runner always attempts all five, logs exceptions and writes a combined feedback ZIP.
