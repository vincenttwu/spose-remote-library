# SPOSE state model: metadata, not gates

| Field | Meaning | Stops import or next batch? |
|---|---|---|
| source `generation_gate` | Editorial review flag on catalog row | **No** |
| geometry `hard_gate_pass` | Legacy name for whether optional checks reported issues | **No** |
| `stability=needs_work` | Quality annotation | **No** |
| `status=draft` | Blender generated a usable revision | **No** |
| `status=failed` | Technical execution did not finish; logs retained | **No** (next pose proceeds) |
| `status=accepted` | User optionally approved a revision | **No** |
| `ROADMAP` checkbox | At least one matching-source built revision exists | **No** |
| variation phase | Scheduling preference for later | **No** |

The runner does not use geometry or approval results as decisions. If import code sees a bad ZIP, missing asset or mismatched source fingerprint, the item may fail as an **integrity** error. It still logs the issue and continues to the remaining items. Those checks protect data, not pose quality.

`ROADMAP.json` includes both `v00_built` and `v00_accepted`. A family can be fully built with zero accepted, and that is still progress. Old `blocked` revisions with actual renders count as built in the new roadmap; their historical labels are not rewritten.
