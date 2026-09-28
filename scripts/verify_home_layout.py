"""Read-only homepage rendering checks. Never submit a production form."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--base-url', required=True)
parser.add_argument('--output-dir', required=True)
args = parser.parse_args()
out = Path(args.output_dir)
out.mkdir(parents=True, exist_ok=True)
viewports = [(320,760),(390,844),(768,1024),(1024,900),(1280,900),(1440,1000),(1920,1080),(2560,1440),(3440,1440)]
results = []
failures = []
with sync_playwright() as p:
    executable = shutil.which('google-chrome') or shutil.which('chromium')
    if not executable:
        subprocess.run(['python','-m','playwright','install','chromium'],check=True)
    browser = p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':executable} if executable else {}))
    for width,height in viewports:
        page = browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        page.emulate_media(reduced_motion='reduce')
        errors = []
        page.on('pageerror',lambda e: errors.append(str(e)))
        response = page.goto(args.base_url,wait_until='networkidle',timeout=60000)
        page.evaluate('document.fonts.ready')
        page.mouse.move(0,0)
        row = page.evaluate('''() => {
          const rect = s => {const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
          return {overflow:document.documentElement.scrollWidth>innerWidth,
            wrapper:rect('.hero-grid'),hero:rect('.home-hero-premium'),photo:rect('.hero-media'),
            sections:[...document.querySelectorAll('main>section')].map(e=>e.className),
            ready_when_you_are:document.body.innerText.includes('Ready When You Are'),
            broken_images:[...document.images].filter(e=>!e.complete||!e.naturalWidth).map(e=>e.getAttribute('src')),
            headline:document.querySelector('h1').innerText,
            search_columns:getComputedStyle(document.querySelector('.ats-search')).gridTemplateColumns,
            current_stylesheet:!!document.querySelector('link[href*="home-responsive.css"]')};
        }''')
        row.update(width=width,status=response.status if response else None,errors=errors)
        if row['status'] != 200 or row['overflow'] or errors or row['broken_images'] or row['ready_when_you_are'] or not row['current_stylesheet']:
            failures.append(row)
        if len(row['sections']) != 6:
            failures.append({'width':width,'issue':'Approved homepage section count changed'})
        if width >= 1280:
            if row['photo']['right'] > row['wrapper']['right']+2 or row['hero']['height']>780:
                failures.append({'width':width,'issue':'Desktop hero escaped the bounded grid or became oversized'})
        if width in [390,1440,1920,2560,3440]:
            page.screenshot(path=str(out/('home-'+str(width)+'-top.png')),animations='disabled')
            page.screenshot(path=str(out/('home-'+str(width)+'-full.png')),full_page=True,animations='disabled')
        if width in [390,1920]:
            if width == 390:
                page.locator('.menu').click()
                if page.locator('.links.open').count()!=1:
                    failures.append({'width':width,'issue':'Mobile navigation failed'})
            page.locator('.nav-dropdown .nav-drop-trigger').first.click()
            if page.locator('.nav-dropdown.open').count()==0:
                failures.append({'width':width,'issue':'Specialties dropdown failed'})
            page.keyboard.press('Escape')
        # Navigation-only job-search test, no backend request or staffing submission.
        if width == 1920:
            page.goto(args.base_url,wait_until='networkidle')
            page.locator('#job-profession').select_option('Rehabilitation')
            page.locator('#job-location').fill('Washington')
            page.locator('.ats-search button').click()
            page.wait_for_url('**/search-jobs.html?**')
            row['job_search_handoff'] = page.url
            if 'division=Rehabilitation' not in page.url or 'location=Washington' not in page.url:
                failures.append({'width':width,'issue':'Job-search filter handoff failed'})
            response = page.goto(urljoin(args.base_url,'request-staff.html'),wait_until='networkidle')
            row['request_staff_status'] = response.status
            if response.status!=200 or page.locator('#staffingRequestForm').count()!=1:
                failures.append({'width':width,'issue':'Request Staff page missing'})
        results.append(row)
        page.close()
    browser.close()
report = {'results':results,'failures':failures,'passed':not failures}
(out/'home-layout-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if failures:
    raise SystemExit('Homepage viewport checks failed')
