"""
# Anthropic's Original Performance Engineering Take-home (Release version)

Copyright Anthropic PBC 2026. Permission is granted to modify and use, but not
to publish or redistribute your solutions so it's hard to find spoilers.

# Task

- Optimize the kernel (in KernelBuilder.build_kernel) as much as possible in the
  available time, as measured by test_kernel_cycles on a frozen separate copy
  of the simulator.

Validate your results using `python tests/submission_tests.py` without modifying
anything in the tests/ folder.

We recommend you look through problem.py next.
"""

import random
import unittest
from problem import Machine, Tree, Input, N_CORES, build_mem_image, reference_kernel2, reference_kernel, HASH_STAGES
from collections import defaultdict
from problem import SLOT_LIMITS, VLEN, SCRATCH_SIZE, DebugInfo
import heapq

class KernelBuilder:
    def __init__(self):
        self.instrs=[]; self.ptr=0; self.names={}; self.ops=[]; self.lastw={}; self.reads=defaultdict(set); self.sconst={}; self.vconst={}
    def debug_info(self): return DebugInfo(self.names)
    def alloc(self,n=1,name=None):
        p=self.ptr;self.ptr+=n
        assert self.ptr<=SCRATCH_SIZE, self.ptr
        if name:self.names[p]=(name,n)
        return p
    def op(self,e,s,r,w):
        i=len(self.ops); deps=set()
        for a in r:
            if a in self.lastw:deps.add(self.lastw[a])
        for a in w:
            if a in self.lastw:deps.add(self.lastw[a])
            deps.update(self.reads[a])
        deps.discard(i)
        self.ops.append([e,s,deps,[]])
        for d in deps:self.ops[d][3].append(i)
        for a in w:self.reads[a].clear(); self.lastw[a]=i
        for a in r:
            if a not in w:self.reads[a].add(i)
        return i
    def sc(self,x):
        x&=0xffffffff
        if x not in self.sconst:
            p=self.alloc();self.sconst[x]=p;self.op('load',('const',p,x),[],[p])
        return self.sconst[x]
    def vc(self,x):
        x&=0xffffffff
        if x not in self.vconst:
            p=self.alloc(8);self.vconst[x]=p;self.op('valu',('vbroadcast',p,self.sc(x)),[self.sc(x)],range(p,p+8))
        return self.vconst[x]
    def v(self,o,d,a,b=None,c=None):
        s=(o,d,a) if b is None else ((o,d,a,b) if c is None else (o,d,a,b,c))
        r=([a] if o=='vbroadcast' else list(range(a,a+8)))
        if b is not None:r+=list(range(b,b+8))
        if c is not None:r+=list(range(c,c+8))
        return self.op('valu',s,r,range(d,d+8))
    def a(self,o,d,a,b):return self.op('alu',(o,d,a,b),[a,b],[d])
    def vv(self,o,d,a,b,scalar=False):
        if scalar:
            for k in range(8):self.a(o,d+k,a+k,b+k)
        else:self.v(o,d,a,b)
    def vs(self,d,cond,a,b):return self.op('flow',('vselect',d,cond,a,b),list(range(cond,cond+8))+list(range(a,a+8))+list(range(b,b+8)),range(d,d+8))
    def ld(self,d,a):return self.op('load',('load',d,a),[a],[d])
    def vl(self,d,a):return self.op('load',('vload',d,a),[a],range(d,d+8))
    def st(self,a,d):return self.op('store',('vstore',a,d),[a]+list(range(d,d+8)),[])
    def build_kernel(self,forest_height,n_nodes,batch_size,rounds):
        cfg='cs'
        cache=3
        n= batch_size//8
        vs=[self.alloc(8,f'value{g}') for g in range(n)]
        ix=[self.alloc(8,f'index{g}') for g in range(n)]
        t1=[self.alloc(8) for g in range(n)]
        t2=[self.alloc(8) for g in range(n)]
        shared3=[self.alloc(8) for g in range(8)]
        shared4=[self.alloc(8) for g in range(8)]
        t3=[shared3[g%8] for g in range(n)]
        t4=[shared4[g%8] for g in range(n)]
        # Constants
        one=self.vc(1);two=self.vc(2);base=self.vc(6)
        h0=self.vc(0x7ED55D16); h1=self.vc(0xC761C23C)
        h23=self.vc(0x165667B1+0xD3A2646C); h23s=self.vc((0x165667B1<<9)&0xffffffff)
        h4=self.vc(0xFD7046C5);h5=self.vc(0xB55A4F09)
        m0=self.vc(4097);m2=self.vc(33);m23=self.vc(16896);m4=self.vc(9)
        s19=self.vc(19);s16=self.vc(16)
        trees=[]
        for j in range((1<<(cache+1))-1):
            p=self.alloc(8,f'tree{j}');self.ld(p,self.sc(7+j));self.v('vbroadcast',p,p);trees.append(p)
        inptr=[self.sc(7+n_nodes+batch_size+g*8) for g in range(n)]
        for g in range(n):self.vl(vs[g],inptr[g])
        for r in range(rounds):
            depth=r%(forest_height+1)
            for g in range(n):
                x=vs[g];q=ix[g];a=t1[g];b=t2[g];c=t3[g];d=t4[g]
                if depth==0:
                    self.vv('^',x,x,trees[0], 'x' in cfg)
                elif depth==1:
                    self.vs(a,q,trees[2],trees[1]);self.vv('^',x,x,a,'x' in cfg)
                elif depth==2:
                    # q holds pathbits0..3
                    self.vv('&',a,q,one,'c' in cfg)
                    self.vs(b,a,trees[4],trees[3]); self.vs(c,a,trees[6],trees[5])
                    self.vv('>>',a,q,one,'c' in cfg);self.vs(b,a,c,b)
                    self.vv('^',x,x,b,'x' in cfg)
                elif depth==3 and cache>=3:
                    self.vv('&',a,q,one,'c' in cfg)
                    self.vs(b,a,trees[8],trees[7]);self.vs(c,a,trees[10],trees[9])
                    self.vv('&',a,q,two,'c' in cfg);self.vs(b,a,c,b)
                    self.vv('&',a,q,one,'c' in cfg)
                    self.vs(c,a,trees[12],trees[11]);self.vs(a,a,trees[14],trees[13])
                    self.vv('&',d,q,two,'c' in cfg)
                    self.vs(c,d,a,c)
                    self.vv('>>',d,q,two,'c' in cfg)
                    self.vs(b,d,c,b)
                    self.vv('^',x,x,b,'x' in cfg)
                else:
                    # q encodes level-local bits
                    self.vv('+',a,q,self.vc((1<<depth)-1+7),'a' in cfg)
                    for k in range(8):self.ld(a+k,a+k)
                    self.vv('^',x,x,a,'x' in cfg)
                self.v('multiply_add',x,x,m0,h0)
                self.vv('>>',a,x,s19,'s' in cfg)
                self.vv('^',x,x,h1,'h' in cfg)
                self.vv('^',x,x,a,'b' in cfg)
                self.v('multiply_add',a,x,m2,h23)
                self.v('multiply_add',b,x,m23,h23s)
                self.vv('^',x,a,b,'z' in cfg)
                self.v('multiply_add',x,x,m4,h4)
                self.vv('>>',a,x,s16,'s' in cfg)
                self.vv('^',x,x,h5,'h' in cfg)
                self.vv('^',x,x,a,'b' in cfg)
                if r+1<rounds and depth<forest_height:
                    if depth==0:self.vv('&',q,x,one,'i' in cfg)
                    else:
                        self.vv('&',a,x,one,'i' in cfg)
                        self.v('multiply_add',q,q,two,a)
        for g in range(n):self.st(inptr[g],vs[g])
        self.instrs.append({'flow': [('pause',)]})
        self.schedule()
        self.instrs.append({'flow': [('pause',)]})
    def schedule(self):
        n=len(self.ops); cp=[1]*n
        for i in range(n-1,-1,-1):
            if self.ops[i][3]:cp[i]=1+max(cp[j] for j in self.ops[i][3])
        indeg=[len(v[2]) for v in self.ops]
        ready=defaultdict(list)
        for i in range(n):
            if not indeg[i]:heapq.heappush(ready[self.ops[i][0]],(-cp[i],i))
        cnt=0
        while cnt<n:
            inst={};selected=[]
            for e,lim in SLOT_LIMITS.items():
                for _ in range(lim):
                    if not ready[e]:break
                    _,i=heapq.heappop(ready[e]);selected.append(i);inst.setdefault(e,[]).append(self.ops[i][1])
            assert selected
            self.instrs.append(inst);cnt+=len(selected)
            for i in selected:
                for j in self.ops[i][3]:
                    indeg[j]-=1
                    if not indeg[j]:heapq.heappush(ready[self.ops[j][0]],(-cp[j],j))

