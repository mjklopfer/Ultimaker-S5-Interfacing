// No printer address, credentials or hostname is bundled with this project.
export function printerBaseUrl() {
  const value=process.env.CURA_PRINTER_BASE_URL;
  if (!value) throw new Error('Set CURA_PRINTER_BASE_URL explicitly for printer operations.');
  let url;
  try { url=new URL(value); } catch { throw new Error('CURA_PRINTER_BASE_URL must be an HTTP(S) origin.'); }
  if (!['http:','https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname!=='/')
    throw new Error('Use an HTTP(S) origin without credentials, path, query or fragment.');
  return url.origin;
}
