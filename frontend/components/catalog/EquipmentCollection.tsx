'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import type { PageListItem } from '@/lib/types';

type ItemFields = {
  item_type?: string;
  rarity?: string;
  requires_attunement?: boolean;
};

interface TypeConfig {
  id: string;
  label: string;
  aliases: string[];
}

const EQUIPMENT_TYPES: TypeConfig[] = [
  { id: 'weapon', label: 'Armas', aliases: ['weapon', 'weapons', 'arma'] },
  { id: 'armor', label: 'Armaduras e Escudos', aliases: ['armor', 'shield', 'armadura'] },
  { id: 'wand', label: 'Varinhas', aliases: ['wand', 'varinha'] },
  { id: 'staff', label: 'Cajados', aliases: ['staff', 'cajado'] },
  { id: 'wondrous', label: 'Itens Maravilhosos', aliases: ['wondrous item', 'wondrous', 'item maravilhoso'] },
  {
    id: 'general',
    label: 'Equipamento Geral e Regras',
    aliases: [
      'equipamento geral',
      'adventuring gear',
      'tools',
      'mounts and vehicles',
      'poison',
      'trinkets',
      'crafting',
      'currency',
      'other',
    ],
  },
];

function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function getItemGroupId(item: PageListItem): string {
  const data = item.structured_data as ItemFields;
  const rawType = (data?.item_type || item.page_type || '').toLowerCase();

  for (const group of EQUIPMENT_TYPES) {
    if (group.aliases.some((alias) => rawType.includes(alias))) {
      return group.id;
    }
  }
  return 'general';
}

