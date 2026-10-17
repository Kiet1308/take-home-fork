"""Reproduce the exact fixed-input-parity first-prefix constraints."""
import json
import numpy as np
from influence_search import active_edges
from rankone_translations import fwht
from shift_pair_influence import filter_pairs, target_edges


def main():
    n=1<<19;u=np.arange(n,dtype=np.int64)
    constants={};translations=[]
    for p in (0,1):
        c=(0x7ed55d16+4097*p)//2
        edges=[active_edges(4097,c,j,19) for j in range(18)]
        candidates=sorted({sign*(edges[0]+off)%n for sign in (1,-1) for off in (-1,1)})
        constants[p]={}
        target=fwht(1-2*(((4097*u+c)>>18)&1))
        for m in candidates:
            choices=[0]
            for j in range(18):
                choices=[v for lo in choices for v in (lo,lo+(1<<j))
                         if active_edges(m,v,j,19)==edges[j]]
                if not choices:break
            constants[p][m]=choices
            for value in choices:
                transformed=fwht(1-2*(((m*u+value)>>18)&1))
                correlation=fwht(transformed*target)
                for k in np.flatnonzero(np.abs(correlation)==n*n):
                    row={'parity':p,'m19':m,'c18':value,'ki19':int(k),
                         'flip':bool(correlation[k]<0)}
                    translations.append(row)
                    print(row,flush=True)
        print('parity',p,'shift pairs',filter_pairs(p),flush=True)
        for final_shift in (4,8):
            width=35-final_shift;mod=1<<width;choices=None
            for bit in range(2):
                target_count=target_edges(final_shift,bit+1,input_parity=p)
                if choices is None:
                    choices={m:[0] for m in sorted({sign*(target_count+off)%mod
                             for sign in (1,-1) for off in (-1,1)})}
                choices={m:[c for lo in cs for c in (lo,lo+(1<<bit))
                            if active_edges(m,c,bit,width)==target_count]
                         for m,cs in choices.items()}
                print('parity',p,'final',final_shift,'inputbit',bit+1,
                      'edges',target_count,'choices',choices,flush=True)
            assert not any(choices.values())
    with open('parity_influence_constants.json','w') as f:json.dump(constants,f,indent=2)
    with open('parity_translations.json','w') as f:json.dump(translations,f,indent=2)


if __name__=='__main__':main()
