from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import importlib.util,json,re,random
M=(1<<32)-1
C1=0xc761c23c;A=0xe9f8cc1d;B=0xaccf6200;C4=0xfd7046c5;C5=0xb55a4f09
base=Path(__file__).with_name('baseline.py').read_text()
variants=[]
for name,c1,a,b,mv,c4,flip in [
 ('identity',C1,A,B,16896,C4,False),
 ('both_branches_complement',C1^M,(32-A)&M,(16895-B)&M,16896,C4,False),
 ('v_branch_complement',C1,A,B^M,(-16896)&M,(8-C4)&M,True),
 ('u_branch_complement',C1^M,(32-A)&M,(B-16896)&M,(-16896)&M,(8-C4)&M,True)]:
 for msb in [False,True]:
  c4x=c4^(0x80000000 if msb else 0)
  c5x=C5^(0xffff0000 if flip else 0)^(0x80008000 if msb else 0)
  repl={'0xc761c23c':hex(c1),'0xe9f8cc1d':hex(a),'0xaccf6200':hex(b),'0xfd7046c5':hex(c4x),'0xb55a4f09':hex(c5x),'16896':str(mv)}
  source=re.sub(r'0xc761c23c|0xe9f8cc1d|0xaccf6200|0xfd7046c5|0xb55a4f09|\b16896\b',lambda m:repl[m.group()],base)
  tag=name+('_msb' if msb else '')
  path=Path(__file__).with_name(tag+'.py');path.write_text(source)
  rng=random.Random(319)
  for x in [0,1,M,1<<31]+[rng.getrandbits(32) for _ in range(1024)]:
   z=(4097*x+0x7ed55d16)&M;bb=z^(z>>19)^C1
   f=(9*(((33*bb+A)&M)^((16896*bb+B)&M))+C4)&M
   want=f^(f>>16)^C5
   bb=z^(z>>19)^c1
   f=(9*(((33*bb+a)&M)^((mv*bb+b)&M))+c4x)&M
   got=f^(f>>16)^c5x
   assert got==want,(tag,x,hex(got),hex(want))
  spec=importlib.util.spec_from_file_location(tag,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  k=module.KernelBuilder();k.build_kernel(10,2047,256,16)
  counts=dict(k.counts)
  result={'name':tag,'cycles':len(k.instrs),'scratch':k.scratch_ptr,'weight':counts['alu']+8*counts['valu'],'counts':counts,'hash_checks':1028}
  variants.append(result);print(json.dumps(result),flush=True)
  Path(__file__).with_name('free_gauges_results.json').write_text(json.dumps(variants,indent=2)+'\n')
