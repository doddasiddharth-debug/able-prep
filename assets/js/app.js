/* The app shell: sidebar, hash router, and every page except the practice
   screen (that lives in practice.js). Pages render into #page. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const SECONDS_PER_Q = { rw: (32 * 60) / 27, math: (35 * 60) / 22 };
  const MODULE_SIZE = { rw: 27, math: 22 }; // the real module lengths

  let bank = null, vocab = null;
  const secName = (s) => (s === "all" ? "Both sections" : bank.meta.sections[s].name);
  const qsIn = (f) => bank.questions.filter((q) =>
    (!f.section || f.section === "all" || q.section === f.section) &&
    (!f.domain || f.domain === "all" || q.domain === f.domain) &&
    (!f.skill || q.skill === f.skill) &&
    (!f.difficulty || f.difficulty === "all" || q.difficulty === f.difficulty) &&
    (!f.ids || f.ids.has(q.id)));
  const moduleSeconds = (section, n) => Math.round((n * SECONDS_PER_Q[section]) / 60) * 60;
  const fmtMin = (s) => `${Math.round(s / 60)} min`;
  const fmtDate = (ts) => new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  const pctBar = (label, ok, n, sub) => {
    const pct = n ? Math.round(100 * ok / n) : 0;
    return `<div class="stat"><div class="stat-label"><span>${esc(label)}</span><small>${n ? `${ok}/${n}` : (sub || "")}</small></div><div class="stat-bar"><i style="width:${pct}%"></i></div></div>`;
  };

  // ---------------------------------------------------------------- graphics
  // One stroke icon set, 24-unit grid, drawn in currentColor.
  const ICON = {
    dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    bank: '<path d="M4 19.5V5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0 0 4h13"/><path d="M8 7h7M8 11h5"/>',
    tests: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v2h6V3M8.5 12l2.5 2.5 4.5-5"/>',
    rush: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z" stroke-linejoin="round"/>',
    challenge: '<path d="M3 20h18M6 20l5-12 3 6 2-3 4 9"/><circle cx="17" cy="5" r="2"/>',
    vocab: '<path d="M4 19V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v13M12 19V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v13"/><path d="M4 19h16"/>',
    mistakes: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 8v4l3 2"/>',
    planner: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/><path d="M8 15h3M13 15h3"/>',
    analytics: '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    predictor: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>',
    calculator: '<rect x="5" y="2.5" width="14" height="19" rx="2"/><rect x="8" y="5.5" width="8" height="4" rx="0.8"/><path d="M8.5 13h1M12 13h1M15.5 13h1M8.5 17h1M12 17h1M15.5 17h1"/>',
    settings: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2.5"/><circle cx="9" cy="17" r="2.5"/>',
    account: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    flame: '<path d="M12 3c1 3 4 4.5 4 9a4 4 0 0 1-8 0c0-1.5.5-2.5 1-3.5.5 1 1 1.5 2 1.5 0-3-1-4.5 1-7z" stroke-linejoin="round"/>',
    check: '<path d="M5 12.5 10 17.5 19 7"/>',
    star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" stroke-linejoin="round"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pencil: '<path d="m4 20 4-1L19.5 7.5a2 2 0 0 0-3-3L5 16z" stroke-linejoin="round"/><path d="m14 6 4 4"/>'
  };
  const icon = (name, size = 18) => `<svg class="ico" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">${ICON[name] || ""}</svg>`;
  const spot = (name) => `<span class="spot">${icon(name, 22)}</span>`;

  // Half-ring gauge for a 400 to 1600 score.
  const gauge = (score, target) => {
    const f = score ? Math.max(0, Math.min(1, (score - 400) / 1200)) : 0;
    const t = target ? Math.max(0, Math.min(1, (target - 400) / 1200)) : null;
    const pt = (fr) => { const a = Math.PI * (1 - fr); return [100 + 84 * Math.cos(a), 96 - 84 * Math.sin(a)]; };
    const [tx, ty] = t !== null ? pt(t) : [0, 0];
    return `<svg class="gauge" viewBox="0 0 200 118" aria-hidden="true">
      <path d="M16 96 A84 84 0 0 1 184 96" pathLength="100" class="gauge-track"/>
      <path d="M16 96 A84 84 0 0 1 184 96" pathLength="100" class="gauge-fill" style="stroke-dasharray:${(f * 100).toFixed(1)} 100"/>
      ${t !== null ? `<circle cx="${tx.toFixed(1)}" cy="${ty.toFixed(1)}" r="5" class="gauge-target"><title>Target ${target}</title></circle>` : ""}
      <text x="16" y="116" text-anchor="middle" class="gauge-lbl">400</text><text x="184" y="116" text-anchor="middle" class="gauge-lbl">1600</text>
    </svg>`;
  };

  // Small progress ring, 0 to 1.
  const ring = (frac, label) => `<svg class="ring" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="18" class="ring-track"/><circle cx="22" cy="22" r="18" pathLength="100" class="ring-fill" style="stroke-dasharray:${(Math.max(0, Math.min(1, frac)) * 100).toFixed(1)} 100"/><text x="22" y="26" text-anchor="middle" class="ring-lbl">${label}</text></svg>`;

  // Accuracy by day, most recent days with activity, as an area line.
  const trend = (history, days = 14) => {
    const by = {};
    history.forEach((h) => { const k = Store.dayKey(h.ts); (by[k] = by[k] || { n: 0, ok: 0 }); by[k].n++; if (h.correct) by[k].ok++; });
    const keys = Object.keys(by).sort().slice(-days);
    if (keys.length < 2) return `<p class="fine">Accuracy over time appears after two days of practice.</p>`;
    const W = 320, H = 110, px = 8, py = 10;
    const x = (i) => px + (i * (W - 2 * px)) / (keys.length - 1);
    const y = (p) => py + (1 - p) * (H - 2 * py - 14);
    const pts = keys.map((k, i) => [x(i), y(by[k].ok / by[k].n)]);
    const line = pts.map(([a, b], i) => `${i ? "L" : "M"}${a.toFixed(1)} ${b.toFixed(1)}`).join(" ");
    const area = `${line} L${pts[pts.length - 1][0].toFixed(1)} ${H - 14} L${pts[0][0].toFixed(1)} ${H - 14} Z`;
    const lbl = (k) => { const d = new Date(k + "T00:00"); return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }); };
    return `<svg class="trend" viewBox="0 0 ${W} ${H}" aria-label="Accuracy by day">
      ${[0.5, 1].map((g) => `<line x1="${px}" x2="${W - px}" y1="${y(g).toFixed(1)}" y2="${y(g).toFixed(1)}" class="trend-grid"/>`).join("")}
      <path d="${area}" class="trend-area"/><path d="${line}" class="trend-line"/>
      ${pts.map(([a, b], i) => `<circle cx="${a.toFixed(1)}" cy="${b.toFixed(1)}" r="3" class="trend-dot"><title>${lbl(keys[i])}: ${Math.round(100 * by[keys[i]].ok / by[keys[i]].n)}% of ${by[keys[i]].n}</title></circle>`).join("")}
      <text x="${px}" y="${H - 2}" class="trend-lbl">${lbl(keys[0])}</text><text x="${W - px}" y="${H - 2}" text-anchor="end" class="trend-lbl">${lbl(keys[keys.length - 1])}</text>
      <text x="${W - px}" y="${(y(1) - 3).toFixed(1)}" text-anchor="end" class="trend-lbl">100%</text><text x="${W - px}" y="${(y(0.5) - 3).toFixed(1)}" text-anchor="end" class="trend-lbl">50%</text>
    </svg>`;
  };

  const pageHead = (name, title, lede) => `<div class="page-head"><div class="page-title">${spot(name)}<h1>${title}</h1></div>${lede ? `<p class="lede">${lede}</p>` : ""}</div>`;

  // ---------------------------------------------------------------- router
  const ROUTES = ["dashboard", "bank", "tests", "rush", "challenge", "vocab", "planner", "analytics", "calculator", "predictor", "mistakes", "settings", "account"];
  const route = () => (location.hash.replace(/^#\/?/, "").split("?")[0] || "dashboard");
  const go = (r) => { location.hash = "#/" + r; };
  const render = () => {
    const r = ROUTES.includes(route()) ? route() : "dashboard";
    document.querySelectorAll(".view").forEach((v) => { v.hidden = v.id !== "app"; });
    document.querySelectorAll(".nav-item").forEach((a) => a.classList.toggle("active", a.dataset.route === r));
    $("sidebar").classList.remove("open");
    PAGES[r]();
    window.scrollTo(0, 0);
  };
  // Every practice session returns to the page it started from.
  const launch = (opts) => Practice.start({ ...opts, onExit: () => { render(); } });

  // ---------------------------------------------------------------- pages
  const PAGES = {};

  PAGES.dashboard = () => {
    const st = Store.load();
    const pred = Scoring.predict(st.history);
    const streak = Store.streak();
    const total = st.history.length;
    const name = st.settings.name ? `, ${esc(st.settings.name.split(" ")[0])}` : "";
    const days = st.settings.testDate ? Math.ceil((new Date(st.settings.testDate + "T00:00") - new Date()) / 86400000) : null;

    // Weakest domains with enough data, for "Focus next".
    const doms = Object.keys(bank.meta.sections).flatMap((s) => bank.meta.sections[s].domains.map((d) => ({ s, d })));
    const focus = doms.map(({ s, d }) => ({ s, d, ...Store.accuracy((h) => h.domain === d) })).filter((x) => x.n >= 3).sort((a, b) => a.pct - b.pct).slice(0, 3);

    const nextSession = st.plan && st.plan.weeks.flatMap((w) => w.sessions).find((x) => !x.done);

    $("page").innerHTML = `
      ${pageHead("dashboard", `Dashboard${name}`)}
      <div class="dash-grid">
        <section class="card card-score">
          <h2>Predicted score</h2>
          ${pred.total ? `
            <div class="gauge-wrap">${gauge(pred.total, st.settings.target)}<div class="pred-total">${pred.total}<small>400 to 1600</small></div></div>
            <div class="pred-split"><div><span>Reading &amp; Writing</span><strong>${pred.rw.score}</strong></div><div><span>Math</span><strong>${pred.math.score}</strong></div></div>
            <p class="fine">Based on your last ${pred.rw.n + pred.math.n} answers${st.settings.target ? `. Target ${st.settings.target}` : ""}</p>`
          : `<div class="pred-empty">${gauge(0, st.settings.target)}<p>Take the diagnostic to get a predicted score.</p><button class="btn btn-primary" data-go="predictor">Take the diagnostic</button></div>`}
        </section>
        <section class="card">
          <h2>Focus next</h2>
          ${focus.length ? focus.map((f) => `<button type="button" class="focus-row" data-domain="${esc(f.d)}" data-section="${f.s}"><span>${esc(f.d)}</span><strong class="${f.pct < 60 ? "bad" : f.pct < 80 ? "mid" : "good"}">${f.pct}%</strong></button>`).join("") : `<p class="fine">Practice a few questions to see your weakest areas.</p>`}
        </section>
        <section class="card card-streak">
          <div class="streak-num"><span class="streak-ico ${streak ? "lit" : ""}">${icon("flame", 22)}</span>${streak}<small>day streak</small></div>
          <div class="streak-num"><span class="streak-ico">${icon("pencil", 22)}</span>${total}<small>questions answered</small></div>
          ${days !== null ? `<div class="streak-num ${days <= 14 ? "warn" : ""}"><span class="streak-ico">${icon("planner", 22)}</span>${days > 0 ? days : 0}<small>day${days === 1 ? "" : "s"} to test day</small></div>` : `<div class="streak-num"><span class="streak-ico">${icon("planner", 22)}</span><button class="btn-text" data-go="settings">Set your test date</button></div>`}
        </section>
        <section class="card card-next">
          <h2>Up next</h2>
          ${nextSession ? sessionCard(nextSession, true) : `<p>No study plan yet.</p><button class="btn btn-outline" data-go="planner">Build a plan</button>`}
        </section>
        <section class="card card-actions">
          <h2>Practice</h2>
          <div class="action-grid">
            <button data-go="bank">${spot("bank")}<strong>Question bank</strong><span>Practice by skill</span></button>
            <button data-go="tests">${spot("tests")}<strong>Practice test</strong><span>Full-length, timed</span></button>
            <button data-go="rush">${spot("rush")}<strong>Question Rush</strong><span>Timed drills</span></button>
            <button data-go="mistakes">${spot("mistakes")}<strong>Mistakes</strong><span>Review and retry</span></button>
          </div>
        </section>
        <section class="card card-trend"><h2>Accuracy</h2>${trend(st.history)}</section>
        <section class="card card-activity"><h2>Activity</h2>${heatmap(12)}</section>
      </div>`;
    wireGo();
    document.querySelectorAll(".focus-row").forEach((b) => b.addEventListener("click", () => startBank({ section: b.dataset.section, domain: b.dataset.domain })));
    wireSessionButtons();
  };

  const wireGo = () => document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));

  const heatmap = (weeks) => {
    const act = Store.activityByDay();
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const start = new Date(today); start.setDate(today.getDate() - (weeks * 7 - 1) - today.getDay());
    let cells = "";
    for (let d = new Date(start); d <= today; d.setDate(d.getDate() + 1)) {
      const k = Store.dayKey(d); const n = act[k] || 0;
      const lvl = n === 0 ? 0 : n < 5 ? 1 : n < 12 ? 2 : n < 25 ? 3 : 4;
      cells += `<i class="hm-${lvl}" title="${k}: ${n} question${n === 1 ? "" : "s"}"></i>`;
    }
    return `<div class="heatmap">${cells}</div><div class="heat-legend"><span>Less</span><i class="hm-0"></i><i class="hm-1"></i><i class="hm-2"></i><i class="hm-3"></i><i class="hm-4"></i><span>More</span></div>`;
  };

  // ---- Question bank -----------------------------------------------------
  const startBank = ({ section = "all", domain, skill, difficulty = "all", ids, label }) => {
    const qs = Practice.shuffle(qsIn({ section, domain, skill, difficulty, ids }));
    if (!qs.length) return alert("No questions match that yet.");
    launch({ mode: "bank", section, questions: qs, label: label || (skill || domain || secName(section)) });
  };

  PAGES.bank = () => {
    const params = new URLSearchParams(location.hash.split("?")[1] || "");
    const section = params.get("section") || "rw";
    const diff = params.get("difficulty") || "all";
    const latest = Store.latestByQuestion();
    const skillRows = Object.entries(bank.meta.skills[section]).map(([domain, skills]) => {
      const rows = skills.map((sk) => {
        const qs = qsIn({ section, skill: sk, difficulty: diff });
        const solved = qs.filter((q) => latest[q.id]).length, right = qs.filter((q) => latest[q.id] && latest[q.id].correct).length;
        const acc = solved ? Math.round(100 * right / solved) : null;
        return `<div class="skill-row"><div class="skill-name">${esc(sk)}<small>${qs.length} question${qs.length === 1 ? "" : "s"}${solved ? `, ${solved} solved` : ""}</small></div><div class="skill-acc">${acc === null ? '<span class="dim">-</span>' : `<span class="${acc < 60 ? "bad" : acc < 80 ? "mid" : "good"}">${acc}%</span>`}</div><button class="btn btn-sm btn-outline" data-skill="${esc(sk)}" ${qs.length ? "" : "disabled"}>Practice</button></div>`;
      }).join("");
      const dq = qsIn({ section, domain, difficulty: diff });
      const dAcc = Store.accuracy((h) => h.domain === domain);
      return `<section class="card skill-group"><div class="skill-group-head"><h2>${esc(domain)}</h2><span class="fine">${dq.length} questions${dAcc.n ? `, ${dAcc.pct}% accuracy` : ""}</span><button class="btn btn-sm btn-outline" data-domain="${esc(domain)}" ${dq.length ? "" : "disabled"}>Practice all</button></div>${rows}</section>`;
    }).join("");
    const total = qsIn({ section, difficulty: diff }).length;
    $("page").innerHTML = `
      ${pageHead("bank", "Question bank", `Practice by skill with an explanation after every question.`)}
      <div class="toolbar">
        <div class="seg">${["rw", "math"].map((s) => `<button class="${s === section ? "on" : ""}" data-sec="${s}">${secName(s)}</button>`).join("")}</div>
        <div class="seg">${["all", "easy", "medium", "hard"].map((d) => `<button class="${d === diff ? "on" : ""}" data-diff="${d}">${d === "all" ? "All levels" : d[0].toUpperCase() + d.slice(1)}</button>`).join("")}</div>
        <button class="btn btn-primary" id="bank-all">Practice all ${total}</button>
      </div>
      ${skillRows}`;
    document.querySelectorAll("[data-sec]").forEach((b) => b.addEventListener("click", () => { location.hash = `#/bank?section=${b.dataset.sec}&difficulty=${diff}`; }));
    document.querySelectorAll("[data-diff]").forEach((b) => b.addEventListener("click", () => { location.hash = `#/bank?section=${section}&difficulty=${b.dataset.diff}`; }));
    document.querySelectorAll("[data-skill]").forEach((b) => b.addEventListener("click", () => startBank({ section, skill: b.dataset.skill, difficulty: diff })));
    document.querySelectorAll("[data-domain]").forEach((b) => b.addEventListener("click", () => startBank({ section, domain: b.dataset.domain, difficulty: diff })));
    $("bank-all").addEventListener("click", () => startBank({ section, difficulty: diff, label: `${secName(section)}${diff !== "all" ? ": " + diff : ""}` }));
  };

  // ---- Practice tests ----------------------------------------------------
  const startModule = (section) => {
    const all = bank.questions.filter((q) => q.section === section);
    const qs = Practice.shuffle(all).slice(0, MODULE_SIZE[section]);
    launch({ mode: "test", section, questions: qs, label: secName(section), seconds: moduleSeconds(section, qs.length) });
  };
  PAGES.tests = () => {
    const attempts = Store.load().attempts.filter((a) => a.mode === "test").slice().reverse();
    $("page").innerHTML = `
      ${pageHead("tests", "Practice tests", `Full-length timed modules in the Digital SAT format.`)}
      <div class="two-col">
        ${["rw", "math"].map((s) => { const n = Math.min(MODULE_SIZE[s], bank.questions.filter((q) => q.section === s).length); return `
        <section class="card module-card">
          ${spot(s === "rw" ? "vocab" : "calculator")}
          <h2>${secName(s)}</h2>
          <p>${icon("clock", 15)} ${n} questions, ${fmtMin(moduleSeconds(s, n))}</p>
          <button class="btn btn-primary" data-module="${s}">Start module</button>
        </section>`; }).join("")}
      </div>
      <section class="card">
        <h2>History</h2>
        ${attempts.length ? `<table class="table"><thead><tr><th>Date</th><th>Module</th><th>Score</th><th>Estimate</th><th>Time</th></tr></thead><tbody>${attempts.map((a) => `<tr><td>${fmtDate(a.ts)}</td><td>${esc(a.label)}</td><td>${a.correct}/${a.n}</td><td>${a.section !== "all" ? Scoring.scaled(a.section, a.correct / a.n) : "-"}</td><td>${Math.floor(a.seconds / 60)}:${String(a.seconds % 60).padStart(2, "0")}</td></tr>`).join("")}</tbody></table>` : `<p class="fine">No attempts yet.</p>`}
      </section>`;
    document.querySelectorAll("[data-module]").forEach((b) => b.addEventListener("click", () => startModule(b.dataset.module)));
  };

  // ---- Question Rush -----------------------------------------------------
  PAGES.rush = () => {
    const attempts = Store.load().attempts.filter((a) => a.mode === "rush").slice().reverse().slice(0, 8);
    const best = attempts.reduce((m, a) => Math.max(m, a.stars || 0), 0);
    $("page").innerHTML = `
      ${pageHead("rush", "Question Rush", `Timed drills. Earn stars for speed and accuracy.`)}
      <div class="two-col">
        <section class="card">
          <h2>New rush</h2>
          <form id="rush-form" class="filters">
            <label>Section<select name="section"><option value="rw">Reading and Writing</option><option value="math">Math</option></select></label>
            <label>Domain<select name="domain"><option value="all">All domains</option></select></label>
            <label>Difficulty<select name="difficulty"><option value="all">All</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <label>Questions<select name="count"><option>5</option><option selected>10</option><option>15</option></select></label>
            <label>Seconds per question<select name="pace"><option value="30">30</option><option value="45">45</option><option value="60" selected>60</option><option value="90">90</option></select></label>
            <button type="submit" class="btn btn-primary">Start rush <span id="rush-count" class="count"></span></button>
          </form>
        </section>
        <section class="card">
          <h2>History</h2>
          
          ${attempts.length ? `<table class="table"><thead><tr><th>Date</th><th>Set</th><th>Stars</th><th>Accuracy</th></tr></thead><tbody>${attempts.map((a) => `<tr><td>${fmtDate(a.ts)}</td><td>${esc(a.label)}</td><td><span class="stars">${icon("star", 14)} ${a.stars}/${a.n * 3}</span></td><td>${a.correct}/${a.n}</td></tr>`).join("")}</tbody></table>` : `<p class="fine">No rushes yet.</p>`}
        </section>
      </div>`;
    const f = $("rush-form");
    const fillDomains = () => { const s = f.elements.section.value; f.elements.domain.innerHTML = '<option value="all">All domains</option>' + bank.meta.sections[s].domains.map((d) => `<option>${esc(d)}</option>`).join(""); };
    const count = () => { const n = qsIn({ section: f.elements.section.value, domain: f.elements.domain.value, difficulty: f.elements.difficulty.value }).length; $("rush-count").textContent = `(${Math.min(n, +f.elements.count.value)} available)`; f.querySelector("button").disabled = n === 0; };
    fillDomains(); count();
    f.elements.section.addEventListener("change", () => { fillDomains(); count(); });
    ["domain", "difficulty", "count"].forEach((k) => f.elements[k].addEventListener("change", count));
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      const s = f.elements.section.value, d = f.elements.domain.value;
      const qs = Practice.shuffle(qsIn({ section: s, domain: d, difficulty: f.elements.difficulty.value })).slice(0, +f.elements.count.value);
      launch({ mode: "rush", section: s, questions: qs, label: `Rush: ${d === "all" ? secName(s) : d}`, pace: +f.elements.pace.value });
    });
  };

  // ---- Challenge questions ----------------------------------------------
  PAGES.challenge = () => {
    const latest = Store.latestByQuestion();
    $("page").innerHTML = `
      ${pageHead("challenge", "Challenge questions", `The hardest questions in the bank.`)}
      <div class="two-col">${["rw", "math"].map((s) => { const qs = qsIn({ section: s, difficulty: "hard" }); const done = qs.filter((q) => latest[q.id]).length, right = qs.filter((q) => latest[q.id] && latest[q.id].correct).length; return `
        <section class="card">${spot("challenge")}<h2>${secName(s)}</h2><p>${qs.length} questions${done ? `, ${done} solved` : ""}</p>${pctBar("Accuracy", right, done)}<button class="btn btn-primary" data-ch="${s}" style="margin-top:16px" ${qs.length ? "" : "disabled"}>Practice</button></section>`; }).join("")}</div>`;
    document.querySelectorAll("[data-ch]").forEach((b) => b.addEventListener("click", () => startBank({ section: b.dataset.ch, difficulty: "hard", label: `${secName(b.dataset.ch)}: hard` })));
  };

  // ---- Vocabulary --------------------------------------------------------
  PAGES.vocab = () => {
    const prog = Store.load().vocab;
    const mastered = vocab.words.filter((w) => prog[w.word] && prog[w.word].right >= 2).length;
    $("page").innerHTML = `
      ${pageHead("vocab", "Vocabulary", `${vocab.words.length} words for Words in Context questions.`)}
      <div class="two-col">
        <section class="card"><h2>Flashcards</h2><div class="flash" id="flash"></div><div class="flash-controls"><button class="btn btn-outline btn-sm" id="flash-prev">Previous</button><button class="btn btn-primary btn-sm" id="flash-flip">Flip</button><button class="btn btn-outline btn-sm" id="flash-next">Next</button></div></section>
        <section class="card"><div class="ring-row">${ring(mastered / vocab.words.length, mastered)}<div><h2>Quiz</h2><p class="fine">${mastered} of ${vocab.words.length} words mastered</p></div></div><div id="quiz" style="margin-top:18px"></div></section>
      </div>
      <section class="card"><h2>Word list</h2><div class="word-grid">${vocab.words.map((w) => { const p = prog[w.word]; const m = p && p.right >= 2; return `<div class="word-chip ${m ? "mastered" : ""}"><strong>${esc(w.word)}</strong> <em>${esc(w.pos)}</em><span>${esc(w.def)}</span></div>`; }).join("")}</div></section>`;

    // flashcards
    let i = Math.floor(Math.random() * vocab.words.length), flipped = false;
    const drawFlash = () => { const w = vocab.words[i]; $("flash").innerHTML = flipped ? `<div class="flash-back"><strong>${esc(w.word)}</strong> <em>${esc(w.pos)}</em><p>${esc(w.def)}</p><p class="ex">“${esc(w.example)}”</p></div>` : `<div class="flash-front">${esc(w.word)}</div>`; };
    drawFlash();
    $("flash").addEventListener("click", () => { flipped = !flipped; drawFlash(); });
    $("flash-flip").addEventListener("click", () => { flipped = !flipped; drawFlash(); });
    $("flash-next").addEventListener("click", () => { i = (i + 1) % vocab.words.length; flipped = false; drawFlash(); });
    $("flash-prev").addEventListener("click", () => { i = (i - 1 + vocab.words.length) % vocab.words.length; flipped = false; drawFlash(); });

    // quiz: pick words with the fewest correct answers first
    const drawQuiz = () => {
      const pool = vocab.words.slice().sort((a, b) => ((prog[a.word] || {}).right || 0) - ((prog[b.word] || {}).right || 0) + (Math.random() - 0.5));
      const w = pool[Math.floor(Math.random() * Math.min(8, pool.length))];
      const others = Practice.shuffle(vocab.words.filter((x) => x !== w)).slice(0, 3);
      const opts = Practice.shuffle([w, ...others]);
      $("quiz").innerHTML = `<p class="quiz-q">Which is the best definition of <strong>${esc(w.word)}</strong>?</p><div class="quiz-opts">${opts.map((o) => `<button class="quiz-opt" data-w="${esc(o.word)}">${esc(o.def)}</button>`).join("")}</div><div class="quiz-fb" id="quiz-fb"></div>`;
      $("quiz").querySelectorAll(".quiz-opt").forEach((b) => b.addEventListener("click", () => {
        const right = b.dataset.w === w.word;
        Store.vocabResult(w.word, right);
        $("quiz").querySelectorAll(".quiz-opt").forEach((x) => { x.disabled = true; if (x.dataset.w === w.word) x.classList.add("correct"); else if (x === b) x.classList.add("wrong"); });
        $("quiz-fb").innerHTML = `${right ? "Correct." : "Incorrect."} <em>${esc(w.example)}</em> <button class="btn btn-sm btn-primary" id="quiz-next">Next</button>`;
        $("quiz-next").addEventListener("click", () => { PAGES.vocab(); });
      }));
    };
    drawQuiz();
  };

  // ---- Study planner -----------------------------------------------------
  const sessionCard = (s, compact) => `<div class="session ${s.done ? "done" : ""}"><div class="session-body"><strong>${esc(s.title)}</strong><span>${esc(s.sub)}, ${s.minutes} min</span></div><div class="session-actions"><button class="btn btn-sm btn-primary" data-start="${s.id}">${s.done ? "Again" : "Start"}</button>${compact ? "" : `<button class="btn-text" data-done="${s.id}">${s.done ? "Undo" : "Mark done"}</button>`}</div></div>`;
  const wireSessionButtons = () => {
    document.querySelectorAll("[data-start]").forEach((b) => b.addEventListener("click", () => runSession(b.dataset.start)));
    document.querySelectorAll("[data-done]").forEach((b) => b.addEventListener("click", () => { const s = findSession(b.dataset.done); Store.markSession(s.id, !s.done); render(); }));
  };
  const findSession = (id) => Store.load().plan.weeks.flatMap((w) => w.sessions).find((s) => s.id === id);
  const runSession = (id) => {
    const s = findSession(id);
    Store.markSession(id, true);
    if (s.type === "module") return startModule(s.section);
    if (s.type === "rush") { const qs = Practice.shuffle(qsIn({ section: s.section })).slice(0, 10); return launch({ mode: "rush", section: s.section, questions: qs, label: `Rush: ${secName(s.section)}`, pace: 60 }); }
    if (s.type === "mistakes") { const ids = mistakeIds(); if (!ids.size) return alert("No mistakes to review yet."); return startBank({ ids, label: "Mistakes review" }); }
    if (s.type === "vocab") return go("vocab");
    return startBank({ section: s.section, domain: s.domain, label: s.domain });
  };
  const buildPlan = () => {
    const st = Store.load(); const { testDate, daysPerWeek, sessionMinutes } = st.settings;
    const start = new Date(); start.setHours(0, 0, 0, 0);
    const end = new Date(testDate + "T00:00");
    const weeks = Math.max(1, Math.min(12, Math.ceil((end - start) / (7 * 86400000))));
    // Weakest domain per section drives the drill sessions; ties go to the
    // domain with the least data so every domain gets seen.
    const weakest = (s) => bank.meta.sections[s].domains.map((d) => ({ d, ...Store.accuracy((h) => h.domain === d) })).sort((a, b) => (a.pct ?? -1) - (b.pct ?? -1) || a.n - b.n);
    const plan = { createdAt: Date.now(), weeks: [] };
    for (let w = 0; w < weeks; w++) {
      const wk = { start: new Date(start.getTime() + w * 7 * 86400000).toISOString().slice(0, 10), sessions: [] };
      const rw = weakest("rw"), m = weakest("math");
      const menu = [
        { type: "drill", section: "rw", domain: rw[w % rw.length].d, title: `Drill: ${rw[w % rw.length].d}`, sub: "Reading and Writing" },
        { type: "drill", section: "math", domain: m[w % m.length].d, title: `Drill: ${m[w % m.length].d}`, sub: "Math" },
        { type: "rush", section: w % 2 ? "math" : "rw", title: "Question Rush", sub: w % 2 ? "Math" : "Reading and Writing" },
        { type: "module", section: w % 2 ? "rw" : "math", title: `Practice test: ${w % 2 ? "Reading and Writing" : "Math"}`, sub: "Timed" },
        { type: "mistakes", title: "Mistakes", sub: "Review" },
        { type: "vocab", title: "Vocabulary", sub: "Flashcards" }
      ];
      for (let d = 0; d < daysPerWeek; d++) { const s = menu[d % menu.length]; wk.sessions.push({ id: `w${w}s${d}`, ...s, minutes: s.type === "module" ? 20 : sessionMinutes, done: false }); }
      plan.weeks.push(wk);
    }
    Store.setPlan(plan);
  };
  PAGES.planner = () => {
    const st = Store.load(); const s = st.settings;
    const plan = st.plan;
    const days = s.testDate ? Math.ceil((new Date(s.testDate + "T00:00") - new Date()) / 86400000) : null;
    $("page").innerHTML = `
      ${pageHead("planner", "Study planner", `A weekly plan built around your test date and weakest areas.`)}
      <section class="card"><form id="plan-form" class="filters filters-row">
        <label>Test date<input type="date" name="testDate" value="${esc(s.testDate)}" required></label>
        <label>Target score<input type="number" name="target" min="400" max="1600" step="10" value="${s.target}"></label>
        <label>Days per week<select name="daysPerWeek">${[2, 3, 4, 5, 6].map((n) => `<option ${n === s.daysPerWeek ? "selected" : ""}>${n}</option>`).join("")}</select></label>
        <label>Minutes per session<select name="sessionMinutes">${[20, 30, 45, 60].map((n) => `<option ${n === s.sessionMinutes ? "selected" : ""}>${n}</option>`).join("")}</select></label>
        <button type="submit" class="btn btn-primary">${plan ? "Rebuild plan" : "Build my plan"}</button>
      </form></section>
      ${plan ? plan.weeks.map((w, i) => `<section class="card week"><div class="week-head"><h2>Week ${i + 1}</h2><span class="fine">${fmtDate(w.start + "T00:00")}, ${w.sessions.filter((x) => x.done).length}/${w.sessions.length} done</span></div>${w.sessions.map((x) => sessionCard(x)).join("")}</section>`).join("") : ""}`;
    $("plan-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      Store.setSettings({ testDate: fd.get("testDate"), target: +fd.get("target"), daysPerWeek: +fd.get("daysPerWeek"), sessionMinutes: +fd.get("sessionMinutes") });
      if (new Date(fd.get("testDate") + "T00:00") <= new Date()) return alert("Pick a test date in the future.");
      buildPlan(); render();
    });
    wireSessionButtons();
  };

  // ---- Analytics ---------------------------------------------------------
  PAGES.analytics = () => {
    const st = Store.load(); const h = st.history;
    const bySkill = (s) => Object.entries(bank.meta.skills[s]).flatMap(([d, skills]) => skills.map((sk) => ({ d, sk, ...Store.accuracy((x) => x.skill === sk) }))).filter((x) => x.n);
    const byDiff = ["easy", "medium", "hard"].map((d) => { const rows = h.filter((x) => x.difficulty === d && x.seconds > 0); return { d, n: rows.length, avg: rows.length ? rows.reduce((a, x) => a + x.seconds, 0) / rows.length : null, acc: Store.accuracy((x) => x.difficulty === d) }; });
    const attempts = st.attempts.slice().reverse().slice(0, 12);
    $("page").innerHTML = `
      ${pageHead("analytics", "Analytics", `${h.length} question${h.length === 1 ? "" : "s"} answered.`)}
      ${h.length ? `<section class="card"><h2>Accuracy over time</h2>${trend(h, 30)}</section>` : `<section class="card"><p>No data yet.</p></section>`}
      <div class="two-col">
        ${["rw", "math"].map((s) => `<section class="card"><h2>${secName(s)}</h2>${bank.meta.sections[s].domains.map((d) => { const a = Store.accuracy((x) => x.domain === d); return pctBar(d, a.ok, a.n); }).join("")}</section>`).join("")}
      </div>
      <div class="two-col">
        <section class="card"><h2>By skill</h2>${["rw", "math"].map((s) => { const rows = bySkill(s); return rows.length ? `<table class="table"><thead><tr><th>${secName(s)}</th><th>Solved</th><th>Accuracy</th></tr></thead><tbody>${rows.sort((a, b) => a.pct - b.pct).map((r) => `<tr><td>${esc(r.sk)}<div class="review-meta">${esc(r.d)}</div></td><td>${r.n}</td><td class="${r.pct < 60 ? "bad" : r.pct < 80 ? "mid" : "good"}">${r.pct}%</td></tr>`).join("")}</tbody></table>` : ""; }).join("") || '<p class="fine">No data yet.</p>'}</section>
        <section class="card"><h2>Pacing</h2><p class="fine">Average seconds per question</p>${byDiff.map((r) => `<div class="pace-row"><span>${r.d[0].toUpperCase() + r.d.slice(1)}</span><strong>${r.avg === null ? "-" : Math.round(r.avg) + "s"}</strong><small>${r.acc.n ? `${r.acc.pct}% correct, ${r.acc.n} answered` : ""}</small></div>`).join("")}
        <h2 style="margin-top:28px">Activity</h2>${heatmap(16)}</section>
      </div>
      <section class="card"><h2>Recent sessions</h2>${attempts.length ? `<table class="table"><thead><tr><th>Date</th><th>Type</th><th>Set</th><th>Result</th></tr></thead><tbody>${attempts.map((a) => `<tr><td>${fmtDate(a.ts)}</td><td>${{ test: "Module", rush: "Rush", diagnostic: "Diagnostic", bank: "Bank" }[a.mode] || a.mode}</td><td>${esc(a.label)}</td><td>${a.correct}/${a.n}${a.stars != null ? `, ${a.stars} stars` : ""}</td></tr>`).join("")}</tbody></table>` : '<p class="fine">No sessions yet.</p>'}</section>`;
    wireGo();
  };

  // ---- Score calculator --------------------------------------------------
  PAGES.calculator = () => {
    $("page").innerHTML = `
      ${pageHead("calculator", "Score calculator", `Estimate a scaled score from raw module scores.`)}
      <div class="two-col">
        <section class="card"><form id="calc-form" class="filters">
          ${[["rw1", "Reading and Writing, Module 1", 27], ["rw2", "Reading and Writing, Module 2", 27], ["m1", "Math, Module 1", 22], ["m2", "Math, Module 2", 22]].map(([k, l, max]) => `<label>${l}<div class="range-row"><input type="range" name="${k}" min="0" max="${max}" value="${Math.round(max / 2)}"><output name="${k}o">${Math.round(max / 2)}</output><span class="fine">/ ${max}</span></div></label>`).join("")}
        </form></section>
        <section class="card calc-out"><h2>Estimated score</h2><div class="pred-total" id="calc-total">-<small>400 to 1600</small></div><div class="pred-split"><div><span>Reading &amp; Writing</span><strong id="calc-rw">-</strong></div><div><span>Math</span><strong id="calc-m">-</strong></div></div>
          <table class="table" style="margin-top:18px"><tbody><tr><td>1000 to 1100</td><td>National average</td></tr><tr><td>1200 to 1300</td><td>Competitive for many universities</td></tr><tr><td>1400+</td><td>Strong for selective colleges</td></tr><tr><td>1500+</td><td>Highly competitive</td></tr></tbody></table></section>
      </div>`;
    const f = $("calc-form");
    const calc = () => {
      const v = (k) => +f.elements[k].value;
      ["rw1", "rw2", "m1", "m2"].forEach((k) => { f.elements[k + "o"].value = v(k); });
      const rw = Scoring.scaled("rw", (v("rw1") + v("rw2")) / 54), m = Scoring.scaled("math", (v("m1") + v("m2")) / 44);
      $("calc-rw").textContent = rw; $("calc-m").textContent = m; $("calc-total").firstChild.textContent = rw + m;
    };
    f.addEventListener("input", calc); calc();
  };

  // ---- Score predictor (diagnostic) --------------------------------------
  PAGES.predictor = () => {
    const last = Store.load().attempts.filter((a) => a.mode === "diagnostic").slice(-1)[0];
    $("page").innerHTML = `
      ${pageHead("predictor", "Score predictor", `A 16-question diagnostic with an estimated score.`)}
      <div class="two-col">
        <section class="card">${spot("predictor")}<h2>Diagnostic</h2><p>${icon("clock", 15)} 16 questions, 22 minutes</p><button class="btn btn-primary" id="diag-start">Start the diagnostic</button>${last ? `<p class="fine" style="margin-top:14px">Last taken ${fmtDate(last.ts)}, ${last.correct}/${last.n}</p>` : ""}</section>
        <section class="card"><h2>Predicted score</h2>${(() => { const p = Scoring.predict(Store.load().history); return p.total ? `<div class="gauge-wrap">${gauge(p.total, Store.load().settings.target)}<div class="pred-total">${p.total}<small>400 to 1600</small></div></div><div class="pred-split"><div><span>Reading &amp; Writing</span><strong>${p.rw.score}</strong></div><div><span>Math</span><strong>${p.math.score}</strong></div></div>` : `<p class="fine">Take the diagnostic or answer ${Scoring.MIN_PER_SECTION} questions per section.</p>`; })()}</section>
      </div>`;
    $("diag-start").addEventListener("click", () => {
      const qs = [];
      Object.keys(bank.meta.sections).forEach((s) => bank.meta.sections[s].domains.forEach((d) => {
        const pool = Practice.shuffle(bank.questions.filter((q) => q.section === s && q.domain === d));
        // one easier, one harder where possible
        const a = pool.find((q) => q.difficulty !== "hard") || pool[0], b = pool.find((q) => q !== a && q.difficulty !== "easy") || pool.find((q) => q !== a);
        [a, b].filter(Boolean).forEach((q) => qs.push(q));
      }));
      const ordered = [...qs.filter((q) => q.section === "rw"), ...qs.filter((q) => q.section === "math")];
      const secs = Math.round(ordered.reduce((t, q) => t + SECONDS_PER_Q[q.section], 0) / 60) * 60;
      launch({ mode: "diagnostic", section: "all", questions: ordered, label: "Diagnostic", seconds: secs });
    });
  };

  // ---- Mistakes ----------------------------------------------------------
  const mistakeIds = () => { const latest = Store.latestByQuestion(); return new Set(Object.keys(latest).filter((id) => !latest[id].correct)); };
  PAGES.mistakes = () => {
    const latest = Store.latestByQuestion(); const ids = mistakeIds();
    const qs = bank.questions.filter((q) => ids.has(q.id));
    $("page").innerHTML = `
      ${pageHead("mistakes", "Mistakes", `Questions you got wrong most recently.`)}
      <section class="card">${qs.length ? `<div class="toolbar"><span>${qs.length} question${qs.length === 1 ? "" : "s"} to revisit</span><button class="btn btn-primary" id="redo-all">Redo all</button></div><ol class="review-list">${qs.map((q) => `<li><button class="review-item" data-q="${q.id}"><span class="review-num no">${q.section === "rw" ? "RW" : "M"}</span><span><span>${esc(q.stem.split("\n")[0]).slice(0, 110)}</span><div class="review-meta">${esc(q.skill)}, ${fmtDate(latest[q.id].ts)}</div></span><span class="review-ans">Redo</span></button></li>`).join("")}</ol>` : `<p>No mistakes to review.</p>`}</section>`;
    wireGo();
    if (qs.length) {
      $("redo-all").addEventListener("click", () => startBank({ ids, label: "Mistakes review" }));
      document.querySelectorAll("[data-q]").forEach((b) => b.addEventListener("click", () => startBank({ ids: new Set([b.dataset.q]), label: "Mistakes review" })));
    }
  };

  // ---- Settings ----------------------------------------------------------
  PAGES.settings = () => {
    const s = Store.load().settings;
    $("page").innerHTML = `
      ${pageHead("settings", "Settings")}
      <section class="card"><form id="settings-form" class="filters filters-row">
        <label>Your name<input type="text" name="name" value="${esc(s.name)}"></label>
        <label>Test date<input type="date" name="testDate" value="${esc(s.testDate)}"></label>
        <label>Target score<input type="number" name="target" min="400" max="1600" step="10" value="${s.target}"></label>
        <button type="submit" class="btn btn-primary">Save</button>
      </form></section>
      <section class="card"><h2>Data</h2><p class="fine">${Auth.user() ? `Your progress is saved to your account (${esc(Auth.user().email)}) and to this browser.` : Auth.enabled ? `Your progress is stored in this browser. <a href="#/account">Create an account</a> to keep it across devices.` : "Your progress is stored in this browser only."}</p><button class="btn btn-outline btn-sm" id="reset-all">Reset progress</button></section>
      <section class="card"><h2>About</h2><p class="fine">Built by <a href="https://ableinitiatives.com">ABLE Initiatives</a>. Report a question issue at <a href="mailto:ableinitiativespchs@gmail.com">ableinitiativespchs@gmail.com</a>.</p><p class="fine">SAT is a registered trademark of College Board, which is not affiliated with this site.</p></section>`;
    $("settings-form").addEventListener("submit", (e) => { e.preventDefault(); const fd = new FormData(e.target); Store.setSettings({ name: fd.get("name").trim(), testDate: fd.get("testDate"), target: +fd.get("target") || 1300 }); render(); });
    $("reset-all").addEventListener("click", () => { if (confirm(Auth.user() ? "Clear every answer, session, plan, and setting on this account and this browser?" : "Clear every answer, session, plan, and setting in this browser?")) { Store.reset(); render(); } });
  };

  // ---- Account -----------------------------------------------------------
  const STATUS_TEXT = { idle: "", syncing: "Saving…", synced: "Saved to your account", offline: "Offline. Will save when you're back.", error: "Couldn't save. Check your connection." };
  const renderFoot = () => {
    const u = Auth.user();
    $("account-bar").innerHTML = u
      ? `<a class="who" href="#/account" title="${esc(u.email)}"><i>${esc(u.email[0].toUpperCase())}</i><span>${esc(u.email)}</span></a>`
      : Auth.enabled ? `<a class="btn btn-outline btn-sm" href="#/account">Sign in</a><a class="btn btn-primary btn-sm" href="#/account?new">Create account</a>` : "";
    $("sidebar-foot").innerHTML = u
      ? `<a href="#/account" title="${esc(u.email)}">${esc(u.email)}</a><span id="sync-status">${STATUS_TEXT[Auth.status()] || ""}</span>`
      : Auth.enabled ? `<a href="#/account">Sign in</a><span>Save progress across devices</span>`
      : `<a href="https://ableinitiatives.com/preps.html">ABLE Preps</a><span>No account needed</span>`;
  };
  const authError = (e) => {
    const m = (e && e.message) || "Something went wrong.";
    if (/invalid login/i.test(m)) return "Wrong email or password.";
    if (/already registered/i.test(m)) return "That email already has an account. Sign in instead.";
    if (/rate limit/i.test(m)) return "Too many tries. Wait a minute and try again.";
    if (/password/i.test(m) && /6/.test(m)) return "Use at least 6 characters.";
    return m;
  };
  const form = (id, fields, submit, extra = "") => `<form id="${id}" class="filters auth-form">${fields}<button type="submit" class="btn btn-primary">${submit}</button>${extra}<p class="fine auth-msg" hidden></p></form>`;
  const wireForm = (id, handler) => {
    const f = $(id); if (!f) return;
    f.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = f.querySelector(".auth-msg"), btn = f.querySelector("[type=submit]");
      msg.hidden = true; btn.disabled = true;
      try { const note = await handler(new FormData(f)); if (note) { msg.textContent = note; msg.className = "fine auth-msg ok"; msg.hidden = false; } }
      catch (err) { msg.textContent = authError(err); msg.className = "fine auth-msg bad"; msg.hidden = false; }
      btn.disabled = false;
    });
  };
  PAGES.account = () => {
    if (!Auth.enabled) { $("page").innerHTML = `<div class="page-head"><h1>Account</h1><p class="lede">Accounts aren't switched on for this copy of the app. Progress stays in this browser.</p></div>`; return; }
    const u = Auth.user();
    if (u) {
      const st = Store.load();
      $("page").innerHTML = `
        ${pageHead("account", "Account", esc(u.email))}
        <div class="two-col">
          <section class="card"><h2>Progress</h2>
            <p>${st.history.length} answers and ${st.attempts.length} sessions are saved to this account. Sign in on any device to pick up where you left off.</p>
            <p class="fine" id="sync-line">${STATUS_TEXT[Auth.status()] || ""}</p>
            <div class="toolbar" style="margin:0"><button class="btn btn-outline btn-sm" id="sync-now">Sync now</button><button class="btn btn-outline btn-sm" id="sign-out">Sign out</button></div>
          </section>
          <section class="card"><h2>${Auth.inRecovery() ? "Set a new password" : "Change password"}</h2>
            ${form("pw-form", `<label>New password<input type="password" name="password" minlength="6" required autocomplete="new-password"></label>`, "Update password")}
          </section>
        </div>
        <section class="card"><h2>Delete account data</h2><p class="fine">Removes everything saved to this account on the server. This browser keeps its copy until you reset progress in Settings.</p><button class="btn btn-outline btn-sm" id="delete-data">Delete server data</button></section>`;
      $("sign-out").addEventListener("click", async () => { await Auth.signOut(); go("dashboard"); });
      $("sync-now").addEventListener("click", async () => { await Auth.pull(); render(); });
      $("delete-data").addEventListener("click", async () => { if (confirm("Delete everything saved to this account on the server?")) { try { await Auth.deleteData(); alert("Deleted."); } catch (e) { alert(authError(e)); } } });
      wireForm("pw-form", async (fd) => { await Auth.updatePassword(fd.get("password")); return "Password updated."; });
      return;
    }
    const st = Store.load();
    $("page").innerHTML = `
      ${pageHead("account", "Account", "Free. Your progress follows you to any device.")}
      <div class="two-col">
        <section class="card"><h2>Sign in</h2>
          ${form("in-form", `<label>Email<input type="email" name="email" required autocomplete="email"></label><label>Password<input type="password" name="password" required autocomplete="current-password"></label>`, "Sign in", `<button type="button" class="btn-text" id="forgot">Forgot password?</button>`)}
        </section>
        <section class="card"><h2>Create an account</h2>
          ${st.history.length ? `<p class="fine">The ${st.history.length} answers already in this browser will be added to the new account.</p>` : ""}
          ${form("up-form", `<label>Email<input type="email" name="email" required autocomplete="email"></label><label>Password<input type="password" name="password" minlength="6" required autocomplete="new-password"></label>`, "Create account")}
        </section>
      </div>
      <p class="fine">What's saved: your answers, sessions, plan, vocabulary progress, and settings. Nothing else. Questions about your data: <a href="mailto:ableinitiativespchs@gmail.com">ableinitiativespchs@gmail.com</a>.</p>`;
    if (location.hash.includes("?new")) $("up-form").email.focus();
    wireForm("in-form", async (fd) => { await Auth.signIn(fd.get("email").trim(), fd.get("password")); go("dashboard"); });
    wireForm("up-form", async (fd) => { const r = await Auth.signUp(fd.get("email").trim(), fd.get("password")); if (r.needsConfirm) return "Check your email for a confirmation link, then sign in."; go("dashboard"); });
    $("forgot").addEventListener("click", async () => {
      const f = $("in-form"), email = f.email.value.trim(), msg = f.querySelector(".auth-msg");
      if (!email) { f.email.focus(); return; }
      try { await Auth.resetPassword(email); msg.textContent = "Reset link sent. Check your email."; msg.className = "fine auth-msg ok"; }
      catch (e) { msg.textContent = authError(e); msg.className = "fine auth-msg bad"; }
      msg.hidden = false;
    });
  };

  // ---------------------------------------------------------------- boot
  Promise.all([fetch("data/questions.json?v=3").then((r) => r.json()), fetch("data/vocab.json?v=3").then((r) => r.json())])
    .then(([q, v]) => {
      bank = q; vocab = v;
      Practice.init();
      document.querySelectorAll(".nav-item[data-route]").forEach((a) => { a.insertAdjacentHTML("afterbegin", icon(a.dataset.route)); });
      $("menu-toggle").addEventListener("click", () => $("sidebar").classList.toggle("open"));
      window.addEventListener("hashchange", render);
      renderFoot();
      Auth.onChange((u, status) => {
        renderFoot();
        const line = $("sync-line"); if (line) line.textContent = STATUS_TEXT[status] || "";
      });
      // A pull can change every number on the page; redraw unless mid-session.
      Auth.onPull(() => { if ($("view-practice").hidden && $("view-results").hidden) render(); });
      render();
      Auth.init();
    })
    .catch((err) => { $("page").innerHTML = `<p class="lede">Couldn't load the question bank. ${esc(err.message)}</p>`; });
})();
