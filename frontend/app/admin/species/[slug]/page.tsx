import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { TypeEditor } from '@/components/admin/TypeEditor';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function AdminSpeciesEditPage({ params }: { params: { slug: string } }) {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try { navigation = await api.navigation(); } catch { /* offline */ }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Admin' }, { name: 'Species' }, { name: 'Editar' }]} />
      <TypeEditor pageType="species" typeLabel="Species" slug={params.slug} />
    </AppLayout>
  );
}