"""Compare the standalone import to the approved local snapshot.

No layout or visible-copy change is allowed. Chromium occasionally rasterizes
28-37 rounded-button edge pixels differently in its composited sticky header.
After inspecting saved before/after images, allow at most 100 changed pixels,
only inside the first 100px of the header, only with identical DOM geometry.
The report retains exact pixel counts; this is not called pixel-identical.
"""
import io
import json
import pathlib
import shutil
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

OUT = pathlib.Path('verification')
OUT.mkdir(exist_ok=True)
results = []
with sync_playwright() as p:
    exe = shutil.which('google-chrome') or shutil.which('chromium')
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **({'executable_path': exe} if exe else {}))
    for width in [1440, 390]:
        for name in ['index.html', 'workforce-solutions.html', 'nursing-allied.html', 'rehabilitation.html']:
            screenshots = []
            geometry = []
            for label, prefix in [('before', '_approved-source/'), ('after', '')]:
                page = browser.new_page(viewport={'width': width, 'height': 1000 if width == 1440 else 844}, device_scale_factor=1, reduced_motion='reduce')
                page.goto('http://127.0.0.1:8765/' + prefix + name, wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                page.evaluate('Promise.all(Array.from(document.images).map(i=>i.decode().catch(()=>{})))')
                page.wait_for_timeout(500)
                geometry.append(page.locator('main h1, main h2, main h3, main section, header, footer').evaluate_all('(es)=>es.map(e=>({tag:e.tagName,text:e.matches("h1,h2,h3")?e.textContent:null,x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}))'))
                data = page.screenshot(full_page=True, animations='disabled', caret='hide')
                image = Image.open(io.BytesIO(data)).convert('RGB')
                screenshots.append(image)
                (OUT / (name.removesuffix('.html') + '-' + str(width) + '-' + label + '.png')).write_bytes(data)
                page.close()
            before, after = screenshots
            same_size = before.size == after.size
            diff = ImageChops.difference(before, after) if same_size else None
            bounds = diff.getbbox() if diff else None
            same_layout = geometry[0] == geometry[1]
            row = {'page': name, 'width': width, 'same_dimensions': same_size, 'same_layout': same_layout, 'pixel_identical': same_size and bounds is None, 'difference_bounds': bounds, 'changed_pixels': 0, 'pixel_count': before.width * before.height}
            if bounds:
                diff.crop(bounds).save(OUT / (name.removesuffix('.html') + '-' + str(width) + '-difference.png'))
                row['changed_pixels'] = sum(1 for rgb in diff.getdata() if rgb != (0, 0, 0))
            if not same_layout:
                (OUT / (name.removesuffix('.html') + '-' + str(width) + '-geometry.json')).write_text(json.dumps(geometry, indent=2))
            header_edge_noise = same_size and same_layout and bounds is not None and bounds[3] <= 100 and row['changed_pixels'] <= 100
            row['header_edge_rasterization_only'] = header_edge_noise
            row['passed'] = same_layout and (row['pixel_identical'] or header_edge_noise)
            results.append(row)
    browser.close()
(OUT / 'design-comparison.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
assert all(r['passed'] for r in results), 'Inspect saved before/after evidence before committing the import.'
