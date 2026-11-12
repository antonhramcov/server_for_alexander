import {scoreAssessment, answeredCount, validAnswer, answerStatus} from './scoring.js';
import {freshState, createStorage} from './state.js';
import {interpret, reportText} from './interpretation.js';
import {escapeHTML, buildPrintHTML, printReport, copyReport} from './export.js';
import {selectableStandard} from './validation.js';
import {stagesHTML} from './stages.js';
import {formatText} from './content.js';
import {guidanceHTML} from './guidance.js';

export function mountAssessment(root, catalog, copy) {
  const t=(key,values)=>formatText(key.split('.').reduce((value,part)=>value[part],copy),values);
  const e=escapeHTML, runtime=root.querySelector('#aa-runtime'), startArea=root.querySelector('#aa-start-area');
  const selector=root.querySelector('#aa-standard');
  const initialTitle=root.querySelector('#aa-tool-title').textContent, initialIntro=root.querySelector('.aa-lead').textContent;
  const stages=root.querySelector('#aa-stages'), initialStages=stages.innerHTML;
  let config=null, storage=null, pending=null, state=freshState(), renderedReport=null, milestoneMessage='';
  selector.value='';
  const announcer=root.querySelector('#aa-announcer');
  const milestoneTexts=copy.milestones;
  let selectionRequest=0;

  async function chooseStandard(id) {
    const request=++selectionRequest;
    config=null;delete root.dataset.standardId;pending=null;renderedReport=null;
    startArea.innerHTML=`<button type="button" class="aa-button aa-primary" data-action="start" disabled>${e(t('navigation.start'))} →</button>`;
    const entry=catalog.find(s=>s.id===id&&s.status==='ready');
    if(!entry)return;
    try {
      let chosen;
      if(entry.load){root.querySelector('#aa-selection-info').textContent=t('loading.standard');chosen=await entry.load();}
      else chosen=selectableStandard(catalog,id);
      if(request!==selectionRequest)return;
      config=chosen;
      if(!config)return;
    } catch(error) {
      if(request!==selectionRequest)return;
      config=null;
      root.querySelector('#aa-selection-info').textContent=t('loading.standardError');
      startArea.innerHTML=`<button type="button" class="aa-button" data-action="retry-standard">${e(t('loading.retry'))}</button>`;
      return;
    }
    storage=createStorage(config,()=>window.localStorage);
    const loaded=storage.load();pending=loaded.state;
    root.querySelector('#aa-tool-title').textContent=config.title;
    root.querySelector('.aa-lead').textContent=config.intro;
    const guidance=root.querySelector('#aa-guidance');if(guidance)guidance.innerHTML=guidanceHTML(config);
    stages.innerHTML=stagesHTML(config,copy);
    root.querySelector('#aa-selection-info').textContent=t('selection.summary',{standard:config.standard.label,count:config.questions.length,duration:config.duration});
    startArea.querySelector('[data-action="start"]').disabled=false;
    if(pending){
      const count=answeredCount(config,pending.answers);
      startArea.innerHTML=`<div class="aa-resume"><p>${e(pending.screen==='results'?t('storage.resumeComplete'):t('storage.resumePartial',{count,total:config.questions.length}))}</p><div class="aa-actions"><button type="button" class="aa-button aa-primary" data-action="resume">${e(t(pending.screen==='results'?'storage.openResults':'storage.resume'))} →</button><button type="button" class="aa-linkbutton" data-action="reset">${e(t('navigation.reset'))}</button></div></div>`;
    }
    storageStatus(loaded.reason?copy.storage[loaded.reason]:null);
    root.dataset.standardId=config.id;
  }
  function storageStatus(message) {
    root.querySelector('#aa-storage-status').textContent=message || (storage.available?'':t('storage.unavailable'));
  }

  function save() {storage.save(state);storageStatus();}
  function focusTitle() {
    const title=runtime.querySelector('[data-screen-title]');
    if(title) {title.focus({preventScroll:true}); const rect=runtime.getBoundingClientRect();if(rect.top<0||rect.top>100) runtime.scrollIntoView({behavior:'auto',block:'start'});}
  }
  function render(focus=true) {
    root.dataset.view=state.screen;
    if(state.screen==='question') renderQuestion();
    if(state.screen==='transition') renderTransition();
    if(state.screen==='results') renderResults();
    if(focus) focusTitle();
  }
  function dateLabel() {
    return new Intl.DateTimeFormat(config.locale||copy.locale,{day:'numeric',month:'long',year:'numeric',...(config.timeZone?{timeZone:config.timeZone}:{})}).format(new Date(state.completedAt || new Date().toISOString()));
  }
  function questionSection(q) {return config.sections.find(s=>s.id===q.section);}
  function renderQuestion() {
    const q=config.questions[state.index], section=questionSection(q), num=config.sections.indexOf(section)+1;
    const count=answeredCount(config,state.answers), progress=Math.round(count/config.questions.length*100);
    const answer=state.answers[q.id], choices=q.answerOptions||copy.answerPresets[q.responseMode==='binary'?'documents':'practice'].filter(o=>(o.value!=='na'||q.allowNA)&&(o.value!=='no_events'||q.allowNoEvents));
    runtime.innerHTML=`<div class="aa-question-wrap">
      <section class="aa-status-panel" aria-label="${e(t('question.metadataLabel'))}">
        <div class="aa-status-top"><span>${e(config.standard.label)}</span><span>${e(t('question.section',{current:num,total:config.sections.length}))}</span></div>
        <div class="aa-progress-header"><span>${e(section.title)}</span><span id="aa-progress-label">${e(t('question.progress',{percent:progress}))}</span></div>
        <div class="aa-bar" id="aa-progress" role="progressbar" aria-label="${e(t('question.progressLabel'))}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><div class="aa-bar-fill" style="width:${progress}%"></div></div>
        <div class="aa-progress-detail"><span>${e(t('question.position',{current:state.index+1,total:config.questions.length}))}</span><span id="aa-remaining">${e(t('question.remaining',{count:config.questions.length-count}))}</span></div>
        <div class="aa-question-meta"><span>${e(q.topic)}</span><span>${e(q.id)}</span></div>
      </section>
      <button type="button" class="aa-button aa-return" data-action="finish" ${count===config.questions.length?'':'hidden'}>${e(t('navigation.returnToResults'))} →</button>
      <article class="aa-question-card" data-question-id="${e(q.id)}" data-content-file="${e(config.contentFile||'')}" data-content-pointer="${e(q.contentPointer||'')}" aria-labelledby="aa-question-title">
        <h2 id="aa-question-title" data-content-field="heading" data-screen-title tabindex="-1">${e(q.text)}</h2>
        <div class="aa-question-description" id="aa-question-explanation">${(q.description||[q.explanation]).map((paragraph,i)=>`<p class="aa-explanation" data-content-field="description.${i}">${e(paragraph)}</p>`).join('')}
          <section class="aa-evidence" aria-labelledby="aa-evidence-title"><h3 class="aa-evidence-title" id="aa-evidence-title" data-copy-key="question.examplesHeading">${e(t('question.examplesHeading'))}</h3><ul>${q.evidence.map((x,i)=>`<li data-content-field="examples.${i}">${e(x)}</li>`).join('')}</ul></section>
        </div>
        <fieldset class="aa-options" aria-labelledby="aa-question-title" aria-describedby="aa-question-explanation"><legend class="aa-sr">${e(t('question.chooseOne'))}</legend>
          ${choices.map(option=>`<label class="aa-option ${answer===option.value?'aa-selected':''}" for="aa-answer-${e(option.value)}"><input type="radio" id="aa-answer-${e(option.value)}" name="aa-answer" value="${e(option.value)}" ${answer===option.value?'checked':''} aria-labelledby="aa-answer-${e(option.value)}-label" aria-describedby="aa-answer-${e(option.value)}-description${option.value==='na'?' aa-na-note':option.value==='no_events'?' aa-events-note':''}"><span class="aa-answer-copy"><span class="aa-answer-label" id="aa-answer-${e(option.value)}-label" data-answer-value="${e(option.value)}" data-copy-source="${e(option.labelSource||'')}" data-content-field="answers.overrides.${e(option.value)}.label">${e(option.label)}</span><small class="aa-answer-description" id="aa-answer-${e(option.value)}-description" data-copy-source="${e(option.descriptionSource||'')}" data-content-field="answers.overrides.${e(option.value)}.description">${e(option.description)}</small></span></label>`).join('')}
        </fieldset>
        ${q.allowNA?`<p class="aa-na-note" id="aa-na-note"><strong>${e(t('question.notApplicableHeading'))}</strong> ${e(q.naExplanation)}</p>`:''}
        ${q.allowNoEvents?`<p class="aa-na-note" id="aa-events-note"><strong>${e(t('question.noEventsHeading'))}</strong> ${e(q.noEventsExplanation)}</p>`:''}
        ${q.condition&&!q.allowNA&&!q.allowNoEvents?`<p class="aa-na-note"><strong>${e(t('question.conditionHeading'))}</strong> ${e(q.condition)}</p>`:''}
        <p class="aa-feedback" id="aa-feedback" role="status" aria-live="polite" aria-atomic="true">${e(answer?q.feedback[answer]:t('question.unanswered'))}</p>
        <nav class="aa-nav" aria-label="${e(t('question.navigationLabel'))}"><button type="button" class="aa-button" data-action="back" ${state.index===0?'disabled':''}><span aria-hidden="true">←</span> ${e(t('navigation.back'))}</button><button type="button" class="aa-button aa-primary" data-action="next" ${validAnswer(q,answer)?'':'disabled'}>${e(t(state.index===config.questions.length-1?'navigation.finish':'navigation.next'))} <span aria-hidden="true">→</span></button></nav>
      </article><p class="aa-milestone" id="aa-milestone" role="status" aria-live="polite">${e(milestoneMessage)}</p><p class="aa-quiz-note">${e(t('question.progressHint'))}</p>
      <div class="aa-actions"><button type="button" class="aa-linkbutton" data-action="reset">${e(t('navigation.reset'))}</button></div>
    </div>`;
    announcer.textContent=t('question.announcement',{current:state.index+1,total:config.questions.length,section:num});
    milestoneMessage='';
  }
  function answerQuestion(value) {
    const q=config.questions[state.index];
    if(!validAnswer(q,value)) return;
    state.answers[q.id]=value; state.completedAt=null;
    const count=answeredCount(config,state.answers), progress=Math.round(count/config.questions.length*100);
    runtime.querySelectorAll('.aa-option').forEach(el=>el.classList.toggle('aa-selected',el.querySelector('input').value===value));
    runtime.querySelector('#aa-feedback').textContent=q.feedback[value];
    runtime.querySelector('[data-action="next"]').disabled=false;
    runtime.querySelector('#aa-progress').setAttribute('aria-valuenow',String(progress));
    runtime.querySelector('#aa-progress .aa-bar-fill').style.width=progress+'%';
    runtime.querySelector('#aa-progress-label').textContent=t('question.progress',{percent:progress});
    runtime.querySelector('#aa-remaining').textContent=t('question.remaining',{count:config.questions.length-count});
    runtime.querySelector('[data-action="finish"]').hidden=count!==config.questions.length;
    for(const point of [25,50,75]) if(progress>=point&&!state.milestones.includes(point)) {
      state.milestones.push(point); milestoneMessage=milestoneTexts[point];
      runtime.querySelector('#aa-milestone').textContent=milestoneMessage;
    }
    save();
  }
  function renderTransition() {
    const current=questionSection(config.questions[state.index]),next=questionSection(config.questions[state.index+1]);
    const count=answeredCount(config,state.answers);
    runtime.innerHTML=`<section class="aa-transition"><span class="aa-tag">${e(t('transition.count',{count,total:config.questions.length}))}</span><h2 data-screen-title tabindex="-1">${e(t('transition.heading',{section:current.title}))}</h2><p>${e(next.intro||t('transition.description',{section:next.title}))}</p><div class="aa-actions"><button type="button" class="aa-button aa-primary" data-action="continue-section">${e(t('navigation.continueSection'))} →</button><button type="button" class="aa-linkbutton" data-action="transition-back">${e(t('navigation.transitionBack'))}</button></div></section>`;
    announcer.textContent=t('transition.announcement',{section:next.title});
  }
  function renderResults() {
    const score=scoreAssessment(config,state.answers);
    if(!score.complete) {state.index=config.questions.findIndex(q=>!validAnswer(q,state.answers[q.id]));state.screen='question';render();return;}
    const content=interpret(config,state.answers,score), date=dateLabel(), conflicts=content.applicabilityConflicts;
    renderedReport={score,content,date};
    const circle=2*Math.PI*64;
    runtime.innerHTML=`<article class="aa-results">
      <header class="aa-report-header"><div><p class="aa-eyebrow">${e(t('results.reportHeading'))}</p><p class="aa-small">${e(config.standard.label)} · ${e(date)} · ${e(t('results.completed'))}</p></div><button type="button" class="aa-linkbutton" data-action="review">${e(t('navigation.review'))}</button></header>
      <section class="aa-overview"><div class="aa-dial" role="img" aria-label="${e(copy.export.readiness)}: ${score.readiness===null?e(t('results.notCalculated')):score.readiness+'%'}"><svg viewBox="0 0 150 150" aria-hidden="true"><circle class="aa-dial-bg" cx="75" cy="75" r="64"/><circle class="aa-dial-value" cx="75" cy="75" r="64" stroke-dasharray="${circle}" stroke-dashoffset="${circle*(1-(score.readiness||0)/100)}"/></svg><div class="aa-dial-label"><strong id="aa-result-score">${score.readiness===null?'—':score.readiness+'%'}</strong></div></div><div><p class="aa-eyebrow">${e(t('results.readinessHeading'))}</p><h2 data-screen-title tabindex="-1">${e(content.level.title)}</h2><p>${e(content.level.text)}</p></div></section>
      <div class="aa-section-scores">${score.sections.map(s=>`<section><div class="aa-score-heading"><span>${e(s.title)}</span><strong>${s.score===null?'—':Math.round(s.score)+'%'}</strong></div><div class="aa-bar" role="meter" aria-label="${e(s.title)}" aria-valuemin="0" aria-valuemax="100" ${s.score===null?'':`aria-valuenow="${Math.round(s.score)}"`}><div class="aa-bar-fill" style="width:${s.score||0}%"></div></div></section>`).join('')}</div>
      ${content.gapCount?`<aside class="aa-notice" id="aa-critical"><h3>${e(t('results.gapsHeading'))}</h3><p>${e(t('results.gapsDescription',{count:content.gapCount,total:config.questions.length}))}</p>${score.criticalGaps.length?`<p><strong>${e(t('results.firstHeading'))}</strong></p><ul>${score.criticalGaps.map(q=>`<li>${e(q.id)}. ${e(q.planTitle||q.topic)} — ${e(answerStatus(q,state.answers[q.id]))}.</li>`).join('')}</ul>`:''}</aside>`:''}
      ${conflicts.length?`<aside class="aa-notice" id="aa-conflicts"><h3>${e(t('results.applicabilityHeading'))}</h3><p>${e(t('results.applicabilityDescription'))}</p>${conflicts.map(([a,b,title])=>`<p>${e(title)}: ${a} / ${b}. <button class="aa-linkbutton" data-action="edit-question" data-id="${a}">${e(t('navigation.editAnswer'))} ${a}</button> · <button class="aa-linkbutton" data-action="edit-question" data-id="${b}">${e(t('navigation.editAnswer'))} ${b}</button></p>`).join('')}</aside>`:''}
      <div class="aa-insights"><section class="aa-insight"><h3>${e(t('results.strengthsHeading'))}</h3>${content.strengths.length?`<p>${e(t('results.strengthsIntro'))}</p><ul>${content.strengths.map(q=>`<li>${e(q.strength)}</li>`).join('')}</ul>${score.strengths.length>6?`<p class="aa-small">${e(t('results.moreStrengths',{count:score.strengths.length-6}))}</p>`:''}`:`<p>${e(t('results.noStrengths'))}</p>`}</section><section class="aa-insight"><h3>${e(t('results.attentionHeading'))}</h3>${content.attention.length?`<p>${e(t('results.attentionIntro'))}</p><ul>${content.attention.map(t=>`<li>${e(t)}</li>`).join('')}</ul>`:`<p>${e(t('results.noGaps'))}</p>`}</section></div>
      <div class="aa-section-title"><h2>${e(t('results.planHeading'))}</h2><span class="aa-small">${e(t('results.planCount',{count:content.gapCount}))}</span></div>
      <p class="aa-small">${e(t('results.planDescription'))}</p>
      <div id="aa-plan">${content.plan.map((group,i)=>`<details class="aa-plan-group" open><summary>${i+1}. ${e(group.title)}</summary>${group.items.map(item=>`<section class="aa-plan-item" data-plan-id="${e(item.id)}"><h3>${e(item.title)}</h3><div class="aa-item-meta">${e(item.status)} · ${e(item.id)} · ${e(config.standard.label)}, ${e(copy.metadata.clause)} ${e(item.clause)}</div><p>${e(item.action)}</p>${item.condition?`<p class="aa-small">${e(item.condition)}</p>`:''}<p class="aa-outcome"><strong>${e(item.outcomeLabel)}:</strong> ${e(item.outcome)}</p><button type="button" class="aa-linkbutton" data-action="edit-question" data-id="${e(item.id)}">${e(t('navigation.editAnswer'))}</button></section>`).join('')}</details>`).join('')||`<div class="aa-insight"><h3>${e(t('results.allYesHeading'))}</h3><p>${e(t('results.allYesDescription'))}</p></div>`}</div>
      ${score.excluded.length?`<details class="aa-omitted"><summary>${e(t('results.excludedHeading'))}: ${score.excluded.length}</summary><p>${e(t('results.exclusionsDescription'))}</p><ul>${score.excluded.map(q=>`<li><strong>${e(q.id)}. ${e(q.planTitle||q.topic)}</strong> ${e(q.exclusionStatus)}. ${e(q.exclusionReason)}</li>`).join('')}</ul></details>`:''}
      <p class="aa-closing">${e(content.closing)}</p>
      <div class="aa-report-actions"><button type="button" class="aa-button aa-primary" data-action="print">${e(t('results.save'))} <span aria-hidden="true">↓</span></button><button type="button" class="aa-button" data-action="copy">${e(t('results.copy'))}</button><button type="button" class="aa-button" data-action="reset">${e(t('navigation.repeat'))}</button></div>
      <p class="aa-small">${e(t('results.printHint'))}</p>
      <p class="aa-report-status" id="aa-report-status" role="status" aria-live="polite"></p><textarea class="aa-copy-area" id="aa-copy-fallback" aria-label="${e(copy.accessibility.copyFallback)}" readonly hidden></textarea>
      <p class="aa-disclaimer">${e(config.disclaimer)}</p><details class="aa-method"><summary>${e(t('results.limitationsHeading'))}</summary><p class="aa-small">${e(config.standard.note)} ${e(copy.export.version)}: ${e(config.version)}.</p></details>
      <section class="aa-cta"><div><h2>${e(t('results.serviceHeading',{standard:config.standard.label}))}</h2><p>${e(t('results.serviceDescription'))}</p></div><a class="aa-button aa-primary" href="${e(config.links.service)}">${e(t('results.serviceButton'))}</a></section>
      ${config.links.chat?`<section class="aa-chat"><div><h2>${e(t('results.chatHeading',{standard:config.standard.label}))}</h2><p>${e(t('results.chatDescription'))}</p></div><a class="aa-button" href="${e(config.links.chat)}" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">${e(t('results.chatButton'))}</a></section>`:''}${guidanceHTML(config)}
    </article>`;
    announcer.textContent=t('results.announcement',{result:score.readiness===null?t('results.notCalculated'):score.readiness+'%'});
  }
  function start() {if(!config)return;state=freshState();pending=null;state.screen='question';save();render();}
  function reset() {
    if(!window.confirm(t('storage.resetPrompt'))) return;
    const cleared=storage.clear();selectionRequest++;
    state=freshState();config=null;storage=null;pending=null;renderedReport=null;milestoneMessage='';
    root.dataset.view='welcome';delete root.dataset.standardId;runtime.innerHTML='';selector.value='';
    root.querySelector('#aa-tool-title').textContent=initialTitle;const guidance=root.querySelector('#aa-guidance');if(guidance)guidance.innerHTML='';
    root.querySelector('.aa-lead').textContent=initialIntro;
    stages.innerHTML=initialStages;
    root.querySelector('#aa-selection-info').textContent=t('welcome.selectionHint');
    startArea.innerHTML=`<button type="button" class="aa-button aa-primary" data-action="start" disabled>${e(t('navigation.start'))} →</button>`;
    root.querySelector('#aa-storage-status').textContent=cleared?'':t('storage.resetFailure');
    announcer.textContent=t('storage.resetAnnouncement');
    selector.focus({preventScroll:true});root.scrollIntoView({behavior:'auto',block:'start'});
  }
  function next() {
    const q=config.questions[state.index]; if(!validAnswer(q,state.answers[q.id])) return;
    milestoneMessage='';
    if(state.index===config.questions.length-1) {
      const firstMissing=config.questions.findIndex(x=>!validAnswer(x,state.answers[x.id]));
      if(firstMissing>=0) state.index=firstMissing;
      else {state.screen='results';state.completedAt ||= new Date().toISOString();}
    } else if(config.questions[state.index+1].section!==q.section&&!state.seenSections.includes(config.questions[state.index+1].section)) {state.screen='transition';}
    else state.index++;
    save();render();
  }
  function editQuestion(id) {
    const index=config.questions.findIndex(q=>q.id===id);if(index<0)return;
    state.index=index;state.screen='question';save();render();
  }
  root.addEventListener('change',event=>{
    if(event.target===selector&&state.screen==='welcome')chooseStandard(selector.value);
    if(event.target.matches('input[name="aa-answer"]')&&state.screen==='question')answerQuestion(event.target.value);
  });
  root.addEventListener('click',event=>{
    const button=event.target.closest('[data-action]'); if(!button||!root.contains(button)||button.disabled)return;
    const action=button.dataset.action;
    if(action==='retry-standard'){chooseStandard(selector.value);return;}
    if(!config)return;
    if(action==='start')start();
    if(action==='resume'&&pending){state=pending;pending=null;render();storageStatus();}
    if(action==='reset')reset();
    if(action==='next'&&state.screen==='question')next();
    if(action==='finish'&&answeredCount(config,state.answers)===config.questions.length){state.screen='results';state.completedAt ||= new Date().toISOString();save();render();}
    if(action==='back'&&state.index>0){state.index--;milestoneMessage='';save();render();}
    if(action==='continue-section'){state.index++;state.seenSections.push(config.questions[state.index].section);state.screen='question';save();render();}
    if(action==='transition-back'){state.screen='question';save();render();}
    if(action==='review')editQuestion(config.questions[0].id);
    if(action==='edit-question')editQuestion(button.dataset.id);
    if(action==='print'&&renderedReport){const {score,content,date}=renderedReport;printReport(root,buildPrintHTML(config,score,content,date,root.querySelector('style').textContent),setReportStatus,copy);}
    if(action==='copy'&&renderedReport){const {score,content,date}=renderedReport;copyReport(root,reportText(config,score,content,date),setReportStatus,copy);}
  });
  function setReportStatus(message){const target=root.querySelector('#aa-report-status');if(target)target.textContent=message;}
}
