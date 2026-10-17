"""Reproduce finite checks for the elementary shift/MAD prefix lemmas.

The general proofs are in verified_results.md.  These small-width exhaustive
checks are regression checks for the exact formulas, not substitutes for them.
"""


def valuation(x,w):
    return (x&-x).bit_length()-1 if x else w


def run(max_width=8):
    checked=0
    for w in range(2,max_width+1):
        n=1<<w;mask=n-1
        for s in range(1,w):
            for k in range(n):
                add=len({(a+k*(a>>s))&mask for a in range(n)})==n
                rotate=len({(k*a+(a>>s))&mask for a in range(n)})==n
                assert add == (k% (1<<(s+1)) == 0),(w,s,k,'add')
                assert rotate == (valuation(k,w)==w-s),(w,s,k,'rotate')
                checked+=2
            assert len({(a+(a>>s)**2)&mask for a in range(n)})<n
            assert len({(a*((a>>s)+1))&mask for a in range(n)})<n
            assert sum((a*((a>>s)+1))&1 for a in range(n))==n//4
        print('width',w,'all formulas verified',flush=True)
    # The square-plus-shift prefix at the only surviving effective shift.
    assert ((65536**2)+(65536>>19))&0xffffffff == 0
    print('Verified',checked,'coefficient/shift/permutation comparisons.',flush=True)


if __name__=='__main__':run()
