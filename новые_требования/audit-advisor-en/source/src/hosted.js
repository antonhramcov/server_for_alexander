import {mountAssessment} from './ui.js';
import {createConfig,validateCopy} from './content.js';
import {escapeHTML} from './export.js';
import {stagesHTML} from './stages.js';

// No question or editorial copy is bundled here. JSON remains directly editable.
const script=document.currentScript;
const root=document.getElementById(script?.dataset.rootId||'aa-iso-readiness');
const base=new URL('./',script.src), attempt=script.dataset.attempt;
const active=()=>root&&root.dataset.loadAttempt===attempt;
async function json(path) {
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
  try {
    const response=await fetch(new URL('content/'+path,base),{signal:controller.signal,cache:'no-cache',credentials:'omit'});
    if(!response.ok)throw new Error('Content HTTP '+response.status+': '+path);
    return await response.json();
  } finally {clearTimeout(timer);}
}
async function initialize() {
  if(!active()||root.dataset.initialized==='true')return;
  try {
    const manifest=await json('catalog.json');
    if(manifest.schemaVersion!==1||!/^interface\.(ru|en)\.json$/.test(manifest.interfaceFile)||!Array.isArray(manifest.standards))throw new Error('Invalid content catalog');
    const ids=new Set();
    for(const item of manifest.standards){
      if(!/^[a-z0-9-]+$/.test(item.id)||ids.has(item.id)||!['ready','planned'].includes(item.status)||typeof item.label!=='string')throw new Error('Invalid catalog entry');
      if(item.status==='ready'&&item.file!=='standards/'+item.id+'.json')throw new Error('Invalid questionnaire path');
      ids.add(item.id);
    }
    const copy=validateCopy(await json(manifest.interfaceFile));
    if(!active())return;
    const e=escapeHTML,selector=root.querySelector('#aa-standard');
    root.querySelector('#aa-tool-title').textContent=copy.welcome.heading;
    root.querySelector('.aa-lead').textContent=copy.welcome.description;
    root.querySelector('#aa-selection-label').textContent=copy.welcome.selectionLabel;
    root.querySelector('#aa-selection-info').textContent=copy.welcome.selectionHint;
    root.querySelector('#aa-stages').innerHTML=stagesHTML({sections:copy.stages.sections},copy);
    selector.innerHTML=`<option value="" selected disabled>${e(copy.welcome.selectionPlaceholder)}</option>`+manifest.standards.map(item=>`<option value="${e(item.id)}"${item.status==='ready'?'':' disabled'}>${e(item.label)}${item.status==='ready'?'':' — '+e(copy.selection.planned)}</option>`).join('');
    selector.disabled=false;
    root.querySelector('[data-action="start"]').textContent=copy.navigation.start+' →';
    const catalog=manifest.standards.map(item=>{
      let pending;
      return {...item,load:()=>pending||(pending=json(item.file).then(doc=>{
        if(doc.id!==item.id)throw new Error('Questionnaire identifier does not match catalog');
        return createConfig(doc,copy);
      }).catch(error=>{pending=null;throw error;}))};
    });
    mountAssessment(root,catalog,copy);
    root.dataset.initialized='true';
    root.dispatchEvent(new CustomEvent('aa:ready'));
  } catch(error) {
    if(active()){console.error('Audit Advisor:',error.message);root.dispatchEvent(new CustomEvent('aa:load-error'));}
  }
}
initialize();
