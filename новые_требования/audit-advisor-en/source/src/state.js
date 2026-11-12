import {validAnswer} from './scoring.js';

export function freshState() {
  return {answers: {}, index: 0, screen: 'welcome', milestones: [], seenSections: [], completedAt: null};
}

export function validateSaved(config, value) {
  if (!value || value.testId !== config.id || (value.version !== config.version && !config.compatibleVersions?.includes(value.version))) return null;
  if (!value.answers || typeof value.answers !== 'object' || Array.isArray(value.answers)) return null;
  const state = freshState();
  for (const q of config.questions) if (validAnswer(q, value.answers[q.id])) state.answers[q.id] = value.answers[q.id];
  state.index = Number.isInteger(value.index) ? Math.max(0, Math.min(value.index, config.questions.length - 1)) : 0;
  state.milestones = Array.isArray(value.milestones) ? [...new Set(value.milestones.filter(x => [25,50,75].includes(x)))] : [];
  state.seenSections = Array.isArray(value.seenSections) ? [...new Set(value.seenSections.filter(id=>config.sections.some(s=>s.id===id)))] : value.sectionSeen&&config.sections[1]?[config.sections[1].id]:[];
  const complete = Object.keys(state.answers).length === config.questions.length;
  state.screen = complete && value.screen === 'results' ? 'results' : 'question';
  const current=config.questions[state.index], next=config.questions[state.index+1];
  if (value.screen === 'transition' && next&&next.section!==current.section && config.questions.slice(0,state.index+1).every(q=>validAnswer(q,state.answers[q.id]))) state.screen='transition';
  if (typeof value.completedAt === 'string' && Number.isFinite(Date.parse(value.completedAt))) state.completedAt = value.completedAt;
  if (!complete) state.completedAt = null;
  // Never restore a position beyond an unanswered earlier question.
  const firstMissing = config.questions.findIndex(q => !validAnswer(q, state.answers[q.id]));
  if (firstMissing >= 0) {
    state.index = value.version!==config.version ? firstMissing : Math.min(state.index, firstMissing);
    if (state.index!==value.index) state.screen='question';
  }
  return state;
}

export function createStorage(config, getStorage) {
  let available = true;
  const key = 'audit-advisor:' + config.id;
  function fail() { available = false; }
  return {
    get available() { return available; }, key,
    load() {
      try {
        const raw = getStorage().getItem(key);
        if (!raw) return {state: null, reason: null};
        const data = JSON.parse(raw), state = validateSaved(config, data);
        return {state, reason: state ? (data.version!==config.version?'migrated':null) : 'version'};
      } catch (e) {
        if (e instanceof SyntaxError) return {state: null, reason: 'damaged'};
        fail(); return {state: null, reason: 'unavailable'};
      }
    },
    save(state) {
      try {
        getStorage().setItem(key, JSON.stringify({testId: config.id, version: config.version,
          answers: state.answers, index: state.index, screen: state.screen,
          milestones: state.milestones, seenSections: state.seenSections,
          completedAt: state.completedAt, savedAt: new Date().toISOString()}));
        available = true; return true;
      } catch { fail(); return false; }
    },
    clear() { try {getStorage().removeItem(key); return true;} catch {fail(); return false;} }
  };
}
