import type {
  Category,
  Navigation,
  PageDetail,
  PageLink,
  PageListItem,
  SearchResponse,
  SpellIndexResponse,
  ContentModule,
} from './types';

const isServer = typeof window === 'undefined';
export const API_URL = isServer
  ? (process.env.INTERNAL_API_URL?.replace(/\/$/, '') || process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000')
  : (process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isServer = typeof window === 'undefined';
  const base = isServer
    ? (process.env.INTERNAL_API_URL?.replace(/\/$/, '') || process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000')
    : (process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000');
  const url = `${base}/api${path}`;

  const fetchOptions: RequestInit = {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  };

  // Cache GET requests on the server for 60 seconds (ISR) unless explicit cache/next config is provided
  if (isServer && (!init?.method || init.method.toUpperCase() === 'GET') && !init?.cache && !('next' in (init ?? {}))) {
    (fetchOptions as any).next = { revalidate: 60 };
  }

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  navigation: () => request<Navigation>('/navigation'),
  categories: () => request<Category[]>('/categories/'),
  preview: (markdown: string, token?: string) =>
    request<{ html: string }>('/pages/preview/', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: JSON.stringify({ markdown }),
    }),

  page: (slug: string) => request<PageDetail>(`/pages/${slug}/`),
  backlinks: (slug: string) => request<PageLink[]>(`/pages/${slug}/backlinks/`),
  children: (slug: string) => request<PageListItem[]>(`/pages/${slug}/children/`),
  search: (params: URLSearchParams) =>
    request<SearchResponse>(`/search?${params.toString()}`),
  spellIndex: (params: URLSearchParams) =>
    request<SpellIndexResponse>(`/spells-index?${params.toString()}`),
  pages: (query: string) =>
    request<{ results: PageListItem[] }>(`/pages/?${query}&page_size=2000`),
  modules: () => request<ContentModule[]>('/modules/'),
  module: (slug: string) => request<ContentModule>(`/modules/${slug}/`),

  pageCreate: (data: Record<string, unknown>, token: string) =>
    request<PageDetail>('/pages/', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    }),
  pageUpdate: (slug: string, data: Record<string, unknown>, token: string) =>
    request<PageDetail>(`/pages/${slug}/`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    }),
  pageDelete: (slug: string, token: string) =>
    request<null>(`/pages/${slug}/`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    }),
};

export type ApiPage = Awaited<ReturnType<typeof api.page>>;
