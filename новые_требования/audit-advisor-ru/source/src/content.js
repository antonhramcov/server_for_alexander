import {validateConfig} from './validation.js';
import {COPY_CONTRACT} from './copy-contract.js';

export function formatText(template,values={}) {
  return String(template).replace(/\{([a-zA-Z]+)\}/g,(match,key)=>Object.hasOwn(values,key)?String(values[key]):match);
}
const fail=(path,message)=>{throw new Error(`${path}: ${message}`);};
const string=(value,path,empty=false)=>{if(typeof value!=='string'||!empty&&!value.trim())fail(path,'expected text');};
const paragraphs=(value,path)=>{if(!Array.isArray(value)||!value.length)fail(path,'expected a non-empty list of paragraphs');value.forEach((v,i)=>string(v,`${path}[${i}]`));};
const answerValues=['yes','partial','no','na','no_events'];

function checkContract(value,contract,path) {
  if(typeof contract==='string'){if(typeof value!==contract||contract==='string'&&!value.trim())fail(path,'missing or invalid '+contract);return;}
  if(Array.isArray(contract)){if(!Array.isArray(value)||!value.length)fail(path,'expected a non-empty list');value.forEach((v,i)=>checkContract(v,contract[0],path+'['+i+']'));return;}
  if(!value||typeof value!=='object')fail(path,'expected an object');
  for(const [key,nested] of Object.entries(contract))checkContract(value[key],nested,path+'.'+key);
}
export function validateCopy(copy) {
  checkContract(copy,COPY_CONTRACT,'interface');
  if(copy?.schemaVersion!==1)fail('interface.schemaVersion','unsupported version');
  for(const group of ['welcome','stages','navigation','question','answerPresets','feedback','milestones','plan','loading','storage','results','seo'])if(!copy[group]||typeof copy[group]!=='object')fail('interface.'+group,'missing text group');
  for(const [name,preset] of Object.entries(copy.answerPresets)){
    if(!['documents','practice'].includes(name)||!Array.isArray(preset))fail('answerPresets.'+name,'invalid preset');
    const expected=[...(name==='documents'?['yes','no','na','no_events']:answerValues),...(preset.some(o=>o.value==='unsure')?['unsure']:[])];
    if(preset.length!==expected.length||new Set(preset.map(o=>o.value)).size!==expected.length||expected.some(v=>!preset.some(o=>o.value===v)))fail('answerPresets.'+name,'answer values cannot be added, removed or renamed');
    for(const option of preset){string(option.label,`answerPresets.${name}.${option.value}.label`);string(option.description,`answerPresets.${name}.${option.value}.description`);}
  }
  for(const key of answerValues)string(copy.feedback[key],'feedback.'+key);
  if(Object.values(copy.answerPresets).some(p=>p.some(o=>o.value==='unsure'))){
    for(const [value,path] of [[copy.feedback.unsure,'feedback.unsure'],[copy.answerStatuses.unsure,'answerStatuses.unsure'],[copy.plan.whenUnsurePrefix,'plan.whenUnsurePrefix']])string(value,path);
  }
  if(copy.assessment.levels[0].min!==0||copy.assessment.levels.some((level,i)=>level.min<0||level.min>100||i&&level.min<=copy.assessment.levels[i-1].min))fail('assessment.levels','thresholds must increase from zero');
  for(const group of ['welcome','navigation','question','plan','loading','storage','results','seo'])for(const [key,value] of Object.entries(copy[group]))string(value,`${group}.${key}`);
  if(!Array.isArray(copy.stages.sections)||!copy.stages.sections.length)fail('stages.sections','missing sections');
  return copy;
}

