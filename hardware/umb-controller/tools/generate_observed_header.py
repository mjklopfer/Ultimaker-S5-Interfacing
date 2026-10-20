"""Generate ordinary const STM32/native catalog data from the reviewed JSON."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'endpoint_catalog.json').read_text(encoding='utf-8'))['registers']
header=['// GENERATED register catalog. Const names/flags for STM32 and native tests.',
        '#pragma once','#include <stddef.h>','#include <string.h>','namespace umb {']
for prefix,role in [('Air','air_manager'),('Material','material_station')]:
    subset=[r for r in rows if r['role']==role]
    for i,row in enumerate(subset):
        header.append(f'static const char {prefix}Name{i}[] = {json.dumps(row["name"])};')
    names=','.join(f'{prefix}Name{i}' for i in range(len(subset)))
    flags=','.join('1' if r['draft_writable'] else '0' for r in subset)
    header += [f'static const char* const {prefix}Names[] = {{{names}}};',
               f'static const unsigned char {prefix}Writable[] = {{{flags}}};',
               f'constexpr size_t {prefix}Count = {len(subset)};']
header += [
    'inline bool catalogName(bool air,size_t i,char* out,size_t cap) {',
    ' if (i >= (air?AirCount:MaterialCount) || !cap) return false;',
    ' const char* name=(air?AirNames:MaterialNames)[i];',
    ' const size_t n=strlen(name); if (n>=cap) return false;',
    ' memcpy(out,name,n+1); return true;',
    '}',
    'inline bool catalogWritable(bool air,size_t i) {',
    ' if (i >= (air?AirCount:MaterialCount)) return false;',
    ' return (air?AirWritable:MaterialWritable)[i]!=0;',
    '}',
    'static_assert(AirCount+20<=256 && MaterialCount+20<=256,"Increase router monitor capacity");',
    '}']
(ROOT/'firmware/UmbReplacement/src/ObservedCatalog.h').write_text('\n'.join(header)+'\n',encoding='utf-8',newline='\n')
print(f'Generated {len(rows)} const register names/flags for STM32/native tests.')
