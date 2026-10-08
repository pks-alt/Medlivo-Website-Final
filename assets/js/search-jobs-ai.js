(function(){
  const careerTaxonomy={
    "Nursing & Allied":[
      {value:"Registered Nurse",label:"Registered Nurse (RN)",specialties:["ICU","Med/Surg","Telemetry","Emergency Room","Operating Room","PACU","Labor & Delivery","Mother/Baby","NICU","PICU","Cath Lab","Oncology","Case Management","Home Health"]},
      {value:"LPN/LVN",label:"LPN / LVN",specialties:["Long-Term Care","Skilled Nursing","Clinic","Home Health","Corrections"]},
      {value:"CNA",label:"Certified Nursing Assistant (CNA)",specialties:["Acute Care","Long-Term Care","Skilled Nursing","Rehabilitation"]},
      {value:"Imaging & Radiology",label:"Imaging & Radiology",specialties:["CT","MRI","Radiologic Technologist","Ultrasound / Sonography","Mammography","Nuclear Medicine","Interventional Radiology"]},
      {value:"Laboratory",label:"Laboratory",specialties:["Medical Laboratory Scientist","Medical Laboratory Technician","Phlebotomy","Histology","Cytology"]},
      {value:"Respiratory Therapy",label:"Respiratory Therapy",specialties:["Registered Respiratory Therapist (RRT)","Certified Respiratory Therapist (CRT)"]},
      {value:"Surgical Services",label:"Surgical Services",specialties:["Surgical Technologist","Sterile Processing"]},
      {value:"Cardiovascular",label:"Cardiovascular",specialties:["Cath Lab Tech","Cardiovascular Technologist","EKG Tech"]},
      {value:"Audiology",label:"Audiology",specialties:["Audiology"]},
      {value:"Other Allied Health",label:"Other Allied Health",specialties:["Medical Assistant","Other Allied Health"]}
    ],
    "Rehabilitation":[
      {value:"Physical Therapist",label:"Physical Therapist (PT)",specialties:["Acute Care","Inpatient Rehabilitation","Outpatient","Skilled Nursing","Home Health","Pediatrics","Schools"]},
      {value:"Physical Therapist Assistant",label:"Physical Therapist Assistant (PTA)",specialties:["Inpatient Rehabilitation","Outpatient","Skilled Nursing","Home Health"]},
      {value:"Occupational Therapist",label:"Occupational Therapist (OT)",specialties:["Acute Care","Inpatient Rehabilitation","Outpatient","Skilled Nursing","Home Health","Pediatrics","Schools"]},
      {value:"COTA",label:"Certified Occupational Therapy Assistant (COTA)",specialties:["Inpatient Rehabilitation","Skilled Nursing","Home Health","Pediatrics"]},
      {value:"Speech-Language Pathologist",label:"Speech-Language Pathologist (SLP)",specialties:["Acute Care","Inpatient Rehabilitation","Skilled Nursing","Home Health","Pediatrics","Schools"]}
    ],
    "Locum Tenens":[
      {value:"Physician",label:"Physician",specialties:["Emergency Medicine","Hospitalist","Family Medicine","Internal Medicine","Cardiology","OB/GYN","Urology","Neurology","Psychiatry","Radiology","Anesthesiology","General Surgery","Gastroenterology","Oncology","Pulmonology","Critical Care","Pediatrics","Urgent Care","ENT / Otolaryngology"]},
      {value:"Nurse Practitioner",label:"Nurse Practitioner (NP)",specialties:["Primary Care","Urgent Care","Emergency Medicine","Hospitalist","Cardiology","OB/GYN","Psychiatry","Pediatrics"]},
      {value:"Physician Assistant",label:"Physician Assistant (PA)",specialties:["Primary Care","Urgent Care","Emergency Medicine","Hospitalist","Cardiology","Surgery","Orthopedics"]},
      {value:"Nurse Practitioner / Physician Assistant",label:"Nurse Practitioner / Physician Assistant (NP / PA)",specialties:["Primary Care","Urgent Care","Emergency Medicine","Hospitalist","Cardiology","OB/GYN","Psychiatry","Pediatrics","Surgery","Orthopedics"]},
      {value:"CRNA",label:"Certified Registered Nurse Anesthetist (CRNA)",specialties:["Anesthesia"]}
    ]
  };
  const divisionApi={"Nursing & Allied":"nursing_allied","Rehabilitation":"rehabilitation","Locum Tenens":"locum_tenens"};
  const divisionConfig={
    "":{title:"Job opportunities",eyebrow:"Popular Searches",shortcuts:[["specialty","ICU"],["specialty","Operating Room"],["profession","Physical Therapist"],["profession","Occupational Therapist"],["specialty","Emergency Medicine"],["specialty","Cardiology"]]},
    "Nursing & Allied":{title:"Nursing & Allied jobs.",eyebrow:"Popular Nursing & Allied Searches",shortcuts:[["specialty","ICU"],["specialty","Med/Surg"],["specialty","Operating Room"],["profession","Imaging & Radiology"],["profession","Respiratory Therapy"],["profession","Laboratory"]]},
    "Rehabilitation":{title:"Rehabilitation jobs.",eyebrow:"Popular Rehabilitation Searches",shortcuts:[["profession","Physical Therapist"],["profession","Physical Therapist Assistant"],["profession","Occupational Therapist"],["profession","COTA"],["profession","Speech-Language Pathologist"]]},
    "Locum Tenens":{title:"Locum Tenens jobs.",eyebrow:"Popular Locum Tenens Searches",shortcuts:[["specialty","Emergency Medicine"],["specialty","Hospitalist"],["specialty","Cardiology"],["specialty","OB/GYN"],["specialty","Urology"],["specialty","Neurology"]]}
  };
  const qs=s=>document.querySelector(s), qsa=s=>[...document.querySelectorAll(s)];
  const list=qs("#jobList"), noResults=qs("#noResults"), summary=qs("#resultsSummary"), resultsTitle=qs("#resultsTitle");
  const division=qs("#searchDivision"), profession=qs("#searchProfession"), specialty=qs("#searchSpecialty"), locationInput=qs("#searchLocation"), state=qs("#filterState");
  const pagination=qs("#jobsPagination"), paginationSummary=qs("#paginationSummary"), paginationPage=qs("#paginationPage"), prev=qs("#jobsPrevPage"), next=qs("#jobsNextPage");
  const allButton=qs(".jobs-all-button"), contextEyebrow=qs("#divisionContextEyebrow"), shortcuts=qs("#specialtyShortcuts");
  const PAGE_SIZE=20;
  let activeCategory="", nextCursor=null, cursorStack=[null], pageIndex=0, loading=false;

  function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  function normalizeCategory(value){
    const v=String(value||"").trim().toLowerCase();
    if(["nursing-allied","nursing & allied","nursing and allied"].includes(v))return "Nursing & Allied";
    if(["rehab","rehabilitation"].includes(v))return "Rehabilitation";
    if(["locum","locums","locum-tenens","locum tenens"].includes(v))return "Locum Tenens";
    return "";
  }
  function itemsForDivision(){return activeCategory?careerTaxonomy[activeCategory]:Object.values(careerTaxonomy).flat();}
  function unique(items){const seen=new Set();return items.filter(x=>seen.has(x.value)?false:(seen.add(x.value),true));}
  function rebuildProfession(preferred=""){
    const items=unique(itemsForDivision()), current=preferred||profession.value;
    profession.innerHTML='<option value="">All professions</option>'+items.map(x=>'<option value="'+esc(x.value)+'">'+esc(x.label)+'</option>').join("");
    if(items.some(x=>x.value===current))profession.value=current;
  }
  function rebuildSpecialty(preferred=""){
    const p=profession.value, items=itemsForDivision();
    let values=p?items.filter(x=>x.value===p).flatMap(x=>x.specialties):items.flatMap(x=>x.specialties);
    values=[...new Set(values)];
    const current=preferred||specialty.value;
    specialty.innerHTML='<option value="">All specialties</option>'+values.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");
    if(values.includes(current))specialty.value=current;
  }
  function updateUI(){
    const cfg=divisionConfig[activeCategory]||divisionConfig[""];
    allButton.classList.toggle("active",!activeCategory);allButton.setAttribute("aria-pressed",String(!activeCategory));
    qsa(".jobs-division-card").forEach(b=>{const on=b.dataset.category===activeCategory;b.classList.toggle("active",on);b.setAttribute("aria-pressed",String(on));});
    resultsTitle.textContent=profession.value?(profession.options[profession.selectedIndex]?.text||profession.value)+" jobs.":specialty.value?specialty.value+" jobs.":cfg.title;
    contextEyebrow.textContent=cfg.eyebrow;
    shortcuts.innerHTML=cfg.shortcuts.map(([kind,value])=>'<button type="button" data-kind="'+kind+'" data-value="'+esc(value)+'">'+esc(value)+'</button>').join("");
  }
  function query(after){
    const p=new URLSearchParams({limit:String(PAGE_SIZE)});
    if(activeCategory)p.set("division",divisionApi[activeCategory]);
    if(profession.value)p.set("profession",profession.value);
    if(specialty.value)p.set("specialty",specialty.value);
    const loc=locationInput.value.trim();
    if(state.value)p.set("state",state.value);
    if(loc){
      if(/^[A-Za-z]{2}$/.test(loc)&&!state.value)p.set("state",loc.toUpperCase());
      else p.set("city",loc);
    }
    if(after)p.set("after",after);
    return p;
  }
  function card(job){
    const location=[job.city,job.state].filter(Boolean).join(", ")||"Location to be confirmed";
    const category={"nursing_allied":"Nursing & Allied","rehabilitation":"Rehabilitation","locum_tenens":"Locum Tenens"}[job.division]||"Healthcare";
    return '<article class="job-card cat-'+esc(job.division)+'"><div class="job-card-main"><div class="job-badges"><span class="job-badge">'+esc(category)+'</span><span class="job-badge alt">'+esc(job.profession||job.specialty||"Clinician")+'</span></div><h3>'+esc(job.title)+'</h3><div class="job-location-line"><span class="job-location-dot"></span><span>'+esc(location)+'</span></div>'+(job.specialty?'<div class="job-specialty-line">Specialty: <strong>'+esc(job.specialty)+'</strong></div>':'')+'<div class="job-detail-grid"><div class="job-detail"><small>Starts</small><strong>'+esc(job.start_date||"Ask recruiter")+'</strong></div><div class="job-detail"><small>Duration</small><strong>'+esc(job.duration_weeks?job.duration_weeks+" weeks":"Ask recruiter")+'</strong></div><div class="job-detail job-id"><small>Job ID</small><strong>'+esc(String(job.id).slice(0,8).toUpperCase())+'</strong></div></div></div><div class="job-card-side"><span class="job-pay-label">Opportunity</span><div class="job-pay">'+esc(job.shift||job.care_setting||"Current opening")+'</div><a class="job-apply" href="job.html?id='+encodeURIComponent(job.id)+'">View Job Details</a><span class="job-ats-note">Medlivo-reviewed job details</span></div></article>';
  }
  async function load({reset=false,direction=0}={}){
    if(loading)return;loading=true;
    if(reset){cursorStack=[null];pageIndex=0;}
    if(direction>0&&nextCursor){cursorStack.push(nextCursor);pageIndex++;}
    if(direction<0&&pageIndex>0){cursorStack.pop();pageIndex--;}
    const cursor=cursorStack[pageIndex];
    list.innerHTML='<div class="jobs-loading" role="status">Loading current Medlivo opportunities…</div>';
    noResults.hidden=true;pagination.hidden=true;
    try{
      const response=await fetch('/api/careers/jobs?'+query(cursor),{headers:{Accept:"application/json"},cache:"no-store"});
      if(!response.ok)throw new Error("unavailable");
      const data=await response.json(), items=data.items||[];nextCursor=data.next_cursor||null;
      list.innerHTML=items.map(card).join("");list.hidden=items.length===0;noResults.hidden=items.length!==0;
      summary.textContent=items.length?("Showing "+items.length+" current Medlivo job"+(items.length===1?"":"s")+(activeCategory?" in "+activeCategory:"")+"."):"No jobs match these selections. A recruiter can help check current availability.";
      pagination.hidden=pageIndex===0&&!nextCursor;
      paginationSummary.textContent=items.length?("Showing up to "+PAGE_SIZE+" jobs on this page"):"";
      paginationPage.textContent="Page "+(pageIndex+1);
      prev.disabled=pageIndex===0;next.disabled=!nextCursor;
    }catch(error){
      list.hidden=false;list.innerHTML='<div class="jobs-api-error"><h3>Current jobs are temporarily unavailable.</h3><p>Please try again shortly or contact a Medlivo recruiter for current opportunities.</p></div>';
      summary.textContent="We could not load the current job feed.";
    }finally{loading=false;updateUI();saveSearch();}
  }
  function setDivision(value){activeCategory=normalizeCategory(value);division.value=activeCategory;profession.value="";specialty.value="";rebuildProfession();rebuildSpecialty();load({reset:true});}
  function saveSearch(){
    if(!/^https?:$/.test(location.protocol))return;
    const u=new URL(location.href);["division","profession","specialty","location","state"].forEach(k=>u.searchParams.delete(k));
    const values={division:activeCategory,profession:profession.value,specialty:specialty.value,location:locationInput.value.trim(),state:state.value};
    Object.entries(values).forEach(([k,v])=>{if(v)u.searchParams.set(k,v)});history.replaceState(null,"",u);
  }

  const params=new URLSearchParams(location.search);activeCategory=normalizeCategory(params.get("division")||params.get("profession")||"");division.value=activeCategory;
  rebuildProfession(params.get("profession")&&!normalizeCategory(params.get("profession"))?params.get("profession"):"");
  rebuildSpecialty(params.get("specialty")||"");
  locationInput.value=params.get("location")||"";state.value=(params.get("state")||"").toUpperCase();updateUI();

  qs("#jobsSearchForm").addEventListener("submit",e=>{e.preventDefault();activeCategory=normalizeCategory(division.value);load({reset:true});qs(".jobs-results-section")?.scrollIntoView({behavior:"smooth",block:"start"});});
  qsa(".jobs-division-card").forEach(b=>b.addEventListener("click",()=>setDivision(b.dataset.category)));
  allButton.addEventListener("click",()=>setDivision(""));
  profession.addEventListener("change",()=>{rebuildSpecialty();load({reset:true});});
  specialty.addEventListener("change",()=>load({reset:true}));
  state.addEventListener("change",()=>load({reset:true}));
  locationInput.addEventListener("change",()=>load({reset:true}));
  shortcuts.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;if(b.dataset.kind==="profession"){for(const [d,items] of Object.entries(careerTaxonomy))if(items.some(x=>x.value===b.dataset.value)){activeCategory=d;division.value=d;break;}rebuildProfession(b.dataset.value);profession.value=b.dataset.value;rebuildSpecialty();}else{specialty.value=b.dataset.value;}load({reset:true});});
  qs("#clearFilters").addEventListener("click",()=>{activeCategory="";division.value="";profession.value="";specialty.value="";locationInput.value="";state.value="";rebuildProfession();rebuildSpecialty();load({reset:true});});
  qs("#viewAllJobs").addEventListener("click",()=>qs("#clearFilters").click());
  prev.addEventListener("click",()=>load({direction:-1}));
  next.addEventListener("click",()=>load({direction:1}));
  const sort=qs("#sortJobs");if(sort){sort.innerHTML='<option value="current">Current openings</option>';sort.disabled=true;}
  load({reset:true});
})();