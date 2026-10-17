"""Actual32-bit, three-op nonlinear core candidates with12-bit witnesses."""
import argparse
import itertools
import json
import multiprocessing
import random
import sys
import time
import z3


def solve(job):
    first,second,addend,timeout,samples=job
    k,m,c,out=z3.BitVecs('k m c out',32)
    params=[k,m,c,out]
    def cand(x):
        if first=='and': t=x&k
        elif first=='or':t=x|k
        elif first=='xor':t=x^k
        elif first=='shr':t=z3.LShR(x,k)
        elif first=='shl':t=x<<k
        elif first=='rem':t=z3.URem(x,k)
        elif first=='div':t=z3.UDiv(x,k)
        elif first=='ceil':
            t=z3.Extract(31,0,z3.UDiv(z3.ZeroExt(1,x)+z3.ZeroExt(1,k)-1,z3.ZeroExt(1,k)))
        if second=='and':u=t&x
        elif second=='or':u=t|x
        elif second=='xor':u=t^x
        elif second=='add':u=t+x
        elif second=='sub':u=t-x
        elif second=='rsub':u=x-t
        elif second=='mul':u=t*x
        return m*u+{'x':x,'t':t,'c':c}[addend]
    def target(x):
        return 9*((33*x+0xe9f8cc1d)^(16896*x+0xaccf6200))+0xfd7046c5
    project=lambda x:z3.Extract(11,0,x)
    solver=z3.SolverFor('QF_BV');solver.set(timeout=timeout)
    if first in ('div','ceil','rem'):solver.add(k!=0)
    if first in ('shr','shl'):solver.add(z3.ULT(k,32))
    rng=random.Random(101718)
    examples=list(range(min(16,samples)))+[rng.getrandbits(32) for _ in range(max(0,samples-16))]
    seen=set();start=time.monotonic()
    result={'first':first,'second':second,'add':addend}
    for iteration in range(8):
        for v in examples:
            if v in seen:continue
            seen.add(v);x=z3.BitVecVal(v,32)
            solver.add(project(cand(x)^out)==project(target(x)))
        res=solver.check()
        result.update(result=str(res),samples=len(seen),seconds=round(time.monotonic()-start,3))
        if res!=z3.sat:return result
        model=solver.model();vals=[model.eval(p,model_completion=True).as_long() for p in params]
        result['params']={str(p):hex(v) for p,v in zip(params,vals)}
        x=z3.BitVec('verify_x',32)
        candidate=z3.substitute(cand(x)^out,*[(p,z3.BitVecVal(v,32)) for p,v in zip(params,vals)])
        verify=z3.SolverFor('QF_BV');verify.set(timeout=timeout)
        verify.add(project(candidate)!=project(target(x)))
        vr=verify.check();result['verify']=str(vr)
        if vr!=z3.sat:return result
        examples=[verify.model().eval(x).as_long()]+[rng.getrandbits(32) for _ in range(7)]
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--first',default='shr,shl')
    ap.add_argument('--second',default='and,or,xor')
    ap.add_argument('--add',default='x,t,c')
    ap.add_argument('--timeout',type=int,default=10000)
    ap.add_argument('--samples',type=int,default=32)
    ap.add_argument('--workers',type=int,default=2)
    args=ap.parse_args()
    jobs=[(*case,args.timeout,args.samples) for case in itertools.product(args.first.split(','),args.second.split(','),args.add.split(','))]
    with multiprocessing.Pool(args.workers) as pool:
        for result in pool.imap_unordered(solve,jobs):
            print(json.dumps(result),flush=True)
