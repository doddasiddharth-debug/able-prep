"""Math question generator for the ABLE Preps bank, modeled on the Digital
SAT's published question style.

Conventions copied from College Board items:
  - stems use their standard phrasings ("What is the solution to the given
    equation?", "Which expression is equivalent to...", "In the xy-plane...")
  - numeric multiple-choice options are listed in ascending order
  - roughly a quarter of items are student-produced responses (grid-ins)
  - distractors come from distinct, named errors, so the four choices are
    spread out rather than clustered around the key

Every key is computed from the parameters, then re-solved independently by
audit_math.py before the bank ships.
"""
import json, random, sys
from fractions import Fraction
from math import isqrt

R = random.Random(2027)
OUT = []
_n = [1]

ALG = "Algebra"; ADV = "Advanced Math"; PSDA = "Problem-Solving and Data Analysis"; GEO = "Geometry and Trigonometry"

# ---------------------------------------------------------------- helpers
def fmt(n, dec=False):
    """Integers plain; other values as a/b, or as a decimal when dec=True
    and the decimal terminates (money, measurements, means)."""
    if isinstance(n, float): n = Fraction(n).limit_denominator(1000)
    if isinstance(n, Fraction):
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

def term(c, v="x", first=False):
    if c == 0: return ""
    mag = abs(c)
    body = (v if mag == 1 else f"{fmt(mag)}{v}") if v else fmt(mag)
    if first: return ("−" if c < 0 else "") + body
    return ("− " if c < 0 else "+ ") + body

def poly(*coefs, v="x"):
    deg = len(coefs) - 1
    parts = []
    for i, c in enumerate(coefs):
        p = deg - i
        if c == 0: continue
        var = "" if p == 0 else (v if p == 1 else f"{v}{'²' if p == 2 else '³'}")
        parts.append(term(c, var, first=not parts))
    return " ".join(parts) if parts else "0"

def lin(m, b, v="x"):
    return poly(m, b, v=v)

def num_choices(correct, distractors, dec=False):
    """Ascending numeric options; drops duplicates, tops up with spread values."""
    vals = [Fraction(correct)]
    for d in distractors:
        d = Fraction(d)
        if d not in vals: vals.append(d)
        if len(vals) == 4: break
    k = 2
    while len(vals) < 4:
        for cand in (Fraction(correct) * k if correct != 0 else Fraction(5 * k), Fraction(correct) + 7 * k):
            if cand not in vals and len(vals) < 4: vals.append(cand)
        k += 1
    vals.sort()
    return [neg(fmt(v, dec)) for v in vals], vals.index(Fraction(correct))

def mc(domain, skill, diff, stem, correct, distractors, expl, passage=None, numeric=True, dec=False):
    if numeric:
        choices, idx = num_choices(correct, distractors, dec)
    else:
        choices = [correct] + [d for d in distractors if d != correct][:3]
        assert len(choices) == 4, (stem, choices)
        R.shuffle(choices)
        idx = choices.index(correct)
    item = {"id": f"m-{_n[0]:03d}", "section": "math", "domain": domain, "skill": skill, "difficulty": diff,
            "stem": stem, "choices": choices, "answer": idx, "explanation": expl}
    if passage: item["passage"] = passage
    OUT.append(item); _n[0] += 1

def spr(domain, skill, diff, stem, answer, expl, passage=None, dec=False):
    item = {"id": f"m-{_n[0]:03d}", "section": "math", "domain": domain, "skill": skill, "difficulty": diff,
            "stem": stem, "type": "spr", "answer": answer if isinstance(answer, str) else fmt(Fraction(answer), dec), "explanation": expl}
    if passage: item["passage"] = passage
    OUT.append(item); _n[0] += 1

def pick(*xs): return R.choice(xs)

# ============================================================ ALGEBRA
S = "Linear equations in one variable"
for diff in ["easy", "easy", "medium"]:
    a = pick(3, 4, 5, 6, 7); x = R.randint(2, 9); b = R.randint(2, 20); c = a * x + b
    if diff == "easy":
        mc(ALG, S, diff, f"{a}x + {b} = {c}\n\nWhat is the solution to the given equation?", x,
           [x + b, c - b, Fraction(c + b, a)],
           f"Subtract {b} from both sides to get {a}x = {c - b}, then divide by {a}: x = {x}.")
    else:
        spr(ALG, S, diff, f"{a}x + {b} = {c}\n\nWhat is the value of x?", x,
            f"Subtract {b} from both sides: {a}x = {c - b}. Divide by {a}: x = {x}.")
for diff in ["medium", "medium"]:
    a = pick(2, 3, 4); k = R.randint(2, 7); c = pick(5, 6, 7, 8); x = R.randint(2, 9); d = a * (x + k) - c * x
    mc(ALG, S, diff, f"{a}(x + {k}) = {c}x{'' if d == 0 else (' + ' if d > 0 else ' − ') + str(abs(d))}\n\nWhat is the solution to the given equation?", x,
       [Fraction(a * k + d, c - a), a * k, -x],
       f"Distribute: {a}x + {a * k} = {c}x{'' if d == 0 else (' + ' if d > 0 else ' − ') + str(abs(d))}. Collect the x terms: {a * k - d} = {c - a}x, so x = {x}.")
a = pick(2, 3, 4); b = R.randint(2, 9)
mc(ALG, S, "hard", f"{a}(x + {b}) = {a}x + k\n\nIn the given equation, k is a constant. For what value of k does the equation have infinitely many solutions?", a * b,
   [b, a + b, -a * b], f"The left side is {a}x + {a * b}. The equation is true for every x only if k = {a * b}.")
a = pick(2, 3, 5); b = R.randint(1, 9)
mc(ALG, S, "hard", f"{a}x + {b} = {a}x + c\n\nIn the given equation, c is a constant. Which of the following must be true for the equation to have no solution?",
   f"c ≠ {b}", [f"c = {b}", "c = 0", f"c ≠ {a}"],
   f"Subtracting {a}x from both sides leaves {b} = c. That is false for every x unless c = {b}, so the equation has no solution exactly when c ≠ {b}.", numeric=False)
n = pick(12, 15, 18, 20); p = pick(3, 4, 5); fee = pick(10, 15, 20, 25); total = fee + n * p
mc(ALG, S, "easy", f"A community pool charges a ${fee} membership fee plus ${p} per visit. A member paid a total of ${total} for the membership and some visits. How many visits did the member make?", n,
   [Fraction(total, p), n + fee, total - fee], f"Visits cost {total} − {fee} = {total - fee} dollars in total; at ${p} each, that is {n} visits.")

S = "Linear functions"
m = pick(3, 4, 5, 6); b = pick(10, 15, 20, 25, 40); x0 = R.randint(3, 9)
mc(ALG, S, "easy", f"The function f is defined by f(x) = {m}x + {b}. What is the value of f({x0})?", m * x0 + b,
   [m + b + x0, m * x0, b * x0 + m], f"Substitute x = {x0}: f({x0}) = {m}({x0}) + {b} = {m * x0 + b}.")
m = pick(12, 15, 18, 20); b = pick(200, 250, 300, 350)
mc(ALG, S, "easy", f"A plumber charges a fixed fee of ${b} for a visit plus ${m} for each quarter hour of work. Which function C gives the total charge, in dollars, for a visit with q quarter hours of work?",
   f"C(q) = {m}q + {b}", [f"C(q) = {b}q + {m}", f"C(q) = {m + b}q", f"C(q) = {m}q − {b}"],
   f"The fixed fee {b} is the starting value, and each quarter hour adds {m}, so C(q) = {m}q + {b}.", numeric=False)
x1, x2 = 2, 7; m = pick(3, 4, 6, 8); b = pick(5, 9, 11, 14)
mc(ALG, S, "medium", f"x   f(x)\n{x1}   {m * x1 + b}\n{x2}   {m * x2 + b}\n\nThe table gives two values of the linear function f. Which equation defines f?",
   f"f(x) = {m}x + {b}", [f"f(x) = {m}x − {b}", f"f(x) = {b}x + {m}", f"f(x) = {m}x + {m * x1 + b}"],
   f"The slope is ({m * x2 + b} − {m * x1 + b})/({x2} − {x1}) = {m}. Then {m * x1 + b} = {m}({x1}) + b gives b = {b}.", numeric=False)
