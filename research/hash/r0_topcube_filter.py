"""Exact necessary high-input-cube tests for the 30-bit round-zero domain.

A candidate bit of MAD(m, x XOR K, C), with v2(m) removed, restricted
to the highest k genuine input bits has a small complete truth table.
We enumerate every relevant odd multiplier residue, input XOR mask and
base for that table.  Bases are allowed to vary independently between
low-input centers, making rejection a rigorous necessary-condition test.
"""
import argparse
import json
import random
import time

def hash_value(x):
    mask = (1 << 32) - 1
    a = (4097*x + 0x7ed55d16) & mask
    b = a ^ (a >> 19) ^ 0xc761c23c
    d = ((33*b + 0xe9f8cc1d) & mask) ^ ((16896*b + 0xaccf6200) & mask)
    e = (9*d + 0xfd7046c5) & mask
    return e ^ (e >> 16) ^ 0xb55a4f09


def inverse_tail_bit(x, last):
    y = hash_value(x)
    return sum((y >> j) & 1 for j in range(0, 32, last)) & 1


def derivative_filter(samples=96):
    rng = random.Random(115237)
    xs = [0, 1, (1 << 30)-1, 0x15555555, 0x2aaaaaaa]
    xs += [rng.getrandbits(30) for _ in range(samples)]
    observed = {(last, j): set() for last in range(1, 33) for j in range(1, 30)}
    for x in xs:
        for j in range(1, 30):
            dh = hash_value(x) ^ hash_value(x ^ (1 << j))
            for last in range(1, 33):
                observed[last, j].add(sum((dh >> q) & 1 for q in range(0, 32, last)) & 1)
    survivors = []
    for effective in range(0, 32):
        for last in range(1, 33):
            if 1 <= effective < 30 and observed[last, effective] != {1}:
                continue
            if any(observed[last, j] != {0} for j in range(max(effective+1, 1), 30)):
                continue
            survivors.append((effective, last))
    print(json.dumps(dict(derivative_survivors=survivors)), flush=True)
    return survivors


def filter_cases(k=5, samples=20):
    low = 30 - k
    rng = random.Random(20261018)
    centers = [0, 1, (1 << low) - 1, 0x15555555 & ((1 << low) - 1)]
    centers += [rng.getrandbits(low) for _ in range(max(0, samples-len(centers)))]
    rows = []
    for effective in (30, 31):
        bits = effective - low + 1
        modulus = 1 << bits
        sign = modulus >> 1
        t0 = time.monotonic()
        by_table = {}
        for m in range(1, modulus, 2):
            for c in range(modulus):
                table = sum((bool((m*z+c) & sign) << z) for z in range(1 << k))
                by_table.setdefault(table, set()).add(m)
        for last in range(1, 33):
            candidates = None
            for ci, center in enumerate(centers):
                vals = [inverse_tail_bit(center | (z << low), last) for z in range(1 << k)]
                current = set()
                for key in range(1 << k):
                    signature = sum(vals[z ^ key] << z for z in range(1 << k))
                    current.update((m, key) for m in by_table.get(signature, ()))
                candidates = current if candidates is None else candidates & current
                if not candidates:
                    break
            row = dict(effective=effective, last=last, top_bits=k,
                       tested_centers=ci+1, surviving=len(candidates),
                       residues=sorted(candidates), seconds=round(time.monotonic()-t0, 3))
            rows.append(row)
            print(json.dumps(row), flush=True)
    return rows


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--top-bits', type=int, default=5)
    p.add_argument('--samples', type=int, default=20)
    p.add_argument('--output', default='r0_topcube_results.json')
    o = p.parse_args()
    derivative_filter()
    rows = filter_cases(o.top_bits, o.samples)
    with open(o.output, 'w') as f:
        json.dump(rows, f, indent=2)
        f.write('\n')
