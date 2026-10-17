import argparse,sys,random,time
import z3
P=argparse.ArgumentParser();P.add_argument('--input-xor',type=lambda s:int(s,0),default=0xc761c23c);P.add_argument('--width',type=int,default=32);P.add_argument('--m3',default='9');P.add_argument('--samples',type=int,default=32);P.add_argument('--timeout',type=int,default=60000);P.add_argument('--mask',default='free');o=P.parse_args()
w=o.width; mod=(1<<w)-1
m1,m2,aa,bb,cc,mm,mu=z3.BitVecs('m1 m2 aa bb cc mm mu',w)
m3=mu if o.m3=='free' else z3.BitVecVal(int(o.m3)&mod,w)
mask=mm if o.mask=='free' else z3.BitVecVal(int(o.mask,0)&mod,w)
def target(x):
 t=x^(o.input_xor&mod)
 return (9*(((33*t+0xe9f8cc1d)&mod)^((16896*t+0xaccf6200)&mod))+0xfd7046c5)&mod

def cand(x):return m3*((m1*x+aa)^(m2*x+bb))+cc ^mask
rng=random.Random(475823)
xs=[0,1,2,3,mod,1<<(w-1)]+[rng.getrandbits(w) for _ in range(o.samples-6)]
so=z3.Solver();so.set(timeout=o.timeout);so.add(m1&1==1,m2&1==0,m3&1==1)
for xv in xs:so.add(cand(z3.BitVecVal(xv,w))==target(xv))
for it in range(20):
 t=time.time();res=so.check();print('check',o.width,o.m3,o.mask,it,res,round(time.time()-t,3),flush=True)
 if res!=z3.sat:break
 mo=so.model();pars={str(q):mo.eval(q,model_completion=True).as_long() for q in (m1,m2,aa,bb,cc,mm,mu)}
 print({k:hex(v) for k,v in pars.items()},flush=True)
 xx=z3.BitVec('xx',w); tt=xx^(o.input_xor&mod)
 ref=9*((33*tt+0xe9f8cc1d)^(16896*tt+0xaccf6200))+0xfd7046c5
 ve=z3.Solver();ve.set(timeout=o.timeout);ve.add(mo.eval(cand(xx),model_completion=True)!=ref)
 r=ve.check();print('verify',r,flush=True)
 if r!=z3.sat:break
 bad=ve.model()[xx].as_long();print('counterexample',hex(bad),flush=True);so.add(cand(z3.BitVecVal(bad,w))==target(bad))
