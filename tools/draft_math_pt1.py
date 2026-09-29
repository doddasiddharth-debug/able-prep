"""Draft math items for ABLE Preps practice test 1 (two modules) plus 20
extra bank items, written to the conventions of tools/gen_math.py.

Every key is computed from the item's numbers and then re-solved a second,
independent way (substitution, brute force over rationals, evaluating each
displayed choice, or a rule check for the statistics items) before anything
is written. The run stops on the first failed assertion.

Writes:
  data/draft/pt1-m1.json    Module 1, 22 items (pt1-m1-01 .. -22)
  data/draft/pt1-m2.json    harder Module 2, 22 items (pt1-m2-01 .. -22), 11 medium / 11 hard
  data/draft/pt1-m2e.json   easier Module 2, 22 items (pt1-m2e-01 .. -22), 9 easy / 10 medium / 3 hard
  data/draft/bank-m-1.json  20 bank items (m-134 .. m-153)
  data/draft/bank-m-pt1-moved.json  the 4 easy items taken out of Module 2 (m-194 .. m-197)
Usage: python3 tools/draft_math_pt1.py
"""
import json, os, re
from collections import Counter
from fractions import Fraction as F
from math import sqrt, isqrt

ALG = "Algebra"; ADV = "Advanced Math"; PSDA = "Problem-Solving and Data Analysis"; GEO = "Geometry and Trigonometry"
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "data", "draft")

# ---------------------------------------------------------------- helpers (copied from gen_math.py)
def fmt(n, dec=False):
    """Integers plain; other values as a/b, or as a decimal when dec=True
    and the decimal terminates (money, measurements, means)."""
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

def neg(s):  # "-3" -> "−3"
    return str(s).replace("-", "−")

def comma(s):
    """1395 -> 1,395 (whole numbers of 4+ digits, as the SAT prints them)."""
    m = re.fullmatch(r"(-?)(\d{4,})", s)
    return f"{m.group(1)}{int(m.group(2)):,}" if m else s

# ---------------------------------------------------------------- independent checkers
def py(expr):
    """Displayed math -> Python, written separately from audit_math.to_py."""
    e = expr.replace("−", "-").replace("²", "**2").replace("³", "**3").replace("√", "S").replace("^", "**")
    e = re.sub(r"\s+", "", e)
    e = re.sub(r"(\d|\))(?=[a-zS(])", r"\1*", e)   # 3x, 2(, )(, )x, 3S(
    e = re.sub(r"([a-z])(?=[a-zS(])", r"\1*", e)   # xy, x(
    return e

def ev(expr, **env):
    return eval(py(expr), {"S": sqrt, "__builtins__": {}}, env)

def close(a, b): return abs(float(a) - float(b)) < 1e-9

PTS = [F(7, 2), F(5), F(-11, 3), F(13), F(29, 4), F(-6)]
def equivalent(e1, fn, pts=PTS, var="x"):
    ok = True
    for p in pts:
        try: ok &= close(ev(e1, **{var: p}), fn(p))
        except ZeroDivisionError: pass
    return ok

GRID = sorted({F(n, d) for d in (1, 2, 3, 4, 5, 6, 8, 10) for n in range(-80 * d, 80 * d + 1)})
def roots(f):
    """Every rational root of f on a fine grid (exact Fraction arithmetic)."""
    out = []
    for x in GRID:
        try:
            if f(x) == 0: out.append(x)
        except ZeroDivisionError: pass
    return out

def js_norm(s):
    """Python port of normalizeSpr in assets/js/practice.js."""
    t = re.sub(r"\s+", "", str(s).strip())
    def num(x):
        x = float(f"{x:.4f}")
        return str(int(x)) if x == int(x) else repr(x)
    if re.fullmatch(r"-?\d+(\.\d+)?/\d+(\.\d+)?", t):
        n, d = (float(p) for p in t.split("/"))
        return num(n / d) if d else t
    try: return num(float(t))
    except ValueError: return t.lower()

# ---------------------------------------------------------------- item builders
def base(dom, skill, diff):
    return {"section": "math", "domain": dom, "skill": skill, "difficulty": diff}

def MC(lst, dom, skill, diff, stem, key, distractors, expl, passage=None, dec=False, suffix=""):
    """Numeric choices, ascending (gen_math.num_choices, minus the top-up: all
    three distractors must come from a named error)."""
    vals = [F(key)] + [F(d) for d in distractors]
    assert len(set(vals)) == 4, (stem, vals)
    vals.sort()
    it = base(dom, skill, diff)
    it.update(stem=stem, choices=[neg(comma(fmt(v, dec))) + suffix for v in vals], answer=vals.index(F(key)), explanation=expl)
    if passage: it["passage"] = passage
    lst.append(it); return it

def TXT(lst, dom, skill, diff, stem, key, distractors, expl, passage=None):
    """Non-numeric choices; the key's slot is assigned later to even out positions."""
    assert len(distractors) == 3 and len({key, *distractors}) == 4, stem
    it = base(dom, skill, diff)
    it.update(stem=stem, choices=None, answer=None, explanation=expl, _key=key, _dis=list(distractors))
    if passage: it["passage"] = passage
    lst.append(it); return it

def SPR(lst, dom, skill, diff, stem, answer, expl, passage=None, dec=True):
    a = fmt(F(answer), dec)           # ASCII "-" for negatives: that is what a student types
    it = base(dom, skill, diff)
    it.update(stem=stem, type="spr", answer=a, explanation=expl)
    if passage: it["passage"] = passage
    # every form a student could reasonably enter must normalize the same way
    v = F(answer)
    forms = {a, str(v.numerator) + ("" if v.denominator == 1 else f"/{v.denominator}")}
    d = v.denominator
    while d % 2 == 0: d //= 2
    while d % 5 == 0: d //= 5
    assert d == 1, f"grid-in answer {a} does not terminate"
    forms.add(f"{float(v):.4f}"); forms.add(str(float(v)))
    if 0 < abs(v) < 1: forms.add(str(float(v)).replace("0.", ".", 1))
    assert len({js_norm(f) for f in forms}) == 1, (a, forms)
    lst.append(it); return it

M1, M2, BANK = [], [], []

# =====================================================================================
# MODULE 1   (7 easy, 9 medium, 6 hard)
# =====================================================================================

# ---- easy
a, b, c = 5, 7, 23
x = F(c + b, a)
assert roots(lambda t: a * t - b - c) == [x] and x == 6
MC(M1, ALG, "Linear equations in one variable", "easy",
   f"{a}x − {b} = {c}\n\nWhat is the solution to the given equation?", x,
   [F(c - b, a),            # subtracted 7 instead of adding it
    F(c, a) + b,            # divided 23 by 5 before undoing the −7
    c + b],                 # added 7 but never divided by 5
   f"Add {b} to both sides to get {a}x = {c + b}. Then divide both sides by {a}: x = {x}.")

key = "3x − 12"
assert equivalent(key, lambda t: 4 * (2 * t - 3) - 5 * t)
dis = ["3x − 3",            # multiplied only the 2x by 4
       "13x − 12",          # added 5x instead of subtracting
       "3x + 12"]           # sign error on 4(−3)
assert not any(equivalent(d, lambda t: 4 * (2 * t - 3) - 5 * t) for d in dis)
TXT(M1, ADV, "Equivalent expressions", "easy", "Which expression is equivalent to 4(2x − 3) − 5x?", key, dis,
    "Distribute the 4: 4(2x − 3) = 8x − 12. Then combine like terms: 8x − 12 − 5x = 3x − 12.")

flour, batches, want = 9, 4, 10
ans = F(flour * want, batches)
assert ans * batches == flour * want and ans == F(45, 2)          # cross-multiplied proportion
SPR(M1, PSDA, "Ratios, rates, proportional relationships, and units", "easy",
    f"Hazel's Bakery uses {flour} cups of flour to make {batches} batches of muffins. At this rate, how many cups of flour are needed to make {want} batches of muffins?", ans,
    f"The bakery uses {flour} ÷ {batches} = {fmt(F(flour, batches), True)} cups of flour per batch, so {want} batches need {want} × {fmt(F(flour, batches), True)} = {fmt(ans, True)} cups.")

m, b0 = 8, 35
C = lambda g: m * g + b0
assert C(1) - C(0) == 8 and C(7) - C(6) == 8 and C(0) == 35
TXT(M1, ALG, "Linear functions", "easy",
    f"The monthly cost C, in dollars, of Ana's phone plan is given by C(g) = {m}g + {b0}, where g is the number of gigabytes of data she uses that month. Which of the following is the best interpretation of the number {m} in this context?",
    f"Each additional gigabyte of data increases the monthly cost by ${m}.",
    [f"The monthly cost is ${m} when no data is used.",           # slope read as the intercept
     f"The plan includes {m} gigabytes of data each month.",       # slope read as an allowance
     f"Each gigabyte of data costs ${m + b0}."],                   # added slope and intercept
    f"The coefficient {m} is the rate of change of C: each additional gigabyte adds {m} dollars to C(g). The monthly cost with no data is C(0) = {b0} dollars.")

L, W, D = 3, 2, F(3, 2)
vol = L * W * D
assert vol == 9 and (2 * L) * (2 * W) * (2 * D) * F(1, 8) == vol     # count half-foot cubes, each 1/8 cubic foot
MC(M1, GEO, "Area and volume", "easy",
   f"A rectangular planter box has an inside length of {L} feet, an inside width of {W} feet, and an inside depth of {fmt(D, True)} feet. How many cubic feet of soil are needed to fill the box completely?", vol,
   [L * W,                          # ignored the depth
    L + W + D,                      # added the dimensions
    2 * (L * W + L * D + W * D)],   # surface area
   f"Volume = length × width × depth = {L} × {W} × {fmt(D, True)} = {fmt(vol)} cubic feet.", dec=True)

g = lambda t: t * t - 3 * t
assert g(-4) == 28 and ev("x² − 3x", x=-4) == 28
MC(M1, ADV, "Nonlinear functions", "easy",
   "The function g is defined by g(x) = x² − 3x. What is the value of g(−4)?", 28,
   [-16 + 12,     # took (−4)² as −16
    16 - 12,      # took −3(−4) as −12
    -16 - 12],    # both errors
   "Substitute x = −4: g(−4) = (−4)² − 3(−4) = 16 + 12 = 28.")

n, p = 240, 30
ans = F(n * p, 100)
assert ans == 72 and ans / n == F(3, 10)
MC(M1, PSDA, "Percentages", "easy",
   f"Of the {n} students at a school's sports day, {p}% signed up for the relay race. How many of the students signed up for the relay race?", ans,
   [F(n, p),                 # divided by 30
    F(n, 3),                 # treated 30% as one third
    n - ans],                # found the 70% who did not sign up
   f"{p}% of {n} is 0.{p} × {n} = {ans}.")

# ---- medium
sx, sy = 5, 4
assert (sx + 3 * sy, 2 * sx - sy) == (17, 6)
det = 1 * (-1) - 3 * 2
assert F(17 * -1 - 3 * 6, det) == sx and F(1 * 6 - 2 * 17, det) == sy   # Cramer's rule
dis = ["(4, 5)", "(11, 2)", "(4, 2)"]    # swapped; fits only the first equation; fits only the second
for d in dis:
    px, py_ = map(int, d.strip("()").split(", "))
    assert not (px + 3 * py_ == 17 and 2 * px - py_ == 6)
assert 11 + 3 * 2 == 17 and 2 * 4 - 2 == 6
TXT(M1, ALG, "Systems of two linear equations", "medium",
    "x + 3y = 17\n2x − y = 6\n\nWhat is the solution (x, y) to the given system of equations?", f"({sx}, {sy})", dis,
    "The second equation gives y = 2x − 6. Substitute into the first: x + 3(2x − 6) = 17, so 7x − 18 = 17, 7x = 35, and x = 5. Then y = 2(5) − 6 = 4.")

