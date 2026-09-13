# ABLE Preps · SAT Practice

A free Digital SAT practice app from ABLE Preps. Static site, no build step:
serve the folder with any static server (`python3 -m http.server`) or host it
on GitHub Pages exactly like ableinitiatives.com. No accounts; everything a
student does stays in their browser.

## What it does

| Page | What's there |
|---|---|
| **Dashboard** | Predicted score (from recent answers), "Focus next" weakest domains, streak, days to test day, the next study-plan session, activity heatmap |
| **Question bank** | Every College Board skill (10 R&W, 19 Math) with question counts, solved counts, and your accuracy; drill by skill, domain, or difficulty; untimed with explanations |
| **Practice tests** | Timed modules per section at the real test's pace, Bluebook-style screen, score report by domain plus an estimated 200–800 section score; attempt history |
| **Question Rush** | One question at a time against a per-question clock; stars for speed and accuracy |
| **Challenge questions** | Hard-tier only, per section |
| **Vocabulary** | Flashcards and a definition quiz; words count as mastered after two correct answers |
| **Mistakes** | Every question whose latest attempt was wrong, to redo |
| **Study planner** | Test date + target + days per week → week-by-week sessions (drills on your weakest domains, Rush, a timed module, mistakes review, vocab), launchable and checkable |
| **Analytics** | Accuracy by domain and by skill, pacing by difficulty, activity, session history |
| **Score predictor** | 16-question mixed diagnostic → estimated 400–1600 total, plus a running prediction from all practice |
| **Score calculator** | Raw module scores → estimated scaled score |
| **Settings** | Name (shown on the test screen), test date, target, reset |

The **practice screen** copies the real testing app's layout: passage left /
question right (Math centres the question alone), Mark for Review, answer
eliminator, question navigator with legend, timer with hide (forced back for
the last five minutes), Directions, a Desmos calculator drawer on Math, and
grid-in inputs. Keyboard: 1–4 to answer, arrows to move, Esc to close popups.

## Files

```
index.html             app shell (sidebar + page), practice screen, results screen
assets/css/prep.css    shell (ABLE palette) + practice screen (Bluebook palette)
assets/js/store.js     localStorage state: history, attempts, settings, plan, vocab
assets/js/scoring.js   raw→scaled curves and the running prediction
assets/js/practice.js  the session engine: bank / test / diagnostic / rush / review
assets/js/app.js       router and every page
data/questions.json    the question bank
data/vocab.json        the word list
assets/images/         ABLE Preps mark, favicon
```

## Scoring

`scoring.js` holds two curves (R&W over 54 raw, Math over 44) sampled from a
published Digital SAT score calculator and interpolated by fraction correct,
so they apply to a 12-question module the same way. The real test is adaptive
and every form has its own curve; every screen that shows an estimate says so.

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

## Cache version

When any CSS or JS file changes, bump the `?v=` on its tag in `index.html`.

## Not affiliated with College Board

SAT is a registered trademark of College Board, which is not involved with
this project.
