"""Check Search Jobs rendering and frontend filters; never submit an application.
The retained job records are preview data, not a live ATS inventory.
Use --inline for offline rendering. --public also checks published source hashes.
"""
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
import argparse, base64, hashlib, json, mimetypes, shutil, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
WIDTHS=[320,360,375,390,540,768,820,1024,1040,1041,1100,1200,1280,1440,1920,2560,3440]
PHOTO='assets/images/embedded/e70494b94f9f610e514f.webp'
CONTRAST=(ROOT/'scripts/nursing_contrast_audit.js').read_text()
FILES=['search-jobs.html','assets/css/search-jobs.css','assets/css/jobs-responsive.css','assets/js/search-jobs-3.js',PHOTO]

def inline_html():
    s=BeautifulSoup((ROOT/'search-jobs.html').read_text(),'html.parser')
    for link in s.select('link[rel="stylesheet"]'):
        t=s.new_tag('style');t.string=(ROOT/link['href'].split('?')[0]).read_text();link.replace_with(t)
    for img in s.select('img[src]'):
        p=ROOT/img['src'].split('?')[0];img['src']='data:'+mimetypes.guess_type(p)[0]+';base64,'+base64.b64encode(p.read_bytes()).decode()
    for sc in s.select('script[src]'):
        sc.string=(ROOT/sc['src'].split('?')[0]).read_text();del sc['src']
    return str(s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base-url',default='http://127.0.0.1:8765/');ap.add_argument('--output-dir',required=True);ap.add_argument('--inline',action='store_true');ap.add_argument('--public',action='store_true');a=ap.parse_args()
    if a.inline and a.public:ap.error('Inline and public modes are mutually exclusive')
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);url=urljoin(a.base_url,'search-jobs.html');results=[];failures=[]
    if a.public:
        hashes=[]
        for name in FILES:
            req=urllib.request.Request(urljoin(a.base_url,name),headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=40) as response:data=response.read()
            actual=hashlib.sha256(data).hexdigest();expected=hashlib.sha256((ROOT/name).read_bytes()).hexdigest();hashes.append({'file':name,'matched':actual==expected,'actual':actual,'expected':expected})
        (out/'hashes.json').write_text(json.dumps(hashes,indent=2));assert all(x['matched'] for x in hashes),'Published source differs'
    offline=inline_html() if a.inline else None
    with sync_playwright() as pw:
        exe=shutil.which('google-chrome') or shutil.which('chromium');browser=pw.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
        for width in WIDTHS:
            page=browser.new_page(viewport={'width':width,'height':1080 if width>1040 else 844},device_scale_factor=1);errors=[];page.on('pageerror',lambda e,bucket=errors:bucket.append(str(e)))
            if offline:page.set_content(offline,wait_until='load');status=None
            else:resp=page.goto(url,wait_until='networkidle',timeout=60000);status=resp.status
            page.evaluate('document.fonts.ready')
            bad_images=page.evaluate('''async()=>{const bad=[];await Promise.all([...document.images].map(async e=>{try{await e.decode()}catch{bad.push(e.alt)}}));return bad}''')
            row=page.evaluate('''()=>{
              const clipped=[];document.querySelectorAll('main h1,main h2,main h3,main p,main label,main button,.division-copy strong,.job-pay,.job-detail strong').forEach(e=>{const r=e.getBoundingClientRect();if(r.width>1&&r.height>1&&(e.scrollWidth>e.clientWidth+2||r.left< -2||r.right>innerWidth+2))clipped.push(e.textContent.trim())});
              return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,clipped,first_job_top:document.querySelector('.job-card').getBoundingClientRect().top,canvas:document.querySelector('.jobs-hero-grid').getBoundingClientRect().width,divisions:[...document.querySelectorAll('.jobs-division-card')].map(e=>e.dataset.category),state_values:[...document.querySelectorAll('#filterState option')].map(e=>e.value).filter(Boolean),state_count:document.querySelectorAll('#filterState option').length-1,job_count:document.querySelectorAll('.job-card').length,sections:[...document.querySelectorAll('main>section')].map(e=>e.className),em_dash_absent:!document.querySelector('main').innerText.includes('—'),duplicate_sidebar_absent:!document.querySelector('.jobs-filters'),promotions_above_results_absent:!document.querySelector('.jobs-career-tools'),canonical_division_hidden:document.querySelector('#searchDivision').hidden};
            }''')
            contrast=page.evaluate(CONTRAST);(out/f'contrast-{width}.json').write_text(json.dumps(contrast,indent=2));row['contrast']={'minimum_ratio':contrast['minimum_ratio'],'paragraph_minimum':contrast['paragraph_minimum'],'failures':contrast['failures'],'unknown':contrast['unknown']}
            row.update(errors=errors,status=status,image_decode_errors=bad_images)
            checks={
              'http_ok':offline is not None or status==200,'no_overflow':not row['overflow'],'no_clipped_text':not row['clipped'],'no_script_errors':not errors,'images_decoded':not bad_images,
              'three_divisions':row['divisions']==['Nursing & Allied','Rehabilitation','Locum Tenens'],'fifty_unique_states':row['state_count']==len(set(row['state_values']))==50,
              'existing_preview_records':row['job_count']==8,'wide_alignment':width<1920 or abs(row['canvas']-1560)<2,
              'results_earlier':row['first_job_top']<820 if width>=1440 else row['first_job_top']<1100 if width==390 else row['first_job_top']<1400 if width==320 else True,
              'simple_flow':row['sections']==['jobs-hero','jobs-search-stage','jobs-results-section','jobs-support-strip','jobs-bottom-cta'],
              'truthful_preview':page.locator('[data-ats-preview-notice]').count()==1 and 'not live' in page.locator('[data-ats-preview-notice]').inner_text(),
              'integration_points':page.locator('[data-ats-results="pending"]').count()==1 and page.locator('[data-ats-action="quick-apply"]').count()==1 and page.locator('[data-ats-action="job-alerts"]').count()==1,
              'clean_copy':row['em_dash_absent'] and row['duplicate_sidebar_absent'] and row['promotions_above_results_absent'],
              'text_contrast':not contrast['failures'] and not contrast['unknown']}
            row['checks']=checks
            for name,ok in checks.items():
                if not ok:failures.append({'width':width,'check':name,'detail':row['clipped'] if name=='no_clipped_text' else None})
            if width in [390,1440,1920,2560]:
                page.screenshot(path=str(out/f'jobs-{width}-top.png'),animations='disabled')
                if width in [390,1920]:page.screenshot(path=str(out/f'jobs-{width}-full.png'),full_page=True,animations='disabled')
            if width in [390,1920]:
                # Division buttons are a pressed-button group, not incomplete ARIA tabs.
                page.locator('.division-locum').click();expect(page.locator('#searchDivision')).to_have_value('Locum Tenens');expect(page.locator('.division-locum')).to_have_attribute('aria-pressed','true')
                page.locator('#searchProfession').select_option('Nurse Practitioner / Physician Assistant');expect(page.locator('.job-card')).to_have_count(2)
                assert all('Practitioner' in x or 'Physician Assistant' in x for x in page.locator('.job-card').all_text_contents())
                page.locator('#searchProfession').select_option('Physician');expect(page.locator('.job-card')).to_have_count(5);assert not any('Physician Assistant' in x for x in page.locator('.job-card').all_text_contents())
                page.locator('#searchProfession').select_option('CRNA');expect(page.locator('#noResults')).to_be_visible();expect(page.locator('#jobList')).to_be_hidden()
                page.locator('#clearFilters').click();expect(page.locator('.job-card')).to_have_count(8)
                page.locator('#searchLocation').fill('Washington');page.locator('.jobs-search-button').click();expect(page.locator('.job-card')).to_have_count(2)
                page.locator('#clearFilters').click();page.locator('#filterState').select_option('CA');expect(page.locator('.job-card')).to_have_count(2)
                page.locator('#clearFilters').click();page.locator('#sortJobs').select_option('pay-high');assert 'OB/GYN' in page.locator('.job-card h3').first.inner_text()
                page.locator('.division-rehab').click();expect(page.locator('#searchDivision')).to_have_value('Rehabilitation');assert 'Physical Therapist' in page.locator('#searchProfession').inner_text()
                page.locator('.division-nursing').click();expect(page.locator('#searchDivision')).to_have_value('Nursing & Allied');assert 'Registered Nurse' in page.locator('#searchProfession').inner_text()
                page.locator('#divisionContext summary').click();expect(page.locator('#specialtyShortcuts')).to_be_visible();page.get_by_role('button',name='ICU',exact=True).click();expect(page.locator('#searchSpecialty')).to_have_value('ICU')
                page.locator('#clearFilters').click();page.locator('#divisionContext summary').click()
                # No mail client, telephone call, application or lead form is submitted.
                for link in page.locator('.jobs-email-options a,.jobs-bottom-actions a').all():assert link.get_attribute('href').startswith(('mailto:','tel:'))
                page.evaluate('window.scrollTo(0,0)')
                if width==390:page.locator('button.menu').click()
                trigger=page.get_by_role('button',name='Specialties',exact=False).first;trigger.click();expect(trigger).to_have_attribute('aria-expanded','true');page.keyboard.press('Escape');expect(trigger).to_have_attribute('aria-expanded','false')
                if width==390:page.locator('button.menu').click()
                for selector in ['.division-locum','.jobs-search-button','.job-apply','.jobs-bottom-actions a']:
                    page.locator(selector).first.hover();page.locator(selector).first.focus();page.wait_for_timeout(170)
                    state=page.evaluate(CONTRAST)
                    if state['failures'] or state['unknown']:failures.append({'width':width,'check':'interaction_contrast','selector':selector,'failures':state['failures'],'unknown':state['unknown']})
                row['frontend_filter_tests']='passed: divisions, NP/PA vs Physician, CRNA empty state, full state names, state selection, sort, shortcuts, reset'
                if not offline:
                    for query,div,prof in [('?division=Locum%20Tenens&profession=Physician','Locum Tenens','Physician'),('?division=Locum%20Tenens&profession=Nurse%20Practitioner%20%2F%20Physician%20Assistant','Locum Tenens','Nurse Practitioner / Physician Assistant'),('?division=Locum%20Tenens&profession=CRNA','Locum Tenens','CRNA'),('?profession=Rehabilitation','Rehabilitation',''),('?division=Rehabilitation&profession=Physical%20Therapist','Rehabilitation','Physical Therapist'),('?division=INVALID','','')]:
                        page.goto(url+query,wait_until='networkidle');expect(page.locator('#searchDivision')).to_have_value(div);expect(page.locator('#searchProfession')).to_have_value(prof)
                    page.goto(url+'?division=Locum%20Tenens&state=WA',wait_until='networkidle');expect(page.locator('#filterState')).to_have_value('WA');expect(page.locator('.job-card')).to_have_count(1)
                    row['url_routes']='passed: provider deep links, legacy Rehab, state, invalid input; no external submissions'
            results.append(row);page.close()
        browser.close()
    report={'mode':'offline' if a.inline else 'public' if a.public else 'local-http','results':results,'failures':failures,'passed':not failures};(out/'jobs-layout.json').write_text(json.dumps(report,indent=2));print(json.dumps({'mode':report['mode'],'widths':len(results),'failures':failures,'passed':not failures},indent=2));assert not failures,'Search Jobs checks found defects'

if __name__=='__main__':main()
