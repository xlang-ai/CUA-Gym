---
name: chrome
description: "How to programmatically set up, control, and verify Google Chrome browser state using Python (Playwright CDP, SQLite, JSON configs). For setup-gen and reward-gen agents."
user-invocable: false
---

# Chrome — Python Manipulation Guide

This skill teaches **setup-gen** (create initial browser state) and **reward-gen** (verify browser state after agent actions) how to work with Chrome programmatically. Unlike file-based domains, Chrome tasks involve **three data layers**: config files (JSON/SQLite), live browser via CDP, and accessibility tree.

- Libraries: `playwright`, `sqlite3`, `json`, `beautifulsoup4`
- Install: `pip3 install playwright beautifulsoup4 lxml rapidfuzz tldextract`

---

## 0. GUI Startup on VM (for setup-gen)

After preparing browser state, setup-gen should leave Chrome visibly opened for the GUI agent.

CRITICAL VM LIMIT: GUI launches must set `DISPLAY=:0`.

```python
import os
import shlex
import subprocess
import time

def launch_gui(command: str, delay_sec: float = 1.0):
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(delay_sec)

# Open Chrome with default profile
launch_gui("google-chrome", delay_sec=2.0)

# Optional URL preload
# launch_gui('google-chrome "https://example.com"', delay_sec=2.0)
```

Guidelines:
- Use non-blocking launch (`Popen`) so `initial_setup.py` exits cleanly.
- If the task needs multiple apps, launch all required windows in order with small sleeps.

---

## 1. Setting Up Browser State (setup-gen)

### Chrome Config File Paths (Linux VM)

```python
import os, json, sqlite3, shutil, time

# Standard paths on the OSWorld Linux VM
CHROME_USER_DATA = os.path.expanduser("~/.config/google-chrome")
CHROME_DEFAULT = os.path.join(CHROME_USER_DATA, "Default")

PREFS_FILE = os.path.join(CHROME_DEFAULT, "Preferences")
LOCAL_STATE = os.path.join(CHROME_USER_DATA, "Local State")
BOOKMARKS_FILE = os.path.join(CHROME_DEFAULT, "Bookmarks")
HISTORY_DB = os.path.join(CHROME_DEFAULT, "History")
COOKIES_DB = os.path.join(CHROME_DEFAULT, "Cookies")
EXTENSIONS_DIR = os.path.join(CHROME_DEFAULT, "Extensions")

# ARM/Chromium alternative
CHROMIUM_DEFAULT = os.path.expanduser("~/snap/chromium/common/chromium/Default")
```

### Modifying Preferences (JSON)

```python
def read_prefs():
    with open(PREFS_FILE, 'r') as f:
        return json.load(f)

def write_prefs(prefs):
    with open(PREFS_FILE, 'w') as f:
        json.dump(prefs, f, indent=2)

prefs = read_prefs()

# Do Not Track
prefs['enable_do_not_track'] = True

# Default font size
prefs.setdefault('webkit', {}).setdefault('webprefs', {})
prefs['webkit']['webprefs']['default_font_size'] = 16
prefs['webkit']['webprefs']['default_fixed_font_size'] = 13
prefs['webkit']['webprefs']['minimum_font_size'] = 6

# Safe browsing
prefs.setdefault('safebrowsing', {})['enhanced'] = True
prefs['safebrowsing']['enabled'] = True

# Color scheme: 0=system, 1=light, 2=dark
prefs.setdefault('browser', {}).setdefault('theme', {})['color_scheme2'] = 2

# Profile name
prefs['profile'] = prefs.get('profile', {})
prefs['profile']['name'] = "Custom Profile"

# Startup: 5 = open new tab page (fresh start)
prefs.setdefault('session', {})['restore_on_startup'] = 5

# Default search engine
prefs.setdefault('default_search_provider_data', {}).setdefault('template_url_data', {})
prefs['default_search_provider_data']['template_url_data']['short_name'] = "DuckDuckGo"

write_prefs(prefs)
```

### Modifying Local State (JSON)

```python
def read_local_state():
    with open(LOCAL_STATE, 'r') as f:
        return json.load(f)

def write_local_state(state):
    with open(LOCAL_STATE, 'w') as f:
        json.dump(state, f, indent=2)

state = read_local_state()

# Chrome language
state['intl'] = state.get('intl', {})
state['intl']['app_locale'] = 'en-US'

# Chrome Labs experiments
state.setdefault('browser', {})['enabled_labs_experiments'] = [
    'smooth-scrolling@1', 'tab-hover-card-images@2'
]

write_local_state(state)
```

### Setting Up Bookmarks (JSON)

