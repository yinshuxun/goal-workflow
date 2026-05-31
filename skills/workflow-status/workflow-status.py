#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import html
import http.server
import json
import os
import re
import socket
import socketserver
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from pathlib import Path

TZ = timezone(timedelta(hours=8))
COLUMN_ORDER = [
    ('blocked', 'Blocked'),
    ('todo', 'Todo'),
    ('inProgress', 'In Progress'),
    ('review', 'Review'),
    ('done', 'Done'),
]
ISSUE_TOKEN_RE = re.compile(r'^(\d{1,4})([a-z]?)$', re.I)
FOCUS_COLUMNS = [
    ('blocked', 'Blocked'),
    ('todo', 'Ready next'),
    ('inProgress', 'In Progress'),
    ('review', 'Review'),
]
KANBAN_COLUMNS = [
    ('todo', 'Todo'),
    ('inProgress', 'In Progress'),
    ('review', 'Review'),
    ('done', 'Done'),
]
TRACEABILITY_GROUPS = [
    {
        'id': 'runtime-shell',
        'title': 'Runtime / Shell',
        'description': 'Host shell, plugin runtime, manifest, route ownership, and dynamic plugin safety.',
        'specCodes': ['2.2', '3.2', '5.3', '7.4'],
    },
    {
        'id': 'deployment-migration',
        'title': 'Deployment Migration',
        'description': 'Deployment list/detail/create/edit migration and browser parity evidence.',
        'specCodes': ['3.1', '4.2', '5.4', '9.4', '10.1'],
    },
    {
        'id': 'validation-evidence',
        'title': 'Validation & Evidence',
        'description': 'Automated checks, browser validation, evidence records, and data protection.',
        'specCodes': ['7.3', '9.1', '9.2', '9.3', '9.4', '10.4'],
    },
    {
        'id': 'platform-evolution',
        'title': 'Platform Evolution',
        'description': 'Configurable style, intent operations, metadata, and next-generation cloud UI.',
        'specCodes': ['2.6', '5.6', '6.1', '10.3'],
    },
    {
        'id': 'ui-foundation',
        'title': 'UI Foundation',
        'description': 'UI capability foundation, visual style, and component-level validation.',
        'specCodes': ['2.3', '8.2', '9.2'],
    },
]


def resolve_root(start: Path, explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        return root if root.name == '.workflow' else root / '.workflow'
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / '.workflow' / 'config.json').exists():
            return path / '.workflow'
        if (path / '.workflow').is_dir():
            return path / '.workflow'
    if (current / 'tasks').is_dir():
        return current / 'tasks'
    raise SystemExit('No .workflow workspace found. Run /workflow-init first.')


def section(text: str, name: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == f'## {name}':
            start = index + 1
            break
    if start is None:
        return ''
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith('## '):
            end = index
            break
    return '\n'.join(lines[start:end]).strip()


def first_section_line(text: str, name: str, default: str = 'unknown') -> str:
    for line in section(text, name).splitlines():
        clean = line.strip()
        if clean:
            return clean
    return default


def normalize_issue_id(value: str) -> str:
    raw = str(value).strip().lower()
    raw = raw.removeprefix('issue-').removeprefix('#')
    match = ISSUE_TOKEN_RE.match(raw)
    if not match:
        return raw
    number, suffix = match.groups()
    return f'issue-{int(number):03d}{suffix.lower()}'


def issue_number(path: Path) -> str:
    match = re.search(r'issue-(\d{1,4}[a-z]?)', path.name, re.I)
    if not match:
        return path.stem
    return normalize_issue_id(match.group(1)).removeprefix('issue-')


def issue_label(issue_id: str) -> str:
    return f"#{issue_id.removeprefix('issue-')}"


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def parse_dependencies(raw: str) -> list[str]:
    if not raw or raw.strip().lower() in {'none', '无', '—', '-'}:
        return []
    refs: list[str] = []
    for issue_ref, hash_ref in re.findall(r'issue-(\d{1,4}[a-z]?)|#(\d{1,4}[a-z]?)', raw, re.I):
        refs.append(normalize_issue_id(issue_ref or hash_ref))
    return dedupe(refs)


def parse_check_items(raw: str) -> list[dict]:
    items = []
    for mark, text in re.findall(r'^- \[( |x|X)\]\s+(.+)$', raw, re.M):
        items.append({'done': mark.lower() == 'x', 'text': text.strip()})
    return items


def plain_excerpt(markdown: str, max_chars: int = 420) -> str:
    lines = []
    for line in markdown.splitlines():
        clean = re.sub(r'[`*_>#-]', '', line).strip()
        if clean:
            lines.append(clean)
    text = ' '.join(lines)
    return text[: max_chars - 1] + '…' if len(text) > max_chars else text


def markdown_href(workflow_path: str) -> str:
    return f"markdown.html?file={quote(workflow_path, safe='')}"


def parse_issue(path: Path, spec_catalog: dict[str, dict]) -> dict:
    text = path.read_text()
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith('# ')), path.stem)
    acceptance = section(text, 'Acceptance Criteria')
    check_items = parse_check_items(acceptance)
    done = sum(1 for item in check_items if item['done'])
    total = len(check_items)
    number = issue_number(path)
    issue_id = normalize_issue_id(number)
    spec_codes = parse_spec_codes(section(text, 'SPEC Reference'))
    return {
        'id': issue_id,
        'number': number,
        'label': issue_label(issue_id),
        'file': path.name,
        'path': f'.workflow/issues/{path.name}',
        'rawHref': markdown_href(f'issues/{path.name}'),
        'title': title,
        'description': section(text, 'Description'),
        'descriptionExcerpt': plain_excerpt(section(text, 'Description')),
        'priority': first_section_line(text, 'Priority'),
        'type': first_section_line(text, 'Type'),
        'dependencies': parse_dependencies(section(text, 'Dependencies')),
        'specReference': section(text, 'SPEC Reference'),
        'specReferences': [spec_reference(code, spec_catalog) for code in spec_codes],
        'acceptanceItems': check_items,
        'output': section(text, 'Output'),
        'checklist': {'done': done, 'total': total},
        'completionRatio': done / total if total else 0,
    }


