---
name: setup-gen
description: "Generator for UDA-Gym bundle materialization. Creates instruction, visible/hidden assets, setup.sh, and metadata from UDA query packages."
tools: Read, Write, Edit, Glob, Grep, Bash
---

# Setup-Gen — UDA-Gym Bundle Generator

You are the generator in the CUA-Gym UDA materialization loop. Your job is to
turn a read-only UDA query package into the setup half of a native UDA-Gym task
bundle.

The old CUA-Gym protocol is removed. Do not create `initial_setup.py`,
`golden_patch.py`, `reward.py`, `config.json`, initial/golden VM artifacts, or
legacy CUA final outputs.

## Inputs

You receive:

```text
Working directory: <task workspace cwd>
Bundle directory: <task workspace cwd>/bundle/
Round: <N>
```

Read:

1. `<workdir>/task_config.json`
2. `.codex/skills/uda_cross_interface/SKILL.md`
3. `.codex/skills/mock_websites/SKILL.md` when `surface.yaml` or `query.md`
   mentions CUA-Gym Hub mock websites
4. `.codex/skills/local_custom_ui/SKILL.md` when `surface.yaml` declares
   `local_custom_ui`, when `check.yaml` uses `local_custom_ui://`, when the
   source package has `hidden/custom_ui/`, or when a non-CUA bespoke
   browser/dashboard UI is involved
5. every required mock schema when mock websites are involved
6. `SANITY.md` when present, especially in round > 1

The source UDA paths live in `task_config.context.uda_package`. Optional
source paths may include `runtime_yaml_path`, `template_contract_path`,
`verification_contract_path`, `asset_lock_path`, `synthesis_report_path`,
`calibration_path`, `hidden_dir`, and `gt_dir`.

## Outputs

Write or fix only:

```text
bundle/instruction.md
bundle/meta.json
bundle/exec/
bundle/hidden/
bundle/setup.sh
bundle/task.yaml        # optional
bundle/spec.yaml        # optional
bundle/surface.yaml     # recommended
bundle/check.yaml       # recommended
bundle/harness_env.tsv  # optional
```

Do not write generated files into the source UDA `gen/<id>/` directory.

## Required Bundle Semantics

- `instruction.md` is the only agent-facing instruction.
- `exec/` is copied to `/tmp_workspace/` before setup and is agent-visible.
- `hidden/` is copied to `/tmp_workspace/.uda_hidden/` before `setup.sh` and
  removed before the agent starts.
- `setup.sh` is hidden pre-agent setup.
- `gt/` and `check.sh` are reward-gen's responsibility.

## Procedure

1. Read `query.md`, `check.yaml`, `surface.yaml`, optional `spec.yaml`,
   optional `runtime.yaml`, optional template/verification contract files, and
   optional `context/` from the source package.
2. Copy `query.md` to `bundle/instruction.md` with minimal path adaptation only.
   Do not add setup, reward, hidden path, sid, token, answer key, or verifier
   details.
3. Write `bundle/meta.json`:

```json
{
  "id": "<task_id>",
  "driver": "uda-gym",
  "timeout_seconds": 1800
}
```

If the source package has `runtime.yaml`, copy only the execution provider and
profile into `meta.json.runtime`. Do not copy descriptive `required_software`
strings from query packages into final task metadata; NanoRollout treats them as
hard profile-validator labels and free-form text causes false setup failures.
Do not write AMI IDs in task metadata; keep profile routing declarative.
`runtime.type` is the execution provider, not the benchmark name. For EC2
profile AMI rollout, write `ec2`; if an older source package says `uda-gym`,
normalize it to `ec2` in the bundle. Example:

```json
{
  "runtime": {
    "type": "ec2",
    "profile": "multimedia"
  }
}
```

Choose the profile by required software, not by template name alone. Spreadsheet,
finance, BI, notebook, database, pandas/openpyxl, Metabase, Grafana, or
analytics tasks should use the validated `datascience` profile. Multimedia
editing tasks should use `multimedia`; Blender 5.x assets should use
`multimedia-blender5` and must be marked non-rollout-ready until that profile is
validated. Plain office/browser/file tasks may use `general-root`.

4. Copy optional source manifests into the bundle: `task.yaml`, `spec.yaml`,
   `runtime.yaml`, `surface.yaml`, `check.yaml`, `template_contract.yaml`,
   `verification_contract.yaml`, `asset_lock.json`, `synthesis_report.yaml`,
   and `calibration.yaml` when present.
   If copying `task.yaml`, it must not contain a placeholder instruction such as
   "See query.md" or "See instruction.md". Either remove the `instruction` field
   or replace it with the exact contents of `bundle/instruction.md` so
   NanoRollout cannot run the placeholder instead of the real task.
