"""Necessary exact coordinate counts for parity-preserving rank-one encodings.

E(x) = x XOR(bit_source(x)*D), D0=Dsource=0.  With source<31,
input31 witnesses force D16=0 for ordinary first/final XOR shears (19,16).
After that constraint the pre-tail low bit equals the original b0.

This script also allows every first shift.  For source != i, E preserves
coordinate-i pairs, so their influence counts remain ordinary MAD counts.
Every candidate first shift is 19, or equals source>=20: the highest input
coordinate otherwise has the wrong constant derivative.  A shift18 at
source19 is separately rejected by coordinate18's nonconstant derivative.
"""
import json
from influence_search import active_edges
from shift_pair_influence import h

def main():
    target=[active_edges(4097,0x7ed55d16,i,20) for i in range(20)]
    out={}
    for source in range(1,31):
        zero=one=None
        for x in range(4096):
            d=((h(x)^h(x^(1<<31)))>>source)&1
            if d:one=x
            else:zero=x
            if zero is not None and one is not None:break
        assert zero is not None and one is not None
        print('source',source,'D16-zero witnesses',zero,one,flush=True)
        assert target[18] != 1<<19
        shifts=[19]+([source] if source>=20 else [])
        for shift in shifts:
            width=shift+1;n=1<<width
            targets=[(target[i]<<(width-20)) if i<20 else 0 for i in range(shift)]
            options={}
            for m in sorted({v%n for v in ((1<<(shift-7))-1,(1<<(shift-7))+1,
                                             -((1<<(shift-7))-1),-((1<<(shift-7))+1))}):
                cs=[0]
                for i in range(shift):
                    cs=[c for lo in cs for c in (lo,lo+(1<<i))
                        if i==source or active_edges(m,c,i,width)==targets[i]]
                    if not cs:break
                if cs:options[str(m)]=cs
            out[f'{source}:{shift}']=options
            print('source',source,'shift',shift,'classes',{hex(int(m)):len(cs) for m,cs in options.items()},flush=True)
    with open('rankone_general_influence.json','w') as f:json.dump(out,f)

if __name__=='__main__':main()