def parse_spec_codes(raw: str) -> list[str]:
    codes = re.findall(r'\b\d+(?:\.\d+)+\b', raw)
    return dedupe(codes)


def spec_reference(code: str, catalog: dict[str, dict]) -> dict:
    value = catalog.get(code, {})
    return {
        'code': code,
        'title': value.get('title', ''),
        'excerpt': value.get('excerpt', ''),
        'file': value.get('file', ''),
        'path': value.get('path', ''),
        'rawHref': markdown_href(f"specs/{value.get('file', '')}") if value.get('file') else '',
    }


def spec_catalog(root: Path) -> dict[str, dict]:
    specs_dir = root / 'specs'
    if not specs_dir.is_dir():
        return {}
    catalog: dict[str, dict] = {}
    for path in sorted(specs_dir.glob('*.md')):
        text = path.read_text()
        headings = list(re.finditer(r'^(#{2,6})\s+(\d+(?:\.\d+)+)\s+(.+)$', text, re.M))
        for index, match in enumerate(headings):
            code = match.group(2)
            title = match.group(3).strip()
            start = match.end()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            excerpt = plain_excerpt(text[start:end])
            catalog.setdefault(
                code,
                {
                    'code': code,
                    'title': title,
                    'excerpt': excerpt,
                    'file': path.name,
                    'path': f'.workflow/specs/{path.name}',
                },
            )
    return catalog


def is_done(issue: dict) -> bool:
    return issue['checklist']['total'] > 0 and issue['checklist']['done'] == issue['checklist']['total']


def extract_verification_issue_ids(path: Path) -> set[str]:
    stem = path.stem.lower()
    if not stem.startswith('issue-'):
        return set()
    ids: set[str] = set()
    for token in stem.removeprefix('issue-').split('-'):
        if not ISSUE_TOKEN_RE.fullmatch(token):
            break
        ids.add(normalize_issue_id(token))
    return ids


def verification_index(verification_dir: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    if not verification_dir.is_dir():
        return index
    for path in verification_dir.glob('*.md'):
        for issue_id in extract_verification_issue_ids(path):
            index.setdefault(issue_id, []).append(path)
    return index


def verification_state(issue: dict, index: dict[str, list[Path]]) -> str:
    matches = index.get(issue['id'], [])
    if not matches:
        return 'missing' if is_done(issue) else 'not-required'
    text = max(matches, key=lambda p: p.stat().st_mtime_ns).read_text().lower()
    if 'passed' in text or 'completion decision: yes' in text or '通过' in text:
        return 'passed'
    if 'failed' in text or 'incomplete' in text or '失败' in text:
        return 'failed'
    return 'pending'


def verification_files(issue: dict, index: dict[str, list[Path]], root: Path) -> list[dict]:
    files = []
    for path in sorted(index.get(issue['id'], [])):
        files.append({'file': path.name, 'path': str(path.relative_to(root.parent)), 'href': f'../verification/{path.name}'})
    return files


def read_current_progress(root: Path) -> str:
    progress = root / 'progress' / 'current.md'
    return progress.read_text() if progress.exists() else ''


def progress_status(text: str) -> str | None:
    match = re.search(r'^\s*-?\s*Status:\s*([A-Za-z][\w -]*)\s*$', text, re.I | re.M)
    if not match:
        return None
    value = match.group(1).strip().lower().replace('-', '_').replace(' ', '_')
    return 'in_progress' if value == 'inprogress' else value


def progress_issue_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for issue_ref, hash_ref in re.findall(r'issue-(\d{1,4}[a-z]?)|#(\d{1,4}[a-z]?)', text, re.I):
        ids.add(normalize_issue_id(issue_ref or hash_ref))
    return ids


def active_issue_ids_from_text(text: str) -> set[str]:
    for line in text.splitlines():
        if re.search(r'\b(?:Active\s+)?Issue\b', line, re.I):
            ids = progress_issue_ids(line)
            if ids:
                return ids
    return set()


def build_data(root: Path) -> dict:
    issues_dir = root / 'issues'
    specs = spec_catalog(root)
    issues = [parse_issue(path, specs) for path in sorted(issues_dir.glob('*.md'))] if issues_dir.is_dir() else []
    by_id = {issue['id']: issue for issue in issues}
    progress_text = read_current_progress(root)
    current_status = progress_status(progress_text)
    progress_ids = progress_issue_ids(progress_text)
    active_ids = active_issue_ids_from_text(progress_text)
    verification_by_issue = verification_index(root / 'verification')

    columns = [{'id': key, 'title': title, 'cards': []} for key, title in COLUMN_ORDER]
    by_column = {column['id']: column for column in columns}

    for issue in issues:
        blockers = []
        for dep in issue['dependencies']:
            if dep not in by_id or not is_done(by_id[dep]):
                blockers.append(dep)
        issue['blockedBy'] = dedupe(blockers)
        issue['dependencyLabels'] = [issue_label(dep) for dep in issue['dependencies']]
        issue['blockedByLabels'] = [issue_label(dep) for dep in issue['blockedBy']]
        issue['blockedReasons'] = blocked_reasons(issue['blockedBy'], by_id)
        issue['verification'] = verification_state(issue, verification_by_issue)
        issue['verificationFiles'] = verification_files(issue, verification_by_issue, root)
        issue['suggestedCommand'] = f"/goal .workflow/issues/{issue['file']}"
        if issue['blockedBy']:
            status = 'blocked'
        elif is_done(issue):
            status = 'done'
        elif current_status == 'review' and issue['id'] in progress_ids:
            status = 'review'
        elif current_status == 'in_progress' and issue['id'] in active_ids:
            status = 'inProgress'
        elif current_status is None and issue['id'] in active_ids:
            status = 'inProgress'
        else:
            status = 'todo'
        issue['status'] = status
        by_column[status]['cards'].append(issue)

    summary = {
        'total': len(issues),
        'todo': len(by_column['todo']['cards']),
        'inProgress': len(by_column['inProgress']['cards']),
        'blocked': len(by_column['blocked']['cards']),
        'review': len(by_column['review']['cards']),
        'done': len(by_column['done']['cards']),
        'ready': len(by_column['todo']['cards']),
        'verificationMissing': sum(
            1 for column in columns for card in column['cards'] if card['verification'] == 'missing'
        ),
    }
    spec_sections = sorted(specs.values(), key=lambda item: [int(part) for part in item['code'].split('.')])
    return {
        'workflow': workflow_name(root),
        'updatedAt': datetime.now(TZ).isoformat(timespec='seconds'),
        'summary': summary,
        'health': health_summary(issues),
        'recommendedNext': next_issue_from_columns(by_column),
        'columns': columns,
        'views': {
            'focus': view_columns(by_column, FOCUS_COLUMNS),
            'kanban': view_columns(by_column, KANBAN_COLUMNS),
        },
        'traceabilityGroups': traceability_groups(issues),
        'specSections': spec_sections,
    }


def blocked_reasons(blocked_by: list[str], by_id: dict[str, dict]) -> list[dict]:
    reasons = []
    for issue_id in blocked_by:
        issue = by_id.get(issue_id)
        reasons.append(
            {
                'id': issue_id,
                'label': issue_label(issue_id),
                'title': issue['title'] if issue else 'Missing dependency',
                'missing': issue is None,
            }
        )
    return reasons


def view_columns(by_column: dict[str, dict], definitions: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            'id': column_id,
            'title': title,
            'cards': by_column[column_id]['cards'],
        }
        for column_id, title in definitions
    ]


