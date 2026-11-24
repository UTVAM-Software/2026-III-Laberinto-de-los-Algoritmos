/* Amplía la pestaña actual sin abandonar la partida ni duplicar sus controles. */
(() => {
  const buttons = document.querySelectorAll('[data-fullscreen]');
  if (!buttons.length) return;
  const sync = () => {
    const active = Boolean(document.fullscreenElement) || document.body.classList.contains('presentation-mode');
    buttons.forEach(button => {
      button.textContent = active ? 'Salir de pantalla completa' : 'Pantalla completa';
      button.setAttribute('aria-pressed', String(active));
    });
  };
  buttons.forEach(button => button.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (document.body.classList.contains('presentation-mode')) document.body.classList.remove('presentation-mode');
      else if (document.fullscreenEnabled) await document.documentElement.requestFullscreen();
      else document.body.classList.add('presentation-mode');
    } catch {
      // Algunos navegadores bloquean Fullscreen: conservar un modo ampliado reversible.
      if (!document.fullscreenElement) document.body.classList.toggle('presentation-mode');
    }
    sync();
  }));
  document.addEventListener('fullscreenchange', sync);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      document.body.classList.remove('presentation-mode');
      sync();
    }
  });
})();
