---
name: uda-gym-materializer
description: Materialize UDA-Gym generated query packages into native UDA-Gym task bundles with Codex custom agents, setup/reward generation, and sanity rollout.
---

Use this skill when converting UDA-Gym `gen/<id>` query packages into native
UDA-Gym task bundles.

Read these files before acting:

1. `.codex/agents/prompts/orchestrator.md`
2. `.codex/skills/uda_cross_interface/SKILL.md`
3. `.codex/skills/mock_websites/SKILL.md` and `REWARD_SKILL.md` when mock
   websites are involved
4. `.codex/skills/local_custom_ui/SKILL.md` when `surface.yaml` declares
   `local_custom_ui`, `browser_app`, `dashboard_app`, or `mock_saas` without a
   CUA mock, when `check.yaml` uses `local_custom_ui://`, or when the source
   package contains `hidden/custom_ui/`

For interactive/manual runs, the custom agents are:

- `uda-orchestrator` for loop management and `SANITY.md`
- `uda-setup-gen` for `instruction.md`, `meta.json`, `exec/`, `hidden/`, and
  `setup.sh`
- `uda-reward-gen` for `check.sh`, `gt/`, and `REVIEW.md`

For noninteractive Codex materialization, prefer a serial role-runner in the
main Codex process instead of `spawn_agent`/`wait`: read the setup-gen,
reward-gen, and orchestrator prompts as role checklists, then produce the same
files in that order. This avoids partial bundles caused by subagent wait
liveness failures. Keep role boundaries explicit in the written REVIEW/SANITY
notes.

Template-derived packages may include optional declarative artifacts such as
`runtime.yaml`, `template_contract.yaml`, `verification_contract.yaml`,
`asset_lock.json`, `synthesis_report.yaml`, source `hidden/`, and source `gt/`.
Preserve these as inputs to the setup/reward agents instead of turning them into
pipeline-specific branches.

Runtime metadata is a task requirement, not a deployment plan. If present, copy
only `type` and `profile` into `bundle/meta.json.runtime`; do not copy
descriptive `required_software` strings from query packages into final task
metadata because NanoRollout treats them as hard profile-validator labels. Do
not write AMI IDs, launch templates, subnet IDs, or security groups into the
task bundle. `type` is the execution provider, not
the benchmark name. For EC2 profile AMI rollout, write `type: ec2`, not
`type: uda-gym`. The UDA-Gym runner resolves the profile through
`$NANOROLLOUT_ROOT/nanorollout/envs/uda_env/ec2_runtime/env_profiles.yaml`.

For `source: primitives` packages, reject materialization if `spec.yaml`
contains only `uda-cli-*` or only `uda-gui-*` primitives. Native UDA-from-
primitives tasks must require both axes; pure CLI/pure GUI baseline tasks belong
outside this pipeline.

When a template or verification contract is present, treat it as the seed for
`check.sh`: preserve the verifier family, expected outputs, hidden references,
and metrics unless the source package is internally inconsistent. Keep hidden
contracts and answer keys out of `bundle/exec/` and the agent-facing
`instruction.md`.

Keep final bundles lean. `bundle/hidden/` is for setup-only files that
`setup.sh` actually reads before the agent starts. Reward-only references,
golden outputs, material contracts, expected metrics, and verifier fixtures
belong in `bundle/gt/` if `check.sh` reads them. Source provenance that is not
used by setup or reward should remain in source manifests, not in final
`bundle/hidden/`.

For bespoke browser UI, never materialize source-visible local HTML as the task
surface. Use the local custom UI protocol: source package `hidden/custom_ui/`
becomes `bundle/hidden/custom_ui/`, `setup.sh` copies it into a per-run
`/opt/uda_apps/...` service directory, opens Chrome, and writes harness-only
metadata under `$UDA_GYM_HARNESS_STATE_DIR`. The agent-visible `exec/` tree must
not contain the UI source, source maps, seeds, verifier endpoints, or answer
keys for UDA-critical browser surfaces.

The only accepted output is a native UDA-Gym bundle:

```text
bundle/meta.json
bundle/instruction.md
bundle/exec/
bundle/hidden/
bundle/setup.sh
bundle/gt/
bundle/check.sh
REVIEW.md
SANITY.md
```

Do not generate legacy CUA-Gym `config.json`, `initial_setup.py`,
`golden_patch.py`, or `reward.py`.

Runtime sanity must use NanoRollout. The orchestrator must run the accepted
bundle through `$NANOROLLOUT_ROOT` with
`BENCH=uda-gym`, `UDA_TASKS_DIR` pointing at a staged `rollout/nro_tasks/`
tree, and `examples/eval/uda/run_codex_oauth.sh`. Export
`PATH=$NANOROLLOUT_ROOT/.venv/bin:$PATH` before
invoking the wrapper so its `nro` command resolves. Do not replace NanoRollout
with custom boto3, SSH, direct sandbox `/v1/*`, or local checker drivers; if
NanoRollout is unavailable, write `SANITY.md` with `## Verdict: FAIL`.
Every accepted rollout must preserve a setup-complete, pre-agent screenshot at
`rollout/screenshots/pre_rollout.png`; this screenshot should be captured after
`setup.sh`/warmup opens the required GUI surfaces and before the strong model
begins acting. Missing pre-rollout screenshot evidence is a runtime sanity
failure.

For batch or noninteractive use, prefer:

```bash
python3 .codex/scripts/codex_materialize.py --task-id <task_id> /path/to/UDA-Gym/gen
```
