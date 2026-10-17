import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { PageEditor } from '@/components/editor/PageEditor';
import { api } from '@/lib/api';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function EditPage({ params }: { params: { slug: string } }) {
  const [page, navigation] = await Promise.all([
    api.page(params.slug),
    api.navigation().catch(() => ({ core: [] as Category[], campaign: [] as Category[] })),
  ]);
  return <AppLayout navigation={navigation}><Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: page.title, href: page.url_path }, { name: 'Editar' }]} /><h1 className="page-title">Editar: {page.title}</h1><PageEditor slug={page.slug} initialContent={page.source_content} /></AppLayout>;
}
