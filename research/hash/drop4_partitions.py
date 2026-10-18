"""Reproduce finite exclusions for a C1-deleted, four-operation hash core.

The residual all-constant coefficient/addend case reduces at q=0 to
core_mask_parity.py with --width 12 --m3 free.  This driver deliberately
does not turn the residual direct-synthesis timeout into a proof.
"""
import argparse
from prefix_core_search import solve


def partitions():
    for co1 in (1, 2, 3):
        yield {"co1": co1}
    for co2 in (1, 2, 3, 4):
        yield {"co1": 0, "co2": co2}
    for co3 in (1, 2, 3):
        yield {"co1": 0, "co2": 0, "co3": co3}
    for a3 in (1, 2, 3, 4, 5):
        yield {"co1": 0, "co2": 0, "co3": 0, "a3": a3}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=120000)
    parser.add_argument("--samples", type=int, default=76)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=15)
    parser.add_argument("--and-or", action="store_true")
    args = parser.parse_args()
    for fixes in list(partitions())[args.start:args.stop]:
        solve("drop4", args.timeout, args.samples, True, fixes,
              "xor", True, True, True)
    if args.and_or:
        for operation in ("and", "or"):
            solve("drop4", args.timeout, args.samples, True, None,
                  operation, True, True, True)
