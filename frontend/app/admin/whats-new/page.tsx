import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { WhatsNewEditor } from '@/components/admin/WhatsNewEditor';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function AdminWhatsNewPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try { navigation = await api.navigation(); } catch { /* offline */ }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Admin' }, { name: 'O que há de novo' }]} />
      <WhatsNewEditor />
    </AppLayout>
  );
}