
(function(){
  const panel=document.querySelector('[data-medlivo-agent-panel]');
  const launcher=document.querySelector('[data-medlivo-agent-launcher]');
  if(!panel||!launcher)return;

  const body=panel.querySelector('[data-agent-body]');
  const form=panel.querySelector('[data-agent-form]');
  const input=panel.querySelector('[data-agent-input]');
  const close=panel.querySelector('[data-agent-close]');
  const send=panel.querySelector('[data-agent-send]');
  const state={mode:'home',step:null,data:{}};
  let thinkingNode=null;

  const divisions=['Nursing & Allied','Rehabilitation','Locum Tenens'];

  function scrollBottom(){body.scrollTop=body.scrollHeight}
  function addMessage(text,who='bot'){
    const row=document.createElement('div');
    row.className='medlivo-agent-message '+who;
    const bubble=document.createElement('div');
    bubble.className='medlivo-agent-bubble';
    bubble.textContent=text;
    row.appendChild(bubble);
    body.appendChild(row);
    scrollBottom();
    return row;
  }
  function addOptions(options){
    const wrap=document.createElement('div');
    wrap.className='medlivo-agent-options';
    options.forEach(opt=>{
      const btn=document.createElement('button');
      btn.type='button';
      btn.className='medlivo-agent-option';
      btn.textContent=opt.label;
      btn.addEventListener('click',()=>opt.onClick(btn));
      wrap.appendChild(btn);
    });
    body.appendChild(wrap);
    scrollBottom();
    return wrap;
  }
  function addCard(title,text,actions=[]){
    const card=document.createElement('div');
    card.className='medlivo-agent-card';
    const strong=document.createElement('strong');
    strong.textContent=title;
    card.appendChild(strong);
    if(text){
      const p=document.createElement('p');
      p.textContent=text;
      card.appendChild(p);
    }
    if(actions.length){
      const row=document.createElement('div');
      row.className='medlivo-agent-card-actions';
      actions.forEach((a,i)=>{
        const link=document.createElement('a');
        link.className='medlivo-agent-link'+(i?' secondary':'');
        link.href=a.href;
        link.textContent=a.label;
        if(a.target)link.target=a.target;
        row.appendChild(link);
      });
      card.appendChild(row);
    }
    body.appendChild(card);
    scrollBottom();
  }
  function showThinking(){
    thinkingNode=document.createElement('div');
    thinkingNode.className='medlivo-agent-message bot';
    thinkingNode.innerHTML='<div class="medlivo-agent-thinking"><i></i><i></i><i></i></div>';
    body.appendChild(thinkingNode);
    scrollBottom();
  }
  function hideThinking(){if(thinkingNode){thinkingNode.remove();thinkingNode=null}}
  function reset(){
    state.mode='home';state.step=null;state.data={};
    body.innerHTML='';
    addMessage('Hi, I’m here to help you reach the right Medlivo team.');
    addMessage('What brings you to Medlivo today?');
    addOptions([
      {label:'I need healthcare staff',onClick:startClient},
      {label:'I’m looking for a job',onClick:startClinician},
      {label:'I have a question',onClick:startQuestion}
    ]);
  }
  function startClient(){
    state.mode='client';state.step='division';state.data={};
    addMessage('I need healthcare staff','user');
    addMessage('Which Medlivo team is closest to your need?');
    addOptions(divisions.map(d=>({label:d,onClick:()=>chooseClientDivision(d)})).concat([
      {label:'Not sure',onClick:()=>chooseClientDivision('Not sure')}
    ]));
  }
  function chooseClientDivision(division){
    state.data.division=division;
    addMessage(division,'user');
    state.step='role';
    addMessage('What role or specialty do you need?');
    input.placeholder='Example: ICU RN, PT, Urologist';
    input.focus();
  }
  function clientNext(value){
    if(state.step==='role'){
      state.data.role=value;state.step='location';
      addMessage('What city and state is the coverage for?');
      input.placeholder='Example: Tacoma, WA';
    }else if(state.step==='location'){
      state.data.location=value;state.step='timing';
      addMessage('When do you need the clinician or provider to start?');
      input.placeholder='Example: ASAP or October 15';
    }else if(state.step==='timing'){
      state.data.timing=value;state.step='count';
      addMessage('How many people do you need?');
      input.placeholder='Example: 2';
    }else if(state.step==='count'){
      state.data.count=value;finishClient();
    }
  }
  function finishClient(){
    const d=state.data;
    const params=new URLSearchParams();
    if(d.division&&d.division!=='Not sure')params.set('division',d.division);
    if(d.role)params.set('role',d.role);
    if(d.location)params.set('location',d.location);
    if(d.timing)params.set('start',d.timing);
    if(d.count)params.set('count',d.count);
    addMessage('That gives the Medlivo team a strong starting point.');
    addCard(
      'Continue your staffing request',
      [d.division,d.role,d.location,d.timing,d.count?d.count+' needed':null].filter(Boolean).join(' · '),
      [
        {label:'Continue to Request Staff',href:'request-staff.html?'+params.toString()},
        {label:'Call 855-633-5486',href:'tel:+18556335486'}
      ]
    );
    addMessage('You can also keep typing if you want to add context before you continue.');
    state.step='client-free';
    input.placeholder='Add schedule, facility type, or other details';
  }
  function startClinician(){
    state.mode='clinician';state.step='division';state.data={};
    addMessage('I’m looking for a job','user');
    addMessage('Which area best matches your profession?');
    addOptions(divisions.map(d=>({label:d,onClick:()=>chooseClinicianDivision(d)})));
  }
  function chooseClinicianDivision(division){
    state.data.division=division;
    addMessage(division,'user');
    state.step='profession';
    addMessage('What is your profession or specialty?');
    input.placeholder='Example: ICU RN, Physical Therapist, CRNA';
    input.focus();
  }
  function clinicianNext(value){
    if(state.step==='profession'){
      state.data.profession=value;state.step='location';
      addMessage('Where would you like to work?');
      input.placeholder='City, state, or states';
    }else if(state.step==='location'){
      state.data.location=value;finishClinician();
    }
  }
  function finishClinician(){
    const d=state.data;
    const params=new URLSearchParams();
    if(d.division)params.set('division',d.division);
    if(d.profession)params.set('specialty',d.profession);
    if(d.location)params.set('location',d.location);
    addMessage('I can take you directly into a search with those details.');
    addCard(
      'Explore matching opportunities',
      [d.division,d.profession,d.location].filter(Boolean).join(' · '),
      [
        {label:'Search Jobs',href:'search-jobs.html?'+params.toString()},
        {label:'Ask a Recruiter',href:'mailto:hello@medlivo.com?subject=Healthcare%20Job%20Search'}
      ]
    );
    state.step='clinician-free';
    input.placeholder='Ask about jobs, locations, or the process';
  }
  function startQuestion(){
    state.mode='question';state.step='question';
    addMessage('I have a question','user');
    addMessage('Ask me about Medlivo, our staffing divisions, jobs, credentialing, or how to reach the right team.');
    input.placeholder='Type your question';
    input.focus();
  }

  function answerKnownQuestion(text){
    const q=text.toLowerCase();
    if(/medical advice|diagnos|symptom|patient treatment/.test(q)){
      return {text:'I can help with staffing, jobs, and Medlivo services, but I can’t provide medical advice or collect patient information.',actions:[{label:'Contact Medlivo',href:'contact.html'}]};
    }
    if(/nursing|allied/.test(q)){
      return {text:'Medlivo’s Nursing & Allied team supports nursing and allied health staffing across hospital, clinic, procedural, diagnostic, post-acute, and other care settings.',actions:[{label:'Nursing & Allied',href:'nursing-allied.html'},{label:'Search Jobs',href:'search-jobs.html?division=Nursing%20%26%20Allied'}]};
    }
    if(/rehab|physical therap|occupational therap|speech|slp|pt\b|ot\b/.test(q)){
      return {text:'Medlivo’s Rehabilitation division focuses on Physical Therapy, Occupational Therapy, and Speech-Language Pathology across multiple care settings.',actions:[{label:'Rehabilitation',href:'rehabilitation.html'},{label:'Search Rehab Jobs',href:'search-jobs.html?division=Rehabilitation'}]};
    }
    if(/locum|physician|provider|crna|nurse practitioner|physician assistant/.test(q)){
      return {text:'Medlivo’s Locum Tenens team supports physicians and advanced practice providers for per diem, travel locum, and permanent hiring needs.',actions:[{label:'Locum Tenens',href:'locum-tenens.html'},{label:'Search Provider Jobs',href:'search-jobs.html?division=Locum%20Tenens'}]};
    }
    if(/job|career|opening|work/.test(q)){
      return {text:'You can search current Medlivo opportunities by division, profession, specialty, and location.',actions:[{label:'Search Jobs',href:'search-jobs.html'}]};
    }
    if(/staff|coverage|hire|need people|need talent/.test(q)){
      return {text:'Medlivo supports healthcare organizations across Nursing & Allied, Rehabilitation, and Locum Tenens. I can help you start a staffing request now.',actions:[{label:'Request Staff',href:'request-staff.html'}]};
    }
    if(/credential|onboard|compliance/.test(q)){
      return {text:'Credentialing and onboarding requirements vary by role, client, and program. Medlivo coordinates required licenses, documentation, compliance steps, and start readiness with the clinician and client team.',actions:[{label:'Contact Medlivo',href:'contact.html'}]};
    }
    if(/contact|phone|email|reach/.test(q)){
      return {text:'You can reach Medlivo at 855-633-5486 or hello@medlivo.com.',actions:[{label:'Contact Medlivo',href:'contact.html'}]};
    }
    if(/about|who is medlivo|company/.test(q)){
      return {text:'Medlivo is a healthcare staffing company with specialized Nursing & Allied, Rehabilitation, and Locum Tenens practices, supported by shared credentialing, compliance, delivery, and technology capabilities.',actions:[{label:'About Medlivo',href:'about.html'}]};
    }
    return null;
  }

  async function askApi(text){
    try{
      const controller=new AbortController();
      const timeout=setTimeout(()=>controller.abort(),6500);
      const response=await fetch('https://medlivo-ai-agent-397967014447.us-west1.run.app/api/medlivo-agent',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          message:text,
          page:location.pathname,
          context:{mode:state.mode,data:state.data}
        }),
        signal:controller.signal
      });
      clearTimeout(timeout);
      if(!response.ok){
        const errorText=await response.text().catch(()=>"");
        console.error('Ask Medlivo API error',response.status,errorText);
        return null;
      }
      const data=await response.json();
      if(!data||!data.message)return null;
      return data;
    }catch(e){return null}
  }

  function heuristicIntent(text){
    const q=text.toLowerCase();
    if(/need|looking for|hire|coverage|opening/.test(q) && /rn|nurse|therap|physician|provider|crna|staff|talent/.test(q))return 'client';
    if(/i am|i'm|im |looking for a job|job in|travel job|position/.test(q) && /rn|nurse|therap|physician|crna|pa\b|np\b|slp|job/.test(q))return 'clinician';
    return null;
  }

  async function handleFreeText(text){
    const known=answerKnownQuestion(text);
    if(known){
      addMessage(known.text);
      if(known.actions)addCard('Next step','',known.actions);
      return;
    }
    const intent=heuristicIntent(text);
    if(intent==='client'){
      addMessage('It sounds like you may be looking for healthcare staff. I can collect the basics and route you to the right Medlivo team.');
      addOptions([{label:'Start staffing request',onClick:startClient},{label:'Keep asking',onClick:()=>{state.mode='question';state.step='question';}}]);
      return;
    }
    if(intent==='clinician'){
      addMessage('It sounds like you may be looking for a healthcare job. I can narrow the search by division, specialty, and location.');
      addOptions([{label:'Find jobs',onClick:startClinician},{label:'Keep asking',onClick:()=>{state.mode='question';state.step='question';}}]);
      return;
    }
    showThinking();
    const api=await askApi(text);
    hideThinking();
    if(api){
      addMessage(api.message);
      if(Array.isArray(api.actions)&&api.actions.length)addCard(api.title||'Next step','',api.actions);
      return;
    }
    addMessage('I can help with staffing requests, healthcare jobs, Medlivo services, credentialing, and contact information. For anything more specific, I can connect you with the Medlivo team.');
    addOptions([
      {label:'I need staff',onClick:startClient},
      {label:'Find a job',onClick:startClinician},
      {label:'Contact Medlivo',onClick:()=>addCard('Contact Medlivo','',[{label:'Contact Medlivo',href:'contact.html'}])}
    ]);
  }

  async function submitText(text){
    const value=(text||'').trim();
    if(!value)return;
    addMessage(value,'user');
    input.value='';
    if(state.mode==='client'&&['role','location','timing','count'].includes(state.step))return clientNext(value);
    if(state.mode==='clinician'&&['profession','location'].includes(state.step))return clinicianNext(value);
    return handleFreeText(value);
  }

  launcher.addEventListener('click',()=>{
    panel.classList.toggle('open');
    launcher.setAttribute('aria-expanded',panel.classList.contains('open')?'true':'false');
    if(panel.classList.contains('open')&&!body.children.length)reset();
    if(panel.classList.contains('open'))setTimeout(()=>input.focus(),100);
  });
  close.addEventListener('click',()=>{
    panel.classList.remove('open');
    launcher.setAttribute('aria-expanded','false');
    launcher.focus();
  });
  form.addEventListener('submit',e=>{e.preventDefault();submitText(input.value)});
  send.addEventListener('click',()=>submitText(input.value));
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'&&panel.classList.contains('open')){
      panel.classList.remove('open');
      launcher.setAttribute('aria-expanded','false');
      launcher.focus();
    }
  });
})();
