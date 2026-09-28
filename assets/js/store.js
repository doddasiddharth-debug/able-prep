/* All persistent state, one localStorage key. With an account (auth.js),
   the same object is mirrored to the server after every save.
   Shape:
     history   every graded answer: { qid, section, domain, skill, difficulty,
               correct, seconds, mode, ts }
     attempts  every finished session: { id, mode, section, label, ts, n,
               correct, seconds, stars }
     settings  { name, testDate, target, daysPerWeek, sessionMinutes }
     plan      { createdAt, weeks: [{ start, sessions: [...] }] } | null
     vocab     { word: { seen, right } }
     college   the College tools: { myScore, colleges: [...], scholarships: [...],
               removed: { id: ts }, checklist: { id: { done, ts } },
               aid: [3 offers], essay: { text, limit, updated } }. List items
               carry `updated` so a merge keeps the newer copy, and deletions
               leave a tombstone in `removed` so they don't come back.        */
window.Store = (() => {
  "use strict";
  const KEY = "ablePrep.v2";
  const LEGACY = "ablePrep.history.v1";
  const blankCollege = () => ({ myScore: "", colleges: [], scholarships: [], removed: {}, checklist: {}, aid: [{}, {}, {}], essay: { text: "", limit: 650, updated: 0 } });
  const blank = () => ({ history: [], attempts: [], settings: { name: "", testDate: "", target: 1300, daysPerWeek: 4, sessionMinutes: 30 }, plan: null, vocab: {}, college: blankCollege() });

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
    state.college = { ...blankCollege(), ...(state.college || {}) };
    return state;
  };
  const listeners = [];
  const subscribe = (fn) => { listeners.push(fn); };
  const save = () => {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode: session-only */ }
    listeners.forEach((fn) => fn(state));
  };
  const reset = () => { state = blank(); save(); };
  // Swap in a state built elsewhere (the merge after sign-in).
  const replace = (next) => { state = { ...blank(), ...next }; state.settings = { ...blank().settings, ...(next.settings || {}) }; state.college = { ...blankCollege(), ...(next.college || {}) }; save(); };

  // Union of two states, for a device that has practised offline and an
  // account that has practised elsewhere. Answers and sessions are keyed so
  // nothing doubles; for the rest, the more advanced copy wins.
  const merge = (a, b) => {
    const out = blank();
    const hk = (h) => `${h.qid}|${h.ts}`;
    const seenH = new Set();
    [...(a.history || []), ...(b.history || [])].forEach((h) => { const k = hk(h); if (!seenH.has(k)) { seenH.add(k); out.history.push(h); } });
    out.history.sort((x, y) => x.ts - y.ts);
    const seenA = new Set();
    [...(a.attempts || []), ...(b.attempts || [])].forEach((x) => { const k = x.id || `${x.mode}|${x.ts}`; if (!seenA.has(k)) { seenA.add(k); out.attempts.push(x); } });
    out.attempts.sort((x, y) => x.ts - y.ts);
    const d = blank().settings, sa = a.settings || {}, sb = b.settings || {};
    Object.keys(d).forEach((k) => { out.settings[k] = sa[k] !== undefined && sa[k] !== d[k] && sa[k] !== "" ? sa[k] : (sb[k] !== undefined ? sb[k] : d[k]); });
    const pa = a.plan, pb = b.plan;
    out.plan = pa && pb ? (pa.createdAt >= pb.createdAt ? pa : pb) : (pa || pb || null);
    const words = new Set([...Object.keys(a.vocab || {}), ...Object.keys(b.vocab || {})]);
    words.forEach((w) => { const x = (a.vocab || {})[w] || { seen: 0, right: 0 }, y = (b.vocab || {})[w] || { seen: 0, right: 0 }; out.vocab[w] = { seen: Math.max(x.seen, y.seen), right: Math.max(x.right, y.right) }; });
    out.college = mergeCollege({ ...blankCollege(), ...(a.college || {}) }, { ...blankCollege(), ...(b.college || {}) });
    return out;
  };

  const mergeCollege = (a, b) => {
    const out = blankCollege();
    out.myScore = a.myScore || b.myScore || "";
    out.removed = { ...b.removed, ...a.removed };
    const newer = (x, y) => (!x ? y : !y ? x : ((y.updated || 0) > (x.updated || 0) ? y : x));
    ["colleges", "scholarships"].forEach((k) => {
      const m = {};
      [...a[k], ...b[k]].forEach((r) => { m[r.id] = newer(m[r.id], r); });
      out[k] = Object.values(m).filter((r) => !(out.removed[r.id] >= (r.updated || 0)));
    });
    new Set([...Object.keys(a.checklist), ...Object.keys(b.checklist)]).forEach((id) => { out.checklist[id] = newer(a.checklist[id] && { ...a.checklist[id], updated: a.checklist[id].ts }, b.checklist[id] && { ...b.checklist[id], updated: b.checklist[id].ts }); });
    out.aid = [0, 1, 2].map((i) => newer(a.aid[i] || {}, b.aid[i] || {}) || {});
    out.essay = newer(a.essay, b.essay);
    return out;
  };
  const college = () => load().college;
  const setCollege = (patch) => { Object.assign(college(), patch); save(); };
  const upsert = (kind, rec) => { const list = college()[kind]; const i = list.findIndex((r) => r.id === rec.id); if (i >= 0) list[i] = rec; else list.push(rec); save(); };
  const remove = (kind, id) => { const c = college(); c[kind] = c[kind].filter((r) => r.id !== id); c.removed[id] = Date.now(); save(); };
  const setCheck = (id, done) => { college().checklist[id] = { done, ts: Date.now() }; save(); };
  const setAid = (i, k, v) => { const o = college().aid[i] || (college().aid[i] = {}); o[k] = v; o.updated = Date.now(); save(); };

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

  return { load, save, reset, replace, merge, subscribe, college, setCollege, upsert, remove, setCheck, setAid, addHistory, addAttempt, setSettings, setPlan, markSession, vocabResult, latestByQuestion, accuracy, activityByDay, streak, dayKey };
})();
