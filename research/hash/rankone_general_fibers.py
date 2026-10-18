"""Exact necessary first-prefix fibers for general parity-preserving rank one.

Requires the separately verified influence/Walsh classification.  Candidate
core may be ANY invertible triangular permutation, not only three MADs.
The final right shear is16; the classified first right shear is19.
"""
import argparse
import itertools
import json
import random
import sys
import time
sys.path.insert(0,'.deps')
import z3
from shift_pair_influence import h

MASK=(1<<32)-1;M20=(1<<20)-1;M19=(1<<19)-1
C0=0x7ed55d16;C1=0xc761c23c;INV=pow(4097,-1,1<<32)

def classes(source):
    with open('rankone_general_walsh.json') as f:allclasses=json.load(f)
    result=[]
    lookup=source if source<20 else 1
    for key,res in allclasses.items():
        if key=='high_source_periods' or res is None:continue
        s,c=map(int,key.split(':'))
        if s!=lookup:continue
        for flags in itertools.product((0,1),repeat=len(res['directions'])):
            v=res['offset']
            for flag,direction in zip(flags,res['directions']):
                if flag:v^=direction
            d=v&M20;ell=(v>>20)&M20
            ki=ell^(((ell>>source)&1)*d)
            # Input31 derivatives in prefix bits0..11 require T16(D) low12=0.
            if ((d^(d>>16))&15)!=0:continue
            result.append((c&M19,d,ki))
    return sorted(set(result))

def run(source,samples,timeout,nonzero=True,limit=12,require_bits=None):
    m,ki,c,d=z3.BitVecs('m ki c d',32)
    so=z3.SolverFor('QF_BV');so.set(timeout=timeout)
    so.add(m&M20==4097,d&((1<<source)|1)==0)
    if nonzero:so.add(d!=0)
    if require_bits is not None:so.add(d&require_bits!=0)
    dt=d^z3.LShR(d,16)
    so.add(dt&0xfff==0)
    opts=classes(source)
    so.add(z3.Or(*[z3.And(c&M19==cv,d&M20==dv,ki&M20==kv) for cv,dv,kv in opts]))
    def pref(b):
        a=b^(b>>19);x=(INV*(a-C0))&MASK
        xx=z3.BitVecVal(x,32)^ki
        if (x>>source)&1:xx=xx^d
        # Symbolic bit contributions avoid general variable-by-variable MAD.
        aa=c+sum((z3.If(z3.Extract(i,i,xx)==1,m<<i,z3.BitVecVal(0,32))
                  for i in range(32)),z3.BitVecVal(0,32))
        return aa^z3.LShR(aa,19),x
    def core(b):
        b^=C1
        return (9*(((33*b+0xe9f8cc1d)&MASK)^((16896*b+0xaccf6200)&MASK))+0xfd7046c5)&MASK
    rng=random.Random(812872)
    bs=[0,1,MASK,0xaaaaaaaa,0x55555555]+[rng.getrandbits(32) for _ in range(max(0,samples-5))]
    for b in bs:
        pb,x=pref(b);cb=core(b);hs=(h(x)>>source)&1
        for j in range(32):
            pp,y=pref(b^(1<<j));cp=core(b^(1<<j));ht=(h(y)>>source)&1
            # Necessary iff of low-word equality for a triangular bijection.
            width=min(j,limit)
            qdiff=z3.BitVecVal(cb^cp,32)^(dt if hs!=ht else z3.BitVecVal(0,32))
            pdiff=pb^pp
            if width:
                so.add((z3.Extract(width-1,0,pdiff)==0)==(z3.Extract(width-1,0,qdiff)==0))
            if j<limit:
                so.add((z3.Extract(j,0,pdiff)==0)==(z3.Extract(j,0,qdiff)==0))
    start=time.monotonic();res=so.check()
    print('source',source,'samples',len(bs),'limit',limit,'classes',len(opts),res,'seconds',time.monotonic()-start,flush=True)
    if res==z3.sat:
        mo=so.model();print({str(p):hex(mo.eval(p,model_completion=True).as_long()) for p in (m,ki,c,d)},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=int,required=True)
    ap.add_argument('--samples',type=int,default=8);ap.add_argument('--timeout',type=int,default=60000)
    ap.add_argument('--limit',type=int,default=12);ap.add_argument('--allow-zero',action='store_true')
    ap.add_argument('--require-bits',type=lambda s:int(s,0))
    o=ap.parse_args();run(o.source,o.samples,o.timeout,not o.allow_zero,o.limit,o.require_bits)
