# Medlivo Website Final

This is the independent Medlivo website repository. It is not a branch or preview folder in the old project.

The initial import uses the recovered, version-recorded page set from commit `ec962a7bb7850cd6bfe7805664ca15a4261b508e` in the original repository. Only the eleven canonical pages and their required assets will be brought into this project. The original repository will not be modified.

## Site structure

- Root HTML files: the single editable version of each page.
- `assets/`: local approved logos, photography, page styles and scripts.
- `BUILD.json`: page provenance and file checksums.
- `scripts/verify_site.py`: source, route and browser regression checks.
- `.github/workflows/site.yml`: the sole ongoing build, verification and Pages deployment workflow.

No old V1/V2, preview or backup folders are part of this repository. The imported site must not load assets or pages from the old GitHub project.

## Preserved decisions

- Homepage uses the recovered V2 design without the repeated Ready When You Are / Move forward with Medlivo closing section.
- Workforce Solutions uses the polished version without the redundant programs section.
- Nursing & Allied includes the approved opportunities section and spacing pass.
- Rehabilitation includes therapist experience, opportunities, and exactly four care-setting rows.
- Existing approved logo and image bytes are preserved.
- Website copy does not use em dashes.

## Integration boundary

This is the front-end website handoff. The current staffing request form opens a prepared email; it is not a backend lead-capture service. The job-search interface still requires the developer's production ATS integration. Do not treat category links or demonstration job data as confirmed live openings.

## GitHub Pages

The publishing source for this repository should be **GitHub Actions**, using the single `site.yml` workflow. Do not also enable a branch-based publisher. Publishing is complete only when the public page contents match `BUILD.json` and the public browser checks pass.

## Local preview

Run `python -m http.server 8000` at the repository root, then open `http://localhost:8000/`. No files from the old repository are needed after import.
