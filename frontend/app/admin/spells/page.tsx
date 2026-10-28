import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { AdminList } from '@/components/admin/AdminList';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function AdminSpellsPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try { navigation = await api.navigation(); } catch { /* offline */ }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Admin' }, { name: 'Spells' }]} />
      <AdminList pageType="spell" typeLabel="Spells" typeSlug="spells" />
    </AppLayout>
  );
}