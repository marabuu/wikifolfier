import Link from 'next/link';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import type { Category, WhatsNewItem } from '@/lib/types';

export const revalidate = 60;

const GROUP_ORDER = [
  'Subclasses',
  'Classes',
  'Invocação Mística',
  'Talentos',
  'Magias',
  'Itens Mágicos',
  'Regras',
  'Outros',
];

export default async function WhatsNewPage() {
  let navigation = { core: [] as Category[], campaign: [] as Category[] };
  let items: WhatsNewItem[] = [];
  let total = 0;

  try {
    const [nav, data] = await Promise.all([
      api.navigation().catch(() => ({ core: [] as Category[], campaign: [] as Category[] })),
      api.whatsNew({ days: 30, limit: 400 }).catch(() => ({ days: 30, total: 0, results: [] })),
    ]);
    navigation = nav;
    items = data.results;
    total = data.total;
  } catch {
    // API offline
  }

  const groups = items.reduce<Record<string, WhatsNewItem[]>>((result, item) => {
    let group = item.type_label;
    if (group === 'Subclasse') group = 'Subclasses';
    else if (group === 'Classe') group = 'Classes';
    else if (group === 'Magia') group = 'Magias';
    else if (group === 'Item Mágico') group = 'Itens Mágicos';
    else if (group === 'Talento') group = 'Talentos';
    else if (group === 'Regra') group = 'Regras';

    (result[group] ||= []).push(item);
    return result;
  }, {});

  const sortedGroupKeys = Object.keys(groups).sort((a, b) => {
    const ia = GROUP_ORDER.indexOf(a);
    const ib = GROUP_ORDER.indexOf(b);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return a.localeCompare(b);
  });

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('pt-BR');
    } catch {
      return '';
    }
  };

  return (
    <AppLayout navigation={navigation}>
      <Breadcrumbs crumbs={[{ name: 'D&D 2024', href: '/' }, { name: 'O que há de novo' }]} />
      <h1 className="page-title">✨ O que há de novo no compêndio</h1>
      <p className="page-subtitle">
        Todos os conteúdos lançados nos últimos 30 dias ({total} itens encontrados).
        Os itens permanecem nesta página por um mês a partir de seu lançamento e depois saem automaticamente.
      </p>

      {items.length === 0 ? (
        <p style={{ marginTop: 24, color: 'var(--muted)' }}>
          Nenhum conteúdo novo foi adicionado nos últimos 30 dias.
        </p>
      ) : (
        sortedGroupKeys.map((group) => (
          <section className="catalog-section" key={group} style={{ marginTop: 32 }}>
            <h2 className="index-heading" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span>{group}</span>
              <span className="whats-new-pill-count">{groups[group].length}</span>
            </h2>
            <ul className="index-list">
              {groups[group].map((item) => (
                <li key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Link href={item.url} style={{ fontWeight: 600 }}>
                      {item.title}
                    </Link>
                    <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                      {item.category_name ?? ''}
                    </span>
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                    {formatDate(item.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
    </AppLayout>
  );
}
