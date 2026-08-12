---
description: "Deprecated. CUA-Gym no longer generates old task-generation JSON; use UDA-Gym query generation and batch_orchestrator materialization instead."
tools: Read
---

# Task-Gen Deprecated

The old CUA-Gym task-generation protocol is removed from this workspace.

Do not generate `output/task_generation/*.json`.
Do not create native CUA task-gen JSON.
Do not produce tasks targeting the legacy `config.json` + `initial_setup.py` +
`golden_patch.py` + `reward.py` pipeline.

Use UDA-Gym's query generators to create packages containing:

```text
query.md
check.yaml
surface.yaml
spec.yaml
context/   # optional
```

Then materialize them from CUA-Gym with:

```bash
python scripts/batch_orchestrator.py /path/to/UDA-Gym/gen
```

The batch orchestrator will output native UDA-Gym bundles under:

```text
output/final/<task_id>/
```
