import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { PageView } from '@/components/pages/PageView';
import { ClassDirectory } from '@/components/catalog/ClassDirectory';
import { SubclassDirectory } from '@/components/catalog/SubclassDirectory';
import { MagicItemCollection } from '@/components/catalog/MagicItemCollection';
import { EquipmentCollection } from '@/components/catalog/EquipmentCollection';
import { CatalogCollection } from '@/components/catalog/CatalogCollection';
import type { Category, PageLink, PageListItem } from '@/lib/types';

export const revalidate = 60;

/**
 * Category index page: /classes, /spells, /locations, ...
 * Homebrew pages appear in the same list as imported ones.
 */
export default async function ContentPage({ params }: { params: Promise<{ slug: string[] }> }) {
  const { slug: segments } = await params;
  const last = segments[segments.length - 1];

  // /classes/wizard -> page detail; /classes -> category index
  if (segments.length >= 2) {
    return <PageDetailRoute categorySlug={segments[0]} pageSlug={last} />;
  }
  return <SingleSegmentRoute slug={last} />;
}

/**
 * One segment can be either a category (/spells) or a bare page slug.
 * Imported content links spells as "/acid-splash", without the category, so a
 * single segment that is not a category is resolved as a page instead of 404.
 */
async function SingleSegmentRoute({ slug }: { slug: string }) {
  const categories = await api.categories().catch(() => []);
  const known = findCategory(categories, slug);
  if (known) return <CategoryIndexRoute slug={slug} initialCategories={categories} />;

  const page = await api.page(slug).catch(() => null);
  if (page) return <PageDetailRoute categorySlug={page.category?.slug ?? slug} pageSlug={slug} />;

  return <CategoryIndexRoute slug={slug} initialCategories={categories} />;
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

  // The page itself is the only thing that must succeed. Backlinks and
  // children are supplementary: if they fail, the page still renders instead
  // of turning into a misleading 404.
  try {
    page = await api.page(pageSlug);
  } catch {
    notFound();
  }

  const [navRes, backlinksRes, childrenRes] = await Promise.all([
    api.navigation().catch(() => navigation),
    api.backlinks(pageSlug).catch(() => backlinks),
    api.children(pageSlug).catch(() => children),
  ]);
  navigation = navRes;
  backlinks = backlinksRes;
  children = childrenRes;

  // A page may be reached under the wrong category segment: serve the
  // canonical URL instead of failing.
  if (page.category && page.category.slug !== categorySlug) {
    redirect(page.url_path);
  }

  return (
    <AppLayout navigation={navigation} currentSlug={page.category?.slug}>
      <PageView page={page} backlinks={backlinks} children={children} />
    </AppLayout>
  );
}

async function CategoryIndexRoute({
  slug,
  initialCategories,
}: {
  slug: string;
  initialCategories?: Category[];
}) {
  const [navigation, categories] = await Promise.all([
    api.navigation().catch(() => ({ core: [] as Category[], campaign: [] as Category[] })),
    initialCategories ? Promise.resolve(initialCategories) : api.categories().catch(() => [] as Category[]),
  ]);

  const category =
    findCategory(categories, slug) ??
    findCategory(navigation.core, slug) ??
    findCategory(navigation.campaign, slug);

  // A category that lives under a parent (spell level, feat kind) is filled
  // through Page.subcategory; top-level categories through Page.category.
  const query = category?.parent
    ? `subcategory__slug=${slug}`
    : `category__slug=${slug}`;

  if (slug === 'classes') {
    const [pagesResponse, subclassesResponse] = await Promise.all([
      api.pages(query).catch(() => ({ results: [] as PageListItem[] })),
      api.pages('page_type=subclass').catch(() => ({ results: [] as PageListItem[] })),
    ]);

    const pages = pagesResponse.results;
    const classes = pages.filter((page) => !isUnearthedArcana(page) && !isRevisedClass(page));
    const allSubclasses = subclassesResponse.results;
    const subclasses: Record<string, PageListItem[]> = {};
    for (const sub of allSubclasses) {
      const parent = sub.parent_page_slug;
      if (parent) {
        if (!subclasses[parent]) subclasses[parent] = [];
        subclasses[parent].push(sub);
      }
    }
    return (
      <AppLayout navigation={navigation} currentSlug={slug}>
        <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: category?.name ?? slug }]} />
        <ClassDirectory classes={classes} subclasses={subclasses} />
      </AppLayout>
    );
  }

  const pagesResponse = await api.pages(query).catch(() => ({ results: [] as PageListItem[] }));
  const pages = pagesResponse.results;

  if (!category && pages.length === 0) notFound();

  if (slug === 'subclasses') {
    return (
      <AppLayout navigation={navigation} currentSlug={slug}>
        <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: category?.name ?? slug }]} />
        <SubclassDirectory pages={pages} />
      </AppLayout>
    );
  }

  if (slug === 'equipment') {
    return (
      <AppLayout navigation={navigation} currentSlug={slug}>
        <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: category?.name ?? 'Equipment' }]} />
        <h1 className="page-title">{category?.name ?? 'Equipment'}</h1>
        {category?.description && <p className="page-subtitle">{category.description}</p>}
        <EquipmentCollection pages={pages} />
      </AppLayout>
    );
  }

  if (slug === 'magic-items') {
    return (
      <AppLayout navigation={navigation} currentSlug={slug}>
        <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: category?.name ?? 'Magic Items' }]} />
        <h1 className="page-title">{category?.name ?? 'Magic Items'}</h1>
        {category?.description && <p className="page-subtitle">{category.description}</p>}
        <MagicItemCollection pages={pages} />
      </AppLayout>
    );
  }

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
        <>
        <CatalogCollection pages={pages} showTitle={false} />
        {/*
        <ul className="index-list" hidden>
          {pages.map((page) => (
            <li key={page.id}>
              <Link href={page.url_path}>{page.title}</Link>
              {page.subtitle ? ` — ${page.subtitle}` : ''}
            </li>
          ))}
        </ul>
        */}
        </>
      )}

      <footer className="page-footer">{pages.length} páginas nesta categoria.</footer>
    </AppLayout>
  );
}

function isUnearthedArcana(page: PageListItem): boolean {
  return typeof page.structured_data?.wikidot_path === 'string'
    && page.structured_data.wikidot_path.startsWith('ua:');
}

function isRevisedClass(page: PageListItem): boolean {
  return /\b(?:revised|revision|revis(?:ão|ao|ado))\b/i.test(page.title);
}

function findCategory(items: Category[], slug: string): Category | undefined {
  for (const item of items) {
    if (item.slug === slug) return item;
    const found = item.children ? findCategory(item.children, slug) : undefined;
    if (found) return found;
  }
  return undefined;
}
