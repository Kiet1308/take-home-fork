# C0 mask and bootstrap experiments

## Outcome

No candidate beats the validated 865-cycle main kernel. The best candidate
in this bounded experiment takes 866 cycles and passes all nine frozen
submission tests. Main, the simulator, and the official test files were not
modified. All candidate instructions stay inside the ordinary ISA and the
1536-word scratch limit.

The prototype is `kernel.py`; `best_parameters.json` selects the
866-cycle version with the same arithmetic weight and LOAD/FLOW counts as
main. Run `python run_frozen.py` to repeat the complete frozen suite.

## Implemented changes

C0's nine-word single-broadcast owner is also the fixed alternating mask.
Its three required copies populate the even mask positions; the odd words
keep their initial zero values. C0 is loaded at cycle zero. The combined
bootstrap initially routes C1 through FLOW at cycle one and uses the
existing header values to derive 4097 with a vector multiply-add. C0 and
C1 selection instructions are prioritized so the first hash multiply stays
at cycle three and its C1 XOR stays at cycle four.

Additional switches compare direct loading of 4097, a native C1 broadcast,
partial interleaved constant patterns, and a live scalar32 helper for input
addresses. The latter computes 32 from header16 and explicitly forms input
pointer2342 from header2310+32, making the helper available to ordinary
constant folding. The best version uses this helper and interleaved pattern
lengths [0,2].

A separate requested route puts 4097 in FLOW0, removes the immediate2334,
and forms2326=header2310+16 and2334=2326 OR header10. It uses native C1 and
keeps C0's selection at cycle two. This route is correct but takes867 cycles.

## Measured comparisons

Weight means ALU instructions plus eight times VALU instructions. The
startup deficit is unused arithmetic capacity in the first16 cycles,
relative to60 scalar-equivalent operations per cycle.

| Variant | Cycles | Weight | LOAD | FLOW | Startup deficit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unmodified baseline | 865 | 51704 | 1680 | 849 | 76 |
| Both singles, MAD4097, patterns [4,4] | 868 | 51695 | 1683 | 850 | 140 |
| Both singles, MAD4097, patterns [8,8] | 868 | 51688 | 1682 | 850 | 124 |
| Both singles, MAD4097, patterns [0,2] | 866 | 51700 | 1682 | 850 | 140 |
| Previous row plus live scalar32 | 866 | 51704 | 1680 | 849 | 92 |
| FLOW0-4097, native C1, explicit2334 | 867 | 51700 | 1680 | 849 | 108 |
| Previous row, native A and MAD9 | 867 | 51712 | 1680 | 849 | 92 |
| Previous row, native A and single9 | 867 | 51709 | 1680 | 849 | 100 |

## Interpretation

Deriving4097 replaces its broadcast with a multiply-add, but additionally
requires a broadcast of header256. The two single broadcasts save ten
scalar-equivalent arithmetic instructions; the extra256 broadcast costs
eight. The constant and input-address routes then determine whether those
small savings are usable. The successful scalar32 variation restores the
baseline LOAD/FLOW totals, while its startup deficit remains16 operations
larger than main's.

The FLOW0-4097 route preserves the first group's multiply timing, but loses
some work from the second early input vector. Native middle constants fill
some of those early slots while adding arithmetic. None of the measured
tradeoffs reaches864 cycles.

## Evidence

The original `measure.py` builds each candidate and checks a fresh random input against
the unchanged frozen simulator and reference implementation. The five
named result files record61 parameterized configurations, all correct.
`frozen_tests.log` records the full nine-test pass at866 for
`best_parameters.json`. The source retains diagnostic scheduling metadata
only for measurements; it does not inspect runtime input values during
kernel construction.

The full baseline comparison independently reproduced865 cycles,
weight51704, LOAD1680, FLOW849, and scratch1370.

The checkpoint runner uses the repository’s existing frozen test files and simulator. It loads `kernel.py` into a separate Python module without editing the main kernel. The recorded measurement script is retained as experiment provenance.
