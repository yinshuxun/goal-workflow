---
name: workflow-init
description: "Initialize or migrate a goal-workflow workspace. Use when starting long-running work, adopting .workflow as the artifact root, or consolidating PRD, SPEC, issues, progress, verification, and notes. Triggers on: workflow-init, 初始化工作流, 初始化.workflow, migrate workflow."
user-invocable: true
---

# workflow-init — Initialize Workflow Workspace

Create or update a `.workflow/` workspace so goal-workflow artifacts have one durable home. This skill does not implement product code.

---

## The Job

1. **Locate Workflow Root** — choose `.workflow/` by default or accept a custom directory.
2. **Create Workflow Structure** — create missing folders and starter files without overwriting existing content.
3. **Migration** — if legacy `tasks/` or `docs/` artifacts exist, offer copy/link/skip options.
4. **Review** — show what will be created or migrated and wait for confirmation.
5. **Output** — print created files and next commands.

---

## Step 1: Locate Workflow Root

If the user did not specify a root, ask:

```
Where should I initialize the workflow?

A. .workflow/ (recommended)
B. tasks/ (legacy-compatible)
C. Custom path
```

Rules:

- Default to `.workflow/` for new work.
- Support `--dir <path>` or explicit user paths.
- If `.workflow/config.json` already exists, read it and update only missing files.
- Never replace an existing config without user confirmation.

---

## Step 2: Create Workflow Structure

Create these directories when missing:

```text
.workflow/
├── README.md
├── config.json
├── index.md
├── prds/
├── specs/
├── issues/
├── progress/
├── verification/
├── notes/
├── decisions/
├── status/
└── archive/
```

Starter `config.json`:

```json
{
  "version": 1,
  "name": "workflow",
  "root": ".workflow",
  "paths": {
    "prds": "prds",
    "specs": "specs",
    "issues": "issues",
    "progress": "progress",
    "verification": "verification",
    "notes": "notes",
    "decisions": "decisions",
    "status": "status",
    "archive": "archive"
  },
  "verification": {
    "requiredBeforeDone": true
  }
}
```

Starter `index.md` should link to PRD, SPEC, issues, progress, verification, status, notes, decisions, and archive directories.

---

## Step 3: Migration

When legacy artifacts exist, present options:

```
Found existing artifacts:
- tasks/prd-*.md
- tasks/spec-*.md
- tasks/issues/*.md
- docs/**

How should I handle them?

A. Copy into .workflow/ and keep originals (recommended)
B. Move into .workflow/
C. Link from .workflow/index.md only
D. Skip migration
```

Mapping:

| Source | Destination |
|---|---|
| `tasks/prd-*.md` | `.workflow/prds/` |
| `tasks/spec-*.md` | `.workflow/specs/` |
| `tasks/issues/*.md` | `.workflow/issues/` |
| durable progress docs | `.workflow/progress/` |
| verification or batch docs | `.workflow/verification/` |
| implementation notes | `.workflow/notes/` |
| durable decisions | `.workflow/decisions/` |

Prefer copy over move unless the user explicitly requests moving files.

---

## Output

After initialization, print:

```text
✅ Workflow initialized at .workflow/

Created or updated:
- .workflow/config.json
- .workflow/index.md
- .workflow/prds/
- .workflow/specs/
- .workflow/issues/
- .workflow/progress/
- .workflow/verification/
- .workflow/status/

Next steps:
  /prd              → create PRD
  /prd-to-spec      → create SPEC
  /to-issues        → create issues
  /workflow-status  → view status board
```

---

## Edge Cases

| Scenario | Handling |
|---|---|
| `.workflow/` already exists | Update missing files only; do not overwrite content |
| `config.json` exists | Read and merge missing keys |
| User chooses custom directory | Use it and record the path in config |
| Legacy files conflict with destination | Ask whether to skip, overwrite, or create a renamed copy |
| No legacy artifacts exist | Create a fresh workspace |
| User asks to delete legacy files | Confirm explicitly before deleting |

---

## Relationship to Other Skills

```text
/workflow-init → /prd → /prd-to-spec → /to-issues → /workflow-status → /goal
```

- **/workflow-init** creates the artifact root.
- **/prd** should save PRDs under `.workflow/prds/` when config exists.
- **/prd-to-spec** should save SPECs under `.workflow/specs/` when config exists.
- **/to-issues** should save local issues under `.workflow/issues/` when config exists.
- **/workflow-status** reads the workspace created by this skill.
