# Variable-shift first-prefix exclusion on the initial 30-bit domain

This closes a gap in the **usual nine-operation hash topology**, specialized
to inputs `0 <= x < 2**30`. It does not exclude arbitrary nine-operation
programs, alternative encodings, or unrelated instruction layouts.

The topology is:

1. One MAD with arbitrary first multiplier, additive constant and input XOR mask.
2. A right shift and XOR with the first MAD result.
3. Two arbitrary constant-coefficient MADs, their XOR, and a final MAD.
4. A right shift and XOR for the final shear.

Constant input and output XOR gauges are allowed in these necessary conditions.
All calculations are genuine 32-bit modular arithmetic.

## Why the first-bit test is necessary

The middle four operations act affinely on the low bit. The reference
pre-tail low bit is nonconstant on the initial domain, so the middle map
must preserve the candidate prefix's low bit, up to a constant.

Write the first multiplier as `2**v * m`, with `m` odd. Since the first
MAD must be injective on a domain containing coordinate29 edges, `v <= 2`.
If its shift is `s`, set `effective = s-v`. The variable high-bit term in
the candidate prefix's low bit is a bit of `m*(x XOR K)+C` at `effective`.
Whether the original unshifted low bit is present only adds `x0` and a
constant. For `effective >= 1`, this addition can also be absorbed by
replacing the free odd multiplier with `m + 2**effective`.

For a final shift `last`, the necessary reference bit is the XOR of raw
hash output bits `0,last,2*last,...`. This is bit zero of the exact inverse
of the final XOR shear. A constant output XOR gauge changes this bit only
by a constant.

## Exact finite derivative and top-cube filters

Run:

```bash
python r0_topcube_filter.py --top-bits 5 --samples 24
```

Coordinate derivatives for input bits1 through29 leave effective/final
shift pairs `(19,16)`, `(27,8)`, and the 64 possibilities formed by
effective shift30 or31 and final shift1 through32. These are necessary
conditions evaluated at explicitly generated, valid 30-bit inputs.

The script then enumerates every possible truth table of the first MAD
bit on the top five genuine input bits. It permits every relevant odd
multiplier residue, every top-input XOR mask, and an independently free
base for each low-input center. Therefore this test allows more freedom
than any real candidate.

**62 of the 64 high-shift cases are excluded.** Only `(30,16)` and
`(31,16)` survive. In particular, the full-domain alternative `(31,4)`
is also excluded on this restricted initial domain. The complete JSON
results and execution log are saved beside the script.

## Closing `(30,16)` and `(31,16)`

At final shift16 the necessary reference bit depends only on input bits
0 through19, and flipping input bit19 flips it. Hence a candidate
`bit_s(m*(x XOR K)+C)` must be independent of input bits20 through29.
The input XOR mask merely permutes all values of those high bits; it
does not affect the following necessary independence conditions.

Set `P=2**20`. For a fixed low input, the 1024 possible high-input values
produce an arithmetic progression modulo `2**(s+1)`. Exact enumeration
of this small high-input cube gives:

| Effective shift | Relevant small modulus | Permitted odd multiplier residues |
| --- | --- | --- |
| 30 | 2048 | 1, 2047 |
| 31 | 4096 | 1, 4095 |

Thus the high-input progression has step `+P` or `-P`. Its output bit can
stay constant only when its base, modulo `2**s`, lies in a circular
interval containing exactly `W = 2**s - 1023*P` consecutive words.

As the low input ranges over all `P` values, the bases are a translate of
`{m*z mod 2**s : 0 <= z < P}`. All those points can fit the required
interval only if their largest circular gap is at least
`2**s - W + 1`. The extra one matters because the interval contains `W`
integer positions and therefore has endpoint distance `W-1`.

`r0_independence_gap.cpp` checks every compatible multiplier residue and
every one of the `P` low inputs. Short prefixes prune candidates before
the full check; they do not weaken the final condition. Run:

```bash
g++ -O3 -std=c++17 r0_independence_gap.cpp -o r0_independence_gap
./r0_independence_gap
```

The exact result is:

| Effective shift | Remaining multiplier residues |
| --- | --- |
| 30, modulo `2**30` | `+1`, `-1` |
| 31, modulo `2**31` | `+1`, `-1`, `2**30+1`, `2**30-1` |

The run takes about half a second on this workspace. No SMT result or
probabilistic assumption is used by this enumeration.

All surviving full multipliers have form `epsilon + q*2**30`, with
`epsilon` equal to `+1` or `-1`. Fixing the lowest two input bits makes
the `q*2**30*x` term constant modulo `2**32`. Over the increasing sequence
of remaining inputs in that residue class, the argument of the output
bit then changes monotonically through an interval shorter than
`2**30`. Its output bit can change at most once.

Independence of input bits20 through29 would repeat the same low-input
pattern 1024 times across that interval. A pattern repeated this often
and having at most one transition must be constant. Consequently every
surviving candidate could depend only on the lowest two input bits.
The reference bit flips between `x=0` and `x=2**19`, whose lowest two bits
are equal. This is a contradiction for both remaining high shifts.

## The two lower effective shifts

The `(27,8)` reference bit depends only on the low28 input bits: its
pre-tail expression uses only core bits0 and8, hence first-prefix bits
0 through8 and first-MAD bits0 through27. The existing exact low-coordinate
influence exclusion in `kernel_math/shift_pair_influence.py --shift 8`
therefore applies unchanged on the 30-bit domain, which contains four
complete copies of that 28-bit domain. Input XOR gauges preserve these
influence counts, and first-multiplier valuations are absorbed as above.

The ordinary `(19,16)` case, including first valuations0,1,2, is handled
by the prior restricted-domain first-prefix fiber checks in
`kernel_math/domain_first_fibers.py` and the existing arbitrary-gauge
core exclusion. This work adds the missing variable-shift cases; it
does not strengthen those earlier checks beyond their stated topology.

**Result:** varying the first and final right shifts does not open a
new usual nine-operation implementation for round zero's legitimate
30-bit input domain. The best executable kernel remains 865 cycles;
these proof scripts do not change its runtime.
