"""Exact parity-half Walsh correlations for rank-one first-MAD encodings."""
import json
import time
import numpy as np


def fwht(values):
    data = values.copy()
    width = 1
    while width < len(data):
        blocks = data.reshape((-1,2*width))
        left = blocks[:,:width].copy()
        right = blocks[:,width:].copy()
        blocks[:,:width] = left+right
        blocks[:,width:] = left-right
        width *= 2
    return data


def run():
    start = time.monotonic()
    n = 1<<19
    u = np.arange(n,dtype=np.int64)
    target = [fwht(1-2*(((4097*(2*u+p)+0x7ed55d16)>>19)&1)) for p in (0,1)]
    results=[]
    for mul,constants in ((0x1001,(0x2b2ea,0x55d16)),
                          (0x81001,(0x2b2ea,0x55d16)),
                          (0x7efff,(0x2a2e9,0x54d15)),
                          (0xfefff,(0x2a2e9,0x54d15))):
        for c in constants:
            transformed=[fwht(1-2*(((mul*(2*u+p)+c)>>19)&1)) for p in (0,1)]
            correlations={}
            for p in (0,1):
                for q in (0,1):
                    sums=fwht(transformed[q]*target[p])
                    correlations[p,q]=[(int(v),int(sums[v]//(n*n)))
                                       for v in np.flatnonzero(np.abs(sums)==n*n)]
            for ki0 in (0,1):
                for left,sign0 in correlations[0,ki0]:
                    for right,sign1 in correlations[1,1^ki0]:
                        if sign0!=sign1:
                            continue
                        d=(left^right)<<1
                        ki=(left<<1)|ki0
                        # E preserves parity; T16(D) low12 must vanish.
                        # Bits0..3 and16..19 are both now fixed.
                        if (d^(d>>16))&15:
                            continue
                        row={'m20':mul,'c19':c,'ki20':ki,'d20':d,'flip':sign0<0}
                        results.append(row)
                        print({k:hex(v) if isinstance(v,int) and not isinstance(v,bool) else v for k,v in row.items()},flush=True)
    print('solutions',len(results),'seconds',time.monotonic()-start,flush=True)
    with open('rankone_translations.json','w') as output:
        json.dump(results,output)


if __name__=='__main__':
    run()
