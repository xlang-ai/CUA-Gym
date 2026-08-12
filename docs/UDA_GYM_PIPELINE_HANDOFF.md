# UDA-Gym Materialization Pipeline Handoff

Last updated: 2026-08-12

This branch turns CUA-Gym into the materialization layer between generated
UDA-Gym query packages and executable native UDA-Gym task bundles. The active
path is one generic `scripts/materialize.py` entrypoint, the first-class
`kimi_cli/` integration, and AWS EC2 runtime evidence.

## Branch and Dependencies

- CUA-Gym branch: `uda`
- Hub submodule: pinned to the UDA hardened/hybrid API commit
- Kimi Code CLI: `kimi --version` and local authentication are required.
- AWS: the worker endpoint is supplied at runtime; credentials never enter
  task manifests or checked-in artifacts.

Legacy Claude/Codex role prompts remain for historical pipelines. The active
Kimi copies are maintained under:

```text
.claude/agents/{task-gen,setup-gen,reward-gen,orchestrator}.md
.codex/agents/prompts/{task-gen,setup-gen,reward-gen,orchestrator}.md
kimi_cli/agents/{task-gen,setup-gen,reward-gen,orchestrator}.md
kimi_cli/skills/{uda-gym-materializer,uda_cross_interface,mock_websites,local_custom_ui}/
```

The Kimi asset topology is checked by `python3 kimi_cli/verify_mirror.py`.
Kimi-specific runtime changes belong only under `kimi_cli/`; do not add them to
the historical `.codex/` runner.

## Inputs

The loader accepts:

- a UDA-Gym `gen/` tree;
- `gen/queries.jsonl`;
- one query package directory.

A valid package includes:

```text
query.md
spec.yaml
check.yaml
surface.yaml
context/
hidden/          optional generator-side harness assets
runtime.yaml     optional profile declaration
```

Primitive inputs are rejected when `spec.yaml` does not contain at least one
`uda-gui-*` and one `uda-cli-*` primitive.

## Workspace Contract

Every task gets one task-local workspace:

```text
output/workspaces/<task_id>/           legacy Claude pipeline
output/materialization/<task_id>/      active Kimi pipeline
```

Inside either workspace:

```text
source/uda_package/  immutable source copy
task_config.json
bundle/              setup-gen candidate
reward_sandbox/      reward-gen isolated review copy
rollout/             authoritative AWS teacher evidence
REVIEW.md
SANITY.md
materialization_result.json
```

Agents must treat the workspace cwd as their only mutable area. Source package
files are copied in; no agent needs write access to the parent repository.

## Role Boundaries

`setup-gen` owns:

- `instruction.md`, `meta.json`;
- `exec/`, `hidden/`, `setup.sh`;
- optional runtime/surface/spec manifests;
- GUI launch and pre-agent initial state.

`reward-gen` owns:

- `gt/`, `check.sh`;
- structured criteria and partial credit;
- adversarial review in `REVIEW.md`;
- reward-hacking and equivalence-class checks.

In the Claude pipeline, `orchestrator` owns:

- loop state and role invocation;
- agreement/revision routing;
- final instruction/setup/reward consistency scan;
- real NanoRollout sanity rollout;
- trajectory-versus-reward review;
- `SANITY.md`, classification, and publication.

The Claude orchestrator must not author or repair bundle files directly.

The active Kimi runner uses one bounded Kimi Code process per query. It applies
the copied setup/reward/orchestrator checklists through one generic skill and
does not create task-specific materializer scripts.

## Publication Gates

Publication requires:

- complete bundle contract;
- `REVIEW.md` with `## Verdict: PASS`;
- `SANITY.md` with `## Verdict: PASS`;
- static consistency and secret-boundary checks;
- nonempty `rollout/screenshots/pre_rollout.png`;
- AWS teacher output tree;
- trajectory and reward artifacts;
- a coherent classification.

Strong-model score may be partial or zero. Acceptance depends on whether the
trajectory and reward accurately reflect the task, not whether Kimi reaches
full reward.

Canonical classifications:

- `task_valid`
- `agent_low_score`
- `infra_fail`
- `setup_fail`
- `reward_fail`
- `artifact_gate_fail`
- `rollout_artifact_fail`
- `final_gate_fail`

Never count `infra_fail` as evidence that a task is hard or invalid.

## Mock Website Rules

Use the copied hybrid hardened flow in `kimi_cli/skills/mock_websites/`:

- random real sid per rollout;
- admin-authenticated hidden setup;
- one-time launch URL opened in Chrome;
- real sid and token never agent-visible;
- server-side authoritative state;
- admin `/go` reward readback;
- no Chrome DB/localStorage/browser history as verifier truth.

Every mock surface named by the task must actually be opened by `setup.sh`.
The pre-rollout screenshot must show the intended initialized product surface,
not just a Chrome process or generic desktop.

## Commands

Kimi/AWS:

```bash
python3 scripts/materialize.py \
  /path/to/UDA-Gym/gen \
  --task-id <task_id> \
  --model local/k3
```

Claude:

```bash
python3 scripts/batch_orchestrator.py \
  "$UDA_GYM_ROOT/gen" \
  --task-id <task_id>
```

Dry-run and static checks:

```bash
python3 -m py_compile \
  scripts/batch_orchestrator.py \
  scripts/uda_materialization_audit.py \
  scripts/materialize.py \
  uda_materializer/pipeline.py \
  kimi_cli/runner.py
python3 scripts/materialize.py --dry-run <input>
```

## Operational Warnings

- `output/` is generated state and is intentionally not committed.
- Do not restore old `config.json`/`initial_setup.py`/`golden_patch.py`/
  `reward.py` protocol.
- Do not replace the AWS worker/controller with ad hoc local checker scripts.
- Keep the Hub submodule pointer stable until the corresponding deployment is
  available.
- Never commit `CUA_GYM_ADMIN_TOKEN`; only commit its variable name and expected
  harness source.
- Keep stalled-output timeouts and process-group termination enabled for batch
  scale.
