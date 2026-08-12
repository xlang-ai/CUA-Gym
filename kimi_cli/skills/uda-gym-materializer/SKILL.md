# UDA-Gym materializer for Kimi Code CLI

This is the single, generic materialization workflow. The query package owns
task-specific behavior; the materializer must never branch on a game, website,
dataset, or task id.

## Source contract

Read the complete `source/uda_package/` before editing the bundle:

- `query.md`, `spec.yaml`, `surface.yaml`, `check.yaml`;
- optional `runtime.yaml`, `template_contract.yaml`,
  `verification_contract.yaml`, `asset_lock.json`, `calibration.yaml`;
- every file under `context/`, `hidden/`, and `gt/` when present.

Keep `source/uda_package/` immutable. Copy only the intended visible assets to
`bundle/exec/`; keep authoritative contracts and verifiers under `bundle/hidden/`
and `bundle/gt/`. Never leak hidden solution data through `instruction.md`,
visible assets, logs, or runtime metadata.

## Native bundle contract

Produce exactly one native bundle with:

```text
bundle/meta.json
bundle/instruction.md
bundle/setup.sh
bundle/check.sh
bundle/exec/
bundle/hidden/
bundle/gt/
```

`meta.json` must declare `task_family: uda`, the source query identity, the
normalized runtime type `ec2`, and only portable requirements/profile data.
Never write AMI IDs, subnet IDs, security groups, instance IDs, or AWS secrets
into the bundle.

`setup.sh` must create a fresh episode, initialize the visible surface, start
the authoritative harness, and leave a usable desktop state. `check.sh` must
consume only harness-owned/evaluator-owned state and emit one final JSON object
with numeric `score` or `reward` in `[0, 1]`. A failed task may score zero, but
checker infrastructure failure must be explicit and distinguishable.

## Review and runtime gate

`REVIEW.md` is the static/adversarial review. It must cover every criterion in
`check.yaml`, reward strictness, solution multiplicity, hidden-data boundary,
and reward-hacking attempts.

`SANITY.md` may say `## Verdict: PASS` only after a real AWS worker run. The
Kimi hybrid teacher controller must perform setup/reset, capture the initial
screenshot, execute the teacher trajectory, call evaluate, and preserve:

```text
rollout/teacher_trajectory.jsonl
rollout/teacher_score.json
rollout/teacher_alignment.json
rollout/teacher_feedback.md
rollout/setup.log
rollout/run_metadata.json
rollout/aws_output/
rollout/screenshots/pre_rollout.png
```

The alignment report must compare the final trajectory state with the checker
score and contain `"verdict": "PASS"`. If score and trajectory disagree,
write feedback, revise the bundle through the same generic workflow, and rerun
the AWS teacher. Never convert a local/static checker result into rollout
evidence.

## Related copied skills

Use the copied skills under `kimi_cli/skills/` when the source surface needs
them. In particular, load `uda_cross_interface`, `mock_websites` (including
`REWARD_SKILL.md` and the relevant schema), and `local_custom_ui`; domain skills
are available one-for-one for document, graphics, browser, and application
surfaces. Do not reference `.codex/` or `.claude/` from the active Kimi path.
