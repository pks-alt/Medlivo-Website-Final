
const form=document.querySelector('#staffingRequestForm');
const status=document.querySelector('#formStatus');
// Carry the division into the existing form. Ignore unrecognized query values.
const requestParams = new URLSearchParams(window.location.search);
const requestedDivision = requestParams.get('division');
const divisionInput = form.querySelector('[name="division"]');
if (requestedDivision && [...divisionInput.options].some(option => option.value === requestedDivision)) {
  divisionInput.value = requestedDivision;
}

// Carry additional structured lead details from Ask Medlivo into the form.
['role','location','start','count'].forEach(name=>{
  const value=requestParams.get(name);
  const field=form.querySelector('[name="'+name+'"]');
  if(value && field) field.value=value;
});

form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;const d=new FormData(form);const v=n=>(d.get(n)||'').toString().trim();const subject=encodeURIComponent((v('division')||'Healthcare Staffing')+' Staffing Request - '+v('organization'));const body=['Healthcare Staffing Request','','Division: '+v('division'),'Role / Specialty: '+v('role'),'Organization / Facility: '+v('organization'),'Location: '+v('location'),'Start Timing: '+v('start'),'Number Needed: '+v('count'),'','Contact Name: '+v('contact'),'Work Email: '+v('email'),'Phone: '+v('phone'),'','Additional Details:',v('details')].join('\n');if(status)status.textContent='Opening your email app with the request filled in. Please send the email to complete your request.';window.location.href='mailto:hello@medlivo.com?subject='+subject+'&body='+encodeURIComponent(body);});
