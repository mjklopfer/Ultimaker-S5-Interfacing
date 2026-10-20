"""Offline reference codec. No live serial connection, GPIO, reset or flashing support."""
import argparse

def crc8(data):
    crc=0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc=((crc<<1)^0x07)&255 if crc&128 else (crc<<1)&255
    return crc

def request(address,command,payload=b''):
    if not 0<=address<254 or not 0<=command<=255 or len(payload)>255:
        raise ValueError('invalid operational request')
    body=bytes([address,command,len(payload)])+payload
    return b'\xff'+body+bytes([crc8(body)])

def reply(command,payload=b''):
    if not 0<=command<=255 or len(payload)>255:
        raise ValueError('invalid reply')
    body=bytes([command,len(payload)])+payload
    return b'\xff'+body+bytes([crc8(body)])

def decode_reply(frame,expected_command=None):
    if len(frame)<4 or frame[0]!=255 or len(frame)!=frame[2]+4:
        raise ValueError('bad reply length/header')
    if crc8(frame[1:-1])!=frame[-1]:
        raise ValueError('bad reply CRC')
    if frame[1]==254:
        raise ValueError('device error: '+frame[3:-1].hex())
    if expected_command is not None and frame[1]!=expected_command:
        raise ValueError('unexpected reply command')
    return frame[1],frame[3:-1]

def write_payload(index_bytes,text):
    value=text.encode('ascii')
    if len(index_bytes)!=2 or not value.isascii() or any(b<32 or b>126 for b in value) or len(value)>251:
        raise ValueError('invalid index/value')
    return bytes([len(value)+1])+value+b'\0'+index_bytes

def monitor_records(payload,separator=b'\0'):
    if separator not in (b'\0',b'\\x00'):
        raise ValueError('unsupported delimiter')
    records=[]
    while payload:
        if len(payload)<2:raise ValueError('truncated monitor index')
        end=payload.find(separator,2)
        if end<0:raise ValueError('unterminated monitor value')
        records.append((payload[:2],payload[2:end].decode('ascii')))
        payload=payload[end+len(separator):]
    return records

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address',type=lambda s:int(s,0),default=0)
    parser.add_argument('--command',type=lambda s:int(s,0),default=0)
    parser.add_argument('--payload-hex',default='')
    args=parser.parse_args()
    print(request(args.address,args.command,bytes.fromhex(args.payload_hex)).hex(' '))
