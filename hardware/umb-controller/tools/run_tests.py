"""Local native C++ tests and Arduino sketch syntax check. NEVER opens a serial port."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler',default=shutil.which('g++') or 'g++')
args=parser.parse_args()
compiler=Path(args.compiler)
env=os.environ.copy()
env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
env['PYTHONDONTWRITEBYTECODE']='1'
build=root/'build';build.mkdir(exist_ok=True)
results=[]
def run(label,cmd):
    proc=subprocess.run([str(s) for s in cmd],env=env,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(label+':\n'+proc.stdout)
    results.append({'check':label,'returncode':proc.returncode,'output':proc.stdout})
    if proc.returncode:
        (build/'validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8',newline='\n')
        raise SystemExit(proc.returncode)
src=root/'firmware/UmbReplacement/src'
exe=build/('test_core.exe' if os.name=='nt' else 'test_core')
common=[compiler,'-std=c++11','-Wall','-Wextra','-Werror','-pedantic','-I',src]
run('Compile native core',[*common,*[src/(n+'.cpp') for n in ['UmbProtocol','Controller','FanModel','ThermalControl']],root/'tests/test_core.cpp','-o',exe])
run('Run native core',[exe])
run('Python reference codec tests',[sys.executable,'-m','unittest','discover','-s',root/'tests','-p','test_wire.py','-v'])
run('Arduino sketch syntax ONLY (stub APIs)',[*common,'-I',root/'tests/arduino_stub','-x','c++','-fsyntax-only',root/'firmware/UmbReplacement/examples/ReplacementBench/ReplacementBench.ino'])
(build/'validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8',newline='\n')
print('PASS. Target AVR compile, SRAM/stack use and electrical/hardware behavior remain UNTESTED.')
