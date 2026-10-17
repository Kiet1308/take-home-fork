"""Necessary low-bit fibers for the live-input prefix x*(m*x+C)+(a>>s).

The actual input to the candidate is z=x XOR ki.  Its first MAD produces
a=m*z+C and its third instruction is MAD(z,a,a>>s).  An arbitrary invertible
triangular downstream core and output XOR constant are allowed implicitly.
The first-bit influence classification forces s-v2(m)=19 and the gauges used
below.  This script checks only necessary finite exact bit-vector identities.
"""
import argparse
import random
import sys
import time
import z3

C0=0x7ed55d16
INV=pow(4097,-1,1<<32)
MASK=0xffffffff


def run(valuation,timeout,samples,fiberbits,kind='product'):
    assert 0<=valuation<=12
    m,ki,base,lower,coef=z3.BitVecs('m ki base lower coef',32)
    params=[m,ki,base,lower,coef]
    so=z3.SolverFor('QF_BV');so.set(timeout=timeout)
    if valuation:
        so.add(z3.LShR(m,32-valuation)==0,z3.LShR(base,32-valuation)==0)
        so.add(z3.ULT(lower,1<<valuation))
    else:so.add(lower==0)
    cases=[]
    for theta in (0,1):
        target_mul=4097+(theta<<19)
        for sign in (1,-1):
            for flip in (False,True):
                cond=z3.And(m&0xfffff==(sign*target_mul)&0xfffff,
                    ki&0x7ffff==(0x7ffff if flip else 0),
                    base&0x7ffff==((C0 if (sign==1)^flip else ~C0)&0x7ffff))
                # theta = 1 XOR parity coefficient of the polynomial z*a.
                # For v=0 that coefficient is 1 XOR C0 = 1 XOR base0 XOR ki0.
                # For v>0 it is the invariant parity bit of a, lower0.
                if kind=='product':
                    cond=z3.And(cond, ((base^ki)&1)==theta if valuation==0
                                else (lower&1)==(1-theta))
                elif kind in ('square_input','square_shift'):
                    cond=z3.And(cond,theta==0)
                elif kind=='affine_input':
                    cond=z3.And(cond,(coef&1)==(1-theta))
                elif kind=='affine_shift':
                    cond=z3.And(cond,theta==0,(coef&1)==1)
                elif kind=='a_shift_input':
                    assert valuation>0
                    cond=z3.And(cond,theta==0,(lower&1)==1)
                else:raise ValueError(kind)
                cases.append(cond)
    so.add(z3.Or(*cases))

    def first(b):
        if isinstance(b,int):
            x=(INV*((b^(b>>19))-C0))&MASK
            high=base+sum((z3.If(ki&(1<<i)==0,m<<i,-(m<<i))
                for i in range(32-valuation) if x&(1<<i)),z3.BitVecVal(0,32))
            a=(high<<valuation)+lower
            # Only low fiberbits are used; ki has a uniform low19 mask.
            z=z3.If(ki&1==0,z3.BitVecVal(x,32),z3.BitVecVal((~x)&MASK,32))
        else:
            x=INV*((b^z3.LShR(b,19))-C0)
            a=((m*(x^ki)+base-m*ki)<<valuation)+lower
            z=x^ki
        q=z3.LShR(a,19+valuation)
        if kind=='product':return z*a+q
        if kind=='square_input':return z*z+q
        if kind=='square_shift':return q*q+z
        if kind=='affine_input':return coef*z+q
        if kind=='affine_shift':return coef*q+z
        if kind=='a_shift_input':return a*q+z
        raise ValueError(kind)

    rng=random.Random(34102)
    examples=[0,1,MASK,0xaaaaaaaa,0x55555555]
    examples += [rng.getrandbits(32) for _ in range(max(0,samples-5))]
    seen=set()
    for iteration in range(20):
        for b in examples:
            if b in seen:continue
            seen.add(b);center=first(b)
            for j in range(32):
                width=min(j+1,fiberbits);other=first(b^(1<<j))
                delta=1<<j if j<fiberbits else 0
                so.add(z3.Extract(width-1,0,center^other)==delta)
        start=time.monotonic();result=so.check()
        print(kind,'valuation',valuation,'samples',len(seen),result,
              round(time.monotonic()-start,3),flush=True)
        if result!=z3.sat:return
        mo=so.model();vals=[mo.eval(p,model_completion=True).as_long() for p in params]
        print({str(p):hex(v) for p,v in zip(params,vals)},flush=True)
        bx=z3.BitVec('verify_b',32);repl=[(p,z3.BitVecVal(v,32)) for p,v in zip(params,vals)]
        center=z3.substitute(first(bx),*repl);conditions=[]
        for j in range(32):
            width=min(j+1,fiberbits);other=z3.substitute(first(bx^(1<<j)),*repl)
            delta=1<<j if j<fiberbits else 0
            conditions.append(z3.Extract(width-1,0,center^other)!=delta)
        ve=z3.SolverFor('QF_BV');ve.set(timeout=timeout);ve.add(z3.Or(*conditions))
        answer=ve.check();print('verify',answer,flush=True)
        if answer!=z3.sat:return
        examples=[ve.model().eval(bx).as_long()]


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--valuation',type=int,default=0)
    ap.add_argument('--timeout',type=int,default=30000)
    ap.add_argument('--samples',type=int,default=8)
    ap.add_argument('--fiberbits',type=int,default=12)
    ap.add_argument('--kind',default='product',choices=['product','square_input',
        'square_shift','affine_input','affine_shift','a_shift_input'])
    args=ap.parse_args();run(args.valuation,args.timeout,args.samples,args.fiberbits,args.kind)
