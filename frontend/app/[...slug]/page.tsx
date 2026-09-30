import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { PageView } from '@/components/pages/PageView';
import type { Category, PageLink, PageListItem } from '@/lib/types';

export const dynamic = 'force-dynamic';

/**
 * Category index page: /classes, /spells, /locations, ...
 * Homebrew pages appear in the same list as imported ones.
 */
export default async function ContentPage({ params }: { params: { slug: string[] } }) {
  const segments = params.slug;
  const last = segments[segments.length - 1];

  // /classes/wizard -> page detail; /classes -> category index
  if (segments.length >= 2) {
    return <PageDetailRoute categorySlug={segments[0]} pageSlug={last} />;
  }
  return <CategoryIndexRoute slug={last} />;
}

async function PageDetailRoute({
  categorySlug,
  pageSlug,
}: {
  categorySlug: string;
  pageSlug: string;
}) {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let page;
  let backlinks: PageLink[] = [];
  let children: PageListItem[] = [];

  try {
    navigation = await api.navigation();
    page = await api.page(pageSlug);
    [backlinks, children] = await Promise.all([
      api.backlinks(pageSlug),
      api.children(pageSlug),
    ]);
  } catch {
    notFound();
  }

  // Guard against a page living under a category it does not belong to.
  if (page.category && page.category.slug !== categorySlug) {
    redirect(page.url_path);
  }

  return (
    <AppLayout navigation={navigation} currentSlug={page.category?.slug}>
      <PageView page={page} backlinks={backlinks} children={children} />
    </AppLayout>
  );
}

async function CategoryIndexRoute({ slug }: { slug: string }) {

  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let categories: Category[] = [];
  let pages: PageListItem[] = [];

  try {
    navigation = await api.navigation();
    categories = await api.categories();
    const response = await api.pagesByCategory(slug);
    pages = response.results;
  } catch {
    notFound();
  }

  const category =
    findCategory(categories, slug) ??
    findCategory(navigation.core, slug) ??
    findCategory(navigation.campaign, slug);

  if (!category && pages.length === 0) notFound();

  return (
    <AppLayout navigation={navigation} currentSlug={slug}>
      <Breadcrumbs
        crumbs={[
          { name: 'D&D 2024', href: '/' },
          { name: category?.name ?? slug },
        ]}
      />
      <h1 className="page-title">{category?.name ?? slug}</h1>
      {category?.description && <p className="page-subtitle">{category.description}</p>}

      {category && category.children.length > 0 && (
        <>
          <h2 className="index-heading">Subcategorias</h2>
          <ul className="index-list">
            {category.children.map((child) => (
              <li key={child.slug}>
                <Link href={`/${child.slug}`}>{child.name}</Link>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2 className="index-heading">Páginas ({pages.length})</h2>
      {pages.length === 0 ? (
        <p>Nenhuma página nesta categoria ainda.</p>
      ) : (
        <ul className="index-list">
          {pages.map((page) => (
            <li key={page.id}>
              <Link href={page.url_path}>{page.title}</Link>
              {page.subtitle ? ` — ${page.subtitle}` : ''}
            </li>
          ))}
        </ul>
      )}

      <footer className="page-footer">{pages.length} páginas nesta categoria.</footer>
    </AppLayout>
  );
}

function findCategory(items: Category[], slug: string): Category | undefined {
  for (const item of items) {
    if (item.slug === slug) return item;
    const found = item.children ? findCategory(item.children, slug) : undefined;
    if (found) return found;
  }
  return undefined;
}