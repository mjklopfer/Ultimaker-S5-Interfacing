"""Exercise the actual plugin listener class without importing Cura/Qt."""
import ast,os,socket,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer

class ListenerTest(unittest.TestCase):
    def test_second_instance_cannot_bind(self):
        source=Path(__file__).resolve().parents[1]/'cura_plugin/CuraMcpBridge/CuraMcpBridge.py'
        tree=ast.parse(source.read_text())
        declaration=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ExclusiveLoopbackServer')
        namespace=dict(os=os,socket=socket,ThreadingHTTPServer=ThreadingHTTPServer)
        exec(compile(ast.Module(body=[declaration],type_ignores=[]),str(source),'exec'),namespace)
        server=namespace['ExclusiveLoopbackServer'](('127.0.0.1',0),object)
        try:
            self.assertEqual(server.server_address[0],'127.0.0.1')
            with self.assertRaises(OSError):
                namespace['ExclusiveLoopbackServer'](server.server_address,object)
        finally:server.server_close()

if __name__=='__main__':unittest.main()
