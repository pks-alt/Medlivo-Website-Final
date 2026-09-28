"""Verify the current Final Specialties overview. Never submit production forms."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import urllib.request
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [320,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]
DIVISIONS = ['nursing-allied.html','rehabilitation.html','locum-tenens.html']

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--public',action='store_true')
    args=parser.parse_args()
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    url=urljoin(args.base_url,'specialties.html');results=[];failures=[]
    if args.public:
        hashes=[]
        for name in ['specialties.html','assets/css/specialties.css','assets/css/specialties-responsive.css']:
            req=urllib.request.Request(urljoin(args.base_url,name),headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=40) as r:actual=hashlib.sha256(r.read()).hexdigest()
            expected=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            hashes.append({'file':name,'expected':expected,'actual':actual,'matched':actual==expected})
        (out/'hashes.json').write_text(json.dumps(hashes,indent=2))
        assert all(x['matched'] for x in hashes),'Published Specialties files do not match this build'
    with sync_playwright() as p:
        exe=shutil.which('google-chrome') or shutil.which('chromium')
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for width in WIDTHS:
            page=browser.new_page(viewport={'width':width,'height':1080 if width>1040 else 844},device_scale_factor=1)
            errors=[]
            page.on('pageerror',lambda e,bucket=errors:bucket.append(str(e)))
            response=page.goto(url,wait_until='networkidle',timeout=60000)
            page.evaluate('document.fonts.ready')
            row=page.evaluate('''()=>{
                const g=s=>document.querySelector(s);
                const rect=s=>{const r=g(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
                const clipped=[];
                document.querySelectorAll('main h1,main h2,main h3,main p,.ops-card strong,.ops-card small,.map-row b,.map-head strong').forEach(e=>{
                    if(e.clientWidth>0 && (e.scrollWidth>e.clientWidth+2 || e.getBoundingClientRect().right>innerWidth+2))clipped.push(e.textContent.trim());
                });
                return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,
                    clipped_text:clipped,hero:rect('.hero'),hero_grid:rect('.hero-grid'),map:rect('.specialty-map'),
                    map_links:[...document.querySelectorAll('.map-row')].map(e=>e.getAttribute('href')),
                    map_priorities:[...document.querySelectorAll('.map-row b')].map(e=>getComputedStyle(e).display),
                    division_links:[...document.querySelectorAll('.division-link')].map(e=>e.getAttribute('href')),
                    division_count:document.querySelectorAll('.specialty-block').length,
                    detail_count:document.querySelectorAll('.ops-card').length,
                    detail_font:getComputedStyle(g('.ops-card strong')).fontSize,
                    sections:[...document.querySelectorAll('main>section')].map(e=>e.className),
                    request:g('.final-side:first-child .btn').getAttribute('href'),
                    jobs:g('.final-side:last-child .btn').getAttribute('href'),
                    stylesheet:!!g('link[href*="specialties-responsive.css"]'),
                    broken_images:[...document.querySelectorAll('img')].filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.getAttribute('src'))};
            }''')
            row.update(status=response.status,errors=errors)
            if width<=1040 and row['map']['y']<=row['hero_grid']['y']+100:failures.append('Hero did not stack at '+str(width))
            if width>=1920 and abs(row['hero_grid']['width']-1560)>2:failures.append('Incorrect wide-screen grid')
            if row['sections']!=['hero','divisions','standard','final']:failures.append('Section order changed')
            if row['map_links']!=DIVISIONS or row['division_links']!=DIVISIONS:failures.append('Incorrect division targets')
            if row['division_count']!=3 or row['detail_count']!=9:failures.append('Division content missing')
            if row['request']!='request-staff.html' or row['jobs']!='search-jobs.html':failures.append('Incorrect closing paths')
            if row['overflow'] or row['clipped_text'] or errors or row['broken_images'] or row['status']!=200 or not row['stylesheet']:failures.append(row.copy())
            if width in [390,1041,1440,1920,2560]:
                page.screenshot(path=str(out/f'specialties-{width}-top.png'),animations='disabled')
                page.screenshot(path=str(out/f'specialties-{width}-full.png'),full_page=True,animations='disabled')
            if width in [390,1920]:
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first
                trigger.click();assert trigger.get_attribute('aria-expanded')=='true'
                page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
                if width==390:page.locator('button.menu').click()
                page.locator('a[href="#divisions"]').click();page.wait_for_url('**#divisions')
                page.locator('.final-side:first-child a.btn').click();page.wait_for_url('**/request-staff.html')
                assert page.locator('#staffingRequestForm').count()==1
                page.goto(url,wait_until='networkidle')
                page.locator('.final-side:last-child a.btn').click();page.wait_for_url('**/search-jobs.html')
                row['menu_anchor_request_jobs']='passed'
            if width==1920:
                for i,target in enumerate(DIVISIONS):
                    page.goto(url,wait_until='networkidle');page.locator('.map-row').nth(i).click()
                    page.wait_for_url('**/'+target);assert page.locator('h1').count()==1
                row['three_division_routes']='passed'
            results.append(row);page.close()
        browser.close()
    report={'results':results,'failures':failures,'passed':not failures}
    (out/'specialties-layout.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    assert not failures,'Specialties layout checks found defects'

if __name__=='__main__':main()
