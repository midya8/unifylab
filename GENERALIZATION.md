# Ground finite-term anti-unification

[Live generalization inspector](https://midya8.github.io/unifylab/generalize.html) · [Unification](METHOD.md) · [Conflict subsets](SUBSETS.md)

Unification asks for a common instance. Anti-unification asks for a common generalizer. This is an original bounded implementation and inspector of established Plotkin/Reynolds syntactic anti-unification, not a new algorithm, code-clone detector or inductive program learner.

## Exact domain and order

Input is exactly `{"terms":[left,right]}`. Both terms must be **ground** finite constructor trees: no input variable strings. Constants are zero-argument arrays, as in `["amber"]`. Names, ranked constructor arities, depth six from root zero, arity at most two and 96 total input term nodes follow the base input grammar. Arity is fixed globally across both terms. Input byte limit is 65,536 UTF-8 bytes. No rational/cyclic terms or hidden input bindings. The base equation solver's six-input-variable bound does not restrict freshly introduced generalization variables; one control introduces eight.

A pattern g generalizes a and b if gσ=a and gτ=b for two simultaneous substitutions. A least-general generalization l is itself a common generalizer and, for every other common generalizer g, there is a substitution ρ with gρ=l. It is unique up to renaming. Least-general does not mean shortest text, fewest variables, minimum edit distance or semantic similarity. A correct reconstruction proves only the common-generalizer half, not least-generality.

## Construction and sharing

Compare corresponding nodes, retaining a common constructor and recursing on its children left to right. If root constructors differ, replace the entire ordered subtree pair by a fresh variable. The same ordered disagreement pair must reuse the same variable. Matching only the left term, matching only the right term, or treating reversed pairs as identical is wrong.

For `pair(amber,amber)` and `pair(blue,blue)`, the LGG is `pair(?g0,?g0)`. The looser `pair(?g0,?g1)` reconstructs both too, but loses a shared equality. For `pair(amber,blue)` and `pair(blue,amber)`, the two ordered pairs differ, so the LGG has two variables.

Variables are assigned ?g0, ?g1, ... on first encounter of a disagreement. Each step records input subtrees, zero-based child path, rule, resulting generalized subtree, variable and first-source record. Records are **postorder**: retained constructors appear after their children. A fresh record's source index is itself; reuse points to that earlier fresh record; retain has null variable/source. Constants are retained constructor records with no children. There is no equal-whole-tree shortcut, so identical compound trees still show every visited common node.

The certificate includes the pair table, both reconstruction maps, final generalized term and both reconstructed inputs. Substitution images are ground, so one simultaneous application suffices. Structural JSON keys memoize pairs in the generator. This is not hash-consed DAG construction, linear-time implementation, benchmark speed evidence or a claim about a vendor's implementation. Full subtree/path records intentionally repeat small structures.

Established reasoning: any common generalizer can retain a constructor only where both inputs have that constructor. If a variable repeats in a common generalizer, its corresponding ordered input subtrees must agree at every occurrence. Keeping every common constructor and identifying every repeated disagreement pair therefore preserves all syntactic structure and equality relationships available to a common generalizer. The least-generality interpretation follows the standard first-order theorem; tests below do not replace it with a universal empirical claim.

## Native checker and independent tests

`verify_generalization` does not call `generalize`, the unification solver or `core.apply`. It builds postorder obligations with an explicit stack, inspects the supplied records, searches a structural list of previous pairs instead of the generator's JSON-key memo, checks child outputs and canonical fresh/reuse references, then privately instantiates the final term and checks both exact originals. It checks every field and rejects added fields, altered paths, reordered/missing nodes, wrong maps and boolean/numeric metadata confusion. The checker accepts this deterministic naming/record policy, not every possible renamed LGG certificate. It is executable checking, not a proof-assistant extraction, cryptographic signature, provenance attestation or guarantee of bug-free checking.

Python tests check nine original controls, 600 seeded ground pairs, all 64 ordered pairs from a small ground-term pool, symmetry of the canonical generalized shape, input immutability and field/record forgeries. An independently written pattern matcher checks the factorization direction against a bounded pool of 60 candidate patterns over 159 systems; this is bounded regression evidence, not an exhaustive theorem. A coherent fresh-per-position forged trace reconstructs both inputs but is rejected for splitting a repeated pair. Tests disable the generator while checking a valid trace. CLI tests cover mode exclusion, duplicate-key rejection, valid checking and atomic output preservation on invalid input.

The independently written browser generator agrees with Python on controls plus 200 differently seeded ground pairs. Actual Chrome checks every retained node, ordered pair, reconstruction map, summary, full/selected JSON, export and invalid-state clearing, with all control/node layouts at 320/390/1280. The browser equality checks only reconstruction; it does not claim to independently verify the trace. Installed checks reproduce both --generalize and --verify-generalization through module and console entry points outside the source checkout, alongside existing modes.

## Reproduce

```sh
python -m unifylab --generalize terms.json -o generalization.json
python -m unifylab --verify-generalization generalization.json
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
```

Both new flags are mutually exclusive with solve/verify/subsets modes. Verification input is bounded to 64 MiB like base certificate verification. Native parsing rejects duplicate keys, non-finite JSON and bad UTF-8; output replacement is atomic after computation. Browser JSON.parse keeps the last duplicate key, disclosed in the UI. No external service, model, runtime dependency, account or private dataset.

## Inspected public sources

Six source groups were found by public search and fetched. Only the inspected coverage below informs this implementation; no source code, figures or examples were copied. Original controls use the project's own synthetic constructor vocabulary.

1. David M. Cerna and Temur Kutsia, **Anti-unification and Generalization: A Survey**, IJCAI 2023. Inspected introduction and section 3.1, including definition of FOSG, substitution order, uniqueness up to renaming and example distinguishing a shared variable from a looser generalizer. Higher-order, equational and other survey frameworks are out of scope. The www-host PDF fetch failed; the observed ijcai.org version was fetched successfully. https://ijcai.org/proceedings/2023/0736.pdf
2. SWI-Prolog **term_subsumer/3**, official reference. Inspected most-specific-generalizer description and explicit ability to handle cyclic terms. UnifyLab is deliberately narrower: two finite ground trees only. SWI implementation/version behavior is not tested or claimed equivalent. https://www.swi-prolog.org/pldoc/doc_for?object=term_subsumer%2F3
3. Gerald Jay Sussman, MIT **Least-General Generalization** teaching material, code heading dated March 9, 2020. Inspected introductory attribution and LGG/example/pair-binding traversal sections. Its S-expression representation can generalize identifiers in positions where this ranked first-order constructor representation cannot. No Scheme implementation, examples or application claims copied. https://groups.csail.mit.edu/mac/users/gjs/6.945/L17-anti-unification.pdf
4. Erik Jacobsen, **Unification and anti-unification**, course continuation report, June 6, 1991. Inspected definitions 2.3.3/2.3.10 and section 4.1 through 4.1.4: paired traversal, substitution-pair search, reconstruction and warning that skipping pair reuse loses least-generality. Linear/DAG/parallel algorithms and performance results are not implemented. Its historic 1969 attribution differs from the 1970 publications cited by the survey; this project follows the survey's Plotkin/Reynolds attribution without claiming a new history result. https://erikjacobsen.com/pdf/unification.pdf
5. Eric Lippert, **Anti-unification, part 2**, October 31, 2018. Inspected constructor refinement, redundant-pair sharing and equal-term rule explanation. Explanatory support only; the article explicitly does not prove convergence/optimality. This implementation uses direct traversal, not its global rule-state procedure. https://ericlippert.com/2018/10/31/anti-unification-part-2/
6. **Anti-unification**, Wikipedia community overview. Inspected prerequisites, substitution/generalization ordering and first-order syntactic section, including injective ordered-pair-to-variable mapping. Used as a cross-check and vocabulary source, not primary correctness authority. Higher-order/equational examples and implementation code are not adopted. https://en.wikipedia.org/wiki/Anti-unification

No AST parser, code repair engine, multiple-input learner, semantic clone judgment, higher-order/AC/equational generalization or rational-tree support is implied by these sources or the demonstration.
