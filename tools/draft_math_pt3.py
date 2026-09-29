"""Draft math items for ABLE Preps practice test 3 (two modules) and 20 extra
bank items, written to the conventions of tools/gen_math.py.

Every key is computed from the item's parameters and then re-solved a second,
independent way (substitution into the displayed text, brute force over a
grid, or a different method) with an assert. A failed assert stops the run
before anything is written.

Usage: python3 tools/draft_math_pt3.py
Writes data/draft/pt3-m1.json (Module 1), pt3-m2.json (harder Module 2),
pt3-m2e.json (easier Module 2), bank-m-3.json (bank extras) and
bank-m-pt3-moved.json (the easy items taken out of the harder Module 2).
Audit:  python3 tools/audit_math.py < data/draft/pt3-m1.json   (and the others)
"""
import json, os, re, math, itertools, statistics
from fractions import Fraction as F
from collections import Counter

ALG = "Algebra"; ADV = "Advanced Math"; PSDA = "Problem-Solving and Data Analysis"; GEO = "Geometry and Trigonometry"
HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT = os.path.join(HERE, "..", "data", "draft")

# ---------------------------------------------------------------- helpers (copied from gen_math.py)
def fmt(n, dec=False):
    if isinstance(n, float): n = F(n).limit_denominator(1000)
    if isinstance(n, F):
        if n.denominator == 1: return str(n.numerator)
        d = n.denominator
        while d % 2 == 0: d //= 2
        while d % 5 == 0: d //= 5
        if dec and d == 1:
            return f"{float(n):.4f}".rstrip("0").rstrip(".")
        return f"{n.numerator}/{n.denominator}"
    return str(n)

def neg(s):
    return str(s).replace("-", "−")

def commas(s):
    """1,234-style grouping for numbers of four or more digits, as College Board prints them."""
    return re.sub(r"\d{4,}", lambda m: f"{int(m.group()):,}", s) if "." not in s and "/" not in s else s

# ---------------------------------------------------------------- independent evaluator (same parser as audit_math.py)
def to_py(expr):
    e = expr.replace("−", "-").replace("²", "**2").replace("³", "**3").replace("√", "SQRT").replace(",", "")
    e = e.replace("≤", "<=").replace("≥", ">=").replace("π", "*PI").replace("(*PI", "(PI")
    e = re.sub(r"^\*PI", "PI", e)
    e = re.sub(r"(\d)\s*\(", r"\1*(", e)
    e = re.sub(r"(\d)([a-z])", r"\1*\2", e)
    e = re.sub(r"\)\s*\(", ")*(", e)
    e = re.sub(r"\)([a-z])", r")*\1", e)
    e = re.sub(r"(?<![A-Z])([a-z])\(", r"\1*(", e)
    return e.replace("^", "**").replace("SQRT", "sqrt")

def ev(expr, **env):
    return eval(to_py(expr), {"sqrt": math.sqrt, "PI": math.pi, "__builtins__": {}}, env)

def rhs(s):  # "M(d) = 45d + 240" -> "45d + 240"
    return s.split("=", 1)[1]

def same_poly(a, b, var="x", pts=(-3, -1, 2, 5, 7)):
    return all(abs(ev(a, **{var: F(p)}) - ev(b, **{var: F(p)})) < 1e-9 for p in pts)

def val(s):
    """Numeric value of a displayed choice ('−3', '1,125', '5π/12', '20/29'), or None."""
    t = s.replace("−", "-").replace(",", "")
    if re.fullmatch(r"-?\d+(\.\d+)?(/\d+)?", t): return float(F(t))
    if re.fullmatch(r"-?\d*π(/\d+)?", t):
        coef, _, den = t.partition("/")
        c = coef.replace("π", "")
        c = 1 if c in ("", "+") else (-1 if c == "-" else float(c))
        return c * math.pi / (float(den) if den else 1)
    return None

# ---------------------------------------------------------------- item builders
OUT = {"m1": [], "m2": [], "bank": []}

def _item(dest, domain, skill, diff, stem, expl, passage):
    it = {"id": None, "section": "math", "domain": domain, "skill": skill, "difficulty": diff, "stem": stem}
    OUT.setdefault(dest, []).append(it)
    return it

def mc(dest, domain, skill, diff, stem, correct, distractors, expl, pos, passage=None, dec=False):
    """Numeric choices, listed in ascending order; `pos` asserts where the key lands."""
    vals = [F(correct)] + [F(d) for d in distractors]
    assert len(set(vals)) == 4, (stem, vals)
    vals.sort()
    it = _item(dest, domain, skill, diff, stem, expl, passage)
    it["choices"] = [commas(neg(fmt(v, dec))) for v in vals]
    it["answer"] = vals.index(F(correct))
    assert it["answer"] == pos, (stem[:60], it["answer"], pos)
    it["explanation"] = expl
    if passage: it["passage"] = passage
    return it

def mct(dest, domain, skill, diff, stem, choices, key, expl, passage=None):
    """Text choices in the given order; `key` is the correct index."""
    assert len(set(choices)) == 4
    it = _item(dest, domain, skill, diff, stem, expl, passage)
    it["choices"] = list(choices); it["answer"] = key; it["explanation"] = expl
    if passage: it["passage"] = passage
    return it

def spr(dest, domain, skill, diff, stem, answer, expl, passage=None, dec=False):
    it = _item(dest, domain, skill, diff, stem, expl, passage)
    it["type"] = "spr"
    it["answer"] = answer if isinstance(answer, str) else fmt(F(answer), dec)
    it["explanation"] = expl
    if passage: it["passage"] = passage
    return it

def solve2(a1, b1, c1, a2, b2, c2):
    """Cramer's rule for a1x + b1y = c1, a2x + b2y = c2."""
    d = F(a1 * b2 - a2 * b1)
    return F(c1 * b2 - c2 * b1) / d, F(a1 * c2 - a2 * c1) / d

def real_roots(a, b, c):
    D = b * b - 4 * a * c
    if D < 0: return []
    if D == 0: return [F(-b, 2 * a)]
    r = math.isqrt(D)
    if r * r == D: return sorted([F(-b - r, 2 * a), F(-b + r, 2 * a)])
    return sorted([(-b - math.sqrt(D)) / (2 * a), (-b + math.sqrt(D)) / (2 * a)])

GRID = sorted({F(n, d) for n in range(-40, 41) for d in (1, 2, 3, 4)})

# ================================================================ MODULE 1
D = "m1"

# 01 Algebra · Linear equations in one variable · easy
a, b, c = 7, 12, 51
x = F(c + b, a)
assert ev("7x − 12", x=x) == 51 and all(ev("7x − 12", x=g) != 51 for g in GRID if g != x)
mc(D, ALG, "Linear equations in one variable", "easy", f"{a}x − {b} = {c}\n\nWhat is the solution to the given equation?", x,
   [F(c - b, a), c + b, F(c, a) + b],
   f"Add {b} to both sides to get {a}x = {c + b}. Then divide both sides by {a}: x = {fmt(x)}.", pos=1)

# 02 PSDA · Ratios, rates · easy · grid-in
rate, gain = 450, 1575
hrs = F(gain, rate)
assert rate * 3.5 == gain and hrs == F(7, 2)
spr(D, PSDA, "Ratios, rates, proportional relationships, and units", "easy",
    f"A hiker on a mountain trail gains elevation at a constant rate of {rate} feet per hour. At this rate, how many hours will it take the hiker to gain {commas(str(gain))} feet of elevation?",
    hrs, f"Divide the elevation gain by the rate: {commas(str(gain))} ÷ {rate} = {fmt(hrs, True)} hours.", dec=True)

# 03 Advanced Math · Equivalent expressions · easy
ch = ["6x² − 5", "6x² − 15", "6x² − 5x", "6x² − 15x"]
assert same_poly(ch[3], "3*x*(2*x - 5)") and not any(same_poly(c_, "3*x*(2*x - 5)") for c_ in ch[:3])
mct(D, ADV, "Equivalent expressions", "easy", "Which expression is equivalent to 3x(2x − 5)?", ch, 3,
    "Multiply 3x by each term in the parentheses: 3x(2x) = 6x² and 3x(−5) = −15x. So 3x(2x − 5) = 6x² − 15x.")

# 04 Geometry · Lines, angles, and triangles · easy · grid-in
pqs = 58; sqr = 180 - pqs
assert sqr + pqs == 180 and sqr == 122
spr(D, GEO, "Lines, angles, and triangles", "easy",
    f"Points P, Q, and R lie on a line, with Q between P and R. Point S does not lie on the line. The measure of angle PQS is {pqs}°. What is the measure, in degrees, of angle SQR?",
    sqr, f"Angles PQS and SQR together form the straight angle PQR, so their measures add to 180°: 180 − {pqs} = {sqr}.")

# 05 Algebra · Linear functions · easy
ch = ["M(d) = 240d + 45", "M(d) = 45d + 240", "M(d) = 285d", "M(d) = 45d − 240"]
truth = lambda d: 240 + 45 * d
assert all(ev(rhs(ch[1]), d=d) == truth(d) for d in range(0, 20))
assert all(any(ev(rhs(c_), d=d) != truth(d) for d in range(0, 20)) for i, c_ in enumerate(ch) if i != 1)
mct(D, ALG, "Linear functions", "easy",
    "Priya has streamed 240 minutes of a documentary series so far this month. She plans to stream 45 minutes of the series each day for the rest of the month. Which function M gives the total number of minutes of the series Priya will have streamed this month after d more days?",
    ch, 1, "Priya starts with 240 minutes, and each day adds 45 minutes, so after d days she will have streamed 240 + 45d minutes: M(d) = 45d + 240.")

# 06 PSDA · Percentages · easy
n, p = 360, 35
k = F(n * p, 100)
assert k == 126 and abs(0.35 * 360 - 126) < 1e-9
mc(D, PSDA, "Percentages", "easy",
   f"A greenhouse has {n} seedlings, and {p}% of them are tomato seedlings. How many of the seedlings in the greenhouse are tomato seedlings?", k,
   [n - k, n - p, F(n * p, 10)], f"{p}% of {n} is 0.{p} × {n} = {k}.", pos=0)

# 07 Advanced Math · Nonlinear functions · easy
f = "3x² − 2x + 4"
k = ev(f, x=-2)
assert k == 20 and 3 * 4 + 4 + 4 == k
mc(D, ADV, "Nonlinear functions", "easy", f"The function f is defined by f(x) = {f}. What is the value of f(−2)?", k,
   [ev(f, x=2), 3 * (-4) + 4 + 4, (3 * -2) ** 2 + 4 + 4],
   "Substitute x = −2: f(−2) = 3(−2)² − 2(−2) + 4 = 3(4) + 4 + 4 = 20.", pos=2)

