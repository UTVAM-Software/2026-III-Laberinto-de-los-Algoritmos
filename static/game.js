/* La puntuación, los tiempos y el movimiento permitido vienen del servidor. */
(() => {
const root=document.getElementById('game');if(!root)return;
const stage=document.getElementById('stage'),notice=document.getElementById('connection');
const theme=JSON.parse(document.getElementById('world-theme').textContent);
const reduced=()=>window.LabAppearance?.reduced||matchMedia('(prefers-reduced-motion: reduce)').matches;
const control=root.dataset.controller==='yes',pub=root.dataset.public==='yes';
let state=null,key='',busy=false,polling=false,offset=0,showRoute=false,sound=false,revision=0;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const label=n=>String.fromCharCode(65+Math.floor(n/5))+(n%5+1);
function button(text,fn,cls='button'){const b=el('button',text,cls);b.type='button';b.onclick=fn;return b;}
function issue(text){notice.textContent=text;notice.hidden=false;}
function beep(){if(sound)window.LabAudio?.play('correct');}
const soundToggle=document.getElementById('sound-toggle');if(soundToggle)soundToggle.onclick=()=>{sound=!sound;window.LabAudio?.setEnabled(sound);soundToggle.textContent='Sonido: '+(sound?'encendido':'apagado');soundToggle.setAttribute('aria-pressed',String(sound));if(sound)beep();};
async function send(command,extra={}){
 if(busy)return;busy=true;revision++;stage.querySelectorAll('button').forEach(b=>b.disabled=true);
 try{const r=await fetch(root.dataset.action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':root.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({command,...extra})});
 if(!r.ok)throw Error('No se pudo guardar. Revisa la conexión o vuelve a iniciar sesión.');
 render(await r.json());notice.hidden=true;
 }catch(e){issue(e.message);}finally{busy=false;stage.querySelectorAll('button').forEach(b=>b.disabled=false);}
}
function moveMarker(grid,marker,n,instant=false){
 const cell=grid.querySelector(`[data-cell="${n}"]`);if(!cell)return;marker.dataset.cell=String(n);
 marker.style.transition=instant||reduced()?'none':'';marker.style.left=(cell.offsetLeft+cell.offsetWidth/2)+'px';marker.style.top=(cell.offsetTop+cell.offsetHeight/2)+'px';
}
function drawMaze(d,parent,previous){
 const box=el('div',undefined,'maze-panel');box.append(el('span',d.mode==='solo'?'TU ROBOT · TU CAMINO':'MAPA DEL GUÍA','eyebrow'),el('h2','A1 → '+label(d.board.goal)));
 const grid=el('div',undefined,'maze');grid.setAttribute('aria-label','Tablero 5 por 5; fila A abajo, E arriba.');
 const route=d.board.routes?.[0]||[];
 for(let row=4;row>=0;row--)for(let col=0;col<5;col++){
  const n=row*5+col,safe=d.board.safe.includes(n);
  const cell=el('div',undefined,'cell '+(safe?'safe':'virus')+(n===0?' start':'')+(n===d.board.goal?' goal':'')+(d.mode==='solo'&&route.slice(0,d.score+1).includes(n)?' visited':''));cell.dataset.cell=n;
  cell.append(el('span',label(n),'coordinate'));if(!safe){const virus=el('img',undefined,'virus-icon');virus.src=root.dataset.virus;virus.alt='Virus';cell.append(virus);}else{cell.append(el('strong',n===0?'INICIO':n===d.board.goal?'⚑':'·'));}cell.setAttribute('aria-label',label(n)+(n===d.board.goal?' Meta':safe?' Segura':' Virus'));
  if(showRoute && d.mode==='mission'&&route.includes(n))cell.classList.add('route');grid.append(cell);
 }
 box.append(grid,el('p',d.mode==='solo'?`${d.score} de ${d.total} pasos seguros`:'Arriba · Abajo · Izquierda · Derecha','maze-caption'));parent.append(box);
 if(d.mode==='solo'){
  const marker=el('div',undefined,'robot-token');const sprite=el('span',undefined,'companion '+theme.code);marker.append(sprite);marker.setAttribute('aria-label','Tu robot');grid.append(marker);
  const initial=d.state==='lost'?(d.board.crash_path?.[0]??route[d.score]):route[Math.min(previous?.score??d.score,d.score)];
  moveMarker(grid,marker,initial,true);
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
   if(d.state==='lost'){
    const path=d.board.crash_path||[initial];let step=1;
    const walk=()=>{if(!grid.isConnected)return;if(reduced()){moveMarker(grid,marker,path[path.length-1],true);showFinish(d);return;}if(step<path.length){moveMarker(grid,marker,path[step++]);setTimeout(walk,350);}else{grid.classList.add('infected');marker.classList.add('infected-token');showFinish(d);}};
    setTimeout(walk,250);
   }else{moveMarker(grid,marker,route[d.score]);if(d.state==='won')setTimeout(()=>showFinish(d),reduced()?0:650);}
  }));
 }
}
function hud(d,parent){
 const bar=el('div',undefined,'game-hud');bar.setAttribute('aria-live','polite');
 bar.append(el('span',`✦ ${d.score} aciertos`,'hud-correct'),el('span',`✹ ${d.errors} errores`,'hud-errors'),el('span',`${Math.min(d.state==='quiz'?d.current+1:d.current,d.total)} / ${d.total}`,'hud-progress'));
 const clock=el('span',d.seconds?'':'∞ Sin límite','clock');clock.id='clock';bar.append(clock);parent.append(bar);
}
function showFinish(d){
 if(stage.querySelector('.finish-alert'))return;
 const alert=el('div',undefined,'finish-alert '+(d.state==='won'?'victory':'defeat'));alert.setAttribute('role','alert');
 const title=d.state==='won'?theme.win:d.state==='abandoned'?'Misión interrumpida':d.state==='lost'&&d.mode!=='solo'?theme.quiz_loss:theme.loss;
 alert.append(el('span',undefined,'companion finish-companion '+theme.code),el('h2',title));
 alert.append(el('p',d.state==='won'?theme.win_detail:d.state==='abandoned'?'Tus aciertos se conservan. Vuelve cuando quieras.':theme.loss_detail));
 if(d.last_answer?.timeout)alert.append(el('p','Se acabó el tiempo de la pregunta.','timeout-note'));
 if(root.dataset.result){
  const actions=el('div',undefined,'actions centered');
  if(control&&root.dataset.retry){const form=el('form');form.method='POST';form.action=root.dataset.retry;const csrf=el('input');csrf.type='hidden';csrf.name='csrfmiddlewaretoken';csrf.value=root.querySelector('[name=csrfmiddlewaretoken]').value;const retry=el('button','↻ Volver a intentar','button');retry.type='submit';form.append(csrf,retry);actions.append(form);}
  const exit=el('a','Salir a los mundos','button secondary');exit.href=root.dataset.home||'/';actions.append(exit);alert.append(actions);
  const link=el('a','Ver lo que aprendí →','result-review');link.href=root.dataset.result;alert.append(link);
 }
 else alert.append(el('p',d.state==='virus'?'Recorrido finalizado.':`${d.score} aciertos`));
 stage.append(alert);if(sound)window.LabAudio?.play(d.state);if(d.state==='won'){document.body.classList.add('is-restored');window.LabCelebration?.play(alert,theme.code);}
}
function render(d){
 const previous=state;state=d;offset=Date.parse(d.server_now)-Date.now();
 const next=JSON.stringify([d.state,d.current,d.question,d.board,d.deadline]);if(next===key)return;key=next;stage.replaceChildren();stage.className='is-'+d.state;
 if(previous && d.current>previous.current && d.last_answer?.correct)beep(true);
 if(d.state==='ready'){
  const symbol=el('div',undefined,'stage-symbol');symbol.append(el('span',undefined,'companion '+theme.code));stage.append(symbol,el('span',d.category+' · '+(d.mode==='solo'?'INDIVIDUAL':'DINÁMICO'),'eyebrow'),el('h2',d.mode==='solo'?'Un acierto. Un paso.':'¡Preparen el equipo!'),el('p',d.mode==='solo'?`Tu ruta tiene ${d.total} movimientos. Llega a la meta sin fallar.`:'El participante se prepara para caminar a ciegas. El guía ve el mapa y confirma lo que ocurre.','muted'));
  stage.append(el('p',theme.intro,'mission-intro'));
  stage.append(el('p',d.seconds?`${d.seconds} segundos por pregunta`:'Alfa: piensa con calma, sin límite de tiempo.','pill'));
  if(control)stage.append(button(d.mode==='mission'?'Mostrar tablero e iniciar →':'¡A jugar! →',()=>send('start')));else stage.append(el('p','Esperando al guía…'));
 }else if(d.state==='board'){
  drawMaze(d,stage,previous);
  if(control){const actions=el('div',undefined,'actions centered');actions.append(button('✓ Llegó a la meta',()=>send('goal')),button('✹ Pisó un virus',()=>send('virus'),'button danger'));stage.append(actions,button(showRoute?'Ocultar solución':'Mostrar una solución',()=>{showRoute=!showRoute;key='';render(state);},'text-button'));}
 }else if(d.state==='quiz'){
  hud(d,stage);
  const layout=el('div',undefined,d.mode==='solo'?'solo-layout':'quiz-layout'),quiz=el('div',undefined,'question-panel');layout.append(quiz);stage.append(layout);
  quiz.append(el('span',`PREGUNTA ${d.current+1} · ${d.category}`,'eyebrow'),el('h2',d.question.text,'question-title'));
  const options=el('div',undefined,'options');d.question.options.forEach((option,i)=>{const b=control?button('',()=>send('answer',{position:d.question.position,selected:i}),'option'):el('div',undefined,'option');b.append(el('span','ABCD'[i],'option-letter'),el('span',option));options.append(b);});quiz.append(options);
  if(!control)quiz.append(el('p','Di tu respuesta al guía.','muted'));
  if(d.mode==='solo'){drawMaze(d,layout,previous);const companion=el('div',undefined,'companion-note');companion.append(el('span',undefined,'companion '+theme.code),el('span','Tú das las instrucciones. Tu ingenio abre el camino.'));quiz.append(companion);}
 }else{
  hud(d,stage);
  if(d.mode==='solo'&&d.board){const layout=el('div',undefined,'solo-layout');const words=el('div',undefined,'question-panel');words.append(el('span','ÚLTIMO MOVIMIENTO','eyebrow'),el('h2',d.state==='won'?'¡Llegaste a la meta!':d.state==='abandoned'?'Hasta la próxima aventura':'¡Cuidado, un desvío!'),el('p',d.last_answer?.timeout?'Se acabó el tiempo.':d.state==='won'?'Cada respuesta abrió un paso.':'Tu robot recorre el último tramo.'));layout.append(words);stage.append(layout);drawMaze(d,layout,previous);if(d.state==='abandoned')showFinish(d);}
  else showFinish(d);
 }
 if(control&&['ready','board','quiz'].includes(d.state))stage.append(button('Salir de este intento',()=>{if(confirm('¿Salir? Tus aciertos se conservarán.'))send('abandon');},'text-button exit-game'));
 updateClock();
}
function updateClock(){const c=document.getElementById('clock');if(c&&state?.deadline){const seconds=Math.max(0,Math.ceil((Date.parse(state.deadline)-Date.now()-offset)/1000));c.textContent='◷ '+seconds+' s';c.classList.toggle('urgent',seconds<=5);}}
async function poll(){if(polling||busy)return;polling=true;const version=revision;try{const r=await fetch(root.dataset.status,{cache:'no-store'});if(pub && r.status===404)throw Error('Esta proyección venció o ya no está disponible. Pide al guía que compruebe la partida y abra una proyección vigente.');if(r.redirected)throw Error('Tu sesión terminó. Vuelve a iniciar sesión para continuar. Tus respuestas guardadas se conservan.');if(!r.ok)throw Error('Se perdió la conexión o terminó tu sesión. Tus respuestas ya guardadas se conservan.');const d=await r.json();if(!busy&&version===revision){render(d);notice.hidden=true;}}catch(e){issue(e.message);}finally{polling=false;}}
window.addEventListener('resize',()=>{const marker=stage.querySelector('.robot-token');if(marker)moveMarker(marker.parentElement,marker,Number(marker.dataset.cell),true);});
setInterval(poll,700);setInterval(updateClock,100);poll();
})();
