(function() {
  const burger = document.querySelector('[data-burger]');
  const overlay = document.querySelector('[data-overlay]');
  const drawer = document.querySelector('[data-drawer]');
  const closeBtn = document.querySelector('[data-close]');
  const links = document.querySelectorAll('[data-drawer] a');

  function open() {
    if (!overlay || !drawer) return;
    overlay.style.display = 'block';
    drawer.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    if (!overlay || !drawer) return;
    drawer.classList.remove('open');
    overlay.style.display = 'none';
    document.body.style.overflow = '';
  }

  if (burger) burger.addEventListener('click', open);
  if (closeBtn) closeBtn.addEventListener('click', close);
  if (overlay) overlay.addEventListener('click', close);
  links.forEach(a => a.addEventListener('click', close));

  window.addEventListener('resize', function() {
    if (window.innerWidth > 820) close();
  });
})();
