"""Verify the standalone Medlivo build. No forms are submitted by these tests.

python scripts/verify_site.py --base-url http://127.0.0.1:8000/ --output-dir /tmp/medlivo-check
Pass --public to check that the published bytes match BUILD.json before browser tests.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import time
import urllib.request
from urllib.parse import urlsplit, unquote, urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OLD_PATH = '/Medlivo-Website/'

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify_source(manifest: dict) -> dict:
    failures = []
    warnings = []
    for name, expected in manifest['files'].items():
        path = ROOT / name
        if not path.is_file() or sha256(path.read_bytes()) != expected:
            failures.append('File checksum mismatch: ' + name)
    for name in manifest['pages']:
        text = (ROOT / name).read_text(encoding='utf-8')
        soup = BeautifulSoup(text, 'html.parser')
        if OLD_PATH in text or 'raw.githubusercontent.com/pks-alt/Medlivo-Website/' in text:
            failures.append(name + ': runtime reference to old repository')
        if '\u2014' in soup.get_text():
            failures.append(name + ': em dash in page text')
        if soup.find('base'):
            failures.append(name + ': base tag redirects relative routes')
        if len(soup.find_all('h1')) != 1:
            failures.append(name + ': expected exactly one H1')
        for element in soup.select('[href], [src], form[action]'):
            attr = 'src' if element.has_attr('src') else ('action' if element.name == 'form' else 'href')
            value = element.get(attr, '')
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc:
                continue
            relative = unquote(parsed.path)
            target = (ROOT / relative) if relative else (ROOT / name)
            if relative and not target.exists():
                failures.append(name + ': missing local target ' + value)
            elif parsed.fragment and target.suffix == '.html':
                document = BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser')
                if not document.find(id=unquote(parsed.fragment)):
                    warnings.append(name + ': missing fragment ' + value)
    home = BeautifulSoup((ROOT / 'index.html').read_text(), 'html.parser')
    if home.select('.closing-cta') or 'Ready When You Are' in home.get_text():
        failures.append('Repeated homepage closing section returned')
    if not home.select('.workforce-v2') or not home.select('.why-v2'):
        failures.append('Wrong homepage version')
    nursing = BeautifulSoup((ROOT / 'nursing-allied.html').read_text(), 'html.parser')
    if not nursing.select_one('#open-positions'):
        failures.append('Nursing opportunities section missing')
    rehab = BeautifulSoup((ROOT / 'rehabilitation.html').read_text(), 'html.parser')
    labels = [x.get_text(' ', strip=True) for x in rehab.select('.care-settings .setting-card h3')]
    if labels != ['Acute & Inpatient', 'Inpatient Rehabilitation', 'Post-Acute & Home-Based Care', 'Outpatient']:
        failures.append('Wrong Rehabilitation settings: ' + repr(labels))
    if not rehab.select_one('.therapist-proof') or not rehab.select_one('.rehab-positions'):
        failures.append('Rehabilitation experience or opportunities section missing')
    solutions = BeautifulSoup((ROOT / 'workforce-solutions.html').read_text(), 'html.parser')
    if solutions.select('section.programs'):
        failures.append('Old repeated Solutions program section returned')
    request = BeautifulSoup((ROOT / 'request-staff.html').read_text(), 'html.parser')
    if not request.select_one('#staffingRequestForm'):
        failures.append('Request Staff form missing')
    report = {'pages': len(manifest['pages']), 'files': len(manifest['files']), 'rehab_settings': labels,
              'failures': failures, 'warnings': sorted(set(warnings))}
    return report

def verify_public(manifest: dict, base: str) -> dict:
    results = []
    for name in list(manifest['pages']) + ['BUILD.json']:
        expected = sha256((ROOT / name).read_bytes())
        url = urljoin(base, '' if name == 'index.html' else name)
        row = {'file': name, 'url': url, 'expected_sha256': expected, 'matched': False}
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache', 'User-Agent': 'Medlivo-Final-Verification'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = response.read()
                    row.update(status=response.status, actual_sha256=sha256(data), matched=sha256(data) == expected)
                if row['matched']:
                    break
            except Exception as error:
                row['error'] = str(error)
            if attempt < 5:
                time.sleep(10)
        results.append(row)
    return {'results': results, 'passed': all(r['matched'] for r in results)}

def verify_browser(manifest: dict, base: str, output: pathlib.Path) -> dict:
    results, failures = [], []
    with sync_playwright() as playwright:
        executable = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'], **({'executable_path': executable} if executable else {}))
        for width in [1440, 390]:
            for name in manifest['pages']:
                page = browser.new_page(viewport={'width': width, 'height': 1000 if width == 1440 else 844}, device_scale_factor=1)
                errors, old_requests = [], []
                page.on('pageerror', lambda error, bucket=errors: bucket.append(str(error)))
                page.on('request', lambda request, bucket=old_requests: bucket.append(request.url) if OLD_PATH in request.url else None)
                url = urljoin(base, '' if name == 'index.html' else name)
                row = {'page': name, 'width': width, 'url': url}
                try:
                    response = page.goto(url, wait_until='networkidle', timeout=60000)
                    row.update(status=response.status if response else None, errors=errors, old_repository_requests=old_requests,
                        overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth'),
                        headings=page.locator('main h1,main h2').all_text_contents(),
                        broken_images=page.locator('img').evaluate_all('(es)=>es.filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.getAttribute("src"))'))
                    if name == 'index.html':
                        row['home_v2'] = page.locator('.workforce-v2').count() == 1 and page.locator('.why-v2').count() == 1
                        row['removed_closing_section'] = page.locator('.closing-cta').count() == 0
                        if not row['home_v2'] or not row['removed_closing_section']:
                            failures.append(name + ': homepage version check failed')
                    if name == 'rehabilitation.html':
                        row['care_setting_rows'] = page.locator('.care-settings .setting-card').count()
                        if row['care_setting_rows'] != 4:
                            failures.append(name + ': expected four settings')
                        if width == 1440:
                            page.locator('.care-settings').screenshot(path=str(output / 'rehab-four-care-settings.png'))
                    if name == 'nursing-allied.html':
                        row['open_positions'] = page.locator('#open-positions').count() == 1
                        if not row['open_positions']:
                            failures.append(name + ': opportunities missing')
                    if name in ['index.html', 'workforce-solutions.html', 'nursing-allied.html', 'rehabilitation.html', 'request-staff.html']:
                        page.screenshot(path=str(output / (name.removesuffix('.html') + '-' + str(width) + '.png')), full_page=True)
                    if name == 'index.html':
                        if width == 390:
                            page.locator('button.menu').click()
                            row['mobile_menu_open'] = page.locator('nav.links').is_visible()
                        trigger = page.get_by_role('button', name='Specialties', exact=False).first
                        trigger.click()
                        row['specialties_dropdown_open'] = trigger.get_attribute('aria-expanded') == 'true'
                        if not row['specialties_dropdown_open']:
                            failures.append('Homepage Specialties menu did not open at ' + str(width))
                    if row.get('status') != 200 or row.get('overflow') or errors or row.get('broken_images') or old_requests:
                        failures.append(row.copy())
                except Exception as error:
                    row['test_error'] = str(error)
                    failures.append(row.copy())
                results.append(row)
                page.close()
        browser.close()
    return {'results': results, 'failures': failures, 'passed': not failures}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--public', action='store_true')
    args = parser.parse_args()
    output = pathlib.Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'BUILD.json').read_text())
    source = verify_source(manifest)
    (output / 'source-checks.json').write_text(json.dumps(source, indent=2))
    print(json.dumps(source, indent=2), flush=True)
    if source['failures']:
        raise SystemExit('Source checks failed')
    if args.public:
        published = verify_public(manifest, args.base_url)
        (output / 'public-hashes.json').write_text(json.dumps(published, indent=2))
        if not published['passed']:
            raise SystemExit('Published files do not yet match the build')
    browser = verify_browser(manifest, args.base_url, output)
    (output / 'browser-checks.json').write_text(json.dumps(browser, indent=2))
    print(json.dumps(browser, indent=2), flush=True)
    if not browser['passed']:
        raise SystemExit('Browser checks failed')

if __name__ == '__main__':
    main()
