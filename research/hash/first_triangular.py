"""Classify first-MAD maps compatible with any odd downstream T-function."""
import argparse
import random
import sys
import time
import z3

C0 = 0x7ed55d16
MASK = 0xffffffff
INV = pow(4097, -1, 1 << 32)


def run(kind, nsamples, timeout, fiberbits=32, gauge_bits=32):
    m, ki, base = z3.BitVecs('m ki base',32)
    params = [m,ki,base]
    mask19 = (1 << 19)-1
    mask20 = (1 << 20)-1
    solver = z3.SolverFor('QF_BV')
    solver.set(timeout=timeout)
    first_coefficient = 4097+(1<<19) if kind=='rotate' else 4097
    solver.add(z3.Or(*[
        z3.And((m & mask20) == ((sign*first_coefficient) & mask20),
               (ki & mask19) == (mask19 if flip else 0),
               (base & mask19) == ((C0 if (sign==1)^flip else ~C0) & mask19))
        for sign in (1,-1) for flip in (False,True)]))
    gauge_mask=(1<<gauge_bits)-1
    gauge_high=1<<(gauge_bits-1)
    if kind == 'multiplier':
        solver.add(m&gauge_mask != 4097&gauge_mask, m&gauge_mask != (-4097)&gauge_mask)
    elif kind == 'input':
        solver.add(*[ki&gauge_mask != v for v in (0,gauge_high,gauge_high-1,gauge_mask)])
    elif kind == 'base':
        solver.add(*[base&gauge_mask != v&gauge_mask for v in (C0,C0^gauge_high,~C0,(~C0)^gauge_high)])

    def mad_x(x):
        return base + sum((z3.If(ki & (1<<i)==0, m<<i, -(m<<i))
                           for i in range(32) if x & (1<<i)), z3.BitVecVal(0,32))
    def map_b(b):
        if isinstance(b,int):
            x = (INV*((b^(b>>19))-C0)) & MASK
            a = mad_x(x)
        else:
            x = INV*((b^z3.LShR(b,19))-C0)
            a = m*(x ^ ki)+base-m*ki
        if kind=='rotate':
            return z3.LShR(a,19)
        if kind=='branch_shift':
            return (x ^ ki) ^ z3.LShR(a,19)
        if kind=='branch_ceil':
            return (x ^ ki) ^ (z3.LShR(a,19)+1)
        return a ^ z3.LShR(a,19)

    rng = random.Random(18472)
    examples = [0,1,MASK,0xaaaaaaaa,0x55555555]
    examples += [rng.getrandbits(32) for _ in range(max(0,nsamples-5))]
    seen = set()
    for iteration in range(100):
        for b in examples:
            if b in seen:
                continue
            seen.add(b)
            center = map_b(b)
            for j in range(1,32):
                other = map_b(b^(1<<j))
                width = min(j,13) if kind=='rotate' else min(j,3) if kind.startswith('branch_') else min(j,fiberbits)
                solver.add(z3.Extract(width-1,0,center)==z3.Extract(width-1,0,other))
        start = time.monotonic()
        result = solver.check()
        print(kind, 'samples',len(seen),'iteration',iteration,result,'seconds',time.monotonic()-start,flush=True)
        if result != z3.sat:
            return
        model = solver.model()
        values = [model.eval(p,model_completion=True).as_long() for p in params]
        print({str(p):hex(v) for p,v in zip(params,values)},flush=True)
        b = z3.BitVec('verify_b',32)
        replacements = [(p,z3.BitVecVal(v,32)) for p,v in zip(params,values)]
        center = z3.substitute(map_b(b),*replacements)
        conditions=[]
        for j in range(1,32):
            other = z3.substitute(map_b(b^(1<<j)),*replacements)
            width = min(j,13) if kind=='rotate' else min(j,3) if kind.startswith('branch_') else min(j,fiberbits)
            conditions.append(z3.Extract(width-1,0,center)!=z3.Extract(width-1,0,other))
        verify=z3.SolverFor('QF_BV')
        verify.set(timeout=timeout)
        verify.add(z3.Or(*conditions))
        answer=verify.check()
        print('verify',answer,flush=True)
        if answer != z3.sat:
            return
        examples = [verify.model().eval(b).as_long()]


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('kind',choices=['multiplier','input','base','any','rotate','branch_shift','branch_ceil'])
    ap.add_argument('--samples',type=int,default=8)
    ap.add_argument('--timeout',type=int,default=60000)
    ap.add_argument('--fiberbits',type=int,default=32)
    ap.add_argument('--gauge_bits',type=int,default=32)
    args=ap.parse_args()
    run(args.kind,args.samples,args.timeout,args.fiberbits,args.gauge_bits)
