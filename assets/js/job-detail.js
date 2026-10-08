(function(){
  const qs=s=>document.querySelector(s);
  const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const params=new URLSearchParams(location.search),id=params.get("id");
  const title=qs("#jobTitle"),summary=qs("#jobSummary"),meta=qs("#jobMeta"),content=qs("#jobContent"),facts=qs("#jobFactList"),apply=qs("#applyNow");
  const labelMap={profession:"Profession",specialty:"Specialty",city:"City",state:"State",care_setting:"Setting",shift:"Shift",schedule:"Schedule",start_date:"Start Date",end_date:"End Date",duration_weeks:"Duration",openings:"Openings",rate_unit:"Rate Unit",remote_allowed:"Remote",travel_required:"Travel"};
  function fact(key,value){if(value===null||value===undefined||value==="")return "";let display=value;if(typeof value==="boolean")display=value?"Yes":"No";if(key==="duration_weeks")display=value+" weeks";return '<div class="job-fact"><small>'+esc(labelMap[key]||key.replaceAll("_"," "))+'</small><strong>'+esc(display)+'</strong></div>';}
  async function load(){
    if(!id){showError("This job link is incomplete.");return;}
    try{
      const response=await fetch('/api/careers/jobs/'+encodeURIComponent(id),{headers:{Accept:"application/json"},cache:"no-store"});
      if(response.status===404){showError("This job is no longer available.");return;}
      if(!response.ok)throw new Error();
      const job=await response.json();
      title.textContent=job.title;summary.textContent=job.summary||"Review this current Medlivo opportunity.";
      document.title=job.title+" | Medlivo";
      const locationText=[job.city,job.state].filter(Boolean).join(", ");
      meta.innerHTML=[job.division?job.division.replaceAll("_"," "):"",job.profession,job.specialty,locationText].filter(Boolean).map(x=>'<span>'+esc(x)+'</span>').join("");
      content.innerHTML=(job.sections||[]).map(section=>'<section class="job-section"><h2>'+esc(section.heading)+'</h2><p>'+esc(section.content)+'</p></section>').join("")||'<div class="job-error"><h2>Details are being confirmed.</h2><p>Please contact a Medlivo recruiter for the latest information.</p></div>';
      facts.innerHTML=Object.entries(job.public_fields||{}).filter(([key])=>labelMap[key]).map(([key,value])=>fact(key,value)).join("");
      if(!facts.innerHTML)facts.innerHTML='<p>Contact Medlivo to confirm assignment details.</p>';
      const subject='Interest in '+job.title+' - Job '+String(job.id).slice(0,8).toUpperCase();
      apply.href='mailto:hello@medlivo.com?subject='+encodeURIComponent(subject);
      const canonical='https://www.medlivo.com/job.html?id='+encodeURIComponent(job.id);
      let link=document.querySelector('link[rel="canonical"]');if(link)link.href=canonical;
      const ld={"@context":"https://schema.org","@type":"JobPosting","title":job.title,"description":job.summary||job.title,"identifier":{"@type":"PropertyValue","name":"Medlivo","value":job.id},"hiringOrganization":{"@type":"Organization","name":"Medlivo","sameAs":"https://www.medlivo.com"}};
      if(job.city||job.state)ld.jobLocation={"@type":"Place","address":{"@type":"PostalAddress","addressLocality":job.city||undefined,"addressRegion":job.state||undefined,"addressCountry":"US"}};
      if(job.start_date)ld.datePosted=job.start_date;
      const script=document.createElement("script");script.type="application/ld+json";script.textContent=JSON.stringify(ld);document.head.appendChild(script);
    }catch{showError("Current job details are temporarily unavailable.");}
  }
  function showError(message){title.textContent="Job unavailable";summary.textContent=message;meta.innerHTML="";content.innerHTML='<div class="job-error"><h2>'+esc(message)+'</h2><p>Search current Medlivo opportunities or contact a recruiter for help.</p><p><a class="btn btn-primary" href="search-jobs.html">Search Jobs</a></p></div>';facts.innerHTML="";}
  load();
})();