m = pick(-3, -2, 2, 3, 4); b = R.randint(-8, 8); x0 = R.randint(2, 6); y0 = m * x0 + b
mc(ALG, S, "medium", f"The graph of the linear function g passes through the points (0, {neg(b)}) and ({x0}, {neg(y0)}). What is the slope of the graph of g?", m,
   [-m, Fraction(1, m), b], f"Slope = change in y over change in x = ({neg(y0)} − ({neg(b)}))/({x0} − 0) = {neg(m)}.")
rate = pick(25, 30, 40, 45); start = pick(500, 600, 750, 900); t = pick(6, 8, 10, 12)
spr(ALG, S, "medium", f"A water tank holds {start} gallons. Water drains from the tank at a constant rate of {rate} gallons per minute. How many gallons of water remain in the tank after {t} minutes of draining?", start - rate * t,
    f"After {t} minutes, {rate} × {t} = {rate * t} gallons have drained, leaving {start} − {rate * t} = {start - rate * t} gallons.")
m = pick(2, 3, 5); b = pick(4, 7, 9)
mc(ALG, S, "hard", f"For the linear function h, h(1) = {m + b} and h(4) = {4 * m + b}. What is the value of h(10)?", 10 * m + b,
   [10 * m, 10 * (m + b), 4 * m + b + 6],
   f"The slope is ({4 * m + b} − {m + b})/(4 − 1) = {m}. Then h(x) = {m}x + {b}, so h(10) = {10 * m + b}.")
a = pick(2, 3, 4); k = pick(3, 5, 6)
mc(ALG, S, "hard", f"The function f is defined by f(x) = {a}x + c, where c is a constant. If f({k}) = {2 * a * k}, what is the value of c?", a * k,
   [2 * a * k, k, -a * k],
   f"f({k}) = {a}({k}) + c = {a * k} + c = {2 * a * k}, so c = {a * k}.")

S = "Linear equations in two variables"
m = pick(2, 3, 4, 5); b = pick(-6, -3, 3, 6, 8)
mc(ALG, S, "easy", f"Which equation represents the line in the xy-plane that has slope {m} and passes through the point (0, {neg(b)})?",
   f"y = {lin(m, b)}", [f"y = {lin(b, m)}", f"y = {lin(-m, b)}", f"y = {lin(m, -b)}"],
   f"In slope-intercept form y = mx + b, the slope is {m} and the y-intercept is {neg(b)}.", numeric=False)
A, B = pick(2, 3, 4), pick(3, 5, 6); x0 = R.randint(1, 6); y0 = R.randint(1, 6); C = A * x0 + B * y0
mc(ALG, S, "easy", f"{A}x + {B}y = {C}\n\nWhat is the y-intercept of the graph of the given equation in the xy-plane?",
   f"(0, {fmt(Fraction(C, B))})", [f"(0, {fmt(Fraction(C, A))})", f"(0, {C})", f"({fmt(Fraction(C, A))}, 0)"],
   f"Set x = 0: {B}y = {C}, so y = {fmt(Fraction(C, B))}. The y-intercept is (0, {fmt(Fraction(C, B))}).", numeric=False)
A, B = pick(2, 3, 4), pick(2, 3, 5, 6); x0 = R.randint(2, 5); y0 = R.randint(1, 5); C = A * x0 + B * y0
spr(ALG, S, "medium", f"{A}x + {B}y = {C}\n\nThe graph of the given equation in the xy-plane passes through the point ({x0}, k). What is the value of k?", y0,
    f"Substitute x = {x0}: {A * x0} + {B}k = {C}, so {B}k = {C - A * x0} and k = {y0}.")
m = pick(2, 3, 4); x1, y1 = R.randint(1, 5), R.randint(1, 9)
mc(ALG, S, "medium", f"A line in the xy-plane has slope {m} and passes through the point ({x1}, {y1}). Which of the following points also lies on the line?",
   f"({x1 + 3}, {y1 + 3 * m})", [f"({x1 + 3}, {y1 + 3})", f"({x1 + m}, {y1 + 1})", f"({x1 - 1}, {y1 + m})"],
   f"Moving 3 units right raises y by 3 × {m} = {3 * m}, giving ({x1 + 3}, {y1 + 3 * m}).", numeric=False)
A, B, C = pick(3, 4, 6), pick(2, 5, 8), pick(24, 30, 36, 40)
mc(ALG, S, "hard", f"{A}x − {B}y = {C}\n\nWhich of the following is the slope of the graph of the given equation in the xy-plane?", Fraction(A, B),
   [Fraction(-A, B), Fraction(B, A), -Fraction(B, A)],
   f"Solve for y: {B}y = {A}x − {C}, so y = ({A}/{B})x − {fmt(Fraction(C, B))}. The slope is {fmt(Fraction(A, B))}.")
m = pick(2, 3); b = pick(-4, -2, 5)
mc(ALG, S, "hard", f"Line k is perpendicular to the line y = {lin(m, b)} in the xy-plane and passes through the point ({m}, 0). Which equation defines line k?",
   f"y = −(1/{m})x + 1", [f"y = {m}x − {m * m}", f"y = (1/{m})x − 1", f"y = −{m}x + {m * m}"],
   f"A perpendicular line has slope −1/{m}. Through ({m}, 0): 0 = −(1/{m})({m}) + b gives b = 1.", numeric=False)
p1 = pick(4, 5, 6); p2 = pick(7, 8, 9); tot = pick(60, 72, 84)
mc(ALG, S, "medium", f"A student buys x notebooks at ${p1} each and y binders at ${p2} each and spends exactly ${tot}. Which equation represents this situation?",
   f"{p1}x + {p2}y = {tot}", [f"{p1}x + {p2}y + {tot} = 0", f"{p2}x + {p1}y = {tot}", f"({p1} + {p2})(x + y) = {tot}"],
   f"Notebooks cost {p1}x dollars and binders {p2}y dollars; their sum is the total, {tot}.", numeric=False)

S = "Systems of two linear equations"
x0, y0 = R.randint(1, 7), R.randint(1, 7)
mc(ALG, S, "easy", f"x + y = {x0 + y0}\nx − y = {neg(x0 - y0)}\n\nWhat is the solution (x, y) to the given system of equations?",
   f"({x0}, {y0})", [f"({y0}, {x0})", f"({x0 + y0}, {neg(x0 - y0)})", f"({x0}, {neg(-y0)})"],
   f"Add the equations: 2x = {2 * x0}, so x = {x0}. Then y = {x0 + y0} − {x0} = {y0}.", numeric=False)
a, b = pick(2, 3), pick(3, 4, 5); x0, y0 = R.randint(1, 6), R.randint(1, 6)
spr(ALG, S, "medium", f"{a}x + y = {a * x0 + y0}\n{b}x + y = {b * x0 + y0}\n\nIf (x, y) is the solution to the given system of equations, what is the value of x?", x0,
    f"Subtract the first equation from the second: {b - a}x = {b * x0 - a * x0}, so x = {x0}.")
x0, y0 = R.randint(2, 6), R.randint(1, 5)
spr(ALG, S, "medium", f"2x + 3y = {2 * x0 + 3 * y0}\n5x − 2y = {5 * x0 - 2 * y0}\n\nIf (x, y) is the solution to the given system of equations, what is the value of x + y?", x0 + y0,
    f"Solving the system gives x = {x0} and y = {y0}, so x + y = {x0 + y0}.")
m = pick(2, 3, 4); b = pick(4, 5, 7)
mc(ALG, S, "hard", f"y = {m}x + {b}\ny = {m}x + k\n\nIn the given system of equations, k is a constant. If the system has no solution, which of the following must be true?",
   f"k ≠ {b}", [f"k = {b}", f"k = {m}", "k = 0"],
   f"The lines have the same slope, {m}. They are parallel and never meet unless they are the same line, which happens only when k = {b}.", numeric=False)
a = pick(2, 3, 4); b = pick(3, 5); mult = pick(2, 3); c = a * mult
mc(ALG, S, "hard", f"{a}x + {b}y = 12\n{c}x + ky = {12 * mult}\n\nIn the given system of equations, k is a constant. For what value of k does the system have infinitely many solutions?", b * mult,
   [b, mult, a * mult],
   f"The second equation is {mult} times the first when k = {mult} × {b} = {b * mult}; then both equations describe the same line.")
