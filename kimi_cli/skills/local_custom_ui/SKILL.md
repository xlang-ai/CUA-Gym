---
name: local_custom_ui
description: "Materialize and verify bespoke UDA browser UIs without exposing app source or verifier state to the solving agent."
---

# Local Custom UI for UDA-Gym Bundles

Use this when a source UDA query package declares `realized_as:
local_custom_ui`, has `hidden/custom_ui/`, uses `local_custom_ui://...` in
`check.yaml`, or otherwise requires a bespoke browser/dashboard surface that is
not a deployed CUA-Gym Hub mock.

Prefer CUA-Gym Hub mocks whenever one fits. A local custom UI is a fallback for
task-specific screens that cannot be represented by the deployed mock suite.

## Isolation Model

There is no strong security boundary if the solving agent can read arbitrary
host files or run as root. For local custom UI tasks, the bundle must therefore
avoid accidental source/state leaks and must record weak isolation when true.

Accepted isolation levels:

- `server_side`: app state is authoritative outside agent-visible files, usually
  on CUA-Gym Hub or a separate service.
- `hidden_service`: setup starts a local service from hidden assets, source is
  not in `exec/`, state/readback lives in `$UDA_GYM_HARNESS_STATE_DIR`.
- `weak_local`: the agent can plausibly discover source/state with CLI access.
  Do not accept this for UDA-hard scale tasks unless the task is explicitly
  about editing the app itself.

## Bundle Layout

Setup-gen may copy only user-facing input files into `bundle/exec/`.

Custom UI assets belong in:

```text
bundle/hidden/custom_ui/
  dist/
  server.py|server.js
  seed.json
```

Do not put these under `bundle/exec/context/`:

- app source directories;
- `index.html` used as the browser UI entrypoint;
- app JavaScript/TypeScript/JSX/TSX;
- source maps;
- complete seed state;
- answer keys or golden values;
- verifier/admin tokens or endpoints.

## setup.sh Requirements

For each local custom UI, `setup.sh` must:

1. require `$UDA_GYM_HARNESS_STATE_DIR` and `chmod 700` it;
2. create a per-run runtime directory, usually
   `/opt/uda_apps/${TASK_ID:-uda_task}/<random>/`;
3. copy only files from `/tmp_workspace/.uda_hidden/custom_ui/` into that
   runtime directory;
4. reject source maps and unbuilt source such as `.tsx`, `.jsx`, app source
   folders, or answer-bearing JSON in the client bundle;
5. start the server on `127.0.0.1` with a random free port;
6. write only pid, port, runtime path, and harness-only verifier token/state
   references to `$UDA_GYM_HARNESS_STATE_DIR/custom_ui.json`;
7. open Google Chrome normally to `http://127.0.0.1:<port>/`;
8. poll for a durable Chrome process or visible browser window before exiting;
9. exit nonzero if the service, browser launch, or metadata write fails.

`instruction.md` must not mention the runtime directory, harness metadata path,
server token, verifier endpoint, or hidden source path. It can say that the
custom dashboard/app is already open in Chrome, or give only the normal
localhost URL if the task naturally expects the user to open a local tool.

## check.sh Requirements

Reward-gen must grade from authoritative server-side state:

- read `$UDA_GYM_HARNESS_STATE_DIR/custom_ui.json`;
- call the local app's harness-only verifier endpoint or read the server-side
  state file named there;
- combine that state with `bundle/gt/` references when needed;
- implement every `local_custom_ui://...` check item in `check.yaml`;
- never score from visible client source, browser history, Chrome SQLite DBs,
  localStorage, cookies, IndexedDB, screenshots alone, or files under
  `/tmp_workspace/context` that duplicate hidden UI state.

Verifier endpoints should require a harness-only token stored in
`custom_ui.json` or be bound to an unadvertised local state file. Do not put the
token in the browser URL, process arguments, `exec/`, or `instruction.md`.

## Audit Failures

Treat these as blocking:

- `surface.yaml` declares `browser_app`, `dashboard_app`, `mock_saas`, or
  `local_custom_ui` while `bundle/exec/context` contains UDA-critical
  `.html`, `.js`, `.jsx`, `.ts`, `.tsx`, or `.map` files;
- `setup.sh` for `local_custom_ui` does not mention `/opt/uda_apps` and
  `$UDA_GYM_HARNESS_STATE_DIR`;
- `check.sh` for `local_custom_ui` reads browser databases or visible context
  files as reward truth;
- Chrome is not opened during setup for a required UI task;
- the task can be solved by shell-reading or patching the UI.
