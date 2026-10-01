import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import type { Category, PageListItem } from '@/lib/types';

export const dynamic = 'force-dynamic';

const FEAT_GROUPS = [
  { slug: 'feat-origin', label: 'Origin Feats' },
  { slug: 'feat-general', label: 'General Feats' },
  { slug: 'feat-fighting-style', label: 'Fighting Styles' },
  { slug: 'feat-epic-boon', label: 'Epic Boons' },
];

/** Feats grouped by kind. Homebrew feats appear alongside imported ones. */
export default async function FeatsPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let pages: PageListItem[] = [];

  try {
    navigation = await api.navigation();
    const response = await api.pagesByCategory('feats');
    pages = response.results;
  } catch {
    // offline
  }

  const byGroup = (slug: string) =>
    pages.filter((page) => page.subcategory?.slug === slug);

  const ungrouped = pages.filter((page) => !page.subcategory);

  return (
    <AppLayout navigation={navigation} currentSlug="feats">
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Feats' }]} />
      <h1 className="page-title">Feats</h1>
      <p className="page-subtitle">{pages.length} feats</p>

      {FEAT_GROUPS.map((group) => {
        const feats = byGroup(group.slug);
        if (feats.length === 0) return null;
        return (
          <section key={group.slug}>
            <h2 className="index-heading">
              {group.label}{' '}
              <span style={{ fontWeight: 'normal', color: '#777' }}>
                ({feats.length})
              </span>
            </h2>
            <ul className="index-list">
              {feats.map((feat) => (
                <li key={feat.id}>
                  <Link href={feat.url_path}>{feat.title}</Link>
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      {ungrouped.length > 0 && (
        <section>
          <h2 className="index-heading">
            Outros Feats{' '}
            <span style={{ fontWeight: 'normal', color: '#777' }}>
              ({ungrouped.length})
            </span>
          </h2>
          <ul className="index-list">
            {ungrouped.map((feat) => (
              <li key={feat.id}>
                <Link href={feat.url_path}>{feat.title}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </AppLayout>
  );
}