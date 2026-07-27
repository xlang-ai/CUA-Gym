# CUA-Gym: Scaling Verifiable Training Environments and Tasks for Computer-Use Agents

<p align="center">
  <a href="https://arxiv.org/abs/2605.25624">📄 Paper</a> |
  <a href="https://bowenbryanwang.github.io/blog/introducing-cua-gym">📝 Blog</a> |
  <a href="https://huggingface.co/datasets/xlangai/CUA-Gym">🤗 Dataset</a> |
  <a href="https://huggingface.co/datasets/xlangai/CUA-Gym/viewer/tasks/train">🔎 Data Viewer</a> |
  🤖 Models (coming soon) |
  <a href="https://github.com/xlang-ai/CUA-Gym-Hub">🧩 CUA-Gym-Hub</a>
</p>

<div align="center">

[![arXiv](https://img.shields.io/badge/arXiv-2605.25624-b31b1b.svg)](https://arxiv.org/abs/2605.25624)
[![Dataset](https://img.shields.io/badge/🤗%20Dataset-CUA--Gym-yellow)](https://huggingface.co/datasets/xlangai/CUA-Gym)
![Models](https://img.shields.io/badge/🤗%20Models-coming%20soon-lightgrey)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)

</div>

CUA-Gym is a scalable pipeline for synthesizing verifiable RLVR training data for computer-use agents (CUAs). Given a topic, it jointly produces task instructions, environment states, and reward functions as verified triples — using coding agents to handle the engineering work previously requiring human experts.

<p align="center">
  <img src="figures/main_figure.png" alt="CUA-Gym pipeline" width="100%"/>
</p>

## 📣 Updates

- **2026-05-21:** We release the full [pipeline](https://github.com/xlang-ai/CUA-Gym) and [dataset](https://huggingface.co/datasets/xlangai/CUA-Gym) of CUA-Gym 🔥🔥🔥 (models coming soon)
- We will gradually release the full dataset — the remaining data is currently undergoing administrative review.

## About

Training computer-use agents with reinforcement learning requires a consistent triple of **(task instruction, executable environment, verifiable reward)**. Hand-authoring even one such triple takes hours; CUA-Gym automates this at scale.

**Current pipeline.** CUA-Gym now acts as a materializer for UDA-Gym generated
queries. Three coordinated agents run per task:

- **Generator** (`setup-gen`): builds the native UDA-Gym bundle setup side:
  `instruction.md`, `meta.json`, `exec/`, `hidden/`, and `setup.sh`
- **Discriminator** (`reward-gen`): builds `gt/` and `check.sh`, then reviews
  the bundle against the original UDA `query.md`, `surface.yaml`, and
  `check.yaml`
- **Orchestrator**: drives the two through iterative rounds until the bundle
  review passes and then exports `output/final/<task_id>/`

**Filtering.** Verified tuples pass through an LLM majority-vote filter (`filter/majority_vote_filter.py`) that rejects tasks where the reward is fragile, ambiguous, or inconsistent. Teacher rollouts provide a second filter stage.

**Environments.** CUA-Gym covers 110 environments: 16 desktop applications and 94 synthesized mock web applications grounded in real-world software-use distributions.

**Dataset.** The resulting [CUA-Gym dataset](https://huggingface.co/datasets/xlangai/CUA-Gym) contains **32,112** verified RLVR training tuples.

**Comparison with existing CUA RLVR datasets:**

<div align="center">

| Dataset | Platform | Data size | Env. size | Reward | Open |
|---------|----------|----------:|----------:|--------|:----:|
| GUI-Genesis | Mobile | 969 | 1 | Programmatic | No |
| WebArena-Infinity | Web | 1,260 | 10 | Programmatic | Yes |
| InfiniteWeb | Web | 600 | — | Programmatic | No★ |
| UltraCUA | Desktop | 17,000 | 9 | Programmatic | No★ |
| Gym-Anything | Desktop | 7,277 | 193 | VLM | Yes |
| **CUA-Gym** | **Desktop + Web** | **32,122** | **110** | **Programmatic** | **Yes** |

</div>

★ partial release.

## Getting Started

**Install**

```bash
git clone https://github.com/xlang-ai/CUA-Gym
cd CUA-Gym
pip install -e ".[dev]"
cp .env.example .env  # fill in OPENAI_API_KEY and ALIYUN_* credentials
```

**Materialize UDA-Gym generated queries directly**

CUA-Gym can also read UDA-Gym `gen/` outputs as task input and materialize them
into native UDA-Gym task bundles. The source UDA query package remains
read-only; CUA-Gym writes completed bundles under `output/final/<task_id>/`.
See [`docs/UDA_GYM_PIPELINE_HANDOFF.md`](docs/UDA_GYM_PIPELINE_HANDOFF.md) for
the role boundaries, workspace contract, publication gates, and office-machine
setup.

```bash
export UDA_GYM_ROOT=/path/to/UDA-Gym
export NANOROLLOUT_ROOT=/path/to/NanoRollout

# Run every valid query package under gen/
python scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen"

# Or run every valid UDA query listed in queries.jsonl
python scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen/queries.jsonl"

# Or run one generated query package directly
python scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen/20260625_849781"
```

`NANOROLLOUT_ROOT` is optional when NanoRollout is checked out at
`../NanoRollout` or `../UDA-Gym/NanoRollout`; both materializers discover those
layouts automatically.

The loader accepts only UDA packages that contain `query.md`, `check.yaml`, and
`surface.yaml`; older non-surface packages are skipped until regenerated or
re-criticized.

For UDA inputs, the final artifact is an open-box UDA-Gym bundle:

```text
output/final/<task_id>/
  meta.json
  instruction.md
  exec/
  hidden/
  setup.sh
  gt/
  check.sh
```

Mock website tasks use the public hybrid `cua-gym-*.xlang.ai` hosts: hidden
setup/check code uses `CUA_GYM_ADMIN_TOKEN`, setup opens Chrome to the returned
one-time `launch_url`, and verifier code reads server-side state through
admin-token `/go?sid=<sid>`. Seed state, sid files, admin responses, and answer
keys must not be placed in agent-visible `exec/` or instructions.

**Run the majority-vote filter**

```bash
export OPENAI_API_KEY=sk-...
python filter/majority_vote_filter.py \
  --tasks-dir output/final \
  --votes 3 \
  --model gpt-4o \
  --write
```

**Download the pre-built dataset**

```bash
huggingface-cli download xlangai/CUA-Gym --repo-type dataset --local-dir data/
```

## CUA-Gym-Hub

[CUA-Gym-Hub](https://github.com/xlang-ai/CUA-Gym-Hub) is the environment layer of CUA-Gym: a suite of self-contained mock web applications designed for scalable RL training. Each environment looks and behaves like a realistic web product, while exposing a unified state API for deterministic reset, inspection, mutation, and reward verification.

<p align="center">
  <img src="figures/env_grid.png" alt="CUA-Gym supported environments" width="75%"/>
</p>

<p align="center">
  <img src="figures/env_pipeline_t.png" alt="CUA-Gym-Hub environment pipeline" width="100%"/>
</p>

CUA-Gym-Hub is built by a multi-agent environment synthesis pipeline. Given a target application seed, the system drafts the product specification, implements the mock web app, exercises the UI with Playwright, and iterates until the live interface and API protocol match the specification.

Two design choices make each mock usable as an RL training environment: **(1) state injection** — a task seeds server-side state from hidden setup code, so a single mock can host arbitrarily many distinct task worlds with no code change; and **(2) session isolation** — every task gets an isolated session, so parallel RL workers training on the same mock never see one another's mutations. See [hub/README.md](hub/README.md#why-this-works) for the full design rationale and HTTP state API.

**What CUA-Gym-Hub provides:**

- **Realistic mock applications:** browser environments spanning productivity, communication, development, commerce, finance, analytics, and media workflows.
- **Unified state API:** every mock supports programmatic state injection, reset, retrieval, and diffing through a consistent HTTP interface.
- **Verifiable rewards:** task-specific reward functions can inspect environment state directly instead of relying on screenshots or manual labels.
- **Drop-in task generation:** generated apps plug into the CUA-Gym task synthesis pipeline as reproducible training environments.

**Run a mock app locally**

```bash
cd hub/websites/notion_mock
npm install
npm run dev          # http://localhost:5173
```

**Inspect environment state**

```bash
curl "http://localhost:5173/go?sid=task_001"
# → {"initial_state": {...}, "current_state": {...}, "state_diff": {...}}
```

Every mock supports the same session-scoped state API (`/go`, `/post`, `/state`, `/upload`, `/files/...`). For production-style deployment using `npm run preview` + a reverse proxy, see [hub/DEPLOY.md](hub/DEPLOY.md). For the full environment list, schema contract, and app-specific notes, see [hub/README.md](hub/README.md).

## CUA-Gym Datasets

CUA-Gym now emits native UDA-Gym task bundles. Each final bundle contains:

```
<task_id>/
  meta.json
  instruction.md
  exec/
  hidden/
  setup.sh
  gt/
  check.sh
```

To execute a task, stage `exec/` into `/tmp_workspace`, stage `hidden/` into
`/tmp_workspace/.uda_hidden`, run `setup.sh`, remove hidden setup assets, let the
agent follow `instruction.md`, stage `gt/`, and run `check.sh` to compute the
programmatic JSON score.

## Results

CUA-Gym improves computer-use agents through verifiable RL training over both desktop and web environments. We evaluate trained models on [OSWorld-Verified](https://os-world.github.io/) and [WebArena](https://webarena.dev/), covering realistic multi-step software and browser tasks. CUA-Gym models deliver strong gains over their base models, with the A17B model setting a new open-source state-of-the-art on both benchmarks.

<div align="center">

| Model | OSWorld-Verified | WebArena |
|-------|:----------------:|:--------:|
| *Claude Sonnet 4.6* | 72.9 | 65.6 |
| *Claude Opus 4.7* | 78.0 | — |
| *GPT-5.5* | 78.7 | — |
| *EvoCUA-8B* | 46.1 | — |
| *EvoCUA-32B* | 56.7 | — |
| *Kimi-K2.6* | 73.1 | — |
| Qwen3.5-35B-A3B (base) | 54.5 | 40.8 |
| Qwen3.5-397B-A17B (base) | 62.2 | 54.0 |
| **CUA-Gym-A3B** | **62.1** | **44.5** |
| **CUA-Gym-A17B** | **72.6** | **56.0** |

</div>

Both models set state-of-the-art among open-source CUAs at their respective scales. CUA-Gym-A3B matches the much larger A17B base at ~10× fewer active parameters.

## Citation

```bibtex
@misc{wang2026cuagymscalingverifiabletraining,
      title={CUA-Gym: Scaling Verifiable Training Environments and Tasks for Computer-Use Agents},
      author={Bowen Wang and Dunjie Lu and Junli Wang and Tianyi Bai and Shixuan Liu and Zhipeng Zhang and Haiquan Wang and Hao Hu and Tianbao Xie and Shuai Bai and Dayiheng Liu and Que Shen and Junyang Lin and Tao Yu},
      year={2026},
      eprint={2605.25624},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.25624},
}
```

## Research and Commercial Use

CUA-Gym may be used for **research, educational, and commercial purposes** under the following licenses:

- **Code, tools, and pipeline:** [Apache License 2.0](LICENSE)
- **Dataset:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

## Citation and Acknowledgement

If you use CUA-Gym, including its code, tools, CUA-Gym-Hub environments, dataset, models, or generated task artifacts, in any report, technical report, publication, thesis, presentation, blog post, documentation, or other publicly shared material, please include an explicit acknowledgement and cite the CUA-Gym paper.

## Prohibited Uses

- CUA-Gym may not be used for any purpose or activity that violates applicable laws or regulations in any jurisdiction.
- Use for illegal, unethical, deceptive, privacy-invasive, or harmful activities is strictly prohibited.
- Users may not use CUA-Gym to target real third-party services, accounts, credentials, or production systems without authorization.

## Disclaimer

- The authors, contributors, and copyright holders are not responsible for any illegal, unethical, or harmful use of CUA-Gym, nor for any direct or indirect damages resulting from such use.
- The released tasks and mock environments are intended for controlled research and evaluation. Users are solely responsible for deploying, sandboxing, and operating them safely.
- Use of the "CUA-Gym" name, logo, or trademarks does not imply endorsement or affiliation unless separate written permission is obtained.