# 08 Algebra · Systems of two linear equations · medium
tot, ps, pg, money = 310, 8, 14, 3500
s = F(pg * tot - money, pg - ps)
brute = [st for st in range(tot + 1) if ps * st + pg * (tot - st) == money]
assert brute == [s] == [140]
mc(D, ALG, "Systems of two linear equations", "medium",
   f"A community theater sold {tot} tickets for one performance. Student tickets cost ${ps} each, and general admission tickets cost ${pg} each. The theater collected a total of ${commas(str(money))} from these ticket sales. How many student tickets did the theater sell?", s,
   [tot - s, F(money, pg), F(tot, 2)],
   f"Let s be the number of student tickets and g the number of general admission tickets. Then s + g = {tot} and {ps}s + {pg}g = {commas(str(money))}. Substituting g = {tot} − s gives {ps}s + {commas(str(pg * tot))} − {pg}s = {commas(str(money))}, so −{pg - ps}s = −{pg * tot - money} and s = {s}.", pos=0)

# 09 Advanced Math · Equivalent expressions · medium
ch = ["6x² − 20", "6x² − 7x − 20", "6x² + 23x − 20", "6x² + 7x − 20"]
orig = "(3x − 4)(2x + 5)"
assert same_poly(ch[3], orig) and not any(same_poly(c_, orig) for c_ in ch[:3])
mct(D, ADV, "Equivalent expressions", "medium", f"Which expression is equivalent to {orig}?", ch, 3,
    "Multiply each term of the first factor by each term of the second: (3x)(2x) + (3x)(5) + (−4)(2x) + (−4)(5) = 6x² + 15x − 8x − 20 = 6x² + 7x − 20.")

# 10 Algebra · Linear equations in two variables · medium · grid-in
pb, pq, earned, nb = 9, 6, 792, 48
q = F(earned - pb * nb, pq)
assert [qq for qq in range(0, 200) if pb * nb + pq * qq == earned] == [q] == [60]
spr(D, ALG, "Linear equations in two variables", "medium",
    f"A food truck sells burritos for ${pb} each and quesadillas for ${pq} each. The equation {pb}b + {pq}q = {earned} represents a day on which the truck earned ${earned} from selling b burritos and q quesadillas. If the truck sold {nb} burritos that day, how many quesadillas did it sell?",
    q, f"Substitute b = {nb}: {pb}({nb}) + {pq}q = {earned}, so {pb * nb} + {pq}q = {earned}. Then {pq}q = {earned - pb * nb} and q = {q}.")

# 11 PSDA · One-variable data · medium
freq = {2: 6, 4: 5, 6: 3, 8: 6}
data = [v for v, c_ in freq.items() for _ in range(c_)]
mean = F(sum(v * c_ for v, c_ in freq.items()), sum(freq.values()))
assert len(data) == 20 and abs(statistics.mean(data) - float(mean)) < 1e-12 and mean == F(49, 10)
assert statistics.median(data) == 4
mc(D, PSDA, "One-variable data: distributions and measures of center and spread", "medium",
   "What is the mean length, in miles, of these trails?", mean,
   [statistics.median(data), F(sum(freq), len(freq)), F(sum(data), len(freq))],
   f"The total length of the trails is 2(6) + 4(5) + 6(3) + 8(6) = 12 + 20 + 18 + 48 = {sum(data)} miles. Dividing by the 20 trails gives {sum(data)}/20 = {fmt(mean, True)} miles.",
   pos=1, dec=True,
   passage="Trail length (miles)   Number of trails\n2                      6\n4                      5\n6                      3\n8                      6\n\nThe table shows the distribution of the lengths of the 20 hiking trails in a state park.")

# 12 Advanced Math · Nonlinear equations in one variable · medium · grid-in
eq = "2x² − 7x − 15 = 0"
roots = real_roots(2, -7, -15)
assert roots == [F(-3, 2), 5] and all(ev(eq.split("=")[0], x=r) == 0 for r in roots)
spr(D, ADV, "Nonlinear equations in one variable", "medium", f"{eq}\n\nWhat is the positive solution to the given equation?", max(roots),
    "Factor the left side: (2x + 3)(x − 5) = 0. So 2x + 3 = 0, giving x = −3/2, or x − 5 = 0, giving x = 5. The positive solution is 5.")

# 13 Algebra · Linear inequalities · medium
ch = ["18 + 6.5h ≤ 70", "6.5 + 18h ≥ 70", "18h + 6.5h ≥ 70", "18 + 6.5h ≥ 70"]
hs = [F(i, 4) for i in range(0, 80)]
meets = lambda h: 18 + F(13, 2) * h >= 70
assert all(ev(ch[3], h=h) == meets(h) for h in hs)
assert all(any(ev(c_, h=h) != meets(h) for h in hs) for c_ in ch[:3])
mct(D, ALG, "Linear inequalities", "medium",
    "A construction crew is pouring concrete for a building's foundation. The crew has already poured 18 cubic yards of concrete and will pour 6.5 cubic yards per hour from now on. The foundation requires at least 70 cubic yards of concrete. Which inequality represents all possible numbers of additional hours, h, the crew could pour concrete to meet this requirement?",
    ch, 3, "After h more hours, the crew will have poured the 18 cubic yards already poured plus 6.5h cubic yards, for a total of 18 + 6.5h. This total must be at least 70 cubic yards, so 18 + 6.5h ≥ 70.")

# 14 Geometry · Area and volume · medium
L, W, depth_in = 12, F(9, 2), 8
vol = L * W * F(depth_in, 12)
assert vol == 36 and abs(12 * 4.5 * (8 / 12) - 36) < 1e-9
mc(D, GEO, "Area and volume", "medium",
   f"A rectangular planting bed in a greenhouse is {L} feet long and 4.5 feet wide. The bed is filled with soil to a depth of {depth_in} inches. What is the volume of the soil, in cubic feet? (12 inches = 1 foot)", vol,
   [L * W * F(8, 10), L * W, L * W * depth_in],
   f"A depth of {depth_in} inches is {depth_in}/12 = 2/3 foot. The volume is length × width × depth = 12 × 4.5 × 2/3 = {vol} cubic feet.", pos=0, dec=True)

# 15 Advanced Math · Nonlinear functions · medium
h2 = 12 * F(5, 4) ** 2
assert h2 == F(75, 4) and abs(ev("12(1.25)^2") - 18.75) < 1e-9
mc(D, ADV, "Nonlinear functions", "medium",
   "The function h models the height, in centimeters, of a vine growing in a greenhouse t weeks after it was planted, where h(t) = 12(1.25)^t. According to the model, what is the height of the vine, in centimeters, 2 weeks after it was planted?", h2,
   [15, 12 + 2 * 3, 12 * F(5, 2)],
   "Substitute t = 2: h(2) = 12(1.25)² = 12(1.5625) = 18.75 centimeters.", pos=2, dec=True)

# 16 PSDA · Probability · medium · grid-in
tbl = {("Orchestra", "Adult"): 90, ("Orchestra", "Student"): 44, ("Balcony", "Adult"): 30, ("Balcony", "Student"): 36}
tickets = [k_ for k_, c_ in tbl.items() for _ in range(c_)]
stud = [t for t in tickets if t[1] == "Student"]
pr = F(sum(t[0] == "Balcony" for t in stud), len(stud))
assert len(tickets) == 200 and pr == F(36, 80) == F(9, 20)
spr(D, PSDA, "Probability and conditional probability", "medium",
    "If one of the student tickets is selected at random, what is the probability that it is for a balcony seat?", pr,
    f"There are 44 + 36 = {len(stud)} student tickets, and 36 of them are for balcony seats. The probability is 36/{len(stud)} = {fmt(pr)}.",
    passage="             Adult   Student\nOrchestra    90      44\nBalcony      30      36\n\nThe table shows the numbers of adult and student tickets sold for orchestra seats and balcony seats for the opening night of a play at a theater.")

# 17 Algebra · Linear equations in one variable · hard
ch = ["a = 4 and c = −12", "a = 4 and c = 12", "a = 7 and c = −12", "a = 10 and c = 12"]
def n_solutions(a_, c_):
    # ax + 3(x − 4) = 7x + c  ->  (a + 3 − 7)x = c + 12 ; count solutions on a grid, then by rule
    hits = sum(1 for g in GRID if a_ * g + 3 * (g - 4) == 7 * g + c_)
    rule = ("inf" if c_ + 12 == 0 else 0) if a_ + 3 == 7 else 1
    assert (rule == 0 and hits == 0) or (rule == "inf" and hits == len(GRID)) or (rule == 1 and hits <= 1)
    return rule
got = [n_solutions(int(s_.split()[2]), int(neg(s_.split()[-1]).replace("−", "-"))) for s_ in ch]
assert got == ["inf", 0, 1, 1]
mct(D, ALG, "Linear equations in one variable", "hard",
    "ax + 3(x − 4) = 7x + c\n\nIn the given equation, a and c are constants. The equation has no solution. Which of the following could be the values of a and c?",
    ch, 1, "Distributing and combining like terms gives (a + 3)x − 12 = 7x + c. The equation has no solution when the x-terms on the two sides are equal but the constant terms are not. So a + 3 = 7, which means a = 4, and c ≠ −12. Of the choices, only a = 4 and c = 12 meets both conditions. (If a = 4 and c = −12, the equation has infinitely many solutions.)")

# 18 Advanced Math · Systems of equations in two variables · hard
pts = [(x_, x_ + 7) for x_ in range(-50, 51) if x_ * x_ - 2 * x_ - 3 == x_ + 7]
xs = real_roots(1, -3, -10)
assert [p_[0] for p_ in pts] == xs == [-2, 5]
bd = sum(p_[1] for p_ in pts)
assert bd == 17 and bd == sum(xs) + 14
mc(D, ADV, "Systems of equations in two variables", "hard",
   "In the xy-plane, the graph of y = x² − 2x − 3 intersects the graph of y = x + 7 at two points, (a, b) and (c, d). What is the value of b + d?", bd,
   [sum(xs), pts[1][1], pts[0][1] * pts[1][1]],
   "Setting the expressions for y equal gives x² − 2x − 3 = x + 7, or x² − 3x − 10 = 0. This factors as (x − 5)(x + 2) = 0, so the x-coordinates are 5 and −2. Using y = x + 7, the y-coordinates are 12 and 5. So b + d = 12 + 5 = 17.", pos=2)

# 19 Algebra · Systems of two linear equations · hard · grid-in
x_, y_ = solve2(3, 5, 7, 5, 3, 25)
assert (x_, y_) == (F(13, 2), F(-5, 2)) and 3 * x_ + 5 * y_ == 7 and 5 * x_ + 3 * y_ == 25
assert F(7 + 25, 8) == x_ + y_ == 4
spr(D, ALG, "Systems of two linear equations", "hard",
    "3x + 5y = 7\n5x + 3y = 25\n\nIf (x, y) is the solution to the given system of equations, what is the value of x + y?", x_ + y_,
    "Adding the two equations gives 8x + 8y = 32. Dividing both sides by 8 gives x + y = 4. (Solving the system completely gives x = 13/2 and y = −5/2, whose sum is also 4.)")

