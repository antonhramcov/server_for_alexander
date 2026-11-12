import {escapeHTML} from './export.js';
import {formatText} from './content.js';

export function stagesHTML(config,copy) {
  const e=escapeHTML;
  return `<h3>${copy?(config.sections.length===2?copy.stages.two:copy.stages.many):(config.sections.length===2?'Два этапа самопроверки':'Этапы самопроверки')}</h3><ol class="aa-stage-list">${config.sections.map(section=>`<li><strong>${e(section.summaryTitle||section.title)}</strong><p>${section.description?e(section.description)+' ':''}${config.questions?formatText(copy?.stages.questionCount||'Вопросов: {count}.',{count:config.questions.filter(q=>q.section===section.id).length}):''}</p></li>`).join('')}</ol>`;
}
