"""
Tests with processing (simplification, CNF, DNF) of random complex expressions
with 15-30 variables. Uses fixed seeds for reproducibility.
"""

import random

import pytest

from pyeda.boolalg.bfarray import exprvars
from pyeda.boolalg.expr import (
    And,
    Implies,
    Not,
    One,
    Or,
    Xor,
    Zero,
    expr2dimacscnf,
    exprvar,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vars(n):
    """Create n expression variables."""
    return exprvars("x", n)


def _random_literal(rng, variables):
    """Return a random literal (variable or its complement)."""
    v = rng.choice(variables)
    return ~v if rng.random() < 0.5 else v


def _random_clause(rng, variables, min_width=2, max_width=5):
    """Return a random OR-clause (disjunction of literals)."""
    width = rng.randint(min_width, max_width)
    lits = [_random_literal(rng, variables) for _ in range(width)]
    return Or(*lits)


def _random_cube(rng, variables, min_width=2, max_width=5):
    """Return a random AND-cube (conjunction of literals)."""
    width = rng.randint(min_width, max_width)
    lits = [_random_literal(rng, variables) for _ in range(width)]
    return And(*lits)


def _random_cnf(rng, variables, num_clauses, clause_width=(2, 5)):
    """Return a random CNF (conjunction of OR-clauses)."""
    clauses = [_random_clause(rng, variables, *clause_width)
               for _ in range(num_clauses)]
    return And(*clauses)


def _random_dnf(rng, variables, num_cubes, cube_width=(2, 5)):
    """Return a random DNF (disjunction of AND-cubes)."""
    cubes = [_random_cube(rng, variables, *cube_width)
             for _ in range(num_cubes)]
    return Or(*cubes)


def _random_nested_expr(rng, variables, depth=3, breadth=3):
    """Build a random nested expression tree."""
    if depth == 0:
        return _random_literal(rng, variables)
    ops = [And, Or, Xor]
    op = rng.choice(ops)
    children = [_random_nested_expr(rng, variables, depth - 1, breadth)
                for _ in range(rng.randint(2, breadth))]
    return op(*children)


# ===========================================================================
# Simplification of random expressions (15-30 vars)
# ===========================================================================

class TestRandomSimplify:
    """Simplification of random complex expressions."""

    @pytest.mark.parametrize("seed", range(10))
    def test_simplify_random_cnf_20vars(self, seed):
        """Simplify random CNF with 20 variables, 30 clauses."""
        rng = random.Random(seed)
        variables = _make_vars(20)
        f = _random_cnf(rng, variables, num_clauses=30)
        s = f.simplify()
        assert s.equivalent(f)

    @pytest.mark.parametrize("seed", range(10))
    def test_simplify_random_dnf_20vars(self, seed):
        """Simplify random DNF with 20 variables, 15 cubes."""
        rng = random.Random(100 + seed)
        variables = _make_vars(20)
        f = _random_dnf(rng, variables, num_cubes=15)
        s = f.simplify()
        assert s.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_simplify_random_nested_25vars(self, seed):
        """Simplify random nested expression with 25 variables, depth 4."""
        rng = random.Random(200 + seed)
        variables = _make_vars(25)
        f = _random_nested_expr(rng, variables, depth=4, breadth=3)
        s = f.simplify()
        assert s.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_simplify_random_nested_30vars(self, seed):
        """Simplify random nested expression with 30 variables, depth 3."""
        rng = random.Random(300 + seed)
        variables = _make_vars(30)
        f = _random_nested_expr(rng, variables, depth=3, breadth=4)
        s = f.simplify()
        assert s.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_simplify_with_redundancy_20vars(self, seed):
        """Simplify expression with injected redundancy (a | ~a terms)."""
        rng = random.Random(400 + seed)
        variables = _make_vars(20)
        # Build base expression
        f = _random_cnf(rng, variables, num_clauses=10, clause_width=(3, 4))
        # Inject tautological clauses
        tautologies = [Or(v, ~v) for v in rng.sample(list(variables), 5)]
        bloated = And(f, *tautologies)
        s = bloated.simplify()
        assert s.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_simplify_with_contradictions_15vars(self, seed):
        """Expression with contradiction sub-expressions simplify to Zero."""
        rng = random.Random(500 + seed)
        variables = _make_vars(15)
        v = rng.choice(variables)
        # f & v & ~v => Zero
        f = _random_cnf(rng, variables, num_clauses=5)
        contradicted = And(f, v, ~v)
        s = contradicted.simplify()
        assert s is Zero


# ===========================================================================
# CNF conversion of random expressions (15-30 vars)
# ===========================================================================

class TestRandomToCNF:
    """CNF conversion of random complex expressions."""

    @pytest.mark.parametrize("seed", range(10))
    def test_random_dnf_to_cnf_15vars(self, seed):
        """Convert random DNF (15 vars, 6 cubes) to CNF."""
        rng = random.Random(600 + seed)
        variables = _make_vars(15)
        f = _random_dnf(rng, variables, num_cubes=6, cube_width=(2, 4))
        cnf = f.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(10))
    def test_random_nested_to_cnf_15vars(self, seed):
        """Convert random nested expression (15 vars, depth 3) to CNF."""
        rng = random.Random(700 + seed)
        variables = _make_vars(15)
        f = _random_nested_expr(rng, variables, depth=3, breadth=2)
        cnf = f.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_random_xor_mix_to_cnf_18vars(self, seed):
        """Convert XOR-heavy expression (18 vars) to CNF."""
        rng = random.Random(800 + seed)
        variables = _make_vars(18)
        # Mix XOR and AND/OR
        parts = []
        for _ in range(4):
            v1, v2, v3 = rng.sample(list(variables), 3)
            parts.append(Xor(v1, v2, v3))
        f = And(*parts)
        cnf = f.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_random_implies_chain_to_cnf_20vars(self, seed):
        """Convert chain of implications (20 vars) to CNF."""
        rng = random.Random(900 + seed)
        variables = _make_vars(20)
        shuffled = list(variables)
        rng.shuffle(shuffled)
        # Build implication chain: v0 => v1 => v2 => ... => v9
        implications = [Implies(shuffled[i], shuffled[i+1])
                        for i in range(10)]
        f = And(*implications)
        cnf = f.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_cnf_of_cnf_is_stable_25vars(self, seed):
        """CNF of an already-CNF expression should be stable."""
        rng = random.Random(1000 + seed)
        variables = _make_vars(25)
        f = _random_cnf(rng, variables, num_clauses=20, clause_width=(3, 5))
        assert f.is_cnf()
        cnf = f.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)