BASELINE = 147734

def do_kernel_test(
    forest_height: int,
    rounds: int,
    batch_size: int,
    seed: int = 123,
    trace: bool = False,
    prints: bool = False,
):
    print(f"{forest_height=}, {rounds=}, {batch_size=}")
    random.seed(seed)
    forest = Tree.generate(forest_height)
    inp = Input.generate(forest, batch_size, rounds)
    mem = build_mem_image(forest, inp)

    kb = KernelBuilder()
    kb.build_kernel(forest.height, len(forest.values), len(inp.indices), rounds)
    # print(kb.instrs)

    value_trace = {}
    machine = Machine(
        mem,
        kb.instrs,
        kb.debug_info(),
        n_cores=N_CORES,
        value_trace=value_trace,
        trace=trace,
    )
    machine.prints = prints
    for i, ref_mem in enumerate(reference_kernel2(mem, value_trace)):
        machine.run()
        inp_values_p = ref_mem[6]
        if prints:
            print(machine.mem[inp_values_p : inp_values_p + len(inp.values)])
            print(ref_mem[inp_values_p : inp_values_p + len(inp.values)])
        assert (
            machine.mem[inp_values_p : inp_values_p + len(inp.values)]
            == ref_mem[inp_values_p : inp_values_p + len(inp.values)]
        ), f"Incorrect result on round {i}"
        inp_indices_p = ref_mem[5]
        if prints:
            print(machine.mem[inp_indices_p : inp_indices_p + len(inp.indices)])
            print(ref_mem[inp_indices_p : inp_indices_p + len(inp.indices)])
        # Updating these in memory isn't required, but you can enable this check for debugging
        # assert machine.mem[inp_indices_p:inp_indices_p+len(inp.indices)] == ref_mem[inp_indices_p:inp_indices_p+len(inp.indices)]

    print("CYCLES: ", machine.cycle)
    print("Speedup over baseline: ", BASELINE / machine.cycle)
    return machine.cycle


