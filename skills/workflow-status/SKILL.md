---
name: workflow-status
description: "View or generate a goal-workflow status board. Use when inspecting .workflow issues, priorities, dependencies, current work, completion, verification state, or when generating an HTML board. Triggers on: workflow-status, workflow board, kanban, 状态看板, 工作流状态."
user-invocable: true
---

# workflow-status — Workflow Status Board

Aggregate `.workflow/` artifacts into a terminal status board by default. With `--html`, generate a GitHub Project-style local HTML board.

---

## The Job

1. **Locate Workflow Root** — default to `.workflow/`, or use `--dir <path>`.
2. **Build Board Data** — parse issues, dependencies, progress, notes, and verification records.
3. **Terminal Output** — print a compact issue board and next action.
4. **HTML Output** — with `--html`, write `.workflow/status/index.html` and `.workflow/status/data.json`.
5. **Watch Mode** — with `--html --watch`, rebuild the HTML board when workflow files change.

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

Read:

```text
.workflow/config.json
.workflow/issues/*.md
.workflow/progress/current.md
.workflow/verification/*.md
.workflow/notes/*
```

Parse each issue from frontmatter when available, otherwise from Markdown sections:

| Field | Source |
|---|---|
| ID | frontmatter `id` or filename |
| Title | frontmatter `title` or H1 |
| Priority | frontmatter `priority` or `## Priority` |
| Type | frontmatter `type` or `## Type` |
| Dependencies | frontmatter `depends_on` or `## Dependencies` |
| SPEC reference | `## SPEC Reference` |
| Checklist | `## Acceptance Criteria` checklist |
| Verification | matching `.workflow/verification/*issue-id*.md` |

Status rules:

| Column | Rule |
|---|---|
| `Done` | all acceptance criteria are checked |
| `In Progress` | frontmatter `status: in_progress` or current progress points to the issue |
| `Blocked` | dependencies are missing or incomplete |
| `Review` | done but review/ship is pending when that signal exists |
| `Todo` | default incomplete state |

Verification states:

| State | Rule |
|---|---|
| `passed` | latest verification says completion decision is yes or passed |
| `failed` | latest verification command failed or says incomplete |
| `missing` | issue is done or verification-required but no verification exists |
| `not-required` | documentation-only or explicitly marked not required |
| `pending` | current issue has verification work in progress |

---

## Step 3: Terminal Output

Default command:

```text
/workflow-status
```

Output format:

```text
Workflow: testing-coverage-governance
Root: .workflow/
Updated: 2026-05-28 14:32

Summary:
- Issues: 8 total / 4 done / 1 in progress / 3 todo
- Blocked: 0
- Verification missing: 2
- Next issue: issue-005-unreachable-branch-rules.md

Todo
  [high][infra] issue-005 固化不可达分支处理规则
    depends: issue-004 ✓
    verification: missing

In Progress
  [high][infra] issue-008 按新规则执行下一批 P1 focused coverage
    verification: pending

Done
  [high][infra] issue-003 回填当前 P1 Secret batch 文档
    verification: passed
```

Always include a recommended next command when a pending issue exists:

```text
Suggested next step:
  /goal .workflow/issues/issue-005-unreachable-branch-rules.md
```

---

## Step 4: HTML Output

Command:

```text
/workflow-status --html
```

Write generated files:

```text
.workflow/status/index.html
.workflow/status/data.json
.workflow/status/style.css
```

HTML board requirements:

- Render columns: `Todo`, `In Progress`, `Blocked`, `Review`, `Done`.
- Render issue cards with ID, title, priority, type, completion ratio, dependencies, and verification state.
- Use the visual style already used by goal-workflow docs: warm background, soft cards, small badges.
- Link each card to its local issue file path when possible.

`data.json` shape:

```json
{
  "workflow": "testing-coverage-governance",
  "updatedAt": "2026-05-28T14:32:00+08:00",
  "summary": {
    "total": 8,
    "todo": 3,
    "inProgress": 1,
    "blocked": 0,
    "done": 4,
    "verificationMissing": 2
  },
  "columns": [
    {
      "id": "todo",
      "title": "Todo",
      "cards": []
    }
  ]
}
```

---

## Step 5: Watch Mode

Command:

```text
/workflow-status --html --watch
```

Behavior:

- Rebuild `.workflow/status/index.html` and `.workflow/status/data.json` when workflow files change.
- First version may use polling every 5 seconds.
- Watch these paths:
  - `.workflow/issues/`
  - `.workflow/progress/`
  - `.workflow/verification/`
  - `.workflow/notes/`
  - `.workflow/config.json`

Print rebuild events:

```text
Watching .workflow/...
[14:32:10] rebuilt .workflow/status/index.html
[14:32:25] issue-005 changed, rebuilt
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
| `--watch` without `--html` | Ask to add `--html` or refresh terminal periodically |
| Existing generated files | Overwrite only files under `.workflow/status/` |

---

## Relationship to Other Skills

```text
/workflow-init → /prd → /prd-to-spec → /to-issues → /workflow-status → /goal → /verify-it
```

- **/workflow-status** reads PRDs, SPECs, issues, progress, notes, and verification records.
- **/verify-it** improves card trust by adding verification evidence.
- **/resume-it** uses the same data to recommend the next action after time away.
