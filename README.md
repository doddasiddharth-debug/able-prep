# ABLE Preps · SAT Practice

A free Digital SAT practice app from ABLE Preps. Static site, no build step:
serve the folder with any static server (`python3 -m http.server`) or host it
on GitHub Pages exactly like ableinitiatives.com. Works without an account
(everything stays in the browser); with an account, progress syncs across
devices through Supabase.

## What it does

| Page | What's there |
|---|---|
| **Dashboard** | Predicted score (from recent answers), "Focus next" weakest domains, streak, days to test day, the next study-plan session, activity heatmap |
| **Question bank** | Every College Board skill (10 R&W, 19 Math) with question counts, solved counts, and your accuracy; drill by skill, domain, or difficulty; untimed with explanations |
| **Practice tests** | Numbered full-length tests (`data/tests.json`): Reading and Writing Module 1 and 2 (27 questions, 32 min each), a 10-minute break, Math Module 1 and 2 (22 questions, 35 min each), then a score report (estimated 400–1600, section scores, by module and by domain, each module reviewable). Take a whole test or one section. Plus a quick module of random bank questions; attempt history |
| **Question Rush** | One question at a time against a per-question clock; stars for speed and accuracy |
| **Challenge questions** | Hard-tier only, per section |
| **Vocabulary** | Flashcards and a definition quiz; words count as mastered after two correct answers |
| **Mistakes** | Every question whose latest attempt was wrong, to redo |
| **Study planner** | Test date + target + days per week → week-by-week sessions (drills on your weakest domains, Rush, a timed module, mistakes review, vocab), launchable and checkable |
| **Analytics** | Accuracy by domain and by skill, pacing by difficulty, activity, session history |
| **Score predictor** | 16-question mixed diagnostic → estimated 400–1600 total, plus a running prediction from all practice |
| **Score calculator** | Raw module scores → estimated scaled score |
| **Settings** | Name (shown on the test screen), test date, target, reset |
| **Account** | Sign in / create account (email + password), password reset, sync status, delete server data |
| **College list** | Colleges you're considering with plan, deadline and status; each tagged reach / target / likely from your SAT score against the college's middle-50% range (admit rate under 20% is always a reach) |
| **Scholarships** | Tracker with amount, deadline, what each needs and status; totals applied for and won, the next deadline, where to look, scam red flags |
| **Application timeline** | Junior fall to senior spring checklist (no year-specific dates), checkable |
| **Aid offers** | Up to three offers side by side: cost of attendance, net price (cost minus grants), still to cover after work-study and loans, four-year net price |
| **Essay checker** | Word count against your limit, characters, paragraphs, sentences, most repeated words and filler words; the draft saves with your progress |

The **practice screen** copies the real testing app's layout: passage left /
question right (Math centres the question alone), Mark for Review, answer
eliminator, question navigator with legend, timer with hide (forced back for
the last five minutes), Directions, a Desmos calculator drawer on Math, and
grid-in inputs. Keyboard: 1–4 to answer, arrows to move, Esc to close popups.

## Files

```
index.html             app shell (sidebar + page), practice screen, results screen
assets/css/prep.css    shell (ABLE palette) + practice screen (Bluebook palette)
assets/js/config.js    Supabase URL + anon key (blank = accounts off)
assets/js/store.js     localStorage state: history, attempts, settings, plan, vocab
assets/js/auth.js      accounts and sync (Supabase); merges device + account on sign-in
supabase/schema.sql    the one table and its row-level-security policies
assets/js/scoring.js   raw→scaled curves and the running prediction
assets/js/practice.js  the session engine: bank / test / diagnostic / rush / review
assets/js/app.js       router and every page
assets/js/college.js   the College tools (college list, scholarships, timeline, aid, essay); registered into app.js's router
data/questions.json    the question bank
data/tests.json        the numbered practice tests (their questions are not in the bank)
data/vocab.json        the word list
assets/images/         ABLE Preps mark, favicon
```

## College tools

`college.js` adds five pages under **College** in the sidebar. Its data lives
in `Store` under `college` and syncs with an account like everything else.
List items carry an `updated` time so a merge keeps the newer copy, and a
removed item leaves a tombstone in `college.removed` so a merge can't bring it
back. Nothing states a year-specific date, price or rate: students enter their
own numbers, and the guidance points to official sources (College Scorecard,
StudentAid.gov, the FTC, CareerOneStop).

## Scoring

`scoring.js` holds two curves (R&W over 54 raw, Math over 44) sampled from a
published Digital SAT score calculator and interpolated by fraction correct,
so they apply to a 12-question module the same way. The real test is adaptive
and every form has its own curve; every screen that shows an estimate says so.

## Practice tests

