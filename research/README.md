# Optimization research checkpoint — 865 cycles

The implementation at the parent commit `2a13debc6420b43e65e2f9f16e79836321ffb537` passes all nine frozen submission tests and measures **865 simulated cycles**. The requested target is **strictly below 850**; it has **not** been reached. This branch records reproducible investigations without changing the validated kernel, simulator, or tests.

## Current resource measurements

| Resource | Instructions / scalar-equivalent work |
|---|---:|
| ALU | 10,328 |
| VALU | 5,172 |
| LOAD | 1,680 |
| FLOW | 849 |
| STORE | 474 |
| Scratch words | 1,370 |
| ALU + 8 × VALU | 51,704 |

The arithmetic engines jointly execute at most 60 scalar-equivalent operations per cycle. Cycles 4 through 860 use all 60. The measured unused arithmetic capacity is 76 at startup and 120 in the final four cycles. LOAD uses both slots in every cycle from 0 through 839. Therefore apparent unused LOAD and FLOW slots near the end cannot automatically replace constants needed early in the kernel.

`python research/constant_routing_bound.py` derives a **conditional** bound for this exact instruction dependency graph. At 864 cycles, the graph's constant deadlines permit at most nine constants on LOAD and nine on FLOW. At least 123 constants must use ALU. Its resulting arithmetic requirement, including a conservative startup and final-output dependency bound, exceeds the 864-cycle capacity by 21 scalar-equivalent operations. This does not exclude a changed instruction graph, changed memory layout, or a kernel below 850.

## Hash identity investigations

`hash/verified_results.md` describes exact finite witness checks, bit-vector `UNSAT` results, composed mathematical arguments, and their limitations. It explicitly distinguishes proved family exclusions from timeouts. The scripts cover several ordinary MAD/shear hash topologies, parity specialization, restricted state encodings, and cores that reuse live prefix intermediates. No mathematical search recorded here produced a faster kernel, and no result proves a global instruction-count lower bound.

To reproduce the lightweight checks:

```bash
cd research/hash
python -m pip install -r requirements.txt
python rawnode_top2_witnesses.py
python quarter_mask_lemma.py
python free_parity_encoding_influence.py
python core_mask_parity.py --width 12 --m3 free
```

The other scripts and command options are documented in `verified_results.md`; some synthesis modes may take minutes or return `UNKNOWN`. Scripts use their own deterministic witness samples to disprove instruction identities. They do not inspect or specialize the benchmark's randomized inputs.

## Next work

The target still requires a meaningful change to the arithmetic or memory-access graph. Current independent investigations include shorter hash topologies, alternative deep-tree records, and using late memory packing to reduce FLOW pressure. Correctness and cycle claims for kernel changes must continue to be verified using the unmodified `python tests/submission_tests.py` harness before replacing the best implementation.
