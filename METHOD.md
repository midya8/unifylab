# UnifyLab method and evidence

## Domain, names and syntax

Finite first-order terms over a ranked constructor alphabet. A variable is an ASCII string matching `?` then a lowercase letter and up to fifteen lowercase letters/digits/underscores. A constructor is an array whose first item is its ASCII lowercase name followed by zero to two terms. A constant is a zero-argument constructor. The same constructor name must have the same arity throughout the input. An arity inconsistency is invalid input, not a reported constructor clash. The variable `?amber` and constant `["amber"]` are distinct.

The entire input is `{"equations": [[left, right], ...]}`. All equal variable names in all equations designate the same variable. There are no binders, capture, quantifier instantiation, standardizing-apart step, literal polarity, predicate logic parser or semantic equality theory. Equations and constructor children are ordered for the certificate, even though unifiability does not depend on equation order.

Input bounds: six distinct variables, eight equations, depth at most six with a term root at depth zero, 96 total input term nodes, arity at most two. Each variable and constructor occurrence counts one node; equation pairs, names and argument containers do not add nodes. No strings other than valid variables are terms.

## Rewrite policy

Process the first pending equation `a = b`:

1. **delete** if the two terms are structurally equal, including whole compound terms.
2. **orient** if the left term is a constructor and the right a variable.
3. If the left term is a variable, inspect the right term for that variable. A proper occurrence yields **occurs** failure. Otherwise **eliminate**: remove the equation, replace that variable throughout all remaining equations and every existing binding, then add the new binding. Replacement does not re-enter an inserted term. Sort the binding keys by ASCII name.
4. Otherwise different constructor names yield **clash** failure. Matching constructors **decompose**, prepending corresponding child equations left to right.

Both sides of an alias have already been rewritten by earlier eliminations. Consequently `?x = ?y` followed by `?y = ?x` becomes an equality to delete, not a false occurs failure. This explicitly tests the class of binding-list pitfalls discussed by Norvig. Norvig's correction concerns faulty implementations, not a flaw in the unification theorem.

Each step retains index, rule, full before and after equations/bindings and rule witness. Occurs witnesses use the first depth-first left-to-right occurrence and zero-based child positions; the root position is `[]`. A genuine occurs failure has a nonempty path because identical terms are deleted first. Failure steps leave the current state unchanged and terminate. Partial bindings on failure or a limit are not a unifier.

## Substitution and generality

A substitution is applied simultaneously once. Replacing a variable returns its replacement without applying the same map again inside it. Composition at each elimination ensures no bound-domain variable remains inside the final binding range. The result is idempotent. Every original equation is retained after one substitution application on success.

A most general unifier is defined by factorization: every other unifier is an instance of it. It is not defined by having the shortest printed map or the smallest number of characters. MGUs may differ by residual variable naming. The deterministic policy selects one presentation, not a unique literal map. The success interpretation relies on the established solution-preserving rewrite rules and solved-form theorem, not on a finite empirical test proving all substitutions. This implementation is an original educational variant with eager binding composition, not the optimized multiequation/PASCAL algorithm in Martelli and Montanari's paper.

## Resource limits and parser behavior

At most 256 rewrites. Each proposed composed state is limited to 4,096 term nodes, counting pending equations and binding right sides. Budget checks happen during construction before oversized replacements are allocated. The final applied-original-equation array has its own 4,096-node budget. A limit record has status `limit`, reason `nodes`, `steps` or `result_nodes`, null failure, null substitution, null applied equations and null free-variable result. It retains exactly the completed prefix and final partial state. It is neither success nor non-unifiability. The step-cap branch is exercised by lowering both solver/checker caps in a native test; the two node-limit controls hit the actual default limits.

Input construction is bounded, but the expanded-tree representation is not a linear-time or compact-DAG unifier. The native CLI accepts at most 65,536 UTF-8 bytes for equation input and 67,108,864 bytes for a supplied certificate to check. It reads only one byte beyond the limit. It rejects duplicate keys, nonfinite JSON constants, malformed UTF-8 and parser recursion errors. Output replacement is atomic only after successful parsing/computation. A valid `limit` result is still an output record, not a CLI parse error. `--verify` emits `{"valid": false}` for a well-parsed invalid certificate; invalid JSON exits with code two. The browser has the 65,536-byte equation-input limit and uses standard JSON.parse, which retains the last duplicate object key. This difference is disclosed in the UI.

## Independent checks and their scope

The native verifier does not call `solve`. It validates input/metadata, reconstructs each local rule and exact witness, checks continuity, terminal failure or the actual pending resource bound, and checks final substitution normalization and original-equation equality. A verifier accepting a certificate is evidence under this checker's rules, not a cryptographic signature, origin authentication, formal proof-assistant extraction or a guarantee that the checker has no bugs. The browser's displayed equality/idempotence checks are narrower result checks and are labeled as such; they are not claimed to be this independent native checker.