`data/tests.json` holds each numbered test as four modules in order
(`rw1`, `rw2`, `m1`, `m2`), each a list of full question objects in the bank's
schema, with ids like `pt2-rw1-07`. Test questions are deliberately **not** in
`questions.json`, so the bank, Rush, the diagnostic and Mistakes never show
them and a test is unseen the first time. Modules follow the real test's
layout: Reading and Writing grouped by domain in the official order (Craft
and Structure, Information and Ideas, Standard English Conventions,
Expression of Ideas), easy to hard within each group; Math easy to hard with
the domains interleaved and about a quarter grid-ins. The forms are fixed,
not adaptive, and the report says the score is an estimate.

`tools/build_tests.py` rebuilds `tests.json` from per-module drafts in
`data/draft/` (not committed) and appends bank drafts to `questions.json`,
checking schema, taxonomy, module sizes and id collisions. The Math items
for each test come from `tools/draft_math_ptN.py`, which computes and
re-checks every key like `gen_math.py`. The full-test flow is in `app.js`
(`runTest`): `Practice.start` takes `onModuleDone` to hand back a finished
module instead of showing results, and `onReviewExit` to return from
reviewing a module to the report. A finished test is saved as a `fulltest`
attempt with each module's answers, so its report can be reopened.

## Adding questions

Append to `questions` in `data/questions.json`:

| field | notes |
|---|---|
| `id` | unique, e.g. `rw-023` / `m-025` |
| `section` | `rw` or `math` |
| `domain` | one of the four for that section (`meta.sections`) |
| `skill` | must be one of the names under that domain in `meta.skills` |
| `difficulty` | `easy` / `medium` / `hard` |
| `passage` | R&W only. `\n\n` separates paragraphs; a line that is exactly `Text 1` or `Text 2` renders bold; a block with two-space-aligned columns renders monospaced (tables) |
| `stem` | the question |
| `choices` | four strings, A–D (omit for grid-ins) |
| `type` | `"spr"` for a grid-in |
| `answer` | index 0–3 for multiple choice; a string like `"9"` or `"3/4"` for grid-ins |
| `explanation` | why the right answer is right and, briefly, why the tempting wrong ones are wrong |

**Every question must be original and reviewed by a person before it's
merged.** Do not copy College Board questions: their released material is free
to use on their site, not to republish here. Generated drafts are fine as
drafts; an ABLE Preps officer works every one and confirms the key before it
goes in. A wrong answer key is worse than no question.

Grid-in grading is forgiving on format and strict on value: `9`, `9.0`, and
`18/2` all match `"9"`.

Words go in `data/vocab.json`: `word`, `pos`, `def`, `example`.

## Accounts (Supabase)

1. Create a free project at supabase.com. In **SQL Editor**, run
   `supabase/schema.sql` once.
2. **Authentication → Providers → Email**: leave Email on. Turn **Confirm
   email off** unless you've set up custom SMTP: the built-in mailer sends
   only a few messages an hour, which won't survive a classroom signing up
   at once.
3. **Authentication → URL Configuration**: Site URL
   `https://prep.ableinitiatives.com`; add `https://prep.ableinitiatives.com/**`
   and `http://localhost:4178/**` to Redirect URLs (password-reset links go
   there).
4. **Project Settings → API**: copy the Project URL and the `anon` `public`
   key into `assets/js/config.js`, bump its `?v=`, push.

The anon key is meant to be public; row-level security means each user can
only read and write their own `progress` row. Every save is pushed (debounced
1.5 s); signing in merges the browser's progress with the account's (answers
and sessions are unioned, the fuller record wins elsewhere); signing out clears
the browser copy so a shared computer doesn't hand it to the next student.

## Cache version

When any CSS or JS file changes, bump the `?v=` on its tag in `index.html`.

## Not affiliated with College Board

SAT is a registered trademark of College Board, which is not involved with
this project.

## Visitor analytics

Anonymous visitor counts come from [GoatCounter](https://www.goatcounter.com)
(`assets/js/analytics.js`): no cookies, no personal data, nothing that
identifies a visitor, so no cookie banner is needed. One GoatCounter site
(code `siddo`, dashboard at https://siddo.goatcounter.com)
covers every ABLE site: ableinitiatives.com, prep. and business.ableinitiatives.com,
and Strands of Life. Each path is prefixed with its host to keep them apart.
The same `analytics.js` is copied into each repo; keep the copies in step.

Besides page views it records, as events: clicks on email links
(`email/…`) and on links to other sites (`outbound/…`), and in the course apps
`window.ableTrack(...)` calls (quizzes passed or failed, calculators used,
courses completed, certificates made, downloaded or printed; SAT sessions
finished). Visits from localhost are not counted.