def next_issue_from_columns(by_column: dict[str, dict]) -> dict | None:
    for column_id in ['inProgress', 'todo', 'review', 'blocked']:
        cards = by_column[column_id]['cards']
        if cards:
            return cards[0]
    return None


def health_summary(issues: list[dict]) -> dict:
    missing_dependencies = sum(1 for issue in issues for reason in issue.get('blockedReasons', []) if reason['missing'])
    return {
        'blocked': sum(1 for issue in issues if issue.get('status') == 'blocked'),
        'ready': sum(1 for issue in issues if issue.get('status') == 'todo'),
        'verificationMissing': sum(1 for issue in issues if issue.get('verification') == 'missing'),
        'missingDependencies': missing_dependencies,
    }


def traceability_groups(issues: list[dict]) -> list[dict]:
    result = []
    for group in TRACEABILITY_GROUPS:
        spec_codes = set(group['specCodes'])
        cards = [issue for issue in issues if any(spec['code'] in spec_codes for spec in issue['specReferences'])]
        result.append(
            {
                **group,
                'issueCount': len(cards),
                'doneCount': sum(1 for card in cards if card.get('status') == 'done'),
                'blockedCount': sum(1 for card in cards if card.get('status') == 'blocked'),
                'readyCount': sum(1 for card in cards if card.get('status') == 'todo'),
            }
        )
    return result


def workflow_name(root: Path) -> str:
    config = root / 'config.json'
    if config.exists():
        try:
            data = json.loads(config.read_text())
            return data.get('name') or data.get('workflow') or root.parent.name
        except json.JSONDecodeError:
            pass
    return root.parent.name


def markdown_data(root: Path) -> dict[str, str]:
    documents: dict[str, str] = {}
    for folder in ['issues', 'specs', 'verification']:
        source = root / folder
        if not source.is_dir():
            continue
        for path in sorted(source.glob('*.md')):
            documents[f'{folder}/{path.name}'] = path.read_text()
    return documents


def write_html(root: Path, data: dict) -> None:
    status_dir = root / 'status'
    status_dir.mkdir(exist_ok=True)
    (status_dir / 'data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
    (status_dir / 'markdown-data.json').write_text(json.dumps(markdown_data(root), ensure_ascii=False, indent=2))
    (status_dir / 'markdown.html').write_text(MARKDOWN_HTML)
    (status_dir / 'style.css').write_text(STYLE)
    (status_dir / 'app.js').write_text(render_app_js(data))
    (status_dir / 'index.html').write_text(render_html(data))


def render_html(data: dict) -> str:
    updated = datetime.fromisoformat(data['updatedAt']).strftime('%Y-%m-%d %H:%M')
    summary = data['summary']
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(data['workflow'])} status</title>
  <link rel="icon" href="data:," />
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="topbar">
    <div>
      <p class="eyebrow">workflow cockpit</p>
      <h1>{html.escape(data['workflow'])}</h1>
      <div class="meta">Root: .workflow/ · Updated: {html.escape(updated)}</div>
    </div>
    <label class="theme-control">Theme<select id="themeMode"><option value="default">Default</option><option value="dark">Dark</option><option value="github">GitHub</option><option value="nord">Nord</option><option value="solarized">Solarized</option></select></label>
  </header>
  <section class="summary">
    {metric('Total', summary['total'])}
    {metric('Blocked', summary['blocked'])}
    {metric('Ready', summary['ready'])}
    {metric('In Progress', summary['inProgress'])}
    {metric('Review', summary['review'])}
    {metric('Done', summary['done'])}
  </section>
  <section class="toolbar" aria-label="Workflow filters">
    <label>Search<input id="searchInput" type="search" placeholder="Issue, title, description" /></label>
    <label>View<select id="viewMode"><option value="focus">Focus</option><option value="kanban">Kanban</option></select></label>
    <label>Priority<select id="priorityFilter"><option value="all">All</option></select></label>
    <label>Type<select id="typeFilter"><option value="all">All</option></select></label>
    <label>Verification<select id="verificationFilter"><option value="all">All</option></select></label>
    <label class="check"><input id="hideDone" type="checkbox" checked /> Hide done</label>
  </section>
  <main class="layout">
    <aside class="navigator" aria-label="Workflow navigation">
      <section>
        <h2>Execution</h2>
        <div id="executionNav" class="nav-list"></div>
      </section>
      <section>
        <h2>Traceability</h2>
        <div id="traceabilityNav" class="nav-list"></div>
      </section>
      <section>
        <h2>Health</h2>
        <div id="healthNav" class="nav-list"></div>
      </section>
    </aside>
    <section id="board" class="board" aria-label="Workflow board"></section>
  </main>
  <aside id="drawer" class="drawer" aria-hidden="true">
    <div class="drawer-head">
      <div>
        <div id="drawerLabel" class="drawer-label"></div>
        <h2 id="drawerTitle"></h2>
      </div>
      <button id="closeDrawer" class="icon-button" aria-label="Close detail">×</button>
    </div>
    <div id="drawerContent" class="drawer-content"></div>
  </aside>
  <div id="drawerBackdrop" class="drawer-backdrop"></div>
  <script src="app.js"></script>
