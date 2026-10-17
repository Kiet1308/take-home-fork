"""Classify first prefixes on a fixed original input parity.

Use t=x>>1 as mathematical coordinates, not as an extra kernel instruction.
The first affine word is 2*m*(t XOR k)+c. Its low-bit influence constraints
come from exact 19-bit coordinate counts and Walsh correlations.
"""
import argparse
import random
import sys
import time
import z3


def solve(parity,kind,samples,timeout):
    m,k,base=z3.BitVecs('m k base',32)
    solver=z3.SolverFor('QF_BV');solver.set(timeout=timeout)
    C0=0x7ed55d16;cp=(C0+4097*parity)&0xffffffff
    inv=pow(4097,-1,1<<32)
    solver.add(m&0x80000000==0,k&0x80000000==0)
    solver.add(z3.Or(*[
        z3.And(m&0x7ffff==(sign*4097)&0x7ffff,
               k&0x3ffff==(0x3ffff if flip else 0),
               base&0x7fffe==((cp if (sign==1)^flip else ~cp)&0x7fffe))
        for sign in (1,-1) for flip in (False,True)]))
    if kind=='multiplier':solver.add(m!=4097,m!=(-4097)&0x7fffffff)
    elif kind=='input':solver.add(*[k!=v for v in (0,0x40000000,0x3fffffff,0x7fffffff)])
    elif kind=='base':
        solver.add(*[base&0xfffffffe != v&0xfffffffe
                     for v in (cp,cp^0x80000000,~cp,(~cp)^0x80000000)])
    def map_b(b):
        if isinstance(b,int):
            x=(inv*((b^(b>>19))-C0))&0xffffffff
            assert x&1==parity
            t=x>>1
            a=base+sum((z3.If(k&(1<<i)==0,m<<(i+1),-(m<<(i+1)))
                        for i in range(31) if t&(1<<i)),z3.BitVecVal(0,32))
        else:
            x=inv*((b^z3.LShR(b,19))-C0);t=z3.LShR(x,1)
            a=2*m*(t^k)+base-2*m*k
        return a^z3.LShR(a,19)
    rng=random.Random(97129)
    examples=[0,1,0xffffffff,0xaaaaaaaa,0x55555555]
    examples += [rng.getrandbits(32) for _ in range(max(0,samples-5))]
    examples=[(b&~(1<<19))|(((b&1)^parity)<<19) for b in examples]
    seen=set()
    for it in range(20):
        for b in examples:
            if b in seen:continue
            seen.add(b);center=map_b(b)
            for j in range(1,32):
                if j==19:continue
                other=map_b(b^(1<<j));width=min(j,19)
                solver.add(z3.Extract(width-1,0,center)==z3.Extract(width-1,0,other))
        start=time.monotonic();res=solver.check()
        print(parity,kind,len(seen),str(res),round(time.monotonic()-start,3),flush=True)
        if res!=z3.sat:return
        model=solver.model();values=[model.eval(v).as_long() for v in (m,k,base)]
        print({str(p):hex(v) for p,v in zip((m,k,base),values)},flush=True)
        bx=z3.BitVec('verify_b',32);repl=[(p,z3.BitVecVal(v,32)) for p,v in zip((m,k,base),values)]
        conditions=[];center=z3.substitute(map_b(bx),*repl)
        for j in range(1,32):
            if j==19:continue
            other=z3.substitute(map_b(bx^(1<<j)),*repl);width=min(j,19)
            conditions.append(z3.Extract(width-1,0,center)!=z3.Extract(width-1,0,other))
        ve=z3.SolverFor('QF_BV');ve.set(timeout=timeout)
        ve.add(z3.Extract(19,19,bx)^z3.Extract(0,0,bx)==parity,z3.Or(*conditions))
        vr=ve.check();print('verify',vr,flush=True)
        if vr!=z3.sat:return
        examples=[ve.model().eval(bx).as_long()]


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['multiplier','input','base','any'])
    ap.add_argument('--parity',type=int,choices=[0,1],default=0)
    ap.add_argument('--samples',type=int,default=8);ap.add_argument('--timeout',type=int,default=60000)
    o=ap.parse_args();solve(o.parity,o.kind,o.samples,o.timeout)
