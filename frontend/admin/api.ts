let csrf = '';
export function setCSRF(value: string): void { csrf = value; }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if(options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if(options.method && !['GET','HEAD'].includes(options.method)) headers.set('X-CSRF-Token', csrf);
  const response = await fetch(path, {...options, headers, credentials:'same-origin'});
  const result = await response.json();
  if(!response.ok) {
    if(response.status === 401 && path !== '/api/login') window.dispatchEvent(new Event('session-expired'));
    let message = 'Die Aktion konnte nicht ausgeführt werden.';
    if(typeof result.detail === 'string') message = result.detail;
    else if(Array.isArray(result.detail)) message = result.detail.map((x: {loc: string[]; msg: string}) => `${x.loc.slice(1).join('.')}: ${x.msg}`).join(' · ');
    throw new Error(message);
  }
  return result as T;
}
export const json = (method: string, data: unknown): RequestInit => ({method, body:JSON.stringify(data)});
