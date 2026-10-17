import copy
from collections import defaultdict

GUIDE = None

def capture(ir, ins, usage):
    return dict(nodes=copy.deepcopy(ir.nodes), ins=copy.deepcopy(ins),
                usage=copy.deepcopy(usage), zero=ir.const_zero,
                owner=ir.owner.copy(), width=ir.width.copy())

def prefix(ir, changed, cutoff=None):
    old = GUIDE
    if old is None:
        return None
    def index(nodes):
        counts=defaultdict(int); result={}
        for i,n in enumerate(nodes):
            ctx=n[5]
            if ctx in changed:
                continue
            key=(ctx,counts[ctx]); counts[ctx]+=1
            result[key]=i
        return result
    a=index(old['nodes']); b=index(ir.nodes)
    assert a.keys()==b.keys(),(a.keys()-b.keys(),b.keys()-a.keys())
    imap={i:b[key] for key,i in a.items()}
    word={old['zero']:ir.const_zero}
    for oi,ni in imap.items():
        on,nn=old['nodes'][oi],ir.nodes[ni]
        assert on[0]==nn[0] and on[1][0]==nn[1][0],(oi,ni,on[:2],nn[:2])
        for oa,na in zip(on[7],nn[7]):
            assert oa not in word or word[oa]==na,(oi,ni,oa,word.get(oa),na)
            word[oa]=na
        for oa,na in zip(on[6],nn[6]):
            assert oa not in word or word[oa]==na,(oi,ni,oa,word.get(oa),na)
            word[oa]=na
    owner_map={old['owner'][oa]:ir.owner[na] for oa,na in word.items()}
    for oa,na in owner_map.items():
        assert old['width'][oa]==ir.width[na],(oa,na,old['width'][oa],ir.width[na])
        for k in range(old['width'][oa]):
            assert oa+k not in word or word[oa+k]==na+k
            word[oa+k]=na+k
    changed_cycles=[t for t,ids in enumerate(old['usage'])
                    if any(old['nodes'][i][5] in changed for i in ids)]
    cutoff=min(changed_cycles) if cutoff is None else cutoff
    assert all(old['nodes'][i][5] not in changed
               for ids in old['usage'][:cutoff] for i in ids)
    ins=[]
    for bundle in old['ins'][:cutoff]:
        new={}
        for engine,slots in bundle.items():
            assert engine!='lookup_target'
            ns=[]
            for s in slots:
                if s[0] in ('const','lookup_tablebase'):
                    ns.append((s[0],word[s[1]],s[2]))
                elif s[0] in ('add_imm','lookup_base'):
                    ns.append((s[0],word[s[1]],word[s[2]],s[3]))
                else:
                    ns.append((s[0],*(word[x] for x in s[1:])))
            new[engine]=ns
        ins.append(new)
    usage=[{imap[i] for i in ids} for ids in old['usage'][:cutoff]]
    last={i:t for t,ids in enumerate(old['usage']) for i in ids}
    completed=[False]*len(ir.nodes); partial=[]
    for oi,ni in imap.items():
        if last.get(oi,cutoff)<cutoff:
            completed[ni]=True
        elif any(oi in ids for ids in old['usage'][:cutoff]):
            on=old['nodes'][oi]; assert on[0]=='flex',(oi,on)
            dest=on[1][1]
            count=sum(dest<=s[1]<dest+8 for bundle in old['ins'][:cutoff]
                      for s in bundle.get('alu',[]))
            assert 0<count<8,(oi,count)
            partial.append((ni,count))
        if any(oi in ids for ids in old['usage'][:cutoff]):
            ir.nodes[ni][6]=[word[x] for x in old['nodes'][oi][6]]
    return ins,usage,completed,partial,cutoff


def insert_metadata(ir,frozen,changed):
    ins,usage,completed,partial,cutoff=frozen
    available={i:t+1 for t,ids in enumerate(usage) for i in ids}
    for i,k in partial:available.pop(i,None)
    candidates={i for i,n in enumerate(ir.nodes) if n[5] in changed and n[0] in ('store','load')}
    for cycle,bundle in enumerate(ins):
        for engine,capacity in [('store',2),('load',2)]:
            for _ in range(capacity-len(bundle.get(engine,[]))):
                ready=[i for i in candidates if ir.nodes[i][0]==engine and all(available.get(d,1000000)<=cycle for d in ir.nodes[i][2])]
                if not ready:break
                i=min(ready);candidates.remove(i)
                bundle.setdefault(engine,[]).append(ir.nodes[i][1])
                usage[cycle].add(i);completed[i]=True;available[i]=cycle+1
    return ins,usage,completed,partial,cutoff
