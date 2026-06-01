#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const skillsDir = path.join(root, 'skills');

const requiredSkills = [
  {
    name: 'workflow-init',
    required: [
      'user-invocable: true',
      '## The Job',
      '## Step 1: Locate Workflow Root',
      '## Step 2: Create Workflow Structure',
      '## Step 3: Migration',
      '## Output',
      '## Edge Cases',
      '## Relationship to Other Skills',
      '.workflow/config.json',
      '.workflow/prds/',
      '.workflow/specs/',
      '.workflow/issues/',
      '.workflow/verification/',
    ],
  },
  {
    name: 'workflow-status',
    required: [
      'user-invocable: true',
      '## The Job',
      '## Step 1: Locate Workflow Root',
      '## Step 2: Build Board Data',
      '## Step 3: HTML Dashboard',
      '## Step 4: Terminal Output',
      '## Step 5: Watch Mode',
      '## Edge Cases',
      '--shell',
      '.workflow/status/data.json',
      '.workflow/status/index.html',
      '.workflow/status/markdown.html',
      '.workflow/status/markdown-data.json',
      '.workflow/status/app.js',
      'Todo',
      'In Progress',
      'Blocked',
      'Done',
      'Workflow Navigation',
      'Traceability',
      'recommended executable `/goal` command',
      'SPEC Traceability',
      'verification',
    ],
  },
  {
    name: 'verify-it',
    required: [
      'user-invocable: true',
      '## The Job',
      '## Step 1: Identify Issue',
      '## Step 2: Capture Fresh Verification',
      '## Step 3: Save Verification Record',
      '## Step 4: Completion Decision',
      '## Verification Structure',
      '## Edge Cases',
      '.workflow/verification/',
      'fresh',
      'exit code',
      'test suites',
      'statements',
      'branches',
      'functions',
      'lines',
    ],
  },
  {
    name: 'resume-it',
    required: [
      'user-invocable: true',
      '## The Job',
      '## Step 1: Locate Workflow Root',
      '## Step 2: Read Workflow State',
      '## Step 3: Detect Gaps',
      '## Step 4: Recommend Next Action',
      '## Output',
      '## Edge Cases',
      '.workflow/progress/current.md',
      '.workflow/issues/',
      '.workflow/verification/',
      'Recommended next step',
    ],
  },
  {
    name: 'progress-it',
    required: [
      'user-invocable: true',
      '## The Job',
      '## Step 1: Identify Issue',
      '## Step 2: Read Evidence',
      '## Step 3: Update Current Progress',
      '## Step 4: Append History',
      '## Step 5: Update Workflow Index',
      '## Completion Rules',
      '## Output',
      '## Edge Cases',
      '.workflow/progress/current.md',
      '.workflow/progress/history.md',
      '.workflow/index.md',
      '.workflow/verification/',
      'fresh verification',
      'Recommended next step',
    ],
  },
];

const existingWorkflowSkills = [
  {
    name: 'prd',
    required: [
      '.workflow/config.json',
      '.workflow/prds/',
      '--dir <path>',
      'tasks/` only as a legacy fallback',
      'custom path',
    ],
  },
  {
    name: 'prd-to-spec',
    required: [
      '.workflow/config.json',
      '.workflow/prds/',
      '.workflow/specs/',
      '--dir <path>',
      'tasks/` only as a legacy fallback',
      'custom path',
    ],
  },
  {
    name: 'to-issues',
    required: [
      '.workflow/config.json',
      '.workflow/prds/',
      '.workflow/specs/',
      '.workflow/issues/',
      '--dir <path>',
      '.autoresearch/issues` only as a legacy fallback',
      'custom path',
    ],
  },
  {
    name: 'note-it',
    required: [
      '.workflow/config.json',
      '.workflow/notes/',
      '--dir <path>',
      'docs/` only as a legacy fallback',
      'custom path',
    ],
  },
];

const failures = [];

