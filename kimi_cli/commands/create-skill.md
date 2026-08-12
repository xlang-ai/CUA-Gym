# Create Domain Skill

Generate a SKILL.md for a CUA-Gym domain. Usage: `/create-skill <domain>`

Domain argument: `$ARGUMENTS`

---

## Your Goal

Create a `kimi_cli/skills/<domain>/SKILL.md` that teaches **setup-gen** and **reward-gen** agents how to **programmatically create, modify, and verify** files for this domain using pure Python code.

## Critical Principles

1. **This is a CODE MANIPULATION guide, not an operator/API-system reference.** The agents write standalone Python scripts. They do NOT invoke any evaluation framework operators. Extract knowledge FROM existing code, but teach it as "how to use the Python library".

2. **Two audiences, one file:**
   - **setup-gen** needs to know: how to CREATE and MODIFY files (initial_setup.py, golden_patch.py)
   - **reward-gen** needs to know: how to READ and VERIFY file properties (reward.py)

3. **Bitter lessons are the highest-value content.** Things that silently break, counterintuitive API behaviors, format gotchas — these are more valuable than basic tutorials.

## Process (follow in order)

### Step 1: Identify the Python library

Map the domain to its primary Python library:
| Domain | Library | File Extension |
|--------|---------|---------------|
| `libreoffice_calc` | openpyxl + pandas | .xlsx |
| `libreoffice_impress` | python-pptx | .pptx |
| `libreoffice_writer` | python-docx | .docx |
| `gimp` | Pillow (PIL) | .png/.jpg/.xcf |
| `chrome` / `firefox` | playwright / selenium | N/A (browser) |
| `os` | os, shutil, subprocess | varies |
| `vlc` | subprocess + python-vlc | .mp4/.mp3 |
| `thunderbird` | subprocess + sqlite3 | .sqlite |

If the domain is not listed, determine the library by reading existing code and task configs.

### Step 2: Mine knowledge from OSWorld source code

Read these files to EXTRACT practical knowledge (NOT to document their APIs):

```
# Evaluator metrics — reveals WHAT properties matter and HOW to verify them
/Users/bowen/Downloads/Projects/OSWorld/desktop_env/evaluators/metrics/

# Controllers — reveals HOW files get set up and common setup patterns
/Users/bowen/Downloads/Projects/OSWorld/desktop_env/controllers/

# Getters — reveals HOW to fetch/extract file content
/Users/bowen/Downloads/Projects/OSWorld/desktop_env/evaluators/getters/

# Real task examples — reveals what tasks actually look like in practice
/Users/bowen/Downloads/Projects/OSWorld/evaluation_examples/examples/<domain>/
```

Read at least:
- The relevant metric file (e.g., `table.py` for calc, `slides.py` for impress)
- 5-8 diverse task JSON configs from the examples directory
- The setup controller methods used by this domain

**What to extract:**
- What cell/element properties does the evaluator check? → These are the things reward-gen needs to verify
- What code patterns does the setup controller use? → These are patterns setup-gen should know
- What edge cases and error handling exist? → These become bitter lessons
- What file format quirks does the code work around? → These become bitter lessons

**What NOT to include in the skill:**
- OSWorld evaluator function names (`compare_table`, `compare_slides`, etc.)
- OSWorld-specific parameter formats (`sheet_idx0`, `RI0`, `EI0`, etc.)
- OSWorld config/rule schema (`"type": "sheet_data"`, `"type": "check_cell"`, etc.)
- OSWorld getter/postconfig step definitions

### Step 3: Web search the Python library

Perform web searches to supplement the knowledge extracted from code:

- `"<library> advanced tutorial create <filetype> python 2025"` — creation patterns
- `"<library> read verify properties programmatically python"` — verification patterns
- `"<library> common pitfalls gotchas"` — bitter lessons
- `"<library> <specific_feature>"` — for features discovered in Step 2 (e.g., charts, conditional formatting, slide layouts)

**Goal:** Ensure the skill covers the library correctly, not just what OSWorld happens to use.

### Step 4: Write SKILL.md

Create the directory and file:
```
kimi_cli/skills/<domain>/SKILL.md
```

Domain name uses hyphens: `libreoffice_calc` → `libreoffice-calc`.

#### Format

```markdown
---
name: <domain-with-hyphens>
description: "How to programmatically create, modify, and verify <filetype> files using Python <library>. For setup-gen and reward-gen agents."
user-invocable: false
---

# <Domain> — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify) and **reward-gen** (read/verify) how to work with <filetype> files using pure Python code.

- Library: `<library>`
- Install: `pip3 install <packages>`

---

## 1. Creating & Writing Files (setup-gen)

[Code patterns for creating files from scratch and modifying existing files.
Cover: basic creation, all relevant properties/features, styling, embedded objects, etc.
Every pattern should be a runnable code snippet.]

---

## 2. Reading & Verifying Files (reward-gen)

[Code patterns for loading files and checking every property.
Cover: reading values, verifying styles, checking structure, comparing data.
Include helper function templates that reward.py can directly use.]

---

## 3. Bitter Lessons

[Numbered list of gotchas and counterintuitive behaviors.
Each lesson should be specific and actionable, not generic advice.
Source: OSWorld code edge cases + web search findings + library quirks.]
```

#### Quality Checklist

- [ ] Every code snippet is **runnable** (correct imports, no pseudocode)
- [ ] Section 1 covers ALL features discovered in the OSWorld evaluator metrics (if the evaluator checks charts, the skill must teach how to create charts)
- [ ] Section 2 covers reading back EVERY property that Section 1 can write
- [ ] Bitter lessons include at least 8 specific, non-obvious gotchas
- [ ] No OSWorld operator names, parameter formats, or evaluation rule schemas
- [ ] Under 500 lines
- [ ] YAML frontmatter with `user-invocable: false`

### Step 5: Verify by cross-referencing

After writing, verify completeness:

1. Re-read the OSWorld evaluator for this domain
2. For every property the evaluator checks, confirm your SKILL.md teaches both how to SET it (Section 1) and how to READ it (Section 2)
3. If any property is missing, add it

### Step 6: Report

Output a summary:
- Skill file path
- Line count
- Properties covered (list)
- Bitter lessons count
- Any properties you found in the evaluator but couldn't cover (and why)

---

## Reference: Existing Skill

See `kimi_cli/skills/libreoffice-calc/SKILL.md` as the gold-standard example of the expected output format, depth, and style.
