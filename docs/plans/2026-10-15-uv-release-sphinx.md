# uv, GitHub Release and Sphinx implementation plan

**Goal:** Manage Python dependencies with uv, distribute the bundled dashboard through GitHub Releases, and publish Sphinx documentation to GitHub Pages.

**Architecture:** Runtime dependencies remain in pyproject.toml; development, documentation and release tools use dependency groups and a committed uv.lock. CI builds the frontend once, bundles it into the wheel and sdist, validates isolated installations, then prepares an independent frontend archive and checksums. A version-tag workflow uploads these tested assets to GitHub Release. Sphinx + MyST render the existing Chinese documentation; the Pages workflow publishes the HTML and synthetic demo.

## Steps

1. Write failing release preparation tests: matching version/tag, required bundled assets, matching frontend contents, archive paths and checksums.
2. Replace dependency files with pyproject dependency groups and uv.lock. Change all supported setup, test, build and smoke-check commands to uv.
3. Implement the release asset helper; build wheel, sdist and standalone frontend archive with SHA256SUMS. Replace PyPI publishing with a gated, repeatable GitHub Release workflow.
4. Add Sphinx configuration, theme and MyST navigation. Update frontend documentation links for Sphinx .html paths. Replace the Pages build command and upload directory.
5. Update README and guides around installing prebuilt GitHub Release wheels with uv, source development, release publishing and Sphinx builds.
6. Verify frozen uv sync, backend/frontend tests, strict Sphinx HTML, real release assets and isolated wheel/sdist serving. Review the workflows and changes; actual publishing waits for a pushed version tag.

## Acceptance

- No requirements files or active pip/MkDocs/PyPI instructions.
- End users can install a GitHub Release wheel containing the frontend without Node.
- Each release contains a wheel, source package, frontend archive and checksums; a mismatched tag fails before publication.
- Sphinx builds with warnings treated as errors and all internal documentation links resolve.
- CI and local instructions use the committed uv lock; Pages serves the Sphinx site and demo.
