---
name: verify-it
description: "Use when fresh verification evidence is needed for a goal-workflow issue after implementation, tests, coverage, manual checks, or before marking an issue complete. Triggers on: verify-it, verification, 验证记录, 测试证据, coverage evidence."
user-invocable: true
---

# verify-it — Capture Fresh Verification

Record fresh verification evidence for an issue so completion claims are backed by commands, results, coverage, or manual checks.

---

## The Job

1. **Identify Issue** — determine the issue from user input, current goal, branch, or prompt.
2. **Capture Fresh Verification** — run or record current test, coverage, build, lint, or manual verification evidence.
3. **Save Verification Record** — write a dated Markdown file under `.workflow/verification/`.
4. **Completion Decision** — decide whether the issue can be marked complete based on evidence.
5. **Update Links** — link verification from issue or progress when appropriate.

---

## Step 1: Identify Issue

Supported inputs:

```text
/verify-it issue-003
/verify-it .workflow/issues/issue-003-current-p1-secret-batch.md
/verify-it --command "npx nx test workload-ui-shared --coverage --runInBand"
/verify-it --manual
```

Issue resolution order:

1. User-provided issue ID or file path.
2. Current `/goal` target if available.
3. Current branch name such as `feat/issue-003-*`.
4. Ask the user to choose from `.workflow/issues/`.

---

## Step 2: Capture Fresh Verification

Fresh means evidence from this run, not old logs or inferred results.

Verification may include:

| Type | Evidence |
|---|---|
| Test | command, exit code, test suites, tests |
| Coverage | statements, branches, functions, lines |
| Build | command and exit code |
| Lint/typecheck | command and exit code |
| Manual | exact scenario, observed result, screenshots if applicable |
| Review | review command and accepted findings status |

For coverage, record all four metrics when available:

```text
statements
branches
functions
lines
```

For test output, record:

```text
test suites
test cases
exit code
```

Do not use old `coverage-summary.json`, pasted historical logs, or memory as current completion evidence unless marked as historical.

---

## Step 3: Save Verification Record

Save to:

```text
.workflow/verification/YYYY-MM-DD-issue-003-current-p1-secret-batch.md
```

If no issue is known, save to:

```text
.workflow/verification/YYYY-MM-DD-verification.md
```

---

## Verification Structure

```markdown
# Verification: issue-003-current-p1-secret-batch

## Scope

- Issue: `.workflow/issues/issue-003-current-p1-secret-batch.md`
- Date: 2026-05-28
- Verification type: test / coverage / build / manual / mixed

## Commands

| Command | Exit Code | Result |
|---|---:|---|
| `npx nx test ...` | 0 | passed |

## Test Results

| Metric | Result |
|---|---|
| Test suites | 3 passed / 3 total |
| Tests | 17 passed / 17 total |

## Coverage

| Metric | Result |
|---|---:|
| Statements | 100% |
| Branches | 100% |
| Functions | 100% |
| Lines | 100% |

## Manual Checks

- None.

## Known Gaps

- `workload-ui-shared` full coverage exit code is 1.

## Completion Decision

- Issue complete: yes
- Full gate complete: no
- Reason: focused targets reached 100%, but module full coverage remains below threshold.
```

---

## Step 4: Completion Decision

Rules:

- If a command exits non-zero, the verification record may be saved, but completion is `no` unless the failure is the expected baseline being documented.
- If the issue requires coverage and any of statements, branches, functions, or lines is missing, completion is `no`.
- If the issue is documentation-only, manual verification may be enough, but the record must say why.
- If the evidence is historical, completion is `no` for fresh verification.
- If verification passes, the issue checklist may be marked complete only when all acceptance criteria are satisfied.

---

## Output

After saving:

```text
✅ Verification saved to .workflow/verification/2026-05-28-issue-003-current-p1-secret-batch.md

Result:
- tests: 17/17 passed
- coverage: statements 100%, branches 100%, functions 100%, lines 100%
- completion decision: issue complete, full gate not complete

Next:
  /progress-it issue-003
  /workflow-status
```

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Command failed | Save failed verification and do not mark issue complete |
| User provides old output | Save as historical reference, not fresh evidence |
| No issue found | Ask user to select issue or save generic verification |
| Coverage metrics incomplete | Mark completion decision as no |
| Manual-only verification | Require concrete scenario and observed result |
| Verification file exists | Append a new run section or create a new timestamped file |
| User asks to skip verification | Warn that completion cannot be trusted |

---

## Relationship to Other Skills

```text
/goal → /verify-it → /progress-it → /workflow-status → /review-it → /ship-it
```

- **/goal** implements an issue.
- **/verify-it** records fresh proof that the implementation satisfies acceptance criteria.
- **/workflow-status** surfaces missing or failed verification on the board.
- **/resume-it** uses verification records to distinguish trusted completion from stale claims.