# 20 Geometry · Right triangles and trigonometry · hard
J = math.asin(20 / 29); Lang = math.pi / 2 - J
key = F(21, 20)
assert abs(math.tan(Lang) - float(key)) < 1e-12 and 29 ** 2 - 20 ** 2 == 21 ** 2
mc(D, GEO, "Right triangles and trigonometry", "hard",
   "In right triangle JKL, angle K is the right angle, and sin J = 20/29. What is the value of tan L?", key,
   [F(20, 21), F(21, 29), F(20, 29)],
   "sin J = (side opposite J)/(hypotenuse) = KL/JL = 20/29, so the sides can be taken as KL = 20 and JL = 29. By the Pythagorean theorem, JK = √(29² − 20²) = √441 = 21. For angle L, the opposite side is JK and the adjacent side is KL, so tan L = 21/20.", pos=3)

# 21 Advanced Math · Nonlinear equations in one variable · hard
eq = "x/(x − 3) + 4/(x + 1) = 12/((x − 3)(x + 1))"
def holds(x0):
    try: return abs(ev(eq.split("=")[0], x=x0) - ev(eq.split("=")[1], x=x0)) < 1e-12
    except ZeroDivisionError: return False
sols = [g for g in GRID if holds(g)]
assert sols == [-8] and real_roots(1, 5, -24) == [-8, 3]
mc(D, ADV, "Nonlinear equations in one variable", "hard", f"{eq}\n\nWhat is the solution to the given equation?", -8,
   [-3, 3, 8],
   "Multiply both sides by (x − 3)(x + 1): x(x + 1) + 4(x − 3) = 12. This simplifies to x² + 5x − 24 = 0, which factors as (x + 8)(x − 3) = 0. The value x = 3 makes two denominators 0, so it is not a solution. The only solution is −8.", pos=0)

# 22 Algebra · Linear functions · hard
t1, e1, t2, e2 = 20, 6340, 55, 5570
m = F(e2 - e1, t2 - t1)
e0 = e1 - m * t1
assert m == -22 and e0 == 6780
assert all(e0 + m * t == e for t, e in ((t1, e1), (t2, e2)))
mc(D, ALG, "Linear functions", "hard",
   f"A hiker's elevation, in feet, during a descent is a linear function of the number of minutes since the descent began. The hiker's elevation was {commas(str(e1))} feet {t1} minutes after the descent began and {commas(str(e2))} feet {t2} minutes after the descent began. What was the hiker's elevation, in feet, when the descent began?", e0,
   [e1 + m * t1, e1, e1 - (e2 - e1)],
   f"The rate of change is ({commas(str(e2))} − {commas(str(e1))})/({t2} − {t1}) = −770/35 = −22 feet per minute. The descent began {t1} minutes before the elevation was {commas(str(e1))} feet, so the starting elevation was {commas(str(e1))} + 22({t1}) = {commas(str(e1))} + 440 = {commas(str(int(e0)))} feet.", pos=2)

# ================================================================ MODULE 2
D = "m2"

# 01 Algebra · Linear equations in two variables · easy
k = ev("3x − 7", x=4)
assert k == 5 and 5 == 3 * 4 - 7
mc(D, ALG, "Linear equations in two variables", "easy",
   "y = 3x − 7\n\nThe graph of the given equation in the xy-plane passes through the point (4, k). What is the value of k?", k,
   [-k, 3 * 4, 3 * 4 + 7], "Substitute x = 4 and y = k: k = 3(4) − 7 = 12 − 7 = 5.", pos=1)

# 02 PSDA · Percentages · easy · grid-in
last, pct = 1250, 18
now = F(last * (100 + pct), 100)
assert now == 1475 and last + last * 18 // 100 == 1475
spr(D, PSDA, "Percentages", "easy",
    f"Last month, Dev streamed {commas(str(last))} minutes of video. This month, he streamed {pct}% more minutes of video than he did last month. How many minutes of video did Dev stream this month?", now,
    f"An increase of {pct}% multiplies the amount by 1.{pct}: 1.{pct} × {commas(str(last))} = {commas(str(int(now)))} minutes.")

# 03 Advanced Math · Equivalent expressions · easy
orig = "(5x² − 2x + 7) − (3x² − 6x + 1)"
ch = ["2x² − 8x + 6", "2x² + 4x + 8", "2x² + 4x + 6", "8x² − 8x + 8"]
assert same_poly(ch[2], orig) and not any(same_poly(c_, orig) for i, c_ in enumerate(ch) if i != 2)
mct(D, ADV, "Equivalent expressions", "easy", f"Which expression is equivalent to {orig}?", ch, 2,
    "Distribute the subtraction to every term of the second polynomial: 5x² − 2x + 7 − 3x² + 6x − 1. Combining like terms gives 2x² + 4x + 6.")

# 04 Algebra · Linear inequalities · easy
ch = ["175b ≥ 2,400", "2,400b ≤ 175", "b + 175 ≤ 2,400", "175b ≤ 2,400"]
safe = lambda b_: 175 * b_ <= 2400
assert all(ev(ch[3], b=b_) == safe(b_) for b_ in range(0, 40))
assert all(any(ev(c_, b=b_) != safe(b_) for b_ in range(0, 40)) for c_ in ch[:3])
mct(D, ALG, "Linear inequalities", "easy",
    "A crane at a construction site can safely lift at most 2,400 pounds at one time. Each steel beam the crane lifts weighs 175 pounds. Which inequality represents the possible numbers of beams, b, the crane can safely lift at one time?",
    ch, 3, "The total weight of b beams is 175b pounds. \"At most 2,400\" means the total weight must be less than or equal to 2,400, so 175b ≤ 2,400.")

# 05 Advanced Math · Nonlinear functions · medium
b0 = ev("(x − 4)(x + 6)", x=0)
assert b0 == -24 == (-4) * 6
mc(D, ADV, "Nonlinear functions", "medium",
   "In the xy-plane, the graph of y = (x − 4)(x + 6) intersects the y-axis at the point (0, b). What is the value of b?", b0,
   [-4 - 6, -4 + 6, 24], "The graph intersects the y-axis where x = 0. Substituting x = 0 gives y = (0 − 4)(0 + 6) = (−4)(6) = −24, so b = −24.", pos=0)

# 06 Algebra · Linear equations in one variable · medium · grid-in
eq = "(2/3)(x − 6) = (1/4)x + 1"
xs = [g for g in GRID if ev(eq.split("=")[0], x=g) == ev(eq.split("=")[1], x=g)]
assert xs == [12] and F(60, 5) == 12
spr(D, ALG, "Linear equations in one variable", "medium", f"{eq}\n\nWhat is the value of x?", 12,
    "Multiply both sides by 12 to clear the fractions: 8(x − 6) = 3x + 12. Then 8x − 48 = 3x + 12, so 5x = 60 and x = 12.")

# 07 Geometry · Lines, angles, and triangles · medium
post, sh1, sh2 = 6, F(9, 2), 63
h = post * sh2 / sh1
assert h == 84 and abs(84 / 63 - 6 / 4.5) < 1e-12
mc(D, GEO, "Lines, angles, and triangles", "medium",
   f"At a construction site, a vertical fence post that is {post} feet tall casts a shadow 4.5 feet long. At the same time, a vertical crane tower casts a shadow {sh2} feet long. The triangle formed by the post and its shadow is similar to the triangle formed by the tower and its shadow. What is the height, in feet, of the crane tower?", h,
   [sh2 * sh1 / post, sh2 + (post - sh1), post * sh2],
   f"Corresponding sides of similar triangles are proportional, so height/{sh2} = {post}/4.5. Then height = {sh2} × {post}/4.5 = {sh2} × 4/3 = {h} feet.", pos=2, dec=True)

# 08 Algebra · Linear functions · medium
assert ev("6.5n − 180", n=0) == -180 and ev("6.5n − 180", n=1) - ev("6.5n − 180", n=0) == 6.5
mct(D, ALG, "Linear functions", "medium",
    "P(n) = 6.5n − 180\n\nThe function P gives the profit, in dollars, that a food truck makes on a certain day from selling n meals. Which of the following is the best interpretation of the number 180 in this context?",
    ["The truck loses $180 on the day if it sells no meals.", "The truck earns $180 in profit for each meal it sells.",
     "The truck must sell 180 meals to make a profit.", "The truck's maximum possible profit for the day is $180."], 0,
    "When n = 0, P(0) = 6.5(0) − 180 = −180. So if the truck sells no meals, its profit is −$180; that is, it loses $180 (for example, the day's fixed costs). The profit per meal is 6.5 dollars, not 180.")

# 09 PSDA · Two-variable data · medium
diff = ev("2.4x + 15", x=10) - ev("2.4x + 15", x=5)
assert abs(diff - 12) < 1e-9 and abs(5 * 2.4 - 12) < 1e-9
mc(D, PSDA, "Two-variable data: models and scatterplots", "medium",
   "A greenhouse manager measured the heights of 30 pepper plants at various times after planting. The line of best fit for the data is y = 2.4x + 15, where y is the predicted height, in centimeters, of a plant x days after planting. According to the line of best fit, how many centimeters taller is a plant predicted to be 10 days after planting than 5 days after planting?", 12,
   [F(12, 5), 27, 39],
   "The predicted heights are 2.4(10) + 15 = 39 centimeters at 10 days and 2.4(5) + 15 = 27 centimeters at 5 days. The difference is 39 − 27 = 12 centimeters. (Equivalently, 5 more days times the slope, 2.4 centimeters per day, is 12.)", pos=1, dec=True)

# 10 Advanced Math · Equivalent expressions · medium
orig = "(x² − 9)/(x² + 5x + 6)"
ch = ["(x + 3)/(x + 2)", "(x − 3)/(x + 3)", "−9/(5x + 6)", "(x − 3)/(x + 2)"]
pts_ = (1, 2, 4, 7, 10)
assert same_poly(ch[3], orig, pts=pts_) and not any(same_poly(c_, orig, pts=pts_) for c_ in ch[:3])
mct(D, ADV, "Equivalent expressions", "medium", f"Which expression is equivalent to {orig}, for x > 0?", ch, 3,
    "Factor the numerator and the denominator: x² − 9 = (x − 3)(x + 3) and x² + 5x + 6 = (x + 2)(x + 3). Dividing out the common factor x + 3 leaves (x − 3)/(x + 2).")

