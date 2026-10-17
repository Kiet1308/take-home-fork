"""Exclude the source-bit17 rank-one escape for the free-parity tail.

E(x)=x XOR (((x>>17)&1)*D), with D0=0,D1=1,D17=0, is a
parity-preserving invertible rank-one shear. Its encoded output bit1 is
H1 XOR H17 = e1 XOR constant. For the target's core, e1=b1 XOR constant.
The encoding leaves coordinate flips0 and1 unchanged. Therefore, for any D,
an ordinary odd first MAD would need bit20 influence counts matching
    a20 XOR x1 XOR x0, a=4097*x+C0.
Input XOR gauges and additive constants preserve coordinate influence counts.
The first two exact counts exclude every multiplier and additive constant.
"""
from influence_search import active_edges

width=21;n=1<<width;choices=None
for bit in (0,1):
    target=n//2-active_edges(4097,0x7ed55d16,bit,width)
    if choices is None:
        choices={m:[0] for m in sorted({sign*(target+off)%n
                 for sign in (1,-1) for off in (-1,1)})}
    choices={m:[c for lo in cs for c in (lo,lo+(1<<bit))
                if active_edges(m,c,bit,width)==target]
             for m,cs in choices.items()}
    print('input bit',bit,'target edges',target,
          'remaining',{hex(m):[hex(c) for c in cs] for m,cs in choices.items()})
assert not any(choices.values())
print('All source-bit17 parity-preserving rank-one shears excluded for this tail topology.')
