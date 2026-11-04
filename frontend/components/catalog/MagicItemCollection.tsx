'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import type { PageListItem } from '@/lib/types';

type ItemFields = {
  item_type?: string;
  rarity?: string;
  requires_attunement?: boolean;
  price?: number;
  price_display?: string;
};

interface TypeConfig {
  id: string;
  label: string;
  aliases: string[];
}

const MAGIC_ITEM_TYPES: TypeConfig[] = [
  { id: 'wondrous', label: 'Itens Maravilhosos', aliases: ['wondrous item', 'wondrous'] },
  { id: 'weapon', label: 'Armas', aliases: ['weapon'] },
  { id: 'potion', label: 'Poções', aliases: ['potion'] },
  { id: 'ring', label: 'Anéis', aliases: ['ring'] },
  { id: 'rod', label: 'Varas e Cetros', aliases: ['rod'] },
  { id: 'scroll', label: 'Pergaminhos', aliases: ['scroll'] },
  { id: 'armor', label: 'Armaduras e Escudos', aliases: ['armor', 'shield'] },
  { id: 'staff', label: 'Cajados', aliases: ['staff'] },
  { id: 'wand', label: 'Varinhas', aliases: ['wand'] },
  { id: 'other', label: 'Outros e Regras', aliases: ['other', 'consumable', 'crafting', 'listings'] },
];

function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function getMagicItemGroupId(item: PageListItem): string {
  const data = item.structured_data as ItemFields;
  const rawType = (data?.item_type || item.page_type || '').toLowerCase();

  for (const group of MAGIC_ITEM_TYPES) {
    if (group.aliases.some((alias) => rawType.includes(alias))) {
      return group.id;
    }
  }
  return 'other';
}

export function MagicItemCollection({ pages }: { pages: PageListItem[] }) {
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

  // Group pages by magic item type
  const groupedPages = useMemo(() => {
    const groups: Record<string, PageListItem[]> = {};
    for (const group of MAGIC_ITEM_TYPES) {
      groups[group.id] = [];
    }
    for (const item of searchedPages) {
      const gId = getMagicItemGroupId(item);
      if (!groups[gId]) groups[gId] = [];
      groups[gId].push(item);
    }
    return groups;
  }, [searchedPages]);

  // Active groups for rendering
  const activeGroups = useMemo(() => {
    if (selectedType === 'all') {
      return MAGIC_ITEM_TYPES.filter((group) => (groupedPages[group.id]?.length || 0) > 0);
    }
    return MAGIC_ITEM_TYPES.filter((group) => group.id === selectedType);
  }, [selectedType, groupedPages]);

  const totalVisible = useMemo(() => {
    if (selectedType === 'all') return searchedPages.length;
    return groupedPages[selectedType]?.length || 0;
  }, [selectedType, searchedPages, groupedPages]);

  return (
    <section className="catalog-section" aria-labelledby="magic-items-heading">
      <div className="catalog-section__heading">
        <h2 id="magic-items-heading" className="index-heading">
          Itens Mágicos ({totalVisible})
        </h2>
        <div className="catalog-section__tools">
          <div className="catalog-search-wrap">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar item mágico..."
              aria-label="Pesquisar item mágico"
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
      <nav className="spell-level-tabs" aria-label="Filtrar por tipo de item mágico">
        <button
          type="button"
          className={selectedType === 'all' ? 'active' : undefined}
          onClick={() => setSelectedType('all')}
        >
          Todos ({pages.length})
        </button>
        {MAGIC_ITEM_TYPES.map((type) => {
          const count = pages.filter((item) => getMagicItemGroupId(item) === type.id).length;
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
          Nenhum item mágico encontrado{search ? ` para "${search}"` : ''}.
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
                      if (data.rarity) metaParts.push(data.rarity);
                      if (data.item_type) metaParts.push(data.item_type);
                      if (data.requires_attunement) metaParts.push('Sintonia');
                      if (data.price_display) metaParts.push(data.price_display);
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
                          <th>Preço Sugerido</th>
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
                              <td>{data.price_display || '—'}</td>
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
