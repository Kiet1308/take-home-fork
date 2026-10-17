# Verified mathematical search results

These experiments investigate legal 32-bit instruction identities for the take-home hash. They do not alter the simulator, tests, input generator, or benchmark. **No kernel cycle improvement was produced by these mathematical experiments.** The main implementation's latest reported frozen-test result is 865 cycles, obtained by the scheduling/bootstrap work.

An `UNSAT` result below is an exact exclusion of the stated family: finitely many exact input equations already contradict that family. A timeout/`UNKNOWN` is not an exclusion. None of these results proves an overall instruction-count lower bound for arbitrary programs.

## Notation and reference function

All arithmetic is modulo `2**32`, except logical right shifts and the explicitly modeled unsigned floor/ceil division. Write `T_s(x) = x XOR (x >> s)`.

```
C0 = 0x7ed55d16
C1 = 0xc761c23c
A  = 0xe9f8cc1d
B  = 0xaccf6200
C4 = 0xfd7046c5
C5 = 0xb55a4f09

a = 4097*x + C0
b = T_19(a) XOR C1
G(b) = 9*((33*b + A) XOR (16896*b + B)) + C4
H(x) = T_16(G(b)) XOR C5
```

The usual nine-operation candidate has one first MAD, one two-operation right XOR shear, two parallel MADs combined by XOR, a final MAD, and one final two-operation right XOR shear. Its four coefficients, additive constants, input XOR encoding, output XOR encoding, and (where stated) both shift amounts are free. It removes the separate `C1` XOR from the existing ten-operation encoded hash.

Reproduction dependencies: Python, NumPy, and `z3-solver`. Install them with `python -m pip install -r requirements.txt`, and run these scripts from this directory. Research scripts are standalone and do not change kernel behavior.

## 1. First-prefix classification and the usual nine-operation family

**Status: excluded for the full 32-bit domain**, combining exact first-prefix classification with the independent core mask-absorption exclusion.

The low bit before the final shear must match the low bit of an odd first MAD followed by its first shear, up to a constant. Coordinate-flip influence counts are invariant under a constant input XOR. At the ordinary `(19,16)` shift pair, exact counts restrict the first multiplier modulo `2**20` first to `±4095, ±4097`, then to `±4097`. Exact integer Walsh correlations restrict the low input XOR mask to the identity/complement gauges. Necessary low-bit fiber equations then restrict the full first multiplier, input mask, and additive base to the ordinary sign/complement/MSB gauges.

Scripts:

- `influence_search.py`: exact coordinate-influence formula, with exhaustive small-width checks; 20-bit classification.
- `influence_constants.json`: resulting constant classes.
- `first_triangular.py`: exact bit-vector fiber exclusions. Commands `python first_triangular.py multiplier`, `input`, and `base` exclude all nongauge alternatives under the influence constraints.
- `superopt_hash.py`: synthesis harness, including `allmulsdrop` and `coremulsinput`.
- `core_mask_parity.py`: independent core mask absorption with free coefficients/constants.

For other first/final right-shift pairs, exact finite derivative witnesses leave only `(19,16)`, `(27,8)`, and `(31,4)`. Exact low-coordinate counts eliminate the latter two. `shift_pair_influence.py` reproduces both the witness filter and exact counts. This is not a claim about different operation orderings or non-shift division operations.

The decisive remaining core family is

```
m3*((m1*b + A') XOR (m2*b + B')) + C' XOR M
    == G(b XOR C1).
```

With arbitrary coefficients and constants, the 12-bit projection is already `UNSAT`. Odd/even branch normalization and an odd final multiplier are justified by the target's low-bit permutation. The root investigation also independently excluded this family at full 32 bits. Thus retuning ordinary MAD coefficients cannot absorb the missing `C1` operation.

## 2. Independently specialized even and odd input domains

**Status: excluded for the same nine-operation topology, even when only one input parity must be handled and both shifts are free.** This result permits different constants for the two domains.

For fixed `x & 1 = p`, use mathematical coordinate `t = x >> 1`. The first word is an affine function `2*m*(t XOR k) + c`; this coordinate change is only for the proof. Exact 19-bit influence counts and Walsh correlations constrain `m mod 2**19` to `±4097`, and the low 18 bits of `k` to all zeros/all ones. Six separate first-fiber checks, for multiplier/input mask/base and each parity, were `UNSAT` in approximately 1.1–2.1 seconds. Only the ordinary gauges and an optional first-prefix bit-zero flip survive. The low 12 core input bits remain unrestricted, so the core must absorb either `C1` or `C1 XOR 1`. Both are `UNSAT`; the latter was independently rerun with a free final coefficient and free output XOR mask in 4.1 seconds.

Reproduction:

```
python parity_influence_search.py
python parity_first_fibers.py multiplier --parity 0
python parity_first_fibers.py input --parity 0
python parity_first_fibers.py base --parity 0
# Repeat the last three commands with --parity 1.
python core_mask_parity.py --width 12 --m3 free --input-xor 0xc761c23d
```

