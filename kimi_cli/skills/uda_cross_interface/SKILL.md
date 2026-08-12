---
name: uda_cross_interface
description: Read UDA-Gym generated query packages and materialize them as native UDA-Gym task bundles, not legacy CUA-Gym tasks.
---

# UDA Cross-Interface Query Packages

Use this skill when `task_config.json` has:

```json
{
  "domain": "uda_cross_interface",
  "source": "uda_gym"
}
```

The task came from UDA-Gym's query generator. CUA-Gym must read the generated
query package directly and materialize a native UDA-Gym task bundle. Do not
translate it into the old CUA-Gym `config.json` + `initial_setup.py` +
`golden_patch.py` + `reward.py` format.

## Source Package Contract

`scripts/batch_orchestrator.py` passes direct paths in
`task_config.context.uda_package`:

- `package_dir` — absolute path to the source UDA `gen/<id>/` directory.
- `query_md_path` — source instruction. This becomes `instruction.md`.
- `check_yaml_path` — verifier blueprint. This drives `check.sh`.
- `surface_yaml_path` — required interfaces and anchor surfaces.
- `spec_yaml_path` — generation metadata. Useful for setup context, not agent
  instruction.
- `context_dir` — optional source assets/fixtures.
- `context_manifest` — relative paths and sizes for orientation.
- `index_row` — original JSONL row when present.

Treat the source package as read-only. Never edit, normalize, or write generated
files back into UDA-Gym `gen/`.

If the source package is primitive-derived, `spec.yaml.primitives` must contain
at least one `uda-gui-*` and at least one `uda-cli-*`. Do not materialize pure
CLI or pure GUI primitive packages; send them back to the UDA generator as
invalid.

## Final Bundle Contract

The output bundle must be a directory with this shape:

```text
<task_id>/
  meta.json
  instruction.md
  exec/
  hidden/
  setup.sh
  gt/
  check.sh
  task.yaml        # optional
  spec.yaml        # optional
  surface.yaml     # recommended
  check.yaml       # recommended
  harness_env.tsv  # optional, harness-only env requests
```

Runtime staging:

- `exec/*` is copied into `/tmp_workspace/` before setup and is visible to the
  agent.
- `hidden/*` is copied into `/tmp_workspace/.uda_hidden/` before `setup.sh` and
  removed before the agent starts.
- `setup.sh` runs before the agent. It is hidden from the agent.
- `gt/*` is copied into `/tmp_workspace/gt/` only after the agent finishes.
- `check.sh` runs after the agent and prints the final JSON score.

Required `check.sh` final stdout line:

```json
{"overall_score": 0.0, "subscores": {}, "errors": []}
```

`overall_score` must be numeric in `[0, 1]`.

## Generator Responsibilities

Setup-gen is the generator for bundle materialization. It writes:

- `instruction.md`
- `meta.json`
- `exec/`
- `hidden/`
- `setup.sh`
- optional `task.yaml`, `spec.yaml`, `surface.yaml`, `check.yaml`,
  `harness_env.tsv`

Setup-gen must not write `check.sh` except for a temporary placeholder that the
discriminator will replace. Prefer leaving it for reward-gen.

### Instruction

Copy `query.md` into `instruction.md` with minimal path adaptation only.

Do not add:

- hidden paths;
- setup/check details;
- sid values;
- admin tokens;
- `/post`, `/go`, verifier endpoints;
- answer keys;
- instructions to read `mock.json`, `cua_mock_session.json`, or seeded-state
  files.

### Visible Assets

Copy user-visible assets into `exec/` so they stage to the paths named in the
instruction.

Examples:

- source context expected at `/tmp_workspace/context/...` goes under
  `exec/context/...`;
- starter repos go under `exec/context/<repo>/...`;
- visible CSV/PDF/image/media files go under `exec/context/...`.

Do not put complete mock state, expected answers, sid files, verifier fixtures,
or admin responses in `exec/`. For UDA-critical custom browser UI, also do not
put app source, `index.html`, JavaScript/TypeScript/JSX/TSX, source maps, seed
state, server files, or verifier endpoints in `exec/context/`; use
`hidden/custom_ui/` and `kimi_cli/skills/local_custom_ui/SKILL.md`.

### Hidden Assets

Copy setup-only assets into `hidden/`.

Examples:

- CUA mock website seed state: `hidden/cua_mock/<mock>_initial_state.json`;
- mock website name tables: `hidden/cua_mock/mock_site_name_table.json`;
- private service bootstrap manifests;
- files needed only by `setup.sh`.

Hidden contents must never be copied into `/tmp_workspace/context`.

For local custom UI, hidden contents should include only setup-needed files
under `hidden/custom_ui/`. Setup must copy them into an isolated per-run service
directory and open Chrome; reward must read server-side state via harness
metadata.

### setup.sh

`setup.sh` must:

1. start with `#!/usr/bin/env bash` and `set -euo pipefail`;
2. create `/tmp_workspace/results`;
3. verify required visible files are staged;
4. start required local services or dev servers;
5. open every required GUI/browser/desktop software surface before the agent
   starts;
6. keep secrets and hidden assets out of agent-visible paths;
7. exit nonzero if setup fails.

When `spec.yaml.primitives` includes `uda-gui-*`, setup must make that GUI
primitive real. Open the matching `surface.yaml` entrypoint in the appropriate
viewer/app before the agent starts and verify a live process/window. Examples:
PDF/report/chart-readout surfaces open in Chrome/Evince/LibreOffice; mock or
custom browser surfaces open in Chrome; image/video/audio/app surfaces open in
their appropriate GUI tools. Merely staging files, checking paths, headlessly
extracting text, or relying on the instruction to tell the agent to open the
surface is a failure. The pre-rollout screenshot is required evidence that the
initialized GUI state exists.

