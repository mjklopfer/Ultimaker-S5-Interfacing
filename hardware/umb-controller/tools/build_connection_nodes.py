"""Generate symbolic two-STM32 nodes; no physical pinout is claimed."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[]
def net(name, endpoints, domain='3.3V logic', status='R', notes=''):
    for component,pin,direction in endpoints:
        rows.append(dict(net=name,component=component,pin=pin,direction=direction,domain=domain,status=status,notes=notes))
def n(component,pin,direction='passive'): return component,pin,direction
net('P24_IN',[n('J_PWR24','PLUS'),n('F_MAIN','IN')],'24V power',notes='Separate supply; no identified UMB power contact')
net('P24_FUSED',[n('F_MAIN','OUT'),n('F_FAN','IN'),n('F_LOGIC','IN')],'24V power')
net('FAN_24V',[n('F_FAN','OUT'),n('FAN1','VCC')],'24V fan power',notes='Reported rating; verify fan model')
net('LOGIC_24V',[n('F_LOGIC','OUT'),n('U_PWR5','VIN')],'24V power')
net('BOARD_5V',[n('U_PWR5','VOUT'),n('U_AIR_POWER','EXTERNAL_INPUT'),n('U_MATERIAL_POWER','EXTERNAL_INPUT'),n('U_PWM','VCC')],'5V regulated power',notes='Board power selection and USB backfeed review; not MCU VDD')
for role in ['AIR','MATERIAL']:
    mcu='U_'+role
    net(role+'_BOARD_INPUT',[n('U_'+role+'_POWER','SELECTED_OUTPUT'),n(mcu,'BOARD_POWER_INPUT_TBD')],'board input TBD','H','Confirm exact board power input and regulator requirements')
    loads=[n(mcu,'BOARD_3V3_OUTPUT')]
    loads += [n('U_MUX','VIN')]+[n('S_C'+str(i),'VIN') for i in range(4)] if role=='AIR' else [n('S_M0','VIN'),n('U_GPIO_IN','VCC'),n('U_GPIO_OUT','VCC')]
    net(role+'_3V3',loads,'3.3V power',notes='Review regulator load and sensor/module pullups')
    net(role+'_ENABLE',[n(mcu,'PIN_ROLE_ENABLE_TBD','input/pullup'),n('JP_'+role,'1')],notes='Fixed role; active-low jumper enables this controller only')
    grounds=[n(mcu,'GND'),n('JP_'+role,'2'),n('U_'+role+'_POWER','GND'),n('U_'+role+'_UMB','MCU_GND')]
    grounds += [n('U_MUX','GND')]+[n('S_C'+str(i),'GND') for i in range(4)] if role=='AIR' else [n('S_M0','GND'),n('U_GPIO_IN','GND'),n('U_GPIO_OUT','GND')]
    net(role+'_GND',grounds,'local return',notes='External UMB/chassis/PE and high-current return bonds unresolved')
    for signal in ['TX','RX']:
        net(role+'_UART_'+signal,[n(mcu,'PIN_UMB_'+signal+'_TBD','USART'),n('U_'+role+'_UMB','MCU_'+signal+'_TBD')],status='H',notes='Review ROM boot UART; external electrical layer unresolved')
    for signal in ['BOOT_RESET','NEXT_ENABLE','NEXT_RESET']:
        net(role+'_'+signal,[n(mcu,'PIN_'+signal+'_TBD','reserved'),n('U_'+role+'_UMB',signal+'_TBD')],status='H',notes='Functional reservation only; external reset/BOOT circuitry may be needed')
    for signal in ['SWDIO','SWCLK','NRST']:
        net(role+'_'+signal,[n(mcu,signal+'_TBD'),n('J_'+role+'_DEBUG',signal)],status='H',notes='Preserve recovery; exact board routing pending')
    for signal in ['SDA','SCL']:
        endpoints=[n(mcu,'PIN_I2C_'+signal+'_TBD','I2C')]
        endpoints += [n('U_MUX',signal)] if role=='AIR' else [n('S_M0',signal),n('U_GPIO_IN',signal),n('U_GPIO_OUT',signal),n('U_LED',signal)]
        net(role+'_I2C_'+signal,endpoints,notes='Separate buses; reviewed 3.3V pullups and unique module addresses')
    for side in ['UPSTREAM','DOWNSTREAM']:
        net(role+'_'+side+'_UMB',[n('U_'+role+'_UMB',side+'_CONTACTS_UNKNOWN'),n('J_'+role+'_'+side,'CONTACTS_UNKNOWN')],'external UMB unknown','H','No physical pin numbers, electrical topology or chain order assigned')
for i in range(4):
    for signal,muxpin in [('SDA','SD'),('SCL','SC')]:
        net('C'+str(i)+'_'+signal,[n('U_MUX',muxpin+str(i)),n('S_C'+str(i),signal)],notes='Chamber SHT45 0x44 on mux channel '+str(i))
net('MUX_ADDRESS',[n('U_MUX','A0_A1_A2_DEFAULT_LOW')],notes='0x70; channels 4..7 unused')
net('MUX_RESET_N',[n('U_AIR','PIN_MUX_RESET_TBD','optional output'),n('U_MUX','RST')],notes='Retain module pullup until reviewed')
net('FAN_PWM_MCU',[n('U_AIR','PIN_FAN_PWM_TBD','timer output'),n('U_PWM','INPUT_3V3')],notes='25kHz; fail-state bias and powered-off behavior pending')
net('FAN_PWM',[n('U_PWM','FAN_PWM_OUTPUT'),n('FAN1','PWM')],'fan logic TBD',notes='Conditioned CMOS-compatible driver; verify exact fan input')
net('FAN_TACH',[n('FAN1','TACH'),n('R_TACH_SERIES','IN'),n('R_TACH_PULLUP','SIGNAL')],'conditioned 3.3V tach',notes='Open collector; reviewed resistance and sink-current limit')
net('FAN_TACH_PULLUP',[n('U_AIR','BOARD_3V3_OUTPUT'),n('R_TACH_PULLUP','SUPPLY')],'3.3V power')
net('FAN_TACH_MCU',[n('R_TACH_SERIES','OUT'),n('U_AIR','PIN_TACH_CAPTURE_TBD','capture/interrupt')])
net('FAN_RETURN',[n('FAN1','GND'),n('U_PWM','GND'),n('J_PWR24','MINUS')],'fan power return',notes='No motor current through sensor/MCU returns; logic reference bond requires review')
net('ACTUATOR_INPUT',[n('J_ACT_PWR','PLUS'),n('F_ACT','IN')],'actuator voltage TBD',notes='Do not assume 24V before motor/coil ratings')
for i in range(6):
    drv='DRV_F'+str(i)
    for signal in ['STEP','DIR','ENABLE']:
        net('FEED_'+str(i)+'_'+signal,[n('U_MATERIAL','PIN_FEED_'+str(i)+'_'+signal+'_TBD','reserved output'),n(drv,signal)],notes='Proposed six-driver option, not stock motor count; external driver interface')
    for signal in ['ARRIVAL','EXIT']:
        net('FEED_'+str(i)+'_'+signal,[n('S_FEED'+str(i),signal+'_TBD'),n('U_GPIO_IN','FEED_'+str(i)+'_'+signal)],notes='Sensor type/count/conditioning unresolved')
    net('FEED_'+str(i)+'_POWER',[n('F_ACT','OUT'),n(drv,'POWER_INPUT')],'actuator power TBD')
    net('FEED_'+str(i)+'_RETURN',[n('J_ACT_PWR','MINUS'),n(drv,'POWER_RETURN')],'actuator return',notes='Review grounding/logic reference; no assumed direct bond')
for signal in ['DRIVE','DIRECTION','ENABLE']:
    net('REWINDER_'+signal,[n('U_MATERIAL','PIN_REWINDER_'+signal+'_TBD','reserved output'),n('DRV_RW',signal+'_TBD')],notes='Motor/driver architecture unresolved')
for side in ['LEFT','RIGHT']:
    net('DECOUPLER_'+side,[n('S_DECOUPLER_'+side,'CONDITIONED_FEEDBACK_TBD'),n('U_MATERIAL','PIN_DECOUPLER_'+side+'_TBD','reserved input')],notes='Interface unknown; optional ADC must use reviewed 0..3.3V range')
for signal in ['DOOR','DRIVER_FAULT','SELECTOR_ENDSTOP']:
    net(signal,[n('S_'+signal,'CONDITIONED_OUTPUT_TBD'),n('U_GPIO_IN',signal+'_TBD')],notes='Polarity and fault behavior unresolved')
for signal in ['SELECTOR','SOLENOID','DRYER_HEATER','DRYER_FAN','DRYER_VALVE']:
    net(signal,[n('U_GPIO_OUT',signal+'_TBD'),n('DRV_'+signal,'CONTROL_TBD')],notes='External power stage and default inhibit required')
for signal in ['MISO','MOSI','SCK','CS']:
    net('NFC_'+signal,[n('U_MATERIAL','PIN_NFC_'+signal+'_TBD','SPI reserve'),n('U_NFC',signal+'_TBD')],notes='Only if selected NFC reader uses SPI; antenna selection unresolved')
for source,dest in [('AIR','MATERIAL'),('MATERIAL','AIR')]:
    net(source+'_TO_'+dest+'_OPTION',[n('U_'+source,'PIN_PRIVATE_TX_TBD'),n('U_'+dest,'PIN_PRIVATE_RX_TBD')],status='H',notes='Optional private telemetry link, not UMB; unimplemented')
seen=set()
for row in rows:
    key=(row['net'],row['component'],row['pin']);assert key not in seen,key;seen.add(key)
with (ROOT/'connection_nodes.csv').open('w',newline='',encoding='utf-8') as stream:
    writer=csv.DictWriter(stream,fieldnames=['net','component','pin','direction','domain','status','notes'],lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
print(f'Generated {len(rows)} symbolic nodes on {len(set(r["net"] for r in rows))} nets; no physical pin allocation/electrical validation.')
