export function selectableStandard(catalog,id) {
  return catalog.find(item=>item.id===id&&item.status==='ready'&&item.config)?.config || null;
}
export function validateConfig(config) {
  if(!config?.id||!config.version||!config.standard?.label||!config.questions?.length||!config.sections?.length)throw new Error('Incomplete standard configuration');
  const sectionIds=config.sections.map(s=>s.id), ids=config.questions.map(q=>q.id);
  if(new Set(ids).size!==ids.length||new Set(sectionIds).size!==sectionIds.length)throw new Error('Duplicate IDs');
  if(Math.abs(config.sections.reduce((sum,s)=>sum+s.share,0)-1)>1e-9||config.sections.some(s=>!Number.isFinite(s.share)||s.share<=0))throw new Error('Invalid section shares');
  let previous=-1;
  for(const q of config.questions){
    const position=sectionIds.indexOf(q.section);
    if(position<previous||position<0)throw new Error('Questions must follow the configured section order');
    previous=position;
    if(!Number.isFinite(q.weight)||q.weight<=0||q.allowNA&&!q.naExplanation||q.allowNoEvents&&!q.noEventsExplanation)throw new Error('Invalid question rules');
    if(q.responseMode && !['binary','graded'].includes(q.responseMode))throw new Error('Invalid response mode');
  }
  if(config.sections.some(s=>!config.questions.some(q=>q.section===s.id)))throw new Error('Empty section');
  for(const [a,b] of config.applicabilityPairs||[])if(!ids.includes(a)||!ids.includes(b))throw new Error('Unknown applicability question');
  return config;
}
