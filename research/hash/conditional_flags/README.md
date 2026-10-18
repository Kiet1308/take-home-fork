# Conditional hash inputs and exact branch flags

These experiments found no faster complete kernel. Main remains at 865 cycles.
The scripts use ordinary 32-bit arithmetic and never read the benchmark's
random inputs. Install `requirements.txt` before running them.

## An exact, shorter-latency branch

For the existing core output `G`, the raw hash branch is exactly:

```text
s = multiply_add(G, 0x80048000, 0x23628000)
p = s >> 31
```

For the encoded branch `(H XOR C5) & 1`, the additive constant is
`0xa3628000`. `branch_identity.py` proves both identities for every 32-bit
`G` by checking their negations with Z3. Both checks return UNSAT.

The ordinary full-value tail plus branch costs four instructions:
`MAD; >>16; XOR; &1`. Retaining that value tail and adding this branch
identity costs five. Branch latency after `G` decreases from four cycles
to two, but using it at all 448 branch-producing vector blocks would add
3584 arithmetic equivalents. No throughput improvement is claimed.

The same script rejects direct branch flags made from every pair of nine
existing live hash words using comparison, integer division, ceiling
division, remainder, or variable shifts. Its exact finite witnesses also
reject zero/nonzero flags and flags taking any two distinct constants,
including separately on each input-parity coset. This is an exclusion of
those fixed expressions, not a lower bound for different hash graphs.

## Conditional prefix relation

At a non-root node the path determines the previous hash's low bit. With
the node value, this determines the next hash input's low bit. The exact
relation after the first MAD and right shear is:

```text
a0 = parity
q = a >> 19
b = a XOR q XOR C1
b0 = parity XOR q0
```

In particular, `b0`, `G0`, and the next branch are not fixed by `a0`.
The low-12-bit searches enforce this relation. Each sampled pair lifts to
a real 32-bit first-prefix input in that parity coset.

`conditional_core_search.py` tests cores targeting the original word
`e = 9*G + C4`. Its `two_mad` mode retains the prefix C1 XOR and tries two
MADs followed by XOR. Its `drop4` mode deletes the C1 XOR and uses two MADs,
XOR, and a final MAD with a live addend. Constants and documented live
source choices are symbolic; UNKNOWN is never treated as UNSAT.

Recorded agent results before packaging:

| Candidate | a0 = 0 | a0 = 1 |
| --- | --- | --- |
| Retain C1, constant-coefficient MADs with live source/addend choices | UNSAT, 1.33 s | UNSAT, 1.33 s |
| Retain C1, fully general MADs; second may consume first | UNSAT, 10.56 s | UNKNOWN, 15 s |
| Delete C1, four-op core with live sources and addends | UNKNOWN, 30 s | UNKNOWN, 30 s |

## Sum prefix with a live bypass

The alternative `s = a + (a >> 19)` is injective on each fixed-`a0` coset.
It nevertheless cannot feed an ordinary triangular core by itself: the
two inputs `a1 = parity` and `a2 = 2^20 + 6 + parity` give the same `s`
modulo eight, but their required original `G` values differ by four
modulo eight. A live `q` bypass could escape that particular obstruction.

`conditional_sum_core_search.py` therefore permits all of `a`, `q`, and
`s` as live inputs to two constant-coefficient MADs, XOR, and a final MAD
with a live addend. This family is UNSAT at low 12 bits on both cosets;
the original checks took 4.07 and 14.30 seconds.

## Reproduction

```bash
python branch_identity.py
python conditional_core_search.py two_mad --parity 0 --samples 40 --timeout 15000
python conditional_core_search.py two_mad --parity 1 --samples 40 --timeout 15000
python conditional_sum_core_search.py drop4 --parity 0 --samples 40 --timeout 15000
python conditional_sum_core_search.py drop4 --parity 1 --samples 40 --timeout 15000
```

The parent reran the exact branch and existing-word checks, both
constant-coefficient conditional cores, and both sum-prefix cores
successfully on 2026-10-18. The first 15-second sum-parity-one rerun
returned UNKNOWN. Its retained 60-second retry returned UNSAT in 13.604
seconds. Packaged logs preserve both outcomes; UNKNOWN is not an exclusion.