</body>
</html>
'''

def metric(label: str, value: int) -> str:
    return f'<div class="metric"><strong>{value}</strong><span>{html.escape(label)}</span></div>'


def render_app_js(data: dict) -> str:
    return f"const WORKFLOW_DATA = {json.dumps(data, ensure_ascii=False)};\n{APP_JS}"


def print_terminal(root: Path, data: dict) -> None:
    summary = data['summary']
    print(f"Workflow: {data['workflow']}")
    print(f"Root: {root}/")
    print(f"Updated: {datetime.fromisoformat(data['updatedAt']).strftime('%Y-%m-%d %H:%M')}")
    print('\nSummary:')
    print(
        f"- Issues: {summary['total']} total / {summary['done']} done / "
        f"{summary['review']} review / {summary['inProgress']} in progress / {summary['todo']} todo"
    )
    print(f"- Ready: {summary['ready']}")
    print(f"- Blocked: {summary['blocked']}")
    print(f"- Verification missing: {summary['verificationMissing']}")
    next_card = next_issue(data)
    print(f"- Next issue: {next_card['file'] if next_card else 'None'}")
    for column in data['columns']:
        if not column['cards']:
            continue
        print(f"\n{column['title']}")
        for card in column['cards']:
            deps = ', '.join(card['dependencyLabels']) or 'None'
            print(f"  [{card['priority']}][{card['type']}] {card['file']} {card['title']}")
            print(
                f"    acceptance: {card['checklist']['done']}/{card['checklist']['total']}; "
                f"depends: {deps}; verification: {card['verification']}"
            )
    if next_card:
        print('\nSuggested next step:')
        print(f"  /goal .workflow/issues/{next_card['file']}")


def next_issue(data: dict) -> dict | None:
    for column_id in ['inProgress', 'todo', 'blocked']:
        column = next(column for column in data['columns'] if column['id'] == column_id)
        if column['cards']:
            return column['cards'][0]
    return None


def snapshot(paths: list[Path]) -> tuple:
    values = []
    for path in paths:
        if path.is_file():
            values.append((str(path), path.stat().st_mtime_ns))
        elif path.is_dir():
            values.extend((str(child), child.stat().st_mtime_ns) for child in path.rglob('*') if child.is_file())
    return tuple(sorted(values))


def first_available_port(start: int) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                continue
            return port
    raise SystemExit(f'No available port found from {start} to {start + 99}.')


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def serve_dashboard(root: Path, port: int, open_browser: bool, watch: bool) -> None:
    actual_port = first_available_port(port)
    url = f'http://127.0.0.1:{actual_port}/status/index.html'
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    with ReusableTCPServer(('127.0.0.1', actual_port), handler) as server:
        print(f'Serving {root} at {url}')
        if open_browser:
            webbrowser.open(url)
        if watch:
            server.timeout = 1
            run_watch(root, server)
        else:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print('\nStopped workflow dashboard server.')


def run_watch(root: Path, server: ReusableTCPServer) -> None:
    watch_paths = [root / 'issues', root / 'progress', root / 'verification', root / 'notes', root / 'config.json', root / 'specs']
    print('Watching .workflow/...')
    print(f"[{datetime.now(TZ).strftime('%H:%M:%S')}] rebuilt .workflow/status/index.html")
    last = snapshot(watch_paths)
    try:
        while True:
            server.handle_request()
            current = snapshot(watch_paths)
            if current == last:
                continue
            last = current
            write_html(root, build_data(root))
            print(f"[{datetime.now(TZ).strftime('%H:%M:%S')}] workflow changed, rebuilt .workflow/status/index.html", flush=True)
    except KeyboardInterrupt:
        print('\nStopped workflow dashboard server.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate goal-workflow status board')
    parser.add_argument('--dir')
    parser.add_argument('--html', action='store_true', help='Generate HTML dashboard. This is the default.')
    parser.add_argument('--shell', action='store_true', help='Print terminal status instead of generating HTML.')
    parser.add_argument('--watch', action='store_true', help='Rebuild the served dashboard when workflow files change.')
    parser.add_argument('--no-open', action='store_true', help='Do not open the dashboard in the default browser.')
    parser.add_argument('--no-serve', action='store_true', help='Only generate dashboard files without starting a local server.')
    parser.add_argument('--port', type=int, default=int(os.environ.get('WORKFLOW_STATUS_PORT', '8766')))
    args = parser.parse_args()

    if args.watch and args.shell:
        raise SystemExit('--watch cannot be combined with --shell')
    if args.shell and (args.no_open or args.no_serve):
        raise SystemExit('--shell cannot be combined with --no-open or --no-serve')

    root = resolve_root(Path.cwd(), args.dir)
    data = build_data(root)
    if args.shell:
        print_terminal(root, data)
        return 0

    write_html(root, data)
    print(f'Generated {root / "status" / "index.html"}')
    if args.no_serve:
        return 0

    serve_dashboard(root, args.port, not args.no_open, args.watch)
    return 0


MARKDOWN_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>workflow markdown</title>
  <link rel="icon" href="data:," />
  <style>
    body { margin: 0; background: var(--panel-soft); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    main { max-width: 1040px; margin: 0 auto; padding: 32px 24px; }
    .toolbar { margin-bottom: 16px; display: flex; justify-content: space-between; gap: 16px; align-items: center; color: #57606a; }
    a { color: #0969da; text-decoration: none; }
    article { background: var(--panel); border: 1px solid #d0d7de; border-radius: 8px; padding: 24px; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; font: 14px/1.6 ui-monospace, SFMono-Regular, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; }
    .error { color: #cf222e; }
  </style>
</head>
<body>
  <main>
    <div class="toolbar"><a href="index.html">← Back to dashboard</a><span id="fileLabel"></span></div>
    <article><pre id="content">Loading…</pre></article>
  </main>
  <script>
    const params = new URLSearchParams(location.search);
    const file = params.get('file') || '';
    document.querySelector('#fileLabel').textContent = file;
    fetch('markdown-data.json')
      .then((response) => response.json())
      .then((documents) => {
        const content = documents[file];
        const target = document.querySelector('#content');
        if (typeof content === 'string') {
          target.textContent = content;
        } else {
          target.className = 'error';
          target.textContent = `Markdown file not found: ${file}`;
        }
      })
      .catch((error) => {
        const target = document.querySelector('#content');
        target.className = 'error';
        target.textContent = error.message;
      });
  </script>
</body>
</html>
'''