`parity_influence_constants.json` and `parity_translations.json` store the exact finite classifications. `parity_influence_search.py` also closes the alternative shift pairs using domain-restricted coordinate counts. The first two relevant counts are:

| Input parity | Final shift | Original input-bit1 edges | Original input-bit2 edges |
|---|---:|---:|---:|
| even | 8 | 38,246,070 | 35,868,630 |
| odd | 8 | 38,246,070 | 35,790,294 |
| even | 4 | 560,051,178 | 531,720,134 |
| odd | 4 | 560,051,178 | 531,516,514 |

No odd first multiplier and additive constant match the two counts in any row.

## 3. Rank-one parity-preserving state conjugacy

**Status: excluded in the usual nine-operation topology with ordinary `(19,16)` shifts**, for every even `D` in the invertible linear encoding `E(x) = x XOR ((x & 1)*D)`, with arbitrary MAD coefficients/constants and constant input/output gauges.

The target before the final shear must be independent of original input bit31 in its low12 bits. Since the true branch bit varies under that input flip, this forces `T_16(D) & 0xfff == 0`. Exact parity-half Walsh correlations then force `D`'s low20 bits to zero. Combined with the previous condition, its low28 bits vanish. Low-bit fiber contradictions exclude any remaining bits28–30. The bit31-only shear can be absorbed into a first multiplier's high bit; first-prefix classification below bit15 and the 12-bit core exclusion finish that case.

Scripts: `rankone_translations.py`, `rankone_translations.json`, `rankone_fibers.py`, and `first_triangular.py --fiberbits 15`. Direct fixed-coefficient searches are also available as `superopt_hash.py linearconjugate9`; `linearconjugatemuls9` is the broader synthesis form, with necessary constraints from the exact proofs.

General rank-one shears sourced from an arbitrary bit were **not** completely excluded with arbitrary coefficients. A joint fixed-coefficient source-bit search reached `UNKNOWN`; it must not be described as a proof.

## 4. Raw-node commuting state encodings: proof scope

**Status: excluded for the ordinary ten-operation MAD/shear topology with `(19,16)` shifts**, using the first-prefix/core exclusions. The argument applies to invertible word encodings that commute with XOR by every 30-bit node value; it does not cover arbitrary encodings or arbitrary instruction orderings.

Every such normalized encoding has the form `E(x) = x XOR F(x >> 30)`, for a four-entry tag table `F`; a separate constant gauge may be added. This includes rank-two linear tags and nonlinear top-bit-AND tags.

Under an input-bit29 flip, the true hash's top-two-bit transition graph contains all six possible edges in each of the four input-top-two-bit cosets. Therefore every nonconstant Boolean function of the output top two bits introduces a dependency on that input flip. Exact witnesses are in `rawnode_top2_witnesses.py`.

For the ordinary first prefix, the low pre-tail bit cannot have that dependency. The first-prefix Walsh no-period property forces all four input tags' low20 bits to agree. The same graph argument for low10 pre-tail bits forces their low26 bits to agree. If a first differing tag bit `k < 30` remained, changing input coset would affect the reference first prefix at bit `k-19`, whereas the output tag correction can start only at bit `k-16`; this is a contradiction. Thus only a permutation of the top two bits remains. Every permutation of two bits is affine. First-prefix classification below bit11 with 30-bit gauges, followed by the arbitrary-input-mask low11 core exclusion, eliminates those cases.

This is a composed mathematical argument, not one monolithic SMT check. `rawnode_top2_witnesses.py` verifies the finite graph witnesses; `first_triangular.py --fiberbits 11 --gauge_bits 30` supplies the relevant first-prefix exclusions; the core `coremulsinput` checks supply the final obstruction.

## 5. Free live prefix intermediates in shorter cores

The ordinary prefix already computes `a`, `q=a>>19`, `c=a XOR C1`, and `b=c XOR q`. It is legitimate for a new core to reuse all of them without extra prefix instructions. At a 12-bit projection, `b` and `q` are independent inputs, and the other free words equal `a=b XOR q XOR C1`, `c=b XOR q`. This makes exact small-width falsification possible without incorrectly discarding high-input information.

`prefix_core_search.py` uses 40–56 exact independent `(b,q)` pairs, symbolic operand selectors, arbitrary constants, and a free output XOR mask.

Verified exclusions:

- **Two MADs then XOR:** each MAD may use a free prefix source, arbitrary constant multiplier, and either a constant or free-prefix addend. `UNSAT` in 1.35s.
- **Three-operation XOR feed:** `t=MAD(source,coefficient,addend); u=t XOR operand; result=MAD(u,coefficient,addend)`. The first coefficient may be constant or any free prefix word; the XOR operand may be a free word or constant; the final coefficient/addend may also use `t`. All selector splits are excluded, generally in under 2s. The constant-XOR/constant-final-coefficient case uses the quarter-increment invariant described below rather than a timeout being counted as a proof.
- **C1-deleted four-operation core:** two MADs on the free `b/a/q` words, XOR, then MAD, targeting `G(b XOR C1)`. Both first addends and the final addend may use free words; the final addend may also use either MAD result; final multiplier may be constant or `b/a/q`. `UNSAT` in 53.9s with the latter freedom.
- **AND/OR feed variants:** all variable-final-coefficient cases and all free-word middle operands are `UNSAT`, including variable first coefficients. Residual constant-middle-mask/constant-final-coefficient cases with a variable first coefficient are also `UNSAT` in under one second each. The remaining case with a constant first coefficient is excluded by the finite quarter-mask lemma below. Thus this entire stated selector family is excluded; the unsplit SMT timeouts were not themselves counted as proofs.

