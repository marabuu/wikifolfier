import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import type { Category, PageListItem } from '@/lib/types';

export const revalidate = 60;

export default async function ModulePage({ params }: { params: { slug: string } }) {
  const module = await api.module(params.slug).catch(() => null);
  if (!module) notFound();
  const [navigation, response] = await Promise.all([
    api.navigation().catch(() => ({ core: [] as Category[], campaign: [] as Category[] })),
    api.pages(`module__slug=${encodeURIComponent(params.slug)}&ordering=title`),
  ]);
  const pages = response.results ?? [];
  const grouped = pages.reduce<Record<string, PageListItem[]>>((all, page) => {
    (all[page.page_type] ??= []).push(page);
    return all;
  }, {});

  return <AppLayout navigation={navigation}>
    <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: module.name }]} />
    <h1 className="page-title">{module.name}</h1>
    <p className="page-subtitle">{module.description}</p>
    {module.source_url && <p><a href={module.source_url} target="_blank" rel="noreferrer">Fonte do módulo ↗</a></p>}
    <p className="page-subtitle">{pages.length} entradas{module.version ? ` · versão ${module.version}` : ''}</p>
    {Object.entries(grouped).map(([type, entries]) => <section className="home-group" key={type}>
      <h2 className="section-heading">{type.replace('_', ' ')} ({entries.length})</h2>
      <ul className="index-list">
        {entries.map((page) => <li key={page.id}><Link href={page.url_path}>{page.title}</Link></li>)}
      </ul>
    </section>)}
  </AppLayout>;
}
