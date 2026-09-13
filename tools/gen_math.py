"""Math question generator for the ABLE Preps bank.

Every template computes its answer from its parameters, so no key can be
wrong. Distractors are the answers a student gets from a specific common
error (sign slip, using the intercept instead of the slope, forgetting to
square, etc.), which is what makes them tempting. Parameters are drawn
from a seeded RNG so the bank is reproducible.
"""
import json, io, random, sys
from fractions import Fraction
from math import gcd, sqrt, isqrt

R = random.Random(2026)
OUT = []
_next = [25]

ALG = "Algebra"; ADV = "Advanced Math"; PSDA = "Problem-Solving and Data Analysis"; GEO = "Geometry and Trigonometry"

def fmt(n):
    if isinstance(n, Fraction):
        if n.denominator == 1: return str(n.numerator)
        return f"{n.numerator}/{n.denominator}"
    if isinstance(n, float):
        return f"{n:g}"
    return str(n)

def sgn(n):  # "+ 3" / "− 3"
    return f"+ {n}" if n >= 0 else f"− {-n}"

def mc(domain, skill, diff, stem, correct, distractors, expl):
    """correct + distractors are display strings; distractors are de-duplicated
    against the correct answer and each other, and topped up if needed."""
    seen = {str(correct)}
    ds = []
    for x in distractors:
        s = str(x)
        if s not in seen:
            seen.add(s); ds.append(s)
        if len(ds) == 3: break
    assert len(ds) == 3, (stem, correct, distractors)
    choices = ds + [str(correct)]
    R.shuffle(choices)
    OUT.append({"id": f"m-{_next[0]:03d}", "section": "math", "domain": domain, "skill": skill, "difficulty": diff,
                "stem": stem, "choices": choices, "answer": choices.index(str(correct)), "explanation": expl})
    _next[0] += 1

def spr(domain, skill, diff, stem, answer, expl):
    OUT.append({"id": f"m-{_next[0]:03d}", "section": "math", "domain": domain, "skill": skill, "difficulty": diff,
                "stem": stem, "type": "spr", "answer": fmt(answer), "explanation": expl})
    _next[0] += 1

# ============================================================ ALGEBRA
S_L1 = "Linear equations in one variable"
for _ in range(3):
    a = R.choice([2, 3, 4, 5, 6]); x = R.randint(2, 12); b = R.randint(1, 15); c = a * x + b
    spr(ALG, S_L1, "easy", f"If {a}x + {b} = {c}, what is the value of x?", x,
        f"Subtract {b} from both sides: {a}x = {c - b}. Divide by {a}: x = {x}.")
for _ in range(3):
    a = R.choice([2, 3, 4]); b = R.randint(1, 6); c = R.choice([5, 6, 7, 8]); x = R.randint(2, 9); d = a * (x + b) - c * x
    stem = f"What value of x satisfies {a}(x + {b}) = {c}x {sgn(d)}?"
    mc(ALG, S_L1, "medium", stem, x, [x + b, a * b, -x],
       f"Distribute: {a}x + {a*b} = {c}x {sgn(d)}. Collect x terms: {a*b - d} = {c - a}x, so x = {x}. (A common slip is to forget to multiply {b} by {a} when distributing.)")
for _ in range(2):
    n = R.randint(4, 15); k = R.randint(2, 9); m = R.randint(1, 8)
    # k less than twice a number is m more than the number: 2n - k = n + m -> n = k + m
    n = k + m
    spr(ALG, S_L1, "hard", f"{k} less than twice a number is {m} more than the number. What is the number?", n,
        f"Let the number be n. \"{k} less than twice a number\" is 2n − {k}; \"{m} more than the number\" is n + {m}. Set them equal: 2n − {k} = n + {m}, so n = {k + m}.")

S_LF = "Linear functions"
for _ in range(2):
    x1, y1 = R.randint(-4, 4), R.randint(-6, 6); dx = R.choice([1, 2, 3, 4]); m = R.choice([-3, -2, -1, 2, 3, 4]); x2, y2 = x1 + dx, y1 + m * dx
    mc(ALG, S_LF, "easy", f"What is the slope of the line that passes through the points ({x1}, {y1}) and ({x2}, {y2}) in the xy-plane?", m,
       [-m, Fraction(dx, m) if m else 1, m + 1],
       f"Slope = change in y over change in x = ({y2} − {y1}) / ({x2} − {x1}) = {y2 - y1}/{dx} = {m}. Reversing the subtraction in only one of the differences flips the sign, and dividing the other way gives the reciprocal.")
