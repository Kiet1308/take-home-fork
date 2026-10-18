# Additional exact hash-family investigations

These experiments use legal 32-bit arithmetic identities and do not modify the simulator, benchmark, tests, or runtime data. **They produced no faster kernel.** The last reported verified main kernel remains 865 cycles. An exact exclusion of one family is not a lower bound for arbitrary programs and does not establish that the requested sub-850 target is impossible.

Notation is the same as `verified_results.md`: `T_s(x)=x XOR (x>>s)`, the reference hash is `H(x)=T_16(G(T_19(4097*x+C0) XOR C1)) XOR C5`, and `G` is an invertible triangular word function. A triangular bijection preserves the position of the first differing input bit.

## 1. Two floor-divisor XOR shears: a bounded exclusion

`F_D(a)=a XOR floor(a/D)` is a permutation for every even positive divisor `D`. This permits a genuinely different nine-operation candidate: first MAD, `F_D1`, two MADs combined by XOR, final MAD, then `F_D2`.

`divisor_two_bit.cpp` compares exact contingency tables of input and pre-tail low-two-bit values. The first and middle odd triangular permutations can only apply one of the eight triangular permutations to each two-bit coordinate. Exact Walsh transforms compute the reference tables for all relevant output XOR masks. A necessary first-bit correlation then enumerates every possible even first divisor, before the full two-bit tables are compared.

The preserved `divisor_two_bit_lower.log` and `divisor_two_bit_upper.log` exclude **every even `D1` in the legal word range**, with arbitrary first-MAD/core constants and output XOR masks, for every even `D2` from **65,280 through 65,792 except 65,536**. No output mask passed the table comparison. This is a bounded final-divisor result. It does not exclude every pair of arbitrary divisors. Direct full-word synthesis with both divisors free timed out; `UNKNOWN` is not a proof.

Portable source: `divisor_two_bit.cpp`. Compile with a standard optimizing C++17 compiler and pass `D2` as its sole argument. No compiled executables are needed in the repository.

## 2. Three-operation prefix using ceiling division

The following prefix is excluded before any invertible triangular middle function and an arbitrary final right XOR shear:

```
z = x XOR input_mask       # mathematical input encoding, not a counted instruction
a = m*z+C                 # m odd
q = ceil(a/D)             # exact unsigned ceiling division, without wrapping a+D-1
p = z XOR q
```

All legal positive constant divisors are included. For `N=2^32`, the parity imbalance of `ceil(a/D)` is `1-distance(N-1, 2*D*Z)`. The reference input-parity correlation after an inverse final shear vanishes for every final shift except19, whose absolute correlation is 1,343,488.

For zero correlation, the divisor must divide `2^31` or `2^31-1`. The latter is prime. The Mersenne divisor is excluded by exact input-MSB derivative witnesses: the candidate has precisely two zero-derivative MSB pairs, whereas each reference tail either supplies at least three such pairs or has a constantly one derivative.

For power-of-two divisors, ceiling boundaries introduce no gap in the reduced-bit proof. Put `D=2^s` and `a'=(a+D-1) mod N`. The exact quotient `ceil(a/D)` differs from `a'>>s` only by the overflow bit `2^(32-s)`. Thus its parity is the ordinary shifted-MAD parity. The earlier exact shift classification leaves `(s, final_shift)=(19,16)`. At `s=19`, the boundary correction is bit13; the existing `first_triangular.py branch_shift` exclusion already uses only the low three prefix bits. Therefore boundary cases cannot rescue this family. `D=1` yields a nonbijective prefix with constant parity.

The nonzero correlation leaves exactly13 divisors. Exact first-coordinate counts give at most four odd multiplier candidates per divisor; second-coordinate counts reject all of them. There are no unresolved flat intervals in the piecewise-count calculation.

Portable sources: `ceil_prefix_invariants.py`, `final19_edges.cpp`, `ceil_final19_influences.cpp`, plus their imported earlier proof files. Preserved fresh outputs are `ceil_prefix_invariants.log` and `ceil_final19_influences.log`. The C++ reference enumeration supplies transformed coordinate counts 1,068,417,854 and 1,074,013,576.

