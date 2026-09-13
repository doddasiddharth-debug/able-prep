/* The practice screen (Bluebook vocabulary) and the results screen.
   Modes:
     bank        untimed, Check grades each item, explanation shown
     test        one section on the clock, graded at the end (module)
     diagnostic  like test but mixed sections, results add a score estimate
     rush        one question at a time against a per-question clock
     review      read-only walk through a finished session
   Practice.start(opts) takes over the screen; opts.onExit runs when the
   student leaves, so the app can route back to where they came from. */
window.Practice = (() => {
  "use strict";
  const LETTERS = ["A", "B", "C", "D"];
  const DIRECTIONS = {
    rw: "The questions in this section address a number of important reading and writing skills. Each question includes one or more passages, which may include a table or graph. Read each passage and question carefully, and then choose the best answer to the question based on the passage(s). All questions in this section are multiple-choice with four answer choices. Each question has a single best answer.",
    math: "The questions in this section address a number of important math skills. Use of a calculator is permitted for all questions. For multiple-choice questions, solve each problem and choose the correct answer from the choices provided. For student-produced response questions, solve each problem and enter your answer in the box. Figures are drawn to scale unless otherwise noted. All variables and expressions represent real numbers unless otherwise noted.",
    rush: "Answer each question before the timer runs out. The next question loads as soon as you answer."
  };
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  let S = null; // the live session

  // ---------------------------------------------------------------- helpers
  const current = () => S.questions[S.index];
  const isSpr = (q) => q.type === "spr";
  const isAnswered = (q) => { const a = S.answers[q.id]; return isSpr(q) ? typeof a === "string" && a.trim() !== "" : Number.isInteger(a); };
  // Forgiving on format, strict on value: "9", "9.0", " 9", "18/2" all match 9.
  const normalizeSpr = (s) => {
    const t = String(s).trim().replace(/\s+/g, "");
    if (/^-?\d+(\.\d+)?\/\d+(\.\d+)?$/.test(t)) { const [n, d] = t.split("/").map(Number); return d ? String(+(n / d).toFixed(4)) : t; }
    const n = Number(t);
    return Number.isFinite(n) ? String(+n.toFixed(4)) : t.toLowerCase();
  };
  const isCorrect = (q) => { const a = S.answers[q.id]; return isSpr(q) ? typeof a === "string" && normalizeSpr(a) === normalizeSpr(q.answer) : a === q.answer; };
  const stampTime = () => {
    // Accumulate seconds spent on the question currently on screen.
    if (S.shownAt != null) { const q = current(); S.times[q.id] = (S.times[q.id] || 0) + (Date.now() - S.shownAt) / 1000; }
    S.shownAt = Date.now();
  };
  const entry = (q) => ({ qid: q.id, section: q.section, domain: q.domain, skill: q.skill, difficulty: q.difficulty, correct: isCorrect(q), seconds: Math.round(S.times[q.id] || 0), mode: S.mode, ts: Date.now() });

  // ---------------------------------------------------------------- start
  const start = (opts) => {
    stopTimers();
    S = {
      mode: opts.mode, section: opts.section || "all", label: opts.label, questions: opts.questions, index: 0,
      answers: opts.answers || {}, marked: new Set(), eliminated: {}, checked: new Set(opts.checked || []),
      elimMode: false, seconds: opts.seconds || 0, remaining: opts.seconds || 0, pace: opts.pace || 0, qRemaining: 0,
      timerHidden: false, timerId: null, qTimerId: null, startedAt: Date.now(), shownAt: null, reviewing: false,
      times: opts.times || {}, elapsed: opts.elapsed || 0, onExit: opts.onExit || (() => {}), parent: opts.parent || null,
      studentName: (window.Store && Store.load().settings.name) || "ABLE Preps student"
    };
    const sec = S.section === "all" ? null : S.section;
    const isRush = S.mode === "rush", isTimed = S.mode === "test" || S.mode === "diagnostic";
    $("test-section").textContent = (S.mode === "review" ? "Review: " : "") + S.label;
    $("directions-text").textContent = isRush ? DIRECTIONS.rush : sec ? DIRECTIONS[sec] : DIRECTIONS.rw + " " + DIRECTIONS.math;
    $("directions").hidden = true;
    $("btn-calc").hidden = sec === "rw";
    $("calc-panel").hidden = true; $("nav-pop").hidden = true;
    $("review-page").hidden = true; $("test-body").hidden = false;
    $("btn-check").hidden = S.mode !== "bank";
    $("btn-mark").hidden = isRush;
    $("btn-back").hidden = isRush;
    $("btn-nav").hidden = isRush;
    $("timer").hidden = !(isTimed || isRush);
    $("btn-timer-toggle").hidden = !isTimed;
    $("timer-text").hidden = false; $("btn-timer-toggle").textContent = "Hide";
    $("student-name").textContent = S.studentName;
    $("rush-progress").hidden = !isRush;
    document.querySelectorAll(".view").forEach((v) => { v.hidden = v.id !== "view-practice"; });
    window.scrollTo(0, 0);
    if (isTimed) startTimer();
    renderQuestion();
  };

  // ---------------------------------------------------------------- render
  const renderPassage = (q) => {
    const left = $("pane-left");
    $("test-body").classList.toggle("math", q.section === "math");
    if (!q.passage) { left.classList.add("empty"); $("passage").innerHTML = ""; return; }
    left.classList.remove("empty");
    // Tables in passages are plain text blocks; keep their columns aligned.
    const html = esc(q.passage).replace(/^(Text [12])$/gm, "<strong>$1</strong>");
    $("passage").innerHTML = html;
    $("passage").classList.toggle("mono-table", /\n\S+\s{2,}\S+/.test(q.passage));
    left.scrollTop = 0;
  };

  const renderQuestion = () => {
    const q = current();
    stampTime();
    const graded = S.checked.has(q.id);
    const n = S.index + 1, total = S.questions.length;
    renderPassage(q);
    $("q-num").textContent = n;
    $("nav-label").textContent = `Question ${n} of ${total}`;
    $("rush-progress").textContent = `${n} / ${total}`;
    $("q-stem").textContent = q.stem;
    $("btn-mark").setAttribute("aria-pressed", S.marked.has(q.id));
    $("btn-elim").setAttribute("aria-pressed", S.elimMode);
    $("btn-elim").hidden = isSpr(q) || graded;
    $("test-body").classList.toggle("elim-mode", S.elimMode && !isSpr(q) && !graded);
    $("pane-right").scrollTop = 0;

    const box = $("q-choices");
    if (isSpr(q)) {
      const a = S.answers[q.id] || "";
      box.innerHTML = `<div class="spr"><label for="spr-input">Enter your answer</label><input id="spr-input" type="text" inputmode="text" autocomplete="off" spellcheck="false" value="${esc(a)}" ${graded ? "disabled" : ""} class="${graded ? (isCorrect(q) ? "correct" : "wrong") : ""}">${graded ? `<div class="spr-answer">Correct answer: <strong>${esc(q.answer)}</strong></div>` : '<div class="spr-answer">Fractions and decimals are both fine.</div>'}</div>`;
      if (!graded) {
        const inp = $("spr-input");
        inp.addEventListener("input", () => { S.answers[q.id] = inp.value; syncButtons(); });
        inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); if (S.mode === "bank") check(); else next(); } });
        inp.focus();
      }
    } else {
      const elim = S.eliminated[q.id] || new Set();
      box.innerHTML = q.choices.map((c, i) => {
        const sel = S.answers[q.id] === i;
        let cls = "choice";
        if (graded) { if (i === q.answer) cls += " correct"; else if (sel) cls += " wrong"; }
        else if (sel) cls += " selected";
        if (elim.has(i) && !graded) cls += " eliminated";
        return `<button type="button" class="${cls}" data-i="${i}" ${graded ? "disabled" : ""}><span class="choice-letter">${LETTERS[i]}</span><span class="choice-text">${esc(c)}</span><span class="elim-x" aria-hidden="true">${elim.has(i) ? "↺" : "×"}</span></button>`;
      }).join("");
      box.querySelectorAll(".choice").forEach((b) => b.addEventListener("click", (e) => {
        const i = +b.dataset.i;
        if (e.target.closest(".elim-x") || S.elimMode) {
          const set = S.eliminated[q.id] || (S.eliminated[q.id] = new Set());
          if (set.has(i)) set.delete(i); else { set.add(i); if (S.answers[q.id] === i) delete S.answers[q.id]; }
        } else {
          S.answers[q.id] = i;
          if (S.eliminated[q.id]) S.eliminated[q.id].delete(i);
          if (S.mode === "rush") { answerRush(); return; }
        }
        renderQuestion();
      }));
    }

    const fb = $("q-feedback");
    if (graded) {
      const ok = isCorrect(q), answered = isAnswered(q);
      fb.hidden = false;
      fb.className = "q-feedback " + (ok ? "correct" : "wrong");
      const t = S.times[q.id] ? `, ${Math.round(S.times[q.id])}s` : "";
      fb.innerHTML = `<strong>${ok ? "Correct" : answered ? "Incorrect" : "Skipped"}</strong>${esc(q.explanation)}<div class="tag">${esc(q.skill)}, ${esc(q.difficulty)}${t}</div>`;
    } else { fb.hidden = true; }
    if (S.mode === "rush") startQuestionClock();
    syncButtons();
  };

  const syncButtons = () => {
    const q = current();
    const last = S.index === S.questions.length - 1;
    if (S.reviewing) {
      $("btn-back").disabled = false;
      $("btn-next").textContent = "Submit";
      $("nav-label").textContent = "Review";
      return;
    }
    $("btn-back").disabled = S.index === 0;
    $("btn-check").disabled = !isAnswered(q) || S.checked.has(q.id);
    const labels = { bank: last ? "Finish" : "Next", test: last ? "Review" : "Next", diagnostic: last ? "Finish" : "Next", rush: "Skip", review: last ? "Done" : "Next" };
    $("btn-next").textContent = labels[S.mode];
  };

  // ---------------------------------------------------------------- actions
  const goTo = (i) => { stampTime(); S.index = Math.max(0, Math.min(S.questions.length - 1, i)); $("nav-pop").hidden = true; if (S.reviewing) hideReview(); renderQuestion(); };

  // Bluebook's "Check Your Work" page: the full question grid after the last
  // question, before the module is submitted. The clock keeps running.
  const showReview = () => {
    stampTime();
    S.shownAt = null; // time on the review page belongs to no question
    S.reviewing = true;
    $("nav-pop").hidden = true;
    $("test-body").hidden = true;
    $("btn-nav").hidden = true;
    $("review-page-title").textContent = `${S.label} Questions`;
    $("review-grid").innerHTML = navButtons();
    $("review-grid").querySelectorAll(".nav-q").forEach((b) => b.addEventListener("click", () => goTo(+b.dataset.i)));
    $("review-page").hidden = false;
    $("review-page").scrollTop = 0;
    syncButtons();
  };
  const hideReview = () => {
    S.reviewing = false;
    S.shownAt = Date.now();
    $("review-page").hidden = true;
    $("test-body").hidden = false;
    $("btn-nav").hidden = false;
  };
  const back = () => { if (S.reviewing) { goTo(S.index); return; } goTo(S.index - 1); };

  const check = () => {
    const q = current();
    if (!isAnswered(q) || S.checked.has(q.id)) return;
    stampTime();
    S.checked.add(q.id);
    Store.addHistory([entry(q)]);
    renderQuestion();
  };

  const next = () => {
    const last = S.index === S.questions.length - 1;
    if (S.reviewing) return finish();
    if (S.mode === "bank") {
      // Moving on without checking still grades the item, so the explanation
      // is never skipped by accident.
      if (isAnswered(current()) && !S.checked.has(current().id)) { check(); return; }
      if (last) return finish();
    } else if (S.mode === "rush") {
      return answerRush(); // "Skip": no answer recorded, clock stops, move on
    } else if ((S.mode === "test" || S.mode === "diagnostic") && last) {
      return showReview();
    } else if (S.mode === "review" && last) {
      return showResults();
    }
    goTo(S.index + 1);
  };

  const answerRush = () => {
    stopQuestionClock();
    stampTime();
    const q = current();
    S.checked.add(q.id);
    if (S.index === S.questions.length - 1) return finish();
    S.index++;
    renderQuestion();
  };

  const finish = () => {
    const isTimed = S.mode === "test" || S.mode === "diagnostic";
    if (isTimed) {
      const unanswered = S.questions.filter((q) => !isAnswered(q)).length;
      if (unanswered && S.remaining > 0 && !confirm(`You have ${unanswered} unanswered question${unanswered > 1 ? "s" : ""}. Finish anyway?`)) return;
    }
    stopTimers();
    stampTime();
    if (isTimed) S.elapsed = S.seconds - Math.max(0, S.remaining);
    else S.elapsed = Math.round((Date.now() - S.startedAt) / 1000);
    S.questions.forEach((q) => S.checked.add(q.id));
    if (S.mode !== "bank") Store.addHistory(S.questions.map(entry)); // bank recorded per Check
    const ok = S.questions.filter(isCorrect).length;
    S.stars = S.mode === "rush" ? S.questions.reduce((sum, q) => sum + starsFor(q), 0) : undefined;
    Store.addAttempt({ mode: S.mode, section: S.section, label: S.label, ts: Date.now(), n: S.questions.length, correct: ok, seconds: S.elapsed, stars: S.stars });
    S.finished = true;
    showResults();
  };

  const starsFor = (q) => {
    if (!isCorrect(q)) return 0;
    const t = S.times[q.id] || S.pace;
    return t <= S.pace * 0.5 ? 3 : t <= S.pace ? 2 : 1;
  };

  const exit = () => {
    if (S.mode === "review") return showResults();
    if ((S.mode === "test" || S.mode === "diagnostic" || S.mode === "rush") && !confirm("Leave now? This session won't be scored.")) return;
    stopTimers();
    const cb = S.onExit; S = null;
    cb();
  };

  // ---------------------------------------------------------------- timers
  const startTimer = () => {
    S.remaining = S.seconds; tick();
    S.timerId = setInterval(() => {
      S.remaining--; tick();
      if (S.remaining <= 0) { stopTimers(); alert("Time is up."); finish(); }
    }, 1000);
  };
  const tick = () => {
    $("timer-text").textContent = fmtTime(Math.max(0, S.remaining));
    $("timer").classList.toggle("low", S.remaining <= 300);
    // Bluebook brings the clock back for the last five minutes regardless.
    if (S.remaining <= 300 && S.timerHidden) { S.timerHidden = false; $("timer-text").hidden = false; $("btn-timer-toggle").textContent = "Hide"; }
  };
  const startQuestionClock = () => {
    stopQuestionClock();
    S.qRemaining = S.pace;
    const draw = () => { $("timer-text").textContent = `${S.qRemaining}s`; $("timer").classList.toggle("low", S.qRemaining <= 5); };
    draw();
    S.qTimerId = setInterval(() => {
      S.qRemaining--; draw();
      if (S.qRemaining <= 0) answerRush();
    }, 1000);
  };
  const stopQuestionClock = () => { if (S && S.qTimerId) { clearInterval(S.qTimerId); S.qTimerId = null; } };
  const stopTimers = () => { if (S && S.timerId) { clearInterval(S.timerId); S.timerId = null; } stopQuestionClock(); };

  // ---------------------------------------------------------------- nav popup
  const navButtons = () => S.questions.map((q, i) => {
    let cls = "nav-q";
    if (isAnswered(q)) cls += " answered";
    if (S.marked.has(q.id)) cls += " marked";
    if (i === S.index && !S.reviewing) cls += " current";
    return `<button type="button" class="${cls}" data-i="${i}">${i + 1}</button>`;
  }).join("");
  const renderNav = () => {
    $("nav-pop-title").textContent = `${S.label} Questions`;
    $("nav-grid").innerHTML = navButtons();
    $("nav-grid").querySelectorAll(".nav-q").forEach((b) => b.addEventListener("click", () => goTo(+b.dataset.i)));
    $("btn-review").hidden = S.mode === "review";
    $("btn-review").textContent = S.mode === "bank" ? "Finish" : "Go to Review Page";
  };

  // ---------------------------------------------------------------- results
  const showResults = () => {
    const s = S.parent || S;
    renderResults(s);
    document.querySelectorAll(".view").forEach((v) => { v.hidden = v.id !== "view-results"; });
    window.scrollTo(0, 0);
  };

  const renderResults = (s) => {
    const qs = s.questions;
    const correctOf = (q) => { const a = s.answers[q.id]; return isSpr(q) ? typeof a === "string" && normalizeSpr(a) === normalizeSpr(q.answer) : a === q.answer; };
    const answeredOf = (q) => { const a = s.answers[q.id]; return isSpr(q) ? typeof a === "string" && a.trim() !== "" : Number.isInteger(a); };
    const ok = qs.filter(correctOf).length;
    const names = { bank: "Question bank", test: "Practice test", diagnostic: "Diagnostic", rush: "Question Rush" };
    $("results-eyebrow").textContent = names[s.mode] || "Session";
    $("results-title").textContent = s.label;
    $("score-pct").textContent = `${Math.round(100 * ok / qs.length)}%`;
    $("score-frac").textContent = `${ok} of ${qs.length} correct`;
    $("score-time").textContent = s.elapsed ? `${fmtTime(s.elapsed)}${s.mode === "test" || s.mode === "diagnostic" ? ` of ${fmtTime(s.seconds)}` : ""}` : "";

    // Estimate card: modules get a section estimate, the diagnostic a total.
    const est = $("score-estimate");
    if (s.mode === "test" && s.section !== "all") {
      est.hidden = false;
      est.innerHTML = `<div class="est-num">${Scoring.scaled(s.section, ok / qs.length)}</div><div class="est-label">Estimated ${esc(s.label)} score<br><small>200 to 800</small></div>`;
    } else if (s.mode === "diagnostic") {
      const rw = qs.filter((q) => q.section === "rw"), m = qs.filter((q) => q.section === "math");
      const rwS = Scoring.scaled("rw", rw.filter(correctOf).length / rw.length), mS = Scoring.scaled("math", m.filter(correctOf).length / m.length);
      est.hidden = false;
      est.innerHTML = `<div class="est-num">${rwS + mS}</div><div class="est-label">Estimated total<br><small>Reading and Writing ${rwS}, Math ${mS}</small></div>`;
    } else if (s.mode === "rush") {
      const stars = s.stars || 0, max = qs.length * 3;
      const avg = qs.reduce((a, q) => a + (s.times[q.id] || 0), 0) / qs.length;
      est.hidden = false;
      est.innerHTML = `<div class="est-num">${"★".repeat(Math.min(3, Math.round(3 * stars / max)))}<span class="est-dim">${"★".repeat(3 - Math.min(3, Math.round(3 * stars / max)))}</span></div><div class="est-label">${stars} of ${max} stars<br><small>${avg.toFixed(1)}s average per question</small></div>`;
    } else { est.hidden = true; }

    const by = {};
    qs.forEach((q) => { const d = by[q.domain] || (by[q.domain] = { n: 0, ok: 0 }); d.n++; if (correctOf(q)) d.ok++; });
    $("domain-bars").innerHTML = Object.keys(by).map((d) => {
      const r = by[d]; const pct = Math.round(100 * r.ok / r.n);
      return `<div class="stat"><div class="stat-label"><span>${esc(d)}</span><small>${r.ok}/${r.n}</small></div><div class="stat-bar"><i style="width:${pct}%"></i></div></div>`;
    }).join("");

    $("review-list").innerHTML = qs.map((q, i) => {
      const answered = answeredOf(q), correct = correctOf(q);
      const a = s.answers[q.id];
      const yours = !answered ? "-" : isSpr(q) ? esc(a) : LETTERS[a];
      const right = isSpr(q) ? esc(q.answer) : LETTERS[q.answer];
      const t = s.times[q.id] ? `${Math.round(s.times[q.id])}s` : "";
      return `<li><button type="button" class="review-item" data-i="${i}"><span class="review-num ${correct ? "ok" : answered ? "no" : "skip"}">${i + 1}</span><span><span>${esc(q.stem.split("\n")[0]).slice(0, 110)}${q.stem.length > 110 ? "…" : ""}</span><div class="review-meta">${esc(q.skill)}${t ? ", " + t : ""}</div></span><span class="review-ans">${correct ? right : `${yours} / ${right}`}</span></button></li>`;
    }).join("");
    $("review-list").querySelectorAll(".review-item").forEach((b) => b.addEventListener("click", () => {
      start({ mode: "review", section: s.section, label: s.label, questions: s.questions, answers: s.answers, checked: s.questions.map((q) => q.id), times: s.times, elapsed: s.elapsed, seconds: s.seconds, pace: s.pace, onExit: s.onExit, parent: s });
      S.stars = s.stars;
      goTo(+b.dataset.i);
    }));
    $("btn-retry").onclick = () => {
      const opts = { mode: s.mode, section: s.section, label: s.label, questions: shuffle(s.questions), seconds: s.seconds, pace: s.pace, onExit: s.onExit };
      start(opts);
    };
    $("btn-results-home").onclick = () => { const cb = s.onExit; S = null; cb(); };
  };

  const shuffle = (arr) => { const a = arr.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

  // ---------------------------------------------------------------- wiring
  const init = () => {
    $("btn-back").addEventListener("click", back);
    $("btn-next").addEventListener("click", next);
    $("btn-check").addEventListener("click", check);
    $("btn-exit").addEventListener("click", exit);
    $("btn-mark").addEventListener("click", () => { const q = current(); if (S.marked.has(q.id)) S.marked.delete(q.id); else S.marked.add(q.id); renderQuestion(); });
    $("btn-elim").addEventListener("click", () => { S.elimMode = !S.elimMode; renderQuestion(); });
    $("btn-directions").addEventListener("click", () => { $("directions").hidden = !$("directions").hidden; });
    $("btn-directions-close").addEventListener("click", () => { $("directions").hidden = true; });
    $("btn-nav").addEventListener("click", () => { const p = $("nav-pop"); p.hidden = !p.hidden; if (!p.hidden) renderNav(); });
    $("btn-nav-close").addEventListener("click", () => { $("nav-pop").hidden = true; });
    $("btn-review").addEventListener("click", () => { $("nav-pop").hidden = true; if (S.mode === "test" || S.mode === "diagnostic") showReview(); else finish(); });
    $("btn-timer-toggle").addEventListener("click", () => { S.timerHidden = !S.timerHidden; $("timer-text").hidden = S.timerHidden; $("btn-timer-toggle").textContent = S.timerHidden ? "Show" : "Hide"; });
    $("btn-calc").addEventListener("click", () => { const p = $("calc-panel"); p.hidden = !p.hidden; if (!p.hidden && !$("calc-frame").src) $("calc-frame").src = "https://www.desmos.com/calculator"; });
    $("btn-calc-close").addEventListener("click", () => { $("calc-panel").hidden = true; });
    initCalcPanel();
    document.addEventListener("keydown", (e) => {
      if (!S || $("view-practice").hidden) return;
      const tag = e.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      const q = current();
      if (!S.reviewing && !isSpr(q) && !S.checked.has(q.id) && /^[1-4]$/.test(e.key)) { S.answers[q.id] = +e.key - 1; if (S.mode === "rush") answerRush(); else renderQuestion(); return; }
      // Enter on a focused button already fires its click; only bare Enter advances.
      if ((e.key === "ArrowRight") || (e.key === "Enter" && tag !== "BUTTON")) { e.preventDefault(); next(); }
      if (e.key === "ArrowLeft" && S.mode !== "rush") back();
      if (e.key === "Escape") { $("nav-pop").hidden = true; $("calc-panel").hidden = true; }
    });
  };

  // The calculator floats like Bluebook's: drag it by the header, resize from
  // the corner, or expand it to fill the screen. Pointer events with capture,
  // so a fast drag that leaves the header still tracks; the shield covers the
  // iframe during a move because an iframe eats pointer events it receives.
  const initCalcPanel = () => {
    const panel = $("calc-panel"), head = $("calc-head"), grip = $("calc-resize");
    const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
    const pin = () => {
      // Convert the CSS-positioned default (right/top) into explicit left/top
      // and size, so subsequent moves are simple arithmetic.
      const r = panel.getBoundingClientRect();
      panel.style.left = r.left + "px"; panel.style.top = r.top + "px";
      panel.style.right = "auto"; panel.style.width = r.width + "px"; panel.style.height = r.height + "px";
    };
    let drag = null;
    head.addEventListener("pointerdown", (e) => {
      if (e.target.closest("button") || panel.classList.contains("max")) return;
      pin();
      const r = panel.getBoundingClientRect();
      drag = { dx: e.clientX - r.left, dy: e.clientY - r.top };
      head.setPointerCapture(e.pointerId);
      panel.classList.add("moving");
    });
    head.addEventListener("pointermove", (e) => {
      if (!drag) return;
      panel.style.left = clamp(e.clientX - drag.dx, 0, innerWidth - panel.offsetWidth) + "px";
      panel.style.top = clamp(e.clientY - drag.dy, 0, innerHeight - panel.offsetHeight) + "px";
    });
    const endDrag = () => { drag = null; panel.classList.remove("moving"); };
    head.addEventListener("pointerup", endDrag);
    head.addEventListener("pointercancel", endDrag);
    head.addEventListener("dblclick", (e) => { if (!e.target.closest("button")) toggleMax(); });

    let rs = null;
    grip.addEventListener("pointerdown", (e) => {
      pin();
      const r = panel.getBoundingClientRect();
      rs = { x: e.clientX, y: e.clientY, w: r.width, h: r.height, left: r.left, top: r.top };
      grip.setPointerCapture(e.pointerId);
      panel.classList.add("moving");
      e.preventDefault();
    });
    grip.addEventListener("pointermove", (e) => {
      if (!rs) return;
      panel.style.width = clamp(rs.w + (e.clientX - rs.x), Math.min(320, innerWidth - 32), innerWidth - rs.left) + "px";
      panel.style.height = clamp(rs.h + (e.clientY - rs.y), Math.min(280, innerHeight - 152), innerHeight - rs.top) + "px";
    });
    const endResize = () => { rs = null; panel.classList.remove("moving"); };
    grip.addEventListener("pointerup", endResize);
    grip.addEventListener("pointercancel", endResize);

    const toggleMax = () => {
      const on = panel.classList.toggle("max");
      $("btn-calc-max").textContent = on ? "⤡" : "⤢";
      $("btn-calc-max").setAttribute("aria-label", on ? "Restore calculator size" : "Expand calculator");
      $("btn-calc-max").title = on ? "Restore" : "Expand";
    };
    $("btn-calc-max").addEventListener("click", toggleMax);
    // If the window shrinks under a pinned panel, pull it back on screen.
    window.addEventListener("resize", () => {
      if (panel.hidden || !panel.style.left) return;
      panel.style.left = clamp(parseFloat(panel.style.left), 0, Math.max(0, innerWidth - panel.offsetWidth)) + "px";
      panel.style.top = clamp(parseFloat(panel.style.top), 0, Math.max(0, innerHeight - panel.offsetHeight)) + "px";
    });
  };

  return { start, init, shuffle, normalizeSpr };
})();
