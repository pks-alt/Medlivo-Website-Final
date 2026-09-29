
(function(){
  /*
    ATS HANDOFF CONTRACT
    --------------------
    Replace "jobs" with live ATS records while preserving these normalized fields:
    id, title, category, profession, specialty, type, state, city, pay, start, posted, applyUrl.
    The page is intentionally organized for clinicians as:
    Division → Profession → Specialty → Location/State.

    LARGE INVENTORY REQUIREMENT
    ---------------------------
    Production ATS integration must be server/API paginated. Do NOT load thousands
    of jobs into the browser. Request one page at a time and return totalCount,
    page, pageSize, and jobs. The preview below uses client-side paging only because
    it contains a small static sample.

    Replace the temporary Quick Apply and Job Alert email actions with existing ATS workflows.
  */
  const jobs=[
    {id:"26-38997",title:"Neurology",category:"Locum Tenens",profession:"Physician",specialty:"Neurology",type:"Physician",state:"AZ",city:"Prescott",pay:"$110.00 – $130.00 / Hour",start:"A.S.A.P",posted:"09/22/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38892",title:"OB/GYN Physician",category:"Locum Tenens",profession:"Physician",specialty:"OB/GYN",type:"Physician",state:"CO",city:"Fort Morgan",pay:"$315.00 – $365.00 / Hour",start:"A.S.A.P",posted:"09/21/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38883",title:"ENT Physician",category:"Locum Tenens",profession:"Physician",specialty:"ENT / Otolaryngology",type:"Physician",state:"CA",city:"Sacramento",pay:"$315.00 – $345.00 / Hour",start:"A.S.A.P",posted:"09/21/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38946",title:"Emergency Medicine",category:"Locum Tenens",profession:"Physician",specialty:"Emergency Medicine",type:"Physician",state:"CA",city:"Fortuna",pay:"$250.00 – $300.00 / Hour",start:"A.S.A.P",posted:"09/21/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38740",title:"Nurse Practitioner (NP)",category:"Locum Tenens",profession:"Nurse Practitioner",specialty:"",type:"Advanced Practice",state:"NM",city:"Deming",pay:"$90.00 – $110.00 / Hour",start:"A.S.A.P",posted:"09/18/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38617",title:"Physician Assistant - Cardiology, Nurse Practitioner - Cardiology",category:"Locum Tenens",profession:"Nurse Practitioner / Physician Assistant",specialty:"Cardiology",type:"Advanced Practice",state:"WA",city:"Everett",pay:"$100.00 – $120.00 / Hour",start:"A.S.A.P",posted:"09/17/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38616",title:"Obstetrics and Gynecology",category:"Locum Tenens",profession:"Physician",specialty:"OB/GYN",type:"Physician",state:"OR",city:"Hood River",pay:"$150.00 – $200.00 / Hour",start:"A.S.A.P",posted:"09/17/2026",applyUrl:"https://www.medlivo.com/search-jobs"},
    {id:"26-38524",title:"Audiologist",category:"Nursing & Allied",profession:"Audiology",specialty:"Audiology",type:"Allied Health",state:"WA",city:"Yakima",pay:"$80.00 – $90.00 / Hour",start:"A.S.A.P",posted:"09/16/2026",applyUrl:"https://www.medlivo.com/search-jobs"}
  ];

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

  const divisionConfig={
    "":{
      title:"Job opportunities",
      eyebrow:"Popular Searches",
      contextTitle:"Start with a common search, or use the filters above.",
      contextText:"Choose a shortcut below, or leave any field set to All to see more jobs.",
      shortcuts:[
        {label:"ICU",kind:"specialty",value:"ICU"},
        {label:"Operating Room",kind:"specialty",value:"Operating Room"},
        {label:"Physical Therapist",kind:"profession",value:"Physical Therapist"},
        {label:"Occupational Therapist",kind:"profession",value:"Occupational Therapist"},
        {label:"Emergency Medicine",kind:"specialty",value:"Emergency Medicine"},
        {label:"Cardiology",kind:"specialty",value:"Cardiology"}
      ]
    },
    "Nursing & Allied":{
      title:"Nursing & Allied jobs.",
      eyebrow:"Popular Nursing & Allied Searches",
      contextTitle:"Choose a common specialty or profession.",
      contextText:"You can also use Profession and Specialty above to narrow your search.",
      shortcuts:[
        {label:"ICU",kind:"specialty",value:"ICU"},
        {label:"Med/Surg",kind:"specialty",value:"Med/Surg"},
        {label:"Operating Room",kind:"specialty",value:"Operating Room"},
        {label:"Imaging & Radiology",kind:"profession",value:"Imaging & Radiology"},
        {label:"Respiratory Therapy",kind:"profession",value:"Respiratory Therapy"},
        {label:"Laboratory",kind:"profession",value:"Laboratory"}
      ]
    },
    "Rehabilitation":{
      title:"Rehabilitation jobs.",
      eyebrow:"Popular Rehabilitation Searches",
      contextTitle:"Choose your therapy profession.",
      contextText:"Select your profession first, then narrow by care setting if you want.",
      shortcuts:[
        {label:"Physical Therapist",kind:"profession",value:"Physical Therapist"},
        {label:"PTA",kind:"profession",value:"Physical Therapist Assistant"},
        {label:"Occupational Therapist",kind:"profession",value:"Occupational Therapist"},
        {label:"COTA",kind:"profession",value:"COTA"},
        {label:"SLP",kind:"profession",value:"Speech-Language Pathologist"}
      ]
    },
    "Locum Tenens":{
      title:"Locum Tenens jobs.",
      eyebrow:"Popular Locum Tenens Searches",
      contextTitle:"Choose a specialty or provider type.",
      contextText:"Search physician, nurse practitioner, physician assistant and CRNA opportunities.",
      shortcuts:[
        {label:"Emergency Medicine",kind:"specialty",value:"Emergency Medicine"},
        {label:"Hospitalist",kind:"specialty",value:"Hospitalist"},
        {label:"Cardiology",kind:"specialty",value:"Cardiology"},
        {label:"OB/GYN",kind:"specialty",value:"OB/GYN"},
        {label:"Urology",kind:"specialty",value:"Urology"},
        {label:"Neurology",kind:"specialty",value:"Neurology"}
      ]
    }
  };

  const qs=s=>document.querySelector(s);
  const qsa=s=>[...document.querySelectorAll(s)];
  const list=qs("#jobList");
  const noResults=qs("#noResults");
  const summary=qs("#resultsSummary");
  const resultsTitle=qs("#resultsTitle");
  const division=qs("#searchDivision");
  const profession=qs("#searchProfession");
  const specialty=qs("#searchSpecialty");
  const locationInput=qs("#searchLocation");
  const filterState=qs("#filterState");
  const sort=qs("#sortJobs");
  const allButton=qs(".jobs-all-button");
  const contextEyebrow=qs("#divisionContextEyebrow");
  const shortcuts=qs("#specialtyShortcuts");
  const pagination=qs("#jobsPagination");
  const paginationSummary=qs("#paginationSummary");
  const paginationPage=qs("#paginationPage");
  const prevPage=qs("#jobsPrevPage");
  const nextPage=qs("#jobsNextPage");
  const PAGE_SIZE=20;
  let currentPage=1;
  let searchReady=false;
  let activeCategory="";

  function slug(value){
    return String(value||"").toLowerCase().replace(/&/g,"and").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
  }
  function norm(value){
    return String(value||"").trim().toLowerCase().replace(/&/g,"and").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim();
  }
  function normalizeCategory(value){
    const v=String(value||"").trim().toLowerCase();
    if(["nursing-allied","nursing & allied","nursing and allied"].includes(v))return "Nursing & Allied";
    if(["rehab","rehabilitation"].includes(v))return "Rehabilitation";
    if(["locum","locums","locum-tenens","locum tenens"].includes(v))return "Locum Tenens";
    return "";
  }
  function taxonomyItems(category){
    if(category && careerTaxonomy[category])return careerTaxonomy[category];
    return Object.values(careerTaxonomy).flat();
  }
  function uniqueByValue(items){
    const seen=new Set();
    return items.filter(item=>{
      if(seen.has(item.value))return false;
      seen.add(item.value);
      return true;
    });
  }
  function findDivisionForProfession(value){
    for(const [category,items] of Object.entries(careerTaxonomy)){
      if(items.some(item=>item.value===value))return category;
    }
    return "";
  }
  function findDivisionForSpecialty(value){
    for(const [category,items] of Object.entries(careerTaxonomy)){
      if(items.some(item=>item.specialties.includes(value)))return category;
    }
    return "";
  }
  function rebuildProfessionOptions(preferred=""){
    const items=uniqueByValue(taxonomyItems(activeCategory));
    const current=preferred||profession.value;
    const options=['<option value="">All professions</option>']
      .concat(items.map(item=>'<option value="'+item.value.replace(/"/g,"&quot;")+'">'+item.label+'</option>'));
    profession.innerHTML=options.join("");
    if(items.some(item=>item.value===current)){
      profession.value=current;
    }
  }
  function rebuildSpecialtyOptions(preferred=""){
    let values=[];
    const currentProfession=profession.value;
    const items=taxonomyItems(activeCategory);
    if(currentProfession){
      const matching=items.filter(item=>item.value===currentProfession);
      values=matching.flatMap(item=>item.specialties);
    }else if(activeCategory){
      values=items.flatMap(item=>item.specialties);
    }else{
      values=["ICU","Med/Surg","Operating Room","Physical Therapy","Occupational Therapy","Speech-Language Pathology","Emergency Medicine","Cardiology","OB/GYN","Urology","Neurology"];
    }
    values=[...new Set(values)];
    const current=preferred||specialty.value;
    specialty.innerHTML='<option value="">All specialties</option>'+values.map(v=>'<option value="'+v.replace(/"/g,"&quot;")+'">'+v+'</option>').join("");
    if(values.includes(current))specialty.value=current;
  }
  function setProfession(value){
    profession.value=value||"";
  }
  function payHigh(job){
    const nums=(String(job.pay||"").replace(/,/g,"").match(/\d+(?:\.\d+)?/g)||[]).map(Number);
    return nums.length?Math.max(...nums):0;
  }
  function formatPosted(value){
    if(!value)return "Current";
    const d=new Date(value);
    if(Number.isNaN(d.getTime()))return value;
    return d.toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"});
  }
  function showSpecialty(job){
    const sp=String(job.specialty||"").trim();
    if(!sp)return "";
    const title=norm(job.title);
    const professionName=norm(job.profession||job.type);
    const specialtyName=norm(sp);
    if(!specialtyName || title===specialtyName || professionName===specialtyName)return "";
    return sp;
  }
  function professionMatch(job,filter){
    if(!filter)return true;
    const target=norm(filter);
    // A physician assistant is not a physician. Keep provider routes distinct.
    if(target==="physician" && /physician assistant|nurse practitioner|crna|nurse anesthetist/.test(norm(job.profession)))return false;
    if(target==="nurse practitioner physician assistant")return professionMatch(job,"Nurse Practitioner")||professionMatch(job,"Physician Assistant");
    if(norm(job.profession)===target)return true;
    const hay=norm([job.profession,job.type,job.title,job.specialty].filter(Boolean).join(" "));
    const aliases={
      "registered nurse":["registered nurse"," rn "],
      "lpn lvn":["lpn","lvn","licensed practical nurse","licensed vocational nurse"],
      "cna":["cna","certified nursing assistant"],
      "imaging and radiology":["imaging","radiology","radiologic","ct tech","mri","sonograph","ultrasound","mammograph","nuclear medicine"],
      "laboratory":["laboratory","medical technologist","lab tech","phlebot","histolog","cytolog"],
      "respiratory therapy":["respiratory therapist","rrt","crt"],
      "surgical services":["surgical technologist","sterile processing"],
      "cardiovascular":["cath lab tech","cardiovascular","ekg"],
      "audiology":["audiolog"],
      "other allied health":["allied health"],
      "physical therapist":["physical therapist"],
      "physical therapist assistant":["physical therapist assistant","pta"],
      "occupational therapist":["occupational therapist"],
      "cota":["cota","occupational therapy assistant"],
      "speech language pathologist":["speech language pathologist","slp"],
      "physician":["physician"],
      "nurse practitioner":["nurse practitioner"," np "],
      "physician assistant":["physician assistant"," pa "],
      "crna":["crna","nurse anesthetist"]
    };
    const terms=aliases[target]||[target];
    const padded=" "+hay+" ";
    return terms.some(term=>padded.includes(norm(term).length<=3?" "+norm(term)+" ":norm(term)));
  }
  function specialtyMatch(job,filter){
    if(!filter)return true;
    const target=norm(filter);
    const hay=norm([job.specialty,job.title,job.profession,job.type].filter(Boolean).join(" "));
    if(target==="ob gyn")return hay.includes("ob gyn")||hay.includes("obstetrics and gynecology");
    if(target==="ent otolaryngology")return hay.includes("ent")||hay.includes("otolaryngology");
    return hay.includes(target);
  }
  function matches(job){
    const div=normalizeCategory(division.value||activeCategory);
    const pr=profession.value||"";
    const sp=specialty.value||"";
    const l=(locationInput.value||"").trim().toLowerCase();
    const st=(filterState.value||"").toLowerCase();
    if(div && job.category!==div)return false;
    if(pr && !professionMatch(job,pr))return false;
    if(sp && !specialtyMatch(job,sp))return false;
    const stateName=[...filterState.options].find(o=>o.value===job.state)?.text||"";
    if(l && !(job.city+" "+job.state+" "+stateName).toLowerCase().includes(l))return false;
    if(st && job.state.toLowerCase()!==st)return false;
    return true;
  }
  function renderShortcuts(){
    const cfg=divisionConfig[activeCategory]||divisionConfig[""];
    shortcuts.innerHTML=cfg.shortcuts.map(item=>
      '<button type="button" data-kind="'+item.kind+'" data-value="'+item.value.replace(/"/g,"&quot;")+'">'+item.label+'</button>'
    ).join("");
    qsa("#specialtyShortcuts button").forEach(btn=>btn.addEventListener("click",()=>{
      const kind=btn.dataset.kind;
      const value=btn.dataset.value||"";
      if(kind==="profession"){
        const inferred=findDivisionForProfession(value);
        if(inferred && !activeCategory){
          activeCategory=inferred;
          division.value=inferred;
          rebuildProfessionOptions(value);
        }
        setProfession(value);
        rebuildSpecialtyOptions();
      }else{
        const inferred=findDivisionForSpecialty(value);
        if(inferred && !activeCategory){
          activeCategory=inferred;
          division.value=inferred;
          rebuildProfessionOptions();
          rebuildSpecialtyOptions(value);
        }
        specialty.value=value;
      }
      render(true);
      qs(".job-list")?.scrollIntoView({behavior:"smooth",block:"start"});
    }));
  }
  function updateDivisionUI(){
    const cfg=divisionConfig[activeCategory]||divisionConfig[""];
    allButton.classList.toggle("active",!activeCategory);
    allButton.setAttribute("aria-pressed",String(!activeCategory));
    qsa(".jobs-division-card").forEach(btn=>{
      const selected=btn.dataset.category===activeCategory;
      btn.classList.toggle("active",selected);
      btn.setAttribute("aria-pressed",String(selected));
    });
    const selectedProfession=profession.value;
    const selectedSpecialty=specialty.value;
    resultsTitle.textContent=selectedProfession
      ? (profession.options[profession.selectedIndex]?.text||selectedProfession)+" jobs."
      : selectedSpecialty
        ? selectedSpecialty+" jobs."
        : cfg.title;
    contextEyebrow.textContent=cfg.eyebrow;
    renderShortcuts();
  }
  function render(resetPage=false){
    if(resetPage)currentPage=1;
    let items=jobs.filter(matches);
    if(sort.value==="pay-high")items.sort((a,b)=>payHigh(b)-payHigh(a));
    if(sort.value==="location")items.sort((a,b)=>(a.state+a.city).localeCompare(b.state+b.city));
    if(sort.value==="newest")items.sort((a,b)=>(Date.parse(b.posted)||0)-(Date.parse(a.posted)||0));

    const count=items.length;
    const totalPages=Math.max(1,Math.ceil(count/PAGE_SIZE));
    if(currentPage>totalPages)currentPage=totalPages;
    const start=(currentPage-1)*PAGE_SIZE;
    const end=Math.min(start+PAGE_SIZE,count);
    const visibleItems=items.slice(start,end);

    list.innerHTML=visibleItems.map(job=>`
      <article class="job-card cat-${slug(job.category)}" data-job-id="${job.id}" data-ats-template="job-card" data-ats-category="${job.category}">
        <div class="job-card-main">
          <div class="job-badges">
            <span class="job-badge">${job.category}</span>
            <span class="job-badge alt">${job.profession||job.type}</span>
          </div>
          <h3>${job.title}</h3>
          <div class="job-location-line"><span class="job-location-dot"></span><span>${job.city}, ${job.state}</span></div>
          ${showSpecialty(job)?`<div class="job-specialty-line">Specialty: <strong>${showSpecialty(job)}</strong></div>`:""}
          <div class="job-detail-grid">
            <div class="job-detail"><small>Starts</small><strong>${job.start||"Ask recruiter"}</strong></div>
            <div class="job-detail"><small>Posted</small><strong>${formatPosted(job.posted)}</strong></div>
            <div class="job-detail job-id"><small>Job ID</small><strong>${job.id}</strong></div>
          </div>
        </div>
        <div class="job-card-side">
          <span class="job-pay-label">Pay range</span>
          <div class="job-pay">${job.pay||"Ask recruiter"}</div>
          <a class="job-apply" href="${job.applyUrl||"https://www.medlivo.com/search-jobs"}" data-ats-apply-id="${job.id}" aria-label="Open Medlivo’s current job search to check ${job.title}">View Current Jobs</a>
          <span class="job-ats-note">Confirm availability with Medlivo</span>
        </div>
      </article>`).join("");

    noResults.hidden=count!==0;
    list.hidden=count===0;
    const scope=profession.value
      ? (profession.options[profession.selectedIndex]?.text||profession.value)
      : specialty.value||activeCategory;
    summary.textContent=count
      ? `${count.toLocaleString("en-US")} job${count===1?"":"s"} found${scope?` for ${scope}`:""}`
      : "No jobs match these selections. A recruiter can help check current availability.";

    const showPagination=count>PAGE_SIZE;
    pagination.hidden=!showPagination;
    if(count){
      paginationSummary.textContent=`Showing jobs ${start+1}–${end} of ${count.toLocaleString("en-US")}`;
      paginationPage.textContent=`Page ${currentPage} of ${totalPages}`;
      prevPage.disabled=currentPage<=1;
      nextPage.disabled=currentPage>=totalPages;
    }
    updateDivisionUI();
    saveSearch();
  }
  function setDivision(category){
    activeCategory=normalizeCategory(category);
    division.value=activeCategory;
    setProfession("");
    specialty.value="";
    rebuildProfessionOptions();
    rebuildSpecialtyOptions();
    render(true);
  }

  const params=new URLSearchParams(window.location.search);
  let requestedDivision=normalizeCategory(params.get("division")||"");
  const legacyProfession=params.get("profession")||"";
  const normalizedLegacy=normalizeCategory(legacyProfession);
  if(!requestedDivision && ["Nursing & Allied","Rehabilitation","Locum Tenens"].includes(normalizedLegacy)){
    requestedDivision=normalizedLegacy;
  }
  activeCategory=requestedDivision;
  division.value=activeCategory;
  rebuildProfessionOptions();
  const requestedProfession=(activeCategory && normalizeCategory(legacyProfession)===activeCategory)?"":legacyProfession;
  if(requestedProfession && [...profession.options].some(o=>o.value===requestedProfession))setProfession(requestedProfession);
  if(params.has("type") && [...profession.options].some(o=>o.value===params.get("type")))setProfession(params.get("type"));
  rebuildSpecialtyOptions(params.get("specialty")||"");
  if(params.has("location"))locationInput.value=params.get("location")||"";
  if(params.has("state"))filterState.value=(params.get("state")||"").toUpperCase();

  qs("#jobsSearchForm").addEventListener("submit",e=>{
    e.preventDefault();
    activeCategory=normalizeCategory(division.value);
    rebuildProfessionOptions(profession.value);
    rebuildSpecialtyOptions(specialty.value);
    render(true);
    qs(".jobs-results-section")?.scrollIntoView({behavior:"smooth",block:"start"});
  });

  division.addEventListener("change",()=>{
    activeCategory=normalizeCategory(division.value);
    setProfession("");
    specialty.value="";
    rebuildProfessionOptions();
    rebuildSpecialtyOptions();
    render(true);
  });
  profession.addEventListener("change",()=>{
    setProfession(profession.value);
    if(!activeCategory && profession.value){
      const inferred=findDivisionForProfession(profession.value);
      if(inferred){
        activeCategory=inferred;
        division.value=inferred;
        rebuildProfessionOptions(profession.value);
        setProfession(profession.value);
      }
    }
    rebuildSpecialtyOptions();
    render(true);
  });
  specialty.addEventListener("change",()=>render(true));
  [filterState,sort].forEach(el=>el.addEventListener("change",()=>render(true)));

  qsa(".jobs-division-card").forEach(btn=>btn.addEventListener("click",()=>setDivision(btn.dataset.category||"")));
  allButton.addEventListener("click",()=>{
    activeCategory="";
    division.value="";
    setProfession("");
    specialty.value="";
    rebuildProfessionOptions();
    rebuildSpecialtyOptions();
    render(true);
  });

  function clearAll(){
    activeCategory="";
    division.value="";
    setProfession("");
    specialty.value="";
    locationInput.value="";
    filterState.value="";
    rebuildProfessionOptions();
    rebuildSpecialtyOptions();
    render(true);
  }
  qs("#clearFilters").addEventListener("click",clearAll);
  qs("#viewAllJobs").addEventListener("click",clearAll);

  prevPage.addEventListener("click",()=>{
    if(currentPage<=1)return;
    currentPage--;
    render();
    qs(".jobs-results-head")?.scrollIntoView({behavior:"smooth",block:"start"});
  });
  nextPage.addEventListener("click",()=>{
    currentPage++;
    render();
    qs(".jobs-results-head")?.scrollIntoView({behavior:"smooth",block:"start"});
  });

  // Keep the selected search shareable without a page reload. No backend submission.
  function saveSearch(){
    if(!searchReady || !/^https?:$/.test(window.location.protocol))return;
    const url=new URL(window.location.href);
    for(const key of ['division','profession','specialty','location','state','type'])url.searchParams.delete(key);
    for(const [key,value] of Object.entries({division:activeCategory,profession:profession.value,specialty:specialty.value,location:locationInput.value.trim(),state:filterState.value}))if(value)url.searchParams.set(key,value);
    history.replaceState(null,'',url);
  }
  locationInput.addEventListener('change',()=>render(true));
  render();
  searchReady=true;
})();
