"""Necessary low12 fiber tests after exact rank-one Walsh classification."""
import argparse
import json
import random
import sys
import time
import z3


def run(samples,timeout):
    C0=0x7ed55d16
    MASK=0xffffffff
    INV=pow(4097,-1,1<<32)
    m,ki,base,d=z3.BitVecs('m ki base d',32)
    solver=z3.SolverFor('QF_BV')
    solver.set(timeout=timeout)
    solver.add(d&0x0fffffff==0, d&0x70000000!=0)
    solver.add(z3.Or(*[
        z3.And(m&0xfffff==(sign*4097)&0xfffff,
               ki&0x7ffff==(0x7ffff if flip else 0),
               base&0x7ffff==((C0 if (sign==1)^flip else ~C0)&0x7ffff))
        for sign in (1,-1) for flip in (False,True)]))
    def map_b(b):
        if isinstance(b,int):
            x=(INV*((b^(b>>19))-C0))&MASK
            terms=[]
            for i in range(32):
                toggle=z3.BitVecVal((x>>i)&1,32)
                if x&1:
                    toggle=toggle^z3.ZeroExt(31,z3.Extract(i,i,d))
                if i<28 and not (x>>i)&1:
                    continue
                terms.append(z3.If(toggle==0,z3.BitVecVal(0,32),
                                   z3.If(ki&(1<<i)==0,m<<i,-(m<<i))))
            a=base+sum(terms,z3.BitVecVal(0,32))
        else:
            x=INV*((b^z3.LShR(b,19))-C0)
            z=x^((x&1)*d)^ki
            a=m*z+base-m*ki
        return a^z3.LShR(a,19)
    rng=random.Random(18472)
    examples=[0,1,MASK,0xaaaaaaaa,0x55555555]
    examples += [rng.getrandbits(32) for _ in range(max(0,samples-5))]
    for b in examples:
        center=map_b(b)
        for j in range(1,32):
            width=min(j,12)
            other=map_b(b^(1<<j))
            solver.add(z3.Extract(width-1,0,center)==z3.Extract(width-1,0,other))
            for limit in (13,14,15):
                width=min(j,limit)
                mask=((1<<(limit-12))-1)<<28
                solver.add(z3.Implies(d&mask==0,
                    z3.Extract(width-1,0,center)==z3.Extract(width-1,0,other)))
    start=time.monotonic()
    result=solver.check()
    print(result,'seconds',time.monotonic()-start,flush=True)
    if result==z3.sat:
        model=solver.model()
        print({str(p):hex(model.eval(p,model_completion=True).as_long()) for p in (m,ki,base,d)},flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--samples',type=int,default=8)
    ap.add_argument('--timeout',type=int,default=60000)
    args=ap.parse_args()
    run(args.samples,args.timeout)
