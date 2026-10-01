import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { PAGE_TYPE_LABELS } from '@/lib/pageTemplates';
import type { Category, PageListItem } from '@/lib/types';

export const dynamic = 'force-dynamic';

/**
 * Unearthed Arcana: every page whose source path lives in the "ua:" namespace.
 * It stays reachable from its own page, and the pages keep their normal
 * category — UA is a sourcebook grouping, not a separate kind of content.
 */
export default async function UnearthedArcanaPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let pages: PageListItem[] = [];

  try {
    navigation = await api.navigation();
    const response = await api.pages(`subcategory__slug=unearthed-arcana`);
    pages = response.results;
  } catch {
    // offline
  }

  const grouped = pages.reduce<Record<string, PageListItem[]>>((acc, page) => {
    const key = page.page_type;
    (acc[key] ||= []).push(page);
    return acc;
  }, {});

  return (
    <AppLayout navigation={navigation} currentSlug="unearthed-arcana">
      <Breadcrumbs
        crumbs={[
          { name: 'D&D 2024', href: '/' },
          { name: 'Unearthed Arcana' },
        ]}
      />
      <h1 className="page-title">Unearthed Arcana</h1>
      <p className="page-subtitle">
        {pages.length} páginas do suplemento oficial Unearthed Arcana.
      </p>

      {pages.length === 0 && <p>Nenhuma página de Unearthed Arcana.</p>}

      {Object.entries(grouped).map(([pageType, items]) => (
        <section key={pageType}>
          <h2 className="index-heading">
            {PAGE_TYPE_LABELS[pageType] ?? pageType}{' '}
            <span style={{ fontWeight: 'normal', color: '#777' }}>
              ({items.length})
            </span>
          </h2>
          <ul className="index-list">
            {items.map((page) => (
              <li key={page.id}>
                <Link href={page.url_path}>{page.title}</Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </AppLayout>
  );
}