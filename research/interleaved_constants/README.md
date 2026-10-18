# SIMD constant interleaving — 866-cycle experiment

This is an alternate legal-ISA kernel, retained as a reproducible experiment.
It does not replace the validated865-cycle main implementation and does not
meet the requested strictly-below850 target.

The middle hash core computes an XOR of two affine branches. Swapping those
branches in alternate SIMD lanes leaves every lane result unchanged. Their
coefficient and bias vectors can consequently share nine-word alternating
patterns: vector views at offsets0 and1 are the two opposite orientations.
This removes the two deinterleaving vselects that a conventional paired
constant broadcast requires.

The saved parameter set constructs each pattern with four scalar memory
stores, one ordinary vload, and four scratch copies. Explicit dependencies
order the replacements after the vload's real writes. The coefficient
pattern also overlaps the fixed alternating condition mask at its final
word. Scratch words that are not meaningful payload remain reserved when
required by actual vector writes.

Measured resource counts:

| Resource | Count |
| --- | ---: |
| Cycles | 866 |
| ALU | 10297 |
| VALU | 5175 |
| ALU +8*VALU | 51697 |
| LOAD | 1682 |
| FLOW | 850 |
| STORE | 474 |
| Scratch words | 1349 |

The lower arithmetic count does not translate into a faster schedule:
constant availability and extra memory traffic leave it one cycle behind
main. The saved partial-pattern kernel passes all nine unmodified frozen tests,
each at866 cycles; see frozen_validation.log. Both direct and partial patterns
also received independent frozen single-seed checks during development. Run the complete unmodified frozen
harness through this loader:

```bash
python research/interleaved_constants/run_frozen.py
```

The loader imports this alternate kernel into the existing test harness.
It does not alter the simulator, tests, runtime data, or main kernel file.
