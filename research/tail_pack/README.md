# Deferred packing of the final child records

This alternate kernel also measures **865 cycles** and passes all nine frozen submission tests. It is preserved as an experimental building block; it does not improve the best cycle count.

Compared with the parent kernel, it packs the child records for the final four groups through existing memory staging buffers. It adds four LOADs and 32 STOREs, removes four FLOW instructions, and preserves the 51,704 scalar-equivalent arithmetic count. Reported counts are LOAD 1,684, FLOW 845, STORE 506. The fastest kernel on the main branch remains unchanged.

The dependency graph orders each staging-buffer write after its previous packed read. These dependencies are added in semantic round order so final-round packing does not accidentally become a prerequisite of an earlier round. The compiler computes critical paths in topological order instead of assuming instruction IDs already have that order. The guide preserves the previously validated schedule where possible and places added metadata work into available slots.

From the repository root, run:

```bash
python research/tail_pack/run_frozen.py
```

The runner builds an ordinary instruction schedule and supplies it to the unmodified frozen test harness. It does not change the simulator, test inputs, or the test files. All memory accesses remain in the existing image. The helper files are required only to reproduce this alternate schedule.
