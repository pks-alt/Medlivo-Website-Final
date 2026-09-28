"""Check Nursing & Allied in the current Final build. Never submit lead forms."""
from pathlib import Path
from urllib.parse import urljoin
import argparse, base64, hashlib, json, mimetypes, shutil, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WIDTHS=[320,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]
SECTIONS=['na-premium-hero','market na-market-premium','signals','clinical-ready','open-positions','engage']
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
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://127.0.0.1:8765/')
    p.add_argument('--output-dir',required=True)
    p.add_argument('--public',action='store_true')
    p.add_argument('--inline',action='store_true',help='Offline in-memory rendering only; excludes URL/navigation verification')
    args=p.parse_args()
    if args.public and args.inline:p.error('--public and --inline are mutually exclusive')
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    url=urljoin(args.base_url,'nursing-allied.html');results=[];failures=[]
    if args.public:
        rows=[]
        for name in ['nursing-allied.html','assets/css/nursing-allied.css','assets/css/nursing-responsive.css',PHOTO]:
            request=urllib.request.Request(urljoin(args.base_url,name),headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(request,timeout=40) as r:data=r.read()
            expected=hashlib.sha256((ROOT/name).read_bytes()).hexdigest();actual=hashlib.sha256(data).hexdigest()
            rows.append({'file':name,'expected':expected,'actual':actual,'matched':expected==actual})
        (out/'hashes.json').write_text(json.dumps(rows,indent=2))
        assert all(x['matched'] for x in rows),'Public Nursing HTML/CSS/photo differ from the tested build'
    offline=inline_html() if args.inline else None
    with sync_playwright() as playwright:
        exe=shutil.which('google-chrome') or shutil.which('chromium')
        browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for width in WIDTHS:
            page=browser.new_page(viewport={'width':width,'height':1080 if width>1040 else 900},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda e,bucket=errors:bucket.append(str(e)))
            if offline:
                page.set_content(offline,wait_until='load');status=None
            else:
                response=page.goto(url,wait_until='networkidle',timeout=60000);status=response.status
            page.evaluate('document.fonts.ready')
            decode_errors=page.evaluate('''async()=>{const bad=[];await Promise.all([...document.images].map(async img=>{try{await img.decode()}catch(e){bad.push(img.alt||img.getAttribute('src'))}}));return bad}''')
            row=page.evaluate('''()=>{
                const rect=s=>{let r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
                const clipped=[];
                document.querySelectorAll('main h1, main h2, main h3, main p, .stack-card strong, .stack-card small, main a.btn').forEach(e=>{
                    let r=e.getBoundingClientRect();if(r.width>0&&(e.scrollWidth>e.clientWidth+2||r.right>innerWidth+2||r.left< -2))clipped.push(e.textContent.trim());
                });
                return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,clipped_text:clipped,
                    hero:rect('.na-premium-hero'),grid:rect('.na-premium-grid'),copy:rect('.na-premium-copy'),stack:rect('.na-hero-stack'),
                    cards:['.stack-main','.stack-nursing','.stack-allied'].map(rect),
                    sections:[...document.querySelectorAll('main>section')].map(e=>e.className),
                    recruiting_cards:document.querySelectorAll('.signal-card').length,readiness_cards:document.querySelectorAll('.ready-card').length,
                    opportunity_cards:document.querySelectorAll('#open-positions .position-card').length,role_tags:document.querySelectorAll('.role-cloud span').length,
                    opportunity_links:[...document.querySelectorAll('.position-card a')].map(e=>e.getAttribute('href')),
                    readable_font:getComputedStyle(document.querySelector('.signal-card p')).fontSize,
                    hero_photo_width:document.querySelector('.na-hero-image img').naturalWidth,
                    removed_nav_absent:!document.querySelector('.section-nav,.page-nav')};
            }''')
            row.update(status=status,errors=errors,image_decode_errors=decode_errors)
            for i,a in enumerate(row['cards']):
                for b in row['cards'][i+1:]:
                    if min(a['right'],b['right'])-max(a['x'],b['x'])>1 and min(a['bottom'],b['bottom'])-max(a['y'],b['y'])>1:failures.append(f'Hero cards overlap at {width}')
            if width>=1920 and abs(row['grid']['width']-1560)>2:failures.append(f'Wrong large-screen width {width}')
            if width<=1040 and row['stack']['y']<row['copy']['bottom']:failures.append(f'Mobile hero not stacked at {width}')
            if row['sections']!=SECTIONS or row['recruiting_cards']!=4 or row['readiness_cards']!=4 or row['opportunity_cards']!=3 or row['role_tags']!=13:failures.append('Approved content missing')
            if row['hero_photo_width']!=1800 or decode_errors:failures.append('Hero photo or logo failed decoding')
            if row['overflow'] or row['clipped_text'] or errors or (not offline and status!=200):failures.append(row.copy())
            if width in [390,1041,1440,1920,2560]:
                page.screenshot(path=str(out/f'nursing-{width}-top.png'),animations='disabled')
                if width in [390,1920]:page.screenshot(path=str(out/f'nursing-{width}-full.png'),full_page=True,animations='disabled')
            if width in [390,1920]:
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first
                trigger.click();assert trigger.get_attribute('aria-expanded')=='true'
                page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
                if width==390:page.locator('button.menu').click()
                row['menu_keyboard']='passed'
                if not offline:
                    page.locator('.client-card a.btn').click();page.wait_for_url('**/request-staff.html')
                    assert page.locator('#staffingRequestForm').count()==1
                    page.goto(url,wait_until='networkidle');page.locator('.clinician-card a.btn').click();page.wait_for_url('**/search-jobs.html')
                    row['request_and_jobs']='passed'
            if width==1920 and not offline:
                for i,target in enumerate(row['opportunity_links']):
                    page.goto(url,wait_until='networkidle');page.locator('.position-card a').nth(i).click()
                    assert page.url==urljoin(args.base_url,target)
                row['three_opportunity_destinations']='passed'
            results.append(row);page.close()
        browser.close()
    report={'mode':'offline-render-only' if args.inline else 'public' if args.public else 'local-http','results':results,'failures':failures,'passed':not failures}
    (out/'nursing-layout.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    assert not failures,'Nursing layout tests found defects'

if __name__=='__main__':main()
