"""Draft math items for ABLE Preps practice test 2 (two 22-item modules) and
20 extra bank items (m-154 to m-173).

Follows gen_math.py's conventions: College Board stems, the U+2212 minus sign
in displayed math, ²/³ superscripts, fractions as a/b, numeric options in
ascending order, distractors from distinct named errors.

Every key is computed from the item's parameters, then re-checked a second
way inside this script: each multiple-choice item carries a check that is run
against all four displayed options (exactly one must pass, and it must be the
key), and each grid-in answer is re-derived by substitution or brute force.
Usage: python3 tools/draft_math_pt2.py   (writes data/draft/pt2-m1.json,
pt2-m2.json and bank-m-2.json)
"""
import json, os, re
from fractions import Fraction as Fr
from itertools import product
from math import isqrt, sqrt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DRAFT = os.path.join(ROOT, "data", "draft")

ALG = "Algebra"; ADV = "Advanced Math"; PSDA = "Problem-Solving and Data Analysis"; GEO = "Geometry and Trigonometry"
A1, A2, A3, A4, A5 = ("Linear equations in one variable", "Linear functions", "Linear equations in two variables",
                      "Systems of two linear equations", "Linear inequalities")
V1, V2, V3, V4 = ("Equivalent expressions", "Nonlinear equations in one variable", "Nonlinear functions",
                  "Systems of equations in two variables")
P1, P2, P3, P4, P5, P6, P7 = ("Ratios, rates, proportional relationships, and units", "Percentages",
                              "One-variable data: distributions and measures of center and spread",
                              "Two-variable data: models and scatterplots", "Probability and conditional probability",
                              "Inference from sample statistics and margin of error", "Evaluating statistical claims")
G1, G2, G3, G4 = "Area and volume", "Lines, angles, and triangles", "Right triangles and trigonometry", "Circles"

# ---------------------------------------------------------------- helpers (copied from gen_math.py)
def fmt(n, dec=False):
    if isinstance(n, float): n = Fr(n).limit_denominator(1000)
    if isinstance(n, Fr):
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

# ---------------------------------------------------------------- independent evaluator for displayed math
def to_py(expr):
    e = expr.replace("−", "-").replace("²", "**2").replace("³", "**3").replace("√", "SQRT")
    e = re.sub(r"(\d)\s*\(", r"\1*(", e)
    e = re.sub(r"(\d)([a-z])", r"\1*\2", e)
    e = re.sub(r"\)\s*\(", ")*(", e)
    e = re.sub(r"\)([a-z])", r")*\1", e)
    e = re.sub(r"(?<![A-Z])([a-z])\(", r"\1*(", e)
    e = re.sub(r"([a-z])([a-z])", r"\1*\2", e)       # ab -> a*b (single-letter variables only)
    return e.replace("^", "**").replace("SQRT", "sqrt")

def ev(expr, **env):
    code = re.sub(r"\d+\.\d+", lambda m: f"Fr('{m.group()}')", to_py(expr))   # exact decimals
    return eval(code, {"sqrt": sqrt, "Fr": Fr, "__builtins__": {}}, {k: Fr(v) for k, v in env.items()})

def point(s):
    m = re.fullmatch(r"\((−?\d+), (−?\d+)\)", s)
    return Fr(m.group(1).replace("−", "-")), Fr(m.group(2).replace("−", "-"))

def holds(eq, **env):
    l, r = eq.split("=")
    return ev(l, **env) == ev(r, **env)

def ineq_holds(s, **env):
    for op, f in (("≥", lambda a, b: a >= b), ("≤", lambda a, b: a <= b), (">", lambda a, b: a > b), ("<", lambda a, b: a < b)):
        if op in s:
            l, r = s.split(op)
            return f(ev(l, **env), ev(r, **env))
    raise ValueError(s)

GRID = sorted({Fr(n, d) for n in range(-60, 61) for d in (1, 2, 3, 4, 5)})

# ---------------------------------------------------------------- item builders
MODULES = {}      # key -> list of items (in final order)
CONCEPTUAL = []   # MC items whose key rests on a written rationale rather than a computation

def _base(domain, skill, diff, stem, expl, passage):
    it = {"id": None, "section": "math", "domain": domain, "skill": skill, "difficulty": diff, "stem": stem}
    return it, expl, passage

def _finish(it, expl, passage):
    it["explanation"] = expl
    if passage: it["passage"] = passage
    return it

def mc_num(domain, skill, diff, stem, correct, distractors, check, expl, passage=None, dec=False, show=None):
    """Numeric options in ascending order. `check(value)` re-decides correctness independently."""
    it, expl, passage = _base(domain, skill, diff, stem, expl, passage)
    vals = [Fr(correct)] + [Fr(d) for d in distractors]
    assert len(vals) == 4 and len(set(vals)) == 4, (stem, vals)
    vals.sort()
    verdicts = [bool(check(v)) for v in vals]
    assert verdicts.count(True) == 1 and verdicts[vals.index(Fr(correct))], (stem, vals, verdicts)
    it["choices"] = [show(v) if show else neg(fmt(v, dec)) for v in vals]
    it["answer"] = vals.index(Fr(correct))
    return _finish(it, expl, passage)

def mc_txt(domain, skill, diff, stem, correct, distractors, check, expl, passage=None):
    """Non-numeric options; the key's slot is chosen later to balance positions.
    `check(choice)` re-decides correctness independently; None marks a conceptual item."""
    it, expl, passage = _base(domain, skill, diff, stem, expl, passage)
    opts = [correct] + list(distractors)
    assert len(opts) == 4 and len(set(opts)) == 4, opts
    if check is None:
        CONCEPTUAL.append(stem[:60])
    else:
        verdicts = [bool(check(o)) for o in opts]
        assert verdicts == [True, False, False, False], (stem, verdicts)
    it["_txt"] = (correct, list(distractors))
    return _finish(it, expl, passage)

def spr(domain, skill, diff, stem, answer, recheck, expl, passage=None, dec=False):
    """Grid-in. `recheck` is the answer found a second way (brute force or substitution)."""
    it, expl, passage = _base(domain, skill, diff, stem, expl, passage)
    a = Fr(answer)
    assert Fr(recheck) == a, (stem, answer, recheck)
    assert a > 0 and (a * 10000).denominator == 1, ("grid-in must be positive and terminate within 4 places", stem, a)
    assert len(fmt(a, dec)) <= 5, ("grid-in answers fit the 5-character entry", stem, a)
    it["type"] = "spr"
    it["answer"] = fmt(a, dec)
    return _finish(it, expl, passage)

def solve_lin(f):
    """Solutions of f(x) = 0 for a linear f given as a function: 'none', 'all', or the root."""
    c0, c1 = f(Fr(0)), f(Fr(1)) - f(Fr(0))
    assert f(Fr(7)) == c0 + 7 * c1  # really linear
    if c1 == 0: return "all" if c0 == 0 else "none"
    return -c0 / c1

# ================================================================ MODULE 1
M = []
# ---- easy
M.append(mc_num(ALG, A1, "easy", "7x − 9 = 5x + 13\n\nWhat is the solution to the given equation?", 11,
    [2,            # 2x = 13 − 9: subtracted 9 instead of adding it
     Fr(11, 6),    # 12x = 22: added 5x to the left instead of subtracting it
     22],          # 2x = 22, but did not divide by 2
    lambda v: holds("7x − 9 = 5x + 13", x=v),
    "Subtract 5x from both sides: 2x − 9 = 13. Add 9 to both sides: 2x = 22. Divide both sides by 2: x = 11."))

M.append(mc_txt(ADV, V1, "easy", "Which expression is equivalent to 3x(2x − 5) + 4x?", "6x² − 11x",
    ["6x² − 19x",   # added 4x as if it were −4x
     "5x² − 11x",   # 3x · 2x taken as 5x²
     "6x² − 11"],   # dropped the x from the linear term
    lambda c: all(ev(c, x=t) == ev("3x(2x − 5) + 4x", x=t) for t in (-3, 1, 2, 5)),
    "Distribute 3x: 3x(2x) − 3x(5) = 6x² − 15x. Then add 4x: 6x² − 15x + 4x = 6x² − 11x."))

