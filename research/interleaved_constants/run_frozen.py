import json, os, sys, types, runpy
from pathlib import Path
folder=Path(__file__).resolve().parent
repo=folder.parents[1]
os.chdir(repo)
sys.path.insert(0,str(repo))
params=json.loads((folder/'parameters.json').read_text())['params']
for key,value in params.items(): os.environ[key]=json.dumps(value)
for key in ('FAST_SCHEDULE','NOEMIT'): os.environ.pop(key,None)
module=types.ModuleType('perf_takehome')
module.__file__=str(folder/'kernel.py')
exec(compile((folder/'kernel.py').read_text(),module.__file__,'exec'),module.__dict__)
sys.modules['perf_takehome']=module
sys.argv=['tests/submission_tests.py']
sys.path.insert(0,'tests')
runpy.run_path('tests/submission_tests.py',run_name='__main__')