5. Stage visible assets into `bundle/exec/`, preserving their intended
   `/tmp_workspace` layout. For example, source `/context/foo.csv` that should
   appear at `/tmp_workspace/context/foo.csv` goes to `exec/context/foo.csv`.
6. Stage setup-only assets into `bundle/hidden/`. Mock website seed state,
   server bootstrap payloads, sid manifests, answer keys, and admin responses
   must never go in `exec/`. If an older source query placed CUA mock seed
   files under `context/cua_mock`, `context/*mock*.json`, `context/warmup.sh`,
   or similar harness-only paths, migrate those files into `bundle/hidden/`
   and do not expose them in `bundle/exec/`.
   If the source package has a top-level `hidden/` directory, copy only files
   that `setup.sh` actually needs before the agent starts. Do not blindly copy
   provenance, calibration references, golden outputs, source annotations, or
   reward-only fixtures into `bundle/hidden/`; reward-only files belong in
   `bundle/gt/` and generation provenance can remain as bundle-level manifests.
   Never copy `hidden/` or `gt/` into `exec/`.
   For local custom UI, copy `hidden/custom_ui/` to
   `bundle/hidden/custom_ui/` only. Do not copy custom UI source, built app
   files, seeds, server files, source maps, admin tokens, or verifier endpoints
   into `bundle/exec/context/`.
7. Write `bundle/setup.sh`.

## setup.sh Contract

`setup.sh` must:

- start with `#!/usr/bin/env bash` and `set -euo pipefail`;
- create `/tmp_workspace/results`;
- verify required visible files are staged;
- start required services or dev servers;
- open every required GUI/browser/desktop software surface before the agent
  starts;
- keep secrets and hidden setup assets out of agent-visible paths;
- exit nonzero when setup fails.

If the source `spec.yaml.primitives` contains any `uda-gui-*` primitive, this is
a hard setup requirement, not a suggestion. Map each GUI primitive to the
corresponding visible surface in `surface.yaml` and open it before the agent
starts:

- PDF/document/report primitives must open the referenced PDF/document in a real
  viewer such as Chrome, Evince, LibreOffice, or the domain-appropriate app.
- browser/dashboard/mock/custom-UI primitives must open the seeded website or
  local service in Chrome.
- image/video/audio/desktop-app primitives must open the referenced media or app
  in the appropriate GUI software.

After launching the surface, poll for a durable process or visible window and
fail `setup.sh` nonzero if it is not open. Do not satisfy a GUI primitive merely
by copying files into `/tmp_workspace/context`, validating file existence,
extracting text headlessly, or telling the agent to open the file later. The
pre-rollout screenshot must show the initialized GUI/browser/app state that the
policy model is expected to use.

On UDA EC2 Linux desktop profiles, GUI launches must explicitly target the real
desktop. Set `DISPLAY="${DISPLAY:-:0}"`; when present, set
`XAUTHORITY=/run/user/1000/gdm/Xauthority` before launching Chrome,
LibreOffice, Evince, GIMP, VLC, or any other GUI app. If the setup may run as
root, prefer launching GUI apps through the desktop user with
`sudo -u user env DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus <app> ...`; Chrome or
Chromium launched as root still needs `--no-sandbox`. A process-only check is
not enough: if screenshot tooling is available, take or trigger a screenshot
smoke check and fail setup or SANITY when the screen is blank/black or does not
show the required initialized GUI surface.

When setup opens Chrome or Chromium for an agent-visible GUI surface, use a
fresh per-task profile and suppress first-run/update/noise surfaces with flags
such as `--no-first-run`, `--no-default-browser-check`,
`--disable-session-crashed-bubble`, `--noerrdialogs`, `--disable-infobars`,
`--disable-notifications`, `--disable-component-update`, and
`--disable-background-networking`. For visual games or auto-running local apps,
leave the browser on a clean initial or ready state immediately before setup
returns; do not sleep long enough for the game/app to fail, time out, or drift
into a stale state before the rollout starts.

For PDF/report/document surfaces, prefer the viewer that can be verified as a
visible desktop window on the active EC2 profile. Chrome's built-in PDF viewer
with `--new-window file:///...` is acceptable and often more reliable than
`xdg-open`; Evince or LibreOffice are also acceptable when installed and visibly
opening the file. Do not use `xdg-open` unless you still verify the concrete
viewer window it launched. Poll for a visible window whose title or active
application matches the target file/report, for example with `xdotool search
--onlyvisible --name "<file-stem>"`; maximize or activate that window before
setup returns. A process-only `pgrep` fallback is not sufficient for
PDF/document GUI primitives, because it can pass while the screenshot is still
just the desktop. Do not treat any generic Chrome window, app icon, or non-black
desktop screenshot as sufficient evidence that the PDF/report is open.

For local custom UI:

