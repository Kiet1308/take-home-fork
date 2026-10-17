"""Three-instruction nonlinear hash cores with a live input feedforward."""
import argparse
import json
import random
import sys
import time
import z3


def solve(form,width,timeout,samples,lowbits=None):
    m,a,n,c,k,out=z3.BitVecs('m a n c k out',width)
    params=[m,a,n,c,k,out]
    def cand(x):
        t=m*x+a
        if form.startswith('shr_t_'):
            u=z3.LShR(t,k)
            if form.endswith('mad_x'):return n*x+u
            if form.endswith('mad_t'):return n*t+u
            if form.endswith('add_x'):return n*u+x
            if form.endswith('add_t'):return n*u+t
            if form.endswith('mul_x'):return x*u+c
            if form.endswith('mul_t'):return t*u+c
        if form.startswith('and_x_') or form.startswith('or_x_'):
            u=(t&x) if form.startswith('and') else (t|x)
            if form.endswith('square_add_x'):return u*u+x
            if form.endswith('square_add_t'):return u*u+t
            if form.endswith('add_x'):return n*u+x
            if form.endswith('add_t'):return n*u+t
            if form.endswith('mul_x'):return x*u+c
            if form.endswith('mul_t'):return t*u+c
        if form=='xor_x_add_x': return n*(t^x)+x
        if form=='xor_x_add_t': return n*(t^x)+t
        if form=='xor_x_mul_x': return x*(t^x)+c
        if form=='xor_x_mul_t': return t*(t^x)+c
        if form=='xor_k_mul_x': return x*(t^k)+c
        if form=='xor_k_mul_t': return t*(t^k)+c
        if form=='xor_k_add_x': return n*(t^k)+x
        if form=='xor_k_add_t': return n*(t^k)+t
        if form=='square_xor_k_add_x': return n*((x*x+a)^k)+x
        if form=='square_xor_x_add_x': return n*((x*x+a)^x)+x
        raise ValueError(form)
    def target(x):
        return 9*((33*x+0xe9f8cc1d)^(16896*x+0xaccf6200))+0xfd7046c5
    solver=z3.SolverFor('QF_BV');solver.set(timeout=timeout)
    if form.startswith('shr_t_'):solver.add(z3.ULT(k,width))
    project=(lambda x:z3.Extract(lowbits-1,0,x)) if lowbits else (lambda x:x)
    rng=random.Random(101718)
    examples=list(range(min(16,samples)))+[rng.getrandbits(width) for _ in range(max(0,samples-16))]
    seen=set()
    for iteration in range(100):
        for v in examples:
            if v in seen:continue
            seen.add(v)
            x=z3.BitVecVal(v,width)
            solver.add(project(cand(x)^out)==project(target(x)))
        start=time.monotonic();res=solver.check()
        print(json.dumps({'form':form,'width':width,'iteration':iteration,'samples':len(seen),'result':str(res),'seconds':time.monotonic()-start}),flush=True)
        if res!=z3.sat:return
        model=solver.model()
        vals=[model.eval(p,model_completion=True).as_long() for p in params]
        print({str(p):hex(v) for p,v in zip(params,vals)},flush=True)
        x=z3.BitVec('verify_x',width)
        candidate=z3.substitute(cand(x)^out,*[(p,z3.BitVecVal(v,width)) for p,v in zip(params,vals)])
        verify=z3.SolverFor('QF_BV');verify.set(timeout=timeout)
        verify.add(project(candidate)!=project(target(x)))
        result=verify.check();print('verify',result,flush=True)
        if result!=z3.sat:return
        examples=[verify.model().eval(x).as_long()]+[rng.getrandbits(width) for _ in range(7)]


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('form',choices=['xor_x_add_x','xor_x_add_t','xor_x_mul_x','xor_x_mul_t','xor_k_mul_x','xor_k_mul_t','xor_k_add_x','xor_k_add_t','square_xor_k_add_x','square_xor_x_add_x']+[op+'_x_'+end for op in ('and','or') for end in ('add_x','add_t','mul_x','mul_t','square_add_x','square_add_t')]+['shr_t_'+end for end in ('mad_x','mad_t','add_x','add_t','mul_x','mul_t')])
    ap.add_argument('--width',type=int,default=12)
    ap.add_argument('--timeout',type=int,default=60000)
    ap.add_argument('--samples',type=int,default=32)
    ap.add_argument('--lowbits',type=int)
    args=ap.parse_args()
    solve(args.form,args.width,args.timeout,args.samples,args.lowbits)
