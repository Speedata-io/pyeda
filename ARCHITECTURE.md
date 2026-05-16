# PyEDA Architecture

PyEDA (Python Electronic Design Automation) is a library for symbolic Boolean algebra, providing multiple Boolean function representations, SAT solving, logic minimization, and digital circuit design primitives.

## High-Level Structure

```
pyeda/
├── inter.py              Public API (single import entry point)
├── util.py               Bit utilities (clog2, parity, bit_on)
├── boolalg/              Core Boolean algebra subsystem
├── parsing/              Input format parsers
└── logic/                High-level digital circuit designs

extension/boolexpr/       C library for expression node manipulation
thirdparty/
├── espresso/             Berkeley two-level logic minimizer
└── picosat/              SAT solver
```

## Core Subsystem: `pyeda/boolalg/`

### Class Hierarchy

The central abstraction is `Function` (in `boolfunc.py`), representing a Boolean function independent of its internal representation. Three concrete representations extend it:

```
boolfunc.Function (abstract)
├── expr.Expression       AST-based symbolic expressions
├── bdd.BinaryDecisionDiagram   Reduced ordered BDDs
└── table.TruthTable      Compact positional cube notation
```

Each representation has its own `Variable` subclass (extending `boolfunc.Variable`) that carries a unique ID, name, and optional multi-dimensional indices.

### Expression Representation (`expr.py`)

The richest representation. Expression nodes form a tree:

```
Expression
├── Atom
│   ├── Constant (_Zero, _One)
│   └── Literal
│       ├── Variable (positive)
│       └── Complement (negated)
└── Operator
    ├── NaryOp (OrOp, AndOp, XorOp, EqualOp)
    ├── NotOp
    ├── ImpliesOp
    └── IfThenElseOp
```

Python operators (`~`, `|`, `&`, `^`, `>>`) are overloaded for intuitive expression construction. Higher-level combinators include `OneHot()`, `Majority()`, `Mux()`, `ForAll()`, `Exists()`, and normal form constructors (`DimacsCNF`, `ConjNormalForm`, `DisjNormalForm`).

Expression simplification and NNF conversion are accelerated by the **exprnode** C extension.

### BDD Representation (`bdd.py`)

Reduced Ordered Binary Decision Diagrams with canonical node sharing. Each `BDDNode` holds a variable root plus `lo`/`hi` child pointers. The core operation is `ite(f, g, h)` (if-then-else), from which all Boolean operations derive.

### Truth Table Representation (`table.py`)

Stores function values as packed 2-bit positional cube data (`PC_ZERO`, `PC_ONE`, `PC_DC`) in `array.array` for memory efficiency. Useful for exhaustive enumeration and as input to Espresso minimization.

### Function Arrays (`bfarray.py`)

`farray` provides N-dimensional arrays of Boolean functions (any representation). Supports slicing, reshaping, concatenation (`fcat()`), and arithmetic operations. Factory functions like `exprvars("x", 8)` create named bit-vectors.

### Minimization (`minimization.py`)

Wraps the Espresso C extension to minimize sum-of-products expressions and truth tables. Entry points: `espresso_exprs()` and `espresso_tts()`.

## C Extensions

Three compiled extension modules provide performance-critical backends:

| Extension | Source | Purpose |
|-----------|--------|---------|
| `pyeda.boolalg.exprnode` | `extension/boolexpr/` + `exprnodemodule.c` | Expression simplification, NNF, flattening |
| `pyeda.boolalg.espresso` | `thirdparty/espresso/src/` + `espressomodule.c` | Two-level logic minimization |
| `pyeda.boolalg.picosat` | `thirdparty/picosat/` + `picosatmodule.c` | DPLL-based SAT solving |

The C modules are built via `setup.py` Extension declarations and linked against their respective third-party sources.

## Parsing Layer (`pyeda/parsing/`)

| Module | Format | Output |
|--------|--------|--------|
| `boolexpr.py` | Human-readable Boolean expressions | Expression AST |
| `dimacs.py` | DIMACS CNF/SAT | `(litmap, DimacsCNF)` or `(litmap, Expression)` |
| `pla.py` | Espresso PLA format | `(inputs, outputs)` |

A shared lexer infrastructure (`lex.py`, `token.py`) provides regex-based tokenization with token types: Keyword, Operator, Punctuation, Integer, Name.

## Logic Module (`pyeda/logic/`)

High-level digital designs built on the core algebra:

- **`addition.py`** — Ripple-carry, Kogge-Stone, and Brent-Kung adder circuits
- **`sudoku.py`** — SAT-based Sudoku solver using `OneHot()` constraints
- **`aes.py`** — AES S-box and cipher round logic
- **`graycode.py`** — Gray code bit-vector generation

## Public API (`inter.py`)

A single import (`from pyeda.inter import *`) exposes the full user-facing API:

- Variable/expression constructors: `exprvar()`, `bddvar()`, `ttvar()`, `expr()`
- Operators: `Not()`, `Or()`, `And()`, `Xor()`, `Equal()`, `Implies()`, `ITE()`
- Derived gates: `Nor()`, `Nand()`, `OneHot()`, `Majority()`, `Mux()`
- Conversions: `expr2bdd()`, `bdd2expr()`, `expr2truthtable()`, `truthtable2expr()`
- SAT/minimization: `espresso_exprs()`, `espresso_tts()`
- Parsing: `parse_expr()`, `parse_cnf()`, `parse_sat()`
- Arrays: `exprvars()`, `bddvars()`, `ttvars()`, `fcat()`
- Iteration: `iter_points()`, `iter_terms()`, `num2point()`, `point2term()`

## Representation Conversions

```
Expression ←→ BDD        (expr2bdd / bdd2expr)
Expression ←→ TruthTable (expr2truthtable / truthtable2expr)
```

BDD ↔ TruthTable conversion goes through Expression as intermediate.

## Build & Test

**Build**: `python setup.py build_ext --inplace` compiles C extensions.

**Test**: `pytest --doctest-modules` runs unit tests plus inline doctests.

**Lint**: `pylint` via `make lint`.

**Docs**: Sphinx documentation under `doc/`, built with `make html`.

## Design Principles

1. **Multiple representations** — The same logical function can exist as an expression, BDD, or truth table, each with different performance tradeoffs.
2. **C acceleration** — Computationally expensive operations (simplification, SAT solving, minimization) are implemented in C.
3. **Canonical caching** — Variables are globally unique (keyed by name+indices). BDD nodes are canonically shared.
4. **Pythonic DSL** — Operator overloading enables writing `f = a & b | ~c` directly.
5. **Generic arrays** — `farray` works uniformly across all representation types for bit-vector arithmetic.
