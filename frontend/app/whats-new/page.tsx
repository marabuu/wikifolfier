import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import type { Category, PageDetail } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface WhatsNewItem {
  title: string;
  type: string;
  url: string;
}

const TYPE_LABELS: Record<string, string> = {
  class: 'Classes',
  subclass: 'Subclasses',
  species: 'Espécies',
  background: 'Backgrounds',
  feat: 'Feats',
  spell: 'Magias',
  magic_item: 'Itens Mágicos',
  equipment: 'Equipamentos',
  weapon: 'Armas',
  armor: 'Armaduras',
  adventuring_gear: 'Equipamentos de Aventura',
  rule: 'Regras',
  condition: 'Condições',
  location: 'Localizações',
  npc: 'NPCs',
  faction: 'Facções',
  lore: 'Lore',
  event: 'Eventos',
  session: 'Sessões',
  house_rule: 'Regras de Casa',
  other: 'Outros',
};

export default async function WhatsNewPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let items: WhatsNewItem[] = [];

  try {
    navigation = await api.navigation();
    const page = await api.page('whats-new') as PageDetail;
    items = (page.structured_data?.items as WhatsNewItem[]) ?? [];
  } catch {
    // The feature is intentionally empty until the admin selects content.
  }

  const groups = items.reduce<Record<string, WhatsNewItem[]>>((result, item) => {
    (result[item.type] ||= []).push(item);
    return result;
  }, {});

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'Destaques e lançamentos' }]} />
      <h1 className="page-title">Destaques e lançamentos</h1>
      <p className="page-subtitle">Conteúdos selecionados pelo mestre, organizados por tipo.</p>

      {items.length === 0 ? (
        <p>Nenhum destaque publicado ainda.</p>
      ) : (
        Object.entries(groups).map(([type, entries]) => (
          <section className="catalog-section" key={type}>
            <h2 className="index-heading">{TYPE_LABELS[type] ?? type}</h2>
            <ul className="index-list">
              {entries.map((item) => <li key={item.url}><Link href={item.url}>{item.title}</Link></li>)}
            </ul>
          </section>
        ))
      )}
    </AppLayout>
  );
}