APP_JS = r"""
const allCards = WORKFLOW_DATA.columns.flatMap((column) => column.cards);
const cardsById = Object.fromEntries(allCards.map((card) => [card.id, card]));
const validThemes = new Set(['default', 'dark', 'github', 'nord', 'solarized']);
const storedTheme = localStorage.getItem('workflow-status-theme');
const state = { query: '', view: 'focus', theme: validThemes.has(storedTheme) ? storedTheme : 'default', priority: 'all', type: 'all', verification: 'all', nav: 'all', hideDone: true };

const els = {
  board: document.querySelector('#board'),
  search: document.querySelector('#searchInput'),
  view: document.querySelector('#viewMode'),
  theme: document.querySelector('#themeMode'),
  priority: document.querySelector('#priorityFilter'),
  type: document.querySelector('#typeFilter'),
  verification: document.querySelector('#verificationFilter'),
  hideDone: document.querySelector('#hideDone'),
  executionNav: document.querySelector('#executionNav'),
  traceabilityNav: document.querySelector('#traceabilityNav'),
  healthNav: document.querySelector('#healthNav'),
  drawer: document.querySelector('#drawer'),
  drawerBackdrop: document.querySelector('#drawerBackdrop'),
  drawerLabel: document.querySelector('#drawerLabel'),
  drawerTitle: document.querySelector('#drawerTitle'),
  drawerContent: document.querySelector('#drawerContent'),
};

function uniq(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), 'zh-CN'));
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

function option(value, label) {
  return `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`;
}

function fillFilters() {
  for (const priority of uniq(allCards.map((card) => card.priority))) els.priority.insertAdjacentHTML('beforeend', option(priority, priority));
  for (const type of uniq(allCards.map((card) => card.type))) els.type.insertAdjacentHTML('beforeend', option(type, type));
  for (const verification of uniq(allCards.map((card) => card.verification))) els.verification.insertAdjacentHTML('beforeend', option(verification, verification));
}

function setNav(value) {
  state.nav = state.nav === value ? 'all' : value;
  render();
}

function navButton(value, label, count, detail = '') {
  return `<button class="nav-item ${state.nav === value ? 'active' : ''}" data-nav="${escapeHtml(value)}">
    <span>${escapeHtml(label)}</span><strong>${count}</strong>${detail ? `<small>${escapeHtml(detail)}</small>` : ''}
  </button>`;
}

function renderNavigation() {
  const counts = Object.fromEntries(['blocked', 'todo', 'inProgress', 'review'].map((status) => [status, allCards.filter((card) => card.status === status).length]));
  els.executionNav.innerHTML = [
    navButton('status:blocked', 'Blocked', counts.blocked, 'Resolve bottlenecks first'),
    navButton('status:todo', 'Ready next', counts.todo, 'Ready to execute'),
    navButton('status:inProgress', 'In Progress', counts.inProgress, 'Currently active'),
    navButton('status:review', 'Review', counts.review, 'Needs closeout'),
  ].join('');

  els.traceabilityNav.innerHTML = WORKFLOW_DATA.traceabilityGroups.map((group) =>
    navButton(`group:${group.id}`, group.title, group.issueCount, `${group.doneCount} done · ${group.blockedCount} blocked`)
  ).join('');

  const health = WORKFLOW_DATA.health;
  els.healthNav.innerHTML = [
    navButton('health:verificationMissing', 'Missing verification', health.verificationMissing, 'Done without evidence'),
    navButton('health:missingDependencies', 'Missing dependencies', health.missingDependencies, 'Broken dependency refs'),
    navButton('health:blocked', 'All blocked work', health.blocked, 'Blocked by incomplete work'),
  ].join('');

  document.querySelectorAll('[data-nav]').forEach((button) => button.addEventListener('click', () => setNav(button.dataset.nav)));
}

function cardMatchesNav(card) {
  if (state.nav === 'all') return true;
  const [kind, value] = state.nav.split(':');
  if (kind === 'status') return card.status === value;
  if (kind === 'group') {
    const group = WORKFLOW_DATA.traceabilityGroups.find((item) => item.id === value);
    return Boolean(group && card.specReferences.some((spec) => group.specCodes.includes(spec.code)));
  }
  if (kind === 'health' && value === 'verificationMissing') return card.verification === 'missing';
  if (kind === 'health' && value === 'missingDependencies') return card.blockedReasons.some((reason) => reason.missing);
  if (kind === 'health' && value === 'blocked') return card.status === 'blocked';
  return true;
}

function filteredCards() {
  const query = state.query.trim().toLowerCase();
  return allCards.filter((card) => {
    if (state.view === 'focus' && card.status === 'done') return false;
    if (state.view === 'kanban' && state.hideDone && card.status === 'done') return false;
    if (state.priority !== 'all' && card.priority !== state.priority) return false;
    if (state.type !== 'all' && card.type !== state.type) return false;
    if (state.verification !== 'all' && card.verification !== state.verification) return false;
    if (!cardMatchesNav(card)) return false;
    if (query) {
      const haystack = [card.title, card.file, card.description, card.type, card.priority, card.specReference, card.label].join(' ').toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    return true;
  });
}

function activeViewColumns() {
  return WORKFLOW_DATA.views[state.view] || WORKFLOW_DATA.views.focus;
}

function applyTheme() {
  document.documentElement.dataset.theme = state.theme === 'default' ? '' : state.theme;
  els.theme.value = state.theme;
  localStorage.setItem('workflow-status-theme', state.theme);
}

function render() {
  applyTheme();
  renderNavigation();
  const cards = filteredCards();
  const columns = activeViewColumns();
  els.hideDone.disabled = state.view === 'focus';
  els.board.style.gridTemplateColumns = `repeat(${Math.max(1, columns.length)}, minmax(260px, 1fr))`;
  els.board.innerHTML = columns.map((column) => renderColumn(column.title, cards.filter((card) => card.status === column.id))).join('');
  els.board.querySelectorAll('[data-card-id]').forEach((button) => button.addEventListener('click', () => openDrawer(button.dataset.cardId)));
}

function renderColumn(title, cards) {
  const body = cards.length ? cards.map(renderCard).join('') : '<div class="empty">No issues</div>';
  return `<section class="column"><h2>${escapeHtml(title)}<span>${cards.length}</span></h2>${body}</section>`;
}

function renderCard(card) {
  const pct = Math.round(card.completionRatio * 100);
  const specs = groupLabelsForCard(card).join(', ') || card.specReferences.map((item) => item.code).join(', ') || 'No SPEC group';
  const blocked = card.blockedReasons.length ? `<div class="blocked-line">Blocked by: ${escapeHtml(card.blockedReasons.map((item) => `${item.label} ${item.missing ? '(missing)' : item.title}`).join(', '))}</div>` : '';
  return `<button class="card ${card.status === 'blocked' ? 'is-blocked' : ''}" data-card-id="${escapeHtml(card.id)}">
    <div class="card-meta"><span class="priority ${escapeHtml(card.priority)}">${escapeHtml(card.priority)}</span><span>${escapeHtml(card.type)}</span><span class="verification ${escapeHtml(card.verification)}">${escapeHtml(card.verification)}</span></div>
    <div class="card-title">${escapeHtml(card.label)} ${escapeHtml(card.title)}</div>
    <div class="card-spec">${escapeHtml(specs)}</div>
    <div class="card-progress"><span style="width:${pct}%"></span></div>
    <div class="card-foot"><span>${card.checklist.done}/${card.checklist.total}</span><span>${escapeHtml(card.dependencyLabels.join(', ') || 'No dependencies')}</span></div>
    ${blocked}
  </button>`;
}

function groupLabelsForCard(card) {
  return WORKFLOW_DATA.traceabilityGroups
    .filter((group) => card.specReferences.some((spec) => group.specCodes.includes(spec.code)))
    .map((group) => group.title);
}

function openDrawer(cardId) {
  const card = cardsById[cardId];
  if (!card) return;
  els.drawerLabel.textContent = `${card.label} · ${card.priority} · ${card.type}`;
  els.drawerTitle.textContent = card.title;
  els.drawerContent.innerHTML = renderDrawer(card);
  els.drawer.classList.add('open');
  els.drawerBackdrop.classList.add('open');
  els.drawer.setAttribute('aria-hidden', 'false');
}

function renderDrawer(card) {
  const groups = groupLabelsForCard(card);
  const specs = card.specReferences.length ? card.specReferences.map((spec) => `
    <details class="spec-detail">
      <summary><strong>${escapeHtml(spec.code)}</strong> ${escapeHtml(spec.title || '')}</summary>
      ${spec.excerpt ? `<p>${escapeHtml(spec.excerpt)}</p>` : '<p>No parsed excerpt.</p>'}
      ${spec.rawHref ? `<a href="${escapeHtml(spec.rawHref)}">Open full SPEC</a>` : ''}
    </details>`).join('') : '<p class="muted">No SPEC reference.</p>';
  const checks = card.acceptanceItems.length ? `<ul class="checks">${card.acceptanceItems.map((item) => `<li class="${item.done ? 'done' : ''}">${item.done ? '✓' : '□'} ${escapeHtml(item.text)}</li>`).join('')}</ul>` : '<p class="muted">No acceptance criteria.</p>';
  const blockers = card.blockedReasons.length ? `<ul>${card.blockedReasons.map((reason) => `<li>${escapeHtml(reason.label)} ${escapeHtml(reason.title)}${reason.missing ? ' <strong class="danger">missing</strong>' : ''}</li>`).join('')}</ul>` : '<p class="muted">No blockers.</p>';
  const evidence = card.verificationFiles.length ? `<ul>${card.verificationFiles.map((file) => `<li><a href="${escapeHtml(file.href)}">${escapeHtml(file.file)}</a></li>`).join('')}</ul>` : '<p class="muted">No verification file linked.</p>';
  return `<section class="drawer-action"><h3>Action</h3><pre>${escapeHtml(card.suggestedCommand)}</pre></section>
    <section><h3>Summary</h3><p>${escapeHtml(card.descriptionExcerpt || 'No description.')}</p><p class="muted">Groups: ${escapeHtml(groups.join(', ') || 'None')}</p></section>
    <section><h3>Acceptance Criteria</h3>${checks}</section>
    <section><h3>Dependencies</h3><p>${escapeHtml(card.dependencyLabels.join(', ') || 'None')}</p>${blockers}</section>
    <section><h3>SPEC Traceability</h3>${specs}</section>
    <section><h3>Verification Evidence</h3><p><span class="verification ${escapeHtml(card.verification)}">${escapeHtml(card.verification)}</span></p>${evidence}</section>
    ${card.output ? `<section><h3>Output</h3><pre>${escapeHtml(card.output)}</pre></section>` : ''}
    <section><h3>Raw Markdown</h3><a href="${escapeHtml(card.rawHref)}">Open issue file</a></section>`;
}

function closeDrawer() {
  els.drawer.classList.remove('open');
  els.drawerBackdrop.classList.remove('open');
  els.drawer.setAttribute('aria-hidden', 'true');
}

document.querySelector('#closeDrawer').addEventListener('click', closeDrawer);
els.drawerBackdrop.addEventListener('click', closeDrawer);
els.search.addEventListener('input', () => { state.query = els.search.value; render(); });
els.view.addEventListener('change', () => { state.view = els.view.value; render(); });
els.theme.addEventListener('change', () => { state.theme = els.theme.value; render(); });
els.priority.addEventListener('change', () => { state.priority = els.priority.value; render(); });
els.type.addEventListener('change', () => { state.type = els.type.value; render(); });
els.verification.addEventListener('change', () => { state.verification = els.verification.value; render(); });
els.hideDone.addEventListener('change', () => { state.hideDone = els.hideDone.checked; render(); });

fillFilters();
render();
"""


