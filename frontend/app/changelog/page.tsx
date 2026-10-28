import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import Link from 'next/link';
import type { Category, PageListItem } from '@/lib/types';

export const dynamic = 'force-dynamic';

const PAGE_TYPE_LABELS: Record<string, string> = {
  class: 'Classe',
  subclass: 'Subclasse',
  species: 'Espécie',
  background: 'Background',
  feat: 'Feat',
  spell: 'Magia',
  magic_item: 'Item Mágico',
  equipment: 'Equipamento',
  weapon: 'Arma',
  armor: 'Armadura',
  adventuring_gear: 'Equipamento de Aventura',
  rule: 'Regra',
  condition: 'Condição',
  location: 'Localização',
  npc: 'NPC',
  faction: 'Facção',
  lore: 'Lore',
  event: 'Evento',
  session: 'Sessão',
  house_rule: 'Regra de Casa',
  other: 'Página',
};

export default async function ChangelogPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let pages: PageListItem[] = [];
  try {
    navigation = await api.navigation();
    const data = await api.pages('app_modified_at__isnull=false&ordering=-app_modified_at&page_size=2000');
    pages = data.results ?? [];
  } catch { /* offline */ }

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Changelog' }]} />
      <h1 className="page-title">Changelog</h1>
      <p className="page-subtitle">{pages.length} páginas, ordenadas pela última atualização.</p>

      <div className="admin-list-wrap">
        <table className="catalog-list">
          <thead>
            <tr>
              <th>Data</th>
              <th>Título</th>
              <th>Tipo</th>
              <th>Origem</th>
              <th>Publicado</th>
            </tr>
          </thead>
          <tbody>
            {pages.map((page) => (
              <tr key={page.id}>
                <td>{new Date(page.app_modified_at ?? '').toLocaleDateString('pt-BR')}</td>
                <td>
                  <Link href={page.url_path}>{page.title}</Link>
                  {page.subtitle && <small> — {page.subtitle}</small>}
                </td>
                <td>{PAGE_TYPE_LABELS[page.page_type] ?? page.page_type}</td>
                <td>{page.source_label}</td>
                <td>{page.is_published ? 'Sim' : 'Não'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}