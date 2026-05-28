---
name: progress-it
description: "Use when a goal-workflow Issue needs durable progress updates after implementation, verification, notes, or status changes. Triggers on: /progress-it, update progress, 记录进展, progress ledger, workflow progress."
user-invocable: true
---

# Progress Ledger

Update the durable progress ledger for a goal-workflow Issue so long-running work can be resumed without relying on chat history.

## Triggers

Use when:
- After `/verify-it` records fresh verification for an Issue
- After implementation status changes and `.workflow/progress/` should reflect it
- Before `/workflow-status` or `/resume-it` needs an accurate long-term state
- User says "记录进展", "update progress", "progress-it", or `/progress-it`

## The Job

1. Identify the Issue and workflow root
2. Read available evidence: Issue file, verification records, notes, and current progress
3. Update `.workflow/progress/current.md`
4. Append a dated entry to `.workflow/progress/history.md`
5. Update `.workflow/index.md`
6. Report the status and Recommended next step

## Step 1: Identify Issue

Resolve the Issue from the strongest available signal:

1. Direct argument: `/progress-it issue-003` or `/progress-it .workflow/issues/issue-003-title.md`
2. Current branch name containing an Issue number
3. Last `/goal` or `/verify-it` target in conversation context
4. If ambiguous, ask the user which Issue to update

Resolve the workflow root before reading or writing:

1. Use `--dir <path>` when provided.
2. Use `.workflow/config.json` when it exists.
3. Default to `.workflow/` when present.
4. Support a custom path when the user explicitly provides one.

## Step 2: Read Evidence

Read the smallest set of files needed to make the progress update reliable:

- Issue file under `.workflow/issues/`
- Fresh verification records under `.workflow/verification/`
- Existing `.workflow/progress/current.md`
- Existing `.workflow/progress/history.md`
- Existing `.workflow/index.md`
- Implementation notes under `.workflow/notes/` when available

A verification record is fresh only when it was produced after the implementation change it supports and includes commands or manual checks with clear outcomes.

## Step 3: Update Current Progress

Create or update `.workflow/progress/current.md` as the single-page working snapshot.

Required sections:

```markdown
# Current Progress

## Active Issue

- Issue: #003 — [title]
- Status: todo | in_progress | blocked | review | done
- Priority: high | medium | low
- Updated: YYYY-MM-DD

## Evidence

- Verification: .workflow/verification/YYYY-MM-DD-issue-003-*.md
- Notes: .workflow/notes/issue#0003.html

## Current State

[1-3 bullets describing what is done, blocked, or pending]

## Recommended next step

[The next concrete action]
```

## Step 4: Append History

Append a new dated entry to `.workflow/progress/history.md` every time `/progress-it` runs.

Entry format:

```markdown
## YYYY-MM-DD — Issue #003 — [status]

- Summary: [what changed]
- Evidence: [verification or note path]
- Decision: [trusted complete / continue / blocked]
- Recommended next step: [next action]
```

Do not rewrite prior history entries unless the user explicitly asks to correct an error.

## Step 5: Update Workflow Index

Update `.workflow/index.md` so it remains the durable navigation entry point.

At minimum, keep these links current:

```markdown
# Workflow Index

## Current

- Current progress: progress/current.md
- Progress history: progress/history.md
- Status board: status/index.html

## Active Work

- Issue: issues/issue-003-title.md
- Verification: verification/YYYY-MM-DD-issue-003-*.md
- Notes: notes/issue#0003.html
```

## Completion Rules

- Do not mark an Issue as `done` unless fresh verification exists.
- If verification failed, mark the Issue as `in_progress` or `blocked` and record the failure.
- If verification is missing, write the progress update but set the decision to `continue` and recommend `/verify-it <issue>`.
- If notes are missing, completion can still proceed, but recommend `/note-it <issue>` before `/ship-it` when design rationale changed.
- Keep status conservative: stale or missing evidence is not trusted completion.

## Output

Print a compact summary:

```text
Progress updated

Issue: #003 — Current P1 Secret batch
Status: done
Evidence: .workflow/verification/2026-05-28-issue-003-current-p1-secret-batch.md
Updated:
- .workflow/progress/current.md
- .workflow/progress/history.md
- .workflow/index.md

Recommended next step: /workflow-status, then /resume-it or /review-it
```

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Issue not found | Ask for the Issue path or number |
| `.workflow/progress/` does not exist | Create it when `.workflow/config.json` exists |
| `.workflow/index.md` does not exist | Create a minimal index with current links |
| Fresh verification missing | Do not mark done; recommend `/verify-it <issue>` |
| Verification failed | Record failure and recommend fixing the Issue |
| Multiple verification records exist | Use the newest fresh verification for the same Issue |
| Notes missing | Record "None found" and recommend `/note-it` only when rationale needs capture |
| Custom workflow directory provided | Use that path consistently for progress, history, index, verification, and notes |

## Relationship to Other Skills

```text
/workflow-init → /prd → /prd-to-spec → /to-issues → /workflow-status
  → /goal → /verify-it → /progress-it → /resume-it → /review-it → /ship-it
```

- **/verify-it** records fresh verification evidence.
- **/progress-it** turns implementation and verification state into durable progress records.
- **/workflow-status** reads Issue and verification state for board output.
- **/resume-it** uses progress records to restore context and choose the Recommended next step.
- **/note-it** captures implementation rationale when design decisions, deviations, or tradeoffs need durable documentation.
