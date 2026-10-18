"""Exact 2/5/8 triple-record layout and its resource audit.

This is an independently checkable layout experiment, not a replacement kernel.
It stays inside the frozen 2,566-word memory image and uses 32-bit arithmetic.
"""

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys


MEMORY_WORDS = 2566
MASK = (1 << 32) - 1


def signed_bit(bit):
    return MASK - 1 + bit


def mad(a, b, c):
    return (a * b + c) & MASK


def make_layout():
    records = {}
    anchors = {}
    p2_indices = [6, 16, 26, 36]
    first_tiles = {}
    for path in range(32):
        q0, q1, q2, q3, q4 = [(path >> b) & 1 for b in range(4, -1, -1)]
        p2 = 48 + 40 * p2_indices[2 * q0 + q1]
        a2 = p2 + 200
        p5 = mad(signed_bit(q4), 120 if q3 else 80, a2 if q2 else p2)
        first_tiles[path] = (p5 - 48) // 40
        records[2, 2 * q0 + q1] = p2
        anchors[2, 2 * q0 + q1] = a2
        records[5, path] = p5
    assert len(set(first_tiles.values())) == 32
    remaining = sorted(set(range(64)) - set(first_tiles.values()))
    for path, second_tile in enumerate(remaining):
        anchors[5, path] = 48 + 40 * second_tile
        for q5 in range(2):
            for q6 in range(2):
                for q7 in range(2):
                    p5 = records[5, path]
                    a5 = anchors[5, path]
                    p8 = mad(signed_bit(q7), 24 if q6 else 16, a5 if q5 else p5)
                    records[8, (path << 3) | (q5 << 2) | (q6 << 1) | q7] = p8

    # Breadth-first ascending child/grandchild fields enable raw vload views.
    # All upper records additionally contain an anchor in their eighth word.
    fields = {}
    payload = {}
    for (depth, path), address in records.items():
        node = (1 << (depth + 1)) - 2 - path
        record = [('tree', 2 * node + 1), ('tree', 2 * node + 2)]
        record += [('tree', 4 * node + k) for k in (3, 4, 5, 6)]
        record += [('tree', node)]
        if depth < 8:
            record += [('anchor', anchors[depth, path])]
        fields[depth, path] = record
        assert 0 <= address and address + 7 < MEMORY_WORDS
        for offset, value in enumerate(record):
            location = address + offset
            assert location not in payload, (location, payload.get(location), value)
            payload[location] = value

    reserved_indices = set(first_tiles.values()) | set(p2_indices)
    staging = []
    for grid_index in range(63):
        if grid_index in reserved_indices:
            continue
        address = 48 + 40 * grid_index
        assert all(address + k not in payload for k in range(8))
        staging.append(address)
        if len(staging) == 4:
            break
    assert len(staging) == 4
    return records, anchors, fields, payload, staging


