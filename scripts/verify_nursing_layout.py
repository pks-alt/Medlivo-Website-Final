"""Nursing & Allied care-setting revision checks. Never submit leads or call phones."""
from pathlib import Path
from urllib.parse import urljoin
import argparse, base64, hashlib, json, mimetypes, shutil, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WIDTHS=[320,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]
SECTIONS=['nd-hero','nd-perspective','nd-settings','nd-recruiting','nd-readiness','open-positions nd-opportunities','nd-connect']
SETTINGS=['Acute & Inpatient','Procedural, Diagnostic & Technical Care','Ambulatory, Clinic & Specialty Practice','Post-Acute, Long-Term & Home-Based Care']
PHOTO='assets/images/embedded/fef3061a52147602be64.webp'

def inline_html():
    soup=BeautifulSoup((ROOT/'nursing-allied.html').read_text(),'html.parser')
    for link in soup.select('link[rel="stylesheet"]'):
        tag=soup.new_tag('style');tag.string=(ROOT/link['href'].split('?')[0]).read_text();link.replace_with(tag)
    for image in soup.select('img[src]'):
        path=ROOT/image['src'].split('?')[0]
        image['src']='data:'+mimetypes.guess_type(path)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()
    for script in soup.select('script[src]'):
        script.string=(ROOT/script['src']).read_text();del script['src']
    return str(soup)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://127.0.0.1:8765/')
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--public',action='store_true')
    parser.add_argument('--inline',action='store_true')
    args=parser.parse_args()
    if args.public and args.inline:parser.error('--public and --inline cannot be combined')
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    url=urljoin(args.base_url,'nursing-allied.html');results=[];failures=[]
    if args.public:
        rows=[]
        for name in ['nursing-allied.html','assets/css/nursing-allied.css','assets/css/nursing-responsive.css',PHOTO]:
            req=urllib.request.Request(urljoin(args.base_url,name),headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=40) as response:data=response.read()
            expected=hashlib.sha256((ROOT/name).read_bytes()).hexdigest();actual=hashlib.sha256(data).hexdigest()
            rows.append({'file':name,'expected':expected,'actual':actual,'matched':expected==actual})
        (out/'hashes.json').write_text(json.dumps(rows,indent=2))
        assert all(row['matched'] for row in rows),'Public files do not match the tested Nursing revision'
    offline=inline_html() if args.inline else None
    with sync_playwright() as p:
        exe=shutil.which('google-chrome') or shutil.which('chromium')
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for width in WIDTHS:
            page=browser.new_page(viewport={'width':width,'height':1080 if width>1040 else 900},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda error,bucket=errors:bucket.append(str(error)))
            if offline:page.set_content(offline,wait_until='load');status=None
            else:response=page.goto(url,wait_until='networkidle',timeout=60000);status=response.status
            page.evaluate('document.fonts.ready')
            decode_errors=page.evaluate('''async()=>{const bad=[];await Promise.all([...document.images].map(async img=>{try{await img.decode()}catch(e){bad.push(img.alt)}}));return bad}''')
            row=page.evaluate('''()=>{
                const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
                const clipped=[];
                document.querySelectorAll('main h1, main h2, main h3, main h4, main p, main a.btn, .role-cloud span').forEach(e=>{
                    if(e.classList.contains('nd-sr-only'))return;
                    const r=e.getBoundingClientRect();
                    if(r.width>2&&(e.scrollWidth>e.clientWidth+2||r.right>innerWidth+2||r.left< -2))clipped.push(e.textContent.trim());
                });
                return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,clipped_text:clipped,
                    grid:rect('.nd-hero-grid'),copy:rect('.nd-hero-copy'),photo:rect('.nd-hero-photo'),
                    sections:[...document.querySelectorAll('main>section')].map(e=>e.className),
                    care_settings:[...document.querySelectorAll('.nd-setting-copy h3')].map(e=>e.textContent.trim()),
                    what_matters:document.querySelectorAll('.nd-setting-factors').length,
                    recruiting_steps:document.querySelectorAll('.nd-process-step').length,
                    readiness_checks:document.querySelectorAll('.nd-ready-item').length,
                    opportunity_cards:document.querySelectorAll('#open-positions .position-card').length,
                    role_tags:document.querySelectorAll('.role-cloud span').length,
                    opportunity_links:[...document.querySelectorAll('.position-card a')].map(e=>e.getAttribute('href')),
                    hero_photo_width:document.querySelector('.nd-hero-photo img').naturalWidth,
                    backgrounds:[...document.querySelectorAll('main>section')].map(e=>getComputedStyle(e).backgroundColor),
                    extra_nav_absent:!document.querySelector('.section-nav,.page-nav'),
                    removed_closing_absent:!document.body.innerText.includes('Ready When You Are'),
                    therapist_claim_absent:!/20\\+|firsthand therapist|founder.*therapist/i.test(document.querySelector('main').innerText),
                    em_dash_absent:!document.querySelector('main').innerText.includes('—')};
            }''')
            row.update(status=status,errors=errors,image_decode_errors=decode_errors)
            if width>=1920 and abs(row['grid']['width']-1560)>2:failures.append(f'Unexpected content width at {width}')
            if width<=1040 and row['photo']['y']<row['copy']['bottom']:failures.append(f'Hero stacking failed at {width}')
            if width>1040 and row['photo']['x']<row['copy']['right']-1:failures.append(f'Hero columns overlap at {width}')
            if row['sections']!=SECTIONS or row['care_settings']!=SETTINGS:failures.append('Section order or four care settings changed')
            if [row['what_matters'],row['recruiting_steps'],row['readiness_checks'],row['opportunity_cards'],row['role_tags']]!=[4,4,4,3,13]:failures.append('Expected content missing')
            if row['hero_photo_width']!=1800 or decode_errors:failures.append('Photo or logo decoding failed')
            if not all(row[k] for k in ['extra_nav_absent','removed_closing_absent','therapist_claim_absent','em_dash_absent']):failures.append('Editorial regression')
            if row['overflow'] or row['clipped_text'] or errors or (not offline and status!=200):failures.append(row.copy())
            if width in [390,1041,1440,1920,2560]:
                page.screenshot(path=str(out/f'nursing-{width}-top.png'),animations='disabled')
                if width in [390,1920]:
                    page.screenshot(path=str(out/f'nursing-{width}-full.png'),full_page=True,animations='disabled')
                    page.locator('#care-settings').screenshot(path=str(out/f'care-settings-{width}.png'),animations='disabled')
            if width in [390,1920]:
                page.evaluate('window.scrollTo(0,0)')
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first
                trigger.click();assert trigger.get_attribute('aria-expanded')=='true'
                page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
                if width==390:page.locator('button.menu').click()
                row['menu_keyboard']='passed'
                if not offline:
                    page.locator('.nd-hero-actions a[href="#open-positions"]').click();page.wait_for_url('**/#open-positions') if url.endswith('/') else page.wait_for_url('**/nursing-allied.html#open-positions')
                    assert page.locator('#open-positions').is_visible()
                    page.locator('.client-card a.btn').click();page.wait_for_url('**/request-staff.html')
                    assert page.locator('#staffingRequestForm').count()==1
                    page.goto(url,wait_until='networkidle');page.locator('.clinician-card a.btn').click();page.wait_for_url('**/search-jobs.html')
                    row['anchor_request_and_jobs']='passed'
            if width==1920 and not offline:
                for i,target in enumerate(row['opportunity_links']):
                    page.goto(url,wait_until='networkidle');page.locator('.position-card a').nth(i).click()
                    assert page.url==urljoin(args.base_url,target)
                row['three_opportunity_destinations']='passed'
            results.append(row);page.close()
        browser.close()
    report={'mode':'offline-render-only' if args.inline else 'public' if args.public else 'local-http','results':results,'failures':failures,'passed':not failures}
    (out/'nursing-layout.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'mode':report['mode'],'widths':len(results),'failures':failures,'passed':not failures},indent=2))
    assert not failures,'Nursing page checks found defects'

if __name__=='__main__':main()