r = roots(lambda t: (t - 3) ** 2 - 49)
assert r == [-4, 10]
SPR(M1, ADV, "Nonlinear equations in one variable", "medium",
    "(x − 3)² = 49\n\nWhat is the positive solution to the given equation?", max(r),
    "Take the square root of both sides: x − 3 = 7 or x − 3 = −7. So x = 10 or x = −4. The positive solution is 10.")

freq = {0: 1, 1: 2, 2: 3, 3: 2, 4: 1, 8: 1}
games = [g_ for g_, f in freq.items() for _ in range(f)]
assert len(games) == 10
mean = F(sum(games), len(games)); med = F(sorted(games)[4] + sorted(games)[5], 2)
assert mean == F(13, 5) and med == 2
table = "Goals scored   Number of games\n" + "\n".join(f"{g_:<14} {f}" for g_, f in freq.items())
MC(M1, PSDA, "One-variable data: distributions and measures of center and spread", "medium",
   "What is the mean number of goals the club scored per game?", mean,
   [med,                                   # the median
    F(sum(freq), len(freq)),               # averaged the six goal values, ignoring frequencies
    F(min(freq) + max(freq), 2)],          # midrange
   "The club scored 0(1) + 1(2) + 2(3) + 3(2) + 4(1) + 8(1) = 26 goals in 10 games, so the mean is 26 ÷ 10 = 2.6 goals per game.",
   passage=table + "\n\nThe table summarizes the number of goals a soccer club scored in each of its 10 games this season.", dec=True)

G = lambda t: 14 - F(5, 2) * t
t4 = F(14 - 4) / F(5, 2)
assert G(t4) == 4 and t4 == 4 and roots(lambda t: G(t) - 4) == [4]
MC(M1, ALG, "Linear functions", "medium",
   "On a road trip, the amount of gasoline, in gallons, in the tank of Theo's car t hours after he fills the tank is modeled by the function G(t) = 14 − 2.5t. According to the model, how many hours after Theo fills the tank will 4 gallons of gasoline remain in the tank?", t4,
   [F(4) / F(5, 2),          # solved 2.5t = 4
    F(14) / F(5, 2),         # time until the tank is empty
    F(18) / F(5, 2)],        # sign error: 2.5t = 14 + 4
   "Set G(t) = 4: 14 − 2.5t = 4, so 2.5t = 10 and t = 10 ÷ 2.5 = 4.", dec=True)

key = "2x² − x − 15"
fn = lambda t: (2 * t + 5) * (t - 3)
assert equivalent(key, fn)
dis = ["2x² − 15",           # multiplied first terms and last terms only
       "2x² + x − 15",       # sign error combining −6x and 5x
       "2x² − 11x − 15"]     # took 5(x) as −5x
assert not any(equivalent(d, fn) for d in dis)
TXT(M1, ADV, "Equivalent expressions", "medium", "Which expression is equivalent to (2x + 5)(x − 3)?", key, dis,
    "Multiply each term of the first factor by each term of the second: 2x(x) + 2x(−3) + 5(x) + 5(−3) = 2x² − 6x + 5x − 15 = 2x² − x − 15.")

A_ang = 40
xs = roots(lambda t: A_ang + (3 * t + 5) + (2 * t + 15) - 180)
assert xs == [24]
B_ang, C_ang = 3 * 24 + 5, 2 * 24 + 15
assert A_ang + B_ang + C_ang == 180 and B_ang == 77
MC(M1, GEO, "Lines, angles, and triangles", "medium",
   f"In triangle ABC, the measure of angle A is {A_ang}°, the measure of angle B is (3x + 5)°, and the measure of angle C is (2x + 15)°. What is the measure, in degrees, of angle B?", B_ang,
   [24,                 # the value of x
    C_ang,              # angle C
    180 - B_ang],       # the exterior angle at B
   f"The angles of a triangle sum to 180°: {A_ang} + (3x + 5) + (2x + 15) = 180, so 5x + 60 = 180 and x = 24. Angle B measures 3(24) + 5 = {B_ang}°.")

price_t, price_p, goal, sold_t = 4, 3, 600, 95
need = next(q for q in range(0, 1000) if price_t * sold_t + price_p * q >= goal)
assert need == 74 and price_t * sold_t + price_p * (need - 1) < goal
SPR(M1, ALG, "Linear inequalities", "medium",
    f"A school garden club sells tomato plants for ${price_t} each and pepper plants for ${price_p} each. The club's goal is to earn at least ${goal} from plant sales. If the club sells {sold_t} tomato plants, what is the minimum number of pepper plants the club must sell to meet its goal?", need,
    f"Let p be the number of pepper plants sold. The goal requires {price_t}({sold_t}) + {price_p}p ≥ {goal}, so {price_t * sold_t} + {price_p}p ≥ {goal} and {price_p}p ≥ {goal - price_t * sold_t}. Then p ≥ {goal - price_t * sold_t}/{price_p}, which is about 73.3. Since p must be a whole number, the minimum is {need}.")

N = lambda t: 18 * F(5, 4) ** t
assert N(1) / N(0) == F(5, 4) and N(3) / N(2) == F(5, 4) and N(0) == 18
TXT(M1, ADV, "Nonlinear functions", "medium",
    "The number of members in a school's hiking club t years after 2022 is modeled by the function N(t) = 18(1.25)^t. Which of the following is the best interpretation of the number 1.25 in this context?",
    "The number of members is predicted to increase by 25% each year.",
    ["The number of members is predicted to increase by 1.25 members each year.",   # additive reading
     "The number of members is predicted to increase by 125% each year.",           # factor read as the percent
     "The number of members is predicted to increase by 18% each year."],           # initial value read as the rate
    "Each year the number of members is multiplied by 1.25 = 1 + 0.25, which is a 25% increase per year. The 18 is the number of members in 2022, when t = 0.")

tab = [[18, 12], [14, 21]]
g11 = sum(tab[1]); total = sum(map(sum, tab)); debate = tab[0][1] + tab[1][1]
p = F(tab[1][1], g11)
assert p == F(3, 5) and sum(1 for _ in range(tab[1][1])) / F(g11) == p
MC(M1, PSDA, "Probability and conditional probability", "medium",
   "If one of the grade 11 students in the table is selected at random, what is the probability that the student belongs to the debate club?", p,
   [F(tab[1][1], total),        # debate AND grade 11 out of everyone
    F(g11, total),              # probability of grade 11
    F(tab[1][1], debate)],      # grade 11 given debate (reversed condition)
   f"There are {tab[1][0]} + {tab[1][1]} = {g11} grade 11 students, and {tab[1][1]} of them belong to the debate club. The probability is {tab[1][1]}/{g11} = {fmt(p)}.",
   passage=f"            Robotics   Debate\nGrade 10    {tab[0][0]:<10} {tab[0][1]}\nGrade 11    {tab[1][0]:<10} {tab[1][1]}\n\nThe table shows the numbers of grade 10 and grade 11 students at a school who belong to the robotics club or the debate club. Each of these {total} students belongs to exactly one of the two clubs.")

# ---- hard
slope = F(-3, 4)                                  # 3x + 4y = 20 through (0, 5) and (4, 2)
assert 3 * 0 + 4 * 5 == 20 and 3 * 4 + 4 * 2 == 20 and F(2 - 5, 4 - 0) == slope
bint = 0 - slope * 8
assert bint == 6 and slope * 8 + bint == 0
MC(M1, ALG, "Linear equations in two variables", "hard",
   "In the xy-plane, line p is parallel to the graph of 3x + 4y = 20 and passes through the point (8, 0). What is the y-coordinate of the y-intercept of line p?", bint,
   [0 - F(3, 4) * 8,        # slope sign error (+3/4)
    5,                      # y-intercept of the given line
    0 - F(-4, 3) * 8],      # used −4/3 (reciprocal) as the slope
   "Rewrite 3x + 4y = 20 as y = −(3/4)x + 5; its slope is −3/4, so parallel line p also has slope −3/4. Substituting (8, 0) into y = −(3/4)x + b gives 0 = −6 + b, so b = 6.")

inner = lambda t: (t - 3) * (t + 5)
mn = min(inner(t) for t in GRID)
assert mn == -16 and inner(F(-1)) == -16 and -15 - 1 == mn        # x² + 2x − 15 = (x + 1)² − 16
k = 4 - mn
assert min(inner(t) + k for t in GRID) == 4 and k == 20
SPR(M1, ADV, "Nonlinear functions", "hard",
    "The function g is defined by g(x) = (x − 3)(x + 5) + k, where k is a constant. The minimum value of g(x) is 4. What is the value of k?", k,
    "The graph of y = (x − 3)(x + 5) has x-intercepts 3 and −5, so its vertex is midway between them, at x = (3 + (−5))/2 = −1. There, (x − 3)(x + 5) = (−4)(4) = −16, the minimum value of (x − 3)(x + 5). So the minimum value of g(x) is −16 + k = 4, which gives k = 20.")

c_ = 49 - 25 - 9
assert c_ == 15
for (px, py_) in [(2, 3), (-12, 3), (-5, 10), (-5, -4)]:        # the four points 7 units from (−5, 3)
    assert px ** 2 + 10 * px + py_ ** 2 - 6 * py_ == c_
assert 0 ** 2 + 10 * 0 + 0 - 0 != c_                              # (0, 0) is not on it
SPR(M1, GEO, "Circles", "hard",
    "x² + 10x + y² − 6y = c\n\nIn the given equation, c is a constant. The graph of the equation in the xy-plane is a circle with radius 7. What is the value of c?", c_,
    "Complete the square for x and for y: (x² + 10x + 25) + (y² − 6y + 9) = c + 25 + 9, so (x + 5)² + (y − 3)² = c + 34. The radius is 7, so c + 34 = 7² = 49 and c = 15.")

def n_solutions(a_):     # a(2x − 3) = 8x + 12  ->  (2a − 8)x = 12 + 3a
    lhs, rhs = 2 * a_ - 8, 12 + 3 * a_
    return 1 if lhs != 0 else ("all" if rhs == 0 else 0)
none = [a_ for a_ in GRID if n_solutions(a_) == 0]
assert none == [4]
SPR(M1, ALG, "Linear equations in one variable", "hard",
    "a(2x − 3) = 8x + 12\n\nIn the given equation, a is a constant. The equation has no solution. What is the value of a?", none[0],
    "Distribute: 2ax − 3a = 8x + 12. A linear equation has no solution when the x-terms match but the constants do not. So 2a = 8, which gives a = 4. Then the equation is 8x − 12 = 8x + 12, and −12 ≠ 12, so it has no solution.")

def parabola_hits(cc):   # x² − 6x + 11 = 2x + cc  ->  x² − 8x + (11 − cc) = 0
    disc = 64 - 4 * (11 - cc)
    return 0 if disc < 0 else (1 if disc == 0 else 2)
tangent = [cc for cc in GRID if parabola_hits(cc) == 1]
assert tangent == [-5] and roots(lambda t: t * t - 6 * t + 11 - (2 * t - 5)) == [4]
dis = [-2,     # used −6x, not −8x, in the discriminant
       3,      # the y-coordinate of the point of tangency (4, 3)
       5]      # sign error
assert all(parabola_hits(d) != 1 for d in dis)
MC(M1, ADV, "Systems of equations in two variables", "hard",
   "In the xy-plane, the line y = 2x + c, where c is a constant, intersects the parabola y = x² − 6x + 11 at exactly one point. What is the value of c?", -5, dis,
   "Set the expressions for y equal: x² − 6x + 11 = 2x + c, or x² − 8x + (11 − c) = 0. The graphs meet at exactly one point when this equation has exactly one solution, which happens when its discriminant is 0: (−8)² − 4(1)(11 − c) = 0. So 64 − 44 + 4c = 0, 4c = −20, and c = −5. (The point is (4, 3).)")