The third test oracle uses a mutable lazy binding environment, symmetric dereferencing, recursive occurrence checks and final expansion. It does not use the production pending-equation rewrite engine or verifier. It covers the seventeen controls (comparing decisions/maps where no limit is reached), 600 seeded systems and all 64 ordered pairs from an eight-term pool. Sixty additional seeded systems enumerate a bounded ground candidate pool to test solution factorization; this finite pool is not a completeness or universal-most-generality proof. Forgery tests mutate every recorded step field and report metadata/final claims, including boolean-versus-integer metadata.

A separately written JavaScript composed engine agrees on 167 complete reports containing 270 rewrites: the seventeen controls and a different 150-task bank. Actual Chrome checks all control results, each of 38 recorded rewrites, every displayed equation/binding/witness, selected/full JSON, final states, exports and invalid-edit clearing. Every control and step is layout-checked at 320/390/1280. Fixture counts are coverage, not speed or accuracy benchmarks.

Twelve native tests, three Node/Chrome tests, native Python 3.10/3.11/3.12/3.13. A wheel built and installed in a temporary environment outside the checkout reproduces all seventeen reports through `python -m unifylab` and `unifylab`, in solve and verify modes, checking four module origins. No runtime dependency, model, dataset or paid service.

## Synthetic controls and attribution

The control bank was written for this project. It includes eager composition through nested terms; an alias reversal inspired by Norvig's documented bug class; direct/indirect nested cycles; constructor clash; repeated-variable late clash; orientation; identity/empty systems; free residual variables; child-order decomposition; six-variable alias chains; repeated equations; distinct variable/constant namespaces; and separate state/result expansion limits. Familiar boundary cases are established unification examples, not a claim of new theory. No source's code, benchmark corpus, paper figure or numerical performance table is copied.

Six source groups were found by public search and fetched. Inspected coverage is intentionally stated; it is not a claim of line-by-line review of every source:

- **Alberto Martelli and Ugo Montanari, An Efficient Unification Algorithm**, ACM TOPLAS 4(2), April 1982, 258-282. Inspected abstract/introduction, equation-system framing and discussion distinguishing the nondeterministic foundation from later optimized multiequations. Grounds the established algorithm family and expense of expanded substitution; optimized implementation and performance results are not reproduced. https://dl.acm.org/doi/pdf/10.1145/357162.357169
- **James Worrell, Resolution for Predicate Logic**, Oxford Logic and Proof, Hilary 2024. Inspected section 1 substitution/composition, factorization definition, solved form and section 1.1 rewrite rules/theorem; read section 1.2's contrasting variant for context. Primary operational and MGU terminology source. Resolution sections are outside this implementation. https://www.cs.ox.ac.uk/people/james.worrell/lecture14.pdf
- **Peter Norvig, Correcting A Widespread Error in Unification Algorithms**. Inspected problem, alias/dereferencing failure mechanism, correction and conclusions. Grounds alias-reversal regression coverage and the need to dereference both sides in the independent lazy oracle. No Lisp implementation copied. https://www.norvig.com/unify-bug.pdf
- **SWI-Prolog reference manual, unify_with_occurs_check/2**. Inspected finite versus rational-tree distinction and cycle-safe behavior with already cyclic arguments. UnifyLab only accepts finite JSON trees and does not imitate SWI's acceptance of already cyclic terms. Community comments are not authority for the algorithm. https://www.swi-prolog.org/pldoc/doc_for?object=unify_with_occurs_check%2F2
- **Hannes Strass, Unification, Lecture 2**, TU Dresden, dated October 19, 2026, with Michael Thielscher slide credit. Inspected ranked alphabets, simultaneous substitution application, solved form/factorization, Martelli-Montanari theorem and exponential-unifier warning. Supports explicit representation/resource caveats. No slide examples copied. https://iccl.inf.tu-dresden.de/w/images/5/5f/FLP2026-02.pdf
- **hardmath123, Meet the Robinson: 4**, January 11, 2016, independent explanatory article. Inspected introductory unification/resolution context and occurs-check discussion. Used only for audience/context, not correctness evidence. Its loose statement about Norvig is not adopted: Norvig corrects faulty binding-list implementations, not the underlying theorem. The article's resolution proof examples are not implemented or copied. https://hardmath123.github.io/meet-the-robinson-4.html

No rational trees, associative/commutative theories, higher-order unification, resolution theorem prover, learned model, novel algorithm, linear complexity or benchmark win is claimed.
