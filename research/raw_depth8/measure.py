import json
import os
import sys
from pathlib import Path

folder = Path(__file__).resolve().parent
repo = next((p for p in folder.parents if (p / 'tests' / 'frozen_problem.py').is_file()),
            folder.parent / 'take-home-fork')
sys.path.insert(0, str(repo))
from kernel import KernelBuilder

sys.path.insert(0, str(repo / 'tests'))
from frozen_problem import Machine, Tree, Input, build_mem_image, reference_kernel2


def measure(params, validate=True):
    previous = dict(os.environ)
    try:
        for key, value in params.items():
            os.environ[key] = value if isinstance(value, str) else json.dumps(value)
        kb = KernelBuilder()
        kb.build_kernel(10, 2047, 256, 16)
        counts = dict(kb.counts)
        result = {'params': params, 'cycles': len(kb.instrs), 'scratch': kb.scratch_ptr,
                  'counts': counts, 'weight': counts.get('alu', 0) + 8 * counts.get('valu', 0)}
        result['early_weight'] = [len(b.get('alu', [])) + 8 * len(b.get('valu', [])) for b in kb.instrs[:12]]
        result['prefix_deficit16'] = sum(60-len(b.get('alu', []))-8*len(b.get('valu', [])) for b in kb.instrs[:16])
        result['first_hash'] = {}
        for cycle, used in enumerate(kb.ir.schedule_usage):
            for node_id in used:
                node = kb.ir.nodes[node_id]
                if node[5] == (0, 0):
                    result['first_hash'].setdefault(str(node[1][0]), []).append(cycle)
        result['last_raw_prep'] = max((cycle for cycle,used in enumerate(kb.ir.schedule_usage) if any(kb.ir.nodes[i][0]=='prepstore' for i in used)),default=None)
        result['first_r7_record'] = min((cycle for cycle,used in enumerate(kb.ir.schedule_usage) if any(kb.ir.nodes[i][0]=='record' and kb.ir.nodes[i][5] is not None and kb.ir.nodes[i][5][1]==7 for i in used)),default=None)
        if validate:
            tree = Tree.generate(10)
            inp = Input.generate(tree, 256, 16)
            mem = build_mem_image(tree, inp)
            machine = Machine(mem, kb.instrs, kb.debug_info())
            machine.enable_pause = False
            machine.enable_debug = False
            machine.run()
            for reference in reference_kernel2(mem):
                pass
            start = reference[6]
            assert machine.mem[start:start+256] == reference[start:start+256], 'Incorrect output'
            result['correct'] = True
            result['machine_cycles'] = machine.cycle
        return result
    finally:
        os.environ.clear()
        os.environ.update(previous)


if __name__ == '__main__':
    configs = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else [
        {'BOOT_COMBO':'0', 'HC_INTERLEAVED':'0'},
        {'HC_PATTERN_WORDS':[4,4], 'HC_NINE_PAIR':'0', 'HC_FLOW':{'0xaccf6200':4,'0xfd7046c5':5}},
        {'HC_PATTERN_WORDS':[8,8], 'HC_NINE_PAIR':'0', 'HC_FLOW':{'0xaccf6200':4,'0xfd7046c5':5}},
        {'HC_PATTERN_WORDS':[0,0], 'HC_NINE_PAIR':'0', 'HC_FLOW':{'0xaccf6200':4,'0xfd7046c5':5}},
    ]
    results = []
    for params in configs:
        try:
            result = measure(params)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            result = {'params':params, 'error':repr(exc)}
        results.append(result)
        print(json.dumps(result), flush=True)
        (folder / 'results.json').write_text(json.dumps(results, indent=2)+'\n')