# 11 Algebra · Systems of two linear equations · medium
r_, c2 = solve2(1, 1, 15, 7, 4, 84)
assert (r_, c2) == (8, 7) and r_ / 2 + c2 / F(7, 2) == 6
assert [r for r in range(16) if F(r, 2) + F(15 - r) / F(7, 2) == 6] == [8]
mc(D, ALG, "Systems of two linear equations", "medium",
   "Maya hiked the Ridge Trail and then the Creek Trail, a total distance of 15 miles. Her average speed was 2 miles per hour on the Ridge Trail and 3.5 miles per hour on the Creek Trail, and the entire hike took 6 hours. How many miles long is the Ridge Trail?", r_,
   [c2, 6, r_ / 2],
   "Let r and c be the lengths, in miles, of the Ridge Trail and the Creek Trail. Then r + c = 15, and the times add to 6 hours: r/2 + c/3.5 = 6. Multiplying the second equation by 14 gives 7r + 4c = 84. Substituting c = 15 − r gives 7r + 60 − 4r = 84, so 3r = 24 and r = 8.", pos=3)

# 12 PSDA · Inference · medium
lo, hi = 94 - 7, 94 + 7
opts = [80, 99, 103, 108]
assert [o for o in opts if lo <= o <= hi] == [99]
mc(D, PSDA, "Inference from sample statistics and margin of error", "medium",
   "A random sample of 250 subscribers to a streaming service found that the mean time the subscribers spent streaming each day was 94 minutes, with an associated margin of error of 7 minutes. Based on these results, which of the following is a plausible value for the mean daily streaming time, in minutes, of all the service's subscribers?", 99,
   [80, 103, 108],
   f"The plausible values for the mean daily streaming time of all subscribers run from 94 − 7 = {lo} minutes to 94 + 7 = {hi} minutes. Of the choices, only 99 falls in this interval.", pos=1)

# 13 Algebra · Linear inequalities · medium · grid-in
budget, fee, per = 1500, 260, F(7, 2)
mx = int((budget - fee) / per)
assert mx == 354 and fee + per * mx <= budget < fee + per * (mx + 1)
assert max(m_ for m_ in range(1000) if 260 + 3.5 * m_ <= 1500) == mx
spr(D, ALG, "Linear inequalities", "medium",
    f"A food truck owner has a budget of ${commas(str(budget))} for a weekend festival. The owner must pay a booth fee of ${fee}, and the ingredients for each meal cost $3.50. What is the maximum number of meals the owner can buy ingredients for without going over the budget?", mx,
    f"For m meals, the cost is 260 + 3.5m, which must be at most 1,500. So 3.5m ≤ 1,240, and m ≤ 1,240/3.5 ≈ 354.3. The number of meals must be a whole number, so the maximum is {mx}.")

# 14 Advanced Math · Nonlinear equations in one variable · hard
eq = "√(3x + 10) = x + 2"
cands = real_roots(1, 1, -6)
good = [c_ for c_ in cands if abs(ev(eq.split("=")[0], x=c_) - ev(eq.split("=")[1], x=c_)) < 1e-12]
assert cands == [-3, 2] and good == [2]
assert [g for g in GRID if 3 * g + 10 >= 0 and abs(math.sqrt(3 * g + 10) - (g + 2)) < 1e-12] == [2]
mc(D, ADV, "Nonlinear equations in one variable", "hard", f"{eq}\n\nWhat is the solution to the given equation?", 2,
   [-3, -2, 3],
   "Square both sides: 3x + 10 = x² + 4x + 4, so x² + x − 6 = 0, which factors as (x + 3)(x − 2) = 0. Check each value in the original equation. For x = −3, the left side is √1 = 1 but the right side is −1, so −3 is not a solution. For x = 2, both sides equal 4. The solution is 2.", pos=2)

# 15 Algebra · Linear equations in two variables · hard
ch = ["y = (2/3)x + 25/3", "y = −(3/2)x + 10", "y = −(3/2)x + 4", "y = (3/2)x + 10"]
given_slope = F(4, 6)
def line_ok(s_):
    slope = ev(rhs(s_), x=1) - ev(rhs(s_), x=0)
    return abs(slope * float(given_slope) + 1) < 1e-9 and abs(ev(rhs(s_), x=-2) - 7) < 1e-9
assert [line_ok(c_) for c_ in ch] == [False, False, True, False]
mct(D, ALG, "Linear equations in two variables", "hard",
    "In the xy-plane, line p passes through the point (−2, 7) and is perpendicular to the graph of 4x − 6y = 9. Which equation defines line p?",
    ch, 2, "Solving 4x − 6y = 9 for y gives y = (2/3)x − 3/2, so that line has slope 2/3. A perpendicular line has slope −3/2, the negative reciprocal. Substituting (−2, 7) into y = −(3/2)x + b gives 7 = 3 + b, so b = 4 and line p is y = −(3/2)x + 4.")

# 16 PSDA · Probability · hard
grid = {("A", "F"): 20, ("A", "N"): 60, ("B", "F"): 60, ("B", "N"): 40}
plants = [k_ for k_, c_ in grid.items() for _ in range(c_)]
flw = [p_ for p_ in plants if p_[1] == "F"]
pr = F(sum(p_[0] == "B" for p_ in flw), len(flw))
assert len(plants) == 180 and pr == F(3, 4)
mc(D, PSDA, "Probability and conditional probability", "hard",
   "If one of the plants that flowered is selected at random, what is the probability that it is a Variety B plant?", pr,
   [F(60, 180), F(80, 180), F(60, 100)],
   "A total of 20 + 60 = 80 plants flowered, and 60 of them are Variety B. So the probability is 60/80 = 3/4.", pos=3,
   passage="             Flowered   Did not flower\nVariety A    20         60\nVariety B    60         40\n\nA greenhouse grew 180 orchid plants of two varieties. The table shows how many plants of each variety flowered during their first year.")

# 17 Advanced Math · Nonlinear functions · hard
half = F(6, 5)
assert half * half == F(144, 100) and abs(1.44 ** 0.5 - 1.2) < 1e-12
assert abs(180 * 1.44 ** 2.5 - 180 * 1.2 ** 5) < 1e-6
mc(D, ADV, "Nonlinear functions", "hard",
   "M(t) = 180(1.44)^t\n\nThe function M models the number of members of a hiking club t years after the club was founded. According to the model, by what percent does the number of members increase every 6 months?", 20,
   [22, 44, 88],
   "Six months is half a year, so every 6 months the number of members is multiplied by (1.44)^(1/2) = 1.2. (Equivalently, M(t) = 180(1.2)^(2t).) Multiplying by 1.2 is a 20% increase.", pos=0)

# 18 Geometry · Circles · hard · grid-in
eq = "x² + y² + 10x − 4y − 7 = 0"
hx, ky, r2 = -5, 2, 7 + 25 + 4
assert r2 == 36
for th in range(0, 360, 15):
    px, py = hx + 6 * math.cos(math.radians(th)), ky + 6 * math.sin(math.radians(th))
    assert abs(ev(eq.split("=")[0], x=px, y=py)) < 1e-9
assert abs(ev(eq.split("=")[0], x=hx + 5, y=ky)) > 1
spr(D, GEO, "Circles", "hard", f"{eq}\n\nIn the xy-plane, the graph of the given equation is a circle. What is the length of the circle's diameter?", 2 * math.isqrt(r2),
    "Complete the square in x and in y: (x² + 10x + 25) + (y² − 4y + 4) = 7 + 25 + 4, so (x + 5)² + (y − 2)² = 36. The radius is √36 = 6, so the diameter is 2(6) = 12.")

# 19 Algebra · Linear functions · hard · grid-in
a1, c1, a2, c2_ = 400, 3160, 650, 4760
m = F(c2_ - c1, a2 - a1); b_ = c1 - m * a1
cost = m * 520 + b_
assert (m, b_, cost) == (F(32, 5), 600, 3928)
assert cost == c1 + (c2_ - c1) * F(520 - a1, a2 - a1)
spr(D, ALG, "Linear functions", "hard",
    f"A construction company's price for pouring a concrete driveway is a linear function of the driveway's area. The price is ${commas(str(c1))} for a {a1}-square-foot driveway and ${commas(str(c2_))} for a {a2}-square-foot driveway. What is the price, in dollars, for a 520-square-foot driveway?", cost,
    f"The rate of change is ({commas(str(c2_))} − {commas(str(c1))})/({a2} − {a1}) = 1,600/250 = 6.4 dollars per square foot. Then {commas(str(c1))} = 6.4({a1}) + b = 2,560 + b, so b = {b_}. The price for 520 square feet is 6.4(520) + 600 = 3,328 + 600 = 3,928 dollars.")

# 20 Advanced Math · Nonlinear equations in one variable · hard · grid-in
# (replaces an x² − 10x + c item that turned out to match another writer's pt1-m2-17)
eq = "9^(x + 1) = 27^(x − 1)"
xs = [g for g in range(-30, 31) if F(9) ** (g + 1) == F(27) ** (g - 1)]  # exact, integers
assert [g for g in GRID if abs(math.log(9) * (g + 1) - math.log(27) * (g - 1)) < 1e-12] == xs
assert xs == [5] and 9 ** 6 == 27 ** 4 == 3 ** 12 and ev(eq.split("=")[0], x=5) == ev(eq.split("=")[1], x=5)
spr(D, ADV, "Nonlinear equations in one variable", "hard", f"{eq}\n\nWhat is the value of x?", 5,
    "Write both sides as powers of 3: 9^(x + 1) = (3²)^(x + 1) = 3^(2x + 2) and 27^(x − 1) = (3³)^(x − 1) = 3^(3x − 3). The exponents must be equal, so 2x + 2 = 3x − 3, and x = 5. Check: 9⁶ and 27⁴ both equal 3¹², which is 531,441.")

# 21 Geometry · Right triangles and trigonometry · hard
xs = [x0 for x0 in range(-50, 100) if 0 < 3 * x0 + 10 < 90 and 0 < 2 * x0 + 15 < 90
      and abs(math.sin(math.radians(3 * x0 + 10)) - math.cos(math.radians(2 * x0 + 15))) < 1e-12]
assert xs == [13]
mc(D, GEO, "Right triangles and trigonometry", "hard",
   "sin((3x + 10)°) = cos((2x + 15)°)\n\nIn the given equation, the angle measures (3x + 10)° and (2x + 15)° are each between 0° and 90°. What is the value of x?", 13,
   [5, 31, 65],
   "For acute angles, the sine of one angle equals the cosine of another exactly when the two angles are complementary. So (3x + 10) + (2x + 15) = 90, which gives 5x + 25 = 90, 5x = 65, and x = 13. Check: the angles are 49° and 41°, which add to 90°.", pos=1)

# 22 Advanced Math · Systems of equations in two variables · hard
one = [c_ for c_ in range(-50, 51) if len(real_roots(1, -6, 7 - c_)) == 1]
assert one == [-2]
mc(D, ADV, "Systems of equations in two variables", "hard",
   "In the xy-plane, the line y = 2x + c intersects the parabola y = x² − 4x + 7 at exactly one point, where c is a constant. What is the value of c?", -2,
   [2, 3, 6],
   "At an intersection point, x² − 4x + 7 = 2x + c, or x² − 6x + (7 − c) = 0. There is exactly one intersection point when this equation has exactly one real solution, that is, when its discriminant is 0: (−6)² − 4(1)(7 − c) = 0. So 36 − 28 + 4c = 0, 4c = −8, and c = −2.", pos=0)

