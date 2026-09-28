"""Rehabilitation layout and content checks. Never submit leads, email, or calls."""
from pathlib import Path
from urllib.parse import urljoin
import argparse,base64,hashlib,json,mimetypes,shutil,urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WIDTHS=[320,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]
SECTIONS=['rd-hero','therapist-proof rd-proof','rd-disciplines','care-settings rd-settings','rd-recruiting','rd-readiness','rehab-positions rd-opportunities','rd-connect']
SETTINGS=['Acute & Inpatient','Inpatient Rehabilitation','Post-Acute & Home-Based Care','Outpatient']
PHOTO='assets/images/embedded/33c339dc14f5797409bd.webp'
FOUNDER='One of Medlivo’s founders spent more than two decades working as a therapist. That firsthand experience brings a different lens to rehabilitation staffing, understanding the language of therapy, the realities of different care environments, and the pressures clinicians and healthcare organizations navigate every day.'
CONTRAST=(ROOT/'scripts/nursing_contrast_audit.js').read_text().replace('.nd-sr-only','.rd-sr-only')

def inline_html():
    soup=BeautifulSoup((ROOT/'rehabilitation.html').read_text(),'html.parser')
    for link in soup.select('link[rel="stylesheet"]'):
        tag=soup.new_tag('style');tag.string=(ROOT/link['href'].split('?')[0]).read_text();link.replace_with(tag)
    for img in soup.select('img[src]'):
        path=ROOT/img['src'].split('?')[0]
        img['src']='data:'+mimetypes.guess_type(path)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()
    for script in soup.select('script[src]'):
        script.string=(ROOT/script['src']).read_text();del script['src']
    return str(soup)

