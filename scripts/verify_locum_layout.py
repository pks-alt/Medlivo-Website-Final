"""Verify Locum presentation and route handoffs, without submitting a form/email.

--inline performs offline rendering only. Default and --public use real HTTP.
Existing job search records remain a frontend sample, not verified ATS inventory.
"""
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
import argparse, base64, hashlib, json, mimetypes, shutil, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [320,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]
SECTIONS = ['ld-hero','ld-coverage','ld-providers','ld-settings','ld-recruiting','ld-readiness','ld-opportunities','ld-connect']
SETTINGS = ['Hospital & Inpatient Care','Emergency & Urgent Care','Surgery, Anesthesia & Procedural Care','Primary Care & Specialty Practice']
MODELS = ['Per Diem Coverage','Travel Locum Assignments','Permanent / Full-Time Hiring']
PHOTO = 'assets/images/embedded/40d75589766d58e62b17.webp'
CONTRAST = (ROOT/'scripts/nursing_contrast_audit.js').read_text().replace('.nd-sr-only','.ld-sr-only')
RECRUITER = 'mailto:hello@medlivo.com?subject=Locum%20Tenens%20%26%20Permanent%20Placement%20Recruiter%20Inquiry'
PROFESSIONS = ['Physician','Nurse Practitioner / Physician Assistant','CRNA']

def inline_html():
    soup = BeautifulSoup((ROOT/'locum-tenens.html').read_text(), 'html.parser')
    for link in soup.select('link[rel="stylesheet"]'):
        tag=soup.new_tag('style'); tag.string=(ROOT/link['href'].split('?')[0]).read_text(); link.replace_with(tag)
    for img in soup.select('img[src]'):
        path=ROOT/img['src'].split('?')[0]
        img['src']='data:'+mimetypes.guess_type(path)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()
    for script in soup.select('script[src]'):
        script.string=(ROOT/script['src'].split('?')[0]).read_text(); del script['src']
    return str(soup)

