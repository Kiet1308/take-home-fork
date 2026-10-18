# Mixed record layout audit

This checkpoint contains accounting for concrete mixed layouts considered from
the validated 865-cycle kernel. It does not contain an improved kernel, and the
counts do not establish a lower bound on other layouts or instruction sequences.

Run `python resource_audit.py` to reproduce `resource_audit.json`.

## Upper triples: the p3 dependency matters

Replacing only the second-pass depths 2--4 with a seven-field triple could remove
the 32 p3 pointer MADs, or 256 scalar-equivalent arithmetic operations. With fully
aligned descendants, its seven FLOWs per vector match the existing three FLOWs
for depth2, two for the p3 pointer, and two for native depth4 selection.

The same arithmetic saving does **not** apply in the first pass while retaining
the current depth5 formula: `p5 = p3 + signed_b4 * V[b3]`. It still needs p3. The
two FLOW selectors and MAD that create p3 merely move to round5. An initial
estimate of 512 arithmetic saved across both passes was therefore wrong. Supplying
two p3 metadata alternatives alongside the seven tree fields would require nine
words; it no longer fits in one eight-word load.

There is also a concrete packing cost. A stride-one native loading chain retains
one field for all eight walkers. Packing the other five descendant fields takes
40 scalar STOREs and five vloads per event. For all32 tail events, this alone
adds160 LOADs and1280 STOREs. Even before any new setup, that produces1840 LOADs
and1754 STOREs, each exceeding the1698 slots available in849 cycles.

Packing fewer columns retains interleaved fields. Such fields need additional
FLOWs to select across their partial lane sets, or scalar arithmetic to align
them. No implementation was found that pays those costs within the available
budgets. The five-column counter is for the fully aligned implementation; it is
not asserted to be a minimum for every possible packing scheme.

## Lower triples at depths7--9

An eight-word record can contain the encoded depth7 parent, its two encoded
depth8 children, four raw depth9 grandchildren, and padding. The depth7 record
pointer can use stride8, so a direct depth10 pointer can recover the leaf path
without first creating p9. This removes256 arithmetic operations.

The exact simple FLOW count is13 per vector: two for p7, one for the child, three
for the grandchild, and seven for the three-bit leaf digit. The current corresponding
count is seven for ordinary native records. One existing depth7 event is already
packed and saves a FLOW; accounting for its replacement, the change adds193 FLOWs.

A favorable local preparation construction reads each group of eight depth8
children, encodes those required children, and processes four records in reverse
order. For each record, it loads four raw grandchildren into the following words,
places the encoded parent after them, then stores the record. Counting reuse of
the original first511 source reads, this adds128 data LOADs and increases image
STOREs by64. It avoids scalar copies of the512 raw grandchildren. Global in-place
memory hazards and new pointer constants have not been scheduled and are omitted
from the optimistic counter.

Combining that preparation with the fully aligned five-column packing gives1711
LOADs,1042 FLOWs, and1810 STOREs, before omitted setup. The counter subtracts the
one LOAD and eight STOREs of the existing packed depth7 event126 that this layout
replaces. This concrete variant is
over capacity in all three engines.

For the both-pass upper variant, the counter likewise removes the existing
packed events0,4,12, including their LOADs, STOREs, and FLOW savings.

## Other checks

Rearranging raw depth9 parent/leaf pairs offers a nominal256-pointer-arithmetic
saving, but the no-copy preparation considered needs192 data LOADs and1024 STOREs.
Those stores also require roughly1024 distinct destination addresses, with only
a fraction shared with its192 source block addresses. Materializing this address
set must be included; counting only data movements understates the setup cost.
Taking a static fraction of the tree scales this particular setup cost and the
runtime saving together. A different address reuse construction could change
that result, but none was found here.

No simulator or test files were changed.
