"""Private transport: Digest auth in macOS Keychain; request/response over stdio."""
import base64
import ctypes as C
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


def mac_keychain(host, value=None):
    service = ('cura-mcp-s5.' + host).encode()
    account = b'Cura MCP Bridge'
    sec = C.CDLL('/System/Library/Frameworks/Security.framework/Security')
    find = sec.SecKeychainFindGenericPassword
    find.argtypes = [C.c_void_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_char_p,
                     C.POINTER(C.c_uint32),C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)]
    size, data, item = C.c_uint32(), C.c_void_p(), C.c_void_p()
    code = find(None,len(service),service,len(account),account,C.byref(size),C.byref(data),C.byref(item))
    current = None
    if code == 0:
        current = C.string_at(data, size.value)
        free = sec.SecKeychainItemFreeContent
        free.argtypes = [C.c_void_p,C.c_void_p]
        free(None,data)
    elif code != -25300:
        raise RuntimeError('Keychain access denied')
    try:
        if value is None:
            return json.loads(current) if current else None
        encoded = json.dumps(value).encode()
        if code == 0:
            modify = sec.SecKeychainItemModifyAttributesAndData
            modify.argtypes = [C.c_void_p,C.c_void_p,C.c_uint32,C.c_void_p]
            code = modify(item,None,len(encoded),encoded)
        else:
            add = sec.SecKeychainAddGenericPassword
            add.argtypes = [C.c_void_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_void_p,C.c_void_p]
            code = add(None,len(service),service,len(account),account,len(encoded),encoded,None)
        if code:
            raise RuntimeError('Keychain storage failed')
    finally:
        if item:
            core = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
            core.CFRelease.argtypes = [C.c_void_p]
            core.CFRelease(item)


def windows_credentials(host, value=None):
    from ctypes import wintypes as W
    class Credential(C.Structure):
        _fields_=[('Flags',W.DWORD),('Type',W.DWORD),('TargetName',W.LPWSTR),
            ('Comment',W.LPWSTR),('LastWritten',W.FILETIME),('CredentialBlobSize',W.DWORD),
            ('CredentialBlob',C.POINTER(C.c_ubyte)),('Persist',W.DWORD),
            ('AttributeCount',W.DWORD),('Attributes',C.c_void_p),('TargetAlias',W.LPWSTR),('UserName',W.LPWSTR)]
    api=C.WinDLL('Advapi32',use_last_error=True)
    api.CredReadW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.POINTER(C.POINTER(Credential))]
    api.CredReadW.restype=W.BOOL
    api.CredWriteW.argtypes=[C.POINTER(Credential),W.DWORD];api.CredWriteW.restype=W.BOOL
    api.CredFree.argtypes=[C.c_void_p]
    target='Codex.CuraMCP.S5.'+host
    if value is None:
        ptr=C.POINTER(Credential)()
        if not api.CredReadW(target,1,0,C.byref(ptr)):
            if C.get_last_error()==1168:return None
            raise RuntimeError('Windows credential access denied')
        try:return json.loads(C.string_at(ptr.contents.CredentialBlob,ptr.contents.CredentialBlobSize).decode('utf-16-le'))
        finally:api.CredFree(ptr)
    raw=json.dumps(value).encode('utf-16-le');buffer=(C.c_ubyte*len(raw)).from_buffer_copy(raw)
    credential=Credential();credential.Type=1;credential.TargetName=target
    credential.CredentialBlobSize=len(raw);credential.CredentialBlob=buffer
    credential.Persist=2;credential.UserName='Cura MCP Bridge'
    if not api.CredWriteW(C.byref(credential),0):raise RuntimeError('Windows credential storage failed')


def keychain(host,value=None):
    if sys.platform=='win32':return windows_credentials(host,value)
    if sys.platform=='darwin':return mac_keychain(host,value)
    if value is not None:raise RuntimeError('Secure credential storage unavailable on this platform')
    return None


def main():
    args = json.load(sys.stdin)
    base = args['base_url']
    host = urllib.parse.urlsplit(base).netloc
    url = base + args['path']
    if args.get('query'):
        url += '?' + urllib.parse.urlencode(args['query'], doseq=True)
    headers, body = {}, None
    if args.get('files'):
        boundary = 'cura-' + uuid.uuid4().hex
        chunks = []
        for k,v in args.get('form', {}).items():
            chunks.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+k+'"\r\n\r\n'+str(v)+'\r\n').encode())
        for file in args['files']:
            chunks.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+file['field']+'"; filename="'+file['name']+'"\r\nContent-Type: application/octet-stream\r\n\r\n').encode())
            with open(file['path'],'rb') as source:
                chunks.extend([source.read(), b'\r\n'])
        chunks.append(('--'+boundary+'--\r\n').encode())
        body = b''.join(chunks)
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    elif 'form' in args:
        body = urllib.parse.urlencode(args['form']).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    elif 'body' in args:
        body = json.dumps(args['body']).encode()
        headers['Content-Type'] = 'application/json'
    credentials = keychain(host)
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    if credentials:
        manager.add_password(None, base, credentials['id'], credentials['key'])
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *unused):
            return None
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPDigestAuthHandler(manager))
    request = urllib.request.Request(url, data=body, headers=headers, method=args['method'])
    try:
        response = opener.open(request, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read(5*1024*1024+1)
        if len(raw) > 5*1024*1024:
            raise RuntimeError('Response exceeds 5 MiB; use a bounded/snapshot endpoint')
        content_type = response.headers.get('Content-Type','')
        try:
            payload = json.loads(raw) if raw else None
        except (ValueError,UnicodeError):
            payload = {'content_base64': base64.b64encode(raw).decode()}
        if args['path'] == '/api/v1/auth/request' and response.status == 200:
            if not isinstance(payload,dict) or not payload.get('id') or not payload.get('key'):
                raise RuntimeError('Unexpected pairing response')
            keychain(host,payload)
            payload = {'pairing_id':payload['id'],'key_stored_in':('Windows Credential Manager' if sys.platform=='win32' else 'macOS Keychain'),
                       'next_step':'Approve Cura MCP Bridge on the printer display, then read /auth/verify.'}
        return {'http_status':response.status,'content_type':content_type,'data':payload,
                'digest_credentials_available':bool(credentials)}


if __name__ == '__main__':
    try:
        print(json.dumps(main()))
    except Exception as error:
        print(json.dumps({'error':type(error).__name__,'detail':'Printer transport failed; secrets suppressed.'}))
