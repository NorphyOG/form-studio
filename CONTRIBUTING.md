# Contributing to FORM / STUDIO

Thanks for helping make website creation accessible to more people. Bug reports, translations, documentation improvements, accessibility fixes, designs and code are welcome.

## Start with an issue

Search existing issues first. Describe the user goal, steps to reproduce and the expected result. Remove private data and credentials from screenshots and logs. For security reports, use [SECURITY.md](SECURITY.md).

## Development

1. Fork the repository and work in a focused branch.
2. Install Python 3.11+ and Node.js, then install `requirements-dev.txt` and run `npm ci`.
3. Make a small change and add a test when behavior or an important contract changes.
4. Run `python -m pytest tests -q`, `npm run typecheck` and `npm run build`.
5. Include generated `app/static/js/` files when TypeScript changes. Explain any migration, privacy or compatibility impact in the pull request.

The app uses FastAPI, server-rendered Jinja templates, SQLite and TypeScript. Public content is validated and rendered as text. Avoid executable HTML, arbitrary scripts, external CDN dependencies and unreviewed tracking. Keep normal navigation usable when animations are unsupported or reduced motion is requested.

By submitting a contribution, you agree to license it under the repository's [AGPL-3.0-only license](LICENSE). Please contribute only work you have the right to share, including images and fonts.
