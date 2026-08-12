# Kimi CLI contract

Source: official Kimi Code CLI reference, accessed 2026-08-12:
<https://moonshotai.github.io/kimi-code/en/reference/kimi-command.html>

The integration relies only on the following stable documented behavior:

- the process current directory is the file-operation root.
- `--add-dir PATH` expands the workspace scope.
- `--skills-dir PATH` adds project skills.
- `--model NAME` selects the model.
- `--prompt TEXT` runs one non-interactive query.
- `--output-format stream-json` emits JSONL suitable for a controller.

The integration targets Kimi Code CLI 0.34.0+ and does not use retired
kimi-cli flags, undocumented options, browser state, or a Codex OAuth wrapper.
Authentication remains in the user's local Kimi Code configuration.
