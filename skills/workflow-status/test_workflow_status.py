import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name('workflow-status.py')
spec = importlib.util.spec_from_file_location('workflow_status', MODULE_PATH)
workflow_status = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(workflow_status)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class WorkflowStatusTest(unittest.TestCase):
    def test_build_data_groups_issues_by_prd(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / '.workflow'
            write(root / 'config.json', '{"name":"demo"}')
            write(root / 'prds' / 'prd-alpha.md', '# Alpha PRD\n')
            write(root / 'prds' / 'prd-beta.md', '# Beta PRD\n')
            write(
                root / 'specs' / 'spec-alpha.md',
                '# Alpha SPEC\n\n> Technical specification derived from: `.workflow/prds/prd-alpha.md`\n\n## 1. Summary\n\n### 1.1 Alpha Scope\n\nAlpha summary.\n\n### 2.2 Shared Runtime\n\nAlpha shared section.\n\n### 3.3 Alpha Unique\n\nAlpha unique section.\n',
            )
            write(
                root / 'specs' / 'spec-beta.md',
                '# Beta SPEC\n\n> Technical specification derived from: `.workflow/prds/prd-beta.md`\n\n## 1. Summary\n\n### 1.1 Beta Scope\n\nBeta summary.\n\n### 2.2 Shared Runtime\n\nBeta shared section.\n',
            )
            write(
                root / 'issues' / 'issue-001-alpha.md',
                '# Alpha issue\n\n## Description\n\nAlpha work.\n\n## Acceptance Criteria\n\n- [ ] alpha todo\n\n## Dependencies\n\nNone\n\n## Type\n\nfeature\n\n## Priority\n\nhigh\n\n## SPEC Reference\n\nSection 3.3\n',
            )
            write(
                root / 'issues' / 'issue-002-beta.md',
                '# Beta issue\n\n## Description\n\nBeta work.\n\n## Acceptance Criteria\n\n- [ ] beta todo\n\n## Dependencies\n\nNone\n\n## Type\n\ntest\n\n## Priority\n\nmedium\n\n## SPEC Reference\n\n`.workflow/specs/spec-beta.md` sections 1.1\n',
            )
            write(
                root / 'issues' / 'issue-003-alpha-dependent.md',
                '# Alpha dependent issue\n\n## Description\n\nAlpha follow-up.\n\n## Acceptance Criteria\n\n- [ ] alpha follow-up todo\n\n## Dependencies\n\nissue-001\n\n## Type\n\ntest\n\n## Priority\n\nmedium\n\n## SPEC Reference\n\nSection 2.2\n',
            )

            data = workflow_status.build_data(root)

        prds = {prd['id']: prd for prd in data['prds']}
        self.assertEqual(set(prds), {'prd-alpha', 'prd-beta'})
        self.assertEqual(prds['prd-alpha']['title'], 'Alpha PRD')
        self.assertEqual(prds['prd-alpha']['summary']['total'], 2)
        self.assertEqual(prds['prd-alpha']['specFiles'], ['spec-alpha.md'])
        alpha_ids = [card['id'] for column in prds['prd-alpha']['views']['focus'] for card in column['cards']]
        self.assertEqual(alpha_ids, ['issue-003', 'issue-001'])
        self.assertEqual(prds['prd-beta']['summary']['total'], 1)
        beta_issue = prds['prd-beta']['views']['focus'][1]['cards'][0]
        self.assertEqual(beta_issue['id'], 'issue-002')
        self.assertEqual(beta_issue['specReferences'][0]['file'], 'spec-beta.md')
        self.assertEqual(beta_issue['specReferences'][0]['title'], 'Beta Scope')
        self.assertEqual(data['selectedPrdId'], 'prd-alpha')

    def test_render_html_keeps_prd_switcher_without_filters_or_navigation(self) -> None:
        data = {
            'workflow': 'demo',
            'updatedAt': '2026-06-29T12:00:00+08:00',
            'summary': {'total': 0, 'blocked': 0, 'ready': 0, 'inProgress': 0, 'review': 0, 'done': 0},
        }

        html = workflow_status.render_html(data)

        self.assertIn('id="prdSwitcher"', html)
        self.assertNotIn('id="searchInput"', html)
        self.assertNotIn('Workflow filters', html)
        self.assertNotIn('Workflow navigation', html)
        self.assertNotIn('id="executionNav"', html)


if __name__ == '__main__':
    unittest.main()
