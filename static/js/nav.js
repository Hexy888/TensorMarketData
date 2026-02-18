(function(){
 // Mobile menu
 const openBtn = document.querySelector('[data-nav-open]');
 const closeBtn = document.querySelector('[data-nav-close]');
 const menu = document.querySelector('[data-mobile-menu]');
 const links = document.querySelectorAll('[data-mobile-menu] a');
 function open(){ if(!menu) return; menu.classList.add('open'); document.body.style.overflow = 'hidden'; }
 function close(){ if(!menu) return; menu.classList.remove('open'); document.body.style.overflow = ''; }
 if(openBtn) openBtn.addEventListener('click', open);
 if(closeBtn) closeBtn.addEventListener('click', close);
 if(menu) menu.addEventListener('click', (e)=>{ if(e.target === menu) close(); });
 links.forEach(a => a.addEventListener('click', close));

 // Accordion
 document.querySelectorAll('[data-accordion]').forEach((wrap)=>{
  wrap.querySelectorAll('[data-acc-item]').forEach((item)=>{
   const btn = item.querySelector('[data-acc-btn]');
   const panel = item.querySelector('[data-acc-panel]');
   if(!btn || !panel) return;
   btn.addEventListener('click', ()=>{
    const open = item.classList.contains('open');
    wrap.querySelectorAll('[data-acc-item]').forEach(x=>x.classList.remove('open'));
    if(!open) item.classList.add('open');
   });
  });
 });
})();
