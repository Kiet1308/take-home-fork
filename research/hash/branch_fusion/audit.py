"""Audit existing parity consumers and verify compact-state identities.

Run from any location with an optional path to the unmodified take-home repo:
    python audit.py /path/to/take-home-fork

This does not modify or monkey-patch simulator behavior. The temporary IR
wrapper only inspects the generated dependency graph after normal compilation.
"""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import random
import sys


def discover_repo():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    for parent in Path(__file__).resolve().parents:
        for candidate in (parent, parent / "take-home-fork"):
            if (candidate / "perf_takehome.py").is_file() and (candidate / "problem.py").is_file():
                return candidate
    raise FileNotFoundError("Pass the take-home repository path as the first argument.")


ROOT = discover_repo()
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("branch_audit_kernel", ROOT / "perf_takehome.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

captured = {}
original_compile = module.IR.compile


def capture_compile(ir):
    result = original_compile(ir)
    captured["nodes"] = ir.nodes
    return result


module.IR.compile = capture_compile
kernel = module.KernelBuilder()
kernel.build_kernel(10, 2047, 256, 16)
nodes = captured["nodes"]
flags = [n for n in nodes if n[5] is not None and n[1][0] in ("%", "|")]
flags_by_round = Counter()
flags_by_opcode = Counter()
for node in flags:
    flags_by_round[node[5][1]] += len(node[7]) / 8
    flags_by_opcode[node[1][0]] += len(node[7]) / 8
flags_by_round = Counter({k: int(v) for k, v in flags_by_round.items()})
flags_by_opcode = Counter({k: int(v) for k, v in flags_by_opcode.items()})
flows_by_round = Counter(n[5][1] for n in nodes if n[0] == "flow" and n[5] is not None)
assert sum(flags_by_round.values()) == 448
assert flags_by_opcode == {"%": 352, "|": 96}
assert set(flags_by_round) == set(range(10)) | set(range(11, 15))
assert all(v == 32 for v in flags_by_round.values())

MASK = (1 << 32) - 1
C4 = 0xFD7046C5
BRANCH_M = 0x80048000
BRANCH_B_ENCODED = 0xA3628000
BRANCH_B_RAW = 0x23628000


def u32(x):
    return x & MASK


def encoded_tail(d):
    e = u32(9 * d + C4)
    return e, e ^ (e >> 16)


def restore_from_ehalf(state, parity):
    low = parity ^ ((state >> 15) & 1)
    e = u32((state << 1) | low)
    return e ^ (e >> 16)


rng = random.Random(0xB4A6C)
witnesses = [0, MASK, 1, 2, 3, 0x7FFFFFFF, 0x80000000]
witnesses += [1 << k for k in range(32)]
witnesses += [MASK ^ (1 << k) for k in range(32)]
witnesses += [rng.getrandbits(32) for _ in range(100000)]
for d in witnesses:
    e, h = encoded_tail(d)
    parity = u32(d * BRANCH_M + BRANCH_B_ENCODED) >> 31
    parity_raw = u32(d * BRANCH_M + BRANCH_B_RAW) >> 31
    assert parity == h & 1
    assert parity_raw == (h ^ 0xB55A4F09) & 1
    assert restore_from_ehalf(e >> 1, parity) == h
    assert (e >> 1) ^ (e >> 17) == h >> 1

counts = Counter()
for instruction in kernel.instrs:
    for engine, slots in instruction.items():
        counts[engine] += len(slots)
report = {
    "baseline_cycles": len(kernel.instrs),
    "scratch_peak": kernel.scratch_ptr,
    "instruction_counts": counts,
    "flow_instructions_excluding_pause": counts["flow"] - sum(slot[0] == "pause" for instruction in kernel.instrs for slot in instruction.get("flow", [])),
    "arithmetic_scalar_equivalent": counts["alu"] + 8 * counts["valu"],
    "parity_vectors": sum(flags_by_round.values()),
    "parity_scalar_equivalent": sum(len(n[7]) for n in flags),
    "parity_vectors_by_round": dict(sorted(flags_by_round.items())),
    "parity_vectors_by_opcode": flags_by_opcode,
    "flow_nodes_by_round": dict(sorted(flows_by_round.items())),
    "compact_state_identity_witnesses": len(witnesses),
    "compact_state_identity_checks": "PASS",
    "per_hash_operation_accounting": {
        "ordinary_encoded_h_and_flag": 11,
        "hhalf_and_flag_before_node_preparation": 12,
        "hhalf_using_separate_branch_identity_before_node_preparation": 13,
        "ehalf_and_flag_and_next_input_conversion_before_node_preparation": 13,
        "existing_node_xor_excluded_from_all_three": True,
    },
    "scope": "The checks verify identities and exact baseline consumers. They are not a general instruction lower bound.",
}
print(json.dumps(report, indent=2))
