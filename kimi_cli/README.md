# Kimi CLI integration

This directory is the first-class Kimi Code CLI integration for CUA-Gym. The
UDA materializer invokes Kimi through `kimi_cli.runner`; it does not depend on
the historical `.codex/` runner or on NanoRollout.

The command contract is based on the official Kimi Code CLI reference:

<https://moonshotai.github.io/kimi-code/en/reference/kimi-command.html>

The materializer uses these documented options:

```text
cd <workspace>
kimi --add-dir <source-root>
     --skills-dir <kimi-skills>
     --model <model> --prompt <prompt>
     --output-format stream-json
```

`--prompt` is non-interactive and `stream-json` is JSONL for programmatic
integration. Credentials are resolved
by the local Kimi installation; they are never placed in task manifests or
materialization artifacts.

## Local checks

```bash
kimi --version
python3 -m kimi_cli.runner --help
python3 scripts/materialize.py --dry-run <uda-query-or-tree>
```

The runner deliberately does not pass `--yolo` by default. Use a local Kimi
configuration for approval policy when a task requires tool execution.