ks = [k_ for k_ in GRID if 6 * 10 - (-4) * k_ == 0]         # parallel: determinant 0
assert ks == [-15]
k_ = F(-15)
assert F(6, k_) == F(-4, 10) and F(6, k_) != F(9, 3)        # proportional coefficients, constants not
dis = [F(-20, 3),        # set slope −k/10 equal to 2/3, the reciprocal
       F(20, 3),         # perpendicular condition
       F(15)]            # sign error
assert all(6 * 10 + 4 * d != 0 for d in dis)
MC(M1, ALG, "Systems of two linear equations", "hard",
   "In the xy-plane, the lines with equations 6x − 4y = 9 and kx + 10y = 3, where k is a constant, have no points in common. What is the value of k?", k_, dis,
   "Lines with no points in common are parallel and distinct, so their slopes are equal. Solving 6x − 4y = 9 for y gives y = (3/2)x − 9/4, a slope of 3/2. Solving kx + 10y = 3 for y gives y = −(k/10)x + 3/10, a slope of −k/10. So −k/10 = 3/2, and k = −15. The y-intercepts, −9/4 and 3/10, are different, so the lines are distinct.")

# =====================================================================================
# MODULE 2   (4 easy, 9 medium, 9 hard)
# =====================================================================================

# ---- easy
dis = ["(3, 2)", "(2, −3)", "(0, 6)"]     # sign error; swapped coordinates; y-intercept with the wrong sign
assert 4 * 3 - 3 * (-2) == 18
for d in dis:
    px, py_ = (int(v.replace("−", "-")) for v in d.strip("()").split(", "))
    assert 4 * px - 3 * py_ != 18
TXT(M2, ALG, "Linear equations in two variables", "easy",
    "4x − 3y = 18\n\nWhich of the following points (x, y) is a solution to the given equation?", "(3, −2)", dis,
    "Substitute each point. For (3, −2): 4(3) − 3(−2) = 12 + 6 = 18, so it is a solution. For (3, 2): 12 − 6 = 6. For (2, −3): 8 + 9 = 17. For (0, 6): 0 − 18 = −18.")

key = "3x²(2x + 3)"
fn = lambda t: 6 * t ** 3 + 9 * t ** 2
assert equivalent(key, fn)
dis = ["3x²(2x + 9)",     # did not divide 9 by 3
       "3x³(2 + 3x)",     # factored out x³ from both terms
       "x²(6x + 3)"]      # divided 9 by 3 without factoring out the 3
assert not any(equivalent(d, fn) for d in dis)
TXT(M2, ADV, "Equivalent expressions", "easy", "Which expression is equivalent to 6x³ + 9x²?", key, dis,
    "The greatest common factor of 6x³ and 9x² is 3x². Dividing each term by 3x² gives 2x and 3, so 6x³ + 9x² = 3x²(2x + 3).")

miles, hrs, t_ = 186, 3, 5
ans = F(miles, hrs) * t_
assert ans == 310 and ans * hrs == miles * t_
SPR(M2, PSDA, "Ratios, rates, proportional relationships, and units", "easy",
    f"A bus carrying a school's soccer team to a tournament travels {miles} miles in {hrs} hours. At this rate, how many miles will the bus travel in {t_} hours?", ans,
    f"The bus travels {miles} ÷ {hrs} = {miles // hrs} miles per hour, so in {t_} hours it travels {miles // hrs} × {t_} = {ans} miles.")

w_, l_ = 60, 80
diag = isqrt(w_ * w_ + l_ * l_)
assert diag * diag == w_ * w_ + l_ * l_ == 10000 and diag == 100
MC(M2, GEO, "Right triangles and trigonometry", "easy",
   f"A rectangular soccer practice field is {w_} yards wide and {l_} yards long. What is the length, in yards, of a diagonal of the field?", diag,
   [l_ - w_,            # subtracted the sides
    l_ + w_,            # added the sides
    2 * (l_ + w_)],     # perimeter
   f"A diagonal is the hypotenuse of a right triangle whose legs are the sides of the field: √({w_}² + {l_}²) = √(3,600 + 6,400) = √10,000 = {diag}.")

# ---- medium
eq = "(x + 4)/3 − (x − 2)/5 = 4"
r = roots(lambda t: (t + 4) / F(3) - (t - 2) / F(5) - 4)
assert r == [17] and close(ev(eq.split("=")[0], x=17), 4)
MC(M2, ALG, "Linear equations in one variable", "medium",
   eq + "\n\nWhat is the solution to the given equation?", 17,
   [23,        # did not distribute the minus sign: 5x + 20 − 3x − 6 = 60
    34,        # stopped at 2x = 34
    43],       # added 26 instead of subtracting: 2x = 86
   "Multiply both sides by 15: 5(x + 4) − 3(x − 2) = 60. Distribute: 5x + 20 − 3x + 6 = 60, so 2x + 26 = 60, 2x = 34, and x = 17.")

(n1, c1), (n2, c2), n3 = (2, 95), (5, 170), 8
slope = F(c2 - c1, n2 - n1); icpt = c1 - slope * n1
ans = icpt + slope * n3
assert (slope, icpt, ans) == (25, 45, 245) and c2 + (n3 - n2) * slope == ans
SPR(M2, ALG, "Linear functions", "medium",
    f"The total cost C(n), in dollars, to rent a sports field for n hours is a linear function of n. It costs ${c1} to rent the field for {n1} hours and ${c2} to rent it for {n2} hours. What is the total cost, in dollars, to rent the field for {n3} hours?", ans,
    f"The cost rises by {c2} − {c1} = {c2 - c1} dollars over {n2 - n1} hours, or {slope} dollars per hour. Going from {n2} hours to {n3} hours adds {n3 - n2} × {slope} = {(n3 - n2) * slope} dollars, so C({n3}) = {c2} + {(n3 - n2) * slope} = {ans}.")

sols = [(mm, 64 - mm) for mm in range(65) if 3 * mm + F(9, 2) * (64 - mm) == 231]
assert sols == [(38, 26)]
MC(M2, ALG, "Systems of two linear equations", "medium",
   "Maple Lane Bakery sold 64 items on Saturday. Each item was either a muffin that sold for $3.00 or a scone that sold for $4.50. The bakery's total revenue from these items was $231.00. How many scones did the bakery sell?", 26,
   [13,      # divided the extra $39 by 3 instead of by 1.50
    38,      # number of muffins
    39],     # the extra revenue, 231 − 192
   "Let m and s be the numbers of muffins and scones. Then m + s = 64 and 3m + 4.5s = 231. Substituting m = 64 − s gives 3(64 − s) + 4.5s = 231, so 192 + 1.5s = 231, 1.5s = 39, and s = 26.")

eq = "√(3x + 10) = x"
cand = roots(lambda t: t * t - (3 * t + 10))
assert cand == [-2, 5]
good = [t for t in cand if 3 * t + 10 >= 0 and close(sqrt(3 * t + 10), t)]
assert good == [5] and close(ev("√(3x + 10)", x=5), 5)
MC(M2, ADV, "Nonlinear equations in one variable", "medium",
   eq + "\n\nWhat is the solution to the given equation?", 5,
   [-5,      # sign error in factoring, positive root rejected
    -2,      # extraneous root kept
    2],      # sign error in factoring: (x + 5)(x − 2)
   "Square both sides: 3x + 10 = x², so x² − 3x − 10 = 0 and (x − 5)(x + 2) = 0. The possible solutions are 5 and −2. Check each: √(3(5) + 10) = √25 = 5, which works, but √(3(−2) + 10) = √4 = 2, not −2. So −2 is extraneous, and the solution is 5.")

h = lambda t: 2 * t * t - 12 * t + 7
best = min(GRID, key=h)
assert best == 3 and F(12, 2 * 2) == 3 and h(3) == -11
MC(M2, ADV, "Nonlinear functions", "medium",
   "The function h is defined by h(x) = 2x² − 12x + 7. For what value of x does h(x) reach its minimum value?", 3,
   [-11,     # the minimum value, not where it occurs
    -3,      # sign error in −b/(2a)
    6],      # used −b/a
   "For a quadratic function ax² + bx + c with a > 0, the minimum occurs at x = −b/(2a) = 12/(2 · 2) = 3. (The minimum value itself is h(3) = 18 − 36 + 7 = −11.)")

yfit = lambda t: F(9, 5) * t + 22
inc = yfit(9) - yfit(4)
assert inc == 9 and yfit(10) - yfit(5) == inc
MC(M2, PSDA, "Two-variable data: models and scatterplots", "medium",
   "A garden club recorded, for each of several tomato plants, the average number of hours of sunlight the plant received per day, x, and the plant's height after 6 weeks, y, in centimeters. The line of best fit for the data is y = 1.8x + 22. Based on the line of best fit, how many more centimeters tall is a plant predicted to be for each increase of 5 hours of sunlight per day?", inc,
   [F(9, 5),        # the slope: increase for 1 hour
    22,             # the y-intercept
    yfit(5)],       # predicted height at x = 5
   "The slope, 1.8, is the predicted increase in height for each additional hour of sunlight per day. For 5 additional hours, the predicted increase is 5 × 1.8 = 9 centimeters.", dec=True)

CD, DA, DE = 6, 4, 9
AB = F(DE) * (CD + DA) / CD
assert AB == 15 and F(AB, DE) == F(CD + DA, CD)
MC(M2, GEO, "Lines, angles, and triangles", "medium",
   f"In triangle ABC, point D lies on side AC and point E lies on side BC so that segment DE is parallel to side AB. If CD = {CD}, DA = {DA}, and DE = {DE}, what is the length of AB?", AB,
   [F(DE * CD, CD + DA),     # inverted the scale factor
    DE + DA,                 # added DA to DE
    F(DE * (CD + DA), DA)],  # used DA instead of CD in the ratio
   f"Because DE is parallel to AB, triangle DEC is similar to triangle ABC (they share angle C, and angles CDE and CAB are corresponding angles). So AB/DE = CA/CD = ({CD} + {DA})/{CD} = 10/6. Then AB = {DE} × 10/6 = {fmt(AB)}.", dec=True)

won, played, season = 9, 15, 25
need = next(w for w in range(0, season - played + 1) if F(won + w, season) >= F(7, 10))
assert need == 9 and F(won + need - 1, season) < F(7, 10)
MC(M2, ALG, "Linear inequalities", "medium",
   f"A soccer team has won {won} of its first {played} games this season and will play {season} games in all. What is the minimum number of its remaining games the team must win in order to win at least 70% of its {season} games?", need,
   [7,       # 70% of the 10 remaining games
    8,       # rounded 8.5 down
    18],     # total wins needed, not remaining wins
   f"If the team wins w of its {season - played} remaining games, it wins {won} + w games in all, and it needs {won} + w ≥ 0.70({season}) = 17.5. So w ≥ 8.5. Since w must be a whole number, the minimum is {need}.")

cs = [cc for cc in range(0, 1000) if F(5, 100) * cc + F(2, 100) * 500 == 30]
assert cs == [400]
MC(M2, ALG, "Linear equations in two variables", "medium",
   "Luis has $30 of credit on a prepaid phone plan. Each minute of calls costs $0.05, and each text message costs $0.02. The equation 0.05c + 0.02t = 30 represents the situation in which Luis uses all his credit on c minutes of calls and t text messages. If Luis sends 500 text messages and uses all his credit, how many minutes of calls does he make?", 400,
   [20,      # stopped at 0.05c = 20
    600,     # ignored the texts: 30 ÷ 0.05
    800],    # added the text cost: (30 + 10) ÷ 0.05
   "Substitute t = 500: 0.05c + 0.02(500) = 30, so 0.05c + 10 = 30, 0.05c = 20, and c = 20 ÷ 0.05 = 400.")