for _ in range(3):
    f = R.choice([20, 25, 30, 40, 50]); r = R.choice([12, 15, 18, 20, 24, 35]); m1 = R.randint(2, 5); m2 = m1 + R.randint(2, 6)
    t1, t2 = f + r * m1, f + r * m2
    mc(ALG, S_LF, "medium", f"A streaming service charges a one-time setup fee plus a fixed monthly rate. A customer paid ${t1} in total for the first {m1} months and ${t2} in total for the first {m2} months. What is the monthly rate, in dollars?", r,
       [f, Fraction(t2, m2) if t2 % m2 else t2 // m2, t2 - t1],
       f"The difference between the two totals covers {m2 - m1} extra months: ${t2} − ${t1} = ${t2 - t1}, so the monthly rate is {t2 - t1}/{m2 - m1} = ${r}. (Then the setup fee is ${t1} − {m1}·{r} = ${f}.)")
for _ in range(2):
    m = R.choice([-3, -2, 2, 3, 5]); b = R.randint(-8, 8); a, c = R.randint(1, 4), R.randint(6, 10); bb = a + R.randint(1, 3)
    spr(ALG, S_LF, "hard", f"For the linear function f, f({a}) = {m*a + b} and f({bb}) = {m*bb + b}. What is the value of f({c})?", m * c + b,
        f"The slope is ({m*bb + b} − {m*a + b}) / ({bb} − {a}) = {m}. Using f({a}) = {m*a+b}: f(x) = {m}(x − {a}) + {m*a+b}, so f({c}) = {m}·{c - a} + {m*a+b} = {m*c + b}.")

S_L2 = "Linear equations in two variables"
for _ in range(2):
    m = R.choice([2, 3, -2, 4, -3]); b = R.randint(-7, 7); x = R.randint(2, 6)
    spr(ALG, S_L2, "easy", f"The line y = {m}x {sgn(b)} passes through the point ({x}, k) in the xy-plane. What is the value of k?", m * x + b,
        f"Substitute x = {x}: k = {m}({x}) {sgn(b)} = {m*x} {sgn(b)} = {m*x + b}.")
for _ in range(2):
    xi = R.randint(2, 8); a = R.choice([2, 3, 4, 5]); c = a * xi; b = R.choice([2, 3, 4, 6])
    mc(ALG, S_L2, "medium", f"What is the x-intercept of the graph of {a}x + {b}y = {c} in the xy-plane?", f"({xi}, 0)",
       [f"(0, {Fraction(c, b)})".replace("(0, ", "(0, "), f"({c}, 0)", f"(0, {xi})"],
       f"At the x-intercept, y = 0: {a}x = {c}, so x = {xi}. The point is ({xi}, 0). Setting x = 0 instead gives the y-intercept, and (c, 0) forgets to divide by the coefficient.")
for _ in range(2):
    m = R.choice([2, 3, -2, -1, 4]); x1, y1 = R.randint(1, 5), R.randint(-5, 8); b0 = R.randint(-9, 9)
    b = y1 - m * x1
    mc(ALG, S_L2, "hard", f"In the xy-plane, a line passes through ({x1}, {y1}) and is parallel to the line y = {m}x {sgn(b0)}. What is the y-intercept of the first line?", b,
       [b0, y1, -b],
       f"Parallel lines share a slope, so the line is y = {m}x + b. Substitute ({x1}, {y1}): {y1} = {m}·{x1} + b, so b = {y1} − {m*x1} = {b}. The y-intercept is {b}; {b0} is the other line's intercept.")

S_SYS = "Systems of two linear equations"
for _ in range(2):
    x, y = R.randint(2, 12), R.randint(1, 9)
    spr(ALG, S_SYS, "easy", f"If x + y = {x + y} and x − y = {x - y}, what is the value of x?", x,
        f"Add the two equations: 2x = {2*x}, so x = {x}. (Then y = {y}.)")
for _ in range(3):
    pa, pc = R.choice([(12, 8), (15, 9), (10, 6), (20, 12), (18, 10)]); n = R.randint(20, 60); a = R.randint(5, n - 5); c = n - a
    rev = pa * a + pc * c
    mc(ALG, S_SYS, "medium", f"A theater sold {n} tickets to a show. Adult tickets cost ${pa} and child tickets cost ${pc}, and the total revenue was ${rev}. How many adult tickets were sold?", a,
       [c, n, a + c // 2 if c // 2 else a + 1],
       f"Let a be adult tickets and c child tickets. Then a + c = {n} and {pa}a + {pc}c = {rev}. From the first, c = {n} − a. Substitute: {pa}a + {pc}({n} − a) = {rev}, so {pa - pc}a = {rev - pc*n}, and a = {a}. ({c} is the number of child tickets.)")
for _ in range(2):
    a, b = R.choice([2, 3, 4]), R.choice([3, 5, 7]); k = R.choice([2, 3]); c1 = R.randint(5, 20); c2 = k * c1 + R.choice([1, 2, 3, -1, -2])
    spr(ALG, S_SYS, "hard", f"The system of equations below has no solution. What is the value of k?\n\n{a}x + {b}y = {c1}\n{k*a}x + ky = {c2}".replace("ky", "ky"), k * b,
        f"Lines with no common point are parallel: the second equation's coefficients must be a multiple of the first's. {k*a} is {k}·{a}, so k must be {k}·{b} = {k*b}; and {c2} ≠ {k}·{c1} = {k*c1}, so the lines are distinct rather than identical.")

S_INEQ = "Linear inequalities"
for _ in range(2):
    a = R.choice([2, 3, 4, 5]); x0 = R.randint(2, 8); b = R.randint(1, 9); c = a * x0 - b
    mc(ALG, S_INEQ, "easy", f"Which of the following values of x satisfies the inequality {a}x − {b} > {c}?", x0 + 1,
       [x0, x0 - 1, x0 - 2],
       f"Add {b}: {a}x > {c + b}. Divide by {a}: x > {x0}. The inequality is strict, so {x0} itself does not work; the only listed value greater than {x0} is {x0 + 1}.")
for _ in range(2):
    fee = R.choice([15, 20, 25, 30]); per = R.choice([6, 7, 8, 9, 12]); nmax = R.randint(5, 14); budget = fee + per * nmax + R.randint(0, per - 1)
    mc(ALG, S_INEQ, "medium", f"A club has ${budget} to spend on a party. The venue charges a flat ${fee} fee plus ${per} per guest. What is the greatest number of guests the club can afford?", nmax,
       [nmax + 1, (budget) // per, nmax - 1],
       f"With g guests the cost is {fee} + {per}g, which must be at most {budget}: {per}g ≤ {budget - fee}, so g ≤ {(budget - fee)/per:g}. The greatest whole number is {nmax}. Ignoring the flat fee gives {budget // per}, which is too many.")
for _ in range(2):
    a = R.choice([3, 4, 5, 6]); b = R.randint(1, 8); lo = R.randint(2, 9)
    # a x - b >= a*lo - b + 1 -> x >= lo + 1/a -> smallest integer lo+1
    c = a * lo - b + 1
    spr(ALG, S_INEQ, "hard", f"What is the smallest integer value of x for which {a}x − {b} ≥ {c}?", lo + 1,
        f"Add {b}: {a}x ≥ {c + b}. Divide by {a}: x ≥ {Fraction(c + b, a)}. That is a little more than {lo}, so the smallest integer that satisfies it is {lo + 1}.")

# ============================================================ ADVANCED MATH
S_EQ = "Equivalent expressions"
for _ in range(3):
    a, b = R.choice([-6, -5, -4, -3, -2, 2, 3, 4, 5, 6]), R.choice([-7, -5, -3, -2, 2, 3, 5, 7])
    while a == b or a == -b: b = R.choice([-7, -5, -3, -2, 2, 3, 5, 7])
    s, p = a + b, a * b
    lin = lambda k: (f"x² {sgn(k)}x" if abs(k) != 1 else (f"x² + x" if k == 1 else "x² − x")) if k else "x²"
    mc(ADV, S_EQ, "easy", f"Which expression is equivalent to (x {sgn(a)})(x {sgn(b)})?", f"{lin(s)} {sgn(p)}",
       [f"{lin(s)} {sgn(-p)}", f"{lin(-s)} {sgn(p)}", f"x² {sgn(p)}"],
       f"Multiply each term: x·x = x², x·({b}) + ({a})·x = {s}x, and ({a})({b}) = {p}. So the product is {lin(s)} {sgn(p)}. Sign slips on the middle or last term produce the wrong choices, and dropping the middle term entirely gives x² {sgn(p)}.")
for _ in range(2):
    a, b = R.choice([2, 3, 4, 5, 6]), R.choice([-7, -5, -3, -2, -1])
    while a == -b: b = R.choice([-7, -5, -3, -2, -1])
    s, p = a + b, a * b
    mc(ADV, S_EQ, "medium", f"Which of the following is a factor of x² {sgn(s)}x {sgn(p)}?", f"x {sgn(b)}",
       [f"x {sgn(-b)}", f"x {sgn(-a)}", f"x {sgn(s)}"],
       f"Look for two numbers that multiply to {p} and add to {s}: {a} and {b}. So x² {sgn(s)}x {sgn(p)} = (x {sgn(a)})(x {sgn(b)}), and x {sgn(b)} is a factor.")
for _ in range(2):
    a = R.choice([2, 3, 4, 5, 6, 7])
    mc(ADV, S_EQ, "hard", f"For x ≠ {a}, which expression is equivalent to (x² − {a*a}) / (x − {a})?", f"x + {a}",
       [f"x − {a}", f"x + {a*a}", f"x² + {a}"],
       f"x² − {a*a} is a difference of squares: (x − {a})(x + {a}). Dividing by x − {a} leaves x + {a}.")

S_NL1 = "Nonlinear equations in one variable"
for _ in range(2):
    r = R.randint(3, 12)
    spr(ADV, S_NL1, "easy", f"If x² = {r*r} and x > 0, what is the value of x?", r,
        f"The positive square root of {r*r} is {r}.")
for _ in range(3):
    r1, r2 = R.randint(1, 6), R.randint(7, 12); s, p = r1 + r2, r1 * r2
    mc(ADV, S_NL1, "medium", f"What is the sum of the solutions to x² − {s}x + {p} = 0?", s,
       [p, -s, r2],
       f"Factor: (x − {r1})(x − {r2}) = 0, so the solutions are {r1} and {r2}, and their sum is {s}. (Shortcut: for x² + bx + c = 0 the solutions sum to −b.) The product of the solutions is {p}, not the sum.")
for _ in range(2):
    h = R.randint(2, 9); b = 2 * h; c = h * h
    spr(ADV, S_NL1, "hard", f"The equation x² − {b}x + c = 0 has exactly one real solution. What is the value of c?", c,
        f"One real solution means the discriminant is zero: b² − 4ac = {b}² − 4c = 0, so c = {b*b}/4 = {c}. Check: x² − {b}x + {c} = (x − {h})².")

S_NLF = "Nonlinear functions"
for _ in range(2):
    p0 = R.choice([2000, 5000, 12000, 800, 1500]); r = R.choice([3, 4, 6, 8, 12])
    mc(ADV, S_NLF, "easy", f"A colony of bacteria starts with {p0:,} cells and grows by {r}% each hour. Which function models the number of cells N(t) after t hours?",
       f"N(t) = {p0:,}(1.{r:02d})ᵗ", [f"N(t) = {p0:,}(0.{r:02d})ᵗ", f"N(t) = {p0:,} + {r}t", f"N(t) = {p0:,}({r})ᵗ"],
       f"A {r}% increase per hour multiplies the count by 1.{r:02d} each hour, so after t hours it is {p0:,} × 1.{r:02d}ᵗ. Multiplying by 0.{r:02d} would shrink it, adding {r}t is linear growth, and multiplying by {r} is {r*100}% growth.")
for _ in range(3):
    h = R.randint(1, 6); k = R.randint(-5, 9); b = 2 * h; c = h * h + k
    mc(ADV, S_NLF, "medium", f"The function f is defined by f(x) = x² − {b}x {sgn(c)}. What is the minimum value of f(x)?", k,
       [h, c, -k if k else 1],
       f"The parabola opens upward, so the minimum is at the vertex, x = −b/(2a) = {b}/2 = {h}. Then f({h}) = {h*h} − {b*h} {sgn(c)} = {k}. The x-coordinate {h} and the constant term {c} are the tempting wrong answers.")
for _ in range(2):
    m0 = R.choice([160, 320, 640, 800, 1200]); hl = R.choice([3, 5, 6, 8]); n = R.randint(2, 4)
    spr(ADV, S_NLF, "hard", f"A sample of a radioactive substance has a mass of {m0} grams and a half-life of {hl} years. What will its mass be, in grams, after {hl*n} years?", Fraction(m0, 2**n),
        f"{hl*n} years is {n} half-lives. Each half-life halves the mass: {m0} → " + " → ".join(fmt(Fraction(m0, 2**i)) for i in range(1, n+1)) + f". After {n} halvings the mass is {fmt(Fraction(m0, 2**n))} grams.")

S_NLS = "Systems of equations in two variables"
for _ in range(2):
    m = R.choice([2, 3, 4, 5, 6])
    mc(ADV, S_NLS, "medium", f"In the xy-plane, the graphs of y = x² and y = {m}x intersect at two points. What is the sum of the x-coordinates of the two points?", m,
       [0, m*m, -m],
       f"Set the expressions equal: x² = {m}x, so x² − {m}x = 0 and x(x − {m}) = 0. The x-coordinates are 0 and {m}, which sum to {m}.")
for _ in range(2):
    c = R.randint(1, 6); k = c + R.randint(1, 9); n = 2
    mc(ADV, S_NLS, "hard", f"How many points of intersection do the graphs of y = x² + {c} and y = {k} have in the xy-plane?", 2,
       [0, 1, 4],
       f"Set x² + {c} = {k}, so x² = {k - c}. Since {k - c} is positive, x = ±√{k - c}: two solutions, so two intersection points. There would be one if {k} equaled {c} (the vertex) and none if {k} were less than {c}.")

# ============================================================ PSDA
S_RATE = "Ratios, rates, proportional relationships, and units"
for _ in range(3):
    a, b = R.choice([(3, 2), (5, 3), (4, 3), (7, 4), (2, 5)]); k = R.randint(3, 8)
    spr(PSDA, S_RATE, "easy", f"A paint mixture uses {a} parts blue for every {b} parts white. How many parts blue are needed for {b*k} parts white?", a*k,
        f"{b*k} parts white is {k} times the {b} in the ratio, so the blue must be {k} times {a}: {a*k}. Equivalently, {a}/{b} = x/{b*k} gives x = {a*k}.")
for _ in range(3):
    mph = R.choice([45, 54, 60, 72, 90]); minutes = R.choice([20, 30, 40, 50])
    dist = Fraction(mph * minutes, 60)
    mc(PSDA, S_RATE, "medium", f"A train travels at a constant speed of {mph} miles per hour. How many miles does it travel in {minutes} minutes?", fmt(dist),
       [mph * minutes, fmt(Fraction(mph, minutes)), fmt(dist * 2)],
       f"Convert minutes to hours: {minutes} minutes = {Fraction(minutes, 60)} hour. Distance = {mph} × {Fraction(minutes, 60)} = {fmt(dist)} miles. Multiplying by {minutes} without converting gives {mph*minutes}, which is far too large.")
for _ in range(2):
    a, b = R.choice([(2, 3), (3, 4), (1, 4), (3, 5)]); total = (a + b) * R.randint(4, 12)
    mc(PSDA, S_RATE, "hard", f"A {total}-milliliter solution is made of alcohol and water in the ratio {a} : {b}. How many milliliters of alcohol does it contain?", total * a // (a + b),
       [total * b // (a + b), Fraction(total, a) if total % a else total // a, total // (a + b)],
       f"The ratio has {a + b} parts in all, so each part is {total}/{a + b} = {total // (a + b)} mL. Alcohol is {a} parts: {a} × {total // (a + b)} = {total * a // (a + b)} mL. ({total * b // (a + b)} mL is the water.)")

S_PCT = "Percentages"
for _ in range(3):
    pct = R.choice([15, 20, 25, 30, 40]); base = R.choice([60, 80, 120, 150, 240])
    while (base * pct) % 100: base = R.choice([60, 80, 120, 150, 240])
    mc(PSDA, S_PCT, "easy", f"A pair of shoes regularly priced at ${base} is on sale for {pct}% off. What is the sale price?", f"${base - base*pct//100}",
       [f"${base*pct//100}", f"${base + base*pct//100}", f"${base - pct}"],
       f"{pct}% of ${base} is ${base*pct//100}, so the sale price is ${base} − ${base*pct//100} = ${base - base*pct//100}. ${base*pct//100} is the discount itself, and subtracting {pct} dollars instead of {pct} percent is a common slip.")
for _ in range(3):
    old = R.choice([40, 50, 80, 120, 200]); pct = R.choice([10, 15, 20, 25, 50])
    while (old * pct) % 100: old = R.choice([40, 50, 80, 120, 200])
    new = old + old*pct//100
    mc(PSDA, S_PCT, "medium", f"The number of students in a club increased from {old} to {new}. By what percent did the membership increase?", f"{pct}%",
       [f"{round(100*(new-old)/new)}%", f"{new-old}%", f"{round(100*new/old)}%"],
       f"Percent increase = (change) / (original) × 100 = ({new} − {old}) / {old} × 100 = {new-old}/{old} × 100 = {pct}%. Dividing by the new value instead of the original gives {round(100*(new-old)/new)}%.")
for _ in range(2):
    pct = R.choice([20, 25, 40]); sale = R.choice([48, 60, 72, 90, 120]); orig = Fraction(sale * 100, 100 - pct)
    if orig.denominator != 1: sale = 60; pct = 25; orig = Fraction(80)
    mc(PSDA, S_PCT, "hard", f"After a {pct}% discount, a jacket costs ${sale}. What was the original price of the jacket?", f"${fmt(orig)}",
       [f"${sale + sale*pct//100}", f"${sale + pct}", f"${fmt(Fraction(sale*100, 100+pct)) if Fraction(sale*100,100+pct).denominator==1 else sale - pct}"],
       f"A {pct}% discount leaves {100-pct}% of the original: 0.{100-pct} × original = {sale}, so original = {sale} / 0.{100-pct} = ${fmt(orig)}. Adding {pct}% to the sale price (${sale + sale*pct//100}) is wrong because {pct}% of the smaller sale price is less than {pct}% of the original.")

S_1V = "One-variable data: distributions and measures of center and spread"
for _ in range(2):
    xs = sorted(R.sample(range(60, 100), 5)); s = sum(xs)
    while s % 5: xs[-1] += 1; s = sum(xs)
    spr(PSDA, S_1V, "easy", f"A student's scores on five quizzes were {', '.join(map(str, xs[:-1]))}, and {xs[-1]}. What is the mean of the five scores?", s // 5,
        f"Mean = sum ÷ count = {s} ÷ 5 = {s // 5}.")
for _ in range(2):
    xs = sorted(R.sample(range(10, 50), 6)); med = Fraction(xs[2] + xs[3], 2)
    mc(PSDA, S_1V, "medium", f"The list below shows the number of minutes six students spent on homework one evening.\n\n{', '.join(map(str, R.sample(xs, 6)))}\n\nWhat is the median of the list?", fmt(med),
       [xs[2], xs[3], fmt(Fraction(sum(xs), 6)), xs[1], xs[4]],
       f"Order the values: {', '.join(map(str, xs))}. With six values the median is the average of the third and fourth: ({xs[2]} + {xs[3]}) / 2 = {fmt(med)}. Taking just one of the middle values, or computing the mean ({fmt(Fraction(sum(xs), 6))}), gives a wrong answer.")
for _ in range(2):
    n = R.choice([4, 5, 6, 8]); m1 = R.choice([10, 12, 15, 20]); m2 = m1 + R.choice([1, 2, 3]); x = (n+1)*m2 - n*m1
    mc(PSDA, S_1V, "hard", f"The mean of {n} numbers is {m1}. When one more number is added to the list, the mean of the {n+1} numbers is {m2}. What is the number that was added?", x,
       [m2, m2 + (m2 - m1), n*m2 - n*m1 + m1],
       f"Mean × count = total. The {n} numbers total {n} × {m1} = {n*m1}; the {n+1} numbers total {n+1} × {m2} = {(n+1)*m2}. The added number is the difference: {(n+1)*m2} − {n*m1} = {x}.")

S_2V = "Two-variable data: models and scatterplots"
ctx2 = [("the number of hours a student studies, h", "score on a test, s", "s = {m}h + {b}", "points per hour of study", "points"),
        ("the age of a used car in years, a", "its price in thousands of dollars, p", "p = {b} − {m}a", "thousand dollars per year of age", "thousand dollars"),
        ("the temperature in degrees Celsius, t", "daily ice cream sales, y", "y = {m}t + {b}", "sales per degree", "sales")]
for i in range(3):
    xdesc, ydesc, form, unit, yunit = ctx2[i]; m = R.choice([2.5, 3, 4, 1.5, 6]); b = R.choice([20, 35, 50, 12])
    eq = form.format(m=fmt(m), b=b)
    neg = "−" in form
    mc(PSDA, S_2V, "medium", f"A scatterplot shows the relationship between {xdesc}, and {ydesc}. The line of best fit is {eq}. Which of the following is the best interpretation of the number {fmt(m)} in this equation?",
       f"For each 1-unit increase in the first variable, the model predicts a {'decrease' if neg else 'increase'} of {fmt(m)} in the second.",
       [f"The predicted value of the second variable when the first is 0 is {fmt(m)}.", f"The first variable {'decreases' if neg else 'increases'} by {fmt(m)} for each 1-unit increase in the second.", f"The maximum predicted value of the second variable is {fmt(m)}."],
       f"In a linear model the coefficient of the input variable is the slope: the change in the output for each 1-unit change in the input. {b} is the intercept (the prediction when the input is 0), and the slope does not describe a maximum or run in the other direction.")
for _ in range(2):
    m = R.choice([2, 3, 4, 5]); b = R.choice([10, 15, 25, 40]); x = R.randint(4, 12)
    spr(PSDA, S_2V, "hard", f"The line of best fit for a data set is y = {m}x + {b}. According to the model, what is the predicted value of y when x = {x}?", m*x + b,
        f"Substitute x = {x}: y = {m}({x}) + {b} = {m*x} + {b} = {m*x + b}.")

S_PROB = "Probability and conditional probability"
for _ in range(3):
    r, b, g = R.randint(2, 6), R.randint(2, 6), R.randint(1, 5); t = r + b + g
    want = R.choice(["red", "blue", "not green"])
    num = {"red": r, "blue": b, "not green": r + b}[want]
    mc(PSDA, S_PROB, "easy", f"A jar contains {r} red, {b} blue, and {g} green marbles. If one marble is chosen at random, what is the probability that it is {want}?", fmt(Fraction(num, t)),
       [fmt(Fraction(num, t - num)) if t - num else "1", fmt(Fraction(t - num, t)), fmt(Fraction(num, t + 1)), fmt(Fraction(1, 3)), fmt(Fraction(num + 1, t))],
       f"There are {t} marbles in all and {num} that are {want}, so the probability is {num}/{t} = {fmt(Fraction(num, t))}. Dividing by the number of other marbles instead of the total, or finding the complement, gives the wrong choices.")
for _ in range(3):
    a1, a2, b1, b2 = R.randint(10, 40), R.randint(10, 40), R.randint(10, 40), R.randint(10, 40)
    mc(PSDA, S_PROB, "medium", f"The table shows the results of a survey of {a1+a2+b1+b2} students.\n\n              Plays a sport   No sport\nGrade 10        {a1:<10}       {a2}\nGrade 11        {b1:<10}       {b2}\n\nIf a Grade 10 student is chosen at random, what is the probability that the student plays a sport?", fmt(Fraction(a1, a1 + a2)),
       [fmt(Fraction(a1, a1+a2+b1+b2)), fmt(Fraction(a1, a1 + b1)), fmt(Fraction(a2, a1 + a2))],
       f"The condition \"a Grade 10 student\" restricts attention to that row: {a1 + a2} students. Of those, {a1} play a sport, so the probability is {a1}/{a1+a2} = {fmt(Fraction(a1, a1+a2))}. Dividing by all {a1+a2+b1+b2} students ignores the condition.")

S_INF = "Inference from sample statistics and margin of error"
for _ in range(2):
    n = R.choice([200, 250, 400, 500]); pop = R.choice([2000, 3000, 5000, 8000]); pct = R.choice([15, 20, 30, 35, 40, 60])
    mc(PSDA, S_INF, "medium", f"A random sample of {n} residents of a town with {pop:,} residents found that {pct}% of the sample use the public library at least once a month. Based on the sample, which is the best estimate of the number of residents in the town who use the library at least once a month?", f"{pop*pct//100:,}",
       [f"{n*pct//100:,}", f"{pop - pop*pct//100:,}", f"{pop*pct//10:,}"],
       f"A random sample's proportion is the best estimate for the whole population: {pct}% of {pop:,} = {pop*pct//100:,}. Applying {pct}% to the sample ({n*pct//100}) answers a different question.")
for _ in range(2):
    est = R.choice([42, 55, 63, 70]); moe = R.choice([3, 4, 5])
    mc(PSDA, S_INF, "hard", f"A poll of a random sample of voters estimates that {est}% support a ballot measure, with a margin of error of {moe} percentage points. Which of the following is the most appropriate conclusion?",
       f"It is plausible that between {est-moe}% and {est+moe}% of all voters support the measure.",
       [f"Exactly {est}% of all voters support the measure.", f"{moe}% of the voters polled changed their minds.", f"The poll surveyed {moe}% of all voters."],
       f"A margin of error gives a range of plausible values for the population: {est} ± {moe}, or {est-moe}% to {est+moe}%. It does not make the sample estimate exact, and it says nothing about voters changing their minds or about how many were surveyed.")

S_CLAIM = "Evaluating statistical claims"
mc(PSDA, S_CLAIM, "medium", "A researcher wants to estimate the average number of hours per week that students at a large university spend on homework. Which sampling method is most likely to produce a sample that represents the whole student body?",
   "Selecting 300 students at random from a list of all enrolled students",
   ["Surveying the 300 students who attend a study-skills workshop", "Surveying every student in one large chemistry lecture", "Posting a survey online and using the first 300 responses"],
   "Only random selection from the full list gives every student an equal chance of being chosen. The other methods draw from groups likely to differ from the student body: workshop attendees, one course's students, or people who choose to respond.")
mc(PSDA, S_CLAIM, "hard", "A study found that people who drink coffee every morning score higher on memory tests than people who do not. Which of the following, if true, would most weaken the conclusion that coffee improves memory?",
   "People who drink coffee every morning also sleep more regularly, and regular sleep is known to improve memory.",
   ["The study included more than 1,000 participants.", "The memory tests were scored by researchers who did not know which participants drank coffee.", "Participants who drank coffee reported enjoying it."],
   "The study is observational, so a third factor linked to both coffee drinking and memory could explain the result. Regular sleep is exactly such a factor. A large sample and blind scoring strengthen the study, and enjoyment is irrelevant.")
mc(PSDA, S_CLAIM, "medium", "A school wants to test whether a new tutoring program raises math scores. Which study design would best support a conclusion that the program causes higher scores?",
   "Randomly assign half of the interested students to the program and half to a waiting list, then compare their scores at the end of the term.",
   ["Compare the scores of students who chose to join the program with those who did not.", "Offer the program to the students with the lowest scores and see whether their scores rise.", "Survey students in the program about whether they feel more confident in math."],
   "Random assignment is what allows a causal conclusion, because it makes the two groups alike in everything except the program. Students who choose the program may differ from those who don't, the lowest scorers would likely rise anyway, and confidence is not a score.")

# ============================================================ GEOMETRY
S_AREA = "Area and volume"
for _ in range(3):
    kind = R.choice(["rect", "tri", "sq"])
    if kind == "rect":
        l, w = R.randint(6, 15), R.randint(3, 8)
        mc(GEO, S_AREA, "easy", f"A rectangle has a length of {l} centimeters and a width of {w} centimeters. What is the area of the rectangle, in square centimeters?", l*w, [2*(l+w), l+w, l*w//2],
           f"Area of a rectangle = length × width = {l} × {w} = {l*w}. The perimeter, 2({l} + {w}) = {2*(l+w)}, is a different measure.")
    elif kind == "tri":
        b, h = R.choice([6, 8, 10, 12]), R.randint(3, 9)
        mc(GEO, S_AREA, "easy", f"A triangle has a base of {b} inches and a height of {h} inches. What is the area of the triangle, in square inches?", b*h//2, [b*h, b+h, 2*b*h],
           f"Area of a triangle = ½ × base × height = ½ × {b} × {h} = {b*h//2}. Forgetting the ½ gives {b*h}.")
    else:
        s = R.randint(4, 12)
        mc(GEO, S_AREA, "easy", f"The perimeter of a square is {4*s} meters. What is the area of the square, in square meters?", s*s, [4*s, s, 2*s*s],
           f"Each side is {4*s} ÷ 4 = {s} meters, so the area is {s}² = {s*s} square meters.")
for _ in range(2):
    if R.random() < 0.5:
        l, w, h = R.randint(3, 8), R.randint(3, 8), R.randint(2, 10)
        mc(GEO, S_AREA, "medium", f"A rectangular box has a length of {l} inches, a width of {w} inches, and a height of {h} inches. What is the volume of the box, in cubic inches?", l*w*h, [l*w+h, 2*(l*w+l*h+w*h), l*w],
           f"Volume = length × width × height = {l} × {w} × {h} = {l*w*h}. The surface area, 2({l}·{w} + {l}·{h} + {w}·{h}) = {2*(l*w+l*h+w*h)}, is a different quantity.")
    else:
        r, h = R.randint(2, 6), R.randint(4, 12)
        mc(GEO, S_AREA, "medium", f"A right circular cylinder has a radius of {r} and a height of {h}. What is the volume of the cylinder?", f"{r*r*h}π", [f"{2*r*h}π", f"{r*h}π", f"{r*r*h*2}π", f"{r*r*h//2 if r*r*h%2==0 else r*r*h+r}π", f"{2*r*r*h+1}π"],
           f"Volume of a cylinder = πr²h = π({r}²)({h}) = {r*r*h}π. Using r instead of r² gives {r*h}π.")
for _ in range(2):
    r = R.choice([3, 4, 5, 6, 7, 8])
    spr(GEO, S_AREA, "hard", f"The circumference of a circle is {2*r}π. What is the area of the circle, in terms of π? (Enter the coefficient of π.)", r*r,
        f"Circumference = 2πr = {2*r}π, so r = {r}. Area = πr² = {r*r}π. The answer is the coefficient, {r*r}.")

S_ANG = "Lines, angles, and triangles"
for _ in range(2):
    a = R.randint(25, 70); b = R.randint(30, 80)
    spr(GEO, S_ANG, "easy", f"Two angles of a triangle measure {a}° and {b}°. What is the measure, in degrees, of the third angle?", 180 - a - b,
        f"The angles of a triangle sum to 180°: 180 − {a} − {b} = {180-a-b}.")
for _ in range(2):
    if R.random() < 0.5:
        x = R.choice([35, 48, 57, 62, 71, 115, 124])
        mc(GEO, S_ANG, "medium", f"Two parallel lines are cut by a transversal. One of the angles formed measures {x}°. Which of the following could be the measure of one of the other angles formed?", f"{180-x}°", [f"{90-x if x<90 else x-90}°", f"{x//2}°", f"{360-x}°"],
           f"When parallel lines are cut by a transversal, every angle formed is either equal to {x}° or supplementary to it, 180 − {x} = {180-x}°. None of the other values can occur.")
    else:
        a, b = R.randint(30, 70), R.randint(30, 70)
        mc(GEO, S_ANG, "medium", f"In a triangle, two interior angles measure {a}° and {b}°. What is the measure of the exterior angle at the third vertex?", f"{a+b}°", [f"{180-a-b}°", f"{360-a-b}°", f"{abs(a-b)}°"],
           f"An exterior angle equals the sum of the two remote interior angles: {a} + {b} = {a+b}°. Equivalently, the third interior angle is {180-a-b}°, and its exterior angle is 180 − {180-a-b} = {a+b}°.")
for _ in range(2):
    a, b, k = R.choice([(3, 4, 2), (5, 7, 3), (4, 6, 4), (6, 9, 2), (2, 5, 5)])
    spr(GEO, S_ANG, "hard", f"Triangle ABC is similar to triangle DEF, with AB corresponding to DE. AB = {a}, BC = {b}, and DE = {a*k}. What is the length of EF?", b*k,
        f"Corresponding sides of similar triangles are proportional. The scale factor from ABC to DEF is DE/AB = {a*k}/{a} = {k}, so EF = {k} × BC = {k} × {b} = {b*k}.")

S_RT = "Right triangles and trigonometry"
triples = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15), (7, 24, 25), (12, 16, 20)]
for _ in range(3):
    a, b, c = R.choice(triples)
    if R.random() < 0.6:
        mc(GEO, S_RT, "easy", f"A right triangle has legs of length {a} and {b}. What is the length of the hypotenuse?", c, [a+b, c+1, c-1],
           f"Pythagorean theorem: hypotenuse² = {a}² + {b}² = {a*a} + {b*b} = {c*c}, so the hypotenuse is √{c*c} = {c}.")
    else:
        mc(GEO, S_RT, "easy", f"A right triangle has a hypotenuse of length {c} and one leg of length {a}. What is the length of the other leg?", b, [c-a, c+a, a],
           f"Pythagorean theorem: {a}² + leg² = {c}², so leg² = {c*c} − {a*a} = {b*b} and the leg is {b}. Subtracting the lengths themselves ({c} − {a}) is a common error.")
for _ in range(2):
    a, b, c = R.choice(triples)
    fn = R.choice(["sin", "cos", "tan"]); val = {"sin": Fraction(a, c), "cos": Fraction(b, c), "tan": Fraction(a, b)}[fn]
    mc(GEO, S_RT, "medium", f"In right triangle PQR, the right angle is at Q, PQ = {b}, QR = {a}, and PR = {c}. What is the value of {fn} of angle P?", fmt(val),
       [fmt(Fraction(b, c)), fmt(Fraction(a, c)), fmt(Fraction(a, b)), fmt(Fraction(b, a)), fmt(Fraction(c, a))],
       f"For angle P, the opposite side is QR = {a}, the adjacent side is PQ = {b}, and the hypotenuse is PR = {c}. {fn} P = " + {"sin": f"opposite/hypotenuse = {a}/{c}", "cos": f"adjacent/hypotenuse = {b}/{c}", "tan": f"opposite/adjacent = {a}/{b}"}[fn] + f" = {fmt(val)}.")
for _ in range(2):
    a, b, c = R.choice(triples)
    spr(GEO, S_RT, "hard", f"In a right triangle, one of the acute angles has a sine of {a}/{c}. What is the cosine of the same angle? (Enter a fraction.)", Fraction(b, c),
        f"sin = opposite/hypotenuse = {a}/{c}, so the opposite leg is {a} (up to scale) and the hypotenuse is {c}. The adjacent leg is √({c}² − {a}²) = {b}, so cos = adjacent/hypotenuse = {b}/{c}.")

S_CIRC = "Circles"
for _ in range(2):
    r = R.randint(2, 9)
    if R.random() < 0.5:
        mc(GEO, S_CIRC, "easy", f"A circle has a radius of {r}. What is its circumference?", f"{2*r}π", [f"{r}π", f"{r*r}π", f"{4*r}π"],
           f"Circumference = 2πr = 2π({r}) = {2*r}π. {r*r}π is the area.")
    else:
        mc(GEO, S_CIRC, "easy", f"A circle has a diameter of {2*r}. What is its area?", f"{r*r}π", [f"{4*r*r}π", f"{2*r}π", f"{r}π"],
           f"The radius is half the diameter, {r}. Area = πr² = {r*r}π. Using the diameter in place of the radius gives {4*r*r}π.")
for _ in range(2):
    h, k, r = R.randint(-6, 6), R.randint(-6, 6), R.randint(2, 7)
    mc(GEO, S_CIRC, "medium", f"Which equation represents a circle in the xy-plane with center ({h}, {k}) and radius {r}?", f"(x {sgn(-h)})² + (y {sgn(-k)})² = {r*r}",
       [f"(x {sgn(h)})² + (y {sgn(k)})² = {r*r}", f"(x {sgn(-h)})² + (y {sgn(-k)})² = {r}", f"(x {sgn(-h)})² − (y {sgn(-k)})² = {r*r}"],
       f"A circle with center (h, k) and radius r has equation (x − h)² + (y − k)² = r². With h = {h}, k = {k}, r = {r}: (x {sgn(-h)})² + (y {sgn(-k)})² = {r*r}. Watch the signs inside the parentheses and remember the right side is r², not r.")
for _ in range(2):
    h, k, r = R.choice([1, 2, 3, 4]), R.choice([1, 2, 3, 5]), R.choice([3, 4, 5, 6])
    sh, sk = R.choice([1, -1]), R.choice([1, -1]); h *= sh; k *= sk
    c = r*r - h*h - k*k
    mc(GEO, S_CIRC, "hard", f"A circle in the xy-plane has the equation x² + y² {sgn(-2*h)}x {sgn(-2*k)}y = {c}. What is the radius of the circle?", r, [r*r, abs(c), r*r - h*h],
       f"Complete the square: x² {sgn(-2*h)}x becomes (x {sgn(-h)})² − {h*h}, and y² {sgn(-2*k)}y becomes (y {sgn(-k)})² − {k*k}. So (x {sgn(-h)})² + (y {sgn(-k)})² = {c} + {h*h} + {k*k} = {r*r}, and the radius is √{r*r} = {r}. {r*r} is the radius squared.")

# ============================================================ write
p = sys.argv[1]
d = json.load(io.open(p, encoding="utf-8"))
d["questions"] = [q for q in d["questions"] if not (q["section"] == "math" and int(q["id"].split("-")[1]) >= 25)]
d["questions"].extend(OUT)
io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
from collections import Counter
print(len(OUT), "math generated; bank total", len(d["questions"]))
print(Counter(q["difficulty"] for q in OUT))
