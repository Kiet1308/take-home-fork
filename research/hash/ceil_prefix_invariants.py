"""Exact invariants for x XOR ceil(MAD(x)/D) before a right-shear tail.

This verifies the finite parts of the proof in verified_results.md.  The
remaining nonzero-correlation divisors are excluded independently by
final19_edges.cpp and ceil_final19_influences.cpp.  Power-of-two divisors
reduce to shift_pair_influence.py and first_triangular.py branch_shift.
No simulator or benchmark data is used.
"""
import math
import numpy as np

from shift_pair_influence import h, C0, C1, A, B, C4, C5, MASK

N = 1 << 32


def inverse_shear_mask(s):
    return sum(1 << j for j in range(0, 32, s))


def parity(v):
    out = np.zeros(v.size, dtype=np.uint8)
    while np.any(v):
        out ^= (v & np.uint64(1)).astype(np.uint8)
        v >>= np.uint64(1)
    return out


def reference_correlations():
    """All correlations with input parity, using only a 20-bit sum.

    Since G is an odd triangular permutation, x0 expressed in e=G(b)
    depends only on e low20 and toggles when e19 is flipped. Thus every
    Walsh coefficient with a bit above19 or without bit19 vanishes.
    """
    masks = {}
    for s in range(1, 33):
        before = inverse_shear_mask(s)
        after = (before ^ (before << 16)) & MASK
        if after >> 20 or not (after & (1 << 19)):
            masks[s] = 0
        else:
            assert s == 19 and after == (1 | (1 << 16) | (1 << 19))
            b = np.arange(1 << 20, dtype=np.uint64)
            e = (np.uint64(9) * ((np.uint64(33)*b+A) ^
                 (np.uint64(16896)*b+B)) + C4) & np.uint64(MASK)
            x0 = ((b ^ (b >> np.uint64(19)) ^ C1 ^ (C1 >> 19) ^ C0)
                  & np.uint64(1)).astype(np.uint8)
            out0 = parity(e & np.uint64(after))
            out0 ^= (C5 & before).bit_count() & 1
            signs = (x0 ^ out0).astype(np.int64)
            masks[s] = int(np.sum(1-2*signs)) * (1 << 12)
    assert {s: abs(v) for s, v in masks.items() if v} == {19: 1343488}
    print('Reference nonzero correlations:', {s:v for s,v in masks.items() if v})
    return masks


def ceil_balance(n, d):
    residue = (n-1) % (2*d)
    return 1-min(residue, 2*d-residue)


def check_balance_formula():
    for w in range(2, 9):
        n = 1 << w
        for d in range(1, n):
            direct = sum(1-2*(((a+d-1)//d)&1) for a in range(n))
            assert direct == ceil_balance(n, d)
    # With zero correlation, distance(N-1,2D*Z)=1, so D divides N/2
    # or N/2-1. The latter is prime.
    mersenne = (1 << 31)-1
    assert all(mersenne % k for k in range(2, math.isqrt(mersenne)+1))
    print('Ceil-balance formula verified exhaustively at widths2..8.')


def exclude_mersenne_divisor():
    """D=2^31-1 has precisely two zero-derivative MSB pairs.

    For a in [0,2^31), parity(ceil(a/D)) differs from its MSB partner
    except at a=0 and a=D. Any odd MAD and input XOR permutes MSB pairs.
    Reference has at least three zero pairs for each inverse tail other
    than T4. Its T4 inverse projection has derivative identically one:
    it is e0 XOR e4 XOR e8 XOR e12, and input31 flips only e12 among
    these bits. Both cases contradict the candidate's exactly-two count.
    """
    d = (1 << 31)-1
    q = 1 << 31
    f = lambda a: ((a+d-1)//d)&1
    assert f(0) == f(q) and f(d) == f(d+q)
    for a in (1,2,3,q//2,d-2,d-1):
        assert f(a) != f(a+q)
    for s in range(1, 33):
        mask = inverse_shear_mask(s)
        if s == 4:
            assert (mask ^ (mask << 16)) & MASK == 0x1111
            assert all(((h(x)^h(x^q))&mask).bit_count()&1 for x in range(256))
            print('Mersenne divisor: inverse T4 has constant-one derivative.')
        else:
            zeros = [x for x in range(256)
                     if ((h(x)^h(x^q))&mask).bit_count()%2 == 0]
            assert len(zeros) >= 3
            print('Mersenne divisor: inverse tail', s, 'zero-pair witnesses', zeros[:3])


def remaining_divisors():
    delta = 1343488
    choices = set()
    for value in ((N-delta-2)//2, (N+delta)//2):
        for k in range(1, math.isqrt(value)+1):
            if value % k == 0:
                for d in (k, value//k):
                    if d >= delta+1:
                        assert abs(ceil_balance(N, d)) == delta
                        choices.add(d)
    assert len(choices) == 13
    print('Final19 divisor candidates:', sorted(choices))
    print('Run final19_edges.cpp and ceil_final19_influences.cpp for their exact exclusion.')


if __name__ == '__main__':
    assert h(0)^h(1 << 31) != h(1)^h(1^(1 << 31))
    reference_correlations()
    check_balance_formula()
    exclude_mersenne_divisor()
    remaining_divisors()
