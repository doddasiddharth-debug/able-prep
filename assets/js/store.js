/* All persistent state, one localStorage key. Nothing leaves the browser.
   Shape:
     history   every graded answer: { qid, section, domain, skill, difficulty,
               correct, seconds, mode, ts }
     attempts  every finished session: { id, mode, section, label, ts, n,
               correct, seconds, stars }
     settings  { name, testDate, target, daysPerWeek, sessionMinutes }
     plan      { createdAt, weeks: [{ start, sessions: [...] }] } | null
     vocab     { word: { seen, right } }                                      */
window.Store = (() => {
  "use strict";
  const KEY = "ablePrep.v2";
  const LEGACY = "ablePrep.history.v1";
  const blank = () => ({ history: [], attempts: [], settings: { name: "", testDate: "", target: 1300, daysPerWeek: 4, sessionMinutes: 30 }, plan: null, vocab: {} });

  let state = null;
  const load = () => {
    if (state) return state;
    try { state = JSON.parse(localStorage.getItem(KEY)); } catch (e) { state = null; }
    if (!state) {
      state = blank();
      // Carry over the prototype's history so nobody loses a streak.
      try { const old = JSON.parse(localStorage.getItem(LEGACY)); if (Array.isArray(old)) state.history = old.map((h) => ({ ...h, mode: h.mode || "bank", seconds: h.seconds || 0 })); } catch (e) { /* none */ }
    }
    state.settings = { ...blank().settings, ...(state.settings || {}) };
    return state;
  };
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode: session-only */ } };
  const reset = () => { state = blank(); save(); };

  const addHistory = (entries) => { load().history.push(...entries); save(); };
  const addAttempt = (a) => { load().attempts.push({ id: "a" + Date.now().toString(36), ...a }); save(); };
  const setSettings = (patch) => { Object.assign(load().settings, patch); save(); };
  const setPlan = (plan) => { load().plan = plan; save(); };
  const markSession = (id, done) => {
    const p = load().plan; if (!p) return;
    p.weeks.forEach((w) => w.sessions.forEach((s) => { if (s.id === id) s.done = done; }));
    save();
  };
  const vocabResult = (word, right) => {
    const v = load().vocab; const e = v[word] || (v[word] = { seen: 0, right: 0 });
    e.seen++; if (right) e.right++; save();
  };

  // ---- derived views of the history, used by several pages -------------
  const latestByQuestion = () => {
    const m = {};
    load().history.forEach((h) => { m[h.qid] = h; });
    return m;
  };
  const accuracy = (filterFn) => {
    const rows = load().history.filter(filterFn || (() => true));
    const ok = rows.filter((h) => h.correct).length;
    return { n: rows.length, ok, pct: rows.length ? Math.round(100 * ok / rows.length) : null };
  };
  const dayKey = (ts) => { const d = new Date(ts); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const activityByDay = () => {
    const m = {};
    load().history.forEach((h) => { const k = dayKey(h.ts); m[k] = (m[k] || 0) + 1; });
    return m;
  };
  const streak = () => {
    const days = activityByDay();
    let n = 0; const d = new Date();
    // Today counts if there is activity; otherwise the streak is measured
    // up to yesterday so it does not read as broken at 9 a.m.
    if (!days[dayKey(d)]) d.setDate(d.getDate() - 1);
    while (days[dayKey(d)]) { n++; d.setDate(d.getDate() - 1); }
    return n;
  };

  return { load, save, reset, addHistory, addAttempt, setSettings, setPlan, markSession, vocabResult, latestByQuestion, accuracy, activityByDay, streak, dayKey };
})();
