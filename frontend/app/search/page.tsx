import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { PAGE_TYPE_LABELS } from '@/lib/pageTemplates';
import type { Category, PageType, SearchResponse, Source } from '@/lib/types';

export const dynamic = 'force-dynamic';

const SOURCE_LABELS: Record<string, string> = {
  official: 'Official',
  wikidot: 'Wikidot',
  homebrew: 'Homebrew',
  campaign: 'Campaign',
  custom: 'Custom',
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const term = typeof searchParams.q === 'string' ? searchParams.q : '';
  const type = typeof searchParams.type === 'string' ? searchParams.type : '';
  const source = typeof searchParams.source === 'string' ? searchParams.source : '';
  const tag = typeof searchParams.tag === 'string' ? searchParams.tag : '';

  const params = new URLSearchParams();
  if (term) params.set('q', term);
  if (type) params.set('type', type);
  if (source) params.set('source', source);
  if (tag) params.append('tag', tag);

  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let data: SearchResponse = {
    query: term,
    count: 0,
    results: [],
    filters: { types: [], sources: [], visibilities: [] },
  };

  try {
    navigation = await api.navigation();
    data = await api.search(params);
  } catch {
    // Offline: render the shell with an empty result set.
  }

  const sources = data.filters.sources.length
    ? data.filters.sources
    : (['official', 'wikidot', 'homebrew', 'campaign', 'custom'] as Source[]);
  const types = data.filters.types.length
    ? data.filters.types
    : Object.keys(PAGE_TYPE_LABELS) as PageType[];

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Busca' }]} />
      <h1 className="page-title">Busca</h1>

      <form className="search-box" action="/search" method="get">
        <input type="search" name="q" defaultValue={term} aria-label="Termo de busca" />
        {type && <input type="hidden" name="type" value={type} />}
        {source && <input type="hidden" name="source" value={source} />}
        <button type="submit">Buscar</button>
      </form>

      <div className="filter-row">
        <span>Source:</span>
        {['', ...sources].map((value) => (
          <Link
            key={value || 'all'}
            href={buildHref(term, type, value, tag)}
            className={source === value ? 'active' : undefined}
          >
            {value ? SOURCE_LABELS[value] ?? value : 'Todos'}
          </Link>
        ))}
      </div>

      <div className="filter-row">
        <span>Tipo:</span>
        {['', ...types].map((value) => (
          <Link
            key={value || 'all'}
            href={buildHref(term, value, source, tag)}
            className={type === value ? 'active' : undefined}
          >
            {value ? PAGE_TYPE_LABELS[value] : 'Todos'}
          </Link>
        ))}
      </div>

      <h2 className="index-heading">
        {term ? `Resultados para "${term}"` : 'Todas as páginas'} ({data.count})
      </h2>

      {data.results.length === 0 ? (
        <p>Nenhuma página encontrada.</p>
      ) : (
        <div>
          {data.results.map((result) => (
            <div key={result.id} className="result-item">
              <div className="result-item__meta">
                {PAGE_TYPE_LABELS[result.page_type] ?? result.page_type} · Source:{' '}
                {result.source_label}
                {result.category ? ` · ${result.category.name}` : ''}
              </div>
              <div className="result-item__title">
                <Link href={result.url_path}>{result.title}</Link>
              </div>
              <div className="result-item__excerpt">{result.excerpt}</div>
            </div>
          ))}
        </div>
      )}

      <footer className="page-footer">{data.count} páginas encontradas.</footer>
    </AppLayout>
  );
}

function buildHref(term: string, type: string, source: string, tag: string): string {
  const params = new URLSearchParams();
  if (term) params.set('q', term);
  if (type) params.set('type', type);
  if (source) params.set('source', source);
  if (tag) params.set('tag', tag);
  const query = params.toString();
  return query ? `/search?${query}` : '/search';
}