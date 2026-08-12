---
name: overleaf_reward
description: "How to write reward.py scripts that verify Overleaf LaTeX project state for CUA-Gym tasks. For reward-gen agent."
user-invocable: false
---

# Overleaf — Reward Script Guide

This skill teaches **reward-gen** how to write `reward.py` scripts that verify task completion against Overleaf project state. Unlike file-based domains, there are no local artifacts — project content is fetched via HTTP.

---

## 1. Reading Task State

The state file was written by `initial_setup.py` to `/tmp/task_overleaf_state`. Fail early if not found.

```python
import json
import sys

try:
    with open('/tmp/task_overleaf_state') as f:
        state = json.load(f)
    OVERLEAF_URL = state['overleaf_url']
    PROJECT_ID = state['project_id']
except Exception as e:
    print(f'CRITICAL: Cannot read state: {e}')
    print('REWARD: 0.0')
    sys.exit(0)
```

---

## 2. Logging In and Fetching Project Content

```python
import io
import re
import zipfile
import requests

def get_csrf(session):
    resp = session.get(f'{OVERLEAF_URL}/login', timeout=10)
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    return match.group(1)

# Login as session user
try:
    session = requests.Session()
    csrf = get_csrf(session)
    resp = session.post(f'{OVERLEAF_URL}/login',
        json={'email': state['session_email'], 'password': state['session_password'], '_csrf': csrf},
        timeout=15, allow_redirects=False)
    assert resp.status_code in (200, 302)
except Exception as e:
    print(f'CRITICAL: Login failed: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

# Download project ZIP (primary data source for verification)
try:
    zip_resp = session.get(f'{OVERLEAF_URL}/Project/{PROJECT_ID}/download/zip', timeout=30)
    zip_resp.raise_for_status()
    project_zip = zip_resp.content
except Exception as e:
    print(f'CRITICAL: Cannot download project: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

# Helper functions
def read_file(filename):
    """Read a text file from the project ZIP."""
    with zipfile.ZipFile(io.BytesIO(project_zip)) as zf:
        return zf.read(filename).decode('utf-8')

def list_files():
    """List all files in the project ZIP."""
    with zipfile.ZipFile(io.BytesIO(project_zip)) as zf:
        return zf.namelist()

def file_exists(filename):
    """Check if a file exists in the project."""
    return filename in list_files()
```

---

## 3. Verification Patterns

### 3.1 LaTeX Content Checks

```python
main_tex = read_file('main.tex')

# Section exists
has_section = r'\section{Related Work}' in main_tex

# Package is loaded
has_package = r'\usepackage{hyperref}' in main_tex

# Environment exists
has_table = r'\begin{tabular}' in main_tex
has_figure = r'\begin{figure}' in main_tex
has_equation = r'\begin{equation}' in main_tex

# Count occurrences
import re
num_sections = len(re.findall(r'\\section\{', main_tex))
num_figures = len(re.findall(r'\\begin\{figure\}', main_tex))
num_citations = len(re.findall(r'\\cite\{', main_tex))

# Check specific text content (flexible matching)
has_region_data = all(r in main_tex for r in ['North America', 'Europe', 'Asia'])

# Check table dimensions
tables = re.findall(r'\\begin\{tabular\}\{([^}]+)\}', main_tex)
if tables:
    num_cols = tables[0].count('|') + tables[0].count('l') + tables[0].count('c') + tables[0].count('r')
```

### 3.2 Bibliography Checks

```python
bib = read_file('references.bib')

# Count entries
entries = re.findall(r'@\w+\{(\w+),', bib)
num_entries = len(entries)

# Check specific entry exists
has_vaswani = 'vaswani2017attention' in bib

# Check entry type
article_entries = re.findall(r'@article\{', bib)
book_entries = re.findall(r'@book\{', bib)

# Verify citations match bibliography
main_tex = read_file('main.tex')
cited_keys = set(re.findall(r'\\cite\{([^}]+)\}', main_tex))
# Flatten multi-cite like \cite{a,b,c}
all_cited = set()
for group in cited_keys:
    for key in group.split(','):
        all_cited.add(key.strip())
bib_keys = set(entries)
uncited = bib_keys - all_cited
missing = all_cited - bib_keys
```

### 3.3 File Structure Checks