class Tests(unittest.TestCase):
    def test_ref_kernels(self):
        """
        Test the reference kernels against each other
        """
        random.seed(123)
        for i in range(10):
            f = Tree.generate(4)
            inp = Input.generate(f, 10, 6)
            mem = build_mem_image(f, inp)
            reference_kernel(f, inp)
            for _ in reference_kernel2(mem, {}):
                pass
            assert inp.indices == mem[mem[5] : mem[5] + len(inp.indices)]
            assert inp.values == mem[mem[6] : mem[6] + len(inp.values)]

    def test_kernel_trace(self):
        # Full-scale example for performance testing
        do_kernel_test(10, 16, 256, trace=True, prints=False)

    # Passing this test is not required for submission, see submission_tests.py for the actual correctness test
    # You can uncomment this if you think it might help you debug
    # def test_kernel_correctness(self):
    #     for batch in range(1, 3):
    #         for forest_height in range(3):
    #             do_kernel_test(
    #                 forest_height + 2, forest_height + 4, batch * 16 * VLEN * N_CORES
    #             )

    def test_kernel_cycles(self):
        do_kernel_test(10, 16, 256)


# To run all the tests:
#    python perf_takehome.py
# To run a specific test:
#    python perf_takehome.py Tests.test_kernel_cycles
# To view a hot-reloading trace of all the instructions:  **Recommended debug loop**
# NOTE: The trace hot-reloading only works in Chrome. In the worst case if things aren't working, drag trace.json onto https://ui.perfetto.dev/
#    python perf_takehome.py Tests.test_kernel_trace
# Then run `python watch_trace.py` in another tab, it'll open a browser tab, then click "Open Perfetto"
# You can then keep that open and re-run the test to see a new trace.

# To run the proper checks to see which thresholds you pass:
#    python tests/submission_tests.py

if __name__ == "__main__":
    unittest.main()

