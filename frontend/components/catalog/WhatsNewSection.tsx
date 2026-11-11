'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { WhatsNewItem, WhatsNewResponse } from '@/lib/types';

interface Props {
  initialData?: WhatsNewResponse | null;
}

type FilterKey = 'all' | 'subclass_class' | 'spell' | 'magic_item' | 'other';

export function WhatsNewSection({ initialData }: Props) {
  const [data, setData] = useState<WhatsNewResponse | null>(initialData ?? null);
  const [activeFilter, setActiveFilter] = useState<FilterKey>('all');
  const [loading, setLoading] = useState(!initialData);

  useEffect(() => {
    if (!initialData) {
      setLoading(true);
      api.whatsNew({ days: 30, limit: 120 })
        .then((res) => {
          setData(res);
        })
        .catch(() => {
          setData({ days: 30, total: 0, results: [] });
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [initialData]);

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  // Counts by category tab
  const counts = useMemo(() => {
    let subclassClass = 0;
    let spell = 0;
    let magicItem = 0;
    let other = 0;

    for (const it of items) {
      if (it.type === 'subclass' || it.type === 'class') subclassClass++;
      else if (it.type === 'spell') spell++;
      else if (it.type === 'magic_item') magicItem++;
      else other++;
    }

    return {
      all: total,
      subclass_class: subclassClass,
      spell,
      magic_item: magicItem,
      other,
    };
  }, [items, total]);

  // Filtered items based on active tab
  const filteredItems = useMemo(() => {
    let list = items;
    if (activeFilter === 'subclass_class') {
      list = items.filter((it) => it.type === 'subclass' || it.type === 'class');
    } else if (activeFilter === 'spell') {
      list = items.filter((it) => it.type === 'spell');
    } else if (activeFilter === 'magic_item') {
      list = items.filter((it) => it.type === 'magic_item');
    } else if (activeFilter === 'other') {
      list = items.filter((it) => it.type !== 'subclass' && it.type !== 'class' && it.type !== 'spell' && it.type !== 'magic_item');
    }
    // Limit to 12 cards on the home page so it looks balanced
    return list.slice(0, 12);
  }, [items, activeFilter]);

  if (!loading && total === 0) {
    return null;
  }

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('pt-BR');
    } catch {
      return '';
    }
  };

  const getBadgeClass = (type: string) => {
    if (type === 'subclass') return 'whats-new-badge--subclass';
    if (type === 'class') return 'whats-new-badge--class';
    if (type === 'spell') return 'whats-new-badge--spell';
    if (type === 'magic_item') return 'whats-new-badge--magic_item';
    if (type === 'feat') return 'whats-new-badge--feat';
    return 'whats-new-badge--other';
  };

  return (
    <section className="whats-new-section" aria-label="O que há de novo">
      <div className="whats-new-header">
        <div className="whats-new-title-group">
          <h2 className="whats-new-title">
            <span>✨ O que há de novo</span>
            {total > 0 && (
              <span className="whats-new-pill-count">{total} novos</span>
            )}
          </h2>
          <p className="whats-new-subtitle">
            Novos conteúdos lançados no compêndio nos últimos 30 dias (permanecem por 1 mês após o lançamento).
          </p>
        </div>
        <Link href="/whats-new" className="button" style={{ fontSize: 13, padding: '7px 14px' }}>
          Ver todos ({total}) →
        </Link>
      </div>

      <div className="whats-new-filters">
        <button
          type="button"
          className={`whats-new-filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          Todos ({counts.all})
        </button>
        {counts.subclass_class > 0 && (
          <button
            type="button"
            className={`whats-new-filter-btn ${activeFilter === 'subclass_class' ? 'active' : ''}`}
            onClick={() => setActiveFilter('subclass_class')}
          >
            Subclasses &amp; Classes ({counts.subclass_class})
          </button>
        )}
        {counts.spell > 0 && (
          <button
            type="button"
            className={`whats-new-filter-btn ${activeFilter === 'spell' ? 'active' : ''}`}
            onClick={() => setActiveFilter('spell')}
          >
            Magias ({counts.spell})
          </button>
        )}
        {counts.magic_item > 0 && (
          <button
            type="button"
            className={`whats-new-filter-btn ${activeFilter === 'magic_item' ? 'active' : ''}`}
            onClick={() => setActiveFilter('magic_item')}
          >
            Itens Mágicos ({counts.magic_item})
          </button>
        )}
        {counts.other > 0 && (
          <button
            type="button"
            className={`whats-new-filter-btn ${activeFilter === 'other' ? 'active' : ''}`}
            onClick={() => setActiveFilter('other')}
          >
            Outros ({counts.other})
          </button>
        )}
      </div>

      <div className="whats-new-grid">
        {filteredItems.map((item) => (
          <Link key={item.id} href={item.url} className="whats-new-card">
            <div className="whats-new-card__head">
              <span className={`whats-new-badge ${getBadgeClass(item.type)}`}>
                {item.type_label}
              </span>
              <span className="whats-new-card__date">{formatDate(item.created_at)}</span>
            </div>
            <div className="whats-new-card__title">{item.title}</div>
            <div className="whats-new-card__meta">
              {item.category_name ?? (item.edition ? `D&D ${item.edition}` : 'Compêndio')}
            </div>
          </Link>
        ))}
      </div>

      {total > 12 && (
        <div style={{ textAlign: 'center', marginTop: 18 }}>
          <Link href="/whats-new" className="button" style={{ fontSize: 13 }}>
            Ver todos os {total} conteúdos lançados nos últimos 30 dias →
          </Link>
        </div>
      )}
    </section>
  );
}
