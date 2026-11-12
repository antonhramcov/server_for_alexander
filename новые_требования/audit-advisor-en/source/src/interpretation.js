import {answerStatus} from './scoring.js';
import {formatText} from './content.js';
import {guidanceText} from './guidance.js';


export function interpret(config, answers, score) {
  const level = score.readiness === null ? {title:config.copy.assessment.noDataHeading,text:config.copy.assessment.noDataDescription} : [...config.copy.assessment.levels].reverse().find(l => score.readiness >= l.min);
  const gaps = config.questions.filter(q => ['no','partial','unsure'].includes(answers[q.id]));
  const groups = new Map();
  for (const q of gaps) {
    if (!groups.has(q.category)) groups.set(q.category, {title:q.category, priority:q.priority, critical:false, items:[]});
    const group=groups.get(q.category);
    group.priority=Math.min(group.priority,q.priority); group.critical ||= q.critical;
    group.items.push({id:q.id, title:q.planTitle||q.topic, clause:q.clause, condition:q.condition,
      answer:answers[q.id], status:answerStatus(q,answers[q.id]),
      action:answers[q.id]==='unsure'?q.recommendationUnsure:answers[q.id]==='no'?q.recommendationNo:q.recommendationPartial, outcome:q.outcome,outcomeLabel:q.outcomeLabel||config.copy.plan.confirmationHeading});
  }
  const plan=[...groups.values()].sort((a,b)=>Number(b.critical)-Number(a.critical)||a.priority-b.priority);
  const applicabilityConflicts=(config.applicabilityPairs||[]).filter(([a,b])=>(answers[a]==='na')!==(answers[b]==='na'));
  return {level, plan, applicabilityConflicts, gapCount:gaps.length, strengths:score.strengths.slice(0,6),
    attention:plan.slice(0,4).map(g=>g.title),
    closing:score.readiness!==null&&score.readiness>=80?config.copy.assessment.closingHigh:config.copy.assessment.closingOther};
}

export function reportText(config, score, interpretation, date) {
  const c=config.copy,r=c.results,x=c.export;
  const lines=['Audit Advisor · '+config.title,config.standard.label,x.date+': '+date,
    x.readiness+': '+(score.readiness===null?x.notCalculated:score.readiness+'%'),
    ...score.sections.map(s=>s.title+': '+(s.score===null?x.notCalculated:Math.round(s.score)+'%')),
    '',interpretation.level.title,interpretation.level.text,'',r.strengthsHeading+':',
    interpretation.strengths.length?interpretation.strengths.map(q=>q.strength).join('; '):x.noStrengths,
    '',r.gapsHeading+':',interpretation.gapCount?formatText(x.gapCount,{count:interpretation.gapCount}):x.noGaps,
    ...(score.criticalGaps.length?[r.firstHeading,...score.criticalGaps.map(q=>q.id+' — '+(q.planTitle||q.topic))]:[]),
    '',r.planHeading+':'];
  if(!interpretation.plan.length)lines.push(x.noPlan);
  interpretation.plan.forEach((group,i)=>{
    lines.push('',(i+1)+'. '+group.title);
    group.items.forEach(item=>lines.push(item.id+' · '+item.title+' · '+item.status+' · '+config.standard.label+', '+c.metadata.clause+' '+item.clause,item.action,...(item.condition?[x.condition+': '+item.condition]:[]),item.outcomeLabel+': '+item.outcome));
  });
  if(interpretation.applicabilityConflicts.length)lines.push('',r.applicabilityHeading+':',...interpretation.applicabilityConflicts.map(([first,second,title])=>formatText(x.conflict,{first,second,title})));
  if(score.excluded.length)lines.push('',r.excludedHeading+':',...score.excluded.map(q=>q.id+' — '+(q.planTitle||q.topic)+'. '+q.exclusionStatus+'. '+x.condition+': '+q.exclusionReason));
  lines.push('',config.disclaimer,config.standard.note,x.version+': '+config.version,...guidanceText(config));
  return lines.join('\n');
}
export function methodText(config) {
  return formatText(config.copy.assessment.method,{
    weights:[...new Set(config.questions.map(q=>q.weight))].sort((a,b)=>a-b).join(', '),
    shares:config.sections.map(s=>s.title+' — '+Math.round(s.share*100)+'%').join('; ')
  });
}
