"""Exact finite witnesses used in the raw-node encoding argument.

For every fixed original input top-two-bit coset, flipping input bit29
connects all four possible H top-two-bit values. Any nonconstant Boolean
function of those output bits must therefore vary under that input flip.
"""
from shift_pair_influence import h

WITNESSES=[
    [0x0808cc7c,0x0df9db18,0x1d97d1fb,0x197abd3a,0,0x186dc9b9],
    [0x5d97d1fb,0x4b82c0aa,0x40000000,0x58fdfa3a,0x4b1c4fce,0x4c372a5d],
    [0x844a94bf,0x8b1c4fce,0x997abd3a,0x87e30a2b,0x98c1416c,0x9d97d1fb],
    [0xdd97d1fb,0xd97abd3a,0xc0000000,0xc0756f80,0xdcb74e57,0xc7e30a2b],
]
EXPECTED={(a,b) for a in range(4) for b in range(a+1,4)}
for coset,xs in enumerate(WITNESSES):
    assert all(x>>30==coset for x in xs)
    edges={tuple(sorted((h(x)>>30,h(x^(1<<29))>>30))) for x in xs}
    assert edges==EXPECTED,(coset,edges)
    print('input top2',coset,'all six output edges verified')
for mask in (2,3):
    changes=[((h(x)^h(x^(1<<31)))&mask).bit_count()&1 for x in (0,1)]
    assert len(set(changes))==2
    print('output mask',hex(mask),'input-bit31 derivatives at x=0,1:',changes)