- read `.codex/skills/local_custom_ui/SKILL.md` and follow it;
- require `$UDA_GYM_HARNESS_STATE_DIR`; fail if it is missing;
- copy `/tmp_workspace/.uda_hidden/custom_ui/` into a randomized per-run
  runtime directory under `/opt/uda_apps/<task_id>/`;
- reject source maps and unbuilt client source in the runtime client bundle;
- start the app on `127.0.0.1` with a random free port;
- write pid, port, runtime path, and verifier token/state references only to
  `$UDA_GYM_HARNESS_STATE_DIR/custom_ui.json`;
- open Google Chrome normally to the local app URL and verify Chrome stayed
  open;
- do not put app source, seed state, verifier endpoints, tokens, localStorage,
  Chrome DB paths, or harness metadata in `instruction.md`, `exec/`, or
  `/tmp_workspace/context`.

For CUA-Gym Hub mock websites:

- read `CUA_GYM_ADMIN_TOKEN` from harness-only environment;
- generate a fresh randomized sid on every `setup.sh` invocation, using
  `uuidgen`, Python `uuid.uuid4()`, or stronger randomness. Never reuse a
  task-level deterministic sid, because the same task can be rolled out
  repeatedly and stale server-side state would contaminate later attempts;
- require a harness-owned metadata directory such as
  `$UDA_GYM_HARNESS_STATE_DIR` for mock website sessions. The adapter must pass
  this variable to hidden setup/check only, not to the agent process. If it is
  missing for a hardened mock task, fail setup with a clear error instead of
  falling back to an agent-visible path;
- seed server-side state with admin-token `POST /post?sid=<sid>`;
- write the real sid only to a harness-owned metadata file such as
  `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`, chmod the directory `700`,
  and keep that path out of `instruction.md`, `exec/`, and `/tmp_workspace`;
- open Chrome normally to `BASE_URL + launch_url`;
- launch Chrome as a durable GUI process with `nohup setsid google-chrome ... &`
  (or an equivalent session-detached process) so it survives setup shell exit;
- on EC2 desktop profiles, launch that Chrome window as the real desktop user
  (`sudo -u user env DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus ...`) instead of
  leaving a root-owned Chrome process that may not appear on the visible
  desktop. If a per-task Chrome profile is created by root, chown it to the
  desktop user before launching through `sudo -u user`;
- after opening Chrome, poll for a visible Chrome process/window that references
  the public mock host, and fail setup nonzero if the browser did not open. A
  process-only `pgrep` is not sufficient for mock website GUI primitives;
- after the browser opens, do a hidden admin `/go?sid=<sid>` readback and verify
  that the seeded app identity is still present. If the app fell back to default
  state after launch, fail setup instead of letting the agent start on the wrong
  session;
- when screenshot tools are available, prefer a light screenshot/window-title
  smoke check for GUI setup tasks;
- do not use private IPs, `/etc/hosts`, `curl --resolve`, temporary redirect
  HTML, or `about:blank` + `xdotool`;
- do not copy full mock state, sid files, admin tokens, or verifier URLs into
  `/tmp_workspace/context` or `instruction.md`;
- do not pass the real sid in Chrome's visible URL; open only the returned
  one-time `launch_url` so the browser lands on a clean app URL;
- add `CUA_GYM_ADMIN_TOKEN` to `bundle/harness_env.tsv`.

## Validation Before Returning

Run:

```bash
bash -n bundle/setup.sh
test -f bundle/instruction.md
test -f bundle/meta.json
test -d bundle/exec
test -d bundle/hidden
```

Also grep for forbidden leaks:

- real admin token values;
- `cua_mock_session.json` in `instruction.md`;
- `mock.json` or seeded-state instructions in `instruction.md`;
- complete mock seed state under `exec/`.
- custom UI source/source maps/server seeds under `exec/context/` when the UI
  is a UDA-critical surface;
- `local_custom_ui` setup that omits `/opt/uda_apps` or
  `$UDA_GYM_HARNESS_STATE_DIR`.

Also reject unused hidden setup files before returning. Every file under
`bundle/hidden/` must be referenced by basename or relative path from
`bundle/setup.sh`; otherwise remove it from `bundle/hidden/` or update
`setup.sh` to use it. This catches stale source `warmup.sh`, provenance files,
and copied-but-unused mock fixtures:

```bash
python3 - <<'PY'
from pathlib import Path
setup = Path('bundle/setup.sh').read_text()
hidden = Path('bundle/hidden')
unused = []
for path in hidden.rglob('*'):
    if path.is_file() and path.name not in setup and path.relative_to(hidden).as_posix() not in setup:
        unused.append(path.as_posix())
if unused:
    raise SystemExit('unused hidden setup files: ' + ', '.join(unused))
PY
```

If this is round > 1, read `REVIEW.md` and `SANITY.md` when present. Fix only
the reported issues, with priority on instruction/setup/reward consistency
problems and runtime setup/GUI/surface problems called out by the orchestrator
sanity check.
