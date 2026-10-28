import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import type { Category } from '@/lib/types';

export const dynamic = 'force-dynamic';

const ADMIN_TYPES = [
  { slug: 'classes', label: 'Classes', page_type: 'class' },
  { slug: 'subclasses', label: 'Subclasses', page_type: 'subclass' },
  { slug: 'species', label: 'Species', page_type: 'species' },
  { slug: 'backgrounds', label: 'Backgrounds', page_type: 'background' },
  { slug: 'feats', label: 'Feats', page_type: 'feat' },
  { slug: 'spells', label: 'Spells', page_type: 'spell' },
  { slug: 'equipments', label: 'Equipamentos', page_type: 'equipment' },
  { slug: 'whats-new', label: 'Destaques e lançamentos', page_type: 'other' },
];

export default async function AdminPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  try { navigation = await api.navigation(); } catch { /* offline */ }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Admin' }]} />
      <h1 className="page-title">Admin do Compêndio</h1>
      <p className="page-subtitle">
        Crie, edite e exclua conteúdo do compêndio. Somente o proprietário pode alterar.
      </p>
      <div className="catalog-grid catalog-grid--generic">
        {ADMIN_TYPES.map((type) => (
          <a key={type.slug} href={`/admin/${type.slug}`} className="catalog-card">
            <span className="catalog-card__title">{type.label}</span>
            <span className="catalog-card__meta">{type.page_type}</span>
          </a>
        ))}
      </div>
    </AppLayout>
  );
}