Separately, `square_shift_witnesses.py` gives exact collisions for all31 nonzero shifts in `x XOR ((x*x+x mod N)>>s)`. It does not exclude arbitrary quadratic prefixes.

## 3. Arbitrary parity-preserving rank-one state encodings

The usual nine-operation MAD/shear topology is now excluded for every rank-one linear encoding

```
E(x) = x XOR (((x>>source)&1)*D)
D & 1 == 0
D & (1<<source) == 0
```

The second condition makes `E` invertible and self-inverse. The first preserves the branch bit. Input/output constant gauges and all MAD coefficients/constants are free. **Both right XOR shear amounts are free**, including the identity case for shifts at least32. This extends the older parity-source and fixed-shift proofs; it does not cover arbitrary higher-rank encodings or different operation orderings.

### Sources1 through30, ordinary tail16

Exact input31 witnesses first force `D16=0`. Coordinate influence counts, with the source coordinate correctly omitted, force the first shear to19 and the first multiplier modulo `2^20` to the ordinary sign gauges.

The complete low20 Fourier identities under a rank-one linear map reduce to a GF(2) system. Magnitude matching constrains `D`; Fourier signs jointly constrain `D` and the input XOR translation. These are exact transforms over all `2^20` inputs. They find a few real low-bit symmetries, so assuming only constant gauges would have been incorrect. A separate direct enumeration validated all106 affine-system basis solutions on the full low20 domain.

Input31 derivatives in candidate prefix bits0..11 then force `T_16(D)&0xfff=0`. Almost all low-bit symmetries disappear. The remaining exceptional low bits occur only for sources9..11, where bits8..11 may be mirrored into bits24..27.

Necessary triangular-fiber equations retain the full first-MAD multiplier, constant, input gauge, and encoding mask. Sources1..29 are all `UNSAT` on eight exact reference centers and their coordinate flips, using a15-bit projection (approximately3.6–5.0 seconds per source). Source30 has a top-bit survivor at15 bits, but the16-bit projection is `UNSAT` in2.69 seconds. A zero-encoding control is `SAT`, as expected. These nonzero-encoding fiber exclusions allow any invertible triangular middle function, not merely the three-MAD middle.

### All first/final shifts

For every input coordinate other than `source`, `E` preserves coordinate pairs. Exact derivative witnesses reduce sources0..30 to the ordinary `(19,16)` pair, alternatives `(27,8)` and `(31,4)`, or a few cases where the first shift equals a high source bit. Exact influence counts for coordinates0,1,2 eliminate every alternate/high-source case. The source coordinate is omitted: source1 uses coordinates0 and2, while source0 uses coordinates1 and2. The ordinary pair uses the new fibers above and the earlier parity-source/core proof.

For source31, on the entire lower input half `E(x)=x`. Every first31/final-tail case therefore supplies exact equations for a single odd MAD's bit31, without any unknown encoding mask or middle function. Sixty-two nonstandard tail/flag cases are `UNSAT` on192 exact lower-half inputs, generally in1.2–3.6 seconds. The remaining `(first31, final16, flag0)` SMT run was `UNKNOWN`; it is separately and exactly excluded by coordinate0/1 influence counts. The surviving ordinary `(19,16)` case belongs to the previously excluded raw-node-commuting top-two-bit encoding family. Tail shifts at least32 reduce to the separately checked identity tail.

Portable sources:

- `rankone_general_influence.py` and its JSON classification.
- `rankone_general_walsh.py` and its JSON affine solution spaces.
- `rankone_general_fibers.py`.
- `rankone_general_shift_witnesses.py`.
- `rank31_shift_prefix.py`.
- `rankone_general_results.json` consolidates result logs, including the explicitly marked SMT timeout and zero-mask control.

All compose with the previous exact first-prefix, parity-source, raw-top-two-bit, and core-mask exclusions. They do not justify treating an unrelated timeout or a different topology as impossible.
