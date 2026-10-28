import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { CatalogCollection } from '@/components/catalog/CatalogCollection';
import type { Category, PageListItem } from '@/lib/types';

export const dynamic = 'force-dynamic';

const FEAT_GROUPS = [
  { slug: 'feat-origin', label: 'Origin Feats' },
  { slug: 'feat-general', label: 'General Feats' },
  { slug: 'feat-fighting-style', label: 'Fighting Styles' },
  { slug: 'feat-epic-boon', label: 'Epic Boons' },
];

export default async function FeatsPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const kind = typeof searchParams.kind === 'string' ? searchParams.kind : '';
  const params = new URLSearchParams();
  if (kind) params.set('kind', kind);

  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let pages: PageListItem[] = [];
  try {
    navigation = await api.navigation();
    pages = (await api.pages('page_type=feat')).results;
  } catch { /* offline */ }

  const filtered = kind
    ? pages.filter((page) => page.subcategory?.slug === kind)
    : pages;

  const link = (patch: Record<string, string>) => {
    const merged = { kind, ...patch };
    const next = new URLSearchParams();
    if (merged.kind) next.set('kind', merged.kind);
    const query = next.toString();
    return query ? `/feats?${query}` : '/feats';
  };

  return (
    <AppLayout navigation={navigation} currentSlug="feats">
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Feats' }]} />
      <h1 className="page-title">Feats</h1>
      <p className="page-subtitle">{pages.length} feats</p>

      <form className="spell-filters" action="/feats" method="get">
        <label>
          Tipo
          <select name="kind" defaultValue={kind}>
            <option value="">Todos os tipos</option>
            {FEAT_GROUPS.map((group) => (
              <option key={group.slug} value={group.slug}>
                {group.label}
              </option>
            ))}
          </select>
        </label>
        <button className="filter-button button--solid" type="submit">
          Filtrar
        </button>
      </form>

      <nav className="spell-level-tabs" aria-label="Filtrar por tipo de feat">
        <Link className={!kind ? 'active' : undefined} href={link({ kind: '' })}>Todos</Link>
        {FEAT_GROUPS.map((group) => (
          <Link
            className={kind === group.slug ? 'active' : undefined}
            href={link({ kind: group.slug })}
            key={group.slug}
          >
            {group.label}
          </Link>
        ))}
      </nav>

      {filtered.length === 0 ? (
        <p className="spell-empty">Nenhum feat encontrado com esse filtro.</p>
      ) : (
        FEAT_GROUPS.map((group) => {
          const feats = filtered.filter((page) => page.subcategory?.slug === group.slug);
          return feats.length ? (
            <CatalogCollection key={group.slug} title={group.label} pages={feats} />
          ) : null;
        })
      )}
      {filtered.some((page) => !page.subcategory) && (
        <CatalogCollection title="Outros Feats" pages={filtered.filter((page) => !page.subcategory)} />
      )}
    </AppLayout>
  );
}
