import {escapeHTML} from './export.js';

// Approved source-document guidance stays editable beside the questions.
export function guidanceHTML(config, print=false) {
  if(!config?.guidance)return '';
  const e=escapeHTML,g=config.guidance;
  const body=(g.instructions||[]).map(p=>`<p>${e(p)}</p>`).join('')+(g.sections||[]).map(s=>`<section><h3>${e(s.heading)}</h3>${s.paragraphs.map(p=>`<p>${e(p)}</p>`).join('')}${s.links?.length?`<ul>${s.links.filter(l=>/^https:\/\//.test(l.url)).map(l=>`<li><a href="${e(l.url)}" target="_blank" rel="noopener noreferrer">${e(l.label)}</a></li>`).join('')}</ul>`:''}</section>`).join('');
  return print?`<section><h2>${e(config.copy.metadata.guidanceHeading)}</h2>${body}</section>`:`<details class="aa-method aa-guidance"><summary>${e(config.copy.metadata.guidanceHeading)}</summary>${body}</details>`;
}

export function guidanceText(config) {
  if(!config?.guidance)return [];
  return ['',config.copy.metadata.guidanceHeading,...(config.guidance.instructions||[]),...config.guidance.sections.flatMap(s=>[s.heading,...s.paragraphs,...(s.links||[]).map(l=>l.label+': '+l.url)])];
}
