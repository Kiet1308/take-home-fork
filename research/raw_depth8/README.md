# Raw depth-8 representation experiment

This is an ordinary-ISA kernel experiment based on main commit 2a13debc6420b43e65e2f9f16e79836321ffb537 (865 cycles). It is not a faster replacement for main.

The baseline encodes all 256 depth-8 nodes with XOR C5 during setup. This experiment keeps those nodes raw, decodes the 256 round-7 outputs instead, and swaps the round-9 address digit choices to account for the round-7 branch bit becoming raw. The depth-8 child fields use natural left/right order.

A simple raw-field substitution would retain 256 arithmetic copies into the table image. To remove those copies, the experiment loads each eight raw children into a 14-word scratch owner and visits their four parent records in descending scratch order. Each vstore consumes the old child pair while an ordinary ALU operation in that same cycle writes the following encoded parent into the consumed pair. Overlapping memory stores run in increasing address order. The last record uses three scalar stores, preserving the adjacent original depth-9 nodes. Dependencies protect every original tree load before in-place writes.

The compound prepstore nodes exist only inside the scheduler. The emitted machine program contains ordinary ALU and STORE slots; the simulator and frozen tests are untouched.

This movement removes 256 child XOR operations and adds 256 round-7 decode operations. It also adds 66 STORE slots and 65 scalar address operations. The first direct constant-materialization version used 1,739 LOAD and 856 FLOW slots and took 935 cycles. Synthesizing new table addresses using existing pointers restored 1,680 LOAD and 849 FLOW, but an uncombined overwrite chain took 929 cycles. Combining a store with its succeeding overwrite reduced the default to 889 cycles. An eight-point setup critical-path weight sweep found a best of 877 cycles, still slower than main.

## Reproduce

Run `python path/to/this/folder/run_frozen.py`. The runner locates the enclosing repository (or the sibling `take-home-fork` workspace checkout), imports this kernel, and runs the unchanged `tests/submission_tests.py` and frozen simulator. For the eight-point fresh-input sweep, run `python path/to/this/folder/measure.py path/to/this/folder/cp_grid.json`.

`kernel.py` is the final combined setup implementation. `raw_depth8_935.py` and `raw_depth8_929.py` preserve the simpler intermediate implementations. `results.json` contains every sweep result, including the scratch overflow at weight zero. `best_parameters.json` selects weight one.

## Recorded measurements

| Implementation | Cycles | Scratch | ALU | VALU | Arithmetic weight | LOAD | FLOW | STORE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Main baseline | 865 | 1370 | 10328 | 5172 | 51704 | 1680 | 849 | 474 |
| Separate raw stores and flexible constants | 935 | 1399 | 9767 | 5242 | 51703 | 1739 | 856 | 540 |
| Separate raw stores and ALU addresses | 929 | 1512 | 9305 | 5308 | 51769 | 1680 | 849 | 540 |
| Combined stores, setup weight 0.05 | 889 | 1513 | 9905 | 5233 | 51769 | 1680 | 849 | 540 |
| Combined stores, setup weight 1 | 877 | 1429 | 10143 | 5203 | 51767 | 1680 | 851 | 540 |

Arithmetic weight is ALU + 8 * VALU. The last configuration places two more existing constants in FLOW than the weight-0.05 configuration, which lowers arithmetic by two. Every successful sweep entry passed a fresh complete generated input. The 877-cycle configuration passed all nine untouched frozen tests; see `frozen_tests.log`.

## Reusing the combined store and overwrite

The machine reads every operand at the start of a cycle and commits writes at the end. A vector store may therefore consume the old raw child pair from a scratch word in the same cycle that an ALU XOR writes the encoded parent of the next record into that word. The scheduler's `prepstore` node binds those two ordinary slots together and consumes one STORE plus one ALU slot. Its destination write updates `ir.last`, and the following record store depends on that node. This avoids a separate store-to-overwrite dependency cycle for each record.

The constructor must retain three constraints: all meaningful source fields must be initialized before the combined node; the overwritten scratch word must have no later consumer that expects its old value; and overlapping destination-memory stores must run in their intended order after every original tree load they would destroy. The last record must also avoid writing beyond the prepared table into the adjacent raw depth-9 data. This experiment handles that last boundary with three scalar stores.