```python
import time as _time

def create_bookmark_entry(name, url):
    return {
        "date_added": str(int(_time.time() * 1e6)),  # Chrome microsecond timestamp
        "date_last_used": "0",
        "guid": "",  # Chrome generates this
        "id": str(int(_time.time() * 1e3)),
        "name": name,
        "type": "url",
        "url": url
    }

def create_bookmark_folder(name, children):
    return {
        "children": children,
        "date_added": str(int(_time.time() * 1e6)),
        "date_modified": str(int(_time.time() * 1e6)),
        "guid": "",
        "id": str(int(_time.time() * 1e3)),
        "name": name,
        "type": "folder"
    }

bookmarks = {
    "checksum": "",
    "roots": {
        "bookmark_bar": {
            "children": [
                create_bookmark_entry("Google", "https://www.google.com"),
                create_bookmark_folder("Liked Authors", [
                    create_bookmark_entry("Author1", "https://example.com/author1"),
                    create_bookmark_entry("Author2", "https://example.com/author2"),
                ]),
            ],
            "date_added": str(int(_time.time() * 1e6)),
            "date_modified": str(int(_time.time() * 1e6)),
            "guid": "",
            "id": "1",
            "name": "Bookmarks bar",
            "type": "folder"
        },
        "other": {"children": [], "type": "folder", "name": "Other bookmarks"},
        "synced": {"children": [], "type": "folder", "name": "Mobile bookmarks"}
    },
    "version": 1
}

with open(BOOKMARKS_FILE, 'w') as f:
    json.dump(bookmarks, f, indent=2)
```

### Setting Up Browsing History (SQLite)

```python
import datetime

def chrome_timestamp(dt=None, seconds_ago=0):
    """Chrome timestamps: microseconds since 1601-01-01 (Windows FILETIME)."""
    epoch_1601 = datetime.datetime(1601, 1, 1)
    if dt is None:
        dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds_ago)
    delta = dt - epoch_1601
    return int(delta.total_seconds() * 1_000_000)

def setup_history(history_items):
    """history_items: list of {url, title, visit_time_from_now_in_seconds}"""
    # MUST close Chrome before modifying History DB
    conn = sqlite3.connect(HISTORY_DB)
    c = conn.cursor()
    # Ensure tables exist (normally they do in an existing profile)
    c.execute("""CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INTEGER DEFAULT 1,
        typed_count INTEGER DEFAULT 0, last_visit_time INTEGER, hidden INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER, from_visit INTEGER DEFAULT 0,
        transition INTEGER DEFAULT 805306368, segment_id INTEGER DEFAULT 0,
        visit_duration INTEGER DEFAULT 0
    )""")
    for item in history_items:
        ts = chrome_timestamp(seconds_ago=item['visit_time_from_now_in_seconds'])
        c.execute("INSERT INTO urls (url, title, last_visit_time) VALUES (?, ?, ?)",
                  (item['url'], item['title'], ts))
        url_id = c.lastrowid
        c.execute("INSERT INTO visits (url, visit_time) VALUES (?, ?)", (url_id, ts))
    conn.commit()
    conn.close()

setup_history([
    {"url": "https://www.youtube.com/watch?v=abc", "title": "Video", "visit_time_from_now_in_seconds": 3600},
    {"url": "https://news.example.com", "title": "News", "visit_time_from_now_in_seconds": 7200},
])
```

### Opening Tabs via Playwright CDP

```python
from playwright.sync_api import sync_playwright

def open_chrome_tabs(urls, host="localhost", port=9222):
    """Open URLs in existing Chrome (must be running with --remote-debugging-port)."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        context = browser.contexts[0]  # use existing default profile context
        for url in urls:
            page = context.new_page()
            page.goto(url, timeout=60000, wait_until='networkidle')
        # Close default blank tab if present
        for page in context.pages:
            if page.url == "about:blank" or page.url == "chrome://newtab/":
                page.close()
                break
        # Do NOT call browser.close() — keep Chrome open for agent

open_chrome_tabs(["https://www.google.com", "https://www.github.com"])
```

---

## 2. Reading & Verifying Browser State (reward-gen)

### Reading Preferences

```python
prefs = read_prefs()  # reuse from above

# Do Not Track
do_not_track = prefs.get('enable_do_not_track', False)

# Font size
font_size = prefs.get('webkit', {}).get('webprefs', {}).get('default_font_size', 16)

# Safe browsing
safe_browsing = prefs.get('safebrowsing', {}).get('enabled', False)
enhanced_safe = prefs.get('safebrowsing', {}).get('enhanced', False)

# Color scheme
scheme = prefs.get('browser', {}).get('theme', {}).get('color_scheme2',
         prefs.get('browser', {}).get('theme', {}).get('color_scheme', 0))
# 0=system, 1=light, 2=dark

# Startup page
startup = prefs.get('session', {}).get('restore_on_startup', None)
# 5 or missing = open new tab page

# Search engine
search = prefs.get('default_search_provider_data', {}).get('template_url_data', {}).get('short_name', '')
```