# ---- hard
D = lambda t: 300 + (t - 2) * F(120 - 300, 5 - 2)
arrive = roots(D)
assert arrive == [7] and D(5) == 120 and D(0) == 420
SPR(M2, ALG, "Linear functions", "hard",
    "On a road trip, the distance, in miles, that the Okafor family still has to drive is a linear function of the time, in hours, since they started driving. After 2 hours of driving, they have 300 miles left to drive, and after 5 hours of driving, they have 120 miles left. At this rate, how many hours after they started driving will they reach their destination?", arrive[0],
    "The distance left drops by 300 − 120 = 180 miles in 3 hours, a rate of 60 miles per hour. After 5 hours, 120 miles remain, which takes 120 ÷ 60 = 2 more hours. So they arrive 5 + 2 = 7 hours after they started.")

pairs = [(a_, b_) for a_ in range(-30, 31) for b_ in range(-30, 31) if 4 * b_ - (-6) * a_ == 0 and F(a_, 4) == F(15, 10)]
assert pairs == [(6, -9)]
dis = [F(8, 3) - 4,     # scaled by 2/3 instead of 3/2
       6 + 9,           # sign error on b
       9 + (-1)]        # added 5 to each coefficient instead of multiplying
MC(M2, ALG, "Systems of two linear equations", "hard",
   "The system of equations 4x − 6y = 10 and ax + by = 15, where a and b are constants, has infinitely many solutions. What is the value of a + b?", sum(pairs[0]), dis,
   "A system of two linear equations has infinitely many solutions when one equation is a multiple of the other. Since 15 = 1.5 × 10, the second equation must be 1.5 times the first: 1.5(4x − 6y) = 1.5(10), or 6x − 9y = 15. So a = 6 and b = −9, and a + b = −3.")

key = "(3x − 3)/(x² − 9)"
fn = lambda t: 1 / (t - 3) + 2 / (t + 3)
P3 = [F(7, 2), F(5), F(13), F(29, 4), F(41, 3)]
assert equivalent(key, fn, P3)
dis = ["3/(2x)",                 # added numerators and added denominators
       "3/(x² − 9)",             # added numerators over the common denominator
       "(3x + 9)/(x² − 9)"]      # 2(x − 3) taken as 2x + 6
assert not any(equivalent(d, fn, P3) for d in dis)
TXT(M2, ADV, "Equivalent expressions", "hard", "Which expression is equivalent to 1/(x − 3) + 2/(x + 3), for x > 3?", key, dis,
    "Use the common denominator (x − 3)(x + 3) = x² − 9: (x + 3)/(x² − 9) + 2(x − 3)/(x² − 9) = (x + 3 + 2x − 6)/(x² − 9) = (3x − 3)/(x² − 9).")

cands = [cc for cc in range(-60, 61) if (lambda r_: len(r_) == 2 and r_[1] - r_[0] == 6)(roots(lambda t: t * t - 14 * t + cc))]
assert cands == [40]
SPR(M2, ADV, "Nonlinear equations in one variable", "hard",
    "x² − 14x + c = 0\n\nIn the given equation, c is a constant. The equation has two solutions, and one solution is 6 greater than the other. What is the value of c?", cands[0],
    "Completing the square, x² − 14x + c = 0 becomes (x − 7)² = 49 − c, so x = 7 ± √(49 − c). The two solutions differ by 2√(49 − c) = 6, so √(49 − c) = 3, 49 − c = 9, and c = 40. Check: x² − 14x + 40 = (x − 4)(x − 10), and 10 is 6 greater than 4.")

key = "m(d) = 200(9)^d"
truth = lambda d: 200 * 3 ** (2 * d)          # triples every half day
assert all(close(ev(key.split("= ")[1], d=d), truth(d)) for d in (0, F(1, 2), 1, F(3, 2), 2))
dis = ["m(d) = 200(3)^d",          # one tripling per day
       "m(d) = 200(3)^(d/2)",      # triples every 2 days
       "m(d) = 200(6)^d"]          # added the two triplings, 3 + 3
assert all(not close(ev(dd.split("= ")[1], d=1), truth(1)) for dd in dis)
TXT(M2, ADV, "Nonlinear functions", "hard",
    "The mass of a sourdough starter at Juniper Bakery is 200 grams when it is first measured. According to a model, the mass triples every 12 hours. Which function gives the mass m(d), in grams, of the starter d days after it is first measured, according to the model?",
    key, dis,
    "A day has 24 ÷ 12 = 2 twelve-hour periods, so the mass triples twice each day, a growth factor of 3² = 9 per day. Starting from 200 grams, m(d) = 200(9)^d.")

sols = [(t, t * t + 2 * t - 9) for t in GRID if t * t + 2 * t - 9 - 3 * t == 3]
assert sols == [(-3, -6), (4, 15)]
pos = [s for s in sols if s[0] > 0]
assert pos == [(4, 15)] and 15 - 3 * 4 == 3
SPR(M2, ADV, "Systems of equations in two variables", "hard",
    "y = x² + 2x − 9\ny − 3x = 3\n\nIf (x, y) is a solution to the given system of equations and x > 0, what is the value of y?", pos[0][1],
    "The second equation gives y = 3x + 3. Substituting into the first: 3x + 3 = x² + 2x − 9, so x² − x − 12 = 0 and (x − 4)(x + 3) = 0. Since x > 0, x = 4, and y = 3(4) + 3 = 15.")

A_n, B_n, A_g, B_g = 120, 80, F(70, 100), F(75, 100)
seeds = ["A"] * int(A_n * A_g) + ["B"] * int(B_n * B_g)
p = F(seeds.count("B"), len(seeds))
assert p == F(5, 12) and len(seeds) == 144
MC(M2, PSDA, "Probability and conditional probability", "hard",
   f"A gardener planted {A_n} seeds of variety A and {B_n} seeds of variety B. Of the variety A seeds, 70% germinated, and of the variety B seeds, 75% germinated. If one of the seeds that germinated is selected at random, what is the probability that it is a variety B seed?", p,
   [F(60, 200),     # germinated B out of all 200 seeds
    F(80, 200),     # probability a seed is variety B
    F(60, 80)],     # probability a B seed germinated (reversed condition)
   "Variety A: 0.70 × 120 = 84 seeds germinated. Variety B: 0.75 × 80 = 60 seeds germinated. Of the 84 + 60 = 144 seeds that germinated, 60 are variety B, so the probability is 60/144 = 5/12.")

scores = [150] * 12
new_total = 14 * 146 - sum(scores)
ans = F(new_total, 2)
assert ans == 122 and F(sum(scores) + 2 * ans, 14) == 146
SPR(M2, PSDA, "One-variable data: distributions and measures of center and spread", "hard",
    "At a bowling tournament, the 12 original members of a school's bowling club had a mean score of 150. When the scores of the club's 2 newest members are included, the mean score of all 14 members is 146. What is the mean score of the 2 newest members?", ans,
    "The 12 original members scored 12 × 150 = 1,800 points in total. All 14 members scored 14 × 146 = 2,044 points in total. So the 2 newest members scored 2,044 − 1,800 = 244 points, a mean of 244 ÷ 2 = 122.")

ST, RS = 8, 17
RT = isqrt(RS * RS - ST * ST)
assert RT * RT + ST * ST == RS * RS and RT == 15
tanS = F(RT, ST)                              # opposite S is RT, adjacent S is ST
assert close(tanS, 1 / (F(ST) / RT))          # tan S = 1/tan R (complementary angles)
MC(M2, GEO, "Right triangles and trigonometry", "hard",
   "In triangle RST, angle T is a right angle, and sin R = 8/17. What is the value of tan S?", tanS,
   [F(ST, RS),      # sin R itself
    F(ST, RT),      # tan R
    F(RT, RS)],     # cos R, which equals sin S
   "sin R = ST/RS = 8/17, so let ST = 8 and RS = 17. By the Pythagorean theorem, RT = √(17² − 8²) = √225 = 15. For angle S, the opposite side is RT and the adjacent side is ST, so tan S = 15/8.")

# =====================================================================================
# BANK EXTRAS m-134 .. m-153
# =====================================================================================

def conclusion_ok(random_sample_of, random_assignment, claim_scope, causal):
    """Rule check for study conclusions: causal claims need random assignment;
    a claim may reach only the population that was randomly sampled."""
    if causal and not random_assignment: return False
    return claim_scope == random_sample_of

# B1  observational study, random sample of one school
opts = {
    "Among students at the school, playing on a sports team is associated with a higher grade point average, but it cannot be concluded that playing on a team causes the higher average.": ("school", False, True),
    "Playing on a sports team causes students at the school to earn higher grade point averages.": ("school", True, True),
    "Playing on a sports team is associated with a higher grade point average for all high school students in the country.": ("country", False, True),
    "No association can be concluded, because the students were not randomly assigned to play on a team.": ("school", False, False),
}
valid = [o for o, (scope, causal, assoc) in opts.items() if assoc and conclusion_ok("school", False, scope, causal)]
assert len(valid) == 1
TXT(BANK, PSDA, "Evaluating statistical claims", "medium",
    "A researcher selected 300 students at random from a large high school. She found that the students in the sample who play on a school sports team had a higher mean grade point average than the students in the sample who do not. Which of the following is the most appropriate conclusion?",
    valid[0], [o for o in opts if o != valid[0]],
    "Selecting students at random lets the result extend to all students at this school, but the students chose whether to play on a team; they were not randomly assigned. So the study shows an association, not a cause, and it says nothing about students at other schools. An association can still be concluded without random assignment.")

# B2  random sample of city plots + random assignment
opts = {
    "The compost is likely to increase vegetable yield for plots in the city's community gardens.": ("city", True, "likely"),
    "The compost is likely to increase vegetable yield for all vegetable gardens in the country.": ("country", True, "likely"),
    "The compost will increase the vegetable yield of every plot in the city's community gardens.": ("city", True, "every"),
    "Only an association between the compost and vegetable yield can be concluded, because only 80 plots were studied.": ("city", False, "assoc-only"),
}
valid = [o for o, (scope, causal, kind) in opts.items() if kind == "likely" and conclusion_ok("city", True, scope, causal)]
assert len(valid) == 1
TXT(BANK, PSDA, "Evaluating statistical claims", "hard",
    "A community garden association selected 80 plots at random from all the plots in the city's community gardens. It then randomly assigned 40 of the selected plots to receive a new compost and the other 40 to receive no compost. At the end of the season, the plots that received the compost had a significantly greater mean vegetable yield. Which of the following conclusions is best supported by the study?",
    valid[0], [o for o in opts if o != valid[0]],
    "Random assignment of the compost supports a cause-and-effect conclusion, and random selection from all the city's community garden plots lets that conclusion extend to those plots. It cannot extend to gardens across the country, a greater mean yield does not mean every plot improves, and a sample of 80 does not prevent a causal conclusion.")

# B3  biased sample
opts = {
    "The sample consisted only of students who already practice early in the morning.": "selection bias",
    "The sample included fewer than 50 students.": "size (affects precision, not bias)",
    "The survey was conducted by the athletic director rather than by a student.": "irrelevant",
    "More than half of the students surveyed favored early practices.": "a result, not a flaw",
}
valid = [o for o, why in opts.items() if why == "selection bias"]
assert len(valid) == 1
TXT(BANK, PSDA, "Evaluating statistical claims", "easy",
    "To estimate the percentage of students at Northfield High School who favor moving sports practices to early morning, the athletic director surveyed the 45 members of the swim team, which already practices at 6:00 a.m. Of the students surveyed, 80% favored early practices. Which of the following is the most likely reason the survey's result is biased?",
    valid[0], [o for o in opts if o != valid[0]],
    "Swim team members already practice at 6:00 a.m., so they are not representative of all students and are likely to favor early practices more than other students. A small sample makes an estimate less precise but does not by itself bias it, and neither who ran the survey nor the size of the result makes the sample unrepresentative.")