# ===========================================================================
# DNF conversion of random expressions (15-30 vars)
# ===========================================================================

class TestRandomToDNF:
    """DNF conversion of random complex expressions."""

    @pytest.mark.parametrize("seed", range(10))
    def test_random_cnf_to_dnf_15vars(self, seed):
        """Convert random CNF (15 vars, 5 clauses) to DNF."""
        rng = random.Random(1100 + seed)
        variables = _make_vars(15)
        # Keep clause count low to avoid exponential DNF blowup
        f = _random_cnf(rng, variables, num_clauses=5, clause_width=(2, 3))
        dnf = f.to_dnf()
        assert dnf.is_dnf()
        assert dnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(10))
    def test_random_nested_to_dnf_15vars(self, seed):
        """Convert random nested expression (15 vars, depth 2) to DNF."""
        rng = random.Random(1200 + seed)
        variables = _make_vars(15)
        f = _random_nested_expr(rng, variables, depth=2, breadth=3)
        dnf = f.to_dnf()
        assert dnf.is_dnf()
        assert dnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_dnf_of_dnf_is_stable_20vars(self, seed):
        """DNF of an already-DNF expression should be stable."""
        rng = random.Random(1300 + seed)
        variables = _make_vars(20)
        f = _random_dnf(rng, variables, num_cubes=10, cube_width=(3, 5))
        assert f.is_dnf()
        dnf = f.to_dnf()
        assert dnf.is_dnf()
        assert dnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_xor_pairs_to_dnf_16vars(self, seed):
        """XOR pairs combined with AND, converted to DNF (16 vars)."""
        rng = random.Random(1400 + seed)
        variables = _make_vars(16)
        pairs = [(variables[i], variables[i+1]) for i in range(0, 16, 2)]
        rng.shuffle(pairs)
        # AND of 4 XOR-pairs -> 2^4 = 16 minterms
        xors = [Xor(a, b) for a, b in pairs[:4]]
        f = And(*xors)
        dnf = f.to_dnf()
        assert dnf.is_dnf()
        assert dnf.equivalent(f)


