"""Scoped counters for three concrete mixed-record proposals.

These are accounting models, not implementations or lower bounds over all ISA
programs.  Preparation is omitted where it has not been scheduled; such rows
are explicitly optimistic.  Baseline counts are the validated main865 kernel.
"""

import json
from pathlib import Path

BASELINE = dict(cycles=865, arithmetic=51704, load=1680, flow=849, store=474)
TARGET_CYCLES = 849
CAPACITY = dict(arithmetic=60 * TARGET_CYCLES,
                load=2 * TARGET_CYCLES,
                flow=TARGET_CYCLES,
                store=2 * TARGET_CYCLES)


def row(name, arithmetic=0, load=0, flow=0, store=0, **notes):
    delta = dict(arithmetic=arithmetic, load=load, flow=flow, store=store)
    counts = {k: BASELINE[k] + v for k, v in delta.items()}
    return dict(name=name, delta=delta, optimistic_counts=counts,
                exceeded={k: value - CAPACITY[k] for k, value in counts.items()
                          if value > CAPACITY[k]}, **notes)


def audit():
    # A stride-one record-loading chain retains its first descendant field
    # without copying.  Fully aligning the other five fields costs five sets
    # of eight scalar STOREs plus five vloads.  Once aligned, child selection
    # costs one FLOW and grandchild selection costs three FLOWs.
    packed_loads = 5
    packed_stores = 5 * 8
    tail = row(
        "Only second-pass depths 2--4, fully packed six descendant fields",
        arithmetic=-32 * 8, load=32 * packed_loads,
        store=32 * packed_stores,
        selected_events=32,
        omitted="All new layout, address, and metadata preparation costs",
        flow_per_event=dict(old=3 + 2 + 2, new=3 + 1 + 3),
        pointer_note="The second-pass p3 has no later consumer and can vanish.")

    both = row(
        "Both passes of depths 2--4, retaining the existing p5 formula",
        arithmetic=-32 * 8, load=64 * packed_loads - 3,
        flow=32 * 2 + 3, store=64 * packed_stores - 3 * 8,
        selected_events=64,
        replaced_baseline_packed_events=[0, 4, 12],
        omitted="All new layout, address, and metadata preparation costs",
        pointer_note=("First-pass p5 = p3 + signed_b4 * V[b3] still requires "
                      "p3, including its MAD and two selector FLOWs.  Moving "
                      "p3 computation to round5 does not remove its cost."))

    deep = row(
        "Depths 7--9 triples, direct depth10 pointer, fully packed descendants",
        arithmetic=-32 * 8,
        load=-32 * 8 + 128 + 32 * packed_loads - 1,
        flow=32 * ((2 + 1 + 3 + 7) - (2 + 2 + 3)) + 1,
        store=64 + 32 * packed_stores - 8,
        selected_events=32,
        replaced_baseline_packed_events=[126],
        omitted=("New address constants, global in-place preparation hazards, "
                 "and scheduling costs"),
        setup=("Optimistically reuses the original first511 source loads; "
               "adds128 vloads for groups of four raw depth9 grandchildren. "
               "The128 new eight-word record stores replace64 old image stores."),
        flow_per_event=dict(old=2 + 2 + 3, new=2 + 1 + 3 + 7),
        pointer_note=("p7 stride8 can encode the depth7 path for direct leaf "
                      "addressing.  Selecting its three-bit depth10 digit "
                      "uses seven FLOWs in this implementation."))

    return dict(baseline=BASELINE, target_cycles=TARGET_CYCLES,
                resource_capacities=CAPACITY,
                scope="Named implementations only; no general impossibility claim",
                proposals=[tail, both, deep])


if __name__ == "__main__":
    result = audit()
    out = Path(__file__).with_name("resource_audit.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
