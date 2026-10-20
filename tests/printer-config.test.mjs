import test from 'node:test';
import assert from 'node:assert/strict';
import {printerBaseUrl} from '../src/printer-config.mjs';

test('printer origin has no default and rejects credentials or URL suffixes',()=>{
  const original=process.env.CURA_PRINTER_BASE_URL;
  try {
    delete process.env.CURA_PRINTER_BASE_URL;
    assert.throws(()=>printerBaseUrl(),/explicitly/);
    process.env.CURA_PRINTER_BASE_URL='';
    assert.throws(()=>printerBaseUrl(),/explicitly/);
    for (const value of ['file:///tmp/device','http://example.invalid/path','http://example.invalid/?key=dummy','http://example.invalid/#dummy','http://dummy:dummy@example.invalid']) {
      process.env.CURA_PRINTER_BASE_URL=value;
      assert.throws(()=>printerBaseUrl(),/origin/);
    }
    process.env.CURA_PRINTER_BASE_URL='http://example.invalid:8080/';
    assert.equal(printerBaseUrl(),'http://example.invalid:8080');
  } finally {
    if (original===undefined) delete process.env.CURA_PRINTER_BASE_URL;
    else process.env.CURA_PRINTER_BASE_URL=original;
  }
});