# ===========================================================================
# Tseitin encoding of random expressions (20-30 vars)
# ===========================================================================

class TestRandomTseitin:
    """Tseitin CNF encoding for large random expressions."""

    @pytest.mark.parametrize("seed", range(10))
    def test_tseitin_random_nested_20vars(self, seed):
        """Tseitin encode a random nested expression (20 vars, depth 4)."""
        rng = random.Random(1500 + seed)
        variables = _make_vars(20)
        f = _random_nested_expr(rng, variables, depth=4, breadth=3)
        t = f.tseitin()
        assert t.is_cnf()
        # Equisatisfiable: if f is SAT, then t is SAT
        f_soln = f.satisfy_one()
        if f_soln is not None:
            t_soln = t.satisfy_one()
            assert t_soln is not None

    @pytest.mark.parametrize("seed", range(5))
    def test_tseitin_random_nested_30vars(self, seed):
        """Tseitin encode a random nested expression (30 vars, depth 3)."""
        rng = random.Random(1600 + seed)
        variables = _make_vars(30)
        f = _random_nested_expr(rng, variables, depth=3, breadth=3)
        t = f.tseitin()
        assert t.is_cnf()
        f_soln = f.satisfy_one()
        if f_soln is not None:
            t_soln = t.satisfy_one()
            assert t_soln is not None

    @pytest.mark.parametrize("seed", range(5))
    def test_tseitin_deep_xor_chain_20vars(self, seed):
        """Tseitin encode deep XOR chains (20 vars)."""
        rng = random.Random(1700 + seed)
        variables = _make_vars(20)
        shuffled = list(variables)
        rng.shuffle(shuffled)
        # XOR of 8 random variables
        f = Xor(*shuffled[:8])
        t = f.tseitin()
        assert t.is_cnf()
        # XOR of 8 vars always has solutions
        assert t.satisfy_one() is not None


# ===========================================================================
# SAT solving on random CNF (15-30 vars)
# ===========================================================================