```python
files = list_files()

# Required files exist
required = ['main.tex', 'references.bib']
all_present = all(f in files for f in required)

# Directory structure
has_figures_dir = any(f.startswith('figures/') for f in files)
has_sections_dir = any(f.startswith('sections/') for f in files)

# File count
tex_files = [f for f in files if f.endswith('.tex')]
image_files = [f for f in files if f.endswith(('.png', '.jpg', '.pdf'))]
```

### 3.4 Compilation Checks

```python
def check_compilation():
    """Compile and check result. Returns (success, compile_result)."""
    csrf = get_csrf(session)
    resp = session.post(f'{OVERLEAF_URL}/project/{PROJECT_ID}/compile',
        json={'rootDoc_id': '', 'draft': False, 'check': 'silent', '_csrf': csrf},
        timeout=120)
    result = resp.json()
    return result.get('status') == 'success', result

compile_ok, compile_result = check_compilation()

# Check for specific warnings
if compile_ok:
    for f in compile_result.get('outputFiles', []):
        if f['path'] == 'output.log':
            log = session.get(f'{OVERLEAF_URL}{f["url"]}', timeout=30).text
            no_warnings = 'LaTeX Warning' not in log
            no_undefined_refs = 'undefined references' not in log
```

### 3.5 PDF Content Checks (Advanced)

```python
def check_pdf_content(compile_result):
    """Download PDF and check rendered content."""
    for f in compile_result.get('outputFiles', []):
        if f['path'] == 'output.pdf':
            pdf_resp = session.get(f'{OVERLEAF_URL}{f["url"]}', timeout=30)
            pdf_bytes = pdf_resp.content
            break
    else:
        return False, 'No PDF output'

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        full_text = ''.join(page.get_text() for page in doc)
        num_pages = len(doc)
        doc.close()
        return True, {'text': full_text, 'pages': num_pages}
    except ImportError:
        # PyMuPDF not available, check PDF header only
        is_pdf = pdf_bytes[:5] == b'%PDF-'
        return is_pdf, {'size': len(pdf_bytes)}
```

### 3.6 Compiler Setting Check

```python
def check_compiler_setting(expected_compiler):
    """Verify compiler by attempting compilation with compiler-specific features.

    For xelatex: use fontspec package
    For lualatex: use luacode package
    For pdflatex: default (most packages work)
    """
    # Indirect check: if task requires xelatex and compilation succeeds
    # with a xelatex-only package, the setting is correct
    main_tex = read_file('main.tex')
    if expected_compiler == 'xelatex':
        return r'\usepackage{fontspec}' in main_tex and compile_ok
    elif expected_compiler == 'lualatex':
        return r'\usepackage{luacode}' in main_tex and compile_ok
    return compile_ok
```

---

## 4. Reward Script Template (Full)

```python
"""
Reward Script: <task_description>
Task ID: <task_id>
Domain: overleaf
Scoring:
  C1: <check> (X.X pts)
  C2: <check> (X.X pts)
  C3: <check> (X.X pts)
"""
import io
import json
import re
import sys
import zipfile

import requests

# --- Load state ---
try:
    with open('/tmp/task_overleaf_state') as f:
        state = json.load(f)
    OVERLEAF_URL = state['overleaf_url']
    PROJECT_ID = state['project_id']
except Exception as e:
    print(f'CRITICAL: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

# --- Login ---
def get_csrf(s):
    r = s.get(f'{OVERLEAF_URL}/login', timeout=10)
    m = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', r.text)
    return m.group(1)

try:
    session = requests.Session()
    csrf = get_csrf(session)
    r = session.post(f'{OVERLEAF_URL}/login',
        json={'email': state['session_email'], 'password': state['session_password'], '_csrf': csrf},
        timeout=15, allow_redirects=False)
    assert r.status_code in (200, 302)
except Exception as e:
    print(f'CRITICAL: Login failed: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

# --- Download project ---
try:
    zr = session.get(f'{OVERLEAF_URL}/Project/{PROJECT_ID}/download/zip', timeout=30)
    zr.raise_for_status()
    project_zip = zr.content
except Exception as e:
    print(f'CRITICAL: Download failed: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

def read_file(name):
    with zipfile.ZipFile(io.BytesIO(project_zip)) as zf:
        return zf.read(name).decode('utf-8')

def list_files():
    with zipfile.ZipFile(io.BytesIO(project_zip)) as zf:
        return zf.namelist()

# --- Verify ---
def verify_task():
    total_score = 0.0

    # Component 1: <description> (X.X points)
    try:
        # ... verification logic ...
        pass
    except Exception as e:
        print(f'ERROR: C1 — {e}')

    # Component 2: <description> (X.X points)
    try:
        # ... verification logic ...
        pass
    except Exception as e:
        print(f'ERROR: C2 — {e}')

    # Component 3: Compilation succeeds (X.X points)
    try:
        csrf = get_csrf(session)
        cr = session.post(f'{OVERLEAF_URL}/project/{PROJECT_ID}/compile',
            json={'rootDoc_id': '', 'draft': False, 'check': 'silent', '_csrf': csrf},
            timeout=120).json()
        if cr.get('status') == 'success':
            print(f'PASS: Compilation OK')
            total_score += 0.0  # set weight
        else:
            print(f'FAIL: Compilation: {cr.get("status")}')
    except Exception as e:
        print(f'ERROR: Compilation — {e}')

    final_score = min(total_score, 1.0)
    print(f'\nScore: {total_score}/1.0')
    print(f'REWARD: {final_score}')
    return final_score

verify_task()
```

