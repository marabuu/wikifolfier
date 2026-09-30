import type {
  Category,
  Navigation,
  PageDetail,
  PageLink,
  PageListItem,
  SearchResponse,
} from './types';

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  navigation: () => request<Navigation>('/navigation'),
  categories: () => request<Category[]>('/categories/'),
  pagesByCategory: (slug: string) =>
    request<{ results: PageListItem[] }>(`/pages/?category=${slug}&page_size=500`),
  page: (slug: string) => request<PageDetail>(`/pages/${slug}/`),
  backlinks: (slug: string) => request<PageLink[]>(`/pages/${slug}/backlinks/`),
  children: (slug: string) => request<PageListItem[]>(`/pages/${slug}/children/`),
  search: (params: URLSearchParams) =>
    request<SearchResponse>(`/search?${params.toString()}`),
  preview: (markdown: string, token?: string) =>
    request<{ html: string }>('/pages/preview/', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: JSON.stringify({ markdown }),
    }),
};

export type ApiPage = Awaited<ReturnType<typeof api.page>>;