# B4  estimate a population count
ans = F(62, 200) * 4500
assert ans == 1395 and ans / 4500 == F(31, 100)
MC(BANK, PSDA, "Inference from sample statistics and margin of error", "medium",
   "A random sample of 200 students was selected from the 4,500 students in a school district. Of the students in the sample, 62 said they play on a school sports team. Based on the sample, which of the following is the best estimate of the number of students in the district who play on a school sports team?", ans,
   [62,                     # the sample count
    4500 - ans,             # students who do not play
    4500 - 62],             # subtracted the sample count from the district
   "In the sample, 62/200 = 0.31, or 31%, play on a team. Applying this to the district: 0.31 × 4,500 = 1,395 students.")

# B5  margin of error interpretation
lo, hi = 45 - 8, 45 + 8
checks = {
    "It is plausible that fewer than half of all the school's students plan to attend the bake sale.": lo < 50,
    "Exactly 45% of all the school's students plan to attend the bake sale.": False,          # a sample never pins the population exactly
    "Between 37% and 53% of the 120 students surveyed plan to attend the bake sale.": False,   # the sample percentage is exactly 45%
    "A random sample of 60 students would most likely have produced a smaller margin of error.": 1 / sqrt(60) < 1 / sqrt(120),
}
valid = [o for o, ok in checks.items() if ok]
assert len(valid) == 1 and (lo, hi) == (37, 53)
TXT(BANK, PSDA, "Inference from sample statistics and margin of error", "medium",
    "The student council at a high school surveyed a random sample of 120 of the school's students and found that 45% of the students in the sample plan to attend the spring bake sale. The margin of error for this estimate is 8 percentage points. Which of the following conclusions is best supported by the survey?",
    valid[0], [o for o in checks if o != valid[0]],
    "The plausible values for the percentage of all the school's students who plan to attend are 45% ± 8%, or 37% to 53%. That interval includes values below 50%, so it is plausible that fewer than half plan to attend. The interval describes all students, not the 120 surveyed (exactly 45% of them plan to attend), and a smaller sample would give a larger margin of error.")

# B6  plausible population total
lo, hi = F(20, 100) * 1200, F(40, 100) * 1200
dis = [F(30, 100) * 80,       # applied 30% to the 80 sampled plots
       F(10, 100) * 1200,     # applied the 10-point margin to the total
       F(70, 100) * 1200]     # plots without tomato plants
assert (lo, hi) == (240, 480) and lo <= 420 <= hi and not any(lo <= d <= hi for d in dis)
MC(BANK, PSDA, "Inference from sample statistics and margin of error", "hard",
   "A gardening association selected 80 of the 1,200 plots in a large community garden at random and found that 30% of the selected plots had tomato plants. The margin of error for this estimate is 10 percentage points. Which of the following is a plausible value for the total number of plots in the community garden that have tomato plants?", 420, dis,
   "The plausible values for the percentage of all plots with tomato plants are 30% ± 10%, or 20% to 40%. For 1,200 plots, that is 0.20 × 1,200 = 240 to 0.40 × 1,200 = 480 plots. Of the choices, only 420 is in this range.")

# B7  line and parabola, x > 0
sols = [(t, t * t - 4 * t + 5) for t in GRID if t * t - 4 * t + 5 - 2 * t == 12]
assert sols == [(-1, 10), (7, 26)]
p7 = [s for s in sols if s[0] > 0][0]
SPR(BANK, ADV, "Systems of equations in two variables", "medium",
    "y = x² − 4x + 5\ny − 2x = 12\n\nIf (x, y) is a solution to the given system of equations and x > 0, what is the value of x + y?", sum(p7),
    "The second equation gives y = 2x + 12. Substituting into the first: 2x + 12 = x² − 4x + 5, so x² − 6x − 7 = 0 and (x − 7)(x + 1) = 0. Since x > 0, x = 7, and y = 2(7) + 12 = 26. So x + y = 7 + 26 = 33.")

# B8  horizontal line meets a downward parabola twice
def hits(k_):   # −x² + 6x − 5 = k  ->  x² − 6x + (5 + k) = 0
    disc = 36 - 4 * (5 + k_)
    return 0 if disc < 0 else (1 if disc == 0 else 2)
assert max(-t * t + 6 * t - 5 for t in GRID) == 4
dis = [4,     # the maximum value: one point
       5,     # sign of the constant term
       9]     # vertex value of −x² + 6x, ignoring the −5
assert hits(3) == 2 and all(hits(d) != 2 for d in dis)
MC(BANK, ADV, "Systems of equations in two variables", "hard",
   "In the xy-plane, the graph of y = −x² + 6x − 5 intersects the graph of y = k, where k is a constant, at exactly two points. Which of the following could be the value of k?", 3, dis,
   "Complete the square: y = −(x² − 6x + 9) + 9 − 5 = −(x − 3)² + 4. The parabola opens downward and has a maximum value of 4 at x = 3. A horizontal line y = k meets it at exactly two points when k < 4, at one point when k = 4, and at no points when k > 4. Of the choices, only 3 is less than 4.")

# B9  circle and tangent line
sols = [(t, t + 10) for t in GRID if t * t + (t + 10) ** 2 == 50]
assert sols == [(-5, 5)]
SPR(BANK, ADV, "Systems of equations in two variables", "hard",
    "x² + y² = 50\ny = x + 10\n\nIf (x, y) is the solution to the given system of equations, what is the value of y?", sols[0][1],
    "Substitute y = x + 10 into the first equation: x² + (x + 10)² = 50, so 2x² + 20x + 100 = 50. Then 2x² + 20x + 50 = 0, or x² + 10x + 25 = 0, which is (x + 5)² = 0. So x = −5 and y = −5 + 10 = 5.")

# B10  exponential decay from a table
vals = [F(800), F(600), F(450), F(675, 2)]
ratios = {vals[i + 1] / vals[i] for i in range(3)}
diffs = {vals[i + 1] - vals[i] for i in range(3)}
assert ratios == {F(3, 4)} and len(diffs) == 3
key = "V(t) = 800(0.75)^t"
dis = ["V(t) = 800 − 200t", "V(t) = 800(0.25)^t", "V(t) = 600(0.75)^t"]   # linear; rate of decrease as the factor; year-1 value as the start
fits = lambda e: all(close(ev(e.split("= ")[1], t=i), v) for i, v in enumerate(vals))
assert fits(key) and not any(fits(d) for d in dis)
TXT(BANK, PSDA, "Two-variable data: models and scatterplots", "medium",
    "Which of the following functions best models the value V(t), in dollars, of the phone t years after it was purchased?", key, dis,
    "Each year the value is multiplied by the same factor: 600/800 = 450/600 = 337.50/450 = 0.75. A constant ratio means exponential decay with a factor of 0.75, starting at 800. The value does not drop by a constant amount (it drops by 200, then 150, then 112.50), so a linear model does not fit.",
    passage="Years since purchase   Value (dollars)\n0                      800\n1                      600\n2                      450\n3                      337.50\n\nThe table shows the value of a phone, in dollars, t years after it was purchased, for t = 0 through 3.")

# B11  solve a line of best fit for x
wk = roots(lambda t: F(7, 2) * t + 4 - 39)
assert wk == [10]
SPR(BANK, PSDA, "Two-variable data: models and scatterplots", "easy",
    "A garden club measured the heights of its sunflower plants each week. The line of best fit for the data is y = 3.5x + 4, where y is the predicted height, in centimeters, of a plant x weeks after planting. According to the line of best fit, how many weeks after planting will a plant's predicted height be 39 centimeters?", wk[0],
    "Set 3.5x + 4 = 39. Subtract 4: 3.5x = 35. Divide by 3.5: x = 10.")

# B12  exponential growth rate from two points
bs = [F(n, 100) for n in range(1, 300) if F(n, 100) ** 2 * 250 == 360]
assert bs == [F(6, 5)]
rate = (bs[0] - 1) * 100
assert rate == 20
MC(BANK, PSDA, "Two-variable data: models and scatterplots", "hard",
   "A school's sports podcast tracked its number of subscribers after it launched. An exponential function fit to the data estimates 250 subscribers at launch and 360 subscribers 2 years after launch. According to the model, by what percent does the estimated number of subscribers increase each year?", rate,
   [22,        # halved the two-year increase of 44%
    44,        # the increase over 2 years
    55],       # the linear rate, 110 ÷ 2 = 55 subscribers per year, read as a percent
   "An exponential model has the form S(t) = 250b^t. The model gives 250b² = 360, so b² = 1.44 and b = 1.2. A growth factor of 1.2 is a 20% increase each year. (The 44% increase happens over 2 years.)", suffix="%")

# B13  simple probability
box = ["blueberry"] * 6 + ["bran"] * 4 + ["lemon"] * 10
p = F(box.count("lemon"), len(box))
assert p == F(1, 2)
SPR(BANK, PSDA, "Probability and conditional probability", "easy",
    "A bakery box contains 6 blueberry muffins, 4 bran muffins, and 10 lemon muffins. If one muffin is selected from the box at random, what is the probability that it is a lemon muffin?", p,
    "There are 6 + 4 + 10 = 20 muffins, and 10 of them are lemon, so the probability is 10/20 = 1/2.", dec=False)

# B14  conditional probability from a table
tab = {("Prepaid", "u30"): 45, ("Prepaid", "o30"): 30, ("Monthly", "u30"): 55, ("Monthly", "o30"): 120}
o30 = tab[("Prepaid", "o30")] + tab[("Monthly", "o30")]
tot = sum(tab.values())
p = F(tab[("Prepaid", "o30")], o30)
assert p == F(1, 5) and tot == 250
MC(BANK, PSDA, "Probability and conditional probability", "medium",
   "If one of the customers who is 30 or older is selected at random, what is the probability that the customer has a prepaid plan?", p,
   [F(30, tot),       # prepaid AND 30+ out of everyone
    F(30, 75),        # 30+ given prepaid (reversed condition)
    F(o30, tot)],     # probability of being 30 or older
   "There are 30 + 120 = 150 customers who are 30 or older, and 30 of them have prepaid plans. The probability is 30/150 = 1/5.",
   passage="           Under 30   30 or older\nPrepaid    45         30\nMonthly    55         120\n\nThe table shows the type of phone plan, prepaid or monthly, chosen by each of 250 customers of a phone company, by age group.")

# B15  conditional probability from percentages (Bayes)
campers = 1000
soc = campers * 40 // 100; both = soc * 30 // 100; bb_only = (campers - soc) * 50 // 100
p = F(both, both + bb_only)
assert p == F(2, 7) and F(4, 10) * F(3, 10) / (F(4, 10) * F(3, 10) + F(6, 10) * F(5, 10)) == p
MC(BANK, PSDA, "Probability and conditional probability", "hard",
   "At a summer sports camp, 40% of the campers play soccer. Of the campers who play soccer, 30% also play basketball. Of the campers who do not play soccer, 50% play basketball. If a camper who plays basketball is selected at random, what is the probability that the camper plays soccer?", p,
   [F(12, 100),       # probability of soccer AND basketball
    F(3, 10),         # basketball given soccer (reversed condition)
    F(4, 10)],        # probability of soccer
   "Soccer and basketball: 0.40 × 0.30 = 0.12 of the campers. Basketball but not soccer: 0.60 × 0.50 = 0.30 of the campers. So 0.12 + 0.30 = 0.42 of the campers play basketball, and the probability is 0.12/0.42 = 2/7.")