M.append(spr(ALG, A2, "easy", "Rolling Hills Bike Shop charges a flat fee of $12 plus $4.50 per hour to rent a bike. The function C(h) = 4.5h + 12 gives the total cost, in dollars, to rent a bike for h hours. What is the total cost, in dollars, to rent a bike for 6 hours?",
    Fr(9, 2) * 6 + 12, sum([12] + [Fr(9, 2)] * 6),
    "Substitute h = 6: C(6) = 4.5(6) + 12 = 27 + 12 = 39 dollars."))

M.append(mc_num(PSDA, P1, "easy", "A bike shop assembles 3 bikes every 4 hours. At this rate, how many hours will it take the shop to assemble 27 bikes?", Fr(27, 3) * 4,
    [9,            # 27 ÷ 3: counted groups of bikes, not hours
     Fr(27 * 3, 4),  # 27 × 3/4: used bikes per hour as hours per bike
     27 * 4],      # 27 × 4: treated 4 hours as the time for one bike
    lambda v: v * Fr(3, 4) == 27,
    "27 bikes is 27 ÷ 3 = 9 groups of 3 bikes. Each group takes 4 hours, so the shop needs 9 × 4 = 36 hours.", dec=True))

M.append(mc_txt(ALG, A4, "easy", "x = 3y\nx + y = 24\n\nWhat is the solution (x, y) to the given system of equations?", "(18, 6)",
    ["(6, 18)",    # x and y reversed
     "(12, 4)",    # satisfies only x = 3y
     "(20, 4)"],   # satisfies only x + y = 24
    lambda c: holds("x = 3y", x=point(c)[0], y=point(c)[1]) and holds("x + y = 24", x=point(c)[0], y=point(c)[1]),
    "Substitute 3y for x in the second equation: 3y + y = 24, so 4y = 24 and y = 6. Then x = 3(6) = 18, and the solution is (18, 6)."))

M.append(mc_num(ADV, V3, "easy", "The function f is defined by f(x) = 2x² − 3x + 1. What is the value of f(−2)?", 2 * 4 + 6 + 1,
    [3,     # −3(−2) taken as −6: 8 − 6 + 1
     -1,    # (−2)² taken as −4: −8 + 6 + 1
     23],   # 2(−2)² taken as (2 · −2)² = 16: 16 + 6 + 1
    lambda v: v == ev("2x² − 3x + 1", x=-2),
    "f(−2) = 2(−2)² − 3(−2) + 1 = 2(4) + 6 + 1 = 15."))

M.append(mc_num(GEO, G2, "easy", "Two lines intersect at a point. Two of the angles formed are vertical angles with measures (3x + 10)° and (5x − 30)°. What is the value of x?", 20,
    [10,    # 2x = 30 − 10: sign slip when collecting constants
     25,    # treated the angles as supplementary: 8x − 20 = 180
     70],   # the angle measure, not x
    lambda v: holds("3x + 10 = 5x − 30", x=v),
    "Vertical angles are congruent, so 3x + 10 = 5x − 30. Then 40 = 2x, and x = 20. (Each angle measures 3(20) + 10 = 70°.)"))

# ---- medium
M.append(mc_num(ALG, A3, "medium", "At a science fair, tickets cost $5 for adults and $3 for students. The equation 5a + 3s = 420 represents a day on which the fair collected $420 from the sale of a adult tickets and s student tickets. If 60 student tickets were sold that day, how many adult tickets were sold?", Fr(420 - 3 * 60, 5),
    [84,    # 420 ÷ 5: ignored the student tickets
     72,    # (420 − 60) ÷ 5: subtracted 60 instead of 3 × 60
     80],   # (420 − 180) ÷ 3: divided by the student price
    lambda v: 5 * v + 3 * 60 == 420,
    "Substitute s = 60: 5a + 3(60) = 420, so 5a + 180 = 420. Then 5a = 240, and a = 48."))

r1, r2 = Fr(3, 2), -4   # 2x² + 5x − 12 = (2x − 3)(x + 4)
M.append(spr(ADV, V2, "medium", "2x² + 5x − 12 = 0\n\nWhat is the positive solution to the given equation?",
    (-5 + isqrt(25 + 96)) / Fr(4), [v for v in GRID if v > 0 and holds("2x² + 5x − 12 = 0", x=v)][0],
    "Factor: (2x − 3)(x + 4) = 0, so x = 3/2 or x = −4. The positive solution is 3/2, or 1.5."))

M.append(spr(PSDA, P2, "medium", "A concert venue sold 750 tickets for its Friday show. The number of tickets sold for its Saturday show was 16% greater than the number sold for the Friday show. How many tickets were sold for the Saturday show?",
    750 + Fr(16, 100) * 750, 750 * Fr(116, 100),
    "16% of 750 is 0.16 × 750 = 120, so the Saturday show sold 750 + 120 = 870 tickets. (Equivalently, 1.16 × 750 = 870.)"))

tbl = {3: 740, 8: 1040}
slope = Fr(tbl[8] - tbl[3], 8 - 3); icpt = tbl[3] - slope * 3
M.append(mc_txt(ALG, A2, "medium", "Dana deposits the same amount into her savings account at the end of every month and makes no withdrawals. The table shows the balance B(x), in dollars, in the account x months after she opened it. If B is a linear function, which equation defines B?",
    f"B(x) = {fmt(slope)}x + {fmt(icpt)}",
    [f"B(x) = {fmt(slope)}x + {tbl[3]}",                     # used the first balance as the intercept
     f"B(x) = {tbl[8] - tbl[3]}x − {(tbl[8] - tbl[3]) * 3 - tbl[3]}",  # change in balance not divided by the 5 months
     f"B(x) = {fmt(icpt)}x + {fmt(slope)}"],                 # slope and intercept swapped
    lambda c: all(ev(c.split("=")[1], x=k) == v for k, v in tbl.items()),
    "The slope is (1,040 − 740)/(8 − 3) = 300/5 = 60 dollars per month. Then 740 = 60(3) + b, so b = 740 − 180 = 560, and B(x) = 60x + 560.",
    passage="x    B(x)\n3    740\n8    1,040"))

M.append(mc_txt(ADV, V3, "medium", "The function R models the number of riders on a city bus route each weekday t years after 2020, where R(t) = 850(0.96)^t. Which of the following is the best interpretation of 0.96 in this context?",
    "Each year, the number of weekday riders is 4% less than it was the year before.",
    ["Each year, the number of weekday riders is 96% less than it was the year before.",
     "Each year, the number of weekday riders decreases by 4.",
     "Each year, the number of weekday riders decreases by 0.96."],
    None,
    "Each increase of 1 in t multiplies R by 0.96, so each year's number of riders is 96% of the previous year's. That is a decrease of 100% − 96% = 4% per year, not a decrease by a fixed number of riders."))

M.append(spr(GEO, G1, "medium", "A recycling bin is shaped like a right rectangular prism that is 4 feet long, 2.5 feet wide, and 3 feet tall. How many cubic feet of material are in the bin when it is filled to 80% of its volume?",
    4 * Fr(5, 2) * 3 * Fr(80, 100), Fr(4 * 25 * 3 * 8, 10 * 10),
    "The bin's volume is 4 × 2.5 × 3 = 30 cubic feet. 80% of 30 is 0.8 × 30 = 24 cubic feet."))

