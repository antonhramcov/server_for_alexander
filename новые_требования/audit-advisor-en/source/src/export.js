import {methodText} from './interpretation.js';
import {formatText} from './content.js';
import {guidanceHTML} from './guidance.js';
export function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

export function buildPrintHTML(config, score, content, date, css) {
  const e=escapeHTML,copy=config.copy;
  const plan=content.plan.map((group,i)=>`<section><h2>${i+1}. ${e(group.title)}</h2>${group.items.map(item=>`<div class="aa-print-item"><h3>${e(item.id)}. ${e(item.title)}</h3><p>${e(item.status)} · ${e(config.standard.label)}, ${e(copy.metadata.clause)} ${e(item.clause)}</p><p>${e(item.action)}</p>${item.condition?`<p>${e(item.condition)}</p>`:''}<p><strong>${e(item.outcomeLabel)}:</strong> ${e(item.outcome)}</p></div>`).join('')}</section>`).join('');
  return `<!doctype html><html lang="${e(copy.locale.split('-')[0])}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Audit Advisor — ${e(config.title)}</title><style>${css}</style></head><body><section id="aa-iso-readiness"><div class="aa-print"><p>Audit Advisor · ${e(config.standard.label)}</p><h1>${e(config.title)}</h1><p>${e(copy.export.dateAssessment)}: ${e(date)} · ${e(copy.export.version)}: ${e(config.version)}</p><div class="aa-print-result">${score.readiness===null?e(copy.export.notCalculated):score.readiness+'%'} — ${e(copy.export.readiness)}</div><p>${e(content.level.title)}</p><p>${e(content.level.text)}</p>${score.sections.map(s=>`<p>${e(s.title)}: <strong>${s.score===null?e(copy.export.notCalculated):Math.round(s.score)+'%'}</strong></p>`).join('')}<h2>${e(copy.results.strengthsHeading)}</h2><p>${content.strengths.length?e(content.strengths.map(q=>q.strength).join('; ')):e(copy.export.noStrengths)}</p><h2>${e(copy.results.gapsHeading)}</h2><p>${e(content.gapCount?formatText(copy.export.gapCount,{count:content.gapCount}):copy.export.noGaps)}</p>${score.criticalGaps.length?`<h2>${e(copy.results.firstHeading)}</h2><ul>${score.criticalGaps.map(q=>`<li>${e(q.id)} — ${e(q.planTitle||q.topic)}</li>`).join('')}</ul>`:''}<h2>${e(copy.results.planHeading)}</h2>${plan||`<p>${e(copy.export.noPlan)}</p>`}${score.excluded.length?`<h2>${e(copy.results.excludedHeading)}</h2>${score.excluded.map(q=>`<p>${e(q.id)}. ${e(q.planTitle||q.topic)}. ${e(q.exclusionStatus)}. ${e(q.exclusionReason)}</p>`).join('')}`:''}${content.applicabilityConflicts.length?`<h2>${e(copy.results.applicabilityHeading)}</h2><p>${e(content.applicabilityConflicts.map(([first,second,title])=>formatText(copy.export.conflict,{first,second,title})).join("; "))}</p>`:''}<h2>${e(copy.export.boundaries)}</h2><p>${e(config.disclaimer)}</p><p>${e(config.standard.note)}</p><p>${e(methodText(config))}</p>${guidanceHTML(config,true)}</div></section></body></html>`;
}

export function printReport(root, html, status, copy) {
  // A same-origin in-memory document keeps Tilda headers/forms out of the PDF.
  // No remote URL or library is loaded. Uses the browser's native window.print().
  const previous=root.querySelector('.aa-print-frame');
  if(previous) previous.remove();
  const frame=document.createElement('iframe');
  frame.className='aa-print-frame'; frame.title=copy.export.printFrame; frame.setAttribute('aria-hidden','true');
  frame.onload=()=>{
    try { frame.contentWindow.focus(); frame.contentWindow.print(); status(copy.export.printSuccess); }
    catch { status(copy.export.printError); }
  };
  frame.srcdoc=html; root.appendChild(frame);
}

export async function copyReport(root, text, status, copy) {
  try {
    if(navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text); status(copy.export.copySuccess); return true;
    }
  } catch { /* Fall through to a visible, selectable text version. */ }
  const area=root.querySelector('#aa-copy-fallback');
  area.hidden=false; area.value=text; area.focus(); area.select();
  try {
    if(document.execCommand && document.execCommand('copy')) {status(copy.export.copySuccessFallback);return true;}
  } catch { /* Manual copying remains available. */ }
  status(copy.export.copyManual);
  return false;
}