### Reading Local State

```python
state = read_local_state()
language = state.get('intl', {}).get('app_locale', '')
experiments = state.get('browser', {}).get('enabled_labs_experiments', [])
exp_names = [e.split("@")[0] for e in experiments]
```

### Verifying Bookmarks

```python
with open(BOOKMARKS_FILE, 'r') as f:
    bm = json.load(f)

bar = bm['roots']['bookmark_bar']['children']
folder_names = [b['name'] for b in bar if b['type'] == 'folder']
bookmark_urls = [b['url'] for b in bar if b['type'] == 'url']

# Check specific folder contents
def get_folder_urls(bar_children, folder_name):
    for b in bar_children:
        if b['type'] == 'folder' and b['name'] == folder_name:
            return [c['url'] for c in b['children'] if c['type'] == 'url']
    return []
```

### Verifying History (SQLite)

```python
def read_history():
    conn = sqlite3.connect(HISTORY_DB)
    c = conn.cursor()
    c.execute("SELECT url, title, last_visit_time FROM urls")
    rows = c.fetchall()
    conn.close()
    return rows  # list of (url, title, timestamp)

def check_history_keyword_deleted(keyword):
    """True if no history URL contains the keyword."""
    return all(keyword not in url for url, _, _ in read_history())
```

### Verifying Cookies (SQLite)

```python
def read_cookies():
    conn = sqlite3.connect(COOKIES_DB)
    c = conn.cursor()
    c.execute("SELECT * FROM cookies")
    rows = c.fetchall()
    conn.close()
    return rows

def check_cookie_domain_deleted(domain):
    """True if no cookies from this domain exist."""
    cookies = read_cookies()
    return all(domain not in str(row[1]) for row in cookies)
```

### Verifying Extensions

```python
def get_installed_extensions():
    """Read extension names from manifest.json files."""
    names = []
    if not os.path.isdir(EXTENSIONS_DIR):
        return names
    for ext_id in os.listdir(EXTENSIONS_DIR):
        ext_path = os.path.join(EXTENSIONS_DIR, ext_id)
        if not os.path.isdir(ext_path):
            continue
        for version in os.listdir(ext_path):
            manifest = os.path.join(ext_path, version, "manifest.json")
            if os.path.exists(manifest):
                with open(manifest, 'r') as f:
                    data = json.load(f)
                    names.append(data.get('name', ''))
    return names

# Extension name aliases (same extension, different names across versions)
EXTENSION_ALIASES = [{"Zoom Chrome Extension", "Zoom for Google Chrome"}]

def canonicalize_ext(name):
    for group in EXTENSION_ALIASES:
        if name in group:
            return sorted(group)[0]
    return name
```

### Verifying Active Tab URL via CDP

```python
def get_active_tab_url(host="localhost", port=9222):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        context = browser.contexts[0]
        # Last page is usually the active one
        if context.pages:
            page = context.pages[-1]
            return page.url
    return None
```

### Verifying Page Content via CDP

```python
def get_page_info(url, host="localhost", port=9222):
    """Navigate to URL and return {title, url, content}."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        context = browser.contexts[0]
        page = context.new_page()
        page.goto(url, timeout=60000, wait_until='networkidle')
        return {"title": page.title(), "url": page.url, "content": page.content()}

def get_all_open_tabs(host="localhost", port=9222):
    """Return list of {title, url} for all open tabs."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        tabs = []
        for ctx in browser.contexts:
            for page in ctx.pages:
                try:
                    page.wait_for_load_state('networkidle', timeout=30000)
                    tabs.append({"title": page.title(), "url": page.url})
                except:
                    tabs.append({"title": "", "url": page.url})
        return tabs
```

### URL Comparison Helper

```python
from urllib.parse import urlparse, urlunparse
import tldextract

def normalize_url(url):
    """Normalize URL: drop www, ignore TLD suffix differences, strip trailing slash."""
    if not url:
        return ""
    import re
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', url):
        url = f"http://{url}"
    parsed = urlparse(url)
    extracted = tldextract.extract(parsed.netloc.lower())
    subdomain = '' if extracted.subdomain == 'www' else extracted.subdomain
    netloc = f"{subdomain}.{extracted.domain}" if subdomain else extracted.domain
    path = parsed.path if parsed.path != '/' else ''
    return urlunparse((parsed.scheme.lower(), netloc, path, parsed.params, parsed.query, parsed.fragment))

def compare_urls(url1, url2):
    return normalize_url(url1) == normalize_url(url2)
```

