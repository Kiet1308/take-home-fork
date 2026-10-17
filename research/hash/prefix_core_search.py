"""Cores using genuine free intermediates from the first XOR-shift prefix.

At12 output bits, b and q=a>>19 are independent12-bit inputs. Thus this
projection is exact for falsification of every32-bit program in these families.
"""
import argparse
import json
import random
import sys
import time
import z3


def solve(kind,timeout,samples,outer_free=False,fixes=None,combine='xor',first_free=False):
    width=12
    m1,m2,m3,a,b,c,k,out=z3.BitVecs('m1 m2 m3 a b c k out',width)
    constants=[m1,m2,m3,a,b,c,k,out]
    selectors={}
    limits={}
    def pick(name,values):
        if name not in selectors:
            selectors[name]=z3.BitVec(name,4)
            limits[name]=len(values)
        s=selectors[name]
        result=values[-1]
        for i in range(len(values)-2,-1,-1):
            result=z3.If(s==i,values[i],result)
        return result
    def cand(x,q):
        if kind=='drop4':
            src=[x,x^q,q]
        else:
            src=[x,x^q^0xc761c23c,q,x^q]
        coefficient1=pick('co1',[m1]+src) if first_free else m1
        t=coefficient1*pick('s1',src)+pick('a1',[a]+src)
        if kind in ('two_mad','drop4'):
            u=m2*pick('s2',src)+pick('a2',[b]+src)
            d=t^u
            if kind=='two_mad':return d
            coeff=pick('co3',[m3]+src) if outer_free else m3
            return coeff*d+pick('a3',[c]+src+[t,u])
        operand=pick('sx',src+[k])
        if combine=='xor':u=t^operand
        elif combine=='and':u=t&operand
        elif combine=='or':u=t|operand
        elif combine=='add':u=t+operand
        elif combine=='sub':u=t-operand
        elif combine=='rsub':u=operand-t
        elif combine=='mul':u=t*operand
        else:raise ValueError(combine)
        coeff=pick('co3',[m3]+src+[t]) if outer_free else m3
        return coeff*u+pick('a3',[c]+src+[t])
    def target(x):
        if kind=='drop4':x=x^0xc761c23c
        return 9*((33*x+0xe9f8cc1d)^(16896*x+0xaccf6200))+0xfd7046c5
    solver=z3.SolverFor('QF_BV');solver.set(timeout=timeout)
    rng=random.Random(20612)
    examples=[(x,rng.getrandbits(width)) for x in range(16)]
    examples += [(rng.getrandbits(width),rng.getrandbits(width)) for _ in range(max(0,samples-16))]
    examples += [(x,q) for x in range(4) for q in (0,4095)]
    examples += [(x,q) for x in (0,1,1024,1025) for q in (0,1,1024,1025,4095)]
    seen=set();start=time.monotonic()
    x,q=z3.BitVecs('verify_x verify_q',width)
    expression=cand(x,q)^out
    for name,lim in limits.items():solver.add(z3.ULT(selectors[name],lim))
    for name,value in (fixes or {}).items():solver.add(selectors[name]==value)
    # Canonical ordering removes the symmetry of the two XOR branches.
    if kind in ('two_mad','drop4'):
        solver.add(z3.ULE(selectors['s1'],selectors['s2']))
    params=constants+list(selectors.values())
    for iteration in range(20):
        for xv,qv in examples:
            if (xv,qv) in seen:continue
            seen.add((xv,qv))
            xx,qq=z3.BitVecVal(xv,width),z3.BitVecVal(qv,width)
            solver.add(cand(xx,qq)^out==target(xx))
        res=solver.check()
        print(json.dumps({'kind':kind,'combine':combine,'first_free':first_free,'outer_free':outer_free,'fixes':fixes,'result':str(res),'samples':len(seen),'seconds':round(time.monotonic()-start,3)}),flush=True)
        if res!=z3.sat:return
        model=solver.model();vals=[model.eval(p,model_completion=True).as_long() for p in params]
        print({str(p):hex(v) for p,v in zip(params,vals)},flush=True)
        ver=z3.SolverFor('QF_BV');ver.set(timeout=timeout)
        replacement=[(p,z3.BitVecVal(v,p.size())) for p,v in zip(params,vals)]
        fixed=z3.substitute(expression,*replacement)
        ver.add(fixed!=target(x));vr=ver.check()
        print('verify',vr,flush=True)
        if vr!=z3.sat:return
        vm=ver.model();examples=[(vm.eval(x).as_long(),vm.eval(q).as_long())]
        examples += [(rng.getrandbits(width),rng.getrandbits(width)) for _ in range(7)]


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('kind',choices=['two_mad','feed','drop4'])
    ap.add_argument('--outer_free',action='store_true')
    ap.add_argument('--first_free',action='store_true')
    ap.add_argument('--combine',choices=['xor','and','or','add','sub','rsub','mul'],default='xor')
    ap.add_argument('--timeout',type=int,default=60000)
    ap.add_argument('--samples',type=int,default=32)
    ap.add_argument('--fix',type=json.loads)
    args=ap.parse_args()
    solve(args.kind,args.timeout,args.samples,args.outer_free,args.fix,args.combine,args.first_free)
