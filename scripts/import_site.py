"""One-time import from the locally checked-out, pinned recovered snapshot."""
import pathlib,json,hashlib,re,base64,shutil
from bs4 import BeautifulSoup
root=pathlib.Path('.');source=root/'_approved-source'
original=json.loads((source/'BUILD.json').read_text())
assert len(original['pages'])==11
assert not (root/'BUILD.json').exists(),'Initial import already completed. Never overwrite later edits.'
def digest(data):return hashlib.sha256(data).hexdigest()
def write(name,data):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data,str) else data)
shutil.copytree(source/'assets',root/'assets',dirs_exist_ok=True)
image_paths={digest(p.read_bytes()):p.as_posix() for p in (root/'assets').rglob('*') if p.is_file()}
shared={};pages={}
for name,provenance in original['pages'].items():
    raw=(source/name).read_bytes()
    assert digest(raw)==provenance['sha256'],'Unexpected source version: '+name
    text=raw.decode('utf-8');stem=pathlib.Path(name).stem
    visible_before=BeautifulSoup(text,'html.parser').get_text(' ',strip=True)
    assert '/Medlivo-Website/' not in text
    assert not re.search(r'<base\b',text,re.I)
    def local_image(match):
        kind=match.group(1);data=base64.b64decode(match.group(2),validate=True);key=digest(data)
        if key not in image_paths:
            ext={'svg+xml':'svg','jpeg':'jpg'}.get(kind,kind)
            path='assets/images/embedded/'+key[:20]+'.'+ext
            write(path,data);image_paths[key]=path
        return image_paths[key]
    text=re.sub(r'data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)',local_image,text)
    style_number=[0]
    def extract_style(match):
        style_number[0]+=1;css=match.group(1)
        assert not re.search(r'url\(',css,re.I),'Review CSS relative URLs before extraction'
        suffix='' if style_number[0]==1 else '-'+str(style_number[0])
        path='assets/css/'+stem+suffix+'.css';write(path,css)
        return '<link rel="stylesheet" href="'+path+'">'
    text=re.sub(r'<style\b[^>]*>(.*?)</style>',extract_style,text,flags=re.S|re.I)
    script_number=[0]
    def extract_script(match):
        attrs=match.group(1);code=match.group(2)
        if re.search(r'\bsrc\s*=|application/ld\+json|application/json',attrs,re.I):return match.group(0)
        script_number[0]+=1
        if 'const menu=document.querySelector' in code:filename='navigation-menu.js'
        elif 'const navDropdowns=' in code:filename='navigation-dropdowns.js'
        else:filename=stem+'-'+str(script_number[0])+'.js'
        path='assets/js/'+filename
        if path in shared:assert shared[path]==code,'Different shared script variants'
        shared[path]=code;write(path,code)
        return '<script src="'+path+'"></script>'
    text=re.sub(r'<script\b([^>]*)>(.*?)</script>',extract_script,text,flags=re.S|re.I)
    if name=='index.html' and 'assets/js/navigation-dropdowns.js' not in text:
        text=text.replace('</body>','<script src="assets/js/navigation-dropdowns.js"></script>\n</body>')
    assert visible_before==BeautifulSoup(text,'html.parser').get_text(' ',strip=True),'Visible copy changed: '+name
    write(name,text)
    pages[name]={'source_page_sha256':provenance['sha256'],'original_revision':provenance['commit'],'original_path':provenance['path'],'selection':provenance['selection'],'sha256':digest(text.encode())}
assert (root/'assets/js/navigation-dropdowns.js').is_file()
used=set();pending=list(original['pages'])
while pending:
    path=pending.pop();data=(root/path).read_bytes()
    if pathlib.Path(path).suffix not in ['.html','.css','.js','.svg','.json']:continue
    for asset in re.findall(r'assets/[A-Za-z0-9_./-]+\.(?:png|jpe?g|webp|svg|gif|css|js)',data.decode('utf-8')):
        assert (root/asset).is_file(),'Missing asset '+asset
        if asset not in used:used.add(asset);pending.append(asset)
for asset in (root/'assets').rglob('*'):
    if asset.is_file() and asset.as_posix() not in used:asset.unlink()
for directory in sorted((root/'assets').rglob('*'),reverse=True):
    if directory.is_dir() and not any(directory.iterdir()):directory.rmdir()
manifest={'build_id':'medlivo-final-20260928-01','repository':'pks-alt/Medlivo-Website-Final','source_policy':'One root version per page, all assets local. No runtime or ongoing build dependency on the old repository.','initial_import_commit':'ec962a7bb7850cd6bfe7805664ca15a4261b508e','transformations':['Moved inline page styles and scripts into local assets without changing their cascade or execution order.','Decoded embedded images to byte-identical local files.','Connected the existing homepage dropdown click handler. No visual redesign.'],'pages':pages,'files':{}}
for path in sorted([root/n for n in pages]+[p for p in (root/'assets').rglob('*') if p.is_file()]):manifest['files'][path.as_posix()]=digest(path.read_bytes())
write('BUILD.json',json.dumps(manifest,indent=2)+'\n')
write('.nojekyll','')
write('.gitignore','/_approved-source/\n/_site/\n/verification/\n__pycache__/\n')
print(json.dumps({'pages':len(pages),'required_asset_files':len(used),'source_hashes':'all matched','visible_copy':'unchanged','old_preview_folders_copied':False},indent=2))