class TestRandomSAT:
    """SAT solving on random formulas with many variables."""

    @pytest.mark.parametrize("seed", range(10))
    def test_sat_random_cnf_20vars_satisfiable(self, seed):
        """Random satisfiable CNF (20 vars, moderate clause/var ratio)."""
        rng = random.Random(1800 + seed)
        variables = _make_vars(20)
        # Clause/var ratio ~2 is typically satisfiable for 3-SAT
        f = _random_cnf(rng, variables, num_clauses=40, clause_width=(3, 3))
        soln = f.satisfy_one()
        if soln is not None:
            assert f.restrict(soln) is One

    @pytest.mark.parametrize("seed", range(10))
    def test_sat_random_cnf_25vars(self, seed):
        """Random CNF (25 vars, 50 clauses of width 3)."""
        rng = random.Random(1900 + seed)
        variables = _make_vars(25)
        f = _random_cnf(rng, variables, num_clauses=50, clause_width=(3, 3))
        soln = f.satisfy_one()
        if soln is not None:
            assert f.restrict(soln) is One

    @pytest.mark.parametrize("seed", range(5))
    def test_sat_random_cnf_30vars(self, seed):
        """Random CNF (30 vars, 60 clauses of width 3)."""
        rng = random.Random(2000 + seed)
        variables = _make_vars(30)
        f = _random_cnf(rng, variables, num_clauses=60, clause_width=(3, 3))
        soln = f.satisfy_one()
        if soln is not None:
            assert f.restrict(soln) is One

    @pytest.mark.parametrize("seed", range(5))
    def test_sat_via_dimacs_20vars(self, seed):
        """Solve random CNF via DIMACS encoding (20 vars)."""
        rng = random.Random(2100 + seed)
        variables = _make_vars(20)
        f = _random_cnf(rng, variables, num_clauses=40, clause_width=(3, 3))
        cnf_expr = f.to_cnf()
        litmap, dimacs = expr2dimacscnf(cnf_expr)
        soln = dimacs.satisfy_one()
        if soln is not None:
            point = dimacs.soln2point(soln, litmap)
            assert f.restrict(point) is One

    @pytest.mark.parametrize("seed", range(5))
    def test_sat_all_solutions_15vars_sparse(self, seed):
        """Enumerate all solutions of a sparse random CNF (15 vars)."""
        rng = random.Random(2200 + seed)
        variables = _make_vars(15)
        # Sparse CNF: few clauses, many solutions
        f = _random_cnf(rng, variables, num_clauses=8, clause_width=(3, 3))
        solutions = list(f.satisfy_all())
        # Verify each solution
        for soln in solutions:
            assert f.restrict(soln) is One
        # Cross-check count
        assert len(solutions) == f.satisfy_count()

    @pytest.mark.parametrize("seed", range(5))
    def test_unsat_random_cnf_15vars(self, seed):
        """Likely unsatisfiable CNF (15 vars, high clause/var ratio)."""
        rng = random.Random(2300 + seed)
        variables = _make_vars(15)
        # High clause/var ratio ~10 is typically UNSAT for 3-SAT
        f = _random_cnf(rng, variables, num_clauses=150, clause_width=(3, 3))
        soln = f.satisfy_one()
        # Whether SAT or UNSAT, the result should be consistent
        if soln is None:
            assert f.satisfy_count() == 0
        else:
            assert f.restrict(soln) is One


# ===========================================================================
# Combined processing pipelines (simplify -> CNF/DNF -> SAT)
# ===========================================================================

class TestRandomPipeline:
    """End-to-end processing pipelines on random expressions."""

    @pytest.mark.parametrize("seed", range(10))
    def test_simplify_then_cnf_then_sat_20vars(self, seed):
        """Simplify -> to_cnf -> satisfy_one pipeline (20 vars)."""
        rng = random.Random(2400 + seed)
        variables = _make_vars(20)
        f = _random_nested_expr(rng, variables, depth=3, breadth=3)
        simplified = f.simplify()
        assert simplified.equivalent(f)
        cnf = simplified.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)
        soln = cnf.satisfy_one()
        if soln is not None:
            assert f.restrict(soln) is One

    @pytest.mark.parametrize("seed", range(5))
    def test_simplify_then_tseitin_then_sat_25vars(self, seed):
        """Simplify -> Tseitin -> satisfy_one pipeline (25 vars)."""
        rng = random.Random(2500 + seed)
        variables = _make_vars(25)
        f = _random_nested_expr(rng, variables, depth=4, breadth=2)
        simplified = f.simplify()
        t = simplified.tseitin()
        assert t.is_cnf()
        f_soln = f.satisfy_one()
        t_soln = t.satisfy_one()
        # Equisatisfiable
        if f_soln is not None:
            assert t_soln is not None
        if t_soln is None:
            assert f_soln is None

    @pytest.mark.parametrize("seed", range(5))
    def test_dnf_then_simplify_15vars(self, seed):
        """to_dnf -> simplify pipeline (15 vars)."""
        rng = random.Random(2600 + seed)
        variables = _make_vars(15)
        # Small CNF to keep DNF conversion tractable
        f = _random_cnf(rng, variables, num_clauses=4, clause_width=(2, 3))
        dnf = f.to_dnf()
        assert dnf.is_dnf()
        simplified = dnf.simplify()
        assert simplified.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_cnf_simplify_equivalence_20vars(self, seed):
        """Verify simplify(to_cnf(f)) is equivalent to f (20 vars)."""
        rng = random.Random(2700 + seed)
        variables = _make_vars(20)
        f = _random_nested_expr(rng, variables, depth=3, breadth=2)
        cnf = f.to_cnf()
        simplified_cnf = cnf.simplify()
        assert simplified_cnf.equivalent(f)

    @pytest.mark.parametrize("seed", range(5))
    def test_restrict_then_simplify_20vars(self, seed):
        """Partially restrict, then simplify (20 vars)."""
        rng = random.Random(2800 + seed)
        variables = _make_vars(20)
        f = _random_cnf(rng, variables, num_clauses=15, clause_width=(3, 4))
        # Fix first 5 variables to random values
        point = {variables[i]: rng.randint(0, 1) for i in range(5)}
        restricted = f.restrict(point)
        simplified = restricted.simplify()
        # The simplified restricted form should be equivalent to restriction
        assert simplified.equivalent(restricted)
        # And if satisfiable, solution should satisfy original under the point
        soln = simplified.satisfy_one()
        if soln is not None:
            full_point = {**point, **soln}
            assert f.restrict(full_point) is One