w = -(-(800 - 380) // 45)
M.append(spr(ALG, A5, "medium", "Members of a recycling drive have collected 380 pounds of paper so far. They plan to collect 45 pounds of paper each week from now on. What is the least number of whole weeks from now after which the total amount of paper collected will be at least 800 pounds?",
    w, min(n for n in range(100) if 380 + 45 * n >= 800),
    "The total after w weeks is 380 + 45w pounds. Solve 380 + 45w ≥ 800: 45w ≥ 420, so w ≥ 420/45 ≈ 9.33. The least whole number of weeks is 10. (After 9 weeks the total is 785 pounds; after 10 weeks it is 830 pounds.)"))

freq = {1: 2, 2: 4, 3: 7, 4: 5, 5: 2}
days = [k for k, n in freq.items() for _ in range(n)]
M.append(mc_num(PSDA, P3, "medium", "What is the mean number of bikes repaired per day over the 20 days?", Fr(sum(k * n for k, n in freq.items()), sum(freq.values())),
    [3,                   # mean of the values 1 through 5, ignoring frequencies
     4,                   # mean of the frequencies, 20 ÷ 5
     Fr(61, 5)],          # correct total divided by the 5 rows instead of 20 days
    lambda v: v == Fr(sum(days), len(days)),
    "The total number of bikes repaired is 1(2) + 2(4) + 3(7) + 4(5) + 5(2) = 2 + 8 + 21 + 20 + 10 = 61. Dividing by the 20 days gives 61/20 = 3.05.",
    passage="Bikes repaired    Number of days\n1                 2\n2                 4\n3                 7\n4                 5\n5                 2\n\nThe table summarizes the number of bikes a bike shop repaired each day over 20 days.", dec=True))
assert len(days) == 20

sols = [(x, y) for x in GRID for y in GRID if holds("y = x² − 6x + 11", x=x, y=y) and holds("y = 2x − 5", x=x, y=y)]
assert sols == [(4, 3)]
M.append(spr(ADV, V4, "medium", "y = x² − 6x + 11\ny = 2x − 5\n\nThe given system of equations has exactly one solution (x, y). What is the value of y?",
    2 * 4 - 5, sols[0][1],
    "Set the two expressions for y equal: x² − 6x + 11 = 2x − 5, so x² − 8x + 16 = 0, or (x − 4)² = 0. Thus x = 4, and y = 2(4) − 5 = 3."))

# ---- hard
def n_solutions_h(a):  # 4(3x − 5) = 2(ax + 7)
    return solve_lin(lambda x: 4 * (3 * x - 5) - 2 * (a * x + 7))
M.append(mc_num(ALG, A1, "hard", "4(3x − 5) = 2(ax + 7)\n\nIn the given equation, a is a constant. If the equation has no solution, what is the value of a?", Fr(12, 2),
    [-6,    # sign error when matching coefficients
     12,    # matched 12x with ax, forgetting the factor of 2 on the right
     24],   # multiplied by 2 instead of dividing
    lambda v: n_solutions_h(v) == "none",
    "Distribute: 12x − 20 = 2ax + 14. Collect terms: (12 − 2a)x = 34. If 12 − 2a ≠ 0, then x = 34/(12 − 2a) is a solution. If 12 − 2a = 0, the equation becomes 0 = 34, which is false for every x. So the equation has no solution when 2a = 12, that is, when a = 6."))

M.append(mc_num(ADV, V2, "hard", "3x² + bx + 12 = 0\n\nIn the given equation, b is a positive constant. If the equation has exactly one real solution, what is the value of b?", isqrt(4 * 3 * 12),
    [6,     # √(3 · 12): left out the 4 in 4ac
     36,    # 3 × 12: used ac as the answer
     144],  # b² = 144, but did not take the square root
    lambda v: v > 0 and len({x for x in GRID if holds("3x² + bx + 12 = 0", x=x, b=v)}) == 1 and v * v - 4 * 3 * 12 == 0,
    "A quadratic equation has exactly one real solution when its discriminant is 0: b² − 4(3)(12) = 0, so b² = 144. Since b is positive, b = 12."))

bus = {"Route A": (84, 16), "Route B": (66, 24), "Route C": (90, 20)}
late = sum(l for _, l in bus.values())
M.append(mc_num(PSDA, P5, "hard", "If one of the late trips is selected at random, what is the probability that it was a trip on Route B?", Fr(bus["Route B"][1], late),
    [Fr(24, 90),     # P(late | Route B) instead of P(Route B | late)
     Fr(24, 300),    # divided by all 300 trips
     Fr(60, 300)],   # P(late) overall
    lambda v: v == Fr(sum(1 for r, (o, l) in bus.items() for _ in range(l) if r == "Route B"), sum(l for _, (o, l) in bus.items())),
    "Only the late trips matter. There were 16 + 24 + 20 = 60 late trips, and 24 of them were on Route B. So the probability is 24/60 = 2/5.",
    passage="           On time    Late\nRoute A    84         16\nRoute B    66         24\nRoute C    90         20\n\nThe table shows the numbers of on-time and late trips for three bus routes during one month."))

def no_solution_g(k):  # 3x − 5y = 8 and kx + 10y = 11
    if 3 * 10 - (-5) * k != 0: return False      # lines not parallel: exactly one solution
    ratio = Fr(10, -5)                              # second row = ratio × first row on the left side
    assert k == ratio * 3
    return 11 != ratio * 8                          # parallel and distinct
M.append(mc_num(ALG, A4, "hard", "The system of equations 3x − 5y = 8 and kx + 10y = 11, where k is a constant, has no solution. What is the value of k?", Fr(-10 * 3, 5),
    [Fr(-3, 2),   # set k/3 equal to −5/10 (ratio inverted)
     3,           # matched the x-coefficients
     6],          # sign error in −10 × 3/5
    no_solution_g,
    "A system of two linear equations has no solution when its lines are parallel and distinct. The first line is y = (3/5)x − 8/5 and the second is y = −(k/10)x + 11/10. Parallel lines need −k/10 = 3/5, so k = −6. With k = −6 the y-intercepts, −8/5 and 11/10, differ, so the lines never meet."))

a_p = [a for a in GRID if ev("a(x − 3)² + 5", a=a, x=1) == 13]
assert a_p == [2]
M.append(mc_num(ADV, V3, "hard", "g(x) = a(x − 3)² + 5\n\nThe function g is defined by the given equation, where a is a constant. If g(1) = 13, what is the value of g(6)?", 2 * 9 + 5,
    [-13,   # (1 − 3)² taken as −4, so a = −2
     11,    # forgot to square (6 − 3): 2(3) + 5
     18],   # forgot to add 5
    lambda v: v == ev("a(x − 3)² + 5", a=a_p[0], x=6),
    "g(1) = a(1 − 3)² + 5 = 4a + 5. Since g(1) = 13, 4a = 8 and a = 2. Then g(6) = 2(6 − 3)² + 5 = 2(9) + 5 = 23."))

r_sq = 15 + 3 ** 2 + 5 ** 2
assert all(holds("x² + y² + 6x − 10y = 15", x=-3 + dx, y=5 + dy) for dx, dy in ((7, 0), (0, 7), (-7, 0), (0, -7)))
M.append(mc_txt(GEO, G4, "hard", "x² + y² + 6x − 10y = 15\n\nIn the xy-plane, the graph of the given equation is a circle. What is the area of the circle?", f"{r_sq}π",
    ["15π",   # took the constant 15 as r²
     "34π",   # completed the square but did not add the 15
     "14π"],  # computed the circumference 2πr instead of the area
    lambda c: Fr(c[:-1]) == r_sq,
    "Complete the square: (x² + 6x + 9) + (y² − 10y + 25) = 15 + 9 + 25, so (x + 3)² + (y − 5)² = 49. The radius is 7, and the area is π(7)² = 49π."))
assert all(Fr(850) * Fr(96, 100) ** (t + 1) == Fr(96, 100) * (Fr(850) * Fr(96, 100) ** t) for t in range(5))  # 0.96 = 1 − 4%
MODULES["pt2-m1"] = M

# ================================================================ MODULE 2
M = []
# ---- easy
M.append(mc_txt(ALG, A3, "easy", "4x − 3y = 24\n\nWhat is the x-intercept of the graph of the given equation in the xy-plane?", "(6, 0)",
    ["(0, −8)",   # the y-intercept
     "(−6, 0)",   # sign error
     "(24, 0)"],  # did not divide by 4
    lambda c: point(c)[1] == 0 and holds("4x − 3y = 24", x=point(c)[0], y=point(c)[1]),
    "The x-intercept is the point where y = 0: 4x − 3(0) = 24, so x = 6. The x-intercept is (6, 0)."))

M.append(mc_num(ADV, V2, "easy", "3x² = 75\n\nWhat is the positive solution to the given equation?", isqrt(75 // 3),
    [15,    # multiplied 75 by 3, then took the square root
     25,    # x² = 25, but did not take the square root
     225],  # multiplied 75 by 3
    lambda v: v > 0 and holds("3x² = 75", x=v),
    "Divide both sides by 3: x² = 25. The solutions are 5 and −5, so the positive solution is 5."))

M.append(mc_num(PSDA, P2, "easy", "A school's recycling drive set a goal of collecting 1,000 pounds of paper. The drive collected 1,250 pounds. The amount collected was what percent of the goal?", Fr(1250, 1000) * 100,
    [25,    # the percent by which the goal was exceeded
     80,    # the goal as a percent of the amount collected
     250],  # the difference in pounds
    lambda v: v / 100 * 1000 == 1250,
    "Divide the amount collected by the goal: 1,250/1,000 = 1.25, which is 125% of the goal."))

M.append(mc_txt(ALG, A5, "easy", "Lena is saving to buy a bike that costs $540. She has already saved $180 and plans to save $40 each week. Which inequality represents all numbers of weeks, w, after which Lena will have saved at least enough money to buy the bike?",
    "180 + 40w ≥ 540",
    ["180 + 40w ≤ 540",   # inequality reversed
     "40 + 180w ≥ 540",   # savings amount and weekly rate swapped
     "40w ≥ 540 + 180"],  # added the amount already saved to the price
    lambda c: all(ineq_holds(c, w=n) == (180 + 40 * n >= 540) for n in range(0, 30)),
    "After w weeks Lena has 180 + 40w dollars. Having at least enough for the $540 bike means 180 + 40w ≥ 540."))

# ---- medium
M.append(spr(ALG, A1, "medium", "(x + 4)/3 = (2x − 1)/5\n\nWhat is the solution to the given equation?",
    Fr(-3 - 20, 5 - 6), [v for v in GRID if holds("(x + 4)/3 = (2x − 1)/5", x=v)][0],
    "Multiply both sides by 15: 5(x + 4) = 3(2x − 1), so 5x + 20 = 6x − 3. Subtract 5x from both sides and add 3 to both sides: x = 23."))

M.append(mc_txt(ADV, V1, "medium", "Which expression is equivalent to (3x − 2)² − (3x − 2)(x + 4)?", "(3x − 2)(2x − 6)",
    ["(3x − 2)(2x + 2)",   # subtracted x but added 4: −(x + 4) taken as −x + 4
     "(3x − 2)(4x + 2)",   # added (x + 4) instead of subtracting it
     "2x − 6"],            # divided out (3x − 2) instead of factoring it out
    lambda c: all(ev(c, x=t) == ev("(3x − 2)² − (3x − 2)(x + 4)", x=t) for t in (-2, 0, 1, 3, 7)),
    "Factor out the common factor (3x − 2): (3x − 2)[(3x − 2) − (x + 4)] = (3x − 2)(3x − 2 − x − 4) = (3x − 2)(2x − 6)."))

hyp, rise = 13, 5
run = isqrt(hyp * hyp - rise * rise)
M.append(mc_num(GEO, G3, "medium", "A ramp at a bike park is 13 feet long and rises from the ground to the top of a platform 5 feet high. The ramp, the ground, and the vertical side of the platform form a right triangle, with the ramp as the hypotenuse. What is the tangent of the angle the ramp makes with the ground?", Fr(rise, run),
    [Fr(5, 13),    # opposite/hypotenuse (the sine)
     Fr(12, 13),   # adjacent/hypotenuse (the cosine)
     Fr(12, 5)],   # adjacent/opposite (reciprocal)
    lambda v: run * run + rise * rise == hyp * hyp and v == Fr(rise, run),
    "The horizontal leg is √(13² − 5²) = √144 = 12 feet. For the angle at the ground, the opposite side is the 5-foot rise and the adjacent side is the 12-foot horizontal leg, so the tangent of the angle is 5/12."))

concert = [(f, b) for f in range(421) for b in range(421) if f + b == 420 and 30 * f + 18 * b == 9360]
assert concert == [(150, 270)]
M.append(mc_num(ALG, A4, "medium", "A concert hall sold 420 tickets for one performance. Floor tickets cost $30 each and balcony tickets cost $18 each, and ticket sales totaled $9,360. How many balcony tickets were sold?", Fr(30 * 420 - 9360, 30 - 18),
    [150,   # the number of floor tickets
     210,   # split the tickets evenly
     312],  # 9,360 ÷ 30: as if every ticket were a floor ticket
    lambda v: v == concert[0][1],
    "Let f be the number of floor tickets and b the number of balcony tickets: f + b = 420 and 30f + 18b = 9,360. Substituting f = 420 − b gives 30(420 − b) + 18b = 9,360, so 12,600 − 12b = 9,360. Then 12b = 3,240 and b = 270."))

fit = lambda x: Fr(18, 10) * x + Fr(45, 10)
M.append(mc_num(PSDA, P4, "medium", "For a science fair project, a student grew bean plants under different amounts of light. A scatterplot of the data has a line of best fit given by y = 1.8x + 4.5, where x is the number of hours of light per day and y is the plant's height, in centimeters, after 3 weeks. According to the line of best fit, what is the predicted increase in height, in centimeters, for every 5 additional hours of light per day?", Fr(18, 10) * 5,
    [Fr(18, 10),    # the increase for 1 additional hour
     Fr(135, 10),   # 1.8(5) + 4.5: the predicted height at x = 5
     Fr(225, 10)],  # 4.5 × 5: multiplied the intercept
    lambda v: v == fit(11) - fit(6) == fit(5) - fit(0),
    "The slope, 1.8, is the predicted increase in height for each additional hour of light per day. For 5 additional hours, the predicted increase is 5 × 1.8 = 9 centimeters.", dec=True))

sys_l = ("y = x² − 2x − 3", "y = x + 7")
M.append(mc_txt(ADV, V4, "medium", f"{sys_l[0]}\n{sys_l[1]}\n\nWhich of the following is a solution (x, y) to the given system of equations?", "(−2, 5)",
    ["(2, 9)",     # sign error in the roots: x = 2
     "(5, −12)",   # sign error in y
     "(−5, 2)"],   # lies on the line only
    lambda c: all(holds(e, x=point(c)[0], y=point(c)[1]) for e in sys_l),
    "Set x² − 2x − 3 = x + 7, so x² − 3x − 10 = 0, which factors as (x − 5)(x + 2) = 0. The solutions have x = 5 or x = −2, giving (5, 12) and (−2, 5). Of the choices, only (−2, 5) is a solution."))

M.append(mc_num(ALG, A2, "medium", "A bus leaves the start of its route and travels at a constant speed toward the end of the route. The function d(t) = 42 − 0.7t gives the distance, in miles, between the bus and the end of the route t minutes after the bus leaves. How many minutes after leaving does the bus reach the end of the route?", Fr(42) / Fr(7, 10),
    [Fr(294, 10),  # 42 × 0.7: multiplied instead of dividing
     Fr(413, 10),  # d(1): the distance after 1 minute
     42],          # d(0): the length of the route
    lambda v: solve_lin(lambda t: 42 - Fr(7, 10) * t) == v,
    "The bus reaches the end of the route when d(t) = 0: 42 − 0.7t = 0, so 0.7t = 42 and t = 42/0.7 = 60 minutes.", dec=True))

bal = 2000 * Fr(105, 100) ** 2
M.append(spr(ADV, V3, "medium", "A savings account earns interest compounded annually, and no deposits or withdrawals are made after the first deposit. The balance, in dollars, t years after the first deposit is given by B(t) = 2000(1.05)^t. What is the balance, in dollars, after 2 years?",
    bal, 2000 + Fr(5, 100) * 2000 + Fr(5, 100) * (2000 + Fr(5, 100) * 2000),
    "B(2) = 2000(1.05)² = 2000(1.1025) = 2205 dollars. (Year by year: 2000 + 100 = 2100, then 2100 + 105 = 2205.)"))

pop, pct, moe = 4000, 36, 6
lo, hi = pop * Fr(pct - moe, 100), pop * Fr(pct + moe, 100)
M.append(mc_txt(PSDA, P6, "medium", "A bus system has 4,000 regular riders. In a survey of 250 of these riders selected at random, 36% said they would use a proposed express route. The margin of error for this estimate is 6 percentage points. Based on the survey, which of the following is the most plausible range for the number of all 4,000 regular riders who would use the express route?",
    f"Between {int(lo):,} and {int(hi):,}",
    [f"Between {int(250 * Fr(30, 100))} and {int(250 * Fr(42, 100))}",                 # applied the interval to the 250 surveyed riders
     f"Between {int(pop * Fr(36, 100)) - 6:,} and {int(pop * Fr(36, 100)) + 6:,}",       # treated the margin as 6 riders
     f"Exactly {int(pop * Fr(36, 100)):,}"],                                            # ignored the margin of error
    lambda c: [int(n.replace(",", "")) for n in re.findall(r"[\d,]+\d", c)] == [pop * pct // 100 - pop * moe // 100, pop * pct // 100 + pop * moe // 100],
    "The plausible range for the percentage of all riders is 36% ± 6%, or 30% to 42%. Applied to all 4,000 riders: 0.30 × 4,000 = 1,200 and 0.42 × 4,000 = 1,680."))

# ---- hard
sl = Fr(-5 - 7, 4 - (-2)); sp = -1 / sl
xint = 6 - 1 / sp
M.append(spr(ALG, A3, "hard", "In the xy-plane, line ℓ passes through the points (−2, 7) and (4, −5). Line p is perpendicular to line ℓ and passes through the point (6, 1). What is the x-coordinate of the x-intercept of line p?",
    xint, [x for x in GRID if sl * (0 - 1) == -(x - 6)][0],   # a point (x, 0) on p makes (x − 6, −1) perpendicular to ℓ's direction
    "The slope of line ℓ is (−5 − 7)/(4 − (−2)) = −12/6 = −2, so line p has slope 1/2. Through (6, 1): y − 1 = (1/2)(x − 6). Setting y = 0 gives −1 = (1/2)(x − 6), so x − 6 = −2 and x = 4."))

ab = [(a, b) for a in range(-20, 21) for b in range(-20, 21) if all(ev("(ax + 3)(2x − b)", a=a, b=b, x=t) == ev("6x² − 9x − 15", x=t) for t in (0, 1, 2))]
assert ab == [(3, 5)]
M.append(mc_num(ADV, V1, "hard", "(ax + 3)(2x − b) = 6x² − 9x − 15\n\nThe given equation is true for all values of x, where a and b are constants. What is the value of a + b?", Fr(6, 2) + Fr(15, 3),
    [-2,    # took b = −5 (sign error in −3b = −15)
     11,    # took a = 6, not dividing 6x² by 2x
     15],   # computed ab from the x-coefficient instead of a + b
    lambda v: v == sum(ab[0]),
    "Expanding the left side gives 2ax² + (6 − ab)x − 3b. Matching coefficients: 2a = 6, so a = 3, and −3b = −15, so b = 5. (Check: 6 − ab = 6 − 15 = −9, which matches.) So a + b = 3 + 5 = 8."))

def shoelace(*p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2
AD, DB, area_ade = 6, 9, 24
k_sim = Fr(AD + DB, AD)
# coordinates: A = (0, 0), B = (15, 0), C chosen so that area(ADE) = 24 with D on AB and E on AC at ratio 6/15
C = (Fr(4), Fr(2 * area_ade) / AD * k_sim)
A_, B_ = (Fr(0), Fr(0)), (Fr(AD + DB), Fr(0))
D_ = (Fr(AD), Fr(0)); E_ = (C[0] * Fr(AD, AD + DB), C[1] * Fr(AD, AD + DB))
assert shoelace(A_, D_, E_) == area_ade
M.append(mc_num(GEO, G2, "hard", "In triangle ABC, point D lies on side AB and point E lies on side AC so that segment DE is parallel to side BC. The length of AD is 6, the length of DB is 9, and the area of triangle ADE is 24. What is the area of quadrilateral DBCE?", area_ade * k_sim ** 2 - area_ade,
    [area_ade * k_sim - area_ade,          # scaled the area by 5/2 instead of (5/2)²
     area_ade * Fr(DB, AD) ** 2,           # used DB/AD as the scale factor
     area_ade * k_sim ** 2],               # area of triangle ABC, not the quadrilateral
    lambda v: v == shoelace(D_, B_, C, E_),
    "Because DE is parallel to BC, triangle ADE is similar to triangle ABC with scale factor AB/AD = (6 + 9)/6 = 5/2. Areas scale by the square of the scale factor, so the area of triangle ABC is 24 × (5/2)² = 24 × 25/4 = 150. The area of quadrilateral DBCE is 150 − 24 = 126."))

def infinitely_many(a, b):  # ax + 4y = 18 and 3x + 2y = b describe the same line
    return a * 2 - 4 * 3 == 0 and 4 * b - 2 * 18 == 0 and a * b - 3 * 18 == 0
sums = {a + b for a in GRID for b in GRID if infinitely_many(a, b)}
assert sums == {15}
M.append(mc_num(ALG, A4, "hard", "The system of equations ax + 4y = 18 and 3x + 2y = b, where a and b are constants, has infinitely many solutions (x, y). What is the value of a + b?", 2 * 3 + Fr(18, 2),
    [Fr(3, 2) + 9,   # scaled the x-coefficient the wrong way: a = 3/2
     6 + 18,         # scaled a but not the constant: b = 18
     6 + 36],        # scaled the constant the wrong way: b = 36
    lambda v: v in sums,
    "The system has infinitely many solutions only when the two equations describe the same line, so one equation must be a multiple of the other. Comparing the y-coefficients, 4 = 2 × 2, so the first equation is 2 times the second. Then a = 2 × 3 = 6 and 18 = 2b, so b = 9. Therefore a + b = 6 + 9 = 15.", dec=True))

cs = [c for c in range(-50, 51) if min(ev("x² − 6x + c", x=x, c=c) for x in GRID) == -4]
assert cs == [5]
M.append(mc_num(ADV, V3, "hard", "f(x) = x² − 6x + c\n\nThe function f is defined by the given equation, where c is a constant. The minimum value of f(x) is −4. What is the value of f(1)?", 1 - 6 + 5,
    [-18,   # c = −13 from a sign error: c = −4 − 9
     -9,    # took c = −4, the minimum value itself
     -4],   # the minimum value, not f(1)
    lambda v: v == ev("x² − 6x + c", x=1, c=cs[0]),
    "Complete the square: f(x) = (x² − 6x + 9) + (c − 9) = (x − 3)² + (c − 9). The minimum value is c − 9, so c − 9 = −4 and c = 5. Then f(1) = 1² − 6(1) + 5 = 0."))

n_all, mean_all, n_rest, mean_rest = 12, 45, 10, 42
pair = n_all * mean_all - n_rest * mean_rest
M.append(spr(PSDA, P3, "hard", "At a recycling drive, 12 volunteers collected a mean of 45 pounds of cans each. Two of the volunteers were Ari and Bea, and Bea collected twice as many pounds of cans as Ari. The mean amount collected by the other 10 volunteers was 42 pounds. How many pounds of cans did Bea collect?",
    Fr(pair, 3) * 2, [2 * a for a in range(200) if Fr(n_rest * mean_rest + a + 2 * a, n_all) == mean_all][0],
    "All 12 volunteers collected 12 × 45 = 540 pounds, and the other 10 collected 10 × 42 = 420 pounds, so Ari and Bea together collected 540 − 420 = 120 pounds. If Ari collected a pounds, then a + 2a = 120, so a = 40, and Bea collected 2(40) = 80 pounds."))

feasible = [(c, m) for c in range(0, 26) for m in range(0, 26) if c + m <= 25 and 80 * c + 120 * m >= 2400]
M.append(spr(ALG, A5, "hard", "A bike shop earns a profit of $80 on each city bike and $120 on each mountain bike it sells. This week the shop can sell at most 25 bikes in total, and it wants a total profit of at least $2,400 from these sales. What is the greatest number of city bikes the shop can sell this week and still meet both conditions?",
    Fr(120 * 25 - 2400, 120 - 80), max(c for c, m in feasible),
    "Let c be the number of city bikes and m the number of mountain bikes: c + m ≤ 25 and 80c + 120m ≥ 2,400. For a given c, profit is greatest when m is as large as possible, m = 25 − c. Then 80c + 120(25 − c) ≥ 2,400 gives 3,000 − 40c ≥ 2,400, so 40c ≤ 600 and c ≤ 15. Selling 15 city bikes and 10 mountain bikes earns exactly 1,200 + 1,200 = 2,400 dollars, so the greatest number is 15."))

eq_n = "(x + 1)/(x − 2) = 12/(x² − 4)"
roots_n = sorted(v for v in GRID if v not in (2, -2) and holds(eq_n, x=v))
assert roots_n == [-5]
M.append(mc_txt(ADV, V2, "hard", f"{eq_n}\n\nWhich of the following gives all the solutions to the given equation?", "−5 only",
    ["2 only",       # kept the extraneous root and dropped the real one
     "−5 and 2",     # did not reject x = 2, which makes a denominator 0
     "5 and −2"],    # sign error when factoring x² + 3x − 10
    lambda c: sorted(Fr(t.replace("−", "-")) for t in c.replace(" only", "").split(" and ")) == roots_n,
    "Since x² − 4 = (x − 2)(x + 2), multiply both sides by (x − 2)(x + 2), where x ≠ 2 and x ≠ −2: (x + 1)(x + 2) = 12. Then x² + 3x + 2 = 12, so x² + 3x − 10 = 0, or (x + 5)(x − 2) = 0. The value x = 2 makes a denominator 0, so it is not a solution. The only solution is x = −5."))

circ = "x² + y² − 4x + 2y = 20"
ks = [k for k in GRID if k > 0 and holds(circ, x=5, y=k)]
M.append(spr(GEO, G4, "hard", f"{circ}\n\nIn the xy-plane, the graph of the given equation is a circle. The circle passes through the point (5, k), where k > 0. What is the value of k?",
    isqrt(25 - 9) - 1, ks[0],
    "Complete the square: (x − 2)² + (y + 1)² = 20 + 4 + 1 = 25. Substitute x = 5 and y = k: 9 + (k + 1)² = 25, so (k + 1)² = 16 and k + 1 = 4 or k + 1 = −4. Then k = 3 or k = −5. Since k > 0, k = 3."))
assert len(ks) == 1
MODULES["pt2-m2"] = M

# ================================================================ BANK EXTRAS (m-154 to m-173)
M = []
M.append(mc_txt(PSDA, P7, "easy", "A band posted a poll on its website asking visitors which song it should play to open its next concert. Of the 1,600 visitors who chose to respond, 62% picked the same song. The band says this shows that 62% of all the people who will attend the concert prefer that song. Which of the following best explains why this conclusion is not justified?",
    "The people who responded chose to take the poll on the band's website, so they may not be representative of all the people who will attend.",
    ["A sample of 1,600 people is too small to support any conclusion.",
     "The percentage should have been rounded to the nearest 10 percent.",
     "A poll cannot be used to learn about people's preferences."],
    None,
    "The respondents volunteered and were all visitors to the band's website, so they are not a random sample of concert attendees; people who answer such a poll may prefer different songs than other attendees. A sample of 1,600 is not too small, and rounding has nothing to do with whether the sample is representative."))

M.append(mc_txt(PSDA, P7, "medium", "The owner of a bike shop surveyed the first 50 customers who came into the shop on a Saturday. Of those surveyed, 70% said they ride a bike to work at least once a week. Which of the following is the most appropriate conclusion?",
    "The result should not be generalized to all adults in the town, because the sample was not selected at random from that population.",
    ["About 70% of all adults in the town ride a bike to work at least once a week.",
     "About 70% of all people who visit bike shops in the country ride a bike to work at least once a week.",
     "Riding a bike to work causes people to visit the bike shop."],
    None,
    "The first 50 customers of a bike shop are not a random sample of the town's adults; people who shop at a bike shop are more likely than others to ride bikes. So the 70% cannot be generalized to the town, and certainly not to the whole country. A survey with no random assignment also cannot show that one thing causes another."))

M.append(mc_txt(PSDA, P7, "hard", "For a science fair project, a student randomly selected 40 bean plants from the 300 bean plants in a school greenhouse. She then randomly assigned 20 of the selected plants to receive a new plant food and the other 20 to receive none. After four weeks, the plants that received the plant food had grown significantly more, on average. Which of the following is the most appropriate conclusion?",
    "The plant food is likely to cause increased growth for bean plants in the school greenhouse.",
    ["The plant food is likely to cause increased growth for all types of plants.",
     "There is an association between the plant food and growth, but the plant food cannot be said to cause the increase.",
     "The plant food is likely to cause increased growth only for the 20 plants that received it."],
    None,
    "Random assignment of the treatment supports a cause-and-effect conclusion, and random selection from the 300 greenhouse plants lets the result extend to that population. It does not extend to other kinds of plants, which were never sampled."))

hh, n_s, glass = 2400, 80, 15
M.append(spr(PSDA, P6, "medium", "A town has 2,400 households that take part in its curbside recycling program. A random sample of 80 of these households found that 15 of them recycled glass during a certain week. Based on the sample, what is the best estimate of the number of the 2,400 households that recycled glass that week?",
    Fr(glass, n_s) * hh, (hh // n_s) * glass,
    "In the sample, 15/80 = 0.1875 of the households recycled glass. Applying that proportion to all 2,400 households gives 0.1875 × 2,400 = 450 households."))

mean_s, moe_s = Fr(2340, 100), Fr(185, 100)
M.append(mc_num(PSDA, P6, "medium", "At a music festival, a random sample of 120 attendees was asked how much they spent on food. The sample mean was $23.40, with an estimated margin of error of $1.85. Which of the following is a plausible value for the mean amount spent on food by all attendees of the festival?", Fr(2490, 100),
    [mean_s - 2 * moe_s,   # 23.40 − 2(1.85): used twice the margin of error
     Fr(2140, 100),        # below 23.40 − 1.85 = 21.55
     mean_s + 2 * moe_s],  # 23.40 + 2(1.85): used twice the margin of error
    lambda v: mean_s - moe_s <= v <= mean_s + moe_s,
    "Plausible values for the population mean lie within the margin of error of the sample mean: from 23.40 − 1.85 = 21.55 to 23.40 + 1.85 = 25.25 dollars. Of the choices, only $24.90 is in this interval.",
    show=lambda v: f"${float(v):.2f}"))

i1 = (62 - Fr(43, 10), 62 + Fr(43, 10)); i2 = (58 - Fr(44, 10), 58 + Fr(44, 10))
assert i1[0] < i2[1] and i2[0] < i1[1]   # the plausible ranges overlap
M.append(mc_txt(PSDA, P6, "hard", "A city's bus system surveyed a random sample of 500 riders in 2024 and another random sample of 500 riders in 2025. In 2024, 62% of the sampled riders said they were satisfied with the service, with a margin of error of 4.3 percentage points. In 2025, 58% of the sampled riders said they were satisfied, with a margin of error of 4.4 percentage points. Which of the following is the most appropriate conclusion?",
    "The surveys do not provide convincing evidence that the percentage of all riders who were satisfied decreased from 2024 to 2025.",
    ["The percentage of all riders who were satisfied decreased by exactly 4 percentage points from 2024 to 2025.",
     "The percentage of all riders who were satisfied decreased from 2024 to 2025, because 58% is less than 62%.",
     "The 2025 survey is more reliable than the 2024 survey because its margin of error is larger."],
    None,
    "The plausible range for 2024 is 62% ± 4.3%, or 57.7% to 66.3%, and for 2025 it is 58% ± 4.4%, or 53.6% to 62.4%. These ranges overlap, so the true percentage could be the same in both years (for example, 60%). The surveys do not show a decrease, and a larger margin of error means less precision, not more."))

sys_7 = ("y = 2x² − 5x + 1", "y = x + 9")
s7 = [(x, y) for x in GRID for y in range(-100, 101) if all(holds(e, x=x, y=y) for e in sys_7)]
assert sorted(s7) == [(-1, 8), (4, 13)]
M.append(spr(ADV, V4, "medium", f"{sys_7[0]}\n{sys_7[1]}\n\nIf (x, y) is a solution to the given system of equations and x > 0, what is the value of y?",
    4 + 9, [y for x, y in s7 if x > 0][0],
    "Set 2x² − 5x + 1 = x + 9, so 2x² − 6x − 8 = 0, or x² − 3x − 4 = 0. This factors as (x − 4)(x + 1) = 0, so x = 4 or x = −1. Since x > 0, x = 4, and y = 4 + 9 = 13."))

def one_meet(b):   # y = x² + bx + 10 meets y = 2x + 1 exactly once
    return (b - 2) ** 2 - 4 * 9 == 0 and len([x for x in GRID if x * x + b * x + 10 == 2 * x + 1]) == 1
M.append(mc_num(ADV, V4, "hard", "In the xy-plane, the graph of y = x² + bx + 10, where b is a positive constant, intersects the graph of y = 2x + 1 at exactly one point. What is the value of b?", 2 + isqrt(36),
    [-4,    # the other root of (b − 2)² = 36, which is not positive
     6,     # ignored the 2x from the line: b² = 36
     38],   # (b − 2)² = 36, but did not take the square root
    lambda v: v > 0 and one_meet(v),
    "Setting x² + bx + 10 = 2x + 1 gives x² + (b − 2)x + 9 = 0. The graphs meet at exactly one point when this equation has exactly one real solution, which happens when its discriminant is 0: (b − 2)² − 4(1)(9) = 0. So (b − 2)² = 36, and b − 2 = 6 or b − 2 = −6, giving b = 8 or b = −4. Since b is positive, b = 8."))

sys_9 = ("y = 3x", "y = x² − 4")
M.append(mc_txt(ADV, V4, "easy", f"{sys_9[0]}\n{sys_9[1]}\n\nWhich of the following is a solution (x, y) to the given system of equations?", "(−1, −3)",
    ["(1, 3)",       # lies on y = 3x only
     "(2, 0)",       # lies on y = x² − 4 only
     "(−4, −12)"],   # lies on y = 3x only (sign error in the root 4)
    lambda c: all(holds(e, x=point(c)[0], y=point(c)[1]) for e in sys_9),
    "Substitute 3x for y in the second equation: 3x = x² − 4, so x² − 3x − 4 = 0, or (x − 4)(x + 1) = 0. The solutions are (4, 12) and (−1, −3); of the choices, only (−1, −3) is a solution. Each other choice lies on only one of the two graphs."))

M.append(mc_num(PSDA, P4, "easy", "A bike rental shop recorded the number of bikes rented and the high temperature, in degrees Fahrenheit, on each of 30 days. The line of best fit for the data is y = 2.4x − 96, where x is the high temperature and y is the number of bikes rented. Based on the line of best fit, how many bikes are predicted to be rented on a day when the high temperature is 75 degrees Fahrenheit?", Fr(24, 10) * 75 - 96,
    [Fr(24, 10) * (75 - 96),   # 2.4(75 − 96): subtracted 96 before multiplying
     Fr(24, 10) * 75,          # left out the −96
     Fr(24, 10) * 75 + 96],    # added 96 instead of subtracting it
    lambda v: v == ev("2.4x − 96", x=75),
    "Substitute x = 75: y = 2.4(75) − 96 = 180 − 96 = 84 bikes.", dec=True))

M.append(mc_txt(PSDA, P4, "medium", "A recycling center tracked the total amount of material, in tons, it had collected since the start of the year. A line of best fit for the data is y = 0.8x + 12.5, where x is the number of weeks since a new curbside program began and y is the total amount of material collected, in tons. Which of the following is the best interpretation of 12.5 in this context?",
    "The estimated total amount of material collected, in tons, when the curbside program began",
    ["The estimated increase in the total amount of material collected, in tons, each week",
     "The estimated number of weeks it takes to collect 1 ton of material",
     "The estimated total amount of material collected, in tons, 12.5 weeks after the curbside program began"],
    None,
    "12.5 is the value of y when x = 0, that is, the estimated total collected (in tons) at the moment the curbside program began. The weekly increase is the slope, 0.8."))

pred_x = [x for x in range(0, 101) if -Fr(4, 10) * x + 38 == Fr(285, 10) + Fr(15, 10)]
M.append(spr(PSDA, P4, "hard", "For data collected at the stops along a bus route, a line of best fit is y = −0.4x + 38, where x is the distance, in kilometers, of a stop from downtown and y is the average number of riders who board at that stop each hour. For one stop, the actual average number of riders is 28.5, and the residual for that stop (the actual value minus the value predicted by the line of best fit) is −1.5. How far, in kilometers, is this stop from downtown?",
    (38 - (Fr(285, 10) - Fr(-15, 10))) / Fr(4, 10), pred_x[0],
    "The residual is actual minus predicted, so 28.5 − predicted = −1.5, and the predicted value is 30. Then −0.4x + 38 = 30, so −0.4x = −8 and x = 20 kilometers."))

bin_ = {"aluminum cans": 24, "plastic bottles": 36, "glass jars": 20}
M.append(mc_num(PSDA, P5, "easy", "A bin at a recycling drive contains 24 aluminum cans, 36 plastic bottles, and 20 glass jars. If one item is selected at random from the bin, what is the probability that it is not a glass jar?", 1 - Fr(20, 80),
    [Fr(20, 80),   # probability that it is a glass jar
     Fr(24, 80),   # probability of an aluminum can only
     Fr(36, 80)],  # probability of a plastic bottle only
    lambda v: v == Fr(sum(n for k, n in bin_.items() if k != "glass jars"), sum(bin_.values())),
    "There are 24 + 36 + 20 = 80 items, and 80 − 20 = 60 of them are not glass jars. The probability is 60/80 = 3/4."))

seats = {("Floor", "u21"): 180, ("Floor", "21+"): 220, ("Balcony", "u21"): 120, ("Balcony", "21+"): 280}
M.append(mc_num(PSDA, P5, "medium", "If an attendee under 21 is selected at random, what is the probability that the attendee has a floor seat?", Fr(180, 180 + 120),
    [Fr(180, 800),   # divided by all 800 attendees
     Fr(180, 400),   # P(under 21 | floor) instead of P(floor | under 21)
     Fr(400, 800)],  # P(floor) for all attendees
    lambda v: v == Fr(seats[("Floor", "u21")], sum(n for (s, g), n in seats.items() if g == "u21")),
    "Restrict to attendees under 21: 180 + 120 = 300 people, of whom 180 have floor seats. The probability is 180/300 = 3/5.",
    passage="           Under 21    21 or older\nFloor      180         220\nBalcony    120         280\n\nThe table shows the numbers of attendees at a concert, by seating section and age group."))

sold, elec = 200, 80
bikes = [("e", i < elec * 25 // 100) for i in range(elec)] + [("o", i < (sold - elec) * 10 // 100) for i in range(sold - elec)]
M.append(spr(PSDA, P5, "hard", "Last month a bike shop sold 200 bikes, 80 of which were electric bikes. Of the electric bikes sold, 25% were sold with an extended warranty, and of the other bikes sold, 10% were sold with an extended warranty. If one of the bikes sold with an extended warranty is selected at random, what is the probability that it is an electric bike?",
    Fr(Fr(25, 100) * 80, Fr(25, 100) * 80 + Fr(10, 100) * 120), Fr(sum(1 for t, w in bikes if w and t == "e"), sum(1 for t, w in bikes if w)),
    "Electric bikes with a warranty: 25% of 80 = 20. Other bikes with a warranty: 10% of 120 = 12. So 20 + 12 = 32 bikes were sold with a warranty, and 20 of them are electric. The probability is 20/32 = 5/8, or 0.625."))

riders = [(a, s) for a in range(361) for s in range(361) if a + s == 360 and Fr(350, 100) * a + Fr(225, 100) * s == 1110]
assert riders == [(240, 120)]
M.append(mc_num(ALG, A4, "medium", "On one day, 360 riders paid fares on a bus route. Adults paid $3.50 each and students paid $2.25 each, and the route collected a total of $1,110 in fares. How many of the riders were students?", (Fr(350, 100) * 360 - 1110) / (Fr(350, 100) - Fr(225, 100)),
    [180,   # split the riders evenly
     240,   # the number of adults
     360],  # all the riders
    lambda v: v == riders[0][1],
    "Let a be the number of adults and s the number of students: a + s = 360 and 3.50a + 2.25s = 1,110. Substituting a = 360 − s: 3.50(360 − s) + 2.25s = 1,110, so 1,260 − 1.25s = 1,110. Then 1.25s = 150 and s = 120."))

sys_i = ("y ≥ 3x − 1", "y ≤ −x + 9")
M.append(mc_num(ALG, A5, "medium", f"{sys_i[0]}\n{sys_i[1]}\n\nThe point (2, k) is a solution to the given system of inequalities in the xy-plane. Which of the following could be the value of k?", 6,
    [4,     # satisfies only y ≤ −x + 9
     8,     # satisfies only y ≥ 3x − 1
     10],   # satisfies only y ≥ 3x − 1
    lambda v: all(ineq_holds(s, x=2, y=v) for s in sys_i),
    "Substitute x = 2 into each inequality. The first gives k ≥ 3(2) − 1 = 5, and the second gives k ≤ −2 + 9 = 7. So 5 ≤ k ≤ 7, and of the choices only 6 works."))

sl_f = Fr(3 - 11, 6 - 2)
M.append(spr(ALG, A2, "hard", "For the linear function f, f(2) = 11 and f(6) = 3. If f(a) = 0, what is the value of a?",
    2 - Fr(11) / sl_f, [a for a in GRID if solve_lin(lambda t: 11 + (t - 2) * sl_f) == a][0],
    "The slope is (3 − 11)/(6 − 2) = −8/4 = −2, so f(x) = 11 − 2(x − 2) = −2x + 15. Setting −2a + 15 = 0 gives a = 15/2, or 7.5."))

mph = 18
M.append(mc_num(PSDA, P1, "medium", "A cyclist rides at a constant speed of 18 miles per hour. What is the cyclist's speed, in feet per second? (1 mile = 5,280 feet)", Fr(mph * 5280, 3600),
    [Fr(mph, 60),           # miles per minute
     Fr(mph * 5280, 60),    # feet per minute
     mph * 5280],           # feet per hour
    lambda v: v * 3600 / 5280 == mph,
    "18 miles per hour is 18 × 5,280 = 95,040 feet per hour. There are 60 × 60 = 3,600 seconds in an hour, so the speed is 95,040/3,600 = 26.4 feet per second.", dec=True))

r_c, arc = 10, 6   # arc length 6π
M.append(mc_num(GEO, G4, "medium", "A circle has a radius of 10 centimeters. An arc of the circle has a length of 6π centimeters. What is the measure, in degrees, of the central angle that intercepts this arc?", Fr(arc, 2 * r_c) * 360,
    [Fr(arc, r_c * r_c) * 360,   # divided by the area, 100π, instead of the circumference
     Fr(arc, 4 * r_c) * 360,     # used 2π × diameter as the circumference
     Fr(arc, r_c) * 360],        # used πr as the circumference
    lambda v: v / 360 * 2 * r_c == arc,
    "The circumference is 2π(10) = 20π. The arc is 6π/20π = 3/10 of the circle, so the central angle is (3/10) × 360° = 108°.", dec=True))
MODULES["bank-m-2"] = M

# ================================================================ positions, ids, validation
META = json.load(open(os.path.join(ROOT, "data", "questions.json")))["meta"]["skills"]["math"]

def place(items):
    """Put each non-numeric key in the least-used slot so far (numeric keys are fixed by ascending order)."""
    used = [0, 0, 0, 0]
    for it in items:
        if "_txt" not in it and "choices" in it: used[it["answer"]] += 1
    for it in items:
        if "_txt" in it:
            correct, ds = it.pop("_txt")
            slot = min(range(4), key=lambda s: (used[s], s))
            it["choices"] = ds[:slot] + [correct] + ds[slot:]
            it["answer"] = slot; used[slot] += 1
    # order keys like the bank
    return [{k: it[k] for k in ("id", "section", "domain", "skill", "difficulty", "stem", "type", "choices", "answer", "explanation", "passage") if k in it} for it in items]

def normalize_spr(s):  # Python port of normalizeSpr in assets/js/practice.js
    t = re.sub(r"\s+", "", str(s))
    def num(x): r = round(float(x), 4); return str(int(r)) if r == int(r) else repr(r)
    if re.fullmatch(r"-?\d+(\.\d+)?/\d+(\.\d+)?", t):
        n, d = map(float, t.split("/")); return num(n / d) if d else t
    try: return num(float(t))
    except ValueError: return t.lower()

def validate(name, items, n, id_fmt, mix=None):
    assert len(items) == n, (name, len(items))
    ids = [it["id"] for it in items]
    assert ids == [id_fmt(i) for i in range(1, n + 1)], ids
    for it in items:
        assert it["section"] == "math" and it["skill"] in META[it["domain"]], it["id"]
        assert it["difficulty"] in ("easy", "medium", "hard")
        text = it["stem"] + " " + " ".join(it.get("choices", [])) + " " + it["explanation"]
        assert not re.search(r"(?<![A-Za-z0-9])-(?=[\s\d(a-z])|\d\s*-\s*\d", text), ("ASCII minus", it["id"])
        assert not re.search(r"\^2|\^3|figure|shown", text), it["id"]
        if it.get("type") == "spr":
            assert "choices" not in it and isinstance(it["answer"], str)
            v = Fr(it["answer"])
            forms = {fmt(v), f"{float(v):.4f}".rstrip("0").rstrip("."), f"{v.numerator * 2}/{v.denominator * 2}"}
            assert len({normalize_spr(f) for f in forms}) == 1, (it["id"], forms)
        else:
            ch = it["choices"]
            assert len(ch) == 4 and len(set(ch)) == 4 and 0 <= it["answer"] < 4, it["id"]
            nums = []
            for c in ch:
                try: nums.append(Fr(c.replace("−", "-").replace("$", "")))
                except ValueError: nums = None; break
            if nums: assert nums == sorted(nums), ("numeric choices not ascending", it["id"], ch)
    if mix:
        dom = {d: sum(it["domain"] == d for it in items) for d in (ALG, ADV, PSDA, GEO)}
        assert dom == {ALG: 8, ADV: 7, PSDA: 4, GEO: 3}, dom
        diff = [sum(it["difficulty"] == d for it in items) for d in ("easy", "medium", "hard")]
        assert diff == mix, diff
        order = {"easy": 0, "medium": 1, "hard": 2}
        assert [order[it["difficulty"]] for it in items] == sorted(order[it["difficulty"]] for it in items), "not easy→hard"
        assert 5 <= sum(it.get("type") == "spr" for it in items) <= 6
    pos = [0] * 4
    for it in items:
        if "choices" in it: pos[it["answer"]] += 1
    assert max(pos) - min(pos) <= 1, (name, pos)
    return pos

os.makedirs(DRAFT, exist_ok=True)
out = {}
for name, items in MODULES.items():
    for i, it in enumerate(items, 1):
        it["id"] = f"{name}-{i:02d}" if name.startswith("pt2") else f"m-{153 + i}"
    out[name] = place(items)
p1 = validate("pt2-m1", out["pt2-m1"], 22, lambda i: f"pt2-m1-{i:02d}", [7, 9, 6])
p2 = validate("pt2-m2", out["pt2-m2"], 22, lambda i: f"pt2-m2-{i:02d}", [4, 9, 9])
pb = validate("bank-m-2", out["bank-m-2"], 20, lambda i: f"m-{153 + i}")
alg_skills = {it["skill"] for k in ("pt2-m1", "pt2-m2") for it in out[k] if it["domain"] == ALG}
assert alg_skills == set(META[ALG]), alg_skills
stems = [it["stem"] for items in out.values() for it in items]
bank_stems = {q["stem"] for q in json.load(open(os.path.join(ROOT, "data", "questions.json")))["questions"]}
assert len(set(stems)) == len(stems) and not set(stems) & bank_stems

for name, items in out.items():
    with open(os.path.join(DRAFT, f"{name}.json"), "w") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
print("positions m1", p1, "m2", p2, "bank", pb)
print("conceptual (no computed check):", len(CONCEPTUAL))
