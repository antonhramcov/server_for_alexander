// Pure scoring: no DOM, storage, network or side effects.
export const ANSWER_VALUES = Object.freeze({yes: 1, partial: 0.5, no: 0});

export function validAnswer(question, answer) {
  return typeof answer==='string' && !(answer==='partial' && question.responseMode==='binary') && (Object.hasOwn(ANSWER_VALUES, answer) || answer==='unsure'&&question.allowUnsure || isExcluded(question, answer));
}

export function isExcluded(question, answer) {
  return Boolean(answer==='na'&&question.allowNA || answer==='no_events'&&question.allowNoEvents);
}

export function answerStatus(question, answer) {
  const labels=question.statusLabels;
  if(answer==='na'||answer==='no_events'||answer==='unsure')return labels[answer];
  return labels[question.responseMode==='binary'?'documents':'practice'][answer];
}

export function answeredCount(config, answers) {
  return config.questions.filter(q => validAnswer(q, answers[q.id])).length;
}

export function scoreAssessment(config, answers) {
  const count = answeredCount(config, answers);
  const sections = config.sections.map(section => {
    const questions = config.questions.filter(q => q.section === section.id);
    let earned = 0, possible = 0, excluded = 0, unverified = 0;
    for (const q of questions) {
      const answer = answers[q.id];
      if (isExcluded(q, answer)) { excluded++; continue; }
      if (answer==='unsure'&&q.allowUnsure)unverified++;
      if (!Number.isFinite(q.weight) || q.weight <= 0) throw new Error('Invalid question weight');
      possible += q.weight;
      if (validAnswer(q, answer) && Object.hasOwn(ANSWER_VALUES, answer)) earned += q.weight * ANSWER_VALUES[answer];
    }
    return {...section, earned, possible, excluded, unverified, score: possible&&!unverified ? 100 * earned / possible : null};
  });
  const complete = count === config.questions.length;
  // An empty section is never silently reweighted; the headline score is unavailable.
  const calculable = complete && sections.every(s => s.score !== null);
  const shareSum = sections.reduce((sum, s) => sum + s.share, 0);
  if (Math.abs(shareSum - 1) > 1e-9) throw new Error('Section shares must sum to 1');
  const readiness = calculable ? Math.round(sections.reduce((sum, s) => sum + s.score * s.share, 0)) : null;
  return {
    complete, count, progress: Math.round(count / config.questions.length * 100), sections, readiness,
    unverified: config.questions.filter(q=>q.allowUnsure&&answers[q.id]==='unsure'),
    criticalGaps: config.questions.filter(q => q.critical && ['no','partial','unsure'].includes(answers[q.id])),
    excluded: config.questions.filter(q => isExcluded(q, answers[q.id])).map(q=>({...q,exclusionStatus:answerStatus(q,answers[q.id]),exclusionReason:answers[q.id]==='na'?q.naExplanation:q.noEventsExplanation})),
    strengths: config.questions.filter(q => answers[q.id] === 'yes')
  };
}