# B16  linear system word problem
sols = [(t2, 10 - t2) for t2 in range(11) if 2 * t2 + 3 * (10 - t2) == 23]
assert sols == [(7, 3)]
MC(BANK, ALG, "Systems of two linear equations", "medium",
   "In a basketball game, Keisha scored 23 points, all on 2-point and 3-point shots. She made 10 shots in all. How many 3-point shots did Keisha make?", 3,
   [5,       # assumed equal numbers of each shot
    7,       # the number of 2-point shots
    13],     # subtracted the shots from the points
   "Let t be the number of 2-point shots and h the number of 3-point shots. Then t + h = 10 and 2t + 3h = 23. Substituting t = 10 − h: 2(10 − h) + 3h = 23, so 20 + h = 23 and h = 3.")

# B17  compare two plans
cheaperA = [F(q, 4) for q in range(0, 4 * 400) if 40 + F(1, 10) * F(q, 4) < 25 + F(1, 4) * F(q, 4)]
assert min(cheaperA) == F(401, 4) and F(100) not in cheaperA and all(v > 100 for v in cheaperA)
TXT(BANK, ALG, "Linear inequalities", "medium",
    "Phone plan A costs $40 per month plus $0.10 per minute of calls. Phone plan B costs $25 per month plus $0.25 per minute of calls. For which numbers of minutes of calls per month, m, does plan A cost less than plan B?",
    "m > 100",
    ["m < 100",      # reversed the inequality
     "m > 60",       # divided 15 by 0.25 instead of 0.15
     "m > 150"],     # divided 15 by 0.10 instead of 0.15
    "Plan A costs less when 40 + 0.10m < 25 + 0.25m. Subtract 25 and 0.10m from both sides: 15 < 0.15m. Divide by 0.15: m > 100.")

# B18  rational equation
eq = "x/(x − 2) + 3/(x + 4) = 1"
r = roots(lambda t: t / (t - 2) + F(3) / (t + 4) - 1)
assert r == [F(-2, 5)] and close(ev(eq.split("=")[0], x=F(-2, 5)), 1)
SPR(BANK, ADV, "Nonlinear equations in one variable", "hard",
    eq + "\n\nWhat is the solution to the given equation?", r[0],
    "Multiply both sides by (x − 2)(x + 4): x(x + 4) + 3(x − 2) = (x − 2)(x + 4). So x² + 4x + 3x − 6 = x² + 2x − 8, which gives 7x − 6 = 2x − 8, 5x = −2, and x = −2/5. This value does not make either denominator 0, so it is the solution.", dec=False)

# B19  circle from a diameter
P, Q = (-1, 4), (7, -2)
cx, cy = F(P[0] + Q[0], 2), F(P[1] + Q[1], 2)
r2 = (P[0] - cx) ** 2 + (P[1] - cy) ** 2
assert (cx, cy, r2) == (3, 1, 25) and (Q[0] - cx) ** 2 + (Q[1] - cy) ** 2 == r2
key = "(x − 3)² + (y − 1)² = 25"
dis = ["(x − 3)² + (y − 1)² = 100",     # used the diameter as the radius
       "(x + 3)² + (y + 1)² = 25",      # signs of the center reversed
       "(x − 4)² + (y + 3)² = 25"]      # half the differences instead of the midpoint
on = lambda e, pt: close(ev(e.split("=")[0], x=pt[0], y=pt[1]), ev(e.split("=")[1], x=pt[0], y=pt[1]))
assert on(key, P) and on(key, Q) and not any(on(d, P) and on(d, Q) for d in dis)
TXT(BANK, GEO, "Circles", "hard",
    "In the xy-plane, the points (−1, 4) and (7, −2) are the endpoints of a diameter of a circle. Which equation represents the circle?", key, dis,
    "The center is the midpoint of the diameter: ((−1 + 7)/2, (4 + (−2))/2) = (3, 1). The diameter's length is √((7 − (−1))² + (−2 − 4)²) = √(64 + 36) = 10, so the radius is 5 and r² = 25. The equation is (x − 3)² + (y − 1)² = 25.")

# B20  percent of a percent
members = 80
gk = members * F(60, 100) * F(25, 100)
assert gk == 12 and gk == F(15, 100) * members
SPR(BANK, PSDA, "Percentages", "easy",
    f"A school's sports club has {members} members. Of the members, 60% play soccer, and 25% of the members who play soccer are goalkeepers. How many of the club's members are soccer goalkeepers?", gk,
    "The number of soccer players is 0.60 × 80 = 48. The number of goalkeepers is 0.25 × 48 = 12.")


# =====================================================================================
# ADAPTIVE MODULE 2
#   harder Module 2 (pt1-m2.json): the Module 2 above with its 4 easy items replaced by
#     new medium/hard items of the same skills; the 4 easy items move to the bank.
#   easier Module 2 (pt1-m2e.json): 22 new items, 9 easy / 10 medium / 3 hard.
# =====================================================================================
HARD_NEW = {}

# replaces "4x − 3y = 18 ... which point" (Linear equations in two variables, easy)
def intercepts(e):
    lhs, rhs = e.split(" = ")
    a_, b_, c0 = ev(lhs, x=1, y=0), ev(lhs, x=0, y=1), F(rhs.replace("−", "-"))
    return (c0 / a_, c0 / b_)
key = "2x − 3y = 12"
dis = ["3x − 2y = 12",     # intercepts swapped
       "2x + 3y = 12",     # y-intercept sign error
       "4x − 6y = 12"]     # intercepts halved
assert intercepts(key) == (6, -4) and all(intercepts(d) != (6, -4) for d in dis)
assert 2 * 6 - 3 * 0 == 12 and 2 * 0 - 3 * (-4) == 12
HARD_NEW["le2v"] = TXT([], ALG, "Linear equations in two variables", "medium",
    "In the xy-plane, the graph of which of the following equations has an x-intercept at (6, 0) and a y-intercept at (0, −4)?", key, dis,
    "Check the intercepts. For 2x − 3y = 12, setting y = 0 gives 2x = 12, so x = 6, and setting x = 0 gives −3y = 12, so y = −4. The other graphs have intercepts (4, 0) and (0, −6) for 3x − 2y = 12, (6, 0) and (0, 4) for 2x + 3y = 12, and (3, 0) and (0, −2) for 4x − 6y = 12.")

# replaces "6x³ + 9x²" (Equivalent expressions, easy)
poly_ = lambda t: 4 * t * t - 20 * t + 31
assert equivalent("4(x − 5/2)² + 6", poly_) and min(poly_(t) for t in GRID) == 6
k_ = F(6)
HARD_NEW["equiv"] = MC([], ADV, "Equivalent expressions", "hard",
   "4x² − 20x + 31\n\nThe given expression can be written in the form a(x − h)² + k, where a, h, and k are constants. What is the value of k?", k_,
   [31 - 100,             # completed the square on x² − 20x without factoring out the 4
    31 - F(25, 4),        # did not multiply 25/4 by 4
    31],                  # took the constant term
   "Factor 4 out of the x-terms: 4(x² − 5x) + 31. Complete the square: x² − 5x = (x − 5/2)² − 25/4. So the expression equals 4(x − 5/2)² − 4(25/4) + 31 = 4(x − 5/2)² − 25 + 31 = 4(x − 5/2)² + 6, and k = 6.", dec=True)

# replaces "bus travels 186 miles" (Ratios, rates, proportional relationships, and units, easy grid-in)
mpg, price, dist = 32, F(18, 5), 280
cost = F(dist, mpg) * price
assert cost == F(63, 2) and price / mpg * dist == cost          # gallons first, then cost per mile
HARD_NEW["ratio"] = SPR([], PSDA, "Ratios, rates, proportional relationships, and units", "medium",
    f"On a road trip, Priya's car travels {mpg} miles per gallon of gasoline, and gasoline costs $3.60 per gallon. What is the cost, in dollars, of the gasoline the car uses to travel {dist} miles?", cost,
    f"The car uses {dist} ÷ {mpg} = {fmt(F(dist, mpg), True)} gallons of gasoline. At $3.60 per gallon, that costs {fmt(F(dist, mpg), True)} × 3.60 = {fmt(cost, True)} dollars.")

# replaces "60 by 80 field diagonal" (Right triangles and trigonometry, easy)
AB_, cosA = 26, F(5, 13)
AC_ = AB_ * cosA; BC_ = isqrt(AB_ ** 2 - int(AC_) ** 2)
assert AC_ == 10 and BC_ ** 2 + AC_ ** 2 == AB_ ** 2 and F(AC_, AB_) == cosA
area = F(AC_ * BC_, 2)
assert area == 120
HARD_NEW["trig"] = MC([], GEO, "Right triangles and trigonometry", "hard",
   f"In right triangle ABC, angle C is the right angle, AB = {AB_}, and cos A = 5/13. What is the area of triangle ABC?", area,
   [F(AC_ * AB_, 2),      # used the hypotenuse as a leg with AC
    AC_ * BC_,            # forgot the 1/2
    F(BC_ * AB_, 2)],     # used the hypotenuse as a leg with BC
   f"cos A = AC/AB, so AC = {AB_} × 5/13 = {AC_}. By the Pythagorean theorem, BC = √({AB_}² − {AC_}²) = √{AB_ ** 2 - AC_ ** 2} = {BC_}. The legs are AC and BC, so the area is (1/2)({AC_})({BC_}) = {area}.")

# ---------------------------------------------------------------- easier Module 2
M2E = []
# easy
r = roots(lambda t: 8 * t - 5 - (3 * t + 20))
assert r == [5]
MC(M2E, ALG, "Linear equations in one variable", "easy",
   "8x − 5 = 3x + 20\n\nWhat is the solution to the given equation?", r[0],
   [F(15, 11),     # moved both terms across without changing signs: 11x = 15
    3,             # subtracted 5 instead of adding: 5x = 15
    25],           # did not divide by 5
   "Subtract 3x from both sides: 5x − 5 = 20. Add 5 to both sides: 5x = 25. Divide by 5: x = 5.")

key = "5x² − 2x + 4"
fn = lambda t: (4 * t * t + 3 * t - 2) + (t * t - 5 * t + 6)
dis = ["5x² + 8x + 4",     # dropped the sign of −5x
       "5x² − 2x − 8",     # subtracted the constants
       "4x² − 2x + 4"]     # left out the second x² term
assert equivalent(key, fn) and not any(equivalent(d, fn) for d in dis)
TXT(M2E, ADV, "Equivalent expressions", "easy", "Which expression is equivalent to (4x² + 3x − 2) + (x² − 5x + 6)?", key, dis,
    "Combine like terms: (4x² + x²) + (3x − 5x) + (−2 + 6) = 5x² − 2x + 4.")

rye = F(250 * 18, 100)
assert rye == 45 and rye / 250 == F(9, 50)
SPR(M2E, PSDA, "Percentages", "easy",
    "Rosa's Bakery sold 250 loaves of bread on Saturday, and 18% of the loaves sold were rye bread. How many loaves of rye bread did the bakery sell on Saturday?", rye,
    "18% of 250 is 0.18 × 250 = 45.")

d_ = 14
circ = F(d_)                            # coefficient of π
assert circ == 2 * F(d_, 2)             # πd = 2πr
dis = ["7π",      # used the radius in C = πd
       "28π",     # used C = 2πd
       "49π"]     # area, πr²
assert all(F(d.rstrip("π")) != circ for d in dis)
TXT(M2E, GEO, "Circles", "easy", f"A circular garden has a diameter of {d_} feet. What is the circumference of the garden, in feet?", f"{d_}π", dis,
    f"Circumference = π × diameter = π({d_}) = {d_}π feet. (Equivalently, 2πr with radius r = 7.)")