# ================================================================ EXTRA BANK ITEMS
D = "bank"

# Algebra · Systems of two linear equations · hard
def all_on_line(a_):  # every grid point of 6x − 4y = 10 also satisfies 9x + ay = 15?
    return all(9 * g + a_ * (6 * g - 10) / 4 == 15 for g in GRID)
av = [a_ for a_ in range(-20, 21) if all_on_line(a_)]
assert av == [-6] and F(-4) * F(3, 2) == -6
mc(D, ALG, "Systems of two linear equations", "hard",
   "The system of equations 6x − 4y = 10 and 9x + ay = 15, where a is a constant, has infinitely many solutions. What is the value of a?", -6,
   [-4, 4, 6],
   "A system has infinitely many solutions when one equation is a multiple of the other. Since 9 = (3/2)(6) and 15 = (3/2)(10), the second equation must be 3/2 times the first, so a = (3/2)(−4) = −6.", pos=0)

# Algebra · Linear inequalities · medium
opts = [(100, 300), (150, 260), (200, 200), (250, 180)]
ok = [a_ + s_ <= 420 and 22 * a_ + 14 * s_ >= 7000 for a_, s_ in opts]
assert ok == [False, False, True, False]
mct(D, ALG, "Linear inequalities", "medium",
    "A theater has 420 seats. Adult tickets for a show cost $22 each, and student tickets cost $14 each. The theater wants to collect at least $7,000 from ticket sales for the show without selling more tickets than there are seats. Which of the following combinations of adult and student tickets meets both conditions?",
    [f"{a_} adult tickets and {s_} student tickets" for a_, s_ in opts], 2,
    "The conditions are a + s ≤ 420 and 22a + 14s ≥ 7,000. For 200 adult and 200 student tickets, 400 ≤ 420 and 22(200) + 14(200) = 7,200 ≥ 7,000, so both hold. The other choices each fail one condition: 100 and 300 collects 6,400 dollars; 150 and 260 collects 6,940 dollars; 250 and 180 is 430 tickets, more than 420.")

# Advanced Math · Systems of equations in two variables · medium · grid-in
sol = [(g, g * g + 4 * g - 5) for g in GRID if g * g + 4 * g - 5 == 2 * g + 3]
assert sol == [(-4, -5), (2, 7)]
spr(D, ADV, "Systems of equations in two variables", "medium",
    "y = x² + 4x − 5\ny = 2x + 3\n\nIf (x, y) is a solution to the given system of equations and x > 0, what is the value of y?", 7,
    "Setting the expressions for y equal gives x² + 4x − 5 = 2x + 3, or x² + 2x − 8 = 0, which factors as (x + 4)(x − 2) = 0. Since x > 0, x = 2, and y = 2(2) + 3 = 7.")

# Advanced Math · Systems of equations in two variables · medium
n_sol = len([g for g in GRID if g * g - 4 * g + 7 == 2 * g - 2])
assert n_sol == 1 and 6 * 6 - 4 * 9 == 0
mct(D, ADV, "Systems of equations in two variables", "medium",
    "y = x² − 4x + 7\ny = 2x − 2\n\nHow many solutions (x, y) does the given system of equations have?",
    ["Zero", "Exactly one", "Exactly two", "Infinitely many"], 1,
    "Setting the expressions for y equal gives x² − 4x + 7 = 2x − 2, or x² − 6x + 9 = 0. This factors as (x − 3)² = 0, so x = 3 is the only solution, and y = 2(3) − 2 = 4. The system has exactly one solution, (3, 4).")

# Advanced Math · Systems of equations in two variables · hard
sols = [(g, 7 - g) for g in GRID if g * g + (7 - g) ** 2 == 25]
assert sols == [(3, 4), (4, 3)] and {x0 * y0 for x0, y0 in sols} == {12} and F(49 - 25, 2) == 12
mc(D, ADV, "Systems of equations in two variables", "hard",
   "If (x, y) is a solution to the system of equations x + y = 7 and x² + y² = 25, what is the value of xy?", 12,
   [24, F(49 + 25, 2), 49],
   "Squaring both sides of x + y = 7 gives x² + 2xy + y² = 49. Substituting x² + y² = 25 gives 25 + 2xy = 49, so 2xy = 24 and xy = 12. (The solutions are (3, 4) and (4, 3), and xy = 12 for both.)", pos=0)

# PSDA · Percentages · medium · grid-in
may = 2400 * F(115, 100) * F(80, 100)
assert may == 2208 and abs(2400 * 1.15 * 0.8 - 2208) < 1e-9
spr(D, PSDA, "Percentages", "medium",
    "Viewers of a streaming channel watched 2,400 hours of its content in March. The number of hours watched in April was 15% greater than in March, and the number of hours watched in May was 20% less than in April. How many hours of the channel's content did viewers watch in May?", may,
    "April's total was 1.15 × 2,400 = 2,760 hours. May's total was 20% less than April's, or 0.80 × 2,760 = 2,208 hours.")

# PSDA · Two-variable data · easy
pred = ev("4.5x − 120", x=70)
assert pred == 195
mc(D, PSDA, "Two-variable data: models and scatterplots", "easy",
   "A park ranger recorded the high temperature x, in degrees Fahrenheit, and the number of hikers y who used a trail on each of 40 days. The line of best fit for the data is y = 4.5x − 120. According to the line of best fit, how many hikers are predicted to use the trail on a day when the high temperature is 70°F?", pred,
   [120, 4.5 * 70, 4.5 * 70 + 120],
   "Substitute x = 70 into the equation of the line of best fit: y = 4.5(70) − 120 = 315 − 120 = 195.", pos=1)

# PSDA · Two-variable data · medium
table = [(0, 1024), (1, 1280), (2, 1600), (3, 2000)]
ch = ["F(w) = 1,024 + 256w", "F(w) = 1,024(0.25)^w", "F(w) = 1,280(1.25)^w", "F(w) = 1,024(1.25)^w"]
fits = [all(abs(ev(rhs(c_), w=w) - v) < 1e-9 for w, v in table) for c_ in ch]
assert fits == [False, False, False, True]
mct(D, PSDA, "Two-variable data: models and scatterplots", "medium",
    "Which of the following functions best models the number of followers, F, w weeks after the food truck opened?",
    ch, 3, "Each week's number of followers is 1.25 times the previous week's: 1,280/1,024 = 1,600/1,280 = 2,000/1,600 = 1.25. The number of followers when the truck opened was 1,024, so F(w) = 1,024(1.25)^w. A linear model with slope 256 fits only the first two weeks.",
    passage="Week   Followers\n0      1,024\n1      1,280\n2      1,600\n3      2,000\n\nA food truck tracked the number of followers of its social media account for the first four weeks after it opened.")

# PSDA · Two-variable data · hard
dec2 = 100 * (1 - F(88, 100) ** 2)
assert dec2 == F(2256, 100) and abs((1 - 86000 * 0.88 ** 7 / (86000 * 0.88 ** 5)) * 100 - 22.56) < 1e-9
mc(D, PSDA, "Two-variable data: models and scatterplots", "hard",
   "A construction company fit the model V(x) = 86,000(0.88)^x to data on the resale value V, in dollars, of its excavators x years after purchase. According to the model, by what percent does the predicted value of an excavator decrease over any 2-year period?", dec2,
   [12, 24, F(7744, 100)],
   "Each year the predicted value is multiplied by 0.88, so over 2 years it is multiplied by (0.88)² = 0.7744. The value keeps 77.44% of what it was, so it decreases by 100 − 77.44 = 22.56%.", pos=1, dec=True)

# PSDA · Probability · easy · grid-in
pr = F(15, 250)
assert pr == F(3, 50) and abs(15 / 250 - 0.06) < 1e-12
spr(D, PSDA, "Probability and conditional probability", "easy",
    "A theater sold 250 raffle tickets at a fundraiser, and 15 of the tickets are winning tickets. If one of the 250 tickets is selected at random, what is the probability that it is a winning ticket?", pr,
    "15 of the 250 tickets are winning tickets, so the probability is 15/250 = 3/50.")

# PSDA · Probability · medium
hikes = {("Easy", "C"): 74, ("Easy", "T"): 6, ("Moderate", "C"): 60, ("Moderate", "T"): 20, ("Strenuous", "C"): 18, ("Strenuous", "T"): 22}
allh = [k_ for k_, c_ in hikes.items() for _ in range(c_)]
stren = [h_ for h_ in allh if h_[0] == "Strenuous"]
pr = F(sum(h_[1] == "T" for h_ in stren), len(stren))
assert len(allh) == 200 and pr == F(11, 20)
mc(D, PSDA, "Probability and conditional probability", "medium",
   "If one of the Strenuous hikes is selected at random, what is the probability that the group turned back before finishing?", pr,
   [F(22, 200), F(40, 200), F(22, 48)],
   "There were 18 + 22 = 40 Strenuous hikes, and the group turned back on 22 of them. The probability is 22/40 = 11/20.", pos=3,
   passage="             Completed   Turned back\nEasy         74          6\nModerate     60          20\nStrenuous    18          22\n\nA hiking club recorded whether each of its 200 group hikes last year was completed or turned back before finishing, by the difficulty of the trail.")

# PSDA · Probability · hard · grid-in
trays = ["B"] * 12 + ["M"] * 4
pairs = list(itertools.combinations(range(16), 2))
pr = F(sum(1 for i, j in pairs if "M" in (trays[i], trays[j])), len(pairs))
assert pr == F(9, 20) == 1 - F(12, 16) * F(11, 15)
spr(D, PSDA, "Probability and conditional probability", "hard",
    "A greenhouse worker will randomly select 2 of 16 seedling trays, without replacement, to inspect. Of the 16 trays, 12 contain basil seedlings and 4 contain mint seedlings. What is the probability that at least one of the 2 selected trays contains mint seedlings?", pr,
    "Find the probability that neither tray contains mint. The first tray is basil with probability 12/16, and then the second is basil with probability 11/15. So P(both basil) = (12/16)(11/15) = 132/240 = 11/20. The probability that at least one tray contains mint is 1 − 11/20 = 9/20.")

# PSDA · Inference · easy
est = F(45, 200) * 5000
assert est == 1125 and 5000 * 0.225 == 1125
mc(D, PSDA, "Inference from sample statistics and margin of error", "easy",
   "A state park selected a random sample of 200 of the 5,000 hikers who registered to use its trails this season. Of the hikers in the sample, 45 said they had seen a black bear on the trails. Based on the sample, which of the following is the best estimate of the number of the 5,000 registered hikers who had seen a black bear on the trails?", est,
   [F(45, 2), 45, 5000 - 45],
   "In the sample, 45/200 = 22.5% of the hikers had seen a black bear. Applying this proportion to all registered hikers gives 0.225 × 5,000 = 1,125.", pos=2, dec=True)

