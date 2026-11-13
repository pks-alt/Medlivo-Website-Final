(function(){
  if(window.__medlivoAgentLoaded)return;window.__medlivoAgentLoaded=true;
  const API_BASE='https://medlivo-ai-agent-397967014447.us-west1.run.app';
  const KEY='medlivoAgentChatV2';
  const CHIPS=['I need healthcare staff','Find me a job','What does Medlivo do?'];
  const WELCOME='Hi, I’m Ask Medlivo. I can search our open jobs, send a staffing request to the right team, or answer questions about Medlivo. What can I help with?';

  function ensureMarkup(){
    if(document.querySelector('[data-medlivo-agent-panel]'))return;
    const wrap=document.createElement('div');
    wrap.innerHTML='<button class="medlivo-agent-launcher" type="button" data-medlivo-agent-launcher aria-expanded="false" aria-controls="medlivo-agent-panel"><span class="medlivo-agent-launcher-dot" aria-hidden="true"></span><span class="medlivo-agent-launcher-label"><span>Ask Medlivo<small>Jobs &amp; staffing help</small></span></span><span class="medlivo-agent-launcher-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M7 18.5 3.5 21v-5A8 8 0 1 1 7 18.5Z"/><path d="M8 10h8M8 14h5"/></svg></span></button>'+
    '<div class="medlivo-agent-panel" id="medlivo-agent-panel" data-medlivo-agent-panel role="dialog" aria-label="Ask Medlivo"><div class="medlivo-agent-head"><div class="medlivo-agent-brand"><div class="medlivo-agent-mark" aria-hidden="true">M</div><div class="medlivo-agent-title"><strong>Ask Medlivo</strong><span>AI assistant · jobs and staffing</span></div></div><div class="medlivo-agent-head-actions"><button class="medlivo-agent-new" type="button" data-agent-new aria-label="Start a new chat">New chat</button><button class="medlivo-agent-close" type="button" data-agent-close aria-label="Close Ask Medlivo">×</button></div></div><div class="medlivo-agent-body" data-agent-body aria-live="polite"></div><form class="medlivo-agent-foot" data-agent-form><div class="medlivo-agent-input-row"><input class="medlivo-agent-input" type="text" data-agent-input maxlength="1000" autocomplete="off" placeholder="Type a message" aria-label="Message Ask Medlivo"><button class="medlivo-agent-send" type="submit" data-agent-send aria-label="Send message">Send</button></div><div class="medlivo-agent-note">AI assistant for staffing and jobs. Please do not share patient information.</div></form></div>';
    while(wrap.firstChild)document.body.appendChild(wrap.firstChild);
  }
  function init(){
    ensureMarkup();
    const panel=document.querySelector('[data-medlivo-agent-panel]');
    const launcher=document.querySelector('[data-medlivo-agent-launcher]');
    const body=panel.querySelector('[data-agent-body]');
    const form=panel.querySelector('[data-agent-form]');
    const input=panel.querySelector('[data-agent-input]');
    const closeBtn=panel.querySelector('[data-agent-close]');
    let newBtn=panel.querySelector('[data-agent-new]');
    let history=[],busy=false,thinking=null;

    function track(e,d){const p=Object.assign({event:e,source:'ask_medlivo'},d||{});window.dataLayer=window.dataLayer||[];window.dataLayer.push(p)}
    function save(){try{sessionStorage.setItem(KEY,JSON.stringify(history.slice(-30)))}catch(e){}}
    function load(){try{const h=JSON.parse(sessionStorage.getItem(KEY)||'[]');return Array.isArray(h)?h:[]}catch(e){return[]}}
    function scroll(){body.scrollTop=body.scrollHeight}
    function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n}
    function bubble(text,who){const row=el('div','medlivo-agent-message '+who);row.appendChild(el('div','medlivo-agent-bubble',text));body.appendChild(row);scroll();return row}
    function chips(list){const w=el('div','medlivo-agent-options');list.forEach(t=>{const b=el('button','medlivo-agent-option',t);b.type='button';b.addEventListener('click',()=>{w.remove();send(t)});w.appendChild(b)});body.appendChild(w);scroll()}
    function link(label,href,secondary){const a=el('a','medlivo-agent-link'+(secondary?' secondary':''),label);a.href=href;return a}
    function jobCards(jobs){
      jobs.forEach(j=>{
        const c=el('div','medlivo-agent-card medlivo-agent-job');
        c.appendChild(el('strong','',j.title||j.profession||'Open role'));
        const loc=[j.city,j.state].filter(Boolean).join(', ');
        const meta=[j.division,loc,j.specialty,j.contract_weeks?j.contract_weeks+' wks':'',j.shift,j.start_date?'Starts '+j.start_date:''].filter(Boolean).join(' · ');
        if(meta)c.appendChild(el('p','',meta));
        const row=el('div','medlivo-agent-card-actions');
        row.appendChild(link('Talk to a recruiter','mailto:hello@medlivo.com?subject='+encodeURIComponent('Interested in job '+(j.id||'')+' - '+(j.title||''))));
        c.appendChild(row);body.appendChild(c);
      });
      if(jobs.length){const r=el('div','medlivo-agent-card-actions');r.style.margin='0 0 14px';r.appendChild(link('See all jobs','search-jobs.html',true));body.appendChild(r)}
      scroll();
    }
    function actions(list){const c=el('div','medlivo-agent-card');const r=el('div','medlivo-agent-card-actions');list.forEach((a,i)=>r.appendChild(link(a.label,a.href,i>0)));c.appendChild(r);body.appendChild(c);scroll()}
    function showThinking(){thinking=el('div','medlivo-agent-message bot');thinking.innerHTML='<div class="medlivo-agent-thinking"><i></i><i></i><i></i></div>';body.appendChild(thinking);scroll()}
    function hideThinking(){if(thinking){thinking.remove();thinking=null}}
    function setBusy(v){busy=v;input.disabled=v;form.querySelector('[data-agent-send]').disabled=v;if(!v)input.focus()}

    async function send(text){
      const v=(text||'').trim();if(!v||busy)return;
      input.value='';bubble(v,'user');history.push({role:'user',content:v});save();
      setBusy(true);showThinking();
      let data=null;
      try{
        const ctl=new AbortController(),t=setTimeout(()=>ctl.abort(),30000);
        const r=await fetch(API_BASE+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:history.slice(-20),page:location.pathname}),signal:ctl.signal});
        clearTimeout(t);if(r.ok)data=await r.json();
      }catch(e){}
      hideThinking();setBusy(false);
      if(!data||!data.message){
        bubble('I’m having trouble connecting right now. You can reach the team directly at hello@medlivo.com or 855-633-5486.','bot');
        actions([{label:'Request Staff',href:'request-staff.html'},{label:'Search Jobs',href:'search-jobs.html'},{label:'Call 855-633-5486',href:'tel:+18556335486'}]);
        return;
      }
      history.push({role:'assistant',content:data.message});save();
      bubble(data.message,'bot');
      if(data.jobs&&data.jobs.length){track('ask_medlivo_jobs_shown',{count:data.jobs.length});jobCards(data.jobs)}
      if(data.actions&&data.actions.length)actions(data.actions);
      if(data.lead){track('ask_medlivo_lead_submitted',{type:data.lead.type,lead_id:data.lead.leadId});
        const c=el('div','medlivo-agent-card');c.appendChild(el('strong','','Sent to Medlivo'));c.appendChild(el('p','','Reference '+data.lead.leadId+(data.lead.team?' · '+data.lead.team:'')));body.appendChild(c);scroll()}
    }
    function render(){
      body.innerHTML='';
      if(!history.length){bubble(WELCOME,'bot');chips(CHIPS);return}
      history.forEach(m=>bubble(m.content,m.role==='user'?'user':'bot'));
      chips(['Search jobs','Request staff']);
    }
    function open(){panel.classList.add('open');launcher.setAttribute('aria-expanded','true');if(!body.children.length){history=load();render();track('ask_medlivo_opened')}setTimeout(()=>input.focus(),100)}
    function close(){panel.classList.remove('open');launcher.setAttribute('aria-expanded','false');launcher.focus()}
    launcher.addEventListener('click',()=>panel.classList.contains('open')?close():open());
    closeBtn.addEventListener('click',close);
    if(newBtn)newBtn.addEventListener('click',()=>{if(busy)return;history=[];save();render()});
    form.addEventListener('submit',e=>{e.preventDefault();send(input.value)});
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&panel.classList.contains('open'))close()});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
