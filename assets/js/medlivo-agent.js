(function(){
  const panel=document.querySelector('[data-medlivo-agent-panel]');
  const launcher=document.querySelector('[data-medlivo-agent-launcher]');
  if(!panel||!launcher)return;
  const API_BASE='https://medlivo-ai-agent-397967014447.us-west1.run.app';
  const body=panel.querySelector('[data-agent-body]');
  const form=panel.querySelector('[data-agent-form]');
  const input=panel.querySelector('[data-agent-input]');
  const close=panel.querySelector('[data-agent-close]');
  const state={mode:'home',step:null,data:{}};
  const divisions=['Nursing & Allied','Rehabilitation','Locum Tenens'];
  let thinkingNode=null;

  function scrollBottom(){body.scrollTop=body.scrollHeight}
  function setPlaceholder(text){input.placeholder=text||'Type a message';input.focus()}
  function addMessage(text,who='bot'){
    const row=document.createElement('div');row.className='medlivo-agent-message '+who;
    const bubble=document.createElement('div');bubble.className='medlivo-agent-bubble';bubble.textContent=text;
    row.appendChild(bubble);body.appendChild(row);scrollBottom();return row;
  }
  function addStep(label,current,total){
    const wrap=document.createElement('div');wrap.className='medlivo-agent-progress';
    wrap.innerHTML='<span>'+label+'</span><strong>'+current+' of '+total+'</strong><i><b style="width:'+Math.round((current/total)*100)+'%"></b></i>';
    body.appendChild(wrap);scrollBottom();
  }
  function addOptions(options){
    const wrap=document.createElement('div');wrap.className='medlivo-agent-options';
    options.forEach(opt=>{const btn=document.createElement('button');btn.type='button';btn.className='medlivo-agent-option';btn.textContent=opt.label;btn.addEventListener('click',()=>{wrap.remove();opt.onClick()});wrap.appendChild(btn)});
    body.appendChild(wrap);scrollBottom();return wrap;
  }
  function addCard(title,text,actions=[]){
    const card=document.createElement('div');card.className='medlivo-agent-card';
    const strong=document.createElement('strong');strong.textContent=title;card.appendChild(strong);
    if(text){const p=document.createElement('p');p.textContent=text;card.appendChild(p)}
    if(actions.length){const row=document.createElement('div');row.className='medlivo-agent-card-actions';actions.forEach((a,i)=>{const link=document.createElement('a');link.className='medlivo-agent-link'+(i?' secondary':'');link.href=a.href;link.textContent=a.label;row.appendChild(link)});card.appendChild(row)}
    body.appendChild(card);scrollBottom();return card;
  }
  function showThinking(){thinkingNode=document.createElement('div');thinkingNode.className='medlivo-agent-message bot';thinkingNode.innerHTML='<div class="medlivo-agent-thinking"><i></i><i></i><i></i></div>';body.appendChild(thinkingNode);scrollBottom()}
  function hideThinking(){if(thinkingNode){thinkingNode.remove();thinkingNode=null}}
  function reset(){
    state.mode='home';state.step=null;state.data={};body.innerHTML='';
    addMessage('Hi. I can help with staffing needs, healthcare jobs, or questions about Medlivo.');
    addMessage('What would you like to do?');
    addOptions([{label:'I need healthcare staff',onClick:startClient},{label:'I’m looking for a job',onClick:startClinician},{label:'I have a question',onClick:startQuestion}]);
    setPlaceholder('Type a message');
  }

  function startClient(){
    state.mode='client';state.step='division';state.data={};addMessage('I need healthcare staff','user');addStep('Staffing request',1,3);addMessage('Which team is closest to your need?');
    addOptions(divisions.map(d=>({label:d,onClick:()=>chooseClientDivision(d)})).concat([{label:'Not sure',onClick:()=>chooseClientDivision('Not sure')}]));
  }
  function chooseClientDivision(v){state.data.division=v;addMessage(v,'user');state.step='role';addMessage('What role or specialty do you need?');setPlaceholder('Example: ICU RN, PT, Urologist')}
  function clientNext(v){
    if(state.step==='role'){state.data.role=v;state.step='location';addMessage('What city and state is the coverage for?');setPlaceholder('Example: Tacoma, WA');return}
    if(state.step==='location'){state.data.location=v;state.step='timing';addMessage('When do you need coverage to start?');setPlaceholder('Example: ASAP or October 15');return}
    if(state.step==='timing'){state.data.startTiming=v;state.step='count';addMessage('How many people do you need?');setPlaceholder('Example: 2');return}
    if(state.step==='count'){state.data.numberNeeded=v;state.step='organization';addStep('Organization',2,3);addMessage('What organization or facility is this for?');setPlaceholder('Organization or facility name');return}
    if(state.step==='organization'){state.data.organization=v;state.step='contactName';addMessage('Who should our team contact?');setPlaceholder('Your name');return}
    if(state.step==='contactName'){state.data.contactName=v;state.step='workEmail';addMessage('What is your work email?');setPlaceholder('name@organization.com');return}
    if(state.step==='workEmail'){state.data.workEmail=v;state.step='phone';addMessage('Phone number? You can type “skip” if you prefer email.');setPlaceholder('Phone number or skip');return}
    if(state.step==='phone'){state.data.phone=/^skip$/i.test(v)?'':v;state.step='notes';addStep('Review and send',3,3);addMessage('Anything else the team should know? You can type “skip”.');setPlaceholder('Schedule, shift, call, credentialing, or skip');return}
    if(state.step==='notes'){state.data.notes=/^skip$/i.test(v)?'':v;submitClientLead()}
  }
  async function submitClientLead(){
    state.step='submitting';showThinking();
    try{
      const response=await fetch(API_BASE+'/api/leads/client',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...state.data,source:'Ask Medlivo'})});
      hideThinking();if(!response.ok)throw new Error('Client lead '+response.status);
      const result=await response.json(),d=state.data;
      addMessage('Thank you. Your staffing request has been sent to Medlivo.');
      addCard('Request received',[d.division,d.role,d.location,d.startTiming,d.numberNeeded?d.numberNeeded+' needed':null].filter(Boolean).join(' · '),[{label:'Workforce Solutions',href:'workforce-solutions.html'},{label:'Call Medlivo',href:'tel:+18556335486'}]);
      if(result.leadId)addMessage('Reference: '+result.leadId);state.step='complete';setPlaceholder('Ask another question');
    }catch(e){
      hideThinking();console.error(e);addMessage('I could not send the request online. I can still take you to the Request Staff form with the details already filled in.');
      const d=state.data,p=new URLSearchParams();if(d.division&&d.division!=='Not sure')p.set('division',d.division);if(d.role)p.set('role',d.role);if(d.location)p.set('location',d.location);if(d.startTiming)p.set('start',d.startTiming);if(d.numberNeeded)p.set('count',d.numberNeeded);
      addCard('Continue your request','Your details can be carried into the form.',[{label:'Open Request Staff',href:'request-staff.html?'+p.toString()},{label:'Call 855-633-5486',href:'tel:+18556335486'}]);state.step='complete';
    }
  }

  function startClinician(){
    state.mode='clinician';state.step='division';state.data={};addMessage('I’m looking for a job','user');addStep('Career preferences',1,3);addMessage('Which area best matches your profession?');
    addOptions(divisions.map(d=>({label:d,onClick:()=>chooseClinicianDivision(d)})));
  }
  function chooseClinicianDivision(v){state.data.division=v;addMessage(v,'user');state.step='profession';addMessage('What is your profession?');setPlaceholder('Example: RN, Physical Therapist, CRNA')}
  function clinicianNext(v){
    if(state.step==='profession'){state.data.profession=v;state.step='specialty';addMessage('What specialty best describes your experience? You can type “skip”.');setPlaceholder('Example: ICU, Pediatrics, Outpatient, or skip');return}
    if(state.step==='specialty'){state.data.specialty=/^skip$/i.test(v)?'':v;state.step='preferredLocations';addMessage('Where would you like to work?');setPlaceholder('City, state, or states');return}
    if(state.step==='preferredLocations'){state.data.preferredLocations=v;state.step='travelLocal';addMessage('Are you looking for travel, local, or either?');addOptions(['Travel','Local','Either'].map(x=>({label:x,onClick:()=>{state.data.travelLocal=x;addMessage(x,'user');state.step='availability';addMessage('When are you available to start?');setPlaceholder('Example: ASAP, October, or flexible')}})));return}
    if(state.step==='availability'){state.data.availability=v;state.step='name';addStep('Contact details',2,3);addMessage('What is your name?');setPlaceholder('Your name');return}
    if(state.step==='name'){state.data.name=v;state.step='email';addMessage('What email should a recruiter use?');setPlaceholder('you@example.com');return}
    if(state.step==='email'){state.data.email=v;state.step='phone';addMessage('What is the best phone number? You can type “skip”.');setPlaceholder('Phone number or skip');return}
    if(state.step==='phone'){state.data.phone=/^skip$/i.test(v)?'':v;addStep('Connect with Medlivo',3,3);submitClinicianLead()}
  }
  async function submitClinicianLead(){
    state.step='submitting';showThinking();
    try{
      const response=await fetch(API_BASE+'/api/leads/clinician',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...state.data,source:'Ask Medlivo'})});
      hideThinking();if(!response.ok)throw new Error('Clinician lead '+response.status);
      const result=await response.json(),d=state.data,p=new URLSearchParams();
      if(d.division)p.set('division',d.division);if(d.profession)p.set('profession',d.profession);if(d.specialty)p.set('specialty',d.specialty);if(d.preferredLocations)p.set('location',d.preferredLocations);
      addMessage('Thanks. Your information has been sent to the Medlivo recruiting team.');
      addCard('You’re connected',[d.profession,d.specialty,d.preferredLocations,d.travelLocal,d.availability].filter(Boolean).join(' · '),[{label:'View Jobs',href:'search-jobs.html?'+p.toString()},{label:'About Medlivo',href:'about.html'}]);
      if(result.leadId)addMessage('Reference: '+result.leadId);state.step='complete';setPlaceholder('Ask another question');
    }catch(e){hideThinking();console.error(e);addMessage('I could not send your information online right now. You can still search Medlivo jobs or contact us directly.');addCard('Next step','',[{label:'Search Jobs',href:'search-jobs.html'},{label:'Contact Medlivo',href:'contact.html'}]);state.step='complete'}
  }

  function startQuestion(){state.mode='question';state.step='question';addMessage('I have a question','user');addMessage('Ask about Medlivo, staffing, jobs, credentialing, or how to reach the right team.');setPlaceholder('Type your question')}
  function answerKnownQuestion(text){
    const q=text.toLowerCase();
    if(/medical advice|diagnos|symptom|patient treatment/.test(q))return {text:'I can help with staffing, jobs, and Medlivo services, but I can’t provide medical advice or collect patient information.',actions:[{label:'Contact Medlivo',href:'contact.html'}]};
    if(/nursing|allied/.test(q))return {text:'Medlivo’s Nursing & Allied team supports nursing and allied health staffing across healthcare settings.',actions:[{label:'Nursing & Allied',href:'nursing-allied.html'},{label:'Search Jobs',href:'search-jobs.html?division=Nursing%20%26%20Allied'}]};
    if(/rehab|physical therap|occupational therap|speech|slp|pt\b|ot\b/.test(q))return {text:'Medlivo’s Rehabilitation division focuses on Physical Therapy, Occupational Therapy, and Speech-Language Pathology.',actions:[{label:'Rehabilitation',href:'rehabilitation.html'},{label:'Search Rehab Jobs',href:'search-jobs.html?division=Rehabilitation'}]};
    if(/locum|physician|provider|crna|nurse practitioner|physician assistant/.test(q))return {text:'Medlivo’s Locum Tenens team supports physicians and advanced practice providers.',actions:[{label:'Locum Tenens',href:'locum-tenens.html'},{label:'Search Provider Jobs',href:'search-jobs.html?division=Locum%20Tenens'}]};
    if(/job|career|opening|work/.test(q))return {text:'You can search Medlivo opportunities by division, profession, specialty, and location.',actions:[{label:'Search Jobs',href:'search-jobs.html'}]};
    if(/staff|coverage|hire|need people|need talent/.test(q))return {text:'I can collect your staffing need here and send it directly to the right Medlivo team.',startClient:true};
    if(/credential|onboard|compliance/.test(q))return {text:'Credentialing and onboarding requirements vary by role, client, and program. Medlivo coordinates required documentation, compliance steps, and start readiness.',actions:[{label:'Contact Medlivo',href:'contact.html'}]};
    if(/contact|phone|email|reach/.test(q))return {text:'You can reach Medlivo at 855-633-5486 or hello@medlivo.com.',actions:[{label:'Contact Medlivo',href:'contact.html'}]};
    if(/about|who is medlivo|company/.test(q))return {text:'Medlivo is a healthcare staffing company with specialized Nursing & Allied, Rehabilitation, and Locum Tenens practices.',actions:[{label:'About Medlivo',href:'about.html'}]};
    return null;
  }
  async function askApi(text){
    try{
      const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),7000);
      const response=await fetch(API_BASE+'/api/medlivo-agent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,page:location.pathname,context:{mode:state.mode,data:state.data}}),signal:controller.signal});
      clearTimeout(timeout);if(!response.ok)return null;const data=await response.json();return data&&data.message?data:null;
    }catch(e){return null}
  }
  async function handleFreeText(text){
    const known=answerKnownQuestion(text);
    if(known){addMessage(known.text);if(known.startClient)addOptions([{label:'Start staffing request',onClick:startClient}]);else if(known.actions)addCard('Next step','',known.actions);return}
    showThinking();const api=await askApi(text);hideThinking();if(api){addMessage(api.message);return}
    addMessage('I can help with staffing requests, healthcare jobs, Medlivo services, credentialing, and contact information.');
    addOptions([{label:'I need staff',onClick:startClient},{label:'Find a job',onClick:startClinician},{label:'Contact Medlivo',onClick:()=>addCard('Contact Medlivo','',[{label:'Contact Medlivo',href:'contact.html'}])}]);
  }
  async function submitText(text){
    const v=(text||'').trim();if(!v)return;addMessage(v,'user');input.value='';
    if(state.mode==='client'&&['role','location','timing','count','organization','contactName','workEmail','phone','notes'].includes(state.step))return clientNext(v);
    if(state.mode==='clinician'&&['profession','specialty','preferredLocations','availability','name','email','phone'].includes(state.step))return clinicianNext(v);
    return handleFreeText(v);
  }
  launcher.addEventListener('click',()=>{panel.classList.toggle('open');launcher.setAttribute('aria-expanded',panel.classList.contains('open')?'true':'false');if(panel.classList.contains('open')&&!body.children.length)reset();if(panel.classList.contains('open'))setTimeout(()=>input.focus(),100)});
  close.addEventListener('click',()=>{panel.classList.remove('open');launcher.setAttribute('aria-expanded','false');launcher.focus()});
  form.addEventListener('submit',e=>{e.preventDefault();submitText(input.value)});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&panel.classList.contains('open')){panel.classList.remove('open');launcher.setAttribute('aria-expanded','false');launcher.focus()}});
})();