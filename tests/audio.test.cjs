const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function setup() {
 const notes=[];
 class AudioContext {
  constructor(){this.currentTime=10;this.state='running';this.destination={};}
  resume(){return Promise.resolve();}
  createOscillator(){const n={frequency:{setValueAtTime:f=>n.frequencyValue=f},connect(){},disconnect(){},start:t=>n.startAt=t,stop:t=>n.stopAt=t};notes.push(n);return n;}
  createGain(){return {gain:{setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){},disconnect(){}};}
 }
 const window={AudioContext,addEventListener(){}};
 vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../static/audio.js'),'utf8'),{window});
 return {audio:window.LabAudio,notes};
}
test('muted by default and voluntary exit is silent',()=>{
 const x=setup();x.audio.play('won');assert.equal(x.notes.length,0);
 x.audio.setEnabled(true);x.audio.play('abandoned');assert.equal(x.notes.length,0);
});
test('victory and defeat have distinct finite melodies',()=>{
 for(const result of ['won','lost','virus']){
  const x=setup();x.audio.setEnabled(true);x.audio.play(result);
  assert(x.notes.length>3);assert.equal(x.notes[0].frequencyValue,result==='won'?523.25:392);
  assert(x.notes.every(n=>n.stopAt>n.startAt&&n.stopAt<14));
 }
});
test('muting cancels scheduled notes and prevents subsequent playback',()=>{
 const x=setup();x.audio.setEnabled(true);x.audio.play('won');x.audio.setEnabled(false);
 assert(x.notes.every(n=>n.stopAt===undefined));const count=x.notes.length;
 x.audio.play('lost');assert.equal(x.notes.length,count);
});
