import importlib.util
import unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('wire',Path(__file__).resolve().parents[1]/'tools/umb_wire.py')
wire=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(wire)
class WireTests(unittest.TestCase):
    def test_reference_crc(self):self.assertEqual(wire.crc8(b'123456789'),0xf4)
    def test_write(self):
        self.assertEqual(wire.write_payload(b'\x12\x34','48'),b'\x0348\x00\x12\x34')
        with self.assertRaises(ValueError):wire.write_payload(b'\0\1','a'*252)
    def test_frames(self):
        self.assertEqual(wire.decode_reply(wire.reply(2,b'1200'),2),(2,b'1200'))
        bad=bytearray(wire.reply(2,b'1200'));bad[-1]^=1
        with self.assertRaises(ValueError):wire.decode_reply(bad)
        with self.assertRaises(ValueError):wire.decode_reply(wire.reply(254,b'\xfd'))
        self.assertEqual(len(wire.request(1,3,b'x'*255)),260)
        with self.assertRaises(ValueError):wire.request(1,3,b'x'*256)
    def test_monitor(self):
        self.assertEqual(wire.monitor_records(b'\0\x0112\0\0\x0248\0'),[(b'\0\1','12'),(b'\0\2','48')])
        self.assertEqual(wire.monitor_records(b'\0\x0112\\x00',b'\\x00'),[(b'\0\1','12')])
        with self.assertRaises(ValueError):wire.monitor_records(b'\0\1bad')
if __name__=='__main__':unittest.main()