export function EquipmentCollection({ pages }: { pages: PageListItem[] }) {
  const [view, setView] = useState<'cards' | 'list'>('cards');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [search, setSearch] = useState<string>('');

  useEffect(() => {
    if (localStorage.getItem('catalog-view') === 'list') {
      setView('list');
    }
  }, []);

  const changeView = (next: 'cards' | 'list') => {
    setView(next);
    localStorage.setItem('catalog-view', next);
  };

  const normalizedQuery = normalizeText(search.trim());

  // Filter items by search query
  const searchedPages = useMemo(() => {
    if (!normalizedQuery) return pages;
    return pages.filter((item) => {
      const data = item.structured_data as ItemFields;
      const titleMatch = normalizeText(item.title).includes(normalizedQuery);
      const subtitleMatch = item.subtitle ? normalizeText(item.subtitle).includes(normalizedQuery) : false;
      const typeMatch = data.item_type ? normalizeText(data.item_type).includes(normalizedQuery) : false;
      const rarityMatch = data.rarity ? normalizeText(data.rarity).includes(normalizedQuery) : false;
      return titleMatch || subtitleMatch || typeMatch || rarityMatch;
    });
  }, [pages, normalizedQuery]);

  // Group pages by equipment type
  const groupedPages = useMemo(() => {
    const groups: Record<string, PageListItem[]> = {};
    for (const group of EQUIPMENT_TYPES) {
      groups[group.id] = [];
    }
    for (const item of searchedPages) {
      const gId = getItemGroupId(item);
      if (!groups[gId]) groups[gId] = [];
      groups[gId].push(item);
    }
    return groups;
  }, [searchedPages]);

  // Filtered by selected type tab
  const activeGroups = useMemo(() => {
    if (selectedType === 'all') {
      return EQUIPMENT_TYPES.filter((group) => (groupedPages[group.id]?.length || 0) > 0);
    }
    return EQUIPMENT_TYPES.filter((group) => group.id === selectedType);
  }, [selectedType, groupedPages]);

  const totalVisible = useMemo(() => {
    if (selectedType === 'all') return searchedPages.length;
    return groupedPages[selectedType]?.length || 0;
  }, [selectedType, searchedPages, groupedPages]);

  return (
    <section className="catalog-section" aria-labelledby="equipment-heading">
      <div className="catalog-section__heading">
        <h2 id="equipment-heading" className="index-heading">
          Equipamentos ({totalVisible})
        </h2>
        <div className="catalog-section__tools">
          <div className="catalog-search-wrap">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar equipamento..."
              aria-label="Pesquisar equipamento"
              className="catalog-search-input"
            />
            {search && (
              <button
                type="button"
                className="catalog-search-clear"
                onClick={() => setSearch('')}
                aria-label="Limpar pesquisa"
              >
                ×
              </button>
            )}
          </div>
          <div className="view-toggle" aria-label="Modo de visualização">
            <button
              type="button"
              className={view === 'cards' ? 'active' : ''}
              onClick={() => changeView('cards')}
            >
              Cards
            </button>
            <button
              type="button"
              className={view === 'list' ? 'active' : ''}
              onClick={() => changeView('list')}
            >
              Lista
            </button>
          </div>
        </div>
      </div>

      {/* Tabs / Filter by Type */}
      <nav className="spell-level-tabs" aria-label="Filtrar por tipo de equipamento">
        <button
          type="button"
          className={selectedType === 'all' ? 'active' : undefined}
          onClick={() => setSelectedType('all')}
        >
          Todos ({pages.length})
        </button>
        {EQUIPMENT_TYPES.map((type) => {
          const count = pages.filter((item) => getItemGroupId(item) === type.id).length;
          if (count === 0) return null;
          return (
            <button
              key={type.id}
              type="button"
              className={selectedType === type.id ? 'active' : undefined}
              onClick={() => setSelectedType(type.id)}
            >
              {type.label} ({count})
            </button>
          );
        })}
      </nav>

      {totalVisible === 0 ? (
        <p className="spell-empty">
          Nenhum equipamento encontrado{search ? ` para "${search}"` : ''}.
        </p>
      ) : (
        <div className="catalog-groups-container">
          {activeGroups.map((group) => {
            const items = groupedPages[group.id] || [];
            if (items.length === 0) return null;

            return (
              <div key={group.id} className="catalog-type-section" style={{ marginBottom: '32px' }}>
                <h3
                  className="index-heading"
                  style={{
                    fontSize: '18px',
                    margin: '16px 0 12px',
                    borderBottom: '1px solid var(--line)',
                    paddingBottom: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <span>{group.label}</span>
                  <span style={{ fontSize: '14px', color: 'var(--ink-soft)', fontWeight: 'normal' }}>
                    ({items.length})
                  </span>
                </h3>

                {view === 'cards' ? (
                  <div className="catalog-grid catalog-grid--generic">
                    {items.map((item) => {
                      const data = item.structured_data as ItemFields;
                      const metaParts: string[] = [];
                      if (data.item_type) metaParts.push(data.item_type);
                      if (data.rarity) metaParts.push(data.rarity);
                      if (data.requires_attunement) metaParts.push('Sintonia');
                      if (metaParts.length === 0) metaParts.push(item.source_label);

                      return (
                        <Link className="catalog-card" href={item.url_path} key={item.id}>
                          <span className="catalog-card__title">{item.title}</span>
                          {item.subtitle && <span className="catalog-card__subtitle">{item.subtitle}</span>}
                          <span className="catalog-card__meta">{metaParts.join(' • ')}</span>
                        </Link>
                      );
                    })}
                  </div>
                ) : (
                  <div className="catalog-list-wrap">
                    <table className="catalog-list">
                      <thead>
                        <tr>
                          <th>Nome</th>
                          <th>Tipo</th>
                          <th>Raridade</th>
                          <th>Sintonia</th>
                          <th>Origem</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item) => {
                          const data = item.structured_data as ItemFields;
                          return (
                            <tr key={item.id}>
                              <td>
                                <Link href={item.url_path}>{item.title}</Link>
                                {item.subtitle && <small style={{ display: 'block', color: 'var(--ink-soft)' }}>{item.subtitle}</small>}
                              </td>
                              <td>{data.item_type || group.label}</td>
                              <td>{data.rarity || '—'}</td>
                              <td>{data.requires_attunement ? 'Sim' : 'Não'}</td>
                              <td>{item.source_label}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
