"""Cost-filtered legal-ISA branch candidate. This does not change the kernel.

All words and MAD results wrap to 32 bits. Given the existing core word G,
two operations compute the decoded or encoded hash branch bit:

    t = multiply_add(G, 0x80048000, 0x23628000)  # encoded: 0xa3628000
    p = t >> 31

This reduces flag latency, but adds one vector instruction if the full hash
value is still required. It is therefore not a throughput improvement.
"""

import random
import sys

import z3


MASK = 0xFFFFFFFF
C4 = 0xFD7046C5
C5 = 0xB55A4F09


def verify_identity():
    g = z3.BitVec("g", 32)
    e = 9 * g + C4
    h = e ^ z3.LShR(e, 16) ^ C5
    for encoded, constant in ((False, 0x23628000), (True, 0xA3628000)):
        flag = z3.LShR(0x80048000 * g + constant, 31)
        target = ((h ^ C5) if encoded else h) & 1
        solver = z3.SolverFor("QF_BV")
        solver.add(flag != target)
        solver.set(timeout=10000)
        result = solver.check()
        print(f"branch identity encoded={encoded}: {result}", flush=True)
        assert result == z3.unsat


def existing_word_comparison_filter():
    # A failing exact finite witness excludes each listed fixed comparator;
    # this is not a lower bound for changed prefix/core instruction graphs.
    rng = random.Random(760882)
    names = ("a", "q", "a_xor_c1", "b", "left", "right", "core", "e", "e_hi")
    xs = [0, 1, 2, 3, 0x7FFFFFFF, 0xFFFFFFFF]
    xs.extend(rng.getrandbits(32) for _ in range(512))
    data = []
    for x in xs:
        a = (4097 * x + 0x7ED55D16) & MASK
        q = a >> 19
        a_xor_c1 = a ^ 0xC761C23C
        b = a_xor_c1 ^ q
        left = (33 * b + 0xE9F8CC1D) & MASK
        right = (16896 * b + 0xACCF6200) & MASK
        core = left ^ right
        e = (9 * core + C4) & MASK
        hi = e >> 16
        p = (e ^ hi) & 1
        data.append(((a, q, a_xor_c1, b, left, right, core, e, hi), p))
    for count in (7, 8, 9):
        survivors = []
        for i in range(count):
            for j in range(count):
                for op in ("<", "=="):
                    values = [int(w[i] < w[j]) if op == "<" else int(w[i] == w[j])
                              for w, _ in data]
                    for invert in (0, 1):
                        if all(v == (p ^ invert) for v, (_, p) in zip(values, data)):
                            survivors.append((names[i], op, names[j], invert))
            for invert in (0, 1):
                ones = [w[i] for w, p in data if p ^ invert]
                zeros = [w[i] for w, p in data if not (p ^ invert)]
                if min(ones) > max(zeros):
                    survivors.append((names[i], ">constant", max(zeros), invert))
                if max(ones) < min(zeros):
                    survivors.append((names[i], "<constant", min(zeros), invert))
        print(f"comparison survivors from first {count} existing words: {survivors}", flush=True)
        assert not survivors
    return names, data


def existing_word_exotic_filter(names, data):
    # Also test the weaker zero/nonzero convention accepted by vselect and
    # arbitrary two-constant flags usable by a suitably adjusted address MAD.
    operations = {
        "//": lambda a, b: a // b,
        "cdiv": lambda a, b: (a + b - 1) // b,
        "%": lambda a, b: a % b,
        ">>": lambda a, b: a >> b,
        "<<": lambda a, b: ((a << b) & MASK) if b < 32 else 0,
        "<": lambda a, b: int(a < b),
        "==": lambda a, b: int(a == b),
    }
    for parity in (None, 0, 1):
        # a0 equals x0 because the first multiplier is odd and C0 is even.
        subset = [(w, p) for w, p in data if parity is None or (w[0] & 1) == parity]
        survivors = []
        for i in range(len(names)):
            for j in range(len(names)):
                for op, fn in operations.items():
                    try:
                        values = [fn(w[i], w[j]) for w, _ in subset]
                    except ZeroDivisionError:
                        # This input is a legal domain member, so an undefined
                        # instruction already rejects the proposed candidate.
                        continue
                    for invert in (0, 1):
                        if all(bool(v) == bool(p ^ invert)
                               for v, (_, p) in zip(values, subset)):
                            survivors.append((names[i], op, names[j], "truthiness", invert))
                    groups = [{v for v, (_, p) in zip(values, subset) if p == bit}
                              for bit in (0, 1)]
                    if all(len(g) == 1 for g in groups) and groups[0] != groups[1]:
                        survivors.append((names[i], op, names[j], "two_constants"))
        print(f"exotic existing-word flag survivors, input parity={parity}: {survivors}", flush=True)
        assert not survivors


if __name__ == "__main__":
    verify_identity()
    existing_word_exotic_filter(*existing_word_comparison_filter())