key = "C(t) = 0.25t + 15"
truth = lambda t: 15 + F(1, 4) * t
dis = ["C(t) = 15t + 0.25", "C(t) = 15.25t", "C(t) = 0.25t − 15"]   # swapped rate and fee; combined them; subtracted the fee
same = lambda e: all(close(ev(e.split("= ")[1], t=t), truth(t)) for t in (0, 4, 30))
assert same(key) and not any(same(d) for d in dis)
TXT(M2E, ALG, "Linear functions", "easy",
    "Nia's phone plan costs $15 per month plus $0.25 for each text message she sends. Which function gives the total monthly cost C(t), in dollars, if Nia sends t text messages in a month?", key, dis,
    "The $15 is charged once each month, and each text message adds $0.25, so t messages add 0.25t dollars. The total is C(t) = 0.25t + 15.")

p3 = 5 * 2 ** 3
assert p3 == 40 and close(ev("5(2)^x", x=3), 40)
MC(M2E, ADV, "Nonlinear functions", "easy",
   "The function p is defined by p(x) = 5(2)^x. What is the value of p(3)?", p3,
   [5 + 2 ** 3,    # added 5 instead of multiplying
    5 * 3,         # ignored the base 2
    5 * 2 * 3],    # multiplied by the exponent
   "Substitute x = 3: p(3) = 5(2)³ = 5(8) = 40.")

runs = [4, 9, 2, 7, 4, 11, 5]
srt = sorted(runs); med = srt[3]
assert med == 5 and sum(1 for v in runs if v < med) == sum(1 for v in runs if v > med) == 3
MC(M2E, PSDA, "One-variable data: distributions and measures of center and spread", "easy",
   ", ".join(map(str, runs)) + "\n\nThe list gives the numbers of runs a softball team scored in its first 7 games of the season. What is the median of the data?", med,
   [Counter(runs).most_common(1)[0][0],    # the mode
    F(sum(runs), len(runs)),               # the mean
    runs[3]],                              # middle of the unsorted list
   "In order, the values are 2, 4, 4, 5, 7, 9, 11. The median is the middle (fourth) value, 5.")

sx, sy = 5, 9
assert sy == sx + 4 and 3 * sx + sy == 24 and roots(lambda t: 3 * t + (t + 4) - 24) == [5]
dis = ["(9, 5)", "(4, 12)", "(2, 6)"]     # swapped; fits only the second equation; fits only the first
for d in dis:
    px, py_ = map(int, d.strip("()").split(", "))
    assert not (py_ == px + 4 and 3 * px + py_ == 24)
TXT(M2E, ALG, "Systems of two linear equations", "easy",
    "y = x + 4\n3x + y = 24\n\nWhat is the solution (x, y) to the given system of equations?", f"({sx}, {sy})", dis,
    "Substitute y = x + 4 into the second equation: 3x + x + 4 = 24, so 4x = 20 and x = 5. Then y = 5 + 4 = 9.")

big = [a_ + 36 for a_ in range(0, 181) if a_ + (a_ + 36) == 180]
assert big == [108]
SPR(M2E, GEO, "Lines, angles, and triangles", "easy",
    "Two angles are supplementary. The measure of one angle is 36° greater than the measure of the other angle. What is the measure, in degrees, of the larger angle?", big[0],
    "Let the smaller angle measure a degrees. Then a + (a + 36) = 180, so 2a = 144 and a = 72. The larger angle measures 72 + 36 = 108°.")

# medium
slope = F(7 - (-3), 5 - 1)
assert slope == F(5, 2) and -3 + slope * 4 == 7
MC(M2E, ALG, "Linear equations in two variables", "medium",
   "In the xy-plane, a line passes through the points (1, −3) and (5, 7). What is the slope of the line?", slope,
   [-slope,            # sign error
    1 / slope,         # run over rise
    F(7 - 3, 5 - 1)],  # dropped the sign of −3
   "Slope = (change in y)/(change in x) = (7 − (−3))/(5 − 1) = 10/4 = 5/2.")

r = roots(lambda t: t * t - (6 * t + 16))
assert r == [-2, 8]
SPR(M2E, ADV, "Nonlinear equations in one variable", "medium",
    "x² = 6x + 16\n\nWhat is the positive solution to the given equation?", max(r),
    "Subtract 6x and 16 from both sides: x² − 6x − 16 = 0, which factors as (x − 8)(x + 2) = 0. The solutions are 8 and −2, so the positive solution is 8.")

mins = F(3000, F(400, 80)) / 60
assert mins == 10 and F(3000, 400) * 80 / 60 == mins
MC(M2E, PSDA, "Ratios, rates, proportional relationships, and units", "medium",
   "A runner on a school's track team runs 400 meters in 80 seconds. At this rate, how many minutes will it take the runner to run 3,000 meters?", mins,
   [F(3000, 400),     # number of 400-meter laps
    F(3000, 80),      # divided the distance by the time for one lap
    600],             # seconds, not minutes
   "The runner's rate is 400 ÷ 80 = 5 meters per second. Running 3,000 meters takes 3,000 ÷ 5 = 600 seconds, which is 600 ÷ 60 = 10 minutes.", dec=True)

sol = lambda pred: [t for t in GRID if pred(t)]
truth = sol(lambda t: -3 * (t - 2) > 15)
opts = {"x < −3": lambda t: t < -3, "x > −3": lambda t: t > -3, "x < −7": lambda t: t < -7, "x > −7": lambda t: t > -7}
match = [o for o, f in opts.items() if sol(f) == truth]
assert match == ["x < −3"]
TXT(M2E, ALG, "Linear inequalities", "medium",
    "−3(x − 2) > 15\n\nWhich of the following is the solution to the given inequality?", "x < −3",
    ["x > −3",      # did not reverse the inequality
     "x < −7",      # distributed −3(x − 2) as −3x − 6
     "x > −7"],     # both errors
    "Distribute: −3x + 6 > 15. Subtract 6 from both sides: −3x > 9. Dividing both sides by −3 reverses the inequality: x < −3.")

key = "(2x − 7)(2x + 7)"
fn = lambda t: 4 * t * t - 49
dis = ["(2x − 7)²", "(2x + 7)²", "(4x − 7)(x + 7)"]    # square of a difference; square of a sum; split 4x² as 4x · x
assert equivalent(key, fn) and not any(equivalent(d, fn) for d in dis)
TXT(M2E, ADV, "Equivalent expressions", "medium", "Which expression is equivalent to 4x² − 49?", key, dis,
    "4x² − 49 is a difference of two squares: (2x)² − 7². So it factors as (2x − 7)(2x + 7).")

L_, P_ = 15, 48
W_ = F(P_ - 2 * L_, 2)
assert W_ == 9 and 2 * (L_ + W_) == P_
MC(M2E, GEO, "Area and volume", "medium",
   f"A rectangular garden plot has a length of {L_} feet and a perimeter of {P_} feet. What is the area of the plot, in square feet?", L_ * W_,
   [L_ * (P_ - 2 * L_),     # did not halve 48 − 30
    L_ * (P_ - L_),         # subtracted only one length
    L_ * P_],               # multiplied the length by the perimeter
   f"The perimeter is 2({L_}) + 2w = {P_}, so 2w = {P_ - 2 * L_} and w = {W_}. The area is {L_} × {W_} = {L_ * W_} square feet.")

R_ = lambda t: 12400 + 55 * t
hrs = roots(lambda t: R_(t) - 12730)
assert hrs == [6]
SPR(M2E, ALG, "Linear functions", "medium",
    "At the start of a road trip, the odometer of the Reyes family's van read 12,400 miles. The odometer reading R, in miles, t hours after the start of the trip is modeled by the function R(t) = 12,400 + 55t. According to the model, how many hours after the start of the trip will the odometer read 12,730 miles?", hrs[0],
    "Set 12,400 + 55t = 12,730. Subtract 12,400 from both sides: 55t = 330. Divide by 55: t = 6.")

f_ = lambda t: t * t - 8 * t + 12
assert roots(f_) == [2, 6]
opts = {"(2, 0) and (6, 0)": [(2, 0), (6, 0)], "(−2, 0) and (−6, 0)": [(-2, 0), (-6, 0)],
        "(1, 0) and (12, 0)": [(1, 0), (12, 0)], "(0, 2) and (0, 6)": [(0, 2), (0, 6)]}
good = [o for o, pts in opts.items() if all(f_(px) == py_ and py_ == 0 for px, py_ in pts)]
assert good == ["(2, 0) and (6, 0)"]
TXT(M2E, ADV, "Nonlinear functions", "medium",
    "The function f is defined by f(x) = x² − 8x + 12. At which points does the graph of y = f(x) cross the x-axis in the xy-plane?", good[0],
    ["(−2, 0) and (−6, 0)",    # sign error in the factors
     "(1, 0) and (12, 0)",     # a factor pair of 12 that does not add to 8
     "(0, 2) and (0, 6)"],     # coordinates reversed
    "The graph crosses the x-axis where f(x) = 0. The equation x² − 8x + 12 = 0 factors as (x − 2)(x − 6) = 0, so x = 2 or x = 6. The points are (2, 0) and (6, 0).")

fl = {("Tulip", "White"): 24, ("Tulip", "Yellow"): 16, ("Daffodil", "White"): 6, ("Daffodil", "Yellow"): 34}
yellow = fl[("Tulip", "Yellow")] + fl[("Daffodil", "Yellow")]; totf = sum(fl.values())
p = F(fl[("Daffodil", "Yellow")], yellow)
assert p == F(17, 25) and totf == 80
MC(M2E, PSDA, "Probability and conditional probability", "medium",
   "If one of the yellow flowers is selected at random, what is the probability that it is a daffodil?", p,
   [F(34, totf),        # yellow daffodils out of all flowers
    F(yellow, totf),    # probability a flower is yellow
    F(34, 40)],         # yellow given daffodil (reversed condition)
   "There are 16 + 34 = 50 yellow flowers, and 34 of them are daffodils. The probability is 34/50 = 17/25.",
   passage="           White   Yellow\nTulip      24      16\nDaffodil   6       34\n\nThe table shows the types and colors of the 80 flowers a school's garden club planted this spring.")

sols = [(t, 6 * t) for t in GRID if 3 * t * t == 6 * t]
assert sols == [(0, 0), (2, 12)]
dis = ["(−2, 12)", "(1, 3)", "(4, 24)"]
for d in dis:
    px, py_ = (int(v.replace("−", "-")) for v in d.strip("()").split(", "))
    assert not (py_ == 3 * px * px and py_ == 6 * px)
TXT(M2E, ADV, "Systems of equations in two variables", "medium",
    "y = 3x²\ny = 6x\n\nWhich of the following is a solution (x, y) to the given system of equations?", "(2, 12)", dis,
    "Set 3x² = 6x: 3x² − 6x = 0, so 3x(x − 2) = 0 and x = 0 or x = 2. When x = 2, y = 6(2) = 12, so (2, 12) is a solution. The other choices each fail an equation: for (−2, 12), 6(−2) = −12; for (1, 3), 6(1) = 6; for (4, 24), 3(4)² = 48.")

# hard
ks = [kk for kk in GRID if all(F(3, 4) * (8 * t - 12) == 2 * (3 * t + kk) for t in (0, 1, 5))]
assert ks == [F(-9, 2)]
SPR(M2E, ALG, "Linear equations in one variable", "hard",
    "(3/4)(8x − 12) = 2(3x + k)\n\nIn the given equation, k is a constant. The equation has infinitely many solutions. What is the value of k?", ks[0],
    "Distribute on both sides: (3/4)(8x − 12) = 6x − 9, and 2(3x + k) = 6x + 2k. The equation 6x − 9 = 6x + 2k is true for every value of x exactly when −9 = 2k, so k = −9/2, or −4.5.")