# PSDA · Inference · medium
lo, hi = F(565, 1000) * 6000, F(675, 1000) * 6000
opts = [186, 3200, 3720, 4200]
assert (lo, hi) == (3390, 4050) and [o for o in opts if lo <= o <= hi] == [3720]
mc(D, PSDA, "Inference from sample statistics and margin of error", "medium",
   "A theater surveyed a random sample of 300 of its 6,000 season subscribers. Of those surveyed, 62% said they would attend a new afternoon performance. The margin of error for this estimate is 5.5 percentage points. Based on the survey, which of the following is a plausible number of the theater's 6,000 season subscribers who would attend the afternoon performance?", 3720,
   [186, 3200, 4200],
   "The plausible percentages for all subscribers run from 62 − 5.5 = 56.5% to 62 + 5.5 = 67.5%. Applied to 6,000 subscribers, that is from 0.565 × 6,000 = 3,390 to 0.675 × 6,000 = 4,050. Of the choices, only 3,720 is in this range. (186 is 62% of the 300 people surveyed, not of all subscribers.)", pos=2)

# PSDA · Inference · hard
A_, B_ = (81 - 4, 81 + 4), (76 - 6, 76 + 6)
assert max(A_[0], B_[0]) <= min(A_[1], B_[1])  # intervals overlap -> no convincing difference
mct(D, PSDA, "Inference from sample statistics and margin of error", "hard",
    "A greenhouse tested seeds from two suppliers. In a random sample of seeds from Supplier A, 81% germinated, with an associated margin of error of 4 percentage points. In a random sample of seeds from Supplier B, 76% germinated, with an associated margin of error of 6 percentage points. Which of the following conclusions is best supported by these results?",
    ["The results do not provide convincing evidence that the germination rate of all of Supplier A's seeds is greater than that of all of Supplier B's seeds.",
     "The germination rate of all of Supplier A's seeds is greater than that of all of Supplier B's seeds.",
     "The germination rate of all of Supplier B's seeds is between 76% and 82%.",
     "The germination rate of all of Supplier A's seeds is exactly 81%."], 0,
    "The plausible germination rates for Supplier A run from 77% to 85%, and for Supplier B from 70% to 82%. The intervals overlap (both rates could be 80%, for example), so the samples do not show that A's rate is greater. B's interval is 70% to 82%, not 76% to 82%, and a sample percentage is an estimate, not an exact population value.")

# PSDA · Evaluating statistical claims · easy
mct(D, PSDA, "Evaluating statistical claims", "easy",
    "The owner of a food truck posted a poll on the truck's social media page asking followers whether the truck should add a vegetarian dish to its menu. Of the 412 followers who chose to respond, 71% said yes. Which of the following is the most appropriate conclusion?",
    ["About 71% of all the truck's customers want a vegetarian dish added to the menu.",
     "Adding a vegetarian dish will increase the truck's sales by 71%.",
     "Exactly 71% of the truck's social media followers want a vegetarian dish added to the menu.",
     "The poll results may not represent the truck's customers, because the people who responded chose to take part."], 3,
    "The respondents selected themselves rather than being chosen at random, so they may differ from customers in general (and from followers who did not respond). The poll therefore cannot support a conclusion about all customers or all followers, and it says nothing about sales.")

# PSDA · Evaluating statistical claims · hard
mct(D, PSDA, "Evaluating statistical claims", "hard",
    "A researcher selected 120 tomato plants at random from the 2,000 tomato plants in a greenhouse. Half of the 120 plants were randomly assigned to receive a new plant food, and the other half received none. The plants that received the plant food produced significantly more tomatoes, on average, than the plants that did not. Which of the following conclusions is best supported?",
    ["The plant food causes an increase in tomato production for all tomato plants everywhere.",
     "The plant food is associated with greater tomato production, but it cannot be said to cause the increase.",
     "No conclusion can be drawn, because not all 2,000 plants in the greenhouse were used.",
     "The plant food is likely to cause an increase in tomato production for tomato plants in this greenhouse."], 3,
    "Random assignment to the two groups allows a cause-and-effect conclusion, and because the 120 plants were selected at random from the greenhouse's 2,000 plants, the conclusion extends to the plants in this greenhouse. It does not extend to all tomato plants everywhere, since only this greenhouse was sampled.")

# PSDA · Evaluating statistical claims · easy
mct(D, PSDA, "Evaluating statistical claims", "easy",
    "A researcher surveyed 50 randomly selected students at a high school. Students who reported streaming more than 3 hours of video per day had lower average test scores than students who reported streaming less. Which of the following is the most appropriate conclusion?",
    ["Among students at the school, streaming more video is associated with lower test scores, but the survey does not show that streaming causes lower scores.",
     "Streaming more than 3 hours of video per day causes students at the school to have lower test scores.",
     "Among all high school students in the country, streaming more video is associated with lower test scores.",
     "There is no relationship between streaming video and test scores among students at the school."], 0,
    "The students were a random sample from the school, so the association can be generalized to students at that school. Because the researcher did not assign streaming time, the survey shows association, not causation, and it says nothing about students at other schools.")

# Geometry · Lines, angles, and triangles · medium · grid-in
xs = [g for g in GRID if (5 * g + 12) + (3 * g + 32) == 180]
assert xs == [17]
spr(D, GEO, "Lines, angles, and triangles", "medium",
    "At a construction site, two parallel steel beams are crossed by a straight brace. Two same-side interior angles formed by the brace and the beams measure (5x + 12)° and (3x + 32)°. What is the value of x?", 17,
    "When a line crosses two parallel lines, same-side interior angles are supplementary. So (5x + 12) + (3x + 32) = 180, which gives 8x + 44 = 180, 8x = 136, and x = 17.")

# Geometry · Circles · medium
theta = 5 * math.pi / 12
ch = ["5/12", "5π/24", "5π/12", "60π"]
assert abs(12 * theta - 5 * math.pi) < 1e-12 and abs(val(ch[2]) - theta) < 1e-12
assert [val(c_) for c_ in ch] == sorted(val(c_) for c_ in ch)
mct(D, GEO, "Circles", "medium",
    "A theater's circular revolving stage has a radius of 12 feet. During one scene, the stage rotates so that a point on its outer edge travels 5π feet along the edge. Through what angle, in radians, does the stage rotate?",
    ch, 2, "Arc length equals radius times the central angle in radians: s = rθ. So 5π = 12θ, and θ = 5π/12 radians.")

# ================================================================ HARDER MODULE 2: replace the easy items
# The 4 easy items written above move to the bank unchanged (ids m-202 to m-205); each is replaced
# by a new medium or hard item of the same skill, keyed in the same answer position.
D = "m2x"

# Algebra · Linear equations in two variables · medium (replaces the easy "(4, k)" item)
a_int = [g for g in GRID if ev("5x − 2y", x=g, y=0) == 30]
b_int = [g for g in GRID if ev("5x − 2y", x=0, y=g) == 30]
assert a_int == [6] and b_int == [-15]
R1 = mc(D, ALG, "Linear equations in two variables", "medium",
   "5x − 2y = 30\n\nIn the xy-plane, the graph of the given equation intersects the x-axis at the point (a, 0) and the y-axis at the point (0, b). What is the value of a + b?", a_int[0] + b_int[0],
   [6 + 15, -6 - 15, -6 + 15],
   "At the x-intercept, y = 0, so 5x = 30 and a = 6. At the y-intercept, x = 0, so −2y = 30 and b = −15. Therefore a + b = 6 + (−15) = −9.", pos=1)

# PSDA · Percentages · hard · grid-in (replaces the easy streaming-minutes item)
ps_ = [p_ for p_ in range(0, 101) if F(125, 100) * (1 - F(p_, 100)) == F(110, 100)]
assert ps_ == [12] and abs(10 * 1.25 * 0.88 - 11) < 1e-9
R2 = spr(D, PSDA, "Percentages", "hard",
    "A food truck raised the price of its tacos by 25%. A month later, it lowered the new price by p%. The final price was 10% greater than the original price. What is the value of p?", ps_[0],
    "Call the original price 1. After the 25% increase, the price is 1.25. Lowering it by p% multiplies it by 1 − p/100, and the result is 10% more than the original, or 1.10. So 1.25(1 − p/100) = 1.10, which gives 1 − p/100 = 0.88 and p = 12.")

# Advanced Math · Equivalent expressions · hard (replaces the easy polynomial-subtraction item)
orig = "4/(x − 2) − 3/(x + 1)"
ch = ["1/(2x − 1)", "(x + 2)/((x − 2)(x + 1))", "(x + 10)/((x − 2)(x + 1))", "(7x − 2)/((x − 2)(x + 1))"]
pts_ = (3, 4, 5, 7, 10)
assert same_poly(ch[2], orig, pts=pts_) and not any(same_poly(c_, orig, pts=pts_) for i, c_ in enumerate(ch) if i != 2)
R3 = mct(D, ADV, "Equivalent expressions", "hard", f"Which expression is equivalent to {orig}, for x > 2?", ch, 2,
    "Rewrite both fractions over the common denominator (x − 2)(x + 1): 4(x + 1)/((x − 2)(x + 1)) − 3(x − 2)/((x − 2)(x + 1)). The numerator is 4x + 4 − 3x + 6 = x + 10, so the expression is equivalent to (x + 10)/((x − 2)(x + 1)).")

# Algebra · Linear inequalities · medium (replaces the easy crane item)
ch = ["12x + 18y ≤ 540", "18x + 12y ≥ 540", "x + y ≥ 540", "12x + 18y ≥ 540"]
enough = lambda x0, y0: 12 * x0 + 18 * y0 >= 540
box = [(x0, y0) for x0 in range(0, 60, 3) for y0 in range(0, 40, 2)]
assert all(ev(ch[3], x=x0, y=y0) == enough(x0, y0) for x0, y0 in box)
assert all(any(ev(c_, x=x0, y=y0) != enough(x0, y0) for x0, y0 in box) for c_ in ch[:3])
R4 = mct(D, ALG, "Linear inequalities", "medium",
    "A construction crew must haul at least 540 cubic yards of dirt away from a site. A small truck carries 12 cubic yards of dirt per trip, and a large truck carries 18 cubic yards of dirt per trip. Which inequality represents the numbers of small-truck trips, x, and large-truck trips, y, that will haul away the required amount of dirt?",
    ch, 3, "In x small-truck trips the crew hauls 12x cubic yards, and in y large-truck trips it hauls 18y cubic yards. The total, 12x + 18y, must be at least 540, so 12x + 18y ≥ 540.")

