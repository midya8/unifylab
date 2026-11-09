# UnifyLab

A binding is not a solution. An auditable finite first-order unifier: every pending equation, every composed substitution, every constructor conflict and every occurs-check path.

[Live inspector](https://midya8.github.io/unifylab/) · [Method, limits and inspected sources](METHOD.md)

## Why inspect it?

Binding `?x` to `box(?y)` is only the start. If `?y` later becomes `pair(?z, ?z)` and `?z` becomes `amber`, the earlier `?x` binding must change too. An alias reversal is not automatically a cycle. A real cycle can appear only after an earlier substitution. A resource limit is not non-unifiability.

The native Python engine eagerly composes equation rewrites. The separately written JavaScript engine reproduces the complete certificate in the browser. A native certificate checker reconstructs every local rewrite without calling the solver. A third, lazy-environment oracle in tests recursively dereferences bindings instead of rewriting the pending system.

## Run without a service

```sh
python -m unifylab examples/equations.json
python -m unifylab examples/equations.json -o certificate.json
python -m unifylab --verify certificate.json
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
```

Install the wheel to get the `unifylab` command. No runtime dependencies, API, model weights or account required. Browser demo is static.

Terms are JSON strings like `"?x"` for variables, arrays like `["box", "?x"]` for constructors, and `["amber"]` for constants. Constructor arity is fixed across the input. Variable names share one namespace across the equation system; variables and constructors are distinct. Only the `equations` key is accepted.

```json
{"equations": [["?x", ["box", "?y"]], ["?y", ["pair", "?z", "?z"]], ["?z", ["amber"]]]}
```

## What the certificate keeps

- Deterministic first-pending-equation policy and all delete/orient/decompose/eliminate/occurs/clash steps.
- Full before/after equations and bindings, including the composed changes to older bindings.
- Exact zero-based child path to the first depth-first occurrence for cycle failure.
- Final normalized simultaneous substitution and every original equation after one application on success.
- Explicit non-unifiability versus node/step/result resource limit, with only a completed prefix claimed for limits.
- A separate local rewrite checker, tested against forged fields, broken transitions and false terminal claims.

Seventeen controls retain 38 rewrites: eleven successes, four non-unifiable tasks and two resource-limit cases. Native tests compare a lazy-binding oracle on the controls, 600 seeded tasks and all 64 pairs from a small term pool. Bounded ground factorization tests are regression evidence, not a proof of most-generality. Python/JavaScript compare 167 complete reports with 270 rewrites. Actual Chrome checks every retained rewrite, rendered equations/bindings/witnesses, export, invalid-input clearing and every control/step layout at 320/390/1280. Twelve native tests run on Python 3.10-3.13; three Node/Chrome tests. Isolated wheel reproduction checks seventeen reports, four installed module origins and both CLI entry points in solve/verify modes outside the source checkout.

## Scope

Established finite-tree syntactic unification, not a new algorithm. Six variables/eight equations, input depth six, arity at most two and 96 input nodes. Composed states and the applied-original result each have a 4,096-node budget; at most 256 steps. This expanded-tree implementation can be expensive. Resource limits never imply non-unifiability. No rational trees, higher-order/AC unification, quantified formulas, resolution prover, linear-time claim or benchmark win. See METHOD.md for checker scope, JSON differences, attribution and exact limits.


## Which equations explain the conflict?

[Equation-subset inspector](https://midya8.github.io/unifylab/cores.html) · [Subset method and eight inspected sources](SUBSETS.md)

Run `python -m unifylab --subsets examples/equations.json`. Every indexed subset is solved independently. Confirmed inclusion-minimal conflicts show successful single deletions; confirmed deletion repairs list indices to remove and failing restorations. Duplicate equations keep separate identities. Minimal is not minimum-cardinality. A resource limit stays unknown and withholds completeness and minimum-size claims; an aggregate summary is not a base rewrite certificate. Any selected subsystem opens in the existing rewrite inspector for its detailed trace.


## Generalize two terms without losing repeated differences

[Ground-term generalization inspector](https://midya8.github.io/unifylab/generalize.html) · [Generalization method and inspected sources](GENERALIZATION.md)

`python -m unifylab --generalize terms.json -o generalization.json` retains common constructors and reuses one variable for each repeated ordered disagreement pair. Both exact reconstruction maps and every postorder node remain inspectable. `python -m unifylab --verify-generalization generalization.json` checks the supplied canonical trace without calling its generator. Two reconstructions alone do not establish least-generality: a fresh-per-position trace can reconstruct yet lose a shared equality. Finite **ground inputs only**, distinct from the solver's variable-bearing equations. Established Plotkin/Reynolds anti-unification, not a new algorithm or code-repair system.
