"""First-bit synthesis for source31 rank-one conjugacy with different shifts.

For x<2**31, E(x)=x for every E=x XOR((x>>31)*D).  After any final
inverse right shear, the target bit is one of two known output parities:
parity(H & inverse_mask) XOR(flag*H31).  Thus finite equations for an
odd first MAD/shear can reject a case without modeling D or the middle.
"""
import argparse
import json
import random
import sys
import time
sys.path.insert(0,'.deps')
import z3
from shift_pair_influence import h

def run(first,final,flag,samples,timeout):
    m,ki,base=z3.BitVecs('m ki base',32);out=z3.BitVec('out',1)
    mask=sum(1<<i for i in range(0,32,final))^(flag<<31)
    so=z3.SolverFor('QF_BV');so.set(timeout=timeout);so.add(m&1==1)
    rng=random.Random(763271)
    xs=list(range(min(64,samples)))+[rng.getrandbits(31) for _ in range(max(0,samples-64))]
    for x in xs:
        a=base+sum((z3.If(ki&(1<<i)==0,m<<i,-(m<<i))
                   for i in range(31) if x&(1<<i)),z3.BitVecVal(0,32))
        bit=z3.Extract(first,first,a)^z3.Extract(0,0,a)
        target=(h(x)&mask).bit_count()&1
        so.add(bit^out==target)
    start=time.monotonic();res=so.check()
    print(json.dumps({'first':first,'final':final,'flag':flag,'samples':samples,
                     'result':str(res),'seconds':time.monotonic()-start}),flush=True)
    if res==z3.sat:
        mo=so.model();print({str(p):hex(mo.eval(p,model_completion=True).as_long()) for p in (m,ki,base,out)},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--first',type=int,default=31)
    ap.add_argument('--final',type=int,required=True);ap.add_argument('--flag',type=int,required=True)
    ap.add_argument('--samples',type=int,default=192);ap.add_argument('--timeout',type=int,default=30000)
    o=ap.parse_args();run(o.first,o.final,o.flag,o.samples,o.timeout)