On UDA EC2 Linux desktop profiles, launch GUI apps with the real display
environment: `DISPLAY="${DISPLAY:-:0}"` and, when available,
`XAUTHORITY=/run/user/1000/gdm/Xauthority`. When setup runs as root, prefer
launching GUI apps through the desktop user with
`sudo -u user env DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus <app> ...`. Chrome or
Chromium launched as root must include `--no-sandbox`. Process existence alone
is insufficient; reject blank/black pre-rollout screenshots and require visual
evidence of the intended surface. For PDF/report/document surfaces, use Evince
or LibreOffice when practical and verify a visible target-titled window; a
generic Chrome window, app icon, or non-black desktop is not sufficient.

For CUA-Gym Hub mock websites, load `kimi_cli/skills/mock_websites/SKILL.md` and
follow its hardened-public-hybrid flow:

- read `CUA_GYM_ADMIN_TOKEN` from harness-only environment;
- seed server-side state with admin-token `POST /post?sid=<sid>`;
- store the real sid only in a harness-only runtime file such as
  `/tmp/.uda_gym_runtime/<task_id>/<mock>_sid`;
- open Chrome normally to `BASE_URL + launch_url`;
- do not use private IPs, `/etc/hosts`, `curl --resolve`, temporary redirect
  HTML, or `about:blank` + `xdotool`;
- do not expose the full mock state, sid, token, or verifier URL in
  `/tmp_workspace/context` or the instruction.

If `setup.sh` needs harness-only secrets, add `harness_env.tsv` with one env var
name per line, for example:

```text
CUA_GYM_ADMIN_TOKEN
```

Never place secret values in the bundle.

For local custom UI, load `kimi_cli/skills/local_custom_ui/SKILL.md` and follow
its hidden-service protocol. Source-visible local HTML under
`/tmp_workspace/context` is not an acceptable realization of a UDA-critical
browser/dashboard surface.

## Discriminator Responsibilities

Reward-gen is the discriminator/check generator. It writes:

- `check.sh`
- `gt/`
- `REVIEW.md`

It may read original `query.md`, `surface.yaml`, `check.yaml`, and `spec.yaml`
because these are task inputs. It may inspect `instruction.md`, `exec/`, and
public manifests for bundle validation. It must not derive scoring from
`hidden/` seed fixtures.

### check.sh

`check.sh` must:

1. start with `#!/usr/bin/env bash` and `set -euo pipefail`;
2. read agent outputs from `/tmp_workspace/results`;
3. read hidden scoring references from `/tmp_workspace/gt`;
4. inspect live services or CUA-Gym Hub mock state when required;
5. compute deterministic subscores from `check.yaml`;
6. print one JSON object as the final stdout line;
7. exit zero when grading completed, even for low scores;
8. exit nonzero only when the evaluator itself failed.

For CUA-Gym Hub mock websites, load
`kimi_cli/skills/mock_websites/REWARD_SKILL.md` and use admin-token
`/go?sid=<sid>` as the verifier source of truth. Do not read Chrome history,
cookies, IndexedDB, localStorage, browser SQLite DBs, seeded fixture JSON, or
`context/cua_mock_session.json` as reward truth.

For local custom UI, load `kimi_cli/skills/local_custom_ui/SKILL.md` and use
server-side state referenced by `$UDA_GYM_HARNESS_STATE_DIR/custom_ui.json` as
the verifier source of truth. Do not read browser storage, Chrome DBs, visible
client source, or `/tmp_workspace/context` clones of app state as reward truth.

### gt/

Use `gt/` for answer keys, private reference data, schemas, thresholds, and
expected outputs needed only at scoring time. Do not put `gt/` data in `exec/`
or `instruction.md`.

## REVIEW.md Verdict

The discriminator's `REVIEW.md` must include:

```md
## Verdict: PASS
```

or

```md
## Verdict: FAIL
```

A PASS requires all of:

- required bundle files exist;
- `exec/`, `hidden/`, and `gt/` directories exist;
- `bash -n setup.sh` and `bash -n check.sh` pass;
- `instruction.md` is agent-facing and contains no hidden/verifier details;
- complete mock state and answers are not leaked into `exec/`;
- mock website setup/check follows hardened-public-hybrid rules;
- `check.sh` implements all material `check.yaml` criteria with structured
  deterministic scoring;
- final JSON score shape is valid.

## Common Failure Modes

- Treating UDA input as old CUA task-gen JSON.
- Producing `initial_setup.py`, `golden_patch.py`, or `reward.py` instead of a
  UDA-Gym bundle.
- Copying all `context/` files into `exec/` without separating hidden mock seed
  state.
- Asking the agent to open local mock session JSON instead of opening the
  seeded website.
- Leaving CUA mock seed state in `/tmp_workspace/context`.
- Verifying CUA mock state from browser DB/localStorage instead of server-side
  admin-token `/go`.
- Implementing bespoke browser UI as editable `context/**/index.html`, visible
  app JS, or source maps.
- Verifying custom UI tasks from browser storage or visible source instead of
  server-side state.
- Claiming GUI primitives while setup only copies/validates files and never
  opens the required GUI/browser/desktop surface.
- Scoring free-form markdown summaries as the primary deliverable.
- Rewarding setup success rather than final agent outputs/state.
