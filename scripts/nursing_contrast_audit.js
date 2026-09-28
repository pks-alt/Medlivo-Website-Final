() => {
  // Computed CSS colors, not antialiased glyph pixels. Fail closed on an
  // image/gradient surface instead of guessing a flat background behind text.
  const parse = value => {
    const v = value.match(/[\d.]+/g);
    if (!v || !value.startsWith('rgb')) throw new Error('Unsupported color: ' + value);
    return [Number(v[0]), Number(v[1]), Number(v[2]), v[3] === undefined ? 1 : Number(v[3])];
  };
  const blend = (fg,bg) => fg.slice(0,3).map((v,i)=>v*fg[3]+bg[i]*(1-fg[3])).concat(1);
  const lum = rgb => rgb.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
  const elements = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n=walker.currentNode,e=n.parentElement;
    if(!n.textContent.trim() || e.closest('script,style,.nd-sr-only,[hidden],[aria-hidden="true"]')) continue;
    const r=e.getBoundingClientRect(), s=getComputedStyle(e);
    if(r.width>1 && r.height>1 && s.display!=='none' && s.visibility==='visible') elements.add(e);
  }
  const results=[],failures=[],unknown=[];
  for (const e of elements) {
    const s=getComputedStyle(e),layers=[];let opaque=false,opacity=1,reasons=[];
    for(let a=e;a;a=a.parentElement){
      const st=getComputedStyle(a);opacity*=Number(st.opacity);
      if(!opaque){
        if(st.backgroundImage!=='none') reasons.push('Non-flat background: '+a.className);
        layers.push(parse(st.backgroundColor));
        if(layers[layers.length-1][3]===1) opaque=true;
      }
      if(st.filter!=='none'||st.mixBlendMode!=='normal') reasons.push('Filter or blending on text');
    }
    if(opacity===0) continue;
    let bg=[255,255,255,1];for(const layer of layers.reverse())bg=blend(layer,bg);
    const color=parse(s.color);color[3]*=opacity;const fg=blend(color,bg);
    const a=lum(fg),b=lum(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    const paragraph=!!e.closest('main p');
    const item={text:[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).join(' ').slice(0,160),selector:e.tagName.toLowerCase()+(e.className?'.'+String(e.className).trim().replace(/\s+/g,'.'):''),foreground:s.color,background:bg.slice(0,3),font_size:parseFloat(s.fontSize),ratio,required:paragraph?7:4.5};
    if(reasons.length){item.manual_review=reasons;unknown.push(item);}
    else if(ratio<item.required) failures.push(item);
    results.push(item);
  }
  return {text_elements:results.length,minimum_ratio:Math.min(...results.filter(x=>!x.manual_review).map(x=>x.ratio)),paragraph_minimum:Math.min(...results.filter(x=>x.required===7&&!x.manual_review).map(x=>x.ratio)),failures,unknown,results};
}
