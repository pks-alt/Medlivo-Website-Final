
const navDropdowns=[...document.querySelectorAll('.nav-dropdown')];
function closeNavDropdowns(except=null){
  navDropdowns.forEach(dropdown=>{
    if(dropdown===except)return;
    dropdown.classList.remove('open');
    const trigger=dropdown.querySelector('.nav-drop-trigger');
    if(trigger)trigger.setAttribute('aria-expanded','false');
  });
}
navDropdowns.forEach(dropdown=>{
  const trigger=dropdown.querySelector('.nav-drop-trigger');
  if(!trigger)return;
  trigger.addEventListener('click',(e)=>{
    e.preventDefault();
    const willOpen=!dropdown.classList.contains('open');
    closeNavDropdowns(dropdown);
    dropdown.classList.toggle('open',willOpen);
    trigger.setAttribute('aria-expanded',String(willOpen));
  });
});
document.addEventListener('click',(e)=>{
  if(!e.target.closest('.nav-dropdown'))closeNavDropdowns();
});
document.addEventListener('keydown',(e)=>{
  if(e.key==='Escape'){
    const openDropdown=document.querySelector('.nav-dropdown.open');
    const trigger=openDropdown?.querySelector('.nav-drop-trigger');
    closeNavDropdowns();
    if(trigger)trigger.focus();
  }
});