export function validateStandardDocument(doc,copy) {
  const path=doc?.id||'standard';
  if(doc?.schemaVersion!==1)fail(path+'.schemaVersion','unsupported version');
  if(!/^[a-z0-9-]+$/.test(doc.id))fail(path+'.id','invalid stable identifier');
  string(doc.answerVersion,path+'.answerVersion');string(doc.contentRevision,path+'.contentRevision');
  for(const key of ['heading','description','duration'])string(doc.page?.[key],path+'.page.'+key);
  string(doc.standard?.label,path+'.standard.label');
  if(doc.guidance){
    paragraphs(doc.guidance.instructions,path+'.guidance.instructions');
    if(!Array.isArray(doc.guidance.sections))fail(path+'.guidance.sections','expected sections');
    for(const [i,section] of doc.guidance.sections.entries()){
      string(section.heading,`${path}.guidance.sections[${i}].heading`);
      paragraphs(section.paragraphs,`${path}.guidance.sections[${i}].paragraphs`);
      if(!Array.isArray(section.links))fail(path+'.guidance.links','expected links');
      for(const link of section.links){string(link.label,path+'.guidance.link.label');if(!/^https:\/\//.test(link.url))fail(path+'.guidance.link.url','expected HTTPS');}
    }
  }
  if(!Array.isArray(doc.questions)||!doc.questions.length)fail(path+'.questions','missing questions');
  for(const [index,q] of doc.questions.entries()){
    const p=path+'.questions['+index+']';
    if(!/^[A-Za-z0-9_-]+$/.test(q.id))fail(p+'.id','invalid stable identifier');
    for(const key of ['heading','section','clause'])string(q[key],p+'.'+key);
    paragraphs(q.description,p+'.description');paragraphs(q.examples,p+'.examples');
    string(q.condition,p+'.condition',true);
    const options=copy.answerPresets[q.answers?.preset];if(!options)fail(p+'.answers.preset','unknown answer preset');
    for(const [value,override] of Object.entries(q.answers.overrides||{})){
      if(!options.some(o=>o.value===value))fail(p+'.answers.overrides.'+value,'unknown answer value');
      for(const [key,text] of Object.entries(override)){if(!['label','description'].includes(key))fail(p+'.answers.overrides.'+value+'.'+key,'only labels and descriptions can be overridden');string(text,p+'.answers.overrides.'+value+'.'+key);}
    }
    for(const key of ['notApplicable','noEvents']){
      const rule=q.applicability?.[key];if(typeof rule?.allowed!=='boolean')fail(p+'.applicability.'+key,'expected allowed: true or false');
      string(rule.explanation,p+'.applicability.'+key+'.explanation',!rule.allowed);
    }
    if(typeof q.evaluation?.important!=='boolean')fail(p+'.evaluation.important','expected boolean');
    if(!Number.isFinite(q.evaluation?.priority)||q.evaluation.priority<1)fail(p+'.evaluation.priority','expected positive priority');
    for(const [key,text] of Object.entries(q.plan||{})){if(!['heading','whenNo','whenPartial','confirmation','strength'].includes(key))fail(p+'.plan.'+key,'unknown editorial field');string(text,p+'.plan.'+key,true);}
  }
  return doc;
}

export function createConfig(doc,copy) {
  validateStandardDocument(doc,copy);
  const questions=doc.questions.map((q,index)=>{
    const explanation=q.description.join('\n\n'), chapter=q.clause?.match(doc.id==='haccp-ru'?/^\d+(?:\.\d+)?/:/^(?:A\.)?\d+/)?.[0];
    const category=chapter?formatText(chapter.startsWith('A.')?copy.metadata.annex:copy.metadata.section,{chapter}):copy.metadata.general;
    const plan=q.plan||{},allowNA=q.applicability.notApplicable.allowed,allowNoEvents=q.applicability.noEvents.allowed;
    return {id:q.id,section:q.section,contentPointer:'/questions/'+index,text:q.heading,description:q.description,explanation,evidence:q.examples,condition:q.condition,clause:q.clause,
      responseMode:q.answers.preset==='documents'?'binary':'graded',
      answerOptions:copy.answerPresets[q.answers.preset].map((o,answerIndex)=>({...o,...q.answers.overrides?.[o.value],labelSource:q.answers.overrides?.[o.value]?.label?'content/standards/'+doc.id+'.json#/questions/'+index+'/answers/overrides/'+o.value+'/label':`content/interface.${copy.locale.split('-')[0]}.json#/answerPresets/`+q.answers.preset+'/'+answerIndex+'/label',descriptionSource:q.answers.overrides?.[o.value]?.description?'content/standards/'+doc.id+'.json#/questions/'+index+'/answers/overrides/'+o.value+'/description':`content/interface.${copy.locale.split('-')[0]}.json#/answerPresets/`+q.answers.preset+'/'+answerIndex+'/description'})).filter(o=>(o.value!=='na'||allowNA)&&(o.value!=='no_events'||allowNoEvents)),
      topic:category,category,planTitle:plan.heading||q.heading,
      weight:q.evaluation.weight,critical:q.evaluation.important,priority:q.evaluation.priority,
      allowNA,naExplanation:q.applicability.notApplicable.explanation,allowNoEvents,noEventsExplanation:q.applicability.noEvents.explanation,
      allowUnsure:copy.answerPresets[q.answers.preset].some(o=>o.value==='unsure'),
      recommendationNo:plan.whenNo||copy.plan.whenNoPrefix+' '+explanation,
      recommendationPartial:plan.whenPartial||copy.plan.whenPartialPrefix+' '+explanation,
      recommendationUnsure:copy.plan.whenUnsurePrefix?copy.plan.whenUnsurePrefix+' '+explanation:'',
      outcome:plan.confirmation||q.examples.join('\n'),outcomeLabel:copy.plan.confirmationHeading,statusLabels:copy.answerStatuses,
      strength:plan.strength||q.heading+' — '+(q.answers.preset==='documents'?copy.plan.positiveDocument:copy.plan.positivePractice),feedback:copy.feedback};
  });
  return validateConfig({id:doc.id,version:doc.answerVersion,contentRevision:doc.contentRevision,title:doc.page.heading,intro:doc.page.description,duration:doc.page.duration,
    source:doc.source.file,standard:doc.standard,sections:doc.sections,questions,applicabilityPairs:doc.applicabilityPairs||[],links:doc.links,disclaimer:doc.disclaimer,
    locale:copy.locale,timeZone:copy.locale==='ru-RU'?'Europe/Moscow':undefined,guidance:doc.guidance,
    priorityLabels:{1:copy.metadata.firstPriority,2:copy.metadata.nextPriority},copy,contentFile:'content/standards/'+doc.id+'.json'});
}
