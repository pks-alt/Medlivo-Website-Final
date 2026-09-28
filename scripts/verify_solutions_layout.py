"""Check the current Solutions page, never submit production forms."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import urllib.request
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--public', action='store_true')
    args = parser.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    results = []; failures = []
    url = urljoin(args.base_url, 'workforce-solutions.html')
    if args.public:
        hashes = []
        for name in ['workforce-solutions.html', 'assets/css/solutions-responsive.css']:
            request = urllib.request.Request(urljoin(args.base_url, name), headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(request, timeout=40) as response:
                actual = hashlib.sha256(response.read()).hexdigest()
            expected = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            hashes.append({'file':name,'matched':actual==expected})
        (out/'hashes.json').write_text(json.dumps(hashes, indent=2))
        assert all(row['matched'] for row in hashes), 'Published Solutions files differ from this build'
    with sync_playwright() as p:
        executable = shutil.which('google-chrome') or shutil.which('chromium')
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **({'executable_path':executable} if executable else {}))
        for width in [320,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]:
            page = browser.new_page(viewport={'width':width,'height':1080 if width>1040 else 844}, device_scale_factor=1)
            errors=[]
            page.on('pageerror',lambda error,bucket=errors:bucket.append(str(error)))
            response=page.goto(url,wait_until='networkidle',timeout=60000)
            page.evaluate('document.fonts.ready')
            row=page.evaluate('''()=>{
              const get=(selector)=>document.querySelector(selector);
              const rect=(selector)=>{const r=get(selector).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
              const clipped=[];
              document.querySelectorAll('main h1,main h2,main h3,main p,.enterprise-core strong,.enterprise-grid b').forEach(e=>{
                if(e.clientWidth>0 && e.scrollWidth>e.clientWidth+2)clipped.push(e.textContent.trim());
              });
              return {
                width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,
                clipped_text:clipped,hero:rect('.hero'),hero_grid:rect('.hero-grid'),support:rect('.enterprise-visual'),
                hero_columns:getComputedStyle(get('.hero-grid')).gridTemplateColumns,
                model_count:document.querySelectorAll('.solution-model').length,
                step_count:document.querySelectorAll('.delivery-step').length,
                delivery_font:getComputedStyle(get('.delivery-step p')).fontSize,
                sections:[...document.querySelectorAll('main>section')].map(e=>e.className),
                broken_images:[...document.querySelectorAll('img')].filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.getAttribute('src')),
                panel_text:get('.solutions-contact-panel').innerText,
                stylesheet:!!document.querySelector('link[href*="solutions-responsive.css"]')
              };
            }''')
            row.update(status=response.status,errors=errors)
            if width<=1040 and row['support']['y'] <= row['hero_grid']['y']+100:
                failures.append('Hero did not stack at '+str(width))
            if width>=1920 and abs(row['hero_grid']['width']-1560)>2:
                failures.append('Large-screen content width changed')
            if width in [390,768,1041,1440,1920,2560,3440]:
                page.screenshot(path=str(out/f'solutions-{width}.png'),full_page=True,animations='disabled')
                page.screenshot(path=str(out/f'solutions-{width}-top.png'),animations='disabled')
            if row['overflow'] or row['clipped_text'] or row['broken_images'] or errors or row['status']!=200 or not row['stylesheet']:
                failures.append(row.copy())
            assert row['sections']==['hero','challenges','solutions','delivery','final'], 'Approved section order changed'
            assert row['model_count']==3 and row['step_count']==4
            assert 'Need healthcare talent?' in row['panel_text'] and '855-633-5486' in row['panel_text']
            if width in [390,1920]:
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first
                trigger.click();assert trigger.get_attribute('aria-expanded')=='true'
                page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
                if width==390:page.locator('button.menu').click()
                page.locator('a[href="#solutions"]').click();page.wait_for_url('**#solutions')
                page.locator('.solutions-contact-panel a[href="request-staff.html"]').click()
                page.wait_for_url('**/request-staff.html')
                assert page.locator('#staffingRequestForm').count()==1
                row['navigation_and_request_destination']='passed'
            results.append(row);page.close()
        browser.close()
    report={'results':results,'failures':failures,'passed':not failures}
    (out/'solutions-layout.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    assert not failures, 'Solutions layout defects found'

if __name__=='__main__':main()
