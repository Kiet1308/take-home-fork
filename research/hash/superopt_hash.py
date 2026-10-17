"""Search the real fixed-word hash instruction family; no simulator changes."""
import argparse
import json
import random
import sys
import time
import z3

C0 = 0x7ed55d16
C1 = 0xc761c23c
A = 0xe9f8cc1d
B = 0xaccf6200
C4 = 0xfd7046c5
C5 = 0xb55a4f09
M = C5 ^ (C5 >> 16)


def bstage(x, c0=C0, c1=C1):
    a = x * 4097 + c0
    if isinstance(a, int):
        a &= 0xffffffff
        return a ^ (a >> 19) ^ c1
    return a ^ z3.LShR(a, 19) ^ c1


def core(b, aa=A, bb=B, cc=C4):
    if isinstance(b, int):
        return (9 * (((33*b+aa)&0xffffffff) ^ ((16896*b+bb)&0xffffffff)) + cc) & 0xffffffff
    return 9 * ((33*b+aa) ^ (16896*b+bb)) + cc


def emit(*args):
    print(*args, flush=True)


def solve(mode, timeout, mask=M, width=32, nsamples=8, sampling='random', parity=None, lowbits=None, staged=False):
    rng = random.Random(742837)
    vnames = {'last': ['d', 'c'], 'core': ['k', 'a', 'b', 'c'],
              'family': ['c0', 'c1', 'a', 'b', 'c'],
              'dropxor': ['c0', 'a', 'b', 'c', 'm'],
              'dropxorcore': ['a', 'b', 'c', 'm'],
              'middle2': ['mul', 'a', 'c', 'm'],
              'tail2': ['mul', 'shift', 'm'],
              'dropxorshifts': ['c0', 'a', 'b', 'c', 's1', 's2', 'm'],
              'coremuls': ['m1', 'm2', 'm3', 'a', 'b', 'c'],
              'coremulsinput': ['kin', 'm1', 'm2', 'm3', 'a', 'b', 'c'],
              'dropxormuls': ['m0', 'm1', 'm2', 'm3', 'c0', 'a', 'b', 'c', 'm'],
              'dropxorinput': ['kin', 'c0', 'a', 'b', 'c', 'm'],
              'familyinput': ['kin', 'c0', 'c1', 'a', 'b', 'c'],
              'encodefree': ['kin', 'c0', 'c1', 'a', 'b', 'c'],
              'paritydropxor': ['c0', 'a', 'b', 'c', 'm', 'd'],
              'parityencode': ['c0', 'c1', 'a', 'b', 'c', 'd'],
              'paritysheardrop': ['c0', 'a', 'b', 'c', 'm', 'd', 'h0', 'h1'],
              'parityshearencode': ['c0', 'c1', 'a', 'b', 'c', 'd', 'h0', 'h1'],
              'encodeshearfree': ['kin', 'c0', 'c1', 'a', 'b', 'c', 'h0', 'h1'],
              'parityshearinput': ['kin', 'c0', 'a', 'b', 'c', 'm', 'd', 'h0', 'h1'],
              'parityshearhalf': ['kin', 'c0', 'c1', 'a', 'b', 'c', 'd', 'h0', 'h1'],
              'dropmadcore': ['m1', 'm2', 'a', 'b', 'm'],
              'tailaddcore': ['mul', 'a', 'b', 'm'],
              'allmulsraw': ['m0', 'm1', 'm2', 'm3', 'kin', 'c0', 'c1', 'a', 'b', 'c'],
              'allmulsdrop': ['m0', 'm1', 'm2', 'm3', 'kin', 'c0', 'a', 'b', 'c', 'm'],
              'firstaffine': ['m0', 'k', 'kin', 'c0', 't'],
              'linearconjugate9': ['d', 'kin', 'c0', 'a', 'b', 'c', 'm'],
              'linearconjugatemuls9': ['d', 'kin', 'm0', 'm1', 'm2', 'm3', 'c0', 'a', 'b', 'c', 'm'],
              'rankconjugate9': ['d', 'source', 'kin', 'c0', 'a', 'b', 'c', 'm'],
              'rankconjugate10': ['d', 'source', 'c0', 'c1', 'a', 'b', 'c'],
              'encodecycle': ['ki', 'ko', 'c00', 'c10', 'a0', 'b0', 'c0', 'c01', 'c11', 'a1', 'b1', 'c1']}[mode]
    params = [z3.BitVec(s, width) for s in vnames]
    def encoded_mad(x, mm, ki, base):
        # base is a(0), absorbing mm*ki into the unconstrained additive offset.
        # Concrete synthesis examples share signed-shift weights instead of
        # producing separate variable-by-variable multiplication circuits.
        if z3.is_bv_value(x):
            value = x.as_long()
            return base + sum((z3.If(ki & (1 << i) == 0, mm << i, -(mm << i))
                              for i in range(width) if value & (1 << i)),
                             z3.BitVecVal(0, width))
        return mm*(x ^ ki)+base-mm*ki
    def cand(x):
        if mode in ('rankconjugate9','rankconjugate10'):
            if mode=='rankconjugate9':
                dd, source, ki, c0, aa, bb, cc, mm = params
                c1=0
            else:
                dd,source,c0,c1,aa,bb,cc=params
                ki=0;mm=M
            ex=x ^ ((z3.LShR(x,source)&1)*dd) ^ ki
            ax=4097*ex+c0
            bx=ax ^ z3.LShR(ax,19) ^ c1
            qnew=core(bx,aa,bb,cc)
            qref=core(bstage(x))
            hx=qref ^ z3.LShR(qref,16) ^ C5
            p=z3.LShR(hx,source)&1
            return qnew ^ (p*(dd ^ z3.LShR(dd,16))) ^ mm
        if mode in ('linearconjugate9', 'linearconjugatemuls9'):
            if mode == 'linearconjugate9':
                dd, ki, c0, aa, bb, cc, mm = params
                m0, m1, m2, m3 = 4097, 33, 16896, 9
            else:
                dd, ki, m0, m1, m2, m3, c0, aa, bb, cc, mm = params
            ex = x ^ ((x & 1)*dd) ^ ki
            ax = m0*ex+c0
            bx = ax ^ z3.LShR(ax,19)
            qnew = m3*((m1*bx+aa) ^ (m2*bx+bb))+cc
            qref = core(bstage(x))
            p = (qref ^ z3.LShR(qref,16) ^ C5) & 1
            return qnew ^ (p*(dd ^ z3.LShR(dd,16))) ^ mm
        if mode == 'last':
            dd, cc = params
            return 9 * (x ^ dd) + cc
        if mode == 'core':
            kk, aa, bb, cc = params
            return core(x ^ kk, aa, bb, cc)
        if mode == 'dropxor':
            c0, aa, bb, cc, mm = params
            return core(bstage(x, c0, 0), aa, bb, cc) ^ mm
        if mode == 'dropxorcore':
            aa, bb, cc, mm = params
            return core(x ^ C1, aa, bb, cc) ^ mm
        if mode == 'middle2':
            mul, aa, cc, mm = params
            return (9 * ((mul*x+aa)^x) + cc) ^ mm
        if mode == 'tail2':
            mul, ss, mm = params
            return (mul*x + z3.LShR(x, ss)) ^ mm
        if mode == 'dropxorshifts':
            c0, aa, bb, cc, s1, s2, mm = params
            ax = x*4097+c0
            ex = core(ax ^ z3.LShR(ax, s1), aa, bb, cc)
            return ex ^ z3.LShR(ex, s2) ^ mm
        if mode == 'coremuls':
            m1, m2, m3, aa, bb, cc = params
            return m3*((m1*x+aa) ^ (m2*x+bb)) + cc
        if mode == 'coremulsinput':
            ki, m1, m2, m3, aa, bb, cc = params
            return m3*(encoded_mad(x,m1,ki,aa) ^ encoded_mad(x,m2,ki,bb)) + cc
        if mode == 'dropxormuls':
            m0, m1, m2, m3, c0, aa, bb, cc, mm = params
            ax = x*m0+c0
            bx = ax ^ z3.LShR(ax, 19)
            return (m3*((m1*bx+aa) ^ (m2*bx+bb)) + cc) ^ mm
        if mode == 'dropxorinput':
            ki, c0, aa, bb, cc, mm = params
            return core(bstage(x ^ ki, c0, 0), aa, bb, cc) ^ mm
        if mode == 'familyinput':
            ki, c0, c1, aa, bb, cc = params
            return core(bstage(x ^ ki, c0, c1), aa, bb, cc)
        if mode == 'encodefree':
            ki, c0, c1, aa, bb, cc = params
            return core(bstage(x ^ ki, c0, c1), aa, bb, cc) ^ ki ^ z3.LShR(ki,16)
        if mode == 'paritydropxor':
            c0, aa, bb, cc, mm, dd = params
            q = core(bstage(x))
            p = (q ^ z3.LShR(q,16) ^ C5) & 1
            return core(bstage(x, c0, 0), aa, bb, cc) ^ mm ^ (p*dd)
        if mode == 'parityencode':
            c0, c1, aa, bb, cc, dd = params
            q = core(bstage(x))
            p = (q ^ z3.LShR(q,16) ^ C5) & 1
            return core(bstage(x, c0, c1), aa, bb, cc) ^ (p*dd)
        if mode in ('paritysheardrop', 'parityshearencode'):
            if mode == 'paritysheardrop':
                c0, aa, bb, cc, mm, dd, h0, h1 = params
                c1 = 0
            else:
                c0, c1, aa, bb, cc, dd, h0, h1 = params
                mm = 0
            ax = (x*4097+c0) ^ z3.If(h0==1, x<<31, z3.BitVecVal(0,width))
            bx = ax ^ z3.LShR(ax,19) ^ c1
            cx = core(bx, aa, bb, cc) ^ z3.If(h1==1, bx<<31, z3.BitVecVal(0,width))
            q = core(bstage(x))
            p = (q ^ z3.LShR(q,16) ^ C5) & 1
            return cx ^ mm ^ (p*dd)
        if mode == 'encodeshearfree':
            ki, c0, c1, aa, bb, cc, h0, h1 = params
            xx = x ^ ki
            ax = (xx*4097+c0) ^ z3.If(h0==1, xx<<31, z3.BitVecVal(0,width))
            bx = ax ^ z3.LShR(ax,19) ^ c1
            cx = core(bx, aa, bb, cc) ^ z3.If(h1==1, bx<<31, z3.BitVecVal(0,width))
            return cx ^ ki ^ z3.LShR(ki,16)
        if mode in ('parityshearinput', 'parityshearhalf'):
            if mode == 'parityshearinput':
                ki, c0, aa, bb, cc, mm, dd, h0, h1 = params
                c1 = 0
            else:
                ki, c0, c1, aa, bb, cc, dd, h0, h1 = params
                mm = ki ^ z3.LShR(ki,16)
            xx = x ^ ki
            ax = (xx*4097+c0) ^ z3.If(h0==1, xx<<31, z3.BitVecVal(0,width))
            bx = ax ^ z3.LShR(ax,19) ^ c1
            cx = core(bx, aa, bb, cc) ^ z3.If(h1==1, bx<<31, z3.BitVecVal(0,width))
            q = core(bstage(x))
            p = (q ^ z3.LShR(q,16) ^ C5) & 1
            return cx ^ mm ^ (p*dd)
        if mode == 'dropmadcore':
            m1, m2, aa, bb, mm = params
            return (m1*x+aa) ^ (m2*x+bb) ^ mm
        if mode == 'tailaddcore':
            mul, aa, bb, mm = params
            dx = (33*x+aa) ^ (16896*x+bb)
            return (mul*dx + z3.LShR(dx,16)) ^ mm
        if mode in ('allmulsraw', 'allmulsdrop'):
            if mode == 'allmulsraw':
                m0, m1, m2, m3, ki, c0, c1, aa, bb, cc = params
                mm = ki ^ z3.LShR(ki,16)
            else:
                m0, m1, m2, m3, ki, c0, aa, bb, cc, mm = params
                c1 = 0
            ax = encoded_mad(x, m0, ki, c0)
            bx = ax ^ z3.LShR(ax,19) ^ c1
            return (m3*((m1*bx+aa) ^ (m2*bx+bb)) + cc) ^ mm
        if mode == 'encodecycle':
            ki, ko, c00, c10, a0, b0, c0, c01, c11, a1, b1, c1 = params
            q0 = core(bstage(x ^ ki, c00, c10), a0, b0, c0) ^ ko ^ z3.LShR(ko,16)
            q1 = core(bstage(x ^ ko, c01, c11), a1, b1, c1) ^ ki ^ z3.LShR(ki,16)
            return z3.Concat(q0, q1)
        if mode == 'firstaffine':
            m0, kk, ki, c0, tt = params
            ax = encoded_mad(x, m0, ki, c0)
            return ax ^ z3.LShR(ax,19)
        c0, c1, aa, bb, cc = params
        return core(bstage(x, c0, c1), aa, bb, cc)
    def ref(x):
        if mode in ('rankconjugate9','rankconjugate10'): return core(bstage(x))
        if mode in ('linearconjugate9', 'linearconjugatemuls9'): return core(bstage(x))
        if mode == 'last': return (9*x+C4) ^ mask
        if mode == 'core': return core(x) ^ mask
        if mode == 'dropxorcore': return core(x)
        if mode == 'dropxor': return core(bstage(x))
        if mode == 'middle2': return core(x)
        if mode == 'tail2':
            ex = 9*x+C4
            return ex ^ z3.LShR(ex, 16)
        if mode == 'dropxorshifts':
            ex = core(bstage(x))
            return ex ^ z3.LShR(ex, 16)
        if mode == 'coremuls': return core(x) ^ mask
        if mode == 'coremulsinput': return core(x) ^ mask
        if mode == 'dropxormuls': return core(bstage(x))
        if mode == 'dropxorinput': return core(bstage(x))
        if mode == 'familyinput': return core(bstage(x)) ^ mask
        if mode == 'encodefree': return core(bstage(x)) ^ mask
        if mode == 'paritydropxor': return core(bstage(x))
        if mode == 'parityencode': return core(bstage(x)) ^ mask
        if mode == 'paritysheardrop': return core(bstage(x))
        if mode == 'parityshearencode': return core(bstage(x)) ^ mask
        if mode == 'encodeshearfree': return core(bstage(x)) ^ mask
        if mode == 'parityshearinput': return core(bstage(x))
        if mode == 'parityshearhalf': return core(bstage(x)) ^ mask
        if mode == 'dropmadcore': return core(x)
        if mode == 'tailaddcore':
            q = core(x)
            return q ^ z3.LShR(q,16)
        if mode == 'allmulsraw': return core(bstage(x)) ^ mask
        if mode == 'allmulsdrop': return core(bstage(x))
        if mode == 'firstaffine': return params[1]*bstage(x)+params[4]
        if mode == 'encodecycle':
            q = core(bstage(x)) ^ mask
            return z3.Concat(q, q)
        return core(bstage(x)) ^ mask
    solver = z3.SolverFor('QF_BV')
    solver.set(timeout=timeout)
    if mode in ('rankconjugate9','rankconjugate10'):
        dd,source=params[:2]
        solver.add(z3.ULT(source,32), dd&1==0, z3.LShR(dd,source)&1==0)
        solver.add(z3.Implies(source!=31, (dd ^ z3.LShR(dd,16))&0xfff==0))
        if mode=='rankconjugate10': solver.add(z3.UGE(source,30))
    if mode in ('linearconjugate9', 'linearconjugatemuls9'):
        # E preserves parity. D16 would make the target pre-tail bit0 equal
        # original e16, which changes under x31 (witness x=0); a first
        # T19(MAD(E(x)^K)) bit0 cannot depend on x31.
        solver.add(params[0]&1 == 0)
        solver.add((params[0] ^ z3.LShR(params[0],16)) & 0xfff == 0)
    if mode == 'linearconjugatemuls9':
        solver.add(params[2]&1 == 1, params[3]&1 == 1, params[4]&1 == 0, params[5]&3 == 1)
        # E commutes with every coordinate flip except bit0. Exact influence
        # counts of those 18 lower coordinate flips constrain the first MAD.
        solver.add(z3.Or(*[
            z3.And((params[2]&0xfffff)==mul,
                   z3.Or(*[(params[6]&0x7ffff)==c for c in constants]))
            for mul,constants in ((0x1001,(0x2b2ea,0x55d16)),
                                  (0x81001,(0x2b2ea,0x55d16)),
                                  (0x7efff,(0x2a2e9,0x54d15)),
                                  (0xfefff,(0x2a2e9,0x54d15)))]))
    if mode == 'tail2': solver.add(z3.ULT(params[1], width))
    if mode == 'dropxorshifts':
        solver.add(z3.ULT(params[4], width), z3.ULT(params[5], width))
    if mode == 'coremuls':
        solver.add((params[0]^params[1])&1 == 1, params[2]&1 == 1)
    if mode == 'coremulsinput':
        solver.add(params[1]&1 == 1, params[2]&1 == 0, params[3]&3 == 1)
    if mode in ('dropxormuls', 'allmulsraw', 'allmulsdrop'):
        solver.add(params[0]&1 == 1, (params[1]^params[2])&1 == 1, params[3]&1 == 1)
    if mode in ('allmulsraw', 'allmulsdrop'):
        solver.add(params[1]&1 == 1, params[2]&1 == 0, params[3]&3 == 1)
    if mode == 'allmulsdrop':
        solver.add(params[0]&3 == 1)
    if mode == 'firstaffine':
        solver.add(params[0]&3 == 1, params[1]&1 == 1)
    if mode in ('firstaffine', 'allmulsraw', 'allmulsdrop') and parity is None:
        # Input bit-0 influence of output bit 0 is invariant under XOR input
        # translation. Odd downstream T-functions only toggle that bit by a
        # constant. The reference first MAD has influence 8192 / 2**20;
        # an odd first coefficient must therefore be ±4095 or ±4097 mod 2**20.
        solver.add(z3.Or(*[(params[0] & ((1 << 20)-1)) == (v & ((1 << 20)-1))
                           for v in (4095,4097,-4095,-4097)]))
        ki = params[2] if mode == 'firstaffine' else params[4]
        base = params[3] if mode == 'firstaffine' else params[5]
        mask19 = (1 << 19)-1
        mask20 = (1 << 20)-1
        # All coordinate influences leave only ±4097. The exact 20-bit
        # Walsh support has affine span rank 19, so input XOR translations
        # are only 0 or bit19 after accounting for input complementation.
        solver.add(z3.Or(*[
            z3.And((params[0] & mask20) == ((sign*4097) & mask20),
                   (ki & mask19) == (mask19 if flip else 0),
                   (base & mask19) == ((C0 if (sign==1)^flip else ~C0) & mask19))
            for sign in (1,-1) for flip in (False,True)]))
        # first_triangular.py excludes every other full-word coefficient,
        # input mask and base using necessary low-bit-fiber identities.
        solver.add(z3.Or(params[0] == 4097, params[0] == ((-4097)&0xffffffff)))
        solver.add(z3.Or(*[ki == v for v in (0,0x80000000,0x7fffffff,0xffffffff)]))
        solver.add(z3.Or(*[base == v for v in (C0,C0^0x80000000,(~C0)&0xffffffff,((~C0)&0xffffffff)^0x80000000)]))
    if mode in ('paritydropxor', 'parityencode', 'paritysheardrop', 'parityshearencode'):
        solver.add(((params[5] ^ z3.LShR(params[5], 16)) & 1) == 0)
    if mode in ('paritysheardrop', 'parityshearencode', 'encodeshearfree'):
        solver.add(z3.ULE(params[6],1), z3.ULE(params[7],1))
    if mode in ('parityshearinput', 'parityshearhalf'):
        solver.add(((params[6] ^ z3.LShR(params[6], 16)) & 1) == 0)
        solver.add(z3.ULE(params[7],1), z3.ULE(params[8],1))
    examples = [0, 1, 0xffffffff, 0xaaaaaaaa, 0x55555555]
    if sampling == 'random':
        examples += [rng.getrandbits(width) for _ in range(nsamples-5)]
    elif sampling == 'basis':
        examples += [1 << (i % width) for i in range(nsamples-5)]
    elif sampling == 'linear':
        examples += list(range(2, nsamples-3))
    seen = set()
    def project(x):
        if lowbits is not None and mode == 'encodecycle':
            return z3.Concat(z3.Extract(width+lowbits-1,width,x), z3.Extract(lowbits-1,0,x))
        return z3.Extract(lowbits-1,0,x) if lowbits is not None else x
    for iteration in range(1000):
        new_constraints = []
        for value in examples:
            value &= (1 << width)-1
            if parity is not None: value = (value & ~1) | parity
            if value in seen: continue
            seen.add(value)
            x = z3.BitVecVal(value, width)
            new_constraints.append((cand(x), ref(x)))
        if staged and iteration == 0:
            for active_bits in range(1, (lowbits or width)+1):
                for cx, rx in new_constraints:
                    solver.add(z3.Extract(active_bits-1, 0, cx) == z3.Extract(active_bits-1, 0, rx))
                partial_start = time.monotonic()
                partial = solver.check()
                emit('stage', active_bits, partial, time.monotonic()-partial_start)
                if partial != z3.sat:
                    return
        else:
            for cx, rx in new_constraints:
                solver.add(project(cx) == project(rx))
        start = time.monotonic()
        result = solver.check()
        emit(json.dumps({'mode': mode, 'width': width, 'iteration': iteration,
                         'lowbits': lowbits,
                         'samples': len(seen), 'result': str(result),
                         'seconds': time.monotonic()-start}))
        if result != z3.sat:
            if result == z3.unknown: emit(solver.reason_unknown())
            return
        model = solver.model()
        values = [model.eval(p, model_completion=True).as_long() for p in params]
        emit({k: hex(v) for k, v in zip(vnames, values)})
        x = z3.BitVec('verify_x', width)
        expr = z3.substitute(cand(x), *[(p,z3.BitVecVal(v,width)) for p,v in zip(params,values)])
        target_expr = z3.substitute(ref(x), *[(p,z3.BitVecVal(v,width)) for p,v in zip(params,values)])
        verify = z3.SolverFor('QF_BV')
        verify.set(timeout=timeout)
        if parity is not None: verify.add(x&1 == parity)
        verify.add(project(expr) != project(target_expr))
        vr = verify.check()
        emit('verify', vr)
        if vr == z3.unsat:
            emit('PROVED', {k:hex(v) for k,v in zip(vnames,values)})
            return
        if vr == z3.unknown: return
        examples = [verify.model().eval(x).as_long()] + [rng.getrandbits(width) for _ in range(3)]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['last', 'core', 'family', 'dropxor', 'dropxorcore', 'middle2', 'tail2', 'dropxorshifts', 'coremuls', 'coremulsinput', 'dropxormuls', 'dropxorinput', 'familyinput', 'encodefree', 'paritydropxor', 'parityencode', 'paritysheardrop', 'parityshearencode', 'encodeshearfree', 'parityshearinput', 'parityshearhalf', 'dropmadcore', 'tailaddcore', 'allmulsraw', 'allmulsdrop', 'encodecycle', 'firstaffine', 'linearconjugate9', 'linearconjugatemuls9', 'rankconjugate9','rankconjugate10'])
    ap.add_argument('--timeout', type=int, default=60000)
    ap.add_argument('--width', type=int, default=32)
    ap.add_argument('--mask', type=lambda s:int(s,0), default=M)
    ap.add_argument('--samples', type=int, default=8)
    ap.add_argument('--sampling', choices=['random', 'basis', 'linear'], default='random')
    ap.add_argument('--parity', type=int, choices=[0,1])
    ap.add_argument('--lowbits', type=int)
    ap.add_argument('--staged', action='store_true')
    args = ap.parse_args()
    solve(args.mode, args.timeout, args.mask, args.width, args.samples, args.sampling, args.parity, args.lowbits, args.staged)
