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
sampler_exe=build/('test_sampler.exe' if os.name=='nt' else 'test_sampler')
run('Compile role-local sensor tests',[*common,'-I',root/'tests/arduino_stub',
    src/'Controller.cpp',src/'UmbProtocol.cpp',root/'tests/test_sampler.cpp','-o',sampler_exe])
run('Run role-local sensor tests',[sampler_exe])
run('Python reference codec tests',[sys.executable,'-m','unittest','discover','-s',root/'tests','-p','test_wire.py','-v'])
for role in ['AirManagerBench','MaterialStationBench']:
    sketch=root/f'firmware/UmbReplacement/examples/{role}/{role}.ino'
    syntax=[*common,'-I',root/'tests/arduino_stub','-DARDUINO_ARCH_STM32','-x','c++','-fsyntax-only']
    run(f'{role} disabled syntax ONLY (stub APIs)',[*syntax,sketch])
    # Wide STM32 pin IDs ensure no truncating uint8 pin assumptions in the entry point.
    enabled=['-DUMB_BOARD_CONFIGURED=1','-DUMB_ROLE_ENABLE_PIN=512',
             '-DUMB_ENABLE_TRANSPORT=1','-DUMB_UART_RX_PIN=513','-DUMB_UART_TX_PIN=514',
             '-DUMB_ENABLE_SENSORS=1','-DUMB_I2C_SDA_PIN=515','-DUMB_I2C_SCL_PIN=516']
    run(f'{role} configured syntax ONLY (stub APIs)',[*syntax,*enabled,sketch])
# Fail-closed compile checks: unsupported MCU and unconfigured UART must reject.
sketch=root/'firmware/UmbReplacement/examples/AirManagerBench/AirManagerBench.ino'
for label,flags in [('Reject unsupported MCU sketch',[]),
                    ('Reject unconfigured transport',['-DARDUINO_ARCH_STM32','-DUMB_ENABLE_TRANSPORT=1']),
                    ('Reject simultaneous roles',['-DARDUINO_ARCH_STM32','-DUMB_BUILD_MATERIAL_STATION'])]:
    cmd=[*common,'-I',root/'tests/arduino_stub',*flags,'-x','c++','-fsyntax-only',sketch]
    proc=subprocess.run([str(x) for x in cmd],env=env,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    expected={'Reject unsupported MCU sketch':'target STM32duino',
              'Reject unconfigured transport':'Configure reviewed STM32 board pins',
              'Reject simultaneous roles':'Select exactly one role'}[label]
    passed=proc.returncode!=0 and expected in proc.stdout
    results.append({'check':label,'returncode':0 if passed else 1,'output':'Expected compile rejection observed' if passed else proc.stdout})
    print(label+(': PASS' if passed else ': FAIL'))
    if not passed: raise SystemExit(1)
(build/'validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8',newline='\n')
print('PASS. Real STM32 core compile, SRAM/stack use and electrical/hardware behavior remain UNTESTED.')
