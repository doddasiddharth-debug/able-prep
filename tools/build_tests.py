"""Assemble the numbered practice tests and new bank items from data/draft/.

  data/draft/ptN-rw1.json, ptN-rw2.json, ptN-rw2e.json,
             ptN-m1.json,  ptN-m2.json,  ptN-m2e.json                -> data/tests.json
  (Module 2 comes in two versions, as on the adaptive real test: `rw2`/`m2`
  is the harder one, `rw2e`/`m2e` the easier; Module 1 decides which a
  student gets.)
  data/draft/bank-*.json                                            -> appended to data/questions.json

Checks every item against the bank's schema and taxonomy, module sizes, and
id uniqueness (test items must never share an id with the bank). Run it
again after editing a draft; it rebuilds tests.json and replaces bank items
by id rather than duplicating them.
Usage: python3 tools/build_tests.py
"""
import json, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, "data", *p)
bank = json.load(open(D("questions.json")))
meta = bank["meta"]
SIZE = {"rw": 27, "math": 22}
errors = []

def check(q, where):
    need = ["id", "section", "domain", "skill", "difficulty", "stem", "answer", "explanation"]
    for k in need:
        if k not in q: errors.append(f"{where} {q.get('id')}: missing {k}")
    s = q.get("section")
    if s not in ("rw", "math"): errors.append(f"{where} {q.get('id')}: bad section"); return
    if q.get("domain") not in meta["skills"][s] or q.get("skill") not in meta["skills"][s].get(q.get("domain"), []):
        errors.append(f"{where} {q['id']}: skill/domain {q.get('domain')!r}/{q.get('skill')!r} not in meta")
    if q.get("difficulty") not in ("easy", "medium", "hard"): errors.append(f"{where} {q['id']}: difficulty")
    if q.get("type") == "spr":
        if not isinstance(q["answer"], str) or "choices" in q: errors.append(f"{where} {q['id']}: grid-in needs a string answer and no choices")
    else:
        c = q.get("choices")
        if not (isinstance(c, list) and len(c) == 4 and len(set(c)) == 4): errors.append(f"{where} {q['id']}: needs 4 distinct choices")
        if q.get("answer") not in (0, 1, 2, 3): errors.append(f"{where} {q['id']}: answer index")
    if s == "rw" and not q.get("passage"): errors.append(f"{where} {q['id']}: rw needs a passage")

tests = {}
for f in sorted(glob.glob(D("draft", "pt*-*.json"))):
    key = os.path.basename(f)[:-5]                     # pt1-rw1
    m = re.fullmatch(r"pt(\d+)-(rw|m)(1|2|2e)", key)
    if not m: errors.append(f"unexpected draft {key}"); continue
    n, sec = int(m.group(1)), ("rw" if m.group(2) == "rw" else "math")
    mod, level = (1, None) if m.group(3) == "1" else (2, "easier" if m.group(3) == "2e" else "harder")
    qs = json.load(open(f))
    if len(qs) != SIZE[sec]: errors.append(f"{key}: {len(qs)} items, expected {SIZE[sec]}")
    for i, q in enumerate(qs, 1):
        check(q, key)
        want = f"{key}-{i:02d}"
        if q.get("id") != want: errors.append(f"{key}: item {i} id {q.get('id')} != {want}")
        if q.get("section") != sec: errors.append(f"{key}: {q.get('id')} section {q.get('section')}")
    entry = {"key": key, "section": sec, "module": mod, "questions": qs}
    if level: entry["level"] = level
    tests.setdefault(n, []).append(entry)

order = {("rw", 1, None): 0, ("rw", 2, "harder"): 1, ("rw", 2, "easier"): 2, ("math", 1, None): 3, ("math", 2, "harder"): 4, ("math", 2, "easier"): 5}
out = {"note": "Numbered full-length adaptive practice tests: per section, Module 1 then a harder or easier Module 2 depending on Module 1. Their questions are kept out of the question bank so each test is unseen the first time. Built by tools/build_tests.py from data/draft/.", "tests": []}
for n in sorted(tests):
    mods = sorted(tests[n], key=lambda m: order[(m["section"], m["module"], m.get("level"))])
    if len(mods) != 6: errors.append(f"test {n}: {len(mods)} modules, expected 6 (Module 1, harder and easier Module 2, per section)")
    out["tests"].append({"id": f"pt{n}", "number": n, "name": f"Practice Test {n}", "modules": mods})

new_bank = []
for f in sorted(glob.glob(D("draft", "bank-*.json"))):
    for q in json.load(open(f)):
        check(q, os.path.basename(f)); new_bank.append(q)
ids = {}
for q in [q for t in out["tests"] for m in t["modules"] for q in m["questions"]] + new_bank + [q for q in bank["questions"] if q["id"] not in {x["id"] for x in new_bank}]:
    if q["id"] in ids: errors.append(f"duplicate id {q['id']}")
    ids[q["id"]] = 1
passages = {}
for q in [q for t in out["tests"] for m in t["modules"] for q in m["questions"]] + new_bank + bank["questions"]:
    p = (q.get("passage") or "") + "|" + q["stem"]
    if p in passages and passages[p] != q["id"]: errors.append(f"same passage+stem: {q['id']} and {passages[p]}")
    passages.setdefault(p, q["id"])

if errors:
    print("\n".join(errors)); sys.exit(1)
json.dump(out, open(D("tests.json"), "w"), ensure_ascii=False, indent=1)
keep = [q for q in bank["questions"] if q["id"] not in {x["id"] for x in new_bank}]
bank["questions"] = sorted(keep + new_bank, key=lambda q: (q["section"] != "rw", int(q["id"].split("-")[1])))
json.dump(bank, open(D("questions.json"), "w"), ensure_ascii=False, indent=1)
print(f"tests.json: {len(out['tests'])} tests; bank: {len(bank['questions'])} questions ({len(new_bank)} new)")
