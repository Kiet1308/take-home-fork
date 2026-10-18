# Raw-boundary reassociation and constant gauges

None of these variants improves the validated 865-cycle kernel.

`delay_r8.py` retains H XOR C5 after round8, inverts the outer depth9 pointer
selection to account for the complemented branch bit, and applies C5 before
the next gathered node XOR. This preserves the exact arithmetic count but
changes dependencies. It compiles to866 cycles, versus865 for `baseline.py`,
both with51704 scalar-equivalent arithmetic operations. Simply moving this
correction does not remove it: the next MAD still requires the corrected
input.

`free_gauges.py` generates eight exact constant transformations. These
include complementing both middle affine branches, complementing one branch
with the matching final-MAD correction, and applying the final-MAD MSB
gauge. Every generated hash passed1028 independent arbitrary32-bit identity
checks. Complete compiler counts are in `free_gauges_results.json`.

The identity and both-branch complement variants compile to865 at51704
arithmetic equivalents. Single-branch complements compile to866 at51703,
with one additional LOAD. These candidates were not promoted, and no new
full frozen-suite pass is claimed for them.

To regenerate the gauge variants and repeat the identity/count checks:

```bash
python research/boundaries/free_gauges.py
```

The generator uses the saved baseline corresponding to main commit
`2a13debc6420b43e65e2f9f16e79836321ffb537`, without changing main or any test.