B_ = lambda t: 100 * F(4, 5) ** (F(t) / 2) if F(t) / 2 == int(F(t) / 2) else None
assert B_(4) == 64 and 100 * F(4, 5) * F(4, 5) == 64
MC(M2E, ADV, "Nonlinear functions", "hard",
   "The charge remaining in a phone's battery, as a percent of full charge, t hours after the phone is unplugged is modeled by the function B(t) = 100(0.8)^(t/2). According to the model, what percent of full charge remains 4 hours after the phone is unplugged?", B_(4),
   [100 * F(4, 5) ** 4,     # used t instead of t/2
    100 - 20 * 2,           # took off 20 percentage points every 2 hours
    100 * F(4, 5)],         # applied only one 2-hour period
   "Substitute t = 4: B(4) = 100(0.8)^(4/2) = 100(0.8)² = 100(0.64) = 64.", dec=True)

boxes = [(s6, 40 - s6) for s6 in range(41) if 6 * s6 + 4 * (40 - s6) == 196]
assert boxes == [(18, 22)]
rev = 15 * boxes[0][0] + 11 * boxes[0][1]
assert rev == 512
SPR(M2E, ALG, "Systems of two linear equations", "hard",
    "A bakery sells muffins only in boxes of 4 and boxes of 6. On Friday, the bakery sold 40 boxes containing a total of 196 muffins. Each box of 4 muffins sells for $11, and each box of 6 muffins sells for $15. What was the bakery's total revenue, in dollars, from these 40 boxes?", rev,
    "Let s be the number of boxes of 6 and f the number of boxes of 4. Then s + f = 40 and 6s + 4f = 196. Substituting f = 40 − s: 6s + 160 − 4s = 196, so 2s = 36, s = 18, and f = 22. The revenue is 18 × 15 + 22 × 11 = 270 + 242 = 512 dollars.")

# =====================================================================================
# finish: key positions, ids, validation, output
# =====================================================================================
def place_text_keys(items):
    """Numeric keys sit where ascending order puts them; slot each non-numeric
    key into the least-used position so the four positions come out even."""
    count = Counter(it["answer"] for it in items if "_key" not in it and it.get("type") != "spr")
    for it in items:
        if "_key" in it:
            slot = min(range(4), key=lambda i: (count[i], i))
            ch = list(it.pop("_dis")); key = it.pop("_key")
            ch.insert(slot, key)
            it["choices"], it["answer"] = ch, slot
            count[slot] += 1
    return count

ORDER = ["id", "section", "domain", "skill", "difficulty", "stem", "type", "choices", "answer", "explanation", "passage"]
def finish(items, ids):
    out = []
    for it, i in zip(items, ids):
        it["id"] = i
        out.append({k: it[k] for k in ORDER if k in it and it[k] is not None})
    return out

SKILLS = json.load(open(os.path.join(HERE, "..", "data", "questions.json")))["meta"]["skills"]["math"]
BANK_Q = json.load(open(os.path.join(HERE, "..", "data", "questions.json")))["questions"]
RANK = {"easy": 0, "medium": 1, "hard": 2}

def as_num(s):
    s = s.replace("−", "-").replace(",", "").rstrip("%")
    try: return F(s)
    except (ValueError, ZeroDivisionError): return None

def validate(items, n, mix=None, spr_range=None, module=False):
    assert len(items) == n
    assert len({it["id"] for it in items}) == n
    for it in items:
        assert it["section"] == "math" and it["skill"] in SKILLS[it["domain"]], it["id"]
        assert it["difficulty"] in RANK
        if it.get("type") == "spr":
            assert "choices" not in it and isinstance(it["answer"], str)
        else:
            assert "type" not in it and len(it["choices"]) == 4 and len(set(it["choices"])) == 4
            assert isinstance(it["answer"], int) and 0 <= it["answer"] < 4
            nums = [as_num(c) for c in it["choices"]]
            if all(v is not None for v in nums): assert nums == sorted(nums), it["id"]
        text = " ".join([it["stem"], it["explanation"], it.get("passage", "")] + it.get("choices", []))
        assert not re.search(r"(^|[\s(=\d])-\s?[\dx(]", text), (it["id"], "ASCII minus in displayed math")
        assert not re.search(r"\b(figure|graph shown|shown in the|shown below|shown above)\b", text, re.I), it["id"]
        assert not any(q["stem"] == it["stem"] and q["id"] != it["id"] for q in BANK_Q), it["id"]   # (bank-m-1 has since been merged into the bank)
    if module:
        doms = Counter(it["domain"] for it in items)
        assert doms == Counter({ALG: 8, ADV: 7, PSDA: 4, GEO: 3}), doms
        assert Counter(it["difficulty"] for it in items) == Counter(mix)
        assert [RANK[it["difficulty"]] for it in items] == sorted(RANK[it["difficulty"]] for it in items), "not easiest to hardest"
        ns = sum(it.get("type") == "spr" for it in items)
        assert spr_range[0] <= ns <= spr_range[1], ns
    pos = Counter(it["answer"] for it in items if it.get("type") != "spr")
    assert max(pos.values()) - min(pos[i] for i in range(4)) <= 1, pos
    return pos


# ---------------------------------------------------------------- assemble
# interleave domains within each difficulty band of the original Module 2 (written grouped by domain)
M2[:] = [M2[i] for i in [0, 1, 2, 3, 4, 7, 5, 9, 12, 8, 6, 10, 11, 13, 15, 19, 16, 14, 21, 17, 20, 18]]
assert len({id(it) for it in M2}) == 22

m1pos = place_text_keys(M1); m2pos = place_text_keys(M2); bpos = place_text_keys(BANK)
m1 = finish(M1, [f"pt1-m1-{i:02d}" for i in range(1, 23)])
m2_orig = finish(M2, [f"pt1-m2-{i:02d}" for i in range(1, 23)])
bk = finish(BANK, [f"m-{i:03d}" for i in range(134, 154)])

# the original Module 2's easy items move to the bank unchanged except for their ids
easy_items = [it for it in m2_orig if it["difficulty"] == "easy"]
assert len(easy_items) == 4
moved = finish([dict(it) for it in easy_items], [f"m-{i:03d}" for i in range(194, 198)])

# harder Module 2: the rest of the original, plus the replacements, in easy-to-hard order
old = [it for it in m2_orig if it["difficulty"] != "easy"]          # 9 medium then 9 hard, as ordered above
med, hard = old[:9], old[9:]
assert all(it["difficulty"] == "medium" for it in med) and all(it["difficulty"] == "hard" for it in hard)
# medium band: m1 A, ratio P, m2 A, m4 D, le2v A, m6 P, m9 A, m5 D, m3 A, m7 G, m8 A
by = lambda lst, skill: next(it for it in lst if it["skill"] == skill and it not in used)
used = []
def take(lst, skill):
    it = by(lst, skill); used.append(it); return it
med_order = [take(med, "Linear equations in one variable"), HARD_NEW["ratio"], take(med, "Linear functions"),
             take(med, "Nonlinear equations in one variable"), HARD_NEW["le2v"], take(med, "Two-variable data: models and scatterplots"),
             take(med, "Linear equations in two variables"), take(med, "Nonlinear functions"), take(med, "Systems of two linear equations"),
             take(med, "Lines, angles, and triangles"), take(med, "Linear inequalities")]
hard_order = [take(hard, "Linear functions"), take(hard, "Equivalent expressions"), take(hard, "Probability and conditional probability"),
              HARD_NEW["trig"], take(hard, "Nonlinear equations in one variable"), take(hard, "Systems of two linear equations"),
              HARD_NEW["equiv"], take(hard, "Right triangles and trigonometry"), take(hard, "Nonlinear functions"),
              take(hard, "One-variable data: distributions and measures of center and spread"), take(hard, "Systems of equations in two variables")]
M2H = med_order + hard_order
assert len(M2H) == 22 and len(used) == 18
for it in M2H: it.pop("id", None)
m2hpos = place_text_keys(M2H)
m2 = finish(M2H, [f"pt1-m2-{i:02d}" for i in range(1, 23)])

m2epos = place_text_keys(M2E)
m2e = finish(M2E, [f"pt1-m2e-{i:02d}" for i in range(1, 23)])

validate(m1, 22, {"easy": 7, "medium": 9, "hard": 6}, (5, 6), module=True)
validate(m2, 22, {"medium": 11, "hard": 11}, (5, 6), module=True)
validate(m2e, 22, {"easy": 9, "medium": 10, "hard": 3}, (5, 6), module=True)
validate(bk, 20)
assert [{k: v for k, v in a.items() if k != "id"} for a in moved] == [{k: v for k, v in b.items() if k != "id"} for b in easy_items]
for it in moved:
    assert it["skill"] in SKILLS[it["domain"]] and it["difficulty"] == "easy"
for mod in (m1 + m2, m1 + m2e):
    assert {it["skill"] for it in mod if it["domain"] == ALG} == set(SKILLS[ALG])
# every skill of a replaced easy item is kept in the harder module by its replacement
assert sorted(it["skill"] for it in moved) == sorted(HARD_NEW[k]["skill"] for k in HARD_NEW)
assert all(HARD_NEW[k]["difficulty"] in ("medium", "hard") for k in HARD_NEW)
assert not {it["id"] for it in moved} & {q["id"] for q in BANK_Q}

# no duplicates across all drafts and the bank: same stem, or same displayed equation line
MINE = {"pt1-m1.json", "pt1-m2.json", "pt1-m2e.json", "bank-m-1.json", "bank-m-pt1-moved.json"}
others = [q for q in BANK_Q if q.get("section") == "math" and q["id"] not in {it["id"] for it in bk}]
for fn_ in sorted(os.listdir(OUTDIR)):
    if fn_.endswith(".json") and fn_ not in MINE:
        d = json.load(open(os.path.join(OUTDIR, fn_)))
        others += [q for q in (d if isinstance(d, list) else d.get("questions", [])) if q.get("section") == "math"]
EQ = re.compile(r"[\s0-9a-z+\-−*/().²³√^=<>≤≥]+")
eqlines = lambda q: {l.strip() for l in q["stem"].split("\n") if "=" in l and EQ.fullmatch(l)}
def dupes(items, pool):
    stems = {q["stem"]: q["id"] for q in pool}; lines = {}
    for q in pool:
        for l in eqlines(q): lines[l] = q["id"]
    return [(it["id"], stems.get(it["stem"]) or next(lines[l] for l in eqlines(it) if l in lines))
            for it in items if it["stem"] in stems or eqlines(it) & set(lines)]
new_items = m2 + m2e + moved
assert not dupes(new_items, others), dupes(new_items, others)
mine_all = m1 + m2 + m2e + bk + moved
assert len({it["stem"] for it in mine_all}) == len(mine_all)
for i, it in enumerate(mine_all):
    assert not dupes([it], mine_all[:i] + mine_all[i + 1:]), it["id"]
OLD_OVERLAP = dupes(m1 + bk, others)      # reported, not fixed: those two files are frozen

os.makedirs(OUTDIR, exist_ok=True)
for name, data in (("pt1-m1.json", m1), ("pt1-m2.json", m2), ("pt1-m2e.json", m2e),
                   ("bank-m-1.json", bk), ("bank-m-pt1-moved.json", moved)):
    with open(os.path.join(OUTDIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")

if __name__ == "__main__":
    for label, data in (("Module 1", m1), ("Module 2 (harder)", m2), ("Module 2 (easier)", m2e), ("Bank", bk), ("Moved to bank", moved)):
        print(label, len(data), "items |", dict(Counter(it["domain"] for it in data)), "|",
              dict(Counter(it["difficulty"] for it in data)), "| grid-ins:", sum(it.get("type") == "spr" for it in data),
              "| key slots:", dict(sorted(Counter(it["answer"] for it in data if it.get("type") != "spr").items())))
    if OLD_OVERLAP: print("equation/stem overlap in frozen files:", OLD_OVERLAP)