for (const skill of requiredSkills) {
  const file = path.join(skillsDir, skill.name, 'SKILL.md');
  if (!fs.existsSync(file)) {
    failures.push(`${skill.name}: missing ${path.relative(root, file)}`);
    continue;
  }
  const content = fs.readFileSync(file, 'utf8');
  const frontmatter = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatter) {
    failures.push(`${skill.name}: missing YAML frontmatter`);
  } else {
    if (!frontmatter[1].includes(`name: ${skill.name}`)) {
      failures.push(`${skill.name}: frontmatter name mismatch`);
    }
    if (!/description:\s*"?[^"\n]*Use when/i.test(frontmatter[1])) {
      failures.push(`${skill.name}: description must include Use when trigger`);
    }
  }
  for (const required of skill.required) {
    if (!content.includes(required)) {
      failures.push(`${skill.name}: missing required content: ${required}`);
    }
  }
}

for (const skill of existingWorkflowSkills) {
  const file = path.join(skillsDir, skill.name, 'SKILL.md');
  if (!fs.existsSync(file)) {
    failures.push(`${skill.name}: missing ${path.relative(root, file)}`);
    continue;
  }
  const content = fs.readFileSync(file, 'utf8');
  for (const required of skill.required) {
    if (!content.includes(required)) {
      failures.push(`${skill.name}: missing workflow-root behavior: ${required}`);
    }
  }
}

const readme = fs.readFileSync(path.join(root, 'README.md'), 'utf8');
const readmeCn = fs.readFileSync(path.join(root, 'README_CN.md'), 'utf8');
const docsCn = fs.readFileSync(path.join(root, 'docs', 'index_cn.html'), 'utf8');
const docsEn = fs.readFileSync(path.join(root, 'docs', 'index_en.html'), 'utf8');

for (const skill of requiredSkills) {
  if (!readme.includes(`/${skill.name}`)) {
    failures.push(`README.md: missing /${skill.name}`);
  }
  if (!readmeCn.includes(`/${skill.name}`)) {
    failures.push(`README_CN.md: missing /${skill.name}`);
  }
  if (!docsCn.includes(`/${skill.name}`)) {
    failures.push(`docs/index_cn.html: missing /${skill.name}`);
  }
  if (!docsEn.includes(`/${skill.name}`)) {
    failures.push(`docs/index_en.html: missing /${skill.name}`);
  }
}

if (!docsCn.includes('.workflow')) {
  failures.push('docs/index_cn.html: missing .workflow explanation');
}
if (!docsEn.includes('.workflow')) {
  failures.push('docs/index_en.html: missing .workflow explanation');
}

const prdReadme = fs.readFileSync(path.join(skillsDir, 'prd', 'README.md'), 'utf8');
if (!prdReadme.includes('.workflow/prds/prd-[feature-name].md')) {
  failures.push('skills/prd/README.md: missing .workflow PRD default output');
}

function writeIssue(workflowRoot, issueToken, body) {
  const token = String(issueToken);
  const padded = token.replace(/^(\d+)/, (number) => number.padStart(3, '0'));
  fs.writeFileSync(
    path.join(workflowRoot, 'issues', `issue-${padded}-fixture.md`),
    `# Fixture ${padded}\n\n${body}`
  );
}

function workflowStatusData(workflowRoot) {
  const script = path.join(skillsDir, 'workflow-status', 'workflow-status.py');
  const result = spawnSync(
    'python3',
    [
      '-c',
      `import importlib.util, json, pathlib, sys\n` +
        `spec = importlib.util.spec_from_file_location('workflow_status', sys.argv[1])\n` +
        `module = importlib.util.module_from_spec(spec)\n` +
        `spec.loader.exec_module(module)\n` +
        `print(json.dumps(module.build_data(pathlib.Path(sys.argv[2]))))\n`,
      script,
      workflowRoot,
    ],
    { encoding: 'utf8' }
  );
  if (result.status !== 0) {
    failures.push(`workflow-status: build_data fixture failed: ${result.stderr.trim()}`);
    return null;
  }
  return JSON.parse(result.stdout);
}