OUT["moved"] = [it for it in OUT["m2"] if it["difficulty"] == "easy"]
assert [it.get("type", "mc") for it in OUT["moved"]] == ["mc", "spr", "mc", "mc"]
assert [it["skill"] for it in OUT["moved"]] == [R1["skill"], R2["skill"], R3["skill"], R4["skill"]]
assert [it.get("answer") for it in OUT["moved"] if "choices" in it] == [R1["answer"], R3["answer"], R4["answer"]]
med = [it for it in OUT["m2"] if it["difficulty"] == "medium"]
hrd = [it for it in OUT["m2"] if it["difficulty"] == "hard"]
assert len(med) == 9 and len(hrd) == 9
# interleave: no two Algebra items in a row where avoidable
OUT["m2"] = [R1] + med[:5] + [R4] + med[5:] + [R2] + hrd[:2] + [R3] + hrd[2:]
del OUT["m2x"]

# ================================================================ EASIER MODULE 2 (pt3-m2e)
D = "m2e"

# 01 Algebra · Linear equations in one variable · easy
x = F(37 - 9, 4)
assert x == 7 and ev("4x + 9", x=x) == 37 and [g for g in GRID if ev("4x + 9", x=g) == 37] == [7]
mc(D, ALG, "Linear equations in one variable", "easy", "4x + 9 = 37\n\nWhat is the solution to the given equation?", x,
   [F(37 + 9, 4), 37 - 9 - 4, 37 - 9],
   "Subtract 9 from both sides to get 4x = 28. Then divide both sides by 4: x = 7.", pos=0)

# 02 PSDA · Ratios, rates · easy · grid-in
rice = F(3, 8) * 56
assert rice == 21 and 56 // 8 * 3 == 21
spr(D, PSDA, "Ratios, rates, proportional relationships, and units", "easy",
    "A food truck uses 3 pounds of rice for every 8 burritos it makes. At this rate, how many pounds of rice does the truck use to make 56 burritos?", rice,
    "56 burritos is 56 ÷ 8 = 7 times as many as 8 burritos, so the truck uses 7 × 3 = 21 pounds of rice.")

# 03 Advanced Math · Equivalent expressions · easy
orig = "7x² + 4x − 3x² + 2x"
ch = ["4x² + 6x", "10x² + 6x", "4x² + 2x", "10x²"]
assert same_poly(ch[0], orig) and not any(same_poly(c_, orig) for c_ in ch[1:])
mct(D, ADV, "Equivalent expressions", "easy", f"Which expression is equivalent to {orig}?", ch, 0,
    "Combine like terms: 7x² − 3x² = 4x² and 4x + 2x = 6x. The expression is equivalent to 4x² + 6x.")

# 04 Algebra · Linear functions · easy
cost = ev("6h + 15", h=9)
assert cost == 69 == 6 * 9 + 15
mc(D, ALG, "Linear functions", "easy",
   "A hiking club charges a $15 membership fee plus $6 for each guided hike a member goes on. The function C(h) = 6h + 15 gives the total cost, in dollars, for a member who goes on h guided hikes. What is the total cost, in dollars, for a member who goes on 9 guided hikes?", cost,
   [6 * 9, 15 * 9 + 6, (6 + 15) * 9],
   "Substitute h = 9: C(9) = 6(9) + 15 = 54 + 15 = 69.", pos=1)

# 05 Geometry · Area and volume · easy
area = 40 * 25
assert area == 1000 and sum(1 for _ in itertools.product(range(40), range(25))) == area
mc(D, GEO, "Area and volume", "easy",
   "A theater's stage is a rectangle that is 40 feet wide and 25 feet deep. What is the area of the stage, in square feet?", area,
   [40 + 25, 2 * (40 + 25), F(40 * 25, 2)],
   "The area of a rectangle is its length times its width: 40 × 25 = 1,000 square feet.", pos=3)

# 06 Advanced Math · Nonlinear functions · easy
f = "x² − 5x"
k = ev(f, x=-3)
assert k == 24 and 9 + 15 == 24
mc(D, ADV, "Nonlinear functions", "easy", f"The function f is defined by f(x) = {f}. What is the value of f(−3)?", k,
   [-k, ev(f, x=3), -9 + 15],
   "Substitute x = −3: f(−3) = (−3)² − 5(−3) = 9 + 15 = 24.", pos=3)

# 07 Algebra · Linear inequalities · easy
ch = ["x ≥ 5", "x ≤ 5", "x ≤ 7/3", "x ≤ 15"]
assert all(ev(ch[1], x=g) == (ev("3x − 4", x=g) <= 11) for g in GRID)
assert all(any(ev(c_, x=g) != (ev("3x − 4", x=g) <= 11) for g in GRID) for i, c_ in enumerate(ch) if i != 1)
mct(D, ALG, "Linear inequalities", "easy", "3x − 4 ≤ 11\n\nWhich of the following is the solution to the given inequality?", ch, 1,
    "Add 4 to both sides: 3x ≤ 15. Divide both sides by 3 (a positive number, so the inequality does not reverse): x ≤ 5.")

# 08 PSDA · Percentages · easy · grid-in
pct = F(28 * 100, 80)
assert pct == 35 and 0.35 * 80 == 28
spr(D, PSDA, "Percentages", "easy",
    "A greenhouse has 80 plants, and 28 of them are ferns. What percent of the plants in the greenhouse are ferns?", pct,
    "28/80 = 0.35, which is 35%.")

# 09 Advanced Math · Nonlinear equations in one variable · easy · grid-in
roots = [g for g in GRID if 5 * g * g == 180]
assert roots == [-6, 6]
spr(D, ADV, "Nonlinear equations in one variable", "easy", "5x² = 180\n\nWhat is the positive solution to the given equation?", 6,
    "Divide both sides by 5: x² = 36. So x = 6 or x = −6, and the positive solution is 6.")

# 10 Algebra · Systems of two linear equations · medium
y0 = F(11 - 3, 2); x0 = 2 * y0 + 1
sols = [(g, h_) for g in GRID for h_ in GRID if g == 2 * h_ + 1 and 3 * g - 4 * h_ == 11]
assert sols == [(9, 4)] == [(x0, y0)]
cands = [(-3, -2), (4, 9), (5, 2), (9, 4)]
assert [c_[0] == 2 * c_[1] + 1 and 3 * c_[0] - 4 * c_[1] == 11 for c_ in cands] == [False, False, False, True]
mct(D, ALG, "Systems of two linear equations", "medium",
    "x = 2y + 1\n3x − 4y = 11\n\nWhat is the solution (x, y) to the given system of equations?",
    [f"({neg(a_)}, {neg(b_)})" for a_, b_ in cands], 3,
    "Substitute x = 2y + 1 into the second equation: 3(2y + 1) − 4y = 11, so 6y + 3 − 4y = 11, 2y = 8, and y = 4. Then x = 2(4) + 1 = 9. The solution is (9, 4).")

# 11 Advanced Math · Equivalent expressions · medium
orig = "3x² + 10x − 8"
ch = ["(3x − 2)(x + 4)", "(3x + 2)(x − 4)", "(3x − 4)(x + 2)", "(3x + 4)(x − 2)"]
assert same_poly(ch[0], orig) and not any(same_poly(c_, orig) for c_ in ch[1:])
mct(D, ADV, "Equivalent expressions", "medium", f"Which expression is equivalent to {orig}?", ch, 0,
    "Check by expanding: (3x − 2)(x + 4) = 3x² + 12x − 2x − 8 = 3x² + 10x − 8. The other products give middle terms of −10x, 2x, and −2x.")

# 12 PSDA · One-variable data · medium
mins = [40, 25, 90, 65, 25, 70, 50]
med_ = statistics.median(mins)
assert med_ == 50 == sorted(mins)[3] and mins[3] == 65 and statistics.mode(mins) == 25
mc(D, PSDA, "One-variable data: distributions and measures of center and spread", "medium",
   f"Leo recorded the number of minutes he spent streaming music on each of 7 days: {', '.join(map(str, mins))}. What is the median number of minutes Leo spent streaming music on these days?", med_,
   [25, 65, 90],
   "Listed in order, the values are 25, 25, 40, 50, 65, 70, 90. The median is the middle (fourth) value, 50.", pos=1)

# 13 Algebra · Linear equations in two variables · medium · grid-in
m = F(17 - 5, 6 - 2)
assert m == 3 and 5 - 3 * 2 == 17 - 3 * 6
spr(D, ALG, "Linear equations in two variables", "medium",
    "In the xy-plane, a line passes through the points (2, 5) and (6, 17). What is the slope of the line?", m,
    "Slope = (change in y)/(change in x) = (17 − 5)/(6 − 2) = 12/4 = 3.")

# 14 Advanced Math · Nonlinear functions · medium
f = "−2(x − 3)² + 11"
mx = max(ev(f, x=g) for g in GRID)
assert mx == 11 and ev(f, x=3) == 11 and ev(f, x=0) == -7
mc(D, ADV, "Nonlinear functions", "medium", f"f(x) = {f}\n\nThe function f is defined by the given equation. What is the maximum value of f(x)?", mx,
   [ev(f, x=0), -2, 3],
   "Because (x − 3)² ≥ 0, the term −2(x − 3)² is at most 0, and it equals 0 when x = 3. So the maximum value of f(x) is 0 + 11 = 11.", pos=3)

# 15 Geometry · Right triangles and trigonometry · medium
A = math.atan2(7, 24)
assert abs(math.cos(A) - 24 / 25) < 1e-12 and 24 ** 2 + 7 ** 2 == 25 ** 2
mc(D, GEO, "Right triangles and trigonometry", "medium",
   "In right triangle ABC, angle C is the right angle, AC = 24, and BC = 7. What is the value of cos A?", F(24, 25),
   [F(7, 25), F(7, 24), F(24, 7)],
   "The hypotenuse is AB = √(24² + 7²) = √625 = 25. For angle A, the adjacent leg is AC = 24, so cos A = AC/AB = 24/25.", pos=2)

# 16 Algebra · Linear functions · medium
ch = ["T(t) = 0.4t + 58", "T(t) = 0.4t + 52", "T(t) = 2.5t + 52", "T(t) = 10t + 52"]
fit = [abs(ev(rhs(c_), t=15) - 58) < 1e-9 and abs(ev(rhs(c_), t=40) - 68) < 1e-9 for c_ in ch]
assert fit == [False, True, False, False] and F(68 - 58, 40 - 15) == F(2, 5)
mct(D, ALG, "Linear functions", "medium",
    "After a heater is switched on, the temperature inside a greenhouse rises at a constant rate. The temperature is 58°F 15 minutes after the heater is switched on and 68°F 40 minutes after the heater is switched on. Which function T gives the temperature, in °F, t minutes after the heater is switched on?",
    ch, 1, "The rate of change is (68 − 58)/(40 − 15) = 10/25 = 0.4 degree per minute. Then 58 = 0.4(15) + b = 6 + b, so b = 52 and T(t) = 0.4t + 52.")

