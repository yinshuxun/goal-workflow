---
name: resume-it
description: "Restore context for a long-running goal-workflow project. Use when returning after time away, after context loss, or before continuing the next issue from .workflow artifacts. Triggers on: resume-it, resume workflow, 恢复上下文, 继续工作流, 下一步做什么."
user-invocable: true
---

# resume-it — Resume Workflow Context

Recover the current state of a long-running workflow from `.workflow/` artifacts and recommend the safest next action.

---

## The Job

1. **Locate Workflow Root** — find `.workflow/` or use `--dir <path>`.
2. **Read Workflow State** — inspect PRD, SPEC, issues, progress, verification, notes, and decisions.
3. **Detect Gaps** — identify stale progress, missing verification, blocked issues, and unclear next steps.
4. **Recommend Next Action** — suggest the next issue and command to continue.
5. **Output** — print a concise recovery summary.

---

## Step 1: Locate Workflow Root

Search order:

1. `--dir <path>`.
2. `.workflow/config.json` in current directory.
3. Nearest `.workflow/` parent.
4. Legacy `tasks/` only as fallback.

If multiple workflows exist, ask the user to choose:

```text
Found multiple workflows:

1. .workflow/ — testing-coverage-governance
2. ../other/.workflow/ — auth-redesign

Which workflow should I resume?
```

If none exists, suggest `/workflow-init`.

---

## Step 2: Read Workflow State

Read these files when available:

```text
.workflow/index.md
.workflow/config.json
.workflow/prds/*.md
.workflow/specs/*.md
.workflow/issues/*.md
.workflow/progress/current.md
.workflow/progress/history.md
.workflow/verification/*.md
.workflow/notes/*
.workflow/decisions/*.md
```

Summarize:

- workflow name and root;
- PRD and SPEC paths;
- issue counts by status;
- latest completed issue;
- active issue if any;
- latest verification;
- current pause point;
- known blockers;
- next eligible issue.

---

## Step 3: Detect Gaps

Check for:

| Gap | Meaning |
|---|---|
| Done issue without verification | Completion may be untrusted |
| Verification failed | Issue should not be considered complete |
| Progress stale | `current.md` disagrees with issue state |
| Blocked issue | Dependencies are incomplete |
| Missing PRD or SPEC | Workflow can continue, but context is weaker |
| No pending issues | Workflow may be ready for `/archive-it` |

Rules:

- Trust issue checklists and verification records over prose summaries.
- Treat old progress summaries as potentially stale.
- Do not claim a workflow is complete unless all issues are complete and required verification exists.

---

## Step 4: Recommend Next Action

Recommendation order:

1. Continue active `in_progress` issue.
2. Fix failed verification.
3. Add missing verification for done issue.
4. Start the first unblocked pending issue by issue number.
5. If no issues remain, suggest `/archive-it`.

Example:

```text
Recommended next step:
  /goal .workflow/issues/issue-005-unreachable-branch-rules.md
```

---

## Output

Default output:

```text
Workflow: testing-coverage-governance
Root: .workflow/

Current state:
- PRD: .workflow/prds/testing-coverage-governance.md
- SPEC: .workflow/specs/testing-coverage-governance.md
- Issues: 8 total / 4 done / 0 in progress / 4 todo
- Latest verification: .workflow/verification/2026-05-28-issue-003-current-p1-secret-batch.md

Trusted completions:
- issue-003: fresh coverage recorded
- issue-004: documentation rule update, manual verification acceptable

Warnings:
- issue-006 is pending and requires verification after completion

Recommended next step:
  /goal .workflow/issues/issue-005-unreachable-branch-rules.md
```

Keep output concise enough to read after context loss.

---

## Edge Cases

| Scenario | Handling |
|---|---|
| No `.workflow/` | Suggest `/workflow-init` |
| Multiple workflows | Ask user to choose |
| Progress conflicts with issues | Report conflict and trust issues + verification |
| Done issue has missing verification | Warn and suggest `/verify-it <issue>` |
| No pending issues | Suggest `/archive-it` |
| Active issue found | Suggest continuing that issue |
| PRD/SPEC missing | Continue from issues but warn context is incomplete |

---

## Relationship to Other Skills

```text
/resume-it → /workflow-status → /goal → /verify-it → /progress-it
```

- **/resume-it** restores context after time away.
- **/workflow-status** gives a board view of the same state.
- **/goal** continues the recommended issue.
- **/verify-it** records proof before completion claims.
