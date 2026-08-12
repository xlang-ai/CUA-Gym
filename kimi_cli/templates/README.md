# Materialization templates

The source workspace contains no separate `templates/` directory. Its
materialization templates are the role checklists and skill assets:

- `kimi_cli/agents/{setup-gen,reward-gen,orchestrator,task-gen}.md`;
- `kimi_cli/commands/create-skill.md`;
- `kimi_cli/skills/uda-gym-materializer/SKILL.md`;
- `kimi_cli/skills/uda_cross_interface/`;
- `kimi_cli/skills/mock_websites/` and every schema;
- `kimi_cli/skills/local_custom_ui/`;
- all copied domain skills under `kimi_cli/skills/`.

`verify_mirror.py` checks that the copied file topology stays one-for-one with
the source skill/agent/command libraries. The Kimi orchestrator and main UDA
skill are intentionally adapted to the AWS/Kimi runtime; their source
checklists remain represented in the copied role files and are not forked per
task.
