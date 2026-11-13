import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { TypeEditor } from '@/components/admin/TypeEditor';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function AdminSubclassEditPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try { navigation = await api.navigation(); } catch { /* offline */ }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Admin' }, { name: 'Subclasses' }, { name: 'Editar' }]} />
      <TypeEditor pageType="subclass" typeLabel="Subclasses" slug={slug} />
    </AppLayout>
  );
}