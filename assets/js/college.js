/* College tools: college list, scholarship tracker, application timeline,
   aid offer comparison and essay checker. app.js calls College.register()
   with its page table and helpers before the first render; everything saves
   through Store (so it syncs with an account like the rest of progress).
   Nothing here states a year-specific date, price or rate: students enter
   their own numbers, and the guidance points to official sources. */
window.College = (() => {
  "use strict";

  const uid = () => "c" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const money = (x) => "$" + Math.round(x).toLocaleString("en-US");
  const daysUntil = (d) => (d ? Math.ceil((new Date(d + "T00:00") - new Date(new Date().toDateString())) / 86400000) : null);
  const fmtDay = (d) => new Date(d + "T00:00").toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  const safeUrl = (u) => (/^https?:\/\/[^\s"<>]+$/i.test(u || "") ? u : "");
  const dueText = (d) => {
    const n = daysUntil(d);
    if (n === null) return "No deadline set";
    if (n < 0) return `${fmtDay(d)} · passed`;
    return `${fmtDay(d)} · ${n === 0 ? "today" : n === 1 ? "tomorrow" : `${n} days`}`;
  };

  const ICONS = {
    colleges: '<path d="M3 9.5 12 4l9 5.5"/><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18"/>',
    scholarships: '<circle cx="12" cy="9" r="5.5"/><path d="M12 6.5v5M10 8h3a1 1 0 0 1 0 2h-2a1 1 0 0 0 0 2h3"/><path d="M8.5 14 7 21l5-2.5 5 2.5-1.5-7"/>',
    timeline: '<path d="M8 6h12M8 12h12M8 18h12"/><path d="m3 6 1 1 2-2M3 12l1 1 2-2M3 18l1 1 2-2"/>',
    aid: '<path d="M12 4v16M7 20h10M4 7h16"/><path d="M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z" stroke-linejoin="round"/>',
    essay: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 12h7M9 16h7"/>'
  };

  // ---------------------------------------------------------------- timeline
  // Months and deadlines vary by college and by year, so items say "often"
  // and point to where the real date lives.
  const TIMELINE = [
    { id: "jr-fall", title: "Junior year · fall", items: [
      ["jf1", "Take the PSAT/NMSQT", "It's practice for the SAT and the qualifying test for National Merit scholarships."],
      ["jf2", "Meet your school counselor about your plans", "Ask what your school offers: college nights, fee waivers, scholarship lists."],
      ["jf3", "Start a college list", "Anything that interests you. Use the College list tool to sort it later."]] },
    { id: "jr-spring", title: "Junior year · winter and spring", items: [
      ["js1", "Pick your SAT dates and take the SAT", "Leave time for a retake in late summer or fall."],
      ["js2", "Visit campuses, in person or virtually", "Take notes on what you liked while it's fresh."],
      ["js3", "Ask two teachers for recommendation letters", "Before summer, so they aren't writing twenty in October."],
      ["js4", "Start tracking scholarships", "Many have deadlines long before senior spring."]] },
    { id: "summer", title: "Summer before senior year", items: [
      ["su1", "Draft your personal essay", "Use the Essay checker for word count and overused words."],
      ["su2", "Settle on a balanced college list", "Some reach, some target, and at least a couple of likely schools you'd be happy at."],
      ["su3", "Create your application accounts", "Many application platforms open in late summer."],
      ["su4", "Retake the SAT if you want a higher score", ""]] },
    { id: "sr-fall", title: "Senior year · fall", items: [
      ["sf1", "Confirm every college's deadlines and requirements", "Check each college's admissions site: they vary."],
      ["sf2", "Send test scores and request your transcripts", ""],
      ["sf3", "Submit early applications", "Early deadlines are often in November. Early Decision is binding."],
      ["sf4", "Submit the FAFSA as soon as it opens", "Plus the CSS Profile if a college asks for it. Dates are on StudentAid.gov."],
      ["sf5", "Apply for scholarships", ""]] },
    { id: "sr-winter", title: "Senior year · winter", items: [
      ["sw1", "Submit regular decision applications", "Deadlines are often in January."],
      ["sw2", "Send mid-year grades if a college asks", ""],
      ["sw3", "Check your application portals and email", "Colleges ask for missing documents there."]] },
    { id: "sr-spring", title: "Senior year · spring", items: [
      ["sp1", "Compare your financial aid offers", "The Aid offers tool puts them side by side."],
      ["sp2", "Decide, and pay your deposit by the deadline", "May 1 at many colleges."],
      ["sp3", "Send your final transcript and thank your recommenders", ""]] }
  ];

  const STATUSES = ["Researching", "Applying", "Submitted", "Accepted", "Waitlisted", "Not admitted"];
  const PLANS = ["Regular Decision", "Early Action", "Early Decision", "Rolling"];
  const SCH_STATUSES = ["Not started", "In progress", "Submitted", "Won", "Not selected"];

  // Reach / target / likely from the student's score against the middle 50%
  // of admitted students. Very selective colleges are a reach for everyone.
  const fit = (c, score) => {
    if (c.admitRate !== "" && c.admitRate !== undefined && +c.admitRate < 20) return { k: "reach", label: "Reach", why: "Admit rate under 20%: a reach whatever your scores" };
    if (!score || !c.sat25 || !c.sat75) return { k: "none", label: "Add scores", why: "Add the college's SAT range to sort it" };
    if (score < +c.sat25) return { k: "reach", label: "Reach", why: `Your ${score} is below their middle 50% (${c.sat25}–${c.sat75})` };
    if (score > +c.sat75) return { k: "likely", label: "Likely", why: `Your ${score} is above their middle 50% (${c.sat25}–${c.sat75})` };
    return { k: "target", label: "Target", why: `Your ${score} is inside their middle 50% (${c.sat25}–${c.sat75})` };
  };

  const register = (h) => {
    const { PAGES, ROUTES, ICON, pageHead, esc, $, render } = h;
    Object.assign(ICON, ICONS);
    ROUTES.push("colleges", "scholarships", "timeline", "aid", "essay");
    const opts = (list, cur) => list.map((x) => `<option${x === cur ? " selected" : ""}>${esc(x)}</option>`).join("");
    const col = () => Store.college();

    // ---- College list --------------------------------------------------
    PAGES.colleges = () => {
      const st = Store.load(), data = col();
      const pred = window.Scoring ? Scoring.predict(st.history).total : null;
      const score = +data.myScore || pred || 0;
      const list = [...data.colleges].sort((a, b) => (a.deadline || "9999").localeCompare(b.deadline || "9999"));
      const fits = list.map((c) => fit(c, score));
      const count = (k) => fits.filter((f) => f.k === k).length;
      const editing = list.find((c) => c.id === location.hash.split("?edit=")[1]);
      const e = editing || {};
      $("page").innerHTML = `
        ${pageHead("colleges", "College list", "Keep every college you're considering in one place, with deadlines, and see which are reach, target and likely schools for you.")}
        <div class="two-col">
          <section class="card">
            <h2>${editing ? "Edit college" : "Add a college"}</h2>
            <form id="col-form" class="filters">
              <label>College name<input type="text" name="name" required maxlength="80" value="${esc(e.name || "")}"></label>
              <div class="filters filters-row">
                <label>SAT 25th percentile<input type="number" name="sat25" min="400" max="1600" step="10" value="${esc(e.sat25 || "")}" placeholder="e.g. 1250"></label>
                <label>SAT 75th percentile<input type="number" name="sat75" min="400" max="1600" step="10" value="${esc(e.sat75 || "")}" placeholder="e.g. 1420"></label>
                <label>Admit rate (%)<input type="number" name="admitRate" min="0" max="100" step="0.1" value="${esc(e.admitRate ?? "")}" placeholder="optional"></label>
              </div>
              <div class="filters filters-row">
                <label>Application plan<select name="plan">${opts(PLANS, e.plan)}</select></label>
                <label>Deadline<input type="date" name="deadline" value="${esc(e.deadline || "")}"></label>
                <label>Status<select name="status">${opts(STATUSES, e.status)}</select></label>
              </div>
              <label>Notes<input type="text" name="notes" maxlength="200" value="${esc(e.notes || "")}" placeholder="Majors, visit dates, what you liked"></label>
              <div class="row-actions"><button type="submit" class="btn btn-primary">${editing ? "Save changes" : "Add college"}</button>${editing ? `<a class="btn-text" href="#/colleges">Cancel</a>` : ""}</div>
            </form>
            <p class="fine" style="margin-top:14px">Find a college's SAT range and admit rate on its admissions site, its Common Data Set, or the US Department of Education's <a href="https://collegescorecard.ed.gov/" target="_blank" rel="noopener">College Scorecard</a>. The middle 50% means a quarter of admitted students scored below the 25th percentile and a quarter above the 75th.</p>
          </section>
          <section class="card">
            <h2>Your list</h2>
            <form id="score-form" class="filters filters-row" style="margin-bottom:16px">
              <label>Your SAT score for sorting<input type="number" name="myScore" min="400" max="1600" step="10" value="${esc(data.myScore || "")}" placeholder="${pred ? `predicted ${pred}` : "e.g. 1300"}"></label>
            </form>
            <div class="fit-sum">
              <div class="fit-box reach"><strong>${count("reach")}</strong><span>Reach</span></div>
              <div class="fit-box target"><strong>${count("target")}</strong><span>Target</span></div>
              <div class="fit-box likely"><strong>${count("likely")}</strong><span>Likely</span></div>
            </div>
            <p class="fine">${list.length ? (count("likely") < 2 ? "A balanced list usually includes at least a couple of likely schools you'd be happy to attend." : "Scores are one factor among many: grades, courses, essays and activities count too.") : "Add colleges to see how your list balances."}${score ? "" : " Enter your score (or take the diagnostic) to sort them."}</p>
          </section>
        </div>
        ${list.length ? `<section class="card"><div class="table-scroll"><table class="table col-table">
          <thead><tr><th>College</th><th>Fit</th><th>Plan and deadline</th><th>Status</th><th></th></tr></thead>
          <tbody>${list.map((c, i) => `<tr>
            <td><strong>${esc(c.name)}</strong>${c.notes ? `<div class="fine">${esc(c.notes)}</div>` : ""}</td>
            <td><span class="fit-tag ${fits[i].k}" title="${esc(fits[i].why)}">${fits[i].label}</span><div class="fine">${esc(fits[i].why)}</div></td>
            <td>${esc(c.plan || "")}${c.plan === "Early Decision" ? ` <span class="fine">(binding)</span>` : ""}<div class="fine ${daysUntil(c.deadline) !== null && daysUntil(c.deadline) >= 0 && daysUntil(c.deadline) <= 14 ? "warn-text" : ""}">${dueText(c.deadline)}</div></td>
            <td><select class="inline-select" data-status="${c.id}" aria-label="Status for ${esc(c.name)}">${opts(STATUSES, c.status)}</select></td>
            <td><div class="row-actions"><a class="btn-text" href="#/colleges?edit=${c.id}">Edit</a><button type="button" class="btn-text" data-del="${c.id}">Remove</button></div></td>
          </tr>`).join("")}</tbody></table></div></section>` : ""}`;

      $("col-form").addEventListener("submit", (ev) => {
        ev.preventDefault();
        const fd = new FormData(ev.target), rec = { id: e.id || uid(), updated: Date.now() };
        ["name", "sat25", "sat75", "admitRate", "plan", "deadline", "status", "notes"].forEach((k) => { rec[k] = String(fd.get(k) || "").trim(); });
        if (!rec.name) return;
        Store.upsert("colleges", rec);
        if (editing) location.hash = "#/colleges"; else render();
      });
      $("score-form").addEventListener("change", (ev) => { Store.setCollege({ myScore: ev.target.value }); render(); });
      document.querySelectorAll("[data-status]").forEach((s) => s.addEventListener("change", () => { const c = data.colleges.find((x) => x.id === s.dataset.status); Store.upsert("colleges", { ...c, status: s.value, updated: Date.now() }); }));
      document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => { if (confirm("Remove this college from your list?")) { Store.remove("colleges", b.dataset.del); render(); } }));
    };

    // ---- Scholarships -------------------------------------------------
    PAGES.scholarships = () => {
      const data = col();
      const list = [...data.scholarships].sort((a, b) => (a.deadline || "9999").localeCompare(b.deadline || "9999"));
      const live = list.filter((s) => s.status !== "Not selected");
      const won = list.filter((s) => s.status === "Won").reduce((t, s) => t + (+s.amount || 0), 0);
      const possible = live.reduce((t, s) => t + (+s.amount || 0), 0);
      const next = list.find((s) => !["Submitted", "Won", "Not selected"].includes(s.status) && daysUntil(s.deadline) !== null && daysUntil(s.deadline) >= 0);
      const editing = list.find((s) => s.id === location.hash.split("?edit=")[1]);
      const e = editing || {};
      const need = (k) => (e.needs || []).includes(k);
      $("page").innerHTML = `
        ${pageHead("scholarships", "Scholarship tracker", "Every scholarship you're applying for, what each one needs, and what's due next.")}
        <div class="stat-row">
          <div class="card mini"><span class="fine">Applying for</span><strong>${money(possible)}</strong><span class="fine">${live.length} scholarship${live.length === 1 ? "" : "s"}</span></div>
          <div class="card mini"><span class="fine">Won so far</span><strong class="good">${money(won)}</strong><span class="fine">${list.filter((s) => s.status === "Won").length} won</span></div>
          <div class="card mini"><span class="fine">Next deadline</span><strong>${next ? esc(next.name) : "None"}</strong><span class="fine">${next ? dueText(next.deadline) : "Nothing open"}</span></div>
        </div>
        <div class="two-col">
          <section class="card">
            <h2>${editing ? "Edit scholarship" : "Add a scholarship"}</h2>
            <form id="sch-form" class="filters">
              <label>Name<input type="text" name="name" required maxlength="100" value="${esc(e.name || "")}"></label>
              <div class="filters filters-row">
                <label>Amount ($)<input type="number" name="amount" min="0" step="50" value="${esc(e.amount || "")}"></label>
                <label>Deadline<input type="date" name="deadline" value="${esc(e.deadline || "")}"></label>
                <label>Status<select name="status">${opts(SCH_STATUSES, e.status)}</select></label>
              </div>
              <fieldset class="checks"><legend>It needs</legend>
                ${[["essay", "An essay"], ["rec", "Recommendation letter"], ["transcript", "Transcript"], ["fafsa", "FAFSA"], ["interview", "Interview"]].map(([k, l]) => `<label><input type="checkbox" name="needs" value="${k}"${need(k) ? " checked" : ""}> ${l}</label>`).join("")}
                <label><input type="checkbox" name="renewable"${e.renewable ? " checked" : ""}> Renewable each year</label>
              </fieldset>
              <label>Link<input type="text" name="link" maxlength="300" value="${esc(e.link || "")}" placeholder="https://"></label>
              <div class="row-actions"><button type="submit" class="btn btn-primary">${editing ? "Save changes" : "Add scholarship"}</button>${editing ? `<a class="btn-text" href="#/scholarships">Cancel</a>` : ""}</div>
            </form>
          </section>
          <section class="card">
            <h2>Where to look</h2>
            <ul class="ticks">
              <li>Your school counselor, who often has a list of local awards</li>
              <li>Local groups: community foundations, clubs, employers and places of worship</li>
              <li>Each college's financial aid office, and your state's higher-education agency</li>
              <li>Free search tools, like the US Department of Labor's <a href="https://www.careeronestop.org/toolkit/training/find-scholarships.aspx" target="_blank" rel="noopener">CareerOneStop scholarship finder</a></li>
            </ul>
            <h2>Scam red flags</h2>
            <ul class="flags">
              <li>You have to pay to apply, or pay a fee to collect a prize</li>
              <li>It's "guaranteed," or you "won" one you never applied for</li>
              <li>It asks for a bank account or card number to hold the award</li>
            </ul>
            <p class="fine">Real scholarships don't charge you. The FTC's advice: <a href="https://consumer.ftc.gov/articles/how-avoid-scholarship-and-financial-aid-scams" target="_blank" rel="noopener">consumer.ftc.gov</a>. Tip: many essay prompts overlap, so one strong essay can often be adapted for several.</p>
          </section>
        </div>
        ${list.length ? `<section class="card"><div class="table-scroll"><table class="table col-table">
          <thead><tr><th>Scholarship</th><th>Amount</th><th>Deadline</th><th>Needs</th><th>Status</th><th></th></tr></thead>
          <tbody>${list.map((s) => `<tr class="${s.status === "Not selected" ? "row-dim" : ""}">
            <td><strong>${safeUrl(s.link) ? `<a href="${esc(safeUrl(s.link))}" target="_blank" rel="noopener">${esc(s.name)}</a>` : esc(s.name)}</strong>${s.renewable ? `<div class="fine">Renewable</div>` : ""}</td>
            <td>${s.amount ? money(+s.amount) : "—"}</td>
            <td class="${daysUntil(s.deadline) !== null && daysUntil(s.deadline) >= 0 && daysUntil(s.deadline) <= 14 && !["Submitted", "Won", "Not selected"].includes(s.status) ? "warn-text" : ""}">${dueText(s.deadline)}</td>
            <td class="fine">${(s.needs || []).map((k) => ({ essay: "Essay", rec: "Recommendation", transcript: "Transcript", fafsa: "FAFSA", interview: "Interview" }[k])).join(", ") || "—"}</td>
            <td><select class="inline-select" data-sstatus="${s.id}" aria-label="Status for ${esc(s.name)}">${opts(SCH_STATUSES, s.status)}</select></td>
            <td><div class="row-actions"><a class="btn-text" href="#/scholarships?edit=${s.id}">Edit</a><button type="button" class="btn-text" data-sdel="${s.id}">Remove</button></div></td>
          </tr>`).join("")}</tbody></table></div></section>` : ""}`;

      $("sch-form").addEventListener("submit", (ev) => {
        ev.preventDefault();
        const fd = new FormData(ev.target);
        const rec = { id: e.id || uid(), updated: Date.now(), name: String(fd.get("name") || "").trim(), amount: fd.get("amount") || "", deadline: fd.get("deadline") || "", status: fd.get("status"), needs: fd.getAll("needs"), renewable: !!fd.get("renewable"), link: String(fd.get("link") || "").trim() };
        if (!rec.name) return;
        Store.upsert("scholarships", rec);
        if (editing) location.hash = "#/scholarships"; else render();
      });
      document.querySelectorAll("[data-sstatus]").forEach((s) => s.addEventListener("change", () => { const x = data.scholarships.find((y) => y.id === s.dataset.sstatus); Store.upsert("scholarships", { ...x, status: s.value, updated: Date.now() }); render(); }));
      document.querySelectorAll("[data-sdel]").forEach((b) => b.addEventListener("click", () => { if (confirm("Remove this scholarship?")) { Store.remove("scholarships", b.dataset.sdel); render(); } }));
    };

    // ---- Application timeline -----------------------------------------
    PAGES.timeline = () => {
      const done = col().checklist;
      const all = TIMELINE.flatMap((g) => g.items), n = all.filter(([id]) => done[id] && done[id].done).length;
      $("page").innerHTML = `
        ${pageHead("timeline", "Application timeline", "What to do and when, from junior fall to senior spring. Check things off as you go. Exact dates vary by college and by year, so always confirm on each college's site.")}
        <section class="card"><div class="stat"><div class="stat-label">Progress<small>${n} of ${all.length} done</small></div><div class="stat-bar"><i style="width:${Math.round((100 * n) / all.length)}%"></i></div></div></section>
        ${TIMELINE.map((g) => `<section class="card week"><div class="week-head"><h2>${g.title}</h2><span class="fine">${g.items.filter(([id]) => done[id] && done[id].done).length}/${g.items.length}</span></div>
          ${g.items.map(([id, t, sub]) => `<label class="session check-item ${done[id] && done[id].done ? "done" : ""}"><input type="checkbox" data-check="${id}"${done[id] && done[id].done ? " checked" : ""}><span class="session-body"><strong>${esc(t)}</strong>${sub ? `<span>${esc(sub)}</span>` : ""}</span></label>`).join("")}
        </section>`).join("")}`;
      document.querySelectorAll("[data-check]").forEach((c) => c.addEventListener("change", () => { Store.setCheck(c.dataset.check, c.checked); render(); }));
    };

    // ---- Aid offer comparison -----------------------------------------
    const AID_ROWS = [
      ["tuition", "Tuition and fees", "cost"], ["housing", "Housing and food", "cost"], ["other", "Books, travel and other costs", "cost"],
      ["grants", "Grants and scholarships", "free"], ["workstudy", "Work-study", "earn"], ["loans", "Loans (federal and private)", "loan"]
    ];
    PAGES.aid = () => {
      const offers = col().aid;
      const calc = (o) => {
        const v = (k) => Math.max(0, +o[k] || 0);
        const coa = v("tuition") + v("housing") + v("other"), net = Math.max(0, coa - v("grants"));
        return { coa, net, gap: Math.max(0, net - v("workstudy") - v("loans")), four: net * 4, loans: v("loans") };
      };
      $("page").innerHTML = `
        ${pageHead("aid", "Aid offer comparison", "Put up to three financial aid offers side by side. Enter each year's numbers from the offer letter.")}
        <section class="card"><div class="table-scroll"><table class="table aid-table">
          <thead><tr><th></th>${offers.map((o, i) => `<th><input type="text" class="aid-name" data-aid="${i}" data-k="name" value="${esc(o.name || "")}" placeholder="College ${i + 1}" aria-label="College ${i + 1} name"></th>`).join("")}</tr></thead>
          <tbody>
            ${AID_ROWS.map(([k, l, kind]) => `<tr class="aid-${kind}"><td>${l}${kind === "loan" ? `<div class="fine">Must be repaid, with interest</div>` : kind === "earn" ? `<div class="fine">Earned by working during the year</div>` : kind === "free" ? `<div class="fine">Free money: no repaying</div>` : ""}</td>${offers.map((o, i) => `<td><input type="number" min="0" step="100" inputmode="decimal" data-aid="${i}" data-k="${k}" value="${esc(o[k] || "")}" aria-label="${l}, college ${i + 1}"></td>`).join("")}</tr>`).join("")}
          </tbody>
          <tfoot>
            <tr><td>Cost of attendance</td>${offers.map((o, i) => `<td data-out="coa-${i}"></td>`).join("")}</tr>
            <tr class="aid-key"><td><strong>Net price</strong><div class="fine">Cost minus grants and scholarships</div></td>${offers.map((o, i) => `<td data-out="net-${i}"></td>`).join("")}</tr>
            <tr><td>Still to cover<div class="fine">After work-study and loans</div></td>${offers.map((o, i) => `<td data-out="gap-${i}"></td>`).join("")}</tr>
            <tr><td>Four years at this net price<div class="fine">If nothing changes; costs usually rise</div></td>${offers.map((o, i) => `<td data-out="four-${i}"></td>`).join("")}</tr>
          </tfoot>
        </table></div>
        <p class="fine" style="margin-top:14px">Compare net prices, not sticker prices: a college with a higher cost can be cheaper after grants. Loans lower what you pay now, not what the college costs. Ask each college whether its scholarships renew every year and what grades they require. Offer letters use different words for the same things; the <a href="https://studentaid.gov/" target="_blank" rel="noopener">StudentAid.gov</a> site explains the terms.</p></section>`;
      const paint = () => {
        const res = col().aid.map(calc);
        const filled = res.map((r, i) => (r.coa ? i : -1)).filter((i) => i >= 0);
        const best = filled.length > 1 ? filled.reduce((a, b) => (res[b].net < res[a].net ? b : a)) : -1;
        res.forEach((r, i) => {
          const set = (k, t) => { document.querySelector(`[data-out="${k}-${i}"]`).textContent = t; };
          set("coa", r.coa ? money(r.coa) : "—"); set("net", r.coa ? money(r.net) : "—"); set("gap", r.coa ? money(r.gap) : "—"); set("four", r.coa ? money(r.four) : "—");
          document.querySelector(`[data-out="net-${i}"]`).classList.toggle("best", i === best);
        });
      };
      document.querySelectorAll("[data-aid]").forEach((inp) => inp.addEventListener("input", () => { Store.setAid(+inp.dataset.aid, inp.dataset.k, inp.value); paint(); }));
      paint();
    };

    // ---- Essay checker --------------------------------------------------
    const STOP = new Set("a an and are as at be but by for from had has have he her his i if in into is it its me my not of on or our she so than that the their them then there they this to too up was we were what when which who will with you your i'm it's i've".split(" "));
    const FILLER = ["very", "really", "just", "things", "stuff", "basically", "actually", "literally"];
    PAGES.essay = () => {
      const es = col().essay;
      $("page").innerHTML = `
        ${pageHead("essay", "Essay checker", "Paste or write your essay to check its length and spot words you lean on too often. It's saved with your progress, never sent anywhere else.")}
        <div class="essay-grid">
          <section class="card">
            <form class="filters filters-row" id="essay-limit"><label>Word limit<input type="number" name="limit" min="50" max="5000" step="10" value="${esc(es.limit || 650)}"></label></form>
            <textarea id="essay-text" class="essay-box" placeholder="Start writing, or paste your draft here." aria-label="Your essay">${esc(es.text || "")}</textarea>
          </section>
          <section class="card essay-side">
            <div class="essay-count"><strong id="es-words">0</strong><span id="es-limit">of 650 words</span></div>
            <div class="stat-bar"><i id="es-bar"></i></div>
            <p class="fine" id="es-msg"></p>
            <table class="table"><tbody>
              <tr><td>Characters</td><td id="es-chars"></td></tr>
              <tr><td>Paragraphs</td><td id="es-paras"></td></tr>
              <tr><td>Sentences</td><td id="es-sents"></td></tr>
              <tr><td>Average sentence</td><td id="es-avg"></td></tr>
            </tbody></table>
            <h2 style="margin-top:18px">Most repeated words</h2><div id="es-reps" class="chips"></div>
            <h2 style="margin-top:18px">Words that often add little</h2><div id="es-fill" class="chips"></div>
            <p class="fine" style="margin-top:14px">A limit is a ceiling, not a target, but using most of it usually gives you room for specific details. Read it aloud: the ear catches what the eye skips.</p>
          </section>
        </div>`;
      const ta = $("essay-text"), lim = $("essay-limit").elements.limit;
      let t = null;
      const paint = () => {
        const text = ta.value, limit = Math.max(1, +lim.value || 650);
        const words = (text.match(/[A-Za-z0-9À-ɏ'’-]+/g) || []);
        const n = words.length, sents = (text.match(/[^.!?]+[.!?]+/g) || []).length || (n ? 1 : 0);
        const paras = text.split(/\n\s*\n/).filter((p) => p.trim()).length;
        $("es-words").textContent = n.toLocaleString("en-US");
        $("es-limit").textContent = `of ${limit.toLocaleString("en-US")} words`;
        $("es-bar").style.width = Math.min(100, (100 * n) / limit) + "%";
        $("es-bar").classList.toggle("over", n > limit);
        $("es-msg").textContent = n > limit ? `${n - limit} over the limit: time to cut.` : n ? `${limit - n} words left.` : "";
        $("es-msg").className = "fine" + (n > limit ? " warn-text" : "");
        $("es-chars").textContent = text.length.toLocaleString("en-US");
        $("es-paras").textContent = paras;
        $("es-sents").textContent = sents;
        $("es-avg").textContent = sents ? `${(n / sents).toFixed(1)} words` : "—";
        const counts = {};
        words.forEach((w) => { const k = w.toLowerCase().replace(/[’']/g, "'"); if (k.length > 2 && !STOP.has(k)) counts[k] = (counts[k] || 0) + 1; });
        const reps = Object.entries(counts).filter(([, c]) => c >= 3).sort((a, b) => b[1] - a[1]).slice(0, 10);
        $("es-reps").innerHTML = reps.length ? reps.map(([w, c]) => `<span class="word-chip">${esc(w)} <b>${c}</b></span>`).join("") : `<p class="fine">No word appears three or more times yet.</p>`;
        const fills = FILLER.map((f) => [f, words.filter((w) => w.toLowerCase() === f).length]).filter(([, c]) => c);
        $("es-fill").innerHTML = fills.length ? fills.map(([w, c]) => `<span class="word-chip">${w} <b>${c}</b></span>`).join("") : `<p class="fine">None found.</p>`;
      };
      const save = () => { clearTimeout(t); t = setTimeout(() => Store.setCollege({ essay: { text: ta.value, limit: +lim.value || 650, updated: Date.now() } }), 600); };
      ta.addEventListener("input", () => { paint(); save(); });
      lim.addEventListener("input", () => { paint(); save(); });
      paint();
    };
  };

  return { register, fit, TIMELINE };
})();