def main():
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8765/');p.add_argument('--output-dir',required=True);p.add_argument('--inline',action='store_true');p.add_argument('--public',action='store_true');args=p.parse_args()
    if args.public and args.inline:p.error('Public and inline modes are mutually exclusive')
    out=Path(args.output_dir);out.mkdir(exist_ok=True,parents=True);url=urljoin(args.base_url,'locum-tenens.html');failures=[];results=[]
    if args.public:
        hashes=[]
        for name in ['locum-tenens.html','assets/css/locum-tenens.css','assets/css/locum-responsive.css',PHOTO,'assets/js/request-staff-1.js','assets/js/search-jobs-3.js','request-staff.html','search-jobs.html']:
            req=urllib.request.Request(urljoin(args.base_url,name),headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=40) as r:data=r.read()
            actual=hashlib.sha256(data).hexdigest();expected=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            hashes.append({'file':name,'actual':actual,'expected':expected,'matched':actual==expected})
        (out/'hashes.json').write_text(json.dumps(hashes,indent=2));assert all(x['matched'] for x in hashes),'Published Locum files differ from tested source'
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
              const clipped=[];document.querySelectorAll('main h1,main h2,main h3,main h4,main p,main a.btn,.ld-role-tag,.ld-specialty-list li').forEach(e=>{if(e.classList.contains('ld-sr-only'))return;const r=e.getBoundingClientRect();if(r.width>2&&(e.scrollWidth>e.clientWidth+2||r.right>innerWidth+2||r.left< -2))clipped.push(e.textContent.trim())});
              return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,clipped_text:clipped,grid:rect('.ld-hero-grid'),copy:rect('.ld-hero-copy'),photo:rect('.ld-hero-photo'),sections:[...document.querySelectorAll('main>section')].map(e=>e.className),section_heights:[...document.querySelectorAll('main>section')].map(e=>e.getBoundingClientRect().height),care_settings:[...document.querySelectorAll('.ld-setting-row h3')].map(e=>e.textContent.trim()),settings_height:document.querySelector('#care-settings').getBoundingClientRect().height,models:[...document.querySelectorAll('.ld-coverage-card h3')].map(e=>e.textContent.trim()),role_tags:[...document.querySelectorAll('.ld-role-tag')].map(e=>e.textContent.trim()),what_matters:document.querySelectorAll('.ld-setting-factors').length,recruiting_steps:document.querySelectorAll('.ld-process-step').length,readiness_items:document.querySelectorAll('.ld-ready-item').length,opportunity_cards:document.querySelectorAll('.ld-opportunity-card').length,opportunity_links:[...document.querySelectorAll('.ld-opportunity-card a')].map(e=>e.getAttribute('href')),photo_width:document.querySelector('.ld-hero-photo img').naturalWidth,em_dash_absent:!document.querySelector('main').innerText.includes('—'),no_unrelated_claim:!document.querySelector('main').innerText.includes('20+'),extra_nav_absent:!document.querySelector('.section-nav,.page-nav')};
            }''')
            contrast=page.evaluate(CONTRAST);(out/f'contrast-{width}.json').write_text(json.dumps(contrast,indent=2))
            if contrast['failures'] or contrast['unknown']:failures.append({'width':width,'contrast':contrast['failures'],'unresolved':contrast['unknown']})
            if any(x['font_size']<16 for x in contrast['results'] if x['required']==7):failures.append({'width':width,'error':'Body text below 16px'})
            row.update(status=status,errors=errors,image_decode_errors=decode,contrast={'checked':contrast['text_elements'],'minimum_ratio':contrast['minimum_ratio'],'paragraph_minimum':contrast['paragraph_minimum'],'passed':not contrast['failures'] and not contrast['unknown']})
            checks={
              'approved_headline':page.locator('h1').inner_text()=='Locum coverage and permanent hiring, built around your practice.',
              'correct_sections':row['sections']==SECTIONS,'three_models':row['models']==MODELS,'four_settings':row['care_settings']==SETTINGS,
              'content_counts':[row['what_matters'],row['recruiting_steps'],row['readiness_items'],row['opportunity_cards']]==[4,4,4,3],
              'four_provider_groups':row['role_tags']==['MD / DO','NP','PA','CRNA'],
              'specialty_coverage':page.locator('.ld-specialty-list li').all_text_contents()==['Primary Care','Hospitalist Medicine','Emergency Medicine','Behavioral Health','Surgery','Critical Care','Urgent Care','Women’s Health','Cardiology','Orthopedics','Anesthesia'],
              'ongoing_support': 'schedule changes, extensions and assignment questions' in page.locator('.ld-support-note').inner_text(),
              'provider_clarity': 'before you commit' in page.locator('.ld-opportunities .ld-section-head').inner_text(),
              'program_support': 'MSP and VMS' in page.locator('.ld-recruiting .ld-section-head').inner_text(),
              'permanent_is_direct_hire':'join your organization directly' in page.locator('.ld-coverage-card').nth(2).inner_text(),
              'readable_image':row['photo_width']==1800 and not decode,
              'wide_canvas':width<1920 or abs(row['grid']['width']-1560)<2,
              'hero_not_overlapping':row['photo']['y']>=row['copy']['bottom']-1 if width<=1040 else row['photo']['x']>=row['copy']['right']-1,
              'compact_settings':row['settings_height']<=850 if width>=1440 else (row['settings_height']<=1400 if width==390 else True),
              'no_clipping':not row['overflow'] and not row['clipped_text'],'no_script_errors':not errors,
              'editorial':row['em_dash_absent'] and row['extra_nav_absent'] and row['no_unrelated_claim'],'http_ok':offline is not None or status==200}
            row['checks']=checks
            for name,ok in checks.items():
                if not ok:failures.append({'width':width,'check':name})
            if width in [390,1041,1440,1920,2560]:
                page.screenshot(path=str(out/f'locum-{width}-top.png'),animations='disabled')
                if width in [390,1920]:
                    page.screenshot(path=str(out/f'locum-{width}-full.png'),full_page=True,animations='disabled')
                    page.locator('#care-settings').screenshot(path=str(out/f'care-settings-{width}.png'),animations='disabled')
            if width in [390,1920]:
                page.evaluate('window.scrollTo(0,0)')
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first;trigger.click();assert trigger.get_attribute('aria-expanded')=='true'
                expanded=page.evaluate(CONTRAST);assert not expanded['failures'] and not expanded['unknown'],'Expanded navigation contrast'
                page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
                if width==390:page.locator('button.menu').click()
                for selector in ['.ld-hero .ld-button-light','.ld-opportunity-card a','.ld-connect .clinician-card a']:
                    control=page.locator(selector).first;control.hover();control.focus();page.wait_for_timeout(220)
                    state=page.evaluate(CONTRAST);assert not state['failures'] and not state['unknown'],'Hover/focus contrast'
                row['navigation_and_interaction_states']='passed'
                assert page.locator('.clinician-card a.btn').get_attribute('href')==RECRUITER
                row['recruiter_target']='validated; no email sent'
                if not offline:
                    page.locator('.ld-hero a[href="#open-positions"]').click();page.wait_for_url('**/locum-tenens.html#open-positions');assert page.locator('#open-positions').is_visible()
                    page.locator('.client-card a.btn').click();page.wait_for_url('**/request-staff.html?division=Locum%20Tenens');assert page.locator('#staffingRequestForm').count()==1
                    assert page.locator('#division').input_value()=='Locum Tenens';row['request_division_prefill']='passed; form not submitted'
                    for i,target in enumerate(row['opportunity_links']):
                        page.goto(url,wait_until='networkidle');page.locator('.ld-opportunity-card a').nth(i).click();assert page.url==urljoin(args.base_url,target)
                        assert page.locator('#searchDivision').input_value()=='Locum Tenens'
                        assert page.locator('#searchProfession').input_value()==PROFESSIONS[i]
                        cards=page.locator('.job-card').all_text_contents()
                        if i==0:assert not any('Physician Assistant' in c or 'Nurse Practitioner' in c for c in cards)
                        if i==1:assert all('Physician Assistant' in c or 'Nurse Practitioner' in c for c in cards)
                        if i==2:assert all('CRNA' in c or 'Nurse Anesthetist' in c for c in cards)
                    row['opportunity_routes']='passed with selected provider filters; existing frontend dataset, not verified live inventory'
                    page.goto(urljoin(args.base_url,'request-staff.html'),wait_until='networkidle');assert page.locator('#division').input_value()==''
                    page.goto(urljoin(args.base_url,'request-staff.html?division=INVALID'),wait_until='networkidle');assert page.locator('#division').input_value()==''
                    page.goto(urljoin(args.base_url,'search-jobs.html?division=Rehabilitation&profession=Physical%20Therapist'),wait_until='networkidle');assert page.locator('#searchDivision').input_value()=='Rehabilitation';assert page.locator('#searchProfession').input_value()=='Physical Therapist'
                    row['unrelated_routes']='unscoped request, invalid division and existing Rehab search preserved'
            results.append(row);page.close()
        browser.close()
    report={'mode':'offline-render-only' if args.inline else 'public' if args.public else 'local-http','results':results,'failures':failures,'passed':not failures}
    (out/'locum-layout.json').write_text(json.dumps(report,indent=2));print(json.dumps({'mode':report['mode'],'widths':len(results),'failures':failures,'passed':not failures},indent=2));assert not failures,'Locum checks found defects'

if __name__=='__main__':main()
