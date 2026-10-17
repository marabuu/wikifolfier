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

export default async function FeatsPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let pages: PageListItem[] = [];
  try { navigation = await api.navigation(); pages = (await api.pagesByCategory('feats')).results; } catch { /* offline */ }
  return <AppLayout navigation={navigation} currentSlug="feats">
    <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Feats' }]} />
    <h1 className="page-title">Feats</h1>
    <p className="page-subtitle">{pages.length} feats</p>
    {FEAT_GROUPS.map((group) => { const feats = pages.filter((page) => page.subcategory?.slug === group.slug); return feats.length ? <CatalogCollection key={group.slug} title={group.label} pages={feats} /> : null; })}
    {pages.some((page) => !page.subcategory) && <CatalogCollection title="Outros Feats" pages={pages.filter((page) => !page.subcategory)} />}
  </AppLayout>;
}
