'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { PageListItem, SpellGroup } from '@/lib/types';

const CLASS_LABELS: Record<string, string> = {
  artificer: 'Artificer', barbarian: 'Barbarian', bard: 'Bard', cleric: 'Cleric',
  druid: 'Druid', fighter: 'Fighter', monk: 'Monk', paladin: 'Paladin',
  ranger: 'Ranger', rogue: 'Rogue', sorcerer: 'Sorcerer', warlock: 'Warlock', wizard: 'Wizard',
  runescaper: 'Runescaper', 'filho-da-magia': 'Nascido da Magia', heroi: 'Herói',
  'cavaleiro-da-morte': 'Cavaleiro da Morte', 'cacador-de-demonios': 'Caçador de Demônios',
  xama: 'Xamã', witcher: 'Witcher', dovahkiin: 'Dovahkiin',
};

type SpellFields = {
  school?: string;
  classes?: string[];
  casting_time?: string;
  range?: string;
  duration?: string;
};

function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

export function SpellCollection({
  spells,
  groups,
  level,
  initialSearch = '',
}: {
  spells: PageListItem[];
  groups: SpellGroup[];
  level: string;
  initialSearch?: string;
}) {
  const [view, setView] = useState<'cards' | 'list'>('cards');
  const [search, setSearch] = useState(initialSearch);

  useEffect(() => {
    if (localStorage.getItem('catalog-view') === 'list') setView('list');
  }, []);

  const change = (next: 'cards' | 'list') => {
    setView(next);
    localStorage.setItem('catalog-view', next);
  };

  const normalizedQuery = normalizeText(search.trim());

  const visible = spells.filter((spell) => {
    if (level && String((spell.structured_data as { level?: number })?.level) !== level) {
      return false;
    }
    if (!normalizedQuery) return true;

    const data = spell.structured_data as SpellFields;
    const titleMatch = normalizeText(spell.title).includes(normalizedQuery);
    const schoolMatch = data.school ? normalizeText(data.school).includes(normalizedQuery) : false;
    const classMatch = data.classes?.some((item) => {
      const label = CLASS_LABELS[item.toLowerCase()] || item;
      return normalizeText(label).includes(normalizedQuery);
    });

    return titleMatch || schoolMatch || classMatch;
  });

  return (
    <section className="catalog-section" aria-labelledby="spells-heading">
      <div className="catalog-section__heading">
        <h2 id="spells-heading" className="index-heading">
          Magias ({visible.length})
        </h2>
        <div className="catalog-section__tools">
          <div className="catalog-search-wrap">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar magia..."
              aria-label="Pesquisar magia"
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
              onClick={() => change('cards')}
            >
              Cards
            </button>
            <button
              type="button"
              className={view === 'list' ? 'active' : ''}
              onClick={() => change('list')}
            >
              Lista
            </button>
          </div>
        </div>
      </div>

      {visible.length === 0 ? (
        <p className="spell-empty">
          Nenhuma magia encontrada{search ? ` para "${search}"` : ''}.
        </p>
      ) : view === 'cards' ? (
        <div className="catalog-grid catalog-grid--generic">
          {visible.map((spell) => {
            const data = spell.structured_data as SpellFields;
            return (
              <Link className="catalog-card" href={spell.url_path} key={spell.id}>
                <span className="catalog-card__title">{spell.title}</span>
                <span className="catalog-card__subtitle">
                  {data.school || '—'} · {data.casting_time || '—'}
                </span>
                <span className="catalog-card__meta">
                  {data.classes?.map((item) => CLASS_LABELS[item.toLowerCase()] || item).join(', ') ||
                    spell.source_label}
                </span>
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
                <th>Escola</th>
                <th>Classes</th>
                <th>Conjuração</th>
                <th>Alcance</th>
                <th>Duração</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((spell) => {
                const data = spell.structured_data as SpellFields;
                return (
                  <tr key={spell.id}>
                    <td>
                      <Link href={spell.url_path}>{spell.title}</Link>
                    </td>
                    <td>{data.school || '—'}</td>
                    <td>
                      {data.classes
                        ?.map((item) => CLASS_LABELS[item.toLowerCase()] || item)
                        .join(', ') || '—'}
                    </td>
                    <td>{data.casting_time || '—'}</td>
                    <td>{data.range || '—'}</td>
                    <td>{data.duration || '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
