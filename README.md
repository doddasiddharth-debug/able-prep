# ABLE Preps · SAT Practice

A free Digital SAT practice tool from ABLE Preps. Static site, no build step:
open `index.html` or serve the folder with any static server. Hosts on GitHub
Pages exactly like ableinitiatives.com.

## What it does (v0)

- **Question bank** — filter by section, domain, difficulty; untimed; check
  each answer and read the explanation.
- **Timed module** — one section on the clock, no feedback until the end,
  scored by domain, then review every question with its explanation.
- **Bluebook-style screen** — the practice screen copies the real testing
  app's layout: passage left / question right, Mark for Review, answer
  eliminator, question navigator, timer with hide, Desmos calculator on Math,
  student-produced-response (grid-in) inputs.
- **Progress** stays in the browser (`localStorage`), no account. The home
  page shows accuracy by domain; "Reset" clears it.

## Files

```
index.html            all three views (home, practice, results)
assets/css/prep.css   shell styles (ABLE palette) + practice screen (Bluebook palette)
assets/js/prep.js     everything: filtering, session, timer, grading, results
data/questions.json   the question bank
```

## Adding questions

Append to `questions` in `data/questions.json`. Every field:

| field | notes |
|---|---|
| `id` | unique, e.g. `rw-013` / `m-013` |
| `section` | `rw` or `math` |
| `domain` | one of the four for that section (see `meta.sections`) |
| `skill` | College Board's skill name within the domain |
| `difficulty` | `easy` / `medium` / `hard` |
| `passage` | R&W only. `\n\n` separates paragraphs; a line that is exactly `Text 1` or `Text 2` renders bold |
| `stem` | the question |
| `choices` | four strings, A–D (omit for grid-ins) |
| `type` | `"spr"` for a grid-in |
| `answer` | index 0–3 for multiple choice; a string like `"9"` or `"3/4"` for grid-ins |
| `explanation` | why the right answer is right and, briefly, why the tempting wrong ones are wrong |

**Every question must be original and reviewed by a person before it's
merged.** Do not copy College Board questions: their released material is
free to use on their site but not to republish here. Generated drafts are
fine as drafts — an ABLE Preps officer works every one and confirms the key
before it goes in. A wrong answer key is worse than no question.

Grid-in grading is forgiving on format and strict on value: `9`, `9.0`, and
`18/2` all match an answer of `"9"`.

## Cache version

When `prep.css` or `prep.js` changes, bump `?v=1` on both tags in
`index.html` so returning visitors are not served a stale copy.

## Not affiliated with College Board

SAT is a registered trademark of College Board, which is not involved with
this project.