def main():
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8765/');p.add_argument('--output-dir',required=True);p.add_argument('--inline',action='store_true');p.add_argument('--public',action='store_true');args=p.parse_args()
    if args.public and args.inline:p.error('Public and inline modes are mutually exclusive')
    out=Path(args.output_dir);out.mkdir(exist_ok=True,parents=True);url=urljoin(args.base_url,'rehabilitation.html');failures=[];results=[]
    if args.public:
        hashes=[]
        for name in ['rehabilitation.html','assets/css/rehabilitation.css','assets/css/rehab-responsive.css',PHOTO]:
            req=urllib.request.Request(urljoin(args.base_url,name),headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=40) as r:data=r.read()
            actual=hashlib.sha256(data).hexdigest();expected=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            hashes.append({'file':name,'actual':actual,'expected':expected,'matched':actual==expected})
        (out/'hashes.json').write_text(json.dumps(hashes,indent=2))
        assert all(x['matched'] for x in hashes),'Public Rehab files differ from the tested source'
    offline=inline_html() if args.inline else None
    with sync_playwright() as pw:
        exe=shutil.which('google-chrome') or shutil.which('chromium')
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for width in WIDTHS:
            page=browser.new_page(viewport={'width':width,'height':1080 if width>1040 else 900},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda error,bucket=errors:bucket.append(str(error)))
            if offline:page.set_content(offline,wait_until='load');status=None
            else:resp=page.goto(url,wait_until='networkidle',timeout=60000);status=resp.status
            page.evaluate('document.fonts.ready')
            decode=page.evaluate('''async()=>{const bad=[];await Promise.all([...document.images].map(async e=>{try{await e.decode()}catch(err){bad.push(e.alt)}}));return bad}''')
            row=page.evaluate('''()=>{
              const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
              const clipped=[];document.querySelectorAll('main h1,main h2,main h3,main h4,main p,main a.btn,.role-cloud span').forEach(e=>{if(e.classList.contains('rd-sr-only'))return;const r=e.getBoundingClientRect();if(r.width>2&&(e.scrollWidth>e.clientWidth+2||r.right>innerWidth+2||r.left< -2))clipped.push(e.textContent.trim())});
              return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,clipped_text:clipped,grid:rect('.rd-hero-grid'),copy:rect('.rd-hero-copy'),photo:rect('.rd-hero-photo'),sections:[...document.querySelectorAll('main>section')].map(e=>e.className),section_heights:[...document.querySelectorAll('main>section')].map(e=>e.getBoundingClientRect().height),care_settings:[...document.querySelectorAll('.setting-card h3')].map(e=>e.textContent.trim()),settings_height:document.querySelector('#settings').getBoundingClientRect().height,what_matters:document.querySelectorAll('.rd-setting-factors').length,recruiting_steps:document.querySelectorAll('.rd-process-step').length,readiness_items:document.querySelectorAll('.rd-ready-item').length,opportunity_cards:document.querySelectorAll('.rd-opportunity-card').length,role_tags:[...document.querySelectorAll('.rd-discipline-card .role-cloud span')].map(e=>e.textContent.trim()),opportunity_links:[...document.querySelectorAll('.rd-opportunity-card a')].map(e=>e.getAttribute('href')),photo_width:document.querySelector('.rd-hero-photo img').naturalWidth,backgrounds:[...document.querySelectorAll('main>section')].map(e=>getComputedStyle(e).backgroundColor),em_dash_absent:!document.querySelector('main').innerText.includes('—'),extra_nav_absent:!document.querySelector('.section-nav,.page-nav')};
            }''')
            contrast=page.evaluate(CONTRAST);(out/f'contrast-{width}.json').write_text(json.dumps(contrast,indent=2))
            if contrast['failures'] or contrast['unknown']:failures.append({'width':width,'contrast':contrast['failures'],'unresolved':contrast['unknown']})
            if any(x['font_size']<16 for x in contrast['results'] if x['required']==7):failures.append({'width':width,'error':'Body text below 16px'})
            row.update(status=status,errors=errors,image_decode_errors=decode,contrast={'checked':contrast['text_elements'],'minimum_ratio':contrast['minimum_ratio'],'paragraph_minimum':contrast['paragraph_minimum'],'passed':not contrast['failures'] and not contrast['unknown']})
            checks={
              'correct_sections':row['sections']==SECTIONS,'four_settings':row['care_settings']==SETTINGS,
              'expected_content':[row['what_matters'],row['recruiting_steps'],row['readiness_items'],row['opportunity_cards']]==[4,4,4,3],
              'five_roles':row['role_tags']==['PT','PTA','OT','COTA','SLP'],
              'founder_story':page.locator('.rd-proof-copy p').inner_text()==FOUNDER and page.locator('.rd-proof-mark strong').inner_text()=='20+',
              'readable_image':row['photo_width']==1800 and not decode,
              'wide_canvas':width<1920 or abs(row['grid']['width']-1560)<2,
              'hero_not_overlapping':row['photo']['y']>=row['copy']['bottom']-1 if width<=1040 else row['photo']['x']>=row['copy']['right']-1,
              'compact_settings':row['settings_height']<=830 if width>=1440 else (row['settings_height']<=1450 if width==390 else True),
              'white_reading_areas':row['backgrounds']==['rgb(16, 38, 65)','rgb(255, 255, 255)','rgb(255, 255, 255)','rgb(245, 248, 248)','rgb(255, 255, 255)','rgb(245, 247, 250)','rgb(255, 255, 255)','rgb(255, 255, 255)'],
              'no_clipping':not row['overflow'] and not row['clipped_text'],'no_script_errors':not errors,
              'editorial':row['em_dash_absent'] and row['extra_nav_absent'],'http_ok':offline is not None or status==200}
            row['checks']=checks
            for name,ok in checks.items():
                if not ok:failures.append({'width':width,'check':name})
            if width in [390,1041,1440,1920,2560]:
                page.screenshot(path=str(out/f'rehab-{width}-top.png'),animations='disabled')
                if width in [390,1920]:
                    page.screenshot(path=str(out/f'rehab-{width}-full.png'),full_page=True,animations='disabled')
                    page.locator('#settings').screenshot(path=str(out/f'care-settings-{width}.png'),animations='disabled')
            if width in [390,1920]:
                page.evaluate('window.scrollTo(0,0)')
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first;trigger.click();assert trigger.get_attribute('aria-expanded')=='true'
                expanded=page.evaluate(CONTRAST);assert not expanded['failures'] and not expanded['unknown'],'Expanded nav text contrast'
                page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
                if width==390:page.locator('button.menu').click()
                for selector in ['.rd-hero .rd-button-light','.rd-opportunity-card a','.rd-connect .clinician-card a']:
                    control=page.locator(selector).first;control.hover();control.focus();page.wait_for_timeout(220)
                    state=page.evaluate(CONTRAST);assert not state['failures'] and not state['unknown'],'Hover/focus contrast'
                row['navigation_and_interaction_states']='passed'
                recruiter=page.locator('.clinician-card a.btn');assert recruiter.get_attribute('href')=='mailto:hello@medlivo.com?subject=Rehabilitation%20Recruiter%20Inquiry'
                row['recruiter_target']='validated; no email sent'
                if not offline:
                    page.locator('.rd-hero a[href="#open-positions"]').click();page.wait_for_url('**/rehabilitation.html#open-positions');assert page.locator('#open-positions').is_visible()
                    page.locator('.client-card a.btn').click();page.wait_for_url('**/request-staff.html');assert page.locator('#staffingRequestForm').count()==1
                    page.goto(url,wait_until='networkidle');row['anchor_and_request_destination']='passed; form not submitted'
                    for i,target in enumerate(row['opportunity_links']):
                        page.goto(url,wait_until='networkidle');page.locator('.rd-opportunity-card a').nth(i).click();assert page.url==urljoin(args.base_url,target)
                    row['opportunity_routes']='passed; frontend handoff only'
            results.append(row);page.close()
        browser.close()
    report={'mode':'offline-render-only' if args.inline else 'public' if args.public else 'local-http','results':results,'failures':failures,'passed':not failures}
    (out/'rehab-layout.json').write_text(json.dumps(report,indent=2));print(json.dumps({'mode':report['mode'],'widths':len(results),'failures':failures,'passed':not failures},indent=2));assert not failures,'Rehab checks found defects'

if __name__=='__main__':main()
