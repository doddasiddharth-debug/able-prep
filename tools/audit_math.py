"""Independent check of generated math keys.

For every item whose stem opens with one or two equations, the key is
substituted back (for systems, the solution is found by brute force over
small rationals and compared with the key). Items with no parseable
equation are counted as needing a human read-through.
Usage: python3 tools/gen_math.py | python3 tools/audit_math.py
"""
import json, re, sys
from fractions import Fraction
from math import sqrt

def to_py(expr):
    e = expr.replace("−", "-").replace("²", "**2").replace("³", "**3").replace("√", "SQRT")
    e = re.sub(r"(\d)\s*\(", r"\1*(", e)          # 3(x + 2)
    e = re.sub(r"(\d)([a-z])", r"\1*\2", e)        # 3x
    e = re.sub(r"\)\s*\(", ")*(", e)               # (x-1)(x+2)
    e = re.sub(r"\)([a-z])", r")*\1", e)
    e = re.sub(r"(?<![A-Z])([a-z])\(", r"\1*(", e) # x(x+1) but not SQRT(
    return e.replace("^", "**").replace("SQRT", "sqrt")

def ev(expr, env):
    return eval(to_py(expr), {"sqrt": sqrt, "__builtins__": {}}, dict(env))

def val(s):
    try: return Fraction(s.replace("−", "-"))
    except Exception: return None

def balances(eqs, env):
    return all(abs(Fraction(ev(l.split("=")[0], env)) - Fraction(ev(l.split("=")[1], env))) < Fraction(1, 10**9) for l in eqs)

items = json.load(sys.stdin)
checked = failed = unchecked = 0
GRID = [Fraction(n, d) for n in range(-30, 31) for d in (1, 2, 3)]
for q in items:
    lines = q["stem"].split("\n")
    eqs = [l for l in lines[:3] if l.count("=") == 1 and re.fullmatch(r"[\s0-9a-z+\-−*/().²³√^=]+", l)]
    tail = lines[-1]
    key = q["answer"] if q.get("type") == "spr" else q["choices"][q["answer"]]
    k = val(key)
    ok = None
    try:
        m = re.match(r"\(\s*(-?[\d/−.]+)\s*,\s*(-?[\d/−.]+)\s*\)", key)
        if eqs and m and len(eqs) == 2:
            ok = balances(eqs, {"x": val(m.group(1)), "y": val(m.group(2))})
        elif eqs and k is not None and len(eqs) == 1 and any(t in tail for t in ("value of x", "solution to the given equation", "positive solution")):
            ok = balances(eqs, {"x": k})
        elif eqs and k is not None and len(eqs) == 1 and "passes through" in tail and "value of k" in tail:
            mm = re.search(r"\((\d+), k\)", tail)
            if mm: ok = balances(eqs, {"x": Fraction(mm.group(1)), "y": k})
        elif eqs and k is not None and len(eqs) == 2:
            sols = [(x, y) for x in GRID for y in GRID if balances(eqs, {"x": x, "y": y})]
            if "x > 0" in tail: sols = [p for p in sols if p[0] > 0]
            want = (lambda p: p[0] + p[1]) if "x + y" in tail else (lambda p: p[1]) if "value of y" in tail else (lambda p: p[0])
            if sols: ok = all(want(p) == k for p in sols)
    except Exception as e:
        print("ERR", q["id"], eqs, e)
    if ok is True: checked += 1
    elif ok is False: failed += 1; print("FAIL", q["id"], eqs, key)
    else: unchecked += 1
print(f"balanced: {checked}  failed: {failed}  needs human read: {unchecked}")
sys.exit(1 if failed else 0)
