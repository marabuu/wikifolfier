import { API_URL } from './api';

export const OWNER_TOKEN_KEY = 'owner_editor_token';

/** Raised when the stored JWT is rejected (401/403) so editors reset to login. */
export class OwnerAuthError extends Error {
  constructor(message = 'Sessão expirada ou sem permissão. Entre novamente.') {
    super(message);
    this.name = 'OwnerAuthError';
  }
}

export function getOwnerToken(): string {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(OWNER_TOKEN_KEY) ?? '';
}

export function setOwnerToken(token: string): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(OWNER_TOKEN_KEY, token);
}

export function clearOwnerToken(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(OWNER_TOKEN_KEY);
}

/** Authenticate against the owner-only JWT endpoint with rate-limit handling. */
export async function loginOwner(username: string, password: string): Promise<string> {
  const response = await fetch(`${API_URL}/api/auth/owner-token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (response.status === 429) {
    throw new Error('Muitas tentativas de login. Aguarde 1 minuto e tente novamente.');
  }
  if (!response.ok) {
    throw new Error('Usuário ou senha inválidos; somente a conta proprietária pode entrar.');
  }
  const data = (await response.json()) as { access?: string };
  if (!data.access) {
    throw new Error('Resposta de autenticação inválida.');
  }
  setOwnerToken(data.access);
  return data.access;
}

/** Perform an authenticated API call and clear the token on 401/403 responses. */
export async function ownerRequest<T>(
  path: string,
  token: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });
  if (response.status === 401 || response.status === 403) {
    clearOwnerToken();
    throw new OwnerAuthError();
  }
  if (response.status === 429) {
    throw new Error('Muitas requisições em sequência. Aguarde um instante e tente novamente.');
  }
  if (!response.ok) {
    const body = await response.text().catch(() => '');
    throw new Error(body || `API ${response.status}: ${path}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