---

## 5. LLM-as-Judge (Constrained Usage)

For task components where success cannot be verified programmatically (e.g., "write a professional abstract", "improve the writing style"):

### Budget Rule

- **>= 60%** of total score MUST come from programmatic checks
- **<= 40%** MAY use LLM judge via `call_llm_judge()`
- Every LLM judge call MUST have a `# JUSTIFICATION:` comment

### Usage

```python
sys.path.insert(0, '/tmp')
from reward_judge import call_llm_judge

# JUSTIFICATION: Task asks "write an engaging abstract" —
# no single correct phrasing, needs semantic evaluation.
main_tex = read_file('main.tex')
abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', main_tex, re.DOTALL)
if abstract_match:
    llm_score = call_llm_judge(
        task_instruction='Write an engaging abstract for a sales report',
        success_criteria='Abstract is professional, summarizes key findings, under 200 words',
        state_excerpt=abstract_match.group(1).strip(),
    )
    total_score += 0.3 * llm_score
```

---

## 6. Scoring Design Guidelines

### What to Score

| Component Type | Weight | Example |
|---|---|---|
| Required content added | 0.3-0.5 | Section added, table created, figure inserted |
| Content correctness | 0.2-0.3 | Data values match, formula correct, citations resolve |
| Compilation success | 0.1-0.3 | Project compiles without errors |
| Structure/organization | 0.1-0.2 | Files in correct directories, main document \input{}s sections |

### What NOT to Score

- **Pre-existing properties**: If the initial project already compiles, don't give points for compilation unless the task could have broken it.
- **File existence alone**: Checking that `main.tex` exists is worthless — it was there before the task started.
- **Formatting preferences**: Unless the task specifically asks for a format change.

### Progressive Scoring

Award partial credit for partial completion:

```python
# Instead of binary 0/1:
# Check each row of a required table separately
required_regions = ['North America', 'Europe', 'Asia Pacific']
found = [r for r in required_regions if r in main_tex]
component_score = len(found) / len(required_regions) * 0.4
total_score += component_score
```

---

## 7. Error Handling Checklist

Your reward.py MUST handle these failures gracefully (print `REWARD: 0.0` and exit):

| Failure | Cause | Handling |
|---|---|---|
| State file not found | initial_setup.py didn't run | `REWARD: 0.0` |
| Login fails | Password wrong or user deleted | `REWARD: 0.0` |
| Project download 404 | Project was deleted | `REWARD: 0.0` |
| ZIP is empty or corrupt | Upload failed | `REWARD: 0.0` |
| main.tex not in ZIP | Agent deleted main file | `REWARD: 0.0` |
| Compilation timeout | Heavy document or server load | Score what you can, skip compilation component |
| PyMuPDF not installed | VM missing package | Fall back to non-PDF checks |

**Never let reward.py crash without printing `REWARD: X.X`.** Wrap everything in try/except.

---

## 8. Information Barrier Reminder

As the reward-gen agent (discriminator), you MUST NOT:
- Read `initial_setup.py` or `golden_patch.py`
- Derive verification logic from setup-gen's implementation
- Hardcode expected values from the golden state

Your reward script must be derivable purely from `task_config.json` (task description + success criteria). Explore the VMs to understand what changed, but design scoring based on task requirements.

---

## 9. REWARD: X.X Format

The **last printed line** of reward.py MUST be `REWARD: X.X` where X.X is a float between 0.0 and 1.0.

```python
print(f'REWARD: {final_score}')
```

The pipeline parses this line to extract the reward value. Any other format will cause evaluation failure.
