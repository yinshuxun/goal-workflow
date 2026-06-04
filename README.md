# goal-workflow

English | [简体中文](./README_CN.md)

An AI-driven development workflow — from PRD to shipped code, all within Claude Code.

```
/prd  →  /prd-to-spec (optional)  →  /to-issues  →  /goal  →  /review-it  →  /ship-it
```

<p align="center">
  <img src="docs/workflow.png" alt="Goal Workflow Infographic" width="800">
</p>

## Installation

```bash
npx skills add yinshuxun/goal-workflow
```

## Skills

| Command | Description |
|---------|-------------|
| `/workflow-init` | Initialize the unified `.workflow/` artifact workspace |
| `/prd` | Generate PRD (requirements document) |
| `/prd-to-spec` | Transform PRD into technical SPEC (optional) |
| `/to-issues` | Decompose PRD/SPEC into Issues and create tickets |
| `/workflow-status` | Serve the interactive workflow dashboard locally, open it in the default browser, and watch `.workflow/` for rebuilds by default; use `--shell` for terminal output |
| `/goal` | Implement an Issue end-to-end (Claude Code built-in) |
| `/verify-it` | Capture fresh verification evidence for an Issue |
| `/progress-it` | Update durable progress, history, and workflow index records |
| `/resume-it` | Restore context and pick the next action for long-running work |
| `/review-it` | Automated code review with iterative fixes |
| `/ship-it` | Commit, PR, merge, and close the Issue |
| `/note-it` | Capture implementation notes per Issue |
| `/humanize-it` | Remove AI traces from documents |
| `/listenhub-tts` | Text-to-speech via ListenHub |
| `/insight-diagram` | Generate UML and architecture diagrams |
| `/code-to-spec` | Reverse-engineer SPEC from existing projects |
| `/refactor` | Expert code refactoring (Fowler catalog) |
| `/modern-go` | Modernize Go code (35+ gofix-style rules) |
| `/smell` | Detect architecture anti-patterns, code smells, and complexity hotspots |

## Documentation

Full usage guide: [docs/index.html](docs/index.html)

The `docs/` directory is a static documentation site suitable for GitHub Pages. Use `docs/` as the Pages source and `docs/index.html` as the entry point; it redirects readers to the Chinese or English guide.

`docs/workflow.png` is the shared README and Pages infographic. It does not need to be regenerated unless the top-level lifecycle changes; command details belong in the HTML guides.

## License

MIT