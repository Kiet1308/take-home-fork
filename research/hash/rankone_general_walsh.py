"""Exact low20 affine-rank-one symmetries of the first-prefix low bit.

Fourier reindexing under E=I+D*e_s^T toggles only frequency bit s.
Magnitude compatibility imposes linear equations in D.  When both toggles
are compatible, the signs still impose a joint linear equation in D and
the free input XOR translation.  Hence this full 2**20 identity check is a
small GF(2) system; it is not a random-witness search.
"""
import json
import time
import numpy as np

W=20;N=1<<W;MASK=N-1

def walsh(c):
    xs=np.arange(N,dtype=np.int64)
    a=1-2*(((4097*xs+c)>>(W-1))&1)
    step=1
    while step<N:
        rows=a.reshape(-1,2*step)
        p=rows[:,:step].copy();q=rows[:,step:].copy()
        rows[:,:step]=p+q;rows[:,step:]=p-q
        step*=2
    return a

def solve(rows, initial=()):
    basis={};bad=False
    def add(row):
        while row>>1:
            pivot=row.bit_length()-1
            if pivot in basis:row^=basis[pivot]
            else:
                basis[pivot]=row
                return True
        return row==0
    for row in initial:
        if not add(int(row)):return None
    for row in rows:
        if not add(int(row)):return None
    # Variables use bits1..41, bit0 is the RHS.
    free=[i for i in range(1,42) if i not in basis]
    def complete(v):
        for p,row in sorted(basis.items()):
            if (v&row).bit_count()&1:v^=1<<p
        return v>>1
    offset=complete(1)
    directions=[complete(1<<f) for f in free]
    return {'rank':len(basis),'offset':offset,'directions':directions}

def main():
    start=time.monotonic()
    with open('rankone_general_influence.json') as f:classes=json.load(f)
    ref=walsh(0x7ed55d16);absref=np.abs(ref)
    freqs=np.arange(N,dtype=np.uint64)
    out={}
    cache={}
    for source in range(1,20):
        cs=classes[f'{source}:19']['4097']
        for c in cs:
            if c not in cache:cache[c]=walsh(c)
            wc=cache[c];alt=wc[np.arange(N)^(1<<source)]
            p0=np.abs(wc)==absref;p1=np.abs(alt)==absref
            if np.any(~p0&~p1):
                out[f'{source}:{c}']=None
                print(source,hex(c),'incompatible magnitudes',flush=True)
                continue
            forced=p0^p1
            # D dot k = required toggle, unknown D occupies bits1..20.
            rows1=(freqs[forced]<<np.uint64(1))|p1[forced].astype(np.uint64)
            valid=absref!=0
            k=freqs[valid]
            # Phase equation k dot L + global_flip = sign(ref/candidate).
            # If p0 is allowed, choose wc as reference; otherwise choose alt.
            base=np.where(p0[valid],wc[valid],alt[valid])
            sign=(base<0)^(ref[valid]<0)
            phase=((wc[valid]<0)^(alt[valid]<0)) & p0[valid] & p1[valid]
            rows2=(k<<np.uint64(W+1))|(np.uint64(1)<<np.uint64(2*W+1))|sign.astype(np.uint64)
            rows2^=np.where(phase,k<<np.uint64(1),np.uint64(0))
            initial=[1<<(1+b) for b in {0,16,source}]
            result=solve(np.concatenate([rows1,rows2]),initial)
            out[f'{source}:{c}']=result
            print(source,hex(c),result,flush=True)
    # For source>=20 the unchanged function must have period Dlow20.
    support=freqs[ref!=0]
    periods=solve(support<<np.uint64(1),[1<<(W+1+i) for i in range(W+1)])
    print('low20 periods',periods,flush=True)
    out['high_source_periods']=periods
    with open('rankone_general_walsh.json','w') as f:json.dump(out,f)
    print('seconds',time.monotonic()-start,flush=True)

if __name__=='__main__':main()
