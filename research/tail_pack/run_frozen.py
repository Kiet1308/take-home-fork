import json,os,sys,types,runpy
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
os.chdir(repo)
sys.path.insert(0,str(repo))
import tail_freeze
source,config=(str(Path(__file__).with_name(name)) for name in ('kernel.py','parameters.json'))
params=json.loads(Path(config).read_text())['params']
for key,value in params.items():os.environ[key]=json.dumps(value)
os.environ.pop('FAST_SCHEDULE',None)
module=types.ModuleType('perf_takehome');module.__file__=str(Path(source).resolve())
exec(compile(Path(source).read_text(),module.__file__,'exec'),module.__dict__);sys.modules['perf_takehome']=module
saved=os.environ.pop('STRIDE1_EVENTS',None)
base=module.KernelBuilder();base.build_kernel(10,2047,256,16);tail_freeze.GUIDE=base.ir.freeze_guide
if saved is not None:os.environ['STRIDE1_EVENTS']=saved
sys.argv=['tests/submission_tests.py'];sys.path.insert(0,'tests');runpy.run_path('tests/submission_tests.py',run_name='__main__')
