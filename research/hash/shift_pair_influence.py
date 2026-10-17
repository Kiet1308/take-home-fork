"""Exact low-bit invariants for jointly changed first/final XOR shifts."""
import argparse
import random
import time
import numpy as np
from influence_search import active_edges

C0=0x7ed55d16
C1=0xc761c23c
A=0xe9f8cc1d
B=0xaccf6200
C4=0xfd7046c5
C5=0xb55a4f09
MASK=(1<<32)-1
INV=pow(4097,-1,1<<32)


def h(x):
    a=(4097*x+C0)&MASK
    b=a^(a>>19)^C1
    d=((33*b+A)&MASK)^((16896*b+B)&MASK)
    e=(9*d+C4)&MASK
    return e^(e>>16)^C5


def filter_pairs(parity=None):
    rng=random.Random(923844)
    examples=[0,1,MASK,0xaaaaaaaa,0x55555555]+[rng.getrandbits(32) for _ in range(59)]
    if parity is not None:examples=[(x&~1)|parity for x in examples]
    masks={s:sum(1<<bit for bit in range(0,32,s)) for s in range(1,33)}
    observed={(s,j):set() for s in masks for j in range(1,32)}
    for x in examples:
        hx=h(x)
        for j in range(1,32):
            dh=hx^h(x^(1<<j))
            for s,mask in masks.items():
                observed[s,j].add((dh&mask).bit_count()%2)
    survivors=[]
    for s2 in masks:
        for s1 in range(1,33):
            if s1<32 and observed[s2,s1] != {1}: continue
            if any(observed[s2,j] != {0} for j in range(s1+1 if s1<32 else 1,32)):continue
            survivors.append((s1,s2))
    print('Surviving (first shift, final shift) pairs:',survivors,flush=True)
    return survivors


def target_edges(final_shift, bit, input_parity=None):
    assert final_shift in (4,8)
    assert bit < 19
    k=17-final_shift
    size=1<<k
    mask=size-1
    upper=np.arange(size,dtype=np.uint64)
    b=upper^np.uint64(C1)
    q=(9*((33*b+A)^(16896*b+B))+C4)&np.uint64(MASK)
    parity=np.zeros(size,dtype=np.uint8)
    for pos in range(0,16,final_shift):
        parity ^= ((q>>np.uint64(pos))&1).astype(np.uint8)

    alow=np.arange(1<<19,dtype=np.uint64)
    xlow=(np.uint64(INV)*(alow-np.uint64(C0)))&np.uint64((1<<(bit+1))-1)
    selected=(xlow&np.uint64(1<<bit))==0
    if input_parity is not None:
        assert bit>0
        selected &= (xlow&np.uint64(1))==input_parity
    delta=4097<<bit
    carry=(((alow+np.uint64(delta))>>np.uint64(19))-(delta>>19)).astype(np.uint8)
    low=(alow&np.uint64(mask)).astype(np.int64)
    counts=[np.bincount(low[selected&(carry==c)],minlength=size) for c in (0,1)]
    answer=0
    for lo in range(size):
        if not (counts[0][lo] or counts[1][lo]): continue
        p0=parity[upper^np.uint64(lo)]
        newlo=(lo+delta)&mask
        for c in (0,1):
            if not counts[c][lo]: continue
            increment=(delta>>19)+c
            indices=((upper+np.uint64(increment))&np.uint64(mask))^np.uint64(newlo)
            changed=int(np.count_nonzero(p0 != parity[indices]))
            answer += int(counts[c][lo])*changed
    width=19+k
    if bit==0:
        answer=(1<<(width-1))-answer
    return answer


def classify(final_shift, max_bits=19):
    width=36-final_shift
    choices=None
    for bit in range(max_bits):
        start=time.monotonic()
        target=target_edges(final_shift,bit)
        if choices is None:
            mod=1<<width
            candidates=sorted({sign*(target+offset)%mod for sign in (1,-1) for offset in (-1,1)})
            choices={mul:[0] for mul in candidates}
            print('Initial multiplier candidates:',[hex(v) for v in candidates],flush=True)
        choices={mul:[c for lo in constants for c in (lo,lo+(1<<bit))
                      if active_edges(mul,c,bit,width)==target]
                 for mul,constants in choices.items()}
        print('shift',final_shift,'bit',bit,'edges',target,
              'remaining',{hex(m):[hex(c) for c in cs] for m,cs in choices.items()},
              'seconds',round(time.monotonic()-start,3),flush=True)
        if not any(choices.values()):
            print('EXCLUDED: no odd first MAD has these coordinate influences.',flush=True)
            return


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--shift',type=int,choices=[4,8])
    ap.add_argument('--bits',type=int,default=19)
    args=ap.parse_args()
    if args.shift is None:
        filter_pairs()
    else:
        classify(args.shift,args.bits)
