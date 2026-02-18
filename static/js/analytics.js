(function(){
 function track(event, props){
  try{
   fetch('/api/track', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({event:event, props:props||{}, ts: Date.now()})
   }).catch(()=>{});
  }catch(e){}
 }
 // Track any element with data-track
 document.addEventListener('click', (e)=>{
  const el = e.target.closest('[data-track]');
  if(!el) return;
  const name = el.getAttribute('data-track');
  const plan = el.getAttribute('data-plan') || undefined;
  track(name, {plan: plan, href: el.getAttribute('href') || undefined});
 });
 // Track plan change on get-started select
 const planSel = document.querySelector('select[name="plan"]');
 if(planSel){
  planSel.addEventListener('change', ()=>{
   track('plan_select', {plan: planSel.value});
  });
 }
})();