def check_layout():
    records, anchors, fields, payload, staging = make_layout()
    nodes = [value for kind, value in payload.values() if kind == 'tree']
    assert sorted(nodes) == list(range(3, 2047))
    assert len(nodes) == len(set(nodes))
    assert Counter(depth for depth, _ in records) == {2: 4, 5: 32, 8: 256}
    assert len(payload) == 2080
    assert max(payload) == 2558
    for (depth, path), record in fields.items():
        node = (1 << (depth + 1)) - 2 - path
        for first in range(2):
            for second in range(2):
                child = 2 * node + (1 if first else 2)
                grandchild = 2 * child + (1 if second else 2)
                assert record[1 - first] == ('tree', child)
                assert record[2 + 3 - 2 * first - second] == ('tree', grandchild)

    # Four depth-8 parents have eight consecutive depth-9 children. Reuse that
    # parent-pair buffer backwards. A grandchild vload overwrites only pairs
    # already consumed, and the encoded root occupies the next padding word.
    # This validates ordinary scratch semantics without an ALU raw-data copy.
    checks = 0
    original = [(i * 0x9E3779B9 + 0xB5297A4D) & MASK for i in range(2047)] + [0] * 16
    for first_parent in range(255, 511, 4):
        scratch = original[2 * first_parent + 1:2 * first_parent + 9] + [0] * 16
        for pair in (3, 2, 1, 0):
            parent = first_parent + pair
            start = 2 * pair
            scratch[start + 2:start + 10] = original[4 * parent + 3:4 * parent + 11]
            # Last raw vload may include subsequent indices; only the first
            # four raw-grandchild words are used, all within the actual tree.
            scratch[start + 6] = original[parent] ^ 0xB55A4F09
            got = scratch[start:start + 7]
            want = original[2 * parent + 1:2 * parent + 3]
            want += original[4 * parent + 3:4 * parent + 7]
            want += [original[parent] ^ 0xB55A4F09]
            assert got == want, (parent, got, want)
            checks += 1

    return {
        'status': 'layout and local zero-copy preparation verified',
        'records': {'depth2': 4, 'depth5': 32, 'depth8': 256},
        'payload_words': len(payload),
        'memory_words': MEMORY_WORDS,
        'highest_meaningful_word': max(payload),
        'highest_vload_word': max(records.values()) + 7,
        'staging_addresses': staging,
        'preparation_records_checked': checks,
        'deep_preparation': {'LOAD': 320, 'STORE': 256, 'encoded_root_XOR': 256, 'raw_copy_ALU': 0},
        'ideal_walk': {'pointer_weighted': 512, 'pointer_savings_vs_baseline': 1024, 'FLOW': 896, 'record_LOAD': 1024},
        'blockers': [
            '896 ideal walk FLOW already exceeds the 849-cycle target before setup.',
            'The ideal FLOW assumes four fully transposed grandchild vectors.',
            'The best concrete local grandchild packing found costs six FLOW, eight STORE, and two LOAD before preserving or selecting children.',
            'The local preparation proof does not yet schedule global in-place source/destination hazards under the 1536-word scratch limit.',
            'Preparation counts exclude pointer-constant materialization and the already-required first-511-node reads.',
        ],
    }


def check_frozen_isa():
    """Execute the local preparation on the untouched submission simulator."""
    frozen_file = Path(__file__).resolve().parents[1] / 'take-home-fork/tests/frozen_problem.py'
    if not frozen_file.exists():
        frozen_file = Path(__file__).resolve().parents[2] / 'tests/frozen_problem.py'
    spec = importlib.util.spec_from_file_location('triple_layout_frozen_problem', frozen_file)
    frozen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = frozen
    spec.loader.exec_module(frozen)
    original = [(i * 0x9E3779B9 + 0xB5297A4D) & MASK for i in range(2047)]
    initial = [0] * MEMORY_WORDS
    initial[7:2054] = original
    checked = 0
    for first_parent in range(255, 511, 4):
        program = [
            {'load': [('const', 32, 7 + 2 * first_parent + 1)]},
            {'load': [('vload', 0, 32)]},
            {'load': [('const', 36, 7 + first_parent)]},
            {'load': [('vload', 40, 36)]},
            {'load': [('const', 35, 0xB55A4F09)]},
        ]
        for pair in (3, 2, 1, 0):
            parent = first_parent + pair
            start = 2 * pair
            program += [
                {'load': [('const', 33, 7 + 4 * parent + 3)]},
                {'load': [('vload', start + 2, 33)]},
                {'alu': [('^', start + 6, 40 + pair, 35)]},
                {'load': [('const', 34, 2054 + 8 * pair)]},
                {'store': [('vstore', 34, start)]},
            ]
        machine = frozen.Machine(initial, program, frozen.DebugInfo({}))
        machine.enable_pause = False
        machine.enable_debug = False
        machine.run()
        for pair in range(4):
            parent = first_parent + pair
            want = original[2 * parent + 1:2 * parent + 3]
            want += original[4 * parent + 3:4 * parent + 7]
            want += [original[parent] ^ 0xB55A4F09]
            assert machine.mem[2054 + 8 * pair:2061 + 8 * pair] == want
            checked += 1
    return {'records_checked': checked, 'scratch_highest_used_word': 47, 'simulator': str(frozen_file)}


if __name__ == '__main__':
    report = check_layout()
    report['frozen_isa_preparation'] = check_frozen_isa()
    print(json.dumps(report, indent=2))
