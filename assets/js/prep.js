/* ABLE Preps · SAT Practice
   One page, three views: home (pick a mode), practice (the Bluebook-style
   screen), results. No framework, no build. Progress lives in localStorage
   under one key, so "reset" is one line and nothing leaves the browser. */
(() => {
  "use strict";

  const STORAGE_KEY = "ablePrep.history.v1";
  // Real Digital SAT pacing: Reading and Writing is 27 questions in 32 minutes,
  // Math is 22 in 35. Modules here are shorter, so the clock scales to match.
  const SECONDS_PER_Q = { rw: (32 * 60) / 27, math: (35 * 60) / 22 };
  const LETTERS = ["A", "B", "C", "D"];
  const DIRECTIONS = {
    rw: "The questions in this section address a number of important reading and writing skills. Each question includes one or more passages, which may include a table or graph. Read each passage and question carefully, and then choose the best answer to the question based on the passage(s). All questions in this section are multiple-choice with four answer choices. Each question has a single best answer.",
    math: "The questions in this section address a number of important math skills. Use of a calculator is permitted for all questions. For multiple-choice questions, solve each problem and choose the correct answer from the choices provided. For student-produced response questions, solve each problem and enter your answer in the box. Figures are drawn to scale unless otherwise noted. All variables and expressions represent real numbers unless otherwise noted."
  };

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  let bank = null;   // { meta, questions }
  let session = null;

  // ---------------------------------------------------------------- storage
  const loadHistory = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; } catch (e) { return []; }
  };
  const saveHistory = (h) => { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(h)); } catch (e) { /* private mode etc. */ } };
  const record = (entries) => { const h = loadHistory(); h.push(...entries); saveHistory(h); };

  // ---------------------------------------------------------------- views
  const show = (name) => {
    ["home", "practice", "results"].forEach((v) => { $("view-" + v).hidden = v !== name; });
    window.scrollTo(0, 0);
  };

  // ---------------------------------------------------------------- home
  const sectionName = (s) => (s === "all" ? "Both sections" : bank.meta.sections[s].name);

  const filtered = (f) => bank.questions.filter((q) =>
    (f.section === "all" || q.section === f.section) &&
    (f.domain === "all" || q.domain === f.domain) &&
    (f.difficulty === "all" || q.difficulty === f.difficulty));

  const readFilters = () => {
    const fd = new FormData($("bank-form"));
    return { section: fd.get("section"), domain: fd.get("domain"), difficulty: fd.get("difficulty") };
  };

  const fillDomains = () => {
    const f = readFilters();
    const sel = $("bank-form").elements.domain;
    const prev = sel.value;
    const secs = f.section === "all" ? Object.keys(bank.meta.sections) : [f.section];
    const domains = secs.flatMap((s) => bank.meta.sections[s].domains);
    sel.innerHTML = '<option value="all">All domains</option>' + domains.map((d) => `<option value="${esc(d)}">${esc(d)}</option>`).join("");
    if (domains.includes(prev)) sel.value = prev;
  };

  const updateCount = () => {
    const n = filtered(readFilters()).length;
    $("bank-count").textContent = `(${n})`;
    $("bank-form").querySelector("button").disabled = n === 0;
  };

  const moduleQuestions = (section) => bank.questions.filter((q) => q.section === section);
  const moduleSeconds = (section) => Math.round(moduleQuestions(section).length * SECONDS_PER_Q[section]);
  const fmtMin = (s) => `${Math.round(s / 60)} min`;

  const renderStats = () => {
    const h = loadHistory();
    const box = $("stats");
    if (!h.length) { box.hidden = true; return; }
    box.hidden = false;
    const byDomain = {};
    h.forEach((e) => {
      const d = byDomain[e.domain] || (byDomain[e.domain] = { n: 0, ok: 0, section: e.section });
      d.n++; if (e.correct) d.ok++;
    });
    const order = Object.keys(bank.meta.sections).flatMap((s) => bank.meta.sections[s].domains);
    const total = h.length, totalOk = h.filter((e) => e.correct).length;
    $("stats-grid").innerHTML =
      `<div class="stat"><div class="stat-label"><span>Overall</span><small>${totalOk}/${total} · ${Math.round(100 * totalOk / total)}%</small></div><div class="stat-bar"><i style="width:${100 * totalOk / total}%"></i></div></div>` +
      order.filter((d) => byDomain[d]).map((d) => {
        const s = byDomain[d]; const pct = Math.round(100 * s.ok / s.n);
        return `<div class="stat"><div class="stat-label"><span>${esc(d)}</span><small>${s.ok}/${s.n} · ${pct}%</small></div><div class="stat-bar"><i style="width:${pct}%"></i></div></div>`;
      }).join("");
  };

  const initHome = () => {
    fillDomains();
    updateCount();
    $("bank-form").elements.section.addEventListener("change", () => { fillDomains(); updateCount(); });
    $("bank-form").elements.domain.addEventListener("change", updateCount);
    $("bank-form").elements.difficulty.addEventListener("change", updateCount);
    $("bank-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const f = readFilters();
      startSession({ mode: "bank", section: f.section, questions: shuffle(filtered(f)), label: `${sectionName(f.section)}${f.domain !== "all" ? " · " + f.domain : ""}` });
    });
    ["rw", "math"].forEach((s) => {
      const qs = moduleQuestions(s);
      document.querySelector(`[data-meta="${s}"]`).textContent = `${qs.length} questions · ${fmtMin(moduleSeconds(s))}`;
    });
    document.querySelectorAll(".module-btn").forEach((b) => b.addEventListener("click", () => {
      const s = b.dataset.module;
      startSession({ mode: "test", section: s, questions: shuffle(moduleQuestions(s)), label: bank.meta.sections[s].name, seconds: moduleSeconds(s) });
    }));
    $("stats-reset").addEventListener("click", () => {
      if (confirm("Clear all saved progress in this browser?")) { saveHistory([]); renderStats(); }
    });
    renderStats();
  };

  const shuffle = (arr) => {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  };

  // ---------------------------------------------------------------- session
  const startSession = (opts) => {
    session = {
      mode: opts.mode,                       // "bank" | "test" | "review"
      section: opts.section,
      label: opts.label,
      questions: opts.questions,
      index: 0,
      answers: opts.answers || {},           // qid -> choice index | string
      marked: new Set(),
      eliminated: {},                        // qid -> Set of choice indexes
      checked: new Set(opts.checked || []),  // qids graded (bank + review)
      elimMode: false,
      seconds: opts.seconds || 0,
      remaining: opts.seconds || 0,
      timerHidden: false,
      timerId: null,
      startedAt: Date.now(),
      elapsed: opts.elapsed
    };
    const sec = session.section === "all" ? null : session.section;
    $("test-section").textContent = session.mode === "review" ? "Review · " + session.label : session.label;
    $("directions-text").textContent = sec ? DIRECTIONS[sec] : DIRECTIONS.rw + " " + DIRECTIONS.math;
    $("directions").hidden = true;
    $("btn-calc").hidden = sec === "rw";
    $("calc-panel").hidden = true;
    $("nav-pop").hidden = true;
    $("btn-check").hidden = session.mode !== "bank";
    $("timer").hidden = $("btn-timer-toggle").hidden = session.mode !== "test";
    if (session.mode === "test") startTimer();
    show("practice");
    renderQuestion();
  };

  const current = () => session.questions[session.index];
  const isSpr = (q) => q.type === "spr";
  const isAnswered = (q) => {
    const a = session.answers[q.id];
    return isSpr(q) ? typeof a === "string" && a.trim() !== "" : Number.isInteger(a);
  };
  const isCorrect = (q) => {
    const a = session.answers[q.id];
    if (isSpr(q)) return typeof a === "string" && normalizeSpr(a) === normalizeSpr(q.answer);
    return a === q.answer;
  };
  // "5", "5.0", " 5 ", "10/2" all count as 5. Keep it forgiving on format,
  // strict on value, which is how the real grid-in is scored.
  const normalizeSpr = (s) => {
    const t = String(s).trim().replace(/\s+/g, "");
    if (/^-?\d+\/\d+$/.test(t)) { const [n, d] = t.split("/").map(Number); return d ? String(+(n / d).toFixed(4)) : t; }
    const n = Number(t);
    return Number.isFinite(n) ? String(+n.toFixed(4)) : t;
  };

  // ---------------------------------------------------------------- render
  const renderPassage = (q) => {
    const left = $("pane-left");
    $("test-body").classList.toggle("math", q.section === "math");
    if (!q.passage) { left.classList.add("empty"); $("passage").innerHTML = ""; return; }
    left.classList.remove("empty");
    $("passage").innerHTML = esc(q.passage).replace(/^(Text [12])$/gm, "<strong>$1</strong>");
    left.scrollTop = 0;
  };

  const renderQuestion = () => {
    const q = current();
    const graded = session.checked.has(q.id);
    const n = session.index + 1, total = session.questions.length;
    renderPassage(q);
    $("q-num").textContent = n;
    $("nav-label").textContent = `Question ${n} of ${total}`;
    $("q-stem").textContent = q.stem;
    $("btn-mark").setAttribute("aria-pressed", session.marked.has(q.id));
    $("btn-elim").setAttribute("aria-pressed", session.elimMode);
    $("btn-elim").hidden = isSpr(q);
    $("test-body").classList.toggle("elim-mode", session.elimMode && !isSpr(q));

    const box = $("q-choices");
    if (isSpr(q)) {
      const a = session.answers[q.id] || "";
      box.innerHTML = `<div class="spr"><label for="spr-input">Enter your answer</label><input id="spr-input" type="text" inputmode="decimal" autocomplete="off" value="${esc(a)}" ${graded ? "disabled" : ""} class="${graded ? (isCorrect(q) ? "correct" : "wrong") : ""}">${graded ? `<div class="spr-answer">Correct answer: <strong>${esc(q.answer)}</strong></div>` : ""}</div>`;
      if (!graded) {
        const inp = $("spr-input");
        inp.addEventListener("input", () => { session.answers[q.id] = inp.value; syncButtons(); });
        inp.addEventListener("keydown", (e) => { if (e.key === "Enter") (session.mode === "bank" ? check : next)(); });
        inp.focus();
      }
    } else {
      const elim = session.eliminated[q.id] || new Set();
      box.innerHTML = q.choices.map((c, i) => {
        const sel = session.answers[q.id] === i;
        let cls = "choice";
        if (graded) { if (i === q.answer) cls += " correct"; else if (sel) cls += " wrong"; }
        else if (sel) cls += " selected";
        if (elim.has(i) && !graded) cls += " eliminated";
        return `<button type="button" class="${cls}" data-i="${i}" ${graded ? "disabled" : ""}><span class="choice-letter">${LETTERS[i]}</span><span class="choice-text">${esc(c)}</span><span class="elim-x" aria-hidden="true">${elim.has(i) ? "↺" : "×"}</span></button>`;
      }).join("");
      box.querySelectorAll(".choice").forEach((b) => b.addEventListener("click", (e) => {
        const i = +b.dataset.i;
        if (e.target.closest(".elim-x") || session.elimMode) {
          const set = session.eliminated[q.id] || (session.eliminated[q.id] = new Set());
          if (set.has(i)) set.delete(i); else { set.add(i); if (session.answers[q.id] === i) delete session.answers[q.id]; }
        } else {
          session.answers[q.id] = i;
          if (session.eliminated[q.id]) session.eliminated[q.id].delete(i);
        }
        renderQuestion();
      }));
    }

    const fb = $("q-feedback");
    if (graded) {
      const ok = isCorrect(q);
      const answered = isAnswered(q);
      fb.hidden = false;
      fb.className = "q-feedback " + (ok ? "correct" : "wrong");
      fb.innerHTML = `<strong>${ok ? "Correct." : answered ? "Not quite." : "Skipped."}</strong>${esc(q.explanation)}<div class="tag">${esc(q.domain)} · ${esc(q.skill)} · ${esc(q.difficulty)}</div>`;
    } else { fb.hidden = true; }
    syncButtons();
  };

  const syncButtons = () => {
    const q = current();
    const last = session.index === session.questions.length - 1;
    $("btn-back").disabled = session.index === 0;
    $("btn-check").disabled = !isAnswered(q) || session.checked.has(q.id);
    const nextBtn = $("btn-next");
    if (session.mode === "bank") {
      nextBtn.textContent = last ? "Finish" : "Next";
    } else if (session.mode === "test") {
      nextBtn.textContent = last ? "Review" : "Next";
    } else {
      nextBtn.textContent = last ? "Done" : "Next";
    }
  };

  // ---------------------------------------------------------------- actions
  const goTo = (i) => { session.index = Math.max(0, Math.min(session.questions.length - 1, i)); $("nav-pop").hidden = true; renderQuestion(); };

  const check = () => {
    const q = current();
    if (!isAnswered(q) || session.checked.has(q.id)) return;
    session.checked.add(q.id);
    record([{ qid: q.id, section: q.section, domain: q.domain, correct: isCorrect(q), ts: Date.now() }]);
    renderQuestion();
  };

  const next = () => {
    const last = session.index === session.questions.length - 1;
    if (session.mode === "bank") {
      // In the bank, moving on without checking still grades the item, so the
      // explanation is never skipped by accident.
      if (isAnswered(current()) && !session.checked.has(current().id)) { check(); return; }
      if (last) return finish();
    } else if (session.mode === "test" && last) {
      return finish();
    } else if (session.mode === "review" && last) {
      show("results"); return;
    }
    goTo(session.index + 1);
  };

  const finish = () => {
    if (session.mode === "test") {
      const unanswered = session.questions.filter((q) => !isAnswered(q)).length;
      if (unanswered && session.remaining > 0 && !confirm(`You have ${unanswered} unanswered question${unanswered > 1 ? "s" : ""}. Finish anyway?`)) return;
      stopTimer();
      session.elapsed = session.seconds - session.remaining;
      record(session.questions.map((q) => ({ qid: q.id, section: q.section, domain: q.domain, correct: isCorrect(q), ts: Date.now() })));
    }
    if (session.mode === "bank" && !session.elapsed) session.elapsed = Math.round((Date.now() - session.startedAt) / 1000);
    renderResults();
    show("results");
  };

  const exit = () => {
    if (session.mode === "review") { show("results"); return; }
    if (session.mode === "test" && !confirm("Leave this module? Your answers won't be scored.")) return;
    stopTimer();
    renderStats();
    show("home");
  };

  // ---------------------------------------------------------------- timer
  const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  const startTimer = () => {
    stopTimer();
    session.remaining = session.seconds;
    tick();
    session.timerId = setInterval(() => {
      session.remaining--;
      tick();
      if (session.remaining <= 0) { stopTimer(); alert("Time's up. Let's see how you did."); finish(); }
    }, 1000);
  };
  const stopTimer = () => { if (session && session.timerId) { clearInterval(session.timerId); session.timerId = null; } };
  const tick = () => {
    $("timer-text").textContent = fmtTime(Math.max(0, session.remaining));
    $("timer").classList.toggle("low", session.remaining <= 300);
    // Bluebook brings the clock back for the last five minutes no matter what.
    if (session.remaining <= 300 && session.timerHidden) { session.timerHidden = false; $("timer-text").hidden = false; $("btn-timer-toggle").textContent = "Hide"; }
  };

  // ---------------------------------------------------------------- nav popup
  const renderNav = () => {
    $("nav-pop-title").textContent = `${session.label} Questions`;
    $("nav-grid").innerHTML = session.questions.map((q, i) => {
      let cls = "nav-q";
      if (isAnswered(q)) cls += " answered";
      if (session.marked.has(q.id)) cls += " marked";
      if (i === session.index) cls += " current";
      return `<button type="button" class="${cls}" data-i="${i}">${i + 1}</button>`;
    }).join("");
    $("nav-grid").querySelectorAll(".nav-q").forEach((b) => b.addEventListener("click", () => goTo(+b.dataset.i)));
    $("btn-review").hidden = session.mode === "review";
    $("btn-review").textContent = session.mode === "test" ? "Go to Review Page" : "Finish";
  };

  // ---------------------------------------------------------------- results
  const renderResults = () => {
    const qs = session.questions;
    const ok = qs.filter(isCorrect).length;
    $("results-eyebrow").textContent = session.mode === "test" ? "Timed module" : "Question bank";
    $("results-title").textContent = session.label;
    $("score-pct").textContent = `${Math.round(100 * ok / qs.length)}%`;
    $("score-frac").textContent = `${ok} of ${qs.length} correct`;
    $("score-time").textContent = session.elapsed ? `Time: ${fmtTime(session.elapsed)}${session.mode === "test" ? ` of ${fmtTime(session.seconds)}` : ""}` : "";

    const by = {};
    qs.forEach((q) => { const d = by[q.domain] || (by[q.domain] = { n: 0, ok: 0 }); d.n++; if (isCorrect(q)) d.ok++; });
    $("domain-bars").innerHTML = Object.keys(by).map((d) => {
      const s = by[d]; const pct = Math.round(100 * s.ok / s.n);
      return `<div class="stat"><div class="stat-label"><span>${esc(d)}</span><small>${s.ok}/${s.n} · ${pct}%</small></div><div class="stat-bar"><i style="width:${pct}%"></i></div></div>`;
    }).join("");

    $("review-list").innerHTML = qs.map((q, i) => {
      const answered = isAnswered(q), correct = isCorrect(q);
      const a = session.answers[q.id];
      const yours = !answered ? "—" : isSpr(q) ? esc(a) : LETTERS[a];
      const right = isSpr(q) ? esc(q.answer) : LETTERS[q.answer];
      return `<li><button type="button" class="review-item" data-i="${i}"><span class="review-num ${correct ? "ok" : answered ? "no" : "skip"}">${i + 1}</span><span><span>${esc(q.stem.split("\n")[0]).slice(0, 110)}${q.stem.length > 110 ? "…" : ""}</span><div class="review-meta">${esc(q.domain)} · ${esc(q.difficulty)}</div></span><span class="review-ans">${correct ? "✓ " + right : `You: ${yours} · Correct: ${right}`}</span></button></li>`;
    }).join("");
    $("review-list").querySelectorAll(".review-item").forEach((b) => b.addEventListener("click", () => {
      const finished = session;
      startSession({ mode: "review", section: finished.section, label: finished.label, questions: finished.questions, answers: finished.answers, checked: finished.questions.map((q) => q.id), elapsed: finished.elapsed, seconds: finished.seconds });
      // Keep the finished session's results reachable from "Done"/"Exit".
      session.parent = finished;
      goTo(+b.dataset.i);
    }));
    $("btn-retry").onclick = () => {
      const s = session.parent || session;
      if (s.mode === "test") startSession({ mode: "test", section: s.section, questions: shuffle(s.questions), label: s.label, seconds: s.seconds });
      else startSession({ mode: "bank", section: s.section, questions: shuffle(s.questions), label: s.label });
    };
  };

  // ---------------------------------------------------------------- wiring
  const initPractice = () => {
    $("btn-back").addEventListener("click", () => goTo(session.index - 1));
    $("btn-next").addEventListener("click", next);
    $("btn-check").addEventListener("click", check);
    $("btn-exit").addEventListener("click", exit);
    $("btn-mark").addEventListener("click", () => {
      const q = current();
      if (session.marked.has(q.id)) session.marked.delete(q.id); else session.marked.add(q.id);
      renderQuestion();
    });
    $("btn-elim").addEventListener("click", () => { session.elimMode = !session.elimMode; renderQuestion(); });
    $("btn-directions").addEventListener("click", () => { $("directions").hidden = !$("directions").hidden; });
    $("btn-directions-close").addEventListener("click", () => { $("directions").hidden = true; });
    $("btn-nav").addEventListener("click", () => { const p = $("nav-pop"); p.hidden = !p.hidden; if (!p.hidden) renderNav(); });
    $("btn-nav-close").addEventListener("click", () => { $("nav-pop").hidden = true; });
    $("btn-review").addEventListener("click", () => { $("nav-pop").hidden = true; finish(); });
    $("btn-timer-toggle").addEventListener("click", () => {
      session.timerHidden = !session.timerHidden;
      $("timer-text").hidden = session.timerHidden;
      $("btn-timer-toggle").textContent = session.timerHidden ? "Show" : "Hide";
    });
    $("btn-calc").addEventListener("click", () => {
      const p = $("calc-panel");
      p.hidden = !p.hidden;
      // Loaded on first open only: no point pulling Desmos on a reading module.
      if (!p.hidden && !$("calc-frame").src) $("calc-frame").src = "https://www.desmos.com/calculator";
    });
    $("btn-calc-close").addEventListener("click", () => { $("calc-panel").hidden = true; });
    document.addEventListener("keydown", (e) => {
      if ($("view-practice").hidden || e.target.tagName === "INPUT") return;
      const q = current();
      if (!isSpr(q) && !session.checked.has(q.id) && /^[1-4]$/.test(e.key)) { session.answers[q.id] = +e.key - 1; renderQuestion(); }
      if (e.key === "ArrowRight" || e.key === "Enter") next();
      if (e.key === "ArrowLeft") goTo(session.index - 1);
      if (e.key === "Escape") { $("nav-pop").hidden = true; $("calc-panel").hidden = true; }
    });
    $("results-home").addEventListener("click", (e) => { e.preventDefault(); renderStats(); show("home"); });
    $("btn-results-home").addEventListener("click", () => { renderStats(); show("home"); });
  };

  // ---------------------------------------------------------------- boot
  fetch("data/questions.json")
    .then((r) => r.json())
    .then((data) => { bank = data; initHome(); initPractice(); })
    .catch((err) => {
      document.querySelector(".home").innerHTML = `<p class="lede">Couldn't load the question bank. ${esc(err.message)}</p>`;
    });
})();
