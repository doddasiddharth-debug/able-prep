/* Raw-to-scaled score curves.
   Calibrated against a published Digital SAT calculator by sampling raw totals
   across both modules of a section (0–54 R&W, 0–44 Math) and reading the
   scaled result. Stored as fraction-correct -> scaled points and interpolated
   linearly, so they apply to a 12-question module the same way as a 54-question
   section. The real test is adaptive and no fixed curve is exact; this is an
   estimate and every screen that shows it says so. */
window.Scoring = (() => {
  "use strict";
  const CURVES = {
    rw:   [[0, 200], [6 / 54, 250], [12 / 54, 300], [18 / 54, 330], [24 / 54, 370], [30 / 54, 450], [36 / 54, 540], [40 / 54, 590], [42 / 54, 620], [44 / 54, 650], [48 / 54, 710], [50 / 54, 740], [52 / 54, 770], [1, 800]],
    math: [[0, 200], [4 / 44, 220], [10 / 44, 290], [14 / 44, 350], [20 / 44, 400], [24 / 44, 460], [30 / 44, 550], [32 / 44, 580], [34 / 44, 620], [36 / 44, 660], [40 / 44, 730], [42 / 44, 770], [1, 800]]
  };
  const round10 = (x) => Math.round(x / 10) * 10;

  const scaled = (section, fraction) => {
    const c = CURVES[section];
    const f = Math.max(0, Math.min(1, fraction));
    for (let i = 1; i < c.length; i++) {
      if (f <= c[i][0]) {
        const [f0, s0] = c[i - 1], [f1, s1] = c[i];
        return round10(s0 + (s1 - s0) * ((f - f0) / (f1 - f0)));
      }
    }
    return 800;
  };

  // Prediction from practice history: the most recent answers per section,
  // weighted toward the newest so improvement shows up. Needs a minimum
  // sample or it returns null and the UI asks for a diagnostic instead.
  const MIN_PER_SECTION = 8, WINDOW = 40;
  const predict = (history) => {
    const per = {};
    ["rw", "math"].forEach((s) => {
      const recent = history.filter((h) => h.section === s).slice(-WINDOW);
      if (recent.length < MIN_PER_SECTION) { per[s] = null; return; }
      let w = 0, ok = 0;
      recent.forEach((h, i) => { const wt = 1 + i / recent.length; w += wt; if (h.correct) ok += wt; });
      per[s] = { n: recent.length, fraction: ok / w, score: scaled(s, ok / w) };
    });
    if (!per.rw || !per.math) return { rw: per.rw, math: per.math, total: null };
    return { rw: per.rw, math: per.math, total: per.rw.score + per.math.score };
  };

  return { scaled, predict, MIN_PER_SECTION };
})();
