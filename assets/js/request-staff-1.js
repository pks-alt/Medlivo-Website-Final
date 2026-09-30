const form=document.querySelector('#staffingRequestForm');
const status=document.querySelector('#formStatus');
const submitButton=form?.querySelector('.submit-btn');
const API_BASE='https://medlivo-ai-agent-397967014447.us-west1.run.app';

// Carry structured details from Ask Medlivo into the form.
const requestParams=new URLSearchParams(window.location.search);
const requestedDivision=requestParams.get('division');
const divisionInput=form?.querySelector('[name="division"]');
if(requestedDivision && divisionInput && [...divisionInput.options].some(option=>option.value===requestedDivision)){
  divisionInput.value=requestedDivision;
}
['role','location','start','count'].forEach(name=>{
  const value=requestParams.get(name);
  const field=form?.querySelector('[name="'+name+'"]');
  if(value && field)field.value=value;
});

function value(formData,name){
  return (formData.get(name)||'').toString().trim();
}

function fallbackEmail(formData){
  const subject=encodeURIComponent((value(formData,'division')||'Healthcare Staffing')+' Staffing Request - '+value(formData,'organization'));
  const body=[
    'Healthcare Staffing Request','',
    'Division: '+value(formData,'division'),
    'Role / Specialty: '+value(formData,'role'),
    'Organization / Facility: '+value(formData,'organization'),
    'Location: '+value(formData,'location'),
    'Start Timing: '+value(formData,'start'),
    'Number Needed: '+value(formData,'count'),'',
    'Contact Name: '+value(formData,'contact'),
    'Work Email: '+value(formData,'email'),
    'Phone: '+value(formData,'phone'),'',
    'Additional Details:',
    value(formData,'details')
  ].join('\n');
  window.location.href='mailto:hello@medlivo.com?subject='+subject+'&body='+encodeURIComponent(body);
}

form?.addEventListener('submit',async e=>{
  e.preventDefault();
  if(!form.reportValidity())return;

  const data=new FormData(form);
  const payload={
    organization:value(data,'organization'),
    contactName:value(data,'contact'),
    workEmail:value(data,'email'),
    phone:value(data,'phone'),
    division:value(data,'division'),
    role:value(data,'role'),
    location:value(data,'location'),
    startTiming:value(data,'start'),
    numberNeeded:value(data,'count'),
    notes:value(data,'details'),
    source:requestParams.get('source')||'Request Staff'
  };

  if(status)status.textContent='Sending your staffing request securely to Medlivo…';
  if(submitButton){
    submitButton.disabled=true;
    submitButton.textContent='Sending…';
  }

  try{
    const response=await fetch(API_BASE+'/api/leads/client',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });

    if(!response.ok){
      const detail=await response.text().catch(()=> '');
      throw new Error('Lead API '+response.status+' '+detail);
    }

    const result=await response.json();
    if(status)status.textContent='Thank you. Your request has been received. A Medlivo team member will follow up with you.';
    if(submitButton)submitButton.textContent='Request Received';
    form.reset();
    if(result?.leadId)form.dataset.leadId=result.leadId;
  }catch(error){
    console.error('Medlivo staffing request submission failed',error);
    if(status)status.textContent='We could not submit the request online. Opening your email app as a fallback.';
    if(submitButton){
      submitButton.disabled=false;
      submitButton.textContent='Submit Staffing Request';
    }
    fallbackEmail(data);
  }
});