# ===========================================================================
# Stress: large variable count, structure preservation
# ===========================================================================

class TestRandomStress:
    """Stress tests on larger variable counts."""

    def test_30var_cnf_simplify_sat(self):
        """30-variable random CNF: simplify and solve."""
        rng = random.Random(3000)
        variables = _make_vars(30)
        f = _random_cnf(rng, variables, num_clauses=80, clause_width=(3, 4))
        s = f.simplify()
        assert s.equivalent(f)
        soln = s.satisfy_one()
        if soln is not None:
            assert f.restrict(soln) is One

    def test_20var_deep_nested_simplify(self):
        """20-variable deeply nested (depth 5) expression: simplify."""
        rng = random.Random(3001)
        variables = _make_vars(20)
        f = _random_nested_expr(rng, variables, depth=5, breadth=2)
        s = f.simplify()
        assert s.equivalent(f)

    def test_25var_mixed_ops_cnf(self):
        """25-variable expression mixing AND/OR/XOR/Implies: to_cnf."""
        rng = random.Random(3002)
        variables = _make_vars(25)
        parts = []
        for _ in range(5):
            v1, v2, v3 = rng.sample(list(variables), 3)
            parts.append(Xor(v1, v2))
        for _ in range(5):
            v1, v2 = rng.sample(list(variables), 2)
            parts.append(Implies(v1, v2))
        for _ in range(5):
            vs = rng.sample(list(variables), 3)
            parts.append(Or(*vs))
        f = And(*parts)
        cnf = f.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)

    def test_15var_many_xors_dnf(self):
        """15-variable expression with XOR pairs: to_dnf."""
        rng = random.Random(3003)
        variables = _make_vars(15)
        # 3 XOR terms ANDed together -> 2^3 = 8 minterms in DNF
        pairs = rng.sample(list(variables), 6)
        f = And(Xor(pairs[0], pairs[1]),
                Xor(pairs[2], pairs[3]),
                Xor(pairs[4], pairs[5]))
        dnf = f.to_dnf()
        assert dnf.is_dnf()
        assert dnf.equivalent(f)

    def test_20var_not_pushdown(self):
        """20-variable expression: pushdown_not then to_cnf."""
        rng = random.Random(3004)
        variables = _make_vars(20)
        inner = _random_nested_expr(rng, variables, depth=3, breadth=2)
        f = Not(Not(inner))
        pushed = f.pushdown_not()
        assert pushed.equivalent(f)
        cnf = pushed.to_cnf()
        assert cnf.is_cnf()
        assert cnf.equivalent(f)
