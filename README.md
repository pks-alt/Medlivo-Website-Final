# Medlivo Website Final

The independent Medlivo website repository. It contains one current version of each page and all required local logos, photography, styles and scripts. It is not a branch, preview folder or wrapper around the old project.

## Pages

`index.html`, `workforce-solutions.html`, `nursing-allied.html`, `rehabilitation.html`, `locum-tenens.html`, `search-jobs.html`, `request-staff.html`, `about.html`, `leadership.html`, `careers.html`, `specialties.html`.

There are no V1/V2, preview, backup or alternate homepage folders. Page styling lives in `assets/css/`; shared navigation and page behavior live in `assets/js/`. Images and logos are local. No runtime or recurring build step fetches code or assets from the original repository.

## Preserved decisions

- The recorded homepage V2, without the repeated Ready When You Are / Move forward with Medlivo section.
- Polished Workforce Solutions without the redundant programs section.
- Nursing & Allied with approved opportunities and final spacing.
- Rehabilitation with therapist experience, opportunities and exactly four care-setting rows.
- Original approved image and logo bytes, including the transparent footer logo.
- No em dashes in website copy.

This migration preserved the selected page text and design. Inline CSS and JavaScript were moved to local files and embedded images were decoded losslessly. The existing homepage dropdowns were connected to the shared click handler. Historical CSS declarations were not blindly deleted, because their cascade controls the approved layouts.

## One publishing path

GitHub **Settings > Pages > Deploy from a branch > main > / (root) > Save**.

Use GitHub's native branch-based Pages publisher only. Do not add a second workflow that deploys a V2 folder or another source tree. `.github/workflows/site.yml` is read-only verification and packaging; it does not publish a competing version.

The intended website address after Pages is enabled is `https://pks-alt.github.io/Medlivo-Website-Final/`. A repository commit or a passing local test alone is not proof that this public address is live.

## Local browser preview

Run `python -m http.server 8000` from the repository root, then open `http://localhost:8000/`. No installation is necessary to view the site.

For verification: `python -m pip install -r requirements-dev.txt`, then `python -m playwright install chromium`, and run `python scripts/verify_site.py --base-url http://localhost:8000/ --output-dir verification`. Do not submit production forms in tests.

## Controlled updates

Edit only these root pages and their local assets. After an intentional approved change, run `python scripts/update_manifest.py --build-id YOUR_NEW_BUILD_ID`, then run verification before committing. Do not change hashes to conceal a failed content or route check.

`BUILD.json` records the imported page revisions, original hashes, and current file hashes. The old project was read at the fixed recovered commit `ec962a7bb7850cd6bfe7805664ca15a4261b508e`; it was not modified. The one-time import tools have been removed from this repository.

## Verification evidence

Initial standalone verification: https://github.com/pks-alt/Medlivo-Website-Final/actions/runs/36434811525

All eleven pages were opened at 1440px and 390px. The checks cover local links and anchors, loaded images, script errors, horizontal overflow, the removed homepage closing section, Nursing opportunities, the four Rehab settings and the homepage dropdown controls. Home, Solutions, Nursing and Rehab were also compared with the saved design at both viewport widths. Geometry and visible copy were unchanged; the comparison records any small Chromium header-edge rasterization differences rather than calling them pixel-identical.

## Remaining production integrations

The current Request Staff form opens a prepared email. A successful backend lead submission is not implemented by this static site. The job-search page is a front-end ATS handoff and must be connected to production JobDiva/ATS data by the developers. Category links and demonstration records are not proof of live openings. Existing external privacy/terms destinations are retained.