function cardsById(data) {
  const cards = new Map();
  for (const column of data.columns) {
    for (const card of column.cards) {
      cards.set(card.id, { ...card, columnId: column.id });
    }
  }
  return cards;
}

function validateWorkflowStatusBehavior() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'workflow-status-'));
  const workflowRoot = path.join(tmp, '.workflow');
  fs.mkdirSync(path.join(workflowRoot, 'issues'), { recursive: true });
  fs.mkdirSync(path.join(workflowRoot, 'progress'), { recursive: true });
  fs.mkdirSync(path.join(workflowRoot, 'specs'), { recursive: true });
  fs.mkdirSync(path.join(workflowRoot, 'verification'), { recursive: true });
  fs.writeFileSync(path.join(workflowRoot, 'config.json'), '{"name":"fixture"}\n');
  fs.writeFileSync(
    path.join(workflowRoot, 'specs', 'spec-fixture.md'),
    '# SPEC Fixture\n\n## 5.4 Feature Migration Logic\n\nSpec excerpt for fixture issues.\n'
  );

  writeIssue(workflowRoot, 1, '## Acceptance Criteria\n\n- [x] Done\n');
  writeIssue(workflowRoot, 2, '## Acceptance Criteria\n\n- [ ] Blocked\n\n## Dependencies\n\nIssue #999\n');
  writeIssue(workflowRoot, 3, '## Acceptance Criteria\n\n- [ ] Review\n');
  writeIssue(workflowRoot, 4, '## Acceptance Criteria\n\n- [ ] Review\n');
  writeIssue(workflowRoot, 5, '## Acceptance Criteria\n\n- [ ] Review\n');
  writeIssue(workflowRoot, 11, '## Acceptance Criteria\n\n- [x] Parent done\n\n## SPEC Reference\n\n5.4 Feature Migration Logic\n');
  writeIssue(workflowRoot, '11a', '## Acceptance Criteria\n\n- [x] Suffixed done\n\n## SPEC Reference\n\n5.4 Feature Migration Logic\n');
  writeIssue(workflowRoot, '11b', '## Acceptance Criteria\n\n- [ ] Suffixed todo\n\n## Dependencies\n\n#011a, issue-011a, #011\n\n## SPEC Reference\n\n5.4 Feature Migration Logic\n');
  fs.writeFileSync(
    path.join(workflowRoot, 'issues', 'issue-011-bug-fixture.md'),
    '# Fixture 011 Bug\n\n## Acceptance Criteria\n\n- [x] Bug follow-up\n'
  );
  fs.writeFileSync(path.join(workflowRoot, 'verification', 'issue-011-fixture.md'), 'Completion decision: passed\n');
  fs.writeFileSync(
    path.join(workflowRoot, 'progress', 'current.md'),
    '# Current Progress\n\n## Active Issue\n\n- Issue: #005\n- Status: review\n\n## Current State\n\n- Issue #001、#002、#003、#004、#005 are mentioned.\n'
  );

  const reviewData = workflowStatusData(workflowRoot);
  if (reviewData) {
    const cards = cardsById(reviewData);
    for (const number of ['003', '004', '005']) {
      if (cards.get(`issue-${number}`)?.columnId !== 'review') {
        failures.push(`workflow-status: issue-${number} should be review, got ${cards.get(`issue-${number}`)?.columnId}`);
      }
    }
    if (cards.get('issue-001')?.columnId !== 'done') {
      failures.push(`workflow-status: checked issue should remain done, got ${cards.get('issue-001')?.columnId}`);
    }
    if (cards.get('issue-002')?.columnId !== 'blocked') {
      failures.push(`workflow-status: blocked issue should remain blocked, got ${cards.get('issue-002')?.columnId}`);
    }
    const suffixedDone = cards.get('issue-011a');
    const suffixedTodo = cards.get('issue-011b');
    const keys = [...cards.values()].map((card) => card.key);
    if (new Set(keys).size !== keys.length) {
      failures.push('workflow-status: card keys should remain unique when normalized issue IDs collide');
    }
    if (suffixedDone?.label !== '#011a') {
      failures.push(`workflow-status: suffixed issue should preserve label #011a, got ${suffixedDone?.label}`);
    }
    if (suffixedDone?.verification !== 'missing') {
      failures.push(`workflow-status: issue-011 verification must not match issue-011a, got ${suffixedDone?.verification}`);
    }
    if (suffixedTodo?.dependencies.join(',') !== 'issue-011a,issue-011') {
      failures.push(`workflow-status: dependencies should preserve and dedupe suffixed IDs, got ${suffixedTodo?.dependencies.join(',')}`);
    }
    if (suffixedTodo?.blockedBy.join(',') !== '') {
      failures.push(`workflow-status: done dependencies should not block suffixed todo, got ${suffixedTodo?.blockedBy.join(',')}`);
    }
    if (suffixedDone?.specReferences[0]?.code !== '5.4') {
      failures.push(`workflow-status: SPEC reference should be parsed, got ${suffixedDone?.specReferences[0]?.code}`);
    }
    const focusOrder = reviewData.views?.focus?.map((column) => column.id).join(',');
    if (focusOrder !== 'blocked,todo,inProgress,review,done') {
      failures.push(`workflow-status: focus view order should be blocked,todo,inProgress,review,done, got ${focusOrder}`);
    }
    if ('kanban' in (reviewData.views || {})) {
      failures.push('workflow-status: kanban view should not be emitted');
    }
    if (!reviewData.recommendedNext || reviewData.recommendedNext.id !== 'issue-011b') {
      failures.push(`workflow-status: recommended next should prefer executable ready issue-011b, got ${reviewData.recommendedNext?.id}`);
    }
    if (!reviewData.traceabilityGroups?.some((group) => group.id === 'deployment-migration' && group.issueCount >= 2)) {
      failures.push('workflow-status: deployment-migration traceability group should include suffixed fixture issues');
    }
    if (typeof reviewData.health?.missingDependencies !== 'number') {
      failures.push('workflow-status: health summary should include missingDependencies');
    }
  }

  fs.writeFileSync(
    path.join(workflowRoot, 'progress', 'current.md'),
    '# Current Progress\n\n## Active Issue\n\n- Issue: #003 / #004\n- Status: in progress\n'
  );
  const inProgressData = workflowStatusData(workflowRoot);
  if (inProgressData) {
    const cards = cardsById(inProgressData);
    for (const number of ['003', '004']) {
      if (cards.get(`issue-${number}`)?.columnId !== 'inProgress') {
        failures.push(`workflow-status: active in-progress issue-${number} should be inProgress, got ${cards.get(`issue-${number}`)?.columnId}`);
      }
    }
  }
}

validateWorkflowStatusBehavior();

const docsPathExpectations = [
  [docsCn, 'docs/index_cn.html', '.workflow/prds/prd-[feature-name].md'],
  [docsCn, 'docs/index_cn.html', '.workflow/specs/spec-[feature-name].md'],
  [docsCn, 'docs/index_cn.html', '.workflow/issues/'],
  [docsCn, 'docs/index_cn.html', '.workflow/notes/issue#XXXX.html'],
  [docsEn, 'docs/index_en.html', '.workflow/prds/prd-[feature-name].md'],
  [docsEn, 'docs/index_en.html', '.workflow/specs/spec-[feature-name].md'],
  [docsEn, 'docs/index_en.html', '.workflow/issues/'],
  [docsEn, 'docs/index_en.html', '.workflow/notes/issue#XXXX.html'],
];

for (const [content, label, expected] of docsPathExpectations) {
  if (!content.includes(expected)) {
    failures.push(`${label}: missing default path ${expected}`);
  }
}

if (failures.length > 0) {
  console.error('workflow skill validation failed:');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log('workflow skill validation passed');
