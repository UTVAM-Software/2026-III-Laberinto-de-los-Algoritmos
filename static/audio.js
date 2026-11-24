/* Melodías originales sintetizadas localmente: no requieren internet ni archivos externos. */
(() => {
  let context, enabled = false;
  const voices = new Set();
  function stop() {
    for (const voice of voices) {
      try { voice.stop(); } catch {}
    }
    voices.clear();
  }
  function note(frequency, start, duration, volume = 0.055) {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = 'triangle';
    oscillator.frequency.setValueAtTime(frequency, start);
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(volume, start + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.001, start + duration);
    oscillator.connect(gain);
    gain.connect(context.destination);
    voices.add(oscillator);
    oscillator.onended = () => {
      voices.delete(oscillator);
      oscillator.disconnect();
      gain.disconnect();
    };
    oscillator.start(start);
    oscillator.stop(start + duration + 0.03);
  }
  function play(kind) {
    if (!enabled || !context || context.state !== 'running') return;
    try {
      if (kind === 'correct') {
        note(660, context.currentTime, 0.16, 0.025);
        return;
      }
      if (!['won', 'lost', 'virus'].includes(kind)) return;
      stop();
      const win = kind === 'won';
      const melody = win
        ? [[523.25,0.18],[659.25,0.18],[783.99,0.18],[1046.5,0.36],[783.99,0.18],[1046.5,0.65]]
        : [[392,0.3],[349.23,0.3],[311.13,0.35],[261.63,0.7]];
      let time = context.currentTime + 0.02;
      for (const [frequency, duration] of melody) {
        note(frequency, time, duration);
        time += duration + 0.07;
      }
      const chord = win ? [261.63,329.63,392] : [130.81,155.56,196];
      for (const frequency of chord) note(frequency, time - 0.65, 0.9, 0.018);
    } catch { /* El audio nunca debe impedir una respuesta o un resultado. */ }
  }
  window.LabAudio = {
    setEnabled(value) {
      enabled = Boolean(value);
      if (!enabled) { stop(); return; }
      try {
        const Audio = window.AudioContext || window.webkitAudioContext;
        if (!Audio) return;
        context = context || new Audio();
        // Se invoca desde el clic del usuario para habilitar audio en el navegador.
        context.resume().catch(() => {});
      } catch {}
    },
    play,
    stop,
  };
  window.addEventListener('pagehide', stop);
})();
