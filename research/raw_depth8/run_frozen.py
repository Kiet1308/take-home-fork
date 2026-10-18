"""Run the bootstrap candidate against the repository's frozen tests."""
import json
import os
from pathlib import Path
import runpy
import sys
import types

folder = Path(__file__).resolve().parent
repo = next((p for p in folder.parents if (p / 'tests' / 'frozen_problem.py').is_file()),
            folder.parent / 'take-home-fork')
os.chdir(repo)
sys.path.insert(0, str(repo))
for key, value in json.loads((folder / 'best_parameters.json').read_text()).items():
    os.environ[key] = value if isinstance(value, str) else json.dumps(value)
for key in ('FAST_SCHEDULE', 'NOEMIT'):
    os.environ.pop(key, None)
module = types.ModuleType('perf_takehome')
module.__file__ = str(folder / 'kernel.py')
exec(compile((folder / 'kernel.py').read_text(), module.__file__, 'exec'), module.__dict__)
sys.modules['perf_takehome'] = module
sys.path.insert(0, str(repo / 'tests'))
sys.argv = ['tests/submission_tests.py']
runpy.run_path('tests/submission_tests.py', run_name='__main__')