# 17 Advanced Math · Systems of equations in two variables · medium · grid-in
sols = [g for g in GRID if g * g - 6 == g]
assert sols == [-2, 3]
spr(D, ADV, "Systems of equations in two variables", "medium",
    "y = x² − 6\ny = x\n\nIf (x, y) is a solution to the given system of equations and x > 0, what is the value of x?", max(sols),
    "Substituting y = x into the first equation gives x = x² − 6, or x² − x − 6 = 0, which factors as (x − 3)(x + 2) = 0. Since x > 0, x = 3.")

# 18 Algebra · Systems of two linear equations · medium · grid-in
lg = [l_ for l_ in range(56) if 4 * (55 - l_) + 10 * l_ == 370]
assert lg == [25] == [solve2(1, 1, 55, 4, 10, 370)[1]]
spr(D, ALG, "Systems of two linear equations", "medium",
    "A greenhouse sells small plants for $4 each and large plants for $10 each. On one day, the greenhouse sold 55 plants for a total of $370. How many large plants did the greenhouse sell that day?", lg[0],
    "Let s and g be the numbers of small and large plants. Then s + g = 55 and 4s + 10g = 370. Substituting s = 55 − g gives 220 − 4g + 10g = 370, so 6g = 150 and g = 25.")

# 19 PSDA · Probability · medium
drinks = ["L"] * 48 + ["T"] * 57 + ["W"] * 45
pr = F(sum(d_ != "T" for d_ in drinks), len(drinks))
assert len(drinks) == 150 and pr == F(31, 50)
mc(D, PSDA, "Probability and conditional probability", "medium",
   "On Saturday, a food truck sold 150 drinks: 48 lemonades, 57 iced teas, and 45 bottles of water. If one of these drinks is selected at random, what is the probability that it is not an iced tea?", pr,
   [F(45, 150), F(57, 150), F(2, 3)],
   "150 − 57 = 93 of the drinks are not iced teas, so the probability is 93/150 = 31/50.", pos=2)

# 20 Algebra · Linear equations in one variable · hard
xs = [g for g in GRID if F(3, 4) * g - 5 == 13]
assert xs == [24] and 3 * xs[0] - 20 == 52 == 4 * 13
mc(D, ALG, "Linear equations in one variable", "hard",
   "(3/4)x − 5 = 13\n\nIf x satisfies the given equation, what is the value of 3x − 20?", 52,
   [13, 24, 72],
   "Multiply both sides of the equation by 4: 3x − 20 = 52. (Alternatively, solving gives x = 24, and 3(24) − 20 = 52.)", pos=2)

# 21 Advanced Math · Nonlinear equations in one variable · hard
nroots = {kk: len(real_roots(1, -8, kk)) for kk in (12, 16, 20, 64)}
assert nroots == {12: 2, 16: 1, 20: 0, 64: 0}
mc(D, ADV, "Nonlinear equations in one variable", "hard",
   "x² − 8x + k = 0\n\nIn the given equation, k is a constant. The equation has exactly two real solutions. Which of the following could be the value of k?", 12,
   [16, 20, 64],
   "A quadratic equation has exactly two real solutions when its discriminant is positive: (−8)² − 4(1)(k) > 0, so 64 − 4k > 0 and k < 16. Of the choices, only 12 is less than 16. (When k = 16 there is exactly one solution, and when k = 20 or 64 there are none.)", pos=0)

# 22 Geometry · Circles · hard
ch = ["(x − 1)² + (y + 4)² = 100", "(x + 1)² + (y − 4)² = 10", "(x + 1)² + (y − 4)² = 100", "(x − 5)² + (y − 12)² = 100"]
def circ_ok(c_):
    lhs, r_ = c_.split("=")
    return ev(lhs, x=5, y=12) == ev(r_) and ev(lhs, x=-1, y=4) == 0
assert [circ_ok(c_) for c_ in ch] == [False, False, True, False] and (5 + 1) ** 2 + (12 - 4) ** 2 == 100
mct(D, GEO, "Circles", "hard",
    "In the xy-plane, a circle has center (−1, 4) and passes through the point (5, 12). Which equation represents the circle?", ch, 2,
    "The radius is the distance from the center to (5, 12): √((5 − (−1))² + (12 − 4)²) = √(36 + 64) = 10. A circle with center (h, k) and radius r has equation (x − h)² + (y − k)² = r², so the circle is (x + 1)² + (y − 4)² = 100.")

# ================================================================ ids, validation, output
for k_, pre in (("m1", "pt3-m1-"), ("m2", "pt3-m2-"), ("m2e", "pt3-m2e-")):
    for i, it in enumerate(OUT[k_], 1): it["id"] = f"{pre}{i:02d}"
for i, it in enumerate(OUT["bank"], 174): it["id"] = f"m-{i:03d}"
for i, it in enumerate(OUT["moved"], 202): it["id"] = f"m-{i:03d}"

META = json.load(open(os.path.join(HERE, "..", "data", "questions.json")))
SK = META["meta"]["skills"]["math"]
MINE = {"pt3-m1.json", "pt3-m2.json", "pt3-m2e.json", "bank-m-3.json", "bank-m-pt3-moved.json"}
MY_BANK = {f"m-{i:03d}" for i in range(174, 194)}  # already merged into questions.json
OTHERS = [q for q in META["questions"] if q["id"] not in MY_BANK]
for t_ in json.load(open(os.path.join(HERE, "..", "data", "tests.json"), encoding="utf-8"))["tests"]:
    for mod in t_["modules"]:
        OTHERS += [q for q in mod["questions"] if not q["id"].startswith("pt3-m")]
for fn in sorted(os.listdir(DRAFT)):
    if fn.endswith(".json") and fn not in MINE:
        OTHERS += json.load(open(os.path.join(DRAFT, fn), encoding="utf-8"))
OTHER_IDS = {q["id"] for q in OTHERS}
OTHER_STEMS = {q["stem"] for q in OTHERS}
def math_lines(q):  # displayed equations / function definitions, to catch reused items with a new wording
    t = q["stem"]
    return {l.strip() for l in t.split("\n") if "=" in l and len(l) < 60} | set(re.findall(r"[a-zA-Z]\([a-z]\) = [^.?]+", t))
OTHER_MATH = set().union(*(math_lines(q) for q in OTHERS if q.get("section") == "math"))

def norm_spr(s):  # Python port of normalizeSpr in assets/js/practice.js
    t = re.sub(r"\s+", "", str(s).strip())
    if re.fullmatch(r"-?\d+(\.\d+)?/\d+(\.\d+)?", t):
        n_, d_ = map(float, t.split("/"))
        return repr(float(f"{n_ / d_:.4f}")) if d_ else t
    try: return repr(float(f"{float(t):.4f}"))
    except ValueError: return t.lower()

ORDER = ["id", "section", "domain", "skill", "difficulty", "stem", "choices", "type", "answer", "explanation", "passage"]
DOM_ORDER = {"easy": 0, "medium": 1, "hard": 2}
MIX = {"m1": {"easy": 7, "medium": 9, "hard": 6}, "m2": {"medium": 11, "hard": 11}, "m2e": {"easy": 9, "medium": 10, "hard": 3}}
all_stems = [it["stem"] for items in OUT.values() for it in items]
assert len(all_stems) == len(set(all_stems)), "duplicate stem within my own files"
for k_, items in OUT.items():
    for it in items:
        assert it["domain"] in SK and it["skill"] in SK[it["domain"]], it["id"]
        assert it["id"] not in OTHER_IDS, it["id"]  # bank ids, other drafts and built tests
        assert it["stem"] not in OTHER_STEMS, it["id"]
        shared = math_lines(it) & OTHER_MATH
        if shared: print("note: math line also used elsewhere:", it["id"], shared)
        assert "figure" not in it["stem"] and "shown" not in it["stem"]
        # displayed math uses U+2212; an ASCII hyphen may only join words ("400-square-foot")
        assert not re.search(r"(?<![A-Za-z0-9])-|-(?![A-Za-z])", it["stem"] + it.get("passage", "") + it["explanation"] + "".join(it.get("choices", []))), it["id"]
        if it.get("type") == "spr":
            assert "choices" not in it and isinstance(it["answer"], str)
            v = F(it["answer"])
            forms = {it["answer"], f"{v.numerator}/{v.denominator}"}
            dd = v.denominator
            while dd % 2 == 0: dd //= 2
            while dd % 5 == 0: dd //= 5
            assert dd == 1, (it["id"], "grid-in answer must terminate")
            forms.add(f"{float(v):.4f}".rstrip("0").rstrip("."))
            assert len({norm_spr(s_) for s_ in forms}) == 1, (it["id"], forms)
        else:
            ch = it["choices"]
            assert len(ch) == 4 and len(set(ch)) == 4 and 0 <= it["answer"] < 4, it["id"]
            nums = [val(c_) for c_ in ch]
            if all(n_ is not None for n_ in nums):
                assert nums == sorted(nums) and len(set(nums)) == 4, (it["id"], ch)
    if k_ in MIX:
        assert len(items) == 22
        assert [DOM_ORDER[it["difficulty"]] for it in items] == sorted(DOM_ORDER[it["difficulty"]] for it in items)
        dom = Counter(it["domain"] for it in items)
        assert dom == {ALG: 8, ADV: 7, PSDA: 4, GEO: 3}, dom
        diff = Counter(it["difficulty"] for it in items)
        assert diff == MIX[k_], (k_, diff)
        assert 5 <= sum(it.get("type") == "spr" for it in items) <= 6
        pos = Counter(it["answer"] for it in items if "choices" in it)
        assert max(pos.values()) - min(pos.values()) <= 1 and len(pos) == 4, pos
        assert all(items[i]["domain"] != items[i + 1]["domain"] for i in range(len(items) - 1)), k_
    elif k_ == "bank":
        assert len(items) == 20
        pos = Counter(it["answer"] for it in items if "choices" in it)
        assert max(pos.values()) - min(pos.values()) <= 1 and len(pos) == 4, pos
    else:
        assert k_ == "moved" and len(items) == 4 and all(it["difficulty"] == "easy" for it in items)
for pair in (("m1", "m2"), ("m1", "m2e")):
    alg = {it["skill"] for k_ in pair for it in OUT[k_] if it["domain"] == ALG}
    assert alg == set(SK[ALG]), pair

os.makedirs(DRAFT, exist_ok=True)
for k_, name in (("m1", "pt3-m1.json"), ("m2", "pt3-m2.json"), ("m2e", "pt3-m2e.json"),
                 ("bank", "bank-m-3.json"), ("moved", "bank-m-pt3-moved.json")):
    items = [{f_: it[f_] for f_ in ORDER if f_ in it} for it in OUT[k_]]
    with open(os.path.join(DRAFT, name), "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"{name}: {len(items)} items, {sum(i.get('type') == 'spr' for i in items)} grid-ins, "
          f"{dict(Counter(i['domain'].split()[0] for i in items))}, "
          f"{dict(Counter(i['difficulty'] for i in items))}, keys {dict(sorted(Counter(i['answer'] for i in items if 'choices' in i).items()))}")