STYLE = '''
:root {
  color-scheme: light;
  --bg: #f6f8fa;
  --panel: #ffffff;
  --panel-soft: #f6f8fa;
  --panel-hover: #fbfbfc;
  --text: #24292f;
  --muted: #57606a;
  --border: #d0d7de;
  --soft-border: #eaeef2;
  --blue: #0969da;
  --red: #cf222e;
  --green: #1a7f37;
  --amber: #9a6700;
  --purple: #8250df;
  --shadow: rgba(31, 35, 40, 0.16);
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0d1117;
  --panel: #161b22;
  --panel-soft: #21262d;
  --panel-hover: #1f2630;
  --text: #e6edf3;
  --muted: #8b949e;
  --border: #30363d;
  --soft-border: #262c36;
  --blue: #58a6ff;
  --red: #ff7b72;
  --green: #7ee787;
  --amber: #d29922;
  --purple: #bc8cff;
  --shadow: rgba(0, 0, 0, 0.35);
}
:root[data-theme="github"] {
  --bg: #f6f8fa;
  --panel: #ffffff;
  --panel-soft: #f6f8fa;
  --panel-hover: #f3f4f6;
  --text: #24292f;
  --muted: #57606a;
  --border: #d0d7de;
  --soft-border: #eaeef2;
  --blue: #0969da;
  --red: #cf222e;
  --green: #1a7f37;
  --amber: #9a6700;
  --purple: #8250df;
  --shadow: rgba(31, 35, 40, 0.16);
}
:root[data-theme="nord"] {
  --bg: #eceff4;
  --panel: #f8fafc;
  --panel-soft: #e5e9f0;
  --panel-hover: #edf2f7;
  --text: #2e3440;
  --muted: #5e6b7f;
  --border: #c8d1df;
  --soft-border: #d8dee9;
  --blue: #5e81ac;
  --red: #bf616a;
  --green: #689d6a;
  --amber: #b48ead;
  --purple: #81a1c1;
  --shadow: rgba(46, 52, 64, 0.14);
}
:root[data-theme="solarized"] {
  --bg: #fdf6e3;
  --panel: #fffaf0;
  --panel-soft: #eee8d5;
  --panel-hover: #f7f0da;
  --text: #586e75;
  --muted: #839496;
  --border: #d8cfb4;
  --soft-border: #eee8d5;
  --blue: #268bd2;
  --red: #dc322f;
  --green: #859900;
  --amber: #b58900;
  --purple: #6c71c4;
  --shadow: rgba(101, 83, 32, 0.14);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 14px;
}
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  padding: 16px 24px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}
.eyebrow { margin: 0 0 4px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; font-size: 11px; font-weight: 700; }
h1 { margin: 0 0 4px; font-size: 22px; font-weight: 650; }
.meta, .muted { color: var(--muted); font-size: 12px; }
.theme-control {
  display: grid;
  gap: 4px;
  min-width: 160px;
  color: var(--muted);
  font-size: 12px;
  justify-self: end;
}
.theme-control select {
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  color: var(--text);
  padding: 6px 8px;
}
pre {
  border: 1px solid var(--border);
  background: var(--panel-soft);
  border-radius: 6px;
  padding: 7px 9px;
  color: var(--text);
  overflow: auto;
}
button, select, input { font: inherit; }
button { cursor: pointer; }
.icon-button {
  border: 1px solid var(--border);
  background: var(--panel-soft);
  color: var(--text);
  border-radius: 6px;
  padding: 7px 10px;
}
.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1px;
  margin: 16px 24px 0;
  border: 1px solid var(--border);
  background: var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.metric { background: var(--panel); padding: 12px 14px; }
.metric strong { display: block; font-size: 20px; line-height: 1; }
.metric span { color: var(--muted); font-size: 12px; }
.toolbar {
  margin: 12px 24px;
  padding: 10px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  display: grid;
  grid-template-columns: minmax(220px, 1.2fr) repeat(4, minmax(130px, 1fr)) auto;
  gap: 8px;
  align-items: end;
}
.toolbar label { display: grid; gap: 4px; color: var(--muted); font-size: 12px; }
.toolbar input, .toolbar select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  color: var(--text);
  padding: 6px 8px;
}
.toolbar .check { display: flex; align-items: center; color: var(--text); padding-bottom: 6px; }
.toolbar .check input { width: auto; }
.layout { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 12px; padding: 0 24px 24px; }
.navigator {
  align-self: start;
  position: sticky;
  top: 12px;
  display: grid;
  gap: 12px;
}
.navigator section, .column {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.navigator h2, .column h2 {
  margin: 0;
  padding: 10px 12px;
  border-bottom: 1px solid var(--soft-border);
  font-size: 13px;
  font-weight: 650;
}
.nav-list { display: grid; gap: 1px; background: var(--soft-border); }
.nav-item {
  appearance: none;
  border: 0;
  background: var(--panel);
  color: var(--text);
  padding: 9px 12px;
  text-align: left;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 8px;
}
.nav-item:hover, .nav-item.active { background: var(--panel-soft); }
.nav-item.active { box-shadow: inset 3px 0 var(--blue); }
.nav-item strong { font-size: 12px; color: var(--muted); }
.nav-item small { grid-column: 1 / -1; color: var(--muted); font-size: 11px; }
.board { display: grid; gap: 12px; overflow-x: auto; align-items: start; }
.column { min-height: 360px; }
.column h2 { display: flex; justify-content: space-between; align-items: center; }
.column h2 span { color: var(--muted); font-size: 12px; }
.card {
  width: calc(100% - 16px);
  margin: 8px;
  appearance: none;
  display: block;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  color: inherit;
  text-align: left;
  padding: 10px;
}
.card:hover { border-color: #8c959f; background: var(--panel-hover); }
.card.is-blocked { border-left: 3px solid var(--red); }
.card-meta { display: flex; gap: 6px; flex-wrap: wrap; color: var(--muted); font-size: 11px; }
.priority, .verification {
  border-radius: 999px;
  padding: 1px 6px;
  background: var(--panel-soft);
  border: 1px solid var(--border);
  color: var(--muted);
}
.priority.high { color: var(--red); border-color: #ffebe9; background: #fff1f0; }
.priority.medium { color: var(--amber); border-color: #fff8c5; background: #fff8c5; }
.priority.low { color: var(--muted); }
.verification.passed { color: var(--green); border-color: #dafbe1; background: #dafbe1; }
.verification.missing, .verification.failed { color: var(--red); border-color: #ffebe9; background: #fff1f0; }
.verification.pending { color: var(--blue); border-color: #ddf4ff; background: #ddf4ff; }
.card-title { margin: 7px 0 5px; font-weight: 650; line-height: 1.35; }
.card-spec, .card-foot, .blocked-line { color: var(--muted); font-size: 12px; line-height: 1.45; }
.card-progress { height: 4px; background: #eaeef2; border-radius: 999px; overflow: hidden; margin: 8px 0; }
.card-progress span { display: block; height: 100%; background: var(--blue); }
.card-foot { display: flex; justify-content: space-between; gap: 8px; }
.blocked-line { margin-top: 6px; color: var(--red); }
.empty { color: var(--muted); font-size: 12px; padding: 12px; }
.drawer-backdrop { position: fixed; inset: 0; background: rgba(31, 35, 40, 0.25); opacity: 0; pointer-events: none; transition: opacity 0.16s ease; }
.drawer-backdrop.open { opacity: 1; pointer-events: auto; }
.drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: min(700px, 92vw);
  height: 100vh;
  background: var(--panel);
  border-left: 1px solid var(--border);
  box-shadow: -16px 0 32px var(--shadow);
  transform: translateX(104%);
  transition: transform 0.18s ease;
  z-index: 2;
  display: flex;
  flex-direction: column;
}
.drawer.open { transform: translateX(0); }
.drawer-head { padding: 14px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; gap: 16px; }
.drawer-label { color: var(--muted); font-size: 12px; margin-bottom: 4px; }
.drawer h2 { margin: 0; font-size: 18px; }
.icon-button { width: 32px; height: 32px; padding: 0; font-size: 22px; line-height: 1; }
.drawer-content { padding: 14px 16px 28px; overflow: auto; }
.drawer-content section { border-bottom: 1px solid var(--soft-border); padding-bottom: 14px; margin-bottom: 14px; }
.drawer-content h3 { margin: 0 0 8px; font-size: 13px; }
.drawer-action { background: var(--panel-soft); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
.checks { padding-left: 0; list-style: none; display: grid; gap: 6px; }
.checks li.done { color: var(--green); }
.spec-detail { border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; background: var(--panel); }
.spec-detail summary { cursor: pointer; }
.danger { color: var(--red); }
pre { white-space: pre-wrap; word-break: break-word; }
@media (max-width: 1180px) {
  .toolbar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .layout { grid-template-columns: 1fr; }
  .navigator { position: static; }
}
'''



if __name__ == '__main__':
    sys.exit(main())
