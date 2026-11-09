# Equation subsets, conflicts and deletion repairs

The finite-term solver answers one system. This extension asks which indexed obligations explain failure, and which deletions make the original system unifiable. It is an original bounded exhaustive inspector of established concepts, not a new MUS, MCS, SAT, MaxSAT or diagnosis algorithm.

[Live subset inspector](https://midya8.github.io/unifylab/cores.html) · [Base rewrite method](METHOD.md)

## Indexed finite-term semantics

For an input of n equations, the universe is the zero-based positions `0..n-1`, even when two equations are identical. A mask's bit i retains equation i. Retained equations stay in original order. Equal variable names remain shared; removing an equation never renames variables. Validate the full input before enumerating, so inconsistent constructor arities cannot disappear through subset selection.

Run the existing finite-tree solver independently on every mask in ascending numeric order. Do not infer statuses from other masks. Keep mask, original indices, outcome, failure/limit kind and rewrite count. Detailed certificates are reproduced by opening the retained subsystem in the base inspector or invoking the native solve/verify CLI. The aggregate is NOT an independently verified certificate; the native base verifier checks individual detailed rewrite certificates, not these summaries or their completeness.

- A **confirmed inclusion-minimal conflict** C is non-unifiable, and every immediate single-equation deletion C\{i} is unifiable.
- A **confirmed inclusion-minimal deletion repair** D lists indices to REMOVE. The kept system F\D is unifiable, and restoring any removed equation makes it non-unifiable. Empty deletion is a minimal repair precisely when F itself unifies.
- **Minimal is not minimum-cardinality.** The default control has conflicts of sizes two and three, and deletion repairs of sizes two and three. All confirmed frontiers are listed; sizes are not an optimization objective.
- A `limit` is unresolved, never non-unifiable. If a required immediate neighbor is unresolved, do not confirm the corresponding frontier. Known frontiers can still be confirmed elsewhere. Any unresolved mask sets `complete=false`, retains `unresolved_masks`, and withholds both minimum-size fields even when a size seems inferable.

Why immediate neighbors suffice: a unifier satisfying all equations also satisfies any subset of those equations. Thus unifiability is downward closed and non-unifiability is upward closed. For any proper subset of C, choose a removed i; that subset lies inside C\{i}, which unifies. For a proper subset of deletions D, choose an i not deleted; the remaining equations contain (F\D)∪{i}, which fails. This argument concerns actual finite-term semantics. A resource-bound outcome is not a semantic truth and has no such monotonicity claim.

If every subset decides, numeric enumeration and these local conditions identify every inclusion-minimal conflict and repair, so `complete=true`. Only then are `minimum_core_size` and `minimum_repair_size` reported. No conflict gives null core size; the empty repair gives deletion size zero. With no input equations there is one mask, no conflict and the empty repair.

For a fully decided universe, deletion repairs are exactly the inclusion-minimal hitting sets of all minimal conflicts: every conflict must lose an equation, and a deletion set hitting every conflict leaves no inconsistent subset. This is tested by separate brute-force hitting-set enumeration, not used to generate or infer the production status table. No hitting-set completeness claim is made for incomplete tables.

## Limits and representation

All original input and per-solve bounds remain: at most eight equations, six variables, 96 input term nodes, arity two, input depth six, 4,096 nodes per composed state/applied-original result and 256 rewrites. At most 256 independent solver calls. Only aggregate summaries are retained after each call, not all detailed traces simultaneously. Runtime remains exponential in equation count and the base expanded-tree solver can expand exponentially; these are deliberate small-domain limits, not a scalability or benchmark claim. Inputs are finite JSON trees, not rational-tree or arbitrary logical constraints. A fixed global input signature is checked before any calls.

```sh
python -m unifylab --subsets examples/equations.json
unifylab --subsets examples/equations.json -o subsets.json
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
```

`--subsets` and `--verify` are mutually exclusive. Native input remains bounded to 65,536 UTF-8 bytes, duplicate keys and non-finite constants are rejected, and output replacement is atomic. Browser JSON parsing keeps the last duplicate key, as disclosed in both inspectors. Browser state clears on any edit or invalid input, and selected-system links put only the selected JSON in a URL fragment, not a request body. The rewrite inspector renumbers that subsystem locally; the subset page preserves original indices explicitly.

## Original controls and checks

Eight original synthetic controls: duplicated conflicts plus a separate indirect cycle; a successful composed substitution; direct occurrence; empty universe; eight indexed equations including duplicate identities; actual state expansion; actual applied-result expansion; a known singleton clash beside an unresolved expansion. The last control keeps its confirmed singleton conflict without promoting the unknown full mask or claiming complete frontiers.

Tests compare each decided subsystem to a separate lazy-binding oracle and verify all generated detailed certificates. Native frontier tests enumerate ALL proper subsets independently rather than repeating the production immediate-neighbor condition. They check hitting-set duality on complete tables, duplicate identity, equation-order relabeling, actual resource controls, input immutability and a deliberately stubbed unknown required neighbor. Browser/native full-summary parity includes 100 separately seeded systems, in addition to controls. Actual Chrome checks every control/subset, every equation and neighbor, frontier witnesses, export, invalid-state clearing and selected-system reproduction, with layouts at 320/390/1280. These tests are executable regression evidence, not a formal proof or performance comparison.

## Inspected sources and attribution

Public search found and fetched eight sources in research, lecture/tutorial, official implementation documentation and independent explanatory forms. Coverage used is below; no source code, figures, evaluation data or optimized extraction implementation is copied. The direct finite-term monotonicity argument above is derived from satisfying every equation, not a claim that propositional clauses and unification terms are the same representation.

1. Joao Marques-Silva et al., **On Computing Minimal Correction Subsets**, IJCAI 2013. Inspected introduction and definitions 1-3: MUS single-deletion criterion, MCS restoration criterion, MSS complement and distinction from smallest MCS/MaxSAT. Extraction algorithms and benchmark results are not implemented or claimed. https://ijcai.org/proceedings/2013/0098.pdf
2. Anton Belov et al., **Using Minimal Correction Sets to more Efficiently Compute Minimal Unsatisfiable Sets**, CAV 2015. Inspected section 2 definitions and duality discussion, including critical constraints and minimal versus minimum. No mcs-mus algorithms, pruning or reported performance adopted. https://gkatsi.github.io/papers/bkcav15.pdf
3. **Smallest MUS Extraction with Minimal Hitting Set Dualization**, CP 2015 preprint. Inspected preliminary definitions 1-4 and distinction of smallest MUS; the optimized smallest-core algorithm is explicitly out of scope. https://alexeyignatiev.github.io/assets/pdf/iplms-cp15-preprint.pdf
4. Joao Marques-Silva, Mikolas Janota and Anton Belov, **Minimal Sets over Monotone Predicates in Boolean Formulae**, CAV 2013. Inspected definitions 3-6 and MSMP setup. Used only for established inclusion-minimal/monotone framing, not the asymptotically optimal algorithm or comparative results. http://sat.inesc-id.pt/~mikolas/cav13.pdf
5. **Generalizing Redundancy in Propositional Logic: Foundations and Hitting Sets Duality**, arXiv 1207.1257v2. Inspected section 2, multiset formulation, MUS/MSS/co-MSS discussion, irreducible hitting-set definition and theorem 2.1. Labelled-CNF framework, groups, redundancy-preserving reductions and later theorems are not implemented. https://ar5iv.labs.arxiv.org/html/1207.1257v2
6. James Worrell, **Resolution for Predicate Logic**, Oxford Hilary 2024. Inspected section 1 definition of a term-equation unifier and section 1.1 rewrite theorem. Establishes the underlying finite-term semantics, not a complete diagnosis procedure. No resolution prover here. https://www.cs.ox.ac.uk/people/james.worrell/lecture14.pdf
7. Nikolaj Bjorner et al., **Programming Z3**, implementation-authored tutorial, section 4.4 Cores. Inspected caveat that ordinary cores need not be minimal and tactic pipelines can affect minimization. This inspector does not use Z3 or claim Z3 parameter behavior was tested. https://theory.stanford.edu/%7Enikolaj/programmingz3.html
8. Dennis Yurichev, **[SAT] UNSAT core**, August 1, 2020. Inspected PicoMUS/PicoMCS explanatory example and explicit minimal-versus-smallest warning. Independent explanation only, not correctness authority; tools and SAT examples are not copied. https://yurichev.com/news/20200801_MUS/

Existing base-solver attribution, finite-versus-rational-tree scope and independent checker caveats remain in METHOD.md.
