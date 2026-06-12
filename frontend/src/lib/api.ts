/**
 * API 客户端 — 自动带 JWT token，处理 401 跳转登录
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface FetchOptions extends RequestInit {
  noAuth?: boolean;
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export async function apiFetch(path: string, options: FetchOptions = {}) {
  const { noAuth, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    ...(customHeaders as Record<string, string>),
  };

  if (!noAuth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_BASE}${path}`, { headers, ...rest });

  if (res.status === 401 && !noAuth) {
    localStorage.removeItem('token');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  return res;
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const res = await apiFetch(path);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiPost<T = any>(path: string, body: any): Promise<T> {
  const res = await apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `POST ${path} failed`);
  }
  return res.json();
}

export async function apiUpload<T = any>(path: string, formData: FormData): Promise<T> {
  const res = await apiFetch(path, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || `Upload failed`);
  }
  return res.json();
}

export async function apiDelete(path: string): Promise<void> {
  const res = await apiFetch(path, { method: 'DELETE' });
  if (!res.ok) throw new Error(`DELETE ${path} failed`);
}