### Verifying Desktop Shortcuts (.desktop files)

```python
def check_desktop_shortcut(expected_name):
    """Check if a .desktop shortcut exists on Desktop."""
    desktop_dir = os.path.expanduser("~/Desktop")
    for fname in os.listdir(desktop_dir):
        if fname.endswith('.desktop'):
            with open(os.path.join(desktop_dir, fname), 'r') as f:
                content = f.read()
            for line in content.split('\n'):
                if line.startswith('Name='):
                    actual = line[5:]
                    if expected_name.lower() in actual.lower() or actual.lower() in expected_name.lower():
                        return True
    return False
```

---

## 3. Bitter Lessons

1. **Chrome must be killed before modifying SQLite databases.** History, Cookies, and other SQLite files are locked while Chrome is running. Setup scripts must `pkill chrome`, modify files, then relaunch with `--remote-debugging-port=1337`. Forgetting this causes "database is locked" errors.

2. **Chrome timestamps are NOT Unix timestamps.** Chrome uses microseconds since 1601-01-01 (Windows FILETIME epoch). `datetime(1601,1,1) + timedelta(microseconds=chrome_ts)` gives the real time. Writing Unix timestamps will produce dates in the 1600s.

3. **`connect_over_cdp` reuses existing contexts.** `browser.contexts[0]` is the real Chrome profile with cookies, history, and extensions. Do NOT create `browser.new_context()` — it creates an incognito-like context that shares nothing with the user's profile.

4. **URL comparison must normalize aggressively.** `www.google.com` and `google.com` are the same. `airbnb.com` and `airbnb.com.sg` may be the same. Always strip `www`, ignore TLD suffix, and normalize trailing slashes before comparing.

5. **Preferences file has async writes.** Chrome may not flush settings to Preferences immediately. After changing settings via the Chrome UI, poll the file up to 5 times with 1-second delays. Similarly, after writing Preferences, Chrome may overwrite your changes on next save. Write BEFORE Chrome starts.

6. **Accessibility tree URL lacks protocol.** The URL from AT-SPI's "Address and search bar" entry has no `https://` prefix. Always prepend a `goto_prefix` (typically `"https://"`) before using it.

7. **Extension names have aliases.** The same Chrome extension can have different `manifest.json` names across versions (e.g., "Zoom Chrome Extension" vs "Zoom for Google Chrome"). Canonicalize names before comparison using alias groups.

8. **`page.goto()` with `networkidle` can hang on streaming pages.** Some pages (YouTube live, infinite feeds) never reach `networkidle`. Use `timeout=60000` and catch `TimeoutError` gracefully — the page may still be usable.

9. **socat bridges port 9222 to 1337 inside the VM.** Chrome runs with `--remote-debugging-port=1337` internally. An `socat tcp-listen:9222,fork tcp:localhost:1337` bridge exposes it on port 9222 for external access. Setup scripts must launch both processes.

10. **ARM machines use `chromium`, x86 uses `google-chrome`.** Binary name, user data path, and accessibility tree application name all differ. Check `platform.machine()` to determine which binary to use. ARM: `~/snap/chromium/common/chromium/Default/`, x86: `~/.config/google-chrome/Default/`.

11. **HTML parsing needs shadow DOM traversal for Chrome settings.** Chrome settings pages (chrome://settings/*) use nested shadow DOMs. Regular CSS selectors don't penetrate shadow roots. Use `page.evaluate()` with JavaScript that calls `.shadowRoot.querySelector()` chains.

12. **`compare_urls` drops TLD suffixes entirely.** The URL normalizer uses `tldextract` and ignores the suffix, so `airbnb.com` and `airbnb.co.uk` normalize to the same domain. This is intentional for cross-region tolerance but can cause false matches.

13. **Cookie values are encrypted on disk.** Chrome encrypts cookie values using platform-specific keys (DPAPI on Windows, keychain on macOS, gnome-keyring on Linux). The `cookies` table has encrypted `value` and `encrypted_value` columns. For verification, check domain/name presence rather than decrypting values.

14. **Post-config must kill and restart Chrome before reading settings.** Many evaluators use a `postconfig` sequence: `pkill chrome` → sleep 3s → relaunch Chrome → sleep 3s → then read. This ensures settings are flushed to disk and Chrome re-reads the state cleanly.