adult, child = pick(8, 10, 12), pick(5, 6); na, nc = R.randint(20, 60), R.randint(20, 60)
mc(ALG, S, "medium", f"Tickets to a school play cost ${adult} for adults and ${child} for children. A total of {na + nc} tickets were sold for ${adult * na + child * nc}. How many adult tickets were sold?", na,
   [nc, na + nc, Fraction(adult * na + child * nc, adult) // 1], f"With a adult and c child tickets: a + c = {na + nc} and {adult}a + {child}c = {adult * na + child * nc}. Solving gives a = {na}.")

S = "Linear inequalities"
a = pick(2, 3, 4, 5); b = R.randint(1, 9); c = a * R.randint(3, 9) + b
mc(ALG, S, "easy", f"{a}x + {b} > {c}\n\nWhich of the following is the solution to the given inequality?",
   f"x > {(c - b) // a}", [f"x < {(c - b) // a}", f"x > {c - b}", f"x > {fmt(Fraction(c + b, a), True)}"],
   f"Subtract {b}: {a}x > {c - b}. Divide by {a}: x > {(c - b) // a}.", numeric=False)
a = pick(2, 3, 4); b = R.randint(2, 9); c = R.randint(1, 8)
mc(ALG, S, "medium", f"{b} − {a}x ≥ {c}\n\nWhich of the following is the solution to the given inequality?",
   f"x ≤ {neg(fmt(Fraction(b - c, a), True))}", [f"x ≥ {neg(fmt(Fraction(b - c, a), True))}", f"x ≤ {neg(fmt(Fraction(c - b, a), True))}", f"x ≥ {neg(fmt(Fraction(c - b, a), True))}"],
   f"Subtract {b}: −{a}x ≥ {neg(c - b)}. Dividing by −{a} reverses the inequality: x ≤ {neg(fmt(Fraction(b - c, a), True))}.", numeric=False)
budget = pick(120, 150, 200); price = pick(8, 12, 15); fixed = pick(20, 30, 45)
mc(ALG, S, "medium", f"A club has ${budget} to spend on a party. It must pay a ${fixed} room fee and ${price} per guest for food. Which inequality gives the possible numbers of guests, g, the club can afford?",
   f"{price}g + {fixed} ≤ {budget}", [f"{price}g + {fixed} ≥ {budget}", f"{fixed}g + {price} ≤ {budget}", f"{price}g ≤ {budget} + {fixed}"],
   f"Food for g guests costs {price}g, plus the {fixed} fee; the total cannot exceed {budget}.", numeric=False)
price = pick(8, 12, 15); fixed = pick(20, 30, 45); budget = pick(150, 200, 260)
spr(ALG, S, "medium", f"A club has ${budget} to spend on a party. It must pay a ${fixed} room fee and ${price} per guest for food. What is the maximum number of guests the club can afford?", (budget - fixed) // price,
    f"{price}g + {fixed} ≤ {budget} gives g ≤ {fmt(Fraction(budget - fixed, price))}, so at most {(budget - fixed) // price} guests.")
mc(ALG, S, "hard", "y ≤ 2x + 1\ny > −x + 4\n\nWhich of the following points (x, y) is a solution to the given system of inequalities in the xy-plane?",
   "(3, 5)", ["(0, 5)", "(1, 3)", "(2, 6)"],
   "Check (3, 5): 5 ≤ 7 is true and 5 > 1 is true. For (0, 5): 5 ≤ 1 is false. For (1, 3): 3 > 3 is false. For (2, 6): 6 ≤ 5 is false.", numeric=False)
lo = pick(3, 4, 5); hi = lo + pick(4, 5, 6)
mc(ALG, S, "hard", f"A shipping company accepts boxes whose length, in inches, is at least {lo * 4} and at most {hi * 4}. If the length of a box is 4 times its width w, in inches, which inequality gives all possible values of w?",
   f"{lo} ≤ w ≤ {hi}", [f"{lo * 4} ≤ w ≤ {hi * 4}", f"{lo * 16} ≤ w ≤ {hi * 16}", f"{lo} < w < {hi}"],
   f"The length is 4w, so {lo * 4} ≤ 4w ≤ {hi * 4}. Dividing by 4: {lo} ≤ w ≤ {hi}.", numeric=False)

# ============================================================ ADVANCED MATH
S = "Equivalent expressions"
a, b = pick(2, 3, 4), pick(1, 2, 3, 5)
mc(ADV, S, "easy", f"Which expression is equivalent to ({a}x + {b})²?",
   f"{a * a}x² + {2 * a * b}x + {b * b}", [f"{a * a}x² + {b * b}", f"{a * a}x² + {a * b}x + {b * b}", f"{2 * a}x² + {2 * a * b}x + {2 * b}"],
   f"({a}x + {b})² = ({a}x)² + 2({a}x)({b}) + {b}² = {a * a}x² + {2 * a * b}x + {b * b}.", numeric=False)
p, q = pick(2, 3, 4, 5), pick(6, 7, 9)
mc(ADV, S, "easy", f"Which expression is equivalent to x² + {p + q}x + {p * q}?",
   f"(x + {p})(x + {q})", [f"(x + {p * q})(x + 1)", f"(x − {p})(x − {q})", f"(x + {p + q})(x + {p * q})"],
   f"Two numbers that multiply to {p * q} and add to {p + q} are {p} and {q}, so the expression factors as (x + {p})(x + {q}).", numeric=False)
r, s = pick(2, 3, 4), pick(5, 6, 7)
mc(ADV, S, "medium", f"Which expression is equivalent to (x − {r})(x + {s}) − x²?",
   f"{s - r}x − {r * s}", [f"−{s - r}x − {r * s}", f"{s - r}x + {r * s}", f"{s + r}x − {r * s}"],
   f"Expand: x² + {s - r}x − {r * s} − x² = {s - r}x − {r * s}.", numeric=False)
k = pick(2, 3, 5)
mc(ADV, S, "medium", f"Which expression is equivalent to ({k}x³y²)² · x?",
   f"{k * k}x⁷y⁴", [f"{k * k}x⁶y⁴", f"{2 * k}x⁷y⁴", f"{k * k}x⁵y⁴"],
   f"Square each factor: {k}² = {k * k}, (x³)² = x⁶, (y²)² = y⁴. Multiplying by x gives x⁷: {k * k}x⁷y⁴.", numeric=False)
c = pick(4, 6, 8)
mc(ADV, S, "hard", f"Which expression is equivalent to (x² − {c * c})/(x + {c}) for x ≠ −{c}?",
   f"x − {c}", [f"x + {c}", f"x − {c * c}", f"x² − {c}"],
   f"x² − {c * c} = (x − {c})(x + {c}); dividing by x + {c} leaves x − {c}.", numeric=False)
n = pick(2, 3, 5)
mc(ADV, S, "hard", f"Which expression is equivalent to √({n * n * 2}x⁴) for x > 0?",
   f"{n}x²√2", [f"{n}x√2", f"{n * n}x²", f"{n}x⁴√2"],
   f"√({n * n} · 2 · x⁴) = {n} · x² · √2.", numeric=False)
h = pick(3, 4, 5); w = pick(2, 3)
mc(ADV, S, "medium", f"The expression {h}x² + {h * 2 * w}x + {h * w * w} can be written as {h}(x + k)², where k is a constant. What is the value of k?", w,
   [h, 2 * w, w * w], f"Factor out {h}: {h}(x² + {2 * w}x + {w * w}) = {h}(x + {w})². So k = {w}.")
a = pick(3, 5, 7)
spr(ADV, S, "hard", f"(x + {a})² − (x − {a})² = kx\n\nThe given equation is true for all values of x, where k is a constant. What is the value of k?", 4 * a,
    f"Expanding: (x² + {2 * a}x + {a * a}) − (x² − {2 * a}x + {a * a}) = {4 * a}x, so k = {4 * a}.")

S = "Nonlinear equations in one variable"
r1, r2 = pick(2, 3, 4, 5), pick(6, 7, 8, 9)
mc(ADV, S, "easy", f"x² − {r1 + r2}x + {r1 * r2} = 0\n\nWhat is the sum of the solutions to the given equation?", r1 + r2,
   [r1 * r2, -(r1 + r2), r2 - r1], f"The equation factors as (x − {r1})(x − {r2}) = 0, so the solutions are {r1} and {r2} and their sum is {r1 + r2}.")
r = pick(3, 4, 5, 6, 7)
spr(ADV, S, "easy", f"(x − {r})² = 0\n\nWhat is the solution to the given equation?", r, f"A square is 0 only when its base is 0: x − {r} = 0, so x = {r}.")
k = pick(5, 7, 11); m = pick(3, 4, 5, 6)
mc(ADV, S, "medium", f"√(x + {k}) = {m}\n\nWhat is the solution to the given equation?", m * m - k,
   [m - k, m * m + k, m * m], f"Square both sides: x + {k} = {m * m}, so x = {m * m - k}.")
a = pick(2, 3); r1 = pick(1, 2, 4); r2 = -pick(3, 5, 6); B = -a * (r1 + r2); C = a * r1 * r2
spr(ADV, S, "medium", f"{a}x² {'+' if B >= 0 else '−'} {abs(B)}x {'+' if C >= 0 else '−'} {abs(C)} = 0\n\nWhat is the positive solution to the given equation?", r1,
    f"The equation factors as {a}(x − {r1})(x + {-r2}) = 0, so the solutions are {r1} and {neg(r2)}; the positive one is {r1}.")
c = pick(4, 9, 16, 25)
mc(ADV, S, "medium", f"x² + k = 0\n\nIn the given equation, k is a constant. For which value of k does the equation have exactly two real solutions?",
   f"−{c}", [f"{c}", "0", f"√{c}"],
   f"x² = −k has two real solutions only when −k > 0, that is, when k < 0. Of the choices, only −{c} is negative.", numeric=False)
a = pick(1, 2); b = pick(4, 6, 8); disc0 = Fraction(b * b, 4 * a)
mc(ADV, S, "hard", f"{poly(a, b, 0)} + c = 0\n\nIn the given equation, c is a constant. For what value of c does the equation have exactly one real solution?", disc0,
   [b * b, -disc0, b], f"A quadratic has one real solution when its discriminant is 0: {b}² − 4({a})c = 0, so c = {b * b}/{4 * a} = {fmt(disc0)}.")
a = pick(2, 3, 4)
mc(ADV, S, "hard", f"{a}x/(x + 2) = {a}\n\nWhich of the following describes the solutions to the given equation?",
   "There are no solutions.", ["x = 0", "x = 2", "x = −2"],
   f"Multiplying both sides by x + 2 (with x ≠ −2) gives {a}x = {a}x + {2 * a}, which is never true. So the equation has no solution.", numeric=False)

S = "Nonlinear functions"
a, b = pick(1, 2), pick(2, 3, 4)
mc(ADV, S, "easy", f"The function f is defined by f(x) = {poly(a, 0, -b)}. What is the value of f(3)?", 9 * a - b,
   [3 * a - b, 9 * a + b, 6 * a - b], f"f(3) = {a}(3)² − {b} = {9 * a} − {b} = {9 * a - b}.")
p = pick(200, 500, 800)
mc(ADV, S, "easy", f"The function P models the population of a colony of bacteria t hours after an experiment begins, where P(t) = {p}(2)^t. Which of the following is the best interpretation of the number {p} in this context?",
   "The population at the start of the experiment", ["The number of hours it takes the population to double", "The population after 2 hours", "The amount the population increases each hour"],
   f"At t = 0, P(0) = {p} · 2⁰ = {p}, so {p} is the initial population.", numeric=False)
h, k = pick(2, 3, 4), pick(-5, -3, 4, 6)
mc(ADV, S, "medium", f"f(x) = (x − {h})² {'+' if k >= 0 else '−'} {abs(k)}\n\nThe function f is defined by the given equation. What is the minimum value of f(x)?", k,
   [h, -k, h * h + k], f"A square is at least 0, so f(x) ≥ {neg(k)}, with equality at x = {h}. The minimum value is {neg(k)}.")
h, k = pick(1, 2, 3), pick(2, 4, 5)
mc(ADV, S, "medium", f"In the xy-plane, the graph of y = x² − {2 * h}x + {h * h + k} has its vertex at the point (a, b). What is the value of b?", k,
   [h, h * h + k, -k], f"Complete the square: x² − {2 * h}x + {h * h + k} = (x − {h})² + {k}. The vertex is ({h}, {k}), so b = {k}.")
p0 = pick(1000, 2000, 5000); pct = pick(3, 4, 5, 6)
mc(ADV, S, "medium", f"A savings account earns {pct}% interest compounded annually. If the initial deposit is ${p0} and no other deposits or withdrawals are made, which function A gives the balance, in dollars, after t years?",
   f"A(t) = {p0}(1.0{pct})^t", [f"A(t) = {p0}({pct})^t", f"A(t) = {p0}(1 + 0.0{pct}t)", f"A(t) = {p0} + 1.0{pct}t"],
   f"Each year the balance is multiplied by 1 + {pct}/100 = 1.0{pct}, so A(t) = {p0}(1.0{pct})^t.", numeric=False)
r1, r2 = pick(2, 3), pick(5, 6, 7)
mc(ADV, S, "hard", f"The function g is defined by g(x) = (x − {r1})(x − {r2}). In the xy-plane, what is the x-coordinate of the vertex of the graph of y = g(x)?", Fraction(r1 + r2, 2),
   [r1 + r2, r1 * r2, Fraction(r2 - r1, 2)], f"The x-intercepts are {r1} and {r2}; the vertex lies midway between them at ({r1} + {r2})/2 = {fmt(Fraction(r1 + r2, 2))}.")
p0 = pick(120, 150, 240); f = pick(80, 90)
mc(ADV, S, "hard", f"The function m models the mass, in grams, of a sample of a substance t days after it is measured, where m(t) = {p0}(0.{f})^t. By what percent does the mass decrease each day?", 100 - f,
   [f, 100 - f + 10, 100 - f - 5], f"Each day the mass is multiplied by 0.{f}, which is a decrease of 1 − 0.{f} = {100 - f}%.")
a = pick(2, 3)
spr(ADV, S, "hard", f"f(x) = {a}x² + bx + 5\n\nThe function f is defined by the given equation, where b is a constant. If f(2) = f(−4), what is the value of b?", 2 * a,
    f"f(2) = {4 * a} + 2b + 5 and f(−4) = {16 * a} − 4b + 5. Setting them equal: 6b = {12 * a}, so b = {2 * a}.")

S = "Systems of equations in two variables"
mc(ADV, S, "medium", "y = x² − 4\ny = 5\n\nWhich of the following is a solution (x, y) to the given system of equations?",
   "(−3, 5)", ["(3, −5)", "(5, 21)", "(1, −3)"], "Set x² − 4 = 5, so x² = 9 and x = 3 or −3. Both (3, 5) and (−3, 5) are solutions; (−3, 5) is the one listed.", numeric=False)
c = pick(2, 3, 4)
spr(ADV, S, "medium", f"y = x²\ny = {c}x\n\nIf (x, y) is a solution to the given system of equations and x > 0, what is the value of y?", c * c,
    f"x² = {c}x gives x = 0 or x = {c}. For x > 0, x = {c} and y = {c * c}.")
mc(ADV, S, "hard", "y = x² + 9\ny = kx\n\nIn the given system of equations, k is a positive constant. For what value of k does the system have exactly one solution?", 6,
   [3, 9, 18], "x² + 9 = kx gives x² − kx + 9 = 0, which has one solution when k² − 36 = 0. Since k > 0, k = 6.")
mc(ADV, S, "hard", "x² + y² = 25\ny = x + 1\n\nHow many solutions (x, y) does the given system of equations have?", "Exactly two", ["Exactly one", "Zero", "Infinitely many"],
   "Substituting: x² + (x + 1)² = 25, so 2x² + 2x − 24 = 0, or x² + x − 12 = 0, which factors as (x + 4)(x − 3) = 0. Two x-values, two solutions.", numeric=False)
a = pick(2, 3)
spr(ADV, S, "hard", f"y = {a}x²\n{a * 2}x − y = {a}\n\nIf (x, y) is the solution to the given system of equations, what is the value of x?", 1,
    f"Substitute: {a * 2}x − {a}x² = {a}, so {a}x² − {a * 2}x + {a} = 0, or {a}(x − 1)² = 0. Thus x = 1.")

# ============================================================ PROBLEM-SOLVING AND DATA ANALYSIS
S = "Ratios, rates, proportional relationships, and units"
miles, gal = pick((240, 8), (300, 10), (360, 12), (280, 8)); tgt = miles * pick(3, 5) // 2
mc(PSDA, S, "easy", f"A car travels {miles} miles on {gal} gallons of gasoline. At this rate, how many gallons of gasoline does the car use to travel {tgt} miles?", Fraction(tgt * gal, miles),
   [Fraction(tgt, gal), Fraction(miles, gal), Fraction(tgt * gal, miles) + gal], f"The car gets {fmt(Fraction(miles, gal))} miles per gallon, so {tgt} miles requires {tgt} ÷ {fmt(Fraction(miles, gal))} = {fmt(Fraction(tgt * gal, miles))} gallons.")
a, b = pick((2, 3), (3, 5), (4, 7)); k = pick(4, 6, 8)
spr(PSDA, S, "easy", f"The ratio of red marbles to blue marbles in a bag is {a} to {b}. If there are {a * k} red marbles, how many blue marbles are in the bag?", b * k,
    f"Each part of the ratio is {k} marbles ({a * k} ÷ {a}), so there are {b} × {k} = {b * k} blue marbles.")
cm = pick(15, 18, 25)
mc(PSDA, S, "medium", f"A scale model of a building uses a scale of 1 centimeter to 2.5 meters. If the model is {cm} centimeters tall, what is the height of the actual building, in meters?", Fraction(cm * 5, 2),
   [cm * 25, Fraction(cm * 2, 5), cm + 25], f"Multiply the model's height by the scale factor: {cm} × 2.5 = {fmt(Fraction(cm * 5, 2), True)} meters.", dec=True)
kmh = pick(54, 72, 90)
mc(PSDA, S, "medium", f"A train travels at a constant speed of {kmh} kilometers per hour. What is the train's speed in meters per second? (1 kilometer = 1,000 meters)", Fraction(kmh * 1000, 3600),
   [Fraction(kmh * 1000, 60), Fraction(kmh, 60), kmh * 1000], f"{kmh} km/h = {kmh * 1000} m per 3,600 s = {fmt(Fraction(kmh * 1000, 3600), True)} m/s.", dec=True)
w = pick(3, 4, 5); paint = pick(2, 3)
spr(PSDA, S, "medium", f"A painter uses {paint} gallons of paint to cover {w * 100} square feet of wall. At this rate, how many gallons of paint are needed to cover {w * 250} square feet?", Fraction(paint * 5, 2),
    f"Set up a proportion: {paint}/{w * 100} = g/{w * 250}, so g = {paint} × {w * 250}/{w * 100} = {fmt(Fraction(paint * 5, 2), True)} gallons.", dec=True)
c1, c2 = pick(3, 4), pick(5, 6, 8)
mc(PSDA, S, "hard", f"Recipe A calls for flour and sugar in a ratio of {c1} to 1, and recipe B calls for them in a ratio of {c2} to 1. A baker combines {c1 * 2} cups of flour and 2 cups of sugar from recipe A with {c2 * 3} cups of flour and 3 cups of sugar from recipe B. What is the ratio of flour to sugar in the combined mixture?",
   f"{fmt(Fraction(c1 * 2 + c2 * 3, 5), True)} to 1", [f"{fmt(Fraction(c1 + c2, 2), True)} to 1", f"{c1 * c2} to 1", f"{c1 + c2} to 1"],
   f"Total flour is {c1 * 2 + c2 * 3} cups and total sugar is 5 cups, so the ratio is {c1 * 2 + c2 * 3}/5 = {fmt(Fraction(c1 * 2 + c2 * 3, 5), True)} to 1.", numeric=False)
speed = pick(4, 6); dist = pick(1, 2, 3); mins = dist * 60 // speed
mc(PSDA, S, "hard", f"A hiker walks {fmt(dist)} miles in {mins} minutes. At this rate, how many miles will the hiker walk in 2 hours?", 2 * speed,
   [speed, dist * 2, 4 * speed], f"The rate is {fmt(dist)} miles per {mins} minutes, which is {speed} miles per hour, so 2 hours covers {2 * speed} miles.")

S = "Percentages"
n = pick(40, 60, 80, 120); p = pick(15, 25, 30, 45)
mc(PSDA, S, "easy", f"What is {p}% of {n}?", Fraction(n * p, 100), [Fraction(n * p, 10), n - Fraction(n * p, 100), n - p], f"{p}% of {n} = 0.{p:02d} × {n} = {fmt(Fraction(n * p, 100))}.")
price = pick(40, 60, 80); off = pick(15, 20, 25, 30)
spr(PSDA, S, "easy", f"A jacket regularly priced at ${price} is on sale for {off}% off the regular price. What is the sale price of the jacket, in dollars?", Fraction(price * (100 - off), 100),
    f"The discount is {off}% of {price} = {fmt(Fraction(price * off, 100), True)} dollars, so the sale price is {price} − {fmt(Fraction(price * off, 100), True)} = {fmt(Fraction(price * (100 - off), 100), True)} dollars.", dec=True)
old, new = pick((120, 150), (200, 260), (80, 100), (50, 64))
mc(PSDA, S, "medium", f"The number of members of a club increased from {old} to {new}. By what percentage did the number of members increase?", Fraction((new - old) * 100, old),
   [Fraction((new - old) * 100, new), new - old, Fraction(new * 100, old)], f"The increase is {new - old}, which is {new - old}/{old} = {fmt(Fraction((new - old) * 100, old))}% of the original.")
sale = pick(60, 72, 90); pct = pick(20, 25, 40)
mc(PSDA, S, "medium", f"After a {pct}% discount, the price of a bicycle is ${sale}. What was the price of the bicycle before the discount?", Fraction(sale * 100, 100 - pct),
   [sale + Fraction(sale * pct, 100), sale + pct, Fraction(sale * 100, pct)], f"The sale price is {100 - pct}% of the original: 0.{100 - pct} × p = {sale}, so p = {sale}/0.{100 - pct} = {fmt(Fraction(sale * 100, 100 - pct))} dollars.")
p1, p2 = pick(10, 20), pick(10, 20, 50)
mc(PSDA, S, "hard", f"The price of a stock increased by {p1}% one year and then decreased by {p2}% the next year. The price at the end of the two years was what percent of the price at the start?", Fraction((100 + p1) * (100 - p2), 100),
   [100 + p1 - p2, 100, Fraction((100 + p1) * (100 + p2), 100)], f"Multiply the factors: 1.{p1} × 0.{100 - p2} = {fmt(Fraction((100 + p1) * (100 - p2), 10000))}, which is {fmt(Fraction((100 + p1) * (100 - p2), 100))}%.")
tax = pick(6, 8); base = pick(50, 100, 150); total = base * (100 + tax) // 100
spr(PSDA, S, "hard", f"A restaurant bill, including {tax}% sales tax, came to ${total}. What was the bill, in dollars, before tax?", base,
    f"The total is {100 + tax}% of the pre-tax bill: 1.0{tax}b = {total}, so b = {base}.")
part = pick(12, 18, 27); whole = pick(40, 60, 90)
mc(PSDA, S, "medium", f"In a survey of {whole} students, {part} said they walk to school. What percentage of the students surveyed said they walk to school?", Fraction(part * 100, whole),
   [Fraction(whole * 100, part), part, Fraction((whole - part) * 100, whole)], f"{part}/{whole} = {fmt(Fraction(part * 100, whole))}%.")

S = "One-variable data: distributions and measures of center and spread"
data = sorted(R.sample(range(60, 100), 7))
mc(PSDA, S, "easy", f"{', '.join(map(str, data))}\n\nWhat is the median of the seven data values listed?", data[3],
   [data[2], data[4], data[6] - data[0]], f"Listed in order, the middle (fourth) value is {data[3]}.")
vals = sorted([pick(2, 3), pick(4, 5), pick(4, 5), 7, 9])
spr(PSDA, S, "easy", f"{', '.join(map(str, vals))}\n\nWhat is the mean of the five numbers listed?", Fraction(sum(vals), 5),
    f"Add the values ({sum(vals)}) and divide by 5: {fmt(Fraction(sum(vals), 5), True)}.", dec=True)
mc(PSDA, S, "medium", "Data set A: 2, 4, 6, 8, 10\nData set B: 5, 6, 6, 6, 7\n\nWhich of the following statements about the two data sets is true?",
   "The means are equal, and the standard deviation of A is greater than that of B.",
   ["The means are equal, and the standard deviation of B is greater than that of A.", "The mean of A is greater than the mean of B.", "The medians are different."],
   "Both sets have mean 6 and median 6. Set A's values are spread from 2 to 10; set B's are clustered near 6, so A has the larger standard deviation.", numeric=False)
avg = pick(80, 84, 88); n = pick(4, 5); last = pick(60, 95, 100)
spr(PSDA, S, "medium", f"The mean of {n} test scores is {avg}. If a {'fifth' if n == 4 else 'sixth'} score of {last} is added, what is the mean of all {n + 1} scores?", Fraction(avg * n + last, n + 1),
    f"The {n} scores total {avg * n}; adding {last} gives {avg * n + last}, and dividing by {n + 1} gives {fmt(Fraction(avg * n + last, n + 1), True)}.", dec=True)
mc(PSDA, S, "medium", "Number of pets   Frequency\n0                5\n1                8\n2                4\n3                2\n4                1\n\nThe table shows the number of pets owned by each of 20 students. What is the median number of pets?", 1,
   [0, 2, Fraction(3, 2)], "In order, values 1 through 5 are 0 and values 6 through 13 are 1. The 10th and 11th values are both 1, so the median is 1.")
mc(PSDA, S, "hard", "A data set of 15 house prices has a mean of $320,000 and a median of $290,000. If the highest price in the data set is removed, which of the following is most likely to be true?",
   "The mean will decrease more than the median will.", ["The median will decrease more than the mean will.", "The mean and median will decrease by the same amount.", "Neither the mean nor the median will change."],
   "A mean above the median signals a high outlier pulling the mean up. Removing the highest value lowers the mean noticeably, while the median shifts to the next middle value, usually a small change.", numeric=False)
mc(PSDA, S, "hard", "Two classes took the same test. Class A's scores had a mean of 78 and a standard deviation of 4. Class B's scores had a mean of 78 and a standard deviation of 12. Which of the following is the best interpretation of the standard deviations?",
   "Class A's scores were more tightly clustered around 78 than Class B's scores were.",
   ["Class A's highest score was lower than Class B's highest score.", "Class B had more students than Class A.", "Class B's median was higher than Class A's median."],
   "Standard deviation measures spread around the mean. A smaller standard deviation means the scores are closer to the mean. It does not determine the maximum, the class size, or the median.", numeric=False)

S = "Two-variable data: models and scatterplots"
m = pick(2, 3, 5); b = pick(10, 20, 30)
mc(PSDA, S, "medium", f"A scatterplot shows the relationship between the number of hours x a student studied and the score y on a test. The line of best fit is y = {m}x + {b}. Which of the following is the best interpretation of the number {m} in this context?",
   f"The predicted score increases by {m} points for each additional hour of study.", [f"The predicted score for a student who studies 0 hours is {m}.", f"Each student studied about {m} hours.", f"The predicted score increases by {m} points for every {b} hours of study."],
   f"The slope gives the change in y per unit change in x: {m} points per hour.", numeric=False)
m = pick(2, 3, 5); b = pick(10, 20, 30); x0 = pick(4, 6, 8); delta = pick(-6, 5, 7); actual = m * x0 + b + delta
mc(PSDA, S, "medium", f"The line of best fit for a data set is y = {m}x + {b}. One data point in the set is ({x0}, {actual}). How much {'greater' if delta > 0 else 'less'} is the actual y-value of this point than the y-value predicted by the line of best fit?", abs(delta),
   [m * x0 + b, actual, abs(actual - b)], f"The predicted value is {m}({x0}) + {b} = {m * x0 + b}; the difference from {actual} is {abs(delta)}.")
p0 = pick(50, 80); g = pick(4, 6)
mc(PSDA, S, "hard", f"Year   Trees planted\n0      {p0}\n1      {p0 + g}\n2      {p0 + 2 * g}\n3      {p0 + 3 * g}\n\nThe table shows the number of trees a group planted each year for four years. Which type of function best models the number of trees planted, y, as a function of the year, x?",
   f"A linear function with slope {g}", ["An exponential function with a growth factor of 2", f"A linear function with slope {p0}", "A quadratic function with a positive leading coefficient"],
   f"The number increases by the same amount, {g}, each year, which is a constant rate of change: a linear model with slope {g}.", numeric=False)
mc(PSDA, S, "hard", "Day   Bacteria\n0     100\n1     300\n2     900\n3     2,700\n\nThe table shows the number of bacteria in a culture on four days. Which function best models the number of bacteria, B, as a function of the day, d?",
   "B(d) = 100(3)^d", ["B(d) = 100 + 200d", "B(d) = 100(2)^d", "B(d) = 300d"],
   "The count is multiplied by 3 each day, which is exponential growth with factor 3 from an initial 100.", numeric=False)
mc(PSDA, S, "medium", "A scatterplot shows a strong negative linear association between the average monthly temperature in a city and the amount of heating fuel its residents use that month. Which statement is most consistent with the scatterplot?",
   "In months with higher average temperatures, residents tended to use less fuel.", ["Higher temperatures cause residents to use more fuel.", "There is no relationship between temperature and fuel use.", "In months with higher average temperatures, residents tended to use more fuel."],
   "A negative association means that as one variable increases, the other tends to decrease. 'Tended to' is right; the scatterplot alone cannot establish cause.", numeric=False)

S = "Probability and conditional probability"
r, b, g = pick(3, 4, 5), pick(7, 8), pick(1, 2)
mc(PSDA, S, "easy", f"A bag contains {r} red, {b} blue, and {g} green marbles. If one marble is selected at random, what is the probability that it is blue?", Fraction(b, r + b + g),
   [Fraction(r, r + b + g), Fraction(r + g, r + b + g), Fraction(g, r + b + g)], f"There are {r + b + g} marbles, {b} of them blue: {fmt(Fraction(b, r + b + g))}.")
tbl = [[4 * R.randint(3, 8), 4 * R.randint(3, 8)], [4 * R.randint(3, 8), 4 * R.randint(3, 8)]]
tot = sum(map(sum, tbl))
passage = f"           Cats   No cats\nDogs       {tbl[0][0]:<6} {tbl[0][1]}\nNo dogs    {tbl[1][0]:<6} {tbl[1][1]}\n\nThe table shows the pets owned by {tot} households."
mc(PSDA, S, "medium", "If a household is selected at random from those that own dogs, what is the probability that it also owns cats?", Fraction(tbl[0][0], sum(tbl[0])),
   [Fraction(tbl[0][0], tot), Fraction(tbl[0][0], tbl[0][0] + tbl[1][0]), Fraction(sum(tbl[0]), tot)],
   f"Restrict to dog owners: {sum(tbl[0])} households, of which {tbl[0][0]} own cats. The probability is {fmt(Fraction(tbl[0][0], sum(tbl[0])))}.", passage=passage)
mc(PSDA, S, "medium", "If a household is selected at random from all the households, what is the probability that it owns neither cats nor dogs?", Fraction(tbl[1][1], tot),
   [Fraction(tbl[1][1], sum(tbl[1])), Fraction(tbl[1][1], tbl[0][1] + tbl[1][1]), Fraction(tot - tbl[1][1], tot)],
   f"{tbl[1][1]} of the {tot} households own neither: {fmt(Fraction(tbl[1][1], tot))}.", passage=passage)
n = pick(20, 25, 40)
spr(PSDA, S, "easy", f"A jar contains {n} tickets numbered 1 through {n}. One ticket is drawn at random. What is the probability that the number on the ticket is a multiple of 5?", Fraction(n // 5, n),
    f"There are {n // 5} multiples of 5 from 1 to {n}, so the probability is {n // 5}/{n} = {fmt(Fraction(n // 5, n))}.")
mc(PSDA, S, "hard", "A box contains 4 red and 6 black cards. Two cards are drawn at random without replacement. What is the probability that both cards are red?", Fraction(4 * 3, 10 * 9),
   [Fraction(4 * 4, 10 * 10), Fraction(2, 10), Fraction(4, 10)], "P(first red) = 4/10; then 3 red remain among 9 cards, so P(second red) = 3/9. The product is 12/90 = 2/15.")
mc(PSDA, S, "hard", "In a school, 60% of students take Spanish, 30% take French, and 10% take both. If a student who takes Spanish is selected at random, what is the probability that the student also takes French?", Fraction(1, 6),
   [Fraction(1, 10), Fraction(1, 3), Fraction(3, 10)], "P(French | Spanish) = P(both)/P(Spanish) = 0.10/0.60 = 1/6.")

S = "Inference from sample statistics and margin of error"
mc(PSDA, S, "medium", "A random sample of 400 residents of a city was surveyed, and 52% said they support building a new park, with a margin of error of 5 percentage points. Which of the following is the most appropriate conclusion?",
   "It is plausible that between 47% and 57% of all the city's residents support the park.", ["Exactly 52% of the city's residents support the park.", "Between 47% and 57% of the residents surveyed support the park.", "The survey should have included more than 400 residents to be valid."],
   "The margin of error describes uncertainty in extending the sample result to the population: the population percentage is plausibly within 52% ± 5%.", numeric=False)
mc(PSDA, S, "medium", "Researchers want to estimate the mean commute time of employees at a large company. Which sampling method is most likely to produce a sample that represents all the employees?",
   "Selecting 200 employees at random from a list of all employees", ["Surveying the first 200 employees to arrive one morning", "Surveying 200 employees who volunteer online", "Surveying all 200 employees in the company's main office"],
   "Only random selection from the whole population avoids favoring some employees (early arrivers, volunteers, one office) over others.", numeric=False)
mc(PSDA, S, "hard", "Two surveys estimate the proportion of adults in a state who own a bicycle. Survey A used a random sample of 500 adults; survey B used a random sample of 2,000 adults. Both reported 38%. Which statement is true about the margins of error?",
   "Survey B's margin of error is smaller than survey A's.", ["Survey A's margin of error is smaller than survey B's.", "The margins of error are equal because both surveys reported 38%.", "The margin of error cannot be compared without knowing the state's population."],
   "For random samples, a larger sample gives a smaller margin of error; the estimate itself does not determine the margin.", numeric=False)
mc(PSDA, S, "hard", "A random sample of 150 apples from an orchard has a mean mass of 182 grams, and the estimated margin of error for the mean is 6 grams. Which of the following is the best interpretation?",
   "The mean mass of all apples in the orchard is plausibly between 176 and 188 grams.", ["Every apple in the orchard has a mass between 176 and 188 grams.", "The masses of the 150 apples ranged from 176 to 188 grams.", "Exactly 182 grams is the mean mass of all apples in the orchard."],
   "The interval 182 ± 6 is a range of plausible values for the population mean, not for individual apples or the sample's range.", numeric=False)
mc(PSDA, S, "medium", "A poll of 1,000 randomly selected voters found that 46% favored a ballot measure. Which of the following changes to the poll would reduce the margin of error?",
   "Increasing the sample size", ["Decreasing the sample size", "Surveying only voters who have an opinion", "Reporting the result to more decimal places"],
   "Margin of error shrinks as sample size grows. Selecting only opinionated voters introduces bias, and precision of reporting does not change the underlying uncertainty.", numeric=False)

S = "Evaluating statistical claims"
mc(PSDA, S, "medium", "A study found that people who drink coffee daily have lower rates of a certain disease than people who do not. The study did not assign people to groups. Which of the following is the most appropriate conclusion?",
   "There is an association between drinking coffee and lower rates of the disease, but the study cannot show that coffee causes the lower rate.", ["Drinking coffee causes lower rates of the disease.", "People with the disease should start drinking coffee.", "There is no relationship between coffee and the disease."],
   "Without random assignment, an observational study can show association, not causation; other differences between the groups could explain the result.", numeric=False)
mc(PSDA, S, "medium", "In an experiment, 200 volunteers with insomnia were randomly assigned to take either a new supplement or a placebo. After a month, the supplement group slept 40 minutes longer per night on average. Which of the following is the most appropriate conclusion?",
   "The supplement likely caused the longer sleep, but the result generalizes only to people similar to the volunteers.", ["The supplement causes longer sleep for all adults with insomnia.", "Only an association can be concluded, but it applies to all adults with insomnia.", "Neither causation nor association can be concluded."],
   "Random assignment supports a causal conclusion; but because the participants were volunteers rather than a random sample of all adults with insomnia, the result generalizes only to similar people.", numeric=False)
mc(PSDA, S, "hard", "A company claims that its tutoring program raises SAT scores, citing that students who completed the program scored 120 points higher on average than students who did not enroll. Which of the following is the strongest objection to this claim?",
   "Students who chose to enroll may differ from those who did not in ways that affect scores, such as motivation.", ["The company should have compared scores to the national average.", "120 points is too small a difference to matter.", "The students should not have been told their scores."],
   "Self-selection means the two groups may not be comparable; the difference could reflect who enrolls rather than the program. The other objections do not address the validity of the comparison.", numeric=False)
mc(PSDA, S, "hard", "A researcher wants to test whether a new fertilizer increases tomato yield. Which design would best support a conclusion that the fertilizer causes any increase observed?",
   "Randomly assign half of 60 similar plots to receive the fertilizer and compare their yields with the other half.", ["Apply the fertilizer to the 30 plots with the best soil and compare their yields with the other 30.", "Survey farmers who use the fertilizer about their yields.", "Apply the fertilizer to all 60 plots and compare yields with last year's."],
   "Random assignment with a comparison group isolates the fertilizer's effect. Choosing plots by soil quality or comparing across years introduces other differences.", numeric=False)

# ============================================================ GEOMETRY AND TRIGONOMETRY
S = "Area and volume"
l, w = pick(8, 10, 12), pick(5, 6, 7)
mc(GEO, S, "easy", f"A rectangle has a length of {l} centimeters and a width of {w} centimeters. What is the area of the rectangle, in square centimeters?", l * w,
   [2 * (l + w), l + w, Fraction(l * w, 2)], f"Area = length × width = {l} × {w} = {l * w}.")
r = pick(3, 5, 6)
mc(GEO, S, "easy", f"What is the area, in square units, of a circle with radius {r}?", f"{r * r}π", [f"{2 * r}π", f"{r * r * 2}π", f"{r}π"],
   f"Area = πr² = π({r})² = {r * r}π.", numeric=False)
l, w, h = pick(4, 5), pick(6, 8), pick(3, 10)
spr(GEO, S, "easy", f"A rectangular box has a length of {l} inches, a width of {w} inches, and a height of {h} inches. What is the volume of the box, in cubic inches?", l * w * h,
    f"Volume = {l} × {w} × {h} = {l * w * h}.")
b, h = pick(10, 12, 16), pick(5, 7, 9)
spr(GEO, S, "medium", f"A triangle has a base of {b} inches and a height of {h} inches. What is the area of the triangle, in square inches?", Fraction(b * h, 2),
    f"Area = (1/2) × base × height = (1/2)({b})({h}) = {fmt(Fraction(b * h, 2), True)}.", dec=True)
r, h = pick(3, 4), pick(5, 6, 10)
mc(GEO, S, "medium", f"A right circular cylinder has a radius of {r} centimeters and a height of {h} centimeters. What is the volume of the cylinder, in cubic centimeters?", f"{r * r * h}π", [f"{2 * r * h}π", f"{r * h}π", f"{r * r * h * 3}π"],
   f"Volume = πr²h = π({r})²({h}) = {r * r * h}π.", numeric=False)
s = pick(4, 6, 8)
mc(GEO, S, "medium", f"The area of a square is {s * s} square meters. What is the perimeter of the square, in meters?", 4 * s, [s, s * s, 2 * s], f"The side length is √{s * s} = {s}, so the perimeter is 4 × {s} = {4 * s}.")
r = pick(6, 9)
mc(GEO, S, "hard", f"A sphere has a radius of {r} inches. What is the volume of the sphere, in cubic inches?", f"{fmt(Fraction(4 * r ** 3, 3))}π", [f"{4 * r * r}π", f"{fmt(Fraction(4 * r * r, 3))}π", f"{fmt(Fraction(r ** 3, 3))}π"],
   f"Volume = (4/3)πr³ = (4/3)π({r})³ = {fmt(Fraction(4 * r ** 3, 3))}π.", numeric=False)
k = pick(2, 3)
mc(GEO, S, "hard", f"The length and width of rectangle A are each {k} times the length and width of rectangle B. The area of rectangle A is how many times the area of rectangle B?", k * k, [k, 2 * k, k ** 3],
   f"Scaling both dimensions by {k} scales the area by {k} × {k} = {k * k}.")

S = "Lines, angles, and triangles"
a = pick(35, 48, 62); b = pick(50, 57, 71)
spr(GEO, S, "easy", f"In a triangle, two of the angles measure {a}° and {b}°. What is the measure, in degrees, of the third angle?", 180 - a - b,
    f"The angles of a triangle sum to 180°, so the third angle is 180 − {a} − {b} = {180 - a - b}°.")
x = pick(40, 55, 70)
mc(GEO, S, "easy", f"Two lines intersect, forming four angles. One of the angles measures {x}°. What is the measure of an angle adjacent to it?", 180 - x, [x, 90 - x, 360 - x],
   f"Adjacent angles formed by intersecting lines are supplementary: 180 − {x} = {180 - x}°.")
x = pick(38, 44, 52)
mc(GEO, S, "medium", f"Two parallel lines are cut by a transversal. One of the acute angles formed measures {x}°. What is the measure of each obtuse angle formed?", 180 - x, [x, 90 + x, 2 * x],
   f"Each obtuse angle is supplementary to each acute angle: 180 − {x} = {180 - x}°.")
base = pick(40, 50, 64)
spr(GEO, S, "medium", f"In an isosceles triangle, the two equal angles each measure {base}°. What is the measure, in degrees, of the third angle?", 180 - 2 * base,
    f"180 − 2({base}) = {180 - 2 * base}°.")
k = pick(2, 3); a, b, c = 3 * k, 4 * k, 5 * k
mc(GEO, S, "medium", f"Triangle ABC is similar to triangle DEF, with A corresponding to D and B corresponding to E. AB = 3, BC = 4, and DE = {a}. What is the length of EF?", b, [a, c, 4 + a - 3],
   f"The scale factor is DE/AB = {a}/3 = {k}, so EF = {k} × BC = {b}.")
n = pick(5, 6, 8)
mc(GEO, S, "hard", f"What is the measure, in degrees, of each interior angle of a regular polygon with {n} sides?", Fraction(180 * (n - 2), n), [Fraction(360, n), 180 * (n - 2), 180 - n],
   f"The interior angles sum to 180({n} − 2) = {180 * (n - 2)}°; dividing by {n} gives {fmt(Fraction(180 * (n - 2), n))}°.")
mc(GEO, S, "hard", "In triangle PQR, the measure of angle P is twice the measure of angle Q, and the measure of angle R is 30° more than the measure of angle Q. What is the measure of angle P, in degrees?", 75, [37.5, 67.5, 105],
   "Let Q = q. Then 2q + q + (q + 30) = 180, so 4q = 150 and q = 37.5. Angle P = 2q = 75°.", dec=True)

S = "Right triangles and trigonometry"
a, b, c = pick((3, 4, 5), (5, 12, 13), (8, 15, 17)); k = pick(1, 2, 3)
spr(GEO, S, "easy", f"A right triangle has legs of length {a * k} and {b * k}. What is the length of the hypotenuse?", c * k,
    f"By the Pythagorean theorem, √({a * k}² + {b * k}²) = √{(a * k) ** 2 + (b * k) ** 2} = {c * k}.")
a, b, c = pick((3, 4, 5), (5, 12, 13), (7, 24, 25))
mc(GEO, S, "easy", f"The hypotenuse of a right triangle has length {c}, and one leg has length {a}. What is the length of the other leg?", b, [c - a, c + a, c * c - a * a],
   f"√({c}² − {a}²) = √{c * c - a * a} = {b}.")
a, b, c = pick((3, 4, 5), (5, 12, 13), (8, 15, 17))
mc(GEO, S, "medium", f"In right triangle ABC, angle C is the right angle, AC = {b}, and BC = {a}. What is the value of sin A?", f"{a}/{c}", [f"{b}/{c}", f"{a}/{b}", f"{b}/{a}"],
   f"The hypotenuse AB = {c}. sin A = (opposite)/(hypotenuse) = BC/AB = {a}/{c}.", numeric=False)
mc(GEO, S, "medium", "In a right triangle, one acute angle measures 30°. If the hypotenuse has length 12, what is the length of the side opposite the 30° angle?", 6, [12, 4, 8],
   "The side opposite 30° is half the hypotenuse: 12 ÷ 2 = 6.")
mc(GEO, S, "medium", "A ladder leaning against a wall makes a 60° angle with the ground. If the foot of the ladder is 5 feet from the wall, what is the length of the ladder, in feet?", 10, [5, 20, 15],
   "cos 60° = adjacent/hypotenuse = 5/L, and cos 60° = 1/2, so L = 10.")
mc(GEO, S, "hard", "In right triangle XYZ, the right angle is at Y. If tan X = 3/4, what is the value of cos Z?", "3/5", ["4/5", "3/4", "4/3"],
   "tan X = 3/4 means the legs are in ratio 3 : 4 (opposite X : adjacent X), so the hypotenuse is 5. Angle Z's adjacent side is the leg opposite X, length 3, so cos Z = 3/5.", numeric=False)
mc(GEO, S, "hard", "Angles A and B are the acute angles of a right triangle. If sin A = 0.6, what is the value of cos B?", "0.6", ["0.8", "0.36", "0.4"],
   "In a right triangle the acute angles are complementary, and sin A = cos(90° − A) = cos B. So cos B = 0.6.", numeric=False)
mc(GEO, S, "hard", "An angle measure of π/3 radians is equivalent to how many degrees?", 60, [30, 90, 120], "π radians = 180°, so π/3 radians = 180°/3 = 60°.")

S = "Circles"
h, k, r = pick(-3, 2, 5), pick(-4, 1, 6), pick(2, 3, 5)
sx = "−" if h > 0 else "+"; sy = "−" if k > 0 else "+"; ox = "+" if h > 0 else "−"; oy = "+" if k > 0 else "−"
mc(GEO, S, "easy", f"Which equation represents the circle in the xy-plane with center ({neg(h)}, {neg(k)}) and radius {r}?",
   f"(x {sx} {abs(h)})² + (y {sy} {abs(k)})² = {r * r}",
   [f"(x {ox} {abs(h)})² + (y {oy} {abs(k)})² = {r * r}", f"(x {sx} {abs(h)})² + (y {sy} {abs(k)})² = {r}", f"(x {sx} {abs(h)})² − (y {sy} {abs(k)})² = {r * r}"],
   f"A circle with center (h, k) and radius r has equation (x − h)² + (y − k)² = r²; here r² = {r * r}.", numeric=False)
r = pick(4, 6, 9)
spr(GEO, S, "easy", f"x² + y² = {r * r}\n\nWhat is the radius of the circle in the xy-plane defined by the given equation?", r, f"The equation has the form x² + y² = r² with r² = {r * r}, so r = {r}.")
r = pick(6, 9, 12); deg = pick(60, 90, 120)
mc(GEO, S, "medium", f"A circle has radius {r}. What is the length of an arc that subtends a central angle of {deg}°?", f"{fmt(Fraction(2 * r * deg, 360))}π", [f"{fmt(Fraction(r * deg, 360))}π", f"{fmt(Fraction(r * r * deg, 360))}π", f"{deg}π"],
   f"Arc length = ({deg}/360) × 2π({r}) = {fmt(Fraction(2 * r * deg, 360))}π.", numeric=False)
r = pick(4, 6, 8); deg = pick(45, 90, 120)
mc(GEO, S, "medium", f"A circle has radius {r}. What is the area of a sector with a central angle of {deg}°?", f"{fmt(Fraction(r * r * deg, 360))}π", [f"{fmt(Fraction(2 * r * deg, 360))}π", f"{r * r}π", f"{fmt(Fraction(r * r * deg, 180))}π"],
   f"Sector area = ({deg}/360) × π({r})² = {fmt(Fraction(r * r * deg, 360))}π.", numeric=False)
h, k, r = pick(2, 4), pick(3, 5), pick(3, 5)
mc(GEO, S, "hard", f"x² + y² − {2 * h}x − {2 * k}y + {h * h + k * k - r * r} = 0\n\nWhat is the radius of the circle in the xy-plane defined by the given equation?", r, [r * r, h, h * h + k * k - r * r],
   f"Complete the square: (x − {h})² + (y − {k})² = {r * r}, so the radius is {r}.")
mc(GEO, S, "hard", "Points A and B lie on a circle with center O. If the measure of angle AOB is 80°, what is the measure, in degrees, of an inscribed angle that intercepts the same arc AB?", 40, [80, 160, 100],
   "An inscribed angle measures half the central angle that intercepts the same arc: 80 ÷ 2 = 40°.")
mc(GEO, S, "medium", "A circle in the xy-plane has center (3, −2) and passes through the point (7, 1). What is the radius of the circle?", 5, [7, 25, 3],
   "The radius is the distance from the center to the point: √((7 − 3)² + (1 − (−2))²) = √(16 + 9) = 5.")

# ---------------------------------------------------------------- output
if __name__ == "__main__":
    json.dump(OUT, sys.stdout, ensure_ascii=False, indent=1)
