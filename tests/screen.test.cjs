const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/screen.js'), 'utf8');
function setup(enabled, reject=false) {
  const classes = new Set(), events = {}, attrs = {};
  const button = {addEventListener: (_, fn) => button.click=fn, setAttribute: (k,v)=>attrs[k]=v};
  const doc = {fullscreenEnabled: enabled, fullscreenElement: null,
    querySelectorAll: ()=>[button], addEventListener:(k,v)=>events[k]=v,
    body:{classList:{contains:x=>classes.has(x),remove:x=>classes.delete(x),add:x=>classes.add(x),toggle:x=>classes.has(x)?classes.delete(x):classes.add(x)}},
    documentElement:{requestFullscreen:async()=>{if(reject)throw Error('denied');doc.fullscreenElement={};}},
    exitFullscreen:async()=>{doc.fullscreenElement=null;}
  };
  vm.runInNewContext(source, {document:doc});
  return {button, doc, attrs, events, classes};
}
test('enters and exits fullscreen without navigation',async()=>{
  const x=setup(true);await x.button.click();assert.equal(x.attrs['aria-pressed'],'true');
  await x.button.click();assert.equal(x.doc.fullscreenElement,null);assert.equal(x.attrs['aria-pressed'],'false');
});
test('browser Escape updates the button',async()=>{
  const x=setup(true);await x.button.click();x.doc.fullscreenElement=null;x.events.fullscreenchange();
  assert.equal(x.button.textContent,'Pantalla completa');
});
for(const [label,enabled,reject] of [['unsupported',false,false],['rejected',true,true]]) {
 test(label+' fullscreen uses reversible presentation mode',async()=>{
   const x=setup(enabled,reject);await x.button.click();assert(x.classes.has('presentation-mode'));
   await x.button.click();assert(!x.classes.has('presentation-mode'));
   await x.button.click();x.events.keydown({key:'Escape'});assert(!x.classes.has('presentation-mode'));
   assert.equal(x.attrs['aria-pressed'],'false');
 });
}
