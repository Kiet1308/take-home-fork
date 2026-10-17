import importlib.util,collections
from pathlib import Path
import sys
repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo))
spec=importlib.util.spec_from_file_location('m',repo/'perf_takehome.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
k=m.KernelBuilder();k.build_kernel(10,2047,256,16)
n=k.ir.nodes
end={i for i,v in enumerate(n) if v[0]=='store' and v[5] is not None and v[5][1]==16}
cp=[None]*len(n);choice=[None]*len(n)
for i in range(len(n)-1,-1,-1):
 candidates=[j for j in n[i][3] if cp[j] is not None]
 if candidates:
  j=max(candidates,key=lambda j:cp[j]);cp[i]=cp[j]+1;choice[i]=j
 elif i in end:cp[i]=1
loads=[i for i,v in enumerate(n) if v[0] in ('load','record')]

flows=[i for i,v in enumerate(n) if v[0]=='flow']
constants=[i for i,v in enumerate(n) if v[0]=='constflex']
print('LOAD',len(loads),'minimum-tail',min(cp[i] for i in loads)-1)
print('FLOW',len(flows),'minimum-tail',min(cp[i] for i in flows)-1)
print('CONST',len(constants),'minimum-tail',min(cp[i] for i in constants)-1)
for T in [849,863,864,865,866]:
 lc=min(2*(T-d+1)-sum(cp[i]>=d for i in loads) for d in {cp[i] for i in loads} if d<=min(cp[i] for i in constants))
 fc=min((T-d+1)-1-sum(cp[i]>=d for i in flows) for d in {cp[i] for i in flows} if d<=min(cp[i] for i in constants))
 alu=len(constants)-lc-fc
 print('T',T,'maxconstantload',lc,'maxconstantflow',fc,'minimumconstantALU',alu,'minimum-arith',51570+alu,'minimum-with-startup52-tail116',51570+alu+168)
