---
name: workflow-status
description: "View or serve a goal-workflow dashboard. Use when inspecting .workflow issues, priorities, dependencies, current work, completion, verification state, SPEC traceability, or opening the local workflow dashboard. Triggers on: workflow-status, workflow dashboard, kanban, 状态看板, 工作流状态."
user-invocable: true
---

# workflow-status — Workflow Status Dashboard

Aggregate `.workflow/` artifacts into an interactive HTML dashboard with watch mode enabled by default. Use `--shell` when a compact terminal board is needed.

Use `workflow-status.py` in this skill directory for terminal, HTML, and watch mode generation instead of reimplementing parsing logic inline.

---

## The Job

1. **Locate Workflow Root** — default to `.workflow/`, or use `--dir <path>`.
2. **Build Board Data** — parse issues, dependencies, progress, specs, notes, and verification records.
3. **HTML Dashboard** — default output writes `.workflow/status/index.html`, `.workflow/status/data.json`, `.workflow/status/markdown.html`, `.workflow/status/markdown-data.json`, `.workflow/status/style.css`, and `.workflow/status/app.js`, serves `.workflow/` locally, and opens `/status/index.html` in the default browser.
4. **Terminal Output** — with `--shell`, print a compact issue board and next action.
5. **Watch Mode** — enabled by default for HTML mode; use `--no-watch` to serve without rebuilding when workflow files change.

---

## Step 1: Locate Workflow Root

Search order:

1. `--dir <path>` if provided.
2. `.workflow/config.json` in current directory.
3. Nearest `.workflow/` in the project tree.
4. Legacy `tasks/` only as a fallback.

If no workflow root exists, suggest:

```text
No .workflow workspace found. Run /workflow-init first.
```

---

## Step 2: Build Board Data

When running inside Claude Code, prefer:

```bash
python3 <skill-dir>/workflow-status.py [--dir <path>]
```

Use shell mode only when the user explicitly wants terminal output:

```bash
python3 <skill-dir>/workflow-status.py [--dir <path>] --shell
```

Read:

```text
.workflow/config.json
.workflow/issues/*.md
.workflow/specs/*.md
.workflow/progress/current.md
.workflow/verification/*.md
.workflow/notes/*
```

Parse each issue from frontmatter when available, otherwise from Markdown sections:

| Field | Source |
|---|---|
| ID | frontmatter `id` or filename |
| Title | frontmatter `title` or H1 |
| Description | `## Description` |
| Priority | frontmatter `priority` or `## Priority` |
| Type | frontmatter `type` or `## Type` |
| Dependencies | frontmatter `depends_on` or `## Dependencies` |
| SPEC reference | `## SPEC Reference` |
| Checklist | `## Acceptance Criteria` checklist |
| Output | `## Output` |
| Verification | exact matching `.workflow/verification/issue-id*.md` |

Important parsing rules:

- Preserve letter-suffixed issue IDs such as `issue-007a` and `issue-011a`.
- Normalize dependency references:
  - `#11`, `#011`, `issue-011` → `issue-011`
  - `#011a`, `issue-011a` → `issue-011a`
- Deduplicate dependencies and blockers.
- Verification matching must be exact by issue token. `issue-011-*.md` must not match `issue-011a`.

Status rules:

| Column | Rule |
|---|---|
| `Done` | all acceptance criteria are checked |
| `In Progress` | frontmatter `status: in_progress` or current progress points to the issue |
| `Blocked` | dependencies are missing or incomplete |
| `Review` | done but review/ship is pending when that signal exists |
| `Todo` | dependency-free incomplete issue |

Verification states:

| State | Rule |
|---|---|
| `passed` | latest verification says completion decision is yes or passed |
| `failed` | latest verification command failed or says incomplete |
| `missing` | issue is done or verification-required but no verification exists |
| `not-required` | incomplete issue without verification yet, or documentation-only work |
| `pending` | current issue has verification work in progress |

---

## Step 3: HTML Dashboard

Default command:

```text
/workflow-status
```

Equivalent script call:

```bash
python3 <skill-dir>/workflow-status.py
```

Default behavior:

- Generate dashboard files.
- Serve the workflow root locally, defaulting to `127.0.0.1:8766` and trying the next available port when occupied.
- Open `http://127.0.0.1:<port>/status/index.html` in the default browser.
- Watch `.workflow/` and rebuild the dashboard when workflow files change.
- Keep the local server running until interrupted.

Useful options:

```bash
python3 <skill-dir>/workflow-status.py --no-open
python3 <skill-dir>/workflow-status.py --no-watch
python3 <skill-dir>/workflow-status.py --no-serve
python3 <skill-dir>/workflow-status.py --port 8766
```

Write generated files:

```text
.workflow/status/index.html
.workflow/status/data.json
.workflow/status/markdown.html
.workflow/status/markdown-data.json
.workflow/status/style.css
.workflow/status/app.js
```

Dashboard behavior:

- Render a workflow cockpit optimized for execution decisions, not a decorative AI dashboard.
- Default board uses one execution-focused view ordered as `Blocked`, `Todo`, `In Progress`, `Review`, `Done`.
- Top bar shows workflow identity and a right-aligned persisted theme selector with Default, Dark, GitHub, Nord, and Solarized styles.
- Cards open an in-page detail drawer instead of navigating away to raw markdown.
- Drawer is action-first: Action, Summary, Acceptance Criteria, Dependencies, SPEC Traceability, Verification Evidence, Output, and UTF-8 markdown viewer fallback.
- Drawer Action shows the recommended executable `/goal` command for the selected issue.
- Provide filters for search, priority, type, verification, and a persisted column selector; all five columns are selected by default and users can hide any column.
- Parse SPEC section headings from `.workflow/specs/*.md`, but do not show the full SPEC section list as the primary navigation.
- Workflow Navigation groups workflow state into Execution, Traceability, and Health.
- Traceability groups aggregate related SPEC sections into route-map categories such as Runtime / Shell, Deployment Migration, Validation & Evidence, Platform Evolution, and UI Foundation.
- Use an engineering console style: neutral background, compact cards, low decoration, and color only for meaningful states.

`data.json` shape includes summary, health, recommended next, view-specific columns, traceability groups, issue detail fields, verification files, and SPEC section metadata:

```json
{
  "workflow": "workflow-name",
  "updatedAt": "2026-05-31T12:00:00+08:00",
  "summary": {
    "total": 30,
    "ready": 6,
    "blocked": 8,
    "done": 16,
    "verificationMissing": 0
  },
  "health": {
    "blocked": 8,
    "ready": 6,
    "verificationMissing": 0,
    "missingDependencies": 0
  },
  "recommendedNext": {
    "id": "issue-011b",
    "suggestedCommand": "/goal .workflow/issues/issue-011b-deployment-create-form.md"
  },
  "views": {
    "focus": [
      { "id": "blocked", "title": "Blocked", "cards": [] },
      { "id": "todo", "title": "Todo", "cards": [] },
      { "id": "inProgress", "title": "In Progress", "cards": [] },
      { "id": "review", "title": "Review", "cards": [] },
      { "id": "done", "title": "Done", "cards": [] }
    ]
  },
  "traceabilityGroups": [],
  "specSections": []
}
```

---

## Step 4: Terminal Output

Command:

```text
/workflow-status --shell
```

Output format:

```text
Workflow: testing-coverage-governance
Root: .workflow/
Updated: 2026-05-28 14:32

Summary:
- Issues: 8 total / 4 done / 1 in progress / 3 todo
- Ready: 2
- Blocked: 0
- Verification missing: 2
- Next issue: issue-005-unreachable-branch-rules.md

Todo
  [high][infra] issue-005 固化不可达分支处理规则
    acceptance: 0/6; depends: issue-004; verification: missing

Suggested next step:
  /goal .workflow/issues/issue-005-unreachable-branch-rules.md
```

Always include a recommended next command when a pending issue exists.

---

## Step 5: Watch Mode

Command:

```text
/workflow-status
```

`--watch` is still accepted for explicitness. Use `--no-watch` to serve without file watching.

Behavior:

- Serve `.workflow/` locally and open the dashboard unless `--no-open` is provided.
- Rebuild `.workflow/status/index.html`, `.workflow/status/data.json`, `.workflow/status/markdown.html`, `.workflow/status/markdown-data.json`, `.workflow/status/style.css`, and `.workflow/status/app.js` when workflow files change.
- Watch these paths:
  - `.workflow/issues/`
  - `.workflow/specs/`
  - `.workflow/progress/`
  - `.workflow/verification/`
  - `.workflow/notes/`
  - `.workflow/config.json`

Print rebuild events:

```text
Serving .workflow at http://127.0.0.1:8766/status/index.html
Watching .workflow/...
[14:32:10] rebuilt .workflow/status/index.html
[14:32:25] workflow changed, rebuilt .workflow/status/index.html
```

---

## Edge Cases

| Scenario | Handling |
|---|---|
| No `.workflow/` | Suggest `/workflow-init` |
| No issues | Print empty board and suggest `/to-issues` |
| Issue lacks metadata | Parse H1 and known sections best-effort |
| Dependency refers to missing issue | Put card in `Blocked` and show warning |
| Done issue has missing verification | Show `verification: missing`; do not hide completion |
| User asks for terminal view | Use `--shell` |
| User wants generated files only | Use `--no-serve` |
| User wants server without browser launch | Use `--no-open` |
| Preferred port is occupied | Try the next available port automatically |
| Existing generated files | Overwrite only files under `.workflow/status/` |

---

## Relationship to Other Skills

```text
/workflow-init → /prd → /prd-to-spec → /to-issues → /workflow-status → /goal → /verify-it
```

- **/workflow-status** reads PRDs, SPECs, issues, progress, notes, and verification records.
- **/verify-it** improves card trust by adding verification evidence.
- **/resume-it** uses the same data to recommend the next action after time away.