The quarter-increment invariant is useful for exact closure: in a `w`-bit word, write `Q=2**(w-2)`. Odd affine maps and fixed XOR masks have a constant modular increment `f(x+Q)-f(x)=±Q`, independent of `x`. Compositions inherit the property. The reference core violates it at 12 bits: the increment is 1024 at `x=0`, but 3072 at `x=1`. For the free-prefix constant-XOR/constant-final-coefficient feed, fixing `q=0` reduces every live source to `b`, `b XOR C1`, or zero, and the same constant-quarter-increment argument applies. It does not automatically apply when two variable words are multiplied.

For the masked version, if both `t(x)` and `w(x)` have constant quarter increments, the top two bits of `n*(t(x) AND K)+w(x)` in each input quarter have form `n*((alpha*j+A) AND k)+beta*j+B (mod4)`. `quarter_mask_lemma.py` exhaustively checks all 1024 parameter tuples: every permutation of `j` has a constant odd slope, and that slope does not depend on `A`. Consequently a permutation of this form also has a constant quarter increment. OR reduces to the same statement by `t OR K = t+K-(t AND K)`. Fixing the free prefix `q=0` gives the required constant increments for any first MAD with a constant coefficient and any permitted final addend.

## 6. Other exact finite family searches

- `feedforward_core.py`: several three-operation cores with a first MAD, a feedforward XOR/AND/OR, and final MAD (including variable addends/multiplicands) are `UNSAT` at 12 bits. Ordinary AND/OR feed cases completed in 0.01–0.17s; XOR cases in 0.03–5.93s. Shifted-affine cases using `e=n*x+(t>>s)` and `e=x*(t>>s)+C` were excluded with exact full32 expressions projected to low12. Other shifted-affine variants timed out and remain open.
- `nonlinear_core_grid.py`: all 72 tested three-operation families `t=x op K; u=t AND/OR/XOR x; e=MAD(u,m,addend)` were `UNSAT`, with addend `x`, `t`, or a constant. First op ranged over AND/OR/XOR/left shift/right shift/unsigned floor division/ceil division/remainder. Ceil division uses a 33-bit sum to match simulator semantics. These results cover that grid only.
- `superopt_hash.py dropmadcore`: two arbitrary affine MAD terms combined by XOR, plus a free output XOR mask, cannot replace the whole ordinary core; exact low-width samples are already contradictory.

## 7. Free branch-bit tail obstruction

Consider the proposed ten-operation topology whose final three operations are

```
q = d >> 31
y = (even_m*d + even_C) XOR q
```

with `even_m` divisible by two but not four, so `q` is directly the branch bit. If the preceding core is an odd triangular map of an ordinary first MAD/right-shear prefix, output bit1 must equal the first-prefix low bit up to a constant. Its derivative under input bit31 must therefore be constantly zero or constantly one, depending on the first shift. The reference `H1` derivative is zero at `x=0` and one at `x=1`; the derivative of `H1 XOR H0` is one at `x=0` and zero at `x=1`. Consequently the raw form and parity-source rank-one conjugacies (including the left-one shear) cannot implement this topology. More general input/output encodings are outside this obstruction. The exact two witnesses are checked by `rawnode_top2_witnesses.py`.

A separate possible escape is `E(x)=x XOR (((x>>17)&1)*D)`, with `D0=0`, `D1=1`, `D17=0`. Its encoded output bit1 is `H1 XOR H17`, so the simple bit31 obstruction cancels. Nevertheless, all these encodings are excluded by `free_parity_encoding_influence.py`: the required first shift is 20, and its first-MAD bit20 must have coordinate0/1 influence counts 1,044,480 and 1,040,380. The first count permits only four multiplier residues modulo `2**21`; the second excludes every constant for all four. These exact counts are independent of the other bits of `D`, because this encoding leaves coordinate flips0 and1 unchanged. This proof also assumes the ordinary first MAD/right-shear prefix and a triangular middle core; it is not a statement about arbitrary ten-operation topologies.

## Explicit limits

The search does not prove that nine-operation hashes, a kernel below 850 cycles, or useful nonlinear encodings are impossible. Changed operation order, other nonlinear instructions, more live intermediate reuse, larger multiword representations, mixed lookup/arithmetic algorithms, and other encodings remain outside the proved families. No `UNKNOWN` result should be promoted to `UNSAT`.
