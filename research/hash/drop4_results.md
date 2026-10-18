# C1-deleted core with live prefix operands

This check permits a four-operation replacement for the current middle
core, while deleting the prefix XOR with C1. At the low12-bit projection,
let `x=a XOR (a>>19)` and `q=a>>19`. These two low12-bit words are
independently free over legitimate 32-bit values of the invertible first
MAD. The target is `G(x XOR C1)`.

The replacement has two MADs, one XOR/AND/OR combining their outputs, and
a final MAD. Each MAD may choose its input and additive operand from the
live words `x`, `x XOR q`, and `q`, or an arbitrary constant. Its multiplier
may likewise be a live word or arbitrary constant. The second MAD can
also use the first MAD's output as either multiplicand or its addend;
the final MAD may use either earlier MAD as its additive operand.
An arbitrary output XOR mask is allowed mathematically, without adding
to the candidate's instruction budget.

`drop4_partitions.py` calls the existing `prefix_core_search.py` with this
scope. Both complete AND and OR models are `UNSAT` on100 exact finite
witness pairs. Direct unpartitioned XOR synthesis timed out, so it is
split into exhaustive cases:

| Partition | Number of cases | Result |
| --- | ---: | --- |
| First multiplier is a live word | 3 | All UNSAT |
| First multiplier constant, second multiplier a live word or first MAD | 4 | All UNSAT |
| First two multipliers constant, final multiplier a live word | 3 | All UNSAT |
| All multipliers constant, final addend a live word or earlier MAD | 5 | All UNSAT |

The first seven cases were rerun with100 finite witness pairs and are
preserved in `drop4_first_partitions.log`, together with the AND/OR runs.
The last eight were checked with104 pairs; their outputs are preserved
in `root_drop4_outer.log` and `root_drop4_finish.log`.

The one remaining partition has three constant multipliers and a
constant final addend. Set `q=0`. Then both earlier MADs are affine
functions of `x`, even when one depends on the other. The residual
function is therefore

```
m3 * ((m1*x+c1) XOR (m2*x+c2)) + c3 XOR output_mask.
```

This is the already excluded `core_mask_parity.py --width 12 --m3 free`
family. Its parity normalizations are necessary: a bijective target
requires odd `m3` and precisely one odd inner multiplier; swapping the
XOR branches makes that the first multiplier. The residual direct
synthesis run returned `UNKNOWN`, which is explicitly retained in its
log; the independent q=0 reduction supplies the exclusion.

This closes the stated four-operation core family, including its live
prefix operands. It does not establish a global nine-operation lower
bound and did not produce a faster executable kernel.
