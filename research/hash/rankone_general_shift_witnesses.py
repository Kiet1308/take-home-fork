"""Exact derivative witnesses and coordinate counts for rank-one conjugacy.

This handles every source0..31 and first/final logical XOR shear shift.
Shifts>=32 have zero shifted word and are represented by32.  Shift0 is
nonbijective and therefore cannot occur in the candidate composition.
The surviving ordinary(19,16) case is closed by separate fiber/core files.
The source31/first31 nonstandard cases use rank31_shift_prefix.py.
"""
import json
import random
from influence_search import active_edges
from shift_pair_influence import h,target_edges

def main():
    rng=random.Random(76311)
    xs=list(range(64))+[rng.getrandbits(32) for _ in range(256)]
    deltas=[[h(x)^h(x^(1<<i)) for x in xs] for i in range(1,32)]
    all_survivors={}
    counts={tail:[target_edges(tail,b) for b in range(3)] for tail in (4,8)}
    print('Exact alternative-tail coordinate counts:',counts,flush=True)
    for source in range(32):
        survivors=[]
        for tail in range(1,33):
            for flag in ((0,) if tail==32 else (0,1)):
                mask=sum(1<<i for i in range(0,32,tail))^(flag<<source)
                seen=[{(d&mask).bit_count()&1 for d in ds} for ds in deltas]
                # Any first shift>=32 would preserve input parity up to a
                # constant; E also preserves parity. These witnesses rule it out.
                assert any(vals!={0} for vals in seen)
                for first in range(1,32):
                    if not all(i==source or i<first or (i==first and vals=={1}) or
                               (i>first and vals=={0}) for i,vals in enumerate(seen,1)):
                        continue
                    survivors.append((first,tail,flag))
        print('source',source,'derivative survivors',survivors,flush=True)
        remaining=[]
        for first,tail,flag in survivors:
            if (first,tail,flag)==(19,16,0):
                remaining.append((first,tail,flag));continue
            if source==31 and first==31 and (tail,flag)!=(16,0):
                remaining.append((first,tail,flag));continue
            assert flag==0 and tail in (4,8,16),(source,first,tail,flag)
            width=first+1;mod=1<<width
            if tail==16:
                targets=[active_edges(4097,0x7ed55d16,i,20)<<(width-20) for i in range(3)]
            else:
                targets=[v<<(width-(36-tail)) for v in counts[tail]]
            if source==0:
                # Coordinate0 is changed by E; classify from coordinates1,2.
                half=1<<(width-1)
                muls={((sgn*(targets[1]//2+off))%half)+high
                      for sgn in (-1,1) for off in (-1,0,1) for high in (0,half)}
                choices={m:[c for c in range(4) if active_edges(m,c,1,width)==targets[1]]
                         for m in muls if m&1}
                choices={m:[c for lo in cs for c in (lo,lo+4)
                            if active_edges(m,c,2,width)==targets[2]]
                         for m,cs in choices.items()}
            else:
                muls={sgn*(targets[0]+off)%mod for sgn in (-1,1) for off in (-1,1)}
                choices={m:[0] for m in muls}
                for bit in range(3):
                    choices={m:[c for lo in cs for c in (lo,lo+(1<<bit))
                                if bit==source or active_edges(m,c,bit,width)==targets[bit]]
                             for m,cs in choices.items()}
            assert not any(choices.values()),(source,first,tail,flag,choices)
            print('source',source,'excluded by exact counts',(first,tail,flag),flush=True)
        all_survivors[source]=remaining
    with open('rankone_general_shift_witnesses.json','w') as f:json.dump(all_survivors,f)
    with open('rankone_alternative_shift_counts.json','w') as f:json.dump(counts,f)
    print('All nonstandard candidates reduce to source31/first31 prefix checks.',flush=True)

if __name__=='__main__':main()
