#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

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
      '## Step 3: Terminal Output',
      '## Step 4: HTML Output',
      '## Step 5: Watch Mode',
      '## Edge Cases',
      '--html --watch',
      '.workflow/status/data.json',
      '.workflow/status/index.html',
      'Todo',
      'In Progress',
      'Blocked',
      'Done',
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
